"""
Hold-out paper-trade backtest for XAUUSD v2 model.

Two strategies are evaluated on the same entry signals:

  TEST A — User spec: fixed TP=$10 / SL=$15
  TEST B — Adaptive (regime-aware ATR + breakeven trailing):
      base:    TP=1.5×ATR_M30, SL=1.0×ATR_M30
      ADX_H4 ≥ 25 (trending): TP=2.0×ATR, SL=1.0×ATR  → let trend run
      ADX_H4 < 18 (ranging):  TP=0.8×ATR, SL=0.6×ATR  → quick scalp
      breakeven trail: when price moves +0.5×ATR in favor, SL → entry  (kills TP_GREED_REVERSAL)

Execution path simulation uses M5 bars (5x finer than M30 entries) to detect TP/SL hit order.
Hold-out window: last 60 days of M30 data — fully outside the training set
(training stops `horizon_bars` before the data ends; hold-out is fully forward).

Run:
    python xauusdegitim/backtest.py [--days 60] [--threshold 0.60] [--margin 0.05]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loader import load_xauusd, load_macros  # noqa: E402
from features import build_dataset, atr  # noqa: E402

ART = Path(__file__).resolve().parent / "artifacts"


@dataclass
class Trade:
    entry_time: pd.Timestamp
    direction: str        # "BUY" or "SELL"
    confidence: float
    entry: float
    initial_tp: float
    initial_sl: float
    atr_entry: float
    adx_h4_entry: float
    # filled after exec
    exit_time: pd.Timestamp | None = None
    exit_price: float | None = None
    pnl_dollars: float | None = None
    outcome: str | None = None       # "TP" / "SL" / "TIMEOUT" / "BE_TRAIL"
    bars_held: int | None = None


def simulate_trade_fixed(entry_t: pd.Timestamp, direction: str, entry: float,
                          tp_dollars: float, sl_dollars: float,
                          m5: pd.DataFrame, horizon_min: int) -> tuple[str, float, pd.Timestamp, int]:
    """Walk M5 bars after entry_t until TP, SL, or horizon."""
    if direction == "BUY":
        tp = entry + tp_dollars
        sl = entry - sl_dollars
    else:
        tp = entry - tp_dollars
        sl = entry + sl_dollars
    end_t = entry_t + pd.Timedelta(minutes=horizon_min)
    path = m5.loc[(m5.index > entry_t) & (m5.index <= end_t)]
    for i, (t, row) in enumerate(path.iterrows()):
        if direction == "BUY":
            if row["low"] <= sl:
                return "SL", -sl_dollars, t, i + 1
            if row["high"] >= tp:
                return "TP", +tp_dollars, t, i + 1
        else:
            if row["high"] >= sl:
                return "SL", -sl_dollars, t, i + 1
            if row["low"] <= tp:
                return "TP", +tp_dollars, t, i + 1
    if path.empty:
        return "TIMEOUT", 0.0, end_t, 0
    last_close = float(path["close"].iloc[-1])
    pnl = (last_close - entry) if direction == "BUY" else (entry - last_close)
    return "TIMEOUT", pnl, path.index[-1], len(path)


def simulate_trade_adaptive(entry_t: pd.Timestamp, direction: str, entry: float,
                             atr_v: float, adx_h4: float,
                             m5: pd.DataFrame, horizon_min: int) -> tuple[str, float, pd.Timestamp, int]:
    """Adaptive TP/SL with breakeven trailing."""
    if adx_h4 >= 25:
        tp_mult, sl_mult = 2.0, 1.0
    elif adx_h4 < 18:
        tp_mult, sl_mult = 0.8, 0.6
    else:
        tp_mult, sl_mult = 1.5, 1.0
    tp_dist = tp_mult * atr_v
    sl_dist = sl_mult * atr_v
    be_trigger = 0.5 * atr_v

    if direction == "BUY":
        tp_price = entry + tp_dist
        sl_price = entry - sl_dist
    else:
        tp_price = entry - tp_dist
        sl_price = entry + sl_dist

    end_t = entry_t + pd.Timedelta(minutes=horizon_min)
    path = m5.loc[(m5.index > entry_t) & (m5.index <= end_t)]
    be_active = False
    for i, (t, row) in enumerate(path.iterrows()):
        if direction == "BUY":
            # Trail SL to BE once price has moved +be_trigger in favor
            if not be_active and row["high"] - entry >= be_trigger:
                sl_price = entry  # move stop to breakeven
                be_active = True
            if row["low"] <= sl_price:
                pnl = sl_price - entry  # 0 if be triggered, else -sl_dist
                return ("BE_TRAIL" if be_active and abs(pnl) < 1e-6 else "SL"), pnl, t, i + 1
            if row["high"] >= tp_price:
                return "TP", tp_price - entry, t, i + 1
        else:
            if not be_active and entry - row["low"] >= be_trigger:
                sl_price = entry
                be_active = True
            if row["high"] >= sl_price:
                pnl = entry - sl_price
                return ("BE_TRAIL" if be_active and abs(pnl) < 1e-6 else "SL"), pnl, t, i + 1
            if row["low"] <= tp_price:
                return "TP", entry - tp_price, t, i + 1
    if path.empty:
        return "TIMEOUT", 0.0, end_t, 0
    last_close = float(path["close"].iloc[-1])
    pnl = (last_close - entry) if direction == "BUY" else (entry - last_close)
    return "TIMEOUT", pnl, path.index[-1], len(path)


def summarize(trades: list[Trade], label: str) -> dict:
    if not trades:
        return {"label": label, "n": 0}
    n = len(trades)
    pnls = np.array([t.pnl_dollars for t in trades if t.pnl_dollars is not None])
    wins = pnls > 0
    sl_hits = sum(1 for t in trades if t.outcome == "SL")
    tp_hits = sum(1 for t in trades if t.outcome == "TP")
    be = sum(1 for t in trades if t.outcome == "BE_TRAIL")
    timeouts = sum(1 for t in trades if t.outcome == "TIMEOUT")
    by_dir = {"BUY": [t for t in trades if t.direction == "BUY"],
              "SELL": [t for t in trades if t.direction == "SELL"]}
    dir_stats = {}
    for d, ts in by_dir.items():
        if not ts:
            dir_stats[d] = {"n": 0}
            continue
        ps = np.array([t.pnl_dollars for t in ts])
        dir_stats[d] = {
            "n": len(ts),
            "win_rate": float((ps > 0).mean()),
            "total_pnl": float(ps.sum()),
            "avg_pnl": float(ps.mean()),
            "tp_hits": sum(1 for t in ts if t.outcome == "TP"),
            "sl_hits": sum(1 for t in ts if t.outcome == "SL"),
            "be_hits": sum(1 for t in ts if t.outcome == "BE_TRAIL"),
        }
    return {
        "label": label,
        "n": n,
        "win_rate": float(wins.mean()),
        "total_pnl_$": float(pnls.sum()),
        "avg_pnl_$": float(pnls.mean()),
        "max_drawdown_$": float(min(np.minimum.accumulate(np.cumsum(pnls)))),
        "tp_rate": tp_hits / n,
        "sl_rate": sl_hits / n,
        "be_trail_rate": be / n,
        "timeout_rate": timeouts / n,
        "expectancy_$": float(pnls.mean()),
        "by_direction": dir_stats,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60, help="Hold-out window in days (last N days of data)")
    ap.add_argument("--threshold", type=float, default=0.60, help="Min calibrated probability to enter")
    ap.add_argument("--margin", type=float, default=0.05, help="Min margin between BUY and SELL probs")
    ap.add_argument("--horizon-min", type=int, default=720, help="Max trade duration in minutes (12h)")
    ap.add_argument("--cooldown-min", type=int, default=60, help="Min minutes between same-direction entries")
    args = ap.parse_args()

    print(f"Loading model from {ART / 'model_xauusd_v2.joblib'}...")
    bundle = joblib.load(ART / "model_xauusd_v2.joblib")
    feat_cols = bundle["feature_columns"]

    print("Loading raw data...")
    xau = load_xauusd(broker_offset_h=3)
    macros = load_macros()
    print("Building features...")
    X, y = build_dataset(xau["M30"], xau["H1"], xau["H4"], macros=macros,
                         horizon_bars=bundle["config"]["horizon_bars"])
    # ATR on M30 for adaptive sizing
    atr_m30 = atr(xau["M30"]["high"], xau["M30"]["low"], xau["M30"]["close"], 14)
    # ADX_H4 already in X
    adx_h4 = X["adx_H4"]

    # Hold-out: last `days` of M30 timestamps
    cutoff = X.index.max() - pd.Timedelta(days=args.days)
    holdout = X[X.index >= cutoff]
    valid = holdout[feat_cols].dropna().index
    print(f"\nHold-out window: {cutoff} → {X.index.max()}  ({len(valid)} usable bars)")

    # Predict on hold-out
    Xh = X.loc[valid, feat_cols]
    p_buy_raw = bundle["buy_model"].predict_proba(Xh)[:, 1]
    p_sell_raw = bundle["sell_model"].predict_proba(Xh)[:, 1]
    p_buy = bundle["buy_calibrator"].transform(p_buy_raw)
    p_sell = bundle["sell_calibrator"].transform(p_sell_raw)

    print(f"  P(BUY) mean={p_buy.mean():.3f}  P(SELL) mean={p_sell.mean():.3f}")
    print(f"  Bars where max(p) ≥ {args.threshold}: {((np.maximum(p_buy, p_sell) >= args.threshold)).sum()}")

    # Generate entries with cooldown
    entries: list[tuple[pd.Timestamp, str, float, float, float, float]] = []  # (t, dir, conf, entry, atr, adx)
    last_entry: dict[str, pd.Timestamp] = {}
    cooldown = pd.Timedelta(minutes=args.cooldown_min)
    m30_close = xau["M30"]["close"]

    for i, t in enumerate(valid):
        pb, ps = p_buy[i], p_sell[i]
        if max(pb, ps) < args.threshold:
            continue
        if abs(pb - ps) < args.margin:
            continue
        direction = "BUY" if pb > ps else "SELL"
        last = last_entry.get(direction)
        if last is not None and (t - last) < cooldown:
            continue
        entry_price = float(m30_close.loc[t])
        atr_v = float(atr_m30.loc[t]) if t in atr_m30.index else float("nan")
        adx_v = float(adx_h4.loc[t]) if t in adx_h4.index else float("nan")
        if not (np.isfinite(atr_v) and np.isfinite(adx_v) and atr_v > 0):
            continue
        conf = float(max(pb, ps))
        entries.append((t, direction, conf, entry_price, atr_v, adx_v))
        last_entry[direction] = t

    print(f"\nGenerated {len(entries)} entries (after threshold/margin/cooldown)")

    if not entries:
        print("No trades generated — check threshold/margin or hold-out window.")
        return

    m5 = xau["M5"]

    # Run TEST A and TEST B
    trades_a: list[Trade] = []
    trades_b: list[Trade] = []
    for t, d, conf, entry, atr_v, adx_v in entries:
        # TEST A: fixed $10/$15
        out_a, pnl_a, exit_t_a, bars_a = simulate_trade_fixed(t, d, entry, 10.0, 15.0, m5, args.horizon_min)
        trade_a = Trade(entry_time=t, direction=d, confidence=conf, entry=entry,
                        initial_tp=entry + (10 if d == "BUY" else -10),
                        initial_sl=entry - (15 if d == "BUY" else -15),
                        atr_entry=atr_v, adx_h4_entry=adx_v,
                        exit_time=exit_t_a, exit_price=entry + pnl_a if d == "BUY" else entry - pnl_a,
                        pnl_dollars=pnl_a, outcome=out_a, bars_held=bars_a)
        trades_a.append(trade_a)

        # TEST B: adaptive
        out_b, pnl_b, exit_t_b, bars_b = simulate_trade_adaptive(t, d, entry, atr_v, adx_v, m5, args.horizon_min)
        trade_b = Trade(entry_time=t, direction=d, confidence=conf, entry=entry,
                        initial_tp=float("nan"), initial_sl=float("nan"),
                        atr_entry=atr_v, adx_h4_entry=adx_v,
                        exit_time=exit_t_b,
                        exit_price=entry + pnl_b if d == "BUY" else entry - pnl_b,
                        pnl_dollars=pnl_b, outcome=out_b, bars_held=bars_b)
        trades_b.append(trade_b)

    summary_a = summarize(trades_a, "Test A — fixed $10/$15")
    summary_b = summarize(trades_b, "Test B — adaptive ATR + BE trailing")

    def fmt(s):
        if s["n"] == 0:
            return "  (no trades)"
        out = []
        out.append(f"  trades: {s['n']}")
        out.append(f"  win-rate: {s['win_rate']:.3f}")
        out.append(f"  total P/L: ${s['total_pnl_$']:+.2f}")
        out.append(f"  avg P/L per trade: ${s['avg_pnl_$']:+.3f}")
        out.append(f"  max drawdown: ${s['max_drawdown_$']:+.2f}")
        out.append(f"  TP/SL/BE/Timeout: {s['tp_rate']:.2%} / {s['sl_rate']:.2%} / "
                   f"{s['be_trail_rate']:.2%} / {s['timeout_rate']:.2%}")
        for d, ds in s["by_direction"].items():
            if ds["n"] == 0:
                continue
            out.append(f"  {d}: n={ds['n']}  win={ds['win_rate']:.3f}  total=${ds['total_pnl']:+.2f}  "
                       f"TP={ds['tp_hits']} SL={ds['sl_hits']} BE={ds['be_hits']}")
        return "\n".join(out)

    print(f"\n=== {summary_a['label']} ===")
    print(fmt(summary_a))
    print(f"\n=== {summary_b['label']} ===")
    print(fmt(summary_b))

    # Persist
    out = {
        "config": {**vars(args), "threshold": args.threshold, "margin": args.margin,
                   "model_config": bundle["config"]},
        "test_a_fixed": summary_a,
        "test_b_adaptive": summary_b,
        "n_entries": len(entries),
        "holdout_start": str(cutoff), "holdout_end": str(X.index.max()),
    }
    (ART / "backtest_report.json").write_text(json.dumps(out, indent=2, default=str))
    # Also dump per-trade CSVs for inspection
    pd.DataFrame([t.__dict__ for t in trades_a]).to_csv(ART / "trades_test_a.csv", index=False)
    pd.DataFrame([t.__dict__ for t in trades_b]).to_csv(ART / "trades_test_b.csv", index=False)
    print(f"\nSaved → {ART / 'backtest_report.json'}")
    print(f"Per-trade CSVs → trades_test_a.csv, trades_test_b.csv")


if __name__ == "__main__":
    main()
