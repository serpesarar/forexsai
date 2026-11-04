"""PROTOCOL.md §3–5 ana koşu (Duka keşif 2008–16 / doğrulama 2017–2026-06-16).
Çıktı: results/tests.csv (20 test × 2 dönem), results/tail.csv, results/strat.csv, results/null_*.npy, results/main.txt"""
import json, os
import numpy as np, pandas as pd
from common import load_d, events, sim_cell, path_sim, one_position, day_boot_p, RES
from features import raw_features, load_vix, add_f9, FEATS, NAMES

REPS = int(os.environ.get("REPS", "1000"))
SPREAD = 0.12
rng = np.random.default_rng(20261016)

d = load_d(); vix = load_vix()
fe = raw_features(d, vix)
ev = events(d, "R0", +1)
R, xi, code, hl = sim_cell(d, ev, None, 1.5, 20, +1, SPREAD)
m = np.isfinite(R)
ev = ev[m].reset_index(drop=True); R = R[m]; xi = xi[m]
ev["R"] = R; ev["dur"] = xi - ev.ent.to_numpy()
ev["per"] = np.where(ev.year <= 2016, "kesif", "dogrulama")
ev["ent_day"] = d.ts.dt.strftime("%Y-%m-%d").to_numpy()[ev.ent]
ev["week"] = d.ts.dt.tz_convert(None).dt.to_period("W").astype(str).to_numpy()[ev.sig]
thr9 = float(np.nanquantile(fe.mom6.to_numpy()[ev.sig[ev.per == "kesif"]], 2 / 3))
fe = add_f9(fe, thr9)
for f in FEATS:
    ev[f] = fe[f].to_numpy()[ev.sig].astype(bool)

# ── tüm barlar için aynı geometride BUY R'si (haftalık sürüklenme W ve P1-F için) ──
O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy(); atr = d.atr.to_numpy(); n = len(d)
valid = np.zeros(n, bool); valid[:-1] = seg[1:] == seg[:-1]; valid &= np.isfinite(atr) & (atr > 0)
vi = np.where(valid)[0]
Rall = np.full(n, np.nan)
Rall[vi], _, _ = path_sim(O, H, L, C, seg, vi, vi + 1, atr[vi], np.full(len(vi), 20), None, 1.5, +1, SPREAD)
wk_all = d.ts.dt.tz_convert(None).dt.to_period("W").astype(str).to_numpy()
W = pd.Series(Rall).groupby(wk_all).mean()
ev["W"] = W.reindex(ev.week).to_numpy()
ev["exc"] = ev.R - ev.W
fe_bool = {f: fe[f].to_numpy().astype(bool) for f in FEATS}


def strat(sub: pd.DataFrame, w: np.ndarray, per: str) -> dict:
    """Strateji ölçüleri; w = risk ağırlığı."""
    if len(sub) == 0:
        return dict(n=0)
    r = sub.R.to_numpy(); wr = w * r
    t0 = pd.Timestamp("2008-01-01") if per == "kesif" else pd.Timestamp("2017-01-01")
    t1 = pd.Timestamp("2016-12-31") if per == "kesif" else pd.Timestamp("2026-06-16")
    weeks = pd.period_range(t0, t1, freq="W").astype(str)
    wk = pd.Series(wr).groupby(sub.week.to_numpy()).sum()
    wall = wk.reindex(weeks, fill_value=0.0)
    cum = np.cumsum(wr)
    dd = float((cum - np.maximum.accumulate(np.r_[0, cum])[1:]).min())
    day = pd.Series(wr).groupby(sub.ent_day.to_numpy()).sum().sort_values(ascending=False)
    top20 = set(day.index[:20])
    keep = ~np.isin(sub.ent_day.to_numpy(), list(top20))
    rep = np.repeat(np.arange(len(r)), w.astype(int))
    P, ci = day_boot_p(r[rep], sub.ent_day.to_numpy()[rep])
    return dict(n=len(r), per_week=len(r) / len(weeks), ortR=float(wr.sum() / w.sum()), R_week=float(wall.mean()),
                sharpe_w=float(wall.mean() / wall.std()), pos_weeks=float((wk > 0).mean()), maxdd=dd, totR=float(wr.sum()),
                ex20=float(wr[keep].sum() / w[keep].sum()), P=P, ci_lo=ci[0], ci_hi=ci[1],
                top20_share=float(day.iloc[:20].sum() / wr.sum()) if wr.sum() != 0 else np.nan)


def stats_d(e: pd.DataFrame, Rv: np.ndarray, dur: np.ndarray) -> np.ndarray:
    """20 istatistik: [FİLTRE F1..F10, BOYUT2 F1..F10] (R/süre verilen düzenle)."""
    ent = e.ent.to_numpy()
    kb = one_position(ent, ent + dur)
    base = Rv[kb].mean()
    out = np.empty(2 * len(FEATS))
    for j, f in enumerate(FEATS):
        F = e[f].to_numpy()
        idx = np.where(F)[0]
        kf = one_position(ent[idx], ent[idx] + dur[idx])
        out[j] = Rv[idx][kf].mean() - base if kf.any() else np.nan
        Fb = F[kb]; rb = Rv[kb]
        out[len(FEATS) + j] = rb[Fb].mean() - rb[~Fb].mean() if Fb.any() and (~Fb).any() else np.nan
    return out


def circ_shift(e: pd.DataFrame, rng) -> np.ndarray:
    """Yıl içinde dairesel kaydırma permütasyon indeksi (olaylar giriş sırasında)."""
    perm = np.arange(len(e))
    for y, g in e.groupby("year").indices.items():
        g = np.sort(g)
        perm[g] = np.roll(g, rng.integers(1, len(g)))
    return perm


def did_boot(e: pd.DataFrame, f: str, nb=4000, seed=7):
    x = e.exc.to_numpy(); F = e[f].to_numpy(); ok = np.isfinite(x)
    x, F, days = x[ok], F[ok], e.ent_day.to_numpy()[ok]
    u, inv = np.unique(days, return_inverse=True)
    sF = np.bincount(inv, weights=x * F, minlength=len(u)); nF = np.bincount(inv, weights=F.astype(float), minlength=len(u))
    sN = np.bincount(inv, weights=x * ~F, minlength=len(u)); nN = np.bincount(inv, weights=(~F).astype(float), minlength=len(u))
    obs = sF.sum() / nF.sum() - sN.sum() / nN.sum()
    r = np.random.default_rng(seed); idx = r.integers(0, len(u), (nb, len(u)))
    bs = sF[idx].sum(1) / nF[idx].sum(1) - sN[idx].sum(1) / nN[idx].sum(1)
    return float(obs), float((bs > 0).mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def p1f(e: pd.DataFrame, f: str, draws=20, seed=11):
    """İkincil: aynı yıl + UTC saati + aynı bayrak durumundan rastgele bar R'si (Rall)."""
    r = np.random.default_rng(seed)
    yr = d.year.to_numpy(); uh = d.utc_h.to_numpy(); Fb = fe_bool[f]
    ok = valid & np.isfinite(Rall)
    key_all = (yr * 100 + uh) * 2 + Fb
    pools = pd.Series(np.where(ok)[0]).groupby(key_all[ok]).apply(np.array).to_dict()
    key_ev = (e.year.to_numpy() * 100 + e.utc_h.to_numpy()) * 2 + e[f].to_numpy()
    pm = np.full(len(e), np.nan)
    for k, idx in pd.Series(np.arange(len(e))).groupby(key_ev).indices.items():
        p = pools.get(k)
        if p is not None and len(p):
            pm[idx] = Rall[p[r.integers(0, len(p), (len(idx), draws))]].mean(1)
    F = e[f].to_numpy()
    return dict(rule_F=float(e.R[F].mean()), p1f_F=float(np.nanmean(pm[F])), rule_N=float(e.R[~F].mean()),
                p1f_N=float(np.nanmean(pm[~F])), cover=float(np.isfinite(pm).mean()))


rows, tails, strats, lines = [], [], [], []
lines.append(f"F9 eşiği (keşif olayları mom6 %66,7'lik) = {thr9:.4f}")
for per in ("kesif", "dogrulama"):
    e = ev[ev.per == per].sort_values("ent").reset_index(drop=True)
    Rv, dur = e.R.to_numpy(), e.dur.to_numpy()
    obs = stats_d(e, Rv, dur)
    null = np.empty((REPS, len(obs)))
    for r_ in range(REPS):
        p = circ_shift(e, rng)
        null[r_] = stats_d(e, Rv[p], dur[p])
    np.save(os.path.join(RES, f"null_{per}.npy"), null); np.save(os.path.join(RES, f"obs_{per}.npy"), obs)
    ent = e.ent.to_numpy(); kb = one_position(ent, ent + dur)
    base = e[kb]
    sb = strat(base, np.ones(len(base)), per); sb.update(feat="TABAN", use="-", per=per); strats.append(sb)
    # en iyi günler (taban tek-poz)
    day = base.groupby("ent_day").R.sum().sort_values(ascending=False)
    b20, b50 = set(day.index[:20]), set(day.index[:50])
    lines.append(f"[{per}] olay {len(e)}, taban tek-poz n={len(base)} ortR {base.R.mean():+.4f} toplam {base.R.sum():.1f} "
                 f"en iyi 20 gün payı {day.iloc[:20].sum()/base.R.sum():.2f}")
    for j, f in enumerate(FEATS):
        F = e[f].to_numpy()
        # FİLTRE stratejisi
        idx = np.where(F)[0]; kf = one_position(ent[idx], ent[idx] + dur[idx])
        sf = strat(e.iloc[idx][kf], np.ones(kf.sum()), per); sf.update(feat=f, use="FILTRE", per=per); strats.append(sf)
        w = np.where(base[f].to_numpy(), 2.0, 1.0)
        ss = strat(base, w, per); ss.update(feat=f, use="BOYUT2", per=per); strats.append(ss)
        Fb = base[f].to_numpy(); rb = base.R.to_numpy()
        did, Pd, dlo, dhi = did_boot(e, f)
        pf = p1f(e, f)
        inb20 = np.isin(base.ent_day, list(b20)); inb50 = np.isin(base.ent_day, list(b50))
        tails.append(dict(per=per, feat=f, name=NAMES[f], rate_events=float(F.mean()), rate_1pos=float(Fb.mean()),
                          ortR_in=float(rb[Fb].mean()), ortR_out=float(rb[~Fb].mean()),
                          p3_in=float((rb[Fb] >= 3).mean()), p3_out=float((rb[~Fb] >= 3).mean()),
                          Rshare=float(rb[Fb].sum() / rb.sum()), tradeshare=float(Fb.mean()),
                          lift_b20=float(Fb[inb20].mean() / Fb.mean()) if Fb.mean() > 0 else np.nan,
                          lift_b50=float(Fb[inb50].mean() / Fb.mean()) if Fb.mean() > 0 else np.nan,
                          raw_in=float(e.R[F].mean()), raw_out=float(e.R[~F].mean()),
                          did=did, did_P=Pd, did_lo=dlo, did_hi=dhi, **pf))
        for u, k in (("FILTRE", j), ("BOYUT2", len(FEATS) + j)):
            nu = null[:, k]
            rows.append(dict(per=per, feat=f, name=NAMES[f], use=u, d=float(obs[k]),
                             null_mean=float(np.nanmean(nu)), null_sd=float(np.nanstd(nu)),
                             p_raw=float((np.nan_to_num(nu, nan=-9) >= obs[k]).mean())))
    # max-T
    mu, sd = np.nanmean(null, 0), np.nanstd(null, 0)
    zo = (obs - mu) / sd; zn = np.nanmax((null - mu) / sd, axis=1)
    for rr in rows[-len(obs):]:
        k = FEATS.index(rr["feat"]) + (0 if rr["use"] == "FILTRE" else len(FEATS))
        rr["z"] = float(zo[k]); rr["p_maxT"] = float((zn >= zo[k]).mean())
    # Holm (m=20)
    blk = rows[-len(obs):]
    order = np.argsort([x["p_raw"] for x in blk]); M = len(blk); run = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (M - rank) * blk[i]["p_raw"]); run = max(run, adj); blk[i]["p_holm"] = run

pd.DataFrame(rows).to_csv(os.path.join(RES, "tests.csv"), index=False)
pd.DataFrame(tails).to_csv(os.path.join(RES, "tail.csv"), index=False)
pd.DataFrame(strats).to_csv(os.path.join(RES, "strat.csv"), index=False)
json.dump(dict(thr9=thr9), open(os.path.join(RES, "params.json"), "w"))
ev.to_parquet(os.path.join(RES, "events.parquet"))
open(os.path.join(RES, "main.txt"), "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
