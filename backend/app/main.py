from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.api import strategies
from app.config import config

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