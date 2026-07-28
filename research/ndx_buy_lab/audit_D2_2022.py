"""audit_D2_2022.py — 2022 AYRIŞTIRMASI + GÜN-BLOKLU BOOTSTRAP.

Sorular:
  1. 2022'de EMA200 ALTINDA long neden kazanmış? "Ayı piyasası rallisi" hipotezini
     doğrudan ölç: alt/üst rejimde ham 24s ileri getiri, WR, EV, kuyruklar.
  2. 2022'nin gerçek örneklem büyüklüğü ne? (örtüşen 24s etiket → gün bloğu)
  3. EV(üst) - EV(alt) farkı gün-bloklu bootstrap'ta anlamlı mı?
  4. -0.352 birkaç güne mi dayanıyor? (gün bazında R dağılımı, en kötü 5 gün çıkarılınca)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from audit_common import build, r_series, block_boot, block_boot_diff

GEOMS = [(2.0, 1.0), (3.0, 1.0), (1.5, 1.0), (0.727, 1.0)]


def main() -> None:
    pd.set_option("display.width", 250)
    d, entry, cmax, cmin, end_ret = build("BUY")
    ts = pd.DatetimeIndex(d["ts"])
    year = ts.year.to_numpy()
    day_key = ts.normalize().astype("int64").to_numpy()
    ok = np.isfinite(d["atr_pct"].to_numpy()) & (d["atr_pct"].to_numpy() > 0)
    above = np.nan_to_num(d["above_ema200"].to_numpy(), nan=0.0) > 0.5
    y22 = ok & (year == 2022)

    print("═════ 1) 2022 ÖRNEKLEM ANATOMİSİ ═════")
    for lbl, m in (("2022 tümü", y22), ("2022 EMA200 ÜSTÜ", y22 & above),
                   ("2022 EMA200 ALTI", y22 & ~above)):
        nd = len(np.unique(day_key[m]))
        print(f"  {lbl:20s} n={m.sum():5d} bar  |  BAĞIMSIZ GÜN={nd:4d}  "
              f"|  bar/gün={m.sum()/max(nd,1):.1f}")
    print("  → 24 saatlik ufuk + saatlik karar = her etiket 23 komşusuyla ÖRTÜŞÜYOR.")
    print("    Etkin bağımsız gözlem ~gün sayısı kadardır, bar sayısı kadar DEĞİL.")

    print("\n═════ 2) HAM PİYASA DAVRANIŞI (geometriden bağımsız) ═════")
    fwd = d["fwd24_ret"].to_numpy()
    rows = []
    for y in range(2016, 2027):
        for lbl, sel in (("ÜST", above), ("ALT", ~above)):
            m = ok & (year == y) & sel
            if m.sum() < 100:
                continue
            rows.append(dict(yil=y, rejim=lbl, n=int(m.sum()),
                             gun=len(np.unique(day_key[m])),
                             fwd24_ort=round(float(fwd[m].mean()), 4),
                             fwd24_med=round(float(np.median(fwd[m])), 4),
                             yukari_pay=round(float((fwd[m] > 0).mean()), 3),
                             maxUp_ort=round(float(d["_cmax_final"].to_numpy()[m].mean()*100), 3),
                             maxDn_ort=round(float(d["_cmin_final"].to_numpy()[m].mean()*100), 3)))
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n═════ 3) GEOMETRİ x REJİM — 2022 (gün-bloklu %95 GA) ═════")
    for tp_a, sl_a in GEOMS:
        r, win, opn = r_series(d, cmax, cmin, end_ret, tp_a, sl_a)
        print(f"\n── TP{tp_a}/SL{sl_a} ──")
        rows = []
        for lbl, sel in (("2022 tümü", y22), ("2022 ÜST", y22 & above), ("2022 ALT", y22 & ~above)):
            ev, lo, hi = block_boot(r, sel, day_key)
            rows.append(dict(alt_kume=lbl, n=int(sel.sum()), gun=len(np.unique(day_key[sel])),
                             wr=round(float(win[sel].mean()), 4), ev=round(ev, 4),
                             ga_alt=round(lo, 4), ga_ust=round(hi, 4),
                             toplamR=round(float(r[sel].sum()), 1)))
        print(pd.DataFrame(rows).to_string(index=False))
        obs, lo, hi, p_ge0 = block_boot_diff(r, y22 & above, y22 & ~above, day_key)
        print(f"  FARK EV(ÜST)-EV(ALT) = {obs:+.4f}  %95 GA [{lo:+.4f}, {hi:+.4f}]  "
              f"P(fark>=0) = {p_ge0:.3f}")
        # taban ile kıyas: iddia "-0.074 -> -0.352"
        obs2, lo2, hi2, p2 = block_boot_diff(r, y22 & above, y22, day_key)
        print(f"  FARK EV(ÜST)-EV(2022 tümü) = {obs2:+.4f}  %95 GA [{lo2:+.4f}, {hi2:+.4f}]  P(>=0)={p2:.3f}")

    print("\n═════ 4) -0.352 KAÇ GÜNE DAYANIYOR? (TP2.0/SL1.0, 2022 ÜST) ═════")
    r, win, opn = r_series(d, cmax, cmin, end_ret, 2.0, 1.0)
    m = y22 & above
    df = pd.DataFrame({"gun": pd.DatetimeIndex(ts[m]).date, "r": r[m]})
    g = df.groupby("gun")["r"].agg(["mean", "count", "sum"]).sort_values("sum")
    print(f"  gün sayısı={len(g)}  toplamR={g['sum'].sum():.1f}")
    print("  EN KÖTÜ 8 GÜN:")
    print(g.head(8).round(3).to_string())
    print("  EN İYİ 5 GÜN:")
    print(g.tail(5).round(3).to_string())
    for k in (1, 3, 5, 10):
        keep = g.iloc[k:]
        ev_k = keep["sum"].sum() / keep["count"].sum()
        print(f"  en kötü {k:2d} gün ÇIKARILINCA EV = {ev_k:+.4f}  (ham {r[m].mean():+.4f})")
    top = g.tail(20)["sum"].sum() / g["sum"].sum()
    print(f"  toplam R'nin ne kadarı en kötü 20 günden: "
          f"{g.head(20)['sum'].sum()/g['sum'].sum():.1%}")

    print("\n═════ 5) 2022 AY AY (TP2.0/SL1.0) ═════")
    mm = y22
    dfm = pd.DataFrame({"ay": pd.DatetimeIndex(ts[mm]).to_period("M").astype(str),
                        "r": r[mm], "ust": above[mm]})
    piv = dfm.pivot_table(index="ay", columns="ust", values="r", aggfunc=["mean", "count"])
    print(piv.round(3).to_string())


if __name__ == "__main__":
    main()
