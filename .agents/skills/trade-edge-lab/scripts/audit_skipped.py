#!/usr/bin/env python3
"""Replay bot gate-skips / vetoes on 1m bars: were the rejected entries right?

Offline. Complements ``audit_trades.py``, which can only see opened trades.
Each skipped intent is resolved as if it had been entered at the logged price
with a fixed TP/SL geometry, so the question "did the gate block winners or
losers" has a number. Known limits are written into the report.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit_trades as at

BAR_SECONDS = 60
SPREAD_POINT = 0.1            # MT5 bar `spread` column is in points of 0.1 index points
MAX_HOLD_SECONDS = 24 * 3600  # unresolved after this long = censored, not a loss
LOT = 5.0                     # bot lot; USD per index point per lot = 1.0 (verified: 80pt*5 = 400$)
USD_PER_POINT_LOT = 1.0
# (tp_points, sl_points). Bot geometry is not constant (80/110 early, 80/60 for
# VIXREG later, S/R-derived SL elsewhere) and skip logs carry none, so the
# verdict must hold across several.
GEOMETRIES = ((80.0, 110.0), (80.0, 60.0), (80.0, 80.0))
MIN_CALIBRATION_N = 20
BASELINE_STEP_SECONDS = 300   # drift baseline: a hypothetical entry every 5 minutes
MIN_VERDICT_N = 10
SOURCE_GATE_LOG = "gate_skipped"
SOURCE_DECISION_LOG = "decision_log"


def load_bars_with_spread(path: Path) -> dict[str, list[float]]:
    """Columnar bars: ts (bar start), high, low, spread in index points."""
    cols: dict[str, list[float]] = {k: [] for k in ("ts", "open", "high", "low", "spread")}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cols["ts"].append(at.utc_timestamp(row["time_utc"]))
            for key in ("open", "high", "low"):
                cols[key].append(float(row[key]))
            cols["spread"].append(float(row["spread"]) * SPREAD_POINT)
    order = sorted(range(len(cols["ts"])), key=cols["ts"].__getitem__)
    return {k: [v[i] for i in order] for k, v in cols.items()}


def resolve(bars: dict[str, list[float]], start_ts: float, direction: str,
            entry: float, tp_pts: float, sl_pts: float) -> str:
    """Return 'win' | 'loss' | 'open'. Bars starting at/after start_ts only.

    Entry is the fill (BUY at ask, SELL at bid). Exits cross the spread:
    a BUY closes at bid (bar low/high), a SELL closes at ask (bar + spread).
    A bar touching both TP and SL counts as a loss.
    """
    buy = direction == "BUY"
    tp = entry + tp_pts if buy else entry - tp_pts
    sl = entry - sl_pts if buy else entry + sl_pts
    ts = bars["ts"]
    i = bisect.bisect_left(ts, start_ts)
    limit = start_ts + MAX_HOLD_SECONDS
    while i < len(ts) and ts[i] <= limit:
        high, low, spread = bars["high"][i], bars["low"][i], bars["spread"][i]
        hit_tp = high >= tp if buy else low + spread <= tp
        hit_sl = low <= sl if buy else high + spread >= sl
        if hit_sl:
            return "loss"
        if hit_tp:
            return "win"
        i += 1
    return "open"


def hold_seconds(bars: dict[str, list[float]], start_ts: float, direction: str,
                 entry: float, tp_pts: float, sl_pts: float) -> float:
    """Seconds until resolution (used to sequence one position at a time)."""
    buy = direction == "BUY"
    tp = entry + tp_pts if buy else entry - tp_pts
    sl = entry - sl_pts if buy else entry + sl_pts
    ts = bars["ts"]
    i = bisect.bisect_left(ts, start_ts)
    limit = start_ts + MAX_HOLD_SECONDS
    while i < len(ts) and ts[i] <= limit:
        low, high, spread = bars["low"][i], bars["high"][i], bars["spread"][i]
        if (low <= sl if buy else high + spread >= sl) or (
                high >= tp if buy else low + spread <= tp):
            return ts[i] + BAR_SECONDS - start_ts
        i += 1
    return MAX_HOLD_SECONDS


def calibrate(bars: dict[str, list[float]], trades_csv: Path) -> dict[str, Any]:
    """Replay the bot's own TP/SL fills with the simulator; it must agree."""
    agree = total = 0
    for row in csv.DictReader(trades_csv.open(newline="", encoding="utf-8")):
        if row["exit_reason"] not in ("tp", "sl") or not row["tp_price"] or not row["sl_price"]:
            continue
        entry, tp, sl = float(row["open_price"]), float(row["tp_price"]), float(row["sl_price"])
        opened = at.utc_timestamp(row["open_time_utc"])
        start = opened // BAR_SECONDS * BAR_SECONDS + BAR_SECONDS
        outcome = resolve(bars, start, row["direction"], entry, abs(tp - entry), abs(sl - entry))
        if outcome == "open":
            continue
        total += 1
        agree += outcome == ("win" if row["exit_reason"] == "tp" else "loss")
    return {"n": total, "agree": agree, "rate": round(agree / total, 4) if total else None}


def load_gate_log(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        rows.append({"ts": at.utc_timestamp(rec["ts"]), "scope": rec["scope"],
                     "direction": rec["direction"], "price": float(rec["price"]),
                     "reason": rec["reason"], "source": SOURCE_GATE_LOG})
    return rows


def load_decision_log(path: Path, bars: dict[str, list[float]]) -> list[dict[str, Any]]:
    """VETO rows carry price 0; use the open of the bar containing the decision."""
    rows = []
    for rec in csv.DictReader(path.open(newline="", encoding="utf-8")):
        if rec["mode"] != "VETO":
            continue
        ts = at.utc_timestamp(rec["time_utc"])
        i = bisect.bisect_right(bars["ts"], ts) - 1
        if i < 0 or ts - bars["ts"][i] >= BAR_SECONDS:
            continue  # no bar covering the decision minute
        reason = rec["note"].removeprefix("reason=")
        rows.append({"ts": ts, "scope": rec["scope"], "direction": rec["direction"],
                     "price": bars["open"][i], "reason": f"veto:{reason}",
                     "source": SOURCE_DECISION_LOG})
    return rows


def sequence(events: list[dict[str, Any]], bars: dict[str, list[float]],
             geometry: tuple[float, float]) -> tuple[list[dict[str, Any]], int]:
    """One hypothetical position at a time per (reason, scope, direction).

    Repeated skips of the same intent every ~75 s are one opportunity, not
    hundreds. Returns resolved outcomes and the count censored at data end.
    """
    tp, sl = geometry
    busy: dict[tuple, float] = {}
    out, censored = [], 0
    for ev in sorted(events, key=lambda e: e["ts"]):
        key = (ev["reason"], ev["scope"], ev["direction"])
        if ev["ts"] < busy.get(key, 0.0):
            continue
        start = ev["ts"] // BAR_SECONDS * BAR_SECONDS + BAR_SECONDS
        outcome = resolve(bars, start, ev["direction"], ev["price"], tp, sl)
        if outcome == "open":
            censored += 1
            continue
        busy[key] = start + hold_seconds(bars, start, ev["direction"], ev["price"], tp, sl)
        out.append({**ev, "win": outcome == "win"})
    return out, censored


def stats(rows: list[dict[str, Any]], geometry: tuple[float, float]) -> dict[str, Any]:
    tp, sl = geometry
    n = len(rows)
    wins = sum(r["win"] for r in rows)
    breakeven = sl / (tp + sl)
    lo_hi = at.wilson_interval(wins, n)
    pnl = (wins * tp - (n - wins) * sl) * LOT * USD_PER_POINT_LOT
    return {"n": n, "wins": wins, "wr": round(wins / n, 4) if n else None,
            "wilson95": [round(v, 4) for v in lo_hi] if lo_hi else None,
            "breakeven_wr": round(breakeven, 4),
            "pnl_usd": round(pnl, 0), "usd_per_trade": round(pnl / n, 1) if n else None}


def stable_halves(rows: list[dict[str, Any]], geometry: tuple[float, float]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: r["ts"])
    mid = len(ordered) // 2
    return [stats(ordered[:mid], geometry), stats(ordered[mid:], geometry)]


def hourly_baseline(bars: dict[str, list[float]], direction: str, first_ts: float,
                    last_ts: float, geometry: tuple[float, float]) -> dict[int, list[int]]:
    """UTC hour -> [wins, resolved] for an entry every 5 min, no gate, same dates.

    This is the drift control: a blocked BUY that "would have won 60%" means
    nothing if every BUY in that month and hour won 60%.
    """
    tp, sl = geometry
    table: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    ts = bars["ts"]
    point = first_ts // BASELINE_STEP_SECONDS * BASELINE_STEP_SECONDS
    while point < last_ts:
        i = bisect.bisect_right(ts, point) - 1
        if i >= 0 and point - ts[i] < BAR_SECONDS:
            spread = bars["spread"][i]
            price = bars["open"][i] + (spread if direction == "BUY" else 0.0)
            outcome = resolve(bars, ts[i] + BAR_SECONDS, direction, price, tp, sl)
            if outcome != "open":
                cell = table[datetime.fromtimestamp(point, timezone.utc).hour]
                cell[0] += outcome == "win"
                cell[1] += 1
        point += BASELINE_STEP_SECONDS
    return table


def matched_baseline_wr(rows: list[dict[str, Any]], table: dict[int, list[int]]) -> float | None:
    """Expected WR of unfiltered entries with the same hour-of-day mix as ``rows``."""
    expected = weight = 0.0
    for row in rows:
        cell = table.get(datetime.fromtimestamp(row["ts"], timezone.utc).hour)
        if cell and cell[1]:
            expected += cell[0] / cell[1]
            weight += 1
    return round(expected / weight, 4) if weight else None


def verdict(first: dict[str, Any], second: dict[str, Any], whole: dict[str, Any]) -> str:
    """Gate verdict from the blocked set vs breakeven; 'kanıtlı' needs the CI to exclude it."""
    if whole["n"] < MIN_VERDICT_N:
        return "n<10"
    lo, hi = whole["wilson95"]
    be = whole["breakeven_wr"]
    if hi < be:
        return "HAKLI — kanıtlı (CI başabaşın altında)"
    if lo > be:
        return "YANLIŞ — kanıtlı (CI başabaşın üstünde)"
    signs = {s["usd_per_trade"] > 0 for s in (first, second) if s["n"]}
    if len(signs) > 1:
        return "kararsız (yarılar çelişiyor)"
    side = "YANLIŞ" if whole["usd_per_trade"] > 0 else "HAKLI"
    return f"eğilim: {side} (CI başabaşı içeriyor)"


def analyse(events: list[dict[str, Any]], bars: dict[str, list[float]]) -> dict[str, Any]:
    by_reason: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        by_reason[ev["reason"]].append(ev)
    result: dict[str, Any] = {"geometries": {}}
    for geometry in GEOMETRIES:
        label = f"tp{geometry[0]:.0f}_sl{geometry[1]:.0f}"
        table: dict[str, Any] = {}
        baselines: dict[tuple, dict[int, list[int]]] = {}
        for reason, evs in sorted(by_reason.items()):
            rows, censored = sequence(evs, bars, geometry)
            if not rows:
                continue
            direction = Counter(e["direction"] for e in evs).most_common(1)[0][0]
            span = (min(e["ts"] for e in evs), max(e["ts"] for e in evs))
            key = (direction, *span)
            if key not in baselines:
                baselines[key] = hourly_baseline(bars, direction, span[0], span[1], geometry)
            halves = stable_halves(rows, geometry)
            whole = stats(rows, geometry)
            base = matched_baseline_wr(rows, baselines[key])
            table[reason] = {"raw_events": len(evs), "censored": censored, "direction": direction,
                             **whole, "baseline_wr": base,
                             "lift_pp": round(100 * (whole["wr"] - base), 1) if base is not None else None,
                             "halves": halves, "verdict": verdict(halves[0], halves[1], whole)}
        result["geometries"][label] = table
    return result


def render(summary: dict[str, Any]) -> str:
    cal = summary["calibration"]
    lines = [
        "# NDX reddedilen fırsatlar (WAIT/kapı/veto) — 1m replay",
        "",
        "**Durum: KEŞİF. Canlı kapı değişikliği önerisi değil.**",
        "",
        f"- Kaynak olay: {summary['events']} (gate_skipped + VETO); bar aralığı "
        f"{summary['bars_first']} → {summary['bars_last']}.",
        f"- **Simülatör kalibrasyonu:** botun gerçek TP/SL işlemlerinin "
        f"{cal['agree']}/{cal['n']} ({100 * (cal['rate'] or 0):.1f}%) sonucunu aynen üretiyor.",
        "- Aynı niyetin ~75 sn'de bir tekrar logu TEK fırsat sayıldı: (neden, scope, yön) başına "
        "aynı anda tek varsayımsal pozisyon. Yarıları kronolojik ikiye bölüp işaret tutarlılığı arandı.",
        "- Geometri logda yok → 3 geometride çözüldü; gerçek botta SL S/R'den türetilir.",
        "",
    ]
    for label, table in summary["analysis"]["geometries"].items():
        first = next(iter(table.values()), None)
        be = first["breakeven_wr"] if first else 0
        lines += [f"## {label}  (başabaş WR {100 * be:.1f}%)", "",
                  "| Neden | Yön | Ham olay | Fırsat n | WR | Wilson %95 | Kapısız taban WR* | "
                  "Fark (pp) | $/işlem | Toplam $ | 1. yarı $/iş | 2. yarı $/iş | Verdikt |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for reason, r in sorted(table.items(), key=lambda kv: -kv[1]["n"]):
            ci = r["wilson95"]
            h1, h2 = r["halves"]
            lines.append(
                f"| {reason} | {r['direction']} | {r['raw_events']} | {r['n']} | {100 * r['wr']:.1f}% | "
                f"{100 * ci[0]:.0f}–{100 * ci[1]:.0f}% | "
                f"{100 * r['baseline_wr']:.1f}% | {r['lift_pp']:+.1f} | {r['usd_per_trade']:+.0f} | "
                f"{r['pnl_usd']:+.0f} | {h1['usd_per_trade'] if h1['n'] else '—'} | "
                f"{h2['usd_per_trade'] if h2['n'] else '—'} | {r['verdict']} |")
        lines.append("")
    lines += [
        "*Kapısız taban WR: aynı tarih aralığında, aynı UTC saat dağılımıyla, 5 dk'da bir "
        "kapısız giriş yapılsaydı beklenen WR (piyasa sürüklenmesi kontrolü). "
        "Fark ≈ 0 → kapının ayırt ettiği bir şey yok; negatif → engellenen fırsatlar "
        "ortalamadan kötüydü (kapı bilgi taşıyor).*", "",
        "## Sınırlar", "",
        "- Engellenen fırsat = botun niyeti; gerçekte pozisyon-çakışması, marjin ve "
        "diğer kapıların birleşik etkisi modellenmedi.",
        "- Toplam $ lot 5 ile; engellenenler kârlıysa 'kapının maliyeti', zararlıysa "
        "'kapının kurtardığı'dır. İşaret ters okunmasın: pozitif $ = kapı para kaybettirmiş.",
        "- ~10 neden × 3 geometri = çoklu karşılaştırma; tek hücredeki sapmaya güvenme, "
        "geometriler ve yarılar arasında tutarlı olana bak.",
        "- Bu veri kapıların devreye girdiği dönemi kapsar; aynı dönemde açılan işlemlerin "
        "karşılaştırması için `audit_trades.py --since` ile çalıştır.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bars", type=Path, required=True)
    parser.add_argument("--gate-log", type=Path, required=True)
    parser.add_argument("--decision-log", type=Path)
    parser.add_argument("--trades", type=Path, required=True, help="MT5 deal CSV for calibration")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    bars = load_bars_with_spread(args.bars)
    events = load_gate_log(args.gate_log)
    if args.decision_log:
        events += load_decision_log(args.decision_log, bars)
    # Events past the last bar cannot be resolved; events before the first bar neither.
    events = [e for e in events if bars["ts"][0] <= e["ts"] < bars["ts"][-1]]
    summary = {
        "events": len(events),
        "bars_first": datetime.fromtimestamp(bars["ts"][0], timezone.utc).isoformat(),
        "bars_last": datetime.fromtimestamp(bars["ts"][-1], timezone.utc).isoformat(),
        "calibration": calibrate(bars, args.trades),
        "analysis": analyse(events, bars),
    }
    if summary["calibration"]["n"] < MIN_CALIBRATION_N:
        raise SystemExit("calibration sample too small; simulator unverified")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (args.out / "report.md").write_text(render(summary), encoding="utf-8")
    print(f"events={summary['events']} calibration={summary['calibration']}")
    print(f"Report: {args.out / 'report.md'}")


if __name__ == "__main__":
    main()
