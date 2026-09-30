"""Aday kuralların sağlamlık bataryası: gün-blok bootstrap, aylık, yön, grup, gerçek-öldürme muhasebesi."""
import pickle
import numpy as np
import pandas as pd

A, B, C = pickle.load(open("zz_ds.pkl", "rb"))
RULES = {
    "F1 Z→K %60 kilit½TP": dict(n_p=1, first=-1, P=0.6, L=0.3, lock=0.5, lock_tp=True),
    "F2 Z→K %50 KAPAT": dict(n_p=1, first=-1, P=0.5, L=0.3, action=1),
    "F3 Z→K %60 KAPAT": dict(n_p=1, first=-1, P=0.6, L=0.3, action=1),
    "R4 K %60 kilit½TP (klasik)": dict(n_p=1, first=0, P=0.6, L=0.3, lock=0.5, lock_tp=True),
    "R5 K %60 BE (klasik, giriş)": dict(n_p=1, first=0, P=0.6, L=0.3, lock=0.0),
    "R6 3.kâr %20 kilit−0.1R": dict(n_p=3, first=0, P=0.2, Pa=0.2, L=0.05, lock=-0.1),
}


def day_boot(d, days, n=2000, seed=5):
    u, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=d)
    rng = np.random.default_rng(seed)
    b = np.array([s[rng.integers(0, len(s), len(s))].sum() for _ in range(n)])
    return (b > 0).mean(), np.percentile(b, [2.5, 97.5])


def accounting(base, R):
    w = base > 0; l = base < 0
    return dict(
        kazanan_zarara=int((w & (R <= 0)).sum()),          # GERÇEK öldürme
        kazanan_kari_azaldi=int((w & (R > 0) & (R < base - 1e-9)).sum()),
        kazanan_kaybi_R=round(float((base - R)[w & (R < base)].sum()), 1),
        kaybeden_kara=int((l & (R > 0)).sum()),
        kaybeden_azaldi=int((l & (R <= 0) & (R > base + 1e-9)).sum()),
        kaybeden_kazanc_R=round(float((R - base)[l & (R > base)].sum()), 1))


def report(name, ds, R, extra=None):
    d = R - ds.base
    t = pd.to_datetime(ds.meta.t, utc=True)
    days = t.dt.strftime("%Y-%m-%d").values
    p, ci = day_boot(d, days)
    mon = pd.Series(d).groupby(t.dt.strftime("%m").values).sum().round(1).to_dict()
    dirs = pd.Series(d).groupby(ds.meta.dir.values).sum().round(1).to_dict()
    syms = pd.Series(d).groupby(ds.meta.sym.str[:4].values).sum().round(1).to_dict()
    row = dict(set=name, n=len(d), dR=round(d.sum(), 1), per100=round(d.mean() * 100, 2),
               P_pos=round(p, 3), ci=f"[{ci[0]:.1f},{ci[1]:.1f}]", wr=f"{(ds.base>0).mean():.2f}→{(R>0).mean():.2f}",
               aylar=mon, yon=dirs, sembol=syms, **accounting(ds.base, R))
    if extra is not None:
        row["d_usd"] = round(float((d * extra).sum()))
    return row


if __name__ == "__main__":
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 80)
    out = []
    for rn, kw in RULES.items():
        for nm, ds in (("A", A), ("B", B), ("C", C)):
            R, _ = ds.run(delay=2, **kw)
            r = report(nm, ds, R, A.meta.usd_R.values if nm == "A" else None)
            r["kural"] = rn
            out.append(r)
    D = pd.DataFrame(out)
    D.to_pickle("zz_robust.pkl")
    for rn in RULES:
        x = D[D.kural == rn]
        print(f"\n### {rn}")
        print(x[["set", "n", "dR", "per100", "P_pos", "ci", "wr", "d_usd"]].to_string(index=False))
        print(x[["set", "kazanan_zarara", "kazanan_kari_azaldi", "kazanan_kaybi_R", "kaybeden_kara",
                 "kaybeden_azaldi", "kaybeden_kazanc_R"]].to_string(index=False))
        for _, r in x.iterrows():
            print(f"  {r.set} aylar {r.aylar}  yön {r.yon}  sembol {r.sembol}")
