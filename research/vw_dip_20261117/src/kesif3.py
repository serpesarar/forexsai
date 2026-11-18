"""kesif3.py — Tur 3 (PROTOCOL EK-3): W girişleri (b, a, yeni r = boyun geri-testi) × TP {ölçülen hareket, 2R, yok} ×
zaman {24 sa, ertesi gün 16:00, 3. gün 16:00} × düşüş {≥%1,5, ≥%3} × VIX {hepsi, ≥18,4} = 216 hücre. Yalnız KEŞİF."""
from __future__ import annotations

import json

import numpy as np

import vw  # noqa: I001
import kesif as KS

TYPES3 = ("W1b", "W1a", "W1r", "WGb", "WGa", "WGr")
DROPS3 = {"d1.5": 0.015, "d3": 0.03}
TAG = "tur3"


def main() -> None:
    p, e = KS.build_entries()                      # yeniden kurulur: W·r girişleri eklendi
    e.to_parquet(KS.CACHE / "girisler_tur3.parquet")
    print("W girişleri:", e[e.typ.isin(TYPES3)].groupby(["typ", "era"]).size().unstack().to_dict(), flush=True)
    ek = e[(e.era == "KESIF") & e.typ.isin(TYPES3)].reset_index(drop=True)
    ev = vw.evaluate_r3_all(p, ek)
    gr = KS.grid(ev, ek, drops=DROPS3, types=TYPES3)
    gr.to_csv(KS.RES / f"kesif_izgara_{TAG}.csv", index=False)
    real = KS.passing(gr)
    print(f"{TAG} KEŞİF: {len(gr)} hücre, aday {len(real)}", flush=True)
    pc = []
    for r in range(KS.N_PLACEBO):
        evp = vw.evaluate_r3_all(p, ek, shift=KS.placebo_shifts(ek, 300 + r))
        pc.append(int(len(KS.passing(KS.grid(evp, ek, n_boot=500, drops=DROPS3, types=TYPES3)))))
        print(f"  plasebo {r}: {pc[-1]}", flush=True)
    frozen, per = [], {}
    for r in real.sort_values("t", ascending=False).itertuples():
        if per.get(r.typ, 0) >= KS.MAX_PER_TYPE:
            continue
        frozen.append({k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in r._asdict().items() if k != "Index"})
        per[r.typ] = per.get(r.typ, 0) + 1
        if len(frozen) == KS.MAX_FROZEN:
            break
    oz = {"hucre": len(gr), "gercek_aday": len(real), "plasebo_aday": pc, "plasebo_p95": float(np.percentile(pc, 95)),
          "izgara_sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (KS.RES / f"kesif_ozet_{TAG}.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    (KS.RES / f"donmus_adaylar_{TAG}.json").write_text(json.dumps(frozen, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(oz, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
