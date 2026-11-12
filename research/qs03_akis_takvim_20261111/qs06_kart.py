"""QS-06 kart: 'son seans' (GÜN+0) — ayın son işlem günü 09:30→16:00, R1 yönünde (Δ D−3'te bilinir).
Hacim/beklenti/kararlılık: QQQ+SPY 2002-26 (ay = işlem); sürtünme: broker NAS100+US500 ×1,5; icra: Dukascopy 1m 09:30 vs 09:31 + spread."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import monthly, side, COST
from qs06_harita import adj_oc

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt  # noqa: E402


def main():
    spy, tlt = px("SPY"), px("TLT")
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    s = side(M.dm.to_numpy())
    O = {n: adj_oc(n)[0] for n in ("QQQ", "SPY")}; C = {n: adj_oc(n)[1] for n in ("QQQ", "SPY")}
    v = []
    for i, r in M.iterrows():
        if s[i] == 0:
            continue
        g = [(C[n].loc[r.d_D] / O[n].loc[r.d_D] - 1) * 1e4 for n in ("QQQ", "SPY")]
        v.append(s[i] * np.mean(g) - COST)
    v = np.array(v); h = len(v) // 2
    br, brs = {}, {}
    for sym in ("NAS100", "US500"):
        for stress, store in ((1.0, br), (1.5, brs)):
            mk = Mkt(sym, stress=stress); o = []
            for i, r in M.iterrows():
                if s[i] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
                    continue
                a, b = mk.at(r.d_D + pd.Timedelta(minutes=570)), mk.at(r.d_D + pd.Timedelta(minutes=960))
                if a < 0 or b < 0:
                    continue
                o.append(s[i] * (mk.o[b] - mk.o[a]) / mk.o[a] * 1e4 - mk.cost(a) / mk.o[a] * 1e4)
            store[sym] = np.array(o)
    p_ = pd.read_parquet(H.parent / "geri_cekilme_limit_20261109/data/path.parquet")
    et = pd.to_datetime(p_.t, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    so = pd.Series(p_.open.values, index=et); sp = pd.Series(p_.spr.values, index=et)
    opt, real = [], []
    for i, r in M.iterrows():
        if s[i] == 0:
            continue
        t0, t1, t2 = (r.d_D + pd.Timedelta(minutes=m) for m in (570, 571, 960))
        if t0 in so.index and t1 in so.index and t2 in so.index:
            opt.append(s[i] * (so[t2] - so[t0]) / so[t0] * 1e4)
            real.append(s[i] * (so[t2] - so[t1]) / so[t1] * 1e4 - sp[t1] / so[t1] * 1e4)
    opt, real = np.array(opt), np.array(real)
    allb = np.concatenate(list(br.values())); alls = np.concatenate(list(brs.values()))
    card = {"1_hacim": {"n_ETF_ay": int(len(v)), "n_broker": int(len(allb)), "gecti": bool(len(v) >= 150)},
            "2_beklenti": st(v) | {"gecti": bool(v.mean() > 0 and st(v)["P"] >= .9)},
            "3_kararlilik": {"yari1": round(float(v[:h].mean()), 1), "yari2": round(float(v[h:].mean()), 1), "gecti": bool(min(v[:h].mean(), v[h:].mean()) >= 0)},
            "4_surtunme": {"broker_x1.5": st(alls), "gecti": bool(alls.mean() > 0)},
            "5_icra": {"iyimser_0930_spreadsiz": round(float(opt.mean()), 1), "gercek_0931_spread": round(float(real.mean()), 1), "n": int(len(real)),
                       "gecti": bool(real.mean() > 0 and opt.mean() - real.mean() <= 0.5 * abs(opt.mean()))},
            "6_tek_pozisyon": {"not": "ayda bir seans", "gecti": True},
            "broker": {k: st(x) for k, x in br.items()}}
    n = sum(card[k]["gecti"] for k in card if k[0].isdigit())
    card["gecen"] = f"{n}/6"; card["verdikt"] = "LIVE adayı (önce GÖLGE, karar kullanıcıda)" if n == 6 else ("SHADOW" if n >= 4 else "RED")
    gl = H.parent.parent / "backend/data/evolution/go_live_cards/qs06_son_seans.json"
    gl.write_text(json.dumps({"scope": "qs06_son_seans", "tarih": "2026-11-11",
                              "kural": "Ayın son işlem günü 09:30→16:00 ET; D−3 kapanışında SPY−TLT ay içi ≥ +%2 → KISA, ≤ −%2 → UZUN", **card},
                             indent=1, ensure_ascii=False, default=str))
    (H / "results/qs06_kart.json").write_text(json.dumps(card, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(card, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
