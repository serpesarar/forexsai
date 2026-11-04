"""dv_1_test.py — TEK SEFERLİK doğrulayıcı sınama (PROTOCOL.md §2–§6, eşikler §8.2). Bir kez koşulur.

Setler: N-H, N-X, N-HX (NDX holdout + uzatma), D-30 (DAX birincil), D-1h (DAX vekil), Q-D (QQQ günlük vekil).
Her sette: son saat aşağı vs yukarı → gece farkı (puan, %, yükseliş oranı), 5-gün blok bootstrap, MDE, verdikt;
plasebo (11→12 saati) + eşli özgüllük; koşulsuz oran; işlem görünümü (1,5 puan spread).
Çıktı: results/test_sonuc.json (+ stdout → results/test_stdout.txt).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dv_core import (B15, BER, DAX1H, DAX30, RES, Px, agg_15m_to_1h, boot_specs, boot_summary, dax_nights,  # noqa: E402
                     describe, fix_dax_axis, load_long1h, ndx_nights, ny_calendar, qqq_nights, verdict, xetra_days)

ESIK = json.load(open(RES / "hazirlik.json"))["esikler"]
SPREAD = 1.5


def analyse(T: pd.DataFrame, kind: str, plasebo: bool = True) -> dict:
    """kind: 'NDX' (eşik % sabit) | 'DAX' (eşik d × SD) | 'QQQ' (NDX eşikleri, karar yok)."""
    r = describe(T)
    dn, up = (T.rl < 0).to_numpy(), (T.rl > 0).to_numpy()
    on, onp = T.on.to_numpy(), T.onp.to_numpy()
    bs = boot_specs(T.i.to_numpy(), {"pts": (dn, up, on), "pct": (dn, up, onp), "up": (dn, up, (on > 0) * 100.0)})
    thr_pct = ESIK["esik_d_DAX"] * r["sd_pct_tum"] if kind == "DAX" else ESIK["esik_pct_NDX"]
    r["esik_pct"], r["esik_up"] = thr_pct, ESIK["esik_up"]
    r["boot"] = {"pts": boot_summary(bs["pts"]), "pct": boot_summary(bs["pct"], thr_pct),
                 "up": boot_summary(bs["up"], ESIK["esik_up"])}
    r["d_std"] = r["pct_fark"] / r["sd_pct_tum"]
    r["verdikt_pct"] = verdict(r["pct_fark"], r["boot"]["pct"], thr_pct)
    r["verdikt_up"] = verdict(r["up_fark"], r["boot"]["up"], ESIK["esik_up"])
    # işlem görünümü (puan/gece, spread düşülmüş; swap hariç)
    r["islem"] = dict(her_gece_AL_net_ort=float(on.mean() - SPREAD), asagi_sonrasi_AL_net_ort=float(on[dn].mean() - SPREAD),
                      yukari_sonrasi_SAT_net_ort=float(-on[up].mean() - SPREAD),
                      her_gece_AL_toplam=float(on.sum() - SPREAD * len(on)),
                      asagi_sonrasi_AL_toplam=float(on[dn].sum() - SPREAD * dn.sum()),
                      ort_mutlak_gece_puan=float(np.abs(on).mean()))
    if plasebo and T.rp.notna().any():
        P_ = T[np.isfinite(T.rp) & (T.rp != 0)].reset_index(drop=True)
        q = describe(P_, "rp")
        dnp, upp = (P_.rp < 0).to_numpy(), (P_.rp > 0).to_numpy()
        dnm, upm = (P_.rl < 0).to_numpy(), (P_.rl > 0).to_numpy()
        b2 = boot_specs(P_.i.to_numpy(), {"plc": (dnp, upp, P_.onp.to_numpy()), "main": (dnm, upm, P_.onp.to_numpy()),
                                          "plc_up": (dnp, upp, (P_.on > 0).to_numpy() * 100.0)})
        bp = boot_summary(b2["plc"], thr_pct)
        main_sub = describe(P_)
        ozg = float(np.mean(b2["main"] - b2["plc"] > 0))
        pv = verdict(q["pct_fark"], bp, thr_pct)
        r["plasebo"] = dict(n=q["n"], pct_fark=q["pct_fark"], up_fark=q["up_fark"], pts_fark=q["pts_fark"], P=bp["P"],
                            P_up=float(np.mean(b2["plc_up"] > 0)), verdikt=pv, ana_pct_fark_ayni_geceler=main_sub["pct_fark"],
                            P_ana_eksi_plasebo=ozg, kapanisa_ozgu=bool(ozg >= 0.90 and pv != "GEÇER"))
    return r


def by_year(T: pd.DataFrame) -> dict:
    out = {}
    for y, S in T.groupby(pd.to_datetime(T.D).dt.year):
        q = describe(S)
        out[int(y)] = dict(n=q["n"], pct_fark=round(q["pct_fark"], 4), up_fark=round(q["up_fark"], 2),
                           up_asagi=round(q["up_asagi"], 1), up_yukari=round(q["up_yukari"], 1))
    return out


def main() -> None:
    cal = ny_calendar()
    out: dict = {"esikler": ESIK}
    # NDX
    h1 = load_long1h()
    a1 = agg_15m_to_1h(pd.read_parquet(B15))
    NH = ndx_nights(cal, Px(h1.ts, h1.close.to_numpy(), 60), date(2025, 12, 1), date(2026, 7, 13))
    NX = ndx_nights(cal, Px(a1.ts, a1.close.to_numpy(), 60, a1.last45.to_numpy()), date(2026, 7, 14), date(2026, 12, 31))
    NHX = pd.concat([NH, NX], ignore_index=True)
    for nm, T in (("N-H", NH), ("N-X", NX), ("N-HX", NHX)):
        out[nm] = analyse(T, "NDX")
    out["N-HX"]["aylik"] = {str(k): v for k, v in
                            {m: describe(S) for m, S in NHX.groupby(pd.to_datetime(NHX.D).dt.strftime("%Y-%m"))}.items()}
    out["N-HX"]["aylik"] = {k: dict(n=v["n"], pct_fark=round(v["pct_fark"], 4), up_asagi=round(v["up_asagi"], 1),
                                    up_yukari=round(v["up_yukari"], 1)) for k, v in out["N-HX"]["aylik"].items()}
    # DAX
    f30, f1h = fix_dax_axis(pd.read_parquet(DAX30)), fix_dax_axis(pd.read_parquet(DAX1H))
    xd30 = xetra_days(f30.ts.min().tz_convert(BER).date(), f30.ts.max().tz_convert(BER).date())
    xd1h = xetra_days(date(2020, 1, 1), f1h.ts.max().tz_convert(BER).date())
    D30 = dax_nights(xd30, Px(f30.ts, f30.close.to_numpy(), 30), date(2021, 3, 17), date(2026, 12, 31), (16, 30), (17, 30))
    D1 = dax_nights(xd1h, Px(f1h.ts, f1h.close.to_numpy(), 60), date(2020, 1, 1), date(2026, 12, 31), (17, 0), (18, 0))
    out["D-30"] = analyse(D30, "DAX")
    out["D-30"]["yillik"] = by_year(D30)
    h = len(D30) // 2
    out["D-30"]["yarilar"] = {"yari1": {k: describe(D30.iloc[:h])[k] for k in ("n", "pct_fark", "up_fark")},
                              "yari2": {k: describe(D30.iloc[h:])[k] for k in ("n", "pct_fark", "up_fark")}}
    out["D-1h"] = analyse(D1, "DAX")
    out["D-1h_2020-01_2021-03-16"] = analyse(D1[pd.to_datetime(D1.D) <= "2021-03-16"].reset_index(drop=True), "DAX")
    # QQQ vekil (karar yok)
    for nm, a, b in (("Q-pre", date(2015, 1, 1), date(2016, 5, 27)), ("Q-ovl", date(2016, 5, 30), date(2025, 11, 28)),
                     ("Q-hold", date(2025, 12, 1), date(2026, 9, 29))):
        out[nm] = analyse(qqq_nights(cal, a, b), "QQQ", plasebo=False)
        out[nm]["not"] = "VEKİL (CLV<0,5), karar yok"
    # hipotez verdikti
    vn, vd = out["N-HX"]["verdikt_pct"], out["D-30"]["verdikt_pct"]
    if vn == "GEÇER" and vd == "GEÇER":
        H = "TEKRARLANDI"
    elif "GEÇER" in (vn, vd):
        H = "KISMİ"
    elif "ÇÜRÜTÜLDÜ" in (vn, vd):
        H = "TEKRARLANMADI"
    else:
        H = "SONUÇSUZ"
    out["hipotez_verdikti"] = dict(N_HX=vn, D_30=vd, sonuc=H)
    json.dump(out, open(RES / "test_sonuc.json", "w"), indent=1, ensure_ascii=False, default=float)
    cols = ["n", "n_asagi", "up_asagi", "up_yukari", "up_kosulsuz", "pct_asagi", "pct_yukari", "pct_fark", "pts_asagi",
            "pts_yukari", "pts_fark", "d_std", "esik_pct"]
    for nm in ("N-H", "N-X", "N-HX", "D-30", "D-1h", "D-1h_2020-01_2021-03-16", "Q-pre", "Q-ovl", "Q-hold"):
        r = out[nm]
        print(f"\n=== {nm} ===")
        print({k: (round(r[k], 4) if isinstance(r[k], float) else r[k]) for k in cols})
        print(" boot pct:", {k: round(v, 4) for k, v in r["boot"]["pct"].items()}, "| verdikt %:", r["verdikt_pct"])
        print(" boot up :", {k: round(v, 4) for k, v in r["boot"]["up"].items()}, "| verdikt up:", r["verdikt_up"])
        print(" boot pts:", {k: round(v, 3) for k, v in r["boot"]["pts"].items()})
        print(" işlem:", {k: round(v, 2) for k, v in r["islem"].items()})
        if "plasebo" in r:
            print(" plasebo:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r["plasebo"].items()})
    print("\nN-HX aylık:", out["N-HX"]["aylik"])
    print("D-30 yıllık:", out["D-30"]["yillik"])
    print("D-30 yarılar:", out["D-30"]["yarilar"])
    print("\nHİPOTEZ VERDİKTİ:", out["hipotez_verdikti"])


if __name__ == "__main__":
    main()
