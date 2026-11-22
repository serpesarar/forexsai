"""EK-13: VIXREG-FX yönü × H1 geri çekilme × yüksek isabet geometrisi (PROTOCOL.md EK-13)."""
import itertools, json
import numpy as np, pandas as pd
import core, d1, ek11

PAIRS = dict(d1.VIXREG_PAIRS)
GRID = list(itertools.product([1.5, 2.0], [0.5, 1.0], [3.0, 6.0], [24, 72]))
VIX = d1._vix()


def swap_cost(x, t, pair):
    """Tutulan devir başına bugünkü swap (bp, + = kazanç); Çarşamba ×3."""
    days = x.srv.dt.normalize().values
    wd = x.srv.dt.dayofweek.values
    out = np.zeros(len(t))
    sl, ss = d1.swap_bp(pair, 1, 1.0), d1.swap_bp(pair, -1, 1.0)
    for k, (a, b, s) in enumerate(zip(t.ei.values, t.xi.values, t.side.values)):
        ch = np.where(days[a + 1:b + 1] != days[a:b])[0] + a
        n = len(ch) + 2 * int((wd[ch] == 2).sum())
        out[k] = n * (sl if s > 0 else ss) / x.c.values[a]
    return out


def run_pair(pair):
    x = ek11.h1(pair)
    rd = PAIRS[pair]
    etd = (x.srv - pd.Timedelta(hours=core.SRV_MINUS_ET_H)).dt.normalize()
    v = VIX.reindex(VIX.index.union(etd.unique())).sort_index().ffill().shift(1).reindex(etd).values
    reg = v >= d1.VIX_TH
    sma, sd = x.c.rolling(20).mean(), x.c.rolling(20).std(ddof=0)
    out = []
    for ci, (k, tpk, slk, tm) in enumerate(GRID):
        lo, hi = x.c < sma - k * sd, x.c > sma + k * sd
        dip = (lo if rd > 0 else hi).values      # risk yönüne karşı geri çekilme
        rip = (hi if rd > 0 else lo).values
        for grp, m, side in (("ANA", reg & dip, rd), ("K1", (~reg) & dip & ~np.isnan(v), rd), ("K2", reg & rip, -rd)):
            idx = np.where(m & x.atr.notna().values)[0]
            if len(idx) == 0:
                continue
            a = x.atr.values[idx]
            t = core.run(x, idx, np.full(len(idx), side), tpk * a, slk * a, np.full(len(idx), tm))
            if len(t) == 0:
                continue
            sw = swap_cost(x, t, pair)
            t["gross"] = t.gross + sw
            t["net"] = t.gross - t.cost
            t["R"] = t.net / t.sl_bp
            t["swap"] = sw
            t["time"] = x.utc.values[t.ei.values]
            t["day"] = x.day.values[t.ei.values]
            t["pair"], t["cell"], t["grp"] = pair, ci, grp
            out.append(t)
    print(pair, flush=True)
    return pd.concat(out, ignore_index=True)


def main():
    T = pd.concat([run_pair(p) for p in PAIRS], ignore_index=True)
    T["per"] = [ek11.per(pd.Timestamp(v)) for v in T.time.values]
    T.to_parquet(core.RES / "trades_EK13.parquet")
    pd.set_option("display.width", 250)
    rows = []
    for (ci, grp), g in T[T.per == "KESIF"].groupby(["cell", "grp"]):
        rows.append({"cell": ci, "def": GRID[ci], "grp": grp, **core.summ(g)})
    H = pd.DataFrame(rows)
    H.to_csv(core.RES / "kesif_EK13.csv", index=False)
    print(H[H.grp == "ANA"].to_string(index=False))
    print(H[H.grp != "ANA"][["cell", "grp", "n", "wr", "ort", "brut"]].to_string(index=False))


if __name__ == "__main__":
    main()
