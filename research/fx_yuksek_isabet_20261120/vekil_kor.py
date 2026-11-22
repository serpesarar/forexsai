"""EK-22 (1): USDHKD ile aday vekillerin eş hareketi — günlük/haftalık getiri korelasyonu ve yön uyumu (tanımlayıcı)."""
import json
import numpy as np, pandas as pd
import core

CANDS = ["HK50", "CHINAH", "CN50", "USDX", "EWH.US", "FXI.US", "XAUUSD", "0388.HK", "0005.HK", "USDCNH", "USDSGD", "USDJPY", "EURUSD"]


def d1c(s):
    x = pd.read_csv(core.FX / f"{s}_D1.csv.gz"); x["d"] = pd.to_datetime(x.t, unit="s").dt.normalize()
    return x.set_index("d").c


def main():
    h = d1c("USDHKD")
    rows = []
    for s in CANDS:
        c = d1c(s)
        df = pd.DataFrame({"h": np.log(h), "c": np.log(c)}).dropna()
        df = df[df.index >= "2017-09-01"]
        for nm, k in (("gunluk", 1), ("haftalik", 5), ("aylik", 21)):
            r = df.diff(k).iloc[::k].dropna()
            r = r[(r.h != 0)]
            rho = float(r.h.corr(r.c))
            agree = float((np.sign(r.h) == np.sign(r.c)).mean())
            rows.append({"vekil": s, "olcek": nm, "n": len(r), "rho": round(rho, 3), "ayni_yon": round(agree * 100, 1)})
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(R.pivot(index="vekil", columns="olcek", values=["rho", "ayni_yon"]).to_string())
    R.to_csv(core.RES / "vekil_kor.csv", index=False)


if __name__ == "__main__":
    main()
