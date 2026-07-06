"""Debate engine, LLM router, and auto-runner scheduling."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import services.llm_router as lr  # noqa: E402
import services.bias_debate_engine as engine  # noqa: E402
import services.bias_auto_runner as runner  # noqa: E402


# ── llm_router ────────────────────────────────────────────────────────────────
def test_extract_json_plain_and_wrapped():
    assert lr.extract_json('{"a":1}') == {"a": 1}
    assert lr.extract_json('bla bla {"a": 2} trailing') == {"a": 2}
    assert lr.extract_json("no json here") is None


def test_provider_routing_order(monkeypatch):
    monkeypatch.setattr(lr.settings, "kimi_api_key", "K")
    monkeypatch.setattr(lr.settings, "deepseek_api_key", "D")
    imp = [c[0] for c in lr._provider_for("important")]
    nor = [c[0] for c in lr._provider_for("normal")]
    assert imp[0] == "kimi"        # important → Kimi first
    assert nor[0] == "deepseek"    # normal → DeepSeek first


def test_provider_falls_back_when_key_missing(monkeypatch):
    monkeypatch.setattr(lr.settings, "kimi_api_key", None)
    monkeypatch.setattr(lr.settings, "deepseek_api_key", "D")
    # important prefers Kimi but has no key → only DeepSeek remains
    assert [c[0] for c in lr._provider_for("important")] == ["deepseek"]


@pytest.mark.asyncio
async def test_chat_raises_without_keys(monkeypatch):
    monkeypatch.setattr(lr.settings, "kimi_api_key", None)
    monkeypatch.setattr(lr.settings, "deepseek_api_key", None)
    with pytest.raises(lr.LLMUnavailable):
        await lr.chat("sys", "user")


# ── debate engine ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_run_debate_produces_verdict(monkeypatch):
    async def fake_ctx(symbol, now):
        return {"session": {"ny_time": "2026-07-06T08:00:00-04:00",
                            "current_session": "us_premarket",
                            "minutes_to_us_open": 90, "session_overlap": False,
                            "is_half_day": False, "is_holiday": False,
                            "london_session_direction": "up",
                            "asia_overnight_change": None, "us_premarket_change": None},
                "price": 20100, "prior_day": None, "recent_range": None}
    monkeypatch.setattr(engine, "_gather_context", fake_ctx)

    async def fake_chat(system, user, importance="normal", json_mode=False, **k):
        if json_mode:   # CIO
            return ('{"nasdaq_daily_bias":"bullish","confidence":71,'
                    '"main_support":20000,"main_resistance":20500,'
                    '"debate_winner":"bull","reason_summary":"ok"}'), "kimi"
        return f"note from importance={importance}", ("kimi" if importance == "important" else "deepseek")
    monkeypatch.setattr(engine.llm_router, "chat", fake_chat)

    verdict = await engine.run_debate(now_utc=datetime(2026, 7, 6, 12, tzinfo=timezone.utc))
    assert verdict["nasdaq_daily_bias"] == "bullish"
    assert verdict["confidence"] == 71
    assert verdict["_debate"]["cio_provider"] == "kimi"
    assert "bull_case" in verdict["_debate"]


@pytest.mark.asyncio
async def test_run_debate_rejects_non_nasdaq():
    with pytest.raises(ValueError):
        await engine.run_debate(symbol="XAUUSD")


# ── QQQ / macro side feeds ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_qqq_premarket_computes_change(monkeypatch):
    import services.data_fetcher as df

    async def price(sym):
        return 488.0
    async def daily(sym, tf, limit=5):
        # [-2] is yesterday's close (480); [-1] is today's still-forming bar.
        return [{"close": 460}, {"close": 480}, {"close": 999}]
    monkeypatch.setattr(df, "fetch_latest_price", price)
    monkeypatch.setattr(df, "fetch_ohlc_data", daily)
    q = await engine._qqq_premarket()
    assert q["price"] == 488.0
    assert q["prior_close"] == 480
    assert q["premarket_change_pct"] == pytest.approx((488 - 480) / 480 * 100, abs=0.01)


@pytest.mark.asyncio
async def test_qqq_premarket_nullable_without_data(monkeypatch):
    import services.data_fetcher as df

    async def price(sym):
        return None
    async def daily(sym, tf, limit=5):
        return []
    monkeypatch.setattr(df, "fetch_latest_price", price)
    monkeypatch.setattr(df, "fetch_ohlc_data", daily)
    q = await engine._qqq_premarket()
    assert q["price"] is None and q["premarket_change_pct"] is None


def test_macro_gauges(monkeypatch):
    import services.macro_data_service as mds
    monkeypatch.setattr(mds, "get_macro_dict", lambda: {
        "dxy": {"price": 104.2, "change_1h_pct": -0.1},
        "vix": {"price": 15.3, "change_1h_pct": 2.0},
        "us10y": {"price": 4.3, "change_1h_pct": 0.5}})
    g = engine._macro_gauges()
    assert g["vix"]["price"] == 15.3 and g["dxy"]["chg_1h"] == -0.1


def test_context_block_renders_qqq_and_macro():
    market = {
        "session": {"ny_time": "2026-07-06T08:00:00-04:00", "current_session": "us_premarket",
                    "minutes_to_us_open": 90, "session_overlap": False,
                    "is_half_day": False, "is_holiday": False,
                    "london_session_direction": "up", "asia_overnight_change": None,
                    "us_premarket_change": 0.4},
        "price": 20100, "prior_day": None, "recent_range": None,
        "qqq": {"price": 488.0, "premarket_change_pct": 0.4, "prior_close": 486},
        "macro": {"dxy": {"price": 104.2, "chg_1h": -0.1}, "vix": {"price": 15.3, "chg_1h": 2.0},
                  "us10y": {"price": 4.3, "chg_1h": 0.5}}}
    block = engine._context_block(market)
    assert "QQQ" in block and "488.0" in block
    assert "Macro" in block and "VIX 15.3" in block


@pytest.mark.asyncio
async def test_run_debate_aborts_on_bad_cio(monkeypatch):
    async def fake_ctx(symbol, now):
        return {"session": {"ny_time": "2026-07-06T08:00:00-04:00",
                            "current_session": "us_premarket", "minutes_to_us_open": 90,
                            "session_overlap": False, "is_half_day": False,
                            "is_holiday": False, "london_session_direction": None,
                            "asia_overnight_change": None, "us_premarket_change": None},
                "price": None, "prior_day": None, "recent_range": None}
    monkeypatch.setattr(engine, "_gather_context", fake_ctx)

    async def fake_chat(system, user, importance="normal", json_mode=False, **k):
        return ("garbage no json" if json_mode else "note"), "kimi"
    monkeypatch.setattr(engine.llm_router, "chat", fake_chat)

    with pytest.raises(lr.LLMUnavailable):
        await engine.run_debate(now_utc=datetime(2026, 7, 6, 12, tzinfo=timezone.utc))


# ── auto-runner ───────────────────────────────────────────────────────────────
def test_parse_windows():
    ws = runner._parse_windows("08:00=0800_main,09:45=0945_confirm")
    assert ws == [(480, "0800_main"), (585, "0945_confirm")]
    assert runner._parse_windows("garbage") == []


@pytest.mark.asyncio
async def test_tick_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(runner.settings, "bias_auto_run_enabled", False)
    assert await runner.tick(datetime(2026, 7, 6, 12, tzinfo=timezone.utc)) is None


@pytest.mark.asyncio
async def test_tick_fires_window(monkeypatch):
    runner._ran.clear(); runner._filled.clear()
    monkeypatch.setattr(runner.settings, "bias_auto_run_enabled", True)
    monkeypatch.setattr(runner.settings, "bias_run_windows_et", "08:00=0800_main")
    monkeypatch.setattr(runner.settings, "bias_fill_time_et", "16:15")
    monkeypatch.setattr(runner.bts, "already_logged", lambda d, l: False)

    calls = {}

    async def fake_debate(now_utc=None):
        calls["debate"] = True
        return {"nasdaq_daily_bias": "bearish", "confidence": 66}

    async def fake_record(payload, run_label, run_ts=None):
        calls["record"] = run_label
        return {"predicted_bias": payload["nasdaq_daily_bias"]}

    monkeypatch.setattr("services.bias_debate_engine.run_debate", fake_debate)
    monkeypatch.setattr(runner.bts, "record_run", fake_record)

    # 2026-07-06 08:01 EDT = 12:01 UTC → inside the 08:00 window band
    out = await runner.tick(datetime(2026, 7, 6, 12, 1, tzinfo=timezone.utc))
    assert calls.get("debate") is True
    assert calls.get("record") == "0800_main"
    assert "0800_main" in out

    # Second tick same window → deduped (in-memory guard), no new debate
    calls.clear()
    await runner.tick(datetime(2026, 7, 6, 12, 2, tzinfo=timezone.utc))
    assert "debate" not in calls


@pytest.mark.asyncio
async def test_tick_skips_holiday(monkeypatch):
    runner._ran.clear()
    monkeypatch.setattr(runner.settings, "bias_auto_run_enabled", True)
    monkeypatch.setattr(runner.settings, "bias_run_windows_et", "08:00=0800_main")
    # 2026-07-03 is a holiday → no run even at the window
    out = await runner.tick(datetime(2026, 7, 3, 12, 1, tzinfo=timezone.utc))
    assert out is None
