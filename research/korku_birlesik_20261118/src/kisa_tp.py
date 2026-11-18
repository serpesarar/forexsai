"""kisa_tp.py — EK-1: çift teyitli korku gecesi (S≥2) 16:00 AL, TP {%0,3, %0,5, %0,8} ya da TP'siz, ertesi 16:00 zaman çıkışı."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import kb

TPS = (None, 0.003, 0.005, 0.008)


def main() -> None:
    df = pd.read_parquet(kb.RES / "geceler_DUKA.parquet")
    df = df[df.S >= 2].reset_index(drop=True)
    m = kb.G.lib.load_m1()
    t, o, h, sp = m.t, m.o, m.h, m.spr
    rows = []
    for r in df.itertuples():
        i0, i1 = int(np.searchsorted(t, r.t_in)), int(np.searchsorted(t, r.t_out))
        if i1 <= i0 or i1 >= len(t):
            continue
        pin = o[i0] + sp[i0]
        cm = np.maximum.accumulate(h[i0:i1])
        nights_fin = r.bp_yok - ((o[i1] / pin - 1) * 1e4)          # finansman payı (bp_yok = brüt − fin)
        rec = {"d": r.d, "era": r.era}
        for tp in TPS:
            if tp is None:
                px, j = o[i1], i1
            else:
                k = int(np.searchsorted(cm, pin * (1 + tp)))
                px, j = (pin * (1 + tp), i0 + k) if k < len(cm) else (o[i1], i1)
            held_h = (t[j] - t[i0]) / 3600
            # finansman maliyeti (pozitif bp): sona kadar tutulduysa gerçek gece sayısı, erken TP'de gece geçtiyse 1 gece
            fin_cost = -nights_fin if t[j] >= r.t_out - 60 else (kb.G.lib.FIN_BP_PER_DAY if held_h > 1.2 else 0.0)
            rec[f"bp_{tp}"] = (px / pin - 1) * 1e4 - fin_cost
            rec[f"saat_{tp}"] = held_h
        rows.append(rec)
    x = pd.DataFrame(rows)
    out = {}
    for tp in TPS:
        c = f"bp_{tp}"
        out[str(tp)] = {e: {"n": int(len(g)), "ort": round(float(g[c].mean()), 1), "isabet": round(float((g[c] > 0).mean()), 3),
                            "sharpe_islem": round(float(g[c].mean() / g[c].std()), 3), "en_kotu": round(float(g[c].min()), 1),
                            "ort_saat": round(float(g[f"saat_{tp}"].mean()), 1)} for e, g in x.groupby("era")}
        print(f"TP {tp}:", out[str(tp)])
    base = {e: out["None"][e]["sharpe_islem"] for e in ("ESKI", "YENI")}
    better = [tp for tp in ("0.003", "0.005", "0.008") if all(out[tp][e]["sharpe_islem"] > base[e] for e in ("ESKI", "YENI"))]
    out["hukum"] = {"TP'sizden iyi (iki dönem)": better, "sinif": "C+" if better else "X"}
    print(out["hukum"])
    (kb.RES / "kisa_tp.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
