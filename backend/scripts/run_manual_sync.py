import os
import sys
import glob
import asyncio
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
# Populate environment variables for supabase client
if settings.supabase_url:
    os.environ["SUPABASE_URL"] = settings.supabase_url
if settings.supabase_key:
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = settings.supabase_key
    os.environ["SUPABASE_KEY"] = settings.supabase_key

from services.mt5_report_matcher import MT5ReportMatcher

async def run_sync():
    print("--- Starting Manual MT5 Trade Sync Utility ---")
    
    # 1. Discover MT5 HTML files on Desktop and Downloads
    html_files = glob.glob("/Users/melihcanodacioglu/Desktop/ReportHistory*.html") + \
                 glob.glob("/Users/melihcanodacioglu/Downloads/ReportHistory*.html")
                 
    if not html_files:
        # Check current folder and parents for files containing report or history
        all_htmls = glob.glob("/Users/melihcanodacioglu/Desktop/*.html") + glob.glob("/Users/melihcanodacioglu/Downloads/*.html")
        html_files = [f for f in all_htmls if "reporthistory" in f.lower() or "report" in f.lower()]

    if not html_files:
        print("❌ No MT5 Trade History HTML files discovered.")
        return

    matcher = MT5ReportMatcher()
    
    for html_path in html_files:
        print(f"\nProcessing report file: {html_path}")
        
        # Read contents
        content = ""
        with open(html_path, "rb") as f_bytes:
            b_content = f_bytes.read()
            for enc in ["utf-16", "utf-8", "windows-1254", "iso-8859-9", "windows-1252", "latin-1"]:
                try:
                    content = b_content.decode(enc)
                    if enc == "utf-16" and content.count("\x00") > len(content) * 0.3:
                        continue
                    print(f"  Successfully decoded using {enc}")
                    break
                except Exception:
                    continue

        if not content:
            print("  ❌ Failed to decode file using any common encoding. Skipping.")
            continue

        # Parse trades
        trades = matcher.parse_html_report(content)
        if not trades:
            print("  ❌ No trades could be parsed from this file.")
            continue

        print(f"  Successfully parsed {len(trades)} trades from HTML.")
        
        # Perform matching and database synchronization
        print("  Synchronizing trades with Supabase database...")
        sync_result = await matcher.match_and_sync_trades(trades, tolerance_seconds=90)
        
        if sync_result.get("success"):
            print(f"  ✅ SUCCESS: Matched and updated {sync_result['matched']} trades out of {sync_result['total']} total trades!")
        else:
            print(f"  ❌ FAILED: {sync_result.get('error')}")

    print("\n--- Manual MT5 Trade Sync Utility Completed ---")

if __name__ == "__main__":
    asyncio.run(run_sync())
