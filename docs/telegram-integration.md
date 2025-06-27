
# Telegram Bot Integration Guide

## Overview
This guide explains how to integrate the Bingo Game with Telegram Bot for enhanced player experience.

## Bot Setup

### 1. Create a Telegram Bot
1. Message @BotFather on Telegram
2. Send `/newbot` command
3. Choose a name and username for your bot
4. Save the bot token securely

### 2. Bot Configuration
Add your bot token to environment variables:
```bash
VITE_TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Bot Features

#### Game Notifications
- Real-time number calls
- Game start/end announcements
- Winner notifications
- Prize pool updates

#### Interactive Commands
- `/start` - Welcome message and game rules
- `/join [game_id]` - Join a specific game
- `/balance` - Check wallet balance
- `/games` - List active games
- `/help` - Show available commands

#### Webhook Setup
Configure webhook to receive updates:
```javascript
const webhookUrl = 'https://your-replit-url.replit.dev/api/telegram/webhook';
await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/setWebhook`, {
  url: webhookUrl
});
```

## Implementation Steps

### 1. Add Telegram Webhook Endpoint
```python
@app.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    # Process Telegram updates
    handle_telegram_update(update)
    return jsonify({'status': 'ok'})
```

### 2. Bot Commands Handler
```python
def handle_telegram_update(update):
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        if text.startswith('/start'):
            send_welcome_message(chat_id)
        elif text.startswith('/join'):
            handle_join_game(chat_id, text)
        # Add more command handlers
```

### 3. Channel Integration
For broadcasting to channels:
```python
def send_to_channel(channel_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': channel_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.post(url, json=payload)
```

## Game Integration Features

### 1. Number Calling
When a number is called in the game:
```python
def broadcast_number_call(game_room, number):
    if game_room.get('telegramChannelId'):
        message = f"🎯 <b>Number Called: {get_letter_for_number(number)}-{number}</b>"
        send_to_channel(game_room['telegramChannelId'], message)
```

### 2. Player Notifications
```python
def notify_players(game_room, event_type, data=None):
    for player in game_room['players']:
        if player.get('telegramChatId'):
            message = format_notification(event_type, data)
            send_message(player['telegramChatId'], message)
```

### 3. Game Invitations
```python
def send_game_invitation(channel_id, game_room):
    keyboard = {
        'inline_keyboard': [[{
            'text': '🎮 Join Game',
            'url': f'https://your-app.replit.dev/game/{game_room["id"]}'
        }]]
    }
    
    message = f"""
🎯 <b>NEW BINGO GAME!</b>
🏆 {game_room['name']}
💰 Entry: {game_room['entryFee']} ETB
👥 {len(game_room['players'])}/{game_room['maxPlayers']} players
"""
    
    send_message_with_keyboard(channel_id, message, keyboard)
```

## Revenue Integration

### 1. Subscription Channels
- Premium channels with exclusive games
- VIP notifications for high-stakes games
- Early access to special events

### 2. Referral System
```python
def handle_referral(referrer_id, new_user_id):
    # Give bonus to referrer
    add_wallet_bonus(referrer_id, REFERRAL_BONUS)
    
    # Track referral for analytics
    track_referral(referrer_id, new_user_id)
```

### 3. Bot Commands for Monetization
- `/premium` - Upgrade to premium account
- `/deposit` - Quick deposit via Telegram
- `/withdraw` - Request withdrawal

## Security Considerations

1. **Webhook Validation**: Verify Telegram webhook signatures
2. **Rate Limiting**: Implement rate limits for bot commands
3. **User Verification**: Link Telegram accounts securely
4. **Data Privacy**: Handle user data according to regulations

## Testing

1. Test bot commands in development
2. Use Telegram Bot API test environment
3. Verify webhook delivery
4. Test channel broadcasting

## Monitoring

- Track bot usage metrics
- Monitor webhook delivery success
- Log bot errors and responses
- Analyze user engagement
