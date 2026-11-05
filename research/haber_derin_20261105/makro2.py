"""S1–S5 makro sürpriz: NDX 1m; XAU/USOIL 5m (MT5 2025-06→). KEŞİF ≤2025-12-31. --acik ile tüm dönem (adaylar için)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).parent; sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "c1_turev_20261105"))
import ortak as O
pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 44)
A = int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()); Z = int(pd.Timestamp("2026-01-01", tz="UTC").timestamp()); N = 1000
def broker(sym, name, sp):
    p = O.DATA / f"{name}_1m.parquet"
    if not p.exists():
        x = pd.read_csv(HERE.parent / f"c1_turev_20261105/data/mt5/{sym}_M5.csv.gz"); et = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7)
        u = et.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC"); x = x[u.notna()]; u = u.dropna()
        d = pd.DataFrame({"t": u.astype("int64") // 10**9, "open": x.o, "high": x.h, "low": x.l, "close": x.c, "ask_open": x.o + sp, "ask_close": x.c + sp}); d.to_parquet(p, index=False)
    return O.Bars(name)
BB = {"NDX": (O.Bars("NDX"), (1, 5)), "XAU": (broker("XAUUSD", "XAUb", .25), (5,)), "USOIL": (broker("SpotCrude", "OILb", .03), (5,))}
SIGNS = {"NDX": {"infl": -1, "grow": -1, "grow_inv": 1}, "XAU": {"infl": -1, "grow": -1, "grow_inv": 1}, "USOIL": {"oil": -1, "grow": 1, "grow_inv": -1}}
def reaction(B, t, lb):
    t0 = t - t % 60; a = np.searchsorted(B.t, t0 - (B.t[1] - B.t[0] > 60) * (t0 % 300)); b = np.searchsorted(B.t, t0 + lb * 60)
    if a >= len(B.t) or b >= len(B.t) or a == b or B.t[a] - t0 > 300: return np.nan
    return (B.c[b - 1] / B.o[a] - 1) * 1e4
E0 = O.macro_events(); E0["u"] = E0.ts.astype("int64") // 10**9
HZ = (5, 15, 60, 240)
for name, (B, lbs) in BB.items():
    e = E0[E0.kind.isin(SIGNS[name])].sort_values(["u", "order"]).copy(); e["m"] = e.u // 60; e = e.drop_duplicates("m"); e = e[(e.u >= max(A, B.t[0])) & (e.u < Z)].reset_index(drop=True)
    print(f"\n#### {name} olay {len(e)} |z|≥1 {(e.z.abs() >= 1).sum()} |z|<0,5 {(e.z.abs() < .5).sum()}", e.family.value_counts().head(8).to_dict(), flush=True)
    sg = np.array([SIGNS[name][k] for k in e.kind]) * np.sign(e.z.to_numpy()); big = (e.z.abs() >= 1).to_numpy(); small = (e.z.abs() < .5).to_numpy(); us = e.family.str.startswith(("US_", "EIA", "API")).to_numpy()
    # ilk bar için aile başı geçmişten öğrenilen işaret
    lb = lbs[-1]; r = np.array([reaction(B, u, lb) for u in e.u]); learned = np.full(len(e), np.nan)
    for _, g in e.groupby("family"):
        h = []
        for i in g.index:
            if len(h) >= 4 and e.z.at[i] != 0: learned[i] = np.sign(np.sum(h[-12:])) * np.sign(e.z.at[i])
            if np.isfinite(r[i]) and e.z.at[i] != 0: h.append(np.sign(e.z.at[i]) * np.sign(r[i]))
    t_a = e.u.to_numpy(float); t_l = (e.u.to_numpy() - e.u.to_numpy() % 60 + lb * 60 - 1).astype(float); mr = np.abs(r)
    sh = mr >= np.nanmedian(mr)
    cell = lambda nm, mask, side, ts: [{"name": f"{nm} {h}", "ts": ts[mask & np.isfinite(side)], "side": side[mask & np.isfinite(side)].astype(int), "h": h} for h in HZ]
    fams = {"S1 öncül yön": cell("S1", big & (sg != 0), sg, t_a), "S2 öğrenilen": cell("S2", big & np.isfinite(learned) & (learned != 0), learned, t_a),
            "S3 tepkiye uy": cell("S3", big & (r == r) & (r != 0), np.sign(np.nan_to_num(r)), t_l), "S4 sürprizsiz söndür": cell("S4", small & sh & (r == r) & (r != 0), -np.sign(np.nan_to_num(r)), t_l),
            "S5 reddedilen": cell("S5", big & (r == r) & (np.sign(np.nan_to_num(r)) == -sg) & (sg != 0), np.sign(np.nan_to_num(r)), t_l), "S5b kabul": cell("S5b", big & (r == r) & (np.sign(np.nan_to_num(r)) == sg) & (sg != 0), sg, t_l), "S6 büyük şaşkınlık": cell("S6z", (e.z.abs().to_numpy() >= 2) & (sg != 0), sg, t_a)}
    for fm, c in fams.items():
        try:
            print(f"-- {fm}"); print(O.family(B, c, N=N).to_string(index=False), flush=True)
        except Exception as ex:
            print(fm, "hata", ex)
    for f_ in ("US_CPI_MOM", "US_CORE_CPI_MOM", "US_NFP", "US_ISM_SVC", "US_ISM_MFG", "US_RETAIL", "US_CLAIMS", "US_ADP", "EIA_CRUDE", "API_CRUDE"):
        k = (e.family == f_).to_numpy() & big & (sg != 0)
        if k.sum() >= 6:
            print(O.family(B, cell(f"S1 {f_}", k, sg, t_a), N=300).to_string(index=False, header=False), flush=True)
