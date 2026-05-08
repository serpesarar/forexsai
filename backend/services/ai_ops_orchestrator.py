"""
AI-Ops Orchestrator — daily failure analysis + DeepSeek improvement proposals.

Pipeline:
  1. Fetch resolved failures from prediction_logs (last N days)
  2. Layer 1: tag each via failure_tagger (programmatic, free)
     → write to failure_analyses table
  3. Cluster failures by (symbol, model_type, direction, signature)
     → write summary rows to failure_clusters table
  4. For clusters with sample_size >= MIN_CLUSTER_SIZE:
     Layer 2: send to DeepSeek for root-cause + remediation proposal
     → write to improvement_proposals table (status='pending')
  5. Human reviews proposals on a dashboard, approves/rejects.

Entry: orchestrate_ai_ops(window_days=7) — call from cron.
"""
from __future__ import annotations

import json
import logging
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Config
DEFAULT_WINDOW_DAYS = 7
MIN_CLUSTER_SIZE = 5            # Below this, don't bother LLM
MAX_LLM_CLUSTERS_PER_RUN = 10   # Cost cap
LLM_TIMEOUT_SECONDS = 60

# Models we audit (focus on the actual decision-makers)
AUDITED_MODELS = {"meta", "ml", "ml:main", "ml:nasdaq_precision", "ml:full_power",
                  "ml:aggressive", "ml:balanced",
                  "pulse1", "pulse2", "pulse3", "emel", "smc", "ai_panel"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Layer 1 — programmatic tagging
# ---------------------------------------------------------------------------

async def _fetch_resolved_failures(client, since_iso: str, limit: int = 5000) -> list[dict]:
    """Fetch failed (stopped or negative-resolution) signals + their outcomes."""
    try:
        rows = client.table("prediction_logs").select(
            "id,symbol,model_type,ml_direction,ml_confidence,status,resolution_reason,"
            "ml_entry_price,ml_target_price,ml_stop_price,factors,created_at,timeframe"
        ).gte("created_at", since_iso).in_("status", ["stopped", "completed"]).limit(limit)
        result = rows.execute() if hasattr(rows, "execute") else rows
        data = result.get("data") if isinstance(result, dict) else getattr(result, "data", [])
        return data or []
    except Exception as e:
        logger.exception("[ai_ops] fetch failures failed: %s", e)
        return []


async def _fetch_outcome_map(client, prediction_ids: list[str]) -> dict[str, dict]:
    if not prediction_ids:
        return {}
    out: dict[str, dict] = {}
    # Chunk by 200 to keep URL length sane
    for i in range(0, len(prediction_ids), 200):
        chunk = prediction_ids[i:i + 200]
        try:
            r = client.table("outcome_results").select(
                "prediction_id,outcome,exit_price,highest_profit_pips,lowest_drawdown_pips,"
                "hit_target,hit_stop,ml_correct"
            ).in_("prediction_id", chunk)
            result = r.execute() if hasattr(r, "execute") else r
            data = result.get("data") if isinstance(result, dict) else getattr(result, "data", [])
            for o in (data or []):
                pid = o.get("prediction_id")
                if pid:
                    out[pid] = o
        except Exception as e:
            logger.warning("[ai_ops] outcome chunk %d failed: %s", i, e)
    return out


async def _persist_tags(client, tagged: list[dict]) -> int:
    """Insert tagged failures into failure_analyses. Tries UPSERT first, then
    falls back to plain INSERT with manual dedup if the UNIQUE constraint
    is missing (back-compat with installs where the migration was incomplete)."""
    if not tagged:
        return 0
    # Filter out internal keys (the underscore-prefixed ones the tagger uses)
    rows = []
    for t in tagged:
        rows.append({k: v for k, v in t.items() if not k.startswith("_")})

    # Pre-check: is there already a row for any of these prediction_ids? (safe dedup)
    existing_ids: set[str] = set()
    try:
        pred_ids = [r["prediction_id"] for r in rows if r.get("prediction_id")]
        for i in range(0, len(pred_ids), 200):
            chunk = pred_ids[i:i + 200]
            r = client.table("failure_analyses").select("prediction_id").in_(
                "prediction_id", chunk)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            for row in (data or []):
                if row.get("prediction_id"):
                    existing_ids.add(row["prediction_id"])
    except Exception as e:
        logger.warning("[ai_ops] dedup pre-check failed (will rely on DB constraint): %s", e)

    fresh_rows = [r for r in rows if r.get("prediction_id") not in existing_ids]
    if not fresh_rows:
        logger.info("[ai_ops] all %d tagged failures already in failure_analyses", len(rows))
        return 0

    inserted = 0
    upsert_failed = False
    for i in range(0, len(fresh_rows), 200):
        chunk = fresh_rows[i:i + 200]
        try:
            r = client.table("failure_analyses").upsert(chunk, on_conflict="prediction_id")
            res = r.execute() if hasattr(r, "execute") else r
            err = res.get("error") if isinstance(res, dict) else None
            if err:
                logger.warning("[ai_ops] upsert err on chunk %d (will fallback to insert): %s",
                               i, err)
                upsert_failed = True
                break
            inserted += len(chunk)
        except Exception as e:
            err_str = str(e)
            if "unique" in err_str.lower() or "constraint" in err_str.lower() or "on_conflict" in err_str.lower():
                logger.warning("[ai_ops] UNIQUE constraint missing on failure_analyses.prediction_id "
                               "— falling back to plain INSERT (apply migration "
                               "20260430_ai_ops_proposals.sql to enable proper UPSERT). Error: %s",
                               err_str[:200])
                upsert_failed = True
                break
            logger.warning("[ai_ops] failure_analyses upsert chunk %d unexpected error: %s",
                           i, err_str[:200])

    if upsert_failed:
        # Plain insert (we already deduped above)
        inserted = 0
        for i in range(0, len(fresh_rows), 200):
            chunk = fresh_rows[i:i + 200]
            try:
                r = client.table("failure_analyses").insert(chunk)
                res = r.execute() if hasattr(r, "execute") else r
                err = res.get("error") if isinstance(res, dict) else None
                if err:
                    logger.warning("[ai_ops] fallback insert err on chunk %d: %s", i, err)
                else:
                    inserted += len(chunk)
            except Exception as e:
                logger.warning("[ai_ops] fallback insert chunk %d: %s", i, str(e)[:200])

    logger.info("[ai_ops] failure_analyses persisted: %d (skipped %d existing)",
                inserted, len(rows) - len(fresh_rows))
    return inserted


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def _build_clusters(tagged: list[dict], all_resolved: list[dict],
                    outcomes: dict[str, dict], window_start: datetime, window_end: datetime
                    ) -> list[dict]:
    """Group tagged failures by (symbol, model_type, direction, signature)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    pred_by_id = {p["id"]: p for p in all_resolved}
    for t in tagged:
        key = (t["symbol"], pred_by_id.get(t["prediction_id"], {}).get("model_type") or "unknown",
               t["direction"], t.get("_signature") or "unknown")
        groups[key].append(t)

    # For win-rate computation, we need ALL resolved (not just failures) per group
    all_by_group: dict[tuple, list[dict]] = defaultdict(list)
    for p in all_resolved:
        # Re-derive direction
        d = p.get("ml_direction") or "HOLD"
        if d not in ("BUY", "SELL"):
            continue
        # Approximate signature from factors (using snapshot flags directly)
        f = p.get("factors")
        if isinstance(f, str):
            try: f = json.loads(f)
            except: f = {}
        elif not isinstance(f, dict):
            f = {}
        sig_parts: list[str] = []
        for flag, label in [("near_resistance", "near_resistance"), ("near_support", "near_support"),
                            ("overbought", "rsi_overbought_buy"), ("oversold", "rsi_oversold_sell"),
                            ("exhaustion_up", "exhaustion_up"), ("exhaustion_down", "exhaustion_down")]:
            if f.get(flag) is True:
                sig_parts.append(label)
        sig_parts.append(f"regime={f.get('regime_label') or 'unknown'}")
        sig = "|".join(sorted(set(sig_parts)))
        key = (p["symbol"], p.get("model_type") or "unknown", d, sig)
        all_by_group[key].append(p)

    clusters: list[dict] = []
    for key, fails in groups.items():
        if len(fails) < MIN_CLUSTER_SIZE:
            continue
        all_in_group = all_by_group.get(key, [])
        wins = sum(1 for p in all_in_group if p.get("status") == "completed")
        total_resolved = len(all_in_group)
        common_tags = Counter()
        for f in fails:
            for tag in (f.get("_tags") or []):
                common_tags[tag] += 1
        top_tags = [t for t, _ in common_tags.most_common(5)]
        rep_ids = [f["prediction_id"] for f in fails[:20]]
        confidences = [p.get("ml_confidence") or 0 for p in all_in_group]
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0
        # Total P/L (sum of MFE - MAE proxy from outcomes)
        total_pnl = 0.0
        for p in all_in_group:
            o = outcomes.get(p["id"])
            if not o:
                continue
            if p.get("status") == "completed":
                total_pnl += float(o.get("highest_profit_pips") or 0)
            elif p.get("status") == "stopped":
                total_pnl -= float(o.get("lowest_drawdown_pips") or 0)
        clusters.append({
            "symbol": key[0],
            "model_type": key[1],
            "direction": key[2],
            "cluster_signature": key[3],
            "common_tags": top_tags,
            "sample_size": len(fails),
            "win_rate": round(wins / total_resolved * 100, 2) if total_resolved else 0,
            "total_pnl_pips": round(total_pnl, 2),
            "avg_confidence": avg_conf,
            "representative_prediction_ids": rep_ids,
            "window_start": _iso(window_start),
            "window_end": _iso(window_end),
            "_failed_count": len(fails),
            "_total_resolved": total_resolved,
        })
    # Sort by impact: most failures first, then worst win-rate
    clusters.sort(key=lambda c: (-c["_failed_count"], c["win_rate"]))
    return clusters


async def _persist_clusters(client, clusters: list[dict]) -> list[dict]:
    """Insert cluster rows; return rows with their assigned IDs."""
    if not clusters:
        return []
    persisted: list[dict] = []
    for c in clusters:
        try:
            payload = {k: v for k, v in c.items() if not k.startswith("_")}
            r = client.table("failure_clusters").insert(payload)
            res = r.execute() if hasattr(r, "execute") else r
            data = res.get("data") if isinstance(res, dict) else getattr(res, "data", [])
            if data:
                persisted.append({**c, "id": data[0].get("id")})
        except Exception as e:
            logger.warning("[ai_ops] cluster insert failed: %s", e)
    return persisted


# ---------------------------------------------------------------------------
# Layer 2 — DeepSeek strategic analysis
# ---------------------------------------------------------------------------

DEEPSEEK_SYSTEM_PROMPT = """You are a quantitative trading systems analyst.
Your role: an external "operations manager" reviewing a cluster of failed
trading signals from a multi-model trading system. The system is ForexSAI:
  - Stack: FastAPI + LightGBM + Supabase + Next.js
  - 6 models: ML (XGBoost/LightGBM), PULSE 1/2/3 (algo+TA), EMEL (9-check),
    SMC (ICT/order-block), Meta (ensemble of all 6).
  - Symbols: XAUUSD, NDX.INDX, GDAXI.INDX, USOIL.FOREX

Given a cluster of similar failures, identify the root cause and propose
concrete, implementable remediation. Your output is reviewed by humans and
NOT auto-applied — be precise but don't be afraid to propose bold ideas.

ALWAYS reply with valid JSON in this exact schema:
{
  "root_cause": "<one paragraph hypothesis in plain English>",
  "severity": "critical|high|medium|low",
  "proposed_fixes": [
    {
      "type": "filter_rule|threshold_tweak|feature_addition|weight_adjustment|retrain",
      "description": "<plain language change>",
      "implementation_hint": "<code-level guidance: which file/function, pseudo-code>",
      "estimated_impact": "<X% of failures prevented, Y% of wins also affected>",
      "risk": "low|medium|high",

      // FOR filter_rule TYPE — REQUIRED for auto-simulation:
      "filter_spec": {
        "predicates": [
          {"field": "factors.regime_label", "op": "eq", "value": "ranging"},
          {"field": "factors.M30_rsi_14", "op": "gt", "value": 70},
          {"field": "factors.near_resistance", "op": "is_true", "value": null}
        ],
        "applies_to_direction": "BUY",
        "action": "block"
      },

      // FOR threshold_tweak TYPE — REQUIRED for auto-simulation:
      "threshold_spec": {
        "field": "ml_confidence",
        "op": "gte",
        "old_value": 60,
        "new_value": 65
      }
    }
  ],
  "alternative_explanations": ["<other plausible root cause>"],
  "requires_data": "<what additional data would help confirm/refute>"
}

Allowed predicate ops: eq, ne, gt, gte, lt, lte, in, not_in, is_true, is_false.
Field paths use 'factors.<key>' for snapshot fields, or top-level columns
like 'ml_confidence', 'ml_direction'. Snapshot keys you can reference include:
  factors.regime_label, factors.mtf_trend, factors.volatility_regime,
  factors.near_resistance, factors.near_support, factors.overbought,
  factors.oversold, factors.exhaustion_up, factors.exhaustion_down,
  factors.bb_extreme_upper, factors.bb_extreme_lower, factors.sar_bearish,
  factors.M30_rsi_14, factors.M30_adx_14, factors.M30_macd_hist,
  factors.M30_dist_swing_high_30_atr, factors.M30_dist_swing_low_30_atr,
  factors.M30_consec_green, factors.M30_consec_red, factors.H4_ema_stack,
  factors.H4_adx_14, factors.macro_dxy_chg1d_pct, factors.macro_vix_chg1d_pct.

Always include filter_spec or threshold_spec when proposing those types — the
system will counterfactually replay them on historical data and show the user
the simulated win-rate delta before they approve.
"""


def _build_user_prompt(cluster: dict, samples: list[dict]) -> str:
    """Compose the cluster description sent to DeepSeek."""
    sample_lines = []
    for s in samples[:10]:
        f = s.get("factors")
        if isinstance(f, str):
            try: f = json.loads(f)
            except: f = {}
        elif not isinstance(f, dict):
            f = {}
        # Pick the most informative fields for the LLM
        keys = ["regime_label", "mtf_trend", "volatility_regime",
                "near_resistance", "near_support", "overbought", "oversold",
                "exhaustion_up", "exhaustion_down", "sar_bearish",
                "M30_rsi_14", "M30_adx_14", "M30_macd_hist", "M30_dist_swing_high_30_atr",
                "M30_dist_swing_low_30_atr", "M30_consec_green", "M30_consec_red",
                "H4_ema_stack", "H4_adx_14", "macro_dxy_chg1d_pct", "macro_vix_chg1d_pct"]
        snap = {k: f.get(k) for k in keys if f.get(k) is not None}
        sample_lines.append(
            f"  - id={s['id'][:8]} entry={s.get('ml_entry_price')} stop={s.get('ml_stop_price')} "
            f"resolution={s.get('resolution_reason')} factors={json.dumps(snap, default=str)}"
        )
    return f"""Failure cluster summary:
  symbol: {cluster['symbol']}
  model_type: {cluster['model_type']}
  direction: {cluster['direction']}
  signature: {cluster['cluster_signature']}
  common_tags: {cluster.get('common_tags')}
  sample_size: {cluster['sample_size']} failures out of {cluster.get('_total_resolved', cluster['sample_size'])} resolved
  win_rate: {cluster['win_rate']}% (worse than the typical ~70-80% target)
  total_pnl_pips: {cluster.get('total_pnl_pips')}
  avg_confidence: {cluster.get('avg_confidence')}
  window: {cluster['window_start']} → {cluster['window_end']}

10 representative failures from this cluster (showing key factors):
{chr(10).join(sample_lines)}

Diagnose the root cause and propose remediation per the schema. Be concrete: which file/function to edit, what threshold to tweak, what feature to add."""


async def _call_deepseek(cluster: dict, samples: list[dict]) -> Optional[dict]:
    try:
        from services.deepseek_json_client import call_deepseek_json, DEEPSEEK_MODEL
    except ImportError:
        logger.warning("[ai_ops] deepseek client unavailable")
        return None
    user_prompt = _build_user_prompt(cluster, samples)
    # Existing client uses a single concatenated prompt; bundle system + user
    full_prompt = f"{DEEPSEEK_SYSTEM_PROMPT}\n\n---\n\n{user_prompt}"
    try:
        result = await call_deepseek_json(
            full_prompt,
            enforce_market_hours=False,    # AI-ops runs any time (not a trade decision)
            max_tokens=2000,                # Allow room for multiple proposed_fixes
            timeout_seconds=LLM_TIMEOUT_SECONDS,
        )
        if not isinstance(result, dict):
            logger.warning("[ai_ops] DeepSeek returned non-dict")
            return None
        return {"llm_model": result.get("ai_model") or DEEPSEEK_MODEL, "response": result}
    except Exception as e:
        logger.exception("[ai_ops] DeepSeek call failed: %s", e)
        return None


async def _persist_proposal(client, cluster_id: Optional[str], cluster: dict,
                            llm_out: dict) -> Optional[str]:
    resp = llm_out.get("response", {})
    payload = {
        "cluster_id": cluster_id,
        "symbol": cluster["symbol"],
        "model_type": cluster["model_type"],
        "severity": resp.get("severity") or "medium",
        "llm_model": llm_out.get("llm_model"),
        "root_cause": resp.get("root_cause"),
        "proposed_fixes": resp.get("proposed_fixes") or [],
        "alternative_explanations": resp.get("alternative_explanations") or [],
        "requires_data": resp.get("requires_data"),
        "raw_llm_response": json.dumps(resp, default=str)[:8000],
        "status": "pending",
        "pre_change_metric": {
            "win_rate": cluster["win_rate"],
            "sample_size": cluster["sample_size"],
            "total_pnl_pips": cluster.get("total_pnl_pips"),
        },
    }
    try:
        r = client.table("improvement_proposals").insert(payload)
        res = r.execute() if hasattr(r, "execute") else r
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", [])
        if data:
            return data[0].get("id")
    except Exception as e:
        logger.exception("[ai_ops] proposal insert failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

async def orchestrate_ai_ops(window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    """Run the full AI-ops cycle. Safe to call from cron daily."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        logger.warning("[ai_ops] supabase unavailable — aborting")
        return {"status": "skipped", "reason": "db_unavailable"}
    client = get_supabase_client()
    if client is None:
        return {"status": "skipped", "reason": "no_client"}

    end = _now()
    start = end - timedelta(days=window_days)
    logger.info("[ai_ops] running orchestration for window %s → %s", _iso(start), _iso(end))

    # 1) Pull resolved signals
    resolved = await _fetch_resolved_failures(client, _iso(start))
    logger.info("[ai_ops] fetched %d resolved signals", len(resolved))
    if not resolved:
        return {"status": "ok", "resolved": 0, "tagged": 0, "clusters": 0, "proposals": 0}

    # 2) Pull outcomes
    pred_ids = [p["id"] for p in resolved]
    outcomes = await _fetch_outcome_map(client, pred_ids)
    logger.info("[ai_ops] fetched %d outcomes", len(outcomes))

    # 3) Tag failures (Layer 1)
    from services.failure_tagger import tag_failure
    tagged = []
    for p in resolved:
        rec = tag_failure(p, outcomes.get(p["id"]))
        if rec:
            tagged.append(rec)
    inserted = await _persist_tags(client, tagged)
    logger.info("[ai_ops] tagged %d failures, persisted %d", len(tagged), inserted)

    # 4) Cluster
    clusters = _build_clusters(tagged, resolved, outcomes, start, end)
    logger.info("[ai_ops] built %d clusters (>=%d samples)", len(clusters), MIN_CLUSTER_SIZE)
    persisted_clusters = await _persist_clusters(client, clusters)

    # 5) Send top clusters to DeepSeek (Layer 2)
    proposals = 0
    sent = 0
    for cluster in persisted_clusters[:MAX_LLM_CLUSTERS_PER_RUN]:
        # Pull full prediction_log rows for the representative IDs (samples)
        samples: list[dict] = []
        for pid in cluster.get("representative_prediction_ids", [])[:10]:
            for p in resolved:
                if p["id"] == pid:
                    samples.append(p)
                    break
        llm_out = await _call_deepseek(cluster, samples)
        sent += 1
        if not llm_out:
            continue
        prop_id = await _persist_proposal(client, cluster.get("id"), cluster, llm_out)
        if prop_id:
            proposals += 1
            # Mark cluster as sent
            try:
                client.table("failure_clusters").update(
                    {"sent_to_llm": True, "proposal_id": prop_id}
                ).eq("id", cluster["id"])
            except Exception:
                pass
            # Counterfactual simulation — fire-and-forget; persists into the same row
            try:
                from services.proposal_simulator import simulate_and_persist
                await simulate_and_persist(prop_id, window_days=60)
            except Exception as sim_err:
                logger.warning("[ai_ops] proposal simulation failed for %s: %s",
                               prop_id, sim_err)

    summary = {
        "status": "ok",
        "window_days": window_days,
        "resolved_signals": len(resolved),
        "tagged_failures": len(tagged),
        "clusters_total": len(clusters),
        "clusters_sent_to_llm": sent,
        "proposals_created": proposals,
    }
    logger.info("[ai_ops] cycle complete: %s", summary)
    return summary
