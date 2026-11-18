"""kesisim.py — PROTOCOL: 4 kanıtlı NDX kuralı × fitil etiketi (W 6 sa / 24 sa). Seçim yok; 8 hücrenin hepsi raporlanır."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
sys.path.insert(0, str(ROOT / "research/fitil_zamanlama_20261118/src"))
import lib  # noqa: E402
import rules  # noqa: E402
import fz  # noqa: E402

RES = Path(__file__).resolve().parents[1] / "results"
WINDOWS = {"6h": 6 * 3600, "24h": 24 * 3600}
P_REQ = 1 - 0.10 / 8


def wick_times() -> np.ndarray:
    m = lib.load_m1()
    p = fz.veri.PathBars(m.t, m.o, m.h, m.l, m.c, m.spr, 60, "NDX")
    b = fz.veri.add_wicks(fz.agg(p, 3600))
    ok = (b.lw_pct >= 0.50) & (b.uw_pct <= 0.5 * b.lw_pct)
    return np.sort(b.tend.values[ok.values]).astype(np.int64)


def diff_p(a: np.ndarray, da: np.ndarray, b: np.ndarray, db: np.ndarray, n: int = 4000, seed: int = 4) -> float:
    rng = np.random.default_rng(seed)

    def boot(v, d):
        u, inv = np.unique(d, return_inverse=True)
        s, c = np.bincount(inv, v), np.bincount(inv)
        k = rng.integers(0, len(u), (n, len(u)))
        return s[k].sum(1) / c[k].sum(1)

    return float((boot(a, da) - boot(b, db) > 0).mean())


def main() -> None:
    RES.mkdir(exist_ok=True)
    m1 = lib.load_m1()
    D = lib.daily_table(m1)
    vixp = lib.vix_prev_map(D.d.tolist())
    tr = {"C3b": (lib.to_frame(rules.c3b(m1, D)), "net_bp"), "ORBxVIX": (lib.to_frame(rules.orb(m1, D, vixp, tp_r=3.0)), "R"),
          "KSG": (lib.to_frame(rules.ksg(m1, D)), "net_bp"), "CAPREV": (lib.to_frame(rules.caprev(m1, D, vixp)), "R")}
    wt = wick_times()
    out = {}
    for name, (df, col) in tr.items():
        df = df.dropna(subset=[col]).reset_index(drop=True)
        for wn, ws in WINDOWS.items():
            lo = np.searchsorted(wt, df.t_in.values - ws, "left")
            hi = np.searchsorted(wt, df.t_in.values, "right")
            tag = hi > lo
            a, b = df[tag], df[~tag]
            res = {"olcu": col, "n_fitil": int(tag.sum()), "n_fitilsiz": int((~tag).sum()),
                   "fitil_ort": round(float(a[col].mean()), 4) if len(a) else None, "fitilsiz_ort": round(float(b[col].mean()), 4),
                   "taban_ort": round(float(df[col].mean()), 4)}
            for e in ("ESKI", "YENI"):
                ae, be = a[a.era == e], b[b.era == e]
                res[e] = {"n_fitil": int(len(ae)), "fitil": round(float(ae[col].mean()), 4) if len(ae) else None,
                          "fitilsiz": round(float(be[col].mean()), 4) if len(be) else None}
            res["P_fark"] = round(diff_p(a[col].values, a.d.astype(str).values, b[col].values, b.d.astype(str).values), 4) if len(a) >= 3 else None
            ok = (len(a) >= 30 and all(res[e]["fitil"] is not None and res[e]["fitil"] > 0 for e in ("ESKI", "YENI"))
                  and all(res[e]["fitil"] is not None and res[e]["fitilsiz"] is not None and res[e]["fitil"] > res[e]["fitilsiz"] for e in ("ESKI", "YENI"))
                  and (res["P_fark"] or 0) >= P_REQ)
            res["gecti"] = bool(ok)
            out[f"{name}|{wn}"] = res
            print(f"{name:8s} W{wn:4s} fitilli n {res['n_fitil']:4d} ort {res['fitil_ort']} | fitilsiz {res['fitilsiz_ort']} (n {res['n_fitilsiz']}) | "
                  f"ESKİ {res['ESKI']['fitil']} vs {res['ESKI']['fitilsiz']} | YENİ {res['YENI']['fitil']} vs {res['YENI']['fitilsiz']} | "
                  f"P {res['P_fark']} {'GEÇTİ' if ok else ''}", flush=True)
    (RES / "kesisim.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
