"""SL vuran işlemlerin otopsisi (orijinal geometri): SL'den önce lehte en fazla kaç ATR gidildi ve SL'den
SONRA fiyat orijinal TP'ye / girişe döndü mü ("stop dar mıydı?"). Çıktı: results/sl_autopsy.txt"""
import numpy as np
import pandas as pd
import core

HERE = core.HERE
A = pd.read_pickle(HERE / "data" / "grid_set.pkl")
P = core.Paths(core.load_1m())
L = []
rows = []
for x in A[A.sim_outcome == "LOSS"].itertuples(index=False):
    w = P.window(int(x.path_i0), core.MAX_HOLD_MIN)
    h, l, c, t = P.h[w], P.l[w], P.c[w], P.t[w]
    fav, adv, _ = core.fav_adv(x.direction, x.entry_price, x.spread_used, h, l, c)
    ksl = int(np.argmax(adv >= x.orig_sl_usd))
    mfe_pre = fav[:ksl].max() if ksl > 0 else 0.0
    post = slice(ksl + 1, None)
    tpost = t[post]
    def reached(level, H):
        k = int(np.searchsorted(tpost, t[ksl] + np.timedelta64(H, "m")))
        return bool(np.any(fav[post][:k] >= level))
    rows.append({"dir": x.direction, "rr": round(x.j_rr, 2), "mfe_pre_atr": mfe_pre / x.atr_m5,
                 "sl_min": (t[ksl] - t[0]).astype("timedelta64[m]").astype(int) + 1,
                 "back_to_entry_240": reached(0.0, 240), "orig_tp_after_240": reached(x.orig_tp_usd, 240),
                 "orig_tp_after_48h": reached(x.orig_tp_usd, 48 * 60)})
D = pd.DataFrame(rows)
for (d, rr), g in D.groupby(["dir", "rr"]):
    L.append(f"{d} rr{rr} LOSS n={len(g)}: SL'e kadar medyan {g.sl_min.median():.0f} dk (≤5dk: {np.mean(g.sl_min<=5):.0%}, ≤15dk: {np.mean(g.sl_min<=15):.0%}) | "
             f"SL öncesi lehte ≥0.25ATR {np.mean(g.mfe_pre_atr>=.25):.0%} ≥0.5ATR {np.mean(g.mfe_pre_atr>=.5):.0%} ≥0.75ATR {np.mean(g.mfe_pre_atr>=.75):.0%} (medyan {g.mfe_pre_atr.median():.2f}) | "
             f"SL sonrası 240dk'da girişe dönüş {g.back_to_entry_240.mean():.0%}, orijinal TP'ye ulaşma {g.orig_tp_after_240.mean():.0%} (48s: {g.orig_tp_after_48h.mean():.0%})")
W = A[A.sim_outcome == "WIN"]
for d, g in W.groupby("direction"):
    L.append(f"{d} WIN n={len(g)}: TP'ye medyan {g.sim_hold_min.median():.0f} dk (≤5dk {np.mean(g.sim_hold_min<=5):.0%}); TP öncesi aleyhte (ATR) medyan "
             f"{(g.mae_before_exit_R*g.orig_sl_atr5).median():.2f}, ≥0.5ATR {np.mean(g.mae_before_exit_R*g.orig_sl_atr5>=.5):.0%}, ≥0.75ATR {np.mean(g.mae_before_exit_R*g.orig_sl_atr5>=.75):.0%}, ≥1.0ATR {np.mean(g.mae_before_exit_R*g.orig_sl_atr5>=1.0):.0%}")
(HERE / "results" / "sl_autopsy.txt").write_text("\n".join(L))
print("\n".join(L))
