"""FX-01 EK-7 H10: günlük Donchian55/EMA200 trend takibi, 2×ATR stop, Donchian20 çıkış. Çalıştır: ../../.venv/bin/python -I h10.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fx_core as f  # noqa: E402
from ek6 import comm  # noqa: E402

MAIN = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"]
BLIND = ["EURJPY", "GBPJPY", "AUDJPY", "CADJPY", "NZDJPY", "EURGBP", "EURCHF", "EURAUD", "GBPAUD", "AUDCAD", "EURCAD", "GBPCHF",
         "AUDNZD", "USDMXN", "USDZAR", "USDNOK", "USDSEK"]
N_IN, N_OUT, N_EMA, N_ATR, K_STOP = 55, 20, 200, 20, 2.0
N_PLACEBO = 500
P1, P2 = pd.Timestamp("2010-01-01"), pd.Timestamp("2022-01-01")
MIRROR = False


def prep(pair: str) -> pd.DataFrame:
    d = f.load(pair, "D1")
    d = d[d.srv.dt.dayofweek < 5].reset_index(drop=True)
    pt = f.meta()[pair]["point"]
    d["sp_bp"] = d.sp.where(d.sp > 0) * pt / d.c * 1e4
    d["sp_bp"] = d.sp_bp.fillna(d.groupby(d.srv.dt.year).sp_bp.transform("median")).fillna(d.sp_bp.median()).fillna(1.0)
    pc = d.c.shift()
    tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(N_ATR).mean()
    d["ema"] = d.c.ewm(span=N_EMA, adjust=False).mean()
    d["hi_in"], d["lo_in"] = d.h.rolling(N_IN).max().shift(), d.l.rolling(N_IN).min().shift()
    d["hi_out"], d["lo_out"] = d.h.rolling(N_OUT).max().shift(), d.l.rolling(N_OUT).min().shift()
    d["yr_sp"] = d.groupby(d.srv.dt.year).sp_bp.transform("median")
    return d


def swap_bp_night(pair: str, side: int, px: float) -> float:
    m = f.meta()[pair]
    pts = m["swap_long"] if side > 0 else m["swap_short"]
    return -pts * m["point"] / px * 1e4            # pozitif = maliyet


def simulate(pair: str, d: pd.DataFrame) -> list[dict]:
    o, h, l, c = d.o.values, d.h.values, d.l.values, d.c.values
    trades, i, n = [], N_EMA, len(d)
    while i < n - 2:
        side = 0
        if c[i] > d.hi_in.iat[i] and c[i] > d.ema.iat[i]:
            side = 1
        elif c[i] < d.lo_in.iat[i] and c[i] < d.ema.iat[i]:
            side = -1
        if MIRROR:
            side = -side
        if side == 0 or not np.isfinite(d.atr.iat[i]):
            i += 1
            continue
        e_i = i + 1
        entry = o[e_i]
        stop = entry - side * K_STOP * d.atr.iat[i]
        x_i, xp, why = None, None, None
        for j in range(e_i, n):
            if (side > 0 and l[j] <= stop) or (side < 0 and h[j] >= stop):
                xp = min(o[j], stop) if side > 0 else max(o[j], stop)
                x_i, why = j, "stop"
                break
            exit_sig = (c[j] < d.lo_out.iat[j]) if side > 0 else (c[j] > d.hi_out.iat[j])
            if (not MIRROR) and exit_sig and j + 1 < n:
                x_i, xp, why = j + 1, o[j + 1], "donchian"
                break
            if MIRROR and j + 1 < n and j - e_i >= 20:
                x_i, xp, why = j + 1, o[j + 1], "zaman"
                break
        if x_i is None:
            break
        nights_days = d.srv.iloc[e_i:x_i]
        nights = int(len(nights_days)) + int((nights_days.dt.dayofweek == 2).sum() * 2)
        gross = side * np.log(xp / entry) * 1e4
        cost = 2 * d.yr_sp.iat[e_i] + comm(pair) + swap_bp_night(pair, side, entry) * nights
        r_bp = K_STOP * d.atr.iat[i] / entry * 1e4
        trades.append({"pair": pair, "t": d.utc.iat[e_i], "side": side, "gross": gross, "net": gross - cost, "R": (gross - cost) / r_bp,
                       "gun": x_i - e_i, "why": why, "cost": cost, "e_i": e_i})
        i = x_i
    return trades


def placebo(d: pd.DataFrame, trades: list[dict], pair: str, rng: np.random.Generator) -> np.ndarray:
    o = d.o.values
    n = len(o)
    hold = np.array([max(1, t["gun"]) for t in trades])
    sides = np.array([t["side"] for t in trades])
    costs = np.array([t["cost"] for t in trades])
    rbp = np.array([t["gross"] / t["R"] if t["R"] else np.nan for t in trades])  # yaklaşık
    _ = rbp
    out = []
    lo = N_EMA + 1
    for _ in range(N_PLACEBO):
        idx = rng.integers(lo, n - hold.max() - 2, len(hold))
        sgn = rng.permutation(sides)
        g = sgn * np.log(o[idx + hold] / o[idx]) * 1e4
        out.append(float(np.mean(g - costs)))
    return np.array(out)


def period(t: pd.Timestamp) -> str:
    return "D1" if t < P1 else ("D2" if t < P2 else "D3")


def block(trs: list[dict], pl: np.ndarray | None = None) -> dict:
    x = pd.DataFrame(trs)
    if x.empty:
        return {"n": 0}
    x["per"] = x.t.map(period)
    top = x.net.abs().nlargest(5).index
    out = {"n": int(len(x)), "ort_R": round(x.R.mean(), 3), "ort_net_bp": round(x.net.mean(), 1), "medyan_R": round(x.R.median(), 3),
           "isabet": round((x.net > 0).mean(), 3), "P_R": round(f.boot_p(x.R.values), 3), "ort_gun": round(x.gun.mean(), 1),
           "donem_R": {k: [int(len(g)), round(g.R.mean(), 3)] for k, g in x.groupby("per")},
           "ilk5_haric_R": round(x.drop(top).R.mean(), 3), "ort_maliyet_bp": round(x.cost.mean(), 1),
           "uzun_R": round(x[x.side > 0].R.mean(), 3), "kisa_R": round(x[x.side < 0].R.mean(), 3)}
    if pl is not None:
        out["plasebo_net_bp"] = round(float(np.mean(pl)), 1)
        out["plasebo_yuzdelik"] = round(float((pl < x.net.mean()).mean()), 3)
    return out


def main() -> dict:
    rng = np.random.default_rng(31)
    res: dict = {"cift": {}}
    pools = {"ana": [], "kor": []}
    plp = {"ana": [], "kor": []}
    for grp, pairs in (("ana", MAIN), ("kor", BLIND)):
        for p in pairs:
            d = prep(p)
            tr = simulate(p, d)
            pl = placebo(d, tr, p, rng) if tr else None
            res["cift"][p] = block(tr, pl)
            pools[grp] += tr
            if pl is not None:
                plp[grp].append((len(tr), pl))
            print(p, json.dumps(res["cift"][p], ensure_ascii=False), flush=True)
    for grp in ("ana", "kor"):
        w = np.array([k for k, _ in plp[grp]], float)
        pl = sum(k * v for k, v in plp[grp]) / w.sum()
        res[grp] = block(pools[grp], pl)
        print(grp.upper(), json.dumps(res[grp], ensure_ascii=False), flush=True)
    pd.DataFrame(pools["ana"] + pools["kor"]).to_parquet(f.RES / f"h10_islemler{'_ayna' if MIRROR else ''}.parquet")
    (f.RES / f"h10{'_ayna' if MIRROR else ''}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    return res


if __name__ == "__main__":
    if "--ayna" in sys.argv:
        MIRROR = True
    main()
