"""
Proposal Simulator — counterfactual backtest for AI-ops improvement proposals.

For each fix in a proposal, replays it against last N days of resolved signals
to answer: "If this fix had been live, what would the metrics look like?"

Supports two fix types out of the box (auto-simulatable):
  - filter_rule:    {predicates: [{field, op, value}], applies_to_direction, action}
                    → block signals whose predicates all match
  - threshold_tweak: {field, op, new_value}
                    → block signals that fail the new threshold

Other types (feature_addition, weight_adjustment, retrain) require code/model
changes and are returned with status='manual_review_required'.

Lazy vectorbt import: when present, used for grid search later. The core
simulation here is plain pandas — fast enough for proposal validation
(single config × thousands of signals, sub-second).
"""
from __future__ import annotations

import json
import logging
import operator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_WINDOW_DAYS = 60
MAX_SIGNALS = 10000  # safety cap

# Operators allowed in filter predicates — no eval, deterministic mapping
OPS: dict[str, callable] = {
    "eq":  operator.eq,
    "ne":  operator.ne,
    "gt":  operator.gt,
    "gte": operator.ge,
    "lt":  operator.lt,
    "lte": operator.le,
    "in":  lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
    "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple)) else True,
    "is_true":  lambda a, _: bool(a) is True,
    "is_false": lambda a, _: bool(a) is False,
}


@dataclass
class SimulationResult:
    status: str                       # ok | manual_review_required | error
    window_days: int
    original: dict
    simulated: dict
    deltas: dict
    fixes_evaluated: list[dict]
    fixes_skipped: list[dict]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "window_days": self.window_days,
            "original": self.original,
            "simulated": self.simulated,
            "deltas": self.deltas,
            "fixes_evaluated": self.fixes_evaluated,
            "fixes_skipped": self.fixes_skipped,
            "error": self.error,
            "simulated_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Predicate evaluator
# ---------------------------------------------------------------------------

def _resolve_field(row: pd.Series, dotted_path: str) -> Any:
    """Lookup `factors.M30_rsi_14` style paths against the dataframe row."""
    if not dotted_path:
        return None
    parts = dotted_path.split(".")
    if parts[0] == "factors":
        f = row.get("factors")
        if isinstance(f, str):
            try: f = json.loads(f)
            except Exception: f = {}
        if not isinstance(f, dict):
            return None
        cur: Any = f
        for p in parts[1:]:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
        return cur
    return row.get(parts[0])


def _eval_predicate(row: pd.Series, pred: dict) -> bool:
    field = pred.get("field")
    op = pred.get("op", "eq")
    value = pred.get("value")
    actual = _resolve_field(row, field)
    fn = OPS.get(op)
    if fn is None:
        return False
    try:
        return bool(fn(actual, value))
    except Exception:
        return False


def _signal_blocked_by_filter(row: pd.Series, spec: dict) -> bool:
    """All predicates must match for signal to be blocked."""
    direction_filter = spec.get("applies_to_direction")
    if direction_filter and direction_filter != "ANY" and row.get("ml_direction") != direction_filter:
        return False
    preds = spec.get("predicates") or []
    if not preds:
        return False
    for p in preds:
        if not _eval_predicate(row, p):
            return False
    return True


def _signal_blocked_by_threshold(row: pd.Series, spec: dict) -> bool:
    """A threshold tweak BLOCKS signals failing the new threshold (op holds for KEEP)."""
    field = spec.get("field")
    new_value = spec.get("new_value")
    op = spec.get("op", "gte")
    actual = _resolve_field(row, field)
    if actual is None or new_value is None:
        return False
    fn = OPS.get(op)
    if fn is None:
        return False
    try:
        # op describes the KEEP condition. If it fails → block.
        return not bool(fn(actual, new_value))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _signal_pnl_pips(row: pd.Series) -> float:
    """Best-effort P/L in pips from outcome data attached to the row."""
    status = row.get("status")
    mfe = row.get("highest_profit_pips") or 0
    mae = row.get("lowest_drawdown_pips") or 0
    if status == "completed":
        return float(mfe)
    if status == "stopped":
        return -float(mae)
    return 0.0


def _compute_metrics(df: pd.DataFrame, label: str) -> dict:
    n = len(df)
    if n == 0:
        return {"label": label, "n_signals": 0, "win_rate": None, "total_pnl_pips": 0}
    wins = (df["status"] == "completed").sum()
    resolved = df["status"].isin(["completed", "stopped"]).sum()
    pnl = df.apply(_signal_pnl_pips, axis=1).sum()
    return {
        "label": label,
        "n_signals": int(n),
        "n_resolved": int(resolved),
        "n_wins": int(wins),
        "win_rate": round(float(wins / resolved * 100), 2) if resolved else None,
        "total_pnl_pips": round(float(pnl), 2),
        "avg_pnl_pips": round(float(pnl / resolved), 3) if resolved else None,
    }


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

async def _fetch_signals(client, symbol: str, model_type: Optional[str],
                          window_days: int) -> pd.DataFrame:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    since_iso = since.isoformat()

    q = client.table("prediction_logs").select(
        "id,symbol,model_type,ml_direction,ml_confidence,status,resolution_reason,"
        "ml_entry_price,ml_target_price,ml_stop_price,factors,created_at,timeframe"
    ).eq("symbol", symbol).gte("created_at", since_iso).in_(
        "status", ["completed", "stopped"]
    ).limit(MAX_SIGNALS)
    if model_type and model_type != "any":
        q = q.eq("model_type", model_type)

    rows = q.execute() if hasattr(q, "execute") else q
    data = rows.get("data") if isinstance(rows, dict) else getattr(rows, "data", []) or []
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)

    # Attach outcome data
    pred_ids = df["id"].tolist()
    outcomes: dict[str, dict] = {}
    for i in range(0, len(pred_ids), 200):
        chunk = pred_ids[i:i + 200]
        try:
            r = client.table("outcome_results").select(
                "prediction_id,highest_profit_pips,lowest_drawdown_pips"
            ).in_("prediction_id", chunk)
            res = r.execute() if hasattr(r, "execute") else r
            data2 = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
            for o in data2:
                outcomes[o["prediction_id"]] = o
        except Exception as e:
            logger.warning("[simulator] outcome chunk failed: %s", e)
    df["highest_profit_pips"] = df["id"].map(lambda i: outcomes.get(i, {}).get("highest_profit_pips"))
    df["lowest_drawdown_pips"] = df["id"].map(lambda i: outcomes.get(i, {}).get("lowest_drawdown_pips"))
    return df


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

AUTO_SIMULATABLE = {"filter_rule", "threshold_tweak"}


async def simulate_proposal(proposal_id: str,
                             window_days: int = DEFAULT_WINDOW_DAYS) -> SimulationResult:
    """Run counterfactual replay of a proposal's fixes against historical signals."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return SimulationResult("error", window_days, {}, {}, {}, [], [], "db_unavailable")
    client = get_supabase_client()

    # 1) Pull the proposal
    try:
        rows = client.table("improvement_proposals").select(
            "id,symbol,model_type,proposed_fixes"
        ).eq("id", proposal_id).limit(1)
        res = rows.execute() if hasattr(rows, "execute") else rows
        data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
        if not data:
            return SimulationResult("error", window_days, {}, {}, {}, [], [], "proposal_not_found")
        prop = data[0]
    except Exception as e:
        logger.exception("[simulator] proposal fetch failed: %s", e)
        return SimulationResult("error", window_days, {}, {}, {}, [], [], str(e))

    fixes = prop.get("proposed_fixes") or []
    if isinstance(fixes, str):
        try: fixes = json.loads(fixes)
        except Exception: fixes = []

    auto_fixes = [f for f in fixes if isinstance(f, dict) and f.get("type") in AUTO_SIMULATABLE]
    skipped = [{"type": f.get("type"), "description": f.get("description"),
                "reason": "non-simulatable type"}
               for f in fixes if isinstance(f, dict) and f.get("type") not in AUTO_SIMULATABLE]

    if not auto_fixes:
        return SimulationResult(
            "manual_review_required", window_days,
            {}, {}, {}, [], skipped,
            error=None,
        )

    # 2) Pull historical signals for this symbol/model
    df = await _fetch_signals(client, prop["symbol"], prop.get("model_type"), window_days)
    if df.empty:
        return SimulationResult(
            "ok", window_days,
            {"label": "original", "n_signals": 0},
            {"label": "simulated", "n_signals": 0},
            {"win_rate_pp": 0, "pnl_pips": 0},
            [], skipped,
            error="no_historical_signals_in_window",
        )

    # 3) Build "would be blocked" mask across all auto-simulatable fixes (OR logic —
    #    if ANY proposed filter would have caught the signal, it's counted as blocked)
    blocked_mask = pd.Series([False] * len(df), index=df.index)
    fixes_evaluated: list[dict] = []
    for fix in auto_fixes:
        ftype = fix.get("type")
        if ftype == "filter_rule":
            spec = fix.get("filter_spec") or {}
            if not spec.get("predicates"):
                skipped.append({"type": ftype, "description": fix.get("description"),
                                "reason": "missing filter_spec.predicates"})
                continue
            mask = df.apply(lambda r: _signal_blocked_by_filter(r, spec), axis=1)
        elif ftype == "threshold_tweak":
            spec = fix.get("threshold_spec") or {}
            if not spec.get("field") or spec.get("new_value") is None:
                skipped.append({"type": ftype, "description": fix.get("description"),
                                "reason": "missing threshold_spec.field or new_value"})
                continue
            mask = df.apply(lambda r: _signal_blocked_by_threshold(r, spec), axis=1)
        else:
            continue
        n_blocked = int(mask.sum())
        fixes_evaluated.append({
            "type": ftype,
            "description": fix.get("description"),
            "n_blocked": n_blocked,
            "block_rate_pct": round(n_blocked / len(df) * 100, 2),
        })
        blocked_mask = blocked_mask | mask

    # 4) Compute metrics
    original = _compute_metrics(df, "original")
    kept = df[~blocked_mask]
    simulated = _compute_metrics(kept, "simulated")
    blocked = df[blocked_mask]

    # Of the blocked signals, how many were FAILS we successfully prevented?
    blocked_fails = int((blocked["status"] == "stopped").sum())
    blocked_wins = int((blocked["status"] == "completed").sum())
    blocked_pnl = float(blocked.apply(_signal_pnl_pips, axis=1).sum())

    deltas = {
        "win_rate_pp": (round(simulated.get("win_rate", 0) - original.get("win_rate", 0), 2)
                        if simulated.get("win_rate") is not None and original.get("win_rate") is not None
                        else None),
        "pnl_pips": round(simulated.get("total_pnl_pips", 0) - original.get("total_pnl_pips", 0), 2),
        "n_signals_blocked": int(blocked_mask.sum()),
        "blocked_pnl_avoided": round(-blocked_pnl, 2),  # if we saved net negative P/L, this is positive
        "blocked_was_loss": blocked_fails,
        "blocked_was_win": blocked_wins,
    }

    return SimulationResult(
        "ok", window_days,
        original, simulated, deltas,
        fixes_evaluated, skipped,
    )


async def simulate_and_persist(proposal_id: str, window_days: int = DEFAULT_WINDOW_DAYS) -> dict:
    """Run simulation + write result back to improvement_proposals.simulated_metric."""
    from database.supabase_client import get_supabase_client
    result = await simulate_proposal(proposal_id, window_days=window_days)
    payload = result.to_dict()
    try:
        client = get_supabase_client()
        if client is not None:
            client.table("improvement_proposals").update({
                "simulated_metric": payload,
                "simulated_at": payload["simulated_at"],
            }).eq("id", proposal_id)
    except Exception as e:
        logger.exception("[simulator] persist failed: %s", e)
        payload["persist_error"] = str(e)
    return payload
