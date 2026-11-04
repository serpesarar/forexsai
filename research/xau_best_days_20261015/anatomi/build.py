"""XAU R0B_G1 (MK-04) en iyi günler anatomisi — ADIM 1: işlem + özellik tablosu.
mekanik/ dosyalarına DOKUNMAZ; yalnız import eder. Çıktı: results/trades.parquet, results/d1.parquet
Gün = giriş barının UTC takvim günü. EX-ANTE özellikler yalnız sinyal barı kapanışında bilinenler
(kapanmış D1/W1 barları; H1 sinyal barı dahil). Ön ek: xa_ = ex-ante, xp_ = ex-post."""
from __future__ import annotations
import os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
MK = "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"
sys.path.insert(0, MK)
import run_main
from run_main import load_main, sim_cell
from rules import events, GEOM
from mech import one_position

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
SPREAD = 0.12
END = os.environ.get("END")  # holdout uzatması için (ör. 2026-10-01)
if END:
    run_main.END_MAIN = pd.Timestamp(END, tz="UTC")


def d1_frame(d: pd.DataFrame) -> pd.DataFrame:
    """UTC takvim günü D1; Cmt/Paz UTC barları (Pazar 22-23 açılış) sonraki Pazartesiye katılır."""
    ts = d.ts
    td = ts.dt.tz_convert(None).dt.normalize()
    wd = td.dt.weekday
    td = td + pd.to_timedelta(np.where(wd >= 5, 7 - wd, 0), unit="D")
    d["tday"] = td
    D = d.groupby("tday").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"),
                              v=("v", "sum"), n=("ts", "size"))
    D = D[D.n >= 4].copy()
    pc = D.c.shift(1)
    tr = np.maximum(D.h - D.l, np.maximum((D.h - pc).abs(), (D.l - pc).abs()))
    D["atr"] = tr.rolling(14).mean()
    D["atrp"] = D.atr / D.c
    D["atrp_pct252"] = D.atrp.rolling(252, min_periods=120).rank(pct=True)
    D["ema50"] = D.c.ewm(span=50, adjust=False, min_periods=50).mean()
    D["ema200"] = D.c.ewm(span=200, adjust=False, min_periods=200).mean()
    D["ema50_slope10"] = (D.ema50 - D.ema50.shift(10)) / D.atr
    D["ath"] = D.h.cummax()
    D["hi252"] = D.h.rolling(252, min_periods=60).max()
    D["ret1"] = D.c.pct_change()
    D["ret5"] = D.c.pct_change(5); D["ret20"] = D.c.pct_change(20)
    D["gap_atr"] = (D.o - pc) / D.atr.shift(1)
    D["range_atr"] = (D.h - D.l) / D.atr.shift(1)          # ex-post (o günün aralığı / dünkü ATR)
    D["ret_atr"] = (D.c - pc) / D.atr.shift(1)
    for k in (1, 3, 5):
        D[f"fwd{k}"] = D.c.shift(-k) / D.c - 1
    # haftalık (ISO hafta, Pazartesi), kapanmış haftalar
    W = D.groupby(D.index.to_period("W-SUN")).agg(c=("c", "last"), end=("c", lambda s: s.index[-1]))
    W["ema20"] = W.c.ewm(span=20, adjust=False, min_periods=20).mean()
    W["ema50"] = W.c.ewm(span=50, adjust=False, min_periods=50).mean()
    D["wk"] = D.index.to_period("W-SUN")
    return D, W


def main() -> None:
    d = load_main()
    raw = pd.read_parquet(os.path.join(MK, "data", "duka_h1.parquet"), columns=["ts", "v"])
    raw["ts"] = pd.to_datetime(raw.ts, utc=True)
    d["v"] = d.ts.map(raw.set_index("ts").v).astype(float).to_numpy()
    D, W = d1_frame(d)
    ev = events(d, "R0", +1); tp, sl, hold = GEOM["R0"][0]
    R, xi, code, hl = sim_cell(d, ev, tp, sl, hold, +1, SPREAD)
    m = np.isfinite(R)
    # tüm-olay (örtüşmeli) seti de sakla — mutabakat için
    allev = ev[m].copy(); allev["R"] = R[m]; allev["xi"] = xi[m]; allev["code"] = code[m]
    allev["edate"] = d.ts.dt.strftime("%Y-%m-%d").to_numpy()[allev.ent]
    allev.to_parquet(os.path.join(OUT, "all_events.parquet"))
    k = one_position(ev.ent.to_numpy()[m], xi[m])
    T = allev[k].reset_index(drop=True)
    O, H, L, C, V = (d[c].to_numpy() for c in ("o", "h", "l", "c", "v"))
    atr = d.atr.to_numpy(); ts = d.ts; tday = d.tday.to_numpy()
    sig, ent, x = T.sig.to_numpy(), T.ent.to_numpy(), T.xi.to_numpy()
    entry = O[ent] + SPREAD; unit = 1.5 * T.atr.to_numpy()
    T["ent_ts"] = ts.to_numpy()[ent]
    T["eday"] = ts.dt.strftime("%Y-%m-%d").to_numpy()[ent]
    T["eday_ny"] = d.day.to_numpy()[ent]
    T["tday"] = tday[ent]
    T["ent_hour"] = ts.dt.hour.to_numpy()[ent]
    T["weekday"] = ts.dt.weekday.to_numpy()[ent]
    # ---- yol / ex-post ----
    mfe, mae, r_d0, held, pex, atr_real, maxc_at = [], [], [], [], [], [], []
    for i in range(len(T)):
        a, b = ent[i], x[i]
        mfe.append((H[a:b + 1].max() - entry[i]) / unit[i]); mae.append((L[a:b + 1].min() - entry[i]) / unit[i])
        same = np.where(tday[a:b + 1] == tday[a])[0]
        lastsame = a + same[-1]
        r_d0.append(T.R[i] if lastsame >= b else (C[lastsame] - entry[i]) / unit[i])
        held.append(b - a + 1)
        e2 = min(b + 20, len(C) - 1)
        pex.append((C[e2] - C[b]) / unit[i])
        trr = (H[a:b + 1] - L[a:b + 1]).mean()
        atr_real.append(trr / T.atr[i])
        maxc_at.append(C[b] >= C[a:b + 1].max() - 1e-9)
    T["xp_mfe_R"] = mfe; T["xp_mae_R"] = mae; T["xp_R_day0"] = r_d0; T["xp_held"] = held
    T["xp_post20_R"] = pex; T["xp_vol_expand"] = atr_real; T["xp_exit_at_maxclose"] = maxc_at
    T["xp_giveback_R"] = T.xp_mfe_R - T.R
    # ---- ex-ante: kırılım barı ----
    hs = pd.Series(H); ls = pd.Series(L)
    lvl = hs.rolling(20).max().shift(1).to_numpy(); low20 = ls.rolling(20).min().shift(1).to_numpy()
    T["xa_pen_high_atr"] = (H[sig] - lvl[sig]) / atr[sig]
    T["xa_pen_close_atr"] = (C[sig] - lvl[sig]) / atr[sig]
    T["xa_rng20_atr"] = (lvl[sig] - low20[sig]) / atr[sig]
    T["xa_body_atr"] = (C[sig] - O[sig]) / atr[sig]
    T["xa_bar_range_atr"] = (H[sig] - L[sig]) / atr[sig]
    T["xa_body_ratio"] = (C[sig] - O[sig]) / np.maximum(H[sig] - L[sig], 1e-9)
    # seviyenin yaşı (önceki 20 bar içinde max'ın kaç bar önce olduğu)
    age = np.array([20 - int(np.argmax(H[s - 20:s][::-1][::-1])) for s in sig])  # 1..20
    T["xa_level_age"] = age
    # önceki 20-tepe olayından bu yana bar (olay = h ≥ önceki 20 tepe)
    isev = np.zeros(len(H), bool); isev[ev.sig.to_numpy()] = True
    evidx = np.where(isev)[0]
    pos = np.searchsorted(evidx, sig)
    prev = np.where(pos > 0, evidx[np.clip(pos - 1, 0, None)], -10 ** 6)
    T["xa_bars_since_prev_brk"] = np.minimum(sig - prev, 500)
    T["xa_brk_density24"] = [isev[s - 24:s].sum() for s in sig]
    # BB genişliği yüzdeliği (önceki 120 / 500 bar) — sinyal barı ÖNCESİ kapanışla
    cs = pd.Series(C); mid = cs.rolling(20).mean(); sd = cs.rolling(20).std(ddof=0); bw = 4 * sd / mid
    bwp120 = bw.shift(1).rolling(120).rank(pct=True).to_numpy(); bwp500 = bw.shift(1).rolling(500).rank(pct=True).to_numpy()
    T["xa_bbw_pct120"] = bwp120[sig]; T["xa_bbw_pct500"] = bwp500[sig]
    T["xa_atrH1_pct500"] = pd.Series(atr).rolling(500).rank(pct=True).to_numpy()[sig]
    # hacim: aynı UTC saatin önceki 20 gözlem medyanı
    uh = d.utc_h.to_numpy()
    vmed = pd.Series(V).groupby(uh).transform(lambda s: s.shift(1).rolling(20, min_periods=10).median()).to_numpy()
    T["xa_vol_ratio_hour"] = V[sig] / vmed[sig]
    vmed100 = pd.Series(V).shift(1).rolling(100).median().to_numpy()
    T["xa_vol_ratio_100"] = V[sig] / vmed100[sig]
    T["xa_spread"] = d.spr.to_numpy()[sig]
    T["xa_shock24_atr"] = [np.max(np.abs(C[s - 23:s + 1] - O[s - 23:s + 1])) / atr[s] for s in sig]
    T["xa_hour_sig"] = uh[sig]
    sess = np.select([(uh[sig] >= 7) & (uh[sig] < 13), (uh[sig] >= 13) & (uh[sig] < 21)], ["Londra", "NY"], "Asya")
    T["xa_session"] = sess
    # ---- ex-ante: D1/W1 (yalnız kapanmış) ----
    Di = D.index.to_numpy()
    sday = tday[sig]
    kd = np.searchsorted(Di, sday, side="left") - 1          # sinyal gününden ÖNCEKİ son kapanmış gün
    ok = kd >= 0
    def col(c):
        v = D[c].to_numpy(); return np.where(ok, v[np.clip(kd, 0, None)], np.nan)
    atrD = col("atr"); cD = col("c")
    T["xa_atrD1"] = atrD
    T["xa_atrD1p_pct252"] = col("atrp_pct252")
    T["xa_atrH1_over_D1"] = atr[sig] / atrD
    T["xa_d1_above_ema50"] = (cD > col("ema50")).astype(float)
    T["xa_d1_above_ema200"] = (cD > col("ema200")).astype(float)
    T["xa_ema50_gt_200"] = (col("ema50") > col("ema200")).astype(float)
    T["xa_ema50_slope10"] = col("ema50_slope10")
    T["xa_dist_ath_atr"] = (C[sig] - col("ath")) / atrD
    T["xa_dist_ath_pct"] = C[sig] / col("ath") - 1
    T["xa_dist_52wh_atr"] = (C[sig] - col("hi252")) / atrD
    T["xa_ret5"] = col("ret5"); T["xa_ret20"] = col("ret20")
    T["xa_intraday_atr"] = (C[sig] - cD) / atrD     # bugün sinyale kadar
    # bugünün açılış boşluğu (sinyal günü açıldıysa bilinir)
    dopen = pd.Series(D.o.to_numpy(), index=Di)
    kt = np.searchsorted(Di, sday, side="left")
    okt = (kt < len(Di)) & (Di[np.clip(kt, 0, len(Di) - 1)] == sday)
    T["xa_gap_atr"] = np.where(ok & okt, (D.o.to_numpy()[np.clip(kt, 0, len(Di) - 1)] - cD) / atrD, np.nan)
    # W1: sinyal haftasından önceki kapanmış hafta
    wk_sig = pd.PeriodIndex(pd.to_datetime(sday), freq="W-SUN")
    wpos = np.searchsorted(W.index.to_numpy(), wk_sig.to_numpy(), side="left") - 1
    okw = wpos >= 0
    wc = np.where(okw, W.c.to_numpy()[np.clip(wpos, 0, None)], np.nan)
    T["xa_w1_above_ema20"] = (wc > np.where(okw, W.ema20.to_numpy()[np.clip(wpos, 0, None)], np.nan)).astype(float)
    T["xa_w1_above_ema50"] = (wc > np.where(okw, W.ema50.to_numpy()[np.clip(wpos, 0, None)], np.nan)).astype(float)
    # ---- ex-post: giriş gününün D1 hareketi ----
    ke = np.searchsorted(Di, tday[ent], side="left")
    oke = (ke < len(Di)) & (Di[np.clip(ke, 0, len(Di) - 1)] == tday[ent])
    for c in ("ret1", "ret_atr", "range_atr", "fwd1", "fwd3", "fwd5"):
        v = D[c].to_numpy(); T["xp_day_" + c] = np.where(oke, v[np.clip(ke, 0, len(Di) - 1)], np.nan)
    # tüm örneklem ATR yüzdeliği (ex-post, betimsel)
    T["xp_atrD1p_pct_full"] = np.where(ok, D.atrp.rank(pct=True).to_numpy()[np.clip(kd, 0, None)], np.nan)
    T.to_parquet(os.path.join(OUT, "trades.parquet" if not END else "trades_ext.parquet"))
    D.drop(columns=["wk"]).to_parquet(os.path.join(OUT, "d1.parquet" if not END else "d1_ext.parquet"))
    print(len(T), T.R.sum(), T.R.mean(), (T.R > 0).mean())


if __name__ == "__main__":
    main()
