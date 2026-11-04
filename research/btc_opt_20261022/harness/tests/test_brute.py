"""Vektörel motor ↔ kaba döngü: ≥10.000 rastgele (olay × spec) çifti, 4 maliyet modu, 3 ufuk sınıfı, tüm spec türleri.

Çalıştır: .venv/bin/python -I tests/test_brute.py  (harness kökünden)
Çıktı: results/validation_brute.json
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config as K  # noqa: E402
import data as Dt  # noqa: E402
import exit_space as S  # noqa: E402
import exits as X  # noqa: E402
from brute import brute_one  # noqa: E402

rng = np.random.default_rng(20261022)
P = Dt.path("main")
eng = X.ExitEngine("main")
PLAN = {"scalp": 4000, "intraday": 4000, "swing": 2600}
rows, t0 = [], time.time()
for cls, npairs in PLAN.items():
    space = S.build_space(cls, include_opp=True) + [S.orig_spec(True), S.orig_spec(False)]
    for mode in K.COST_MODES:
        ne = npairs // 4 // 8 + 1
        ts = rng.integers(K.m("2021-07-01"), K.m("2026-10-15"), ne)
        # bir kısmı dışlama aralığına / veri sonuna yakın (kenar durumları)
        ts[:3] = [K.EX0 - 30, K.EX0 + 10, K.m("2026-10-20 23:00")]
        ev = pd.DataFrame({"ts_dec": ts, "dir": rng.choice([1, -1], ne)})
        ev = ev.assign(**Dt.context("main", ts))
        ev["sl_orig"] = ev["atr_1h"] * rng.uniform(0.5, 3, ne)
        ev["tp_orig"] = ev["sl_orig"] * rng.uniform(0.5, 3, ne)
        hz = {"scalp": 60, "intraday": 1440, "swing": 7200}[cls]
        ev["end_orig"] = ts + rng.integers(1, hz, ne)
        ev["end_opp"] = np.where(rng.random(ne) < 0.7, ts + rng.integers(1, hz * 2, ne), np.nan)
        pick = rng.choice(len(space), 8, replace=False)
        specs = [space[i] for i in pick]
        o = eng.run(ev, specs, mode=mode)
        for i in range(ne):
            for j, s in enumerate(specs):
                r = brute_one(P, eng.RO, ev.iloc[i].to_dict(), s, mode=mode)
                rows.append(dict(cls=cls, mode=mode, kind=s.kind, key=s.key(), i=i,
                                 R_v=o["R"][i, j], R_b=r[0], ext_v=o["ext"][i, j], ext_b=r[2]))
    print(cls, len(rows), f"{time.time() - t0:.0f}s", flush=True)
df = pd.DataFrame(rows)
both_nan = df.R_v.isna() & df.R_b.isna()
okR = both_nan | (np.abs(df.R_v - df.R_b) <= 1e-9 * np.maximum(1, np.abs(df.R_b)))
okX = (df.ext_v.isna() & df.ext_b.isna()) | (df.ext_v == df.ext_b)
df["ok"] = okR & okX
bad = df[~df.ok]
res = {"pairs": int(len(df)), "valid_pairs": int((~both_nan).sum()), "mismatches": int(len(bad)),
       "by_kind": df.groupby("kind").agg(n=("ok", "size"), bad=("ok", lambda x: int((~x).sum()))).to_dict("index"),
       "by_mode": df.groupby("mode").agg(n=("ok", "size"), bad=("ok", lambda x: int((~x).sum()))).to_dict("index"),
       "first_bad": bad.head(20).to_dict("records")}
(K.RESULTS / "validation_brute.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k: v for k, v in res.items() if k != "first_bad"}, indent=1, default=str))
print("ÖRNEK UYUŞMAZLIK:", bad.head(10).to_string())
