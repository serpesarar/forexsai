"""oynat.py — canlı KSG (ksg_live.find_signal + 09:30 çıkışı + VIX ≥ 25 çift lot) MT5 NAS100 ve Duka NDX'te birebir; korku_live.opex_veto ile
vetolu / vetosuz kitap. python oynat.py"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RES = HERE / "results"
sys.path.insert(0, str(ROOT / "research/korku_evren_20261119/src"))
sys.path.insert(0, str(ROOT / "yeni deneme"))
import esik as E  # noqa: E402
import ksg_live as ks  # noqa: E402
import korku_live as kl  # noqa: E402
import caprev_shadow as cs  # noqa: E402

RNG = np.random.default_rng(31)
SPLIT = pd.Timestamp("2022-07-01")


def holidays() -> set:
    d0, d1 = date(2018, 1, 1), E.CUT.date()
    return {d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)
            if (d0 + timedelta(days=i)).weekday() < 5 and not E.VR.G.nyse_ok(d0 + timedelta(days=i))}


def bars30(name: str) -> pd.DataFrame:
    b, st = E.feeds()[name]
    if st == 60:
        g = b.assign(k=(b.t // 1800) * 1800).groupby("k")
        b = pd.DataFrame({"t": g.t.first().index.values, "o": g.o.first().values, "c": g.c.last().values, "sp": g.sp.first().values})
    b = b[b.t < E.VR.ts(E.CUT + timedelta(days=1), 0, 0)]
    return b[["t", "o", "c", "sp"]].reset_index(drop=True)


def vix_prev() -> pd.Series:
    v = pd.read_parquet(ROOT / "research/qs03_akis_takvim_20261111/data/VIX.parquet")
    if isinstance(v.columns, pd.MultiIndex):
        v.columns = v.columns.get_level_values(0)
    v.index = pd.to_datetime(v.index).tz_localize(None).normalize()
    return v.Close


def nights(name: str) -> pd.DataFrame:
    b = bars30(name)
    loc = [cs.to_local(int(t), "US") for t in b.t]
    b["day"], b["mn"] = [x[0] for x in loc], [x[1] for x in loc]
    vc = vix_prev()
    by_day = {d: g for d, g in b.groupby("day")}
    days = sorted(d for d in by_day if kl.is_trading_day(d))
    rows = []
    for i, d in enumerate(days[:-1]):
        g = by_day[d]
        recs = [{"t": int(t), "open": float(o), "high": float(o), "low": float(o), "close": float(c)} for t, o, c in zip(g.t, g.o, g.c)]
        sig = ks.find_signal(recs, d)
        if sig is None:
            continue
        r16 = g[g.mn == 960].iloc[0]
        nd = days[i + 1]
        x = by_day[nd]
        x930 = x[x.mn == 570]
        if x930.empty:
            continue
        ask = r16.o + r16.sp
        px = float(x930.o.iloc[0])
        net = (px / ask - 1) * 1e4 - E.VR.FIN * (nd - d).days
        vp = vc[vc.index < pd.Timestamp(d)]
        vprev = float(vp.iloc[-1]) if len(vp) else None
        rows.append({"d": pd.Timestamp(d), "net": net, "lot": ks.entry_lot(1.0, vprev), "vix_prev": vprev,
                     "veto": kl.opex_veto(d), "vadeye": kl.days_to_opex(d)})
    return pd.DataFrame(rows)


def boot_p_neg(v: np.ndarray, d: np.ndarray) -> float:
    m = pd.to_datetime(d).to_period("M").astype(str)
    ub = np.unique(m)
    return float(np.mean([np.concatenate([v[m == u] for u in RNG.choice(ub, len(ub))]).mean() < 0 for _ in range(2000)]))


def book(x: pd.DataFrame) -> dict:
    days = pd.bdate_range(x.d.min(), E.CUT)
    s = (x.net * x.lot).groupby(x.d).sum().reindex(days).fillna(0)
    c = s.cumsum()
    yrs = len(days) / 252
    return {"gece_yilda": round(len(x) / yrs, 1), "toplam_bp_yil": round(float(s.sum() / yrs), 0),
            "sharpe": round(float(s.mean() / s.std() * np.sqrt(252)), 3), "maxDD_bp": round(float((c - c.cummax()).min()), 0)}


def main() -> None:
    kl.ay.NYSE_HOLIDAYS = set(kl.ay.NYSE_HOLIDAYS) | holidays()
    res = {}
    for name in ("MT5_NAS100", "DUKA_NDX"):
        x = nights(name)
        v = x[x.veto]
        w = (v.net * v.lot)
        halves = {h: round(float((z.net * z.lot).sum() / z.lot.sum()), 1) if len(z) else None
                  for h, z in (("ilk", v[v.d < SPLIT]), ("ikinci", v[v.d >= SPLIT]))}
        r = {"gece": len(x), "ort_tum": round(float(x.net.mean()), 1), "vetolanan_n": len(v),
             "vetolanan_lot_agirlikli_ort": round(float(w.sum() / v.lot.sum()), 1), "vetolanan_ham_ort": round(float(v.net.mean()), 1),
             "kalan_ort": round(float(x[~x.veto].net.mean()), 1), "P_vetolanan_eksi": round(boot_p_neg(v.net.values, v.d.values), 3),
             "yarilar": halves, "vadeye_gun": {int(k): round(float(g.net.mean()), 1) for k, g in x[x.vadeye <= 4].groupby("vadeye")},
             "dozlu_vetolanan": {"n": int((v.lot > 1).sum()), "ort": round(float(v[v.lot > 1].net.mean()), 1) if (v.lot > 1).any() else None},
             "yillar_vetolanan": {int(y): round(float(g.net.mean()), 1) for y, g in v.groupby(v.d.dt.year)},
             "kitap_vetosuz": book(x), "kitap_vetolu": book(x[~x.veto])}
        a, b = r["kitap_vetosuz"], r["kitap_vetolu"]
        r["olcut"] = {"vetolanan_eksi": r["vetolanan_lot_agirlikli_ort"] < 0,
                      "yarilar": (min(halves["ilk"], halves["ikinci"]) < 0 and max(halves["ilk"], halves["ikinci"]) <= 3),
                      "sharpe_dusmuyor": b["sharpe"] >= a["sharpe"], "toplam_bp_artar_ya_da_esit": b["toplam_bp_yil"] >= a["toplam_bp_yil"]}
        res[name] = r
        x.to_csv(RES / f"ksg_geceler_{name}.csv", index=False)
        print(name, json.dumps({k: r[k] for k in r if k not in ("yillar_vetolanan",)}, ensure_ascii=False), "\n   yıllar:", r["yillar_vetolanan"], flush=True)
    ok = all(all(v["olcut"].values()) for v in res.values())
    res["hukum"] = "BAĞLAMA ÖNERİLİR" if ok else "bağlanmaz / koşullu (ölçüt tutmadı)"
    print("HÜKÜM:", res["hukum"])
    (RES / "oynat.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
