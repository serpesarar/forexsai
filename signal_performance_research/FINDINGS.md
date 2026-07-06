# Production Signal Success Table — Models, Combinations, Days/Dates

Source: `prediction_logs`, **81,552 resolved signals** (status `completed`=WIN /
`stopped`=LOSS), 2026-02-19 → 2026-05-29 (~3.3 months). Combinations from the
system's own `meta_combination_stats` (105 combos) plus a derived co-occurrence check.
Reproducible: `signal_performance_research/analyze.py` (+ cached `resolved_logs.json`,
`meta_combos.json`, raw `results.txt`).

> **WR-scale caveat (important):** production "completed" = a TP was hit on **5m-candle
> outcome eval**, which the prior 1m-replay work showed is **geometry-inflated**
> (in-bar TP/SL ambiguity counts ambiguous bars as wins). So these are the **system's
> REPORTED numbers** — reliable for *ranking* models/combos/days relative to each
> other, but the absolute WRs are optimistic. The one place this is proven: **XAUUSD
> production WR = 49.8%**, exactly the leak-free ~50% from the research, i.e. when the
> instrument has no real drift to ride, the inflation disappears and the coin-flip shows.

Overall reported WR: **68.7%** (56,013 W / 25,539 L).

---

## 1. WR by MODEL

| Model | WR | N | Note |
|---|---|---|---|
| ai_panel | 83.4% | 614 | NY-session DeepSeek; small N |
| emel_inverse | 83.0% | 88 | tiny N — ignore |
| **ml:ultra_safe** | **80.9%** | 1142 | highest-confidence ML scope |
| ml:aggressive | 78.9% | 1256 | |
| **meta** | **77.4%** | 3753 | 6-model fusion, solid N |
| ml:balanced | 73.5% | 3060 | |
| ml:full_power / ml:main | 72.8% | ~3300 | |
| **smc** | **72.7%** | 5332 | |
| pulse3 | 69.4% | 20839 | highest-volume model |
| pulse2 | 68.1% | 13897 | |
| pulse1 | 63.2% | 22184 | weakest, highest volume |
| emel | 62.1% | 2325 | weakest of the strategics |

**Read:** confidence-gated scopes (`ml:ultra_safe`, `ml:aggressive`) and `meta` lead;
`pulse1` is the workhorse but the weakest. `emel` underperforms its peers.

## 2. WR by SYMBOL (the decisive split)

| Symbol | WR | N |
|---|---|---|
| USOIL.FOREX | **78.7%** | 41,361 |
| GDAXI (DAX) | 72.4% | 8,787 |
| NDX | 69.2% | 7,453 |
| **XAUUSD** | **49.8%** | 23,951 |

USOIL drives the headline (half of all volume at ~79%). **XAUUSD is a coin flip in
production** — this is the live-data confirmation of the multi-asset research (XAUUSD
no edge; USOIL/NDX inflated by trend). Best model×symbol cells: `ml:ultra_safe|USOIL`
91.0% (714), `smc|USOIL` 86.0% (3044), `ml:balanced|DAX` 86.3% (315),
`meta|USOIL` 83.3% (1734). XAUUSD's best is only `meta|XAUUSD` 65.5%.

## 3. WR by DAY-OF-WEEK

Mild effect. **Tuesday best (70.7%)**, then Thu/Fri/Mon ~68%, Wed weakest (67.4%).
Per model: `meta` strong all week (Tue 81%, Fri 78%); `smc` peaks **Thursday 78%**;
all pulse models peak **Tuesday**. No weekend edge (Sun tiny N).

## 4. WR by HOUR (UTC) — when to trust signals

Best hours: **h21 (75.3%), h22 (73.8%), h13 (73.0%), h14 (72.9%)** — i.e. the NY
session / NY-overlap and the late-NY close window. Asia/early hours rank lower.

## 5. Best / Worst DATES

- **Best:** mid-May 2026 cluster — 05-18 (85.2%), 05-11 (84.5%), 05-19 (84.0%),
  05-20 (82.5%), 04-30 (82.3%), 05-07 (82.2%). Strong trending stretch.
- **Worst:** 05-28 (42.9%), 04-06 (45.8%), 05-25 (47.3%), 04-09/04-10 (~49%). (05-29
  shows 29.7% but only 138 signals = today, partial — ignore.) Worst days cluster in
  choppy/transition periods.

## 6. COMBINATIONS — system's `meta_combination_stats`

Best by **win rate** (min 60 signals) — dominated by USOIL multi-model consensus:

| combo | symbol | WR | N | PF | EV(pips) |
|---|---|---|---|---|---|
| emel+pulse1+pulse2+smc | USOIL | 84.3% | 280 | 2.26 | +0.02 |
| emel+pulse1+pulse2+pulse3+smc | USOIL | 84.2% | 328 | 2.37 | +0.02 |
| pulse1+pulse2+pulse3+smc | USOIL | 82.8% | 371 | 2.22 | +0.03 |
| pulse2+pulse3+smc | USOIL | 79.7% | 532 | 2.76 | +0.03 |
| pulse3+smc | USOIL | 77.1% | 638 | 2.66 | +0.04 |

Best by **expectancy (pips/trade)** — high-EV but watch the low-WR/high-variance ones:

| combo | symbol | WR | N | PF | EV |
|---|---|---|---|---|---|
| pulse3+smc | DAX | 30.8% | 198 | 5.31 | +31.86 | ← few big trend wins, risky |
| emel+pulse1+pulse3+smc | NDX | 73.4% | 94 | 5.26 | +27.39 |
| pulse1+smc | NDX | 70.3% | 74 | 2.26 | +21.86 |
| emel+pulse1+pulse3+smc | XAUUSD | 71.3% | 94 | 7.05 | +14.52 |
| emel+pulse1+pulse2+pulse3+smc | XAUUSD | 72.2% | 108 | 6.92 | +13.74 |

**Notable:** on XAUUSD — a 50% instrument solo — the **full 5-model consensus stack
reaches 72% WR with PF ~7**. The consensus filter is doing real work: requiring many
independent models to agree removes the coin-flip entries. (N is modest, ~100; worth
watching as it accumulates.)

## 7. DERIVED CONSENSUS (models agreeing same direction, 15-min bucket)

| # models agreeing | WR | N |
|---|---|---|
| 1 | 65.8% | 7,761 |
| 2 | 63.9% | 13,791 |
| 3 | 65.1% | 18,005 |
| **4+** | **72.3%** | 41,995 |

Consensus of **4+ models lifts WR ~+7pp** over 1–3. Strongest agreeing **pairs**:
`meta+ml:ultra_safe` **89.7%** (3957), `meta+ml:aggressive` 86.7%, `meta+ml:*` ~85%,
`ml:aggressive+ml:ultra_safe` 82.0%. **The meta + high-confidence-ML agreement is the
single strongest live signal in the system.**

---

## Bottom line / how to use this

1. **Best standalone models:** `ml:ultra_safe` (80.9%), `meta` (77.4%), `smc` (72.7%)
   — confidence-gated and fusion models beat the raw pulses.
2. **Best combination:** require **meta + ml:ultra_safe agreement** (≈90% reported), or
   the **4+ model consensus** stack; on USOIL the pulse+smc stacks hit ~84%.
3. **Best conditions:** **Tuesday**, **NY session (h13–14, h21–22 UTC)**, trending
   stretches (mid-May was the strongest).
4. **Weakest:** `pulse1` and `emel` solo; **XAUUSD any single model** (~50–65%);
   Wednesdays and choppy dates.
5. **Reliability caveat:** absolute WRs are 5m-eval-inflated. XAUUSD's honest 49.8%
   proves the inflation is real where there's no trend. Trust the **rankings and the
   consensus lift**, discount the absolute level — especially for USOIL/NDX/DAX whose
   high WRs partly reflect strong directional drift over this window.
