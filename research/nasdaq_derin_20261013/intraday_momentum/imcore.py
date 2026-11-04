"""Ortak çekirdek: veri yükleme, saat ekseni, gün tablosu, R hesabı, bootstrap/permütasyon.

Ön kayıt: PROTOCOL.md. Tüm zamanlar bar BAŞLANGICI UTC damgalı; yerel saat zoneinfo ile.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
HERE = ROOT / "research/nasdaq_derin_20261013/intraday_momentum"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
MOT = ROOT / "research/ndx_pattern_motifs/data"
GF = ROOT / "research/ndx_gate_forge"
sys.path.insert(0, str(GF))

LOCK = pd.Timestamp("2026-07-01")          # kasa başlangıcı (NY tarihi)
COST = 1.5                                  # puan / işlem (gidiş-dönüş)
STRESS = 1.5
VIX_TH = 18.4


def macro() -> pd.DataFrame:
    m = pd.read_csv(GF / "data/macro_daily_patched.csv", parse_dates=["date"]).set_index("date").sort_index()
    return m


def load_ndx(tf: str) -> pd.DataFrame:
    """N1h / N30 / N1m — UTC bar başlangıcı."""
    if tf == "1h":
        from long_data import load_long
        d = load_long("1h")[["ts", "open", "high", "low", "close"]]
        bad = (d.ts >= pd.Timestamp("2017-11-05", tz="UTC")) & (d.ts < pd.Timestamp("2018-03-12", tz="UTC"))
        return d[~bad].reset_index(drop=True)          # PROTOCOL Ek-1
    if tf == "30m":
        from long_data import load_long
        a = load_long("30m")[["ts", "open", "high", "low", "close"]]
        b = pd.read_parquet(MOT / "bars_30m.parquet")[["ts", "open", "high", "low", "close"]]
        a = a[a.ts < b.ts.min()]
        return pd.concat([a, b]).sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    if tf == "1m":
        return pd.read_parquet(MOT / "bars_1m.parquet")[["ts", "open", "high", "low", "close"]]
    raise ValueError(tf)


def load_dax(tf: str = "30m", fix: bool = True) -> pd.DataFrame:
    """PROTOCOL Ek-1: NY standart saatindeyken kaynak 60 dk erken etiketli → +60 dk."""
    d = pd.read_parquet(GF / f"data/dax_{tf}.parquet")[["ts", "open", "high", "low", "close"]].copy()
    if fix:
        us_dst = d.ts.dt.tz_convert("America/New_York").map(lambda t: bool(t.dst())).to_numpy()
        d.loc[~us_dst, "ts"] = d.ts[~us_dst] + pd.Timedelta(minutes=60)
        d = d.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    return d


def localize(d: pd.DataFrame, tz: str, step: int) -> pd.DataFrame:
    d = d.copy()
    lt = d.ts.dt.tz_convert(tz)
    d["date"] = pd.to_datetime(lt.dt.date.values)
    d["m0"] = (lt.dt.hour * 60 + lt.dt.minute).values
    d["m1"] = d.m0 + step
    d["wd"] = lt.dt.weekday.values
    d["year"] = lt.dt.year.values
    return d


def axis_check(d: pd.DataFrame, tz: str, step: int) -> pd.DataFrame:
    """Yıl başına medyan aralığın en büyük olduğu yerel dakika (yalnız hafta içi)."""
    x = localize(d, tz, step)
    x = x[x.wd <= 4]
    x["rng"] = x.high - x.low
    g = x.groupby(["year", "m0"]).rng.median().reset_index()
    pk = g.loc[g.groupby("year").rng.idxmax()]
    return pk.assign(hhmm=pk.m0.map(lambda v: f"{v // 60:02d}:{v % 60:02d}"))[["year", "hhmm", "rng"]]


# ---------------------------------------------------------------- takvim
def us_half_days(years: range) -> set:
    out = set()
    for y in years:
        nov = pd.date_range(f"{y}-11-01", f"{y}-11-30")
        thu = nov[nov.weekday == 3][3]
        out.add(thu + pd.Timedelta(days=1))
        d24 = pd.Timestamp(f"{y}-12-24")
        if d24.weekday() <= 3:
            out.add(d24)
        j4 = pd.Timestamp(f"{y}-07-04")
        if 1 <= j4.weekday() <= 4:
            out.add(pd.Timestamp(f"{y}-07-03"))
    return out


def day_table(d: pd.DataFrame, tz: str, step: int, close_pts: list[int], open_pts: list[int],
              fh: tuple[int, int] | None, valid_days: set | None, excl: set) -> pd.DataFrame:
    """Gün başına: P{t}=bitişi t olan barın kapanışı; O{t}=t'de başlayan barın açılışı; FH aralığı."""
    x = localize(d, tz, step)
    x = x[x.wd <= 4]
    cols = {}
    for t in close_pts:
        s = x[x.m1 == t].groupby("date").close.last()
        cols[f"P{t}"] = s
    for t in open_pts:
        s = x[x.m0 == t].groupby("date").open.first()
        cols[f"O{t}"] = s
    T = pd.DataFrame(cols)
    if fh is not None:
        w = x[(x.m0 >= fh[0]) & (x.m1 <= fh[1])]
        g = w.groupby("date")
        need = (fh[1] - fh[0]) // step
        ok = g.size() >= need
        T["FH_hi"] = g.high.max()[ok]
        T["FH_lo"] = g.low.min()[ok]
    if valid_days is not None:
        T = T[T.index.isin(valid_days)]
    T = T[~T.index.isin(excl)]
    T = T.sort_index()
    return T


def add_prev_close(T: pd.DataFrame, close_col: str, max_gap_days: int = 4) -> pd.DataFrame:
    T = T.copy()
    s = T[close_col]
    prev = s.shift(1)
    gap = pd.Series(T.index, index=T.index).diff().dt.days
    T["C0"] = np.where(gap <= max_gap_days, prev, np.nan)
    return T


def add_dvol_ndx(T: pd.DataFrame) -> pd.DataFrame:
    m = macro()
    nd = m.NDXCASH_close.dropna()
    vol = nd.pct_change().rolling(20).std()
    full = pd.date_range("2014-01-01", "2026-12-31")
    prev = T.index - pd.Timedelta(days=1)
    T = T.copy()
    T["dvol"] = vol.reindex(full).ffill().reindex(prev).to_numpy()
    T["vix"] = m.VIX_close.dropna().reindex(full).ffill().reindex(prev).to_numpy()
    return T


def add_dvol_own(T: pd.DataFrame, close_col: str) -> pd.DataFrame:
    T = T.copy()
    r = T[close_col].pct_change()
    T["dvol"] = r.rolling(20).std().shift(1)
    m = macro()
    full = pd.date_range("2014-01-01", "2026-12-31")
    prev = T.index - pd.Timedelta(days=1)
    T["vix"] = m.VIX_close.dropna().reindex(full).ffill().reindex(prev).to_numpy()
    return T


def nyse_days() -> set:
    m = macro()
    return set(m.NDXCASH_close.dropna().index)


# ---------------------------------------------------------------- işlem
def trades(T: pd.DataFrame, sig: pd.Series, entry_col: str, exit_col: str, cost: float = COST,
           opt_col: str | None = None) -> pd.DataFrame:
    """sig: +1/-1/0 (NaN → yok). entry_col gerçek giriş (sonraki bar açılışı), opt_col iyimser (karar barı kapanışı)."""
    s = np.sign(sig)
    ok = s.notna() & (s != 0) & T[entry_col].notna() & T[exit_col].notna() & T.dvol.notna()
    X = T[ok].copy()
    X["side"] = s[ok]
    e, x = X[entry_col], X[exit_col]
    X["raw"] = x - e
    X["scale"] = e * X.dvol
    X["pts"] = X.side * (x - e) - cost
    X["R"] = X.pts / (e * X.dvol)
    X["bp"] = X.pts / e * 1e4
    if opt_col is not None:
        eo = X[opt_col]
        X["R_opt"] = (X.side * (x - eo)) / (eo * X.dvol)
    X["R_long"] = ((x - e) - cost) / (e * X.dvol)
    return X


def boot_p(v: np.ndarray, n: int = 4000, seed: int = 7, block: int = 1) -> tuple[float, float, float]:
    """Gün-blok (block=1) veya ardışık-blok bootstrap. Dönüş: P(ort>0), %2,5, %97,5."""
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) < 5 or len(v) <= block:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    if block <= 1:
        idx = rng.integers(0, len(v), size=(n, len(v)))
        mu = v[idx].mean(1)
    else:
        nb = int(np.ceil(len(v) / block))
        st = rng.integers(0, len(v) - block + 1, size=(n, nb))
        idx = (st[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, :len(v)]
        mu = v[idx].mean(1)
    return float((mu > 0).mean()), float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))


def perm_p(X: pd.DataFrame, n: int = 2000, seed: int = 11, cost: float = COST) -> tuple[float, float]:
    """İşaret permütasyonu: yön dizisini günler arasında karıştır → ortR boş dağılımı. Dönüş (p, boş ort)."""
    rng = np.random.default_rng(seed)
    side, raw, scale = X.side.to_numpy(), X.raw.to_numpy(), X.scale.to_numpy()
    obs = np.mean((side * raw - cost) / scale)
    null = np.array([np.mean((rng.permutation(side) * raw - cost) / scale) for _ in range(n)])
    return float((null >= obs).mean()), float(null.mean())


def summarize(X: pd.DataFrame, label: str) -> dict:
    if len(X) == 0:
        return {"id": label, "n": 0}
    v = X.R.to_numpy()
    P, lo, hi = boot_p(v)
    P20, _, _ = boot_p(v, block=20)
    h = len(X) // 2
    out = {
        "id": label, "n": int(len(X)), "ortR": round(float(v.mean()), 4),
        "ort_puan": round(float(X.pts.mean()), 2), "ort_bp": round(float(X.bp.mean()), 2),
        "WR": round(float((v > 0).mean()), 3), "P_EV>0": round(P, 3), "P_EV>0_blok20": round(P20, 3),
        "CI95": [round(lo, 4), round(hi, 4)],
        "yari1": round(float(v[:h].mean()), 4), "yari2": round(float(v[h:].mean()), 4),
        "hepAL_ortR": round(float(X.R_long.mean()), 4),
        "fark_hepAL": round(float(v.mean() - X.R_long.mean()), 4),
        "long_payi": round(float((X.side > 0).mean()), 3),
    }
    return out


def yearly(X: pd.DataFrame) -> dict:
    g = X.groupby(X.index.year)
    return {int(y): [int(len(s)), round(float(s.R.mean()), 4), round(float(s.R_long.mean()), 4)] for y, s in g}


def ols(y: np.ndarray, x: np.ndarray) -> dict:
    ok = np.isfinite(y) & np.isfinite(x)
    y, x = y[ok], x[ok]
    if len(y) < 10:
        return {}
    xm, ym = x.mean(), y.mean()
    b = ((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum()
    a = ym - b * xm
    res = y - a - b * x
    r2 = 1 - (res ** 2).sum() / ((y - ym) ** 2).sum()
    se = np.sqrt((res ** 2).sum() / (len(y) - 2) / ((x - xm) ** 2).sum())
    return {"b_x100": round(b * 100, 2), "t": round(b / se, 2), "R2_pct": round(r2 * 100, 2), "n": int(len(y))}
