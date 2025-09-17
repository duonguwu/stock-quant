"""
Simple Feature Engineering for Real-time Signals
Copy từ src/data/feature_engineering.py và đơn giản hóa
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

# Import original feature engineering
try:
    sys.path.append(
        '/media/duongn/New Volume/UIT/AI Challenge/DATA DSTCDSTC/stock-quant/src')
    from data.feature_engineering import FeatureEngineer as OriginalFeatureEngineer
    print("✅ Successfully imported original FeatureEngineer")
except ImportError as e:
    print(f"❌ Error importing FeatureEngineer: {e}")
    print("💡 Using simplified version")


class SimpleFeatureEngine:
    """Đơn giản hóa feature engineering cho real-time inference"""

    def __init__(self):
        """Initialize simple feature engine"""
        self.original_engine = None
        self.use_original = False

        # Try to use original feature engine
        try:
            if 'OriginalFeatureEngineer' in globals():
                # Mock client for feature engine
                class MockClient:
                    def FiinIndicator(self):
                        return MockIndicator()

                class MockIndicator:
                    def ema(
                        self, series, window): return series.ewm(
                        span=window).mean()

                    def sma(
                        self,
                        series,
                        window): return series.rolling(window).mean()

                    def rsi(
                        self,
                        series,
                        window): return self._calculate_rsi(
                        series,
                        window)

                    def macd(self, series, **kwargs): return series.ewm(
                        span=12).mean() - series.ewm(span=26).mean()

                    def macd_signal(
                        self, series, **kwargs): return self.macd(series).ewm(span=9).mean()

                    def macd_diff(
                        self, series, **kwargs): return self.macd(series) - self.macd_signal(series)

                    def atr(
                        self,
                        high,
                        low,
                        close,
                        window): return self._calculate_atr(
                        high,
                        low,
                        close,
                        window)

                    def bollinger_hband(self, series, window, window_dev):
                        sma = series.rolling(window).mean()
                        std = series.rolling(window).std()
                        return sma + (std * window_dev)

                    def bollinger_lband(self, series, window, window_dev):
                        sma = series.rolling(window).mean()
                        std = series.rolling(window).std()
                        return sma - (std * window_dev)

                    def stoch(
                        self,
                        high,
                        low,
                        close,
                        window): return self._calculate_stoch(
                        high,
                        low,
                        close,
                        window)

                    def stoch_signal(
                        self, high, low, close, window): return self.stoch(
                        high, low, close, window).rolling(3).mean()

                    def adx(
                        self, high, low, close, window): return pd.Series(
                        50, index=close.index)  # Mock ADX

                    def mfi(
                        self,
                        high,
                        low,
                        close,
                        volume,
                        window): return pd.Series(
                        50,
                        index=close.index)  # Mock MFI

                    def vwap(self, high, low, close, volume, window): return (
                        close * volume).rolling(window).sum() / volume.rolling(window).sum()

                    def obv(
                        self,
                        close,
                        volume): return (
                        volume *
                        close.diff().apply(
                            lambda x: 1 if x > 0 else -
                            1 if x < 0 else 0)).cumsum()

                    def _calculate_rsi(self, series, window):
                        delta = series.diff()
                        gain = (
                            delta.where(
                                delta > 0,
                                0)).rolling(
                            window=window).mean()
                        loss = (-delta.where(delta < 0, 0)
                                ).rolling(window=window).mean()
                        rs = gain / loss
                        return 100 - (100 / (1 + rs))

                    def _calculate_atr(self, high, low, close, window):
                        tr1 = high - low
                        tr2 = abs(high - close.shift())
                        tr3 = abs(low - close.shift())
                        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                        return tr.rolling(window).mean()

                    def _calculate_stoch(self, high, low, close, window):
                        lowest_low = low.rolling(window).min()
                        highest_high = high.rolling(window).max()
                        return 100 * (close - lowest_low) / \
                            (highest_high - lowest_low)

                mock_client = MockClient()
                self.original_engine = OriginalFeatureEngineer(mock_client)
                self.use_original = True
                print("✅ Using original FeatureEngineer with mock client")
        except Exception as e:
            print(f"⚠️ Cannot use original engine: {e}")
            print("💡 Using simplified feature engineering")

    def create_feature_config(self) -> Dict:
        """Tạo config cho feature engineering (15m timeframe)"""
        return {
            'features': {
                'technical_indicators': {
                    'ema_periods': [20, 40, 80],  # Scaled for 15m
                    'sma_periods': [20, 40, 80],
                    'rsi_period': 56,  # 14 * 4 = 56 for 15m
                    'macd': {'fast': 48, 'slow': 104, 'signal': 36},  # Scaled
                    'bollinger': {'period': 80, 'std_dev': 2},
                    'atr_period': 56,
                    'stoch_period': 56,
                    'adx_period': 56,
                    'mfi_period': 56,
                    'vwap_period': 80
                },
                'price_features': {
                    'returns_periods': [1, 4, 18],  # 1 bar, 1h, 1 day
                    'volatility_window': 72,  # ~4 hours
                    'volume_ratio_window': 36  # ~2 hours
                },
                'regime_features': {
                    'trend_window': 144,  # ~8 hours
                    'volatility_regime_window': 72
                }
            }
        }

    def process_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Xử lý features cho data

        Args:
            data: Raw OHLCV data

        Returns:
            DataFrame: Data với features đã tính
        """
        if self.use_original and self.original_engine:
            try:
                config = self.create_feature_config()
                features_df = self.original_engine.engineer_features(
                    data, config)
                print(
                    f"✅ Original engine: {len(data.columns)} → {len(features_df.columns)} columns")
                return features_df
            except Exception as e:
                print(f"❌ Original engine failed: {e}")
                print("💡 Falling back to simplified features")

        # Simplified feature engineering
        return self._create_simplified_features(data)

    def _create_simplified_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Tạo features đơn giản nếu không có original engine"""
        print("🔧 Using simplified feature engineering...")

        df = data.copy()

        # Group by ticker if multiple tickers
        if 'ticker' in df.columns:
            result = df.groupby(
                'ticker', group_keys=False).apply(
                self._add_simple_features)
        else:
            result = self._add_simple_features(df)

        print(
            f"✅ Simplified features: {len(data.columns)} → {len(result.columns)} columns")
        return result

    def _add_simple_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators"""
        df = df.copy()

        # Price features
        df['return_1d'] = df['close'].pct_change(1)
        df['return_4h'] = df['close'].pct_change(4)  # 4 bars = 1 hour
        df['return_1day'] = df['close'].pct_change(18)  # 18 bars = 1 day

        # Moving averages (scaled for 15m)
        df['sma_20'] = df['close'].rolling(20).mean()  # ~5 hours
        df['sma_40'] = df['close'].rolling(40).mean()  # ~10 hours
        df['sma_80'] = df['close'].rolling(80).mean()  # ~4 days

        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_40'] = df['close'].ewm(span=40).mean()
        df['ema_80'] = df['close'].ewm(span=80).mean()

        # RSI (scaled)
        df['rsi'] = self._calculate_rsi(df['close'], 56)  # 14 * 4 = 56

        # MACD (scaled)
        ema_12 = df['close'].ewm(span=48).mean()  # 12 * 4 = 48
        ema_26 = df['close'].ewm(span=104).mean()  # 26 * 4 = 104
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=36).mean()  # 9 * 4 = 36
        df['macd_diff'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        sma_bb = df['close'].rolling(80).mean()  # 20 * 4 = 80
        std_bb = df['close'].rolling(80).std()
        df['bb_upper'] = sma_bb + (std_bb * 2)
        df['bb_lower'] = sma_bb - (std_bb * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
        df['bb_position'] = (df['close'] - df['bb_lower']) / \
            (df['bb_upper'] - df['bb_lower'])

        # Volatility
        returns = df['close'].pct_change()
        df['volatility'] = returns.rolling(72).std()  # ~4 hours
        df['volatility_of_volatility'] = df['volatility'].rolling(72).std()

        # Volume features (if available)
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(36).mean()  # ~2 hours
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_zscore'] = (
                df['volume'] - df['volume_sma']) / df['volume'].rolling(36).std()

        # Price action
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_open_ratio'] = (df['close'] - df['open']) / df['open']
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        # Trend features
        df['trend_sma'] = df['close'].rolling(144).mean()  # ~8 hours
        df['above_trend'] = (df['close'] > df['trend_sma']).astype(int)

        # Rate of change
        for period in [20, 40, 80]:  # Scaled periods
            df[f'roc_{period}'] = (
                (df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100

        # Price percentile rank
        for window in [80, 200]:  # Scaled windows
            df[f'price_rank_{window}d'] = df['close'].rolling(
                window=window).rank(pct=True)

        return df

    def _calculate_rsi(self, series: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def prepare_for_inference(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Chuẩn bị data cho model inference

        Args:
            features_df: DataFrame với features

        Returns:
            DataFrame: Data sẵn sàng cho model
        """
        # Lấy row cuối cùng (latest data)
        if 'ticker' in features_df.columns:
            # Multiple tickers: lấy latest row cho mỗi ticker
            latest_data = features_df.groupby(
                'ticker').tail(1).reset_index(drop=True)
        else:
            # Single ticker: lấy row cuối
            latest_data = features_df.tail(1).reset_index(drop=True)

        # Remove metadata columns
        exclude_cols = [
            'ticker',
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume']
        feature_cols = [
            col for col in latest_data.columns if col not in exclude_cols]

        inference_data = latest_data[feature_cols].copy()

        # Handle missing values
        inference_data = inference_data.fillna(0)

        print(
            f"📊 Prepared inference data: {inference_data.shape[0]} rows, {inference_data.shape[1]} features")
        return inference_data

    def get_feature_names(self, data: pd.DataFrame) -> List[str]:
        """Lấy list tên features (exclude metadata)"""
        exclude_cols = [
            'ticker',
            'timestamp',
            'open',
            'high',
            'low',
            'close',
            'volume']
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        return feature_cols

    def get_status(self) -> Dict:
        """Get status của feature engine"""
        return {
            'use_original_engine': self.use_original,
            'engine_type': 'Original' if self.use_original else 'Simplified',
            'available_features': 'Full set' if self.use_original else 'Basic set'}
