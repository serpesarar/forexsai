"""QS-03 R1: ay sonu hisse/tahvil dengeleme akışı (PROTOCOL.md §R1)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

H = Path(__file__).resolve().parent
D = H / "data"
sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
TH, COST = 0.02, 2.0
RNG = np.random.default_rng(41)


def px(nm: str, col: str = "Adj Close") -> pd.Series:
    return pd.read_parquet(D / f"{nm}.parquet")[col]


def synth_bond(tnx: pd.Series) -> pd.Series:
    y = tnx / 100
    r = y.shift(1) / 252 - 7.5 * y.diff()
    return (1 + r.fillna(0)).cumprod()


def months(cal: pd.DatetimeIndex, lag: int, back: int) -> pd.DataFrame:
    """Her ay: önceki ay sonu (p0), sinyal günü s = D−lag, çıkış e = D−lag+back... (indeks konumları)."""
    s = pd.Series(np.arange(len(cal)), index=cal)
    last = s.groupby(cal.to_period("M")).max()
    rows = []
    for k in range(1, len(last)):
        Dpos = last.iloc[k]; p0 = last.iloc[k - 1]
        sp = Dpos - lag; ep = sp + back
        if sp <= p0 or ep > Dpos + 2 or ep >= len(cal):
            continue
        rows.append(dict(m=last.index[k], p0=p0, s=sp, e=ep))
    return pd.DataFrame(rows)


def build(eq: pd.Series, bond: pd.Series, inst: dict[str, pd.Series], lag: int = 3, hold: int = 3) -> pd.DataFrame:
    cal = eq.dropna().index.intersection(bond.dropna().index)
    eq, bond = eq.reindex(cal), bond.reindex(cal)
    M = months(cal, lag, hold)
    M["delta"] = (eq.iloc[M.s].values / eq.iloc[M.p0].values - 1) - (bond.iloc[M.s].values / bond.iloc[M.p0].values - 1)
    M["d_s"] = cal[M.s]; M["d_e"] = cal[M.e]
    for nm, s in inst.items():
        s = s.reindex(cal)
        M[f"r_{nm}"] = (s.iloc[M.e].values / s.iloc[M.s].values - 1) * 1e4
    M["side"] = np.where(M.delta >= TH, -1, np.where(M.delta <= -TH, 1, 0))
    return M


def st(a: np.ndarray) -> dict:
    a = a[np.isfinite(a)]
    if len(a) < 3:
        return {"n": int(len(a))}
    p = float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean())
    h = len(a) // 2
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "isabet": round(float((a > 0).mean()), 3), "P": round(p, 3),
            "y1": round(float(a[:h].mean()), 1), "y2": round(float(a[h:].mean()), 1)}


def rule(M: pd.DataFrame, nm: str) -> np.ndarray:
    t = M[M.side != 0]
    return (t.side * t[f"r_{nm}"] - COST).to_numpy()


def slope(M: pd.DataFrame, nm: str) -> dict:
    x, y = M.delta.to_numpy(), M[f"r_{nm}"].to_numpy()
    ok = np.isfinite(x) & np.isfinite(y); x, y = x[ok], y[ok]
    b = np.polyfit(x, y, 1)[0]; res = y - np.polyval(np.polyfit(x, y, 1), x)
    se = np.sqrt(res.var(ddof=2) / ((x - x.mean()) ** 2).sum())
    return {"egim_bp_per_1pct": round(b / 100, 2), "t": round(b / se, 2), "n": int(len(x))}


def broker_nas(M: pd.DataFrame) -> dict:
    from ortak import Mkt, SWAP_BP
    mk = Mkt("NAS100")
    out = []
    for _, r in M[(M.side != 0) & (M.d_s >= "2018-06-01")].iterrows():
        i, j = mk.at(r.d_s + pd.Timedelta(hours=16)), mk.at(r.d_e + pd.Timedelta(hours=16))
        if i < 0 or j < 0:
            continue
        c = mk.cost(i)
        bp = r.side * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - c / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j])
        out.append(bp)
    return st(np.array(out))


def main() -> None:
    inst = {nm: px(nm) for nm in ("QQQ", "SPY", "IWM", "DIA")}
    M = build(px("SPY"), px("TLT"), inst)
    P = build(px("SPY"), px("TLT"), inst, lag=13, hold=3)  # plasebo: ay ortası
    res = {}
    for per, a, b in (("KESIF", "2002-08-01", "2013-12-31"), ("TEST", "2014-01-01", "2026-10-31")):
        m = M[(M.d_s >= a) & (M.d_s <= b)]; pm = P[(P.d_s >= a) & (P.d_s <= b)]
        r = {nm: st(rule(m, nm)) for nm in inst}
        pool = np.concatenate([rule(m, "QQQ"), rule(m, "SPY")])
        r["havuz_QQQ_SPY"] = st(pool)
        r["egim"] = {nm: slope(m, nm) for nm in inst}
        r["plasebo_QQQ"] = st(rule(pm, "QQQ")); r["plasebo_SPY"] = st(rule(pm, "SPY"))
        r["n_kisa"] = int((m.side == -1).sum()); r["n_uzun"] = int((m.side == 1).sum())
        r["kisa_QQQ"] = st((-(m[m.side == -1].r_QQQ) - COST).to_numpy()); r["uzun_QQQ"] = st((m[m.side == 1].r_QQQ - COST).to_numpy())
        q = m[m.m.dt.month.isin([3, 6, 9, 12])]
        r["ceyrek_sonu_QQQ"] = st(rule(q, "QQQ"))
        res[per] = r
    # bağımsız 1990-2002
    g = px("GSPC", "Close"); bnd = synth_bond(px("TNX", "Close"))
    G = build(g, bnd, {"GSPC": g})
    G = G[(G.d_s >= "1990-01-01") & (G.d_s < "2002-08-01")]
    res["BAGIMSIZ_1990_2002"] = {"GSPC": st(rule(G, "GSPC")), "egim": slope(G, "GSPC"),
                                 "kisa": st((-(G[G.side == -1].r_GSPC) - COST).to_numpy()), "uzun": st((G[G.side == 1].r_GSPC - COST).to_numpy())}
    # sentetik tahvil 2002-2026 tutarlılık (TLT yerine)
    Ms = build(px("SPY"), synth_bond(px("TNX", "Close")), inst)
    res["sentetik_tahvil_2002_2026_QQQ"] = st(rule(Ms[Ms.d_s >= "2002-08-01"], "QQQ"))
    res["broker_NAS100_2018_26"] = broker_nas(M)
    # ölçütler
    K, T = res["KESIF"], res["TEST"]
    c1 = K["havuz_QQQ_SPY"].get("ort", -1) > 0 and K["havuz_QQQ_SPY"].get("P", 0) >= 0.9
    c2 = T["QQQ"].get("ort", -1) > 0 and T["SPY"].get("ort", -1) > 0 and T["havuz_QQQ_SPY"].get("P", 0) >= 0.9
    c3 = K["egim"]["QQQ"]["egim_bp_per_1pct"] < 0 and T["egim"]["QQQ"]["egim_bp_per_1pct"] < 0
    c4 = res["BAGIMSIZ_1990_2002"]["GSPC"].get("ort", -1) > 0
    c5 = res["broker_NAS100_2018_26"].get("ort", -1) > 0
    cls = "B" if all([c1, c2, c3, c4, c5]) else ("C+" if c1 and c2 and c3 else ("C" if c2 and c3 else "X"))
    res["olcut"] = {"1": c1, "2": c2, "3": c3, "4": c4, "5": c5, "sinif": cls}
    (H / "results/r1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
