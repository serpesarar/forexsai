"""
Target Configuration for Multi-Level Outcome Tracking
Symbol-specific pip targets and stoploss levels.

Target definitions (canonical — see SYMBOL_CONFIGS below):
  NASDAQ / DAX:  TP1=30, TP2=30, TP3=30, TP4=30 pips, SL=50 pips
  XAUUSD:        TP1=8,  TP2=15, TP3=25, TP4=40 pips, SL=15 pips  (1 pip = $1.00)
  US OIL:        TP1=0.10%, TP2=0.20%, TP3=0.35%, TP4=0.50%, SL=0.30% (percentage-based)

  USOIL SELL has a walk-forward DirectionOverride (TP=[1.04,1.30,1.60,2.00]%,
  SL=1.49%) active by default via env TP_SL_DERIVED_OVERRIDES — applied through
  get_effective_config(symbol, direction), not get_symbol_config.
"""
from typing import Dict, List, NamedTuple, Optional

class TargetLevel(NamedTuple):
    """Represents a target level in pips."""
    name: str
    pips: float

class DirectionOverride(NamedTuple):
    """Optional direction-specific TP ladder and SL.

    When present, these REPLACE the symbol's base targets/stoploss_pips
    for the matching direction. Used to apply AI-Ops TP/SL recommendations
    that diverged by direction (e.g. XAUUSD BUY wants tight scalp while
    SELL wants a wider ride).
    """
    targets: List[TargetLevel]
    stoploss_pips: float
    source: str = ""  # provenance — e.g. "ai-ops:tp_sl/<id>"

class SymbolConfig(NamedTuple):
    """Configuration for a trading symbol."""
    pip_value: float        # 1 pip in price units
    targets: List[TargetLevel]
    stoploss_pips: float
    is_percentage: bool     # If True, pips are actually percentage values
    direction_overrides: Optional[Dict[str, DirectionOverride]] = None
    # Realistic SL floor — spread + typical intra-bar noise + slippage.
    # The MFE/MAE optimizer samples every 3-15 min so an SL below this floor
    # is statistically optimal on the recorded data but unfilled in real
    # execution. AI-Ops recommendations get clamped to ≥ this value.
    noise_floor_pips: float = 0.0
    # Realistic TP floor — same idea: TP below typical spread is meaningless.
    min_tp_pips: float = 0.0

# ─── Symbol configs ───────────────────────────────────────────────────────────
# NASDAQ-100: 1 pip = 1 index point
# DAX:        1 pip = 1 index point
# XAUUSD:     1 pip = $1.00 (4711 → 4710 = 1 pip)
# US OIL:     percentage-based targets (pip_value=1.0, pips = % of entry)

SYMBOL_CONFIGS: Dict[str, SymbolConfig] = {
    "NDX.INDX": SymbolConfig(
        pip_value=1.0,
        targets=[
            TargetLevel("TP1", 30),   # 30 pips
            TargetLevel("TP2", 30),   # 30 pips
            TargetLevel("TP3", 30),   # 30 pips
            TargetLevel("TP4", 30),   # 30 pips
        ],
        stoploss_pips=50,
        is_percentage=False,
        # NDX spread typically 0.5-1 pt, intra-3min range often 5-10 pts.
        noise_floor_pips=8.0,
        min_tp_pips=5.0,
    ),
    "GDAXI.INDX": SymbolConfig(
        pip_value=1.0,
        targets=[
            TargetLevel("TP1", 30),
            TargetLevel("TP2", 30),
            TargetLevel("TP3", 30),
            TargetLevel("TP4", 30),
        ],
        stoploss_pips=50,
        is_percentage=False,
        # DAX spread typically 1-2 pt, intra-3min range often 6-12 pts.
        noise_floor_pips=8.0,
        min_tp_pips=5.0,
    ),
    "XAUUSD": SymbolConfig(
        pip_value=1.0,  # 1 pip = $1.00 (4711→4710 = 1 pip)
        # REVERT 2026-05-15: All direction_overrides removed. Live trading
        # on the May-14 AI-Ops recommendation (TP1=6/SL=5 → then TP1=6/SL=5
        # for both directions) produced systematic losses on MT5. Diagnosis:
        # SL=5 is below realistic execution friction once spread (0.5) +
        # slippage (1-2) + intra-tick wick (2-4) are stacked. SL was firing
        # before any signal could develop. Reverted to the pre-AI-Ops base
        # ladder which had been profitable historically.
        targets=[
            TargetLevel("TP1", 8),
            TargetLevel("TP2", 15),
            TargetLevel("TP3", 25),
            TargetLevel("TP4", 40),
        ],
        stoploss_pips=15,
        is_percentage=False,
        noise_floor_pips=5.0,
        min_tp_pips=3.0,
        # direction_overrides intentionally omitted — base ladder applies to
        # both BUY and SELL until we have a re-validated per-direction config.
    ),
    "USOIL.FOREX": SymbolConfig(
        pip_value=1.0,  # placeholder, overridden by is_percentage
        # 2026-05-27: Eski config (TP1=0.02%) broker spread'inin (%0.03)
        # ALTINDAYDI → her ufak intra-bar dalgalanma TP1 sayılıyordu,
        # şişirilmiş WR / gerçekte zarar. A/B backtest (280 sinyal):
        #   Eski: WR=68.2% net=+%1.93 / Yeni: WR=80.7% net=+%24.6
        # +%1175 iyileşme. Spread × 3 minimum TP1.
        targets=[
            TargetLevel("TP1", 0.10),   # 0.10% — spread (0.03%) × 3
            TargetLevel("TP2", 0.20),   # 0.20%
            TargetLevel("TP3", 0.35),   # 0.35%
            TargetLevel("TP4", 0.50),   # 0.50%
        ],
        stoploss_pips=0.30,  # 0.30% — geniş SL intra-bar noise'a takılmaz
        is_percentage=True,
        # USOIL spread 0.02-0.04%, intra-3min noise ~0.05%.
        noise_floor_pips=0.10,   # spread × 3 — TP1 ile aynı
        min_tp_pips=0.10,
    ),
}

# Default config for unknown symbols
DEFAULT_CONFIG = SymbolConfig(
    pip_value=1.0,
    targets=[
        TargetLevel("TP1", 15),
        TargetLevel("TP2", 25),
        TargetLevel("TP3", 35),
        TargetLevel("TP4", 50),
    ],
    stoploss_pips=50,
    is_percentage=False,
)

# ─── Walk-forward derived TP/SL — SIDE SYSTEM ────────────────────────────────
# Distribution-derived configs that survived the multi-fold rolling
# walk-forward (2026-05-21): only NDX.INDX BUY (5/5 folds), GDAXI.INDX SELL
# (3/4) and USOIL.FOREX SELL (5/5) were robust out-of-sample. TP1 is the
# walk-forward-validated win threshold; TP2-4 ladder up from it.
#
# KILL SWITCH: env TP_SL_DERIVED_OVERRIDES (1=on, 0=off).
# 2026-05-24'ten itibaren VARSAYILAN AÇIK — walk-forward 3 robust scope'u
# (NDX BUY 5/5, USOIL SELL 5/5, GDAXI SELL 3/4) doğruladı, mevcut config
# R:R 0.34-0.57 ile zarar veriyordu. Devre dışı bırakmak için
# TP_SL_DERIVED_OVERRIDES=0 ile redeploy.
import os as _os

_DERIVED_OVERRIDES = {
    # "NDX.INDX": ("BUY", DirectionOverride(
    #     targets=[TargetLevel("TP1", 80), TargetLevel("TP2", 100),
    #              TargetLevel("TP3", 125), TargetLevel("TP4", 155)],
    #     stoploss_pips=110, source="walkforward:NDX-BUY/5of5-folds")),
    # "GDAXI.INDX": ("SELL", DirectionOverride(
    #     targets=[TargetLevel("TP1", 67), TargetLevel("TP2", 85),
    #              TargetLevel("TP3", 105), TargetLevel("TP4", 130)],
    #     stoploss_pips=119, source="walkforward:GDAXI-SELL/3of4-folds")),
    "USOIL.FOREX": ("SELL", DirectionOverride(
        targets=[TargetLevel("TP1", 1.04), TargetLevel("TP2", 1.30),
                 TargetLevel("TP3", 1.60), TargetLevel("TP4", 2.00)],
        stoploss_pips=1.49, source="walkforward:USOIL-SELL/5of5-folds")),
}

DERIVED_OVERRIDES_ACTIVE = _os.getenv("TP_SL_DERIVED_OVERRIDES", "1") == "1"

if DERIVED_OVERRIDES_ACTIVE:
    for _sym, (_dir, _ov) in _DERIVED_OVERRIDES.items():
        if _sym in SYMBOL_CONFIGS:
            SYMBOL_CONFIGS[_sym] = SYMBOL_CONFIGS[_sym]._replace(
                direction_overrides={_dir: _ov})


def get_symbol_config(symbol: str) -> SymbolConfig:
    """Get base configuration for a symbol (no direction override)."""
    return SYMBOL_CONFIGS.get(symbol, DEFAULT_CONFIG)


def get_effective_config(symbol: str, direction: Optional[str] = None) -> SymbolConfig:
    """Resolve the effective TP/SL config, applying any direction override.

    When `direction` is "BUY" or "SELL" and the symbol has a matching
    `direction_overrides` entry, return a SymbolConfig with that direction's
    targets and stoploss_pips substituted. Otherwise return the base.
    """
    base = SYMBOL_CONFIGS.get(symbol, DEFAULT_CONFIG)
    if direction and base.direction_overrides:
        override = base.direction_overrides.get(direction)
        if override is not None:
            return SymbolConfig(
                pip_value=base.pip_value,
                targets=override.targets,
                stoploss_pips=override.stoploss_pips,
                is_percentage=base.is_percentage,
                direction_overrides=base.direction_overrides,
            )
    return base


def get_timeframe_addition_pct(timeframe: str) -> float:
    """
    Returns the percentage addition for wider timeframes.
    User rule: +0.2% per timeframe step after 15m.
    """
    steps = {
        "1m": 0.0,
        "5m": 0.0,
        "15m": 0.0,
        "30m": 0.2,
        "1h": 0.4,
        "4h": 0.6,
        "1d": 0.8,
    }
    return steps.get(timeframe.lower(), 0.0)


def calculate_target_prices(entry_price: float, direction: str, symbol: str, timeframe: str = "15m") -> Dict[str, float]:
    """
    Calculate target prices based on entry price and direction.
    Supports both pip-based and percentage-based targets.
    Adds timeframe-based expansion (+0.2% per step) to maintain Risk/Reward ratios.
    Uses direction-specific TP ladder when configured (e.g. XAUUSD).
    """
    config = get_effective_config(symbol, direction)
    targets = {}
    
    # Calculate timeframe expansion distance based on entry price
    tf_addition_pct = get_timeframe_addition_pct(timeframe)
    tf_addition_distance = entry_price * (tf_addition_pct / 100.0)

    for target in config.targets:
        if config.is_percentage:
            # Percentage-based: distance = entry_price * (pct / 100)
            base_distance = entry_price * (target.pips / 100.0)
        else:
            # Pip-based: distance = pips * pip_value
            base_distance = target.pips * config.pip_value

        total_distance = base_distance

        if direction == "BUY":
            targets[target.name] = entry_price + total_distance
        elif direction == "SELL":
            targets[target.name] = entry_price - total_distance
        else:
            targets[target.name] = entry_price

    return targets


def calculate_stoploss_price(entry_price: float, direction: str, symbol: str, timeframe: str = "15m") -> float:
    """
    Calculate stoploss price based on entry price and direction.
    Supports both pip-based and percentage-based stoploss.
    Expands SL distance by +0.2% of entry price for each timeframe step.
    Uses direction-specific SL when configured (e.g. XAUUSD).
    """
    config = get_effective_config(symbol, direction)

    # 1. Base SL calculation
    if config.is_percentage:
        base_sl_distance = entry_price * (config.stoploss_pips / 100.0)
    else:
        base_sl_distance = config.stoploss_pips * config.pip_value

    # 2. Timeframe expansion (+0.2% per step)
    tf_addition_pct = get_timeframe_addition_pct(timeframe)
    tf_addition_distance = entry_price * (tf_addition_pct / 100.0)
    
    # 3. Total Distance
    total_sl_distance = base_sl_distance

    if direction == "BUY":
        return entry_price - total_sl_distance
    elif direction == "SELL":
        return entry_price + total_sl_distance
    return entry_price


def pips_from_price_change(price_change: float, symbol: str) -> float:
    """
    Convert price change to pips for a symbol.
    For percentage-based symbols, returns the raw price change (pips = price).
    """
    config = get_symbol_config(symbol)
    if config.is_percentage:
        # For percentage symbols, just return the raw change
        # The caller should interpret this as price units, not pips
        return price_change
    return price_change / config.pip_value
