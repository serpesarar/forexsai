from __future__ import annotations
import glob, os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ortak as O
pd.set_option("display.width", 190); pd.set_option("display.max_colwidth", 30)
SRC = os.path.expanduser("~/dukascopy_us100/data")
INF = ["US_CORE_CPI_MOM", "US_CPI_MOM", "US_CORE_PCE", "US_PPI"]; GRW = ["US_NFP", "US_UNEMP", "US_CLAIMS", "US_ISM_MFG", "US_ISM_SVC", "US_RETAIL", "US_GDP", "US_ADP"]
e = O.macro_events(); e["u"] = e.ts.astype("int64") // 10**9; et = e.ts.dt.tz_convert("America/New_York"); e["sn"] = et.dt.minute % 15 * 60 + et.dt.second; e = e[e.family.isin(INF + GRW) & (e.sn <= 300) & (e.z.abs() >= 1)].copy(); e["top"] = (e.u - e.sn).astype(int)
SG = {"infl": -1, "grow": -1, "grow_inv": 1}; e["sg"] = e.kind.map(SG) * np.sign(e.z); ORD = {f: i for i, f in enumerate(INF + GRW)}; e["o"] = e.family.map(ORD); e = e.sort_values(["top", "o"]).drop_duplicates("top")
def ticks(day):
    f = glob.glob(f"{SRC}/{day}/*.csv")
    if not f: return None
    d = pd.read_csv(f[0], dtype={"timestamp": "int64"}); return d.sort_values("timestamp").reset_index(drop=True)
DL = [.5, 1, 2, 5, 10, 20, 30, 47, 60, 120]; XT = [60, 120, 300, 900]; rows = []
for r in e.itertuples():
    day = pd.Timestamp(r.top, unit="s", tz="UTC").strftime("%Y-%m-%d"); T = ticks(day)
    if T is None: continue
    t = T.timestamp.to_numpy() / 1000; a, b = T.askPrice.to_numpy(), T.bidPrice.to_numpy(); t0 = r.top; i0 = np.searchsorted(t, t0)
    if i0 >= len(t) or t[i0] - t0 > 5: continue
    pre = (a[max(i0 - 1, 0)] + b[max(i0 - 1, 0)]) / 2
    for d_ in DL:
        i = np.searchsorted(t, t0 + d_)
        if i >= len(t): continue
        for x_ in XT:
            j = np.searchsorted(t, t0 + x_)
            if j >= len(t) or j <= i: continue
            en, ex = (a[i], b[j]) if r.sg > 0 else (b[i], a[j])
            rows.append({"t": r.top, "fam": r.family, "tür": "enf" if r.family in INF else "büy", "d": d_, "x": x_, "bp": r.sg * (ex - en) / pre * 1e4, "sp": (a[i] - b[i]) / pre * 1e4, "z": r.z})
R = pd.DataFrame(rows); R.to_parquet("results_hiz.parquet") if False else None
print("olay", R.t.nunique(), R.groupby("fam").t.nunique().to_dict(), "olay anı spread med bp", round(R[R.d <= 2].sp.median(), 2), "p90", round(R[R.d <= 2].sp.quantile(.9), 2), "| d=47", round(R[R.d == 47].sp.median(), 2))
for gr, g in [("ENFLASYON", R[R["tür"] == "enf"]), ("BÜYÜME", R[R["tür"] == "büy"]), ("CPI çekirdek+CPI", R[R.fam.isin(["US_CORE_CPI_MOM", "US_CPI_MOM"])]), ("PCE", R[R.fam == "US_CORE_PCE"]), ("PPI", R[R.fam == "US_PPI"]), ("NFP", R[R.fam == "US_NFP"]), ("Başvuru", R[R.fam == "US_CLAIMS"]), ("ISM", R[R.fam.isin(["US_ISM_MFG", "US_ISM_SVC"])])]:
    if g.empty: continue
    print(f"\n{gr} n={g.t.nunique()} ort net bp; satır d(sn), sütun çıkış(sn)"); print(g.pivot_table(index="d", columns="x", values="bp", aggfunc="mean").round(1).to_string())
    print("  d=47 x=300 isabet", round(float((g[(g.d == 47) & (g.x == 300)].bp > 0).mean()), 3), "| d=2 x=60 isabet", round(float((g[(g.d == 2) & (g.x == 60)].bp > 0).mean()), 3))
