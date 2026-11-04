# WTI / USOIL.FOREX — Nasdaq research transfer and oil derivatives

2026-10-02. Offline research only. The user authorized market-data downloads and all prior Nasdaq tests followed by oil-specific variations; no live/shadow process changes, orders or deployment.

## Phase 0: data and inventory, before oil outcomes

Instrument: canonical USOIL.FOREX; MT5 broker SpotCrude, verify current symbol metadata instead of assuming. USO ETF is not the subject. Download Supabase candle_cache M1/M5/M15/M30/H1/D1 and direct read-only MT5 reference/history. Obtain VIX and OVX (oil volatility), CL=F only as reference; own CFD daily close supplies tradable return features. Futures reference rolls and daily bars are not CFD fills.

Audit UTC/broker offsets by native-vs-direct-M1 price matching and session gaps, not Nasdaq volatility clock. Preserve raw exports and provenance. A source with unresolved clock stays excluded. No forward-fill intraday OHLC. Only completed bars; prior finished session macro; next M1 open with recorded spread when available. Unknown historical spread explicit proxy, spread stress and price-basis comparison. Preserve missing intervals and stop-gap ambiguity.

## Phase 1: complete prior Nasdaq family transfer

Inventory the first432 strategy definitions; expanded1620 strategy/geometry definitions;20 mechanism derivatives including their parent/rejected/blind controls;22 synthesis definitions and CAPREV/CHASE controls;22 final path/open/overnight/capital definitions. Deduplicate definitions but retain source-to-test coverage. Test discarded alternatives as well as selected candidates. Include original day-gate K1/K3/K5/K5b/K6 where definable from completed oil data. Claims requiring actual Nasdaq bot intentions cannot become oil bot evidence from candles; download oil decision/trade history if accessible, otherwise mark not reproducible.

Primary transfer retains dimensionless signal thresholds and elapsed-minute horizons. Oil price units: minimum ATR stop0.05 USD/barrel; fixed oil reference TP1.04% / SL1.49%, borrowed from existing project oil research rather than Nasdaq80/110. Report this as scale adaptation. A literal Nasdaq nominal-distance diagnostic is separate and cannot be called an economically equivalent oil test. Main CFD spread proxy0.03 USD and0.002 per-side slip only where quotes missing; actual recorded spread otherwise. Stress spread3, slip0.01, entry+1M1, 1:1 geometry, fixed oil geometry as appropriate.

Primary micro tests keep Nasdaq Mon–Thu03:00–15:30 NY window/15:55 deadline for a faithful control. Oil-specific session changes only in phase2. M1/M3/M5/M15 triggers, same M1 execution; native M15/M30/H1 longer samples separately, not counted as independent events or next-M1 validation. CAPREV initial transfer uses exact Nasdaq09:30–16:00 reference window, prior oil returns−1.5%/5day−4%, VIX18.4, first dip03:00–15:00, daily-vol stop, same-day/next-session exit. Interpret lack of support before adapting.

Chronological split after input audit based on available complete days. Selection uses discovery periods only. Lock oil derivative definitions before validation/final-period results. Purge crossing outcomes. Earlier Nasdaq selection counts are not erased; distinguish zero-oil-training transfer from oil-selected exploration.

## Phase 2: oil-specific ideas

After phase1 discovery, write a separate protocol with five economic mechanisms and bounded variants: own-vol normalized stress and OVX instead of equity VIX;09:00–14:30 energy window; EIA release/calendar-aware entries; symmetric long/short shock versus directional recovery; spread/ATR and risk-time efficiency. Do not assume which mechanism will win. No fitting on final oil test period. EIA holidays use authoritative published exceptions; historical unverified calendar years excluded from EIA-specific labels.

## Evidence / final deliverable

Coverage ledger lists every prior configuration tested or explicitly non-reproducible. Chronological/provider breakdown, rejected opportunities, matched/time/side controls, netR/WR/Wilson/EV bootstrap/day-paired delta/drawdown, best-days removal, one total position, costs, TF transfer, representative first wins/losses. Count ALL configurations and cells; controls are not independent samples. No minimum five profitable discoveries forced. Five oil hypotheses may be rejected. LIVE requires project go-live card >=150 suitable resolved events, both halves, causal timing/actual spread/one position plus prospective evidence; bar-only results remain research candidates.

## Post-download integrity finding (no rule changes)

Full MT5 overlap revealed cache candles interleaving identical SpotCrude quotes and a distinct CFD price base, with abrupt basis switches. Original cache results are retained as diagnostics, not selectively repaired. Cache outcomes on/after2026-08-28 NY are excluded from claimed validation evidence; primary recent/final evaluation uses the separate direct SpotCrude replay and its own macro warmup. These feeds overlap and share many exact prices, so they are not independent provider evidence. No source prices are spliced, no results-driven threshold changes. Native long tests remain historical transfer checks with missing spread; recent native results carry the same source-integrity caveat. The main scope is historical candle strategy replay, not actual bot decision/WAIT logs or actual fill PnL. No claim that every gate in the full running bot was reconstructed.
