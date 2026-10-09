"""Sahte kırılım dedektörü — gölge işlem kartı (shadow_pattern_trades, source=fakeout).

ÖN KAYIT (2026-10-09): giriş = karar anındaki son kapanmış 5m kapanışı (tracker kuralı), TP/SL =
dedektör geometrisi × ATR14(5m); çözüm girişten sonraki barlarla, aynı barda ikisi → LOSS.
Maliyet: tipik spread (islem_otopsi.settings.TYPICAL_SPREAD) / SL mesafesi, R'den düşülür (round-trip 1 spread).
Süresi dolan (expired) işlemler kendi r_multiple'ıyla (yoksa 0) sayılır. Karar birimi: aynı sembol+yön+tür
aynı 30 dk içinde tek karar. Ölçütler canlı kartla aynı (≥100, P≥%90, iki yarı, ×1,5 spread, —, tek pozisyon).
Kapsamlar: tüm semboller; NDX; fake_call (fade) ayrı; genuine_call ayrı.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from scripts.islem_otopsi import data, settings as S

RNG = np.random.default_rng(5)
c = data.get_client()
rows = data.fetch_table(c, "shadow_pattern_trades", "symbol,pattern_type,direction,status,entry_time,exit_time,entry_price,sl_price,r_multiple",
                        [("source", "eq", "fakeout")], "entry_time")
d = pd.DataFrame(rows)
d["entry_time"] = pd.to_datetime(d.entry_time, utc=True, format="ISO8601"); d["exit_time"] = pd.to_datetime(d.exit_time, utc=True, format="ISO8601")
d = d[d.status.isin(["win", "loss", "expired"])].copy()
d["r"] = d.r_multiple.fillna(0.0)
d["cost"] = d.symbol.map(S.TYPICAL_SPREAD) / (d.entry_price - d.sl_price).abs()
d["R"] = d.r - d.cost
d["R15"] = d.r - 1.5 * d.cost
d = d.sort_values("entry_time")
key = d.symbol + d.direction + d.pattern_type
d["dec"] = (key.ne(key.shift()) | (d.entry_time.diff() > pd.Timedelta(minutes=30))).cumsum()

def boot(R, days, n=4000):
    u, inv = np.unique(days, return_inverse=True); s, k = np.bincount(inv, weights=R), np.bincount(inv)
    pick = RNG.integers(0, len(u), (n, len(u))); m = s[pick].sum(1) / k[pick].sum(1)
    return (m > 0).mean(), np.percentile(m, [2.5, 97.5])

def single(g):
    keep, busy = [], pd.Timestamp.min.tz_localize("UTC")
    for r in g.itertuples():
        if r.entry_time >= busy: keep.append(r.Index); busy = r.exit_time if pd.notna(r.exit_time) else r.entry_time
    return g.loc[keep]

def card(g, name):
    g = g.groupby("dec").agg(entry_time=("entry_time", "first"), exit_time=("exit_time", "max"), R=("R", "mean"), R15=("R15", "mean"), r=("r", "mean")).reset_index(drop=True)
    R = g.R.to_numpy(); h = len(R) // 2
    p, ci = boot(R, g.entry_time.dt.strftime("%F").to_numpy())
    sp = single(g)
    ok = [len(R) >= 100, R.mean() > 0 and p >= .9, R[:h].mean() >= 0 and R[h:].mean() >= 0, g.R15.mean() > 0, sp.R.mean() > 0]
    v = "RED" if not ok[0] else ("LIVE" if all(ok) else "SHADOW")
    print(f"{name:28} karar={len(R):4} WR %{100*(g.r>0).mean():.1f} brütR {g.r.mean():+.3f} netR {R.mean():+.3f} "
          f"P %{100*p:.0f} CI[{ci[0]:+.3f},{ci[1]:+.3f}] yarılar {R[:h].mean():+.3f}/{R[h:].mean():+.3f} "
          f"×1,5 {g.R15.mean():+.3f} tekpoz {sp.R.mean():+.3f} → {v}")

print(d.entry_time.min().date(), "→", d.entry_time.max().date())
card(d, "TÜMÜ")
for t in ["fake_call", "genuine_call"]:
    card(d[d.pattern_type == t], f"tümü {t}")
for s in sorted(d.symbol.unique()):
    card(d[d.symbol == s], s)
    for t in ["fake_call", "genuine_call"]:
        card(d[(d.symbol == s) & (d.pattern_type == t)], f"  {s} {t}")
