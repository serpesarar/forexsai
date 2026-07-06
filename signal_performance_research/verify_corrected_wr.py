"""Independent in-memory verification of per-symbol corrected WR.

Replays resolved signals over the window where 1m bars exist (<= 2026-05-21)
using the SAME replay engine the corrections batch uses, then computes
corrected WR = completed / (completed + stopped) per symbol. No DB write —
this is a pure read+replay verification against the validated baselines.
"""
import os, sys, asyncio, json, time
import httpx

for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from services.signal_replay_1m import replay_signal_row, _load_all_1m_bars_sync  # noqa

URL = os.environ["SUPABASE_URL"]
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
SINCE = "2026-02-10T00:00:00Z"
UNTIL = "2026-05-21T00:00:00Z"   # 1m bar coverage ends here
COLS = ("id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,"
        "resolution_reason,exit_price,highest_profit_pips,lowest_drawdown_pips,created_at")
BASELINES = {"USOIL.FOREX": 72.6, "XAUUSD": 71.0, "GDAXI.INDX": 75.6, "NDX.INDX": 71.0}


def fetch_all():
    rows, off, page = [], 0, 1000
    with httpx.Client(timeout=60) as c:
        while True:
            h = dict(H); h["Range"] = f"{off}-{off+page-1}"
            r = c.get(f"{URL}/rest/v1/prediction_logs?select={COLS}"
                      f"&created_at=gte.{SINCE}&created_at=lt.{UNTIL}"
                      f"&status=in.(completed,stopped)&order=created_at.asc", headers=h)
            if r.status_code not in (200, 206):
                raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
            b = r.json()
            if not isinstance(b, list) or not b:
                break
            rows.extend([x for x in b if isinstance(x, dict)])
            if len(b) < page:
                break
            off += page
    return rows


async def main():
    t0 = time.time()
    rows = fetch_all()
    print(f"fetched {len(rows)} resolved signals in [{SINCE} .. {UNTIL})", flush=True)
    symbols = sorted({r.get("symbol") for r in rows if r.get("symbol")})
    bars = {s: _load_all_1m_bars_sync(s) for s in symbols}
    tks = {s: [b["ts"] for b in bars[s]] for s in symbols}

    sem = asyncio.Semaphore(12)

    async def one(sig):
        async with sem:
            sym = sig.get("symbol") or ""
            try:
                return await replay_signal_row(sig, symbol_bars=bars.get(sym, []),
                                               ts_keys=tks.get(sym, []))
            except Exception as e:
                return {"symbol": sym, "replay_status": "exception", "replay_notes": str(e)[:120]}

    results = await asyncio.gather(*[one(s) for s in rows])

    # per-symbol corrected WR (only replay_status ok + resolved)
    agg = {}
    for r in results:
        if r.get("replay_status") != "ok":
            continue
        cs = r.get("corrected_status")
        if cs not in ("completed", "stopped"):
            continue
        sym = r.get("symbol")
        a = agg.setdefault(sym, {"completed": 0, "stopped": 0})
        a[cs] += 1

    print(f"\n{'symbol':<14}{'completed':>10}{'stopped':>9}{'corrWR%':>9}{'baseline':>10}{'diff':>7}")
    out = {}
    for sym in sorted(agg):
        a = agg[sym]
        n = a["completed"] + a["stopped"]
        wr = 100.0 * a["completed"] / n if n else 0.0
        base = BASELINES.get(sym)
        diff = (wr - base) if base is not None else None
        out[sym] = {"completed": a["completed"], "stopped": a["stopped"], "resolved": n,
                    "corrected_wr": round(wr, 1), "baseline": base,
                    "diff": round(diff, 1) if diff is not None else None}
        bs = f"{base:.1f}" if base is not None else "-"
        ds = f"{diff:+.1f}" if diff is not None else "-"
        print(f"{sym:<14}{a['completed']:>10}{a['stopped']:>9}{wr:>8.1f}%{bs:>10}{ds:>7}", flush=True)

    json.dump({"window": [SINCE, UNTIL], "secs": round(time.time()-t0, 1), "per_symbol": out},
              open("signal_performance_research/verify_corrected_wr.json", "w"), indent=2)
    print(f"\nsecs={round(time.time()-t0,1)}", flush=True)


asyncio.run(main())
