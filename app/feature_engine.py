"""
Simple Feature Engineering Engine
Copy và đơn giản hóa từ src/data/feature_engineering.py để tự chứa trong app
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SimpleFeatureEngine:
    """Đơn giản hóa feature engineering để self-contained trong app"""
    
    def __init__(self):
        """Initialize feature engine"""
        self.feature_config = self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """Get default feature configuration tương thích với model đã train"""
        return {
            'features': {
                'technical_indicators': {
                    'ema_periods': [20, 40, 80, 200],  # Match reference data
                    'sma_periods': [40, 80, 200],      # Match reference data
                    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                    'rsi_period': 14,
                    'stoch_period': 14,
                    'bollinger': {'period': 20, 'std_dev': 2},
                    'atr_period': 14,
                    'adx_period': 14,
                    'mfi_period': 14,
                    'vwap_period': 20
                },
                'price_features': {
                    'returns_periods': [4, 20, 40, 80, 240, 480],  # Match reference
                    'volatility_window': 20,
                    'volume_ratio_window': 20
                },
                'regime_features': {
                    'trend_window': 50,  # Creates trend_sma and above_trend
                    'volatility_regime_window': 30
                }
            }
        }
    
    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators tương thích với original FeatureEngineer"""
        df = data.copy()
        
        try:
            # EMA - Match reference periods
            for period in [20, 40, 80, 200]:
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # SMA - Match reference periods  
            for period in [40, 80, 200]:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            
            # MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema12 - ema26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_diff'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Stochastic
            lowest_low = df['low'].rolling(window=14).min()
            highest_high = df['high'].rolling(window=14).max()
            df['stoch'] = (100 * (df['close'] - lowest_low) / 
                          (highest_high - lowest_low))
            df['stoch_signal'] = df['stoch'].rolling(window=3).mean()
            
            # Bollinger Bands
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            df['bb_upper'] = sma20 + (std20 * 2)
            df['bb_lower'] = sma20 - (std20 * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            df['bb_position'] = ((df['close'] - df['bb_lower']) / 
                                (df['bb_upper'] - df['bb_lower']))
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = true_range.rolling(window=14).mean()
            df['atr_ratio'] = df['atr'] / df['close']
            
            # ADX (simplified version)
            period = 14
            high_diff = df['high'].diff()
            low_diff = df['low'].diff()
            
            plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
            minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
            
            tr_sum = true_range.rolling(window=period).sum()
            plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).sum() / tr_sum)
            minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).sum() / tr_sum)
            
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(window=period).mean()
            
            # Volume indicators
            if 'volume' in df.columns:
                # MFI (Money Flow Index) - simplified
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                money_flow = typical_price * df['volume']
                
                positive_flow = np.where(typical_price > typical_price.shift(1), money_flow, 0)
                negative_flow = np.where(typical_price < typical_price.shift(1), money_flow, 0)
                
                positive_mf = pd.Series(positive_flow).rolling(window=14).sum()
                negative_mf = pd.Series(negative_flow).rolling(window=14).sum()
                
                mfi_ratio = positive_mf / negative_mf
                df['mfi'] = 100 - (100 / (1 + mfi_ratio))
                
                # VWAP (Volume Weighted Average Price)
                cum_vol = df['volume'].rolling(window=20).sum()
                cum_vol_price = (typical_price * df['volume']).rolling(window=20).sum()
                df['vwap'] = cum_vol_price / cum_vol
                df['vwap_ratio'] = df['close'] / df['vwap']
                
                # OBV (On Balance Volume)
                price_change = df['close'].diff()
                obv_values = np.where(price_change > 0, df['volume'], 
                            np.where(price_change < 0, -df['volume'], 0))
                df['obv'] = pd.Series(obv_values).cumsum()
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {e}")
            
        return df
    
    def add_price_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features tương thích với original"""
        df = data.copy()
        
        try:
            # Returns - Match reference periods
            for period in [4, 20, 40, 80, 240, 480]:
                df[f'return_{period}d'] = df['close'].pct_change(periods=period)
            
            # Volatility
            returns = df['close'].pct_change()
            df['volatility'] = returns.rolling(window=20).std()
            df['volatility_of_volatility'] = df['volatility'].rolling(window=20).std()
            
            # Volume features - Add back as they ARE in reference
            if 'volume' in df.columns:
                df['volume_sma'] = df['volume'].rolling(window=20).mean()
                df['volume_ratio'] = df['volume'] / df['volume_sma']
                df['volume_zscore'] = ((df['volume'] - df['volume_sma']) / 
                                      df['volume'].rolling(window=20).std())
            
            # Active trading features (BU/SD from FiinQuantX)
            if 'bu' in df.columns and 'sd' in df.columns:
                df['bu_sd_ratio'] = df['bu'] / (df['sd'] + 1e-8)  # Back in reference
                df['net_active_volume'] = df['bu'] - df['sd']
                df['active_volume_ratio'] = ((df['bu'] - df['sd']) / 
                                            (df['bu'] + df['sd'] + 1e-8))
            
            # Price action features - Add back as they ARE in reference
            df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
            df['close_open_ratio'] = (df['close'] - df['open']) / df['open']
            
            # Gap features
            df['gap'] = ((df['open'] - df['close'].shift(1)) / 
                        df['close'].shift(1))
            
        except Exception as e:
            logger.error(f"Error adding price features: {e}")
            
        return df
    
    def add_regime_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add market regime features"""
        df = data.copy()
        
        try:
            # Trend regime - Match reference
            df['trend_sma'] = df['close'].rolling(window=50).mean()
            df['above_trend'] = (df['close'] > df['trend_sma']).astype(int)
            
            # Volatility regime
            returns = df['close'].pct_change()
            rolling_vol = returns.rolling(window=30).std()
            
            # Calculate quantiles for volatility regime
            if len(rolling_vol.dropna()) > 30:
                vol_33 = rolling_vol.quantile(0.33)
                vol_67 = rolling_vol.quantile(0.67)
                
                def get_vol_regime(vol):
                    if pd.isna(vol):
                        return np.nan
                    elif vol <= vol_33:
                        return 0  # Low volatility
                    elif vol <= vol_67:
                        return 1  # Medium volatility
                    else:
                        return 2  # High volatility
                
                df['vol_regime'] = rolling_vol.apply(get_vol_regime)
            else:
                df['vol_regime'] = 1  # Default to medium volatility
            
        except Exception as e:
            logger.error(f"Error adding regime features: {e}")
            
        return df
    
    def add_momentum_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add momentum features"""
        df = data.copy()
        
        try:
            # Rate of change - Match reference
            for period in [5, 10, 20]:
                df[f'roc_{period}'] = (
                    (df['close'] - df['close'].shift(period)) / 
                    df['close'].shift(period) * 100
                )
            
            # Cumulative returns - Match reference
            for period in [5, 10, 20]:
                df[f'cum_return_{period}d'] = (
                    (df['close'] / df['close'].shift(period) - 1) * 100
                )
            
            # Price percentile rank - Match reference
            for window in [20, 50]:
                df[f'price_rank_{window}d'] = (
                    df['close'].rolling(window=window).rank(pct=True)
                )
            
        except Exception as e:
            logger.error(f"Error adding momentum features: {e}")
            
        return df
    
    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Complete feature engineering pipeline"""
        
        def process_ticker_data(df):
            """Process features for single ticker"""
            try:
                # Reset index to ensure proper processing
                df = df.reset_index(drop=True)
                
                # Add all features
                df = self.add_technical_indicators(df)
                df = self.add_price_features(df)
                df = self.add_regime_features(df)
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
        logger.info(f"Feature engineering: {original_cols} -> {new_cols} columns")
        
        return result
    
    def get_feature_list(self, data: pd.DataFrame) -> List[str]:
        """Get list of feature columns (exclude metadata only)"""
        # Match exactly with backtest engine exclude list
        exclude_cols = [
            'ticker', 'timestamp', 'label', 'hit_time', 'hit_type',
            'ub', 'lb', 'vbar_end', 'change_pct'
        ]
        
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        return feature_cols 