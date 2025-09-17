"""
MongoDB database service for trading signals and portfolio data
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class MongoDBService:
    """Async MongoDB service for trading application"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.settings = get_settings()

    async def connect(self):
        """Connect to MongoDB"""
        try:
            # Check if authentication is needed
            if self.settings.mongodb_username and self.settings.mongodb_password:
                auth_url = f"mongodb://{self.settings.mongodb_username}:{self.settings.mongodb_password}@localhost:27017"
                self.client = AsyncIOMotorClient(auth_url)
            else:
                # Try without authentication first
                self.client = AsyncIOMotorClient(self.settings.mongodb_url)

            self.db = self.client[self.settings.mongodb_database]

            # Test connection
            try:
                await self.db.command("ping")
                logger.info("✅ Connected to MongoDB")
            except Exception as auth_error:
                if "authentication" in str(auth_error).lower():
                    logger.warning(
                        "⚠️ MongoDB requires authentication, using no-auth mode for development")
                    # For development, use MongoDB without authentication
                    self.client = AsyncIOMotorClient(
                        "mongodb://localhost:27017/?authSource=admin")
                    self.db = self.client[self.settings.mongodb_database]
                    await self.db.command("ping")
                    logger.info("✅ Connected to MongoDB (no-auth mode)")
                else:
                    raise auth_error

            # Create indexes for better performance
            await self.create_indexes()

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 Disconnected from MongoDB")

    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Signals collection indexes
            await self.db.signals.create_index([
                ("timestamp", -1), ("ticker", 1), ("strategy", 1)
            ])
            await self.db.signals.create_index([("timestamp", -1)])
            await self.db.signals.create_index([("ticker", 1)])

            # Portfolio collection indexes
            await self.db.portfolio_snapshots.create_index([
                ("timestamp", -1), ("account_id", 1)
            ])

            # Market data indexes
            await self.db.market_data.create_index([
                ("timestamp", -1), ("ticker", 1)
            ])

            logger.info("✅ Database indexes created")

        except Exception as e:
            logger.warning(f"⚠️ Failed to create indexes: {e}")

    # ========== SIGNALS OPERATIONS ==========

    async def save_signal(self, signal_data: Dict[str, Any]) -> str:
        """Save trading signal to database"""
        try:
            signal_data["created_at"] = datetime.utcnow()
            signal_data["_id"] = f"{signal_data['ticker']}_{signal_data['timestamp']}_{signal_data['strategy']}"

            result = await self.db.signals.insert_one(signal_data)
            logger.debug(
                f"💾 Signal saved: {signal_data['ticker']} {signal_data['action']}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"❌ Failed to save signal: {e}")
            return None

    async def get_recent_signals(
            self,
            limit: int = 50,
            strategy: str = None) -> List[Dict]:
        """Get recent trading signals"""
        try:
            query = {}
            if strategy:
                query["strategy"] = strategy

            cursor = self.db.signals.find(query).sort(
                "timestamp", -1).limit(limit)
            signals = await cursor.to_list(length=limit)

            return signals

        except Exception as e:
            logger.error(f"❌ Failed to get recent signals: {e}")
            return []

    async def get_signals_by_timeframe(self, hours: int = 24) -> List[Dict]:
        """Get signals within specified timeframe"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            query = {"timestamp": {"$gte": start_time}}
            cursor = self.db.signals.find(query).sort("timestamp", -1)
            signals = await cursor.to_list(length=None)

            return signals

        except Exception as e:
            logger.error(f"❌ Failed to get signals by timeframe: {e}")
            return []

    async def get_signal_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get signal statistics for dashboard"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": None,
                        "total_signals": {"$sum": 1},
                        "buy_signals": {
                            "$sum": {"$cond": [{"$eq": ["$action", "BUY"]}, 1, 0]}
                        },
                        "sell_signals": {
                            "$sum": {"$cond": [{"$eq": ["$action", "SELL"]}, 1, 0]}
                        },
                        "avg_confidence": {"$avg": "$confidence"},
                        "strategies": {"$addToSet": "$strategy"}
                    }
                }
            ]

            result = await self.db.signals.aggregate(pipeline).to_list(length=1)

            if result:
                stats = result[0]
                stats.pop("_id", None)
                return stats
            else:
                return {
                    "total_signals": 0,
                    "buy_signals": 0,
                    "sell_signals": 0,
                    "avg_confidence": 0,
                    "strategies": []
                }

        except Exception as e:
            logger.error(f"❌ Failed to get signal stats: {e}")
            return {}

    # ========== PORTFOLIO OPERATIONS ==========

    async def save_portfolio_snapshot(
            self, account_id: str, portfolio_data: Dict[str, Any]) -> str:
        """Save portfolio snapshot (for multiple accounts demo)"""
        try:
            snapshot = {
                "account_id": account_id,
                "timestamp": datetime.utcnow(),
                "portfolio_value": portfolio_data.get("total_value", 0),
                "cash": portfolio_data.get("cash", 0),
                "positions": portfolio_data.get("positions", []),
                "daily_pnl": portfolio_data.get("daily_pnl", 0),
                "total_pnl": portfolio_data.get("total_pnl", 0),
                "drawdown": portfolio_data.get("drawdown", 0),
                "sharpe_ratio": portfolio_data.get("sharpe_ratio", 0),
                "win_rate": portfolio_data.get("win_rate", 0),
                "created_at": datetime.utcnow()
            }

            result = await self.db.portfolio_snapshots.insert_one(snapshot)
            logger.debug(f"💾 Portfolio snapshot saved for {account_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"❌ Failed to save portfolio snapshot: {e}")
            return None

    async def get_portfolio_summary(
            self, account_id: str = "demo") -> Dict[str, Any]:
        """Get latest portfolio summary for account"""
        try:
            latest = await self.db.portfolio_snapshots.find_one(
                {"account_id": account_id},
                sort=[("timestamp", -1)]
            )

            if latest:
                return {
                    "account_id": latest["account_id"],
                    "total_pnl": latest.get("total_pnl", 0),
                    "daily_pnl": latest.get("daily_pnl", 0),
                    "portfolio_value": latest.get("portfolio_value", 1000000000),
                    "cash": latest.get("cash", 200000000),
                    "max_drawdown": latest.get("drawdown", 0),
                    "sharpe_ratio": latest.get("sharpe_ratio", 0),
                    "win_rate": latest.get("win_rate", 0),
                    "active_positions": len(latest.get("positions", [])),
                    "exposure": latest.get("exposure", 0.75),
                    "last_updated": latest["timestamp"]
                }
            else:
                # Return demo data for initial state
                return {
                    "account_id": account_id,
                    "total_pnl": 5.67,
                    "daily_pnl": 1.23,
                    "portfolio_value": 1000000000,
                    "cash": 200000000,
                    "max_drawdown": -3.45,
                    "sharpe_ratio": 2.45,
                    "win_rate": 68.2,
                    "active_positions": 8,
                    "exposure": 0.75,
                    "last_updated": datetime.utcnow()
                }

        except Exception as e:
            logger.error(f"❌ Failed to get portfolio summary: {e}")
            return {}

    async def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all portfolio accounts for multi-account demo"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$account_id",
                        "latest_snapshot": {"$last": "$$ROOT"}
                    }
                },
                {
                    "$replaceRoot": {"newRoot": "$latest_snapshot"}
                },
                {
                    "$sort": {"total_pnl": -1}
                }
            ]

            results = await self.db.portfolio_snapshots.aggregate(pipeline).to_list(length=None)
            return results

        except Exception as e:
            logger.error(f"❌ Failed to get all accounts: {e}")
            return []

    # ========== MARKET DATA OPERATIONS ==========

    async def save_market_data(self, market_data: Dict[str, Any]):
        """Save market data snapshot"""
        try:
            market_data["timestamp"] = datetime.utcnow()
            await self.db.market_data.insert_one(market_data)
            logger.debug("💾 Market data saved")

        except Exception as e:
            logger.error(f"❌ Failed to save market data: {e}")

    async def get_latest_market_data(self) -> Dict[str, Any]:
        """Get latest market data"""
        try:
            latest = await self.db.market_data.find_one(
                {},
                sort=[("timestamp", -1)]
            )

            if latest:
                return latest
            else:
                # Return demo data
                return {
                    "vnindex": {"value": "1,285.4", "change": 0.85},
                    "vn30": {"value": "1,321.2", "change": 1.2},
                    "active_tickers": 9,
                    "session": "Morning",
                    "last_update": "2s ago",
                    "timestamp": datetime.utcnow()
                }

        except Exception as e:
            logger.error(f"❌ Failed to get market data: {e}")
            return {}

    # ========== CLEANUP OPERATIONS ==========

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data to save space"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Clean old signals
            result1 = await self.db.signals.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )

            # Clean old portfolio snapshots (keep some history)
            result2 = await self.db.portfolio_snapshots.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )

            # Clean old market data
            result3 = await self.db.market_data.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )

            logger.info(
                f"🧹 Cleaned up old data: {result1.deleted_count + result2.deleted_count + result3.deleted_count} records")

        except Exception as e:
            logger.error(f"❌ Failed to cleanup old data: {e}")


# Global MongoDB service instance
mongodb_service = MongoDBService()


async def get_mongodb() -> MongoDBService:
    """Get MongoDB service instance"""
    return mongodb_service
