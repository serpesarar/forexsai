import sys, json, importlib.util as u
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sp = u.spec_from_file_location("mum_scan", ROOT / "research/mum_kural_20261009/scan.py"); S = u.module_from_spec(sp); sp.loader.exec_module(S)
S.TUR2 = True
SPR = {"XAUUSD": 0.25, "USOIL": 0.03}
A, B = pd.Timestamp("2026-06-01", tz="UTC"), pd.Timestamp("2026-09-03", tz="UTC")
out = {}
for sym in ("XAUUSD", "USOIL"):
    S.SPREAD = SPR[sym]; S._BASE.clear()
    raw = {tf: pd.read_parquet(HERE / "data" / f"{sym}_{tf}.parquet") for tf in ("15m", "30m", "1h")}
    Fs = {tf: S.features(d[d.ts < A].reset_index(drop=True)) for tf, d in raw.items()}
    real = S.evaluate(Fs, S.build_events(Fs)); passed = [k for k, v in real.items() if v["gecti"]]
    null = [sum(v["gecti"] for v in S.evaluate(Fs, S.build_events(Fs, shift=True)).values()) for _ in range(S.REPS)]
    nv = np.array(null)
    print(f"\n{sym} KEŞİF: geçen {len(passed)} | plasebo ort {nv.mean():.1f} %95 {np.percentile(nv,95):.1f} max {nv.max()}")
    for k in passed:
        v = real[k]; print("  ✓", k, {tf: (p["n"], round(p["R"], 3), round(p["pf"], 2), round(p["fark"], 3)) for tf, p in v["tf"].items()})
    S._BASE.clear()
    Fk = {tf: S.features(d[(d.ts >= A) & (d.ts < B)].reset_index(drop=True)) for tf, d in raw.items()}
    rk = S.evaluate(Fk, S.build_events(Fk)) if passed else {}
    for k in passed:
        v = rk[k]; ok = all(np.isfinite(p["R"]) and p["R"] > 0 for p in v["tf"].values())
        print(f"  KASA {'✓' if ok else '✗'} {k}", {tf: (p['n'], round(p['R'], 3)) for tf, p in v['tf'].items()})
    out[sym] = {"gecen": passed, "plasebo": null}
(HERE / "results" / "scan_symbol.json").write_text(json.dumps(out, ensure_ascii=False))
