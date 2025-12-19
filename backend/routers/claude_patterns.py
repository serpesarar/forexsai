from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.responses import ClaudePatternsResponse
from backend.services.pattern_analyzer import run_claude_pattern_analysis

router = APIRouter(prefix="/api/claude", tags=["claude_patterns"])


class ClaudePatternRequest(BaseModel):
    symbol: str = "NDX.INDX"
    timeframes: list[str] = ["5m", "15m", "30m", "1h", "4h", "1d"]


@router.post("/analyze-patterns", response_model=ClaudePatternsResponse)
async def analyze_patterns(payload: ClaudePatternRequest) -> ClaudePatternsResponse:
    result = run_claude_pattern_analysis(payload.symbol, payload.timeframes)
    return ClaudePatternsResponse(
        analyses=result["analyses"],
        current_price=result["current_price"],
    )
