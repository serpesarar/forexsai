from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class ChartCandle(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(ge=0)


class SupportResistanceLevel(BaseModel):
    type: Literal["support", "resistance"]
    price: float
    label: str


class ChartDataResponse(BaseModel):
    symbol: str
    timeframe: str
    data: List[ChartCandle]
    support_resistance: List[SupportResistanceLevel]
