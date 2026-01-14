from datetime import datetime
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="AI Trading Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(ok=True)


@app.post("/api/run/all", response_model=RunAllResponse)
async def run_all() -> RunAllResponse:
    start = time.perf_counter()
    nasdaq_price = await fetch_latest_price("NDX.INDX")
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
        nasdaq={
            "signal": nasdaq_result.signal,
            "confidence": nasdaq_result.confidence,
            "reasoning": nasdaq_result.reasoning,
            "metrics": nasdaq_result.metrics,
            "timestamp": nasdaq_result.timestamp,
            "model_status": nasdaq_result.model_status,
        },
        xauusd={
            "signal": xauusd_result.signal,
            "confidence": xauusd_result.confidence,
            "reasoning": xauusd_result.reasoning,
            "metrics": xauusd_result.metrics,
            "timestamp": xauusd_result.timestamp,
            "model_status": xauusd_result.model_status,
        },
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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
