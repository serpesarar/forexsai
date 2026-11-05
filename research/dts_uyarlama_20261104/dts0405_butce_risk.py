"""DTS-04 (sabit $-risk lot) + DTS-05 (risk kuralları) — botun gerçek işlemleri. Ön-kayıt: PROTOCOL.md Ek-2."""
import json
import numpy as np
import pandas as pd

B = 5000
rng = np.random.default_rng(404)


def load():
    d = pd.read_csv("data/bot_trades.csv"); d["open_time"] = pd.to_datetime(d.open_time, utc=True, format="ISO8601"); d["close_time"] = pd.to_datetime(d.close_time, utc=True, format="ISO8601")
    d["dir"] = np.where(d.direction.str.upper().str.startswith("BUY"), 1, -1)
    move = (d.close_price - d.open_price) * d.dir
    d["d_sl"] = (d.open_price - d.sl).abs()
    d["d_tp"] = (d.tp - d.open_price).abs()
    d["pnl"] = d.profit + d.commission.fillna(0) + d.swap.fillna(0)
    ok = (d.d_sl > d.open_price * 0.0002) & (move.abs() > 0) & (d.volume > 0)
    d = d[ok].copy()
    k = (d.profit / ((d.close_price - d.open_price) * d.dir * d.volume)).replace([np.inf, -np.inf], np.nan)
    d["usd_per_pt_lot"] = k.groupby(d.normalized_symbol).transform("median")       # sembol başına sağlam çarpan
    d["risk_usd"] = d.usd_per_pt_lot * d.volume * d.d_sl
    d["R"] = d.pnl / d.risk_usd
    d["day"] = d.close_time.dt.date
    return d.sort_values("open_time").reset_index(drop=True)


def stats(pnl_by_day: pd.Series) -> dict:
    eq = pnl_by_day.cumsum(); dd = float((eq - eq.cummax()).min())
    return {"toplam": float(pnl_by_day.sum()), "gun_sharpe": float(pnl_by_day.mean() / pnl_by_day.std()), "max_dd": dd}


def dts04(d):
    mean_risk = d.risk_usd.mean()
    fixed = d.groupby("day").pnl.sum(); risk = (d.R * mean_risk).groupby(d.day).sum()
    a, b = stats(fixed), stats(risk)
    days = fixed.index.to_numpy(); fx, rk = fixed.to_numpy(), risk.reindex(fixed.index).to_numpy()
    i = rng.integers(0, len(days), size=(B, len(days)))
    sh = lambda x: x.mean(1) / x.std(1)  # noqa: E731
    p = float((sh(rk[i]) > sh(fx[i])).mean())
    return {"islem": len(d), "ort_risk_usd": float(mean_risk), "risk_usd_cv": float(d.risk_usd.std() / mean_risk),
            "sabit_lot": a, "sabit_risk": b, "P_sharpe_iyilesir": p,
            "calisiyor": bool(p >= 0.90 and b["max_dd"] > a["max_dd"])}


def apply_rules(d, max_entries=None, daily_loss=None, min_rr=None):
    keep = np.ones(len(d), bool); cnt, loss = {}, {}
    for i, r in d.iterrows():
        day = r.open_time.date()
        if min_rr is not None and (r.d_tp <= 0 or r.d_tp / r.d_sl < min_rr):
            keep[i] = False; continue
        if max_entries is not None and cnt.get(day, 0) >= max_entries:
            keep[i] = False; continue
        if daily_loss is not None:
            realized = sum(x.pnl for _, x in d[(d.close_time < r.open_time) & (d.open_time.dt.date == day) & keep[: len(d)]].iterrows())
            if realized <= -daily_loss:
                keep[i] = False; continue
        cnt[day] = cnt.get(day, 0) + 1
    return keep


def dts05(d):
    mid = d.close_time.median(); first = (d.close_time < mid).to_numpy()
    lim = 3 * d.risk_usd.mean()
    rules = {"gunde_3_giris": dict(max_entries=3), "gunluk_zarar_3R": dict(daily_loss=lim), "min_rr_1": dict(min_rr=1.0),
             "hepsi": dict(max_entries=3, daily_loss=lim, min_rr=1.0)}
    out = {}
    for name, kw in rules.items():
        k = apply_rules(d, **kw); el = ~k
        res = {"elenen": int(el.sum()), "elenen_ort_usd": float(d.pnl[el].mean()) if el.any() else None,
               "elenen_ort_R": float(d.R[el].mean()) if el.any() else None,
               "kalan_toplam": float(d.pnl[k].sum()), "hepsi_toplam": float(d.pnl.sum())}
        for nm, m in (("y1", first), ("y2", ~first)):
            res[f"{nm}_elenen_ort_usd"] = float(d.pnl[el & m].mean()) if (el & m).any() else None
            res[f"{nm}_kalan_minus_hepsi"] = float(d.pnl[k & m].sum() - d.pnl[m].sum())
        res["calisiyor"] = bool(res["elenen"] > 0 and res["elenen_ort_usd"] < 0 and res["kalan_toplam"] >= res["hepsi_toplam"]
                                and all((res[f"{y}_elenen_ort_usd"] or 0) < 0 and res[f"{y}_kalan_minus_hepsi"] >= 0 for y in ("y1", "y2")))
        out[name] = res
    return out


def main():
    d = load()
    print("işlem:", len(d), "| sembol:", d.normalized_symbol.value_counts().to_dict())
    print("R:R dağılımı (tp/sl):", d.assign(rr=d.d_tp / d.d_sl).rr.describe().round(2).to_dict())
    r4, r5 = dts04(d), dts05(d)
    json.dump({"DTS-04": r4, "DTS-05": r5}, open("dts0405_sonuc.json", "w"), indent=1, default=str)
    print(json.dumps({"DTS-04": r4}, indent=1, default=str))
    for k, v in r5.items():
        print(k, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    main()
