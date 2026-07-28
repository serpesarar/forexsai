"""audit_common.py — İddia D denetimi için ortak yükleyici (bağımsız yeniden inşa).

regime_gate_10y.py'nin çıktısını körü körüne kabul etmiyoruz; aynı veriden
kendi rejim matrisimizi kuruyoruz ve her adımda sızıntıyı ayrıca test ediyoruz.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import DATA
from geometry_sweep import build_paths, outcomes

HORIZON = 24            # 24 x 1h = 24 saat
FRIC = 1.0 / 29000


def load_1h() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1h.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    pc = d["close"].shift(1)
    tr = pd.concat([d.high - d.low, (d.high - pc).abs(), (d.low - pc).abs()], axis=1).max(axis=1)
    d["atr_pct"] = (tr.ewm(alpha=1 / 14, adjust=False).mean() / d["close"]).shift(1)
    return d


def daily_feats() -> pd.DataFrame:
    d = pd.read_csv(DATA / "long_1d.csv", parse_dates=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d = d.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    c = d["close"]
    f = pd.DataFrame({"known_at": d["ts"]})
    f["d_close"] = c.shift(1)
    f["ema50"] = c.ewm(span=50, adjust=False).mean().shift(1)
    f["ema200"] = c.ewm(span=200, adjust=False).mean().shift(1)
    f["ret5d"] = (c / c.shift(5) - 1).shift(1) * 100
    f["ret20d"] = (c / c.shift(20) - 1).shift(1) * 100
    f["ret60d"] = (c / c.shift(60) - 1).shift(1) * 100
    f["dd60"] = (c / c.rolling(60).max() - 1).shift(1) * 100
    f["dd120"] = (c / c.rolling(120).max() - 1).shift(1) * 100
    lr = np.log(c / c.shift(1))
    f["rv20"] = (lr.rolling(20).std() * np.sqrt(252) * 100).shift(1)
    f["rv60"] = (lr.rolling(60).std() * np.sqrt(252) * 100).shift(1)
    # gerçekleşen vol yüzdelik dilimi — SADECE geçmiş 2 yıla göre (genişleyen değil,
    # kayan pencere; gelecek bilgisi yok)
    f["rv20_pct"] = f["rv20"].rolling(504, min_periods=120).rank(pct=True)
    f["above_ema200"] = (f.d_close > f.ema200).astype(float)
    f["above_ema50"] = (f.d_close > f.ema50).astype(float)
    f["golden"] = (f.ema50 > f.ema200).astype(float)
    f["ema200_slope"] = (f["ema200"] / f["ema200"].shift(20) - 1) * 100
    return f


def macro_feats() -> pd.DataFrame:
    m = pd.read_csv(DATA / "macro_daily.csv", parse_dates=["date"]).sort_values("date")
    m["date"] = pd.to_datetime(m["date"], utc=True)
    out = pd.DataFrame({"known_at": m["date"] + pd.Timedelta(days=1)})
    v, v3 = m["VIX_close"].values, m["VIX3M_close"].values
    out["vix"] = v
    out["vix3m"] = v3
    with np.errstate(invalid="ignore", divide="ignore"):
        out["vix_ts"] = v / v3                       # >1 = vade yapısı ters (stres)
    out["vix_ma20"] = m["VIX_close"].rolling(20).mean().values
    out["vix_rel"] = out["vix"] / out["vix_ma20"]
    hyg = m["HYG_close"]
    out["hyg_ret20"] = (hyg / hyg.shift(20) - 1).values * 100
    dxy = m["DXY_close"]
    out["dxy_ret20"] = (dxy / dxy.shift(20) - 1).values * 100
    out["us10y_chg20"] = (m["US10Y_close"] - m["US10Y_close"].shift(20)).values
    spx = m["SPX_close"]
    out["spx_above_ema200"] = (spx > spx.ewm(span=200, adjust=False).mean()).astype(float).values
    return out


def build(direction: str = "BUY"):
    """Tüm rejim özellikleri eklenmiş 1h çerçevesi + yol çıktıları."""
    d = load_1h()
    d = pd.merge_asof(d, daily_feats().sort_values("known_at"), left_on="ts",
                      right_on="known_at", direction="backward").drop(columns=["known_at"])
    d = pd.merge_asof(d, macro_feats().sort_values("known_at"), left_on="ts",
                      right_on="known_at", direction="backward").drop(columns=["known_at"])
    entry, cmax, cmin, end_ret = build_paths(d, HORIZON)
    n = len(entry)
    d = d.iloc[:n].reset_index(drop=True)
    d["_cmax_final"] = cmax[:, -1]
    d["_cmin_final"] = cmin[:, -1]
    d["fwd24_ret"] = end_ret * 100
    return d, entry, cmax, cmin, end_ret


def r_series(d, cmax, cmin, end_ret, tp_a: float, sl_a: float, direction="BUY"):
    a = d["atr_pct"].to_numpy()
    tp, sl = a * tp_a, a * sl_a
    win, loss, opn, _ = outcomes(cmax, cmin, tp, sl, direction)
    sgn = 1.0 if direction == "BUY" else -1.0
    r = np.where(win, (tp - FRIC) / sl, np.where(loss, -(sl + FRIC) / sl, 0.0))
    r = np.where(opn, (sgn * end_ret - FRIC) / sl, r)
    return r, win, opn


def block_boot(r: np.ndarray, mask: np.ndarray, day_key: np.ndarray,
               n_boot: int = 4000, seed: int = 7):
    """GÜN-BLOKLU bootstrap: günler yerine konarak çekilir (örtüşen etiketler i.i.d. değil)."""
    rng = np.random.default_rng(seed)
    sub_days = day_key[mask]
    sub_r = r[mask]
    if len(sub_r) == 0:
        return np.nan, np.nan, np.nan
    uniq, inv = np.unique(sub_days, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    inv_s = inv[order]
    r_s = sub_r[order]
    starts = np.searchsorted(inv_s, np.arange(len(uniq)))
    ends = np.searchsorted(inv_s, np.arange(len(uniq)), side="right")
    csum = np.concatenate([[0.0], np.cumsum(r_s)])
    day_sum = csum[ends] - csum[starts]
    day_cnt = (ends - starts).astype(float)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    tot = day_sum[idx].sum(1)
    cnt = day_cnt[idx].sum(1)
    means = tot / cnt
    return float(np.mean(sub_r)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def block_boot_diff(r, mask_a, mask_b, day_key, n_boot=4000, seed=7):
    """İki maskenin EV farkı için gün-bloklu bootstrap (aynı günler birlikte çekilir)."""
    rng = np.random.default_rng(seed)
    both = mask_a | mask_b
    days = day_key[both]
    uniq, inv = np.unique(days, return_inverse=True)
    ra = np.where(mask_a[both], r[both], 0.0)
    na = mask_a[both].astype(float)
    rb = np.where(mask_b[both], r[both], 0.0)
    nb = mask_b[both].astype(float)
    A = np.zeros(len(uniq)); NA = np.zeros(len(uniq))
    B = np.zeros(len(uniq)); NB = np.zeros(len(uniq))
    np.add.at(A, inv, ra); np.add.at(NA, inv, na)
    np.add.at(B, inv, rb); np.add.at(NB, inv, nb)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    ea = A[idx].sum(1) / np.maximum(NA[idx].sum(1), 1e-9)
    eb = B[idx].sum(1) / np.maximum(NB[idx].sum(1), 1e-9)
    diff = ea - eb
    obs = r[mask_a].mean() - r[mask_b].mean()
    return float(obs), float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5)), \
        float((diff >= 0).mean())
