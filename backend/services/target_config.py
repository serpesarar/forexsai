"""
Target Configuration for Multi-Level Outcome Tracking
Symbol-specific pip targets and stoploss levels.

Target definitions (user-specified):
  NASDAQ / DAX:  TP1=15, TP2=25, TP3=35, TP4=50 pips, SL=50 pips
  XAUUSD:        TP1=7,  TP2=12, TP3=20, TP4=30 pips, SL=10 pips
  US OIL:        TP1=0.02%, TP2=0.04%, TP3=0.06%, TP4=0.1%, SL=0.05% (percentage-based)
"""
from typing import Dict, List, NamedTuple

class TargetLevel(NamedTuple):
    """Represents a target level in pips."""
    name: str
    pips: float

class SymbolConfig(NamedTuple):
    """Configuration for a trading symbol."""
    pip_value: float        # 1 pip in price units
    targets: List[TargetLevel]
    stoploss_pips: float
    is_percentage: bool     # If True, pips are actually percentage values

# ─── Symbol configs ───────────────────────────────────────────────────────────
# NASDAQ-100: 1 pip = 1 index point
# DAX:        1 pip = 1 index point
# XAUUSD:     1 pip = $0.10 (gold trades in $0.01 steps → 1 pip = 10 ticks)
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
    ),
    "XAUUSD": SymbolConfig(
        pip_value=0.01,  # 1 pip = $0.01 (1 cent) - DÜZELTİLDİ
        targets=[
            TargetLevel("TP1", 300),   # 300 pips = $3.00
            TargetLevel("TP2", 600),   # 600 pips = $6.00
            TargetLevel("TP3", 1000),  # 1000 pips = $10.00
            TargetLevel("TP4", 1500),  # 1500 pips = $15.00
        ],
        stoploss_pips=500,  # 500 pips = $5.00
        is_percentage=False,
    ),
    "CL.COMM": SymbolConfig(
        pip_value=1.0,  # placeholder, overridden by is_percentage
        targets=[
            TargetLevel("TP1", 0.02),   # 0.02%
            TargetLevel("TP2", 0.04),   # 0.04%
            TargetLevel("TP3", 0.06),   # 0.06%
            TargetLevel("TP4", 0.10),   # 0.10%
        ],
        stoploss_pips=0.05,  # 0.05%
        is_percentage=True,
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
    """Get configuration for a symbol."""
    return SYMBOL_CONFIGS.get(symbol, DEFAULT_CONFIG)


def calculate_target_prices(entry_price: float, direction: str, symbol: str) -> Dict[str, float]:
    """
    Calculate target prices based on entry price and direction.
    Supports both pip-based and percentage-based targets.
    """
    config = get_symbol_config(symbol)
    targets = {}

    for target in config.targets:
        if config.is_percentage:
            # Percentage-based: distance = entry_price * (pct / 100)
            distance = entry_price * (target.pips / 100.0)
        else:
            # Pip-based: distance = pips * pip_value
            distance = target.pips * config.pip_value

        if direction == "BUY":
            targets[target.name] = entry_price + distance
        elif direction == "SELL":
            targets[target.name] = entry_price - distance
        else:
            targets[target.name] = entry_price

    return targets


def calculate_stoploss_price(entry_price: float, direction: str, symbol: str) -> float:
    """
    Calculate stoploss price based on entry price and direction.
    Supports both pip-based and percentage-based stoploss.
    """
    config = get_symbol_config(symbol)

    if config.is_percentage:
        sl_distance = entry_price * (config.stoploss_pips / 100.0)
    else:
        sl_distance = config.stoploss_pips * config.pip_value

    if direction == "BUY":
        return entry_price - sl_distance
    elif direction == "SELL":
        return entry_price + sl_distance
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
