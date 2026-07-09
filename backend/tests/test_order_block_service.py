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
            "services.prediction_logger": SimpleNamespace(log_smc_prediction=AsyncMock(return_value="pred-1")),
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
        self.swing_list = []
        self.projection = None

    def to_dict(self):
        return {"trend": self.trend}


@pytest.mark.asyncio
async def test_detect_logs_smc_buy_signals_with_prediction_logger():
    module = _load_order_block_service_module("test_order_block_service_buy")
    service = module.OrderBlockService(ttl_seconds=0)

    with patch.object(service, "_load_candles", AsyncMock(side_effect=lambda **kw: ([SimpleNamespace(close=2345.6)], kw.get("timeframe", "5m")))), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "BUY", "confidence": 0.78, "reasoning": ["Bullish structure"]}),
    ), patch.object(module, "log_smc_prediction", AsyncMock(return_value="pred-1")) as mock_log:
        payload = await service.detect("XAUUSD", "15m", 200, module.OrderBlockConfig())

    assert payload["combined_signal"]["action"] == "BUY"
    mock_log.assert_awaited_once()
    kwargs = mock_log.await_args.kwargs
    assert kwargs["symbol"] == "XAUUSD"
    assert kwargs["timeframe"] == "15m"
    assert kwargs["entry_price"] == 2345.6
    assert kwargs["confidence"] == 78.0
    assert kwargs["direction"] == "BUY"
    assert kwargs["reasoning"] == ["Bullish structure"]


@pytest.mark.asyncio
async def test_detect_skips_logging_for_neutral_smc_signal():
    module = _load_order_block_service_module("test_order_block_service_neutral")
    service = module.OrderBlockService(ttl_seconds=0)

    with patch.object(service, "_load_candles", AsyncMock(side_effect=lambda **kw: ([SimpleNamespace(close=21500.0)], kw.get("timeframe", "5m")))), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "NEUTRAL", "confidence": 0.61, "reasoning": ["No edge"]}),
    ), patch.object(module, "log_smc_prediction", AsyncMock(return_value=None)) as mock_log:
        await service.detect("NDX.INDX", "5m", 200, module.OrderBlockConfig())

    mock_log.assert_not_awaited()


@pytest.mark.asyncio
async def test_detect_can_disable_signal_logging_for_read_only_panel_calls():
    module = _load_order_block_service_module("test_order_block_service_read_only")
    service = module.OrderBlockService(ttl_seconds=300)

    with patch.object(service, "_load_candles", AsyncMock(side_effect=lambda **kw: ([SimpleNamespace(close=2345.6)], kw.get("timeframe", "5m")))), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "BUY", "confidence": 0.78, "reasoning": ["Bullish structure"]}),
    ), patch.object(module, "log_smc_prediction", AsyncMock(return_value="pred-1")) as mock_log:
        payload = await service.detect(
            "XAUUSD",
            "15m",
            200,
            module.OrderBlockConfig(),
            log_signals=False,
        )

    assert payload["combined_signal"]["action"] == "BUY"
    mock_log.assert_not_awaited()


@pytest.mark.asyncio
async def test_detect_can_bypass_cache_for_scheduler_logging():
    module = _load_order_block_service_module("test_order_block_service_cache_bypass")
    service = module.OrderBlockService(ttl_seconds=300)

    with patch.object(service, "_load_candles", AsyncMock(side_effect=lambda **kw: ([SimpleNamespace(close=2345.6)], kw.get("timeframe", "5m")))), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "BUY", "confidence": 0.78, "reasoning": ["Bullish structure"]}),
    ), patch.object(module, "log_smc_prediction", AsyncMock(return_value="pred-1")) as mock_log:
        await service.detect(
            "XAUUSD",
            "15m",
            200,
            module.OrderBlockConfig(),
            log_signals=False,
        )
        await service.detect(
            "XAUUSD",
            "15m",
            200,
            module.OrderBlockConfig(),
            use_cache=False,
            log_signals=True,
        )

    mock_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_detect_returns_support_resistance_payload_for_panel_rendering():
    module = _load_order_block_service_module("test_order_block_service_support_resistance")
    service = module.OrderBlockService(ttl_seconds=0)

    candle = SimpleNamespace(close=21500.0, high=21540.0, low=21460.0)
    candles = [candle for _ in range(80)]

    with patch.object(service, "_load_candles", AsyncMock(side_effect=lambda **kw: (candles, kw.get("timeframe", "5m")))), patch.object(
        module.MarketStructureAnalyzer, "analyze", return_value=_FakeStructure("bullish")
    ), patch.object(module.OrderBlockDetector, "detect", return_value=[]), patch.object(
        service,
        "_combine_signals",
        AsyncMock(return_value={"action": "BUY", "confidence": 0.78, "reasoning": ["Bullish structure"]}),
    ), patch.object(module, "log_smc_prediction", AsyncMock(return_value=None)):
        payload = await service.detect("NDX.INDX", "15m", 200, module.OrderBlockConfig(), log_signals=False)

    support_resistance = payload["support_resistance"]
    assert support_resistance["method"] == "swing_cluster_fib"
    assert support_resistance["nearest_support"] is not None
    assert support_resistance["nearest_resistance"] is not None
    assert support_resistance["all_levels"]

@pytest.mark.asyncio
async def test_mtf_alignment_vetoes_signal_opposed_by_both_htf_structures():
    module = _load_order_block_service_module("obs_mtf_veto")
    service = module.OrderBlockService(ttl_seconds=0)
    with patch.object(service, "_htf_trend", AsyncMock(side_effect=lambda s, tf: "bearish")):
        sig, info = await service._apply_mtf_alignment(
            "XAUUSD", "15m", {"action": "BUY", "confidence": 0.8, "reasons": [], "reasoning": []}
        )

    assert sig["action"] == "NEUTRAL"
    assert "MTF veto" in sig["reasons"][-1]
    assert info["applied"] is True


@pytest.mark.asyncio
async def test_mtf_alignment_reduces_confidence_when_one_htf_opposes():
    module = _load_order_block_service_module("obs_mtf_caution")
    service = module.OrderBlockService(ttl_seconds=0)
    async def one(symbol, tf):
        return "bearish" if tf == "1h" else "bullish"

    with patch.object(service, "_htf_trend", AsyncMock(side_effect=one)):
        sig, _ = await service._apply_mtf_alignment(
            "XAUUSD", "5m", {"action": "BUY", "confidence": 0.8, "reasons": [], "reasoning": []}
        )

    assert sig["action"] == "BUY"
    assert sig["confidence"] == pytest.approx(0.6)
    assert "MTF caution" in sig["reasons"][-1]


@pytest.mark.asyncio
async def test_mtf_alignment_fails_open_without_htf_data_and_skips_htf_requests():
    module = _load_order_block_service_module("obs_mtf_failopen")
    service = module.OrderBlockService(ttl_seconds=0)
    with patch.object(service, "_htf_trend", AsyncMock(return_value=None)):
        sig, _ = await service._apply_mtf_alignment(
            "XAUUSD", "15m", {"action": "SELL", "confidence": 0.7, "reasons": [], "reasoning": []}
        )
    assert sig["action"] == "SELL" and sig["confidence"] == 0.7

    _, info = await service._apply_mtf_alignment("XAUUSD", "1h", {"action": "SELL", "confidence": 0.8})
    assert info["applied"] is False
