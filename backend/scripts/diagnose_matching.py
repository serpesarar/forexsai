import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
if settings.supabase_url:
    os.environ["SUPABASE_URL"] = settings.supabase_url
if settings.supabase_key:
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = settings.supabase_key
    os.environ["SUPABASE_KEY"] = settings.supabase_key

from database.supabase_client import get_supabase_client
client = get_supabase_client()

html_path = "/Users/melihcanodacioglu/Desktop/ReportHistory-52832695.html"
print("Diagnosing with file:", html_path)

# Multi-encoding read
content = ""
with open(html_path, "rb") as f_bytes:
    b_content = f_bytes.read()
    for enc in ["utf-16", "utf-8", "windows-1254", "iso-8859-9", "windows-1252", "latin-1"]:
        try:
            content = b_content.decode(enc)
            if enc == "utf-16" and content.count("\x00") > len(content) * 0.3:
                continue
            print(f"Decoded successfully with encoding: {enc}")
            break
        except Exception:
            continue

if not content:
    content = b_content.decode("utf-8", errors="ignore")

# Define multilingual keywords
SYMBOL_KEYWORDS = {"symbol", "sembol", "item", "yatırım"}
TYPE_KEYWORDS = {"type", "action", "direction", "tür", "tip", "yön", "işlem"}
PROFIT_KEYWORDS = {"profit", "pnl", "kâr", "kar", "kazanç"}
POSITION_KEYWORDS = {"position", "pozisyon"}
DEAL_KEYWORDS = {"deal", "anlaşma"}
ORDER_KEYWORDS = {"order", "emir", "state", "durum"}
VOLUME_KEYWORDS = {"volume", "lot", "hacim", "miktar"}
PRICE_KEYWORDS = {"price", "fiyat"}
TIME_KEYWORDS = {"time", "zaman", "tarih", "saat"}

# Segment tables
from bs4 import BeautifulSoup
soup = BeautifulSoup(content, "lxml")
tables = []
for table in soup.find_all("table"):
    table_rows = []
    for tr in table.find_all("tr"):
        cols = [cell.get_text().strip() for cell in tr.find_all(["td", "th"])]
        if cols:
            table_rows.append(cols)
    if table_rows:
        tables.append(table_rows)

print(f"Found {len(tables)} tables in HTML.")

# Dynamic Table Selector using Multilingual keywords
selected_table_info = None
positions_table = None
trades_table = None
deals_table = None

for idx, table_rows in enumerate(tables):
    is_trade_table = False
    table_type = "unknown"
    header_idx = -1
    
    for r_idx, row in enumerate(table_rows[:20]):
        row_lower = [c.lower().strip() for c in row]
        has_sym = any(any(w in c for w in SYMBOL_KEYWORDS) for c in row_lower)
        has_type = any(any(w in c for w in TYPE_KEYWORDS) for c in row_lower)
        
        if has_sym and has_type:
            is_trade_table = True
            header_idx = r_idx
            
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
        print(f"Table {idx} classified as {table_type} (Header at row {header_idx})")
        if table_type == "POSITIONS":
            positions_table = (table_rows, header_idx)
        elif table_type == "TRADES":
            trades_table = (table_rows, header_idx)
        elif table_type == "DEALS":
            deals_table = (table_rows, header_idx)

# Select the best table to prevent duplicates
if positions_table:
    selected_table_info = positions_table
    print("Selected POSITIONS table.")
elif trades_table:
    selected_table_info = trades_table
    print("Selected TRADES table.")
elif deals_table:
    selected_table_info = deals_table
    print("Selected DEALS table.")

if not selected_table_info:
    print("❌ No trade table identified!")
    sys.exit(0)

target_rows, header_idx = selected_table_info
header_row = target_rows[header_idx]
header_lower = [c.lower().strip() for c in header_row]

# Map columns
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

from services.mt5_report_matcher import MT5ReportMatcher
matcher = MT5ReportMatcher()

trades = []
for row in target_rows[header_idx + 1:]:
    shift = 0
    if len(row) > 4:
        try:
            v_idx = volume_idx if volume_idx < len(row) else 4
            float(row[v_idx].replace(" ", "").replace(",", ""))
        except ValueError:
            shift = 1
            
    r_symbol_idx = symbol_idx + shift if symbol_idx >= 4 else symbol_idx
    r_direction_idx = direction_idx + shift if direction_idx >= 4 else direction_idx
    r_profit_idx = profit_idx + shift if profit_idx >= 4 else profit_idx
    
    if len(row) <= max(r_symbol_idx, r_direction_idx, r_profit_idx):
        continue
        
    direction = row[r_direction_idx].upper().strip()
    if "BUY" not in direction and "SELL" not in direction:
        continue
        
    try:
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
        continue

print(f"Parsed {len(trades)} unique trades.")

if not trades:
    sys.exit(0)

# Fetch prediction logs in parallel chunks
async def main():
    trade_times = []
    for t in trades:
        dt = matcher.parse_datetime(t["time_str"])
        if dt:
            trade_times.append(dt)
            
    if not trade_times:
        print("❌ No valid trade datetimes found!")
        sys.exit(0)
        
    min_time = min(trade_times)
    max_time = max(trade_times)
    
    start_dt = min_time - timedelta(days=3)
    end_dt = max_time + timedelta(days=3)
    
    print(f"Dynamic time range: {start_dt.isoformat()} to {end_dt.isoformat()}")
    
    # Split range into 3-day intervals
    chunks = []
    curr = start_dt
    while curr < end_dt:
        nxt = min(curr + timedelta(days=3), end_dt)
        chunks.append((curr, nxt))
        curr = nxt
        
    print(f"Splitting timeframe into {len(chunks)} chunks...")
    
    sem = asyncio.Semaphore(4) # Limit to 4 concurrent database requests to avoid rate limits
    
    async def fetch_chunk(start, end):
        async with sem:
            chunk_signals = []
            offset = 0
            chunk_size = 1000
            s_iso = start.isoformat().replace("+00:00", "Z")
            e_iso = end.isoformat().replace("+00:00", "Z")
            
            while True:
                def _query():
                    # REMOVED .order() to optimize database fetch query extremely fast without table sort!
                    return client.table("prediction_logs") \
                        .select("id, symbol, ml_direction, ml_entry_price, created_at, status") \
                        .gte("created_at", s_iso) \
                        .lte("created_at", e_iso) \
                        .range(offset, offset + chunk_size - 1) \
                        .execute()
                
                res = await asyncio.to_thread(_query)
                data = res.data if hasattr(res, "data") else res.get("data") or []
                chunk_signals.extend(data)
                
                if len(data) < chunk_size:
                    break
                offset += chunk_size
                
            return chunk_signals

    tasks = [fetch_chunk(start, end) for start, end in chunks]
    results = await asyncio.gather(*tasks)
    
    signals = []
    for r in results:
        signals.extend(r)
        
    # Deduplicate signals
    seen = set()
    deduped = []
    for sig in signals:
        sid = sig.get("id")
        if sid not in seen:
            seen.add(sid)
            deduped.append(sig)
            
    print(f"Fetched {len(deduped)} UNIQUE prediction logs from DB.")
    
    # Match trades with prediction logs
    # Auto-detect timezone offset
    detected_offset = matcher.detect_timezone_offset(trades, deduped)
    print(f"Auto-detected offset: {detected_offset} hours")
    
    matched = 0
    matched_details = []
    
    for idx, trade in enumerate(trades):
        raw_trade_time = matcher.parse_datetime(trade["time_str"])
        if not raw_trade_time:
            continue
        trade_time = raw_trade_time - timedelta(hours=detected_offset)
        trade_symbol = matcher.normalize_symbol(trade["symbol"])
        trade_dir = trade["direction"]
        trade_entry = trade["entry_price"]
        
        best_match = None
        min_price_diff = 0.01 # 1% price tolerance for Stage 1
        
        for sig in deduped:
            sig_symbol = sig.get("symbol")
            sig_dir = (sig.get("ml_direction") or "HOLD").upper()
            if sig_symbol == trade_symbol and sig_dir == trade_dir:
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
                        
        if not best_match:
            min_price_diff = 0.005 # 0.5% price tolerance for Stage 2
            for sig in deduped:
                sig_symbol = sig.get("symbol")
                sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                if sig_symbol == trade_symbol and sig_dir == trade_dir:
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
                            
        if not best_match:
            min_price_diff = 0.0025 # 0.25% price tolerance for Stage 3
            for sig in deduped:
                sig_symbol = sig.get("symbol")
                sig_dir = (sig.get("ml_direction") or "HOLD").upper()
                if sig_symbol == trade_symbol and sig_dir == trade_dir:
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
            matched += 1
            matched_details.append({
                "trade_idx": idx,
                "symbol": trade_symbol,
                "direction": trade_dir,
                "trade_price": trade_entry,
                "signal_price": float(best_match["ml_entry_price"]),
                "time_diff_hours": abs(trade_time - datetime.fromisoformat(best_match["created_at"].replace("Z", "+00:00"))).total_seconds() / 3600.0
            })
            
    print(f"\n✅ Diagnostic Results: MATCHED {matched} out of {len(trades)} trades!")
    print("Sample Matches:")
    for m in matched_details[:10]:
        print(f"  Match: {m['symbol']} {m['direction']} | Trade Price: {m['trade_price']} | Signal Price: {m['signal_price']} | Time Diff: {m['time_diff_hours']:.2f} hours")

if __name__ == "__main__":
    asyncio.run(main())
