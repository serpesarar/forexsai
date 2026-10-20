"""Ek (ön-kayıt sonrası, simetri kontrolü + dünkü SL profili): keşif 2026 → sınama 2025; 10-19 SL'lerinin canlı
DAYCOMBO'lar içindeki yüzdelikleri. python3 research/daycombo_kombo_20261020/ek.py"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("dk_run", HERE / "run.py")
K = importlib.util.module_from_spec(spec)
sys.modules["dk_run"] = K
spec.loader.exec_module(K)


def reverse(L: list) -> None:
    d = pd.read_parquet(K.OUT / "daycombo_feats.parquet")
    k, s = d[d.split == "sınama"].reset_index(drop=True), d[d.split == "keşif"].reset_index(drop=True)
    cols = [c for c in d.columns if c not in K.SKIP and pd.api.types.is_numeric_dtype(d[c]) and c != "B"]
    conds = K.conditions(k, cols)
    cd = dict(conds)
    real = K.search(k, conds, k.R.to_numpy(float))
    L.append("\n## Ters yön: keşif 2026 → sınama 2025")
    for f, top in real.items():
        sv = [-s.R[K.apply(s, r, cd)].sum() for _, _, r in top]
        best = "; ".join(f"{n} ({m:+.2f}→{v:+.1f})" for (m, n, r), v in list(zip(top, sv))[:3])
        L.append(f"- {f}: 2025'te + olan {sum(x > 0 for x in sv)}/10, ortalama kurt_R {np.mean(sv):+.2f} · ilk 3: {best}")


def profile(L: list) -> None:
    b = pd.read_csv(K.ROOT / "output" / "islem_otopsi" / "2026-10-20_1429_all" / "islemler.csv")
    b = b[(b.family == "DAYCOMBO") & b.outcome.isin(["TP", "SL"])].copy()
    b["t0"] = pd.to_datetime(b.entry_utc, utc=True)
    y = b[(b.t0 >= "2026-10-19") & (b.t0 < "2026-10-20") & (b.outcome == "SL")]
    rest = b.drop(y.index)
    cols = [c for c in b.columns if c.startswith(("pre_", "geo_")) and pd.api.types.is_numeric_dtype(b[c])]
    rows = []
    for c in cols:
        x = rest[c].dropna()
        if len(x) < 15:
            continue
        pct = [float((x < v).mean()) for v in y[c]]
        sl, tp = rest[rest.outcome == "SL"][c].median(), rest[rest.outcome == "TP"][c].median()
        rows.append({"özellik": c, "dünkü 3 SL yüzdelik": "/".join(f"{100 * p:.0f}" for p in pct),
                     "uç mu": all(p <= 0.1 for p in pct) or all(p >= 0.9 for p in pct),
                     "diğer SL medyan": sl, "TP medyan": tp})
    t = pd.DataFrame(rows)
    L.append(f"\n## 10-19un 2 SL DAYCOMBOsu, diğer {len(rest)} canlı DAYCOMBO içinde (yüzdelik)")
    L.append(f"Üçü de aynı uçta (≤%10 veya ≥%90) olan özellik: {int(t['uç mu'].sum())} / {len(t)}")
    ext = t[t["uç mu"]]
    if len(ext):
        L.append(K.C.md(ext.drop(columns=["uç mu"])))
    L.append("Beklenen (tesadüf, bağımsız özellikler varsayımıyla): her özellik için 2×0,1² = %2 (yalnız 2 SL; ayrık/0 değerli özellikler anlamsız) → "
             f"{len(t)} özellikte ≈{len(t) * 0.02:.1f}")


def main() -> None:
    L = ["# DAYCOMBO — ek kontroller (ek.py)"]
    reverse(L)
    profile(L)
    txt = "\n".join(L)
    (K.OUT / "ek.md").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
