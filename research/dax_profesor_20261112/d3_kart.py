"""D3 canlıya alma kartı (2. KURAL 6 ölçüt), broker GER40 M30 gerçek icra + ^GDAXI günlük uzun dönem.
Kural: FOMC gününden önceki işlem günü 17:30 Berlin barı açılışında AL → FOMC günü 19:30 barı açılışında SAT (duyuru 20:00 Berlin).
Maliyet: spread × 1,5 (giriş barının sp'si) + 1 gece swap; Cuma gecesi yok (FOMC Pzt/Salı başlarsa önceki gün Cuma → 3 gece)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
sys.path.insert(0, "research/dax_profesor_20261112")
from data_load import load
RNG = np.random.default_rng(42)
SWAP = 4.94 / 365 * 100
OUT = Path("research/dax_profesor_20261112/results")
cal = pd.read_csv("research/xau_best_days_20261015/makro/out/calendar.csv")
fomc = pd.to_datetime(cal[cal.event == "FOMC"].date).sort_values()
d = load(); d["day"] = d.ber.dt.tz_localize(None).dt.normalize(); d["hm"] = d.ber.dt.strftime("%H:%M")
px = d.pivot_table(index="day", columns="hm", values="o", aggfunc="first")
sp = d.pivot_table(index="day", columns="hm", values="sp", aggfunc="first")
cl = d.pivot_table(index="day", columns="hm", values="c", aggfunc="first")
rows = []
for f in fomc:
    if f not in px.index: continue
    i = px.index.get_loc(f); prev = px.index[i - 1]
    if (f - prev).days > 4: continue
    e, x = px.at[prev, "17:30"], px.at[f, "19:30"] if "19:30" in px.columns else np.nan
    if pd.isna(e) or pd.isna(x): continue
    nights = (f - prev).days
    cost = 1.5 * sp.at[prev, "17:30"] * 0.1 / e * 1e4 + SWAP * nights
    gross = (x / e - 1) * 1e4
    opt = (cl.at[f, "19:00"] / cl.at[prev, "17:00"] - 1) * 1e4 if pd.notna(cl.at[f, "19:00"]) and pd.notna(cl.at[prev, "17:00"]) else np.nan   # iyimser: bar kapanışı, spread'siz
    rows.append(dict(fomc=f.date(), gross=gross, net=gross - cost, net15=gross - 1.5 * cost, opt=opt, cost=cost))
t = pd.DataFrame(rows)
def bP(x): return float((np.array([RNG.choice(x, len(x)).mean() for _ in range(5000)]) > 0).mean())
h = len(t) // 2
card = dict(n=len(t), net_bp=t.net.mean(), P_EV=bP(t.net.values), yari=[t.net.iloc[:h].mean(), t.net.iloc[h:].mean()],
            sp15_bp=t.net15.mean(), iyimser_bp=t.opt.mean(), icra_farki=t.opt.mean() - t.net.mean(), isabet=(t.net > 0).mean(),
            en_buyuk5_haric=t.net.sort_values().iloc[:-5].mean(), en_kotu=t.net.min(), ilk=str(t.fomc.min()), son=str(t.fomc.max()))
card["olcutler"] = dict(hacim=card["n"] >= 150, beklenti=card["net_bp"] > 0 and card["P_EV"] >= 0.90,
                        kararlilik=min(card["yari"]) >= 0, surtunme=card["sp15_bp"] > 0,
                        icra=abs(card["icra_farki"]) <= card["net_bp"] / 2, sira_bagimli=True)
card["gecen"] = int(sum(card["olcutler"].values()))
# uzun dönem günlük (^GDAXI, kapanış→kapanış = 17:30→17:30, duyurudan önce): mutlak net
g = yf.download("^GDAXI", start="2007-12-01", progress=False, auto_adjust=False)["Close"].squeeze()
r = ((g / g.shift() - 1) * 1e4).dropna(); r = r[r.index >= "2008-01-01"]; a = r[r.index.isin(set(fomc))] - 0.5 - SWAP
gd = dict(n=len(a), net_bp=a.mean(), P_EV=bP(a.values), yari=[a.iloc[:len(a)//2].mean(), a.iloc[len(a)//2:].mean()])
t.to_csv(OUT / "d3_broker_islemler.csv", index=False)
res = {"broker_GER40_2019_2026": card, "GDAXI_gunluk_2008_2026": gd}
print(json.dumps(res, indent=1, default=lambda x: round(float(x), 3) if not isinstance(x, (bool, np.bool_)) else bool(x)))
json.dump(res, open(OUT / "d3_kart.json", "w"), indent=1, default=lambda x: round(float(x), 3) if not isinstance(x, (bool, np.bool_)) else bool(x))
