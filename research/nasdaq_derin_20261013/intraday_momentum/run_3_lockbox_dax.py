"""Adım 3 — KASA (2026-07-01 → 10-02, bir kez) + DAX bağımsız piyasa. PROTOCOL §6.

Kasa: P1 ve S6 (S6 = ROD60 → 15:00–16:00; 1h uzun veri 07-14'te bittiği için 30m ve 1m ile, tanım birebir aynı)
      + S6|VIX≥18,4 kovası (keşifte 5/6; §3 gereği kasa ister).
DAX : Berlin seansı 09:00–17:30. P1_DAX: sign(önceki 17:30 → 17:00) → 17:00–17:30; S1_DAX: sign(önceki 17:30 → 09:30)
      → 17:00–17:30; S2_DAX: sign(09:00→09:30) → 17:00–17:30; S6_DAX: sign(önceki 17:30 → 16:30) → 16:30–17:30.
      Maliyet 1,5 puan; R = puan / (giriş × kendi dvol'ü).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from dateutil.easter import easter

from imcore import (COST, LOCK, RES, VIX_TH, add_dvol_ndx, add_dvol_own, add_prev_close, day_table, load_dax,
                    load_ndx, nyse_days, perm_p, summarize, trades, us_half_days, yearly)

TZ = "America/New_York"


def ndx_lock(tf: str, step: int) -> pd.DataFrame:
    pts = list(range(570, 961, 30))
    T = day_table(load_ndx(tf), TZ, step, pts, [p for p in pts if p < 960], (570, 600), nyse_days(),
                  us_half_days(range(2015, 2027)))
    T = add_dvol_ndx(add_prev_close(T, "P960"))
    return T[T.index >= LOCK]


def de_holidays(years: range) -> set:
    out = set()
    for y in years:
        e = pd.Timestamp(easter(y))
        out |= {pd.Timestamp(f"{y}-01-01"), e - pd.Timedelta(days=2), e + pd.Timedelta(days=1),
                pd.Timestamp(f"{y}-05-01"), pd.Timestamp(f"{y}-12-24"), pd.Timestamp(f"{y}-12-25"),
                pd.Timestamp(f"{y}-12-26"), pd.Timestamp(f"{y}-12-31")}
    return out


def dax_table() -> pd.DataFrame:
    pts = [540, 570, 990, 1020, 1050]
    T = day_table(load_dax("30m"), "Europe/Berlin", 30, pts, [990, 1020], (540, 570), None, de_holidays(range(2020, 2027)))
    T = T.dropna(subset=["P540", "P1050"])
    T = add_prev_close(T, "P1050")
    T = add_dvol_own(T, "P1050")
    return T


def main() -> None:
    out: dict = {"not": "KASA bir kez açıldı (2026-10-13)"}
    rows = []
    for tf, step in [("30m", 30), ("1m", 1)]:
        T = ndx_lock(tf, step)
        out[f"kasa_gun_{tf}"] = [str(T.index.min().date()), str(T.index.max().date()), len(T)]
        for hid, s, ent in [("P1", T.P930 / T.C0 - 1, 930), ("S6", T.P900 / T.C0 - 1, 900)]:
            X = trades(T, s, f"O{ent}", "P960", opt_col=f"P{ent}")
            r = summarize(X, f"{hid}@kasa_{tf}")
            r["perm_p"] = round(perm_p(X)[0], 4)
            r["iyimser"] = round(float(X.R_opt.mean()), 4)
            rows.append(r)
            if hid == "S6":
                Xv = X[X.vix >= VIX_TH]
                r2 = summarize(Xv, f"S6|VIX>=18.4@kasa_{tf}")
                rows.append(r2)
                Xl = X[X.vix < VIX_TH]
                rows.append(summarize(Xl, f"S6|VIX<18.4@kasa_{tf}"))
    out["kasa"] = rows

    D = dax_table()
    out["dax_gun"] = [str(D.index.min().date()), str(D.index.max().date()), len(D)]
    C0 = D.C0
    defs = {"P1_DAX": (D.P1020 / C0 - 1, 1020), "S1_DAX": (D.P570 / C0 - 1, 1020),
            "S2_DAX": (D.P570 / D.P540 - 1, 1020), "S6_DAX": (D.P990 / C0 - 1, 990)}
    drows, dyears = [], {}
    for hid, (s, ent) in defs.items():
        X = trades(D, s, f"O{ent}", "P1050", opt_col=f"P{ent}")
        for lab, Xs in [("tum", X), ("<2026-07", X[X.index < LOCK]), (">=2026-07", X[X.index >= LOCK])]:
            r = summarize(Xs, f"{hid}|{lab}")
            if len(Xs) >= 30:
                r["perm_p"] = round(perm_p(Xs)[0], 4)
            drows.append(r)
        Xv = X[X.vix >= VIX_TH]
        r = summarize(Xv, f"{hid}|VIX>=18.4")
        r["perm_p"] = round(perm_p(Xv)[0], 4)
        drows.append(r)
        drows.append(summarize(X[X.vix < VIX_TH], f"{hid}|VIX<18.4"))
        dyears[hid] = yearly(X)
        b = np.sign(s).reindex(X.index)
        lh = (D.P1050 / D[f"P{ent}"] - 1).reindex(X.index)
        from imcore import ols
        out.setdefault("dax_regresyon", {})[hid] = ols(lh.to_numpy(), s.reindex(X.index).to_numpy())
        del b
    out["dax"] = drows
    out["dax_yillar"] = dyears
    json.dump(out, open(RES / "kasa_dax.json", "w"), ensure_ascii=False, indent=1, default=str)
    pd.set_option("display.width", 250)
    cols = ["id", "n", "ortR", "ort_puan", "WR", "P_EV>0", "yari1", "yari2", "hepAL_ortR", "fark_hepAL", "long_payi"]
    print(out["kasa_gun_30m"], out["kasa_gun_1m"], out["dax_gun"])
    print(pd.DataFrame(rows)[cols + ["perm_p", "iyimser"]].to_string(index=False))
    print(pd.DataFrame(drows)[cols + ["perm_p"]].to_string(index=False))
    print(json.dumps(out["dax_regresyon"]), json.dumps(dyears))


if __name__ == "__main__":
    main()
