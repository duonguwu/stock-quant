#!/usr/bin/env python3
"""
Backfill realtime_signals từ historical_data theo khoảng ngày
- Đọc bars 15m trong khoảng [start_date, end_date]
- Tính features qua SimpleFeatureEngine
- Chuẩn hóa và predict bằng RealModelInference
- Lưu BUY/SELL ở ngưỡng CONF_THRESHOLD vào collection realtime_signals

Chạy: chỉ cần sửa các hằng số dưới đây rồi chạy script.
"""
from datetime import datetime, timedelta
from typing import List, Dict

import pandas as pd
from pymongo import MongoClient, UpdateOne

from feature_engine import SimpleFeatureEngine
from core.model_inference import RealModelInference

# =====================
# Hard-coded parameters
# =====================
MONGO_URI = (
    "mongodb://admin:password123@localhost:27017/"
    "trading_signals?authSource=admin"
)
DB_NAME = None  # Lấy theo default db từ URI (trading_signals)
HISTORICAL_COL = "historical_data"
SIGNALS_COL = "realtime_signals"
TICKERS = ["CTG", "MBB", "ACB", "QNS", "MSH"]
START_DATE = "2025-09-12"  # YYYY-MM-DD (VN time)
END_DATE = "2025-09-18"    # YYYY-MM-DD (VN time)
CONF_THRESHOLD = 0.5        # Đổi sang 0.5 nếu muốn
# =====================


def iso_floor_minute(ts: pd.Timestamp) -> str:
    if isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    ts = ts.replace(second=0, microsecond=0)
    return ts.isoformat(timespec="minutes")


def main() -> None:
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d") + timedelta(days=1)

    client = MongoClient(MONGO_URI)
    db = client.get_default_database() if DB_NAME is None else client[DB_NAME]
    historical = db[HISTORICAL_COL]
    signals = db[SIGNALS_COL]

    # 1) Load historical bars for tickers in date range
    print(
        f"📥 Loading historical_data [{START_DATE} → {END_DATE}] "
        f"for {len(TICKERS)} tickers..."
    )
    cursor = historical.find({
        "ticker": {"$in": TICKERS},
        "timestamp": {"$gte": start_dt, "$lt": end_dt}
    })
    rows: List[Dict] = list(cursor)

    if not rows:
        print("⚠️ No historical bars found in the given range.")
        return

    df = pd.DataFrame(rows)
    # Ensure required base columns exist
    for col in ["bu", "sd"]:
        if col not in df.columns:
            df[col] = 0

    base_cols = [
        "ticker", "timestamp", "open", "high", "low",
        "close", "volume", "bu", "sd"
    ]
    missing_base = [c for c in base_cols if c not in df.columns]
    if missing_base:
        raise ValueError(f"Missing required base columns: {missing_base}")

    df = df.sort_values(["ticker", "timestamp"]).reset_index(drop=True)
    print(f"✅ Loaded {len(df)} bars → {df['ticker'].nunique()} tickers")

    # 2) Feature engineering
    print("🔧 Engineering features...")
    fe = SimpleFeatureEngine()
    features_df = fe.engineer_features(df)

    # Loại bỏ các cột meta/phi số có thể len vào features
    meta_cols = [
        "_id", "source", "finalized", "inserted_at", "updated_at"
    ]
    drop_cols = [c for c in meta_cols if c in features_df.columns]
    if drop_cols:
        features_df = features_df.drop(columns=drop_cols)

    # Bỏ mọi cột object trừ các cột định danh thời gian/mã
    keep_object = {"ticker", "timestamp"}
    for col in list(features_df.columns):
        if features_df[col].dtype == object and col not in keep_object:
            try:
                features_df[col] = pd.to_numeric(features_df[col])
            except Exception:
                features_df = features_df.drop(columns=[col])

    # 3) Chuẩn bị danh sách feature đúng thứ tự như lúc train
    #    (theo đúng cách ở app/test_realtime.py)
    print("🧠 Loading model & predicting signals...")
    infer = RealModelInference()

    feature_cols = fe.get_feature_list(features_df)
    features_only = features_df[feature_cols].fillna(0)
    tickers_series = features_df["ticker"].tolist()

    # Truyền trực tiếp features theo đúng thứ tự vào model
    results = infer.predict_with_confidence(features_only, tickers_series)

    conf_key = f"conf_{CONF_THRESHOLD}"
    if conf_key not in results:
        # Nếu không có đúng key, chọn key đầu tiên (phòng hờ)
        conf_key = sorted(results.keys())[0]

    level = results[conf_key]
    level_signals: List[Dict] = level.get("signals", [])

    # 4) Map predictions back to bar rows to extract price/volume/timestamps
    print(f"📝 Saving BUY/SELL at {conf_key} to {SIGNALS_COL}...")
    ops: List[UpdateOne] = []

    # Join back minimal info by index alignment
    features_df = features_df.reset_index(drop=True)
    df = df.reset_index(drop=True)

    for i, sig in enumerate(level_signals):
        if sig.get("action") == "HOLD":
            continue
        ticker = sig["ticker"]
        # Safety: match same row i
        if i >= len(df):
            continue
        row = df.iloc[i]
        if row.get("ticker") != ticker:
            # fallback: find nearest by ticker and index
            candidates = df.index[df["ticker"] == ticker].tolist()
            if not candidates:
                continue
            row = df.loc[candidates[-1]]

        ts = row["timestamp"]
        ts_floor_iso = iso_floor_minute(ts)
        doc_id = f"{ticker}_{conf_key}_{ts_floor_iso}"
        price = float(row.get("close", 0))
        volume = int(row.get("volume", 0))
        open_p = float(row.get("open", price))
        change_pct = (price - open_p) / open_p if open_p else 0.0

        doc = {
            "_id": doc_id,
            "ticker": ticker,
            "action": sig["action"],
            "confidence": float(sig.get("confidence", 0.0)),
            "confidence_level": conf_key,
            "confidence_threshold": float(level["confidence_threshold"]),
            "timestamp": ts,
            "created_at": datetime.utcnow(),
            "price": price,
            "volume": volume,
            "change_pct": float(change_pct),
            "source": "backfill",
        }

        ops.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))

    if ops:
        res = signals.bulk_write(ops, ordered=False)
        upserts = (res.upserted_count if hasattr(res, "upserted_count") else 0)
        mods = res.modified_count
        print(
            f"✅ Saved signals: upserted={upserts}, modified={mods}, "
            f"total_ops={len(ops)}"
        )
    else:
        print("ℹ️ No BUY/SELL signals to save.")


if __name__ == "__main__":
    main()
