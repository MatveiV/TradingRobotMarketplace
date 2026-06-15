from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.database import engine, Base, get_db
from app.api import strategies
from app.config import config
from app.models import Strategy, RobotStatus
from app.schemas import MarketStats

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trading Robot Marketplace API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(strategies.router)

@app.get("/")
async def root():
    return {"message": "Trading Robot Marketplace API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/api/stats", response_model=MarketStats)
async def market_stats(db: Session = Depends(get_db)):
    strategies = db.query(Strategy).filter(Strategy.status == RobotStatus.PUBLISHED).all()
    total_funds = sum(s.aum or 0 for s in strategies)
    top_growth = 0
    for s in strategies:
        perf = s.performance_data or {}
        g = perf.get("growth_percent", 0) or 0
        if g > top_growth:
            top_growth = g
    return MarketStats(
        totalStrategies=len(strategies),
        totalInvestors=sum(s.investors_count or 0 for s in strategies),
        totalFunds=total_funds,
        topGrowth=top_growth,
    )