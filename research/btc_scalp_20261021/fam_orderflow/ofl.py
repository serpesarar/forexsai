"""fam_orderflow ortak modül: ızgara, özellikler, geometri/çıkış motoru.

Fiyat yolu = Binance spot 1m (btc_scalp_1m.parquet spot_*). İlk-dokunuş motoru feasibility/lib.py'den
(kaba-döngü doğrulamalı: 0/18.000 uyuşmazlık). Tüm dizinler dakika ızgarası m (2021-06-01 00:00 UTC'den).
"""
from __future__ import annotations

import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "feasibility"))
import lib  # noqa: E402

DATA = os.path.join(HERE, "..", "data")
RES = os.path.join(HERE, "results")
N = lib.N
T0 = lib.T0
LW = 60          # izleme penceresi (dk)
KLEV = 7         # 2^6=64 >= 60
ZWIN = 43200     # 30 gün
ZMIN = 14400     # min 10 gün

SEG = {
    "DISC": (lib.tmin("2021-06-01"), lib.tmin("2024-01-01")),
    "OOS": (lib.tmin("2024-01-11"), lib.tmin("2025-07-01")),
    "BLIND": (lib.tmin("2025-07-01"), lib.tmin("2026-10-21")),
}
SL_RULES = {"S1": (19.0, 1.1), "S2": (28.0, 2.0)}
RHOS = [1.0, 1.5, 2.0]
HS = [15, 30, 60]
GEOMS = [(s, r, h) for s in SL_RULES for r in RHOS for h in HS]
COSTS = {"PEP": 1.85, "STRESS": 2.775, "BMAKER": 4.0, "BTAKER": 10.0}  # FIX15 ayrı (15/fiyat)


def gname(g):
    s, r, h = g
    return f"{s}_r{r:g}_H{h}"


def load_frame(cols=None) -> pd.DataFrame:
    base = ["ts", "spot_open", "spot_high", "spot_low", "spot_close", "spot_volume", "spot_taker_buy_base",
            "perp_open", "perp_high", "perp_low", "perp_close", "perp_volume", "perp_taker_buy_base", "perp_trades",
            "perp_zero_vol", "spot_missing", "spot_zero_vol"]
    df = pd.read_parquet(os.path.join(DATA, "btc_scalp_1m.parquet"), columns=base + (cols or []))
    assert len(df) == N and (df["ts"].iloc[0] == T0)
    return df


def build_grid(df: pd.DataFrame) -> dict:
    g = {c: df[f"spot_{c}"].to_numpy().astype(float).copy() for c in ["open", "high", "low", "close"]}
    bad = np.zeros(N, dtype=bool)
    bad[lib.tmin("2023-03-24 11:28"):lib.tmin("2023-03-24 14:00")] = True
    miss = np.isnan(g["close"])
    d = np.diff(np.concatenate([[0], miss.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    for a, b in zip(st, en):
        if b - a >= 5:
            bad[a:b] = True
    g["bad"] = bad
    for c in ["open", "high", "low", "close"]:
        g[c][bad] = np.nan
    g["close_ff"] = pd.Series(g["close"]).ffill().to_numpy()
    return g


def rollover_cap() -> tuple[np.ndarray, np.ndarray]:
    """Her m için: fc_next(m) = m'den büyük ilk zorunlu kapanış dakikası (RO−2); blocked(m) = m ∈ [RO−2, RO+3)."""
    ny = ZoneInfo("America/New_York")
    days = pd.date_range("2021-05-31", "2026-10-22", freq="D")
    ros = []
    for d in days:
        ro = pd.Timestamp(d.year, d.month, d.day, 17, 0, tzinfo=ny).tz_convert("UTC")
        ros.append(int((ro - T0) / pd.Timedelta(minutes=1)))
    ros = np.array(sorted(ros))
    fc = ros - 2
    m = np.arange(N)
    j = np.searchsorted(fc, m, side="right")  # fc[j] > m
    fc_next = fc[j]
    blocked = np.zeros(N, dtype=bool)
    for f in fc:
        a, b = max(f, 0), min(f + 5, N)
        if a < b:
            blocked[a:b] = True
    return fc_next, blocked


def valid_entries(g: dict) -> np.ndarray:
    o = g["open"]
    ok = ~np.isnan(o)
    ok[1:] &= ~np.isnan(g["close"][:-1])
    ok[0] = False
    bcs = np.concatenate([[0], np.cumsum(g["bad"])])
    e = np.arange(N)
    hi = np.minimum(e + LW, N)
    ok &= (bcs[hi] - bcs[e]) == 0
    ok &= e + LW <= N
    return ok


def zpast(x: np.ndarray, win: int = ZWIN, minp: int = ZMIN) -> np.ndarray:
    s = pd.Series(x)
    mu = s.rolling(win, min_periods=minp).mean().shift(1)
    sd = s.rolling(win, min_periods=minp).std().shift(1)
    return ((s - mu) / sd).to_numpy()


def wsum(x: np.ndarray, w: int) -> np.ndarray:
    return pd.Series(x).rolling(w, min_periods=w).sum().to_numpy()


def features(df: pd.DataFrame) -> dict:
    """Karar dakikası t'de (bar kapanışında) bilinen özellikler; dizin = t."""
    f = {}
    vp = df["perp_volume"].to_numpy().astype(float)
    dp = 2 * df["perp_taker_buy_base"].to_numpy().astype(float) - vp
    vs = df["spot_volume"].to_numpy().astype(float)
    ds = 2 * df["spot_taker_buy_base"].to_numpy().astype(float) - vs
    trp = df["perp_trades"].to_numpy().astype(float)
    pz = df["perp_zero_vol"].to_numpy().astype(float)
    sm = (df["spot_missing"].to_numpy() + df["spot_zero_vol"].to_numpy()).astype(float)
    sm = np.where(np.isnan(df["spot_close"].to_numpy()), 1.0, sm)
    pc = df["perp_close"].to_numpy().astype(float)
    po = df["perp_open"].to_numpy().astype(float)
    sc = pd.Series(df["spot_close"].to_numpy().astype(float)).ffill().to_numpy()
    for w in [1, 5, 15, 30, 60]:
        f[f"pbad{w}"] = wsum(pz, w) > 0
        f[f"sbad{w}"] = wsum(sm, w) > 0
    for w in [1, 5, 15]:
        Dp = wsum(dp, w)
        f[f"zDp{w}"] = zpast(Dp)
        Ds = wsum(np.nan_to_num(ds), w)
        f[f"zDs{w}"] = zpast(Ds)
        r = np.log(sc) - np.log(np.concatenate([np.full(w, np.nan), sc[:-w]]))
        f[f"zr{w}"] = zpast(r)
    for w in [1, 5]:
        f[f"zlv{w}"] = zpast(np.log(np.maximum(wsum(vp, w), 1e-9)))
        f[f"zlt{w}"] = zpast(np.log(np.maximum(wsum(trp, w), 1.0)))
        po_w = np.concatenate([np.full(w - 1, np.nan), po[: N - (w - 1)]]) if w > 1 else po
        f[f"dir{w}"] = np.sign(pc - po_w)
    cvd = np.cumsum(np.nan_to_num(dp))
    sd_d = pd.Series(dp).rolling(1440, min_periods=720).std().shift(1).to_numpy()
    lr = np.log(pc) - np.log(np.concatenate([[np.nan], pc[:-1]]))
    sd_r = pd.Series(lr).rolling(1440, min_periods=720).std().shift(1).to_numpy()
    for n in [30, 60]:
        f[f"pmax{n}"] = pd.Series(pc).rolling(n, min_periods=n).max().shift(1).to_numpy()
        f[f"pmin{n}"] = pd.Series(pc).rolling(n, min_periods=n).min().shift(1).to_numpy()
        f[f"cmax{n}"] = pd.Series(cvd).rolling(n, min_periods=n).max().shift(1).to_numpy()
        f[f"cmin{n}"] = pd.Series(cvd).rolling(n, min_periods=n).min().shift(1).to_numpy()
        f[f"sdc{n}"] = sd_d * np.sqrt(n)
        f[f"sdp{n}"] = sd_r * np.sqrt(n) * pc
    f["cvd"] = cvd
    f["pc"] = pc
    f["minute"] = (np.arange(N) % 60)
    return f


def cvd_rel(f: dict, n: int):
    """CVD karşılaştırmasını kümülatif toplamdan bağımsız yap: cvd − cmax (fark tabanlı, öneke duyarsız)."""
    return f["cvd"] - f[f"cmax{n}"], f["cvd"] - f[f"cmin{n}"]


# ---------------------------------------------------------------- olay üretimi

def refractory(cand: np.ndarray, gap: int = 30) -> np.ndarray:
    out = []
    last = -10 ** 9
    for t in cand:
        if t - last >= gap:
            out.append(t)
            last = t
    return np.array(out, dtype=np.int64)


def events_from_dir(dirarr: np.ndarray, cond: np.ndarray, entry_ok: np.ndarray, gap: int = 30):
    """dirarr: olay 'akış yönü' (+1/−1) karar dakikası t'de; cond: koşul. Dönüş: t (karar), side (+1/−1)."""
    t_all = np.arange(N - 1)
    okk = cond[:-1] & entry_ok[1:] & (dirarr[:-1] != 0) & ~np.isnan(dirarr[:-1])
    ts, sides = [], []
    for s in (1, -1):
        cand = t_all[okk & (dirarr[:-1] == s)]
        ev = refractory(cand, gap)
        ts.append(ev)
        sides.append(np.full(len(ev), s, dtype=np.int8))
    t = np.concatenate(ts)
    sd = np.concatenate(sides)
    o = np.argsort(t, kind="stable")
    return t[o], sd[o]


# ---------------------------------------------------------------- geometri motoru

class Engine:
    def __init__(self, g: dict, atr5: np.ndarray, entry_ok: np.ndarray, hcap: np.ndarray, slip_thr: float):
        self.g = g
        self.p0 = g["open"]
        self.atr5bp = atr5 / self.p0 * 1e4
        self.entry_ok = entry_ok
        self.hcap = hcap  # izin verilen azami H (rollover)
        self.E = np.where(entry_ok)[0]
        cff = g["close_ff"]
        ar = np.abs(np.diff(np.log(cff), prepend=np.nan)) * 1e4
        self.absret = ar
        self.slip_thr = slip_thr
        self.K = {}
        MX, MN = lib.sparse_tables(g["high"], g["low"], KLEV)
        E = self.E
        p0 = self.p0[E]
        for sname, (flo, mult) in SL_RULES.items():
            sl = np.maximum(flo, mult * self.atr5bp[E])
            self.K[(sname, "sl")] = sl
            for side in (1, -1):
                lvl = p0 * (1 - side * sl / 1e4)
                self.K[(sname, side, "ksl")] = lib.first_hit(MN if side == 1 else MX, E, lvl, LW, side != 1).astype(np.int8)
                for r in RHOS:
                    lvl = p0 * (1 + side * r * sl / 1e4)
                    self.K[(sname, side, r)] = lib.first_hit(MX if side == 1 else MN, E, lvl, LW, side == 1).astype(np.int8)
        self.pos = np.full(N, -1, dtype=np.int64)
        self.pos[E] = np.arange(len(E))
        del MX, MN

    def outcome(self, e: np.ndarray, side: np.ndarray, geom, amb_mode: str = "sl", slip: bool = True):
        """e: giriş barları (geçerli), side ±1. Dönüş dict: ret_bp (brüt, kayma dahil), sl_bp, cls, tau, amb."""
        sname, r, H = geom
        i = self.pos[e]
        assert np.all(i >= 0)
        sl = self.K[(sname, "sl")][i]
        Hp = np.minimum(H, self.hcap[e]).astype(np.int64)
        ktp = np.empty(len(e), dtype=np.int64)
        ksl = np.empty(len(e), dtype=np.int64)
        for s in (1, -1):
            m = side == s
            ktp[m] = self.K[(sname, s, r)][i[m]]
            ksl[m] = self.K[(sname, s, "ksl")][i[m]]
        p0 = self.p0[e]
        amb = (ktp == ksl) & (ktp < Hp)
        tpf = (ktp < ksl) & (ktp < Hp)
        slf = (ksl < ktp) & (ksl < Hp)
        if amb_mode == "sl":
            slf = slf | amb
        elif amb_mode == "tp":
            tpf = tpf | amb
        elif amb_mode == "heur":
            ob = self.g["open"][np.minimum(e + ktp, N - 1)]
            tpl = p0 * (1 + side * r * sl / 1e4)
            sll = p0 * (1 - side * sl / 1e4)
            tp_closer = np.abs(ob - tpl) < np.abs(ob - sll)
            tpf = tpf | (amb & tp_closer)
            slf = slf | (amb & ~tp_closer)
        ret = np.empty(len(e))
        ret[tpf] = (r * sl)[tpf]
        hb = np.minimum(e + np.minimum(ksl, LW - 1), N - 1)
        gap = side * (self.g["open"][hb] / p0 - 1) * 1e4
        rsl = np.minimum(-sl, np.nan_to_num(gap, nan=-1e9))
        rsl = np.where(rsl < -1e8, -sl, rsl)
        if slip:
            sp = np.where(self.absret[hb] > self.slip_thr, 5.0, 1.0)
            rsl = rsl - sp
        ret[slf] = rsl[slf]
        tm = ~(tpf | slf)
        xb = e + Hp - 1
        ret[tm] = (side * (self.g["close_ff"][xb] / p0 - 1) * 1e4)[tm]
        tau = np.where(tpf, ktp + 1, np.where(slf, ksl + 1, Hp))
        cls = np.where(tpf, 1, np.where(slf, -1, 0)).astype(np.int8)
        return {"ret": ret, "sl": sl, "cls": cls, "tau": tau, "amb": amb, "p0": p0}


def net_R(o: dict, cost: str = "PEP"):
    if cost == "FIX15":
        c = 15.0 / o["p0"] * 1e4
    else:
        c = COSTS[cost]
    return (o["ret"] - c) / o["sl"], o["ret"] - c


def seg_of(e: np.ndarray) -> np.ndarray:
    s = np.full(len(e), "", dtype=object)
    for k, (a, b) in SEG.items():
        s[(e >= a) & (e < b)] = k
    return s


def year_hour(e: np.ndarray):
    ts = T0 + pd.to_timedelta(e, unit="m")
    return ts.year.to_numpy(), ts.hour.to_numpy()


def cluster_z(x: np.ndarray, day: np.ndarray):
    n = len(x)
    if n < 2:
        return np.nan, np.nan, np.nan
    m = x.mean()
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=x - m)
    se = np.sqrt((S ** 2).sum()) / n
    return m, se, (m / se if se > 0 else np.nan)


def day_boot(x: np.ndarray, day: np.ndarray, B: int = 2000, seed: int = 11):
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, weights=x)
    C = np.bincount(inv)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(u), size=(B, len(u)))
    means = S[idx].sum(1) / C[idx].sum(1)
    return float((means > 0).mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def single_position(e: np.ndarray, tau: np.ndarray) -> np.ndarray:
    o = np.argsort(e, kind="stable")
    keep = np.zeros(len(e), dtype=bool)
    free = -1
    for j in o:
        if e[j] > free:
            keep[j] = True
            free = e[j] + tau[j] - 1
    return keep
