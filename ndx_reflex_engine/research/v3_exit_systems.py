"""V3 — EXIT SYSTEMS BENCHMARK. Entry frozen (V1 gate), 11 exit families compared.

Families: fixed_sl (baseline), atr_trail, chandelier, supertrend, donchian,
swing_low, structure, vwap_target, liquidity_target, ml_exit, time_based, hybrid.

All exits are bar-by-bar, causal (dynamic stops ratchet only from prior/closed bars;
ML/structure/swing use confirmed values only), conservative intrabar ordering
(adverse extreme before favorable), spread inside the replay, 1pt slippage/fill.
Risk unit R = initial SL distance (fixed per family). Params tuned on 2025-train,
reported on 2025-holdout + 2026 broker. Winners get the 10-group stability check.

Usage: python3 research/v3_exit_systems.py
"""
from __future__ import annotations

import glob
import json
import logging
import os
import sys
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from labels.triple_barrier import compute_atr  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402
from research.v2_exit_study import entries_2025, entries_2026, metrics  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("v3_exits")
RNG = np.random.default_rng(23)
SLIP = config.SLIPPAGE_PTS
GAP_NS = config.GAP_MAX_SILENT_MIN * 60_000_000_000


# ── extended per-day arrays (all causal) ─────────────────────────────────────

def ext_arrays(bars: pd.DataFrame, prev: pd.DataFrame | None) -> dict:
    b = bars.sort_values("ts").reset_index(drop=True)
    n = len(b)
    mh, ml_, mc = b["mid_h"].to_numpy(), b["mid_l"].to_numpy(), b["mid_c"].to_numpy()
    atr = compute_atr(b).to_numpy()
    hl2 = (mh + ml_) / 2.0

    def roll_max(a, N):
        return pd.Series(a).rolling(N, min_periods=1).max().to_numpy()

    def roll_min(a, N):
        return pd.Series(a).rolling(N, min_periods=1).min().to_numpy()

    # SuperTrend (period 10, mult 3), causal recursive final bands
    per, mult = 10, 3.0
    atr_st = pd.Series(mh - ml_).rolling(per, min_periods=1).mean().to_numpy()
    upper = hl2 + mult * atr_st
    lower = hl2 - mult * atr_st
    st = np.full(n, np.nan)
    dir_ = np.ones(n, dtype=int)
    fu, fl = upper.copy(), lower.copy()
    for i in range(1, n):
        fu[i] = upper[i] if (upper[i] < fu[i - 1] or mc[i - 1] > fu[i - 1]) else fu[i - 1]
        fl[i] = lower[i] if (lower[i] > fl[i - 1] or mc[i - 1] < fl[i - 1]) else fl[i - 1]
        if mc[i] > fu[i - 1]:
            dir_[i] = 1
        elif mc[i] < fl[i - 1]:
            dir_[i] = -1
        else:
            dir_[i] = dir_[i - 1]
        st[i] = fl[i] if dir_[i] == 1 else fu[i]

    # session VWAP (per-day cumulative, tick-count weighted)
    w = b["n_ticks"].fillna(1).clip(lower=1).to_numpy() if "n_ticks" in b else np.ones(n)
    vwap = np.cumsum(mc * w) / np.maximum(np.cumsum(w), 1e-9)

    # confirmed swing pivots (k=2, confirmed at j+2)
    last_sl = np.full(n, np.nan)
    last_sh = np.full(n, np.nan)
    sl_v = sh_v = np.nan
    for j in range(n):
        c = j - 2  # candidate bar confirmable at j
        if c >= 2 and c + 2 <= n - 1 and c <= j:
            seg_l = ml_[c - 2:c + 3]
            seg_h = mh[c - 2:c + 3]
            if ml_[c] == seg_l.min():
                sl_v = ml_[c]
            if mh[c] == seg_h.max():
                sh_v = mh[c]
        last_sl[j], last_sh[j] = sl_v, sh_v

    pdh = float(prev["mid_h"].max()) if prev is not None and len(prev) else np.nan
    pdl = float(prev["mid_l"].min()) if prev is not None and len(prev) else np.nan

    ts = b["ts"].to_numpy().astype("datetime64[ns]").astype("int64")
    return dict(
        ts=ts, pos={t: k for k, t in enumerate(ts)}, atr=atr,
        ao=b["ask_o"].to_numpy(), bo=b["bid_o"].to_numpy(),
        bh=b["bid_h"].to_numpy(), bl=b["bid_l"].to_numpy(),
        ah=b["ask_h"].to_numpy(), al=b["ask_l"].to_numpy(),
        bc=b["bid_c"].to_numpy(), ac=b["ac" if "ac" in b else "ask_c"].to_numpy(),
        mc=mc, mh=mh, ml=ml_,
        rmax10=roll_max(mh, 10), rmax20=roll_max(mh, 20),
        rmin10=roll_min(ml_, 10), rmin20=roll_min(ml_, 20),
        st=st, st_dir=dir_, vwap=vwap, last_sl=last_sl, last_sh=last_sh, pdh=pdh, pdl=pdl,
    )


def _win(A, e, ts_min):
    n = len(A["ts"])
    i = e + 1
    if i >= n or (A["ts"][i] - A["ts"][e]) > GAP_NS:
        return None
    a = A["atr"][e]
    if not np.isfinite(a) or a <= 0:
        return None
    hh, mm = (int(x) for x in config.FLAT_BY_UTC.split(":"))
    day_ns = 86_400_000_000_000
    flat = (A["ts"][i] // day_ns) * day_ns + (hh * 60 + mm) * 60_000_000_000
    deadline = min(A["ts"][i] + ts_min * 60_000_000_000, flat)
    return i, deadline, a


def _dyn_stop(A, j, is_buy, cfg, a, entry, peak):
    """Return the candidate dynamic stop level for bar j (favor-ratcheting)."""
    mode = cfg["stop_mode"]
    if mode == "atr_trail":
        return (peak - cfg["trail"] * a) if is_buy else (peak + cfg["trail"] * a)
    if mode == "chandelier":
        N = cfg.get("N", 10)
        rmax = A["rmax10"] if N == 10 else A["rmax20"]
        rmin = A["rmin10"] if N == 10 else A["rmin20"]
        return (rmax[j] - cfg["m"] * a) if is_buy else (rmin[j] + cfg["m"] * a)
    if mode == "supertrend":
        return A["st"][j]
    if mode == "donchian":
        N = cfg.get("N", 10)
        arr = (A["rmin10"] if N == 10 else A["rmin20"]) if is_buy else (A["rmax10"] if N == 10 else A["rmax20"])
        return arr[j]  # level from bars ≤ j, applied on bar j+1 (no lookahead)
    if mode == "swing":
        return A["last_sl"][j] if is_buy else A["last_sh"][j]
    if mode == "structure":  # only ratchet on higher-low / lower-high
        return A["last_sl"][j] if is_buy else A["last_sh"][j]
    return np.nan


def _target(A, i, is_buy, cfg, a, entry):
    """Static target level at entry, or None."""
    tm = cfg.get("target_mode")
    if tm is None:
        return None
    if tm == "atr":
        return entry + cfg["tp"] * a if is_buy else entry - cfg["tp"] * a
    if tm == "vwap":
        v = A["vwap"][i]
        # only use if it's a real target in the trade's favor
        if (is_buy and v > entry) or (not is_buy and v < entry):
            return v
        return entry + cfg.get("tp", 0.8) * a if is_buy else entry - cfg.get("tp", 0.8) * a
    if tm == "liquidity":
        if is_buy:
            cands = [x for x in (A["pdh"], A["last_sh"][i]) if np.isfinite(x) and x > entry]
            return min(cands) if cands else entry + cfg.get("tp", 1.0) * a
        cands = [x for x in (A["pdl"], A["last_sl"][i]) if np.isfinite(x) and x < entry]
        return max(cands) if cands else entry - cfg.get("tp", 1.0) * a
    return None


def simulate(A, e, direction, sl_atr, p, cfg, ml_model=None) -> dict | None:
    w = _win(A, e, cfg.get("ts_min", 60))
    if w is None:
        return None
    i, deadline, a = w
    is_buy = direction == "BUY"
    entry = A["ao"][i] if is_buy else A["bo"][i]
    sl_dist = sl_atr * a
    if sl_dist <= 0:
        return None
    slip_r = SLIP / sl_dist
    stop = entry - sl_dist if is_buy else entry + sl_dist
    target = _target(A, i, is_buy, cfg, a, entry)
    peak = entry
    frac = 1.0
    realized = 0.0
    last_ts = A["ts"][i]
    n = len(A["ts"])
    armed = cfg.get("stop_mode") not in ("atr_trail",)  # atr_trail needs arming
    time_exit = cfg.get("time_exit_min")
    tp1_done = False
    flip_next = False  # dynamic stop crossed price / SuperTrend flip → exit next open at market

    # NO-LOOKAHEAD ORDERING: the stop/target active DURING bar j is established only
    # from bars ≤ j-1. Each iteration: (1) test bar j against the pre-existing
    # stop/target/ml/time, then (2) update the dynamic stop, peak and partial using
    # bar j's data for use in bar j+1. SuperTrend/chandelier/etc. indexed at j thus
    # act as the level for the NEXT bar (their value is only known at j's close).
    for j in range(i, n):
        if (A["ts"][j] - last_ts) > GAP_NS:
            return None
        last_ts = A["ts"][j]
        fav = A["bh"][j] if is_buy else A["al"][j]
        adv = A["bl"][j] if is_buy else A["ah"][j]

        # 1) stop (adverse first) — resting stop set from bars ≤ j-1, filled intrabar at
        # the stop level (standard intraday convention; true session/data gaps are already
        # excluded by the gap registry). +1pt slippage applied below covers stop slip.
        # Robustness knobs: gap_fill forces fill at bar open (conservative); extra_stop_slip
        # adds points of adverse slippage on every stop/trail exit.
        if (adv <= stop) if is_buy else (adv >= stop):
            fill = stop
            if cfg.get("gap_fill"):
                fill = min(stop, A["bo"][j]) if is_buy else max(stop, A["ao"][j])
            pnl = (fill - entry) if is_buy else (entry - fill)
            extra = cfg.get("extra_stop_slip", 0.0) / sl_dist
            realized += frac * (pnl / sl_dist) - frac * (slip_r + extra)
            return _res(realized, A, i, j)

        # 2) target
        if target is not None and ((fav >= target) if is_buy else (fav <= target)):
            pnl = (target - entry) if is_buy else (entry - target)
            realized += frac * (pnl / sl_dist) - frac * slip_r
            return _res(realized, A, i, j)

        # 3) ML exit — features use only closed info through bar j; exit at j close
        if ml_model is not None and j > i:
            feat = _ml_feats(A, i, j, entry, sl_dist, is_buy, a)
            if ml_model.predict(feat.reshape(1, -1))[0] >= cfg.get("ml_tau", 0.6):
                px = A["bc"][j] if is_buy else A["ac"][j]
                pnl = (px - entry) if is_buy else (entry - px)
                realized += frac * (pnl / sl_dist) - frac * slip_r
                return _res(realized, A, i, j)

        # 4) time exit / deadline
        held = (A["ts"][j] - A["ts"][i]) // 60_000_000_000
        if (time_exit is not None and held >= time_exit) or A["ts"][j] >= deadline:
            px = A["bc"][j] if is_buy else A["ac"][j]
            pnl = (px - entry) if is_buy else (entry - px)
            realized += frac * (pnl / sl_dist) - frac * slip_r
            return _res(realized, A, i, j)

        # ── update state for bar j+1 (no effect on bar j's own tests above) ──
        if is_buy:
            peak = max(peak, fav)
        else:
            peak = min(peak, fav)
        if cfg["stop_mode"] != "fixed":
            if cfg["stop_mode"] == "atr_trail":
                fav_move = (peak - entry) if is_buy else (entry - peak)
                if fav_move >= cfg.get("arm", 0.4) * a:
                    armed = True
            if cfg["stop_mode"] == "supertrend":
                # SuperTrend is a reversal signal, not a resting stop: when the trend
                # flips against the position the band jumps to the wrong side of price.
                # Exit at THIS bar's close (market) — never book a fill beyond market.
                if (is_buy and A["st_dir"][j] < 0) or (not is_buy and A["st_dir"][j] > 0):
                    px = A["bc"][j] if is_buy else A["ac"][j]
                    pnl = (px - entry) if is_buy else (entry - px)
                    realized += frac * (pnl / sl_dist) - frac * slip_r
                    return _res(realized, A, i, j)
                cand = A["st"][j]
                if np.isfinite(cand) and ((is_buy and cand < A["mc"][j]) or (not is_buy and cand > A["mc"][j])):
                    stop = max(stop, cand) if is_buy else min(stop, cand)
            elif armed:
                # genuine trailing stops: ratchet the resting level; an intrabar breach
                # fills at the stop level via the adverse check next bar (realistic).
                cand = _dyn_stop(A, j, is_buy, cfg, a, entry, peak)
                if np.isfinite(cand):
                    stop = max(stop, cand) if is_buy else min(stop, cand)
        # break-even after N one-minute bars: pull the stop to entry once the trade
        # has had N bars to work (user rule: 5 bars → SL to entry level)
        if cfg.get("be_after_bars"):
            held_now = (A["ts"][j] - A["ts"][i]) // 60_000_000_000
            if held_now >= cfg["be_after_bars"]:
                stop = max(stop, entry) if is_buy else min(stop, entry)

        if cfg.get("partial") and not tp1_done:
            t1 = entry + cfg["tp1"] * a if is_buy else entry - cfg["tp1"] * a
            if (peak >= t1) if is_buy else (peak <= t1):
                realized += 0.5 * (cfg["tp1"] * a / sl_dist) - 0.5 * slip_r
                frac = 0.5
                stop = max(stop, entry) if is_buy else min(stop, entry)
                tp1_done = True
    return None


def _res(realized, A, i, j):
    return {"r": realized, "win": int(realized > 0),
            "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}


def _ml_feats(A, i, j, entry, sl_dist, is_buy, a):
    mc = A["mc"]
    unreal = ((mc[j] - entry) if is_buy else (entry - mc[j])) / sl_dist
    seg = A["bl"][i:j + 1] if is_buy else A["ah"][i:j + 1]
    mae = ((entry - seg.min()) if is_buy else (seg.max() - entry)) / sl_dist
    favseg = A["bh"][i:j + 1] if is_buy else A["al"][i:j + 1]
    mfe = ((favseg.max() - entry) if is_buy else (entry - favseg.min())) / sl_dist
    mom3 = ((mc[j] - mc[max(i, j - 3)]) / a) * (1 if is_buy else -1)
    held = float(j - i)
    return np.array([unreal, mae, mfe, mom3, held, a / max(A["atr"][i], 1e-9)], dtype=float)


# ── ML-exit training (train entries only) ────────────────────────────────────

def train_ml_exit(entries_train, bars_by_day) -> lgb.Booster:
    X, y = [], []
    base_cfg = {"stop_mode": "fixed", "ts_min": 60}
    for _, ev in entries_train.iterrows():
        d = str(pd.Timestamp(ev["ts"]).date())
        A = bars_by_day.get(d)
        if A is None:
            continue
        e = A["pos"].get(pd.Timestamp(ev["ts"]).to_datetime64().astype("datetime64[ns]").astype("int64"))
        if e is None:
            continue
        w = _win(A, int(e), 60)
        if w is None:
            continue
        i, deadline, a = w
        is_buy = ev["direction"] == "BUY"
        entry = A["ao"][i] if is_buy else A["bo"][i]
        sl_dist = ev["sl_atr"] * a
        if sl_dist <= 0:
            continue
        # final baseline outcome (loss?) under fixed SL + time
        res = simulate(A, int(e), ev["direction"], ev["sl_atr"], ev["p"], base_cfg)
        if res is None:
            continue
        loss = int(res["r"] <= 0)
        n = len(A["ts"])
        for j in range(i + 1, n):
            if A["ts"][j] > deadline:
                break
            X.append(_ml_feats(A, i, j, entry, sl_dist, is_buy, a))
            y.append(loss)
    X, y = np.array(X), np.array(y)
    ds = lgb.Dataset(X, y)
    return lgb.train({**config.LGBM_PARAMS, "objective": "binary"}, ds, num_boost_round=120)


def run(entries, bars_by_day, cfg, ml_model=None) -> pd.DataFrame:
    recs = []
    for _, ev in entries.iterrows():
        d = str(pd.Timestamp(ev["ts"]).date())
        A = bars_by_day.get(d)
        if A is None:
            continue
        e = A["pos"].get(pd.Timestamp(ev["ts"]).to_datetime64().astype("datetime64[ns]").astype("int64"))
        if e is None:
            continue
        r = simulate(A, int(e), ev["direction"], ev["sl_atr"], ev["p"], cfg,
                     ml_model if cfg.get("ml_exit") else None)
        if r is not None:
            r.update(ts=ev["ts"], family=ev["family"])
            recs.append(r)
    return pd.DataFrame(recs)


def _fmt(m):
    if not m or m.get("n", 0) == 0:
        return "n=0"
    return (f"n={m['n']:4d} WR={m['wr']*100:5.1f}% EV={m['ev_r']:+.3f}R PF={m['pf']:.2f} "
            f"DD={m['max_dd_r']:5.1f} aw={m['avg_win']} al={m['avg_loss']}")


def main() -> None:
    # build arrays
    raw25 = {os.path.basename(p).replace(".parquet", ""): pd.read_parquet(p)
             for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet")))}
    days25 = sorted(raw25.keys())
    bars25 = {}
    for k, d in enumerate(days25):
        bars25[d] = ext_arrays(raw25[d], raw25[days25[k - 1]] if k else None)
    bars26_raw = to_bar_frame(fetch_candles())
    days26 = sorted(str(d) for d in bars26_raw["ts"].dt.date.unique())
    grp26 = {str(d): g.reset_index(drop=True) for d, g in bars26_raw.groupby(bars26_raw["ts"].dt.date)}
    bars26 = {}
    for k, d in enumerate(days26):
        bars26[d] = ext_arrays(grp26[d], grp26[days26[k - 1]] if k else None)

    e25 = entries_2025()
    e_train, e_hold = e25[e25["split"] == "train"], e25[e25["split"] == "hold"]
    e26 = entries_2026(grp26)
    log.info("entries: train=%d hold=%d 2026=%d", len(e_train), len(e_hold), len(e26))

    log.info("training ML-exit model on train entries…")
    ml_model = train_ml_exit(e_train, bars25)

    CANDIDATES = {
        "fixed_sl (base)": {"stop_mode": "fixed", "ts_min": 60},
        "atr_trail 0.4/0.4": {"stop_mode": "atr_trail", "arm": 0.4, "trail": 0.4, "ts_min": 60},
        "chandelier N10 m2.5": {"stop_mode": "chandelier", "N": 10, "m": 2.5, "ts_min": 60},
        "chandelier N10 m2.0": {"stop_mode": "chandelier", "N": 10, "m": 2.0, "ts_min": 60},
        "supertrend 10/3": {"stop_mode": "supertrend", "ts_min": 60},
        "donchian N10": {"stop_mode": "donchian", "N": 10, "ts_min": 60},
        "swing_low": {"stop_mode": "swing", "ts_min": 60},
        "structure": {"stop_mode": "structure", "ts_min": 60},
        "vwap_target": {"stop_mode": "fixed", "target_mode": "vwap", "tp": 0.8, "ts_min": 60},
        "liquidity_target": {"stop_mode": "fixed", "target_mode": "liquidity", "tp": 1.0, "ts_min": 60},
        "ml_exit tau0.6": {"stop_mode": "fixed", "ml_exit": True, "ml_tau": 0.6, "ts_min": 60},
        "time_based 10m": {"stop_mode": "fixed", "time_exit_min": 10, "ts_min": 60},
        "time_based 20m": {"stop_mode": "fixed", "time_exit_min": 20, "ts_min": 60},
        "hybrid part+chand+time": {"stop_mode": "chandelier", "N": 10, "m": 2.5,
                                   "partial": True, "tp1": 0.4, "time_exit_min": 45, "ts_min": 60},
    }

    results = []
    log.info("\n%-24s | %-52s | %-52s", "EXIT SYSTEM", "HOLDOUT", "2026 BROKER")
    for name, cfg in CANDIDATES.items():
        mh = metrics(run(e_hold, bars25, cfg, ml_model))
        m26 = metrics(run(e26, bars26, cfg, ml_model))
        results.append({"name": name, "cfg": cfg, "hold": mh, "y2026": m26})
        log.info("%-24s | %-52s | %-52s", name, _fmt(mh), _fmt(m26))

    # rank by mean OOS EV (holdout + 2026)
    for r in results:
        evs = [r["hold"].get("ev_r"), r["y2026"].get("ev_r")]
        r["mean_ev"] = np.mean([x for x in evs if x is not None]) if any(evs) else None
    ranked = sorted([r for r in results if r["mean_ev"] is not None],
                    key=lambda x: x["mean_ev"], reverse=True)
    log.info("\n══ RANK by mean OOS EV ══")
    for r in ranked:
        log.info("%-24s meanEV=%+.4fR  (HOLD PF=%s DD=%s | 2026 PF=%s DD=%s)",
                 r["name"], r["mean_ev"], r["hold"].get("pf"), r["hold"].get("max_dd_r"),
                 r["y2026"].get("pf"), r["y2026"].get("max_dd_r"))

    # 10-group stability for top 3
    log.info("\n══ 10-GROUP STABILITY (top 3) ══")
    hold_days = sorted(e_hold["ts"].dt.date.astype(str).unique())
    chunks = np.array_split(np.array(hold_days), 5)
    stability = {}
    for r in ranked[:3]:
        cfg = r["cfg"]
        rows = []
        for gi, ch in enumerate(chunks, 1):
            ent = e_hold[e_hold["ts"].dt.date.astype(str).isin(set(ch))]
            rows.append(metrics(run(ent, bars25, cfg, ml_model)))
        for gi, month in enumerate([2, 3, 4, 5, 6], 6):
            ent = e26[(e26["ts"].dt.year == 2026) & (e26["ts"].dt.month == month)]
            rows.append(metrics(run(ent, bars26, cfg, ml_model)))
        pos = sum(1 for m in rows if m.get("ev_r", -9) and m["ev_r"] > 0)
        wr_band = [m.get("wr") for m in rows if m.get("wr") is not None]
        log.info("%-24s EV>0 in %d/10 | WR %.0f-%.0f%% | per-group EV: %s",
                 r["name"], pos, min(wr_band) * 100, max(wr_band) * 100,
                 " ".join(f"{m.get('ev_r', float('nan')):+.2f}" for m in rows))
        stability[r["name"]] = {"groups_pos": pos, "rows": rows}

    with open(os.path.join(config.MODELS_DIR, "v3_exit_systems.json"), "w") as f:
        json.dump({"results": results, "stability": stability}, f, indent=2, default=str)
    log.info("\nsaved → v3_exit_systems.json")


if __name__ == "__main__":
    main()
