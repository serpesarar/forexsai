"""caprev_live.py saf fonksiyonları ↔ kartın olay listesi (round4/cross_market) sadakat testi (Mac, araştırma verisi)."""
import sys
from datetime import date
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "yeni deneme")); sys.path.insert(0, str(ROOT / "research/ndx_gate_forge"))
import caprev_live as cl
from long_data import load_long, macro
from round4 import build, events
import cross_market as cm

vix = macro().VIX_close.dropna()
hist = {str(d.date()): float(v) for d, v in vix.items()}

def mine(bars_df, prof, start):
    bars = [{"t": int(t.timestamp()), "open": o, "high": h, "low": l, "close": c}
            for t, o, h, l, c in zip(bars_df.ts, bars_df.open, bars_df.high, bars_df.low, bars_df.close)]
    days = cl.rth_days(bars, prof)
    by_day = {}
    for b in bars:
        by_day.setdefault(cl.cs.to_local(b["t"], prof["tz"])[0], []).append(b)
    out = {}
    for today, bb in sorted(by_day.items()):
        if today < start or today.weekday() not in cl.TRADE_WEEKDAYS:
            continue
        ctx = cl.daily_context(days, today); v = cl.prev_day_vix(hist, today)
        if ctx is None or ctx["pdl"] is None or not ctx["stress"] or v is None or v < cl.VIX_MIN:
            continue
        tr = cl.trigger(bb, prof, today, ctx["pdl"])
        if tr: out[today] = pd.Timestamp(tr["t"], unit="s", tz="UTC")
    return out

def compare(name, bars_df, prof, ev, start):
    m = mine(bars_df, prof, start)
    r = {pd.Timestamp(d).date(): t for d, t in zip(ev.nyd, ev.ts) if pd.Timestamp(d).date() >= start}
    both = set(m) & set(r); same_bar = sum(m[d] == r[d] for d in both)
    print(f"{name}: kart {len(r)} gün, canlı kod {len(m)} gün, ortak {len(both)}, aynı tetik mumu {same_bar}")
    print("   yalnız kartta:", sorted(set(r) - set(m))[:8], " yalnız canlı kodda:", sorted(set(m) - set(r))[:8])

nd = load_long("1h"); d = build(nd, 60, 540)
compare("NDX", nd, cl.PROFILES["NDX.INDX"], d.loc[events(d, "stress", "hi").index], date(2017, 1, 1))
dd = cm.build_dax("1h")
compare("DAX", dd, cl.PROFILES["GDAXI.INDX"], dd.loc[cm.events(dd, "stress", "hi").index], date(2019, 3, 1))
