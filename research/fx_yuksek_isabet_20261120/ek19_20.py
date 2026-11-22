"""EK-19 emtia adil değer sapması + EK-20 hisse göreli getirisi (Hau–Rey) → D1 FX (PROTOCOL.md)."""
import itertools, json, sys
import numpy as np, pandas as pd
import core, d1

GEOM = list(itertools.product([0.5, 1.0], [2.0, 3.0], [5, 10]))
YF = core.HERE / "data/yf"
QS = core.HERE.parent / "qs03_akis_takvim_20261111/data"
_X = {}


def fx(pair):
    if pair not in _X:
        x = d1.load_d1(pair); x["day"] = x.srv.dt.normalize(); _X[pair] = x
    return _X[pair]


def ser_yf(s):
    d = pd.read_csv(YF / f"{s}.csv", index_col=0, parse_dates=True)
    c = pd.to_numeric(d["Close"], errors="coerce")
    return c.where(c > 0).dropna()


def ser_qs(s):
    d = pd.read_parquet(QS / f"{s}.parquet"); d.index = pd.to_datetime(d.index).normalize()
    return d["Close"].astype(float)


def per(y):
    return np.select([y <= 2009, y <= 2017], ["KESIF", "TEST"], "KOR")


def trades_for(pair, sig_days, sides, geo):
    x = fx(pair)
    pos = pd.Series(np.arange(len(x)), index=x.day.values)
    idx, sd = [], []
    for d, s in zip(sig_days, sides):
        if d in pos.index and s != 0:
            i = int(pos[d])
            if i > 25:
                idx.append(i); sd.append(int(s))
    if not idx:
        return pd.DataFrame()
    t = d1.trades(x, pair, np.array(idx), np.array(sd), geo)
    if len(t):
        t["day"] = x.day.values[t.sig.values]; t["time"] = t.day; t["pair"] = pair
    return t


def ek19(placebo=False):
    MAP = [("USDCAD", -1, "CL"), ("USDNOK", -1, "CL"), ("AUDUSD", 1, "HG"), ("AUDUSD", 1, "GC"), ("USDZAR", -1, "GC")]
    out = []
    for pair, s, com in MAP:
        c = ser_yf("ZC" if placebo else com)
        x = fx(pair).set_index("day")
        df = pd.DataFrame({"y": s * np.log(x.c), "x": np.log(c)}).dropna()
        cov = df.y.rolling(120).cov(df.x); var = df.x.rolling(120).var()
        b = cov / var; a = df.y.rolling(120).mean() - b * df.x.rolling(120).mean()
        e = df.y - (a + b * df.x)
        z = (e - e.rolling(120).mean()) / e.rolling(120).std()
        df["z"], df["b"] = z, b
        for k in (1.5, 2.0):
            m = (df.z.abs() >= k) & (df.b > 0)
            for gi, geo in enumerate(GEOM):
                t = trades_for(pair, df.index[m], (-np.sign(df.z[m]) * s).astype(int).values, geo)
                if len(t):
                    t["cell"] = f"k{k}|g{gi}"; t["map"] = f"{pair}~{com}"; out.append(t)
    T = pd.concat(out, ignore_index=True); T["per"] = per(pd.to_datetime(T.day).dt.year); return T


def ek20():
    MAP = [("EURUSD", 1, "GDAXI", "1999-01-01"), ("GBPUSD", 1, "FTSE", "1993-01-01"), ("USDJPY", -1, "N225", "1993-01-01")]
    spx = ser_qs("GSPC")
    out = []
    for pair, s, idx, start in MAP:
        f = ser_qs(idx)
        df = pd.DataFrame({"f": np.log(f), "u": np.log(spx)}).dropna()
        for L in (5, 20):
            D = (df.f - df.f.shift(L)) - (df.u - df.u.shift(L))
            z = D / D.rolling(250, min_periods=200).std().shift(1)
            zz = z[z.index >= start]
            for k in (1.5, 2.0):
                m = zz.abs() >= k
                for md in ("TERS", "DEVAM"):
                    cur = -np.sign(zz[m]) if md == "TERS" else np.sign(zz[m])
                    for gi, geo in enumerate(GEOM):
                        t = trades_for(pair, zz.index[m], (cur * s).astype(int).values, geo)
                        if len(t):
                            t["cell"] = f"L{L}|k{k}|{md}|g{gi}"; t["map"] = pair; out.append(t)
    T = pd.concat(out, ignore_index=True); T["per"] = per(pd.to_datetime(T.day).dt.year); return T


def table(T):
    rows = []
    for (c, p), g in T.groupby(["cell", "per"]):
        mo = max(1.0, (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44)
        s = core.summ(g); rows.append({"cell": c, "per": p, "frq": round(g.day.nunique() / mo, 2), **s})
    return pd.DataFrame(rows)


def main():
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    res = {}
    for nm, T in (("EK19", ek19()), ("EK19_plasebo", ek19(True)), ("EK20", ek20())):
        T.to_parquet(core.RES / f"trades_{nm}.parquet")
        H = table(T); H.to_csv(core.RES / f"tablo_{nm}.csv", index=False)
        K = H[H.per == "KESIF"].copy(); K["t"] = K.t.astype(float)
        print(nm, "KEŞİF"); print(K.sort_values("t", ascending=False).head(10)[["cell", "frq", "n", "wr", "ort", "t", "brut", "maliyet"]].to_string(index=False))
        if nm != "EK19_plasebo":
            S = K[(K.wr >= 70) & (K.ort > 0) & (K.t >= 2) & (K.frq >= 3)].sort_values("t", ascending=False).head(2)
            res[nm] = S.cell.tolist(); print("SEÇİLEN", res[nm])
    (core.RES / "ek19_20_secim.json").write_text(json.dumps(res))


if __name__ == "__main__":
    main()
