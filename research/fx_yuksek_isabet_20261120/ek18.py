"""EK-18: CFTC TFF COT pozisyon sinyalleri × D1 geometri (PROTOCOL.md EK-18)."""
import glob, itertools, json
import numpy as np, pandas as pd
import core, d1

CODES = {"099741": ("EURUSD", 1), "096742": ("GBPUSD", 1), "097741": ("USDJPY", -1), "232741": ("AUDUSD", 1),
         "090741": ("USDCAD", -1), "092741": ("USDCHF", -1), "112741": ("NZDUSD", 1), "095741": ("USDMXN", -1)}
SKIP = [("2013-10-01", "2013-11-01"), ("2018-12-18", "2019-03-08"), ("2025-09-30", "2026-01-31")]
GEOM = list(itertools.product([0.5, 1.0], [2.0, 3.0], [5, 10]))
GRID = list(itertools.product(["P-LEV", "F-LEV", "P-AM"], [1.5, 2.0], ["TERS", "DEVAM"], range(len(GEOM))))


def cot() -> pd.DataFrame:
    fs = sorted(glob.glob(str(core.HERE / "data/cot_raw/fut_fin_txt_*/*.txt")))
    x = pd.concat([pd.read_csv(f, low_memory=False, dtype={"CFTC_Contract_Market_Code": str}) for f in fs], ignore_index=True)
    x["code"] = x.CFTC_Contract_Market_Code.str.strip()
    x = x[x.code.isin(CODES)].copy()
    x["rep"] = pd.to_datetime(x.As_of_Date_In_Form_YYMMDD.astype(int).astype(str).str.zfill(6), format="%y%m%d")
    x = x.drop_duplicates(["code", "rep"]).sort_values(["code", "rep"])
    oi = x.Open_Interest_All.astype(float)
    x["lev"] = (x.Lev_Money_Positions_Long_All.astype(float) - x.Lev_Money_Positions_Short_All.astype(float)) / oi
    x["am"] = (x.Asset_Mgr_Positions_Long_All.astype(float) - x.Asset_Mgr_Positions_Short_All.astype(float)) / oi
    x["dlev"] = x.groupby("code").lev.diff()
    for col, nm in (("lev", "P-LEV"), ("dlev", "F-LEV"), ("am", "P-AM")):
        g = x.groupby("code")[col]
        mu = g.transform(lambda s: s.shift(1).rolling(52, min_periods=40).mean())
        sd = g.transform(lambda s: s.shift(1).rolling(52, min_periods=40).std())
        x["z_" + nm] = (x[col] - mu) / sd
    keep = np.ones(len(x), bool)
    for a, b in SKIP:
        keep &= ~((x.rep >= a) & (x.rep <= b))
    x = x[keep]
    x["pub"] = x.rep + pd.Timedelta(days=3)   # Cuma yayını
    return x


def main():
    C = cot()
    print("hafta sayısı", C.groupby("code").size().to_dict(), C.rep.min(), C.rep.max())
    out = []
    for code, (pair, cs) in CODES.items():
        x = d1.load_d1(pair)
        x["day"] = x.srv.dt.normalize()
        c = C[C.code == code]
        pos = pd.Series(np.arange(len(x)), index=x.day.values)
        for ci, (sg, k, md, gi) in enumerate(GRID):
            z = c["z_" + sg].values
            m = np.abs(z) >= k
            idx, side = [], []
            for pub, zz in zip(c.pub.values[m], z[m]):
                pub = pd.Timestamp(pub)
                j = pos.index.searchsorted(pub, side="right") - 1   # yayın Cuma'sının (veya öncesi son) D1 barı
                if j < 25 or pd.Timestamp(pos.index[j]) < pub - pd.Timedelta(days=3):
                    continue
                cur = -np.sign(zz) if md == "TERS" else np.sign(zz)   # para birimi yönü
                idx.append(int(pos.iloc[j])); side.append(int(cur * cs))
            if not idx:
                continue
            t = d1.trades(x, pair, np.array(idx), np.array(side), GEOM[gi])
            if len(t) == 0:
                continue
            t["day"] = x.day.values[t.sig.values] if "sig" in t else x.day.values[t.ei.values - 1]
            t["time"] = t.day
            t["pair"], t["cell"] = pair, ci
            out.append(t)
        print(pair, flush=True)
    T = pd.concat(out, ignore_index=True)
    y = pd.to_datetime(T.time).dt.year
    T["per"] = np.select([y <= 2017, y <= 2021], ["KESIF", "TEST"], "KOR")
    T.to_parquet(core.RES / "trades_EK18.parquet")
    rows = []
    for ci, g in T[T.per == "KESIF"].groupby("cell"):
        months = (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44
        rows.append({"cell": ci, "def": GRID[ci][:3] + (GEOM[GRID[ci][3]],), "frq": round(g.day.nunique() / months, 2), **core.summ(g)})
    H = pd.DataFrame(rows); H.to_csv(core.RES / "kesif_EK18.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(H[["cell", "def", "frq", "n", "wr", "ort", "t", "brut", "maliyet"]].to_string(index=False))


if __name__ == "__main__":
    main()
