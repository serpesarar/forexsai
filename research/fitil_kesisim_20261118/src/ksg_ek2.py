"""ksg_ek2.py — PROTOCOL EK-2: fitilli KSG, dokunulmamış / bağımsız veride (Duka M30 2016-17, EET30, NQ 5m)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import ksg_dogrulama as KD

ROOT, lib, fz, KS = KD.ROOT, KD.lib, KD.fz, KD.KS


def bars(name: str) -> tuple[pd.DataFrame, int]:
    import kaynak
    if name == "DUKA_M30_2016_17":
        d = kaynak.load_duka_m30_export()
        d = d[d.t < int(pd.Timestamp("2018-01-01", tz="UTC").timestamp())]
        step, spr = 1800, 1.5
    elif name == "EET30":
        d = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/EET30_kalibre.parquet")
        step, spr = 1800, 1.5
    else:
        d = pd.read_parquet(ROOT / "research/ndx_tf_yapilandirma_20261117/out/ek/NQ_kalibre.parquet")
        step, spr = 300, 0.25
    d = d.sort_values("t").drop_duplicates("t")
    return pd.DataFrame({"t": d.t.values.astype(np.int64), "o": d.open.values, "h": d.high.values, "l": d.low.values,
                         "c": d.close.values, "sp": np.full(len(d), spr)}), step


def ksg_generic(d: pd.DataFrame) -> pd.DataFrame:
    """KD.ksg_m30 ile aynı (15:00 / 16:00 / 09:30 açılışları); 5m veride de çalışır."""
    return KD.ksg_m30(d)


def wicks(d: pd.DataFrame, step: int) -> np.ndarray:
    p = fz.veri.PathBars(d.t.values, d.o.values, d.h.values, d.l.values, d.c.values, d.sp.values, step, "x")
    b = fz.veri.add_wicks(fz.agg(p, 3600))
    ok = (b.lw_pct >= 0.50) & (b.uw_pct <= 0.5 * b.lw_pct)
    return np.sort(b.tend.values[ok.values]).astype(np.int64)


def main() -> None:
    out, A, B = {}, [], []
    for nm in ("DUKA_M30_2016_17", "EET30", "NQ"):
        d, step = bars(nm)
        k = ksg_generic(d)
        m = KD.tag(k.t_in.values, wicks(d, step))
        out[nm] = KD.comp(k, "net_bp", m) | {"n_ksg": int(len(k)), "aralik": [str(k.d.min()), str(k.d.max())]}
        A.append(k[m].assign(src=nm))
        B.append(k[~m].assign(src=nm))
        print(nm, out[nm], flush=True)
    a, b = pd.concat(A), pd.concat(B)
    P = KS.diff_p(a.net_bp.values, (a.src + a.d.astype(str)).values, b.net_bp.values, (b.src + b.d.astype(str)).values)
    ok_each = all(out[n]["fitil"] is not None and out[n]["fitil"] > 0 and out[n]["fitil"] > out[n]["fitilsiz"] for n in out)
    out["havuz"] = {"fitil": round(float(a.net_bp.mean()), 2), "fitilsiz": round(float(b.net_bp.mean()), 2), "P": round(P, 4)}
    out["gecti"] = bool(ok_each and P >= 0.90)
    print("havuz", out["havuz"], "GEÇTİ" if out["gecti"] else "geçmedi")
    (KD.RES / "ksg_ek2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
