"""EK-15: NDX korku gecesi (QQQ V1/V0) → risk FX gecesi (PROTOCOL.md EK-15)."""
import itertools, json
import numpy as np, pandas as pd
import core, d1, ek11, ek13

Q = pd.read_parquet(core.HERE.parent / "qs03_akis_takvim_20261111/data/QQQ.parquet")
Q.index = pd.to_datetime(Q.index).normalize()
V1 = (Q.Close <= (Q.High + Q.Low) / 2 * 0.995) & (Q.Close < Q.Open)
V0 = ((Q.Close - Q.Low) / (Q.High - Q.Low) <= 0.25) & (Q.Close < Q.Open)
VIXP = d1._vix().shift(1)
GRID = list(itertools.product(["V1", "V0"], [False, True], [0.5, 1.0], [1.5, 3.0, 100.0], ["X0", "X1"]))
PAIRS = dict(d1.VIXREG_PAIRS)


def run_pair(pair):
    x = ek11.h1(pair)
    pos = pd.Series(np.arange(len(x)), index=x.utc.values)
    rows = []
    for d in Q.index[(Q.index >= "2010-10-08") & (Q.index <= "2026-11-12")]:
        nd = d + pd.offsets.BDay(1)
        ti = ek11.loc(d, 16, "America/New_York")
        if ti not in pos.index:
            continue
        for ex, (dd, hh) in (("X0", (nd, 9)), ("X1", (nd, 16))):
            to = ek11.loc(dd, hh, "America/New_York")
            if to in pos.index:
                rows.append((d, ex, int(pos[ti]), int(pos[to])))
    S = pd.DataFrame(rows, columns=["d", "ex", "i", "j"])
    S["v1"], S["v0"] = S.d.map(V1).fillna(False).astype(bool), S.d.map(V0).fillna(False).astype(bool)
    S["vix"] = (S.d.map(VIXP.reindex(VIXP.index.union(S.d.unique())).ffill()) >= d1.VIX_TH)
    S["U"] = x.atr.values[S.i - 1] * np.sqrt((S.j - S.i).clip(lower=1))
    out = []
    for ci, (dfn, vx, tpk, slk, ex) in enumerate(GRID):
        s = S[(S.ex == ex) & S.U.notna()]
        sigm = s["v1" if dfn == "V1" else "v0"] & (s.vix if vx else True)
        for grp, g in (("ANA", s[sigm]), ("KONTROL", s[~sigm])):
            if len(g) == 0:
                continue
            t = core.run(x, (g.i - 1).values, np.full(len(g), PAIRS[pair]), tpk * g.U.values, slk * g.U.values, (g.j - g.i).values)
            if len(t) == 0:
                continue
            sw = ek13.swap_cost(x, t, pair)
            t["gross"] = t.gross + sw; t["net"] = t.gross - t.cost; t["R"] = t.net / t.sl_bp
            t["time"] = x.utc.values[t.ei.values]; t["day"] = (pd.to_datetime(t.time) - pd.Timedelta(hours=5)).dt.normalize()
            t["pair"], t["cell"], t["grp"] = pair, ci, grp
            out.append(t)
    print(pair, flush=True)
    return pd.concat(out, ignore_index=True)


def main():
    T = pd.concat([run_pair(p) for p in PAIRS], ignore_index=True)
    T["per"] = [ek11.per(pd.Timestamp(v)) for v in T.time.values]
    T.to_parquet(core.RES / "trades_EK15.parquet")
    rows = []
    for (ci, grp), g in T[T.per == "KESIF"].groupby(["cell", "grp"]):
        months = (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44
        rows.append({"cell": ci, "def": GRID[ci], "grp": grp, "frq": round(g.day.nunique() / months, 2), **core.summ(g)})
    H = pd.DataFrame(rows); H.to_csv(core.RES / "kesif_EK15.csv", index=False)
    pd.set_option("display.width", 250)
    A = H[H.grp == "ANA"].merge(H[H.grp == "KONTROL"][["cell", "wr", "ort"]], on="cell", suffixes=("", "_k"))
    print(A[["cell", "def", "frq", "n", "gun", "wr", "ort", "t", "brut", "maliyet", "wr_k", "ort_k"]].to_string(index=False))


if __name__ == "__main__":
    main()
