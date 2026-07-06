"""V1 EXIT-OPTIMIZATION STUDY — entry logic frozen, exits only.

Entry set = the frozen high_wr_asymmetric_gate_v1 gated events (chan_rev, vwap_rev,
sweep ML gates + mom_cont base rate). Per-family SL geometry is HELD FIXED
(chan_rev/vwap_rev 2.5×ATR, sweep 2.0, mom_cont 1.5). Only the exit is changed.

Risk unit R = initial SL distance (fixed per trade), so every policy is comparable.
Realistic execution: entry next-bar at ask/bid, exits on the opposite book side,
spread inside the replay, 1pt slippage per fill; conservative intrabar ordering
(adverse extreme assumed before favorable; stops/BE update from prior bars only).

Policies:
  base            V1 as-is (tp0.4×ATR, full SL, 30m stop)
  fixed_tp_X      TP ∈ {0.4,0.5,0.6,0.7,0.8,1.0}×ATR, SL fixed
  partial_be      50% off at tp1=0.4×ATR, stop→breakeven, remainder to tp2 (grid)
  atr_trail       arm at A×ATR, trail T×ATR from favorable peak (grid)
  vol_adj         TP scaled by entry ATR-percentile regime (low/high vol)
  momentum_exit   exit on 2 consecutive adverse closes (cap TP, full SL)
  confidence_exit TP widened with model p_cal above tau (scale grid)

Adaptive params are tuned on 2025-TRAIN entries (max EV), frozen, then reported on
2025-HOLDOUT and 2026 broker candles (both fully OOS for entry gate AND exit param).

Usage: python3 research/v2_exit_study.py
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import sys
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from features.pack import compute_feature_frame, event_features  # noqa: E402
from labels.triple_barrier import compute_atr  # noqa: E402
from triggers.detect import detect_day  # noqa: E402
from research.transfer_test_2026 import fetch_candles, to_bar_frame  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("exit_study")

FROZEN_DIR = os.path.join(config.ENGINE_DIR, "frozen", "high_wr_asymmetric_gate_v1")
with open(os.path.join(FROZEN_DIR, "hp_frozen.json")) as fh:
    FROZEN = json.load(fh)
SPLIT_DAY = date.fromisoformat(FROZEN["split_day"])
SLIP = config.SLIPPAGE_PTS


# ── entry reconstruction (frozen — independent of exit) ──────────────────────

def _score_gate(feats: pd.DataFrame) -> pd.DataFrame:
    """Apply each family's frozen model+tau; return gated entries with sl_atr, p."""
    out = []
    for fam, cfg in FROZEN["families"].items():
        sub = feats[feats["family"] == fam].copy()
        if sub.empty:
            continue
        if cfg["tau"] is None:  # mom_cont base rate — all events enter
            sub["p"] = 1.0
            gated = sub
        else:
            with open(os.path.join(FROZEN_DIR, f"hp_{fam}_cal.pkl"), "rb") as fh:
                cal = pickle.load(fh)
            m = lgb.Booster(model_file=os.path.join(FROZEN_DIR, f"hp_{fam}.txt"))
            sub["p"] = cal["iso"].predict(m.predict(sub[cal["cols"]]))
            gated = sub[sub["p"] >= cfg["tau"]]
        g = gated[["ts", "direction", "family", "p"]].copy()
        g["sl_atr"], g["tau"] = cfg["sl_atr"], (cfg["tau"] if cfg["tau"] is not None else 0.0)
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def entries_2025() -> pd.DataFrame:
    ds = pd.read_parquet(os.path.join(config.EVENTS_DIR, "dataset.parquet"))
    feats = ds.drop_duplicates(subset=["ts", "direction", "family"])
    e = _score_gate(feats)
    e["split"] = np.where(e["ts"].dt.date <= SPLIT_DAY, "train", "hold")
    return e


def entries_2026(bars_by_day: dict) -> pd.DataFrame:
    days = sorted(bars_by_day.keys())
    feat_frames = []
    for i, d in enumerate(days):
        day_bars = bars_by_day[d]
        prev = None if i == 0 else bars_by_day[days[i - 1]]
        ev = detect_day(day_bars, prev, date.fromisoformat(d))
        if ev.empty:
            continue
        ctx = pd.concat([prev, day_bars]).reset_index(drop=True) if prev is not None else day_bars
        fe = event_features(compute_feature_frame(ctx), ev)
        if not fe.empty:
            feat_frames.append(fe)
    feats = pd.concat(feat_frames, ignore_index=True)
    e = _score_gate(feats)
    e["split"] = "y2026"
    return e


# ── bar-array cache per day ──────────────────────────────────────────────────

def day_arrays(bars: pd.DataFrame) -> dict:
    b = bars.sort_values("ts").reset_index(drop=True)
    atr = compute_atr(b).to_numpy()
    return {
        "ts": b["ts"].to_numpy().astype("datetime64[ns]").astype("int64"),
        "ao": b["ask_o"].to_numpy(), "bo": b["bid_o"].to_numpy(),
        "bh": b["bid_h"].to_numpy(), "bl": b["bid_l"].to_numpy(),
        "ah": b["ask_h"].to_numpy(), "al": b["ask_l"].to_numpy(),
        "bc": b["bid_c"].to_numpy(), "ac": b["ask_c"].to_numpy(),
        "mc": b["mid_c"].to_numpy(), "atr": atr,
        "pos": {t: k for k, t in enumerate(b["ts"].to_numpy().astype("datetime64[ns]").astype("int64"))},
    }


GAP_NS = config.GAP_MAX_SILENT_MIN * 60_000_000_000


def _window(A: dict, e: int, ts_min: int):
    """Return (i_entry, j_end, deadline_ns) or None if entry invalid/gapped."""
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


def simulate(A: dict, e: int, direction: str, sl_atr: float, p: float,
             policy: str, prm: dict) -> dict | None:
    """Bar-by-bar exit simulator. Returns {r, win, hold} in risk units, or None if dropped."""
    w = _window(A, e, prm.get("ts_min", 30))
    if w is None:
        return None
    i, deadline, a = w
    is_buy = direction == "BUY"
    entry = A["ao"][i] if is_buy else A["bo"][i]
    sl_dist = sl_atr * a
    if sl_dist <= 0:
        return None
    slip_r = SLIP / sl_dist

    # policy → barrier plan
    tp1 = prm.get("tp_atr", 0.4) * a
    tp2 = prm.get("tp2_atr", prm.get("tp_atr", 0.4)) * a
    if policy == "vol_adj":
        # regime by entry ATR percentile proxy: wider TP in high vol
        tp1 = (prm["tp_lo"] if a < prm["atr_ref"] else prm["tp_hi"]) * a
    if policy == "confidence_exit":
        tp1 = (prm["tp_base"] + max(0.0, p - prm["tau_ref"]) * prm["scale"]) * a

    stop = entry - sl_dist if is_buy else entry + sl_dist
    frac = 1.0                # remaining position
    realized = 0.0            # realized R
    peak = entry              # favorable extreme for trailing
    be_armed = False
    n = len(A["ts"])
    last_ts = A["ts"][i]
    adverse_closes = 0

    def px_fav(j):   # favorable exit price (limit fills) — bid for buy, ask for sell
        return A["bh"][j] if is_buy else A["al"][j]

    def px_adv(j):   # adverse exit price
        return A["bl"][j] if is_buy else A["ah"][j]

    for j in range(i, n):
        if (A["ts"][j] - last_ts) > GAP_NS:
            return None  # gap in window → drop
        last_ts = A["ts"][j]
        hi_fav = px_fav(j)
        lo_adv = px_adv(j)

        # 1) adverse first (conservative): stop / BE hit?
        stop_hit = (lo_adv <= stop) if is_buy else (lo_adv >= stop)
        if stop_hit:
            pnl = (stop - entry) if is_buy else (entry - stop)
            realized += frac * (pnl / sl_dist)
            realized -= frac * slip_r
            r = realized
            return {"r": r, "win": int(r > 0), "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}

        # 2) favorable targets
        if policy in ("partial_be",):
            # TP1 → scale out 50%, move stop to breakeven
            if frac == 1.0:
                tp1_hit = (hi_fav >= entry + tp1) if is_buy else (hi_fav <= entry - tp1)
                if tp1_hit:
                    realized += 0.5 * (tp1 / sl_dist) - 0.5 * slip_r
                    frac = 0.5
                    stop = entry  # breakeven
                    be_armed = True
            else:
                tp2_hit = (hi_fav >= entry + tp2) if is_buy else (hi_fav <= entry - tp2)
                if tp2_hit:
                    realized += 0.5 * (tp2 / sl_dist) - 0.5 * slip_r
                    return {"r": realized, "win": int(realized > 0),
                            "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}
        elif policy == "atr_trail":
            # arm once favorable move >= activate; then trail from peak
            peak = max(peak, hi_fav) if is_buy else min(peak, lo_adv if False else (A["al"][j] if is_buy else A["ah"][j]))
            fav_move = (hi_fav - entry) if is_buy else (entry - hi_fav)
            if fav_move >= prm["activate_atr"] * a:
                if is_buy:
                    peak = max(peak, hi_fav)
                    stop = max(stop, peak - prm["trail_atr"] * a)
                else:
                    peak = min(peak, hi_fav)
                    stop = min(stop, peak + prm["trail_atr"] * a)
            # also honor a hard TP cap if provided
            if prm.get("tp_cap_atr"):
                cap_hit = (hi_fav >= entry + prm["tp_cap_atr"] * a) if is_buy else (hi_fav <= entry - prm["tp_cap_atr"] * a)
                if cap_hit:
                    realized += frac * (prm["tp_cap_atr"] * a / sl_dist) - frac * slip_r
                    return {"r": realized, "win": int(realized > 0),
                            "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}
        elif policy == "momentum_exit":
            tp_hit = (hi_fav >= entry + tp1) if is_buy else (hi_fav <= entry - tp1)
            if tp_hit:
                realized += frac * (tp1 / sl_dist) - frac * slip_r
                return {"r": realized, "win": int(realized > 0),
                        "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}
            if j > i:
                adverse = (A["mc"][j] < A["mc"][j - 1]) if is_buy else (A["mc"][j] > A["mc"][j - 1])
                adverse_closes = adverse_closes + 1 if adverse else 0
                if adverse_closes >= prm.get("mom_bars", 2):
                    exit_px = A["bc"][j] if is_buy else A["ac"][j]
                    pnl = (exit_px - entry) if is_buy else (entry - exit_px)
                    realized += frac * (pnl / sl_dist) - frac * slip_r
                    return {"r": realized, "win": int(realized > 0),
                            "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}
        else:  # fixed_tp / base / vol_adj / confidence_exit
            tp_hit = (hi_fav >= entry + tp1) if is_buy else (hi_fav <= entry - tp1)
            if tp_hit:
                realized += frac * (tp1 / sl_dist) - frac * slip_r
                return {"r": realized, "win": int(realized > 0),
                        "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}

        # 3) time stop
        if A["ts"][j] >= deadline:
            exit_px = A["bc"][j] if is_buy else A["ac"][j]
            pnl = (exit_px - entry) if is_buy else (entry - exit_px)
            realized += frac * (pnl / sl_dist) - frac * slip_r
            return {"r": realized, "win": int(realized > 0),
                    "hold": int((A["ts"][j] - A["ts"][i]) // 60_000_000_000)}
    return None  # ran out of bars


def run_policy(entries: pd.DataFrame, bars_by_day: dict, policy: str, prm: dict) -> pd.DataFrame:
    A_cache = {d: day_arrays(b) for d, b in bars_by_day.items()}
    recs = []
    for _, ev in entries.iterrows():
        d = str(pd.Timestamp(ev["ts"]).date())
        A = A_cache.get(d)
        if A is None:
            continue
        e = A["pos"].get(pd.Timestamp(ev["ts"]).to_datetime64().astype("datetime64[ns]").astype("int64"))
        if e is None:
            continue
        r = simulate(A, int(e), ev["direction"], ev["sl_atr"], ev["p"], policy, prm)
        if r is not None:
            r.update(ts=ev["ts"], family=ev["family"])
            recs.append(r)
    return pd.DataFrame(recs)


def metrics(res: pd.DataFrame) -> dict:
    if res.empty:
        return {"n": 0}
    r = res["r"].to_numpy()
    wins, losses = r[r > 0], r[r <= 0]
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(r) else 0.0
    pf = float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf")
    return {"n": len(r), "wr": round(float((r > 0).mean()), 4), "ev_r": round(float(r.mean()), 4),
            "pf": round(pf, 3), "max_dd_r": round(dd, 2),
            "avg_win": round(float(wins.mean()), 3) if len(wins) else None,
            "avg_loss": round(float(losses.mean()), 3) if len(losses) else None}


def main() -> None:
    # bar sources
    bars25 = {}
    import glob
    for p in sorted(glob.glob(os.path.join(config.BARS_DIR, "*.parquet"))):
        d = os.path.basename(p).replace(".parquet", "")
        bars25[d] = pd.read_parquet(p)
    bars26_all = to_bar_frame(fetch_candles())
    bars26 = {str(d): g.reset_index(drop=True) for d, g in bars26_all.groupby(bars26_all["ts"].dt.date)}

    e25 = entries_2025()
    e26 = entries_2026(bars26)
    e_train = e25[e25["split"] == "train"]
    e_hold = e25[e25["split"] == "hold"]
    log.info("frozen entries: train=%d hold=%d 2026=%d", len(e_train), len(e_hold), len(e26))

    def evaluate(policy, prm, tag):
        rows = {}
        for name, ent, bars in (("train(IS)", e_train, bars25), ("HOLDOUT", e_hold, bars25),
                                ("2026", e26, bars26)):
            rows[name] = metrics(run_policy(ent, bars, policy, prm))
        log.info("%-34s | HOLD %s | 2026 %s", tag,
                 _fmt(rows["HOLDOUT"]), _fmt(rows["2026"]))
        return {"policy": policy, "prm": prm, "tag": tag, **{k: rows[k] for k in rows}}

    results = []
    log.info("\n══ FIXED-TP SWEEP (SL fixed per family) ══")
    for tp in (0.4, 0.5, 0.6, 0.7, 0.8, 1.0):
        results.append(evaluate("fixed_tp", {"tp_atr": tp, "ts_min": 30},
                                f"fixed_tp {tp}xATR"))

    log.info("\n══ PARTIAL + BREAKEVEN (50%% at 0.4, stop→BE, remainder→tp2) ══")
    best = None
    for tp2 in (0.8, 1.2, 1.6, 2.0):
        r = run_policy(e_train, bars25, "partial_be", {"tp_atr": 0.4, "tp2_atr": tp2, "ts_min": 30})
        m = metrics(r)
        if best is None or (m.get("ev_r", -9) or -9) > best[1]:
            best = (tp2, m.get("ev_r", -9))
    log.info("  [train-selected tp2=%.1f]", best[0])
    results.append(evaluate("partial_be", {"tp_atr": 0.4, "tp2_atr": best[0], "ts_min": 30},
                            f"partial_be tp2={best[0]}"))

    log.info("\n══ ATR TRAILING STOP (arm A, trail T; tuned on train) ══")
    best = None
    for act in (0.3, 0.4, 0.6):
        for tr in (0.4, 0.6, 0.8):
            m = metrics(run_policy(e_train, bars25, "atr_trail",
                                   {"activate_atr": act, "trail_atr": tr, "ts_min": 60}))
            if best is None or (m.get("ev_r", -9) or -9) > best[2]:
                best = (act, tr, m.get("ev_r", -9))
    log.info("  [train-selected activate=%.1f trail=%.1f]", best[0], best[1])
    results.append(evaluate("atr_trail", {"activate_atr": best[0], "trail_atr": best[1], "ts_min": 60},
                            f"atr_trail arm={best[0]} trail={best[1]}"))

    log.info("\n══ VOLATILITY-ADJUSTED TP (low/high ATR regime) ══")
    atr_ref = float(np.nanmedian([day_arrays(b)["atr"][~np.isnan(day_arrays(b)["atr"])].mean()
                                  for b in list(bars25.values())[:40]]))
    results.append(evaluate("vol_adj", {"tp_lo": 0.4, "tp_hi": 0.8, "atr_ref": atr_ref, "ts_min": 30},
                            "vol_adj tp lo0.4/hi0.8"))

    log.info("\n══ MOMENTUM EXIT (2 adverse closes; TP0.6 cap, full SL) ══")
    results.append(evaluate("momentum_exit", {"tp_atr": 0.6, "mom_bars": 2, "ts_min": 30},
                            "momentum_exit 2bars tp0.6"))

    log.info("\n══ CONFIDENCE-SCALED TP (tp = 0.4 + (p-tau)*scale) ══")
    best = None
    for sc in (1.0, 2.0, 4.0):
        m = metrics(run_policy(e_train, bars25, "confidence_exit",
                               {"tp_base": 0.4, "tau_ref": 0.6, "scale": sc, "ts_min": 30}))
        if best is None or (m.get("ev_r", -9) or -9) > best[1]:
            best = (sc, m.get("ev_r", -9))
    log.info("  [train-selected scale=%.1f]", best[0])
    results.append(evaluate("confidence_exit", {"tp_base": 0.4, "tau_ref": 0.6, "scale": best[0], "ts_min": 30},
                            f"confidence_exit scale={best[0]}"))

    with open(os.path.join(config.MODELS_DIR, "v1_exit_study.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    log.info("\nsaved → v1_exit_study.json")


def _fmt(m: dict) -> str:
    if not m or m.get("n", 0) == 0:
        return "n=0"
    return (f"n={m['n']:4d} WR={m['wr']*100:5.1f}% EV={m['ev_r']:+.3f}R PF={m['pf']:.2f} "
            f"DD={m['max_dd_r']:.1f} aw={m['avg_win']} al={m['avg_loss']}")


if __name__ == "__main__":
    main()
