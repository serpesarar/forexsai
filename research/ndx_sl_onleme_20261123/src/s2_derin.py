"""1. ölçütü geçen adaylar: plasebo (ölçüt 4), plato, mekanizma ayrıştırması, yıl kırılımı, kullanıcı ölçüsü.

Kullanım: python s2_derin.py "E probasyon 10 bar" [...]
"""
from __future__ import annotations

import importlib.util
import sys

import numpy as np
import pandas as pd

from eng import CORE, HERE, run2

_sp = importlib.util.spec_from_file_location("my_s1", HERE / "s1_tarama.py")
S = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S)
RES = HERE.parent / "results"
RNG = np.random.default_rng(11)


def yearly(t: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y in sorted(set(b.et.dt.year)):
        x, z = t[t.et.dt.year == y], b[b.et.dt.year == y]
        rows.append(dict(yil=y, n=len(x), n0=len(z), SR=round(x.R.sum(), 1), SR0=round(z.R.sum(), 1),
                         dSR=round(x.R.sum() - z.R.sum(), 1), mR=round(x.R.mean(), 3), mR0=round(z.R.mean(), 3),
                         SL=int((x.why == "SL").sum()), SL0=int((z.why == "SL").sum()),
                         TP=int((x.why == "TP").sum()), TP0=int((z.why == "TP").sum())))
    return pd.DataFrame(rows)


def placebo_skip(t: pd.DataFrame, b: pd.DataFrame, reps: int = 500) -> tuple[float, float]:
    """Tabandan aynı sayıda rastgele işlem at (dönem başına); ΔΣR dağılımı vs gerçek Δ (çekirdek dönemler)."""
    real = t[t.period.isin(CORE)].R.sum() - b[b.period.isin(CORE)].R.sum()
    sims = []
    for _ in range(reps):
        d = 0.0
        for p in CORE:
            z = b[b.period == p].R.to_numpy()
            k = max(len(z) - int((t.period == p).sum()), 0)
            if k:
                d -= z[RNG.choice(len(z), k, replace=False)].sum()
        sims.append(d)
    sims = np.array(sims)
    return float(real), float((sims >= real).mean())


def placebo_delay(kw: dict, reps: int = 40) -> list[float]:
    """Aynı ek bekleme süresi, filtre YOK: taban + rastgele 0–10 dk ek gecikme (zincir kaosu tabanı, E89)."""
    out = []
    for i in range(reps):
        lag = int(RNG.integers(1, 11))
        ts = []
        for k in S.MK:
            t, _ = run2(S.M[k], S.SIG[k], lag=lag)
            ts.append(t)
        t = pd.concat(ts)
        out.append(float(t[t.period.isin(CORE)].R.sum()))
    return out


def main():
    b = pd.read_pickle(RES / "base_full.pkl")
    names = sys.argv[1:]
    for name in names:
        kw = S.C[name]
        t, s = S.run_all(kw)
        print(f"\n══ {name} ══")
        y = yearly(t, b)
        print(y.to_string(index=False))
        for fam in ("DC", "RE"):
            x, z = t[(t.fam == fam) & t.period.isin(CORE)], b[(b.fam == fam) & b.period.isin(CORE)]
            print(f"  {fam}: n {len(x)} vs {len(z)}  ortR {x.R.mean():+.3f} vs {z.R.mean():+.3f}  ΣR {x.R.sum():+.1f} vs {z.R.sum():+.1f}")
        sk = s[s.period.isin(CORE)] if len(s) else s
        if len(sk):
            print("  atlanan kararlar (piyasa girişi karşı-olgusu):",
                  sk.groupby("why").R.agg(["size", "mean", "sum"]).round(3).to_dict("index"))
        real, p = placebo_skip(t, b)
        print(f"  plasebo (aynı sayıda rastgele atma): gerçek Δ {real:+.1f}R, p = {p:.3f}")
        core_b = b[b.period.isin(CORE)]
        for p_ in CORE + ["Y26b", "VAKA"]:
            x, z = t[t.period == p_], b[b.period == p_]
            sl0, tp0 = (z.why == "SL").sum(), (z.why == "TP").sum()
            print(f"  {p_:7s} SL {int((x.why == 'SL').sum())}/{sl0} (engel %{100 * (1 - (x.why == 'SL').sum() / max(sl0, 1)):.0f})"
                  f"  TP {int((x.why == 'TP').sum())}/{tp0} (kayıp %{100 * (1 - (x.why == 'TP').sum() / max(tp0, 1)):.0f})"
                  f"  ortR {x.R.mean():+.3f} vs {z.R.mean():+.3f}")
        if kw.get("prob_n") or kw.get("prob_cap"):
            d = placebo_delay(kw)
            real_sr = t[t.period.isin(CORE)].R.sum()
            print(f"  gecikme plasebosu (filtresiz 1–10 dk ek gecikme, 40 koşu): ΣR medyan {np.median(d):+.1f}, "
                  f"%90 {np.percentile(d, 90):+.1f}, max {max(d):+.1f} | aday ΣR {real_sr:+.1f} "
                  f"(taban {core_b.R.sum():+.1f}); p = {np.mean(np.array(d) >= real_sr):.3f}")
        y.to_csv(RES / f"yillik_{name.split()[0]}_{abs(hash(name)) % 10**6}.csv", index=False)


if __name__ == "__main__":
    main()
