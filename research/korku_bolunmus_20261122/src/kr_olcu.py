"""kr_olcu.py — ortak ölçüler + Tur 1 (KR-01). python kr_olcu.py tur1"""
from __future__ import annotations

import itertools
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import kr_motor as M  # noqa: E402

RNG = np.random.default_rng(122)
MAIN, BLIND = ["DUKA_NDX", "MT5_NAS100"], ["MT5_US500", "MT5_US30", "MT5_US2000"]


def load() -> list[dict]:
    return pickle.load(open(HERE / "cache/olaylar.pkl", "rb"))


def frame(P: list[dict], cells: dict) -> pd.DataFrame:
    rows = []
    for ev in P:
        r = {"feed": ev["feed"], "d": pd.Timestamp(ev["d"]), "donem": ev["donem"]}
        r["base"], r["base#j"] = M.sim(ev, "E0", "XP", 1.0)
        for c, fn in cells.items():
            r[c], r[c + "#j"] = fn(ev)
        rows.append(r)
    T = pd.DataFrame(rows)
    T["blk"] = T.feed + "|" + T.d.dt.to_period("M").astype(str)
    return T


def cvar5(v) -> float:
    s = np.sort(np.asarray(v, float))
    s = s[np.isfinite(s)]
    return float(s[:max(1, int(len(s) * 0.05))].mean()) if len(s) else np.nan


def sharpe(d: pd.Series, v: pd.Series) -> float:
    days = pd.bdate_range(d.min(), d.max())
    s = v.groupby(d.values).sum().reindex(days).fillna(0)
    return round(float(s.mean() / s.std() * np.sqrt(252)), 3) if s.std() > 0 else np.nan


def maxdd(d: pd.Series, v: pd.Series) -> float:
    s = v.groupby(d.values).sum().sort_index().cumsum()
    return round(float((s - s.cummax()).min()), 0)


def boot(v: np.ndarray, blk: np.ndarray, n: int = 3000) -> float:
    ub = np.unique(blk)
    idx = {u: np.flatnonzero(blk == u) for u in ub}
    return round(float(np.mean([v[np.concatenate([idx[u] for u in RNG.choice(ub, len(ub))])].mean() > 0 for _ in range(n)])), 4)


def stats(x: pd.DataFrame, c: str) -> dict:
    x = x.dropna(subset=[c])
    return {"n": len(x), "taban": round(float(x.base.mean()), 1), "ort": round(float(x[c].mean()), 1),
            "fark": round(float((x[c] - x.base).mean()), 1),
            "isabet": [round(float((x.base > 0).mean()), 3), round(float((x[c] > 0).mean()), 3)],
            "sharpe": [sharpe(x.d, x.base), sharpe(x.d, x[c])], "cvar5": [round(cvar5(x.base)), round(cvar5(x[c]))],
            "maxdd": [maxdd(x.d, x.base), maxdd(x.d, x[c])], "en_kotu": [round(float(x.base.min())), round(float(x[c].min()))]}


def select(T: pd.DataFrame, cells: list[str], cvar_mult: float = 1.2) -> dict:
    K = T[T.donem == "KESIF"]
    cv0 = cvar5(K.base)
    tab = {c: {"fark": round(float((K[c] - K.base).mean()), 2), "cvar5": round(cvar5(K[c])), "isabet": round(float((K[c] > 0).mean()), 3),
               "sharpe": sharpe(K.d, K[c])} for c in cells}
    elig = [c for c in cells if tab[c]["cvar5"] >= cvar_mult * cv0]
    sel = sorted(elig, key=lambda c: tab[c]["fark"], reverse=True)[:1]
    return {"kesif_taban": {"n": len(K), "ort": round(float(K.base.mean()), 1), "cvar5": round(cv0), "sharpe": sharpe(K.d, K.base)},
            "kesif_tablo": tab, "uygun": elig, "secilen": sel}


def judge(T: pd.DataFrame, c: str, cvar_lim: float = 1.5) -> dict:
    X = T[T.donem == "TEST"]
    res = {g: stats(X[X.feed == g], c) for g in MAIN + BLIND}
    x = X.dropna(subset=[c])
    P = boot((x[c] - x.base).values, x.blk.values)
    ok = {"i_ana": all(res[g]["fark"] > 0 for g in MAIN), "ii_P": P >= 0.95, "iii_kor": sum(res[g]["fark"] > 0 for g in BLIND) >= 2,
          "iv_sharpe": res["DUKA_NDX"]["sharpe"][1] > res["DUKA_NDX"]["sharpe"][0],
          "v_cvar": all(res[g]["cvar5"][1] >= cvar_lim * res[g]["cvar5"][0] for g in MAIN)}
    return {"test": res, "P": P, "olcut": ok, "hukum": "B" if all(ok.values()) else ("C" if ok["i_ana"] else "X"),
            "kesif": {g: stats(T[(T.donem == "KESIF") & (T.feed == g)], c) for g in MAIN + BLIND}}


def tur1() -> dict:
    cells = {f"{e}_{r}_h{h}": (lambda ev, e=e, r=r, h=h: M.sim(ev, e, r, h))
             for e, r, h in itertools.product(("E0", "E2"), ("XP", "XU"), (1.0, 0.5)) if not (e == "E0" and r == "XP" and h == 1.0)}
    T = frame(load(), cells)
    chk = {g: round(float(T[T.feed == g].base.mean()), 1) for g in MAIN}
    sel = select(T, list(cells))
    out = {"taban_kontrol_tum_donem": chk, "secim": sel, "hucre": {c: judge(T, c) for c in sel["secilen"]},
           "test_tum": {c: {g: stats(T[(T.donem == "TEST") & (T.feed == g)], c) for g in MAIN} for c in cells}}
    T.to_pickle(HERE / "cache/tur1.pkl")
    return out


# ───────── TUR 2 ─────────
_CTX: dict = {}


def _ctx():
    if _CTX:
        return _CTX
    sys.path.insert(0, str(M.ROOT / "research/caprev_tpsl_20261120/src"))
    import cr_gunluk as G  # noqa: E402
    import cr_motor as CM  # noqa: E402
    v = pd.read_parquet(CM.VIX_PATH)["Close"].squeeze()
    v.index = pd.to_datetime(v.index).tz_localize(None).normalize() if getattr(v.index, "tz", None) else pd.to_datetime(v.index).normalize()
    _CTX["vix"] = v.dropna()
    _CTX["r1"] = {n: G.load_daily(n).Close.pct_change() for n in ("NDX", "GSPC", "DJI", "RUT")}
    return _CTX


OWN = {"DUKA_NDX": "NDX", "MT5_NAS100": "NDX", "MT5_US500": "GSPC", "MT5_US30": "DJI", "MT5_US2000": "RUT"}


def d1_feats(ev: dict) -> dict:
    c = _ctx()
    d0, d1 = pd.Timestamp(ev["dates"][0]).normalize(), pd.Timestamp(ev["dates"][1]).normalize()
    vx = c["vix"]
    k0 = int(vx.index.searchsorted(d0)) - 1
    v0 = float(vx.iloc[k0]) if k0 >= 0 else np.nan
    v1 = float(vx.loc[d1]) if d1 in vx.index else np.nan
    br = 0
    for n, r in c["r1"].items():
        if n == OWN[ev["feed"]]:
            continue
        if d1 in r.index and r.loc[d1] <= -0.01:
            br += 1
    rng = ev["rhi"][1] - ev["rlo"][1]
    return {"r1bp": (ev["bid"][1] / ev["ask"][0] - 1) * 1e4, "vixchg": v1 / v0 - 1 if v0 > 0 else np.nan,
            "clv": (ev["bid"][1] - ev["rlo"][1]) / rng if rng > 0 else np.nan, "br": br, "ll": ev["rlo"][1] < ev["rlo"][0], "vix0": v0}


def s_cells() -> dict:
    C = {}
    for a in (50, 100, 150, 200):
        C[f"S1_{a}"] = ("S1", lambda f, a=a: f["r1bp"] <= -a)
    for v in (0.05, 0.10, 0.20):
        C[f"S2_{v}"] = ("S2", lambda f, v=v: np.isfinite(f["vixchg"]) and f["vixchg"] >= v)
    for q in (0.15, 0.25):
        C[f"S3_{q}"] = ("S3", lambda f, q=q: np.isfinite(f["clv"]) and f["clv"] <= q)
    for k in (2, 3):
        C[f"S4_{k}"] = ("S4", lambda f, k=k: f["br"] >= k)
    C["S5"] = ("S5", lambda f: bool(f["ll"]))
    return C


def tur2() -> dict:
    from sklearn.metrics import roc_auc_score
    P = load()
    for ev in P:
        ev["d1"] = d1_feats(ev) if len(ev["bid"]) > 1 else None
    S = s_cells()
    combos = {k: [k] for k in S} | {f"{a}|{b}": [a, b] for a, b in itertools.combinations(S, 2) if S[a][0] != S[b][0]}

    def mk(names):
        def hold(ev, j, r):
            return not any(S[n][1](ev["d1"]) for n in names)
        return lambda ev: M.sim(ev, "E0", "XP", 1.0, hold_if=hold)
    cells = {c: mk(n) for c, n in combos.items()}
    T = frame(P, cells)
    sel = select(T, list(cells))
    # anatomi: D1'de tutulanlar
    rows = []
    for ev, (_, r) in zip(P, T.iterrows()):
        if r["base#j"] <= 1 or ev["d1"] is None:
            continue
        cls = "COKUS" if r.base <= -300 else ("DONUS" if r.base > 0 else "SURUNME")
        rows.append({"donem": ev["donem"], "cls": cls, **ev["d1"],
                     **{f"g_{k}": v for k, v in ev["f"].items() if isinstance(v, float)}})
    A = pd.DataFrame(rows)
    an = {}
    for dn in ("KESIF", "TEST"):
        x = A[A.donem == dn]
        y = (x.cls == "COKUS").astype(int)
        tab = {"n": x.cls.value_counts().to_dict()}
        for col in [c for c in x.columns if c not in ("donem", "cls")]:
            v = pd.to_numeric(x[col], errors="coerce")
            ok = v.notna()
            if ok.sum() >= 30 and y[ok].sum() >= 5 and (1 - y[ok]).sum() >= 5:
                tab[col] = round(float(roc_auc_score(y[ok], v[ok])), 3)
        an[dn] = tab
    top = sorted([k for k in an["KESIF"] if k != "n"], key=lambda k: -abs(an["KESIF"][k] - 0.5))[:15]
    out = {"secim": {k: v for k, v in sel.items() if k != "kesif_tablo"},
           "kesif_ilk10": dict(sorted(sel["kesif_tablo"].items(), key=lambda kv: -kv[1]["fark"])[:10]),
           "anatomi_n": {dn: an[dn]["n"] for dn in an},
           "anatomi_ilk15": {k: [an["KESIF"].get(k), an["TEST"].get(k)] for k in top},
           "hucre": {c: judge(T, c) for c in sel["secilen"]}}
    T.to_pickle(HERE / "cache/tur2.pkl")
    return out


if __name__ == "__main__":
    fn = {"tur1": tur1, "tur2": tur2}[sys.argv[1]]
    out = fn()
    json.dump(out, open(HERE / f"results/{sys.argv[1]}.json", "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: out[k] for k in out if k != "test_tum"}, ensure_ascii=False, indent=1, default=float)[:6000])
