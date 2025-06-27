
# Chapa Payment Integration Guide

## Overview
This document explains how to integrate Chapa payment gateway in test mode for development and production setup.

## Test Mode Setup

### 1. Get Chapa Test Credentials
1. Go to [Chapa Developer Dashboard](https://developer.chapa.co/)
2. Sign up/Login to your account
3. Navigate to API Keys section
4. Copy your test credentials:
   - Test Secret Key (starts with `CHASECK_TEST-`)
   - Test Public Key (starts with `CHAPUBK_TEST-`)

### 2. Environment Configuration
Add these to your `.env` file:
```bash
CHAPA_SECRET_KEY=CHASECK_TEST-your-actual-test-secret-key
CHAPA_PUBLIC_KEY=CHAPUBK_TEST-your-actual-test-public-key
CHAPA_BASE_URL=https://api.chapa.co/v1
ENVIRONMENT=development
```

### 3. Test Mode Features
- **No real money**: All transactions are simulated
- **Test Cards**: Use test card numbers provided by Chapa
- **Webhook Testing**: Use ngrok or similar for local webhook testing

## API Endpoints

### 1. Initialize Payment
```
POST /v1/transaction/initialize
```

**Request Body:**
```json
{
  "amount": "100.00",
  "currency": "ETB",
  "email": "test@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "0911222333",
  "tx_ref": "unique-transaction-reference",
  "callback_url": "https://your-app.com/api/payment-callback",
  "return_url": "https://your-app.com/payment-success",
  "customization": {
    "title": "Bingo Game Payment",
    "description": "Wallet deposit"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Hosted link generated",
  "data": {
    "checkout_url": "https://checkout.chapa.co/checkout/payment/....."
  }
}
```

### 2. Verify Payment
```
GET /v1/transaction/verify/{tx_ref}
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment details retrieved",
  "data": {
    "status": "success",
    "amount": 100,
    "currency": "ETB",
    "tx_ref": "your-tx-ref",
    "charge": 2.5
  }
}
```

## Test Cards for Development

### Successful Payment Cards
- **Card Number**: 4000000000000002
- **Expiry**: Any future date
- **CVV**: Any 3 digits

### Failed Payment Cards  
- **Card Number**: 4000000000000010
- **Expiry**: Any future date
- **CVV**: Any 3 digits

## Backend Implementation

### Payment Flow
1. **User initiates deposit** → Frontend calls `/api/wallet/deposit`
2. **Backend creates Chapa transaction** → Calls Chapa initialize API
3. **User redirected to Chapa** → Completes payment on Chapa's secure page
4. **Chapa sends webhook** → Calls your `/api/payment-callback` endpoint
5. **Update wallet balance** → Add funds to user's wallet in Firestore

### Error Handling
Common errors and solutions:

#### "Authentication failed"
- Check if CHAPA_SECRET_KEY starts with `CHASECK_TEST-`
- Verify the key is correct in your environment

#### "Invalid amount"
- Amount must be numeric string
- Minimum amount: 1 ETB
- Maximum amount: Check Chapa limits

#### "Invalid callback URL"
- Must be publicly accessible HTTPS URL
- Use ngrok for local development: `ngrok http 5000`

## Webhook Configuration

### Setting Up Webhooks
1. In Chapa dashboard, go to Webhooks
2. Add your callback URL: `https://your-domain.com/api/payment-callback`
3. Select events: `charge.success`, `charge.failed`

### Webhook Security
```python
# Verify webhook signature (recommended for production)
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

## Production Deployment

### 1. Get Production Credentials
- Replace test keys with live keys from Chapa dashboard
- Live Secret Key starts with `CHASECK_LIVE-`
- Live Public Key starts with `CHAPUBK_LIVE-`

### 2. Update Environment
```bash
CHAPA_SECRET_KEY=CHASECK_LIVE-your-live-secret-key
CHAPA_PUBLIC_KEY=CHAPUBK_LIVE-your-live-public-key
ENVIRONMENT=production
```

### 3. SSL Requirements
- All callback URLs must use HTTPS
- Chapa validates SSL certificates

## Monitoring & Analytics

### Transaction Tracking
```python
# Track all payment attempts
def log_payment_attempt(user_id, amount, status):
    fs_db.collection('payment_logs').add({
        'userId': user_id,
        'amount': amount,
        'status': status,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'environment': ENVIRONMENT
    })
```

### Revenue Analytics  
- Track successful payments
- Monitor failed payment reasons
- Calculate conversion rates

## Troubleshooting

### Common Issues

1. **"Failed to initialize a certificate credential"**
   - Check Firebase service account file
   - Ensure proper JSON format
   - Verify file permissions

2. **"Chapa API timeout"**
   - Increase request timeout
   - Check network connectivity
   - Verify Chapa service status

3. **"Invalid transaction reference"**
   - Ensure tx_ref is unique
   - Use timestamp + user_id format
   - Check for special characters

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

1. **API Keys**: Never expose secret keys in frontend
2. **Webhooks**: Validate all webhook signatures  
3. **SSL**: Always use HTTPS in production
4. **Validation**: Validate all payment amounts server-side
5. **Logging**: Log all transactions for audit trail

## Support
- Chapa Documentation: https://developer.chapa.co/
- Chapa Support: support@chapa.co
- Test Environment: Use sandbox for development
