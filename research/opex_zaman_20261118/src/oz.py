"""oz.py — OPEX penceresi çapa × tutuş ızgarası (zaman çıkışı). python oz.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/son4_20261118/src"))
import ox  # noqa: E402
import hp  # noqa: E402

G, KD, V = ox.G, ox.KD, ox.V
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
NY = "America/New_York"
ANCH = {"SAL16": (-3, 16, 0), "CAR0930": (-2, 9, 30), "CAR16": (-2, 16, 0), "PER0930": (-1, 9, 30), "PER16": (-1, 16, 0),
        "CUM0930": (0, 9, 30), "CUM16": (0, 16, 0), "PZT0930": (1, 9, 30)}
HOLDS = {"1sa": 60, "5sa": 300, "1gun": 1440, "1_5gun": 2160}
FIN = V.FIN


def calendar() -> tuple[pd.DatetimeIndex, set, list]:
    idx = pd.DatetimeIndex(sorted(set(V.ndx_frame().index) | set(V.ohlc("QQQ").index)))
    idx = idx[idx >= "2015-06-01"]
    oxd = ox.opex_days(idx)
    fr = [d for d in idx if d.dayofweek == 4 and d not in oxd]
    return idx, oxd, fr


def ts(d: pd.Timestamp, hh: int, mm: int) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def cells(b: pd.DataFrame, step: int, idx: pd.DatetimeIndex, oxd: set, fr: list) -> pd.DataFrame:
    t, o, sp = b.t.values, b.o.values, b.sp.values
    pos = {d: i for i, d in enumerate(idx)}
    tol = 300 if step == 60 else step
    rows = []
    for F, is_ox in [(f, True) for f in sorted(oxd)] + [(f, False) for f in fr]:
        i = pos[F]
        for an, (off, hh, mm) in ANCH.items():
            if not 0 <= i + off < len(idx):
                continue
            u = ts(idx[i + off], hh, mm)
            k = int(np.searchsorted(t, u))
            if k >= len(t) or t[k] - u > tol:
                continue
            for hn, hm in HOLDS.items():
                j = k + max(1, hm * 60 // step)
                if j >= len(t):
                    continue
                g = (o[j] / o[k] - 1) * 1e4
                nl = (o[j] / (o[k] + sp[k]) - 1) * 1e4 - FIN * hm / 1440
                ns = -((o[j] + sp[j]) / o[k] - 1) * 1e4
                rows.append({"F": F, "opex": is_ox, "cell": f"{an}_{hn}", "g": g, "nl": nl, "ns": ns})
    return pd.DataFrame(rows)


def stat(z: pd.DataFrame, side: int | None = None) -> dict:
    a, b = z[z.opex], z[~z.opex]
    if len(a) < 8:
        return {"n": int(len(a))}
    d = a.g.mean() - b.g.mean()
    se = np.sqrt(a.g.var(ddof=1) / len(a) + b.g.var(ddof=1) / len(b))
    s = side if side is not None else (1 if d >= 0 else -1)
    r = np.random.default_rng(61)
    bs = r.choice(a.g.values, (4000, len(a))).mean(1) - r.choice(b.g.values, (4000, len(b))).mean(1)
    net = a.nl if s > 0 else a.ns
    return {"yon": s, "n": int(len(a)), "opex_g": round(float(a.g.mean()), 1), "kontrol_g": round(float(b.g.mean()), 1),
            "fark": round(float(d), 1), "t": round(float(d / se), 2), "P_yon": round(float(((s * bs) > 0).mean()), 4),
            "islem_net": round(float(net.mean()), 1), "isabet": round(float((net > 0).mean()), 3)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    idx, oxd, fr = calendar()
    h1 = cells(hp.h1_bars(), 3600, idx, oxd, fr)
    h1 = h1[h1.F <= "2018-03-31"]
    du = cells(G.ndx_bars(), 60, idx, oxd, fr)
    kes = pd.concat([h1, du[(du.F >= "2018-04-01") & (du.F <= "2021-10-31")]], ignore_index=True)
    test = du[du.F >= "2021-11-01"]
    feeds = {"MT5_NAS100": (KD.mt5_m30("NAS100"), 1800, "2021-11-01"), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800, "2018-06-01"),
             "MT5_US30": (KD.mt5_m30("US30"), 1800, "2018-07-01"), "MT5_US2000": (KD.mt5_m30("US2000"), 1800, "2018-05-01")}
    fz = {nm: cells(b, st, idx, oxd, fr).query("F >= @a") for nm, (b, st, a) in feeds.items()}
    out = {"KESIF": {}, "TEST": {}, "besleme": {}}
    for c, z in kes.groupby("cell"):
        out["KESIF"][c] = stat(z)
    g = pd.DataFrame(out["KESIF"]).T
    g["abs_t"] = g.t.abs()
    ok = g[(g.P_yon >= 0.90)].sort_values("abs_t", ascending=False)
    frozen = list(ok.index[:4])
    out["dondurulan"] = frozen
    for c, z in test.groupby("cell"):
        out["TEST"][c] = stat(z, int(out["KESIF"][c]["yon"]))
    for nm, f in fz.items():
        out["besleme"][nm] = {c: stat(z, int(out["KESIF"][c]["yon"])) for c, z in f.groupby("cell") if c in frozen or True}
    (RES / "oz.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print("KEŞİF n hücre", len(g), "P>=0,90:", len(ok), "dondurulan", frozen)
    print(g.sort_values("abs_t", ascending=False).head(10)[["yon", "n", "opex_g", "kontrol_g", "fark", "t", "P_yon", "islem_net"]].to_string())
    for c in frozen:
        print("\nDONDURULAN", c, "KEŞİF", out["KESIF"][c])
        print("  TEST Duka", out["TEST"].get(c))
        for nm in fz:
            print("  ", nm, out["besleme"][nm].get(c))
    print("\nTEST tüm hücreler (seçilen yönde fark, P):")
    for c in sorted(out["TEST"]):
        v = out["TEST"][c]
        print(f"  {c:16s} yön {v.get('yon')} fark {v.get('fark')} P {v.get('P_yon')} net {v.get('islem_net')}")


if __name__ == "__main__":
    main()
