"""Haber motoru birim testleri: ağ yok, gerçek biçimlerde sabit örnekler."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from services.newsfeed import adapters as ad
from services.newsfeed.catalog import SOURCES, SourceDef, active_sources, inactive_sources
from services.newsfeed.classifier import classify
from services.newsfeed.dedup import is_same_story, normalize, tokens
from services.newsfeed.engine import NewsEngine, in_release_window
from services.newsfeed.scoreboard import MIN_INTERVAL_S, MIN_SAMPLES, Scoreboard


class NullStore:
    """Veritabanına gitmeyen kuyruk: sıra ve içerik sınanır."""

    def __init__(self) -> None:
        self.stories, self.sightings, self.legacy = [], [], []
        self.stats = {}

    def queue_story(self, row):
        self.stories.append(row)

    def queue_sighting(self, row):
        self.sightings.append(row)

    def queue_legacy(self, row):
        self.legacy.append(row)


def _src(sid: str, tier: str = "squawk", interval: int = 20) -> SourceDef:
    return SourceDef(sid, sid, "rss", "http://x", tier, "t/t", interval)


def _engine(*ids: str) -> NewsEngine:
    return NewsEngine(sources=[_src(i) for i in ids], store=NullStore())


FED = "BREAKING: Federal Reserve cuts interest rates by 25 basis points in surprise move"
FED2 = "Federal Reserve cuts interest rates by 25 basis points in a surprise move, statement shows"


def test_normalize_keeps_numbers_and_drops_prefix() -> None:
    assert normalize("BREAKING: Gold +1.5% to $2,400!") == "gold 1.5% to $2 400"


def test_same_story_matches_rewording_not_unrelated() -> None:
    a, b = normalize(FED), normalize(FED2)
    assert is_same_story(a, tokens(a), b, tokens(b))
    c = normalize("Bank of Japan holds interest rates steady at 0.5 percent policy meeting")
    assert not is_same_story(a, tokens(a), c, tokens(c))


def test_short_headline_needs_exact_match() -> None:
    a, b = normalize("Gold rises sharply"), normalize("Gold rises sharply today again")
    assert not is_same_story(a, tokens(a), b, tokens(b))


def test_first_source_wins_and_second_joins() -> None:
    e = _engine("a", "b")
    e._seeded.update({"a", "b"})
    row = e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1000.0, False, 20)
    assert row["first_source"] == "a"
    assert e.ingest(e.sources[1], ad.RawItem("9", FED2, "v", None), 1012.0, False, 20) is None
    assert row["n_sources"] == 2 and row["sources"] == ["a", "b"]
    races = {s: list(e.board._races[s]) for s in ("a", "b")}
    assert races["a"][0][3] is True and races["b"][0][3] is False
    assert races["b"][0][1] == pytest.approx(12.0)


def test_same_ext_id_is_not_processed_twice() -> None:
    e = _engine("a")
    assert e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1000.0, False, 20) is not None
    assert e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1001.0, False, 20) is None


def test_seeded_items_never_enter_race_or_stream() -> None:
    e = _engine("a", "b")
    e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1000.0, True, 20)
    e.ingest(e.sources[1], ad.RawItem("2", FED2, "v", None), 1010.0, False, 20)
    assert not e.board._races["a"] and not e.board._races["b"]
    assert not e.store.legacy


def test_stale_item_is_treated_as_seed() -> None:
    e = _engine("a")
    row = e.ingest(e.sources[0], ad.RawItem("1", FED, "u", 1000.0), 1000.0 + 7 * 3600, False, 20)
    assert row["seeded"] is True


def test_low_relevance_story_is_not_persisted_even_on_join() -> None:
    e = _engine("a", "b")
    text = "Local bakery opens second branch downtown this weekend with live music"
    e.ingest(e.sources[0], ad.RawItem("1", text, "u", None), 1000.0, False, 20)
    e.ingest(e.sources[1], ad.RawItem("2", text, "v", None), 1001.0, False, 20)
    assert e.store.stories == [] and e.store.sightings == []


def test_relevant_story_reaches_legacy_bridge_without_ai() -> None:
    e = _engine("a")
    e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1000.0, False, 20)
    leg = e.store.legacy[0]
    assert leg["id"].startswith("nf_") and leg["ai_model"] == "newsfeed_rule" and leg["impacts"] == []


def test_adjusted_lag_removes_polling_wait() -> None:
    e = NewsEngine(sources=[_src("fast", interval=20), _src("slow", interval=120)], store=NullStore())
    e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 1000.0, False, 20)
    e.ingest(e.sources[1], ad.RawItem("2", FED2, "v", None), 1060.0, False, 120)
    _, raw, adj, _ = e.board._races["slow"][0]
    assert raw == pytest.approx(60.0) and adj == pytest.approx(10.0)


def test_interval_unchanged_until_enough_races() -> None:
    srcs = [_src("a"), _src("b"), _src("c")]
    b = Scoreboard(srcs)
    assert b.interval_for("a") == 20
    import time
    now = time.time()
    for i, sid in enumerate(("a", "b", "c")):
        for _ in range(MIN_SAMPLES):
            b._races[sid].append((now, i * 30.0, i * 30.0, i == 0))
    assert b.interval_for("a") == max(MIN_INTERVAL_S, 10)
    assert b.interval_for("c") == 40


def test_burst_only_for_official_and_squawk() -> None:
    b = Scoreboard([_src("o", "official", 60), _src("m", "media", 60)])
    assert b.interval_for("o", burst=True) == 8.0
    assert b.interval_for("m", burst=True) == 60


def test_release_window_respects_timezone_and_weekend() -> None:
    et = ZoneInfo("America/New_York")
    assert in_release_window(datetime(2026, 11, 6, 8, 30, tzinfo=et).timestamp())
    assert not in_release_window(datetime(2026, 11, 7, 8, 30, tzinfo=et).timestamp())
    assert not in_release_window(datetime(2026, 11, 6, 3, 0, tzinfo=et).timestamp())


def test_parse_rss_extracts_guid_and_time() -> None:
    body = b"""<rss version="2.0"><channel><item><title>Fed &amp; markets</title><link>http://a</link><guid>g1</guid>
    <pubDate>Wed, 04 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>"""
    item = ad.parse_rss(body)[0]
    assert item.ext_id == "g1" and item.title == "Fed & markets"
    assert item.published_ts == datetime(2026, 11, 4, 12, tzinfo=timezone.utc).timestamp()


def test_parse_telegram_preview_page() -> None:
    html = b"""<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="fj/77">
    <div class="tgme_widget_message_text js-message_text" dir="auto">US CPI <b>3.1%</b><br/>vs 3.0% expected</div>
    <time datetime="2026-11-04T13:30:00+00:00" class="time">13:30</time></div></div>"""
    item = ad.parse_telegram(html)[0]
    assert item.ext_id == "fj/77" and item.title == "US CPI 3.1% vs 3.0% expected"
    assert item.url == "https://t.me/fj/77"


def test_parse_truth_marks_author_and_media_only() -> None:
    body = json.dumps([{"id": "5", "content": "<p>TARIFFS on steel!</p>", "url": "u", "created_at": "2026-11-04T23:33:47.879Z"},
                       {"id": "6", "content": "", "url": "v", "created_at": "2026-11-04T23:40:00Z"}]).encode()
    a, b = ad.parse_truth(body)
    assert a.title == "Trump (Truth Social): TARIFFS on steel!"
    assert "Metinsiz" in b.title


def test_alpaca_frame_only_news_messages() -> None:
    frame = json.dumps([{"T": "success", "msg": "connected"},
                        {"T": "n", "id": 9, "headline": "Apple beats", "url": "u", "created_at": "2026-11-04T10:00:00Z"}])
    items = ad.parse_alpaca_frame(frame)
    assert len(items) == 1 and items[0].ext_id == "9"


def test_benzinga_ignores_updates_and_removals() -> None:
    created = {"data": {"action": "Created", "id": 1, "content": {"title": "T", "url": "u", "created_at": "2026-11-04T10:00:00Z"}}}
    updated = {"data": {"action": "Updated", "id": 1, "content": {"title": "T2"}}}
    assert len(ad.parse_benzinga_frame(json.dumps(created))) == 1
    assert ad.parse_benzinga_frame(json.dumps(updated)) == []


@pytest.mark.parametrize("title,event,sym", [
    ("Fed cuts rates by 25 bps", "cb_decision", "XAUUSD"),
    ("US CPI rises 3.1% in October", "macro_print", "NDX.INDX"),
    ("Trump announces new tariffs on EU cars", "tariff_trade", "GDAXI.INDX"),
    ("OPEC+ agrees to extend oil output cuts", "energy", "USOIL.FOREX"),
    ("Gold hits record as bullion demand climbs", "metals", "XAUUSD"),
    ("Missiles hit Tel Aviv as Iran retaliates", "geopolitics", "USOIL.FOREX"),
    ("Nvidia shares jump after earnings", "big_tech", "NDX.INDX"),
])
def test_classifier_routes_events(title: str, event: str, sym: str) -> None:
    c = classify(title, "media")
    assert c.event_type == event and sym in c.symbols


def test_classifier_never_outputs_direction_and_flags_opinion() -> None:
    c = classify("Here's why gold could rally: best stocks to buy", "media")
    assert c.is_opinion and c.urgency == "low"
    assert not hasattr(c, "direction")


def test_classifier_official_vs_hedged() -> None:
    assert classify("Federal Reserve issues FOMC statement", "official").confirmation == "official"
    assert classify("Trump considering new tariffs, sources say", "media").confirmation == "unconfirmed"


def test_catalog_ids_unique_and_keyed_sources_stay_off(monkeypatch: pytest.MonkeyPatch) -> None:
    ids = [s.id for s in SOURCES]
    assert len(ids) == len(set(ids))
    for k in ("FINNHUB_API_KEY", "ALPACA_API_KEY", "ALPACA_SECRET_KEY", "BENZINGA_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    active = {s.id for s in active_sources()}
    assert "alpaca_news" not in active and "financialjuice_rss" in active
    assert any(r["id"] == "alpaca_news" and "anahtar" in r["reason"] for r in inactive_sources())


def test_disabled_source_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEWSFEED_DISABLED_SOURCES", "marketfeed_tg")
    assert "marketfeed_tg" not in {s.id for s in active_sources()}


def test_seeded_row_shows_publish_time_and_old_seed_is_hidden() -> None:
    import time
    e = _engine("a")
    now = time.time()
    fresh = e.ingest(e.sources[0], ad.RawItem("1", FED, "u", now - 600), now, True, 20)
    assert fresh["display_ts"] == now - 600
    old = "Bank of England raises rates by 50 basis points in emergency meeting today"
    e.ingest(e.sources[0], ad.RawItem("2", old, "v", now - 90000), now, True, 20)
    ids = [r["headline"] for r in e.latest(min_relevance=0)]
    assert ids == [FED]


def test_generic_politics_from_media_stays_below_threshold() -> None:
    assert classify("Man arrested near White House after gesture", "media").relevance < 50
    assert classify("White House issues executive order on trade", "official").relevance >= 50


def test_scoreboard_restore_rebuilds_races_and_skips_singletons() -> None:
    b = Scoreboard([_src("a"), _src("b", interval=120)])
    rows = [
        {"story_id": "s1", "source_id": "a", "first_seen_at": "2026-11-05T10:00:00+00:00", "poll_interval_s": 20},
        {"story_id": "s1", "source_id": "b", "first_seen_at": "2026-11-05T10:01:00+00:00", "poll_interval_s": 120},
        {"story_id": "s2", "source_id": "a", "first_seen_at": "2026-11-05T11:00:00+00:00", "poll_interval_s": 20},
        {"story_id": "s3", "source_id": "kaldirilmis", "first_seen_at": "2026-11-05T11:00:00+00:00", "poll_interval_s": 20},
    ]
    assert b.restore(rows) == 2
    assert b._races["a"][0][3] is True
    _, raw, adj, first = b._races["b"][0]
    assert raw == pytest.approx(60) and adj == pytest.approx(10) and first is False


def test_legacy_row_satisfies_table_and_api_contract() -> None:
    e = _engine("a")
    e.ingest(e.sources[0], ad.RawItem("1", FED, "", None), 1000.0, False, 20)
    leg = e.store.legacy[0]
    assert leg["sentiment"] in ("risk_on", "risk_off", "neutral")
    assert leg["urgency"] in ("breaking", "high", "medium", "low")
    assert leg["event_duration"] in ("immediate", "short_term", "long_term")
    assert leg["url"] == "" and leg["ai_confidence"] == 0 and isinstance(leg["sources"], list)


def test_router_latest_status_sources_and_stream_headers() -> None:
    import asyncio
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    import services.newsfeed.engine as eng
    from routers.newsfeed_router import _sse, router

    e = _engine("a")
    e.ingest(e.sources[0], ad.RawItem("1", FED, "u", None), 2_000_000_000.0, False, 20)
    eng._engine = e
    try:
        app = FastAPI()
        app.include_router(router)
        c = TestClient(app)
        assert c.get("/api/newsfeed/latest").json()["items"][0]["headline"] == FED
        assert c.get("/api/newsfeed/latest", params={"symbol": "USOIL.FOREX"}).json()["items"]
        assert c.get("/api/newsfeed/status").json()["running"] is False
        assert [r["id"] for r in c.get("/api/newsfeed/sources").json()["sources"]] == ["a"]

        async def first_event() -> str:
            gen = _sse(e)
            task = asyncio.ensure_future(gen.__anext__())
            await asyncio.sleep(0.01)
            e._publish({"type": "story", "story": {"id": "x"}})
            out = await asyncio.wait_for(task, 2)
            await gen.aclose()
            return out

        assert '"id": "x"' in asyncio.run(first_event())
    finally:
        eng._engine = None


@pytest.mark.parametrize("title,is_decision", [
    ("Nasdaq 100 beats chip index by 460 basis points as hyperscalers rally", False),
    ("Fed delivers 25 basis points cut, statement shows", True),
    ("ECB lowers deposit rate by 25 bps", True),
])
def test_basis_points_alone_is_not_rate_decision(title: str, is_decision: bool) -> None:
    assert (classify(title, "media").event_type == "cb_decision") is is_decision
