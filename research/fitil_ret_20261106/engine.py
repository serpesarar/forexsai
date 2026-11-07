"""Büyük fitil → ret yönü motoru (PROTOCOL.md). Tüm HTF mumları için her yön × D × SL × TP sonucunu hesaplar;
olay hücreleri bu matrisin alt kümeleridir (taban, plasebo, ızgara aynı matristen)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
R = HERE.parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)

DELAYS = (0, 5, 10, 15, 20)
SL_MODES = ("tip", "a0.5", "a1.0", "a1.5")
TPS = (0.5, 1.0, 1.5, 2.0, 3.0)
TIP_PAD = 0.1          # fitil ucu + 0,1 ATR
ATR_N = 14
CTX_N = 6              # bağlam: 6 mum önceki kapanıştan hareket
HOLD = {60: 8, 240: 6}  # zaman stopu (HTF mum)
GAP_MIN = 180           # > 3 sa boşluk → önceki barda çık
MAX_ENTRY_LAG = 30      # istenen girişten sonra ilk bar 30 dk'dan geç gelirse işlem yok
KESIF_END = pd.Timestamp("2025-07-01", tz="UTC")


@dataclass
class Base:
    t: np.ndarray       # dakika (epoch/60), int
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spo: np.ndarray     # açılış spread'i
    spc: np.ndarray     # bar spread'i (high/low/close ask yaklaşımı)
    step: int           # taban bar süresi (dk)


def load_1m(spread_mult: float = 1.0) -> Base:
    d = pd.read_parquet(R / "haber_derin_20261105/data/NDX_1m.parquet").sort_values("t").reset_index(drop=True)
    spo = (d.ask_open - d.open).clip(lower=0).to_numpy()
    spc = ((d.ask_open - d.open) + (d.ask_close - d.close)).clip(lower=0).to_numpy() / 2
    return Base((d.t.to_numpy() // 60).astype(np.int64), d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(),
                d.close.to_numpy(), spo * spread_mult, spc * spread_mult, 1)


def load_long1h(spread: float = 1.5, end: str = "2024-01-01") -> Base:
    d = pd.read_parquet(R / "ndx_gate_forge/data/long_1h_utc.parquet")
    d = d[d.ts < pd.Timestamp(end, tz="UTC")].sort_values("ts").reset_index(drop=True)
    t = (d.ts.astype("int64") // 10**9 // 60).to_numpy()
    sp = np.full(len(d), spread)
    return Base(t, d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy(), sp, sp, 60)


def htf_bars(B: Base, tf: int) -> pd.DataFrame:
    """HTF mumları. 1h: UTC saat başı; 4h: 17:00 ET çapası. Mum, son taban barı kapanınca bilinir."""
    ts = pd.to_datetime(B.t * 60, unit="s", utc=True)
    if tf == 60:
        key = ts.floor("60min")
    else:
        ny = ts.tz_convert("America/New_York").tz_localize(None)
        k = (ny - pd.Timedelta(hours=17)).floor("240min") + pd.Timedelta(hours=17)
        key = pd.Series(k)
    key = pd.Series(np.asarray(key))
    g = pd.DataFrame({"key": key.values, "i": np.arange(len(B.t))})
    a = g.groupby("key", sort=False).i.agg(["first", "last", "size"]).reset_index()
    a = a.sort_values("first").reset_index(drop=True)
    o = B.o[a["first"]]
    c = B.c[a["last"]]
    hi = np.maximum.reduceat(B.h, a["first"].to_numpy())
    lo = np.minimum.reduceat(B.l, a["first"].to_numpy())
    # reduceat sınırları ardışık olduğundan son grubun sonu dizinin sonu; gruplar ardışık mı kontrol
    assert (a["first"].to_numpy()[1:] == a["last"].to_numpy()[:-1] + 1).all()
    f = pd.DataFrame({"first": a["first"], "last": a["last"], "n": a["size"], "o": o, "h": hi, "l": lo, "c": c})
    f["close_t"] = B.t[f["last"]] + B.step          # mumun bilindiği dakika
    f["ts"] = pd.to_datetime(B.t[f["first"]] * 60, unit="s", utc=True)
    need = tf // B.step
    f["full"] = f.n * B.step >= tf / 2 if B.step == 1 else f.n >= need
    pc = f.c.shift(1)
    tr = np.maximum(f.h - f.l, np.maximum((f.h - pc).abs(), (f.l - pc).abs()))
    f["atr"] = tr.rolling(ATR_N).mean()
    rng = (f.h - f.l).replace(0, np.nan)
    f["uw"] = f.h - np.maximum(f.o, f.c)
    f["lw"] = np.minimum(f.o, f.c) - f.l
    f["s_up"], f["s_dn"] = f.uw / rng, f.lw / rng
    f["w_up"], f["w_dn"] = f.uw / f.atr, f.lw / f.atr
    f["M"] = (f.c - f.c.shift(CTX_N)) / f.atr
    ny = f.ts.dt.tz_convert("America/New_York")
    f["hour"] = f.ts.dt.hour
    f["day"] = (ny.dt.tz_localize(None) + pd.Timedelta(hours=7)).dt.date
    f["ny_min"] = ny.dt.hour * 60 + ny.dt.minute
    f["year"] = ny.dt.year
    f["kesif"] = f.ts < KESIF_END
    return f


def _first_ge(cm: np.ndarray, x: np.ndarray) -> np.ndarray:
    """cm artan (cummax); her x için cm >= x ilk indeks (yoksa len)."""
    return np.searchsorted(cm, x, side="left")


def outcomes(B: Base, F: pd.DataFrame, tf: int) -> np.ndarray:
    """R[bar, side(0=SAT,1=AL), D, SL, TP] (NaN = işlem yok) + giriş indeksi E[bar, D]."""
    nb = len(F)
    Rm = np.full((nb, 2, len(DELAYS), len(SL_MODES), len(TPS)), np.nan)
    Tm = np.full((nb, len(DELAYS)), -1, dtype=np.int64)
    hold = HOLD[tf] * tf
    t = B.t
    gap_after = np.r_[np.diff(t) > GAP_MIN, True]       # bu bardan sonra boşluk
    nxt_gap = np.searchsorted(np.flatnonzero(gap_after), np.arange(len(t)))
    gap_idx = np.flatnonzero(gap_after)
    ok = F.full.to_numpy() & np.isfinite(F.atr.to_numpy())
    for bi in np.flatnonzero(ok):
        atr = F.atr.iat[bi]
        H, L = F.h.iat[bi], F.l.iat[bi]
        ct = F.close_t.iat[bi]
        for di, D in enumerate(DELAYS):
            want = ct + D
            e = np.searchsorted(t, want)
            if e >= len(t) or t[e] - want > MAX_ENTRY_LAG:
                continue
            Tm[bi, di] = e
            end_t = t[e] + hold
            j1 = min(np.searchsorted(t, end_t, side="right"), gap_idx[nxt_gap[e]] + 1)
            sl = slice(e, j1)
            o, h, l, c = B.o[sl], B.h[sl], B.l[sl], B.c[sl]
            spo, spc = B.spo[sl], B.spc[sl]
            n = j1 - e
            # ---- SAT: bid'den gir, ask'tan çık
            Eb = o[0]
            adv = np.maximum.accumulate(h + spc)            # ask high
            fav = -np.minimum.accumulate(l + spc)           # -(ask low)
            dists = np.array([H + TIP_PAD * atr - Eb, 0.5 * atr, 1.0 * atr, 1.5 * atr])
            for si, dist in enumerate(dists):
                if not dist > 0:
                    continue
                P = Eb + dist
                ks = _first_ge(adv, P)
                if ks < n:
                    fill = max(P, o[ks] + spo[ks]) if ks > 0 else max(P, o[0] + spo[0])
                    r_sl = (Eb - fill) / dist
                ktp = _first_ge(fav, -(Eb - np.array(TPS) * dist))
                r_time = (Eb - (c[-1] + spc[-1])) / dist
                for ti, r in enumerate(TPS):
                    if ks < n and ks <= ktp[ti]:
                        Rm[bi, 0, di, si, ti] = r_sl
                    elif ktp[ti] < n:
                        Rm[bi, 0, di, si, ti] = r
                    else:
                        Rm[bi, 0, di, si, ti] = r_time
            # ---- AL: ask'tan gir, bid'den çık
            Ea = o[0] + spo[0]
            adv2 = -np.minimum.accumulate(l)                # -(bid low)
            fav2 = np.maximum.accumulate(h)                 # bid high
            dists = np.array([Ea - (L - TIP_PAD * atr), 0.5 * atr, 1.0 * atr, 1.5 * atr])
            for si, dist in enumerate(dists):
                if not dist > 0:
                    continue
                P = Ea - dist
                ks = _first_ge(adv2, -P)
                if ks < n:
                    fill = min(P, o[ks])
                    r_sl = (fill - Ea) / dist
                ktp = _first_ge(fav2, Ea + np.array(TPS) * dist)
                r_time = (c[-1] - Ea) / dist
                for ti, r in enumerate(TPS):
                    if ks < n and ks <= ktp[ti]:
                        Rm[bi, 1, di, si, ti] = r_sl
                    elif ktp[ti] < n:
                        Rm[bi, 1, di, si, ti] = r
                    else:
                        Rm[bi, 1, di, si, ti] = r_time
    return Rm, Tm


def event_mask(F: pd.DataFrame, side: int, s: float, w: float, k: float) -> np.ndarray:
    """side 0 = üst fitil → SAT, 1 = alt fitil → AL."""
    if side == 0:
        m = (F.s_up >= s) & (F.w_up >= w) & (F.uw >= 2 * F.lw)
        if k > 0:
            m &= F.M >= k
    else:
        m = (F.s_dn >= s) & (F.w_dn >= w) & (F.lw >= 2 * F.uw)
        if k > 0:
            m &= F.M <= -k
    return m.fillna(False).to_numpy()


def build(tf: int, B: Base | None = None, tag: str = "duka") -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    p = OUT / f"cache_{tag}_{tf}.npz"
    if B is None:
        B = load_1m()
    F = htf_bars(B, tf)
    if p.exists():
        z = np.load(p)
        if len(z["R"]) == len(F):
            return F, z["R"], z["T"]
    Rm, Tm = outcomes(B, F, tf)
    np.savez_compressed(p, R=Rm, T=Tm)
    return F, Rm, Tm


def simulate_one(B: Base, e: int, side: int, dist: float, r: float, hold_min: int) -> tuple[float, int]:
    """Tek işlem (ayna, tek pozisyon için). side 0 = SAT, 1 = AL. (R, çıkış indeksi)."""
    t = B.t
    j1 = np.searchsorted(t, t[e] + hold_min, side="right")
    gaps = np.flatnonzero(np.diff(t[e:j1]) > GAP_MIN)
    if len(gaps):
        j1 = e + gaps[0] + 1
    sl = slice(e, j1)
    o, h, l, c, spo, spc = B.o[sl], B.h[sl], B.l[sl], B.c[sl], B.spo[sl], B.spc[sl]
    n = j1 - e
    if side == 0:
        Eb = o[0]; P = Eb + dist
        ks = _first_ge(np.maximum.accumulate(h + spc), P)
        kt = _first_ge(-np.minimum.accumulate(l + spc), -(Eb - r * dist))
        if ks < n and ks <= kt:
            return (Eb - max(P, o[ks] + spo[ks])) / dist, e + ks
        if kt < n:
            return r, e + kt
        return (Eb - (c[-1] + spc[-1])) / dist, j1 - 1
    Ea = o[0] + spo[0]; P = Ea - dist
    ks = _first_ge(-np.minimum.accumulate(l), -P)
    kt = _first_ge(np.maximum.accumulate(h), Ea + r * dist)
    if ks < n and ks <= kt:
        return (min(P, o[ks]) - Ea) / dist, e + ks
    if kt < n:
        return r, e + kt
    return (c[-1] - Ea) / dist, j1 - 1


def sl_dist(F: pd.DataFrame, bi: int, side: int, si: int, entry_px: float) -> float:
    atr = F.atr.iat[bi]
    if si == 0:
        return (F.h.iat[bi] + TIP_PAD * atr - entry_px) if side == 0 else (entry_px - (F.l.iat[bi] - TIP_PAD * atr))
    return float(SL_MODES[si][1:]) * atr
