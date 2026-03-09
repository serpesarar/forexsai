from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

import pytest

if "aiohttp" not in sys.modules:
    aiohttp_stub = ModuleType("aiohttp")
    aiohttp_stub.ClientSession = object
    aiohttp_stub.ClientTimeout = object
    sys.modules["aiohttp"] = aiohttp_stub

import services.news_candle_matcher as matcher_module
from services.deepseek_json_client import extract_json_object


def _load_module(name: str, relative_path: str):
    spec = spec_from_file_location(name, Path(__file__).resolve().parents[1] / relative_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


news_correlation = _load_module("test_news_correlation_module", "routers/news_correlation.py")


def test_extract_json_object_parses_fenced_incomplete_json():
    payload = """```json
    {
      \"explanation\": \"Altın CPI sonrası güçlendi\",
      \"confidence\": 82,
    ```"""

    parsed = extract_json_object(payload)

    assert parsed == {
        "explanation": "Altın CPI sonrası güçlendi",
        "confidence": 82,
    }


@pytest.mark.asyncio
async def test_generate_move_explanation_falls_back_when_ai_response_missing(monkeypatch):
    async def fake_call(*args, **kwargs):
        return None

    monkeypatch.setattr(news_correlation, "call_deepseek_json", fake_call)

    result = await news_correlation._generate_move_explanation(
        symbol="XAUUSD",
        candle={"open": 2000.0, "high": 2012.0, "low": 1998.0, "close": 2010.0},
        candle_time=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
        change_percent=0.5,
        related_news=[
            {
                "id": "news-1",
                "headline": "US CPI missed expectations",
                "ai_confidence": 77,
                "symbol_impact": {"reasoning_tr": "Dolar zayıflığı altını destekledi"},
            }
        ],
    )

    assert result["confidence"] == 77
    assert "Dolar zayıflığı altını destekledi" in result["explanation"]
    assert "DeepSeek analizinde" not in result["explanation"]


@pytest.mark.asyncio
async def test_rerank_with_ai_applies_order_and_metadata(monkeypatch):
    async def fake_call(*args, **kwargs):
        return {
            "confidence": 91,
            "matches": [
                {
                    "id": "n2",
                    "reasoning_tr": "İkinci haber mum yönüyle daha uyumlu",
                    "importance_level": "critical",
                    "importance_score": 94,
                },
                {
                    "id": "n1",
                    "reasoning_tr": "Birinci haber destekleyici ama ikincil",
                    "importance_level": "high",
                    "importance_score": 81,
                },
            ],
        }

    monkeypatch.setattr(matcher_module, "call_deepseek_json", fake_call)
    matcher = matcher_module.NewsCandleMatcher.__new__(matcher_module.NewsCandleMatcher)
    candle = matcher_module.CandleInfo(
        timestamp=datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc),
        open=100.0,
        high=106.0,
        low=99.0,
        close=105.0,
        volume=0,
    )
    candidates = [
        {
            "id": "n1",
            "headline": "Older candidate",
            "timestamp": "2026-03-09T11:50:00+00:00",
            "urgency": "high",
            "relevance_score": 0.82,
            "time_diff_minutes": -10,
            "symbol_impact": {"direction": "bullish", "score": 8, "reasoning_tr": "Destekleyici"},
        },
        {
            "id": "n2",
            "headline": "Better candidate",
            "timestamp": "2026-03-09T11:58:00+00:00",
            "urgency": "breaking",
            "relevance_score": 0.79,
            "time_diff_minutes": -2,
            "symbol_impact": {"direction": "bullish", "score": 9, "reasoning_tr": "Daha güçlü"},
        },
        {
            "id": "n3",
            "headline": "Unranked candidate",
            "timestamp": "2026-03-09T11:40:00+00:00",
            "urgency": "medium",
            "relevance_score": 0.55,
            "time_diff_minutes": -20,
            "symbol_impact": {"direction": "neutral", "score": 5, "reasoning_tr": "Zayıf"},
        },
    ]

    ranked = await matcher._rerank_with_ai(
        symbol="NDX",
        candle=candle,
        timeframe="1h",
        significance={"movement_type": "major"},
        candidates=candidates,
    )

    assert [item["id"] for item in ranked[:3]] == ["n2", "n1", "n3"]
    assert ranked[0]["ai_reasoning_tr"] == "İkinci haber mum yönüyle daha uyumlu"
    assert ranked[0]["importance_level"] == "critical"
    assert ranked[0]["importance_score"] == 94
    assert ranked[0]["ai_match_confidence"] == 91