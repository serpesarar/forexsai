"""fh.py — FX habere dayanan / habersiz büyük günlük hareket → ertesi gün (PROTOCOL). python fh.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/fx_secim_20261113"))
import fx_core as F  # noqa: E402

RES = ROOT / "research/fx_haber_20261118/results"
MAJ = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"]
KOR = ["AUDCAD", "AUDJPY", "AUDNZD", "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "GBPAUD", "GBPCHF", "GBPJPY", "NZDJPY"]
KS = (1.5, 2.0)
START, END = pd.Timestamp("2008-01-01"), pd.Timestamp("2026-10-02")
ERAS = (("KESIF", "2008-01-01", "2015-12-31"), ("TEST", "2016-01-01", "2021-10-31"), ("YENI", "2021-11-01", "2026-10-02"))


def cost_bp(pair: str, point: float) -> float:
    h = F.load(pair, "H1")
    h = h[h.utc >= pd.Timestamp("2018-01-01")]
    return float(F.spread_bp(h, point).median() * 1.5)


def table(pair: str, ev: set, meta: dict) -> pd.DataFrame:
    x = F.load(pair, "D1")
    x["d"] = (x.et + pd.Timedelta(hours=7)).dt.normalize()     # sunucu günü (NY 17:00'da başlar) → takvim günü
    x = x[(x.d >= START - pd.Timedelta(days=60)) & (x.d <= END + pd.Timedelta(days=5))].reset_index(drop=True)
    r = x.c.pct_change()
    sig = r.shift(1).rolling(20).std()
    nxt = x.c.shift(-1) / x.c - 1
    c = cost_bp(pair, meta[pair]["point"])
    df = pd.DataFrame({"d": x.d, "r": r, "sig": sig, "f": -np.sign(r) * nxt * 1e4 - c})
    df["olay"] = df.d.dt.date.isin(ev)
    df["pair"] = pair
    df = df[(df.d >= START) & (df.d <= END)].dropna()
    return df


def boot(v: np.ndarray, g: np.ndarray, n: int = 4000) -> float:
    return F.boot_p(v, g, n)


def main() -> None:
    RES.mkdir(exist_ok=True)
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.date)
    meta = F.meta()
    T = pd.concat([table(p, ev, meta) for p in MAJ + KOR])
    T["uni"] = np.where(T.pair.isin(MAJ), "ANA", "KOR")
    out = {}
    for k in KS:
        big = T[T.r.abs() >= k * T.sig]
        rec = {}
        for uni in ("ANA", "KOR"):
            u = big[big.uni == uni]
            for grp, m in (("habersiz", ~u.olay), ("olay", u.olay)):
                y = u[m]
                rr = {}
                for nm, a, b in ERAS:
                    z = y[(y.d >= a) & (y.d <= b)]
                    rr[nm] = {"n": int(len(z)), "ort": round(float(z.f.mean()), 2)}
                rr["TUM"] = {"n": int(len(y)), "ort": round(float(y.f.mean()), 2), "P": round(boot(y.f.values, y.d.astype(str).values), 4)}
                rec[f"{uni}_{grp}"] = rr
            rec[f"{uni}_DD"] = {nm: round(rec[f"{uni}_habersiz"][nm]["ort"] - rec[f"{uni}_olay"][nm]["ort"], 2) for nm in ("KESIF", "TEST", "YENI", "TUM")}
        A = rec["ANA_habersiz"]
        ok1 = all(A[nm]["ort"] > 0 for nm in ("KESIF", "TEST", "YENI"))
        ok2 = A["TUM"]["P"] >= 0.975
        ok3 = rec["KOR_habersiz"]["TUM"]["ort"] > 0
        rec["hukum_kural"] = "B" if ok1 and ok2 and ok3 else ("C+" if ok1 and ok3 else ("C" if ok1 else "X"))
        rec["ilke_FX"] = bool(all(rec["ANA_DD"][nm] > 0 for nm in ("KESIF", "TEST", "YENI")))
        bp = big[(big.uni == "ANA") & ~big.olay]
        rec["cift"] = {p: [int(len(g)), round(float(g.f.mean()), 1)] for p, g in bp.groupby("pair")}
        out[f"k{k}"] = rec
        print(f"k{k}: kural {rec['hukum_kural']} | ilke {rec['ilke_FX']}")
        for key in ("ANA_habersiz", "ANA_olay", "KOR_habersiz", "KOR_olay"):
            print(f"  {key}: {rec[key]}")
        print(f"  ANA_DD {rec['ANA_DD']} | KOR_DD {rec['KOR_DD']}\n  çift {rec['cift']}", flush=True)
    (RES / "fx_haber.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
