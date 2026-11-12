"""D3 sağlamlık (karar dışı, sonradan): yıl tablosu, en iyi 5 hariç, gün-eşli kontrol, komşu gün plasebosu,
gün içi yol (broker M30), sahte FOMC tarihleri (±7 gün kaydırma), S&P/Euro Stoxx yan seti."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf
sys.path.insert(0, "research/dax_profesor_20261112")
from data_load import load
OUT = Path("research/dax_profesor_20261112/results")
cal = pd.read_csv("research/xau_best_days_20261015/makro/out/calendar.csv")
fomc = pd.to_datetime(cal[cal.event == "FOMC"].date).sort_values()
F = set(fomc)
g = yf.download("^GDAXI", start="2007-12-01", progress=False, auto_adjust=False)["Close"].squeeze()
r = ((g / g.shift() - 1) * 1e4).dropna(); r = r[r.index >= "2008-01-01"]
isf = r.index.isin(F)
out = {}
a = r[isf]
out["yil"] = {int(y): round(v, 1) for y, v in a.groupby(a.index.year).mean().items()}
out["yil_pos"] = f"{(a.groupby(a.index.year).mean() > 0).sum()}/{a.index.year.nunique()}"
out["en_iyi5_haric"] = a.sort_values().iloc[:-5].mean()
out["medyan"] = a.median(); out["diger_medyan"] = r[~isf].median()
wd = r[~isf]; out["gun_esli_kontrol"] = {int(k): round(wd[wd.index.weekday == k].mean(), 1) for k in (1, 2)}
out["fomc_gun_dagilimi"] = a.index.weekday.value_counts().to_dict()
# komşu günler: FOMC'dan k işlem günü önce/sonra
pos = np.where(isf)[0]
out["komsu"] = {k: round(r.iloc[np.clip(pos + k, 0, len(r) - 1)].mean(), 1) for k in (-3, -2, -1, 1, 2)}
# sahte tarih plasebosu: her FOMC'u rastgele ±5..±15 işlem günü kaydır, 2000 çekiliş
rng = np.random.default_rng(11); pl = []
for _ in range(2000):
    sh = pos + rng.choice([*range(-15, -4), *range(5, 16)], len(pos)); sh = sh[(sh >= 0) & (sh < len(r))]
    pl.append(r.iloc[sh].mean())
out["sahte_tarih_p"] = float((np.array(pl) >= a.mean()).mean()); out["sahte_tarih_ort"] = float(np.mean(pl))
# VIX kırılımı (önceki gün VIX, sonradan)
vix = yf.download("^VIX", start="2007-12-01", progress=False, auto_adjust=False)["Close"].squeeze().shift(1)
v = vix.reindex(a.index)
out["vix_ge_18_4"] = {"n": int((v >= 18.4).sum()), "ort": round(a[v >= 18.4].mean(), 1)}
out["vix_lt_18_4"] = {"n": int((v < 18.4).sum()), "ort": round(a[v < 18.4].mean(), 1)}
# yan setler: Euro Stoxx 50, FTSE, CAC (Avrupa kapanışı FOMC'dan önce) — aynı tanım
for s in ("^STOXX50E", "^FCHI", "^FTSE", "^N225"):
    x = yf.download(s, start="2007-12-01", progress=False, auto_adjust=False)["Close"].squeeze()
    rx = ((x / x.shift() - 1) * 1e4).dropna(); rx = rx[rx.index >= "2008-01-01"]
    if s == "^N225":   # Tokyo FOMC'dan sonraki sabah kapanır → FOMC günü kapanışı duyurudan ÖNCE (aynı mantık)
        pass
    f2 = rx.index.isin(F); out[s] = {"n": int(f2.sum()), "fomc": round(rx[f2].mean(), 1), "diger": round(rx[~f2].mean(), 1)}
# gün içi yol: broker M30, FOMC öncesi gün 17:30 → FOMC günü saatleri
d = load(); d["day"] = d.ber.dt.tz_localize(None).dt.normalize(); d["hm"] = d.ber.dt.strftime("%H:%M")
px = d.pivot_table(index="day", columns="hm", values="o", aggfunc="first")
days = px.index; path = {}
for hm in ("20:00", "22:00", "08:00", "09:00", "11:00", "13:00", "15:30", "17:30", "19:30"):
    vals = []
    for f in fomc[fomc >= "2019-10-01"]:
        if f not in days: continue
        i = days.get_loc(f); prev = days[i - 1]
        p0 = px.at[prev, "17:30"] if "17:30" in px.columns else np.nan
        day = prev if hm in ("20:00", "22:00") else f
        p1 = px.at[day, hm] if hm in px.columns else np.nan
        if pd.notna(p0) and pd.notna(p1): vals.append((p1 / p0 - 1) * 1e4)
    path[hm] = (len(vals), round(float(np.mean(vals)), 1))
out["broker_yol_17_30_dan"] = path
print(json.dumps(out, indent=1, default=lambda x: round(float(x), 2)))
json.dump(out, open(OUT / "d3_saglamlik.json", "w"), indent=1, default=lambda x: round(float(x), 2))
