"""ox.py — EK-1 OX: OPEX haftası Çarşamba kapanış → OPEX Cuma kapanış SAT. python ox.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/nq_yapi3_20261118/src", "research/fitil_gece_20261118/src", "research/fitil_kesisim_20261118/src",
          "research/moc_pencere_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gunluk3 as M  # noqa: E402
import gece as G  # noqa: E402
import ksg_dogrulama as KD  # noqa: E402
import vs  # noqa: E402

V = M.V
HERE = Path(__file__).resolve().parents[1]
RES = HERE / "results"
NY = "America/New_York"


def close_series(name: str) -> pd.Series:
    if name == "NDX":
        return V.ndx_frame().c
    if name == "GSPC":
        d = pd.read_parquet(HERE / "data/GSPC_1950.parquet")
        d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
        return d.Close.astype(float)
    return V.ohlc(name).c


def opex_days(idx: pd.DatetimeIndex) -> set:
    td = set(idx)
    out = set()
    for y in range(idx[0].year, idx[-1].year + 1):
        for m in range(1, 13):
            f = pd.Timestamp(vs.third_friday(y, m))
            k = 0
            while f not in td and k < 4:
                f -= pd.Timedelta(days=1)
                k += 1
            if f in td:
                out.add(f)
    return out


def events(px: pd.Series, sp: pd.Series | None = None) -> pd.DataFrame:
    """Her hafta: hafta son işlem günü F, giriş F'den 2 işlem günü önce. OPEX haftası işaretli. SAT net bp."""
    idx = px.index
    ox = opex_days(idx)
    wk = pd.Series(idx, index=idx).groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).max()
    pos = {d: i for i, d in enumerate(idx)}
    rows = []
    for f in wk.values:
        f = pd.Timestamp(f)
        is_ox = f in ox
        if not is_ox and f.dayofweek != 4:
            continue
        i = pos[f]
        if i < 2:
            continue
        a, b = px.values[i - 2], px.values[i]
        cost = 2.0 if sp is None else (sp.values[i] / b * 1e4)
        rows.append({"d": f, "opex": is_ox, "ceyrek": is_ox and f.month in (3, 6, 9, 12), "sat": -(b / a - 1) * 1e4 - cost,
                     "sat15": -(b / a - 1) * 1e4 - 1.5 * cost})
    return pd.DataFrame(rows)


def stat(e: pd.DataFrame, a: str, b: str) -> dict:
    z = e[(e.d >= a) & (e.d <= b)]
    v, w = z[z.opex].sat.values, z[~z.opex].sat.values
    if len(v) < 10:
        return {"n": int(len(v))}
    se = np.sqrt(v.var(ddof=1) / len(v) + w.var(ddof=1) / len(w))
    return {"n": int(len(v)), "opex_SAT": round(float(v.mean()), 1), "taban_SAT": round(float(w.mean()), 1),
            "fark": round(float(v.mean() - w.mean()), 1), "t": round(float((v.mean() - w.mean()) / se), 2), "P": round(vs.boot(v, w), 4),
            "isabet": round(float((v > 0).mean()), 3), "s15": round(float(z[z.opex].sat15.mean()), 1),
            "yil_arti": f"{int((z[z.opex].groupby(z[z.opex].d.dt.year).sat.mean() > 0).sum())}/{z[z.opex].d.dt.year.nunique()}"}


def intraday(b: pd.DataFrame, step: int) -> pd.DataFrame:
    dp = G.day_prices(b, NY, [960], step)
    dp = dp[np.isfinite(dp.o960)]
    s = pd.Series(dp.o960.values, index=pd.to_datetime(dp.index))
    sp = pd.Series(dp.s960.values, index=s.index)
    s = s[s.index.dayofweek < 5]
    return events(s, sp.reindex(s.index))


def main() -> None:
    RES.mkdir(exist_ok=True)
    out = {}
    nd, gs, q, spy = (events(close_series(n)) for n in ("NDX", "GSPC", "QQQ", "SPY"))
    out["a_NDX_1985_1999"] = stat(nd, "1985-10-01", "1999-02-28")
    out["b_GSPC_1983_1998"] = stat(gs, "1983-04-01", "1998-12-31")
    out["c_PLASEBO_GSPC_1950_1983"] = stat(gs, "1950-01-01", "1983-03-31")
    out["QQQ_1999_2026"] = stat(q, "1999-03-01", "2026-12-31")
    out["QQQ_SON5"] = stat(q, "2021-11-01", "2026-12-31")
    out["SPY_1993_2026"] = stat(spy, "1993-01-01", "2026-12-31")
    for nm, ev in (("NDX", nd), ("GSPC", gs)):
        for a, b in (("1985-01-01", "1999-12-31"), ("2000-01-01", "2009-12-31"), ("2010-01-01", "2017-12-31"), ("2018-01-01", "2026-12-31")):
            out[f"{nm}_{a[:4]}_{b[:4]}"] = stat(ev, a, b)
    q2 = q.copy()
    q2["opex"] = q2.ceyrek
    out["e_QQQ_ceyrek_OPEX"] = stat(q2[q2.opex | ~q.opex], "1999-03-01", "2026-12-31")
    import moc  # noqa: E402
    feeds = {"DUKA_NDX": (G.ndx_bars(), 60), "MT5_US500": (KD.mt5_m30("US500", "2018-06-01"), 1800),
             "MT5_US30": (KD.mt5_m30("US30"), 1800), "MT5_US2000": (KD.mt5_m30("US2000"), 1800)}
    pool = []
    for nm, (b, st) in feeds.items():
        ev = intraday(b, st)
        out[f"d_{nm}"] = stat(ev, "2016-01-01", "2026-12-31")
        pool.append(ev)
    h1 = pd.read_csv(ROOT / "research/c1_turev_20261105/data/mt5/NAS100_H1.csv.gz")
    import kaynak  # noqa: E402
    t = kaynak.server_to_utc(h1["t"].to_numpy())
    hb = pd.DataFrame({"t": t.astype(np.int64), "o": h1.o, "h": h1.h, "l": h1.l, "c": h1.c, "sp": np.where(h1.sp > 0, h1.sp * 0.1, 1.5)})
    hb = hb[hb.t >= int(pd.Timestamp("2016-01-01", tz=NY).timestamp())].reset_index(drop=True)
    ev = intraday(hb, 3600)
    out["d_MT5_NAS100_H1_2016_2018"] = stat(ev, "2016-01-01", "2018-04-30")
    pool.append(ev[ev.d <= "2018-04-30"])
    pz = pd.concat(pool, ignore_index=True)
    out["d_havuz_gunici"] = stat(pz, "2016-01-01", "2026-12-31")
    (RES / "ox.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for k, v in out.items():
        print(k, v)


if __name__ == "__main__":
    main()
