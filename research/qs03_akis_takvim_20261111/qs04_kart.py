"""QS-04 kartlar: E2-uzun tek başına ve 'ay sonu döngüsü' (R1 iki bacak + E2 uzun) — 2. KURAL 6 ölçüt.
Hacim/beklenti/kararlılık QQQ 2002-26; sürtünme/icra broker NAS100 2018-26 (iyimser 16:00, gerçek 16:30 ET)."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import monthly, side, TH, COST

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402


def leg_broker(M, cal, sd, col, n_days, hh, mm, stress=1.0):
    mk = Mkt("NAS100", stress=stress); out = {}
    for k, r in M.iterrows():
        if sd[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        p = cal.get_loc(r[col]); off = pd.Timedelta(hours=hh, minutes=mm)
        i, j = mk.at(cal[p] + off), mk.at(cal[p + n_days] + off)
        if i < 0 or j < 0 or j <= i:
            continue
        out[(r.m, col)] = sd[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j])
    return pd.Series(out, dtype=float)


def card(qqq_trades: np.ndarray, legs_opt: list, legs_real: list, legs_stress: list, name: str) -> dict:
    v = qqq_trades; h = len(v) // 2
    opt, real, strs = (pd.concat(x) for x in (legs_opt, legs_real, legs_stress))
    c = {"1_hacim": {"n_QQQ": int(len(v)), "n_broker": int(len(real)), "gecti": bool(len(v) >= 150)},
         "2_beklenti": st(v) | {"gecti": bool(v.mean() > 0 and st(v)["P"] >= .9)},
         "3_kararlilik": {"yari1": round(float(v[:h].mean()), 1), "yari2": round(float(v[h:].mean()), 1), "gecti": bool(min(v[:h].mean(), v[h:].mean()) >= 0)},
         "4_surtunme": {"broker_x1.5": st(strs.to_numpy()), "gecti": bool(strs.mean() > 0)},
         "5_icra": {"iyimser": round(float(opt.mean()), 1), "gercek": round(float(real.mean()), 1),
                    "gecti": bool(real.mean() > 0 and opt.mean() - real.mean() <= 0.5 * abs(opt.mean()))},
         "6_tek_pozisyon": {"not": "R1 D−3→D, E2 D→D+3 ardışık; çakışma yok", "gecti": True}}
    n = sum(c[k]["gecti"] for k in c)
    c["gecen"] = f"{n}/6"; c["verdikt"] = "LIVE adayı (önce GÖLGE, karar kullanıcıda)" if n == 6 else ("SHADOW" if n >= 4 else "RED")
    c["broker_gercek"] = st(real.to_numpy()); c["scope"] = name
    return c


def main():
    spy, tlt, qqq = px("SPY"), px("TLT"), px("QQQ")
    M = monthly(spy, tlt, {"QQQ": qqq}); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    cal = spy.dropna().index.intersection(tlt.dropna().index)
    sR1 = side(M.dm.to_numpy()); sE2 = np.where(M.dD.to_numpy() >= TH, 1, 0)
    r1 = (sR1 * M.w_QQQ - COST)[sR1 != 0].to_numpy(); e2 = (M.n_QQQ - COST)[sE2 == 1].to_numpy()
    # kronolojik birleşik işlem listesi
    both = pd.concat([pd.Series((sR1 * M.w_QQQ - COST)[sR1 != 0].to_numpy(), index=M.d_s[sR1 != 0].to_numpy()),
                      pd.Series(e2, index=M.d_D[sE2 == 1].to_numpy())]).sort_index().to_numpy()
    L = {}
    for tag, hh, mm, s in (("opt", 16, 0, 1.0), ("real", 16, 30, 1.0), ("stress", 16, 30, 1.5)):
        L[tag] = (leg_broker(M, cal, sR1, "d_s", 3, hh, mm, s), leg_broker(M, cal, sE2, "d_D", 3, hh, mm, s))
    out = {"E2_uzun": card(e2, [L["opt"][1]], [L["real"][1]], [L["stress"][1]], "qs04_e2_ay_basi_uzun"),
           "ay_sonu_dongusu": card(both, list(L["opt"]), list(L["real"]), list(L["stress"]), "qs04_ay_sonu_dongusu")}
    gl = H.parent.parent / "backend/data/evolution/go_live_cards"
    rules = {"E2_uzun": "Ay sonu D kapanışında SPY ay içi − TLT ay içi ≥ +%2 → NAS100 UZUN, D 16:30 → D+3 16:30",
             "ay_sonu_dongusu": "R1 (D−3: Δ ≥ +%2 KISA / ≤ −%2 UZUN → D) + E2 uzun (D: Δ_D ≥ +%2 → D+3)"}
    for k, c in out.items():
        (gl / f"{c['scope']}.json").write_text(json.dumps({"tarih": "2026-11-11", "kural": rules[k], **c}, indent=1, ensure_ascii=False, default=str))
    (H / "results/qs04_kart.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, c in out.items():
        print("==", k, c["gecen"], c["verdikt"])
        for kk in ("1_hacim", "2_beklenti", "3_kararlilik", "4_surtunme", "5_icra", "broker_gercek"):
            print("   ", kk, c[kk])


if __name__ == "__main__":
    main()
