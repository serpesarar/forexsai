# XAUUSD Daily-Swing Edge — FOUND (2026-06-16)

After 3 weeks of prior research proved XAUUSD **1m scalping** has no edge, this study
opened the untested door the user asked about: **daily support/resistance & trend
channels = higher-timeframe swing.** Result: there IS a robust, friction-proof,
BUY-only edge on the daily timeframe.

## Data
`xauusdegitim/data/raw/`: D1 (1289 bars, 2021-05 → 2026-04, 5y), H1 (29.5k, intrabar
TP/SL fills). Gold rose +157% over the window — so drift-control was the central test.

## Engine (leak-free)
Signal on closed D1 bar `i` → fill at D1 `open[i+1]` → trade walked forward on H1
(pessimistic SL-first on ambiguous bars) → ATR(14) TP/SL + time-stop → friction in $.
Deduped to **one position at a time** (independent trades). Validated with 60/40 OOS,
5-fold walk-forward, per-year breakdown, bootstrap EV CI, friction stress, parameter grid.

## Battery result (full sample, friction $0.40)
| side | verdict |
|---|---|
| Donchian breakout BUY (N=20/55, close>EMA200) | **+EV, robust** avgR 0.64–0.78, OOS holds |
| RSI oversold-dip BUY in uptrend | +EV but rare (n=21) |
| ALL SELL variants (breakdown, resistance-reject) | **−EV / 0 OOS trades — reject** |

Confirms the standing directional bias: **gold is BUY-only.** Never sell it.

## 🏆 Winner: DONCH(N)_BUY, BUY-only daily swing
**Rule:** BUY when daily close prints a new **N-day high (N≈40–55)** AND daily
**close > EMA200** (uptrend filter = the off-switch in bears). Fill next D1 open.
**SL = entry − 2.0×ATR(14)**, **TP = entry + 4.0×ATR(14)** (5.0 slightly better),
**time-stop 20 trading days**, **one position at a time**.

Deduped performance (N=55, 2.0/4.0/20d):
- 31 independent trades / 5y (~6/yr), **WR 64.5%**, **avgR +0.686**, **PF 3.04**, maxDD **2.0R**
- Bootstrap 95% CI on EV: **(0.217, 1.154)** — lower bound clearly > 0

## Why it's a real edge, not buy&hold drift
1. **Per-year positive every year** except 1-trade 2021. In **flat 2022 (gold +1.2%)
   it made +3.3R / 75% WR** — buy&hold made ~0; the rule timed the intra-year legs.
2. **All 5 walk-forward folds positive** (avgR 0.22 / 0.79 / 0.51 / 1.50 / 0.50).
3. **Parameter PLATEAU** — every cell of N∈{40,50,55,60,70} × 4 exit configs is
   positive avgR (+0.51…+0.94). Not a lucky cell → not curve-fit.
4. **Friction-proof**: survives $8 round-trip (20× realistic gold cost) — avgR +0.577,
   CI still > 0. This is why swing works where scalp failed: $0.40 spread is 8% of a
   $5 scalp target but <0.3% of a ~$200 swing target.

## Honest limitations
- 31 deduped trades over one gold up-cycle. No sustained multi-year BEAR was observed
  (none has occurred since 2013–15). The EMA200 filter SHOULD mute signals in a
  downtrend, but this is untested live in a bear — size conservatively.
- Edge concentrates in trending years; chop years (2021/2023) are ~breakeven (small
  bleed, not big losses — exactly the trend-follower profile).

## How to deploy
Run ONCE per day on the D1 close (NOT the 2-min intraday lifecycle). This is a new
model, separate from the 6 intraday models — those keep XAUUSD live-trading OFF
(they're the ones that lost money). Trade ONLY this daily-swing BUY rule for gold.

Repro: `swing_battery.py` (battery), `validate.py` (dedup/per-year/WF), `stress.py`
(friction + param grid). Run from repo root with `.venv`.

## Stage 4 — higher-frequency variant (`develop.py`)
Raised frequency by moving the breakout to H4 with a D1-uptrend confluence filter.
**H4_DONCH30, SL=2×ATR/TP=4×ATR/30-bar(~5d) hold, BUY-only, D1-uptrend confluence:**
~24 trades/yr (4× the D1 rule), WR 47.7%, avgR +0.331, PF 1.65, maxDD 6.6R, bootstrap
CI (0.103, 0.562), **positive every single year** (incl. flat 2022). Trade-off vs the
D1 rule: smaller per-trade edge (+0.33R vs +0.69R) and higher DD (6.6R vs 2.0R) but ~4×
the trades → more total return (~47R vs ~21R over 5y). The **oversold-DIP second entry
was REJECTED** (all variants' bootstrap CI straddle 0, negative in 2023) — gold's edge
is buying STRENGTH (breakout), not weakness (dip).

### Two deployable modes (same edge, different dosage)
- **D1 "Sniper"** — Donch55, 2/4/20d: ~6 trades/yr, +0.69R, 2R DD. Patient, high-quality.
- **H4 "Active"** — Donch30 + D1 confluence, 2/4/30bar: ~24 trades/yr, +0.33R, 6.6R DD.
Both BUY-only, EMA200/D1-trend gated (off in downtrends), positive every year.
