"""
Real Data Fetcher for Trading Signals
Chỉ lấy dữ liệu thật từ FiinQuantX API - Không mock data
"""
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Callable
import sys
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config.data_fetcher import FiinDataFetcher
from FiinQuantX import FiinSession
from pymongo import UpdateOne
logger = logging.getLogger(__name__)


def parse_realtime_row(row_str: str) -> Dict:
    """Parse một chuỗi realtime từ FiinQuant thành dict chuẩn"""
    try:
        parts = row_str.strip().split("|")
        if len(parts) < 32:
            raise ValueError("Dữ liệu không đầy đủ")

        # Parse timestamp and convert to timezone-naive for consistency
        timestamp = pd.to_datetime(parts[2])
        if timestamp.tz is not None:
            timestamp = timestamp.tz_localize(None)

        return {
            "ticker": parts[6],
            "timestamp": timestamp,
            "open": float(parts[7]) / 1000,
            "high": float(parts[8]) / 1000,
            "low": float(parts[9]) / 1000,
            "close": float(parts[12]) / 1000,  # LastPrice
            "volume": int(parts[18]),  # TotalVol
            "change_pct": float(parts[16])
        }

    except Exception as e:
        logger.error(f"❌ Lỗi parse realtime row: {e}")
        return {}


class RealDataFetcher:
    """Real-only data fetcher từ FiinQuantX"""

    def __init__(self, username: str = None, password: str = None,
                 mongodb_url: str = None):
        """
        Initialize real data fetcher

        Args:
            username: FiinQuantX username
            password: FiinQuantX password
            mongodb_url: MongoDB connection string
        """
        self.username = username or 'DSTC_19@fiinquant.vn'
        self.password = password or 'Fiinquant0606'
        self.mongodb_url = "mongodb://admin:password123@localhost:27017/trading_signals?authSource=admin"

        # FiinQuantX components
        self.client = None
        self.data_fetcher = None
        self.realtime_stream = None

        # MongoDB for persistence
        self.mongo_client = None
        self.db = None

        # Data storage
        self.latest_bars = {}
        self.historical_data = pd.DataFrame()
        self.realtime_callbacks = []

        # Initialize connections
        self._initialize_fiin_connection()
        # self._initialize_mongodb()

    async def init_mongo(self):
        """Khởi tạo MongoDB client trong đúng event loop"""
        self.mongo_client = AsyncIOMotorClient(self.mongodb_url)
        self.db = self.mongo_client["trading_signals"]
        logger.info("✅ MongoDB initialized in correct loop")

    def _initialize_fiin_connection(self):
        """Khởi tạo kết nối với FiinQuantX"""
        try:
            logger.info("🔄 Connecting to FiinQuantX...")
            self.client = FiinSession(
                username=self.username,
                password=self.password
            ).login()

            self.data_fetcher = FiinDataFetcher(
                username=self.username,
                password=self.password
            )

            logger.info("✅ FiinQuantX connection successful")

        except Exception as e:
            logger.error(f"❌ FiinQuantX connection failed: {e}")
            raise ConnectionError(f"Cannot connect to FiinQuantX: {e}")

    def _initialize_mongodb(self):
        """Khởi tạo kết nối MongoDB"""
        try:
            self.mongo_client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.mongo_client.trading_signals
            logger.info("✅ MongoDB connection successful")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB connection failed: {e}")
            logger.info("💡 Continuing without persistence")

    def get_current_15m_bar_time(self) -> datetime:
        """Lấy thời gian của 15m bar hiện tại"""
        now = datetime.now()
        minute = (now.minute // 15) * 15
        current_bar = now.replace(minute=minute, second=0, microsecond=0)
        return current_bar

    def fetch_historical_data(self,
                              tickers: List[str],
                              start_date: str = "2025-03-15",
                              end_date: str = None) -> pd.DataFrame:
        """
        Fetch historical data từ FiinQuantX

        Args:
            tickers: List các mã cổ phiếu
            start_date: Ngày bắt đầu (hard-coded 15/03/2025)
            end_date: Ngày kết thúc (default = hôm nay)

        Returns:
            DataFrame: Dữ liệu OHLCV lịch sử
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            logger.info(f"📊 Fetching historical data for {tickers} "
                        f"from {start_date} to {end_date}")

            # Fetch từ FiinQuantX
            data = self.data_fetcher.fetch_trading_data(
                tickers=tickers,
                fields=['open', 'high', 'low', 'close', 'volume'],
                start_date=start_date,
                end_date=end_date,
                timeframe='15m',
                adjusted=True
            )

            if data is None or len(data) == 0:
                logger.error("❌ No historical data received from FiinQuantX")
                return pd.DataFrame()

            # Standardize column names
            if 'timestamp' not in data.columns and 'time' in data.columns:
                data = data.rename(columns={'time': 'timestamp'})

            # Ensure timestamp is datetime
            data['timestamp'] = pd.to_datetime(data['timestamp'])

            # Sort data
            sorted_data = data.sort_values(['ticker', 'timestamp'])
            sorted_data = sorted_data.reset_index(drop=True)

            logger.info(f"✅ Fetched {len(sorted_data)} rows of "
                        f"historical data")
            self.historical_data = sorted_data

            # Save to MongoDB if available
            asyncio.create_task(self._save_historical_data(sorted_data))

            return sorted_data

        except Exception as e:
            logger.error(f"❌ Error fetching historical data: {e}")
            # Try to load from MongoDB as fallback
            try:
                return asyncio.run(
                    self._load_historical_data_from_db(tickers))
            except Exception as mongo_error:
                logger.error(f"❌ Error loading from MongoDB fallback: "
                             f"{mongo_error}")
                return pd.DataFrame()

    async def _save_historical_data(self, data: pd.DataFrame):
        """Save historical data to MongoDB"""
        if self.db is None:
            return

        try:
            # Convert to records
            records = data.to_dict('records')
            for record in records:
                timestamp_iso = record['timestamp'].isoformat()
                record['_id'] = f"{record['ticker']}_{timestamp_iso}"
                record['finalized'] = True
                record['source'] = 'historical'
                record['updated_at'] = datetime.now()
                record.setdefault('inserted_at', datetime.now())

            # Upsert to MongoDB using BulkWrite operations
            collection = self.db.historical_data
            operations = []
            for record in records:
                operations.append(
                    UpdateOne(
                        {'_id': record['_id']},
                        {'$set': record},
                        upsert=True
                    )
                )

            if operations:
                await collection.bulk_write(operations)
                logger.info(f"💾 Saved {len(operations)} historical "
                            f"records to MongoDB")

        except Exception as e:
            logger.error(f"❌ Error saving to MongoDB: {e}")

    async def upsert_historical_bar(self, bar_data: Dict,
                                    finalized: bool = False,
                                    source: str = 'realtime'):
        """Upsert một bar (15m) vào historical_data (floor 15m, có cờ finalized/source)"""
        if self.db is None or not bar_data:
            return
        try:
            ts = bar_data.get('timestamp')
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            if ts is None:
                return
            # Ensure tz-naive and floor to 15m
            if getattr(ts, 'tzinfo', None) is not None:
                ts = ts.replace(tzinfo=None)
            floored = ts.replace(minute=(ts.minute // 15) * 15,
                                 second=0, microsecond=0)

            record = {
                'ticker': bar_data.get('ticker'),
                'timestamp': floored,
                'open': float(bar_data.get('open', 0) or 0),
                'high': float(bar_data.get('high', 0) or 0),
                'low': float(bar_data.get('low', 0) or 0),
                'close': float(bar_data.get('close', 0) or 0),
                'volume': int(bar_data.get('volume', 0) or 0),
                'finalized': finalized,
                'source': source,
                'updated_at': datetime.now()
            }
            record.setdefault('inserted_at', datetime.now())
            record['_id'] = f"{record['ticker']}_{floored.isoformat()}"

            collection = self.db.historical_data
            await collection.update_one(
                {'_id': record['_id']},
                {'$set': record},
                upsert=True
            )
        except Exception as e:
            logger.error(f"❌ Upsert historical bar error: {e}")

    async def _load_historical_data_from_db(
            self, tickers: List[str]) -> pd.DataFrame:
        """Load historical data from MongoDB as fallback"""
        if self.db is None:
            return pd.DataFrame()

        try:
            logger.info("📚 Loading historical data from MongoDB...")
            collection = self.db.historical_data

            # Query data
            cursor = collection.find({
                'ticker': {'$in': tickers},
                'timestamp': {'$gte': datetime(2025, 3, 15)}
            })

            records = await cursor.to_list(length=None)

            if records:
                df = pd.DataFrame(records)
                df = df.drop('_id', axis=1)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                sorted_df = df.sort_values(['ticker', 'timestamp'])
                sorted_df = sorted_df.reset_index(drop=True)

                logger.info(f"✅ Loaded {len(sorted_df)} rows from MongoDB")
                return sorted_df
            else:
                logger.warning("⚠️ No data found in MongoDB")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ Error loading from MongoDB: {e}")
            return pd.DataFrame()

    def start_realtime_stream(self, tickers: List[str],
                              callback: Callable = None):
        """
        Start real-time data stream

        Args:
            tickers: List các mã cổ phiếu
            callback: Callback function để xử lý data
        """
        try:
            logger.info(f"🔴 Starting real-time stream for {tickers}")

            def realtime_callback(data):
                """Internal callback để xử lý real-time data"""
                try:
                    # Parse data từ FiinQuantX format
                    if hasattr(data, 'to_dataFrame'):
                        # Old format - convert to DataFrame first
                        df = data.to_dataFrame()
                        for _, row in df.iterrows():
                            ticker = row['Ticker']
                            # Parse timestamp and ensure timezone-naive
                            timestamp = pd.to_datetime(row['TradingDate'])
                            if timestamp.tz is not None:
                                timestamp = timestamp.tz_localize(None)

                            bar_data = {
                                'ticker': ticker,
                                'timestamp': timestamp,
                                'open': float(row['Open']),
                                'high': float(row['High']),
                                'low': float(row['Low']),
                                'close': float(row['Close']),
                                'volume': int(row.get('MatchVolume', 0)),
                                'change_pct': float(
                                    row.get('ChangePercent', 0)
                                )
                            }
                            self.latest_bars[ticker] = bar_data
                            # Upsert to historical (15m bucket, realtime)
                            try:
                                loop = asyncio.get_running_loop()

                                def create_task_upsert():
                                    return asyncio.create_task(
                                        self.upsert_historical_bar(bar_data, finalized=False, source='realtime')
                                    )

                                loop.call_soon_threadsafe(create_task_upsert)
                            except RuntimeError:
                                def run_async():
                                    try:
                                        asyncio.run(self.upsert_historical_bar(bar_data, finalized=False, source='realtime'))
                                    except Exception as e:
                                        logger.error(f"❌ Async upsert error: {e}")
                                threading.Thread(target=run_async).start()
                    else:
                        # New format - parse from string data
                        for row_str in data.get("data", []):
                            bar_data = parse_realtime_row(row_str)
                            if bar_data:
                                ticker = bar_data['ticker']
                                self.latest_bars[ticker] = bar_data

                                logger.info(f"📊 Updated {ticker}: "
                                            f"Close={bar_data['close']:.0f}, "
                                            f"Change="
                                            f"{bar_data['change_pct']:+.2f}%")
                                # Upsert to historical (15m bucket, realtime)
                                try:
                                    loop = asyncio.get_running_loop()

                                    def create_task_upsert2():
                                        return asyncio.create_task(
                                            self.upsert_historical_bar(bar_data, finalized=False, source='realtime')
                                        )

                                    loop.call_soon_threadsafe(create_task_upsert2)
                                except RuntimeError:
                                    def run_async2():
                                        try:
                                            asyncio.run(self.upsert_historical_bar(bar_data, finalized=False, source='realtime'))
                                        except Exception as e:
                                            logger.error(f"❌ Async upsert error: {e}")
                                    threading.Thread(target=run_async2).start()

                    # Call external callback if provided
                    if callback and self.latest_bars:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                # Try thread-safe scheduling
                                try:
                                    loop = asyncio.get_running_loop()

                                    def create_callback_task():
                                        return asyncio.create_task(
                                            callback(self.latest_bars))

                                    loop.call_soon_threadsafe(
                                        create_callback_task)
                                except RuntimeError:
                                    # Run in new thread
                                    def run_async():
                                        try:
                                            asyncio.run(
                                                callback(self.latest_bars)
                                            )
                                        except Exception as e:
                                            logger.error(
                                                f"❌ Async callback error: {e}"
                                            )

                                    thread = threading.Thread(
                                        target=run_async
                                    )
                                    thread.start()
                            else:
                                # Sync callback - call directly
                                callback(self.latest_bars)
                        except Exception as cb_error:
                            logger.error(f"❌ Callback error: {cb_error}")

                    # Call registered callbacks
                    for cb in self.realtime_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(cb):
                                # Try to get existing loop from main thread
                                try:
                                    loop = asyncio.get_running_loop()

                                    def create_cb_task():
                                        return asyncio.create_task(
                                            cb(self.latest_bars))

                                    loop.call_soon_threadsafe(create_cb_task)
                                except RuntimeError:
                                    # No running loop, schedule from thread

                                    def run_async():
                                        try:
                                            asyncio.run(cb(self.latest_bars))
                                        except Exception as e:
                                            logger.error(
                                                f"❌ Async callback error: {e}"
                                            )

                                    thread = threading.Thread(
                                        target=run_async
                                    )
                                    thread.start()
                            else:
                                cb(self.latest_bars)
                        except Exception as cb_error:
                            logger.error(
                                f"❌ Registered callback error: {cb_error}"
                            )

                except Exception as e:
                    logger.error(f"❌ Error in realtime callback: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

            # Start FiinQuantX stream
            self.realtime_stream = self.client.Trading_Data_Stream(
                tickers=tickers,
                callback=realtime_callback
            )
            self.realtime_stream.start()

            logger.info("✅ Real-time stream started successfully")

        except Exception as e:
            logger.error(f"❌ Error starting real-time stream: {e}")
            raise

    def stop_realtime_stream(self):
        """Stop real-time data stream"""
        try:
            if self.realtime_stream:
                self.realtime_stream.stop()
                logger.info("🛑 Real-time stream stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping stream: {e}")

    def register_realtime_callback(self, callback: Callable):
        """Register callback cho real-time data"""
        self.realtime_callbacks.append(callback)

    async def _save_realtime_bar(self, bar_data: Dict):
        """Save real-time bar to MongoDB"""
        if self.db is None:
            return

        try:
            if isinstance(bar_data["timestamp"], pd.Timestamp):
                bar_data["timestamp"] = bar_data["timestamp"].to_pydatetime()
            collection = self.db.realtime_bars
            timestamp_iso = bar_data['timestamp'].isoformat()
            bar_data['_id'] = f"{bar_data['ticker']}_{timestamp_iso}"

            await collection.update_one(
                {'_id': bar_data['_id']},
                {'$set': bar_data},
                upsert=True
            )

        except Exception as e:
            logger.error(f"❌ Error saving realtime bar: {e}")

    def get_latest_bars(self) -> Dict[str, Dict]:
        """Get latest bar data"""
        return self.latest_bars.copy()

    def get_historical_data(self) -> pd.DataFrame:
        """Get historical data"""
        return self.historical_data.copy()

    def get_vnindex_data(self, days: int = 30) -> pd.DataFrame:
        """
        Lấy dữ liệu VN-Index

        Args:
            days: Số ngày lấy dữ liệu

        Returns:
            DataFrame: VN-Index data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            logger.info(f"📈 Fetching VN-Index data for {days} days")

            data = self.data_fetcher.fetch_trading_data(
                tickers=['VNINDEX'],
                fields=['open', 'high', 'low', 'close', 'volume'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                timeframe='15m',
                adjusted=True
            )

            if data is None or len(data) == 0:
                logger.warning("⚠️ No VN-Index data received")
                return pd.DataFrame()

            # Standardize columns
            if 'timestamp' not in data.columns and 'time' in data.columns:
                data = data.rename(columns={'time': 'timestamp'})

            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.sort_values('timestamp').reset_index(drop=True)

            logger.info(f"✅ Fetched {len(data)} VN-Index records")
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching VN-Index: {e}")
            return pd.DataFrame()

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        weekday = now.weekday()
        # Skip weekends
        if weekday >= 5:
            return False

        # Check trading hours
        hour = now.hour
        minute = now.minute
        current_minutes = hour * 60 + minute

        # Morning session: 9:00-11:30
        morning_start = 9 * 60
        morning_end = 11 * 60 + 30

        # Afternoon session: 13:00-15:00
        afternoon_start = 13 * 60
        afternoon_end = 15 * 60

        return (morning_start <= current_minutes <= morning_end) or \
               (afternoon_start <= current_minutes <= afternoon_end)

    async def load_last_session_data(self, tickers: List[str]) -> Dict:
        """Load data from last trading session when market is closed"""
        if self.db is None:
            return {}

        try:
            logger.info("📚 Loading last session data...")

            # Get latest realtime bars
            collection = self.db.realtime_bars
            latest_bars = {}

            for ticker in tickers:
                cursor = collection.find(
                    {'ticker': ticker}
                ).sort('timestamp', -1).limit(1)

                record = await cursor.to_list(length=1)
                if record:
                    bar_data = record[0]
                    bar_data.pop('_id', None)
                    latest_bars[ticker] = bar_data

            logger.info(f"✅ Loaded last session data for "
                        f"{len(latest_bars)} tickers")
            return latest_bars

        except Exception as e:
            logger.error(f"❌ Error loading last session data: {e}")
            return {}

    def get_status(self) -> Dict:
        """Get status của data fetcher"""
        connection_status = 'Connected' if self.client else 'Disconnected'
        return {
            'connection_status': connection_status,
            'username': self.username,
            'market_open': self.is_market_open(),
            'latest_bars_count': len(self.latest_bars),
            'historical_data_rows': len(self.historical_data),
            'mongodb_connected': self.db is not None,
            'realtime_active': self.realtime_stream is not None
        }
