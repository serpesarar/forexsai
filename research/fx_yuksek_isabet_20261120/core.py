"""FX-YI ortak çekirdek: veri, maliyet, TP/SL yarışı (numba), özet. Ön kayıt: PROTOCOL.md."""
from __future__ import annotations

import json
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "fx_secim_20261113"
FX = SRC / "data" / "fx"
RES = HERE / "results"
RES.mkdir(exist_ok=True)
SRV_MINUS_ET_H = 7
SPLIT = pd.Timestamp("2025-01-01")
START = pd.Timestamp("2022-11-07")
ROLL_CUT_H = 23  # srv 23:00'ten sonra pozisyon taşınmaz
PAIRS = ["AUDCAD", "AUDJPY", "AUDNZD", "AUDUSD", "CADJPY", "CHFJPY", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY",
         "EURUSD", "GBPAUD", "GBPCHF", "GBPJPY", "GBPUSD", "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "USDMXN",
         "USDNOK", "USDSEK", "USDZAR"]
BASE_USD = {"EUR": 1.16, "GBP": 1.33, "AUD": 0.66, "NZD": 0.58, "CAD": 0.72, "USD": 1.0, "CHF": 1.25}
TS = json.loads((SRC / "data" / "tick_spread.json").read_text())["sp"]
META = json.loads((SRC / "data" / "probe.json").read_text())["fx"]


def point(pair: str) -> float:
    m = META.get(pair)
    if m:
        return float(m["point"])
    return 1e-3 if pair.endswith("JPY") else 1e-5


def comm_bp(pair: str) -> float:
    """Razor 7$/lot gidiş-dönüş, 100k baz para birimi nominaline göre bp."""
    return 7.0 / (100_000 * BASE_USD[pair[:3]]) * 1e4


_CACHE: dict[str, pd.DataFrame] = {}


def load(pair: str) -> pd.DataFrame:
    """M15 barlar + göstergeler. srv = sunucu saati (NY+7)."""
    if pair in _CACHE:
        return _CACHE[pair]
    x = pd.read_csv(FX / f"{pair}_M15.csv.gz")
    x["srv"] = pd.to_datetime(x.t, unit="s")
    x = x[x.srv >= START].reset_index(drop=True)
    x["hr"] = x.srv.dt.hour.astype(np.int64)
    x["day"] = x.srv.dt.normalize()
    sp = x.sp.astype(float) * point(pair) / x.o * 1e4
    sh = (TS.get(pair) or {}).get("saat")
    tick = x.hr.map(lambda h: sh.get(str(h), [np.nan])[0]) if sh else pd.Series(np.nan, index=x.index)
    x["cost"] = np.fmax(sp.values, np.nan_to_num(tick.values.astype(float), nan=0.0)) + comm_bp(pair)
    pc = x.c.shift(1)
    tr = np.maximum(x.h - x.l, np.maximum((x.h - pc).abs(), (x.l - pc).abs()))
    x["atr"] = tr.rolling(14).mean()
    x["sma"] = x.c.rolling(20).mean()
    x["sd"] = x.c.rolling(20).std(ddof=0)
    # devir sınırı: aynı srv günü içinde saati < 23 olan son bar
    ok = (x.hr < ROLL_CUT_H).values
    idx = np.arange(len(x))
    last = pd.Series(np.where(ok, idx, -1)).groupby(x.day.values).transform("max").values
    x["cap"] = last
    # günlük ATR20 (yalnız önceki günler) ve gün açılışı
    d = x.groupby("day").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), n=("o", "size"))
    d = d[d.n >= 40]
    dpc = d.c.shift(1)
    dtr = np.maximum(d.h - d.l, np.maximum((d.h - dpc).abs(), (d.l - dpc).abs()))
    d["atrd"] = dtr.rolling(20).mean().shift(1)
    x["dopen"] = x.day.map(d.o)
    x["atrd"] = x.day.map(d.atrd)
    _CACHE[pair] = x
    return x


@nb.njit(cache=True)
def race(o, h, l, c, sig, side, tp, sl, tmax, cap):
    """Sinyal barı sig[i] kapanışından sonra sig[i]+1 açılışında giriş; çift başına tek pozisyon.
    Döndürür: giriş idx, çıkış idx, giriş fiyatı, çıkış fiyatı, neden (1 TP, -1 SL, 0 zaman)."""
    n = len(sig)
    ei = np.full(n, -1, np.int64)
    xi = np.full(n, -1, np.int64)
    ep = np.zeros(n)
    xp = np.zeros(n)
    rs = np.zeros(n, np.int64)
    busy = -1
    N = len(o)
    for k in range(n):
        j = sig[k] + 1
        if j >= N or j <= busy:
            continue
        end = min(j + tmax[k] - 1, cap[sig[k]], N - 1)
        if end < j:
            continue
        e = o[j]
        s = side[k]
        up = e + tp[k] if s > 0 else e + sl[k]
        dn = e - sl[k] if s > 0 else e - tp[k]
        out = c[end]
        why = 0
        t = end
        for b in range(j, end + 1):
            hit_up = h[b] >= up
            hit_dn = l[b] <= dn
            if hit_up or hit_dn:
                t = b
                if s > 0:
                    if hit_dn:
                        out, why = dn, -1
                    else:
                        out, why = up, 1
                else:
                    if hit_up:
                        out, why = up, -1
                    else:
                        out, why = dn, 1
                break
        ei[k], xi[k], ep[k], xp[k], rs[k] = j, t, e, out, why
        busy = t
    return ei, xi, ep, xp, rs


def run(x: pd.DataFrame, sig: np.ndarray, side: np.ndarray, tp: np.ndarray, sl: np.ndarray, tmax: np.ndarray,
        cost_mult: float = 1.0) -> pd.DataFrame:
    """Sinyal dizileri → işlem tablosu (bp)."""
    if len(sig) == 0:
        return pd.DataFrame()
    order = np.argsort(sig, kind="stable")
    sig, side, tp, sl, tmax = sig[order], side[order], tp[order], sl[order], tmax[order]
    ei, xi, ep, xp, rs = race(x.o.values, x.h.values, x.l.values, x.c.values, sig.astype(np.int64),
                              side.astype(np.int64), tp.astype(float), sl.astype(float), tmax.astype(np.int64),
                              x.cap.values.astype(np.int64))
    m = ei >= 0
    t = pd.DataFrame({"sig": sig[m], "side": side[m], "ei": ei[m], "xi": xi[m], "ep": ep[m], "xp": xp[m], "why": rs[m],
                      "tp_bp": tp[m] / ep[m] * 1e4, "sl_bp": sl[m] / ep[m] * 1e4})
    t["gross"] = t.side * (t.xp - t.ep) / t.ep * 1e4
    t["cost"] = x.cost.values[t.ei.values] * cost_mult
    t["net"] = t.gross - t.cost
    t["R"] = t.net / t.sl_bp
    t["time"] = x.srv.values[t.sig.values]
    t["day"] = x.day.values[t.sig.values]
    t["hr"] = x.hr.values[t.sig.values]
    return t


def boot_p(v: np.ndarray, g: np.ndarray, n: int = 2000, seed: int = 7) -> float:
    """P(ort > 0), gün-kümeli bootstrap."""
    if len(v) < 5:
        return float("nan")
    s = pd.Series(v).groupby(g).agg(["sum", "count"])
    su, co = s["sum"].values, s["count"].values
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), (n, len(s)))
    m = su[idx].sum(1) / co[idx].sum(1)
    return float((m > 0).mean())


def summ(t: pd.DataFrame, boot: bool = False) -> dict:
    if len(t) == 0:
        return {"n": 0}
    v = t.net.values
    sd = v.std(ddof=1) if len(v) > 2 else np.nan
    d = {"n": int(len(v)), "gun": int(t.day.nunique()), "wr": round(float((v > 0).mean()) * 100, 1),
         "tp_orani": round(float((t.why == 1).mean()) * 100, 1), "ort": round(float(v.mean()), 3),
         "ortR": round(float(t.R.mean()), 4), "t": round(float(v.mean() / (sd / np.sqrt(len(v)))), 2) if sd > 0 else None,
         "brut": round(float(t.gross.mean()), 3), "maliyet": round(float(t.cost.mean()), 3),
         "stres15": round(float((t.gross - 1.5 * t.cost).mean()), 3)}
    if boot:
        d["P"] = round(boot_p(v, t.day.values), 3)
        h = len(v) // 2
        tt = t.sort_values("time")
        d["yari"] = [round(float(tt.net.values[:h].mean()), 3), round(float(tt.net.values[h:].mean()), 3)]
    return d
