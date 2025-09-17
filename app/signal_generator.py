"""
Signal Generator - Chuyên dụng để generate trading signals
Tất cả pipeline từ realtime data đến signals trong 1 file
"""

from app.core.model_inference import RealModelInference
from app.feature_engine import SimpleFeatureEngine
from app.data_fetcher import RealDataFetcher
import pandas as pd
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
import sys
import os

# Add src to path for FiinQuantX
sys.path.append('/media/duongn/New Volume/UIT/AI Challenge/DATA '
                'DSTCDSTC/stock-quant/src')


logger = logging.getLogger(__name__)


class TradingSignalGenerator:
    """All-in-one signal generator"""

    def __init__(self,
                 tickers: List[str] = None,
                 confidence_levels: List[float] = None):
        """
        Initialize signal generator

        Args:
            tickers: List of tickers to track
            confidence_levels: Confidence thresholds to use
        """
        self.tickers = tickers or ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
        self.confidence_levels = confidence_levels or [0.4, 0.5, 0.6, 0.7, 0.8]

        # Initialize components
        self.data_fetcher = None
        self.feature_engine = None
        self.model_inference = None

        # Signal callbacks
        self.signal_callbacks = []

        # Initialize
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all components"""
        try:
            logger.info("🔧 Initializing signal generator components...")

            # Data fetcher
            self.data_fetcher = RealDataFetcher()
            logger.info("✅ Data fetcher initialized")

            # Feature engine
            self.feature_engine = SimpleFeatureEngine()
            logger.info("✅ Feature engine initialized")

            # Model inference
            self.model_inference = RealModelInference()
            logger.info("✅ Model inference initialized")

            logger.info("🎯 Signal generator ready")

        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise

    def register_signal_callback(self, callback: Callable):
        """Register callback để nhận signals khi có"""
        self.signal_callbacks.append(callback)

    async def generate_single_signal(self) -> Dict:
        """
        Generate signals 1 lần duy nhất

        Returns:
            Dict: Signals cho tất cả confidence levels
        """
        try:
            logger.info("🎯 Generating single signal...")

            # Get latest bars
            latest_bars = self.data_fetcher.get_latest_bars()

            if not latest_bars:
                logger.warning("⚠️ No latest bars available")
                return self._empty_signals()

            # Convert to DataFrame
            latest_df = pd.DataFrame([bar for bar in latest_bars.values()])

            # Feature engineering
            features_df = self.feature_engine.engineer_features(latest_df)

            # Get features for model
            feature_cols = self.feature_engine.get_feature_list(features_df)
            features_only = features_df[feature_cols].fillna(0)
            tickers_list = features_df['ticker'].tolist()

            # Generate predictions
            predictions = self.model_inference.predict_with_confidence(
                features_only, tickers_list
            )

            # Add metadata
            result = {
                'timestamp': datetime.now().isoformat(),
                'tickers': tickers_list,
                'latest_bars': latest_bars,
                'predictions': predictions,
                'status': 'success'
            }

            logger.info(f"✅ Generated signals for {len(tickers_list)} tickers")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating signals: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }

    def start_realtime_signal_stream(self):
        """Start continuous realtime signal generation"""
        try:
            logger.info("🔴 Starting realtime signal stream...")

            async def signal_callback(latest_bars: Dict):
                """Callback khi có realtime data mới"""
                try:
                    # Convert to DataFrame
                    latest_df = pd.DataFrame(
                        [bar for bar in latest_bars.values()])

                    if len(latest_df) == 0:
                        return

                    # Feature engineering
                    features_df = self.feature_engine.engineer_features(
                        latest_df)

                    # Get features for model
                    feature_cols = self.feature_engine.get_feature_list(
                        features_df)
                    features_only = features_df[feature_cols].fillna(0)
                    tickers_list = features_df['ticker'].tolist()

                    # Generate predictions
                    predictions = self.model_inference.predict_with_confidence(
                        features_only, tickers_list
                    )

                    # Create signal result
                    signals = {
                        'timestamp': datetime.now().isoformat(),
                        'tickers': tickers_list,
                        'latest_bars': latest_bars,
                        'predictions': predictions,
                        'type': 'realtime'
                    }

                    # Call all registered callbacks
                    for callback in self.signal_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(signals)
                            else:
                                callback(signals)
                        except Exception as cb_error:
                            logger.error(
                                f"❌ Signal callback error: {cb_error}")

                    logger.info(
                        f"📡 Generated realtime signals for {len(tickers_list)} tickers")

                except Exception as e:
                    logger.error(f"❌ Error in signal callback: {e}")

            # Register with data fetcher
            self.data_fetcher.register_realtime_callback(signal_callback)

            # Start stream
            self.data_fetcher.start_realtime_stream(self.tickers)

            logger.info("✅ Realtime signal stream started")

        except Exception as e:
            logger.error(f"❌ Error starting signal stream: {e}")
            raise

    def stop_realtime_signal_stream(self):
        """Stop realtime signal stream"""
        try:
            if self.data_fetcher:
                self.data_fetcher.stop_realtime_stream()
                logger.info("🛑 Realtime signal stream stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping signal stream: {e}")

    def _empty_signals(self) -> Dict:
        """Empty signals response"""
        return {
            'timestamp': datetime.now().isoformat(),
            'tickers': [],
            'latest_bars': {},
            'predictions': {},
            'status': 'no_data'
        }

    def get_status(self) -> Dict:
        """Get status của signal generator"""
        return {
            'tickers': self.tickers,
            'confidence_levels': self.confidence_levels,
            'components': {
                'data_fetcher': self.data_fetcher is not None,
                'feature_engine': self.feature_engine is not None,
                'model_inference': self.model_inference is not None},
            'market_open': self.data_fetcher.is_market_open() if self.data_fetcher else False,
            'callbacks_registered': len(
                self.signal_callbacks)}


async def generate_signals_once(tickers: List[str] = None) -> Dict:
    """
    Utility function - Generate signals 1 lần duy nhất

    Args:
        tickers: List of tickers

    Returns:
        Dict: Signals result
    """
    generator = TradingSignalGenerator(tickers=tickers)
    return await generator.generate_single_signal()


def print_signals(signals: Dict):
    """
    Utility function - Print signals ra console

    Args:
        signals: Signals dict from generator
    """
    try:
        if signals.get('status') != 'success':
            print(
                f"❌ Signal generation failed: {signals.get('error', 'Unknown error')}")
            return

        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Trading Signals:")
        print("=" * 60)

        predictions = signals.get('predictions', {})

        for conf_key, conf_data in predictions.items():
            confidence = conf_data.get('confidence_threshold', 0)
            signals_list = conf_data.get('signals', [])

            active_signals = [
                s for s in signals_list if s.get('action') != 'HOLD']

            print(f"\n🎯 Confidence {confidence*100:.0f}%:")
            if active_signals:
                for signal in active_signals:
                    print(f"  📊 {signal['ticker']}: {signal['action']} "
                          f"(confidence: {signal['confidence']:.2f})")
            else:
                print("  💤 No active signals")

        print("=" * 60)

    except Exception as e:
        print(f"❌ Error printing signals: {e}")


# Example usage
if __name__ == "__main__":
    async def main():
        """Example usage"""
        # Generate signals once
        print("🧪 Testing single signal generation...")
        signals = await generate_signals_once()
        print_signals(signals)

        # Start realtime stream with callback
        print("\n🔴 Starting realtime signal stream (Press Ctrl+C to stop)...")
        generator = TradingSignalGenerator()

        # Register callback to print signals
        generator.register_signal_callback(print_signals)

        # Start stream
        generator.start_realtime_signal_stream()

        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping signal stream...")
            generator.stop_realtime_signal_stream()

    asyncio.run(main())
