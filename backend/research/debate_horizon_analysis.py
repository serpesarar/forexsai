"""Agent tartışma sistemi çok-ufuklu analiz.

bias_test_log koşularını 5m mumlarla +10/20/30/60/120/240 dk ve gün-kapanışı
ufuklarında yeniden notlar; sembol/saat/ajan/confidence kırılımları üretir.
"""
import json, os, re, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from collections import defaultdict

ENV = {}
with open("backend/.env") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            ENV.setdefault(k.strip(), v.strip().strip('"').strip("'"))  # first wins

URL = ENV["SUPABASE_URL"].rstrip("/")
KEY = ENV.get("SUPABASE_SERVICE_ROLE_KEY") or ENV["SUPABASE_KEY"]

def rest(path, params, page_size=1000):
    out, offset = [], 0
    while True:
        q = urllib.parse.urlencode({**params, "limit": page_size, "offset": offset})
        req = urllib.request.Request(f"{URL}/rest/v1/{path}?{q}",
            headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
        with urllib.request.urlopen(req) as r:
            batch = json.loads(r.read())
        out.extend(batch)
        if len(batch) < page_size:
            return out
        offset += page_size

LABEL_SYMBOLS = {"xau": "XAUUSD", "dax": "GDAXI.INDX", "usoil": "USOIL.FOREX", "ndx": "NDX.INDX"}

def symbol_for(row):
    raw = row.get("raw_payload") or {}
    if isinstance(raw, dict) and raw.get("symbol"):
        return raw["symbol"]
    label = (row.get("run_label") or "").lower()
    for p, s in LABEL_SYMBOLS.items():
        if label.startswith(p):
            return s
    return "NDX.INDX"

runs = rest("bias_test_log", {"select": "*", "order": "id"})
print(f"runs: {len(runs)}", file=sys.stderr)

# needed (symbol, utc-date) candle windows
need = set()
parsed_runs = []
for r in runs:
    ts = datetime.fromisoformat(r["run_timestamp_utc"].replace("Z", "+00:00"))
    sym = symbol_for(r)
    for d in (0, 1):
        need.add((sym, (ts + timedelta(days=d)).date().isoformat()))
    parsed_runs.append((r, sym, ts))

candles = defaultdict(dict)  # sym -> {ts: (o,h,l,c)}
for sym, day in sorted(need):
    rows = rest("candle_cache", {
        "select": "candle_time,open,high,low,close",
        "symbol": f"eq.{sym}", "timeframe": "eq.5m",
        "candle_time": f"gte.{day}T00:00:00+00:00",
        "and": f"(candle_time.lt.{day}T23:59:59+00:00)",
        "order": "candle_time"})
    for c in rows:
        t = datetime.fromisoformat(c["candle_time"].replace("Z", "+00:00"))
        candles[sym][t] = (float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"]))
print(f"candle days: {len(need)}; symbols: { {s: len(v) for s, v in candles.items()} }", file=sys.stderr)

def close_at(sym, ts):
    """Close of last 5m bar at/before ts (up to 30m lookback)."""
    b = ts.replace(minute=ts.minute - ts.minute % 5, second=0, microsecond=0)
    for i in range(7):
        t = b - timedelta(minutes=5 * i)
        if t in candles[sym]:
            return candles[sym][t][3]
    return None

def excursion(sym, ts, minutes):
    """(max_high, min_low) over (ts, ts+minutes]."""
    b = ts.replace(minute=ts.minute - ts.minute % 5, second=0, microsecond=0)
    hs, ls = [], []
    for i in range(1, minutes // 5 + 1):
        t = b + timedelta(minutes=5 * i)
        if t in candles[sym]:
            _, h, l, _ = candles[sym][t]
            hs.append(h); ls.append(l)
    return (max(hs), min(ls)) if hs else (None, None)

HORIZONS = [10, 20, 30, 60, 120, 240]

STANCE_PAT = [
    (re.compile(r"\b(bearish|bear bias|short bias|downside|sell)\b", re.I), "bearish"),
    (re.compile(r"\b(bullish|bull bias|long bias|upside|buy)\b", re.I), "bullish"),
    (re.compile(r"\b(neutral|mixed|choppy|balanced|range)\b", re.I), "neutral"),
]

def agent_stance(text):
    """First directional keyword in the opening of an agent note."""
    if not isinstance(text, str):
        return None
    head = text[:400]
    best = None
    for pat, lab in STANCE_PAT:
        m = pat.search(head)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), lab)
    return best[1] if best else None

records = []
for r, sym, ts in parsed_runs:
    raw = r.get("raw_payload") or {}
    deb = raw.get("_debate") or {}
    p0 = None
    try:
        p0 = float(raw.get("price_at_decision")) if raw.get("price_at_decision") else None
    except (TypeError, ValueError):
        pass
    if p0 is None:
        p0 = close_at(sym, ts)
    if p0 is None:
        continue
    rec = {
        "id": r["id"], "symbol": sym, "run_label": r["run_label"],
        "ny_date": r["ny_date"], "utc_hour": ts.hour,
        "ts": ts.isoformat(),
        "bias": (r.get("predicted_bias") or "").lower(),
        "confidence": r.get("confidence"),
        "agreement": raw.get("agent_agreement"),
        "winner": raw.get("debate_winner"),
        "trade_mode": r.get("trade_mode"),
        "expected_close": raw.get("expected_close"),
        "p0": p0,
        "day_change_pct": r.get("actual_change_pct"),
        "day_correct": r.get("was_correct"),
        "invalid_if_triggered": r.get("invalid_if_triggered"),
    }
    for m in HORIZONS:
        px = close_at(sym, ts + timedelta(minutes=m))
        rec[f"ret_{m}"] = round((px - p0) / p0 * 100, 4) if px else None
    h60, l60 = excursion(sym, ts, 60)
    rec["mfe60_up"] = round((h60 - p0) / p0 * 100, 4) if h60 else None
    rec["mfe60_dn"] = round((p0 - l60) / p0 * 100, 4) if l60 else None
    # specialist agent stances
    notes = deb.get("context_notes") or {}
    rec["agents"] = {k: agent_stance(v) for k, v in notes.items()} if isinstance(notes, dict) else {}
    records.append(rec)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debate_records.json")
with open(out, "w") as f:
    json.dump(records, f, indent=1)
print(f"wrote {len(records)} records -> {out}", file=sys.stderr)
