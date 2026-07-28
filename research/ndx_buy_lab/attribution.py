"""attribution.py — "yüksek RR bir kenar mı, yoksa sürüklenme hasadı mı?"

Denetçi bulgusu (bağımsız doğrulama): geometri taramasındaki avantaj,
geometrinin bir özelliği değil, pozisyonun PİYASADA GEÇİRDİĞİ SÜRE olabilir —
NDX 2016-2026'da ~5 kat arttı, uzun tutan çok toplar.

Üç bağımsız kontrol (11 yıl, saatlik, 2016-05 → 2026-07):
  T1 GERÇEKÇİ SÜRTÜNME  Broker verisi: spread medyan 1.3 puan, 218 SL/TP kapanışının
     218'i hedef seviyeden 0.000 puan sapmayla doldu → kayma ≈ 0. Sürtünme artık
     FİYATA ORANTILI (2016'da 1.3 puan, 2026'da 1.3 puan — ama oransal maliyeti farklı).
  T2 SÜRÜKLEME ÇIKARILMIŞ SERİ  Her yılın ortalama log-getirisi bar bazında çıkarılır
     (bar-içi şekil korunur). Bu bir STRATEJİ DEĞİL, ATFETME testidir: avantaj
     sürüklemeden mi geliyor? (Yıllık ortalama ileriye-bakan bilgidir; bilerek.)
  T3 AL-TUT KIYASI  Aynı giriş noktalarından 24 saat TP/SL'siz tutmak ne veriyor?
     Geometriler bunu geçebiliyor mu?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA

HORIZON = 24
SPREAD_PTS = 1.3          # broker ölçümü (medyan); kayma ≈ 0 (218/218 tam seviye)


def load() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1h.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    return d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)


def demean_by_year(d: pd.DataFrame) -> pd.DataFrame:
    """Bar-içi şekli koruyarak yıllık ortalama log-getiriyi sıfırla."""
    d = d.copy()
    lr = np.log(d["close"] / d["close"].shift(1)).fillna(0.0)
    yr = d["ts"].dt.year
    adj = lr - lr.groupby(yr).transform("mean")
    newc = np.exp(adj.cumsum()) * d["close"].iloc[0]
    scale = newc / d["close"]
    for c in ("open", "high", "low", "close"):
        d[c] = d[c] * scale
    return d


def evaluate(d: pd.DataFrame, label: str) -> pd.DataFrame:
    pc = d["close"].shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean().shift(1).to_numpy()

    o, h, l, c = (d[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(d) - HORIZON - 1
    idx = np.arange(n)[:, None] + np.arange(HORIZON)[None, :]
    entry = o[:n]
    up = np.maximum.accumulate(h[idx] - entry[:, None], axis=1)
    dn = np.minimum.accumulate(l[idx] - entry[:, None], axis=1)
    end_move = c[idx[:, -1]] - entry
    a = atr[:n]
    year = pd.DatetimeIndex(d["ts"].to_numpy()[:n]).year
    week = pd.PeriodIndex(pd.DatetimeIndex(d["ts"].to_numpy()[:n]), freq="W")
    ok = np.isfinite(a) & (a > 0)

    def boot_ci(r, m, B=2000, seed=11):
        rng = np.random.default_rng(seed)
        w = week[m]; vals = r[m]
        uw = np.unique(w)
        by = {x: vals[w == x] for x in uw}
        out = np.empty(B)
        for i in range(B):
            pick = rng.choice(uw, size=len(uw), replace=True)
            out[i] = np.concatenate([by[x] for x in pick]).mean()
        return np.quantile(out, 0.05), np.quantile(out, 0.95), (out > 0).mean()

    rows = []
    # AL-TUT: stop yok, 24 saat tut. R birimi = 1 ATR (kıyas edilebilirlik için)
    r_bh = (end_move - SPREAD_PTS) / a
    lo, hi, p = boot_ci(r_bh, ok)
    rows.append(dict(geometri="AL-TUT (TP/SL yok, 24s)", rr=np.nan, wr=float((r_bh[ok] > 0).mean()),
                     ev=float(r_bh[ok].mean()), ci5=lo, ci95=hi, p_poz=p,
                     **{f"y{y}": round(float(r_bh[ok & (year == y)].mean()), 3)
                        for y in (2018, 2022, 2026)}))
    for tp_a, sl_a in ((0.727, 1.0), (1.0, 1.0), (1.5, 1.0), (2.0, 1.0), (3.0, 1.0), (4.0, 1.0)):
        tp, sl = a * tp_a, a * sl_a
        hit_tp, hit_sl = up >= tp[:, None], dn <= -sl[:, None]
        a_tp, a_sl = hit_tp.any(1), hit_sl.any(1)
        t_tp = np.where(a_tp, hit_tp.argmax(1), 10**6)
        t_sl = np.where(a_sl, hit_sl.argmax(1), 10**6)
        win = a_tp & (t_tp < t_sl)
        loss = a_sl & (t_sl <= t_tp)
        opn = ~win & ~loss
        r = np.where(win, (tp - SPREAD_PTS) / sl, np.where(loss, -(sl + SPREAD_PTS) / sl, 0.0))
        r = np.where(opn, (end_move - SPREAD_PTS) / sl, r)
        lo, hi, p = boot_ci(r, ok)
        rows.append(dict(geometri=f"ATR {tp_a}/{sl_a}", rr=round(tp_a / sl_a, 2),
                         wr=float(win[ok].mean()), ev=float(r[ok].mean()),
                         ci5=lo, ci95=hi, p_poz=p,
                         **{f"y{y}": round(float(r[ok & (year == y)].mean()), 3)
                            for y in (2018, 2022, 2026)}))
    df = pd.DataFrame(rows).round(4)
    print(f"\n══════ {label} ══════")
    print(df.to_string(index=False))
    return df


def main() -> None:
    pd.set_option("display.width", 220)
    d = load()
    print(f"veri: {len(d)} saatlik bar  {d.ts.min()} → {d.ts.max()}")
    print(f"sürtünme = {SPREAD_PTS} puan (broker ölçümü), kayma = 0 (218/218 tam seviye dolum)")
    a = evaluate(d, "T1 — GERÇEK SERİ (sürükleme dahil)")
    b = evaluate(demean_by_year(d), "T2 — SÜRÜKLEME ÇIKARILMIŞ SERİ (atfetme testi)")
    m = a[["geometri", "ev"]].merge(b[["geometri", "ev"]], on="geometri",
                                    suffixes=("_gercek", "_suruklemesiz"))
    m["surukleme_payi"] = (m.ev_gercek - m.ev_suruklemesiz).round(4)
    print("\n══════ ATFETME: EV'nin ne kadarı sürüklemeden geliyor? ══════")
    print(m.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
