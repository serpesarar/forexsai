"""vs.py — VS VIX vade (uzlaşma) haftası pencereleri. python vs.py"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_yapi3_20261118/src"))
import gunluk3 as M  # noqa: E402

V, FIN = M.V, M.FIN
RES = Path(__file__).resolve().parents[1] / "results"
ERAS = (("PLASEBO_cag", "1993-01-01", "2004-02-29"), ("KESIF", "2004-03-01", "2015-12-31"), ("TEST", "2016-01-01", "2026-12-31"),
        ("SON5", "2021-11-01", "2026-12-31"))


def third_friday(y: int, m: int) -> date:
    d = date(y, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def expiries(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    tdays = set(idx)
    out = []
    for y in range(1990, 2027):
        for m in range(1, 13):
            ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
            e = pd.Timestamp(third_friday(ny, nm) - timedelta(days=30))
            k = 0
            while e not in tdays and k < 5:
                e -= pd.Timedelta(days=1)
                k += 1
            if e in tdays:
                out.append(e)
    return out


def windows(x: pd.DataFrame, i: int) -> dict:
    o, c, idx = x.o.values, x.c.values, x.index
    if i < 2 or i + 2 >= len(x):
        return {}
    fin = lambda a, b: FIN * (idx[b] - idx[a]).days  # noqa: E731
    return {"W1_pzt_kapanis_car_acilis": (o[i] / c[i - 2] - 1) * 1e4 - 2 - fin(i - 2, i),
            "W2_car_acilis_kapanis": (c[i] / o[i] - 1) * 1e4 - 2,
            "W3_car_kapanis_cuma_kapanis": (c[i + 2] / c[i] - 1) * 1e4 - 2 - fin(i, i + 2),
            "W4_pzt_kapanis_car_kapanis": (c[i] / c[i - 2] - 1) * 1e4 - 2 - fin(i - 2, i)}


def boot(a: np.ndarray, b: np.ndarray) -> float:
    r = np.random.default_rng(17)
    return float((r.choice(a, (5000, len(a))).mean(1) - r.choice(b, (5000, len(b))).mean(1) > 0).mean())


def table(x: pd.DataFrame) -> pd.DataFrame:
    ex = set(expiries(x.index))
    rows = []
    for i, d in enumerate(x.index):
        if d.dayofweek != 2:
            continue
        w = windows(x, i)
        if w:
            rows.append({"d": d, "vade": d in ex, **w})
    # tatil nedeniyle Salı'ya kayan vadeler de dahil
    for d in ex:
        if d.dayofweek != 2:
            i = x.index.get_loc(d)
            w = windows(x, i)
            if w:
                rows.append({"d": d, "vade": True, **w})
    return pd.DataFrame(rows)


def summ(t: pd.DataFrame, sides: dict | None) -> dict:
    out = {}
    for e, a, b in ERAS:
        z = t[(t.d >= a) & (t.d <= b)]
        rec = {}
        for w in [c for c in t.columns if c.startswith("W")]:
            v, bb = z[z.vade][w].dropna().values, z[~z.vade][w].dropna().values
            if len(v) < 10:
                continue
            s = sides[w] if sides else 1
            diff = s * (v.mean() - bb.mean())
            se = np.sqrt(v.var(ddof=1) / len(v) + bb.var(ddof=1) / len(bb))
            rec[w] = {"yon": s, "n": int(len(v)), "vade": round(float(v.mean()), 1), "taban": round(float(bb.mean()), 1),
                      "fark_yonlu": round(float(diff), 1), "t": round(float(diff / se), 2), "P": round(boot(s * v, s * bb), 4)}
        out[e] = rec
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    q = V.ohlc("QQQ")
    tq = table(q)
    k = summ(tq, None)["KESIF"]
    sides = {w: (1 if r["fark_yonlu"] >= 0 else -1) for w, r in k.items()}
    out = {"yon_KESIF_QQQ": sides, "QQQ": summ(tq, sides), "SPY": summ(table(V.ohlc("SPY")), sides)}
    (RES / "vs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print("yön", sides)
    for t in ("QQQ", "SPY"):
        for e, r in out[t].items():
            for w, v in r.items():
                print(t, e, w, v)


if __name__ == "__main__":
    main()
