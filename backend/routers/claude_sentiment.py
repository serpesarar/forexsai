from fastapi import APIRouter

from backend.models.responses import ClaudeSentimentResponse
from backend.services.sentiment_analyzer import run_claude_sentiment

router = APIRouter(prefix="/api/claude", tags=["claude_sentiment"])


@router.post("/analyze-sentiment", response_model=ClaudeSentimentResponse)
async def analyze_sentiment() -> ClaudeSentimentResponse:
    result = await run_claude_sentiment()
    return ClaudeSentimentResponse(**result)
