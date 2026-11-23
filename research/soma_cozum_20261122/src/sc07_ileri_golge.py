"""SC-07 — Soma kopyası ileri gölge (PROTOCOL.md SC-07). Yeni export geldikçe koşulur; hüküm n ≥ 100 sinyalde.

Adımlar: (1) kullanıcı yeni export'u research/kopya_hesap_20261122/data/raw/2268766_T.csv + history/ altına koyar,
(2) .venv/bin/python -I research/kopya_hesap_20261122/src/kh_yukle.py, (3) sc_duka.py guncel + sc_veri.bar_kur(),
(4) bu betik → results/sc07_ileri.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sc01_ayristirma as A  # noqa: E402
import sc_degerlendir as D  # noqa: E402
import sc_veri as V  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
KESIM = D.ts("2026-11-21")
GECIKME = 5 * 60
N_MIN = 100


def main() -> None:
    H = A.Hazir()
    p = V.islemler("2268766")
    ilk = p.groupby("sinyal")["t_giris"].transform("min")
    p = p[(ilk >= KESIM) & (p["t_cikis"] + GECIKME < H.bar.t[-1])].reset_index(drop=True)
    if p.empty:
        print("Kesimden sonra bar kapsamında sinyal yok.")
        return
    t0 = p["t_giris"].to_numpy() + GECIKME
    t1 = p["t_cikis"].to_numpy() + GECIKME
    yon, lot, sid = p["yon"].to_numpy().astype(np.int32), p["volume"].to_numpy(), p["sinyal"].to_numpy()

    def kos(sk: float) -> pd.DataFrame:
        r = A.bacak_sim(H, t0, np.maximum(t1 - t0, 60), yon, lot, sid, sk=sk)
        g = r.groupby("sinyal")
        return pd.DataFrame({"bp": g.apply(lambda q: np.average(q["bp"], weights=q["lot"]), include_groups=False),
                             "t0": g["t0"].min(), "t1": g["t1"].max()})

    s, ss = kos(1.0), kos(1.5)
    kendi = p.groupby("sinyal").apply(lambda q: np.average(q["bp_kendi"], weights=q["volume"]), include_groups=False)
    oz = D.ozet(s)
    tp = D.tek_pozisyon(s)
    olcut = {"hacim": oz["n"] >= N_MIN, "beklenti": oz["ort_bp"] > 0 and oz["P"] >= 0.90,
             "kararlilik": (oz["yari1"] or 0) >= 0 and oz["yari2"] >= 0, "surtunme": float(ss["bp"].mean()) > 0,
             "tek_pozisyon": float(tp["bp"].mean()) > 0,
             "icra": float(kendi.reindex(s.index).mean() - s["bp"].mean()) < s["bp"].mean() / 2}
    sonuc = {"n": oz["n"], "ozet": oz, "stres": round(float(ss["bp"].mean()), 3), "tek_poz": round(float(tp["bp"].mean()), 3),
             "saglayici_kendi": round(float(kendi.mean()), 3), "olcutler": olcut,
             "hukum": ("GEÇTİ" if all(olcut.values()) else "GEÇMEDİ") if oz["n"] >= N_MIN else f"ARA BAKIŞ (n {oz['n']} < {N_MIN})"}
    D.kaydet("SC-07", "ILERI", {"kesim": "2026-11-21", "gecikme_sn": GECIKME}, sonuc)
    (KOK / "results" / "sc07_ileri.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(sonuc, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
