"""
Simple Data Fetcher for Real-time Trading Signals
Lấy dữ liệu thật từ FiinQuantX API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Import FiinQuantX
try:
    sys.path.append('/media/duongn/New Volume/UIT/AI Challenge/DATA '
                    'DSTCDSTC/stock-quant/src')
    from data.data_fetcher import create_data_fetcher
    print("✅ Successfully imported FiinQuantX data fetcher")
except ImportError as e:
    print(f"❌ Error importing FiinQuantX: {e}")
    print("💡 Using mock data instead")


class SimpleDataFetcher:
    """Đơn giản hóa việc lấy dữ liệu từ FiinQuantX"""

    def __init__(self, username: str = None, password: str = None):
        """
        Initialize data fetcher

        Args:
            username: FiinQuantX username
            password: FiinQuantX password
        """
        self.username = username or os.getenv('TRADING_FIIN_USERNAME', 'demo')
        self.password = password or os.getenv('TRADING_FIIN_PASSWORD', 'demo')
        self.use_real_data = False
        self.data_fetcher = None

        # Thử kết nối FiinQuantX
        self._initialize_connection()

    def _initialize_connection(self):
        """Khởi tạo kết nối với FiinQuantX"""
        try:
            if self.username != 'demo' and self.password != 'demo':
                self.data_fetcher = create_data_fetcher()
                # Test connection
                test_data = self.data_fetcher.fetch_trading_data(
                    tickers=['VCB'],
                    timeframe='15m',
                    start_date='2024-01-01',
                    end_date='2024-01-02'
                )
                if len(test_data) > 0:
                    self.use_real_data = True
                    print("✅ FiinQuantX connection successful")
                else:
                    print("⚠️ FiinQuantX returned empty data, using mock mode")
            else:
                print("⚠️ No FiinQuantX credentials, using mock mode")
        except Exception as e:
            print(f"❌ FiinQuantX connection failed: {e}")
            print("💡 Falling back to mock data")

    def get_current_15m_bar_time(self) -> datetime:
        """
        Lấy thời gian của 15m bar hiện tại

        Returns:
            datetime: Thời gian bar 15m hiện tại (rounded down)
        """
        now = datetime.now()

        # Round down to nearest 15 minutes
        minute = (now.minute // 15) * 15
        current_bar = now.replace(minute=minute, second=0, microsecond=0)

        print(
            f"🕐 Current 15m bar time: {current_bar.strftime('%Y-%m-%d %H:%M:%S')}")
        return current_bar

    def calculate_lookback_period(self, bars: int = 600) -> tuple:
        """
        Tính thời gian lookback để lấy đủ 600 bars

        Args:
            bars: Số bars cần lấy (default 600)

        Returns:
            tuple: (start_date, end_date)
        """
        current_bar = self.get_current_15m_bar_time()

        # 15m bars per day: 18 bars/day (9:00-11:30 + 13:00-15:00)
        # 600 bars = ~33 trading days = ~47 calendar days
        days_needed = int(bars / 18 * 1.5)  # Add buffer for weekends

        start_date = current_bar - timedelta(days=days_needed)
        end_date = current_bar

        print(
            f"📅 Lookback period: {start_date.date()} to {end_date.date()} ({days_needed} days)")
        return start_date, end_date

    def fetch_historical_data(self,
                              tickers: List[str],
                              bars: int = 600) -> pd.DataFrame:
        """
        Lấy dữ liệu lịch sử để tính features

        Args:
            tickers: List các mã cổ phiếu
            bars: Số bars cần lấy

        Returns:
            DataFrame: Dữ liệu OHLCV lịch sử
        """
        start_date, end_date = self.calculate_lookback_period(bars)

        if self.use_real_data:
            return self._fetch_real_data(tickers, start_date, end_date)
        else:
            return self._generate_mock_data(
                tickers, start_date, end_date, bars)

    def _fetch_real_data(self,
                         tickers: List[str],
                         start_date: datetime,
                         end_date: datetime) -> pd.DataFrame:
        """Lấy dữ liệu thật từ FiinQuantX"""
        try:
            print(f"🔄 Fetching REAL data for {tickers} from FiinQuantX...")

            data = self.data_fetcher.fetch_trading_data(
                tickers=tickers,
                timeframe='15m',
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            print(f"✅ Fetched {len(data)} rows of REAL data")
            return data

        except Exception as e:
            print(f"❌ Error fetching real data: {e}")
            print("💡 Falling back to mock data")
            return self._generate_mock_data(tickers, start_date, end_date, 600)

    def _generate_mock_data(self,
                            tickers: List[str],
                            start_date: datetime,
                            end_date: datetime,
                            bars: int) -> pd.DataFrame:
        """Tạo mock data cho demo"""
        print(f"🎭 Generating MOCK data for {tickers}...")

        data = []
        base_prices = {
            'CTG': 25000,
            'MBB': 23000,
            'ACB': 21000,
            'QNS': 45000,
            'MSH': 120000}

        # Tạo timestamp sequence cho 15m bars
        current_time = start_date
        timestamps = []

        while current_time <= end_date and len(timestamps) < bars:
            # Chỉ tạo data trong giờ giao dịch
            if (9 <= current_time.hour < 11.5) or (
                    13 <= current_time.hour < 15):
                if current_time.minute in [0, 15, 30, 45]:
                    timestamps.append(current_time)
            current_time += timedelta(minutes=15)

        for ticker in tickers:
            base_price = base_prices.get(ticker, 30000)

            for i, timestamp in enumerate(timestamps):
                # Tạo price movement realistic
                trend = np.sin(i / 50) * 0.02  # Long term trend
                noise = np.random.normal(0, 0.01)  # Random noise

                price_change = trend + noise
                current_price = base_price * (1 + price_change)

                # OHLC logic
                open_price = current_price * np.random.uniform(0.995, 1.005)
                close_price = open_price * (1 + price_change)
                high_price = max(open_price, close_price) * \
                    np.random.uniform(1.0, 1.01)
                low_price = min(open_price, close_price) * \
                    np.random.uniform(0.99, 1.0)

                volume = np.random.randint(50000, 500000)

                data.append({
                    'ticker': ticker,
                    'timestamp': timestamp,
                    'open': round(open_price, -1),
                    'high': round(high_price, -1),
                    'low': round(low_price, -1),
                    'close': round(close_price, -1),
                    'volume': volume
                })

                base_price = close_price  # Update base for next iteration

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

        print(f"✅ Generated {len(df)} rows of MOCK data")
        return df

    def get_latest_bar_data(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Lấy dữ liệu bar mới nhất (real-time simulation)

        Args:
            tickers: List các mã cổ phiếu

        Returns:
            Dict: Latest bar data cho mỗi ticker
        """
        current_bar_time = self.get_current_15m_bar_time()

        latest_data = {}
        base_prices = {
            'CTG': 25000,
            'MBB': 23000,
            'ACB': 21000,
            'QNS': 45000,
            'MSH': 120000}

        for ticker in tickers:
            if self.use_real_data:
                # TODO: Implement real-time data fetch
                # For now, simulate latest bar
                pass

            # Mock latest bar
            base_price = base_prices.get(ticker, 30000)
            price_change = np.random.uniform(-0.02, 0.02)

            open_price = base_price
            close_price = open_price * (1 + price_change)
            high_price = max(open_price, close_price) * \
                np.random.uniform(1.0, 1.01)
            low_price = min(open_price, close_price) * \
                np.random.uniform(0.99, 1.0)
            volume = np.random.randint(50000, 500000)

            latest_data[ticker] = {
                'timestamp': current_bar_time,
                'open': round(open_price, -1),
                'high': round(high_price, -1),
                'low': round(low_price, -1),
                'close': round(close_price, -1),
                'volume': volume,
                'change_pct': round(price_change * 100, 2)
            }

        print(f"📊 Retrieved latest bar data for {len(latest_data)} tickers")
        return latest_data

    def get_vnindex_data(self, days: int = 30) -> pd.DataFrame:
        """
        Lấy dữ liệu VN-Index để hiển thị

        Args:
            days: Số ngày lấy dữ liệu

        Returns:
            DataFrame: VN-Index data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        if self.use_real_data:
            try:
                # Fetch real VN-Index data
                data = self.data_fetcher.fetch_trading_data(
                    tickers=['VNINDEX'],
                    timeframe='15m',
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                if len(data) > 0:
                    print(f"✅ Fetched REAL VN-Index data: {len(data)} rows")
                    return data
            except Exception as e:
                print(f"❌ Error fetching VN-Index: {e}")

        # Mock VN-Index data
        print("🎭 Generating MOCK VN-Index data...")
        dates = pd.date_range(start=start_date, end=end_date, freq='15min')

        # Filter trading hours
        trading_dates = []
        for date in dates:
            if (9 <= date.hour < 11.5) or (13 <= date.hour < 15):
                if date.minute in [0, 15, 30, 45]:
                    trading_dates.append(date)

        base_value = 1250  # VN-Index around 1250
        data = []

        for i, timestamp in enumerate(trading_dates):
            trend = np.sin(i / 100) * 0.01  # Gentle trend
            noise = np.random.normal(0, 0.005)  # Market noise

            change = trend + noise
            current_value = base_value * (1 + change)

            open_val = current_value * np.random.uniform(0.998, 1.002)
            close_val = open_val * (1 + change)
            high_val = max(open_val, close_val) * np.random.uniform(1.0, 1.005)
            low_val = min(open_val, close_val) * np.random.uniform(0.995, 1.0)

            data.append({
                'ticker': 'VNINDEX',
                'timestamp': timestamp,
                'open': round(open_val, 2),
                'high': round(high_val, 2),
                'low': round(low_val, 2),
                'close': round(close_val, 2),
                'volume': np.random.randint(1000000, 5000000)
            })

            base_value = close_val

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        print(f"✅ Generated {len(df)} rows of VN-Index data")
        return df

    def get_status(self) -> Dict:
        """Lấy status của data fetcher"""
        return {
            'use_real_data': self.use_real_data,
            'connection_status': 'Connected' if self.use_real_data else 'Mock Mode',
            'username': self.username if self.use_real_data else 'demo',
            'current_bar_time': self.get_current_15m_bar_time().isoformat()}
