"""HEKA kitabı sınamaları — ortak veri, gösterge, icra ve plasebo motoru (ön kayıt: PROTOCOL.md)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

GF = ROOT / "research/ndx_gate_forge/data"
PB = ROOT / "research/pinbar_20261010/data"
SRC = {
    ("NDX", "1h"): GF / "long_1h_utc.parquet", ("NDX", "30m"): GF / "long_30m_utc.parquet",
    ("DAX", "1h"): GF / "dax_1h.parquet", ("DAX", "30m"): GF / "dax_30m.parquet",
    ("XAU", "1h"): PB / "XAUUSD_1h.parquet", ("XAU", "30m"): PB / "XAUUSD_30m.parquet",
    ("OIL", "1h"): PB / "USOIL_1h.parquet", ("OIL", "30m"): PB / "USOIL_30m.parquet",
}
SPREAD = {"NDX": 1.3, "DAX": 1.5, "XAU": 0.12, "OIL": 0.028}
TF_MIN = {"30m": 30, "1h": 60}
START = {"DAX": pd.Timestamp("2019-01-01", tz="UTC")}   # DAX 1h 2019 öncesi seyrek
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")
SYMS = ["NDX", "DAX", "XAU", "OIL"]
N_PLACEBO = 20
RNG_SEED = 20261021


def load(sym: str, tf: str) -> pd.DataFrame:
    d = pd.read_parquet(SRC[(sym, tf)])
    if "src" in d.columns:
        d = d[d.src == "broker"]
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    if sym in START:
        d = d[d.ts >= START[sym]].reset_index(drop=True)
    d = d[["ts", "open", "high", "low", "close"]].astype({c: float for c in ["open", "high", "low", "close"]})
    d["atr"] = atr(d)
    gap = d.ts.diff().shift(-1) > pd.Timedelta(minutes=3 * TF_MIN[tf])
    # her barın ait olduğu kesintisiz bloğun son bar indeksi
    blk = np.cumsum(np.r_[0, gap.values[:-1].astype(int)])
    last = pd.Series(np.arange(len(d))).groupby(blk).transform("max").values
    d["blk_end"] = last
    d["year"] = d.ts.dt.year
    d["hour"] = d.ts.dt.hour
    return d


def atr(d: pd.DataFrame, n: int = 14) -> np.ndarray:
    pc = d.close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean().values


def ema(x: pd.Series, n: int) -> np.ndarray:
    return x.ewm(span=n, adjust=False).mean().values


def rsi(x: pd.Series, n: int = 14) -> np.ndarray:
    dlt = x.diff()
    up = dlt.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-dlt.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).values


@dataclass
class Trade:
    entry_i: int
    exit_i: int
    r: float
    r_stress: float
    hit: str


def simulate(d: pd.DataFrame, sig_i: int, direction: int, sl_dist: float, tp_dist: float | None,
             max_bars: int, spread: float, exit_at: int | None = None, exit_fn=None) -> Trade | None:
    """Karar barı sig_i (kapanmış) → giriş sig_i+1 açılışı. exit_at: zorla kapanış bar indeksi (kapanışında);
    exit_fn(j) True → j barının kapanışından sonraki açılışta çık. Aynı barda TP+SL → SL."""
    o, h, l, c, be = d.open.values, d.high.values, d.low.values, d.close.values, d.blk_end.values
    e = sig_i + 1
    if e >= len(d) or not np.isfinite(sl_dist) or sl_dist <= 0 or be[sig_i] < e:
        return None
    px = o[e]
    stop = px - direction * sl_dist
    tgt = None if tp_dist is None else px + direction * tp_dist
    last = min(e + max_bars - 1, be[e], len(d) - 1)
    if exit_at is not None:
        last = min(last, exit_at)
    exit_px, hit, j = c[last], "time", last
    for j in range(e, last + 1):
        if j > e and (o[j] - stop) * direction <= 0:          # boşlukla stop ötesi açılış
            exit_px, hit = o[j], "sl"
            break
        lo_hit = (l[j] <= stop) if direction > 0 else (h[j] >= stop)
        tp_hit = tgt is not None and ((h[j] >= tgt) if direction > 0 else (l[j] <= tgt))
        if lo_hit:
            exit_px, hit = stop, "sl"
            break
        if tp_hit:
            exit_px, hit = tgt, "tp"
            break
        if exit_fn is not None and j < last and exit_fn(j):
            exit_px, hit, j = o[j + 1], "rule", j + 1
            break
    else:
        j = last
    gross = (exit_px - px) * direction
    return Trade(e, j, (gross - spread) / sl_dist, (gross - 1.5 * spread) / sl_dist, hit)


def placebo_pool(d: pd.DataFrame, key_cols=("year", "hour")) -> dict:
    g = d.groupby(list(key_cols)).indices
    return {k: np.asarray(v) for k, v in g.items()}


def day_boot(df: pd.DataFrame, col: str = "d", n: int = 2000, seed: int = RNG_SEED) -> float:
    """Gün-blok bootstrap: P(ortalama col > 0)."""
    if len(df) == 0:
        return np.nan
    rng = np.random.default_rng(seed)
    g = df.groupby(df.day)[col].agg(["sum", "count"])
    s, cnt = g["sum"].values, g["count"].values
    idx = rng.integers(0, len(g), size=(n, len(g)))
    m = s[idx].sum(1) / cnt[idx].sum(1)
    return float((m > 0).mean())


def boot_diff(a: pd.DataFrame, b: pd.DataFrame, col: str = "r", n: int = 2000, seed: int = RNG_SEED) -> float:
    """İki grubun ort. farkı (a−b) için gün-blok bootstrap P(>0); günler birleşik kümeden çekilir."""
    if len(a) == 0 or len(b) == 0:
        return np.nan
    rng = np.random.default_rng(seed)
    days = np.union1d(a.day.unique(), b.day.unique())
    ga = a.groupby("day")[col].agg(["sum", "count"]).reindex(days, fill_value=0)
    gb = b.groupby("day")[col].agg(["sum", "count"]).reindex(days, fill_value=0)
    idx = rng.integers(0, len(days), size=(n, len(days)))
    ma = ga["sum"].values[idx].sum(1) / np.maximum(ga["count"].values[idx].sum(1), 1)
    mb = gb["sum"].values[idx].sum(1) / np.maximum(gb["count"].values[idx].sum(1), 1)
    return float((ma - mb > 0).mean())


def holm(p: pd.Series, alpha: float = 0.05) -> pd.Series:
    order = p.sort_values().index
    m, ok, cont = len(p), {}, True
    for k, i in enumerate(order):
        cont = cont and p[i] <= alpha / (m - k)
        ok[i] = cont
    return pd.Series(ok).reindex(p.index)


def run_with_placebo(d: pd.DataFrame, sig: pd.DataFrame, sym: str, make_trade, pool_key=("year", "hour"),
                     seed: int = RNG_SEED) -> pd.DataFrame:
    """sig: index sütunu 'i', 'dir'. make_trade(i, dir, ref=None) → Trade (ref: gerçek işlem, süre/ölçü eşleme için).
    Tek pozisyon/sembol/yön kuralı uygulanır. Dönüş: işlem başına R, plasebo ort. R ve fark d."""
    rng = np.random.default_rng(seed + SYMS.index(sym))
    pool = placebo_pool(d, pool_key)
    rows, busy = [], {1: -1, -1: -1}
    keys = d[list(pool_key)].values
    for i, direction in zip(sig.i.values, sig.dir.values):
        if i <= busy[direction]:
            continue
        t = make_trade(int(i), int(direction), None)
        if t is None:
            continue
        busy[direction] = t.exit_i
        cand = pool.get(tuple(keys[i]), np.array([]))
        cand = cand[(cand != i) & (cand < len(d) - 2)]
        pr = []
        if len(cand):
            for pi in rng.choice(cand, size=min(N_PLACEBO, len(cand)), replace=len(cand) < N_PLACEBO):
                pt = make_trade(int(pi), int(direction), t)
                if pt is not None:
                    pr.append(pt.r)
        ts = d.ts.iloc[t.entry_i]
        rows.append(dict(sym=sym, i=int(i), dir=int(direction), ts=ts, day=ts.normalize(), r=t.r,
                         r_stress=t.r_stress, hit=t.hit, bars=t.exit_i - t.entry_i + 1,
                         plc=np.mean(pr) if pr else np.nan))
    out = pd.DataFrame(rows)
    if len(out):
        out["d"] = out.r - out.plc
        out["period"] = np.where(out.ts < SPLIT, "dev", "test")
    return out


def summarize(t: pd.DataFrame, cell: str) -> dict:
    t = t.dropna(subset=["d"])
    if len(t) == 0:
        return dict(cell=cell, n=0)
    top5 = t.groupby("day").r.sum().nlargest(5).index
    rest = t[~t.day.isin(top5)]
    per = {p: g.d.mean() for p, g in t.groupby("period")}
    sym_pos = sum(g.d.mean() > 0 for _, g in t.groupby("sym"))
    return dict(cell=cell, n=len(t), n_days=t.day.nunique(), ortR=t.r.mean(), plcR=t.plc.mean(), fark=t.d.mean(),
                P=day_boot(t), fark_dev=per.get("dev", np.nan), fark_test=per.get("test", np.nan),
                sym_pos=f"{sym_pos}/{t.sym.nunique()}", ortR_x15=t.r_stress.mean(), ortR_ex5=rest.r.mean(),
                wr=(t.r > 0).mean())
