"""Ön-kayıt: PROTOCOL.md. python3 research/ndx_sell_dusus_20261008/run.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi.stats import boot_mean_ci  # noqa: E402

DATA = ROOT / "research" / "ndx_gate_forge" / "data"
TP_PCT, SL_PCT, HALF_SPREAD_PCT = 0.00258, 0.00355, 0.000025
VIX_T = 18.4
SESSION = (14, 19.5)
MAX_HOLD_H = 72


def bars(name: str) -> pd.DataFrame:
    d = pd.read_parquet(DATA / f"{name}.parquet")
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.set_index("ts").sort_index()
    d["ema20"] = d.close.ewm(span=20, adjust=False).mean()
    d["ema50"] = d.close.ewm(span=50, adjust=False).mean()
    mid, sd = d.close.rolling(20).mean(), d.close.rolling(20).std(ddof=0)
    d["bb_up"] = mid + 2 * sd
    vix = pd.read_csv(DATA / "macro_daily_patched.csv", parse_dates=["date"]).set_index("date")["VIX_close"]
    prev = vix.shift(1)                                           # önceki günün kapanışı (E20)
    d["vix_prev"] = prev.reindex(d.index.tz_localize(None).normalize(), method="ffill").to_numpy()
    return d


def regimes(d: pd.DataFrame) -> pd.DataFrame:
    daily = d.close.resample("1D").last().dropna()
    m = daily.resample("ME").last().pct_change()
    lab = np.where(m <= -0.03, "DÜŞÜŞ", np.where(m >= 0.03, "YÜKSELİŞ", "YATAY"))
    month_lab = pd.Series(lab, index=m.index.strftime("%Y-%m"))
    dd = daily / daily.rolling(252, min_periods=60).max() - 1
    bear = (dd <= -0.15)
    d = d.copy()
    d["ay_rejim"] = d.index.strftime("%Y-%m").map(month_lab).fillna("YATAY")
    d["ayi"] = pd.Series(bear.reindex(d.index.normalize().tz_localize(None).tz_localize("UTC"), method="ffill").to_numpy(),
                         index=d.index).fillna(False)
    return d


def signals(d: pd.DataFrame) -> dict[str, tuple[np.ndarray, int]]:
    h = d.index.hour + d.index.minute / 60
    ses = np.asarray((h >= SESSION[0]) & (h <= SESSION[1]) & (d.index.dayofweek < 5))
    ret2 = d.close.pct_change(2).to_numpy()
    c, e20, e50, bb = (d[k].to_numpy() for k in ("close", "ema20", "ema50", "bb_up"))
    vix = d.vix_prev.to_numpy()
    return {"S0 taban SELL": (ses, -1), "S1 VIXREG SELL (VIX<18,4)": (ses & (vix < VIX_T), -1),
            "S1b VIXREG BUY (VIX≥18,4)": (ses & (vix >= VIX_T), 1),
            "S2 momentum SELL": (ses & (c < e50) & (e20 < e50) & (ret2 < 0), -1),
            "S3 kanal-üst SELL": (ses & (c >= bb), -1)}


def simulate(d: pd.DataFrame, sig: np.ndarray, s: int, tp_mult: float, bar_h: float) -> pd.DataFrame:
    o, hi, lo, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    n, maxk = len(d), int(MAX_HOLD_H / bar_h)
    rows, i = [], 0
    idx = np.flatnonzero(sig)
    busy_until = -1
    for i in idx:
        j = i + 1
        if j >= n or i <= busy_until:
            continue
        e = o[j] * (1 + s * HALF_SPREAD_PCT)
        tp, sl = e * (1 + s * TP_PCT * tp_mult), e * (1 - s * SL_PCT)
        hit_tp = (hi[j:j + maxk] >= tp) if s > 0 else (lo[j:j + maxk] <= tp)
        hit_sl = (lo[j:j + maxk] <= sl) if s > 0 else (hi[j:j + maxk] >= sl)
        kt = np.flatnonzero(hit_tp); ks = np.flatnonzero(hit_sl)
        k_t = kt[0] if kt.size else np.inf; k_s = ks[0] if ks.size else np.inf
        if np.isinf(k_t) and np.isinf(k_s):
            k = min(maxk, n - j) - 1
            R = s * (c[j + k] - e) / (e * SL_PCT)
        else:
            k = int(min(k_t, k_s))
            R = -1.0 if k_s <= k_t else TP_PCT * tp_mult / SL_PCT
        busy_until = j + k
        rows.append({"ts": d.index[i], "R": R, "ay_rejim": d.ay_rejim.iat[i], "ayi": bool(d.ayi.iat[i]),
                     "yil": d.index[i].year})
    return pd.DataFrame(rows)


def summary(r: pd.DataFrame, by: str) -> pd.DataFrame:
    out = []
    for k, g in r.groupby(by):
        lo, hi, p = boot_mean_ci(g.R.to_numpy(float))
        out.append({by: k, "n": len(g), "WR%": round(100 * (g.R > 0).mean(), 1), "ort_R": round(g.R.mean(), 3),
                    "%95": f"{lo:+.2f}…{hi:+.2f}", "P(>0)": round(p, 2), "top_R": round(g.R.sum(), 1)})
    return pd.DataFrame(out)


def run(name: str, bar_h: float) -> pd.DataFrame:
    d = regimes(bars(name))
    allr = []
    for sname, (sig, s) in signals(d).items():
        for tpm in (1.0, 2.0):
            r = simulate(d, sig, s, tpm, bar_h)
            r["strateji"], r["geo"] = sname, f"TP×{tpm:g}"
            allr.append(r)
    return pd.concat(allr, ignore_index=True)


def main() -> None:
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    pd.set_option("display.width", 220)
    for name, bh, label in (("long_30m_utc", 0.5, "30m 2021-06→2026-07 (ANA)"), ("long_1h_utc", 1.0, "1h 2016-05→2026-07")):
        r = run(name, bh)
        if name == "long_1h_utc":
            r = r[r.ts < pd.Timestamp("2021-06-29", tz="UTC")]
            label = "1h 2016-05→2021-06 (ikincil)"
        r.to_csv(out / f"{name}.csv", index=False)
        print(f"\n################ {label}")
        for (sname, geo), g in r.groupby(["strateji", "geo"]):
            print(f"\n--- {sname} [{geo}]  (başabaş WR TP×1 %57,9 / TP×2 %40,8)")
            print(pd.concat([summary(g, "ay_rejim"), summary(g.assign(ayi_p=np.where(g.ayi, "AYI (tepeden ≥%15)", "ayı değil")), "ayi_p")
                             .rename(columns={"ayi_p": "ay_rejim"})]).to_string(index=False))


if __name__ == "__main__":
    main()
