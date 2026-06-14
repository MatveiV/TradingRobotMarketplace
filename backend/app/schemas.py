from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class StrategyBase(BaseModel):
    name: str
    description: str
    subscription_type: str
    price: float
    commission_percent: float = 0.0
    risk_level: str = "medium"
    platform_type: str

class StrategyCreate(StrategyBase):
    money_manager_name: Optional[str] = None
    # MT4 fields
    mt4_login: Optional[str] = None
    mt4_password: Optional[str] = None
    mt4_server: Optional[str] = None
    # MT5 fields
    mt5_login: Optional[str] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    execution_type: Optional[str] = None

class StrategyResponse(StrategyBase):
    id: int
    logo_path: Optional[str]
    status: str
    money_manager_name: Optional[str]
    investors_count: int = 0
    aum: float = 0.0
    performance_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MarketplaceStrategy(BaseModel):
    id: int
    name: str
    profit_percent: float
    risk_level: str
    commission_percent: float
    platform: str
    investors_count: int
    aum: float
    mm_name: Optional[str]
    logo_path: Optional[str]

class PerformanceResponse(BaseModel):
    total_profit: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    trades: List[Dict[str, Any]]

class StatusResponse(BaseModel):
    strategy_id: int
    status: str
    is_running: bool
    last_error: Optional[str] = None

class InvestorConnectRequest(BaseModel):
    strategy_id: int
    investor_name: Optional[str] = None
    investment_amount: float = 0.0

class InvestorConnectionResponse(BaseModel):
    connection_id: int
    strategy_id: int
    status: str
    message: str

class ModerationAction(BaseModel):
    reason: Optional[str] = None
