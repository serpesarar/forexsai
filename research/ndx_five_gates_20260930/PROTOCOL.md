# NDX five-gate research protocol — frozen before outcome screening

Created 2026-09-30. This is offline research, not a production change.

## Data and chronology

- Source A: corrected `nasdaq_1m_candle_cache_2026-02-10_2026-08-29/` CSV.
- Source B: direct MT5 NAS100 M1 CSV in `nasdaq_tam_veri_2026-08-29/1m_veri/`.
- Source B takes precedence at its first timestamp; no double timezone correction.
- Discovery: 2026-02-11 through 2026-05-15, cache only. Cache execution is approximate.
- Validation: 2026-05-20 through 2026-06-30, MT5 only.
- Final evaluation: 2026-07-02 through 2026-08-28, MT5 only, read after selection.
- Discovery and validation are each divided into two calendar halves. Outcomes
  crossing a split are purged. Period gaps exceed the 90-minute maximum holding time.
- Prior investigations used overlapping history: final evaluation is held out from
  this run's search, not unprecedented or genuinely new market data.

## Search space and selection

12 families, 3 lookback settings, 4 context gates, 3 side selections = 432 rules.
All are detected on closed M1 bars. Three lookbacks are 15, 30, 60 minutes.
Context gates: unrestricted, H1 EMA50 alignment, path efficiency alignment,
or low short/long ATR ratio. Sides: both, BUY, SELL.

Families: trend pullback reclaim; range sweep return; compression breakout;
impulse absorption; variance-normalized exhaustion; failed breakout return;
path-efficient retracement; session VWAP reclaim; opening-range continuation;
opening-range failure; two-shock reversal; range-midpoint reclaim.

Common executable session: Monday–Thursday, 03:00–15:30 America/New_York;
all positions closed by 15:55. This preserves the existing Friday/Asia restrictions
as a common prerequisite. This study does not revalidate those restrictions.

Primary geometry: SL=max(35, 5×closed-M1 ATR70) points, TP=1.5×SL,
90-minute maximum hold, flat by 15:55 NY. One position per strategy at a time,
10-minute refractory period from the prior accepted decision.

Eligibility for selection: at least 80 discovery and 40 validation decisions,
nonnegative EV in all four chronological subperiods, positive overall validation EV.
Rank by the minimum of the four EVs, then validation EV. Select one rule per family
and the first five families. If fewer than five qualify, fill with the highest
validation candidates and clearly label them exploratory. Never substitute a new
rule after seeing the final evaluation.

## Execution and falsification

- Decision time = signal bar start + duration. Only complete bars enter features.
- Entry = exact next-M1 open. Skip stale entries, incomplete feature bars and
  decisions without the preceding continuous 60-minute M1 window.
- MT5 bars are bid OHLC; spread is MT5 integer points ×0.1 price points, supported
  by existing NAS100 research (median 13→1.3 points). Source A uses assumed 1.3.
- BUY opens at ask; SELL opens at bid. SELL exits use bid OHLC + each bar's spread.
- Adverse slippage 0.2 point per fill; commission set to zero, consistent with
  the local demo export, without claiming that live account costs are identical.
- Stop gaps fill at the adverse opening price; ambiguous TP/SL same bar → stop.
- Unexpected missing bars terminate at the last observable close and are marked
  separately; also report worst-case gap sensitivity. Do not silently drop them.
- Stress: 1.5×spread, 3×spread, 1 point/fill slippage, next-minute delayed entry.
- Alternate geometries: fixed TP/SL 80/110 and 1×/1× adaptive geometry.
- Transfer: unchanged rule on complete 3m/5m bars; durations are physical minutes,
  common M1 risk scale/execution, plus H1 context. These are the same market path,
  not independent samples.
- Day-block bootstrap, Wilson interval, calendar subperiods, side breakdown,
  equity/drawdown, matched calendar-day/hour/side unconditional baseline, and
  five-rule Holm correction for matched-baseline tests.
- A frozen five-rule portfolio must enforce one total position at a time.
- Causal feature truncation and hand-built execution fixtures verify the engine.
- Example charts use the first final-period winner and loser, not best examples.
- Evaluate equivalent six-check go-live cards, but force SHADOW/RED because this
  bar replay lacks future shadow fills and uses an approximate early source.

## Interpretation

Report net R and points, never invented USD returns or future profit guarantees.
Distinguish standalone bar-defined entry sources from gates on recorded bot
signals. A positive bar-defined source does not establish incremental bot profit.
Disclose every tested configuration and every final failure.
