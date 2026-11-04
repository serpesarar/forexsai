"""capali_kur.py — PROTOCOL.md §4'teki TÜM konfigürasyonları kurar (özellik, sorgu anı, sonuç, kütüphane, komşular).

Çıktı: results/aile_kur.pkl  (liste: her öğe bir konfig sözlüğü)
Çalıştır: nice -n 10 python3.13 research/mum_derin_tarama_20261013/capali/capali_kur.py
Sonuç değerlerine yalnız "geçerli mi (NaN değil mi)" için bakılır; isabet hesaplanmaz.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import pickle
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capali_veri import HERE, HOLD_NS, NSMIN, Grid, load_daily, local_min, outcome, utc_ns  # noqa: E402

OUT = HERE / "results"
MIN_LIB = 100
KMAX = 50
OPEN, T10, T1500, T1530, T1600 = 570, 600, 900, 930, 960


# ───────────────────────── komşu motoru ─────────────────────────
def knn_prefix(X: np.ndarray, L: np.ndarray, kmax: int = KMAX) -> np.ndarray:
    """Olaylar bitişe göre sıralı; q'nun kütüphanesi [0, L_q). L_q ≥ MIN_LIB olanlar için en yakın kmax (uzaklık sırasıyla)."""
    Q = len(X)
    NB = np.full((Q, kmax), -1, dtype=np.int32)
    X = X.astype(np.float64)
    sq = (X ** 2).sum(1)
    rows = np.flatnonzero(L >= MIN_LIB)
    for a in range(0, len(rows), 512):
        r = rows[a:a + 512]
        D = sq[r, None] + sq[None, :] - 2.0 * X[r] @ X.T
        D[np.arange(Q)[None, :] >= L[r, None]] = np.inf
        p = np.argpartition(D, kmax, axis=1)[:, :kmax]
        dp = np.take_along_axis(D, p, 1)
        o = np.argsort(dp, axis=1, kind="stable")
        NB[r] = np.take_along_axis(p, o, 1)
    return NB


def finalize(cfg: dict, G, X: np.ndarray | None, call: np.ndarray | None) -> list[dict]:
    """Sonucu hesapla, geçersizleri at, bitişe göre sırala, kütüphane L ve komşuları kur. K∈{20,50} → iki konfig (kNN)."""
    y, t_end = outcome(G, cfg["day"], cfg["refmin"], cfg["hz"])
    ok = np.isfinite(y) & (cfg["tq"] < t_end) & (t_end < HOLD_NS)
    if X is not None:
        ok &= np.isfinite(X).all(1)
    if call is not None:
        ok &= np.isfinite(call)
    idx = np.flatnonzero(ok)
    idx = idx[np.argsort(t_end[idx], kind="stable")]
    base = {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in cfg.items()}
    base["end"] = t_end[idx]
    base["L"] = np.searchsorted(base["end"], base["tq"], side="right")
    base["n_tf_days"] = len(G.days)
    out = []
    if X is not None:
        NB = knn_prefix(X[idx], base["L"])
        for K in (20, 50):
            c = dict(base); c["NB"] = NB[:, :K]; c["K"] = K; c["kind"] = "knn"
            c["name"] = f'{cfg["name"]}|K{K}'
            out.append(c)
    else:
        c = dict(base); c["call"] = call[idx]; c["kind"] = "rule"; c["K"] = 0
        out.append(c)
    return out


def mk(name, idea, tf, day, refmin, tq, hz, hzlab, **kw) -> dict:
    d = dict(name=f"{idea}|{tf}|{name}|{hzlab}", idea=idea, tf=tf, day=np.asarray(day, np.int64),
             refmin=np.broadcast_to(np.asarray(refmin, np.int64), np.shape(day)).copy(),
             tq=np.asarray(tq, np.int64), hz=hz, hzlab=hzlab)
    d.update(kw)
    return d


def day_ok(G: Grid) -> np.ndarray:
    return ~G.early & ~G.prev_early & (G.prev_dn > 0)


# ───────────────────────── (a) seans yolu ─────────────────────────
def build_a(G: Grid) -> list[dict]:
    out = []
    Ns = [15, 30, 60, 90] if G.m < 30 else [30, 60, 90]
    hzs = ([("h15", ("plus", 15))] if G.m <= 15 else []) + [("h60", ("plus", 60)), ("hROS", None), ("h1d", ("nextsame", None))]
    days = np.flatnonzero(day_ok(G))
    t0 = utc_ns(G.days[days], OPEN)
    for N in Ns:
        nb = N // G.m
        I = np.stack([G.at_start(t0 + k * G.m * NSMIN) for k in range(nb)], 1)
        good = (I >= 0).all(1)
        dd, II = days[good], I[good]
        O0 = G.o[II[:, 0]]
        P = np.concatenate([np.stack([G.h[II[:, k]] - O0, G.l[II[:, k]] - O0, G.c[II[:, k]] - O0], 1) for k in range(nb)], 1)
        tq = utc_ns(G.days[dd], OPEN + N)
        for norm, sc in (("atr", G.atr[dd]), ("pct", O0 / 100.0)):
            X = P / sc[:, None]
            for lab, hz in hzs:
                hz2 = hz if hz is not None else ("plus", T1600 - (OPEN + N))
                c = mk(f"N{N}|{norm}", "a", G.tf, dd, OPEN + N, tq, hz2, lab, N=N, norm=norm)
                out += finalize(c, G, X, None)
    return out


# ───────────────────────── (b) gece yolu ─────────────────────────
def on_features(G: Grid, dd: np.ndarray, q_min: int) -> tuple[np.ndarray, np.ndarray]:
    dn, pdn = G.days[dd], G.prev_dn[dd]
    CP = G.px(utc_ns(pdn, T1600))
    pts = [(pdn, 1020), (dn - 1, 1200), (dn - 1, 1380), (dn, 120), (dn, 240), (dn, 360), (dn, 480), (dn, 540)]
    if q_min == OPEN:
        pts.append((dn, OPEN))
    cols = [G.px_tol(utc_ns(a, m), 180) - CP for a, m in pts]
    a0 = np.searchsorted(G.st, utc_ns(pdn, T1600)); a1 = np.searchsorted(G.st, utc_ns(dn, q_min))
    hi = np.full(len(dd), np.nan); lo = np.full(len(dd), np.nan)
    for k in range(len(dd)):
        if a1[k] > a0[k]:
            hi[k] = G.h[a0[k]:a1[k]].max(); lo[k] = G.l[a0[k]:a1[k]].min()
    F = np.stack(cols + [hi - CP, lo - CP], 1)
    # son nokta kesin olmalı (sorgu anındaki fiyat)
    F[~np.isfinite(G.px(utc_ns(dn, q_min)))] = np.nan
    return F, CP


def build_b(G: Grid) -> list[dict]:
    out = []
    dd = np.flatnonzero(day_ok(G))
    q = OPEN if G.m <= 30 else 540
    F, CP = on_features(G, dd, q)
    hzs = {"15m": [("o15", 15), ("o60", 60)], "30m": [("o30", 30), ("o60", 60)], "1h": [("o60", 60), ("o120", 120)]}[G.tf]
    tq = utc_ns(G.days[dd], q)
    for norm, sc in (("atr", G.atr[dd]), ("pct", CP / 100.0)):
        X = F / sc[:, None]
        for lab, h in hzs:
            c = mk(f"{norm}", "b", G.tf, dd, q, tq, ("plus", h), lab, norm=norm)
            out += finalize(c, G, X, None)
    return out


# ───────────────────────── (c) MIM ─────────────────────────
def build_c(G: Grid) -> list[dict]:
    out = []
    dd = np.flatnonzero(day_ok(G))
    dn, pdn = G.days[dd], G.prev_dn[dd]
    CP = G.px(utc_ns(pdn, T1600))
    r1 = G.px(utc_ns(dn, T10)) - CP
    vix = G.prev_vix[dd]
    if G.tf != "1h":
        q, hz, lab = T1530, ("plus", 30), "LH30"
        r12 = G.px(utc_ns(dn, T1530)) - G.px(utc_ns(dn, T1500))
        s1, s12 = np.sign(r1), np.sign(r12)
        rules = {"c1_r1": s1, "c2_r1r12": np.where((s1 == s12) & np.isfinite(r12), s1, 0.0),
                 "c4_r1r12_vix20": np.where((s1 == s12) & np.isfinite(r12) & (vix >= 20), s1, 0.0)}
        # analog: boşluk + ilk yarım saatin barları
        nb = 30 // G.m
        I = np.stack([G.at_start(utc_ns(dn, OPEN) + k * G.m * NSMIN) for k in range(nb)], 1)
        good = (I >= 0).all(1)
        Ic = np.where(I >= 0, I, 0)
        F = np.concatenate([(G.o[Ic[:, 0]] - CP)[:, None]] +
                           [np.stack([G.h[Ic[:, k]] - CP, G.l[Ic[:, k]] - CP, G.c[Ic[:, k]] - CP], 1) for k in range(nb)], 1)
        F[~good] = np.nan
    else:
        q, hz, lab = T1500, ("plus", 60), "LH60"
        s1 = np.sign(r1)
        rules = {"c1_r1": s1, "c4h_r1_vix20": np.where(vix >= 20, s1, 0.0)}
        i9 = G.at_start(utc_ns(dn, 540))
        ic = np.where(i9 >= 0, i9, 0)
        F = np.stack([G.px(utc_ns(dn, 540)) - CP, G.h[ic] - CP, G.l[ic] - CP, G.c[ic] - CP], 1)
        F[i9 < 0] = np.nan
    tq = utc_ns(dn, q)
    for rn, call in rules.items():
        call = np.where(np.isfinite(r1), call, np.nan)
        c = mk(rn, "c", G.tf, dd, q, tq, hz, lab, rule=rn)
        out += finalize(c, G, None, call)
    for norm, sc in (("atr", G.atr[dd]), ("pct", CP / 100.0)):
        c = mk(f"c3_analog|{norm}", "c", G.tf, dd, q, tq, hz, lab, norm=norm)
        out += finalize(c, G, F / sc[:, None], None)
    return out


# ───────────────────────── (d) olay tetikli ─────────────────────────
def dedup_60(ix: np.ndarray, st: np.ndarray) -> np.ndarray:
    kept, last = [], -10 ** 19
    for i in ix.tolist():
        if st[i] >= last + 60 * NSMIN:
            kept.append(i); last = st[i]
    return np.array(kept, dtype=np.int64)


def build_d(G: Grid) -> list[dict]:
    out = []
    n = len(G.st)
    di = G.day_index_of(G.st)
    okd = np.zeros(len(G.days), bool); okd[:] = day_ok(G)
    in_day = (di >= 0) & okd[np.maximum(di, 0)]
    lm = np.where(di >= 0, local_min(G.days[np.maximum(di, 0)], G.st), -1)
    rng_ = G.h - G.l
    win = in_day & (lm >= 600) & (lm < 930) & np.isfinite(G.batr) & (G.batr > 0)
    hi20 = np.full(n, np.inf); lo20 = np.full(n, -np.inf)
    import pandas as pd
    hi20[:] = pd.Series(G.h).rolling(20).max().shift(1).to_numpy()
    lo20[:] = pd.Series(G.l).rolling(20).min().shift(1).to_numpy()
    span_ok = np.zeros(n, bool); span_ok[20:] = (G.st[20:] - G.st[:-20]) <= 3 * 1440 * NSMIN
    types = {
        "E2": win & (rng_ >= 2 * G.batr),
        "E3": win & (rng_ >= 3 * G.batr),
        "HI20": win & span_ok & (G.c > hi20),
        "LO20": win & span_ok & (G.c < lo20),
    }
    # GAP: 09:30 barı, |O − C_P| ≥ 0,5 × günlük ATR
    dd = np.flatnonzero(okd)
    i930 = G.at_start(utc_ns(G.days[dd], OPEN))
    CP = G.px(utc_ns(G.prev_dn[dd], T1600))
    gapv = np.where(i930 >= 0, G.o[np.maximum(i930, 0)] - CP, np.nan)
    gsel = (i930 >= 0) & (np.abs(gapv) >= 0.5 * G.atr[dd]) & np.isfinite(G.batr[np.maximum(i930, 0)])
    gap_bar = np.zeros(n, bool); gap_bar[i930[gsel]] = True
    gap_feat = np.full(n, np.nan); gap_feat[i930[gsel]] = (gapv / G.atr[dd])[gsel]
    types["GAP"] = gap_bar
    hz_list = ([("p15", ("plus", 15))] if G.m <= 15 else []) + [("p60", ("plus", 60)), ("p1d", ("nextsame", None))]
    for tp, mask in types.items():
        ev = dedup_60(np.flatnonzero(mask), G.st)
        for m in (1, 3, 5):
            e = ev[ev + m < n]
            e = e[(G.st[e + m] - G.st[e]) == m * G.m * NSMIN]
            Oe, Ae = G.o[e], G.batr[e]
            F = np.concatenate([np.stack([(G.h[e + k] - Oe) / Ae, (G.l[e + k] - Oe) / Ae, (G.c[e + k] - Oe) / Ae], 1)
                                for k in range(m + 1)], 1)
            if tp == "GAP":
                F = np.concatenate([gap_feat[e][:, None], F], 1)
            tq = G.en[e + m]
            day = di[e]
            refmin = local_min(G.days[day], tq)
            for lab, hz in hz_list:
                c = mk(f"{tp}|m{m}", "d", G.tf, day, refmin, tq, hz, lab, etype=tp, m=m)
                out += finalize(c, G, F, None)
    return out


# ───────────────────────── (f) kapanış baskısı dönüşü ─────────────────────────
def build_f(G: Grid) -> list[dict]:
    out = []
    dd = np.flatnonzero(day_ok(G))
    dn = G.days[dd]
    p16 = G.px(utc_ns(dn, T1600))
    a = T1530 if G.tf != "1h" else T1500
    rl = p16 - G.px(utc_ns(dn, a))
    # nedensel %67 eşik: önceki günlerin |r_last|'i (≥100 gün)
    ab = np.abs(rl); thr = np.full(len(dd), np.nan)
    for k in range(len(dd)):
        prev = ab[:k][np.isfinite(ab[:k])]
        if len(prev) >= 100:
            thr[k] = np.quantile(prev, 0.67)
    f1 = -np.sign(rl)
    f2 = np.where(ab >= thr, f1, 0.0); f2 = np.where(np.isfinite(thr) & np.isfinite(rl), f2, np.nan)
    if G.tf != "1h":
        hzs = [("pc", ("plus", 60)), ("on", ("next", OPEN)), ("om", ("next", 630))]
    else:
        hzs = [("pc", ("plus", 60)), ("on", ("next", 540)), ("om", ("next", 600))]
    tq = utc_ns(dn, T1600)
    for lab, hz in hzs:
        for rn, call in (("f1_rev", f1), ("f2_rev_strong", f2)):
            c = mk(rn, "f", G.tf, dd, T1600, tq, hz, lab, rule=rn)
            out += finalize(c, G, None, np.where(np.isfinite(rl), call, np.nan))
    if G.tf in ("15m", "30m", "1h"):
        nb = 60 // G.m
        I = np.stack([G.at_start(utc_ns(dn, T1500) + k * G.m * NSMIN) for k in range(nb)], 1)
        good = (I >= 0).all(1); Ic = np.where(I >= 0, I, 0)
        p15 = G.px(utc_ns(dn, T1500))
        F = np.concatenate([np.stack([G.h[Ic[:, k]] - p15, G.l[Ic[:, k]] - p15, G.c[Ic[:, k]] - p15], 1)
                            for k in range(nb)], 1) / G.atr[dd][:, None]
        F[~good] = np.nan
        for lab, hz in hzs:
            c = mk("f3_analog|atr", "f", G.tf, dd, T1600, tq, hz, lab, norm="atr")
            out += finalize(c, G, F, None)
    return out


# ───────────────────────── (e) günlük ─────────────────────────
def build_e(daily) -> list[dict]:
    out = []
    O, H, Lw, C, A = (daily[k].to_numpy(float) for k in ("O", "H", "L", "C", "ATR"))
    n = len(O)
    i = np.arange(n)
    OC = C - O
    OO = np.r_[O[1:] - O[:-1], np.nan]
    for Lb in (1, 3):
        cols = []
        for b in range(1, Lb + 1):
            j = i - b; jj = np.maximum(j - 1, 0); jc = np.maximum(j, 0)
            pc = np.where(j - 1 >= 0, C[jj], np.nan)
            cols += [np.where(j >= 0, O[jc], np.nan) - pc, np.where(j >= 0, H[jc], np.nan) - pc,
                     np.where(j >= 0, Lw[jc], np.nan) - pc, np.where(j >= 0, C[jc], np.nan) - pc]
        gap = O - np.r_[np.nan, C[:-1]]
        P = np.stack(cols + [gap], 1)
        for norm, sc in (("atr", A), ("pct", np.r_[np.nan, C[:-1]] / 100.0)):
            X = P / sc[:, None]
            for lab, yy, off in (("OC", OC, 0.5), ("OO", OO, 1.0)):
                ok = np.isfinite(X).all(1) & np.isfinite(yy)
                idx = np.flatnonzero(ok)
                tq = i[idx].astype(float); end = tq + off
                o_ = np.argsort(end, kind="stable"); idx, tq, end = idx[o_], tq[o_], end[o_]
                Lq = np.searchsorted(end, tq, side="right")
                NB = knn_prefix(X[idx], Lq)
                base = dict(idea="e", tf="1d", day=idx, tq=tq, end=end, L=Lq, hzlab=lab, Lb=Lb, norm=norm,
                            yall=yy, n_tf_days=n, refmin=np.zeros(len(idx), np.int64), hz=("daily", lab))
                for K in (20, 50):
                    c = dict(base); c["NB"] = NB[:, :K]; c["K"] = K; c["kind"] = "knn"
                    c["name"] = f"e|1d|L{Lb}|{norm}|{lab}|K{K}"
                    out.append(c)
    return out


def main() -> None:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    daily = load_daily()
    fam: list[dict] = []
    for tf in ("5m", "15m", "30m", "1h"):
        G = Grid(tf, daily)
        print(f"{tf}: {len(G.st)} bar, {len(G.days)} gün  {G.days[0]}→{G.days[-1]}", flush=True)
        if tf in ("5m", "15m", "30m"):
            fam += build_a(G); print(f"  a ok ({len(fam)})", flush=True)
            fam += build_d(G); print(f"  d ok ({len(fam)})", flush=True)
        if tf in ("15m", "30m", "1h"):
            fam += build_b(G); print(f"  b ok ({len(fam)})", flush=True)
        fam += build_c(G); print(f"  c ok ({len(fam)})", flush=True)
        fam += build_f(G); print(f"  f ok ({len(fam)})", flush=True)
    fam += build_e(daily)
    for c in fam:
        assert (c["end"] > c["tq"]).all()
        if c["tf"] != "1d":
            assert (c["end"] < HOLD_NS).all()
    with open(OUT / "aile_kur.pkl", "wb") as f:
        pickle.dump(fam, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"{len(fam)} konfig, {time.time() - t0:.0f} sn")


if __name__ == "__main__":
    main()
