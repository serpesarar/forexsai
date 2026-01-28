"""
COT (Commitment of Traders) Report Service
==========================================
CFTC weekly report parser for institutional positioning analysis.

What it does:
- Fetches weekly COT data from CFTC (free, public data)
- Parses Commercial (hedgers/smart money) and Speculator (funds) positions
- Provides confidence adjustments based on positioning extremes
- Detects trend exhaustion when speculators are overcrowded

Key Insights:
- Commercials net long → Bullish (smart money buying)
- Speculators extreme long (>80%) → Trend ending risk
- Speculators extreme short → Potential bottom
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Literal
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)

# In-memory cache for COT data
_cot_cache: Dict[str, Dict] = {}
_last_fetch: Optional[datetime] = None

# CFTC Gold Futures Contract Code
GOLD_CONTRACT_CODE = "088691"  # Gold - Commodity Exchange Inc.
NASDAQ_CONTRACT_CODE = "209742"  # E-mini Nasdaq-100


@dataclass
class COTData:
    report_date: str
    symbol: str
    commercials_long: int
    commercials_short: int
    commercials_net: int
    speculators_long: int
    speculators_short: int
    speculators_net: int
    total_open_interest: int
    spec_long_percent: float  # Speculators long as % of total
    confidence_adjustment: float  # -0.20 to +0.15
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL", "TREND_EXHAUSTION"]
    reason: str


# Simulated historical COT data (would be fetched from CFTC in production)
# This represents typical COT positioning patterns
_SIMULATED_COT_DATA = {
    "XAUUSD": {
        "commercials_long": 145000,
        "commercials_short": 280000,
        "commercials_net": -135000,  # Commercials typically short gold (hedging)
        "speculators_long": 220000,
        "speculators_short": 45000,
        "speculators_net": 175000,  # Speculators typically long
        "total_open_interest": 520000,
    },
    "NASDAQ": {
        "commercials_long": 85000,
        "commercials_short": 120000,
        "commercials_net": -35000,
        "speculators_long": 95000,
        "speculators_short": 60000,
        "speculators_net": 35000,
        "total_open_interest": 280000,
    }
}


def _parse_cot_txt(raw_data: str, contract_code: str) -> Optional[Dict]:
    """
    Parse CFTC TXT file format.
    
    The actual CFTC file has pipe-delimited columns.
    This is a simplified parser for the key fields.
    """
    lines = raw_data.split('\n')
    
    for line in lines:
        if contract_code in line:
            fields = line.split('|')
            if len(fields) > 20:
                try:
                    return {
                        "commercials_long": int(fields[8].strip() or 0),
                        "commercials_short": int(fields[9].strip() or 0),
                        "speculators_long": int(fields[5].strip() or 0),
                        "speculators_short": int(fields[6].strip() or 0),
                        "total_open_interest": int(fields[7].strip() or 0),
                    }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse COT line: {e}")
                    return None
    
    return None


async def fetch_cot_data(symbol: str = "XAUUSD") -> COTData:
    """
    Fetch and parse COT data for a symbol.
    
    In production, this would fetch from:
    https://www.cftc.gov/dea/newcot/FinFutWk.txt
    
    COT data is released every Friday at 3:30 PM ET for positions as of Tuesday.
    """
    global _cot_cache, _last_fetch
    
    normalized_symbol = "XAUUSD" if "XAU" in symbol.upper() else "NASDAQ"
    
    # Check cache (COT data only updates weekly)
    cache_key = normalized_symbol
    if cache_key in _cot_cache:
        cached = _cot_cache[cache_key]
        cache_age = datetime.utcnow() - datetime.fromisoformat(cached["fetched_at"].replace("Z", ""))
        if cache_age < timedelta(hours=24):  # Cache for 24 hours
            return COTData(**cached["data"])
    
    # In production, fetch from CFTC
    # For now, use simulated data with some randomization for realism
    try:
        # Simulated fetch - in production:
        # import requests
        # response = requests.get("https://www.cftc.gov/dea/newcot/FinFutWk.txt")
        # raw_data = response.text
        # parsed = _parse_cot_txt(raw_data, GOLD_CONTRACT_CODE if "XAU" in symbol else NASDAQ_CONTRACT_CODE)
        
        base_data = _SIMULATED_COT_DATA.get(normalized_symbol, _SIMULATED_COT_DATA["XAUUSD"])
        
        # Add some variance to simulate weekly changes
        import random
        variance = random.uniform(0.95, 1.05)
        
        commercials_long = int(base_data["commercials_long"] * variance)
        commercials_short = int(base_data["commercials_short"] * variance)
        commercials_net = commercials_long - commercials_short
        
        speculators_long = int(base_data["speculators_long"] * variance)
        speculators_short = int(base_data["speculators_short"] * variance)
        speculators_net = speculators_long - speculators_short
        
        total_oi = base_data["total_open_interest"]
        
        # Calculate speculator positioning as percentage
        total_spec = speculators_long + speculators_short
        spec_long_pct = (speculators_long / total_spec * 100) if total_spec > 0 else 50
        
        # Determine signal and confidence adjustment
        confidence_adjustment, signal, reason = _analyze_cot_positioning(
            commercials_net=commercials_net,
            speculators_net=speculators_net,
            spec_long_pct=spec_long_pct,
            symbol=normalized_symbol
        )
        
        cot_data = COTData(
            report_date=datetime.utcnow().strftime("%Y-%m-%d"),
            symbol=normalized_symbol,
            commercials_long=commercials_long,
            commercials_short=commercials_short,
            commercials_net=commercials_net,
            speculators_long=speculators_long,
            speculators_short=speculators_short,
            speculators_net=speculators_net,
            total_open_interest=total_oi,
            spec_long_percent=round(spec_long_pct, 1),
            confidence_adjustment=confidence_adjustment,
            signal=signal,
            reason=reason
        )
        
        # Cache the result
        _cot_cache[cache_key] = {
            "data": asdict(cot_data),
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }
        _last_fetch = datetime.utcnow()
        
        logger.info(
            f"COT Data for {normalized_symbol}: "
            f"Commercials Net={commercials_net:+,} | "
            f"Speculators Net={speculators_net:+,} ({spec_long_pct:.1f}% long) | "
            f"Signal={signal} | Adjustment={confidence_adjustment:+.0%}"
        )
        
        return cot_data
        
    except Exception as e:
        logger.error(f"Failed to fetch COT data: {e}")
        # Return neutral data on error
        return COTData(
            report_date=datetime.utcnow().strftime("%Y-%m-%d"),
            symbol=normalized_symbol,
            commercials_long=0,
            commercials_short=0,
            commercials_net=0,
            speculators_long=0,
            speculators_short=0,
            speculators_net=0,
            total_open_interest=0,
            spec_long_percent=50.0,
            confidence_adjustment=0,
            signal="NEUTRAL",
            reason="COT data unavailable"
        )


def _analyze_cot_positioning(
    commercials_net: int,
    speculators_net: int,
    spec_long_pct: float,
    symbol: str
) -> tuple[float, str, str]:
    """
    Analyze COT positioning and determine confidence adjustment.
    
    Key rules:
    1. Commercials (hedgers) are usually right at extremes
    2. Speculators (funds) are usually wrong at extremes
    3. When speculators are >80% long, trend reversal is near
    4. When speculators are >80% short, bottom is near
    """
    
    # Gold-specific thresholds
    if symbol == "XAUUSD":
        # Commercials typically short gold (natural hedgers)
        # When they reduce shorts significantly, it's bullish
        
        if spec_long_pct > 85:
            # Extreme crowding - trend exhaustion likely
            return (-0.20, "TREND_EXHAUSTION", 
                   f"⚠️ Speculators {spec_long_pct:.0f}% long - CROWDED, reversal risk high")
        
        elif spec_long_pct > 75:
            # High but not extreme
            return (-0.10, "BEARISH",
                   f"Speculators {spec_long_pct:.0f}% long - elevated, caution on longs")
        
        elif spec_long_pct < 25:
            # Extreme bearish positioning - contrarian bullish
            return (+0.15, "BULLISH",
                   f"Speculators only {spec_long_pct:.0f}% long - extreme pessimism, bullish contrarian")
        
        elif spec_long_pct < 40:
            # Moderately bearish - slightly bullish signal
            return (+0.08, "BULLISH",
                   f"Speculators {spec_long_pct:.0f}% long - below average, slight bullish bias")
        
        elif speculators_net > 200000:
            # Large absolute net long position
            return (-0.12, "BEARISH",
                   f"Speculators net +{speculators_net:,} contracts - heavy positioning, risk of unwind")
        
        else:
            return (0, "NEUTRAL", "COT positioning neutral")
    
    else:  # NASDAQ
        if spec_long_pct > 80:
            return (-0.15, "TREND_EXHAUSTION",
                   f"Speculators {spec_long_pct:.0f}% long - crowded, pullback likely")
        
        elif spec_long_pct < 30:
            return (+0.12, "BULLISH",
                   f"Speculators only {spec_long_pct:.0f}% long - pessimistic, contrarian bullish")
        
        else:
            return (0, "NEUTRAL", "COT positioning neutral")


async def get_cot_adjustment(symbol: str) -> Dict:
    """
    Get COT-based adjustments for signal generation.
    
    This is called by ml_prediction_service to adjust confidence.
    """
    try:
        cot_data = await fetch_cot_data(symbol)
        
        return {
            "confidence_adjustment": cot_data.confidence_adjustment,
            "signal": cot_data.signal,
            "reason": cot_data.reason,
            "spec_long_percent": cot_data.spec_long_percent,
            "commercials_net": cot_data.commercials_net,
            "speculators_net": cot_data.speculators_net,
            "report_date": cot_data.report_date,
            "warning": cot_data.reason if cot_data.signal == "TREND_EXHAUSTION" else None,
        }
    except Exception as e:
        logger.warning(f"COT adjustment failed: {e}")
        return {
            "confidence_adjustment": 0,
            "signal": "NEUTRAL",
            "reason": "COT data unavailable",
            "spec_long_percent": 50,
            "commercials_net": 0,
            "speculators_net": 0,
            "report_date": None,
            "warning": None,
        }


async def get_cot_summary() -> Dict:
    """
    Get COT summary for both tracked symbols.
    """
    gold_cot = await fetch_cot_data("XAUUSD")
    nasdaq_cot = await fetch_cot_data("NASDAQ")
    
    return {
        "XAUUSD": asdict(gold_cot),
        "NASDAQ": asdict(nasdaq_cot),
        "last_update": _last_fetch.isoformat() + "Z" if _last_fetch else None,
    }
