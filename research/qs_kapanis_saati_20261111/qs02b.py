"""QS-02 Tur 2 (EK-1): H2a coşku kırılması KISA, H2c korku+aşağı boşluk UZUN, H2f haftalık coşku Pazartesi KISA.
Bağımsız günlük veri: yabancı endeksler + ABD ön-2018 + SPY/IWM 1999-2018."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import binomtest

H = Path(__file__).resolve().parent
FD = H.parent / "geri_cekilme_20261106/data"
ND = H.parent / "ndx_kapi_20261110/data"
OUT = H / "results"
END = "2018-05-01"
FOREIGN = ["AEX", "AXJO", "BSESN", "BVSP", "FCHI", "GSPTSE", "IBEX", "JKSE", "KS11", "MXX", "SSMI", "TWII", "DJI", "RUT", "IXIC"]
RNG = np.random.default_rng(31)


def load_yahoo_csv(name: str) -> pd.DataFrame:
    x = pd.read_csv(FD / f"{name}.csv")
    x.index = pd.to_datetime(x.Date.str[:10]); x = x[x.index < END]
    return x


def clean(x: pd.DataFrame) -> pd.DataFrame:
    """Geçerli açılışlı günler; geçerli oranı < %90 olan yıllar atılır."""
    pc = x.Close.shift(1)
    ok = (x.Open - pc).abs() > 1e-9
    ok &= x.High > x.Low
    yr = ok.groupby(x.index.year).mean()
    good_years = yr[yr >= 0.9].index
    x = x.assign(valid=ok)
    return x[x.index.year.isin(good_years)]


def frame(x: pd.DataFrame, adj: bool = False) -> pd.DataFrame:
    f = (x["Adj Close"] / x.Close) if adj else 1.0
    t = pd.DataFrame({"O": x.Open * f, "C": x["Adj Close"] if adj else x.Close, "hi": x.High * f, "lo": x.Low * f},
                     index=x.index)
    t["valid"] = x["valid"] if "valid" in x else True
    t["C1"] = t.C.shift(1); t["r"] = t.C / t.C1 - 1
    t["k"] = (t.C - t.lo) / (t.hi - t.lo)
    t["r1"] = t.r.shift(1); t["k1"] = t.k.shift(1)
    t["gap"] = t.O / t.C1 - 1
    t["w5"] = t.C1 / t.C.shift(6) - 1
    return t.iloc[10:]


def cells(t: pd.DataFrame, cost: float, e_ret: float = 0.015, g: float = 0.003) -> dict:
    v = t.valid & t.valid.shift(1, fill_value=False)
    E = (t.r1 >= e_ret) & (t.k1 >= 0.75); F = (t.r1 <= -e_ret) & (t.k1 <= 0.25)
    Gm = t.gap <= -g
    oc = (t.C / t.O - 1) * 1e4
    nxt = (t.C.shift(-1) / t.C - 1) * 1e4
    return {"H2a": (-oc - cost)[v & E & Gm], "H2c": (oc - cost)[v & F & Gm],
            "H2f": (-oc - cost)[v & (t.w5 >= 0.03) & (t.index.dayofweek == 0) & Gm],
            "H2a_ertesi": (-nxt - cost)[v & E & Gm], "taban_kisa": (-oc - cost)[v], "taban_uzun": (oc - cost)[v]}


def st(v: pd.Series) -> dict:
    a = v.dropna().to_numpy()
    if len(a) < 2:
        return {"n": int(len(a))}
    p = float((a[RNG.integers(0, len(a), (5000, len(a)))].mean(1) > 0).mean())
    return {"n": int(len(a)), "ort": round(float(a.mean()), 1), "isabet": round(float((a > 0).mean()), 3), "P": round(p, 3)}


def main() -> None:
    res = {"yabanci": {}, "etf": {}, "doz": {}}
    for nm in FOREIGN:
        t = frame(clean(load_yahoo_csv(nm)))
        if len(t) < 500:
            continue
        c = cells(t, 3.0)
        res["yabanci"][nm] = {k: st(v) for k, v in c.items()} | {"donem": f"{t.index[0].year}-{t.index[-1].year}"}
    for nm in ("SPY", "IWM", "QQQ"):
        x = pd.read_parquet(ND / f"{nm}.parquet"); x = x[(x.index >= "1999-03-10") & (x.index < END)]
        x = x.assign(valid=True)
        t = frame(x, adj=True)
        res["etf"][nm] = {k: st(v) for k, v in cells(t, 2.0).items()}
        if nm == "QQQ":
            for er in (0.01, 0.015, 0.02, 0.03):
                for g in (0.003, 0.006):
                    res["doz"][f"QQQ E{er} G{g}"] = st(cells(t, 2.0, er, g)["H2a"])
    hk = {}
    for h in ("H2a", "H2c", "H2f"):
        ms = {m: r[h] for m, r in res["yabanci"].items() if r[h].get("n", 0) >= 10}
        means = [s["ort"] for s in ms.values()]
        pos = sum(1 for x in means if x > 0)
        pool = float(np.mean(means)) if means else np.nan
        sign_p = binomtest(pos, len(means), 0.5, alternative="greater").pvalue if means else 1.0
        c1 = pool > 0 and pos >= 0.6 * len(means) and sign_p <= 0.10
        c2 = all(res["etf"][e][h].get("ort", -1) > 0 for e in ("SPY", "IWM"))
        hk[h] = {"piyasa": len(means), "artı": pos, "havuz_ort": round(pool, 1), "isaret_p": round(float(sign_p), 3),
                 "olc1": bool(c1), "olc2": bool(c2), "sinif": "B-" if c1 and c2 else ("C" if c1 else "X")}
    res["hukum"] = hk
    (OUT / "qs02b.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for h in ("H2a", "H2c", "H2f", "H2a_ertesi", "taban_kisa"):
        print(f"--- {h}")
        for m, r in {**res["yabanci"], **res["etf"]}.items():
            s = r[h]; print(f"  {m:7s} {r.get('donem', 'ETF 99-18'):10s} n {s.get('n', 0):4d}  ort {s.get('ort', float('nan')):7.1f}  isabet {s.get('isabet', float('nan'))}  P {s.get('P', float('nan'))}")
    print("DOZ (QQQ H2a):", json.dumps(res["doz"], ensure_ascii=False))
    print("HÜKÜM:", json.dumps(hk, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
