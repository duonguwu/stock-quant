#!/usr/bin/env python3
"""
Test script for real-time signal integration with backtest engine
"""

from app.config.settings import get_settings
from app.core.signal_engine import RealTimeSignalEngine
from app.core.backtest_integration import RealTimeBacktestIntegration
from app.core.feature_engine import FeatureEngine
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


async def test_feature_engine():
    """Test feature engineering pipeline"""
    print("🧪 Testing Feature Engine...")

    try:
        engine = FeatureEngine()

        # Test status
        status = engine.get_status()
        print(f"📊 Feature Engine Status: {status}")

        # Test latest features
        print("🔄 Preparing latest features...")
        features = await engine.prepare_latest_features(["CTG", "MBB"])
        print(f"✅ Generated features: {features.shape}")
        # First 10 columns
        print(f"📝 Columns: {list(features.columns)[:10]}...")

        # Test single ticker inference data
        print("🎯 Testing single ticker inference...")
        inference_data = await engine.prepare_realtime_inference_data("CTG")
        if inference_data is not None:
            print(f"✅ Inference data shape: {inference_data.shape}")
        else:
            print("⚠️ No inference data available")

        print("✅ Feature Engine test completed")
        return True

    except Exception as e:
        print(f"❌ Feature Engine test failed: {e}")
        return False


async def test_backtest_integration():
    """Test backtest integration pipeline"""
    print("\n🧪 Testing Backtest Integration...")

    try:
        integration = RealTimeBacktestIntegration()

        # Test status
        status = integration.get_status()
        print(f"📊 Integration Status: {status}")

        # Test signal generation
        print("🔄 Generating real-time signals...")
        signals = await integration.generate_realtime_signals(["CTG", "MBB"])
        print(f"✅ Generated {len(signals)} signals")

        for signal in signals:
            print(
                f"🎯 {signal['ticker']}: {signal['action']} (conf: {signal['confidence']:.3f})")

        # Test market overview
        print("🔄 Getting market overview...")
        overview = await integration.get_market_overview()
        print(f"📈 Market Overview: {overview}")

        # Test individual ticker backtest
        if signals:
            ticker = signals[0]['ticker']
            print(f"🔄 Testing backtest for {ticker}...")
            backtest_result = await integration.simulate_realtime_backtest(ticker)
            print(f"📊 Backtest result: {backtest_result}")

        print("✅ Backtest Integration test completed")
        return True

    except Exception as e:
        print(f"❌ Backtest Integration test failed: {e}")
        return False


async def test_signal_engine():
    """Test signal engine pipeline"""
    print("\n🧪 Testing Signal Engine...")

    try:
        engine = RealTimeSignalEngine()
        await engine.initialize()

        # Test strategies
        strategies = await engine.get_strategies()
        print(f"📊 Loaded {len(strategies)} strategies")
        for strategy_id, strategy in strategies.items():
            print(
                f"🎯 {strategy_id}: {strategy['name']} (conf: {strategy['confidence_threshold']})")

        # Test signal generation (using mock market data)
        mock_market_data = {
            "ticker": "CTG",
            "close": 45000,
            "timestamp": "2025-09-16 00:00:00"
        }

        print("🔄 Processing mock market data...")
        signals = await engine.process_market_data(mock_market_data)
        print(f"✅ Generated {len(signals)} signals from market data")

        # Test recent signals
        recent = await engine.get_recent_signals(5)
        print(f"📈 Recent signals: {len(recent)}")

        # Test market status
        market_status = await engine.get_market_status()
        print(f"📊 Market Status: {market_status}")

        print("✅ Signal Engine test completed")
        return True

    except Exception as e:
        print(f"❌ Signal Engine test failed: {e}")
        return False


async def test_end_to_end():
    """Test complete end-to-end pipeline"""
    print("\n🧪 Testing End-to-End Pipeline...")

    try:
        # Initialize components
        signal_engine = RealTimeSignalEngine()
        await signal_engine.initialize()

        if signal_engine.backtest_integration:
            # Generate signals
            signals = await signal_engine.backtest_integration.generate_realtime_signals()

            if signals:
                print(f"🎯 End-to-End: Generated {len(signals)} signals")

                # Test each signal through the pipeline
                for signal in signals[:3]:  # Test first 3 signals
                    print(
                        f"📊 Processing {signal['ticker']}: {signal['action']} ({signal['confidence']:.3f})")

                    # Simulate portfolio update (mock)
                    print(
                        f"💼 Portfolio would be updated for {signal['ticker']}")

                    # Simulate Telegram alert (mock)
                    if signal['confidence'] > 0.65:
                        print(
                            f"📱 Telegram alert would be sent for {signal['ticker']}")

                print("✅ End-to-End test completed successfully")
                return True
            else:
                print("⚠️ No signals generated in end-to-end test")
                return False
        else:
            print("❌ Backtest integration not available")
            return False

    except Exception as e:
        print(f"❌ End-to-End test failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Integration Tests...")
    print("=" * 60)

    settings = get_settings()
    print(f"📊 Using settings: {settings.fiin_username}")
    print(f"🎯 Default tickers: {settings.default_tickers}")
    print("=" * 60)

    tests = [
        ("Feature Engine", test_feature_engine),
        ("Backtest Integration", test_backtest_integration),
        ("Signal Engine", test_signal_engine),
        ("End-to-End Pipeline", test_end_to_end)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1

    print(f"\n🎯 Tests Passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 All tests passed! Integration is working correctly.")
        print("🚀 You can now run the main application:")
        print("   cd app && python main.py")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        print("🔧 Make sure you have:")
        print("   - FiinQuantX credentials in .env")
        print("   - MongoDB running on port 27017")
        print("   - All required dependencies installed")


if __name__ == "__main__":
    asyncio.run(main())
