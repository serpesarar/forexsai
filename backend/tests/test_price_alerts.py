"""price_alert_service — tetik mantığı, doğrulama, plan alarmları ve atomik tek-tetik."""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from services import price_alert_service as pas

NOW = datetime(2026, 11, 4, 15, 0, tzinfo=timezone.utc)


def test_evaluate_above_below_and_missing_price():
    assert pas.evaluate({"kind": "above", "price": 100}, 100.0, NOW)
    assert not pas.evaluate({"kind": "above", "price": 100}, 99.9, NOW)
    assert pas.evaluate({"kind": "below", "price": 100}, 99.0, NOW)
    assert not pas.evaluate({"kind": "below", "price": 100}, None, NOW)


def test_evaluate_stop_target_direction_from_ref():
    # AL planı: giriş 100, stop 95 (altta), hedef 110 (üstte)
    assert pas.evaluate({"kind": "stop", "price": 95, "ref_price": 100}, 94.9, NOW)
    assert not pas.evaluate({"kind": "stop", "price": 95, "ref_price": 100}, 96, NOW)
    assert pas.evaluate({"kind": "target", "price": 110, "ref_price": 100}, 110.5, NOW)
    # SAT planı: stop üstte
    assert pas.evaluate({"kind": "stop", "price": 105, "ref_price": 100}, 105, NOW)
    assert not pas.evaluate({"kind": "stop", "price": 105, "ref_price": 100}, 101, NOW)


def test_evaluate_pct_and_time():
    a = {"kind": "pct_move", "pct": 1.0, "ref_price": 200}
    assert pas.evaluate(a, 202.0, NOW) and pas.evaluate(a, 198.0, NOW)
    assert not pas.evaluate(a, 201.0, NOW)
    t = {"kind": "time", "at_utc": (NOW - timedelta(seconds=1)).isoformat()}
    assert pas.evaluate(t, None, NOW)
    assert not pas.evaluate({"kind": "time", "at_utc": (NOW + timedelta(minutes=1)).isoformat()}, None, NOW)


def test_validate_rejects_bad_input_and_fills_ref():
    with pytest.raises(ValueError):
        pas.validate({"symbol": "NDX", "kind": "above"})
    with pytest.raises(ValueError):
        pas.validate({"symbol": "NDX", "kind": "nope", "price": 1})
    with pytest.raises(ValueError):
        pas.validate({"symbol": "NDX", "kind": "stop", "price": 100})          # ref yok
    row = pas.validate({"symbol": "NDX", "kind": "pct_move", "pct": 0.5}, current_price=20000)
    assert row["symbol"] == "NDX.INDX" and row["ref_price"] == 20000


def test_plan_alerts_geometry():
    rows = pas.plan_alerts("XAUUSD", "buy", 4000, 3990, 4020, horizon_min=60, now=NOW)
    kinds = [r["kind"] for r in rows]
    assert kinds == ["stop", "target", "time"]
    assert all(r["source"] == "plan" and r["ref_price"] == 4000 for r in rows)
    assert rows[2]["at_utc"].startswith("2026-11-04T16:00")
    with pytest.raises(ValueError):
        pas.plan_alerts("XAUUSD", "buy", 4000, 4010, 4020)                     # stop girişin üstünde


class _Q:
    """Proje sarmalayıcısının (database/supabase_client.TableQuery) taklidi: filtre önce, update dict döner."""

    def __init__(self, db):
        self.db, self.f = db, []

    def select(self, *_): return self
    def eq(self, k, v): self.f.append((k, v)); return self
    def or_(self, *_): return self
    def limit(self, *_): return self
    def _rows(self): return [r for r in self.db.rows if all(r.get(k) == v for k, v in self.f)]
    def execute(self): return {"data": [dict(r) for r in self._rows()], "error": None}

    def update(self, patch):
        rows = self._rows()
        for r in rows:
            r.update(patch)
        return {"data": [dict(r) for r in rows], "error": None}


class _DB:
    def __init__(self, rows): self.rows = rows
    def table(self, _): return _Q(self)


def test_run_once_triggers_once_and_skips_stale(monkeypatch):
    db = _DB([
        {"id": 1, "symbol": "NDX.INDX", "kind": "above", "price": 100, "status": "active",
         "one_shot": True, "notify_telegram": False},
        {"id": 2, "symbol": "XAUUSD", "kind": "below", "price": 1, "status": "active",
         "one_shot": True, "notify_telegram": False},
    ])
    monkeypatch.setattr(pas, "_db", lambda: db)
    monkeypatch.setattr(pas, "current_price", lambda s: 101.0 if s == "NDX.INDX" else None)   # XAU bayat
    r1 = asyncio.run(pas.run_once(NOW))
    assert r1["triggered"] == 1 and db.rows[0]["status"] == "triggered" and db.rows[0]["triggered_price"] == 101.0
    assert db.rows[1]["status"] == "active"
    r2 = asyncio.run(pas.run_once(NOW))                                        # ikinci tur: aynı alarm yeniden yok
    assert r2["triggered"] == 0


def test_claim_lost_to_other_backend(monkeypatch):
    db = _DB([{"id": 7, "symbol": "NDX.INDX", "kind": "above", "price": 100, "status": "triggered", "one_shot": True}])
    assert not pas._claim(db, db.rows[0], 101.0, NOW)                          # status artık active değil
