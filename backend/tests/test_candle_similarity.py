"""Mum benzerlik motoru testleri: hızlı RMS = kaba kuvvet, gömülü kopya bulunur, boşluk/çakışma dışlanır."""
import numpy as np
import pytest

from services import candle_similarity_service as cs


def _series(n: int, seed: int = 0, step: int = 3600) -> cs.Series:
    rng = np.random.default_rng(seed)
    c = 100 + np.cumsum(rng.normal(0, 0.5, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.uniform(0, 0.4, n)
    l = np.minimum(o, c) - rng.uniform(0, 0.4, n)
    return cs.Series(np.arange(n, dtype=np.int64) * step, o, h, l, c)


def test_fast_rms_equals_brute_force():
    s = _series(400)
    n = 30
    q = cs.normalize_window(s.o[-n:], s.h[-n:], s.l[-n:], s.c[-n:])
    fast = cs.window_rms(s, q)
    for i in (0, 57, 200, 370):
        w = cs.normalize_window(s.o[i:i + n], s.h[i:i + n], s.l[i:i + n], s.c[i:i + n])
        brute = np.sqrt(((w - q) ** 2).mean())
        assert fast[i] == pytest.approx(brute, abs=1e-9)


def test_planted_copy_found_first_scale_free():
    s = _series(3000, seed=1)
    n, src = 50, 2900
    seg = [a[src:src + n] for a in (s.o, s.h, s.l, s.c)]
    # 800. bara aynı şekli 3 kat ölçekli ve +500 ötelenmiş olarak göm
    arrs = [a.copy() for a in (s.o, s.h, s.l, s.c)]
    for a, g in zip(arrs, seg):
        a[800:800 + n] = (g - seg[3].mean()) * 3 + 500   # tüm sütunlara AYNI doğrusal dönüşüm
    lib = cs.Series(s.ts, *arrs)
    q = cs.Series(s.ts[src:src + n], *seg)
    out = cs.match_core(lib, q, "1h", n, 5, end_before_ts=int(s.ts[src]))
    assert out["matches_idx"][0] == 800
    assert out["dist"][0] == pytest.approx(0.0, abs=1e-9)


def test_gap_and_overlap_excluded():
    s = _series(500)
    ts = s.ts.copy(); ts[250:] += 10 * 86400            # 250'de 10 günlük boşluk
    s2 = cs.Series(ts, s.o, s.h, s.l, s.c)
    ok = cs.valid_starts(s2, 20, 5, end_before_ts=int(ts[400]))
    assert not ok[240]                                   # pencere+ufuk boşluğu kesiyor
    assert ok[100]
    assert not ok[390]                                   # sorgu başlangıcıyla çakışıyor


def test_dedup_spacing():
    d = np.linspace(0, 1, 200)
    kept = cs.pick_matches(d, np.ones(200, bool), 5, gap=25)
    assert all(abs(a - b) >= 25 for i, a in enumerate(kept) for b in kept[i + 1:])
    assert kept[0] == 0


def test_binom():
    assert cs.binom_two_sided(5, 10, 0.5) == pytest.approx(1.0)
    assert cs.binom_two_sided(10, 10, 0.5) == pytest.approx(2 / 1024)


def test_real_history_runs():
    try:
        s = cs.load_history("NDX.INDX", "1h")
    except FileNotFoundError:
        pytest.skip("arşiv yok")
    q = cs._slice(s, len(s.ts) - 50, len(s.ts))
    res = cs.build_response("NDX.INDX", "1h", 50, 20, s, q, "arsiv_sonu", int(q.ts[0]))
    assert len(res["matches"]) == 20 and res["matches"][0]["similarity"] > 0
    assert all(m["end"] < res["query"]["start"] for m in res["matches"])
