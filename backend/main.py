from datetime import datetime
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.responses import HealthResponse, RunAllResponse
from backend.routers import (
    nasdaq,
    xauusd,
    pattern_engine,
    claude_patterns,
    claude_sentiment,
    order_blocks,
    rtyhiim,
)
from backend.services.data_fetcher import fetch_latest_price
from backend.services.ml_service import run_nasdaq_signal, run_xauusd_signal
from backend.services.pattern_engine_runner import run_pattern_engine
from backend.services.pattern_analyzer import run_claude_pattern_analysis
from backend.services.sentiment_analyzer import run_claude_sentiment
from backend.services.rtyhiim_service import run_rtyhiim_detector
from backend.services.order_block_service import service as order_block_service
from backend.order_block_detector import OrderBlockConfig

app = FastAPI(title="AI Trading Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

app.include_router(nasdaq.router)
app.include_router(xauusd.router)
app.include_router(pattern_engine.router)
app.include_router(claude_patterns.router)
app.include_router(claude_sentiment.router)
app.include_router(order_blocks.router)
app.include_router(rtyhiim.router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(ok=True)


@app.post("/api/run/all", response_model=RunAllResponse)
async def run_all() -> RunAllResponse:
    start = time.perf_counter()
    nasdaq_price = await fetch_latest_price("NAS100.INDX")
    xauusd_price = await fetch_latest_price("XAUUSD")
    nasdaq_result = run_nasdaq_signal(current_price=nasdaq_price)
    xauusd_result = run_xauusd_signal(current_price=xauusd_price)
    pattern_result = run_pattern_engine(last_n=500, select_top=0.3, output_selected_only=True)
    claude_patterns_result = run_claude_pattern_analysis(
        symbol="NDX.INDX",
        timeframes=["5m", "15m", "30m", "1h", "4h", "1d"],
    )
    claude_sentiment_result = await run_claude_sentiment()
    order_blocks_result = await order_block_service.detect(
        symbol="NDX.INDX",
        timeframe="5m",
        limit=500,
        config=OrderBlockConfig(),
    )
    rtyhiim_result = run_rtyhiim_detector(symbol="NDX.INDX", timeframe="1m")
    total_time_ms = int((time.perf_counter() - start) * 1000)
    return RunAllResponse(
        nasdaq=nasdaq_result,
        xauusd=xauusd_result,
        pattern_engine=pattern_result,
        claude_patterns={
            "analyses": claude_patterns_result["analyses"],
            "current_price": claude_patterns_result["current_price"],
        },
        claude_sentiment=claude_sentiment_result,
        order_blocks=order_blocks_result,
        rtyhiim=rtyhiim_result,
        timestamp=datetime.utcnow().isoformat() + "Z",
        total_time_ms=total_time_ms,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
