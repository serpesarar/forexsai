"""tur4.py — PROTOCOL EK-1 Tur 4: bağımsız piyasa taşıması (kural değiştirilmeden).

Ön kayıtlı: hiçbir aday TEST'i geçmediği için üç turun en iyi KEŞİF hücresi (t'ye göre) taşınır →
tur 3 W1b, düşüş ≥ %1,5, VIX hepsi, TP 2R, 3. gün 16:00 (KEŞİF t 2,35).
Ek (ön kayıt dışı, yalnız bilgi): tur 1/3'te TEST + MT5'te artı kalan W1b, düşüş ≥ %1,5, VIX ≥ 18,4, TP 2R, ertesi gün 16:00.

Veri: kutu MT5 (Pepperstone) GER40 M15 2022-03 → 2026-11; US500/US30/US2000 M5 2025-06 → 2026-11 (yon_lab). Sunucu = NY+7.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import vw  # noqa: I001
import kesif as KS
import lib
import veri

POINT = 0.1
SRC = {"GER40": (vw.ROOT / "research/c1_turev_20261105/data/mt5/GER40_M15.csv.gz", 900),
       "US500": (vw.ROOT / "research/yon_lab_20261114/data/mt5/US500_M5.csv.gz", 300),
       "US30": (vw.ROOT / "research/yon_lab_20261114/data/mt5/US30_M5.csv.gz", 300),
       "US2000": (vw.ROOT / "research/yon_lab_20261114/data/mt5/US2000_M5.csv.gz", 300)}
CELLS = [{"ad": "ON_KAYITLI_tur3_en_iyi_KESIF", "typ": "W1b", "drop": 0.015, "vix": 0.0, "tp": "2R", "time": "D3_16", "eval": "r3"},
         {"ad": "EK_bilgi_W1b_VIX_D1", "typ": "W1b", "drop": 0.015, "vix": 18.4, "tp": 2.0, "time": "D1_16", "eval": "r1"}]


def path_of(sym: str) -> veri.PathBars:
    import kaynak
    f, step = SRC[sym]
    x = pd.read_csv(f)
    t = kaynak.server_to_utc(x["t"].to_numpy())
    ok = ~pd.isna(t)
    d = pd.DataFrame({"t": np.asarray(t)[ok].astype(np.int64), "o": x.o[ok], "h": x.h[ok], "l": x.l[ok], "c": x.c[ok],
                      "sp": x.sp[ok] * POINT}).drop_duplicates("t").sort_values("t")
    return veri.PathBars(d.t.values, d.o.values, d.h.values, d.l.values, d.c.values, d.sp.values.astype(float), step, sym)


def main() -> None:
    out = {}
    for sym in SRC:
        p = path_of(sym)
        q = veri.build_15m(p)
        b = veri.build_210m(q)
        anc = vw.a210_anchors(q, b, set())
        e = vw.entries(q, anc)
        e = e[e.typ == "W1b"].reset_index(drop=True)
        e["d"] = [pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(vw.NY).date() for t in e.t_sig]
        e["vix"] = e.d.map(lib.vix_prev_map(sorted(set(e.d))))
        ev1, ev3 = vw.evaluate_all(p, e), vw.evaluate_r3_all(p, e)
        res = {"aralik": [str(pd.Timestamp(int(p.t[0]), unit="s")), str(pd.Timestamp(int(p.t[-1]), unit="s"))],
               "a210_olay": int(len(anc)), "W1b": int(len(e))}
        for c in CELLS:
            ev = ev3 if c["eval"] == "r3" else ev1
            x = ev.merge(e[["drop", "vix", "d"]], left_on="e", right_index=True)
            x = x[(x["drop"] >= c["drop"]) & (x.vix >= c["vix"]) & (x.tp == c["tp"]) & (x.time == c["time"])]
            res[c["ad"]] = {"n": int(len(x)), "mean": round(float(x.R.mean()), 4) if len(x) else None,
                            "mean15": round(float(x.R15.mean()), 4) if len(x) else None,
                            "P_kume": round(KS.cluster_p(x.R.values, x.d.astype(str).values), 3) if len(x) >= 3 else None,
                            "hit": round(float((x.R > 0).mean()), 3) if len(x) else None}
        out[sym] = res
        print(sym, json.dumps(res, ensure_ascii=False), flush=True)
    for c in CELLS:
        rows = [(s, out[s][c["ad"]]) for s in SRC if out[s][c["ad"]]["n"]]
        n = sum(r["n"] for _, r in rows)
        pooled = sum(r["n"] * r["mean"] for _, r in rows) / n if n else None
        out[f"havuz_{c['ad']}"] = {"n": n, "mean": round(pooled, 4) if pooled is not None else None,
                                   "artı_sembol": f"{sum(r['mean'] > 0 for _, r in rows)}/{len(rows)}"}
        print("havuz", c["ad"], out[f"havuz_{c['ad']}"])
    (KS.RES / "tur4_tasima.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
