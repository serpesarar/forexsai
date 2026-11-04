"""Kart + kasa + CAPREV ilişkisi (PROTOCOL §4–§7). Kasa (2026-07-01 → 10-01) burada TEK KEZ açılır."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import engine as E
from engine import (DISC_END, FILTERS, SIGNALS, add_excess, baseline, block_boot, dax_1h, ndx_1h, ndx_30m, run_rule)

sys.path.insert(0, E.GF)
from caprev_card import SPR, paths  # noqa: E402
from long_data import load_long  # noqa: E402
from round4 import build, events  # noqa: E402

CANDS = {
    "H1_RSI10_MA_MA5": ("RSI10", "MA", "MA5", None),
    "H2_RSI10_F0_MA5_s2": ("RSI10", "F0", "MA5", 2.0),
    "H3_IBS20_F0_k1": ("IBS20", "F0", "k1", None),
    "H4_RSI10_VIX_MA5_s2": ("RSI10", "VIX", "MA5", 2.0),
    "H5_LOW3_MA_MA5": ("LOW3", "MA", "MA5", None),
    "SEL_RSI15_F0_MA5 (seçilmiş, E24)": ("RSI15", "F0", "MA5", None),
}
LOCK_START, LOCK_END = pd.Timestamp("2026-07-01"), pd.Timestamp("2026-10-02")
# POST-HOC (ızgara sonrası, NDX+DAX ikisinde de tutarlı LOW5 ailesi; ön-kayıtlı DEĞİL, E24/E23 damgalı)
POSTHOC = {
    "PH_LOW5_F0_MA5": ("LOW5", "F0", "MA5", None),
    "PH_LOW5_MA_k1": ("LOW5", "MA", "k1", None),
    "PH_DROP1_MA_k1": ("DROP1", "MA", "k1", None),
}
if len(sys.argv) > 1 and sys.argv[1] == "posthoc":
    CANDS = POSTHOC


def mask(mk, sig, filt):
    d = mk.day
    return (SIGNALS[sig](d).fillna(False) & FILTERS[filt](d).fillna(False)).to_numpy()


def trades(mk, c, start, end, base, **kw):
    sig, filt, ex, st = c
    return add_excess(run_rule(mk, mask(mk, sig, filt), ex, st, start, end, **kw), base, st)


def mtm(mk, T):
    """Pozisyondayken günlük kapanıştan kapanışa σR (girişten kapanışa ilk gün dahil değil: giriş kapanış sonrası)."""
    d = mk.day
    C = d.C.to_numpy()
    out = {}
    for r in T.itertuples():
        e = C[r.t]
        for j in range(r.t + 1, r.x + 1):
            out[d.index[j]] = out.get(d.index[j], 0.0) + (C[j] - C[j - 1]) / (r.sig * e)
    return pd.Series(out)


def stats(T, col="R"):
    v = T[col].to_numpy()
    days = T.nyd.astype(str).to_numpy()
    bs = block_boot(v, days)
    pd_ = T.groupby("nyd").R.sum().sort_values(ascending=False)
    h = len(v) // 2
    return {"n": len(v), "mean": v.mean(), "P": float(np.mean(bs > 0)), "ci": (np.percentile(bs, 2.5), np.percentile(bs, 97.5)),
            "h1": v[:h].mean(), "h2": v[h:].mean(), "tot": v.sum(), "no5": v.sum() - pd_.iloc[:5].sum(),
            "no10": v.sum() - pd_.iloc[:10].sum()}


def main():
    n1, n30, dx = ndx_1h(), ndx_30m(), dax_1h()
    s1 = n1.day.index[n1.day.sig.notna()][0]
    b1 = baseline(n1, s1, DISC_END)
    bL = baseline(n30, LOCK_START, LOCK_END - pd.Timedelta(days=14))
    b1s = baseline(n1, s1, DISC_END, spread_mult=1.5)
    sd = dx.day.index[dx.day.sig.notna() & dx.day.ma200.notna()][0]
    bD = baseline(dx, sd, LOCK_END)
    # CAPREV
    dc = build(load_long("1h"), 60, 540)
    cap = paths(dc, events(dc, "stress", "hi"), SPR)
    cap = cap.set_index("nyd").R_d0
    out = {}
    for name, c in CANDS.items():
        Td = trades(n1, c, s1, DISC_END, b1)
        Tl = trades(n30, c, LOCK_START, LOCK_END, bL)
        T = pd.concat([Td.assign(src="1h"), Tl.assign(src="30m_kasa")], ignore_index=True)
        T15 = pd.concat([trades(n1, c, s1, DISC_END, b1s, spread_mult=1.5),
                         trades(n30, c, LOCK_START, LOCK_END, bL, spread_mult=1.5)])
        Topt = pd.concat([trades(n1, c, s1, DISC_END, b1, optimistic=True),
                          trades(n30, c, LOCK_START, LOCK_END, bL, optimistic=True)])
        TE2 = trades(n1, c, s1, DISC_END, b1, entry="E2")
        E.SWAP_ANNUAL = 0.03
        T3 = trades(n1, c, s1, DISC_END, b1)
        E.SWAP_ANNUAL = 0.06
        TD = trades(dx, c, sd, LOCK_END, bD)
        st, sx = stats(T), stats(T, "ex")
        yr = T.groupby(T.nyd.dt.year).agg(n=("R", "size"), R=("R", "sum"), ex=("ex", "sum"))
        # 2022: kendi yılının tabanına göre
        b22 = baseline(n1, pd.Timestamp("2022-01-01"), pd.Timestamp("2023-01-01"))
        T22 = T[T.nyd.dt.year == 2022]
        ex22own = float((T22.R - [b22[(c[3], int(min(h, 10)))] for h in T22.h]).mean()) if len(T22) else np.nan
        # CAPREV ilişkisi (1h dönemi, CAPREV verisi 2026-07-14'e kadar)
        m = mtm(n1, Td)
        held = set()
        for r in Td.itertuples():
            for j in range(r.t + 1, r.x + 1):
                held.add(n1.day.index[j])
        sigdays = set(Td.nyd)
        capd = set(cap.index)
        both = pd.concat([m.rename("cand"), cap.rename("cap")], axis=1).fillna(0.0)
        act = both[(both.cand != 0) | (both.cap != 0)]
        on_cap = both.loc[both.index.isin(list(capd))]
        port_cap = cap[[dd not in held for dd in cap.index]]
        port = pd.concat([Td.set_index("nyd").R, port_cap])
        chk = {
            "1_hacim": (st["n"] >= 150, f"{st['n']}"),
            "2_beklenti": (st["mean"] > 0 and st["P"] >= .9, f"ortσR {st['mean']:+.3f} P %{100*st['P']:.1f}"),
            "3_kararlilik": (st["h1"] >= 0 and st["h2"] >= 0, f"{st['h1']:+.3f}/{st['h2']:+.3f}"),
            "4_surtunme": (T15.R.mean() > 0, f"×1,5 {T15.R.mean():+.3f}"),
            "5_icra": (abs(Topt.R.mean() - st["mean"]) < .5 * abs(st["mean"]), f"iyimser {Topt.R.mean():+.3f} vs {st['mean']:+.3f}"),
            "6_tek_poz": (st["mean"] > 0 and port.mean() > 0, f"kural içi çakışma yok; +CAPREV portföy n={len(port)} ort {port.mean():+.3f}"),
        }
        verdict = "LIVE" if all(v[0] for v in chk.values()) else ("RED" if not chk["1_hacim"][0] else "SHADOW")
        if sx["mean"] <= 0:
            verdict += " (fazla≤0: kenar=sürüklenme)"
        out[name] = {
            "kural": c, "verdikt": verdict, "kart": {k: [bool(v[0]), v[1]] for k, v in chk.items()},
            "olay": st["n"], "yil_basi": round(st["n"] / 10.3, 1),
            "ortR": round(st["mean"], 3), "CI": [round(x, 3) for x in st["ci"]], "toplamR": round(st["tot"], 1),
            "en_iyi5_haric": round(st["no5"], 1), "en_iyi10_haric": round(st["no10"], 1),
            "fazla_ort": round(sx["mean"], 3), "fazla_P": round(sx["P"], 3), "fazla_yarilar": [round(sx["h1"], 3), round(sx["h2"], 3)],
            "yillar": {int(k): [int(v.n), round(v.R, 2), round(v.ex, 2)] for k, v in yr.iterrows()},
            "2022_kendi_tabanina_fazla_ort": round(ex22own, 3),
            "kasa": {"n": len(Tl), "ortR": round(Tl.R.mean(), 3) if len(Tl) else None,
                     "fazla": round(Tl.ex.mean(), 3) if len(Tl) else None, "toplamR": round(Tl.R.sum(), 2) if len(Tl) else None,
                     "isler": [(str(r.nyd.date()), round(r.R, 2)) for r in Tl.itertuples()]},
            "DAX": {"n": len(TD), "ortR": round(TD.R.mean(), 3), "fazla": round(TD.ex.mean(), 3),
                    "P_fazla": round(float(np.mean(block_boot(TD.ex.to_numpy(), TD.nyd.astype(str).to_numpy()) > 0)), 3),
                    "yarilar_fazla": [round(TD.ex[:len(TD)//2].mean(), 3), round(TD.ex[len(TD)//2:].mean(), 3)]},
            "E2_ertesi_acilis": {"n": len(TE2), "ortR": round(TE2.R.mean(), 3), "fazla": round(TE2.ex.mean(), 3)},
            "swap_%3": round(T3.R.mean(), 3), "swap_ort_R_%6": round(Td.swapR.mean(), 3),
            "CAPREV": {"caprev_gun": len(capd), "aday_pozisyonda": int(sum(dd in held for dd in capd)),
                       "ayni_gun_sinyal": int(len(capd & sigdays)),
                       "korelasyon_aktif_gunler": round(act[["cand", "cap"]].corr().iat[0, 1], 3),
                       "korelasyon_tum_gunler": round(both[["cand", "cap"]].corr().iat[0, 1], 3),
                       "caprev_gunu_aday_mtm_ort": round(on_cap.cand[on_cap.cand != 0].mean(), 3) if (on_cap.cand != 0).any() else None,
                       "portfoy_toplam": round(port.sum(), 1), "aday_tek": round(Td.R.sum(), 1), "caprev_tek": round(cap.sum(), 1),
                       "atlanan_caprev": int(len(cap) - len(port_cap))},
        }
        print(f"\n== {name}: {verdict}  n={st['n']} ortσR {st['mean']:+.3f} P %{100*st['P']:.1f} fazla {sx['mean']:+.3f} (P %{100*sx['P']:.1f})")
        for k, v in chk.items():
            print(f"   {k:14} {'✓' if v[0] else '✗'} {v[1]}")
        print("   ", {k: out[name][k] for k in ("toplamR", "en_iyi5_haric", "en_iyi10_haric", "fazla_yarilar", "2022_kendi_tabanina_fazla_ort",
                                                "E2_ertesi_acilis", "swap_%3", "swap_ort_R_%6")})
        print("   yıllar", out[name]["yillar"])
        print("   kasa", out[name]["kasa"])
        print("   DAX", out[name]["DAX"])
        print("   CAPREV", out[name]["CAPREV"])
    json.dump(out, open("results/card_posthoc.json" if len(sys.argv) > 1 else "results/card.json", "w"), ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
