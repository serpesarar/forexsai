"""ek1.py — PROTOCOL EK-1: ayrıştırma, canlı kurallarla örtüşme, E116 karşı kolu, kuyruk. python ek1.py"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import cr_motor as M
from cr_analiz import FEEDS, load, sharpe

R = M.ROOT / "research"


def live_days() -> dict[str, set]:
    a = pd.read_parquet(R / "ndx_10y_1m_20261116/results/a_trades.parquet")
    k = pd.read_csv(R / "korku_evren_20261119/results/t30_islemler_DUKA_NDX.csv", parse_dates=["d"])
    out = {r: set(pd.to_datetime(a[a.rule == r].d).dt.date) for r in ("C3B", "KSG")}
    out["KORKU_T30"] = set(k.d.dt.date)
    return out


def maxdd(d: pd.Series, v: pd.Series) -> float:
    s = v.groupby(d.values).sum().sort_index().cumsum()
    return round(float((s - s.cummax()).min()), 1)


def decomp(K: dict) -> dict:
    out = {}
    for f in FEEDS:
        x = K[f]
        out[f] = {"n": len(x), "stop_kaldir_D0": round(float((x["S_None"] - x.base).mean()), 1),
                  "gece_parcasi": round(float((x["H_D1c_ns"] - x["S_None"]).mean()), 1),
                  "toplam": round(float((x["H_D1c_ns"] - x.base).mean()), 1),
                  "S_yok_sharpe": [sharpe(x.d, x.base), sharpe(x.d, x["S_None"])]}
    return out


def overlap(K: dict) -> dict:
    L = live_days()
    x = K["DUKA_NDX"].copy()
    x["gece"] = x["H_D1c_ns"] - x["S_None"]
    dd = x.d.dt.date
    out = {}
    for r, s in L.items():
        m = dd.isin(s)
        out[r] = {"ortusen": [int(m.sum()), round(float(x[m].gece.mean()), 1) if m.any() else None],
                  "ortusmeyen": [int((~m).sum()), round(float(x[~m].gece.mean()), 1)]}
    anym = dd.isin(set().union(*L.values()))
    out["herhangi"] = {"ortusen": [int(anym.sum()), round(float(x[anym].gece.mean()), 1)],
                       "ortusmeyen": [int((~anym).sum()), round(float(x[~anym].gece.mean()), 1) if (~anym).any() else None]}
    return out


def counter_arm(name: str) -> dict:
    F = M.Feed(name)
    D = F.D
    days = list(D.index)
    cl, lo = D.close.values, D.low.values
    ev = {e["d"] for e in F.events()}
    rows = []
    for k in range(22, len(days) - 1):
        d, nd = days[k], days[k + 1]
        if d.weekday() > 3 or (nd - d).days > 4:
            continue
        c = cl[:k]
        rets = c[1:] / c[:-1] - 1
        r1, r5 = rets[-1], c[-1] / c[-6] - 1
        v = M.vix_prev(d)
        st = v is not None and v >= M.VIX_MIN and (r1 <= M.STRESS_R1 or r5 <= M.STRESS_R5)
        g = (cl[k + 1] / cl[k] - 1) * 1e4 - M.FIN * (nd - d).days
        rows.append({"d": d, "stres": st, "caprev": d in ev, "kirdi": lo[k] < lo[k - 1], "gece": g})
    z = pd.DataFrame(rows)

    def s(m):
        return [int(m.sum()), round(float(z[m].gece.mean()), 1)]
    return {"caprev_gunu": s(z.caprev), "stres_tetiksiz": s(z.stres & ~z.caprev),
            "stres_dip_kirdi_tetiksiz": s(z.stres & ~z.caprev & z.kirdi), "stressiz": s(~z.stres), "tum": s(z.gece.notna())}


def tails(K: dict) -> dict:
    out = {}
    for f in ("DUKA_NDX", "MT5_NAS100", "DUKA_DAX", "U_NDX_GUNLUK"):
        x = K[f]
        o = {}
        for c in ("base", "S_None", "H_D1c_ns"):
            v = x[c]
            o[c] = {"ort": round(float(v.mean()), 1), "en_kotu5": [round(float(a), 0) for a in np.sort(v)[:5]],
                    "maksDD": maxdd(x.d, v), "sharpe": sharpe(x.d, v)}
        dif = (x["H_D1c_ns"] - x.base).sort_values()
        o["fark_en_iyi5_haric"] = round(float(dif.iloc[:-5].mean()), 1)
        o["fark_yillar"] = {int(y): round(float(g.mean()), 1) for y, g in (x["H_D1c_ns"] - x.base).groupby(x.d.dt.year)}
        out[f] = o
    return out


def main() -> None:
    K = load()
    res = {"ayristirma": decomp(K), "ortusme": overlap(K),
           "karsi_kol": {f: counter_arm(f) for f in ("DUKA_NDX", "MT5_NAS100", "DUKA_DAX")}, "kuyruk": tails(K)}
    for k, v in res.items():
        print(k, json.dumps(v, ensure_ascii=False, default=str), flush=True)
    (M.HERE / "results/ek1.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
