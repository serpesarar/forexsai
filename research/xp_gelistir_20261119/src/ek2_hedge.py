import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import kural as KR
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research/son_rapor_20261118/src"))
import rapor as R
G, NY, FIN = R.G, R.NY, R.FIN
HERE = Path(__file__).resolve().parents[1]
T = KR.D[KR.D.besleme == "MT5_NAS100"].sort_values("d").reset_index(drop=True)
def p16(sym, since=None):
    b = R.KD.mt5_m30(sym, since); dp = G.day_prices(b, NY, [960], 1800); dp.index = pd.to_datetime(dp.index)
    return dp.o960, dp.s960
nas_p, nas_s = p16("NAS100")
legs = {"US500": p16("US500", "2018-06-01"), "US30": p16("US30"), "US2000": p16("US2000")}
rn = np.log(nas_p).diff()
def run(leg, mode):
    hp, hs = legs[leg]; rh = np.log(hp).diff()
    beta = (rn.rolling(60).cov(rh) / rh.rolling(60).var()).shift(1)
    rows = []
    for r in T.itertuples():
        d, x = pd.Timestamp(r.d), pd.Timestamp(r.cikis)
        if d not in hp.index or x not in hp.index or not np.isfinite(hp[d]) or not np.isfinite(hp[x]): continue
        if leg == "US500" and d < pd.Timestamp("2020-01-01"): continue
        h = {"h05": 0.5, "h10": 1.0}.get(mode, None)
        if mode == "beta":
            h = float(np.clip(beta.get(d, np.nan), 0.3, 1.5)) if np.isfinite(beta.get(d, np.nan)) else 1.0
        cal = (x - d).days
        short = -((hp[x] + hs[x]) / hp[d] - 1) * 1e4 - 0.5 * cal
        rows.append({"d": d, "don": r.donem, "taban": r.net, "pkt": r.net + h * short})
    return pd.DataFrame(rows)
def m(v, d):
    eq = pd.Series(v, index=d).sort_index().cumsum()
    return {"toplam": float(v.sum()), "zarar": float(v[v < 0].sum()), "kotu10": float(np.sort(v)[:max(1, len(v) // 10)].mean()),
            "DD": float((eq - eq.cummax()).min()), "en_kotu": float(v.min()), "isabet": float((v > 0).mean() * 100), "n": int(len(v))}
out = {}
for leg in legs:
    for mode in ("h05", "h10", "beta"):
        z = run(leg, mode)
        if z.empty: continue
        K, Te = z[z.don == "KESIF"], z[z.don == "TEST"]
        rec = {}
        if len(K) >= 20:
            scale = K.taban.sum() / K.pkt.sum() if K.pkt.sum() > 0 else np.nan
        else:  # US500: KEŞİF yok → TEST'in ilk yarısından ölçek (ikinci yarıda değerlendir)
            h = len(Te) // 2; scale = Te.taban.iloc[:h].sum() / Te.pkt.iloc[:h].sum(); Te = Te.iloc[h:]
        rec["olcek"] = round(float(scale), 2)
        for nm, s in (("KESIF", K), ("TEST", Te)):
            if len(s) < 10: continue
            b, p = m(s.taban.values, s.d.values), m(s.pkt.values * scale, s.d.values)
            rec[nm] = {"n": b["n"], "kar×": round(p["toplam"] / b["toplam"], 2), "zarar×": round(p["zarar"] / b["zarar"], 2),
                       "kotu10×": round(p["kotu10"] / b["kotu10"], 2), "DD×": round(p["DD"] / b["DD"], 2),
                       "en_kotu": [round(b["en_kotu"]), round(p["en_kotu"])], "isabet": [round(b["isabet"], 1), round(p["isabet"], 1)],
                       "korelasyon_taban_pkt": round(float(np.corrcoef(s.taban, s.pkt)[0, 1]), 2)}
        out[f"{leg}_{mode}"] = rec
        print(leg, mode, rec)
(HERE / "results/ek2_hedge.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
