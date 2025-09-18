# =========================
# data.py
# =========================
import time
from collections import deque, defaultdict
from typing import Callable, Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from FiinQuantX import FiinSession, BarDataUpdate

# --------- CẤU HÌNH NGƯỜI DÙNG (điền tài khoản thật của bạn) ----------
USERNAME = "DSTC_19@fiinquant.vn"
PASSWORD = "Fiinquant0606"

# --------- DANH SÁCH MÃ ----------
CORE_TICKERS = ['CTG', 'MBB', 'ACB', 'QNS', 'MSH']              # theo dõi thường trực
OPTIONAL_TICKERS = ['HDB', 'STB', 'TPB', 'NAB', 'BFC', 'NTL']   # bật theo command

# --------- CÁC TRƯỜNG DỮ LIỆU CẦN LẤY ----------
FIELDS = ['open', 'high', 'low', 'close', 'volume', 'bu', 'sd']  # đủ cho VSA/RSI
DEFAULT_BY = '15m'  # khung thời gian mặc định cho bot
DEFAULT_INIT_PERIOD = 40  # lấy dư để ổn định chỉ báo (>= max(14,20))
DEFAULT_WINDOW_BARS = 20   # cửa sổ trượt cố định N nến (ví dụ 20 cho SMA20)

# ===== KẾT NỐI FIINQUANT =====
_fiin_client = None
def get_client() -> FiinSession:
    global _fiin_client
    if _fiin_client is None:
        _fiin_client = FiinSession(username=USERNAME, password=PASSWORD).login()
        print("✅ Đăng nhập FiinQuant thành công.")
    return _fiin_client


# =========================
# 1) STREAM REALTIME CỬA SỔ TRƯỢT
# =========================
class SlidingWindowStreamer:
    """
    Khởi tạo một stream realtime:
    - Ban đầu lấy init_period nến gần nhất (bao gồm nến đang hình thành).
    - Sau đó mỗi khi có cập nhật, giữ đúng 'window_bars' nến gần nhất cho mỗi ticker.
    - Gọi 'on_window(df_window)' mỗi lần cập nhật (df_window = dataframe N nến của 1 ticker).
    """
    def __init__(
        self,
        tickers: List[str],
        by: str = DEFAULT_BY,
        init_period: int = DEFAULT_INIT_PERIOD,
        window_bars: int = DEFAULT_WINDOW_BARS,
        on_window: Optional[Callable[[pd.DataFrame], None]] = None,
        wait_for_full_timeFrame: bool = False,
        adjusted: bool = True,
    ):
        self.client = get_client()
        self.tickers = list(dict.fromkeys([t.upper() for t in tickers]))  # unique & keep order
        self.by = by
        self.init_period = init_period
        self.window_bars = window_bars
        self.on_window = on_window if on_window is not None else self._print_window
        self.wait_for_full_timeFrame = wait_for_full_timeFrame
        self.adjusted = adjusted

        # Bộ đệm trượt cho từng mã
        self.buffers: Dict[str, deque] = {t: deque(maxlen=self.window_bars) for t in self.tickers}

        # Handle kết nối để stop sau này
        self._event = None

    # ---- callback nội bộ (nhận BarDataUpdate từ FiinQuantX) ----
    def _on_update(self, data: BarDataUpdate):
        df = data.to_dataFrame()

        # Ép kiểu & sort để chắc chắn
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['ticker', 'timestamp'])

        # Cập nhật từng mã
        for tkr, g in df.groupby('ticker', sort=False):
            if tkr not in self.buffers:
                # Nếu có mã lạ phát sinh (không nằm trong list), bỏ qua
                continue
            # Append từng dòng vào deque để đảm bảo "bỏ 1 thêm 1" khi đầy
            for _, row in g.iterrows():
                self.buffers[tkr].append(row.to_dict())
            # Lấy ra cửa sổ N nến hiện tại
            win_list = list(self.buffers[tkr])
            if len(win_list) == 0:
                continue
            df_win = pd.DataFrame(win_list)
            # Gọi callback do người dùng định nghĩa (ví dụ: tính RSI/VSA → phát tín hiệu)
            try:
                self.on_window(df_win)
            except Exception as e:
                print(f"⚠️ Lỗi trong on_window({tkr}): {e}")

    # ---- callback mặc định: chỉ in ra vài dòng ----
    @staticmethod
    def _print_window(df_window: pd.DataFrame):
        tkr = df_window['ticker'].iloc[-1]
        last_ts = df_window['timestamp'].iloc[-1]
        print(f"[{tkr}] window({len(df_window)}): đến {last_ts} | close={df_window['close'].iloc[-1]}")

    # ---- BẮT ĐẦU STREAM ----
    def start(self):
        print(f"🚀 Start stream: {self.tickers} | by={self.by} | init_period={self.init_period} | window={self.window_bars}")
        self._event = self.client.Fetch_Trading_Data(
            realtime=True,
            tickers=self.tickers,
            fields=FIELDS,
            adjusted=self.adjusted,
            by=self.by,
            period=self.init_period,                      # chỉ dùng lúc khởi động
            callback=self._on_update,
            wait_for_full_timeFrame=self.wait_for_full_timeFrame
        )
        self._event.get_data()
        return self

    # ---- DỪNG STREAM ----
    def stop(self):
        if self._event is not None:
            print("🛑 Stopping stream ...")
            self._event.stop()


# =========================
# 2) API TIỆN DỤNG DÙNG TRONG main.py
# =========================

def start_core_stream(
    by: str = DEFAULT_BY,
    init_period: int = DEFAULT_INIT_PERIOD,
    window_bars: int = DEFAULT_WINDOW_BARS,
    on_window: Optional[Callable[[pd.DataFrame], None]] = None,
    wait_for_full_timeFrame: bool = True,
):
    """
    Bật stream cho 5 mã CORE (luôn chạy).
    Trả về instance để main.py giữ và stop() khi cần.
    """
    streamer = SlidingWindowStreamer(
        tickers=CORE_TICKERS,
        by=by,
        init_period=init_period,
        window_bars=window_bars,
        on_window=on_window,
        wait_for_full_timeFrame=wait_for_full_timeFrame
    )
    return streamer.start()


def start_optional_stream(
    include_core: bool = True,
    by: str = DEFAULT_BY,
    init_period: int = DEFAULT_INIT_PERIOD,
    window_bars: int = DEFAULT_WINDOW_BARS,
    on_window: Optional[Callable[[pd.DataFrame], None]] = None,
    wait_for_full_timeFrame: bool = False,
):
    """
    Bật stream bật thêm các mã OPTIONAL.
    - include_core=True: chạy CORE + OPTIONAL trong stream này (thường dùng khi muốn gom tất cả).
    - include_core=False: chỉ OPTIONAL (để tách luồng với CORE).
    """
    tickers = (CORE_TICKERS + OPTIONAL_TICKERS) if include_core else OPTIONAL_TICKERS
    streamer = SlidingWindowStreamer(
        tickers=tickers,
        by=by,
        init_period=init_period,
        window_bars=window_bars,
        on_window=on_window,
        wait_for_full_timeFrame=wait_for_full_timeFrame
    )
    return streamer.start()


# =========================
# 3) HÀM LỊCH SỬ (BACKTEST)
# =========================
def fetch_history(
    tickers: List[str],
    by: str = DEFAULT_BY,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    adjusted: bool = True,
) -> pd.DataFrame:
    """
    Lấy dữ liệu lịch sử (không realtime). Nếu thiếu from_date/to_date,
    tự động lấy 120 ngày gần nhất (hoặc 10 phiên cho intraday nếu bạn muốn chỉnh).
    """
    client = get_client()

    # ==== điền mặc định nếu thiếu ====
    if to_date is None:
        to_dt = datetime.now()
        # FiinQuantX chấp nhận chuỗi 'YYYY-MM-DD HH:MM:SS' hoặc 'YYYY-MM-DD'
        to_date = to_dt.strftime("%Y-%m-%d %H:%M:%S")

    if from_date is None:
        # với daily: 120 ngày là an toàn để có giá đóng cửa hôm qua
        lookback_days = 120 if by.endswith("d") or by == "1d" else 10
        from_dt = datetime.now() - timedelta(days=lookback_days)
        from_date = from_dt.strftime("%Y-%m-%d %H:%M:%S")

    event = client.Fetch_Trading_Data(
        realtime=False,
        tickers=tickers,
        fields=FIELDS,
        adjusted=adjusted,
        by=by,
        from_date=from_date,
        to_date=to_date
    )
    df = event.get_data()
    if isinstance(df, pd.DataFrame) and not df.empty:
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['ticker', 'timestamp']).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=['ticker','timestamp',*FIELDS])
    return df


# =========================
# 4) VÍ DỤ DÙNG NHANH (chạy thử)
# =========================
# if __name__ == "__main__":
#     # Ví dụ: chỉ chạy CORE, cửa sổ 20 nến (đủ SMA20); callback mặc định chỉ in ra
#     core_stream = start_core_stream(window_bars=20, by='15m')

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         core_stream.stop()
