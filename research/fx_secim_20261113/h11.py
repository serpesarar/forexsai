"""FX-01 EK-8 H11: taşıma × VIX rejimi. Çalıştır: ../../.venv/bin/python -I h11.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
from ek6 import comm  # noqa: E402
from h10 import prep  # noqa: E402

MAIN = {"AUDJPY": 1, "NZDJPY": 1, "CADJPY": 1}
BLIND = {"AUDUSD": 1, "NZDUSD": 1, "USDJPY": 1, "GBPJPY": 1, "EURJPY": 1, "USDMXN": -1, "USDZAR": -1}
TH = 18.4
P1, P2 = pd.Timestamp("2010-01-01"), pd.Timestamp("2022-01-01")
BLOCK = 21


def vix() -> pd.Series:
    p = f.DATA / "vix_1990.csv"
    if not p.exists():
        import yfinance as yf
        z = yf.Ticker("^VIX").history(start="1990-01-01", end="2026-11-13", auto_adjust=False)
        pd.Series(z["Close"].values, index=pd.to_datetime(z.index.date), name="vix").to_csv(p)
    s = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0]
    return s[s.index < "2026-11-13"]


def daily(pair: str, side: int, v: pd.Series, mirror: bool = False) -> pd.DataFrame:
    d = prep(pair)
    d["day"] = d.srv.dt.normalize()
    d = d.set_index("day")
    d["r"] = side * np.log(d.c / d.c.shift()) * 1e4
    vv = v.reindex(d.index, method="ffill")
    # t+1 getirisi için t−1 VIX'i → bugünkü satırın getirisi (t−1 → t) için t−2 VIX'i
    lag = vv.shift(2)
    on = (lag < TH) if not mirror else (lag >= TH)
    d["on"] = on.astype(float).where(lag.notna())
    sw = on.astype(int).diff().abs().fillna(0)
    d["cost"] = sw * (d.yr_sp + comm(pair) / 2)       # her geçişte yarım RT (giriş veya çıkış)
    d["strat"] = d.on * d.r - d.cost
    return d.dropna(subset=["r", "on"])[["r", "on", "strat", "cost"]]


def per(t: pd.Timestamp) -> str:
    return "P1" if t < P1 else ("P2" if t < P2 else "P3")


def block_p(x: np.ndarray, rng: np.random.Generator, n: int = 3000) -> float:
    k = len(x) // BLOCK
    if k < 5:
        return float("nan")
    xb = x[: k * BLOCK].reshape(k, BLOCK).mean(1)
    m = np.array([rng.choice(xb, k).mean() for _ in range(n)])
    return float((m > 0).mean())


def pool_stats(pairs: dict, v: pd.Series, mirror: bool = False) -> dict:
    rng = np.random.default_rng(13)
    frames = {p: daily(p, s, v, mirror) for p, s in pairs.items()}
    r = pd.concat({p: x.r for p, x in frames.items()}, axis=1)
    on = pd.concat({p: x.on for p, x in frames.items()}, axis=1)
    st = pd.concat({p: x.strat for p, x in frames.items()}, axis=1)
    pool_r, pool_s = r.mean(1), st.mean(1)
    on_any = on.mean(1)
    out = {"ciftler": list(pairs), "gun": int(len(pool_r)), "iceride_pay": round(float(on_any.mean()), 3)}
    for name, idx in [("TUM", slice(None))] + [(k, pool_r.index.map(per) == k) for k in ("P1", "P2", "P3")]:
        rr, ss, oo = pool_r[idx], pool_s[idx], on_any[idx]
        inside, outside = rr[oo > 0.5], rr[oo <= 0.5]
        diff = inside.mean() - outside.mean()
        z = (rr * (oo > 0.5) - rr * (oo <= 0.5) * (len(inside) / max(1, len(outside)))).values
        sh = lambda x: float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else float("nan")  # noqa: E731
        out[name] = {"gun": int(len(rr)), "iceride_ort_bp": round(float(inside.mean()), 2), "disarida_ort_bp": round(float(outside.mean()), 2),
                     "fark_bp": round(float(diff), 2), "P_fark_blok": round(block_p(z, rng), 3),
                     "strateji_yillik_%": round(float(ss.mean() * 252 / 100), 2), "al_tut_yillik_%": round(float(rr.mean() * 252 / 100), 2),
                     "Sharpe_strateji": round(sh(ss), 2), "Sharpe_al_tut": round(sh(rr), 2),
                     "maxDD_strateji_%": round(float(((ss.cumsum() - ss.cumsum().cummax()).min()) / 100), 1),
                     "maxDD_al_tut_%": round(float(((rr.cumsum() - rr.cumsum().cummax()).min()) / 100), 1)}
    out["cift"] = {p: {"iceride": round(float(x.r[x.on > 0.5].mean()), 2), "disarida": round(float(x.r[x.on <= 0.5].mean()), 2),
                       "P3_fark": round(float(x.r[(x.on > 0.5) & (x.index >= P2)].mean() - x.r[(x.on <= 0.5) & (x.index >= P2)].mean()), 2)}
                   for p, x in frames.items()}
    return out


def main() -> dict:
    v = vix()
    res = {"ana": pool_stats(MAIN, v), "kor": pool_stats(BLIND, v), "ana_ayna": pool_stats(MAIN, v, mirror=True)}
    (f.RES / "h11.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    return res


if __name__ == "__main__":
    main()
