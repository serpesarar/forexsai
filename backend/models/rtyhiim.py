from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class RtyhiimPrediction(BaseModel):
    horizon: str
    value: float
    confidence: float


class RtyhiimReactionZone(BaseModel):
    next_type: str             # 'support' (dip) | 'resistance' (tepe)
    expected_direction: str    # BUY at support, SELL at resistance
    price: float
    band: float                # deviation half-width ('sapma payı')
    lower: float
    upper: float
    eta_seconds: float
    eta_label: str
    eta_bars: int


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
    timeframe_used: str = "5m"
    bars: int = 0
    data_source: str = "live"          # live | no_data
    oos_skill: float = 0.0
    significance: float = 0.0
    upper_touches: int = 0
    lower_touches: int = 0
    touches_confirmed: bool = False
    reaction_zone: Optional[RtyhiimReactionZone] = None


class RtyhiimResponse(BaseModel):
    symbol: str
    timeframe: str
    state: RtyhiimState
    timestamp: str
