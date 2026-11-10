"""EK-7: KSG kazancının 09:30 sıçramasındaki payı ve çıkış gecikmesine duyarlılık."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from ortak import ay_blok, OUT
from broker import gun_tablosu, MT5
ROOT = Path(__file__).resolve().parents[1]
dk = pd.read_parquet(ROOT / "tp_sonrasi_ters_20261109/data/duka_1m.parquet"); et = dk.index.tz_convert("America/New_York").tz_localize(None); dk = dk.assign(d=et.normalize(), m=et.hour * 60 + et.minute); dk = dk[et.dayofweek < 5]
od = lambda mm, col="open": dk[dk.m == mm].drop_duplicates("d").set_index("d")[col]
f = pd.DataFrame({"o15": od(900), "o16": od(960)}); 
for mm in (569, 570, 571, 572, 575, 585): f[f"x{mm}"] = od(mm, "open").shift(-1) if mm != 569 else od(569, "close").shift(-1)
gp = (pd.Series(f.index, index=f.index).shift(-1) - pd.Series(f.index, index=f.index)).dt.days; f["n"] = gp.clip(upper=3); f = f[gp <= 4].dropna(); S = (f.o16 / f.o15 - 1) < 0
def P(v):
    a = v.to_numpy(); return round(float((ay_blok(v.index, lambda ix: a[ix].mean()) > 0).mean()), 3)
res = {"duka": {}}
net = lambda x: ((x / (f.o16 + 1.5) - 1) * 1e4 - 1.8 * f.n)
for k in ("x569", "x570", "x571", "x572", "x575", "x585"):
    v = net(f[k])[S]; res["duka"][k] = {"n": int(len(v)), "net": round(float(v.mean()), 2), "P": P(v), "karsi_kol": round(float(net(f[k])[~S].mean()), 2)}; print("Dukascopy çıkış", k, res["duka"][k])
gap = (f.x570 / f.x569 - 1) * 1e4; res["sicrama_duka"] = {"KSG": round(float(gap[S].mean()), 2), "diger": round(float(gap[~S].mean()), 2), "tum": round(float(gap.mean()), 2)}; print("09:29 kapanış→09:30 açılış sıçraması (bp) Dukascopy", res["sicrama_duka"])
# broker M30: 09:00 barı kapanışı → 09:30 açılışı
x = pd.read_csv(MT5 / "NAS100_M30.csv.gz"); x["et"] = pd.to_datetime(x.t, unit="s") - pd.Timedelta(hours=7); x = x[x.et.dt.dayofweek < 5]; x["d"] = x.et.dt.normalize(); x["m"] = x.et.dt.hour * 60 + x.et.dt.minute
c900 = x[x.m == 540].drop_duplicates("d").set_index("d").c; o930 = x[x.m == 570].drop_duplicates("d").set_index("d").o
t = gun_tablosu("NAS100").dropna(subset=["son_saat"]); K = t.son_saat < 0; days = list(t.index)
nxt = pd.Series(days[1:] + [None], index=days); g2 = pd.Series({d: (o930.get(n, np.nan) / c900.get(n, np.nan) - 1) * 1e4 if n is not None else np.nan for d, n in nxt.items()})
res["sicrama_broker"] = {"KSG": round(float(g2[K].mean()), 2), "diger": round(float(g2[~K].mean()), 2), "tum": round(float(g2.mean()), 2)}; print("broker 09:00 barı kapanışı→09:30 açılış (bp)", res["sicrama_broker"])
b = t.y_brut; res["brut_gece_broker"] = {"KSG": round(float(b[K].mean()), 2), "diger": round(float(b[~K].mean()), 2)}; print("brüt gece", res["brut_gece_broker"])
res["sicrama_haric_KSG_brut"] = round(float((b[K] - g2[K]).mean()), 2); res["sicrama_haric_diger_brut"] = round(float((b[~K] - g2[~K]).mean()), 2); print("sıçrama hariç brüt: KSG", res["sicrama_haric_KSG_brut"], "diğer", res["sicrama_haric_diger_brut"])
(OUT / "t_cikis.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
