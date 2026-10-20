"""Q4: aşırı-uyum kontrolleri.
 (a) Kronolojik iki yarı: her hücrenin EV_R'si H1 ve H2'de; H1'de seçilen en iyi hücrenin H2 değeri (ve tersi).
 (b) Rastgele-giriş plasebosu: her decider işlemi için aynı yön + aynı gün-içi saat, dönem içinden rastgele
     gün (K tekrar). Giriş = o dakikadan sonraki 1m açılış + aynı spread; ATR kapalı barlardan. Plasebo
     aynı ızgarada koşulur → "geometri kenarı decider girişinden bağımsız mı?"
 (c) Çoklu sınama: test edilen hücre sayısı; Bonferroni z; White Reality Check (gün-kümeli, merkezlenmiş
     bootstrap ile max-EV istatistiği) + plasebo setlerinde ızgara-maksimumu dağılımı.
Çıktı: results/robust_summary.txt, results/halves_<grup>.csv, results/placebo_<grup>.csv"""
import numpy as np
import pandas as pd
import core, grid_lib as G
from scipy_free import norm_ppf

HERE = core.HERE; OUT = HERE / "results"
K_PLACEBO = 30
SEED = 20261015
A = pd.read_pickle(HERE / "data" / "grid_set.pkl")
C = np.load(HERE / "data" / "grid_cache_all.npz")
PR = np.load(HERE / "data" / "path_cache.npz", allow_pickle=True)
risks = G.risk_arrays(A)
FAMS = ["atr", "usd", "scale", "time_only", "time_sl", "orig_cap"]
AXN = {"atr": lambda i, j: f"ATR tp{G.TP_ATR[i]}/sl{G.SL_ATR[j]}", "usd": lambda i, j: f"$ tp{G.TP_USD[i]:g}/sl{G.SL_USD[j]:g}",
       "scale": lambda i, j: f"orij× tp{G.TP_SCALE[i]}/sl{G.SL_SCALE[j]}", "time_sl": lambda i, j: f"süre{G.TIME_H[i]}dk+sl{G.TIME_SL_ATR[j]}ATR",
       "time_only": lambda i: f"yalnız süre {G.TIME_H[i]}dk (R=1ATR)", "orig_cap": lambda i: f"orij TP/SL + {G.TIME_H[i]}dk tavan"}


def all_cells(idx: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Seçili işlemler için TÜM hücrelerin R matrisi [n, M] ve adları."""
    mats, names = [], []
    for f in FAMS:
        R = (C[f][idx] / risks[f][idx])
        shp = R.shape[1:]
        mats.append(R.reshape(len(idx), -1))
        for flat in range(int(np.prod(shp))):
            ij = np.unravel_index(flat, shp)
            names.append(AXN[f](*ij))
    R = PR["pnl"][idx] / PR["risk"][idx]
    mats.append(R); names += [f"yol: {n}" for n in PR["names"]]
    return np.concatenate(mats, axis=1), names


L = []
def P(s=""): L.append(str(s))
groups = {"BUY": (A.direction == "BUY").values, "SELL": (A.direction == "SELL").values,
          "BUY_rr067": ((A.direction == "BUY") & (A.j_rr.round(2) == 0.67)).values, "BUY_exec": A.executed.values}
best_cells = {}
for g, m in groups.items():
    idx = np.where(m)[0]
    R, names = all_cells(idx)
    M = R.shape[1]
    days = A.day.values[idx]
    ev = R.mean(0)
    boot = G.day_boot(R, days, B=3000, seed=1)
    se = boot.std(0, ddof=1)
    t = ev / se
    b = int(np.nanargmax(ev))
    # White RC: merkezlenmiş bootstrap max
    mx = np.nanmax(boot - ev[None, :], axis=1)
    p_rc = float(np.mean(mx >= ev[b]))
    z_bonf = norm_ppf(1 - 0.05 / M)
    # yarılar
    tt = A.decision_time_utc.values[idx]
    cut = np.quantile(tt.astype("int64"), 0.5).astype("datetime64[ns]")
    h1, h2 = tt < cut, tt >= cut
    e1, e2 = R[h1].mean(0), R[h2].mean(0)
    both = (e1 > 0) & (e2 > 0)
    b1, b2 = int(np.nanargmax(e1)), int(np.nanargmax(e2))
    pd.DataFrame({"cell": names, "EV_R": ev, "se_day": se, "t": t, "EV_H1": e1, "EV_H2": e2}).to_csv(OUT / f"halves_{g}.csv", index=False)
    P(f"\n=== {g}: n={len(idx)} gün={len(set(days))} | test edilen hücre M={M}")
    P(f"  En iyi hücre (tüm örnek): {names[b]}  EV_R={ev[b]:+.3f}  se(gün)={se[b]:.3f}  t={t[b]:.2f} | Bonferroni z*={z_bonf:.2f} → {'GEÇER' if t[b] > z_bonf else 'GEÇMEZ'} | White RC p={p_rc:.3f}")
    P(f"     yarılar: H1={e1[b]:+.3f} (n={h1.sum()}, {pd.Timestamp(tt[h1].min()):%m-%d}→{pd.Timestamp(tt[h1].max()):%m-%d}) | H2={e2[b]:+.3f} (n={h2.sum()}, →{pd.Timestamp(tt[h2].max()):%m-%d})")
    P(f"  H1'de seçilen en iyi: {names[b1]} H1={e1[b1]:+.3f} → H2={e2[b1]:+.3f} | H2'de seçilen: {names[b2]} H2={e2[b2]:+.3f} → H1={e1[b2]:+.3f}")
    P(f"  Her iki yarıda >0 olan hücre: {int(both.sum())}/{M}  (EV_R>0 tüm örnekte: {int((ev>0).sum())})")
    orig_k = names.index("orij× tp1.0/sl1.0")
    P(f"  Orijinal: EV_R={ev[orig_k]:+.3f} t={t[orig_k]:.2f} H1={e1[orig_k]:+.3f} H2={e2[orig_k]:+.3f}")
    top = np.argsort(-np.where(both, np.minimum(e1, e2), -9))[:8]
    P("  İki yarıda da pozitif, min(H1,H2)'ye göre ilk 8:")
    for k in top:
        if both[k]:
            P(f"     {names[k]:45s} EV={ev[k]:+.3f} H1={e1[k]:+.3f} H2={e2[k]:+.3f} t={t[k]:.2f}")
    best_cells[g] = (names, ev, idx)

# ── (b) plasebo ──
b1 = core.load_1m(); Pth = core.Paths(b1)
r5 = core.resample(b1, "5min")
rng = np.random.default_rng(SEED)
tdays = pd.DatetimeIndex(sorted(set(b1.t_utc.dt.normalize())))
tdays = tdays[(tdays >= A.decision_time_utc.min().normalize()) & (tdays <= A.decision_time_utc.max().normalize() - pd.Timedelta(days=2))]


def gap_free(i0: int) -> bool:
    w = Pth.window(i0, 240); tt = Pth.t[w]
    if len(tt) < 2:
        return False
    gaps = np.diff(tt).astype("timedelta64[m]").astype(int)
    hrs = pd.DatetimeIndex(tt[:-1]).hour
    return not np.any((gaps > 5) & (np.asarray(hrs) != 20))


def make_placebo(sub: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for x in sub.itertuples(index=False):
        tod = x.decision_time_utc - x.decision_time_utc.normalize()
        for _ in range(50):
            day = tdays[rng.integers(len(tdays))]
            t0 = (day + tod).floor("min") + pd.Timedelta(minutes=1)
            i0 = Pth.first_idx_at_or_after(t0)
            if i0 >= len(Pth.t) or (pd.Timestamp(Pth.t[i0], tz="UTC") - t0) > pd.Timedelta(minutes=5) or not gap_free(i0):
                continue
            te = pd.Timestamp(Pth.t[i0], tz="UTC")
            a = core.atr_closed(r5, te)
            if not a:
                continue
            e = Pth.o[i0] + (x.spread_used if x.direction == "BUY" else 0.0)
            rows.append({"direction": x.direction, "entry_price": e, "spread_used": x.spread_used, "path_i0": i0,
                         "atr_m5": a, "orig_sl_usd": x.orig_sl_atr5 * a, "orig_tp_usd": x.orig_tp_atr5 * a,
                         "day": te.strftime("%Y-%m-%d"), "t": te})
            break
    return pd.DataFrame(rows)


for g in ("BUY", "SELL"):
    names, ev, idx = best_cells[g]
    sub = A.iloc[idx]
    reps = []
    for k in range(K_PLACEBO):
        pl = make_placebo(sub)
        cc = G.cells_fixed(pl, Pth); rr = G.risk_arrays(pl)
        mats = [(cc[f] / rr[f]).reshape(len(pl), -1) for f in FAMS]
        reps.append(np.concatenate(mats, axis=1).mean(0))
    reps = np.array(reps)                       # [K, M_fixed]
    Mf = reps.shape[1]
    evf = ev[:Mf]
    pct = (reps < evf[None, :]).mean(0)
    dfp = pd.DataFrame({"cell": names[:Mf], "EV_decider": evf, "EV_placebo_mean": reps.mean(0),
                        "EV_placebo_sd": reps.std(0, ddof=1), "decider_pctile_in_placebo": pct})
    dfp["diff"] = dfp.EV_decider - dfp.EV_placebo_mean
    dfp.to_csv(OUT / f"placebo_{g}.csv", index=False)
    pmax = reps.max(1)
    P(f"\n=== PLASEBO {g}: K={K_PLACEBO} rastgele-giriş seti × n≈{len(sub)} (aynı yön, aynı gün-içi saat, rastgele gün)")
    P(f"  Plasebo hücre-ortalaması EV_R: medyan {np.median(reps.mean(0)):+.3f}; EV>0 olan hücre oranı (ort.) {np.mean(reps > 0):.1%}")
    P(f"  Plasebo setlerinde ızgara-maksimumu EV_R: medyan {np.median(pmax):+.3f}, %90 {np.quantile(pmax, .9):+.3f}, max {pmax.max():+.3f}"
      f" | decider sabit-hücre maksimumu {evf.max():+.3f} → plasebo maksimumlarının {np.mean(pmax < evf.max()):.0%}'inden büyük")
    o = dfp[dfp.cell == "orij× tp1.0/sl1.0"].iloc[0]
    P(f"  Orijinal geometri: decider {o.EV_decider:+.3f} vs plasebo {o.EV_placebo_mean:+.3f} (sd {o.EV_placebo_sd:.3f}) → yüzdelik {o.decider_pctile_in_placebo:.0%}")
    P("  Decider − plasebo farkı en büyük 8 hücre (ve decider'ın plasebo dağılımındaki yüzdeliği):")
    for r in dfp.sort_values("diff", ascending=False).head(8).itertuples():
        P(f"     {r.cell:42s} decider {r.EV_decider:+.3f} plasebo {r.EV_placebo_mean:+.3f}±{r.EV_placebo_sd:.3f} yüzdelik {r.decider_pctile_in_placebo:.0%}")
    for nm in ("yalnız süre 120dk (R=1ATR)", "yalnız süre 240dk (R=1ATR)", "ATR tp1.25/sl0.75", "ATR tp1.5/sl0.75"):
        r = dfp[dfp.cell == nm].iloc[0]
        P(f"  {nm:40s} decider {r.EV_decider:+.3f} | plasebo {r.EV_placebo_mean:+.3f}±{r.EV_placebo_sd:.3f} | yüzdelik {r.decider_pctile_in_placebo:.0%}")
(OUT / "robust_summary.txt").write_text("\n".join(L))
print("\n".join(L))
