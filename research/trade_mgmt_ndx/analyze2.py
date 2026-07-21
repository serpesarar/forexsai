"""Aşama 2: segment kırılımı + parametre duyarlılığı + bootstrap CI.

Soru: iyileşme NEREDEN geliyor (BUY mü SELL mi, hangi kohort), parametreye ne
kadar duyarlı ve şansla açıklanabilir mi (bootstrap %90 CI, işlem-bazlı resample)?
"""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

from replay import load, trade_bars, replay, bind_strategy, make_strategies, aggregate

HERE = Path(__file__).resolve().parent
random.seed(42)


def run_strategy(trades, seqs, fn):
    results = []
    for t in trades:
        bound = bind_strategy("x", fn, t) if fn else None
        res = replay(t, seqs[t["pid"]], bound)
        results.append({**res, "pid": t["pid"], "cohort": t["cohort"],
                        "direction": t["direction"], "tag": t.get("strategy_tag", "")})
    return results


def seg_table(results, baseline):
    base_by_pid = {x["pid"]: x for x in baseline}
    segs = {}
    for x in results:
        for key in (f"dir_{x['direction']}", f"cohort_{x['cohort']}",
                    f"{x['cohort']}_{x['direction']}"):
            segs.setdefault(key, []).append(x)
    out = {}
    for key, xs in sorted(segs.items()):
        delta = sum(x["r"] - base_by_pid[x["pid"]]["r"] for x in xs)
        out[key] = {"n": len(xs),
                    "total_r": round(sum(x["r"] for x in xs), 2),
                    "delta_vs_base": round(delta, 2)}
    return out


def bootstrap_delta(results, baseline, iters=4000):
    """İşlem bazlı resample; delta_total_R %5/%50/%95."""
    base_by_pid = {x["pid"]: x for x in baseline}
    deltas = [x["r"] - base_by_pid[x["pid"]]["r"] for x in results]
    n = len(deltas)
    sums = []
    for _ in range(iters):
        sums.append(sum(deltas[random.randrange(n)] for _ in range(n)))
    sums.sort()
    return {"p05": round(sums[int(0.05 * iters)], 2),
            "p50": round(sums[int(0.50 * iters)], 2),
            "p95": round(sums[int(0.95 * iters)], 2),
            "p_improve": round(100 * sum(1 for s in sums if s > 0) / iters, 1)}


# ─── Parametrik aileler ──────────────────────────────────────────────────────

def be_after(minutes_thr):
    def fn(state, r, f, m, closes):
        if m >= minutes_thr and not state["mem"].get("be"):
            state["mem"]["be"] = True
            return {"sl": state["mem"]["entry"]}
    return fn


def cut_dwell(bars_thr, zone):
    def fn(state, r, f, m, closes):
        if len(closes) >= bars_thr and all(x <= zone for x in closes[-bars_thr:]):
            return {"exit": True}
    return fn


def scratch_dwell(bars_thr, zone):
    def fn(state, r, f, m, closes):
        if state["mem"].get("scr"):
            return None
        if len(closes) >= bars_thr and all(x <= zone for x in closes[-bars_thr:]):
            state["mem"]["scr"] = True
            return {"tp": state["mem"]["entry"]}
    return fn


def stall_exit(reach, wait):
    def fn(state, r, f, m, closes):
        if f >= reach and "t0" not in state["mem"]:
            state["mem"]["t0"] = m
        if "t0" in state["mem"] and m - state["mem"]["t0"] >= wait:
            return {"exit": True}
    return fn


def main():
    trades, bars, keys = load()
    seqs = {t["pid"]: trade_bars(t, bars, keys) for t in trades}
    trades = [t for t in trades if len(seqs[t["pid"]]) >= 5]

    baseline = run_strategy(trades, seqs, None)
    report = {"baseline_total_r": round(sum(x["r"] for x in baseline), 2),
              "baseline_seg": seg_table(baseline, baseline)}

    # 1) 10 stratejinin segment kırılımı + bootstrap
    strat_details = {}
    for name, fn in make_strategies().items():
        res = run_strategy(trades, seqs, fn)
        strat_details[name] = {
            "total_r": round(sum(x["r"] for x in res), 2),
            "seg": seg_table(res, baseline),
            "bootstrap_delta": bootstrap_delta(res, baseline),
        }
    report["strategies"] = strat_details

    # 2) Parametre duyarlılığı
    grids = {}
    for thr in (15, 30, 45, 60, 90):
        res = run_strategy(trades, seqs, be_after(thr))
        grids[f"be_after_{thr}m"] = {"total_r": round(sum(x["r"] for x in res), 2),
                                     "delta": round(sum(x["r"] for x in res) - report["baseline_total_r"], 2)}
    for bars_thr in (5, 10, 15, 20):
        for zone in (-0.33, -0.5, -0.66):
            res = run_strategy(trades, seqs, cut_dwell(bars_thr, zone))
            grids[f"cut_dwell{bars_thr}_z{zone}"] = {
                "total_r": round(sum(x["r"] for x in res), 2),
                "delta": round(sum(x["r"] for x in res) - report["baseline_total_r"], 2)}
            res2 = run_strategy(trades, seqs, scratch_dwell(bars_thr, zone))
            grids[f"scratch_dwell{bars_thr}_z{zone}"] = {
                "total_r": round(sum(x["r"] for x in res2), 2),
                "delta": round(sum(x["r"] for x in res2) - report["baseline_total_r"], 2)}
    for reach in (0.5, 0.7, 0.8):
        for wait in (10, 15, 30):
            res = run_strategy(trades, seqs, stall_exit(reach, wait))
            grids[f"stall_r{reach}_w{wait}"] = {
                "total_r": round(sum(x["r"] for x in res), 2),
                "delta": round(sum(x["r"] for x in res) - report["baseline_total_r"], 2)}
    report["param_grid"] = grids

    json.dump(report, open(HERE / "results_stage2.json", "w"), indent=1)

    print("SEGMENT (baseline):", json.dumps(report["baseline_seg"], indent=1))
    print("\nEn iyi 12 grid noktası (delta):")
    ranked = sorted(grids.items(), key=lambda kv: -kv[1]["delta"])
    for k, v in ranked[:12]:
        print(f"  {k:<26} total={v['total_r']:>8} delta={v['delta']:>7}")
    print("\nBootstrap (delta>0 olasılığı):")
    for name, d in strat_details.items():
        b = d["bootstrap_delta"]
        print(f"  {name:<28} Δp50={b['p50']:>7} [{b['p05']},{b['p95']}] P(+)={b['p_improve']}%")


if __name__ == "__main__":
    main()
