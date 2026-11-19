"""sn.py — SN NASDAQ yükseliş serisi → zaman çıkışlı uzun. python sn.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/nq_yapi3_20261118/src"))
sys.path.insert(0, str(ROOT / "research/ndx_tf_yapilandirma_20261117/src"))
import gunluk3 as M  # noqa: E402
import kaynak  # noqa: E402

N, V, FIN = M.N, M.V, M.FIN
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
ERAS = (("1985_1999", "1985-10-01", "1999-02-28"), ("1999_2009", "1999-03-01", "2009-12-31"), ("2010_2017", "2010-01-01", "2017-12-31"),
        ("2018_2026", "2018-01-01", "2026-12-31"), ("SON5", "2021-11-01", "2026-12-31"))


def streak(c: pd.Series) -> np.ndarray:
    up = (c > c.shift(1)).astype(int)
    return up.groupby((up == 0).cumsum()).cumsum().values


def broker_daily() -> pd.DataFrame:
    x = pd.read_csv(ROOT / "research/c1_turev_20261105/data/mt5/NAS100_H1.csv.gz")
    t = kaynak.server_to_utc(x["t"].to_numpy())
    ny = pd.to_datetime(t, unit="s", utc=True).tz_convert("America/New_York").tz_localize(None)
    key = (ny + pd.Timedelta(hours=7)).normalize()
    d = pd.DataFrame({"key": key, "c": x.c.values, "sp": x.sp.values * 0.1}).groupby("key").agg(c=("c", "last"), sp=("sp", "last"))
    d = d[d.index.dayofweek < 5]
    d.sp = d.sp.where(d.sp > 0, 1.5)
    return d


def run_frame(x: pd.DataFrame, n_s: int, h: int, cost: float = 2.0) -> pd.DataFrame:
    st = streak(x.c)
    trig = st == n_s
    ep = M.episodes(x, trig, h, 1, need_off=False)
    if cost != 2.0 and not ep.empty:
        ep["net"] = ep.net - (cost - 2.0)
    return ep


def era_tab(x: pd.DataFrame, ep: pd.DataFrame, h: int) -> dict:
    out = {}
    for nm, a, b in ERAS:
        e = ep[(ep.d >= a) & (ep.d <= b)]
        if len(e) >= 5 and x.index[0] <= pd.Timestamp(a) + pd.Timedelta(days=400):
            out[nm] = M.placebo(x, e, h, 1)
        elif len(e) >= 5:
            out[nm] = M.placebo(x, e, h, 1)
    return out


def boot_p(v: np.ndarray) -> float:
    r = np.random.default_rng(2)
    return float((r.choice(v, (5000, len(v))).mean(1) > 0).mean())


def card(x: pd.DataFrame, qo: pd.DataFrame | None) -> dict:
    ep = run_frame(x, 6, 5)
    v = ep.net.values
    half = len(v) // 2
    ep15 = run_frame(x, 6, 5, cost=3.0)
    c = {"1_hacim_n": int(len(v)), "1_gecti": bool(len(v) >= 150),
         "2_ort": round(float(v.mean()), 1), "2_P": round(boot_p(v), 4), "2_gecti": bool(v.mean() > 0 and boot_p(v) >= 0.90),
         "3_yarilar": [round(float(v[:half].mean()), 1), round(float(v[half:].mean()), 1)], "3_gecti": bool(v[:half].mean() >= 0 and v[half:].mean() >= 0),
         "4_surtunme_x1_5": round(float(ep15.net.mean()), 1), "4_gecti": bool(ep15.net.mean() > 0),
         "6_tek_pozisyon": "epizot tutuşta yeni giriş yok", "6_gecti": True}
    if qo is not None:
        # gerçekçi icra: QQQ sinyal günü kapanışında bilinir → ertesi açılış giriş, 5. gün kapanış çıkış
        q = qo
        st = streak(q.c)
        idx = q.index
        rows, busy = [], -1
        for i in range(1, len(q) - 6):
            if st[i] == 6 and i > busy:
                ent = q.o.values[i + 1]
                cal = (idx[i + 5] - idx[i]).days
                rows.append({"opt": (q.c.values[i + 5] / q.c.values[i] - 1) * 1e4 - 2 - FIN * cal,
                             "real": (q.c.values[i + 5] / ent - 1) * 1e4 - 2 - FIN * cal})
                busy = i + 5
        r = pd.DataFrame(rows)
        c["5_iyimser_kapanis"] = round(float(r.opt.mean()), 1)
        c["5_gercek_ertesi_acilis"] = round(float(r.real.mean()), 1)
        c["5_gecti"] = bool(r.real.mean() > 0 and (r.opt.mean() - r.real.mean()) <= 0.5 * abs(r.opt.mean()))
    c["gecen"] = int(sum(v_ for k_, v_ in c.items() if k_.endswith("_gecti")))
    return c


def main() -> None:
    RES.mkdir(exist_ok=True)
    nd = V.ndx_frame()
    q = M.N.frame("QQQ")
    qo = V.ohlc("QQQ")
    b = broker_daily()
    bx = U_frame = M.U.frame(b.c)
    out = {"birincil": {}, "komsu": {}, "kart": {}}
    for nm, x in (("NDX", nd), ("QQQ", q), ("MT5_NAS100", bx)):
        ep = run_frame(x, 6, 5)
        out["birincil"][nm] = {"tum": M.placebo(x, ep, 5, 1), **era_tab(x, ep, 5)}
    for ns in (5, 6, 7):
        for h in (3, 5, 10):
            ep = run_frame(nd, ns, h)
            out["komsu"][f"NDX_seri{ns}_h{h}"] = {"tum": M.placebo(nd, ep, h, 1),
                                                  "2018_2026": M.placebo(nd, ep[ep.d >= "2018-01-01"], h, 1)}
    out["kart"]["NDX_1985"] = card(nd, None)
    out["kart"]["QQQ_1999"] = card(q, qo)
    (RES / "sn.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, v in out["birincil"].items():
        print("BIRINCIL", k, json.dumps(v, ensure_ascii=False))
    for k, v in out["komsu"].items():
        print("KOMSU", k, {kk: (vv.get("n"), vv.get("ort"), vv.get("fark"), vv.get("yuzdelik")) for kk, vv in v.items()})
    for k, v in out["kart"].items():
        print("KART", k, v)


if __name__ == "__main__":
    main()
