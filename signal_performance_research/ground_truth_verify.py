"""Independent 1m ground-truth verification of production signals.

For each resolved prediction_logs signal (status completed=WIN / stopped=LOSS,
declared ml_entry/target/stop_price), walk the REAL 1m bars from the signal's
timestamp forward and check whether the declared TP or SL was touched first.

Method (leak-free, pessimistic):
  - entry bar = first 1m bar with t >= created_at
  - BUY  win = high >= TP ; loss = low  <= SL
  - SELL win = low  <= TP ; loss = high >= SL
  - if a single 1m bar touches BOTH levels -> count as LOSS (pessimistic SL-first)
  - walk up to a realistic max-hold by timeframe; no touch -> NEUTRAL (timeout)
  - no spread added: this is the cleanest "is the reported WR inflated" test.
    Production evaluates on 5m candles (coarser) and counts in-bar TP/SL ambiguity
    as wins; a finer 1m + pessimistic walk reveals the honest outcome.

Output: corrected GROUND TRUTH WR per model and per symbol vs production-reported.
"""
import json
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone

SYMBOL_FILE = {
    "XAUUSD": "xauusd",
    "NDX.INDX": "ustec",
    "USOIL.FOREX": "xtiusd",
    "GDAXI.INDX": "de40",
}
MAX_HOLD_MIN = {  # minutes by timeframe
    "5m": 720, "15m": 1440, "30m": 2880,
    "1h": 4320, "4h": 10080, "1d": 10080,
}
DEFAULT_HOLD = 1440


def load_bars(sym):
    d = json.load(open(f"1MDATA/mt5_{SYMBOL_FILE[sym]}_1m_bars.json"))
    b = d["bars"]
    return ([x["t"] for x in b], [x["o"] for x in b],
            [x["h"] for x in b], [x["l"] for x in b], [x["c"] for x in b])


def to_unix(ts):
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00"))
               .astimezone(timezone.utc).timestamp())


def replay(t, h, l, ts_unix, direction, tp, sl, hold_min):
    """Return 1 win / 0 loss / -1 neutral(timeout/no-data)."""
    i = bisect_left(t, ts_unix)
    if i >= len(t):
        return -1
    end_ts = t[i] + hold_min * 60
    while i < len(t) and t[i] <= end_ts:
        hi, lo = h[i], l[i]
        if direction == "BUY":
            hit_tp = hi >= tp
            hit_sl = lo <= sl
        else:  # SELL
            hit_tp = lo <= tp
            hit_sl = hi >= sl
        if hit_tp and hit_sl:
            return 0  # pessimistic: both in one bar -> loss
        if hit_sl:
            return 0
        if hit_tp:
            return 1
        i += 1
    return -1  # timeout, never touched either


sigs = json.load(open("signal_performance_research/signals_priced.json"))
print(f"loaded {len(sigs)} priced resolved signals (<= 2026-05-21)")

bars = {s: load_bars(s) for s in SYMBOL_FILE}

# aggregation: model / symbol / (model,symbol)
agg_model = defaultdict(lambda: [0, 0, 0])   # gt_win, gt_loss, gt_neutral
agg_symbol = defaultdict(lambda: [0, 0, 0])
prod_model = defaultdict(lambda: [0, 0])      # prod_win(completed), prod_total_resolved
prod_symbol = defaultdict(lambda: [0, 0])
skipped = defaultdict(int)
# confusion: production said WIN but ground-truth says LOSS, etc.
conf = defaultdict(int)  # (prod, gt) -> count


def valid_geom(direction, entry, tp, sl):
    if not (entry and tp and sl):
        return False
    if direction == "BUY":
        return tp > entry > sl
    if direction == "SELL":
        return tp < entry < sl
    return False


for s in sigs:
    sym = s["symbol"]
    if sym not in bars:
        skipped["unknown_symbol"] += 1
        continue
    d = s["ml_direction"]
    if d not in ("BUY", "SELL"):
        skipped["non_directional"] += 1
        continue
    entry = s.get("ml_entry_price")
    tp = s.get("ml_target_price")
    sl = s.get("ml_stop_price")
    if not valid_geom(d, entry, tp, sl):
        skipped["bad_geometry"] += 1
        continue
    mt = s["model_type"]
    prod_win = 1 if s["status"] == "completed" else 0
    prod_model[mt][0] += prod_win; prod_model[mt][1] += 1
    prod_symbol[sym][0] += prod_win; prod_symbol[sym][1] += 1

    t, o, h, l, c = bars[sym]
    hold = MAX_HOLD_MIN.get(s.get("timeframe") or "", DEFAULT_HOLD)
    gt = replay(t, h, l, to_unix(s["created_at"]), d, tp, sl, hold)
    idx = 0 if gt == 1 else (1 if gt == 0 else 2)
    agg_model[mt][idx] += 1
    agg_symbol[sym][idx] += 1
    conf[("WIN" if prod_win else "LOSS", {1: "WIN", 0: "LOSS", -1: "NEUTRAL"}[gt])] += 1

print("skipped:", dict(skipped))


def line(name, gt, prod):
    gw, gl, gn = gt
    resolved = gw + gl
    gt_wr = gw / resolved if resolved else 0
    pw, pn = prod
    prod_wr = pw / pn if pn else 0
    # WR if neutrals counted as losses (conservative)
    gt_wr_all = gw / (gw + gl + gn) if (gw + gl + gn) else 0
    print(f"  {name:16s} prodWR {prod_wr:5.1%} (N={pn:6d}) | "
          f"GT-WR {gt_wr:5.1%} (res={resolved:6d}) | "
          f"GT-WR(neut=loss) {gt_wr_all:5.1%} | neutral={gn:5d} | "
          f"Δ {gt_wr-prod_wr:+5.1%}")


print("\n=== GROUND TRUTH vs PRODUCTION — by SYMBOL ===")
for sym in sorted(agg_symbol, key=lambda x: -prod_symbol[x][1]):
    line(sym, agg_symbol[sym], prod_symbol[sym])

print("\n=== GROUND TRUTH vs PRODUCTION — by MODEL ===")
for mt in sorted(agg_model, key=lambda x: -prod_model[x][1]):
    line(mt, agg_model[mt], prod_model[mt])

print("\n=== CONFUSION (production label -> ground-truth) ===")
tot = sum(conf.values())
for k in sorted(conf, key=lambda x: -conf[x]):
    print(f"  prod={k[0]:5s} -> GT={k[1]:8s}  {conf[k]:7d}  ({conf[k]/tot:5.1%})")

# headline: of production WINs, how many does GT confirm?
pw_total = conf[("WIN", "WIN")] + conf[("WIN", "LOSS")] + conf[("WIN", "NEUTRAL")]
if pw_total:
    print(f"\nOf {pw_total} production WINS: GT confirms {conf[('WIN','WIN')]} "
          f"({conf[('WIN','WIN')]/pw_total:.1%}), GT-loss {conf[('WIN','LOSS')]} "
          f"({conf[('WIN','LOSS')]/pw_total:.1%}), GT-neutral/timeout "
          f"{conf[('WIN','NEUTRAL')]} ({conf[('WIN','NEUTRAL')]/pw_total:.1%})")
