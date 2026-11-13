"""FX-01 §2 çift seçimi ölçümleri (hüküm değil). Çalıştır: ../../.venv/bin/python -I secim.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402

RECENT = pd.Timestamp("2023-11-13")


def vr(r: np.ndarray, q: int) -> float:
    r = r[~np.isnan(r)]
    if len(r) < q * 20:
        return float("nan")
    rq = pd.Series(r).rolling(q).sum().dropna().values
    return float(rq.var() / (q * r.var()))


def ac1(r: np.ndarray) -> float:
    r = r[~np.isnan(r)]
    return float(np.corrcoef(r[:-1], r[1:])[0, 1]) if len(r) > 30 else float("nan")


def pair_stats(pair: str, m: dict) -> dict:
    d = f.load(pair, "D1")
    d = d[d.et.dt.dayofweek < 5]
    d["r"] = np.log(d.c / d.c.shift()) * 1e4
    d["rng"] = (d.h - d.l) / d.c * 1e4
    h = f.load(pair, "H1")
    h["spb"] = f.spread_bp(h, m["point"])
    h["r"] = np.log(h.c / h.c.shift()) * 1e4
    rec_d, rec_h = d[d.utc >= RECENT], h[h.utc >= RECENT]
    liquid = rec_h[rec_h.utc.dt.hour.between(7, 16)]
    sig = rec_d.r.std()
    px = d.c.iloc[-1]
    swap_bp = {k: round(m[k] * m["point"] / px * 1e4, 2) for k in ("swap_long", "swap_short")}
    out = {"cift": pair, "D1_basi": str(d.utc.iloc[0].date()), "H1_basi": str(h.utc.iloc[0].date()),
           "sigma_gun_bp": round(sig, 1), "ADR_bp": round(rec_d.rng.mean(), 1),
           "spread_bp_likit": round(liquid.spb.median(), 2), "kappa": round(liquid.spb.median() / sig, 4),
           "swap_bp_gece": swap_bp}
    for name, part in (("kesif", d[d.utc < f.SPLIT]), ("kor", d[d.utc >= f.SPLIT])):
        out[f"AC1_gun_{name}"] = round(ac1(part.r.values), 3)
        out[f"VR5_gun_{name}"] = round(vr(part.r.values, 5), 3)
    for name, part in (("kesif", h[h.utc < f.SPLIT]), ("kor", h[h.utc >= f.SPLIT])):
        out[f"AC1_saat_{name}"] = round(ac1(part.r.values), 3)
    return out


if __name__ == "__main__":
    meta = f.meta()
    pairs = sorted({p.name.split("_")[0] for p in f.FX.glob("*_D1.csv.gz")} & {p.name.split("_")[0] for p in f.FX.glob("*_H1.csv.gz")})
    rows = []
    for p in pairs:
        try:
            rows.append(pair_stats(p, meta[p]))
        except Exception as e:  # noqa: BLE001
            print("hata", p, e)
    t = pd.DataFrame(rows).sort_values("kappa")
    t.to_csv(f.RES / "secim_tablosu.csv", index=False)
    pd.set_option("display.width", 250)
    print(t.drop(columns=["swap_bp_gece"]).to_string(index=False))
    print(t[["cift", "swap_bp_gece"]].to_string(index=False))
