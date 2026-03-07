import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def _load_order_block_service_module(module_name: str):
    with patch.dict(
        sys.modules,
        {
            "services.ml_service": SimpleNamespace(run_nasdaq_signal=AsyncMock(), run_xauusd_signal=AsyncMock()),
            "services.sentiment_analyzer": SimpleNamespace(run_claude_sentiment=AsyncMock()),
            "services.rtyhiim_service": SimpleNamespace(run_rtyhiim_detector=AsyncMock()),
            "services.data_fetcher": SimpleNamespace(fetch_eod_candles=AsyncMock(return_value=[]), fetch_ohlc_data=AsyncMock(return_value=[])),
            "services.prediction_logger": SimpleNamespace(log_prediction=AsyncMock(return_value="pred-1")),
        },
    ):
        module_path = backend_dir / "services" / "order_block_service.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module


class _FakeOrderBlock:
    def __init__(self, ob_type: str = "bullish", score: float = 70.0, index: int = 4):
        self.type = ob_type
        self.score = score
        self.index = index

    def to_dict(self):
        return {"type": self.type, "score": self.score, "index": self.index, "zone_low": 99.0, "zone_high": 101.0}


class _FakeEvent:
    def __init__(self, index: int = 4):
        self.index = index

    def to_dict(self):
        return {"index": self.index}


class _FakeStructure:
    def __init__(self, trend: str = "bullish"):
        self.trend = trend
        self.ob_list = [_FakeOrderBlock("bullish" if trend == "bullish" else "bearish")]
        self.choch_list = [_FakeEvent()]
        self.bos_list = [_FakeEvent()]
        self.fvg_list = [_FakeEvent()]

    def to_dict(self):
        return {"trend": self.trend}


@pytest.mark.asyncio
async def test_detect_logs_smc_buy_signals_with_prediction_logger():
    module = _load_order_block_service_module("test_order_block_service_buy")
    service = module.OrderBlockService(ttl_seconds=0)

    with patch.object(service, "_load_candles", AsyncMock(return_value=[SimpleNamespace(close=2345.6)])), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "BUY", "confidence": 0.78, "reasoning": ["Bullish structure"]}),
    ), patch.object(module, "log_prediction", AsyncMock(return_value="pred-1")) as mock_log:
        payload = await service.detect("XAUUSD", "15m", 200, module.OrderBlockConfig())

    assert payload["combined_signal"]["action"] == "BUY"
    mock_log.assert_awaited_once()
    kwargs = mock_log.await_args.kwargs
    assert kwargs["symbol"] == "XAUUSD"
    assert kwargs["timeframe"] == "15m"
    assert kwargs["strategy"] == "SMART_MONEY_ZONES"
    assert kwargs["model_type"] == "smc"
    assert kwargs["context"]["ml_prediction"]["entry_price"] == 2345.6
    assert kwargs["context"]["ml_prediction"]["confidence"] == 78.0
    assert kwargs["analysis"]["model_used"] == "SMART_MONEY_ZONES"


@pytest.mark.asyncio
async def test_detect_skips_logging_for_neutral_smc_signal():
    module = _load_order_block_service_module("test_order_block_service_neutral")
    service = module.OrderBlockService(ttl_seconds=0)

    with patch.object(service, "_load_candles", AsyncMock(return_value=[SimpleNamespace(close=21500.0)])), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "NEUTRAL", "confidence": 0.61, "reasoning": ["No edge"]}),
    ), patch.object(module, "log_prediction", AsyncMock(return_value=None)) as mock_log:
        await service.detect("NDX.INDX", "5m", 200, module.OrderBlockConfig())

    mock_log.assert_not_awaited()