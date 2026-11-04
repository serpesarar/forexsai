"""Ortak altyapı — aile: çapraz varlık rejimi + çıkış mekaniği (BTC).

Yoğun 1m dakika ızgarası, broker kapalı dakikaları, rollover/swap, eşli çok-varyantlı
1m yol simülatörü (TP/SL/BE/koştur/zaman), gün-blok bootstrap, kart.
Tanımlar: prereg.md (bu klasör). Sonuç hesaplamadan önce yazıldı.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
CACHE = os.path.join(HERE, "cache")
RES = os.path.join(HERE, "results")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(RES, exist_ok=True)

BASE = pd.Timestamp("2021-06-01 00:00", tz="UTC")
NY = ZoneInfo("America/New_York")
SPREAD_BASE = 0.000185
SPREAD_STRESS = 0.00028
SPREAD_ABS = 15.0
SWAP_LONG = -0.14 / 365.0
SWAP_SHORT = 0.02 / 365.0
EXCL = (pd.Timestamp("2023-03-24 11:28", tz="UTC"), pd.Timestamp("2023-03-24 14:00", tz="UTC"))
PERIODS = {
    "DISC": (pd.Timestamp("2021-06-01", tz="UTC"), pd.Timestamp("2024-01-01", tz="UTC")),
    "OOS": (pd.Timestamp("2024-01-11", tz="UTC"), pd.Timestamp("2025-07-01", tz="UTC")),
    "BLIND": (pd.Timestamp("2025-07-01", tz="UTC"), pd.Timestamp("2026-10-21", tz="UTC")),
}


def m_of(ts) -> np.ndarray:
    """UTC zaman(lar)ı → dakika indeksi."""
    t = pd.to_datetime(ts, utc=True)
    return ((t - BASE) // pd.Timedelta(minutes=1)).astype(np.int64) if not np.isscalar(t) and not isinstance(t, pd.Timestamp) else int((t - BASE) // pd.Timedelta(minutes=1))


def ts_of(m) -> pd.DatetimeIndex:
    return BASE + pd.to_timedelta(np.asarray(m), unit="m")


@dataclass
class Grid:
    O: np.ndarray
    H: np.ndarray
    L: np.ndarray
    C: np.ndarray
    trad: np.ndarray          # işlem yapılabilir dakika
    nv: np.ndarray            # nv[i] = i'den itibaren ilk işlem dakikası
    roll: np.ndarray          # rollover dakika indeksleri (sıralı)
    closed: np.ndarray        # broker kapalı dakikası
    N: int = 0
    extra: dict = field(default_factory=dict)


def rollovers(start="2021-05-30", end="2026-10-25") -> np.ndarray:
    days = pd.date_range(start, end, freq="D")
    r = [pd.Timestamp(d.year, d.month, d.day, 17, 0, tzinfo=NY).tz_convert("UTC") for d in days]
    fri = [d.weekday() == 4 for d in days]
    return np.array([m_of(x) for x in r], dtype=np.int64), np.array(fri)


def load_grid() -> Grid:
    f = os.path.join(CACHE, "grid.npz")
    if os.path.exists(f):
        z = np.load(f)
        g = Grid(z["O"], z["H"], z["L"], z["C"], z["trad"], z["nv"], z["roll"], z["closed"], int(z["N"]))
        return g
    df = pd.read_parquet(os.path.join(DATA, "btc_1m.parquet"), columns=["ts", "open", "high", "low", "close"])
    mi = m_of(df["ts"]).to_numpy()
    N = int(mi.max()) + 1 + 60 * 24 * 3
    O = np.full(N, np.nan); H = O.copy(); L = O.copy(); C = O.copy()
    O[mi] = df["open"].to_numpy(); H[mi] = df["high"].to_numpy()
    L[mi] = df["low"].to_numpy(); C[mi] = df["close"].to_numpy()
    present = ~np.isnan(O)
    roll, fri = rollovers()
    closed = np.zeros(N, bool)
    for r, f_ in zip(roll, fri):
        lo = r - (5 if f_ else 1)
        if 0 <= r < N:
            closed[max(lo, 0):r + 1] = True
    e0, e1 = m_of(EXCL[0]), m_of(EXCL[1])
    excl = np.zeros(N, bool); excl[e0:e1] = True
    trad = present & ~closed & ~excl
    # kapalı/dışlanan dakikalarda yol kontrolü yok
    H2 = np.where(trad, H, np.nan); L2 = np.where(trad, L, np.nan); O2 = np.where(trad, O, np.nan)
    # nv: sonraki işlem dakikası
    idx = np.where(trad, np.arange(N), N)
    nv = np.minimum.accumulate(idx[::-1])[::-1]
    np.savez(f, O=O2, H=H2, L=L2, C=C, trad=trad, nv=nv, roll=roll, closed=closed, N=N)
    return Grid(O2, H2, L2, C, trad, nv, roll, closed, N)


def swaps_crossed(g: Grid, e: np.ndarray, x: np.ndarray) -> np.ndarray:
    """e < r <= x olan rollover sayısı."""
    return np.searchsorted(g.roll, x, side="right") - np.searchsorted(g.roll, e, side="right")


def next_roll(g: Grid, m: np.ndarray) -> np.ndarray:
    """m'den SONRAKİ ilk rollover dakikası (m < r)."""
    return g.roll[np.searchsorted(g.roll, m, side="right")]


# ───────────────────────── simülatör ─────────────────────────
@dataclass
class Var:
    name: str
    tp: float = np.nan        # R cinsinden TP (nan = yok)
    be: float = np.nan        # MFE ≥ be·D sonrası SL=giriş
    be30: bool = False        # 30. dk kapanışı lehte ise SL=giriş
    runner: bool = False      # TP'ye değince TP kalk, SL=TP−0.6R, iz tepe−0.6R
    hmax: int | None = None   # varyanta özel zaman tavanı (dk); None → olayın x'i


def simulate(g: Grid, dec: np.ndarray, dirn: np.ndarray, x_dec: np.ndarray, risk: np.ndarray,
             variants: list[Var], spread: str = "base", optimistic: bool = False,
             risk_is_frac: bool = False, chunk: int = 1500) -> dict:
    """Olay başına eşli çok-varyant 1m yol simülasyonu.

    dec: karar dakikası (giriş = nv[dec] open). x_dec: zaman çıkışı dakikası (çıkış = nv[x] open).
    risk: SL mesafesi (fiyat) veya risk_is_frac ise giriş fiyatının kesri.
    Dönüş: {varyant: dict(R, gain_bp, reason, hold, nswap, gapfill)} + 'entry','e','D','s'.
    """
    dec = np.asarray(dec, np.int64); dirn = np.asarray(dirn, np.int64)
    x_dec = np.asarray(x_dec, np.int64); risk = np.asarray(risk, float)
    n = len(dec)
    e = g.nv[dec]
    O, H, L, C = g.O, g.H, g.L, g.C
    if optimistic:
        mid_e = C[dec - 1]
        s = np.zeros(n)
        bad = np.isnan(mid_e)
        mid_e = np.where(bad, O[e], mid_e)
    else:
        mid_e = O[e]
        if spread == "base":
            s = SPREAD_BASE * mid_e
        elif spread == "stress":
            s = SPREAD_STRESS * mid_e
        elif spread == "abs":
            s = np.full(n, SPREAD_ABS)
        else:
            raise ValueError(spread)
    entry = mid_e + dirn * s / 2.0
    D = risk * entry if risk_is_frac else risk.copy()
    out = {v.name: {k: np.full(n, np.nan) for k in ("R", "gain_bp", "hold", "nswap")} for v in variants}
    for v in variants:
        out[v.name]["reason"] = np.empty(n, dtype=object)
        out[v.name]["gapfill"] = np.zeros(n, bool)
    xs = {}
    for v in variants:
        xx = g.nv[np.minimum(x_dec, e + v.hmax)] if v.hmax else g.nv[np.maximum(x_dec, e + 1)]
        xs[v.name] = np.maximum(xx, e + 1)
    xmax_all = np.max(np.stack([xs[v.name] for v in variants]), axis=0)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        ee = e[a:b]; W = int((xmax_all[a:b] - ee).max())
        idx = ee[:, None] + np.arange(W)[None, :]
        idx = np.minimum(idx, g.N - 1)
        Hc, Lc, Oc, Cc = H[idx], L[idx], O[idx], C[idx]
        dd = dirn[a:b, None]; ss = s[a:b, None]; en = entry[a:b, None]; Dd = D[a:b, None]
        if True:
            hi_g = np.where(dd > 0, (Hc - ss / 2) - en, en - (Lc + ss / 2))     # lehte uç
            lo_g = np.where(dd > 0, (Lc - ss / 2) - en, en - (Hc + ss / 2))     # aleyhte uç
            op_g = np.where(dd > 0, (Oc - ss / 2) - en, en - (Oc + ss / 2))
            cl_g = np.where(dd > 0, (Cc - ss / 2) - en, en - (Cc + ss / 2))
        tcol = np.arange(W)[None, :]
        hi_n = np.where(np.isnan(hi_g), -np.inf, hi_g)
        mfe_prev = np.concatenate([np.full((b - a, 1), -np.inf), np.maximum.accumulate(hi_n, axis=1)[:, :-1]], axis=1)
        for v in variants:
            xv = xs[v.name][a:b]
            inwin = tcol < (xv - ee)[:, None]
            level = np.full_like(hi_g, -1.0) * Dd
            if not np.isnan(v.be):
                level = np.where(mfe_prev >= v.be * Dd, 0.0, level)
            if v.be30:
                c29 = cl_g[:, 29] if W > 29 else np.full(b - a, np.nan)
                arm = (c29 > 0)[:, None] & (tcol >= 30)
                level = np.where(arm, np.maximum(level, 0.0), level)
            slh = inwin & (lo_g <= level)
            first_sl = np.where(slh.any(1), slh.argmax(1), W + 10)
            if not np.isnan(v.tp):
                tph = inwin & (hi_g >= v.tp * Dd)
                first_tp = np.where(tph.any(1), tph.argmax(1), W + 10)
            else:
                first_tp = np.full(b - a, W + 10)
            rows = np.arange(b - a)
            gain = np.full(b - a, np.nan); reason = np.empty(b - a, dtype=object); exm = np.zeros(b - a, np.int64)
            gap = np.zeros(b - a, bool)
            # SL önce (eşitlikte SL)
            sl_first = (first_sl <= first_tp) & (first_sl < W + 10)
            if sl_first.any():
                r_ = rows[sl_first]; t_ = first_sl[sl_first]
                lv = level[r_, t_]; og = op_g[r_, t_]
                fill = np.where(np.isnan(og), lv, np.minimum(lv, og))
                gap[r_] = fill < lv - 1e-9
                gain[r_] = fill; reason[r_] = np.where(lv < 0, "SL", "BE/iz"); exm[r_] = ee[r_] + t_
            tp_first = (first_tp < first_sl) & (first_tp < W + 10)
            if tp_first.any() and not v.runner:
                r_ = rows[tp_first]; t_ = first_tp[tp_first]
                gain[r_] = v.tp * Dd[r_, 0]; reason[r_] = "TP"; exm[r_] = ee[r_] + t_
            if tp_first.any() and v.runner:
                r_ = rows[tp_first]; t1 = first_tp[tp_first]
                sub_hi = hi_n[r_]; tc = tcol
                after = tc >= t1[:, None]
                pk = np.maximum.accumulate(np.where(after, sub_hi, -np.inf), axis=1)
                pk_prev = np.concatenate([np.full((len(r_), 1), -np.inf), pk[:, :-1]], axis=1)
                lv2 = np.maximum((v.tp - 0.6) * Dd[r_], pk_prev - 0.6 * Dd[r_])
                h2 = inwin[r_] & (tc > t1[:, None]) & (lo_g[r_] <= lv2)
                f2 = np.where(h2.any(1), h2.argmax(1), -1)
                hit = f2 >= 0
                if hit.any():
                    rr = r_[hit]; tt = f2[hit]
                    lv = lv2[hit, tt]; og = op_g[rr, tt]
                    fill = np.where(np.isnan(og), lv, np.minimum(lv, og))
                    gain[rr] = fill; reason[rr] = "iz"; exm[rr] = ee[rr] + tt
                nh = r_[~hit]
                if len(nh):
                    xi = xv[nh]
                    gain[nh] = np.where(dirn[a + nh] > 0, (O[xi] - s[a + nh] / 2) - entry[a + nh], entry[a + nh] - (O[xi] + s[a + nh] / 2))
                    reason[nh] = "zaman(koş)"; exm[nh] = xi
            rest = np.isnan(gain)
            if rest.any():
                r_ = rows[rest]; xi = xv[r_]
                gain[r_] = np.where(dirn[a + r_] > 0, (O[xi] - s[a + r_] / 2) - entry[a + r_], entry[a + r_] - (O[xi] + s[a + r_] / 2))
                reason[r_] = "zaman"; exm[r_] = xi
            ns = swaps_crossed(g, ee, exm)
            sw = np.where(dirn[a:b] > 0, SWAP_LONG, SWAP_SHORT) * entry[a:b] * ns
            net = gain + sw
            o = out[v.name]
            o["R"][a:b] = net / D[a:b]
            o["gain_bp"][a:b] = net / entry[a:b] * 1e4
            o["hold"][a:b] = exm - ee
            o["nswap"][a:b] = ns
            o["reason"][a:b] = reason
            o["gapfill"][a:b] = gap
    out["_entry"] = entry; out["_e"] = e; out["_D"] = D; out["_s"] = s
    return out


# ───────────────────────── istatistik ─────────────────────────
def day_key(m: np.ndarray) -> np.ndarray:
    return (np.asarray(m) // 1440).astype(np.int64)


def boot_mean(R: np.ndarray, days: np.ndarray, B: int = 2000, seed: int = 7):
    R = np.asarray(R, float); ok = ~np.isnan(R); R = R[ok]; days = np.asarray(days)[ok]
    if len(R) < 5:
        return np.nan, np.nan, np.nan
    u, inv = np.unique(days, return_inverse=True)
    sums = np.bincount(inv, weights=R); cnt = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(u), size=(B, len(u)))
    bm = sums[pick].sum(1) / cnt[pick].sum(1)
    return float((bm > 0).mean()), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))


def cluster_t(R: np.ndarray, days: np.ndarray) -> float:
    R = np.asarray(R, float); ok = ~np.isnan(R); R = R[ok]; days = np.asarray(days)[ok]
    if len(R) < 5:
        return np.nan
    u, inv = np.unique(days, return_inverse=True)
    mu = R.mean()
    res = np.bincount(inv, weights=R - mu)
    se = np.sqrt((res ** 2).sum()) / len(R)
    return float(mu / se) if se > 0 else np.nan


def p_one(t: float) -> float:
    from math import erfc, sqrt
    return 0.5 * erfc(t / sqrt(2)) if not np.isnan(t) else np.nan


def as_traded(e: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Zaman sıralı; önceki pozisyon kapanmadan gelen olay atlanır. Maske döner (orijinal sıra)."""
    o = np.argsort(e, kind="stable"); keep = np.zeros(len(e), bool); busy = -1
    for i in o:
        if e[i] >= busy:
            keep[i] = True; busy = x[i]
    return keep


def basic(R, days, wins=None) -> dict:
    R = np.asarray(R, float); ok = ~np.isnan(R)
    Rr = R[ok]
    if len(Rr) == 0:
        return dict(n=0)
    P, lo, hi = boot_mean(R, days)
    w = Rr[Rr > 0]; l_ = Rr[Rr <= 0]
    be = abs(l_.mean()) / (w.mean() + abs(l_.mean())) if len(w) and len(l_) else np.nan
    return dict(n=int(len(Rr)), ndays=int(len(np.unique(np.asarray(days)[ok]))), WR=float((Rr > 0).mean()),
                meanR=float(Rr.mean()), lo=lo, hi=hi, P=P, beWR=float(be), t=cluster_t(R, days))


def card(R, R_stress, R_opt, days, order_key, keep_single) -> dict:
    """6 ölçütlü kart (prereg §0)."""
    R = np.asarray(R, float); ok = ~np.isnan(R)
    b = basic(R, days)
    if b.get("n", 0) == 0:
        return dict(n=0)
    o = np.argsort(np.asarray(order_key)[ok], kind="stable")
    Rs = R[ok][o]; h = len(Rs) // 2
    h1, h2 = float(Rs[:h].mean()), float(Rs[h:].mean())
    st = float(np.nanmean(np.asarray(R_stress)[ok])); op = float(np.nanmean(np.asarray(R_opt)[ok]))
    sp = float(np.nanmean(R[ok & keep_single])) if (ok & keep_single).any() else np.nan
    c = dict(b)
    c.update(h1=h1, h2=h2, stress=st, opt=op, gap=abs(op - b["meanR"]), single=sp, n_single=int((ok & keep_single).sum()))
    c["k1"] = b["n"] >= 150
    c["k2"] = b["meanR"] > 0 and b["P"] >= 0.90
    c["k3"] = h1 >= 0 and h2 >= 0
    c["k4"] = st > 0
    c["k5"] = c["gap"] <= 0.5 * abs(b["meanR"])
    c["k6"] = sp > 0
    c["passed"] = int(sum(c[f"k{i}"] for i in range(1, 7)))
    return c


def period_of(m: np.ndarray) -> np.ndarray:
    t = ts_of(m)
    p = np.full(len(t), "", dtype=object)
    for k, (a, b) in PERIODS.items():
        p[(t >= a) & (t < b)] = k
    return p


def within_year_perm(labels: np.ndarray, years: np.ndarray, rng) -> np.ndarray:
    out = labels.copy()
    for y in np.unique(years):
        ix = np.where(years == y)[0]
        out[ix] = labels[rng.permutation(ix)]
    return out


def atr_wilder(h, l, c, n=14):
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.stack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    tr[0] = h[0] - l[0]
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().to_numpy()
