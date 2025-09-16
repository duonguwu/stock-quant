#!/usr/bin/env python3
"""
Standalone Trading Signal Generator
File độc lập để generate trading signals - Gửi cho bên thứ 3

Chỉ cần chạy: python standalone_signal_generator.py
Output: Trading signals cho các mã chứng khoán

Requirements:
- pip install pandas numpy joblib scikit-learn xgboost
- Cần có model files: models/model15/xgboost_model.pkl, models/model15/feature_scaler.pkl
- Hoặc set MOCK_MODE=True để chạy với mock model
"""

import pandas as pd
import numpy as np
import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration
MOCK_MODE = os.getenv('MOCK_MODE', 'False').lower() == 'true'
TICKERS = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
CONFIDENCE_LEVELS = [0.4, 0.5, 0.6, 0.7, 0.8]


class FeatureEngineer:
    """Feature engineering for trading signals"""
    
    def __init__(self):
        self.indicators_config = {
            'ema_periods': [20, 40, 80, 200],
            'sma_periods': [40, 80, 200],
            'return_periods': [4, 20, 40, 80, 240, 480],
            'roc_periods': [5, 10, 20],
            'cum_return_periods': [5, 10, 20],
            'price_rank_windows': [20, 50]
        }
    
    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Complete feature engineering pipeline"""
        df = data.copy()
        
        # Process by ticker
        result_frames = []
        for ticker in df['ticker'].unique():
            ticker_data = df[df['ticker'] == ticker].copy()
            ticker_data = ticker_data.sort_values('timestamp').reset_index(drop=True)
            
            # Add all features
            ticker_data = self._add_technical_indicators(ticker_data)
            ticker_data = self._add_price_features(ticker_data)
            ticker_data = self._add_regime_features(ticker_data)
            ticker_data = self._add_momentum_features(ticker_data)
            
            result_frames.append(ticker_data)
        
        result = pd.concat(result_frames, ignore_index=True)
        logger.info(f"Feature engineering: {len(data.columns)} -> {len(result.columns)} columns")
        return result
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators"""
        # EMA
        for period in self.indicators_config['ema_periods']:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # SMA
        for period in self.indicators_config['sma_periods']:
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
        df['stoch'] = (100 * (df['close'] - lowest_low) / (highest_high - lowest_low))
        df['stoch_signal'] = df['stoch'].rolling(window=3).mean()
        
        # Bollinger Bands
        sma20 = df['close'].rolling(window=20).mean()
        std20 = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma20 + (std20 * 2)
        df['bb_lower'] = sma20 - (std20 * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
        df['bb_position'] = ((df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower']))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        df['atr_ratio'] = df['atr'] / df['close']
        
        # ADX (simplified)
        high_diff = df['high'].diff()
        low_diff = df['low'].diff()
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        tr_sum = true_range.rolling(window=14).sum()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=14).sum() / tr_sum)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=14).sum() / tr_sum)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(window=14).mean()
        
        # Volume indicators
        if 'volume' in df.columns:
            # MFI
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            money_flow = typical_price * df['volume']
            positive_flow = np.where(typical_price > typical_price.shift(1), money_flow, 0)
            negative_flow = np.where(typical_price < typical_price.shift(1), money_flow, 0)
            positive_mf = pd.Series(positive_flow).rolling(window=14).sum()
            negative_mf = pd.Series(negative_flow).rolling(window=14).sum()
            mfi_ratio = positive_mf / negative_mf
            df['mfi'] = 100 - (100 / (1 + mfi_ratio))
            
            # VWAP
            cum_vol = df['volume'].rolling(window=20).sum()
            cum_vol_price = (typical_price * df['volume']).rolling(window=20).sum()
            df['vwap'] = cum_vol_price / cum_vol
            df['vwap_ratio'] = df['close'] / df['vwap']
            
            # OBV
            price_change = df['close'].diff()
            obv_values = np.where(price_change > 0, df['volume'], 
                        np.where(price_change < 0, -df['volume'], 0))
            df['obv'] = pd.Series(obv_values).cumsum()
            
            # Volume features
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_zscore'] = ((df['volume'] - df['volume_sma']) / 
                                 df['volume'].rolling(window=20).std())
        
        # BU/SD features (if available)
        if 'bu' in df.columns and 'sd' in df.columns:
            df['bu_sd_ratio'] = df['bu'] / (df['sd'] + 1e-8)
            df['net_active_volume'] = df['bu'] - df['sd']
            df['active_volume_ratio'] = ((df['bu'] - df['sd']) / (df['bu'] + df['sd'] + 1e-8))
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        # Returns
        for period in self.indicators_config['return_periods']:
            df[f'return_{period}d'] = df['close'].pct_change(periods=period)
        
        # Volatility
        returns = df['close'].pct_change()
        df['volatility'] = returns.rolling(window=20).std()
        df['volatility_of_volatility'] = df['volatility'].rolling(window=20).std()
        
        # Price action
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_open_ratio'] = (df['close'] - df['open']) / df['open']
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        
        return df
    
    def _add_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add regime features"""
        # Trend regime
        df['trend_sma'] = df['close'].rolling(window=50).mean()
        df['above_trend'] = (df['close'] > df['trend_sma']).astype(int)
        
        # Volatility regime
        returns = df['close'].pct_change()
        rolling_vol = returns.rolling(window=30).std()
        
        if len(rolling_vol.dropna()) > 30:
            vol_33 = rolling_vol.quantile(0.33)
            vol_67 = rolling_vol.quantile(0.67)
            
            def get_vol_regime(vol):
                if pd.isna(vol):
                    return np.nan
                elif vol <= vol_33:
                    return 0
                elif vol <= vol_67:
                    return 1
                else:
                    return 2
            
            df['vol_regime'] = rolling_vol.apply(get_vol_regime)
        else:
            df['vol_regime'] = 1
        
        return df
    
    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum features"""
        # Rate of change
        for period in self.indicators_config['roc_periods']:
            df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / 
                                 df['close'].shift(period) * 100)
        
        # Cumulative returns
        for period in self.indicators_config['cum_return_periods']:
            df[f'cum_return_{period}d'] = ((df['close'] / df['close'].shift(period) - 1) * 100)
        
        # Price rank
        for window in self.indicators_config['price_rank_windows']:
            df[f'price_rank_{window}d'] = df['close'].rolling(window=window).rank(pct=True)
        
        return df
    
    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get feature columns for model"""
        exclude_cols = ['ticker', 'timestamp', 'label', 'hit_time', 'hit_type', 'ub', 'lb', 'vbar_end']
        return [col for col in df.columns if col not in exclude_cols]


class ModelInference:
    """Model inference for trading signals"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.confidence_levels = CONFIDENCE_LEVELS
        self._load_model()
    
    def _load_model(self):
        """Load model and scaler"""
        model_paths = [
            'models/model15/xgboost_model.pkl',
            'app/models/model15/xgboost_model.pkl',
            '../models/model15/xgboost_model.pkl'
        ]
        
        scaler_paths = [
            'models/model15/feature_scaler.pkl',
            'app/models/model15/feature_scaler.pkl', 
            '../models/model15/feature_scaler.pkl'
        ]
        
        if MOCK_MODE:
            logger.warning("🎭 Running in MOCK MODE - using dummy model")
            return
        
        try:
            import joblib
            
            # Load model
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path:
                self.model = joblib.load(model_path)
                logger.info(f"✅ Model loaded from: {model_path}")
            else:
                logger.warning("⚠️ No model found, switching to MOCK MODE")
                return
            
            # Load scaler
            scaler_path = None
            for path in scaler_paths:
                if os.path.exists(path):
                    scaler_path = path
                    break
            
            if scaler_path:
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Scaler loaded from: {scaler_path}")
            else:
                logger.warning("⚠️ No scaler found")
                
        except ImportError:
            logger.error("❌ joblib not installed. Install: pip install joblib")
            logger.info("🎭 Switching to MOCK MODE")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            logger.info("🎭 Switching to MOCK MODE")
    
    def predict_signals(self, features_df: pd.DataFrame, tickers: List[str]) -> Dict:
        """Generate trading signals"""
        if self.model is None:
            return self._mock_predictions(tickers)
        
        try:
            # Prepare features
            X_scaled = self._prepare_features(features_df)
            
            # Get predictions
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            confidence_scores = np.max(probabilities, axis=1)
            
            # Map predictions to signals
            label_map = {0: -1, 1: 0, 2: 1}  # 0: SELL, 1: HOLD, 2: BUY
            signals = np.vectorize(label_map.get)(predictions)
            
            # Generate results for all confidence levels
            results = {}
            for conf_threshold in self.confidence_levels:
                level_signals = []
                
                for i, ticker in enumerate(tickers):
                    original_signal = signals[i]
                    confidence = confidence_scores[i]
                    
                    # Apply confidence threshold
                    if confidence >= conf_threshold:
                        action = {-1: "SELL", 0: "HOLD", 1: "BUY"}[original_signal]
                    else:
                        action = "HOLD"
                    
                    level_signals.append({
                        'ticker': ticker,
                        'action': action,
                        'confidence': float(confidence),
                        'signal_value': int(original_signal),
                        'meets_threshold': confidence >= conf_threshold
                    })
                
                # Calculate summary
                active_signals = [s for s in level_signals if s['action'] != 'HOLD']
                buy_signals = [s for s in level_signals if s['action'] == 'BUY']
                sell_signals = [s for s in level_signals if s['action'] == 'SELL']
                
                results[f"confidence_{int(conf_threshold*100)}"] = {
                    'threshold': conf_threshold,
                    'signals': level_signals,
                    'summary': {
                        'total': len(level_signals),
                        'active': len(active_signals),
                        'buy': len(buy_signals),
                        'sell': len(sell_signals),
                        'hold': len(level_signals) - len(active_signals)
                    }
                }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return self._mock_predictions(tickers)
    
    def _prepare_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """Prepare features for model"""
        # Handle missing values
        X_clean = features_df.fillna(features_df.median())
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
        X_clean = X_clean.fillna(X_clean.median())
        
        # Scale features
        if self.scaler:
            X_scaled = self.scaler.transform(X_clean)
        else:
            X_scaled = X_clean.values
        
        return X_scaled
    
    def _mock_predictions(self, tickers: List[str]) -> Dict:
        """Generate mock predictions"""
        results = {}
        
        for conf_threshold in self.confidence_levels:
            level_signals = []
            
            for ticker in tickers:
                # Random mock signal
                actions = ['BUY', 'SELL', 'HOLD']
                action = np.random.choice(actions, p=[0.3, 0.3, 0.4])
                confidence = np.random.uniform(0.4, 0.9)
                
                level_signals.append({
                    'ticker': ticker,
                    'action': action,
                    'confidence': confidence,
                    'signal_value': {'BUY': 1, 'SELL': -1, 'HOLD': 0}[action],
                    'meets_threshold': confidence >= conf_threshold
                })
            
            # Calculate summary
            active_signals = [s for s in level_signals if s['action'] != 'HOLD']
            buy_signals = [s for s in level_signals if s['action'] == 'BUY']
            sell_signals = [s for s in level_signals if s['action'] == 'SELL']
            
            results[f"confidence_{int(conf_threshold*100)}"] = {
                'threshold': conf_threshold,
                'signals': level_signals,
                'summary': {
                    'total': len(level_signals),
                    'active': len(active_signals),
                    'buy': len(buy_signals),
                    'sell': len(sell_signals),
                    'hold': len(level_signals) - len(active_signals)
                }
            }
        
        return results


def generate_mock_data(tickers: List[str], num_bars: int = 100) -> pd.DataFrame:
    """Generate mock OHLCV data for testing"""
    data = []
    base_prices = {'CTG': 25000, 'MBB': 24000, 'ACB': 18000, 'QNS': 35000, 'MSH': 15000}
    
    for ticker in tickers:
        base_price = base_prices.get(ticker, 25000)
        
        for i in range(num_bars):
            # Generate realistic price movement
            change = np.random.normal(0, 0.01)  # 1% volatility
            
            timestamp = datetime.now() - timedelta(minutes=15*(num_bars-i))
            open_price = base_price
            close_price = open_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.randint(100000, 1000000)
            
            # BU/SD data (active trading volumes)
            total_active = volume * np.random.uniform(0.3, 0.7)
            bu = total_active * np.random.uniform(0.4, 0.6)
            sd = total_active - bu
            
            data.append({
                'ticker': ticker,
                'timestamp': timestamp,
                'open': round(open_price, -1),
                'high': round(high_price, -1),
                'low': round(low_price, -1),
                'close': round(close_price, -1),
                'volume': int(volume),
                'bu': int(bu),
                'sd': int(sd)
            })
            
            # Update base price for next iteration
            base_price = close_price
    
    return pd.DataFrame(data)


def format_signals_output(results: Dict, show_details: bool = True) -> str:
    """Format signals for output"""
    output = []
    output.append("=" * 80)
    output.append("🎯 TRADING SIGNALS GENERATED")
    output.append(f"⏰ Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("=" * 80)
    
    for conf_key, conf_data in results.items():
        threshold = conf_data['threshold']
        signals = conf_data['signals']
        summary = conf_data['summary']
        
        output.append(f"\n📊 CONFIDENCE {threshold*100:.0f}%:")
        output.append(f"   Active: {summary['active']}/{summary['total']} signals")
        output.append(f"   BUY: {summary['buy']}, SELL: {summary['sell']}, HOLD: {summary['hold']}")
        
        if show_details:
            active_signals = [s for s in signals if s['action'] != 'HOLD']
            for signal in active_signals:
                action_emoji = "🟢" if signal['action'] == "BUY" else "🔴"
                output.append(f"   {action_emoji} {signal['ticker']}: {signal['action']} "
                             f"(confidence: {signal['confidence']:.2f})")
    
    output.append("=" * 80)
    return "\n".join(output)


def main():
    """Main function"""
    print("🚀 Standalone Trading Signal Generator")
    print("=" * 80)
    
    try:
        # Initialize components
        logger.info("🔧 Initializing components...")
        feature_engineer = FeatureEngineer()
        model_inference = ModelInference()
        
        # Generate or load data
        logger.info("📊 Generating market data...")
        # In real usage, replace this with actual data fetching
        market_data = generate_mock_data(TICKERS, num_bars=200)
        
        # Feature engineering
        logger.info("🔧 Engineering features...")
        features_df = feature_engineer.engineer_features(market_data)
        
        # Get latest data for each ticker
        latest_data = features_df.groupby('ticker').tail(1).reset_index(drop=True)
        
        # Prepare features for model
        feature_cols = feature_engineer.get_feature_columns(latest_data)
        features_only = latest_data[feature_cols].fillna(0)
        tickers = latest_data['ticker'].tolist()
        
        # Generate signals
        logger.info("🎯 Generating signals...")
        results = model_inference.predict_signals(features_only, tickers)
        
        # Output results
        output = format_signals_output(results, show_details=True)
        print(output)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_signals_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        
        logger.info(f"💾 Results saved to: {filename}")
        
        # Return JSON for programmatic use
        return {
            'timestamp': datetime.now().isoformat(),
            'tickers': tickers,
            'results': results,
            'status': 'success'
        }
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'status': 'error'
        }


if __name__ == "__main__":
    # Set environment variable for mock mode if needed
    # os.environ['MOCK_MODE'] = 'True'
    
    main() 