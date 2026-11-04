"""Literal mum eşleştirme — Faz B değerlendirmesi (ön-kayıt PROTOCOL.md).

  python3 evaluate.py family     # tüm aile → results/aile.csv + çağrı matrisleri (aktif yapılandırmalar)
  python3 evaluate.py null       # hafta kaydırmalı seçim-düzeltmesi null'u (200 tekrar) → results/null_max.csv
  python3 evaluate.py screen     # plasebo + bootstrap (ön-eleği geçenler) → results/aday_eleme.csv
"""
from __future__ import annotations

import sys
import time

import numba as nb
import numpy as np
import pandas as pd

from _lit import HZ, NC, NR, NX, RES, RULES, TOLS, XS, lib_lo, load, query_grid, rep_arrays

NMINS = (1, 5, 30)
AGREE = (False, True)
MIN_EVENTS = 200
TFS = ["1h", "15m", "5m", "1m"]
R_NULL = 200
WEEK = 7 * 86_400 * 10**9
MC_POOL = 1000
R_PLC = 20
B_BOOT = 2000


# ─────────────────────────── tabanlar ───────────────────────────
def base_rates(D: dict, qs: np.ndarray, lo: np.ndarray) -> tuple:
    nh, nq = len(D["hz"]), len(qs)
    P0 = np.full((nh, nq), np.nan); P0h = np.full((nh, nq), np.nan)
    cq = D["close"][qs]; hq = D["hour"][qs]
    for h in range(nh):
        y = D["yv"][h]; V = np.flatnonzero(np.isfinite(y) & (y != 0))
        endV = D["endT"][h, V]
        assert np.all(np.diff(endV) >= 0)
        up = (y[V] > 0)
        k_hi = np.searchsorted(endV, cq, side="right"); k_lo = np.minimum(np.searchsorted(V, lo), k_hi)
        cu = np.r_[0, np.cumsum(up)]
        nv = k_hi - k_lo
        P0[h] = np.where(nv > 0, (cu[k_hi] - cu[k_lo]) / np.maximum(nv, 1), np.nan)
        hv = D["hour"][V]
        for b in range(24):
            m = hv == b; sel = hq == b
            cn = np.r_[0, np.cumsum(m)]; cub = np.r_[0, np.cumsum(up & m)]
            nn = cn[k_hi[sel]] - cn[k_lo[sel]]
            P0h[h, sel] = np.where(nn > 0, (cub[k_hi[sel]] - cub[k_lo[sel]]) / np.maximum(nn, 1), np.nan)
    return P0, P0h


def call_of(p: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(p), np.sign(p - 0.5), 0).astype(np.int8)


def credit(call: np.ndarray, sy: np.ndarray) -> np.ndarray:
    """1 doğru, 0 yanlış, 0,5 çağrı yok (taban için)."""
    return np.where(call == 0, 0.5, (call == sy).astype(float))


@nb.njit(cache=True)
def greedy_events(order_t, order_end):
    cnt = 0; last = -1
    for i in range(order_t.shape[0]):
        if order_t[i] >= last:
            cnt += 1; last = order_end[i]
    return cnt


# ─────────────────────────── aile ───────────────────────────
def family() -> None:
    rows = []
    for tf in TFS:
        t0 = time.time()
        D = load(tf); qs = query_grid(D); lo = lib_lo(D, qs); nh = len(D["hz"]); nq = len(qs)
        P0, P0h = base_rates(D, qs, lo)
        tq = D["close"][qs]; half_t = np.median(tq)
        Y = D["yv"][:, qs]; SY = np.sign(np.nan_to_num(Y)).astype(np.int8); ENDQ = D["endT"][:, qs]
        B0 = np.stack([call_of(P0[h]) for h in range(nh)]); BH = np.stack([call_of(P0h[h]) for h in range(nh)])
        np.savez(RES / f"q_{tf}.npz", qs=qs, tq=tq, Y=Y, ENDQ=ENDQ, B0=B0, BH=BH, P0=P0, P0h=P0h)
        calls_store = []; meta_store = []
        for ti, (rep, tol) in enumerate(TOLS):
            Z = np.load(RES / "scan" / f"{tf}_{ti}.npz")
            up, dn, nind, nraw = (Z[k].astype(np.int64) for k in ("up", "dn", "nind", "nraw"))
            qelig, qvalid = Z["qelig"], Z["qvalid"]
            for h in range(nh):
                sy = SY[h]; okq = np.isfinite(Y[h]) & (sy != 0)
                c0 = credit(B0[h], sy); ch = credit(BH[h], sy)
                for xi, X in enumerate(XS):
                    for r, (rn, _, _) in enumerate(RULES):
                        for c in range(NC):
                            qm = qvalid[:, xi] & (qelig[:, xi] if c & 1 else True)
                            u_, d_ = up[:, h, xi, r, c], dn[:, h, xi, r, c]
                            n_ = u_ + d_
                            u = np.where(n_ > 0, u_ / np.maximum(n_, 1), np.nan)
                            raw_med = float(np.median(nraw[qm, h, xi, r, c])) if qm.any() else np.nan
                            ind_med = float(np.median(nind[qm, h, xi, r, c])) if qm.any() else np.nan
                            for nmin in NMINS:
                                for ag in AGREE:
                                    has = qm & (n_ >= nmin)
                                    if ag:
                                        call = np.where(has & (u >= 0.7), 1, np.where(has & (u <= 0.3), -1, 0))
                                    else:
                                        call = np.where(has & (u > 0.5), 1, np.where(has & (u < 0.5), -1, 0))
                                    call = call.astype(np.int8)
                                    sc = (call != 0) & okq
                                    ns = int(sc.sum())
                                    row = dict(tf=tf, rep=rep, tol=tol, X=int(X), kural=rn, uygunluk=bool(c & 1),
                                               seans=bool(c & 2), ufuk=D["hz"][h], n_min=nmin, guclu_oy=ag,
                                               uygun_sorgu=int((qm & okq).sum()), cagri=ns,
                                               ham_med=raw_med, bag_med=ind_med)
                                    if ns > 0:
                                        idx = np.flatnonzero(sc)
                                        ev = greedy_events(tq[idx], ENDQ[h, idx])
                                        corr = (call[idx] == sy[idx]).astype(float)
                                        a, a0, ah = corr.mean(), c0[idx].mean(), ch[idx].mean()
                                        h1 = tq[idx] < half_t
                                        def ex(m):  # noqa: E306
                                            if m.sum() == 0:
                                                return np.nan
                                            return 100 * (corr[m].mean() - max(c0[idx][m].mean(), ch[idx][m].mean()))
                                        row.update(bag_olay=ev, isabet=100 * a, taban_cogunluk=100 * a0, taban_saat=100 * ah,
                                                   fazla=100 * (a - max(a0, ah)), yari1=ex(h1), yari2=ex(~h1),
                                                   hareket_puan=float(np.mean(call[idx] * Y[h, idx])),
                                                   ort_komsu=float(n_[idx].mean()), yukari_cagri_pay=float((call[idx] > 0).mean()))
                                        if ev >= MIN_EVENTS:
                                            row["cid"] = len(meta_store)
                                            calls_store.append(call); meta_store.append(h)
                                    else:
                                        row.update(bag_olay=0)
                                    rows.append(row)
            print(tf, rep, tol, f"{time.time() - t0:.0f}s", flush=True)
        C = np.stack(calls_store) if calls_store else np.zeros((0, nq), np.int8)
        np.savez(RES / f"calls_{tf}.npz", C=C, H=np.array(meta_store, np.int8))
        print(tf, "aktif yapılandırma", len(C), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(RES / "aile.csv", index=False)
    print("aile", len(df), "aktif", int(df.cid.notna().sum()))


# ─────────────────────────── null ───────────────────────────
def shifted_sign(D: dict, tq: np.ndarray, W: int, h: int) -> np.ndarray:
    t0 = tq[0]; nW = int((tq[-1] - t0) // WEEK) + 1
    T = t0 + (tq - t0 + W * WEEK) % (nW * WEEK)
    j = np.searchsorted(D["close"], T)
    jj = np.clip(j, 0, D["n"] - 1)
    ok = D["close"][jj] == T
    y = np.where(ok, D["yv"][h, jj], np.nan)
    return np.sign(np.nan_to_num(y)).astype(np.int8)


def null() -> None:
    fam = pd.read_csv(RES / "aile.csv")
    rng = np.random.default_rng(777)
    weeks = rng.integers(2, 10**6, size=R_NULL)            # her TF'de mod (nW−4) + 2
    best = np.full((R_NULL, len(TFS)), -np.inf); bestz = np.full((R_NULL, len(TFS)), -np.inf)
    for ti_, tf in enumerate(TFS):
        t0 = time.time()
        D = load(tf); Q = np.load(RES / f"q_{tf}.npz"); Z = np.load(RES / f"calls_{tf}.npz")
        C, Hc = Z["C"], Z["H"]; tq = Q["tq"]
        f = fam[(fam.tf == tf) & fam.cid.notna()].sort_values("cid")
        ev = f.bag_olay.to_numpy(float)
        nW = int((tq[-1] - tq[0]) // WEEK) + 1
        for h in np.unique(Hc):
            rows_h = np.flatnonzero(Hc == h)
            S = np.stack([shifted_sign(D, tq, int(2 + w % max(nW - 4, 1)), h) for w in weeks], 1)   # nq × R
            Sp = (S == 1).astype(np.float32); Sn = (S == -1).astype(np.float32); Snz = Sp + Sn
            bcs = [((B[:, None] == S) & (S != 0)).astype(np.float32) + 0.5 * ((B[:, None] == 0) & (S != 0))
                   for B in (Q["B0"][h], Q["BH"][h])]
            for k0 in range(0, len(rows_h), 3000):
                rows = rows_h[k0:k0 + 3000]
                Cp = (C[rows] == 1).astype(np.float32); Cn = (C[rows] == -1).astype(np.float32); Cz = Cp + Cn
                corr = Cp @ Sp + Cn @ Sn; called = np.maximum(Cz @ Snz, 1)
                acc = corr / called
                exc = 100 * (acc - np.maximum((Cz @ bcs[0]) / called, (Cz @ bcs[1]) / called))
                z = exc / 100 / (0.5 / np.sqrt(ev[rows][:, None]))
                best[:, ti_] = np.maximum(best[:, ti_], exc.max(0)); bestz[:, ti_] = np.maximum(bestz[:, ti_], z.max(0))
        print(tf, "null", f"{time.time() - t0:.0f}s", flush=True)
    out = pd.DataFrame({"rep": np.arange(R_NULL), "max_fazla": best.max(1), "max_z": bestz.max(1),
                        **{f"max_fazla_{tf}": best[:, i] for i, tf in enumerate(TFS)}})
    out.to_csv(RES / "null_max.csv", index=False)
    print(out.describe().round(3).to_string())


# ─────────────────────────── eleme: plasebo + bootstrap ───────────────────────────
def pool_rate(D: dict, qs: np.ndarray, lo: np.ndarray, rep: str, tol: float, xi: int, c: int, h: int,
              rng: np.random.Generator) -> np.ndarray:
    _, invA, medR = rep_arrays(D, rep)
    nq = len(qs); X = XS[xi]
    U = rng.random((nq, MC_POOL))
    E = (lo[:, None] + (U * (qs - lo)[:, None]).astype(np.int64))
    ok = (D["endT"][h][E] <= D["close"][qs][:, None]) & (E - D["seg_start"][E] + 1 >= X) & np.isfinite(invA[E])
    if c & 1:
        ok &= medR[xi][E] * invA[E] >= 3 * tol
    if c & 2:
        dh = np.abs(D["hour"][E].astype(int) - D["hour"][qs][:, None].astype(int)); dh = np.minimum(dh, 24 - dh)
        ok &= dh <= 1
    y = D["yv"][h][E]
    ok &= np.isfinite(y) & (y != 0)
    nup = ((y > 0) & ok).sum(1); nn = ok.sum(1)
    return np.where(nn > 0, nup / np.maximum(nn, 1), np.nan)


def block_boot(diff: np.ndarray, block: np.ndarray, rng: np.random.Generator) -> float:
    u, inv = np.unique(block, return_inverse=True)
    S = np.bincount(inv, diff); N = np.bincount(inv)
    idx = rng.integers(0, len(u), size=(B_BOOT, len(u)))
    bm = S[idx].sum(1) / N[idx].sum(1)
    return float((bm > 0).mean())


def screen() -> None:
    fam = pd.read_csv(RES / "aile.csv")
    pre = fam[(fam.bag_olay >= MIN_EVENTS) & (fam.fazla > 0)].copy()
    print("ön-elek (≥200 olay ve fazla > 0):", len(pre))
    rng = np.random.default_rng(99)
    out = []
    tol_idx = {(r, t): i for i, (r, t) in enumerate(TOLS)}
    for tf, g in pre.groupby("tf"):
        D = load(tf); Q = np.load(RES / f"q_{tf}.npz"); qs = Q["qs"]; lo = lib_lo(D, qs); tq = Q["tq"]
        hz = list(HZ[tf]); half_t = np.median(tq)
        cache_pool = {}; cache_scan = {}
        g = g.sort_values(["rep", "tol", "X", "uygunluk", "seans", "ufuk"])
        for _, row in g.iterrows():
            h = hz.index(row.ufuk); xi = int(np.flatnonzero(XS == row.X)[0])
            r = [x[0] for x in RULES].index(row.kural); c = int(row.uygunluk) + 2 * int(row.seans)
            ti = tol_idx[(row.rep, row.tol)]
            if ti not in cache_scan:
                cache_scan = {ti: np.load(RES / "scan" / f"{tf}_{ti}.npz")}
            Z = cache_scan[ti]
            u_, d_ = Z["up"][:, h, xi, r, c].astype(int), Z["dn"][:, h, xi, r, c].astype(int); n_ = u_ + d_
            qm = Z["qvalid"][:, xi] & (Z["qelig"][:, xi] if c & 1 else True)
            u = np.where(n_ > 0, u_ / np.maximum(n_, 1), np.nan)
            has = qm & (n_ >= row.n_min)
            if row.guclu_oy:
                call = np.where(has & (u >= 0.7), 1, np.where(has & (u <= 0.3), -1, 0))
            else:
                call = np.where(has & (u > 0.5), 1, np.where(has & (u < 0.5), -1, 0))
            Y = Q["Y"][h]; sy = np.sign(np.nan_to_num(Y)); sc = (call != 0) & np.isfinite(Y) & (sy != 0)
            idx = np.flatnonzero(sc)
            key = (ti, xi, c, h)
            if key not in cache_pool:
                cache_pool[key] = pool_rate(D, qs, lo, row.rep, row.tol, xi, c, h, rng)
            pp = cache_pool[key][idx]; nn = n_[idx]
            k = rng.binomial(np.repeat(nn[None, :], R_PLC, 0), np.nan_to_num(np.repeat(pp[None, :], R_PLC, 0), nan=0.5))
            uu = k / np.maximum(nn, 1)
            if row.guclu_oy:
                pc = np.where(uu >= 0.7, 1, np.where(uu <= 0.3, -1, 0))
            else:
                pc = np.where(uu > 0.5, 1, np.where(uu < 0.5, -1, 0))
            made = pc != 0
            plc = float(((pc == sy[idx][None, :]) & made).sum() / max(made.sum(), 1))
            c0 = credit(Q["B0"][h], sy)[idx]; ch = credit(Q["BH"][h], sy)[idx]
            corr = (call[idx] == sy[idx]).astype(float)
            base = c0 if c0.mean() >= ch.mean() else ch
            diff = corr - base
            bdays = 5 if row.ufuk == "1d" else 1
            blk = (tq[idx] // (86_400 * 10**9)) // bdays
            P = block_boot(diff, blk, rng)
            res = row.to_dict()
            res.update(plasebo=100 * plc, plasebo_gecer=bool(100 * corr.mean() > 100 * plc), boot_P=P,
                       aday=bool(row.bag_olay >= MIN_EVENTS and row.fazla >= 2.0 and 100 * corr.mean() > 100 * plc
                                 and P >= 0.975 and row.yari1 > 0 and row.yari2 > 0 and row.hareket_puan > 1.5))
            out.append(res)
        print(tf, "eleme", len(g), flush=True)
    o = pd.DataFrame(out)
    o.to_csv(RES / "aday_eleme.csv", index=False)
    print("adaylar (seçim düzeltmesi ÖNCESİ):", int(o.aday.sum()) if len(o) else 0)


if __name__ == "__main__":
    {"family": family, "null": null, "screen": screen}[sys.argv[1]]()
