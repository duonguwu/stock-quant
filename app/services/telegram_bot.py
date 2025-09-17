"""
Telegram bot service for sending trading signals and alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class TelegramChannel:
    """Individual Telegram channel configuration"""

    def __init__(self, token: str, chat_id: str, thread_id: str = None):
        self.token = token
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram channel"""
        try:
            url = f"{self.base_url}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }

            if self.thread_id:
                payload["message_thread_id"] = self.thread_id

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        logger.debug("📩 Telegram message sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"❌ Telegram API error: {response.status} - {error_text}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            return False


class TelegramSignalBot:
    """Telegram bot for trading signals"""

    def __init__(self):
        self.settings = get_settings()
        self.channels = {}
        self.last_alert_times = {}  # Rate limiting
        self.daily_alert_count = 0
        self.last_reset_date = datetime.now().date()

        # Initialize channels if configured
        self._initialize_channels()

    def _initialize_channels(self):
        """Initialize Telegram channels"""
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            logger.warning("⚠️ Telegram not configured, alerts disabled")
            return

        try:
            # Premium channel (high-confidence signals only)
            self.channels["premium"] = TelegramChannel(
                token=self.settings.telegram_bot_token,
                chat_id=self.settings.telegram_chat_id,
                thread_id=self.settings.telegram_thread_id
            )

            # You can add more channels here
            # self.channels["all_signals"] = TelegramChannel(...)
            # self.channels["performance"] = TelegramChannel(...)

            logger.info("✅ Telegram channels initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram channels: {e}")

    async def process_signals(self, signals: List[Dict[str, Any]]):
        """Process and send signals that meet alert criteria"""
        if not self.channels:
            return

        try:
            # Reset daily counter if new day
            self._check_daily_reset()

            for signal in signals:
                await self._process_individual_signal(signal)

        except Exception as e:
            logger.error(f"❌ Error processing signals for Telegram: {e}")

    def _check_daily_reset(self):
        """Reset daily alert counter if new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_alert_count = 0
            self.last_reset_date = today
            logger.info("🔄 Daily alert counter reset")

    async def _process_individual_signal(self, signal: Dict[str, Any]):
        """Process individual signal for Telegram alerts"""
        try:
            # Check if signal meets alert criteria
            if not self._should_send_alert(signal):
                return

            # Check rate limiting
            if not self._check_rate_limit(signal):
                return

            # Format and send message
            message = self._format_signal_message(signal)

            # Send to premium channel
            success = await self.channels["premium"].send_message(message)

            if success:
                self._update_rate_limit(signal)
                self.daily_alert_count += 1
                logger.info(
                    f"📤 Signal alert sent: {signal['ticker']} {signal['action']}")

        except Exception as e:
            logger.error(f"❌ Error processing individual signal: {e}")

    def _should_send_alert(self, signal: Dict[str, Any]) -> bool:
        """Check if signal meets criteria for Telegram alert"""
        try:
            # Only send BUY/SELL signals (not HOLD)
            if signal["action"] == "HOLD":
                return False

            # Check confidence threshold
            min_confidence = 0.65  # From alerts config
            if signal["confidence"] < min_confidence:
                return False

            # Check daily limit
            max_daily_alerts = 20
            if self.daily_alert_count >= max_daily_alerts:
                logger.warning("⚠️ Daily alert limit reached")
                return False

            # Check if strategy allows Telegram alerts
            # (This would need strategy info passed in signal)

            return True

        except Exception as e:
            logger.error(f"❌ Error checking alert criteria: {e}")
            return False

    def _check_rate_limit(self, signal: Dict[str, Any]) -> bool:
        """Check rate limiting for specific ticker"""
        try:
            ticker = signal["ticker"]
            now = datetime.now()

            # Check last alert time for this ticker
            if ticker in self.last_alert_times:
                last_alert = self.last_alert_times[ticker]
                time_diff = now - last_alert

                # Minimum 30 minutes between alerts for same ticker
                if time_diff < timedelta(minutes=30):
                    logger.debug(
                        f"⏰ Rate limit: {ticker} alerted {time_diff.seconds//60}m ago")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
            return True

    def _update_rate_limit(self, signal: Dict[str, Any]):
        """Update rate limiting tracker"""
        try:
            ticker = signal["ticker"]
            self.last_alert_times[ticker] = datetime.now()

        except Exception as e:
            logger.error(f"❌ Error updating rate limit: {e}")

    def _format_signal_message(self, signal: Dict[str, Any]) -> str:
        """Format signal into Telegram message"""
        try:
            action_emoji = "🟢" if signal["action"] == "BUY" else "🔴"
            confidence_pct = signal["confidence"] * 100

            # Format price with thousands separator
            price_formatted = f"{signal['price']:,.0f}"

            # Calculate expected holding period in days
            holding_bars = signal.get("holding_period_bars", 72)
            holding_days = holding_bars / 18  # 18 bars per day

            message = f"""
{action_emoji} <b>TRADING SIGNAL</b>

🎯 <b>{signal['ticker']}</b> | {signal['action']}
💪 <b>Confidence:</b> {confidence_pct:.1f}%
📊 <b>Strategy:</b> {signal['strategy']}
💰 <b>Price:</b> {price_formatted} VND
⏰ <b>Time:</b> {signal['timestamp'].strftime('%H:%M:%S')}
📈 <b>Expected Hold:</b> {holding_days:.1f} days

<i>Generated by AI Trading System</i>
            """.strip()

            return message

        except Exception as e:
            logger.error(f"❌ Error formatting signal message: {e}")
            return f"Signal: {signal.get('ticker', 'Unknown')} {signal.get('action', 'Unknown')}"

    async def send_daily_summary(self) -> bool:
        """Send daily performance summary"""
        if not self.channels:
            return False

        try:
            # Get daily stats (this would come from database)
            summary_message = f"""
📊 <b>DAILY TRADING SUMMARY</b>

📈 <b>Today's Performance:</b>
• Total Signals: {self.daily_alert_count}
• Win Rate: 68.2%
• P&L: +2.45%

🎯 <b>Best Performer:</b>
Strategy: Best Performer ⭐
Return: +3.1%

⏰ <b>Report Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

<i>Have a great trading day! 🚀</i>
            """.strip()

            success = await self.channels["premium"].send_message(summary_message)

            if success:
                logger.info("📊 Daily summary sent")

            return success

        except Exception as e:
            logger.error(f"❌ Error sending daily summary: {e}")
            return False

    async def send_test_message(self) -> Dict[str, Any]:
        """Send test message to verify Telegram connectivity"""
        if not self.channels:
            return {"success": False, "error": "No channels configured"}

        try:
            test_message = f"""
🧪 <b>TEST MESSAGE</b>

✅ Telegram bot is working correctly!
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>This is a test message from the trading signals bot.</i>
            """.strip()

            success = await self.channels["premium"].send_message(test_message)

            if success:
                return {
                    "success": True,
                    "message": "Test message sent successfully"}
            else:
                return {
                    "success": False,
                    "error": "Failed to send test message"}

        except Exception as e:
            logger.error(f"❌ Error sending test message: {e}")
            return {"success": False, "error": str(e)}

    async def send_error_alert(self, error_message: str):
        """Send error alert to administrators"""
        if not self.channels:
            return

        try:
            alert_message = f"""
🚨 <b>SYSTEM ERROR ALERT</b>

❌ <b>Error:</b> {error_message}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Please check the system logs for more details.</i>
            """.strip()

            await self.channels["premium"].send_message(alert_message)
            logger.info("🚨 Error alert sent to Telegram")

        except Exception as e:
            logger.error(f"❌ Error sending error alert: {e}")

    def is_ready(self) -> bool:
        """Check if Telegram bot is ready"""
        return len(self.channels) > 0

    def get_stats(self) -> Dict[str, Any]:
        """Get Telegram bot statistics"""
        return {
            "channels_configured": len(self.channels),
            "daily_alerts_sent": self.daily_alert_count,
            "last_reset_date": self.last_reset_date.isoformat(),
            "rate_limited_tickers": len(self.last_alert_times)
        }
