"""
Real-time Trading Dashboard
Ứng dụng real-time trading với WebSocket và MongoDB persistence
"""
from motor.motor_asyncio import AsyncIOMotorClient
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
        await data_fetcher.init_mongo()
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
        
        # Load VN-Index data AND historical stock data initially
        await load_vnindex_data()
        logger.info("✅ VN-Index data loaded")
        
        # Load historical stock data for feature calculation
        await load_initial_stock_data()
        logger.info("✅ Historical stock data loaded")
        
                # Calculate features for dashboard ready
        calculate_initial_features()
        
        # Start real-time stream if market is open
        # if data_fetcher.is_market_open():
        if True:
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


async def load_initial_stock_data():
    """Load historical stock data for feature calculation"""
    global historical_data
    
    try:
        # Define tickers to track
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        
        # Fetch historical data from 15/03/2025
        logger.info("📊 Fetching initial historical stock data...")
        hist_data = data_fetcher.fetch_historical_data(
            tickers=tickers,
            start_date="2025-03-15"
        )
        
        if len(hist_data) > 0:
            # Add to historical_data dict
            if 'vnindex' in historical_data:
                historical_data['raw_data'] = hist_data
            else:
                historical_data = {'raw_data': hist_data}
                
            logger.info(f"✅ Loaded {len(hist_data)} rows of stock data")
        else:
            logger.warning("⚠️ No historical stock data available")
            
    except Exception as e:
        logger.error(f"❌ Error loading initial stock data: {e}")


def calculate_initial_features():
    """Calculate features for dashboard from loaded historical data"""
    global historical_data, feature_engine
    
    try:
        if 'raw_data' in historical_data and len(historical_data['raw_data']) > 0:
            logger.info("🔧 Calculating initial features for dashboard...")
            
            raw_data = historical_data['raw_data']
            features_data = feature_engine.engineer_features(raw_data)
            
            historical_data['features_data'] = features_data
            logger.info(f"✅ Calculated features: {features_data.shape}")
        else:
            logger.warning("⚠️ No raw data available for feature calculation")
            
    except Exception as e:
        logger.error(f"❌ Error calculating initial features: {e}")


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
            logger.info(f"✅ Loaded last session data for "
                       f"{len(latest_bars)} tickers")
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
            global current_data
            try:
                # Update current data  
                current_data = {
                    'latest_bars': latest_bars,
                    'last_updated': datetime.now(),
                    'market_closed': False
                }
                logger.info(f"🎯 Received real-time bar:\n{latest_bars}")
                # ⚠️ CRITICAL FIX: Combine với historical data
                latest_df = pd.DataFrame([bar for bar in latest_bars.values()])
                if len(latest_df) > 0:
                    # Check if we have sufficient historical data
                    raw_data_key = 'raw_data'
                    if (raw_data_key in historical_data and
                            len(historical_data['raw_data']) > 200):
                        logger.info("🔧 Combining latest bars with historical "
                                   "data for feature calculation")
                        
                        # Combine historical + latest data
                        hist_data = historical_data['raw_data'].copy()
                        
                        # Ensure latest bars have same columns
                        required_cols = ['timestamp', 'ticker', 'open',
                                       'high', 'low', 'close', 'volume']
                        for col in required_cols:
                            if col not in latest_df.columns:
                                logger.warning(f"⚠️ Missing column {col} "
                                             f"in latest bars")
                                
                        # Add missing BU/SD if not present
                        if 'bu' not in latest_df.columns:
                            latest_df['bu'] = latest_df['volume'] * 0.3
                        if 'sd' not in latest_df.columns:
                            latest_df['sd'] = latest_df['volume'] * 0.25
                        
                        # 🔧 FIX TIMEZONE ISSUE: Normalize timestamps
                        # Convert to timezone-naive for consistency
                        if hist_data['timestamp'].dt.tz is None:
                            # Historical is already timezone-naive, good
                            pass
                        else:
                            # Convert historical to timezone-naive
                            hist_data['timestamp'] = (
                                hist_data['timestamp'].dt.tz_localize(None))
                        
                        if latest_df['timestamp'].dt.tz is not None:
                            # Convert latest to timezone-naive
                            latest_df['timestamp'] = (
                                latest_df['timestamp'].dt.tz_localize(None))
                            
                        logger.info(f"📅 Historical timestamp example: "
                                   f"{hist_data['timestamp'].iloc[0]}")
                        logger.info(f"📅 Latest timestamp example: "
                                   f"{latest_df['timestamp'].iloc[0]}")
                            
                        # Combine data
                        combined_data = pd.concat([hist_data, latest_df],
                                                ignore_index=True)
                        combined_data = combined_data.drop_duplicates(
                            subset=['ticker', 'timestamp'], keep='last'
                        ).sort_values(['ticker', 'timestamp']).reset_index(
                            drop=True)
                        
                        logger.info(f"📊 Combined data shape: "
                                   f"{combined_data.shape} (historical + "
                                   f"latest)")
                        
                        # Feature engineering với sufficient data
                        features_df = feature_engine.engineer_features(
                            combined_data)
                        
                        # Get latest features for each ticker only
                        latest_features = features_df.groupby(
                            'ticker').tail(1).reset_index(drop=True)
                        
                        logger.info(f"📊 Latest features shape: "
                                   f"{latest_features.shape}")
                        
                    else:
                        logger.error("❌ Insufficient historical data for "
                                   "feature calculation")
                        hist_data_len = len(historical_data.get('raw_data',
                                                              []))
                        logger.error(f"Historical data rows: {hist_data_len}")
                        logger.error("🚨 CANNOT CALCULATE PROPER FEATURES - "
                                   "Need ≥200 historical bars")
                        return
                    
                    # Get predictions với properly calculated features
                    if model_inference and len(latest_features) > 0:
                        tickers_list = latest_features['ticker'].tolist()
                        feature_cols = feature_engine.get_feature_list(
                            latest_features)
                        features_only = latest_features[feature_cols].fillna(0)
                        
                        logger.info(f"📊 Model input shape: "
                                   f"{features_only.shape}")
                        
                        # Get multiple confidence predictions
                        predictions = model_inference.predict_with_confidence(
                            features_only, tickers_list
                        )
                        # logger.info(f"🧠 Model predictions: {json.dumps(predictions, indent=2, default=str)}")

                        # Save signals to database for dashboard
                        try:
                            # Schedule database save in main event loop
                            def schedule_db_save():
                                asyncio.create_task(save_signals_to_database(predictions, latest_bars))
                            
                            try:
                                loop = asyncio.get_running_loop()
                                loop.call_soon_threadsafe(schedule_db_save)
                            except RuntimeError:
                                # Fallback: run in thread
                                threading.Thread(
                                    target=lambda: asyncio.run(save_signals_to_database(predictions, latest_bars))
                                ).start()
                        except Exception as db_error:
                            logger.error(f"❌ Database save error: {db_error}")
                        
                        # Send to Telegram if configured
                        if telegram_bot:
                            try:
                                await send_signals_to_telegram(
                                    predictions, latest_bars)
                            except Exception as telegram_error:
                                logger.error(f"❌ Telegram task error: {telegram_error}")
                                import traceback
                                logger.error(f"Telegram traceback: {traceback.format_exc()}")
                        
                        # Broadcast signals via WebSocket (fix timestamp serialization)
                        serializable_bars = {}
                        for ticker, bar in latest_bars.items():
                            serializable_bars[ticker] = {
                                **bar,
                                'timestamp': bar['timestamp'].isoformat() if hasattr(bar['timestamp'], 'isoformat') else str(bar['timestamp'])
                            }
                        
                        message = {
                            'type': 'realtime_signals',
                            'data': {
                                'latest_bars': serializable_bars,
                                'predictions': predictions,
                                'timestamp': datetime.now().isoformat()
                            }
                        }
                        asyncio.create_task(manager.broadcast(message))
                        
                        logger.info(f"📡 Broadcasted signals for "
                                   f"{len(latest_bars)} tickers")
                
            except Exception as e:
                logger.error(f"❌ Error in realtime callback: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Register callback and start stream
        data_fetcher.register_realtime_callback(realtime_callback)
        data_fetcher.start_realtime_stream(tickers)
        
        logger.info("🔴 Real-time pipeline started")
        
    except Exception as e:
        logger.error(f"❌ Error starting realtime pipeline: {e}")


async def save_signals_to_database(predictions: Dict, latest_bars: Dict):
    """Save signals to MongoDB for dashboard display"""
    global data_fetcher
    
    try:
        if data_fetcher is None or data_fetcher.db is None:
            logger.warning("⚠️ No database connection available")
            return
            
        signals_collection = data_fetcher.db.realtime_signals
        current_time = datetime.now()
        
        for conf_key, conf_data in predictions.items():
            signals = conf_data.get('signals', [])
            confidence_threshold = conf_data.get('confidence_threshold', 0)
            
            for signal in signals:
                if signal.get('action') != 'HOLD':
                    ticker = signal.get('ticker')
                    if ticker in latest_bars:
                        bar = latest_bars[ticker]
                        
                        signal_doc = {
                            '_id': f"{ticker}_{conf_key}_{current_time.isoformat()}",
                            'ticker': ticker,
                            'action': signal['action'],
                            'confidence': signal['confidence'],
                            'confidence_level': conf_key,
                            'confidence_threshold': confidence_threshold,
                            'price': bar.get('close', 0),
                            'volume': bar.get('volume', 0),
                            'change_pct': bar.get('change_pct', 0),
                            'timestamp': current_time,
                            'created_at': current_time
                        }
                        
                        await signals_collection.update_one(
                            {'_id': signal_doc['_id']},
                            {'$set': signal_doc},
                            upsert=True
                        )
                        
                        logger.info(f"💾 Saved {ticker} {signal['action']} signal to DB")
        
    except Exception as e:
        logger.error(f"❌ Error saving signals to database: {e}")


async def send_signals_to_telegram(predictions: Dict, latest_bars: Dict):
    """Send signals to Telegram - EXACT COPY from test_realtime_with_telegram.py"""
    try:
        logger.info(f"📱 Telegram bot min_confidence: {telegram_bot.min_confidence}")
        
        for conf_key, conf_data in predictions.items():
            confidence_threshold = conf_data.get('confidence_threshold', 0)
            
            if confidence_threshold >= telegram_bot.min_confidence:
                logger.info(f"✅ Processing {conf_key} (threshold: {confidence_threshold:.2f})")
                signals = conf_data.get('signals', [])
                
                for signal in signals:
                    if signal.get('action') != 'HOLD':
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
                            
                            logger.info(f"📱 Sending {ticker} {signal['action']} to Telegram")
                            await telegram_bot._process_individual_signal(
                                signal_enhanced, confidence_threshold
                            )
                            
    except Exception as e:
        logger.error(f"❌ Error sending to Telegram: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


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
            if len(vnindex_df) > 1:
                prev_vni = vnindex_df.iloc[-2]
            else:
                prev_vni = latest_vni
            
            change_pct = ((latest_vni['close'] - prev_vni['close']) /
                         prev_vni['close'] * 100)
            change_class = ('positive' if latest_vni['close'] >
                          prev_vni['close'] else 'negative')
            
            vnindex_info = {
                'value': f"{latest_vni['close']:.2f}",
                'change': f"{change_pct:.2f}",
                'change_class': change_class
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
                raw_predictions = model_inference.predict_with_confidence(
                    features_only, tickers)
                predictions = model_inference.format_signals_for_display(
                    raw_predictions)
                
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            predictions = {}
    
    # Latest bar data
    latest_bars = current_data.get('latest_bars', {})
    market_closed = current_data.get('market_closed', False)
    
    last_updated_time = current_data.get('last_updated', datetime.now())
    
    return {
        'market_status': market_status,
        'vnindex_info': vnindex_info,
        'predictions': predictions,
        'latest_bars': latest_bars,
        'data_status': {
            'use_real_data': True,
            'last_updated': last_updated_time.strftime('%H:%M:%S'),
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
    
    last_updated_dt = current_data.get('last_updated', datetime.now())
    
    return JSONResponse({
        'status': 'success',
        'data': {
            'current_time': current_bar_time.isoformat(),
            'is_trading_hours': data_fetcher.is_market_open(),
            'latest_bars': current_data.get('latest_bars', {}),
            'last_updated': last_updated_dt.isoformat(),
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
            
            predictions = model_inference.predict_with_confidence(
                features_only, tickers)
            formatted_predictions = model_inference.format_signals_for_display(
                predictions)
            
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
            recent_data = features_df[
                features_df['timestamp'] >= cutoff_date].copy()
            
            if len(recent_data) > 0:
                # Group by ticker and get predictions
                backtest_results = {}
                
                for ticker in recent_data['ticker'].unique():
                    ticker_data = recent_data[
                        recent_data['ticker'] == ticker].copy()
                    
                    if len(ticker_data) >= 10:
                        feature_cols = feature_engine.get_feature_list(
                            ticker_data)
                        features_only = ticker_data[feature_cols].fillna(0)
                        
                        # Get predictions for this ticker
                        predictions = model_inference.predict_with_confidence(
                            features_only, [ticker] * len(features_only)
                        )
                        
                        # Combine with price data
                        timestamps = ticker_data['timestamp'].dt.strftime(
                            '%Y-%m-%d %H:%M').tolist()
                        backtest_results[ticker] = {
                            'timestamps': timestamps,
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
            last_updated_dt = historical_data.get('last_updated',
                                                 datetime.now())
            return JSONResponse({
                'status': 'success',
                'message': 'Historical data loaded successfully',
                'data': {
                    'tickers': ['CTG', 'MBB', 'ACB', 'QNS', 'MSH'],
                    'rows': len(historical_data.get('raw_data', [])),
                    'last_updated': last_updated_dt.isoformat()
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
        features_key = 'features_data'
        raw_key = 'raw_data'
        if (raw_key not in historical_data or
                features_key not in historical_data):
            return JSONResponse({
                'status': 'error',
                'message': 'No historical data available. Please load '
                          'data first.'
            })
        
        # Filter data cho ticker
        raw_data = historical_data['raw_data']
        features_data = historical_data['features_data']
        
        ticker_raw = raw_data[raw_data['ticker'] == ticker].copy()
        ticker_features = features_data[
            features_data['ticker'] == ticker].copy()
        
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
                raw_predictions = model_inference.predict_with_confidence(
                    features_only, tickers_list)
                
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
                                price = (ticker_raw.iloc[i]['close']
                                       if i < len(ticker_raw) else 0)
                                signal_points.append({
                                    'timestamp': timestamp.isoformat(),
                                    'action': signal['action'],
                                    'confidence': signal['confidence'],
                                    'price': price
                                })
                    
                    threshold_pct = int(confidence_threshold * 100)
                    predictions_data[f"confidence_{threshold_pct}"] = {
                        'threshold': confidence_threshold,
                        'signals': signal_points,
                        'summary': conf_data['summary']
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error generating predictions for "
                           f"{ticker}: {e}")
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
        if success:
            message = 'Test message sent'
            status = 'success'
        else:
            message = 'Failed to send test message'
            status = 'failed'
            
        return JSONResponse({
            'status': status,
            'message': message
        })
    except Exception as e:
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


# Add helper function for deduplication
async def deduplicate_signals(signals_list):
    """Remove duplicate signals based on timestamp + action"""
    seen = set()
    unique_signals = []
    
    for signal in signals_list:
        # Create unique key
        key = f"{signal['timestamp']}_{signal['action']}_{signal.get('price', 0)}"
        if key not in seen:
            seen.add(key)
            unique_signals.append(signal)
    
    return unique_signals

@app.get("/api/dashboard-charts")
async def get_dashboard_charts():
    """API endpoint with deduplicated realtime signals merged"""
    global historical_data, model_inference, feature_engine, current_data
    
    try:
        if 'raw_data' not in historical_data or 'features_data' not in historical_data:
            return JSONResponse({
                'status': 'error',
                'message': 'No data available. Please load historical data first.'
            })
        
        # Lấy data 2 ngày gần nhất
        cutoff_date = datetime.now() - timedelta(days=2)
        raw_data = historical_data['raw_data']
        features_data = historical_data['features_data']
        
        # Filter data 2 ngày gần nhất
        recent_raw = raw_data[raw_data['timestamp'] >= cutoff_date].copy()
        recent_features = features_data[features_data['timestamp'] >= cutoff_date].copy()
        
        # 🔥 NEW: Kết hợp với realtime data nếu có
        if current_data and 'latest_bars' in current_data:
            latest_bars = current_data['latest_bars']
            
            # Convert latest bars to DataFrame
            latest_rows = []
            for ticker, bar in latest_bars.items():
                latest_rows.append({
                    'ticker': ticker,
                    'timestamp': bar['timestamp'],
                    'open': bar['open'],
                    'high': bar['high'], 
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume']
                })
            
            if latest_rows:
                latest_df = pd.DataFrame(latest_rows)
                recent_raw = pd.concat([recent_raw, latest_df], ignore_index=True)
                recent_raw = recent_raw.sort_values(['ticker', 'timestamp'])
                recent_raw = recent_raw.drop_duplicates(['ticker', 'timestamp'], keep='last')
        
        # Get realtime signals from database
        realtime_signals_response = {}
        try:
            if data_fetcher and data_fetcher.db:
                signals_collection = data_fetcher.db.realtime_signals
                cutoff_time = datetime.now() - timedelta(days=2)
                
                cursor = signals_collection.find({
                    'timestamp': {'$gte': cutoff_time}
                }).sort('timestamp', -1)
                
                db_signals = await cursor.to_list(length=1000)
                
                # Group and deduplicate signals
                for signal in db_signals:
                    ticker = signal['ticker']
                    conf_level = signal['confidence_level']
                    
                    if ticker not in realtime_signals_response:
                        realtime_signals_response[ticker] = {}
                    
                    if conf_level not in realtime_signals_response[ticker]:
                        realtime_signals_response[ticker][conf_level] = []
                    
                    signal_formatted = {
                        'timestamp': signal['timestamp'].strftime('%Y-%m-%d %H:%M'),
                        'action': signal['action'],
                        'confidence': signal['confidence'],
                        'price': signal['price']
                    }
                    realtime_signals_response[ticker][conf_level].append(signal_formatted)
                
                # Deduplicate signals for each ticker and confidence level
                for ticker in realtime_signals_response:
                    for conf_level in realtime_signals_response[ticker]:
                        realtime_signals_response[ticker][conf_level] = await deduplicate_signals(
                            realtime_signals_response[ticker][conf_level]
                        )
                        
                logger.info(f"📡 Loaded {len(db_signals)} realtime signals from DB")
                
        except Exception as db_error:
            logger.warning(f"⚠️ Could not load realtime signals: {db_error}")
        
        dashboard_data = {}
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        
        for ticker in tickers:
            # Get ticker data
            ticker_raw = recent_raw[recent_raw['ticker'] == ticker].copy()
            ticker_features = recent_features[recent_features['ticker'] == ticker].copy()
            
            if len(ticker_raw) == 0:
                logger.warning(f"⚠️ No raw data for {ticker}")
                continue
            
            # Prepare price data for chart
            price_data = []
            for _, row in ticker_raw.iterrows():
                price_data.append({
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)), 
                    'close': float(row.get('close', 0)),
                    'volume': int(row.get('volume', 0))
                })
            
            # Initialize signals structure
            confidence_signals = {
                'conf_0.4': {'threshold': 0.4, 'signals': [], 'total_signals': 0},
                'conf_0.5': {'threshold': 0.5, 'signals': [], 'total_signals': 0},
                'conf_0.6': {'threshold': 0.6, 'signals': [], 'total_signals': 0},
                'conf_0.7': {'threshold': 0.7, 'signals': [], 'total_signals': 0},
                'conf_0.8': {'threshold': 0.8, 'signals': [], 'total_signals': 0}
            }
            
            # 🔥 Merge realtime signals from database
            if ticker in realtime_signals_response:
                for conf_level, signals in realtime_signals_response[ticker].items():
                    if conf_level in confidence_signals:
                        confidence_signals[conf_level]['signals'] = signals
                        confidence_signals[conf_level]['total_signals'] = len(signals)
                        logger.info(f"📊 {ticker} {conf_level}: merged {len(signals)} realtime signals")
            
            # Try model inference for additional signals (nếu cần)
            if len(ticker_features) > 0 and model_inference:
                logger.info(f"🧠 Processing {ticker}: {len(ticker_features)} feature rows")
                
                try:
                    feature_cols = feature_engine.get_feature_list(ticker_features)
                    features_only = ticker_features[feature_cols].fillna(0)
                    tickers_list = [ticker] * len(features_only)
                    
                    # Get model predictions
                    predictions = model_inference.predict_with_confidence(
                        features_only, tickers_list)
                    
                    # Add model-generated signals to confidence_signals if not already present
                    for conf_level, conf_data in predictions.items():
                        signals = conf_data.get('signals', [])
                        model_signals = []
                        
                        for i, signal in enumerate(signals):
                            if signal.get('action') != 'HOLD' and i < len(ticker_features):
                                timestamp = ticker_features.iloc[i]['timestamp']
                                price = ticker_raw.iloc[i]['close'] if i < len(ticker_raw) else 0
                                
                                model_signals.append({
                                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M'),
                                    'action': signal['action'],
                                    'confidence': signal['confidence'],
                                    'price': float(price)
                                })
                        
                        # Merge with existing realtime signals
                        if conf_level in confidence_signals:
                            existing_signals = confidence_signals[conf_level]['signals']
                            combined_signals = existing_signals + model_signals
                            
                            # Deduplicate combined signals
                            deduplicated = await deduplicate_signals(combined_signals)
                            
                            confidence_signals[conf_level]['signals'] = deduplicated
                            confidence_signals[conf_level]['total_signals'] = len(deduplicated)
                            
                            logger.info(f"🔀 {ticker} {conf_level}: combined {len(existing_signals)} + {len(model_signals)} = {len(deduplicated)} signals")
                            
                except Exception as model_error:
                    logger.warning(f"⚠️ Model inference failed for {ticker}: {model_error}")
            
            dashboard_data[ticker] = {
                'price_data': price_data,
                'signals': confidence_signals,
                'data_range': {
                    'start': ticker_raw['timestamp'].min().strftime('%Y-%m-%d %H:%M'),
                    'end': ticker_raw['timestamp'].max().strftime('%Y-%m-%d %H:%M'),
                    'total_bars': len(ticker_raw)
                }
            }
        
        return JSONResponse({
            'status': 'success',
            'data': dashboard_data,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Dashboard charts API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.post("/api/refresh-data")
async def refresh_data():
    """API endpoint để refresh data từ FiinQuantX cho ngày hiện tại"""
    global data_fetcher, historical_data, feature_engine
    
    try:
        if not data_fetcher:
            return JSONResponse({
                'status': 'error',
                'message': 'Data fetcher not initialized'
            })
        
        logger.info("🔄 Refreshing data from FiinQuantX...")
        
        # Fetch fresh data từ FiinQuantX cho ngày hiện tại
        tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        fresh_data = data_fetcher.fetch_historical_data(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date
        )
        
        if len(fresh_data) > 0:
            # Update historical data với fresh data
            if 'raw_data' in historical_data:
                existing_data = historical_data['raw_data']
                # Kết hợp và loại bỏ duplicates
                combined_data = pd.concat([existing_data, fresh_data], ignore_index=True)
                combined_data = combined_data.drop_duplicates(
                    subset=['ticker', 'timestamp'], keep='last')
                combined_data = combined_data.sort_values(
                    ['ticker', 'timestamp']).reset_index(drop=True)
                historical_data['raw_data'] = combined_data
                
                # Recalculate features
                logger.info("🧮 Recalculating features...")
                features_df = feature_engine.engineer_features(combined_data)
                if len(features_df) > 0:
                    historical_data['features_data'] = features_df
                    logger.info(f"✅ Updated features: {len(features_df)} rows")
            else:
                historical_data['raw_data'] = fresh_data
                features_df = feature_engine.engineer_features(fresh_data)
                historical_data['features_data'] = features_df
            
            latest_timestamp = fresh_data['timestamp'].max()
            return JSONResponse({
                'status': 'success',
                'message': f'Data refreshed successfully',
                'data': {
                    'rows_added': len(fresh_data),
                    'latest_timestamp': latest_timestamp.strftime('%Y-%m-%d %H:%M'),
                    'tickers': tickers
                }
            })
        else:
            return JSONResponse({
                'status': 'warning',
                'message': 'No new data available from FiinQuantX'
            })
            
    except Exception as e:
        logger.error(f"❌ Refresh data error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/api/realtime-signals")
async def get_realtime_signals():
    """Get recent realtime signals from database for dashboard overlay"""
    global data_fetcher
    
    try:
        if data_fetcher is None or data_fetcher.db is None:
            return JSONResponse({
                'status': 'error',
                'message': 'No database connection available'
            })
        
        signals_collection = data_fetcher.db.realtime_signals
        
        # Get signals from last 2 days
        cutoff_time = datetime.now() - timedelta(days=2)
        
        cursor = signals_collection.find({
            'timestamp': {'$gte': cutoff_time}
        }).sort('timestamp', -1)
        
        signals = await cursor.to_list(length=1000)  # Limit to 1000 recent signals
        
        # Group by ticker and confidence level
        grouped_signals = {}
        for signal in signals:
            ticker = signal['ticker']
            conf_level = signal['confidence_level']
            
            if ticker not in grouped_signals:
                grouped_signals[ticker] = {}
            
            if conf_level not in grouped_signals[ticker]:
                grouped_signals[ticker][conf_level] = []
            
            # Format signal for frontend
            signal_formatted = {
                'timestamp': signal['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'action': signal['action'],
                'confidence': signal['confidence'],
                'price': signal['price']
            }
            grouped_signals[ticker][conf_level].append(signal_formatted)
        
        return JSONResponse({
            'status': 'success',
            'data': grouped_signals,
            'total_signals': len(signals),
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Realtime signals API error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


@app.get("/api/debug-signals")
async def debug_signals():
    """Debug endpoint để kiểm tra signal generation"""
    global historical_data, model_inference, feature_engine, current_data
    
    try:
        debug_info = {
            'historical_data_available': 'raw_data' in historical_data and 'features_data' in historical_data,
            'model_inference_available': model_inference is not None,
            'feature_engine_available': feature_engine is not None,
            'current_data_available': bool(current_data)
        }
        
        if 'raw_data' in historical_data:
            raw_data = historical_data['raw_data']
            debug_info['raw_data_rows'] = len(raw_data)
            debug_info['raw_data_latest'] = raw_data['timestamp'].max().isoformat() if len(raw_data) > 0 else 'None'
            
        if 'features_data' in historical_data:
            features_data = historical_data['features_data']
            debug_info['features_data_rows'] = len(features_data)
            debug_info['features_data_latest'] = features_data['timestamp'].max().isoformat() if len(features_data) > 0 else 'None'
            debug_info['feature_columns'] = list(features_data.columns) if len(features_data) > 0 else []
            
        if current_data:
            debug_info['current_data_keys'] = list(current_data.keys())
            if 'latest_bars' in current_data:
                debug_info['latest_bars_tickers'] = list(current_data['latest_bars'].keys())
                
        # Test model inference on a small sample
        if model_inference and 'features_data' in historical_data:
            features_data = historical_data['features_data']
            if len(features_data) > 0:
                # Get last 5 rows for testing
                test_features = features_data.tail(5).copy()
                feature_cols = feature_engine.get_feature_list(test_features)
                features_only = test_features[feature_cols].fillna(0)
                tickers_list = test_features['ticker'].tolist()
                
                predictions = model_inference.predict_with_confidence(features_only, tickers_list)
                
                debug_info['test_predictions'] = {}
                for conf_key, conf_data in predictions.items():
                    debug_info['test_predictions'][conf_key] = {
                        'threshold': conf_data['confidence_threshold'],
                        'signals_count': len(conf_data['signals']),
                        'signals_sample': conf_data['signals'][:3]  # First 3 signals
                    }
                    
        return JSONResponse({
            'status': 'success',
            'debug_info': debug_info
        })
        
    except Exception as e:
        logger.error(f"❌ Debug signals error: {e}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 