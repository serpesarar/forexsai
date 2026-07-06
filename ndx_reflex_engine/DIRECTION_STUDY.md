# Directional prediction study — "above or below entry in 5 min / 1 hour?"
**2026-07-06.** Goal: maximize honest out-of-sample accuracy of the pure direction call.

## Headline: there is NO honest directional edge at 5-min or 60-min horizons.
And in getting here I caught and fixed a **lookahead leak** that had inflated the first result to a
fake 70%.

## The leak (found and fixed)
The multi-timeframe features (`5m_stretch/rsi`, `15m_stretch/rsi`) resampled with left-labelled bins:
a 1-minute bar at minute *t* was handed the **close of the 5-minute bin it was still inside** — up to
5 minutes of future information, landing almost exactly on the 5-minute label. Fix: strictly causal
resampling (`label/closed="right"` + ffill) so a bar only sees higher-TF bars that have already closed.

| horizon | metric | BEFORE fix (leaked) | AFTER fix (honest) |
|---|---|---|---|
| 5 min | overall OOS acc | 70% | **51–52%** |
| 5 min | top-5% confident | 86–89% | **49–53%** |
| 60 min | overall OOS acc | 52–54% | **47–49%** |

The 70% was entirely the leak. The tell was that 5-min looked amazing while 60-min was coin-flip —
real skill doesn't collapse like that; a 5-minute lookahead does exactly that.

## Honest results (leak-fixed, both years on the same causal features)
| horizon | base rate P(up) | ML overall acc | best confident subset | verdict |
|---|---|---|---|---|
| **5 min** | 51–52% | 51–52% | ~53% (noise) | **= base rate, no edge** |
| **60 min** | 53–56% (drift) | 47–49% | ~48–56% (noisy) | **worse than "always up"** |

- At 5 min, the model matches the base rate and beats it nowhere, at any confidence level.
- At 60 min, the single best "predictor" is just **"price will be up"** (NDX drift, 53–56%); the ML
  cannot beat that. Conditioning on features adds nothing reliable.

## What this means
- **You cannot know the 5-min or 1-hour direction on NDX meaningfully better than a coin flip
  (5 min) or the drift (60 min).** This is consistent with efficient intraday pricing and with every
  prior in-house result (2026-05-29 no-edge battery; CORTEX daily-direction failure).
- **The edges we DID find are NOT directional forecasts.** mom_cont (+0.29R), the time-stop exit
  (+0.09R), the PEF (+0.08R) all make money from *asymmetric payoff, regime-sized exposure and
  short-horizon drift capture* — not from predicting which way price goes. That distinction is the
  whole game: you don't need to know direction to have positive expectancy, and here you can't know it.
- Chasing "maximum direction accuracy" is therefore the wrong objective on this instrument. The right
  objective is expectancy under honest execution — which is what the PEF already optimizes.

## Note on earlier results
The same MTF leak was present in the feature pack used by the ML-gated families (chan_rev/vwap_rev/
sweep). mom_cont is **leak-immune** (base-rate family, no ML gate) so its edge stands. The ML-gated
contributions are being re-validated with the fixed features; see the re-validation note appended to
FINAL_PEF.md.

Script: `research/v6_direction.py` · fix: `features/pack.py` MTF block.
