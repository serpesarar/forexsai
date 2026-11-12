"""QS-04 sonradan teşhis + birleşik 'ay sonu döngüsü' (karar ölçütü değil; PROTOCOL_QS04 betimsel bölümü):
T1 E2 uzun bacağı: hisse-yalnız vs tahvil-yalnız ayrıştırma (akış mı, momentum mu?)
T2 broker NAS100/GER40 2018-26: R1 ve E2-uzun gün gün dağılım (E5 anatomi)
T3 birleşik döngü: R1 (iki bacak) + E2 uzun; R1-uzun + E2-uzun; aylık Sharpe, yıl, en kötü ay — QQQ 2002-26 ve broker NAS100
T4 GDAXI yıl kırılımı (GER40 zayıflığı dönem mi?)"""
from __future__ import annotations
import json, sys
import numpy as np, pandas as pd
from r1_dengeleme import px, st, H
from qs04 import monthly, side, TH, COST

sys.path.insert(0, str(H.parent / "kazanan_turev_20261111"))
from ortak import Mkt, SWAP_BP  # noqa: E402


def mtd_parts(eq, bond, cal_ref):
    cal = eq.dropna().index.intersection(bond.dropna().index)
    e, b = eq.reindex(cal).to_numpy(), bond.reindex(cal).to_numpy()
    last = pd.Series(np.arange(len(cal)), index=cal).groupby(cal.to_period("M")).max().to_numpy()
    rows = []
    for k in range(1, len(last)):
        Dp, p0 = last[k], last[k - 1]
        rows.append(dict(d_D=cal[Dp], eqD=e[Dp] / e[p0] - 1, bdD=b[Dp] / b[p0] - 1))
    return pd.DataFrame(rows).set_index("d_D")


def sharpe(v):
    v = np.asarray(v, float); return round(float(v.mean() / v.std(ddof=1) * np.sqrt(12)), 2) if v.std() > 0 else None


def broker_leg(sym, M, entry_col, exit_fn, sd, hh=16, mm=30, start="2018-06-01"):
    mk = Mkt(sym); out = {}
    for k, r in M.iterrows():
        if sd[k] == 0 or r.d_s < pd.Timestamp(start):
            continue
        t0 = r[entry_col] + pd.Timedelta(hours=hh, minutes=mm); t1 = exit_fn(r) + pd.Timedelta(hours=hh, minutes=mm)
        i, j = mk.at(t0), mk.at(t1)
        if i < 0 or j < 0 or j <= i:
            continue
        out[r.m] = sd[k] * (mk.o[j] - mk.o[i]) / mk.o[i] * 1e4 - mk.cost(i) / mk.o[i] * 1e4 - SWAP_BP * mk.swaps(mk.et[i], mk.et[j])
    return pd.Series(out, dtype=float)


def main():
    res = {}
    spy, tlt, qqq = px("SPY"), px("TLT"), px("QQQ")
    M = monthly(spy, tlt, {"QQQ": qqq}); M = M[M.d_s >= "2002-08-01"].reset_index(drop=True)
    cal = spy.dropna().index.intersection(tlt.dropna().index)
    M["d_D3"] = [cal[cal.get_loc(d) + 3] for d in M.d_D]
    parts = mtd_parts(spy, tlt, cal).reindex(M.d_D)
    M["eqD"], M["bdD"] = parts.eqD.values, parts.bdD.values
    # T1
    t1 = {}
    for per, a, b in (("KESIF", "2002-08-01", "2013-12-31"), ("TEST", "2014-01-01", "2026-10-31")):
        m = M[(M.d_s >= a) & (M.d_s <= b)]
        base = m.n_QQQ - COST
        def leg(mask): return st((m.n_QQQ[mask] - COST).to_numpy()) | {"fark_taban": round(float((m.n_QQQ[mask] - COST).mean() - base.mean()), 1)}
        t1[per] = {"E2_uzun(Δ≥2%)": leg(m.dD >= TH), "yalniz_hisse(SPY ay ≥ +2%)": leg(m.eqD >= TH),
                   "yalniz_tahvil(TLT ay ≤ −2%)": leg(m.bdD <= -TH), "hisse↑∧tahvil yatay(|TLT|<1%)": leg((m.eqD >= TH) & (m.bdD.abs() < 0.01)),
                   "tahvil↓∧hisse yatay(|SPY|<1%)": leg((m.bdD <= -TH) & (m.eqD.abs() < 0.01)), "taban": round(float(base.mean()), 1)}
    res["T1_E2_ayristirma"] = t1
    # T3 birleşik (QQQ)
    sR1 = side(M.dm.to_numpy()); sE2 = np.where(M.dD.to_numpy() >= TH, 1, 0)
    r1 = np.where(sR1 != 0, sR1 * M.w_QQQ - COST, 0.0); r1u = np.where(sR1 == 1, M.w_QQQ - COST, 0.0)
    e2 = np.where(sE2 == 1, M.n_QQQ - COST, 0.0)
    combos = {"R1": r1, "R1_uzun": r1u, "E2_uzun": e2, "R1+E2_uzun": r1 + e2, "R1_uzun+E2_uzun": r1u + e2}
    yrs = M.d_s.dt.year.to_numpy()
    res["T3_QQQ_2002_26"] = {k: {"aylik_ort": round(float(v.mean()), 1), "SR_aylik": sharpe(v), "toplam_bp": round(float(v.sum()), 0),
                                 "islem_ay": int((v != 0).sum()), "en_kotu_ay": round(float(v.min()), 0),
                                 "yil_arti": f"{sum(1 for y in np.unique(yrs) if v[yrs == y].sum() > 0)}/{len(np.unique(yrs))}"}
                             for k, v in combos.items()}
    # T2 broker
    br = {}
    for sym in ("NAS100", "GER40"):
        hh, mm = (16, 30)
        R1b = broker_leg(sym, M, "d_s", lambda r: r.d_D, sR1, hh, mm if sym == "NAS100" else 30)
        E2b = broker_leg(sym, M, "d_D", lambda r: r.d_D3, sE2, hh, mm)
        R1u = R1b[R1b.index.isin(M.m[sR1 == 1])]
        br[sym] = {"R1": st(R1b.to_numpy()), "R1_uzun": st(R1u.to_numpy()), "R1_kisa": st(R1b[R1b.index.isin(M.m[sR1 == -1])].to_numpy()),
                   "E2_uzun": st(E2b.to_numpy())}
        allm = pd.Series(0.0, index=M.m[M.d_s >= "2018-06-01"])
        for lab, parts_ in (("R1+E2_uzun", [R1b, E2b]), ("R1_uzun+E2_uzun", [R1u, E2b]), ("R1", [R1b])):
            v = allm.copy()
            for p in parts_:
                v = v.add(p, fill_value=0)
            br[sym][f"aylik_{lab}"] = {"ort": round(float(v.mean()), 1), "SR": sharpe(v.to_numpy()), "toplam": round(float(v.sum()), 0)}
        # gün gün (NAS100): R1 penceresi D−3→D−2→D−1→D ve E2 D→D+1→D+2→D+3, işaretli
        if sym == "NAS100":
            mk = Mkt(sym); days = {}
            for lab, col, sgn in (("R1", "d_s", sR1), ("E2", "d_D", sE2)):
                seg = [[], [], []]
                for k, r in M.iterrows():
                    if sgn[k] == 0 or r.d_s < pd.Timestamp("2018-06-01"):
                        continue
                    p = cal.get_loc(r[col])
                    ts = [cal[p + q] + pd.Timedelta(hours=16) for q in range(4)]
                    ix = [mk.at(t) for t in ts]
                    if min(ix) < 0:
                        continue
                    for q in range(3):
                        seg[q].append(sgn[k] * (mk.o[ix[q + 1]] / mk.o[ix[q]] - 1) * 1e4)
                days[lab] = {f"gun{q + 1}": st(np.array(seg[q])) for q in range(3)}
            br["NAS100_gun_gun"] = days
    res["T2_broker_2018_26"] = br
    # T4 GDAXI yıl
    g = px("GDAXI", "Close"); idx = g.index; yr = {}
    for k, r in M.iterrows():
        if sR1[k] == 0:
            continue
        i = idx.searchsorted(r.d_s, side="right"); j = idx.searchsorted(r.d_D, side="right") - 1
        if j > i:
            yr.setdefault(r.d_s.year, []).append(sR1[k] * (g.iloc[j] / g.iloc[i] - 1) * 1e4 - 3)
    res["T4_GDAXI_yil"] = {y: round(float(np.mean(v)), 1) for y, v in sorted(yr.items())}
    (H / "results/qs04_dongu.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
