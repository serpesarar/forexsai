"""so.py — NASDAQ yükseliş serileri + OPEX haftası (PROTOCOL). python so.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_ath_20261118/src"))
import ath  # noqa: E402

lib = ath.lib
RES = ROOT / "research/ndx_seri_opex_20261118/results"
P_B = 1 - 0.05 / 8


def daily(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(ath.D / f"{sym}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"c": d.Close})
    up = (x.c > x.c.shift(1)).astype(int)
    x["streak"] = up.groupby((up == 0).cumsum()).cumsum()
    days = x.index.to_series()
    for h in (1, 5):
        x[f"f{h}"] = (x.c.shift(-h) / x.c - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (days.shift(-h) - days).dt.days.values
    return x


def weekly(x: pd.DataFrame) -> pd.DataFrame:
    iso = x.index.isocalendar()
    wk = (iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)).values
    g = pd.DataFrame({"c": x.c.values, "d": x.index, "wk": wk})
    w = g.groupby("wk").agg(d=("d", "max"), c=("c", "last"), first=("d", "min")).sort_values("d").reset_index()
    fr = w.d - pd.to_timedelta(w.d.dt.weekday - 4, unit="D")          # haftanın Cuması
    w["opex"] = (fr.dt.day >= 15) & (fr.dt.day <= 21)
    w["ceyrek"] = w.opex & fr.dt.month.isin([3, 6, 9, 12])
    w["r"] = (w.c / w.c.shift(1) - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (w.d - w.d.shift(1)).dt.days
    w["after"] = w.opex.shift(1).fillna(False).astype(bool)
    w["after_q"] = w.ceyrek.shift(1).fillna(False).astype(bool)
    return w.dropna()


def judge(rec: dict, P: float, kor: dict) -> str:
    fs = [rec[e]["fark"] for e in ("KESIF", "TEST", "YENI")]
    sg = np.sign(np.mean(fs))
    same = all(np.sign(f) == sg for f in fs)
    k = sum(np.sign(v) == sg for v in kor.values()) >= 2
    pp = P if sg > 0 else 1 - P
    return ("B" if same and k and pp >= P_B else ("C+" if same and k else "X")) + (" (artı)" if sg > 0 else " (eksi)")


ERAS = ath.ERAS


def main() -> None:
    RES.mkdir(exist_ok=True)
    X = {s: daily(s) for s in ("QQQ", "SPY", "DIA", "IWM")}
    W = {s: weekly(X[s]) for s in X}
    out = {}
    for N in (4, 6):
        for h in (1, 5):
            col = f"f{h}"
            q = X["QQQ"].dropna(subset=[col])
            rec = {}
            for e, a, b in ERAS:
                z = q[(q.index >= a) & (q.index <= b)]
                m = (z.streak >= N).values
                rec[e] = {"n": int(m.sum()), "ort": round(float(z[col][m].mean()), 1), "taban": round(float(z[col].mean()), 1)}
                rec[e]["fark"] = round(rec[e]["ort"] - rec[e]["taban"], 1)
            m = (q.streak >= N).values
            P = ath.bboot(q[col].values[m], q[col].values, max(h, 1))
            kor = {s: round(float(X[s].dropna(subset=[col]).pipe(lambda y: y[col][y.streak >= N].mean() - y[col].mean())), 1) for s in ("SPY", "DIA", "IWM")}
            rec.update({"P": round(P, 4), "kor": kor, "hukum": judge(rec, P, kor)})
            out[f"S_N{N}_h{h}"] = rec
            print(f"S N{N} h{h}", json.dumps(rec, ensure_ascii=False), flush=True)
    for nm, col in (("O1", "opex"), ("O2", "after"), ("O3", "ceyrek"), ("O4", "after_q")):
        w = W["QQQ"]
        rec = {}
        for e, a, b in ERAS:
            z = w[(w.d >= a) & (w.d <= b)]
            m = z[col].values
            rec[e] = {"n": int(m.sum()), "ort": round(float(z.r[m].mean()), 1), "taban": round(float(z.r[~m].mean()), 1)}
            rec[e]["fark"] = round(rec[e]["ort"] - rec[e]["taban"], 1)
        m = w[col].values
        r = np.random.default_rng(3)
        a, b = w.r.values[m], w.r.values[~m]
        P = float((r.choice(a, (8000, len(a))).mean(1) - r.choice(b, (8000, len(b))).mean(1) > 0).mean())
        kor = {s: round(float(W[s].r[W[s][col]].mean() - W[s].r[~W[s][col]].mean()), 1) for s in ("SPY", "DIA", "IWM")}
        rec.update({"P": round(P, 4), "kor": kor, "hukum": judge(rec, P, kor)})
        out[nm] = rec
        print(nm, json.dumps(rec, ensure_ascii=False), flush=True)
    (RES / "seri_opex.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
