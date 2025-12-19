from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any


class HealthResponse(BaseModel):
    ok: bool = True


class SignalMetrics(BaseModel):
    distance_to_ema: float
    distance_to_support: float
    support_strength: float
    rsi: float
    trend: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    current_price: Optional[float] = None


class SignalResponse(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(ge=0, le=1)
    reasoning: List[str]
    metrics: SignalMetrics
    timestamp: str
    model_status: Optional[str] = None


class PatternItem(BaseModel):
    timestamp: str
    pattern_id: str
    route: Literal["BUY", "SELL", "HOLD"]
    p_success: float
    trade_ok: bool
    trade_thr: float
    expected_next: Literal["UP", "DOWN", "SIDEWAYS"]
    stage: str


class PatternEngineResponse(BaseModel):
    patterns: List[PatternItem]
    total_candidates: int
    selected_count: int
    selection_threshold: float
    model_status: Optional[str] = None


class ClaudePatternDetected(BaseModel):
    pattern_name: str
    pattern_source: str
    completion_percentage: int
    signal: Literal["bullish", "bearish", "neutral"]
    entry: float
    stop_loss: float
    target: float
    confidence: float
    reasoning: str


class ClaudePatternTimeframe(BaseModel):
    detected_patterns: List[ClaudePatternDetected]
    summary: str
    recommendation: Literal["BUY", "SELL", "HOLD"]


class ClaudePatternsResponse(BaseModel):
    analyses: Dict[str, ClaudePatternTimeframe]
    current_price: float


class SentimentFactor(BaseModel):
    factor: str
    impact: Literal["positive", "negative", "neutral"]
    weight: float
    reasoning: str


class ClaudeSentimentResponse(BaseModel):
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    confidence: float
    probability_up: int
    probability_down: int
    probability_sideways: int
    key_factors: List[SentimentFactor]
    analysis: str
    recommendation: str
    market_data_summary: Dict[str, Any]
    headlines: List[Dict[str, str]] = []


class RunAllResponse(BaseModel):
    nasdaq: SignalResponse
    xauusd: SignalResponse
    pattern_engine: PatternEngineResponse
    claude_patterns: ClaudePatternsResponse
    claude_sentiment: ClaudeSentimentResponse
    timestamp: str
    total_time_ms: int
