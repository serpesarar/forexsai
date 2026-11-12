"""QS-04: E1 çeyrek sonu, E2 ay başı geri tepme, E3 doz, N5 ABD/uluslararası dengeleme (PROTOCOL_QS04.md)."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from r1_dengeleme import px, synth_bond, st, H

TH, COST = 0.02, 2.0
RNG = np.random.default_rng(59)
PER = (("KESIF", "2002-08-01", "2013-12-31"), ("TEST", "2014-01-01", "2026-10-31"))


def monthly(eq: pd.Series, bond: pd.Series, inst: dict, intl: pd.Series | None = None) -> pd.DataFrame:
    cal = eq.dropna().index.intersection(bond.dropna().index)
    if intl is not None:
        cal = cal.intersection(intl.dropna().index)
    e, b = eq.reindex(cal).to_numpy(), bond.reindex(cal).to_numpy()
    last = pd.Series(np.arange(len(cal)), index=cal).groupby(cal.to_period("M")).max()
    L = last.to_numpy(); per = last.index
    rows = []
    for k in range(3, len(L)):
        Dp, p0 = L[k], L[k - 1]; s = Dp - 3
        if s <= p0 or Dp + 3 >= len(cal):
            continue
        r = dict(m=per[k], d_s=cal[s], d_D=cal[Dp], q=per[k].month in (3, 6, 9, 12))
        r["dm"] = (e[s] / e[p0] - 1) - (b[s] / b[p0] - 1)
        r["dq"] = (e[s] / e[L[k - 3]] - 1) - (b[s] / b[L[k - 3]] - 1)
        r["dD"] = (e[Dp] / e[p0] - 1) - (b[Dp] / b[p0] - 1)
        if intl is not None:
            f = intl.reindex(cal).to_numpy()
            r["d2"] = (e[s] / e[p0] - 1) - (f[s] / f[p0] - 1)
        for nm, x in inst.items():
            v = x.reindex(cal).to_numpy()
            r[f"w_{nm}"] = (v[Dp] / v[s] - 1) * 1e4        # R1 penceresi
            r[f"n_{nm}"] = (v[Dp + 3] / v[Dp] - 1) * 1e4    # E2 penceresi (yeni ayın ilk 3 günü)
        rows.append(r)
    return pd.DataFrame(rows)


def side(x: np.ndarray, sign: int = -1) -> np.ndarray:
    return np.where(x >= TH, sign, np.where(x <= -TH, -sign, 0))


def pnl(sd: np.ndarray, ret: np.ndarray) -> np.ndarray:
    return np.where(sd != 0, sd * ret - COST, 0.0)


def boot_mean_p(a: np.ndarray) -> float:
    return float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean())


def ols_t(y, X):
    X = np.column_stack([np.ones(len(y))] + X); b, *_ = np.linalg.lstsq(X, y, rcond=None); r = y - X @ b
    se = np.sqrt(np.diag(r.var(ddof=X.shape[1]) * np.linalg.inv(X.T @ X)))
    return [round(float(v), 2) for v in b[1:]], [round(float(v), 2) for v in (b / se)[1:]]


def per_block(M: pd.DataFrame, names: list[str]) -> dict:
    out = {}
    sR1 = side(M.dm.to_numpy())
    sE1 = side(np.where(M.q, M.dq, M.dm))
    sE2 = side(M.dD.to_numpy(), sign=+1)
    r1, e1, e2, base_n = [], [], [], []
    for nm in names:
        r1.append(pnl(sR1, M[f"w_{nm}"].to_numpy())); e1.append(pnl(sE1, M[f"w_{nm}"].to_numpy()))
        e2.append(pnl(sE2, M[f"n_{nm}"].to_numpy())); base_n.append(M[f"n_{nm}"].to_numpy() - COST)
    r1m, e1m, e2m = np.mean(r1, 0), np.mean(e1, 0), np.mean(e2, 0)   # ay başına QQQ/SPY ortalaması
    d = e1m - r1m
    out["R1_aylik_ort"] = round(float(r1m.mean()), 2)
    out["E1_aylik_ort"] = round(float(e1m.mean()), 2); out["E1_P"] = round(boot_mean_p(e1m[sE1 != 0]), 3)
    out["E1_islem"] = st(e1m[sE1 != 0]); out["E1-R1_aylik"] = round(float(d.mean()), 2); out["E1-R1_P"] = round(boot_mean_p(d), 3)
    q = M.q.to_numpy().astype(bool)
    out["ceyrek_aylari_R1"] = st(r1m[q & (sR1 != 0)]); out["ceyrek_aylari_E1"] = st(e1m[q & (sE1 != 0)])
    out["E2"] = st(e2m[sE2 != 0])
    bn = np.mean(base_n, 0)
    lg, sh = sE2 == 1, sE2 == -1
    out["E2_uzun"] = st(e2m[lg]); out["E2_kisa"] = st(e2m[sh])
    out["E2_taban_uzun_hepsi"] = round(float(bn.mean()), 2)
    out["E2_uzun-taban"] = round(float(e2m[lg].mean() - bn.mean()), 2) if lg.any() else None
    # E3 doz (R1)
    a = np.abs(M.dm.to_numpy()); trig = sR1 != 0
    if trig.sum() >= 9:
        qs = np.quantile(a[trig], [1 / 3, 2 / 3])
        out["E3_doz"] = {lab: st(r1m[trig & m]) for lab, m in
                         (("dusuk", a < qs[0]), ("orta", (a >= qs[0]) & (a < qs[1])), ("yuksek", a >= qs[1]))}
    if "d2" in M:
        sN = side(M.d2.to_numpy())
        n5 = np.mean([pnl(sN, M[f"w_{nm}"].to_numpy()) for nm in names], 0)
        out["N5"] = st(n5[sN != 0])
        y = np.mean([M[f"w_{nm}"].to_numpy() for nm in names], 0)
        out["N5_regresyon_dm_d2"] = dict(zip(("beta", "t"), ols_t(y, [M.dm.to_numpy() * 100, M.d2.to_numpy() * 100])))
        out["kor_dm_d2"] = round(float(np.corrcoef(M.dm, M.d2)[0, 1]), 2)
        both = (sN != 0) & (sR1 != 0)
        out["N5_R1_ayni_isaret"] = round(float((sN[both] == sR1[both]).mean()), 3) if both.any() else None
        only_n = (sN != 0) & (sR1 == 0)
        out["N5_yalniz(R1_tetiklemedi)"] = st(n5[only_n])
    return out


def main() -> None:
    names = ["QQQ", "SPY"]
    inst = {n: px(n) for n in names}
    M = monthly(px("SPY"), px("TLT"), inst, intl=px("EFA"))
    res = {}
    for p, a, b in PER:
        res[p] = per_block(M[(M.d_s >= a) & (M.d_s <= b)].reset_index(drop=True), names)
    g = px("GSPC", "Close")
    G = monthly(g, synth_bond(px("TNX", "Close")), {"GSPC": g})
    res["BAGIMSIZ_1990_2002"] = per_block(G[(G.d_s >= "1990-01-01") & (G.d_s < "2002-08-01")].reset_index(drop=True), ["GSPC"])
    K, T, B = res["KESIF"], res["TEST"], res["BAGIMSIZ_1990_2002"]
    e1 = K["E1-R1_aylik"] > 0 and T["E1-R1_aylik"] > 0 and K["E1_P"] >= .9 and T["E1_P"] >= .9 and B["E1_aylik_ort"] >= B["R1_aylik_ort"]
    e2a = all(x["E2"].get("ort", -1) > 0 and x["E2"].get("P", 0) >= .9 for x in (K, T))
    e2b = all((x["E2_uzun-taban"] or -1) > 0 for x in (K, T)) and B["E2"].get("ort", -1) > 0
    n5a = all(x["N5"].get("ort", -1) > 0 and x["N5"].get("P", 0) >= .9 for x in (K, T))
    n5b = all(x["N5_regresyon_dm_d2"]["beta"][1] < 0 and x["N5_regresyon_dm_d2"]["t"][1] <= -1.5 for x in (K, T))
    res["hukum"] = {"E1": "genisleme kabul" if e1 else "X",
                    "E2": "B" if e2a and e2b else ("C+" if e2a else "X"),
                    "N5": "B" if n5a and n5b else ("C" if n5a else "X")}
    (H / "results/qs04.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
