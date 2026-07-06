# GOAL: XAUUSD 70%+ Win Rate — TP 5 pips / SL 5 pips

**Do not stop until 70% win rate is confirmed on clean, leak-free data.**

## Data
File: `/Users/melihcanodacioglu/Desktop/panel/1MDATA/mt5_xauusd_1m_bars.json`
Use only the **last 40%** of records. Split: 70% train / 30% test within that slice.

## Step 0 — Data Integrity (MANDATORY FIRST)
Verify before any modeling:
- No duplicate or out-of-order timestamps
- No forward-looking contamination
- OHLC validity: High >= max(O,C), Low <= min(O,C)
- No zero-volume bars or unrealistic spreads
Report findings. Drop bad rows, never patch them.

## Step 1 — Audit Existing Win Rates for Leakage
Current system win rates may be inflated. Check:
- Are entry_price/tp/sl set at signal creation time only?
- Does signal_lifecycle.py use only post-creation prices for outcomes?
- Are market_closed_invalid signals excluded from win rate calculation?
Do not use existing win rate numbers as baseline unless leak-free.

## Step 2 — Test Simple Approaches First
The user historically achieved good results with simple S/R and trend channels on 5m/15m. Current 150-feature models are likely overkill for 5-pip XAUUSD scalping. Test in order:
1. S/R bounce on 5m/15m pivot levels — TP/SL 5 pips
2. Trend channel (ascending/descending) on 5m — buy lower band, sell upper band
3. Confluence of both above
4. Apply session filter: London (07-10 UTC) + NY (13-16 UTC) only

## Step 3 — Lean ML If Simple Fails
Only if Step 2 cannot reach 65%+:
- Max 15-20 features (not 150)
- Label: did price hit +5 pips before -5 pips within 30 bars?
- Use XGBoost or LogisticRegression
- Validate with walk-forward, not random split

## Step 4 — Check AI-Ops Suggestions
Review any audit/improvement files in /docs/ or analysis_report.md for XAUUSD-relevant insights.

## Step 5 — Iterate to 70%
Per attempt: report win rate, signal count, session breakdown. If below 70%, identify failure mode and retry. If above 70% on test set, confirm on out-of-sample slice.

## Deliverables
- Which approach achieved 70% and key parameters
- Integration plan as new model_type="xauusd_scalp" (not replacing existing models)
- Update CLAUDE.md with new model documentation

## Hard Rules
- Zero lookahead bias
- 70% must hold on held-out test slice, not just training
- Simple and explainable over complex
- Pause for confirmation before touching production files
