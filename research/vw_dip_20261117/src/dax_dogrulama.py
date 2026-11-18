"""dax_dogrulama.py — PROTOCOL EK-4: dondurulmuş W1b kurallarının DAX Dukascopy 1m 2018–26'da değiştirilmeden doğrulanması."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import vw  # noqa: I001
import kesif as KS
import dogrulama as DG
import lib
import veri

SRC = vw.ROOT / "research/fibo_altin_bolge_20261116/cache"
CELLS = [{"ad": "W1b_VIX_2R_D1", "typ": "W1b", "drop": "d1.5", "vix": "v18.4", "tp": 2.0, "time": "D1_16", "f": "r1"},
         {"ad": "W1b_2R_D3_onkayit", "typ": "W1b", "drop": "d1.5", "vix": "hepsi", "tp": "2R", "time": "D3_16", "f": "r3"}]


def dax_path() -> veri.PathBars:
    raw = pd.read_parquet(SRC / "DAX_1m_raw.parquet", columns=["t"]).sort_values("t").drop_duplicates("t")
    z = np.load(SRC / "DAX_1m.npz")
    assert len(raw) == len(z["o"])
    return veri.PathBars(raw.t.values.astype(np.int64), z["o"], z["h"], z["l"], z["c"], z["spr"].astype(float), 60, "DAX_1m")


def main() -> None:
    p = dax_path()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    anc = vw.a210_anchors(q, b, set())
    e = vw.entries(q, anc)
    e = e[e.typ == "W1b"].reset_index(drop=True)
    e["d"] = [pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert(vw.NY).date() for t in e.t_sig]
    e["vix"] = e.d.map(lib.vix_prev_map(sorted(set(e.d))))
    out = {"veri": [str(pd.Timestamp(int(p.t[0]), unit="s")), str(pd.Timestamp(int(p.t[-1]), unit="s"))], "a210": len(anc), "W1b": len(e)}
    for c in CELLS:
        f = vw.evaluate_all if c["f"] == "r1" else vw.evaluate_r3_all
        x = DG.cell_rows(f(p, e), e, c)
        xp = pd.concat([DG.cell_rows(f(p, e, shift=KS.placebo_shifts(e, 900 + r)), e, c) for r in range(10)], ignore_index=True)
        s = DG.summ(x)
        dp = float(np.mean([x.R.mean() - xp.sample(len(x), replace=True, random_state=k).R.mean() > 0 for k in range(2000)])) if len(x) > 2 and len(xp) else float("nan")
        ok = {"ort_P": bool(s.get("mean", -1) > 0 and s.get("P_kume", 0) >= 0.9), "iki_yari": bool((s.get("h1") or -1) >= 0 and (s.get("h2") or -1) >= 0),
              "spread15": bool(s.get("mean15", -1) > 0), "plasebo": bool(dp >= 0.9)}
        out[c["ad"]] = {**s, "plasebo_mean": round(float(xp.R.mean()), 4) if len(xp) else None, "P_plasebo_fark": round(dp, 3),
                        "olcut": ok, "gecti": all(ok.values())}
        print(c["ad"], json.dumps(out[c["ad"]], ensure_ascii=False, default=str), flush=True)
    (KS.RES / "dax_dogrulama.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
