#!/usr/bin/env python3
"""
Backfill realtime_signals từ historical_data theo khoảng ngày với logic entry/exit
- Đọc bars 15m trong khoảng [start_date, end_date]
- Tính features qua SimpleFeatureEngine
- Chuẩn hóa và predict bằng RealModelInference
- Áp dụng logic entry/exit như backtest engine:
  * Entry: Khi có BUY signal → lưu BUY vào DB
  * Exit: Khi có SELL signal hoặc hết 16 bars → lưu SELL vào DB
  * Hold: Không lưu gì cả

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
CONF_THRESHOLD = 0.4        # Đổi sang 0.5 nếu muốn
HOLDING_PERIOD_BARS = 16    # Hold tối đa 16 bars (khoảng 1 ngày)
# =====================


def iso_floor_minute(ts: pd.Timestamp) -> str:
    if isinstance(ts, pd.Timestamp):
        ts = ts.to_pydatetime()
    ts = ts.replace(second=0, microsecond=0)
    return ts.isoformat(timespec="minutes")


def simulate_ticker_trades_15m(
    data: pd.DataFrame,
    signals: pd.DataFrame,
    ticker: str,
    holding_period_bars: int = 16,
    transaction_cost: float = 0.0005,
) -> List[Dict]:
    """Simulate 15m trades for single ticker (long-only) - tương tự backtest engine"""
    trades = []
    position = 0  # 0: no position, 1: holding
    entry_date = None
    entry_price = None
    entry_confidence = None
    entry_idx = None

    for i, (idx, row) in enumerate(data.iterrows()):
        current_signal = signals.loc[idx, 'signal']
        current_confidence = signals.loc[idx, 'confidence']
        current_price = row['close']
        current_date = row['timestamp']

        # ======= LOGIC LONG-ONLY =======
        if position == 0:
            # Buy when signal == 1, not holding
            if current_signal == 1:
                position = 1
                entry_date = current_date
                # Buy with transaction cost
                entry_price = current_price * (1 + transaction_cost)
                entry_confidence = current_confidence
                entry_idx = i

        elif position == 1:
            bars_held = i - entry_idx

            # Sell conditions: signal == -1, or exceeded holding period
            if current_signal == -1 or bars_held >= holding_period_bars:
                # Sell with transaction cost
                exit_price = current_price * (1 - transaction_cost)
                return_pct = (exit_price - entry_price) / entry_price

                # Convert bars to days
                holding_days = bars_held / 18  # 18 bars per day

                # Tạo trade record
                trade = {
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'ticker': ticker,
                    'signal': 1,  # Entry is always 1
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return_pct': return_pct,
                    'holding_bars': bars_held,
                    'holding_days': holding_days,
                    'confidence': entry_confidence,
                }
                trades.append(trade)

                # Reset state
                position = 0
                entry_date = None
                entry_price = None
                entry_confidence = None
                entry_idx = None

    # Force exit at end if still holding
    if position == 1:
        last_price = data.iloc[-1]['close'] * (1 - transaction_cost)
        bars_held = len(data) - entry_idx - 1
        holding_days = bars_held / 18

        trade = {
            'entry_date': entry_date,
            'exit_date': data.iloc[-1]['timestamp'],
            'ticker': ticker,
            'signal': 1,
            'entry_price': entry_price,
            'exit_price': last_price,
            'return_pct': (last_price - entry_price) / entry_price,
            'holding_bars': bars_held,
            'holding_days': holding_days,
            'confidence': entry_confidence,
        }
        trades.append(trade)

    return trades


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

    # 4) Map predictions back to bar rows để tạo signals DataFrame
    print(f"📝 Processing signals at {conf_key}...")

    # Join back minimal info by index alignment
    features_df = features_df.reset_index(drop=True)
    df = df.reset_index(drop=True)

    # Tạo signals DataFrame cho từng ticker
    all_trades = []

    # Tạo mapping từ ticker đến signals của ticker đó
    ticker_signals_map = {}
    for i, sig in enumerate(level_signals):
        ticker = sig.get('ticker', '')
        if ticker not in ticker_signals_map:
            ticker_signals_map[ticker] = []
        
        ticker_signals_map[ticker].append({
            'signal': 1 if sig.get('action') == 'BUY' else -1 if sig.get('action') == 'SELL' else 0,
            'confidence': sig.get('confidence', 0.0)
        })

    print(f" Signals per ticker: {[(k, len(v)) for k, v in ticker_signals_map.items()]}")

    for ticker in TICKERS:
        ticker_data = df[df['ticker'] == ticker].copy()
        if len(ticker_data) == 0:
            print(f"⚠️ No data for {ticker}")
            continue
        
        # Lấy signals cho ticker này
        ticker_signals = ticker_signals_map.get(ticker, [])
        if len(ticker_signals) == 0:
            print(f"⚠️ No signals for {ticker}")
            continue
        
        # Tạo signals DataFrame cho ticker này
        signals_df = pd.DataFrame(ticker_signals)
        # Đảm bảo có đủ signals cho data
        if len(signals_df) < len(ticker_data):
            # Pad với HOLD signals nếu thiếu
            missing = len(ticker_data) - len(signals_df)
            pad_signals = pd.DataFrame({
                'signal': [0] * missing,
                'confidence': [0.0] * missing
            })
            signals_df = pd.concat([signals_df, pad_signals], ignore_index=True)
        elif len(signals_df) > len(ticker_data):
            # Cắt bớt nếu thừa
            signals_df = signals_df.iloc[:len(ticker_data)]
        
        signals_df.index = ticker_data.index
        
        # Simulate trades cho ticker này
        ticker_trades = simulate_ticker_trades_15m(
            ticker_data, 
            signals_df, 
            ticker, 
            HOLDING_PERIOD_BARS
        )
        
        all_trades.extend(ticker_trades)
        print(f"✅ {ticker}: {len(ticker_trades)} trades")

    # 5) Lưu trades vào DB dưới dạng BUY/SELL signals
    print(f"💾 Saving {len(all_trades)} trades to {SIGNALS_COL}...")
    ops: List[UpdateOne] = []

    for trade in all_trades:
        # Entry signal (BUY)
        entry_ts = trade['entry_date']
        entry_ts_floor_iso = iso_floor_minute(entry_ts)
        entry_doc_id = f"{trade['ticker']}_BUY_{conf_key}_{entry_ts_floor_iso}"
        
        entry_doc = {
            "_id": entry_doc_id,
            "ticker": trade['ticker'],
            "action": "BUY",
            "confidence": float(trade['confidence']),
            "confidence_level": conf_key,
            "confidence_threshold": float(level["confidence_threshold"]),
            "timestamp": entry_ts,
            "created_at": datetime.utcnow(),
            "price": float(trade['entry_price']),
            "volume": 0,  # Không có volume info từ trade
            "change_pct": 0.0,
            "source": "backfill_entry_exit",
            "trade_id": f"{trade['ticker']}_{entry_ts_floor_iso}",
            "holding_bars": int(trade['holding_bars']),
            "holding_days": float(trade['holding_days']),
        }
        
        ops.append(UpdateOne({"_id": entry_doc_id}, {"$set": entry_doc}, upsert=True))
        
        # Exit signal (SELL)
        exit_ts = trade['exit_date']
        exit_ts_floor_iso = iso_floor_minute(exit_ts)
        exit_doc_id = f"{trade['ticker']}_SELL_{conf_key}_{exit_ts_floor_iso}"
        
        exit_doc = {
            "_id": exit_doc_id,
            "ticker": trade['ticker'],
            "action": "SELL",
            "confidence": float(trade['confidence']),
            "confidence_level": conf_key,
            "confidence_threshold": float(level["confidence_threshold"]),
            "timestamp": exit_ts,
            "created_at": datetime.utcnow(),
            "price": float(trade['exit_price']),
            "volume": 0,  # Không có volume info từ trade
            "change_pct": float(trade['return_pct']),
            "source": "backfill_entry_exit",
            "trade_id": f"{trade['ticker']}_{entry_ts_floor_iso}",
            "holding_bars": int(trade['holding_bars']),
            "holding_days": float(trade['holding_days']),
        }
        
        ops.append(UpdateOne({"_id": exit_doc_id}, {"$set": exit_doc}, upsert=True))

    if ops:
        res = signals.bulk_write(ops, ordered=False)
        upserts = (res.upserted_count if hasattr(res, "upserted_count") else 0)
        mods = res.modified_count
        print(
            f"✅ Saved signals: upserted={upserts}, modified={mods}, "
            f"total_ops={len(ops)}"
        )
        print(f"📊 Total trades: {len(all_trades)}")
        print(f"📈 BUY signals: {len(all_trades)}")
        print(f"�� SELL signals: {len(all_trades)}")
    else:
        print("ℹ️ No trades to save.")


if __name__ == "__main__":
    main()
