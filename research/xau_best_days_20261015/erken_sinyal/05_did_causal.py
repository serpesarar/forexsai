"""SAPMA (sonuç görüldükten sonra, PROTOCOL §10): M2'nin aynı-hafta kontrolü E15 tuzağına düşüyor (hafta, kırılımın
kendisini içeren ileri getiriyle seçiliyor). Nedensel yedek: P1-F = aynı yıl + UTC saati + aynı bayrak durumundan
rastgele bar (20 çekim, olay başına ortalama). DiD = ort(R−P|F) − ort(R−P|¬F); gün-blok bootstrap. → results/did_causal.csv"""
import json, os
import numpy as np, pandas as pd
from common import load_d, path_sim, RES
from features import raw_features, load_vix, add_f9, FEATS, NAMES
ev = pd.read_parquet(os.path.join(RES, "events.parquet"))
d = load_d(); fe = add_f9(raw_features(d, load_vix()), json.load(open(os.path.join(RES, "params.json")))["thr9"])
O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy(); atr = d.atr.to_numpy(); n = len(d)
valid = np.zeros(n, bool); valid[:-1] = seg[1:] == seg[:-1]; valid &= np.isfinite(atr) & (atr > 0)
vi = np.where(valid)[0]; Rall = np.full(n, np.nan)
Rall[vi], _, _ = path_sim(O, H, L, C, seg, vi, vi + 1, atr[vi], np.full(len(vi), 20), None, 1.5, +1, 0.12)
ok = valid & np.isfinite(Rall); yr = d.year.to_numpy(); uh = d.utc_h.to_numpy()
rows = []; rng = np.random.default_rng(5)
for f in FEATS:
    Fb = fe[f].to_numpy().astype(bool)
    key_all = (yr * 100 + uh) * 2 + Fb
    pools = pd.Series(np.where(ok)[0]).groupby(key_all[ok]).apply(np.array).to_dict()
    key_ev = (ev.year.to_numpy() * 100 + ev.utc_h.to_numpy()) * 2 + ev[f].to_numpy()
    pm = np.full(len(ev), np.nan)
    for k, idx in pd.Series(np.arange(len(ev))).groupby(key_ev).indices.items():
        p = pools.get(k)
        if p is not None and len(p):
            pm[idx] = Rall[p[rng.integers(0, len(p), (len(idx), 40))]].mean(1)
    x = ev.R.to_numpy() - pm
    for per in ("kesif", "dogrulama"):
        s = (ev.per == per).to_numpy() & np.isfinite(x)
        xs, F, days = x[s], ev[f].to_numpy()[s], ev.ent_day.to_numpy()[s]
        u, inv = np.unique(days, return_inverse=True)
        sF = np.bincount(inv, xs * F, len(u)); nF = np.bincount(inv, F.astype(float), len(u))
        sN = np.bincount(inv, xs * ~F, len(u)); nN = np.bincount(inv, (~F).astype(float), len(u))
        obs = sF.sum() / nF.sum() - sN.sum() / nN.sum()
        bi = np.random.default_rng(7).integers(0, len(u), (4000, len(u)))
        bs = sF[bi].sum(1) / nF[bi].sum(1) - sN[bi].sum(1) / nN[bi].sum(1)
        rows.append(dict(per=per, feat=f, name=NAMES[f], exc_in=float(xs[F].mean()), exc_out=float(xs[~F].mean()),
                         did=float(obs), P=float((bs > 0).mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5))))
out = pd.DataFrame(rows); out.to_csv(os.path.join(RES, "did_causal.csv"), index=False)
print(out.round(3).to_string())
