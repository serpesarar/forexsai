"""Aday hücrelerin ek stres testleri (yalnız BUY): sıra-bağımlı (aynı anda tek pozisyon), spread×1.5,
giriş +1 dk gecikme, haftalık tutarlılık, tek-hafta-dışarıda (LOWO), model epoku, ATR tabanı (journal ATR).
Çıktı: results/candidates.txt"""
import numpy as np
import pandas as pd
import core

HERE = core.HERE; OUT = HERE / "results"
A = pd.read_pickle(HERE / "data" / "grid_set.pkl")
A = A[A.direction == "BUY"].reset_index(drop=True)
P = core.Paths(core.load_1m())
CANDS = [("orijinal", None, None), ("ATR tp1.0/sl0.75", 1.0, 0.75), ("ATR tp1.25/sl0.75", 1.25, 0.75),
         ("ATR tp1.5/sl0.75", 1.5, 0.75), ("ATR tp1.25/sl1.0", 1.25, 1.0), ("ATR tp1.25/sl1.5", 1.25, 1.5)]
L = []


def run(spread_mult=1.0, delay=0, atr_col="atr_m5"):
    """Dönüş: pnl, risk, çıkış zamanı [N, C]."""
    N = len(A); pnl = np.zeros((N, len(CANDS))); risk = np.zeros_like(pnl); ext = np.empty((N, len(CANDS)), dtype="datetime64[ns]")
    for n, x in enumerate(A.itertuples(index=False)):
        i0 = int(x.path_i0) + delay
        s = x.spread_used * spread_mult
        e = (P.o[i0] + s) if not x.executed or delay or spread_mult != 1.0 else x.entry_price
        if x.executed and spread_mult != 1.0 and not delay:
            e = x.entry_price + (spread_mult - 1) * x.spread_used
        w = P.window(i0, core.MAX_HOLD_MIN); h, l, c, t = P.h[w], P.l[w], P.c[w], P.t[w]
        a = getattr(x, atr_col)
        for k, (_, tp, sl) in enumerate(CANDS):
            tp_d = x.orig_tp_usd if tp is None else tp * a
            sl_d = x.orig_sl_usd if sl is None else sl * a
            p, code, ex = core.sim_grid("BUY", e, s, h, l, c, np.array([tp_d]), np.array([sl_d]))
            pnl[n, k], risk[n, k], ext[n, k] = p[0, 0], sl_d, t[int(ex[0, 0])]
    return pnl, risk, ext


def boot_day(R, days, B=3000, seed=3):
    rng = np.random.default_rng(seed); u, inv = np.unique(days, return_inverse=True)
    S = np.zeros((len(u), R.shape[1])); np.add.at(S, inv, R); Cn = np.bincount(inv).astype(float)
    W = rng.multinomial(len(u), np.ones(len(u)) / len(u), size=B).astype(float)
    m = (W @ S) / (W @ Cn)[:, None]
    return m


base_pnl, base_risk, base_ext = run()
R = base_pnl / base_risk
days = A.day.values
L.append(f"BUY n={len(A)}")
L.append("Hücre | EV_R | WR | P(EV>0) gün-boot | spread×1.5 EV_R | +1dk gecikme EV_R | journal-ATR tabanı EV_R")
s15 = run(spread_mult=1.5); d1 = run(delay=1); ja = run(atr_col="j_atr5")
bt = boot_day(R, days)
for k, (nm, _, _) in enumerate(CANDS):
    L.append(f"  {nm:20s} {R[:, k].mean():+.3f} | {(base_pnl[:, k] > 0).mean():.3f} | {(bt[:, k] > 0).mean():.2f} | "
             f"{(s15[0][:, k] / s15[1][:, k]).mean():+.3f} | {(d1[0][:, k] / d1[1][:, k]).mean():+.3f} | {(ja[0][:, k] / ja[1][:, k]).mean():+.3f}")

# sıra-bağımlı: aynı anda tek pozisyon (her hücre kendi çıkış zamanıyla)
L.append("\nSıra-bağımlı (önceki pozisyon kapanmadan yeni karar alınmaz):")
ent = A.path_start_utc.values.astype("datetime64[ns]")
for k, (nm, _, _) in enumerate(CANDS):
    keep, busy = [], np.datetime64("1970-01-01")
    for n in range(len(A)):
        if ent[n] > busy:
            keep.append(n); busy = base_ext[n, k]
    keep = np.array(keep); r = R[keep, k]
    b = boot_day(r[:, None], days[keep])[:, 0]
    tt = ent[keep]; cut = np.quantile(tt.astype("int64"), .5).astype("datetime64[ns]")
    L.append(f"  {nm:20s} n={len(keep)} EV_R={r.mean():+.3f} WR={(base_pnl[keep, k] > 0).mean():.3f} P(EV>0)={np.mean(b > 0):.2f} "
             f"H1={r[tt < cut].mean():+.3f} H2={r[tt >= cut].mean():+.3f} | $ /0.01lot ort={base_pnl[keep, k].mean():+.3f}")

# haftalık tutarlılık + LOWO
wk = A.decision_time_utc.dt.strftime("%G-W%V").values
L.append("\nHaftalık EV_R (n) — aday tp1.25/sl0.75 ve orijinal:")
for w in sorted(set(wk)):
    m = wk == w
    L.append(f"  {w}: n={m.sum():3d} orij {R[m, 0].mean():+.3f} | tp1.25/sl0.75 {R[m, 2].mean():+.3f} | tp1.25/sl1.0 {R[m, 4].mean():+.3f}")
for k in (0, 2, 4):
    pos = np.mean([R[wk == w, k].mean() > 0 for w in set(wk)])
    lowo = [R[wk != w, k].mean() for w in set(wk)]
    L.append(f"  {CANDS[k][0]}: pozitif hafta oranı {pos:.0%} | tek-hafta-dışarıda EV aralığı [{min(lowo):+.3f}, {max(lowo):+.3f}]")
L.append("\nModel epoku (tp1.25/sl0.75 | orijinal):")
for mdl, g in A.groupby("model"):
    L.append(f"  {mdl:20s} n={len(g):3d} {R[g.index, 2].mean():+.3f} | {R[g.index, 0].mean():+.3f}")
(OUT / "candidates.txt").write_text("\n".join(L))
print("\n".join(L))
