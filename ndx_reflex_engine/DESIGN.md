# NDX Reflex Engine — Design Document

> Event-driven real-time NASDAQ scalping engine.
> Created 2026-07-04. Status: research build (Phase R).
> Prime directive: **honest labels, event-driven triggers, calibrated probabilities, abstention by default.**

---

## 0. Why this shape (and not "predict every candle")

Prior in-house research (2026-05-29 battery, replay corrections, walk-forward studies) proved:

- **No honest 70% WR @ 1:1 exists** for continuous 1m NDX scalping; friction eats marginal signals.
- **Backend lifecycle outcomes are inflated 14–23pp** vs honest 1m replay → all labels must come from bar/tick replay.
- **Validated edges are event-shaped**: channel-z ≥2 / VWAP-z ≥1.5 reversion (44→74–86% WR, OOS-robust),
  momentum-continuation NDX BUY, VIX-regime direction (+25pp), M15 mean-reversion indicator filters (77–83%),
  NY-session concentration.
- MACD cross: no edge (2026-07-03). Analog-kNN daily direction: no edge (CORTEX backfill). Both excluded.

Therefore: the engine **waits for a trigger event**, extracts a rich feature snapshot, and a **calibrated
meta-model estimates P(TP-before-SL)** for that specific instance. No event → no opinion. This is
meta-labeling (López de Prado): hand-validated primary signals + ML secondary filter.

---

## 1. Data inventory (audited 2026-07-04)

| Source | Coverage | Quality | Role |
|---|---|---|---|
| Dukascopy `usatechidxusd` ticks (`~/dukascopy_us100/data`) | 2025-01-01 → 2025-06-19 (download continuing toward 2025-12), 144 trading days, 28.1M ticks | Clean: 0 negative spreads, monotonic ts (epoch ms UTC), `timestamp,askPrice,bidPrice` only (no volume). 99/122 weekdays full US core session; ~16 days have missing hour-files (repairable); 7 US holidays. Spread: median 1.46 pts US session / 3.46 overnight. Price range 16,327–22,245 incl. April-2025 crash → regime diversity. | **Research/training only.** PROXY feed — not IC Markets USTEC. |
| `candle_cache` USTEC 1m (Supabase) | 2026-02-11 → live, 140,533 bars, continuously maintained by `data_recorder.py` | Broker-true prices | **Transfer-validation OOS set + live features** |
| `candle_cache` 5m/15m/30m/1h | 5m since 2026-03, 1h since 2025-09 | good | MTF context |
| `indicator_snapshots` (28-ind JSONB, 1m→1h) | since 2026-06-25 | good | **live feature contract** (training features recomputed offline to match) |
| `tick_recorder.py` archive (MT5 box, `tickdata/*.csv.gz`) | running "for a while" (≈ late June 2026 →) | bid/ask/last/vol, 30s poll | **live microstructure features + IC-true spread/friction measurement** |
| `vix_live` + yfinance VIX | live | good | regime feature |
| Economic calendar (backend gate) | live | fail-open | event veto |

**Critical constraint:** tick archive (2025) and broker candles (2026) do not overlap in time.
⇒ We can never row-match them. Instead: **train on 2025 proxy data, transfer-test on 2026 broker
1m candles at the event level** (all triggers are computable from 1m bars alone; tick features enter
as *optional* columns that the model must survive without — see §5 "two-tier features").

**Proxy caveats (explicit):**
- Dukascopy US100 CFD ≠ IC Markets USTEC: different LPs, slightly different price levels & spreads.
  Mitigation: (a) all features are *relative* (z-scores, ATR-normalized distances, ratios), never absolute price;
  (b) backtest friction uses Dukascopy *measured per-event spread* × **1.5 safety multiplier**, later replaced
  by the IC spread distribution measured from `tickdata/`; (c) final gate = transfer test on 2026 USTEC candles.
- No tick volume ⇒ volume features come from candle volume (broker) and tick-count/tick-rate (proxy of activity).

---

## 2. Architecture

```
                 ┌──────────── OFFLINE (research, this repo dir) ────────────┐
 ticks 2025 ──► ingest (parquet) ──► 1m bid/ask bars + micro cols ──► gap registry
                                            │
 1m bars ──► trigger detectors (§4) ──► EVENT rows ──► feature pack (§5)
                                            │                │
                                    triple-barrier labels (§6)│
                                            └────────┬───────┘
                                                     ▼
                                   per-family LightGBM + isotonic calibration (§7)
                                                     ▼
                                   validation battery (§8): purged WF, placebo,
                                   friction, bootstrap, 2026 transfer test
                 └───────────────────────────────────────────────────────────┘
                                                     ▼   (frozen model + thresholds)
                 ┌──────────── ONLINE (MT5 box sidecar, Phase L) ────────────┐
 MT5 1m/5m/15m candles + tick_recorder tail + VIX + calendar
        ──► same trigger code ──► same feature pack ──► score ──► EV gate
        ──► shadow signal (CSV + Supabase `reflex_signals`) with explanation
        ──► (after shadow graduation) bot scope, own magic, LIVE flag default OFF
                 └───────────────────────────────────────────────────────────┘
```

Directory layout:

```
ndx_reflex_engine/
├── DESIGN.md                ← this file
├── config.py                ← all constants, paths, thresholds (no magic numbers elsewhere)
├── pipeline/
│   ├── ingest_ticks.py      ← Dukascopy CSVs → per-day parquet (canonical schema)
│   ├── build_bars.py        ← ticks → 1m bars: bid/ask/mid OHLC, spread stats, tick rate,
│   │                           direction-run stats, micro-imbalance proxies
│   └── gap_registry.py      ← per-day usable-interval index; labeling refuses to cross gaps
├── triggers/                ← §4 detectors; each returns Event(ts, direction, family, meta)
├── features/pack.py         ← §5 feature computation (offline == online, one code path)
├── labels/triple_barrier.py ← §6
├── models/train.py, calibrate.py, explain.py
├── validation/battery.py    ← §8
├── live/                    ← Phase L sidecar (runs on MT5 Windows box)
└── data/                    ← parquet outputs (gitignored)
```

---

## 3. Tick aggregation decisions

- **1-minute bid/ask bars** as the labeling substrate: `bid_o/h/l/c, ask_o/h/l/c, mid_o/h/l/c,
  spread_mean/med/p95, n_ticks, tick_rate_std, up_ticks, down_ticks, sign_flip_ratio,
  max_run_len, quote_velocity (Δmid p95), intra_minute_range`.
  BUY fills at ask, exits at bid (and vice versa) — spread is *inside the replay*, not a constant haircut.
- **Event-time micro-windows**: at each trigger, features over trailing 30s/60s/300s tick windows
  (tick-rule imbalance, spread state vs its own 20-day hour-of-day baseline, quote acceleration,
  burst detection). These are the **Tier-B features** (§5).
- No sub-minute bars as a global substrate (storage/complexity not justified); micro-windows are
  computed on demand around events only.
- **Gap policy:** the gap registry marks any minute with no ticks inside a trading session. Rules:
  a trigger whose lookback crosses a gap > 5 min is dropped; a label whose barrier window crosses
  any gap is dropped (not imputed). Holiday/early-close days are handled by a static NYSE-2025 calendar.

---

## 4. Trigger detectors (primary signals)

Each detector is deliberately simple, parameter-light, and must clear a **standalone base-rate bar**
(win rate ≥ break-even + 5pp at its family geometry on the training years, and survive placebo) before
its events are given to the ML layer. Detectors that fail stay in the dataset flagged `family_dead`
for research but never trade.

| # | Family | Definition (all on 1m/5m mid bars) | Prior evidence |
|---|---|---|---|
| T1 | `chan_rev` | linreg-channel z ≥ 2.0 against direction, 50-bar window (claude_decider `rev_chan` definition, direction-aligned) | 74% n=493 / OOS 76% live-validated |
| T2 | `vwap_rev` | session-anchored VWAP z ≥ 1.5 (tick-count-weighted on proxy; volume-weighted live) | validated (bot CHREV) |
| T3 | `sr_react` | touch + rejection of a 1m S/R zone (≥4 touches, zone width ≤10 pts — bot `sr_zones.py` params) with close-back-inside confirmation bar | bot live logic, unquantified alone |
| T4 | `sweep` | wick pierces zone/prior-day-high-low/round-number by ≤ k·ATR then closes back through it within ≤3 bars (liquidity sweep / stop-hunt reclaim) | NEW — must earn its place |
| T5 | `orb` | NY open (13:30 UTC / DST-aware) 15-min opening range break **and** failure-back-inside variants; both directions | NEW |
| T6 | `mom_cont` | M15 momentum-stretch > 2.0×ATR in trend direction, pullback ≤38% then 1m resumption; BUY-biased per prior evidence | bot momentum family, +EV NDX BUY |
| T7 | `vol_shock` | 1m realized-vol burst > p99 of trailing 5 days + directional follow-through test | NEW — likely a *veto* feature if not tradable |

Trigger hygiene: per-family 30-min refractory period (no double-firing on the same episode);
events within calendar-gate windows (±30 min high-impact) are generated but flagged `calendar_blocked`
(so the model can *learn* the difference, but live they're vetoed).

---

## 5. Feature pack (~80 features, two tiers)

**Tier A — bar-derived (always available live from MT5 candles):**
trend stack states (EMA5/10/20/50/200 on 1m & 5m & 15m), RSI-14 (1m/5m/15m), ADX bucket (claude_decider edges
0/18/25/35), ATR(14) level + ATR percentile vs 20 days, distance-to-trigger-zone in ATRs, bars-since-session-open,
UTC hour & NY-session phase, day-of-week, opening-gap size, prior-day range position, MTF alignment score,
channel/VWAP z at trigger, consecutive-bar run stats, wick-ratio stats last 5 bars, 5m volume z-score (broker),
VIX level + 1-day Δ + regime bucket (18.4 threshold), distance to round numbers (100s/500s), signed distance
to prior-day high/low, event-family one-hots + family-specific meta (zone touch count, sweep depth, OR width…).

**Tier B — tick-derived (available in training 2025 + live via tick_recorder; MISSING in 2026 transfer test):**
trailing 30s/60s/300s tick-rule imbalance, tick-rate vs hour-of-day baseline (burst z), spread state z,
quote velocity/acceleration, sign-flip ratio, max directional run, micro-drawdown shape since trigger bar open.

**Rule:** the model is trained twice — Tier A-only and Tier A+B. The A-only model is the **deployment
floor** (must pass validation alone, and is the only thing testable on 2026 broker candles). Tier B is
accepted only if it improves *calibrated* OOS EV by a margin, and live it must come from IC tick_recorder
(never assume proxy microstructure == broker microstructure).

No absolute prices anywhere. All features z-scored/ATR-normalized/bucketed. Winsorized at p1/p99 of train folds.

---

## 6. Labels — triple-barrier on honest replay

- Entry: next 1m bar open **at ask** (BUY) / **bid** (SELL) after the trigger-confirm bar closes. No same-bar fills.
- Barriers per family (from MFE/MAE grid on train folds only — like `tp_sl_recommendations`):
  initial grid TP ∈ {0.5, 0.75, 1.0, 1.5}×ATR, SL ∈ {0.75, 1.0, 1.5}×ATR, time-stop ∈ {30, 60, 120} min.
  One frozen geometry per family before ML training (no per-event geometry — that leaks the label into the task).
- Intrabar ambiguity: if TP and SL are both inside one 1m bar's range → **label = LOSS** (SL-first,
  conservative; matches the "27% of wins are SL-first" finding).
- Exits at bid (BUY) / ask (SELL); on proxy data the bar's own bid/ask series is used directly.
- Time-stop exit → label by sign of PnL net of spread; also store continuous outcome (R-multiple) for
  regression diagnostics.
- Any barrier window crossing a data gap / session close ⇒ event dropped (no weekend-hold labels; this
  is a scalper — flat before 20:45 UTC, no events after 20:00 UTC).

---

## 7. Model

- **LightGBM binary classifier per trigger family** (chan_rev, vwap_rev, sr_react pooled with sweep if n small;
  mom_cont separate; orb separate). Families with < 400 train events after dedup don't get a model — they trade
  (or not) on their base rate alone or stay shadow.
- Monotone constraints where domain knowledge is unambiguous (e.g. spread-state z: higher → never-better).
- **Isotonic calibration** on walk-forward validation folds (never train folds).
- **Decision rule:** trade iff `p_cal·TP − (1−p_cal)·SL − friction ≥ margin` with `friction` = measured
  per-event spread×1.5 (proxy) → replaced by IC-measured spread (live), and `margin` = 0.05R.
  Probability alone is never the gate; EV is.
- **Explanation payload** per signal: family + top-5 SHAP contributions + claude_decider-style evidence-pack
  base rates (bucketed rev_chan/adx/session cells with n) → human-readable "why" string. This reuses/extends
  `claude_decider/evidence.py` bucket edges so live and research explanations agree.

Hyperparameters: small fixed grid (depth ≤ 5, leaves ≤ 31, min_child ≥ 50, feature_fraction 0.7,
lr 0.05, early stopping on fold-val loss). No Optuna-style search — the search itself overfits at n≈10³.

---

## 8. Validation battery (all must pass, per family)

1. **Purged walk-forward:** 6 chronological folds over 2025, 1-day embargo around fold boundaries,
   60-min same-family dedup before any statistic.
2. **Friction stress:** EV must stay > 0 at 1.0×, 1.5×, 2.0× measured spread (+1 pt slippage).
3. **Placebo:** trigger times shifted ±(30–180) min randomly ×200 → real edge must beat 95th percentile
   of placebo EV distribution. Feature-shuffle placebo for the ML lift specifically.
4. **Bootstrap:** stationary block bootstrap on the deduped event PnL series → P(EV > 0) ≥ 97.5%.
5. **Calibration check:** Brier + reliability curve on OOS folds; predicted-p deciles must be monotone in
   realized WR (tolerance band); otherwise the model trades at base rate only.
6. **Regime slice:** must not be negative in ≥2 of {VIX<18.4, VIX≥18.4, trend, range} slices
   (April-2025 crash is in-sample on purpose — report it separately).
7. **2026 transfer test (Tier A model only):** run triggers + model on broker USTEC 1m candles
   2026-02-11→now, label by the same replay, compare WR/EV to 2025 OOS bands. This is the FINAL gate —
   a model that works on Dukascopy 2025 but not USTEC 2026 does not ship.
8. **ML-lift test:** the calibrated model must beat the *trigger-only base rate* strategy on OOS EV;
   if it doesn't, ship the trigger with base-rate gating and no ML (honesty over sophistication).

---

## 9. Live pipeline (Phase L — after battery passes)

- **Placement:** sidecar process on the MT5 Windows box (next to bot / data_recorder / tick_recorder):
  direct `mt5.copy_rates_from_pos` for 1m/5m/15m, tail of today's `tickdata/*.csv.gz` for Tier B,
  VIX + calendar from backend HTTP (fail-open to Tier A-only / calendar-closed behavior).
- Poll cadence 5s; triggers evaluated on closed 1m bars; micro-features on the tick tail.
- Output: `reflex_signals` Supabase table (new migration): ts, family, direction, entry/tp/sl, p_cal,
  ev_r, tier (A/A+B), explanation JSON, mode (shadow/live), resolved outcome via its OWN 1m replay
  resolver (never signal_lifecycle).
- **Shadow graduation, per family:** n ≥ 50 resolved shadow signals AND realized WR inside the OOS
  confidence band AND realized spread/slippage within assumption. Then bot gets a 4th magic slot
  (`MAGIC+3`), 0.01–0.05 lots, `REFLEX_LIVE=0` default, per-family enable flags, daily loss cap shared
  with existing `DAILY_MAX_LOSS`.
- Panel: one card later (backend reads `reflex_signals`); NOT in the 6-model ensemble — this engine is
  deliberately isolated from pulse/emel weighting.

---

## 10. Honesty guardrails (standing rules)

- Nothing trains or is scored on `prediction_logs` lifecycle outcomes.
- Every statistic reported anywhere is post-dedup, post-friction.
- Any config change that touches triggers/geometry/thresholds invalidates the frozen model → re-run battery.
- Data repairs: incomplete Dukascopy days get a re-download attempt; still-broken hours stay in the gap
  registry (never imputed).
- The engine reports "no trade" as its default state; expected live cadence is ~2–6 events/day in NY session.
- If Tier B features fail transfer/live checks they are dropped without ceremony; Tier A floor always deployable.
