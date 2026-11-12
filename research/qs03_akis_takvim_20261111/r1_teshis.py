"""QS-03 R1 teşhis (SONRADAN, karar ölçütü değil): kazanç tahvil farkından mı (dengeleme) yoksa hissenin ay içi düşüşünün
dönüşünden mi (korku döner)? D1 yalnız-hisse kuralı, D2 iki değişkenli regresyon, D3 ay içi gün profili, D4 tahvil-yalnız kural."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from r1_dengeleme import px, build, months, synth_bond, st, COST, TH, H


def frame(eq, bond, inst, lag, hold=3):
    M = build(eq, bond, inst, lag, hold)
    cal = eq.dropna().index.intersection(bond.dropna().index)
    e, b = eq.reindex(cal), bond.reindex(cal)
    mm = months(cal, lag, hold)
    M["r_eq"] = e.iloc[mm.s].values / e.iloc[mm.p0].values - 1
    M["r_bd"] = b.iloc[mm.s].values / b.iloc[mm.p0].values - 1
    return M


def ols(y, X):
    X = np.column_stack([np.ones(len(y))] + X); ok = np.isfinite(X).all(1) & np.isfinite(y)
    X, y = X[ok], y[ok]; b, *_ = np.linalg.lstsq(X, y, rcond=None); r = y - X @ b
    cov = r.var(ddof=X.shape[1]) * np.linalg.inv(X.T @ X)
    return [round(float(v), 2) for v in b[1:]], [round(float(v), 2) for v in (b / np.sqrt(np.diag(cov)))[1:]]


def rule_on(M, nm, var, th=TH, sign=-1):
    side = np.where(M[var] >= th, sign, np.where(M[var] <= -th, -sign, 0))
    t = M[side != 0]; s = side[side != 0]
    return (s * t[f"r_{nm}"].to_numpy() - COST)


def main():
    inst = {nm: px(nm) for nm in ("QQQ", "SPY")}
    out = {}
    periods = (("KESIF", "2002-08-01", "2013-12-31"), ("TEST", "2014-01-01", "2026-10-31"))
    M = frame(px("SPY"), px("TLT"), inst, 3)
    for per, a, b in periods:
        m = M[(M.d_s >= a) & (M.d_s <= b)]
        r = {}
        for nm in inst:
            y = m[f"r_{nm}"].to_numpy()
            coef, t = ols(y, [m.r_eq.to_numpy() * 100, m.r_bd.to_numpy() * 100])
            r[nm] = {"D2_beta_hisse_bp_per_1pct": coef[0], "t_hisse": t[0], "beta_tahvil": coef[1], "t_tahvil": t[1],
                     "D1_yalniz_hisse_kural": st(rule_on(m, nm, "r_eq")), "Delta_kural": st(rule_on(m, nm, "delta")),
                     "D4_yalniz_tahvil_kural(tahvil↑→UZUN)": st(rule_on(m, nm, "r_bd", sign=1))}
        out[per] = r
    G = frame(px("GSPC", "Close"), synth_bond(px("TNX", "Close")), {"GSPC": px("GSPC", "Close")}, 3)
    g = G[(G.d_s >= "1990-01-01") & (G.d_s < "2002-08-01")]
    coef, t = ols(g.r_GSPC.to_numpy(), [g.r_eq.to_numpy() * 100, g.r_bd.to_numpy() * 100])
    out["BAGIMSIZ_1990_2002"] = {"beta_hisse": coef[0], "t_hisse": t[0], "beta_tahvil": coef[1], "t_tahvil": t[1]}
    # D3: ay içi profil (sinyal D−lag, 3 gün tut), QQQ+SPY havuz, 2002-2026
    prof = {}
    for lag in range(1, 19):
        Mx = frame(px("SPY"), px("TLT"), inst, lag)
        Mx = Mx[Mx.d_s >= "2002-08-01"]
        a = np.concatenate([rule_on(Mx, "QQQ", "delta"), rule_on(Mx, "SPY", "delta")])
        e = np.concatenate([rule_on(Mx, "QQQ", "r_eq"), rule_on(Mx, "SPY", "r_eq")])
        prof[f"D-{lag}"] = {"Delta": round(float(np.mean(a)), 1), "yalniz_hisse": round(float(np.mean(e)), 1), "n": int(len(a))}
    out["D3_profil"] = prof
    (H / "results/r1_teshis.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
