"""QS-02: coşku kırılması ve kardeş senaryolar — 18 ön-kayıtlı hücre (PROTOCOL_QS02.md)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402

OUT = H / "results"; OUT.mkdir(exist_ok=True)
RNG = np.random.default_rng(23)
E_RET, E_K, G_SMALL, G_BIG = 0.015, 0.75, 0.003, 0.006
CELLS = ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "B1", "B2", "B3", "B4",
         "C1", "C2", "C3", "C4", "C5", "D5", "D6"]
DAILY_CELLS = ["A1", "A7", "A8", "B1", "B3", "D5", "D6"]


def day_table(mk: Mkt) -> pd.DataFrame:
    """Gün başına: fiyatlar (O, P600, P900, C), aralıklar, bar indeksleri."""
    df = pd.DataFrame({"d": mk.d, "m": mk.m, "i": np.arange(len(mk.m))})[mk.wd < 5]
    rows = []
    for d, g in df.groupby("d"):
        idx = dict(zip(g.m, g.i))
        if not all(k in idx for k in (570, 600, 900, 930, 960)):
            continue
        pre = [idx[m] for m in range(570, 900, 30) if m in idx]
        full = [idx[m] for m in range(570, 960, 30) if m in idx]
        if len(pre) < 10:
            continue
        rows.append(dict(d=d, O=mk.o[idx[570]], P600=mk.o[idx[600]], P900=mk.o[idx[900]], C=mk.o[idx[960]],
                         hi15=mk.h[pre].max(), lo15=mk.l[pre].min(), hi=mk.h[full].max(), lo=mk.l[full].min(),
                         i570=idx[570], i600=idx[600], i900=idx[900], i960=idx[960]))
    return pd.DataFrame(rows).set_index("d")


def features(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    t["C1"] = t.C.shift(1); t["C2"] = t.C.shift(2); t["C3"] = t.C.shift(3)
    t["r"] = t.C / t.C1 - 1
    t["k"] = (t.C - t.lo) / (t.hi - t.lo)
    t["r1"] = t.r.shift(1); t["k1"] = t.k.shift(1); t["r2"] = t.r.shift(2)
    t["gap"] = t.O / t.C1 - 1
    t["sma"] = t.C.rolling(50).mean().shift(1)
    t["max250"] = t.C.rolling(250, min_periods=200).max().shift(1)
    k15 = (t.P900 - t.lo15) / (t.hi15 - t.lo15)
    t["strong15"] = (t.P900 > t.O) & (k15 > 0.77)
    t["weak15"] = (t.P900 < t.O) & (k15 < 0.23)
    t["E"] = (t.r1 >= E_RET) & (t.k1 >= E_K)
    t["F"] = (t.r1 <= -E_RET) & (t.k1 <= 1 - E_K)
    t["Gm"] = t.gap <= -G_SMALL; t["Gp"] = t.gap >= G_SMALL
    t["GpB"] = t.gap >= G_BIG; t["GmB"] = t.gap <= -G_BIG
    t["red"] = t.C < t.O
    t["bear"] = t.C1 < t.sma; t["bull"] = t.C1 > t.sma
    t["qs01"] = t.bear & t.GpB & t.strong15
    t["nO"] = t.O.shift(-1); t["ni570"] = t.i570.shift(-1); t["ni960"] = t.i960.shift(-1)
    return t.iloc[50:]


def masks(t: pd.DataFrame) -> dict:
    E, Gm = t.E, t.Gm
    return {
        "A1": E & Gm, "A3": E & Gm & (t.P600 < t.O), "A4": E & Gm & (t.P600 > t.O),
        "A5": E & Gm & t.weak15, "A6": E & Gm & (t.P900 > t.C1),
        "A7": E & Gm & t.red, "A8": E & Gm & t.red,
        "B1": t.F & t.Gp, "B2": t.F & t.Gp & t.strong15, "B3": E & t.GpB, "B4": E & t.GpB & t.weak15,
        "C1": t.bull & t.GpB & t.strong15, "C2": t.bull & t.GmB & t.weak15,
        "C3": t.bear & t.GmB & t.strong15, "C4": t.bear & t.GpB & (t.P900 < t.O), "C5": t.qs01,
        "D5": (t.r1 > 0) & (t.r2 > 0) & (t.C1 / t.C3 - 1 >= 0.03) & Gm,
        "D6": (t.C1 >= t.max250) & Gm,
    }


# hücre → (giriş sütunu, çıkış sütunu, yön)
TRADE = {"A1": ("i570", "i960", 1), "A3": ("i600", "i960", -1), "A4": ("i600", "i960", 1),
         "A5": ("i900", "i960", -1), "A6": ("i900", "i960", 1), "A7": ("i960", "ni570", 1),
         "A8": ("i960", "ni960", 1), "B1": ("i570", "i960", 1), "B2": ("i900", "i960", 1),
         "B3": ("i570", "i960", 1), "B4": ("i900", "i960", -1), "C1": ("i900", "i960", 1),
         "C2": ("i900", "i960", -1), "C3": ("i900", "i960", 1), "C4": ("i900", "i960", -1),
         "C5": ("i960", "ni570", 1), "D5": ("i570", "i960", 1), "D6": ("i570", "i960", 1)}


def trade_series(mk: Mkt, t: pd.DataFrame, cin: str, cout: str, side: int, stress: float = 1.0) -> pd.Series:
    out = {}
    for d, a, b in zip(t.index, t[cin], t[cout]):
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        a, b = int(a), int(b)
        if b <= a:
            continue
        cost = mk.cost(a) * stress
        if not np.isfinite(cost):
            continue
        e, x = mk.o[a], mk.o[b]
        bp = side * (x - e) / e * 1e4 - cost / e * 1e4 - SWAP_BP * mk.swaps(mk.et[a], mk.et[b])
        out[d] = bp
    return pd.Series(out, dtype=float)


def st(v: pd.Series) -> dict:
    v = v.dropna(); a = v.to_numpy()
    if len(a) < 2:
        return {"n": int(len(a))}
    h = len(a) // 2
    p = float((a[RNG.integers(0, len(a), (10000, len(a)))].mean(1) > 0).mean())
    return {"n": int(len(a)), "ort": round(float(a.mean()), 2), "isabet": round(float((a > 0).mean()), 3),
            "P": round(p, 4), "y1": round(float(a[:h].mean()), 2), "y2": round(float(a[h:].mean()), 2),
            "kotu": round(float(a.min()), 0), "iyi5_haric": round(float(np.sort(a)[:-5].mean()), 2) if len(a) > 8 else None}


def run_broker(sym: str) -> tuple[dict, pd.DataFrame]:
    mk = Mkt(sym); t = features(day_table(mk)); M = masks(t)
    res, rows = {}, []
    for c in CELLS:
        cin, cout, side = TRADE[c]
        allv = trade_series(mk, t, cin, cout, side)
        v = allv.reindex(t.index[M[c].fillna(False)]).dropna()
        s = st(v); s["taban"] = round(float(allv.mean()), 2); s["fark"] = round(s.get("ort", np.nan) - s["taban"], 2)
        if c in ("A1",):
            s["stres15"] = st(trade_series(mk, t.loc[v.index], cin, cout, side, 1.5)).get("ort")
        res[c] = s
        for d, x in v.items():
            rows.append(dict(sym=sym, cell=c, d=d, bp=x))
    # betimsel
    a1 = trade_series(mk, t, "i570", "i960", 1)
    base = t[t.E & t.Gm]
    res["dz_A1_doz"] = {lab: st(a1.reindex(base.index[m]).dropna()) for lab, m in
                        (("-0.3..-0.6", base.gap > -0.006), ("-0.6..-1.0", (base.gap <= -0.006) & (base.gap > -0.01)),
                         ("<=-1.0", base.gap <= -0.01))}
    res["dz_A1_pazartesi"] = st(a1.reindex(base.index[base.index.dayofweek == 0]).dropna())
    res["dz_A1_yil"] = {int(y): round(float(g.mean()), 1) for y, g in a1.reindex(base.index).dropna().groupby(lambda d: d.year)}
    return res, pd.DataFrame(rows)


def qqq_daily() -> dict:
    q = pd.read_parquet(H.parent / "ndx_kapi_20261110/data/QQQ.parquet")
    q = q[(q.index >= "1999-03-10") & (q.index < "2018-05-01")].copy()
    adj = q["Adj Close"] / q.Close
    t = pd.DataFrame({"O": q.Open * adj, "C": q["Adj Close"], "hi": q.High * adj, "lo": q.Low * adj})
    t["C1"] = t.C.shift(1); t["C3"] = t.C.shift(3)
    t["r"] = t.C / t.C1 - 1; t["k"] = (t.C - t.lo) / (t.hi - t.lo)
    t["r1"] = t.r.shift(1); t["k1"] = t.k.shift(1); t["r2"] = t.r.shift(2)
    t["gap"] = t.O / t.C1 - 1
    t["max250"] = t.C.rolling(250, min_periods=200).max().shift(1)
    t = t.iloc[260:]
    E = (t.r1 >= E_RET) & (t.k1 >= E_K); F = (t.r1 <= -E_RET) & (t.k1 <= 1 - E_K)
    Gm = t.gap <= -G_SMALL
    oc = (t.C / t.O - 1) * 1e4 - 2.0
    on = (t.O.shift(-1) / t.C - 1) * 1e4 - 2.0
    cc = (t.C.shift(-1) / t.C - 1) * 1e4 - 2.0
    red = t.C < t.O
    defs = {"A1": (E & Gm, oc), "A7": (E & Gm & red, on), "A8": (E & Gm & red, cc),
            "B1": (F & (t.gap >= G_SMALL), oc), "B3": (E & (t.gap >= G_BIG), oc),
            "D5": ((t.r1 > 0) & (t.r2 > 0) & (t.C1 / t.C3 - 1 >= 0.03) & Gm, oc),
            "D6": ((t.C1 >= t.max250) & Gm, oc)}
    out = {}
    for c, (m, ser) in defs.items():
        s = st(ser[m.fillna(False)]); s["taban"] = round(float(ser.mean()), 2)
        s["fark"] = round(s.get("ort", np.nan) - s["taban"], 2); out[c] = s
    return out


def holm(p: dict) -> dict:
    items = sorted(p.items(), key=lambda kv: kv[1]); m = len(items); adj, run = {}, 0.0
    for r, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - r) * v)); adj[k] = round(run, 4)
    return adj


def verdict(nas: dict, blind: dict, qq: dict, hadj: dict) -> dict:
    out = {}
    for c in CELLS:
        s = nas[c]
        if s.get("n", 0) < 20:
            out[c] = "betimsel (n<20)"; continue
        halves = s["y1"] >= 0 and s["y2"] >= 0
        fark = s["fark"] > 0
        bl = [blind[b][c].get("ort", np.nan) for b in blind]
        bn = [blind[b][c].get("n", 0) for b in blind]
        pooled = np.nansum([x * n for x, n in zip(bl, bn)]) / max(1, sum(bn))
        blind_ok = pooled > 0 and sum(1 for x in bl if x == x and x > 0) >= 2
        ind = qq.get(c); ind_ok = None if ind is None else (ind.get("ort", -1) > 0 and ind.get("P", 0) >= 0.9)
        ind_pass = ind_ok in (None, True)
        rawP = s["P"]
        if s["ort"] > 0 and hadj[c] <= 0.10 and halves and fark and blind_ok and ind_pass:
            v = "B"
        elif s["ort"] > 0 and rawP >= 0.95 and halves and fark and blind_ok and ind_pass:
            v = "C+"
        elif s["ort"] > 0 and rawP >= 0.90 and (blind_ok or ind_ok is True):
            v = "C"
        else:
            v = "X"
        out[c] = {"sinif": v, "yarilar": halves, "fark>0": fark, "kor_havuz": round(float(pooled), 2),
                  "kor_artı": int(sum(1 for x in bl if x == x and x > 0)), "bagimsiz": ind_ok, "holm": hadj[c]}
    return out


if __name__ == "__main__":
    res, trades = {}, []
    for s in ("NAS100", "US500", "US30", "US2000"):
        r, tr = run_broker(s); res[s] = r; trades.append(tr)
    qq = qqq_daily()
    pvals = {c: 1 - res["NAS100"][c]["P"] for c in CELLS if res["NAS100"][c].get("n", 0) >= 20}
    hadj = holm(pvals)
    for c in CELLS:
        hadj.setdefault(c, 1.0)
    ver = verdict(res["NAS100"], {b: res[b] for b in ("US500", "US30", "US2000")}, qq, hadj)
    out = {"broker": res, "qqq_1999_2018": qq, "holm": hadj, "hukum": ver}
    (OUT / "qs02.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False))
    pd.concat(trades).to_csv(OUT / "qs02_islemler.csv", index=False)
    print(f"{'hucre':5s} {'n':>4s} {'ort':>7s} {'P':>6s} {'y1':>7s} {'y2':>7s} {'taban':>6s} {'iyi5h':>6s} | "
          f"{'US500':>7s} {'US30':>7s} {'US2000':>7s} | {'QQQ99-18':>14s} | holm  sinif")
    for c in CELLS:
        s = res["NAS100"][c]; q = qq.get(c, {})
        bl = " ".join(f"{res[b][c].get('ort', float('nan')):7.1f}" for b in ("US500", "US30", "US2000"))
        qs = f"{q.get('ort', float('nan')):6.1f}/{q.get('n', 0):4d}/{q.get('P', float('nan')):.2f}" if q else " " * 14
        v = ver[c] if isinstance(ver[c], str) else ver[c]["sinif"]
        print(f"{c:5s} {s.get('n', 0):4d} {s.get('ort', float('nan')):7.1f} {s.get('P', float('nan')):6.3f} "
              f"{s.get('y1', float('nan')):7.1f} {s.get('y2', float('nan')):7.1f} {s.get('taban', float('nan')):6.1f} "
              f"{(s.get('iyi5_haric') or float('nan')):6.1f} | {bl} | {qs} | {hadj[c]:.3f} {v}")
