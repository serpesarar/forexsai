"""PROTOCOL §1 kasa: broker 1m 2026-06-17 → 10-14 (mekanik/holdout.py yöntemi, yalnız R0B_G1).
Özellikler: Duka geçmişi + broker H1 ekinde; hacim (F4) yalnız broker tick hacminden (birimler karışmasın).
Çıktı: results/holdout.csv, results/holdout_events.csv"""
import json, os
import numpy as np, pandas as pd
from common import raw_duka, prep_h1, path_sim, one_position, events, RES, MK
from features import raw_features, load_vix, add_f9, FEATS, NAMES

CUT = pd.Timestamp("2026-06-17", tz="UTC"); SPREAD = 0.12
m = pd.read_csv(os.path.join(MK, "..", "data", "xau_1m_utc.csv.gz"))
m["ts"] = pd.to_datetime(m.t_utc, utc=True)
m = m.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"})[["ts", "o", "h", "l", "c", "v"]]
g = m.set_index("ts").resample("1h", label="left", closed="left")
bh = pd.DataFrame({"o": g.o.first(), "h": g.h.max(), "l": g.l.min(), "c": g.c.last(), "v": g.v.sum(), "k": g.o.size()})
bh = bh[bh.k > 0].reset_index()
du = raw_duka(end=CUT).assign(v=np.nan)
sp = pd.concat([du[["ts", "o", "h", "l", "c", "v"]], bh[bh.ts >= CUT][["ts", "o", "h", "l", "c", "v"]]], ignore_index=True)
d = prep_h1(sp)
fe = add_f9(raw_features(d, load_vix()), json.load(open(os.path.join(RES, "params.json")))["thr9"])
ev = events(d, "R0", +1)
hts = d.ts.dt.tz_convert(None).to_numpy()
ev = ev[hts[ev.sig.to_numpy()] >= np.datetime64(CUT.tz_convert(None))].reset_index(drop=True)
T = m.ts.dt.tz_convert(None).to_numpy(); O1, H1, L1, C1 = (m[k].to_numpy() for k in "ohlc")
seg1 = (np.diff(T.astype("datetime64[s]").astype(np.int64), prepend=0) > 3 * 3600).cumsum()
hold = 20
st = hts[ev.ent.to_numpy()]
en = hts[np.clip(ev.ent.to_numpy() + hold - 1, 0, len(hts) - 1)] + np.timedelta64(1, "h")
k = np.searchsorted(T, st); kend = np.searchsorted(T, en)
good = (k < len(T)) & (kend > k)
ev, k, kend = ev[good].reset_index(drop=True), k[good], kend[good]
R1, x1, c1 = path_sim(O1, H1, L1, C1, seg1, np.maximum(k - 1, 0), k, ev.atr.to_numpy(), kend - k, None, 1.5, +1, SPREAD)
ev["R"] = R1; ev["t_ent"] = T[k].astype("datetime64[m]").astype(np.int64); ev["t_exit"] = T[np.clip(x1, 0, len(T) - 1)].astype("datetime64[m]").astype(np.int64)
ev = ev[np.isfinite(ev.R)].reset_index(drop=True)
for f in FEATS:
    ev[f] = fe[f].to_numpy()[ev.sig].astype(bool)
ev["vol_ratio"] = fe.vol_ratio.to_numpy()[ev.sig]; ev["vix_prev"] = fe.vix_prev.to_numpy()[ev.sig]
kb = one_position(ev.t_ent.to_numpy(), ev.t_exit.to_numpy())
base = ev[kb]
rows = [dict(feat="TABAN", name="-", n_raw=len(ev), raw_mean=float(ev.R.mean()), n_1pos=int(kb.sum()), base_1pos=float(base.R.mean()))]
for f in FEATS:
    F = ev[f].to_numpy(); idx = np.where(F)[0]
    kf = one_position(ev.t_ent.to_numpy()[idx], ev.t_exit.to_numpy()[idx])
    Fb = base[f].to_numpy(); rb = base.R.to_numpy()
    rows.append(dict(feat=f, name=NAMES[f], n_raw_F=int(F.sum()), raw_in=float(ev.R[F].mean()) if F.any() else np.nan,
                     raw_out=float(ev.R[~F].mean()), n_filt=int(kf.sum()),
                     filt_mean=float(ev.R.to_numpy()[idx][kf].mean()) if kf.any() else np.nan,
                     d_FILTRE=float(ev.R.to_numpy()[idx][kf].mean() - base.R.mean()) if kf.any() else np.nan,
                     n_1pos_F=int(Fb.sum()), in_1pos=float(rb[Fb].mean()) if Fb.any() else np.nan,
                     out_1pos=float(rb[~Fb].mean()) if (~Fb).any() else np.nan,
                     d_BOYUT2=float(rb[Fb].mean() - rb[~Fb].mean()) if Fb.any() and (~Fb).any() else np.nan))
out = pd.DataFrame(rows); out.to_csv(os.path.join(RES, "holdout.csv"), index=False)
ev.to_csv(os.path.join(RES, "holdout_events.csv"), index=False)
print(out.round(3).to_string())
