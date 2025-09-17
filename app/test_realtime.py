#!/usr/bin/env python3
"""
Test Real-time Signals
Simulate real-time data để test signals trước khi market mở
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
import pandas as pd
from app.feature_engine import SimpleFeatureEngine
from app.core.model_inference import RealModelInference

# Simulate real-time data


def generate_mock_bar(ticker: str, base_price: float = 25000):
    """Generate một bar data giả với đầy đủ columns cần thiết"""
    now = datetime.now()
    change = random.uniform(-0.02, 0.02)  # ±2% change

    open_price = base_price
    close_price = open_price * (1 + change)
    high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
    low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)
    volume = random.randint(100000, 500000)

    # Add BU/SD data (Buy/Sell volume from FiinQuantX)
    # 30-70% of volume is active
    total_active = volume * random.uniform(0.3, 0.7)
    bu = total_active * random.uniform(0.4, 0.6)  # Buy volume
    sd = total_active - bu  # Sell volume

    return {
        'ticker': ticker,
        'timestamp': now,
        'open': round(open_price, -1),
        'high': round(high_price, -1),
        'low': round(low_price, -1),
        'close': round(close_price, -1),
        'volume': volume,
        'bu': round(bu),
        'sd': round(sd)
    }


async def test_signal_generation():
    """Test signal generation với mock data"""
    print("🧪 Testing Real-time Signal Generation...")

    # Initialize components
    feature_engine = SimpleFeatureEngine()

    try:
        model_inference = RealModelInference()
        print("✅ Real model loaded")
    except Exception as e:
        print(f"❌ Model error: {e}")
        return

    # Test tickers
    tickers = ['CTG', 'MBB', 'ACB']
    base_prices = {'CTG': 25000, 'MBB': 23000, 'ACB': 21000}

    # Generate historical data for features
    print("📊 Generating test historical data...")
    historical_data = []

    # Generate 100 bars of historical data
    for i in range(100):
        timestamp = datetime.now() - timedelta(minutes=15 * i)
        for ticker in tickers:
            bar = generate_mock_bar(ticker, base_prices[ticker])
            bar['timestamp'] = timestamp
            historical_data.append(bar)

    # Create DataFrame
    df = pd.DataFrame(historical_data)
    df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

    print(f"📊 Generated data shape: {df.shape}")
    print(f"📊 Columns: {df.columns.tolist()}")

    # Feature engineering
    print("🔧 Calculating features...")
    features_df = feature_engine.engineer_features(df)

    print(f"📊 Features shape: {features_df.shape}")
    print(f"📊 Feature columns: {len(features_df.columns)}")

    # Get latest features for each ticker
    latest_features = features_df.groupby('ticker').tail(1)
    feature_cols = feature_engine.get_feature_list(latest_features)
    features_only = latest_features[feature_cols].fillna(0)

    print(f"📊 Final features for model: {features_only.shape}")
    print(f"📊 Feature names: {feature_cols[:10]}...")  # Show first 10

    # Debug: Print all feature names
    print(f"\n🔍 DEBUG: All {len(feature_cols)} features:")
    for i, feat in enumerate(feature_cols):
        print(f"  {i+1:2d}. {feat}")

    # Check for reference data
    import os
    ref_path = "data/final/test_data.csv"
    if os.path.exists(ref_path):
        print(f"\n📋 Loading reference data from {ref_path}...")
        test_ref = pd.read_csv(ref_path)

        exclude_cols = [
            'label',
            'hit_time',
            'hit_type',
            'ub',
            'lb',
            'vbar_end']
        ref_feature_cols = [
            col for col in test_ref.columns if col not in exclude_cols]

        print(f"📋 Reference has {len(ref_feature_cols)} features")
        print(f"📋 Model expects {len(ref_feature_cols)} features")

        # Find missing features
        missing_features = set(ref_feature_cols) - set(features_df.columns)
        extra_features = set(features_df.columns) - set(ref_feature_cols)

        if missing_features:
            print(f"\n❌ Missing features ({len(missing_features)}):")
            for feat in sorted(missing_features):
                print(f"  - {feat}")

        if extra_features:
            print(f"\n➕ Extra features ({len(extra_features)}):")
            for feat in sorted(extra_features):
                if feat not in [
                    'ticker',
                    'timestamp',
                    'open',
                    'high',
                    'low',
                    'close',
                        'volume']:
                    print(f"  + {feat}")
    else:
        print(f"\n⚠️ Reference file not found: {ref_path}")

    # Generate signals
    print("🤖 Generating signals...")
    predictions = model_inference.predict_with_confidence(
        features_only,
        latest_features['ticker'].tolist()
    )

    # Display results
    print("\n" + "=" * 60)
    print("📡 REAL-TIME SIGNALS TEST RESULTS")
    print("=" * 60)

    for conf_key, conf_data in predictions.items():
        confidence = conf_data['confidence_threshold']
        signals = conf_data['signals']
        active_signals = [s for s in signals if s['action'] != 'HOLD']

        print(f"\n🎯 Confidence {confidence*100:.0f}%:")
        print(f"   Active Signals: {len(active_signals)}")

        for signal in active_signals:
            print(f"   📊 {signal['ticker']}: {signal['action']} "
                  f"(confidence: {signal['confidence']:.2f})")

    print("\n" + "=" * 60)
    return predictions


async def simulate_realtime_stream():
    """Simulate continuous real-time data stream"""
    print("🔴 Simulating Real-time Stream...")

    # Load components
    feature_engine = SimpleFeatureEngine()
    model_inference = RealModelInference()

    print("📡 Starting simulation (Press Ctrl+C to stop)...")

    tickers = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']
    base_prices = {
        'CTG': 25000,
        'MBB': 24000,
        'ACB': 18000,
        'QNS': 35000,
        'MSH': 15000}

    try:
        while True:
            # Generate test historical data first (like test_signal_generation)
            print("📊 Generating test historical data...")
            all_data = []

            for ticker in tickers:
                # Generate 100 historical bars for each ticker
                historical_data = []
                base_price = base_prices[ticker]

                for i in range(100):
                    bar = generate_mock_bar(ticker, base_price)
                    bar['timestamp'] = datetime.now(
                    ) - timedelta(minutes=15 * (100 - i))
                    historical_data.append(bar)
                    # Slight price drift for realism
                    base_price *= random.uniform(0.999, 1.001)

                all_data.extend(historical_data)

            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

            print(f"📊 Generated data shape: {df.shape}")
            print(f"📊 Columns: {list(df.columns)}")

            # Feature engineering
            print("🔧 Calculating features...")
            features_df = feature_engine.engineer_features(df)

            print(f"📊 Features shape: {features_df.shape}")

            # Take latest data for each ticker (like real-time would be)
            latest_data = features_df.groupby(
                'ticker').tail(1).reset_index(drop=True)

            feature_cols = feature_engine.get_feature_list(latest_data)
            features_only = latest_data[feature_cols].fillna(0)

            print(f"📊 Final features for model: {features_only.shape}")

            # Generate signals
            tickers_list = latest_data['ticker'].tolist()
            predictions = model_inference.predict_with_confidence(
                features_only, tickers_list
            )

            # Display results
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ {current_time} - New Signals:")

            for level, data in predictions.items():
                if level == 'conf_0.6':  # Show only 60% confidence for brevity
                    active_signals = [
                        s for s in data['signals'] if s['action'] != 'HOLD']
                    if active_signals:
                        for signal in active_signals:
                            print(
                                f"  📊 {signal['ticker']}: {signal['action']} "
                                f"(confidence: {signal['confidence']:.2f})")
                    else:
                        print("  💤 No active signals")

            # Wait 5 seconds before next iteration
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Real-time Trading Signals Test")
    print("Choose test mode:")
    print("1. Single test")
    print("2. Simulate real-time stream")

    choice = input("Enter choice (1/2): ").strip()

    if choice == "1":
        asyncio.run(test_signal_generation())
    elif choice == "2":
        asyncio.run(simulate_realtime_stream())
    else:
        print("Invalid choice")
