"""H8c sağlamlık: gerçek maliyet, büyük olay çıkarma, çıkış/eşik duyarlılığı, gotobi tanımı, aile max-t. Çalıştır: ../../.venv/bin/python -I h8c_saglamlik.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f, hyp
TS = json.loads((f.DATA / "tick_spread.json").read_text())["sp"]
COMM = {"USDJPY": 0.70, "EURJPY": 0.60, "GBPJPY": 0.53, "AUDJPY": 1.07}
PAIRS = list(COMM)
got, jbd = hyp.gotobi_days("2010-10-08", "2026-11-12")
DAYS = sorted(d for d in jbd if d.dayofweek < 5)

def cost(pair, r, h_in, h_out):
    sh = TS[pair]["saat"]; tc = (sh.get(str(h_in), [0])[0] + sh.get(str(h_out), [0])[0]) / 2
    return max(r["gross"] - r["net"], tc) + COMM[pair]

def events(pair, lab, exit_h=6, thr=0.0, pre=(-1, 1)):
    rows = []
    for d in DAYS:
        if lab(d) is False: continue
        p = hyp.trade(pair, d + pd.Timedelta(hours=pre[0]), d + pd.Timedelta(hours=pre[1]), +1)
        if p is None or p["gross"] <= thr: continue
        r = hyp.trade(pair, d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=exit_h), -1)
        if r is None: continue
        rows.append({"t": d, "gross": r["gross"], "net": r["gross"] - cost(pair, r, 1, exit_h % 24), "got": d in got})
    return pd.DataFrame(rows)

res = {}
base = events("USDJPY", lambda d: True)
g = base[base.got]
ev = g.set_index("t").net
res["ana"] = f.summ(ev.reset_index(drop=True), pd.Series(ev.index))
res["ilk5_cikinca"] = round(ev.drop(ev.abs().nlargest(5).index).mean(), 2)
res["medyan"] = round(ev.median(), 2); res["isabet"] = round((ev > 0).mean(), 3)
res["yil_pozitif"] = f"{int((ev.groupby(ev.index.year).mean() > 0).sum())}/{ev.index.year.nunique()}"
res["kontrol_net"] = round(base[~base.got].net.mean(), 2)
res["cikis_duyarlilik"] = {h: round(events("USDJPY", lambda d: d in got, exit_h=h).net.mean(), 2) for h in (3, 4, 5, 6, 7, 8)}
sig = (lambda x: x.std())(events("USDJPY", lambda d: d in got, thr=-1e9).gross)
res["esik_duyarlilik"] = {k: round(events("USDJPY", lambda d: d in got, thr=k).net.mean(), 2) for k in (-1e9, 0.0, 5.0, 10.0, 20.0)}
mb = {}
for d in got:
    mb[d] = d.day in (5, 10, 15, 20, 25, 30)
res["tanim"] = {"5_10_gunleri": round(g[g.t.map(lambda d: d.day % 5 == 0)].net.mean(), 2),
                "kaydirilmis_veya_ay_sonu": round(g[~g.t.map(lambda d: d.day % 5 == 0)].net.mean(), 2)}
# aile max-t (4 çift, kontrol farkı), yıl içi dairesel kaydırma
tabs = {p: events(p, lambda d: True) for p in PAIRS}
def dt(df, lab):
    a, b = df.net[lab], df.net[~lab]
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
obs = {p: dt(df, df.got.values) for p, df in tabs.items()}
rng = np.random.default_rng(23); mx = []
for _ in range(1000):
    m = []
    for p, df in tabs.items():
        lab = df.got.values.copy(); yrs = df.t.dt.year.values
        for y in np.unique(yrs):
            i = np.where(yrs == y)[0]; lab[i] = np.roll(lab[i], rng.integers(2, max(3, len(i) - 2)))
        m.append(dt(df, lab))
    mx.append(max(m))
mx = np.array(mx)
res["aile_maxt"] = {p: {"t": round(v, 2), "p": round(float((mx >= v).mean()), 3)} for p, v in obs.items()}
print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
(f.RES / "h8c_saglamlik.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
