import json, sys, urllib.request
from datetime import datetime

url = "https://upbeat-flow-production.up.railway.app/api/data/ohlcv?symbol=NDX.INDX&timeframe=1h&limit=50"
resp = urllib.request.urlopen(url, timeout=15)
data = json.loads(resp.read())

candles = data.get('data', [])
print(f"Total candles: {len(candles)}")
if not candles:
    print("NO DATA!")
    sys.exit()

print(f"First ts: {candles[0]['timestamp']}")
print(f"Last ts: {candles[-1]['timestamp']}")

for i, c in enumerate(candles[:15]):
    ts = c['timestamp']
    ts_s = ts / 1000 if ts > 1e12 else ts
    dt = datetime.utcfromtimestamp(ts_s)
    vol = c.get('volume', 0)
    print(f"  [{i:3d}] {dt} O={c['open']:.2f} C={c['close']:.2f} V={vol}")

print("  ...")

prev_ts_ms = None
gaps = []
for i, c in enumerate(candles):
    ts = c['timestamp']
    ts_ms = ts * 1000 if ts < 1e12 else ts
    if prev_ts_ms is not None:
        gap_h = (ts_ms - prev_ts_ms) / 3600000
        if gap_h > 1.5:
            dt1 = datetime.utcfromtimestamp(prev_ts_ms / 1000)
            dt2 = datetime.utcfromtimestamp(ts_ms / 1000)
            gaps.append((i, gap_h, str(dt1), str(dt2)))
    prev_ts_ms = ts_ms

print(f"\nGaps > 1.5h: {len(gaps)}")
for idx, gh, d1, d2 in gaps:
    print(f"  [{idx:3d}] {gh:6.1f}h gap: {d1} -> {d2}")

zv = sum(1 for c in candles if c.get('volume', 0) == 0)
print(f"\nZero-volume candles: {zv}/{len(candles)}")

