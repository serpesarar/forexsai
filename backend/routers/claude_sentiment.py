from fastapi import APIRouter, Query

from backend.models.responses import ClaudeSentimentResponse
from backend.services.sentiment_analyzer import run_claude_sentiment

router = APIRouter(prefix="/api/claude", tags=["claude_sentiment"])


@router.post("/analyze-sentiment", response_model=ClaudeSentimentResponse)
async def analyze_sentiment(
    symbol: str = Query(default="NDX.INDX"),
    lang: str = Query(default="en"),
) -> ClaudeSentimentResponse:
    """
    Per-symbol Claude sentiment. Example:
      POST /api/claude/analyze-sentiment?symbol=NDX.INDX
      POST /api/claude/analyze-sentiment?symbol=XAUUSD
    """
    result = await run_claude_sentiment(symbol=symbol, lang=lang)
    return ClaudeSentimentResponse(**result)
