import os
import pandas as pd
import numpy as np
from datetime import datetime
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


def prepare_backtest_features(
    username, password, tickers, start_date, end_date, config
):
    # 1. Fetch raw data
    fetcher = create_data_fetcher(username, password)
    data = fetcher.fetch_trading_data(
        tickers=tickers,
        fields=['open', 'high', 'low', 'close', 'volume'],
        start_date=start_date,
        end_date=end_date,
        timeframe="1d",
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
    tickers = [
        'BID', 'MBB', 'ACB', 'HDB', 'STB', 'VIB', 'NAB', 'QNS', 'GEE', 'HAH',
        'MSH', 'BFC', 'NTL', 'HBC', 'PDV',
    ]
    start_date = "2021-01-01"
    end_date = "2024-12-31"

    # Load config
    config = {}
    config.update(config_loader.load_config("data_config"))
    config.update(config_loader.load_config("labeling_config"))

    # Feature engineering cho dữ liệu mới
    features = prepare_backtest_features(
        username, password, tickers, start_date, end_date, config
    )

    # ======= Đảm bảo đủ feature giống file test gốc =======
    ref_path = "data/final/test_data.csv"
    if os.path.exists(ref_path):
        test_ref = pd.read_csv(ref_path)
        # Loại bỏ các cột meta không phải feature
        ignore_cols = ['label', 'hit_time', 'hit_type', 'ub', 'lb', 'vbar_end']
        feature_cols = [
            col for col in test_ref.columns if col not in ignore_cols
        ]
        # Bổ sung cột còn thiếu vào features
        for col in feature_cols:
            if col not in features.columns:
                features[col] = np.nan
        # Đảm bảo đúng thứ tự cột
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
