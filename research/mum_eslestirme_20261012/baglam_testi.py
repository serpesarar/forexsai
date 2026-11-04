"""ME-03 — Bağlam ve çapraz-sembol eşleştirme testi (ön-kayıt: PROTOCOL_BAGLAM.md). SONUÇLAR BU BETİKLE ÜRETİLİR.

Mod 1 "baglam": komşular yalnız aynı bağlamdaki geçmiş anlardan seçilir (vix, stres, vix_stres, saat, oyn) ve
                 bağlamın KENDİ koşullu tabanıyla kıyaslanır. ctx="yok" = ME-02 V2 (şekil tek başına), eşli kıyas için.
Mod 2 "capraz": hedef sembolün şekli / ortak sembolün aynı andaki şekli / ikisi yan yana (12 sıralı çift × 30m/1h/4h/1d).
Değişmeyenler ME-02 ile aynı: R7 + P33, K=50, olay kopyaları kaldırılır (V2), kayan 5 y, j + H ≤ t, çıplak komşu oyu,
son 7 ay dokunulmaz, plasebo = aynı (süzülmüş) havuzdan rastgele komşu.
Çalıştır: python3 research/mum_eslestirme_20261012/baglam_testi.py baglam|capraz   (7 çekirdek)
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

from kaldirma_testi import (HERE, HS, K, LIB_DAYS, R_PLC, RESERVE_DAYS, ROOT, SRC, TF_MIN, derive, greedy_dedup,
                            load_tf, predict, pyramid, race_labels)

OUT = HERE / "results"
MACRO = ROOT / "research/ndx_gate_forge/data/macro_daily_patched.csv"
VIX_THR = 18.4
MIN_POOL = 10
CTXS = ("yok", "vix", "stres", "vix_stres", "saat", "oyn")
SYMS = ("NDX", "DAX", "XAU", "OIL")


# ─────────────────────────── ortak hazırlık ───────────────────────────
def prep(o, h, l, c, ts, tf):
    n = len(c)
    gap_after = np.r_[np.diff(ts) > np.timedelta64(4, "D"), False]
    gcum = np.r_[0, np.cumsum(gap_after)]
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    A = pd.Series(tr).rolling(14).mean().shift(1).to_numpy()
    raw = np.stack([h - o, l - o, c - o], 1)
    F7 = np.full((n, 21), np.nan)
    for k in range(7):
        F7[k:, 3 * k:3 * k + 3] = raw[:n - k] / A[k:, None]
    feats = {"R7": F7, "P33": pyramid(o, h, l, c, A).astype(float)}
    e = np.arange(n)
    valid = {}
    for rep, cov in (("R7", 7), ("P33", 33)):
        s = np.maximum(e - cov - 14, 0)
        valid[rep] = (gcum[e] - gcum[s] == 0) & (e >= cov + 14) & np.isfinite(A) & (A > 0) & np.isfinite(feats[rep]).all(1)
    outc, racel, ok = {}, {}, {}
    for H in HS[tf]:
        r = np.full(n, np.nan); r[:n - H] = (c[H:] - c[:n - H]) / A[:n - H]
        okH = np.zeros(n, bool); idx = np.arange(n - H)
        okH[:n - H] = (gcum[idx + H] - gcum[idx] == 0) & np.isfinite(r[:n - H])
        outc[H], racel[H], ok[H] = r, race_labels(c, h, l, A, H), okH
    return dict(n=n, A=A, feats=feats, valid=valid, outc=outc, racel=racel, ok=ok)


def query_index(ts_series: pd.Series, tf: str, P: dict) -> np.ndarray:
    n = len(ts_series)
    te = ts_series + pd.Timedelta(minutes=TF_MIN[tf])
    if tf in ("5m", "15m", "30m", "1h"):
        qm = ((te.dt.minute == 0) & (te.dt.hour % 4 == 0)).to_numpy()
    elif tf == "4h":
        qm = np.arange(n) % 6 == 0
    else:
        qm = np.ones(n, bool)
    Hmax = max(HS[tf])
    warm = pd.Timedelta(days=90 if tf == "5m" else 365)
    reserve_ts = ts_series.max() - pd.Timedelta(days=RESERVE_DAYS)
    end_ok = np.zeros(n, bool)
    end_ok[:n - Hmax] = (ts_series.iloc[Hmax:].reset_index(drop=True) <= reserve_ts).to_numpy()
    qm &= (ts_series >= ts_series.iloc[0] + warm).to_numpy() & end_ok & P["valid"]["P33"] & P["valid"]["R7"]
    return np.flatnonzero(qm)


def knn_select(dist, fin_mask_range, H, buf):
    fin = np.flatnonzero(np.isfinite(dist))
    if len(fin) == 0:
        return fin
    m = len(fin) if len(fin) <= 4000 else 4000
    cand = fin[np.argpartition(dist[fin], m - 1)[:m]] if m < len(fin) else fin
    cand = cand[np.argsort(dist[cand], kind="stable")]
    idx = greedy_dedup(cand, H, K, buf)
    if len(idx) < K and m < len(fin):
        idx = greedy_dedup(fin[np.argsort(dist[fin], kind="stable")], H, K, buf)
    return idx


def placebo(pool, nn, r, y, ar, rng):
    if nn == 0 or len(pool) == 0:
        return np.nan, np.nan, np.nan
    pick = pool[rng.integers(0, len(pool), size=(R_PLC, min(nn, 500)))]
    rr = r[pick]; pr = (rr > 0).mean(1)
    accs = np.where(pr == 0.5, 0.5, ((pr > 0.5) == (y > 0)).astype(float))
    return float(accs.mean()), float(((pr - float(y > 0)) ** 2).mean()), float(np.abs(np.median(np.abs(rr), 1) - ar).mean())


# ─────────────────────────── bağlamlar ───────────────────────────
def load_vix():
    m = pd.read_csv(MACRO, usecols=["date", "VIX_close"]).dropna()
    return pd.to_datetime(m.date).dt.date.to_numpy(), m.VIX_close.to_numpy(float)


def contexts(sym: str, d: pd.DataFrame, tf: str, A: np.ndarray, vix_dates, vix_vals) -> dict:
    n = len(d)
    te = d.ts + pd.Timedelta(minutes=TF_MIN[tf])
    ny_date = te.dt.tz_convert("America/New_York").dt.date.to_numpy()
    k = np.searchsorted(vix_dates, ny_date, side="left") - 1                  # önceki son işlem günü
    vix = np.where(k >= 0, (vix_vals[np.clip(k, 0, None)] >= VIX_THR).astype(int), -1)
    d1 = derive(load_tf(sym, "1h"), "1d")
    dc = d1.close.to_numpy(); dend = (d1.ts + pd.Timedelta(hours=25)).dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()  # bitiş ≤ başlangıç+25 s (DST payı, temkinli)
    r1 = np.r_[np.nan, dc[1:] / dc[:-1] - 1]; r5 = np.r_[np.full(5, np.nan), dc[5:] / dc[:-5] - 1]
    sd = ((r1 <= -0.015) | (r5 <= -0.04)).astype(int); sd[~np.isfinite(r5)] = -1
    kk = np.searchsorted(dend, te.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy(), side="right") - 1  # son TAMAMLANMIŞ gün
    stres = np.where(kk >= 0, sd[np.clip(kk, 0, None)], -1)
    hour = d.ts.dt.hour.to_numpy()
    bpd = n / max(1.0, (d.ts.iloc[-1] - d.ts.iloc[0]).days)                   # gün başına bar
    N = int(365 * bpd)
    medA = pd.Series(A).rolling(N, min_periods=max(50, N // 4)).median().shift(1).to_numpy()
    ratio = A / medA
    oyn = np.where(np.isfinite(ratio), np.digitize(ratio, [0.8, 1.25]), -1)
    vs = np.where((vix >= 0) & (stres >= 0), vix * 2 + stres, -1)
    return {"vix": vix, "stres": stres, "vix_stres": vs, "saat": hour, "oyn": oyn}


def run_ctx_cell(sym: str, tf: str) -> str:
    t0 = time.time(); rng = np.random.default_rng(zlib.crc32(f"ctx|{sym}|{tf}".encode()))
    d = load_tf(sym, tf)
    ts = d.ts.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
    o, h, l, c = (d[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    P = prep(o, h, l, c, ts, tf); n = P["n"]
    vd, vv = load_vix()
    CT = contexts(sym, d, tf, P["A"], vd, vv)
    Q = query_index(d.ts, tf, P)
    lo_all = np.searchsorted(ts, ts - np.timedelta64(LIB_DAYS, "D"))
    hour = CT["saat"]
    # önekler: koşulsuz + bağlam değerine göre
    pref = {}
    for H in HS[tf]:
        okH, r, rc = P["ok"][H], P["outc"][H], P["racel"][H]
        up = okH & (r > 0)
        pref[(H, "all")] = (np.r_[0, np.cumsum(okH)], np.r_[0, np.cumsum(up)],
                            np.r_[0, np.cumsum(okH & (rc == 1))], np.r_[0, np.cumsum(okH & (rc == -1))])
        for cname, arr in CT.items():
            for v in np.unique(arr[arr >= 0]):
                mv = arr == v
                pref[(H, cname, int(v))] = (np.r_[0, np.cumsum(okH & mv)], np.r_[0, np.cumsum(up & mv)],
                                            np.r_[0, np.cumsum(okH & mv & (rc == 1))], np.r_[0, np.cumsum(okH & mv & (rc == -1))])
    ctx_idx = {cname: {int(v): np.flatnonzero(arr == v) for v in np.unique(arr[arr >= 0])} for cname, arr in CT.items()}
    ok_idx = {H: np.flatnonzero(P["ok"][H]) for H in HS[tf]}
    Fz = {rep: np.nan_to_num(P["feats"][rep], nan=0.0).astype(np.float32) for rep in ("R7", "P33")}
    sq = {rep: (Fz[rep].astype(np.float64) ** 2).sum(1) for rep in Fz}
    rows = []; buf = np.zeros(n, bool); CH = 128

    def rate(key, a, b):
        cv, cu, ru, rd = pref[key]
        nv = cv[b + 1] - cv[a]; nr = (ru[b + 1] - ru[a]) + (rd[b + 1] - rd[a])
        return (nv, (cu[b + 1] - cu[a]) / nv if nv else np.nan, (ru[b + 1] - ru[a]) / nr if nr else np.nan)

    for c0 in range(0, len(Q), CH):
        qs = Q[c0:c0 + CH]
        D2 = {rep: sq[rep][:, None] + sq[rep][qs][None, :] - 2.0 * (Fz[rep] @ Fz[rep][qs].T).astype(np.float64) for rep in Fz}
        for ci, q in enumerate(qs):
            lo = lo_all[q]
            for H in HS[tf]:
                r, rc, okH = P["outc"][H], P["racel"][H], P["ok"][H]
                if not okH[q]:
                    continue
                hi0 = q - H
                if hi0 <= lo + 10:
                    continue
                y, ar, rq = r[q], abs(r[q]), int(rc[q])
                _, p0, prace0 = rate((H, "all"), lo, hi0)
                b = int(hour[q])
                hb = ctx_idx["saat"].get(b, np.array([], int)); hb = hb[(hb >= lo) & (hb <= hi0)]; hb = hb[okH[hb]]
                bmed_h = float(np.median(np.abs(r[rng.choice(hb, 1500)]))) if len(hb) else np.nan
                _, p0h, _ = rate((H, "saat", b), lo, hi0) if (H, "saat", b) in pref else (0, np.nan, np.nan)
                for rep in ("R7", "P33"):
                    cov = 7 if rep == "R7" else 33
                    hi1 = min(hi0, q - cov)
                    base_d = D2[rep][:, ci].copy()
                    base_d[~P["valid"][rep]] = np.inf; base_d[~okH] = np.inf
                    base_d[:lo] = np.inf; base_d[hi1 + 1:] = np.inf
                    for cname in CTXS:
                        if cname == "yok":
                            cv_ = -9; dist = base_d
                            p0c, prace0c, bmedc = p0, prace0, bmed_h
                            pool_all = ok_idx[H]
                        else:
                            cv_ = int(CT[cname][q])
                            if cv_ < 0 or (H, cname, cv_) not in pref:
                                continue
                            dist = base_d.copy(); dist[CT[cname] != cv_] = np.inf
                            nvc, p0c, prace0c = rate((H, cname, cv_), lo, hi0)
                            ci_ = ctx_idx[cname][cv_]; cb = ci_[(ci_ >= lo) & (ci_ <= hi0)]; cb = cb[okH[cb]]
                            bmedc = float(np.median(np.abs(r[rng.choice(cb, 1500)]))) if len(cb) else np.nan
                            pool_all = ci_[okH[ci_]]
                        idx = knn_select(dist, None, H, buf)
                        if len(idx) < MIN_POOL:
                            idx = idx[:0]
                        nn, pu, med, prace, _ = predict(idx, r, rc)
                        pool = pool_all[(pool_all >= lo) & (pool_all <= hi1)]
                        pa, pb, pe = placebo(pool, nn, r, y, ar, rng)
                        rows.append((sym, tf, H, int(q), int(pd.Timestamp(ts[q]).value), y, ar, rq, p0, p0h, prace0, bmed_h,
                                     rep, cname, cv_, p0c, prace0c, bmedc, nn, pu, med, prace, pa, pb, pe))
    df = pd.DataFrame(rows, columns=["sym", "tf", "H", "q", "ts", "y", "absr", "race", "p0", "p0h", "prace0", "bmed_h",
                                     "rep", "ctx", "cval", "p0c", "prace0c", "bmedc", "n", "pu", "med", "prace",
                                     "plc_acc", "plc_br", "plc_ae"])
    (OUT / "baglam").mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "baglam" / f"{sym}_{tf}.parquet")
    return f"baglam {sym} {tf}: sorgu={len(Q)} satır={len(df)} {time.time() - t0:.0f}s"


# ─────────────────────────── çapraz-sembol ───────────────────────────
def run_pair(tgt: str, par: str, tf: str) -> str:
    t0 = time.time(); rng = np.random.default_rng(zlib.crc32(f"pair|{tgt}|{par}|{tf}".encode()))
    a, b = load_tf(tgt, tf), load_tf(par, tf)
    m = a.merge(b, on="ts", suffixes=("", "_p")).sort_values("ts").reset_index(drop=True)
    ts = m.ts.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
    PA = prep(*(m[x].to_numpy(float) for x in ("open", "high", "low", "close")), ts, tf)
    PB = prep(*(m[x + "_p"].to_numpy(float) for x in ("open", "high", "low", "close")), ts, tf)
    n = PA["n"]
    valid = {rep: PA["valid"][rep] & PB["valid"][rep] for rep in ("R7", "P33")}
    PA_q = dict(PA); PA_q["valid"] = valid
    Q = query_index(m.ts, tf, PA_q)
    lo_all = np.searchsorted(ts, ts - np.timedelta64(LIB_DAYS, "D"))
    hour = m.ts.dt.hour.to_numpy()
    hidx = {hh: np.flatnonzero(hour == hh) for hh in range(24)}
    ok_idx = {H: np.flatnonzero(PA["ok"][H]) for H in HS[tf]}
    pref = {}
    for H in HS[tf]:
        okH, r = PA["ok"][H], PA["outc"][H]
        pref[H] = (np.r_[0, np.cumsum(okH)], np.r_[0, np.cumsum(okH & (r > 0))],
                   np.r_[0, np.cumsum(okH & (PA["racel"][H] == 1))], np.r_[0, np.cumsum(okH & (PA["racel"][H] == -1))])
    Z = {}
    for rep in ("R7", "P33"):
        for side, PP in (("A", PA), ("B", PB)):
            F = np.nan_to_num(PP["feats"][rep], nan=0.0).astype(np.float32)
            Z[(rep, side)] = (F, (F.astype(np.float64) ** 2).sum(1))
    rows = []; buf = np.zeros(n, bool); CH = 128
    for c0 in range(0, len(Q), CH):
        qs = Q[c0:c0 + CH]
        D = {}
        for key, (F, s2) in Z.items():
            D[key] = s2[:, None] + s2[qs][None, :] - 2.0 * (F @ F[qs].T).astype(np.float64)
        for ci, q in enumerate(qs):
            lo = lo_all[q]
            for H in HS[tf]:
                r, rc, okH = PA["outc"][H], PA["racel"][H], PA["ok"][H]
                if not okH[q]:
                    continue
                hi0 = q - H
                if hi0 <= lo + 10:
                    continue
                y, ar, rq = r[q], abs(r[q]), int(rc[q])
                cv, cu, ru, rd = pref[H]
                nv = cv[hi0 + 1] - cv[lo]; p0 = (cu[hi0 + 1] - cu[lo]) / nv if nv else np.nan
                nr = (ru[hi0 + 1] - ru[lo]) + (rd[hi0 + 1] - rd[lo]); prace0 = (ru[hi0 + 1] - ru[lo]) / nr if nr else np.nan
                hb = hidx[int(hour[q])]; hb = hb[(hb >= lo) & (hb <= hi0)]; hb = hb[okH[hb]]
                bmed_h = float(np.median(np.abs(r[rng.choice(hb, 1500)]))) if len(hb) else np.nan
                for rep in ("R7", "P33"):
                    cov = 7 if rep == "R7" else 33
                    hi1 = min(hi0, q - cov)
                    dA, dB = D[(rep, "A")][:, ci], D[(rep, "B")][:, ci]
                    pool = ok_idx[H]; pool = pool[(pool >= lo) & (pool <= hi1)]
                    for var, dist0 in (("kendi", dA), ("ortak", dB), ("ikisi", dA + dB)):
                        dist = dist0.copy()
                        dist[~valid[rep]] = np.inf; dist[~okH] = np.inf; dist[:lo] = np.inf; dist[hi1 + 1:] = np.inf
                        idx = knn_select(dist, None, H, buf)
                        nn, pu, med, prace, _ = predict(idx, r, rc)
                        pa, pb, pe = placebo(pool, nn, r, y, ar, rng)
                        rows.append((tgt, par, tf, H, int(q), int(pd.Timestamp(ts[q]).value), y, ar, rq, p0, prace0, bmed_h,
                                     rep, var, nn, pu, med, prace, pa, pb, pe))
    df = pd.DataFrame(rows, columns=["sym", "ortak", "tf", "H", "q", "ts", "y", "absr", "race", "p0", "prace0", "bmed_h",
                                     "rep", "var", "n", "pu", "med", "prace", "plc_acc", "plc_br", "plc_ae"])
    (OUT / "capraz").mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "capraz" / f"{tgt}_{par}_{tf}.parquet")
    return f"capraz {tgt}+{par} {tf}: ortak_bar={n} sorgu={len(Q)} satır={len(df)} {time.time() - t0:.0f}s"


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "baglam"
    only = os.environ.get("BT_ONLY")
    workers = int(os.environ.get("BT_WORKERS", "7"))
    order = {"1h": 0, "30m": 1, "15m": 2, "5m": 3, "4h": 4, "1d": 5}
    if mode == "baglam":
        jobs = [(run_ctx_cell, (s, tf)) for s in SRC for tf in list(SRC[s]) + ["4h", "1d"]]
        jobs.sort(key=lambda j: order[j[1][1]])
    else:
        jobs = [(run_pair, (a, b, tf)) for a in SYMS for b in SYMS if a != b for tf in ("30m", "1h", "4h", "1d")]
        jobs.sort(key=lambda j: order[j[1][2]])
    if only:
        keep = set(only.split(","))
        jobs = [j for j in jobs if ":".join(j[1]) in keep]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(f, *args): args for f, args in jobs}
        for fu in as_completed(futs):
            try:
                print(fu.result(), flush=True)
            except Exception as e:  # noqa: BLE001
                print("HATA", futs[fu], repr(e), flush=True)


if __name__ == "__main__":
    main()
