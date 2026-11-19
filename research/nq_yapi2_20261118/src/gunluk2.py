"""gunluk2.py — NB-01 çekişme, NB-02 yoğunlaşma, NB-03 kredi uyumsuzluğu. python gunluk2.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_akis_20261118/src"))
import gunluk as U  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
DATA, RES = HERE / "data", HERE / "results"
ERAS = [("KESIF", "1990-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31")]


def load(t: str) -> pd.DataFrame:
    d = pd.read_parquet(DATA / f"{t}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    f = d["Adj Close"] / d["Close"]
    return pd.DataFrame({"o": d.Open * f, "c": d["Adj Close"]}).dropna()


def frame(t: str) -> pd.DataFrame:
    x = U.frame(load(t).c)
    x["o"] = load(t).o
    return x


def pct(s: pd.Series) -> pd.Series:
    return s.rolling(504, min_periods=252).apply(lambda a: (a[:-1] < a[-1]).mean() if np.isfinite(a[-1]) else np.nan, raw=True)


def grid(x: pd.DataFrame, cells: dict, fixed_side: dict | None = None) -> dict:
    out = {}
    for k, m in cells.items():
        for h in (5, 20):
            if fixed_side:
                s = fixed_side[k]
            else:
                kz = U.cell(x[(x.index >= ERAS[0][1]) & (x.index <= ERAS[0][2])], m, h, 1)
                s = 1 if kz.get("fark_yonlu", 0) >= 0 else -1
            out[f"{k}_h{h}"] = {"yon": s, **U.by_era(x, m, h, s, ERAS)}
    return out


def nb01(t: str) -> dict:
    x = frame(t)
    on = np.log(x.o / x.c.shift(1))
    idr = np.log(x.c / x.o)
    p = pct(on.rolling(20).sum() - idr.rolling(20).sum())
    r = grid(x, {"ust": p >= 0.8, "alt": p <= 0.2})
    on_f = on[::-1].rolling(20).sum()[::-1].shift(-1) * 1e4
    id_f = idr[::-1].rolling(20).sum()[::-1].shift(-1) * 1e4
    r["bilesen_20g"] = {e: {k: {"gece": round(float(on_f[m & (x.index >= a) & (x.index <= b)].mean()), 1),
                                "gun_ici": round(float(id_f[m & (x.index >= a) & (x.index <= b)].mean()), 1)}
                            for k, m in (("ust", p >= 0.8), ("alt", p <= 0.2), ("tum", p.notna()))} for e, a, b in ERAS}
    return r


def nb02(t: str, ew: str) -> dict:
    x = frame(t)
    rel = np.log(x.c / load(ew).c.reindex(x.index))
    p = pct(rel - rel.shift(20))
    return grid(x, {"dar": p >= 0.8, "genis": p <= 0.2})


def nb03(t: str) -> dict:
    x = frame(t)
    kr = np.log(load("HYG").c / load("IEF").c).reindex(x.index)
    p = pct(kr - kr.shift(20))
    r20 = x.c / x.c.shift(20) - 1
    return grid(x, {"D1_SAT": (r20 > 0) & (p <= 0.2), "D2_AL": (r20 < 0) & (p >= 0.8)}, {"D1_SAT": -1, "D2_AL": 1})


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {"NB01_QQQ": nb01("QQQ"), "NB01_SPY": nb01("SPY"), "NB02_QQQ_QQQE": nb02("QQQ", "QQQE"), "NB02_SPY_RSP": nb02("SPY", "RSP"),
           "NB03_QQQ": nb03("QQQ"), "NB03_SPY": nb03("SPY")}
    (RES / "gunluk2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for fam, cs in out.items():
        for c, v in cs.items():
            if c.startswith("bilesen"):
                print(fam, c, v)
                continue
            print(fam, c, "yon", v["yon"], {e: (z.get("n"), z.get("net"), z.get("fark_yonlu"), z.get("P"), z.get("yil_arti")) for e, z in v.items() if e != "yon"})


if __name__ == "__main__":
    main()
