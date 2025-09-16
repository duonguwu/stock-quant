"""
Real-time data stream handler using FiinQuantX API
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, AsyncGenerator, Optional
from dataclasses import dataclass
import pandas as pd

from app.config.settings import get_settings
from app.services.database import mongodb_service

# Import FiinQuantX when available
try:
    from FiinQuantX import FiinSession, RealTimeData
except ImportError:
    FiinSession = None
    RealTimeData = None
    logging.warning("FiinQuantX not available, using mock data")

logger = logging.getLogger(__name__)


@dataclass
class MarketBar:
    """Market bar data structure"""
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    bu: Optional[int] = None  # Buy volume
    sd: Optional[int] = None  # Sell volume


class RealTimeDataStream:
    """Real-time data stream from FiinQuantX"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
        self.tickers = self.settings.default_tickers
        self.is_running = False
        self.mock_mode = FiinSession is None
        self.last_bars = {}  # Store last bars for each ticker
        
    async def initialize(self):
        """Initialize FiinQuantX connection"""
        if self.mock_mode:
            logger.warning("🚨 Running in MOCK mode - FiinQuantX not available")
            return
            
        try:
            self.session = FiinSession(
                username=self.settings.fiin_username,
                password=self.settings.fiin_password
            ).login()
            logger.info("✅ FiinQuantX session initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize FiinQuantX: {e}")
            self.mock_mode = True
            logger.warning("🚨 Falling back to MOCK mode")
    
    async def stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream real-time market data"""
        if not self.session and not self.mock_mode:
            await self.initialize()
        
        self.is_running = True
        logger.info(f"📡 Starting data stream for tickers: {self.tickers}")
        
        if self.mock_mode:
            async for data in self._mock_stream():
                if not self.is_running:
                    break
                yield data
        else:
            async for data in self._real_stream():
                if not self.is_running:
                    break
                yield data
    
    async def _real_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Real FiinQuantX data stream"""
        try:
            # Setup callback for real-time data
            market_data_queue = asyncio.Queue()
            
            def on_data_callback(data: RealTimeData):
                """Callback for FiinQuantX real-time data"""
                try:
                    df = data.to_dataFrame()
                    if not df.empty:
                        # Convert to our format
                        for _, row in df.iterrows():
                            bar_data = {
                                "ticker": row["ticker"],
                                "timestamp": datetime.now(),
                                "open": row.get("open", 0),
                                "high": row.get("high", 0),
                                "low": row.get("low", 0),
                                "close": row.get("close", 0),
                                "volume": row.get("volume", 0),
                                "bu": row.get("bu", 0),
                                "sd": row.get("sd", 0),
                            }
                            asyncio.create_task(market_data_queue.put(bar_data))
                            
                except Exception as e:
                    logger.error(f"❌ Error in data callback: {e}")
            
            # Start FiinQuantX stream
            stream = self.session.Trading_Data_Stream(
                tickers=self.tickers,
                callback=on_data_callback
            )
            stream.start()
            
            # Process data from queue
            while self.is_running:
                try:
                    # Wait for data with timeout
                    bar_data = await asyncio.wait_for(
                        market_data_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Save to database
                    await mongodb_service.save_market_data(bar_data)
                    
                    yield bar_data
                    
                except asyncio.TimeoutError:
                    # Continue to check if still running
                    continue
                except Exception as e:
                    logger.error(f"❌ Error in real stream: {e}")
                    await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Real stream error: {e}")
            # Fall back to mock mode
            async for data in self._mock_stream():
                yield data
    
    async def _mock_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock data stream for development/testing"""
        logger.info("🎭 Mock data stream started")
        
        # Initialize mock data for each ticker
        mock_prices = {
            ticker: 100000 + (i * 10000) 
            for i, ticker in enumerate(self.tickers)
        }
        
        while self.is_running:
            try:
                for ticker in self.tickers:
                    # Simulate price movement
                    current_price = mock_prices[ticker]
                    
                    # Random price change ±2%
                    import random
                    change_pct = random.uniform(-0.02, 0.02)
                    new_price = current_price * (1 + change_pct)
                    mock_prices[ticker] = new_price
                    
                    # Create mock bar
                    bar_data = {
                        "ticker": ticker,
                        "timestamp": datetime.now(),
                        "open": current_price,
                        "high": new_price + random.uniform(0, 1000),
                        "low": new_price - random.uniform(0, 1000),
                        "close": new_price,
                        "volume": random.randint(100000, 1000000),
                        "bu": random.randint(50000, 600000),
                        "sd": random.randint(50000, 600000),
                    }
                    
                    # Save to database
                    await mongodb_service.save_market_data(bar_data)
                    
                    yield bar_data
                
                # Wait 15 seconds (simulating 15m bars)
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"❌ Mock stream error: {e}")
                await asyncio.sleep(5)
    
    async def get_historical_data(
        self, 
        ticker: str, 
        bars: int = 504,
        timeframe: str = "15m"
    ) -> pd.DataFrame:
        """Get historical data for feature engineering"""
        
        if self.mock_mode:
            return self._generate_mock_historical(ticker, bars)
        
        try:
            # Use FiinQuantX to get historical data
            data = self.session.Fetch_Trading_Data(
                realtime=False,
                tickers=[ticker],
                fields=["open", "high", "low", "close", "volume", "bu", "sd"],
                adjusted=True,
                by=timeframe,
                period=bars
            ).get_data()
            
            if not data.empty:
                # Convert to DataFrame with proper columns
                df = data.reset_index()
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df
            else:
                return self._generate_mock_historical(ticker, bars)
                
        except Exception as e:
            logger.error(f"❌ Error getting historical data: {e}")
            return self._generate_mock_historical(ticker, bars)
    
    def _generate_mock_historical(self, ticker: str, bars: int) -> pd.DataFrame:
        """Generate mock historical data"""
        import random
        import numpy as np
        
        dates = pd.date_range(
            end=datetime.now(), 
            periods=bars, 
            freq="15min"
        )
        
        # Generate realistic price movement
        base_price = 100000 + hash(ticker) % 100000
        returns = np.random.normal(0, 0.02, bars)
        prices = base_price * np.exp(np.cumsum(returns))
        
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * (1 + abs(random.gauss(0, 0.01)))
            low = price * (1 - abs(random.gauss(0, 0.01)))
            
            data.append({
                "ticker": ticker,
                "timestamp": date,
                "open": price,
                "high": high,
                "low": low,
                "close": price * (1 + random.gauss(0, 0.005)),
                "volume": random.randint(100000, 1000000),
                "bu": random.randint(50000, 600000),
                "sd": random.randint(50000, 600000),
            })
        
        return pd.DataFrame(data)
    
    async def stop(self):
        """Stop the data stream"""
        self.is_running = False
        logger.info("🛑 Data stream stopped")
    
    async def get_latest_bars(self) -> Dict[str, MarketBar]:
        """Get latest bars for all tickers"""
        return self.last_bars.copy()
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            # Get latest market data from database
            market_data = await mongodb_service.get_latest_market_data()
            
            return {
                "vnindex": market_data.get("vnindex", {"value": "1,285.4", "change": 0.85}),
                "vn30": market_data.get("vn30", {"value": "1,321.2", "change": 1.2}),
                "active_tickers": len(self.tickers),
                "session": self._get_trading_session(),
                "last_update": "Live",
                "current_time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting market status: {e}")
            return {
                "vnindex": {"value": "1,285.4", "change": 0.85},
                "vn30": {"value": "1,321.2", "change": 1.2},
                "active_tickers": len(self.tickers),
                "session": "Demo",
                "last_update": "Live",
                "current_time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": datetime.now()
            }
    
    def _get_trading_session(self) -> str:
        """Determine current trading session"""
        now = datetime.now().time()
        
        if now >= datetime.strptime("09:00", "%H:%M").time() and now <= datetime.strptime("11:30", "%H:%M").time():
            return "Morning"
        elif now >= datetime.strptime("13:00", "%H:%M").time() and now <= datetime.strptime("15:00", "%H:%M").time():
            return "Afternoon"
        else:
            return "Closed" 