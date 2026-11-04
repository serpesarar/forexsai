"""Ana koşu: Dukascopy H1 2008-01 → 2026-06-16, 6 BUY kuralı × 3 geometri + SELL aynaları (kontrol).
Çıktı: results/cells.csv, results/yearly.csv, results/summary.txt, results/cells.json"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd
from mech import prep_h1, path_sim, one_position, day_boot_p, day_t
from rules import GEOM, DESC, events, holds

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.environ.get("RES_DIR", os.path.join(ROOT, "results")); os.makedirs(RES, exist_ok=True)
SPREAD_A, STRESS = 0.12, 1.5
END_MAIN = pd.Timestamp("2026-06-17", tz="UTC")
REPS = int(os.environ.get("REPS", "200"))


def load_main() -> pd.DataFrame:
    src = os.environ.get("H1_SRC", os.path.join(ROOT, "data", "duka_h1.parquet"))
    d = pd.read_parquet(src)
    if "open" in d.columns:
        d = d.rename(columns=dict(open="o", high="h", low="l", close="c"))
    if "spr" not in d.columns:
        d["spr"] = np.nan
    d["ts"] = pd.to_datetime(d.ts, utc=True)
    d = d[d.ts < END_MAIN][["ts", "o", "h", "l", "c", "spr"]]
    return prep_h1(d)


class Placebo:
    """P1 gün-kaydırma plasebosu: olay gününü aynı yıldan rastgele güne taşı, aynı UTC saati korunur
    (gün-içi kümelenme korunur). P2: aynı yıl+UTC saat+trend koşullu bağımsız bar."""

    def __init__(self, d: pd.DataFrame):
        self.d = d
        n = len(d); seg = d.seg.to_numpy(); atr = d.atr.to_numpy()
        valid = np.zeros(n, bool); valid[:-1] = (seg[1:] == seg[:-1]); valid &= np.isfinite(atr) & (atr > 0)
        self.valid = valid
        date = d.ts.dt.strftime("%Y-%m-%d").to_numpy(); uh = d.utc_h.to_numpy()
        self.dates = np.unique(date)
        self.dpos = {x: i for i, x in enumerate(self.dates)}
        grid = -np.ones((len(self.dates), 24), int)
        di = np.array([self.dpos[x] for x in date])
        grid[di, uh] = np.arange(n)
        grid[grid >= 0] = np.where(valid[grid[grid >= 0]], grid[grid >= 0], -1)
        self.grid = grid
        self.yr_of_date = np.array([int(x[:4]) for x in self.dates])
        self.dates_by_year = {y: np.where(self.yr_of_date == y)[0] for y in np.unique(self.yr_of_date)}
        self.year = d.year.to_numpy(); self.uh = uh

    def p1(self, ev: pd.DataFrame, rng) -> np.ndarray:
        """Dönüş: (len(ev),) yeni sig indeksleri (−1 = eşleşmedi)."""
        out = -np.ones(len(ev), int)
        ud = ev.date.unique()
        newd = {}
        for x in ud:
            pool = self.dates_by_year[int(x[:4])]
            newd[x] = pool[rng.integers(len(pool))]
        di = np.array([newd[x] for x in ev.date])
        out = self.grid[di, ev.utc_h.to_numpy()]
        return out

    def p2(self, ev: pd.DataFrame, rng, cond: np.ndarray) -> np.ndarray:
        out = -np.ones(len(ev), int)
        ok = self.valid & cond
        key = self.year * 100 + self.uh
        for k, idx in ev.groupby(ev.year * 100 + ev.utc_h).groups.items():
            pool = np.where(ok & (key == k))[0]
            if len(pool):
                out[np.asarray(idx)] = pool[rng.integers(len(pool), size=len(idx))]
        return out


def sim_cell(d, ev, tp, sl, hold, side, spread, **kw):
    O, H, L, C = (d[k].to_numpy() for k in "ohlc")
    seg = d.seg.to_numpy()
    hl = holds(d, ev.ent.to_numpy(), hold)
    m = hl > 0
    R = np.full(len(ev), np.nan); xi = np.full(len(ev), -1); code = np.full(len(ev), "", dtype="<U4")
    if m.any():
        sp = spread[m] if np.ndim(spread) else spread
        r, x, cd = path_sim(O, H, L, C, seg, ev.sig.to_numpy()[m], ev.ent.to_numpy()[m], ev.atr.to_numpy()[m],
                            hl[m], tp, sl, side, sp, **kw)
        R[m], xi[m], code[m] = r, x, cd
    return R, xi, code, hl


def placebo_means(d, P, ev, rule, tp, sl, hold, side, reps, rng, mode="p1"):
    """Plasebo ortR dağılımı (reps,)."""
    atr_h1 = d.atr.to_numpy()
    if rule == "R5":
        from rules import H4_atr_at
        atr_src = H4_atr_at(d, np.arange(len(d)))
    else:
        atr_src = atr_h1
    hl_ev = holds(d, ev.ent.to_numpy(), hold)
    cond = (d.trend_up if side > 0 else d.trend_dn).to_numpy() if rule != "R0" else np.ones(len(d), bool)
    out = np.empty(reps)
    O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy()
    for r in range(reps):
        s = P.p1(ev, rng) if mode == "p1" else P.p2(ev, rng, cond)
        ok = (s >= 0) & (hl_ev > 0)
        s2 = s[ok]; a = atr_src[s2]; ok2 = np.isfinite(a) & (a > 0)
        s2, a, hh = s2[ok2], a[ok2], hl_ev[ok][ok2]
        R, _, _ = path_sim(O, H, L, C, seg, s2, s2 + 1, a, hh, tp, sl, side, SPREAD_A)
        out[r] = np.nanmean(R)
    return out


def stats(R, ev, xi):
    m = ~np.isnan(R)
    R_, evm = R[m], ev[m]
    p, ci = day_boot_p(R_, evm.date.to_numpy())
    half = len(R_) // 2
    order = np.argsort(evm.sig.to_numpy(), kind="stable")
    Rs = R_[order]
    keep = one_position(evm.ent.to_numpy(), xi[m])
    return dict(n=int(m.sum()), wr=float((R_ > 0).mean()), ortR=float(R_.mean()), P=p, ci_lo=ci[0], ci_hi=ci[1],
                t=float(day_t(R_, evm.date.to_numpy())), h1=float(Rs[:half].mean()), h2=float(Rs[half:].mean()),
                n_1pos=int(keep.sum()), ortR_1pos=float(R_[keep].mean()),
                era_0815=float(R_[evm.year.to_numpy() <= 2015].mean()) if (evm.year <= 2015).any() else np.nan,
                n_0815=int((evm.year <= 2015).sum()),
                era_1626=float(R_[evm.year.to_numpy() >= 2016].mean()) if (evm.year >= 2016).any() else np.nan)


def main():
    d = load_main()
    print("bar", len(d), d.ts.min(), d.ts.max(), flush=True)
    P = Placebo(d)
    rng = np.random.default_rng(20261015)
    weeks = (d.ts.max() - d.ts.min()).days / 7
    rows, yearly, null_p1 = [], [], {}
    for rule in GEOM:
        for side in (+1, -1):
            ev = events(d, rule, side)
            spB = d.spr.to_numpy()[ev.ent.to_numpy()]
            spB = np.where(np.isfinite(spB), spB, np.nanmedian(d.spr))
            for gi, (tp, sl, hold) in enumerate(GEOM[rule]):
                cell = f"{rule}{'B' if side > 0 else 'S'}_G{gi+1}"
                R, xi, code, hl = sim_cell(d, ev, tp, sl, hold, side, SPREAD_A)
                Rst, *_ = sim_cell(d, ev, tp, sl, hold, side, SPREAD_A * STRESS)
                RB, *_ = sim_cell(d, ev, tp, sl, hold, side, spB)
                Ro, *_ = sim_cell(d, ev, tp, sl, hold, side, 0.0, optimistic=True)
                Rw, *_ = sim_cell(d, ev, tp, sl, hold, side, SPREAD_A, same_bar="win")
                st = stats(R, ev, xi)
                reps = REPS if side > 0 else max(REPS // 4, 30)
                p1 = placebo_means(d, P, ev, rule, tp, sl, hold, side, reps, rng, "p1")
                p2 = placebo_means(d, P, ev, rule, tp, sl, hold, side, max(reps // 2, 30), rng, "p2")
                null_p1[cell] = p1.tolist()
                be = sl / (sl + tp) if tp else np.nan
                row = dict(cell=cell, rule=rule, side="BUY" if side > 0 else "SELL",
                           tp=tp, sl=sl, hold=str(hold), **st,
                           per_week=st["n"] / weeks, be_wr=be,
                           ortR_stress=float(np.nanmean(Rst)), ortR_sprB=float(np.nanmean(RB)),
                           ortR_optim=float(np.nanmean(Ro)), ortR_samebarwin=float(np.nanmean(Rw)),
                           p1_mean=float(p1.mean()), p1_sd=float(p1.std()), p1_pct=float((p1 < st["ortR"]).mean()),
                           p2_mean=float(p2.mean()), p2_pct=float((p2 < st["ortR"]).mean()),
                           tp_rate=float((code == "TP").mean()), sl_rate=float((code == "SL").mean()),
                           med_hold=float(np.median(hl[hl > 0])) if (hl > 0).any() else np.nan,
                           sl_usd_med=float(np.median(ev.atr) * sl))
                rows.append(row)
                yy = pd.Series(R).groupby(ev.year.to_numpy()).agg(["mean", "size"])
                for y, (mu, k) in yy.iterrows():
                    yearly.append(dict(cell=cell, year=int(y), ortR=float(mu), n=int(k)))
                print(f"{cell:10} n={st['n']:6} ortR={st['ortR']:+.3f} P={st['P']:.2f} P1={p1.mean():+.3f}"
                      f" pct={row['p1_pct']:.2f} h={st['h1']:+.3f}/{st['h2']:+.3f} 08-15={st['era_0815']:+.3f}"
                      f" opt={row['ortR_optim']:+.3f} 1pos={st['ortR_1pos']:+.3f}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "cells.csv"), index=False)
    pd.DataFrame(yearly).to_csv(os.path.join(RES, "yearly.csv"), index=False)
    json.dump(null_p1, open(os.path.join(RES, "null_p1.json"), "w"))
    print("bitti")


if __name__ == "__main__":
    main()
