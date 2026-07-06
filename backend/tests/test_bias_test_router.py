"""Bias-test harness — service core + HTTP router (delegates to service)."""
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import services.bias_test_service as bts  # noqa: E402
import routers.bias_test_router as btr  # noqa: E402


# ── Fake Supabase (list-backed, dict-return API) ──────────────────────────────
class _T:
    def __init__(self, rows):
        self._rows = rows
        self._f = {}

    def insert(self, data):
        data = {**data, "id": len(self._rows) + 1}
        self._rows.append(data)
        return {"data": [data], "error": None}

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._f[col] = val
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def execute(self):
        out = [r for r in self._rows if all(r.get(c) == v for c, v in self._f.items())]
        return {"data": out, "error": None}

    def update(self, data):
        for r in self._rows:
            if all(r.get(c) == v for c, v in self._f.items()):
                r.update(data)
        return {"data": [], "error": None}


class _Client:
    def __init__(self):
        self.rows = []

    def table(self, _name):
        return _T(self.rows)


@pytest.fixture
def store(monkeypatch):
    client = _Client()
    monkeypatch.setattr(bts, "_client", lambda: client)

    async def fake_enrich(ts, ctx=None):
        return bts.sc.get_session_context(ts)   # deterministic, no price feed
    monkeypatch.setattr(bts.sc, "enrich_price_context", fake_enrich)
    return client


@pytest.fixture
def api(store):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(btr.router)
    return TestClient(app), store


# ── Pure grading helpers (now in the service) ─────────────────────────────────
def test_direction_from_pct():
    assert bts.direction_from_pct(0.5) == "positive"
    assert bts.direction_from_pct(-0.5) == "negative"
    assert bts.direction_from_pct(0.05) == "flat"
    assert bts.direction_from_pct(None) is None


def test_predicted_matches_actual():
    assert bts.predicted_matches_actual("bullish", "positive") is True
    assert bts.predicted_matches_actual("bearish", "positive") is False
    assert bts.predicted_matches_actual("choppy", "flat") is True
    assert bts.predicted_matches_actual("bullish", None) is None


# ── /log ──────────────────────────────────────────────────────────────────────
def test_log_records_session_context(api):
    client, s = api
    r = client.post("/api/bias-test/log", json={
        "run_label": "0945_confirm",
        "run_timestamp_utc": "2026-07-06T13:30:00Z",   # 09:30 EDT
        "nasdaq_daily_bias": "bullish", "confidence": 72,
        "main_support": 20000, "main_resistance": 20500})
    assert r.status_code == 200
    assert r.json()["current_session"] == "us_regular"
    assert s.rows[0]["session_overlap"] is True
    assert s.rows[0]["ny_date"] == "2026-07-06"


def test_log_invalid_payload_400(api):
    client, _ = api
    r = client.post("/api/bias-test/log", json={"run_label": "x", "confidence": 50})
    assert r.status_code == 400


# ── already_logged idempotency guard ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_already_logged(store):
    from datetime import datetime, timezone
    await bts.record_run({"nasdaq_daily_bias": "bullish", "confidence": 70},
                         "0800_main",
                         datetime(2026, 7, 6, 13, 30, tzinfo=timezone.utc))
    assert bts.already_logged("2026-07-06", "0800_main") is True
    assert bts.already_logged("2026-07-06", "0945_confirm") is False


# ── fill-outcomes + report end to end ─────────────────────────────────────────
def test_fill_and_report(api, monkeypatch):
    client, s = api
    for label, bias in [("0800_main", "bearish"), ("0945_confirm", "bullish")]:
        client.post("/api/bias-test/log", json={
            "run_label": label, "run_timestamp_utc": "2026-07-06T13:30:00Z",
            "nasdaq_daily_bias": bias, "confidence": 80,
            "main_support": 20000, "main_resistance": 20500})

    async def fake_daily(symbol, timeframe, limit=60):
        return [{"timestamp": "2026-07-06T00:00:00", "open": 20000, "close": 20200,
                 "high": 20250, "low": 19990}]
    monkeypatch.setattr("services.data_fetcher.fetch_ohlc_data", fake_daily)

    r = client.post("/api/bias-test/fill-outcomes?ny_date=2026-07-06")
    assert r.status_code == 200 and r.json()["rows_updated"] == 2
    assert r.json()["actual_close_direction"] == "positive"

    bullish = next(x for x in s.rows if x["predicted_bias"] == "bullish")
    assert bullish["was_correct"] is True
    assert bullish["invalid_if_triggered"] is True   # low 19990 < support 20000

    rep = client.get("/api/bias-test/accuracy-report").json()
    assert rep["overall"]["n"] == 2 and rep["overall"]["correct"] == 1
    assert rep["by_run_label"]["0945_confirm"]["accuracy_pct"] == 100.0


def test_fill_no_candle_404(api, monkeypatch):
    client, _ = api

    async def none_daily(symbol, timeframe, limit=60):
        return []
    monkeypatch.setattr("services.data_fetcher.fetch_ohlc_data", none_daily)
    assert client.post("/api/bias-test/fill-outcomes?ny_date=2026-07-06").status_code == 404


# ── lab UI + routing-status ───────────────────────────────────────────────────
def test_lab_serves_html(api):
    client, _ = api
    r = client.get("/api/bias-test/lab")
    assert r.status_code == 200 and "Neural Bias Engine" in r.text


def test_routing_status(api):
    client, _ = api
    r = client.get("/api/bias-test/routing-status")
    assert r.status_code == 200
    assert "important" in r.json() and "normal" in r.json()
