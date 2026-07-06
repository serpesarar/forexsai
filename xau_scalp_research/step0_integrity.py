"""Step 0 — XAUUSD 1m data integrity verification. Read-only."""
import json
from datetime import datetime, timezone

PATH = "/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_xauusd_1m_bars.json"

with open(PATH) as f:
    doc = json.load(f)

bars = doc["bars"]
n = len(bars)
print(f"symbol={doc['symbol']} timeframe={doc['timeframe']} count_field={doc['count']} actual={n}")
print(f"since={doc['since']} until={doc['until']}")

ts = [b["t"] for b in bars]

# 1. Duplicate / out-of-order timestamps
dups = 0
out_of_order = 0
for i in range(1, n):
    if ts[i] == ts[i-1]:
        dups += 1
    elif ts[i] < ts[i-1]:
        out_of_order += 1
print(f"\n[1] duplicate timestamps: {dups}")
print(f"[1] out-of-order timestamps: {out_of_order}")

# 2. Gap analysis (expected 60s steps)
gaps = {}
gap_examples = []
for i in range(1, n):
    d = ts[i] - ts[i-1]
    gaps[d] = gaps.get(d, 0) + 1
    if d != 60 and d > 0 and len(gap_examples) < 15:
        gap_examples.append((
            datetime.fromtimestamp(ts[i-1], tz=timezone.utc).strftime("%Y-%m-%d %a %H:%M"),
            datetime.fromtimestamp(ts[i], tz=timezone.utc).strftime("%Y-%m-%d %a %H:%M"),
            d // 60))
print(f"\n[2] step distribution (top 12 by freq):")
for step, cnt in sorted(gaps.items(), key=lambda x: -x[1])[:12]:
    print(f"    {step:>8}s ({step//60:>6}min): {cnt}")
weekend_like = sum(c for s, c in gaps.items() if s >= 2*24*3600)
print(f"    gaps >= 2 days (weekend-ish): {weekend_like}")
print(f"[2] sample non-60s gaps:")
for a, b, m in gap_examples:
    print(f"    {a} -> {b}  ({m} min)")

# 3. OHLC validity
ohlc_bad = 0
hl_bad = 0
bad_examples = []
for b in bars:
    o, h, l, c = b["o"], b["h"], b["l"], b["c"]
    bad = False
    if h < max(o, c) - 1e-9:
        bad = True
    if l > min(o, c) + 1e-9:
        bad = True
    if h < l:
        hl_bad += 1
        bad = True
    if bad:
        ohlc_bad += 1
        if len(bad_examples) < 5:
            bad_examples.append(b)
print(f"\n[3] OHLC-invalid bars (H<max(O,C) or L>min(O,C) or H<L): {ohlc_bad}")
print(f"[3] H<L bars: {hl_bad}")
for b in bad_examples:
    print(f"    {b}")

# 4. Volume anomalies
zero_vol = sum(1 for b in bars if b["v"] == 0)
neg_vol = sum(1 for b in bars if b["v"] < 0)
vols = sorted(b["v"] for b in bars)
def pct(p): return vols[int(p*len(vols))]
print(f"\n[4] zero-volume bars: {zero_vol}")
print(f"[4] negative-volume bars: {neg_vol}")
print(f"[4] volume p1={pct(0.01)} p50={pct(0.50)} p99={pct(0.99)} max={vols[-1]}")

# 5. Price sanity / range
closes = [b["c"] for b in bars]
print(f"\n[5] close range: min={min(closes)} max={max(closes)}")
# Extreme 1m moves (potential bad ticks): |c-o| > $50
big_moves = [b for b in bars if abs(b["c"] - b["o"]) > 50]
print(f"[5] bars with |close-open| > $50: {len(big_moves)}")
# Extreme bar range high-low > $50
big_range = [b for b in bars if (b["h"] - b["l"]) > 50]
print(f"[5] bars with (high-low) > $50: {len(big_range)}")

# 6. Time span
first = datetime.fromtimestamp(ts[0], tz=timezone.utc)
last = datetime.fromtimestamp(ts[-1], tz=timezone.utc)
print(f"\n[6] first bar UTC: {first}")
print(f"[6] last  bar UTC: {last}")
span_days = (ts[-1] - ts[0]) / 86400
print(f"[6] span: {span_days:.1f} days; bars/day if continuous 24/5 ~ {n/span_days:.0f}")

# Slice math for the goal (last 40%, then 70/30 within)
slice_start = int(n * 0.60)
slice_bars = n - slice_start
test_split = slice_start + int(slice_bars * 0.70)
print(f"\n[SLICE] total={n}")
print(f"[SLICE] untouched first 60%: idx 0..{slice_start-1} ({slice_start} bars)")
print(f"[SLICE] working last 40%: idx {slice_start}..{n-1} ({slice_bars} bars)")
print(f"[SLICE]   train (70% of slice): idx {slice_start}..{test_split-1} ({test_split-slice_start} bars)")
print(f"[SLICE]   test  (30% of slice): idx {test_split}..{n-1} ({n-test_split} bars)")
print(f"[SLICE] train start UTC: {datetime.fromtimestamp(ts[slice_start], tz=timezone.utc)}")
print(f"[SLICE] test  start UTC: {datetime.fromtimestamp(ts[test_split], tz=timezone.utc)}")
print("\nNOTE: data has NO bid/ask spread field (OHLCV only) — spread realism check not possible on this file.")
