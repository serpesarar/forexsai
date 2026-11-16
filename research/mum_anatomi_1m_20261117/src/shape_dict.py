"""shape_dict.py — PROTOCOL EK-6: 30×1m mum resmi → PCA + k-means şekil sözlüğü (KEŞİF'te), ileri getiri üç dönemde. Çıktı results/shape_dict.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import lib  # noqa: E402
from q_daily import PER, per  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
W, K = 30, 20


def build(m1, D):
    a60 = pd.Series(m1.h - m1.l).rolling(60).mean().shift(1).values
    days = D.d.tolist(); nxt = {days[i]: days[i + 1] for i in range(len(days) - 1)}
    X, meta = [], []
    for r in D[D.full].itertuples():
        if r.d not in nxt:
            continue
        nd_close = lib.utc(nxt[r.d], lib.nyse.cash_close_minutes(nxt[r.d]))
        for mnt in range(600, 931, 15):
            j = m1.idx_at(lib.utc(r.d, mnt))                    # karar: mnt'de açılan bar; vektör önceki 30 kapanmış bar
            if j is None or j < W + 61 or m1.d[j - W] != m1.d[j] or not np.isfinite(a60[j]) or a60[j] <= 0:
                continue
            s = slice(j - W, j)
            o, h, l, c = m1.o[s], m1.h[s], m1.l[s], m1.c[s]
            lr = np.diff(np.log(c)); sg = lr.std() if lr.std() > 0 else 1e-6
            rg = h - l
            v = np.r_[(c / c[-1] - 1) / sg, np.where(rg > 0, (c - l) / np.where(rg > 0, rg, 1), 0.5),
                      (h - np.maximum(o, c)) / a60[j], (np.minimum(o, c) - l) / a60[j]]
            k60 = m1.idx_from(m1.t[j] + 3600)
            k1 = m1.idx_from(nd_close)
            if k60 is None or k1 is None:
                continue
            ask, sp = m1.o[j] + m1.spr[j], m1.spr[j]
            # uzun ve kısa net bp (yön sonradan küme işaretinden)
            meta.append({"d": r.d, "per": per(r.d), "minute": mnt,
                         "L60": (m1.o[k60] / ask - 1) * 1e4, "S60": -((m1.o[k60] + m1.spr[k60]) / m1.o[j] - 1) * 1e4,
                         "L1G": (m1.o[k1] / ask - 1) * 1e4 - lib.FIN_BP_PER_DAY * (nxt[r.d] - r.d).days,
                         "S1G": -((m1.o[k1] + m1.spr[k1]) / m1.o[j] - 1) * 1e4})
            X.append(v)
    return np.array(X), pd.DataFrame(meta)


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else 0.0


def main() -> None:
    m1 = lib.load_m1(); D = lib.daily_table(m1)
    X, M = build(m1, D)
    kes = (M.per == "KESIF").values
    sc = StandardScaler().fit(X[kes]); pca = PCA(12, random_state=0).fit(sc.transform(X[kes]))
    km = KMeans(K, n_init=10, random_state=0).fit(pca.transform(sc.transform(X[kes])))
    M["k"] = km.predict(pca.transform(sc.transform(X)))
    rng = np.random.default_rng(0)
    res = {"n": {p: int((M.per == p).sum()) for p in PER}}
    for h in ("60", "1G"):
        Mk = M[kes]
        gross = (Mk["L" + h] + Mk["S" + h]) / 2   # yönsüz ortalama ~ −maliyet/2; t için uzun brüt işareti kullan
        obs = {k: tstat(Mk[Mk.k == k]["L" + h] - Mk["L" + h].mean()) for k in range(K)}
        mx = []
        for _ in range(200):
            lab = Mk.groupby("d")["k"].transform(lambda s: rng.permutation(s.values)).values
            mx.append(max(abs(tstat(Mk["L" + h].values[lab == k] - Mk["L" + h].mean())) for k in range(K)))
        thr = float(np.percentile(mx, 95))
        sel = {k: t for k, t in obs.items() if abs(t) >= thr}
        cell = {"maxT_esik": thr, "kesif_max_abs_t": float(max(abs(t) for t in obs.values())), "secilen": {}}
        for k, t in sel.items():
            side = "L" if t > 0 else "S"
            row = {"yon": side, "kesif_t": t}
            for p in PER:
                g = M[(M.per == p) & (M.k == k)]
                mo = pd.to_datetime(g.d).dt.to_period("M").astype(str).values
                row[p] = {"n": len(g), "net": float(g[side + h].mean()), "P": lib.block_boot_p(g[side + h].values, mo)}
            row["gecti"] = bool(all(row[p]["net"] > 0 for p in ("TEST", "BAGIMSIZ")) and row["TEST"]["P"] >= 0.9 and row["BAGIMSIZ"]["P"] >= 0.9)
            cell["secilen"][int(k)] = row
        # bilgi: tüm kümelerde KEŞİF t ile TEST/BAĞIMSIZ ort. (uzun brüt fark) korelasyonu
        cor = {}
        for p in ("TEST", "BAGIMSIZ"):
            mp = M[M.per == p]
            cor[p] = float(np.corrcoef([obs[k] for k in range(K)], [mp[mp.k == k]["L" + h].mean() - mp["L" + h].mean() for k in range(K)])[0, 1])
        cell["kesif_t_vs_sonraki_fark_korelasyonu"] = cor
        res["H" + h] = cell
    (OUT / "shape_dict.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
