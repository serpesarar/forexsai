"""fblib.py — FB altın bölge Fibonacci motoru (PROTOCOL.md).

Veri: NDX Dukascopy 1m (BID + spr modeli) ve Pepperstone MT5 broker barları (sunucu = NY + 7).
Algılama tamamen nedensel: t barının sinyali yalnız ≤ t barlarına bakar (önek testi `prefix_test`).
"""
from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
CACHE = HERE / "cache"
SYM = os.getenv("FB_SYM", "NDX")      # EK-3: NDX (varsayılan) | DAX | XAU
RESULTS = HERE / "results" if SYM == "NDX" else HERE / "results" / SYM.lower()
DUKA_BROKER = {"DAX": "GER40", "XAU": "XAUUSD"}
BROKER_POINT = {"GER40": 0.1, "XAUUSD": 0.01, "NAS100": 0.1, "SpotCrude": 0.001}
NDX_M1 = ROOT / "research/ndx_10y_1m_20261116/cache/m1_ny.parquet"
NDX_SRC = ROOT / "research/nom_20261113/data/ndx_1m_v3_duka.parquet"
MT5_DIR = ROOT / "research/c1_turev_20261105/data/mt5"

K_WIN = 40            # geri çekilme penceresi (bar)
M_WIN = 30            # itki azami uzunluğu (bar)
ATR_N = 14
SL_BUF = 0.1          # SL tamponu (ATR)
FIN_PER_NIGHT = 6.41 / 365 / 100   # ≈ 1,756 bp / gece
MIN_RISK_SPR = 2.0    # risk < 2 × spread → işlem yok (EK-1)
BROKER_SPREAD = {"NAS100": 1.3, "GER40": 1.2, "US500": 0.5, "XAUUSD": 0.25, "SpotCrude": 0.03}
SERVER_OFFSET_S = 7 * 3600

KESIF_END = np.datetime64("2021-12-31")
TEST_END = np.datetime64("2024-06-30")

ZONES = {  # ad: (bölge üst sınırı a = en az bu kadar geri çekil, bozulma inv)
    "altin": (0.5, 0.786),
    "sig382": (0.382, 0.618),
    "cok_sig": (0.236, 0.5),
    "derin": (0.618, 1.0),
}

_lib = ctypes.CDLL(str(Path(__file__).with_name("fb_resolve.dylib")))
_P = np.ctypeslib.ndpointer
_lib.resolve.argtypes = [ctypes.c_int64, _P(np.float64), _P(np.float64), _P(np.float64), _P(np.float64),
                         _P(np.float64), ctypes.c_int64, _P(np.int32), _P(np.int64), _P(np.int64),
                         _P(np.float64), _P(np.float64), _P(np.float64), _P(np.float64), _P(np.int64), _P(np.int32)]
_lib.single_pos.argtypes = [ctypes.c_int64, _P(np.int64), _P(np.int64), _P(np.int32)]


# ═══════════════════════════ yol (çözüm serisi) ═══════════════════════════

@dataclass
class Path1:
    """Çıkışların çözüldüğü seri (NDX'te 1m, broker'da sinyal TF'inin kendisi)."""
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    spr: np.ndarray
    local: np.ndarray     # NY yerel saniye (epoch gibi, saat dilimi uygulanmış)
    rollday: np.ndarray   # 17:00 ET devrine göre gün numarası

    @property
    def n(self) -> int:
        return len(self.o)


def _ny_local(t_utc: np.ndarray) -> np.ndarray:
    ts = pd.to_datetime(t_utc, unit="s", utc=True).tz_convert("America/New_York")
    return (ts.tz_localize(None).values.astype("datetime64[s]").astype(np.int64))


def make_path(o, h, l, c, spr, local) -> Path1:
    rollday = (local + 7 * 3600) // 86400
    return Path1(np.ascontiguousarray(o, float), np.ascontiguousarray(h, float), np.ascontiguousarray(l, float),
                 np.ascontiguousarray(c, float), np.ascontiguousarray(spr, float), local.astype(np.int64),
                 rollday.astype(np.int64))


def load_ndx_1m() -> Path1:
    CACHE.mkdir(exist_ok=True)
    cp = CACHE / "ndx_1m.npz"
    if cp.exists():
        z = np.load(cp)
        return make_path(z["o"], z["h"], z["l"], z["c"], z["spr"], z["local"])
    df = pd.read_parquet(NDX_SRC, columns=["t", "open", "high", "low", "close", "spr"]).sort_values("t")
    df = df.drop_duplicates("t").reset_index(drop=True)
    local = _ny_local(df.t.values)
    np.savez(cp, o=df.open.values, h=df.high.values, l=df.low.values, c=df.close.values, spr=df.spr.values, local=local)
    return make_path(df.open.values, df.high.values, df.low.values, df.close.values, df.spr.values, local)


def load_duka(sym: str) -> Path1:
    """EK-3: Dukascopy 1m BID 2018-01 → 2026-11 + spread = NY saati başına max(Duka 2025 ask−bid medyanı, Pepperstone
    M1 medyanı) — NDX'teki koruyucu spread modelinin aynısı (nom_20261113/src/data_layer.spread_model)."""
    CACHE.mkdir(exist_ok=True)
    cp = CACHE / f"{sym}_1m.npz"
    if cp.exists():
        z = np.load(cp)
        return make_path(z["o"], z["h"], z["l"], z["c"], z["spr"], z["local"])
    df = pd.read_parquet(CACHE / f"{sym}_1m_raw.parquet").sort_values("t").drop_duplicates("t")
    df = df[(df.high >= df.low) & (df.high >= df[["open", "close"]].max(axis=1)) & (df.low <= df[["open", "close"]].min(axis=1))]
    local = _ny_local(df.t.values.astype(np.int64))
    hr = (local // 3600) % 24
    obs = (df.ask_open - df.open).where(lambda x: x > 0)
    duka_h = obs.groupby(hr).median().reindex(range(24))
    bsym = DUKA_BROKER.get(sym)
    if bsym:
        b = pd.read_csv(MT5_DIR / f"{bsym}_M1.csv.gz", usecols=["t", "sp"])
        bh = ((b.t.values.astype(np.int64) - SERVER_OFFSET_S) // 3600) % 24
        brk_h = (b.sp * BROKER_POINT[bsym]).groupby(bh).median().reindex(range(24))
    else:      # EK-3b: CAC / Stoxx için broker beslemesi yok → yalnız Dukascopy 2025 ask−bid
        brk_h = pd.Series(np.nan, index=range(24))
    model = np.fmax(duka_h.values, brk_h.values)
    model = pd.Series(model).ffill().bfill().values
    spr = model[hr]
    out_dir = HERE / "results" / sym.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"ny_saat": range(24), "duka_2025": duka_h.values, "broker": brk_h.values, "model": model}).round(4) \
        .to_csv(out_dir / "spread_modeli.csv", index=False)
    np.savez(cp, o=df.open.values, h=df.high.values, l=df.low.values, c=df.close.values, spr=spr, local=local)
    return make_path(df.open.values, df.high.values, df.low.values, df.close.values, spr, local)


def load_main() -> Path1:
    return load_ndx_1m() if SYM == "NDX" else load_duka(SYM)


def load_broker(sym: str, tf: str) -> Path1:
    df = pd.read_csv(MT5_DIR / f"{sym}_{tf}.csv.gz").sort_values("t").drop_duplicates("t")
    local = df.t.values.astype(np.int64) - SERVER_OFFSET_S
    keep = local >= np.datetime64("2018-05-01").astype("datetime64[s]").astype(np.int64)
    df, local = df[keep], local[keep]
    spr = np.full(len(df), BROKER_SPREAD[sym])
    return make_path(df.o.values, df.h.values, df.l.values, df.c.values, spr, local)


# ═══════════════════════════ sinyal TF barları ═══════════════════════════

@dataclass
class Bars:
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    atr: np.ndarray
    first: np.ndarray    # yol indeksi: barın ilk 1m'i
    last: np.ndarray     # yol indeksi: barın son 1m'i
    tf: str


def build_bars(p: Path1, tf_min: int, anchor_min: int = 0, tf: str = "") -> Bars:
    if tf_min == 1 or tf_min == 0:
        first = np.arange(p.n)
        last = first.copy()
        o, h, l, c = p.o, p.h, p.l, p.c
    else:
        key = (p.local - anchor_min * 60) // (tf_min * 60)
        chg = np.flatnonzero(np.diff(key)) + 1
        first = np.r_[0, chg]
        last = np.r_[chg - 1, p.n - 1]
        o, c = p.o[first], p.c[last]
        h = np.maximum.reduceat(p.h, first)
        l = np.minimum.reduceat(p.l, first)
    return Bars(o, h, l, c, atr_wilder(h, l, c), first, last, tf)


def atr_wilder(h, l, c, n: int = ATR_N) -> np.ndarray:
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False).mean().values


# ═══════════════════════════ algılama ═══════════════════════════

def _sparse_min(x: np.ndarray, levels: int) -> list[np.ndarray]:
    st = [x]
    for k in range(1, levels):
        prev = st[-1]
        step = 1 << (k - 1)
        nxt = prev.copy()
        nxt[:-step] = np.minimum(prev[:-step], prev[step:])
        st.append(nxt)
    return st


def _range_min(st, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """min x[a..b] (dahil), b ≥ a."""
    ln = b - a + 1
    k = np.floor(np.log2(ln)).astype(int)
    out = np.empty(len(a))
    for kk in np.unique(k):
        m = k == kk
        s = st[kk]
        out[m] = np.minimum(s[a[m]], s[b[m] - (1 << kk) + 1])
    return out


def detect(bars: Bars, side: int) -> pd.DataFrame:
    """Aday satırlar: geçerli itki + geri çekilme içindeki her bar t (filtreler sonra uygulanır).

    side=+1 uzun; side=−1 kısa (fiyatlar aynalanır, seviyeler gerçek fiyata geri çevrilir).
    """
    if side > 0:
        O, Hh, Ll, C = bars.o, bars.h, bars.l, bars.c
    else:
        O, Hh, Ll, C = -bars.o, -bars.l, -bars.h, -bars.c
    N = len(O)
    K, M = K_WIN, M_WIN
    if N < K + M + 5:
        return pd.DataFrame()
    win = sliding_window_view(Hh[:-1], K)                  # pencere s: [s, s+K−1], t = s+K
    am = win.argmax(axis=1)
    t = np.arange(K, N)
    hidx = am + (t - K)
    win2 = sliding_window_view(Ll, M + 1)                  # pencere s: [s, s+M], j = s+M
    lw = np.full(N, -1)
    lw[M:] = win2.argmin(axis=1) + np.arange(N - M)
    ok = (am > 0) & (hidx <= t - 2) & (hidx >= M)
    t, hidx = t[ok], hidx[ok]
    lidx = lw[hidx]
    Hv, Lv = Hh[hidx], Ll[lidx]
    R = Hv - Lv
    ok = R > 0
    t, hidx, lidx, Hv, Lv, R = t[ok], hidx[ok], lidx[ok], Hv[ok], Lv[ok], R[ok]
    st = _sparse_min(Ll, 7)
    pb = _range_min(st, hidx + 1, t)
    d = (Hv - pb) / R
    dp = (Hv - np.minimum(Ll[t - 1], Ll[t])) / R
    dt = (Hv - Ll[t]) / R
    atrL = bars.atr[lidx]
    S = R / atrL
    nleg = np.maximum(hidx - lidx, 1)
    speed = S / nleg
    keep = (d < 1.0) & (dp >= 0.236) & (S >= 1.5)
    eng = (C[t] > O[t]) & (C[t - 1] < O[t - 1]) & (C[t] >= O[t - 1]) & (O[t] <= C[t - 1])
    engf = eng & (C[t] > Hh[t - 1])
    sel = np.flatnonzero(keep)
    df = pd.DataFrame({
        "t": t[sel], "hidx": hidx[sel], "lidx": lidx[sel], "side": side,
        "H": side * Hv[sel], "L": side * Lv[sel], "R": R[sel],
        "d": d[sel], "dp": dp[sel], "dt": dt[sel], "S": S[sel], "speed": speed[sel],
        "eng": eng[sel], "engf": engf[sel],
        "plow": side * np.minimum(Ll[t[sel] - 1], Ll[t[sel]]),   # örüntü ucu (uzunda dip, kısada tepe)
        "atr": bars.atr[t[sel]],
    })
    return df


def signals(cand: pd.DataFrame, pattern: str, zone: str, smin: float, spmin: float) -> pd.DataFrame:
    a, inv = ZONES[zone]
    m = (cand.S >= smin) & (cand.speed >= spmin) & (cand.d < inv)
    if pattern == "eng":
        m &= cand.eng & (cand.dp >= a)
    elif pattern == "engf":
        m &= cand.engf & (cand.dp >= a)
    elif pattern == "none":
        m &= cand.dt >= a
    else:
        raise ValueError(pattern)
    s = cand[m]
    return s.drop_duplicates(["lidx", "hidx"], keep="first")


# ═══════════════════════════ işlem kurulumu + çözüm ═══════════════════════════

def setup_trades(sig: pd.DataFrame, bars: Bars, p: Path1, sl_mode: str, tp_mode: str, hold: int,
                 zone: str = "altin") -> pd.DataFrame:
    if sig.empty:
        return sig.assign(entry=[], sl=[], tp=[], e1=[], end=[])
    s = sig.copy()
    side = s.side.values
    t = s.t.values
    e1 = bars.last[t] + 1
    ok = e1 < p.n
    s, side, t, e1 = s[ok], side[ok], t[ok], e1[ok]
    entry = np.where(side > 0, p.o[e1] + p.spr[e1], p.o[e1])
    H, L, R, atr = s.H.values, s.L.values, s.R.values, s.atr.values
    buf = SL_BUF * atr * side
    if sl_mode == "L":
        sl = L - buf
    elif sl_mode == "inv":
        sl = H - side * ZONES[zone][1] * R - buf
    elif sl_mode == "pat":
        sl = s.plow.values - buf
    else:
        raise ValueError(sl_mode)
    risk = side * (entry - sl)
    if tp_mode == "H":
        tp = H
    elif tp_mode == "x1272":
        tp = H + side * 0.272 * R
    elif tp_mode == "x1618":
        tp = H + side * 0.618 * R
    elif tp_mode == "2R":
        tp = entry + side * 2 * risk
    else:
        raise ValueError(tp_mode)
    reward = side * (tp - entry)
    sprv = p.spr[e1]
    ok = (reward > 0) & (risk >= MIN_RISK_SPR * sprv)
    endbar = t + 1 + hold
    end = np.where(endbar < len(bars.first), bars.first[np.minimum(endbar, len(bars.first) - 1)], p.n)
    s = s.assign(entry=entry, sl=sl, tp=tp, e1=e1, end=end, risk=risk, reward=reward, spr_e=sprv)
    return s[ok]


def resolve(tr: pd.DataFrame, p: Path1) -> pd.DataFrame:
    if tr.empty:
        return tr.assign(exit=[], xidx=[], reason=[], Rg=[], R=[], R15=[])
    m = len(tr)
    side = tr.side.values.astype(np.int32)
    start = tr.e1.values.astype(np.int64)
    end = tr.end.values.astype(np.int64)
    sl = tr.sl.values.astype(float)
    tp = tr.tp.values.astype(float)
    oe, ox = np.zeros(m), np.zeros(m)
    oi = np.zeros(m, np.int64)
    orr = np.zeros(m, np.int32)
    _lib.resolve(p.n, p.o, p.h, p.l, p.c, p.spr, m, side, start, end, sl, tp, oe, ox, oi, orr)
    risk = tr.risk.values
    rg = side * (ox - oe) / risk
    rolls = p.rollday[oi] - p.rollday[start]
    fin = rolls * FIN_PER_NIGHT * oe / risk
    R = rg - fin
    R15 = R - 0.5 * tr.spr_e.values / risk
    loc = p.local[start]
    out = tr.assign(exit=ox, xidx=oi, reason=orr, Rg=rg, R=R, R15=R15, rolls=rolls,
                    ent_local=loc)
    return annotate(out)


SESSIONS = [("ASYA", 18 * 60, 27 * 60), ("AVRUPA", 3 * 60, 9 * 60 + 30), ("NY", 9 * 60 + 30, 16 * 60),
            ("KAPANIS_SONRASI", 16 * 60, 18 * 60)]


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    dt = pd.to_datetime(df.ent_local.values, unit="s")
    mins = dt.hour * 60 + dt.minute
    ses = np.where((mins >= 18 * 60) | (mins < 3 * 60), "ASYA",
          np.where(mins < 9 * 60 + 30, "AVRUPA", np.where(mins < 16 * 60, "NY", "KAPANIS_SONRASI")))
    d = dt.values.astype("datetime64[D]")
    per = np.where(d <= KESIF_END, "KESIF", np.where(d <= TEST_END, "TEST", "KOR"))
    return df.assign(date=d, hour=dt.hour.values, dow=dt.dayofweek.values, year=dt.year.values, session=ses,
                     period=per)


def single_position(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.sort_values("e1")
    keep = np.zeros(len(d), np.int32)
    _lib.single_pos(len(d), d.e1.values.astype(np.int64), d.xidx.values.astype(np.int64), keep)
    return d[keep.astype(bool)]


# ═══════════════════════════ plasebo (K4) ═══════════════════════════

def placebo(tr: pd.DataFrame, bars: Bars, p: Path1, hold: int, draws: int, seed: int = 7) -> pd.DataFrame:
    """Aynı TF, yön, NY saati ve yıl içinde rastgele bar kapanışı; aynı braket (ATR katı)."""
    if tr.empty:
        return tr
    rng = np.random.default_rng(seed)
    bl = bars.last + 1
    okb = (bl < p.n) & (np.arange(len(bars.last)) > K_WIN + M_WIN)
    loc = p.local[np.minimum(bl, p.n - 1)]
    dtb = pd.to_datetime(loc, unit="s")
    key_b = dtb.year.values * 100 + dtb.hour.values
    pools: dict[int, np.ndarray] = {}
    idx_all = np.flatnonzero(okb)
    kb = key_b[idx_all]
    order = np.argsort(kb, kind="stable")
    kbs = kb[order]
    uk, st_ = np.unique(kbs, return_index=True)
    en_ = np.r_[st_[1:], len(kbs)]
    for k_, a_, b_ in zip(uk, st_, en_):
        pools[int(k_)] = idx_all[order[a_:b_]]
    key_t = tr.year.values * 100 + tr.hour.values
    sl_atr = tr.risk.values / tr.atr.values
    tp_atr = tr.reward.values / tr.atr.values
    rows = []
    for dr in range(draws):
        tb = np.empty(len(tr), np.int64)
        for i, k_ in enumerate(key_t):
            pool = pools.get(int(k_))
            tb[i] = rng.choice(pool) if pool is not None and len(pool) else -1
        ok = tb >= 0
        tbo = tb[ok]
        side = tr.side.values[ok]
        e1 = bars.last[tbo] + 1
        entry = np.where(side > 0, p.o[e1] + p.spr[e1], p.o[e1])
        atr = bars.atr[tbo]
        risk = sl_atr[ok] * atr
        reward = tp_atr[ok] * atr
        endbar = tbo + 1 + hold
        end = np.where(endbar < len(bars.first), bars.first[np.minimum(endbar, len(bars.first) - 1)], p.n)
        pt = pd.DataFrame({"t": tbo, "side": side, "e1": e1, "end": end, "entry": entry,
                           "sl": entry - side * risk, "tp": entry + side * reward, "risk": risk,
                           "reward": reward, "spr_e": p.spr[e1], "atr": atr, "draw": dr,
                           "src_row": np.flatnonzero(ok)})
        rows.append(pt[pt.risk >= MIN_RISK_SPR * pt.spr_e])
    return resolve(pd.concat(rows, ignore_index=True), p)


# ═══════════════════════════ istatistik ═══════════════════════════

def day_stats(R: np.ndarray, dates: np.ndarray) -> tuple[float, float, int]:
    """Gün-kümeli t: ortalama / küme SE. Dönüş (ort, t, gün sayısı)."""
    n = len(R)
    if n < 2:
        return (float(R.mean()) if n else np.nan, np.nan, n)
    s = pd.Series(R).groupby(dates).agg(["sum", "count"])
    mu = R.mean()
    g = len(s)
    resid = s["sum"].values - mu * s["count"].values
    se = np.sqrt((resid ** 2).sum() * g / max(g - 1, 1)) / n
    return float(mu), float(mu / se) if se > 0 else np.nan, g


def boot_p(R: np.ndarray, dates: np.ndarray, B: int = 2000, seed: int = 1) -> float:
    if len(R) < 5:
        return np.nan
    s = pd.Series(R).groupby(dates).agg(["sum", "count"])
    sm, ct = s["sum"].values, s["count"].values
    rng = np.random.default_rng(seed)
    ix = rng.integers(0, len(sm), (B, len(sm)))
    mu = sm[ix].sum(1) / ct[ix].sum(1)
    return float((mu > 0).mean())


def summarize(df: pd.DataFrame, col: str = "R", boot: bool = False) -> dict:
    if df.empty:
        return {"n": 0}
    R = df[col].values
    mu, t, g = day_stats(R, df.date.values)
    out = {"n": len(df), "gun": g, "ortR": round(mu, 4), "t": round(t, 2) if t == t else None,
           "medyan": round(float(np.median(R)), 3), "tp_oran": round(float((df.reason == 1).mean()), 3),
           "sl_oran": round(float((df.reason == 0).mean()), 3),
           "basabas": round(float((df.risk / (df.risk + df.reward)).mean()), 3),
           "topR": round(float(R.sum()), 1)}
    if boot:
        out["P"] = round(boot_p(R, df.date.values), 3)
    return out


def prefix_test(bars: Bars, side: int, cut: int, seed: int = 3) -> bool:
    """Önek testi: cut sonrası barlar bozulunca cut'a kadarki aday satırlar aynı kalmalı."""
    a = detect(bars, side)
    rng = np.random.default_rng(seed)
    b2 = Bars(bars.o.copy(), bars.h.copy(), bars.l.copy(), bars.c.copy(), bars.atr.copy(), bars.first, bars.last, bars.tf)
    n = len(b2.o) - cut
    noise = rng.normal(0, bars.atr[cut] * 5, n)
    b2.o[cut:] += noise
    b2.c[cut:] -= noise
    b2.h[cut:] = np.maximum(b2.o[cut:], b2.c[cut:]) + np.abs(noise)
    b2.l[cut:] = np.minimum(b2.o[cut:], b2.c[cut:]) - np.abs(noise)
    b2.atr = atr_wilder(b2.h, b2.l, b2.c)
    b = detect(b2, side)
    a, b = a[a.t < cut].reset_index(drop=True), b[b.t < cut].reset_index(drop=True)
    return a.shape == b.shape and np.allclose(a.select_dtypes("number").values, b.select_dtypes("number").values)


TFS_NDX = {"1m": (1, 0), "5m": (5, 0), "15m": (15, 0), "30m": (30, 0), "1h": (60, 0), "4h": (240, 120)}
