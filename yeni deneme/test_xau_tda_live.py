"""XAU TDA (trend-duraklama AL) canlı modülü — saf fonksiyon testleri. Araştırma paritesi 11.761/11.761 saat başı (MG-4/5)."""
from __future__ import annotations

import datetime as dt

import numpy as np

import kural_katalogu as kk
import xau_trend_duraklama_live as L


def _h1(n=400, egim=0.5, son4_duz=True):
    t = 3600.0 * np.arange(n) + 1_700_000_000 // 3600 * 3600
    c = 2000 + egim * np.arange(n, dtype=float)
    if son4_duz:
        c[-4:] = c[-5]
    h, l = c + 1.0, c - 1.0
    return {"t": t, "o": c, "h": h, "l": l, "c": c}


def test_katalog():
    r = kk.RULES["XAU_TDA"]
    assert r["magic_offset"] == 20 and r["live_key"] == "XAU_TDA_LIVE" and r["lot"] == 0.05
    offs = [v["magic_offset"] for v in kk.RULES.values()]
    assert len(offs) == len(set(offs))


def test_ozellik_ve_karar():
    f = L.ozellik(_h1())
    assert f is not None and f["r12"] > 1 and abs(f["r4"]) < 0.5 and f["uz"] > 1
    u_iyi = dt.datetime(2026, 11, 24, 8, tzinfo=dt.timezone.utc).timestamp()      # Salı 08 UTC
    u_saat = dt.datetime(2026, 11, 24, 9, tzinfo=dt.timezone.utc).timestamp()     # 09 UTC listede yok
    u_cmt = dt.datetime(2026, 11, 28, 8, tzinfo=dt.timezone.utc).timestamp()      # Cumartesi
    f["konum24"] = 0.8
    assert L.karar(f, u_iyi) and not L.karar(f, u_saat) and not L.karar(f, u_cmt)
    assert not L.karar({**f, "konum24": 0.97}, u_iyi) and not L.karar({**f, "r4": 0.6}, u_iyi) and not L.karar(None, u_iyi)


def test_seviyeler():
    s = L.seviyeler(4000.0, 2)
    assert s["tp"] == 4023.68 and s["sl"] == 3962.12 and abs(s["kilit_tetik"] - 4015.28) < 1e-6 and s["kilit_sl"] == 4015.16


def test_srv_to_utc():
    kis = int(dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone.utc).timestamp())
    assert kis - L.srv_to_utc(np.array([kis]))[0] == 2 * 3600
