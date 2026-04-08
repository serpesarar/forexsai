from fastapi import APIRouter, Query

from models.responses import ClaudeSentimentResponse
from services.sentiment_analyzer import run_claude_sentiment

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


@router.post("/analyze-patterns")
async def analyze_patterns(symbol: str = Query(default="NDX.INDX"), lang: str = Query(default="en")):
    """
    Pattern analysis endpoint (deprecated, redirects to stub)
    """
    # Return mock pattern analysis to prevent 404 errors
    return {
        "symbol": symbol,
        "patterns": [],
        "summary": "Pattern analysis temporarily unavailable",
        "message": "Pattern analyzer v2 is being developed",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
    }
