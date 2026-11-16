"""p1_orb.py — PROTOCOL P1: ORB × VIX (TP 3R) kırılım anatomisi. Çıktı results/p1.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ndx_10y_1m_20261116/src"))
import c_new as C  # noqa: E402
import lib  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
FEATS = {"f_clv": +1, "f_uw5": -1, "f_flip": -1, "f_run": 0}     # öngörü yönü: +1 yüksek iyi, −1 düşük iyi, 0 yok


def features(m1, d, t_in) -> dict:
    a = int(np.searchsorted(m1.t, lib.utc(d, 570)))
    b = int(np.searchsorted(m1.t, t_in))                 # yalnız açılışı < giriş olan (kapanmış) barlar
    o, h, l, c = m1.o[a:b], m1.h[a:b], m1.l[a:b], m1.c[a:b]
    rng = np.where(h - l > 0, h - l, np.nan)
    clv = (c - l) / rng
    up = c > o
    uw = h - np.maximum(o, c)
    k = max(0, len(o) - 5)
    run = 0
    for x in up[::-1]:
        if not x:
            break
        run += 1
    return {"f_clv": float(np.nanmean(clv)), "f_uw5": float(uw[k:].sum() / max(1e-9, (h - l)[k:].sum())),
            "f_flip": float(np.mean(up[1:] != up[:-1])) if len(up) > 1 else np.nan, "f_run": run, "n_bars": len(o)}


def tert_diff(df: pd.DataFrame, f: str, edges, sign: int) -> tuple[float, float, float, float]:
    lo, hi = df[df[f] <= edges[0]].R, df[df[f] > edges[1]].R
    good, bad = (hi, lo) if sign >= 0 else (lo, hi)
    return float(good.mean() - bad.mean()), float(good.mean()), float(bad.mean()), C.boot_diff(good, bad)


def main() -> None:
    m1 = lib.load_m1()
    o = pd.read_parquet(lib.RESULTS / "orb_tp3_trades.parquet").reset_index(drop=True)
    F = pd.DataFrame([features(m1, r.d, r.t_in) for r in o.itertuples()])
    o = pd.concat([o, F], axis=1)
    kes, tst = o[o.era == "YENI"], o[o.era == "ESKI"]
    edges = {f: list(kes[f].quantile([1 / 3, 2 / 3])) for f in FEATS}
    res = {"edges": edges, "KESIF": {}, "TEST": {}}
    for f, s in FEATS.items():
        for name, df in (("KESIF", kes), ("TEST", tst)):
            if s == 0:
                d1 = tert_diff(df, f, edges[f], +1)
                res[name][f] = {"yuksek_eksi_dusuk": d1[0], "yuksek": d1[1], "dusuk": d1[2], "P": d1[3]}
            else:
                d1 = tert_diff(df, f, edges[f], s)
                res[name][f] = {"iyi_eksi_kotu": d1[0], "iyi": d1[1], "kotu": d1[2], "P": d1[3]}
    # maxT permütasyonu (KEŞİF, öngörülü üç özellik): R'yi karıştır, en büyük fark dağılımı
    rng = np.random.default_rng(1)
    obs = {f: res["KESIF"][f]["iyi_eksi_kotu"] for f, s in FEATS.items() if s}
    mx = []
    for _ in range(1000):
        sh = kes.copy(); sh["R"] = rng.permutation(sh.R.values)
        mx.append(max(tert_diff(sh, f, edges[f], s)[0] for f, s in FEATS.items() if s))
    mx = np.array(mx)
    best = max(obs, key=obs.get)
    res["secim"] = {"ozellik": best, "kesif_fark": obs[best], "maxT_p": float((mx >= obs[best]).mean()),
                    "test_ayni_yon": res["TEST"][best]["iyi_eksi_kotu"] > 0, "test_P": res["TEST"][best]["P"]}
    o.to_parquet(OUT / "p1_orb_feats.parquet")
    OUT.mkdir(exist_ok=True)
    (OUT / "p1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
