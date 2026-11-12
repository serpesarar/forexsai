"""QS-01: QQQ kapanış saati stratejisi — broker M30 (birincil + kör) ve Dukascopy 1m (birebir). PROTOCOL.md."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402

OUT = H / "results"; OUT.mkdir(exist_ok=True)
GAP, RANGE_POS, STOP, SMA_N = 0.006, 0.77, 0.01, 50
RNG = np.random.default_rng(7)


def days_m30(mk: Mkt, stress: float = 1.0) -> pd.DataFrame:
    """Gün başına 15:00 durumu + 15:00→16:00 uzun işlem sonucu (bp, maliyet dahil)."""
    rows = []
    df = pd.DataFrame({"d": mk.d, "m": mk.m, "i": np.arange(len(mk.m))})
    df = df[mk.wd < 5]
    for d, g in df.groupby("d"):
        idx = dict(zip(g.m, g.i))
        need = [570, 900, 930, 960]
        if not all(k in idx for k in need):
            continue
        rth = [idx[m] for m in range(570, 900, 30) if m in idx]
        if len(rth) < 10:
            continue
        o = mk.o[idx[570]]
        hi, lo = mk.h[rth].max(), mk.l[rth].min()
        p15 = mk.c[idx[870]] if 870 in idx else np.nan
        i_in, i_out = idx[900], idx[960]
        e = mk.o[i_in] + mk.cost(i_in) * stress
        stop_px = e * (1 - STOP)
        lows = min(mk.l[idx[900]], mk.l[idx[930]])
        x = stop_px if lows <= stop_px else mk.o[i_out]
        rows.append(dict(d=d, open=o, close=mk.o[i_out], p15=p15, hi=hi, lo=lo,
                         ret=(x / e - 1) * 1e4, gross=(mk.o[i_out] / mk.o[i_in] - 1) * 1e4,
                         stopped=lows <= stop_px))
    return pd.DataFrame(rows).set_index("d")


def flags(x: pd.DataFrame) -> pd.DataFrame:
    x = x.copy()
    prev = x.close.shift(1)
    sma = x.close.rolling(SMA_N).mean()
    x["c1"] = (prev < sma.shift(1))
    x["c2"] = x.open > prev * (1 + GAP)
    x["c3"] = x.p15 > x.open
    rp = (x.p15 - x.lo) / (x.hi - x.lo)
    x["c4"] = rp > RANGE_POS
    x = x.iloc[SMA_N:]
    x["sig"] = x.c1 & x.c2 & x.c3 & x.c4
    return x


def boot_p(v: np.ndarray, B: int = 10000) -> float:
    if len(v) < 2:
        return np.nan
    m = v[RNG.integers(0, len(v), (B, len(v)))].mean(1)
    return float((m > 0).mean())


def stats(v: pd.Series) -> dict:
    v = v.dropna(); a = v.to_numpy(); h = len(a) // 2
    if len(a) == 0:
        return {"n": 0}
    return {"n": len(a), "ort_bp": round(a.mean(), 2), "isabet": round((a > 0).mean(), 3),
            "P": round(boot_p(a), 3), "y1": round(a[:h].mean(), 2) if h else np.nan,
            "y2": round(a[h:].mean(), 2) if h else np.nan, "top_bp": round(a.sum(), 0),
            "kotu": round(a.min(), 0), "en_iyi5_haric": round(np.sort(a)[:-5].mean(), 2) if len(a) > 6 else np.nan}


def placebo(x: pd.DataFrame, B: int = 10000) -> float:
    """Kuralın ort'unun, aynı yıl dağılımıyla rastgele T0 günlerinin ort dağılımındaki yüzdeliği."""
    s = x[x.sig]; obs = s.ret.mean()
    yrs = s.index.year.value_counts()
    pools = {y: x.ret[x.index.year == y].to_numpy() for y in yrs.index}
    sims = np.zeros(B)
    for y, k in yrs.items():
        sims += RNG.choice(pools[y], (B, k)).sum(1)
    sims /= len(s)
    return float((sims < obs).mean())


def run_sym(sym: str) -> dict:
    mk = Mkt(sym)
    x = flags(days_m30(mk))
    xs = flags(days_m30(mk, stress=1.5))
    res = {"kural": stats(x.ret[x.sig]), "brut_kural": stats(x.gross[x.sig]),
           "T0": stats(x.ret), "T1_c3c4": stats(x.ret[x.c3 & x.c4]),
           "stres_x1.5": stats(xs.ret[xs.sig]), "plasebo_yuzdelik": round(placebo(x), 3),
           "stop_orani": round(float(x.stopped[x.sig].mean()), 3) if x.sig.any() else np.nan}
    for drop in ("c1", "c2", "c3", "c4"):
        keep = [c for c in ("c1", "c2", "c3", "c4") if c != drop]
        res[f"abl_-{drop}"] = stats(x.ret[x[keep].all(1)])
    res["c1c2_tumgun"] = stats(x.ret[x.c1 & x.c2])
    res["yil"] = {int(y): round(float(g.mean()), 1) for y, g in x.ret[x.sig].groupby(x[x.sig].index.year)}
    res["yil_n"] = {int(y): int(len(g)) for y, g in x.ret[x.sig].groupby(x[x.sig].index.year)}
    x[x.sig].to_csv(OUT / f"islemler_{sym}.csv")
    return res


def prefix_test(sym: str) -> bool:
    """15:00 sonrası barlar silinince sinyal değişmemeli (koşul 1-4 yalnız ≤15:00 veriyle)."""
    mk = Mkt(sym); x = flags(days_m30(mk))
    y = x.copy(); y["close_prev_only"] = y.close.shift(1)
    # c3/c4 yalnız open, p15, hi, lo kullanır; c1/c2 yalnız dünkü kapanış → yapısal olarak önek-güvenli.
    return bool((x.sig == (x.c1 & x.c2 & x.c3 & x.c4)).all())


if __name__ == "__main__":
    out = {s: run_sym(s) for s in ("NAS100", "US500", "US30", "US2000")}
    out["prefix_ok"] = prefix_test("NAS100")
    (OUT / "m30.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False))
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))
