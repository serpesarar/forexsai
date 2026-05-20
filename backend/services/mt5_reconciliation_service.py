"""
MT5 Reconciliation Service
==========================

Ingests MT5 deal exports (JSON from the mt5_export_deals.py script, or
plain CSV/HTML from MT5's "Save as Report" GUI) and stores them as
ground-truth in `mt5_trades`. Then matches each deal to the closest
candidate row in `prediction_logs` to expose the gap between what our
lifecycle reported and what the broker actually filled.
"""
from __future__ import annotations

import csv
import io
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Map MT5 broker symbols → our canonical names. Brokers vary; extend as needed.
SYMBOL_NORMALIZATION = {
    "XAUUSD": "XAUUSD",
    "XAUUSDm": "XAUUSD",
    "XAUUSD.": "XAUUSD",
    "GOLD": "XAUUSD",
    "USTEC": "NDX.INDX",
    "NAS100": "NDX.INDX",
    "NASUSD": "NDX.INDX",
    "NDX": "NDX.INDX",
    "NDX.INDX": "NDX.INDX",
    "DE40": "GDAXI.INDX",
    "GER40": "GDAXI.INDX",
    "DAX40": "GDAXI.INDX",
    "GDAXI": "GDAXI.INDX",
    "GDAXI.INDX": "GDAXI.INDX",
    "XTIUSD": "USOIL.FOREX",
    "USOIL": "USOIL.FOREX",
    "WTI": "USOIL.FOREX",
    "WTICOUSD": "USOIL.FOREX",
    "CL.F": "USOIL.FOREX",
    "USOIL.FOREX": "USOIL.FOREX",
}


def normalize_symbol(s: str) -> str:
    if not s:
        return s
    s = s.strip().upper()
    return SYMBOL_NORMALIZATION.get(s, s)


def parse_json_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse the JSON produced by mt5_export_deals.py."""
    deals = payload.get("deals") or []
    meta = {
        "account_login": payload.get("account_login"),
        "broker": payload.get("broker"),
        "currency": payload.get("currency"),
        "balance": payload.get("balance"),
        "equity": payload.get("equity"),
        "exported_at": payload.get("exported_at"),
    }
    rows = []
    for d in deals:
        rows.append({
            "ticket": int(d.get("ticket") or 0),
            "order_id": int(d.get("order") or 0) or None,
            "position_id": int(d.get("position_id") or 0) or None,
            "symbol": d.get("symbol") or "",
            "normalized_symbol": normalize_symbol(d.get("symbol") or ""),
            "direction": (d.get("type") or "").upper(),
            "entry_type": d.get("entry") or "in",
            "volume": float(d.get("volume") or 0),
            "price": float(d.get("price") or 0),
            "profit": float(d.get("profit") or 0),
            "commission": float(d.get("commission") or 0),
            "swap": float(d.get("swap") or 0),
            "deal_time": d.get("time"),
            "comment": (d.get("comment") or "")[:500],
            "account_login": meta.get("account_login"),
            "broker": meta.get("broker"),
            "currency": meta.get("currency"),
        })
    return meta, rows


def parse_mt5_csv(content: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse MT5 'Save as Report — CSV' output.

    MT5 CSV is tab-separated with headers like:
      Time,Deal,Symbol,Type,Direction,Volume,Price,Order,Commission,Fee,Swap,Profit,Balance,Comment
    Different broker MT5 builds vary; we use header-keyed access.
    """
    rows = []
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    if not reader.fieldnames:
        # Try comma fallback
        reader = csv.DictReader(io.StringIO(content), delimiter=",")

    for row in reader:
        # Best-effort field detection
        symbol_raw = (row.get("Symbol") or row.get("symbol") or "").strip()
        if not symbol_raw:
            continue
        type_raw = (row.get("Type") or row.get("Direction") or "").strip().lower()
        direction = "BUY" if "buy" in type_raw else "SELL" if "sell" in type_raw else ""
        if direction == "":
            continue
        entry_raw = (row.get("Direction") or row.get("Entry") or "in").strip().lower()
        entry_type = "in" if entry_raw in ("in", "buy", "sell", "") else "out"

        time_raw = (row.get("Time") or row.get("Open Time") or row.get("Close Time") or "").strip()
        if not time_raw:
            continue
        # MT5 time format usually "2026.05.20 16:30:00"
        try:
            t = datetime.strptime(time_raw, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                t = datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
            except Exception:
                continue

        def _f(key: str) -> float:
            v = row.get(key, "")
            if v is None:
                return 0.0
            v = str(v).replace(" ", "").replace(",", "")
            try:
                return float(v)
            except ValueError:
                return 0.0

        rows.append({
            "ticket": int(_f("Deal") or _f("Ticket") or _f("ID")),
            "order_id": int(_f("Order")) or None,
            "position_id": int(_f("Position")) or None,
            "symbol": symbol_raw,
            "normalized_symbol": normalize_symbol(symbol_raw),
            "direction": direction,
            "entry_type": entry_type,
            "volume": _f("Volume"),
            "price": _f("Price"),
            "profit": _f("Profit"),
            "commission": _f("Commission") or _f("Fee"),
            "swap": _f("Swap"),
            "deal_time": t.isoformat(),
            "comment": (row.get("Comment") or "")[:500],
        })
    return {"source": "mt5_csv"}, rows


def parse_upload(content_bytes: bytes, filename: str = "") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Dispatch parser based on file extension/content."""
    try:
        text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = content_bytes.decode("utf-16", errors="ignore")  # MT5 HTML sometimes UTF-16

    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        # JSON
        payload = json.loads(stripped)
        if isinstance(payload, list):
            payload = {"deals": payload}
        return parse_json_payload(payload)
    if filename.lower().endswith((".csv", ".tsv", ".txt")):
        return parse_mt5_csv(text)
    if "<html" in stripped[:200].lower() or "<table" in stripped[:200].lower():
        # MT5 HTML report — strip tags then look for rows
        return parse_mt5_html(text)
    # Default to CSV best-effort
    return parse_mt5_csv(text)


def parse_mt5_html(content: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parse MT5 'Save as Report — HTML' (best-effort regex)."""
    # Crude: pull each <tr> with at least 8 <td>'s. Real parser would use
    # BeautifulSoup but we keep deps minimal.
    rows = []
    tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)
    tag_pattern = re.compile(r"<[^>]+>")
    for tr_match in tr_pattern.finditer(content):
        tds = [tag_pattern.sub("", td.group(1)).strip()
               for td in td_pattern.finditer(tr_match.group(1))]
        if len(tds) < 8:
            continue
        # MT5 HTML typical columns: Time | Deal | Symbol | Type | Volume |
        # Price | Order | Commission | Swap | Profit | Comment
        try:
            t_raw = tds[0]
            t = datetime.strptime(t_raw, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        symbol_raw = tds[2]
        if not symbol_raw:
            continue
        type_raw = tds[3].lower()
        direction = "BUY" if "buy" in type_raw else "SELL" if "sell" in type_raw else ""
        if not direction:
            continue
        try:
            volume = float((tds[4] or "0").replace(",", "."))
            price = float((tds[5] or "0").replace(",", "."))
            profit = float((tds[-2] or "0").replace(",", "."))
        except ValueError:
            continue
        rows.append({
            "ticket": int(tds[1] or 0),
            "symbol": symbol_raw,
            "normalized_symbol": normalize_symbol(symbol_raw),
            "direction": direction,
            "entry_type": "in",  # MT5 HTML often only shows opens; in/out unclear
            "volume": volume,
            "price": price,
            "profit": profit,
            "commission": 0.0,
            "swap": 0.0,
            "deal_time": t.isoformat(),
            "comment": tds[-1][:500] if len(tds) > 10 else "",
        })
    return {"source": "mt5_html"}, rows


async def ingest_deals(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Insert deals into mt5_trades. Dedupe via UNIQUE(ticket, entry_type)."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"inserted": 0, "error": "db_unavailable"}
    client = get_supabase_client()
    if client is None:
        return {"inserted": 0, "error": "no_client"}

    inserted = 0
    duplicates = 0
    errors = 0
    for row in rows:
        if not row.get("symbol") or row.get("direction") not in ("BUY", "SELL"):
            continue
        try:
            res = client.table("mt5_trades").insert_ignore(row)
            if isinstance(res, dict):
                if res.get("duplicate"):
                    duplicates += 1
                elif res.get("error"):
                    errors += 1
                    logger.debug("mt5 ingest insert err: %s", res.get("error"))
                else:
                    inserted += 1
        except Exception as e:
            errors += 1
            logger.debug("mt5 ingest exception: %s", e)
    return {"inserted": inserted, "duplicates": duplicates, "errors": errors,
            "rows_seen": len(rows)}


async def reconcile_window(days: int = 14, time_tolerance_seconds: int = 90) -> Dict[str, Any]:
    """Match unmatched mt5_trades to prediction_logs.

    Match heuristic:
        same normalized_symbol
        same direction
        prediction_logs.created_at within ±time_tolerance_seconds of deal_time
        match the closest one in time

    Stores matched_prediction_id, matched_at, match_confidence.
    """
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"error": "db_unavailable"}
    client = get_supabase_client()
    if client is None:
        return {"error": "no_client"}

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Pull unmatched IN deals (the trade opens)
    deals_q = client.table("mt5_trades").select(
        "id, ticket, normalized_symbol, direction, deal_time, price, profit"
    ).gte("deal_time", since).is_("matched_prediction_id", "null").eq("entry_type", "in").limit(5000)
    res = deals_q.execute() if hasattr(deals_q, "execute") else deals_q
    deals = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []

    preds_q = client.table("prediction_logs").select(
        "id, symbol, ml_direction, ml_entry_price, created_at"
    ).gte("created_at", since).limit(20000)
    res2 = preds_q.execute() if hasattr(preds_q, "execute") else preds_q
    preds = res2.get("data") if isinstance(res2, dict) else getattr(res2, "data", []) or []

    # Index preds by (symbol, direction) → list of (created_at, id)
    index: Dict[Tuple[str, str], List[Tuple[datetime, str]]] = {}
    for p in preds:
        sym = p.get("symbol") or ""
        dir_ = (p.get("ml_direction") or "").upper()
        ts_raw = p.get("created_at")
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except Exception:
            continue
        index.setdefault((sym, dir_), []).append((ts, p["id"]))

    matched = 0
    unmatched = 0
    for d in deals:
        sym = d.get("normalized_symbol") or ""
        dir_ = (d.get("direction") or "").upper()
        ts_raw = d.get("deal_time")
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except Exception:
            unmatched += 1
            continue
        candidates = index.get((sym, dir_), [])
        best = None
        best_dt = None
        for cts, cid in candidates:
            dt = abs((cts - ts).total_seconds())
            if dt <= time_tolerance_seconds and (best_dt is None or dt < best_dt):
                best = cid
                best_dt = dt
        if best:
            confidence = round(100.0 * (1 - best_dt / time_tolerance_seconds), 1)
            try:
                client.table("mt5_trades").eq("id", d["id"]).update({
                    "matched_prediction_id": best,
                    "matched_at": datetime.now(timezone.utc).isoformat(),
                    "match_confidence": confidence,
                })
                matched += 1
            except Exception as e:
                logger.warning("reconcile update failed: %s", e)
        else:
            unmatched += 1

    return {
        "window_days": days,
        "deals_checked": len(deals),
        "matched": matched,
        "unmatched": unmatched,
        "match_rate_pct": round(matched / len(deals) * 100, 1) if deals else 0,
    }


async def reconciliation_report(days: int = 7) -> Dict[str, Any]:
    """Per-symbol comparison: our claimed pips vs MT5 actual profit."""
    from database.supabase_client import get_supabase_client, is_db_available
    if not is_db_available():
        return {"error": "db_unavailable"}
    client = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Pull deals (with profit) and join in-memory with prediction_logs
    deals_q = client.table("mt5_trades").select(
        "normalized_symbol, direction, profit, deal_time, entry_type, matched_prediction_id"
    ).gte("deal_time", since).limit(5000)
    res = deals_q.execute() if hasattr(deals_q, "execute") else deals_q
    deals = res.get("data") if isinstance(res, dict) else getattr(res, "data", []) or []

    by_symbol: Dict[str, Dict[str, Any]] = {}
    for d in deals:
        sym = d.get("normalized_symbol") or "?"
        e = by_symbol.setdefault(sym, {
            "mt5_total_profit": 0.0, "mt5_trade_count": 0,
            "matched_count": 0, "unmatched_count": 0,
        })
        e["mt5_total_profit"] += float(d.get("profit") or 0)
        if d.get("entry_type") == "in":
            e["mt5_trade_count"] += 1
            if d.get("matched_prediction_id"):
                e["matched_count"] += 1
            else:
                e["unmatched_count"] += 1

    for sym, e in by_symbol.items():
        e["mt5_total_profit"] = round(e["mt5_total_profit"], 2)

    return {"window_days": days, "by_symbol": by_symbol,
            "total_deals": len(deals)}
