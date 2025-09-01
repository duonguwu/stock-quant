"""Data fetcher using FiinQuantX API"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from loguru import logger
from FiinQuantX import FiinSession


class FiinDataFetcher:
    """Data fetcher for FiinQuantX API"""

    def __init__(self, username: str, password: str):
        """Initialize FiinQuantX session

        Args:
            username: FiinQuantX username
            password: FiinQuantX password
        """
        self.username = username
        self.password = password
        self.client = None
        self.login()

    def login(self) -> None:
        """Login to FiinQuantX"""
        try:
            self.client = FiinSession(
                username=self.username,
                password=self.password
            ).login()
            logger.info("Successfully logged in to FiinQuantX")
        except Exception as e:
            logger.error(f"Failed to login to FiinQuantX: {e}")
            raise

    def get_ticker_list(self, universe: str = "VN30") -> List[str]:
        """Get list of tickers from universe

        Args:
            universe: Universe name (VN30, VN100, etc.)

        Returns:
            List of ticker symbols
        """
        try:
            tickers = self.client.TickerList(ticker=universe)
            logger.info(f"Retrieved {len(tickers)} tickers from {universe}")
            return tickers
        except Exception as e:
            logger.error(f"Failed to get ticker list for {universe}: {e}")
            raise

    def fetch_trading_data(
        self,
        tickers: Union[str, List[str]],
        fields: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        timeframe: str = "1d",
        adjusted: bool = True
    ) -> pd.DataFrame:
        """Fetch trading data from FiinQuantX

        Args:
            tickers: Ticker symbol(s)
            fields: Data fields to fetch
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), None for current date
            timeframe: Data frequency (1d, 1h, etc.)
            adjusted: Whether to use adjusted prices

        Returns:
            DataFrame with trading data
        """
        try:
            logger.info(f"Fetching data for {tickers} from {start_date}")

            data = self.client.Fetch_Trading_Data(
                realtime=False,
                tickers=tickers,
                fields=fields,
                adjusted=adjusted,
                by=timeframe,
                from_date=start_date,
                to_date=end_date
            ).get_data()

            if data is None or data.empty:
                logger.warning("No data retrieved")
                return pd.DataFrame()

            # Convert timestamp to datetime
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])

            logger.info(f"Retrieved {len(data)} rows of data")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch trading data: {e}")
            raise

    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean fetched data

        Args:
            data: Raw trading data

        Returns:
            Cleaned data
        """
        if data.empty:
            logger.warning("Empty dataset provided for validation")
            return data

        initial_rows = len(data)

        # Remove rows with all NaN values in OHLC
        ohlc_cols = ['open', 'high', 'low', 'close']
        available_ohlc = [col for col in ohlc_cols if col in data.columns]

        if available_ohlc:
            data = data.dropna(subset=available_ohlc, how='all')

        # Basic data quality checks
        if 'high' in data.columns and 'low' in data.columns:
            # High should be >= Low
            invalid_hl = data['high'] < data['low']
            if invalid_hl.any():
                logger.warning(f"Found {invalid_hl.sum()} rows where high < low")
                data = data[~invalid_hl]

        # Remove negative prices
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in data.columns:
                negative_prices = data[col] <= 0
                if negative_prices.any():
                    logger.warning(f"Found {negative_prices.sum()} negative/zero prices in {col}")
                    data = data[~negative_prices]

        final_rows = len(data)
        removed_rows = initial_rows - final_rows

        if removed_rows > 0:
            logger.info(f"Data validation removed {removed_rows} invalid rows")

        return data

    def prepare_dataset(
        self,
        config: Dict,
        save_raw: bool = True
    ) -> pd.DataFrame:
        """Prepare complete dataset based on configuration

        Args:
            config: Data configuration dictionary
            save_raw: Whether to save raw data

        Returns:
            Prepared dataset
        """
        data_config = config.get('data', {})

        # Get tickers
        universe = data_config.get('universe', 'VN30')
        custom_tickers = data_config.get('custom_tickers')

        if custom_tickers:
            tickers = custom_tickers
            logger.info(f"Using custom ticker list: {tickers}")
        else:
            tickers = self.get_ticker_list(universe)

        # Get date range
        start_date = data_config.get('start_date', '2020-01-01')
        end_date = data_config.get('end_date')

        # Other parameters
        fields = data_config.get('fields', ['open', 'high', 'low', 'close', 'volume'])
        timeframe = data_config.get('timeframe', '1d')
        adjusted = data_config.get('adjusted', True)

        # Fetch data
        data = self.fetch_trading_data(
            tickers=tickers,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            adjusted=adjusted
        )

        # Validate data
        data = self.validate_data(data)

        if data.empty:
            logger.error("No valid data after validation")
            raise ValueError("No valid data available")

        # Save raw data
        if save_raw:
            raw_path = "data/raw/trading_data.csv"
            data.to_csv(raw_path, index=False)
            logger.info(f"Saved raw data to {raw_path}")

        return data


def create_data_fetcher(username: str, password: str) -> FiinDataFetcher:
    """Create and return FiinDataFetcher instance

    Args:
        username: FiinQuantX username
        password: FiinQuantX password

    Returns:
        FiinDataFetcher instance
    """
    return FiinDataFetcher(username, password)
