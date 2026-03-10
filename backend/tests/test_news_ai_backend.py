from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType

import pytest

def _ensure_optional_dependency_stubs() -> None:
    if "aiohttp" not in sys.modules:
        aiohttp_stub = ModuleType("aiohttp")
        setattr(aiohttp_stub, "ClientSession", object)
        setattr(aiohttp_stub, "ClientTimeout", object)
        sys.modules["aiohttp"] = aiohttp_stub

    if "feedparser" not in sys.modules:
        feedparser_stub = ModuleType("feedparser")

        def _parse_date(*_args, **_kwargs):
            return None

        setattr(feedparser_stub, "_parse_date", _parse_date)
        sys.modules["feedparser"] = feedparser_stub


_ensure_optional_dependency_stubs()

import services.news_candle_matcher as matcher_module
from services.deepseek_json_client import extract_json_object


def _load_module(name: str, relative_path: str):
    _ensure_optional_dependency_stubs()
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


def test_rss_news_response_accepts_bilingual_summary_and_analysis_fields():
    rss_router = _load_module("test_rss_router_module", "routers/rss_router.py")

    response = rss_router.RSSNewsResponse(
        id="news-1",
        timestamp="2026-03-10T12:00:00Z",
        source="Reuters",
        headline="Gold rises after softer CPI print",
        headline_tr="Daha yumuşak TÜFE verisi sonrası altın yükseldi",
        content="Gold moved higher after the inflation surprise.",
        content_tr="Enflasyon sürprizi sonrası altın yükseldi.",
        summary_en="Gold climbed after a softer CPI release.",
        summary_tr="Altın, daha yumuşak gelen TÜFE verisi sonrası yükseldi.",
        analysis_en="Lower inflation expectations weakened the dollar and supported gold.",
        analysis_tr="Daha düşük enflasyon beklentisi doları zayıflattı ve altını destekledi.",
        category="markets",
        url="https://example.com/news-1",
        impacts=[],
        sentiment="neutral",
        volatility_expectation="medium",
        urgency="high",
        ai_confidence=0.82,
        duplicate_of=None,
        sources=["Reuters"],
    )

    assert response.summary_en == "Gold climbed after a softer CPI release."
    assert response.summary_tr == "Altın, daha yumuşak gelen TÜFE verisi sonrası yükseldi."
    assert response.analysis_en.startswith("Lower inflation expectations")
    assert response.analysis_tr.startswith("Daha düşük enflasyon beklentisi")


@pytest.mark.asyncio
async def test_rss_candle_news_response_includes_bilingual_fields(monkeypatch):
    rss_router = _load_module("test_rss_router_candle_news_module", "routers/rss_router.py")

    class FakeMatcher:
        async def match_news_to_candle_simple_ai(self, **_kwargs):
            return [{
                "id": "news-1",
                "headline": "Gold rises after CPI",
                "headline_tr": "TÜFE sonrası altın yükseldi",
                "summary_en": "Gold gained after softer CPI data.",
                "summary_tr": "Altın, yumuşak TÜFE verisi sonrası yükseldi.",
                "analysis_en": "Softer inflation weakened the dollar.",
                "analysis_tr": "Yumuşak enflasyon verisi doları zayıflattı.",
                "content": "English content",
                "content_tr": "Türkçe içerik",
                "timestamp": "2026-03-10T12:00:00Z",
                "source": "Reuters",
                "urgency": "high",
                "relevance_score": 0.91,
                "url": "https://example.com/news-1",
                "symbol_impact": {
                    "score": 9,
                    "direction": "bullish",
                    "reasoning_tr": "Dolar zayıflığı altını destekledi",
                },
            }]

    monkeypatch.setattr(matcher_module, "get_news_candle_matcher", lambda: FakeMatcher())

    result = await rss_router.get_news_for_candle(
        symbol="XAUUSD",
        candle_timestamp="2026-03-10T12:00:00Z",
        candle_open=2900.0,
        candle_close=2912.0,
        candle_high=2915.0,
        candle_low=2898.0,
        timeframe="1h",
    )

    assert result["success"] is True
    assert result["news_count"] == 1
    assert result["news"][0]["summary_tr"].startswith("Altın")
    assert result["news"][0]["analysis_en"].startswith("Softer inflation")
    assert result["news"][0]["headline"] == "TÜFE sonrası altın yükseldi"


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