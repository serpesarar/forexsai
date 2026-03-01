"""
COT (Commitment of Traders) Report Service
==========================================
Real CFTC weekly report parser for institutional positioning analysis.

Data source: CFTC public data (FREE, no API key needed)
- Futures-only report: https://www.cftc.gov/dea/newcot/deafut.txt
- Financial Futures: https://www.cftc.gov/dea/newcot/FinFutWk.txt

COT released every Friday ~3:30 PM ET for positions as of prior Tuesday.

Key Insights:
- Commercials net long → Bullish (smart money buying / hedging less)
- Speculators extreme long (>80%) → Trend ending risk (crowded trade)
- Speculators extreme short → Potential bottom (contrarian bullish)
- Week-over-week changes reveal positioning momentum
"""

import logging
import io
import csv
from datetime import datetime, timedelta
from typing import Dict, Optional, Literal, List
from dataclasses import dataclass, asdict, field
from collections import deque

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# CFTC Contract Codes (Market_and_Exchange_Names field contains these)
# ═══════════════════════════════════════════════════════════════════
COT_CONTRACTS = {
    "XAUUSD": {
        "code": "088691",
        "search": "GOLD - COMMODITY EXCHANGE",
        "name": "Gold Futures",
        "exchange": "COMEX",
    },
    "SILVER": {
        "code": "084691",
        "search": "SILVER - COMMODITY EXCHANGE",
        "name": "Silver Futures",
        "exchange": "COMEX",
    },
    "NASDAQ": {
        "code": "209742",
        "search": "NASDAQ-100",
        "name": "E-mini NASDAQ-100",
        "exchange": "CME",
    },
    "SP500": {
        "code": "13874+",
        "search": "E-MINI S&P 500",
        "name": "E-mini S&P 500",
        "exchange": "CME",
    },
    "DAX": {
        "code": "244002",
        "search": "DAX",
        "name": "DAX Futures",
        "exchange": "CME",
    },
    "USOIL": {
        "code": "067651",
        "search": "CRUDE OIL",
        "name": "WTI Crude Oil Futures",
        "exchange": "NYMEX",
    },
}

# CFTC URLs
CFTC_FUTURES_ONLY_URL = "https://www.cftc.gov/dea/newcot/deafut.txt"
CFTC_FIN_FUTURES_URL = "https://www.cftc.gov/dea/newcot/FinFutWk.txt"

# ═══════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════

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
    spec_long_percent: float
    confidence_adjustment: float
    signal: Literal["BULLISH", "BEARISH", "NEUTRAL", "TREND_EXHAUSTION"]
    reason: str
    # Week-over-week changes
    commercials_net_change: int = 0
    speculators_net_change: int = 0
    oi_change: int = 0
    oi_change_pct: float = 0.0
    # Historical percentile (0-100)
    spec_positioning_percentile: float = 50.0
    data_source: str = "live"  # "live" or "fallback"


@dataclass
class COTHistoryEntry:
    """Single week's COT snapshot for historical tracking."""
    report_date: str
    commercials_net: int
    speculators_net: int
    total_open_interest: int
    spec_long_percent: float


# ═══════════════════════════════════════════════════════════════════
# In-memory Cache & History
# ═══════════════════════════════════════════════════════════════════

# Current week cache: symbol → {data: COTData, fetched_at: str}
_cot_cache: Dict[str, Dict] = {}
_last_fetch: Optional[datetime] = None

# Historical data for percentile calculations (last 52 weeks)
_cot_history: Dict[str, deque] = {
    sym: deque(maxlen=52) for sym in COT_CONTRACTS
}

# Raw CFTC file cache (shared across symbols, fetched once)
_raw_file_cache: Dict[str, Dict] = {}  # url → {data: str, fetched_at: datetime}
RAW_CACHE_TTL = timedelta(hours=6)


# ═══════════════════════════════════════════════════════════════════
# CFTC File Fetching & Parsing
# ═══════════════════════════════════════════════════════════════════

async def _fetch_cftc_file(url: str) -> Optional[str]:
    """Fetch raw CFTC text file with caching."""
    global _raw_file_cache

    cached = _raw_file_cache.get(url)
    if cached:
        age = datetime.utcnow() - cached["fetched_at"]
        if age < RAW_CACHE_TTL:
            return cached["data"]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            raw = resp.text
            _raw_file_cache[url] = {"data": raw, "fetched_at": datetime.utcnow()}
            logger.info(f"Fetched CFTC file from {url} ({len(raw)} bytes)")
            return raw
    except Exception as e:
        logger.error(f"Failed to fetch CFTC file {url}: {e}")
        return None


def _parse_cftc_futures_only(raw_data: str, contract_info: Dict) -> Optional[Dict]:
    """
    Parse the CFTC Disaggregated Futures-Only report (deafut.txt).
    
    This is a fixed-width/comma-separated file. The key columns are:
    - Non-Commercial Long/Short (Speculators / Managed Money)
    - Commercial Long/Short (Hedgers / Producers)
    - Open Interest
    - Report Date
    """
    search_term = contract_info["search"]
    contract_code = contract_info["code"]
    
    lines = raw_data.strip().split('\n')
    
    for line in lines:
        # Match by contract code or search term
        if contract_code in line or search_term.upper() in line.upper():
            fields = [f.strip() for f in line.split(',')]
            if len(fields) < 15:
                fields = [f.strip() for f in line.split('|')]
            
            if len(fields) >= 15:
                try:
                    # Standard CFTC futures-only format column indices:
                    # The exact indices depend on the format variant
                    # Try to find numeric fields for positions
                    report_date_str = None
                    numeric_fields = []
                    
                    for f in fields:
                        f_clean = f.replace('"', '').strip()
                        # Look for date pattern
                        if not report_date_str and len(f_clean) >= 8:
                            try:
                                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
                                    try:
                                        dt = datetime.strptime(f_clean, fmt)
                                        report_date_str = dt.strftime("%Y-%m-%d")
                                        break
                                    except ValueError:
                                        continue
                            except Exception:
                                pass
                        # Collect numeric values
                        try:
                            numeric_fields.append(int(f_clean.replace(',', '')))
                        except (ValueError, AttributeError):
                            pass
                    
                    if len(numeric_fields) >= 6:
                        # Typical order in futures-only:
                        # OI, NonComm_Long, NonComm_Short, Comm_Long, Comm_Short, ...
                        # But varies by format. Use heuristic: largest value = OI
                        sorted_vals = sorted(enumerate(numeric_fields), key=lambda x: x[1], reverse=True)
                        oi_idx = sorted_vals[0][0]
                        total_oi = sorted_vals[0][1]
                        
                        # The remaining large values are position sizes
                        position_vals = [v for i, v in enumerate(numeric_fields) if i != oi_idx and v > 0]
                        
                        if len(position_vals) >= 4:
                            return {
                                "report_date": report_date_str or datetime.utcnow().strftime("%Y-%m-%d"),
                                "speculators_long": position_vals[0],
                                "speculators_short": position_vals[1],
                                "commercials_long": position_vals[2],
                                "commercials_short": position_vals[3],
                                "total_open_interest": total_oi,
                            }
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse CFTC line for {search_term}: {e}")
                    continue
    
    return None


def _parse_cftc_csv_format(raw_data: str, contract_info: Dict) -> Optional[Dict]:
    """
    Parse CFTC data using CSV reader - handles both comma and pipe delimiters.
    Tries to identify the header row and map columns by name.
    """
    search_term = contract_info["search"]
    
    lines = raw_data.strip().split('\n')
    if not lines:
        return None
    
    # Try to find header line
    header_line = None
    data_lines = []
    for i, line in enumerate(lines):
        lower = line.lower()
        if "open_interest" in lower or "open interest" in lower or "noncommercial" in lower:
            header_line = i
            break
    
    if header_line is not None:
        # CSV with headers
        delimiter = ',' if ',' in lines[header_line] else '|'
        headers = [h.strip().strip('"').lower() for h in lines[header_line].split(delimiter)]
        
        for line in lines[header_line + 1:]:
            if search_term.upper() in line.upper():
                fields = [f.strip().strip('"') for f in line.split(delimiter)]
                if len(fields) == len(headers):
                    row = dict(zip(headers, fields))
                    return _extract_from_named_row(row)
    
    return None


def _extract_from_named_row(row: Dict[str, str]) -> Optional[Dict]:
    """Extract COT data from a row with named columns."""
    def safe_int(key_patterns: List[str], default: int = 0) -> int:
        for pattern in key_patterns:
            for k, v in row.items():
                if pattern in k:
                    try:
                        return int(v.replace(',', '').strip())
                    except (ValueError, AttributeError):
                        continue
        return default
    
    try:
        report_date = None
        for k, v in row.items():
            if "date" in k.lower() and v.strip():
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
                    try:
                        report_date = datetime.strptime(v.strip(), fmt).strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                if report_date:
                    break
        
        return {
            "report_date": report_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "speculators_long": safe_int(["noncommercial_long", "non-commercial_long", "non_commercial_long", "noncomm_long"]),
            "speculators_short": safe_int(["noncommercial_short", "non-commercial_short", "non_commercial_short", "noncomm_short"]),
            "commercials_long": safe_int(["commercial_long", "comm_long"]),
            "commercials_short": safe_int(["commercial_short", "comm_short"]),
            "total_open_interest": safe_int(["open_interest", "open interest", "oi_all"]),
        }
    except Exception as e:
        logger.warning(f"Failed to extract from named row: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# Fallback Data (realistic ranges from real CFTC reports)
# Used only when CFTC fetch fails
# ═══════════════════════════════════════════════════════════════════

_FALLBACK_COT_DATA = {
    "XAUUSD": {
        "commercials_long": 145000,
        "commercials_short": 280000,
        "speculators_long": 220000,
        "speculators_short": 45000,
        "total_open_interest": 520000,
    },
    "SILVER": {
        "commercials_long": 52000,
        "commercials_short": 95000,
        "speculators_long": 55000,
        "speculators_short": 18000,
        "total_open_interest": 155000,
    },
    "NASDAQ": {
        "commercials_long": 85000,
        "commercials_short": 120000,
        "speculators_long": 95000,
        "speculators_short": 60000,
        "total_open_interest": 280000,
    },
    "SP500": {
        "commercials_long": 350000,
        "commercials_short": 480000,
        "speculators_long": 280000,
        "speculators_short": 150000,
        "total_open_interest": 2800000,
    },
}


# ═══════════════════════════════════════════════════════════════════
# Core Fetch & Analysis
# ═══════════════════════════════════════════════════════════════════

def _normalize_symbol(symbol: str) -> str:
    """Normalize input symbol to our internal keys."""
    s = symbol.upper().replace(".", "").replace("/", "")
    if "XAU" in s or "GOLD" in s:
        return "XAUUSD"
    if "XAG" in s or "SILVER" in s:
        return "SILVER"
    if "NDX" in s or "NASDAQ" in s or "NQ" in s:
        return "NASDAQ"
    if "SPX" in s or "SP500" in s or "ES" in s:
        return "SP500"
    return "XAUUSD"


async def fetch_cot_data(symbol: str = "XAUUSD") -> COTData:
    """
    Fetch and parse real COT data for a symbol.
    
    1. Tries to fetch live CFTC data from deafut.txt
    2. Falls back to FinFutWk.txt
    3. Final fallback to realistic hardcoded ranges
    """
    global _cot_cache, _last_fetch

    normalized = _normalize_symbol(symbol)
    contract = COT_CONTRACTS.get(normalized)
    if not contract:
        contract = COT_CONTRACTS["XAUUSD"]
        normalized = "XAUUSD"

    # Check cache (6 hours - COT only updates weekly on Fridays)
    cache_key = normalized
    if cache_key in _cot_cache:
        cached = _cot_cache[cache_key]
        try:
            cache_age = datetime.utcnow() - datetime.fromisoformat(cached["fetched_at"].replace("Z", ""))
            if cache_age < timedelta(hours=6):
                return COTData(**cached["data"])
        except Exception:
            pass

    # Try live CFTC fetch
    parsed = None
    data_source = "live"

    # Try Futures-Only report first (has commodities: gold, silver)
    if normalized in ("XAUUSD", "SILVER"):
        raw = await _fetch_cftc_file(CFTC_FUTURES_ONLY_URL)
        if raw:
            parsed = _parse_cftc_futures_only(raw, contract)
            if not parsed:
                parsed = _parse_cftc_csv_format(raw, contract)

    # Try Financial Futures report (has NASDAQ, SP500)
    if not parsed and normalized in ("NASDAQ", "SP500"):
        raw = await _fetch_cftc_file(CFTC_FIN_FUTURES_URL)
        if raw:
            parsed = _parse_cftc_futures_only(raw, contract)
            if not parsed:
                parsed = _parse_cftc_csv_format(raw, contract)

    # If both failed, try the other URL as fallback
    if not parsed:
        other_url = CFTC_FIN_FUTURES_URL if normalized in ("XAUUSD", "SILVER") else CFTC_FUTURES_ONLY_URL
        raw = await _fetch_cftc_file(other_url)
        if raw:
            parsed = _parse_cftc_futures_only(raw, contract)
            if not parsed:
                parsed = _parse_cftc_csv_format(raw, contract)

    # Final fallback: use realistic static data
    if not parsed:
        logger.warning(f"Using fallback COT data for {normalized}")
        data_source = "fallback"
        base = _FALLBACK_COT_DATA.get(normalized, _FALLBACK_COT_DATA["XAUUSD"])
        parsed = {
            "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "speculators_long": base["speculators_long"],
            "speculators_short": base["speculators_short"],
            "commercials_long": base["commercials_long"],
            "commercials_short": base["commercials_short"],
            "total_open_interest": base["total_open_interest"],
        }

    return _build_cot_data(normalized, parsed, data_source)


def _build_cot_data(symbol: str, parsed: Dict, data_source: str) -> COTData:
    """Build COTData from parsed CFTC row, compute analysis, track history."""
    global _cot_cache, _last_fetch

    comm_long = parsed.get("commercials_long", 0)
    comm_short = parsed.get("commercials_short", 0)
    comm_net = comm_long - comm_short

    spec_long = parsed.get("speculators_long", 0)
    spec_short = parsed.get("speculators_short", 0)
    spec_net = spec_long - spec_short

    total_oi = parsed.get("total_open_interest", 0)
    report_date = parsed.get("report_date", datetime.utcnow().strftime("%Y-%m-%d"))

    total_spec = spec_long + spec_short
    spec_long_pct = (spec_long / total_spec * 100) if total_spec > 0 else 50.0

    # Week-over-week changes from history
    history = _cot_history.get(symbol, deque(maxlen=52))
    comm_net_change = 0
    spec_net_change = 0
    oi_change = 0
    oi_change_pct = 0.0
    if history:
        prev = history[-1]
        comm_net_change = comm_net - prev.commercials_net
        spec_net_change = spec_net - prev.speculators_net
        oi_change = total_oi - prev.total_open_interest
        oi_change_pct = (oi_change / prev.total_open_interest * 100) if prev.total_open_interest else 0.0

    # Percentile: where current spec_long_pct sits in last 52 weeks
    spec_percentile = 50.0
    if len(history) >= 4:
        sorted_hist = sorted(h.spec_long_percent for h in history)
        rank = sum(1 for v in sorted_hist if v <= spec_long_pct)
        spec_percentile = round(rank / len(sorted_hist) * 100, 1)

    # Analyze positioning
    confidence_adj, signal, reason = _analyze_cot_positioning(
        commercials_net=comm_net,
        speculators_net=spec_net,
        spec_long_pct=spec_long_pct,
        symbol=symbol,
        oi_change_pct=oi_change_pct,
        spec_percentile=spec_percentile,
    )

    cot = COTData(
        report_date=report_date,
        symbol=symbol,
        commercials_long=comm_long,
        commercials_short=comm_short,
        commercials_net=comm_net,
        speculators_long=spec_long,
        speculators_short=spec_short,
        speculators_net=spec_net,
        total_open_interest=total_oi,
        spec_long_percent=round(spec_long_pct, 1),
        confidence_adjustment=confidence_adj,
        signal=signal,
        reason=reason,
        commercials_net_change=comm_net_change,
        speculators_net_change=spec_net_change,
        oi_change=oi_change,
        oi_change_pct=round(oi_change_pct, 2),
        spec_positioning_percentile=spec_percentile,
        data_source=data_source,
    )

    # Update history (avoid duplicate dates)
    if not history or history[-1].report_date != report_date:
        history.append(COTHistoryEntry(
            report_date=report_date,
            commercials_net=comm_net,
            speculators_net=spec_net,
            total_open_interest=total_oi,
            spec_long_percent=round(spec_long_pct, 1),
        ))
    _cot_history[symbol] = history

    # Cache
    _cot_cache[symbol] = {
        "data": asdict(cot),
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    _last_fetch = datetime.utcnow()

    logger.info(
        f"COT {symbol} ({data_source}): Comm={comm_net:+,} Δ{comm_net_change:+,} | "
        f"Spec={spec_net:+,} Δ{spec_net_change:+,} ({spec_long_pct:.0f}% long, P{spec_percentile:.0f}) | "
        f"OI={total_oi:,} Δ{oi_change_pct:+.1f}% | Signal={signal}"
    )

    return cot


def _analyze_cot_positioning(
    commercials_net: int,
    speculators_net: int,
    spec_long_pct: float,
    symbol: str,
    oi_change_pct: float = 0.0,
    spec_percentile: float = 50.0,
) -> tuple:
    """
    Analyze COT positioning and determine confidence adjustment.
    
    Key rules:
    1. Commercials (hedgers) are usually right at extremes
    2. Speculators (funds) are usually wrong at extremes  
    3. When speculators are >80% long, trend reversal is near
    4. When speculators are >80% short, bottom is near
    5. Large OI changes + positioning = new whale activity
    """
    
    # Commodity-specific thresholds (Gold, Silver)
    if symbol in ("XAUUSD", "SILVER"):
        if spec_long_pct > 85 or spec_percentile > 95:
            return (-0.20, "TREND_EXHAUSTION",
                    f"Speculators {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - CROWDED, reversal risk high")
        
        elif spec_long_pct > 75 or spec_percentile > 80:
            return (-0.10, "BEARISH",
                    f"Speculators {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - elevated, caution on longs")
        
        elif spec_long_pct < 25 or spec_percentile < 5:
            return (+0.15, "BULLISH",
                    f"Speculators only {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - extreme pessimism, contrarian bullish")
        
        elif spec_long_pct < 40 or spec_percentile < 20:
            return (+0.08, "BULLISH",
                    f"Speculators {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - below average, slight bullish bias")
        
        elif speculators_net > 200000:
            return (-0.12, "BEARISH",
                    f"Speculators net +{speculators_net:,} - heavy positioning, unwind risk")
        
        elif abs(oi_change_pct) > 10:
            direction = "bullish" if oi_change_pct > 0 and commercials_net > 0 else "bearish"
            return (0.05 if direction == "bullish" else -0.05, 
                    "BULLISH" if direction == "bullish" else "BEARISH",
                    f"OI surged {oi_change_pct:+.1f}% - new large positions detected ({direction})")
        
        else:
            return (0, "NEUTRAL", "COT positioning neutral")
    
    else:  # NASDAQ, SP500
        if spec_long_pct > 80 or spec_percentile > 90:
            return (-0.15, "TREND_EXHAUSTION",
                    f"Speculators {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - crowded, pullback likely")
        
        elif spec_long_pct < 30 or spec_percentile < 10:
            return (+0.12, "BULLISH",
                    f"Speculators only {spec_long_pct:.0f}% long (P{spec_percentile:.0f}) - pessimistic, contrarian bullish")
        
        elif abs(oi_change_pct) > 10:
            direction = "bullish" if oi_change_pct > 0 and commercials_net > 0 else "bearish"
            return (0.05 if direction == "bullish" else -0.05,
                    "BULLISH" if direction == "bullish" else "BEARISH",
                    f"OI surged {oi_change_pct:+.1f}% - new large positions detected ({direction})")
        
        else:
            return (0, "NEUTRAL", "COT positioning neutral")


# ═══════════════════════════════════════════════════════════════════
# Public API (backward compatible)
# ═══════════════════════════════════════════════════════════════════

async def get_cot_adjustment(symbol: str) -> Dict:
    """
    Get COT-based adjustments for signal generation.
    Called by ml_prediction_service to adjust confidence.
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
            "oi_change_pct": cot_data.oi_change_pct,
            "spec_percentile": cot_data.spec_positioning_percentile,
            "data_source": cot_data.data_source,
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
            "oi_change_pct": 0,
            "spec_percentile": 50,
            "data_source": "error",
        }


async def get_cot_summary() -> Dict:
    """Get COT summary for all tracked symbols - XAUUSD, NASDAQ, DAX, USOIL."""
    results = {}
    # Main 4 symbols for the dashboard
    for sym in ("XAUUSD", "NASDAQ", "DAX", "USOIL"):
        try:
            cot = await fetch_cot_data(sym)
            results[sym] = asdict(cot)
        except Exception as e:
            logger.warning(f"COT summary failed for {sym}: {e}")

    return {
        **results,
        "last_update": _last_fetch.isoformat() + "Z" if _last_fetch else None,
        "symbols": list(results.keys()),
    }


def get_cot_history(symbol: str) -> List[Dict]:
    """Get historical COT entries for a symbol (up to 52 weeks)."""
    normalized = _normalize_symbol(symbol)
    history = _cot_history.get(normalized, [])
    return [asdict(h) for h in history]
