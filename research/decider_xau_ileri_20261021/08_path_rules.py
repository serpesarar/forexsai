"""Q3 (devam): yol-bağımlı çıkış kuralları — başabaşa çekme (BE), iz-süren stop, kısmi TP.
Tüm seviyeler kapalı-bar ATR5 biriminde; R paydası = başlangıç SL mesafesi. Konservatif sıra
(core.sim_path_rule): aynı barda stop+hedef → stop; stop yalnız ÖNCEKİ barların ekstremumuyla güncellenir.
Çıktı: results/path_rules_<grup>.csv + data/path_cache.npz"""
import numpy as np
import pandas as pd
import core, grid_lib as G

HERE = core.HERE; OUT = HERE / "results"
A = pd.read_pickle(HERE / "data" / "grid_set.pkl")
P = core.Paths(core.load_1m())
BIG = 1e9
VARIANTS = []   # (ad, tp_atr|None=orijinal, sl_atr|None=orijinal, kwargs(ATR biriminde))
for base, tp, sl in (("orij", None, None), ("tp1.25/sl0.75", 1.25, 0.75), ("tp2.0/sl1.5", 2.0, 1.5)):
    VARIANTS.append((f"{base} sabit", tp, sl, {}))
    for be in (0.25, 0.5, 0.75):
        VARIANTS.append((f"{base} +BE@{be}ATR", tp, sl, {"be_trig": be}))
for d in (0.5, 1.0, 1.5):
    for act in (0.0, 0.5, 1.0):
        VARIANTS.append((f"sl1.5 iz-stop d{d} akt{act} (TP yok)", BIG, 1.5, {"trail_d": d, "trail_act": act}))
for pt in (0.5, 0.75):
    for tp in (1.5, 2.0, 3.0):
        for be in (False, True):
            VARIANTS.append((f"sl1.5 kısmi50%@{pt} kalan@{tp}{' +BE' if be else ''}", tp, 1.5,
                             {"partial_tp": pt, **({"be_trig": 0.0} if be else {})}))

res = np.full((len(A), len(VARIANTS)), np.nan); risk = np.full_like(res, np.nan)
for n, x in enumerate(A.itertuples(index=False)):
    w = P.window(int(x.path_i0), core.MAX_HOLD_MIN)
    h, l, c = P.h[w], P.l[w], P.c[w]
    a = x.atr_m5
    for k, (_, tp, sl, kw) in enumerate(VARIANTS):
        tp_d = x.orig_tp_usd if tp is None else (BIG if tp >= BIG else tp * a)
        sl_d = x.orig_sl_usd if sl is None else sl * a
        kk = {kname: (v * a if kname in ("be_trig", "trail_d", "trail_act", "partial_tp") and v not in (0.0,) else v)
              for kname, v in kw.items()}
        res[n, k] = core.sim_path_rule(x.direction, x.entry_price, x.spread_used, h, l, c, tp_d, sl_d, **kk)
        risk[n, k] = sl_d
np.savez_compressed(HERE / "data" / "path_cache.npz", pnl=res, risk=risk, names=np.array([v[0] for v in VARIANTS]))
L = []
for gname, m in {"BUY": A.direction == "BUY", "SELL": A.direction == "SELL", "BUY_exec": A.executed}.items():
    idx = np.where(m.values)[0]
    st = G.summarize(res[idx], risk[idx], A.day.values[idx])
    T = pd.DataFrame({k: np.asarray(v) for k, v in st.items()}); T.insert(0, "variant", [v[0] for v in VARIANTS])
    T.to_csv(OUT / f"path_rules_{gname}.csv", index=False)
    L.append(f"\n=== {gname} n={len(idx)}")
    L.append(T[["variant", "WR", "EV_R", "R_lo", "R_hi", "P_R_gt0", "EV_usd", "usd_lo", "usd_hi"]].round(3).to_string(index=False))
(OUT / "path_rules_summary.txt").write_text("\n".join(L))
print("\n".join(L))
