from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class RtyhiimPrediction(BaseModel):
    horizon: str
    value: float
    confidence: float


class RtyhiimState(BaseModel):
    pattern_type: str
    dominant_period_s: float
    confidence: float
    regularity: float
    phase: float
    amplitude: float
    should_trade: bool
    direction: str
    predictions: List[RtyhiimPrediction]


class RtyhiimResponse(BaseModel):
    symbol: str
    timeframe: str
    state: RtyhiimState
    timestamp: str
