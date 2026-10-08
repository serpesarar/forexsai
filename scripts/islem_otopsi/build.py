"""Özellik tablosunu kurar: işlem başına tek satır, dört zaman ailesi + bağlam."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from . import settings as S
from .features import Ctx, early, geometry, make_ctx, pre_divergence, pre_momentum, pre_trend, pre_volume, time_features
from .indicators import SymbolBars
from .path import classify_outcome, path_core, path_events, path_volume, post_exit, sl_verdict

log = logging.getLogger("islem_otopsi.build")


def trade_features(row: pd.Series, sb: SymbolBars, now: pd.Timestamp) -> dict | None:
    c = make_ctx(row, sb)
    if c is None:
        return None
    r_exit = float(c.r(c.exit)) if np.isfinite(c.risk) else np.nan
    f: dict = {"pid": row["pid"], "r_exit": r_exit,
               "outcome": classify_outcome(int(row["reason"]), r_exit, float(row["net"])),
               "pre_stale_min": (c.t0 - c.sb.m1.index[c.i_pre]).total_seconds() / 60 - 1}
    tr = pre_trend(c)
    mo = pre_momentum(c, tr["_atr1"], tr["_atr5"])
    f.update(tr)
    f.update(mo)
    f.update(pre_volume(c))
    f.update(pre_divergence(c))
    f.update(geometry(c, tr["_atr5"], tr["_atr60"]))
    f.update(time_features(c.t0))
    for k in S.EARLY_MARKS_MIN:
        f.update(early(c, k))
    core = path_core(c, r_exit)
    f.update(core)
    if "_i_mfe" in core:
        f.update(path_volume(c, core["_i_mfe"], core["_i_mae"], r_exit))
    f.update(path_events(c, mo["_struct"], tr["_atr1"]))
    if f["outcome"] != "SL":
        f["path_spike_stop"] = np.nan          # iğne-stop yalnız SL çıkışında anlamlı
    f.update(_exit_slip(c, f["outcome"], r_exit))
    post = {}
    for h in (S.POST_EXIT_SHORT_MIN, S.POST_EXIT_MIN):
        post.update(post_exit(c, r_exit, now, h))
    f.update(post)
    f["sl_verdict"] = sl_verdict(f["outcome"], r_exit, post)
    return f


def _exit_slip(c: Ctx, outcome: str, r_exit: float) -> dict:
    if outcome == "SL" and np.isfinite(r_exit):
        return {"path_exit_slip_r": r_exit + 1.0}
    if outcome == "TP" and np.isfinite(c.reward):
        return {"path_exit_slip_r": r_exit - c.reward / c.risk}
    return {}


def add_context(t: pd.DataFrame, vix: pd.Series) -> pd.DataFrame:
    """Hesap düzeyi bağlam: eşzamanlı pozisyon, önceki işlem, VIX rejimi (önceki gün)."""
    t = t.sort_values("entry_utc").reset_index(drop=True)
    starts, ends = t["entry_utc"].values, t["exit_utc"].values
    t["ctx_n_open"] = [int(((starts < s0) & (ends > s0)).sum()) for s0 in starts]
    prev_gap, prev_win, prev_same = [], [], []
    for i, r in t.iterrows():
        prior = t[(t["symbol"] == r["symbol"]) & (t["exit_utc"] <= r["entry_utc"])]
        if prior.empty:
            prev_gap.append(np.nan); prev_win.append(np.nan); prev_same.append(np.nan)
            continue
        p = prior.loc[prior["exit_utc"].idxmax()]
        prev_gap.append((r["entry_utc"] - p["exit_utc"]).total_seconds() / 60)
        prev_win.append(float(p["net"] > 0))
        prev_same.append(float(p["direction"] == r["direction"]))
    t["ctx_min_since_prev"] = prev_gap
    t["ctx_prev_win"] = prev_win
    t["ctx_prev_same_dir"] = prev_same
    t["pre_vix_prev"] = [_vix_before(vix, ts) for ts in t["entry_utc"]]
    is_ndx = t["symbol"] == "NDX.INDX"
    buy = t["direction"] == "BUY"
    fav = np.where(buy, t["pre_vix_prev"] >= S.VIX_REGIME_THRESHOLD, t["pre_vix_prev"] < S.VIX_REGIME_THRESHOLD)
    t["pre_vix_favors"] = np.where(is_ndx & t["pre_vix_prev"].notna(), fav.astype(float), np.nan)
    return t


def _vix_before(vix: pd.Series, ts: pd.Timestamp) -> float:
    """Karar gününden ÖNCEKİ tamamlanmış VIX kapanışı (E20: gün içi değer kullanılmaz)."""
    if vix.empty:
        return np.nan
    day = pd.Timestamp(ts.tz_convert("America/New_York").date())
    prior = vix[vix.index < day]
    return float(prior.iloc[-1]) if len(prior) else np.nan


def build_table(trades: pd.DataFrame, bars: dict[str, SymbolBars], fps: dict[int, dict],
                vix: pd.Series, now: pd.Timestamp) -> tuple[pd.DataFrame, list]:
    rows, skipped = [], []
    for _, r in trades.iterrows():
        sb = bars.get(r["symbol"])
        f = trade_features(r, sb, now) if sb is not None else None
        if f is None:
            skipped.append((r["pid"], "giriş öncesi yeterli mum yok (ısınma)"))
            continue
        rows.append(f)
    if not rows:
        return pd.DataFrame(), skipped
    feats = pd.DataFrame(rows)
    t = trades.merge(feats, on="pid", how="inner")
    fp = pd.DataFrame.from_dict(fps, orient="index")
    if not fp.empty:
        fp.index.name = "pid"
        t = t.merge(fp.reset_index(), on="pid", how="left")
    t = add_context(t, vix)
    t["is_win"] = (t["net"] > 0).astype(int)
    t["side"] = t["symbol"].str.split(".").str[0] + " " + t["direction"]
    return t, skipped
