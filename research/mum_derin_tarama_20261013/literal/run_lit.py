"""Literal mum eşleştirme — çalıştırıcı (ön-kayıt PROTOCOL.md).

  python3 run_lit.py pilot        # inceltme oranı φ: son mumu tutan aday sayısı (SONUCA BAKMAZ)
  python3 run_lit.py feas         # Faz A: 300 rastgele sorguda eşleşme sayıları (SONUCA BAKMAZ)
  python3 run_lit.py scan [TF..]  # Faz B: sorgu ızgarasında yuva sayıları → results/scan_<TF>.npz
Hepsi `nice -n 10`, NUMBA_NUM_THREADS=2 ile çalıştırılır.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from _lit import HZ, NX, RES, RULES, TOLS, XS, k0_rate, lib_lo, load, query_grid, rep_arrays, run_scan

CAP_B = 10**9     # Faz B: inceltme YOK (pilot süresi yeterli çıktı; φ = 1 her hücrede)
CAP_A = 10**9     # Faz A: inceltme YOK (tam sayım)
TFS = ["1h", "15m", "5m", "1m"]


def pilot() -> None:
    out = {}
    for tf in TFS:
        D = load(tf); qs = query_grid(D)
        rng = np.random.default_rng(5); sub = np.sort(rng.choice(qs, 40, replace=False))
        lo = lib_lo(D, sub)
        for rep, tol in TOLS:
            F, invA, _ = rep_arrays(D, rep)
            m = k0_rate(sub.astype(np.int64), lo, np.ascontiguousarray(F), invA, float(tol))
            libn = float(np.mean(sub - lo))
            out[f"{tf}|{rep}|{tol}"] = dict(k0_mean=float(np.mean(m)), lib_mean=libn, p1=float(np.mean(m) / libn),
                                            phiB=float(min(1.0, CAP_B / max(np.mean(m), 1))),
                                            phiA=float(min(1.0, CAP_A / max(np.mean(m), 1))))
            print(tf, rep, tol, out[f"{tf}|{rep}|{tol}"], flush=True)
    (RES / "pilot_phi.json").write_text(json.dumps(out, indent=1))


def feas() -> None:
    phi = json.loads((RES / "pilot_phi.json").read_text())
    rows = []
    for tf in TFS:
        D = load(tf); qs = query_grid(D)
        rng = np.random.default_rng(11); sub = np.sort(rng.choice(qs, 300, replace=False))
        for rep, tol in TOLS:
            t0 = time.time(); ph = phi[f"{tf}|{rep}|{tol}"]["phiA"]
            S = run_scan(D, sub, rep, tol, ph, seed=3)
            for hi, hn in enumerate(D["hz"]):
                for xi, X in enumerate(XS):
                    for r, (rn, _, _) in enumerate(RULES):
                        scale = 1.0 if r == 0 else 1.0 / ph
                        for c in range(4):
                            qv = S["qvalid"][:, xi]
                            if c & 1:
                                qv = qv & S["qelig"][:, xi]
                            raw = S["nraw"][:, hi, xi, r, c][qv] * scale
                            ind = S["nind"][:, hi, xi, r, c][qv] * scale
                            rows.append(dict(tf=tf, rep=rep, tol=tol, X=int(X), kural=rn, uygunluk=bool(c & 1),
                                             seans=bool(c & 2), ufuk=hn, phi=ph if r else 1.0,
                                             sorgu=int(S["qvalid"][:, xi].sum()), uygun_sorgu=int(qv.sum()),
                                             ham_med=float(np.median(raw)) if len(raw) else np.nan,
                                             ham_p90=float(np.percentile(raw, 90)) if len(raw) else np.nan,
                                             bag_med=float(np.median(ind)) if len(ind) else np.nan,
                                             bag_p75=float(np.percentile(ind, 75)) if len(ind) else np.nan,
                                             bag_p90=float(np.percentile(ind, 90)) if len(ind) else np.nan,
                                             pay_ge1=float(np.mean(ind >= 1)) if len(ind) else np.nan,
                                             pay_ge30=float(np.mean(ind >= 30)) if len(ind) else np.nan))
            print(tf, rep, tol, f"phiA={ph:.3g}", f"{time.time() - t0:.0f}s", flush=True)
    pd.DataFrame(rows).to_csv(RES / "fizibilite.csv", index=False)


def scan_tf(tf: str) -> None:
    phi = json.loads((RES / "pilot_phi.json").read_text())
    D = load(tf); qs = query_grid(D)
    for ti, (rep, tol) in enumerate(TOLS):
        t0 = time.time(); ph = phi[f"{tf}|{rep}|{tol}"]["phiB"]
        S = run_scan(D, qs, rep, tol, ph, seed=100 + ti)
        np.savez_compressed(RES / "scan" / f"{tf}_{ti}.npz", qs=qs, nraw=S["nraw"].astype(np.int32),
                            nind=S["nind"].astype(np.uint16), up=S["up"].astype(np.uint16), dn=S["dn"].astype(np.uint16),
                            qelig=S["qelig"], qvalid=S["qvalid"], phi=np.array(ph))
        print(tf, rep, tol, f"phiB={ph:.3g}", f"sorgu={len(qs)}", f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    (RES / "scan").mkdir(parents=True, exist_ok=True)
    mode = sys.argv[1]
    if mode == "pilot":
        pilot()
    elif mode == "feas":
        feas()
    elif mode == "scan":
        for tf in (sys.argv[2:] or TFS):
            scan_tf(tf)
