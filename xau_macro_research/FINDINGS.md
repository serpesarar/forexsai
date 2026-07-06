# XAUUSD Macro/News Direction Model — TESTED, NO EDGE (2026-06-16)

User chose the "different angle": predict gold's direction from macro/news instead of
price patterns. Built it honestly with real data. Verdict: **macro does not give gold
a directional edge in this period — the traditional relationships broke, and models
can't beat simply being long.**

## Data
FRED daily (free, no key), aligned with XAUUSD D1 → `macro_panel.csv`, 1289 rows
2021-05→2026-04: DFII10 (10Y real yield), DGS10/DGS2 (nominal), T10YIE (breakeven),
DTWEXBGS (broad USD), VIXCLS (VIX) + gold.

## Finding 1 — the textbook relationships BROKE (regime sign-flip) `explore.py`
Spearman corr of each factor(t) with forward 20-day gold return, split by era:
| factor | 2021-23 | 2024-26 |
|---|---|---|
| real yield (DFII10) | +0.20* | **−0.11*** (flip) |
| nominal 10Y | +0.20* | **−0.09*** (flip) |
| broad USD | +0.20* | +0.01 (gone) |
| VIX | +0.10* | **−0.11*** (flip) |

The strong FULL-sample corrs (~+0.29) are SPURIOUS co-trending: gold AND real
yields/dollar both rose 2021-26, so they correlate without predicting. Splitting by
era flips the sign — proof the link isn't predictive. Gold DECOUPLED from real
yields/dollar in 2024-26 (central-bank buying, de-dollarization, geopolitics — none
captured by these series). A model trained on the old inverse link would have screamed
"sell gold" exactly as it went parabolic.

## Finding 2 — walk-forward models can't beat always-long `model.py`
Expanding-window, purged (H-gap to kill overlap leak), predict P(gold up in 20d):
| model | OOS dir-acc | base rate | sim sum-ret | always-long |
|---|---|---|---|---|
| GBM | 62.3% | 72.9% | +0.60 | +0.88 |
| Logistic | 68.7% | 72.9% | +0.95 | +0.88 |

Both score BELOW the base rate (i.e. worse than naively predicting "up"). Logistic's
sim only "wins" by being long 81% of the time — that's buy&hold, not timing. **No
robust directional edge.**

## Why this matters (and what it confirms)
Gold's *why* (macro drivers) became unstable, but its *what* (persistent upward price
trend) held. So a **price-following rule that ignores the why is exactly the right
tool** — which is precisely why the daily-swing Donchian rule (`xau_swing_research/`)
works while macro-direction and intraday-trigger approaches don't. The only durable,
repeatable fact is gold's strong drift (up in 64-73% of 20d windows); the swing rule
harvests it with defined risk; macro can neither sharpen direction nor time exits.

Repro: `fetch_macro.py` → `explore.py` → `model.py` (run from repo root, .venv).
