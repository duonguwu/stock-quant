"""
Integration layer between backtest engine and real-time data processing
"""

from app.core.feature_engine import FeatureEngine
from app.config.settings import get_settings
import os
import sys
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))


# Import backtest components
try:
    from src.backtesting.backtest_engine_15m import BacktestEngine15m
except ImportError as e:
    logging.warning(f"Could not import backtest engine: {e}")
    BacktestEngine15m = None

logger = logging.getLogger(__name__)


class MockBacktestEngine:
    """Mock backtest engine for demo purposes"""

    def __init__(self):
        self.bars_per_day = 18

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Mock feature preparation"""
        return data

    def generate_signals(
            self,
            data: pd.DataFrame,
            confidence_threshold: float = 0.65) -> pd.DataFrame:
        """Generate mock signals"""
        n_rows = len(data)

        # Generate realistic signal distribution
        signals = np.random.choice(
            [-1, 0, 1], size=n_rows, p=[0.15, 0.7, 0.15])
        # Bias toward higher confidence
        confidence = np.random.beta(2, 5, size=n_rows) * 0.5 + 0.5

        # Apply confidence threshold
        signals[confidence < confidence_threshold] = 0

        return pd.DataFrame({
            'signal': signals,
            'confidence': confidence,
            'prob_sell': np.random.uniform(0, 1, n_rows),
            'prob_hold': np.random.uniform(0, 1, n_rows),
            'prob_buy': np.random.uniform(0, 1, n_rows),
        }, index=data.index)


class RealTimeBacktestIntegration:
    """Integration layer for real-time backtesting and signal generation"""

    def __init__(self):
        self.settings = get_settings()
        self.feature_engine = FeatureEngine()
        self.backtest_engine = None
        self.model = None
        self.scaler = None

        # Initialize components
        self._initialize_backtest_engine()
        self._load_models()

    def _initialize_backtest_engine(self):
        """Initialize backtest engine"""
        try:
            if BacktestEngine15m:
                # Try to load real backtest engine with models
                model_path = self.settings.model_path_15m
                scaler_path = self.settings.scaler_path_15m

                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.backtest_engine = BacktestEngine15m(
                        model_path, scaler_path)
                    logger.info("✅ Real backtest engine initialized")
                else:
                    logger.warning(
                        "⚠️ Model files not found, using mock engine")
                    self.backtest_engine = MockBacktestEngine()
            else:
                logger.warning(
                    "⚠️ BacktestEngine15m not available, using mock")
                self.backtest_engine = MockBacktestEngine()

        except Exception as e:
            logger.error(f"❌ Error initializing backtest engine: {e}")
            self.backtest_engine = MockBacktestEngine()

    def _load_models(self):
        """Load trained models for inference"""
        try:
            model_path = self.settings.model_path_15m
            scaler_path = self.settings.scaler_path_15m

            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"✅ Model loaded from {model_path}")
            else:
                logger.warning(f"⚠️ Model not found at {model_path}")

            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Scaler loaded from {scaler_path}")
            else:
                logger.warning(f"⚠️ Scaler not found at {scaler_path}")

        except Exception as e:
            logger.error(f"❌ Error loading models: {e}")

    async def generate_realtime_signals(
        self,
        tickers: Optional[List[str]] = None,
        confidence_threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """Generate real-time trading signals for multiple tickers"""
        try:
            if tickers is None:
                tickers = self.settings.default_tickers

            # Prepare latest features
            features_df = await self.feature_engine.prepare_latest_features(tickers)

            if features_df.empty:
                logger.warning(
                    "⚠️ No features available for signal generation")
                return []

            signals = []

            # Generate signals for each ticker
            for ticker in tickers:
                signal = await self._generate_ticker_signal(
                    ticker, features_df, confidence_threshold
                )
                if signal:
                    signals.append(signal)

            logger.info(f"✅ Generated {len(signals)} real-time signals")
            return signals

        except Exception as e:
            logger.error(f"❌ Error generating real-time signals: {e}")
            return []

    async def _generate_ticker_signal(
        self,
        ticker: str,
        features_df: pd.DataFrame,
        confidence_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Generate signal for single ticker"""
        try:
            # Extract ticker data
            ticker_data = features_df[features_df['ticker'] == ticker]
            if ticker_data.empty:
                return None

            # Get latest features for inference
            latest_features = self.feature_engine.get_latest_single_bar_features(
                ticker, features_df)

            if latest_features is None:
                return None

            # Generate signal using backtest engine or direct model
            if self.model and self.scaler:
                signal_data = self._predict_with_model(
                    latest_features, confidence_threshold
                )
            else:
                # Use backtest engine signals
                signals_df = self.backtest_engine.generate_signals(
                    ticker_data, confidence_threshold
                )
                if signals_df.empty:
                    return None
                signal_data = signals_df.iloc[-1].to_dict()

            # Get latest price
            latest_price = ticker_data['close'].iloc[-1]

            # Format signal
            if signal_data['signal'] != 0:  # Only return non-HOLD signals
                return {
                    'ticker': ticker,
                    'action': self._signal_to_action(signal_data['signal']),
                    'confidence': float(signal_data['confidence']),
                    'price': float(latest_price),
                    'timestamp': datetime.now(),
                    'probabilities': {
                        'buy': float(signal_data.get('prob_buy', 0)),
                        'sell': float(signal_data.get('prob_sell', 0)),
                        'hold': float(signal_data.get('prob_hold', 0))
                    },
                    'strategy': 'Real-time 15m',
                    'timeframe': '15m'
                }

            return None

        except Exception as e:
            logger.error(f"❌ Error generating signal for {ticker}: {e}")
            return None

    def _predict_with_model(
        self,
        features: pd.Series,
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """Make prediction using loaded model"""
        try:
            # Prepare features for model
            feature_array = features.values.reshape(1, -1)
            feature_array = np.nan_to_num(feature_array, nan=0.0)

            # Scale features
            scaled_features = self.scaler.transform(feature_array)

            # Get prediction
            prediction = self.model.predict(scaled_features)[0]
            probabilities = self.model.predict_proba(scaled_features)[0]

            # Map prediction to signal
            label_map = {0: -1, 1: 0, 2: 1}  # 0=SELL, 1=HOLD, 2=BUY
            signal = label_map.get(prediction, 0)

            # Calculate confidence
            confidence = float(np.max(probabilities))

            return {
                'signal': signal, 'confidence': confidence, 'prob_sell': float(
                    probabilities[0]) if len(probabilities) > 0 else 0, 'prob_hold': float(
                    probabilities[1]) if len(probabilities) > 1 else 0, 'prob_buy': float(
                    probabilities[2]) if len(probabilities) > 2 else 0, }

        except Exception as e:
            logger.error(f"❌ Error in model prediction: {e}")
            # Return neutral signal
            return {
                'signal': 0,
                'confidence': 0.5,
                'prob_sell': 0.33,
                'prob_hold': 0.34,
                'prob_buy': 0.33,
            }

    def _signal_to_action(self, signal: int) -> str:
        """Convert signal integer to action string"""
        signal_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
        return signal_map.get(signal, 'HOLD')

    async def simulate_realtime_backtest(
        self,
        ticker: str,
        confidence_threshold: float = 0.65,
        holding_period_bars: int = 36
    ) -> Dict[str, Any]:
        """Simulate backtest on latest data for single ticker"""
        try:
            # Get latest features
            features_df = await self.feature_engine.prepare_latest_features([ticker])

            if features_df.empty:
                return {'error': 'No data available'}

            # Extract ticker data
            ticker_data = features_df[features_df['ticker'] == ticker]

            # Generate signals using backtest engine
            signals_df = self.backtest_engine.generate_signals(
                ticker_data, confidence_threshold
            )

            # Simulate trades (simplified)
            trades = self.backtest_engine.simulate_trades(
                ticker_data,
                signals_df,
                holding_period_bars=holding_period_bars,
                transaction_cost=0.0005
            )

            # Calculate basic metrics
            if trades:
                returns = [t.return_pct for t in trades]
                total_return = (1 + np.array(returns)).prod() - 1
                win_rate = len([r for r in returns if r > 0]) / len(returns)
                avg_return = np.mean(returns)
            else:
                total_return = 0
                win_rate = 0
                avg_return = 0

            return {
                'ticker': ticker,
                'total_trades': len(trades),
                'total_return': float(total_return),
                'win_rate': float(win_rate),
                'avg_return': float(avg_return),
                'latest_signal': signals_df.iloc[-1].to_dict() if not signals_df.empty else None,
                'data_points': len(ticker_data),
                'timeframe': '15m'
            }

        except Exception as e:
            logger.error(f"❌ Error in realtime backtest for {ticker}: {e}")
            return {'error': str(e)}

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview with latest signals"""
        try:
            # Generate signals for all default tickers
            signals = await self.generate_realtime_signals()

            # Count signal types
            buy_signals = len([s for s in signals if s['action'] == 'BUY'])
            sell_signals = len([s for s in signals if s['action'] == 'SELL'])

            # Calculate average confidence
            avg_confidence = np.mean([s['confidence']
                                     for s in signals]) if signals else 0

            return {
                'total_tickers': len(self.settings.default_tickers),
                'active_signals': len(signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': float(avg_confidence),
                'market_hours': self.feature_engine.is_market_hours(),
                'last_update': datetime.now(),
                'signals': signals[:5]  # Latest 5 signals
            }

        except Exception as e:
            logger.error(f"❌ Error getting market overview: {e}")
            return {
                'total_tickers': len(self.settings.default_tickers),
                'active_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'avg_confidence': 0,
                'market_hours': False,
                'last_update': datetime.now(),
                'signals': [],
                'error': str(e)
            }

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            'backtest_engine_ready': self.backtest_engine is not None,
            'model_loaded': self.model is not None,
            'scaler_loaded': self.scaler is not None,
            'feature_engine_status': self.feature_engine.get_status(),
            'demo_mode': isinstance(self.backtest_engine, MockBacktestEngine)
        }
