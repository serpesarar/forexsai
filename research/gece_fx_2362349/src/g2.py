"""GF-2 — rollover açılışında aralık ucundan dönüş (PROTOCOL GF-2), dh4_gece motoru üstünde."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK.parent / "diger_hesap_20261124" / "src"))
import dh4_gece as G  # noqa: E402

G.SPREAD_MAKS = np.inf
G.PENCERE.update({"RO": [(1015, 1040)], "SA": [(480, 659)], "AK": [(960, 1014)]})
DON = {"KESIF": ("2018-01-01", "2022-01-01"), "TEST": ("2022-01-01", "2026-01-01"), "KOR": ("2026-01-01", "2026-11-24")}


def hucreler():
    return [{"ad": f"{W}_q{q}_sl{sl}_T{T}", "W": W, "q": q, "m": 1, "TP": 5, "SL": sl, "T": T}
            for W in ("RO", "SA", "AK") for q in (0.15, 0.05) for sl in (25, 50) for T in (360, 2880)]


def main(mod: str, adlar: list[str] | None = None) -> None:
    Ds = {c: G.yukle(c) for c in G.CIFT}
    for D in Ds.values():
        assert np.isfinite(D["ao"]).all(), "eksik ask (E154)"
    if mod == "KESIF":
        out = {}
        for c in hucreler():
            h = G.olc(Ds, c, *DON["KESIF"])
            out[c["ad"]] = {"tanim": c, **h}
            print(c["ad"], {k: h.get(k) for k in ("n", "ayda", "ort_R", "ort_pip", "isabet", "basabas_isabet", "P_EV", "yari1", "yari2",
                                                  "stres_R", "en_kotu_pip")}, flush=True)
        gec = sorted([k for k, v in out.items() if G.gecer_kesif(v)], key=lambda k: -out[k]["ort_R"] * out[k]["n"])
        out["_aday"] = gec[:2]
        print("GEÇEN", gec, flush=True)
        (KOK / "results/g2_kesif.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    else:
        j = json.loads((KOK / "results/g2_kesif.json").read_text())
        out = {}
        for ad in adlar:
            c = j[ad]["tanim"]
            h = G.olc(Ds, c, *DON["TEST"], plasebo=True)
            yil = all(h["yillik_R"].get(y, -1) > 0 for y in (2022, 2023, 2024, 2025))
            cift = sum((v["ort_R"] or -1) > 0 for v in h["cift"].values()) >= 3
            h["kontrol"] = {"kesif_olcutleri": G.gecer_kesif(h), "plasebo": h.get("fark_R", -1) > 0 and h.get("fark_P", 0) >= 0.95,
                            "2022_25": yil, "cift_3of4": cift}
            h["hukum"] = "B" if all(h["kontrol"].values()) else "X"
            h["kor"] = G.olc(Ds, c, *DON["KOR"], plasebo=True)
            out[ad] = h
            print(ad, h["hukum"], h["kontrol"], {k: h.get(k) for k in ("n", "ayda", "ort_R", "ort_pip", "isabet", "P_EV", "stres_R", "fark_R",
                                                                       "fark_P", "yillik_R", "cift", "en_kotu_pip")}, flush=True)
            print("   KÖR", {k: h["kor"].get(k) for k in ("n", "ort_R", "ort_pip", "isabet", "fark_R", "fark_P")}, flush=True)
        (KOK / "results/g2_test.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2].split(",") if len(sys.argv) > 2 else None)
