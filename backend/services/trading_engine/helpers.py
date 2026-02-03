"""
Trading Engine Helper Functions
"""
import numpy as np
from typing import List, Dict, Tuple
from .constants import PriceStructure


def ema(values: np.ndarray, period: int) -> float:
    """EMA hesapla"""
    if len(values) < period:
        return float(values[-1]) if len(values) else 0.0
    alpha = 2.0 / (period + 1.0)
    result = float(values[0])
    for v in values[1:]:
        result = alpha * float(v) + (1 - alpha) * result
    return float(result)


def ema_series(values: np.ndarray, period: int) -> np.ndarray:
    """EMA serisi hesapla"""
    if len(values) < period:
        return values.copy()
    alpha = 2.0 / (period + 1.0)
    result = np.zeros_like(values, dtype=float)
    result[0] = values[0]
    for i in range(1, len(values)):
        result[i] = alpha * values[i] + (1 - alpha) * result[i-1]
    return result


def atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """ATR hesapla"""
    if len(closes) < period + 1:
        return float(np.mean(highs - lows)) if len(highs) else 0.0
    
    tr_list = []
    for i in range(1, len(closes)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        tr_list.append(max(high_low, high_close, low_close))
    
    return float(np.mean(tr_list[-period:])) if len(tr_list) >= period else float(np.mean(tr_list))


def adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Tuple[float, float, float]:
    """ADX, +DI, -DI hesapla"""
    if len(closes) < period + 1:
        return 25.0, 50.0, 50.0
    
    tr_list, plus_dm_list, minus_dm_list = [], [], []
    
    for i in range(1, len(closes)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        tr_list.append(max(high_low, high_close, low_close))
        
        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        plus_dm_list.append(up_move if (up_move > down_move and up_move > 0) else 0)
        minus_dm_list.append(down_move if (down_move > up_move and down_move > 0) else 0)
    
    if len(tr_list) < period:
        return 25.0, 50.0, 50.0
    
    tr_smooth = float(np.mean(tr_list[-period:]))
    plus_di = (np.mean(plus_dm_list[-period:]) / tr_smooth * 100) if tr_smooth > 0 else 50
    minus_di = (np.mean(minus_dm_list[-period:]) / tr_smooth * 100) if tr_smooth > 0 else 50
    
    di_sum = plus_di + minus_di
    dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
    
    return float(dx), float(plus_di), float(minus_di)


def rsi(values: np.ndarray, period: int = 14) -> float:
    """RSI hesapla"""
    if len(values) < period + 1:
        return 50.0
    diffs = np.diff(values)
    gains = np.where(diffs > 0, diffs, 0.0)
    losses = np.where(diffs < 0, -diffs, 0.0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:]) + 1e-9
    rs = avg_gain / avg_loss
    return float(np.clip(100.0 - (100.0 / (1.0 + rs)), 0.0, 100.0))


def find_swing_points(highs: np.ndarray, lows: np.ndarray, strength: int = 3) -> Tuple[List[Dict], List[Dict]]:
    """Swing high/low noktalarını bul"""
    swing_highs, swing_lows = [], []
    
    for i in range(strength, len(highs) - strength):
        if highs[i] == max(highs[i-strength:i+strength+1]):
            swing_highs.append({"index": i, "price": float(highs[i])})
        if lows[i] == min(lows[i-strength:i+strength+1]):
            swing_lows.append({"index": i, "price": float(lows[i])})
    
    return swing_highs, swing_lows


def analyze_price_structure(swing_highs: List[Dict], swing_lows: List[Dict]) -> PriceStructure:
    """Fiyat yapısını analiz et"""
    if len(swing_highs) < 3 or len(swing_lows) < 3:
        return PriceStructure.CHAOTIC
    
    recent_highs = [s["price"] for s in swing_highs[-4:]]
    recent_lows = [s["price"] for s in swing_lows[-4:]]
    
    hh = all(recent_highs[i] < recent_highs[i+1] for i in range(len(recent_highs)-1))
    hl = all(recent_lows[i] < recent_lows[i+1] for i in range(len(recent_lows)-1))
    lh = all(recent_highs[i] > recent_highs[i+1] for i in range(len(recent_highs)-1))
    ll = all(recent_lows[i] > recent_lows[i+1] for i in range(len(recent_lows)-1))
    
    if hh and hl:
        return PriceStructure.HIGHER_HIGHS
    elif lh and ll:
        return PriceStructure.LOWER_LOWS
    elif hh and ll:
        return PriceStructure.EXPANDING_RANGE
    elif lh and hl:
        return PriceStructure.CONTRACTING_RANGE
    return PriceStructure.CHAOTIC


def extract_ohlcv(candles: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Candle listesinden OHLCV arrayları çıkar"""
    opens = np.array([c.get("open", c.get("o", 0)) for c in candles], dtype=float)
    highs = np.array([c.get("high", c.get("h", 0)) for c in candles], dtype=float)
    lows = np.array([c.get("low", c.get("l", 0)) for c in candles], dtype=float)
    closes = np.array([c.get("close", c.get("c", 0)) for c in candles], dtype=float)
    volumes = np.array([c.get("volume", c.get("v", 0)) for c in candles], dtype=float)
    return opens, highs, lows, closes, volumes
