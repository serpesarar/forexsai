"""EK-18b: COT-TERS sağlamlık (gecikme, fiyat kontrolü, görülmemiş enstrüman, 1993–2009 legacy, sepet). PROTOCOL.md EK-18b."""
import glob, json
import numpy as np, pandas as pd
import core, d1, ek18

CELLS = {"19": ("P", 2.0, (0.5, 3.0, 10)), "39": ("F", 1.5, (1.0, 3.0, 10))}
BLIND = {"122741": ("USDZAR", -1), "299741": ("EURGBP", 1), "399741": ("EURJPY", 1)}
LEG = {"099741": ("EURUSD", 1), "096742": ("GBPUSD", 1), "097741": ("USDJPY", -1), "232741": ("AUDUSD", 1),
       "090741": ("USDCAD", -1), "092741": ("USDCHF", -1), "112741": ("NZDUSD", 1), "095741": ("USDMXN", -1)}
_X = {}
HIST = False


def zcols(x: pd.DataFrame, col: str) -> pd.DataFrame:
    x = x.sort_values(["code", "rep"]).copy()
    x["d_" + col] = x.groupby("code")[col].diff()
    for c, nm in ((col, "P"), ("d_" + col, "F")):
        g = x.groupby("code")[c]
        mu = g.transform(lambda s: s.shift(1).rolling(52, min_periods=40).mean())
        sd = g.transform(lambda s: s.shift(1).rolling(52, min_periods=40).std())
        x["z" + nm] = (x[c] - mu) / sd
    x["pub"] = x.rep + pd.Timedelta(days=3)
    keep = np.ones(len(x), bool)
    for a, b in ek18.SKIP:
        keep &= ~((x.rep >= a) & (x.rep <= b))
    return x[keep]


def tff() -> pd.DataFrame:
    fs = sorted(glob.glob(str(core.HERE / "data/cot_raw/fut_fin_txt_*/*.txt")))
    if HIST:
        fs = sorted(glob.glob(str(core.HERE / "data/cot_tff_hist/h/*.txt"))) + fs
    x = pd.concat([pd.read_csv(f, low_memory=False, dtype={"CFTC_Contract_Market_Code": str}) for f in fs], ignore_index=True)
    x["code"] = x.CFTC_Contract_Market_Code.str.strip()
    x["rep"] = pd.to_datetime(x.As_of_Date_In_Form_YYMMDD.astype(int).astype(str).str.zfill(6), format="%y%m%d")
    x = x.drop_duplicates(["code", "rep"])
    x["v"] = (x.Lev_Money_Positions_Long_All.astype(float) - x.Lev_Money_Positions_Short_All.astype(float)) / x.Open_Interest_All.astype(float)
    return zcols(x[["code", "rep", "v"]], "v")


def legacy() -> pd.DataFrame:
    fs = sorted(glob.glob(str(core.HERE / "data/cot_legacy/deacot*/*")))
    x = pd.concat([pd.read_csv(f, low_memory=False, dtype={"CFTC Contract Market Code": str}) for f in fs], ignore_index=True)
    x["code"] = x["CFTC Contract Market Code"].astype(str).str.strip()
    x["rep"] = pd.to_datetime(x["As of Date in Form YYMMDD"].astype(int).astype(str).str.zfill(6), format="%y%m%d")
    x = x[x.code.isin(LEG)].drop_duplicates(["code", "rep"])
    oi = pd.to_numeric(x["Open Interest (All)"], errors="coerce")
    x["v"] = (pd.to_numeric(x["Noncommercial Positions-Long (All)"], errors="coerce") - pd.to_numeric(x["Noncommercial Positions-Short (All)"], errors="coerce")) / oi
    return zcols(x[["code", "rep", "v"]], "v")


def pxload(pair):
    if pair not in _X:
        x = d1.load_d1(pair); x["day"] = x.srv.dt.normalize(); _X[pair] = x
    return _X[pair]


def price_z(codes: dict, ref: pd.DataFrame) -> pd.DataFrame:
    """Fiyat kontrolü: aynı rapor Salılarında para birimi log fiyatı (seviye) ve haftalık değişimi."""
    rows = []
    for code, (pair, cs) in codes.items():
        x = pxload(pair).set_index("day")
        r = ref[ref.code == code][["code", "rep"]].copy()
        r["v"] = [cs * np.log(x.c.iloc[x.index.searchsorted(d, side="right") - 1]) if x.index.searchsorted(d, side="right") > 0 else np.nan for d in r.rep]
        rows.append(r)
    return zcols(pd.concat(rows, ignore_index=True), "v")


def run(Z: pd.DataFrame, codes: dict, cell: str, delay: int = 0) -> pd.DataFrame:
    sg, k, geo = CELLS[cell]
    out = []
    for code, (pair, cs) in codes.items():
        c = Z[Z.code == code]
        if len(c) == 0:
            continue
        x = pxload(pair)
        idx_day = x.day.values
        z = c["z" + sg].values
        m = np.abs(z) >= k
        idx, side = [], []
        for pub, zz in zip(c.pub.values[m], z[m]):
            j = np.searchsorted(idx_day, np.datetime64(pub), side="right") - 1
            if j < 25 or j + delay >= len(x) - 1 or pd.Timestamp(idx_day[j]) < pd.Timestamp(pub) - pd.Timedelta(days=3):
                continue
            idx.append(j + delay); side.append(int(-np.sign(zz) * cs))
        if not idx:
            continue
        t = d1.trades(x, pair, np.array(idx), np.array(side), geo)
        if len(t):
            t["day"] = x.day.values[t.sig.values]; t["time"] = t.day; t["pair"] = pair; t["cell"] = cell
            out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def per_summ(t, splits=((None, 2017), (2018, 2021), (2022, None))):
    if len(t) == 0:
        return {"n": 0}
    y = pd.to_datetime(t.day).dt.year
    out = {}
    for a, b in splits:
        m = np.ones(len(t), bool)
        if a: m &= (y >= a).values
        if b: m &= (y <= b).values
        g = t[m]
        s = core.summ(g, boot=True) if len(g) else {"n": 0}
        if len(g):
            mo = max(1.0, (pd.to_datetime(g.day).max() - pd.to_datetime(g.day).min()).days / 30.44)
            s["frq"] = round(g.day.nunique() / mo, 2)
        out[f"{a or ''}-{b or ''}"] = {k: s[k] for k in ("n", "wr", "ort", "P", "yari", "stres15", "frq") if k in s}
    return out


def main():
    Zt = tff()
    res = {}
    for cell in CELLS:
        r = {"ana": per_summ(run(Zt, ek18.CODES, cell)), "a_gecikme1": per_summ(run(Zt, ek18.CODES, cell, delay=1))}
        Zp = price_z(ek18.CODES, Zt)
        r["b_fiyat_kontrol"] = per_summ(run(Zp, ek18.CODES, cell))
        tb = run(Zt, BLIND, cell)
        r["c_gorulmemis"] = per_summ(tb, splits=((None, None),))
        r["c_cift"] = {p: (len(g), round(float((g.net > 0).mean() * 100), 1), round(float(g.net.mean()), 2)) for p, g in tb.groupby("pair")} if len(tb) else {}
        tl = run(legacy(), LEG, cell)
        tl = tl[pd.to_datetime(tl.day) < "2010-01-01"] if len(tl) else tl
        r["d_1993_2009"] = per_summ(tl, splits=((None, 2001), (2002, 2009), (None, 2009)))
        r["d_cift"] = {p: (len(g), round(float((g.net > 0).mean() * 100), 1), round(float(g.net.mean()), 2)) for p, g in tl.groupby("pair")} if len(tl) else {}
        res[cell] = r
        print(cell, json.dumps(r, ensure_ascii=False, default=str), flush=True)
    # (e) sepet: 19 ∪ 39, çift başına tarih sırasıyla tek pozisyon (çakışan sonraki sinyal atlanır)
    T = pd.concat([run(Zt, ek18.CODES, "19"), run(Zt, ek18.CODES, "39")], ignore_index=True).sort_values(["pair", "day"])
    keep = []
    for p, g in T.groupby("pair"):
        busy = pd.Timestamp("1900-01-01")
        for i, r in g.iterrows():
            if pd.Timestamp(r.day) > busy:
                keep.append(i); busy = pd.Timestamp(r.day) + pd.Timedelta(days=int(1.4 * 10) + 2)
    res["e_sepet"] = per_summ(T.loc[keep])
    print("sepet", json.dumps(res["e_sepet"], default=str))
    (core.RES / "ek18b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
