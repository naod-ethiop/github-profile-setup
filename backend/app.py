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

try:
    # Try to use environment variable first, fallback to JSON file
    service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
    if service_account_key:
        # Parse the JSON string from environment variable
        import json
        service_account_info = json.loads(service_account_key)
        cred = credentials.Certificate(service_account_info)
    else:
        # Fallback to JSON file
        cred = credentials.Certificate("backend/serviceAccountKey.json")
    
    firebase_admin.initialize_app(cred)
    fs_db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization error: {e}")
    # Create a mock client for development
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
    }), 200


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
        phone = data.get('phone')  # <-- Accept phone

        print(f"Received deposit request: {data}")  # Debug log

        if not all([amount, email, first_name, last_name, user_id, phone]):
            missing_fields = [field for field, value in [
                ('amount', amount), ('email', email), ('first_name', first_name),
                ('last_name', last_name), ('userId', user_id), ('phone', phone)
            ] if not value]
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400

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
                "title": "Deposit to Wallet",
                "description": "Deposit funds to your wallet"
            }
        }

        headers = {
            "Authorization": f"Bearer {CHAPA_SECRET}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.chapa.co/v1/transaction/initialize",
            json=payload,
            headers=headers
        )

        if response.status_code != 200:
            return jsonify({'error': 'Chapa API error', 'details': response.text}), 500

        resp_json = response.json()
        if resp_json.get('status') != 'success':
            return jsonify({'error': 'Chapa error', 'details': resp_json}), 500

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
        data = request.json

        # In a real app, you would:
        # 1. Validate the withdrawal request
        # 2. Check user balance
        # 3. Process the withdrawal to their account
        # 4. Update the database

        return jsonify({
            "success": True,
            "transactionId": f"WTH-{data.get('userId')}-{int(time.time())}",
            "status": "processing",
            "message": "Withdrawal request submitted successfully"
        })

    except Exception as e:
        print(f"Withdrawal error: {str(e)}")
        return jsonify({"error": str(e)}), 500


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


@app.route('/api/verify-payment/<tx_ref>', methods=['GET'])
def verify_payment(tx_ref):
    headers = {"Authorization": f"Bearer {CHAPA_SECRET}"}

    try:
        response = requests.get(
            f"https://api.chapa.co/v1/transaction/verify/{tx_ref}",
            headers=headers)
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