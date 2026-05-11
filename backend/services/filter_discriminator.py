"""
Filter Discriminator — derinlik analizi.

Bir öneri filter'ı 329 fail + 208 win birden bloklarsa (precision %61),
"kazançları kurtarmak için" hangi feature wins ile fails arasında fark
yaratıyor sorusuna cevap arar.

Workflow:
  1. Proposal'ı al + filter_spec'i çıkar (proposed_fixes[0])
  2. Son 60g sinyallerini al, filter ile match olanları bul → blocked set
  3. Blocked'i 2 gruba ayır: wins (status=completed) + fails (status=stopped)
  4. Her aday feature için win/fail dağılımının ayrımını ölç:
        - Numeric → best threshold ve (above/below win-rate farkı)
        - Categorical → her kategori için win/fail oranı
  5. En güçlü 3 discriminator'ı sırala
  6. Top discriminator için "refined filter" öner: original_filter AND NOT (discriminator condition)
        → kurtarılabilecek win sayısı, hala blocklanan fail sayısı
  7. Refined precision/win-rate/P-L hesapla, original'a göre delta'la kıyasla

Output: ranked discriminators + recommended refinement spec (filter_matcher uyumlu).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Snapshot factor key'ler — discriminator olarak test edilecek
NUMERIC_FEATURES = [
    "M30_rsi_14", "H1_rsi_14", "H4_rsi_14",
    "M30_adx_14", "H1_adx_14", "H4_adx_14",
    "M30_macd_hist", "M30_macd_hist_atr",
    "M30_bb_pctb", "M30_atr_pct", "M30_atr_ratio_50",
    "M30_dist_swing_high_30_atr", "M30_dist_swing_low_30_atr",
    "M30_consec_green", "M30_consec_red",
    "M30_chan_pct", "M30_sar_dist_atr",
    "M30_upper_wick_5_atr", "M30_lower_wick_5_atr",
    "M30_dist_ema20_atr", "M30_dist_ema50_atr", "M30_dist_ema200_atr",
    "H4_adx_14", "H4_rsi_14",
    "macro_dxy_chg1d_pct", "macro_vix_chg1d_pct", "macro_us10y_chg1d_pct",
    "macro_vix_price",
    "ml_confidence",
    "hour_utc",
]
CATEGORICAL_FEATURES = [
    "regime_label", "mtf_trend", "volatility_regime", "session",
    "H4_ema_stack", "H1_ema_stack", "M30_ema_stack",
    "H4_adx_label", "M30_adx_label",
    "macro_event_proximity",
]
# Min sample sizes for confident discrimination
MIN_WINS_FOR_ANALYSIS = 5
MIN_FAILS_FOR_ANALYSIS = 5
MIN_SAMPLES_PER_GROUP = 3  # within each side of a threshold split


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_factors(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {}
    return {}


def _extract_value(signal: dict, key: str) -> Any:
    """Snapshot factor OR top-level column."""
    if key == "ml_confidence":
        return signal.get("ml_confidence")
    if key == "hour_utc":
        ts = signal.get("created_at")
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
            except Exception:
                return None
        return None
    factors = _parse_factors(signal.get("factors"))
    return factors.get(key)


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return f


# ---------------------------------------------------------------------------
# Filter spec evaluation (mirrors proposal_simulator semantics)
# ---------------------------------------------------------------------------

import operator
_OPS = {
    "eq": operator.eq, "ne": operator.ne,
    "gt": operator.gt, "gte": operator.ge,
    "lt": operator.lt, "lte": operator.le,
    "in": lambda a, b: a in b if isinstance(b, (list, tuple)) else False,
    "is_true": lambda a, _: bool(a) is True,
    "is_false": lambda a, _: bool(a) is False,
}


def _resolve_path(signal: dict, path: str) -> Any:
    if not path:
        return None
    parts = path.split(".")
    if parts[0] == "factors":
        factors = _parse_factors(signal.get("factors"))
        cur: Any = factors
        for p in parts[1:]:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                return None
        return cur
    return signal.get(parts[0])


def _signal_matches_filter(signal: dict, filter_spec: dict) -> bool:
    direction_filter = filter_spec.get("applies_to_direction")
    if direction_filter and direction_filter != "ANY":
        if signal.get("ml_direction") != direction_filter:
            return False
    for pred in filter_spec.get("predicates") or []:
        fn = _OPS.get(pred.get("op", "eq"))
        if fn is None:
            return False
        actual = _resolve_path(signal, pred.get("field", ""))
        try:
            if not bool(fn(actual, pred.get("value"))):
                return False
        except Exception:
            return False
    return True


# ---------------------------------------------------------------------------
# Numeric discriminator: find threshold that best separates wins from fails
# ---------------------------------------------------------------------------

def _best_numeric_threshold(values_win: list[float], values_fail: list[float]
                             ) -> Optional[dict]:
    """Find threshold T where the gap between (% wins above T) and (% fails
    above T) is maximized — Kolmogorov-Smirnov-like single-split."""
    if (len(values_win) < MIN_SAMPLES_PER_GROUP
            or len(values_fail) < MIN_SAMPLES_PER_GROUP):
        return None
    all_vals = sorted(set(values_win + values_fail))
    if len(all_vals) < 2:
        return None
    best = None
    n_win = len(values_win)
    n_fail = len(values_fail)
    for t in all_vals:
        wins_above = sum(1 for v in values_win if v > t)
        fails_above = sum(1 for v in values_fail if v > t)
        wins_below = n_win - wins_above
        fails_below = n_fail - fails_above
        # Avoid edge splits with too-small subgroups
        if (min(wins_above, fails_above) < MIN_SAMPLES_PER_GROUP
                and min(wins_below, fails_below) < MIN_SAMPLES_PER_GROUP):
            continue
        win_rate_above = wins_above / n_win
        fail_rate_above = fails_above / n_fail
        # Two-sided separation — pick the direction where wins cluster
        sep_above = win_rate_above - fail_rate_above
        sep_below = (wins_below / n_win) - (fails_below / n_fail)
        if abs(sep_above) >= abs(sep_below):
            sep = sep_above
            direction = "above"  # wins are above threshold
            wins_in_rescue = wins_above
            fails_re_allowed = fails_above
        else:
            sep = sep_below
            direction = "below"  # wins are below threshold
            wins_in_rescue = wins_below
            fails_re_allowed = fails_below
        if best is None or abs(sep) > abs(best["separation"]):
            best = {
                "threshold": float(t),
                "direction": direction,
                "separation": float(sep),
                "wins_in_rescue": int(wins_in_rescue),
                "fails_re_allowed": int(fails_re_allowed),
                "rescue_ratio": float(wins_in_rescue / max(n_win, 1)),
                "fail_leak_ratio": float(fails_re_allowed / max(n_fail, 1)),
            }
    return best


def _categorical_discriminator(values_win: list[str], values_fail: list[str]
                                ) -> Optional[dict]:
    """For categorical features, find the category most over-represented in wins."""
    if not values_win or not values_fail:
        return None
    from collections import Counter
    win_counts = Counter(values_win)
    fail_counts = Counter(values_fail)
    n_win = len(values_win)
    n_fail = len(values_fail)
    best = None
    for cat in set(list(win_counts) + list(fail_counts)):
        w = win_counts.get(cat, 0)
        f = fail_counts.get(cat, 0)
        if w + f < MIN_SAMPLES_PER_GROUP:
            continue
        sep = (w / max(n_win, 1)) - (f / max(n_fail, 1))
        if best is None or abs(sep) > abs(best["separation"]):
            best = {
                "category": str(cat),
                "separation": float(sep),
                "wins_in_category": w,
                "fails_in_category": f,
                "wins_in_rescue": w,
                "fails_re_allowed": f,
                "rescue_ratio": float(w / max(n_win, 1)),
                "fail_leak_ratio": float(f / max(n_fail, 1)),
            }
    return best


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

async def _fetch_blocked_signals(client, symbol: str, model_type: Optional[str],
                                    days: int, filter_spec: dict) -> tuple[list[dict], list[dict]]:
    """Return (wins, fails) lists for signals matching the filter."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    q = client.table("prediction_logs").select(
        "id,symbol,model_type,ml_direction,ml_confidence,status,resolution_reason,"
        "factors,created_at,timeframe"
    ).eq("symbol", symbol).gte("created_at", since).in_(
        "status", ["completed", "stopped"]
    ).limit(10000)
    if model_type:
        q = q.eq("model_type", model_type)
    res = q.execute() if hasattr(q, "execute") else q
    data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
    blocked = [s for s in (data or []) if _signal_matches_filter(s, filter_spec)]
    wins = [s for s in blocked if s.get("status") == "completed"]
    fails = [s for s in blocked if s.get("status") == "stopped"]
    return wins, fails


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

async def analyze_discriminators(proposal_id: str, days: int = 60) -> dict:
    """For a proposal, hunt for features that separate the blocked WINS
    from blocked FAILS within the same filter signature."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"status": "error", "error": "db_unavailable"}
    client = get_supabase_client()

    # 1. Pull proposal
    rows = client.table("improvement_proposals").select(
        "id,symbol,model_type,proposed_fixes"
    ).eq("id", proposal_id).limit(1)
    res = rows.execute() if hasattr(rows, "execute") else rows
    data = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []
    if not data:
        return {"status": "error", "error": "proposal_not_found"}
    prop = data[0]

    fixes = prop.get("proposed_fixes") or []
    if isinstance(fixes, str):
        try: fixes = json.loads(fixes)
        except Exception: fixes = []
    filter_fix = next(
        (f for f in fixes if isinstance(f, dict) and f.get("type") == "filter_rule"),
        None)
    if not filter_fix or not filter_fix.get("filter_spec"):
        return {"status": "error",
                "error": "no_filter_rule_with_spec",
                "note": "Discriminator analysis only works for filter_rule type fixes."}
    filter_spec = filter_fix["filter_spec"]

    # 2. Pull blocked subset
    wins, fails = await _fetch_blocked_signals(
        client, prop["symbol"], prop.get("model_type"), days, filter_spec)

    if len(wins) < MIN_WINS_FOR_ANALYSIS or len(fails) < MIN_FAILS_FOR_ANALYSIS:
        return {
            "status": "insufficient_data",
            "n_wins": len(wins), "n_fails": len(fails),
            "min_required": {"wins": MIN_WINS_FOR_ANALYSIS, "fails": MIN_FAILS_FOR_ANALYSIS},
        }

    # 3. Per-feature discriminator hunt
    discriminators: list[dict] = []

    for feat in NUMERIC_FEATURES:
        win_vals = [_to_float(_extract_value(s, feat)) for s in wins]
        fail_vals = [_to_float(_extract_value(s, feat)) for s in fails]
        win_vals = [v for v in win_vals if v is not None]
        fail_vals = [v for v in fail_vals if v is not None]
        if (len(win_vals) < MIN_SAMPLES_PER_GROUP
                or len(fail_vals) < MIN_SAMPLES_PER_GROUP):
            continue
        result = _best_numeric_threshold(win_vals, fail_vals)
        if result is None:
            continue
        discriminators.append({
            "feature": feat, "type": "numeric",
            "win_n": len(win_vals), "fail_n": len(fail_vals),
            "win_mean": round(float(np.mean(win_vals)), 4),
            "fail_mean": round(float(np.mean(fail_vals)), 4),
            "win_median": round(float(np.median(win_vals)), 4),
            "fail_median": round(float(np.median(fail_vals)), 4),
            **result,
            "abs_separation": abs(result["separation"]),
        })

    for feat in CATEGORICAL_FEATURES:
        win_vals = [str(_extract_value(s, feat)) for s in wins
                     if _extract_value(s, feat) is not None]
        fail_vals = [str(_extract_value(s, feat)) for s in fails
                     if _extract_value(s, feat) is not None]
        if not win_vals or not fail_vals:
            continue
        result = _categorical_discriminator(win_vals, fail_vals)
        if result is None:
            continue
        discriminators.append({
            "feature": feat, "type": "categorical",
            "win_n": len(win_vals), "fail_n": len(fail_vals),
            **result,
            "abs_separation": abs(result["separation"]),
        })

    discriminators.sort(key=lambda d: -d["abs_separation"])

    # 4. Build refined filter recommendation from top discriminator
    refined_filter: Optional[dict] = None
    if discriminators and discriminators[0]["abs_separation"] >= 0.15:
        top = discriminators[0]
        # Build an EXTRA predicate that, when added (with negation), rescues wins.
        # The recommended_refinement is: ORIGINAL_FILTER AND NOT (top_discriminator_condition)
        # — i.e. don't block signals matching the win-prone subset.
        if top["type"] == "numeric":
            # Wins cluster above threshold → exclude those: filter only fires
            # when value <= threshold (or vice versa)
            if top["direction"] == "above":
                # Wins are above threshold → block only when value <= threshold
                guard_op = "lte"
            else:
                # Wins are below → block only when value >= threshold
                guard_op = "gte"
            # The exclusion predicate to ADD to the original filter:
            extra_pred = {
                "field": (f"factors.{top['feature']}"
                          if top["feature"] not in ("ml_confidence", "hour_utc")
                          else top["feature"]),
                "op": guard_op,
                "value": top["threshold"],
            }
            human_rule = (
                f"Add `{extra_pred['field']} {guard_op} {extra_pred['value']}` "
                f"to the existing filter — rescues "
                f"{top['wins_in_rescue']}/{top['win_n']} wins "
                f"while only re-allowing {top['fails_re_allowed']}/{top['fail_n']} fails."
            )
        else:  # categorical
            # Wins cluster in one category → exclude that category: add ne predicate
            extra_pred = {
                "field": (f"factors.{top['feature']}"
                          if top["feature"] != "ml_confidence" else top["feature"]),
                "op": "ne",
                "value": top["category"],
            }
            human_rule = (
                f"Add `{extra_pred['field']} ne '{top['category']}'` to the existing "
                f"filter — rescues {top['wins_in_rescue']}/{top['win_n']} wins "
                f"while only re-allowing {top['fails_re_allowed']}/{top['fail_n']} fails."
            )

        # Simulate refined performance
        new_n_wins = top["win_n"] - top["wins_in_rescue"]
        new_n_fails = top["fail_n"] - top["fails_re_allowed"]
        new_precision = (new_n_fails / (new_n_wins + new_n_fails) * 100
                         if (new_n_wins + new_n_fails) > 0 else None)
        refined_filter = {
            "rule": human_rule,
            "extra_predicate": extra_pred,
            "refined_filter_spec": {
                **filter_spec,
                "predicates": list(filter_spec.get("predicates") or []) + [extra_pred],
            },
            "expected": {
                "wins_rescued": top["wins_in_rescue"],
                "fails_re_allowed": top["fails_re_allowed"],
                "new_blocked_fails": new_n_fails,
                "new_blocked_wins": new_n_wins,
                "new_precision_pct": round(new_precision, 2)
                                      if new_precision is not None else None,
                "fail_block_efficacy_loss_pct": round(
                    top["fails_re_allowed"] / max(top["fail_n"], 1) * 100, 2),
            },
        }

    # 5. Original metrics (for delta comparison on the UI)
    n_wins, n_fails = len(wins), len(fails)
    original = {
        "n_blocked": n_wins + n_fails,
        "n_wins_blocked": n_wins,
        "n_fails_blocked": n_fails,
        "precision_pct": round(n_fails / (n_wins + n_fails) * 100, 2)
                          if (n_wins + n_fails) > 0 else None,
    }

    return {
        "status": "ok",
        "proposal_id": proposal_id,
        "window_days": days,
        "symbol": prop["symbol"],
        "model_type": prop.get("model_type"),
        "original": original,
        "discriminators_top": discriminators[:8],
        "recommended_refinement": refined_filter,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
