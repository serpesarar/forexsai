"""QS-04 E4: R1 ABD sinyali yabancı endeksleri ve GER40'ı da taşıyor mu (PROTOCOL_QS04.md §E4)."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest
from r1_dengeleme import px, synth_bond, st, H
from qs04 import monthly, side

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402
FD = H.parent / "geri_cekilme_20261106/data"
CSV = ["AEX", "AXJO", "BSESN", "BVSP", "FCHI", "GSPTSE", "IBEX", "JKSE", "KS11", "MXX", "SSMI", "TWII"]
PQ = ["GDAXI", "STOXX50E", "N225", "FTSE"]
COST = 3.0


def load(nm: str) -> pd.Series:
    if nm in PQ:
        return px(nm, "Close").dropna()
    x = pd.read_csv(FD / f"{nm}.csv"); x.index = pd.to_datetime(x.Date.str[:10])
    c = x.Close; return c[c > 0]


def trades(M: pd.DataFrame, c: pd.Series) -> np.ndarray:
    sd = side(M.dm.to_numpy()); out = []
    idx = c.index
    for k, r in M.iterrows():
        if sd[k] == 0:
            continue
        i = idx.searchsorted(r.d_s, side="right")
        j = idx.searchsorted(r.d_D, side="right") - 1
        if i >= len(idx) or j <= i:
            continue
        out.append(sd[k] * (c.iloc[j] / c.iloc[i] - 1) * 1e4 - COST)
    return np.array(out)


def ger40(M: pd.DataFrame) -> dict:
    mk = Mkt("GER40"); sd = side(M.dm.to_numpy()); out = []
    for k, r in M.iterrows():
        if sd[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
            continue
        i = mk.at(r.d_s + pd.Timedelta(hours=16, minutes=30)); j = mk.at(r.d_D + pd.Timedelta(hours=11, minutes=0))
        if i < 0 or j < 0 or j <= i:
            continue
        c = mk.cost(i)
        out.append(sd[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - c / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j]))
    return st(np.array(out))


def main() -> None:
    M = monthly(px("SPY"), px("TLT"), {"SPY": px("SPY")}); M = M[(M.d_s >= "2002-08-01")].reset_index(drop=True)
    g = px("GSPC", "Close")
    G = monthly(g, synth_bond(px("TNX", "Close")), {"GSPC": g}); G = G[(G.d_s >= "1990-01-01") & (G.d_s < "2002-08-01")].reset_index(drop=True)
    res = {"2002_2026": {}, "1990_2002": {}}
    for nm in CSV + PQ:
        c = load(nm)
        res["2002_2026"][nm] = st(trades(M, c))
        res["1990_2002"][nm] = st(trades(G, c))
    def verdict(block):
        v = {k: x for k, x in block.items() if x.get("n", 0) >= 30}
        means = [x["ort"] for x in v.values()]; pos = sum(m > 0 for m in means)
        return {"piyasa": len(means), "arti": int(pos), "havuz": round(float(np.mean(means)), 1),
                "isaret_p": round(float(binomtest(pos, len(means), .5, alternative="greater").pvalue), 4)}
    res["ozet_2002_2026"] = verdict(res["2002_2026"]); res["ozet_1990_2002"] = verdict(res["1990_2002"])
    res["GER40_broker_2018_26"] = ger40(M)
    o = res["ozet_2002_2026"]
    c1 = o["arti"] >= 0.6 * o["piyasa"] and o["isaret_p"] <= 0.10 and o["havuz"] > 0
    c2 = res["2002_2026"]["GDAXI"].get("ort", -1) > 0 and res["GER40_broker_2018_26"].get("ort", -1) > 0
    res["hukum"] = "B-" if c1 and c2 else ("C+" if c1 else "X")
    (H / "results/qs04_e4.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    for blk in ("2002_2026", "1990_2002"):
        print("==", blk)
        for k, v in res[blk].items():
            print(f"   {k:9s} {v}")
    print(res["ozet_2002_2026"], res["ozet_1990_2002"]); print("GER40", res["GER40_broker_2018_26"]); print("HÜKÜM", res["hukum"])


if __name__ == "__main__":
    main()
