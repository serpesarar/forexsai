"""HK3 (EK-8) yeniden üretim: USDHKD H1 kapanış ≤ 7,7520 → AL, SL 7,7470, TP +20 pip, en çok 1.500 H1 bar; tek pozisyon."""
import numpy as np, pandas as pd
import band, core

TRIG, SL_LVL, TP_PIP, PIP, HOLD = 7.7520, 7.7470, 20, 0.0001, 1500


def trades() -> pd.DataFrame:
    x = band.load_h1("USDHKD")
    c = x.c.values
    t = band.run_rule("USDHKD", x, c <= TRIG, 1, np.full(len(x), TP_PIP * PIP), np.maximum(c - SL_LVL, 5 * PIP), HOLD)
    t["gun"] = (pd.to_datetime(x.srv.values[t.xi.values]) - pd.to_datetime(x.srv.values[t.ei.values])).total_seconds() / 86400
    return t


if __name__ == "__main__":
    t = trades()
    t["ay"] = pd.to_datetime(t.time).dt.to_period("M")
    months = pd.period_range(pd.to_datetime(t.time).min().to_period("M"), "2026-11", freq="M")
    per_m = t.groupby("ay").size().reindex(months, fill_value=0)
    print("işlem", len(t), "| isabet %", round((t.net > 0).mean() * 100, 1), "| ort net bp", round(t.net.mean(), 2),
          "| TP oranı %", round((t.why == 1).mean() * 100, 1), "| en kötü bp", round(t.net.min(), 1))
    print("ay sayısı", len(months), "| ort işlem/ay", round(len(t) / len(months), 2), "| işlem olan ay", int((per_m > 0).sum()),
          "| işlem olan ayda ort", round(per_m[per_m > 0].mean(), 1))
    print("tutuş günü medyan / ort / p90", round(t.gun.median(), 1), round(t.gun.mean(), 1), round(t.gun.quantile(.9), 1))
    print(t.groupby(pd.to_datetime(t.time).dt.year).agg(n=("net", "size"), isabet=("net", lambda v: round((v > 0).mean() * 100)), ort=("net", lambda v: round(v.mean(), 1))).T.to_string())
