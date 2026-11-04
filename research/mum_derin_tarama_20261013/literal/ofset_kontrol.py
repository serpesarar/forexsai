"""SONRADAN (post-hoc) kontrol — aile aramasından SONRA bakıldı, kanıt sınıfı düşüktür.
Ön-düzeltme adaylarını ve 15m/15m'deki en iyi kümeyi, AYNI dönemde ama orijinal sorgularla çakışmayan kaydırılmış
sorgu ızgarasında (ofset = adım/2) yeniden ölçer. Dokunulmaz dönem yine yüklenmez.
Çalıştır: python3 ofset_kontrol.py"""
import numpy as np, pandas as pd
from _lit import HZ, QSTEP, RES, RULES, TOLS, XS, lib_lo, load, query_grid, run_scan
from evaluate import base_rates, call_of
E = pd.read_csv(RES / "aday_eleme.csv"); A = pd.read_csv(RES / "aile.csv")
sel = pd.concat([E[E.aday], A[(A.tf == "15m") & (A.ufuk == "15m") & (A.rep == "pct") & (A.tol == 0.02) & (A.X == 10) &
                              A.kural.str.startswith("%80") & (~A.uygunluk) & (~A.seans) & (~A.guclu_oy)]])
tol_idx = {(r, t): i for i, (r, t) in enumerate(TOLS)}
rows = []
for tf, g in sel.groupby("tf"):
    D = load(tf); q0 = query_grid(D); qs = q0 + QSTEP[tf] // 2; qs = qs[qs < D["n"] - 1]
    lo = lib_lo(D, qs); P0, P0h = base_rates(D, qs, lo)
    for (rep, tol), gg in g.groupby(["rep", "tol"]):
        S = run_scan(D, qs, rep, tol, 1.0)
        for _, row in gg.iterrows():
            h = HZ[tf].index(row.ufuk); xi = int(np.flatnonzero(XS == row.X)[0]); r = [x[0] for x in RULES].index(row.kural)
            c = int(row.uygunluk) + 2 * int(row.seans)
            u_, d_ = S["up"][:, h, xi, r, c], S["dn"][:, h, xi, r, c]; n_ = u_ + d_
            qm = S["qvalid"][:, xi] & (S["qelig"][:, xi] if c & 1 else True); u = np.where(n_ > 0, u_ / np.maximum(n_, 1), np.nan)
            has = qm & (n_ >= row.n_min)
            hi, lo_ = (0.7, 0.3) if row.guclu_oy else (0.5, 0.5)
            call = np.where(has & ((u >= hi) if row.guclu_oy else (u > 0.5)), 1, np.where(has & ((u <= lo_) if row.guclu_oy else (u < 0.5)), -1, 0))
            Y = D["yv"][h, qs]; sy = np.sign(np.nan_to_num(Y)); idx = np.flatnonzero((call != 0) & np.isfinite(Y) & (sy != 0))
            corr = (call[idx] == sy[idx]).mean()
            b0 = call_of(P0[h])[idx]; bh = call_of(P0h[h])[idx]
            a0 = np.where(b0 == 0, .5, b0 == sy[idx]).mean(); ah = np.where(bh == 0, .5, bh == sy[idx]).mean()
            rows.append(dict(tf=tf, rep=rep, tol=tol, X=row.X, kural=row.kural, uygunluk=row.uygunluk, seans=row.seans, ufuk=row.ufuk,
                             n_min=row.n_min, guclu_oy=row.guclu_oy, orijinal_isabet=round(row.isabet, 2), orijinal_fazla=round(row.fazla, 2),
                             orijinal_hareket=round(row.hareket_puan, 2), ofset_cagri=len(idx), ofset_isabet=round(100 * corr, 2),
                             ofset_taban=round(100 * max(a0, ah), 2), ofset_fazla=round(100 * (corr - max(a0, ah)), 2),
                             ofset_hareket=round(float(np.mean(call[idx] * Y[idx])), 2)))
o = pd.DataFrame(rows); pd.set_option("display.width", 250); print(o.to_string()); o.to_csv(RES / "ofset_kontrol.csv", index=False)
