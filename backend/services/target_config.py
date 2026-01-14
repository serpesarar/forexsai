"""
Target Configuration for Multi-Level Outcome Tracking
Symbol-specific pip targets and stoploss levels.
"""
from typing import Dict, List, NamedTuple

class TargetLevel(NamedTuple):
    """Represents a target level in pips."""
    name: str
    pips: float

class SymbolConfig(NamedTuple):
    """Configuration for a trading symbol."""
    pip_value: float  # 1 pip in price units
    targets: List[TargetLevel]
    stoploss_pips: float

# NASDAQ-100: 1 pip = 1 point (index points)
# XAUUSD: 1 pip = 0.1 USD (gold trades in 0.01 increments, so 1 pip = $0.10)

SYMBOL_CONFIGS: Dict[str, SymbolConfig] = {
    "NDX.INDX": SymbolConfig(
        pip_value=1.0,  # 1 index point = 1 pip
        targets=[
            TargetLevel("TP1", 20),   # 20 pips
            TargetLevel("TP2", 30),   # 30 pips
            TargetLevel("TP3", 50),   # 50 pips
        ],
        stoploss_pips=50,  # 50 pips below entry
    ),
    "XAUUSD": SymbolConfig(
        pip_value=0.1,  # $0.10 = 1 pip for gold
        targets=[
            TargetLevel("TP1", 5),    # 5 pips = $0.50
            TargetLevel("TP2", 10),   # 10 pips = $1.00
            TargetLevel("TP3", 20),   # 20 pips = $2.00
        ],
        stoploss_pips=10,  # 10 pips below entry
    ),
}

# Default config for unknown symbols
DEFAULT_CONFIG = SymbolConfig(
    pip_value=1.0,
    targets=[
        TargetLevel("TP1", 10),
        TargetLevel("TP2", 20),
        TargetLevel("TP3", 30),
    ],
    stoploss_pips=20,
)


def get_symbol_config(symbol: str) -> SymbolConfig:
    """Get configuration for a symbol."""
    return SYMBOL_CONFIGS.get(symbol, DEFAULT_CONFIG)


def calculate_target_prices(entry_price: float, direction: str, symbol: str) -> Dict[str, float]:
    """
    Calculate target prices based on entry price and direction.
    
    Args:
        entry_price: Entry price
        direction: BUY or SELL
        symbol: Trading symbol
    
    Returns:
        Dict with target names and prices
    """
    config = get_symbol_config(symbol)
    targets = {}
    
    for target in config.targets:
        pip_distance = target.pips * config.pip_value
        if direction == "BUY":
            targets[target.name] = entry_price + pip_distance
        elif direction == "SELL":
            targets[target.name] = entry_price - pip_distance
        else:
            targets[target.name] = entry_price
    
    return targets


def calculate_stoploss_price(entry_price: float, direction: str, symbol: str) -> float:
    """
    Calculate stoploss price based on entry price and direction.
    
    Args:
        entry_price: Entry price
        direction: BUY or SELL
        symbol: Trading symbol
    
    Returns:
        Stoploss price
    """
    config = get_symbol_config(symbol)
    sl_distance = config.stoploss_pips * config.pip_value
    
    if direction == "BUY":
        return entry_price - sl_distance
    elif direction == "SELL":
        return entry_price + sl_distance
    return entry_price


def pips_from_price_change(price_change: float, symbol: str) -> float:
    """
    Convert price change to pips for a symbol.
    
    Args:
        price_change: Absolute price change
        symbol: Trading symbol
    
    Returns:
        Number of pips
    """
    config = get_symbol_config(symbol)
    return price_change / config.pip_value
