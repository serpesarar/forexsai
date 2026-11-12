"""QS-10: ay sonu dengeleme testleri altında (PROTOCOL.md). 2 sinyal × 4 pencere × 2 yön; KEŞİF'te tek seçim."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
Q3 = H.parent / "qs03_akis_takvim_20261111"
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111")); sys.path.insert(0, str(Q3))
from ortak import Mkt, SWAP_BP  # noqa: E402
from r1_dengeleme import synth_bond  # noqa: E402

TH, COST = 0.02, 2.0
RNG = np.random.default_rng(113)
KES, TES = ("2004-12-01", "2014-12-31"), ("2015-01-01", "2026-10-31")
WIN = ("R1", "SON", "GECE", "E2")


def load(p: Path, adj: bool = True) -> tuple[pd.Series, pd.Series]:
    x = pd.read_parquet(p)
    if adj and "Adj Close" in x:
        f = x["Adj Close"] / x.Close
        return x.Open * f, x["Adj Close"]
    return x.Open, x.Close


def table(eq: pd.Series, bond: pd.Series, gO: pd.Series, gC: pd.Series) -> pd.DataFrame:
    cal = eq.dropna().index.intersection(bond.dropna().index).intersection(gC.dropna().index)
    e, b, O, C = (s.reindex(cal).to_numpy() for s in (eq, bond, gO, gC))
    L = pd.Series(np.arange(len(cal)), index=cal).groupby(cal.to_period("M")).max()
    rows = []
    for k in range(1, len(L)):
        Dp, p0 = int(L.iloc[k]), int(L.iloc[k - 1]); s = Dp - 3
        if s <= p0 or Dp + 3 >= len(cal):
            continue
        rows.append(dict(m=str(L.index[k]), d_s=cal[s], d_D=cal[Dp], d_D1=cal[Dp + 1], d_D3=cal[Dp + 3],
                         S1=(e[s] / e[p0] - 1) - (b[s] / b[p0] - 1), S2=C[s] / C[p0] - 1,
                         S1_D=(e[Dp] / e[p0] - 1) - (b[Dp] / b[p0] - 1), S2_D=C[Dp] / C[p0] - 1,
                         R1=(C[Dp] / C[s] - 1) * 1e4, SON=(C[Dp] / O[Dp] - 1) * 1e4,
                         GECE=(O[Dp + 1] / C[Dp] - 1) * 1e4, E2=(C[Dp + 3] / C[Dp] - 1) * 1e4))
    return pd.DataFrame(rows)


def sig(M: pd.DataFrame, sname: str, w: str) -> np.ndarray:
    x = M[f"{sname}_D" if w == "E2" else sname].to_numpy()
    return np.where(x >= TH, 1, np.where(x <= -TH, -1, 0))


def cell(M: pd.DataFrame, sname: str, w: str, d: int) -> np.ndarray:
    s = sig(M, sname, w) * d
    return (s * M[w].to_numpy() - COST)[s != 0]


def st(a: np.ndarray) -> dict:
    a = a[np.isfinite(a)]
    if len(a) < 5:
        return {"n": int(len(a))}
    P = float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean()); h = len(a) // 2
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "t": round(float(a.mean() / a.std(ddof=1) * np.sqrt(len(a))), 2),
            "isabet": round(float((a > 0).mean()), 3), "P": round(P, 3), "y1": round(float(a[:h].mean()), 1), "y2": round(float(a[h:].mean()), 1)}


def broker(M: pd.DataFrame, sname: str, w: str, d: int, stress: float) -> dict:
    mk = Mkt("XAUUSD", stress=stress); s = sig(M, sname, w) * d; out = []
    for k, r in M.reset_index(drop=True).iterrows():
        if s[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        t0, t1 = {"R1": (r.d_s + pd.Timedelta(minutes=960), r.d_D + pd.Timedelta(minutes=960)),
                  "SON": (r.d_D + pd.Timedelta(minutes=570), r.d_D + pd.Timedelta(minutes=960)),
                  "GECE": (r.d_D + pd.Timedelta(minutes=960), r.d_D1 + pd.Timedelta(minutes=570)),
                  "E2": (r.d_D + pd.Timedelta(minutes=960), r.d_D3 + pd.Timedelta(minutes=960))}[w]
        i, j = mk.at(t0), mk.at(t1)
        if i < 0 or j < 0 or not np.isfinite(mk.cost(i)):
            continue
        out.append(s[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    return st(np.array(out))


def holm(p: dict) -> dict:
    ks = sorted(p, key=p.get); m = len(ks); out, run = {}, 0.0
    for i, k in enumerate(ks):
        run = max(run, min(1.0, (m - i) * p[k])); out[k] = round(run, 3)
    return out


def main() -> None:
    spy, tlt = load(Q3 / "data/SPY.parquet")[1], load(Q3 / "data/TLT.parquet")[1]
    gO, gC = load(H / "data/GLD.parquet")
    M = table(spy, tlt, gO, gC)
    Mk, Mt = M[(M.d_s >= KES[0]) & (M.d_s <= KES[1])], M[(M.d_s >= TES[0]) & (M.d_s <= TES[1])]
    names = [(s, w, d) for s in ("S1", "S2") for w in WIN for d in (1, -1)]
    lab = lambda s, w, d: f"{s}_{w}_{'AYNI' if d == 1 else 'TERS'}"
    kes = {lab(*c): st(cell(Mk, *c)) for c in names}; tes = {lab(*c): st(cell(Mt, *c)) for c in names}
    best = max(names, key=lambda c: kes[lab(*c)].get("t", -9)); bl = lab(*best)
    bt = tes[bl]; br1, br15 = broker(M, *best, 1.0), broker(M, *best, 1.5)
    # destek: GC=F 2000-08 → 2004-11, sentetik tahvil
    gc = pd.read_parquet(H.parent / "qs09_gunluk_kapi_20261112/data/GC.parquet")
    gsp = pd.read_parquet(Q3 / "data/GSPC.parquet")["Close"]; bnd = synth_bond(pd.read_parquet(Q3 / "data/TNX.parquet")["Close"])
    G = table(gsp, bnd, gc.Open, gc.Close); G = G[(G.d_s >= "2000-08-01") & (G.d_s < "2004-12-01")]
    sup = st(cell(G, *best))
    a = bt.get("ort", -1) > 0 and bt.get("P", 0) >= .9
    b = min(bt.get("y1", -1), bt.get("y2", -1)) >= 0
    c = br15.get("ort", -1) > 0
    cls = "B-" if a and b and c else ("C" if a else "X")
    pv = {k: 1 - v.get("P", 0) for k, v in tes.items() if "P" in v}
    res = {"secilen": bl, "KESIF": kes[bl], "TEST": bt, "broker_x1": br1, "broker_x1.5": br15, "destek_GC_2000_04": sup,
           "olcut": {"a": a, "b": b, "c": c}, "sinif": cls,
           "tum": {k: {"KESIF_t": kes[k].get("t"), "KESIF_ort": kes[k].get("ort"), "TEST_ort": tes[k].get("ort"), "TEST_P": tes[k].get("P"),
                       "TEST_n": tes[k].get("n")} for k in kes},
           "holm_TEST": holm(pv),
           "taban_GLD_TEST": {w: round(float(Mt[w].mean()), 1) for w in WIN},
           "aylik_tetik_orani": {s: round(float((sig(M, s, "R1") != 0).mean()), 2) for s in ("S1", "S2")}}
    (H / "results/qs10.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
