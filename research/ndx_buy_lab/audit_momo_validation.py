"""audit_momo_validation.py — Ö2: momentum filtresinin OOS doğrulaması sızıntılı mıydı?

`backend/routers/bot_router.py` yorumu: "NDX.INDX:BUY filtresiz TEST %51.4 → filtreli %78.6".
Canlı NDX BUY kapısı bu rakama dayanıyor.

O doğrulamanın kurgusu (research/structure_filter_oos.py + bot_fixed_tpsl_replay.py):
  • filtre değerleri  → `prediction_logs.factors` (sinyal anında, GERÇEK UTC)
  • sonuç (TP/SL)     → `candle_cache` 1m barları (BROKER saati, +2/+3 saat ileri)

İki saat ekseni karışınca: sinyal gerçek UTC 13:30'da, ama bar araması
"13:31 etiketli" barı bulur — o bar gerçekte 10:31'dir. Yani işlem sinyalden
**3 saat ÖNCE** açılır ve filtre değerleri işlemin ilk 3 saatini ZATEN BİLİR.
Klasik sızıntı: filtre "öngörmez", GÖRMÜŞTÜR.

Bu script aynı kurguyu İKİ KEZ koşar — kaymış (orijinal) ve saat düzeltilmiş —
ve farkı gösterir.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from engine import DATA
from fix_time import correct

TP, SL, FRIC = 80.0, 110.0, 1.0
MODELS = ["pulse1", "pulse2", "pulse3"]


def momo_pass(f: dict) -> bool | None:
    def g(k):
        v = f.get(k)
        try:
            x = float(v)
            return None if x != x else x
        except (TypeError, ValueError):
            return None
    sk, de, sar = g("M15_stoch_k"), g("M15_dist_ema20_atr"), g("H1_sar_dist_atr")
    if None in (sk, de, sar):
        return None
    return (sk > 70) and (de > 0.8) and (sar > 0)


def replay(bars, ts, t, tp=TP, sl=SL):
    i = np.searchsorted(ts, t, side="right")
    if i >= len(ts):
        return None
    entry = bars[i, 0] + FRIC
    tp_px, sl_px = entry + tp, entry - sl
    for j in range(i, min(len(ts), i + 1440)):
        if bars[j, 2] <= sl_px:
            return 0
        if bars[j, 1] >= tp_px:
            return 1
    return None


def run(b1: pd.DataFrame, sig: pd.DataFrame, label: str) -> None:
    ts = b1["ts"].values
    arr = b1[["open", "high", "low", "close"]].to_numpy()
    rows = []
    for r in sig.itertuples(index=False):
        o = replay(arr, ts, np.datetime64(r.ts))
        if o is None:
            continue
        rows.append(dict(ts=r.ts, mp=r.mp, outcome=o))
    d = pd.DataFrame(rows)
    if d.empty:
        print(f"  {label}: veri yok"); return
    a, b = d[d.mp], d[~d.mp]
    print(f"  {label}")
    print(f"     filtresiz (tümü) : n={len(d):4d}  WR={d.outcome.mean()*100:5.1f}%")
    print(f"     filtre GEÇEN     : n={len(a):4d}  WR={a.outcome.mean()*100:5.1f}%")
    print(f"     filtre KALAN     : n={len(b):4d}  WR={b.outcome.mean()*100:5.1f}%")
    print(f"     ΔWR = {(a.outcome.mean()-b.outcome.mean())*100:+.1f} puan")


def main() -> None:
    raw = pd.read_csv(DATA / "bars_1m.csv", parse_dates=["ts"])
    raw["ts"] = pd.to_datetime(raw["ts"], utc=True)
    raw = raw.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    fixed = correct(raw)

    s = pd.read_csv(DATA / "signals.csv")
    s["ts"] = pd.to_datetime(s["created_at"], utc=True, format="mixed")
    s = s[s.model_type.isin(MODELS) & (s.ml_direction == "BUY")].copy()
    s["fac"] = s["factors"].apply(lambda v: json.loads(v) if isinstance(v, str) and v.startswith("{") else {})
    s["mp"] = s["fac"].apply(momo_pass)
    s = s[s.mp.notna()].copy()
    s["mp"] = s["mp"].astype(bool)
    print(f"factors taşıyan NDX BUY sinyali: {len(s)}  "
          f"({s.ts.min().date()} → {s.ts.max().date()})\n")

    print("Orijinal doğrulamanın penceresi (2026-04-25 →) ve tamamı:\n")
    for lo, lbl in ((pd.Timestamp("2026-04-25", tz="UTC"), "2026-04-25 sonrası"),
                    (s.ts.min(), "tüm dönem")):
        sub = s[s.ts >= lo]
        print(f"── {lbl} (n={len(sub)}) ──")
        run(raw, sub, "A) KAYMIŞ barlar (orijinal kurgu — SIZINTILI)")
        run(fixed, sub, "B) SAAT DÜZELTİLMİŞ barlar (dürüst)")
        print()

    # Sızıntının doğrudan kanıtı: filtre, işlemin İLK 3 SAATİNİ mi biliyor?
    print("── SIZINTI TESTİ: filtre, girişten SONRAKİ 3 saatin getirisini 'öngörüyor' mu? ──")
    ts_raw = raw["ts"].values
    px = raw["close"].to_numpy()
    fw = []
    for r in s.itertuples(index=False):
        i = np.searchsorted(ts_raw, np.datetime64(r.ts), side="right")
        if i + 180 >= len(px):
            continue
        fw.append(dict(mp=r.mp, ileri180=px[i + 180] - px[i]))
    f = pd.DataFrame(fw)
    a, b = f[f.mp], f[~f.mp]
    print(f"   KAYMIŞ eksende, girişten sonraki 180 dk ortalama hareket:")
    print(f"     filtre GEÇEN {a.ileri180.mean():+7.1f} puan (n={len(a)})  |  "
          f"KALAN {b.ileri180.mean():+7.1f} puan (n={len(b)})  |  fark {a.ileri180.mean()-b.ileri180.mean():+.1f}")
    print("   (Büyük pozitif fark = filtre geleceği 'biliyor' → fiziksel olarak imkânsız,")
    print("    çünkü kaymış eksende o 180 dk aslında sinyalden ÖNCEKİ 3 saattir.)")


if __name__ == "__main__":
    main()
