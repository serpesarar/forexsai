"""Ortak araçlar: günlük tablo, nedensel özellikler, kapı değerlendirme. Ön kayıt: PROTOCOL.md."""
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parent / "data"; OUT = Path(__file__).resolve().parent / "results"
def ld(nm): return pd.read_parquet(D / f"{nm}.parquet")
def tablo() -> pd.DataFrame:
    q = ld("QQQ"); t = pd.DataFrame(index=q.index)
    t["o"], t["h"], t["l"], t["c"], t["ac"], t["vol"] = q.Open, q.High, q.Low, q.Close, q["Adj Close"], q.Volume
    t["r"] = np.log(t.ac / t.ac.shift(1))
    for nm in ("VXN", "VIX", "VVIX", "VIX3M", "VIX9D", "SKEW"): t[nm.lower()] = ld(nm).Close.reindex(t.index)
    for nm in ("QQEW", "TQQQ", "SQQQ"):
        x = ld(nm); t["r_" + nm.lower()] = np.log(x["Adj Close"] / x["Adj Close"].shift(1)).reindex(t.index); t["v_" + nm.lower()] = (x.Volume * x.Close).reindex(t.index)
    t["y_gun"] = (t.c.shift(-1) / t.o.shift(-1) - 1) * 1e4          # t+1 açılış → t+1 kapanış
    t["y_gece"] = (t.o.shift(-1) / t.c - 1) * 1e4                    # t kapanış → t+1 açılış (temettü günü hafif aşağı yanlı)
    return t
def korku_asimi(t: pd.DataFrame, vol="vxn", win=252) -> pd.Series:
    """e_t = ΔlnVol_t − (a + b r_t); (a,b) önceki `win` günden (t hariç)."""
    dv = np.log(t[vol] / t[vol].shift(1)); r = t.r
    x, y = r.shift(1), dv.shift(1)
    mx, my = x.rolling(win).mean(), y.rolling(win).mean()
    cov = (x * y).rolling(win).mean() - mx * my; var = (x * x).rolling(win).mean() - mx * mx
    b = cov / var; a = my - b * mx
    return dv - (a + b * r)
def ay_blok(idx, vals_fn, B=3000, seed=5):
    """vals_fn(mask_idx_array) -> istatistik; ay bloklarını yeniden örnekler."""
    rng = np.random.default_rng(seed); ym = pd.DatetimeIndex(idx).to_period("M").astype(str); u, inv = np.unique(ym, return_inverse=True)
    groups = [np.flatnonzero(inv == k) for k in range(len(u))]; out = np.empty(B)
    for b in range(B):
        out[b] = vals_fn(np.concatenate([groups[k] for k in rng.integers(0, len(groups), len(groups))]))
    return out
def degerlendir(ev: pd.DataFrame, g: str, y: str = "y", cost=2.0, n_perm=2000, seed=9) -> dict:
    """ev: taban olaylar (kronolojik), g: bool kapı sütunu."""
    ev = ev.dropna(subset=[g, y]); G = ev[g].to_numpy().astype(bool); Y = ev[y].to_numpy()
    if G.sum() < 20 or (~G).sum() < 20: return {"n": int(len(ev)), "n_acik": int(G.sum()), "yetersiz": True}
    d = lambda ix: Y[ix][G[ix]].mean() - Y[ix][~G[ix]].mean() if G[ix].any() and (~G[ix]).any() else np.nan
    m1 = lambda ix: Y[ix][G[ix]].mean() - cost if G[ix].any() else np.nan
    real = Y[G].mean() - Y[~G].mean(); rng = np.random.default_rng(seed); n = len(Y)
    perm = np.array([(lambda Gs: Y[Gs].mean() - Y[~Gs].mean())(np.roll(G, int(rng.integers(20, n - 20)))) for _ in range(n_perm)])
    bd = ay_blok(ev.index, d); bm = ay_blok(ev.index, m1); h = n // 2
    return {"n": int(n), "n_acik": int(G.sum()), "ort_acik": round(float(Y[G].mean()), 2), "ort_kapali": round(float(Y[~G].mean()), 2), "delta": round(float(real), 2),
            "p_perm": round(float((perm >= real).mean()), 4), "P_delta>0": round(float(np.nanmean(bd > 0)), 3), "P_acik_net>0": round(float(np.nanmean(bm > 0)), 3),
            "isabet_acik": round(float((Y[G] > 0).mean()), 3), "yari_delta": [round(float(Y[:h][G[:h]].mean() - Y[:h][~G[:h]].mean()), 2), round(float(Y[h:][G[h:]].mean() - Y[h:][~G[h:]].mean()), 2)]}
