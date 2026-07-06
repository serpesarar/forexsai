"""Honest triple-barrier labeler on 1m bid/ask bars.

Rules (see DESIGN.md §6):
  * entry at the NEXT bar's open, at ask for BUY / bid for SELL (no same-bar fill)
  * BUY exits happen on the bid series, SELL exits on the ask series —
    the spread is inside the replay, never a constant haircut
  * TP and SL both touchable within one bar ⇒ LOSS (conservative, matches the
    2026-05 finding that ~27% of naive "wins" are SL-first)
  * time-stop exit at bar close, labeled by sign of net PnL
  * events whose barrier window crosses a data gap, the session flat-time, or
    runs out of bars ⇒ dropped (label = None), never imputed

The labeler is deliberately loop-based per event (clarity over speed); with a
few thousand events this runs in seconds.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402


@dataclass
class Geometry:
    tp_atr: float           # in "pct" mode this holds the TP fraction (e.g. 0.0010 = 0.10%)
    sl_atr: float           # in "pct" mode this holds the SL fraction
    time_stop_min: int
    mode: str = "atr"       # "atr" (×ATR distances) | "pct" (×entry-price distances)
    entry_mode: str = "market"  # "market" (next-bar open at ask/bid) | "limit_mid"
                                # (resting limit at event-bar mid close; fills on the
                                # next bar only if price trades through it, else no trade)


@dataclass
class LabelResult:
    outcome: str          # "win" | "loss" | "dropped"
    exit_reason: str      # "tp" | "sl" | "ambiguous_bar" | "time_stop" | gap/flat/eod reasons
    entry_px: float = np.nan
    exit_px: float = np.nan
    r_multiple: float = np.nan
    hold_min: int = 0
    mfe_r: float = np.nan  # max favorable excursion in R (risk units)
    mae_r: float = np.nan  # max adverse excursion in R
    sl_dist: float = np.nan  # stop distance in points (risk unit for R↔points conversion)


def compute_atr(bars: pd.DataFrame, period: int = config.ATR_PERIOD) -> pd.Series:
    """Wilder ATR on mid OHLC. `bars` must be time-sorted."""
    h, l, c = bars["mid_h"], bars["mid_l"], bars["mid_c"]
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def _flat_deadline(day_ts: pd.Timestamp) -> pd.Timestamp:
    hh, mm = config.FLAT_BY_UTC.split(":")
    return day_ts.normalize() + pd.Timedelta(hours=int(hh), minutes=int(mm))


def label_event(
    bars: pd.DataFrame,
    event_idx: int,
    direction: str,
    geometry: Geometry,
    atr: pd.Series,
) -> LabelResult:
    """Label one event. `bars` time-sorted with positional index; `event_idx` is the
    positional index of the trigger-confirm bar (entry happens on the next bar)."""
    if event_idx + 1 >= len(bars):
        return LabelResult("dropped", "eod_no_next_bar")
    a = atr.iloc[event_idx]
    if geometry.mode == "atr" and (not np.isfinite(a) or a <= 0):
        return LabelResult("dropped", "no_atr")

    entry_bar = bars.iloc[event_idx + 1]
    prev_bar_ts = bars.iloc[event_idx]["ts"]
    if (entry_bar["ts"] - prev_bar_ts) > pd.Timedelta(minutes=config.GAP_MAX_SILENT_MIN):
        return LabelResult("dropped", "gap_at_entry")

    is_buy = direction == "BUY"
    if geometry.entry_mode == "limit_mid":
        ev_bar = bars.iloc[event_idx]
        entry = float((ev_bar["bid_c"] + ev_bar["ask_c"]) / 2.0)
        filled = (entry_bar["ask_l"] <= entry) if is_buy else (entry_bar["bid_h"] >= entry)
        if not filled:
            return LabelResult("dropped", "no_fill")
    else:
        entry = float(entry_bar["ask_o"] if is_buy else entry_bar["bid_o"])
    unit = entry if geometry.mode == "pct" else a
    tp_d, sl_d = geometry.tp_atr * unit, geometry.sl_atr * unit
    tp = entry + tp_d if is_buy else entry - tp_d
    sl = entry - sl_d if is_buy else entry + sl_d
    deadline = min(
        entry_bar["ts"] + pd.Timedelta(minutes=geometry.time_stop_min),
        _flat_deadline(entry_bar["ts"]),
    )

    mfe = mae = 0.0
    last_ts = entry_bar["ts"]
    for j in range(event_idx + 1, len(bars)):
        b = bars.iloc[j]
        if (b["ts"] - last_ts) > pd.Timedelta(minutes=config.GAP_MAX_SILENT_MIN):
            return LabelResult("dropped", "gap_in_window")
        last_ts = b["ts"]

        # exit side series: BUY exits on bid, SELL exits on ask
        hi = float(b["bid_h"] if is_buy else b["ask_h"])
        lo = float(b["bid_l"] if is_buy else b["ask_l"])
        fav = (hi - entry) if is_buy else (entry - lo)
        adv = (entry - lo) if is_buy else (hi - entry)
        mfe, mae = max(mfe, fav), max(mae, adv)
        hold = int((b["ts"] - entry_bar["ts"]).total_seconds() // 60)

        hit_tp = hi >= tp if is_buy else lo <= tp
        hit_sl = lo <= sl if is_buy else hi >= sl
        if hit_tp and hit_sl:
            if config.AMBIGUOUS_BAR_IS_LOSS:
                return LabelResult("loss", "ambiguous_bar", entry, float(sl), -1.0, hold, mfe / sl_d, mae / sl_d, sl_d)
            hit_tp = False  # fallthrough to SL (never used with default config)
        if hit_sl:
            return LabelResult("loss", "sl", entry, float(sl), -1.0, hold, mfe / sl_d, mae / sl_d, sl_d)
        if hit_tp:
            return LabelResult("win", "tp", entry, float(tp), tp_d / sl_d, hold, mfe / sl_d, mae / sl_d, sl_d)

        if b["ts"] >= deadline:
            exit_px = float(b["bid_c"] if is_buy else b["ask_c"])
            pnl = (exit_px - entry) if is_buy else (entry - exit_px)
            r = pnl / sl_d
            return LabelResult("win" if pnl > 0 else "loss", "time_stop", entry, exit_px, r, hold, mfe / sl_d, mae / sl_d, sl_d)

    return LabelResult("dropped", "ran_out_of_bars")


def label_events_fast(
    bars: pd.DataFrame,
    events: pd.DataFrame,
    geometry: Geometry,
) -> pd.DataFrame:
    """Vectorized labeler — same semantics as label_event (cross-checked by
    tests/test_labeler_parity.py). Required for the placebo battery (~1M labelings)."""
    bars = bars.sort_values("ts").reset_index(drop=True)
    atr_s = compute_atr(bars).to_numpy()
    ts = bars["ts"].to_numpy()
    ts_ns = ts.astype("datetime64[ns]").astype("int64")
    ask_o, bid_o = bars["ask_o"].to_numpy(), bars["bid_o"].to_numpy()
    bid_h, bid_l = bars["bid_h"].to_numpy(), bars["bid_l"].to_numpy()
    ask_h, ask_l = bars["ask_h"].to_numpy(), bars["ask_l"].to_numpy()
    bid_c, ask_c = bars["bid_c"].to_numpy(), bars["ask_c"].to_numpy()
    n = len(bars)
    gap_after = np.empty(n, dtype=bool)  # gap between bar k and k+1
    gap_after[:-1] = (np.diff(ts_ns) > config.GAP_MAX_SILENT_MIN * 60_000_000_000)
    gap_after[-1] = True
    pos = pd.Series(np.arange(n), index=ts)

    hh, mm = (int(x) for x in config.FLAT_BY_UTC.split(":"))
    day_ns = 86_400_000_000_000
    ts_min_ns = geometry.time_stop_min * 60_000_000_000

    results = []
    for ev_ts, direction in zip(events["ts"].to_numpy(), events["direction"].to_numpy()):
        e = pos.get(pd.Timestamp(ev_ts))
        if e is None or (isinstance(e, float) and np.isnan(e)):
            results.append(LabelResult("dropped", "event_bar_missing"))
            continue
        e = int(e)
        i = e + 1
        if i >= n:
            results.append(LabelResult("dropped", "eod_no_next_bar"))
            continue
        a = atr_s[e]
        if geometry.mode == "atr" and (not np.isfinite(a) or a <= 0):
            results.append(LabelResult("dropped", "no_atr"))
            continue
        if gap_after[e]:
            results.append(LabelResult("dropped", "gap_at_entry"))
            continue

        is_buy = direction == "BUY"
        if geometry.entry_mode == "limit_mid":
            # resting limit at event-bar mid close; conservative single-bar fill window
            entry = (bid_c[e] + ask_c[e]) / 2.0
            filled = (ask_l[i] <= entry) if is_buy else (bid_h[i] >= entry)
            if not filled:
                results.append(LabelResult("dropped", "no_fill"))
                continue
        else:
            entry = ask_o[i] if is_buy else bid_o[i]
        unit = entry if geometry.mode == "pct" else a
        tp_d, sl_d = geometry.tp_atr * unit, geometry.sl_atr * unit
        deadline_ns = min(ts_ns[i] + ts_min_ns,
                          (ts_ns[i] // day_ns) * day_ns + (hh * 60 + mm) * 60_000_000_000)
        j_end = int(np.searchsorted(ts_ns, deadline_ns, side="left"))
        if j_end >= n:
            j_end = n - 1
        if j_end < i:  # entry bar already at/past the flat deadline (e.g. shifted events)
            results.append(LabelResult("dropped", "past_flat_time"))
            continue
        w = slice(i, j_end + 1)

        if is_buy:
            tp, sl = entry + tp_d, entry - sl_d
            hit_tp_a = bid_h[w] >= tp
            hit_sl_a = bid_l[w] <= sl
            fav, adv = bid_h[w] - entry, entry - bid_l[w]
        else:
            tp, sl = entry - tp_d, entry + sl_d
            hit_tp_a = ask_l[w] <= tp
            hit_sl_a = ask_h[w] >= sl
            fav, adv = entry - ask_l[w], ask_h[w] - entry

        first_tp = int(np.argmax(hit_tp_a)) if hit_tp_a.any() else 1 << 30
        first_sl = int(np.argmax(hit_sl_a)) if hit_sl_a.any() else 1 << 30
        gaps_w = gap_after[i:j_end + 1]  # gap after bar i+k invalidates resolution beyond it
        first_gap = int(np.argmax(gaps_w)) if gaps_w.any() else 1 << 30

        hit_k = min(first_tp, first_sl)
        if hit_k <= first_gap and hit_k < (1 << 30):
            k = hit_k
            hold = int((ts_ns[i + k] - ts_ns[i]) // 60_000_000_000)
            mfe = float(np.max(fav[: k + 1])) / sl_d
            mae = float(np.max(adv[: k + 1])) / sl_d
            if first_tp == first_sl:
                results.append(LabelResult("loss", "ambiguous_bar", float(entry), float(sl), -1.0, hold, mfe, mae, sl_d))
            elif first_sl < first_tp:
                results.append(LabelResult("loss", "sl", float(entry), float(sl), -1.0, hold, mfe, mae, sl_d))
            else:
                results.append(LabelResult("win", "tp", float(entry), float(tp), tp_d / sl_d, hold, mfe, mae, sl_d))
            continue

        # no barrier hit before a gap: gap first ⇒ dropped; else time-stop at j_end
        if first_gap < (1 << 30) and (i + first_gap) < j_end:
            results.append(LabelResult("dropped", "gap_in_window"))
            continue
        if ts_ns[j_end] < deadline_ns and j_end == n - 1:
            results.append(LabelResult("dropped", "ran_out_of_bars"))
            continue
        exit_px = float(bid_c[j_end] if is_buy else ask_c[j_end])
        pnl = (exit_px - entry) if is_buy else (entry - exit_px)
        hold = int((ts_ns[j_end] - ts_ns[i]) // 60_000_000_000)
        mfe = float(np.max(fav)) / sl_d
        mae = float(np.max(adv)) / sl_d
        results.append(LabelResult("win" if pnl > 0 else "loss", "time_stop",
                                   float(entry), exit_px, pnl / sl_d, hold, mfe, mae, sl_d))

    lab = pd.DataFrame([r.__dict__ for r in results])
    return pd.concat([events.reset_index(drop=True), lab], axis=1)


def label_events(
    bars: pd.DataFrame,
    events: pd.DataFrame,
    geometry: Geometry,
) -> pd.DataFrame:
    """Label a frame of events. `events` needs columns [ts, direction]; returns
    events joined with label columns. `bars` must cover the events' days."""
    bars = bars.sort_values("ts").reset_index(drop=True)
    atr = compute_atr(bars)
    pos = pd.Series(np.arange(len(bars)), index=pd.DatetimeIndex(bars["ts"]))

    out = []
    for _, ev in events.iterrows():
        idx = pos.get(pd.Timestamp(ev["ts"]))
        if idx is None or (isinstance(idx, float) and np.isnan(idx)):
            out.append(LabelResult("dropped", "event_bar_missing"))
            continue
        out.append(label_event(bars, int(idx), ev["direction"], geometry, atr))

    lab = pd.DataFrame([r.__dict__ for r in out])
    return pd.concat([events.reset_index(drop=True), lab], axis=1)
