"""Tüm adaylar için yıl başına Δ Σ R + EK-2 S4 ikincil hükmü (2023–2026 her yıl Δ>0)."""
from __future__ import annotations

import importlib.util

import pandas as pd

from eng import HERE

_sp = importlib.util.spec_from_file_location("my_s1", HERE / "s1_tarama.py")
S = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(S)
RES = HERE.parent / "results"
LAST4 = [2023, 2024, 2025, 2026]


def main():
    b = pd.read_pickle(RES / "base_full.pkl")
    b = b[b.period != "VAKA"]
    by0 = b.groupby(b.et.dt.year).R.sum()
    scan = pd.read_csv(RES / "tarama.csv").set_index("aday")
    rows = []
    for name, kw in S.C.items():
        t, _ = S.run_all(kw)
        t = t[t.period != "VAKA"]
        by = t.groupby(t.et.dt.year).R.sum().reindex(by0.index, fill_value=0) - by0
        r = {"aday": name, **{str(y): round(v, 1) for y, v in by.items()}}
        r["S4_yillar"] = all(by.get(y, 0) > 0 for y in LAST4)
        r["boot_P"] = scan.loc[name, "boot_P"] if name in scan.index else None
        r["stres"] = scan.loc[name, "stres_dSR"] if name in scan.index else None
        r["krit1"] = scan.loc[name, "krit1"] if name in scan.index else None
        rows.append(r)
        print(f"{name:34s} " + " ".join(f"{y}:{by.get(y, 0):+5.1f}" for y in by0.index)
              + f"  S4 {'✓' if r['S4_yillar'] else '✗'}", flush=True)
    pd.DataFrame(rows).to_csv(RES / "yillik_delta.csv", index=False)


if __name__ == "__main__":
    main()
