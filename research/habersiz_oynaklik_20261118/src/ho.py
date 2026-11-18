"""ho.py — habersiz / olay günü oynaklığı → ertesi gün (PROTOCOL). python ho.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/k1_ayi_cagi_20261118/src"))
import ka  # noqa: E402

RES = ROOT / "research/habersiz_oynaklik_20261118/results"


def boot(a: np.ndarray, b: np.ndarray) -> float:
    r = np.random.default_rng(8)
    return float((r.choice(a, (8000, len(a))).mean(1) - r.choice(b, (8000, len(b))).mean(1) > 0).mean())


def main() -> None:
    RES.mkdir(exist_ok=True)
    cal = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    ev = set(pd.to_datetime(cal.date).dt.normalize())
    out = {}
    for sym in ("QQQ", "SPY", "DIA", "IWM"):
        x = ka.daily(sym)
        rr = (x.h - x.l) / x.c
        x["vol"] = rr >= 1.5 * rr.shift(1).rolling(20).mean()
        x["up"] = x.c > x.o
        x["olay"] = x.index.isin(ev)
        rec = {}
        for nm, a, b in (("1999_2007", "1999-01-01", "2007-12-31"), ("2008_2017", "2008-01-01", "2017-12-31"), ("2018_2026", "2018-01-01", "2026-10-02")):
            z = x[(x.index >= a) & (x.index <= b)]
            r2 = {}
            for grp, gm in (("habersiz", ~z.olay), ("olay", z.olay), ("hepsi", np.ones(len(z), bool))):
                y = z[gm]
                for tag, ex in (("tum", np.zeros(len(y), bool)), ("V1_haric", y.V1.values)):
                    k = y[~ex]
                    m = k.vol.values
                    if m.sum() < 3:
                        continue
                    r2[f"{grp}_{tag}"] = {"n": int(m.sum()), "ort": round(float(k.nx[m].mean()), 1), "taban": round(float(k.nx.mean()), 1),
                                          "fark": round(float(k.nx[m].mean() - k.nx.mean()), 1),
                                          "yukari_gun": round(float(k.nx[m & k.up.values].mean()), 1), "asagi_gun": round(float(k.nx[m & ~k.up.values].mean()), 1)}
                    if tag == "V1_haric":
                        r2[f"{grp}_{tag}"]["P"] = round(boot(k.nx.values[m], k.nx.values), 4)
            rec[nm] = r2
        out[sym] = rec
        q = rec["2008_2017"]
        print(sym, "2008-17 habersiz V1 hariç", q.get("habersiz_V1_haric"), "| olay V1 hariç", q.get("olay_V1_haric"), flush=True)
    Q = out["QQQ"]["2008_2017"]
    h = Q["habersiz_V1_haric"]
    hk = sum(out[s]["2008_2017"]["habersiz_V1_haric"]["fark"] > 0 for s in ("SPY", "DIA", "IWM"))
    out["hukum_habersiz"] = "B" if h["fark"] > 0 and h["P"] >= 0.95 and hk >= 2 else ("C+" if h["fark"] > 0 and hk >= 2 else "X")
    o = Q["olay_V1_haric"]
    ok_ = sum(out[s]["2008_2017"]["olay_V1_haric"]["fark"] < 0 for s in ("SPY", "DIA", "IWM"))
    out["hukum_olay"] = "C+" if o["fark"] < 0 and ok_ >= 2 else "X"
    print("habersiz:", out["hukum_habersiz"], "| olay:", out["hukum_olay"])
    for s in out:
        if s in ("QQQ",):
            for nm in ("1999_2007", "2018_2026"):
                print(s, nm, {k: v for k, v in out[s][nm].items() if k in ("hepsi_V1_haric", "habersiz_V1_haric", "olay_V1_haric")})
    (RES / "habersiz_oynaklik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
