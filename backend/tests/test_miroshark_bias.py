"""Stage 2.6 + Stage 3.6 — MiroShark daily-bias bridge & alignment rules.

Covers:
  * HMAC signature verification (valid / invalid / missing)
  * CIO payload normalisation (flat, enveloped, invalid → ValueError)
  * UPSERT idempotency (same day twice → one row) via an in-memory fake client
  * /webhook (401 / 400 / 200) and /current-bias endpoints
  * compute_alignment rules (bullish/bearish/choppy/neutral/invalidated/no_bias)
  * check_macro_bias_alignment NASDAQ-only scope guard
  * intraday invalidation (support/resistance breach)
"""
import hashlib
import hmac
import json
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services import daily_bias_service as bias_svc  # noqa: E402


# ── In-memory fake Supabase client (matches the real dict-return REST API) ─────
class _FakeTable:
    def __init__(self, store, name):
        self._store = store
        self._name = name
        self._filters = {}

    # write
    def upsert(self, data, on_conflict=""):
        key = (data.get("bias_date"), data.get("symbol"))
        rows = self._store.setdefault(self._name, {})
        rows[key] = {**rows.get(key, {}), **data}   # merge-duplicates semantics
        return {"data": [rows[key]], "error": None}

    # read chain
    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        self._filters[col] = val
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def execute(self):
        rows = list(self._store.get(self._name, {}).values())
        for col, val in self._filters.items():
            rows = [r for r in rows if r.get(col) == val]
        return {"data": rows, "error": None}

    def update(self, data):
        rows = self._store.get(self._name, {})
        n = 0
        for key, row in rows.items():
            if all(row.get(c) == v for c, v in self._filters.items()):
                row.update(data)
                n += 1
        return {"data": [], "error": None, "count": n}


class _FakeClient:
    def __init__(self):
        self.store = {}

    def table(self, name):
        return _FakeTable(self.store, name)


@pytest.fixture
def fake_db(monkeypatch):
    client = _FakeClient()
    monkeypatch.setattr(bias_svc, "_client", lambda: client)
    bias_svc._clear_cache()
    yield client
    bias_svc._clear_cache()


# ── Signature verification ────────────────────────────────────────────────────
def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_signature_valid_and_invalid():
    from routers.miroshark_router import verify_signature
    body = b'{"nasdaq_daily_bias":"bullish","confidence":70}'
    secret = "topsecret"
    assert verify_signature(body, _sign(body, secret), secret) is True
    assert verify_signature(body, "sha256=deadbeef", secret) is False
    assert verify_signature(body, None, secret) is False
    assert verify_signature(body, _sign(body, "wrong"), secret) is False


# ── Payload normalisation ─────────────────────────────────────────────────────
def test_normalize_flat_payload():
    row = bias_svc.normalize_cio_payload({
        "nasdaq_daily_bias": "Bullish", "confidence": 72,
        "main_support": "20150", "trade_mode": "buy_dips_only",
        "invalid_if": "break premarket low",
    })
    assert row["nasdaq_daily_bias"] == "bullish"      # lowercased
    assert row["confidence"] == 72.0
    assert row["main_support"] == 20150.0             # coerced to float
    assert row["raw_payload"]["trade_mode"] == "buy_dips_only"


def test_normalize_enveloped_and_aliases():
    row = bias_svc.normalize_cio_payload({
        "cio_final": {"bias": "bearish", "conviction": 88, "resistance": 20500}
    })
    assert row["nasdaq_daily_bias"] == "bearish"
    assert row["confidence"] == 88.0
    assert row["main_resistance"] == 20500.0


def test_normalize_confidence_clamped():
    assert bias_svc.normalize_cio_payload(
        {"bias": "neutral", "confidence": 250})["confidence"] == 100.0


def test_normalize_invalid_bias_raises():
    with pytest.raises(ValueError):
        bias_svc.normalize_cio_payload({"confidence": 50})       # no bias
    with pytest.raises(ValueError):
        bias_svc.normalize_cio_payload({"nasdaq_daily_bias": "moon"})


# ── UPSERT idempotency ────────────────────────────────────────────────────────
def test_upsert_idempotent_same_day(fake_db):
    p1 = {"nasdaq_daily_bias": "bullish", "confidence": 60}
    p2 = {"nasdaq_daily_bias": "bullish", "confidence": 75}   # revised same day
    assert bias_svc.upsert_bias(p1)["ok"] is True
    assert bias_svc.upsert_bias(p2)["ok"] is True
    rows = fake_db.store.get("daily_bias", {})
    assert len(rows) == 1                                     # single row
    assert list(rows.values())[0]["confidence"] == 75.0      # latest wins


def test_get_current_bias_none_when_empty(fake_db):
    assert bias_svc.get_current_bias("NDX.INDX") is None


def test_get_current_bias_roundtrip(fake_db):
    bias_svc.upsert_bias({"nasdaq_daily_bias": "bearish", "confidence": 80})
    bias = bias_svc.get_current_bias("NDX.INDX", use_cache=False)
    assert bias and bias["nasdaq_daily_bias"] == "bearish"


# ── Endpoints ─────────────────────────────────────────────────────────────────
@pytest.fixture
def api(monkeypatch, fake_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routers import miroshark_router
    monkeypatch.setattr(miroshark_router.settings,
                        "miroshark_webhook_secret", "testsecret")
    app = FastAPI()
    app.include_router(miroshark_router.router)
    return TestClient(app)


def test_webhook_valid_signature(api):
    body = json.dumps({"nasdaq_daily_bias": "bullish", "confidence": 70}).encode()
    r = api.post("/api/miroshark/webhook", content=body,
                 headers={"X-MiroShark-Signature": _sign(body, "testsecret"),
                          "Content-Type": "application/json"})
    assert r.status_code == 200
    assert r.json()["nasdaq_daily_bias"] == "bullish"


def test_webhook_bad_signature_401(api):
    body = json.dumps({"nasdaq_daily_bias": "bullish", "confidence": 70}).encode()
    r = api.post("/api/miroshark/webhook", content=body,
                 headers={"X-MiroShark-Signature": "sha256=bad",
                          "Content-Type": "application/json"})
    assert r.status_code == 401


def test_webhook_bad_json_400(api):
    body = b"not-json{"
    r = api.post("/api/miroshark/webhook", content=body,
                 headers={"X-MiroShark-Signature": _sign(body, "testsecret"),
                          "Content-Type": "application/json"})
    assert r.status_code == 400


def test_manual_bias_and_current(api):
    r = api.post("/api/miroshark/manual-bias",
                 json={"nasdaq_daily_bias": "choppy", "confidence": 40})
    assert r.status_code == 200
    r2 = api.get("/api/miroshark/current-bias?symbol=NDX.INDX")
    assert r2.json()["status"] == "ok"
    assert r2.json()["bias"]["nasdaq_daily_bias"] == "choppy"


def test_current_bias_absent(api):
    r = api.get("/api/miroshark/current-bias?symbol=NDX.INDX")
    assert r.json()["status"] == "no_bias_today"
    assert r.json()["bias"] is None


# ── Alignment rules (pure) ────────────────────────────────────────────────────
def _bias(b, conf, **extra):
    return {"nasdaq_daily_bias": b, "confidence": conf, "is_invalidated": False, **extra}


def test_align_bullish_buy_bonus():
    r = bias_svc.compute_alignment("BUY", _bias("bullish", 60))
    assert r["adjustment"] == pytest.approx(12.0)     # min(15, 60*0.2)
    assert r["aligned"] is True and r["soft_veto"] is False


def test_align_bullish_buy_bonus_capped():
    r = bias_svc.compute_alignment("BUY", _bias("bullish", 95))
    assert r["adjustment"] == 15.0                     # capped


def test_align_bullish_sell_penalty_no_softveto():
    r = bias_svc.compute_alignment("SELL", _bias("bullish", 60))
    assert r["adjustment"] == pytest.approx(-15.0)     # min(20, 60*0.25)
    assert r["soft_veto"] is False


def test_align_bullish_sell_softveto_high_conf():
    r = bias_svc.compute_alignment("SELL", _bias("bullish", 80))
    assert r["soft_veto"] is True                      # conf > 75 opposing
    assert r["reason"] == "macro_bias_opposition"


def test_align_bearish_buy_softveto():
    r = bias_svc.compute_alignment("BUY", _bias("bearish", 90))
    assert r["adjustment"] < 0 and r["soft_veto"] is True


def test_align_choppy_penalises_all():
    assert bias_svc.compute_alignment("BUY", _bias("choppy", 50))["adjustment"] == -10.0
    assert bias_svc.compute_alignment("SELL", _bias("choppy", 50))["adjustment"] == -10.0


def test_align_choppy_wait_and_see_harder():
    r = bias_svc.compute_alignment("BUY", _bias("choppy", 50, trade_mode="wait_and_see"))
    assert r["adjustment"] == -20.0


def test_align_neutral_no_effect():
    assert bias_svc.compute_alignment("BUY", _bias("neutral", 90))["adjustment"] == 0.0


def test_align_no_bias_and_invalidated():
    assert bias_svc.compute_alignment("BUY", None)["state"] == "no_bias"
    inv = _bias("bullish", 90); inv["is_invalidated"] = True
    r = bias_svc.compute_alignment("BUY", inv)
    assert r["state"] == "invalidated" and r["adjustment"] == 0.0


def test_check_macro_alignment_scope_guard(fake_db):
    # Non-NASDAQ symbols are always a neutral no-op, even with a bias present.
    bias_svc.upsert_bias({"nasdaq_daily_bias": "bullish", "confidence": 90})
    assert bias_svc.check_macro_bias_alignment("SELL", "XAUUSD")["state"] == "not_nasdaq"
    assert bias_svc.check_macro_bias_alignment("SELL", "XAUUSD")["adjustment"] == 0.0
    # NASDAQ picks up the stored bias.
    assert bias_svc.check_macro_bias_alignment("BUY", "NDX.INDX")["aligned"] is True


# ── Intraday invalidation ─────────────────────────────────────────────────────
def test_invalidation_bullish_breaks_support(fake_db):
    bias_svc.upsert_bias({"nasdaq_daily_bias": "bullish", "confidence": 70,
                          "main_support": 20000, "main_resistance": 20500})
    reason = bias_svc.check_and_maybe_invalidate("NDX.INDX", 19950)
    assert reason is not None
    bias = bias_svc.get_current_bias("NDX.INDX", use_cache=False)
    assert bias["is_invalidated"] is True


def test_invalidation_not_triggered_within_range(fake_db):
    bias_svc.upsert_bias({"nasdaq_daily_bias": "bullish", "confidence": 70,
                          "main_support": 20000, "main_resistance": 20500})
    assert bias_svc.check_and_maybe_invalidate("NDX.INDX", 20200) is None


def test_invalidation_ignores_non_nasdaq(fake_db):
    assert bias_svc.check_and_maybe_invalidate("XAUUSD", 1) is None
