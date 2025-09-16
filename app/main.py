"""
Real-time Trading Dashboard
Ứng dụng real-time trading với WebSocket và MongoDB persistence
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import pandas as pd
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta
import json
from typing import List, Dict

from app.data_fetcher import RealDataFetcher
from app.feature_engine import SimpleFeatureEngine
from app.core.model_inference import RealModelInference
from app.telegram_signal_bot import TelegramSignalBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
data_fetcher = None
feature_engine = None
model_inference = None
telegram_bot = None  # Add telegram bot
current_data = {}
historical_data = {}

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 New WebSocket connection: "
                   f"{len(self.active_connections)} total")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected: "
                   f"{len(self.active_connections)} total")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ WebSocket send error: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global data_fetcher, feature_engine, model_inference, telegram_bot
    
    logger.info("🚀 Starting Real-time Trading Dashboard...")
    
    try:
        # Initialize feature engine
        feature_engine = SimpleFeatureEngine()
        logger.info("✅ Feature engine initialized")
        
        # Initialize real model
        model_inference = RealModelInference()
        logger.info("✅ Model inference initialized")
        
        # Initialize real data fetcher
        data_fetcher = RealDataFetcher()
        logger.info("✅ Real data fetcher initialized")
        
        # Initialize Telegram bot
        try:
            telegram_bot = TelegramSignalBot(min_confidence=0.65)
            if telegram_bot.bot_token and telegram_bot.chat_id:
        logger.info("✅ Telegram bot initialized")
            else:
                logger.info("💬 Telegram bot disabled (no credentials)")
                telegram_bot = None
        except Exception as e:
            logger.warning(f"⚠️ Telegram bot initialization failed: {e}")
            telegram_bot = None
        
        # Load VN-Index data only initially
        await load_vnindex_data()
        logger.info("✅ VN-Index data loaded")
        
        # Start real-time stream if market is open
        if data_fetcher.is_market_open():
            start_realtime_pipeline()
        else:
            logger.info("🏪 Market is closed, loading last session data")
            await load_last_session_data()
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down application...")
        if data_fetcher:
            data_fetcher.stop_realtime_stream()


async def load_vnindex_data():
    """Load VN-Index data only"""
    global historical_data

    try:
        # Get VN-Index data
        logger.info("📈 Fetching VN-Index data...")
        vnindex_data = data_fetcher.get_vnindex_data(days=30)
        if len(vnindex_data) > 0:
            historical_data = {'vnindex': vnindex_data}
        else:
            historical_data = {}

    except Exception as e:
        logger.error(f"❌ Error loading VN-Index data: {e}")
        historical_data = {}


async def load_last_session_data():
    """Load data from last trading session when market is closed"""
    global current_data
    
    try:
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        latest_bars = await data_fetcher.load_last_session_data(tickers)
        
        if latest_bars:
            current_data = {
                'latest_bars': latest_bars,
                'last_updated': datetime.now(),
                'market_closed': True
            }
            logger.info(f"✅ Loaded last session data for {len(latest_bars)} tickers")
        else:
            current_data = {'demo': True, 'market_closed': True}
            
    except Exception as e:
        logger.error(f"❌ Error loading last session data: {e}")
        current_data = {'demo': True, 'market_closed': True}


def start_realtime_pipeline():
    """Start real-time data pipeline"""
    global current_data
    
    try:
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        
        async def realtime_callback(latest_bars: Dict):
            """Callback để xử lý real-time data"""
            try:
                # Update current data  
                current_data = {
                    'latest_bars': latest_bars,
                    'last_updated': datetime.now(),
                    'market_closed': False
                }
                
                # Feature engineering cho latest bars
                latest_df = pd.DataFrame([bar for bar in latest_bars.values()])
                if len(latest_df) > 0:
                    # Full feature engineering pipeline
                    features_df = feature_engine.engineer_features(latest_df)
                    
                    # Get predictions
                    if model_inference and len(features_df) > 0:
                        tickers_list = features_df['ticker'].tolist()
                        feature_cols = feature_engine.get_feature_list(features_df)
                        features_only = features_df[feature_cols].fillna(0)
                        
                        # Get multiple confidence predictions
                        predictions = model_inference.predict_with_confidence(
                            features_only, tickers_list
                        )
                        
                        # Send to Telegram if configured
                        if telegram_bot:
                            await send_signals_to_telegram(predictions, latest_bars)
                        
                        # Broadcast signals via WebSocket
                        message = {
                            'type': 'realtime_signals',
                            'data': {
                                'latest_bars': latest_bars,
                                'predictions': predictions,
                                'timestamp': datetime.now().isoformat()
                            }
                        }
                        await manager.broadcast(message)
                        
                        logger.info(f"📡 Broadcasted signals for {len(latest_bars)} tickers")
                
            except Exception as e:
                logger.error(f"❌ Error in realtime callback: {e}")
        
        # Register callback and start stream
        data_fetcher.register_realtime_callback(realtime_callback)
        data_fetcher.start_realtime_stream(tickers)
        
        logger.info("🔴 Real-time pipeline started")
        
    except Exception as e:
        logger.error(f"❌ Error starting realtime pipeline: {e}")


async def send_signals_to_telegram(predictions: Dict, latest_bars: Dict):
    """Send signals to Telegram"""
    try:
        for conf_key, conf_data in predictions.items():
            confidence_threshold = conf_data.get('confidence_threshold', 0)
            
            # Only process high confidence signals
            if confidence_threshold >= telegram_bot.min_confidence:
                signals = conf_data.get('signals', [])
                
                for signal in signals:
                    # Add price and volume info from latest bars
                    ticker = signal.get('ticker')
                    if ticker in latest_bars:
                        bar = latest_bars[ticker]
                        signal_enhanced = {
                            **signal,
                            'price': bar.get('close', 0),
                            'volume': bar.get('volume', 0),
                            'change_pct': bar.get('change_pct', 0),
                            'timestamp': datetime.now()
                        }
                        
                        await telegram_bot._process_individual_signal(
                            signal_enhanced, confidence_threshold
                        )
                        
    except Exception as e:
        logger.error(f"❌ Error sending to Telegram: {e}")


# Create FastAPI app
app = FastAPI(
    title="Real-time Trading Dashboard",
    description="Real-time trading signals với WebSocket và MongoDB",
    version="2.0.0",
    lifespan=lifespan
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/")
async def dashboard(request: Request):
    """Main dashboard page"""
    global current_data, historical_data, model_inference
    
    try:
        # Prepare dashboard data
        dashboard_data = await prepare_dashboard_data()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "page_title": "Real-time Trading Dashboard",
            **dashboard_data
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


async def prepare_dashboard_data():
    """Prepare data for dashboard"""
    global current_data, historical_data, model_inference, feature_engine
    
    # Get current time and bar info
    current_bar_time = data_fetcher.get_current_15m_bar_time()
    market_open = data_fetcher.is_market_open()
    
    # Market status
    market_status = {
        'current_time': current_bar_time.strftime('%Y-%m-%d %H:%M:%S'),
        'is_trading_hours': market_open,
        'data_source': 'Real Data' if data_fetcher else 'No Connection'
    }
    
    # VN-Index data
    vnindex_info = {}
    if 'vnindex' in historical_data:
        vnindex_df = historical_data['vnindex']
        if len(vnindex_df) > 0:
            latest_vni = vnindex_df.iloc[-1]
            prev_vni = vnindex_df.iloc[-2] if len(vnindex_df) > 1 else latest_vni
            
            vnindex_info = {
                'value': f"{latest_vni['close']:.2f}",
                'change': f"{((latest_vni['close'] - prev_vni['close']) / prev_vni['close'] * 100):.2f}",
                'change_class': 'positive' if latest_vni['close'] > prev_vni['close'] else 'negative'
            }
    
    # Get predictions với multiple confidence levels
    predictions = {}
    if 'features_data' in historical_data and model_inference:
        try:
            features_df = historical_data['features_data']
            if len(features_df) > 0:
                # Get latest features for each ticker
                latest_features = features_df.groupby('ticker').tail(1)
                tickers = latest_features['ticker'].tolist()
                
                # Remove non-feature columns
                feature_cols = feature_engine.get_feature_list(latest_features)
                features_only = latest_features[feature_cols].fillna(0)
                
                # Get predictions
                raw_predictions = model_inference.predict_with_confidence(features_only, tickers)
                predictions = model_inference.format_signals_for_display(raw_predictions)
                
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            predictions = {}
    
    # Latest bar data
    latest_bars = current_data.get('latest_bars', {})
    market_closed = current_data.get('market_closed', False)
    
    return {
        'market_status': market_status,
        'vnindex_info': vnindex_info,
        'predictions': predictions,
        'latest_bars': latest_bars,
        'data_status': {
            'use_real_data': True,
            'last_updated': current_data.get('last_updated', datetime.now()).strftime('%H:%M:%S'),
            'market_closed': market_closed
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send heartbeat every 30 seconds
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({
                'type': 'heartbeat',
                'timestamp': datetime.now().isoformat()
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


def is_trading_hours(dt: datetime) -> bool:
    """Check if current time is in trading hours"""
    weekday = dt.weekday()
    hour = dt.hour
    minute = dt.minute
    
    if weekday >= 5:
        return False
    
    current_minutes = hour * 60 + minute
    morning_start = 9 * 60
    morning_end = 11 * 60 + 30
    afternoon_start = 13 * 60
    afternoon_end = 15 * 60
    
    return (morning_start <= current_minutes <= morning_end) or \
           (afternoon_start <= current_minutes <= afternoon_end)


@app.get("/api/market/status")
async def market_status():
    """API endpoint for market status"""
    global current_data, historical_data
    
    current_bar_time = data_fetcher.get_current_15m_bar_time()
    
    return JSONResponse({
        'status': 'success',
        'data': {
            'current_time': current_bar_time.isoformat(),
            'is_trading_hours': data_fetcher.is_market_open(),
            'latest_bars': current_data.get('latest_bars', {}),
            'last_updated': current_data.get('last_updated', datetime.now()).isoformat(),
            'market_closed': current_data.get('market_closed', False)
        }
    })


@app.get("/api/predictions")
async def get_predictions():
    """API endpoint for current predictions"""
    global model_inference, feature_engine, historical_data
    
    try:
        if 'features_data' in historical_data and model_inference:
            features_df = historical_data['features_data']
            latest_features = features_df.groupby('ticker').tail(1)
            tickers = latest_features['ticker'].tolist()
            
            feature_cols = feature_engine.get_feature_list(latest_features)
            features_only = latest_features[feature_cols].fillna(0)
            
            predictions = model_inference.predict_with_confidence(features_only, tickers)
            formatted_predictions = model_inference.format_signals_for_display(predictions)
            
            return JSONResponse({
                'status': 'success',
                'data': formatted_predictions
            })
        else:
            return JSONResponse({
                'status': 'error',
                'message': 'No feature data or model available'
            })
            
    except Exception as e:
        logger.error(f"❌ Predictions API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/api/vnindex")
async def get_vnindex_data():
    """API endpoint for VN-Index chart data"""
    global historical_data
    
    try:
        if 'vnindex' in historical_data:
            vnindex_df = historical_data['vnindex']
            
            # Prepare chart data
            chart_data = []
            for _, row in vnindex_df.tail(100).iterrows():
                chart_data.append({
                    'timestamp': row['timestamp'].isoformat(),
                    'close': float(row['close']),
                    'volume': int(row.get('volume', 0))
                })
            
            return JSONResponse({
                'status': 'success',
                'data': chart_data
            })
        else:
            return JSONResponse({
                'status': 'error',
                'message': 'No VN-Index data available'
            })
            
    except Exception as e:
        logger.error(f"❌ VN-Index API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/api/backtest")
async def get_backtest_data():
    """API endpoint for historical backtest visualization"""
    global historical_data, model_inference, feature_engine
    
    try:
        if 'features_data' in historical_data and model_inference:
            # Get last week's data for backtest
            features_df = historical_data['features_data']
            
            # Get data from 7 days ago
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_data = features_df[features_df['timestamp'] >= cutoff_date].copy()
            
            if len(recent_data) > 0:
                # Group by ticker and get predictions
                backtest_results = {}
                
                for ticker in recent_data['ticker'].unique():
                    ticker_data = recent_data[recent_data['ticker'] == ticker].copy()
                    
                    if len(ticker_data) >= 10:
                        feature_cols = feature_engine.get_feature_list(ticker_data)
                        features_only = ticker_data[feature_cols].fillna(0)
                        
                        # Get predictions for this ticker
                        predictions = model_inference.predict_with_confidence(
                            features_only, [ticker] * len(features_only)
                        )
                        
                        # Combine with price data
                        backtest_results[ticker] = {
                            'timestamps': ticker_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                            'prices': ticker_data['close'].tolist(),
                            'predictions': predictions
                        }
                
                return JSONResponse({
                    'status': 'success',
                    'data': backtest_results
                })
            else:
                return JSONResponse({
                    'status': 'error',
                    'message': 'Insufficient historical data for backtest'
                })
        else:
            return JSONResponse({
                'status': 'error', 
                'message': 'No data or model available for backtest'
            })
                
    except Exception as e:
        logger.error(f"❌ Backtest API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


async def load_historical_data_endpoint():
    """
    Endpoint để load historical data từ 15/03/2025 - có thể gọi riêng
    """
    global historical_data
    
    try:
        # Define tickers to track
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        
        # Fetch historical data from 15/03/2025
        logger.info("📊 Fetching historical data from 15/03/2025...")
        hist_data = data_fetcher.fetch_historical_data(
            tickers=tickers,
            start_date="2025-03-15"
        )
        
        if len(hist_data) > 0:
            # Calculate features
            logger.info("🔧 Calculating features...")
            features_data = feature_engine.engineer_features(hist_data)
            
            # Update historical data
            historical_data.update({
                'raw_data': hist_data,
                'features_data': features_data,
                'last_updated': datetime.now()
            })
            
            logger.info(f"✅ Loaded historical data for {len(tickers)} tickers")
            return True
        else:
            logger.warning("⚠️ No historical data available")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error loading historical data: {e}")
        return False


@app.get("/api/load-historical")
async def load_historical():
    """API endpoint để load historical data từ 15/03/2025"""
    try:
        success = await load_historical_data_endpoint()
        
        if success:
            return JSONResponse({
                'status': 'success',
                'message': 'Historical data loaded successfully',
                'data': {
                    'tickers': ['CTG', 'MBB', 'ACB', 'QNS', 'MSH'],
                    'rows': len(historical_data.get('raw_data', [])),
                    'last_updated': historical_data.get('last_updated', datetime.now()).isoformat()
                }
            })
        else:
            return JSONResponse({
                'status': 'error',
                'message': 'Failed to load historical data'
            })
            
    except Exception as e:
        logger.error(f"❌ Load historical API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/charts")
async def charts_page(request: Request):
    """Charts page với 5 tabs cho các tickers"""
    try:
        return templates.TemplateResponse("charts.html", {
            "request": request,
            "page_title": "Stock Charts",
            "tickers": ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        })
        
    except Exception as e:
        logger.error(f"❌ Charts page error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@app.get("/api/chart-data/{ticker}")
async def get_chart_data(ticker: str):
    """API endpoint để lấy chart data cho một ticker cụ thể"""
    global historical_data, model_inference, feature_engine
    
    try:
        if 'raw_data' not in historical_data or 'features_data' not in historical_data:
            return JSONResponse({
                'status': 'error',
                'message': 'No historical data available. Please load data first.'
            })
        
        # Filter data cho ticker
        raw_data = historical_data['raw_data']
        features_data = historical_data['features_data']
        
        ticker_raw = raw_data[raw_data['ticker'] == ticker].copy()
        ticker_features = features_data[features_data['ticker'] == ticker].copy()
        
        if len(ticker_raw) == 0:
            return JSONResponse({
                'status': 'error',
                'message': f'No data found for ticker {ticker}'
            })
        
        # Prepare chart data
        chart_data = []
        for _, row in ticker_raw.iterrows():
            chart_data.append({
                'timestamp': row['timestamp'].isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row.get('volume', 0))
            })
        
        # Get model predictions for different confidence levels
        predictions_data = {}
        if len(ticker_features) > 0 and model_inference:
            try:
                # Get latest features
                feature_cols = feature_engine.get_feature_list(ticker_features)
                features_only = ticker_features[feature_cols].fillna(0)
                tickers_list = [ticker] * len(features_only)
                
                # Get predictions
                raw_predictions = model_inference.predict_with_confidence(features_only, tickers_list)
                
                # Format for chart display
                for conf_level, conf_data in raw_predictions.items():
                    signals = conf_data['signals']
                    confidence_threshold = conf_data['confidence_threshold']
                    
                    # Map signals to timestamps
                    signal_points = []
                    for i, signal in enumerate(signals):
                        if i < len(ticker_features):
                            timestamp = ticker_features.iloc[i]['timestamp']
                            if signal['action'] != 'HOLD':
                                signal_points.append({
                                    'timestamp': timestamp.isoformat(),
                                    'action': signal['action'],
                                    'confidence': signal['confidence'],
                                    'price': ticker_raw.iloc[i]['close'] if i < len(ticker_raw) else 0
                                })
                    
                    predictions_data[f"confidence_{int(confidence_threshold*100)}"] = {
                        'threshold': confidence_threshold,
                        'signals': signal_points,
                        'summary': conf_data['summary']
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error generating predictions for {ticker}: {e}")
                predictions_data = {}
        
        return JSONResponse({
            'status': 'success',
            'data': {
                'ticker': ticker,
                'price_data': chart_data,
                'predictions': predictions_data,
                'data_range': {
                    'start': ticker_raw['timestamp'].min().isoformat(),
                    'end': ticker_raw['timestamp'].max().isoformat(),
                    'total_bars': len(ticker_raw)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Chart data API error for {ticker}: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/api/telegram/status")
async def telegram_status():
    """API endpoint for Telegram bot status"""
    global telegram_bot
    
    if not telegram_bot:
        return JSONResponse({
            'status': 'disabled',
            'message': 'Telegram bot not configured'
        })
    
    stats = telegram_bot.get_stats()
    return JSONResponse({
        'status': 'active' if stats['bot_configured'] else 'inactive',
        'data': stats
    })


@app.post("/api/telegram/test")
async def test_telegram():
    """API endpoint to test Telegram bot"""
    global telegram_bot
    
    if not telegram_bot:
        return JSONResponse({
            'status': 'error',
            'message': 'Telegram bot not configured'
        })
    
    try:
        success = await telegram_bot.send_test_message()
        return JSONResponse({
            'status': 'success' if success else 'failed',
            'message': 'Test message sent' if success else 'Failed to send test message'
        })
    except Exception as e:
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 