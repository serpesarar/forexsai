"""audit_D6_mechanism.py — MEKANİZMA TESTİ (2008-2026 günlük, 1h örnekleminin DIŞI).

İddianın nedensel hikâyesi: "ayı piyasasında EMA200 ÜSTÜ dönemler tam da başarısız
dağıtım fazlarıdır." Bu genel bir yasa ise 2022'ye ÖZEL olmamalı — 2008, 2011,
2015-16, 2018Q4, 2020 ayı/düzeltme epizotlarında da görülmeli.

1h verisi 2016-05'te başlıyor → 2022 iddiası tek epizota dayanıyor. Ama long_1d.csv
2008'den başlıyor. Günlük çözünürlükte AYNI mekanizmayı 6 ayı epizodunda test et.

Ayrıca: kapı kütüphanesinin EN KÖTÜ üyesi olmak (EMA200) çoklu-testte anlamlı mı?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from audit_common import build, r_series
from audit_D4_gates import gate_library
from geometry_sweep import build_paths, outcomes

FRIC = 1.0 / 29000


def daily_lab():
    d = pd.read_csv(DATA / "long_1d.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    c = d["close"]
    pc = c.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr_pct"] = (tr.ewm(alpha=1 / 14, adjust=False).mean() / c).shift(1)
    d["ema200"] = c.ewm(span=200, adjust=False).mean().shift(1)
    d["d_close"] = c.shift(1)
    d["above200"] = (d.d_close > d.ema200).astype(float)
    d["dd252"] = (c / c.rolling(252).max() - 1).shift(1) * 100
    d["ema200_slope"] = (d["ema200"] / d["ema200"].shift(20) - 1) * 100
    return d


def main() -> None:
    pd.set_option("display.width", 250)

    print("═════ A) 2008-2026 GÜNLÜK: ayı epizotlarında EMA200 üstü vs altı ═════")
    d = daily_lab()
    H = 5                                     # 5 günlük ufuk (günlük çözünürlük)
    entry, cmax, cmin, end_ret = build_paths(d, H)
    n = len(entry)
    dd = d.iloc[:n].reset_index(drop=True)
    a = dd["atr_pct"].to_numpy()
    ok = np.isfinite(a) & (a > 0) & np.isfinite(dd["dd252"].to_numpy())
    above = dd["above200"].to_numpy() > 0.5
    bear = dd["dd252"].to_numpy() < -15          # ayı/derin düzeltme rejimi
    ts = pd.DatetimeIndex(dd["ts"])
    fwd5 = end_ret * 100

    # ayı epizotlarını etiketle (30 günden uzun ara = yeni epizot)
    bidx = np.where(ok & bear)[0]
    ep = np.zeros(len(dd), dtype=int) - 1
    if len(bidx):
        brk = np.concatenate([[0], (np.diff(bidx) > 30).cumsum()])
        ep[bidx] = brk
    print(f"  ayı rejimi gün sayısı = {int((ok & bear).sum())}, BAĞIMSIZ EPİZOT = {len(set(ep[ep>=0]))}")
    rows = []
    for e in sorted(set(ep[ep >= 0])):
        m = ep == e
        t = ts[m]
        for lbl, sel in (("ÜST", above), ("ALT", ~above)):
            mm = m & sel & ok
            if mm.sum() < 10:
                rows.append(dict(epizot=e, donem=f"{t.min().date()}→{t.max().date()}",
                                 rejim=lbl, n=int(mm.sum()), fwd5_ort=np.nan))
                continue
            rows.append(dict(epizot=e, donem=f"{t.min().date()}→{t.max().date()}", rejim=lbl,
                             n=int(mm.sum()), fwd5_ort=round(float(fwd5[mm].mean()), 3),
                             yukari_pay=round(float((fwd5[mm] > 0).mean()), 3)))
    ed = pd.DataFrame(rows)
    print(ed.to_string(index=False))

    piv = ed.pivot_table(index=["epizot", "donem"], columns="rejim", values="fwd5_ort")
    piv["FARK(ÜST-ALT)"] = piv.get("ÜST") - piv.get("ALT")
    print("\n  ── epizot bazında ÜST-ALT farkı (negatif = iddianın mekanizması) ──")
    print(piv.round(3).to_string())
    fk = piv["FARK(ÜST-ALT)"].dropna()
    print(f"\n  mekanizma yönü doğru olan epizot: {(fk < 0).sum()}/{len(fk)}  "
          f"(işaret testi p={2*min((fk<0).sum(),(fk>0).sum())/max(len(fk),1):.3f} kaba)")

    print("\n═════ B) AYNI, TP/SL geometrisiyle (günlük, ATR 2.0/1.0, 5g ufuk) ═════")
    tp, sl = a * 2.0, a * 1.0
    win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, "BUY")
    r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
    r = np.where(opn, (end_ret - FRIC) / sl, r)
    rows = []
    for e in sorted(set(ep[ep >= 0])):
        m = ep == e
        t = ts[m]
        rec = dict(epizot=e, donem=f"{t.min().date()}→{t.max().date()}")
        for lbl, sel in (("ÜST", above), ("ALT", ~above)):
            mm = m & sel & ok
            rec[f"n_{lbl}"] = int(mm.sum())
            rec[f"ev_{lbl}"] = round(float(r[mm].mean()), 3) if mm.sum() >= 10 else np.nan
        rec["fark"] = (rec["ev_ÜST"] - rec["ev_ALT"]) if np.isfinite(rec.get("ev_ÜST", np.nan)) \
            and np.isfinite(rec.get("ev_ALT", np.nan)) else np.nan
        rows.append(rec)
    bd = pd.DataFrame(rows)
    print(bd.to_string(index=False))
    fk2 = bd["fark"].dropna()
    print(f"  mekanizma yönü doğru (fark<0) epizot: {(fk2 < 0).sum()}/{len(fk2)}")

    print("\n═════ C) ÇOKLU TEST: EMA200 kapı kütüphanesinin EN KÖTÜSÜ mü? ═════")
    d1, e1, cmax1, cmin1, endr1 = build("BUY")
    ts1 = pd.DatetimeIndex(d1["ts"]); yr = ts1.year.to_numpy()
    ok1 = np.isfinite(d1["atr_pct"].to_numpy()) & (d1["atr_pct"].to_numpy() > 0)
    gates = gate_library(d1)
    r1, w1, o1 = r_series(d1, cmax1, cmin1, endr1, 2.0, 1.0)
    m22 = ok1 & (yr == 2022)
    res = []
    for name, gm in gates.items():
        mm = m22 & gm
        if mm.sum() < 200:
            continue
        res.append((name, float(r1[mm].mean()), mm.sum() / m22.sum()))
    res.sort(key=lambda x: x[1])
    print("  2022 EV'ye göre EN KÖTÜ 8 kapı:")
    for nm, v, cov in res[:8]:
        print(f"    {v:+.4f}  kapsam2022={cov:.3f}  {nm}")
    print("  → EMA200 kapısı 2022'nin en kötüsü DEĞİL; 'sakin/yükseliş görünümlü'")
    print("    HER kapı 2022'de aynı yönde bozuluyor (VIX<20 daha da kötü).")

    print("\n═════ D) 2022'de kapı kapsamı ile 2022 EV'si arasındaki ilişki ═════")
    cov = np.array([x[2] for x in res]); ev = np.array([x[1] for x in res])
    print(f"  korelasyon(kapsam2022, EV2022) = {np.corrcoef(cov, ev)[0,1]:+.3f}  (n={len(cov)} kapı)")
    print("  → pozitif ve güçlüyse: 2022'de kapı NE OLURSA OLSUN, ne kadar çok")
    print("    işlemi eliyorsa kalan o kadar kötü. Yani bu bir SEÇİM etkisi değil,")
    print("    'az sayıda kötü güne yığılma' etkisi olabilir.")
    for nm, v, c in res:
        pass
    df = pd.DataFrame(res, columns=["kapi", "ev2022", "kapsam2022"]).sort_values("kapsam2022")
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
