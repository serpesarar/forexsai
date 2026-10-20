"""Fakeout kapısı blok kapsamı: NDX'te blok (default), diğer sembollerde gölge, FAKEOUT_GATE_BLOCK=0 → her yerde gölge."""
import asyncio

import pytest

from services import signal_gates as sg


def _fake_result(direction: str = "down") -> dict:
    return {"status": "assessed", "breakout": {"direction": direction, "level_kind": "support", "level_price": 100.0},
            "fake_probability": 85, "matched_rules": [], "breakout_score": 0, "detector": {"call": "fake"}}


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    async def assess(symbol):
        return _fake_result()
    import services.fakeout_service as fs
    monkeypatch.setattr(fs, "assess_symbol", assess)
    monkeypatch.delenv("FAKEOUT_GATE_BLOCK", raising=False)
    monkeypatch.delenv("FAKEOUT_GATE_BLOCK_SYMBOLS", raising=False)
    monkeypatch.delenv("FAKEOUT_GATE_ENABLED", raising=False)


def _run(symbol: str, direction: str = "SELL"):
    return asyncio.run(sg.fakeout_gate(symbol, direction))


def test_ndx_blocked_by_default():
    allowed, reason = _run("NDX.INDX")
    assert allowed is False and "Fakeout" in reason


def test_other_symbols_shadow_only():
    for sym in ("GDAXI.INDX", "XAUUSD", "USOIL.FOREX"):
        assert _run(sym)[0] is True


def test_global_off_switch(monkeypatch):
    monkeypatch.setenv("FAKEOUT_GATE_BLOCK", "0")
    assert _run("NDX.INDX")[0] is True


def test_not_aligned_breakout_passes():
    assert _run("NDX.INDX", "BUY")[0] is True
