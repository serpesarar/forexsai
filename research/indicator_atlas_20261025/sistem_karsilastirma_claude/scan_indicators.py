"""Grep production code for TradingView-indicator signatures. Output JSON: indicator -> {component: [file:line,...]}."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
COMPONENTS = {
    "backend": [ROOT / "backend/services", ROOT / "backend/routers", ROOT / "backend/main.py", ROOT / "backend/ml"],
    "bot": [ROOT / "yeni deneme"],
    "decider": [ROOT / "claude_decider"],
}
SKIP = re.compile(r"(^test_|/tests?/|_test\.py$|backup|\.bak|sl_forensics|sl_indicator_analysis|discrimination|forensics|post_mortem|indicator_event_scan|batch_eval|model_compare|baseline_compare|analyze_missed|exit_compare|replay_report|integrity_audit|backfill)")

I = re.IGNORECASE
P = {
    # moving averages
    "SMA": r"\bsma\b|rolling\([^)]*\)\.mean\(|simple moving average|\bsma_?\d+",
    "EMA": r"\bema_?\d*\b|ewm\(span|exponential moving average",
    "WMA": r"\bwma\b|weighted moving average",
    "Hull MA (HMA)": r"\bhma\b|hull",
    "DEMA": r"\bdema\b|double exponential",
    "TEMA / Triple EMA": r"\btema\b|triple ema|triple exponential",
    "ALMA": r"\balma\b|arnaud legoux",
    "KAMA": r"\bkama\b|kaufman",
    "McGinley Dynamic": r"mcginley",
    "VWMA": r"\bvwma\b",
    "LSMA / Linear Regression": r"linreg|linear.?regression|polyfit|lsma|least.?squares|regression_channel|regression channel",
    "Smoothed MA / RMA (Wilder)": r"\brma\b|\bsmma\b|wilder|alpha=1\s*/|com=\w+\s*-\s*1",
    "MA Cross / MA Ribbon": r"golden.?cross|death.?cross|ma.?cross|ema.?cross|ribbon",
    "Ichimoku Cloud": r"ichimoku|tenkan|kijun|senkou|kumo|chikou",
    "Williams Alligator": r"alligator|\bjaw\b|\bteeth\b|\blips\b",
    # oscillators / momentum
    "RSI": r"\brsi\b|rsi_?\d+|relative strength index",
    "Stochastic": r"stoch(?!astic_rsi|rsi)|%k|\bstoch_k\b",
    "Stochastic RSI": r"stoch_?rsi|stochrsi|stochastic rsi",
    "MACD": r"\bmacd",
    "PPO": r"\bppo\b|percentage price osc",
    "CCI": r"\bcci\b|commodity channel",
    "Williams %R": r"williams|\bwpr\b|willr|\bwr_?\d+",
    "Momentum": r"\bmomentum_?\d*\b|\bmom_?\d*\b",
    "Rate of Change (ROC)": r"\broc\b|roc_?\d+|rate of change|pct_change\(",
    "Awesome Oscillator": r"awesome|\bao\b",
    "CMO": r"\bcmo\b|chande momentum",
    "TSI (True Strength)": r"\btsi\b|true strength",
    "TRIX": r"\btrix\b",
    "Ultimate Oscillator": r"ultimate.?osc|\buo\b",
    "KST": r"\bkst\b|know sure",
    "Coppock": r"coppock",
    "DPO": r"\bdpo\b|detrended",
    "Fisher Transform": r"fisher",
    "Connors RSI": r"connors|crsi",
    "SMI / SMI Ergodic": r"stochastic momentum index|\bsmi\b|ergodic",
    "Relative Vigor Index": r"vigor|\brvi\b",
    "Balance of Power": r"balance.?of.?power|\bbop\b",
    "Bull Bear Power": r"bull.?bear.?power|elder.?ray",
    "RCI": r"\brci\b|rank correlation",
    "Pring Special K / PMO": r"special.?k|\bpmo\b|price momentum osc",
    "RSI divergence": r"diverg",
    # trend strength / direction
    "ADX / DMI": r"\badx\b|adx_?\d+|\bdmi\b|plus_di|minus_di|\+di|directional",
    "Aroon": r"aroon",
    "Parabolic SAR": r"parabolic|psar|\bsar\b",
    "Supertrend": r"supertrend|super_trend",
    "Vortex": r"vortex",
    "Choppiness Index": r"chop(?:piness)?(?:_index)?\b|\bchop\b",
    "Trend Strength Index": r"trend.?strength.?index",
    "Chop Zone": r"chop.?zone",
    "Chande Kroll / Chandelier / Volatility Stop": r"chandelier|kroll|volatility.?stop",
    "Mass Index": r"mass.?index",
    # volatility / bands / channels
    "ATR": r"\batr\b|atr_?\d+|average true range|true_range|\btr\b",
    "ADR (Average Daily Range)": r"\badr\b|adr_?\d+|average daily range",
    "Bollinger Bands": r"bollinger|\bbb_|bb_upper|bb_lower|\bbbands",
    "Bollinger %b": r"%b\b|pct_b|percent_b|bb_pct|bb_position|bbp",
    "Bollinger BandWidth": r"bandwidth|bb_width|bbw",
    "BBTrend": r"bbtrend",
    "Keltner Channels": r"keltner|\bkc_",
    "Donchian Channels": r"donchian|rolling\([^)]*\)\.max\(\)",
    "Envelope": r"envelope",
    "Historical Volatility": r"historical.?vol|realized.?vol|\.std\(\)|stdev|returns?_std",
    "Relative Volatility Index": r"relative.?volatility",
    "Ulcer Index": r"ulcer",
    "TTM / Squeeze": r"squeeze|\bsqz",
    # volume
    "Volume (raw / relative)": r"rel(?:ative)?_?vol|volume_ratio|vol_ratio|vol_ma|volume_ma|volume spike|vol_spike|rvol",
    "OBV": r"\bobv\b|on.?balance",
    "MFI": r"\bmfi\b|money flow index|money_flow",
    "CMF / Chaikin": r"\bcmf\b|chaikin",
    "ADL (Accum/Dist)": r"accumulation.?distribution|\badl\b|accdist",
    "PVT": r"\bpvt\b|price volume trend",
    "Elder Force Index": r"force.?index|\befi\b",
    "Ease of Movement": r"ease.?of.?movement|\beom\b",
    "Klinger": r"klinger",
    "NVI / PVI": r"\bnvi\b|\bpvi\b|negative volume index|positive volume index",
    "Net Volume / Up-Down Volume": r"net.?volume|up.?down.?volume",
    "Volume Delta / CVD": r"\bcvd\b|volume.?delta|cumulative.?delta|delta_vol",
    "VWAP": r"vwap",
    "TWAP": r"twap",
    "Volume Profile (POC/VAH/VAL)": r"\bpoc\b|value.?area|\bvah\b|\bval\b|volume.?profile|market.?profile",
    "TPO": r"\btpo\b|time.?price.?opportunity",
    # levels / structure
    "Pivot Points Standard": r"pivot.?points?|classic.?pivot|camarilla|woodie|pivot_[rs]\d|\br1\b|\bs1\b",
    "Pivot High/Low / Fractal": r"pivothigh|pivotlow|swing.?high|swing.?low|fractal",
    "ZigZag": r"zig.?zag",
    "Fibonacci (auto fib)": r"fibonacci|\bfib\b|fib_",
    "Auto trendlines": r"trend.?line",
    "Auto key levels / S-R": r"support|resistance|\bsr_",
    "Opening Range (ORB)": r"opening.?range|\borb\b",
    "Trading Sessions": r"session",
    "Seasonality": r"seasonal",
    "Correlation Coefficient": r"\.corr\(|correlation",
    "Linear regression channel / std channel": r"channel",
    # patterns
    "Chart patterns (H&S, double top...)": r"head.?and.?shoulders|double.?top|double.?bottom|triangle|wedge|flag|pennant|cup.?and.?handle",
    "Harmonic patterns": r"harmonic|gartley|butterfly|\bbat\b|crab|cypher|shark",
    "Candlestick patterns": r"engulf|hammer|doji|pin.?bar|morning.?star|evening.?star|harami|shooting.?star|marubozu",
    "Elliott wave": r"elliott",
    "Gaps": r"\bgap\b|gap_",
    # SMC / ICT (community)
    "SMC: BOS / CHoCH": r"\bbos\b|choch|break.?of.?structure|change.?of.?character",
    "SMC: Order Block": r"order.?block|\bob_|orderblock",
    "SMC: Fair Value Gap": r"\bfvg\b|fair.?value.?gap|imbalance",
    "SMC: Liquidity sweep": r"liquidity|sweep|stop.?hunt",
    "Heikin Ashi": r"heikin|heiken",
    "Renko / Kagi / P&F": r"renko|kagi|point.?and.?figure",
    # community famous
    "WaveTrend": r"wavetrend|wave_trend",
    "QQE": r"\bqqe",
    "HalfTrend": r"halftrend|half_trend",
    "UT Bot": r"ut.?bot",
    "SSL Channel": r"\bssl\b",
    "Range Filter": r"range.?filter",
    "Nadaraya-Watson / kernel regression": r"nadaraya|kernel.?regress",
    "Lorentzian / kNN classification": r"lorentzian|\bknn\b|k-nn|nearest.?neighbo",
    "Schaff Trend Cycle": r"schaff|\bstc\b",
    "Ehlers filters (MESA, SuperSmoother)": r"ehlers|mesa|super.?smoother|roofing",
    "Kalman filter": r"kalman",
    "CM Williams VIX Fix": r"vix.?fix",
    "Wyckoff": r"wyckoff",
    "Market cipher / VuManChu": r"cipher|vumanchu",
    # macro/context (TradingView data indicators)
    "COT report": r"\bcot\b|commitments? of traders",
    "VIX (external)": r"\bvix\b",
    "DXY (external)": r"\bdxy\b",
    "US10Y (external)": r"us10y|\btnx\b|10y",
    "Open Interest": r"open.?interest",
    "Technical Ratings": r"technical.?rating",
}

def iter_files():
    for comp, paths in COMPONENTS.items():
        for p in paths:
            if not p.exists():
                continue
            files = [p] if p.is_file() else sorted(p.rglob("*.py"))
            for f in files:
                rel = str(f.relative_to(ROOT))
                if SKIP.search(rel) or "__pycache__" in rel:
                    continue
                yield comp, rel, f

res = {k: {c: [] for c in COMPONENTS} for k in P}
comp_re = {k: re.compile(v, I) for k, v in P.items()}
for comp, rel, f in iter_files():
    try:
        lines = f.read_text(errors="ignore").splitlines()
    except Exception:
        continue
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s:
            continue
        for k, rx in comp_re.items():
            if rx.search(s):
                res[k][comp].append(f"{rel}:{i}")
summary = {}
for k, d in res.items():
    summary[k] = {c: {"hits": len(v), "files": sorted({x.rsplit(':', 1)[0] for x in v})} for c, v in d.items()}
json.dump({"summary": summary, "hits": res}, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
for k, d in summary.items():
    print(f"{k:45s} " + "  ".join(f"{c}:{d[c]['hits']:>5}/{len(d[c]['files']):>3}f" for c in COMPONENTS))
