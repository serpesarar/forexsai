# NDX Reflex Engine — Research Findings (2026-07-04)

Full protocol in DESIGN.md. Everything below is deduped, friction-included
(bid/ask replay + 1pt slippage), triple-barrier labeled with SL-first ambiguity.

## Data
- Dukascopy `usatechidxusd` ticks: 144 trading days 2025-01-01→06-19, 28.1M ticks, clean
  (0 crossed quotes, monotonic). ~16 weekdays have missing hour-files (gap registry excludes them;
  re-download recommended). Spread: 1.46 pts US session / 3.46 overnight. Download still running toward 2025-12.
- Transfer set: real USTEC 1m `candle_cache` 2026-02-11→07-03 (140,533 bars), synthetic bid/ask at 2.0 pts.

## Event dataset
5,763 events / 114 days, 6 families, 30-min per-family refractory, 13:00–20:00 UTC only.
Geometry frozen per family on first-60%-of-days ONLY (max-EV over 36-cell grid, n≥30).

## Verdicts (chronological 60/40 split + battery + 2026 transfer)

| Family | Verdict | Evidence |
|---|---|---|
| **mom_cont SELL** (tp1.5/sl1.0 ATR, ts30) | ✅ **SHIP-CANDIDATE** | 2025 holdout +0.495R WR62 (n=45); friction 2.0× +0.33R; placebo real +0.41 vs p95 −0.03; bootstrap P(EV>0)=99.3%; **2026 transfer n=98 WR54 +0.290R**, 5/6 months positive |
| **mom_cont BUY** (tp1.5/sl1.5 ATR, ts60) | ✅ **SHIP-CANDIDATE** (2026-confirmed) | 2025 holdout +0.108R (bootstrap only P=0.82 — small n); **2026 transfer n=135 WR67 +0.293R**, every full month positive |
| vwap_rev (ML-gated, Tier A+B) | ❌ as-is / 🔬 geometry retry | holdout WR 71.7% n=184 but EV +0.045R dies at 1.5× spread. Calibration PERFECT (quintiles monotone, ρ=1.0) — the model ranks; the tight TP doesn't pay. Retry: wider TP on gated subset, train-side only |
| chan_rev (ML-gated) | ❌ as-is / 🔬 same retry | holdout WR 66.4% n=134, EV +0.008R; same friction death, same perfect calibration |
| sr_react | ❌ | holdout marginal, no robust EV |
| sweep | ❌ DEAD | train-OOS +0.28R → holdout −0.21R (overfit) |
| orb | ❌ DEAD | holdout −0.01R, n small |

## Key lessons
1. **Raw triggers are −EV** (chan/vwap/sr/sweep −0.07..−0.26R at base rate) — consistent with the
   2026-05-29 "no naive scalp edge" battery. Only momentum-continuation is +EV raw.
2. **The ML layer genuinely ranks** (isotonic quintiles monotone on unseen data in all 3 fitted
   families) but ranking ≠ tradability: reversion geometry pays too little after spread.
   Next iteration: re-run geometry grid restricted to model-gated events (train split only).
3. **2025-proxy → 2026-broker transfer works** for candle-only (Tier A) logic — the edge is in
   bar geometry, not feed idiosyncrasies.
4. Tier B (microstructure) helped vwap_rev (+0.03R OOS) but nothing passed friction with it —
   park until the geometry retry.

## Combined ship-candidate profile (2026 transfer, both directions)
~2.3 events/day, 233 resolved / 100 days, blended EV ≈ +0.29R net. At 1.0R risk sizing this is
a real but modest edge — sized correctly it compounds; oversized it drowns in variance.

## 10-group ≥70% WR proof (2026-07-04, goal-directed run)

High-precision mode (`research/high_precision.py` → `research/prove_70.py`): per-family
(geometry, calibrated-p threshold τ) selected on the TRAIN split only (target 85% train-OOS WR),
frozen, then evaluated on 10 disjoint never-used-for-selection date groups.
Frozen: chan_rev tp0.4/sl2.5 τ0.80 · vwap_rev tp0.4/sl2.5 τ0.78 · sweep tp0.4/sl2.0 τ0.81 ·
mom_cont tp0.4/sl1.5 base-rate. Attempt #1 (78% target, vwap only) failed 5/10 — disclosed;
attempt #2 passed with wide margin:

| Group | n | WR | EV |
|---|---|---|---|
| G1–G5 2025 holdout (proxy, chunks) | 176–232 | 77.8–85.8% | −0.01..−0.13R |
| G6–G10 2026 broker (monthly Feb–Jun) | 325–555 | 79.7–83.4% | −0.05..−0.10R |
| **Pooled** | **3,374** | **~82%** | **≈ −0.06R** |

**VERDICT: 70% WR proven in all 10 groups (floor 77.8%).**

⚠️ **THE CATCH — read before trading this mode:** the WR is bought with asymmetric geometry
(TP 0.4×ATR vs SL 2.0–2.5×ATR). At tp0.4/sl2.5 the arithmetic breakeven is ~86% WR, so this
stream is slightly **negative-EV after friction in every group**. It wins 82% of the time and
bleeds slowly. This is the exact XAU lesson (high patient WR ≠ profit) reproduced under lab
conditions. The **money-making** configuration remains mom_cont at symmetric geometry
(+0.29R, WR 54–67%). High-WR mode is valid as a *signal-quality/UX layer* (e.g. panel display,
confidence proof) — not as a standalone book. Also note: no cross-family time-dedup in the
proof pooling, so n counts correlated same-minute events from different families more than once;
WR per event is unaffected.

## Next steps (in order)
1. Re-download the 16 damaged Dukascopy days + extend to 2025-12 (script already running).
2. Geometry retry for vwap_rev/chan_rev gated subsets (train-side); re-battery.
3. Formal bootstrap + regime slices on the 2026 transfer sample (n≈233).
4. Validate synthetic-spread assumption against real IC spread from `tickdata/` (MT5 box).
5. Phase L: live sidecar on MT5 box — mom_cont detector on closed 1m bars, shadow mode,
   `reflex_signals` table, own magic (+3), per-family flags, graduation at n≥50 within OOS band.
