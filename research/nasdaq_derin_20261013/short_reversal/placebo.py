"""E24 seçim-yükü plasebosu: sinyal maskesini dairesel kaydır (≥20 gün), aynı 12 sinyal × F0/VIX × 4 çıkış × stop yok
alt-ızgarasını yeniden koş → 'pozitif hücre oranı' ve ortalama fazla getirinin boş dağılımı. Keşif dönemi, NDX 1h (+DAX)."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from engine import DISC_END, EXITS, FILTERS, SIGNALS, add_excess, baseline, dax_1h, ndx_1h, run_rule

REPS = 100
FILTS = ["F0", "VIX"]


def sub_grid(mk, start, end, base, shift: int) -> tuple[float, float]:
    d = mk.day
    exs = []
    for sn, sf in SIGNALS.items():
        s = sf(d).fillna(False).to_numpy()
        if shift:
            s = np.roll(s, shift)
        for fn in FILTS:
            m = s & FILTERS[fn](d).fillna(False).to_numpy()
            for ex in EXITS:
                T = add_excess(run_rule(mk, m, ex, None, start, end), base, None)
                exs.append(T.ex.mean() if len(T) >= 5 else np.nan)
    exs = np.array(exs)
    return float(np.nanmean(exs > 0)), float(np.nanmean(exs))


def main(which):
    mk = ndx_1h() if which == "NDX" else dax_1h()
    d = mk.day
    start = d.index[d.sig.notna() & d.ma200.notna()][0]
    end = DISC_END if which == "NDX" else pd.Timestamp("2026-10-02")
    base = baseline(mk, start, end)
    real = sub_grid(mk, start, end, base, 0)
    rng = np.random.default_rng(11)
    nul = [sub_grid(mk, start, end, base, int(rng.integers(20, len(d) - 20))) for _ in range(REPS)]
    nul = np.array(nul)
    print(f"{which}: gerçek pozitif oran {real[0]:.3f} ort fazla {real[1]:+.3f} | plasebo oran ort {nul[:,0].mean():.3f} "
          f"%95 {np.percentile(nul[:,0],95):.3f} max {nul[:,0].max():.3f}; ort fazla ort {nul[:,1].mean():+.3f} %95 "
          f"{np.percentile(nul[:,1],95):+.3f} max {nul[:,1].max():+.3f}; p(oran)={(nul[:,0]>=real[0]).mean():.3f} "
          f"p(fazla)={(nul[:,1]>=real[1]).mean():.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
