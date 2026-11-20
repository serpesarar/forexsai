"""cd_veri.py — CAPREV derin (PROTOCOL.md): olaylar (günlük vekil 5 endeks + canlı kural 1m/M30) + günlük bağlam özellikleri + X çıkış hücreleri.

python cd_veri.py  → cache/olaylar.parquet
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/caprev_tpsl_20261120/src"))
import cr_gunluk as G  # noqa: E402
import cr_motor as M  # noqa: E402

G.KOR["GDAXI"] = ROOT / "research/kasa_trend_20261028/data/GDAXI.csv"
US = ("NDX", "GSPC", "DJI", "RUT")
ALL = US + ("GDAXI",)
FEED_IDX = {"DUKA_NDX": "NDX", "MT5_NAS100": "NDX", "DUKA_DAX": "GDAXI", "MT5_US500": "GSPC", "MT5_US30": "DJI", "MT5_US2000": "RUT"}
X_M, X_C, X_R = (1, 2, 3, 5), (None, 2.0, 3.0), ("kar", "yuk")
X_CELLS = [f"X_{m}_{c}_{r}" for m in X_M for c in X_C for r in X_R]
FEATS = ["sma200", "sma50", "dd252", "r1z", "r5z", "volx", "seri", "stres10", "olay_once", "vix", "vix_pct", "vix1", "vix5",
         "vix_sma10", "vade_egri", "rsi2", "clv", "aralik", "tlt1", "genislik"]
CATS = ["opex", "wd", "ay_sonu"]
COST_BP = G.COST_BP


# ───────── günlük seriler ve özellikler ─────────
def daily(name: str) -> pd.DataFrame:
    x = G.load_daily(name).copy()
    x.index = pd.to_datetime(x.index).normalize()
    return x[~x.index.duplicated()]


def _series(path: Path) -> pd.Series:
    v = pd.read_parquet(path)
    s = v["Close"].squeeze()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize() if getattr(s.index, "tz", None) else pd.to_datetime(s.index).normalize()
    return s.dropna()


VIXS = _series(M.VIX_PATH)
VIX3M = _series(ROOT / "research/qs13_ters_rejim_ndx_20261112/data/VIX3M.parquet")
TLT = _series(ROOT / "research/qs13_ters_rejim_ndx_20261112/data/TLT.parquet")


def _prev(s: pd.Series, d: pd.Timestamp, lag: int = 1) -> float:
    k = int(s.index.searchsorted(d)) - lag
    return float(s.iloc[k]) if 0 <= k < len(s) else np.nan


def rsi2(c: np.ndarray) -> np.ndarray:
    out = np.full(len(c), np.nan)
    up = dn = 0.0
    for i in range(1, len(c)):
        g = c[i] - c[i - 1]
        up = 0.5 * max(g, 0) + 0.5 * up if i > 1 else max(g, 0)
        dn = 0.5 * max(-g, 0) + 0.5 * dn if i > 1 else max(-g, 0)
        out[i] = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
    return out


def feat_frame(name: str) -> pd.DataFrame:
    """Satır d: d gününün başında bilinen özellikler (yalnız d'den önceki satırlar)."""
    x = daily(name)
    C, H, L = x.Close, x.High, x.Low
    r = C.pct_change()
    dv = r.rolling(20).std(ddof=1)
    f = pd.DataFrame(index=x.index)
    f["sma200"] = C / C.rolling(200).mean() - 1
    f["sma50"] = C / C.rolling(50).mean() - 1
    f["dd252"] = C / C.rolling(252, min_periods=120).max() - 1
    f["r1z"] = r / dv
    f["r5z"] = C.pct_change(5) / (dv * np.sqrt(5))
    f["volx"] = dv / r.rolling(60).std(ddof=1)
    neg = (r < 0).astype(int)
    f["seri"] = neg.groupby((neg == 0).cumsum()).cumsum()
    st = ((r <= M.STRESS_R1) | (C.pct_change(5) <= M.STRESS_R5)).astype(int)
    f["stres10"] = st.rolling(10).sum()
    f["rsi2"] = rsi2(C.values)
    f["clv"] = (C - L) / (H - L).replace(0, np.nan)
    f["aralik"] = (H - L) / (C * dv)
    f["r1"] = r
    f = f.shift(1)                                   # d gününe d−1 bilgisi
    vix = [_prev(VIXS, d) for d in f.index]
    f["vix"] = vix
    f["vix1"] = [v / _prev(VIXS, d, 2) - 1 for v, d in zip(vix, f.index)]
    f["vix5"] = [v / _prev(VIXS, d, 6) - 1 for v, d in zip(vix, f.index)]
    vs = VIXS.rolling(10).mean()
    f["vix_sma10"] = [v / _prev(vs, d) for v, d in zip(vix, f.index)]
    vp = VIXS.rolling(252, min_periods=200).apply(lambda a: (a[:-1] < a[-1]).mean(), raw=True)
    f["vix_pct"] = [_prev(vp, d) for d in f.index]
    f["vade_egri"] = [v / _prev(VIX3M, d) if d >= pd.Timestamp("2006-07-18") else np.nan for v, d in zip(vix, f.index)]
    tr = TLT.pct_change()
    f["tlt1"] = [_prev(tr, d) if d >= pd.Timestamp("2002-08-01") else np.nan for d in f.index]
    return f


FF = {n: feat_frame(n) for n in ALL}
R1 = {n: FF[n].r1 for n in US}


def add_context(T: pd.DataFrame, idx: str) -> pd.DataFrame:
    f = FF[idx]
    d = pd.to_datetime(T.d).dt.normalize()
    k2 = np.clip(f.index.searchsorted(d), 0, len(f) - 1)      # d satırı (yoksa sonraki); özellikler zaten d−1'e kaydırılmış
    late = (d > f.index[-1]).values
    for c in [c for c in f.columns if c != "r1"]:
        T[c] = np.where(late, np.nan, f[c].values[k2])
    others = [u for u in US if u != idx]
    T["genislik"] = [sum(1 for u in others if _prev(R1[u].dropna(), dd, 0) <= M.STRESS_R1) for dd in d]
    bd = pd.to_datetime(T.d).values.astype("datetime64[D]")
    prevd = np.concatenate([bd[:1] - np.timedelta64(120, "D"), bd[:-1]]) if len(bd) else bd
    T["olay_once"] = np.minimum(np.busday_count(prevd, bd), 60)
    T["opex"] = [min(int(M._opex(x.date()) or 9), 5) for x in pd.to_datetime(T.d)]
    T["wd"] = pd.to_datetime(T.d).dt.weekday
    me = pd.to_datetime(T.d) + pd.offsets.BMonthEnd(0)
    T["ay_sonu"] = (np.busday_count(bd, me.values.astype("datetime64[D]")) <= 2).astype(int)
    return T


# ───────── günlük vekil olayları + X ─────────
def daily_events(name: str, start: str, end: str, set_name: str) -> pd.DataFrame:
    x = daily(name)
    O, H, L, C = (x[c].values for c in ("Open", "High", "Low", "Close"))
    days = list(x.index)
    rows = []
    a, b = pd.Timestamp(start), pd.Timestamp(end)
    for i in range(22, len(days) - 6):
        d = days[i]
        if not (a <= d <= b) or d.weekday() > 3 or (d - days[i - 1]).days > 4:
            continue
        rets = C[i - 21:i] / C[i - 22:i - 1] - 1
        r1, r5, dvol = rets[-1], C[i - 1] / C[i - 6] - 1, float(np.std(rets[-20:], ddof=1))
        v = _prev(VIXS, d)
        if not np.isfinite(v) or v < M.VIX_MIN or not (r1 <= M.STRESS_R1 or r5 <= M.STRESS_R5) or L[i] >= L[i - 1]:
            continue
        E = min(O[i], L[i - 1]) * (1 + COST_BP / 1e4)
        bid = lambda p: p * (1 - COST_BP / 1e4)  # noqa: E731
        fin = [M.FIN * (days[i + s] - d).days for s in range(6)]
        cl = [bid(C[i + s]) for s in range(6)]

        def walk(c_k, exit_s: int) -> float:
            sl = E * (1 - (c_k * dvol if c_k is not None else M.EMERG))
            if L[i] <= sl:
                return (bid(sl) / E - 1) * 1e4
            for s in range(1, exit_s + 1):
                if O[i + s] <= sl:
                    return (bid(O[i + s]) / E - 1) * 1e4 - fin[s]
                if L[i + s] <= sl:
                    return (bid(sl) / E - 1) * 1e4 - fin[s]
            return (cl[exit_s] / E - 1) * 1e4 - fin[exit_s]

        base = walk(1.0, 0)
        cls = "SL" if L[i] <= E * (1 - dvol) else ("TP" if base > 0 else "ZK")
        r = {"set": set_name, "idx": name, "feed": f"G_{name}", "d": d, "E": E, "dvol": dvol, "base": base, "cls": cls}
        for cell, (m, c_k, rule) in zip(X_CELLS, [(m, c, rr) for m in X_M for c in X_C for rr in X_R]):
            r[cell] = walk(c_k, exit_index(cl, E, m, rule))
        rows.append(r)
    return pd.DataFrame(rows)


def exit_index(cl: list[float], E: float, m: int, rule: str) -> int:
    """Kapanış dizisinden çıkış günü (0..m). cl[0] = D0 kapanışı (bid)."""
    if cl[0] >= E:
        return 0
    for s in range(1, m + 1):
        if s >= len(cl):
            return len(cl) - 1
        if (rule == "kar" and cl[s] >= E) or (rule == "yuk" and cl[s] > cl[s - 1]):
            return s
    return min(m, len(cl) - 1)


# ───────── canlı kural (1m / M30) olayları + X ─────────
def feed_events(feed: str, set_name: str) -> pd.DataFrame:
    F = M.Feed(feed)
    rows = []
    for ev in F.events():
        base = F.trade_row(ev)
        if base is None:
            continue
        cps = [c for c in F.checkpoints(ev) if c[0].endswith("c")]
        pts = []
        for lab, uu, dd in cps:
            got = F.px_at(uu)
            if got is None:
                break
            pts.append((got[0], got[1], dd))
        if len(pts) < 2:
            continue
        i0, E, dvol, d0 = ev["i0"], ev["E"], ev["dvol"], ev["d"]
        cl = [p[1] for p in pts]
        r = {"set": set_name, "idx": FEED_IDX[feed], "feed": feed, "d": pd.Timestamp(d0), "E": E, "dvol": dvol, "base": base["base"],
             "cls": base["cls"]}
        for cell, (m, c_k, rule) in zip(X_CELLS, [(m, c, rr) for m in X_M for c in X_C for rr in X_R]):
            s = exit_index(cl, E, m, rule)
            ie = pts[s][0]
            sl = E * (1 - (c_k * dvol if c_k is not None else M.EMERG))
            lo = F.l[i0:ie]
            js = int(np.argmax(lo <= sl)) if (lo <= sl).any() else None
            if js is not None:
                r[cell] = (min(sl, F.o[i0 + js]) / E - 1) * 1e4 - M.FIN * (F.d[i0 + js] - d0).days
            else:
                r[cell] = (cl[s] / E - 1) * 1e4 - M.FIN * (pts[s][2] - d0).days
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    parts = []
    for n in ALL:
        parts.append(add_context(daily_events(n, "1990-01-01", "2015-12-31", "KESIF"), n))
        parts.append(add_context(daily_events(n, "2016-01-01", "2026-12-31", "G2016"), n))
    for f in FEED_IDX:
        parts.append(add_context(feed_events(f, f), FEED_IDX[f]))
    T = pd.concat(parts, ignore_index=True)
    T["hit"] = T.base > 0
    (HERE / "cache").mkdir(exist_ok=True)
    T.to_parquet(HERE / "cache/olaylar.parquet")
    print(T.groupby(["set", "idx"]).agg(n=("base", "size"), bp=("base", "mean"), hit=("hit", "mean"),
                                         d0=("d", "min"), d1=("d", "max")).round(3).to_string())


if __name__ == "__main__":
    main()
