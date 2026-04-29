"""
Panel audit — funnel queries against Supabase prediction_logs.
One-off script for the 5-panel audit. Safe to delete after audit.
"""
from __future__ import annotations

import json
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


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_all(params: dict, select: str, page_size: int = 1000, cap: int = 200_000) -> list[dict]:
    rows: list[dict] = []
    client = httpx.Client(timeout=60)
    try:
        offset = 0
        while True:
            headers = {**HEADERS, "Range-Unit": "items", "Range": f"{offset}-{offset+page_size-1}"}
            p = {**params, "select": select, "order": "created_at.desc", "limit": str(page_size), "offset": str(offset)}
            r = client.get(TABLE, headers=headers, params=p)
            r.raise_for_status()
            batch = r.json()
            rows.extend(batch)
            if len(batch) < page_size or len(rows) >= cap:
                break
            offset += page_size
    finally:
        client.close()
    return rows


def q1_model_status() -> None:
    """1. model_type × status totals (all-time)."""
    print("\n=== [Q1] model_type × status totals (all-time) ===")
    rows = fetch_all({}, "model_type,status", page_size=1000)
    print(f"  total rows scanned: {len(rows)}")
    c: Counter[tuple] = Counter()
    for r in rows:
        c[(r.get("model_type") or "NULL", r.get("status") or "NULL")] += 1
    grouped: dict[str, dict[str, int]] = defaultdict(dict)
    for (mt, st), n in c.items():
        grouped[mt][st] = n
    print(f"  {'model_type':22s} {'active':>7} {'completed':>10} {'stopped':>8} {'expired':>8} {'other':>7} {'total':>7}")
    for mt in sorted(grouped):
        st = grouped[mt]
        active = st.get("active", 0)
        completed = st.get("completed", 0)
        stopped = st.get("stopped", 0)
        expired = st.get("expired", 0)
        other = sum(v for k, v in st.items() if k not in {"active", "completed", "stopped", "expired"})
        total = active + completed + stopped + expired + other
        print(f"  {mt:22s} {active:>7d} {completed:>10d} {stopped:>8d} {expired:>8d} {other:>7d} {total:>7d}")
    return grouped


def q2_daily(days: int = 60) -> None:
    print(f"\n=== [Q2] daily signal volume last {days} days ===")
    since = NOW - timedelta(days=days)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "created_at,model_type", page_size=1000)
    by_day: Counter[str] = Counter()
    for r in rows:
        ca = r.get("created_at") or ""
        if isinstance(ca, str) and len(ca) >= 10:
            by_day[ca[:10]] += 1
    zero_days: list[str] = []
    cur = since.date()
    end = NOW.date()
    while cur <= end:
        key = cur.isoformat()
        n = by_day.get(key, 0)
        if n == 0:
            zero_days.append(key)
        cur += timedelta(days=1)
    print(f"  total signals in window: {sum(by_day.values())}")
    print(f"  days with data: {len(by_day)}, days with ZERO: {len(zero_days)}")
    if zero_days:
        print(f"  zero-production days: {', '.join(zero_days[:30])}")
    # last 14 days detail
    print("  last 14 days:")
    for d in sorted(by_day, reverse=True)[:14]:
        print(f"    {d}: {by_day[d]}")


def q3_avg_interval() -> None:
    print("\n=== [Q3] avg interval between signals per model (last 30d, minutes) ===")
    since = NOW - timedelta(days=30)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "created_at,model_type", page_size=1000)
    by_model: dict[str, list[datetime]] = defaultdict(list)
    for r in rows:
        mt = r.get("model_type") or "NULL"
        ca = r.get("created_at")
        if isinstance(ca, str):
            try:
                dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                by_model[mt].append(dt)
            except ValueError:
                pass
    print(f"  {'model_type':22s} {'count':>6} {'avg_min':>10} {'median_min':>12} {'max_gap_min':>13}")
    for mt in sorted(by_model):
        ts = sorted(by_model[mt])
        if len(ts) < 2:
            print(f"  {mt:22s} {len(ts):>6d}  n/a")
            continue
        gaps = [(b - a).total_seconds() / 60.0 for a, b in zip(ts[:-1], ts[1:])]
        gaps.sort()
        avg = sum(gaps) / len(gaps)
        median = gaps[len(gaps) // 2]
        mx = gaps[-1]
        print(f"  {mt:22s} {len(ts):>6d} {avg:>10.1f} {median:>12.1f} {mx:>13.1f}")


def q4_status_pct() -> None:
    print("\n=== [Q4] status distribution (%) — all-time ===")
    rows = fetch_all({}, "status", page_size=1000)
    c: Counter[str] = Counter(r.get("status") or "NULL" for r in rows)
    total = sum(c.values())
    print(f"  total: {total}")
    for st, n in c.most_common():
        print(f"    {st:22s} {n:>7d}   ({n/total*100:5.1f}%)")


def q5_market_closed() -> None:
    print("\n=== [Q5] market_closed_invalid signals ===")
    try:
        client = httpx.Client(timeout=30)
        r = client.get(TABLE, headers=HEADERS, params={"select": "id", "notes": "ilike.*market_closed_invalid*", "limit": "1"})
        r.raise_for_status()
    finally:
        client.close()
    # Grab count via Prefer: count=exact
    hdr = {**HEADERS, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
    for field_filter in [
        {"status": "eq.market_closed_invalid"},
        {"notes": "ilike.*market_closed_invalid*"},
        {"factors->>market_closed_invalid": "eq.true"},
    ]:
        try:
            r = httpx.get(TABLE, headers=hdr, params={**field_filter, "select": "id"}, timeout=30)
            cr = r.headers.get("content-range", "")
            tot = cr.split("/")[-1]
            print(f"  filter {field_filter}: content-range={cr}")
        except Exception as e:
            print(f"  filter {field_filter} error: {e}")


def q6_notes_cooldown_dedup() -> None:
    print("\n=== [Q6] cooldown / dedup / duplicate notes counts ===")
    terms = ["cooldown", "dedup", "duplicate", "fake_signal_timeout", "direction_flip", "regime_blocked", "ath_blocked"]
    for t in terms:
        hdr = {**HEADERS, "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}
        try:
            r = httpx.get(TABLE, headers=hdr, params={"select": "id", "notes": f"ilike.*{t}*"}, timeout=30)
            cr = r.headers.get("content-range", "")
            print(f"  notes ILIKE *{t}*  content-range={cr}")
        except Exception as e:
            print(f"  {t} error: {e}")


def q7_confidence_bucket() -> None:
    print("\n=== [Q7] confidence distribution (last 30d) ===")
    since = NOW - timedelta(days=30)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "ml_confidence,model_type", page_size=1000)
    buckets = {"<40": 0, "40-55": 0, "55-70": 0, "70+": 0, "null": 0}
    by_model_bucket: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        c = r.get("ml_confidence")
        mt = r.get("model_type") or "NULL"
        if c is None:
            buckets["null"] += 1
            by_model_bucket[mt]["null"] += 1
            continue
        try:
            v = float(c)
        except (TypeError, ValueError):
            buckets["null"] += 1
            by_model_bucket[mt]["null"] += 1
            continue
        key = "<40" if v < 40 else "40-55" if v < 55 else "55-70" if v < 70 else "70+"
        buckets[key] += 1
        by_model_bucket[mt][key] += 1
    print("  Overall:")
    for k in ["<40", "40-55", "55-70", "70+", "null"]:
        print(f"    {k:>6s}: {buckets[k]:>6d}")
    print("  Per model:")
    print(f"  {'model_type':22s} {'<40':>6} {'40-55':>6} {'55-70':>6} {'70+':>6} {'null':>6}")
    for mt in sorted(by_model_bucket):
        b = by_model_bucket[mt]
        print(f"  {mt:22s} {b['<40']:>6d} {b['40-55']:>6d} {b['55-70']:>6d} {b['70+']:>6d} {b['null']:>6d}")


def q8_last7_symbol_model() -> None:
    print("\n=== [Q8] last 7 days — symbol × model ===")
    since = NOW - timedelta(days=7)
    rows = fetch_all({"created_at": f"gte.{iso(since)}"}, "symbol,model_type", page_size=1000)
    c: Counter[tuple] = Counter()
    symbols, models = set(), set()
    for r in rows:
        s, m = r.get("symbol") or "NULL", r.get("model_type") or "NULL"
        c[(s, m)] += 1
        symbols.add(s)
        models.add(m)
    models = sorted(models)
    print(f"  total (7d): {sum(c.values())}")
    header = f"  {'symbol':14s}" + "".join(f"{m:>12s}" for m in models) + f"{'TOTAL':>10s}"
    print(header)
    for s in sorted(symbols):
        row = f"  {s:14s}"
        tot = 0
        for m in models:
            n = c.get((s, m), 0)
            tot += n
            row += f"{n:>12d}"
        row += f"{tot:>10d}"
        print(row)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "all"
    try:
        if q in ("all", "1"): q1_model_status()
        if q in ("all", "2"): q2_daily()
        if q in ("all", "3"): q3_avg_interval()
        if q in ("all", "4"): q4_status_pct()
        if q in ("all", "5"): q5_market_closed()
        if q in ("all", "6"): q6_notes_cooldown_dedup()
        if q in ("all", "7"): q7_confidence_bucket()
        if q in ("all", "8"): q8_last7_symbol_model()
    except httpx.HTTPStatusError as e:
        print(f"HTTP ERROR: {e.response.status_code} {e.response.text[:500]}")
        sys.exit(2)
