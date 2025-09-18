# =========================
# main.py (no logger)
# =========================
import time
from data import start_core_stream, CORE_TICKERS, OPTIONAL_TICKERS
from bot import TelegramNotifier
from signals import make_on_window

# --- BOT TOKEN ---
BOT_TOKEN = "8171859502:AAF1QhLrOz0NrFFdRRaL-95ebYGdAWn0a1c"

# True: gửi tin mỗi 15 phút; False: chỉ gửi khi có BUY/SELL
ALWAYS_BROADCAST = True

if __name__ == "__main__":
    # 1) Khởi tạo notifier
    notifier = TelegramNotifier(BOT_TOKEN)

    # 2) Khởi động stream realtime 15m
    #    window_bars nên >= 64 để đủ dữ liệu tính indicator (RSI/ADX/MFI/...).
    core_stream = start_core_stream(
        window_bars=64,
        by="15m",
        on_window=make_on_window(notifier, always_broadcast=ALWAYS_BROADCAST),
        wait_for_full_timeFrame=True  # chỉ gọi khi nến 15m đã đóng
    )

    try:
        while True:
            time.sleep(1.0)  # giữ tiến trình sống
    except KeyboardInterrupt:
        core_stream.stop()
