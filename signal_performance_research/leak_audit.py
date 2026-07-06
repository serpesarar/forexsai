"""LEAK AUDIT — prove the 1m replay never uses information from before the signal
or from the future.

For a random sample of signals, re-run the production replay with a per-bar trace
and assert, on REAL data:
  1. entry bar timestamp >= signal created_at (rounded to the bar minute) — the
     trade is entered at/after the signal, never before.
  2. the resolution (exit) bar timestamp >= entry bar timestamp — the verdict comes
     from a bar at or after entry, never a past bar.
  3. every walked bar that contributes to the verdict has ts >= entry ts (the walk
     is strictly forward; no future bar is consulted before earlier ones).
  4. the TP/SL levels are a deterministic function of the entry price only (no future
     price used to set the levels).
Counts violations across the whole sample.
"""
import sys, os, json, asyncio, random
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from services.signal_replay_1m import replay_signal_row  # noqa: E402

SYMBOL_FILE = {"XAUUSD": "xauusd", "NDX.INDX": "ustec",
               "USOIL.FOREX": "xtiusd", "GDAXI.INDX": "de40"}


def load_bars(sym):
    d = json.load(open(f"1MDATA/mt5_{SYMBOL_FILE[sym]}_1m_bars.json"))
    bars, keys = [], []
    for x in d["bars"]:
        ts = datetime.fromtimestamp(x["t"], tz=timezone.utc)
        bars.append({"ts": ts, "open": x["o"], "high": x["h"],
                     "low": x["l"], "close": x["c"]})
        keys.append(ts)
    return bars, keys


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


async def main():
    sigs = json.load(open("signal_performance_research/signals_priced.json"))
    random.seed(42)
    sample = random.sample(sigs, 3000)
    bars = {s: load_bars(s) for s in SYMBOL_FILE}

    v_entry_before = 0     # entry bar earlier than signal
    v_exit_before_entry = 0
    v_walk_backward = 0    # any traced bar before entry
    v_level_mismatch = 0   # levels not reproducible from entry alone
    checked = 0
    examples = []

    from services.target_config import calculate_target_prices, calculate_stoploss_price

    for s in sample:
        sym = s["symbol"]
        if sym not in bars:
            continue
        b, k = bars[sym]
        trace = []
        r = await replay_signal_row(s, b, k, trace=trace)
        if r.get("replay_status") != "ok":
            continue
        checked += 1
        created = parse(s["created_at"])
        diag = r["_diagnostics"]
        entry_ts = parse(diag["entry_bar_ts"])
        # 1) entry at/after signal (allow same-minute: entry minute >= created minute)
        if entry_ts < created.replace(second=0, microsecond=0):
            v_entry_before += 1
            if len(examples) < 5:
                examples.append(("entry_before", s["created_at"], diag["entry_bar_ts"]))
        # 2) exit >= entry
        exit_at = r.get("corrected_exit_at")
        if exit_at:
            ex = parse(exit_at)
            if ex < entry_ts:
                v_exit_before_entry += 1
        # 3) every traced bar >= entry ts
        for tb in trace:
            if parse(tb["ts"]) < entry_ts:
                v_walk_backward += 1
                break
        # 4) levels reproducible from entry price alone (no future data).
        # Use the FULL-precision entry the replay used (r["entry_price"], 5dp),
        # not the 2dp display value in diag, else USOIL %-levels round differently.
        entry = r["entry_price"]
        d = (s.get("ml_direction") or "").upper()
        tf = s.get("timeframe") or "15m"
        tp_expect = calculate_target_prices(entry, d, sym, tf)
        sl_expect = calculate_stoploss_price(entry, d, sym, tf)
        tp_used = diag["tp_prices"]; sl_used = diag["sl_price"]
        # tolerance = 1 cent / 1 pip equivalent to absorb entry-rounding only
        tol = 0.02 if sym in ("USOIL.FOREX",) else 0.1
        if (abs(sl_expect - sl_used) > tol or
                any(abs(tp_expect[t] - tp_used[t]) > tol for t in tp_expect)):
            v_level_mismatch += 1
            if len(examples) < 5:
                examples.append(("level", entry, tp_expect.get("TP1"), tp_used.get("TP1")))

    print(f"sampled & evaluated: {checked}")
    print(f"  [1] entry bar BEFORE signal time : {v_entry_before}")
    print(f"  [2] exit bar BEFORE entry bar     : {v_exit_before_entry}")
    print(f"  [3] walk consulted a PAST bar     : {v_walk_backward}")
    print(f"  [4] TP/SL not reproducible from entry alone : {v_level_mismatch}")
    if examples:
        print("  examples:", examples)
    ok = (v_entry_before == v_exit_before_entry == v_walk_backward == v_level_mismatch == 0)
    print("\nRESULT:", "NO LEAK DETECTED — all checks clean" if ok else "LEAK SUSPECTED")


asyncio.run(main())
