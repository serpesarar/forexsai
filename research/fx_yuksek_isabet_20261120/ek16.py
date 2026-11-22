"""EK-16: saatlik kesitsel para birimi gücü dönüş/devam (PROTOCOL.md EK-16)."""
import itertools
import numpy as np, pandas as pd
import core, ek11

MAJ = {"EUR": ("EURUSD", 1), "GBP": ("GBPUSD", 1), "AUD": ("AUDUSD", 1), "NZD": ("NZDUSD", 1), "CAD": ("USDCAD", -1), "CHF": ("USDCHF", -1), "JPY": ("USDJPY", -1)}
GRID = list(itertools.product([4, 24], [1.5, 2.0], ["DONUS", "DEVAM"], [4, 8], [1.0, 2.0]))
AVAIL = set(core.PAIRS)


def strengths():
    cl = {}
    for c, (p, s) in MAJ.items():
        x = ek11.h1(p).set_index("utc")
        cl[c] = s * np.log(x.c)
    C = pd.DataFrame(cl).dropna()
    C["USD"] = 0.0
    return C


def decisions(C, L):
    r = C - C.shift(L)
    r = r[r.index.hour.isin([0, 4, 8, 12, 16, 20])].dropna()
    hi, lo = r.idxmax(axis=1), r.idxmin(axis=1)
    D = r.max(axis=1) - r.min(axis=1)
    z = D / D.rolling(250, min_periods=120).std().shift(1)
    return pd.DataFrame({"hi": hi, "lo": lo, "z": z}).dropna()


def main():
    C = strengths()
    out = []
    for ci, (L, k, mode, H, slk) in enumerate(GRID):
        dec = decisions(C, L)
        dec = dec[dec.z >= k]
        by_pair = {}
        for t0, r in dec.iterrows():
            a, b = r.hi, r.lo           # a güçlü, b zayıf
            if a + b in AVAIL:
                pair, side_rev = a + b, -1  # güçlü baz → dönüşte sat
            elif b + a in AVAIL:
                pair, side_rev = b + a, +1
            else:
                continue
            side = side_rev if mode == "DONUS" else -side_rev
            by_pair.setdefault(pair, []).append((t0, side))
        for pair, lst in by_pair.items():
            x = ek11.h1(pair)
            pos = pd.Series(np.arange(len(x)), index=x.utc.values)
            ii, ss = [], []
            for t0, sd in lst:
                if t0 in pos.index:
                    i = int(pos[t0]) + 1      # güç t0 barının KAPANIŞINDAN → giriş sonraki bar açılışı (E7)
                    hrs = x.hr.values[i:i + H]
                    if len(hrs) == H and not np.isin(hrs, [23, 0]).any() and i > 15:
                        ii.append(i); ss.append(sd)
            if not ii:
                continue
            ii = np.array(ii); U = x.atr.values[ii - 1] * np.sqrt(H)
            t = core.run(x, ii - 1, np.array(ss), 0.5 * U, slk * U, np.full(len(ii), H))
            if len(t) == 0:
                continue
            t["time"] = x.utc.values[t.ei.values]; t["day"] = x.day.values[t.ei.values]
            t["pair"], t["cell"] = pair, ci
            out.append(t)
        print(ci, flush=True)
    T = pd.concat(out, ignore_index=True)
    T["per"] = [ek11.per(pd.Timestamp(v)) for v in T.time.values]
    T.to_parquet(core.RES / "trades_EK16.parquet")
    rows = []
    for ci, g in T[T.per == "KESIF"].groupby("cell"):
        months = (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44
        rows.append({"cell": ci, "def": GRID[ci], "frq": round(g.day.nunique() / months, 1), **core.summ(g)})
    H = pd.DataFrame(rows); H.to_csv(core.RES / "kesif_EK16.csv", index=False)
    pd.set_option("display.width", 250)
    print(H[["cell", "def", "frq", "n", "wr", "ort", "t", "brut", "maliyet"]].to_string(index=False))


if __name__ == "__main__":
    main()
