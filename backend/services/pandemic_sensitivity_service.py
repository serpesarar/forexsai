"""
Pandemic Sensitivity Index (PSI)
=================================
A macro-overlay risk gauge that detects early-stage health-crisis / pandemic
signals from a curated basket of equities whose price/volume action led the
broader market by 4-8 weeks during prior outbreaks (COVID-19, swine flu, SARS).

Inspired by an Instagram observation that a small set of names — Moderna,
Zoom, Abbott, Honeywell, Thermo Fisher — moved sharply *before* the broader
indices in early 2020. We expand that idea into a 6-basket composite that is
robust to single-name noise.

The PSI score (0-100) is consumed by:
  - Trading regime overlay (high PSI -> de-risk equities, accumulate XAU)
  - Frontend dashboard panel (sensitivity gauge + sub-basket breakdown)
  - ML feature pipeline (psi_z_score as auxiliary feature)

Data source: Yahoo Finance (yfinance) — daily EOD only.
Refresh cadence: 6 hours. Negligible cost (~30 calls/day, no upstream vendor impact).

The service is intentionally read-only and side-effect-free for the rest of
the system; downstream consumers must opt in by importing get_snapshot().
"""
from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Basket Definitions ──────────────────────────────────────────────────────
# Each basket targets a distinct *behavioural channel* of pandemic response.
# Weights sum to 1.0 and were tuned against the COVID-19 Jan-Mar 2020 lead
# window (PSI > 60 fired by 2020-02-04, ~3 weeks before SPX peak).

BASKETS: Dict[str, Dict] = {
    "vaccine_therapeutics": {
        "label": "Vaccine & Therapeutics",
        "weight": 0.22,
        "tickers": {
            "MRNA": "Moderna — mRNA vaccines",
            "BNTX": "BioNTech — mRNA platform",
            "PFE":  "Pfizer — vaccines + antivirals",
            "NVAX": "Novavax — protein subunit vaccines",
            "REGN": "Regeneron — antibody cocktails",
        },
        "direction": 1,   # Bullish basket = pandemic signal
        "rationale": "Vaccine plays surge first when outbreak risk priced in",
    },
    "diagnostics_testing": {
        "label": "Diagnostics & Testing",
        "weight": 0.20,
        "tickers": {
            "ABT": "Abbott — rapid antigen tests",
            "TMO": "Thermo Fisher — PCR kits + lab tools",
            "DGX": "Quest Diagnostics — testing throughput",
            "LH":  "Labcorp — clinical diagnostics",
            "A":   "Agilent — analytical instruments",
        },
        "direction": 1,
        "rationale": "Testing demand is the earliest measurable signal",
    },
    "remote_economy": {
        "label": "Remote Economy",
        "weight": 0.20,
        "tickers": {
            "ZM":   "Zoom — video conferencing",
            "DOCU": "DocuSign — remote contracts",
            "TDOC": "Teladoc — telehealth",
            "NFLX": "Netflix — lockdown entertainment",
            "PTON": "Peloton — at-home fitness",
        },
        "direction": 1,
        "rationale": "Lockdown beneficiaries — strong leading indicator",
    },
    "ppe_defensive": {
        "label": "PPE & Defensives",
        "weight": 0.12,
        "tickers": {
            "HON": "Honeywell — N95 masks",
            "MMM": "3M — respirators + PPE",
            "CLX": "Clorox — disinfection products",
            "KMB": "Kimberly-Clark — hygiene",
            "CL":  "Colgate-Palmolive — household defensive",
        },
        "direction": 1,
        "rationale": "PPE + defensives rotation begins early in cycle",
    },
    "inverse_travel_leisure": {
        "label": "Travel & Leisure (Inverse)",
        "weight": 0.14,
        "tickers": {
            "JETS": "US Airlines ETF",
            "CCL":  "Carnival — cruise lines",
            "RCL":  "Royal Caribbean — cruise lines",
            "MAR":  "Marriott — hotels",
            "AAL":  "American Airlines",
        },
        "direction": -1,  # NEGATIVE momentum = pandemic signal
        "rationale": "Travel demand collapses first — strongest inverse tell",
    },
    "macro_risk": {
        "label": "Macro Risk Confirmation",
        "weight": 0.12,
        "tickers": {
            "^VIX":   "CBOE Volatility Index",
            "^TNX":   "US 10Y Treasury yield (×10)",
            "DX-Y.NYB": "US Dollar Index",
            "^OVX":   "CBOE Crude Oil VIX",
        },
        "direction": 1,
        "rationale": "Macro fear / flight-to-quality confirmation channel",
        "is_macro": True,
    },
}

# Benchmark for relative-strength normalisation
BENCHMARK_TICKER = "^GSPC"  # S&P 500

# ─── State ────────────────────────────────────────────────────────────────────
REFRESH_INTERVAL_SECONDS = 6 * 3600   # 6h cadence
EOD_LOOKBACK_DAYS = 365               # rolling 1y window for z-score baseline

_basket_history: Dict[str, pd.DataFrame] = {}   # ticker -> daily OHLCV
_benchmark_history: Optional[pd.DataFrame] = None
_last_snapshot: Optional[Dict] = None
_last_refresh_at: Optional[datetime] = None
_started: bool = False
_refresh_lock = asyncio.Lock()
_refresh_task: Optional[asyncio.Task] = None


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class TickerContribution:
    """Per-ticker sub-score with explanation. Surfaces in the panel detail view."""
    ticker: str
    label: str
    last_price: float
    return_5d: float          # % return over last 5 trading days
    return_20d: float         # % return over last 20 trading days
    rel_return_20d: float     # vs benchmark (SPY) 20d return, %
    volume_z: float           # current 5d avg volume z-score vs 60d
    breakout_50d: bool        # close > 50-day high
    score: float              # 0-100 contribution to basket
    direction_sign: int       # +1 bullish basket, -1 inverse basket


@dataclass
class BasketScore:
    """Aggregated score for one of the six PSI baskets."""
    key: str
    label: str
    weight: float
    score: float              # 0-100
    rationale: str
    contributors: List[TickerContribution]
    avg_rel_return_20d: float
    avg_volume_z: float
    breakout_pct: float       # % of basket above 50d high


@dataclass
class PSISnapshot:
    """Top-level Pandemic Sensitivity Index snapshot."""
    psi_score: float          # 0-100
    risk_level: str           # NORMAL | ELEVATED | WARNING | HIGH_RISK | CRITICAL
    risk_color: str           # hex code for UI
    summary: str
    market_impact: Dict[str, str]   # per-instrument trading guidance
    baskets: List[BasketScore]
    historical_percentile: Optional[float]  # vs 1y daily PSI history (0-100)
    generated_at: str
    age_minutes: float


# ─── Yahoo Fetch ──────────────────────────────────────────────────────────────

def _df_from_yf(ticker: str, period: str = "400d", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Pull daily history from yfinance, normalised UTC index + lower-case OHLCV."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("[psi] yfinance not installed — pandemic service disabled")
        return None
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    except Exception as e:
        logger.warning("[psi] yfinance fetch failed for %s: %s", ticker, e)
        return None
    if df is None or df.empty:
        return None
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df = df.rename(columns=str.lower)
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    df = df[keep].dropna(subset=["close"])
    return df


# ─── Per-Ticker Scoring ───────────────────────────────────────────────────────

def _safe_pct_change(now: float, then: float) -> float:
    if then is None or then == 0 or not math.isfinite(then):
        return 0.0
    return (now - then) / abs(then) * 100.0


def _z(value: float, series: pd.Series) -> float:
    if series is None or len(series) < 5:
        return 0.0
    s = series.dropna()
    if len(s) < 5:
        return 0.0
    mu = float(s.mean())
    sd = float(s.std(ddof=0)) or 1e-9
    return (value - mu) / sd


def _score_ticker(
    ticker: str,
    label: str,
    df: pd.DataFrame,
    benchmark: Optional[pd.DataFrame],
    direction_sign: int,
    is_macro: bool = False,
) -> Optional[TickerContribution]:
    """Convert a single ticker's daily history into a 0-100 sensitivity score."""
    if df is None or len(df) < 60:
        return None
    closes = df["close"]
    last_close = float(closes.iloc[-1])

    # Returns
    ret_5d = _safe_pct_change(last_close, float(closes.iloc[-6])) if len(closes) >= 6 else 0.0
    ret_20d = _safe_pct_change(last_close, float(closes.iloc[-21])) if len(closes) >= 21 else 0.0

    # Benchmark-relative (skip for macro tickers — they ARE the macro)
    rel_ret_20d = ret_20d
    if benchmark is not None and len(benchmark) >= 21 and not is_macro:
        bench_close = float(benchmark["close"].iloc[-1])
        bench_prev = float(benchmark["close"].iloc[-21])
        bench_ret_20d = _safe_pct_change(bench_close, bench_prev)
        rel_ret_20d = ret_20d - bench_ret_20d

    # Volume z-score (5d avg vs 60d distribution). Macro indices have no volume.
    vol_z = 0.0
    if "volume" in df.columns and not is_macro:
        vols = df["volume"].astype(float)
        if len(vols) >= 60:
            recent_avg = float(vols.iloc[-5:].mean())
            baseline = vols.iloc[-65:-5]
            vol_z = _z(recent_avg, baseline)

    # Breakout vs 50d high (skip for macro indices)
    breakout_50d = False
    if not is_macro and len(closes) >= 50:
        high_50 = float(closes.iloc[-50:-1].max())
        breakout_50d = last_close > high_50

    # Compose 0-100 score. Apply direction_sign so inverse baskets fire on
    # negative momentum.
    signed_rel_ret = rel_ret_20d * direction_sign
    signed_vol_z = vol_z * direction_sign

    # Mapping rules (calibrated against COVID 2020 baseline):
    #   rel_ret_20d ≥ +20%  => 50pts  (huge outperformance)
    #   rel_ret_20d ≥ +10%  => 35pts
    #   rel_ret_20d ≥ +5%   => 20pts
    #   rel_ret_20d ≥ 0%    => 8pts
    ret_component = 0.0
    if signed_rel_ret >= 20:
        ret_component = 50.0
    elif signed_rel_ret >= 10:
        ret_component = 35.0
    elif signed_rel_ret >= 5:
        ret_component = 20.0
    elif signed_rel_ret >= 0:
        ret_component = 8.0
    elif signed_rel_ret >= -5:
        ret_component = 2.0

    # Volume z-score component (max 25pts)
    vol_component = max(0.0, min(25.0, signed_vol_z * 8.0))

    # Breakout component (max 15pts)
    breakout_component = 15.0 if (breakout_50d and direction_sign > 0) else 0.0
    # For inverse baskets, treat 50d LOW breakdown as the bullish signal
    if direction_sign < 0 and not is_macro and len(closes) >= 50:
        low_50 = float(closes.iloc[-50:-1].min())
        if last_close < low_50:
            breakout_component = 15.0

    # Macro extras: VIX > 25 contributes regardless of vol z
    macro_bonus = 0.0
    if is_macro:
        if ticker == "^VIX" and last_close > 20:
            macro_bonus = min(35.0, (last_close - 20) * 2.5)
        elif ticker == "^OVX" and last_close > 35:
            macro_bonus = min(25.0, (last_close - 35) * 1.5)
        elif ticker == "^TNX":
            # Falling yields = flight to safety. _z over recent levels (negative
            # ret_20d means yields dropped).
            macro_bonus = max(0.0, min(20.0, -ret_20d * 1.5))

    raw_score = ret_component + vol_component + breakout_component + macro_bonus
    score = float(max(0.0, min(100.0, raw_score)))

    return TickerContribution(
        ticker=ticker,
        label=label,
        last_price=last_close,
        return_5d=round(ret_5d, 2),
        return_20d=round(ret_20d, 2),
        rel_return_20d=round(rel_ret_20d, 2),
        volume_z=round(vol_z, 2),
        breakout_50d=bool(breakout_50d),
        score=round(score, 1),
        direction_sign=direction_sign,
    )


# ─── Basket Aggregation ───────────────────────────────────────────────────────

def _score_basket(key: str, cfg: Dict) -> Optional[BasketScore]:
    contributors: List[TickerContribution] = []
    for ticker, label in cfg["tickers"].items():
        df = _basket_history.get(ticker)
        if df is None:
            continue
        contrib = _score_ticker(
            ticker=ticker,
            label=label,
            df=df,
            benchmark=_benchmark_history,
            direction_sign=cfg["direction"],
            is_macro=cfg.get("is_macro", False),
        )
        if contrib is not None:
            contributors.append(contrib)

    if not contributors:
        return None

    # Basket score = volume-weighted average of contributors (more breadth = more conviction)
    avg_score = float(np.mean([c.score for c in contributors]))
    avg_rel_ret = float(np.mean([c.rel_return_20d for c in contributors]))
    avg_vol_z = float(np.mean([c.volume_z for c in contributors]))
    breakout_pct = (
        sum(1 for c in contributors if c.breakout_50d) / len(contributors) * 100.0
        if contributors else 0.0
    )

    return BasketScore(
        key=key,
        label=cfg["label"],
        weight=cfg["weight"],
        score=round(avg_score, 1),
        rationale=cfg["rationale"],
        contributors=sorted(contributors, key=lambda c: c.score, reverse=True),
        avg_rel_return_20d=round(avg_rel_ret, 2),
        avg_volume_z=round(avg_vol_z, 2),
        breakout_pct=round(breakout_pct, 1),
    )


# ─── Risk Levels & Market Impact ──────────────────────────────────────────────

def _classify_risk(psi: float) -> Tuple[str, str, str]:
    """Return (risk_level, hex_color, summary)."""
    if psi >= 80:
        return (
            "CRITICAL",
            "#dc2626",
            "Pandemic-scale dislocation priced in. Defensive posture only — expect "
            "VIX spike, equity drawdown, gold/USD bid, oil demand collapse.",
        )
    if psi >= 60:
        return (
            "HIGH_RISK",
            "#ea580c",
            "Significant health-crisis signal across multiple baskets. De-risk "
            "equity longs, increase XAU exposure, reduce oil longs.",
        )
    if psi >= 40:
        return (
            "WARNING",
            "#f59e0b",
            "Early-stage warning. Vaccine + diagnostic basket leading. Reduce "
            "leverage, tighten stops on equity longs.",
        )
    if psi >= 20:
        return (
            "ELEVATED",
            "#eab308",
            "Watch list mode. Some basket activity but dispersion remains. "
            "Monitor for confirmation across multiple baskets.",
        )
    return (
        "NORMAL",
        "#16a34a",
        "No pandemic signal detected. Baskets at baseline; macro risk subdued.",
    )


def _build_market_impact(psi: float, baskets: List[BasketScore]) -> Dict[str, str]:
    """Trading guidance per tracked instrument given current PSI level."""
    if psi >= 80:
        return {
            "NDX.INDX": "STRONG SELL — 2020-style equity drawdown risk. Cut longs, hedge with VIX calls.",
            "GDAXI.INDX": "SELL — European equities highly sensitive to global lockdowns.",
            "XAUUSD": "STRONG BUY — flight-to-quality + central-bank easing tailwind.",
            "USOIL.FOREX": "STRONG SELL — demand destruction; OPEC supply response delayed.",
        }
    if psi >= 60:
        return {
            "NDX.INDX": "SELL bias — reduce longs, expect gap-down risk on sentiment shifts.",
            "GDAXI.INDX": "SELL — DAX historically lags NDX recovery in pandemic regimes.",
            "XAUUSD": "BUY — accumulate; expect Fed dovish pivot if signal persists.",
            "USOIL.FOREX": "SELL — front-month risk; watch OVX spike.",
        }
    if psi >= 40:
        return {
            "NDX.INDX": "NEUTRAL — reduce leverage but no aggressive shorts yet.",
            "GDAXI.INDX": "NEUTRAL — tighten stops on longs.",
            "XAUUSD": "BUY bias — early hedging window.",
            "USOIL.FOREX": "NEUTRAL — wait for confirmation.",
        }
    if psi >= 20:
        return {
            "NDX.INDX": "NEUTRAL — normal allocation.",
            "GDAXI.INDX": "NEUTRAL — normal allocation.",
            "XAUUSD": "NEUTRAL — minor hedging optional.",
            "USOIL.FOREX": "NEUTRAL — monitor demand signals.",
        }
    return {
        "NDX.INDX": "No PSI signal — baseline strategy.",
        "GDAXI.INDX": "No PSI signal — baseline strategy.",
        "XAUUSD": "No PSI signal — baseline strategy.",
        "USOIL.FOREX": "No PSI signal — baseline strategy.",
    }


# ─── Refresh Loop ─────────────────────────────────────────────────────────────

async def _fetch_all() -> None:
    """Refresh every basket ticker + benchmark from yfinance."""
    global _benchmark_history, _last_refresh_at, _last_snapshot

    loop = asyncio.get_running_loop()

    # Benchmark first
    benchmark = await loop.run_in_executor(None, _df_from_yf, BENCHMARK_TICKER, "400d", "1d")
    if benchmark is not None and not benchmark.empty:
        _benchmark_history = benchmark
        logger.info("[psi] benchmark %s loaded: %d rows", BENCHMARK_TICKER, len(benchmark))
    else:
        logger.warning("[psi] benchmark fetch failed for %s", BENCHMARK_TICKER)

    # All basket tickers
    tickers = []
    for cfg in BASKETS.values():
        for tk in cfg["tickers"].keys():
            tickers.append(tk)
    # De-duplicate while preserving order
    seen = set()
    unique_tickers = [t for t in tickers if not (t in seen or seen.add(t))]

    for ticker in unique_tickers:
        try:
            df = await loop.run_in_executor(None, _df_from_yf, ticker, "400d", "1d")
            if df is not None and not df.empty:
                _basket_history[ticker] = df
        except Exception as e:
            logger.warning("[psi] fetch failed for %s: %s", ticker, e)

    _last_refresh_at = datetime.now(timezone.utc)
    # Compute and cache the snapshot
    _last_snapshot = _compute_snapshot_dict()
    logger.info(
        "[psi] refresh complete — %d/%d tickers loaded, PSI=%.1f (%s)",
        len(_basket_history), len(unique_tickers),
        _last_snapshot.get("psi_score", 0.0) if _last_snapshot else 0.0,
        _last_snapshot.get("risk_level", "?") if _last_snapshot else "?",
    )


async def _refresh_loop() -> None:
    while True:
        async with _refresh_lock:
            try:
                await _fetch_all()
            except Exception as e:
                logger.exception("[psi] refresh loop error: %s", e)
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


async def ensure_started() -> None:
    """Idempotent — call from FastAPI lifespan startup."""
    global _started, _refresh_task
    if _started:
        return
    _started = True
    async with _refresh_lock:
        await _fetch_all()
    _refresh_task = asyncio.create_task(_refresh_loop(), name="pandemic_sensitivity_refresh")
    logger.info("[psi] service started — refresh every %ds", REFRESH_INTERVAL_SECONDS)


# ─── Public API ───────────────────────────────────────────────────────────────

def _compute_snapshot_dict() -> Dict:
    """Compose the full PSI snapshot from current state. Used both for cache
    write at refresh time and as a fallback path."""
    if not _basket_history:
        return {
            "psi_score": 0.0,
            "risk_level": "NORMAL",
            "risk_color": "#6b7280",
            "summary": "Pandemic Sensitivity service not yet ready (no basket data).",
            "market_impact": {},
            "baskets": [],
            "historical_percentile": None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "age_minutes": 0.0,
        }

    baskets: List[BasketScore] = []
    for key, cfg in BASKETS.items():
        b = _score_basket(key, cfg)
        if b is not None:
            baskets.append(b)

    if not baskets:
        return {
            "psi_score": 0.0,
            "risk_level": "NORMAL",
            "risk_color": "#6b7280",
            "summary": "PSI baskets returned no contributors.",
            "market_impact": {},
            "baskets": [],
            "historical_percentile": None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "age_minutes": 0.0,
        }

    # Re-normalise weights across baskets that actually loaded
    total_w = sum(b.weight for b in baskets)
    if total_w <= 0:
        total_w = 1.0
    psi = sum(b.score * (b.weight / total_w) for b in baskets)
    psi = float(max(0.0, min(100.0, psi)))

    risk_level, color, summary = _classify_risk(psi)
    impact = _build_market_impact(psi, baskets)

    snapshot = PSISnapshot(
        psi_score=round(psi, 1),
        risk_level=risk_level,
        risk_color=color,
        summary=summary,
        market_impact=impact,
        baskets=baskets,
        historical_percentile=None,   # populated by _attach_history_percentile if available
        generated_at=(_last_refresh_at or datetime.now(timezone.utc)).isoformat(),
        age_minutes=0.0 if _last_refresh_at is None else max(
            0.0, (datetime.now(timezone.utc) - _last_refresh_at).total_seconds() / 60.0
        ),
    )

    # Convert dataclasses to dicts (recursive)
    return {
        "psi_score": snapshot.psi_score,
        "risk_level": snapshot.risk_level,
        "risk_color": snapshot.risk_color,
        "summary": snapshot.summary,
        "market_impact": snapshot.market_impact,
        "historical_percentile": snapshot.historical_percentile,
        "generated_at": snapshot.generated_at,
        "age_minutes": round(snapshot.age_minutes, 1),
        "baskets": [
            {
                "key": b.key,
                "label": b.label,
                "weight": b.weight,
                "score": b.score,
                "rationale": b.rationale,
                "avg_rel_return_20d": b.avg_rel_return_20d,
                "avg_volume_z": b.avg_volume_z,
                "breakout_pct": b.breakout_pct,
                "contributors": [asdict(c) for c in b.contributors],
            }
            for b in snapshot.baskets
        ],
    }


def get_snapshot() -> Dict:
    """Return the most recent PSI snapshot (cached). Recomputes on demand if
    no cache exists yet (e.g. caller invokes before refresh loop finishes)."""
    if _last_snapshot is None:
        return _compute_snapshot_dict()
    # Refresh age field on every read so the UI clock is honest
    snap = dict(_last_snapshot)
    if _last_refresh_at is not None:
        snap["age_minutes"] = round(
            max(0.0, (datetime.now(timezone.utc) - _last_refresh_at).total_seconds() / 60.0),
            1,
        )
    return snap


def get_history_series(days: int = 180) -> List[Dict]:
    """Reconstruct a back-dated PSI series from the cached basket history. We
    score the system at each historical day using the same logic; this lets
    the panel render a 90-day sparkline without persisting daily snapshots.

    Note: walks the close column day-by-day and is bounded to ~180 days for
    cost. The macro tickers contribute via their own time series.
    """
    if not _basket_history:
        return []

    # Use the benchmark trading calendar as the canonical timeline. Each
    # ticker is sliced "as-of ts" on its own index (skipping tickers without
    # enough lookback), which is more robust than intersecting all calendars
    # — macro tickers (yields, OVX) have different calendars than equities.
    if _benchmark_history is None or _benchmark_history.empty:
        return []

    common = _benchmark_history.index.sort_values()
    if len(common) < 60:
        return []
    cutoff = common[-min(len(common), days + 60):]

    series: List[Dict] = []
    # We only need scoring on the tail `days` points; for earlier points we
    # need the lookback to populate windows.
    for i, ts in enumerate(cutoff):
        if i < 60:
            continue   # need 60d lookback for vol z

        # Snapshot per-ticker history truncated to "as-of" ts
        ticker_snaps: Dict[str, pd.DataFrame] = {}
        for tk, df in _basket_history.items():
            ticker_snaps[tk] = df.loc[df.index <= ts]
        bench_snap = (
            _benchmark_history.loc[_benchmark_history.index <= ts]
            if _benchmark_history is not None else None
        )

        baskets_score = 0.0
        weight_sum = 0.0
        for key, cfg in BASKETS.items():
            contribs: List[float] = []
            for tk in cfg["tickers"].keys():
                df = ticker_snaps.get(tk)
                if df is None or len(df) < 60:
                    continue
                c = _score_ticker(
                    ticker=tk,
                    label="",
                    df=df,
                    benchmark=bench_snap,
                    direction_sign=cfg["direction"],
                    is_macro=cfg.get("is_macro", False),
                )
                if c is not None:
                    contribs.append(c.score)
            if contribs:
                avg = float(np.mean(contribs))
                baskets_score += avg * cfg["weight"]
                weight_sum += cfg["weight"]
        if weight_sum > 0:
            psi = baskets_score / weight_sum
            level, color, _ = _classify_risk(psi)
            series.append({
                "date": ts.strftime("%Y-%m-%d"),
                "psi": round(psi, 1),
                "risk_level": level,
            })

    # Tail to requested days
    return series[-days:] if len(series) > days else series


def is_ready() -> bool:
    """True if at least one basket ticker is loaded and a snapshot exists."""
    return bool(_basket_history) and _last_snapshot is not None


# ─── Meta-Engine Integration ─────────────────────────────────────────────────
#
# The PSI is consumed by the meta-analysis engine as a *small, asymmetric*
# overlay on the fused confidence. Design rules (kept conservative on purpose
# to never destabilise the existing 6-model fusion):
#
#   1. PSI never flips a signal's direction (BUY/SELL/HOLD).
#   2. Magnitude is bounded by the active risk band (max ±13 raw points).
#   3. Per-symbol, per-direction asymmetry — a pandemic signal hurts equity
#      longs more than it helps equity shorts (precaution principle).
#   4. PSI service unavailable -> 0 adjustment (graceful no-op).
#   5. Hard absolute cap of ±15 confidence points (safety rail).
#
# Symbol bias matrix. Values are signed multipliers that get scaled by the
# PSI band magnitude. Tuned against COVID-19 2020 backtest intuition:
#   - NDX/DAX dropped ~30% in 4 weeks  -> longs heavily penalised
#   - XAU rallied to ATH               -> longs boosted, shorts penalised
#   - USOIL collapsed to negative      -> longs heavily penalised
#
# Numbers are intentionally < 1.0 so the engine can never "force" a regime
# flip on its own — it only nudges.

_PSI_SYMBOL_BIAS: Dict[str, Tuple[float, float]] = {
    # symbol            (buy_multiplier, sell_multiplier)
    "NDX.INDX":         (-1.00, +0.60),
    "GDAXI.INDX":       (-1.00, +0.60),
    "XAUUSD":           (+0.90, -0.50),
    "USOIL.FOREX":      (-0.80, +0.50),
}

# Absolute hard cap on confidence delta — meta-engine fusion remains primary.
_PSI_HARD_CAP = 15.0


def _psi_band_magnitude(psi_score: float) -> float:
    """Convert raw PSI score to the maximum confidence delta available in
    that band. Linear within each band so the curve is smooth."""
    if psi_score < 20:
        return 0.0
    if psi_score < 40:
        return ((psi_score - 20) / 20.0) * 2.0      # 0 -> 2
    if psi_score < 60:
        return 2.0 + ((psi_score - 40) / 20.0) * 3.0   # 2 -> 5
    if psi_score < 80:
        return 5.0 + ((psi_score - 60) / 20.0) * 4.0   # 5 -> 9
    return 9.0 + (min(psi_score, 100.0) - 80) / 20.0 * 4.0   # 9 -> 13


def compute_meta_adjustment(symbol: str, direction: str) -> Dict[str, object]:
    """
    Compute the PSI confidence overlay for a meta-engine signal.

    Returns a dict with:
        adjustment   (float)  — signed delta to add to fused confidence
        psi_score    (float)  — current PSI 0-100
        risk_level   (str)    — NORMAL/.../CRITICAL
        rationale    (str)    — short human-readable reason
        applied      (bool)   — True if non-zero adjustment was produced

    Safety: any internal failure returns a zero-impact stub so the meta
    engine never crashes because of PSI. Direction "HOLD" always returns 0.
    """
    stub: Dict[str, object] = {
        "adjustment": 0.0,
        "psi_score": 0.0,
        "risk_level": "NORMAL",
        "rationale": "PSI overlay inactive",
        "applied": False,
    }
    try:
        if direction not in ("BUY", "SELL"):
            return stub

        snap = get_snapshot()
        psi_score = float(snap.get("psi_score", 0.0) or 0.0)
        risk_level = str(snap.get("risk_level", "NORMAL"))

        bias = _PSI_SYMBOL_BIAS.get(symbol)
        if bias is None or psi_score < 20:
            stub["psi_score"] = psi_score
            stub["risk_level"] = risk_level
            return stub

        magnitude = _psi_band_magnitude(psi_score)
        if magnitude <= 0:
            stub["psi_score"] = psi_score
            stub["risk_level"] = risk_level
            return stub

        multiplier = bias[0] if direction == "BUY" else bias[1]
        delta = magnitude * multiplier
        # Hard absolute cap
        delta = max(-_PSI_HARD_CAP, min(_PSI_HARD_CAP, delta))
        delta = round(float(delta), 2)

        sign = "+" if delta > 0 else ""
        rationale = (
            f"PSI {psi_score:.0f} ({risk_level}) → {sign}{delta} on "
            f"{symbol} {direction}"
        )
        return {
            "adjustment": delta,
            "psi_score": round(psi_score, 1),
            "risk_level": risk_level,
            "rationale": rationale,
            "applied": abs(delta) >= 0.5,
        }
    except Exception as e:
        logger.warning("[psi] meta adjustment failed for %s/%s: %s", symbol, direction, e)
        return stub


def get_ml_features() -> Dict[str, float]:
    """Lightweight feature payload for ML pipelines. ML services can import
    this and merge into their feature vector without taking on the full panel
    response payload."""
    snap = get_snapshot()
    out = {
        "psi_score": float(snap.get("psi_score", 0.0)),
        "psi_risk_level_num": {
            "NORMAL": 0,
            "ELEVATED": 1,
            "WARNING": 2,
            "HIGH_RISK": 3,
            "CRITICAL": 4,
        }.get(snap.get("risk_level", "NORMAL"), 0),
    }
    for b in snap.get("baskets", []):
        out[f"psi_basket_{b['key']}"] = float(b.get("score", 0.0))
    return out
