"""Giriş zamanlaması karşı-olgusalları (gerçek sinyaller, 1m yol).

Varyantlar (orijinal giriş anı t0, giriş e, risk R):
  DEEP(x, W, mode): e − x·R'ye limit; W dk içinde dolmazsa işlem YOK (0R).
      mode="dist": TP/SL mesafeleri yeni girişe göre aynı (risk aynı)
      mode="abs" : TP/SL mutlak seviyeleri aynı (risk küçülür, R orijinal risk cinsinden)
  CONF(k, W): önce ≥ k·R aleyhe gidiş, sonra fiyat e'ye geri dönünce gir (W dk içinde)
      — "düşüşü gördükten sonra toparlanma teyidiyle gir".
Sonuç R = orijinal risk birimiyle. Dolum barı ve giriş barı atlanır (muhafazakâr).
"""
import numpy as np
import pandas as pd
from sim import simulate

SPLIT = pd.Timestamp("2026-08-01", tz="UTC")
df = pd.read_pickle("feat.pkl")
df["usd_R"] = df.risk * df.volume * np.where(df.sym == "USOIL.FOREX", 100.0, 1.0)
df["test"] = df.open_utc >= SPLIT
df["grp"] = df.sym.str[:4] + "_" + df.dir


def shifted(p, j, off):
    """Yolu j. bardan başlat, R değerlerini `off` kadar kaydır (yeni giriş = e + off·R)."""
    return dict(fav=p["fav"][j:] - off, adv=p["adv"][j:] - off, cls=p["cls"][j:] - off)


def deep(p, rr, x, W, mode):
    adv = p["adv"]
    hit = np.where(adv[1:W + 1] <= -x)[0]
    if not len(hit):
        return 0.0, False
    j = hit[0] + 1
    q = shifted(p, j, -x)            # yeni giriş e − x·R
    if mode == "dist":
        r, _, _ = simulate(q, rr, sl_r=1.0, start=1)
    else:                            # mutlak seviyeler: TP rr+x yukarıda, SL 1−x aşağıda
        r, _, _ = simulate(q, rr + x, sl_r=1.0 - x, start=1)
    return r, True


def conf(p, rr, k, W):
    adv, fav = p["adv"], p["fav"]
    dip = np.where(adv[1:W + 1] <= -k)[0]
    if not len(dip):
        return 0.0, False
    j = dip[0] + 1
    if adv[j] <= -1:                 # dip barında SL zaten vurulduysa orijinal kayıp yaşanmazdı (girmedik)
        pass
    back = np.where(fav[j + 1:W + 1] >= 0)[0]
    if not len(back):
        return 0.0, False
    j2 = j + 1 + back[0]
    q = shifted(p, j2, 0.0)          # e seviyesinden yeniden giriş (aynı TP/SL)
    r, _, _ = simulate(q, rr, sl_r=1.0, start=1)
    return r, True


if __name__ == "__main__":
    base = np.array([simulate(p, rr)[0] for p, rr in zip(df.path, df.rr)])
    rows = []
    variants = {}
    for x in (0.1, 0.2, 0.3, 0.5):
        for W in (30, 120, 480):
            for mode in ("dist", "abs"):
                variants[f"DEEP x{x} W{W} {mode}"] = ("deep", x, W, mode)
    for k in (0.2, 0.3, 0.5):
        for W in (120, 480):
            variants[f"CONF k{k} W{W}"] = ("conf", k, W, None)
    for name, (kind, a, W, mode) in variants.items():
        R = np.empty(len(df)); F = np.empty(len(df), bool)
        for i, (p, rr) in enumerate(zip(df.path, df.rr)):
            R[i], F[i] = deep(p, rr, a, W, mode) if kind == "deep" else conf(p, rr, a, W)
        for g in ["ALL"] + sorted(df.grp.unique()):
            msk = np.ones(len(df), bool) if g == "ALL" else (df.grp == g).values
            te = df.test.values & msk; tr = ~df.test.values & msk
            d = R - base
            rows.append(dict(v=name, grp=g, n=msk.sum(), fill=F[msk].mean().round(2),
                             sumR=R[msk].sum().round(1), base=base[msk].sum().round(1),
                             dR=d[msk].sum().round(1), dR_tr=d[tr].sum().round(1), dR_te=d[te].sum().round(1),
                             d_usd=(d * df.usd_R.values)[msk].sum().round(0)))
    out = pd.DataFrame(rows)
    out["minTT"] = np.minimum(out.dR_tr, out.dR_te)
    out.to_pickle("entry_grid.pkl")
    pd.set_option("display.width", 220)
    for g, x in out.groupby("grp"):
        print(x.sort_values("minTT", ascending=False).head(6).to_string(index=False))
