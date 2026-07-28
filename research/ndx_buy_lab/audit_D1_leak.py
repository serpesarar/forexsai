"""audit_D1_leak.py — SIZINTI DENETİMİ: günlük/makro özellikler karar anında biliniyor mu?

Test 1: long_1d.csv barının zaman damgası AÇILIŞ mı? (kapanışı gelecekten mi alıyoruz)
Test 2: merge_asof sonrası her 1h satırının kullandığı d_close, o satırın zamanından
        ÖNCE kapanmış bir günlük bara mı ait?
Test 3: makro (VIX) satırının gerçek yayın zamanı geçmiş mi?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from audit_common import load_1h, daily_feats, macro_feats


def main() -> None:
    pd.set_option("display.width", 220)
    d1 = pd.read_csv(DATA / "long_1d.csv", parse_dates=["ts"])
    d1["ts"] = pd.to_datetime(d1["ts"], utc=True)
    d1 = d1.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    h = load_1h()

    print("═════ TEST 1: günlük bar penceresi (1h barlarla eşleştirerek) ═════")
    # Günlük bar D'nin high/low'u hangi 1h aralığıyla örtüşüyor?
    sample = d1[(d1.ts >= "2022-01-01") & (d1.ts < "2022-04-01")]
    rows = []
    for _, row in sample.head(8).iterrows():
        t0 = row.ts
        for lbl, lo, hi in (("[D 00:00, D+1 00:00)", t0, t0 + pd.Timedelta(days=1)),
                            ("[D-1 22:00, D 22:00)", t0 - pd.Timedelta(hours=2), t0 + pd.Timedelta(hours=22))):
            w = h[(h.ts >= lo) & (h.ts < hi)]
            if len(w) == 0:
                continue
            rows.append(dict(gun=str(t0.date()), pencere=lbl, nbar=len(w),
                             d_high=row.high, w_high=w.high.max(),
                             d_low=row.low, w_low=w.low.min(),
                             d_close=row.close, w_lastclose=w.close.iloc[-1],
                             eslesme=bool(abs(row.high - w.high.max()) < 1e-6 and
                                          abs(row.low - w.low.min()) < 1e-6)))
    r = pd.DataFrame(rows)
    print(r.to_string(index=False))
    for lbl, g in r.groupby("pencere"):
        print(f"  {lbl}: tam eşleşme {g.eslesme.mean():.0%}")

    print("\n═════ TEST 2: merge_asof sonrası d_close gerçekten geçmiş mi ═════")
    df = daily_feats()
    m = pd.merge_asof(h[["ts", "close"]], df.sort_values("known_at"),
                      left_on="ts", right_on="known_at", direction="backward")
    # d_close = c.shift(1) → known_at günü D ise değer D-1'in kapanışı.
    # D-1'in kapanışı en geç D-1 22:00 UTC'de gerçekleşir; her 1h satırı >= D 00:00.
    lag_h = (m["ts"] - m["known_at"]).dt.total_seconds() / 3600
    print(f"  merge gecikmesi (saat): min={lag_h.min():.1f} med={lag_h.median():.1f} max={lag_h.max():.1f}")
    print(f"  negatif gecikme (GELECEĞE bakma) satır sayısı: {(lag_h < 0).sum()}")
    # ek: kullanılan d_close değeri, karar anından önceki son GERÇEK 1h kapanışına eşit mi
    # olmalı değil ama ondan ESKİ olmalı — kaba kontrol: d_close ile o anki fiyat farkı
    print(f"  d_close ile anlık fiyat korelasyonu: {m['d_close'].corr(m['close']):.4f} (1.0 olmalı, aynı seri)")

    print("\n═════ TEST 3: makro (VIX) yayın gecikmesi ═════")
    mm = macro_feats()
    m2 = pd.merge_asof(h[["ts"]], mm.sort_values("known_at"), left_on="ts",
                       right_on="known_at", direction="backward")
    lag2 = (m2["ts"] - m2["known_at"]).dt.total_seconds() / 3600
    print(f"  gecikme (saat): min={lag2.min():.1f} med={lag2.median():.1f} max={lag2.max():.1f}")
    print(f"  negatif gecikme: {(lag2 < 0).sum()}")
    print("  NOT: known_at = veri günü + 1 gün → VIX kapanışı (21:15 UTC) her zaman geçmişte. TEMİZ.")

    print("\n═════ TEST 4: 2022'de kapı değerlerinin gün-içi değişkenliği ═════")
    d = load_1h()
    d = pd.merge_asof(d, daily_feats().sort_values("known_at"), left_on="ts",
                      right_on="known_at", direction="backward")
    y22 = d[(d.ts >= "2022-01-01") & (d.ts < "2023-01-01")]
    per_day = y22.groupby(y22.ts.dt.date)["above_ema200"].nunique()
    print(f"  2022 gün sayısı: {len(per_day)}, gün içinde EMA200 kapısı DEĞİŞEN gün: {(per_day > 1).sum()}")
    print("  (0 olmalı — kapı günlük, gün içinde sabit; değişiyorsa merge sınırı kayması var)")


if __name__ == "__main__":
    main()
