#!/usr/bin/env python3
"""
Run Signal Bot - Script để chạy signal generator với Telegram integration
"""

from app.telegram_signal_bot import TelegramSignalBot
from app.signal_generator import TradingSignalGenerator, print_signals
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add app to path
sys.path.append(str(Path(__file__).parent))


async def run_signal_only():
    """Chỉ chạy signal generator và print ra console"""
    print("🎯 Starting Signal Generator (Console mode)")
    print("=" * 60)

    generator = TradingSignalGenerator()
    generator.register_signal_callback(print_signals)

    try:
        generator.start_realtime_signal_stream()

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping signal generator...")
        generator.stop_realtime_signal_stream()


async def run_with_telegram():
    """Chạy signal generator với Telegram bot"""
    print("📡 Starting Signal Generator with Telegram Bot")
    print("=" * 60)

    # Telegram credentials - Replace with your own
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "YOUR_CHAT_ID_HERE"

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("⚠️ Please update BOT_TOKEN and CHAT_ID in the script")
        return await run_signal_only()

    # Initialize Telegram bot
    bot = TelegramSignalBot(
        bot_token=BOT_TOKEN,
        chat_id=CHAT_ID,
        min_confidence=0.65
    )

    # Initialize signal generator
    bot.initialize_signal_generator(['CTG', 'MBB', 'ACB', 'QNS', 'MSH'])

    try:
        await bot.start_signal_monitoring()

        print("✅ Bot started! Check your Telegram for alerts.")
        print("📊 Monitoring signals with confidence >= 65%")
        print("🛑 Press Ctrl+C to stop")

        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\n🛑 Stopping Telegram bot...")
        bot.stop_signal_monitoring()


async def test_single_signal():
    """Test để generate signal 1 lần"""
    print("🧪 Testing Single Signal Generation")
    print("=" * 60)

    from app.signal_generator import generate_signals_once

    signals = await generate_signals_once(['CTG', 'MBB', 'ACB', 'QNS', 'MSH'])
    print_signals(signals)


def main():
    """Main function"""
    print("🚀 Trading Signal Bot")
    print("Choose mode:")
    print("1. Console only (print signals to console)")
    print("2. Telegram bot (send alerts to Telegram)")
    print("3. Test single signal generation")

    try:
        choice = input("Enter choice (1/2/3): ").strip()

        if choice == "1":
            asyncio.run(run_signal_only())
        elif choice == "2":
            asyncio.run(run_with_telegram())
        elif choice == "3":
            asyncio.run(test_single_signal())
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
