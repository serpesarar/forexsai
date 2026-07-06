# "SL → breakeven after 5×1m bars" test — all families (2026-07-06)

User rule: 5 one-minute candles after entry, pull the stop to the entry level. Tested under
realistic (gap-aware) fills on 2025 holdout + 2026 broker. Success = net-positive trade (r>0);
a breakeven scratch is NOT a win (it costs the spread).

## Pooled result (best BE variant = BE@5 + time-stop 15m)
| set | WR (success) | EV | PF | avg win | avg loss |
|---|---|---|---|---|---|
| 2025 holdout | **23.2%** | +0.008R | 1.03 | +1.36R | −0.40R |
| 2026 broker | **23.7%** | +0.098R | 1.31 | +1.74R | −0.41R |
| 10-group | EV>0 in **9/10** (only June-2025 chop negative) | | | | |

## Reference — the current best exit (time-stop 15m, NO breakeven)
| set | WR | EV | PF |
|---|---|---|---|
| 2025 holdout | 45.0% | **+0.037R** | 1.08 |
| 2026 broker | 44.4% | **+0.117R** | 1.26 |

## Per-family under BE@5 + time15 (HOLD / 2026 EV)
| family | HOLD EV | 2026 EV | note |
|---|---|---|---|
| **mom_cont** | **+0.455R** | **+0.923R** | best by far — protective BE + let momentum run |
| vwap_rev | +0.022R | +0.009R | ~breakeven |
| chan_rev | −0.014R | +0.035R | ~breakeven |
| sweep | −0.192R | −0.021R | negative under every exit |

## Verdict
- **The breakeven-after-5-bars rule LOWERS the win rate, not raises it** — from ~45% to ~23% —
  because most protected trades get scratched at breakeven, and a scratch costs the spread (counts
  as a tiny loss, not a win). It is a *capital-preservation* rule, not a *win-rate* rule.
- It **does cut risk**: average loss shrinks from −0.83R to −0.40R (fewer full stop-outs).
- But on **expectancy it is slightly WORSE than the plain time-stop** (+0.008R vs +0.037R on the
  2025 holdout): it scratches too many trades that would have recovered into wins. The plain
  15-minute time-stop remains the better exit.
- **Exception: mom_cont** (momentum-continuation) is strongly positive under BE@5 (+0.46R / +0.92R)
  — for a continuation entry, cutting reverters to breakeven and letting runners run is a natural
  fit. But even mom_cont is marginally better under the plain time-stop (+0.49R / +1.04R).
- **sweep** loses under every exit — it should be dropped from live trading.

## Bottom line
Breakeven-after-5-bars is a legitimate, convention-robust, lower-risk variant (9/10 groups +EV on
the combined stream) — but it trades away win rate and a little expectancy for smaller losses. It
does not beat the simple time-stop. If low drawdown matters more than raw EV, BE@5+time15 on
mom_cont + reversion (drop sweep) is a defensible lower-variance configuration.

Script: `research/v5_be_after5.py` · data: `data/models/v5_be_after5.json`.
