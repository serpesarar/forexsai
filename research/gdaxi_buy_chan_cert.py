"""
RESEARCH ONLY — focused certification for GDAXI.INDX:BUY, CHAN variant (reject
off the LOWER trend-channel band + bullish turn), with the derived reduced tp/sl.

The pooled BUY re-test (buy_rejection_v2.py) did NOT clear the bar as a group
(P(EV>0)≈76-77%), but GDAXI:BUY CHAN was +EV on all 3 splits with real per-LOG
filter separation. This script certifies THAT scope alone the same way the
momentum edge was certified:

  1. derive tp/sl BLIND on TRAIN, replay the longest held-out window (split 05-20)
  2. dedup to real trades -> deduped WR, EV, bootstrap 95% CI + P(EV>0)
  3. friction sweep 0/1/2x
  4. PLACEBO A (random entry): same count of RANDOM entry timestamps from the
     full test pool, same tp/sl -> null EV distribution. p = P(placebo >= observed)
  5. PLACEBO B (label shuffle): shuffle the is-reaction labels across test logs,
     recompute reaction per-LOG WR -> null WR distribution.
  6. consistency: print the other two splits too.

Touches no production file.
"""
import sys, bisect, random, statistics as st

sys.path.insert(0, "backend")
sys.path.insert(0, "research")
from dotenv import load_dotenv
load_dotenv("backend/.env"); load_dotenv(".env")
from database.supabase_client import get_supabase_client
from bot_fixed_tpsl_replay import parse_iso, load_bars, _fnum, load_signals
from sell_resistance_reaction import quantile, dedup, wr_of, be_fric, ev_fric
from buy_rejection_v2 import (excursion_buy, replay_pct_buy, variant_pass,
                              derive_thr, TP_PCTL, SL_PCTL)

random.seed(11)
SCOPE = "GDAXI.INDX:BUY"
VARIANT = "CHAN"
FRIC = 0.006
SINCE = "2026-04-25T00:00:00+00:00"
SPLITS = ["2026-05-20T00:00:00+00:00",
          "2026-05-27T00:00:00+00:00",
          "2026-06-03T00:00:00+00:00"]
NBOOT = 5000
NPLACEBO = 5000


def prep(c):
    symbol, direction = SCOPE.rsplit(":", 1)
    bars = load_bars(c, symbol); tsk = [b[0] for b in bars]
    sigs = load_signals(c, symbol, direction, SINCE)
    prepped = []
    for s in sigs:
        cat = parse_iso(s.get("created_at"))
        if cat is None: continue
        lo = bisect.bisect_left(tsk, cat)
        if lo >= len(bars): continue
        entry = bars[lo][1]
        if entry <= 0: continue
        prepped.append((cat, entry, s.get("factors") or {}))
    prepped.sort(key=lambda x: x[0])
    return bars, tsk, prepped


def derive(train, bars, tsk):
    thr = derive_thr(VARIANT, train)
    mfes = []; maes = []
    for cat, entry, f in train:
        if not variant_pass(VARIANT, f, thr): continue
        mfe, mae = excursion_buy(cat, entry, bars, tsk)
        if mfe is not None: mfes.append(mfe); maes.append(mae)
    if len(mfes) < 8:
        return None
    tp = round(quantile(mfes, TP_PCTL), 3)
    sl = round(quantile(maes, SL_PCTL), 3)
    return thr, tp, sl


def replay_all(test, tp, sl, bars, tsk):
    """Replay every test signal; return list of (cat, res, ex, is_reaction)."""
    out = []
    for cat, entry, f in test:
        res, ex = replay_pct_buy(cat, entry, tp, sl, bars, tsk)
        out.append((cat, res, ex, f))
    return out


def main():
    c = get_supabase_client()
    bars, tsk, prepped = prep(c)
    print(f"{SCOPE} {VARIANT}  ({len(bars)} bars, {len(prepped)} signals)  fric≈{FRIC}%/side")

    main_R = None
    for si, split_iso in enumerate(SPLITS):
        split_dt = parse_iso(split_iso)
        train = [p for p in prepped if p[0] < split_dt]
        test  = [p for p in prepped if p[0] >= split_dt]
        d = derive(train, bars, tsk)
        if d is None:
            print(f"\nsplit {split_iso[5:10]}: too few train reactions — skip"); continue
        thr, tp, sl = d
        be = be_fric(tp, sl, FRIC)
        win_R = (tp - FRIC) / (sl + FRIC)

        # replay all, split into reaction / non
        rep = replay_all(test, tp, sl, bars, tsk)
        rej_cands = [(cat, res, ex) for (cat, res, ex, f) in rep if variant_pass(VARIANT, f, thr)]
        trades = dedup(rej_cands); rwr, rn = wr_of(trades)
        Rs = [win_R if t[1] == "WIN" else -1.0 for t in trades]
        ev = ev_fric(rwr, tp, sl, FRIC) if rn else 0.0

        print(f"\nsplit {split_iso[5:10]}  thr(chan_pct≤)={thr:.3f}  TP={tp}% SL={sl}%  "
              f"win {win_R:+.2f}R  be {be*100:.1f}%")
        print(f"  deduped reaction trades n={rn} WR={rwr*100:.1f}% EV={ev:+.3f}R "
              f"{'+EV' if rn and rwr>be else '-EV'}  {[t[1][0] for t in trades]}")

        if si == 0:
            main_R = Rs
            # friction sweep
            for m in (0, 1, 2):
                co = FRIC * m
                print(f"  friction {m}x: be={be_fric(tp,sl,co)*100:.1f}%  "
                      f"EV={ev_fric(rwr,tp,sl,co):+.3f}R {'+EV' if rwr>be_fric(tp,sl,co) else '-EV'}")

            # ---- bootstrap on the longest window ----
            n = len(Rs)
            if n >= 5:
                boots = []
                for _ in range(NBOOT):
                    s = [Rs[random.randrange(n)] for _ in range(n)]
                    boots.append(sum(s)/n)
                boots.sort()
                lo = boots[int(0.025*NBOOT)]; hi = boots[int(0.975*NBOOT)-1]
                p_pos = sum(1 for b in boots if b > 0)/NBOOT
                print(f"  >>> bootstrap n={n} meanEV={st.mean(Rs):+.3f}R "
                      f"95% CI [{lo:+.3f}R, {hi:+.3f}R] P(EV>0)={p_pos*100:.1f}%")

            # ---- PLACEBO A: random entries from full test pool ----
            all_idx = list(range(len(test)))
            obs_mean = st.mean(Rs) if Rs else 0.0
            ge = 0
            for _ in range(NPLACEBO):
                pick = random.sample(all_idx, min(rn, len(all_idx)))
                cands = [(test[i][0],) + replay_pct_buy(test[i][0], test[i][1], tp, sl, bars, tsk) for i in pick]
                pl_trades = dedup([(cat, res, ex) for (cat, res, ex) in cands])
                pl_R = [win_R if t[1] == "WIN" else -1.0 for t in pl_trades]
                if pl_R and (sum(pl_R)/len(pl_R)) >= obs_mean:
                    ge += 1
            print(f"  >>> PLACEBO A (random entry, same count): "
                  f"P(random meanEV ≥ {obs_mean:+.3f}R) = {ge/NPLACEBO:.4f}")

            # ---- PLACEBO B: shuffle reaction labels over resolved logs ----
            resolved = [(variant_pass(VARIANT, f, thr), 1 if res == "WIN" else 0)
                        for (cat, res, ex, f) in rep if res in ("WIN", "LOSS")]
            k_react = sum(1 for is_r, _ in resolved if is_r)
            obs_wr = (sum(w for is_r, w in resolved if is_r) / k_react) if k_react else 0.0
            wins = [w for _, w in resolved]
            ge2 = 0
            for _ in range(NPLACEBO):
                random.shuffle(wins)
                shuf_wr = sum(wins[:k_react]) / k_react if k_react else 0.0
                if shuf_wr >= obs_wr:
                    ge2 += 1
            print(f"  >>> PLACEBO B (label shuffle, per-LOG): observed reaction WR={obs_wr*100:.1f}% "
                  f"(k={k_react}) | P(shuffled ≥ observed) = {ge2/NPLACEBO:.4f}")

    print(f"\nVERDICT INPUTS: clears bar if split-1 P(EV>0)≳99%, CI low >0, "
          f"both placebo p≲0.05, and other splits stay +EV.")


if __name__ == "__main__":
    main()
