"""Gölge kapı verdikt kaydı — signal_gates._shadow_verdict + apply_signal_gates_ex.

Gölge modda (``*_GATE_BLOCK=0``) bir kapı "bloklardım" dediğinde bu bilgi
eskiden yalnız log satırına gidiyordu, yani ÖLÇÜLEMİYORDU. Artık verdikt
sinyalin ``factors.shadow_gates`` alanına yazılır ve Gölge Modu paneli
"kapıyı açsam ne olurdu" sorusunu cevaplayabilir.

Buradaki testler o zincirin kapı tarafını korur:
  - verdikt toplanıyor mu, aynı kapı iki kez yazılmıyor mu
  - toplayıcı yokken güvenli mi (kapılar apply_signal_gates dışında da çağrılır)
  - eşzamanlı çağrılar birbirinin verdiktini görüyor mu (ContextVar izolasyonu)
  - BLOK moduna alınan kapı gölge verdikti YAZMAMALI (artık gölge değil)
"""
from __future__ import annotations

import asyncio

import pytest

from services import signal_gates as sg


@pytest.fixture
def sink():
    """Verdikt toplayıcıyı kur ve test sonunda geri al."""
    bucket: list = []
    token = sg._shadow_sink.set(bucket)
    yield bucket
    sg._shadow_sink.reset(token)


def test_verdict_collected(sink):
    sg._shadow_verdict("trend_align_gate", "NDX.INDX", "SELL", "1h EMA50 karşıtı")
    assert len(sink) == 1
    v = sink[0]
    assert v["gate"] == "trend_align_gate"
    assert v["symbol"] == "NDX.INDX"
    assert v["direction"] == "SELL"
    assert v["reason"] == "1h EMA50 karşıtı"
    assert v["at"]


def test_same_gate_recorded_once(sink):
    """Bir kapı tek sinyalde birden çok kez tetiklenebilir; verdikt tekilleşmeli."""
    sg._shadow_verdict("fakeout_gate", "NDX.INDX", "BUY", "ilk")
    sg._shadow_verdict("fakeout_gate", "NDX.INDX", "BUY", "ikinci")
    assert len(sink) == 1
    assert sink[0]["reason"] == "ilk"


def test_reason_truncated(sink):
    sg._shadow_verdict("vix_regime_gate", "NDX.INDX", "SELL", "x" * 500)
    assert len(sink[0]["reason"]) == 240


def test_safe_without_sink():
    """Kapılar apply_signal_gates dışından da çağrılır — toplayıcı yoksa sessiz."""
    assert sg._shadow_sink.get() is None
    sg._shadow_verdict("fakeout_gate", "XAUUSD", "BUY", "toplayıcı yok")  # patlamamalı


def test_concurrent_sinks_isolated():
    """İki eşzamanlı sinyal birbirinin verdiktini görmemeli (ContextVar)."""
    async def probe(gate: str, symbol: str) -> list:
        bucket: list = []
        token = sg._shadow_sink.set(bucket)
        await asyncio.sleep(0.01)          # araya başka görev girsin
        sg._shadow_verdict(gate, symbol, "BUY", "test")
        await asyncio.sleep(0.01)
        sg._shadow_sink.reset(token)
        return bucket

    async def main():
        return await asyncio.gather(probe("g1", "A"), probe("g2", "B"))

    a, b = asyncio.run(main())
    assert [v["gate"] for v in a] == ["g1"]
    assert [v["gate"] for v in b] == ["g2"]


def test_apply_signal_gates_ex_returns_triple():
    """_ex üçlü döner; eski apply_signal_gates ikili kalmalı (geri uyum)."""
    async def main():
        triple = await sg.apply_signal_gates_ex("NDX.INDX", "BUY", "pulse1", confidence=70)
        double = await sg.apply_signal_gates("NDX.INDX", "BUY", "pulse1", confidence=70)
        return triple, double

    triple, double = asyncio.run(main())
    assert len(triple) == 3 and isinstance(triple[2], list)
    assert len(double) == 2


def test_shadow_gate_records_but_does_not_block(monkeypatch):
    """XAU scalp kapısı: GÖLGE modda sinyal GEÇER ama verdikt kaydedilir."""
    monkeypatch.setenv("XAU_SCALP_GATE_ENABLED", "1")
    monkeypatch.setenv("XAU_SCALP_GATE_BLOCK", "0")
    # Diğer kapılar yolu kirletmesin
    monkeypatch.setenv("SESSION_GATES_ENABLED", "0")
    monkeypatch.setenv("CALENDAR_GATE_ENABLED", "0")
    monkeypatch.setenv("TQ_GATE_ENABLED", "0")

    gated, _notes, shadow = asyncio.run(
        sg.apply_signal_gates_ex("XAUUSD", "BUY", "pulse1", confidence=70))

    assert gated == "BUY", "gölge kapı sinyali GERÇEKTEN bloklamış"
    gates = [v["gate"] for v in shadow]
    assert "xau_scalp_gate" in gates, f"verdikt yazılmadı: {gates}"


def test_blocking_gate_writes_no_shadow_verdict(monkeypatch):
    """BLOK moduna alınan kapı artık gölge değildir — verdikt YAZMAMALI."""
    monkeypatch.setenv("XAU_SCALP_GATE_ENABLED", "1")
    monkeypatch.setenv("XAU_SCALP_GATE_BLOCK", "1")
    monkeypatch.setenv("SESSION_GATES_ENABLED", "0")
    monkeypatch.setenv("CALENDAR_GATE_ENABLED", "0")
    monkeypatch.setenv("TQ_GATE_ENABLED", "0")

    gated, _notes, shadow = asyncio.run(
        sg.apply_signal_gates_ex("XAUUSD", "BUY", "pulse1", confidence=70))

    assert gated == "HOLD"
    assert not any(v["gate"] == "xau_scalp_gate" for v in shadow)
