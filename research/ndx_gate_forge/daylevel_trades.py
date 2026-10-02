"""Gün-düzeyi aday kapıların İŞLEM düzeyinde (80/110 eşdeğeri) ölçümü — 30m (5y), 15m (3.4y), 1m (2025-26).

30m/15m: yüzde geometri TP %0.348 / SL %0.478 (23k'da 80/110), sonraki barlarla ilk-geçiş,
aynı barda ikisi → SL, en uzun 12 saat, spread %0.006. 1m: gerçek bid/ask G80 etiketleri.
Fark = koşul içindeki R − (yıl/dönem × UTC saati × yön) tabanı.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

from common import OUT, DATA, block_boot
from long_data import load_long, macro
from macro10y import FOMC

TP, SL, SPR = 0.00348, 0.00478, 0.00006


@njit(cache=True)
def walk_pct(t, o, h, l, c, idx, side, tp, sl, spr, maxhold, gapmax):
    n = idx.shape[0]
    R = np.full(n, np.nan)
    N = t.shape[0]
    for k in range(n):
        i = idx[k]
        j = i + 1
        if j >= N or t[j] - t[i] > gapmax:
            continue
        s = side[k]
        e = o[j] * (1 + s * spr)
        tpp = e * (1 + s * tp)
        slp = e * (1 - s * sl)
        jj = j
        r = np.nan
        while jj < N:
            if jj > j and t[jj] - t[jj - 1] > gapmax:
                r = s * (c[jj - 1] / e - 1)
                break
            if s == 1:
                if l[jj] <= slp:
                    r = min(o[jj], slp) / e - 1 if jj > j else slp / e - 1
                    break
                if h[jj] >= tpp:
                    r = tp
                    break
            else:
                if h[jj] >= slp:
                    r = -(max(o[jj], slp) / e - 1) if jj > j else -(slp / e - 1)
                    break
                if l[jj] <= tpp:
                    r = tp
                    break
            if t[jj] - t[j] >= maxhold:
                r = s * (c[jj] / e - 1)
                break
            jj += 1
        R[k] = r / sl
    return R


def day_conditions(nyd: pd.Series, nyh: pd.Series, wd: pd.Series) -> pd.DataFrame:
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    last = lambda s: s.dropna().reindex(full).ffill()
    prev = nyd - pd.Timedelta(days=1)
    ndx = m.NDXCASH_close.dropna()
    x = pd.DataFrame(index=nyd.index)
    x["vix"] = last(m.VIX_close).reindex(prev).to_numpy()
    x["vix_ts"] = last(m.VIX_close / m.VIX3M_close).reindex(prev).to_numpy()
    x["vix_chg1"] = last(m.VIX_close.dropna().pct_change()).reindex(prev).to_numpy()
    x["ndx_ret1"] = last(ndx.pct_change()).reindex(prev).to_numpy()
    x["ndx_ret5"] = last(ndx.pct_change(5)).reindex(prev).to_numpy()
    x["ndx_d200"] = last(ndx / ndx.rolling(200).mean() - 1).reindex(prev).to_numpy()
    mtd = ndx / ndx.groupby(ndx.index.to_period("M")).transform("first") - 1
    x["mtd"] = last(mtd).reindex(prev).to_numpy()
    days = pd.Series(sorted(nyd.unique()))
    rev = days.groupby(days.dt.to_period("M")).cumcount(ascending=False)
    x["month_end2"] = nyd.isin(set(days[rev <= 1])).to_numpy()
    x["wd"] = wd.to_numpy()
    fomc = pd.to_datetime(FOMC)
    x["fomc_eve"] = (nyd.isin(fomc - pd.Timedelta(days=1)) & (nyh >= 14)).to_numpy()
    return x


GATES = {
    # ad: (koşul, bloklanan yön)
    "VIXREG yön (VIX<18.4 → BUY yok, ≥18.4 → SELL yok)": (None, None),
    "Dünkü düşüş ≤−%1.5 → SELL yok": (lambda x: x.ndx_ret1 <= -.015, "S"),
    "5g ≤−%4 → SELL yok": (lambda x: x.ndx_ret5 <= -.04, "S"),
    "VIX sıçrama ≥+%15 → SELL yok": (lambda x: x.vix_chg1 >= .15, "S"),
    "VIX eğrisi ters (≥1) → SELL yok": (lambda x: x.vix_ts >= 1.0, "S"),
    "STRES (herhangi biri) → SELL yok": (lambda x: (x.ndx_ret1 <= -.015) | (x.ndx_ret5 <= -.04) | (x.vix_chg1 >= .15) | (x.vix_ts >= 1.0), "S"),
    "Pazartesi → SELL yok": (lambda x: x.wd == 0, "S"),
    "Perşembe → BUY yok": (lambda x: x.wd == 3, "B"),
    "Ay sonu & MTD≥+4% → BUY yok": (lambda x: x.month_end2 & (x.mtd >= .04), "B"),
    "Ay sonu & MTD≤−4% → SELL yok": (lambda x: x.month_end2 & (x.mtd <= -.04), "S"),
    "200g +%10 üstü → BUY yok": (lambda x: x.ndx_d200 > .10, "B"),
    "FOMC arifesi 14:00+ → SELL yok": (lambda x: x.fomc_eve, "S"),
}


def long_trades(tf: str) -> pd.DataFrame:
    d = load_long(tf)
    step = {"15m": 900, "30m": 1800}[tf]
    t = (d.ts.astype("int64") // 10**9).to_numpy()
    ny = d.ts.dt.tz_convert("America/New_York")
    d["nyd"] = pd.to_datetime(ny.dt.date.values)
    d["nyh"] = ny.dt.hour.values
    d["wd"] = ny.dt.weekday.values
    d["utc_h"] = d.ts.dt.hour.values
    dec_h = ((d.ts + pd.Timedelta(seconds=step)).dt.hour).values
    ok = (d.wd <= 3) & (dec_h >= 7) & (dec_h <= 20)
    idx = np.flatnonzero(ok.to_numpy())
    o, h, l, c = (d[k].to_numpy(float) for k in ["open", "high", "low", "close"])
    out = d.iloc[idx][["ts", "nyd", "nyh", "wd", "utc_h"]].reset_index(drop=True)
    for s, sn in [(1, "B"), (-1, "S")]:
        out[f"R_{sn}"] = walk_pct(t, o, h, l, c, idx, np.full(len(idx), s), TP, SL, SPR, 12 * 3600, 3 * 3600)
    out["grp"] = out.nyd.dt.year.astype(str)
    return out


def m1_trades() -> pd.DataFrame:
    from evaluate import load
    d = load(1)
    out = pd.DataFrame({"nyd": pd.to_datetime(d.ny_date), "nyh": d.ny_min // 60, "wd": d.wd, "utc_h": d.utc_h,
                        "R_B": d.R_G80_B, "R_S": d.R_G80_S, "grp": d.period})
    # 1m'de her dakika giriş → 15 dakikada bir örnekle (bağımlılık/işlem sıklığı gerçekçi)
    return out.iloc[::15].reset_index(drop=True)


def score(T: pd.DataFrame, label: str) -> list[dict]:
    x = day_conditions(T.nyd, T.nyh, T.wd)
    rows = []
    for s in "BS":
        T[f"y_{s}"] = T[f"R_{s}"] - T.groupby(["grp", "utc_h"])[f"R_{s}"].transform("mean")
    for name, (fn, side) in GATES.items():
        if fn is None:
            mb = (x.vix < 18.4).to_numpy()
            ms = (x.vix >= 18.4).to_numpy()
            parts = [("B", mb), ("S", ms)]
        else:
            parts = [(side, fn(x).fillna(False).to_numpy(bool))]
        vals, days, grps = [], [], []
        for s, m in parts:
            v = T[f"y_{s}"].to_numpy()[m]
            ok = ~np.isnan(v)
            vals.append(v[ok]); days.append(T.nyd.astype(str).to_numpy()[m][ok]); grps.append(T.grp.to_numpy()[m][ok])
        v, dd, gg = np.concatenate(vals), np.concatenate(days), np.concatenate(grps)
        if len(v) == 0:
            continue
        bs = block_boot(v, dd, 3000)
        per = pd.Series(v).groupby(gg).mean()
        rows.append({"veri": label, "kapı": name, "gün": len(np.unique(dd)), "bloklanan_fark_R": v.mean(),
                     "P(<0)": float(np.mean(bs < 0)), "grup_doğru": int((per < 0).sum()), "grup": int(len(per)),
                     "gruplar": " ".join(f"{k}:{val:+.2f}" for k, val in per.items())})
    return rows


if __name__ == "__main__":
    rows = []
    for tf in ["30m", "15m"]:
        rows += score(long_trades(tf), tf)
    rows += score(m1_trades(), "1m")
    r = pd.DataFrame(rows)
    pd.set_option("display.width", 300); pd.set_option("display.max_colwidth", 140)
    for k, g in r.groupby("kapı", sort=False):
        print("\n##", k)
        print(g.drop(columns="kapı").round(3).to_string(index=False))
    r.to_csv(OUT / "daylevel_trades.csv", index=False)
