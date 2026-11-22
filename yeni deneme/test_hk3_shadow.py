"""hk3_shadow.py birim testleri (MT5 gerekmez). Çalıştır: cd 'yeni deneme' && python3 -m pytest test_hk3_shadow.py"""
import logging

import hk3_shadow as h

LOG = logging.getLogger("t")
H = 3600


def bar(t, o, hi, lo, c):
    return {"t": t, "o": o, "h": hi, "l": lo, "c": c, "sp": 30.0}


def test_entry_next_bar_and_levels(monkeypatch):
    monkeypatch.setattr(h, "_append", lambda r: None)
    bars = [bar(0, 7.7530, 7.7535, 7.7525, 7.7530), bar(H, 7.7525, 7.7526, 7.7515, 7.7518), bar(2 * H, 7.7517, 7.7522, 7.7516, 7.7520)]
    st = {"pos": None, "last_t": -1}
    assert h.step(st, bars, None, 1e-5, LOG)
    p = st["pos"]
    assert p["t_in"] == 2 * H and abs(p["E"] - 7.7517) < 1e-12
    assert abs(p["tp"] - 7.7537) < 1e-9 and abs(p["sl"] - (7.7517 - (7.7518 - 7.7470))) < 1e-9


def test_no_entry_until_next_bar_exists(monkeypatch):
    monkeypatch.setattr(h, "_append", lambda r: None)
    st = {"pos": None, "last_t": -1}
    h.step(st, [bar(0, 7.7530, 7.7531, 7.7515, 7.7518)], None, 1e-5, LOG)
    assert st["pos"] is None and st["last_t"] == -1          # sinyal barı son bar → bekle, ilerleme yok


def test_first_run_skips_history(monkeypatch):
    monkeypatch.setattr(h, "_append", lambda r: None)
    st = {"pos": None, "last_t": 0}
    h.step(st, [bar(5 * H, 7.75, 7.75, 7.75, 7.7510), bar(6 * H, 7.75, 7.75, 7.75, 7.7510)], None, 1e-5, LOG)
    assert st["pos"] is None and st["last_t"] == 6 * H


def test_same_bar_tp_sl_is_sl():
    pos = {"tp": 7.7540, "sl": 7.7470}
    r = h.resolve(pos, [bar(0, 7.752, 7.7545, 7.7465, 7.75)])
    assert r["why"] == "SL"
    assert h.resolve(pos, [bar(0, 7.752, 7.7541, 7.7500, 7.75)])["why"] == "TP"
    assert h.resolve(pos, [bar(0, 7.752, 7.7530, 7.7500, 7.75)]) is None


def test_swap_nights_weekday_and_wednesday_triple():
    mon = 4 * 86400            # 1970-01-05 Pazartesi
    assert h.swap_nights(mon, mon + 1 * 86400) == 1     # Pzt → Sal
    assert h.swap_nights(mon + 2 * 86400, mon + 3 * 86400) == 3   # Çar → Per (Çarşamba devri)
    assert h.swap_nights(mon + 4 * 86400, mon + 7 * 86400) == 1   # Cum → Pzt (hafta sonu sayılmaz)
