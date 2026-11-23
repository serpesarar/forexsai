"""SC simülatör testleri: elle kurulmuş senaryolar + C çekirdeği = Python referansı (bulanık) + nedensellik.

Koşu: .venv/bin/python -m pytest -q research/soma_cozum_20261122/tests
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import sc_sim as S  # noqa: E402
import sc_veri as V  # noqa: E402


def bar_yap(o, h, l, c, s=0.0, t0=1_000_000_020):  # noqa: E741
    n = len(o)
    t = (t0 // 60 * 60 + 60 * np.arange(n)).astype(np.int64)
    return V.Bar(t, np.array(o, float), np.array(h, float), np.array(l, float), np.array(c, float), np.full(n, float(s)))


def tek(bar, **kw):
    e = S.Emir.yeni(1)
    for k, v in kw.items():
        getattr(e, k)[0] = v
    r = S.simule(bar, e, komisyon_usd=0.0)
    return r.iloc[0]


# ───────── elle kurulmuş senaryolar ─────────
def test_alis_tp():
    b = bar_yap([100, 100.5, 101], [100.4, 101.2, 101.5], [99.8, 100.3, 100.9], [100.2, 101, 101.2])
    r = tek(b, sl_d=1.0, tp_d=1.0)
    assert r.neden == "TP" and r.cikis == 101.0 and r.j == 1


def test_ayni_barda_stop_ve_tp_stop_kazanir():
    b = bar_yap([100, 100], [101.5, 100], [98.5, 100], [100, 100])
    r = tek(b, sl_d=1.0, tp_d=1.0)
    assert r.neden == "STOP" and r.cikis == 99.0 and r.j == 0


def test_bosluk_stopun_otesinde_acilista_doluyor():
    b = bar_yap([100, 97, 97], [100.2, 97.5, 98], [99.5, 96.5, 96.8], [100, 97, 97.5])
    r = tek(b, sl_d=1.0)
    assert r.neden == "STOP" and r.cikis == 97.0 and r.j == 1


def test_spread_alis_ask_ten_girer_bid_den_cikar():
    b = bar_yap([100, 100, 100], [100, 100, 100], [100, 100, 100], [100, 100, 100], s=0.5)
    r = tek(b, t_cik=int(b.t[2]))
    assert r.giris == 100.5 and r.cikis == 100.0 and r.neden == "ZAMAN" and r.j == 2
    assert np.isclose(r.bp_brut, -50.0)


def test_satis_ask_ile_stoplanir():
    # satış bid 100'den; ask = bid + 0,5. Stop 1,0 → 101; bar 1 bid tepe 100,6 → ask tepe 101,1 ≥ 101 → stop
    b = bar_yap([100, 100.2], [100.1, 100.6], [99.9, 100.0], [100, 100.4], s=0.5)
    r = tek(b, yon=-1, sl_d=1.0)
    assert r.neden == "STOP" and r.cikis == 101.0 and r.j == 1


def test_iz_suren_stop_sonraki_bardan_gecerli():
    # alış 100; bar0 tepe 103 → iz (akt 2, mesafe 1) stop 102'ye taşınır; bar0'ın dibi 101,5 < 102 ama aynı bar → çıkmaz
    b = bar_yap([100, 102.5, 102], [103, 102.6, 102.2], [101.5, 101.8, 101], [102.5, 102, 101.2])
    r = tek(b, sl_d=5.0, iz_akt=2.0, iz_d=1.0)
    assert r.neden == "IZ" and r.cikis == 102.0 and r.j == 1


def test_basabas():
    b = bar_yap([100, 101, 100.2], [101.6, 101.1, 100.3], [100, 100.4, 99.5], [101, 100.5, 99.8])
    r = tek(b, sl_d=3.0, be_akt=1.5, be_off=0.1)
    assert r.neden == "IZ" and np.isclose(r.cikis, 100.1) and r.j == 2


def test_zaman_cikisi_en_az_bir_bar():
    b = bar_yap([100, 101, 102], [100, 101, 102], [100, 101, 102], [100, 101, 102])
    r = tek(b, t_cik=0)  # geçmişte bir zaman → yine de giriş barında çıkılmaz
    assert r.j == 1 and r.neden == "ZAMAN" and r.cikis == 101.0


def test_veri_sonu():
    b = bar_yap([100, 100], [100, 100], [100, 100], [100, 101])
    r = tek(b)
    assert r.neden == "SON" and r.cikis == 101.0


def test_emir_dogrulama_hatalari():
    b = bar_yap([100], [100], [100], [100])
    e = S.Emir.yeni(1)
    e.i0[0] = 5
    with pytest.raises(ValueError):
        S.simule(b, e)
    e = S.Emir.yeni(1)
    e.iz_akt[0] = 1.0  # iz_d = 0
    with pytest.raises(ValueError):
        S.simule(b, e)


# ───────── bulanık: C = Python referansı ─────────
def rastgele_bar(rng, n=600):
    r = rng.standard_t(3, n) * 0.4
    c = 100 + np.cumsum(r)
    o = np.r_[100, c[:-1]] + np.where(rng.random(n) < 0.03, rng.normal(0, 2, n), 0)  # ara sıra boşluk
    h = np.maximum(o, c) + rng.exponential(0.3, n)
    l = np.minimum(o, c) - rng.exponential(0.3, n)  # noqa: E741
    t = (1_600_000_000 + 60 * np.cumsum(rng.integers(1, 3, n))).astype(np.int64)
    return V.Bar(t, o, h, l, c, rng.uniform(0.0, 0.3, n))


@pytest.mark.parametrize("tohum", range(25))
def test_c_esit_referans(tohum):
    rng = np.random.default_rng(tohum)
    b = rastgele_bar(rng)
    n = 300
    e = S.Emir.yeni(n)
    e.i0[:] = rng.integers(0, len(b) - 1, n)
    e.yon[:] = rng.choice([-1, 1], n)
    sec = lambda p, a, z: np.where(rng.random(n) < p, rng.uniform(a, z, n), S.YOK)  # noqa: E731
    e.sl_d[:] = sec(0.8, 0.05, 4)
    e.tp_d[:] = sec(0.7, 0.05, 6)
    e.iz_akt[:] = sec(0.4, 0.1, 3)
    e.iz_d[:] = rng.uniform(0.1, 2, n)
    e.be_akt[:] = sec(0.3, 0.1, 3)
    e.be_off[:] = rng.uniform(-0.2, 0.5, n)
    e.t_cik[:] = np.where(rng.random(n) < 0.5, b.t[np.minimum(e.i0 + rng.integers(0, 200, n), len(b) - 1)], S.T_YOK)
    for sk in (1.0, 1.5):
        c_ = S._cekirdek(b, e, sk)
        p_ = S.referans(b, e, sk)
        for a, z in zip(c_, p_):
            assert np.array_equal(a, z) or np.allclose(a, z, rtol=0, atol=1e-12)


# ───────── nedensellik: çıkıştan sonraki / girişten önceki barlar sonucu değiştirmez ─────────
def test_nedensellik():
    rng = np.random.default_rng(7)
    b = rastgele_bar(rng, 800)
    e = S.Emir.yeni(200)
    e.i0[:] = rng.integers(100, 500, 200)
    e.yon[:] = rng.choice([-1, 1], 200)
    e.sl_d[:] = rng.uniform(0.5, 3, 200)
    e.tp_d[:] = rng.uniform(0.5, 3, 200)
    e.iz_akt[:] = 1.0
    e.iz_d[:] = 0.8
    r0 = S.simule(b, e)
    for k in range(200):
        j, i = int(r0.j[k]), int(e.i0[k])
        b2 = V.Bar(b.t, b.o.copy(), b.h.copy(), b.l.copy(), b.c.copy(), b.s.copy())
        for a in (b2.o, b2.h, b2.l, b2.c):
            a[j + 1:] += rng.normal(0, 5, len(a) - j - 1)
            a[:i] += rng.normal(0, 5, i)
        b2.h[:] = np.maximum.reduce([b2.h, b2.o, b2.c])
        b2.l[:] = np.minimum.reduce([b2.l, b2.o, b2.c])
        r1 = S.simule(b2, e.secim(np.arange(200) == k))
        assert r1.j.iat[0] == j and r1.cikis.iat[0] == r0.cikis.iat[k]
