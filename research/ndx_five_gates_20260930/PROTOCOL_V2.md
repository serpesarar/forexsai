# Second search — fixed before reading September trade outcomes

The original five and their July/August failures remain archived unchanged.
This second search uses an independent 2025 provider and all available 2026 data
through August for selection. July/August is now selection data, never labelled
untouched validation in this second search. September outcomes are not used.

- 2025 Dukascopy US100: actual bid AND ask OHLC built from locally available ticks.
- Selection periods: 2025 Jan–Jun, 2025 Jul–Dec, 2026 May20–Aug28 direct MT5.
- Final: 2026 Sep1–Sep29 direct MT5 M1, newly read from terminal, clock measured
  independently from at least two fresh quote symbols. Closed observations only.
- Additional September split: Sep1–15 / Sep16–29. No rule changed after evaluation.
- Common session: Mon–Thu, 03:00–15:30 NY, flat at 15:55. Risk floor 35 points,
  0.2-point adverse slippage per fill, actual spread, one position, 10-min refractory.
- Geometries: FAST SL=2×ATR70, TP=2R, hold15; CORE SL=5×ATR70, TP=1.5R,
  hold90; SLOW SL=8×ATR70, TP=2R, hold240. Risk floors apply to all three.
- 15 families ×3 lookbacks ×4 context gates ×3 sides ×3 geometries = 1,620
  second-search evaluations, in addition to the first 432 evaluations (some
  definitions overlap). No hidden discarded configurations.
- The original 12 mechanisms plus AR(1) innovation reversal, variance-ratio regime
  switching, standardized shock continuation. These are statistical hypotheses,
  not a claim of new financial mathematics or profitable prediction.
- Selection requires ≥100 total 2025 decisions, ≥60 in 2026, ≥30 in each 2025
  half; positive EV and nonnegative matched day/hour/side lift in all three
  periods. Worst-case data-gap EV must stay nonnegative. Prefer the smallest
  positive EV/lift across those periods. One candidate per distinct family.
- If fewer than five pass, fill with the best validation candidates satisfying
  volume and identify these as failed-selection hypotheses, not evidence passes.
- Final stress: actual spread×1.5/3, slippage1, delay1m; alternate fixed80/110 and
  symmetric geometry; unchanged detector on complete3m/5m bars. Equivalent
  six-check card plus five-hypothesis Holm tests and day-block confidence.
- Matched baseline is a diagnostic of incremental selection, not portfolio PnL.
- A replay candidate cannot be called LIVE; future shadow fills remain necessary.
