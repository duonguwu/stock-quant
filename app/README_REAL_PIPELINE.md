# 🚀 Real Trading Pipeline

Ứng dụng trading thật 100% - Không mock data, với WebSocket real-time và MongoDB persistence.

## ✨ Real Data Pipeline Features

- 🔴 **Real-time Stream**: FiinQuantX Trading_Data_Stream
- 📊 **Historical Data**: Fetch từ 15/03/2025 đến hiện tại
- 🔧 **Feature Engineering**: Realtime cho latest bars + historical
- 🤖 **Model Inference**: Multiple confidence levels (0.3-0.8)
- 📡 **WebSocket**: Real-time signals broadcast
- 💾 **MongoDB**: Persistence cho market closed
- 📈 **Live Chart**: VN-Index với Chart.js

## 🎯 Data Flow Pipeline

```
1. Real-time Stream (FiinQuantX) 
   ↓
2. Latest Bars + Feature Engineering
   ↓  
3. Model Prediction (Multiple Confidence)
   ↓
4. WebSocket Broadcast Signals
   ↓
5. Dashboard Real-time Update

PARALLEL:
Historical Data (15/03/2025 → Now) → Feature Engineering → Chart Display
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd app
pip install -r requirements_simple.txt
```

### 2. Start MongoDB (Optional)
```bash
# Ubuntu/Debian
sudo systemctl start mongod

# macOS  
brew services start mongodb-community

# Manual
mongod --dbpath /data/db
```

### 3. Set Environment (Optional)
```bash
export TRADING_FIIN_USERNAME="your_username"
export TRADING_FIIN_PASSWORD="your_password"
```

### 4. Run Real Pipeline
```bash
python start_real.py
```

## 📊 Real Data Components

### 1. RealDataFetcher
- **FiinQuantX Integration**: Login + Session
- **Real-time Stream**: Trading_Data_Stream callback
- **Historical Fetch**: 15m data từ 15/03/2025
- **MongoDB Persistence**: Save bars when market closed

### 2. Feature Engineering Pipeline
- **Real-time**: Process latest bars ngay khi nhận được
- **Historical**: Process 600+ bars cho visualization  
- **Technical Indicators**: EMA, SMA, MACD, RSI, Bollinger, ATR
- **Self-contained**: Không dependency external

### 3. Model Inference Real-time
- **Multiple Confidence**: 6 levels (0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
- **Real Model**: Load từ pickle file
- **Instant Prediction**: Ngay khi có new bar data
- **Signal Broadcasting**: Via WebSocket

### 4. WebSocket Real-time
- **Connection Management**: Auto-reconnect
- **Signal Broadcasting**: Latest bars + predictions
- **Heartbeat**: Keep connection alive
- **Error Handling**: Graceful disconnect/reconnect

## 🕐 Market Hours Handling

### Market Open (9:00-11:30, 13:00-15:00)
1. Start real-time stream
2. Process incoming bars
3. Feature engineering
4. Model predictions
5. WebSocket broadcast

### Market Closed
1. Load last session data từ MongoDB
2. Display historical signals
3. VN-Index chart từ historical data
4. No real-time updates

## 📁 Real Pipeline Structure

```
app/
├── main.py                    # FastAPI + WebSocket
├── data_fetcher.py           # RealDataFetcher - No mock
├── feature_engine.py         # Feature engineering
├── core/model_inference.py   # Model với multiple confidence
├── templates/dashboard.html  # WebSocket client
├── start_real.py            # Real pipeline starter
└── requirements_simple.txt  # Dependencies + motor
```

## 🔧 Configuration

### FiinQuantX Connection
```python
# In data_fetcher.py
username = 'DSTC_19@fiinquant.vn'  # Hard-coded
password = 'Fiinquant0606'          # Hard-coded
```

### MongoDB Settings
```python
# In data_fetcher.py
mongodb_url = 'mongodb://localhost:27017'
database = 'trading_signals'
collections = ['historical_data', 'realtime_bars']
```

### Historical Data Range
```python
# In main.py load_initial_data()
start_date = "2025-03-15"  # Hard-coded
end_date = datetime.now()  # Current
```

## 📡 WebSocket API

### Connection
```javascript
const socket = new WebSocket('ws://localhost:8000/ws');
```

### Message Types
```javascript
// Heartbeat
{
  "type": "heartbeat",
  "timestamp": "2025-09-16T18:00:00.000Z"
}

// Real-time Signals
{
  "type": "realtime_signals", 
  "data": {
    "latest_bars": {...},
    "predictions": {...},
    "timestamp": "2025-09-16T18:00:00.000Z"
  }
}
```

## 🎯 Key Features

### ✅ What's Included
- ✅ Real FiinQuantX data stream
- ✅ Historical data từ 15/03/2025
- ✅ Real-time feature engineering
- ✅ Multiple confidence model
- ✅ WebSocket real-time updates
- ✅ MongoDB persistence
- ✅ Market hours detection
- ✅ Auto-reconnection
- ✅ Live VN-Index chart

### ❌ What's Removed
- ❌ All mock data generation
- ❌ Fallback demo data
- ❌ Fake real-time simulation
- ❌ Random price movements
- ❌ Mock signals

## 🚨 Error Handling

### FiinQuantX Connection Fails
- App will crash with clear error message
- No fallback to mock data
- User must fix FiinQuantX credentials

### MongoDB Not Available
- App continues without persistence
- Limited last-session features
- Warning in logs

### Market Closed
- Load last session from MongoDB
- Display historical data only
- No real-time stream

## 🎨 Dashboard Real-time

- **Status Indicators**: Real/Mock data status
- **Live Bars**: Update via WebSocket
- **Multiple Confidence**: Real-time signal matrix
- **VN-Index Chart**: Live price updates
- **Connection Status**: WebSocket health

Ứng dụng hoàn toàn thật - No compromise! 🚀 