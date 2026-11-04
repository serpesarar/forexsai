"""Ex-ante özellikler (işlem girişinde BİLİNEN) — sonuçlara bakmadan tanımlandı (2026-10-16):
 makro: giriş UTC gününden ÖNCEKİ son ABD işlem günü kapanışı (D-1); DFII10 (reel faiz) yayın gecikmesi için D-2.
 F_evday   : giriş UTC günü FOMC/CPI/NFP yayın günü (takvim önceden ilanlı)
 F_evwin   : FOMC/CPI/NFP yayın anı [giriş, giriş+20s) içinde (zamanlanmış → ex-ante)
 F_post6   : girişten önceki 6 saatte FOMC/CPI/NFP yayını oldu (kırılım olay tetikli; yayın girişte geçmiş)
 F_vix20, F_vix25 : VIX(D-1) ≥ 20 / ≥ 25 ;  F_vixup : VIX(D-1) > VIX(D-6)
 F_dxy5dn, F_dxy20dn : DXY(D-1) < DXY(D-6) / DXY(D-21)
 F_ry20dn  : DFII10(D-2) < DFII10(D-22)
 F_spxdd10 : S&P500(D-1) 252-gün tepesinden ≥ %10 aşağıda
 F_gprev_up1, F_gprev_dn1 : Duka altın önceki UTC günü getirisi > +%1 / < −%1
 F_gvol15  : sinyal barı ATR_H1 / önceki 2.000 H1 ATR medyanı ≥ 1,5 (oynaklık rejimi)
 F_g20up   : Duka altın D-1 kapanışı > 20 işlem günü önceki kapanış
 F_mon     : giriş Pazartesi (hafta sonu haber birikimi)
Rastgele-BUY karşılaştırması: aynı geometri (SL 1,5×ATR, TP yok, 20 bar, $0,12) rastgele H1 barlarda → özelliğin
kırılıma mı yoksa genel altın sürüklenmesine/oynaklığına mı ait olduğunu ayırır."""
import os, sys
import numpy as np, pandas as pd
MK = "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"
sys.path.insert(0, MK); sys.dont_write_bytecode = True
from run_main import load_main
from mech import path_sim
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

def daily_gold(d):
    g = d.assign(ud=d.ts.dt.strftime("%Y-%m-%d")).groupby("ud").c.last()
    g.index = pd.to_datetime(g.index); return g

def add_feats(x, d, M, cal, G):
    """x: DataFrame with ent_ts (UTC), sig (H1 idx). Adds ex-ante features."""
    ent = pd.to_datetime(x.ent_ts, utc=True)
    eday = ent.dt.tz_localize(None).dt.normalize()
    mi = M.index.values
    k1 = np.searchsorted(mi, eday.values, side="left") - 1          # son gün < giriş günü
    def at(col, k, lag=0):
        kk = np.clip(k - lag, 0, len(M) - 1); v = M[col].values[kk]; v[k - lag < 0] = np.nan; return v
    ffM = M.ffill()
    vix1 = ffM.vix.values[np.clip(k1, 0, None)]; vix6 = ffM.vix.values[np.clip(k1 - 5, 0, None)]
    dxy1 = ffM.dxy.values[np.clip(k1, 0, None)]; dxy6 = ffM.dxy.values[np.clip(k1 - 5, 0, None)]; dxy21 = ffM.dxy.values[np.clip(k1 - 20, 0, None)]
    ry2 = ffM.ry10.values[np.clip(k1 - 1, 0, None)]; ry22 = ffM.ry10.values[np.clip(k1 - 21, 0, None)]
    spx = ffM.spx; dd = (spx / spx.rolling(252, min_periods=60).max() - 1).values[np.clip(k1, 0, None)]
    x["vix_prev"] = vix1; x["dxy5"] = dxy1 / dxy6 - 1; x["ry20"] = ry2 - ry22; x["spx_dd"] = dd
    x["F_vix20"] = vix1 >= 20; x["F_vix25"] = vix1 >= 25; x["F_vixup"] = vix1 > vix6
    x["F_dxy5dn"] = dxy1 < dxy6; x["F_dxy20dn"] = dxy1 < dxy21; x["F_ry20dn"] = ry2 < ry22
    x["F_spxdd10"] = dd <= -0.10
    gi = G.index.values; kg = np.searchsorted(gi, eday.values, side="left") - 1
    gc = G.values; g1 = gc[np.clip(kg, 0, None)]; g2 = gc[np.clip(kg - 1, 0, None)]; g21 = gc[np.clip(kg - 20, 0, None)]
    x["gprev"] = g1 / g2 - 1
    x["F_gprev_up1"] = x.gprev > 0.01; x["F_gprev_dn1"] = x.gprev < -0.01; x["F_g20up"] = g1 > g21
    atr = d.atr; med = atr.rolling(2000, min_periods=500).median().shift(1)
    x["gvol"] = (atr / med).values[x.sig.values]; x["F_gvol15"] = x.gvol >= 1.5
    x["F_mon"] = ent.dt.dayofweek.values == 0
    major = cal[cal.event.isin(["FOMC", "CPI", "NFP"])]
    evd = set(pd.to_datetime(major.date)); x["F_evday"] = eday.isin(evd).values
    for e in ["FOMC", "CPI", "NFP"]:
        x[f"F_{e.lower()}day"] = eday.isin(set(pd.to_datetime(cal[cal.event == e].date))).values
    t = np.sort(pd.to_datetime(major.ts_utc, utc=True).values.astype("datetime64[ns]"))
    ev_ns = ent.dt.tz_localize(None).values.astype("datetime64[ns]")
    j = np.searchsorted(t, ev_ns, side="left")                         # ilk yayın ≥ giriş
    nxt = t[np.clip(j, 0, len(t) - 1)]; prv = t[np.clip(j - 1, 0, None)]
    x["F_evwin"] = (j < len(t)) & ((nxt - ev_ns) < np.timedelta64(20, "h"))
    x["F_post6"] = (j > 0) & ((ev_ns - prv) <= np.timedelta64(6, "h")) & ((ev_ns - prv) > np.timedelta64(0, "h"))
    return x

def main():
    d = load_main(); M = pd.read_csv(os.path.join(OUT, "macro_daily.csv"), index_col=0, parse_dates=True)
    cal = pd.read_csv(os.path.join(OUT, "calendar.csv")); G = daily_gold(d)
    tr = pd.read_csv(os.path.join(OUT, "trades.csv"))
    tr = add_feats(tr, d, M, cal, G); tr.to_csv(os.path.join(OUT, "trades_feat.csv"), index=False)
    # rastgele BUY (aynı geometri), 40.000 bar
    n = len(d); seg = d.seg.to_numpy(); atr = d.atr.to_numpy()
    ok = np.zeros(n, bool); ok[:-1] = seg[1:] == seg[:-1]; ok &= np.isfinite(atr) & (atr > 0)
    rng = np.random.default_rng(16); s = np.sort(rng.choice(np.where(ok)[0], 40000, replace=False))
    O, H, L, C = (d[k].to_numpy() for k in "ohlc")
    R, xi, code = path_sim(O, H, L, C, seg, s, s + 1, atr[s], np.full(len(s), 20), None, 1.5, +1, 0.12)
    rb = pd.DataFrame({"sig": s, "R": R, "ent_ts": d.ts.values[s + 1]})
    rb["ent_day"] = pd.to_datetime(rb.ent_ts).dt.strftime("%Y-%m-%d"); rb["year"] = pd.to_datetime(rb.ent_ts).dt.year
    rb = add_feats(rb[np.isfinite(rb.R)].reset_index(drop=True), d, M, cal, G)
    rb.to_csv(os.path.join(OUT, "random_feat.csv"), index=False)
    print("ok", len(tr), len(rb), "randomBUY ortR", round(rb.R.mean(), 4))

if __name__ == "__main__":
    main()
