"""ADIM 3 (PROTOCOL §6, C4): ileri kanıt. (i) Duka 2026-06-17→09-30 (tek-pozisyon tüm seride yürütülür, sinyal ≥06-17
alınır). (ii) Broker 1m 06-17→10-14 (erken_sinyal 02_holdout.py yöntemi: Duka geçmişi + broker H1 eki, yol 1m).
Çıktı: results/fwd_events.parquet (her iki küme, tüm olaylar + S bayrakları + base), results/c4_forward.csv, results/03_log.txt"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
from common import (load_d, run_rule, add_flags, macro_inputs, one_position, prep_h1, path_sim, events, brk_density,
                    gprev_for, MK, RES, CUT, SPREAD)

M, cal = macro_inputs()
L: list[str] = []
def say(s=""):
    L.append(str(s)); print(s)

# (i) Duka uzatması
dx = load_d(end="2026-10-01")
ex = add_flags(run_rule(dx), cal)
ex["base"] = one_position(ex.ent.to_numpy(), ex.xi.to_numpy())
tn = dx.ts.dt.tz_convert(None).to_numpy()
ex["t_ent"] = tn[ex.ent].astype("datetime64[ns]").astype(np.int64)
ex["t_exit"] = tn[ex.xi].astype("datetime64[ns]").astype(np.int64)
ex = ex[tn[ex.sig] >= np.datetime64(CUT.tz_convert(None))].reset_index(drop=True)
ex["set"] = "duka_ext"
say(f"Duka uzatması: olay {len(ex)}, tek-poz {ex.base.sum()} ortR {ex.R[ex.base].mean():+.4f} toplam {ex.R[ex.base].sum():+.1f}")

# (ii) broker 1m kasası
m = pd.read_csv(os.path.join(MK, "..", "data", "xau_1m_utc.csv.gz"))
m["ts"] = pd.to_datetime(m.t_utc, utc=True)
m = m.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c"})[["ts", "o", "h", "l", "c"]]
g = m.set_index("ts").resample("1h", label="left", closed="left")
bh = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "k": g.o.size()})
bh = bh[bh.k > 0].reset_index()
du = pd.read_parquet(os.path.join(MK, "data", "duka_h1.parquet")); du["ts"] = pd.to_datetime(du.ts, utc=True)
sp = pd.concat([du[du.ts < CUT][["ts", "o", "h", "l", "c"]], bh[bh.ts >= CUT][["ts", "o", "h", "l", "c"]]], ignore_index=True)
sp["spr"] = np.nan
d = prep_h1(sp)
ev = events(d, "R0", +1)
hts = d.ts.dt.tz_convert(None).to_numpy()
ev = ev[hts[ev.sig.to_numpy()] >= np.datetime64(CUT.tz_convert(None))].reset_index(drop=True)
T = m.ts.dt.tz_convert(None).to_numpy(); O1, H1, L1, C1 = (m[k].to_numpy() for k in "ohlc")
seg1 = (np.diff(T.astype("datetime64[s]").astype(np.int64), prepend=0) > 3 * 3600).cumsum()
st = hts[ev.ent.to_numpy()]
en = hts[np.clip(ev.ent.to_numpy() + 20 - 1, 0, len(hts) - 1)] + np.timedelta64(1, "h")
k = np.searchsorted(T, st); kend = np.searchsorted(T, en)
good = (k < len(T)) & (kend > k)
ev, k, kend = ev[good].reset_index(drop=True), k[good], kend[good]
R1, x1, c1 = path_sim(O1, H1, L1, C1, seg1, np.maximum(k - 1, 0), k, ev.atr.to_numpy(), kend - k, None, 1.5, +1, SPREAD)
ev["R"] = R1; ev["code"] = c1
ev["t_ent"] = T[k].astype("datetime64[ns]").astype(np.int64); ev["t_exit"] = T[np.clip(x1, 0, len(T) - 1)].astype("datetime64[ns]").astype(np.int64)
ev["ent_ts"] = d.ts.to_numpy()[ev.ent]; ev["ent_day"] = d.ts.dt.strftime("%Y-%m-%d").to_numpy()[ev.ent]
ev["week"] = d.ts.dt.tz_convert(None).dt.to_period("W").astype(str).to_numpy()[ev.ent]
ev["dens24"] = brk_density(d)[ev.sig]; ev["gprev"] = gprev_for(d, ev.ent.to_numpy())
ev = add_flags(ev[np.isfinite(ev.R)].reset_index(drop=True), cal)
ev["base"] = one_position(ev.t_ent.to_numpy(), ev.t_exit.to_numpy())
ev["set"] = "broker_1m"
say(f"Broker 1m kasası: olay {len(ev)}, tek-poz {ev.base.sum()} ortR {ev.R[ev.base].mean():+.4f} toplam {ev.R[ev.base].sum():+.1f}")

cols = ["set", "sig", "ent", "year", "utc_h", "R", "t_ent", "t_exit", "ent_ts", "ent_day", "dens24", "gprev", "base",
        "S1_ge1", "S1_ge2", "S1_ge3", "S2_gt075", "S2_gt100", "S2_gt125", "S3_fomcwin", "S1", "S2", "S12"]
F = pd.concat([ex[cols], ev[cols]], ignore_index=True)
F.to_parquet(os.path.join(RES, "fwd_events.parquet"))

rows = []
for s, X in F.groupby("set"):
    B = X[X.base]
    for flag in ("S1_ge1", "S1_ge2", "S1_ge3", "S2_gt075", "S2_gt100", "S2_gt125", "S12", "S3_fomcwin"):
        Fb = B[flag].to_numpy().astype(bool); r = B.R.to_numpy()
        # filtre: bayraklı olayları at, tek-pozisyonu yeniden yürüt
        keepE = ~X[flag].to_numpy().astype(bool)
        Xf = X[keepE]
        kf = one_position(Xf.t_ent.to_numpy(), Xf.t_exit.to_numpy())
        rows.append(dict(set=s, flag=flag, n_base=len(B), n_on=int(Fb.sum()),
                         R_in=float(r[Fb].mean()) if Fb.any() else np.nan, R_out=float(r[~Fb].mean()) if (~Fb).any() else np.nan,
                         d=float(r[Fb].mean() - r[~Fb].mean()) if Fb.any() and (~Fb).any() else np.nan,
                         P3_in=float((r[Fb] >= 3).mean()) if Fb.any() else np.nan, P3_out=float((r[~Fb] >= 3).mean()),
                         base_ortR=float(r.mean()), base_totR=float(r.sum()),
                         filt_n=int(kf.sum()), filt_ortR=float(Xf.R.to_numpy()[kf].mean()), filt_totR=float(Xf.R.to_numpy()[kf].sum()),
                         in_days=", ".join(sorted(set(B.ent_day[Fb])))[:200] if flag == "S3_fomcwin" else ""))
out = pd.DataFrame(rows); out.to_csv(os.path.join(RES, "c4_forward.csv"), index=False)
say(out.drop(columns="in_days").round(3).to_string(index=False))
say("S3 FOMC penceresindeki ileri işlemler: " + "; ".join(f"{r.set}: {r.in_days}" for r in out[out.flag == 'S3_fomcwin'].itertuples()))
# en iyi/ en kötü işlemler bayraklarla
for s, X in F.groupby("set"):
    B = X[X.base].sort_values("R", ascending=False)
    say(f"\n[{s}] en iyi 8 işlem: " + " | ".join(f"{r.ent_day} R={r.R:+.2f} S1={int(r.S1)} S2={int(r.S2)}" for r in B.head(8).itertuples()))
open(os.path.join(RES, "03_log.txt"), "w").write("\n".join(L) + "\n")
