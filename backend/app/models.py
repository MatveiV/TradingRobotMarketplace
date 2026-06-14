from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, JSON, ForeignKey, Boolean
from datetime import datetime
import enum
from app.database import Base

class PlatformType(str, enum.Enum):
    MT4 = "mt4"
    MT5 = "mt5"

class RobotStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_MODERATION = "pending_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    CONNECTING = "connecting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    logo_path = Column(String(500), nullable=True)

    subscription_type = Column(String(20), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    commission_percent = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(20), nullable=False, default=RiskLevel.MEDIUM)
    money_manager_name = Column(String(200), nullable=True)

    platform_type = Column(String(20), nullable=False)

    # MT4 fields
    mt4_login = Column(String(100), nullable=True)
    mt4_password = Column(String(100), nullable=True)
    mt4_server = Column(String(200), nullable=True)
    robot_file_path = Column(String(500), nullable=True)
    settings_file_path = Column(String(500), nullable=True)

    # MT5 fields
    mt5_login = Column(String(100), nullable=True)
    mt5_password = Column(String(100), nullable=True)
    mt5_server = Column(String(200), nullable=True)
    execution_type = Column(String(20), nullable=True)

    # Marketplace stats
    investors_count = Column(Integer, default=0)
    aum = Column(Float, default=0.0)

    # Status and performance
    status = Column(String(20), default=RobotStatus.DRAFT)
    performance_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    robot_process_id = Column(String(100), nullable=True)


class InvestorConnection(Base):
    __tablename__ = "investor_connections"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    investor_name = Column(String(200), nullable=True)
    investment_amount = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime, nullable=True)
