"""
Phase 0 — XAUUSD model diagnosis.

Reads:
  - backend/models/model_lgbm_xauusd.joblib  (current model)
  - Supabase: prediction_logs, outcome_results, error_analysis,
              failure_analyses, learning_feedback

Writes:
  - phase0_report.md  (human-readable findings)
  - phase0_data.json  (raw numbers for next phases)

Run from project root:
  python xauusdegitim/phase0_diagnose.py
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*InconsistentVersionWarning.*")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
BASE = f"{URL}/rest/v1"

NOW = datetime.now(timezone.utc)
LOOKBACK_DAYS = 90  # 3 months — covers the regime period user complains about

XAUUSD_SYMBOLS = ["XAUUSD", "XAUUSD.FOREX"]


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_paginated(table: str, params: dict, select: str, page: int = 1000, cap: int = 100_000) -> list[dict]:
    rows: list[dict] = []
    with httpx.Client(timeout=60) as c:
        offset = 0
        while True:
            p = {**params, "select": select, "order": "created_at.desc", "limit": str(page), "offset": str(offset)}
            r = c.get(f"{BASE}/{table}", headers=HEADERS, params=p)
            if r.status_code == 404:
                return []
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < page or len(rows) >= cap:
                break
            offset += page
    return rows


def count_exact(table: str, params: dict) -> int:
    hdr = {**HEADERS, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
    r = httpx.get(f"{BASE}/{table}", headers=hdr, params={**params, "select": "id"}, timeout=30)
    if r.status_code == 404:
        return -1
    cr = r.headers.get("content-range", "")
    try:
        return int(cr.split("/")[-1])
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# 1. Current model inspection
# ---------------------------------------------------------------------------

def inspect_model() -> dict:
    import joblib
    import numpy as np
    path = ROOT / "backend" / "models" / "model_lgbm_xauusd.joblib"
    pipe = joblib.load(path)
    feats = list(getattr(pipe, "feature_names_in_", []))
    info: dict = {
        "path": str(path),
        "type": type(pipe).__name__,
        "classes": [int(c) for c in getattr(pipe, "classes_", [])],
        "n_features": len(feats),
        "features": feats,
    }
    # Find the LGBM step inside the pipeline
    final = pipe.steps[-1][1] if hasattr(pipe, "steps") else pipe
    if hasattr(final, "feature_importances_"):
        fi = final.feature_importances_
        # feature_importances_ length matches transformed features, not necessarily names
        if len(fi) == len(feats):
            order = np.argsort(fi)[::-1]
            info["top_importances"] = [
                {"feature": feats[i], "importance": float(fi[i])} for i in order[:30]
            ]
            info["zero_importance_count"] = int((fi == 0).sum())
        else:
            info["importance_length_mismatch"] = {"importances": len(fi), "names": len(feats)}
    return info


# ---------------------------------------------------------------------------
# 2. Supabase: XAUUSD prediction_logs analytics
# ---------------------------------------------------------------------------

def analyze_predictions() -> dict:
    since = NOW - timedelta(days=LOOKBACK_DAYS)
    out: dict = {"window_days": LOOKBACK_DAYS, "since": iso(since)}
    all_rows: list[dict] = []
    for sym in XAUUSD_SYMBOLS:
        rows = fetch_paginated(
            "prediction_logs",
            {"symbol": f"eq.{sym}", "created_at": f"gte.{iso(since)}"},
            select="id,symbol,model_type,ml_direction,ml_confidence,status,resolution_reason,timeframe,created_at,factors,ml_entry_price,ml_target_price,ml_stop_price",
            page=1000,
        )
        all_rows.extend(rows)
    out["total"] = len(all_rows)

    # Filter to ML-only signals (the model we're auditing)
    ml_rows = [r for r in all_rows if (r.get("model_type") or "").startswith("ml")]
    out["ml_rows"] = len(ml_rows)

    # Direction distribution (BUY-bias check)
    dir_overall = Counter((r.get("ml_direction") or "NULL") for r in ml_rows)
    out["direction_distribution"] = dict(dir_overall)
    total_dir = sum(v for k, v in dir_overall.items() if k in ("BUY", "SELL"))
    out["buy_share_pct"] = round(dir_overall.get("BUY", 0) / total_dir * 100, 1) if total_dir else 0
    out["sell_share_pct"] = round(dir_overall.get("SELL", 0) / total_dir * 100, 1) if total_dir else 0

    # Status (resolution outcomes)
    status_counter = Counter(r.get("status") or "NULL" for r in ml_rows)
    out["status_distribution"] = dict(status_counter)
    resolved = status_counter.get("completed", 0) + status_counter.get("stopped", 0)
    out["win_rate_pct"] = round(status_counter.get("completed", 0) / resolved * 100, 1) if resolved else 0
    out["resolved_total"] = resolved

    # Win rate split by direction (the bias hypothesis)
    by_dir_status: dict[str, Counter] = defaultdict(Counter)
    for r in ml_rows:
        d = r.get("ml_direction") or "NULL"
        by_dir_status[d][r.get("status") or "NULL"] += 1
    out["by_direction_status"] = {k: dict(v) for k, v in by_dir_status.items()}
    out["win_rate_by_direction"] = {}
    for d in ("BUY", "SELL"):
        s = by_dir_status.get(d, Counter())
        rs = s.get("completed", 0) + s.get("stopped", 0)
        out["win_rate_by_direction"][d] = {
            "resolved": rs,
            "wins": s.get("completed", 0),
            "win_rate_pct": round(s.get("completed", 0) / rs * 100, 1) if rs else None,
        }

    # Confidence calibration
    conf_buckets = {"<50": [0, 0], "50-60": [0, 0], "60-70": [0, 0], "70-80": [0, 0], "80+": [0, 0]}
    for r in ml_rows:
        c = r.get("ml_confidence")
        st = r.get("status")
        if c is None or st not in ("completed", "stopped"):
            continue
        try:
            v = float(c)
        except Exception:
            continue
        key = "<50" if v < 50 else "50-60" if v < 60 else "60-70" if v < 70 else "70-80" if v < 80 else "80+"
        conf_buckets[key][1] += 1
        if st == "completed":
            conf_buckets[key][0] += 1
    out["confidence_calibration"] = {
        k: {"wins": w, "resolved": r, "win_rate_pct": round(w / r * 100, 1) if r else None}
        for k, (w, r) in conf_buckets.items()
    }

    # Resolution reason breakdown
    reason_counter = Counter(r.get("resolution_reason") or "NULL" for r in ml_rows)
    out["resolution_reasons"] = dict(reason_counter.most_common())

    # Timeframe / scope split
    out["by_timeframe"] = dict(Counter(r.get("timeframe") or "NULL" for r in ml_rows))
    out["by_model_subtype"] = dict(Counter(r.get("model_type") or "NULL" for r in ml_rows))

    # Hourly distribution of BUY signals (BUY-bias might be session-driven)
    hour_buy = Counter()
    hour_sell = Counter()
    for r in ml_rows:
        ca = r.get("created_at")
        if not isinstance(ca, str):
            continue
        try:
            dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
        except Exception:
            continue
        d = r.get("ml_direction")
        if d == "BUY":
            hour_buy[dt.hour] += 1
        elif d == "SELL":
            hour_sell[dt.hour] += 1
    out["hourly_buy_sell"] = {
        str(h): {"BUY": hour_buy.get(h, 0), "SELL": hour_sell.get(h, 0)} for h in range(24)
    }
    return out


# ---------------------------------------------------------------------------
# 3. Outcome results — actual MFE/MAE
# ---------------------------------------------------------------------------

def analyze_outcomes() -> dict:
    since = NOW - timedelta(days=LOOKBACK_DAYS)
    out: dict = {}
    rows: list[dict] = []
    for sym in XAUUSD_SYMBOLS:
        try:
            r = fetch_paginated(
                "outcome_results",
                {"symbol": f"eq.{sym}", "created_at": f"gte.{iso(since)}"},
                select="prediction_id,symbol,outcome,highest_profit_pips,lowest_drawdown_pips,exit_price,hit_target,hit_stop,ml_correct,created_at",
                page=1000,
            )
            rows.extend(r)
        except httpx.HTTPStatusError as e:
            out[f"error_{sym}"] = f"{e.response.status_code} {e.response.text[:200]}"
    out["total"] = len(rows)
    if not rows:
        return out
    # Aggregate
    pips_favor = [r.get("highest_profit_pips") or 0 for r in rows]
    pips_against = [r.get("lowest_drawdown_pips") or 0 for r in rows]
    correct = sum(1 for r in rows if r.get("ml_correct"))
    out["ml_accuracy_pct"] = round(correct / len(rows) * 100, 1)
    out["avg_max_favorable_pips"] = round(sum(pips_favor) / len(pips_favor), 2)
    out["avg_max_adverse_pips"] = round(sum(pips_against) / len(pips_against), 2)
    out["hit_target_rate_pct"] = round(sum(1 for r in rows if r.get("hit_target")) / len(rows) * 100, 1)
    out["hit_stop_rate_pct"] = round(sum(1 for r in rows if r.get("hit_stop")) / len(rows) * 100, 1)
    out["outcome_distribution"] = dict(Counter(r.get("outcome") or "NULL" for r in rows))
    return out


# ---------------------------------------------------------------------------
# 4. Error analysis & failure_analyses — already-AI-extracted root causes
# ---------------------------------------------------------------------------

def analyze_error_tables() -> dict:
    since = NOW - timedelta(days=LOOKBACK_DAYS)
    out: dict = {}

    # error_analysis (Claude Haiku output)
    ea_rows: list[dict] = []
    for sym in XAUUSD_SYMBOLS:
        try:
            ea_rows.extend(fetch_paginated(
                "error_analysis",
                {"created_at": f"gte.{iso(since)}"},
                select="id,prediction_id,error_type,prediction_direction,confidence_pct,is_fake_move,fake_move_type,ai_analysis,lesson_learned,created_at",
                page=500,
            ))
            break  # error_analysis has no symbol filter — fetch once
        except httpx.HTTPStatusError as e:
            out["error_analysis_error"] = f"{e.response.status_code}"
            break
    # Filter by symbol via prediction lookup is expensive — instead, infer from ai_analysis or rely on volume
    out["error_analysis_total"] = len(ea_rows)
    if ea_rows:
        # Direction of failed signals (do BUY signals fail more?)
        dir_fail = Counter(r.get("prediction_direction") or "NULL" for r in ea_rows)
        out["error_analysis_failed_direction"] = dict(dir_fail)
        # Root cause distribution
        root_causes = Counter()
        fake_types = Counter()
        for r in ea_rows:
            ai = r.get("ai_analysis") or {}
            if isinstance(ai, str):
                try:
                    ai = json.loads(ai)
                except Exception:
                    ai = {}
            rc = (ai.get("root_cause") or "unknown") if isinstance(ai, dict) else "unknown"
            root_causes[rc] += 1
            if r.get("is_fake_move"):
                fake_types[r.get("fake_move_type") or "unknown"] += 1
        out["root_cause_distribution"] = dict(root_causes.most_common())
        out["fake_move_types"] = dict(fake_types.most_common())
        # Sample lessons learned (top 10 most recent)
        out["sample_lessons"] = [
            {"direction": r.get("prediction_direction"), "lesson": r.get("lesson_learned")}
            for r in ea_rows[:10] if r.get("lesson_learned")
        ]

    # failure_analyses (older, simpler table)
    fa_rows: list[dict] = []
    for sym in XAUUSD_SYMBOLS:
        try:
            fa_rows.extend(fetch_paginated(
                "failure_analyses",
                {"symbol": f"eq.{sym}", "created_at": f"gte.{iso(since)}"},
                select="id,symbol,direction,failure_reason,rsi_at_failure,volume_change,fib_level_hit,macd_divergence,created_at",
                page=500,
            ))
        except httpx.HTTPStatusError as e:
            out["failure_analyses_error"] = f"{e.response.status_code}"
            break
    out["failure_analyses_total"] = len(fa_rows)
    if fa_rows:
        # failure_reason is pipe-separated tags
        tags = Counter()
        for r in fa_rows:
            fr = r.get("failure_reason") or ""
            for t in [x.strip() for x in fr.split("|") if x.strip()]:
                tags[t] += 1
        out["failure_reason_tags"] = dict(tags.most_common(20))
        out["failure_direction"] = dict(Counter(r.get("direction") or "NULL" for r in fa_rows))
        # RSI at failure — distribution
        rsi_buckets = Counter()
        for r in fa_rows:
            v = r.get("rsi_at_failure")
            if v is None:
                continue
            try:
                v = float(v)
            except Exception:
                continue
            key = "<30" if v < 30 else "30-50" if v < 50 else "50-70" if v < 70 else "70+"
            rsi_buckets[key] += 1
        out["rsi_at_failure_buckets"] = dict(rsi_buckets)

    # learning_feedback table
    try:
        lf_rows = fetch_paginated(
            "learning_feedback",
            {"is_active": "eq.true"},
            select="id,symbol,feedback_type,condition,action,strength,sample_count,created_at",
            page=200,
        )
        out["learning_feedback_active"] = len(lf_rows)
        out["learning_feedback_for_xauusd"] = [
            {"type": r.get("feedback_type"), "condition": r.get("condition"),
             "action": r.get("action"), "strength": r.get("strength"),
             "samples": r.get("sample_count")}
            for r in lf_rows if (r.get("symbol") in XAUUSD_SYMBOLS or r.get("symbol") is None)
        ][:30]
    except httpx.HTTPStatusError:
        out["learning_feedback_error"] = True
    return out


# ---------------------------------------------------------------------------
# 5. candle_cache availability for retraining
# ---------------------------------------------------------------------------

def check_candle_cache() -> dict:
    out: dict = {}
    for sym in XAUUSD_SYMBOLS:
        for tf in ("5m", "15m", "30m", "1h", "4h", "1d"):
            try:
                n = count_exact("candle_cache", {"symbol": f"eq.{sym}", "timeframe": f"eq.{tf}"})
                if n > 0:
                    out[f"{sym}/{tf}"] = n
            except Exception:
                pass
    # Earliest/latest timestamp for the most populated combo
    if out:
        best = max(out.items(), key=lambda x: x[1])
        sym, tf = best[0].split("/")
        try:
            r1 = httpx.get(f"{BASE}/candle_cache", headers=HEADERS,
                           params={"symbol": f"eq.{sym}", "timeframe": f"eq.{tf}",
                                   "select": "timestamp", "order": "timestamp.asc", "limit": "1"}, timeout=30)
            r2 = httpx.get(f"{BASE}/candle_cache", headers=HEADERS,
                           params={"symbol": f"eq.{sym}", "timeframe": f"eq.{tf}",
                                   "select": "timestamp", "order": "timestamp.desc", "limit": "1"}, timeout=30)
            d1 = r1.json()
            d2 = r2.json()
            if d1 and d2:
                out["earliest"] = d1[0].get("timestamp")
                out["latest"] = d2[0].get("timestamp")
                out["best_tf"] = f"{sym}/{tf}"
        except Exception as e:
            out["range_error"] = str(e)
    return out


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(model: dict, preds: dict, outc: dict, errs: dict, candles: dict) -> str:
    lines: list[str] = []
    lines.append(f"# XAUUSD Model — Phase 0 Diagnostic Report")
    lines.append(f"_Generated {NOW.isoformat()} — lookback {LOOKBACK_DAYS} days_\n")

    lines.append("## 1. Current Model")
    lines.append(f"- File: `{model['path']}`")
    lines.append(f"- Type: {model['type']}, classes={model['classes']}")
    lines.append(f"- Features: {model['n_features']}")
    if "zero_importance_count" in model:
        lines.append(f"- **Zero-importance features: {model['zero_importance_count']}/{model['n_features']}** "
                     f"(unused — eğitime hiç katkı yok)")
    if "top_importances" in model:
        lines.append("\n### Top 30 features by importance")
        lines.append("| # | Feature | Importance |")
        lines.append("|---|---------|------------|")
        for i, f in enumerate(model["top_importances"], 1):
            lines.append(f"| {i} | `{f['feature']}` | {f['importance']:.0f} |")

    lines.append("\n## 2. Live Prediction Behavior (last 90 days)")
    lines.append(f"- Total XAUUSD logs: **{preds['total']}** (ML-family: {preds['ml_rows']})")
    lines.append(f"- Direction distribution: {preds['direction_distribution']}")
    lines.append(f"- **BUY share: {preds['buy_share_pct']}% / SELL share: {preds['sell_share_pct']}%** "
                 f"→ {'⚠ BUY-BIAS CONFIRMED' if preds['buy_share_pct'] > 60 else 'no extreme bias'}")
    lines.append(f"- Status mix: {preds['status_distribution']}")
    lines.append(f"- Overall win rate (completed/resolved): **{preds['win_rate_pct']}%** "
                 f"({preds['resolved_total']} resolved)")
    lines.append("\n### Win rate by direction")
    for d, s in preds["win_rate_by_direction"].items():
        lines.append(f"- **{d}**: {s['win_rate_pct']}% ({s['wins']}/{s['resolved']})")
    lines.append("\n### Confidence calibration")
    lines.append("| Bucket | Wins | Resolved | Win-Rate% |")
    lines.append("|--------|------|----------|-----------|")
    for k, v in preds["confidence_calibration"].items():
        lines.append(f"| {k} | {v['wins']} | {v['resolved']} | {v['win_rate_pct']} |")
    lines.append("\n### Resolution reasons")
    for k, v in list(preds["resolution_reasons"].items())[:15]:
        lines.append(f"- `{k}`: {v}")

    lines.append("\n## 3. Outcome Results (MFE/MAE)")
    if outc.get("total"):
        lines.append(f"- Total outcomes: {outc['total']}")
        lines.append(f"- ml_correct rate: **{outc['ml_accuracy_pct']}%**")
        lines.append(f"- Avg max-favorable: {outc['avg_max_favorable_pips']} pips")
        lines.append(f"- Avg max-adverse: {outc['avg_max_adverse_pips']} pips")
        lines.append(f"- Hit-target rate: {outc['hit_target_rate_pct']}%")
        lines.append(f"- Hit-stop rate: {outc['hit_stop_rate_pct']}%")
        lines.append(f"- outcome distribution: {outc['outcome_distribution']}")
    else:
        lines.append("_no outcome data_")

    lines.append("\n## 4. AI-Analyzed Failures (error_analysis table)")
    lines.append(f"- Records: {errs.get('error_analysis_total', 0)}")
    if errs.get("error_analysis_total"):
        lines.append(f"- Failed direction split: {errs.get('error_analysis_failed_direction', {})}")
        lines.append("\n### Root causes (Claude-tagged)")
        for k, v in errs.get("root_cause_distribution", {}).items():
            lines.append(f"- `{k}`: {v}")
        if errs.get("fake_move_types"):
            lines.append("\n### Fake move types")
            for k, v in errs["fake_move_types"].items():
                lines.append(f"- `{k}`: {v}")
        if errs.get("sample_lessons"):
            lines.append("\n### Sample lessons learned (10 recent)")
            for s in errs["sample_lessons"]:
                lines.append(f"- **{s['direction']}**: {s['lesson']}")

    lines.append(f"\n## 5. failure_analyses (rule-based)")
    lines.append(f"- Records: {errs.get('failure_analyses_total', 0)}")
    if errs.get("failure_analyses_total"):
        lines.append(f"- Direction split: {errs.get('failure_direction', {})}")
        lines.append("\n### Top failure tags")
        for k, v in errs.get("failure_reason_tags", {}).items():
            lines.append(f"- `{k}`: {v}")
        if errs.get("rsi_at_failure_buckets"):
            lines.append(f"- RSI at failure: {errs['rsi_at_failure_buckets']}")

    lines.append(f"\n## 6. learning_feedback active rules")
    lines.append(f"- Active total: {errs.get('learning_feedback_active', 0)}")
    if errs.get("learning_feedback_for_xauusd"):
        for f in errs["learning_feedback_for_xauusd"][:10]:
            lines.append(f"- `{f['type']}` strength={f['strength']} samples={f['samples']} "
                         f"cond={json.dumps(f['condition'], ensure_ascii=False)} "
                         f"act={json.dumps(f['action'], ensure_ascii=False)}")

    lines.append(f"\n## 7. candle_cache availability (for retraining)")
    if candles:
        for k, v in candles.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("_candle_cache yok ya da boş — eğitim için MT5'ten geçmiş çekmek gerekecek_")

    return "\n".join(lines)


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    print(">> Inspecting model...")
    model = inspect_model()
    print(f"   {model['n_features']} features, classes={model['classes']}")

    print(">> Querying predictions (90d)...")
    preds = analyze_predictions()
    print(f"   {preds['total']} rows, BUY={preds['buy_share_pct']}% / SELL={preds['sell_share_pct']}%, "
          f"win_rate={preds['win_rate_pct']}%")

    print(">> Querying outcomes...")
    outc = analyze_outcomes()
    print(f"   {outc.get('total', 0)} outcomes")

    print(">> Querying error_analysis & failure_analyses...")
    errs = analyze_error_tables()
    print(f"   error_analysis={errs.get('error_analysis_total', 0)}, "
          f"failure_analyses={errs.get('failure_analyses_total', 0)}, "
          f"learning_feedback_active={errs.get('learning_feedback_active', 0)}")

    print(">> Probing candle_cache...")
    candles = check_candle_cache()
    print(f"   {len(candles)} (symbol/tf) entries")

    payload = {"model": {k: v for k, v in model.items() if k != "features"},
               "model_features": model.get("features"),
               "predictions": preds, "outcomes": outc, "errors": errs, "candles": candles,
               "generated_at": NOW.isoformat()}
    (out_dir / "phase0_data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    (out_dir / "phase0_report.md").write_text(write_report(model, preds, outc, errs, candles))
    print(f"\nWrote {out_dir/'phase0_report.md'} and {out_dir/'phase0_data.json'}")


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text[:500]}", file=sys.stderr)
        sys.exit(2)
