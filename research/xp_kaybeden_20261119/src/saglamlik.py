"""saglamlik.py — EK-1: T_1sa_z kanal uzunluğu/eşik ızgarası, yıl yıl, korelasyon, VIX içi; GBM yıl/piyasa. python saglamlik.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
import ozellik as O  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
M = pd.read_parquet(HERE / "results/ozellikler.parquet")
FEEDS = ["MT5_NAS100", "MT5_US500", "MT5_US30", "MT5_US2000", "DUKA_NDX"]
LENS, QS = (40, 80, 120, 200), (0.1, 0.2, 0.3)


def chan_z(b: pd.DataFrame, dates, n: int) -> pd.Series:
    b = b.assign(t=(b.t // 1800) * 1800)
    x = O.G._local(b, O.NY)
    b = b.assign(day=pd.to_datetime(x.day.values), mn=x.mn.values)
    hb = b.assign(hk=(b.t // 3600) * 3600).groupby("hk").c.last()
    hpos = pd.Series(np.arange(len(hb)), index=hb.index)
    hc = hb.values
    out = {}
    last = b[b.mn == O.LAST_MN].drop_duplicates("day").set_index("day").t
    for d in dates:
        d = pd.Timestamp(d)
        if d not in last.index:
            continue
        hk = (int(last[d]) // 3600) * 3600
        if hk in hpos.index:
            j = int(hpos[hk])
            out[d] = O.linreg(hc[max(0, j - n + 1):j + 1])[2]
    return pd.Series(out)


def veto(z, col, q):
    thr = z[z.donem == "KESIF"][col].quantile(q)
    res = {}
    for era in ("KESIF", "TEST"):
        a = z[z.donem == era]
        m = (a[col] <= thr).values
        net = a.net.values
        res[era] = {"veto_n": int(m.sum()), "veto_ort": round(float(net[m].mean()), 1) if m.any() else None,
                    "kalan_ort": round(float(net[~m].mean()), 1), "kar_x": round(float(net[~m].sum() / net.sum()), 3),
                    "zarar_x": round(float(net[~m][net[~m] < 0].sum() / net[net < 0].sum()), 3)}
    return res


def main():
    bars = {s: O.load_market(s) for s in O.MARKETS}
    bars["DUKA_NDX"] = O.duka_30m()
    for f in FEEDS:
        key = f.replace("MT5_", "")
        dates = M[M.besleme == f].d.tolist()
        for n in LENS:
            z = chan_z(bars[key], dates, n)
            M.loc[M.besleme == f, f"z{n}"] = M.loc[M.besleme == f, "d"].map(z).values
        print(f, "kanallar tamam", flush=True)
    out = {"izgara": {}, "yil": {}, "korelasyon": {}, "vix_ici": {}}
    for n in LENS:
        for q in QS:
            cell = {f: veto(M[M.besleme == f], f"z{n}", q) for f in FEEDS}
            pool = [cell[f]["TEST"] for f in FEEDS[:4]]
            out["izgara"][f"z{n}_q{int(q*100)}"] = {"piyasa": cell,
                "TEST_yon_tutan_4": sum(1 for p in pool if p["veto_ort"] is not None and p["veto_ort"] < p["kalan_ort"]),
                "TEST_kar_x_ort": round(float(np.mean([p["kar_x"] for p in pool])), 3), "TEST_zarar_x_ort": round(float(np.mean([p["zarar_x"] for p in pool])), 3)}
    # yıl yıl (z80, q20, piyasa içi KEŞİF eşiği)
    rows = []
    for f in FEEDS:
        z = M[M.besleme == f].copy()
        thr = z[z.donem == "KESIF"].z80.quantile(0.2)
        z["veto"] = z.z80 <= thr
        z["yil"] = pd.to_datetime(z.d).dt.year
        for y, g in z.groupby("yil"):
            rows.append({"besleme": f, "yil": int(y), "n": len(g), "veto_n": int(g.veto.sum()), "veto_ort": round(float(g[g.veto].net.mean()), 1) if g.veto.any() else None,
                         "kalan_ort": round(float(g[~g.veto].net.mean()), 1)})
    out["yil"] = rows
    P = M[M.besleme.isin(FEEDS[:4])]
    out["korelasyon"] = P[["z80", "T_1sa_z", "vix", "m30_atr_bp", "h1_rsi14", "son_saat", "twap_uz", "gun_ret", "r5", "D_ret3"]].corr(method="spearman")["z80"].round(3).to_dict()
    # VIX üçte birlikleri içinde z80 alt %20'si (piyasa içi KEŞİF eşiği) vs geri kalanı — TEST
    rows = []
    for f in FEEDS[:4]:
        z = M[M.besleme == f].copy()
        z["veto"] = z.z80 <= z[z.donem == "KESIF"].z80.quantile(0.2)
        z["vt"] = pd.qcut(z.vix.rank(method="first"), 3, labels=["düşük", "orta", "yüksek"])
        rows.append(z)
    Z = pd.concat(rows)
    for era in ("KESIF", "TEST"):
        for vt, g in Z[Z.donem == era].groupby("vt"):
            out["vix_ici"][f"{era}_{vt}"] = {"veto_n": int(g.veto.sum()), "veto_ort": round(float(g[g.veto].net.mean()), 1) if g.veto.any() else None,
                                            "kalan_ort": round(float(g[~g.veto].net.mean()), 1)}
    (HERE / "results/saglamlik.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    M.to_parquet(HERE / "results/ozellikler_kanal.parquet")
    for k, v in out["izgara"].items():
        print(k, "TEST yön", v["TEST_yon_tutan_4"], "/4 kâr×", v["TEST_kar_x_ort"], "zarar×", v["TEST_zarar_x_ort"], "| Duka TEST", v["piyasa"]["DUKA_NDX"]["TEST"])
    print("korelasyon", out["korelasyon"])
    for k, v in out["vix_ici"].items():
        print(k, v)


if __name__ == "__main__":
    main()
