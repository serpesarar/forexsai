"""Write a FRESH prediction_replay_corrections batch using current rules/config.

The production run_replay_batch path is currently broken (the custom Supabase
wrapper's .upsert() returns 400). This driver reuses the SAME replay engine
(services.signal_replay_1m.replay_signal_row) but persists via direct httpx
upsert with Prefer: resolution=merge-duplicates (which works), under ONE fresh
batch_id. Non-destructive: existing batches are left intact; panels read the
latest batch per prediction_id via signal_analytics.attach_corrections.
"""
import os, sys, asyncio, json, uuid, time
import httpx

for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))
from services.signal_replay_1m import replay_signal_row, _load_all_1m_bars_sync  # noqa: E402

URL = os.environ["SUPABASE_URL"]
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
SINCE = "2026-02-10T00:00:00Z"
COLS = ("id,symbol,model_type,ml_direction,ml_entry_price,timeframe,status,"
        "resolution_reason,exit_price,highest_profit_pips,lowest_drawdown_pips,created_at")
BATCH_ID = str(uuid.uuid4())


def fetch_all():
    rows, off, page = [], 0, 1000
    with httpx.Client(timeout=60) as c:
        while True:
            h = dict(H); h["Range"] = f"{off}-{off+page-1}"
            r = c.get(f"{URL}/rest/v1/prediction_logs?select={COLS}"
                      f"&created_at=gte.{SINCE}&status=neq.active&order=created_at.asc",
                      headers=h)
            if r.status_code not in (200, 206):
                raise RuntimeError(f"fetch failed {r.status_code}: {r.text[:300]}")
            b = r.json()
            if not isinstance(b, list):
                raise RuntimeError(f"unexpected response (not a list): {str(b)[:300]}")
            if not b:
                break
            rows.extend([x for x in b if isinstance(x, dict)])
            if len(b) < page:
                break
            off += page
    return rows


async def main():
    t0 = time.time()
    rows = fetch_all()
    print(f"fetched {len(rows)} signals since {SINCE}  batch_id={BATCH_ID}", flush=True)
    symbols = sorted({r.get("symbol") for r in rows if r.get("symbol")})
    bars = {s: _load_all_1m_bars_sync(s) for s in symbols}
    tks = {s: [b["ts"] for b in bars[s]] for s in symbols}
    for s in symbols:
        print(f"  {s}: {len(bars[s])} 1m bars", flush=True)

    sem = asyncio.Semaphore(12)
    results = []

    async def one(sig):
        async with sem:
            sym = sig.get("symbol") or ""
            try:
                return await replay_signal_row(sig, symbol_bars=bars.get(sym, []),
                                               ts_keys=tks.get(sym, []), batch_id=BATCH_ID)
            except Exception as e:
                return {"prediction_id": sig.get("id"), "symbol": sym,
                        "model_type": sig.get("model_type"), "direction": sig.get("ml_direction"),
                        "timeframe": sig.get("timeframe"), "entry_price": sig.get("ml_entry_price"),
                        "signal_created_at": sig.get("created_at"), "replay_status": "exception",
                        "replay_notes": str(e)[:200], "rule_version": "v2_2026-05-30",
                        "replay_batch_id": BATCH_ID}

    results = await asyncio.gather(*[one(s) for s in rows])

    # normalize records to a uniform key set (PostgREST PGRST102: all object
    # keys must match within a bulk insert) — union all keys, fill missing None
    norm = []
    by_status = {}
    for r in results:
        rec = {k: v for k, v in r.items() if not k.startswith("_")}
        rec.setdefault("rule_version", "v2_2026-05-30")
        norm.append(rec)
        cs = rec.get("corrected_status")
        if cs:
            by_status[cs] = by_status.get(cs, 0) + 1
    all_keys = set()
    for rec in norm:
        all_keys.update(rec.keys())
    for rec in norm:
        for k in all_keys:
            rec.setdefault(k, None)

    # persist via direct httpx upsert (merge-duplicates)
    hh = dict(H); hh["Content-Type"] = "application/json"
    hh["Prefer"] = "resolution=merge-duplicates,return=minimal"
    persisted = 0
    with httpx.Client(timeout=120) as c:
        CH = 200
        for i in range(0, len(norm), CH):
            chunk = norm[i:i+CH]
            resp = c.post(f"{URL}/rest/v1/prediction_replay_corrections"
                          f"?on_conflict=prediction_id,replay_batch_id",
                          headers=hh, content=json.dumps(chunk, default=str))
            if resp.status_code in (200, 201, 204):
                persisted += len(chunk)
            else:
                print("WRITE FAIL", resp.status_code, resp.text[:200], flush=True)
    summary = {"batch_id": BATCH_ID, "scanned": len(rows), "persisted": persisted,
               "by_corrected_status": by_status, "secs": round(time.time()-t0, 1)}
    json.dump(summary, open("signal_performance_research/fresh_corrections_summary.json", "w"),
              indent=2)
    print("DONE", summary, flush=True)


asyncio.run(main())
