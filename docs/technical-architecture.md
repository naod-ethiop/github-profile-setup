
# Technical Architecture Documentation

## System Overview

### Technology Stack
- **Frontend**: React + TypeScript + Vite
- **Backend**: Python Flask + Firebase Admin SDK
- **Database**: Cloud Firestore (NoSQL)
- **Authentication**: Firebase Auth
- **Payments**: Chapa Payment Gateway
- **Real-time**: Firebase Realtime Database
- **Hosting**: Replit (Development/Production)

### Architecture Patterns
- **Microservices**: Modular service architecture
- **Real-time Communication**: WebSocket connections
- **Event-Driven**: Asynchronous event processing
- **Serverless Functions**: Cloud function triggers

## Frontend Architecture

### Component Structure
```
src/
├── components/          # Reusable UI components
│   ├── AuthPage.tsx    # Authentication
│   ├── GameRoom.tsx    # Game interface
│   ├── GameLobby.tsx   # Game selection
│   └── WalletPage.tsx  # Payment interface
├── services/           # Business logic
│   ├── gameService.ts  # Game operations
│   ├── walletService.ts # Payment operations
│   └── voiceService.ts # Audio features
├── contexts/           # State management
└── types/             # TypeScript definitions
```

### State Management
- **React Context**: Global application state
- **Local State**: Component-specific state
- **Firebase Listeners**: Real-time data synchronization
- **Local Storage**: User preferences and settings

### Key Services

#### Game Service
```typescript
class GameService {
  async createGameRoom(config: GameConfig): Promise<string>
  async joinGameRoom(gameId: string, player: Player): Promise<void>
  subscribeToGameRoom(gameId: string, callback: Function): Function
  checkWin(card: BingoCard): WinResult
  generateBingoCard(playerId: string): BingoCard
}
```

#### Voice Service
```typescript
class VoiceService {
  async speakBingoNumber(number: number, letter: string, language: Language)
  async speakGameEvent(event: string, language: Language)
  loadSettings(): VoiceSettings
  updateSettings(settings: Partial<VoiceSettings>)
}
```

## Backend Architecture

### API Structure
```
backend/
├── app.py              # Main Flask application
├── services/           # Business logic modules
├── models/            # Data models
├── utils/             # Utility functions
└── config/            # Configuration files
```

### Key Endpoints
- `POST /api/wallet/deposit` - Wallet deposit
- `POST /api/wallet/withdraw` - Wallet withdrawal  
- `POST /api/game/create` - Create game room
- `POST /api/game/join` - Join game room
- `POST /api/payment-callback` - Payment webhooks
- `GET /api/admin/revenue` - Revenue analytics

### Database Schema

#### Collections Structure
```javascript
// Game Rooms
gameRooms: {
  id: string,
  name: string,
  hostId: string,
  players: Player[],
  status: 'waiting' | 'playing' | 'completed',
  prizePool: number,
  calledNumbers: number[],
  createdAt: timestamp
}

// User Wallets
wallets: {
  userId: string,
  balance: number,
  currency: string,
  status: 'active' | 'suspended',
  createdAt: timestamp
}

// Transactions
transactions: {
  id: string,
  userId: string,
  amount: number,
  type: 'deposit' | 'withdrawal' | 'game_entry',
  status: 'pending' | 'completed' | 'failed',
  createdAt: timestamp
}
```

## Real-time Features

### Firebase Listeners
```typescript
// Game room updates
gameService.subscribeToGameRoom(gameId, (room) => {
  setGameRoom(room);
  if (room.currentCall !== previousCall) {
    announceNumber(room.currentCall);
  }
});

// Wallet balance updates
walletService.subscribeToWallet(userId, (wallet) => {
  setWalletBalance(wallet.balance);
});
```

### Event Broadcasting
```python
# Server-side event broadcasting
def broadcast_number_call(game_id, number):
    # Update Firestore
    game_ref.update({
        'currentCall': number,
        'calledNumbers': firestore.ArrayUnion([number])
    })
    
    # Send Telegram notification
    if game_room.get('telegramChannelId'):
        send_telegram_notification(game_room['telegramChannelId'], number)
```

## Security Implementation

### Authentication & Authorization
```typescript
// Protected route component
const ProtectedRoute: React.FC<{children: React.ReactNode}> = ({children}) => {
  const user = useAuthState(auth);
  return user ? <>{children}</> : <Navigate to="/auth" />;
};
```

### API Security
```python
# Request validation
@app.before_request
def validate_request():
    if request.endpoint and request.endpoint.startswith('admin'):
        validate_admin_token(request.headers.get('Authorization'))
```

### Data Validation
```python
# Input sanitization
def validate_deposit_request(data):
    required_fields = ['amount', 'email', 'first_name', 'last_name', 'userId']
    for field in required_fields:
        if not data.get(field):
            raise ValueError(f'Missing required field: {field}')
    
    amount = float(data['amount'])
    if amount <= 0 or amount > 100000:
        raise ValueError('Invalid amount range')
```

## Performance Optimization

### Frontend Optimization
- **Code Splitting**: Lazy loading components
- **Image Optimization**: Compressed assets
- **Caching**: Service worker implementation
- **Bundle Analysis**: Webpack bundle optimization

### Backend Optimization
- **Database Indexing**: Optimized Firestore queries
- **Caching**: Redis for frequently accessed data
- **Connection Pooling**: Efficient database connections
- **Rate Limiting**: API request throttling

### Real-time Optimization
```typescript
// Debounced updates to prevent excessive re-renders
const debouncedUpdate = useCallback(
  debounce((data) => {
    updateGameState(data);
  }, 100),
  []
);
```

## Monitoring & Analytics

### Error Tracking
```python
import logging

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.errorhandler(Exception)
def handle_error(error):
    logging.error(f"Unhandled error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500
```

### Performance Metrics
```typescript
// Frontend performance tracking
const trackPageLoad = () => {
  const loadTime = performance.now();
  analytics.track('page_load', {
    duration: loadTime,
    page: window.location.pathname
  });
};
```

### Business Analytics
```python
# Revenue tracking
def track_revenue_metrics():
    daily_revenue = calculate_daily_revenue()
    player_retention = calculate_retention_rate()
    game_completion_rate = calculate_completion_rate()
    
    store_analytics({
        'daily_revenue': daily_revenue,
        'retention_rate': player_retention,
        'completion_rate': game_completion_rate
    })
```

## Deployment Configuration

### Environment Variables
```bash
# Production environment
CHAPA_SECRET_KEY=your_chapa_secret
FIREBASE_ADMIN_SDK=path_to_service_account
TELEGRAM_BOT_TOKEN=your_bot_token
DATABASE_URL=your_firestore_url
```

### CI/CD Pipeline
```yaml
# deployment.yml
name: Deploy to Replit
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Replit
        run: |
          npm install
          npm run build
          python -m pip install -r requirements.txt
```

## Scalability Considerations

### Horizontal Scaling
- **Load Balancing**: Multiple server instances
- **Database Sharding**: Distributed data storage
- **CDN Integration**: Global content delivery
- **Microservice Architecture**: Independent service scaling

### Vertical Scaling
- **Resource Optimization**: CPU and memory usage
- **Database Optimization**: Query performance
- **Caching Strategies**: Reduced database load
- **Connection Management**: Efficient resource usage

This architecture supports thousands of concurrent players while maintaining real-time performance and data consistency.
