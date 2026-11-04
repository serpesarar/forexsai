"""fam_mr_zaman ortak motor: dakika ızgarası, broker takvimi, icra/maliyet, kart ölçütleri.

Ön-kayıt: prereg.md. Tüm zamanlar UTC; dakika indeksi m = 2021-06-01 00:00'dan itibaren dakika.
"""
from __future__ import annotations

import os
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

DATA = "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data"
OUT = "/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/results"
os.makedirs(OUT, exist_ok=True)

T0 = pd.Timestamp("2021-06-01", tz="UTC")
T_END = pd.Timestamp("2026-10-21", tz="UTC")
N = int((T_END - T0) / pd.Timedelta(minutes=1))  # 2.833.920

S_BASE = 0.000185
S_STRESS = 0.00028
S_ABS = 15.0
SWAP_LONG = -0.14 / 365
SWAP_SHORT = 0.02 / 365
ENTRY_MAX_DELAY = 10
N_BOOT = 5000
N_PLAC = 200

PERIODS = {
    "KESIF": ("2021-06-01", "2024-01-01"),
    "OOS": ("2024-01-11", "2025-07-01"),
    "KOR": ("2025-07-01", "2026-10-21"),
}


def tmin(ts: str | pd.Timestamp) -> int:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return int((t - T0) / pd.Timedelta(minutes=1))


PER_BOUNDS = {k: (tmin(a), tmin(b)) for k, (a, b) in PERIODS.items()}


def period_of(m: np.ndarray) -> np.ndarray:
    out = np.full(len(m), "", dtype=object)
    for k, (a, b) in PER_BOUNDS.items():
        out[(m >= a) & (m < b)] = k
    return out


# ---------------------------------------------------------------- dakika ızgarası
def _load_grid():
    df = pd.read_parquet(f"{DATA}/btc_1m.parquet", columns=["ts", "open", "high", "low", "close"])
    idx = ((df["ts"] - T0) / pd.Timedelta(minutes=1)).to_numpy().astype(np.int64)
    arr = {}
    for c in ["open", "high", "low", "close"]:
        a = np.full(N, np.nan)
        a[idx] = df[c].to_numpy()
        arr[c] = a
    return arr


G = _load_grid()
O_RAW, H_RAW, L_RAW, C_RAW = G["open"], G["high"], G["low"], G["close"]
PRESENT = ~np.isnan(C_RAW)

# kötü dakikalar: Binance kesintileri (>=5 dk eksik) + 2023-03-24 dışlaması
BAD = np.zeros(N, dtype=bool)
BAD[tmin("2023-03-24 11:28"):tmin("2023-03-24 14:00")] = True
_miss = ~PRESENT
_d = np.diff(np.concatenate([[0], _miss.astype(np.int8), [0]]))
_st, _en = np.where(_d == 1)[0], np.where(_d == -1)[0]
for a, b in zip(_st, _en):
    if b - a >= 5:
        BAD[a:b] = True
BAD_CS = np.concatenate([[0], np.cumsum(BAD)])

# rollover ve broker kapanış dakikaları
NY = ZoneInfo("America/New_York")
_days = pd.date_range(T0, T_END - pd.Timedelta(days=1), freq="D")
ROLL = []
DST = []
CLOSED = np.zeros(N, dtype=bool)
for d in _days:
    cand = (d + pd.Timedelta(hours=22)).to_pydatetime()
    dst = cand.astimezone(NY).utcoffset() == pd.Timedelta(hours=-4)
    r = tmin(d + pd.Timedelta(hours=21 if dst else 22))
    ROLL.append(r)
    DST.append(dst)
    lo = r - (5 if d.dayofweek == 4 else 1)
    CLOSED[max(lo, 0):min(r + 1, N)] = True  # sunucu 23:59 (Cuma 23:55) ve 00:00
ROLL = np.array(ROLL, dtype=np.int64)
DAY_DST = np.array(DST)  # UTC gün indeksi -> ABD DST mi

TRAD = PRESENT & ~CLOSED & ~BAD
O = np.where(TRAD, O_RAW, np.nan)
H = np.where(TRAD, H_RAW, np.nan)
L = np.where(TRAD, L_RAW, np.nan)
C = np.where(TRAD, C_RAW, np.nan)

# sonraki / önceki işlem görülebilir dakika
_ar = np.arange(N)
_nx = np.where(TRAD, _ar, N)
NXT = np.minimum.accumulate(_nx[::-1])[::-1]
_pv = np.where(TRAD, _ar, -1)
PRV = np.maximum.accumulate(_pv)
_prs = np.where(PRESENT, _ar, -1)
PRV_RAW = np.maximum.accumulate(_prs)


def rollovers_between(e: np.ndarray, x_incl: np.ndarray) -> np.ndarray:
    """e < r <= x_incl olan rollover sayısı."""
    return np.searchsorted(ROLL, x_incl, side="right") - np.searchsorted(ROLL, e, side="right")


def bad_in(e: np.ndarray, x: np.ndarray) -> np.ndarray:
    return (BAD_CS[np.minimum(x + 1, N)] - BAD_CS[e]) > 0


# ---------------------------------------------------------------- ATR14(1h)
def _hourly_atr():
    h = pd.read_parquet(f"{DATA}/btc_1h.parquet", columns=["ts", "high", "low", "close"])
    hi = ((h["ts"] - T0) / pd.Timedelta(hours=1)).to_numpy().astype(np.int64)
    pc = h["close"].shift(1)
    tr = np.maximum(h["high"] - h["low"], np.maximum((h["high"] - pc).abs(), (h["low"] - pc).abs()))
    atr = tr.rolling(14).mean().to_numpy()
    dense = np.full(N // 60 + 2, np.nan)
    dense[hi] = atr
    # eksik saat (kesinti) -> son bilinen değer
    s = pd.Series(dense).ffill().to_numpy()
    return s


ATR1H_DENSE = _hourly_atr()


def atr1h_at(m: np.ndarray) -> np.ndarray:
    """Karar anı m (dakika başı) için son kapanmış 1h barın ATR14'ü."""
    return ATR1H_DENSE[m // 60 - 1]


# ---------------------------------------------------------------- zaman pencereli işlem
def window_trades(entry_t: np.ndarray, exit_t: np.ndarray, direction: int, s_frac: float | None = S_BASE,
                  s_abs: float | None = None, swap: bool = True, optimistic: bool = False) -> pd.DataFrame:
    """entry_t: hedef giriş dakikası (karar = önceki dakikanın kapanışı); exit_t: kapanışında çıkılacak son dakika."""
    entry_t = np.asarray(entry_t, dtype=np.int64)
    exit_t = np.asarray(exit_t, dtype=np.int64)
    ok0 = (entry_t >= 61) & (exit_t < N) & (entry_t < N)
    et = np.where(ok0, entry_t, 61)
    xt = np.where(ok0, exit_t, 61)
    e = NXT[et]
    e_ok = (e < N) & (e - et <= ENTRY_MAX_DELAY)
    e = np.minimum(e, N - 1)
    x = PRV[xt]
    ok = ok0 & e_ok & (x >= e) & ~bad_in(e, np.maximum(x, e))
    if optimistic:
        dm = PRV_RAW[et - 1]
        mid_in = C_RAW[np.maximum(dm, 0)]
        s = np.zeros(len(et))
    else:
        mid_in = O[e]
        s = mid_in * s_frac if s_abs is None else np.full(len(et), s_abs)
    mid_out = C[np.maximum(x, 0)]
    if direction == 1:
        pnl = (mid_out - s / 2) - (mid_in + s / 2)
    else:
        pnl = (mid_in - s / 2) - (mid_out + s / 2)
    nights = rollovers_between(e, x + 1)
    if swap:
        pnl = pnl + nights * (SWAP_LONG if direction == 1 else SWAP_SHORT) * mid_in
    D = atr1h_at(et)
    out = pd.DataFrame({
        "t": et, "e": e, "x": x, "dir": direction, "mid_in": mid_in, "pnl": pnl,
        "bp": pnl / mid_in * 1e4, "D": D, "R": pnl / D, "nights": nights, "ok": ok,
    })
    out = out[out["ok"] & np.isfinite(out["R"])].drop(columns="ok")
    return out


# ---------------------------------------------------------------- braketli işlem (1m yol)
def bracket_trades(dec_t: np.ndarray, direction: int, D: np.ndarray, TPd: np.ndarray, cap: np.ndarray,
                   s_frac: float | None = S_BASE, s_abs: float | None = None, optimistic: bool = False,
                   dec_close: np.ndarray | None = None, chunk_cells: int = 12_000_000) -> pd.DataFrame:
    """dec_t: karar anı (dakika; giriş hedefi = dec_t). D: SL mesafesi ($), TPd: TP mesafesi ($, inf=yok),
    cap: giriş hedefinden itibaren en fazla dakika. Dönüş: R, pnl, bp, çıkış türü."""
    dec_t = np.asarray(dec_t, dtype=np.int64)
    n = len(dec_t)
    e = NXT[np.minimum(dec_t, N - 1)]
    e_ok = (e < N) & (e - dec_t <= ENTRY_MAX_DELAY)
    e = np.minimum(e, N - 1)
    endm = np.minimum(dec_t + cap - 1, N - 1)
    R = np.full(n, np.nan)
    PNL = np.full(n, np.nan)
    XI = np.full(n, -1, dtype=np.int64)
    KIND = np.zeros(n, dtype=np.int8)  # 1 TP, -1 SL, 0 zaman
    MID = np.full(n, np.nan)
    Lmax = int(cap.max()) if n else 0
    step = max(1, chunk_cells // max(Lmax, 1))
    ar = np.arange(Lmax)
    for a in range(0, n, step):
        b = min(n, a + step)
        ee, en = e[a:b], endm[a:b]
        good = e_ok[a:b] & (en >= ee)
        idx = ee[:, None] + ar[None, :]
        inwin = idx <= en[:, None]
        idx = np.minimum(idx, N - 1)
        hh = np.where(inwin, H[idx], np.nan)
        ll = np.where(inwin, L[idx], np.nan)
        oo = np.where(inwin, O[idx], np.nan)
        if optimistic:
            mid = dec_close[a:b]
            s = np.zeros(b - a)
        else:
            mid = O[ee]
            s = mid * s_frac if s_abs is None else np.full(b - a, s_abs)
        d = direction
        E = mid + d * s / 2
        Dd, Td = D[a:b], TPd[a:b]
        SLl = E - d * Dd
        TPl = E + d * Td
        if d == 1:
            slh = (ll - s[:, None] / 2) <= SLl[:, None]
            tph = (hh - s[:, None] / 2) >= TPl[:, None]
        else:
            slh = (hh + s[:, None] / 2) >= SLl[:, None]
            tph = (ll + s[:, None] / 2) <= TPl[:, None]
        big = Lmax + 5
        fs = np.where(slh.any(1), slh.argmax(1), big)
        ft = np.where(tph.any(1), tph.argmax(1), big)
        kind = np.where((fs <= ft) & (fs < big), -1, np.where(ft < big, 1, 0))
        rows = np.arange(b - a)
        # SL dolumu (boşluk)
        o_at = oo[rows, np.minimum(fs, Lmax - 1)]
        if d == 1:
            sl_fill = np.minimum(SLl, o_at - s / 2)
        else:
            sl_fill = np.maximum(SLl, o_at + s / 2)
        sl_fill = np.where(np.isnan(sl_fill), SLl, sl_fill)
        xt = PRV[en]
        tclose = C[np.maximum(xt, 0)] - d * s / 2
        exitp = np.where(kind == -1, sl_fill, np.where(kind == 1, TPl, tclose))
        xi = np.where(kind == -1, ee + fs, np.where(kind == 1, ee + ft, xt))
        good &= (xi >= ee) & np.isfinite(exitp)
        pnl = d * (exitp - E)
        nights = rollovers_between(ee, xi + (kind == 0))
        pnl = pnl + nights * (SWAP_LONG if d == 1 else SWAP_SHORT) * mid
        good &= ~bad_in(ee, np.maximum(xi, ee))
        R[a:b] = np.where(good, pnl / Dd, np.nan)
        PNL[a:b] = np.where(good, pnl, np.nan)
        XI[a:b] = np.where(good, xi, -1)
        KIND[a:b] = kind
        MID[a:b] = mid
    return pd.DataFrame({"t": dec_t, "e": e, "x": XI, "R": R, "pnl": PNL, "bp": PNL / MID * 1e4,
                         "kind": KIND, "D": D, "mid_in": MID})


# ---------------------------------------------------------------- istatistik
RNG = np.random.default_rng(20261021)


def day_sums(t: np.ndarray, v: np.ndarray):
    day = t // 1440
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=v)
    n = np.bincount(inv)
    return S, n


def boot_day(t: np.ndarray, v: np.ndarray, nb: int = N_BOOT, seed: int = 11):
    if len(v) < 20:
        return np.nan, (np.nan, np.nan)
    S, n = day_sums(t, v)
    rng = np.random.default_rng(seed)
    G_ = len(S)
    means = np.empty(nb)
    for i in range(0, nb, 500):
        k = min(500, nb - i)
        idx = rng.integers(0, G_, size=(k, G_))
        means[i:i + k] = S[idx].sum(1) / n[idx].sum(1)
    return float((means > 0).mean()), (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def cluster_t(t: np.ndarray, v: np.ndarray) -> float:
    if len(v) < 5:
        return np.nan
    S, n = day_sums(t, v)
    m = v.mean()
    G_ = len(S)
    if G_ < 3:
        return np.nan
    var = ((S - n * m) ** 2).sum() / len(v) ** 2 * G_ / (G_ - 1)
    return float(m / np.sqrt(var)) if var > 0 else np.nan


def single_position(t: np.ndarray, e: np.ndarray, x: np.ndarray) -> np.ndarray:
    o = np.argsort(t, kind="stable")
    keep = np.zeros(len(t), dtype=bool)
    last = -1
    for i in o:
        if e[i] > last:
            keep[i] = True
            last = x[i]
    return keep


def wr_be(R: np.ndarray):
    w = R[R > 0]
    l_ = R[R <= 0]
    wr = len(w) / len(R) if len(R) else np.nan
    if len(w) and len(l_):
        be = -l_.mean() / (w.mean() - l_.mean())
    else:
        be = np.nan
    return wr, be


def summarize(df: pd.DataFrame, prefix: str = "") -> dict:
    R = df["R"].to_numpy()
    t = df["t"].to_numpy()
    if len(R) == 0:
        return {f"{prefix}n": 0}
    wr, be = wr_be(R)
    P, ci = boot_day(t, R)
    return {f"{prefix}n": len(R), f"{prefix}wr": wr, f"{prefix}be_wr": be, f"{prefix}meanR": R.mean(),
            f"{prefix}bp": df["bp"].mean(), f"{prefix}P": P, f"{prefix}ci_lo": ci[0], f"{prefix}ci_hi": ci[1],
            f"{prefix}t": cluster_t(t, R)}


def halves(df: pd.DataFrame):
    d = df.sort_values("t")
    k = len(d) // 2
    return d["R"].iloc[:k].mean(), d["R"].iloc[k:].mean()


def holm(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    m = np.isfinite(p).sum()
    order = np.argsort(np.where(np.isfinite(p), p, np.inf))
    adj = np.full(len(p), np.nan)
    run = 0.0
    for rank, i in enumerate(order):
        if not np.isfinite(p[i]):
            continue
        val = min(1.0, (m - rank) * p[i])
        run = max(run, val)
        adj[i] = run
    return adj


def norm_sf(z: float) -> float:
    from math import erfc, sqrt
    return 0.5 * erfc(z / sqrt(2)) if np.isfinite(z) else np.nan


def card_row(name: str, real: pd.DataFrame, stress: pd.DataFrame, opt: pd.DataFrame, abs15: pd.DataFrame,
             plac_pct: dict, extra: dict | None = None) -> dict:
    """real/stress/opt/abs15: aynı olaylar (t ile eşlenir), TAM dönem; dönem kolonu 'per'."""
    row = {"cell": name}
    row.update(summarize(real))
    h1, h2 = halves(real) if len(real) >= 2 else (np.nan, np.nan)
    row["half1"], row["half2"] = h1, h2
    row["stressR"] = stress["R"].mean() if len(stress) else np.nan
    row["abs15R"] = abs15["R"].mean() if len(abs15) else np.nan
    row["optR"] = opt["R"].mean() if len(opt) else np.nan
    row["exec_gap"] = abs(row["optR"] - row.get("meanR", np.nan))
    keep = single_position(real["t"].to_numpy(), real["e"].to_numpy(), real["x"].to_numpy())
    row["sp_n"] = int(keep.sum())
    row["spR"] = real["R"].to_numpy()[keep].mean() if keep.any() else np.nan
    row["min_sl_pct"] = float((real["D"] / real["mid_in"]).min() * 100) if len(real) else np.nan
    row["med_sl_pct"] = float((real["D"] / real["mid_in"]).median() * 100) if len(real) else np.nan
    for k in PERIODS:
        sub = real[real["per"] == k]
        r = summarize(sub, prefix=f"{k}_")
        row.update(r)
    row.update({f"plac_{k}": v for k, v in plac_pct.items()})
    if extra:
        row.update(extra)
    mR = row.get("meanR", np.nan)
    c = [row["n"] >= 150,
         (mR > 0) and (row["P"] >= 0.90),
         (h1 >= 0) and (h2 >= 0),
         row["stressR"] > 0,
         row["exec_gap"] <= 0.5 * abs(mR),
         row["spR"] > 0]
    for i, v in enumerate(c, 1):
        row[f"c{i}"] = bool(v)
    row["card_pass"] = int(sum(c))
    return row


def plac_percentile(actual_mean: float, draws: np.ndarray) -> float:
    draws = draws[np.isfinite(draws)]
    if not len(draws) or not np.isfinite(actual_mean):
        return np.nan
    return float((draws < actual_mean).mean() * 100)
