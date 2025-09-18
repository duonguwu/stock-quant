# signals.py — ML inference "nguyên bản" 3 lớp: [SELL, HOLD, BUY]
from __future__ import annotations
import numpy as np
import pandas as pd
import joblib
from typing import List, Tuple

MODEL_PATH = "xgboost_model.pkl"
SCALER_PATH = "feature_scaler.pkl"

# Ngưỡng tự tin tối thiểu để phát tín hiệu (nếu thấp hơn -> HOLD)
CONFIDENCE_THRESHOLD = 0.60  # bạn có thể chỉnh 0.50–0.70

_model, _scaler = None, None

# ----- một số chỉ báo cơ bản để tạo feature INPUT cho model -----


def _sma(s, n): return s.rolling(n, min_periods=1).mean()
def _ema(s, n): return s.ewm(span=n, adjust=False).mean()


def _rsi(close: pd.Series, n: int = 14):
    diff = close.diff()
    up = diff.clip(lower=0.0)
    down = (-diff).clip(lower=0.0)
    rs = _ema(up, n) / (_ema(down, n) + 1e-12)
    return 100 - (100 / (1 + rs))


def _macd(close: pd.Series, f=12, s=26, signal=9):
    ema_f = _ema(close, f)
    ema_s = _ema(close, s)
    macd = ema_f - ema_s
    macd_signal = _ema(macd, signal)
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def _bollinger(close: pd.Series, n=20, k=2.0):
    ma = _sma(close, n)
    std = close.rolling(n, min_periods=1).std(ddof=0)
    upper = ma + k * std
    lower = ma - k * std
    pct = (close - lower) / (upper - lower + 1e-12)
    return upper, lower, pct


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, n=14):
    prev = close.shift(1)
    tr = pd.concat([(high - low), (high - prev).abs(),
                   (low - prev).abs()], axis=1).max(axis=1)
    return _ema(tr, n)


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, n=14):
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = _atr(high, low, close, 1)
    atr_n = _ema(tr, n)
    plus_di = 100 * \
        (_ema(pd.Series(plus_dm, index=high.index), n) / (atr_n + 1e-12))
    minus_di = 100 * \
        (_ema(pd.Series(minus_dm, index=high.index), n) / (atr_n + 1e-12))
    dx = 100 * (plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-12)
    return _ema(dx, n)


def _mfi(high, low, close, volume, n=14):
    tp = (high + low + close) / 3.0
    rmf = tp * volume
    pos = (tp > tp.shift(1)).astype(float)
    neg = (tp < tp.shift(1)).astype(float)
    pos_mf = (rmf * pos).rolling(n, min_periods=1).sum()
    neg_mf = (rmf * neg).rolling(n, min_periods=1).sum()
    mr = pos_mf / (neg_mf + 1e-12)
    return 100 - (100 / (1 + mr))


def _obv(close, volume):
    direction = np.sign(close.diff().fillna(0))
    return (volume * direction).fillna(0).cumsum()


def _vol_rank(volume, n=20):
    return volume.rolling(n, min_periods=1).rank(pct=True)


def _zscore(s, n=20):
    m = s.rolling(n, min_periods=1).mean()
    sd = s.rolling(n, min_periods=1).std(ddof=0)
    return (s - m) / (sd + 1e-12)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Tính feature kỹ thuật (INPUT cho ML, KHÔNG dùng rule TA để ra tín hiệu)."""
    df = df.copy()
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]

    df["ret_1"] = c.pct_change(1).fillna(0.0)
    df["ret_5"] = c.pct_change(5).fillna(0.0)
    df["ret_20"] = c.pct_change(20).fillna(0.0)

    df["sma20"] = _sma(c, 20)
    df["sma50"] = _sma(c, 50)
    df["ema12"] = _ema(c, 12)
    df["ema26"] = _ema(c, 26)

    df["rsi"] = _rsi(c, 14)
    macd, macd_sig, macd_hist = _macd(c)
    df["macd"] = macd
    df["macd_signal"] = macd_sig
    df["macd_hist"] = macd_hist

    bb_hi, bb_lo, bb_pct = _bollinger(c)
    df["bb_high"] = bb_hi
    df["bb_low"] = bb_lo
    df["bb_pct"] = bb_pct

    df["atr"] = _atr(h, l, c, 14)
    df["adx"] = _adx(h, l, c, 14)
    df["mfi"] = _mfi(h, l, c, v, 14)
    df["obv"] = _obv(c, v)

    df["vol_rank_20"] = _vol_rank(v, 20)
    df["zscore_ret_20"] = _zscore(df["ret_1"], 20)

    df["above_trend"] = (c > df["sma20"]).astype(float)
    df["atr_ratio"] = (df["atr"] / (c.replace(0, np.nan))).fillna(0.0)
    df["active_volume_ratio"] = (v / (_sma(v, 20) + 1e-12)).fillna(0.0)
    return df

# ----- model helpers -----


def _load_model_scaler() -> Tuple[object, object]:
    global _model, _scaler
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)
    return _model, _scaler


def _expected_features(df_feat: pd.DataFrame, scaler) -> List[str]:
    if hasattr(scaler, "feature_names_in_"):
        return list(scaler.feature_names_in_)
    meta = {
        "ticker",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "bu",
        "sd"}
    return [c for c in df_feat.columns if c not in meta]


def _prepare_X(df_feat: pd.DataFrame, scaler) -> np.ndarray:
    exp = _expected_features(df_feat, scaler)
    aligned = df_feat.reindex(columns=exp, fill_value=0.0).replace(
        [np.inf, -np.inf], np.nan).fillna(0.0)
    return aligned.to_numpy(dtype=float, copy=False), exp

# ----- inference (nguyên bản GitHub: 3 lớp + threshold) -----


def generate_trade_signals(df_window: pd.DataFrame) -> pd.DataFrame:
    """
    - predict_proba -> xác suất cho 3 lớp [SELL, HOLD, BUY]
    - action = argmax(prob)
    - nếu max_prob < CONFIDENCE_THRESHOLD => action = HOLD
    - map: SELL -> -1, HOLD -> 0, BUY -> +1
    """
    assert "timestamp" in df_window.columns, "Thiếu 'timestamp'."
    model, scaler = _load_model_scaler()

    df = df_window.sort_values("timestamp").reset_index(drop=True).copy()
    df_feat = build_features(df)

    X, _ = _prepare_X(df_feat, scaler)
    Xs = scaler.transform(X) if scaler is not None else X

    # kỳ vọng shape = (N, 3) theo thứ tự [SELL, HOLD, BUY]
    probs = model.predict_proba(Xs)
    if probs.shape[1] != 3:
        # Nếu model của bạn là binary thì fallback: class1=BUY, class0=SELL
        p_buy = probs[:, 1] if probs.shape[1] == 2 else np.zeros(len(df))
        cls = (p_buy >= 0.5).astype(int)
        conf = np.where(cls == 1, p_buy, 1.0 - p_buy)
        # áp threshold như “nguyên bản” engine (nếu conf<thr => HOLD)
        action = np.where(
            conf < CONFIDENCE_THRESHOLD, 1, np.where(
                cls == 1, 2, 0))  # 0=SELL,1=HOLD,2=BUY
        signal = np.select([action == 2, action == 1, action == 0], [1, 0, -1])
        # hiển thị cùng một giá trị
        conf_show = np.where(action == 1, conf, conf)
        return pd.DataFrame({
            "ticker": df["ticker"],
            "timestamp": df["timestamp"],
            "close": df.get("close"),
            "ml_confidence": conf_show,
            "signal": signal
        })

    # 3-class:
    argmax_idx = np.argmax(probs, axis=1)             # 0=SELL, 1=HOLD, 2=BUY
    max_prob = probs[np.arange(len(probs)), argmax_idx]
    # nếu thấp hơn threshold => HOLD
    action_idx = np.where(max_prob < CONFIDENCE_THRESHOLD, 1, argmax_idx)

    # map sang tín hiệu
    signal = np.select([action_idx == 2, action_idx ==
                       1, action_idx == 0], [1, 0, -1])
    # để tham khảo, ghi lại proba BUY/SELL/HOLD
    df_out = pd.DataFrame({
        "ticker": df["ticker"],
        "timestamp": df["timestamp"],
        "close": df.get("close"),
        "p_sell": probs[:, 0],
        "p_hold": probs[:, 1],
        "p_buy": probs[:, 2],
        "ml_confidence": max_prob,
        "signal": signal
    })
    return df_out


def make_on_window(notifier, always_broadcast: bool = True):
    def _on_window(df_window: pd.DataFrame):
        out = generate_trade_signals(df_window)
        last = out.iloc[-1]

        pct = np.nan
        if len(out) >= 2 and pd.notna(df_window["close"].iloc[-2]):
            prev = float(df_window["close"].iloc[-2])
            cur = float(last.get("close", np.nan))
            if prev != 0 and cur == cur:  # not NaN
                pct = (cur / prev - 1.0) * 100.0

        # Ưu tiên hiển thị p_buy nếu có, nếu không có thì hiển thị
        # "ml_confidence"
        proba_display = float(
            last.get(
                "p_buy",
                last.get(
                    "ml_confidence",
                    np.nan)))
        notifier.broadcast(notifier.format_ml_message(
            ts=last["timestamp"],
            ticker=str(last.get("ticker", "UNKNOWN")),
            signal=int(last["signal"]),   # -1 / 0 / +1
            proba=proba_display,
            price=float(last.get("close", np.nan)),
            pct=pct
        )) if (always_broadcast or int(last["signal"]) != 0) else None
    return _on_window
