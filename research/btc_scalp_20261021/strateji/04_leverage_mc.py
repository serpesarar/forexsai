"""Kaldıraç/lot tablosu, eşzamanlılık, ileri gölge süreleri ve gün-bloklu 1 yıllık Monte Carlo (prereg §9, §11)."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import lib_st as L

t0 = time.time()
SETS = pd.read_pickle(L.RES / "portfolio_trades.pkl")
NAMES = ["S1_CORE", "S2_MAX10", "S3_QB", "S4_X04", "S5_CAPREV", "S6_OF02", "S7_DV04c"]
PORT = {"P-CORE": NAMES[:1], "P-PRE": NAMES[:4], "P-ALL-DV": NAMES[:6], "P-ALL": NAMES}
DAYM = 1440
E = L.Engine()
PX = float(E.C[-1])
print(f"son BTC fiyatı (Binance 2026-10-20 kapanış) {PX:,.0f}")
a, b = L.SPLITS["OOS"][0], L.SPLITS["BLIND"][1]
YEARS_POST = ((b - a) - 10 * DAYM * 0) / DAYM / 365.25

# ── kol başı SL, oran, lot ──
rows = []
for k in NAMES:
    d = SETS[k]
    post = d[d.split.isin(["OOS", "BLIND"])]
    bl = d[d.split == "BLIND"]
    slp = (bl.sl_d / bl.sig).median() if len(bl) else (post.sl_d / post.sig).median()
    sl_usd = slp * PX
    r = {"kol": k, "POST_n": len(post), "işlem/yıl": round(len(post) / YEARS_POST, 1),
         "n150_yıl": round(150 / (len(post) / YEARS_POST), 1), "BLIND_medyan_SL_%": round(100 * slp, 3),
         "SL_$_@son_fiyat": round(sl_usd, 0), "ort_tutuş_dk": round(float((post.ext_t - post.ent_t).median()), 0),
         "maks_risk%_2:1": round(100 * 2 * slp, 3), "maks_risk%_1:20": round(100 * 20 * slp, 2)}
    for eq in (10_000, 50_000):
        for rk in (0.0025, 0.005, 0.01):
            lot = eq * rk / sl_usd
            lot_r = max(np.floor(lot * 100) / 100, 0.01)
            r[f"lot_{eq//1000}k_{rk*100:g}%"] = round(lot_r, 2)
            r[f"kaldıraç_{eq//1000}k_{rk*100:g}%"] = round(lot_r * PX / eq, 2)
    rows.append(r)
lev = pd.DataFrame(rows)
lev.to_csv(L.RES / "leverage_table.csv", index=False)
pd.set_option("display.width", 250)
print(lev.to_string())

# ── eşzamanlılık (POST) ──
conc = {}
for p, names in PORT.items():
    d = pd.concat([SETS[k] for k in names])
    d = d[d.split.isin(["OOS", "BLIND"])]
    slp = (d.sl_d / d.sig).to_numpy()
    ev = np.concatenate([np.stack([d.ent_t.to_numpy().astype(float), np.ones(len(d)), 0.005 / slp], 1),
                         np.stack([d.ext_t.to_numpy(), -np.ones(len(d)), -0.005 / slp], 1)])
    ev = ev[np.lexsort((ev[:, 1], ev[:, 0]))]
    npos = np.cumsum(ev[:, 1]); notl = np.cumsum(ev[:, 2])
    conc[p] = {"maks_eşzamanlı_poz": int(npos.max()), "maks_nominal/özs_@%0,5risk": round(float(notl.max()), 2),
               "medyan_nominal_açıkken": round(float(np.median(notl[npos > 0])), 2)}
print("eşzamanlılık:", conc)

# ── kenar görme süresi ──
det = {}
for p, names in PORT.items():
    d = pd.concat([SETS[k] for k in names])
    d = d[d.split.isin(["OOS", "BLIND"])]
    mu, sd = d.R.mean(), d.R.std()
    n2 = (2 * sd / mu) ** 2 if mu > 0 else np.inf
    rate = len(d) / YEARS_POST
    det[p] = {"ortR": round(mu, 4), "sd": round(sd, 3), "n_2σ": int(n2) if np.isfinite(n2) else None,
              "yıl_2σ": round(n2 / rate, 1) if np.isfinite(n2) else None, "işlem/yıl": round(rate, 0)}
print("kenar görme:", det)

# ── Monte Carlo ──
rng = np.random.default_rng(11)
NP = 10_000
mc_rows = []
for p in ("P-CORE", "P-PRE", "P-ALL-DV"):
    d = pd.concat([SETS[k] for k in PORT[p]])
    d = d[d.split.isin(["OOS", "BLIND"])].sort_values("ent_t")
    mu = d.R.mean()
    days = np.arange(a // DAYM, b // DAYM)
    days = days[~((days * DAYM >= L.em("2024-01-01")) & (days * DAYM < L.em("2024-01-11")))]
    dk = (d.ent_t.to_numpy() // DAYM)
    for scen, shift in (("ölçülen", 0.0), ("yarı kenar", 0.5 * mu), ("sıfır kenar", mu)):
        Rv = d.R.to_numpy() - shift
        bydays = [Rv[dk == x] for x in days]
        pick = rng.integers(0, len(days), size=(NP, 365))
        for rk in (0.0025, 0.005, 0.01):
            fin = np.empty(NP); mdd = np.empty(NP)
            for i in range(NP):
                seq = np.concatenate([bydays[j] for j in pick[i]]) if True else None
                eq = np.cumprod(1 + rk * seq) if len(seq) else np.array([1.0])
                pk = np.maximum.accumulate(np.concatenate([[1.0], eq]))
                eqf = np.concatenate([[1.0], eq])
                mdd[i] = np.max(1 - eqf / pk)
                fin[i] = eqf[-1] - 1
            mc_rows.append({"portföy": p, "senaryo": scen, "kenar_R": round(mu - shift, 4), "risk_%": rk * 100,
                            "medyan_getiri_%": round(100 * np.median(fin), 1), "p5_getiri_%": round(100 * np.percentile(fin, 5), 1),
                            "p95_getiri_%": round(100 * np.percentile(fin, 95), 1), "P(zarar)": round(np.mean(fin < 0), 3),
                            "medyan_maxDD_%": round(100 * np.median(mdd), 1), "P(DD≥20%)": round(np.mean(mdd >= 0.2), 3),
                            "P(DD≥50%)": round(np.mean(mdd >= 0.5), 4)})
        print(p, scen, f"{time.time()-t0:.0f}s", flush=True)
mc = pd.DataFrame(mc_rows)
mc.to_csv(L.RES / "mc_risk.csv", index=False)
print(mc.to_string())
json.dump({"price": PX, "concurrency": conc, "detect": det}, open(L.RES / "leverage_meta.json", "w"), indent=1)
print(f"bitti {time.time()-t0:.0f}s")
