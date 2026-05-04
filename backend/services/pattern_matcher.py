"""
Pattern Matcher — runtime evaluation of mined rules against live signals.

Loads `xauusdegitim/pattern_rules.json` (output of pattern_miner.py) and lets
any signal generator answer: "Does the current market state match a known
HIGH-WIN-RATE pattern (≥75%) or a known TOXIC pattern (≤35%) for this symbol
and model?"

Used by:
  - meta_analysis_engine: returns matched patterns alongside signal so frontend
    can flash a "trusted setup detected" indicator
  - AI-Ops orchestrator: future seeding of improvement_proposals from validated
    historical patterns

Architecture:
  - Single-load on first call, in-memory cache (rules don't change at runtime)
  - Pure-Python predicate evaluator, no eval()
  - Bucket boundaries duplicated from pattern_miner.py for self-contained matching
  - Returns rich metadata so UI can render details (win-rate, sample size)

Threshold knobs:
  WINNING_MIN_WIN_RATE = 75  (was 85, lowered per user)
  TOXIC_MAX_WIN_RATE   = 35
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

WINNING_MIN_WIN_RATE = 75.0   # ≥ this: trusted setup
TOXIC_MAX_WIN_RATE = 35.0      # ≤ this: avoid setup
MIN_SAMPLE_SIZE = 20           # rule must have at least this many historical trades

RULES_PATH = Path(__file__).resolve().parent.parent.parent / "xauusdegitim" / "pattern_rules.json"

# Bucket bins — MUST match pattern_miner.py CONTINUOUS_BINS exactly
BINS = {
    "rsi": [-np.inf, 30, 50, 65, 75, np.inf],
    "adx": [-np.inf, 18, 25, 35, np.inf],
    "macd_hist_atr": [-np.inf, -0.3, 0, 0.3, np.inf],
    "bb_pctb": [-np.inf, 0.2, 0.5, 0.8, np.inf],
    "ml_confidence": [-np.inf, 50, 60, 70, 80, np.inf],
    "atr_ratio": [-np.inf, 0.7, 1.0, 1.3, 1.7, np.inf],
    "consec_streak": [-np.inf, 0, 2, 4, 6, np.inf],
    "dist_swing_atr": [-np.inf, 0.3, 0.7, 1.5, np.inf],
    "dxy_chg1d": [-np.inf, -0.5, 0, 0.5, np.inf],
    "vix_chg1d": [-np.inf, -3, 0, 3, np.inf],
    "us10y_chg1d": [-np.inf, -0.5, 0, 0.5, np.inf],
}

# Mining-table column → snapshot-factor key
FIELD_MAP = {
    "rsi_M30":         ("M30_rsi_14", "rsi"),
    "rsi_H1":          ("H1_rsi_14", "rsi"),
    "rsi_H4":          ("H4_rsi_14", "rsi"),
    "adx_M30":         ("M30_adx_14", "adx"),
    "adx_H1":          ("H1_adx_14", "adx"),
    "adx_H4":          ("H4_adx_14", "adx"),
    "macd_atr_M30":    ("M30_macd_hist_atr", "macd_hist_atr"),
    "bb_pctb_M30":     ("M30_bb_pctb", "bb_pctb"),
    "atr_ratio_M30":   ("M30_atr_ratio_50", "atr_ratio"),
    "dist_high_M30":   ("M30_dist_swing_high_30_atr", "dist_swing_atr"),
    "dist_low_M30":    ("M30_dist_swing_low_30_atr", "dist_swing_atr"),
    "consec_green_M30": ("M30_consec_green", "consec_streak"),
    "consec_red_M30":   ("M30_consec_red", "consec_streak"),
    "dxy_chg1d":       ("macro_dxy_chg1d_pct", "dxy_chg1d"),
    "vix_chg1d":       ("macro_vix_chg1d_pct", "vix_chg1d"),
    "us10y_chg1d":     ("macro_us10y_chg1d_pct", "us10y_chg1d"),
}

# Rules cache
_rules_cache: Optional[list[dict]] = None
_rules_loaded_at: Optional[datetime] = None
_rules_mtime: float = 0.0


# ---------------------------------------------------------------------------
# Bucketing (must match pattern_miner._bucket_label exactly)
# ---------------------------------------------------------------------------

def _bucket_label(value: Any, bin_family: str) -> str:
    if value is None:
        return "NA"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "NA"
    if not np.isfinite(v):
        return "NA"
    bins = BINS[bin_family]
    for i in range(len(bins) - 1):
        if bins[i] <= v < bins[i + 1]:
            lo = "−∞" if bins[i] == -np.inf else f"{bins[i]:g}"
            hi = "+∞" if bins[i + 1] == np.inf else f"{bins[i + 1]:g}"
            return f"[{lo},{hi})"
    return "NA"


def _ml_confidence_bucket(conf: Any) -> str:
    return _bucket_label(conf, "ml_confidence")


# ---------------------------------------------------------------------------
# Live snapshot enrichment — make raw factors evaluable against rule strings
# ---------------------------------------------------------------------------

def _session_phase_label(symbol: str, ts: datetime) -> str:
    """Mirror of pattern_miner._session_phase_label."""
    h, m = ts.hour, ts.minute
    s = symbol.upper()
    if "NDX" in s or "SPX" in s:
        minutes = h * 60 + m
        if 14 * 60 + 30 <= minutes < 14 * 60 + 30 + 60:  return "open_drive"
        if 14 * 60 + 30 + 60 <= minutes < 19 * 60:        return "mid_session"
        if 19 * 60 <= minutes < 21 * 60:                  return "close_drive"
        if 21 * 60 <= minutes or minutes < 14 * 60 + 30:  return "after_hours"
        return "pre_market"
    if "GDAXI" in s or "DAX" in s:
        minutes = h * 60 + m
        if 8 * 60 <= minutes < 9 * 60:    return "open_drive"
        if 9 * 60 <= minutes < 14 * 60:   return "mid_session"
        if 14 * 60 <= minutes < 16 * 60 + 30:  return "us_overlap"
        if 16 * 60 + 30 <= minutes < 17 * 60 + 30:  return "close_auction"
        return "after_hours"
    if "OIL" in s:
        if 13 <= h < 16:   return "early_pit"
        if 16 <= h < 18:   return "active_pit"
        if 18 <= h < 22:   return "late_pit"
        return "off_hours"
    return "any"


def _macro_alignment(symbol: str, direction: str, dxy: float | None,
                     vix: float | None, us10y: float | None) -> str:
    """Mirror of pattern_miner._signal_macro_alignment."""
    if direction not in ("BUY", "SELL"):
        return "NA"
    s = symbol.upper().replace(".INDX", "").replace(".FOREX", "")
    sign = 1 if direction == "BUY" else -1
    score = 0
    have = 0
    if "XAU" in s or s == "GOLD":
        if dxy is not None:
            have += 1; score += -sign if dxy > 0.1 else (sign if dxy < -0.1 else 0)
        if us10y is not None:
            have += 1; score += -sign if us10y > 0.05 else (sign if us10y < -0.05 else 0)
        if vix is not None:
            have += 1; score += sign if vix > 1.0 else (-sign if vix < -1.0 else 0)
    elif s in ("NDX", "GDAXI", "DAX", "SPX"):
        if vix is not None:
            have += 1; score += -sign if vix > 1.0 else (sign if vix < -1.0 else 0)
        if dxy is not None:
            have += 1; score += -sign if dxy > 0.1 else (sign if dxy < -0.1 else 0)
        if us10y is not None:
            have += 1; score += -sign if us10y > 0.1 else 0
    elif s == "USOIL" or "OIL" in s:
        if dxy is not None:
            have += 1; score += -sign * 2 if dxy > 0.2 else (sign * 2 if dxy < -0.2 else 0)
    if have == 0: return "NA"
    if score >= 2: return "strong_pro"
    if score == 1: return "weak_pro"
    if score == 0: return "neutral"
    if score == -1: return "weak_against"
    return "strong_against"


def enrich_snapshot(snapshot: dict, *, symbol: str, model_type: str,
                    ml_direction: str, ml_confidence: float | None,
                    ts: datetime | None = None) -> dict:
    """Produce the same column space as the pattern miner so rule conditions evaluate."""
    ts = ts or datetime.now(timezone.utc)
    enriched: dict = {}
    enriched["symbol"] = symbol
    enriched["model_type"] = model_type
    enriched["direction"] = ml_direction

    # Time
    enriched["dow"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][ts.weekday()]
    h = ts.hour
    enriched["hour_bucket"] = (
        "00-04" if h < 4 else "04-08" if h < 8 else "08-12" if h < 12
        else "12-16" if h < 16 else "16-20" if h < 20 else "20-24"
    )
    enriched["session_phase"] = _session_phase_label(symbol, ts)

    # ml_confidence bucket (column-level)
    enriched["ml_confidence_bucket"] = _ml_confidence_bucket(ml_confidence)

    # Categorical / boolean from snapshot
    cat_keys = [
        "regime_label", "mtf_trend", "volatility_regime", "session",
        "near_resistance", "near_support", "overbought", "oversold",
        "exhaustion_up", "exhaustion_down", "bb_extreme_upper", "bb_extreme_lower",
        "sar_bearish", "rsi_extreme",
        "H4_ema_stack", "H1_ema_stack", "M30_ema_stack",
        "H4_adx_label", "H1_adx_label", "M30_adx_label",
    ]
    for k in cat_keys:
        v = snapshot.get(k)
        # Booleans → string for consistent comparison ("True" / "False" / "NA")
        if isinstance(v, bool):
            enriched[k] = str(v)
        elif v is None:
            enriched[k] = "NA"
        else:
            enriched[k] = str(v)

    # Continuous → bucket
    for col, (factor_key, family) in FIELD_MAP.items():
        enriched[col] = _bucket_label(snapshot.get(factor_key), family)

    # Macro alignment per symbol
    enriched["macro_alignment"] = _macro_alignment(
        symbol, ml_direction,
        snapshot.get("macro_dxy_chg1d_pct"),
        snapshot.get("macro_vix_chg1d_pct"),
        snapshot.get("macro_us10y_chg1d_pct"),
    )
    return enriched


# ---------------------------------------------------------------------------
# Rule loading + parsing
# ---------------------------------------------------------------------------

def _load_rules(force: bool = False) -> list[dict]:
    """Load + cache pattern_rules.json. Auto-reloads on file mtime change."""
    global _rules_cache, _rules_loaded_at, _rules_mtime
    try:
        mtime = RULES_PATH.stat().st_mtime if RULES_PATH.exists() else 0
    except Exception:
        mtime = 0
    if _rules_cache is not None and not force and mtime == _rules_mtime:
        return _rules_cache
    if not RULES_PATH.exists():
        logger.warning(f"[pattern_matcher] rules file missing: {RULES_PATH}")
        _rules_cache = []
        return _rules_cache
    try:
        payload = json.loads(RULES_PATH.read_text())
        rules = payload.get("rules") or []
        _rules_cache = rules
        _rules_loaded_at = datetime.now(timezone.utc)
        _rules_mtime = mtime
        logger.info(f"[pattern_matcher] loaded {len(rules)} rules from {RULES_PATH}")
        return rules
    except Exception as e:
        logger.exception(f"[pattern_matcher] failed to load rules: {e}")
        _rules_cache = []
        return _rules_cache


# Parse "field op value" condition strings into (field, op, value)
# Supported ops: =, ≠, ≤, >
_COND_RE = re.compile(r"^\s*(\S+)\s*(=|≠|≤|>)\s*(.+)\s*$")


def _parse_condition(cond: str) -> Optional[tuple[str, str, str]]:
    m = _COND_RE.match(cond)
    if not m:
        return None
    field, op, value = m.group(1), m.group(2), m.group(3).strip()
    return field, op, value


def _evaluate_rule(rule: dict, enriched: dict) -> bool:
    """All conditions must hold for the rule to match."""
    for cond in rule.get("conditions", []):
        parsed = _parse_condition(cond)
        if parsed is None:
            return False
        field, op, expected = parsed
        actual = enriched.get(field)
        if actual is None:
            return False
        actual_str = str(actual)
        if op == "=":
            if actual_str != expected:
                return False
        elif op == "≠":
            if actual_str == expected:
                return False
        elif op == "≤":
            try:
                if float(actual) > float(expected):
                    return False
            except Exception:
                return False
        elif op == ">":
            try:
                if float(actual) <= float(expected):
                    return False
            except Exception:
                return False
    return True


# ---------------------------------------------------------------------------
# Public matcher
# ---------------------------------------------------------------------------

def _segment_matches(rule_segment: str, symbol: str, model_type: str, direction: str) -> bool:
    """A rule's segment label is one of:
        GLOBAL — tüm sembol & model
        XAUUSD · ml:main
        XAUUSD · ml:main · BUY
    """
    if rule_segment.startswith("GLOBAL"):
        return True
    parts = [p.strip() for p in rule_segment.split("·")]
    if len(parts) >= 1 and parts[0] != symbol:
        return False
    if len(parts) >= 2 and parts[1] != model_type:
        return False
    if len(parts) >= 3 and parts[2] != direction:
        return False
    return True


def match_patterns(*, symbol: str, model_type: str, ml_direction: str,
                    ml_confidence: float | None, snapshot: dict,
                    timestamp: datetime | None = None) -> dict:
    """Return all matching winning + toxic patterns for this live signal.

    Returns:
      {
        "winning_matches": [{segment, win_rate, samples, conditions, lift}, ...],
        "avoid_matches":   [...],
        "best_winning_win_rate": float | None,
        "worst_avoid_win_rate":  float | None,
        "alert_level": "trusted" | "caution" | "neutral" | "blocked"
      }
    """
    enriched = enrich_snapshot(
        snapshot, symbol=symbol, model_type=model_type,
        ml_direction=ml_direction, ml_confidence=ml_confidence, ts=timestamp,
    )
    rules = _load_rules()
    winning: list[dict] = []
    avoid: list[dict] = []
    for r in rules:
        seg = r.get("segment") or ""
        if not _segment_matches(seg, symbol, model_type, ml_direction):
            continue
        kind = r.get("kind")
        wr = float(r.get("win_rate", 0))
        samples = int(r.get("samples", 0))
        if samples < MIN_SAMPLE_SIZE:
            continue
        if kind == "winning_pattern" and wr < WINNING_MIN_WIN_RATE:
            continue
        if kind == "avoid_pattern" and wr > TOXIC_MAX_WIN_RATE:
            continue
        if not _evaluate_rule(r, enriched):
            continue
        entry = {
            "segment": seg,
            "win_rate": wr,
            "samples": samples,
            "conditions": r.get("conditions"),
            "kind": kind,
        }
        (winning if kind == "winning_pattern" else avoid).append(entry)

    # Sort: winning by win-rate desc, avoid by win-rate asc (worst first)
    winning.sort(key=lambda x: -x["win_rate"])
    avoid.sort(key=lambda x: x["win_rate"])

    best_win = winning[0]["win_rate"] if winning else None
    worst_avoid = avoid[0]["win_rate"] if avoid else None

    # Alert level summary
    if avoid and worst_avoid is not None and worst_avoid <= 25:
        alert_level = "blocked"     # extreme toxic
    elif avoid:
        alert_level = "caution"
    elif winning and best_win is not None and best_win >= 90:
        alert_level = "trusted"     # high-confidence winner
    elif winning:
        alert_level = "trusted"
    else:
        alert_level = "neutral"

    return {
        "winning_matches": winning[:5],
        "avoid_matches": avoid[:5],
        "best_winning_win_rate": best_win,
        "worst_avoid_win_rate": worst_avoid,
        "alert_level": alert_level,
        "total_winning": len(winning),
        "total_avoid": len(avoid),
    }


def reload_rules() -> int:
    """Force a reload — call after pattern_miner regenerates the file."""
    rules = _load_rules(force=True)
    return len(rules)


def get_rules_meta() -> dict:
    rules = _load_rules()
    return {
        "rules_count": len(rules),
        "loaded_at": _rules_loaded_at.isoformat() if _rules_loaded_at else None,
        "winning_min_win_rate": WINNING_MIN_WIN_RATE,
        "toxic_max_win_rate": TOXIC_MAX_WIN_RATE,
        "min_sample_size": MIN_SAMPLE_SIZE,
        "rules_path": str(RULES_PATH),
    }
