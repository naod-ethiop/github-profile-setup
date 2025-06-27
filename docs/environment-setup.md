
# Environment Setup Guide

## Required Environment Variables

### Chapa Payment Gateway (Test Mode)
```bash
CHAPA_SECRET_KEY=CHASECK_TEST-your-test-secret-key-here
CHAPA_PUBLIC_KEY=CHAPUBK_TEST-your-test-public-key-here
CHAPA_BASE_URL=https://api.chapa.co/v1
ENVIRONMENT=development
```

### Firebase Configuration
```bash
# Option 1: Use service account file (current setup)
# Place your real Firebase service account JSON in backend/serviceAccountKey.json

# Option 2: Use environment variable (recommended for production)
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project",...}'
```

## Getting Chapa Test Credentials

1. Visit [Chapa Developer Portal](https://developer.chapa.co/)
2. Create account or sign in
3. Go to Dashboard → API Keys
4. Copy your test credentials:
   - Test Secret Key (starts with `CHASECK_TEST-`)
   - Test Public Key (starts with `CHAPUBK_TEST-`)

## Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `bingo-game-39ba5`
3. Go to Project Settings → Service Accounts
4. Click "Generate new private key"
5. Download the JSON file
6. Replace the content in `backend/serviceAccountKey.json`

## Local Development Setup

1. Create `.env` file in project root
2. Add all required environment variables
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Run backend: `cd backend && python app.py`
5. Run frontend: `npm run dev`

## Testing Payment Flow

1. Start the application
2. Go to wallet page
3. Click "Deposit"
4. Enter amount (use 10 ETB for testing)
5. You'll be redirected to Chapa test checkout
6. Use test card: 4000000000000002
7. Complete payment
8. Check wallet balance update
