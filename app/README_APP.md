# 🚀 Real-time Trading Signals Dashboard

Ứng dụng dashboard real-time cho tín hiệu trading với hỗ trợ multiple strategies và Telegram alerts.

## 🎯 Features

- **Real-time Signal Generation** từ FiinQuantX API
- **Multi-Strategy Support** với 4 strategies được config sẵn
- **MongoDB Integration** cho data persistence
- **Telegram Bot** cho premium signal alerts
- **WebSocket Dashboard** với real-time updates
- **Portfolio Simulation** với multiple accounts demo
- **Modern UI** với dark theme chuyên nghiệp

## 🔧 Prerequisites

### Yêu cầu hệ thống:
- **Python 3.8+**
- **MongoDB** (đang chạy trên port 27017)
- **Redis** (đang chạy trên port 6379) 
- **FiinQuantX account** (username/password)

### Docker containers đang chạy:
```bash
# MongoDB
docker run -d --name mongo-container -p 27017:27017 mongo:latest

# Redis  
docker run -d --name redis-container -p 6379:6379 redis:7-alpine
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

### 2. Environment Configuration
Tạo file `.env` từ template:
```bash
cp .env.example .env
```

Cập nhật các values cần thiết:
```env
# FiinQuantX credentials
TRADING_FIIN_USERNAME=your_username
TRADING_FIIN_PASSWORD=your_password

# Database (đã setup sẵn)
TRADING_MONGODB_URL=mongodb://localhost:27017
TRADING_REDIS_URL=redis://localhost:6379

# Telegram (optional)
TRADING_TELEGRAM_BOT_TOKEN=your_bot_token
TRADING_TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Run Application
```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python main.py
```

### 4. Access Dashboard
Mở browser và truy cập: **http://localhost:8000**

## 📊 Dashboard Components

### 🔴 Live Market Status
- VN-Index và VN30 real-time
- Trading session status
- Active tickers count

### 📈 Strategy Performance Matrix
- **Best Performer ⭐** (conf: 0.7, hold: 72 bars) - Sharpe 39.21
- **Conservative** (conf: 0.6, hold: 36 bars) - Balanced approach
- **Aggressive** (conf: 0.4, hold: 36 bars) - High frequency
- **Ultra Conservative** (conf: 0.8, hold: 72 bars) - Very selective

### 🎯 Live Signals Feed
- Real-time BUY/SELL signals
- Confidence levels và strategy info
- Signal filtering by strategy
- Win rate tracking

### 💼 Portfolio Performance
- Multiple demo accounts
- P&L tracking real-time
- Risk metrics và drawdown
- Position management

### 🛡️ Risk Monitor
- Portfolio exposure gauge
- Real-time risk alerts
- Correlation tracking

## 🤖 Telegram Integration

### Setup Telegram Bot:
1. Create bot via [@BotFather](https://t.me/BotFather)
2. Get bot token
3. Create group chat, add bot
4. Enable Topics (nếu muốn dùng threads)
5. Get chat_id và thread_id
6. Update `.env` file

### Alert Features:
- High-confidence signals (>= 65%)
- Rate limiting (30 phút/ticker)
- Daily summary reports
- Error notifications

## 🏗️ Architecture

```
├── main.py                 # FastAPI app entry point
├── config/
│   ├── settings.py         # Environment config
│   └── strategies.yaml     # Strategy configurations
├── core/
│   ├── data_stream.py      # FiinQuantX real-time handler
│   ├── signal_engine.py    # Model inference engine
│   └── portfolio.py        # Portfolio simulation
├── services/
│   ├── database.py         # MongoDB operations
│   └── telegram_bot.py     # Telegram integration
├── api/
│   └── websocket.py        # WebSocket manager
├── templates/
│   └── dashboard.html      # Dashboard UI
└── static/
    ├── css/dashboard.css   # Styling
    └── js/                 # JavaScript
```

## 🔄 Real-time Data Flow

1. **FiinQuantX API** → Market data stream
2. **Feature Engineering** → Technical indicators
3. **Model Inference** → Multi-strategy predictions
4. **Signal Generation** → BUY/SELL/HOLD decisions
5. **WebSocket Broadcast** → Dashboard updates
6. **Telegram Alerts** → Premium signals
7. **MongoDB Storage** → Signal history

## 🎛️ Configuration

### Strategy Config (`config/strategies.yaml`):
```yaml
strategies:
  best_performer:
    name: "Best Performer ⭐"
    confidence_threshold: 0.7
    holding_period_bars: 72
    telegram_alerts: true
    primary: true
```

### Tickers (`config/settings.py`):
```python
default_tickers = ["CTG", "MBB", "ACB", "QNS", "MSH"]
```

## 📱 API Endpoints

### REST API:
- `GET /` - Dashboard page
- `GET /api/strategies` - Get all strategies
- `GET /api/signals/history` - Signal history
- `GET /api/portfolio/performance` - Portfolio metrics
- `GET /api/market/status` - Market status
- `POST /api/telegram/test` - Test Telegram
- `GET /health` - Health check

### WebSocket:
- `ws://localhost:8000/ws/signals` - Real-time updates

## 🔍 Troubleshooting

### Common Issues:

1. **MongoDB Connection Error**
   ```bash
   # Check if MongoDB is running
   docker ps | grep mongo
   ```

2. **FiinQuantX Authentication**
   ```bash
   # Verify credentials in .env
   echo $TRADING_FIIN_USERNAME
   ```

3. **Model Not Found**
   ```
   # App will use mock model for demo
   # Put real model in: models/model15/xgboost_model.pkl
   ```

4. **No Signals Generated**
   ```bash
   # Check logs for feature engineering errors
   tail -f logs/dashboard.log
   ```

### Development Mode:
```bash
# Run with debug logging
TRADING_DEBUG=true TRADING_LOG_LEVEL=DEBUG uvicorn main:app --reload
```

## 📈 Performance Notes

- **Mock Mode**: Nếu không có FiinQuantX → dùng mock data
- **Strategies**: Tất cả strategies chạy song song
- **WebSocket**: Auto-reconnect với exponential backoff
- **Database**: MongoDB với indexes optimized
- **Caching**: Redis cho real-time performance

## 🚀 Production Deployment

```bash
# Install production dependencies
pip install gunicorn

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📞 Support

- **Issues**: Check logs trong `logs/dashboard.log`
- **Performance**: Monitor WebSocket connections
- **Database**: MongoDB collections: `signals`, `portfolio_snapshots`, `market_data`

---

🎯 **Focus chính**: Bắn tín hiệu real-time với multiple strategies và Telegram alerts!

✅ **Ready to run** với MongoDB + Redis setup hiện tại của bạn! 