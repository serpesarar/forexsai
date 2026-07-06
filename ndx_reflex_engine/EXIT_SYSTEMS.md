# Exit-Systems Benchmark — 11 exit families, entry frozen (V1 gate)
**2026-07-05.** Entry logic unchanged; only the exit varies. Risk unit R = initial SL.
Realistic execution: bid/ask replay, 1pt slippage, conservative intrabar ordering,
gap registry drops contaminated windows. Reported on untouched 2025 holdout + 2026 broker.

## Headline
**The only exit that is robustly positive under realistic fills is the simplest one — a
time-based exit (~15 min, exit at market). Every dynamic trailing stop's apparent profit
was an artifact of an optimistic stop-fill assumption and disappears under honest fills.**
This also **corrects the previous turn's atr_trail claim**: under realistic fills atr_trail
is −0.037R (holdout), not +0.03R.

## Two bugs caught (why "too good" exit results are usually bugs)
1. **SuperTrend lookahead** — the SuperTrend line at bar *j* uses bar *j*'s close, then the
   same bar's low was tested against it. Removing it dropped SuperTrend from a fake +0.83R/PF 7
   to an honest −0.05R. (atr_trail's independently-validated +0.0296R was the parity anchor that
   exposed this.)
2. **Fantasy fills beyond market** — a dynamic stop that flips to the wrong side of price (e.g.
   SuperTrend reversal) was booked as a fill *above* the market. Fixed: trend-flip exits at the
   bar close (market), never beyond it.

## The fill-convention test (the honesty gate)
Every stop/trail exit scored under **optimistic** (fill at the stop level) vs **realistic**
(gap-aware: cannot fill better than the bar open). Target/time/ML exits fill at real prices →
**convention-immune**.

| Exit | optimistic HOLD EV | realistic HOLD EV | realistic 2026 EV | robust? |
|---|---|---|---|---|
| atr_trail 0.4/0.4 | +0.030 | **−0.037** | −0.011 | ✗ |
| chandelier m2.0 | +0.309 | **−0.036** | +0.022 | ✗ |
| chandelier m2.5 | +0.200 | −0.042 | +0.042 | ✗ |
| swing_low / structure | +0.255 | −0.033 | +0.042 | ✗ |
| donchian N10 | −0.029 | −0.031 | +0.080 | ✗ (holdout neg) |
| supertrend 10/3 | −0.046 | −0.046 | +0.027 | ✗ |
| hybrid partial+chand+time | +0.148 | −0.065 | −0.040 | ✗ |
| vwap_target *(immune)* | — | −0.029 | −0.017 | ✗ |
| liquidity_target *(immune)* | — | −0.006 | +0.024 | ✗ (holdout ~0) |
| ml_exit *(immune)* | — | −0.034 | +0.035 | ✗ (holdout neg) |
| **time_based 15m *(immune)*** | — | **+0.037** | **+0.117** | **✓** |

The trailing family swings from strongly positive (optimistic) to negative (realistic) — a result
that depends on an untestable intrabar assumption is not an edge. Only convention-immune exits can
be trusted, and among those only the time-based exit is positive on both OOS sets.

## The one robust exit: time-based (~15 min, exit at market)
- **Horizon sweep (holdout / 2026):** 10m +0.009/+0.097 · 15m +0.037/+0.117 · 20m +0.010/+0.108 ·
  30m −0.001/+0.091. Positive on 2026 across all horizons; holdout peaks 10–15m. 15m is a plateau
  pick, not cherry-picked.
- **Pooled OOS:** n=3,417, WR 45%, **EV +0.093R, PF 1.21, P(EV>0)=1.000** (block bootstrap).
- **10-group stability:** EV>0 in **8/10** (miss: G4 −0.017 marginal; G5 −0.121, the June-2025 chop
  that hurt every system). All five 2026 months positive (+0.04 … +0.21).
- **Profile:** WR ~44% — a *bigger-winner* strategy: it monetizes the entry's short-horizon
  favorable drift by simply holding a fixed window and exiting at the close. No stop-fill fantasy
  is possible, which is exactly why it survives.
- **Drawdown:** all exits cut DD massively vs the raw fixed-SL base (123R → 55–76R for time-based).

## Honest verdict
- **Does better exit management make the frozen high-WR entry profitable?** Marginally, yes — but
  **only via a time-stop, not via trailing stops.** The robust edge is +0.09R/trade, PF 1.21.
- The fancy trailing systems (chandelier/swing/supertrend/hybrid) are **not** improvements once
  fills are honest; their headline numbers are fill-assumption artifacts.
- The best "exit system" here is the boringest one, precisely because it is the only one that
  cannot be inflated by execution assumptions.
- **Live caveat:** even the time-based edge is modest and leans on 2026 (holdout is weak-positive).
  Shadow-test before sizing; measure real fills from `tickdata/`. WR ~44% means psychological
  tolerance for sub-50% hit-rate is required.

Scripts: `research/v3_exit_systems.py` (engine), `research/v3_exit_verdict.py` (two-convention gate).
Reports: `data/models/v3_exit_systems.json`, `v3_exit_verdict.json`.
