from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class OrderBlockConfigRequest(BaseModel):
    fractal_period: int = Field(default=2, ge=1, le=5)
    min_displacement_atr: float = Field(default=1.0, ge=0.1)
    min_score: float = Field(default=50.0, ge=0.0, le=100.0)
    zone_type: Literal["wick", "body"] = "wick"
    max_tests: int = Field(default=2, ge=0, le=5)


class OrderBlockDetectRequest(BaseModel):
    symbol: str = "NDX.INDX"
    timeframe: Literal["5m", "15m", "1h", "4h"] = "5m"
    limit: int = Field(default=500, ge=50, le=500)
    config: OrderBlockConfigRequest | None = None


class OrderBlockEntryRequest(BaseModel):
    symbol: str
    timeframe: Literal["5m", "15m", "1h", "4h"]
    order_block_index: int


class OrderBlockBacktestRequest(BaseModel):
    symbol: str
    timeframe: Literal["5m", "15m", "1h", "4h"]
    start_date: str
    end_date: str
    config: OrderBlockConfigRequest | None = None


class OrderBlockItem(BaseModel):
    index: int
    type: Literal["bullish", "bearish"]
    zone_low: float
    zone_high: float
    score: float
    displacement: float
    has_choch: bool
    has_bos: bool
    has_fvg: bool
    fib_level: float
    volume_ratio: float
    test_count: int
    is_valid: bool


class OrderBlockSignal(BaseModel):
    order_block_index: int
    has_signal: bool
    entry_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float


class CombinedSignal(BaseModel):
    action: str
    confidence: float
    reasoning: List[str]


class OrderBlockDetectResponse(BaseModel):
    symbol: str
    timeframe: str
    total_order_blocks: int
    bearish_obs: int
    bullish_obs: int
    order_blocks: List[OrderBlockItem]
    active_signals: List[OrderBlockSignal]
    combined_signal: Optional[CombinedSignal] = None
    timestamp: str


class OrderBlockEntryResponse(BaseModel):
    has_signal: bool
    entry_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float


class OrderBlockBacktestResponse(BaseModel):
    total_trades: int
    win_rate: float
    avg_risk_reward: float
    total_profit: float
    max_drawdown: float
    sharpe_ratio: float
