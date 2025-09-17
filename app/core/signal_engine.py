"""
Real-time signal generation engine with multi-strategy support
"""

import asyncio
import logging
import joblib
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config.settings import get_settings
from app.services.database import mongodb_service
from app.core.data_stream import RealTimeDataStream
from app.core.backtest_integration import RealTimeBacktestIntegration

logger = logging.getLogger(__name__)


class Strategy:
    """Individual trading strategy"""

    def __init__(self, config: Dict[str, Any]):
        self.name = config["name"]
        self.confidence_threshold = config["confidence_threshold"]
        self.holding_period_bars = config["holding_period_bars"]
        self.risk_level = config["risk_level"]
        self.color = config["color"]
        self.telegram_alerts = config.get("telegram_alerts", False)
        self.primary = config.get("primary", False)
        self.description = config.get("description", "")
        self.backtest_performance = config.get("backtest_performance", {})

        # Runtime statistics
        self.signals_today = 0
        self.daily_return = 0.0
        self.win_rate = 0.0
        self.status = "active"


class RealTimeSignalEngine:
    """Core engine for real-time signal generation"""

    def __init__(self):
        self.settings = get_settings()
        self.strategies: Dict[str, Strategy] = {}
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.data_stream = None
        self.backtest_integration = None
        self.is_ready = False

    async def initialize(self):
        """Initialize signal engine"""
        try:
            # Load strategies configuration
            await self._load_strategies()

            # Load trained model and scaler
            await self._load_model()

            # Initialize data stream
            self.data_stream = RealTimeDataStream()
            await self.data_stream.initialize()

            # Initialize backtest integration
            self.backtest_integration = RealTimeBacktestIntegration()

            self.is_ready = True
            logger.info("✅ Signal engine initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize signal engine: {e}")
            raise

    async def _load_strategies(self):
        """Load strategy configurations"""
        try:
            config_path = Path(self.settings.strategy_config_path)

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            strategies_config = config.get("strategies", {})

            for strategy_id, strategy_config in strategies_config.items():
                self.strategies[strategy_id] = Strategy(strategy_config)
                logger.info(f"📊 Loaded strategy: {strategy_config['name']}")

            logger.info(f"✅ Loaded {len(self.strategies)} strategies")

        except Exception as e:
            logger.error(f"❌ Failed to load strategies: {e}")
            raise

    async def _load_model(self):
        """Load trained XGBoost model and feature scaler"""
        try:
            # Load model
            model_path = Path(self.settings.model_path_15m)
            if model_path.exists():
                self.model = joblib.load(model_path)
                logger.info(f"✅ Model loaded from {model_path}")
            else:
                logger.warning(f"⚠️ Model not found at {model_path}")
                # Create mock model for demo
                self.model = self._create_mock_model()
                logger.info("🎭 Using mock model for demo")

            # Load scaler
            scaler_path = Path(self.settings.scaler_path_15m)
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Scaler loaded from {scaler_path}")
            else:
                logger.warning(f"⚠️ Scaler not found at {scaler_path}")
                # Create mock scaler
                self.scaler = self._create_mock_scaler()
                logger.info("🎭 Using mock scaler for demo")

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            # Create mock model for demo
            self.model = self._create_mock_model()
            self.scaler = self._create_mock_scaler()
            logger.info("🎭 Using mock model and scaler for demo")

    def _create_mock_model(self):
        """Create mock model for demo purposes"""
        class MockModel:
            def predict_proba(self, X):
                # Generate realistic probabilities
                n_samples = len(X)
                probabilities = np.random.dirichlet([1, 1, 1], n_samples)
                return probabilities

        return MockModel()

    def _create_mock_scaler(self):
        """Create mock scaler for demo purposes"""
        class MockScaler:
            def transform(self, X):
                return X

        return MockScaler()

    async def process_market_data(
            self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process new market data and generate signals using backtest integration"""
        if not self.is_ready or not self.backtest_integration:
            return []

        try:
            # Use backtest integration for signal generation
            signals = await self.backtest_integration.generate_realtime_signals()

            # Process signals for each strategy
            processed_signals = []
            for signal in signals:
                for strategy_id, strategy in self.strategies.items():
                    # Check if signal meets strategy criteria
                    if signal["confidence"] >= strategy.confidence_threshold:
                        # Add strategy information
                        strategy_signal = signal.copy()
                        strategy_signal.update({
                            "strategy": strategy.name,
                            "strategy_id": strategy_id,
                            "holding_period_bars": strategy.holding_period_bars
                        })

                        processed_signals.append(strategy_signal)

                        # Save signal to database
                        await mongodb_service.save_signal(strategy_signal)

                        # Update strategy stats
                        strategy.signals_today += 1

            return processed_signals

        except Exception as e:
            logger.error(f"❌ Error processing market data: {e}")
            return []

    async def _engineer_features(
            self, historical_data: pd.DataFrame) -> Optional[np.ndarray]:
        """Engineer features from historical data"""
        try:
            # Simple feature engineering (you can enhance this)
            df = historical_data.copy()

            # Basic technical indicators
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            df['rsi'] = self._calculate_rsi(df['close'])
            df['volume_sma'] = df['volume'].rolling(10).mean()

            # Price ratios
            df['high_low_ratio'] = df['high'] / df['low']
            df['close_open_ratio'] = df['close'] / df['open']

            # Volume indicators
            df['bu_sd_ratio'] = df['bu'] / \
                (df['sd'] + 1)  # Avoid division by zero
            df['volume_ratio'] = df['volume'] / df['volume_sma']

            # Get latest row features
            latest_features = df.iloc[-1][[
                'sma_5', 'sma_20', 'rsi', 'high_low_ratio',
                'close_open_ratio', 'bu_sd_ratio', 'volume_ratio'
            ]].values

            # Handle NaN values
            latest_features = np.nan_to_num(latest_features, nan=0.0)

            return latest_features.reshape(1, -1)

        except Exception as e:
            logger.error(f"❌ Error engineering features: {e}")
            return None

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    async def _generate_signal(
        self,
        ticker: str,
        features: np.ndarray,
        strategy: Strategy,
        market_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate signal for specific strategy"""
        try:
            # Scale features
            scaled_features = self.scaler.transform(features)

            # Get model prediction
            probabilities = self.model.predict_proba(scaled_features)[0]

            # Probabilities for [SELL, HOLD, BUY]
            sell_prob = probabilities[0]
            hold_prob = probabilities[1]
            buy_prob = probabilities[2]

            # Determine action and confidence
            max_prob = max(probabilities)

            if max_prob < strategy.confidence_threshold:
                action = "HOLD"
                confidence = max_prob
            elif max_prob == buy_prob:
                action = "BUY"
                confidence = buy_prob
            elif max_prob == sell_prob:
                action = "SELL"
                confidence = sell_prob
            else:
                action = "HOLD"
                confidence = hold_prob

            # Only generate signal if above threshold
            if confidence >= strategy.confidence_threshold and action != "HOLD":
                signal = {
                    "ticker": ticker,
                    "action": action,
                    "confidence": float(confidence),
                    "strategy": strategy.name,
                    "strategy_id": list(
                        self.strategies.keys())[
                        list(
                            self.strategies.values()).index(strategy)],
                    "price": float(
                        market_data["close"]),
                    "timestamp": market_data["timestamp"],
                    "holding_period_bars": strategy.holding_period_bars,
                    "probabilities": {
                        "buy": float(buy_prob),
                        "sell": float(sell_prob),
                        "hold": float(hold_prob)}}

                logger.info(
                    f"🎯 Signal: {ticker} {action} (conf: {confidence:.3f}) - {strategy.name}")
                return signal

            return None

        except Exception as e:
            logger.error(f"❌ Error generating signal: {e}")
            return None

    async def get_recent_signals(
            self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent signals from database"""
        try:
            signals = await mongodb_service.get_recent_signals(limit=limit)

            # Convert MongoDB format to display format
            display_signals = []
            for signal in signals:
                display_signals.append({
                    "ticker": signal["ticker"],
                    "action": signal["action"],
                    "confidence": signal["confidence"],
                    "strategy_name": signal["strategy"],
                    "price": signal["price"],
                    "timestamp": signal["timestamp"]
                })

            return display_signals

        except Exception as e:
            logger.error(f"❌ Error getting recent signals: {e}")
            return []

    async def get_signal_history(
        self,
        strategy: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get signal history with pagination"""
        try:
            signals = await mongodb_service.get_recent_signals(
                limit=limit + offset,
                strategy=strategy
            )

            # Apply offset
            signals = signals[offset:offset + limit]

            return signals

        except Exception as e:
            logger.error(f"❌ Error getting signal history: {e}")
            return []

    async def get_strategies(self) -> Dict[str, Any]:
        """Get all available strategies"""
        try:
            strategies_data = {}

            for strategy_id, strategy in self.strategies.items():
                strategies_data[strategy_id] = {
                    "name": strategy.name,
                    "confidence_threshold": strategy.confidence_threshold,
                    "holding_period_bars": strategy.holding_period_bars,
                    "risk_level": strategy.risk_level,
                    "color": strategy.color,
                    "telegram_alerts": strategy.telegram_alerts,
                    "primary": strategy.primary,
                    "description": strategy.description,
                    "backtest_performance": strategy.backtest_performance,
                    "signals_today": strategy.signals_today,
                    "daily_return": strategy.daily_return,
                    "win_rate": strategy.win_rate,
                    "status": strategy.status
                }

            return strategies_data

        except Exception as e:
            logger.error(f"❌ Error getting strategies: {e}")
            return {}

    async def get_strategy_performance(self) -> Dict[str, Any]:
        """Get strategy performance summary for dashboard"""
        try:
            strategies_data = await self.get_strategies()

            # Add real-time stats from database
            signal_stats = await mongodb_service.get_signal_stats(hours=24)

            # Update strategy performance with real data
            for strategy_id, strategy_data in strategies_data.items():
                strategy = self.strategies[strategy_id]

                # Update with mock/demo data for now
                strategy_data.update({
                    "daily_return": strategy.backtest_performance.get("win_rate", 67.0) / 100 * 2.5,
                    "win_rate": strategy.backtest_performance.get("win_rate", 67.0),
                    "signals_today": strategy.signals_today
                })

            return strategies_data

        except Exception as e:
            logger.error(f"❌ Error getting strategy performance: {e}")
            return {}

    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            if self.data_stream:
                return await self.data_stream.get_market_status()
            else:
                return {
                    "vnindex": {"value": "1,285.4", "change": 0.85},
                    "vn30": {"value": "1,321.2", "change": 1.2},
                    "active_tickers": 5,
                    "session": "Demo",
                    "last_update": "Live",
                    "current_time": datetime.now().strftime("%H:%M:%S")
                }

        except Exception as e:
            logger.error(f"❌ Error getting market status: {e}")
            return {}

    def is_ready(self) -> bool:
        """Check if signal engine is ready"""
        return self.is_ready and self.model is not None

    async def cleanup(self):
        """Cleanup signal engine"""
        if self.data_stream:
            await self.data_stream.stop()
        logger.info("🧹 Signal engine cleaned up")
