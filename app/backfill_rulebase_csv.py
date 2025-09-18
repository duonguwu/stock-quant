#!/usr/bin/env python3
"""
Import rule-based signals từ CSV vào MongoDB collection rulebase_signals.
CSV columns: ts_utc, ts_local, ticker, price, signal, method
- signal: -1 → SELL, 0 → HOLD, 1 → BUY
- _id: "{ticker}_{ACTION}_{ts_local}"
- volume: 10000 (fixed)
- timestamp: dùng ts_local (VN time) dạng "YYYY-MM-DD HH:MM:SS"
- created_at: UTC now
- source: "csv_import"
- method: theo cột method

Chạy: sửa các hằng số bên dưới rồi chạy.
"""
from datetime import datetime
from typing import List

import pandas as pd
from pymongo import MongoClient, UpdateOne

# =====================
# Hard-coded parameters
# =====================
MONGO_URI = (
    "mongodb://admin:password123@localhost:27017/"
    "trading_signals?authSource=admin"
)
DB_NAME = None  # dùng default db từ URI
COLLECTION_NAME = "rulebase_signals"
CSV_PATH = "rulebase_signals.csv"  # Đường dẫn CSV cần import
DEFAULT_VOLUME = 10000
# =====================

SIGNAL_MAP = {1: "BUY", 0: "HOLD", -1: "SELL"}


def to_naive(dt: pd.Timestamp) -> datetime:
    if isinstance(dt, pd.Timestamp):
        return dt.to_pydatetime().replace(tzinfo=None)
    return dt.replace(tzinfo=None)


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    required = ["ts_local", "ticker", "price", "signal", "method"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in CSV: {missing}")

    # Chuẩn hóa dữ liệu
    df["ts_local"] = pd.to_datetime(df["ts_local"], errors="coerce")
    df = df.dropna(subset=["ts_local", "ticker", "price", "signal"])  # chỉ giữ dòng hợp lệ
    df["action"] = df["signal"].map(lambda v: SIGNAL_MAP.get(int(v)))
    df = df.dropna(subset=["action"])  # loại bỏ signal không map được

    client = MongoClient(MONGO_URI)
    db = client.get_default_database() if DB_NAME is None else client[DB_NAME]
    col = db[COLLECTION_NAME]

    ops: List[UpdateOne] = []
    now_utc = datetime.utcnow()

    for _, r in df.iterrows():
        ts_local: datetime = to_naive(r["ts_local"])  # lưu dạng naive theo local time
        ts_local_str = ts_local.strftime("%Y-%m-%d %H:%M:%S")
        ticker = str(r["ticker"]).strip().upper()
        action = str(r["action"]).upper()
        price = float(r["price"]) if pd.notna(r["price"]) else 0.0
        method = str(r.get("method", "Wyckoff+VSA+RSI"))

        doc_id = f"{ticker}_{action}_{ts_local_str}"
        doc = {
            "_id": doc_id,
            "ticker": ticker,
            "action": action,
            "price": price,
            "volume": DEFAULT_VOLUME,
            "timestamp": ts_local,
            "created_at": now_utc,
            "method": method,
            "source": "csv_import",
        }
        ops.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))

    if ops:
        res = col.bulk_write(ops, ordered=False)
        upserts = getattr(res, "upserted_count", 0)
        mods = res.modified_count
        print(f"✅ Imported: upserted={upserts}, modified={mods}, total_ops={len(ops)}")
    else:
        print("ℹ️ No rows to import.")


if __name__ == "__main__":
    main() 