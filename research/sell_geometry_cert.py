"""
RESEARCH ONLY — certify the REAL hypothesis behind the SELL "rejection" result:
that an ENTRY-AGNOSTIC, empirically-sized tp/sl (TP=p33 of typical down-move,
SL=p50 of typical adverse rally) makes NDX/USOIL/GDAXI SELL broadly +EV — i.e.
the edge is the tp/sl GEOMETRY, not the rejection filter (which failed Placebo A).

This needs DISCRIMINATING tests, not just "EV>0":
  OOS    : derive tp/sl on TRAIN from ALL SELL signals' excursions; test first-touch
           EV on ALL TEST SELL signals, deduped, 3 temporal splits.
  FRICTION: 0/1/2x sweep + pooled bootstrap (R-units) P(EV>0) on split 05-20.
  PLACEBO C (direction): apply the SAME tp/sl magnitudes to BUY signals of the same
           symbol. If the edge is real downward-drift harvesting, SELL >> BUY. If
           BUY is also +EV, it's just tight-TP noise, not a directional edge.
  PLACEBO D (random clock): enter at RANDOM bar timestamps (no signal at all), same
           tp/sl. If still +EV, the "edge" is pure tp/sl mechanics + the period's
           drift, INDEPENDENT of the model — a regime bet, not a model edge.
  REFERENCE: bot's FIXED tp/sl on the same TEST SELL signals, for context.

Touches no production file.
"""
import sys, bisect, random, statistics as st
from datetime import timedelta

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import parse_iso, load_bars, _fnum, load_signals, replay_fixed
from sell_resistance_reaction import (quantile, excursion_pct, replay_pct_sell,
                                      dedup, wr_of, be_fric, ev_fric, FRIC_PCT, BOT_FIXED)
from buy_rejection_v2 import replay_pct_buy

random.seed(11)
SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]
SCOPES = ["NDX.INDX:SELL", "USOIL.FOREX:SELL", "GDAXI.INDX:SELL"]
TP_PCTL = 0.33
SL_PCTL = 0.50
NBOOT = 5000
NPLACEBO = 2000


def prep_dir(c, symbol, direction):
    bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
    sigs = load_signals(c, symbol, direction, SINCE)
    out = []
    for s in sigs:
        cat = parse_iso(s.get("created_at"))
        if cat is None: continue
        lo = bisect.bisect_left(tsk, cat)
        if lo >= len(bars): continue
        entry = bars[lo][1]
        if entry <= 0: continue
        out.append((cat, entry))
    out.sort(key=lambda x: x[0])
    return bars, tsk, out


def derive_geom(train, bars, tsk):
    mfes = []; maes = []
    for cat, entry in train:
        mfe, mae = excursion_pct(cat, entry, bars, tsk)
        if mfe is not None: mfes.append(mfe); maes.append(mae)
    if len(mfes) < 20: return None
    return round(quantile(mfes, TP_PCTL), 3), round(quantile(maes, SL_PCTL), 3)


def ev_of(trades, win_R):
    Rs = [win_R if t[1] == "WIN" else -1.0 for t in trades]
    return Rs


def main():
    c = get_supabase_client()
    split0 = parse_iso(SPLITS[0])
    pooled_obs = {}     # scope -> Rs on split 05-20 (SELL all-signal)

    for scope in SCOPES:
        symbol, _ = scope.rsplit(":", 1)
        fric = FRIC_PCT[scope]
        bars, tsk, sell = prep_dir(c, symbol, "SELL")
        print(f"\n{'='*80}\n{scope}  ({len(bars)} bars, {len(sell)} SELL signals)  fric≈{fric}%/side")

        for split_iso in SPLITS:
            sd = parse_iso(split_iso)
            train = [p for p in sell if p[0] < sd]
            test  = [p for p in sell if p[0] >= sd]
            g = derive_geom(train, bars, tsk)
            if g is None:
                print(f"  split {split_iso[5:10]}: too few train — skip"); continue
            tp, sl = g
            be = be_fric(tp, sl, fric); win_R = (tp - fric) / (sl + fric)
            cands = [(cat,) + replay_pct_sell(cat, e, tp, sl, bars, tsk) for cat, e in test]
            tr = dedup([(cat, res, ex) for (cat, res, ex) in cands]); wr, n = wr_of(tr)
            print(f"  split {split_iso[5:10]}: TP={tp}% SL={sl}% win {win_R:+.2f}R be {be*100:.1f}%  "
                  f"| ALL-SELL deduped n={n} WR={wr*100:.1f}% EV={ev_fric(wr,tp,sl,fric):+.3f}R "
                  f"{'+EV' if n and wr>be else '-EV'}")
            if split_iso == SPLITS[0]:
                pooled_obs[scope] = (ev_of(tr, win_R), tp, sl, win_R, test, bars, tsk, symbol, fric)
                for m in (0, 1, 2):
                    co = fric * m
                    print(f"      friction {m}x: be={be_fric(tp,sl,co)*100:.1f}% "
                          f"EV={ev_fric(wr,tp,sl,co):+.3f}R {'+EV' if wr>be_fric(tp,sl,co) else '-EV'}")
                # reference: bot fixed tp/sl on same test SELL signals
                bf = BOT_FIXED[scope]
                fcands = [(cat,) + replay_fixed(cat, e, "SELL", bf["tp"], bf["sl"], bf["is_pct"], bars, tsk)
                          for cat, e in test]
                ftr = dedup([(cat, res, ex) for (cat, res, ex) in fcands]); fwr, fn = wr_of(ftr)
                fbe = be_fric(bf["tp"], bf["sl"], 0)
                print(f"      [ref] BOT FIXED tp/sl deduped n={fn} WR={fwr*100:.1f}% be~{fbe*100:.1f}%")

    # ---------- pooled bootstrap (observed all-SELL) ----------
    allR = [x for v in pooled_obs.values() for x in v[0]]
    n = len(allR)
    print(f"\n{'#'*80}\nPOOLED ALL-SELL (split 05-20) n={n} meanEV={st.mean(allR):+.3f}R "
          f"wins={sum(1 for x in allR if x>0)}/{n}")
    boots = []
    for _ in range(NBOOT):
        s = [allR[random.randrange(n)] for _ in range(n)]
        boots.append(sum(s)/n)
    boots.sort()
    lo = boots[int(0.025*NBOOT)]; hi = boots[int(0.975*NBOOT)-1]
    pp = sum(1 for b in boots if b > 0)/NBOOT
    print(f"  bootstrap 95% CI [{lo:+.3f}R, {hi:+.3f}R] P(EV>0)={pp*100:.1f}%")

    # ---------- PLACEBO C: same tp/sl on BUY ----------
    print(f"\nPLACEBO C (direction) — same tp/sl magnitude on BUY signals:")
    buyR = []
    for scope, (_, tp, sl, win_R, _test, bars, tsk, symbol, fric) in pooled_obs.items():
        _, _, buy = prep_dir(c, symbol, "BUY")
        btest = [p for p in buy if p[0] >= split0]
        bc = [(cat,) + replay_pct_buy(cat, e, tp, sl, bars, tsk) for cat, e in btest]
        btr = dedup([(cat, res, ex) for (cat, res, ex) in bc]); bwr, bn = wr_of(btr)
        Rs = ev_of(btr, win_R); buyR.extend(Rs)
        print(f"  {scope[:-4]}BUY: tp={tp}% sl={sl}% deduped n={bn} WR={bwr*100:.1f}% "
              f"meanEV={st.mean(Rs) if Rs else 0:+.3f}R")
    print(f"  >>> POOLED BUY n={len(buyR)} meanEV={st.mean(buyR) if buyR else 0:+.3f}R  "
          f"(want << SELL's {st.mean(allR):+.3f}R if edge is directional)")

    # ---------- PLACEBO D: random clock entries ----------
    print(f"\nPLACEBO D (random clock) — enter SELL at random bar times, same tp/sl:")
    rand_means = []
    for scope, (obsR, tp, sl, win_R, test, bars, tsk, symbol, fric) in pooled_obs.items():
        # restrict to bars in the test time range
        t0 = test[0][0]; idx0 = bisect.bisect_left([b[0] for b in bars], t0)
        pool_idx = list(range(idx0, len(bars) - 1))
        rn = len(obsR)
        scope_means = []
        for _ in range(NPLACEBO):
            pick = random.sample(pool_idx, min(rn, len(pool_idx)))
            rc = []
            for i in pick:
                ts, o, h, l, cl = bars[i]
                rc.append((ts,) + replay_pct_sell(ts, o, tp, sl, bars, tsk))
            rtr = dedup([(cat, res, ex) for (cat, res, ex) in rc])
            rR = ev_of(rtr, win_R)
            if rR: scope_means.append(st.mean(rR))
        m = st.mean(scope_means) if scope_means else 0.0
        rand_means.append((scope, m))
        print(f"  {scope}: random-clock meanEV≈{m:+.3f}R  vs observed {st.mean(obsR):+.3f}R")
    print(f"  >>> if random-clock ≈ observed, the edge is tp/sl mechanics + drift, "
          f"NOT the model/signal.")


if __name__ == "__main__":
    main()
