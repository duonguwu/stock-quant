#!/usr/bin/env python3
"""
Test Real-time Signals WITH Telegram Bot
Copy từ test_realtime.py và thêm Telegram notifications
"""

import asyncio
import random
from datetime import datetime, timedelta
import pandas as pd
from app.feature_engine import SimpleFeatureEngine
from app.core.model_inference import RealModelInference
from app.telegram_signal_bot import TelegramSignalBot


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
    total_active = volume * random.uniform(0.3, 0.7)  # 30-70% active
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
        # Bỏ change_pct để match với test_realtime.py
    }


async def test_single_signal_with_telegram():
    """Test signal generation 1 lần với Telegram - Copy từ test_realtime.py"""
    print("🧪 Testing Real-time Signal Generation WITH Telegram...")

    # Initialize components (giống test_realtime.py)
    feature_engine = SimpleFeatureEngine()

    try:
        model_inference = RealModelInference()
        print("✅ Real model loaded")
    except Exception as e:
        print(f"❌ Model error: {e}")
        return

    # Initialize Telegram bot
    telegram_bot = TelegramSignalBot(min_confidence=0.6)
    if telegram_bot.bot_token and telegram_bot.chat_id:
        print("✅ Telegram bot initialized")
        await telegram_bot.send_startup_message()
    else:
        print("⚠️ Telegram bot not configured")
        telegram_bot = None

    # Test tickers (giống test_realtime.py)
    tickers = ['CTG', 'MBB', 'ACB']
    base_prices = {'CTG': 25000, 'MBB': 23000, 'ACB': 21000}

    # Generate historical data for features (COPY NGUYÊN TỪ test_realtime.py)
    print("📊 Generating test historical data...")
    historical_data = []

    # Generate 100 bars of historical data
    for i in range(100):
        timestamp = datetime.now() - timedelta(minutes=15 * i)
        for ticker in tickers:
            bar = generate_mock_bar(ticker, base_prices[ticker])
            bar['timestamp'] = timestamp
            historical_data.append(bar)

    # Create DataFrame (COPY NGUYÊN)
    df = pd.DataFrame(historical_data)
    df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

    print(f"📊 Generated data shape: {df.shape}")
    print(f"📊 Columns: {df.columns.tolist()}")

    # Feature engineering (COPY NGUYÊN)
    print("🔧 Calculating features...")
    features_df = feature_engine.engineer_features(df)

    print(f"📊 Features shape: {features_df.shape}")
    print(f"📊 Feature columns: {len(features_df.columns)}")

    # Get latest features for each ticker (COPY NGUYÊN)
    latest_features = features_df.groupby('ticker').tail(1)
    feature_cols = feature_engine.get_feature_list(latest_features)
    features_only = latest_features[feature_cols].fillna(0)

    print(f"📊 Final features for model: {features_only.shape}")

    # Generate signals (COPY NGUYÊN)
    print("🤖 Generating signals...")
    predictions = model_inference.predict_with_confidence(
        features_only,
        latest_features['ticker'].tolist()
    )

    # Display results (COPY NGUYÊN từ test_realtime.py)
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

    # THÊM TELEGRAM: Send signals to Telegram
    if telegram_bot:
        print("\n📱 Sending signals to Telegram...")

        # Get latest prices for telegram
        latest_bars = {}
        for ticker in tickers:
            ticker_data = df[df['ticker'] == ticker].iloc[-1]
            latest_bars[ticker] = {
                'close': ticker_data['close'],
                'volume': ticker_data['volume'],
                'change_pct': random.uniform(-2, 2)  # Mock change
            }

        # Send to telegram
        await send_signals_to_telegram(telegram_bot, predictions, latest_bars)

        # Send completion message
        completion_msg = "✅ <b>TEST COMPLETED</b>\n\nSignal generation test finished!"
        await telegram_bot._send_message(completion_msg)
        print("✅ Telegram notifications sent")

    return predictions


async def simulate_realtime_stream_with_telegram():
    """Simulate realtime stream - Copy từ test_realtime.py + Telegram"""
    print("🔴 Simulating Real-time Stream WITH Telegram...")

    # Load components (giống test_realtime.py)
    feature_engine = SimpleFeatureEngine()
    model_inference = RealModelInference()

    # Initialize Telegram
    telegram_bot = TelegramSignalBot(min_confidence=0.6)
    if telegram_bot.bot_token and telegram_bot.chat_id:
        print("✅ Telegram bot ready")
        await telegram_bot.send_startup_message()
    else:
        print("⚠️ Telegram disabled")
        telegram_bot = None

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
            # COPY NGUYÊN logic từ test_realtime.py
            print("📊 Generating test historical data...")
            all_data = []

            # Generate 100 bars theo đúng pattern
            for i in range(100):
                timestamp = datetime.now() - timedelta(minutes=15 * i)
                for ticker in tickers:
                    bar = generate_mock_bar(ticker, base_prices[ticker])
                    bar['timestamp'] = timestamp
                    all_data.append(bar)
                    # Slight price drift for realism
                    if i == 0:  # Update base price từ latest bar
                        base_prices[ticker] = bar['close']

            # Convert to DataFrame (COPY NGUYÊN)
            df = pd.DataFrame(all_data)
            df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

            print(f"📊 Generated data shape: {df.shape}")

            # Feature engineering (COPY NGUYÊN)
            print("🔧 Calculating features...")
            features_df = feature_engine.engineer_features(df)

            print(f"📊 Features shape: {features_df.shape}")

            # Get latest features (COPY NGUYÊN)
            latest_data = features_df.groupby(
                'ticker').tail(1).reset_index(drop=True)
            feature_cols = feature_engine.get_feature_list(latest_data)
            features_only = latest_data[feature_cols].fillna(0)

            print(f"📊 Final features for model: {features_only.shape}")

            # Generate signals (COPY NGUYÊN)
            tickers_list = latest_data['ticker'].tolist()
            predictions = model_inference.predict_with_confidence(
                features_only, tickers_list
            )

            # Display results (COPY NGUYÊN từ test_realtime.py)
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ {current_time} - New Signals:")

            for level, data in predictions.items():
                if level == 'conf_0.6':  # Show only 60% confidence
                    active_signals = [
                        s for s in data['signals'] if s['action'] != 'HOLD']
                    if active_signals:
                        for signal in active_signals:
                            print(
                                f"  📊 {signal['ticker']}: {signal['action']} "
                                f"(confidence: {signal['confidence']:.2f})")
                    else:
                        print("  💤 No active signals")

            # THÊM TELEGRAM: Send to Telegram
            if telegram_bot:
                # Get latest prices
                latest_bars = {}
                for ticker in tickers_list:
                    ticker_data = df[df['ticker'] == ticker].iloc[-1]
                    latest_bars[ticker] = {
                        'close': ticker_data['close'],
                        'volume': ticker_data['volume'],
                        'change_pct': random.uniform(-2, 2)  # Mock change
                    }

                await send_signals_to_telegram(telegram_bot, predictions, latest_bars)

            # Wait 30 seconds (thay vì 5 để tránh spam)
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")
        if telegram_bot:
            goodbye_msg = "🛑 <b>SIMULATION STOPPED</b>\n\nTesting completed!"
            await telegram_bot._send_message(goodbye_msg)


async def send_signals_to_telegram(
        bot: TelegramSignalBot,
        predictions: dict,
        latest_bars: dict):
    """Send signals to Telegram"""
    try:
        for conf_key, conf_data in predictions.items():
            confidence_threshold = conf_data.get('confidence_threshold', 0)

            if confidence_threshold >= bot.min_confidence:
                signals = conf_data.get('signals', [])

                for signal in signals:
                    if signal.get('action') != 'HOLD':
                        ticker = signal.get('ticker')
                        if ticker in latest_bars:
                            bar = latest_bars[ticker]
                            signal_enhanced = {
                                **signal,
                                'price': bar.get('close', 0),
                                'volume': bar.get('volume', 0),
                                'change_pct': bar.get('change_pct', 0),
                                'timestamp': datetime.now()
                            }

                            await bot._process_individual_signal(signal_enhanced, confidence_threshold)

    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")


async def test_single_telegram_message():
    """Test gửi 1 message đơn giản"""
    print("📱 Testing Single Telegram Message...")

    bot = TelegramSignalBot()

    if not bot.bot_token or not bot.chat_id:
        print("❌ Telegram credentials not found!")
        return

    success = await bot.send_test_message()

    if success:
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")


def main():
    """Main function"""
    print("📱 Real-time Signals with Telegram Bot Test")
    print("=" * 60)
    print("Choose test mode:")
    print("1. Single test message")
    print("2. Single signal generation + Telegram")
    print("3. Realtime simulation + Telegram")

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == "1":
        asyncio.run(test_single_telegram_message())
    elif choice == "2":
        asyncio.run(test_single_signal_with_telegram())
    elif choice == "3":
        asyncio.run(simulate_realtime_stream_with_telegram())
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
