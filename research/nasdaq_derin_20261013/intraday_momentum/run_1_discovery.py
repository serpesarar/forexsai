"""Adım 1 — KEŞİF (NY tarihi < 2026-07-01). Kasa burada AÇILMAZ.

P1 (ana) + S1..S7, ön-kayıtlı bölmeler V1–V3, tabanlar (hep-AL, işaret permütasyonu), saat plasebosu,
regresyon (literatür kıyası), yıl-yıl, kart (6 ölçüt) — PROTOCOL.md.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from imcore import (COST, LOCK, RES, STRESS, VIX_TH, add_dvol_ndx, add_prev_close, boot_p, day_table,
                    load_ndx, nyse_days, ols, perm_p, summarize, trades, us_half_days, yearly)

TZ = "America/New_York"
HALF = us_half_days(range(2015, 2027))
NYSE = nyse_days()


def build(tf: str, step: int) -> pd.DataFrame:
    pts = list(range(570, 961, 30)) if step <= 30 else [600, 660, 720, 780, 840, 900, 960]
    if step == 60:
        T = day_table(load_ndx(tf), TZ, step, pts, [p for p in pts if p < 960], (540, 600), NYSE, HALF)
    else:
        T = day_table(load_ndx(tf), TZ, step, pts, [p for p in pts if p < 960], (570, 600), NYSE, HALF)
    T = add_prev_close(T, "P960")
    T = add_dvol_ndx(T)
    T = T[T.index < LOCK]                      # KASA KAPALI
    # nedensel ilk-30 aralığı tertili (yalnız önceki 250 gün)
    ratio = (T.FH_hi - T.FH_lo) / (T.C0 * T.dvol)
    q = ratio.shift(1).rolling(250, min_periods=120).quantile(0.67)
    T["V2_hi"] = np.where(q.notna(), ratio >= q, np.nan)
    return T


def sig(T: pd.DataFrame, name: str) -> pd.Series:
    C0 = T.C0
    if name == "ROD":
        return T.P930 / C0 - 1
    if name == "ROD60":
        return T.P900 / C0 - 1
    if name == "ONFH":
        return T.P600 / C0 - 1
    if name == "FH":
        return T.P600 / T.P570 - 1
    if name == "LATE":
        return T.P930 / T.P720 - 1
    if name == "SLH":
        return T.P930 / T.P900 - 1
    raise ValueError(name)


HYP = {  # id: (sinyal, giriş barı başlangıcı, veri)
    "P1": ("ROD", 930, "30m"), "S1": ("ONFH", 930, "30m"), "S2": ("FH", 930, "30m"), "S3": ("ONFH&ROD", 930, "30m"),
    "S4": ("LATE", 930, "30m"), "S5": ("SLH", 930, "30m"), "S6": ("ROD60", 900, "1h"), "S7": ("ONFH", 900, "1h"),
    "S6_30m": ("ROD60", 900, "30m"), "S7_30m": ("ONFH", 900, "30m"),
}


def run_h(T: pd.DataFrame, hid: str, cost: float = COST) -> pd.DataFrame:
    s, ent, _ = HYP[hid]
    if s == "ONFH&ROD":
        a, b = np.sign(sig(T, "ONFH")), np.sign(sig(T, "ROD"))
        x = pd.Series(np.where(a == b, a, 0.0), index=T.index)
        x[a.isna() | b.isna()] = np.nan
    else:
        x = sig(T, s)
    return trades(T, x, f"O{ent}", "P960", cost=cost, opt_col=f"P{ent}").assign(sigval=x)


def card(X: pd.DataFrame, Xs: pd.DataFrame, icra: dict) -> dict:
    v = X.R.to_numpy()
    P, lo, hi = boot_p(v)
    h = len(v) // 2
    m = float(v.mean())
    chk = {
        "1_hacim": {"deger": len(v), "esik": ">=150", "gecti": len(v) >= 150},
        "2_beklenti": {"deger": f"ortR={m:+.4f}, P(EV>0)={P:.3f}", "esik": ">0 ve >=0.90", "gecti": m > 0 and P >= 0.90},
        "3_kararlilik": {"deger": f"{v[:h].mean():+.4f} / {v[h:].mean():+.4f}", "esik": "ikisi >=0",
                         "gecti": v[:h].mean() >= 0 and v[h:].mean() >= 0},
        "4_surtunme": {"deger": f"spread×{STRESS}: ortR={Xs.R.mean():+.4f}", "esik": ">0", "gecti": Xs.R.mean() > 0},
        "5_icra": icra,
        "6_tek_pozisyon": {"deger": f"günde 1 işlem, çakışma 0 → ortR={m:+.4f}", "esik": ">0", "gecti": m > 0},
    }
    return chk


def main() -> None:
    out: dict = {"not": "KEŞİF, NY tarihi < 2026-07-01; kasa açılmadı"}
    T30, T1h, T1m = build("30m", 30), build("1h", 60), build("1m", 1)
    out["gunler"] = {"N30": [str(T30.index.min().date()), str(T30.index.max().date()), len(T30)],
                     "N1h": [str(T1h.index.min().date()), str(T1h.index.max().date()), len(T1h)],
                     "N1m": [str(T1m.index.min().date()), str(T1m.index.max().date()), len(T1m)]}
    data = {"30m": T30, "1h": T1h}
    rows, perms = [], {}
    for hid, (_, _, tf) in HYP.items():
        X = run_h(data[tf], hid)
        sm = summarize(X, hid)
        p, nullm = perm_p(X)
        sm["perm_p"] = round(p, 4)
        sm["perm_bos_ort"] = round(nullm, 4)
        rows.append(sm)
        perms[hid] = p
        out.setdefault("yillar", {})[hid] = yearly(X)
    # Holm (ikincil: P1 hariç ön-kayıtlı 7 ana ikincil S1..S7)
    sec = sorted([(perms[h], h) for h in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]])
    holm, k = {}, len(sec)
    for i, (p, h) in enumerate(sec):
        holm[h] = min(1.0, max(p * (k - i), max(holm.values()) if holm else 0))
    for r in rows:
        r["holm_p"] = round(holm.get(r["id"], np.nan), 4) if r["id"] in holm else None
    out["hipotezler"] = rows

    # 1m tekrar (P1, S1, S6_1m)
    rows1m = []
    for hid in ["P1", "S1", "S2", "S4", "S5", "S6_30m"]:
        X = run_h(T1m, hid)
        sm = summarize(X, hid + "@1m")
        sm["perm_p"] = round(perm_p(X)[0], 4)
        sm["iyimser_ortR(kapanis,spreadsiz)"] = round(float(X.R_opt.mean()), 4)
        rows1m.append(sm)
    out["1m"] = rows1m

    # regresyonlar (literatür kıyası; getiriler, maliyetsiz)
    reg = {}
    for nm, T in [("N30", T30), ("N1m", T1m)]:
        lh = T.P960 / T.P930 - 1
        for s in ["ROD", "ONFH", "FH", "LATE", "SLH"]:
            reg[f"{nm}:{s}->LH"] = ols(lh.to_numpy(), sig(T, s).to_numpy())
    l60 = T1h.P960 / T1h.P900 - 1
    for s in ["ROD60", "ONFH"]:
        reg[f"N1h:{s}->L60"] = ols(l60.to_numpy(), sig(T1h, s).to_numpy())
    for a, b in [(2016, 2020), (2021, 2026)]:
        m = (T1h.index.year >= a) & (T1h.index.year <= b)
        reg[f"N1h:ROD60->L60 {a}-{b}"] = ols(l60[m].to_numpy(), sig(T1h, "ROD60")[m].to_numpy())
    out["regresyon"] = reg

    # bölmeler V1–V3 (P1, S1, S6)
    spl = {}
    for hid in ["P1", "S1", "S6"]:
        T = data[HYP[hid][2]]
        X = run_h(T, hid)
        conds = {
            "V1_VIX>=18.4": X.vix >= VIX_TH, "V1_VIX<18.4": X.vix < VIX_TH,
            "V2_FHaralik_ust": X.V2_hi == 1, "V2_FHaralik_diger": X.V2_hi == 0,
            "V3_guclu|s|>=dvol": X.sigval.abs() >= X.dvol, "V3_zayif": X.sigval.abs() < X.dvol,
        }
        for cn, c in conds.items():
            Xc = X[c.fillna(False).astype(bool)]
            sm = summarize(Xc, f"{hid}|{cn}")
            if len(Xc) >= 20:
                sm["perm_p"] = round(perm_p(Xc)[0], 4)
            spl[f"{hid}|{cn}"] = sm
    out["bolmeler"] = spl

    # saat plasebosu: sinyal = önceki 16:00 → t, hedef t → t+30 (N30)
    plc = {}
    for t in range(630, 931, 30):
        x = T30[f"P{t}"] / T30.C0 - 1
        X = trades(T30, x, f"O{t}", f"P{t + 30}")
        plc[f"{t // 60:02d}:{t % 60:02d}"] = {"n": len(X), "ortR": round(float(X.R.mean()), 4),
                                              "hepAL": round(float(X.R_long.mean()), 4),
                                              "perm_p": round(perm_p(X, n=1000)[0], 4)}
    out["saat_plasebosu_N30"] = plc

    # KART — P1, N30 (+ 5. ölçüt N1m)
    X = run_h(T30, "P1")
    Xs = run_h(T30, "P1", cost=COST * STRESS)
    X1 = run_h(T1m, "P1")
    m1, o1 = float(X1.R.mean()), float(X1.R_opt.mean())
    m30, o30 = float(X.R.mean()), float(X.R_opt.mean())
    icra = {"deger": f"N1m: iyimser {o1:+.4f} vs gerçek {m1:+.4f} (fark {o1 - m1:+.4f}); "
                     f"N30: iyimser {o30:+.4f} vs gerçek {m30:+.4f} (fark {o30 - m30:+.4f})",
            "esik": "fark < ortR/2 (ortR>0 gerekir)",
            "gecti": bool(m30 > 0 and m1 > 0 and (o1 - m1) < m1 / 2 and (o30 - m30) < m30 / 2)}
    chk = card(X, Xs, icra)
    n_ok = sum(c["gecti"] for c in chk.values())
    out["kart_P1"] = {"checks": chk, "gecen": n_ok,
                      "hepAL_fark": round(m30 - float(X.R_long.mean()), 4), "perm_p": perms["P1"]}
    X.to_csv(RES / "P1_N30_kesif_islemler.csv")
    json.dump(out, open(RES / "kesif.json", "w"), ensure_ascii=False, indent=1, default=str)

    pd.set_option("display.width", 250)
    cols = ["id", "n", "ortR", "ort_puan", "WR", "P_EV>0", "P_EV>0_blok20", "yari1", "yari2", "hepAL_ortR",
            "fark_hepAL", "long_payi", "perm_p", "holm_p"]
    print(pd.DataFrame(rows)[cols].to_string(index=False))
    print(pd.DataFrame(rows1m)[[c for c in cols if c != "holm_p"] + ["iyimser_ortR(kapanis,spreadsiz)"]].to_string(index=False))
    print(json.dumps(reg, indent=0))
    print(pd.DataFrame(spl.values())[["id", "n", "ortR", "WR", "P_EV>0", "yari1", "yari2", "hepAL_ortR", "fark_hepAL"]
                                     + (["perm_p"])].to_string(index=False))
    print(json.dumps(plc))
    print(json.dumps(out["kart_P1"], ensure_ascii=False, indent=1, default=str))
    print(json.dumps(out["yillar"]["S6"]), json.dumps(out["yillar"]["P1"]))
    print(out["gunler"])


if __name__ == "__main__":
    main()
