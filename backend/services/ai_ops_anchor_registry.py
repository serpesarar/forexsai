"""
AI-Ops Anchor Registry — model_type → code-insertion mapping.

For Layer 2 (auto-implementer) to generate filter code, it must know:
  1. Which file owns the signal-decision logic for a model
  2. Where in that file to insert a new filter (the "anchor")
  3. The variable name for the signal direction at that point
  4. How to compose the new filter with existing ones (decision_notes idiom)

This file is a pure config — no behavior, just data. Auto-implementer reads
it to know "for PULSE1 → edit routers/emel_pulse.py, insert AFTER the line
matching ANCHOR, set pulse_signal='HOLD', append to decision_notes".

When new models or refactors change file paths, update only this file.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelAnchor:
    """Code-insertion point for one model's signal-decision flow."""
    model_type: str
    file_path: str                  # relative to backend/ root
    anchor_line_pattern: str         # regex/contains match for insertion point
    insert_after: bool = True        # True = after match, False = before
    signal_variable: str = "signal"  # the var holding 'BUY'/'SELL'/'HOLD'
    decision_notes_variable: str = "decision_notes"   # list to append note
    direction_hold_value: str = '"HOLD"'
    signal_type_variable: Optional[str] = "signal_type"   # downgrade to HOLD too
    description: str = ""


# ---------------------------------------------------------------------------
# Registry — one entry per model_type
# ---------------------------------------------------------------------------

REGISTRY: list[ModelAnchor] = [
    # PULSE1 — already wired (see commit 8048b08). Anchor: AFTER regime filter.
    ModelAnchor(
        model_type="pulse1",
        file_path="routers/emel_pulse.py",
        anchor_line_pattern=(
            'pulse_signal, was_filtered, filter_reason = filter_signal_by_regime'
            '(pulse_signal, regime)'
        ),
        signal_variable="pulse_signal",
        decision_notes_variable="decision_notes",
        signal_type_variable="signal_type",
        description=(
            "PULSE1 (algo-based scalp). Insert filter after the existing "
            "regime filter (line ~1687) and before volume note. Composes "
            "cleanly with the regime + volume filter pipeline."
        ),
    ),

    # PULSE2 — ML+TA hybrid. Same router file, different code path.
    ModelAnchor(
        model_type="pulse2",
        file_path="routers/emel_pulse.py",
        anchor_line_pattern=(
            'signal, was_filtered, filter_reason = filter_signal_by_regime'
            '(signal, regime)'
        ),
        signal_variable="signal",
        decision_notes_variable="notes",
        signal_type_variable="signal_type",
        description=(
            "PULSE2 (ML+TA hybrid). Same emel_pulse.py file as PULSE1 but "
            "uses variable `signal` (not pulse_signal) and notes list is "
            "`notes` not `decision_notes`. Anchor: line ~2135."
        ),
    ),

    # PULSE3 — MTF (5m+1h+4h). 3-layer hybrid.
    ModelAnchor(
        model_type="pulse3",
        file_path="routers/emel_pulse.py",
        anchor_line_pattern=(
            'direction, was_filtered, filter_reason = filter_signal_by_regime'
            '(direction, regime)'
        ),
        signal_variable="direction",
        decision_notes_variable="notes",
        signal_type_variable="signal_type",
        direction_hold_value='"NEUTRAL"',   # PULSE3 uses NEUTRAL not HOLD for direction
        description=(
            "PULSE3 (MTF 5m+1h+4h). Same file, third decision flow. Uses "
            "variable `direction` and `NEUTRAL` as no-signal value. Anchor: "
            "line ~2644."
        ),
    ),

    # EMEL — 9-Check strategic.
    ModelAnchor(
        model_type="emel",
        file_path="routers/emel_pulse.py",
        anchor_line_pattern='if decision in ["BUY", "SELL"]:',
        insert_after=False,             # insert BEFORE the log_prediction block
        signal_variable="decision",
        decision_notes_variable="reasons",   # EMEL uses 'reasons'
        signal_type_variable=None,
        direction_hold_value='"HOLD"',
        description=(
            "EMEL (9-Check strategic). Decision variable is `decision`. "
            "Filter must run BEFORE the `if decision in ['BUY','SELL']:` log "
            "guard so a downgrade to HOLD prevents persistence. Anchor: "
            "line ~1228."
        ),
    ),

    # SMC — ICT/OrderBlock. Different log path (log_smc_prediction).
    ModelAnchor(
        model_type="smc",
        file_path="services/order_block_service.py",
        anchor_line_pattern="# AI_OPS_FILTER_ANCHOR_SMC",   # not present yet
        signal_variable="signal_direction",
        decision_notes_variable="reasons",
        signal_type_variable=None,
        description=(
            "SMC (ICT order-block). Filter point not yet marked in source. "
            "Auto-implementer will fall back to: add `# AI_OPS_FILTER_ANCHOR_SMC` "
            "comment in order_block_service before signal emission, then insert. "
            "For now, SMC fixes need manual file-anchor selection by Claude Code."
        ),
    ),

    # META engine — combines all 6 model signals.
    ModelAnchor(
        model_type="meta",
        file_path="services/meta_analysis_engine.py",
        anchor_line_pattern="# === Determine majority direction ===",
        signal_variable="direction",
        decision_notes_variable="passed_conditions",
        signal_type_variable=None,
        direction_hold_value='"HOLD"',
        description=(
            "Meta engine combines all 6 model outputs. Filter belongs AFTER "
            "majority direction is determined but BEFORE confidence fusion "
            "so a hard-block prevents the trade entirely. Anchor: ~line 787."
        ),
    ),

    # ML (LightGBM) — XAU v3 has its own service.
    ModelAnchor(
        model_type="ml",
        file_path="services/ml_prediction_service.py",
        anchor_line_pattern="# AI_OPS_FILTER_ANCHOR_ML",
        signal_variable="direction",
        decision_notes_variable="reasoning",
        signal_type_variable=None,
        description=(
            "ML LightGBM predictions. Anchor comment not yet placed — auto-"
            "implementer will need a manual file edit OR Claude Code can add "
            "the comment marker, then auto-implement next time. The ml: scope "
            "variants (ml:main, ml:nasdaq_precision, etc.) all funnel through "
            "the same prediction service."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_anchor(model_type: str) -> Optional[ModelAnchor]:
    """Lookup the anchor for a given model_type. Handles scoped variants like
    'ml:nasdaq_precision' by stripping the suffix."""
    base = model_type.split(":", 1)[0].lower()
    for a in REGISTRY:
        if a.model_type == base:
            return a
    return None


def is_auto_implementable(model_type: str) -> bool:
    """True if Layer 2 can fully auto-generate code for this model.
    False if the model needs a manual anchor edit first (smc, ml).
    The "AI_OPS_FILTER_ANCHOR_*" marker convention indicates a placeholder
    comment we plan to add manually before auto-impl can target the model."""
    a = get_anchor(model_type)
    if a is None:
        return False
    return "AI_OPS_FILTER_ANCHOR" not in a.anchor_line_pattern


def list_supported_models() -> list[str]:
    """All model_types we have ANY anchor for."""
    return [a.model_type for a in REGISTRY]


def list_auto_implementable() -> list[str]:
    """Subset of REGISTRY that Layer 2 can handle without manual prep."""
    return [a.model_type for a in REGISTRY if is_auto_implementable(a.model_type)]
