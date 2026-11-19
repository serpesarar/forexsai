"""gx.py — GX-01…04. python gx.py"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/vade_mantik_20261118/src")); sys.path.insert(0, str(ROOT / "research/son4_20261118/src"))
import vm, ek2_sonra as E2, ek7_orb as K7
HERE = Path(__file__).resolve().parents[1]; RES = HERE / "results"
S = E2.S  # 9 set; k ve a kolonları hazır
V = vm.V
CAL = E2.cal

def fomc_dates():
    a = pd.read_csv(HERE / "data/fomc_1994_2007.csv"); b = pd.read_csv(ROOT / "research/xau_best_days_20261015/makro/out/calendar.csv")
    b = b[b.event.str.upper().str.contains("FOMC")]
    d = sorted(set(pd.to_datetime(a.date)) | set(pd.to_datetime(b.date)))
    return [x for x in d if x in set(CAL)]

def fomc_week(cal, fd):
    pos = np.array([cal.get_loc(x) for x in fd]); i = np.arange(len(cal))
    j = np.searchsorted(pos, i, side="right") - 1
    k = np.where(j >= 0, i - pos[np.maximum(j, 0)], 999)
    nxt = np.searchsorted(pos, i, side="left"); nk = np.where(nxt < len(pos), pos[np.minimum(nxt, len(pos) - 1)] - i, 999)
    k = np.where(nk == 1, -1, k)
    w = np.floor((k + 1) / 5).astype(int)
    valid = (k >= -1) & (k <= 33) & (cal >= fd[0])
    return pd.Series(np.where(valid, w, -9), index=cal)

def gx01():
    t = pd.read_parquet(ROOT / "research/ndx_10y_1m_20261116/results/a_trades.parquet"); t["d"] = pd.to_datetime(t.d)
    ex = vm.expiries(CAL, "fri3"); kser = pd.Series(vm.days_to(CAL, ex), index=CAL); aser = E2.A
    t["k"] = kser.reindex(t.d).values; t["a"] = aser.reindex(t.d).values
    unit = {"C3B": "net_bp", "C3": "net_bp", "CAPREV": "R", "ORBVIX": "R", "ORBVIX_LO": "R", "CEKIC": "R", "KSG": "net_bp",
            "AYSONU_SON": "net_bp", "AYSONU_E2": "net_bp", "FOMC_GECE": "net_bp"}
    out = {}
    for rule, g in t.groupby("rule"):
        g = g.reset_index(drop=True); g["net"] = g[unit[rule]]
        rec = {}
        for bn, m in (("veto_k0_2", np.isin(g.k.values, [0, 1, 2])), ("sonra_a3_7", np.isin(g.a.values, range(3, 8)))):
            rec[bn] = {"tum": vm.diff(g, m, seed=1)}
            for e, a_, b_ in (("ESKI", "2018-01-01", "2021-10-31"), ("YENI", "2021-11-01", "2026-12-31")):
                mm = ((g.d >= a_) & (g.d <= b_)).values
                gg = g[mm].reset_index(drop=True); rec[bn][e] = vm.diff(gg, m[mm], seed=2)
        out[rule] = rec
    # ORB bağımsız (örtüşmesiz NQ 2019–22 + MT5 M15 2022–26)
    NY = K7.NY
    vp = lambda b: K7.lib.vix_prev_map(sorted(set(pd.to_datetime(b.t, unit="s", utc=True).dt.tz_convert(NY).dt.date)))
    nq, st = K7.KE.bars("NQ"); a = K7.orb_generic(nq, st, vp(nq)); a = a[a.d < "2022-08-10"]
    m = K7.mt5_m15(); b = K7.orb_generic(m, 900, vp(m)); z = pd.concat([a, b], ignore_index=True).rename(columns={"R": "net"})
    z["k"] = kser.reindex(z.d).values; z["a"] = aser.reindex(z.d).values
    out["ORB_bagimsiz"] = {"veto_k0_2": vm.diff(z, np.isin(z.k.values, [0, 1, 2]), seed=3), "sonra_a3_7": vm.diff(z, np.isin(z.a.values, range(3, 8)), seed=4)}
    return out

def subset_pool(mask_fn, eras=None):
    out = {"havuz": vm.zpool([(t, mask_fn(t)) for t in S.values()]), "set": {nm: vm.diff(t, mask_fn(t), seed=7) for nm, t in S.items()}}
    for nm_e, a_, b_ in (eras or []):
        sets = []
        for t in S.values():
            u = t[(t.d >= a_) & (t.d <= b_)].reset_index(drop=True)
            if len(u) > 20: sets.append((u, mask_fn(u)))
        out[nm_e] = vm.zpool(sets)
    out["set_arti"] = int(sum(1 for v in out["set"].values() if v.get("fark", 0) > 0))
    return out

def main():
    RES.mkdir(exist_ok=True)
    out = {"GX01": gx01()}
    fw = fomc_week(CAL, fomc_dates())
    for t in S.values(): t["fw"] = fw.reindex(pd.to_datetime(t.d)).values
    S2 = {nm: t[t.fw >= 0].reset_index(drop=True) for nm, t in S.items()}
    out["GX02"] = {"havuz": vm.zpool([(t, (t.fw % 2 == 0).values) for t in S2.values()]),
                   "set": {nm: vm.diff(t, (t.fw % 2 == 0).values, seed=8) for nm, t in S2.items()}}
    for e, a_, b_ in (("1994_2016", "1994-01-01", "2016-12-31"), ("2017_sonrasi", "2017-01-01", "2026-12-31")):
        sets = [(u, (u.fw % 2 == 0).values) for u in (t[(t.d >= a_) & (t.d <= b_)].reset_index(drop=True) for t in S2.values()) if len(u) > 20]
        out["GX02"][e] = vm.zpool(sets)
    out["GX02"]["set_arti"] = int(sum(1 for v in out["GX02"]["set"].values() if v.get("fark", 0) > 0))
    def earn(t):
        d = pd.to_datetime(t.d); ld = pd.Series(CAL).groupby(CAL.to_period("M")).max()
        last = d.isin(set(ld.values))
        return (d.dt.month.isin([1, 4, 7, 10]) & (d.dt.day >= 18) & (d.dt.day <= 30) & ~last).values
    out["GX03"] = subset_pool(earn, [("1985_1999", "1985-01-01", "1999-02-28"), ("1999_2026", "1999-03-01", "2026-12-31")])
    hol = []
    cs = list(CAL)
    for i in range(len(cs) - 1):
        gap = (cs[i + 1] - cs[i]).days
        if gap > 1 and not (cs[i].dayofweek == 4 and gap == 3): hol.append(cs[i])
    hol = set(hol)
    out["GX04"] = subset_pool(lambda t: pd.to_datetime(t.d).isin(hol).values, [("1985_1999", "1985-01-01", "1999-02-28"), ("1999_2026", "1999-03-01", "2026-12-31")])
    (RES / "gx.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    for r, v in out["GX01"].items(): print("GX01", r, json.dumps(v, ensure_ascii=False))
    for g in ("GX02", "GX03", "GX04"):
        v = out[g]; print(g, "havuz", v["havuz"], {k: v[k] for k in v if k not in ("havuz", "set")}); print("   ", {nm: (x.get("n"), x.get("fark")) for nm, x in v["set"].items()})

if __name__ == "__main__": main()
