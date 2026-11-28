"""EK-1: makro olay günü SL tipi, DAYCOMBO+REENTRY 9 yıl (ön kayıt ../PROTOCOL.md EK-1)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(1128)
b = pd.read_pickle(ROOT / "research/ndx_sl_onleme_20261123/results/base_full.pkl")
b = b[b.period != "VAKA"].copy()
b["et"] = pd.to_datetime(b.et, utc=True)
b["d"] = b.et.dt.strftime("%Y-%m-%d")
b["cag"] = np.select([b.et.dt.year <= 2020, b.et.dt.year <= 2023], ["2018-20", "2021-23"], "2024-26")
b["sl"] = b.why.eq("SL")
cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
cal["ts"] = pd.to_datetime(cal.ts_utc, utc=True)
fomc = cal[cal.event == "FOMC"]; cpinfp = cal[cal.event.isin(["CPI", "NFP"])]
fd, cd = set(fomc.date), set(cpinfp.date)
b["E1"] = b.d.isin(fd)
fts = fomc.set_index("date").ts
b["E2"] = [bool(r.d in fts.index and (fts[r.d] - pd.Timedelta(minutes=120) <= r.et <= fts[r.d] + pd.Timedelta(minutes=60)))
           if not isinstance(fts.get(r.d), pd.Series) else False for r in b.itertuples()]
b["E3"] = b.d.isin(cd)
b["E4"] = b.E1 | b.E3
base_R, base_sl = b.R.mean(), b.sl.mean()
days = b.d.unique(); dg = {k: g.R.to_numpy() for k, g in b.groupby("d")}
event_days = fd | cd
nonev = [d for d in days if d not in event_days]
dow = pd.to_datetime(pd.Series(nonev)).dt.dayofweek.to_numpy()
rows = []
for f in ["E1", "E2", "E3", "E4"]:
    x, rest = b[b[f]], b[~b[f]]
    fdays = x.d.unique()
    boot = [np.concatenate([dg[k] for k in RNG.choice(fdays, len(fdays))]).mean() for _ in range(4000)]
    p_neg = float((np.array(boot) < 0).mean())
    # plasebo: aynı sayıda olaysız gün, haftanın günü eşli
    fdow = pd.to_datetime(pd.Series(fdays)).dt.dayofweek.value_counts()
    pl = []
    for _ in range(1000):
        pick = np.concatenate([RNG.choice(np.array(nonev)[dow == w], c) for w, c in fdow.items()])
        pl.append(np.concatenate([dg[k] for k in pick]).mean())
    pct = float((np.array(pl) <= x.R.mean()).mean())
    cag = x.groupby("cag").R.agg(["size", "mean"]).round(3).to_dict("index")
    r = {"bayrak": f, "n": len(x), "gun": len(fdays), "ortR": round(x.R.mean(), 3), "kalan_ortR": round(rest.R.mean(), 3),
         "taban_ortR": round(base_R, 3), "SL%": round(100 * x.sl.mean(), 1), "taban_SL%": round(100 * base_sl, 1),
         "P(ortR<0)": round(p_neg, 3), "plasebo_yuzdelik": round(pct, 3), "cag": cag, "toplamR": round(x.R.sum(), 1),
         "aile": x.groupby("fam").R.agg(["size", "mean"]).round(3).to_dict("index")}
    r["gecti_on"] = bool(len(x) >= 40 and x.R.mean() < 0 and rest.R.mean() > base_R and p_neg >= 0.9
                         and all(v["mean"] < 0 for v in cag.values()) and len(cag) == 3
                         and 100 * (x.sl.mean() - base_sl) >= 10 and pct <= 0.05)
    rows.append(r)
ps = sorted([(1 - r["P(ortR<0)"], i) for i, r in enumerate(rows)])
for k, (p, i) in enumerate(ps):
    rows[i]["holm_P"] = round(1 - min(1, p * (len(ps) - k)), 3)
    rows[i]["gecti"] = rows[i]["gecti_on"] and rows[i]["holm_P"] >= 0.9
(OUT / "ek1_olay.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=str))
for r in rows:
    print({k: v for k, v in r.items()})
