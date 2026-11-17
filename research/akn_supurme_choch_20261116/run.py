"""PROTOCOL.md (+EK-0) tek koşum → results/hucreler.csv, hukum.json, islemler.parquet."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import akn as A
import mtf as M

RES = Path(__file__).resolve().parent / "results"
N_BOOT, N_PLACEBO = 5000, 200
PERIODS = (("A", "2018-01-01", "2021-01-01"), ("B", "2021-01-01", "2024-01-01"), ("C", "2024-01-01", "2027-01-01"))
HYP = {"P1": ("K1K2n", "C53", "E1", "RT1"), "P2": ("K1K2n", "C53", "E50", "RT1"), "P3": ("K1K2n", "C53", "E50", "RT2")}
EXITS = ["RT1", "RT2", "R1", "R2"]
TGT = {"RT1": "t1_r", "RT2": "t2_r", "R1": None, "R2": None}
XC = {"RT1": "xT1", "RT2": "xT2", "R1": "x1", "R2": "x2"}


def boot(r: np.ndarray, day: np.ndarray) -> float:
    g = pd.DataFrame({"r": r, "d": day}).groupby("d").r.agg(["sum", "count"])
    if len(g) < 2:
        return np.nan
    idx = np.random.default_rng(5).integers(0, len(g), (N_BOOT, len(g)))
    m = g["sum"].to_numpy()[idx].sum(1) / g["count"].to_numpy()[idx].sum(1)
    return float((m > 0).mean())


def st(df: pd.DataFrame, col: str) -> dict:
    if df.empty:
        return {"n": 0, "ortR": np.nan, "isabet_%": np.nan, "P": np.nan}
    r = df[col].to_numpy()
    return {"n": len(r), "ortR": round(float(r.mean()), 4), "isabet_%": round(float((r > 0).mean() * 100), 1),
            "P": round(boot(r, df.day.to_numpy()), 4)}


def period(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    return df[(df.day >= a) & (df.day < b)] if not df.empty else df


def one_pos(df: pd.DataFrame, col: str) -> pd.DataFrame:
    keep, last = [], -1
    for i, r in df.sort_values("f").iterrows():
        if r.f > last:
            keep.append(i)
            last = r[XC[col]]
    return df.loc[keep]


def placebo(cx: A.Ctx, df: pd.DataFrame, col: str) -> np.ndarray:
    B, rng, out = cx.B, np.random.default_rng(31), []
    tg = df[TGT[col]].to_numpy() if TGT[col] else np.full(len(df), {"R1": 1.0, "R2": 2.0}[col])
    w1 = np.array([np.searchsorted(B.um, B.um[t] + A.W3_MIN, side="left") for t in df.t0])
    for _ in range(N_PLACEBO):
        es = rng.integers(df.t0.to_numpy(), np.maximum(df.t0.to_numpy() + 1, np.minimum(w1, len(B.o) - 1)))
        out.append(np.mean([M.placebo_r(B, s, int(e), rk, t, 120) for s, e, rk, t in zip(df.side, es, df.risk, tg)]))
    return np.array(out)


def holm(p: dict) -> dict:
    ok, res = True, {}
    for i, k in enumerate(sorted(p, key=p.get)):
        ok = ok and p[k] <= 0.05 / (len(p) - i)
        res[k] = ok
    return res


def main() -> None:
    t0 = time.time()
    RES.mkdir(exist_ok=True)
    B = A.load()
    cx = A.build(B)
    print("kuruldu", round(time.time() - t0), flush=True)
    allt, rows = [], []
    for chain in ("K1K2n", "K1K2", "K1", "K2", "K0"):
        for ltf in A.LTFS:
            for em in ("E1", "E50"):
                df = A.run(cx, chain, ltf, em)
                if df.empty:
                    continue
                allt.append(df)
                for col in EXITS:
                    for side_lab, d in (("hepsi", df), ("SAT", df[df.side == -1]), ("AL", df[df.side == 1])):
                        row = {"zincir": chain, "ltf": ltf, "giris": em, "cikis": col, "yon": side_lab,
                               **{f"{k}_birlesik": v for k, v in st(d, col).items()}}
                        for p, a, b in PERIODS:
                            s = st(period(d, a, b), col)
                            row[f"{p}_n"], row[f"{p}_ortR"] = s["n"], s["ortR"]
                        rows.append(row)
        print(chain, round(time.time() - t0), flush=True)
    cells = pd.DataFrame(rows)
    cells.to_csv(RES / "hucreler.csv", index=False)
    trades = pd.concat(allt, ignore_index=True)
    trades.to_parquet(RES / "islemler.parquet")

    hk, praw = {}, {}
    for h, (chain, ltf, em, col) in HYP.items():
        df = trades[(trades.chain == chain) & (trades.ltf_v == ltf) & (trades.giris == em)].reset_index(drop=True)
        sp = A.run(cx, chain, ltf, em, spm=1.5)
        mir = A.mirror(cx, df, col)
        pl = placebo(cx, df, col)
        s_all = st(df, col)
        per = {p: st(period(df, a, b), col) for p, a, b in PERIODS}
        mean_mir = float(np.mean(mir)) if len(mir) else np.nan
        pl_pct = float((pl < s_all["ortR"]).mean() * 100)
        s_sp, s_op = st(sp, col), st(one_pos(df, col), col)
        crit = {"1_ABC_hepsi>0": all(per[p]["ortR"] > 0 for p in per),
                "2_P>=0.95": bool(s_all["P"] >= 0.95),
                "3_ayna_plasebo": bool(s_all["ortR"] > mean_mir and pl_pct >= 50),
                "4_spread1.5>0": bool(s_sp["ortR"] > 0), "5_tek_poz>0": bool(s_op["ortR"] > 0),
                "6_n>=150": bool(s_all["n"] >= 150)}
        praw[h] = 1 - s_all["P"]
        hk[h] = {"tanim": [chain, ltf, em, col], "birlesik": s_all, "donem": per, "ayna_ortR": round(mean_mir, 4),
                 "plasebo_ort": round(float(pl.mean()), 4), "plasebo_yuzdelik": pl_pct, "spread1.5": s_sp,
                 "tek_poz": s_op, "SAT": st(df[df.side == -1], col), "AL": st(df[df.side == 1], col),
                 "olcutler": crit}
    hm = holm(praw)
    for h, v in hk.items():
        c = list(v["olcutler"].values())
        v["holm"] = hm[h]
        v["sinif"] = ("B" if all(c) and hm[h] else "B-" if all(c) else
                      "C" if v["birlesik"]["ortR"] > 0 and v["birlesik"]["P"] >= 0.90 else "X")
    (RES / "hukum.json").write_text(json.dumps(hk, ensure_ascii=False, indent=1, default=float))
    for h, v in hk.items():
        print(h, v["sinif"], v["birlesik"], {p: (d["n"], d["ortR"]) for p, d in v["donem"].items()},
              "ayna", v["ayna_ortR"], "plasebo", v["plasebo_ort"], v["plasebo_yuzdelik"], "SAT", v["SAT"]["ortR"],
              "AL", v["AL"]["ortR"], v["olcutler"], flush=True)
    print("bitti", round(time.time() - t0))


if __name__ == "__main__":
    main()
