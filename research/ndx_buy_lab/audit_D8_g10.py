"""audit_D8_g10.py — TEK KARŞI-ÖRNEK (G10) NE KADAR SAĞLAM?

G10 = 20g gerçekleşen vol'ün 2 yıllık kayan yüzdelik dilimi < 0.8
124 kombinasyon içinde 2022'yi +EV yapan TEK kapı. Gerçek mi, arama artefaktı mı?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from audit_common import build, r_series, block_boot
from audit_D4_gates import gate_library


def main() -> None:
    pd.set_option("display.width", 250)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"]); yr = ts.year.to_numpy()
    day_key = ts.normalize().astype("int64").to_numpy()
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    g = gate_library(d)
    g10 = g["G10 gerç.vol yüzdelik<0.8"]
    above = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
    m22 = ok & (yr == 2022)

    print("═════ A) G10'un 2022 EV'si — gün-bloklu %95 GA, 4 geometri ═════")
    for tp_a, sl_a in ((2.0, 1.0), (2.5, 1.0), (3.0, 1.0), (1.5, 1.0), (0.727, 1.0)):
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        m = m22 & g10
        ev, lo, hi = block_boot(r, m, day_key)
        print(f"  TP{tp_a}/SL{sl_a}: n={m.sum():5d} gün={len(np.unique(day_key[m])):3d} "
              f"EV={ev:+.4f} %95GA[{lo:+.4f},{hi:+.4f}] toplamR={r[m].sum():+.1f}")
    print("  → GA'nın SIFIRI içermesi = 'kurtardı' iddiası istatistiksel olarak kanıtlanmamış.")

    print("\n═════ B) G10 2022'de ne yapıyor: 5 ralli epizodunu mu eliyor? ═════")
    m = m22 & g10
    print(f"  2022 G10 kapsamı: {m.sum()/m22.sum():.1%}")
    ov = (m22 & g10 & above).sum() / max((m22 & above).sum(), 1)
    print(f"  2022 EMA200-ÜSTÜ barlarının G10'dan geçen oranı: {ov:.1%}")
    print(f"  2022 EMA200-ALTI  barlarının G10'dan geçen oranı: "
          f"{(m22 & g10 & ~above).sum()/max((m22 & ~above).sum(),1):.1%}")
    kept = pd.DatetimeIndex(ts[m]).to_period('M').astype(str)
    print("  aylara göre G10'un 2022'de tuttuğu bar sayısı:")
    print("   ", pd.Series(kept).value_counts().sort_index().to_dict())

    print("\n═════ C) G10 yıl yıl (TP2.0/SL1.0) + en kötü yıl ═════")
    r, win, opn = r_series(d, cmax, cmin, end_ret, 2.0, 1.0)
    rows = []
    for y in range(2016, 2027):
        mm = ok & g10 & (yr == y)
        b = ok & (yr == y)
        rows.append(dict(yil=y, n=int(mm.sum()), kapsam=round(mm.sum()/max(b.sum(),1), 3),
                         ev=round(float(r[mm].mean()), 4) if mm.sum() > 50 else np.nan,
                         R=round(float(r[mm].sum()), 1),
                         ev_kapisiz=round(float(r[b].mean()), 4)))
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n═════ D) YARIYA BÖLME (2016-2021 vs 2022-2026) — arama artefaktı testi ═════")
    for tp_a, sl_a in ((2.0, 1.0), (3.0, 1.0)):
        r2, w2, o2 = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        for lbl, sel in (("ilk yarı 2016-2021", yr <= 2021), ("ikinci yarı 2022-2026", yr >= 2022)):
            a_ = ok & sel; b_ = ok & sel & g10
            print(f"  TP{tp_a}/SL{sl_a} {lbl}: kapısız EV={r2[a_].mean():+.4f} → "
                  f"G10 EV={r2[b_].mean():+.4f}  (fark {r2[b_].mean()-r2[a_].mean():+.4f})")


if __name__ == "__main__":
    main()
