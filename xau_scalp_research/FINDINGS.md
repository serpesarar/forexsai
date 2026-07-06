# XAUUSD 5-pip Scalping — Win Rate Investigation (Findings)

**Goal as specified:** ≥70% win rate, TP = 5 pips, SL = 5 pips (1:1 RR), clean leak-free data.
**Verdict: NOT ACHIEVABLE on clean data.** The realistic ceiling is ~52% gross / ~50% net of spread.

Data: `1MDATA/mt5_xauusd_1m_bars.json`, 96,334 1m bars (2026-02-11 → 2026-05-21).
Worked on last 40% only (idx 57,800+); train idx 57,800–84,772, held-out test 84,773–96,333.
XAUUSD pip = $1.00 (production config), so TP=+$5.00 / SL=−$5.00.

## Step 0 — Data integrity: CLEAN
0 dup/out-of-order timestamps, 0 OHLC-invalid bars, 0 zero/neg volume. All non-60s
gaps are legit session boundaries (daily breaks + 14 weekend gaps). No spread field
in file (OHLCV only) → spread modeled separately. 4 large bars are real news/open
events, all in the untouched first 60%.

## Step 1 — Leakage audit
Production `signal_lifecycle._get_price_window_since_signal` correctly cuts off at
`created_at` (post-creation candles only), entry_price is creation-time. BUT outcome
eval uses 5m candles → in-bar TP/SL ambiguity inflates WR at $5 targets. Prior 1m
replay (memory) already proved XAUUSD's "high WR" = pure geometry, zero edge.
→ Existing WR numbers NOT used as baseline. Built own 1m-resolution backtest with
pessimistic (SL-first) in-bar tie-break, entry at next-bar open, no cross-gap eval.

## Engine validation
Directionless baseline on test slice: BUY 47.0% / SELL 52.9% (sum≈100%, shortfall =
pessimistic tie-break). Test slice has a mild SELL drift → "always SELL" = 52.9%.

## Step 2 — Simple approaches (all FAIL, ~baseline)
| Strategy | Train WR |
|---|---|
| S/R bounce (5m OR 15m) | 49.8% |
| S/R confluence (5m AND 15m) | 48.5% |
| Trend channel (5m, mean-reversion) | 49.0% |
| Breakout continuation | 49.3% |
| Trend-following (5m EMA20/50) | 48.3% |

## Step 3 — Lean ML (17 features, GBM + LogReg), walk-forward
Expanding walk-forward, pooled, bootstrap 95% CI:
| thr | trades | WR | 95% CI |
|---|---|---|---|
| 0.55 | 17,343 | 51.3% | [50.6, 52.1] |
| 0.60 | 10,526 | 52.4% | [51.4, 53.3] |
| 0.65 | 6,264 | 52.7% | [51.5, 53.9] |
| 0.70 | 3,625 | 51.8% | [50.1, 53.4] |

Spread sensitivity @ thr 0.60: $0.00 → 52.4%, **$0.30 → 49.7% (net losing)**.
(The transient "75%" seen at thr 0.70 on the single test split was 6/8 trades = noise.)

## Most-charitable pocket scan
Conditioned on (hour × volatility × momentum × direction). 13 cells reach ≥65% on
TRAIN (up to 74.5%). **0/13 hold ≥65% on TEST.** Mean collapse train→test = 18.5pp.
→ All high-WR pockets are in-sample overfitting artifacts.

## Why 70% is impossible here (geometry)
At 1:1 RR the breakeven WR is 50%. 70% requires a genuine ~20pp directional edge —
i.e. reliably predictable drift of ~$2–3 over a ~10-min horizon at a $5 (0.1% of
price) barrier. Gold does not offer this. Five independent lines of evidence
(6 rules, GBM at volume, pocket scan, prior 150-feat model, prior 1m replay) all
converge on **zero exploitable directional edge** at this target scale.

## What WOULD "achieve 70% WR" — and why it's the wrong target
WR is a function of RR geometry, not skill. Tightening TP / widening SL trivially
lifts WR: e.g. TP=2 / SL=8 → baseline WR ≈ 80%. But with no edge that is
**negative expected value** (you win small often, lose big occasionally, and the
spread eats you). WR alone is misleading; the correct objective is **positive
expectancy net of spread**, which this data does not support for XAUUSD scalping.

## Recommendation
Do not deploy a `xauusd_scalp` model claiming 70% — it cannot exist honestly.
Options to redefine the goal so it's both achievable and meaningful are in the chat.
No production files were modified.

---

## ADDENDUM — Positive-EV search (user redirected objective)

Dropped the WR target; searched for positive expectancy net of $0.30 spread across
a grid of symmetric barriers (5/10/15/20/30 pips) × GBM-director selection margins,
expanding walk-forward, with bootstrap 95% CI on mean PnL/trade.

**Result: no statistically-significant +EV config.** Best was barrier=10, margin=0.15:
mean +$0.19/trade, but CI = [−0.005, +0.366] (straddles zero). Larger barriers
(20/30) strongly negative. NO config had CI lower bound > 0.

Per-fold diagnostic of that "best" config exposed it as **drift-riding**: folds 1–2
(earlier) lose (−0.62/−0.86), folds 3–5 (later, falling gold, up to 79% SELL) win
(+2.70/+1.90/+1.34). The profit is non-stationary net-short exposure to gold's recent
decline, not a predictive edge — it would reverse in an uptrend.

**Conclusion:** XAUUSD 1m scalping shows neither an honest ≥70% WR (1:1) nor a robust
positive expectancy. This corroborates the prior 1m-replay finding (zero directional
edge). No `xauusd_scalp` production model is justified.

---

## ADDENDUM 2 — Narrow recurring-condition search (2026-05-29)

Question: does ANY narrow, recurring, leak-free condition reach ~70% WR (5/5, 1:1)?
Method: 132 fixed conditions (direction × hour / 2h-window / session / day-of-week /
volatility tercile / 5m-trend / RSI extreme / bar direction / combos). 5/5 outcomes
net of $0.30 spread, 1m resolution. Working 40% split into 5 time blocks; ranked by
WORST-block WR; opposite-direction drift control on top candidates.

**Result: NO condition is robust at ~70%.**
- Best worst-block WR = 52% (SELL hour=17, overall 59%). Nothing's worst block ≥ 55%.
- Conditions flashing 65–71% (e.g. SELL hour=12 block1=71%) DECAY monotonically across
  blocks → regime artifacts, not recurring edge.
- Drift control: every top SELL condition's opposite (BUY) WR = 36–44%, sums to
  92–95% → the SELL "edge" is just net-short exposure to gold's recent decline,
  mirrored by symmetric BUY losses. This is the directional drift the user asked to
  exclude, and it fails the test.
- Mean-reversion (RSI<30 BUY / RSI>70 SELL, ± low-vol): 40–50%, no consistency.

**Definitive conclusion across all work:** XAUUSD 1m has no narrow, recurring,
leak-free condition reaching ~70% WR that survives walk-forward + out-of-sample with
spread. High-WR pockets are either single-block overfitting (132-way multiple
comparisons) or temporary directional drift. The only "real" asymmetry is trend
exposure, which is non-stationary and reverses.

---

## ADDENDUM 3 — Direction-agnostic windows + regime-aware filter (2026-05-29)

### Part A — direction-agnostic time/session window ranking (`part_a.py`)
Ranked 185 windows × 2 directions (hour, 2h-window, session, day-of-week,
dow+session, dow+hour) by worst-block WR, net of $0.30 spread. Apparent winners
(e.g. Monday 02:00 SELL: overall 80%, worst-block 72%, per-block [82 83 88 77 72]%,
N=253, mean PnL +$2.98) are **overlapping-sample illusions**: a single
02:00–02:59 day contributes ~60 correlated 1m entries, so "253 trades" = only ~5
distinct Mondays. Non-overlapping re-test (one trade per distinct day):
- Mon 02h SELL = 5/5 days, p=0.031 · Mon 17h SELL = 6/6, p=0.016 · Mon 07h = 5/6,
  p=0.109 · hour=17 all-dow = 16/28, p=0.286 (only meaningful sample → 57%).
- Bonferroni threshold for ~370 tests ≈ 0.00014. **NONE pass.**
- Pooled "regardless of direction" WR across headline windows = **46–47%** (no
  direction-agnostic edge; pooling near-complementary BUY/SELL → no-skill baseline).

### Part B — regime-aware filter & ML classifier (`regime_scan.py`)
Tested the user's hypothesis: can a regime model detect when gold's drift is active
vs. reversing, and time SELL-in-bear / BUY-in-bull / flat-in-chop? Causal regime
features only (EMA20/50/200, EMA slope, ADX, 1h/4h rolling return, vol expansion,
prev-day dir, rolling drift; DXY/yields/news unavailable in OHLCV-only file). The 5
working blocks are deliberately mixed — bull(1,+97) bear(2,−156) bear(3,−96)
bull(4,+130) bear(5,−144) — so the decisive test is: **does a config win in BOTH
bull and bear blocks?** Bear-only profit = drift-following, not regime skill.

| Config | N | WR | mean PnL/trade | total$ | bull$ | bear$ |
|---|---|---|---|---|---|---|
| (2) always BUY | 33023 | 45% | −0.55 | −18283 | −3682 | −14601 |
| (2) always SELL | 32902 | 48% | −0.13 | −4355 | −5307 | +952 (bear-only=drift) |
| baseline drift-follow (EMA20>50) | 32993 | 47% | −0.33 | −10948 | −5773 | −5175 |
| (1) time/session + fixed-dir WF | 7132 | 46% | −0.39 | −2805 | −15 | −2790 |
| (3) time + SELL | 9032 | 46% | −0.43 | −3924 | −3240 | −684 |
| (4) time + regime (flat if neutral) | 5972 | 43% | −0.66 | −3971 | −1845 | −2126 |
| (5) regime-gated (SELL-bear/BUY-bull) | 21434 | 46% | −0.38 | −8046 | −3881 | −4165 |
| (6) time + regime-gated | 5972 | 43% | −0.66 | −3971 | −1845 | −2126 |
| (7) ML classifier + margin entry WF | 5888 | 50% | **+0.04** | +214 | +75 | +139 |

**Result: every rule-based regime config is net-negative after spread.** The only
nominally-positive config (7, GBM regime classifier) makes **+$0.04/trade**, and its
bootstrap 95% CI on mean PnL = **[−0.092, +0.165] — straddles zero**. The "+75 bull"
comes entirely from block 4 (block 1 had 0 selected trades), so even the "wins both"
flag is one bull block of noise. Regime detection does NOT convert gold's drift into
a timeable, reversing edge.

**Definitive across ALL addenda:** no honest ≥70% WR, no robust +EV, no recurring
narrow condition, no direction-agnostic window edge, and no regime-aware filter (rule
or ML) that beats spread on this XAUUSD 1m data. The apparent SELL asymmetry is
non-stationary net-short drift, and conditioning on regime cannot reliably time it.
