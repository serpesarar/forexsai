"""
MT5 History Report Matcher & Sync Engine
────────────────────────────────────────
Parses MT5 HTML or CSV transaction history reports, matches executions
with Supabase prediction logs via symbol, direction, and time tolerance,
and updates prediction logs with ground truth execution statistics.
"""
from __future__ import annotations

import logging
import csv
import io
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

from utils.json_helpers import parse_json_field
from database.supabase_client import get_supabase_client, is_db_available
from utils.safe_supabase import safe_get_data

logger = logging.getLogger(__name__)

# Try importing BeautifulSoup soft dependency for premium HTML parsing
BS4_AVAILABLE = False
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    logger.info("BeautifulSoup4 not installed. Using fallback regex HTML parser.")


class MT5ReportMatcher:
    """Parses MT5 transaction history and syncs with Supabase prediction logs."""

    def __init__(self):
        self.client = get_supabase_client() if is_db_available() else None

    def parse_csv_report(self, content: str) -> List[Dict[str, Any]]:
        """Parses MT5 history in CSV format."""
        trades = []
        try:
            f = io.StringIO(content.strip())
            reader = csv.reader(f)
            
            # Read header
            header = next(reader, None)
            if not header:
                return trades

            # Find column indices dynamically
            col_map = {col.lower().strip(): idx for idx, col in enumerate(header)}
            
            # Sütun adı eşleşmeleri
            time_idx = col_map.get("time") or col_map.get("open time") or col_map.get("date")
            symbol_idx = col_map.get("symbol") or col_map.get("item")
            type_idx = col_map.get("type") or col_map.get("action")
            price_idx = col_map.get("price") or col_map.get("open price") or col_map.get("entry price")
            close_price_idx = col_map.get("close price") or col_map.get("exit price")
            profit_idx = col_map.get("profit") or col_map.get("pnl")

            if time_idx is None or symbol_idx is None or type_idx is None:
                logger.warning("Invalid MT5 CSV format: Missing critical columns.")
                return trades

            for row in reader:
                if not row or len(row) <= max(time_idx, symbol_idx, type_idx):
                    continue

                direction = row[type_idx].upper().strip()
                if "BUY" not in direction and "SELL" not in direction:
                    continue

                trades.append({
                    "time_str": row[time_idx].strip(),
                    "symbol": row[symbol_idx].strip(),
                    "direction": "BUY" if "BUY" in direction else "SELL",
                    "entry_price": float(row[price_idx]) if price_idx is not None and row[price_idx] else 0.0,
                    "exit_price": float(row[close_price_idx]) if close_price_idx is not None and row[close_price_idx] else 0.0,
                    "profit": float(row[profit_idx]) if profit_idx is not None and row[profit_idx] else 0.0,
                })
        except Exception as e:
            logger.error(f"Error parsing MT5 CSV report: {e}", exc_info=True)
            
        return self._deduplicate_trades(trades)

    def parse_html_report(self, content: str) -> List[Dict[str, Any]]:
        """Parses MT5 history in standard HTML Report format dynamically mapping columns."""
        trades = []
        tables = []
        
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(content, "lxml")
                # Group by table elements
                for table in soup.find_all("table"):
                    table_rows = []
                    for tr in table.find_all("tr"):
                        cols = [cell.get_text().strip() for cell in tr.find_all(["td", "th"])]
                        if cols:
                            table_rows.append(cols)
                    if table_rows:
                        tables.append(table_rows)
            except Exception as e:
                logger.error(f"BeautifulSoup parsing failed: {e}. Trying fallback regex table parser.")
                
        if not tables:
            # Fallback regex table blocks parser
            try:
                table_matches = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL | re.IGNORECASE)
                for table_content in table_matches:
                    table_rows = []
                    tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
                    for tr in tr_matches:
                        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
                        cols = [re.sub(r'<[^>]*>', '', cell).strip() for cell in cells]
                        if cols:
                            table_rows.append(cols)
                    if table_rows:
                        tables.append(table_rows)
            except Exception as e:
                logger.error(f"Regex fallback table parser failed: {e}")

        # If no tables found at all, fall back to parsing the entire document as a single list of rows
        raw_rows = []
        if not tables:
            logger.info("No tables grouped. Falling back to parsing all rows in the document.")
            if BS4_AVAILABLE:
                try:
                    soup = BeautifulSoup(content, "lxml")
                    for tr in soup.find_all("tr"):
                        cols = [cell.get_text().strip() for cell in tr.find_all(["td", "th"])]
                        if cols:
                            raw_rows.append(cols)
                except Exception:
                    pass
            if not raw_rows:
                try:
                    tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
                    for tr in tr_matches:
                        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
                        cols = [re.sub(r'<[^>]*>', '', cell).strip() for cell in cells]
                        if cols:
                            raw_rows.append(cols)
                except Exception:
                    pass
            if raw_rows:
                tables.append(raw_rows)

        if not tables:
            return trades

        # Multilingual header mapping keywords (supports Turkish and English reports)
        SYMBOL_KEYWORDS = {"symbol", "sembol", "item", "yatırım"}
        TYPE_KEYWORDS = {"type", "action", "direction", "tür", "tip", "yön", "işlem"}
        PROFIT_KEYWORDS = {"profit", "pnl", "kâr", "kar", "kazanç"}
        POSITION_KEYWORDS = {"position", "pozisyon"}
        DEAL_KEYWORDS = {"deal", "anlaşma"}
        ORDER_KEYWORDS = {"order", "emir", "state", "durum"}
        VOLUME_KEYWORDS = {"volume", "lot", "hacim", "miktar"}
        PRICE_KEYWORDS = {"price", "fiyat"}
        TIME_KEYWORDS = {"time", "zaman", "tarih", "saat"}

        # Dynamic Table Selector
        selected_table_info = None
        positions_table = None
        trades_table = None
        deals_table = None
        fallback_table = None
        
        for table_rows in tables:
            is_trade_table = False
            table_type = "unknown"
            header_idx = -1
            
            # Scan first 20 rows of each table for header row containing key columns
            for idx, row in enumerate(table_rows[:20]):
                row_lower = [c.lower().strip() for c in row]
                has_sym = any(any(w in c for w in SYMBOL_KEYWORDS) for c in row_lower)
                has_type = any(any(w in c for w in TYPE_KEYWORDS) for c in row_lower)
                
                if has_sym and has_type:
                    is_trade_table = True
                    header_idx = idx
                    
                    has_position = any(any(w in c for w in POSITION_KEYWORDS) for c in row_lower)
                    has_deal = any(any(w in c for w in DEAL_KEYWORDS) for c in row_lower)
                    has_order = any(any(w in c for w in ORDER_KEYWORDS) for c in row_lower)
                    has_profit = any(any(w in c for w in PROFIT_KEYWORDS) for c in row_lower)
                    
                    if has_position:
                        table_type = "POSITIONS"
                    elif has_deal:
                        table_type = "DEALS"
                    elif has_order and not has_profit:
                        table_type = "ORDERS"
                    elif has_profit:
                        table_type = "TRADES"
                    break
            
            if is_trade_table:
                if table_type == "POSITIONS":
                    positions_table = (table_rows, header_idx)
                elif table_type == "TRADES":
                    trades_table = (table_rows, header_idx)
                elif table_type == "DEALS":
                    deals_table = (table_rows, header_idx)
                elif table_type == "unknown":
                    fallback_table = (table_rows, header_idx)

        # Select the best table to prevent duplicates
        if positions_table:
            selected_table_info = positions_table
            logger.info("Selected POSITIONS table for parsing to avoid Orders/Deals duplicates.")
        elif trades_table:
            selected_table_info = trades_table
            logger.info("Selected TRADES (Strategy Tester) table for parsing.")
        elif deals_table:
            selected_table_info = deals_table
            logger.info("Selected DEALS table for parsing.")
        elif fallback_table:
            selected_table_info = fallback_table
            logger.info("Selected fallback trade table for parsing.")
        else:
            # If no table could be classified but we have raw rows, use the first table's first row as fallback header
            if tables:
                selected_table_info = (tables[0], 0)
                logger.info("No trade table matched headers. Using first table as fallback.")
            else:
                return trades

        target_rows, header_idx = selected_table_info
        header_row = target_rows[header_idx]
        header_lower = [c.lower().strip() for c in header_row]
        
        # Dynamic Column Mapper from the selected header row
        time_indices = []
        price_indices = []
        symbol_idx = 4
        direction_idx = 2
        profit_idx = 12
        ticket_idx = 1
        volume_idx = 4
        
        for idx, col_val in enumerate(header_lower):
            if any(w in col_val for w in SYMBOL_KEYWORDS):
                symbol_idx = idx
            elif any(w in col_val for w in TYPE_KEYWORDS):
                direction_idx = idx
            elif any(w in col_val for w in PROFIT_KEYWORDS):
                profit_idx = idx
            elif any(w in col_val for w in TIME_KEYWORDS):
                time_indices.append(idx)
            elif any(w in col_val for w in PRICE_KEYWORDS):
                price_indices.append(idx)
            elif any(w in col_val for w in POSITION_KEYWORDS) or "ticket" in col_val or "bilet" in col_val:
                ticket_idx = idx
            elif any(w in col_val for w in VOLUME_KEYWORDS):
                volume_idx = idx

        # Set fallbacks if mapper failed to find key fields
        if not time_indices:
            time_indices = [1, 8]
        if not price_indices:
            price_indices = [5, 9]

        # Extract trades from selected table rows starting after the header row
        for row in target_rows[header_idx + 1:]:
            shift = 0
            if len(row) > 4:
                try:
                    # Volume should be numeric. Let's try to convert it.
                    v_idx = volume_idx if volume_idx < len(row) else 4
                    float(row[v_idx].replace(" ", "").replace(",", ""))
                except ValueError:
                    # It's a text comment! So index 4 is the comment, and all subsequent columns are shifted by +1
                    shift = 1
            
            # Apply shift to all indices that are at or after the comment column (index 4)
            r_symbol_idx = symbol_idx + shift if symbol_idx >= 4 else symbol_idx
            r_direction_idx = direction_idx + shift if direction_idx >= 4 else direction_idx
            r_profit_idx = profit_idx + shift if profit_idx >= 4 else profit_idx
            
            if len(row) <= max(r_symbol_idx, r_direction_idx, r_profit_idx):
                continue
                
            direction = row[r_direction_idx].upper().strip()
            if "BUY" not in direction and "SELL" not in direction:
                continue
                
            try:
                # Retrieve and adjust index mappings
                o_time_idx = time_indices[0] if len(time_indices) > 0 else 1
                o_price_idx = price_indices[0] if len(price_indices) > 0 else 5
                c_price_idx = price_indices[1] if len(price_indices) > 1 else (price_indices[0] if len(price_indices) > 0 else 9)
                
                r_open_time_idx = o_time_idx + shift if o_time_idx >= 4 else o_time_idx
                r_open_price_idx = o_price_idx + shift if o_price_idx >= 4 else o_price_idx
                r_close_price_idx = c_price_idx + shift if c_price_idx >= 4 else c_price_idx
                
                r_ticket_idx = ticket_idx + shift if ticket_idx >= 4 else ticket_idx
                r_volume_idx = volume_idx + shift if volume_idx >= 4 else volume_idx
                
                ticket_val = int(row[r_ticket_idx]) if r_ticket_idx < len(row) and row[r_ticket_idx].isdigit() else 0
                volume_val = float(row[r_volume_idx].replace(" ", "").replace(",", "")) if r_volume_idx < len(row) else 0.1
                comment_val = row[4] if shift == 1 and 4 < len(row) else ""
                
                raw_profit = row[r_profit_idx].replace(" ", "").replace(",", "")
                raw_entry = row[r_open_price_idx].replace(" ", "").replace(",", "")
                raw_exit = row[r_close_price_idx].replace(" ", "").replace(",", "")
                
                trades.append({
                    "time_str": row[r_open_time_idx],
                    "symbol": row[r_symbol_idx],
                    "direction": "BUY" if "BUY" in direction else "SELL",
                    "entry_price": float(raw_entry),
                    "exit_price": float(raw_exit),
                    "profit": float(raw_profit),
                    "ticket": ticket_val,
                    "volume": volume_val,
                    "comment": comment_val,
                })
            except Exception as parse_err:
                # Graceful skip for non-numeric/header/summary rows
                logger.debug(f"Skipped parsing non-trade data row: {parse_err}")
                continue

        deduped = self._deduplicate_trades(trades)
        logger.info(f"Successfully parsed {len(trades)} trades from MT5 HTML history. Deduplicated to {len(deduped)} unique trades.")
        return deduped

    def normalize_symbol(self, sym: str) -> str:
        """Normalizes broker symbols to match ForexSAI internal symbols."""
        s = sym.upper().strip()
        if "NDX" in s or "NAS" in s or "USTEC" in s:
            return "NDX.INDX"
        if "XAU" in s or "GOLD" in s:
            return "XAUUSD"
        if "DAX" in s or "DE30" in s or "DE40" in s or "GDAXI" in s:
            return "GDAXI.INDX"
        if "OIL" in s or "WTI" in s or "CL" in s or "XTI" in s:
            return "USOIL.FOREX"
        return s

    def parse_datetime(self, time_str: str) -> Optional[datetime]:
        """Parses MT5 time string format (e.g., '2026.05.26 14:32:05' or ISO)."""
        formats = [
            "%Y.%m.%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z"
        ]
        t = time_str.strip()
        for fmt in formats:
            try:
                dt = datetime.strptime(t, fmt)
                # MT5 times are generally broker local or GMT, coerce to UTC for matching
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    def _deduplicate_trades(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates trades by ticket ID or a composite key of symbol, direction, entry price, and open time."""
        seen = set()
        deduped = []
        for t in trades:
            ticket = t.get("ticket") or 0
            if ticket != 0:
                key = f"t_{ticket}"
            else:
                key = f"p_{t.get('symbol')}_{t.get('direction')}_{t.get('entry_price')}_{t.get('time_str')}"
            
            if key in seen:
                continue
            seen.add(key)
            deduped.append(t)
        return deduped

    def detect_timezone_offset(self, trades: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> float:
        """
        Scans potential timezone offsets (from -12 to +14 hours) to automatically
        find the offset that aligns the MT5 trade execution times with the database signal times.
        """
        best_offset = 0.0
        max_matches = 0
        
        # We will try every hour offset from -12 to +14
        # and also some common half-hour offsets if needed (e.g. India GMT+5.5, Iran GMT+3.5, etc.)
        candidate_offsets = [float(h) for h in range(-12, 15)]
        # Add half-hour offsets for completeness
        candidate_offsets += [h + 0.5 for h in range(-11, 14)]
        
        # Filter signals to only those that have a valid created_at datetimes
        parsed_signals = []
        for sig in signals:
            try:
                sig_time = datetime.fromisoformat(sig["created_at"].replace("Z", "+00:00"))
                parsed_signals.append({
                    "symbol": sig.get("symbol"),
                    "direction": (sig.get("ml_direction") or "HOLD").upper(),
                    "entry_price": float(sig.get("ml_entry_price") or 0.0),
                    "time": sig_time
                })
            except Exception:
                continue
                
        if not parsed_signals:
            return 0.0

        # Filter trades that can be parsed
        parsed_trades = []
        for trade in trades:
            t_time = self.parse_datetime(trade["time_str"])
            if t_time:
                parsed_trades.append({
                    "symbol": self.normalize_symbol(trade["symbol"]),
                    "direction": trade["direction"],
                    "entry_price": trade["entry_price"],
                    "time": t_time
                })
                
        if not parsed_trades:
            return 0.0

        # Try each offset
        for offset in candidate_offsets:
            current_matches = 0
            for trade in parsed_trades:
                adjusted_time = trade["time"] - timedelta(hours=offset)
                
                # Look for a matching signal
                for sig in parsed_signals:
                    if sig["symbol"] != trade["symbol"] or sig["direction"] != trade["direction"]:
                        continue
                        
                    # Check if entry prices are close (within 3%)
                    if sig["entry_price"] > 0 and trade["entry_price"] > 0:
                        price_diff_pct = abs(trade["entry_price"] - sig["entry_price"]) / sig["entry_price"]
                        if price_diff_pct > 0.03:
                            continue
                            
                    # Check if time difference is within 10 minutes (600s) for detection purposes
                    time_diff = abs(adjusted_time - sig["time"])
                    if time_diff <= timedelta(minutes=10):
                        current_matches += 1
                        break # matched this trade to a signal for this offset
                        
            if current_matches > max_matches:
                max_matches = current_matches
                best_offset = offset
                
        if max_matches > 0:
            logger.info(f"Auto-detected timezone offset: {best_offset} hours (aligned {max_matches} trades)")
        else:
            logger.info("No timezone offset could be confidently auto-detected. Defaulting to 0 hours.")
            
        return best_offset

    async def match_and_sync_trades(self, trades: List[Dict[str, Any]], tolerance_seconds: int = 90) -> Dict[str, Any]:
        """Matches parsed trades with Supabase prediction logs and updates them in bulk."""
        if not self.client:
            return {"success": False, "error": "Supabase client not available"}

        synced_count = 0
        total_trades = len(trades)
        matched_details = []
        bulk_prediction_updates = []
        bulk_mt5_trades = []

        try:
            # Collect all valid datetimes from parsed trades
            trade_times = []
            for t in trades:
                dt = self.parse_datetime(t["time_str"])
                if dt:
                    trade_times.append(dt)
            
            # Fetch active or recently completed signals matching the trades timeframe
            if trade_times:
                min_time = min(trade_times)
                max_time = max(trade_times)
                # Expand range by 3 days in both directions to handle timezones and broker offsets safely
                start_cutoff = (min_time - timedelta(days=3)).isoformat().replace("+00:00", "Z")
                end_cutoff = (max_time + timedelta(days=3)).isoformat().replace("+00:00", "Z")
                logger.info(f"Dynamically fetching prediction logs between {start_cutoff} and {end_cutoff} for matching.")
            else:
                # Fallback to 30 days if no times parsed (failsafe)
                start_cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
                end_cutoff = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z")
                logger.info("No trade datetimes found. Using standard 30-day window.")
            
            # Fetch active or recently completed signals matching the trades timeframe using pagination
            signals = []
            offset = 0
            chunk_size = 1000
            max_signals = 15000  # Safe cap to prevent infinite loop or slow response for massive uploads
            
            while len(signals) < max_signals:
                # Executes page-by-page fetching
                result = self.client.table("prediction_logs") \
                    .select("id, symbol, ml_direction, ml_entry_price, created_at, status") \
                    .gte("created_at", start_cutoff) \
                    .lte("created_at", end_cutoff) \
                    .order("created_at", desc=True) \
                    .range(offset, offset + chunk_size - 1) \
                    .execute()
                
                data = safe_get_data(result) or []
                signals.extend(data)
                
                if len(data) < chunk_size:
                    break
                offset += chunk_size

            # Deduplicate signals in case of any overlaps
            seen_sig = set()
            deduped_signals = []
            for sig in signals:
                sig_id = sig.get("id")
                if sig_id not in seen_sig:
                    seen_sig.add(sig_id)
                    deduped_signals.append(sig)
            signals = deduped_signals

            logger.info(f"Successfully fetched {len(signals)} prediction logs from database for matching.")
            if not signals:
                return {"success": True, "matched": 0, "total": total_trades, "message": "No prediction logs found in database to match."}

            # Auto-detect timezone offset
            detected_offset = self.detect_timezone_offset(trades, signals)
            logger.info(f"Using timezone offset of {detected_offset} hours for MT5 report matching.")

            # Map signals for easy lookup
            for trade in trades:
                raw_trade_time = self.parse_datetime(trade["time_str"])
                if not raw_trade_time:
                    continue

                trade_time = raw_trade_time - timedelta(hours=detected_offset)

                trade_symbol = self.normalize_symbol(trade["symbol"])
                trade_dir = trade["direction"]
                trade_entry = trade["entry_price"]

                best_match = None
                
                # --- STAGE 1: Strict matching (within 10 minutes & 1% price tolerance) ---
                min_price_diff = 0.01
                for sig in signals:
                    sig_symbol = sig.get("symbol")
                    sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                    if sig_symbol != trade_symbol or sig_dir != trade_dir:
                        continue

                    try:
                        sig_time = datetime.fromisoformat(sig["created_at"].replace("Z", "+00:00"))
                    except Exception:
                        continue

                    time_diff = abs(trade_time - sig_time)
                    if time_diff <= timedelta(minutes=10):
                        sig_entry = float(sig.get("ml_entry_price") or 0.0)
                        price_diff = abs(trade_entry - sig_entry) / sig_entry if sig_entry > 0 else 1.0
                        if price_diff < min_price_diff:
                            min_price_diff = price_diff
                            best_match = sig

                # --- STAGE 2: Moderate matching (within 6 hours & 0.5% price tolerance) ---
                if not best_match:
                    min_price_diff = 0.005
                    for sig in signals:
                        sig_symbol = sig.get("symbol")
                        sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                        if sig_symbol != trade_symbol or sig_dir != trade_dir:
                            continue

                        try:
                            sig_time = datetime.fromisoformat(sig["created_at"].replace("Z", "+00:00"))
                        except Exception:
                            continue

                        time_diff = abs(trade_time - sig_time)
                        if time_diff <= timedelta(hours=6):
                            sig_entry = float(sig.get("ml_entry_price") or 0.0)
                            price_diff = abs(trade_entry - sig_entry) / sig_entry if sig_entry > 0 else 1.0
                            if price_diff < min_price_diff:
                                min_price_diff = price_diff
                                best_match = sig

                # --- STAGE 3: Relaxed matching (within 24 hours & 0.25% price tolerance) ---
                if not best_match:
                    min_price_diff = 0.0025
                    for sig in signals:
                        sig_symbol = sig.get("symbol")
                        sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                        if sig_symbol != trade_symbol or sig_dir != trade_dir:
                            continue

                        try:
                            sig_time = datetime.fromisoformat(sig["created_at"].replace("Z", "+00:00"))
                        except Exception:
                            continue

                        time_diff = abs(trade_time - sig_time)
                        if time_diff <= timedelta(hours=24):
                            sig_entry = float(sig.get("ml_entry_price") or 0.0)
                            price_diff = abs(trade_entry - sig_entry) / sig_entry if sig_entry > 0 else 1.0
                            if price_diff < min_price_diff:
                                min_price_diff = price_diff
                                best_match = sig

                if best_match:
                    # Found matching prediction log! Sync real execution data
                    signal_id = best_match["id"]
                    
                    # Calculate real pips PnL
                    real_pips_pnl = 0.0
                    entry_p = trade["entry_price"]
                    exit_p = trade["exit_price"]
                    profit = trade["profit"]
                    
                    # Pip difference calculation based on symbol
                    def _pips_diff(entry, exit, sym, direction):
                        diff = (exit - entry) if direction == "BUY" else (entry - exit)
                        sym_upper = sym.upper()
                        if "XAUUSD" in sym_upper:
                            return diff / 0.1
                        if "USOIL" in sym_upper or "CL" in sym_upper:
                            return diff / 0.01
                        return diff  # NASDAQ / DAX

                    real_pips_pnl = _pips_diff(entry_p, exit_p, trade_symbol, trade_dir)
                    
                    # Calculate entry slippage
                    sig_entry_price = float(best_match.get("ml_entry_price") or entry_p)
                    slippage = abs(entry_p - sig_entry_price)
                    slippage_pips = _pips_diff(sig_entry_price, entry_p, trade_symbol, trade_dir)

                    # Part A: Accumulate prediction update payload ONLY if status has changed (e.g. from active to completed/stopped)
                    target_status = "completed" if profit > 0 else "stopped"
                    if best_match.get("status") != target_status:
                        bulk_prediction_updates.append({
                            "id": signal_id,
                            "status": target_status,
                            "resolution_reason": "mt5_manual_sync",
                            "exit_price": round(exit_p, 4),
                            "exit_time": trade_time.isoformat(),
                        })

                    # Part B: Accumulate mt5_trades payload
                    bulk_mt5_trades.append({
                        "ticket": trade.get("ticket", 0),
                        "symbol": trade.get("symbol", ""),
                        "normalized_symbol": trade_symbol,
                        "direction": trade_dir,
                        "entry_type": "inout",
                        "volume": trade.get("volume", 0.1),
                        "price": round(entry_p, 4),
                        "profit": round(profit, 2),
                        "deal_time": trade_time.isoformat(),
                        "comment": trade.get("comment", ""),
                        "matched_prediction_id": signal_id,
                        "matched_at": datetime.now(timezone.utc).isoformat(),
                        "match_confidence": 100.0,
                    })

                    matched_details.append({
                        "signal_id": signal_id[:8],
                        "symbol": trade_symbol,
                        "direction": trade_dir,
                        "real_pnl": round(real_pips_pnl, 1),
                        "slippage": round(abs(slippage_pips), 1),
                    })

            # Perform parallel concurrent updates to prediction_logs (PATCH updates only, avoiding NOT NULL insert constraint issues of upsert)
            if bulk_prediction_updates:
                logger.info(f"Synchronizing {len(bulk_prediction_updates)} matched prediction logs in parallel...")
                
                def _update_one(item):
                    pred_id = item["id"]
                    payload = {
                        "status": item["status"],
                        "resolution_reason": item["resolution_reason"],
                        "exit_price": item["exit_price"],
                        "exit_time": item["exit_time"],
                    }
                    try:
                        self.client.table("prediction_logs").eq("id", pred_id).update(payload)
                    except Exception as pred_err:
                        logger.warning(f"Failed to update prediction_logs row {pred_id[:8]}: {pred_err}")

                import asyncio
                sem = asyncio.Semaphore(3)  # Limit to 3 concurrent workers to be extremely safe under Supabase pool limits
                
                async def _worker(item):
                    async with sem:
                        await asyncio.to_thread(_update_one, item)
                
                await asyncio.gather(*[_worker(x) for x in bulk_prediction_updates])

            # Perform bulk upsert to mt5_trades (idempotent unique constraint upsert)
            if bulk_mt5_trades:
                try:
                    logger.info(f"Bulk upserting {len(bulk_mt5_trades)} trades to mt5_trades in Supabase...")
                    self.client.table("mt5_trades").upsert(bulk_mt5_trades, on_conflict="ticket,entry_type")
                    synced_count = len(bulk_mt5_trades)
                except Exception as mt5_err:
                    logger.error(f"Failed bulk mt5_trades upsert: {mt5_err}")
                    return {"success": False, "error": f"Failed bulk mt5_trades upsert: {mt5_err}"}

            return {
                "success": True,
                "matched": synced_count,
                "total": total_trades,
                "matched_details": matched_details,
                "message": f"Successfully parsed {total_trades} trades. Matched and updated {synced_count} platform signals.",
            }

        except Exception as e:
            logger.error(f"Error matching trades: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
