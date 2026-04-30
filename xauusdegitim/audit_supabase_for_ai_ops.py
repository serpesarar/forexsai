"""
Supabase audit — what's already wired for an AI-ops "self-improving" loop?

We check every table that could hold:
  - feature/indicator snapshot at signal time (input features)
  - reason WHY a signal failed (root cause / lesson learned)
  - learning rules that the system applies back to predictions
  - the candles around a signal (to retrace what happened)
  - any meta-table tracking model performance over time

Output: a single markdown report with row counts, freshness, fill rate,
       and a "ready vs broken vs missing" verdict per table.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
BASE = f"{URL}/rest/v1"
NOW = datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def probe_table(name: str, sample_columns: str = "*", limit: int = 1) -> dict:
    """Returns: existence, total rows, latest row preview, latest created_at age."""
    out: dict = {"name": name}
    # exact count
    hdr = {**HEADERS, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
    try:
        r = httpx.get(f"{BASE}/{name}", headers=hdr, params={"select": "id"}, timeout=30)
    except Exception as e:
        out["exists"] = False
        out["error"] = str(e)[:120]
        return out
    if r.status_code in (404, 400):
        out["exists"] = False
        out["error"] = f"{r.status_code}: {r.text[:120]}"
        return out
    out["exists"] = True
    cr = r.headers.get("content-range", "")
    try:
        out["total_rows"] = int(cr.split("/")[-1])
    except Exception:
        out["total_rows"] = -1
    # latest sample
    try:
        order_cols = ["created_at.desc", "id.desc"]
        for ord_col in order_cols:
            r2 = httpx.get(f"{BASE}/{name}", headers=HEADERS,
                           params={"select": sample_columns, "order": ord_col, "limit": str(limit)}, timeout=30)
            if r2.status_code == 200:
                data = r2.json()
                if data:
                    out["latest"] = data[0]
                    ca = data[0].get("created_at")
                    if ca:
                        try:
                            dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                            age = (NOW - dt).total_seconds() / 3600
                            out["latest_age_hours"] = round(age, 1)
                        except Exception:
                            pass
                    break
            elif r2.status_code == 400 and "created_at" in str(r2.text):
                continue  # try next order column
    except Exception as e:
        out["latest_err"] = str(e)[:120]
    return out


def fill_rate_check(table: str, json_col: str, expected_keys: list[str], days: int = 30) -> dict:
    """Sample recent rows, see what % of them carry each expected JSON key."""
    since = NOW - timedelta(days=days)
    out: dict = {"table": table, "json_col": json_col, "sample": 0, "fills": {}}
    try:
        r = httpx.get(f"{BASE}/{table}", headers=HEADERS,
                      params={"select": json_col, "created_at": f"gte.{iso(since)}",
                              "limit": "500", "order": "created_at.desc"}, timeout=60)
        if r.status_code != 200:
            return out
        rows = r.json()
        out["sample"] = len(rows)
        for k in expected_keys:
            n = 0
            for row in rows:
                v = row.get(json_col)
                if isinstance(v, str):
                    try:
                        v = json.loads(v)
                    except Exception:
                        v = {}
                if isinstance(v, dict) and k in v and v[k] not in (None, "", []):
                    n += 1
            out["fills"][k] = {"present": n, "rate_pct": round(n / max(len(rows), 1) * 100, 1)}
    except Exception as e:
        out["error"] = str(e)[:120]
    return out


CANDIDATES = [
    # Core signal tables
    ("prediction_logs", "id,symbol,model_type,ml_direction,status,resolution_reason,created_at,factors"),
    ("outcome_results", "id,prediction_id,outcome,ml_correct,highest_profit_pips,lowest_drawdown_pips,created_at"),
    ("signal_checks",   "id,signal_id,check_time,current_price,status"),
    # Failure / learning tables
    ("error_analysis",  "id,prediction_id,error_type,prediction_direction,is_fake_move,fake_move_type,analysis_status,ai_analysis,lesson_learned,created_at"),
    ("failure_analyses","id,symbol,direction,failure_reason,rsi_at_failure,fib_level_hit,macd_divergence,recommendation,created_at"),
    ("learning_feedback","id,symbol,feedback_type,condition,action,strength,sample_count,is_active,created_at"),
    ("candle_snapshots","id,prediction_id,symbol,timeframe,snapshot_type,candle_count,created_at"),
    # Performance trackers
    ("meta_combination_stats", "id,total_signals,win_count,created_at"),
    ("ml_strategy_performance", "id,model_type,scope,win_rate,sample_size,created_at"),
    # Cache / context
    ("candle_cache", "symbol,timeframe,timestamp"),
    ("cot_data", "symbol,report_date,commercials_net"),
    # Possibly user-built (hypothesis from "I made a system once")
    ("model_improvements", "*"),
    ("model_iterations", "*"),
    ("model_audits", "*"),
    ("ai_ops_proposals", "*"),
    ("self_improvement_log", "*"),
    ("training_metrics", "*"),
    ("feature_importance_history", "*"),
    ("performance_alerts", "*"),
]

EXPECTED_FACTOR_KEYS = [
    "rsi_14", "rsi", "rsi_14_M30",
    "macd_hist", "macd_hist_M30",
    "adx", "adx_14",
    "volume_ratio", "vol_ratio", "vol_z_M30",
    "trend_direction", "regime",
    "bb_pctb", "bb_position",
    "nearest_resistance_distance", "resistance_distance",
    "nearest_support_distance", "support_distance",
    "atr_14", "session", "strategy",
]


def main():
    print(f"AUDIT @ {iso(NOW)}\nSupabase: {URL}\n")
    rows = []
    for name, cols in CANDIDATES:
        rows.append(probe_table(name, cols))

    # Markdown report
    out = []
    out.append(f"# Supabase AI-Ops Readiness Audit")
    out.append(f"_Generated {iso(NOW)}_\n")

    out.append("## 1. Tables — existence + size + freshness")
    out.append("| Table | Exists | Rows | Latest age (hr) | Verdict |")
    out.append("|---|---|---|---|---|")
    for r in rows:
        if not r.get("exists"):
            out.append(f"| `{r['name']}` | ❌ | — | — | missing — {r.get('error', '')[:50]} |")
            continue
        rows_n = r.get("total_rows", -1)
        age = r.get("latest_age_hours", "?")
        if rows_n == 0:
            verdict = "⚠ EMPTY (table exists, never written)"
        elif rows_n < 10:
            verdict = "⚠ Tiny — likely broken pipeline"
        elif isinstance(age, float) and age > 168:
            verdict = "⚠ Stale (>7d old)"
        else:
            verdict = "✓ Active"
        out.append(f"| `{r['name']}` | ✓ | {rows_n} | {age} | {verdict} |")

    # Detail blocks for anything non-trivial
    out.append("\n## 2. Latest sample row per active table")
    for r in rows:
        if r.get("exists") and r.get("total_rows", 0) > 0 and "latest" in r:
            sample = r["latest"]
            keys = list(sample.keys()) if isinstance(sample, dict) else []
            preview = {k: sample[k] for k in keys[:8]} if isinstance(sample, dict) else sample
            out.append(f"\n### `{r['name']}` latest row")
            out.append("```json")
            out.append(json.dumps(preview, indent=2, default=str)[:1200])
            out.append("```")

    # Factor fill-rate (this is the killer — predict-time features being logged)
    out.append("\n## 3. prediction_logs.factors fill rate (last 30 days)")
    out.append("> If indicator keys (rsi, macd, adx, etc.) aren't here, the AI-ops loop\n"
               "> can't analyze WHAT a model saw at decision time.\n")
    fill = fill_rate_check("prediction_logs", "factors", EXPECTED_FACTOR_KEYS, days=30)
    out.append(f"Sample: **{fill['sample']} rows** scanned\n")
    out.append("| Key | Present | Rate% |")
    out.append("|---|---|---|")
    for k, v in fill.get("fills", {}).items():
        marker = "✓" if v["rate_pct"] >= 50 else ("⚠" if v["rate_pct"] >= 5 else "❌")
        out.append(f"| `{k}` | {v['present']} | {v['rate_pct']}% {marker} |")

    out.append("\n## 4. error_analysis.analysis_status breakdown")
    try:
        r = httpx.get(f"{BASE}/error_analysis", headers=HEADERS,
                      params={"select": "analysis_status,ai_analysis", "limit": "1000",
                              "order": "created_at.desc"}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            from collections import Counter
            stat = Counter(d.get("analysis_status") or "NULL" for d in data)
            out.append(f"Total scanned: {len(data)}\n")
            for k, n in stat.most_common():
                out.append(f"- `{k}`: {n}")
            # how many have a credit-balance error
            credit_err = 0
            for d in data:
                ai = d.get("ai_analysis")
                if isinstance(ai, str):
                    try: ai = json.loads(ai)
                    except: ai = {}
                if isinstance(ai, dict) and "credit balance" in str(ai.get("error", "")).lower():
                    credit_err += 1
            if credit_err:
                out.append(f"\n**⚠ {credit_err} rows failed because Anthropic API credit balance is exhausted.**")
    except Exception as e:
        out.append(f"_query failed: {e}_")

    # Persist
    report = "\n".join(out)
    p = Path(__file__).resolve().parent / "supabase_ai_ops_audit.md"
    p.write_text(report)
    print(report)
    print(f"\n--- Saved to {p}")


if __name__ == "__main__":
    main()
