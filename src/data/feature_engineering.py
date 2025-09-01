"""Feature engineering using FiinQuantX indicators"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from loguru import logger


class FeatureEngineer:
    """Feature engineering class using FiinQuantX indicators"""

    def __init__(self, client):
        """Initialize with FiinQuantX client

        Args:
            client: Authenticated FiinQuantX client
        """
        self.client = client
        self.fi = client.FiinIndicator()

    def add_technical_indicators(
        self, 
        data: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Add technical indicators to data

        Args:
            data: DataFrame with OHLC data
            config: Feature configuration

        Returns:
            DataFrame with technical indicators added
        """
        df = data.copy()

        # Get technical indicators config
        tech_config = config.get('features', {}).get('technical_indicators', {})

        # Trend indicators
        if 'ema_periods' in tech_config:
            for period in tech_config['ema_periods']:
                df[f'ema_{period}'] = self.fi.ema(df['close'], window=period)

        if 'sma_periods' in tech_config:
            for period in tech_config['sma_periods']:
                df[f'sma_{period}'] = self.fi.sma(df['close'], window=period)

        # MACD
        if 'macd' in tech_config:
            macd_config = tech_config['macd']
            fast = macd_config.get('fast', 12)
            slow = macd_config.get('slow', 26)
            signal = macd_config.get('signal', 9)

            df['macd'] = self.fi.macd(df['close'], window_fast=fast, window_slow=slow)
            df['macd_signal'] = self.fi.macd_signal(
                df['close'], window_fast=fast, window_slow=slow, window_sign=signal
            )
            df['macd_diff'] = self.fi.macd_diff(
                df['close'], window_fast=fast, window_slow=slow, window_sign=signal
            )

        # ADX
        if 'adx_period' in tech_config:
            period = tech_config['adx_period']
            df['adx'] = self.fi.adx(df['high'], df['low'], df['close'], window=period)

        # Momentum indicators
        if 'rsi_period' in tech_config:
            period = tech_config['rsi_period']
            df['rsi'] = self.fi.rsi(df['close'], window=period)

        if 'stoch_period' in tech_config:
            period = tech_config['stoch_period']
            df['stoch'] = self.fi.stoch(df['high'], df['low'], df['close'], window=period)
            df['stoch_signal'] = self.fi.stoch_signal(df['high'], df['low'], df['close'], window=period)

        # Volatility indicators
        if 'bollinger' in tech_config:
            bb_config = tech_config['bollinger']
            period = bb_config.get('period', 20)
            std_dev = bb_config.get('std_dev', 2)

            df['bb_upper'] = self.fi.bollinger_hband(df['close'], window=period, window_dev=std_dev)
            df['bb_lower'] = self.fi.bollinger_lband(df['close'], window=period, window_dev=std_dev)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        if 'atr_period' in tech_config:
            period = tech_config['atr_period']
            df['atr'] = self.fi.atr(df['high'], df['low'], df['close'], window=period)
            df['atr_ratio'] = df['atr'] / df['close']

        # Volume indicators
        if 'mfi_period' in tech_config and 'volume' in df.columns:
            period = tech_config['mfi_period']
            df['mfi'] = self.fi.mfi(df['high'], df['low'], df['close'], df['volume'], window=period)

        if 'vwap_period' in tech_config and 'volume' in df.columns:
            period = tech_config['vwap_period']
            df['vwap'] = self.fi.vwap(df['high'], df['low'], df['close'], df['volume'], window=period)
            df['vwap_ratio'] = df['close'] / df['vwap']

        # OBV
        if 'volume' in df.columns:
            df['obv'] = self.fi.obv(df['close'], df['volume'])

        logger.info(f"Added {len([col for col in df.columns if col not in data.columns])} technical indicators")
        return df

    def add_price_features(
        self, 
        data: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Add price-based features

        Args:
            data: DataFrame with price data
            config: Feature configuration

        Returns:
            DataFrame with price features added
        """
        df = data.copy()

        # Get price features config
        price_config = config.get('features', {}).get('price_features', {})

        # Returns
        if 'returns_periods' in price_config:
            for period in price_config['returns_periods']:
                df[f'return_{period}d'] = df['close'].pct_change(periods=period)

        # Volatility
        if 'volatility_window' in price_config:
            window = price_config['volatility_window']
            returns = df['close'].pct_change()
            df['volatility'] = returns.rolling(window=window).std()
            df['volatility_of_volatility'] = df['volatility'].rolling(window=window).std()

        # Volume features
        if 'volume_ratio_window' in price_config and 'volume' in df.columns:
            window = price_config['volume_ratio_window']
            df['volume_sma'] = df['volume'].rolling(window=window).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_zscore'] = (df['volume'] - df['volume_sma']) / df['volume'].rolling(window=window).std()

        # Active trading features (BU/SD from FiinQuantX)
        if 'bu' in df.columns and 'sd' in df.columns:
            df['bu_sd_ratio'] = df['bu'] / (df['sd'] + 1e-8)  # Avoid division by zero
            df['net_active_volume'] = df['bu'] - df['sd']
            df['active_volume_ratio'] = (df['bu'] - df['sd']) / (df['bu'] + df['sd'] + 1e-8)

        # Price action features
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_open_ratio'] = (df['close'] - df['open']) / df['open']

        # Gap features
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        logger.info(f"Added price-based features")
        return df

    def add_regime_features(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Add market regime features

        Args:
            data: DataFrame with price data
            config: Feature configuration

        Returns:
            DataFrame with regime features added
        """
        df = data.copy()

        # Get regime features config
        regime_config = config.get('features', {}).get('regime_features', {})

        # Trend regime
        if 'trend_window' in regime_config:
            window = regime_config['trend_window']
            df['trend_sma'] = df['close'].rolling(window=window).mean()
            df['above_trend'] = (df['close'] > df['trend_sma']).astype(int)

        # Volatility regime
        if 'volatility_regime_window' in regime_config:
            window = regime_config['volatility_regime_window']
            returns = df['close'].pct_change()
            rolling_vol = returns.rolling(window=window).std()
            vol_quantiles = rolling_vol.quantile([0.33, 0.67])

            df['vol_regime'] = pd.cut(
                rolling_vol, 
                bins=[-np.inf, vol_quantiles.iloc[0], vol_quantiles.iloc[1], np.inf],
                labels=[0, 1, 2]  # 0: low vol, 1: medium vol, 2: high vol
            ).astype(float)

        logger.info("Added market regime features")
        return df

    def add_momentum_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add additional momentum features

        Args:
            data: DataFrame with price data

        Returns:
            DataFrame with momentum features added
        """
        df = data.copy()

        # Rate of change
        for period in [5, 10, 20]:
            df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100

        # Cumulative returns
        for period in [5, 10, 20]:
            df[f'cum_return_{period}d'] = (df['close'] / df['close'].shift(period) - 1) * 100

        # Price percentile rank
        for window in [20, 50]:
            df[f'price_rank_{window}d'] = df['close'].rolling(window=window).rank(pct=True)

        logger.info("Added momentum features")
        return df

    def engineer_features(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Complete feature engineering pipeline

        Args:
            data: Raw data with OHLC
            config: Feature configuration

        Returns:
            DataFrame with all features
        """
        logger.info("Starting feature engineering...")

        def process_ticker_data(df):
            """Process features for single ticker"""
            try:
                # Add technical indicators
                df = self.add_technical_indicators(df, config)

                # Add price features
                df = self.add_price_features(df, config)

                # Add regime features
                df = self.add_regime_features(df, config)

                # Add momentum features
                df = self.add_momentum_features(df)

                return df
            except Exception as e:
                logger.error(f"Error processing ticker data: {e}")
                return df

        if 'ticker' in data.columns:
            # Process by ticker
            result = data.groupby('ticker', group_keys=False).apply(process_ticker_data)
        else:
            # Single ticker
            result = process_ticker_data(data)

        # Log feature summary
        original_cols = len(data.columns)
        new_cols = len(result.columns)
        logger.info(f"Feature engineering complete: {original_cols} -> {new_cols} columns")

        return result

    def get_feature_list(self, data: pd.DataFrame) -> List[str]:
        """Get list of feature columns (excluding target and metadata)

        Args:
            data: DataFrame with features

        Returns:
            List of feature column names
        """
        exclude_cols = [
            'ticker', 'timestamp', 'label', 'hit_time', 'hit_type', 
            'ub', 'lb', 'vbar_end'
        ]

        feature_cols = [col for col in data.columns if col not in exclude_cols]
        logger.info(f"Identified {len(feature_cols)} feature columns")

        return feature_cols


def create_feature_engineer(client) -> FeatureEngineer:
    """Create FeatureEngineer instance

    Args:
        client: Authenticated FiinQuantX client

    Returns:
        FeatureEngineer instance
    """
    return FeatureEngineer(client)
