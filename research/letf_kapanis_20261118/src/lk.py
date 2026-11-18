"""lk.py — LETF kapanış dengelemesi (PROTOCOL). python lk.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/algo_tuzak_20261118/src", "research/moc_pencere_20261118/src", "research/fitil_kesisim_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import at  # noqa: E402
import moc  # noqa: E402
import ksg_ek2 as E  # noqa: E402

G = at.G
RES = ROOT / "research/letf_kapanis_20261118/results"
NY = "America/New_York"


def table(b: pd.DataFrame, step: int, e45: int) -> pd.DataFrame:
    mins = [570, 930, e45, 960]
    dp = G.day_prices(b, NY, mins, step)
    days = [z for z in dp.index if z.weekday() < 5 and G.nyse_ok(z) and all(np.isfinite(dp.loc[z, f"o{m}"]) for m in mins)]
    D = dp.loc[days].copy()
    nd = pd.Series(days).shift(-1)
    nxt930 = dp.reindex(nd.values)["o570"].values if "o570" in dp else None
    rows = []
    for ent, lab in ((930, "1530"), (e45, "1545")):
        R = D[f"o{ent}"] / D.o570 - 1
        sig = R.shift(1).rolling(20, min_periods=15).std()
        side = np.sign(R)
        pin = np.where(side > 0, D[f"o{ent}"] + D[f"s{ent}"], D[f"o{ent}"])
        pout = np.where(side > 0, D.o960, D.o960 + D.s960)
        net = side * (pout / pin - 1) * 1e4
        extra = 0.5 * (D[f"s{ent}"] + D.s960) / D[f"o{ent}"] * 1e4
        on = side * (nxt930 / D.o960.values - 1) * 1e4 if nxt930 is not None else np.full(len(D), np.nan)
        for d, r_, s_, v, x_, o_ in zip(days, R.values, sig.values, net, extra.values, on):
            rows.append({"d": d, "giris": lab, "R": r_, "sig": s_, "net": v, "n15": v - x_, "gece_devam": o_, "era": at.era_of(d)})
    return pd.DataFrame(rows).dropna(subset=["sig"])


def st(z: pd.DataFrame) -> dict:
    if len(z) < 3:
        return {"n": int(len(z))}
    P = G.KS.diff_p(z.net.values, z.d.astype(str).values, np.zeros(1), np.array(["x"]), n=3000)
    return {"n": int(len(z)), "ort": round(float(z.net.mean()), 2), "s15": round(float(z.n15.mean()), 2), "isabet": round(float((z.net > 0).mean()), 3),
            "t": round(float(z.net.mean() / (z.net.std(ddof=1) / np.sqrt(len(z)))), 2), "P": round(float(P), 4),
            "gece_devam": round(float(z.gece_devam.mean()), 1)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    T = {"DUKA": table(G.ndx_bars(), 60, 945), "MT5_2m": table(*moc.mt5_2m(), 944), "NQ_5m": table(*E.bars("NQ"), 945)}
    out = {}
    cells = [(g, k) for g in ("1530", "1545") for k in (1.0, 1.5)]
    for g, k in cells:
        rec = {}
        for nm, df in T.items():
            z = df[(df.giris == g) & (df.R.abs() >= k * df.sig)]
            rec[nm] = {e: st(z[z.era == e]) for e in ("ESKI_YAPI", "KESIF", "TEST")}
        out[f"{g}_k{k}"] = rec
        print(g, k, "DUKA", rec["DUKA"], "| MT5 TEST", rec["MT5_2m"]["TEST"], flush=True)
    kes = [(c, out[c]["DUKA"]["KESIF"]) for c in out]
    ok = [(c, s) for c, s in kes if s.get("n", 0) >= 50 and s.get("ort", -1) > 0 and s.get("P", 0) >= 0.90]
    fr = [c for c, s in sorted(ok, key=lambda x: -x[1]["t"])[:2]]
    res = {}
    for c in fr:
        y, m5, e, kz = out[c]["DUKA"]["TEST"], out[c]["MT5_2m"]["TEST"], out[c]["DUKA"]["ESKI_YAPI"], out[c]["DUKA"]["KESIF"]
        okk = {"1_test": bool(y.get("ort", -1) > 0 and y.get("P", 0) >= 0.975), "2_mt5": bool(m5.get("ort", -1) > 0), "3_surtunme": bool(y.get("s15", -1) > 0)}
        hk = "B" if all(okk.values()) else ("C+" if y.get("ort", -1) > 0 and okk["2_mt5"] else "X")
        yap = "son 5 yılda güçlendi" if e.get("ort", 0) < min(kz.get("ort", 0), y.get("ort", 0)) else "—"
        res[c] = {"olcut": okk, "hukum": hk, "yapi": yap}
    # doz: tüm dönem DUKA 15:45, |R| beşte bir
    z = T["DUKA"][T["DUKA"].giris == "1545"].copy()
    z["q"] = pd.qcut(z.R.abs(), 5, labels=False)
    doz = {e: {int(q): round(float(g.net.mean()), 2) for q, g in z[z.era == e].groupby("q")} for e in ("ESKI_YAPI", "KESIF", "TEST")}
    out["_dondurulan"], out["_hukum"], out["_doz_1545"] = fr, res, doz
    print("dondurulan:", fr, res)
    print("doz (|R| beşte bir, 15:45→16:00 net bp):", doz)
    (RES / "letf.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
