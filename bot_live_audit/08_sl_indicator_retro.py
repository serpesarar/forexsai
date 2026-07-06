"""
08 — RETROSPEKTİF: tarihsel işlemleri gösterge-ayrımına sok (şimdi çalışır).
Üretim sl_indicator_analysis.py ile AYNI mantık ama indicator_snapshots yerine
yerel barlardan indicators.compute_all ile hesaplar (snapshot tablosu henüz boş).
Sembol başına en iyi yerel TF: XAU/USOIL=1m, indeksler=5m.
"""
import json, sys, bisect
from datetime import datetime
from pathlib import Path
ROOT = Path("/Users/melihcanodacioglu/Desktop/panel")
sys.path.insert(0, str(ROOT / "yeni deneme"))
from indicators import compute_all
from discrimination import print_report
from combo_filter import combo_report

B = ROOT / "bot_live_audit" / "bars"
P = json.loads((ROOT / "bot_live_audit" / "positions.json").read_text())
def ep(s): return datetime.fromisoformat(s).timestamp()

# endeks 5m yerelde yoksa çek
def ensure(sym, tf):
    f = B / f"{sym}_{tf}.json"
    if f.exists():
        return f
    from dotenv import dotenv_values
    from supabase import create_client
    c = dotenv_values(ROOT / "backend" / ".env")
    sb = create_client(c["SUPABASE_URL"], c.get("SUPABASE_SERVICE_ROLE_KEY") or c["SUPABASE_KEY"])
    rows, off = [], 0
    while True:
        r = (sb.table("candle_cache").select("candle_time,open,high,low,close,volume")
             .eq("symbol", sym).eq("timeframe", tf).gte("candle_time", "2026-06-10")
             .order("candle_time").range(off, off + 999).execute().data)
        rows += r
        if len(r) < 1000:
            break
        off += 1000
    f.write_text(json.dumps(rows))
    print(f"  çekildi {sym} {tf}: {len(rows)} bar")
    return f

TF_BY_SYMBOL = {"XAUUSD": "1m", "USOIL.FOREX": "1m", "NDX.INDX": "5m", "GDAXI.INDX": "5m"}

def load_bars(sym, tf):
    rows = json.loads(ensure(sym, tf).read_text())
    return [(ep(r["candle_time"]), r) for r in rows]

TF_SEC = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}
bars_cache = {}
def indicators_at(sym, tf, t_epoch):
    if (sym, tf) not in bars_cache:
        bars_cache[(sym, tf)] = load_bars(sym, tf)
    arr = bars_cache[(sym, tf)]
    keys = [a[0] for a in arr]
    i = bisect.bisect_right(keys, t_epoch)         # entry'ye ≤ son bar
    if i < 30:
        return None
    if t_epoch - arr[i - 1][0] > 3 * TF_SEC[tf]:   # entry bar-boşluğunda → bayat, atla
        return None
    win = [a[1] for a in arr[max(0, i - 320):i]]
    if len(win) < 30:
        return None
    return compute_all([b["open"] for b in win], [b["high"] for b in win],
                       [b["low"] for b in win], [b["close"] for b in win],
                       [b.get("volume", 0) for b in win])

rows = []
miss = 0
for p in P:
    if p["close_reason"] not in ("tp", "sl"):
        continue
    tf = TF_BY_SYMBOL.get(p["symbol"])
    if not tf:
        continue
    ind = indicators_at(p["symbol"], tf, ep(p["entry_time"]))
    if ind is None or ind.get("insufficient"):
        miss += 1
        continue
    rows.append({"win": p["close_reason"] == "tp", "ind": ind,
                 "symbol": p["symbol"], "direction": p["direction"]})

print(f"\n{len(rows)} işlem gösterge ile eşleşti, {miss} bar-kapsamı dışında (06-22 sonrası 1m yok).\n")
print_report(rows, "TÜM (retro) — entry gösterge ayrımı")
for sym in ["NDX.INDX", "GDAXI.INDX", "USOIL.FOREX", "XAUUSD"]:
    sub = [r for r in rows if r["symbol"] == sym]
    if len(sub) >= 25:
        print()
        print_report(sub, f"{sym} ({TF_BY_SYMBOL[sym]}) — entry gösterge ayrımı")

# çok-göstergeli kombinasyon keşfi (overfit korumalı)
print()
combo_report(rows, "TÜM (retro)")
