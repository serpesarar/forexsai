"""Gölge modülü (yeni deneme/xau_swing_shadow.py) ↔ XS-01 araştırma kodu sadakat sınaması (aynı Dukascopy verisi)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "yeni deneme"))
import xau_swing_shadow as xs
import xs_test as rt

d = rt.d; H = rt.H1
d1 = [{"t": int(t.timestamp()), "o": o, "h": h, "l": l, "c": c} for t, o, h, l, c in zip(d.ts, d.open, d.high, d.low, d.close)]
h1 = [{"t": int(t.timestamp()), "o": o, "h": h, "l": l, "c": c} for t, o, h, l, c in zip(H.ts, H.open, H.high, H.low, H.close)]
h1t = np.array([b["t"] for b in h1])
st = {"open": [], "last_checked": None}; trades = []
for k in range(260, len(d1)):
    cut = int(np.searchsorted(h1t, d1[k]["t"]))       # giriş anına kadarki H1 (gelecek yok)
    for r in xs.step(st, d1[:k + 1], h1[:cut]):
        if r["kind"] == "close":
            trades.append((r["entry_t"], round(r["R"], 6)))
ref = rt.run(d, d.sig)
reft = [(int(t.timestamp()), round(r, 6)) for t, r in zip(ref.ts, ref.R)]
print("gölge işlem:", len(trades), " araştırma işlem:", len(reft))
same = len(set(trades) & set(reft)); print("birebir eşleşen:", same)
print("gölge ortR %.4f  araştırma ortR %.4f" % (np.mean([r for _, r in trades]), ref.R.mean()))
