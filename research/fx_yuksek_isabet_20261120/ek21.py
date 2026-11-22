"""EK-21: faiz farkı adil değeri (A) + Fed net likiditesi (B) → D1 FX (PROTOCOL.md EK-21)."""
import json
import numpy as np, pandas as pd
import core, ek19_20 as E

QS = E.QS


def per21(y, a, b):
    return np.select([y <= a, y <= b], ["KESIF", "TEST"], "KOR")


def fix_cost(T):
    pre = pd.to_datetime(T.day) < "2010-01-01"
    T.loc[pre, "cost"] = T.loc[pre, "cost"] / 2
    T["net"] = T.gross - T.cost; T["R"] = T.net / T.sl_bp
    return T


def famA(placebo=False):
    us = E.ser_qs("TNX")
    eu = pd.read_csv(QS / "EU_AAA_10Y.csv", parse_dates=["d"]).set_index("d").y
    spread = (us - eu.reindex(us.index).ffill()).dropna()
    MAP = [("EURUSD", spread, -1), ("USDJPY", us, 1)]
    out = []
    for pair, xs, sign in MAP:
        if placebo:
            xs = xs.shift(260)
        x = E.fx(pair).set_index("day")
        df = pd.DataFrame({"y": np.log(x.c), "x": xs}).dropna()
        b = df.y.rolling(120).cov(df.x) / df.x.rolling(120).var()
        a = df.y.rolling(120).mean() - b * df.x.rolling(120).mean()
        e = df.y - (a + b * df.x)
        z = (e - e.rolling(120).mean()) / e.rolling(120).std()
        for k in (1.5, 2.0):
            m = (z.abs() >= k) & (np.sign(b) == sign)
            for gi, geo in enumerate(E.GEOM):
                t = E.trades_for(pair, df.index[m], (-np.sign(z[m])).astype(int).values, geo)
                if len(t):
                    t["cell"] = f"k{k}|g{gi}"; out.append(t)
    T = pd.concat(out, ignore_index=True)
    T["per"] = per21(pd.to_datetime(T.day).dt.year, 2012, 2018)
    return fix_cost(T)


def famB():
    w = pd.read_csv(QS / "WALCL.csv"); t = pd.read_csv(QS / "WTREGEN.csv"); r = pd.read_csv(QS / "RRPONTSYD.csv")
    for x in (w, t, r):
        x.columns = ["d", "v"]; x["d"] = pd.to_datetime(x.d); x["v"] = pd.to_numeric(x.v, errors="coerce")
    nl = w.set_index("d").v - t.set_index("d").v.reindex(w.d).values
    rr = r.set_index("d").v.reindex(w.d, method="ffill").fillna(0).values * 1000
    ch = (nl - rr).dropna().pct_change(4)
    z = (ch - ch.shift(1).rolling(52, min_periods=40).mean()) / ch.shift(1).rolling(52, min_periods=40).std()
    thu = ch.index + pd.Timedelta(days=1)
    BASK = {"EURUSD": 1, "GBPUSD": 1, "AUDUSD": 1, "NZDUSD": 1, "USDJPY": -1, "USDCHF": -1, "USDCAD": -1}
    out = []
    for thr in ("SIGN", "Z1"):
        m = (ch.notna() & (ch != 0)).values if thr == "SIGN" else (z.abs() >= 1).values
        usd_short = np.sign(ch.values) > 0
        for md in ("ANA", "AYNA"):
            for pair, s in BASK.items():
                sides = np.where(usd_short, s, -s) * (1 if md == "ANA" else -1)
                for gi, geo in enumerate(E.GEOM):
                    tt = E.trades_for(pair, thu[m], sides[m].astype(int), geo)
                    if len(tt):
                        tt["cell"] = f"{thr}|{md}|g{gi}"; out.append(tt)
    T = pd.concat(out, ignore_index=True)
    T["per"] = per21(pd.to_datetime(T.day).dt.year, 2012, 2018)
    return fix_cost(T)


def main():
    pd.set_option("display.width", 250)
    res = {}
    for nm, T in (("EK21A", famA()), ("EK21A_plasebo", famA(True)), ("EK21B", famB())):
        T.to_parquet(core.RES / f"trades_{nm}.parquet")
        H = E.table(T); H.to_csv(core.RES / f"tablo_{nm}.csv", index=False)
        K = H[H.per == "KESIF"].copy(); K["t"] = K.t.astype(float)
        print(nm); print(K.sort_values("t", ascending=False).head(8)[["cell", "frq", "n", "wr", "ort", "t", "brut", "maliyet"]].to_string(index=False))
        S = K[(K.wr >= 70) & (K.ort > 0) & (K.t >= 2) & (K.frq >= 3)].sort_values("t", ascending=False).head(2)
        res[nm] = S.cell.tolist(); print("SEÇİLEN", res[nm])
        for c in res[nm] if not nm.endswith("plasebo") else []:
            for p in ("TEST", "KOR"):
                g = T[(T.cell == c) & (T.per == p)]
                print("  ", c, p, core.summ(g, boot=True))
    (core.RES / "ek21_secim.json").write_text(json.dumps(res))


if __name__ == "__main__":
    main()
