# =========================
# main.py - Rule-Based Signal Generator (with run_in_main_loop)
# =========================
import time
import pandas as pd
import asyncio
from datetime import datetime
import pytz

from data import start_core_stream
from signals import generate_trade_signals
from motor.motor_asyncio import AsyncIOMotorClient

# ============================================
# MongoDB Connector
# ============================================
MONGO_URL = "mongodb://admin:password123@localhost:27017/trading_signals?authSource=admin"


class MongoConnector:
    def __init__(self, mongo_url=MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        self.db = None
        self.signals_col = None

    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            await self.client.admin.command("ping")
            print("✅ MongoDB connection established")

            self.db = self.client.get_database()
            print(f"📂 Using database: {self.db.name}")

            self.signals_col = self.db["rulebase_signals"]
            print(f"📑 Using collection: {self.signals_col.name}")

        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            self.client = None
            self.db = None
            self.signals_col = None

    async def save_signal(self, signal_data: dict):
        if self.signals_col is None:
            print("❌ No MongoDB collection available")
            return

        try:
            doc = {
                "_id": f"{signal_data['ticker']}_{signal_data['action']}_{signal_data['timestamp']}",
                "ticker": signal_data["ticker"],
                "action": signal_data["action"],
                "price": signal_data["price"],
                "volume": signal_data.get(
                    "volume",
                    0),
                "timestamp": signal_data["timestamp"],
                "created_at": datetime.now(
                    pytz.timezone("Asia/Ho_Chi_Minh"))}
            await self.signals_col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            print(f"✅ Saved signal: {doc['_id']}")
        except Exception as e:
            print(f"❌ Error saving signal: {e}")


# ============================================
# Run coroutine trong main loop
# ============================================
main_loop = None


def run_in_main_loop(coro):
    """Đảm bảo coroutine chạy trong main event loop."""
    global main_loop
    if main_loop is None:
        raise RuntimeError("Main loop chưa được khởi tạo")
    return asyncio.run_coroutine_threadsafe(coro, main_loop)


# ============================================
# Rule-based signal generator
# ============================================
MONGO = MongoConnector()


def make_on_window():
    """Callback: mỗi khi có nến 15m mới cho 1 ticker"""
    def _on_window(df_window: pd.DataFrame):
        signals = generate_trade_signals(df_window)
        latest = signals.iloc[-1]

        # ✅ Luôn lưu signal (BUY/SELL/HOLD)
        signal_data = {
            "ticker": latest["ticker"],
            "action": "BUY" if latest["signal"] == 1 else "SELL" if latest["signal"] == -
            1 else "HOLD",
            "price": latest["close"],
            "volume": latest.get(
                "volume",
                0),
            "timestamp": latest["timestamp"]}

        # chạy coroutine trong main loop
        run_in_main_loop(MONGO.save_signal(signal_data))

        # log terminal
        tkr = latest["ticker"]
        ts = pd.to_datetime(latest["timestamp"])
        print(
            f"{tkr} at {ts} - Signal: {signal_data['action']} (Price: {latest['close']})")

    return _on_window


# ============================================
# Main entry
# ============================================
async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()  # set main loop

    print("🚀 Starting Rule-Based Signal Generator...")

    await MONGO.connect()

    core_stream = start_core_stream(
        window_bars=20,
        by="15m",
        on_window=make_on_window(),
        wait_for_full_timeFrame=True
    )

    try:
        print("✅ Rule-based signal generator is running...")
        print("📊 Monitoring: CTG, MBB, ACB, QNS, MSH")
        print("🔄 Press Ctrl+C to stop")

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping rule-based signal generator...")
        core_stream.stop()
        print("✅ Stopped successfully")


if __name__ == "__main__":
    asyncio.run(main())
