"""Yedi kolun DONDURULMUŞ olay üreticileri + plasebo geometri kurucuları (prereg.md §3, §7).

Her kol: events() → DataFrame[ent, dir, sl_d, tp_d, end, sig, dec, R_den]
          geom(ent, dir) → aynı sütunlar (plasebo: rastgele zamanda aynı tanım), geçersizse sl_d=NaN.
ent = giriş dakikası (epoch, o dakikanın açılışında gir); dec = karar anı (sinyal barı kapanışı); sig = sinyal kapanışı.
R_den = R paydası (dondurulmuş tanım; genelde sl_d; QB'de ATR1h, bot biçiminde sl_d = 2×ATR1h).
"""
from __future__ import annotations

import pickle
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

import lib_st as L

lt = L.lt
R5 = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021")
RS = Path("/Users/melihcanodacioglu/Desktop/panel/research/btc_scalp_20261021")
DAYM = 1440


def _df(ent, dirn, sl, tp, end, sig, dec, rden=None):
    ent = np.asarray(ent, np.int64)
    sl = np.asarray(sl, float)
    out = pd.DataFrame({"ent": ent, "dir": np.asarray(dirn, np.int64) * np.ones(len(ent), np.int64),
                        "sl_d": sl, "tp_d": np.asarray(tp, float) * np.ones(len(ent)),
                        "end": np.asarray(end, np.int64), "sig": np.asarray(sig, float), "dec": np.asarray(dec, np.int64)})
    out["R_den"] = sl if rden is None else np.asarray(rden, float)
    return out


# ═════════════════════════ ortak çerçeveler ═════════════════════════
@lru_cache(None)
def frames():
    D = lt.load_tf("1d", DAYM)
    c = D["close"].to_numpy()
    D["ema200"] = lt.ema(c, 200)
    D["cmax10"] = pd.Series(c).rolling(10).max().to_numpy()
    H4 = lt.load_tf("4h", 240)
    H4["hh20"] = lt.prev_max(H4["high"].to_numpy(), 20)
    a = lt.asof(H4["dec"].to_numpy(), D, ["close", "ema200"])
    H4["d_up"] = (a["close"] > a["ema200"]).to_numpy()
    return D, H4


_E = None


def engine() -> L.Engine:
    global _E
    if _E is None:
        _E = L.Engine()
    return _E


def sig_close(t: np.ndarray) -> np.ndarray:
    E = engine()
    j = E.last_row_before(np.asarray(t, np.int64))
    return E.C[np.maximum(j, 0)]


def open_at(t: np.ndarray) -> np.ndarray:
    E = engine()
    k = np.minimum(E.row_at_or_after(np.asarray(t, np.int64)), E.N - 1)
    return E.O[k]


# ═════════════════════════ S1 CORE (BTC-T03 H4D20-T-L) ═════════════════════════
def core_events() -> pd.DataFrame:
    D, H4 = frames()
    Hv = H4[~H4["excl"] & H4["atr"].notna()]
    s = Hv[(Hv["close"] >= Hv["hh20"]) & Hv["d_up"]]
    dec = s["dec"].to_numpy(np.int64)
    atr = s["atr"].to_numpy()
    return _df(dec, 1, 2 * atr, 4 * atr, dec + 30 * 240, s["close"].to_numpy(), dec)


def core_geom(ent, dirn):
    D, H4 = frames()
    m = H4.set_index("dec")
    ent = np.asarray(ent, np.int64)
    a = m["atr"].reindex(ent).to_numpy()
    ex = m["excl"].reindex(ent).to_numpy()
    a = np.where(ex == True, np.nan, a)  # noqa: E712
    return _df(ent, dirn, 2 * a, 4 * a, ent + 30 * 240, m["close"].reindex(ent).to_numpy(), ent)


# ═════════════════════════ S2 MAX10 (BTC-T02 MX10-L-1d) ═════════════════════════
def max10_events() -> pd.DataFrame:
    D, _ = frames()
    Dm = D[~D["excl"] & D["atr"].notna()]
    s = Dm[Dm["close"] >= Dm["cmax10"]]
    dec = s["dec"].to_numpy(np.int64)
    return _df(dec, 1, 2 * s["atr"].to_numpy(), np.nan, dec + DAYM, s["close"].to_numpy(), dec)


def max10_geom(ent, dirn):
    D, _ = frames()
    m = D.set_index("dec")
    ent = np.asarray(ent, np.int64)
    a = m["atr"].reindex(ent).to_numpy()
    ex = m["excl"].reindex(ent).to_numpy()
    a = np.where(ex == True, np.nan, a)  # noqa: E712
    return _df(ent, dirn, 2 * a, np.nan, ent + DAYM, m["close"].reindex(ent).to_numpy(), ent)


# ═════════════════════════ S3 QB (BTC-M02) ═════════════════════════
@lru_cache(None)
def atr1h_simple():
    h1 = pd.read_parquet(R5 / "data" / "btc_1h.parquet", columns=["ts", "high", "low", "close"])
    s = lt.tmin(h1["ts"])
    pc = h1["close"].shift(1)
    tr = np.maximum(h1["high"] - h1["low"], np.maximum((h1["high"] - pc).abs(), (h1["low"] - pc).abs()))
    atr = tr.rolling(14).mean().to_numpy()
    return pd.Series(atr, index=s)  # index = bar başı (epoch dk)


def atr1h_at(t: np.ndarray) -> np.ndarray:
    """karar anı t için son KAPANMIŞ 1h barın ATR14'ü (bar başı = (t//60 − 1)·60)."""
    ser = atr1h_simple()
    t = np.asarray(t, np.int64)
    return ser.reindex((t // 60 - 1) * 60).to_numpy()


def rollovers_utc_day() -> pd.Series:
    """UTC günü → o gün içindeki NY 17:00 rollover dakikası (epoch)."""
    E = engine()
    ro = E.RO
    return pd.Series(ro, index=ro // DAYM)


def qb_events() -> pd.DataFrame:
    ro = rollovers_utc_day()
    d0, d1 = L.em("2021-06-01") // DAYM, L.em("2026-10-21") // DAYM
    days = np.arange(d0, d1)
    r = ro.reindex(days).to_numpy()
    ok = np.isfinite(r)
    days, r = days[ok], r[ok].astype(np.int64)
    ent = r + 1
    end = days * DAYM + 23 * 60
    a = atr1h_at(ent)
    return _df(ent, 1, 2 * a, np.nan, end, sig_close(ent), ent, rden=2 * a).assign(atr1h=a)


def qb_geom(ent, dirn, dur):
    ent = np.asarray(ent, np.int64)
    a = atr1h_at(ent)
    return _df(ent, dirn, 2 * a, np.nan, ent + np.asarray(dur, np.int64), sig_close(ent), ent).assign(atr1h=a)


# ═════════════════════════ S4 X04 (QQQ açılış boşluğu tersi) ═════════════════════════
@lru_cache(None)
def dvol20_prevday():
    d1 = pd.read_parquet(R5 / "data" / "btc_1d.parquet", columns=["ts", "close"])
    r = np.log(d1["close"]).diff()
    dv = r.rolling(20).std().to_numpy()
    day = lt.tmin(d1["ts"]) // DAYM
    return pd.Series(dv, index=day)  # gün D'nin kapanışına kadar


def dvol_known(t):
    t = np.asarray(t, np.int64)
    return dvol20_prevday().reindex(t // DAYM - 1).to_numpy()


def next_ro(t):
    E = engine()
    return E.RO[np.searchsorted(E.RO, np.asarray(t, np.int64), side="right")]


def x04_events() -> pd.DataFrame:
    macro = pd.read_parquet(R5 / "data" / "macro_daily.parquet").sort_values("date").reset_index(drop=True)
    sel = macro["qqq_close"].notna() & macro["qqq_open"].notna()
    mq = macro.loc[sel].reset_index(drop=True)
    prev_close = macro["qqq_close"].ffill().shift(1).loc[sel].to_numpy()
    gap = np.log(mq["qqq_open"].to_numpy() / prev_close)
    rq = np.log(macro["qqq_close"].ffill()).diff()
    sig_prev = rq.rolling(20).std().shift(1).loc[sel].to_numpy()
    gz = gap / sig_prev
    t10 = pd.DatetimeIndex([pd.Timestamp(d.year, d.month, d.day, 10, 0, tz="America/New_York").tz_convert("UTC")
                            for d in mq["date"]])
    dec = lt.tmin(pd.Series(t10))
    keep = (dec > L.T0M + 30 * DAYM) & (dec < L.em("2026-10-20 12:00"))
    dec, gz = dec[keep], gz[keep]
    dv = dvol_known(dec)
    ok = np.isfinite(dv) & np.isfinite(gz) & (np.abs(gz) > 0.5)
    dec, gz, dv = dec[ok], gz[ok], dv[ok]
    dirn = -np.sign(gz).astype(np.int64)
    end = next_ro(dec) - 2
    return _df(dec, dirn, dv * open_at(dec), np.nan, end, sig_close(dec), dec).assign(gz=gz)


def x04_geom(ent, dirn):
    ent = np.asarray(ent, np.int64)
    dv = dvol_known(ent)
    return _df(ent, dirn, dv * open_at(ent), np.nan, next_ro(ent) - 2, sig_close(ent), ent)


# ═════════════════════════ S5 CAPREV-RV D0 (BTC-S02 post-hoc) ═════════════════════════
@lru_cache(None)
def daily_flags() -> pd.DataFrame:
    d = pd.read_parquet(R5 / "data" / "btc_1d.parquet", columns=["ts", "open", "high", "low", "close"])
    d["day"] = lt.tmin(d["ts"]) // DAYM
    d = d.set_index("day")
    r = d.close.pct_change()
    d["sig20"] = r.shift(1).rolling(20).std()
    d["r1"] = r.shift(1)
    d["r5"] = d.close.shift(1) / d.close.shift(6) - 1
    d["pdl"] = d.low.shift(1)
    d["pdh"] = d.high.shift(1)
    s30 = r.shift(1).rolling(30).std()
    med = s30.rolling(365, min_periods=120).median()
    d["rvhi"] = np.where(med.isna() | s30.isna(), np.nan, (s30 > med).astype(float))
    st = ((d.r1 <= -1.0 * d.sig20) | (d.r5 <= -1.0 * d.sig20 * np.sqrt(5))) & d.sig20.notna()
    d["stress1"] = st
    return d


def caprev_events() -> pd.DataFrame:
    d = daily_flags()
    h1 = pd.read_parquet(R5 / "data" / "btc_1h.parquet", columns=["ts", "close"])
    s = lt.tmin(h1["ts"])
    hh = pd.DataFrame({"s": s, "c": h1["close"].to_numpy()})
    hh["day"] = hh.s // DAYM
    hh["mod"] = hh.s % DAYM
    hh = hh[hh["mod"] <= 19 * 60].join(d[["pdl"]], on="day")
    trig = hh[hh.c < hh.pdl].groupby("day").head(1).set_index("day")
    mask = d.stress1 & (d.rvhi == 1.0)
    days = mask[mask].index
    t = trig.loc[trig.index.intersection(days)]
    dec = (t.s + 60).to_numpy(np.int64)
    sg = d.sig20.reindex(dec // DAYM).to_numpy()
    return _df(dec, 1, sg * open_at(dec), np.nan, (dec // DAYM + 1) * DAYM, t.c.to_numpy(), dec)


def caprev_geom(ent, dirn):
    d = daily_flags()
    ent = np.asarray(ent, np.int64)
    sg = d.sig20.reindex(ent // DAYM).to_numpy()
    return _df(ent, dirn, sg * open_at(ent), np.nan, (ent // DAYM + 1) * DAYM, sig_close(ent), ent)


# ═════════════════════════ S6/S7 scalp kolları (dense ızgara) ═════════════════════════
@lru_cache(None)
def scalp_grid():
    """OF ailesinin geçerlilik maskesi (entry_ok), rollover tavanı hcap, ATR5m(bp) — dense indeks."""
    sys.path.insert(0, str(RS / "fam_orderflow"))
    import ofl  # noqa: E402
    df = ofl.load_frame()
    g = ofl.build_grid(df)
    del df
    fc_next, blocked = ofl.rollover_cap()
    valid = ofl.valid_entries(g)
    hcap = fc_next - np.arange(ofl.N)
    atr5 = ofl.lib.atr_5m(g)
    entry_ok = valid & ~blocked & (hcap >= 5) & ~np.isnan(atr5)
    atr5bp = atr5 / g["open"] * 1e4
    return dict(entry_ok=entry_ok, hcap=hcap, atr5bp=atr5bp, open=g["open"], N=ofl.N)


def _scalp(e_idx, dirn, rho, H):
    G = scalp_grid()
    e_idx = np.asarray(e_idx, np.int64)
    ok = (e_idx >= 0) & (e_idx < G["N"])
    ec = np.clip(e_idx, 0, G["N"] - 1)
    ok &= G["entry_ok"][ec]
    slbp = np.maximum(19.0, 1.1 * G["atr5bp"][ec])
    p0 = G["open"][ec]
    sl = np.where(ok, slbp * 1e-4 * p0, np.nan)
    Hp = np.minimum(H, G["hcap"][ec])
    ent = L.T0M + e_idx
    return _df(ent, dirn, sl, rho * sl, ent + Hp, sig_close(ent), ent)


def of02_events() -> pd.DataFrame:
    z = np.load(RS / "fam_orderflow" / "results" / "events.npz")
    t, dflow = z["OF02_W15_th5__t"], z["OF02_W15_th5__d"]
    return _scalp(t + 1, -np.sign(dflow).astype(np.int64), 1.0, 15)


def of02_geom(ent, dirn):
    return _scalp(np.asarray(ent, np.int64) - L.T0M, dirn, 1.0, 15)


@lru_cache(None)
def dv_valid():
    z = np.load(RS / "fam_turev" / "cache" / "out_H60.npz")
    return z["valid"]


def dv04c_events() -> pd.DataFrame:
    S = pickle.load(open(RS / "fam_turev" / "cache" / "signals.pkl", "rb"))
    t = [s for s in S if s["hid"] == "DV04c-U" and s["par"] == "b3.0"][0]["t"]
    e = np.asarray(t, np.int64) + 1
    v = dv_valid()
    e = e[v[np.clip(e, 0, len(v) - 1)]]
    return _scalp(e, 1, 2.0, 60)


def dv04c_geom(ent, dirn):
    return _scalp(np.asarray(ent, np.int64) - L.T0M, dirn, 2.0, 60)


SLEEVES = {
    "S1_CORE": (core_events, core_geom),
    "S2_MAX10": (max10_events, max10_geom),
    "S3_QB": (qb_events, qb_geom),
    "S4_X04": (x04_events, x04_geom),
    "S5_CAPREV": (caprev_events, caprev_geom),
    "S6_OF02": (of02_events, of02_geom),
    "S7_DV04c": (dv04c_events, dv04c_geom),
}
POSTHOC = {"S5_CAPREV", "S6_OF02", "S7_DV04c"}
