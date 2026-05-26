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
            
        return trades

    def parse_html_report(self, content: str) -> List[Dict[str, Any]]:
        """Parses MT5 history in standard HTML Report format dynamically mapping columns."""
        trades = []
        raw_rows = []
        
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(content, "lxml")
                # Find all table rows in the HTML document
                for tr in soup.find_all("tr"):
                    cols = [cell.get_text().strip() for cell in tr.find_all(["td", "th"])]
                    if cols:
                        raw_rows.append(cols)
            except Exception as e:
                logger.error(f"BeautifulSoup parsing failed: {e}. Trying fallback regex parser.")
                
        if not raw_rows:
            # Robust fallback regex cell parser
            try:
                tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
                for tr in tr_matches:
                    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
                    cols = [re.sub(r'<[^>]*>', '', cell).strip() for cell in cells]
                    if cols:
                        raw_rows.append(cols)
            except Exception as e:
                logger.error(f"Regex fallback parser failed: {e}")

        if not raw_rows:
            return trades

        # Dynamic Column Mapper
        # Standard default indices:
        time_indices = []
        price_indices = []
        symbol_idx = 4
        direction_idx = 2
        profit_idx = 12
        header_mapped = False
        
        # Look for the header row within the first 25 rows
        for row in raw_rows[:25]:
            row_lower = [c.lower().strip() for c in row]
            
            # Identify the main header row containing key fields
            if any("symbol" in c for c in row_lower) and any("type" in c or "action" in c for c in row_lower) and any("profit" in c for c in row_lower):
                temp_time_indices = []
                temp_price_indices = []
                
                for idx, col_val in enumerate(row_lower):
                    if "symbol" in col_val:
                        symbol_idx = idx
                    elif "type" in col_val or "action" in col_val:
                        direction_idx = idx
                    elif "profit" in col_val:
                        profit_idx = idx
                    elif "time" in col_val:
                        temp_time_indices.append(idx)
                    elif "price" in col_val:
                        temp_price_indices.append(idx)
                        
                if temp_time_indices:
                    time_indices = temp_time_indices
                if temp_price_indices:
                    price_indices = temp_price_indices
                header_mapped = True
                logger.info(f"Dynamically mapped HTML headers: Symbol={symbol_idx}, Direction={direction_idx}, Profit={profit_idx}, Time={time_indices}, Price={price_indices}")
                break

        # Fallback to defaults if no header is found
        if not header_mapped:
            logger.info("Header row not found. Using fallback standard MT5 profile.")
            time_indices = [1, 8]
            price_indices = [5, 9]
            symbol_idx = 4
            direction_idx = 2
            profit_idx = 12

        # Extract trades from data rows
        for row in raw_rows:
            # We check if there is a shift by examining if we have a non-numeric column where a numeric one is expected
            # For MT5, Volume is usually at index 4 (standard) or index 5 (if comment column is at index 4).
            # If row has more columns than headers, or if the column at index 4 contains text (comment), it's shifted!
            shift = 0
            if len(row) > 4:
                try:
                    # Volume should be numeric. Let's try to convert it.
                    float(row[4].replace(" ", "").replace(",", ""))
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
                })
            except Exception as parse_err:
                # Graceful skip for non-numeric/header/summary rows
                logger.debug(f"Skipped parsing non-trade data row: {parse_err}")
                continue

        logger.info(f"Successfully parsed {len(trades)} trades from MT5 HTML history.")
        return trades

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
        """Matches parsed trades with Supabase prediction logs and updates them."""
        if not self.client:
            return {"success": False, "error": "Supabase client not available"}

        synced_count = 0
        total_trades = len(trades)
        matched_details = []

        try:
            # Fetch active or recently completed signals (past 30 days) to match
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
            
            result = self.client.table("prediction_logs") \
                .select("id, symbol, ml_direction, ml_entry_price, created_at, status") \
                .gte("created_at", cutoff) \
                .limit(2000) \
                .execute()

            signals = safe_get_data(result) or []
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

                    # Update Supabase
                    update_data = {
                        "real_entry_price": round(entry_p, 4),
                        "real_exit_price": round(exit_p, 4),
                        "real_pnl_pips": round(real_pips_pnl, 2),
                        "slippage_pips": round(abs(slippage_pips), 2),
                        # Mark status as completed/stopped based on profit
                        "status": "completed" if profit > 0 else "stopped",
                        "resolution_reason": "mt5_manual_sync",
                        "exit_price": round(exit_p, 4),
                        "exit_time": trade_time.isoformat(),
                    }

                    try:
                        self.client.table("prediction_logs").eq("id", signal_id).update(update_data).execute()
                        synced_count += 1
                        matched_details.append({
                            "signal_id": signal_id[:8],
                            "symbol": trade_symbol,
                            "direction": trade_dir,
                            "real_pnl": round(real_pips_pnl, 1),
                            "slippage": round(abs(slippage_pips), 1),
                        })
                    except Exception as db_err:
                        logger.error(f"Failed to update prediction_log {signal_id[:8]}: {db_err}")

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
