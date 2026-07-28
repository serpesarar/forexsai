"""long_atr_gates.py — kapıların 3.4 yılda ve DOĞRU (ATR-ölçekli) geometride sınavı.

Neden gerekli: kapı karşılaştırmalarını şimdiye kadar ya (a) 5 aylık pencerede
doğru geometriyle, ya (b) 3.4 yılda YANLIŞ (sabit %, RR 0.73) geometriyle yaptık.
Bu dosya ikisini birleştirir: 2023-03→2026-07, TP/SL = H1 ATR katları.

Kapılar:
  MOM   botun canlı momentum filtresi (M15_stoch>70 & M15_dist_ema20>0.8 & H1_SAR>0)
  K1    H1 güçlü ayı trendi DEĞİL  (~(H1_adx>25 & -DI>+DI))
  K2    H4 ayı yapısı DEĞİL
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA, add_indicators, asof_features

HORIZON = 96      # 96 × 15m = 24 saat
FRIC = 1.0


def resample(d15: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = (d15.set_index("ts").resample(rule, label="left", closed="left")
         .agg({"open": "first", "high": "max", "low": "min",
               "close": "last", "volume": "sum"}).dropna(subset=["open"]))
    return g.reset_index()


def main() -> None:
    pd.set_option("display.width", 250)
    d = pd.read_csv(DATA / "long_15m.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)

    f15 = add_indicators(d, "M15")[["known_at", "M15_stoch_k", "M15_dist_ema20_atr"]]
    f1h = add_indicators(resample(d, "1h"), "H1")[
        ["known_at", "H1_atr", "H1_adx", "H1_di_diff", "H1_sar_dist_atr"]]
    f4h = add_indicators(resample(d, "4h"), "H4")[
        ["known_at", "H4_ema20_slope_atr", "H4_sar_dist_atr"]]
    base = d[["ts", "open", "high", "low", "close"]].copy()
    for f in (f15, f1h, f4h):
        base = asof_features(base, f.assign(ts=f["known_at"])).drop(columns=["known_at"])

    o = base["open"].to_numpy(); h = base["high"].to_numpy()
    l = base["low"].to_numpy(); c = base["close"].to_numpy()
    n = len(base) - HORIZON - 1
    idx = np.arange(n)[:, None] + np.arange(HORIZON)[None, :]
    entry = o[:n]
    up = np.maximum.accumulate(h[idx] - entry[:, None], axis=1)
    dn = np.minimum.accumulate(l[idx] - entry[:, None], axis=1)
    end_move = c[idx[:, -1]] - entry

    x = base.iloc[:n].reset_index(drop=True)
    atr = x["H1_atr"].to_numpy()
    year = pd.DatetimeIndex(x["ts"]).year
    ok = np.isfinite(atr) & (atr > 0)

    GATES = {
        "kapı YOK": np.ones(n, bool),
        "MOM (canlı filtre)": ((x.M15_stoch_k > 70) & (x.M15_dist_ema20_atr > 0.8)
                               & (x.H1_sar_dist_atr > 0)).to_numpy(),
        "~MOM (MOM'un eledikleri)": ~((x.M15_stoch_k > 70) & (x.M15_dist_ema20_atr > 0.8)
                                      & (x.H1_sar_dist_atr > 0)).to_numpy(),
        "K1 (H1 güçlü ayı DEĞİL)": ~((x.H1_adx > 25) & (x.H1_di_diff < 0)).to_numpy(),
        "K2 (H4 ayı yapısı DEĞİL)": ~((x.H4_ema20_slope_atr < 0)
                                      & (x.H4_sar_dist_atr < 0)).to_numpy(),
        "K1 & MOM": (~((x.H1_adx > 25) & (x.H1_di_diff < 0))
                     & ((x.M15_stoch_k > 70) & (x.M15_dist_ema20_atr > 0.8)
                        & (x.H1_sar_dist_atr > 0))).to_numpy(),
        "K1 & ~MOM": (~((x.H1_adx > 25) & (x.H1_di_diff < 0))
                      & ~((x.M15_stoch_k > 70) & (x.M15_dist_ema20_atr > 0.8)
                          & (x.H1_sar_dist_atr > 0))).to_numpy(),
        "K1 & K2": (~((x.H1_adx > 25) & (x.H1_di_diff < 0))
                    & ~((x.H4_ema20_slope_atr < 0) & (x.H4_sar_dist_atr < 0))).to_numpy(),
    }
    years = sorted(set(year[ok]))

    for tp_a, sl_a in ((0.67, 0.92), (1.5, 1.0), (2.0, 1.0), (3.0, 1.0)):
        tp, sl = atr * tp_a, atr * sl_a
        hit_tp = up >= tp[:, None]
        hit_sl = dn <= -sl[:, None]
        a_tp, a_sl = hit_tp.any(1), hit_sl.any(1)
        t_tp = np.where(a_tp, hit_tp.argmax(1), 10**6)
        t_sl = np.where(a_sl, hit_sl.argmax(1), 10**6)
        win = a_tp & (t_tp < t_sl)
        loss = a_sl & (t_sl <= t_tp)
        opn = ~win & ~loss
        r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
        r = np.where(opn, (end_move - FRIC) / sl, r)
        label = "BOT BUGÜN (0.67/0.92 ATR ≈ 80/110 puan)" if tp_a == 0.67 else f"ATR {tp_a}/{sl_a}"
        print(f"\n══════ {label} · RR {tp_a/sl_a:.2f} ══════")
        rows = []
        for name, g in GATES.items():
            m = ok & np.nan_to_num(g, nan=False).astype(bool)
            if m.sum() < 1500:
                continue
            rec = dict(kapı=name, kapsam=round(m.sum() / ok.sum(), 3), n=int(m.sum()),
                       wr=round(float(win[m].mean()), 4), ev=round(float(r[m].mean()), 4),
                       toplamR=round(float(r[m].sum()), 0))
            pos = 0
            for y in years:
                mm = m & (year == y)
                v = float(r[mm].mean()) if mm.sum() > 200 else np.nan
                rec[f"y{y}"] = round(v, 4)
                pos += int(v > 0)
            rec["poz_yıl"] = f"{pos}/{len(years)}"
            rows.append(rec)
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
