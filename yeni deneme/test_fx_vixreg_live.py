"""fx_vixreg_live.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 -m pytest test_fx_vixreg_live.py"""
import logging
from datetime import date
from types import SimpleNamespace

import pytest

import fx_fiks_shadow as fs
import fx_vixreg_live as fv

LOG = logging.getLogger("t")


@pytest.fixture(autouse=True)
def _tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(fv, "STATE_FILE", tmp_path / "st.json")
    monkeypatch.setattr(fv, "EVENTS_JSONL", tmp_path / "ev.jsonl")
    monkeypatch.setattr(fv, "CAPREV_STATE", tmp_path / "caprev.json")
    monkeypatch.setattr(fv, "_last_poll", 0.0)


def test_hedef_bir_onceki_gunun_vixi():
    hist = {"2026-11-12": 19.0, "2026-11-13": 15.0}
    assert fv.target_on(hist, date(2026, 11, 13)) is True       # Cuma kararı → Pazartesi getirisi: Perşembe VIX'i 19
    assert fv.target_on(hist, date(2026, 11, 16)) is False      # Pazartesi kararı: Cuma VIX'i 15
    assert fv.target_on({}, date(2026, 11, 16)) is None


def test_plan_ac_kapat_duzelt():
    to_open, to_close = fv.plan(True, {"AUDJPY": 1, "USDMXN": 1})   # USDMXN ters yönde açık
    assert ("USDMXN", -1) in to_open and "USDMXN" in to_close and ("AUDJPY", 1) not in to_open
    assert len(to_open) == len(fv.PAIRS) - 1
    to_open, to_close = fv.plan(False, {"AUDJPY": 1})
    assert to_open == [] and to_close == ["AUDJPY"]


def test_pencere():
    assert fv.in_window(fs.utc_at(date(2026, 11, 16), 21) + 35 * 60) == date(2026, 11, 16)   # 16:35 EST
    assert fv.in_window(fs.utc_at(date(2026, 11, 16), 22)) is None                            # 17:00 EST
    assert fv.in_window(fs.utc_at(date(2026, 11, 14), 21) + 35 * 60) is None                 # Cumartesi


class FakeMT5:
    TRADE_ACTION_DEAL, ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TIME_GTC = 1, 0, 1, 0
    TRADE_RETCODE_DONE, POSITION_TYPE_SELL = 10009, 1

    def __init__(self, now):
        self.now, self.sent, self.pos = now, [], []

    def positions_get(self):
        return self.pos

    def symbol_select(self, *_):
        return True

    def symbol_info_tick(self, s):
        return SimpleNamespace(time=self.now + 7200, ask=1.0001, bid=1.0)

    def symbol_info(self, s):
        return SimpleNamespace(digits=5)


def test_poll_rejimde_16_pozisyon_acar_bir_kez():
    now = fs.utc_at(date(2026, 11, 16), 21) + 35 * 60
    m = FakeMT5(now)
    cfg = SimpleNamespace(LIVE_TRADING=True, MAGIC_NUMBER=100, DEVIATION_POINTS=20)
    send = lambda req, sym: (m.sent.append(req), SimpleNamespace(retcode=10009, order=len(m.sent)))[1]
    st = fv._load_state(); st["vix_hist"] = {"2026-11-13": 20.0}; fv._save_state(st)
    args = (m, cfg, LOG, lambda s: s, lambda: 19.0, lambda s: 7200, send, lambda a, b: a + b, lambda: True, lambda *a: None)
    fv.poll(*args, now=now)
    assert len(m.sent) == len(fv.PAIRS) and all(r["magic"] == 115 and r["volume"] == 0.01 for r in m.sent)
    sides = {r["symbol"]: r["type"] for r in m.sent}
    assert sides["AUDJPY"] == m.ORDER_TYPE_BUY and sides["USDMXN"] == m.ORDER_TYPE_SELL
    fv.poll(*args, now=now + 60)                                   # aynı gün ikinci kez emir yok
    assert len(m.sent) == len(fv.PAIRS)


def test_poll_rejim_disinda_kapatir():
    now = fs.utc_at(date(2026, 11, 16), 21) + 35 * 60
    m = FakeMT5(now)
    m.pos = [SimpleNamespace(magic=115, symbol="AUDJPY", type=0, ticket=7, volume=0.01, price_open=1.0, profit=1.0)]
    cfg = SimpleNamespace(LIVE_TRADING=True, MAGIC_NUMBER=100, DEVIATION_POINTS=20)
    send = lambda req, sym: (m.sent.append(req), SimpleNamespace(retcode=10009, order=1))[1]
    st = fv._load_state(); st["vix_hist"] = {"2026-11-13": 15.0}; fv._save_state(st)
    fv.poll(m, cfg, LOG, lambda s: s, lambda: 15.0, lambda s: 7200, send, lambda a, b: a + b, lambda: True, lambda *a: None, now=now)
    assert len(m.sent) == 1 and m.sent[0]["position"] == 7 and m.sent[0]["type"] == m.ORDER_TYPE_SELL


def test_kapali_bayrak():
    now = fs.utc_at(date(2026, 11, 16), 21) + 35 * 60
    m = FakeMT5(now)
    cfg = SimpleNamespace(LIVE_TRADING=True, FX_VIXREG_LIVE=False, MAGIC_NUMBER=100, DEVIATION_POINTS=20)
    fv.poll(m, cfg, LOG, lambda s: s, lambda: 20.0, lambda s: 7200, lambda *a: None, lambda a, b: a, lambda: True, lambda *a: None, now=now)
    assert m.sent == []
