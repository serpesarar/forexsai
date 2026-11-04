"""ON — gece sürüklenmesi motoru (PROTOCOL.md). Saf fonksiyonlar; sonuç üretmez."""
from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

R = "/Users/melihcanodacioglu/Desktop/panel/research"
sys.path.insert(0, R + "/ndx_gate_forge")

DISC_END = pd.Timestamp("2026-07-01")
LOCK_END = pd.Timestamp("2026-10-03")
SPREAD = 1.5
ARR_USD = {2016: .40, 2017: 1.00, 2018: 1.83, 2019: 2.16, 2020: .38, 2021: .08, 2022: 1.68,
           2023: 5.02, 2024: 5.14, 2025: 4.21, 2026: 3.64}
ARR_EUR = {y: 0.0 for y in range(2016, 2023)} | {2023: 3.25, 2024: 3.65, 2025: 2.20, 2026: 2.19}
ADMIN = 2.5
VIX_TH = 18.4


@dataclass(frozen=True)
class Win:
    code: str
    tz: str
    ent: tuple            # (gün_ofseti, saat, dakika) ; gün_ofseti: 0 = D, -1 = önceki AÇIK gün, 'pcal' = önceki takvim günü/Pazar
    ext: tuple
    cond: str = ""        # "", "dn0.5", "dn1.0", "vix", "dn0.5vix"


def load_bars(kind: str) -> pd.DataFrame:
    if kind == "ndx1h" or kind == "ndx30m":
        from long_data import load_long
        d = load_long(kind[3:])
    elif kind == "ndx1m":
        d = pd.read_parquet(R + "/ndx_pattern_motifs/data/bars_1m.parquet")
    elif kind == "ndx30m_new":
        d = pd.read_parquet(R + "/ndx_pattern_motifs/data/bars_30m.parquet")
    elif kind.startswith("dax"):
        d = pd.read_parquet(R + f"/ndx_gate_forge/data/dax_{kind[3:]}.parquet")
    else:
        raise ValueError(kind)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    return d[["ts", "open", "high", "low", "close"]]


class Px:
    """Fiyat(T) arayıcı. exact=True → tam T barı; aksi hâlde ilk bar ≥T, ≤T+tol."""

    def __init__(self, bars: pd.DataFrame, exact: bool, tol_min: int = 5):
        self.t = bars.ts.dt.tz_convert("UTC").values.astype("datetime64[ns]").astype(np.int64)
        self.o = bars.open.to_numpy(float)
        self.exact, self.tol = exact, tol_min * 60 * 10**9

    def get(self, ts_utc: np.ndarray, delay_min: int = 0) -> np.ndarray:
        q = ts_utc.astype("datetime64[ns]").astype(np.int64)
        bad = q == np.iinfo(np.int64).min
        q = q + delay_min * 60 * 10**9
        i = np.searchsorted(self.t, q)
        i2 = np.clip(i, 0, len(self.t) - 1)
        ok = (i < len(self.t)) & ~bad
        if self.exact:
            ok &= self.t[i2] == q
        else:
            ok &= (self.t[i2] >= q) & (self.t[i2] - q <= self.tol)
        out = np.where(ok, self.o[i2], np.nan)
        return out


def local_ts(dates: pd.DatetimeIndex, h: int, m: int, tz: str) -> np.ndarray:
    naive = pd.DatetimeIndex(dates.normalize() + pd.Timedelta(hours=h, minutes=m))
    loc = naive.tz_localize(tz, ambiguous="NaT", nonexistent="NaT")
    return loc.tz_convert("UTC").tz_localize(None).values


def trading_days(bars: pd.DataFrame, tz: str, ref_h: int, ref_m: int) -> pd.DatetimeIndex:
    """Pzt–Cum günleri, referans (kapanış) barı mevcut olanlar."""
    loc = bars.ts.dt.tz_convert(tz)
    mask = (loc.dt.hour == ref_h) & (loc.dt.minute == ref_m) & (loc.dt.weekday < 5)
    return pd.DatetimeIndex(sorted(set(loc[mask].dt.tz_localize(None).dt.normalize())))


def build_events(bars: pd.DataFrame, win: Win, ref: tuple, exact: bool, macro: pd.DataFrame | None,
                 arr: dict, delay: int = 0, spread: float = SPREAD, ref_tz: str | None = None) -> pd.DataFrame:
    """Her D için giriş/çıkış fiyatı, swap, R. ref=(saat,dk) günlük kapanış referansı (σ ve önceki gün getirisi)."""
    tz = win.tz
    px = Px(bars, exact)
    pxe = Px(bars, True) if exact else px
    rtz = ref_tz or tz
    days = trading_days(bars, rtz, *ref)
    # günlük referans fiyatları (σ20, önceki gün)
    p_ref = pd.Series(pxe.get(local_ts(days, *ref, rtz)), index=days)
    p_ref = p_ref.dropna()
    days = p_ref.index
    r_d = p_ref.pct_change()
    sig = r_d.rolling(20, min_periods=15).std()
    df = pd.DataFrame(index=days)
    df["prevD"] = pd.Series(days, index=days).shift(1)
    df["r_prev"] = r_d.shift(1)          # P(D−1)/P(D−2)−1
    df["sig"] = sig.shift(1)             # D−1'e kadar
    df = df.iloc[1:].copy()
    D = pd.DatetimeIndex(df.index)

    def when(spec):
        off, h, m = spec
        if off == 0:
            base = D
        elif off == -1:
            base = pd.DatetimeIndex(df.prevD)
        elif off == "pcal":     # önceki takvim günü; Pazartesi için Pazar
            base = D - pd.Timedelta(days=1)
        else:
            raise ValueError(off)
        return local_ts(base, h, m, tz), base

    te, be = when(win.ent)
    tx, bx = when(win.ext)
    df["p_in_opt"] = pxe.get(te) if exact else px.get(te)
    df["p_out_opt"] = pxe.get(tx) if exact else px.get(tx)
    df["p_in"] = px.get(te, delay)
    df["p_out"] = px.get(tx, delay)
    df["t_in"] = pd.to_datetime(te)
    df["nights"] = np.asarray((bx - be).days, float)
    # 17:00 ET rollover'ı geçiyor mu: ET'de giriş < 17:00 ve gece sayısı>0 (S1 18:00 girişi geçmez)
    t_in_et = pd.to_datetime(te).tz_localize("UTC").tz_convert("America/New_York")
    t_out_et = pd.to_datetime(tx).tz_localize("UTC").tz_convert("America/New_York")
    in_min = (t_in_et.hour * 60 + t_in_et.minute).to_numpy()
    out_min = (t_out_et.hour * 60 + t_out_et.minute).to_numpy()
    roll = ((pd.DatetimeIndex(t_out_et.normalize().tz_localize(None)) - pd.DatetimeIndex(t_in_et.normalize().tz_localize(None))).days).to_numpy().astype(float)
    roll = roll + (in_min >= 17 * 60) * -1 + (out_min >= 17 * 60) * 1
    df["rolls"] = np.clip(roll, 0, None)
    yr = D.year
    rate = np.array([arr.get(y, arr[max(arr)]) for y in yr]) + ADMIN
    df["swap_pts"] = df.p_in * rate / 100 / 360 * df.rolls
    if macro is not None:
        v = macro.VIX_close.dropna()
        df["vix"] = v.reindex(pd.DatetimeIndex(df.prevD), method="ffill").to_numpy()
    else:
        df["vix"] = np.nan
    df = df.dropna(subset=["p_in", "p_out", "sig"])
    df["gross_pts"] = df.p_out - df.p_in
    df["gross_opt_pts"] = df.p_out_opt - df.p_in_opt
    df["net_pts"] = df.gross_pts - spread - df.swap_pts
    unit = df.sig * df.p_in
    df["R"] = df.net_pts / unit
    df["R_gross"] = df.gross_pts / unit
    df["R_opt"] = df.gross_opt_pts / unit - df.swap_pts / unit
    df["R_sp15"] = (df.gross_pts - 1.5 * spread - df.swap_pts) / unit
    df["R_sp3"] = (df.gross_pts - 3.0 - df.swap_pts) / unit
    df["ret_net"] = df.net_pts / df.p_in
    df["ret_gross"] = df.gross_pts / df.p_in
    df = apply_cond(df, win.cond)
    return df


def apply_cond(df: pd.DataFrame, c: str) -> pd.DataFrame:
    if c == "":
        return df
    m = pd.Series(True, index=df.index)
    if "dn0.5" in c:
        m &= df.r_prev <= -0.005
    if "dn1.0" in c:
        m &= df.r_prev <= -0.010
    if "vix" in c:
        m &= df.vix >= VIX_TH
    return df[m.fillna(False)]


def month_boot(df: pd.DataFrame, col: str = "R", n: int = 5000, seed: int = 7) -> float:
    if len(df) == 0:
        return np.nan
    g = df.groupby(df.index.to_period("M"))[col]
    s, c = g.sum().to_numpy(), g.count().to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n, len(s)))
    means = s[idx].sum(1) / c[idx].sum(1)
    return float((means > 0).mean())


def month_boot_diff(a: pd.DataFrame, b: pd.DataFrame, col="R", n=5000, seed=11) -> float:
    """P(mean(a) − mean(b) > 0), aylar ortak örneklenir."""
    ma = a.groupby(a.index.to_period("M"))[col].agg(["sum", "count"])
    mb = b.groupby(b.index.to_period("M"))[col].agg(["sum", "count"])
    j = ma.join(mb, lsuffix="a", rsuffix="b", how="outer").fillna(0)
    arr = j.to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n, len(arr)))
    S = arr[idx].sum(1)
    d = S[:, 0] / np.maximum(S[:, 1], 1) - S[:, 2] / np.maximum(S[:, 3], 1)
    return float((d > 0).mean())


def card(df: pd.DataFrame, exec_df: pd.DataFrame | None = None) -> dict:
    n = len(df)
    if n == 0:
        return {"n": 0}
    half = n // 2
    h1, h2 = df.R.iloc[:half].mean(), df.R.iloc[half:].mean()
    P = month_boot(df)
    m = df.R.mean()
    top5 = df.R.sort_values(ascending=False).iloc[5:].mean() if n > 10 else np.nan
    out = dict(n=n, wr=(df.R > 0).mean(), ortR=m, P=P, h1=h1, h2=h2, sp15=df.R_sp15.mean(), sp3=df.R_sp3.mean(),
               bp_gross=df.ret_gross.mean() * 1e4, bp_net=df.ret_net.mean() * 1e4, pts_net=df.net_pts.mean(),
               swap_pts=df.swap_pts.mean(), ex_top5=top5,
               overlap=int(((df.t_in.shift(-1) - df.t_in) <= pd.Timedelta(0)).sum()))
    c = [n >= 150, m > 0 and P >= 0.90, h1 >= 0 and h2 >= 0, out["sp15"] > 0]
    if exec_df is not None and len(exec_df) > 20:
        rr, ro = exec_df.R.mean(), exec_df.R_opt.mean()
        out.update(exec_n=len(exec_df), exec_real=rr, exec_opt=ro)
        c.append(bool(rr > 0 and (ro - rr) < rr / 2))
    else:
        c.append(None)
    c.append(out["overlap"] == 0)
    out["crit"] = c
    out["pass"] = sum(bool(x) for x in c)
    return out
