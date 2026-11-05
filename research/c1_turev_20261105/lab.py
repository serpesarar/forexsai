"""TR lab: gün tablosu + kural simülasyonu + defter. Önce stop; giriş sonraki bar açılışı + spread; zaman çıkışı son bar kapanışı."""
from __future__ import annotations
import csv, sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, yfinance as yf
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
LEDGER = HERE / "results/denemeler.csv"
NY = ZoneInfo("America/New_York")
SPREAD = 1.3
MIN_RISK = 0.0005

def _macro() -> pd.DataFrame:
    p = HERE / "results/macro.parquet"
    if p.exists():
        return pd.read_parquet(p)
    def get(t):
        s = yf.Ticker(t).history(start="2010-01-01", end="2026-11-06")["Close"]; s.index = s.index.tz_localize(None).normalize(); return s
    m = pd.DataFrame({"vix": get("^VIX"), "vix3m": get("^VIX3M"), "vvix": get("^VVIX")})
    m.to_parquet(p); return m
MAC = _macro()
CAL = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
CAL_DAYS = {pd.Timestamp(x).date() for x in CAL.date}

@dataclass
class Day:
    d: object; m: np.ndarray; o: np.ndarray; h: np.ndarray; l: np.ndarray; c: np.ndarray; f: dict

def load_bars(name: str) -> tuple[pd.DataFrame, int, tuple[int, int]]:
    """(UTC ts + OHLC), bar dakikası, seans (dk). Tüm çapalar için 24 saat barı döner."""
    if name == "5m":
        d = pd.read_parquet(ROOT / "research/haber_derin_20261105/data/NDX_1m.parquet"); d = d.assign(ts=pd.to_datetime(d.t, unit="s", utc=True)).set_index("ts")
        x = d.resample("5min", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna().reset_index(); return x, 5
    if name == "30m":
        x = pd.read_parquet(ROOT / "research/ndx_gate_forge/data/long_30m_utc.parquet"); x["ts"] = pd.to_datetime(x.ts, utc=True); x = x[x.ts < "2024-01-01"]; return x.sort_values("ts").reset_index(drop=True)[["ts", "open", "high", "low", "close"]], 30
    if name == "1h":
        z = np.load(ROOT / "backend/data/candle_history/NDX_1h.npz"); x = pd.DataFrame({k: z[k] for k in z.files}); x["ts"] = pd.to_datetime(x.ts.astype("int64"), unit="s", utc=True); x = x[(x.ts >= "2016-06-01") & (x.ts < "2021-06-29")]; return x.sort_values("ts").reset_index(drop=True)[["ts", "open", "high", "low", "close"]], 60
    raise ValueError(name)

def build_days(name: str, o0: int = 570, f0: int = 955) -> list[Day]:
    x, bar = load_bars(name)
    loc = x.ts.dt.tz_convert(NY); mins = (loc.dt.hour * 60 + loc.dt.minute).to_numpy(); dates = loc.dt.date.to_numpy()
    o, h, l, c = (x[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    by: dict = {}
    for i, dd in enumerate(dates):
        by.setdefault(dd, []).append(i)
    ds = sorted(by); rth_o0 = o0 if bar < 60 else 600
    out, closes, rets = [], [], []
    for dd in ds:
        ix = np.array(by[dd]); m = mins[ix]; r = ix[(m >= rth_o0) & (m < f0)]
        if len(r) == 0:
            continue
        pc = closes[-1] if closes else np.nan; ppc = closes[-2] if len(closes) > 1 else np.nan; c5 = closes[-5] if len(closes) >= 5 else np.nan
        key = pd.Timestamp(dd); prev = MAC[MAC.index < key]
        v1 = prev.iloc[-1] if len(prev) else None; v2 = prev.iloc[-2] if len(prev) > 1 else None
        f = {"vix": v1.vix if v1 is not None else np.nan, "vixchg": (v1.vix - v2.vix) if v2 is not None else np.nan, "vix3m": v1.vix3m if v1 is not None else np.nan,
             "vvix": v1.vvix if v1 is not None else np.nan, "gap": (o[r[0]] / pc - 1) * 1e4 if pc == pc else np.nan, "r1": (pc / ppc - 1) * 1e4 if ppc == ppc else np.nan, "r5": (pc / c5 - 1) * 1e4 if c5 == c5 else np.nan,
             "rv20": float(np.std(rets[-20:]) * 1e4) if len(rets) >= 20 else np.nan, "dow": pd.Timestamp(dd).dayofweek, "data": dd in CAL_DAYS, "y": dd.year,
             "rv_q": float(pd.Series(rets[-250:]).rolling(20).std().rank(pct=True).iloc[-1]) if len(rets) >= 40 else np.nan}
        out.append(Day(dd, m, o[ix], h[ix], l[ix], c[ix], f))
        closes.append(c[r[-1]])
        if pc == pc: rets.append(c[r[-1]] / pc - 1)
    return out

def sim(day: Day, i_e: int, side: int, stop: float, tgt: float | None, end_m: int, sp: float) -> tuple[float, float, float] | None:
    """i_e girişin barı (açılışında). (R, bp, risk_bp). tgt None → yalnız zaman çıkışı."""
    if i_e >= len(day.o) or day.m[i_e] >= end_m: return None
    e = day.o[i_e] + side * sp
    risk = (e - stop) * side
    if risk <= MIN_RISK * e: return None
    tp = e + side * tgt * risk if tgt else None
    last = None
    for j in range(i_e, len(day.o)):
        if day.m[j] >= end_m: break
        last = j
        if side > 0:
            if day.l[j] <= stop: return -1.0, -risk / e * 1e4, risk / e * 1e4
            if tp and day.h[j] >= tp: return tgt, tgt * risk / e * 1e4, risk / e * 1e4
        else:
            if day.h[j] >= stop: return -1.0, -risk / e * 1e4, risk / e * 1e4
            if tp and day.l[j] <= tp: return tgt, tgt * risk / e * 1e4, risk / e * 1e4
    if last is None: return None
    r = side * (day.c[last] - e) / risk
    return r, r * risk / e * 1e4, risk / e * 1e4

def or_of(day: Day, a0: int, length: int, bar: int):
    k = (day.m >= a0) & (day.m < a0 + length)
    if k.sum() * bar < length: return None
    return day.h[k].max(), day.l[k].min(), int(np.flatnonzero(k)[-1])

FILTERS = {
    "tümü": lambda f: True, "vix≥18,4": lambda f: f["vix"] >= 18.4, "vix<18,4": lambda f: f["vix"] < 18.4,
    "vix≥25": lambda f: f["vix"] >= 25, "vix18-25": lambda f: 18.4 <= f["vix"] < 25, "vix<15": lambda f: f["vix"] < 15,
    "vix yükseldi": lambda f: f["vixchg"] > 0, "vix düştü": lambda f: f["vixchg"] < 0,
    "vix≥18,4∧yükseldi": lambda f: f["vix"] >= 18.4 and f["vixchg"] > 0, "vix≥18,4∧düştü": lambda f: f["vix"] >= 18.4 and f["vixchg"] < 0,
    "vix<18,4∧yükseldi": lambda f: f["vix"] < 18.4 and f["vixchg"] > 0, "vix<18,4∧düştü": lambda f: f["vix"] < 18.4 and f["vixchg"] < 0,
    "geri eğim(vix>vix3m)": lambda f: f["vix"] > f["vix3m"], "vix/vix3m≥0,9": lambda f: f["vix"] / f["vix3m"] >= 0.9, "vix/vix3m<0,85": lambda f: f["vix"] / f["vix3m"] < 0.85,
    "rv_üst%33": lambda f: f["rv_q"] >= 0.67, "rv_alt%33": lambda f: f["rv_q"] < 0.33,
    "boşluk+": lambda f: f["gap"] > 10, "boşluk−": lambda f: f["gap"] < -10, "boşluk düz": lambda f: abs(f["gap"]) <= 10,
    "dün+": lambda f: f["r1"] > 0, "dün−": lambda f: f["r1"] < 0, "dün≤−%1": lambda f: f["r1"] <= -100, "5g−": lambda f: f["r5"] < 0, "5g+": lambda f: f["r5"] > 0,
    "cuma": lambda f: f["dow"] == 4, "pzt": lambda f: f["dow"] == 0, "sal-per": lambda f: f["dow"] in (1, 2, 3), "veri günü": lambda f: f["data"], "veri dışı": lambda f: not f["data"],
    "vix≥18,4∧dün−": lambda f: f["vix"] >= 18.4 and f["r1"] < 0, "vix≥18,4∧dün+": lambda f: f["vix"] >= 18.4 and f["r1"] > 0,
    "vix≥18,4∧boşluk+": lambda f: f["vix"] >= 18.4 and f["gap"] > 10, "vix≥18,4∧boşluk−": lambda f: f["vix"] >= 18.4 and f["gap"] < -10,
    "vix<18,4∧dün+": lambda f: f["vix"] < 18.4 and f["r1"] > 0, "vix<18,4∧boşluk+": lambda f: f["vix"] < 18.4 and f["gap"] > 10,
}

def metrics(rows: list[tuple]) -> dict:
    """rows: (tarih, R, bp, risk). Ay-blok P."""
    if len(rows) < 5: return {"n": len(rows)}
    d = pd.to_datetime([r[0] for r in rows]); R = np.array([r[1] for r in rows]); bp = np.array([r[2] for r in rows])
    u, inv = np.unique(d.to_period("M").astype(str), return_inverse=True); s, n = np.bincount(inv, R), np.bincount(inv); ix = np.random.default_rng(5).integers(0, len(u), (2000, len(u)))
    h = len(R) // 2
    return {"n": len(R), "R": round(R.mean(), 3), "bp": round(bp.mean(), 2), "isabet": round((R > 0).mean(), 3), "P": round(float(((s[ix].sum(1) / n[ix].sum(1)) > 0).mean()), 3), "y1": round(R[:h].mean(), 3), "y2": round(R[h:].mean(), 3)}

def ledger(sym: str, fam: str, cell: str, ds: str, m: dict) -> None:
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        if new: w.writerow(["sym", "aile", "hücre", "veri", "n", "R", "bp", "isabet", "P", "y1", "y2"])
        w.writerow([sym, fam, cell, ds, m.get("n"), m.get("R"), m.get("bp"), m.get("isabet"), m.get("P"), m.get("y1"), m.get("y2")])


# ── MT5 broker barları (kutudan salt okunur). Sunucu = New York + 7 sa (broker_time.py) ──
def mt5_bars(sym: str, tf: str) -> pd.DataFrame:
    """ts_et: New York duvar saati (tz'siz) · sp: fiyat biriminde bar spread'i."""
    meta = __import__("json").loads((HERE / "data/mt5/meta.json").read_text())
    x = pd.read_csv(HERE / f"data/mt5/{sym}_{tf}.csv.gz")
    x["ts_et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7)
    x["sp"] = x.sp * meta[sym]["point"]
    return x
