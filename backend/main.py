from datetime import datetime
import time
import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

# Load .env file - try multiple locations
env_paths = [
    Path(__file__).parent / ".env",  # backend/.env
    Path(__file__).parent.parent / ".env",  # project root/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Trading Dashboard API", version="0.1.0")

# CORS - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check first
@app.get("/api/health")
async def health_check():
    return {"ok": True, "status": "running"}

@app.get("/")
async def root():
    return {"message": "AI Trading Dashboard API", "status": "ok"}

ROUTERS_LOADED = False
IMPORT_ERROR = None

# Try to import routers with error handling
try:
    from models.responses import HealthResponse, RunAllResponse
    from routers import (
        nasdaq,
        xauusd,
        pattern_engine,
        claude_patterns,
        claude_sentiment,
        order_blocks,
        rtyhiim,
        news,
        ta,
        data,
        prediction,
        ai_analysis,
        learning,
        fvg,
    )
    from services.data_fetcher import fetch_latest_price
    from services.ml_service import run_nasdaq_signal, run_xauusd_signal
    from services.pattern_engine_runner import run_pattern_engine
    from services.pattern_analyzer import run_claude_pattern_analysis
    from services.sentiment_analyzer import run_claude_sentiment
    from services.rtyhiim_service import run_rtyhiim_detector
    from services.order_block_service import service as order_block_service
    from order_block_detector import OrderBlockConfig

    app.include_router(nasdaq.router)
    app.include_router(xauusd.router)
    app.include_router(pattern_engine.router)
    app.include_router(claude_patterns.router)
    app.include_router(claude_sentiment.router)
    app.include_router(order_blocks.router)
    app.include_router(rtyhiim.router)
    app.include_router(news.router)
    app.include_router(ta.router)
    app.include_router(data.router)
    app.include_router(prediction.router)
    app.include_router(ai_analysis.router)
    app.include_router(learning.router)
    app.include_router(fvg.router)
    
    ROUTERS_LOADED = True
except Exception as e:
    ROUTERS_LOADED = False
    IMPORT_ERROR = str(e)
    IMPORT_TRACEBACK = traceback.format_exc()
    print(f"ERROR loading routers: {e}", file=sys.stderr)
    print(IMPORT_TRACEBACK, file=sys.stderr)

@app.get("/api/debug")
async def debug_info():
    return {
        "routers_loaded": ROUTERS_LOADED,
        "import_error": IMPORT_ERROR if not ROUTERS_LOADED else None,
        "env_vars": {
            "EODHD_API_KEY": "set" if os.getenv("EODHD_API_KEY") else "not set",
            "ANTHROPIC_API_KEY": "set" if os.getenv("ANTHROPIC_API_KEY") else "not set",
            "SUPABASE_URL": "set" if os.getenv("SUPABASE_URL") else "not set",
            "SUPABASE_KEY": "set" if os.getenv("SUPABASE_KEY") else "not set",
            "SUPABASE_ANON_KEY": "set" if os.getenv("SUPABASE_ANON_KEY") else "not set",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
