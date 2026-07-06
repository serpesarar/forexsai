# Multi-Asset 1m Scalp Edge Research — XAUUSD · NDX · USOIL · DAX

**Goal:** run the full XAUUSD edge battery on NDX (USTEC), USOIL (XTIUSD) and DAX
(DE40) and find the *best honest edge* per symbol — not a forced 70%.

**Verdict up front:** none of the four instruments has an honest ≥70% 1m-scalp WR or
a statistically robust positive expectancy net of spread. XAUUSD and DAX are the only
two with a *positive gross-of-spread* directional signal (so they are the only ones
worth any further research); NDX is almost pure trend-drift and USOIL is a structural
whipsaw that loses even before spread. Production-worthy config: **none.**

---

## Method (identical across symbols)

- Data: `1MDATA/mt5_{xauusd,ustec,xtiusd,de40}_1m_bars.json` (92k–97k 1m bars each).
  Used **last 40% only** (working slice); first 60% untouched. Working slice split
  70/30 train/test and additionally into **5 equal time blocks** for walk-forward.
- Leak-free engine (`mae.py`, vectorized, validated to reproduce the cached XAUUSD
  outcomes at 100% agreement): entry at next-bar open, 1m TP/SL walk, **pessimistic
  SL-first** in-bar tie-break, session-gap force-close, `MAX_HOLD=30`.
- **Cross-asset fairness:** TP=SL barrier = **0.10% of median price** (= XAUUSD's
  $5/$5000 geometry) and spread = **6% of the barrier** (= XAUUSD's $0.30/$5). This
  isolates whether each *price process* carries edge, independent of absolute price.
  Barriers: XAU 4.75 / NDX 25.0 / USOIL 0.096 / DAX 24.1; spreads = 6% of each.
  *Caveat:* real index/oil spreads may be proportionally wider, so net results here
  are, if anything, optimistic for NDX/USOIL/DAX.
- Battery per symbol (`mae_battery.py`): (1) 70% WR search + window scan + drift
  control, (2) rule strategies, (3) lean GBM walk-forward + bootstrap CI before/after
  spread, (4) EV search vs drift baseline, (5) 7 regime configs with bull/bear split.
- Block trend profile (per-block close-to-close drift) labels each block bull/bear so
  the decisive test for any "edge" is: **does it win in BOTH bull and bear blocks?**

Block profiles (working slice): XAU bull[1,4]/bear[2,3,5]; NDX bull[1,2,3,4]/bear[5]
(strong uptrend); USOIL bull[2,3,5]/bear[1,4] (nearly flat, tiny drifts); DAX
bull[1,3,5]/bear[2,4] (the most balanced two-sided market).

---

## Headline cross-asset table

| Metric | XAUUSD | NDX | USOIL | DAX |
|---|---|---|---|---|
| Pooled BUY+SELL WR (net) | 46.5% | 46.1% | **44.1%** | 45.9% |
| Best large-N window (overall WR, N) | h17 SELL 57% (1672) | h20 BUY 60% (1420) | — all <55% | h11 BUY 56% (1512) |
| …its drift-control sum | ~94% (drift) | ~drift | ~drift | ~drift |
| ML GBM **net** mean PnL/trade | **−0.01** | −2.05 | −0.0115 | −0.91 |
| …bootstrap 95% CI (net) | [−0.10,+0.09] | [−2.59,−1.50] | [−0.0135,−0.0094] | [−1.39,−0.40] |
| ML GBM **gross** mean PnL/trade | **+0.275** | −0.55 | −0.0057 | **+0.539** |
| ML pooled WR | 50.0% | 45.7% | 44.0% | 48.2% |
| EV director net CI lower bound > 0? | no | no | no | no |
| Drift baseline mean PnL | −0.32 | −1.09 | −0.012 | −1.27 |
| Net any +EV config (CI>0)? | no | no | no | no |
| Dominant character | mild SELL drift | **heavy trend-drift** | **whipsaw, sub-50** | balanced, gross-signal |

Key reads:
- **No baseline edge** anywhere — pooled WR 44–47% (below the 50% no-skill line; the
  shortfall is the pessimistic tie-break + spread).
- **Every high-WR window is drift**, not edge: top windows' BUY+SELL WR sums to
  85–96% (one side wins only because the other symmetrically loses), and they are
  built from ~5 overlapping intraday days (the overlapping-sample trap proven for
  XAUUSD applies identically here — "259 trades" in `dow0+h02` ≈ 5 distinct days).
- **Rule strategies** are uniformly net-negative; the only ≥50% blips (NDX breakout
  BUY 50.2% +0.13, DAX breakout SELL 49.8% +0.03) are tiny-N (~1.5–1.9k) and within
  noise.
- **ML net is negative or breakeven for all.** Only XAUUSD's net CI *includes* zero
  (statistically breakeven); NDX/USOIL/DAX nets are robustly negative.
- **Gross-of-spread**, only XAUUSD (+0.275) and DAX (+0.539) show a positive
  directional signal — i.e. a faint real signal that the 6%-of-barrier spread erases.
  NDX is negative even gross (−0.55): its apparent profitability is pure trend
  exposure, not predictive skill. USOIL is ~flat gross (−0.006) — no signal at all.
- **Regime gating does not rescue any symbol.** All rule-based regime configs are
  net-negative; the only nominally-positive ML config is XAUUSD config-7
  (+0.07/trade) but its bootstrap CI straddles zero (noise, as established in the
  XAUUSD work). NDX config-4/6 are bull-block-only positive = drift, not skill.

---

## The 7 questions

**1. Best honest 70% WR candidate?**
None. No symbol reaches an honest, large-sample ≥70% WR that survives walk-forward +
drift control. The best *honest* (large-N, non-overlapping-meaningful) window is
XAUUSD `hour=17 SELL` at 57% overall — and even that is mostly net-short drift
(opposite-direction WR ~37%, sum ~94%). 70% appears only in tiny overlapping pockets
(~5 effective days) that fail any significance test.

**2. Best robust positive-EV candidate?**
None has a bootstrap 95% CI lower bound above zero. The *least-negative* is **XAUUSD**:
its ML net mean PnL is −0.01/trade with CI [−0.10,+0.09] (statistically breakeven) and
it is gross-positive (+0.275). DAX is gross-positive too (+0.539) but its net CI is
firmly negative [−1.39,−0.40] because the spread drag is larger relative to signal.

**3. Most stable fold-by-fold behaviour?**
**XAUUSD** — its ML fold WRs sit tightly around 50% (52.7/46.9/50.8/49.6) and window
std is low. **USOIL** is the most *numerically* stable (block std ~0.01–0.05) but it
is stably *losing*. NDX and DAX are the least stable (fold WR swings driven by regime,
e.g. DAX 45.5→51.8% as later blocks turn bullish).

**4. Which symbol is mostly drift-riding?**
**NDX**, decisively. Four of five blocks are strongly bullish; "always SELL" is
positive only in the lone bear block; ML is negative even gross; drift-control sums
are the highest (94–96%). Its only "profits" are passive long trend exposure.

**5. Which symbol deserves further research?**
**XAUUSD first, DAX second.** XAUUSD is the only one at statistical net-breakeven with
a positive gross signal and stable ~50% folds — with genuinely tighter execution cost
it could become marginal. DAX has the *largest* gross directional signal (+0.539) and
ML WR climbing to ~52% in later folds, so a lower-spread / larger-barrier variant is
worth a focused follow-up (caveat: the late-fold lift partly coincides with bullish
blocks, so it must be re-tested for regime-independence).

**6. Which symbol should be rejected?**
**USOIL and NDX** for 1m scalping. USOIL is a structural whipsaw — both directions
~44% WR (lots of double-touch SL-first losses), no signal even gross (−0.006), tiny
drifts; reject most decisively. NDX should be rejected as a *scalp edge* claim: it is
negative gross and only "works" as undifferentiated long trend exposure.

**7. What exact configuration, if any, is closest to production-worthy?**
None crosses the bar. The single least-bad is the **XAUUSD GBM director** (12 causal
features, expanding walk-forward, |p−0.5|≥0.10 selection, barrier 4.75 / spread 0.285):
net mean **+0.055/trade** but CI **[−0.055,+0.167]** straddles zero and worst-block
mean is −0.28. **Not deployable.** Do not ship any `*_scalp` model on these results.

---

## Reproducibility

- `mae.py` — engine, indicators, vectorized barrier sim (validated vs cached XAUUSD).
- `mae_battery.py SYMBOL` — full battery for one symbol.
- `results_{XAUUSD,NDX,USOIL,DAX}.txt` — captured raw output for each run.
- Prior XAUUSD deep-dive (windows non-overlapping significance, regime CI bootstrap):
  `../xau_scalp_research/FINDINGS.md` (Addenda 1–3).

**Bottom line:** across XAUUSD, NDX, USOIL and DAX there is no honest ≥70% WR and no
robust net-positive 1m scalp edge. XAUUSD and DAX carry a faint *gross* directional
signal worth narrow follow-up under realistic (lower) costs; NDX is trend-drift and
USOIL is whipsaw — both rejected. No production model is justified.
