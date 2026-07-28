"""diagnose.py — NDX BUY neden kanıyor, SELL neden çalışıyor? (teşhis)

Sadece TANIM ve ÖLÇÜM yapar; hiçbir eşik burada seçilmez (seçim mine.py'de,
kronolojik bölünmeyle). Amaç: hipotez üretmek, karar vermek değil.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 60)

BE_WR = None  # aşağıda geometriden hesaplanır


def wr_line(x: pd.DataFrame, label: str) -> str:
    if len(x) == 0:
        return f"{label:34s} n=0"
    return (f"{label:34s} n={len(x):5d}  WR={x.outcome.mean()*100:5.1f}%  "
            f"EV={x.r.mean():+.3f}R  toplam={x.r.sum():+7.1f}R")


def main() -> None:
    d = pd.read_parquet(DATA / "dataset.parquet")
    e = pd.read_parquet(DATA / "episodes.parquet")
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    e["ts"] = pd.to_datetime(e["ts"], utc=True)
    win_r, loss_r = (80 - 1) / 110, -(110 + 1) / 110
    be = -loss_r / (win_r - loss_r)
    print(f"Geometri TP80/SL110 + 1p sürtünme → başabaş WR = {be*100:.1f}%\n")

    print("═══ 1. AYLIK GELİŞİM (epizod = botun gerçeği: aynı anda 1 poz) ═══")
    e["ay"] = e.ts.dt.to_period("M")
    for direction in ("BUY", "SELL"):
        print(f"\n  {direction}")
        g = e[e.direction == direction].groupby("ay")
        for ay, x in g:
            flag = "  ⟵ başabaş altı" if x.outcome.mean() < be else ""
            print(f"    {ay}  " + wr_line(x, "")[34:] + flag)

    print("\n═══ 2. BOTUN CANLI MOMENTUM FİLTRESİ (yeniden hesaplanmış) ═══")
    b = e[e.direction == "BUY"]
    print("  " + wr_line(b, "BUY tümü"))
    print("  " + wr_line(b[b.mom_filter_pass == 1], "BUY momentum filtresi GEÇTİ"))
    print("  " + wr_line(b[b.mom_filter_pass == 0], "BUY momentum filtresi KALDI"))
    print("  — filtre bileşenleri tek tek —")
    for cond, name in ((b.M15_stoch_k > 70, "M15 stoch>70"),
                       (b.M15_dist_ema20_atr > 0.8, "M15 dist(EMA20)/ATR>0.8"),
                       (b.H1_sar_dist_atr > 0, "H1 SAR yukarı")):
        print("  " + wr_line(b[cond], f"BUY {name}"))
    s = e[e.direction == "SELL"]
    print("  " + wr_line(s, "SELL tümü"))
    print("  " + wr_line(s[s.mom_filter_pass_sell == 1], "SELL ayna-momentum GEÇTİ"))

    print("\n═══ 3. SİNYAL YOĞUNLUĞU / KÜMELENME (n şişmesi kanıtı) ═══")
    for direction in ("BUY", "SELL"):
        raw = d[d.direction == direction]
        ep = e[e.direction == direction]
        print(f"  {direction}: ham sinyal {len(raw)} → epizod {len(ep)} "
              f"(sıkışma {len(raw)/max(len(ep),1):.1f}×); "
              f"ham WR {raw.outcome.mean()*100:.1f}% vs epizod WR {ep.outcome.mean()*100:.1f}%")

    print("\n═══ 4. MODEL BAZINDA (epizod) ═══")
    for direction in ("BUY", "SELL"):
        for m in ("pulse1", "pulse2", "pulse3"):
            x = e[(e.direction == direction) & (e.model == m)]
            print("  " + wr_line(x, f"{direction} {m}"))

    print("\n═══ 5. MFE/MAE ANATOMİSİ — kaybedenler nasıl ölüyor ═══")
    for direction in ("BUY", "SELL"):
        x = e[e.direction == direction]
        lo = x[x.outcome == 0]
        wi = x[x.outcome == 1]
        print(f"  {direction}: kaybedenlerin medyan MFE={lo.mfe_r.median():.2f}R "
              f"(TP'ye {lo.mfe_r.median()/ (80/110)*100:.0f}% yol), "
              f"kazananların medyan MAE={wi.mae_r.median():.2f}R; "
              f"medyan süre kazanan {wi.bars_held.median():.0f}dk / "
              f"kaybeden {lo.bars_held.median():.0f}dk")
        near = (lo.mfe_r > 0.7 * (80 / 110)).mean() * 100
        print(f"       kaybedenlerin %{near:.0f}'i TP yolunun %70'ini görmüş")

    print("\n═══ 6. REJİM: BUY hangi ortamda kazanıyor? (SADECE gözlem) ═══")
    b = e[e.direction == "BUY"].copy()
    s = e[e.direction == "SELL"].copy()
    checks = {
        "günlük EMA20>EMA50 (yükseliş)": ("d_trend_up", 0.5, ">"),
        "fiyat günlük EMA50 üstü": ("dist_d_ema50_pct", 0.0, ">"),
        "NDX nakit 50g EMA üstü": ("mx_ndx_above_ema50d", 0.5, ">"),
        "NDX nakit 200g EMA üstü": ("mx_ndx_above_ema200d", 0.5, ">"),
        "VIX < 18.4 (sakin)": ("mx_VIX", 18.4, "<"),
        "20g getiri > 0": ("ret20d", 0.0, ">"),
        "5g getiri > 0": ("ret5d", 0.0, ">"),
        "H4 EMA50 üstü": ("H4_dist_ema50_atr", 0.0, ">"),
        "H1 EMA200 üstü": ("H1_dist_ema200_atr", 0.0, ">"),
        "RTH (NY seansı)": ("is_rth", 0.5, ">"),
        "gün içi pozisyon > %50": ("pos_in_day_range", 0.5, ">"),
        "ADR kullanımı > 1.0": ("day_range_vs_adr", 1.0, ">"),
    }
    for name, (col, thr, op) in checks.items():
        if col not in b.columns:
            continue
        for direction, x in (("BUY", b), ("SELL", s)):
            m = (x[col] > thr) if op == ">" else (x[col] < thr)
            m = m.fillna(False)
            a, bb = x[m], x[~m]
            if len(a) < 15 or len(bb) < 15:
                continue
            print(f"  {direction} {name:32s} EVET n={len(a):4d} WR={a.outcome.mean()*100:5.1f}% "
                  f"EV={a.r.mean():+.3f} | HAYIR n={len(bb):4d} WR={bb.outcome.mean()*100:5.1f}% "
                  f"EV={bb.r.mean():+.3f} | Δ={a.r.mean()-bb.r.mean():+.3f}R")

    print("\n═══ 7. SAAT (UTC) KIRILIMI — BUY ═══")
    for direction in ("BUY", "SELL"):
        x = e[e.direction == direction]
        t = x.groupby("utc_hour").agg(n=("r", "size"), wr=("outcome", "mean"),
                                      ev=("r", "mean"), tot=("r", "sum"))
        t = t[t.n >= 10]
        print(f"  {direction}:")
        print(t.assign(wr=lambda z: (z.wr * 100).round(1),
                       ev=lambda z: z.ev.round(3), tot=lambda z: z.tot.round(1)).to_string())


if __name__ == "__main__":
    main()
