"""kesif2.py — Tur 2 (PROTOCOL EK-1): zaman çıkışı. Aynı 8 giriş; tutuş 2/3/5 işlem günü sonra NY 16:00;
stop yapı (1×) ya da felaket (2×); düşüş {≥%3, ≥%5} × VIX {≥18,4, ≥22} → 8×2×2×2×3 = 192 hücre. Yalnız KEŞİF.
`tp` sütunu = stop çarpanı, `time` = tutuş günü.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import vw  # noqa: I001
import kesif as KS

DROPS2 = {"d3": 0.03, "d5": 0.05}
VIXS2 = {"v18.4": 18.4, "v22": 22.0}
TAG = "tur2"


def main() -> None:
    e = pd.read_parquet(KS.CACHE / "girisler.parquet")
    p = vw.duka_path_stable()
    ek = e[e.era == "KESIF"].reset_index(drop=True)
    ek = ek[ek["drop"] >= 0.03].reset_index(drop=True)
    ev = vw.evaluate_hold_all(p, ek)
    gr = KS.grid(ev, ek, drops=DROPS2, vixs=VIXS2)
    gr.to_csv(KS.RES / f"kesif_izgara_{TAG}.csv", index=False)
    real = KS.passing(gr)
    print(f"{TAG} KEŞİF: {len(gr)} hücre, aday {len(real)}", flush=True)
    pc = []
    for r in range(KS.N_PLACEBO):
        evp = vw.evaluate_hold_all(p, ek, shift=KS.placebo_shifts(ek, 200 + r))
        pc.append(int(len(KS.passing(KS.grid(evp, ek, n_boot=500, drops=DROPS2, vixs=VIXS2)))))
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
