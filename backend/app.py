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
CORS(app, origins=['*'], allow_headers=['Content-Type', 'Authorization'])

CHAPA_SECRET = os.getenv("CHAPA_SECRET_KEY")

cred = credentials.Certificate("serviceAccountkey.json")  # Update path if needed
firebase_admin.initialize_app(cred)
fs_db = firestore.client()


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

                if user_id:
                    # Update transaction status
                    transaction_ref.update({
                        "status": "completed",
                        "completedAt": firestore.SERVER_TIMESTAMP
                    })

                    # Create or update wallet balance
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

        return jsonify({"message": "Payment callback processed"}), 200

    except Exception as e:
        print(f"Callback error: {str(e)}")
        return jsonify({"error": str(e)}), 500


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


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "bingo-backend"})

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"message": "API is working", "timestamp": time.time()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)