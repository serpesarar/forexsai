"""MOD-E probasyon icra çekirdeği testleri (MT5 gerekmez).

`probation_exec.decide` saf: geçen süre + sinyalden sonraki barlar → karar.
Kritik davranış: karar verilemiyorsa **İPTAL** (kör giriş yok) — bu, kapıların
genel 'fail-open' felsefesinin BİLİNÇLİ istisnasıdır, çünkü burada söz konusu
olan bir emrin gönderilmesi.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

BOT = Path(__file__).resolve().parents[1] / "yeni deneme"
sys.path.insert(0, str(BOT))

# probation_exec `import config` yapar; kutu config'i burada yok → sahte modül.
if "config" not in sys.modules:
    sys.modules["config"] = types.ModuleType("config")

import probation_exec as px  # noqa: E402


class Cfg:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def bars(seq):
    return [{"high": h, "low": l, "close": c} for h, l, c in seq]


ATR = 10.0                      # band = 1.28 × 10 × √5 ≈ 28.6


def test_waits_until_five_bars_elapsed():
    v, info = px.decide(3 * 60, bars([(101, 99, 100)] * 3), "BUY", 100.0, ATR, None)
    assert v == "wait"


def test_waits_when_bars_missing_despite_time():
    v, _ = px.decide(6 * 60, bars([(101, 99, 100)] * 2), "BUY", 100.0, ATR, None)
    assert v == "wait"


def test_enters_when_inside_noise_band():
    v, info = px.decide(5 * 60, bars([(101, 95, 99)] * 5), "BUY", 100.0, ATR, None)
    assert v == "enter" and info["adverse"] == pytest.approx(5.0)
    assert info["band"] == pytest.approx(28.62, abs=0.1)


def test_cancels_when_band_exceeded_buy():
    v, info = px.decide(5 * 60, bars([(101, 99, 100)] * 4 + [(100, 60, 70)]),
                        "BUY", 100.0, ATR, None)
    assert v == "cancel" and info["adverse"] == pytest.approx(40.0)


def test_cancels_when_band_exceeded_sell():
    v, info = px.decide(5 * 60, bars([(140, 99, 120)] * 5), "SELL", 100.0, ATR, None)
    assert v == "cancel" and info["adverse"] == pytest.approx(40.0)


def test_cancels_stale_intent():
    v, info = px.decide(20 * 60, bars([(101, 99, 100)] * 5), "BUY", 100.0, ATR, None)
    assert v == "cancel" and "bayat" in info["why"]


def test_cancels_without_atr_instead_of_blind_entry():
    v, info = px.decide(5 * 60, bars([(101, 99, 100)] * 5), "BUY", 100.0, None, None)
    assert v == "cancel" and "kör giriş" in info["why"]


def test_only_first_n_bars_count():
    seq = bars([(101, 99, 100)] * 5 + [(200, 50, 60)])   # 6. bar sayılmamalı
    v, info = px.decide(6 * 60, seq, "BUY", 100.0, ATR, None)
    assert v == "enter" and info["adverse"] == pytest.approx(1.0)


def test_custom_bar_count_and_z(monkeypatch):
    cfg = Cfg(PROBATION_BARS=3, PROBATION_Z=0.5, PROBATION_MAX_WAIT_MIN=15)
    # band = 0.5 × 10 × √3 ≈ 8.66 → 10pt aleyhe İPTAL
    v, info = px.decide(3 * 60, bars([(101, 90, 95)] * 3), "BUY", 100.0, ATR, cfg)
    assert v == "cancel" and info["band"] == pytest.approx(8.66, abs=0.05)


def test_is_live_respects_symbol_scope():
    import config as fake
    fake.PROBATION_LIVE = True
    fake.PROBATION_SYMBOLS = ("NDX.INDX",)
    assert px.is_live("NDX.INDX")
    assert not px.is_live("USOIL.FOREX")
    fake.PROBATION_LIVE = False
    assert not px.is_live("NDX.INDX")
    del fake.PROBATION_LIVE, fake.PROBATION_SYMBOLS


def test_queue_dedupes_same_scope():
    logs = []
    log = types.SimpleNamespace(info=lambda *a, **k: logs.append(a),
                                warning=lambda *a, **k: None)
    px._pending.clear()
    ok1 = px.queue(log, "NDX.INDX:BUY", "NDX.INDX", "NAS100", "BUY", 100.0, 1, lambda: None)
    ok2 = px.queue(log, "NDX.INDX:BUY", "NDX.INDX", "NAS100", "BUY", 100.0, 1, lambda: None)
    assert ok1 and not ok2 and len(px._pending) == 1
    assert px.pending_scopes() == {"NDX.INDX:BUY"}
    px._pending.clear()


def _fake_mt5(hi=100.5, lo=99.8, post_lo=None):
    """Sinyal ÖNCESİ ve SONRASI barları olan sahte MT5 (ATR hesaplanabilsin).

    post_lo verilirse yalnız sinyal SONRASI barlar o düşüğü görür — ATR sakin
    kalır, aleyhe hareket bandı aşar (gerçek 'sinyal öldü' senaryosu)."""
    class FakeTick:
        bid = ask = 100.0
        time = 60

    class FakeMT5:
        TIMEFRAME_M1 = 1

        @staticmethod
        def copy_rates_from_pos(sym, tf, start, n):
            return [{"time": i * 60, "high": hi,
                     "low": (post_lo if (post_lo is not None and i > 30) else lo),
                     "close": 100.0}
                    for i in range(60)]

        @staticmethod
        def symbol_info_tick(sym):
            return FakeTick()

    return FakeMT5


def _queued(log, opener):
    px._pending.clear()
    px.queue(log, "NDX.INDX:BUY", "NDX.INDX", "NAS100", "BUY", 100.0,
             30 * 60, opener)                 # sinyal 30. barda
    px._pending[0]["t0"] -= 10 * 60           # bekleme bitmiş say


def test_guard_blocks_entry_after_wait():
    """Bekleme bitti ama tavan doldu → emir GÖNDERİLMEZ (icra anı kontrolü)."""
    fired = []
    log = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)
    _queued(log, lambda: fired.append(1))
    px.process(_fake_mt5(), log, guard=lambda p: (False, "global tavan dolu"))
    assert fired == [] and px._pending == []


def test_guard_allows_entry_when_room_exists():
    """Bant aşılmadı + tavan uygun → emir gönderilir."""
    fired = []
    log = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)
    _queued(log, lambda: fired.append(1))
    px.process(_fake_mt5(), log, guard=lambda p: (True, ""))
    assert fired == [1] and px._pending == []


def test_no_guard_still_enters():
    fired = []
    log = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)
    _queued(log, lambda: fired.append(1))
    px.process(_fake_mt5(), log)
    assert fired == [1]


def test_band_breach_cancels_before_guard():
    """Bant aşıldıysa guard'a hiç gidilmez — emir zaten iptal."""
    fired, guard_calls = [], []
    log = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None)
    _queued(log, lambda: fired.append(1))
    # 60 puanlık aleyhe hareket: band ~2pt → kesin iptal
    px.process(_fake_mt5(post_lo=95.0), log,
               guard=lambda p: (guard_calls.append(1), (True, ""))[1])
    assert fired == [] and guard_calls == [] and px._pending == []
