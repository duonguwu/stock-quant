"""
Application configuration settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "Real-time Trading Signals Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # FiinQuantX credentials
    fiin_username: str = "DSTC_19@fiinquant.vn"
    fiin_password: str = "Fiinquant0606"
    
    # Trading configuration
    default_tickers: List[str] = ["CTG", "MBB", "ACB", "QNS", "MSH"]

    # Strategy configuration


    BASE_DIR: ClassVar[Path] = Path(__file__).resolve().parent.parent
    strategy_config_path: Path = BASE_DIR / "config" / "strategies.yaml"

    model_path_15m: str = "models/model15/xgboost_model.pkl"
    scaler_path_15m: str = "models/model15/feature_scaler.pkl"
    
    # Data settings
    lookback_bars: int = 504  # For feature engineering
    update_interval_seconds: int = 15  # Real-time update frequency
    
    # Database settings  
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "trading_signals"
    mongodb_username: str = "admin"
    mongodb_password: str = "password123"
    redis_url: str = "redis://localhost:6379"
    
    # Telegram settings
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_thread_id: Optional[str] = None
    
    # WebSocket settings
    max_connections: int = 100
    heartbeat_interval: int = 30
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/dashboard.log"
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl_seconds: int = 60
    max_signal_history: int = 10000
    
    class Config:
        env_file = ".env"
        env_prefix = "TRADING_"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings() 