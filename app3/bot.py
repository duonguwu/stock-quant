# bot.py
import requests
from datetime import datetime


class TelegramNotifier:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def _get_last_chat_id(self):
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        r = requests.get(url, timeout=15)
        data = r.json()
        if not data.get("ok") or not data.get("result"):
            return None
        return data["result"][-1]["message"]["chat"]["id"]

    def broadcast(self, text: str):
        chat_id = self._get_last_chat_id()
        if not chat_id:
            print("⚠️ Chưa có user nào 'Start' bot hoặc không lấy được chat_id.")
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        r = requests.post(url, data=payload, timeout=15)
        print(f"📤 Gửi: {r.status_code}, {r.text}")

    def format_ml_message(self, ts, ticker, signal, proba, price, pct):
        if signal == 1:
            sig_txt = "🟢 BUY"
        elif signal == -1:
            sig_txt = "🔴 SELL"
        else:
            sig_txt = "⚪ HOLD"

        ts_str = ts if isinstance(ts, str) else (ts.strftime(
            "%Y-%m-%d %H:%M") if isinstance(ts, datetime) else str(ts))
        price_str = "—" if price != price else f"{price:,.0f}"
        pct_str = "" if pct != pct else f" ({pct:+.2f}%)"

        return (
            "🤖 <b>MACHINE LEARNING: XGBoost + Features (15m)</b>\n"
            f"⏱ <b>Thời gian:</b> {ts_str}\n"
            f"🏷 <b>Mã:</b> {ticker}\n"
            f"📌 <b>Tín hiệu:</b> {sig_txt}\n"
            f"💵 <b>Giá hiện tại:</b> {price_str}{pct_str}\n"
            f"📈 <b>P(up):</b> {proba:.3f}\n"
            f"⚙️ <i>Ngưỡng:</i> BUY≥{0.65:.2f} | SELL≤{0.35:.2f}\n"
            f"🧩 <i>Hysteresis:</i> {0.05:.2f} • <i>T+{2} bars</i>"
        )
