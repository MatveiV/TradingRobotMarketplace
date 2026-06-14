from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models import Strategy, RobotStatus, InvestorConnection
from app.schemas import (
    StrategyCreate, StrategyResponse, PerformanceResponse, StatusResponse,
    InvestorConnectRequest, InvestorConnectionResponse, ModerationAction
)
from app.utils.file_storage import file_storage
from app.robot_manager.manager import robot_manager

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.post("/", response_model=StrategyResponse, status_code=201)
async def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db)
):
    strategy = Strategy(
        name=strategy_data.name,
        description=strategy_data.description,
        subscription_type=strategy_data.subscription_type,
        price=strategy_data.price,
        commission_percent=strategy_data.commission_percent,
        risk_level=strategy_data.risk_level,
        platform_type=strategy_data.platform_type,
        money_manager_name=strategy_data.money_manager_name,
        mt4_login=strategy_data.mt4_login,
        mt4_password=strategy_data.mt4_password,
        mt4_server=strategy_data.mt4_server,
        mt5_login=strategy_data.mt5_login,
        mt5_password=strategy_data.mt5_password,
        mt5_server=strategy_data.mt5_server,
        execution_type=strategy_data.execution_type,
        status=RobotStatus.DRAFT
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    platform: Optional[str] = None,
    risk: Optional[str] = None,
    sort_by: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Strategy)
    if platform:
        query = query.filter(Strategy.platform_type == platform)
    if risk:
        query = query.filter(Strategy.risk_level == risk)
    if sort_by == "profit":
        query = query.order_by(Strategy.aum.desc())
    elif sort_by == "risk":
        query = query.order_by(Strategy.risk_level)
    else:
        query = query.order_by(Strategy.created_at.desc())
    return query.all()


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
@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


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


@router.get("/{strategy_id}/performance", response_model=PerformanceResponse)
async def get_performance(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    performance = await robot_manager.get_performance(strategy_id)
    strategy.performance_data = performance
    db.commit()
    return PerformanceResponse(**performance)


@router.get("/{strategy_id}/status", response_model=StatusResponse)
async def get_status(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    is_running = strategy_id in robot_manager.running_robots
    return StatusResponse(strategy_id=strategy_id, status=strategy.status, is_running=is_running, last_error=None)
