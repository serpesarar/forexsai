"""SC-08 özellik motoru: pandas ile baştan hesaplanan referansa eşitlik + nedensellik."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import sc08_ozellik as F  # noqa: E402
import sc_veri as V  # noqa: E402


def bar_rw(n=30000, tohum=1):
    rng = np.random.default_rng(tohum)
    c = 2000 + np.cumsum(rng.normal(0, 0.5, n))
    o = np.r_[2000, c[:-1]]
    h = np.maximum(o, c) + rng.exponential(0.2, n)
    l = np.minimum(o, c) - rng.exponential(0.2, n)  # noqa: E741
    t = (1_700_000_040 + 60 * np.cumsum(rng.choice([1, 1, 1, 2], n))).astype(np.int64)
    return V.Bar(t, o, h, l, c, np.full(n, 0.3)), rng.exponential(1, n)


def referans(bar, vol, sun, dk, k, p):
    """Baştan: 1m'den mumları kur, k'ya kadar tamamlananları al, oluşan mumu p ile ekle."""
    kv = (bar.t + sun) // (dk * 60)
    simdi = (bar.t[k] + 60 + sun[k]) // (dk * 60)
    m = np.arange(k + 1)
    df = pd.DataFrame({"kv": kv[m], "o": bar.o[m], "h": bar.h[m], "l": bar.l[m], "c": bar.c[m]})
    g = df.groupby("kv").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tam = g[g.index < simdi]
    C = tam["c"].to_numpy()
    e20 = pd.Series(C).ewm(span=20, adjust=False).mean().to_numpy()
    a_e20 = pd.Series(np.r_[C, p]).ewm(span=20, adjust=False).mean().to_numpy()[-1]
    d = np.diff(np.r_[C, p], prepend=C[0])
    up = pd.Series(np.maximum(d, 0)).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()[-1]
    dn = pd.Series(np.maximum(-d, 0)).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()[-1]
    a_rsi = 100 - 100 / (1 + up / dn)
    hh20 = tam["h"].to_numpy()[-20:].max()
    forming = g[g.index == simdi]
    fO = forming["o"].iat[0] if len(forming) else p
    return {"c_e20": e20[-1], "a_e20": a_e20, "a_rsi": a_rsi, "hh20": hh20, "fO": fO, "C": C[-1]}


def test_motor_referans_esit():
    bar, vol = bar_rw()
    M = F.Motor(bar, vol)
    rng = np.random.default_rng(2)
    ks = rng.integers(25000, 29900, 40)
    p = bar.c[ks] + rng.normal(0, 0.3, 40)
    y = np.ones(40, int)
    t = bar.t[ks] + 60
    o = M.ozellik(ks, p, y, t)
    for ad in ("M5", "M15", "H1", "H4"):
        g = M.tf[ad].g
        for j, k in enumerate(ks):
            r = referans(bar, vol, M.sun, F.TF_DK[ad], k, p[j])
            T = M.tf[ad]
            bc = np.searchsorted(T.kova, (t[j] + M.sun[k]) // (F.TF_DK[ad] * 60)) - 1
            atr = g["atr"][bc]
            assert np.isclose(T.C[bc], r["C"])
            assert np.isclose(o[f"{ad}_c_ema20"].iat[j], (r["C"] - r["c_e20"]) / atr)
            assert np.isclose(o[f"{ad}_a_ema20"].iat[j], (p[j] - r["a_e20"]) / atr)
            assert np.isclose(o[f"{ad}_a_rsi"].iat[j], r["a_rsi"], atol=1e-6)
            assert np.isclose(o[f"{ad}_a_kir20"].iat[j], (p[j] - r["hh20"]) / atr)
            assert np.isclose(o[f"{ad}_a_mum"].iat[j], (p[j] - r["fO"]) / atr)


def test_motor_nedensel():
    bar, vol = bar_rw(12000, 5)
    rng = np.random.default_rng(9)
    ks = rng.integers(9000, 10000, 30)
    p = bar.c[ks]
    y = rng.choice([-1, 1], 30)
    t = bar.t[ks] + 60
    o1 = F.Motor(bar, vol).ozellik(ks, p, y, t)
    kes = ks.max()
    b2 = V.Bar(bar.t, bar.o.copy(), bar.h.copy(), bar.l.copy(), bar.c.copy(), bar.s.copy())
    for a in (b2.o, b2.h, b2.l, b2.c):
        a[kes + 1:] += rng.normal(0, 4, len(a) - kes - 1)
    b2.h[:] = np.maximum.reduce([b2.h, b2.o, b2.c])
    b2.l[:] = np.minimum.reduce([b2.l, b2.o, b2.c])
    v2 = vol.copy()
    v2[kes + 1:] *= 3
    o2 = F.Motor(b2, v2).ozellik(ks, p, y, t)
    pd.testing.assert_frame_equal(o1, o2)
