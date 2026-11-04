"""PROTOCOL.md §2 — 10 ex-ante özellik. Her şey sinyal barı s KAPANIŞINDA bilinen veriden.
d: mech.prep_h1 çıktısı (+ 'v' hacim sütunu, yoksa NaN). Dönüş: ham sürekli değerler + bayraklar (F1..F10)."""
from __future__ import annotations
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NY = "America/New_York"
FEATS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]
NAMES = {"F1": "H1_SIKISMA", "F2": "D1_SIKISMA", "F3": "KAPANIS_TEYIDI", "F4": "HACIM", "F5": "D1_TREND",
         "F6": "D1_DONCHIAN20", "F7": "ZIRVE_250", "F8": "SEANS", "F9": "MOMENTUM6", "F10": "VIX20"}


def _d1_frame(d: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """mech.prep_h1 ile aynı D1 tanımı; her H1 barı için son KAPANMIŞ D1 indeksi (−1 = yok)."""
    end = d.ts + pd.Timedelta(hours=1)
    D = d.groupby("day").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"), end=("ts", "last"), n=("ts", "size"))
    D["end"] = D["end"] + pd.Timedelta(hours=1)
    D = D[D.n >= 4].sort_values("end").reset_index()
    k = np.searchsorted(D["end"].values, end.values, side="right") - 1
    return D, k


def raw_features(d: pd.DataFrame, vix: pd.Series | None) -> pd.DataFrame:
    h, l, c = (d[x].to_numpy() for x in "hlc")
    seg = d.seg.to_numpy(); n = len(d)
    out = pd.DataFrame(index=d.index)
    # F1 — R4 ile aynı sıkışma tanımı (s−1 barında)
    cs = pd.Series(c)
    mid, sd = cs.rolling(20).mean(), cs.rolling(20).std(ddof=0)
    bw = 4 * sd / mid
    q = bw.shift(1).rolling(120).quantile(0.2)
    out["bw_prev"] = bw.shift(1).to_numpy(); out["bw_q20"] = q.to_numpy()
    out["F1"] = (bw.shift(1) <= q).to_numpy()
    # D1 tabanlı
    D, k = _d1_frame(d)
    r = (D.h - D.l).to_numpy()
    nr4 = r <= pd.Series(r).rolling(4).min().to_numpy()
    inside = (D.h.to_numpy() <= D.h.shift(1).to_numpy()) & (D.l.to_numpy() >= D.l.shift(1).to_numpy())
    dc20 = D.h.rolling(20).max().to_numpy(); dc250 = D.h.rolling(250).max().to_numpy()
    ok = k >= 0; kk = np.clip(k, 0, None)
    out["F2"] = np.where(ok, (nr4 | inside)[kk], False)
    out["d1_hh20"] = np.where(ok, dc20[kk], np.nan); out["d1_hh250"] = np.where(ok, dc250[kk], np.nan)
    out["F6"] = h >= out.d1_hh20.to_numpy()          # NaN karşılaştırma → False
    out["F7"] = h >= out.d1_hh250.to_numpy()
    # F3 — kapanışla kabul + kapanış konumu
    hh20 = pd.Series(h).rolling(20).max().shift(1).to_numpy()
    rng = h - l
    clv = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1), np.nan)
    out["clv"] = clv
    out["F3"] = (c > hh20) & (clv >= 0.6)
    # F4 — aynı UTC saatinin önceki 20 gününün medyan hacmi
    v = d["v"].to_numpy() if "v" in d.columns else np.full(n, np.nan)
    vs = pd.Series(v, index=d.index)
    med = vs.groupby(d.utc_h.to_numpy()).transform(lambda s: s.rolling(20, min_periods=10).median().shift(1))
    out["vol_ratio"] = (vs / med).to_numpy()
    out["F4"] = out.vol_ratio.to_numpy() >= 1.5
    # F5
    out["F5"] = d.trend_up.to_numpy().astype(bool)
    # F8 — UTC 07–15 bar başlangıcı
    uh = d.utc_h.to_numpy(); out["F8"] = (uh >= 7) & (uh <= 15)
    # F9 — 6 bar momentum / ATR (aynı segment)
    c6 = pd.Series(c).shift(6).to_numpy(); seg6 = pd.Series(seg).shift(6).to_numpy()
    mom = np.where(seg6 == seg, (c - c6) / d.atr.to_numpy(), np.nan)
    out["mom6"] = mom
    # F10 — karar anının NY gününden ÖNCEKİ son VIX kapanışı
    if vix is not None:
        nyd = (d.ts + pd.Timedelta(hours=1)).dt.tz_convert(NY).dt.strftime("%Y-%m-%d").to_numpy()
        vv = vix.dropna().sort_index()
        idx = np.searchsorted(vv.index.to_numpy(), nyd, side="left") - 1   # tarih < NY günü
        out["vix_prev"] = np.where(idx >= 0, vv.to_numpy()[np.clip(idx, 0, None)], np.nan)
    else:
        out["vix_prev"] = np.nan
    out["F10"] = out.vix_prev.to_numpy() >= 20
    return out


def load_vix() -> pd.Series:
    m = pd.read_csv(os.path.join(HERE, "data", "macro_yf.csv"), index_col=0)
    return m["VIX"]


def add_f9(fe: pd.DataFrame, thr: float) -> pd.DataFrame:
    fe = fe.copy(); fe["F9"] = fe.mom6.to_numpy() >= thr
    return fe
