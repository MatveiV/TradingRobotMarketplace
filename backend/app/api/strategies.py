from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import random
import os
import shutil
import subprocess
import base64
from pathlib import Path
from app.database import get_db
from app.models import Strategy, RobotStatus, InvestorConnection
from app.schemas import (
    StrategyCreate, StrategyResponse, PerformanceResponse, StatusResponse,
    InvestorConnectRequest, InvestorConnectionResponse, ModerationAction,
    StrategyListItem, StrategyDetail, StrategyInput, PerformancePoint,
    Trade, TradeHistory, MarketStats, MarketplaceStrategy, StrategyListResponse
)
from app.utils.file_storage import file_storage
from app.robot_manager.manager import robot_manager
from app.config import config

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

INSTRUMENTS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD"]

def _generate_mock_performance(days: int, growth_percent: float):
    """Generate realistic performance data with chart points and trades."""
    base_date = datetime.utcnow() - timedelta(days=days)
    points = []
    val = 100.0
    daily_growth = growth_percent / days / 100
    for d in range(days):
        noise = random.uniform(-0.005, 0.008)
        val = val * (1 + daily_growth + noise)
        date_str = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        points.append({"date": date_str, "value": round(val - 100, 2)})

    trades = []
    total_profit = 0
    wins = 0
    for i in range(random.randint(15, 40)):
        is_buy = random.choice([True, False])
        entry = round(random.uniform(1.0000, 1.2000), 5)
        spread = random.uniform(0.0010, 0.0100)
        exit_val = entry + spread if is_buy else entry - spread
        profit_pct = random.uniform(-3, 6)
        profit = round(profit_pct * 10, 2)
        if profit > 0:
            wins += 1
        total_profit += profit
        trade_date = base_date + timedelta(days=random.randint(1, days - 1), hours=random.randint(0, 23))
        trades.append({
            "instrument": random.choice(INSTRUMENTS),
            "open_time": trade_date.strftime("%Y-%m-%d %H:%M:%S"),
            "open_price": entry,
            "close_time": (trade_date + timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M:%S"),
            "close_price": entry + (random.uniform(0.001, 0.05) * (1 if is_buy else -1)),
            "type": "buy" if is_buy else "sell",
            "volume": round(random.uniform(0.01, 2.0), 2),
            "profit": profit,
        })

    win_rate = round(wins / len(trades) * 100, 1) if trades else 0
    drawdown = round(abs(min(p["value"] for p in points)), 1) if points else 0

    return {
        "growth_percent": growth_percent,
        "days": days,
        "drawdown": drawdown,
        "chart_points": points,
        "trades": trades,
        "total_profit": round(total_profit, 2),
        "total_trades": len(trades),
        "winning_trades": wins,
        "losing_trades": len(trades) - wins,
        "win_rate": win_rate,
        "withdrawal_policy": random.choice(["anytime", "weekly", "monthly"]),
        "subscription_fee": random.choice([0, 0, 0, 5, 10, 20]),
        "entry_fee": random.choice([0, 0, 1, 2, 5]),
        "agent_reward_performance": round(random.uniform(5, 30), 1),
        "agent_reward_subscription": round(random.uniform(0, 10), 1),
        "agent_reward_entry": round(random.uniform(0, 5), 1),
    }


@router.post("/", response_model=StrategyListItem, status_code=201)
async def create_strategy(
    strategy_data: StrategyInput,
    db: Session = Depends(get_db)
):
    days = random.randint(30, 365)
    growth = round(random.uniform(5, 45), 1)
    settings = {
        "withdrawal_policy": strategy_data.withdrawalPolicy,
        "password_protected": strategy_data.passwordProtected or False,
        "availability": strategy_data.availability,
        "user_name": strategy_data.userName,
        "user_account": strategy_data.userAccount,
        "trades_history_from": strategy_data.tradesHistoryFrom,
        "performance_fee_enabled": strategy_data.performanceFeeEnabled,
        "performance_fee": strategy_data.performanceFee,
        "performance_agent_fee": strategy_data.performanceAgentFee,
        "entry_fee_enabled": strategy_data.entryFeeEnabled,
        "entry_fee": strategy_data.entryFee,
        "entry_agent_fee": strategy_data.entryAgentFee,
        "subscription_fee_enabled": strategy_data.subscriptionFeeEnabled,
        "subscription_fee_type": strategy_data.subscriptionFeeType,
        "subscription_fee": strategy_data.subscriptionFee,
        "subscription_agent_fee": strategy_data.subscriptionAgentFee,
    }
    perf = _generate_mock_performance(days, growth)
    perf["settings"] = settings
    strategy = Strategy(
        name=strategy_data.name,
        description=strategy_data.description or "",
        subscription_type="free",
        price=strategy_data.minInvest,
        commission_percent=strategy_data.performanceFee,
        risk_level=random.choice(["low", "medium", "high"]),
        platform_type=random.choice(["mt4", "mt5"]),
        money_manager_name="Money Manager",
        status=RobotStatus.PUBLISHED,
        investors_count=0,
        aum=0.0,
        performance_data=perf,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return _strategy_to_list_item(strategy)


@router.post("/seed", response_model=List[StrategyListItem], status_code=201)
async def seed_strategies(db: Session = Depends(get_db)):
    seeds = [
        {"name": "EURUSD Grid Master", "platform": "mt4", "risk": "medium", "investors": 34, "aum": 245000},
        {"name": "GBPJPY Breakout Hunter", "platform": "mt5", "risk": "high", "investors": 18, "aum": 89000},
        {"name": "Gold Rush XAUUSD", "platform": "mt4", "risk": "high", "investors": 52, "aum": 412000},
        {"name": "EURUSD Steady Scalper", "platform": "mt5", "risk": "low", "investors": 87, "aum": 678000},
        {"name": "AUDUSD Trend Follower", "platform": "mt4", "risk": "medium", "investors": 41, "aum": 195000},
        {"name": "Crypto Basket Trader", "platform": "mt5", "risk": "high", "investors": 23, "aum": 156000},
    ]
    created = []
    for s in seeds:
        days = random.randint(60, 500)
        growth = round(random.uniform(8, 65), 1)
        perf = _generate_mock_performance(days, growth)
        perf["settings"] = {
            "withdrawal_policy": random.choice(["anytime", "weekly", "monthly"]),
            "password_protected": False,
            "availability": "all",
            "performance_fee_enabled": True,
            "performance_fee": round(random.uniform(15, 35), 1),
            "performance_agent_fee": round(random.uniform(0, 20), 1),
            "entry_fee_enabled": True,
            "entry_fee": round(random.uniform(0, 5), 1),
            "entry_agent_fee": round(random.uniform(0, 10), 1),
            "subscription_fee_enabled": True,
            "subscription_fee_type": random.choice(["daily", "weekly", "monthly", "annual"]),
            "subscription_fee": round(random.uniform(0, 100), 1),
            "subscription_agent_fee": round(random.uniform(0, 15), 1),
        }
        strategy = Strategy(
            name=s["name"],
            description=f"Professional {s['name']} trading strategy for MetaTrader {s['platform'][-1]}. Automated copy trading with risk management.",
            subscription_type="free",
            price=random.choice([0, 0, 50, 100, 200, 500]),
            commission_percent=round(random.uniform(10, 35), 1),
            risk_level=s["risk"],
            platform_type=s["platform"],
            money_manager_name=random.choice(["Alex Smith", "Maria Garcia", "John Chen", "Elena Petrova", "David Kim"]),
            status=RobotStatus.PUBLISHED,
            investors_count=s["investors"],
            aum=s["aum"],
            performance_data=perf,
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        created.append(_strategy_to_list_item(strategy))
    return created


def _strategy_to_list_item(s: Strategy) -> StrategyListItem:
    perf = s.performance_data or {}
    return StrategyListItem(
        id=s.id,
        name=s.name,
        logoUrl=s.logo_path,
        growthPercent=perf.get("growth_percent", 0),
        minInvest=s.price or 0,
        investors=s.investors_count or 0,
        totalFunds=s.aum or 0,
        days=perf.get("days", 0),
        performanceFee=s.commission_percent or 0,
        chartPoints=[p["value"] for p in perf.get("chart_points", [])] if perf.get("chart_points") else None,
    )


def _strategy_to_detail(s: Strategy) -> StrategyDetail:
    perf = s.performance_data or {}
    settings = perf.get("settings", {}) if isinstance(perf, dict) else {}
    return StrategyDetail(
        id=s.id,
        name=s.name,
        logoUrl=s.logo_path,
        growthPercent=perf.get("growth_percent", 0),
        minInvest=s.price or 0,
        investors=s.investors_count or 0,
        totalFunds=s.aum or 0,
        days=perf.get("days", 0),
        drawdown=perf.get("drawdown", 0),
        withdrawalPolicy=settings.get("withdrawal_policy", "anytime"),
        passwordProtected=settings.get("password_protected", False),
        availability=settings.get("availability", "all"),
        userName=settings.get("user_name"),
        userAccount=settings.get("user_account"),
        tradesHistoryFrom=settings.get("trades_history_from"),
        description=s.description,
        performanceFeeEnabled=settings.get("performance_fee_enabled", True),
        performanceFee=settings.get("performance_fee", 30),
        performanceAgentFee=settings.get("performance_agent_fee", 0),
        entryFeeEnabled=settings.get("entry_fee_enabled", False),
        entryFee=settings.get("entry_fee", 0),
        entryAgentFee=settings.get("entry_agent_fee", 0),
        subscriptionFeeEnabled=settings.get("subscription_fee_enabled", False),
        subscriptionFeeType=settings.get("subscription_fee_type", "monthly"),
        subscriptionFee=settings.get("subscription_fee", 0),
        subscriptionAgentFee=settings.get("subscription_agent_fee", 0),
    )


@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    search: Optional[str] = Query(None),
    sortBy: Optional[str] = Query(None),
    order: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db)
):
    query = db.query(Strategy).filter(Strategy.status == RobotStatus.PUBLISHED)
    if search:
        query = query.filter(Strategy.name.ilike(f"%{search}%"))
    if sortBy == "growthPercent":
        query = query.order_by(Strategy.aum.desc() if order != "asc" else Strategy.aum.asc())
    elif sortBy == "investors":
        query = query.order_by(Strategy.investors_count.desc() if order != "asc" else Strategy.investors_count.asc())
    else:
        query = query.order_by(Strategy.created_at.desc())
    total = query.count()
    items = [_strategy_to_list_item(s) for s in query.offset((page - 1) * page_size).limit(page_size).all()]
    return StrategyListResponse(
        strategies=items,
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/marketplace", response_model=List[dict])
async def marketplace_list(
    platform: Optional[str] = None,
    risk: Optional[str] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Strategy).filter(Strategy.status == RobotStatus.PUBLISHED)
    if platform:
        query = query.filter(Strategy.platform_type == platform)
    if risk:
        query = query.filter(Strategy.risk_level == risk)
    if sort_by == "profit":
        query = query.order_by(Strategy.aum.desc())
    elif sort_by == "risk":
        query = query.order_by(Strategy.risk_level)
    elif sort_by == "investors":
        query = query.order_by(Strategy.investors_count.desc())
    else:
        query = query.order_by(Strategy.created_at.desc())

    strategies = query.all()
    result = []
    for s in strategies:
        perf = s.performance_data or {}
        profit = abs(perf.get("total_profit", 0))
        result.append({
            "id": s.id,
            "name": s.name,
            "profit_percent": round(profit, 1),
            "risk_level": s.risk_level,
            "commission_percent": s.commission_percent,
            "platform": s.platform_type,
            "investors_count": s.investors_count,
            "aum": s.aum,
            "mm_name": s.money_manager_name or "Anonymous",
            "logo_path": s.logo_path
        })
    return result


# Investor endpoints (must be before {strategy_id} routes)
@router.post("/investor/connect", response_model=InvestorConnectionResponse)
async def investor_connect(
    request: InvestorConnectRequest,
    db: Session = Depends(get_db)
):
    strategy = db.query(Strategy).filter(Strategy.id == request.strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    connections_count = db.query(InvestorConnection).filter(
        InvestorConnection.strategy_id == request.strategy_id,
        InvestorConnection.status == "active"
    ).count()

    if connections_count >= 5:
        raise HTTPException(status_code=400, detail={
            "error": "max_connections_exceeded",
            "message": "Maximum 5 connections per Money Manager"
        })

    connection = InvestorConnection(
        strategy_id=request.strategy_id,
        investor_name=request.investor_name,
        investment_amount=request.investment_amount,
        status="active"
    )
    strategy.investors_count = connections_count + 1
    strategy.aum += request.investment_amount
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return InvestorConnectionResponse(
        connection_id=connection.id,
        strategy_id=strategy.id,
        status="active",
        message="Connected to strategy. Only new trades will be copied."
    )


@router.post("/investor/disconnect/{connection_id}")
async def investor_disconnect(
    connection_id: int,
    db: Session = Depends(get_db)
):
    connection = db.query(InvestorConnection).filter(
        InvestorConnection.id == connection_id,
        InvestorConnection.status == "active"
    ).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.status = "disconnected"
    connection.disconnected_at = datetime.utcnow()

    strategy = db.query(Strategy).filter(Strategy.id == connection.strategy_id).first()
    if strategy:
        strategy.investors_count = max(0, strategy.investors_count - 1)
        strategy.aum = max(0, strategy.aum - connection.investment_amount)

    db.commit()
    return {"status": "disconnected", "message": "Copying stopped"}


# Strategy detail routes (with {strategy_id} path parameter)
@router.get("/{strategy_id}", response_model=StrategyDetail)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return _strategy_to_detail(strategy)


@router.post("/{strategy_id}/connect")
async def connect_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.status = RobotStatus.CONNECTING
    db.commit()
    check_result = await robot_manager.check_robot_running(strategy)
    if check_result.get("robot_running"):
        return {"status": "confirmation_required", "running_robot": check_result, "message": "Another robot is running."}
    success = await robot_manager.connect_robot(strategy)
    strategy.status = RobotStatus.STOPPED if success else RobotStatus.ERROR
    db.commit()
    return {"connected": success, "message": "Connected successfully" if success else "Connection failed"}


@router.post("/{strategy_id}/start")
async def start_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    if strategy.id not in robot_manager.adapters:
        await robot_manager.connect_robot(strategy)
    success = await robot_manager.start_robot(strategy)
    strategy.status = RobotStatus.RUNNING if success else RobotStatus.ERROR
    db.commit()
    return {"status": "running" if success else "error", "started": success}


@router.post("/{strategy_id}/stop")
async def stop_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    await robot_manager.stop_robot(strategy_id)
    strategy.status = RobotStatus.STOPPED
    db.commit()
    return {"status": "stopped"}


@router.post("/{strategy_id}/replace-robot")
async def replace_robot(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    check_result = await robot_manager.check_robot_running(strategy)
    if check_result.get("robot_running"):
        return {"status": "confirmation_required", "running_robot": check_result}
    return {"status": "no_conflict", "message": "No robot is currently running."}


@router.post("/{strategy_id}/confirm-replace")
async def confirm_replace_robot(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    success = await robot_manager.replace_robot(strategy)
    if success:
        strategy.status = RobotStatus.RUNNING
        db.commit()
        return {"status": "success", "message": "Robot replaced successfully"}
    return {"status": "error", "message": "Failed to replace robot"}


# Moderation endpoints
@router.put("/{strategy_id}/submit")
async def submit_for_moderation(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.status = RobotStatus.PENDING_MODERATION
    db.commit()
    return {"status": "pending_moderation", "message": "Strategy submitted for moderation"}


@router.put("/{strategy_id}/approve")
async def approve_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.status = RobotStatus.PUBLISHED
    db.commit()
    return {"status": "published", "message": "Strategy published to Marketplace"}


@router.put("/{strategy_id}/reject")
async def reject_strategy(strategy_id: int, action: ModerationAction, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.status = RobotStatus.REJECTED
    db.commit()
    return {"status": "rejected", "reason": action.reason or "No reason provided"}


@router.get("/{strategy_id}/performance", response_model=List[PerformancePoint])
async def get_performance(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    perf = strategy.performance_data or {}
    if not perf.get("chart_points"):
        days = perf.get("days", random.randint(60, 365))
        growth = perf.get("growth_percent", round(random.uniform(5, 45), 1))
        perf = _generate_mock_performance(days, growth)
        strategy.performance_data = perf
        db.commit()
    chart = perf.get("chart_points", [])
    return [PerformancePoint(date=p["date"], value=p["value"]) for p in chart]


@router.get("/{strategy_id}/trades", response_model=TradeHistory)
async def list_trades(strategy_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    perf = strategy.performance_data or {}
    if not perf.get("trades"):
        days = perf.get("days", random.randint(60, 365))
        growth = perf.get("growth_percent", round(random.uniform(5, 45), 1))
        perf = _generate_mock_performance(days, growth)
        strategy.performance_data = perf
        db.commit()
    raw_trades = perf.get("trades", [])
    total = len(raw_trades)
    start = (page - 1) * page_size
    end = start + page_size
    trades = []
    for i, t in enumerate(raw_trades[start:end]):
        trades.append(Trade(
            id=i + start + 1,
            instrument=t.get("instrument", "EURUSD"),
            openTime=t.get("open_time", ""),
            openPrice=t.get("open_price", 0),
            closeTime=t.get("close_time", ""),
            closePrice=t.get("close_price", 0),
            tradeType=t.get("type", "buy"),
            volume=t.get("volume", 0),
            profit=t.get("profit", 0),
        ))
    return TradeHistory(
        trades=trades,
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=max(1, (total + page_size - 1) // page_size) if total else 1,
    )


@router.get("/{strategy_id}/status", response_model=StatusResponse)
async def get_status(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    is_running = strategy_id in robot_manager.running_robots
    return StatusResponse(strategy_id=strategy_id, status=strategy.status, is_running=is_running, last_error=None)


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Money Manager: delete a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    db.delete(strategy)
    db.commit()
    return {"status": "deleted"}


@router.post("/{strategy_id}/connect-account")
async def connect_strategy_account(
    strategy_id: int,
    account_login: str = Form(""),
    account_password: str = Form(""),
    account_server: str = Form(""),
    mt_version: int = Form(4),
    trade_symbol: str = Form("EURUSD"),
    trade_period: str = Form("H1"),
    terminal_path: str = Form(""),
    use_uploaded: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Investor: connect a strategy to their trading account.
    Deploys the strategy's robot files to MT and launches on the specified server."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    robot_path = strategy.robot_file_path
    settings_path = strategy.settings_file_path
    ext = os.path.splitext(robot_path)[1].lower() if robot_path else ""

    if use_uploaded and robot_path and os.path.exists(robot_path):
        pass  # use uploaded files
    elif strategy.robot_file_path and os.path.exists(strategy.robot_file_path):
        robot_path = strategy.robot_file_path
        settings_path = strategy.settings_file_path
    else:
        robot_path = None
        settings_path = None

    if not robot_path or not os.path.exists(robot_path):
        raise HTTPException(status_code=400, detail="No robot file available. Upload .ex4/.ex5 first.")

    if not settings_path or not os.path.exists(settings_path):
        # Generate a minimal .set if not present
        strategy_dir = os.path.join(DEPLOY_DIR, str(strategy_id))
        os.makedirs(strategy_dir, exist_ok=True)
        settings_path = os.path.join(strategy_dir, "default.set")
        with open(settings_path, "w") as f:
            f.write(f"; Settings for {strategy.name}\n")
        strategy.settings_file_path = settings_path
        db.commit()

    # Deploy to MT
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise HTTPException(status_code=500, detail="APPDATA not found")
    base_path = Path(appdata) / "MetaQuotes" / "Terminal"
    if not base_path.exists():
        raise HTTPException(status_code=500, detail="MetaTrader not installed")

    folders = [f for f in base_path.iterdir() if f.is_dir() and len(f.name) == 32]
    if not folders:
        raise HTTPException(status_code=500, detail="No MetaTrader terminal ID found")
    terminal_id = folders[0].name
    mql_folder = "MQL4" if mt_version == 4 else "MQL5"
    mql_path = base_path / terminal_id / mql_folder

    expert_dest = mql_path / "Experts" / os.path.basename(robot_path)
    preset_dest = mql_path / "Presets" / os.path.basename(settings_path)
    shutil.copy2(robot_path, expert_dest)
    shutil.copy2(settings_path, preset_dest)

    expert_stem = os.path.splitext(os.path.basename(robot_path))[0]
    preset_name = os.path.basename(settings_path)

    ini_path = Path(os.getcwd()) / f"auto_run_config_{strategy_id}.ini"
    if mt_version == 4:
        content = f"""[Common]
Profile=Default
Login={account_login}
Password={account_password}
Server={account_server}
EnableNews=Analyse
[Charts]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""
    else:
        content = f"""[Common]
Login={account_login}
Password={account_password}
Server={account_server}
[StartUp]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""
    with open(ini_path, "w", encoding="utf-16") as f:
        f.write(content)

    terminal_found = None
    if terminal_path and os.path.exists(terminal_path):
        terminal_found = terminal_path
    else:
        candidates = [
            r"C:\Program Files (x86)\MetaTrader 4\terminal.exe",
            r"C:\Program Files\MetaTrader 4\terminal.exe",
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                terminal_found = c
                break

    if not terminal_found:
        raise HTTPException(status_code=400, detail="MetaTrader terminal not found. Specify path manually.")

    try:
        if mt_version == 4:
            cmd = [terminal_found, str(ini_path)]
        else:
            cmd = [terminal_found, f"/config:{str(ini_path)}"]
        subprocess.Popen(cmd, shell=True)
        strategy.status = RobotStatus.RUNNING
        db.commit()
        return {"status": "connected", "message": f"MetaTrader {mt_version} launched with {expert_stem}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Launch failed: {str(e)}")


@router.post("/{strategy_id}/disconnect-investor")
async def disconnect_investor(strategy_id: int, db: Session = Depends(get_db)):
    """Money Manager: disconnect an investor's running strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    try:
        await robot_manager.stop_robot(strategy_id)
    except Exception:
        pass
    strategy.status = RobotStatus.STOPPED
    db.commit()
    return {"status": "disconnected", "message": "Strategy disconnected from investor account."}


# ── MetaTrader deploy endpoints ──────────────────────────────────────

DEPLOY_DIR = os.path.join(os.getcwd(), "deploy_files")
os.makedirs(DEPLOY_DIR, exist_ok=True)


@router.post("/{strategy_id}/deploy/upload")
async def deploy_upload(
    strategy_id: int,
    file: UploadFile = File(...),
    mt_version: int = Form(4),
    account_login: str = Form(""),
    account_password: str = Form(""),
    account_server: str = Form(""),
    trade_symbol: str = Form("EURUSD"),
    trade_period: str = Form("H1"),
    terminal_path: str = Form(""),
    db: Session = Depends(get_db),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = {".ex4", ".ex5", ".set"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Invalid file type {ext}. Allowed: .ex4, .ex5, .set")

    strategy_dir = os.path.join(DEPLOY_DIR, str(strategy_id))
    os.makedirs(strategy_dir, exist_ok=True)
    file_path = os.path.join(strategy_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if ext in (".ex4", ".ex5"):
        strategy.robot_file_path = file_path
    elif ext == ".set":
        strategy.settings_file_path = file_path
    db.commit()

    return {"status": "uploaded", "filename": file.filename, "path": file_path}


@router.post("/{strategy_id}/deploy/url")
async def deploy_url(
    strategy_id: int,
    url: str = Form(...),
    filename: str = Form(...),
    mt_version: int = Form(4),
    account_login: str = Form(""),
    account_password: str = Form(""),
    account_server: str = Form(""),
    trade_symbol: str = Form("EURUSD"),
    trade_period: str = Form("H1"),
    terminal_path: str = Form(""),
    db: Session = Depends(get_db),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    import urllib.request
    try:
        strategy_dir = os.path.join(DEPLOY_DIR, str(strategy_id))
        os.makedirs(strategy_dir, exist_ok=True)
        file_path = os.path.join(strategy_dir, filename)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(file_path, "wb") as out:
            shutil.copyfileobj(response, out)

        ext = os.path.splitext(filename)[1].lower()
        if ext in (".ex4", ".ex5"):
            strategy.robot_file_path = file_path
        elif ext == ".set":
            strategy.settings_file_path = file_path
        db.commit()
        return {"status": "downloaded", "filename": filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")


@router.post("/{strategy_id}/deploy/launch")
async def deploy_launch(
    strategy_id: int,
    mt_version: int = Form(4),
    account_login: str = Form(""),
    account_password: str = Form(""),
    account_server: str = Form(""),
    trade_symbol: str = Form("EURUSD"),
    trade_period: str = Form("H1"),
    terminal_path: str = Form(""),
    db: Session = Depends(get_db),
):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    robot_path = strategy.robot_file_path
    settings_path = strategy.settings_file_path

    if not robot_path or not os.path.exists(robot_path):
        raise HTTPException(status_code=400, detail="Robot file (.ex4/.ex5) not uploaded. Upload it first.")
    if not settings_path or not os.path.exists(settings_path):
        raise HTTPException(status_code=400, detail="Settings file (.set) not uploaded. Upload it first.")

    ext = os.path.splitext(robot_path)[1].lower()
    if mt_version == 4 and ext != ".ex4":
        raise HTTPException(status_code=400, detail="File is not .ex4 for MT4")
    if mt_version == 5 and ext != ".ex5":
        raise HTTPException(status_code=400, detail="File is not .ex5 for MT5")

    # Find MT data directory
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise HTTPException(status_code=500, detail="APPDATA not found")
    base_path = Path(appdata) / "MetaQuotes" / "Terminal"
    if not base_path.exists():
        raise HTTPException(status_code=500, detail="MetaTrader not installed or never started")

    folders = [f for f in base_path.iterdir() if f.is_dir() and len(f.name) == 32]
    if not folders:
        raise HTTPException(status_code=500, detail="No MetaTrader terminal IDs found. Start MT at least once.")

    terminal_id = folders[0].name
    mql_folder = "MQL4" if mt_version == 4 else "MQL5"
    mql_path = base_path / terminal_id / mql_folder

    # Copy files to MT directories
    expert_dest = mql_path / "Experts" / os.path.basename(robot_path)
    preset_dest = mql_path / "Presets" / os.path.basename(settings_path)
    shutil.copy2(robot_path, expert_dest)
    shutil.copy2(settings_path, preset_dest)

    expert_stem = os.path.splitext(os.path.basename(robot_path))[0]
    preset_name = os.path.basename(settings_path)

    # Generate auto_run_config.ini
    ini_path = Path(os.getcwd()) / f"auto_run_config_{strategy_id}.ini"
    if mt_version == 4:
        content = f"""[Common]
Profile=Default
Login={account_login}
Password={account_password}
Server={account_server}
EnableNews=Analyse

[Charts]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""
    else:
        content = f"""[Common]
Login={account_login}
Password={account_password}
Server={account_server}

[StartUp]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""

    with open(ini_path, "w", encoding="utf-16") as f:
        f.write(content)

    # Find terminal executable
    terminal_found = None
    if terminal_path and os.path.exists(terminal_path):
        terminal_found = terminal_path
    else:
        # Search common paths
        if mt_version == 4:
            candidates = [
                r"C:\Program Files (x86)\MetaTrader 4\terminal.exe",
                r"C:\Program Files\MetaTrader 4\terminal.exe",
            ]
        else:
            candidates = [
                r"C:\Program Files\MetaTrader 5\terminal64.exe",
                r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            ]
        for c in candidates:
            if os.path.exists(c):
                terminal_found = c
                break

    if not terminal_found:
        raise HTTPException(status_code=400, detail="MetaTrader terminal executable not found. Specify path manually.")

    # Launch MetaTrader
    try:
        if mt_version == 4:
            cmd = [terminal_found, str(ini_path)]
        else:
            cmd = [terminal_found, f"/config:{str(ini_path)}"]
        subprocess.Popen(cmd, shell=True)
        strategy.status = RobotStatus.RUNNING
        db.commit()
        return {
            "status": "launched",
            "message": f"MetaTrader {mt_version} launched with {expert_stem}",
            "terminal": terminal_found,
            "config_path": str(ini_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch MetaTrader: {str(e)}")


@router.post("/{strategy_id}/deploy")
async def deploy_full(
    strategy_id: int,
    mt_version: int = Form(4),
    url: Optional[str] = Form(None),
    account_login: str = Form(""),
    account_password: str = Form(""),
    account_server: str = Form(""),
    trade_symbol: str = Form("EURUSD"),
    trade_period: str = Form("H1"),
    terminal_path: str = Form(""),
    db: Session = Depends(get_db),
):
    """Full deploy workflow: upload via URL if provided, copy to MT, launch."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    result = {"steps": [], "status": "ok"}

    # If URL provided, download
    if url and not strategy.robot_file_path:
        try:
            import urllib.request
            strategy_dir = os.path.join(DEPLOY_DIR, str(strategy_id))
            os.makedirs(strategy_dir, exist_ok=True)
            ext = ".ex4" if mt_version == 4 else ".ex5"
            robot_name = f"{strategy.name.replace(' ', '_')}{ext}"
            robot_path_dl = os.path.join(strategy_dir, robot_name)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp, open(robot_path_dl, "wb") as out:
                shutil.copyfileobj(resp, out)
            strategy.robot_file_path = robot_path_dl
            # Generate a dummy .set if not provided
            set_name = f"{strategy.name.replace(' ', '_')}.set"
            set_path_dl = os.path.join(strategy_dir, set_name)
            if not os.path.exists(set_path_dl):
                with open(set_path_dl, "w") as f:
                    f.write(f"; Auto-generated settings for {strategy.name}\n")
            strategy.settings_file_path = set_path_dl
            db.commit()
            result["steps"].append({"step": "download", "status": "ok", "robot": robot_name})
        except Exception as e:
            result["steps"].append({"step": "download", "status": "error", "detail": str(e)})
            return JSONResponse(status_code=400, content=result)

    if not strategy.robot_file_path or not os.path.exists(strategy.robot_file_path):
        result["steps"].append({"step": "download", "status": "error", "detail": "No robot file available. Upload or provide URL."})
        return JSONResponse(status_code=400, content=result)

    robot_path = strategy.robot_file_path
    settings_path = strategy.settings_file_path
    if not settings_path or not os.path.exists(settings_path):
        result["steps"].append({"step": "settings", "status": "error", "detail": "No settings file available."})
        return JSONResponse(status_code=400, content=result)

    ext = os.path.splitext(robot_path)[1].lower()

    # Find MT data directory
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise HTTPException(status_code=500, detail="APPDATA not found")
    base_path = Path(appdata) / "MetaQuotes" / "Terminal"
    if not base_path.exists():
        raise HTTPException(status_code=500, detail="MetaTrader not installed")

    folders = [f for f in base_path.iterdir() if f.is_dir() and len(f.name) == 32]
    if not folders:
        raise HTTPException(status_code=500, detail="No MetaTrader terminal IDs found")
    terminal_id = folders[0].name
    mql_folder = "MQL4" if mt_version == 4 else "MQL5"
    mql_path = base_path / terminal_id / mql_folder

    # Copy files
    expert_dest = mql_path / "Experts" / os.path.basename(robot_path)
    preset_dest = mql_path / "Presets" / os.path.basename(settings_path)
    shutil.copy2(robot_path, expert_dest)
    shutil.copy2(settings_path, preset_dest)
    result["steps"].append({"step": "copy", "status": "ok", "expert": str(expert_dest), "preset": str(preset_dest)})

    expert_stem = os.path.splitext(os.path.basename(robot_path))[0]
    preset_name = os.path.basename(settings_path)

    # Generate ini
    ini_path = Path(os.getcwd()) / f"auto_run_config_{strategy_id}.ini"
    if mt_version == 4:
        content = f"""[Common]
Profile=Default
Login={account_login}
Password={account_password}
Server={account_server}
EnableNews=Analyse

[Charts]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""
    else:
        content = f"""[Common]
Login={account_login}
Password={account_password}
Server={account_server}

[StartUp]
Symbol={trade_symbol}
Period={trade_period}
Expert={expert_stem}
ExpertParameters={preset_name}"""
    with open(ini_path, "w", encoding="utf-16") as f:
        f.write(content)
    result["steps"].append({"step": "config", "status": "ok", "path": str(ini_path)})

    # Find terminal and launch
    terminal_found = None
    if terminal_path and os.path.exists(terminal_path):
        terminal_found = terminal_path
    else:
        if mt_version == 4:
            candidates = [
                r"C:\Program Files (x86)\MetaTrader 4\terminal.exe",
                r"C:\Program Files\MetaTrader 4\terminal.exe",
            ]
        else:
            candidates = [
                r"C:\Program Files\MetaTrader 5\terminal64.exe",
                r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            ]
        for c in candidates:
            if os.path.exists(c):
                terminal_found = c
                break

    if not terminal_found:
        result["steps"].append({"step": "launch", "status": "error", "detail": "Terminal executable not found"})
        return JSONResponse(status_code=400, content=result)

    try:
        if mt_version == 4:
            cmd = [terminal_found, str(ini_path)]
        else:
            cmd = [terminal_found, f"/config:{str(ini_path)}"]
        subprocess.Popen(cmd, shell=True)
        strategy.status = RobotStatus.RUNNING
        db.commit()
        result["steps"].append({"step": "launch", "status": "ok", "terminal": terminal_found})
        result["status"] = "ok"
    except Exception as e:
        result["steps"].append({"step": "launch", "status": "error", "detail": str(e)})
        return JSONResponse(status_code=500, content=result)

    return result
