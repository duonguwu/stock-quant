# =========================
# main.py
# =========================
import time
import pandas as pd

from data import start_core_stream, CORE_TICKERS, OPTIONAL_TICKERS
from bot import TelegramNotifier
from signals import generate_trade_signals   # file của bạn: signals.py (đừng đặt tên "signal.py")
from command import CommandRouter, MarketState

# Thêm import cho MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import pytz

# Thêm kết nối MongoDB cho rule-based signals
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

# --- TOKEN của bot cá nhân (BotFather) ---
BOT_TOKEN = "8171859502:AAF1QhLrOz0NrFFdRRaL-95ebYGdAWn0a1c"

market_state = MarketState()

# --- Callback: mỗi khi có nến 15m mới cho 1 ticker ---
def make_on_window(notifier: TelegramNotifier):
    def _on_window(df_window: pd.DataFrame):
        # Thu thập chat_id mới nếu người dùng vừa mở bot
        # notifier.harvest_chat_ids_once()
        
        # Cập nhật cache snapshot cho lệnh tra cứu nhanh
        market_state.update_from_df_window(df_window)

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
            # asyncio.create_task(save_rulebase_signal(signal_data)) # This line was commented out in the new_code, so it's commented out here.

        # Định dạng thông điệp
        msg = notifier.format_signal_message(latest)

        # Gửi 1 tin nhắn riêng cho mã này
        notifier.broadcast(msg)

        # In log ra terminal
        tkr = latest["ticker"]
        ts  = pd.to_datetime(latest["timestamp"])
        print(f"Sent signal for {tkr} at {ts}")
    return _on_window


if __name__ == "__main__":
    # 1) Khởi tạo bot notifier
    # notifier = TelegramNotifier(BOT_TOKEN)

    # 2) Làm mới prev_close cho toàn bộ (core + optional)
    # notifier.refresh_prev_close(CORE_TICKERS + OPTIONAL_TICKERS)

    # 3) Khởi động stream core tickers; mỗi 15m sẽ chạy callback một lần/ticker
    core_stream = start_core_stream(
        window_bars=20,          # đủ SMA20/RSI14
        by="15m",
        on_window=make_on_window(notifier),
        wait_for_full_timeFrame=True   # chỉ khi nến 15m đóng
    )

    # 4) Khởi tạo CommandRouter
    from command import CommandRouter
    router = CommandRouter(
        notifier=notifier,
        on_window_factory=make_on_window,
        market_state=market_state,
        enabled_strategies=("Wyckoff+VSA+RSI",),   # cập nhật nếu bạn thêm chiến lược khác
        poll_interval_sec=2.0
    )

    try:
        while True:
            router.poll()
            time.sleep(0.5)
    except KeyboardInterrupt:
        core_stream.stop()
        if router.optional_stream is not None:
            router.optional_stream.stop()


