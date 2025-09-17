"""
Telegram Signal Bot - Tích hợp signal generator với Telegram bot
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
from app.signal_generator import TradingSignalGenerator
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class TelegramSignalBot:
    """Telegram bot tích hợp với signal generator"""
    
    def __init__(self, 
                 bot_token: str = None,
                 chat_id: str = None,
                 min_confidence: float = 0.65):
        """
        Initialize Telegram signal bot
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID  
            min_confidence: Minimum confidence để gửi alerts
        """
        try:
            settings = get_settings()
            self.bot_token = "8326359026:AAEOxRvX2cNznk4s81blkDSpJqtPu4V--Vg" or settings.telegram_bot_token
            self.chat_id = "5105911464" or settings.telegram_chat_id
        except:
            self.bot_token = bot_token
            self.chat_id = chat_id
            
        self.min_confidence = min_confidence
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Rate limiting
        self.last_alert_times = {}
        self.daily_alert_count = 0
        self.last_reset_date = datetime.now().date()
        self.max_daily_alerts = 20
        self.min_interval_minutes = 30
        
        # Signal generator
        self.signal_generator = None
        
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials not provided")
        else:
            logger.info("✅ Telegram bot initialized")
            
    def initialize_signal_generator(self, 
                                  tickers: List[str] = None):
        """Initialize signal generator and register callback"""
        try:
            self.signal_generator = TradingSignalGenerator(tickers=tickers)
            
            # Register telegram callback
            self.signal_generator.register_signal_callback(
                self._process_signals_for_telegram
            )
            
            logger.info("✅ Signal generator initialized for Telegram")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize signal generator: {e}")
            raise
            
    async def start_signal_monitoring(self):
        """Start monitoring signals and send to Telegram"""
        if not self.signal_generator:
            raise RuntimeError("Signal generator not initialized")
            
        try:
            logger.info("🔴 Starting Telegram signal monitoring...")
            
            # Send startup message
            await self.send_startup_message()
            
            # Start signal stream
            self.signal_generator.start_realtime_signal_stream()
            
            logger.info("✅ Telegram signal monitoring started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start signal monitoring: {e}")
            raise
            
    def stop_signal_monitoring(self):
        """Stop signal monitoring"""
        try:
            if self.signal_generator:
                self.signal_generator.stop_realtime_signal_stream()
            logger.info("🛑 Telegram signal monitoring stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping monitoring: {e}")
            
    async def _process_signals_for_telegram(self, signals: Dict):
        """Process signals and send to Telegram if criteria met"""
        try:
            # Reset daily counter if new day
            self._check_daily_reset()
            
            predictions = signals.get('predictions', {})
            
            for conf_key, conf_data in predictions.items():
                confidence_threshold = conf_data.get('confidence_threshold', 0)
                
                # Only process signals above minimum confidence
                if confidence_threshold >= self.min_confidence:
                    signals_list = conf_data.get('signals', [])
                    
                    for signal in signals_list:
                        await self._process_individual_signal(signal, confidence_threshold)
                        
        except Exception as e:
            logger.error(f"❌ Error processing signals for Telegram: {e}")
            
    async def _process_individual_signal(self, 
                                       signal: Dict, 
                                       confidence_threshold: float):
        """Process individual signal for Telegram"""
        try:
            logger.info(f"🔍 Processing signal: {signal}")
            
            # Check if should send alert
            should_send = self._should_send_alert(signal)
            logger.info(f"🔍 Should send alert: {should_send}")
            if not should_send:
                return
                
            # Check rate limiting
            rate_ok = self._check_rate_limit(signal)
            logger.info(f"🔍 Rate limit OK: {rate_ok}")
            if not rate_ok:
                return
                
            # Format and send message
            logger.info(f"🔍 Formatting message...")
            message = self._format_signal_message(signal, confidence_threshold)
            logger.info(f"🔍 Sending message: {message[:100]}...")
            success = await self._send_message(message)
            logger.info(f"🔍 Send result: {success}")
            
            if success:
                self._update_rate_limit(signal)
                self.daily_alert_count += 1
                logger.info(f"📤 Telegram alert sent: {signal['ticker']} {signal['action']}")
            else:
                logger.error(f"❌ Failed to send Telegram message")
                
        except Exception as e:
            logger.error(f"❌ Error processing individual signal: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    def _should_send_alert(self, signal: Dict) -> bool:
        """Check if signal meets alert criteria"""
        try:
            # Only BUY/SELL signals
            if signal.get('action') == 'HOLD':
                return False
                
            # Check confidence
            if signal.get('confidence', 0) < self.min_confidence:
                return False
                
            # Check daily limit
            if self.daily_alert_count >= self.max_daily_alerts:
                logger.warning("⚠️ Daily Telegram alert limit reached")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking alert criteria: {e}")
            return False
            
    def _check_rate_limit(self, signal: Dict) -> bool:
        """Check rate limiting for ticker"""
        try:
            ticker = signal.get('ticker')
            if not ticker:
                return False
                
            now = datetime.now()
            
            if ticker in self.last_alert_times:
                last_alert = self.last_alert_times[ticker]
                time_diff = now - last_alert
                
                if time_diff < timedelta(minutes=self.min_interval_minutes):
                    logger.debug(f"⏰ Rate limit: {ticker} alerted {time_diff.seconds//60}m ago")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
            return True
            
    def _update_rate_limit(self, signal: Dict):
        """Update rate limiting tracker"""
        try:
            ticker = signal.get('ticker')
            if ticker:
                self.last_alert_times[ticker] = datetime.now()
        except Exception as e:
            logger.error(f"❌ Error updating rate limit: {e}")
            
    def _check_daily_reset(self):
        """Reset daily counter if new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_alert_count = 0
            self.last_reset_date = today
            logger.info("🔄 Daily Telegram alert counter reset")
            
    def _format_signal_message(self, 
                             signal: Dict, 
                             confidence_threshold: float) -> str:
        """Format signal into professional Telegram message"""
        try:
            action = signal.get('action', 'UNKNOWN')
            ticker = signal.get('ticker', 'UNKNOWN')
            confidence = signal.get('confidence', 0)
            price = signal.get('price', 0)
            volume = signal.get('volume', 0)
            change_pct = signal.get('change_pct', 0)
            
            action_emoji = "🟢" if action == "BUY" else "🔴"
            change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            
            # Format numbers with thousand separators
            price_formatted = f"{price:,.0f}" if price > 0 else "N/A"
            volume_formatted = f"{volume:,.0f}" if volume > 0 else "N/A"
            
            message = f"""
{action_emoji} <b>TRADING SIGNAL</b>

🎯 <b>{ticker}</b> | <b>{action}</b>
💰 <b>Price:</b> {price_formatted} VND
{change_emoji} <b>Change:</b> {change_pct:+.2f}%
📊 <b>Volume:</b> {volume_formatted}

💪 <b>Confidence:</b> {confidence*100:.1f}%
📊 <b>Threshold:</b> {confidence_threshold*100:.0f}%
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

<i>Generated by AI Trading System of DataStorm 🤖</i>
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting message: {e}")
            return f"📊 Signal: {signal.get('ticker', 'Unknown')} {signal.get('action', 'Unknown')}"
            
    async def _send_message(self, text: str) -> bool:
        """Send message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram credentials missing")
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            logger.info(f"🔍 Making request to: {url}")
            logger.info(f"🔍 Payload: {payload}")
            
            timeout = aiohttp.ClientTimeout(total=30)  # Increase timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info("🔍 Creating HTTP session...")
                async with session.post(url, json=payload) as response:
                    logger.info(f"🔍 Response status: {response.status}")
                    if response.status == 200:
                        response_text = await response.text()
                        logger.info(f"✅ Telegram success: {response_text[:100]}...")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("❌ Telegram request timeout (30s)")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
            
    async def send_startup_message(self):
        """Send startup notification"""
        message = f"""
🚀 <b>TRADING BOT STARTED</b>

✅ Signal monitoring active
📊 Min confidence: {self.min_confidence*100:.0f}%
⏰ Started at: {datetime.now().strftime('%H:%M:%S')}

<i>Ready to send trading signals!</i>
        """.strip()
        
        await self._send_message(message)
        
    async def send_daily_summary(self):
        """Send daily summary"""
        summary = f"""
📊 <b>DAILY SUMMARY</b>

📈 Alerts sent today: {self.daily_alert_count}
⏰ Report time: {datetime.now().strftime('%H:%M')}

<i>Have a great trading day! 🚀</i>
        """.strip()
        
        await self._send_message(summary)
        
    async def send_test_message(self) -> bool:
        """Send test message"""
        test_message = f"""
🧪 <b>TEST MESSAGE</b>

✅ Telegram bot working correctly!
🕐 Time: {datetime.now().strftime('%H:%M:%S')}
        """.strip()
        
        return await self._send_message(test_message)
        
    def get_stats(self) -> Dict:
        """Get bot statistics"""
        return {
            "bot_configured": bool(self.bot_token and self.chat_id),
            "min_confidence": self.min_confidence,
            "daily_alerts_sent": self.daily_alert_count,
            "max_daily_alerts": self.max_daily_alerts,
            "rate_limited_tickers": len(self.last_alert_times),
            "signal_generator_ready": self.signal_generator is not None
        }


# Example usage
async def main():
    """Example usage of Telegram Signal Bot"""
    # Initialize with your credentials
    bot = TelegramSignalBot(
        bot_token="YOUR_BOT_TOKEN",
        chat_id="YOUR_CHAT_ID",
        min_confidence=0.65
    )
    
    # Initialize signal generator
    bot.initialize_signal_generator(['CTG', 'MBB', 'ACB', 'QNS', 'MSH'])
    
    # Start monitoring
    try:
        await bot.start_signal_monitoring()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        bot.stop_signal_monitoring()


if __name__ == "__main__":
    asyncio.run(main()) 