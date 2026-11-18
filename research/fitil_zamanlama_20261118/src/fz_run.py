"""fz_run.py — PROTOCOL §5–6. `kesif`: 504 hücre + ızgara plasebosu + dondurma (TEST'e bakmaz). `dogrula`: dondurulmuşlar.

Kullanım: python fz_run.py kesif | python fz_run.py dogrula [K]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

import numpy as np
import pandas as pd

import fz  # noqa: I001
import kesif as KS          # research/vw_dip_20261117/src (cluster_p, placebo_shifts)

RES = fz.HERE / "results"
def _atr_entries(p, tf):
    return pd.concat([fz.entries(p, tf, atr_k=k) for k in (1.0, 1.5, 2.0)], ignore_index=True)


SIDE = {"al": (fz.entries, fz.evaluate_all, ""), "sat": (fz.entries_short, fz.evaluate_all_short, "_sat"),
        "atr": (_atr_entries, fz.evaluate_all, "_atr")}
MODE = "al"
CACHE = fz.HERE / "cache"
VIXS = {"hepsi": 0.0, "v18.4": 18.4}
N_MIN, P_MIN, N_PL, MAX_FROZEN, MAX_PER = 40, 0.90, 20, 5, 2


def ndx_entries() -> tuple:
    p = fz.path_ndx()
    f_ent, _, suf = SIDE[MODE]
    cp = CACHE / f"girisler_ndx{suf}.parquet"
    if cp.exists():
        e = pd.read_parquet(cp)
    else:
        e = pd.concat([f_ent(p, "1h"), f_ent(p, "210m")], ignore_index=True)
        e = fz.add_context(e)
        CACHE.mkdir(exist_ok=True)
        e.to_parquet(cp)
    return p, e


def grid(ev: pd.DataFrame, e: pd.DataFrame, n_boot: int = 2000) -> pd.DataFrame:
    if "k" not in e.columns:
        e = e.assign(k=0.0)
    x = ev.merge(e[["tf", "typ", "vix", "d", "k"]], left_on="e", right_index=True)
    rows = []
    for (tf, kk, typ, st, tp, tm), g0 in x.groupby(["tf", "k", "typ", "stop", "tp", "time"]):
        for vn, vv in VIXS.items():
            g = g0[g0.vix >= vv] if vv > 0 else g0
            if len(g) < 3:
                continue
            rows.append({"tf": tf, "k": kk, "typ": typ, "stop": st, "tp": tp, "time": tm, "vix": vn, "n": len(g), "mean": g.R.mean(),
                         "mean15": g.R15.mean(), "hit": (g.R > 0).mean(),
                         "t": g.R.mean() / (g.R.std(ddof=1) / np.sqrt(len(g))),
                         "P": KS.cluster_p(g.R.values, g.d.astype(str).values, n_boot) if len(g) >= N_MIN else np.nan})
    return pd.DataFrame(rows)


def passing(gr: pd.DataFrame) -> pd.DataFrame:
    return gr[(gr.n >= N_MIN) & (gr["mean"] > 0) & (gr.P >= P_MIN) & (gr.mean15 > 0)]


def kesif() -> None:
    RES.mkdir(exist_ok=True)
    p, e = ndx_entries()
    ek = e[e.era == "KESIF"].reset_index(drop=True)
    print("KEŞİF girişleri:", ek.groupby(["tf", "typ"]).size().to_dict(), flush=True)
    f_ev, suf = SIDE[MODE][1], SIDE[MODE][2]
    gr = grid(f_ev(p, ek), ek)
    gr.to_csv(RES / f"kesif_izgara{suf}.csv", index=False)
    real = passing(gr)
    print(f"KEŞİF: {len(gr)} hücre, aday {len(real)}", flush=True)
    pc = []
    for r in range(N_PL):
        pc.append(int(len(passing(grid(f_ev(p, ek, shift=KS.placebo_shifts(ek, 500 + r)), ek, 500)))))
        print(f"  plasebo {r}: {pc[-1]}", flush=True)
    frozen, per = [], {}
    for r in real.sort_values("t", ascending=False).itertuples():
        key = (r.tf, r.typ, getattr(r, "k", 0.0))
        if per.get(key, 0) >= MAX_PER:
            continue
        frozen.append({k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in r._asdict().items() if k != "Index"})
        per[key] = per.get(key, 0) + 1
        if len(frozen) == MAX_FROZEN:
            break
    oz = {"hucre": len(gr), "aday": len(real), "plasebo": pc, "plasebo_p95": float(np.percentile(pc, 95)),
          "yuzdelik": float((np.array(pc) < len(real)).mean()), "sans_ustu": bool(len(real) > np.percentile(pc, 95)), "donmus": frozen}
    (RES / f"kesif_ozet{suf}.json").write_text(json.dumps(oz, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(oz, indent=1, ensure_ascii=False, default=str))


def rows_of(ev: pd.DataFrame, e: pd.DataFrame, c: dict) -> pd.DataFrame:
    if "k" not in e.columns:
        e = e.assign(k=0.0)
    x = ev.merge(e[["tf", "typ", "vix", "d", "k"]], left_on="e", right_index=True)
    x = x[(x.tf == c["tf"]) & (x.k == c.get("k", 0.0)) & (x.typ == c["typ"]) & (x.stop == c["stop"]) & (x.tp == c["tp"]) & (x.time == c["time"])]
    if VIXS[c["vix"]] > 0:
        x = x[x.vix >= VIXS[c["vix"]]]
    return x.sort_values("t_in").reset_index(drop=True)


def summ(x: pd.DataFrame) -> dict:
    if len(x) == 0:
        return {"n": 0}
    h = len(x) // 2
    return {"n": int(len(x)), "gun": int(x.d.nunique()), "mean": round(float(x.R.mean()), 4), "hit": round(float((x.R > 0).mean()), 3),
            "P_kume": round(KS.cluster_p(x.R.values, x.d.astype(str).values), 4), "mean15": round(float(x.R15.mean()), 4),
            "h1": round(float(x.R.iloc[:h].mean()), 4) if h else None, "h2": round(float(x.R.iloc[h:].mean()), 4) if h else None,
            "ex_top5": round(float((x.R.sum() - np.sort(x.R.values)[-5:].sum()) / max(1, len(x) - 5)), 4) if len(x) > 5 else None,
            "yil": {int(y): round(float(g.R.mean()), 3) for y, g in x.groupby(pd.to_datetime(x.d).dt.year)}}


def single(x: pd.DataFrame) -> pd.DataFrame:
    keep, busy = [], -1
    for r in x.itertuples():
        if r.t_in >= busy:
            keep.append(r.Index)
            busy = r.t_out
    return x.loc[keep]


def dogrula(k_total: int) -> None:
    f_ent, f_ev, suf = SIDE[MODE]
    frozen = json.loads((RES / f"kesif_ozet{suf}.json").read_text())["donmus"]
    p_test = 1 - 0.10 / k_total
    p, e = ndx_entries()
    et = e[e.era == "TEST"].reset_index(drop=True)
    ev, evo = f_ev(p, et), f_ev(p, et, optimistic=True)
    pls = [f_ev(p, et, shift=KS.placebo_shifts(et, 700 + r)) for r in range(10)]
    ext = {}
    for nm, fp in (("DAX", fz.path_dax), ("NQ", fz.path_nq)):
        pp = fp()
        ee = fz.add_context(pd.concat([f_ent(pp, "1h"), f_ent(pp, "210m")], ignore_index=True))
        ext[nm] = (ee, f_ev(pp, ee))
    out = []
    for c in frozen:
        x, xo, xs = rows_of(ev, et, c), rows_of(evo, et, c), None
        xs = single(x)
        xp = pd.concat([rows_of(z, et, c) for z in pls], ignore_index=True)
        s = summ(x)
        sd, sq = summ(rows_of(ext["DAX"][1], ext["DAX"][0], c)), summ(rows_of(ext["NQ"][1], ext["NQ"][0], c))
        dp = float(np.mean([x.R.mean() - xp.sample(len(x), replace=True, random_state=k).R.mean() > 0 for k in range(2000)])) if len(x) > 2 and len(xp) else float("nan")
        icra = float(xo.R.mean()) - s.get("mean", np.nan) if len(xo) else np.nan
        ok = {"1_test": bool(s.get("mean", -1) > 0 and s.get("P_kume", 0) >= p_test),
              "2_dax": bool(sd.get("mean", -1) > 0 and sd.get("P_kume", 0) >= 0.90),
              "3_nq": bool(sq.get("mean", -1) > 0),
              "4_surtunme": bool(s.get("mean15", -1) > 0),
              "5_plasebo": bool(dp >= 0.90),
              "6_icra": bool(np.isfinite(icra) and icra < 0.5 * abs(s.get("mean", 0))),
              "7_tek_poz": bool(len(xs) and xs.R.mean() > 0),
              "8_hacim": bool(c["n"] + s.get("n", 0) >= 150)}
        out.append({"aday": c, "TEST": s, "DAX": sd, "NQ": sq, "P_plasebo": round(dp, 3), "icra_fark": round(icra, 4) if np.isfinite(icra) else None,
                    "tek_poz": round(float(xs.R.mean()), 4) if len(xs) else None, "olcut": ok, "gecti": all(ok.values())})
        print(f"{c['tf']} {c['typ']} {c['stop']} TP{c['tp']} {c['time']} {c['vix']}: KEŞİF {c['mean']:+.3f} (n {c['n']}) → TEST "
              f"{s.get('mean', float('nan')):+.3f} (n {s.get('n')}, P {s.get('P_kume')}) DAX {sd.get('mean', float('nan')):+.3f} "
              f"(n {sd.get('n')}, P {sd.get('P_kume')}) NQ {sq.get('mean', float('nan')):+.3f} (n {sq.get('n')}) plasebo P {dp:.2f} → "
              f"{sum(ok.values())}/8 {'GEÇTİ' if all(ok.values()) else ''}", flush=True)
    (RES / f"dogrulama{suf}.json").write_text(json.dumps({"tarih": datetime.now().isoformat(timespec="seconds"), "P_test_esik": p_test,
                                                     "adaylar": out}, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    if len(sys.argv) > 3:
        MODE = sys.argv[3]
    if sys.argv[1] == "kesif":
        kesif()
    else:
        dogrula(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
    # kullanım: python fz_run.py kesif 0 sat  |  python fz_run.py dogrula K sat
