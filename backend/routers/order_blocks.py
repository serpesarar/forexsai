from fastapi import APIRouter

from models.order_blocks import (
    OrderBlockBacktestRequest,
    OrderBlockBacktestResponse,
    OrderBlockDetectRequest,
    OrderBlockDetectResponse,
    OrderBlockEntryRequest,
    OrderBlockEntryResponse,
)
from order_block_detector import OrderBlockConfig
from services.order_block_service import service

router = APIRouter(prefix="/api/order-blocks", tags=["order_blocks"])


@router.post("/detect", response_model=OrderBlockDetectResponse)
async def detect_order_blocks(payload: OrderBlockDetectRequest) -> OrderBlockDetectResponse:
    config = OrderBlockConfig(**(payload.config.dict() if payload.config else {}))
    result = await service.detect(payload.symbol, payload.timeframe, payload.limit, config)
    return OrderBlockDetectResponse(**result)


@router.post("/check-entry", response_model=OrderBlockEntryResponse)
async def check_entry(payload: OrderBlockEntryRequest) -> OrderBlockEntryResponse:
    result = service.check_entry(payload.symbol, payload.timeframe, payload.order_block_index)
    return OrderBlockEntryResponse(**result)


@router.post("/backtest", response_model=OrderBlockBacktestResponse)
async def backtest(payload: OrderBlockBacktestRequest) -> OrderBlockBacktestResponse:
    result = service.backtest(payload.symbol, payload.timeframe)
    return OrderBlockBacktestResponse(**result)
