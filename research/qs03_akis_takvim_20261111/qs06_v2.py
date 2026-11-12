"""QS-06 sonradan birleştirme (karar ölçütü değil; seçilen hücreler zaten ön-kayıtlı A1'de karar aldı):
döngü v2 = GÜN+0 (D 09:30→16:00, s yönünde) + GECE+1 (D 16:00 → D+1 09:30, −s yönünde) [+ E2 uzun D+1 09:30 → D+3 16:00].
Kıyas: R1 (D−3→D) ve QS-04 döngüsü. Ayrıca bacaklar, KSG çakışması (D'nin 15:00→16:00 aşağı mı), kart."""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import monthly, side, TH, COST
from qs06_harita import adj_oc

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402


def sharpe(v):
    v = np.asarray(v, float); s = v.std(ddof=1)
    return round(float(v.mean() / s * np.sqrt(12)), 2) if s > 0 else None


def etf_legs(names):
    spy, tlt = px("SPY"), px("TLT")
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    s = side(M.dm.to_numpy()); sE2 = M.dD.to_numpy() >= TH
    O = {n: adj_oc(n)[0] for n in names}; C = {n: adj_oc(n)[1] for n in names}
    rows = []
    for i, r in M.iterrows():
        # her fon kendi tarih dizisinde konumlanır (SPY 1993, QQQ 1999'da başlar)
        pos = {n: C[n].index.get_loc(r.d_D) for n in names}
        if any(pos[n] + 3 >= len(C[n].index) for n in names):
            continue
        g = lambda f: float(np.mean([f(O[n], C[n], pos[n]) for n in names]))
        gun0 = g(lambda o, c, p: (c.iloc[p] / o.iloc[p] - 1) * 1e4)
        gece1 = g(lambda o, c, p: (o.iloc[p + 1] / c.iloc[p] - 1) * 1e4)
        r1 = g(lambda o, c, p: (c.iloc[p] / c.iloc[p - 3] - 1) * 1e4)
        e2 = g(lambda o, c, p: (c.iloc[p + 3] / c.iloc[p] - 1) * 1e4)
        e2b = g(lambda o, c, p: (c.iloc[p + 3] / o.iloc[p + 1] - 1) * 1e4)
        rows.append(dict(m=r.m, d=r.d_D, s=s[i], e2=bool(sE2[i]), gun0=gun0, gece1=gece1, r1=r1, e2r=e2, e2b=e2b))
    return pd.DataFrame(rows)


def main():
    out = {}
    L = etf_legs(["QQQ", "SPY"])
    a = L.s != 0
    pnl = pd.DataFrame(index=L.index)
    pnl["R1"] = np.where(a, L.s * L.r1 - COST, 0)
    pnl["GUN0"] = np.where(a, L.s * L.gun0 - COST, 0)
    pnl["GECE1"] = np.where(a, -L.s * L.gece1 - COST, 0)
    pnl["E2u"] = np.where(L.e2, L.e2r - COST, 0)
    pnl["E2u_sabah"] = np.where(L.e2, L.e2b - COST, 0)          # D+1 açılış → D+3
    pnl["dongu_QS04"] = pnl.R1 + pnl.E2u
    pnl["v2_GUN0+GECE1"] = pnl.GUN0 + pnl.GECE1
    pnl["v2+E2u_sabah"] = pnl.GUN0 + pnl.GECE1 + pnl.E2u_sabah
    yrs = L.d.dt.year.to_numpy()
    for per, a_, b_ in (("2002_13", "2002-08-01", "2014-01-01"), ("2014_26", "2014-01-01", "2026-11-01"), ("tum", "2002-08-01", "2026-11-01")):
        mk = (L.d >= a_) & (L.d < b_)
        out[per] = {c: {"aylik_ort": round(float(pnl[c][mk].mean()), 1), "SR": sharpe(pnl[c][mk]), "en_kotu_ay": round(float(pnl[c][mk].min()), 0),
                        "yil_arti": f"{sum(pnl[c][mk & (yrs == y)].sum() > 0 for y in np.unique(yrs[mk]))}/{len(np.unique(yrs[mk]))}"}
                    for c in pnl.columns}
    # bacaklar GECE1: s=+1 (fonlar alıyordu → gece KISA) / s=−1 (satıyordu → gece UZUN)
    out["GECE1_bacak"] = {"s=-1 (gece UZUN)": st((-L.s * L.gece1 - COST)[L.s == -1].to_numpy()),
                          "s=+1 (gece KISA)": st((-L.s * L.gece1 - COST)[L.s == 1].to_numpy())}
    out["GUN0_bacak"] = {"s=+1 (UZUN)": st((L.s * L.gun0 - COST)[L.s == 1].to_numpy()), "s=-1 (KISA)": st((L.s * L.gun0 - COST)[L.s == -1].to_numpy())}
    # broker v2 + KSG çakışması
    spy, tlt = px("SPY"), px("TLT")
    M = monthly(spy, tlt, {"_": spy}); M = M[M.d_s >= "2018-06-01"].reset_index(drop=True)
    cal = spy.dropna().index.intersection(tlt.dropna().index); s = side(M.dm.to_numpy())
    br = {}
    for sym in ("NAS100", "US500"):
        mk = Mkt(sym); rows = []
        for i, r in M.iterrows():
            if s[i] == 0:
                continue
            p = cal.get_loc(r.d_D)
            if p + 1 >= len(cal):
                continue
            t = lambda d, m: mk.at(d + pd.Timedelta(minutes=m))
            i0, i15, i1, i2 = t(cal[p], 570), t(cal[p], 900), t(cal[p], 960), t(cal[p + 1], 570)
            if min(i0, i15, i1, i2) < 0:
                continue
            c0, c1 = mk.cost(i0) / mk.o[i0] * 1e4, mk.cost(i1) / mk.o[i1] * 1e4
            g0 = s[i] * (mk.o[i1] - mk.o[i0]) / mk.o[i0] * 1e4 - c0
            g1 = -s[i] * (mk.o[i2] - mk.o[i1]) / mk.o[i1] * 1e4 - c1 - SWAP_BP * mk.swaps(mk.et[i1], mk.et[i2])
            ksg = mk.o[i1] < mk.o[i15]   # 15:00→16:00 aşağı → KSG gece UZUN tetikler
            rows.append(dict(m=r.m, s=s[i], gun0=g0, gece1=g1, ksg=ksg))
        R = pd.DataFrame(rows)
        R["v2"] = R.gun0 + R.gece1
        br[sym] = {"GUN0": st(R.gun0.to_numpy()), "GECE1": st(R.gece1.to_numpy()), "v2": st(R.v2.to_numpy()), "v2_SR_islem_ayi": sharpe(R.v2),
                   "GECE1_KSG_ayni_yon_oran": round(float(((R.s == -1) & R.ksg).mean()), 3),
                   "GECE1_KSG_ile_cakisan": st(R.gece1[(R.s == -1) & R.ksg].to_numpy()),
                   "GECE1_KSG_disi": st(R.gece1[~((R.s == -1) & R.ksg)].to_numpy())}
    out["broker_2018_26"] = br
    (H / "results/qs06_v2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for per in ("2002_13", "2014_26", "tum"):
        print("==", per)
        for c, v in out[per].items():
            print(f"   {c:16s} {v}")
    print("GECE1 bacak", out["GECE1_bacak"]); print("GUN0 bacak", out["GUN0_bacak"])
    for sym, v in br.items():
        print("==", sym)
        for k, x in v.items():
            print("   ", k, x)


if __name__ == "__main__":
    main()
