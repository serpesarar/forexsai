# Indicator research: methods, source code and four-market applicability

Research date: **25 October 2026**. Target execution feeds: `XAUUSD`, `USOIL.FOREX`, `GDAXI.INDX`, `NDX.INDX`.

## What this research established

The earlier catalogue covered 239 TradingView help pages. This research expands beyond that help centre into **120 method-family cards, 496 public TradingView publication IDs, 13 pinned source repositories, 2,132 downloaded source/notice files and 1,480 statically indexed implementation records**. There are **210 Pine files**, including utilities and visual experiments as well as indicator scripts. The 1,480 entries include repeated implementations, mathematical operations, pattern recognizers, formula helpers and structural components. They are not 1,480 independent indicators.

The deliverables connect names to explanations and actual source locations. [FAMILIES.md](FAMILIES.md) explains the methods; [IMPLEMENTATIONS.md](IMPLEMENTATIONS.md) links the software; [catalog.html](catalog.html) searches both, together with TradingView discoveries. Original names and Chinese/Japanese aliases are preserved.

This is a source investigation, not a profitability ranking. No target-market price data were loaded for a new experiment. No library-wide numerical parity, compilation, prefix-causality or performance certification is implied. Most source records were extracted statically; the focused code observations below were inspected directly. The rest remain available for a subsequent implementation-specific review.

## Research and coverage ledger

| Layer | Method | Confirmed scope | Boundary |
|---|---|---|---|
| TradingView built-in help | Four official support sections, previously retrieved | All 239 listed help pages in those four sections | Includes metrics, guides and some strategies; not a unique-indicator count or complete live menu export |
| TradingView community | First public page of 24 topics plus selected original publications | 496 distinct script IDs | No pagination; discovery metadata does not establish source access |
| Selected publication checks | Opened original publication detail pages | 17 selected publication pages | 16 showed an open-source badge; one BBI publication showed protected/invite access; no source downloaded for these detail-page records |
| Code repositories | Downloaded selected source directories at explicit commit IDs | 13 repositories and 2,132 files | Source snapshots are not necessarily complete buildable repositories |
| Static implementation index | XML registries, AST parsing, C metadata, class/function declarations and Pine titles | 1,480 records | Helpers and implementations are typed; duplicate mathematics is not globally canonicalized |
| Method cards | Authored working explanations and implementation caveats | 120 cards | Some cards group several related methods; exact-name source matches are navigation aids, not equivalence proofs |
| Integrity checks | Compared every local source file to the captured SHA256 and checked indexed line locations | 2,132 hashes and all 1,480 source references | Proves preservation and navigation, not numerical correctness |

The 24 topic pages were: Editors' Picks, KDJ, BBI, Blackcat, Ichimoku Clouds, Ehlers, Kalman Filter, Market Profile, Order Flow, Volume Profile, Smart Money Concepts, Harmonic Patterns, Gold, Crude Oil, DAX, Nasdaq 100, WaveTrend, Wyckoff, Gann, Squeeze, Machine Learning, Fractal, Renko and Point & Figure. Exact topic URLs and result counts are in [TRADINGVIEW_DISCOVERY.json](TRADINGVIEW_DISCOVERY.json). Names such as “gold” in a publication tag establish topical association, not an independently verified edge in gold.

TradingView's [Pine first-steps documentation](https://www.tradingview.com/pine-script-docs/primer/first-steps/) describes a community library exceeding 150,000 scripts. Indicators, strategies and libraries are distinct script types. A bounded public web crawl cannot honestly be described as all of that library, and private/invite-only publications add an inaccessible layer. This package does not bypass those access limits.

## Source-code coverage

| Repository | Language / role | Indexed records | Why included |
|---|---|---:|---|
| [TA-Lib/ta-lib](https://github.com/TA-Lib/ta-lib) | C | 237 | Explicit function registry, inputs, defaults and C calculations, including candle recognizers and math operations |
| [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) | Python | 284 | Broad native implementations, adaptive filters, momentum, volume, patterns and signal utilities |
| [TulipCharts/tulipindicators](https://github.com/TulipCharts/tulipindicators) | C | 104 | Compact computational implementations with typed input/output metadata |
| [DaveSkender/Stock.Indicators](https://github.com/DaveSkender/Stock.Indicators) | C# | 85 | Indicator families including Hurst, Ichimoku, channels and trailing stops |
| [peerchemist/finta](https://github.com/peerchemist/finta) | Python | 92 | Alternative formulas, WaveTrend, FRAMA and several useful comparisons; contains explicit placeholders |
| [bukosabino/ta](https://github.com/bukosabino/ta) | Python | 31 | Class-based price/volume indicator implementations |
| [joshuaulrich/TTR](https://github.com/joshuaulrich/TTR) | R / C | 67 | Established R technical-analysis formulas and related helpers |
| [mpquant/MyTT](https://github.com/mpquant/MyTT) | Python / Chinese formulas | 77 | TongDaXin/TongHuaShun-style formulas and formula-building primitives |
| [everget/tradingview-pinescript-indicators](https://github.com/everget/tradingview-pinescript-indicators) | Pine | 210 | Direct chart scripts including Ehlers, adaptive averages, RSX variants, HalfTrend and trailing stops |
| [anandanand84/technicalindicators](https://github.com/anandanand84/technicalindicators) | TypeScript | 43 | Browser/JavaScript-oriented algorithms and candlestick recognizers |
| [joshyattridge/smart-money-concepts](https://github.com/joshyattridge/smart-money-concepts) | Python | 8 | FVG, confirmed swings, BOS/CHoCH, blocks, liquidity, sessions and retracements |
| [waditu/czsc](https://github.com/waditu/czsc) | Rust / Chinese structural methods | 24 | Chan signal modules rather than misleadingly counting every internal helper as an indicator |
| [QuantConnect/Lean](https://github.com/QuantConnect/Lean) | C# | 218 | Streaming indicators, statistical components and 63 candlestick-pattern classes |

All counts refer to the downloaded commit, not a timeless package claim or marketing count. Libraries change. The exact commits and licence evidence are in [SOURCES_AND_LICENSES.md](SOURCES_AND_LICENSES.md) and [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). We did not install these libraries in ForexSAI or add them as dependencies.

### Source access is not the same as unlimited reuse

MIT/BSD/Apache and GPL/LGPL have different terms. Keep original notices. Public code bearing a proprietary brand name is not automatically the original commercial algorithm. MyTT has a GPL badge in its README but no root full licence/version file in the snapshot. CZSC's root contains an Apache-2.0 notice while GitHub reports NOASSERTION; subcrate terms need confirmation. Their code is therefore excluded from the distributable ZIP, while pinned links and index metadata remain. The other 11 selected source snapshots retain their collected licence notices. No original licence has been replaced by a blanket licence for this package.

## Families beyond the usual RSI/MACD list

The cards deliberately include several different kinds of objects:

- **Japanese charting:** Ichimoku, Heikin Ashi, Renko, Kagi and Line Break; calculation time is separated from chart display location.
- **Chinese formula systems:** KDJ/随机指标, BBI/多空指标, BIAS/乖离率, PSY/心理线, BRAR/人气意愿指标, CR/能量指标, VR, DFMA, EXPMA, TAQ, KTN, XSII/薛斯通道 and Chanlun/缠论 components.
- **Adaptive/digital filters:** KAMA, VIDYA, FRAMA, MAMA/FAMA, McGinley, Jurik-labelled public variants, Ehlers Super Smoother/Roofing/Cyber Cycle, Laguerre, Hilbert cycle/phase methods and Kalman filtering.
- **Momentum variants:** QQE, QQE MOD, WaveTrend, Schaff Trend Cycle, Connors RSI, SMI, TSI, KST, Special K and several normalized price/volume oscillators.
- **Auction/order flow:** anchored VWAP, volume profile, POC/VAH/VAL, TPO, initial balance, delta/CVD, footprint, absorption and DOM imbalance. These differ fundamentally in required data.
- **Structural theories:** BOS/CHoCH, blocks, FVG, sweeps, equal highs/lows, harmonics, Elliott, Wyckoff/VSA/Weis Wave and Gann geometry. Each needs explicit confirmation/anchor rules before it is an algorithm.
- **Statistical and contextual tools:** Hurst, entropy, correlation, beta, kernel regression, nearest-neighbour classification, volatility clustering, COT, open interest, options volatility/skew/gamma, session seasonality, EIA inventories and futures time spreads.

A family card with no exact local source match explicitly says so. In particular, a conceptual footprint, gamma, Gann or Elliott description is not a claim that the package contains a complete, certified implementation of that entire theory.

## Focused software findings

### 1. Ichimoku: forward display is different from a future observation

A typical configuration uses Tenkan 9, Kijun 26 and Senkou B 52 bars:

- Tenkan = (rolling high9 + rolling low9)/2.
- Kijun = (rolling high26 + rolling low26)/2.
- Raw Senkou A = (Tenkan + Kijun)/2; raw Senkou B = (rolling high52 + rolling low52)/2. Both are displayed ahead of their calculation date.
- Chikou is the current close displayed backward. In a historical dataframe, attaching a later close to an earlier row introduces future information if that column is used as a decision-time feature.

The collected [pandas-ta-classic implementation](vendor/xgboosted__pandas-ta-classic/pandas_ta_classic/overlap/ichimoku.py) explicitly creates `close.shift(-kijun)` for Chikou. Its `lookahead=False` option disables inclusion of that component. This is an actual source observation, not a claim that the cloud itself predicts future prices. Its future-dated plotting dataframe must also be handled separately from decision-time feature rows. MT5 buffer access has its own conventions; use [iIchimoku documentation](https://www.mql5.com/en/docs/indicators/iichimoku) when porting.

### 2. The same indicator name can hide materially different formulas

The collected [MyTT source](vendor/mpquant__MyTT/MyTT.py) demonstrates several concrete examples:

| Name | Observed MyTT definition/default | Porting implication |
|---|---|---|
| KDJ | RSV on 9 bars; K and D are EMA(RSV,5) then EMA(K,5) for M1=M2=3; J=3K−2D | Do not substitute a generic fast stochastic without matching recursive smoothing |
| BBI | Average of SMA3, SMA6, SMA12 and SMA20 | A 3/6/12/24 implementation is a different setting |
| MACD | Histogram is **2 × (DIF−DEA)** | A threshold copied from an undoubled histogram is scaled incorrectly |
| ATR | Default 20, calculated with arithmetic MA of true range | Not the usual 14-bar Wilder-smoothed ATR |
| RSI | Default 24, using Chinese recursive SMA primitives | Not automatically identical to a platform's default RSI14 |
| WR | `(highest−close)/(highest−lowest)×100`, positive 0–100 orientation | Classical Williams %R is commonly displayed −100 to 0 |

These differences matter directly when chart signals and backend numbers are compared. Names, screenshots or “same indicator” labels are insufficient for numerical parity. The Chinese `SMA(X,N,M)` primitive is recursive smoothing with a weight related to M/N; it does not mean the same operation as an ordinary arithmetic SMA.

### 3. SMC labels can be attached earlier than they become knowable

The [smart-money-concepts source](vendor/joshyattridge__smart-money-concepts/smartmoneyconcepts/smc.py) compares `high.shift(1)` with `low.shift(-1)` for a bullish FVG around the middle bar. The third bar is required. If a backtest acts at the middle row using the completed batch output, it acts before the needed bar exists.

Its swing routine explicitly considers candles before **and after** a candidate. A final pivot location is therefore different from its confirmation time. Downstream BOS/CHoCH and blocks inherit that dependency. Mitigation/broken indexes are retrospective event annotations and also need availability timestamps. This does not make a retrospective chart-annotation library intrinsically wrong; it means batch annotations cannot be copied directly into a live feature stream without an explicit availability contract.

### 4. A documented method may have no implementation

Direct inspection found six `raise NotImplementedError` methods in [Finta](vendor/peerchemist__finta/finta/finta.py): **LWMA, VIDYA, ALMA, MAMA, SWI and TMF**. The index marks them as placeholders. Several have genuine implementations in other collected libraries. A large indicator count in a README does not prove every named method works.

### 5. Public Jurik-related names are not proof of proprietary equivalence

The Pine snapshot contains JMA/RSX-labelled public scripts. They can be studied as their own published algorithms. We have not established identity with proprietary Jurik Research products, nor obtained any proprietary source. Treat the formula and exact source revision as the method identifier.

### 6. Ehlers methods require state, initialization and sampling discipline

The Pine snapshot includes Super Smoother, Roofing, Cyber Cycle, Laguerre and MESA adaptive variants. For example, [Super Smoother](vendor/everget__tradingview-pinescript-indicators/movings/ehlers_super_smoother_filter.pine) combines current/prior price with previous filter states and period-derived coefficients. Different seeds can produce different early signals even with the same coefficients.

The original MESA papers endpoint returned HTTP 403 during this research, so no claim is based on inspecting a blocked page. Accessible primary references include the [MQL5 Super Smoother publication with its formula](https://www.mql5.com/en/code/22208), the publisher's [April 2024 Traders' Tips](https://traders.com/Documentation/FEEDbk_docs/2024/04/TradersTips.html), and [PineCodersTASC's Ultimate Smoother implementation](https://www.tradingview.com/script/X67OSwqc-TASC-2024-04-The-Ultimate-Smoother/). A “zero-lag” statement about a filter's passband does not establish zero delay or advance knowledge in all market conditions.

### 7. Static flags are review prompts, not a verdict

The index detects negative `.shift()`, centred rolling windows, lookahead settings, pivot/fractal terms and explicit placeholders. Some shifts are necessary for plotting; some centred calculations are safe if output is delayed. A lexical match is neither a complete causality audit nor proof of a defect. Absence of a match is not a safety certificate. No prefix test was run on the vendor algorithms in this task.

## Selected original TradingView publications

These original pages were inspected for publication identity and code-access badges. An open-source badge means the page advertises source accessibility; the corresponding publication's full code was not downloaded as part of the community crawl. Local Pine snapshots are separately indexed by repository and commit and may not match the latest TradingView revision.

| Publication | Described mechanism / distinction |
|---|---|
| [Ichimoku Kinko Hyo — IchimokuEdge](https://www.tradingview.com/script/4EpIOEMu-Ichimoku-Kinko-Hyo/) | Five-line/cloud system; inspect alignment rather than treating every plotted line as contemporaneous data |
| [Ichimoku Kinkō hyō 目均衡表 — RickSimpson](https://www.tradingview.com/script/HG385dBY/) | Broader Ichimoku/Hosoda-related implementation; author descriptions are not independently verified performance claims |
| [KDJ Trading System — blackcat1402](https://www.tradingview.com/script/t2PFNKEf-blackcat-L2-KDJ-Trading-System/) | KDJ-family composite script; confirms presence of Chinese-derived methods on TradingView |
| [BBI — AgentC](https://www.tradingview.com/script/QmGxhXJ7/) | BBI-name publication; page indicated protected/invite access, so full formula identity is not claimed |
| [Squeeze Momentum — LazyBear](https://www.tradingview.com/script/nqQ1DT5a-Squeeze-Momentum-Indicator-LazyBear/) | Bollinger-inside-Keltner compression with a regression-based momentum histogram; publication notes a historical multiplier correction |
| [WaveTrend — LazyBear](https://www.tradingview.com/script/2KE8wTuF-Indicator-WaveTrend-Oscillator-WT/) | Smoothed normalized price displacement with signal-line comparison |
| [QQE MOD — Mihkel00](https://www.tradingview.com/script/TpUW4muw-QQE-MOD/) | Two QQE constructions with a Bollinger-related confirmation layer |
| [HalfTrend — everget](https://www.tradingview.com/script/U1SJ8ubc-HalfTrend/) | Stateful stepped trend algorithm; local author's repository also contains a version |
| [Chandelier Exit — everget](https://www.tradingview.com/script/AqXxNS7j-Chandelier-Exit-everget/) | ATR trailing stop with explicit state transitions; local source available |
| [UT Bot Alerts — QuantNomad](https://www.tradingview.com/script/n8ss8BID-UT-Bot-Alerts/) | ATR trailing-stop alert family; alert publication is distinct from a full execution strategy |
| [Smart Money Concepts — LuxAlgo](https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/) | Structural labels, blocks and related chart annotations; state/confirmation rules need source-specific review |
| [Nadaraya-Watson Envelope — LuxAlgo](https://www.tradingview.com/script/Iko0E2kL-Nadaraya-Watson-Envelope-LuxAlgo/) | Kernel regression envelope; endpoint/non-repainting versus repainting modes must be distinguished |
| [Nadaraya-Watson Smoothers — LuxAlgo](https://www.tradingview.com/script/amRCTgFw-Nadaraya-Watson-Smoothers-LuxAlgo/) | Kernel smoothing family; smoothing mode changes historical information usage |
| [Lorentzian Classification — jdehorty](https://www.tradingview.com/script/WhBzgfDu-Machine-Learning-Lorentzian-Classification/) | Approximate nearest-neighbour feature classification; name and ML branding do not establish an out-of-sample edge |
| [Adaptive SuperTrend — AlgoAlpha](https://www.tradingview.com/script/CLk71Qgy-Machine-Learning-Adaptive-SuperTrend-AlgoAlpha/) | Clusters volatility and adapts Supertrend; volatility clustering is different from directly learning returns |
| [Super Smoother — Shizaru](https://www.tradingview.com/script/SldE4p9a-Ehlers-Super-Smoother-by-Shizaru/) | Ehlers digital-filter implementation |
| [Ultimate Smoother — PineCodersTASC](https://www.tradingview.com/script/X67OSwqc-TASC-2024-04-The-Ultimate-Smoother/) | Publisher-associated implementation of Ehlers' 2024 smoother |

For the remaining discoveries, [TRADINGVIEW_PUBLICATIONS.md](TRADINGVIEW_PUBLICATIONS.md) preserves titles, URLs, topic associations, checked/unchecked access status and a short author-description excerpt. Most are listing-only records; they have not been individually certified or assigned a success rating.

## Applicability to gold, oil, DAX and Nasdaq 100

“Applicable” below means the inputs can support the calculation. It does **not** mean a profitable rule was established for the asset. Formula-based indicators are generally market-neutral computations; their parameter choices, spreads and data requirements are not automatically transferable.

| Method/data family | Gold | WTI oil | DAX | Nasdaq 100 |
|---|---|---|---|---|
| Price-only filters, oscillators, Ichimoku, channels | Broker OHLC can support calculation | Broker OHLC; roll discontinuities need identification | Broker OHLC with defined session | Broker OHLC with defined session |
| ATR/normalized volatility | Use price units and percent/ATR normalization | Nonpositive historical futures prices can invalidate log formulas | Session gaps and cash/futures difference | Opening gaps and extended-hours changes |
| Session/ORB/pivots | Define broker/NY/COMEX convention | Define broker/NYMEX convention | Distinguish Xetra, Eurex and broker day | Distinguish Nasdaq cash, CME and broker day |
| VWAP/volume profile/RVOL | CFD tick-volume version or separately sourced GC volume; label which | CFD tick volume or CL volume; not interchangeable | Cash index lacks a directly traded index volume; FDAX is separate | Cash index versus NQ/QQQ participation are distinct inputs |
| True delta/footprint/DOM | Appropriate GC trade/depth feed required | Appropriate CL trade/depth feed required | Appropriate FDAX-family feed required | Appropriate NQ-family feed required |
| Open interest/COT | Gold derivatives data and release timing | Oil derivatives data and release timing | Appropriate exchange positioning; do not assume a CFTC DAX series | Nasdaq derivatives positioning with correct report/contract mapping |
| Macro/volatility context | Real yields, dollar reference, GVZ or gold-futures options data | EIA, curve spreads, OVX or oil-futures options data | Euro rates and appropriate DAX volatility/constituent data | Rates, VXN, breadth, constituent/QQQ reference data |

Official instrument references: [COMEX Gold](https://www.cmegroup.com/markets/metals/precious/gold.contractSpecs.html), [NYMEX WTI Crude Oil](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html), [E-mini Nasdaq-100](https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.contractSpecs.html), and [DAX futures at Eurex](https://www.eurexgroup.com/ex-en/markets/idx/dax/DAX-Futures-34642). A futures analysis feed is a reference for the corresponding CFD, not an assertion of price identity. Match timestamps, contract rolls, basis and availability before joining them. In this project `QQQ.US` remains a reference feed, not a tradable signal symbol.

Official contextual sources include the [CFTC COT portal](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm), [EIA Weekly Petroleum Status Report](https://www.eia.gov/petroleum/supply/weekly/), [FRED 10-year real yield DFII10](https://fred.stlouisfed.org/series/DFII10), [Cboe GVZ](https://www.cboe.com/us/indices/dashboard/gvz/), [OVX](https://www.cboe.com/us/indices/dashboard/ovx/) and [VXN](https://www.cboe.com/us/indices/dashboard/vxn/). GVZ references GLD option-implied volatility; it is not spot-gold realized volatility. Likewise proxy volatility series are distinct from the actual CFD's realized range.

For historical study, record when data became public. COT observation dates, EIA report dates, daily macro timestamps and later revisions must not be treated as contemporaneously available at an earlier trading decision. No current value, release schedule or market forecast is asserted in this report.

## MT5 software path

[MetaQuotes' technical indicator reference](https://www.mql5.com/en/docs/indicators) exposes native handles for Ichimoku, AMA, FrAMA, VIDyA, ADX/Wilder ADX, ATR, moving averages, MACD/OsMA, DeMarker, stochastic, RSI, bands, SAR, Alligator and others. These are platform APIs, not the downloaded Pine/Python implementations. MQL5 handles and buffer positions require `CopyBuffer` and explicit closed-bar selection. Do not port MQL4's scalar-return examples as if the same call contract applied to MQL5.

For newer or unusual filters, accessible official code/articles include [Super_Smoother.mq5](https://www.mql5.com/en/code/22208) and the [2026 scalar Kalman implementation article](https://www.mql5.com/en/articles/24567). These are external primary references; this package does not claim to have compiled or tested them. For a port, compare a frozen source version against the target runtime using the same bars, initial state, smoothing, missing-data rules and output availability.

## Relation to existing ForexSAI evidence

The existing [gate/strategy registry](../../docs/KAPI_KAYIT_DEFTERI.md) was consulted before extending the search. It records prior leakage, execution and transferability failures, including broad ready-made framework testing. This atlas neither re-runs those tests nor overturns their conclusions. Discovering a new implementation or name is not evidence that an already rejected economic hypothesis now works.

A later experiment would need a small frozen selection of *mathematically distinct* methods, explicit data/availability contracts, independent chronological testing, realistic spread/slippage and one-position-at-a-time evaluation. If implemented, new scopes remain subject to the existing go-live gate. Such testing was not part of this source-catalogue request and is not listed as an unfinished promise here.

## What remains outside the claim

- No exhaustive export of all TradingView publications, private accounts, invite-only scripts or every language's indicator ecosystem.
- No globally deduplicated count of mathematical indicators: implementation counts and family-card counts are intentionally separate.
- No complete source extraction from the 496 TradingView publication records; locally downloaded Pine is the separate 210-file author-repository snapshot.
- No claim that every named library method runs, every script is non-repainting, or all selected source directories form standalone buildable packages.
- No target-market profitability, “best settings”, walk-forward scores or live deployment.

The completed result is a broad, reproducible source atlas with working explanations, original-language names, data distinctions and navigable code evidence. Its scope is explicit so future work can select an exact implementation rather than relying on indicator names or screenshots.
