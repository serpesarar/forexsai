"""(sembol, TF) hücresi: her ufuk için L1/L2/L3 madenciliği + boş eşik + bölme kararı (PROTOCOL §4–§7)."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

import config as C
import data
import engine as E
import indicators

SPLIT_NAMES = ("KESIF", "DOGRULAMA", "KASA")


def _excl(names, ind):
    """Aynı göstergeden türeyen çiftler birleşmez; L1 sütunu (0) hiç dışlanmaz."""
    ii = np.r_[ind, ind]
    ex = ind[:, None] == ii[None, :]
    return np.hstack([np.zeros((len(ind), 1), bool), ex])


def _xname(j, names):
    if j == 0:
        return None
    j -= 1
    ns = len(names)
    return f"S:{names[j]}" if j < ns else f"R:{names[j - ns]}"


def _events(Th, X, i, j, extra=None, rows=None):
    m = Th[:, i] & X[:, j]
    if extra is not None:
        m &= X[:, extra]
    idx = np.flatnonzero(m)
    return idx if rows is None else idx[idx < rows]


def _select(cands, Th, X, disc_end):
    """KEŞİF |z| sırasıyla ilk K; olay kümesi seçilmişle ≥%80 örtüşen atlanır."""
    chosen, sets = [], []
    for c in cands:
        ev = set(_events(Th, X, c["i"], c["j"], c.get("k"), disc_end).tolist())
        if not ev:
            continue
        if any(len(ev & s) / min(len(ev), len(s)) >= C.DEDUP_OVERLAP for s in sets):
            continue
        chosen.append(c)
        sets.append(ev)
        if len(chosen) >= C.TOP_K:
            break
    return chosen


def _l3(top2, Th, X, W, ind, names, n_min):
    """En iyi L2 kombinasyonlarını üçüncü bir durumla genişlet (yalnız KEŞİF seçimi)."""
    ind_x = np.array([""] + list(ind) + list(ind), dtype=object)
    out = []
    for c in top2:
        idx = _events(Th, X, c["i"], c["j"])
        if len(idx) == 0:
            continue
        A3 = (W[idx].T @ X[idx].astype(np.float64)).T          # (nX, 24) — ağırlık ekseni sonda
        g = E.split_stats(A3, 0)
        bad = (np.arange(len(ind_x)) == 0) | (ind_x == ind[c["i"]]) | (ind_x == ind_x[c["j"]])
        z = np.where(bad | (g["n"] < n_min), 0, g["z"])
        for k in np.argsort(-np.abs(z))[:5]:
            if z[k] != 0:
                out.append(dict(i=c["i"], j=c["j"], k=int(k), zd=float(z[k]), vec=A3[k]))
    return out


def _row(c, names, vec, cost, h, level, n_min):
    """Seçilen kombinasyonun üç bölmedeki sonuçları."""
    d = np.sign(c["zd"])
    row = dict(h=h, level=level, combo=" & ".join(x for x in (f"T:{names[c['i']]}", _xname(c["j"], names),
                                                                _xname(c["k"], names) if "k" in c else None) if x),
               dir="BUY" if d > 0 else "SELL")
    for s, sn in enumerate(SPLIT_NAMES):
        g = E.split_stats(vec, s)
        r = E.directional(g, np.array(d), cost[s])
        for key in ("n", "z", "hit", "base", "lift", "ret_bp", "cost_bp"):
            row[f"{sn}_{key}"] = float(np.asarray(r[key]).ravel()[0])
    row["val_ok"] = row["DOGRULAMA_z"] >= C.Z_PASS and row["DOGRULAMA_n"] >= n_min / 4
    row["test_ok"] = (row["KASA_z"] >= C.Z_PASS and row["KASA_n"] >= n_min / 4 and row["KASA_lift"] >= C.LIFT_MIN
                      and row["KASA_ret_bp"] > row["KASA_cost_bp"])
    row["kanitli"] = bool(row["val_ok"] and row["test_ok"])
    row["val_wrong"] = row["DOGRULAMA_z"] <= -C.Z_PASS
    row["test_wrong"] = row["KASA_z"] <= -C.Z_PASS
    return row


def run_h(d, tf, h, Th_raw, X, names, ind, excl, rng, cost_px):
    n_min = C.N_MIN[tf]
    L = E.labels(d, data.bucket(d, tf), h, cost_px)
    W = E.weights(L)
    Th = E.thin(Th_raw, h)
    A = E.pair_sums(Th, X, W).transpose(0, 2, 1)           # (nt, nX, 24) — ağırlık ekseni sonda
    g0 = E.split_stats(A, 0)
    z0 = np.where((g0["n"] >= n_min) & ~excl, g0["z"], 0)
    order = np.dstack(np.unravel_index(np.argsort(-np.abs(z0), axis=None), z0.shape))[0]
    l12 = [dict(i=int(i), j=int(j), zd=float(z0[i, j])) for i, j in order[: 4000] if z0[i, j] != 0]
    top2 = [c for c in l12 if c["j"] != 0][: C.L3_EXPAND]
    l3 = _l3(top2, Th, X, W, ind, names, n_min)
    pool = sorted(l12 + l3, key=lambda c: -abs(c["zd"]))
    disc_end = int(np.flatnonzero(L["split"] == 0).max()) + 1
    chosen = _select(pool, Th, X, disc_end)
    thr, maxes = E.null_threshold(Th, X, L, excl, n_min, rng, ind)
    rows = []
    for c in chosen:
        vec = c["vec"] if "k" in c else A[c["i"], c["j"]]
        level = "L3" if "k" in c else ("L1" if c["j"] == 0 else ("L2b" if c["j"] > len(names) else "L2a"))
        r = _row(c, names, vec, L["cost"], h, level, n_min)
        r["kesif_secimden_sag"] = bool(np.isfinite(thr) and abs(c["zd"]) >= thr)
        rows.append(r)
    null = dict(h=h, thr95=thr, null_max=maxes, pool=int((z0 != 0).sum()), pool_over_thr=int((np.abs(z0) >= thr).sum()) if np.isfinite(thr) else 0,
                l3_over_thr=int(sum(abs(c["zd"]) >= thr for c in l3)) if np.isfinite(thr) else 0)
    return rows, null, L


def run_cell(sym: str, tf: str) -> dict:
    t0 = time.time()
    d = data.load(sym, tf)
    book = indicators.compute(d, tf)
    names, Sm, T, Rm, ind = E.matrices(book)
    X = E.x_matrix(Sm, Rm)
    excl = _excl(names, ind)
    rng = np.random.default_rng(C.SEED)
    out_dir = C.RES / sym / tf
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows, nulls = [], []
    for h in C.HORIZONS:
        rows, null, _ = run_h(d, tf, h, T, X, names, ind, excl, rng, C.SPREAD[sym])
        all_rows += rows
        nulls.append(null)
        print(f"  {sym} {tf} h={h}: eşik {null['thr95']:.2f}, havuz {null['pool']}, eşik üstü {null['pool_over_thr']}, "
              f"kanıtlı {sum(r['kanitli'] for r in rows)}  ({time.time() - t0:.0f}s)", flush=True)
    pd.DataFrame(all_rows).to_csv(out_dir / "cells.csv", index=False)
    json.dump(dict(sym=sym, tf=tf, bars=len(d), start=str(d.ts.iloc[0]), end=str(d.ts.iloc[-1]),
                   split_start=[str(d.ts[d.split == s].iloc[0]) for s in range(3)], n_states=len(names),
                   n_feats=len(book.feats), nulls=nulls, seconds=round(time.time() - t0, 1)),
              open(out_dir / "meta.json", "w"), indent=1)
    return dict(sym=sym, tf=tf, rows=all_rows, nulls=nulls)
