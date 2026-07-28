"""final_combo_10y.py — hayatta kalan tek fikrin 11 yıllık sınavı.

Madencilikte HİÇBİR "giriş" kuralı kör TEST'i geçemedi. Ama birkaç "KAÇIN"
kuralı 3 yıllık holdout'ta tutarlı negatif lift verdi ve mekanizması açık:
  → onaylanmış çok-zaman-dilimli DÜŞÜŞ trendinin içine long açma.
Bu dosya o fikri, tek gerçek kaldıraç olan YÜKSEK RR geometrisiyle birlikte,
11 yıla (2016-2026, 2018/2020/2022 düşüşleri dahil) uygular.

Ayrıca ÇOKLU-TEST dürüstlüğü: aynı anda N kapı deneniyor. Her kapının yanına
aynı kapsamda RASTGELE (gün-bloklu) plasebo kapılarının dağılımı konur — gerçek
kapı plasebo dağılımının neresinde?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features
from geometry_sweep import build_paths, outcomes
from regime_gate_10y import daily_regime, macro

HORIZON = 24
FRIC = 1.0 / 29000
RNG = np.random.default_rng(4242)


def resample_1h(d1h: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = (d1h.set_index("ts").resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last", "volume": "sum"}).dropna(subset=["open"]))
    return g.reset_index()


def build() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1h.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    pc = d["close"].shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr_pct"] = (tr.ewm(alpha=1 / 14, adjust=False).mean() / d["close"]).shift(1)

    h1f = add_indicators(d, "H1")
    h4f = add_indicators(resample_1h(d, "4h"), "H4")
    base = d[["ts", "open", "high", "low", "close", "atr_pct"]].copy()
    base = asof_features(base, h1f).drop(columns=["known_at"])
    base = asof_features(base, h4f).drop(columns=["known_at"])
    base = pd.merge_asof(base, daily_regime().sort_values("known_at"), left_on="ts",
                         right_on="known_at", direction="backward").drop(columns=["known_at"])
    base = pd.merge_asof(base, macro().sort_values("known_at"), left_on="ts",
                         right_on="known_at", direction="backward").drop(columns=["known_at"])
    base["et_hour"] = base.ts.dt.tz_convert("America/New_York").dt.hour
    return base


def main() -> None:
    pd.set_option("display.width", 270)
    b = build()
    entry, cmax, cmin, end_ret = build_paths(b, HORIZON)
    n = len(entry)
    x = b.iloc[:n].reset_index(drop=True)
    a = x["atr_pct"].to_numpy()
    ts = pd.DatetimeIndex(x["ts"])
    year, day = ts.year, ts.date
    ok = np.isfinite(a) & (a > 0)

    def col(name):
        return x[name].to_numpy() if name in x.columns else np.full(n, np.nan)

    h1_bear = (col("H1_adx") > 25) & (col("H1_di_diff") < 0)
    h4_bear = (col("H4_ema20_slope_atr") < 0) & (col("H4_sar_dist_atr") < 0)
    mtf_bear = h1_bear & (col("H4_dist_ema50_atr") < 0)
    risk_off = (col("vix") > col("vix_ma20"))
    below_ema50d = col("above_ema50") < 0.5

    GATES = {
        "kapı YOK":                       np.ones(n, bool),
        "K1 H1 güçlü ayı DEĞİL":          ~h1_bear,
        "K2 H4 ayı yapısı DEĞİL":         ~h4_bear,
        "K3 MTF ayı DEĞİL (H1+H4)":       ~mtf_bear,
        "K4 VIX 20g ort. ÜSTÜNDE DEĞİL":  ~risk_off,
        "K5 K1 & K2":                     ~h1_bear & ~h4_bear,
        "K6 K3 & K4":                     ~mtf_bear & ~risk_off,
        "K7 K1 & günlük EMA50 üstü":      ~h1_bear & ~below_ema50d,
        "K8 K5 & günlük EMA50 üstü":      ~h1_bear & ~h4_bear & ~below_ema50d,
    }
    years = sorted(set(year[ok]))

    for tp_a, sl_a in ((2.0, 1.0), (3.0, 1.0), (0.727, 1.0)):
        tp, sl = a * tp_a, a * sl_a
        win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, "BUY")
        r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
        r = np.where(opn, (end_ret - FRIC) / sl, r)
        base_ev = r[ok].mean()
        print(f"\n══════ LONG · ATR TP {tp_a} / SL {sl_a} (RR {tp_a/sl_a:.2f}) · taban EV {base_ev:+.4f} ══════")
        rows = []
        for name, g in GATES.items():
            m = ok & np.nan_to_num(g, nan=False).astype(bool)
            if m.sum() < 2000:
                continue
            ev = float(r[m].mean())
            # gün-bloklu plasebo: aynı kapsamda rastgele GÜN kümesi
            days = np.array(sorted(set(day[ok])))
            k = int(round(len(days) * m.sum() / ok.sum()))
            worse = 0
            for _ in range(400):
                pick = set(RNG.choice(days, size=max(k, 1), replace=False))
                mm = ok & np.array([d in pick for d in day])
                if mm.sum() < 100:
                    continue
                worse += float(r[mm].mean()) >= ev
            rec = dict(kapı=name, kapsam=round(m.sum() / ok.sum(), 3), n=int(m.sum()),
                       wr=round(float(win[m].mean()), 4), ev=round(ev, 4),
                       toplamR=round(float(r[m].sum()), 0),
                       plasebo_p=round(worse / 400, 3))
            pos = 0
            for y in years:
                mm = m & (year == y)
                v = float(r[mm].mean()) if mm.sum() > 50 else np.nan
                rec[f"y{y}"] = round(v, 3)
                pos += int(v > 0)
            rec["poz_yıl"] = f"{pos}/{len(years)}"
            rows.append(rec)
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
