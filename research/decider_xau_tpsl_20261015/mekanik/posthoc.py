"""POST-HOC KEŞİF (PROTOCOL.md'de YOK; verdikti DEĞİŞTİRMEZ, yalnız yorumlar). 2026-10-15, ana sonuçlar görüldükten SONRA.
Sorular: (a) kuralın sürüklenmeyi aşan kısmı (kural − P1) yıl/çağ bazında nerede? (b) tek-pozisyon sürümü KENDİ
plasebosunu geçiyor mu? (c) en iyi 5/20 gün çıkınca ne kalıyor? (d) Duka gerçek spread'iyle (B) plaseboya göre fark?
(e) broker kasasında (2026-06-17→10-14) aynı P1 plasebosuna göre konum. (f) karar anı → $ dönüşümü (güncel ATR).
Çıktı: results/posthoc.txt"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd
from mech import path_sim, one_position, prep_h1, day_boot_p
from rules import GEOM, events, holds
from run_main import load_main, Placebo, sim_cell, placebo_means, SPREAD_A

ROOT = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(ROOT, "results")
CELLS = [("R0", 0), ("R4", 2), ("R3", 0), ("R5", 0), ("R1", 0)]  # G indeksleri (0-tabanlı)
REPS = 200
out: list[str] = []


def say(s: str = "") -> None:
    print(s, flush=True); out.append(s)


def cellname(rule, gi):
    return f"{rule}B_G{gi+1}"


def excess_by_group(d, P, ev, R, rule, tp, sl, hold, key, rng):
    rows = []
    for g, idx in ev.groupby(key).groups.items():
        idx = np.asarray(idx)
        e = ev.loc[idx].reset_index(drop=True)
        if len(e) < 30:
            continue
        pm = placebo_means(d, P, e, rule, tp, sl, hold, +1, REPS, rng, "p1")
        r = np.nanmean(R[idx])
        rows.append(dict(grup=g, n=len(e), ortR=r, p1=pm.mean(), fark=r - pm.mean(), pct=(pm < r).mean()))
    return pd.DataFrame(rows)


def onepos_placebo(d, P, ev, rule, tp, sl, hold, rng, reps=REPS):
    """Tek-pozisyon kısıtını plasebo olaylarına da uygula (adil kıyas)."""
    from rules import H4_atr_at
    atr_src = H4_atr_at(d, np.arange(len(d))) if rule == "R5" else d.atr.to_numpy()
    O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy()
    hl_ev = holds(d, ev.ent.to_numpy(), hold)
    res = np.empty(reps); ns = np.empty(reps)
    for r in range(reps):
        s = P.p1(ev, rng); ok = (s >= 0) & (hl_ev > 0)
        s2 = s[ok]; a = atr_src[s2]; ok2 = np.isfinite(a) & (a > 0)
        s2, a, hh = s2[ok2], a[ok2], hl_ev[ok][ok2]
        Rp, xi, _ = path_sim(O, H, L, C, seg, s2, s2 + 1, a, hh, tp, sl, +1, SPREAD_A)
        k = one_position(s2 + 1, xi)
        res[r] = np.nanmean(Rp[k]); ns[r] = k.sum()
    return res, ns


def main():
    d = load_main(); P = Placebo(d); rng = np.random.default_rng(777)
    say("POST-HOC KEŞİF — verdikt DEĞİL. P1 = gün-kaydırma plasebosu (aynı yıl, aynı UTC saati, aynı tutma), 200 tekrar.")
    for rule, gi in CELLS:
        tp, sl, hold = GEOM[rule][gi]
        ev = events(d, rule, +1)
        R, xi, code, hl = sim_cell(d, ev, tp, sl, hold, +1, SPREAD_A)
        m = np.isfinite(R)
        say(f"\n=== {cellname(rule, gi)}  (tp={tp}, sl={sl}, hold={hold}) n={m.sum()} ortR={np.nanmean(R):+.3f}")
        # (a) çağ ve yıl bazında sürüklenme-üstü fark
        ev2 = ev.assign(era=np.where(ev.year <= 2015, "2008-15", "2016-26"))
        E = excess_by_group(d, P, ev2, R, rule, tp, sl, hold, "era", rng)
        say("  çağ: " + " | ".join(f"{r.grup}: n={r.n} ortR {r.ortR:+.3f} P1 {r.p1:+.3f} fark {r.fark:+.3f} yüzdelik {r.pct:.2f}" for r in E.itertuples()))
        Y = excess_by_group(d, P, ev, R, rule, tp, sl, hold, "year", rng)
        say("  yıl (fark = kural − P1): " + " ".join(f"{int(r.grup)}:{r.fark:+.2f}" for r in Y.itertuples()))
        say(f"  fark>0 olan yıl: {(Y.fark > 0).sum()}/{len(Y)}; yıllık farkların medyanı {Y.fark.median():+.3f}")
        # (b) tek pozisyon vs kendi plasebosu
        k = one_position(ev.ent.to_numpy()[m], xi[m])
        r1 = np.nanmean(R[m][k])
        pm1, ns = onepos_placebo(d, P, ev, rule, tp, sl, hold, rng)
        weeks = (d.ts.max() - d.ts.min()).days / 7
        say(f"  tek-poz: n={k.sum()} ({k.sum()/weeks:.2f}/hafta) ortR {r1:+.3f} vs tek-poz P1 {pm1.mean():+.3f} (n≈{ns.mean():.0f}) "
            f"yüzdelik {(pm1 < r1).mean():.2f}")
        # (c) en iyi günleri çıkar
        day = ev.date.to_numpy()[m]; Rm = R[m]
        s = pd.Series(Rm).groupby(day).sum().sort_values(ascending=False)
        for kk in (5, 20):
            drop = set(s.index[:kk]); keep = ~np.isin(day, list(drop))
            say(f"  en iyi {kk} gün hariç: ortR {Rm[keep].mean():+.3f} (n={keep.sum()}); en iyi {kk} günün payı toplam R'nin "
                f"%{100*s.iloc[:kk].sum()/Rm.sum():.0f}'i")
        # (d) spread B ile plaseboya göre
        spB = d.spr.to_numpy()
        spB = np.where(np.isfinite(spB), spB, np.nanmedian(spB))
        RB, *_ = sim_cell(d, ev, tp, sl, hold, +1, spB[ev.ent.to_numpy()])
        # plasebo aynı spread modeliyle: olay başına rastgele barın kendi Duka spread'i
        from rules import H4_atr_at
        atr_src = H4_atr_at(d, np.arange(len(d))) if rule == "R5" else d.atr.to_numpy()
        O, H, L, C = (d[k_].to_numpy() for k_ in "ohlc"); seg = d.seg.to_numpy()
        hl_ev = holds(d, ev.ent.to_numpy(), hold); pb = []
        for _ in range(100):
            s_ = P.p1(ev, rng); ok = (s_ >= 0) & (hl_ev > 0); s2 = s_[ok]; a = atr_src[s2]; ok2 = np.isfinite(a) & (a > 0)
            s2, a, hh = s2[ok2], a[ok2], hl_ev[ok][ok2]
            Rp, _, _ = path_sim(O, H, L, C, seg, s2, s2 + 1, a, hh, tp, sl, +1, spB[s2 + 1]); pb.append(np.nanmean(Rp))
        pb = np.array(pb)
        say(f"  spread B (Duka gerçek ask−bid, medyan ${np.nanmedian(spB[ev.ent]):.2f}): ortR {np.nanmean(RB):+.3f} vs P1(B) {pb.mean():+.3f} "
            f"fark {np.nanmean(RB) - pb.mean():+.3f} yüzdelik {(pb < np.nanmean(RB)).mean():.2f}")
    open(os.path.join(RES, "posthoc.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
