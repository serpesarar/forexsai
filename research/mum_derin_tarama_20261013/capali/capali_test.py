"""capali_test.py — ailenin tamamını değerlendir (PROTOCOL.md §3): isabet, taban, plasebo, bootstrap, yarılar,
işaretli hareket, bağımsız olay + sonuç-kaydırma ile seçim düzeltmesi (S=200, ailenin tamamı).

Girdi: results/aile_kur.pkl (capali_kur.py). Çıktı: results/aile.csv, results/null_t.npy, results/null_ozet.json
Çalıştır: nice -n 10 python3.13 research/mum_derin_tarama_20261013/capali/capali_test.py
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capali_veri import HERE, Grid, load_daily, outcome  # noqa: E402

RES = HERE / "results"
MIN_LIB, R_PLC, B_BOOT = 100, 40, 2000
S_NULL = int(os.environ.get("S_NULL", 200))
SPREAD = 1.5
SEED = 20261013


def y_of(c: dict, s: int, GR: dict) -> np.ndarray:
    if c["tf"] == "1d":
        n = c["n_tf_days"]
        return c["yall"][(c["day"] + s) % n]
    G = GR[c["tf"]]
    n = len(G.days)
    y, _ = outcome(G, (c["day"] + s) % n, c["refmin"], c["hz"])
    return y


def calls_of(c: dict, y: np.ndarray) -> np.ndarray:
    if c["kind"] == "rule":
        return c["call"]
    NB = c["NB"]; ok = NB >= 0
    yy = np.where(ok, y[np.maximum(NB, 0)], np.nan)
    up = (yy > 0).sum(1); dn = (yy < 0).sum(1); tot = up + dn
    pu = np.where(tot > 0, up / np.maximum(tot, 1), 0.5)
    return np.sign(pu - 0.5)


def base_of(c: dict, y: np.ndarray) -> np.ndarray:
    v = np.isfinite(y) & (y != 0)
    cu = np.r_[0, np.cumsum(v & (y > 0))]; cv = np.r_[0, np.cumsum(v)]
    L = c["L"]
    bu = cu[L] / np.maximum(cv[L], 1)
    return np.where(bu >= 0.5, 1.0, -1.0)


def stats(c: dict, y: np.ndarray, call: np.ndarray, bcall: np.ndarray) -> tuple[dict, np.ndarray]:
    m = (c["L"] >= MIN_LIB) & np.isfinite(y) & (y != 0) & (call != 0)
    n = int(m.sum())
    out = dict(n=n, n_ind=int(len(np.unique(c["day"][m]))) if n else 0)
    if n < 10:
        out.update(acc=np.nan, bacc=np.nan, diff_pp=np.nan, t=0.0, h1=np.nan, h2=np.nan, move=np.nan, bmove=np.nan, up_rate=np.nan)
        return out, m
    sy = np.sign(y[m])
    corr = (call[m] == sy).astype(float); bcorr = (bcall[m] == sy).astype(float)
    dif = corr - bcorr
    sd = dif.std(ddof=1)
    o = np.argsort(c["tq"][m], kind="stable"); h = n // 2
    out.update(acc=100 * corr.mean(), bacc=100 * bcorr.mean(), diff_pp=100 * dif.mean(),
               t=float(dif.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0,
               h1=100 * dif[o[:h]].mean(), h2=100 * dif[o[h:]].mean(),
               move=float(np.mean(call[m] * y[m])), bmove=float(np.mean(bcall[m] * y[m])),
               up_rate=100 * float(np.mean(y[m] > 0)))
    return out, m


def placebo(c: dict, y: np.ndarray, call: np.ndarray, m: np.ndarray, rng) -> tuple[float, float]:
    sy = np.sign(y[m]); acc = np.mean(call[m] == sy)
    accs = []
    if c["kind"] == "rule":
        cm = call[m]
        for _ in range(R_PLC):
            accs.append(np.mean(rng.permutation(cm) == sy))
    else:
        K = c["NB"].shape[1]; L = c["L"][m]
        for _ in range(R_PLC):
            idx = (rng.random((len(L), K)) * L[:, None]).astype(np.int64)
            yy = y[idx]
            up = (yy > 0).sum(1); dn = (yy < 0).sum(1); tot = up + dn
            pu = np.where(tot > 0, up / np.maximum(tot, 1), 0.5)
            pc = np.sign(pu - 0.5)
            accs.append(np.mean(np.where(pc == 0, 0.5, (pc == sy).astype(float))))
    accs = np.array(accs)
    return 100 * accs.mean(), (1 + np.sum(accs >= acc)) / (R_PLC + 1)


def boot(c: dict, y: np.ndarray, call: np.ndarray, bcall: np.ndarray, m: np.ndarray, rng) -> float:
    sy = np.sign(y[m])
    dif = (call[m] == sy).astype(float) - (bcall[m] == sy).astype(float)
    blk = c["day"][m] // 5
    u, inv = np.unique(blk, return_inverse=True)
    S = np.bincount(inv, weights=dif, minlength=len(u)); N = np.bincount(inv, minlength=len(u)).astype(float)
    pick = rng.integers(0, len(u), size=(B_BOOT, len(u)))
    mb = S[pick].sum(1) / N[pick].sum(1)
    return float(np.mean(mb > 0))


def proxy_pass(s: dict) -> bool:
    return (s["n_ind"] >= 200 and np.isfinite(s["diff_pp"]) and s["diff_pp"] >= 2.0 and s["t"] >= 1.96
            and s["h1"] > 0 and s["h2"] > 0 and s["move"] > SPREAD)


def main() -> None:
    t0 = time.time()
    fam = pickle.load(open(RES / "aile_kur.pkl", "rb"))
    daily = load_daily()
    GR = {tf: Grid(tf, daily) for tf in ("5m", "15m", "30m", "1h")}
    rng = np.random.default_rng(SEED)
    rows = []
    Y0 = []
    for c in fam:
        y = y_of(c, 0, GR); Y0.append(y)
        call = calls_of(c, y); bcall = base_of(c, y)
        s, m = stats(c, y, call, bcall)
        r = dict(name=c["name"], idea=c["idea"], tf=c["tf"], hz=c["hzlab"], K=c["K"], kind=c["kind"], **s)
        if s["n"] >= 10:
            r["plc_acc"], r["plc_p"] = placebo(c, y, call, m, rng)
            r["P_boot"] = boot(c, y, call, bcall, m, rng)
        else:
            r["plc_acc"] = r["plc_p"] = r["P_boot"] = np.nan
        r["coverage"] = 100 * s["n"] / max(1, int(((c["L"] >= MIN_LIB) & np.isfinite(y) & (y != 0)).sum()))
        rows.append(r)
    df = pd.DataFrame(rows)
    print(f"gerçek değerlendirme bitti {time.time() - t0:.0f} sn", flush=True)

    # ── seçim düzeltmesi: sonuçları tam gün kaydır (aynı saat), ailenin tamamını yeniden çalıştır ──
    u = np.random.default_rng(SEED + 1).uniform(0.02, 0.98, S_NULL)
    C = len(fam)
    T = np.zeros((S_NULL, C)); PS = np.zeros((S_NULL, C), bool); DF = np.full((S_NULL, C), np.nan); NI = np.zeros((S_NULL, C), int)
    for k in range(S_NULL):
        for j, c in enumerate(fam):
            n = c["n_tf_days"]
            s_ = int(u[k] * n)
            y = y_of(c, s_, GR)
            call = calls_of(c, y); bcall = base_of(c, y)
            st, _ = stats(c, y, call, bcall)
            T[k, j] = st["t"]; PS[k, j] = proxy_pass(st); DF[k, j] = st["diff_pp"]; NI[k, j] = st["n_ind"]
        if k % 20 == 0:
            print(f"  kaydırma {k}/{S_NULL}  {time.time() - t0:.0f} sn", flush=True)
    np.save(RES / "null_t.npy", T); np.save(RES / "null_pass.npy", PS); np.save(RES / "null_diff.npy", DF)

    elig = (df.n_ind >= 200).to_numpy()
    maxT_all = T.max(1); maxT_el = np.where(elig[None, :], T, -np.inf).max(1)
    df["adj_p_all"] = [(1 + np.sum(maxT_all >= t)) / (S_NULL + 1) for t in df.t]
    df["adj_p_elig"] = [(1 + np.sum(maxT_el >= t)) / (S_NULL + 1) for t in df.t]
    df["bonf_p"] = np.minimum(1.0, (1 - df.P_boot.fillna(0)) * C)
    # her konfigürasyonun kendi kaydırma boş dağılımındaki ham p (bilgi)
    df["raw_shift_p"] = [(1 + np.sum(T[:, j] >= df.t.iloc[j])) / (S_NULL + 1) for j in range(C)]
    df["pass_proxy"] = [proxy_pass(r) for r in df.to_dict("records")]
    df["insufficient"] = df.n_ind < 200
    df["c_n"] = df.n_ind >= 200
    df["c_diff"] = df.diff_pp >= 2.0
    df["c_plc"] = (df.plc_p <= 0.05) & (df.acc > df.plc_acc)
    df["c_boot"] = df.P_boot >= 0.975
    df["c_halves"] = (df.h1 > 0) & (df.h2 > 0)
    df["c_move"] = df.move > SPREAD
    df["c_sel"] = df.adj_p_all <= 0.05
    crit = ["c_n", "c_diff", "c_plc", "c_boot", "c_halves", "c_move", "c_sel"]
    df["n_crit"] = df[crit].sum(1)
    df["CANDIDATE"] = df[crit].all(1)
    df["all_but_sel"] = df[crit[:-1]].all(1)
    df.to_csv(RES / "aile.csv", index=False, float_format="%.4f")
    obs_pass = int(df.pass_proxy.sum())
    null_pass = PS.sum(1)
    summ = dict(n_configs=C, n_eligible=int(elig.sum()), obs_proxy_pass=obs_pass,
                null_proxy_pass_mean=float(null_pass.mean()), null_proxy_pass_q95=float(np.quantile(null_pass, 0.95)),
                p_count=float((1 + np.sum(null_pass >= obs_pass)) / (S_NULL + 1)),
                obs_maxT=float(df.t.max()), null_maxT_q95_all=float(np.quantile(maxT_all, 0.95)),
                null_maxT_q95_elig=float(np.quantile(maxT_el, 0.95)),
                obs_maxT_elig=float(df.t[elig].max()),
                n_all_but_sel=int(df.all_but_sel.sum()), n_candidates=int(df.CANDIDATE.sum()),
                obs_pos_diff_share_elig=float((df.diff_pp[elig] > 0).mean()),
                null_pos_diff_share_elig_mean=float(np.nanmean((DF[:, elig] > 0).mean(1))),
                obs_mean_diff_elig=float(df.diff_pp[elig].mean()),
                null_mean_diff_elig_q05_q95=[float(np.quantile(np.nanmean(DF[:, elig], 1), q)) for q in (0.05, 0.95)],
                runtime_s=round(time.time() - t0))
    json.dump(summ, open(RES / "null_ozet.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
