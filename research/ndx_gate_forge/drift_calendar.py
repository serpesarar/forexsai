"""Sürüklenme takvimi: (hafta günü × NY saati) başına μ/σ, YALNIZ eğitim çağından öğrenilir.

Karar anında 'önümüzdeki 3 saatin beklenen sürüklenmesi' = eğitim çağındaki hücre
ortalamalarının toplamı. Test çağında SELL'ler (ve BUY'lar) bu tahmine göre
kovalanır. Tek hipotez: tahmin yüksekken SELL kötü, BUY iyi olmalı.
Eğitim 2016-2020 (1h), test 2021-2026 (30m/15m işlem düzeyi, 1m 2025-26 + S26).
Ters yön: eğitim 2021-2026 → test 2016-2020 (1h 2 saatlik z) — iki yönlü çapraz geçerlilik.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, block_boot
from long_data import load_long
from macro10y import build
import daylevel_trades as dt

H_AHEAD = 3


def calendar(train: pd.DataFrame) -> pd.Series:
    """(wd, nyh) → 1 saatlik z getirisi ortalaması (yıl-saat tabanı ÇIKARILMADAN: mutlak sürüklenme)."""
    x = train.assign(z1=train.r1 / train.dvol)
    return x.groupby(["wd", "nyh"]).z1.mean()


def predicted(cal: pd.Series, wd: np.ndarray, nyh: np.ndarray) -> np.ndarray:
    out = np.zeros(len(wd))
    for k in range(H_AHEAD):
        h = (nyh + k) % 24
        w = wd + ((nyh + k) // 24)
        v = cal.reindex(pd.MultiIndex.from_arrays([w, h])).to_numpy()
        out += np.nan_to_num(v)
    return out


def main() -> None:
    full = build()      # Pzt–Per, 07–20 UTC; r1 ve dvol içerir
    d1 = load_long("1h")
    # r1 build'de yok → ekle
    full["r1"] = np.nan
    d1 = d1.set_index("ts")
    full["r1"] = (d1.close / d1.open - 1).reindex(full.ts).to_numpy()
    res = []
    for tr_lab, tr_years, te_lab in [("2016-20", range(2016, 2021), "2021-26"), ("2021-26", range(2021, 2027), "2016-20")]:
        cal = calendar(full[full.year.isin(tr_years)])
        # 1h test (2 saatlik z, yıl-saat tabanlı fark)
        te = full[~full.year.isin(tr_years)].copy()
        te["pred"] = predicted(cal, te.wd.to_numpy(), te.nyh.to_numpy())
        q = pd.qcut(te.pred, 5, labels=False, duplicates="drop")
        g = te.groupby(q).y.mean() * 100
        res.append((f"1h z2 | eğitim {tr_lab} → test {te_lab}", g.round(2).to_dict(),
                    float(np.corrcoef(te.pred, te.y)[0, 1])))
        if te_lab == "2021-26":
            for lab, T in [("30m", dt.long_trades("30m")), ("15m", dt.long_trades("15m")), ("1m", dt.m1_trades())]:
                T = T[T.nyd.dt.year >= 2021].reset_index(drop=True)
                T["pred"] = predicted(cal, T.wd.to_numpy(), T.nyh.to_numpy())
                qq = pd.qcut(T.pred, 5, labels=False, duplicates="drop")
                for s in "BS":
                    y = T[f"R_{s}"] - T.groupby(["grp", "utc_h"])[f"R_{s}"].transform("mean")
                    gg = y.groupby(qq).mean()
                    top = qq == qq.max()
                    bs = block_boot(y[top].dropna().to_numpy(), T.nyd[top & y.notna()].astype(str).to_numpy(), 2000)
                    per = y[top].groupby(T.grp[top]).mean()
                    res.append((f"{lab} {s} R | eğitim {tr_lab} → test {te_lab} | üst kova P(<0)={np.mean(bs<0):.3f} "
                                f"gruplar {' '.join(f'{k}:{v:+.3f}' for k, v in per.items())}",
                                gg.round(3).to_dict(), None))
    for name, g, c in res:
        print(name, "→ kovalar (düşük→yüksek tahmin):", g, "" if c is None else f"corr={c:.4f}")


if __name__ == "__main__":
    main()
