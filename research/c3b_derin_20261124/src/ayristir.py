"""ayristir.py — C3b tutuşunun seans dilimlerine ayrıştırılması (betimleyici, TUR 2 ön kaydından ÖNCE).
Dilimler: giriş 15:30 → 16:00 (G0), 16:00 → ertesi 09:30 (gece), 09:30 → 15:30 (gün içi), son gün 09:30 → çıkış 15:30 dahil."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research/ndx_10y_1m_20261116/src"))
import lib
m1 = lib.load_m1(); D = lib.daily_table(m1).set_index("d")
T = pd.read_parquet(Path(__file__).resolve().parents[1] / "cache/duka_trades.parquet")
T = T[T.cand == "BASE"]
days = list(D.index)
rows = []
for x in T.itertuples():
    a, b = days.index(x.d), days.index(x.d_out)
    seg = []
    p = x.px_in
    for k in range(a, b + 1):
        d = days[k]
        if k > a:
            o = D.loc[d, "open930"]
            seg.append(("gece", (o / p - 1) * 1e4)); p = o
        e = D.loc[d, "E"] if k == b else D.loc[d, "c1600"]
        if k == a:
            seg.append(("G0", (D.loc[d, "c1600"] / p - 1) * 1e4)); p = D.loc[d, "c1600"]
        elif k == b:
            seg.append(("gun_ici_son", (e / p - 1) * 1e4)); p = e
        else:
            seg.append(("gun_ici", (e / p - 1) * 1e4)); p = e
    for nm, v in seg:
        rows.append((x.d, x.vd, x.bp > 0, nm, v))
f = pd.DataFrame(rows, columns=["d", "vd", "win", "dilim", "bp"])
print(f.groupby("dilim").bp.agg(["count", "mean", "sum"]).round(1))
print(f.groupby(["win", "dilim"]).bp.agg(["count", "mean", "sum"]).round(1))
print(f.groupby(["vd", "dilim"]).bp.agg(["count", "mean", "sum"]).round(1))

# ── sızıntısız: pozisyon k. gecenin başında (16:00) açıkken k. gece (16:00→09:30) ve k. gün içi (09:30→15:30) ──
rows = []
for x in T.itertuples():
    a, b = days.index(x.d), days.index(x.d_out)
    for k in range(a + 1, b + 1):
        d0, d = days[k - 1], days[k]
        night = (D.loc[d, "open930"] / D.loc[d0, "c1600"] - 1) * 1e4
        day = (D.loc[d, "E"] / D.loc[d, "open930"] - 1) * 1e4
        rows.append((x.d, x.vd, k - a, night, day))
g = pd.DataFrame(rows, columns=["d", "vd", "gece_no", "gece", "gun"])
print("\nSIZINTISIZ")
print(g.groupby("gece_no")[["gece", "gun"]].agg(["count", "mean", "sum"]).round(1))
print(g.groupby("vd")[["gece", "gun"]].agg(["count", "mean", "sum"]).round(1))
