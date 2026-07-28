"""regime_gate_10y.py — yüksek-RR NDX long'a REJİM KAPISI (11 yıl, 2016-2026).

Bulgu (geometry_sweep_1h): ATR 2.0/1.0 long 11 yılın 8'inde +EV; kaybettiği tek
büyük yıl 2022 (ayı piyasası). Soru: basit, mekanizması açık bir rejim kapısı
2022'yi eleyip diğer yılları koruyor mu? Öyleyse bu, kullanıcının istediği
"filtre + kombinasyon" — ve 11 yıl boyunca test edilmiş olur.

Kapı adayları (hepsi karar anında BİLİNEN, günlük veriden, 1 gün gecikmeli):
  R1  fiyat > günlük EMA200            (klasik ayı-piyasası şalteri)
  R2  fiyat > günlük EMA50
  R3  günlük EMA50 > günlük EMA200     (altın kesişim rejimi)
  R4  20 günlük getiri > 0
  R5  60 günlük zirveden düşüş > -%10  (derin düzeltmede long yok)
  R6  VIX < 28                          (panik rejiminde long yok)
  R7  R1 ve R6 birlikte
  R8  R3 ve (60g zirveden düşüş > -%15)

Sızıntı: günlük özellikler her zaman shift(1) — o günün kapanışı karar anında
bilinemez. VIX aynı şekilde önceki kapanış.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from geometry_sweep import build_paths, outcomes

HORIZON = 24
FRIC = 1.0 / 29000


def daily_regime() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1d.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    c = d["close"]
    f = pd.DataFrame({"ts": d["ts"]})
    f["d_close"] = c.shift(1)
    f["ema50"] = c.ewm(span=50, adjust=False).mean().shift(1)
    f["ema200"] = c.ewm(span=200, adjust=False).mean().shift(1)
    f["ret20d"] = (c / c.shift(20) - 1).shift(1) * 100
    f["ret60d"] = (c / c.shift(60) - 1).shift(1) * 100
    f["dd60"] = (c / c.rolling(60).max() - 1).shift(1) * 100
    f["dd120"] = (c / c.rolling(120).max() - 1).shift(1) * 100
    f["above_ema200"] = (f.d_close > f.ema200).astype(float)
    f["above_ema50"] = (f.d_close > f.ema50).astype(float)
    f["golden"] = (f.ema50 > f.ema200).astype(float)
    # günlük bar 00:00 UTC → değerler o günün başından itibaren bilinir
    f["known_at"] = f["ts"]
    return f.drop(columns=["ts"])


def macro() -> pd.DataFrame:
    m = pd.read_csv(DATA / "macro_daily.csv", parse_dates=["date"]).sort_values("date")
    m["date"] = pd.to_datetime(m["date"], utc=True)
    out = pd.DataFrame({"known_at": m["date"] + pd.Timedelta(days=1)})
    out["vix"] = m["VIX_close"].values
    out["vix_ma20"] = m["VIX_close"].rolling(20).mean().values
    return out


def main() -> None:
    pd.set_option("display.width", 260)
    d = pd.read_csv(DATA / "long_1h.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    pc = d["close"].shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr_pct"] = (tr.ewm(alpha=1 / 14, adjust=False).mean() / d["close"]).shift(1)

    reg = daily_regime()
    mac = macro()
    d = pd.merge_asof(d, reg.sort_values("known_at"), left_on="ts",
                      right_on="known_at", direction="backward").drop(columns=["known_at"])
    d = pd.merge_asof(d, mac.sort_values("known_at"), left_on="ts",
                      right_on="known_at", direction="backward").drop(columns=["known_at"])

    entry, cmax, cmin, end_ret = build_paths(d, HORIZON)
    n = len(entry)
    a = d["atr_pct"].to_numpy()[:n]
    ts = pd.DatetimeIndex(d["ts"].to_numpy()[:n])
    year = ts.year
    dd = d.iloc[:n]
    ok = np.isfinite(a) & (a > 0)

    GATES = {
        "kapı YOK (taban)":              np.ones(n, bool),
        "R1 fiyat>günlük EMA200":        dd.above_ema200.to_numpy() > 0.5,
        "R2 fiyat>günlük EMA50":         dd.above_ema50.to_numpy() > 0.5,
        "R3 EMA50>EMA200 (altın kesiş)": dd.golden.to_numpy() > 0.5,
        "R4 20g getiri>0":               dd.ret20d.to_numpy() > 0,
        "R5 60g zirveden düşüş>-%10":    dd.dd60.to_numpy() > -10,
        "R6 VIX<28":                     dd.vix.to_numpy() < 28,
        "R7 R1 & R6":                    (dd.above_ema200.to_numpy() > 0.5) & (dd.vix.to_numpy() < 28),
        "R8 R3 & düşüş>-%15":            (dd.golden.to_numpy() > 0.5) & (dd.dd120.to_numpy() > -15),
        "R9 R1 & 20g getiri>0":          (dd.above_ema200.to_numpy() > 0.5) & (dd.ret20d.to_numpy() > 0),
    }
    years = sorted(set(year[ok]))

    for tp_a, sl_a in ((2.0, 1.0), (3.0, 1.0), (1.5, 1.0), (0.727, 1.0)):
        tp, sl = a * tp_a, a * sl_a
        win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, "BUY")
        r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
        r = np.where(opn, (end_ret - FRIC) / sl, r)
        print(f"\n══════ LONG · ATR TP {tp_a} / SL {sl_a} (RR {tp_a/sl_a:.2f}) ══════")
        rows = []
        for name, g in GATES.items():
            m = ok & np.nan_to_num(g, nan=False).astype(bool)
            if m.sum() < 500:
                continue
            rec = dict(kapı=name, n=int(m.sum()), kapsam=round(m.sum() / ok.sum(), 3),
                       wr=round(float(win[m].mean()), 4), ev=round(float(r[m].mean()), 4),
                       toplamR=round(float(r[m].sum()), 1))
            pos = 0
            for y in years:
                mm = m & (year == y)
                v = float(r[mm].mean()) if mm.sum() > 50 else np.nan
                rec[f"y{y}"] = round(v, 3)
                pos += int(v > 0)
            rec["poz_yıl"] = pos
            rows.append(rec)
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
