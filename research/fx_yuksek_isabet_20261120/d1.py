"""FX-YI EK-1: günlük ölçekli kenar × yüksek isabet geometrisi (PROTOCOL.md EK-1)."""
from __future__ import annotations

import importlib.util
import itertools
import sys

import numpy as np
import pandas as pd

import core

PER = [("KESIF", "1993-01-01", "2010-01-01"), ("TEST", "2010-01-01", "2018-01-01"), ("KOR", "2018-01-01", "2027-01-01")]
GEOM = list(itertools.product([0.25, 0.5], [1.0, 2.0], [1, 3, 5]))
SIGS = ["G1", "G2", "G2b", "G3", "G4", "G6", "G5"]
_sp = importlib.util.spec_from_file_location("fs", core.HERE.parents[1] / "yeni deneme" / "fx_fiks_shadow.py")
VIXREG_PAIRS = None
try:
    _m = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(_m)
    VIXREG_PAIRS = dict(_m.VIXREG_PAIRS)
    VIX_TH = float(_m.VIXREG_TH)
except Exception as e:  # noqa: BLE001
    print("VIXREG_PAIRS okunamadı:", e, file=sys.stderr)
    VIX_TH = 18.4

VIX = pd.read_csv(core.SRC / "data" / "vix_1990.csv")


def _vix() -> pd.Series:
    v = VIX.set_index(VIX.columns[0])
    return pd.Series(v["vix"].astype(float).values, index=pd.to_datetime(v.index).normalize()).sort_index()


def swap_bp(pair: str, side: int, price: float) -> float:
    m = core.META.get(pair, {})
    s = m.get("swap_long" if side > 0 else "swap_short")
    if s is None:
        return 0.0
    return float(s) * core.point(pair) / price * 1e4  # negatif = maliyet


def load_d1(pair: str) -> pd.DataFrame:
    x = pd.read_csv(core.FX / f"{pair}_D1.csv.gz")
    x["srv"] = pd.to_datetime(x.t, unit="s")
    x = x[x.srv.dt.weekday < 5].reset_index(drop=True)
    pc = x.c.shift(1)
    tr = np.maximum(x.h - x.l, np.maximum((x.h - pc).abs(), (x.l - pc).abs()))
    x["atr"] = tr.rolling(20).mean()
    x["r"] = x.c / pc - 1
    x["sig20"] = x.r.shift(1).rolling(20).std()
    d = x.c.diff()
    up = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean()
    x["rsi2"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    x["sma200"] = x.c.rolling(200).mean()
    x["dhi"] = x.h.shift(1).rolling(20).max()
    x["dlo"] = x.l.shift(1).rolling(20).min()
    s = np.sign(x.r)
    x["streak3"] = ((s == s.shift(1)) & (s == s.shift(2)) & (s != 0)) * s
    m15 = core.load(pair)
    base = float((m15.cost - core.comm_bp(pair)).median())
    sp = x.sp.astype(float) * core.point(pair) / x.o * 1e4
    c = 1.5 * np.fmax(sp.fillna(0).values, base) + core.comm_bp(pair)
    x["cost"] = np.where(x.srv < pd.Timestamp("2010-01-01"), 2 * c, c)
    x["cap"] = np.arange(len(x)) + 10_000
    return x


def signals(x: pd.DataFrame, sig: str, pair: str, vix: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """DEVAM yönünde (+1 AL / −1 SAT) sinyal; ayna = −side."""
    if sig == "G1":
        side = np.where(x.rsi2 > 90, 1, np.where(x.rsi2 < 10, -1, 0))
    elif sig in ("G2", "G2b"):
        k = 1.5 if sig == "G2" else 2.0
        side = np.where(x.r.abs() >= k * x.sig20, np.sign(x.r), 0)
    elif sig == "G3":
        side = x.streak3.fillna(0).values
    elif sig == "G4":  # DEVAM tanımı: trend içi geri çekilmede trend yönünde (= dönüş girişi)
        side = np.where((x.c > x.sma200) & (x.rsi2 < 10), 1, np.where((x.c < x.sma200) & (x.rsi2 > 90), -1, 0))
    elif sig == "G6":
        side = np.where(x.c > x.dhi, 1, np.where(x.c < x.dlo, -1, 0))
    elif sig == "G5":
        if not VIXREG_PAIRS or pair not in VIXREG_PAIRS:
            return np.array([], int), np.array([], int)
        v = vix.reindex(x.srv.dt.normalize()).ffill().values
        side = np.where(v >= VIX_TH, VIXREG_PAIRS[pair], 0)
    else:
        raise ValueError(sig)
    side = np.nan_to_num(np.asarray(side, float)).astype(int)
    ok = (side != 0) & x.atr.gt(0).values
    idx = np.where(ok)[0]
    return idx, side[idx]


def trades(x: pd.DataFrame, pair: str, idx: np.ndarray, side: np.ndarray, g: tuple) -> pd.DataFrame:
    tpk, slk, hold = g
    a = x.atr.values[idx]
    t = core.run(x.assign(day=x.srv.dt.normalize(), hr=0), idx, side, tpk * a, slk * a, np.full(len(idx), hold))
    if len(t) == 0:
        return t
    nights = (t.xi - t.ei + 1).astype(int)
    cw = np.concatenate([[0], np.cumsum(x.srv.dt.weekday.values == 2)])
    extra = 2 * (cw[t.xi.values + 1] - cw[t.ei.values])
    sl_, ss_ = swap_bp(pair, 1, 1.0), swap_bp(pair, -1, 1.0)
    sw = np.where(t.side > 0, sl_, ss_) / t.ep.values * (nights + extra)
    t["gross"] = t.gross + sw
    t["net"] = t.gross - t.cost
    t["R"] = t.net / t.sl_bp
    return t


def main() -> None:
    vix = _vix()
    out = []
    for pair in core.PAIRS:
        x = load_d1(pair)
        for sig in SIGS:
            idx, side = signals(x, sig, pair, vix)
            if len(idx) == 0:
                continue
            for mode, sd in (("DEVAM", side), ("AYNA", -side)):
                for gi, g in enumerate(GEOM):
                    t = trades(x, pair, idx, sd, g)
                    if len(t):
                        t["pair"], t["sig"], t["mode"], t["g"] = pair, sig, mode, gi
                        out.append(t[["pair", "sig", "mode", "g", "time", "day", "side", "why", "gross", "cost", "net", "R", "sl_bp"]])
        print(pair, flush=True)
    T = pd.concat(out, ignore_index=True)
    T["per"] = np.select([T.time < pd.Timestamp(PER[1][1]), T.time < pd.Timestamp(PER[2][1])], ["KESIF", "TEST"], "KOR")
    T.to_parquet(core.RES / "trades_G.parquet")


if __name__ == "__main__":
    main()
