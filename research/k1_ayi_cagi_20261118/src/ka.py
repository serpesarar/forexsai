"""ka.py — K1 günlük vekili (V1) ile ayı çağı sınaması (PROTOCOL). python ka.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
for p in ("research/ndx_10y_1m_20261116/src", "research/korku_genislik_20261118/src"):
    sys.path.insert(0, str(ROOT / p))
import lib  # noqa: E402
import gn  # noqa: E402

D = ROOT / "research/qs03_akis_takvim_20261111/data"
RES = ROOT / "research/k1_ayi_cagi_20261118/results"
SUB = (("93-98", "1993-01-01", "1998-12-31"), ("99-02", "1999-01-01", "2002-12-31"), ("03-07", "2003-01-01", "2007-12-31"),
       ("08-09", "2008-01-01", "2009-12-31"), ("10-17", "2010-01-01", "2017-12-31"), ("18-26", "2018-04-01", "2026-12-31"))


def daily(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(D / f"{sym}.parquet")
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    x = pd.DataFrame({"o": d.Open, "h": d.High, "l": d.Low, "c": d.Close})
    x["V1"] = (x.c <= (x.h + x.l) / 2 * 0.995) & (x.c < x.o)
    x["nx"] = (x.c.shift(-1) / x.c - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (x.index.to_series().shift(-1) - x.index.to_series()).dt.days.values
    return x.dropna()


def st(x: pd.DataFrame) -> dict:
    a, b = x.nx[x.V1], x.nx[~x.V1]
    if len(a) < 3:
        return {"n": int(len(a))}
    cs = a.cumsum()
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "taban": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1),
            "en_kotu": round(float(a.min()), 1), "maxDD_bp": round(float((cs - cs.cummax()).min()), 1)}


def main() -> None:
    RES.mkdir(exist_ok=True)
    q = daily("QQQ")
    n = gn.nts(gn.G.ndx_bars(), 60)
    k1 = set(pd.to_datetime(pd.Series(n.d[n.K1])).dt.normalize())
    qq = q[q.index >= pd.Timestamp("2018-04-01")]
    ov = float(np.mean([d in set(qq.index[qq.V1]) for d in k1 if d in qq.index]))
    v = st(qq)
    gecerli = bool(v["fark"] > 20 and ov >= 0.5)
    out = {"dogrulama": {"QQQ_2018_26": v, "K1_V1_ortusme": round(ov, 3), "gecerli": gecerli}}
    print(out["dogrulama"], flush=True)
    if gecerli:
        for sym in ("QQQ", "SPY", "DIA", "IWM"):
            x = daily(sym)
            out[sym] = {nm: st(x[(x.index >= a) & (x.index <= b)]) for nm, a, b in SUB}
            print(sym, json.dumps(out[sym], ensure_ascii=False), flush=True)
        Q = out["QQQ"]
        bear = [Q[k].get("fark", -1) > 0 for k in ("99-02", "08-09")]
        out["hukum"] = "sağlam (ayı çağında da)" if all(bear) else ("çağa bağlı risk" if any(bear) else "boğa çağına bağlı")
    else:
        out["hukum"] = "vekil geçersiz — ölçülemedi"
    print(out["hukum"])
    (RES / "k1_ayi.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))




def ek1() -> None:
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.normalize())
    out = {}
    for sym in ("QQQ", "SPY", "DIA", "IWM"):
        x = daily(sym)
        x = x[x.index <= pd.Timestamp("2017-12-31")]
        prev_v = x.V1.shift(1).fillna(False).astype(bool)
        prev_r = (x.c.shift(1) / x.o.shift(1) - 1) <= -0.01
        ard = x.V1 & (prev_v | prev_r)
        a, z = x.nx[ard], x.nx[x.V1 & ~ard]
        rec = {"ardisik": {"n": int(len(a)), "ort": round(float(a.mean()), 1), "en_kotu": round(float(a.min()), 1)},
               "degil": {"n": int(len(z)), "ort": round(float(z.mean()), 1), "en_kotu": round(float(z.min()), 1)}}
        y = x[x.index >= pd.Timestamp("2008-01-01")]
        ol = y.index.isin(ev)
        g = {}
        for nm, m in (("olay", ol), ("habersiz", ~ol)):
            q = y[m]
            g[nm] = {"n": int(q.V1.sum()), "V1": round(float(q.nx[q.V1].mean()), 1), "taban": round(float(q.nx[~q.V1].mean()), 1)}
            g[nm]["fark"] = round(g[nm]["V1"] - g[nm]["taban"], 1)
        g["DD"] = round(g["habersiz"]["fark"] - g["olay"]["fark"], 1)
        rec["olay_2008_17"] = g
        out[sym] = rec
        print(sym, json.dumps(rec, ensure_ascii=False), flush=True)
    q = out["QQQ"]
    a1 = q["ardisik"]["ort"] > q["degil"]["ort"]
    a2 = sum(out[s]["ardisik"]["ort"] > out[s]["degil"]["ort"] for s in ("SPY", "DIA", "IWM"))
    out["GN05"] = "B'ye yükselir" if a1 and a2 >= 2 else ("X'e düşer" if not a1 and a2 <= 1 else "C+ kalır")
    o1 = q["olay_2008_17"]["DD"] > 0
    o2 = sum(out[s]["olay_2008_17"]["DD"] > 0 for s in ("SPY", "DIA", "IWM"))
    out["ZA04"] = "B'ye yükselir" if o1 and o2 >= 2 else ("X'e düşer" if not o1 and o2 <= 1 else "C+ kalır")
    print("GN-05:", out["GN05"], "| ZA-04:", out["ZA04"])
    (RES / "ek1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"ana": main, "ek1": ek1}[sys.argv[1] if len(sys.argv) > 1 else "ana"]()
