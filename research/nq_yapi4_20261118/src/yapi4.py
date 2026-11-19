"""yapi4.py — PC-01 put/call, BT-01 genişlik itkisi, VD-01 fiyat–VIX ayrışması. python yapi4.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_yapi3_20261118/src"))
import gunluk3 as M  # noqa: E402

N, V = M.N, M.V
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"


def by(x: pd.DataFrame, trig: np.ndarray, h: int, side: int, k_end: str, t0: str, t1: str = "2099-01-01", need_off: bool = True) -> dict:
    ep = M.episodes(x, trig, h, side, need_off)
    if ep.empty:
        return {"KESIF": {"n": 0}, "TEST": {"n": 0}}
    return {"KESIF": M.placebo(x, ep[ep.d <= k_end], h, side), "TEST": M.placebo(x, ep[(ep.d >= t0) & (ep.d <= t1)], h, side)}


def pc() -> dict:
    d = pd.read_csv(HERE / "data/equitypc.csv", skiprows=2)
    d.columns = [c.strip() for c in d.columns]
    d["DATE"] = pd.to_datetime(d.DATE.str.strip(), format="mixed")
    s = d.set_index("DATE")["P/C Ratio"].astype(float)
    out = {}
    for t in ("QQQ", "SPY"):
        x = M.N.frame(t)
        p5 = s.rolling(5).mean().reindex(x.index)
        p = p5.rolling(252, min_periods=126).apply(lambda a: (a[:-1] < a[-1]).mean() if np.isfinite(a[-1]) else np.nan, raw=True)
        hi, lo = (p >= 0.8).fillna(False).values, (p <= 0.2).fillna(False).values
        for h in (5, 20):
            out[f"{t}_PC_yuksek_AL_h{h}"] = by(x, hi, h, 1, "2012-12-31", "2013-01-01", "2019-10-31")
            out[f"{t}_PC_dusuk_SAT_h{h}"] = by(x, lo, h, -1, "2012-12-31", "2013-01-01", "2019-10-31")
    return out


def bt() -> dict:
    m = M.mega()[M.STOCKS].dropna(how="all")
    out = {}
    for t in ("QQQ", "SPY"):
        x = M.N.frame(t)
        mm = m.reindex(x.index)
        g = (mm > mm.rolling(10).mean()).sum(axis=1) / mm.notna().sum(axis=1)
        thrust = ((g.rolling(10).min().shift(1) <= 0.25) & (g >= 0.75)).values
        wash = (g <= 1 / 12 + 1e-9).values
        for h in (5, 20):
            out[f"{t}_BT1_itki_h{h}"] = by(x, thrust, h, 1, str(M.KES.date()), str(M.TEST0.date()))
            out[f"{t}_BT2_tukenme_h{h}"] = by(x, wash, h, 1, str(M.KES.date()), str(M.TEST0.date()))
    return out


def vd_frame(t: str) -> pd.DataFrame:
    if t == "NDX":
        return M.V.ndx_frame()
    return M.N.frame(t)


def vd() -> dict:
    vix = V.vix()
    out = {}
    q = M.N.frame("QQQ")
    rq = q.c.pct_change()
    vq = vix.reindex(q.index).pct_change()
    trig = {"VD1_fiyat_up_vix_up": ((rq >= 0.0075) & (vq >= 0.03)).values, "VD2_fiyat_dn_vix_dn": ((rq <= -0.0075) & (vq <= 0)).values}
    sides = {}
    for nm, tr in trig.items():
        for h in (1, 5):
            k = by(q, tr, h, 1, str(M.KES.date()), str(M.TEST0.date()), need_off=False)["KESIF"]
            s = 1 if k.get("fark", 0) >= 0 else -1
            sides[(nm, h)] = s
            out[f"QQQ_{nm}_h{h}"] = {"yon": s, **by(q, tr, h, s, str(M.KES.date()), str(M.TEST0.date()), need_off=False)}
    for t in ("SPY", "NDX"):
        x = vd_frame(t)
        r = x.c.pct_change()
        v = vix.reindex(x.index).pct_change()
        tt = {"VD1_fiyat_up_vix_up": ((r >= 0.0075) & (v >= 0.03)).values, "VD2_fiyat_dn_vix_dn": ((r <= -0.0075) & (v <= 0)).values}
        for nm, tr in tt.items():
            for h in (1, 5):
                s = sides[(nm, h)]
                if t == "NDX":
                    ep = M.episodes(x, tr, h, s, False)
                    out[f"NDX_1990_1999_{nm}_h{h}"] = {"yon": s, **M.placebo(x, ep[(ep.d >= "1990-01-01") & (ep.d <= "1999-02-28")], h, s)}
                else:
                    out[f"SPY_{nm}_h{h}"] = {"yon": s, **by(x, tr, h, s, str(M.KES.date()), str(M.TEST0.date()), need_off=False)}
    return out


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {"PC": pc(), "BT": bt(), "VD": vd()}
    (RES / "yapi4.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for fam, cs in out.items():
        for k, v in cs.items():
            print(fam, k, json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
