"""FX-01 EK-6: H9-KÖR (görülmemiş çiftler), nedensel doz eşiği D (H9-D, H8c-D). Çalıştır: ../../.venv/bin/python -I ek6.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
import hyp  # noqa: E402

TS = json.loads((f.DATA / "tick_spread.json").read_text())["sp"]
BASKET = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD"]
BLIND = ["NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "NZDJPY", "EURGBP", "EURCHF", "EURAUD", "GBPAUD", "AUDCAD",
         "EURCAD", "GBPCHF", "AUDNZD"]
BASE_USD = {"EUR": 1.16, "GBP": 1.33, "AUD": 0.66, "NZD": 0.58, "CAD": 0.72, "USD": 1.0, "CHF": 1.25}
Q, WIN = 0.67, 250


def comm(pair: str) -> float:
    return 7.0 / (100_000 * BASE_USD[pair[:3]]) * 1e4


def cost(pair: str, r: dict, hours: tuple[int, ...]) -> float:
    bar = r["gross"] - r["net"]
    sh = (TS.get(pair) or {}).get("saat")
    tick = np.mean([sh.get(str(h), [0])[0] for h in hours]) if sh else 2 * bar
    return max(bar, tick) + comm(pair)


def london_table(pair: str) -> pd.DataFrame:
    rows = []
    for d in hyp.bdays("2009-11-01", "2026-11-12"):
        pre = hyp.trade(pair, hyp.london(d, 10), hyp.london(d, 16), +1)
        if pre is None:
            continue
        side = -1 if pre["gross"] > 0 else 1
        r = hyp.trade(pair, hyp.london(d, 16), hyp.london(d, 20), side)
        if r is None or pre["gross"] == 0:
            rows.append({"d": d, "pre": pre["gross"], "gross": np.nan, "net": np.nan})
            continue
        rows.append({"d": d, "pre": pre["gross"], "gross": r["gross"], "net": r["gross"] - cost(pair, r, (15, 16, 19, 20))})
    t = pd.DataFrame(rows).set_index("d")
    t["thr"] = t.pre.abs().rolling(WIN, min_periods=200).quantile(Q).shift(1)
    return t


def tokyo_table(pair: str) -> pd.DataFrame:
    got, jbd = hyp.gotobi_days("2009-10-08", "2026-11-12")
    rows = []
    for d in sorted(x for x in jbd if x.dayofweek < 5):
        pre = hyp.trade(pair, d - pd.Timedelta(hours=1), d + pd.Timedelta(hours=1), +1)
        if pre is None:
            continue
        r = hyp.trade(pair, d + pd.Timedelta(hours=1), d + pd.Timedelta(hours=6), -1)
        rows.append({"d": d, "got": d in got, "pre": pre["gross"], "gross": r["gross"] if r else np.nan,
                     "net": (r["gross"] - cost(pair, r, (1, 6))) if r else np.nan})
    t = pd.DataFrame(rows).set_index("d")
    t["thr"] = t.pre.rolling(WIN, min_periods=200).quantile(Q).shift(1)
    return t


def ev_summary(s: pd.Series) -> dict:
    s = s.dropna()
    return {**f.summ(s.reset_index(drop=True), pd.Series(s.index)), "n_gun": int(s.index.nunique())}


def main() -> dict:
    me = set(hyp.last_bdays("2010-11-01", "2026-10-31"))
    res: dict = {"H9_KOR": {}, "H9_D": {}, "H8c_D": {}}
    L = {p: london_table(p) for p in BASKET + BLIND}
    for grp, pairs in (("sepet", BASKET), ("kor", BLIND)):
        m = pd.concat([L[p].assign(p=p) for p in pairs])
        m = m[m.index >= "2010-11-01"]
        a = m[m.index.isin(me)]
        ctl = m[~m.index.isin(me)].groupby(level=0).net.mean()
        ev = a.groupby(level=0).net.mean()
        per = a.groupby("p").net.mean().round(2).to_dict()
        rng = np.random.default_rng(4)
        dd = np.array([rng.choice(ev.dropna().values, ev.notna().sum()).mean() - rng.choice(ctl.dropna().values, ctl.notna().sum()).mean() for _ in range(2000)])
        res["H9_KOR" if grp == "kor" else "H9_sepet_tekrar"] = {**ev_summary(ev), "brut": round(a.gross.mean(), 2), "kontrol": round(ctl.mean(), 2),
            "P_fark": round(float((dd > 0).mean()), 3), "cift": per, "pozitif_cift": f"{sum(v > 0 for v in per.values())}/{len(per)}"}
        ad = a[a.pre.abs() > a.thr]
        evd = ad.groupby(level=0).net.mean()
        res["H9_D"][grp] = {**ev_summary(evd), "brut": round(ad.gross.mean(), 2), "maliyet": round((ad.gross - ad.net).mean(), 2),
            "cift": ad.groupby("p").net.mean().round(2).to_dict(), "bacak": int(len(ad))}
    for p in ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]:
        t = tokyo_table(p)
        t = t[t.index >= "2010-10-12"]
        g = t[t.got & (t.pre > 0)]
        gd = g[g.pre > g.thr]
        c = t[~t.got & (t.pre > 0) & (t.pre > t.thr)]
        res["H8c_D"][p] = {"H8c": ev_summary(g.net), "H8c_D": {**ev_summary(gd.net), "brut": round(gd.gross.mean(), 2),
                           "maliyet": round((gd.gross - gd.net).mean(), 2)}, "kontrol_D": round(c.net.mean(), 2),
                           "yil_D": {int(y): round(v, 1) for y, v in gd.net.groupby(gd.index.year).mean().items()}}
    (f.RES / "ek6.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    return res


if __name__ == "__main__":
    main()
