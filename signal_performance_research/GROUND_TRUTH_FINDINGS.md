# Ground-Truth Verification — Are the Reported Win Rates Inflated?

**Question (user):** take every model's historical signals, look at the actual 1m
price after the signal time, and check whether the TP *really* got hit — to be sure
the reported win rates are not inflated.

**Method (independent, leak-free):** for each of **74,438 resolved signals** dated
≤ 2026-05-21 (the last day the `1MDATA/` 1m bars cover), reuse the **production**
TP/SL helpers (`calculate_target_prices` / `calculate_stoploss_price`) to build the
exact ladder the system commits to, anchor the entry at the **open of the first real
1m bar** at/after `created_at`, then **walk the real 1m bars** to whichever of TP1 or
SL is touched first. In-bar TP+SL ambiguity is resolved by the OHLC bar-path
heuristic (same rule the system's own `signal_replay_1m` uses). Reproducible:
`signal_performance_research/{fetch_with_prices,gt_replay_driver}.py`,
`signals_priced.json`, raw `ground_truth_results.txt`.

> Walk horizon is **generous** (720 min for a 5m signal … up to 7 d for 1d) — i.e.
> "did the committed TP1 eventually get hit before the SL." This is the honest answer
> to *"did the TP actually print"*, but note TP1 is **small relative to SL** on
> several configs, so a high WR here is **not** the same as net profit (see caveat).

---

## Headline: production WINs that don't survive 1m replay

| production label → ground truth | count | share |
|---|---|---|
| WIN → **WIN (confirmed)** | 36,978 | 49.7% |
| **WIN → LOSS (false win)** | **13,972** | **18.8%** |
| WIN → neutral (never resolved) | 612 | 0.8% |
| LOSS → WIN (false loss) | 16,317 | 21.9% |
| LOSS → LOSS (confirmed) | 6,431 | 8.6% |
| LOSS → neutral | 128 | 0.2% |

**Of 51,562 signals production marked WIN, the 1m replay confirms only 71.7%; 27.1%
were actually SL-first losses** on the real 1m path. That ~27% is the direct
fingerprint of the **5m-candle outcome eval**: a 5m bar that spans both TP and SL is
scored a win, but on 1m bars the SL frequently prints first. So yes — the reported
win counts **do** carry inflation.

But the inflation is **two-sided**: 21.9% of all signals were production-LOSSES that,
given a realistic holding window, *did* reach TP1 on the 1m bars. The tight live
evaluation window cuts off slow winners. Net effect differs sharply by symbol.

## By SYMBOL — reported vs ground-truth WR

| symbol | prod WR | GT WR (1m) | Δ | read |
|---|---|---|---|---|
| USOIL.FOREX | 79.3% (N=38.5k) | **72.6%** | **−6.6** | genuinely inflated ~7pp |
| GDAXI.INDX | 71.7% (N=7.5k) | 75.6% | +4.0 | reliable / slightly understated |
| NDX.INDX | 70.4% (N=6.7k) | 71.0% | +0.6 | reliable |
| XAUUSD | 50.4% (N=21.8k) | 71.0% | +20.6 | tight window *under*-counts |

USOIL — the headline driver (half the volume) — is the one clearly **over**-stated:
honest 1m WR is ~73% vs 79% reported. XAUUSD's live 50% is *low* because the short
eval window kills slow winners; given hours of hold its small TP1 prints ~71% of the
time (which, at TP1≈4 / SL≈8, is still not a profit edge — see caveat).

## By MODEL — where the reported WR is most inflated

| model | prod WR | GT WR (1m) | Δ | verdict |
|---|---|---|---|---|
| **ml:nasdaq_precision** | 76.7% | 53.3% | **−23.3** | most inflated (tiny N=30) |
| **ai_panel** | 82.7% | 62.1% | **−20.6** | premium WR badly overstated |
| **ml:ultra_safe** | 81.9% | 65.5% | **−16.4** | "highest-confidence" → −16pp |
| ml:aggressive | 79.4% | 65.8% | −13.6 | overstated |
| ml:balanced | 72.9% | 65.2% | −7.6 | overstated |
| ml:full_power | 72.2% | 65.4% | −6.8 | overstated |
| ml:main | 72.2% | 66.0% | −6.2 | overstated |
| ml (legacy) | 62.8% | 57.2% | −5.6 | overstated |
| emel_inverse | 82.6% | 76.7% | −5.8 | mild (N=86) |
| **meta** | 78.2% | 75.5% | −2.8 | **reliable** |
| **smc** | 73.6% | 72.8% | −0.7 | **reliable** |
| pulse3 | 70.3% | 74.3% | +3.9 | understated |
| pulse2 | 69.0% | 74.0% | +5.1 | understated |
| pulse1 | 64.0% | 72.6% | +8.6 | understated (slow winners) |
| emel | 61.5% | 75.9% | +14.4 | understated |

**The "premium" models are the worst offenders.** Every confidence-gated ML scope
(`ml:ultra_safe`, `ml:aggressive`, `ml:*`) and `ai_panel` — exactly the ones whose
80%+ headline WRs look best — **lose 14–23pp** under honest 1m replay. Their high
reported WR is substantially a 5m-eval artifact. By contrast **`meta` and `smc` are
trustworthy** (Δ within 3pp), and the high-volume `pulse`/`emel` models are if
anything *under*-reported.

---

## Bottom line

1. **Yes, the headline win rates are inflated where it matters most.** 27% of all
   production "wins" are SL-first losses on the real 1m path; USOIL (the volume
   driver) is ~7pp over-stated, and the premium ML/`ai_panel` scopes are 14–23pp
   over-stated.
2. **`meta` and `smc` are the only models whose reported WR holds up** under 1m
   ground truth (Δ ≤ 3pp). Trust those; heavily discount `ml:ultra_safe`,
   `ml:aggressive`, `ai_panel`.
3. **High WR ≠ profit (critical caveat).** This replay walks to TP1 (small) vs SL
   (large) over a generous hold, so even a 70%+ GT-WR can be net-negative because of
   the asymmetric reward:risk. This is fully consistent with the prior edge research
   ([[xauusd-scalp-no-edge]], [[multi-asset-scalp-no-edge]]): no robust net +EV on any
   instrument. A trustworthy WR (meta/smc) is necessary but not sufficient for an edge.
4. **Caveat on USOIL levels:** the USOIL TP/SL config was widened on 2026-05-27
   (TP1 0.02%→0.10%), *after* these signals fired, so the USOIL GT levels here are the
   newer wider ladder — its true historical inflation may be even larger than −6.6pp.
