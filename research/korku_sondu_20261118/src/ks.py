"""ks.py — korku söndü: VIX zirveden hızlı iniş → H gün AL (PROTOCOL). python ks.py"""
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
RES = ROOT / "research/korku_sondu_20261118/results"
KS, LS, HS = (0.20, 0.30), (25, 30), (5, 10, 20)
COST = 2.0
ERAS = (("KESIF", "1999-03-01", "2011-12-31"), ("TEST", "2012-01-01", "2021-10-31"), ("YENI", "2021-11-01", "2026-12-31"))


def load(sym: str) -> pd.Series:
    d = pd.read_parquet(D / f"{sym}.parquet")
    s = d.Close.copy()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s


def frame(px: pd.Series) -> pd.DataFrame:
    v = load("VIX")
    df = pd.DataFrame({"p": px}).join(v.rename("v"), how="inner").dropna()
    df["vmax"] = df.v.rolling(10).max()
    return df


def rets(df: pd.DataFrame, h: int) -> np.ndarray:
    """d sinyal → d+1 kapanışı giriş → d+1+h kapanışı çıkış, net bp."""
    p = df.p.values
    idx = df.index
    out = np.full(len(df), np.nan)
    for i in range(len(df) - 1 - h):
        a, b = i + 1, i + 1 + h
        out[i] = (p[b] / p[a] - 1) * 1e4 - COST - lib.FIN_BP_PER_DAY * (idx[b] - idx[a]).days
    return out


def signals(df: pd.DataFrame, k: float, L: float) -> np.ndarray:
    raw = ((df.v <= (1 - k) * df.vmax) & (df.vmax >= L)).values
    out, last = np.zeros(len(df), bool), -999
    for i in np.flatnonzero(raw):
        if i - last > 20:
            out[i] = True
            last = i
    return out


def era_mask(df: pd.DataFrame, a: str, b: str) -> np.ndarray:
    return ((df.index >= pd.Timestamp(a)) & (df.index <= pd.Timestamp(b)))


def stat(r: np.ndarray, m: np.ndarray, sel: np.ndarray) -> dict:
    a = r[m & sel & np.isfinite(r)]
    b = r[sel & np.isfinite(r)]
    if len(a) < 2:
        return {"n": int(len(a))}
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "taban": round(float(b.mean()), 1), "fark": round(float(a.mean() - b.mean()), 1),
            "t": round(float((a.mean() - b.mean()) / (a.std(ddof=1) / np.sqrt(len(a)))), 2), "en_kotu": round(float(a.min()), 1),
            "isabet": round(float((a > 0).mean()), 3)}


def boot(a: np.ndarray, base: float, n: int = 10000) -> float:
    rng = np.random.default_rng(7)
    return float((rng.choice(a, (n, len(a))).mean(1) - base > 0).mean())


def main() -> None:
    RES.mkdir(exist_ok=True)
    Q, S = frame(load("QQQ")), frame(load("SPY"))
    cells = []
    for k in KS:
        for L in LS:
            mq, ms = signals(Q, k, L), signals(S, k, L)
            for h in HS:
                rq, rs_ = rets(Q, h), rets(S, h)
                rec = {"k": k, "L": L, "H": h}
                for nm, a, b in ERAS:
                    rec[nm] = stat(rq, mq, era_mask(Q, a, b))
                sel = era_mask(Q, "2012-01-01", "2026-12-31")
                a = rq[mq & sel & np.isfinite(rq)]
                rec["P_test_yeni"] = round(boot(a, np.nanmean(rq[sel])), 4) if len(a) > 2 else None
                rec["SPY"] = stat(rs_, ms, np.ones(len(S), bool))
                cells.append(rec)
    kes = [c for c in cells if c["KESIF"].get("n", 0) >= 8 and c["KESIF"].get("fark", -1) > 0]
    frozen = sorted(kes, key=lambda c: -c["KESIF"]["t"])[:2]
    for c in cells:
        c["donmus"] = c in frozen
        if c["donmus"]:
            ok1 = all(c[e].get("fark", -1) > 0 for e in ("TEST", "YENI"))
            ok2 = (c["P_test_yeni"] or 0) >= 0.975
            ok3 = c["SPY"].get("fark", -1) > 0
            c["hukum"] = "B" if ok1 and ok2 and ok3 else ("C+" if ok1 and ok3 else ("C" if ok1 or ok3 else "X"))
        print(("* " if c["donmus"] else "  ") + f"k{c['k']} L{c['L']} H{c['H']} | KEŞİF {c['KESIF']} | TEST {c['TEST']} | YENİ {c['YENI']} | P {c['P_test_yeni']} | SPY {c['SPY'].get('fark')} | {c.get('hukum', '')}")
    (RES / "korku_sondu.json").write_text(json.dumps(cells, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
