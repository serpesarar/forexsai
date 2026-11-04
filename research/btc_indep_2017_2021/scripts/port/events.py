"""Kol olaylarını üret, 4 maliyet modunda simüle et, kol-içi tek pozisyon zincirini kur, önceki notlarla eşle.
Çıktı: results/trades.pkl  ({kol: DataFrame}), logs/01_events.log"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import lib_st as L
import sleeves as SV

t0 = time.time()
E = SV.engine()


def run(name, ev):
    ev = ev.sort_values("ent").reset_index(drop=True)
    sims = {}
    for md in ("base", "stress", "abs", "opt"):
        sims[md] = E.simulate(ev.ent, ev.dir, ev.sl_d, ev.tp_d, ev.end, ev.sig, mode=md, slip=(md != "opt"))
    b = sims["base"]
    df = ev.copy()
    rescale = df.sl_d.to_numpy() / df.R_den.to_numpy()
    df["R"] = b.R.to_numpy() * rescale
    for md, c in (("stress", "R_st"), ("abs", "R_abs"), ("opt", "R_opt")):
        df[c] = sims[md].R.to_numpy() * rescale
    for c in ("bp", "typ", "ent_t", "ext_t", "samebar", "nights"):
        df[c] = b[c].to_numpy()
    df = df[np.isfinite(df.R)].reset_index(drop=True)
    df["split"] = L.split_of(df.ent_t.to_numpy())
    df = df[df.split != ""].reset_index(drop=True)
    keep = L.single_position(df.ent_t.to_numpy().astype(float), df.ext_t.to_numpy())
    df["single"] = False
    df.loc[keep, "single"] = True
    df["sleeve"] = name
    return df


out = {}
for name, (fev, _) in SV.SLEEVES.items():
    ev = fev()
    out[name] = run(name, ev)
    print(f"{name}: olay {len(ev)} → geçerli {len(out[name])} ({time.time()-t0:.0f}s)", flush=True)

# QB dondurulmuş (stopsuz, R = pnl/ATR1h) — yalnız eşleme için
qb = SV.qb_events()
qf = qb.copy()
qf["sl_d"] = 1e9
s = E.simulate(qf.ent, qf.dir, qf.sl_d, qf.tp_d, qf.end, qf.sig, mode="base", slip=False)
pnl = s.R.to_numpy() * 1e9
qbR = pnl / qb.atr1h.to_numpy()
sp = L.split_of(s.ent_t.to_numpy())
okq = np.isfinite(qbR) & (sp != "")
print(f"QB dondurulmuş (stopsuz, R/ATR1h): n {okq.sum()}, ortR {np.mean(qbR[okq]):+.4f}, bp {np.nanmean(s.bp.to_numpy()[okq]):+.2f}")
out["_QB_frozen"] = pd.DataFrame({"ent_t": s.ent_t.to_numpy()[okq], "R": qbR[okq], "bp": s.bp.to_numpy()[okq], "split": sp[okq]})

rows = []
for name, df in out.items():
    if name.startswith("_"):
        continue
    for sset, m0 in (("tüm", np.ones(len(df), bool)), ("tek-poz", df.single.to_numpy())):
        r = {"kol": name, "set": sset}
        for sp_ in ("A", "PERP"):
            m = m0 & (df.split == sp_).to_numpy()
            r[f"{sp_}_n"] = int(m.sum()); r[f"{sp_}_R"] = round(float(df.R[m].mean()), 3) if m.any() else np.nan
        m = m0 & df.split.isin(["A", "PERP"]).to_numpy()
        r["POST_n"] = int(m.sum()); r["POST_R"] = round(float(df.R[m].mean()), 3)
        r["POST_bp"] = round(float(df.bp[m].mean()), 2)
        r["TAM_n"] = int(m0.sum()); r["TAM_R"] = round(float(df.R[m0].mean()), 3)
        r["aynı_bar_POST_%"] = round(100 * float(df.samebar[m].mean()), 2)
        rows.append(r)
tab = pd.DataFrame(rows)
print(tab.to_string())
tab.to_csv(L.RES / "sleeve_reproduction.csv", index=False)
pd.to_pickle(out, L.RES / "trades.pkl")
print(f"bitti {time.time()-t0:.0f}s")
