# =========================
# main.py - Rule-Based Signal Generator
# =========================
import time
import pandas as pd
import asyncio
from datetime import datetime
import pytz

from data import start_core_stream
from signals import generate_trade_signals
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection for rule-based signals
RULEBASE_DB = None


async def init_rulebase_db():
    """Initialize MongoDB connection for rule-based signals"""
    global RULEBASE_DB
    try:
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        RULEBASE_DB = client.stock_quant.rulebase_signals
        print("✅ Rule-based signals database connected")
    except Exception as e:
        print(f"❌ Rule-based signals database error: {e}")
        RULEBASE_DB = None


async def save_rulebase_signal(signal_data):
    """Save rule-based signal to MongoDB"""
    global RULEBASE_DB
    
    if RULEBASE_DB is None:
        await init_rulebase_db()
    
    if RULEBASE_DB is None:
        print("❌ No database connection for rule-based signals")
        return
    
    try:
        # Create signal document
        signal_doc = {
            '_id': f"{signal_data['ticker']}_{signal_data['action']}_{signal_data['timestamp']}",
            'ticker': signal_data['ticker'],
            'action': signal_data['action'],
            'price': signal_data['price'],
            'volume': signal_data.get('volume', 0),
            'timestamp': signal_data['timestamp'],
            'created_at': datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
        }
        
        # Insert signal
        await RULEBASE_DB.insert_one(signal_doc)
        print(f"✅ Saved rule-based signal: {signal_data['ticker']} {signal_data['action']} at {signal_data['timestamp']}")
        
    except Exception as e:
        print(f"❌ Error saving rule-based signal: {e}")


def make_on_window():
    """Callback: mỗi khi có nến 15m mới cho 1 ticker"""
    def _on_window(df_window: pd.DataFrame):
        # Tính tín hiệu cho đúng cửa sổ hiện tại của ticker
        signals = generate_trade_signals(df_window)
        latest = signals.iloc[-1]

        # Lưu signal vào MongoDB nếu có signal
        if latest['signal'] != 0:  # 1 = BUY, -1 = SELL
            signal_data = {
                'ticker': latest['ticker'],
                'action': 'BUY' if latest['signal'] == 1 else 'SELL',
                'price': latest['close'],
                'volume': latest.get('volume', 0),
                'timestamp': latest['timestamp']
            }
            
            # Lưu signal vào MongoDB
            asyncio.create_task(save_rulebase_signal(signal_data))

        # In log ra terminal
        tkr = latest["ticker"]
        ts = pd.to_datetime(latest["timestamp"])
        signal_type = "BUY" if latest['signal'] == 1 else "SELL" if latest['signal'] == -1 else "HOLD"
        print(f" {tkr} at {ts} - Signal: {signal_type} (Price: {latest['close']})")
    
    return _on_window


if __name__ == "__main__":
    print("🚀 Starting Rule-Based Signal Generator...")
    
    # Initialize database
    asyncio.run(init_rulebase_db())
    
    # Start core stream for signal generation
    core_stream = start_core_stream(
        window_bars=20,          # đủ SMA20/RSI14
        by="15m",
        on_window=make_on_window(),
        wait_for_full_timeFrame=True   # chỉ khi nến 15m đóng
    )

    try:
        print("✅ Rule-based signal generator is running...")
        print("📊 Monitoring: CTG, MBB, ACB, QNS, MSH")
        print("🔄 Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping rule-based signal generator...")
        core_stream.stop()
        print("✅ Stopped successfully")


