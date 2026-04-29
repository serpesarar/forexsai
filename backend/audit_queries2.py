"""Panel audit — part 2. Uses correct schema (resolution_reason, factors->>)."""
from __future__ import annotations

import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
TABLE = f"{URL}/rest/v1/prediction_logs"

NOW = datetime.now(timezone.utc)


def iso(dt): return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_all(params, select, page_size=1000, cap=200_000):
    rows = []
    with httpx.Client(timeout=60) as client:
        offset = 0
        while True:
            p = {**params, "select": select, "order": "created_at.desc", "limit": str(page_size), "offset": str(offset)}
            r = client.get(TABLE, headers=HEADERS, params=p)
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < page_size or len(rows) >= cap:
                break
            offset += page_size
    return rows


def count_exact(params):
    hdr = {**HEADERS, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
    r = httpx.get(TABLE, headers=hdr, params={**params, "select": "id"}, timeout=30)
    cr = r.headers.get("content-range", "")
    # "0-0/123456" -> 123456
    try:
        return int(cr.split("/")[-1])
    except Exception:
        return -1


def q5_resolution_reasons():
    print("\n=== [Q5] resolution_reason distribution (all-time) ===")
    rows = fetch_all({}, "resolution_reason,status,model_type", page_size=1000)
    c = Counter((r.get("resolution_reason") or "NULL", r.get("status") or "NULL") for r in rows)
    # Summarize
    by_reason = Counter()
    for (rsn, _st), n in c.items():
        by_reason[rsn] += n
    print(f"  total: {sum(by_reason.values())}")
    for rsn, n in by_reason.most_common():
        print(f"    {rsn:30s} {n:>7d}")

    print("\n  market_closed_invalid by model_type:")
    c2 = Counter()
    for r in rows:
        if (r.get("resolution_reason") or "").strip() == "market_closed_invalid":
            c2[r.get("model_type") or "NULL"] += 1
    for mt, n in c2.most_common():
        print(f"    {mt:22s} {n:>7d}")


def q6_factor_tags():
    print("\n=== [Q6] signal-rejection hints (factors JSON tags) ===")
    # We don't log cooldown/dedup drops in DB at all (they are `return None` before insert).
    # Still check what's inside factors for signals that DID get logged.
    for tag in ["correlation_warning", "close_reason", "parallel_active_allowed", "signal_reasoning"]:
        n = count_exact({"factors": f"ilike.*{tag}*"})
        print(f"  factors ILIKE *{tag}* : {n}")

    print("\n  resolution_reason ilike checks:")
    for tag in ["direction_flip", "tp4_hit", "sl_hit", "tp1_3_hit_then_sl", "window_resolve_negative", "window_resolve_positive", "all_targets_hit", "market_closed_invalid"]:
        n = count_exact({"resolution_reason": f"eq.{tag}"})
        print(f"    resolution_reason=={tag:30s} {n:>7d}")


def q7_confidence_bucket():
    print("\n=== [Q7] confidence distribution (last 30d) ===")
    since = NOW - timedelta(days=30)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "ml_confidence,model_type,status", page_size=1000)
    buckets = {"<40": 0, "40-55": 0, "55-70": 0, "70+": 0, "null": 0}
    by_model_bucket = defaultdict(Counter)
    by_model_status = defaultdict(lambda: defaultdict(Counter))
    for r in rows:
        c = r.get("ml_confidence")
        mt = r.get("model_type") or "NULL"
        st = r.get("status") or "NULL"
        if c is None:
            buckets["null"] += 1
            by_model_bucket[mt]["null"] += 1
            by_model_status[mt][st]["null"] += 1
            continue
        try:
            v = float(c)
        except Exception:
            buckets["null"] += 1
            by_model_bucket[mt]["null"] += 1
            by_model_status[mt][st]["null"] += 1
            continue
        key = "<40" if v < 40 else "40-55" if v < 55 else "55-70" if v < 70 else "70+"
        buckets[key] += 1
        by_model_bucket[mt][key] += 1
        by_model_status[mt][st][key] += 1
    print("  Overall (30d):")
    for k in ["<40", "40-55", "55-70", "70+", "null"]:
        print(f"    {k:>6s}: {buckets[k]:>6d}")
    print(f"  {'model_type':22s} {'<40':>6} {'40-55':>6} {'55-70':>6} {'70+':>6} {'null':>6}")
    for mt in sorted(by_model_bucket):
        b = by_model_bucket[mt]
        print(f"  {mt:22s} {b['<40']:>6d} {b['40-55']:>6d} {b['55-70']:>6d} {b['70+']:>6d} {b['null']:>6d}")


def q8_last7():
    print("\n=== [Q8] last 7d — symbol × model ===")
    since = NOW - timedelta(days=7)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "symbol,model_type,status", page_size=1000)
    c = Counter()
    c_res = Counter()
    symbols, models = set(), set()
    for r in rows:
        s, m, st = r.get("symbol") or "NULL", r.get("model_type") or "NULL", r.get("status") or "NULL"
        c[(s, m)] += 1
        if st in {"completed", "stopped"}:
            c_res[(s, m)] += 1
        symbols.add(s)
        models.add(m)
    models = sorted(models)
    print(f"  total (7d): {sum(c.values())}")
    print(f"  {'symbol':14s}" + "".join(f"{m[:10]:>11s}" for m in models))
    for s in sorted(symbols):
        row = f"  {s:14s}"
        for m in models:
            row += f"{c.get((s,m),0):>11d}"
        print(row)
    print("\n  RESOLVED only (completed+stopped):")
    for s in sorted(symbols):
        row = f"  {s:14s}"
        for m in models:
            row += f"{c_res.get((s,m),0):>11d}"
        print(row)


def q9_expired_by_model():
    print("\n=== [Q9] Expired ratio per model (all-time) ===")
    rows = fetch_all({}, "model_type,status", page_size=1000)
    per_model_status = defaultdict(Counter)
    for r in rows:
        per_model_status[r.get("model_type") or "NULL"][r.get("status") or "NULL"] += 1
    print(f"  {'model_type':22s} {'total':>6} {'expired%':>9} {'resolved%':>10} {'active':>7}")
    for mt in sorted(per_model_status):
        stc = per_model_status[mt]
        total = sum(stc.values())
        expired = stc.get("expired", 0)
        resolved = stc.get("completed", 0) + stc.get("stopped", 0)
        active = stc.get("active", 0)
        print(f"  {mt:22s} {total:>6d} {expired/total*100:>8.1f}% {resolved/total*100:>9.1f}% {active:>7d}")


def q10_smc_cadence_collapse():
    """Estimate SMC cadence collapse impact — signals with factors.cadence or consecutive timeframe."""
    print("\n=== [Q10] SMC signals per timeframe × status (last 30d) ===")
    since = NOW - timedelta(days=30)
    rows = fetch_all({"model_type": "eq.smc", "created_at": f"gte.{iso(since)}"}, "timeframe,status,symbol", page_size=1000)
    by_tf_status = defaultdict(Counter)
    by_sym_tf = Counter()
    for r in rows:
        by_tf_status[r.get("timeframe") or "NULL"][r.get("status") or "NULL"] += 1
        by_sym_tf[(r.get("symbol"), r.get("timeframe"))] += 1
    print(f"  {'tf':8s} {'total':>6} {'active':>7} {'completed':>10} {'stopped':>8} {'expired':>8} {'expired%':>9}")
    for tf in sorted(by_tf_status):
        stc = by_tf_status[tf]
        t = sum(stc.values())
        exp = stc.get("expired", 0)
        print(f"  {tf:8s} {t:>6d} {stc.get('active',0):>7d} {stc.get('completed',0):>10d} {stc.get('stopped',0):>8d} {exp:>8d} {exp/t*100 if t else 0:>8.1f}%")
    print("  symbol x timeframe:")
    for (s, tf), n in sorted(by_sym_tf.items()):
        print(f"    {s or 'NULL':14s} {tf or 'NULL':8s} {n:>5d}")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "all"
    if q in ("all", "5"): q5_resolution_reasons()
    if q in ("all", "6"): q6_factor_tags()
    if q in ("all", "7"): q7_confidence_bucket()
    if q in ("all", "8"): q8_last7()
    if q in ("all", "9"): q9_expired_by_model()
    if q in ("all", "10"): q10_smc_cadence_collapse()
