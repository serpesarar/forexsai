"""T3 hacim patlaması + K5b kapitülasyon sağlamlığı."""
import json
import numpy as np, pandas as pd
from common import OUT, DATA, ROOT, load_1m, block_boot
from evaluate import load
from final_candidates import lift, conds
from round2 import tf_feats
from features import _last_complete, map_asof

b = load_1m(); d = load(1)
dec = b.t.to_numpy()[d.i.to_numpy()] + 60
vix = pd.read_parquet(DATA / "feat2.parquet", columns=["vix"]).iloc[d.i.to_numpy()].reset_index(drop=True).vix.to_numpy()
tq = d.utc_h.between(15, 17).to_numpy()
ub = (vix >= 18.4) & (d.h1_trend.to_numpy() > 0) & (d.pos4.to_numpy() <= .6) & ~tq
us = (vix < 18.4) & (d.h1_trend.to_numpy() < 0) & (d.pos4.to_numpy() >= .4) & ~tq
def Y(ubm, usm):
    out = {}
    for s, u in [("B", ubm), ("S", usm)]:
        v = d[f"R_G80_{s}"].where(u)
        out[s] = (v - v.groupby([d.period, d.utc_h]).transform("mean")).to_numpy()
    return out
yb, ya = Y(ub, us), Y(np.ones(len(d), bool), np.ones(len(d), bool))
days, per = d.ny_date.to_numpy(), d.period.to_numpy()
res = {"T3 eşik × TF (bot evreni)": {}, "T3 eşik × TF (genel)": {}}
vr = {}
for tf in (1, 5, 15):
    _, vr[tf] = tf_feats(b, tf, dec)
    for thr in (1.3, 1.5, 2.0):
        m = vr[tf] >= thr
        res["T3 eşik × TF (bot evreni)"][f"{tf}m ≥{thr}"] = lift(yb, (m & ub, m & us), days, per)
        res["T3 eşik × TF (genel)"][f"{tf}m ≥{thr}"] = lift(ya, (m, m), days, per)
# son 3 kapanmış 5m barın herhangi biri
s5 = _last_complete(b[["ts","t","open","high","low","close","volume"]], 5)
v = s5.volume.to_numpy(float); prev = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
r = v / prev; anyr = pd.Series(r >= 1.5).rolling(3).max().to_numpy()
any3 = map_asof(dec, s5.avail.to_numpy(), anyr, 900) >= 1
res["T3 son 3×5m'de herhangi ≥1.5 (bot evreni)"] = lift(yb, (any3 & ub, any3 & us), days, per)
# saat dağılımı: sabit saat mi?
m = vr[5] >= 1.5
res["T3 bloklananların UTC saat payı"] = (pd.Series(d.utc_h.to_numpy()[m & (ub | us)]).value_counts(normalize=True).round(3).head(6).to_dict())
# T3 yön: spike barının yönüyle aynı yöne mi karşı mı giriş?
body = map_asof(dec, s5.avail.to_numpy(), (s5.close - s5.open).to_numpy(float), 900)
with_dir_b, with_dir_s = m & (body > 0), m & (body < 0)
res["T3 spike yönünde giriş (bot evreni)"] = lift(yb, (with_dir_b & ub, with_dir_s & us), days, per)
res["T3 spike'a karşı giriş (bot evreni)"] = lift(yb, (m & (body < 0) & ub, m & (body > 0) & us), days, per)

# bot işlemleri
t = pd.read_csv(ROOT / "nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv")
bx = pd.read_csv(DATA / "box_trades_40d.csv"); bx = bx[bx.symbol == "NAS100"]
t = pd.concat([t, bx[~bx.position_id.isin(t.position_id)]], ignore_index=True)
t["ot"] = pd.to_datetime(t.open_time_utc, utc=True); t["pts"] = t.profit / t.volume
t["dec"] = t.ot.dt.floor("min").astype(str) + t.direction
g = t.groupby("dec").agg(ot=("ot","first"), side=("direction","first"), pts=("pts","mean"), usd=("profit","sum")).reset_index()
gd = g.ot.astype("int64").to_numpy() // 10**9
bt = {}
for tf in (1, 5, 15):
    _, vv = tf_feats(b, tf, gd)
    for thr in (1.3, 1.5, 2.0):
        mm = vv >= thr
        bt[f"{tf}m ≥{thr}"] = {"n": int(mm.sum()), "gün": int(g.ot[mm].dt.date.nunique()), "bloklanan_p": round(g.pts[mm].mean(), 1) if mm.any() else None, "kalan_p": round(g.pts[~mm].mean(), 1)}
res["T3 bot işlemleri eşik × TF"] = bt
# K5b kapitülasyon — bot SELL
f1 = pd.read_parquet(DATA / "feat_tf1.parquet", columns=["pdl", "price"])
k = np.searchsorted(b.t.to_numpy() + 60, gd, side="right") - 1
pdl = f1.pdl.to_numpy()[k]; px = g.ot.map(lambda x: x)  # fiyat: işlem açılış fiyatı
op = t.groupby("dec").open_price.first().reindex(g.dec).to_numpy()
ny = g.ot.dt.tz_convert("America/New_York")
C = conds(pd.to_datetime(ny.dt.date), (ny.dt.hour*60+ny.dt.minute).to_numpy(), ny.dt.weekday.to_numpy(), None)
k5 = C["K5 Stres-dönüş SELL yok"][1]
sell = (g.side == "SELL").to_numpy()
# NAS100 fiyatı ile bar (NAS100 MT5) aynı kaynak; pdl barlardan
cap = sell & k5 & (op < pdl)
res["K5b bot SELL: stres & < önceki dip"] = {"n": int(cap.sum()), "gün": int(g.ot[cap].dt.date.nunique()), "p": round(g.pts[cap].mean(), 1) if cap.any() else None}
res["K5b bot SELL: stres & ≥ önceki dip"] = {"n": int((sell & k5 & ~(op < pdl)).sum()), "p": round(g.pts[sell & k5 & ~(op < pdl)].mean(), 1)}
res["K5b bot SELL: stres değil"] = {"n": int((sell & ~k5).sum()), "p": round(g.pts[sell & ~k5].mean(), 1)}
(OUT / "round2c.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
for kk, vv in res.items():
    print(f"\n## {kk}")
    if isinstance(vv, dict) and all(isinstance(x, dict) for x in vv.values()):
        for a, c in vv.items(): print("  ", a, c)
    else: print("  ", vv)
