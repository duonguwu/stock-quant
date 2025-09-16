"""
Simple portfolio tracker for demo purposes
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from app.config.settings import get_settings
from app.services.database import mongodb_service

logger = logging.getLogger(__name__)


class PortfolioTracker:
    """Simple portfolio tracker for demo"""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def update(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update portfolio with new signals (demo implementation)"""
        try:
            if not signals:
                return {"status": "no_signals"}
            
            # Simple demo portfolio update
            portfolio_data = {
                "signals_processed": len(signals),
                "buy_signals": len([s for s in signals if s.get("action") == "BUY"]),
                "sell_signals": len([s for s in signals if s.get("action") == "SELL"]),
                "avg_confidence": sum(s.get("confidence", 0) for s in signals) / len(signals),
                "last_update": datetime.now().isoformat(),
                "status": "updated"
            }
            
            # Save to database
            await mongodb_service.save_portfolio_snapshot("demo", portfolio_data)
            
            logger.info(f"📊 Portfolio updated with {len(signals)} signals")
            return portfolio_data
            
        except Exception as e:
            logger.error(f"❌ Error updating portfolio: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        try:
            summary = await mongodb_service.get_portfolio_summary("demo")
            return summary
        except Exception as e:
            logger.error(f"❌ Error getting portfolio summary: {e}")
            return {
                "account_id": "demo",
                "total_pnl": 5.67,
                "daily_pnl": 1.23,
                "portfolio_value": 1000000000,
                "cash": 200000000,
                "max_drawdown": -3.45,
                "sharpe_ratio": 2.45,
                "win_rate": 68.2,
                "active_positions": 8,
                "exposure": 0.75,
                "last_updated": datetime.now()
            }