from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ── New OpenAPI schemas (frontend v2) ────────────────────────────────

class StrategyInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    minInvest: float = Field(default=0, ge=0)
    withdrawalPolicy: str = "anytime"
    passwordProtected: Optional[bool] = None
    password: Optional[str] = None
    availability: str = "all"
    userName: Optional[str] = None
    userAccount: Optional[str] = None
    tradesHistoryFrom: Optional[str] = None
    description: Optional[str] = None
    performanceFeeEnabled: bool = True
    performanceFee: float = Field(default=30, ge=0, le=100)
    performanceAgentFee: float = Field(default=0, ge=0, le=100)
    entryFeeEnabled: bool = False
    entryFee: float = Field(default=0, ge=0, le=100)
    entryAgentFee: float = Field(default=0, ge=0, le=100)
    subscriptionFeeEnabled: bool = False
    subscriptionFeeType: str = "monthly"
    subscriptionFee: float = Field(default=0, ge=0)
    subscriptionAgentFee: float = Field(default=0, ge=0, le=100)

class StrategyListItem(BaseModel):
    id: int
    name: str
    logoUrl: Optional[str] = None
    growthPercent: float
    minInvest: float
    investors: int
    totalFunds: float
    days: int
    performanceFee: float
    chartPoints: Optional[List[float]] = None

    class Config:
        from_attributes = True

class StrategyDetail(BaseModel):
    id: int
    name: str
    logoUrl: Optional[str] = None
    growthPercent: float
    minInvest: float
    investors: int
    totalFunds: float
    days: int
    drawdown: float = 0
    withdrawalPolicy: str = "anytime"
    passwordProtected: bool = False
    availability: str = "all"
    userName: Optional[str] = None
    userAccount: Optional[str] = None
    tradesHistoryFrom: Optional[str] = None
    description: Optional[str] = None
    performanceFeeEnabled: bool = True
    performanceFee: float = 30
    performanceAgentFee: float = 0
    entryFeeEnabled: bool = False
    entryFee: float = 0
    entryAgentFee: float = 0
    subscriptionFeeEnabled: bool = False
    subscriptionFeeType: str = "monthly"
    subscriptionFee: float = 0
    subscriptionAgentFee: float = 0

    class Config:
        from_attributes = True

class PerformancePoint(BaseModel):
    date: str
    value: float

class Trade(BaseModel):
    id: int
    instrument: str
    openTime: str
    openPrice: float
    closeTime: str
    closePrice: float
    tradeType: str
    volume: float
    profit: float

class StrategyListResponse(BaseModel):
    strategies: List[StrategyListItem]
    total: int
    page: int
    pageSize: int
    totalPages: int

class TradeHistory(BaseModel):
    trades: List[Trade]
    total: int
    page: int
    pageSize: int
    totalPages: int

class MarketStats(BaseModel):
    totalStrategies: int
    totalInvestors: int
    totalFunds: float
    topGrowth: float

# ── Legacy schemas (existing frontend) ───────────────────────────────

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
    mt4_login: Optional[str] = None
    mt4_password: Optional[str] = None
    mt4_server: Optional[str] = None
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
