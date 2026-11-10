"""MA-05 A: DAYCOMBO + REENTRY bağımsız dönem (2024, 2025), dolar ve gün ölçeği. Ön kayıt: PROTOCOL.md EK-2."""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; OUT = HERE / "results"
DEN = HERE.parent / "ndx_seans_tasima_20261103/denetim"
os.chdir(DEN); sys.path.insert(0, str(DEN))
import c1  # noqa: E402  (salt fonksiyonlar; __main__ koşmaz)
SL_PTS = 110.0
def load_year(nm: str) -> pd.DataFrame:
    if nm == "2024":
        d = pd.read_csv(DEN / "canli_daycombo_2024.csv"); r = pd.read_csv(DEN / "canli_reentry_2024.csv")
    else:
        a = pd.read_parquet(DEN / "../../ndx_pattern_motifs/data/bars_1m.parquet"); a = a[a.ts < pd.Timestamp("2026-01-01", tz="UTC")].reset_index(drop=True)
        s = c1.dc.signals(a, friday=False); mm = c1.M(a); d = c1.stream(mm, s); r = c1.reentry(mm, d)
        assert len(d) == 195 and abs(d.R.mean() + .030) < .001, (len(d), d.R.mean())
        d = d[pd.to_datetime(d.et, utc=True) >= "2025-01-01"]; r = r[pd.to_datetime(r.et, utc=True) >= "2025-01-01"]
    d = d.assign(aile="DAYCOMBO"); r = r.assign(aile="REENTRY")
    t = pd.concat([d[["R", "et", "day", "aile"]], r[["R", "et", "day", "aile"]]]).assign(yil=nm)
    t["et"] = pd.to_datetime(t.et, utc=True); return t.sort_values("et").reset_index(drop=True)
def block_p(t: pd.DataFrame, B=5000, seed=7):
    rng = np.random.default_rng(seed); u = np.sort(t.day.unique()); ix = np.searchsorted(u, t.day); S = np.bincount(ix, t.R, len(u)); N = np.bincount(ix, minlength=len(u)); D = len(u); o = []; tot = []
    for _ in range(B):
        dr = ((rng.integers(D, size=int(np.ceil(D / 5)))[:, None] + np.arange(5)) % D).ravel()[:D]; o.append(S[dr].sum() / max(N[dr].sum(), 1)); tot.append(S[dr].sum())
    o = np.array(o); tot = np.array(tot); return float((o > 0).mean()), [float(np.quantile(tot, .025)), float(np.quantile(tot, .975))]
T = pd.concat([load_year("2024"), load_year("2025")]); T.to_csv(OUT / "ma05a_islemler.csv", index=False)
res = {}
for key, t in [("2024", T[T.yil == "2024"]), ("2025", T[T.yil == "2025"]), ("2024+2025", T)]:
    p, ci = block_p(t); day = t.groupby("day").R.sum(); eq = day.cumsum(); dd = float((eq - eq.cummax()).min())
    res[key] = {"n": len(t), "gun": int(day.size), "ortR": round(float(t.R.mean()), 4), "P_ortR>0": round(p, 3), "toplamR": round(float(t.R.sum()), 1), "toplamR_%95": [round(x, 1) for x in ci],
                "aile": {a: [int(len(g)), round(float(g.R.mean()), 4)] for a, g in t.groupby("aile")}, "enkotu_gun_R": round(float(day.min()), 2), "enkotu5_R": round(float(day.nsmallest(5).sum()), 2),
                "maxDD_R": round(dd, 1), "gunlukSR": round(float(day.mean() / day.std()), 3)}
    res[key]["dolar"] = {str(l): {"toplam": round(t.R.sum() * SL_PTS * l), "%95": [round(x * SL_PTS * l) for x in ci], "enkotu_gun": round(day.min() * SL_PTS * l), "enkotu5": round(day.nsmallest(5).sum() * SL_PTS * l), "maxDD": round(dd * SL_PTS * l)} for l in (30, 10, 5)}
    print(key, json.dumps(res[key], ensure_ascii=False))
a = res["2024+2025"]; res["olcut_tam_lot"] = bool(a["ortR"] > 0 and a["P_ortR>0"] >= .95 and res["2024"]["ortR"] > 0 and res["2025"]["ortR"] > 0); print("tam lotu hak eder mi:", res["olcut_tam_lot"])
(OUT / "ma05a.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
