---
name: trade-edge-lab
description: Analyze ForexSAI MT5/bot trade mistakes and decision-time chart confluence, then validate candidate filters on later data. Use for trade autopsies and strategy discovery, not routine UI or signal edits.
---

# Trade edge lab

Use this workflow to turn recorded trades into testable hypotheses. Keep the analysis offline and leave production trading behavior unchanged unless the user separately requests and authorizes an implementation.

1. Identify the exact trade cohort, source files, symbol, dates, strategy version, outcome definition, and stop/target geometry. Read `CODEX_PROJECT_CONTEXT.md` and the relevant existing research report. Distinguish actual MT5 fills from replayed or inferred outcomes.
2. Reconstruct only information available when each trade decision was made. For 1m bars stamped at bar **start**, a bar is available only when `bar_ts + 60 <= entry_ts`; exclude stale or gapped windows. For MT5 historical queries use `backend/research/_bars_upto.py` and verify broker timezone normalization.
3. Compare winners and losers at the decision point. Include conflicting signals and the trades a proposed gate would reject. When possible, include WAIT/rejected opportunities to avoid learning only from trades the bot already chose.
4. Freeze candidate definitions before looking at the final period. Use chronological out-of-sample evaluation, an embargo for outcomes crossing the split, realistic entry and spread, and per-symbol/side/epoch breakdowns. Report sample size, win rate with uncertainty, mean net R, drawdown, and comparison to the unchanged baseline. Count all configurations tried; do not select a rule from the test period and then describe that same period as independent validation.
5. Plot representative winning and losing trades with entry, exit, TP/SL, and decision-time context. State whether the chart is descriptive or supports a causal rule. Avoid selecting only favorable examples.
6. Treat any observed 70%+ win-rate subset as a **hypothesis** until later data, realistic execution, and the project's go-live card support it. High win rate alone can have negative expected R. Keep exploratory candidates in shadow.

For local JSON trades plus 1m CSV bars, use `scripts/audit_trades.py`; read [the data contract](references/data_contract.md) for its input assumptions and output interpretation. The script creates a Markdown report, JSON summary, and two-trade chart without contacting production services. If the task needs a different source or a full strategy replay, adapt the existing project research pipeline rather than forcing this simple audit script to make an unsupported claim.

Example from the repo root:

```bash
python3 .agents/skills/trade-edge-lab/scripts/audit_trades.py \
  --trades research/trade_mgmt_ndx/trades.json \
  --bars research/trade_mgmt_ndx/bars_1m.csv \
  --symbol NDX.INDX \
  --out output/trade-edge-lab/ndx-pilot
```

Checks the script now enforces or surfaces (added 2026-09-30 after a pilot finding failed forward):

- `Clock alignment` must read `ok`. `MISALIGNED` means the trade and bar clocks disagree (this repo has seen +180 and +1230 minute export errors); stop and fix the export before reading any table. A constant price-basis gap between feeds is tolerated by design.
- Read the `Condition combinations` table, not only the score sum; a "2 of 3" bucket can be one specific combination.
- Compare `n` with the decision count in parentheses; split-leg positions opened in the same minute are one decision.
- Validate a selected subset with `--since <end of discovery data>` on a later export (MT5 CSV exports load directly). Precedent: pilot `tMP` 19/19 → forward 07-10..08-27 10/20, −2,151 USD; the pilot's worst bucket (0/3) was the forward period's best.

## Reddedilen fırsatlar (WAIT / kapı / veto)

`scripts/audit_skipped.py` botun kapı-atlama ve veto kayıtlarını 1m barlarla çözer ("kapı haklı mıydı?"). Önce simülatör botun gerçek TP/SL sonuçlarıyla kalibre edilir (<20 örnek ise durur). Logda TP/SL yok → 3 geometride (80/110, 80/60, 80/80) çözülür; aynı niyetin tekrar logları (neden, scope, yön) başına tek varsayımsal pozisyonla dedupe edilir. Yorum kuralı: **WR'ı başabaşla değil, "kapısız taban WR" ile kıyasla** (aynı tarih+saat dağılımında 5 dk'da bir giriş; rastgele yürüyüşte taban ≈ başabaş olduğu için sürüklenmeyi ayırır). Wilson CI başabaşı içeriyorsa "kanıtlı" deme.

```bash
python3 .agents/skills/trade-edge-lab/scripts/audit_skipped.py \
  --bars nasdaq_tam_veri_2026-08-29/1m_veri/NAS100_1m_2026-05-19_2026-08-28.csv \
  --gate-log nasdaq_tam_veri_2026-08-29/karar_gunlukleri/gate_skipped_NAS100.jsonl \
  --decision-log nasdaq_tam_veri_2026-08-29/karar_gunlukleri/demo_trades_TUM_NAS100.csv \
  --trades nasdaq_tam_veri_2026-08-29/islemler/NAS100_tum_islemler.csv \
  --out output/trade-edge-lab/ndx-rejected
```

Deliver the report and chart, explain data coverage and limitations, and identify a specific next validation step. Do not change live gates or bot defaults as a side effect of research.
