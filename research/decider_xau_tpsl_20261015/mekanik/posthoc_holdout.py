"""POST-HOC KEŞİF (verdikt DEĞİL): broker kasasında (2026-06-17→10-14) R0B_G1 ve R4B_G3 için
(1) aynı P1 gün-kaydırma plasebosu (kasa günleri içinde, aynı UTC saati, aynı tutma; broker H1 yolu),
(2) tek-pozisyon sürümü, (3) güncel ATR → $ dönüşümü. Çıktı: results/posthoc_holdout.txt"""
from __future__ import annotations
import os
import numpy as np, pandas as pd
from mech import prep_h1, path_sim, one_position, day_boot_p
from rules import GEOM, events, holds
from run_main import Placebo
from holdout import broker_1m, broker_h1, CUT

ROOT = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(ROOT, "results")
SP = 0.12
out = []


def say(s=""):
    print(s, flush=True); out.append(s)


def main():
    du = pd.read_parquet(os.path.join(ROOT, "data", "duka_h1.parquet")); du["ts"] = pd.to_datetime(du.ts, utc=True)
    bh = broker_h1(broker_1m())
    d = prep_h1(pd.concat([du[du.ts < CUT][["ts", "o", "h", "l", "c"]], bh[bh.ts >= CUT][["ts", "o", "h", "l", "c"]]]))
    hts = d.ts.dt.tz_convert(None).to_numpy(); cut = np.datetime64(CUT.tz_convert(None))
    P = Placebo(d)
    hold_dates = np.where(P.dates >= str(CUT.date()))[0]
    P.dates_by_year[2026] = hold_dates  # plasebo yalnız kasa günlerinden çeker
    O, H, L, C = (d[k].to_numpy() for k in "ohlc"); seg = d.seg.to_numpy()
    rng = np.random.default_rng(99)
    weeks = (hts[-1] - cut) / np.timedelta64(7, "D")
    say(f"Kasa: {CUT.date()} → {d.ts.max()}  ({weeks:.1f} hafta), broker H1 yolu, spread ${SP}")
    for rule, gi in (("R0", 0), ("R4", 2), ("R0", 2)):
        tp, sl, hold = GEOM[rule][gi]
        ev = events(d, rule, +1); ev = ev[hts[ev.sig.to_numpy()] >= cut].reset_index(drop=True)
        hl = holds(d, ev.ent.to_numpy(), hold)
        R, xi, code = path_sim(O, H, L, C, seg, ev.sig.to_numpy(), ev.ent.to_numpy(), ev.atr.to_numpy(), hl, tp, sl, +1, SP)
        k = one_position(ev.ent.to_numpy(), xi)
        pm, pk = [], []
        for _ in range(500):
            s = P.p1(ev, rng); ok = s >= 0; s2 = s[ok]; a = d.atr.to_numpy()[s2]; hh = hl[ok]
            Rp, xp, _ = path_sim(O, H, L, C, seg, s2, s2 + 1, a, hh, tp, sl, +1, SP)
            pm.append(np.nanmean(Rp)); kk = one_position(s2 + 1, xp); pk.append(np.nanmean(Rp[kk]))
        pm, pk = np.array(pm), np.array(pk)
        p, ci = day_boot_p(R, ev.date.to_numpy(), n=2000)
        sl_usd = ev.atr.to_numpy() * sl
        say(f"\n{rule}B_G{gi+1}: n={len(R)} ortR {np.nanmean(R):+.3f} [%95 {ci[0]:+.2f},{ci[1]:+.2f}] P {p:.2f} | P1 kasa {pm.mean():+.3f} "
            f"fark {np.nanmean(R) - pm.mean():+.3f} yüzdelik {(pm < np.nanmean(R)).mean():.2f}")
        say(f"  tek-poz: n={k.sum()} ({k.sum()/weeks:.1f}/hafta) ortR {np.nanmean(R[k]):+.3f} vs tek-poz P1 {pk.mean():+.3f} "
            f"yüzdelik {(pk < np.nanmean(R[k])).mean():.2f}; toplam {np.nansum(R[k]):+.1f}R")
        say(f"  SL$ (={sl}×ATR_H1) medyan {np.median(sl_usd):.2f}$ [p10 {np.percentile(sl_usd,10):.2f}, p90 {np.percentile(sl_usd,90):.2f}] "
            f"→ 0,01 lot (1 ons) beklenen $/işlem = ortR×SL$ ≈ {np.nanmean(R[k]) * np.median(sl_usd):+.2f}$")
        say(f"  çıkış kodları: " + str(pd.Series(code).value_counts().to_dict()))
    open(os.path.join(RES, "posthoc_holdout.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
