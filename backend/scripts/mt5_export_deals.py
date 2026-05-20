"""
MT5 Deal Exporter — runs on the computer where MT5 terminal lives.

Pulls full deal history from MT5 and produces a JSON file that can be
uploaded into the ForexSAI reconciliation endpoint.

Prerequisites (on the MT5 host machine):
    pip install MetaTrader5 pandas

Usage:
    python mt5_export_deals.py --days 30 --out mt5_deals.json
    python mt5_export_deals.py --since 2026-05-13 --out mt5_deals.json

Then upload mt5_deals.json to:
    POST https://upbeat-flow-production.up.railway.app/api/mt5/upload-deals

Output JSON schema:
    {
        "exported_at": ISO timestamp,
        "account_login": int,
        "broker": str,
        "currency": str,
        "deals": [
            {
                "ticket": int,
                "order": int,
                "position_id": int,
                "symbol": str,           # MT5 form e.g. "XAUUSD", "USTEC"
                "type": "BUY" | "SELL",
                "entry": "in" | "out",   # opening vs closing leg
                "volume": float,
                "price": float,
                "profit": float,         # account currency
                "commission": float,
                "swap": float,
                "time": ISO timestamp,
                "comment": str
            }, ...
        ]
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _mt5_type_to_direction(t: int) -> str:
    # MT5 constants: 0=DEAL_TYPE_BUY, 1=DEAL_TYPE_SELL
    return "BUY" if t == 0 else "SELL" if t == 1 else "?"


def _mt5_entry_to_label(e: int) -> str:
    # 0=DEAL_ENTRY_IN, 1=DEAL_ENTRY_OUT, 2=INOUT, 3=OUT_BY
    return {0: "in", 1: "out", 2: "inout", 3: "out_by"}.get(e, str(e))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30, help="Look back N days")
    ap.add_argument("--since", type=str, default=None,
                    help="Start date YYYY-MM-DD (overrides --days)")
    ap.add_argument("--out", type=str, default="mt5_deals.json")
    ap.add_argument("--symbol", type=str, default=None,
                    help="Filter to one symbol (optional)")
    args = ap.parse_args()

    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError:
        print("ERROR: pip install MetaTrader5", file=sys.stderr)
        sys.exit(1)

    if not mt5.initialize():
        print(f"ERROR: mt5.initialize() failed: {mt5.last_error()}", file=sys.stderr)
        sys.exit(1)

    try:
        info = mt5.account_info()
        if info is None:
            print(f"ERROR: account_info() returned None: {mt5.last_error()}", file=sys.stderr)
            sys.exit(1)

        if args.since:
            since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        else:
            since = datetime.now(timezone.utc) - timedelta(days=args.days)
        until = datetime.now(timezone.utc)

        # history_deals_get returns ALL deals (including IN and OUT legs).
        deals = mt5.history_deals_get(since, until) or []
        print(f"Pulled {len(deals)} deals from {since.isoformat()} to {until.isoformat()}")

        rows = []
        for d in deals:
            symbol = getattr(d, "symbol", "")
            if args.symbol and symbol.upper() != args.symbol.upper():
                continue
            rows.append({
                "ticket": int(getattr(d, "ticket", 0)),
                "order": int(getattr(d, "order", 0)),
                "position_id": int(getattr(d, "position_id", 0)),
                "symbol": symbol,
                "type": _mt5_type_to_direction(getattr(d, "type", -1)),
                "entry": _mt5_entry_to_label(getattr(d, "entry", -1)),
                "volume": float(getattr(d, "volume", 0)),
                "price": float(getattr(d, "price", 0)),
                "profit": float(getattr(d, "profit", 0)),
                "commission": float(getattr(d, "commission", 0)),
                "swap": float(getattr(d, "swap", 0)),
                "time": datetime.fromtimestamp(
                    int(getattr(d, "time", 0)), tz=timezone.utc
                ).isoformat(),
                "comment": str(getattr(d, "comment", "") or ""),
            })

        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "account_login": int(getattr(info, "login", 0)),
            "broker": str(getattr(info, "company", "")),
            "currency": str(getattr(info, "currency", "")),
            "balance": float(getattr(info, "balance", 0)),
            "equity": float(getattr(info, "equity", 0)),
            "since": since.isoformat(),
            "until": until.isoformat(),
            "deal_count": len(rows),
            "deals": rows,
        }

        out_path = Path(args.out)
        with open(out_path, "w") as fp:
            json.dump(payload, fp, indent=2)
        print(f"Wrote {len(rows)} deals to {out_path.absolute()}")
        print()
        print("Upload via:")
        print(f"  curl -X POST -F 'file=@{out_path.absolute()}' \\")
        print(f"    https://upbeat-flow-production.up.railway.app/api/mt5/upload-deals")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
