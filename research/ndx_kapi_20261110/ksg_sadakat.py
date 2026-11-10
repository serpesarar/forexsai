"""Canlı modül ↔ araştırma sadakati: ksg_live.find_signal'ı broker NAS100 M30 geçmişinde her gün çalıştır,
araştırmadaki 1.039 sinyal gecesiyle karşılaştır (yeni deneme/ modülünü olduğu gibi içe alır)."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT / "yeni deneme")); sys.path.insert(0, str(Path(__file__).resolve().parent))
import ksg_live as ks
from broker import MT5, gun_tablosu
x = pd.read_csv(MT5 / "NAS100_M30.csv.gz"); x["et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7)
x["utc"] = x.et.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC"); x = x.dropna(subset=["utc"])
x["te"] = x.utc.astype("int64") // 10**9; x["d"] = x.et.dt.normalize()
live = set(); n_days = 0
for d, g in x.groupby("d"):
    if d.dayofweek >= 5: continue
    n_days += 1
    bars = [{"t": int(r.te), "open": r.o, "high": r.h, "low": r.l, "close": r.c} for r in g.itertuples()]
    if ks.find_signal(bars, d.date()): live.add(d)
t = gun_tablosu("NAS100").dropna(subset=["son_saat", "y_net"]); res = set(t.index[t.son_saat < 0])
print(f"gün {n_days} · canlı modül sinyali {len(live)} · araştırma sinyali {len(res)} · ortak {len(live & res)} · yalnız canlı {len(live - res)} · yalnız araştırma {len(res - live)}")
print("yalnız canlı (ilk 8):", sorted(d.date() for d in live - res)[:8]); print("yalnız araştırma (ilk 8):", sorted(d.date() for d in res - live)[:8])
