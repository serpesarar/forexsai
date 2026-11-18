"""kosu.py — ana koşu + önceden sayılmış varyantlar + eşli plasebo + S1 koşulsuz taban + MT5 bağımsız besleme (PROTOCOL §3–5)."""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pandas as pd

import kurallar as K
import lib
import veri

STRATS = ["S1", "S2", "S3", "S4"]
N_PLACEBO = 10
PLACEBO_LW_MAX = 0.15
SEED = 20261117


def col_of(strat: str) -> str:
    return "net_bp" if strat == "S1" else "R"


def cluster_p(v: np.ndarray, cl: np.ndarray, n: int = 4000, seed: int = 11) -> float:
    """Kurulum-küme bootstrap P(ortalama > 0) — bağımsız karar = kurulum."""
    ok = np.isfinite(v)
    v, cl = v[ok], cl[ok]
    if len(v) < 3:
        return float("nan")
    u, inv = np.unique(cl, return_inverse=True)
    s, c = np.bincount(inv, v), np.bincount(inv)
    pick = np.random.default_rng(seed).integers(0, len(u), (n, len(u)))
    return float(((s[pick].sum(1) / c[pick].sum(1)) > 0).mean())


def stats(df: pd.DataFrame, strat: str) -> dict:
    x = df[df.rule == strat]
    if x.empty:
        return {"n": 0}
    col = col_of(strat)
    s = lib.summarize(x, col)
    v = x[col].values.astype(float)
    out = {k: (round(v_, 4) if isinstance(v_, float) else v_) for k, v_ in s.items()
           if k in ("n", "mean", "median", "hit", "P", "h1", "h2", "mean_s15", "ex_top5", "sum")}
    out.update({"kurulum": int(x.setup.nunique()), "P_kume": round(cluster_p(v, x.setup.values), 4),
                "net_bp": round(float(x.net_bp.mean()), 2), "zaman_cikis": int((x.why == "time").sum()) if strat != "S1" else None,
                "tp_orani": round(float((x.why == "tp").mean()), 3)})
    return out


def by_era(df: pd.DataFrame, strat: str) -> dict:
    return {"TUM": stats(df, strat), "KESIF": stats(df[df.era == "ESKI"], strat), "TEST": stats(df[df.era == "YENI"], strat),
            "yil": {int(y): round(float(g[g.rule == strat][col_of(strat)].mean()), 3)
                    for y, g in df.groupby("year") if (g.rule == strat).any()}}


def diff_p(a: pd.DataFrame, b: pd.DataFrame, col: str, n: int = 4000, seed: int = 5) -> float:
    """P(ort(a) − ort(b) > 0), iki tarafta ay-blok bootstrap."""
    rng = np.random.default_rng(seed)

    def boot(df: pd.DataFrame) -> np.ndarray:
        v = df[col].values.astype(float)
        mo = pd.to_datetime(df.d).dt.to_period("M").astype(str).values
        u, inv = np.unique(mo, return_inverse=True)
        s, c = np.bincount(inv, v), np.bincount(inv)
        pick = rng.integers(0, len(u), (n, len(u)))
        return s[pick].sum(1) / c[pick].sum(1)

    if len(a) < 3 or len(b) < 3:
        return float("nan")
    return float((boot(a) - boot(b) > 0).mean())


def placebo_events(b: pd.DataFrame, ev: pd.DataFrame, rep: int) -> pd.DataFrame:
    """Her olay için aynı yıl × dilim × yıl-içi aralık beşlisinde fitilsiz bir mum (yoksa yıl × dilim)."""
    bb = b.copy()
    bb["rq"] = bb.groupby("year").rng_pct.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
    pool = bb[(bb.lw_pct < PLACEBO_LW_MAX) & (bb.n15 >= 6)]
    g3 = {k: v.index.values for k, v in pool.groupby(["year", "slot", "rq"])}
    g2 = {k: v.index.values for k, v in pool.groupby(["year", "slot"])}
    rq = bb.set_index("t").rq
    rng = np.random.default_rng(SEED + rep)
    pick = []
    for e in ev.itertuples():
        c = g3.get((e.year, e.slot, rq.get(e.t)), np.array([]))
        if len(c) == 0:
            c = g2.get((e.year, e.slot), np.array([]))
        if len(c):
            pick.append(int(rng.choice(c)))
    return bb.loc[sorted(set(pick))].sort_values("tend").reset_index(drop=True)


def run_feed(p: veri.PathBars, q: pd.DataFrame, b: pd.DataFrame, excl: set[int], cfgs: list[K.Cfg], n_pl: int,
             tag: str, conf: pd.DataFrame | None = None, h4: pd.DataFrame | None = None) -> dict:
    res: dict = {"besleme": tag, "varyant": {}, "plasebo": {}, "iyimser": {}}
    trades_main = None
    for cfg in cfgs:
        tr, st = K.run(p, q, b, cfg, exclude_t=excl, conf=conf, h4=h4)
        res["varyant"][cfg.name] = {"olay": int(len(st)), "kurulum_var": int(st.j_main.notna().sum()),
                                    "bitis": st.bitis.value_counts().to_dict(), "atlanan": tr.attrs.get("skip"),
                                    **{s: by_era(tr, s) for s in STRATS}}
        if cfg.name == "ANA":
            trades_main = tr
            st.to_csv(veri.RESULTS / f"kurulumlar_{tag}.csv", index=False)
        print(f"[{tag}] {cfg.name}: olay {len(st)}, işlem {len(tr)} — " + ", ".join(
            f"{s} {res['varyant'][cfg.name][s]['TUM'].get('mean', float('nan')):+.3f}" for s in STRATS), flush=True)
    base = cfgs[0]
    opt, _ = K.run(p, q, b, base, exclude_t=excl, optimistic=True, conf=conf, h4=h4)
    res["iyimser"] = {s: stats(opt, s) for s in STRATS}
    ev = K.events(b, base.thr, excl, base.uw_ratio, base.body_rule, conf, base.confirm if conf is not None else "none",
                  q, h4 if base.h4_check else None, base.h4_body)
    res["olay_t"] = ev.t.astype(int).tolist()
    pls = []
    for r in range(n_pl):
        pe = placebo_events(b, ev, r)
        tr, _ = K.run(p, q, b, base, ev=pe)
        tr["rep"] = r
        pls.append(tr)
    pl = pd.concat(pls, ignore_index=True)
    for s in STRATS:
        a, z = trades_main[trades_main.rule == s], pl[pl.rule == s]
        res["plasebo"][s] = {"plasebo": by_era(pl, s), "fark_TUM": round(float(a[col_of(s)].mean() - z[col_of(s)].mean()), 4),
                             "P_fark_TUM": round(diff_p(a, z, col_of(s)), 4),
                             "fark_TEST": round(float(a[a.era == "YENI"][col_of(s)].mean() - z[z.era == "YENI"][col_of(s)].mean()), 4),
                             "P_fark_TEST": round(diff_p(a[a.era == "YENI"], z[z.era == "YENI"], col_of(s)), 4)}
    trades_main.drop(columns=["d"]).assign(d=trades_main.d.astype(str)).to_csv(veri.RESULTS / f"islemler_{tag}_ANA.csv", index=False)
    pl.assign(d=pl.d.astype(str)).to_csv(veri.RESULTS / f"islemler_{tag}_plasebo.csv", index=False)
    return res


def s1_baseline(p: veri.PathBars, b: pd.DataFrame, excl: set[int], tag: str, ev_t: set[int]) -> dict:
    """S1 koşulsuz taban: her 210m kapanışında AL, aynı TP/tutuş; dilim ve olay/olmayan kırılımı."""
    allb = b[~b.t.isin(excl) & (b.n15 >= 6)].sort_values("tend").reset_index(drop=True)
    tr = K.execute(p, K.s1_signals(allb, K.Cfg()), single=False)
    tr["lw"] = allb.lw_pct.values[tr.setup.values]
    tr["slot"] = allb.slot.values[tr.setup.values]
    tr["olay"] = allb.t.values[tr.setup.values].astype(np.int64)
    tr["olay"] = tr.olay.isin(ev_t)
    out = {"tum_mumlar": stats(tr, "S1"), "olay_disi": stats(tr[~tr.olay], "S1"), "olay": stats(tr[tr.olay], "S1"),
           "dilim": {int(k): {"taban": round(float(g[~g.olay].net_bp.mean()), 2), "olay": round(float(g[g.olay].net_bp.mean()), 2),
                              "n_olay": int(g.olay.sum())} for k, g in tr.groupby("slot")},
           "fitil_kova": {str(k): {"n": int(len(g)), "bp": round(float(g.net_bp.mean()), 2)}
                          for k, g in tr.groupby(pd.cut(tr.lw, [0, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 99]), observed=True)}}
    tr.drop(columns=["d"]).to_csv(veri.RESULTS / f"s1_taban_{tag}.csv", index=False)
    return out


def olay_listesi(b: pd.DataFrame, q: pd.DataFrame, conf: pd.DataFrame, h4: pd.DataFrame, ev_t: set[int]) -> None:
    """Tüm ana olaylar: iki beslemenin O/H/L/C ve fitil ölçüleri (kullanıcının gözle denetimi için)."""
    cols = ["t", "open", "high", "low", "close", "lw_pct", "uw_pct", "gv_pct"]
    e = b[b.t.isin(ev_t)][["zaman_ny", "slot", "n15"] + cols]
    m = conf[cols].rename(columns={c: f"mt5_{c}" for c in cols if c != "t"})
    e = e.merge(m, on="t", how="left")
    e["alt_fitil_puan"] = np.minimum(e.open, e.close) - e.low
    ee = b[b.t.isin(ev_t)].sort_values("t")
    hk = veri.h4_key(K.low_time(ee, q))
    hh = h4.reindex(hk)
    e = e.sort_values("t").reset_index(drop=True)
    e["h4_sunucu"] = [str(x) for x in hk]
    for c in ("lw_pct", "uw_pct", "gv_pct"):
        e[f"h4_{c}"] = hh[c].values
    e["zaman_ny"] = e.zaman_ny.astype(str)
    e.round(3).to_csv(veri.RESULTS / "olaylar_ANA.csv", index=False)


def main() -> None:
    veri.RESULTS.mkdir(exist_ok=True)
    out: dict = {}
    # ── Ana besleme: Dukascopy 1m ──
    p = veri.duka_path()
    q = veri.build_15m(p)
    b = veri.build_210m(q)
    chk = veri.check_vs_file(b)
    excl = chk.pop("supheli_t")
    out["veri_kontrol"] = {**chk, "supheli_dislanan_olay": int(((b.lw_pct >= 0.5) & b.t.isin(excl)).sum()),
                           "aralik": [str(b.zaman_ny.min()), str(b.zaman_ny.max())]}
    assert chk["fark_0_olmayan"] == 0, "210m dosyasıyla fark var"
    cfgs = K.variants()
    conf = veri.mt5_210m()
    h4 = veri.mt5_h4()
    out["DUKA"] = run_feed(p, q, b, excl, cfgs, N_PLACEBO, "DUKA", conf, h4)
    ev_t = set(out["DUKA"].pop("olay_t"))
    out["DUKA"]["s1_taban"] = s1_baseline(p, b, excl, "DUKA", ev_t)
    olay_listesi(b, q, conf, h4, ev_t)
    # ── Bağımsız besleme: MT5 NAS100 M15 (15m çözünürlük) ──
    pm = veri.mt5_path("M15")
    qm = veri.build_15m(pm)
    bm = veri.build_210m(qm)
    mt5_cfgs = [c for c in cfgs if c.name in ("ANA", "W14", "W3", "F3", "T75", "T40", "S4g", "U1", "U3", "E1", "G1", "H4", "H4G", "v1")]
    out["MT5"] = run_feed(pm, qm, bm, set(), mt5_cfgs, 5, "MT5", None, h4)
    out["MT5"]["s1_taban"] = s1_baseline(pm, bm, set(), "MT5", set(out["MT5"].pop("olay_t")))
    out["MT5"]["aralik"] = [str(bm.zaman_ny.min()), str(bm.zaman_ny.max())]
    out["deneme_sayaci"] = {"DUKA_hucre": len(cfgs) * len(STRATS) * 3, "MT5_hucre": len(mt5_cfgs) * len(STRATS) * 3,
                            "plasebo_kopya": N_PLACEBO}
    (veri.RESULTS / "ozet.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    print("yazıldı: results/ozet.json")


if __name__ == "__main__":
    main()
