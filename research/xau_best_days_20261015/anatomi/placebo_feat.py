"""ADIM 5: aday ex-ante koşullar kurala mı özgü, yoksa altının genel davranışı mı? Her H1 barından rastgele-BUY (aynı geometri:
SL 1.5×ATR_H1, TP yok, 20 bar, sonraki açılış + $0.12) ortR'si aynı koşullarla. + yıl-içi fark oranı (yalnız iki tarafın da olduğu yıllar)."""
import os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
MK = "/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/mekanik"; sys.path.insert(0, MK)
from run_main import load_main
from rules import events
from mech import path_sim, day_t
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
d = load_main()
O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy(); atr = d.atr.to_numpy(); n = len(d)
sig = np.arange(25, n - 1); ent = sig + 1
ok = (seg[ent] == seg[sig]) & np.isfinite(atr[sig]) & (atr[sig] > 0); sig, ent = sig[ok], ent[ok]
R, xi, code = path_sim(O, H, L, C, seg, sig, ent, atr[sig], np.full(len(sig), 20), None, 1.5, +1, 0.12)
B = pd.DataFrame({"sig": sig, "R": R}).dropna()
ev = events(d, "R0", +1); isev = np.zeros(n, bool); isev[ev.sig.to_numpy()] = True
cs = np.concatenate([[0], np.cumsum(isev)])
B["dens"] = cs[B.sig] - cs[np.maximum(B.sig - 24, 0)]          # önceki 24 bar (sinyal barı hariç)
B["is_brk"] = isev[B.sig]
# ATH (kapanmış UTC günleri)
D = pd.read_parquet(os.path.join(RES, "d1.parquet")); Di = pd.to_datetime(D.index).to_numpy()
ts = d.ts.dt.tz_convert(None).dt.normalize(); wd = ts.dt.weekday
td = (ts + pd.to_timedelta(np.where(wd >= 5, 7 - wd, 0), unit="D")).to_numpy()
kd = np.searchsorted(Di, td[B.sig], side="left") - 1
B["ath"] = np.where(kd >= 0, D.ath.to_numpy()[np.clip(kd, 0, None)], np.nan)
B["near_ath"] = C[B.sig] / B.ath - 1 >= -0.02
B["uh"] = d.utc_h.to_numpy()[B.sig]; B["asia"] = (B.uh >= 23) | (B.uh <= 6)
B["yr"] = d.year.to_numpy()[B.sig]; B["half"] = np.where(B.yr <= 2016, "08-16", "17-26")
B["atrp"] = pd.Series(atr).rolling(500).rank(pct=True).to_numpy()[B.sig]
L = []
def say(s): L.append(s); print(s)
say(f"Tüm barlar rastgele-BUY ortR {B.R.mean():+.4f} (n={len(B)}); kural olay barları {B.R[B.is_brk].mean():+.4f}; olmayan {B.R[~B.is_brk].mean():+.4f}")
def tab(name, cond):
    for grp, sub in (("KURAL", B[B.is_brk]), ("TÜM BAR", B)):
        c = cond(sub)
        diff = sub.R[c].mean() - sub.R[~c].mean()
        hv = [sub.R[c & (sub.half == h)].mean() - sub.R[~c & (sub.half == h)].mean() for h in ("08-16", "17-26")]
        y = sub.groupby(["yr", c]).R.mean().unstack().dropna()
        yp = ((y[True] - y[False]) > 0).mean() if len(y) else np.nan
        say(f"{name:<34} {grp:<7} in {sub.R[c].mean():+.3f} (n={c.sum()}) out {sub.R[~c].mean():+.3f} fark {diff:+.3f} | yarılar {hv[0]:+.3f}/{hv[1]:+.3f} | fark>0 yıl {yp:.2f} ({len(y)} yıl)")
tab("seri kırılım (önceki 24 barda ≥2)", lambda s: s.dens >= 2)
tab("ATH'ye ≤%2", lambda s: s.near_ath)
tab("tekil (≤1) ∧ ATH≤%2", lambda s: (s.dens <= 1) & s.near_ath)
tab("Asya saati (23-06 UTC)", lambda s: s.asia)
tab("ATR_H1 500-bar yüzd. ≤0.2", lambda s: s.atrp <= 0.2)
# kural farkı - plasebo farkı: tekil∧ATH koşulunda kural barı vs aynı koşullu rastgele bar
c = (B.dens <= 1) & B.near_ath
say(f"Koşul tekil∧ATH≤%2 içinde: kural barı {B.R[c & B.is_brk].mean():+.3f} (n={(c & B.is_brk).sum()}) vs kural-dışı bar {B.R[c & ~B.is_brk].mean():+.3f} (n={(c & ~B.is_brk).sum()})")
T = pd.read_parquet(os.path.join(RES, "trades.parquet"))
T["yr"] = pd.to_datetime(T.eday).dt.year
cc = (T.xa_brk_density24 <= 1) & (T.xa_dist_ath_pct >= -0.02)
say("Tek-poz tekil∧ATH≤%2 yıl bazında (n, ortR): " + ", ".join(f"{y}:{g.size}/{g.mean():+.2f}" for y, g in T.R[cc].groupby(T.yr[cc])))
say(f"   gün-kümeli t={day_t(T.R[cc].to_numpy(), T.eday[cc].to_numpy()):.2f}; en iyi 3 işlem hariç ortR {np.sort(T.R[cc].to_numpy())[:-3].mean():+.3f}; medyan {T.R[cc].median():+.2f}; WR {(T.R[cc]>0).mean():.3f}")
open(os.path.join(RES, "placebo_features.txt"), "w").write("\n".join(L) + "\n")
