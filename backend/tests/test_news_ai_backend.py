from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

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

    if "anthropic" not in sys.modules:
        anthropic_stub = ModuleType("anthropic")

        class _Anthropic:
            def __init__(self, *args, **kwargs):
                pass

        setattr(anthropic_stub, "Anthropic", _Anthropic)
        sys.modules["anthropic"] = anthropic_stub


_ensure_optional_dependency_stubs()

import services.news_candle_matcher as matcher_module
import services.news_analyzer_v2 as news_analyzer_module
import services.sentiment_analyzer as sentiment_module
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


def test_enforce_news_analysis_consistency_corrects_geopolitical_deescalation_impacts():
    impacts = [
        {"symbol": "XAUUSD", "direction": "bullish", "impact_score": 8, "confidence": 0.81, "reasoning": "safe haven", "reasoning_tr": "güvenli liman"},
        {"symbol": "USOIL", "direction": "bullish", "impact_score": 8, "confidence": 0.79, "reasoning": "supply risk", "reasoning_tr": "arz riski"},
        {"symbol": "VIX", "direction": "bullish", "impact_score": 8, "confidence": 0.84, "reasoning": "fear", "reasoning_tr": "korku"},
        {"symbol": "NDX", "direction": "bearish", "impact_score": 7, "confidence": 0.76, "reasoning": "risk off", "reasoning_tr": "riskten kaçış"},
        {"symbol": "DXY", "direction": "bullish", "impact_score": 6, "confidence": 0.7, "reasoning": "usd bid", "reasoning_tr": "dolar talebi"},
    ]

    adjusted_impacts, adjusted_sentiment = news_analyzer_module.enforce_news_analysis_consistency(
        headline="Iran says it does not want war and is ready to end fighting if guarantees are met",
        content="The Iranian president said the country does not want war and is ready to end the conflict if guarantees are provided.",
        summary_en="Iran signaled willingness to end the conflict if guarantees are met.",
        analysis_en="This is a geopolitical de-escalation signal that should reduce fear premiums across markets.",
        impacts=impacts,
        sentiment="risk_off",
    )

    impacts_by_symbol = {news_analyzer_module._normalize_symbol_alias(item["symbol"]): item for item in adjusted_impacts}

    assert adjusted_sentiment == "risk_on"
    assert impacts_by_symbol["VIX"]["direction"] == "bearish"
    assert impacts_by_symbol["NDX"]["direction"] == "bullish"
    assert impacts_by_symbol["XAUUSD"]["direction"] == "bearish"
    assert impacts_by_symbol["USOIL"]["direction"] == "bearish"
    assert impacts_by_symbol["DXY"]["direction"] == "bearish"


def test_enforce_news_analysis_consistency_corrects_explicit_oil_drop_direction():
    adjusted_impacts, adjusted_sentiment = news_analyzer_module.enforce_news_analysis_consistency(
        headline="ABD ve İran'dan savaş çözümüne açıklık işaretleri üzerine petrol düştü",
        content="Diplomatik ilerleme işaretleri sonrası petrol düştü ve bölgesel arz riski primi geriledi.",
        summary_en="Oil fell after signs of diplomatic progress between the United States and Iran.",
        analysis_en="The geopolitical risk premium eased as the market priced in lower supply disruption risk.",
        summary_tr="ABD ile İran arasında diplomatik ilerleme sinyalleri sonrası petrol düştü.",
        analysis_tr="Jeopolitik risk priminin azalması petrol üzerinde aşağı yönlü baskı yarattı.",
        impacts=[
            {"symbol": "USOIL", "direction": "bullish", "impact_score": 8, "confidence": 0.82, "reasoning": "oil should rise", "reasoning_tr": "petrol yükselişi"},
            {"symbol": "VIX", "direction": "bullish", "impact_score": 7, "confidence": 0.74, "reasoning": "fear", "reasoning_tr": "korku"},
        ],
        sentiment="risk_off",
    )

    impacts_by_symbol = {news_analyzer_module._normalize_symbol_alias(item["symbol"]): item for item in adjusted_impacts}

    assert adjusted_sentiment == "risk_on"
    assert impacts_by_symbol["USOIL"]["direction"] == "bearish"
    assert impacts_by_symbol["USOIL"]["confidence"] >= 0.74
    assert impacts_by_symbol["VIX"]["direction"] == "bearish"


def test_rss_sanitize_news_item_applies_consistency_guardrails_to_stored_rows():
    rss_router = _load_module("test_rss_router_sanitize_module", "routers/rss_router.py")

    sanitized = rss_router._sanitize_news_item({
        "headline": "Iran says it does not want war and is ready to end fighting if guarantees are met",
        "content": "Diplomatic progress reduces the immediate risk of wider regional conflict.",
        "summary_en": "Iran signaled willingness to end the conflict.",
        "analysis_en": "This is a de-escalation signal that should reduce fear and safe-haven demand.",
        "summary_tr": "İran çatışmayı bitirmeye hazır olduğunu söyledi.",
        "analysis_tr": "Gerilimin azalması korku primini düşürebilir.",
        "sentiment": "risk_off",
        "impacts": [
            {"symbol": "VIX", "direction": "bullish", "score": 8, "confidence": 0.8, "reasoning": "fear bid", "reasoning_tr": "korku primi"},
            {"symbol": "NDX", "direction": "bearish", "score": 7, "confidence": 0.76, "reasoning": "equities weaker", "reasoning_tr": "hisseler zayıf"},
        ],
        "ai_model": "deepseek-reasoner",
        "ai_confidence": 0.82,
    })

    impacts_by_symbol = {item["symbol"]: item for item in sanitized["impacts"]}

    assert sanitized["sentiment"] == "risk_on"
    assert impacts_by_symbol["VIX"]["direction"] == "bearish"
    assert impacts_by_symbol["NDX"]["direction"] == "bullish"


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


@pytest.mark.asyncio
async def test_run_claude_sentiment_fetches_marketaux_using_symbol_list(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_fetch_latest_price(_symbol):
        return 123.45

    async def fake_fetch_marketaux_headlines(symbols):
        captured["symbols"] = symbols
        return [{"title": "Gold steady", "source": "Reuters"}]

    async def fake_deepseek(prompt):
        assert "Instrument: XAUUSD" in prompt
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.61,
            "probability_up": 33,
            "probability_down": 31,
            "probability_sideways": 36,
            "key_factors": [],
            "analysis": "ok",
            "recommendation": "HOLD",
        }

    monkeypatch.setattr(sentiment_module, "fetch_latest_price", fake_fetch_latest_price)
    monkeypatch.setattr(sentiment_module, "fetch_marketaux_headlines", fake_fetch_marketaux_headlines)
    monkeypatch.setattr(sentiment_module, "_call_deepseek_sentiment", fake_deepseek)
    monkeypatch.setattr(sentiment_module.settings, "anthropic_api_key", None, raising=False)
    monkeypatch.setattr(sentiment_module.settings, "deepseek_api_key", "test-key", raising=False)

    redis_module = SimpleNamespace(cache_get=lambda _key: {}, cache_set=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "services.redis_client", redis_module)

    result = await sentiment_module.run_claude_sentiment(symbol="XAUUSD", lang="en")

    assert captured["symbols"] == ["XAUUSD"]
    assert result["sentiment"] == "NEUTRAL"
    assert result["market_data_summary"]["news_source"] == "marketaux+deepseek"


@pytest.mark.asyncio
async def test_rss_aggregator_store_in_database_executes_insert(monkeypatch):
    rss_aggregator = _load_module("test_rss_aggregator_module", "services/rss_aggregator.py")

    class FakeTable:
        def __init__(self):
            self.insert_executed = False
            self.mode = None

        def select(self, *_args, **_kwargs):
            self.mode = "select"
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def execute(self):
            if self.mode == "insert":
                self.insert_executed = True
            return {"data": []}

        def insert(self, payload):
            self.mode = "insert"
            self.payload = payload
            return self

    class FakeSupabase:
        def __init__(self):
            self.table_instance = FakeTable()

        def table(self, _name):
            return self.table_instance

    fake_supabase = FakeSupabase()
    monkeypatch.setattr(rss_aggregator, "get_supabase_client", lambda: fake_supabase)

    aggregator = rss_aggregator.RSSAggregator()

    async def passthrough(item):
        return item

    monkeypatch.setattr(aggregator, "_check_economic_calendar", passthrough)

    item = rss_aggregator.RSSNewsItem(
        id="news-123",
        source="Reuters",
        original_url="https://example.com/news-123",
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        title="Gold climbs",
        content="Gold climbs after CPI.",
        category="markets",
        impacts=[{"symbol": "XAUUSD", "direction": "bullish", "score": 8}],
        sentiment="bullish",
        volatility_expectation="high",
        urgency="high",
        ai_confidence=0.91,
        ai_processed=True,
        processed_at=datetime.now(timezone.utc),
        duplicate_of=None,
        sources=["Reuters"],
    )

    stored = await aggregator.store_in_database(item)

    assert stored is True
    assert fake_supabase.table_instance.insert_executed is True


@pytest.mark.asyncio
async def test_claude_news_compat_analyze_uses_cached_rss_items(monkeypatch):
    claude_news = _load_module("test_claude_news_module", "routers/claude_news.py")

    class FakeQuery:
        def select(self, *_args, **_kwargs):
            return self

        def gte(self, *_args, **_kwargs):
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            return {
                "data": [{
                    "id": "n1",
                    "timestamp": "2026-03-10T12:00:00Z",
                    "source": "Reuters",
                    "headline": "Gold rises after CPI",
                    "impacts": [{"symbol": "XAUUSD", "direction": "bullish", "score": 9, "reasoning_tr": "Dolar zayıfladı"}],
                    "sentiment": "bullish",
                    "ai_confidence": 88,
                    "category": "markets",
                    "analysis_timestamp": "2026-03-10T12:05:00Z",
                    "analysis_tr": "Altın için pozitif",
                }]
            }

    class FakeSupabase:
        def table(self, _name):
            return FakeQuery()

    monkeypatch.setattr(claude_news, "get_supabase_client", lambda: FakeSupabase())

    result = await claude_news.analyze_news("XAUUSD", limit=15, hours_back=24)

    assert result["news_count"] == 1
    assert result["direction_bias"] == "bullish"
    assert result["analyses"][0]["override_signal"] == "bullish"