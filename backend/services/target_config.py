"""
Target Configuration for Multi-Level Outcome Tracking
Symbol-specific pip targets and stoploss levels.

Target definitions (user-specified):
  NASDAQ / DAX:  TP1=15, TP2=25, TP3=35, TP4=50 pips, SL=50 pips
  XAUUSD:        TP1=4,  TP2=7,  TP3=10, TP4=17 pips, SL=8 pips  (1 pip = $1.00)
  US OIL:        TP1=0.02%, TP2=0.04%, TP3=0.06%, TP4=0.1%, SL=0.05% (percentage-based)
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
            TargetLevel("TP1", 15),   # 15 pips
            TargetLevel("TP2", 25),   # 25 pips
            TargetLevel("TP3", 35),   # 35 pips
            TargetLevel("TP4", 50),   # 50 pips
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
            TargetLevel("TP1", 15),
            TargetLevel("TP2", 25),
            TargetLevel("TP3", 35),
            TargetLevel("TP4", 50),
        ],
        stoploss_pips=50,
        is_percentage=False,
        # DAX spread typically 1-2 pt, intra-3min range often 6-12 pts.
        noise_floor_pips=8.0,
        min_tp_pips=5.0,
    ),
    "XAUUSD": SymbolConfig(
        pip_value=1.0,  # 1 pip = $1.00 (4711→4710 = 1 pip)
        # Base ladder kept as a sane fallback for callers that don't pass
        # direction (e.g. backfill paths in signal_lifecycle_router).
        targets=[
            TargetLevel("TP1", 8),
            TargetLevel("TP2", 15),
            TargetLevel("TP3", 25),
            TargetLevel("TP4", 40),
        ],
        stoploss_pips=15,
        is_percentage=False,
        # XAUUSD spread typically 0.2-0.5 ($), intra-3min wick often 3-6 pips.
        # Real-world execution friction makes SL < 5 pips effectively a
        # "spread-trigger" — backtest-optimal but unfilled live.
        noise_floor_pips=5.0,
        min_tp_pips=3.0,
        # AI-Ops tp_sl optimizer recommendations applied 2026-05-14
        # User confirmed via dashboard. Per-direction split because the
        # MFE/MAE asymmetry on XAUUSD diverges sharply:
        #   - BUY: tight scalp — most profit captured around TP1 area,
        #          drawdown beyond a few pips rarely recovers
        #   - SELL: wider ride — profitable signals run to ~25 pips
        # Sources: tp_sl_recommendations
        #   BUY  c1b883a0-4722-4656-a1df-01e3b27742ab (n=941, WR 35%, net +915p)
        #   SELL 92662f50-0ff1-4350-8e94-8dd2c3693027 (n=674, WR 29%, net +2294p)
        # NOTE: optimizer's raw SL recommendations were 2.5 (BUY) and 1.53
        # (SELL) — below the 5-pip noise_floor for XAUUSD. Those values are
        # backtest-optimal on the recorded MAE distribution, but in real
        # execution the spread + intra-bar wick would trigger those SLs
        # before the trade had a chance to develop. We clamp to the noise
        # floor here (5 pips) so the live config is executable.
        direction_overrides={
            "BUY": DirectionOverride(
                targets=[
                    TargetLevel("TP1", 9),
                    TargetLevel("TP2", 14),
                    TargetLevel("TP3", 22),
                    TargetLevel("TP4", 35),
                ],
                stoploss_pips=5.0,   # was 2.5; clamped to noise floor
                source="ai-ops:tp_sl/c1b883a0 (SL clamped to noise_floor=5)",
            ),
            "SELL": DirectionOverride(
                targets=[
                    TargetLevel("TP1", 25),
                    TargetLevel("TP2", 35),
                    TargetLevel("TP3", 45),
                    TargetLevel("TP4", 60),
                ],
                stoploss_pips=5.0,   # was 1.53; clamped to noise floor
                source="ai-ops:tp_sl/92662f50 (SL clamped to noise_floor=5)",
            ),
        },
    ),
    "USOIL.FOREX": SymbolConfig(
        pip_value=1.0,  # placeholder, overridden by is_percentage
        targets=[
            TargetLevel("TP1", 0.02),   # 0.02%
            TargetLevel("TP2", 0.04),   # 0.04%
            TargetLevel("TP3", 0.06),   # 0.06%
            TargetLevel("TP4", 0.10),   # 0.10%
        ],
        stoploss_pips=0.05,  # 0.05%
        is_percentage=True,
        # USOIL spread typically 0.02-0.04%, intra-3min noise ~0.05%.
        noise_floor_pips=0.04,
        min_tp_pips=0.02,
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
