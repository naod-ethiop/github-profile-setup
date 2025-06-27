from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
import time
import uuid
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
app = Flask(__name__)
CORS(app, origins=['*'], allow_headers=['Content-Type', 'Authorization'], supports_credentials=True)

CHAPA_SECRET = os.getenv("CHAPA_SECRET_KEY")
CHAPA_PUBLIC_KEY = os.getenv("CHAPA_PUBLIC_KEY")
CHAPA_BASE_URL = os.getenv("CHAPA_BASE_URL", "https://api.chapa.co/v1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

print(f"Environment: {ENVIRONMENT}")
print(f"Chapa Secret Key configured: {'Yes' if CHAPA_SECRET else 'No'}")
print(f"Using Chapa Base URL: {CHAPA_BASE_URL}")

try:
    service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if service_account_key:
        import json
        service_account_info = json.loads(service_account_key)
        cred = credentials.Certificate(service_account_info)
    else:
        # Try both possible filenames
        try:
            cred = credentials.Certificate("backend/serviceAccountKey.json")
        except FileNotFoundError:
            cred = credentials.Certificate("backend/serviceAccountkey.json")
    
    firebase_admin.initialize_app(cred)
    fs_db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    fs_db = None


@app.route('/api/update-user', methods=['POST'])
def update_user():
    if not request.is_json:
        return jsonify(
            {"error": "Invalid Content-Type. Must be application/json"}), 400

    data = request.get_json()

    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    user_id = data.get("userId")
    phone = data.get("phone")
    telegram_username = data.get("telegram")

    # Here you would typically use something like Firestore's client to update the user profile
    # db.collection('users').document(user_id).update({
    #     'phone': phone,
    #     'telegram': telegram_username
    # })

    return jsonify({
        "success": True,
        "message": "User updated successfully"
    }, 200)


@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    data = request.json
    tx_ref = f"bingo-{uuid.uuid4()}"

    payload = {
        "amount": data.get("amount"),
        "currency": "ETB",
        "email": data.get("email"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "tx_ref": tx_ref,
        "callback_url":
        "https://28f0eda4-60c8-4ddb-a036-763cb8fd46c0-00-2bbc1x56d1sdx.worf.replit.dev:5000/api/payment-callback",
        "return_url":
        "https://28f0eda4-60c8-4ddb-a036-763cb8fd46c0-00-2bbc1x56d1sdx.worf.replit.dev/payment-complete",
        "customization[title]": "Bingo Game",
        "customization[description]": "Entry Fee"
    }

    headers = {"Authorization": f"Bearer {CHAPA_SECRET}"}

    try:
        response = requests.post(
            "https://api.chapa.co/v1/transaction/initialize",
            headers=headers,
            json=payload)
        chapa_res = response.json()

        if chapa_res.get("status") != "success":
            return jsonify(
                {"error": chapa_res.get("message", "Unknown error")}), 400

        return jsonify({
            "checkout_url": chapa_res["data"]["checkout_url"],
            "tx_ref": tx_ref
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/wallet/deposit', methods=['POST'])
def wallet_deposit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        amount = data.get('amount')
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        user_id = data.get('userId')
        phone = data.get('phone')

        print(f"Received deposit request: {data}")  # Debug log

        # Validate required fields (last_name can be empty)
        if not all([amount, email, first_name, user_id, phone]):
            missing_fields = [field for field, value in [
                ('amount', amount), ('email', email), ('first_name', first_name),
                ('userId', user_id), ('phone', phone)
            ] if not value]
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # Provide default for last_name if empty
        if not last_name:
            last_name = "Player"

        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0 or amount > 100000:
                return jsonify({'error': 'Amount must be between 1 and 100,000 ETB'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400

        # Validate email format
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400

        tx_ref = f"deposit-{user_id}-{int(time.time())}"
        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone,  # <-- Pass phone to Chapa
            "tx_ref": tx_ref,
            "callback_url": f"{request.host_url}api/payment-callback",
            "return_url": f"{request.host_url}wallet",
            "customization": {
                "title": "Deposit",  # 7 characters, valid!
                "description": "Deposit funds to your wallet"
            }
        }

        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET}",
            "Content-Type": "application/json"
        }

        print(f"Sending request to Chapa: {CHAPA_BASE_URL}/transaction/initialize")
        print(f"Payload: {payload}")
        print(f"Headers: {headers}")

        response = requests.post(
            f"{CHAPA_BASE_URL}/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"Chapa Response Status: {response.status_code}")
        print(f"Chapa Response Body: {response.text}")

        if response.status_code != 200:
            error_message = f"Chapa API error (Status: {response.status_code})"
            try:
                error_json = response.json()
                error_message += f" - {error_json.get('message', 'Unknown error')}"
            except:
                error_message += f" - {response.text}"
            return jsonify({'error': error_message}), 500

        resp_json = response.json()
        if resp_json.get('status') != 'success':
            error_message = resp_json.get('message', 'Unknown Chapa error')
            return jsonify({'error': f'Chapa error: {error_message}', 'details': resp_json}), 500

        # After creating tx_ref in /api/wallet/deposit
        fs_db.collection('transactions').document(tx_ref).set({
            "userId": user_id,
            "amount": float(amount),
            "status": "pending",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "type": "deposit"
        })

        return jsonify({
            "checkout_url": resp_json['data']['checkout_url'],
            "tx_ref": tx_ref
        })

    except Exception as e:
        print(f"Deposit error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/wallet/withdraw', methods=['POST'])
def process_withdrawal():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        user_id = data.get('userId')
        amount = data.get('amount')
        phone_number = data.get('phoneNumber')
        withdrawal_method = data.get('method', 'mobile_money')  # mobile_money, bank_transfer

        print(f"Received withdrawal request: {data}")

        # Validate required fields
        if not all([user_id, amount, phone_number]):
            return jsonify({'error': 'Missing required fields: userId, amount, phoneNumber'}), 400

        # Validate amount
        try:
            amount = float(amount)
            if amount < 50:
                return jsonify({'error': 'Minimum withdrawal amount is 50 ETB'}), 400
            if amount > 50000:
                return jsonify({'error': 'Maximum withdrawal amount is 50,000 ETB'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400

        # Check user wallet balance
        wallet_ref = fs_db.collection('wallets').document(user_id)
        wallet_doc = wallet_ref.get()

        if not wallet_doc.exists():
            return jsonify({'error': 'Wallet not found'}), 404

        wallet_data = wallet_doc.to_dict()
        current_balance = wallet_data.get('balance', 0)

        if current_balance < amount:
            return jsonify({
                'error': f'Insufficient balance. Available: {current_balance} ETB, Requested: {amount} ETB'
            }), 400

        # Create withdrawal transaction
        tx_ref = f"withdrawal-{user_id}-{int(time.time())}"
        
        # Deduct amount from wallet first (reversible if withdrawal fails)
        try:
            wallet_ref.update({
                "balance": firestore.Increment(-amount),
                "updatedAt": firestore.SERVER_TIMESTAMP
            })

            # Create transaction record
            fs_db.collection('transactions').document(tx_ref).set({
                "userId": user_id,
                "amount": amount,
                "type": "withdrawal",
                "status": "pending",
                "method": withdrawal_method,
                "phoneNumber": phone_number,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "description": f"Withdrawal via {withdrawal_method}",
                "estimatedProcessingTime": "24 hours"
            })

            # In a production environment, here you would:
            # 1. Integrate with mobile money API (like M-Pesa, Telebirr)
            # 2. Process bank transfers
            # 3. Update transaction status based on external API response

            # For now, we'll simulate processing
            process_withdrawal_simulation(tx_ref, user_id, amount, phone_number)

            return jsonify({
                "success": True,
                "transactionId": tx_ref,
                "status": "pending",
                "message": "Withdrawal request submitted successfully. Processing within 24 hours.",
                "estimatedTime": "24 hours",
                "amount": amount,
                "method": withdrawal_method
            })

        except Exception as e:
            # If transaction creation fails, restore the wallet balance
            try:
                wallet_ref.update({
                    "balance": firestore.Increment(amount),
                    "updatedAt": firestore.SERVER_TIMESTAMP
                })
            except:
                pass  # Log this error in production
            
            raise e

    except Exception as e:
        print(f"Withdrawal error: {str(e)}")
        return jsonify({'error': f'Withdrawal processing failed: {str(e)}'}), 500


def process_withdrawal_simulation(tx_ref, user_id, amount, phone_number):
    """
    Simulate withdrawal processing. In production, this would integrate with:
    - Telebirr API
    - M-Pesa API
    - Bank transfer APIs
    - Other mobile money providers
    """
    try:
        # Simulate processing delay (in production this would be async)
        import threading
        import time as time_module
        
        def simulate_processing():
            # Wait 30 seconds to simulate processing
            time_module.sleep(30)
            
            try:
                # Update transaction status to completed (90% success rate simulation)
                import random
                success = random.random() > 0.1  # 90% success rate
                
                if success:
                    fs_db.collection('transactions').document(tx_ref).update({
                        "status": "completed",
                        "completedAt": firestore.SERVER_TIMESTAMP,
                        "processingNote": "Successfully transferred to mobile money account"
                    })
                    
                    # Track successful withdrawal
                    track_withdrawal_analytics(user_id, amount, "completed")
                    
                else:
                    # Failed withdrawal - refund the amount
                    fs_db.collection('transactions').document(tx_ref).update({
                        "status": "failed",
                        "failedAt": firestore.SERVER_TIMESTAMP,
                        "failureReason": "Mobile money transfer failed - account verification required"
                    })
                    
                    # Refund to wallet
                    wallet_ref = fs_db.collection('wallets').document(user_id)
                    wallet_ref.update({
                        "balance": firestore.Increment(amount),
                        "updatedAt": firestore.SERVER_TIMESTAMP
                    })
                    
                    track_withdrawal_analytics(user_id, amount, "failed")
                    
            except Exception as e:
                print(f"Withdrawal simulation error: {str(e)}")
        
        # Start background processing
        thread = threading.Thread(target=simulate_processing)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        print(f"Withdrawal simulation setup error: {str(e)}")


def track_withdrawal_analytics(user_id, amount, status):
    """Track withdrawal analytics"""
    try:
        withdrawal_data = {
            "type": "withdrawal",
            "amount": amount,
            "userId": user_id,
            "status": status,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "date": time.strftime("%Y-%m-%d"),
            "month": time.strftime("%Y-%m"),
            "year": time.strftime("%Y")
        }
        
        fs_db.collection('withdrawal_analytics').add(withdrawal_data)
        
    except Exception as e:
        print(f"Withdrawal analytics error: {str(e)}")


@app.route('/api/payment-callback', methods=['GET', 'POST'])
def payment_callback():
    try:
        data = request.json if request.method == 'POST' else request.args
        print("Received Chapa callback:", data)

        # Extract tx_ref and status from callback
        tx_ref = data.get('tx_ref')
        status = data.get('status')
        amount = float(data.get('amount', 0))

        if status == "success" and tx_ref:
            # First, get the transaction to find the userId
            transaction_ref = fs_db.collection('transactions').document(tx_ref)
            transaction_doc = transaction_ref.get()

            if transaction_doc.exists():
                transaction_data = transaction_doc.to_dict()
                user_id = transaction_data.get('userId')
                transaction_type = transaction_data.get('type', 'deposit')

                if user_id:
                    # Update transaction status
                    transaction_ref.update({
                        "status": "completed",
                        "completedAt": firestore.SERVER_TIMESTAMP,
                        "chapaResponse": data
                    })

                    if transaction_type == 'deposit':
                        # Handle deposit - add to wallet
                        wallet_ref = fs_db.collection('wallets').document(user_id)
                        wallet_doc = wallet_ref.get()

                        if wallet_doc.exists():
                            # Update existing wallet
                            wallet_ref.update({
                                "balance": firestore.Increment(amount),
                                "updatedAt": firestore.SERVER_TIMESTAMP
                            })
                        else:
                            # Create new wallet
                            wallet_ref.set({
                                "userId": user_id,
                                "balance": amount,
                                "currency": "ETB",
                                "status": "active",
                                "createdAt": firestore.SERVER_TIMESTAMP,
                                "updatedAt": firestore.SERVER_TIMESTAMP
                            })

                        # Track revenue analytics
                        track_revenue('deposit', amount, user_id, tx_ref)

                    elif transaction_type == 'game_entry':
                        # Handle game entry payment
                        game_id = transaction_data.get('gameId')
                        if game_id:
                            process_game_entry_payment(user_id, game_id, amount, tx_ref)

        return jsonify({"message": "Payment callback processed"}), 200

    except Exception as e:
        print(f"Callback error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def track_revenue(transaction_type, amount, user_id, tx_ref):
    """Track revenue for analytics"""
    try:
        revenue_data = {
            "type": transaction_type,
            "amount": amount,
            "userId": user_id,
            "transactionRef": tx_ref,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "date": time.strftime("%Y-%m-%d"),
            "month": time.strftime("%Y-%m"),
            "year": time.strftime("%Y")
        }
        
        fs_db.collection('revenue_tracking').add(revenue_data)
        
        # Update daily revenue summary
        daily_ref = fs_db.collection('daily_revenue').document(time.strftime("%Y-%m-%d"))
        daily_ref.set({
            "total_amount": firestore.Increment(amount),
            "transaction_count": firestore.Increment(1),
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        
    except Exception as e:
        print(f"Revenue tracking error: {str(e)}")

def process_game_entry_payment(user_id, game_id, amount, tx_ref):
    """Process game entry payment with house commission"""
    try:
        # Calculate house commission (10% default)
        house_commission = amount * 0.10
        prize_pool_addition = amount - house_commission
        
        # Update game prize pool
        game_ref = fs_db.collection('gameRooms').document(game_id)
        game_ref.update({
            "prizePool": firestore.Increment(prize_pool_addition)
        })
        
        # Track house revenue
        track_revenue('house_commission', house_commission, user_id, tx_ref)
        track_revenue('prize_pool', prize_pool_addition, user_id, tx_ref)
        
        print(f"Game entry processed: Prize pool +{prize_pool_addition}, House +{house_commission}")
        
    except Exception as e:
        print(f"Game entry payment error: {str(e)}")


@app.route('/api/wallet/withdrawal-status/<tx_ref>', methods=['GET'])
def check_withdrawal_status(tx_ref):
    """Check the status of a withdrawal transaction"""
    try:
        transaction_ref = fs_db.collection('transactions').document(tx_ref)
        transaction_doc = transaction_ref.get()
        
        if not transaction_doc.exists():
            return jsonify({'error': 'Transaction not found'}), 404
            
        transaction_data = transaction_doc.to_dict()
        
        # Convert timestamps to strings
        if 'createdAt' in transaction_data and transaction_data['createdAt']:
            transaction_data['createdAt'] = transaction_data['createdAt'].isoformat()
        if 'completedAt' in transaction_data and transaction_data['completedAt']:
            transaction_data['completedAt'] = transaction_data['completedAt'].isoformat()
        if 'failedAt' in transaction_data and transaction_data['failedAt']:
            transaction_data['failedAt'] = transaction_data['failedAt'].isoformat()
            
        return jsonify({
            "transaction": transaction_data,
            "status": transaction_data.get('status', 'unknown')
        })
        
    except Exception as e:
        print(f"Withdrawal status check error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/verify-payment/<tx_ref>', methods=['GET'])
def verify_payment(tx_ref):
    headers = {"Authorization": f"Bearer {CHAPA_SECRET}"}

    try:
        response = requests.get(
            f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=headers,
            timeout=30)
        
        print(f"Verification response: Status {response.status_code}, Body: {response.text}")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "Bingo Game Backend API", "status": "running"})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "bingo-backend"})

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"message": "API is working", "timestamp": time.time()})

@app.route('/api/admin/revenue', methods=['GET'])
def get_revenue_analytics():
    """Get revenue analytics (admin only)"""
    try:
        period = request.args.get('period', 'daily')  # daily, weekly, monthly
        
        if period == 'daily':
            # Get last 30 days
            revenue_docs = fs_db.collection('daily_revenue').limit(30).stream()
            
        revenue_data = []
        total_revenue = 0
        
        for doc in revenue_docs:
            data = doc.to_dict()
            revenue_data.append({
                "date": doc.id,
                "amount": data.get('total_amount', 0),
                "transactions": data.get('transaction_count', 0)
            })
            total_revenue += data.get('total_amount', 0)
        
        return jsonify({
            "revenue_data": revenue_data,
            "total_revenue": total_revenue,
            "period": period
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/withdrawal-history/<user_id>', methods=['GET'])
def get_withdrawal_history(user_id):
    """Get withdrawal history for a user"""
    try:
        # Get user's withdrawal transactions
        transactions_ref = fs_db.collection('transactions')
        query = transactions_ref.where('userId', '==', user_id).where('type', '==', 'withdrawal').order_by('createdAt', direction=firestore.Query.DESCENDING).limit(50)
        
        withdrawals = []
        for doc in query.stream():
            withdrawal_data = doc.to_dict()
            withdrawal_data['id'] = doc.id
            
            # Convert Firestore timestamps to strings
            if 'createdAt' in withdrawal_data and withdrawal_data['createdAt']:
                withdrawal_data['createdAt'] = withdrawal_data['createdAt'].isoformat()
            if 'completedAt' in withdrawal_data and withdrawal_data['completedAt']:
                withdrawal_data['completedAt'] = withdrawal_data['completedAt'].isoformat()
            if 'failedAt' in withdrawal_data and withdrawal_data['failedAt']:
                withdrawal_data['failedAt'] = withdrawal_data['failedAt'].isoformat()
                
            withdrawals.append(withdrawal_data)
        
        return jsonify({
            "withdrawals": withdrawals,
            "total_count": len(withdrawals)
        })
        
    except Exception as e:
        print(f"Withdrawal history error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/game-stats', methods=['GET'])
def get_game_statistics():
    """Get game statistics for analytics"""
    try:
        # Get active games count
        active_games = fs_db.collection('gameRooms').where('status', 'in', ['waiting', 'playing']).stream()
        active_count = len(list(active_games))
        
        # Get completed games count (last 7 days)
        week_ago = time.time() - (7 * 24 * 60 * 60)
        completed_games = fs_db.collection('gameRooms').where('status', '==', 'completed').where('createdAt', '>', week_ago).stream()
        completed_count = len(list(completed_games))
        
        # Get player statistics
        total_users = len(list(fs_db.collection('users').stream()))
        
        return jsonify({
            "active_games": active_count,
            "completed_games_week": completed_count,
            "total_users": total_users,
            "revenue_streams": {
                "game_commissions": "10% of entry fees",
                "transaction_fees": "2% of deposits",
                "premium_subscriptions": "200 ETB/month"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/join-with-payment', methods=['POST'])
def join_game_with_payment():
    """Join game with entry fee payment"""
    try:
        data = request.get_json()
        game_id = data.get('gameId')
        user_id = data.get('userId')
        player_info = data.get('playerInfo')
        
        # Get game details
        game_ref = fs_db.collection('gameRooms').document(game_id)
        game_doc = game_ref.get()
        
        if not game_doc.exists():
            return jsonify({'error': 'Game not found'}), 404
            
        game_data = game_doc.to_dict()
        entry_fee = game_data.get('entryFee', 0)
        
        if entry_fee > 0:
            # Check user wallet balance
            wallet_ref = fs_db.collection('wallets').document(user_id)
            wallet_doc = wallet_ref.get()
            
            if not wallet_doc.exists() or wallet_doc.to_dict().get('balance', 0) < entry_fee:
                return jsonify({'error': 'Insufficient wallet balance'}), 400
            
            # Deduct entry fee from wallet
            wallet_ref.update({
                "balance": firestore.Increment(-entry_fee),
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            
            # Create transaction record
            tx_ref = f"game-entry-{user_id}-{game_id}-{int(time.time())}"
            fs_db.collection('transactions').document(tx_ref).set({
                "userId": user_id,
                "gameId": game_id,
                "amount": entry_fee,
                "type": "game_entry",
                "status": "completed",
                "createdAt": firestore.SERVER_TIMESTAMP
            })
            
            # Process payment (add to prize pool with commission)
            process_game_entry_payment(user_id, game_id, entry_fee, tx_ref)
        
        # Add player to game
        game_ref.update({
            "players": firestore.ArrayUnion([player_info])
        })
        
        return jsonify({
            "success": True,
            "message": "Successfully joined game",
            "transaction_ref": tx_ref if entry_fee > 0 else None
        })
        
    except Exception as e:
        print(f"Join game error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)