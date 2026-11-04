# Indicator and analysis families

120 research cards. Names and aliases preserve English, Japanese and Chinese terminology. Linked source matches are navigation aids: matching a name does not establish mathematical equivalence or runtime correctness. A card with no local match has no exact local implementation claimed; use the linked publication directory and report for external sources. All four target markets require independent execution and profitability validation.

## FAM-001 — Ichimoku Kinkō Hyō / 一目均衡表

**Group:** Japanese chart systems  
**Required data:** OHLC

Tenkan and Kijun are midpoints of rolling high/low ranges; Senkou A averages those lines, Senkou B uses a longer range; the cloud is drawn forward and Chikou backward.

**Implementation detail:** Separate calculation time from display offset. A historical Chikou plot is not information available at that plotted date.

**Source implementations:**

- SRC-0129 — TA-Lib/ta-lib / ICHIMOKU: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ICHIMOKU.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ICHIMOKU.c#L1); source_indexed_not_runtime_validated.
- SRC-0406 — xgboosted/pandas-ta-classic / ichimoku: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/ichimoku.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/ichimoku.py#L13); source_indexed_not_runtime_validated.
- SRC-0602 — peerchemist/finta / ICHIMOKU: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1852); source_indexed_not_runtime_validated.
- SRC-0629 — bukosabino/ta / IchimokuIndicator: [local source](vendor/bukosabino__ta/ta/trend.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/trend.py#L340); source_indexed_not_runtime_validated.
- SRC-1081 — DaveSkender/Stock.Indicators / Ichimoku: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/Ichimoku/Ichimoku.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/Ichimoku/Ichimoku.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1357 — QuantConnect/Lean / IchimokuKinkoHyo: [local source](vendor/QuantConnect__Lean/Indicators/IchimokuKinkoHyo.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/IchimokuKinkoHyo.cs#L28); source_indexed_not_runtime_validated.

## FAM-002 — Heikin Ashi / 平均足

**Group:** Japanese chart systems  
**Required data:** OHLC

Synthetic close averages OHLC; synthetic open averages the previous synthetic open and close. This smooths candle appearance.

**Implementation detail:** Synthetic candle prices are not executable broker quotes.

**Source implementations:**

- SRC-1077 — DaveSkender/Stock.Indicators / HeikinAshi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/HeikinAshi/HeikinAshi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/HeikinAshi/HeikinAshi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1205 — anandanand84/technicalindicators / HeikinAshi: [local source](vendor/anandanand84__technicalindicators/src/chart_types/HeikinAshi.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/chart_types/HeikinAshi.ts#L1); source_indexed_not_runtime_validated.
- SRC-1353 — QuantConnect/Lean / HeikinAshi: [local source](vendor/QuantConnect__Lean/Indicators/HeikinAshi.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/HeikinAshi.cs#L29); source_indexed_not_runtime_validated.

## FAM-003 — Renko / 練行足

**Group:** Alternative chart systems  
**Required data:** Ticks or ordered lower-timeframe prices

Adds bricks when price traverses a selected box size; time between bricks is irregular.

**Implementation detail:** OHLC reconstruction can conceal path ambiguity; ATR-sized historical bricks may change with settings.

**Source implementations:**

- SRC-1097 — DaveSkender/Stock.Indicators / Renko: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Renko/Renko.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Renko/Renko.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-004 — Kagi / 鉤足

**Group:** Alternative chart systems  
**Required data:** Ordered prices

Alternates vertical legs after a reversal threshold; prior swing breaks change line state.

**Implementation detail:** Requires ordered price paths; chart-derived fills must use actual prices.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-005 — Point & Figure

**Group:** Alternative chart systems  
**Required data:** Ordered prices

Uses X/O columns for box-sized advances and declines, reversing after a configured box count.

**Implementation detail:** Intrabar high/low ordering affects columns.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-006 — Line Break

**Group:** Alternative chart systems  
**Required data:** Prices

Prints a new line when price exceeds thresholds from the preceding lines; reversals use a configurable line count.

**Implementation detail:** Irregular chart events are not fixed-time candles.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-007 — KDJ / 随机指标

**Group:** Chinese formula systems  
**Required data:** HLC

Normalizes close within a recent high/low range to RSV, smooths into K and D, then forms J = 3K − 2D.

**Implementation detail:** TongDaXin SMA is recursive smoothing, not an ordinary simple moving average; J can exceed 0–100.

**Source implementations:**

- SRC-0133 — TA-Lib/ta-lib / KDJ: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KDJ.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KDJ.c#L1); source_indexed_not_runtime_validated.
- SRC-0359 — xgboosted/pandas-ta-classic / kdj: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/kdj.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/kdj.py#L17); source_indexed_not_runtime_validated.
- SRC-0689 — mpquant/MyTT / KDJ: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L149); source_indexed_not_runtime_validated.

## FAM-008 — BBI / 多空指标

**Group:** Chinese formula systems  
**Required data:** Close

Averages four simple moving averages to form a combined bull/bear baseline; periods differ across implementations.

**Implementation detail:** MyTT defaults use 3/6/12/20; a different script may use 24 for the last period.

**Source implementations:**

- SRC-0697 — mpquant/MyTT / BBI: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L188); source_indexed_not_runtime_validated.

## FAM-009 — BIAS / 乖离率 / Kairi

**Group:** Chinese/Japanese formulas  
**Required data:** Close

Measures percentage displacement from a moving average: 100 × (price − MA)/MA.

**Implementation detail:** Same concept appears under several names; it is not several independent signals.

**Source implementations:**

- SRC-0344 — xgboosted/pandas-ta-classic / bias: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/bias.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/bias.py#L12); source_indexed_not_runtime_validated.
- SRC-0692 — mpquant/MyTT / BIAS: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L163); source_indexed_not_runtime_validated.
- SRC-0823 — everget/tradingview-pinescript-indicators / Disparity Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/disparity_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/disparity_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-0840 — everget/tradingview-pinescript-indicators / Kairi Relative Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/kairi_relative_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/kairi_relative_index.pine#L1); source_indexed_not_runtime_validated.

## FAM-010 — PSY / 心理线

**Group:** Chinese formula systems  
**Required data:** Close

Reports the percentage of up-closing bars in a rolling period; often accompanied by a smoothed signal.

**Implementation detail:** Counts bar direction, not investor survey sentiment.

**Source implementations:**

- SRC-0369 — xgboosted/pandas-ta-classic / psl: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/psl.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/psl.py#L19); source_indexed_not_runtime_validated.
- SRC-0694 — mpquant/MyTT / PSY: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L175); source_indexed_not_runtime_validated.

## FAM-011 — BRAR / 人气意愿指标

**Group:** Chinese formula systems  
**Required data:** OHLC

AR compares high−open to open−low; BR compares movement relative to the previous close, aggregated over a window.

**Implementation detail:** Exact clipping and zero-denominator conventions vary.

**Source implementations:**

- SRC-0346 — xgboosted/pandas-ta-classic / brar: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/brar.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/brar.py#L18); source_indexed_not_runtime_validated.
- SRC-0706 — mpquant/MyTT / BRAR: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L235); source_indexed_not_runtime_validated.

## FAM-012 — CR / 能量指标

**Group:** Chinese formula systems  
**Required data:** HLC

Compares upward and downward movement around the previous bar midpoint; aggregates into a relative strength ratio.

**Implementation detail:** Different platforms may use different reference prices.

**Source implementations:**

- SRC-0703 — mpquant/MyTT / CR: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L221); source_indexed_not_runtime_validated.

## FAM-013 — VR / 成交量比率

**Group:** Chinese formula systems  
**Required data:** Close + volume

Compares volume accumulated on up bars with down-bar volume, allocating unchanged bars according to its formula.

**Implementation detail:** Needs meaningful volume. CFD tick-volume VR has different economic meaning from exchange-volume VR.

**Source implementations:**

- SRC-0702 — mpquant/MyTT / VR: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L217); source_indexed_not_runtime_validated.

## FAM-014 — DFMA / DMA indicator

**Group:** Chinese formula systems  
**Required data:** Close

Subtracts a long moving average from a short one and smooths the difference.

**Implementation detail:** The name DMA also means dynamic moving average elsewhere; resolve the formula before porting.

**Source implementations:**

- SRC-0707 — mpquant/MyTT / DFMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L240); source_indexed_not_runtime_validated.

## FAM-015 — EXPMA

**Group:** Chinese formula systems  
**Required data:** Close

Plots exponential moving averages at multiple lengths to compare trend direction and crossings.

**Implementation detail:** Usually an EMA presentation variant rather than a new mathematical family.

**Source implementations:**

- SRC-0110 — TA-Lib/ta-lib / EMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_EMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_EMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0398 — xgboosted/pandas-ta-classic / ema: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/ema.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/ema.py#L13); source_indexed_not_runtime_validated.
- SRC-0525 — peerchemist/finta / EMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L106); source_indexed_not_runtime_validated.
- SRC-0667 — mpquant/MyTT / EMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L66); source_indexed_not_runtime_validated.
- SRC-0711 — mpquant/MyTT / EXPMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L257); source_indexed_not_runtime_validated.
- SRC-0973 — TulipCharts/tulipindicators / ema: [local source](vendor/TulipCharts__tulipindicators/indicators/ema.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/ema.c#L1); source_indexed_not_runtime_validated.
- SRC-1070 — DaveSkender/Stock.Indicators / Ema: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/Ema/Ema.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/Ema/Ema.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1146 — joshuaulrich/TTR / EMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L169); source_indexed_not_runtime_validated.
- SRC-1220 — anandanand84/technicalindicators / EMA: [local source](vendor/anandanand84__technicalindicators/src/moving_averages/EMA.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/moving_averages/EMA.ts#L1); source_indexed_not_runtime_validated.

## FAM-016 — TAQ

**Group:** Chinese formula systems  
**Required data:** HLC

Builds a highest-high/lowest-low channel and its midpoint over a chosen window.

**Implementation detail:** Close relative to a current-bar channel is not the same as breakout above the previous channel.

**Source implementations:**

- SRC-0699 — mpquant/MyTT / TAQ: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L201); source_indexed_not_runtime_validated.

## FAM-017 — KTN

**Group:** Chinese formula systems  
**Required data:** OHLC

MyTT combines an EMA of typical price with ATR-based envelopes; belongs to the Keltner family.

**Implementation detail:** Match typical-price source and ATR smoothing when comparing outputs.

**Source implementations:**

- SRC-0132 — TA-Lib/ta-lib / KC: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KC.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KC.c#L1); source_indexed_not_runtime_validated.
- SRC-0494 — xgboosted/pandas-ta-classic / kc: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/kc.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/kc.py#L19); source_indexed_not_runtime_validated.
- SRC-0563 — peerchemist/finta / KC: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1013); source_indexed_not_runtime_validated.
- SRC-0700 — mpquant/MyTT / KTN: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L205); source_indexed_not_runtime_validated.

## FAM-018 — XSII / 薛斯通道 II

**Group:** Chinese formula systems  
**Required data:** Close

Combines a smoothed price centre with percentage envelopes and a dynamic channel construction.

**Implementation detail:** Treat this implementation as a defined variant; the name alone does not uniquely specify every platform version.

**Source implementations:**

- SRC-0715 — mpquant/MyTT / XSII: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L276); source_indexed_not_runtime_validated.

## FAM-019 — Chanlun / 缠论 / CZSC

**Group:** Chinese structural systems  
**Required data:** OHLC

Builds inclusion-adjusted bars, fractals, strokes, segments and central zones; signal modules describe structural relationships.

**Implementation detail:** A central zone or stroke can change while forming. Modules are not independent profitable indicators.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-020 — SMA

**Group:** Moving averages  
**Required data:** Price

Arithmetic mean of the last N observations, with equal weights.

**Implementation detail:** Lookback units are bars, not automatically days.

**Source implementations:**

- SRC-0197 — TA-Lib/ta-lib / SMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_SMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_SMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0426 — xgboosted/pandas-ta-classic / sma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/sma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/sma.py#L12); source_indexed_not_runtime_validated.
- SRC-0522 — peerchemist/finta / SMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L58); source_indexed_not_runtime_validated.
- SRC-0668 — mpquant/MyTT / SMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L69); source_indexed_not_runtime_validated.
- SRC-0801 — everget/tradingview-pinescript-indicators / Simple Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/simple_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/simple_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1012 — TulipCharts/tulipindicators / sma: [local source](vendor/TulipCharts__tulipindicators/indicators/sma.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/sma.c#L1); source_indexed_not_runtime_validated.
- SRC-1104 — DaveSkender/Stock.Indicators / Sma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Sma/Sma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Sma/Sma.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1145 — joshuaulrich/TTR / SMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L152); source_indexed_not_runtime_validated.
- SRC-1222 — anandanand84/technicalindicators / SMA: [local source](vendor/anandanand84__technicalindicators/src/moving_averages/SMA.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/moving_averages/SMA.ts#L1); source_indexed_not_runtime_validated.
- SRC-1418 — QuantConnect/Lean / SimpleMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/SimpleMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/SimpleMovingAverage.cs#L21); source_indexed_not_runtime_validated.

## FAM-021 — EMA

**Group:** Moving averages  
**Required data:** Price

Recursively updates the average using α = 2/(N+1); recent observations receive more weight.

**Implementation detail:** Seed choice and warm-up affect cross-library parity.

**Source implementations:**

- SRC-0110 — TA-Lib/ta-lib / EMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_EMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_EMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0398 — xgboosted/pandas-ta-classic / ema: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/ema.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/ema.py#L13); source_indexed_not_runtime_validated.
- SRC-0525 — peerchemist/finta / EMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L106); source_indexed_not_runtime_validated.
- SRC-0667 — mpquant/MyTT / EMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L66); source_indexed_not_runtime_validated.
- SRC-0764 — everget/tradingview-pinescript-indicators / Exponential Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/exponential_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/exponential_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-0973 — TulipCharts/tulipindicators / ema: [local source](vendor/TulipCharts__tulipindicators/indicators/ema.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/ema.c#L1); source_indexed_not_runtime_validated.
- SRC-1070 — DaveSkender/Stock.Indicators / Ema: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/Ema/Ema.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/Ema/Ema.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1146 — joshuaulrich/TTR / EMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L169); source_indexed_not_runtime_validated.
- SRC-1220 — anandanand84/technicalindicators / EMA: [local source](vendor/anandanand84__technicalindicators/src/moving_averages/EMA.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/moving_averages/EMA.ts#L1); source_indexed_not_runtime_validated.
- SRC-1345 — QuantConnect/Lean / ExponentialMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/ExponentialMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ExponentialMovingAverage.cs#L27); source_indexed_not_runtime_validated.

## FAM-022 — Wilder RMA / SMMA

**Group:** Moving averages  
**Required data:** Price

Recursive smoothing with α approximately 1/N after an initial seed.

**Implementation detail:** Chinese SMA(X,N,M) uses α=M/N and is not identical to SMA arithmetic averaging.

**Source implementations:**

- SRC-0182 — TA-Lib/ta-lib / RMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_RMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_RMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0424 — xgboosted/pandas-ta-classic / rma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/rma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/rma.py#L12); source_indexed_not_runtime_validated.
- SRC-0540 — peerchemist/finta / SMMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L424); source_indexed_not_runtime_validated.
- SRC-1107 — DaveSkender/Stock.Indicators / Smma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Smma/Smma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Smma/Smma.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-023 — WMA / LWMA

**Group:** Moving averages  
**Required data:** Price

Weights recent samples linearly more heavily than older samples.

**Implementation detail:** Check weight orientation and initial valid index.

**Source implementations:**

- SRC-0235 — TA-Lib/ta-lib / WMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_WMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_WMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0439 — xgboosted/pandas-ta-classic / wma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/wma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/wma.py#L13); source_indexed_not_runtime_validated.
- SRC-0536 — peerchemist/finta / WMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L334); source_indexed_not_runtime_validated.
- SRC-0669 — mpquant/MyTT / WMA: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L72); source_indexed_not_runtime_validated.
- SRC-0809 — everget/tradingview-pinescript-indicators / Weighted Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/weighted_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/weighted_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1042 — TulipCharts/tulipindicators / wma: [local source](vendor/TulipCharts__tulipindicators/indicators/wma.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/wma.c#L1); source_indexed_not_runtime_validated.
- SRC-1127 — DaveSkender/Stock.Indicators / Wma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Wma/Wma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Wma/Wma.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1148 — joshuaulrich/TTR / WMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L235); source_indexed_not_runtime_validated.
- SRC-1224 — anandanand84/technicalindicators / WMA: [local source](vendor/anandanand84__technicalindicators/src/moving_averages/WMA.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/moving_averages/WMA.ts#L1); source_indexed_not_runtime_validated.

## FAM-024 — DEMA / TEMA

**Group:** Moving averages  
**Required data:** Price

DEMA = 2E1 − E2; TEMA = 3E1 − 3E2 + E3, using successive EMAs.

**Implementation detail:** Lag compensation can overshoot and react more strongly to noise.

**Source implementations:**

- SRC-0103 — TA-Lib/ta-lib / DEMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_DEMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_DEMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0217 — TA-Lib/ta-lib / TEMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_TEMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_TEMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0397 — xgboosted/pandas-ta-classic / dema: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/dema.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/dema.py#L14); source_indexed_not_runtime_validated.
- SRC-0431 — xgboosted/pandas-ta-classic / tema: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/tema.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/tema.py#L14); source_indexed_not_runtime_validated.
- SRC-0526 — peerchemist/finta / DEMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L125); source_indexed_not_runtime_validated.
- SRC-0527 — peerchemist/finta / TEMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L149); source_indexed_not_runtime_validated.
- SRC-0754 — everget/tradingview-pinescript-indicators / Double Exponential Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/double_exponential_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/double_exponential_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-0966 — TulipCharts/tulipindicators / dema: [local source](vendor/TulipCharts__tulipindicators/indicators/dema.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/dema.c#L1); source_indexed_not_runtime_validated.
- SRC-1022 — TulipCharts/tulipindicators / tema: [local source](vendor/TulipCharts__tulipindicators/indicators/tema.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/tema.c#L1); source_indexed_not_runtime_validated.
- SRC-1064 — DaveSkender/Stock.Indicators / Dema: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Dema/Dema.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Dema/Dema.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1116 — DaveSkender/Stock.Indicators / Tema: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Tema/Tema.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Tema/Tema.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1147 — joshuaulrich/TTR / DEMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L199); source_indexed_not_runtime_validated.
- SRC-1342 — QuantConnect/Lean / DoubleExponentialMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/DoubleExponentialMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/DoubleExponentialMovingAverage.cs#L26); source_indexed_not_runtime_validated.
- SRC-1436 — QuantConnect/Lean / TripleExponentialMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/TripleExponentialMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/TripleExponentialMovingAverage.cs#L26); source_indexed_not_runtime_validated.

## FAM-025 — Tillson T3

**Group:** Moving averages  
**Required data:** Price

Combines successive EMA filters with coefficients controlled by a volume-factor parameter.

**Implementation detail:** The volume-factor parameter is a smoothing coefficient, not an observed volume series.

**Source implementations:**

- SRC-0214 — TA-Lib/ta-lib / T3: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_T3.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_T3.c#L1); source_indexed_not_runtime_validated.
- SRC-0430 — xgboosted/pandas-ta-classic / t3: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/t3.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/t3.py#L14); source_indexed_not_runtime_validated.
- SRC-0805 — everget/tradingview-pinescript-indicators / T3 Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/t3_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/t3_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1115 — DaveSkender/Stock.Indicators / T3: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/T3/T3.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/T3/T3.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1428 — QuantConnect/Lean / T3MovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/T3MovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/T3MovingAverage.cs#L26); source_indexed_not_runtime_validated.

## FAM-026 — Hull Moving Average

**Group:** Moving averages  
**Required data:** Price

Combines WMA at full and half length, then smooths the compensated result over approximately √N.

**Implementation detail:** Integer rounding rules can produce platform differences.

**Source implementations:**

- SRC-0121 — TA-Lib/ta-lib / HMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0403 — xgboosted/pandas-ta-classic / hma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/hma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/hma.py#L14); source_indexed_not_runtime_validated.
- SRC-0537 — peerchemist/finta / HMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L357); source_indexed_not_runtime_validated.
- SRC-0773 — everget/tradingview-pinescript-indicators / Hull Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/hull_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/hull_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-0979 — TulipCharts/tulipindicators / hma: [local source](vendor/TulipCharts__tulipindicators/indicators/hma.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/hma.c#L1); source_indexed_not_runtime_validated.
- SRC-1078 — DaveSkender/Stock.Indicators / Hma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/Hma/Hma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/Hma/Hma.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1151 — joshuaulrich/TTR / HMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L382); source_indexed_not_runtime_validated.
- SRC-1355 — QuantConnect/Lean / HullMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/HullMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/HullMovingAverage.cs#L24); source_indexed_not_runtime_validated.

## FAM-027 — ALMA

**Group:** Moving averages  
**Required data:** Price

Applies Gaussian weights with configurable offset and spread across the rolling price window.

**Implementation detail:** Finta's ALMA entry is a placeholder; use an actual implementation from another source.

**Source implementations:**

- SRC-0010 — TA-Lib/ta-lib / ALMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ALMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ALMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0395 — xgboosted/pandas-ta-classic / alma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/alma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/alma.py#L12); source_indexed_not_runtime_validated.
- SRC-0541 — peerchemist/finta / ALMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L438); unimplemented_marker.
- SRC-0748 — everget/tradingview-pinescript-indicators / Arnaud Legoux Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/arnaud_legoux_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/arnaud_legoux_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1047 — DaveSkender/Stock.Indicators / Alma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/Alma/Alma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/Alma/Alma.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1152 — joshuaulrich/TTR / ALMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L401); source_indexed_not_runtime_validated.
- SRC-1249 — QuantConnect/Lean / ArnaudLegouxMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/ArnaudLegouxMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ArnaudLegouxMovingAverage.cs#L29); source_indexed_not_runtime_validated.

## FAM-028 — KAMA

**Group:** Adaptive filters  
**Required data:** Price

Uses an efficiency ratio to adjust smoothing between fast and slow limits.

**Implementation detail:** A trend-adaptive line still requires warm-up and a precisely defined seed.

**Source implementations:**

- SRC-0131 — TA-Lib/ta-lib / KAMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KAMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KAMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0408 — xgboosted/pandas-ta-classic / kama: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/kama.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/kama.py#L32); source_indexed_not_runtime_validated.
- SRC-0534 — peerchemist/finta / KAMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L266); source_indexed_not_runtime_validated.
- SRC-0777 — everget/tradingview-pinescript-indicators / Kaufman Adaptive Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/kaufman_adaptive_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/kaufman_adaptive_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-0980 — TulipCharts/tulipindicators / kama: [local source](vendor/TulipCharts__tulipindicators/indicators/kama.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/kama.c#L1); source_indexed_not_runtime_validated.
- SRC-1082 — DaveSkender/Stock.Indicators / Kama: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Kama/Kama.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Kama/Kama.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1364 — QuantConnect/Lean / KaufmanAdaptiveMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/KaufmanAdaptiveMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/KaufmanAdaptiveMovingAverage.cs#L23); source_indexed_not_runtime_validated.

## FAM-029 — VIDYA

**Group:** Adaptive filters  
**Required data:** Price

Changes EMA weight using a momentum/variability measure such as absolute CMO.

**Implementation detail:** Variants differ. Finta's named VIDYA method raises NotImplementedError.

**Source implementations:**

- SRC-0227 — TA-Lib/ta-lib / VIDYA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_VIDYA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_VIDYA.c#L1); source_indexed_not_runtime_validated.
- SRC-0435 — xgboosted/pandas-ta-classic / vidya: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/vidya.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/vidya.py#L27); source_indexed_not_runtime_validated.
- SRC-0532 — peerchemist/finta / VIDYA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L241); unimplemented_marker.
- SRC-0808 — everget/tradingview-pinescript-indicators / Variable Index Dynamic Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/vidya_variable_index_dynamic_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/vidya_variable_index_dynamic_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1034 — TulipCharts/tulipindicators / vidya: [local source](vendor/TulipCharts__tulipindicators/indicators/vidya.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/vidya.c#L1); source_indexed_not_runtime_validated.

## FAM-030 — FRAMA

**Group:** Adaptive filters  
**Required data:** HLC or selected price

Estimates fractal dimension from subwindow ranges and maps it into an adaptive smoothing coefficient.

**Implementation detail:** Window parity and coefficient bounds matter.

**Source implementations:**

- SRC-0119 — TA-Lib/ta-lib / FRAMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_FRAMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_FRAMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0543 — peerchemist/finta / FRAMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L463); source_indexed_not_runtime_validated.
- SRC-0768 — everget/tradingview-pinescript-indicators / Fractal Adaptive Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/fractal_adaptive_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/fractal_adaptive_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1349 — QuantConnect/Lean / FractalAdaptiveMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/FractalAdaptiveMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/FractalAdaptiveMovingAverage.cs#L25); source_indexed_not_runtime_validated.

## FAM-031 — MAMA / FAMA

**Group:** Adaptive filters  
**Required data:** Price

Uses Hilbert-transform phase behaviour to adapt moving-average speed; FAMA follows MAMA more slowly.

**Implementation detail:** Finta's MAMA is a placeholder; other implementations are present.

**Source implementations:**

- SRC-0148 — TA-Lib/ta-lib / MAMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_MAMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_MAMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0414 — xgboosted/pandas-ta-classic / mama: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/mama.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/mama.py#L248); source_indexed_not_runtime_validated.
- SRC-0542 — peerchemist/finta / MAMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L458); unimplemented_marker.
- SRC-0759 — everget/tradingview-pinescript-indicators / Ehlers MESA Adaptive Moving Averages (MAMA & FAMA): [local source](vendor/everget__tradingview-pinescript-indicators/movings/ehlers_mesa_adaptive_moving_averages.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/ehlers_mesa_adaptive_moving_averages.pine#L1); source_indexed_not_runtime_validated.
- SRC-1087 — DaveSkender/Stock.Indicators / Mama: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Mama/Mama.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Mama/Mama.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1380 — QuantConnect/Lean / MesaAdaptiveMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/MesaAdaptiveMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/MesaAdaptiveMovingAverage.cs#L25); source_indexed_not_runtime_validated.

## FAM-032 — McGinley Dynamic

**Group:** Adaptive filters  
**Required data:** Price

Updates a moving baseline with a denominator dependent on the price-to-baseline ratio.

**Implementation detail:** Numerical handling near zero needs review.

**Source implementations:**

- SRC-0154 — TA-Lib/ta-lib / MCGD: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_MCGD.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_MCGD.c#L1); source_indexed_not_runtime_validated.
- SRC-0416 — xgboosted/pandas-ta-classic / mcgd: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/mcgd.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/mcgd.py#L28); source_indexed_not_runtime_validated.
- SRC-0782 — everget/tradingview-pinescript-indicators / McGinley Dynamic: [local source](vendor/everget__tradingview-pinescript-indicators/movings/mcginley_dynamic.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/mcginley_dynamic.pine#L1); source_indexed_not_runtime_validated.
- SRC-1378 — QuantConnect/Lean / McGinleyDynamic: [local source](vendor/QuantConnect__Lean/Indicators/McGinleyDynamic.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/McGinleyDynamic.cs#L27); source_indexed_not_runtime_validated.

## FAM-033 — ZLEMA

**Group:** Adaptive filters  
**Required data:** Price

Adds a lag compensation term to price before exponential smoothing.

**Implementation detail:** Zero lag in a name does not mean future price is known.

**Source implementations:**

- SRC-0237 — TA-Lib/ta-lib / ZLEMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ZLEMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ZLEMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0440 — xgboosted/pandas-ta-classic / zlma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/zlma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/zlma.py#L40); source_indexed_not_runtime_validated.
- SRC-0535 — peerchemist/finta / ZLEMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L308); source_indexed_not_runtime_validated.
- SRC-0811 — everget/tradingview-pinescript-indicators / Zero Lag Exponential Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/zero_lag_exponential_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/zero_lag_exponential_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-1043 — TulipCharts/tulipindicators / zlema: [local source](vendor/TulipCharts__tulipindicators/indicators/zlema.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/zlema.c#L1); source_indexed_not_runtime_validated.
- SRC-1150 — joshuaulrich/TTR / ZLEMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L333); source_indexed_not_runtime_validated.
- SRC-1455 — QuantConnect/Lean / ZeroLagExponentialMovingAverage: [local source](vendor/QuantConnect__Lean/Indicators/ZeroLagExponentialMovingAverage.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ZeroLagExponentialMovingAverage.cs#L25); source_indexed_not_runtime_validated.

## FAM-034 — Jurik Moving Average / RSX variants

**Group:** Adaptive filters  
**Required data:** Price

Public scripts implement smooth adaptive lines or RSI-like oscillators carrying Jurik-related names.

**Implementation detail:** A public approximation is not proof of identity with proprietary Jurik software.

**Source implementations:**

- SRC-0377 — xgboosted/pandas-ta-classic / rsx: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/rsx.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/rsx.py#L69); source_indexed_not_runtime_validated.
- SRC-0776 — everget/tradingview-pinescript-indicators / Jurik Moving Average: [local source](vendor/everget__tradingview-pinescript-indicators/movings/jurik_moving_average.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/jurik_moving_average.pine#L1); source_indexed_not_runtime_validated.
- SRC-0839 — everget/tradingview-pinescript-indicators / Jurik RSX: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/jurik_rsx.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/jurik_rsx.pine#L1); source_indexed_not_runtime_validated.
- SRC-0864 — everget/tradingview-pinescript-indicators / Jurik RSX: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/rsx.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/rsx.pine#L1); source_indexed_not_runtime_validated.

## FAM-035 — Ehlers Super Smoother

**Group:** Digital signal processing  
**Required data:** Price

A recursive low-pass filter uses period-derived coefficients and previous filter states to attenuate high-frequency variation.

**Implementation detail:** Initialization and coefficient conventions affect outputs.

**Source implementations:**

- SRC-0427 — xgboosted/pandas-ta-classic / ssf: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/ssf.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/ssf.py#L28); source_indexed_not_runtime_validated.
- SRC-0762 — everget/tradingview-pinescript-indicators / Ehlers Super Smoother Filter: [local source](vendor/everget__tradingview-pinescript-indicators/movings/ehlers_super_smoother_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/ehlers_super_smoother_filter.pine#L1); source_indexed_not_runtime_validated.

## FAM-036 — Ehlers Ultimate Smoother

**Group:** Digital signal processing  
**Required data:** Price

A low-lag smoothing construction combines high-pass/all-pass relationships to preserve lower-frequency components.

**Implementation detail:** Primary publication and official PineCodersTASC page are linked; no independently audited local implementation claimed.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-037 — Ehlers Roofing Filter

**Group:** Digital signal processing  
**Required data:** Price

Combines high-pass detrending with low-pass smoothing to retain a selected cycle band.

**Implementation detail:** Filter period is not a forecast horizon.

**Source implementations:**

- SRC-0829 — everget/tradingview-pinescript-indicators / Ehlers Roofing Filter: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/ehlers_roofing_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/ehlers_roofing_filter.pine#L1); source_indexed_not_runtime_validated.

## FAM-038 — Ehlers Cyber Cycle

**Group:** Digital signal processing  
**Required data:** Price

Smooths and detrends price with recursive terms to isolate oscillatory components.

**Implementation detail:** Turning points can change on the current open bar.

**Source implementations:**

- SRC-0826 — everget/tradingview-pinescript-indicators / Ehlers Cyber Cycle: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/ehlers_cyber_cycle.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/ehlers_cyber_cycle.pine#L1); source_indexed_not_runtime_validated.

## FAM-039 — Laguerre Filter / Laguerre RSI

**Group:** Digital signal processing  
**Required data:** Price

Uses a sequence of Laguerre states; directional state changes can be normalized into an RSI-like output.

**Implementation detail:** Gamma governs the responsiveness and smoothness trade-off.

**Source implementations:**

- SRC-0778 — everget/tradingview-pinescript-indicators / Laguerre Filter: [local source](vendor/everget__tradingview-pinescript-indicators/movings/laguerre_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/laguerre_filter.pine#L1); source_indexed_not_runtime_validated.
- SRC-0841 — everget/tradingview-pinescript-indicators / Laguerre RSI: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/laguerre_rsi.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/laguerre_rsi.pine#L1); source_indexed_not_runtime_validated.

## FAM-040 — Fisher / Inverse Fisher

**Group:** Digital signal processing  
**Required data:** Normalized series

Transforms a bounded input to emphasize extremes; inverse Fisher compresses an oscillator into bounded outputs.

**Implementation detail:** Clipping near ±1 is essential for finite Fisher values.

**Source implementations:**

- SRC-0115 — TA-Lib/ta-lib / FISHER: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_FISHER.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_FISHER.c#L1); source_indexed_not_runtime_validated.
- SRC-0356 — xgboosted/pandas-ta-classic / fisher: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/fisher.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/fisher.py#L36); source_indexed_not_runtime_validated.
- SRC-0552 — peerchemist/finta / IFT_RSI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L714); source_indexed_not_runtime_validated.
- SRC-0976 — TulipCharts/tulipindicators / fisher: [local source](vendor/TulipCharts__tulipindicators/indicators/fisher.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/fisher.c#L1); source_indexed_not_runtime_validated.
- SRC-1073 — DaveSkender/Stock.Indicators / FisherTransform: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/FisherTransform/FisherTransform.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/FisherTransform/FisherTransform.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1347 — QuantConnect/Lean / FisherTransform: [local source](vendor/QuantConnect__Lean/Indicators/FisherTransform.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/FisherTransform.cs#L39); source_indexed_not_runtime_validated.

## FAM-041 — Hilbert dominant cycle / sine / phasor

**Group:** Digital signal processing  
**Required data:** Price

Estimates phase and cycle properties using Hilbert-transform approximations.

**Implementation detail:** Unstable initial periods and phase wrap require explicit handling.

**Source implementations:**

- SRC-0122 — TA-Lib/ta-lib / HT_DCPERIOD: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HT_DCPERIOD.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HT_DCPERIOD.c#L1); source_indexed_not_runtime_validated.
- SRC-0123 — TA-Lib/ta-lib / HT_DCPHASE: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HT_DCPHASE.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HT_DCPHASE.c#L1); source_indexed_not_runtime_validated.
- SRC-0124 — TA-Lib/ta-lib / HT_PHASOR: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HT_PHASOR.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HT_PHASOR.c#L1); source_indexed_not_runtime_validated.
- SRC-0125 — TA-Lib/ta-lib / HT_SINE: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HT_SINE.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HT_SINE.c#L1); source_indexed_not_runtime_validated.
- SRC-0127 — TA-Lib/ta-lib / HT_TRENDMODE: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_HT_TRENDMODE.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_HT_TRENDMODE.c#L1); source_indexed_not_runtime_validated.
- SRC-0305 — xgboosted/pandas-ta-classic / ht_dcperiod: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/cycles/ht_dcperiod.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/cycles/ht_dcperiod.py#L14); source_indexed_not_runtime_validated.
- SRC-0306 — xgboosted/pandas-ta-classic / ht_dcphase: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/cycles/ht_dcphase.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/cycles/ht_dcphase.py#L14); source_indexed_not_runtime_validated.
- SRC-0307 — xgboosted/pandas-ta-classic / ht_phasor: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/cycles/ht_phasor.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/cycles/ht_phasor.py#L14); source_indexed_not_runtime_validated.
- SRC-0308 — xgboosted/pandas-ta-classic / ht_sine: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/cycles/ht_sine.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/cycles/ht_sine.py#L14); source_indexed_not_runtime_validated.
- SRC-0309 — xgboosted/pandas-ta-classic / ht_trendmode: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/cycles/ht_trendmode.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/cycles/ht_trendmode.py#L14); source_indexed_not_runtime_validated.

## FAM-042 — Kalman Filter

**Group:** Statistical filters  
**Required data:** Price + model variances

Predicts a latent price state and uncertainty, then updates using an uncertainty-dependent gain when a new price arrives.

**Implementation detail:** Q/R assumptions specify the model; a filter is causal, a backward smoother uses future observations.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-043 — Moving Median / Hampel Filter

**Group:** Robust filters  
**Required data:** Price

Median filtering reduces sensitivity to isolated outliers; Hampel logic identifies extreme deviations around a local median.

**Implementation detail:** A centred window is noncausal unless results are delayed.

**Source implementations:**

- SRC-0770 — everget/tradingview-pinescript-indicators / Hampel Filter: [local source](vendor/everget__tradingview-pinescript-indicators/movings/hampel_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/hampel_filter.pine#L1); source_indexed_not_runtime_validated.
- SRC-0787 — everget/tradingview-pinescript-indicators / Moving Median: [local source](vendor/everget__tradingview-pinescript-indicators/movings/moving_median.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/moving_median.pine#L1); source_indexed_not_runtime_validated.

## FAM-044 — Gaussian / Butterworth filters

**Group:** Digital signal processing  
**Required data:** Price

Low-pass filtering suppresses rapid fluctuations using Gaussian weights or recursive Butterworth coefficients.

**Implementation detail:** Different implementations can be trailing or centred.

**Source implementations:**

- SRC-0750 — everget/tradingview-pinescript-indicators / Butterworth Filter: [local source](vendor/everget__tradingview-pinescript-indicators/movings/butterworth_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/butterworth_filter.pine#L1); source_indexed_not_runtime_validated.
- SRC-0769 — everget/tradingview-pinescript-indicators / Gaussian Filter: [local source](vendor/everget__tradingview-pinescript-indicators/movings/gaussian_filter.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/movings/gaussian_filter.pine#L1); source_indexed_not_runtime_validated.

## FAM-045 — RSI

**Group:** Momentum  
**Required data:** Close

Normalizes smoothed average gains versus losses into a 0–100 oscillator.

**Implementation detail:** Overbought can persist in a trend; default seed conventions differ.

**Source implementations:**

- SRC-0188 — TA-Lib/ta-lib / RSI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_RSI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_RSI.c#L1); source_indexed_not_runtime_validated.
- SRC-0376 — xgboosted/pandas-ta-classic / rsi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/rsi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/rsi.py#L14); source_indexed_not_runtime_validated.
- SRC-0551 — peerchemist/finta / RSI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L686); source_indexed_not_runtime_validated.
- SRC-0690 — mpquant/MyTT / RSI: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L154); source_indexed_not_runtime_validated.
- SRC-0863 — everget/tradingview-pinescript-indicators / Relative Strength Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/rsi_relative_strength_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/rsi_relative_strength_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-1009 — TulipCharts/tulipindicators / rsi: [local source](vendor/TulipCharts__tulipindicators/indicators/rsi.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/rsi.c#L1); source_indexed_not_runtime_validated.
- SRC-1102 — DaveSkender/Stock.Indicators / Rsi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Rsi/Rsi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Rsi/Rsi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1154 — joshuaulrich/TTR / RSI: [local source](vendor/joshuaulrich__TTR/R/RSI.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/RSI.R#L81); source_indexed_not_runtime_validated.
- SRC-1228 — anandanand84/technicalindicators / RSI: [local source](vendor/anandanand84__technicalindicators/src/oscillators/RSI.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/oscillators/RSI.ts#L1); source_indexed_not_runtime_validated.
- SRC-1410 — QuantConnect/Lean / RelativeStrengthIndex: [local source](vendor/QuantConnect__Lean/Indicators/RelativeStrengthIndex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/RelativeStrengthIndex.cs#L24); source_indexed_not_runtime_validated.

## FAM-046 — Stochastic

**Group:** Momentum  
**Required data:** HLC

Locates close within the rolling high-low range; smooths %K into %D.

**Implementation detail:** Specify fast/slow smoothing and zero-range handling.

**Source implementations:**

- SRC-0203 — TA-Lib/ta-lib / STOCH: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_STOCH.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_STOCH.c#L1); source_indexed_not_runtime_validated.
- SRC-0385 — xgboosted/pandas-ta-classic / stoch: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/stoch.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/stoch.py#L18); source_indexed_not_runtime_validated.
- SRC-0569 — peerchemist/finta / STOCH: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1198); source_indexed_not_runtime_validated.
- SRC-0869 — everget/tradingview-pinescript-indicators / Stochastic: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/stochastic.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/stochastic.pine#L1); source_indexed_not_runtime_validated.
- SRC-1016 — TulipCharts/tulipindicators / stoch: [local source](vendor/TulipCharts__tulipindicators/indicators/stoch.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/stoch.c#L1); source_indexed_not_runtime_validated.
- SRC-1112 — DaveSkender/Stock.Indicators / Stoch: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Stoch/Stoch.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Stoch/Stoch.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1191 — joshuaulrich/TTR / stoch: [local source](vendor/joshuaulrich__TTR/R/stochastics.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/stochastics.R#L128); source_indexed_not_runtime_validated.
- SRC-1216 — anandanand84/technicalindicators / Stochastic: [local source](vendor/anandanand84__technicalindicators/src/momentum/Stochastic.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/momentum/Stochastic.ts#L1); source_indexed_not_runtime_validated.
- SRC-1423 — QuantConnect/Lean / Stochastic: [local source](vendor/QuantConnect__Lean/Indicators/Stochastic.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Stochastic.cs#L27); source_indexed_not_runtime_validated.

## FAM-047 — Stochastic RSI

**Group:** Momentum  
**Required data:** Close

Applies the stochastic range normalization to RSI values rather than raw prices.

**Implementation detail:** Two indicator layers increase sensitivity and warm-up requirements.

**Source implementations:**

- SRC-0205 — TA-Lib/ta-lib / STOCHRSI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_STOCHRSI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_STOCHRSI.c#L1); source_indexed_not_runtime_validated.
- SRC-0387 — xgboosted/pandas-ta-classic / stochrsi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/stochrsi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/stochrsi.py#L49); source_indexed_not_runtime_validated.
- SRC-0571 — peerchemist/finta / STOCHRSI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1228); source_indexed_not_runtime_validated.
- SRC-1017 — TulipCharts/tulipindicators / stochrsi: [local source](vendor/TulipCharts__tulipindicators/indicators/stochrsi.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/stochrsi.c#L1); source_indexed_not_runtime_validated.
- SRC-1113 — DaveSkender/Stock.Indicators / StochRsi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/StochRsi/StochRsi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/StochRsi/StochRsi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1217 — anandanand84/technicalindicators / StochasticRSI: [local source](vendor/anandanand84__technicalindicators/src/momentum/StochasticRSI.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/momentum/StochasticRSI.ts#L1); source_indexed_not_runtime_validated.

## FAM-048 — Stochastic Momentum Index

**Group:** Momentum  
**Required data:** HLC

Double-smooths close displacement from the range midpoint and normalizes by a smoothed half-range.

**Implementation detail:** Distinct from SMI Ergodic and ordinary stochastic.

**Source implementations:**

- SRC-0198 — TA-Lib/ta-lib / SMI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_SMI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_SMI.c#L1); source_indexed_not_runtime_validated.
- SRC-0381 — xgboosted/pandas-ta-classic / smi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/smi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/smi.py#L13); source_indexed_not_runtime_validated.
- SRC-0871 — everget/tradingview-pinescript-indicators / Stochastic Momentum Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/stochastic_momentum_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/stochastic_momentum_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-1106 — DaveSkender/Stock.Indicators / Smi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Smi/Smi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Smi/Smi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1192 — joshuaulrich/TTR / SMI: [local source](vendor/joshuaulrich__TTR/R/stochastics.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/stochastics.R#L222); source_indexed_not_runtime_validated.

## FAM-049 — Connors RSI

**Group:** Momentum  
**Required data:** Close

Averages price RSI, RSI of the signed streak length, and the percentile rank of a one-bar return.

**Implementation detail:** Percent-rank conventions and tie handling vary.

**Source implementations:**

- SRC-0099 — TA-Lib/ta-lib / CRSI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CRSI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CRSI.c#L1); source_indexed_not_runtime_validated.
- SRC-1062 — DaveSkender/Stock.Indicators / ConnorsRsi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/ConnorsRsi/ConnorsRsi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/ConnorsRsi/ConnorsRsi.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-050 — QQE / QQE MOD

**Group:** Momentum  
**Required data:** Close

Smooths RSI and builds adaptive trailing bands from RSI changes; QQE MOD combines two QQE states.

**Implementation detail:** ATR-like smoothing operates on RSI changes, not automatically on price ranges.

**Source implementations:**

- SRC-0371 — xgboosted/pandas-ta-classic / qqe: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/qqe.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/qqe.py#L71); source_indexed_not_runtime_validated.

## FAM-051 — WaveTrend

**Group:** Momentum  
**Required data:** HLC or typical price

EMA-centres price, normalizes displacement by smoothed absolute deviation, then smooths the normalized series and a signal line.

**Implementation detail:** Multiple scripts use different smoothing and threshold settings.

**Source implementations:**

- SRC-0600 — peerchemist/finta / WTO: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1805); source_indexed_not_runtime_validated.

## FAM-052 — MACD / PPO / APO

**Group:** Momentum  
**Required data:** Price

Compares fast and slow averages; MACD/APO show absolute differences, PPO divides by the slow average.

**Implementation detail:** These are related transformations, not independent evidence votes.

**Source implementations:**

- SRC-0012 — TA-Lib/ta-lib / APO: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_APO.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_APO.c#L1); source_indexed_not_runtime_validated.
- SRC-0145 — TA-Lib/ta-lib / MACD: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_MACD.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_MACD.c#L1); source_indexed_not_runtime_validated.
- SRC-0176 — TA-Lib/ta-lib / PPO: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_PPO.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_PPO.c#L1); source_indexed_not_runtime_validated.
- SRC-0343 — xgboosted/pandas-ta-classic / apo: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/apo.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/apo.py#L19); source_indexed_not_runtime_validated.
- SRC-0362 — xgboosted/pandas-ta-classic / macd: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/macd.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/macd.py#L56); source_indexed_not_runtime_validated.
- SRC-0368 — xgboosted/pandas-ta-classic / ppo: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/ppo.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/ppo.py#L48); source_indexed_not_runtime_validated.
- SRC-0544 — peerchemist/finta / MACD: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L502); source_indexed_not_runtime_validated.
- SRC-0545 — peerchemist/finta / PPO: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L541); source_indexed_not_runtime_validated.
- SRC-0688 — mpquant/MyTT / MACD: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L144); source_indexed_not_runtime_validated.
- SRC-0948 — TulipCharts/tulipindicators / apo: [local source](vendor/TulipCharts__tulipindicators/indicators/apo.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/apo.c#L1); source_indexed_not_runtime_validated.
- SRC-0988 — TulipCharts/tulipindicators / macd: [local source](vendor/TulipCharts__tulipindicators/indicators/macd.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/macd.c#L1); source_indexed_not_runtime_validated.
- SRC-1002 — TulipCharts/tulipindicators / ppo: [local source](vendor/TulipCharts__tulipindicators/indicators/ppo.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/ppo.c#L1); source_indexed_not_runtime_validated.
- SRC-1086 — DaveSkender/Stock.Indicators / Macd: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Macd/Macd.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Macd/Macd.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1143 — joshuaulrich/TTR / MACD: [local source](vendor/joshuaulrich__TTR/R/MACD.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MACD.R#L85); source_indexed_not_runtime_validated.
- SRC-1221 — anandanand84/technicalindicators / MACD: [local source](vendor/anandanand84__technicalindicators/src/moving_averages/MACD.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/moving_averages/MACD.ts#L1); source_indexed_not_runtime_validated.

## FAM-053 — ROC / Momentum

**Group:** Momentum  
**Required data:** Price

ROC reports percentage change from N bars ago; momentum usually reports the absolute difference.

**Implementation detail:** Compare normalized rather than raw point thresholds across the four markets.

**Source implementations:**

- SRC-0166 — TA-Lib/ta-lib / MOM: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_MOM.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_MOM.c#L1); source_indexed_not_runtime_validated.
- SRC-0183 — TA-Lib/ta-lib / ROC: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ROC.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ROC.c#L1); source_indexed_not_runtime_validated.
- SRC-0365 — xgboosted/pandas-ta-classic / mom: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/mom.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/mom.py#L12); source_indexed_not_runtime_validated.
- SRC-0372 — xgboosted/pandas-ta-classic / roc: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/roc.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/roc.py#L14); source_indexed_not_runtime_validated.
- SRC-0548 — peerchemist/finta / MOM: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L646); source_indexed_not_runtime_validated.
- SRC-0549 — peerchemist/finta / ROC: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L654); source_indexed_not_runtime_validated.
- SRC-0614 — bukosabino/ta / RSIIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L14); source_indexed_not_runtime_validated.
- SRC-0615 — bukosabino/ta / TSIIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L63); source_indexed_not_runtime_validated.
- SRC-0616 — bukosabino/ta / KAMAIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L282); source_indexed_not_runtime_validated.
- SRC-0617 — bukosabino/ta / ROCIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L362); source_indexed_not_runtime_validated.
- SRC-0618 — bukosabino/ta / AwesomeOscillatorIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L408); source_indexed_not_runtime_validated.
- SRC-0619 — bukosabino/ta / WilliamsRIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L476); source_indexed_not_runtime_validated.
- SRC-0620 — bukosabino/ta / StochRSIIndicator: [local source](vendor/bukosabino__ta/ta/momentum.py) · [pinned upstream](https://github.com/bukosabino/ta/blob/a890410710a6e483c9ba08da7f3dd5089e4b9dff/ta/momentum.py#L549); source_indexed_not_runtime_validated.
- SRC-0710 — mpquant/MyTT / ROC: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L253); source_indexed_not_runtime_validated.
- SRC-0893 — everget/tradingview-pinescript-indicators / Momentum: [local source](vendor/everget__tradingview-pinescript-indicators/research/momentum.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/research/momentum.pine#L1); source_indexed_not_runtime_validated.
- SRC-0996 — TulipCharts/tulipindicators / mom: [local source](vendor/TulipCharts__tulipindicators/indicators/mom.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/mom.c#L1); source_indexed_not_runtime_validated.
- SRC-1006 — TulipCharts/tulipindicators / roc: [local source](vendor/TulipCharts__tulipindicators/indicators/roc.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/roc.c#L1); source_indexed_not_runtime_validated.
- SRC-1099 — DaveSkender/Stock.Indicators / Roc: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Roc/Roc.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Roc/Roc.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1172 — joshuaulrich/TTR / ROC: [local source](vendor/joshuaulrich__TTR/R/changes.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/changes.R#L45); source_indexed_not_runtime_validated.
- SRC-1173 — joshuaulrich/TTR / momentum: [local source](vendor/joshuaulrich__TTR/R/changes.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/changes.R#L83); source_indexed_not_runtime_validated.
- SRC-1215 — anandanand84/technicalindicators / ROC: [local source](vendor/anandanand84__technicalindicators/src/momentum/ROC.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/momentum/ROC.ts#L1); source_indexed_not_runtime_validated.
- SRC-1384 — QuantConnect/Lean / Momentum: [local source](vendor/QuantConnect__Lean/Indicators/Momentum.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Momentum.cs#L22); source_indexed_not_runtime_validated.
- SRC-1385 — QuantConnect/Lean / MomentumPercent: [local source](vendor/QuantConnect__Lean/Indicators/MomentumPercent.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/MomentumPercent.cs#L24); source_indexed_not_runtime_validated.

## FAM-054 — CCI

**Group:** Momentum  
**Required data:** HLC

Divides typical-price displacement from its mean by a scaled mean absolute deviation.

**Implementation detail:** The standard deviation is not the denominator of classical CCI.

**Source implementations:**

- SRC-0025 — TA-Lib/ta-lib / CCI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CCI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CCI.c#L1); source_indexed_not_runtime_validated.
- SRC-0347 — xgboosted/pandas-ta-classic / cci: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/cci.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/cci.py#L15); source_indexed_not_runtime_validated.
- SRC-0592 — peerchemist/finta / CCI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1636); source_indexed_not_runtime_validated.
- SRC-0695 — mpquant/MyTT / CCI: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L180); source_indexed_not_runtime_validated.
- SRC-0816 — everget/tradingview-pinescript-indicators / Commodity Channel Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/cci_commodity_channel_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/cci_commodity_channel_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-0957 — TulipCharts/tulipindicators / cci: [local source](vendor/TulipCharts__tulipindicators/indicators/cci.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/cci.c#L1); source_indexed_not_runtime_validated.
- SRC-1056 — DaveSkender/Stock.Indicators / Cci: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Cci/Cci.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Cci/Cci.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1132 — joshuaulrich/TTR / CCI: [local source](vendor/joshuaulrich__TTR/R/CCI.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/CCI.R#L62); source_indexed_not_runtime_validated.
- SRC-1227 — anandanand84/technicalindicators / CCI: [local source](vendor/anandanand84__technicalindicators/src/oscillators/CCI.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/oscillators/CCI.ts#L1); source_indexed_not_runtime_validated.
- SRC-1329 — QuantConnect/Lean / CommodityChannelIndex: [local source](vendor/QuantConnect__Lean/Indicators/CommodityChannelIndex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/CommodityChannelIndex.cs#L32); source_indexed_not_runtime_validated.

## FAM-055 — CMO

**Group:** Momentum  
**Required data:** Close

Normalizes the difference between summed gains and losses by their total.

**Implementation detail:** Smoothing differs from RSI despite shared input changes.

**Source implementations:**

- SRC-0093 — TA-Lib/ta-lib / CMO: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CMO.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CMO.c#L1); source_indexed_not_runtime_validated.
- SRC-0350 — xgboosted/pandas-ta-classic / cmo: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/cmo.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/cmo.py#L19); source_indexed_not_runtime_validated.
- SRC-0596 — peerchemist/finta / CMO: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1716); source_indexed_not_runtime_validated.
- SRC-0818 — everget/tradingview-pinescript-indicators / Chande Momentum Oscillator: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/chande_momentum_oscillator.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/chande_momentum_oscillator.pine#L1); source_indexed_not_runtime_validated.
- SRC-0959 — TulipCharts/tulipindicators / cmo: [local source](vendor/TulipCharts__tulipindicators/indicators/cmo.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/cmo.c#L1); source_indexed_not_runtime_validated.
- SRC-1061 — DaveSkender/Stock.Indicators / Cmo: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Cmo/Cmo.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Cmo/Cmo.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1135 — joshuaulrich/TTR / CMO: [local source](vendor/joshuaulrich__TTR/R/CMO.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/CMO.R#L50); source_indexed_not_runtime_validated.
- SRC-1327 — QuantConnect/Lean / ChandeMomentumOscillator: [local source](vendor/QuantConnect__Lean/Indicators/ChandeMomentumOscillator.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ChandeMomentumOscillator.cs#L25); source_indexed_not_runtime_validated.

## FAM-056 — TSI / SMI Ergodic

**Group:** Momentum  
**Required data:** Close

Normalizes double-smoothed price changes by double-smoothed absolute changes; a signal EMA can be added.

**Implementation detail:** Do not confuse True Strength Index with Trend Strength Index.

**Source implementations:**

- SRC-0222 — TA-Lib/ta-lib / TSI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_TSI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_TSI.c#L1); source_indexed_not_runtime_validated.
- SRC-0391 — xgboosted/pandas-ta-classic / tsi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/tsi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/tsi.py#L19); source_indexed_not_runtime_validated.
- SRC-0579 — peerchemist/finta / TSI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1363); source_indexed_not_runtime_validated.
- SRC-0881 — everget/tradingview-pinescript-indicators / True Strength Index: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/tsi_true_strength_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/tsi_true_strength_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-1119 — DaveSkender/Stock.Indicators / Tsi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Tsi/Tsi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Tsi/Tsi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1439 — QuantConnect/Lean / TrueStrengthIndex: [local source](vendor/QuantConnect__Lean/Indicators/TrueStrengthIndex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/TrueStrengthIndex.cs#L31); source_indexed_not_runtime_validated.

## FAM-057 — Schaff Trend Cycle

**Group:** Momentum  
**Required data:** Close

Combines MACD with stochastic-style cycle normalization and smoothing.

**Implementation detail:** Variants differ in recursive smoothing and lookbacks.

**Source implementations:**

- SRC-0201 — TA-Lib/ta-lib / STC: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_STC.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_STC.c#L1); source_indexed_not_runtime_validated.
- SRC-0384 — xgboosted/pandas-ta-classic / stc: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/stc.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/stc.py#L100); source_indexed_not_runtime_validated.
- SRC-0609 — peerchemist/finta / STC: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L2124); source_indexed_not_runtime_validated.
- SRC-0867 — everget/tradingview-pinescript-indicators / Schaff Trend Cycle: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/stc_schaff_trend_cycle.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/stc_schaff_trend_cycle.pine#L1); source_indexed_not_runtime_validated.
- SRC-1109 — DaveSkender/Stock.Indicators / Stc: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/Stc/Stc.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/Stc/Stc.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-058 — Coppock / KST / Special K

**Group:** Momentum  
**Required data:** Close

Combines and smooths rates of change over several horizons to represent longer and shorter momentum cycles.

**Implementation detail:** Closely related families should not be counted as independent confirmations.

**Source implementations:**

- SRC-0134 — TA-Lib/ta-lib / KST: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KST.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KST.c#L1); source_indexed_not_runtime_validated.
- SRC-0360 — xgboosted/pandas-ta-classic / kst: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/kst.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/kst.py#L18); source_indexed_not_runtime_validated.
- SRC-0578 — peerchemist/finta / KST: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1345); source_indexed_not_runtime_validated.
- SRC-0819 — everget/tradingview-pinescript-indicators / Coppock Curve: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/coppock_curve.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/coppock_curve.pine#L1); source_indexed_not_runtime_validated.
- SRC-0851 — everget/tradingview-pinescript-indicators / Pring Special K: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/pring_special_k.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/pring_special_k.pine#L1); source_indexed_not_runtime_validated.
- SRC-1142 — joshuaulrich/TTR / KST: [local source](vendor/joshuaulrich__TTR/R/KST.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/KST.R#L72); source_indexed_not_runtime_validated.
- SRC-1213 — anandanand84/technicalindicators / KST: [local source](vendor/anandanand84__technicalindicators/src/momentum/KST.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/momentum/KST.ts#L1); source_indexed_not_runtime_validated.
- SRC-1333 — QuantConnect/Lean / CoppockCurve: [local source](vendor/QuantConnect__Lean/Indicators/CoppockCurve.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/CoppockCurve.cs#L25); source_indexed_not_runtime_validated.

## FAM-059 — Ultimate Oscillator

**Group:** Momentum  
**Required data:** HLC

Aggregates buying pressure relative to true range over three windows with fixed relative weights.

**Implementation detail:** Check preceding-close definition and zero denominators.

**Source implementations:**

- SRC-0392 — xgboosted/pandas-ta-classic / uo: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/uo.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/uo.py#L63); source_indexed_not_runtime_validated.
- SRC-0573 — peerchemist/finta / UO: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1263); source_indexed_not_runtime_validated.
- SRC-1193 — joshuaulrich/TTR / ultimateOscillator: [local source](vendor/joshuaulrich__TTR/R/ultimateOscillator.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/ultimateOscillator.R#L41); source_indexed_not_runtime_validated.
- SRC-1440 — QuantConnect/Lean / UltimateOscillator: [local source](vendor/QuantConnect__Lean/Indicators/UltimateOscillator.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/UltimateOscillator.cs#L26); source_indexed_not_runtime_validated.

## FAM-060 — DeMarker

**Group:** Momentum  
**Required data:** HL

Compares positive high changes with positive low decreases and normalizes their moving totals.

**Implementation detail:** A bounded oscillator still does not by itself define an executable strategy.

**Source implementations:**

- SRC-0820 — everget/tradingview-pinescript-indicators / DeMarker: [local source](vendor/everget__tradingview-pinescript-indicators/oscillators/demarker.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/oscillators/demarker.pine#L1); source_indexed_not_runtime_validated.
- SRC-1336 — QuantConnect/Lean / DeMarkerIndicator: [local source](vendor/QuantConnect__Lean/Indicators/DeMarkerIndicator.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/DeMarkerIndicator.cs#L36); source_indexed_not_runtime_validated.

## FAM-061 — ADX / DMI

**Group:** Trend strength  
**Required data:** HLC

Derives +DI and −DI from directional movement relative to true range, then smooths their normalized difference into ADX.

**Implementation detail:** ADX strength is separate from +DI/−DI direction.

**Source implementations:**

- SRC-0008 — TA-Lib/ta-lib / ADX: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ADX.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ADX.c#L1); source_indexed_not_runtime_validated.
- SRC-0458 — xgboosted/pandas-ta-classic / adx: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/adx.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/adx.py#L23); source_indexed_not_runtime_validated.
- SRC-0565 — peerchemist/finta / DMI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1059); source_indexed_not_runtime_validated.
- SRC-0566 — peerchemist/finta / ADX: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1108); source_indexed_not_runtime_validated.
- SRC-0698 — mpquant/MyTT / DMI: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L191); source_indexed_not_runtime_validated.
- SRC-0945 — TulipCharts/tulipindicators / adx: [local source](vendor/TulipCharts__tulipindicators/indicators/adx.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/adx.c#L1); source_indexed_not_runtime_validated.
- SRC-1045 — DaveSkender/Stock.Indicators / Adx: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/Adx/Adx.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/Adx/Adx.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1129 — joshuaulrich/TTR / ADX: [local source](vendor/joshuaulrich__TTR/R/ADX.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/ADX.R#L67); source_indexed_not_runtime_validated.
- SRC-1207 — anandanand84/technicalindicators / ADX: [local source](vendor/anandanand84__technicalindicators/src/directionalmovement/ADX.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/directionalmovement/ADX.ts#L1); source_indexed_not_runtime_validated.
- SRC-1253 — QuantConnect/Lean / AverageDirectionalIndex: [local source](vendor/QuantConnect__Lean/Indicators/AverageDirectionalIndex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/AverageDirectionalIndex.cs#L30); source_indexed_not_runtime_validated.

## FAM-062 — Aroon

**Group:** Trend strength  
**Required data:** HL

Scales bars-since-high and bars-since-low into Up/Down lines; their difference forms an oscillator.

**Implementation detail:** Tie handling for repeated extremes affects values.

**Source implementations:**

- SRC-0013 — TA-Lib/ta-lib / AROON: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_AROON.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_AROON.c#L1); source_indexed_not_runtime_validated.
- SRC-0461 — xgboosted/pandas-ta-classic / aroon: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/aroon.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/aroon.py#L14); source_indexed_not_runtime_validated.
- SRC-0949 — TulipCharts/tulipindicators / aroon: [local source](vendor/TulipCharts__tulipindicators/indicators/aroon.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/aroon.c#L1); source_indexed_not_runtime_validated.
- SRC-1048 — DaveSkender/Stock.Indicators / Aroon: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/Aroon/Aroon.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/Aroon/Aroon.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1168 — joshuaulrich/TTR / aroon: [local source](vendor/joshuaulrich__TTR/R/aroon.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/aroon.R#L66); source_indexed_not_runtime_validated.
- SRC-1250 — QuantConnect/Lean / AroonOscillator: [local source](vendor/QuantConnect__Lean/Indicators/AroonOscillator.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/AroonOscillator.cs#L27); source_indexed_not_runtime_validated.

## FAM-063 — Vortex

**Group:** Trend direction  
**Required data:** HLC

Normalizes cross-bar high/low movement sums by total true range to produce VI+ and VI−.

**Implementation detail:** Confirm rolling window and first-bar conventions.

**Source implementations:**

- SRC-0228 — TA-Lib/ta-lib / VORTEX: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_VORTEX.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_VORTEX.c#L1); source_indexed_not_runtime_validated.
- SRC-0482 — xgboosted/pandas-ta-classic / vortex: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/vortex.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/vortex.py#L19); source_indexed_not_runtime_validated.
- SRC-0577 — peerchemist/finta / VORTEX: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1323); source_indexed_not_runtime_validated.
- SRC-1123 — DaveSkender/Stock.Indicators / Vortex: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Vortex/Vortex.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Vortex/Vortex.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1448 — QuantConnect/Lean / Vortex: [local source](vendor/QuantConnect__Lean/Indicators/Vortex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Vortex.cs#L27); source_indexed_not_runtime_validated.

## FAM-064 — Choppiness / VHF

**Group:** Regime measures  
**Required data:** HLC

CHOP compares accumulated range to total window excursion; VHF compares directional excursion to total price movement.

**Implementation detail:** These measure path efficiency or consolidation, not a guaranteed future breakout.

**Source implementations:**

- SRC-0089 — TA-Lib/ta-lib / CHOP: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CHOP.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CHOP.c#L1); source_indexed_not_runtime_validated.
- SRC-0226 — TA-Lib/ta-lib / VHF: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_VHF.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_VHF.c#L1); source_indexed_not_runtime_validated.
- SRC-0462 — xgboosted/pandas-ta-classic / chop: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/chop.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/chop.py#L18); source_indexed_not_runtime_validated.
- SRC-0481 — xgboosted/pandas-ta-classic / vhf: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/vhf.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/vhf.py#L18); source_indexed_not_runtime_validated.
- SRC-1033 — TulipCharts/tulipindicators / vhf: [local source](vendor/TulipCharts__tulipindicators/indicators/vhf.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/vhf.c#L1); source_indexed_not_runtime_validated.
- SRC-1059 — DaveSkender/Stock.Indicators / Chop: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Chop/Chop.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Chop/Chop.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1162 — joshuaulrich/TTR / VHF: [local source](vendor/joshuaulrich__TTR/R/VHF.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/VHF.R#L51); source_indexed_not_runtime_validated.
- SRC-1328 — QuantConnect/Lean / ChoppinessIndex: [local source](vendor/QuantConnect__Lean/Indicators/ChoppinessIndex.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ChoppinessIndex.cs#L26); source_indexed_not_runtime_validated.

## FAM-065 — Efficiency Ratio

**Group:** Regime measures  
**Required data:** Price

Absolute net change divided by the sum of absolute step changes measures directional path efficiency.

**Implementation detail:** A high value describes a past path; it does not prove continuation.

**Source implementations:**

- SRC-0112 — TA-Lib/ta-lib / ER: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ER.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ER.c#L1); source_indexed_not_runtime_validated.
- SRC-0354 — xgboosted/pandas-ta-classic / er: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/er.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/er.py#L12); source_indexed_not_runtime_validated.
- SRC-0533 — peerchemist/finta / ER: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L256); source_indexed_not_runtime_validated.

## FAM-066 — Trend Strength / CTI / RCI

**Group:** Regime measures  
**Required data:** Price

Correlation-based measures compare prices or their ranks with time to quantify directional consistency.

**Implementation detail:** Pearson price correlation and rank correlation are distinct definitions.

**Source implementations:**

- SRC-0100 — TA-Lib/ta-lib / CTI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CTI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CTI.c#L1); source_indexed_not_runtime_validated.
- SRC-0352 — xgboosted/pandas-ta-classic / cti: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/cti.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/cti.py#L12); source_indexed_not_runtime_validated.
- SRC-1136 — joshuaulrich/TTR / CTI: [local source](vendor/joshuaulrich__TTR/R/CTI.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/CTI.R#L56); source_indexed_not_runtime_validated.

## FAM-067 — Hurst Exponent

**Group:** Regime measures  
**Required data:** Price or returns

Estimates scaling/persistence using a particular statistical procedure and lookback.

**Implementation detail:** Short-sample estimates are noisy; estimator choice matters.

**Source implementations:**

- SRC-1080 — DaveSkender/Stock.Indicators / Hurst: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/e-j/Hurst/Hurst.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/e-j/Hurst/Hurst.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1356 — QuantConnect/Lean / HurstExponent: [local source](vendor/QuantConnect__Lean/Indicators/HurstExponent.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/HurstExponent.cs#L27); source_indexed_not_runtime_validated.

## FAM-068 — Entropy

**Group:** Regime measures  
**Required data:** Price-derived distribution

Summarizes dispersion or uncertainty of a chosen probability representation of the series.

**Implementation detail:** Results depend on how probabilities or bins are constructed; not all entropy indicators measure the same object.

**Source implementations:**

- SRC-0446 — xgboosted/pandas-ta-classic / entropy: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/statistics/entropy.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/statistics/entropy.py#L13); source_indexed_not_runtime_validated.

## FAM-069 — Bollinger Bands / %B / Width

**Group:** Volatility bands  
**Required data:** Price

Plots a moving centre with standard-deviation envelopes; %B locates price and bandwidth measures spread of the bands.

**Implementation detail:** Touching a band is a description, not automatic mean reversion.

**Source implementations:**

- SRC-0021 — TA-Lib/ta-lib / BBANDS: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_BBANDS.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_BBANDS.c#L1); source_indexed_not_runtime_validated.
- SRC-0488 — xgboosted/pandas-ta-classic / bbands: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/bbands.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/bbands.py#L48); source_indexed_not_runtime_validated.
- SRC-0559 — peerchemist/finta / BBANDS: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L935); source_indexed_not_runtime_validated.
- SRC-0955 — TulipCharts/tulipindicators / bbands: [local source](vendor/TulipCharts__tulipindicators/indicators/bbands.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/bbands.c#L1); source_indexed_not_runtime_validated.
- SRC-1054 — DaveSkender/Stock.Indicators / BollingerBands: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/BollingerBands/BollingerBands.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/BollingerBands/BollingerBands.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1169 — joshuaulrich/TTR / BBands: [local source](vendor/joshuaulrich__TTR/R/bollingerBands.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/bollingerBands.R#L75); source_indexed_not_runtime_validated.
- SRC-1230 — anandanand84/technicalindicators / BollingerBands: [local source](vendor/anandanand84__technicalindicators/src/volatility/BollingerBands.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volatility/BollingerBands.ts#L1); source_indexed_not_runtime_validated.
- SRC-1260 — QuantConnect/Lean / BollingerBands: [local source](vendor/QuantConnect__Lean/Indicators/BollingerBands.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/BollingerBands.cs#L22); source_indexed_not_runtime_validated.

## FAM-070 — Keltner / STARC

**Group:** Volatility bands  
**Required data:** HLC

Uses ATR/range-based envelopes around a moving-average centre.

**Implementation detail:** ATR and standard deviation bands respond differently to gaps.

**Source implementations:**

- SRC-0132 — TA-Lib/ta-lib / KC: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KC.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KC.c#L1); source_indexed_not_runtime_validated.
- SRC-0494 — xgboosted/pandas-ta-classic / kc: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/kc.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/kc.py#L19); source_indexed_not_runtime_validated.
- SRC-0563 — peerchemist/finta / KC: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1013); source_indexed_not_runtime_validated.
- SRC-0735 — everget/tradingview-pinescript-indicators / Stoller Average Range Channels (STARC) Bands: [local source](vendor/everget__tradingview-pinescript-indicators/bands_and_channels/stoller_average_range_channels.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/bands_and_channels/stoller_average_range_channels.pine#L1); source_indexed_not_runtime_validated.
- SRC-1174 — joshuaulrich/TTR / keltnerChannels: [local source](vendor/joshuaulrich__TTR/R/keltnerChannels.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/keltnerChannels.R#L82); source_indexed_not_runtime_validated.
- SRC-1232 — anandanand84/technicalindicators / KeltnerChannels: [local source](vendor/anandanand84__technicalindicators/src/volatility/KeltnerChannels.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volatility/KeltnerChannels.ts#L1); source_indexed_not_runtime_validated.
- SRC-1366 — QuantConnect/Lean / KeltnerChannels: [local source](vendor/QuantConnect__Lean/Indicators/KeltnerChannels.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/KeltnerChannels.cs#L24); source_indexed_not_runtime_validated.

## FAM-071 — Donchian / Price Channel

**Group:** Breakout structure  
**Required data:** HL

Upper/lower lines are rolling extremes with a midpoint centre.

**Implementation detail:** A breakout rule normally compares against an already known previous channel.

**Source implementations:**

- SRC-0105 — TA-Lib/ta-lib / DONCHIAN: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_DONCHIAN.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_DONCHIAN.c#L1); source_indexed_not_runtime_validated.
- SRC-0491 — xgboosted/pandas-ta-classic / donchian: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/donchian.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/donchian.py#L11); source_indexed_not_runtime_validated.
- SRC-1066 — DaveSkender/Stock.Indicators / Donchian: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Donchian/Donchian.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Donchian/Donchian.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1139 — joshuaulrich/TTR / DonchianChannel: [local source](vendor/joshuaulrich__TTR/R/DonchianChannel.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/DonchianChannel.R#L63); source_indexed_not_runtime_validated.
- SRC-1341 — QuantConnect/Lean / DonchianChannel: [local source](vendor/QuantConnect__Lean/Indicators/DonchianChannel.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/DonchianChannel.cs#L28); source_indexed_not_runtime_validated.

## FAM-072 — Squeeze / TTM-style squeeze

**Group:** Volatility compression  
**Required data:** OHLC

Detects Bollinger bands inside Keltner channels; momentum is displayed separately, often with a regression histogram.

**Implementation detail:** Squeeze does not specify the eventual direction; branded versions need not share identical code.

**Source implementations:**

- SRC-0382 — xgboosted/pandas-ta-classic / squeeze: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/squeeze.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/squeeze.py#L94); source_indexed_not_runtime_validated.
- SRC-1421 — QuantConnect/Lean / SqueezeMomentum: [local source](vendor/QuantConnect__Lean/Indicators/SqueezeMomentum.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/SqueezeMomentum.cs#L26); source_indexed_not_runtime_validated.

## FAM-073 — ATR / NATR / ADR

**Group:** Volatility  
**Required data:** OHLC

ATR smooths gap-aware true range; NATR normalizes by price; ADR averages daily high-low spans.

**Implementation detail:** Range units must match each instrument; ATR and ADR are not interchangeable.

**Source implementations:**

- SRC-0018 — TA-Lib/ta-lib / ATR: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ATR.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ATR.c#L1); source_indexed_not_runtime_validated.
- SRC-0168 — TA-Lib/ta-lib / NATR: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_NATR.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_NATR.c#L1); source_indexed_not_runtime_validated.
- SRC-0486 — xgboosted/pandas-ta-classic / atr: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/atr.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/atr.py#L21); source_indexed_not_runtime_validated.
- SRC-0496 — xgboosted/pandas-ta-classic / natr: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/natr.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/natr.py#L20); source_indexed_not_runtime_validated.
- SRC-0556 — peerchemist/finta / ATR: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L811); source_indexed_not_runtime_validated.
- SRC-0696 — mpquant/MyTT / ATR: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L184); source_indexed_not_runtime_validated.
- SRC-0953 — TulipCharts/tulipindicators / atr: [local source](vendor/TulipCharts__tulipindicators/indicators/atr.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/atr.c#L1); source_indexed_not_runtime_validated.
- SRC-0999 — TulipCharts/tulipindicators / natr: [local source](vendor/TulipCharts__tulipindicators/indicators/natr.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/natr.c#L1); source_indexed_not_runtime_validated.
- SRC-1049 — DaveSkender/Stock.Indicators / Atr: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/Atr/Atr.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/Atr/Atr.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1130 — joshuaulrich/TTR / TR: [local source](vendor/joshuaulrich__TTR/R/ATR.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/ATR.R#L65); source_indexed_not_runtime_validated.
- SRC-1131 — joshuaulrich/TTR / ATR: [local source](vendor/joshuaulrich__TTR/R/ATR.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/ATR.R#L88); source_indexed_not_runtime_validated.
- SRC-1208 — anandanand84/technicalindicators / ATR: [local source](vendor/anandanand84__technicalindicators/src/directionalmovement/ATR.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/directionalmovement/ATR.ts#L1); source_indexed_not_runtime_validated.
- SRC-1256 — QuantConnect/Lean / AverageTrueRange: [local source](vendor/QuantConnect__Lean/Indicators/AverageTrueRange.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/AverageTrueRange.cs#L31); source_indexed_not_runtime_validated.

## FAM-074 — Historical / Realized Volatility

**Group:** Volatility  
**Required data:** Returns

Aggregates squared returns or their standard deviation, with an explicit sampling interval and annualization factor.

**Implementation detail:** Trading sessions and annualization conventions change comparisons.

**Source implementations:**

- SRC-0454 — xgboosted/pandas-ta-classic / stdev: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/statistics/stdev.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/statistics/stdev.py#L15); source_indexed_not_runtime_validated.
- SRC-1422 — QuantConnect/Lean / StandardDeviation: [local source](vendor/QuantConnect__Lean/Indicators/StandardDeviation.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/StandardDeviation.cs#L27); source_indexed_not_runtime_validated.

## FAM-075 — Rogers-Satchell range volatility

**Group:** Volatility  
**Required data:** OHLC

Combines log high/open, high/close, low/open and low/close products into a range-based variance estimate.

**Implementation detail:** Requires strictly positive prices; an issue for unadjusted historical oil series containing nonpositive quotes.

**Source implementations:**

- SRC-0187 — TA-Lib/ta-lib / ROGERSSATCHELL: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ROGERSSATCHELL.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ROGERSSATCHELL.c#L1); source_indexed_not_runtime_validated.
- SRC-1415 — QuantConnect/Lean / RogersSatchellVolatility: [local source](vendor/QuantConnect__Lean/Indicators/RogersSatchellVolatility.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/RogersSatchellVolatility.cs#L26); source_indexed_not_runtime_validated.

## FAM-076 — Ulcer Index / drawdown

**Group:** Downside risk  
**Required data:** Price

Measures depth and persistence of percentage drawdowns from recent highs.

**Implementation detail:** Measures downside path risk rather than symmetric return volatility.

**Source implementations:**

- SRC-0501 — xgboosted/pandas-ta-classic / ui: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volatility/ui.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volatility/ui.py#L13); source_indexed_not_runtime_validated.
- SRC-0929 — everget/tradingview-pinescript-indicators / Ulcer Index: [local source](vendor/everget__tradingview-pinescript-indicators/volatility/ulcer_index.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/volatility/ulcer_index.pine#L1); source_indexed_not_runtime_validated.
- SRC-1120 — DaveSkender/Stock.Indicators / UlcerIndex: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/UlcerIndex/UlcerIndex.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/UlcerIndex/UlcerIndex.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-077 — Supertrend

**Group:** Trailing trend/stop  
**Required data:** HLC

Creates ATR-multiple bands and carries a selected band forward according to price breaks and previous state.

**Implementation detail:** Open-bar flips can disappear before the bar closes.

**Source implementations:**

- SRC-0208 — TA-Lib/ta-lib / SUPERTREND: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_SUPERTREND.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_SUPERTREND.c#L1); source_indexed_not_runtime_validated.
- SRC-0428 — xgboosted/pandas-ta-classic / supertrend: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/supertrend.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/supertrend.py#L67); source_indexed_not_runtime_validated.
- SRC-0922 — everget/tradingview-pinescript-indicators / SuperTrend: [local source](vendor/everget__tradingview-pinescript-indicators/trailing_stops/supertrend.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/trailing_stops/supertrend.pine#L1); source_indexed_not_runtime_validated.
- SRC-1114 — DaveSkender/Stock.Indicators / SuperTrend: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/r-s/SuperTrend/SuperTrend.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/r-s/SuperTrend/SuperTrend.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1426 — QuantConnect/Lean / SuperTrend: [local source](vendor/QuantConnect__Lean/Indicators/SuperTrend.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/SuperTrend.cs#L25); source_indexed_not_runtime_validated.

## FAM-078 — Chandelier Exit

**Group:** Trailing stop  
**Required data:** HLC

Places stops an ATR multiple away from rolling highs/lows, with stateful tightening rules.

**Implementation detail:** Exact prior-stop crossing logic matters for porting.

**Source implementations:**

- SRC-0597 — peerchemist/finta / CHANDELIER: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1746); source_indexed_not_runtime_validated.
- SRC-0918 — everget/tradingview-pinescript-indicators / Chandelier Exit: [local source](vendor/everget__tradingview-pinescript-indicators/trailing_stops/chandelier_exit.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/trailing_stops/chandelier_exit.pine#L1); source_indexed_not_runtime_validated.
- SRC-1058 — DaveSkender/Stock.Indicators / Chandelier: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Chandelier/Chandelier.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Chandelier/Chandelier.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1231 — anandanand84/technicalindicators / ChandelierExit: [local source](vendor/anandanand84__technicalindicators/src/volatility/ChandelierExit.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volatility/ChandelierExit.ts#L1); source_indexed_not_runtime_validated.

## FAM-079 — Parabolic SAR

**Group:** Trailing stop  
**Required data:** HL

Updates stop-and-reverse points using an acceleration factor and trend extremes.

**Implementation detail:** Initial trend seed and acceleration caps affect switches.

**Source implementations:**

- SRC-0192 — TA-Lib/ta-lib / SAR: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_SAR.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_SAR.c#L1); source_indexed_not_runtime_validated.
- SRC-0475 — xgboosted/pandas-ta-classic / psar: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/psar.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/psar.py#L73); source_indexed_not_runtime_validated.
- SRC-0557 — peerchemist/finta / SAR: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L821); source_indexed_not_runtime_validated.
- SRC-0558 — peerchemist/finta / PSAR: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L863); source_indexed_not_runtime_validated.
- SRC-0720 — mpquant/MyTT / SAR: [local source](vendor/mpquant__MyTT/MyTT_plus.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT_plus.py#L90); source_indexed_not_runtime_validated.
- SRC-1003 — TulipCharts/tulipindicators / psar: [local source](vendor/TulipCharts__tulipindicators/indicators/psar.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/psar.c#L1); source_indexed_not_runtime_validated.
- SRC-1155 — joshuaulrich/TTR / SAR: [local source](vendor/joshuaulrich__TTR/R/SAR.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/SAR.R#L53); source_indexed_not_runtime_validated.
- SRC-1214 — anandanand84/technicalindicators / PSAR: [local source](vendor/anandanand84__technicalindicators/src/momentum/PSAR.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/momentum/PSAR.ts#L1); source_indexed_not_runtime_validated.
- SRC-1398 — QuantConnect/Lean / ParabolicStopAndReverse: [local source](vendor/QuantConnect__Lean/Indicators/ParabolicStopAndReverse.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ParabolicStopAndReverse.cs#L25); source_indexed_not_runtime_validated.

## FAM-080 — HalfTrend

**Group:** Trailing trend  
**Required data:** OHLC

Uses rolling extremes, smoothed prices and persistent trend state to build a stepped trend line and ATR channel.

**Implementation detail:** A named port must be checked against the actual author implementation.

**Source implementations:**

- SRC-0919 — everget/tradingview-pinescript-indicators / HalfTrend: [local source](vendor/everget__tradingview-pinescript-indicators/trailing_stops/halftrend.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/trailing_stops/halftrend.pine#L1); source_indexed_not_runtime_validated.

## FAM-081 — UT Bot

**Group:** Trailing trend  
**Required data:** Price + ATR

Uses an ATR-distance trailing stop and price/short-average crossings to generate alerts.

**Implementation detail:** The original publication is linked; a chart alert does not define position sizing or fill rules.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-082 — Chande Kroll / NRTR

**Group:** Trailing stop  
**Required data:** OHLC

Combines directional extremes or trailing reversals with volatility/percentage distances.

**Implementation detail:** Different trailing stop families can produce strongly correlated signals.

**Source implementations:**

- SRC-0091 — TA-Lib/ta-lib / CKSP: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CKSP.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CKSP.c#L1); source_indexed_not_runtime_validated.
- SRC-0463 — xgboosted/pandas-ta-classic / cksp: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/trend/cksp.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/trend/cksp.py#L12); source_indexed_not_runtime_validated.
- SRC-0920 — everget/tradingview-pinescript-indicators / Nick Rypock Trailing Reverse: [local source](vendor/everget__tradingview-pinescript-indicators/trailing_stops/nrtr_nick_rypock_trailing_reverse.pine) · [pinned upstream](https://github.com/everget/tradingview-pinescript-indicators/blob/8385cc421888bbf31f36407195796bc0eabafb19/trailing_stops/nrtr_nick_rypock_trailing_reverse.pine#L1); source_indexed_not_runtime_validated.

## FAM-083 — OBV / PVT / ADL

**Group:** Volume accumulation  
**Required data:** OHLCV

OBV signs total volume by close direction; PVT weights volume by percentage return; ADL weights by close location within range.

**Implementation detail:** These are three distinct price-volume accumulation rules.

**Source implementations:**

- SRC-0004 — TA-Lib/ta-lib / AD: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_AD.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_AD.c#L1); source_indexed_not_runtime_validated.
- SRC-0170 — TA-Lib/ta-lib / OBV: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_OBV.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_OBV.c#L1); source_indexed_not_runtime_validated.
- SRC-0180 — TA-Lib/ta-lib / PVT: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_PVT.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_PVT.c#L1); source_indexed_not_runtime_validated.
- SRC-0502 — xgboosted/pandas-ta-classic / ad: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/ad.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/ad.py#L17); source_indexed_not_runtime_validated.
- SRC-0513 — xgboosted/pandas-ta-classic / obv: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/obv.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/obv.py#L19); source_indexed_not_runtime_validated.
- SRC-0517 — xgboosted/pandas-ta-classic / pvt: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/pvt.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/pvt.py#L18); source_indexed_not_runtime_validated.
- SRC-0584 — peerchemist/finta / OBV: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1479); source_indexed_not_runtime_validated.
- SRC-0712 — mpquant/MyTT / OBV: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L260); source_indexed_not_runtime_validated.
- SRC-0942 — TulipCharts/tulipindicators / ad: [local source](vendor/TulipCharts__tulipindicators/indicators/ad.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/ad.c#L1); source_indexed_not_runtime_validated.
- SRC-1001 — TulipCharts/tulipindicators / obv: [local source](vendor/TulipCharts__tulipindicators/indicators/obv.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/obv.c#L1); source_indexed_not_runtime_validated.
- SRC-1090 — DaveSkender/Stock.Indicators / Obv: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Obv/Obv.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Obv/Obv.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1153 — joshuaulrich/TTR / OBV: [local source](vendor/joshuaulrich__TTR/R/OBV.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/OBV.R#L48); source_indexed_not_runtime_validated.
- SRC-1236 — anandanand84/technicalindicators / OBV: [local source](vendor/anandanand84__technicalindicators/src/volume/OBV.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volume/OBV.ts#L1); source_indexed_not_runtime_validated.
- SRC-1470 — waditu/czsc / obv: [local source](vendor/waditu__czsc/crates/czsc-signals/src/obv.rs) · [pinned upstream](https://github.com/waditu/czsc/blob/5d350a943d6b1935561765fed5467c234973d121/crates/czsc-signals/src/obv.rs#L1); source_indexed_not_runtime_validated.

## FAM-084 — CMF / Chaikin Oscillator

**Group:** Volume flow  
**Required data:** OHLCV

CMF normalizes accumulated money-flow volume; Chaikin Oscillator compares short and long EMA values of ADL.

**Implementation detail:** Both depend on the meaning and completeness of volume.

**Source implementations:**

- SRC-0006 — TA-Lib/ta-lib / ADOSC: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ADOSC.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ADOSC.c#L1); source_indexed_not_runtime_validated.
- SRC-0092 — TA-Lib/ta-lib / CMF: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CMF.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CMF.c#L1); source_indexed_not_runtime_validated.
- SRC-0503 — xgboosted/pandas-ta-classic / adosc: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/adosc.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/adosc.py#L31); source_indexed_not_runtime_validated.
- SRC-0505 — xgboosted/pandas-ta-classic / cmf: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/cmf.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/cmf.py#L16); source_indexed_not_runtime_validated.
- SRC-0944 — TulipCharts/tulipindicators / adosc: [local source](vendor/TulipCharts__tulipindicators/indicators/adosc.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/adosc.c#L1); source_indexed_not_runtime_validated.
- SRC-1060 — DaveSkender/Stock.Indicators / Cmf: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Cmf/Cmf.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Cmf/Cmf.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1134 — joshuaulrich/TTR / CMF: [local source](vendor/joshuaulrich__TTR/R/CMF.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/CMF.R#L52); source_indexed_not_runtime_validated.

## FAM-085 — MFI / Force / Ease of Movement

**Group:** Volume flow  
**Required data:** OHLCV

MFI normalizes signed typical-price flow; Force multiplies price change by volume; EOM relates midpoint movement to volume and range.

**Implementation detail:** Do not treat CFD tick counts as centralized exchange turnover.

**Source implementations:**

- SRC-0109 — TA-Lib/ta-lib / EFI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_EFI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_EFI.c#L1); source_indexed_not_runtime_validated.
- SRC-0157 — TA-Lib/ta-lib / MFI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_MFI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_MFI.c#L1); source_indexed_not_runtime_validated.
- SRC-0506 — xgboosted/pandas-ta-classic / efi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/efi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/efi.py#L18); source_indexed_not_runtime_validated.
- SRC-0508 — xgboosted/pandas-ta-classic / eom: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/eom.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/eom.py#L19); source_indexed_not_runtime_validated.
- SRC-0511 — xgboosted/pandas-ta-classic / mfi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/mfi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/mfi.py#L21); source_indexed_not_runtime_validated.
- SRC-0583 — peerchemist/finta / MFI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1441); source_indexed_not_runtime_validated.
- SRC-0588 — peerchemist/finta / EFI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1569); source_indexed_not_runtime_validated.
- SRC-0713 — mpquant/MyTT / MFI: [local source](vendor/mpquant__MyTT/MyTT.py) · [pinned upstream](https://github.com/mpquant/MyTT/blob/7cd36ae13cae56657284badc8d5a6b7b8ed62a37/MyTT.py#L263); source_indexed_not_runtime_validated.
- SRC-0994 — TulipCharts/tulipindicators / mfi: [local source](vendor/TulipCharts__tulipindicators/indicators/mfi.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/mfi.c#L1); source_indexed_not_runtime_validated.
- SRC-1089 — DaveSkender/Stock.Indicators / Mfi: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Mfi/Mfi.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Mfi/Mfi.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1144 — joshuaulrich/TTR / MFI: [local source](vendor/joshuaulrich__TTR/R/MFI.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MFI.R#L57); source_indexed_not_runtime_validated.
- SRC-1235 — anandanand84/technicalindicators / MFI: [local source](vendor/anandanand84__technicalindicators/src/volume/MFI.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volume/MFI.ts#L1); source_indexed_not_runtime_validated.

## FAM-086 — Klinger / VFI / FVE

**Group:** Volume flow  
**Required data:** OHLCV

Alternative volume-pressure calculations use price direction, range or volatility thresholds before smoothing or accumulation.

**Implementation detail:** Filter thresholds and scaling vary substantially.

**Source implementations:**

- SRC-0137 — TA-Lib/ta-lib / KVO: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_KVO.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_KVO.c#L1); source_indexed_not_runtime_validated.
- SRC-0509 — xgboosted/pandas-ta-classic / kvo: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/kvo.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/kvo.py#L20); source_indexed_not_runtime_validated.
- SRC-0518 — xgboosted/pandas-ta-classic / vfi: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/vfi.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/vfi.py#L17); source_indexed_not_runtime_validated.
- SRC-0606 — peerchemist/finta / FVE: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L2001); source_indexed_not_runtime_validated.
- SRC-0607 — peerchemist/finta / VFI: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L2029); source_indexed_not_runtime_validated.
- SRC-0981 — TulipCharts/tulipindicators / kvo: [local source](vendor/TulipCharts__tulipindicators/indicators/kvo.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/kvo.c#L1); source_indexed_not_runtime_validated.
- SRC-1084 — DaveSkender/Stock.Indicators / Kvo: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/k-q/Kvo/Kvo.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/k-q/Kvo/Kvo.Series.cs#L1); source_indexed_not_runtime_validated.

## FAM-087 — VWAP / Anchored VWAP

**Group:** Volume benchmarks  
**Required data:** Price + actual or proxy volume

Computes Σ(price×volume)/Σ(volume) from a session or event anchor.

**Implementation detail:** A price-only approximation cannot reproduce the same quantity; anchors must be known at decision time.

**Source implementations:**

- SRC-0229 — TA-Lib/ta-lib / VWAP: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_VWAP.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_VWAP.c#L1); source_indexed_not_runtime_validated.
- SRC-0436 — xgboosted/pandas-ta-classic / vwap: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/vwap.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/vwap.py#L18); source_indexed_not_runtime_validated.
- SRC-0539 — peerchemist/finta / VWAP: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L411); source_indexed_not_runtime_validated.
- SRC-1124 — DaveSkender/Stock.Indicators / Vwap: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Vwap/Vwap.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Vwap/Vwap.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1237 — anandanand84/technicalindicators / VWAP: [local source](vendor/anandanand84__technicalindicators/src/volume/VWAP.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volume/VWAP.ts#L1); source_indexed_not_runtime_validated.

## FAM-088 — VWMA / EVWMA

**Group:** Volume averages  
**Required data:** Price + volume

VWMA uses a fixed rolling weighted window; EVWMA uses an elastic volume-sensitive update.

**Implementation detail:** Not equivalent to session VWAP.

**Source implementations:**

- SRC-0230 — TA-Lib/ta-lib / VWMA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_VWMA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_VWMA.c#L1); source_indexed_not_runtime_validated.
- SRC-0437 — xgboosted/pandas-ta-classic / vwma: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/vwma.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/vwma.py#L13); source_indexed_not_runtime_validated.
- SRC-0538 — peerchemist/finta / EVWMA: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L381); source_indexed_not_runtime_validated.
- SRC-1037 — TulipCharts/tulipindicators / vwma: [local source](vendor/TulipCharts__tulipindicators/indicators/vwma.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/vwma.c#L1); source_indexed_not_runtime_validated.
- SRC-1125 — DaveSkender/Stock.Indicators / Vwma: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/Vwma/Vwma.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/Vwma/Vwma.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1149 — joshuaulrich/TTR / EVWMA: [local source](vendor/joshuaulrich__TTR/R/MovingAverages.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/MovingAverages.R#L294); source_indexed_not_runtime_validated.

## FAM-089 — RVOL / Volume at Time

**Group:** Volume participation  
**Required data:** Timestamped volume

Compares current volume with historical expected volume, optionally matched by clock time.

**Implementation detail:** Match comparable sessions and daylight-saving transitions.

**Source implementations:**

- SRC-0191 — TA-Lib/ta-lib / RVOL: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_RVOL.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_RVOL.c#L1); source_indexed_not_runtime_validated.
- SRC-1408 — QuantConnect/Lean / RelativeDailyVolume: [local source](vendor/QuantConnect__Lean/Indicators/RelativeDailyVolume.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/RelativeDailyVolume.cs#L29); source_indexed_not_runtime_validated.

## FAM-090 — Volume Profile / POC / VAH / VAL

**Group:** Auction tools  
**Required data:** Price-level volume or lower-timeframe approximation

Distributes traded volume across price bins; POC is the largest bin and value area is constructed around volume concentration.

**Implementation detail:** OHLCV-only reconstruction is an estimate; session and binning rules affect levels.

**Source implementations:**

- SRC-0520 — xgboosted/pandas-ta-classic / vp: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/volume/vp.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/volume/vp.py#L13); source_indexed_not_runtime_validated.
- SRC-1238 — anandanand84/technicalindicators / VolumeProfile: [local source](vendor/anandanand84__technicalindicators/src/volume/VolumeProfile.ts) · [pinned upstream](https://github.com/anandanand84/technicalindicators/blob/7740f17cf681a2b1ace3009f5f396c14cbadf1f1/src/volume/VolumeProfile.ts#L1); source_indexed_not_runtime_validated.
- SRC-1445 — QuantConnect/Lean / VolumeProfile: [local source](vendor/QuantConnect__Lean/Indicators/VolumeProfile.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/VolumeProfile.cs#L23); source_indexed_not_runtime_validated.

## FAM-091 — TPO / Market Profile

**Group:** Auction tools  
**Required data:** Time-price visits

Counts price-level visits across fixed time blocks; builds a distribution of time participation rather than volume.

**Implementation detail:** Time-at-price is different from actual volume-at-price.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-092 — Delta / Cumulative Delta

**Group:** Order flow  
**Required data:** Aggressor-classified trades or an explicitly stated proxy

Delta sums buyer-initiated minus seller-initiated volume; CVD accumulates it over an anchor period.

**Implementation detail:** TradingView intrabar direction estimates and true bid/ask aggressor data are not equivalent.

**Source implementations:**

- SRC-1338 — QuantConnect/Lean / Delta: [local source](vendor/QuantConnect__Lean/Indicators/Delta.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Delta.cs#L27); source_indexed_not_runtime_validated.

## FAM-093 — Footprint / Imbalance / Absorption

**Group:** Order flow  
**Required data:** Bid/ask trades by price + ordered events

Displays buy/sell volume by price, tests imbalance ratios and relates aggressive flow to price response.

**Implementation detail:** Cannot reconstruct true absorption or bid/ask footprint from four OHLC numbers.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-094 — DOM / Order-book imbalance

**Group:** Order flow  
**Required data:** Timestamped depth/order events

Compares displayed bid and ask depth, updates, cancellations and queue behaviour.

**Implementation detail:** Displayed liquidity is not executed volume; spoofing and feed coverage affect interpretation.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-095 — Opening Range / Initial Balance

**Group:** Session structure  
**Required data:** OHLC + timezone/session

Records high/low of a predetermined opening window; monitors price relative to the completed range.

**Implementation detail:** Do not use the final opening-range high before that opening window has ended.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-096 — Pivot Points / CPR / Camarilla

**Group:** Session levels  
**Required data:** Completed prior OHLC

Calculates deterministic reference levels from the preceding session, with different formula families.

**Implementation detail:** Session boundaries and method names must be explicit.

**Source implementations:**

- SRC-0567 — peerchemist/finta / PIVOT: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L1123); source_indexed_not_runtime_validated.
- SRC-1401 — QuantConnect/Lean / PivotPointsHighLow: [local source](vendor/QuantConnect__Lean/Indicators/PivotPointsHighLow.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/PivotPointsHighLow.cs#L27); source_indexed_not_runtime_validated.

## FAM-097 — Fractals / Zigzag / Swing pivots

**Group:** Market structure  
**Required data:** HL

Identifies local extrema with right-side confirmation or reversal thresholds and connects significant swings.

**Implementation detail:** Confirmed historical pivot location is earlier than the moment it became knowable.

**Source implementations:**

- SRC-0236 — TA-Lib/ta-lib / ZIGZAG: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_ZIGZAG.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_ZIGZAG.c#L1); source_indexed_not_runtime_validated.
- SRC-0611 — peerchemist/finta / WILLIAMS_FRACTAL: [local source](vendor/peerchemist__finta/finta/finta.py) · [pinned upstream](https://github.com/peerchemist/finta/blob/af01fa594995de78f5ada5c336e61cd87c46b151/finta/finta.py#L2208); source_indexed_not_runtime_validated.
- SRC-1128 — DaveSkender/Stock.Indicators / ZigZag: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/t-z/ZigZag/ZigZag.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/t-z/ZigZag/ZigZag.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1166 — joshuaulrich/TTR / ZigZag: [local source](vendor/joshuaulrich__TTR/R/ZigZag.R) · [pinned upstream](https://github.com/joshuaulrich/TTR/blob/76e5618e4a714f190519ee98da6de3234cf7d8b5/R/ZigZag.R#L61); source_indexed_not_runtime_validated.
- SRC-1456 — QuantConnect/Lean / ZigZag: [local source](vendor/QuantConnect__Lean/Indicators/ZigZag.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ZigZag.cs#L27); source_indexed_not_runtime_validated.

## FAM-098 — BOS / CHoCH

**Group:** Market structure  
**Required data:** OHLC + a defined swing algorithm

Marks breaks of swing levels, distinguishing continuation and possible change in structural direction.

**Implementation detail:** Definitions depend on pivot confirmation, close/wick rules and lag.

**Source implementations:**

- SRC-0724 — joshyattridge/smart-money-concepts / bos_choch: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L222); source_indexed_not_runtime_validated.

## FAM-099 — Order Blocks

**Group:** Market structure  
**Required data:** OHLCV + structural rules

Labels a preceding price area associated with a defined structural impulse and tracks mitigation.

**Implementation detail:** Price-bar order blocks do not directly identify institutional inventory.

**Source implementations:**

- SRC-0725 — joshyattridge/smart-money-concepts / ob: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L376); source_indexed_not_runtime_validated.

## FAM-100 — FVG / Inverse FVG

**Group:** Market structure  
**Required data:** OHLC

A three-bar gap condition marks nonoverlap between the first and third bars; inverse variants track later invalidation/reuse.

**Implementation detail:** Some implementations attach the result to the middle bar before the third bar actually exists.

**Source implementations:**

- SRC-0722 — joshyattridge/smart-money-concepts / fvg: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L56); source_indexed_not_runtime_validated.

## FAM-101 — Liquidity Sweeps / EQH / EQL

**Group:** Market structure  
**Required data:** OHLC + confirmed swings

Clusters similar highs/lows and detects excursions through a level followed by a specified rejection.

**Implementation detail:** A sweep label is a rule-based price pattern, not proof of stop orders in the book.

**Source implementations:**

- SRC-0380 — xgboosted/pandas-ta-classic / smc_sweep: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/momentum/smc_sweep.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/momentum/smc_sweep.py#L12); source_indexed_not_runtime_validated.
- SRC-0726 — joshyattridge/smart-money-concepts / liquidity: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L573); source_indexed_not_runtime_validated.

## FAM-102 — Previous Day/Week High-Low

**Group:** Market structure  
**Required data:** Completed session OHLC

Projects already completed prior-session extremes as reference levels.

**Implementation detail:** Broker days, New York sessions and exchange sessions produce different boundaries.

**Source implementations:**

- SRC-0727 — joshyattridge/smart-money-concepts / previous_high_low: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L701); source_indexed_not_runtime_validated.

## FAM-103 — Fibonacci / Pitchfork / Regression channels

**Group:** Geometric tools  
**Required data:** Price + selected anchors

Projects ratios, median-line parallels or statistical trend channels from selected price anchors.

**Implementation detail:** Automatically selected historical anchors may revise as later pivots arrive.

**Source implementations:**

- SRC-0409 — xgboosted/pandas-ta-classic / linreg: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/linreg.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/overlap/linreg.py#L92); source_indexed_not_runtime_validated.
- SRC-0983 — TulipCharts/tulipindicators / linreg: [local source](vendor/TulipCharts__tulipindicators/indicators/linreg.c) · [pinned upstream](https://github.com/TulipCharts/tulipindicators/blob/be18abb13e075ba866898dcc7cb52399603302a6/indicators/linreg.c#L1); source_indexed_not_runtime_validated.

## FAM-104 — Harmonics: Gartley / Bat / Butterfly / Crab / Shark / Cypher

**Group:** Geometric patterns  
**Required data:** Confirmed swing points

Classifies multi-leg structures by constrained retracement and extension ratios.

**Implementation detail:** Ratio tolerances and pivot definitions are part of the method; a pattern name is not a full algorithm.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-105 — Elliott Wave

**Group:** Structural theories  
**Required data:** Price + wave-labelling rules

Labels nested impulse/correction structures subject to a chosen set of wave constraints.

**Implementation detail:** Competing valid counts and relabelling make retrospective chart appearance unreliable as live evidence.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-106 — Wyckoff / VSA / Weis Wave

**Group:** Structural theories  
**Required data:** OHLCV + specified event rules

Examines price spread, volume, tests and wave accumulation to describe accumulation/distribution hypotheses.

**Implementation detail:** Narrative labels must become deterministic rules before testing; volume quality matters.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-107 — Gann / square-of-nine / time cycles

**Group:** Geometric theories  
**Required data:** Price scale + time coordinates

Constructs geometric price/time levels from explicit scaling and anchor conventions.

**Implementation detail:** A line angle changes with chart scaling; claims require a precise invariant definition.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-108 — Candlestick pattern families

**Group:** Pattern recognition  
**Required data:** OHLC

Algorithms compare body, wick, gap and relative-size relationships across one or more bars.

**Implementation detail:** Pattern outputs describe candle arrangements, not calibrated win probabilities; trend context may not be checked.

**Source implementations:**

- SRC-0041 — TA-Lib/ta-lib / CDLDOJI: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CDLDOJI.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CDLDOJI.c#L1); source_indexed_not_runtime_validated.
- SRC-0044 — TA-Lib/ta-lib / CDLENGULFING: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CDLENGULFING.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CDLENGULFING.c#L1); source_indexed_not_runtime_validated.
- SRC-0049 — TA-Lib/ta-lib / CDLHAMMER: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CDLHAMMER.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CDLHAMMER.c#L1); source_indexed_not_runtime_validated.
- SRC-0253 — xgboosted/pandas-ta-classic / cdl_doji: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/candles/cdl_doji.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/candles/cdl_doji.py#L18); source_indexed_not_runtime_validated.
- SRC-0256 — xgboosted/pandas-ta-classic / cdl_engulfing: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/candles/cdl_engulfing.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/candles/cdl_engulfing.py#L43); source_indexed_not_runtime_validated.
- SRC-0261 — xgboosted/pandas-ta-classic / cdl_hammer: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/candles/cdl_hammer.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/candles/cdl_hammer.py#L51); source_indexed_not_runtime_validated.

## FAM-109 — Nadaraya-Watson envelope / smoother

**Group:** Kernel methods  
**Required data:** Price

Uses kernel-weighted averages to estimate a smooth curve and optional residual bands.

**Implementation detail:** A trailing endpoint estimate can be causal; a centred/repainting display uses future observations relative to older bars.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-110 — Lorentzian Classification / kNN

**Group:** Machine-learning scripts  
**Required data:** Computed price features + historical labels

Uses a Lorentzian-style distance and approximate neighbour selection to classify future-direction labels from historical examples.

**Implementation detail:** Training-label availability, neighbour chronology and in-sample selection must be checked in the actual code.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-111 — Adaptive ML Supertrend

**Group:** Machine-learning scripts  
**Required data:** ATR history + price

Clusters historical volatility into regimes and uses a selected cluster representative in a Supertrend calculation.

**Implementation detail:** Volatility clustering is not proof of price prediction; fitting must use only past observations.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-112 — COT Index / net positioning

**Group:** Positioning context  
**Required data:** CFTC reports + publication timestamps

Transforms participant net positions, changes or historical min-max ranks into contextual series.

**Implementation detail:** Weekly observation date is not public release time; never backfill Tuesday knowledge into a live decision before publication.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-113 — Open Interest / price-OI regimes

**Group:** Positioning context  
**Required data:** Exchange derivative open interest

Measures outstanding contracts and combines OI changes with price changes to describe participation.

**Implementation detail:** Not a spot CFD field; contract rolls and aggregation affect the series.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-114 — Options IV / skew / term structure / gamma

**Group:** Options context  
**Required data:** Options chains + rates + model assumptions

Summarizes option-implied uncertainty and exposure across strikes and expiries.

**Implementation detail:** Dealer gamma sign and ownership are often estimated rather than directly observed.

**Source implementations:**

- SRC-1351 — QuantConnect/Lean / Gamma: [local source](vendor/QuantConnect__Lean/Indicators/Gamma.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Gamma.cs#L27); source_indexed_not_runtime_validated.
- SRC-1359 — QuantConnect/Lean / ImpliedVolatility: [local source](vendor/QuantConnect__Lean/Indicators/ImpliedVolatility.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/ImpliedVolatility.cs#L29); source_indexed_not_runtime_validated.

## FAM-115 — Intermarket ratios / rolling correlation / beta

**Group:** Cross-market context  
**Required data:** Time-aligned prices of multiple instruments

Compares markets using ratios, covariances, rolling regressions or residuals.

**Implementation detail:** Availability timestamps and different trading hours matter; relationships may change sign.

**Source implementations:**

- SRC-0023 — TA-Lib/ta-lib / BETA: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_BETA.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_BETA.c#L1); source_indexed_not_runtime_validated.
- SRC-0096 — TA-Lib/ta-lib / CORREL: [local source](vendor/TA-Lib__ta-lib/src/ta_func/ta_CORREL.c) · [pinned upstream](https://github.com/TA-Lib/ta-lib/blob/62021c1d14ef5499505af5547384cab509adf3fc/src/ta_func/ta_CORREL.c#L1); source_indexed_not_runtime_validated.
- SRC-0444 — xgboosted/pandas-ta-classic / beta: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/statistics/beta.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/statistics/beta.py#L11); source_indexed_not_runtime_validated.
- SRC-0445 — xgboosted/pandas-ta-classic / correl: [local source](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/statistics/correl.py) · [pinned upstream](https://github.com/xgboosted/pandas-ta-classic/blob/9715f2445f0c39b79cf3dec5e2c341b89d69e182/pandas_ta_classic/statistics/correl.py#L11); source_indexed_not_runtime_validated.
- SRC-1053 — DaveSkender/Stock.Indicators / Beta: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/a-b/Beta/Beta.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/a-b/Beta/Beta.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1063 — DaveSkender/Stock.Indicators / Correlation: [local source](vendor/DaveSkender__Stock.Indicators/src/Indicators/c-d/Correlation/Correlation.Series.cs) · [pinned upstream](https://github.com/DaveSkender/Stock.Indicators/blob/0c72adabc42e8aac5cef788add6529b251d45444/src/Indicators/c-d/Correlation/Correlation.Series.cs#L1); source_indexed_not_runtime_validated.
- SRC-1259 — QuantConnect/Lean / Beta: [local source](vendor/QuantConnect__Lean/Indicators/Beta.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Beta.cs#L33); source_indexed_not_runtime_validated.
- SRC-1334 — QuantConnect/Lean / Correlation: [local source](vendor/QuantConnect__Lean/Indicators/Correlation.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/Correlation.cs#L39); source_indexed_not_runtime_validated.

## FAM-116 — Seasonality / session statistics

**Group:** Calendar context  
**Required data:** Timestamped historical returns

Groups past observations by month, weekday or exchange-session clock to describe recurring distributions.

**Implementation detail:** Avoid full-sample averages that leak the evaluation period into its own reference.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-117 — EIA inventories / crude time spreads

**Group:** Oil-specific context  
**Required data:** EIA releases + separately quoted futures maturities

Inventory changes describe physical balances; near/far futures spreads describe the term structure.

**Implementation detail:** Release timestamp, revisions and contract identity are required; a CFD candle alone cannot supply these data.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-118 — Gold real-yield / dollar / GVZ context

**Group:** Gold-specific context  
**Required data:** FRED real yields + dollar reference + options volatility

Adds separate macro/volatility series alongside gold prices for analysis.

**Implementation detail:** These are contextual data inputs, not a guaranteed negative or positive relationship with gold.

**Source status:** no exact-name local implementation matched; consult the primary publication links in REPORT.md and TRADINGVIEW_PUBLICATIONS.md.

## FAM-119 — Nasdaq breadth / VXN / relative strength

**Group:** Equity-index context  
**Required data:** Constituent prices + index/options data

Measures participation across constituent stocks, implied volatility or relative performance versus a reference index.

**Implementation detail:** Use historical constituents and weights to avoid survivorship bias; QQQ is a reference feed in this project.

**Source implementations:**

- SRC-1243 — QuantConnect/Lean / AdvanceDeclineDifference: [local source](vendor/QuantConnect__Lean/Indicators/AdvanceDeclineDifference.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/AdvanceDeclineDifference.cs#L24); source_indexed_not_runtime_validated.
- SRC-1245 — QuantConnect/Lean / AdvanceDeclineRatio: [local source](vendor/QuantConnect__Lean/Indicators/AdvanceDeclineRatio.cs) · [pinned upstream](https://github.com/QuantConnect/Lean/blob/f3d841e60dfd010ee5fc293ea893e56952484108/Indicators/AdvanceDeclineRatio.cs#L25); source_indexed_not_runtime_validated.

## FAM-120 — DAX session / breadth / volatility context

**Group:** Equity-index context  
**Required data:** Eurex/Xetra sessions + constituents + optional volatility data

Aligns futures, cash-index trading and constituent participation to a documented exchange session.

**Implementation detail:** DAX cash, FDAX futures and a broker CFD are distinct series and can have different prices/hours.

**Source implementations:**

- SRC-0728 — joshyattridge/smart-money-concepts / sessions: [local source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) · [pinned upstream](https://github.com/joshyattridge/smart-money-concepts/blob/1b62fd6c41e1f508e7ed76831a039fa4c82d42f6/smartmoneyconcepts/smc.py#L793); source_indexed_not_runtime_validated.

