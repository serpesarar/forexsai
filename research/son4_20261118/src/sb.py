"""sb.py — SB sabah trendine 13:00'te katıl → 16:00 (haber ayrımı + kör beslemeler). python sb.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/fitil_gece_20261118/src", "research/fitil_kesisim_20261118/src", "research/ndx_tf_yapilandirma_20261117/src"):
    sys.path.insert(0, str(ROOT / p))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gece as G  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import ksg_ek2 as E  # noqa: E402
import hp  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
NY = "America/New_York"
CAL_END = pd.Timestamp("2026-10-02")


def events_set() -> set:
    c = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    return set(pd.to_datetime(c.date).dt.normalize())


def trades(b: pd.DataFrame, step: int, start_min: int, k: float = 1.0, delay: int = 0) -> pd.DataFrame:
    ent_m = 780 + delay
    mins = sorted({start_min, 780, ent_m, 960})
    dp = G.day_prices(b, NY, mins, step)
    ok = np.all([np.isfinite(dp[f"o{m}"]) for m in mins], axis=0)
    dp = dp[ok]
    dp = dp[[pd.Timestamp(d).dayofweek < 5 and G.nyse_ok(d) for d in dp.index]]
    R = dp.o780 / dp[f"o{start_min}"] - 1
    sig = R.shift(1).rolling(20, min_periods=15).std()
    side = np.sign(R).values
    m = (R.abs() >= k * sig).values
    pe, se, px, sx = dp[f"o{ent_m}"].values, dp[f"s{ent_m}"].values, dp.o960.values, dp.s960.values
    pin = np.where(side > 0, pe + se, pe)
    pout = np.where(side > 0, px, px + sx)
    net = side * (pout / pin - 1) * 1e4
    n15 = net - 0.5 * (se + sx) / pe * 1e4
    ev = events_set()
    d = pd.to_datetime(dp.index)
    t = pd.DataFrame({"d": d, "net": net, "n15": n15, "tetik": m, "olay": d.isin(ev), "takvim_ok": d <= CAL_END})
    return t


def boot(v: np.ndarray, w: np.ndarray | None = None) -> float:
    r = np.random.default_rng(23)
    a = r.choice(v, (4000, len(v))).mean(1)
    return float((a > 0).mean()) if w is None else float((a - r.choice(w, (4000, len(w))).mean(1) > 0).mean())


def summ(t: pd.DataFrame, a: str, b: str) -> dict:
    z = t[(t.d >= a) & (t.d <= b)]
    tr = z[z.tetik]
    if len(tr) < 10:
        return {"n": int(len(tr))}
    rec = {"n": int(len(tr)), "ort": round(float(tr.net.mean()), 2), "s15": round(float(tr.n15.mean()), 2), "isabet": round(float((tr.net > 0).mean()), 3),
           "P": round(boot(tr.net.values), 4)}
    zz = tr[tr.takvim_ok]
    for nm, mm in (("olay", zz.olay), ("olaysiz", ~zz.olay)):
        v = zz[mm].net.values
        rec[nm] = {"n": int(len(v)), "ort": round(float(v.mean()), 2) if len(v) else None}
    return rec


def card(t: pd.DataFrame, t_delay: pd.DataFrame) -> dict:
    tr = t[t.tetik]
    v = tr.net.values
    h = len(v) // 2
    yrs = tr.groupby(tr.d.dt.year).net.mean()
    dl = t_delay[t_delay.tetik].net.values
    c = {"1_n": int(len(v)), "1_gecti": bool(len(v) >= 150), "2_ort": round(float(v.mean()), 2), "2_P": round(boot(v), 4),
         "2_gecti": bool(v.mean() > 0 and boot(v) >= 0.90), "3_yarilar": [round(float(v[:h].mean()), 2), round(float(v[h:].mean()), 2)],
         "3_gecti": bool(v[:h].mean() >= 0 and v[h:].mean() >= 0), "4_s15": round(float(tr.n15.mean()), 2), "4_gecti": bool(tr.n15.mean() > 0),
         "5_bir_dk_gec": round(float(dl.mean()), 2), "5_gecti": bool(dl.mean() > 0 and (v.mean() - dl.mean()) <= 0.5 * v.mean()),
         "6_tek_pozisyon": True, "6_gecti": True, "yil_arti": f"{int((yrs > 0).sum())}/{len(yrs)}"}
    c["gecen"] = int(sum(c[k] for k in c if k.endswith("_gecti")))
    return c


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {}
    duka = G.ndx_bars()
    td = trades(duka, 60, 570)
    out["DUKA_ESKI"] = summ(td, "2018-04-01", "2021-10-31")
    out["DUKA_KESIF"] = summ(td, "2021-11-01", "2024-06-30")
    out["DUKA_TEST"] = summ(td, "2024-07-01", "2026-12-31")
    out["DUKA_k1.5"] = summ(trades(duka, 60, 570, 1.5), "2018-04-01", "2026-12-31")
    out["kart_DUKA"] = card(td, trades(duka, 60, 570, 1.0, delay=1))
    blind = {"MT5_NAS100_H1_2016_2018": (hp.h1_bars(), 3600, 600, "2016-01-01", "2018-04-30"),
             "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800, 570, "2018-06-01", "2026-12-31"),
             "MT5_US30": (KD.mt5_m30("US30"), 1800, 570, "2018-07-01", "2026-12-31"),
             "MT5_US2000": (KD.mt5_m30("US2000"), 1800, 570, "2018-05-01", "2026-12-31")}
    for nm in ("NQ", "EET30"):
        b, st = E.bars(nm)
        blind[f"{nm}_NDX"] = (b, st, 570, "2016-01-01", "2026-12-31")
    pool = []
    for nm, (b, st, sm, a, z) in blind.items():
        t = trades(b, st, sm)
        out[nm] = summ(t, a, z)
        if nm.startswith(("MT5_US", "MT5_NAS100_H1")):
            pool.append(t[(t.d >= a) & (t.d <= z)])
        print(nm, out[nm], flush=True)
    pz = pd.concat(pool, ignore_index=True)
    out["kor_havuz_farkli_piyasa"] = summ(pz, "2016-01-01", "2026-12-31")
    (RES / "sb.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main()
