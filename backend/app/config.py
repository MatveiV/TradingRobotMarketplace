import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core database and file storage
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_robots.db")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    
    # MT4 terminal configuration
    MT4_TERMINAL_PATH = os.getenv("MT4_TERMINAL_PATH", "")
    MT4_IPC_HOST = os.getenv("MT4_IPC_HOST", "127.0.0.1")
    MT4_IPC_PORT = int(os.getenv("MT4_IPC_PORT", "9000"))
    
    # Message queue for distributed deployment
    MESSAGE_QUEUE_URL = os.getenv("MESSAGE_QUEUE_URL", "redis://localhost:6379/0")
    
    # Mode settings
    DOCKER_MODE = os.getenv("DOCKER_MODE", "false").lower() == "true"
    USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
    
    # Risk management and rate limits
    RISK_LIMITS = {
        "max_order_value": float(os.getenv("MAX_ORDER_VALUE", "100000")),
        "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "5000")),
        "max_positions": int(os.getenv("MAX_POSITIONS", "10")),
        "max_account_risk": float(os.getenv("MAX_ACCOUNT_RISK", "0.02")),
        "min_account_balance": float(os.getenv("MIN_ACCOUNT_BALANCE", "1000"))
    }
    
    # API rate limits
    RATE_LIMITS = {
        "general": {"requests": 100, "window": 60},
        "create_order": {"requests": 20, "window": 60},
        "cancel_order": {"requests": 20, "window": 60},
        "get_positions": {"requests": 60, "window": 60},
        "get_trade_history": {"requests": 120, "window": 60}
    }
    
    # Trading modes
    TRADING_MODES = ["real", "demo", "sandbox"]
    
    # Webhook configuration
    WEBHOOK_CONFIG = {
        "enabled": os.getenv("WEBHOOKS_ENABLED", "true").lower() == "true",
        "retry_attempts": int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3")),
        "retry_delay": float(os.getenv("WEBHOOK_RETRY_DELAY", "1.0"))
    }
    
    # Monitoring configuration
    MONITORING_CONFIG = {
        "check_interval": float(os.getenv("MONITORING_CHECK_INTERVAL", "1.0")),
        "heartbeat_interval": float(os.getenv("MONITORING_HEARTBEAT_INTERVAL", "30.0")),
        "max_history_points": int(os.getenv("MONITORING_MAX_HISTORY", "1000"))
    }
    
    # Security
    HMAC_SECRET = os.getenv("HMAC_SECRET", "default-secret-key-change-in-production")
    JWT_SECRET = os.getenv("JWT_SECRET", "default-jwt-secret-change-in-production")
    
    # Database
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

# Create config instance
config = Config()