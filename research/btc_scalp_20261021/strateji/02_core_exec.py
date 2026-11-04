"""Core (BTC-T03) için 'scalp-icra' ızgarası (prereg §4): limit geri-çekilme girişi k×ATR5m, W dk, dolmazsa skip/market.
Seçim yalnız DISC (sinyal başı ort R, skip=0; benimseme eşiği +0,02R). Çıktı: results/core_exec_grid.csv, core_exec_choice.json"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
import lib_st as L
import sleeves as SV

t0 = time.time()
E = SV.engine()
G = SV.scalp_grid()
ev = SV.core_events().sort_values("ent").reset_index(drop=True)
eidx = (ev.ent.to_numpy() - L.T0M)
atr5 = G["atr5bp"][eidx] * 1e-4 * G["open"][eidx]
print(f"Core olay {len(ev)}; ATR5m medyan {np.nanmedian(G['atr5bp'][eidx]):.1f} bp; SL medyan {np.nanmedian(ev.sl_d/ev.sig*1e4):.0f} bp")

mk = E.simulate(ev.ent, ev.dir, ev.sl_d, ev.tp_d, ev.end, ev.sig, mode="base")
split = L.split_of(mk.ent_t.to_numpy())
valid = np.isfinite(mk.R.to_numpy()) & (split != "")
VAR = [("MARKET", None, 0, "skip")] + [(f"k{k}_W{w}_{fb}", k, w, fb) for k in (0.25, 0.5) for w in (15, 60) for fb in ("skip", "market")]
rows, store = [], {}
for name, k, w, fb in VAR:
    if k is None:
        s = mk
    else:
        s = E.simulate(ev.ent, ev.dir, ev.sl_d, ev.tp_d, ev.end, ev.sig, mode="base", limit_k=k * atr5, limit_W=w, limit_fallback=fb)
    R = s.R.to_numpy()
    traded = np.isfinite(R) & valid
    Rsig = np.where(traded, R, 0.0)
    filled = s.filled.to_numpy() & valid
    store[name] = s
    for sp in ("DISC", "POST", "TAM"):
        m = valid & ((split == sp) if sp == "DISC" else (np.isin(split, ["OOS", "BLIND"]) if sp == "POST" else True))
        nsig = int(m.sum())
        r = {"hücre": name, "dönem": sp, "sinyal": nsig, "işlem": int((traded & m).sum()),
             "dolum_%": round(100 * (filled & m).sum() / nsig, 1) if k is not None else 100.0,
             "R_sinyal_başı": round(float(Rsig[m].mean()), 4), "R_işlem_başı": round(float(R[traded & m].mean()), 4)}
        if k is not None:
            mR = mk.R.to_numpy()
            r["piyasaR_dolan"] = round(float(np.nanmean(mR[m & filled])), 4) if (m & filled).any() else np.nan
            r["piyasaR_dolmayan"] = round(float(np.nanmean(mR[m & ~filled])), 4) if (m & ~filled).any() else np.nan
            r["limitR_dolan"] = round(float(np.nanmean(R[m & filled])), 4) if (m & filled).any() else np.nan
            r["dolan_iyileşme_R"] = round(r["limitR_dolan"] - r["piyasaR_dolan"], 4) if (m & filled).any() else np.nan
        # tek pozisyon zinciri
        tm = traded & m
        ent_t, ext_t = s.ent_t.to_numpy()[tm].astype(float), s.ext_t.to_numpy()[tm]
        kp = L.single_position(ent_t, ext_t)
        r["tekpoz_n"] = len(kp)
        r["tekpoz_R"] = round(float(R[tm][kp].mean()), 4) if len(kp) else np.nan
        rows.append(r)
tab = pd.DataFrame(rows)
tab.to_csv(L.RES / "core_exec_grid.csv", index=False)
print(tab.to_string())
d = tab[tab["dönem"] == "DISC"].set_index("hücre")["R_sinyal_başı"]
base = d["MARKET"]
cand = d.drop("MARKET")
best = cand.idxmax()
choice = best if cand[best] - base >= 0.02 else "MARKET"
res = {"DISC_market_R_sinyal": float(base), "DISC_en_iyi_limit": best, "DISC_en_iyi_R": float(cand[best]),
       "fark": float(cand[best] - base), "benimsenen": choice}
json.dump(res, open(L.RES / "core_exec_choice.json", "w"), indent=1)
print(res, f"{time.time()-t0:.0f}s")
