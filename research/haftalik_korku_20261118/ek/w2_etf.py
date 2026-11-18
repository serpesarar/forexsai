"""W2 haftalık korku — bağımsız eski dönem ETF sınaması (EK-1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/ndx_10y_1m_20261116/src"))
import lib  # noqa: E402

D = ROOT / "research/qs03_akis_takvim_20261111/data"
END = pd.Timestamp("2017-12-31")


def weeks(sym: str) -> pd.DataFrame:
    d = pd.read_parquet(D / f"{sym}.parquet")
    c = d.Close.copy()
    c.index = pd.to_datetime(c.index).tz_localize(None).normalize()
    c = c[c.index <= END + pd.Timedelta(days=10)]
    iso = c.index.isocalendar()
    wk = iso.year.astype(str) + "-" + iso.week.astype(str)
    last = c.groupby(wk.values).apply(lambda s: s.index.max())
    w = pd.DataFrame({"d": sorted(last.values)})
    w["p"] = c.reindex(w.d).values
    w["ret"] = w.p.pct_change()
    w["nx"] = (w.p.shift(-1) / w.p - 1) * 1e4 - 2 - lib.FIN_BP_PER_DAY * (w.d.shift(-1) - w.d).dt.days
    return w[(w.d <= END)].dropna()


def boot(a: np.ndarray, b: np.ndarray, n: int = 10000) -> float:
    r = np.random.default_rng(9)
    return float((r.choice(a, (n, len(a))).mean(1) - r.choice(b, (n, len(b))).mean(1) > 0).mean())


def main() -> None:
    out = {}
    for sym in ("QQQ", "SPY", "DIA", "IWM"):
        w = weeks(sym)
        m = (w.ret <= -0.03).values
        a, b = w.nx[m], w.nx[~m]
        rec = {"aralik": [str(w.d.min().date()), str(w.d.max().date())], "n": int(m.sum()), "ort": round(float(a.mean()), 1),
               "taban": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1), "P": round(boot(a.values, b.values), 4),
               "en_kotu": round(float(a.min()), 1), "isabet": round(float((a > 0).mean()), 3)}
        sub = {}
        for nm, s, e in (("99-02", "1999-01-01", "2002-12-31"), ("03-07", "2003-01-01", "2007-12-31"), ("08-09", "2008-01-01", "2009-12-31"),
                         ("10-17", "2010-01-01", "2017-12-31"), ("93-98", "1993-01-01", "1998-12-31")):
            z = w[(w.d >= s) & (w.d <= e)]
            mm = (z.ret <= -0.03).values
            if mm.sum():
                sub[nm] = [int(mm.sum()), round(float(z.nx[mm].mean()), 1), round(float(z.nx[~mm].mean()), 1)]
        rec["alt"] = sub
        out[sym] = rec
        print(sym, json.dumps(rec, ensure_ascii=False))
    q = out["QQQ"]
    ok = q["fark"] > 0 and q["ort"] > 0 and q["P"] >= 0.95 and sum(out[s]["fark"] > 0 for s in ("SPY", "DIA", "IWM")) >= 2
    out["hukum"] = "B'ye yükselir" if ok else ("C+ kalır" if q["fark"] > 0 else "X")
    print(out["hukum"])
    (ROOT / "research/haftalik_korku_20261118/results/ek1_etf.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
