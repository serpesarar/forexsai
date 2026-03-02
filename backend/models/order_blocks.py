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
    timeframe: Literal["5m", "15m", "30m", "1h", "4h", "1d"] = "5m"
    limit: int = Field(default=500, ge=50, le=500)
    config: OrderBlockConfigRequest | None = None


class OrderBlockEntryRequest(BaseModel):
    symbol: str
    timeframe: Literal["5m", "15m", "30m", "1h", "4h", "1d"]
    order_block_index: int


class OrderBlockBacktestRequest(BaseModel):
    symbol: str
    timeframe: Literal["5m", "15m", "30m", "1h", "4h", "1d"]
    start_date: str
    end_date: str
    config: OrderBlockConfigRequest | None = None


class OrderBlockItem(BaseModel):
    """Flexible OB item supporting both v1 and v2 formats."""
    # Common fields
    type: Literal["bullish", "bearish"]
    zone_low: float
    zone_high: float
    score: float
    has_choch: bool = False
    has_bos: bool = False
    has_fvg: bool = False
    # v2 fields
    detected: Optional[bool] = None
    strength: Optional[str] = None
    tested: Optional[bool] = None
    mitigated: Optional[bool] = None
    # v1 fields (optional for backward compat)
    index: Optional[int] = None
    displacement: Optional[float] = None
    fib_level: Optional[float] = None
    volume_ratio: Optional[float] = None
    test_count: Optional[int] = None
    is_valid: Optional[bool] = None

    class Config:
        extra = "allow"


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


class CHoCHItem(BaseModel):
    detected: Optional[bool] = None
    type: Optional[str] = None
    index: Optional[int] = None
    price: Optional[float] = None
    prev_swing: Optional[float] = None
    strength: Optional[str] = None

    class Config:
        extra = "allow"


class BOSItem(BaseModel):
    detected: Optional[bool] = None
    type: Optional[str] = None
    index: Optional[int] = None
    price: Optional[float] = None
    broken_level: Optional[float] = None
    confirmation: Optional[bool] = None

    class Config:
        extra = "allow"


class FVGItem(BaseModel):
    detected: Optional[bool] = None
    direction: Optional[str] = None
    high: Optional[float] = None
    low: Optional[float] = None
    size: Optional[float] = None
    filled: Optional[bool] = None
    fill_percentage: Optional[float] = None

    class Config:
        extra = "allow"


class StructureCounts(BaseModel):
    choch: int = 0
    bos: int = 0
    fvg: int = 0
    ob: int = 0


class StructureData(BaseModel):
    choch: Optional[List[CHoCHItem]] = None
    bos: Optional[List[BOSItem]] = None
    fvg: Optional[List[FVGItem]] = None
    order_blocks: Optional[List[OrderBlockItem]] = None
    trend: Optional[str] = None
    counts: Optional[StructureCounts] = None

    class Config:
        extra = "allow"


class OrderBlockDetectResponse(BaseModel):
    symbol: str
    timeframe: str
    total_order_blocks: int
    bearish_obs: int
    bullish_obs: int
    order_blocks: List[OrderBlockItem]
    active_signals: List[OrderBlockSignal]
    combined_signal: Optional[CombinedSignal] = None
    structure: Optional[StructureData] = None
    choch_list: Optional[List[CHoCHItem]] = None
    bos_list: Optional[List[BOSItem]] = None
    fvg_list: Optional[List[FVGItem]] = None
    trend: Optional[str] = None
    timestamp: str

    class Config:
        extra = "allow"


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
