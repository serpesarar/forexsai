"""audit_D3_frame.py — ÇERÇEVE HATASI TESTİ + EPİZOT BLOKLU BOOTSTRAP.

A) "Kapı 2022'yi DAHA KÖTÜ yapıyor" ifadesi EV başına doğru; ama HESABIN gördüğü
   şey TOPLAM R. Kapı işlem sayısını da kesiyor. İkisini yan yana ölç.
B) 2022 ÜST rejimi 30 güne dayanıyor — bu 30 gün kaç BAĞIMSIZ EPİZOT?
   Ardışık günler aynı rallinin parçasıysa gün-bloklu bootstrap bile fazla iyimser.
   Epizot-bloklu (ardışık gün kümesi) bootstrap ile tekrar ölç.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from audit_common import build, r_series

GEOMS = [(2.0, 1.0), (3.0, 1.0), (1.5, 1.0), (0.727, 1.0)]


def episodes_of(days: np.ndarray, gap_days: int = 5) -> np.ndarray:
    """Ardışık (<=gap gün aralıklı) günleri tek epizot say."""
    u = np.unique(days)
    ud = pd.to_datetime(u)
    brk = np.concatenate([[0], (np.diff(ud.values).astype("timedelta64[D]").astype(int) > gap_days).cumsum()])
    return dict(zip(u, brk))


def block_boot_generic(r, mask, key, n_boot=4000, seed=11):
    rng = np.random.default_rng(seed)
    k = key[mask]; rr = r[mask]
    uniq, inv = np.unique(k, return_inverse=True)
    S = np.zeros(len(uniq)); C = np.zeros(len(uniq))
    np.add.at(S, inv, rr); np.add.at(C, inv, 1.0)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    means = S[idx].sum(1) / C[idx].sum(1)
    return float(rr.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)), len(uniq)


def main() -> None:
    pd.set_option("display.width", 250)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"])
    year = ts.year.to_numpy()
    day = ts.normalize()
    day_i = day.astype("int64").to_numpy()
    week_i = ts.to_period("W").astype(str).to_numpy()
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    above = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
    y22 = ok & (year == 2022)

    print("═════ A) 2022 ÜST rejimin 30 GÜNÜ — hangi tarihler, kaç EPİZOT ═════")
    dd = np.unique(day[y22 & above].date)
    print("  " + ", ".join(str(x) for x in dd))
    epmap = episodes_of(np.array([np.datetime64(x) for x in dd]), gap_days=5)
    ep_ids = np.array([epmap[np.datetime64(x)] for x in dd])
    print(f"  BAĞIMSIZ EPİZOT SAYISI (>5 gün ara ile ayrılan küme) = {len(set(ep_ids))}")
    for e in sorted(set(ep_ids)):
        sel = dd[ep_ids == e]
        print(f"    epizot {e}: {sel[0]} → {sel[-1]}  ({len(sel)} gün)")

    print("\n═════ B) EPİZOT-BLOKLU BOOTSTRAP (2022 ÜST) ═════")
    ep_full = np.full(len(d), -1, dtype=object)
    m = y22 & above
    dser = pd.Series(day.date, index=np.arange(len(d)))
    for i in np.where(m)[0]:
        ep_full[i] = f"ep{epmap[np.datetime64(dser.iloc[i])]}"
    for tp_a, sl_a in GEOMS:
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        ev_d, lo_d, hi_d, nd = block_boot_generic(r, m, day_i)
        ev_w, lo_w, hi_w, nw = block_boot_generic(r, m, week_i)
        ev_e, lo_e, hi_e, ne = block_boot_generic(r, m, ep_full)
        print(f"  TP{tp_a}/SL{sl_a}: EV={ev_d:+.4f}")
        print(f"     GÜN bloğu   (n={nd:3d}): %95 GA [{lo_d:+.4f}, {hi_d:+.4f}]")
        print(f"     HAFTA bloğu (n={nw:3d}): %95 GA [{lo_w:+.4f}, {hi_w:+.4f}]")
        print(f"     EPİZOT bloğu(n={ne:3d}): %95 GA [{lo_e:+.4f}, {hi_e:+.4f}]  ← DÜRÜST OLAN")

    print("\n═════ C) ÇERÇEVE: EV mi, TOPLAM R mi? (kapı R1 = fiyat>günlük EMA200) ═════")
    rows = []
    for tp_a, sl_a in GEOMS:
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        for scope, msk in (("2022", y22), ("TÜM 11 YIL", ok)):
            base, gated = msk, msk & above
            rows.append(dict(
                geometri=f"TP{tp_a}/SL{sl_a}", kapsam=scope,
                n_kapisiz=int(base.sum()), n_kapili=int(gated.sum()),
                ev_kapisiz=round(float(r[base].mean()), 4),
                ev_kapili=round(float(r[gated].mean()), 4),
                toplamR_kapisiz=round(float(r[base].sum()), 1),
                toplamR_kapili=round(float(r[gated].sum()), 1),
                R_farki=round(float(r[gated].sum() - r[base].sum()), 1)))
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\n  → 2022'de kapı EV'yi kötüleştirirken TOPLAM ZARARI AZALTIYOR mu? bak: R_farki > 0 ise EVET.")

    print("\n═════ D) 11 YILIN HER BİRİNDE: kapının toplam R etkisi (TP2.0/SL1.0) ═════")
    r, win, opn = r_series(d, cmax, cmin, end_ret, 2.0, 1.0)
    rows = []
    for y in range(2016, 2027):
        b = ok & (year == y); g = b & above
        rows.append(dict(yil=y, n_kapisiz=int(b.sum()), n_kapili=int(g.sum()),
                         kapsam=round(g.sum()/max(b.sum(),1), 3),
                         ev_kapisiz=round(float(r[b].mean()), 4),
                         ev_kapili=round(float(r[g].mean()), 4) if g.sum() > 50 else np.nan,
                         R_kapisiz=round(float(r[b].sum()), 1),
                         R_kapili=round(float(r[g].sum()), 1),
                         R_farki=round(float(r[g].sum() - r[b].sum()), 1)))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
