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
        """Parses MT5 history in standard HTML Report format."""
        trades = []
        
        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(content, "lxml")
                # Look for table rows
                rows = soup.find_all("tr")
                for row in rows:
                    cols = [td.get_text().strip() for td in row.find_all("td")]
                    if len(cols) < 9:
                        continue

                    # Standard MT5 HTML History Row:
                    # Ticket, Time, Type, Volume, Symbol, Price, S/L, T/P, Time, Price, Commission, Swap, Profit
                    direction = cols[2].upper()
                    if "BUY" not in direction and "SELL" not in direction:
                        continue

                    try:
                        trades.append({
                            "time_str": cols[1],  # Position Open Time
                            "symbol": cols[4],
                            "direction": "BUY" if "BUY" in direction else "SELL",
                            "entry_price": float(cols[5].replace(" ", "").replace(",", "")),
                            "exit_price": float(cols[9].replace(" ", "").replace(",", "")),
                            "profit": float(cols[12].replace(" ", "").replace(",", "")),
                        })
                    except (ValueError, IndexError) as parse_err:
                        # Fallback try-catch for slight table structure variations
                        logger.debug(f"Skipping row parse due to variation: {parse_err}")
                        continue
                return trades
            except Exception as e:
                logger.error(f"BeautifulSoup parsing failed: {e}. Trying fallback regex parser.")

        # Robust Regex Fallback Parser (Zero-Failure)
        try:
            # Match tr tags and extract td values
            tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
            for tr in tr_matches:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
                cols = [re.sub(r'<[^>]*>', '', td).strip() for td in tds]
                
                if len(cols) < 9:
                    continue
                    
                direction = cols[2].upper()
                if "BUY" not in direction and "SELL" not in direction:
                    continue
                    
                try:
                    trades.append({
                        "time_str": cols[1],
                        "symbol": cols[4],
                        "direction": "BUY" if "BUY" in direction else "SELL",
                        "entry_price": float(cols[5].replace(" ", "").replace(",", "")),
                        "exit_price": float(cols[9].replace(" ", "").replace(",", "")),
                        "profit": float(cols[12].replace(" ", "").replace(",", "")),
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.error(f"Regex fallback parser failed: {e}")

        return trades

    def normalize_symbol(self, sym: str) -> str:
        """Normalizes broker symbols to match ForexSAI internal symbols."""
        s = sym.upper().strip()
        if "NDX" in s or "NAS" in s or "USTEC" in s:
            return "NDX.INDX"
        if "XAU" in s or "GOLD" in s:
            return "XAUUSD"
        if "DAX" in s or "DE30" in s or "GDAXI" in s:
            return "GDAXI.INDX"
        if "OIL" in s or "WTI" in s or "CL" in s:
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

            # Map signals for easy lookup
            for trade in trades:
                trade_time = self.parse_datetime(trade["time_str"])
                if not trade_time:
                    continue

                trade_symbol = self.normalize_symbol(trade["symbol"])
                trade_dir = trade["direction"]
                trade_entry = trade["entry_price"]

                best_match = None
                min_diff = timedelta(seconds=tolerance_seconds)

                for sig in signals:
                    sig_symbol = sig.get("symbol")
                    sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                    
                    if sig_symbol != trade_symbol or sig_dir != trade_dir:
                        continue

                    # Calculate time difference
                    try:
                        sig_time = datetime.fromisoformat(sig["created_at"].replace("Z", "+00:00"))
                    except Exception:
                        continue

                    time_diff = abs(trade_time - sig_time)
                    if time_diff < min_diff:
                        # Price validation fallback (within 3% tolerance)
                        sig_entry = float(sig.get("ml_entry_price") or 0.0)
                        if sig_entry > 0:
                            price_diff_pct = abs(trade_entry - sig_entry) / sig_entry
                            if price_diff_pct > 0.03:
                                continue  # Entry prices are too far apart (likely different setups)
                        
                        min_diff = time_diff
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
