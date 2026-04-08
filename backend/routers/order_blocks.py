from typing import Any
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
from order_block_detector_v2 import MarketStructureAnalyzer
from services.order_block_service import service

router = APIRouter(prefix="/api/order-blocks", tags=["order_blocks"])


def _build_config(payload_config: Any) -> OrderBlockConfig:
    return OrderBlockConfig(**(payload_config.dict() if payload_config else {}))


def _enrich_order_blocks(structure: Any, min_score: float) -> list[dict[str, Any]]:
    enriched_obs: list[dict[str, Any]] = []
    for ob in getattr(structure, "ob_list", []):
        ob_dict = ob.to_dict()
        ob_dict["has_choch"] = any(c.index <= ob.index + 5 for c in getattr(structure, "choch_list", []))
        ob_dict["has_bos"] = any(b.index <= ob.index + 5 for b in getattr(structure, "bos_list", []))
        ob_dict["has_fvg"] = any(f.index <= ob.index + 5 for f in getattr(structure, "fvg_list", []))
        if float(ob_dict.get("score", 0) or 0) >= float(min_score):
            enriched_obs.append(ob_dict)
    return enriched_obs


@router.post("/detect", response_model=OrderBlockDetectResponse)
async def detect_order_blocks(payload: OrderBlockDetectRequest) -> OrderBlockDetectResponse:
    config = _build_config(payload.config)
    result = await service.detect(
        payload.symbol,
        payload.timeframe,
        payload.limit,
        config,
        use_cache=True,
        log_signals=False,
    )
    return OrderBlockDetectResponse(**result)


@router.post("/check-entry", response_model=OrderBlockEntryResponse)
async def check_entry(payload: OrderBlockEntryRequest) -> OrderBlockEntryResponse:
    result = service.check_entry(payload.symbol, payload.timeframe, payload.order_block_index)
    return OrderBlockEntryResponse(**result)


@router.post("/backtest", response_model=OrderBlockBacktestResponse)
async def backtest(payload: OrderBlockBacktestRequest) -> OrderBlockBacktestResponse:
    result = await service.backtest(payload)
    return OrderBlockBacktestResponse(**result)
