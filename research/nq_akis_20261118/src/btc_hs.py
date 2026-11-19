"""btc_hs.py — NA-04 BTC hafta sonu öncülüğü → NDX Pazar açılışı / Pazartesi. python btc_hs.py"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/btc_korku_20261118/src"))
sys.path.insert(0, str(ROOT / "research/moc_pencere_20261118/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bk  # noqa: E402
import ihale as I  # noqa: E402

G, U = I.G, I.U
NY = "America/New_York"


def u(d, hh: int, mm: int) -> int:
    return int(pd.Timestamp(datetime(d.year, d.month, d.day, hh, mm), tz=NY).timestamp())


def at_open(b: pd.DataFrame, ts: int, tol: int) -> tuple[float, float]:
    i = int(np.searchsorted(b.t.values, ts))
    if i < len(b) and b.t.values[i] - ts <= tol:
        return float(b.o.values[i]), float(b.sp.values[i])
    return np.nan, np.nan


def at_close_before(b: pd.DataFrame, ts: int, step: int, tol: int) -> float:
    i = int(np.searchsorted(b.t.values, ts - step + 1)) - 1
    if 0 <= i < len(b) and ts - (b.t.values[i] + step) <= tol:
        return float(b.c.values[i])
    return np.nan


def table(nb: pd.DataFrame, step: int, btc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    d0, d1 = pd.Timestamp("2018-04-01").date(), pd.Timestamp("2026-11-14").date()
    d = d0 + timedelta(days=(4 - d0.weekday()) % 7)
    tol = 600 if step == 60 else 3 * step
    while d <= d1:
        sun, mon = d + timedelta(days=2), d + timedelta(days=3)
        if G.nyse_ok(d) and G.nyse_ok(mon):
            tf, ts = u(d, 16, 0), u(sun, 18, 0)
            pf = at_close_before(nb, tf, step, 900)
            ps, _ = at_open(nb, ts, 1800)
            pe, se = at_open(nb, u(sun, 18, 5), 1800)
            x930, s930 = at_open(nb, u(mon, 9, 30), tol)
            x16, s16 = at_open(nb, u(mon, 16, 0), tol)
            bf, _ = at_open(btc, tf, 600)
            bs, _ = at_open(btc, ts, 600)
            rows.append({"d": d, "pf": pf, "ps": ps, "pe": pe, "se": se, "x930": x930, "s930": s930, "x16": x16, "s16": s16, "bf": bf, "bs": bs})
        d += timedelta(days=7)
    x = pd.DataFrame(rows).dropna(subset=["pf", "ps", "pe", "bf", "bs"]).reset_index(drop=True)
    x["bw"] = x.bs / x.bf - 1
    x["g"] = x.ps / x.pf - 1
    x["sig"] = x.bw.shift(1).rolling(26, min_periods=20).std()
    beta, sres = [], []
    for k in range(len(x)):
        w = x.iloc[max(0, k - 52):k]
        if len(w) >= 30:
            bt = np.polyfit(w.bw, w.g, 1)[0]
            beta.append(bt)
            sres.append(float(np.std(w.g - bt * w.bw)))
        else:
            beta.append(np.nan)
            sres.append(np.nan)
    x["beta"], x["sres"] = beta, sres
    x["res"] = x.g - x.beta * x.bw
    x["era"] = [I.era_of(z) for z in x.d]
    return x


def nets(x: pd.DataFrame, side: np.ndarray, ex: str) -> tuple[np.ndarray, np.ndarray]:
    px, sx = x[f"x{ex}"].values, x[f"s{ex}"].values
    pin = np.where(side > 0, x.pe + x.se, x.pe)
    pout = np.where(side > 0, px, px + sx)
    fin = np.where(side > 0, U.lib.FIN_BP_PER_DAY * (1 if ex == "930" else 1.0), 0)
    net = side * (pout / pin - 1) * 1e4 - fin
    return net, net - 0.5 * (x.se + sx) / x.pe * 1e4


def summ(net: np.ndarray, n15: np.ndarray, d: np.ndarray) -> dict:
    ok = np.isfinite(net)
    net, n15, d = net[ok], n15[ok], d[ok]
    if len(net) < 5:
        return {"n": int(len(net))}
    rng = np.random.default_rng(3)
    bs = rng.choice(net, (4000, len(net))).mean(1)
    return {"n": int(len(net)), "ort": round(float(net.mean()), 1), "s15": round(float(n15.mean()), 1), "isabet": round(float((net > 0).mean()), 3),
            "P": round(float((bs > 0).mean()), 4), "en_kotu": round(float(net.min()), 1)}


def run(x: pd.DataFrame) -> dict:
    out = {"BH0": {}}
    for e in ("ESKI", "KESIF", "TEST"):
        z = x[x.era == e]
        out["BH0"][e] = {"n": int(len(z)), "beta": round(float(np.polyfit(z.bw, z.g, 1)[0]), 3), "kor": round(float(np.corrcoef(z.bw, z.g)[0, 1]), 3),
                         "kor_bw_pzt": round(float(np.corrcoef(z.bw[np.isfinite(z.x16)], (z.x16 / z.pe - 1)[np.isfinite(z.x16)])[0, 1]), 3)}
    for k in (1.0, 1.5):
        for ex in ("930", "16"):
            m1 = (x.bw.abs() >= k * x.sig).values
            s1 = np.sign(x.bw.values)
            m2 = (x.res.abs() >= k * x.sres).values
            s2 = -np.sign(x.res.values)
            for nm, m, s in ((f"BH1_k{k}_{ex}", m1, s1), (f"BH2_k{k}_{ex}", m2, s2)):
                net, n15 = nets(x, s, ex)
                out[nm] = {e: summ(net[m & (x.era == e).values], n15[m & (x.era == e).values], x.d.values[m & (x.era == e).values]) for e in ("ESKI", "KESIF", "TEST")}
    return out


def main() -> None:
    import moc  # noqa: E402
    btc = bk.btc()
    res = {}
    for src, (nb, st) in {"duka": (G.ndx_bars(), 60), "mt5": moc.mt5_2m()}.items():
        x = table(nb, st, btc)
        x.to_parquet(U.RES / f"btc_hs_{src}.parquet")
        res[src] = run(x)
    (U.RES / "btc_hs.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for src, r in res.items():
        for k, v in r.items():
            print(src, k, v)


if __name__ == "__main__":
    main()
