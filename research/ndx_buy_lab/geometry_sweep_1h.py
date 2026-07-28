"""geometry_sweep_1h.py — 10 YILLIK stres testi (2016-05 → 2026-07, 1h çözünürlük).

NEDEN ŞART: 15m ızgarası 2023-03'te başlıyor ve içinde GERÇEK BİR AYI PİYASASI YOK
(2023-2026 baştan sona boğa + düzeltmeler). "Yüksek RR long her yıl +EV" bulgusu
o örneklemde beta'dan (yukarı sürüklenme) geliyor olabilir. Bu dosya aynı testi
2018 Q4 çöküşü, 2020 COVID çöküşü ve 2022 ayı piyasasını İÇEREN 10 yıla uzatır.

Çözünürlük 1h → TP/SL vuruş sırası daha kaba. Kalibrasyon: çakışan dönemde
(2023-03→2026-07) 15m sonucuyla kıyaslanır; sapma raporlanır.
Aynı barda TP+SL → SL önce (konservatif, her geometride aynı).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from geometry_sweep import build_paths, outcomes

HORIZON = 24          # 24 × 1h = 24 saat (15m ızgarasındaki 96×15m ile aynı)
FRIC = 1.0 / 29000


def load() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1h.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    pc = d["close"].shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    d["atr_pct"] = (atr / d["close"]).shift(1)      # karar anında BİLİNEN (kapanmış bar)
    return d


def run(direction: str, geoms) -> pd.DataFrame:
    d = load()
    entry, cmax, cmin, end_ret = build_paths(d, HORIZON)
    n = len(entry)
    a = d["atr_pct"].to_numpy()[:n]
    ts = pd.DatetimeIndex(d["ts"].to_numpy()[:n])
    year = ts.year
    ok = np.isfinite(a) & (a > 0)
    sgn = 1.0 if direction == "BUY" else -1.0
    years = sorted(set(year[ok]))
    rows = []
    for tp_a, sl_a in geoms:
        tp, sl = a * tp_a, a * sl_a
        win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, direction)
        r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
        r = np.where(opn, (sgn * end_ret - FRIC) / sl, r)
        rec = dict(tp=tp_a, sl=sl_a, rr=round(tp_a / sl_a, 2), n=int(ok.sum()),
                   wr=float(win[ok].mean()), ev=float(r[ok].mean()),
                   acik=float(opn[ok].mean()))
        pos = 0
        for y in years:
            m = ok & (year == y)
            v = float(r[m].mean()) if m.sum() else np.nan
            rec[f"y{y}"] = round(v, 4)
            pos += int(v > 0)
        rec["poz_yil"] = pos
        rec["yil_sayisi"] = len(years)
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    pd.set_option("display.width", 260)
    geoms = [(0.5, 1.0), (0.75, 1.0), (1.0, 1.0), (1.25, 1.0), (1.5, 1.0),
             (2.0, 1.0), (2.5, 1.0), (3.0, 1.0), (4.0, 1.0),
             (1.5, 0.75), (2.0, 0.75), (3.0, 0.75), (2.0, 1.5), (3.0, 1.5),
             (0.727, 1.0)]     # botun bugünkü RR'si (80/110), ATR-ölçekli karşılığı
    for direction in ("BUY", "SELL"):
        df = run(direction, geoms)
        df.to_csv(DATA / f"geometry_1h_{direction}.csv", index=False)
        print(f"\n══════ {direction} — 10 YIL (1h çözünürlük) ══════")
        print(df.sort_values("ev", ascending=False).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
