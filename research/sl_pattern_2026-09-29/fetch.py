"""Supabase'den bot_trades + indicator_snapshots (MT5 broker fiyatı) çek → pickle."""
import sys, time
sys.path.insert(0, "/Users/melihcanodacioglu/Desktop/panel/scripts")
import remote  # _client()
import pandas as pd
cl = remote._client()


def fetch_all(table, cols, filters, order, page=1000):
    out, start = [], 0
    while True:
        rows = None
        for attempt in range(6):
            try:
                q = cl.table(table).select(cols)
                for f in filters:
                    q = getattr(q, f[0])(*f[1:])
                rows = q.order(order).range(start, start + page - 1).execute().data
                break
            except Exception as e:
                print("retry", e); time.sleep(3)
        out += rows or []
        if not rows or len(rows) < page:
            break
        start += page
    return out


if __name__ == "__main__":
    bt = fetch_all("bot_trades", "*", [], "close_time")
    pd.DataFrame(bt).to_pickle("bot_trades.pkl"); print("bot_trades", len(bt))
    fp = fetch_all("bot_entry_fingerprints", "*", [], "ts")
    pd.DataFrame(fp).to_pickle("fingerprints.pkl"); print("fp", len(fp))
    which = sys.argv[1:] or ["USOIL.FOREX", "NDX.INDX", "GDAXI.INDX"]
    for sym in which:
        for tf, cols in (("1m", "candle_time,open,high,low,close,volume"),
                         ("5m", "candle_time,open,high,low,close,volume,ind"),
                         ("15m", "candle_time,open,high,low,close,volume,ind"),
                         ("1h", "candle_time,open,high,low,close,volume,ind")):
            rows = fetch_all("indicator_snapshots", cols,
                             [("eq", "symbol", sym), ("eq", "timeframe", tf),
                              ("gte", "candle_time", "2026-06-01")], "candle_time")
            pd.DataFrame(rows).to_pickle(f"is_{sym}_{tf}.pkl")
            print(sym, tf, len(rows), flush=True)
