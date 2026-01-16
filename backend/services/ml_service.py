from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import settings


@dataclass
class SignalResult:
    signal: str
    confidence: float
    reasoning: List[str]
    metrics: dict
    timestamp: str
    model_status: str | None = None


def _path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


async def run_nasdaq_signal_async(current_price: float | None = None) -> SignalResult:
    """
    Run NASDAQ trend analysis using the new trend_analyzer.
    Returns SignalResult for backward compatibility.
    """
    from services.trend_analyzer import run_trend_analysis
    
    try:
        analysis = await run_trend_analysis("NDX.INDX", include_hourly=False)
        
        # Map trend to signal
        if analysis.trend == "BULLISH" and analysis.confidence > 60:
            signal = "BUY"
        elif analysis.trend == "BEARISH" and analysis.confidence > 60:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        # Build reasoning from analysis
        reasoning = []
        if analysis.ema20.has_data:
            reasoning.append(f"EMA(20): {analysis.ema20.value:.0f} (mesafe: {analysis.ema20.distance_pct:.2f}%)")
        if analysis.rsi_14:
            rsi_zone = "aşırı alım" if analysis.rsi_14 > 70 else "aşırı satım" if analysis.rsi_14 < 30 else "normal"
            reasoning.append(f"RSI: {analysis.rsi_14:.0f} ({rsi_zone})")
        reasoning.append(f"Trend: {analysis.trend} (güç: {analysis.trend_strength}%)")
        reasoning.append(f"Destek: {analysis.nearest_support.price:.0f} (güç: {analysis.nearest_support.strength:.1f})")
        if analysis.conflict and analysis.conflict.has_conflict:
            reasoning.append(f"⚠️ {analysis.conflict.description}")
        reasoning.append(f"Canlı fiyat: {analysis.current_price:.2f}")
        
        # Build metrics
        metrics = {
            "distance_to_ema": analysis.ema20.distance if analysis.ema20.has_data else 0,
            "distance_to_support": analysis.nearest_support.distance,
            "support_strength": analysis.nearest_support.strength,
            "rsi": analysis.rsi_14 or 50,
            "trend": analysis.trend,
            "current_price": analysis.current_price,
            "trend_strength": analysis.trend_strength,
            "volatility": analysis.volatility_level,
            "volume_confirmed": analysis.volume_confirmed,
        }
        
        return SignalResult(
            signal=signal,
            confidence=analysis.confidence / 100,  # API expects 0-1
            reasoning=reasoning,
            metrics=metrics,
            timestamp=analysis.timestamp,
            model_status=None,
        )
    except Exception as e:
        # Fallback on error
        return SignalResult(
            signal="HOLD",
            confidence=0.5,
            reasoning=[f"Analiz hatası: {str(e)}", "Varsayılan değerler kullanılıyor"],
            metrics={
                "distance_to_ema": 0,
                "distance_to_support": 0,
                "support_strength": 0.5,
                "rsi": 50,
                "trend": "NEUTRAL",
                "current_price": current_price,
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            model_status=f"Error: {str(e)}",
        )


async def run_xauusd_signal_async(current_price: float | None = None) -> SignalResult:
    """
    Run XAUUSD trend analysis using the new trend_analyzer.
    Returns SignalResult for backward compatibility.
    """
    from services.trend_analyzer import run_trend_analysis
    
    try:
        analysis = await run_trend_analysis("XAUUSD.FOREX", include_hourly=False)
        
        # Map trend to signal
        if analysis.trend == "BULLISH" and analysis.confidence > 60:
            signal = "BUY"
        elif analysis.trend == "BEARISH" and analysis.confidence > 60:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        # Build reasoning
        reasoning = []
        if analysis.ema20.has_data:
            reasoning.append(f"EMA(20): {analysis.ema20.value:.2f} (mesafe: {analysis.ema20.distance_pct:.2f}%)")
        if analysis.rsi_14:
            rsi_zone = "aşırı alım" if analysis.rsi_14 > 70 else "aşırı satım" if analysis.rsi_14 < 30 else "nötr"
            reasoning.append(f"RSI: {analysis.rsi_14:.0f} ({rsi_zone})")
        reasoning.append(f"Trend: {analysis.trend} (güç: {analysis.trend_strength}%)")
        reasoning.append(f"Destek: {analysis.nearest_support.price:.2f} (güç: {analysis.nearest_support.strength:.1f})")
        if analysis.conflict and analysis.conflict.has_conflict:
            reasoning.append(f"⚠️ {analysis.conflict.description}")
        reasoning.append(f"Canlı fiyat: {analysis.current_price:.2f}")
        
        metrics = {
            "distance_to_ema": analysis.ema20.distance if analysis.ema20.has_data else 0,
            "distance_to_support": analysis.nearest_support.distance,
            "support_strength": analysis.nearest_support.strength,
            "rsi": analysis.rsi_14 or 50,
            "trend": analysis.trend,
            "current_price": analysis.current_price,
            "trend_strength": analysis.trend_strength,
            "volatility": analysis.volatility_level,
            "volume_confirmed": analysis.volume_confirmed,
        }
        
        return SignalResult(
            signal=signal,
            confidence=analysis.confidence / 100,
            reasoning=reasoning,
            metrics=metrics,
            timestamp=analysis.timestamp,
            model_status=None,
        )
    except Exception as e:
        return SignalResult(
            signal="HOLD",
            confidence=0.5,
            reasoning=[f"Analiz hatası: {str(e)}", "Varsayılan değerler kullanılıyor"],
            metrics={
                "distance_to_ema": 0,
                "distance_to_support": 0,
                "support_strength": 0.5,
                "rsi": 50,
                "trend": "NEUTRAL",
                "current_price": current_price,
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            model_status=f"Error: {str(e)}",
        )


# Sync wrappers for backward compatibility (deprecated)
def run_nasdaq_signal(current_price: float | None = None) -> SignalResult:
    """
    DEPRECATED: Use run_nasdaq_signal_async instead.
    This sync version returns basic fallback data.
    """
    return SignalResult(
        signal="HOLD",
        confidence=0.5,
        reasoning=["Senkron çağrı - async versiyonu kullanın"],
        metrics={
            "distance_to_ema": 0,
            "distance_to_support": 0,
            "support_strength": 0.5,
            "rsi": 50,
            "trend": "NEUTRAL",
            "current_price": current_price,
        },
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_status="Use async version",
    )


def run_xauusd_signal(current_price: float | None = None) -> SignalResult:
    """
    DEPRECATED: Use run_xauusd_signal_async instead.
    """
    return SignalResult(
        signal="HOLD",
        confidence=0.5,
        reasoning=["Senkron çağrı - async versiyonu kullanın"],
        metrics={
            "distance_to_ema": 0,
            "distance_to_support": 0,
            "support_strength": 0.5,
            "rsi": 50,
            "trend": "NEUTRAL",
            "current_price": current_price,
        },
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_status="Use async version",
    )
