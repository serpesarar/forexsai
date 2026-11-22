"""kq8_analiz.py — KQ-08 (PROTOCOL.md): KQ-06 yapısında aynı ortalama lotta zarar ve maks. düşüşü azaltan lot aileleri.

python kq8_analiz.py → results/analiz8.json
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kq6_analiz as K6  # noqa: E402

V = K6.V
CELL = K6.CELLS["E2_U0_h0.5"]
US = ["NDX", "GSPC", "DJI", "RUT"]
TESTS = ["DUKA_NDX", "MT5_NAS100", "EET30", "NQ", "G2016_NDX"]


def trades() -> pd.DataFrame:
    P = pickle.load(open(HERE / "cache/yollar2.pkl", "rb"))
    rows = []
    for ev in P:
        if ev["idx"] == "GDAXI" or (ev["set"] == "KESIF" and ev["idx"] not in US):
            continue
        r, s = K6.sim(ev, CELL)
        if not np.isfinite(r):
            continue
        d = pd.Timestamp(ev["d"])
        grp = "G2016_" + ev["idx"] if ev["set"] == "G2016" else ev["set"]
        rows.append({"grp": grp, "idx": ev["idx"], "d": d, "pnl": r, "dvol": ev["dvol"], "vix": V._prev(V.VIXS, d),
                     "exit_d": d + pd.tseries.offsets.BDay(int(s) + 1)})
    return pd.DataFrame(rows).sort_values(["grp", "d"]).reset_index(drop=True)


def weights(x: pd.DataFrame, fam: str, ref: dict) -> np.ndarray:
    n = len(x)
    w = np.ones(n)
    if fam in ("L1", "L5", "L6"):
        w = np.clip(ref["dvol"] / x.dvol.values, 0.25, 2.0)
    if fam == "L2":
        w = np.clip(ref["vix"] / x.vix.values, 0.25, 2.0)
    if fam in ("L3_300", "L3_600", "L5", "L4", "L6"):
        X = 300 if fam in ("L3_300", "L5") else 600
        eq, peak = 0.0, 0.0
        last_loss_exit = None
        out = w.copy()
        for i in range(n):
            m = 1.0
            if fam.startswith("L3") or fam == "L5":
                if peak - eq >= X:
                    m = 0.5
            if fam in ("L4", "L6") and last_loss_exit is not None and (x.d.iloc[i] - last_loss_exit).days <= 14:
                m = 0.5
            out[i] = w[i] * m
            eq += out[i] * x.pnl.iloc[i]
            peak = max(peak, eq)
            if x.pnl.iloc[i] < 0:
                last_loss_exit = x.exit_d.iloc[i]
        w = out
    return w


def metrics(x: pd.DataFrame, w: np.ndarray, k: float) -> dict:
    v = x.pnl.values * w * k
    eq = np.cumsum(v)
    dd = float((eq - np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:]).min())
    loss = v[v < 0]
    days = pd.bdate_range(x.d.min(), x.d.max())
    s = pd.Series(v, index=x.d.values).groupby(level=0).sum().reindex(days).fillna(0)
    return {"n": len(x), "ort_w": round(float((w * k).mean()), 3), "ort": round(float(v.mean()), 1), "ort_zarar": round(float(loss.mean()), 1) if len(loss) else 0.0,
            "maks_dusus": round(dd, 0), "cvar5": round(float(np.sort(v)[:max(1, len(v) // 20)].mean()), 0),
            "sharpe": round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan}


def main() -> None:
    T = trades()
    K = T[T.grp == "KESIF"].sort_values("d").reset_index(drop=True)
    ref = {"dvol": float(K.dvol.median()), "vix": float(K.vix.median())}
    fams = ["BASE", "L1", "L2", "L3_300", "L3_600", "L4", "L5", "L6"]
    out = {"ref": ref, "kesif": {}, "test": {}, "duz_lot_0_4": {}}
    base_k = metrics(K, np.ones(len(K)), 1.0)
    scale = {}
    for f in fams:
        w = np.ones(len(K)) if f == "BASE" else weights(K, f, ref)
        scale[f] = 1.0 / w.mean()
        m = metrics(K, w, scale[f])
        m["zarar_orani"] = round(m["ort_zarar"] / base_k["ort_zarar"], 3)
        m["dusus_orani"] = round(m["maks_dusus"] / base_k["maks_dusus"], 3)
        out["kesif"][f] = m
    cand = [f for f in fams if f != "BASE"]
    sel = max(cand, key=lambda f: min(1 - out["kesif"][f]["zarar_orani"], 1 - out["kesif"][f]["dusus_orani"]))
    out["secilen"] = sel
    for g in TESTS:
        x = T[T.grp == g].sort_values("d").reset_index(drop=True)
        b = metrics(x, np.ones(len(x)), 1.0)
        res = {"BASE": b, "duz_0_4": metrics(x, np.ones(len(x)), 0.4)}
        for f in cand:
            m = metrics(x, weights(x, f, ref), scale[f])
            m["zarar_orani"] = round(m["ort_zarar"] / b["ort_zarar"], 3) if b["ort_zarar"] else np.nan
            m["dusus_orani"] = round(m["maks_dusus"] / b["maks_dusus"], 3) if b["maks_dusus"] else np.nan
            m["kar_orani"] = round(m["ort"] / b["ort"], 3) if b["ort"] else np.nan
            res[f] = m
        out["test"][g] = res
    d = out["test"]["DUKA_NDX"][sel]
    ok = {"zarar_40": d["zarar_orani"] <= 0.40, "dusus_40": d["dusus_orani"] <= 0.40, "kar_60": d["kar_orani"] >= 0.60,
          "sharpe": d["sharpe"] >= out["test"]["DUKA_NDX"]["BASE"]["sharpe"],
          "mt5_eet30_70": all(out["test"][g][sel]["zarar_orani"] <= 0.70 and out["test"][g][sel]["dusus_orani"] <= 0.70 for g in ("MT5_NAS100", "EET30"))}
    out["olcut"], out["hedef"] = ok, all(ok.values())
    json.dump(out, open(HERE / "results/analiz8.json", "w"), ensure_ascii=False, indent=1, default=float)
    print("secilen", sel, "hedef", out["hedef"], ok)
    for g in TESTS:
        print(g, {f: (v.get("zarar_orani"), v.get("dusus_orani"), v.get("kar_orani"), v["sharpe"], v["ort_w"]) for f, v in out["test"][g].items() if f in ("BASE", "duz_0_4", sel, "L1", "L3_300")})
    print("KESIF", {f: (v["zarar_orani"], v["dusus_orani"], v["sharpe"]) for f, v in out["kesif"].items()})


if __name__ == "__main__":
    main()
