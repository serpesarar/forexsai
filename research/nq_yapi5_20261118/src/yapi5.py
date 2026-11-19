"""yapi5.py — CS-01 çapraz şok, AR-01 rejime göre sert gün, VM-01 oynaklık-yönetimli tutuş. python yapi5.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_yapi3_20261118/src"))
import gunluk3 as M  # noqa: E402

N, V, FIN = M.N, M.V, M.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
K, T0 = str(M.KES.date()), str(M.TEST0.date())


def cap() -> pd.DataFrame:
    d = pd.read_parquet(HERE / "data/capraz.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d


def frames() -> dict:
    return {"QQQ": N.frame("QQQ"), "SPY": N.frame("SPY"), "NDX": V.ndx_frame()}


def era(x: pd.DataFrame, trig: np.ndarray, h: int, side: int) -> dict:
    ep = M.episodes(x, trig, h, side, need_off=False)
    if ep.empty:
        return {"KESIF": {"n": 0}, "TEST": {"n": 0}}
    return {"KESIF": M.placebo(x, ep[ep.d <= K], h, side), "TEST": M.placebo(x, ep[ep.d >= T0], h, side)}


def old(x: pd.DataFrame, trig: np.ndarray, h: int, side: int) -> dict:
    ep = M.episodes(x, trig, h, side, need_off=False)
    return M.placebo(x, ep[(ep.d >= "1985-10-01") & (ep.d <= "1999-02-28")], h, side) if not ep.empty else {"n": 0}


def shocks(x: pd.DataFrame, c: pd.DataFrame) -> dict:
    cc = c.reindex(x.index)
    oil, gold, usd = cc["CL=F"].pct_change(fill_method=None), cc["GC=F"].pct_change(fill_method=None), cc["DX-Y.NYB"].pct_change(fill_method=None)
    tnx = cc["^TNX"].diff()
    return {"petrol_up": oil >= 0.04, "petrol_dn": oil <= -0.04, "altin_up": gold >= 0.02, "altin_dn": gold <= -0.02,
            "dolar_up": usd >= 0.01, "dolar_dn": usd <= -0.01, "faiz_up": tnx >= 0.10, "faiz_dn": tnx <= -0.10}


def cs() -> dict:
    F, c = frames(), cap()
    out = {}
    sq = shocks(F["QQQ"], c)
    for nm, m in sq.items():
        for h in (1, 5):
            tr = m.fillna(False).values
            k = era(F["QQQ"], tr, h, 1)["KESIF"]
            s = 1 if k.get("fark", 0) >= 0 else -1
            rec = {"yon": s, "QQQ": era(F["QQQ"], tr, h, s)}
            ss = shocks(F["SPY"], c)[nm].fillna(False).values
            rec["SPY"] = era(F["SPY"], ss, h, s)
            if nm.startswith(("dolar", "faiz")):
                rec["NDX_1985_1999"] = old(F["NDX"], shocks(F["NDX"], c)[nm].fillna(False).values, h, s)
            out[f"{nm}_h{h}"] = rec
    return out


def ar() -> dict:
    out = {}
    for t, x in frames().items():
        r = x.c.pct_change()
        s200 = x.c.rolling(200).mean()
        ar1 = ((x.c < s200) & (r >= 0.02)).values
        ar2 = ((x.c > s200) & (r <= -0.02)).values
        for h in (1, 5):
            if t == "NDX":
                out[f"NDX_1985_1999_AR1_SAT_h{h}"] = old(x, ar1, h, -1)
                out[f"NDX_1985_1999_AR2_AL_h{h}"] = old(x, ar2, h, 1)
            else:
                out[f"{t}_AR1_SAT_h{h}"] = era(x, ar1, h, -1)
                out[f"{t}_AR2_AL_h{h}"] = era(x, ar2, h, 1)
    return out


def stats(rr: np.ndarray) -> dict:
    eq = np.cumprod(1 + rr)
    return {"yillik_%": round(float((eq[-1] ** (252 / len(rr)) - 1) * 100), 1), "sharpe": round(float(rr.mean() / rr.std() * np.sqrt(252)), 2),
            "maxDD_%": round(float((eq / np.maximum.accumulate(eq) - 1).min() * 100), 1)}


def vm() -> dict:
    out = {}
    slices = (("1990s", "1990-01-01", "1999-12-31"), ("2000s", "2000-01-01", "2009-12-31"), ("2010s", "2010-01-01", "2019-12-31"),
              ("2020_2021", "2020-01-01", "2021-10-31"), ("TEST", "2021-11-01", "2026-12-31"))
    for t, x in frames().items():
        r = x.c.pct_change().fillna(0).values
        rv = (np.log(x.c).diff().rolling(20).std() * np.sqrt(252)).shift(1)
        var = rv ** 2
        w_var = np.clip((var.rolling(252, min_periods=126).mean() / var).values, 0, 2)
        w_vol = np.clip((rv.rolling(252, min_periods=126).mean() / rv).values, 0, 2)
        res = {}
        for nm, w in (("al_tut", np.ones(len(r))), ("ters_varyans", np.nan_to_num(w_var, nan=1.0)), ("ters_oynaklik", np.nan_to_num(w_vol, nan=1.0))):
            dw = np.abs(np.diff(np.r_[w[0], w]))
            net = w * r - 2e-4 * dw - (w - 1).clip(min=0) * FIN / 1e4 * 1.4
            for sn, a, b in slices:
                m = (x.index >= a) & (x.index <= b)
                if m.sum() < 200:
                    continue
                res.setdefault(sn, {})[nm] = {**stats(net[m]), "ort_w": round(float(w[m].mean()), 2)}
        out[t] = res
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {"CS": cs(), "AR": ar(), "VM": vm()}
    (RES / "yapi5.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, v in out["CS"].items():
        print("CS", k, "yon", v["yon"], {s: {e: (z.get("n"), z.get("fark"), z.get("yuzdelik")) for e, z in (vv.items() if "KESIF" in vv else [("1985_99", vv)])} for s, vv in v.items() if s != "yon"})
    for k, v in out["AR"].items():
        print("AR", k, v)
    for t, r in out["VM"].items():
        for sn, d in r.items():
            print("VM", t, sn, d)


if __name__ == "__main__":
    main()
