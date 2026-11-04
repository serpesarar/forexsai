"""Read-only MT5 export after protocol freeze; completed cash close refresh."""
import hashlib
import json
import sys
from pathlib import Path
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent / "ndx_five_gates_20260930"))
from pull_fresh import _client, fetch

if __name__ == "__main__":
    audit = {"protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
             "rules_sha256": hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest(),
             "started_utc": pd.Timestamp.now(tz="UTC").isoformat()}
    # Do not overwrite the other researcher's possibly intraday September 30 macro row.
    macro = pd.read_csv(HERE.parent / "ndx_gate_forge/data/macro_daily_patched.csv", parse_dates=["date"])
    original = macro.set_index("date").NDXCASH_close.copy()
    z = yf.Ticker("^NDX").history(start="2026-09-28", end="2026-10-02", auto_adjust=False)
    if z.empty:
        raise RuntimeError("Completed Nasdaq cash close unavailable; do not label Oct1 test verified")
    for t, row in z.iterrows():
        day = pd.Timestamp(t.date())
        match = macro.date.eq(day)
        if match.any():
            macro.loc[match, "NDXCASH_close"] = row.Close
        else:
            macro = pd.concat([macro, pd.DataFrame([{"date": day, "NDXCASH_close": row.Close}])], ignore_index=True)
    macro.sort_values("date").to_csv(OUT / "macro_daily.csv", index=False)
    audit["cash_refresh"] = {str(t.date()): {"old": float(original.get(pd.Timestamp(t.date()), float("nan"))),
                                                   "new": float(row.Close)} for t, row in z.iterrows()}
    v = yf.Ticker("^VIX").history(start="2026-09-28", end="2026-10-02", auto_adjust=False)
    if v.empty:
        raise RuntimeError("Completed previous-session VIX unavailable")
    for t, row in v.iterrows():
        macro.loc[macro.date.eq(pd.Timestamp(t.date())), "VIX_close"] = row.Close
    macro.sort_values("date").to_csv(OUT / "macro_daily.csv", index=False)
    target = OUT / "fresh_oct01.json"
    if target.exists():
        raise RuntimeError("Preserve existing export")
    x = fetch(_client(), "2026-09-30T00:00:00+00:00", "2026-10-02T00:00:00+00:00")
    target.write_text(json.dumps(x))
    audit.update({"bars": len(x["rows"]), "offset_seconds": x["offset_seconds"], "point": x["point"],
                  "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    (OUT / "input_audit.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))
