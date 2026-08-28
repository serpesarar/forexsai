"""Bot işleminin 'hangi kurala göre açıldığı' — services/evolution_remote.py.

İki katman test edilir:
  1. strategy_for_magic: magic numarasından strateji ailesi (%100 kapsam —
     bot_trades.magic her zaman dolu; 479/479 gerçek işlemde doğrulandı).
  2. _fingerprints_by_ticket + get_bot_symbol_history: momentum/SR için
     entry_fingerprints.jsonl'den gelen zengin bağlamın (voters, session,
     backend confidence) satırlara JOIN edilmesi — yalnız best-effort,
     eksikse None (uydurulmaz).
"""
from __future__ import annotations

import pytest

from services import evolution_remote as er


# ── strategy_for_magic ───────────────────────────────────────────────────────

def test_base_magic_is_momentum_sr():
    s = er.strategy_for_magic(er.BOT_MAGIC_BASE)
    assert s["code"] == "momentum_sr"


@pytest.mark.parametrize("offset,expected_code", [
    (1, "channel_reversion"),
    (2, "vix_regime"),
    (3, "reflex"),
    (4, "daycombo"),
    (5, "usoil_breakout"),
    (6, "reentry"),
])
def test_known_offsets_map_to_documented_strategies(offset, expected_code):
    s = er.strategy_for_magic(er.BOT_MAGIC_BASE + offset)
    assert s["code"] == expected_code
    assert s["label"] and s["note"]


def test_unknown_magic_is_labeled_not_crashed():
    assert er.strategy_for_magic(999999999)["code"] == "bilinmiyor"


def test_none_magic_is_labeled_not_crashed():
    assert er.strategy_for_magic(None)["code"] == "bilinmiyor"


def test_zero_magic_is_unknown():
    """DB'de gözlenen gerçek durum: bazı eski/manuel işlemler magic=0 taşır."""
    assert er.strategy_for_magic(0)["code"] == "bilinmiyor"


def test_env_override_shifts_base(monkeypatch):
    """BOT_MAGIC_BASE farklı bir kutuda/konfigde ezilebilmeli."""
    monkeypatch.setattr(er, "BOT_MAGIC_BASE", 1000)
    assert er.strategy_for_magic(1002)["code"] == "vix_regime"


# ── _fingerprints_by_ticket + JOIN ──────────────────────────────────────────

class _FakeFPQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *a):
        return self

    def eq(self, *a):
        return self

    def gte(self, *a):
        return self

    def order(self, *a, **k):
        return self

    def range(self, start, end):
        return self

    def execute(self):
        return {"data": self._rows if self._rows is not None else []}


def _fp_row(ticket, **extra):
    raw = {"session": "NY", "mom_stretch": 1.8, "mom_threshold": 1.5,
           "backend_action": "OPEN", "backend_conf": 72.0, "priority": 0.6,
           "lot_mult": 1.0}
    raw.update(extra.pop("raw_extra", {}))
    return {
        "ticket": ticket, "scope": "NDX.INDX:momentum", "direction": "BUY",
        "entry": 100.0, "tp": 102.0, "sl": 99.0, "lot": 5.0, "rr": 2.0,
        "entry_type": "market", "tp_source": "backend",
        "voters": ["mom_cont"], "raw": raw, **extra,
    }


def test_fingerprints_by_ticket_indexes_by_ticket(monkeypatch):
    fp_rows = [_fp_row(555)]

    class _Client:
        def table(self, name):
            assert name == "bot_entry_fingerprints"
            return _FakeFPQuery(fp_rows)

    monkeypatch.setattr(er, "_client", lambda: _Client())
    out = er._fingerprints_by_ticket(30, host="mt5_box")
    assert 555 in out
    fp = out[555]
    assert fp["voters"] == ["mom_cont"]
    assert fp["session"] == "NY"
    assert fp["backend_confidence"] == 72.0
    assert fp["mom_stretch"] == 1.8 and fp["mom_threshold"] == 1.5


def test_fingerprints_by_ticket_fail_soft_on_db_error(monkeypatch):
    """Fingerprint zenginleştirmesi opsiyoneldir — DB hatası panelin geri
    kalanını düşürmemeli."""
    class _Client:
        def table(self, name):
            raise RuntimeError("supabase kapalı")

    monkeypatch.setattr(er, "_client", lambda: _Client())
    out = er._fingerprints_by_ticket(30, host="mt5_box")
    assert out == {}


def test_get_bot_symbol_history_attaches_strategy_and_fingerprint(monkeypatch):
    """Uçtan uca: bot_trades satırı → magic'ten strateji + ticket eşleşen
    fingerprint JOIN'i, eşleşmeyen satırda fingerprint=None (uydurma yok)."""
    trade_with_fp = {
        "ticket": 9001, "direction": "BUY", "volume": 5.0,
        "open_time": "2026-08-28T10:00:00+00:00", "open_price": 100.0,
        "close_time": "2026-08-28T11:00:00+00:00", "close_price": 102.0,
        "sl": 99.0, "tp": 102.0, "profit": 400.0, "commission": 0.0, "swap": 0.0,
        "comment": "[tp 102.0]", "magic": er.BOT_MAGIC_BASE,
        "raw": {"position_id": 555, "order": 1, "reason": er._MT5_REASON_TP},
    }
    trade_without_fp = {
        "ticket": 9002, "direction": "SELL", "volume": 5.0,
        "open_time": "2026-08-28T09:00:00+00:00", "open_price": 200.0,
        "close_time": "2026-08-28T09:30:00+00:00", "close_price": 205.0,
        "sl": 195.0, "tp": 190.0, "profit": -250.0, "commission": 0.0, "swap": 0.0,
        "comment": "[sl 205.0]", "magic": er.BOT_MAGIC_BASE + 2,  # VIXREG
        "raw": {"position_id": 556, "order": 2, "reason": er._MT5_REASON_SL},
    }

    def fake_fetch_paged(table, *a, **k):
        if table == "bot_trades":
            return [trade_with_fp, trade_without_fp]
        return []

    monkeypatch.setattr(er, "_fetch_paged", fake_fetch_paged)
    monkeypatch.setattr(er, "_fingerprints_by_ticket",
                        lambda days, host=er.DEFAULT_HOST: {555: {
                            "scope": "NDX.INDX:momentum", "voters": ["mom_cont"],
                            "session": "NY", "entry_type": "market",
                            "tp_source": "backend", "rr_planned": 2.0,
                            "mom_stretch": 1.8, "mom_threshold": 1.5,
                            "backend_action": "OPEN", "backend_confidence": 72.0,
                            "priority": 0.6, "lot_mult": 1.0,
                        }})

    out = er.get_bot_symbol_history("NAS100", 30)
    by_ticket = {d["ticket"]: d for d in out["decisions"]}

    fp_trade = by_ticket[9001]
    assert fp_trade["strategy"]["code"] == "momentum_sr"
    assert fp_trade["fingerprint"] is not None
    assert fp_trade["fingerprint"]["voters"] == ["mom_cont"]

    no_fp_trade = by_ticket[9002]
    assert no_fp_trade["strategy"]["code"] == "vix_regime"
    assert no_fp_trade["fingerprint"] is None, "eşleşmeyen işlemde fingerprint uydurulmamalı"


# ── CSV dışa aktarım ─────────────────────────────────────────────────────────

def test_export_csv_has_header_and_rule_columns(monkeypatch):
    trade = {
        "ticket": 9001, "symbol": "NAS100", "direction": "BUY", "volume": 5.0,
        "open_time": "2026-08-28T10:00:00+00:00", "open_price": 100.0,
        "close_time": "2026-08-28T11:00:00+00:00", "close_price": 102.0,
        "sl": 99.0, "tp": 102.0, "profit": 400.0, "commission": 0.0, "swap": 0.0,
        "comment": "[tp 102.0]", "magic": er.BOT_MAGIC_BASE,
        "raw": {"position_id": 555, "order": 1, "reason": er._MT5_REASON_TP},
    }
    monkeypatch.setattr(er, "_fetch_paged", lambda table, *a, **k: [trade] if table == "bot_trades" else [])
    monkeypatch.setattr(er, "_fingerprints_by_ticket", lambda days, host=er.DEFAULT_HOST: {})

    csv_text = er.export_bot_trades_csv(symbol="NAS100", start="2026-08-01", end="2026-08-28")
    lines = csv_text.splitlines()
    header = lines[0].split(",")
    assert "strateji_kodu" in header and "strateji_adi" in header
    assert "acilis_fiyati" in header and "hedef_tp" in header and "stop_sl" in header
    assert "net_usd" in header and "r_multiple" in header
    assert "9001" in lines[1] and "momentum_sr" in lines[1]


def test_export_csv_filters_are_forwarded(monkeypatch):
    captured = {}

    def fake_fetch(table, *a, **k):
        if table == "bot_trades":
            captured.update(k)
        return []

    monkeypatch.setattr(er, "_fetch_paged", fake_fetch)
    monkeypatch.setattr(er, "_fingerprints_by_ticket", lambda days, host=er.DEFAULT_HOST: {})

    er.export_bot_trades_csv(symbol="XAUUSD", start="2026-08-01", end="2026-08-15")
    assert captured.get("eq__symbol") == "XAUUSD"
    assert captured.get("gte__close_time") == "2026-08-01"
    assert captured.get("lte__close_time") == "2026-08-15T23:59:59"


def test_export_csv_without_symbol_covers_all(monkeypatch):
    captured = {}

    def fake_fetch(table, *a, **k):
        if table == "bot_trades":
            captured.update(k)
        return []

    monkeypatch.setattr(er, "_fetch_paged", fake_fetch)
    monkeypatch.setattr(er, "_fingerprints_by_ticket", lambda days, host=er.DEFAULT_HOST: {})

    er.export_bot_trades_csv(symbol=None, start=None, end=None)
    assert "eq__symbol" not in captured
    assert "gte__close_time" not in captured
