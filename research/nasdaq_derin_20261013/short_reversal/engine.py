"""Kısa vadeli dip alımı motoru — ön kayıt PROTOCOL.md (2026-10-13).

Günlük karar (t kapanışı) → giriş = kapanış barından SONRAKİ barın açılışı + maliyet; çıkış aynı mekanik.
Birim σR = PnL / (σ_d × giriş), σ_d = son 20 günlük günlük getiri std'si (t'de bilinen).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

GF = "/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge"
sys.path.insert(0, GF)
from long_data import load_long, macro  # noqa: E402

SPREAD_PT = 1.5
SLIP_PT = 0.2
SWAP_ANNUAL = 0.06
VIX_TH = 18.4
DISC_END = pd.Timestamp("2026-07-01")
LOCK_END = pd.Timestamp("2026-10-02")
MOTIF = "/Users/melihcanodacioglu/Desktop/panel/research/ndx_pattern_motifs/data"


@dataclass
class Market:
    name: str
    bars: pd.DataFrame        # ts, open, high, low, close (bar başlangıcı UTC)
    day: pd.DataFrame         # gün başına: C,H,L,ci (kapanış barı idx), e2i (ertesi RTH açılış barı idx), göstergeler


def _daily(bars: pd.DataFrame, tz: str, step: int, close_start: int, hl_from: int, rth_open: int) -> pd.DataFrame:
    loc = bars.ts.dt.tz_convert(tz)
    nyd = pd.to_datetime(loc.dt.date.values)
    m = (loc.dt.hour * 60 + loc.dt.minute).to_numpy()
    b = pd.DataFrame({"nyd": nyd, "m": m, "i": np.arange(len(bars))})
    cb = b[b.m == close_start].groupby("nyd").i.last()
    hl = b[(b.m >= hl_from) & (b.m <= close_start)]
    H = hl.groupby("nyd").i.apply(lambda s: bars.high.to_numpy()[s.to_numpy()].max())
    L = hl.groupby("nyd").i.apply(lambda s: bars.low.to_numpy()[s.to_numpy()].min())
    cnt = hl.groupby("nyd").size()
    need = (close_start - hl_from) // step + 1
    ro = b[b.m == rth_open].groupby("nyd").i.first()
    d = pd.DataFrame({"ci": cb}).join(pd.DataFrame({"H": H, "L": L, "cnt": cnt}), how="left")
    d = d[(d.cnt >= 0.8 * need)]
    d["C"] = bars.close.to_numpy()[d.ci.to_numpy()]
    d["e2i"] = ro.reindex(d.index).shift(-1)    # ertesi işlem gününün RTH açılış barı
    d.index.name = "nyd"
    return d.drop(columns="cnt")


def add_ind(d: pd.DataFrame, warm: pd.Series | None = None) -> pd.DataFrame:
    """Göstergeler. warm: CFD başlangıcından önceki günler için nakit kapanış (oranla eklenir, yalnız MA200 ısınması)."""
    c = d.C.copy()
    if warm is not None:
        w = warm[warm.index < c.index[0]].dropna()
        common = warm.reindex(c.index).dropna()
        if len(w) and len(common):
            k = c.loc[common.index[0]] / common.iloc[0]
            c = pd.concat([w * k, c])
    ma200 = c.rolling(200).mean()
    d["ma200"] = ma200.reindex(d.index)
    C = d.C
    ch = C.diff()
    up = ch.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    dn = (-ch).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    d["rsi2"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    d.loc[dn == 0, "rsi2"] = 100.0
    d["ma5"] = C.rolling(5).mean()
    d["ret"] = C.pct_change()
    d["sig"] = d.ret.rolling(20).std()
    for n in (3, 5, 10):
        d[f"low{n}"] = C <= C.rolling(n).min()
    d["dn3"] = (ch < 0) & (ch.shift(1) < 0) & (ch.shift(2) < 0)
    d["ibs"] = (C - d.L) / (d.H - d.L).replace(0, np.nan)
    vix = macro().VIX_close.dropna()
    full = pd.date_range("2010-01-01", "2026-12-31")
    d["vix_prev"] = vix.reindex(full).ffill().reindex(d.index - pd.Timedelta(days=1)).to_numpy()
    return d


def ndx_1h() -> Market:
    b = load_long("1h")[["ts", "open", "high", "low", "close"]].reset_index(drop=True)
    d = _daily(b, "America/New_York", 60, 900, 540, 600)
    d = add_ind(d, macro().NDXCASH_close)
    return Market("NDX1h", b, d)


def ndx_30m() -> Market:
    b = pd.read_parquet(f"{MOTIF}/bars_30m.parquet")[["ts", "open", "high", "low", "close"]].reset_index(drop=True)
    d = _daily(b, "America/New_York", 30, 930, 570, 570)
    d = add_ind(d, macro().NDXCASH_close)
    return Market("NDX30m", b, d)


def dax_1h() -> Market:
    b = pd.read_parquet(f"{GF}/data/dax_1h.parquet")
    b = b[b.ts >= "2019-01-01"][["ts", "open", "high", "low", "close"]].reset_index(drop=True)
    d = _daily(b, "Europe/Berlin", 60, 1020, 540, 540)
    d = add_ind(d, None)
    return Market("DAX1h", b, d)


# ───────────────────────── sinyaller / ızgara ─────────────────────────
SIGNALS = {
    "RSI5": lambda d: d.rsi2 < 5, "RSI10": lambda d: d.rsi2 < 10, "RSI15": lambda d: d.rsi2 < 15,
    "LOW3": lambda d: d.low3, "LOW5": lambda d: d.low5, "LOW10": lambda d: d.low10,
    "IBS20": lambda d: d.ibs < 0.2, "IBS30": lambda d: d.ibs < 0.3,
    "DN3": lambda d: d.dn3,
    "DROP1": lambda d: d.ret <= -0.01, "DROP15": lambda d: d.ret <= -0.015, "DROP2": lambda d: d.ret <= -0.02,
}
FILTERS = {
    "F0": lambda d: pd.Series(True, index=d.index),
    "MA": lambda d: d.C > d.ma200,
    "VIX": lambda d: d.vix_prev >= VIX_TH,
    "MAVIX": lambda d: (d.C > d.ma200) & (d.vix_prev >= VIX_TH),
}
EXITS = ["k1", "k3", "k5", "MA5"]
STOPS = [None, 1.5, 2.0]
MAXHOLD = 10


def _plan_exit(d: pd.DataFrame, t: int, ex: str) -> int:
    if ex.startswith("k"):
        return t + int(ex[1:])
    C, ma5 = d.C.to_numpy(), d.ma5.to_numpy()
    for j in range(t + 1, min(t + MAXHOLD, len(d) - 1) + 1):
        if C[j] > ma5[j]:
            return j
    return t + MAXHOLD


def trade(mk: Market, t: int, x: int, stop: float | None, spread_mult: float = 1.0, entry: str = "E1",
          optimistic: bool = False) -> dict | None:
    """t: sinyal gün sırası, x: planlanan çıkış gün sırası. Döner: σR ve ayrıntı."""
    d, b = mk.day, mk.bars
    if x >= len(d):
        return None
    op, lo, cl = b.open.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    ci = d.ci.to_numpy()
    if entry == "E2":
        e2 = d.e2i.to_numpy()[t]
        if not np.isfinite(e2):
            return None
        ei = int(e2)
    else:
        ei = int(ci[t]) + 1
    if ei >= len(b):
        return None
    e = cl[ci[t]] if optimistic else op[ei]
    xi = int(ci[x]) + 1
    if xi >= len(b) or xi <= ei:
        return None
    sig = d.sig.to_numpy()[t]
    if not np.isfinite(sig) or sig <= 0:
        return None
    cost = 0.0 if optimistic else (SPREAD_PT * spread_mult + 2 * SLIP_PT)
    px, how, out_i = op[xi], "exit", xi
    if optimistic:
        px = cl[ci[x]]
    if stop is not None:
        sp = e * (1 - stop * sig)
        for j in range(ei, xi):
            if lo[j] <= sp:
                px = sp if j == ei else min(op[j], sp)
                how, out_i = "stop", j
                break
    nights = (b.ts.iat[out_i].tz_convert("America/New_York").normalize()
              - b.ts.iat[ei].tz_convert("America/New_York").normalize()).days
    swap = 0.0 if optimistic else SWAP_ANNUAL / 360 * max(nights, 0)
    R = (px - e - cost) / (sig * e) - swap / sig
    return {"t": t, "x": x, "nyd": d.index[t], "xd": d.index[x], "ei": ei, "xo": out_i, "R": R, "how": how,
            "nights": nights, "sig": sig, "swapR": swap / sig}


def run_rule(mk: Market, mask: np.ndarray, ex: str, stop: float | None, start: pd.Timestamp | None = None,
             end: pd.Timestamp | None = None, **kw) -> pd.DataFrame:
    """Kuralı yürüt: pozisyon açıkken yeni sinyal yok (sonraki sinyalin kapanış barı > önceki çıkış barı)."""
    d = mk.day
    idx = d.index
    ok = mask & np.isfinite(d.sig.to_numpy())
    if start is not None:
        ok &= (idx >= start)
    if end is not None:
        ok &= (idx < end)
    ci = d.ci.to_numpy()
    rows, busy_until = [], -1
    for t in np.flatnonzero(ok):
        if ci[t] < busy_until:
            continue
        x = _plan_exit(d, t, ex)
        r = trade(mk, t, x, stop, **kw)
        if r is None:
            continue
        r["h"] = x - t
        rows.append(r)
        busy_until = r["xo"]
    return pd.DataFrame(rows)


def baseline(mk: Market, start, end, hmax: int = MAXHOLD, **kw) -> dict:
    """always-long: her gün al, h gün sonra çık, aynı stop. base[(stop,h)] = ortalama σR."""
    d = mk.day
    T = np.flatnonzero((d.index >= start) & (d.index < end) & np.isfinite(d.sig.to_numpy()))
    out = {}
    for s in STOPS:
        for h in range(1, hmax + 1):
            v = [trade(mk, t, t + h, s, **kw) for t in T]
            v = [r["R"] for r in v if r is not None]
            out[(s, h)] = float(np.mean(v)) if v else np.nan
    return out


def block_boot(values: np.ndarray, groups: np.ndarray, n: int = 4000, seed: int = 7) -> np.ndarray:
    if len(values) == 0:
        return np.array([np.nan])
    g, inv = np.unique(groups, return_inverse=True)
    s = np.bincount(inv, weights=values)
    cnt = np.bincount(inv)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(g), size=(n, len(g)))
    return s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)


def add_excess(T: pd.DataFrame, base: dict, stop) -> pd.DataFrame:
    if len(T):
        T["ex"] = T.R - np.array([base[(stop, int(min(h, MAXHOLD)))] for h in T.h])
    return T
