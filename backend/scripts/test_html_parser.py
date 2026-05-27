import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.mt5_report_matcher import MT5ReportMatcher

html_path = "/Users/melihcanodacioglu/Desktop/ReportHistory-52832695.html"

# Read file
content = ""
with open(html_path, "rb") as f_bytes:
    b_content = f_bytes.read()
    for enc in ["utf-16", "utf-8", "windows-1254", "iso-8859-9", "windows-1252", "latin-1"]:
        try:
            content = b_content.decode(enc)
            if enc == "utf-16" and content.count("\x00") > len(content) * 0.3:
                continue
            break
        except Exception:
            continue
    if not content:
        content = b_content.decode("utf-8", errors="ignore")

matcher = MT5ReportMatcher()
trades = matcher.parse_html_report(content)

print(f"Total trades parsed: {len(trades)}")
if trades:
    times = []
    for t in trades:
        dt = matcher.parse_datetime(t["time_str"])
        if dt:
            times.append(dt)
    if times:
        print(f"Min Trade Time: {min(times)}")
        print(f"Max Trade Time: {max(times)}")
    else:
        print("No valid datetimes parsed!")
else:
    print("No trades parsed!")
