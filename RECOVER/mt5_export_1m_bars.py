"""
MT5 1m bar exporter — recovery operation (2026-05-20).

Pulls 1m OHLCV bars for the 4 traded symbols from MT5 and emits a JSON
payload that backend's /api/mt5/upload-1m-bars endpoint will ingest into
candle_cache. Those bars are the ground truth for the signal-replay
service (services/signal_replay_1m.py).

Run on the MT5 host (Windows box where MetaTrader 5 terminal lives):
    pip install MetaTrader5
    python mt5_export_1m_bars.py --since 2026-02-10 --out mt5_1m_bars.json

Then upload from any machine:
    curl -X POST -F 'file=@mt5_1m_bars.json' \
        https://upbeat-flow-production.up.railway.app/api/mt5/upload-1m-bars

Symbol mapping (MT5 → ForexSAI canonical):
    XAUUSD  → XAUUSD
    USTEC   → NDX.INDX
    DE40    → GDAXI.INDX
    XTIUSD  → USOIL.FOREX
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MT5_SYMBOLS = ["XAUUSD", "USTEC", "DE40", "XTIUSD"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=str, default="2026-02-10",
                    help="Start date YYYY-MM-DD (default 2026-02-10)")
    ap.add_argument("--until", type=str, default=None,
                    help="End date YYYY-MM-DD (default: now)")
    ap.add_argument("--symbols", nargs="+", default=MT5_SYMBOLS,
                    help=f"MT5 symbols to export (default: {MT5_SYMBOLS})")
    ap.add_argument("--out", type=str, default="mt5_1m_bars.json")
    ap.add_argument("--chunk-days", type=int, default=10,
                    help="Pull in N-day chunks (MT5 caps bars per request)")
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
        since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        until = (datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc)
                 if args.until else datetime.now(timezone.utc))
        if until <= since:
            print("ERROR: --until must be after --since", file=sys.stderr)
            sys.exit(1)

        total_bars = 0
        per_symbol = {}

        for sym in args.symbols:
            # Verify the symbol exists in the user's MT5 broker terminal.
            info = mt5.symbol_info(sym)
            if info is None:
                print(f"WARN: {sym} not found in MT5 — skipping")
                per_symbol[sym] = {"count": 0, "bars": [], "error": "symbol_not_found"}
                continue
            if not info.visible:
                mt5.symbol_select(sym, True)

            bars_all = []
            cursor = since
            while cursor < until:
                chunk_end = min(cursor + timedelta(days=args.chunk_days), until)
                rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, cursor, chunk_end)
                if rates is not None and len(rates) > 0:
                    for r in rates:
                        bars_all.append({
                            "t": int(r["time"]),                # unix seconds (broker tz)
                            "o": float(r["open"]),
                            "h": float(r["high"]),
                            "l": float(r["low"]),
                            "c": float(r["close"]),
                            "v": float(r.get("tick_volume", 0) or r.get("real_volume", 0) or 0),
                        })
                cursor = chunk_end

            # Dedupe by timestamp (chunks can overlap at boundaries)
            seen = {}
            for b in bars_all:
                seen[b["t"]] = b
            bars_clean = sorted(seen.values(), key=lambda x: x["t"])

            per_symbol[sym] = {"count": len(bars_clean), "bars": bars_clean}
            total_bars += len(bars_clean)
            print(f"  {sym:8s} {len(bars_clean):>7d} bars "
                  f"({datetime.fromtimestamp(bars_clean[0]['t'], tz=timezone.utc).isoformat() if bars_clean else '—'} "
                  f"→ {datetime.fromtimestamp(bars_clean[-1]['t'], tz=timezone.utc).isoformat() if bars_clean else '—'})")

        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "since": since.isoformat(),
            "until": until.isoformat(),
            "timeframe": "1m",
            "total_bars": total_bars,
            "symbols": per_symbol,
        }

        out_path = Path(args.out)
        with open(out_path, "w") as fp:
            json.dump(payload, fp)
        size_mb = out_path.stat().st_size / 1_000_000
        print(f"\nWrote {total_bars} bars across {len(per_symbol)} symbols → {out_path.absolute()} ({size_mb:.1f} MB)")
        print("\nUpload via:")
        print(f"  curl -X POST -F 'file=@{out_path.absolute()}' \\")
        print(f"    https://upbeat-flow-production.up.railway.app/api/mt5/upload-1m-bars")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
