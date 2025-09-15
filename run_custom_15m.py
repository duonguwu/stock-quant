import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.data.data_fetcher import create_data_fetcher
from src.data.feature_engineering import create_feature_engineer
from src.utils.config_loader import config_loader


def _ensure_backtest_data_dir() -> str:
    base_dir = "data/backtest_data"
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _unique_filename(prefix: str = "custom_test_data") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.csv"


def compute_backtest_window(as_of_date: datetime, max_window_bars: int = 504, buffer_bars: int = 90, bars_per_day: int = 18):
    """
    Tính khoảng thời gian cần lấy dữ liệu cho backtest 15m.
    - max_window_bars: cửa sổ lớn nhất (504 bar ~ 28 ngày giao dịch)
    - buffer_bars: thêm dự phòng (90 bar ~ 5 ngày giao dịch)
    - bars_per_day: số bar 15m trong 1 ngày (≈18 bar)
    """
    total_bars = max_window_bars + buffer_bars
    need_days = int(np.ceil(total_bars / bars_per_day))  # số ngày giao dịch
    # chuyển sang ngày lịch (cộng thêm cuối tuần/nghỉ lễ: ~1.5x)
    need_calendar_days = int(need_days * 1.5)
    start_date = as_of_date - timedelta(days=need_calendar_days)
    return start_date.strftime("%Y-%m-%d"), as_of_date.strftime("%Y-%m-%d")


def prepare_backtest_features(
    username, password, tickers, start_date, end_date, config
):
    # 1. Fetch raw data
    fetcher = create_data_fetcher(username, password)
    data = fetcher.fetch_trading_data(
        tickers=tickers,
        fields=["open", "high", "low", "close", "volume", "bu", "sd"],  # thêm bu/sd nếu có
        start_date=start_date,
        end_date=end_date,
        timeframe="15m",
        adjusted=True,
    )
    data = fetcher.validate_data(data)

    # 2. Feature engineering
    feature_engineer = create_feature_engineer(fetcher.client)
    features = feature_engineer.engineer_features(data, config)
    return features


if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("FIIN_USERNAME")
    password = os.getenv("FIIN_PASSWORD")
    tickers = ["CTG", "MBB", "ACB", "QNS", "MSH"]

    # Xác định ngày kết thúc = hôm nay
    as_of_date = datetime.now()
    start_date, end_date = compute_backtest_window(as_of_date)

    # Load config
    config = {}
    config.update(config_loader.load_config("data_config_15m"))
    config.update(config_loader.load_config("labeling_config_15m"))

    # Feature engineering cho dữ liệu mới
    features = prepare_backtest_features(
        username, password, tickers, start_date, end_date, config
    )

    # ======= Đảm bảo đủ feature giống file test gốc =======
    ref_path = "data/final/test_data.csv"
    if os.path.exists(ref_path):
        test_ref = pd.read_csv(ref_path)
        ignore_cols = ["label", "hit_time", "hit_type", "ub", "lb", "vbar_end"]
        feature_cols = [col for col in test_ref.columns if col not in ignore_cols]

        for col in feature_cols:
            if col not in features.columns:
                features[col] = np.nan

        features = features[feature_cols]
    else:
        print(
            f"⚠️ Không tìm thấy file tham chiếu {ref_path}, "
            "chỉ lưu features như hiện tại."
        )

    # Save file để predict/backtest
    out_dir = _ensure_backtest_data_dir()
    out_file = os.path.join(out_dir, _unique_filename())
    features.to_csv(out_file, index=False)
    print(f"✅ Saved file: {out_file}")
