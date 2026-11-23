"""DAYCOMBO + REENTRY canlı akış taklidi — TD-01 motorunun genişletilmiş hâli (PROTOCOL.md).

Ek: yüzde geometri (ESKİ), gün düzeyi durum kuralları, buy-stop girişi, probasyon değişkenleri,
verimlilik oranı / şok / gürültü ölçüleri, atlanan kararların karşı-olgu R'si.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/tepe_destek_20261104"))
import engine as td  # noqa: E402
from engine import Mkt, dc  # noqa: E402

TP, SL, SP = 80.0, 110.0, 1.5
REF = 24000.0
BOX = Path("/private/tmp/claude-501/-Users-melihcanodacioglu-Desktop-panel/"
           "8bb005b7-0e56-4dd7-bfb3-e7a9ba42f974/scratchpad/m1/box_1119_1123.parquet")
BOX_COPY = ROOT / "research/ndx_sl_onleme_20261123/data/box_1119_1123.parquet"

PERIODS = {
    "ESKI-A": ("2018-01-01", "2021-01-01"), "ESKI-B": ("2021-01-01", "2024-01-01"),
    "Y24": ("2024-01-01", "2025-01-01"), "Y25": ("2025-01-01", "2026-07-29"),
    "Y26b": ("2026-07-29", "2026-11-21"), "VAKA": ("2026-11-23", "2026-11-24"),
}
CORE = ["ESKI-A", "ESKI-B", "Y24", "Y25"]


def period_of(ts: pd.Timestamp) -> str:
    for k, (a, b) in PERIODS.items():
        if pd.Timestamp(a, tz="UTC") <= ts < pd.Timestamp(b, tz="UTC"):
            return k
    return "-"


def _seg(d: pd.DataFrame) -> pd.DataFrame:
    d = d[["ts", "open", "high", "low", "close"]].sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    d["seg"] = (d.ts.diff() > pd.Timedelta(days=4)).cumsum().astype(int)
    return d


def load_markets() -> dict[str, pd.DataFrame]:
    """ESKİ (v3 Duka 2018-23), y24, y25, y26 (broker + otopsi önbelleği + kutu MT5)."""
    v = pd.read_parquet(ROOT / "research/nom_20261113/data/ndx_1m_v3_duka.parquet")
    v["ts"] = pd.to_datetime(v.t, unit="s", utc=True)
    v = v[(v.ts >= "2017-12-01") & (v.ts < "2024-01-01")]
    D = td.load_all()
    box = pd.read_parquet(BOX_COPY if BOX_COPY.exists() else BOX)
    y26 = pd.concat([D["y26"][["ts", "open", "high", "low", "close"]], box[["ts", "open", "high", "low", "close"]]])
    return {"eski": _seg(v), "y24": D["y24"], "y25": D["y25"], "y26": _seg(y26)}


class Mkt2(Mkt):
    """TD-01 Mkt + ER, şok oranı, ölçek."""

    def __init__(self, b: pd.DataFrame, pct: bool):
        super().__init__(b)
        self.pct = pct
        c = self.c
        dc_ = np.abs(np.diff(c, prepend=c[0]))
        cs = np.cumsum(dc_)
        self.er = {}
        for n in (60, 120):
            num = np.abs(c - np.roll(c, n))
            den = cs - np.roll(cs, n)
            er = np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)
            er[:n] = np.nan
            self.er[n] = er
        f = self.f15
        body = (f.close - f.open).abs()
        med = body.shift(1).rolling(20 * 92, min_periods=400).median()
        ratio = (body / med).to_numpy()
        self.shock_mx = pd.Series(ratio).rolling(12, min_periods=1).max().to_numpy()
        self.f15_tend = f.tend.to_numpy()

    def sc(self, k: int) -> float:
        return float(self.c[k - 1] / REF) if self.pct else 1.0

    def shock_at(self, k: int) -> float:
        j = int(np.searchsorted(self.f15_tend, self.t[k], side="right")) - 1
        return float(self.shock_mx[j]) if j >= 0 else np.nan

    def noise_at(self, k: int) -> float:
        a = self.atr1[k - 1]
        return float(SL * self.sc(k) / (a * np.sqrt(30))) if a > 0 else np.nan


def _out(m: Mkt2, k: int, sc: float, d: dict, e, spread: float, slip: float):
    tp = d.get("tp", TP) * sc
    sl = d.get("sl", SL) * sc
    x = m.out(k, tp, sl, e=e, spread=spread, slip=slip, tend=d.get("tend"))
    if x is None:
        return None
    j, pts, why = x
    return j, pts / sl, why


def run2(m: Mkt2, sig: pd.DataFrame, rule=None, day_rule=None, spread=SP, slip=0.0, lag=0,
         prob_n=5, prob_nonneg=False, keep_re=True, prob_cap=None):
    """Dönüş: (işlemler DataFrame, atlanan kararlar DataFrame).

    rule(m, k, feat, ctx) -> None (atla) | dict(kind='mkt'|'lim'|'conf'|'stp', level, wait, tp, sl, tend)
    day_rule(list[R]) -> True ise o gün yeni giriş yok (gerçekleşmiş, çıkış sırasıyla).
    """
    rows, skips, done = [], [], []
    busy, idle_re = -1, -1
    first, last_exit = {}, None

    def day_list(tm, day):
        xs = sorted((xt, R) for xt, d, R in done if d == day and xt <= tm)
        return [R for _, R in xs]

    def place(tm, fam, ctx):
        k = m.k_of(tm + lag)
        if k is None or k < 2:
            return None
        sc = m.sc(k)
        spr, slp = spread * sc, slip * sc
        f = m.feat(k)
        ctx["sc"] = sc
        if day_rule is not None and day_rule(day_list(m.t[k], m.day[k])):
            skips.append((fam, k, "day"))
            return None
        d = {"kind": "mkt"} if rule is None else rule(m, k, f, ctx)
        if d is None:
            skips.append((fam, k, "rule"))
            return None
        kind, kk, e = d["kind"], k, None
        if kind == "lim":
            L = d["level"]
            if not np.isfinite(L) or L >= m.o[k] + spr:
                kind = "mkt"
            else:
                kk = None
                for j in range(k, min(k + d["wait"], len(m.t))):
                    if m.g[j] != m.g[k]:
                        break
                    if m.l[j] + spr <= L:
                        kk, e = j, L
                        break
                if kk is None:
                    skips.append((fam, k, "nofill"))
                    return ("cancel", k + d["wait"])
        elif kind == "conf":
            L = d["level"]
            kk, tch = None, False
            for j in range(k, min(k + d["wait"], len(m.t) - 1)):
                if m.g[j] != m.g[k]:
                    break
                if not tch and m.l[j] <= L:
                    tch = True
                    continue
                if tch and m.c[j] > L:
                    kk = j + 1
                    break
            if kk is None:
                skips.append((fam, k, "nofill"))
                return ("cancel", k + d["wait"])
        elif kind == "stp":
            L = d["level"]
            kk = None
            for j in range(k, min(k + d["wait"], len(m.t))):
                if m.g[j] != m.g[k]:
                    break
                if m.h[j] + spr >= L:
                    kk, e = j, max(L, m.o[j] + spr)
                    break
            if kk is None:
                skips.append((fam, k, "nofill"))
                return ("cancel", k + d["wait"])
        x = _out(m, kk, sc, d, e, spr, slp)
        if x is None:
            return None
        j, R, why = x
        return (kk, j, R, why, fam, float(m.o[kk] + spr if e is None else e), k)

    def record(res, sp):
        kk, j, R, why, fam, e, k = res
        rows.append((fam, k, kk, j, R, why, e, sp))
        done.append((int(m.t[j]), m.day[kk], R))

    for r in sig.itertuples():
        tm = int(np.datetime64(r.end.tz_convert(None), "m").astype("int64"))
        if tm < busy:
            continue
        k0 = m.k_of(tm)
        if k0 is None or k0 + prob_n >= len(m.t):
            continue
        sp = m.c[k0 - 1]
        band = 1.28 * m.atr1[k0 - 1] * np.sqrt(prob_n)
        if prob_cap is not None:
            band = min(band, prob_cap * SL * m.sc(k0))
        adv = max(sp - m.l[k0:k0 + prob_n].min(), 0)
        if adv > band or (prob_nonneg and m.c[k0 + prob_n - 1] < sp):
            busy = m.t[k0 + prob_n]
            continue
        dtm = m.t[k0 + prob_n]
        day = m.day[k0]
        ctx = dict(fam="DC", sig_px=sp, first=first.get(day), last_exit=last_exit, prev=None)
        res = place(dtm, "DC", ctx)
        if res is None:
            busy = dtm
            continue
        if res[0] == "cancel":
            busy = m.t[min(res[1], len(m.t) - 1)]
            continue
        record(res, sp)
        kk, j, R, why, fam, e, _ = res
        busy = m.t[j]
        first.setdefault(day, e)
        sc = m.sc(kk)
        last_exit = m.c[j] if why == "TIME" else (e + TP * sc if why == "TP" else e - SL * sc)
        if keep_re and why in ("TP", "SL"):
            tre = int(m.t[j]) + 1 + (5 if why == "TP" else 1)
            ts = pd.Timestamp(tre * 60, unit="s", tz="UTC")
            if tre < idle_re or ts.weekday() == 4 or ts.hour >= 22 or ts.hour < 7:
                continue
            ctx = dict(fam="RE", sig_px=None, first=first.get(ts.strftime("%F")), last_exit=last_exit,
                       prev=dict(why=why, e=e, sl=SL * sc))
            x = place(tre, "RE", ctx)
            if x is None or x[0] == "cancel":
                continue
            record(x, np.nan)
            idle_re = m.t[x[1]]
    t = pd.DataFrame(rows, columns=["fam", "k", "kk", "j", "R", "why", "e", "sig"])
    s = pd.DataFrame(skips, columns=["fam", "k", "why"])
    for df, col in ((t, "kk"), (s, "k")):
        if len(df):
            df["et"] = m.b.ts.to_numpy()[df[col].to_numpy()]
            df["et"] = pd.to_datetime(df.et, utc=True)
            df["day"] = df.et.dt.strftime("%F")
            df["period"] = df.et.map(period_of)
        else:
            for c in ("et", "day", "period"):
                df[c] = []
    return t, s


def skip_cf(m: Mkt2, s: pd.DataFrame) -> pd.DataFrame:
    """Atlanan kararların piyasa girişiyle karşı-olgu R'si (E89/E66)."""
    if not len(s):
        return s.assign(R=[])
    R = []
    for k in s.k.to_numpy():
        x = _out(m, int(k), m.sc(int(k)), {}, None, SP * m.sc(int(k)), 0.0)
        R.append(np.nan if x is None else x[1])
    return s.assign(R=R)
