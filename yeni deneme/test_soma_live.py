"""SOMA E4X3 / E2X3 canlı modülleri — saf fonksiyon testleri. Araştırma paritesi: research/soma_cozum_20261122/src/sc19_*_parite.py."""
from __future__ import annotations

import numpy as np

import kural_katalogu as kk
import soma_e2x3_live as E2
import soma_e4x3_live as E4


def test_katalog_magic_benzersiz():
    offs = [v["magic_offset"] for v in kk.RULES.values()]
    assert len(offs) == len(set(offs)) and 15 not in offs           # +15 fx_vixreg (katalog dışı)
    for r in ("SOMA_E4X3", "SOMA_E2_XAU", "SOMA_E2_NDX"):
        assert r in kk.RULES and kk.RULES[r]["live_key"].endswith("_LIVE")
    assert set(E2.MARKETS) == {"SOMA_E2_XAU", "SOMA_E2_NDX"}


def test_kenar_ates():
    s = {"y": 1, "skor": 0.9, "skor_onceki": 0.1}
    assert E2.fires(s, 0.5)
    assert not E2.fires({**s, "skor_onceki": 0.6}, 0.5)            # önceki dakika da üstündeyse kenar değil
    assert not E2.fires({**s, "y": -1}, 0.5)                        # yalnız AL
    assert not E2.fires({**s, "skor": 0.4}, 0.5)


def test_srv_to_utc_dst():
    import datetime as dt
    yaz = int(dt.datetime(2026, 7, 1, 12, tzinfo=dt.timezone.utc).timestamp())
    kis = int(dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone.utc).timestamp())
    assert (yaz - E2.srv_to_utc(np.array([yaz]))[0]) == 3 * 3600   # sunucu = NY + 7 → yazın UTC+3
    assert (kis - E2.srv_to_utc(np.array([kis]))[0]) == 2 * 3600


def test_build_series_sentetik_onek():
    m1 = {x: np.arange(10.0) for x in "ohlcv"} | {"t": 7200.0 + 60 * np.arange(10)}
    h1 = {x: np.array([1.0, 2.0, 3.0]) for x in "ohlcv"} | {"t": np.array([0.0, 3600.0, 7200.0])}
    s = E2.build_series(m1, h1)
    assert s["n_sentetik"] == 2 and s["t"][:2].tolist() == [0.0, 3600.0] and len(s["t"]) == 12


def test_before_bucket():
    t = np.array([0, 14400, 28800], float)
    assert E4.before_bucket(t, 28800 + 60, 14400).tolist() == [True, True, False]   # k'nın mumu hariç
    assert E4.before_bucket(t, 28800 - 60, 14400).tolist() == [True, False, False]


def _seri(n, base=100.0, egim=0.001, gun_bas=0):
    t = gun_bas + 60 * np.arange(n, dtype=float)
    c = base + egim * np.arange(n)
    return {"t": t, "o": c - 0.0005, "h": c + 0.0002, "l": c - 0.001, "c": c}


def test_evaluate_yeni_gun_tepesi():
    n = E4.EMA_UZUN + 3000
    m1 = _seri(n, gun_bas=86400 * 100)
    # son bar güçlü yükseliş gövdeli yeni gün tepesi
    m1["o"][-1], m1["c"][-1], m1["h"][-1], m1["l"][-1] = m1["c"][-2], m1["c"][-2] + 0.05, m1["c"][-2] + 0.06, m1["c"][-2] - 0.001
    h4 = {x: np.full(60, v) for x, v in (("h", m1["c"][-2]), ("l", m1["c"][-2] - 1.0), ("c", m1["c"][-2] - 0.2))}
    h1 = {x: np.full(60, v) for x, v in (("h", 1.0), ("l", 0.0), ("c", 0.5))}
    s = E4.evaluate(m1, h4, h1)
    assert s is not None and s["stop_dist"] > 0
    m1b = {k: v.copy() for k, v in m1.items()}
    m1b["c"][-1] = m1b["o"][-1] + 0.001                              # zayıf gövde → yok
    assert E4.evaluate(m1b, h4, h1) is None


def test_model_dosyasi():
    m = E2.load_model()
    assert {"model", "oz", "esik"} <= set(m) and 0 < m["esik"] < 1 and len(m["oz"]) > 50


def test_srv_offset_kural():
    import datetime as dt
    kis = dt.datetime(2026, 11, 23, 23, 5, tzinfo=dt.timezone.utc).timestamp()
    yaz = dt.datetime(2026, 7, 1, 12, tzinfo=dt.timezone.utc).timestamp()
    assert E4.srv_offset(kis) == 2 * 3600 and E4.srv_offset(yaz) == 3 * 3600


def test_be_due():
    assert E2.be_due(100.0, 90.0, 90.0, 110.0, 1.0)              # +1R tam
    assert not E2.be_due(100.0, 90.0, 90.0, 109.9, 1.0)
    assert not E2.be_due(100.0, 90.0, 100.0, 120.0, 1.0)         # stop zaten girişte
    assert not E2.be_due(100.0, 90.0, 90.0, 120.0, 0.0)          # kapalı


class _Res:
    def __init__(self, rc):
        self.retcode = rc


class _MT5:
    TRADE_ACTION_SLTP, TRADE_RETCODE_DONE = 6, 10009

    def __init__(self, bid):
        self.bid, self.sent = bid, []

    def symbol_info_tick(self, s):
        return type("T", (), {"bid": self.bid})()

    def symbol_info(self, s):
        return type("I", (), {"digits": 2})()

    def order_send(self, req):
        self.sent.append(req)
        return _Res(self.TRADE_RETCODE_DONE)


class _Log:
    def info(self, *a): pass
    def error(self, *a): pass


def test_breakeven_bir_kez(tmp_path, monkeypatch):
    monkeypatch.setattr(E2, "STATE_FILE", tmp_path / "st.json")
    monkeypatch.setattr(E2.kk, "EVENTS_JSONL", tmp_path / "ev.jsonl")
    pos = type("P", (), {"ticket": 7, "symbol": "NAS100", "price_open": 20000.0, "sl": 19900.0, "tp": 0.0, "time": 1_700_000_000})()
    st = {"pos": {"7": {"entry_t": 1.0, "sl": 19900.0, "rule": "SOMA_E2_NDX"}}}
    cfg = type("C", (), {})()
    m = _MT5(20099.0)
    E2._breakeven(m, cfg, _Log(), "SOMA_E2_NDX", pos, st["pos"]["7"], st)
    assert m.sent == []                                           # +1R'ye ulaşmadı
    m.bid = 20100.0
    E2._breakeven(m, cfg, _Log(), "SOMA_E2_NDX", pos, st["pos"]["7"], st)
    assert len(m.sent) == 1 and m.sent[0]["sl"] == 20000.0 and st["pos"]["7"]["be_done"]
    E2._breakeven(m, cfg, _Log(), "SOMA_E2_NDX", pos, st["pos"]["7"], st)
    assert len(m.sent) == 1                                       # bir kez
    assert "SOMA_E2_XAU" not in E2.BE_RULES                       # DAX/XAU'ya taşınmaz
