# =========================
# signal.py
# =========================
import numpy as np
import pandas as pd

# ===== RSI tính toán =====


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    roll_up = pd.Series(gain).rolling(period, min_periods=1).mean()
    roll_down = pd.Series(loss).rolling(period, min_periods=1).mean()

    rs = roll_up / (roll_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return pd.Series(rsi, index=series.index)


# ===== Thuật toán tín hiệu =====
def generate_trade_signals(df: pd.DataFrame,
                           rsi_buy_th: float = 35,
                           rsi_sell_th: float = 65,
                           tplus2_bars: int = 2,
                           vol_lo: float = 0.85, vol_hi: float = 1.2,
                           spr_lo: float = 0.8, spr_hi: float = 1.2,
                           spr_lookback: int = 20) -> pd.DataFrame:
    out = df.sort_values(["ticker", "timestamp"]).copy()

    # ---- thêm RSI ----
    out["rsi"] = out.groupby("ticker")["close"].transform(
        lambda x: compute_rsi(x, 14))

    def _per_ticker(g: pd.DataFrame) -> pd.DataFrame:
        g = g.copy()

        # ====== VSA features ======
        prev_close = g["close"].shift(1)
        g["_bar"] = np.where(g["close"] > prev_close, "up",
                             np.where(g["close"] < prev_close, "down", "flat"))

        sma20_vol = g["volume"].rolling(20, min_periods=1).mean()
        vratio = g["volume"] / sma20_vol.replace(0, np.nan)
        g["_vol"] = np.select([vratio < vol_lo, vratio <= vol_hi, vratio > vol_hi],
                              ["low", "medium", "high"], default=np.nan)

        spread = (g["high"] - g["low"]).clip(lower=0)
        spr_ref = spread.rolling(spr_lookback, min_periods=1).mean()
        sratio = spread / spr_ref.replace(0, np.nan)
        g["_spr"] = np.select([sratio < spr_lo, sratio <= spr_hi, sratio > spr_hi],
                              ["low", "medium", "high"], default=np.nan)

        q1 = g["low"] + (g["high"] - g["low"]) / 3.0
        q2 = g["low"] + 2.0 * (g["high"] - g["low"]) / 3.0
        g["_cthird"] = np.select([g["close"] < q1, g["close"] < q2],
                                 ["bottom", "middle"], default="top")

        # ====== Patterns ======
        weakness_a = ((g["_bar"] == "down") & (g["_vol"] == "high") & (
            g["_spr"].isin(["low", "medium"])) & (g["_cthird"].isin(["middle", "bottom"])))
        no_demand = ((g["_bar"] == "up") & (g["_vol"] == "low") & (
            g["_spr"].isin(["low", "medium"])) & (g["_cthird"].isin(["middle", "top"])))
        upthrust = ((g["_bar"] == "up") & (g["_spr"] == "high") & (
            g["_cthird"] == "bottom") & (g["_vol"].isin(["medium", "high"])))
        buying_climax = ((g["_bar"] == "up") & (g["_spr"] == "high") &
                         (g["_vol"] == "high") & (g["_cthird"] == "middle"))

        power_a = ((g["_bar"] == "up") & (g["_spr"] == "high") & (
            g["_vol"].isin(["medium", "high"])) & (g["_cthird"] == "top"))
        force_b = ((g["_bar"] == "down") & (g["_spr"].isin(["medium", "high"])) &
                   (g["_vol"] == "high") & (g["_cthird"] == "bottom"))
        reverse_upthrust = (
            (g["_spr"] == "high") & (
                g["_vol"] == "high") & (
                g["_cthird"] == "top"))
        selling_climax = ((g["_bar"] == "down") & (g["_spr"] == "high") &
                          (g["_vol"] == "high") & (g["_cthird"] == "middle"))

        sos = pd.concat(
            [power_a, force_b, reverse_upthrust, selling_climax], axis=1)
        sow = pd.concat(
            [weakness_a, no_demand, upthrust, buying_climax], axis=1)

        g["buy_score"] = sos.sum(axis=1).astype(int)
        g["sell_score"] = sow.sum(axis=1).astype(int)

        # Lưu pattern khớp
        g["pattern"] = ""
        g.loc[weakness_a, "pattern"] += "weakness_a,"
        g.loc[no_demand, "pattern"] += "no_demand,"
        g.loc[upthrust, "pattern"] += "upthrust,"
        g.loc[buying_climax, "pattern"] += "buying_climax,"
        g.loc[power_a, "pattern"] += "power_a,"
        g.loc[force_b, "pattern"] += "force_b,"
        g.loc[reverse_upthrust, "pattern"] += "reverse_upthrust,"
        g.loc[selling_climax, "pattern"] += "selling_climax,"
        g["pattern"] = g["pattern"].str.rstrip(",")

        # BUY khi có pattern SOS và RSI < ngưỡng
        buy_raw = (g["buy_score"] >= 1) & (g["rsi"] < rsi_buy_th)

        # SELL khi có pattern SOW và RSI > ngưỡng
        sell_raw = (g["sell_score"] >= 1) & (g["rsi"] > rsi_sell_th)

        # Loại xung đột
        conflict = buy_raw & sell_raw
        buy_raw &= ~conflict
        sell_raw &= ~conflict

        # State machine
        sig = np.zeros(len(g), dtype=int)
        seen_first_buy = False
        last_buy_idx = None

        for i in range(len(g)):
            if not seen_first_buy:
                if buy_raw.iloc[i]:
                    sig[i] = 1
                    seen_first_buy = True
                    last_buy_idx = i
                continue

            placed = False
            if buy_raw.iloc[i]:
                sig[i] = 1
                last_buy_idx = i
                placed = True

            if (not placed) and sell_raw.iloc[i]:
                if (last_buy_idx is not None) and (
                        (i - last_buy_idx) >= tplus2_bars):
                    sig[i] = -1

        g["signal"] = sig
        return g

    out = out.groupby("ticker", group_keys=False).apply(_per_ticker)
    return out


# ===== Hàm xử lý mỗi khi có dữ liệu mới từ data.py =====
def handle_new_window(df_window: pd.DataFrame) -> pd.DataFrame:
    """
    Nhận df_window (N nến gần nhất của 1 ticker),
    trả về dataframe có tín hiệu mua/bán.
    """
    signals = generate_trade_signals(df_window)
    latest = signals.iloc[-1:]  # chỉ lấy hàng mới nhất để hiển thị
    print("📈 New signal:")
    print(latest[["ticker", "timestamp", "close", "rsi",
          "pattern", "buy_score", "sell_score", "signal"]])
    return latest
