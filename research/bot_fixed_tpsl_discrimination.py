"""
RESEARCH ONLY — indicator discrimination on the BOT'S FIXED tp/sl outcomes.

This is the corrected version of indicator_discrimination.py: instead of
labeling WIN/LOSS by the signal's own multi-target lifecycle resolution, it
RE-RESOLVES every bot-scope signal against the bot's FIXED tp/sl via 1m replay,
THEN computes per-indicator AUC (WIN vs LOSS). Answers "which indicator values
make the BOT'S real fixed-tp/sl trades win" — the right target for tuning the bot.

Per-LOG discrimination (every signal). Duplicate logging inflates absolute WR
but does not bias the WIN-vs-LOSS indicator contrast.
"""
import sys, bisect
from datetime import datetime, timedelta, timezone
from collections import defaultdict

sys.path.insert(0, "backend")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client

PAGE = 1000
SINCE = "2026-04-25T00:00:00+00:00"
MAX_HOLD_MIN = 1440
MIN_PER_GROUP = 40
SKIP = {"session", "source", "strategy", "target_type", "news_count",
        "regime_label", "dow", "hour_utc", "symbol", "model_type", "snapshot_v",
        "meta_snapshot_interval_seconds"}

SCOPES = {
    "NDX.INDX:BUY":     {"tp": 80.0,  "sl": 110.0, "is_pct": False},
    "GDAXI.INDX:SELL":  {"tp": 67.0,  "sl": 119.0, "is_pct": False},
    "USOIL.FOREX:SELL": {"tp": 1.04,  "sl": 1.49,  "is_pct": True},
}
MODELS = ["pulse1", "pulse2", "pulse3"]


def parse_iso(v):
    if not v: return None
    if isinstance(v, datetime): return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try: return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception: return None


def fnum(v):
    try:
        x = float(v); return None if x != x else x
    except (TypeError, ValueError): return None


def load_bars(c, symbol):
    out = []; off = 0
    while True:
        r = (c.table("candle_cache").select("candle_time,open,high,low,close")
             .eq("symbol", symbol).eq("timeframe", "1m")
             .order("candle_time", desc=False).range(off, off+PAGE-1).execute())
        page = r.get("data") if isinstance(r, dict) else getattr(r, "data", [])
        if not page: break
        for row in page:
            ts = parse_iso(row.get("candle_time"))
            if ts is None: continue
            out.append((ts, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])))
        if len(page) < PAGE: break
        off += PAGE
    out.sort(key=lambda x: x[0]); return out


def load_signals(c, symbol, direction):
    out = []; off = 0
    while True:
        r = (c.table("prediction_logs").select("created_at,factors")
             .eq("symbol", symbol).eq("ml_direction", direction).in_("model_type", MODELS)
             .gte("created_at", SINCE).order("created_at", desc=False)
             .range(off, off+PAGE-1).execute())
        page = r.get("data") if isinstance(r, dict) else getattr(r, "data", [])
        if not page: break
        out.extend(page)
        if len(page) < PAGE: break
        off += PAGE
    return out


def replay(entry_ts, entry, direction, tp, sl, is_pct, bars, tsk):
    if is_pct:
        tp_px = entry*(1+tp/100) if direction == "BUY" else entry*(1-tp/100)
        sl_px = entry*(1-sl/100) if direction == "BUY" else entry*(1+sl/100)
    else:
        tp_px = entry+tp if direction == "BUY" else entry-tp
        sl_px = entry-sl if direction == "BUY" else entry+sl
    end = entry_ts + timedelta(minutes=MAX_HOLD_MIN)
    lo = bisect.bisect_left(tsk, entry_ts)
    for i in range(lo, len(bars)):
        ts, o, h, l, cl = bars[i]
        if ts > end: break
        if direction == "BUY": hit_tp = h >= tp_px; hit_sl = l <= sl_px
        else: hit_tp = l <= tp_px; hit_sl = h >= sl_px
        if hit_tp and hit_sl:
            bull = cl >= o
            tp_first = (not bull) if direction == "BUY" else bull
            return "WIN" if tp_first else "LOSS"
        if hit_tp: return "WIN"
        if hit_sl: return "LOSS"
    return None


def auc(w, l):
    n, m = len(w), len(l)
    if n == 0 or m == 0: return None
    allv = sorted([(v, 0) for v in w] + [(v, 1) for v in l])
    ranks = [0.0]*len(allv); i = 0
    while i < len(allv):
        j = i
        while j+1 < len(allv) and allv[j+1][0] == allv[i][0]: j += 1
        avg = (i+j)/2.0+1.0
        for k in range(i, j+1): ranks[k] = avg
        i = j+1
    rs = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    return (rs - n*(n+1)/2.0)/(n*m)


def median(xs):
    s = sorted(xs); n = len(s)
    return None if n == 0 else (s[n//2] if n % 2 else (s[n//2-1]+s[n//2])/2.0)

def pctl(xs, p):
    s = sorted(xs)
    return None if not s else s[max(0, min(len(s)-1, int(round(p*(len(s)-1)))))]


def main():
    c = get_supabase_client()
    for scope, lv in SCOPES.items():
        symbol, direction = scope.split(":")
        bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
        sigs = load_signals(c, symbol, direction)
        win = defaultdict(list); loss = defaultdict(list); nw = nl = 0
        for s in sigs:
            cat = parse_iso(s.get("created_at"))
            if cat is None: continue
            lo = bisect.bisect_left(tsk, cat)
            if lo >= len(bars): continue
            entry = bars[lo][1]
            if entry <= 0: continue
            res = replay(cat, entry, direction, lv["tp"], lv["sl"], lv["is_pct"], bars, tsk)
            if res is None: continue
            f = s.get("factors") or {}
            tgt = win if res == "WIN" else loss
            if res == "WIN": nw += 1
            else: nl += 1
            for k, v in f.items():
                if k in SKIP: continue
                x = fnum(v)
                if x is not None: tgt[k].append(x)
        tot = nw+nl
        print(f"\n{'='*72}\n{scope}  (FIXED tp{lv['tp']}/sl{lv['sl']})  "
              f"WIN={nw} LOSS={nl} WR={(nw/tot*100 if tot else 0):.1f}%")
        scored = []
        for k in set(win) | set(loss):
            w = win.get(k, []); l = loss.get(k, [])
            if len(w) < MIN_PER_GROUP or len(l) < MIN_PER_GROUP: continue
            a = auc(w, l)
            if a is None: continue
            scored.append((abs(a-0.5), a, k, median(w), median(l), pctl(w, .25), pctl(w, .75)))
        scored.sort(reverse=True)
        print(f"  {'indicator':24s} {'AUC':>5s} {'WIN_med':>10s} {'LOSS_med':>10s}  win 25-75%")
        for st, a, k, wm, lm, q1, q3 in scored[:14]:
            arr = "WIN higher" if a > 0.5 else "WIN lower"
            star = "***" if st >= .15 else ("**" if st >= .10 else ("*" if st >= .06 else ""))
            print(f"  {k:24s} {a:5.2f} {wm:10.3f} {lm:10.3f}  [{q1:.2f}..{q3:.2f}] {arr} {star}")


if __name__ == "__main__":
    main()
