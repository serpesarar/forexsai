"""2026-10-08 decider değişiklikleri: kanıt kuralları (D4/D5), canlı izin listesi, seçim değeri,
ileri doğrulama. Çalıştır: cd claude_decider && python3 -m pytest test_evidence_rules.py -q"""
from __future__ import annotations

import importlib

import evidence_rules
import decide
import distill_journal as dj


def _open(direction: str) -> dict:
    return {"action": "OPEN", "direction": direction, "size_factor": 0.5, "reason": "test"}


def test_d4_blocks_ndx_buy_in_calm_vix_and_sets_cf():
    sit = {"vix": {"value": 15.2, "favored_ndx": "SELL", "fresh": True}, "primary_dir": "SELL"}
    dec, info = evidence_rules.apply("NDX.INDX", _open("BUY"), sit)
    assert dec["action"] == "WAIT" and dec["size_factor"] == 0.0 and info["kural"] == "D4_vix_ndx_buy"
    assert sit["primary_dir"] == "BUY"            # engellenen işlem karşı-olgu olarak notlanır


def test_d4_fail_open_and_other_cases():
    for vix in ({}, {"value": 19.0, "favored_ndx": "BUY", "fresh": True},
                {"value": 18.3, "favored_ndx": "SELL", "fresh": False}):
        dec, info = evidence_rules.apply("NDX.INDX", _open("BUY"), {"vix": vix})
        assert dec["action"] == "OPEN" and info is None
    dec, info = evidence_rules.apply("NDX.INDX", _open("SELL"), {"vix": {"favored_ndx": "SELL", "fresh": True}})
    assert dec["action"] == "OPEN" and info is None


def test_d5_blocks_usoil_sell_only():
    dec, info = evidence_rules.apply("USOIL.FOREX", _open("SELL"), {})
    assert dec["action"] == "WAIT" and info["kural"] == "D5_usoil_sell"
    dec, info = evidence_rules.apply("XAUUSD", _open("BUY"), {})
    assert dec["action"] == "OPEN" and info is None
    wait = {"action": "WAIT", "direction": None}
    assert evidence_rules.apply("USOIL.FOREX", wait, {}) == (wait, None)


def test_shadow_mode_does_not_change_decision(monkeypatch):
    monkeypatch.setenv("EVIDENCE_RULES_MODE", "shadow")
    mod = importlib.reload(evidence_rules)
    dec, info = mod.apply("USOIL.FOREX", _open("SELL"), {})
    assert dec["action"] == "OPEN" and info["would_block"] is True
    monkeypatch.delenv("EVIDENCE_RULES_MODE")
    importlib.reload(evidence_rules)


def test_live_allowlist():
    assert decide.live_eligible("XAUUSD", "BUY") == (True, "")
    assert decide.live_eligible("NDX.INDX", "SELL") == (True, "")
    ok, why = decide.live_eligible("USOIL.FOREX", "SELL")
    assert not ok and "İZİN LİSTESİ" in why
    assert not decide.live_eligible("XAUUSD", "SELL")[0]          # sert yasak önce gelir


def _row(ts: str, sym: str, act: str, d: str, pnl: float) -> dict:
    if act == "OPEN":
        return {"ts": ts, "symbol": sym, "decision": {"action": "OPEN", "direction": d},
                "outcome": "WIN" if pnl > 0 else "LOSS", "pnl_r": pnl, "outcome_at": ts}
    return {"ts": ts, "symbol": sym, "decision": {"action": "WAIT"}, "outcome": "WAIT",
            "counterfactual": {"dir": d}, "cf_outcome": "WIN" if pnl > 0 else "LOSS", "cf_pnl_r": pnl,
            "outcome_at": ts}


def test_selection_value_flags_harmful_direction():
    rows = []
    for i in range(80):
        ts = f"2026-08-{1 + i // 8:02d}T{(i % 8) * 3:02d}:00:00+00:00"
        rows.append(_row(ts, "NDX.INDX", "OPEN", "BUY", -1.0 if i % 3 else 0.67))   # açtıkları kötü
        rows.append(_row(ts.replace(":00:00+", ":30:00+"), "NDX.INDX", "WAIT", "BUY", 0.67 if i % 3 else -1.0))
    lines = dj.selection_value(rows)
    assert any("NDX.INDX BUY" in ln and "ZARAR" in ln for ln in lines)


def test_forward_check_rejects_flip():
    g = [{"pnl_r": 0.67 if i % 2 else -1.0, "live": {"adx": float(i)}, "decision": {}} for i in range(100)]
    for r in g[60:]:                      # ileri dönemde yüksek ADX kaybettiriyor
        r["pnl_r"] = -1.0 if r["live"]["adx"] >= 80 else 0.67
    ok, diff = dj._forward_ok(g, "adx", ">=", 80.0)
    assert not ok and diff < 0
