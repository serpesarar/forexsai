#!/usr/bin/env python3
"""Offline, decision-time audit of recorded trades and one-minute bars."""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import os
import statistics
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BAR_SECONDS = 60
HISTORY_BARS = 100
MAX_STALENESS_SECONDS = 300
MAX_GAP_SECONDS = 300
SPLIT_FRACTION = 0.70
Z_95 = 1.959963984540054
# Clock shifts (minutes) scanned by the alignment check. MT5 exports in this
# project have been mislabeled by broker offset (+180) and by a bad offset
# detection (+1230), so both are covered.
ALIGNMENT_SHIFTS_MIN = (-1230, -180, -120, -60, -5, -1, 0, 1, 5, 60, 120, 180, 1230)
MIN_ALIGNMENT_SAMPLES = 10
# MT5 deal export (box_export_trades_30d.py) column -> audit trade field.
MT5_CSV_FIELDS = {"position_id": "pid", "open_time_utc": "entry_time",
                  "close_time_utc": "exit_time", "open_price": "entry_px",
                  "close_price": "exit_px", "volume": "lot", "tp_price": "tp_px",
                  "comment_in": "strategy_tag"}


def utc_timestamp(value: str) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timezone required in timestamp: {value}")
    return parsed.astimezone(timezone.utc).timestamp()


def load_bars(path: Path) -> list[dict[str, float]]:
    """Accept ``ts`` (Unix seconds) or MT5 export ``time_utc`` (ISO, bar start)."""
    with path.open(newline="", encoding="utf-8") as handle:
        bars = [
            {"ts": float(row["ts"]) if row.get("ts") else utc_timestamp(row["time_utc"]),
             **{key: float(row[key]) for key in ("open", "high", "low", "close")}}
            for row in csv.DictReader(handle)
        ]
    bars.sort(key=lambda bar: bar["ts"])
    if len({bar["ts"] for bar in bars}) != len(bars):
        raise ValueError("bar timestamps must be unique")
    if any(bar["high"] < max(bar["open"], bar["close"], bar["low"])
           or bar["low"] > min(bar["open"], bar["close"], bar["high"])
           for bar in bars):
        raise ValueError("invalid OHLC bar")
    return bars


def load_mt5_csv_trades(path: Path) -> list[dict[str, Any]]:
    """Read an MT5 deal export; pnl is net of commission and swap.

    The export's ``sl_price`` is the stop at close time and may have been moved
    by breakeven/runner management, so it is kept only as visual context and
    never becomes pre-entry risk.
    """
    trades = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            trade: dict[str, Any] = {dst: row[src] for src, dst in MT5_CSV_FIELDS.items()
                                     if row.get(src) not in (None, "")}
            for field in ("entry_px", "exit_px", "lot", "tp_px"):
                if field in trade:
                    trade[field] = float(trade[field])
            if row.get("sl_price"):
                trade["sl_px"] = float(row["sl_price"])
            trade["pnl"] = sum(float(row.get(col) or 0)
                               for col in ("profit", "commission", "swap"))
            trade["direction"] = row["direction"].upper()
            trades.append(trade)
    return trades


def load_trades(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        trades: Any = load_mt5_csv_trades(path)
    else:
        trades = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(trades, list):
        raise ValueError("trades JSON must be a list")
    required = {"pid", "direction", "entry_time", "exit_time", "entry_px", "exit_px", "pnl"}
    seen: set[str] = set()
    for row in trades:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"trade missing fields: {sorted(missing)}")
        pid = str(row["pid"])
        if pid in seen:
            raise ValueError(f"duplicate trade pid: {pid}")
        seen.add(pid)
        if row["direction"] not in ("BUY", "SELL"):
            raise ValueError(f"invalid direction for {pid}")
        if utc_timestamp(row["exit_time"]) < utc_timestamp(row["entry_time"]):
            raise ValueError(f"exit precedes entry for {pid}")
        for field in ("entry_px", "exit_px", "pnl"):
            if not math.isfinite(float(row[field])):
                raise ValueError(f"non-finite {field} for {pid}")
    return sorted(trades, key=lambda row: utc_timestamp(row["entry_time"]))


def ema(values: list[float], span: int) -> float:
    alpha = 2.0 / (span + 1)
    current = values[0]
    for value in values[1:]:
        current = alpha * value + (1 - alpha) * current
    return current


def decision_features(
    trade: dict[str, Any], bars: list[dict[str, float]], timestamps: list[float]
) -> dict[str, Any] | None:
    """Use only fully closed one-minute bars preceding the entry timestamp."""
    entry_ts = utc_timestamp(trade["entry_time"])
    last = bisect.bisect_right(timestamps, entry_ts - BAR_SECONDS) - 1
    if last + 1 < HISTORY_BARS:
        return None
    window = bars[last - HISTORY_BARS + 1:last + 1]
    if entry_ts - (window[-1]["ts"] + BAR_SECONDS) > MAX_STALENESS_SECONDS:
        return None
    if any(right["ts"] - left["ts"] > MAX_GAP_SECONDS
           for left, right in zip(window, window[1:])):
        return None

    closes = [bar["close"] for bar in window]
    true_ranges = [
        max(bar["high"] - bar["low"], abs(bar["high"] - prev["close"]),
            abs(bar["low"] - prev["close"]))
        for prev, bar in zip(window[-15:-1], window[-14:])
    ]
    atr14 = statistics.mean(true_ranges)
    if atr14 <= 0:
        return None
    ema20, ema50 = ema(closes, 20), ema(closes, 50)
    sign = 1 if trade["direction"] == "BUY" else -1
    trend = sign * (ema20 - ema50) > 0
    momentum = sign * (closes[-1] - closes[-6]) > 0
    position = sign * (closes[-1] - ema20) > 0
    # Upper case = aligned, e.g. "tMP" = against the slow trend but momentum and
    # price-vs-EMA20 agree. The score alone hides which condition is missing.
    combo = "".join(flag.upper() if ok else flag
                    for flag, ok in (("t", trend), ("m", momentum), ("p", position)))
    return {
        "decision_bar_ts": window[-1]["ts"],
        "ema20": round(ema20, 6),
        "ema50": round(ema50, 6),
        "atr14": round(atr14, 6),
        "trend_aligned": trend,
        "momentum_aligned": momentum,
        "price_aligned": position,
        "confluence_score": sum((trend, momentum, position)),
        "combo": combo,
    }


def alignment_check(trades: list[dict[str, Any]], bars: list[dict[str, float]]) -> dict[str, Any]:
    """Find the clock shift at which fill prices best track the bar series.

    Uses the spread (IQR) of ``entry_px - bar close`` rather than the level, so
    a constant price-basis offset between feeds (broker vs backend) does not
    look like a time error. A best shift other than 0 means the trade and bar
    clocks disagree and every decision-time feature is misaligned.
    """
    closes = {int(bar["ts"]): bar["close"] for bar in bars}
    scan: dict[str, float] = {}
    for shift in ALIGNMENT_SHIFTS_MIN:
        diffs = []
        for trade in trades:
            minute = int(utc_timestamp(trade["entry_time"]) // BAR_SECONDS * BAR_SECONDS)
            close = closes.get(minute + shift * 60)
            if close is not None:
                diffs.append(float(trade["entry_px"]) - close)
        if len(diffs) >= MIN_ALIGNMENT_SAMPLES:
            quartiles = statistics.quantiles(diffs, n=4)
            scan[str(shift)] = round(quartiles[2] - quartiles[0], 4)
    if not scan:
        return {"status": "insufficient_overlap", "best_shift_min": None, "iqr_by_shift": {}}
    best = min(scan, key=scan.get)
    return {"status": "ok" if best == "0" else "MISALIGNED",
            "best_shift_min": int(best), "iqr_by_shift": scan}


def wilson_interval(wins: int, count: int) -> tuple[float, float] | None:
    if count == 0:
        return None
    p = wins / count
    z2 = Z_95 * Z_95
    denominator = 1 + z2 / count
    center = (p + z2 / (2 * count)) / denominator
    half = Z_95 * math.sqrt(p * (1 - p) / count + z2 / (4 * count * count)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def max_drawdown(values: list[float]) -> float | None:
    if not values:
        return None
    equity = peak = worst = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def realized_r(trade: dict[str, Any], point_value: float | None) -> float | None:
    """Calculate R only from explicit pre-entry risk, never inferred geometry."""
    risk_cash = float(trade.get("risk_cash") or 0)
    if risk_cash <= 0 and trade.get("sl_dist_verified") is True and point_value is not None:
        risk_cash = float(trade.get("lot") or 0) * float(trade.get("sl_dist") or 0) * point_value
    return float(trade["pnl"]) / risk_cash if risk_cash > 0 else None


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = [row for row in rows if row["win"] is not None]
    wins = sum(row["win"] for row in resolved)
    r_values = [row["estimated_r"] for row in rows if row["estimated_r"] is not None]
    interval = wilson_interval(wins, len(resolved))
    return {
        "n": len(rows),
        # Split-leg positions opened in the same minute are one decision, not
        # independent evidence; compare n with this before trusting an interval.
        "decisions_n": len({(row["entry_time"][:16], row.get("direction")) for row in rows}),
        "resolved_n": len(resolved),
        "neutral_n": len(rows) - len(resolved),
        "wins": wins,
        "win_rate": round(wins / len(resolved), 4) if resolved else None,
        "win_rate_wilson_95": [round(v, 4) for v in interval] if interval else None,
        "r_covered_n": len(r_values),
        "estimated_mean_r": round(statistics.mean(r_values), 4) if r_values else None,
        "estimated_max_drawdown_r": round(max_drawdown(r_values), 4) if r_values else None,
        "pnl_sum_account_currency": round(sum(float(row["pnl"]) for row in rows), 2),
    }


RULES = {
    "all_eligible": lambda row: True,
    "trend_aligned": lambda row: row["trend_aligned"],
    "momentum_aligned": lambda row: row["momentum_aligned"],
    "confluence_2plus": lambda row: row["confluence_score"] >= 2,
    "confluence_3of3": lambda row: row["confluence_score"] == 3,
}


def evaluate(trades: list[dict[str, Any]]) -> dict[str, Any]:
    if len(trades) < 4:
        raise ValueError("at least four eligible trades are needed for a chronological split")
    split_index = max(1, min(len(trades) - 1, int(len(trades) * SPLIT_FRACTION)))
    test_start = utc_timestamp(trades[split_index]["entry_time"])
    train = [row for row in trades[:split_index]
             if utc_timestamp(row["exit_time"]) <= test_start]
    test = trades[split_index:]
    result: dict[str, Any] = {
        "split_start_utc": datetime.fromtimestamp(test_start, timezone.utc).isoformat(),
        "train_n": len(train),
        "embargoed_n": split_index - len(train),
        "test_n": len(test),
        "rules": {},
        "score_buckets": {},
        "combo_buckets": {},
    }
    for name, predicate in RULES.items():
        result["rules"][name] = {
            "train": metrics([row for row in train if predicate(row)]),
            "test": metrics([row for row in test if predicate(row)]),
        }
    for score in range(4):
        result["score_buckets"][str(score)] = {
            "train": metrics([row for row in train if row["confluence_score"] == score]),
            "test": metrics([row for row in test if row["confluence_score"] == score]),
        }
    for combo in sorted({row["combo"] for row in trades if "combo" in row}):
        result["combo_buckets"][combo] = {
            "train": metrics([row for row in train if row.get("combo") == combo]),
            "test": metrics([row for row in test if row.get("combo") == combo]),
        }
    return result


def chart_examples(
    trades: list[dict[str, Any]], bars: list[dict[str, float]], out: Path, symbol: str
) -> list[str]:
    examples = []
    for target in (True, False):
        selected = next((row for row in trades if row["win"] is target), None)
        if selected is not None:
            examples.append(selected)
    if not examples:
        return []

    os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
    os.environ.setdefault("XDG_CACHE_HOME", tempfile.gettempdir())
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(examples), 1, figsize=(12, 4.2 * len(examples)), squeeze=False)
    for axis, row in zip(axes[:, 0], examples):
        entry, exit_ = utc_timestamp(row["entry_time"]), utc_timestamp(row["exit_time"])
        visible = [bar for bar in bars if entry - 30 * 60 <= bar["ts"] <= exit_ + 10 * 60]
        if len(visible) > 800:
            step = math.ceil(len(visible) / 800)
            visible = visible[::step] + [visible[-1]]
        dates = [datetime.fromtimestamp(bar["ts"] + BAR_SECONDS, timezone.utc) for bar in visible]
        axis.plot(dates, [bar["close"] for bar in visible], color="#2866a0", lw=1.15)
        entry_dt = datetime.fromtimestamp(entry, timezone.utc)
        exit_dt = datetime.fromtimestamp(exit_, timezone.utc)
        axis.scatter([entry_dt, exit_dt], [row["entry_px"], row["exit_px"]],
                     c=["#212121", "#167a4b" if row["win"] else "#ba3b3b"],
                     s=45, zorder=4)
        axis.axvline(entry_dt, color="#555555", ls="--", lw=0.9)
        axis.axhline(row["entry_px"], color="#666666", ls=":", lw=0.8)
        for field, label, color in (("tp_px", "TP", "#167a4b"),
                                     ("sl_px", "SL", "#ba3b3b")):
            if row.get(field) is not None:
                axis.axhline(float(row[field]), color=color, ls="--", lw=0.8,
                             label=f"{label} (recorded/inferred)")
        axis.set_title(
            f"{symbol} {row['direction']} | pid {row['pid']} | "
            f"{'WIN' if row['win'] else 'LOSS'} | confluence {row['confluence_score']}/3"
        )
        axis.set_ylabel("Price")
        axis.grid(alpha=0.22)
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %H:%M", tz=timezone.utc))
        axis.text(0.01, 0.02,
                  "Decision-time: " + ", ".join(
                      f"{name}={'yes' if row[name] else 'no'}"
                      for name in ("trend_aligned", "momentum_aligned", "price_aligned")
                  ), transform=axis.transAxes, fontsize=8, va="bottom",
                  bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none"})
        if row.get("tp_px") is not None or row.get("sl_px") is not None:
            axis.legend(loc="upper left", fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / "trade_examples.png", dpi=150)
    plt.close(fig)
    return [str(row["pid"]) for row in examples]


def metric_text(value: float | None, percent: bool = False) -> str:
    if value is None:
        return "—"
    return f"{100 * value:.1f}%" if percent else f"{value:+.3f}R"


def write_report(out: Path, summary: dict[str, Any]) -> None:
    evaluation = summary["evaluation"]
    lines = [
        f"# {summary['symbol']} offline trade-edge pilot",
        "",
        "**Status: EXPLORATORY — no live strategy or gate approval.**",
        "",
        f"Sources: `{summary['trades_path']}` and `{summary['bars_path']}`. "
        "Win rate uses actual recorded PnL sign (zero PnL is neutral); R is "
        "shown only where the input supplies exact pre-entry `risk_cash` or an "
        "explicitly verified stop distance and point value.",
        "",
        f"- Trades in file: {summary['input_trades']}; decision-time bar coverage: "
        f"{summary['eligible_trades']}; excluded for missing/stale/gapped history: "
        f"{summary['excluded_trades']}.",
        f"- Date range (UTC): {summary['first_entry_utc']} to {summary['last_entry_utc']}.",
        f"- Clock alignment (fill price vs bar close): **{summary['alignment']['status']}**, "
        f"best shift {summary['alignment']['best_shift_min']} min.",
        f"- Chronological test begins {evaluation['split_start_utc']}; train "
        f"{evaluation['train_n']}, embargoed crossing outcomes "
        f"{evaluation['embargoed_n']}, test {evaluation['test_n']}.",
        "",
        "## Predefined filters (unchanged across the split)",
        "",
        "| Filter | Train n | Train WR | Test n | Test WR | Test Wilson 95% | "
        "Test mean R* | Test R coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, value in evaluation["rules"].items():
        tr, te = value["train"], value["test"]
        ci = te["win_rate_wilson_95"]
        ci_text = f"{100 * ci[0]:.1f}–{100 * ci[1]:.1f}%" if ci else "—"
        lines.append(
            f"| {name} | {tr['n']} | {metric_text(tr['win_rate'], True)} | "
            f"{te['n']} | {metric_text(te['win_rate'], True)} | {ci_text} | "
            f"{metric_text(te['estimated_mean_r'])} | {te['r_covered_n']}/{te['n']} |"
        )
    lines += [
        "",
        "*R uses verified pre-entry risk only; missing R is not treated as zero. "
        "The interval assumes independent trades; "
        "overlapping positions can make it too narrow.*",
        "",
        "## Confluence score across eligible trades",
        "",
        "| Score | Train n | Train WR | Test n | Test WR | Test Wilson 95% |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for score, value in evaluation["score_buckets"].items():
        tr, te = value["train"], value["test"]
        ci = te["win_rate_wilson_95"]
        ci_text = f"{100 * ci[0]:.1f}–{100 * ci[1]:.1f}%" if ci else "—"
        lines.append(
            f"| {score}/3 | {tr['n']} | {metric_text(tr['win_rate'], True)} | "
            f"{te['n']} | {metric_text(te['win_rate'], True)} | {ci_text} |"
        )
    lines += [
        "",
        "## Condition combinations (T/M/P upper case = aligned)",
        "",
        "| Combo | Train n | Train WR | Test n (decisions) | Test WR | Test PnL |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for combo, value in evaluation["combo_buckets"].items():
        tr, te = value["train"], value["test"]
        lines.append(
            f"| {combo} | {tr['n']} | {metric_text(tr['win_rate'], True)} | "
            f"{te['n']} ({te['decisions_n']}) | {metric_text(te['win_rate'], True)} | "
            f"{te['pnl_sum_account_currency']:+.0f} |"
        )
    lines += [
        "",
        "## Interpretation and next validation",
        "",
        "These rows describe **executed trades only**. They omit WAIT/rejected "
        "opportunities and cannot establish the result of a new entry strategy. "
        "The three indicators are simple one-minute context proxies, not a replay "
        "of all ForexSAI signal votes. A 70% observed WR in a small subset is a "
        "research lead, not a 70% future success claim. No thresholds were tuned "
        "to the test period in this script, but reading this report to select a rule "
        "uses that test period; collect a new untouched forward period before a claim.",
        "",
        "Next: add decision snapshots and rejected/WAIT opportunities, verify actual "
        "stop distance and spread per fill, compare the candidate with its unchanged "
        "baseline in a later period, then use the existing shadow/live validation card.",
        "",
        "`trade_examples.png` shows the first eligible win and loss chronologically, "
        "including entry, exit, TP/SL levels, and decision-time alignment. Levels "
        "can be inferred by the source dataset; they are visual context, not fill proof.",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.point_value is not None and args.point_value <= 0:
        raise ValueError("point value must be positive")
    bars = load_bars(args.bars)
    trades = load_trades(args.trades)
    if args.since:
        since = utc_timestamp(args.since)
        trades = [row for row in trades if utc_timestamp(row["entry_time"]) >= since]
    alignment = alignment_check(trades, bars)
    timestamps = [bar["ts"] for bar in bars]
    eligible = []
    for trade in trades:
        features = decision_features(trade, bars, timestamps)
        if features is None:
            continue
        estimated_r = realized_r(trade, args.point_value)
        pnl = float(trade["pnl"])
        eligible.append({**trade, **features, "win": None if pnl == 0 else pnl > 0,
                         "estimated_r": estimated_r})
    evaluation = evaluate(eligible)
    args.out.mkdir(parents=True, exist_ok=True)
    example_ids = chart_examples(eligible, bars, args.out, args.symbol)
    summary = {
        "symbol": args.symbol,
        "trades_path": str(args.trades),
        "bars_path": str(args.bars),
        "point_value": args.point_value,
        "input_trades": len(trades),
        "eligible_trades": len(eligible),
        "excluded_trades": len(trades) - len(eligible),
        "first_entry_utc": trades[0]["entry_time"] if trades else None,
        "last_entry_utc": trades[-1]["entry_time"] if trades else None,
        "chart_example_pids": example_ids,
        "alignment": alignment,
        "evaluation": evaluation,
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(args.out, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--bars", type=Path, required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--point-value", type=float,
                        help="verified currency value of one price point per lot")
    parser.add_argument("--since", help="ISO-8601 UTC; drop trades entered earlier "
                        "(use for an untouched forward period)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args)
    print(f"Eligible trades: {summary['eligible_trades']}/{summary['input_trades']}")
    print(f"Clock alignment: {summary['alignment']['status']} "
          f"(best shift {summary['alignment']['best_shift_min']} min)")
    print(f"Report: {args.out / 'report.md'}")
    print(f"Chart: {args.out / 'trade_examples.png'}")


if __name__ == "__main__":
    main()
