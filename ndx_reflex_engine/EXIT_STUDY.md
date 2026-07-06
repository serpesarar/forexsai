> ⚠️ **CORRECTION (2026-07-05, see EXIT_SYSTEMS.md):** the atr_trail +0.03/+0.045R result below
> used an *optimistic* fill-at-stop convention. Under realistic gap-aware fills atr_trail is
> −0.037R (holdout) / −0.011R (2026) — NOT profitable. The convention-robust positive exit is a
> simple **time-based** exit (+0.09R pooled, PF 1.21), not any trailing stop. Read EXIT_SYSTEMS.md
> for the corrected, fill-controlled conclusion.

# V1 Exit-Optimization Study — 2026-07-05

**Question:** does the frozen high-win-rate entry logic (`high_wr_asymmetric_gate_v1`) become
profitable purely by improving exit management, with the entry model, triggers, features, and
τ-gates completely unchanged?

**Answer: YES — an ATR trailing stop converts it from −0.06R to +0.04R, PF 1.22, and cuts
drawdown ~8×.** Entry set is byte-for-byte the frozen V1 gate; only the post-entry logic changed.

## Method
- Entry = frozen V1 gated events (chan_rev/vwap_rev/sweep ML gates + mom_cont base rate).
  Per-family **SL geometry held fixed** (2.5 / 2.0 / 1.5 ×ATR). 1,010 holdout + 2,424 broker-2026 entries.
- Bar-by-bar exit simulator on 1m bid/ask bars: entry next-bar at ask/bid, exits on the opposite
  book side, spread inside the replay, 1-pt slippage per fill, conservative intrabar ordering
  (adverse extreme before favorable; trailing/BE stops update from prior bars only).
- Risk unit R = initial SL distance (fixed), so all policies are comparable.
- Adaptive params tuned on 2025-**train** entries, frozen, reported on 2025-**holdout** + 2026 (both OOS).

## Results (HOLDOUT / 2026 broker)
| Exit policy | HOLD WR | HOLD EV | HOLD PF | 2026 WR | 2026 EV | 2026 PF |
|---|---|---|---|---|---|---|
| base (tp0.4×ATR, full SL) | 81.3% | −0.073R | 0.62 | 82.3% | −0.062R | 0.66 |
| fixed_tp 0.5 | 78.8% | −0.066 | 0.69 | 80.1% | −0.053 | 0.74 |
| fixed_tp 0.7 | 73.6% | −0.061 | 0.77 | 75.5% | −0.037 | 0.85 |
| fixed_tp 1.0 | 67.2% | −0.049 | 0.85 | 69.5% | −0.018 | 0.94 |
| partial 50%@0.4 + BE + tp2=2.0 | 81.2% | −0.044 | 0.77 | 81.6% | −0.035 | 0.81 |
| **atr_trail arm0.4/trail0.4** | **71.1%** | **+0.030R** | **1.15** | **72.8%** | **+0.045R** | **1.25** |
| vol_adj tp lo0.4/hi0.8 | 71.5% | −0.070 | 0.76 | 74.5% | −0.033 | 0.87 |
| momentum_exit 2-bar | 64.8% | −0.064 | 0.71 | 68.5% | −0.053 | 0.75 |
| confidence_exit scale4 | 56.3% | −0.017 | 0.96 | 58.6% | +0.015 | 1.04 |

**Only the ATR trailing stop makes it positive on both OOS sets.** Widening a fixed TP monotonically
raises avg-win but the entry has no continuation edge, so EV stays negative — the fat −1.0R loss tail
is the problem, and only a trailing/ratcheting stop cuts it (avg loss −1.03R → −0.68R).

## Robustness of the trailing winner (arm0.4 / trail0.4)
- **10-group stability:** 9/10 groups EV>0 (5 holdout chunks + 5 broker months); the lone miss is
  G3 2025-05-09..21 at −0.026R (chop). WR band 66–76%, PF up to 1.80.
- **Parameter plateau** (holdout EV_R), not a spike:
  ```
  arm\trail   0.3    0.4    0.5    0.6    0.8
  0.3       +.036  +.023  +.009  -.008  -.031
  0.4       +.041  +.030  +.014  -.001  -.019
  0.5       +.046  +.036  +.024  +.009  -.007
  0.6       +.042  +.035  +.023  +.009  -.003
  ```
  Positive across the whole arm 0.3–0.6 × trail 0.3–0.5 region → low overfit risk. (Train picked 0.4/0.4;
  the plateau centre 0.5/0.3 is marginally better but the chosen point is conservative.)
- **Block bootstrap** pooled OOS (n=3,428): WR 72.3%, EV +0.041R, PF 1.22, **P(EV>0)=1.000**.
- **Drawdown collapse:** base policy max-DD 78–156R → trailing 14–18R pooled (per-group ≤13R).

## Verdict & caveats
- **The high-WR entry is a viable +EV strategy once you stop letting it lose 2.5R.** The trailing
  stop is the mechanism; partial+BE helps but not enough; wider fixed TPs do not.
- EV is **modest** (+0.04R/trade, PF 1.22) — real but not spectacular; sizing/selectivity matters.
- Trailing-stop fills are the most slippage-sensitive exit; the +1pt assumption may be optimistic in
  fast gaps. Forward shadow must measure real trailing-exit slippage from `tickdata/`.
- WR ~72% here is **below** and geometrically **different from** the V2 goal (75% at symmetric
  0.10%/0.10%) — this does NOT satisfy V2; it is a separate, honestly-positive outcome.
- Recommended: promote this as **V1.1 (trailing-exit)** — a shadow-live candidate alongside mom_cont.
  Save params: activate=0.4×ATR, trail=0.4×ATR (or plateau centre 0.5/0.4), time-stop 60m, per-family SL unchanged.
