"""
Meta-Intelligence Engine
Combines signals from all 6 models (ML, PULSE 1-2-3, EMEL, SMC)
into a single high-confidence meta-signal with risk parameters.

Architecture:
  1. Signal Collector  → Gather live model outputs
  2. Combination Miner → Historical best combos (symbol × regime)
  3. Technical Validator → 8 condition checks (EMA, RSI, MACD, ADX, Vol, BB, ATR, EMA200)
  4. Confidence Fusion  → Weighted average + technical boost
  5. Risk Calculator    → Entry / TP1 / TP2 / SL
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from itertools import combinations
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# ENUMS & DATA CLASSES
# ═══════════════════════════════════════════════════════════

SUPPORTED_SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"]

MODEL_IDS = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]

# Default weights per model (used when no historical data exists)
DEFAULT_MODEL_WEIGHTS: Dict[str, float] = {
    "ml":     0.25,
    "pulse1": 0.15,
    "pulse2": 0.15,
    "pulse3": 0.15,
    "emel":   0.20,
    "smc":    0.10,
}

# Regime-specific weight multipliers
REGIME_WEIGHT_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "STRONG_TREND_UP": {
        "ml": 1.2, "pulse1": 0.8, "pulse2": 1.1, "pulse3": 1.3, "emel": 1.2, "smc": 0.7,
    },
    "STRONG_TREND_DOWN": {
        "ml": 1.2, "pulse1": 0.8, "pulse2": 1.1, "pulse3": 1.3, "emel": 1.2, "smc": 0.7,
    },
    "WEAK_TREND_UP": {
        "ml": 1.0, "pulse1": 1.0, "pulse2": 1.0, "pulse3": 1.0, "emel": 1.0, "smc": 1.0,
    },
    "WEAK_TREND_DOWN": {
        "ml": 1.0, "pulse1": 1.0, "pulse2": 1.0, "pulse3": 1.0, "emel": 1.0, "smc": 1.0,
    },
    "RANGING": {
        "ml": 0.8, "pulse1": 1.3, "pulse2": 1.2, "pulse3": 0.9, "emel": 0.9, "smc": 1.3,
    },
    "VOLATILE": {
        "ml": 0.7, "pulse1": 0.7, "pulse2": 0.8, "pulse3": 0.8, "emel": 1.0, "smc": 1.4,
    },
}

# ATR multipliers for TP/SL calculation per symbol
RISK_PARAMS: Dict[str, Dict[str, float]] = {
    "NDX.INDX":     {"sl_atr": 1.5, "tp1_atr": 1.0, "tp2_atr": 2.0, "pip_value": 1.0},
    "XAUUSD":       {"sl_atr": 1.5, "tp1_atr": 1.0, "tp2_atr": 2.0, "pip_value": 0.1},
    "GDAXI.INDX":   {"sl_atr": 1.5, "tp1_atr": 1.0, "tp2_atr": 2.0, "pip_value": 1.0},
    "USOIL.FOREX":  {"sl_atr": 1.5, "tp1_atr": 1.0, "tp2_atr": 2.0, "pip_value": 0.01},
}


@dataclass
class ModelSignal:
    """Single model output."""
    model_id: str
    direction: str          # BUY, SELL, HOLD
    confidence: float       # 0-100
    score: float = 0.0      # raw model score if available
    entry_price: float = 0.0
    take_profit: float = 0.0
    stop_loss: float = 0.0
    timeframe: str = ""
    is_available: bool = True


@dataclass
class TechnicalCondition:
    """Single technical check result."""
    name: str
    passed: bool
    value: float = 0.0
    detail: str = ""


@dataclass
class TechnicalSnapshot:
    """Technical indicator snapshot for validation."""
    price: float = 0.0
    ema_20: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    rsi_14: float = 50.0
    macd_value: float = 0.0
    macd_signal: float = 0.0
    adx: float = 0.0
    atr_14: float = 0.0
    volume_ratio: float = 1.0  # current / average
    bb_upper: float = 0.0
    bb_lower: float = 0.0
    bb_middle: float = 0.0

    def get_conditions(self, direction: str) -> List[TechnicalCondition]:
        """Evaluate 8 technical conditions for the proposed direction."""
        conditions = []
        is_buy = direction == "BUY"

        # 1. EMA Stack (20 > 50 > 200 for BUY, opposite for SELL)
        if is_buy:
            stacked = self.ema_20 > self.ema_50 > self.ema_200
        else:
            stacked = self.ema_20 < self.ema_50 < self.ema_200
        conditions.append(TechnicalCondition(
            name="ema_stack",
            passed=stacked,
            value=self.ema_20,
            detail=f"EMA20={self.ema_20:.2f} EMA50={self.ema_50:.2f} EMA200={self.ema_200:.2f}"
        ))

        # 2. Price vs EMA200
        if is_buy:
            above_200 = self.price > self.ema_200
        else:
            above_200 = self.price < self.ema_200
        conditions.append(TechnicalCondition(
            name="ema200_position",
            passed=above_200,
            value=self.price - self.ema_200,
            detail=f"Price={'above' if self.price > self.ema_200 else 'below'} EMA200"
        ))

        # 3. RSI Momentum
        if is_buy:
            rsi_ok = 40 < self.rsi_14 < 75
        else:
            rsi_ok = 25 < self.rsi_14 < 60
        conditions.append(TechnicalCondition(
            name="rsi_momentum",
            passed=rsi_ok,
            value=self.rsi_14,
            detail=f"RSI={self.rsi_14:.1f}"
        ))

        # 4. MACD Alignment
        if is_buy:
            macd_ok = self.macd_value > self.macd_signal
        else:
            macd_ok = self.macd_value < self.macd_signal
        conditions.append(TechnicalCondition(
            name="macd_alignment",
            passed=macd_ok,
            value=self.macd_value - self.macd_signal,
            detail=f"MACD={self.macd_value:.4f} Signal={self.macd_signal:.4f}"
        ))

        # 5. ADX Strength (>20 means trending)
        adx_ok = self.adx > 20
        conditions.append(TechnicalCondition(
            name="adx_trending",
            passed=adx_ok,
            value=self.adx,
            detail=f"ADX={self.adx:.1f}"
        ))

        # 6. Volume Confirmation (>0.8x average)
        vol_ok = self.volume_ratio > 0.8
        conditions.append(TechnicalCondition(
            name="volume_confirmed",
            passed=vol_ok,
            value=self.volume_ratio,
            detail=f"Vol Ratio={self.volume_ratio:.2f}x"
        ))

        # 7. Bollinger Band Position
        if is_buy:
            bb_ok = self.price > self.bb_middle and self.price < self.bb_upper
        else:
            bb_ok = self.price < self.bb_middle and self.price > self.bb_lower
        conditions.append(TechnicalCondition(
            name="bb_position",
            passed=bb_ok,
            value=self.price,
            detail=f"BB: {self.bb_lower:.2f} | {self.bb_middle:.2f} | {self.bb_upper:.2f}"
        ))

        # 8. ATR Volatility Check (not too extreme — ATR < 3x average is fine)
        # We consider ATR always "ok" here since it's more of a sizing parameter
        atr_ok = self.atr_14 > 0
        conditions.append(TechnicalCondition(
            name="atr_valid",
            passed=atr_ok,
            value=self.atr_14,
            detail=f"ATR={self.atr_14:.4f}"
        ))

        return conditions


@dataclass
class CombinationInfo:
    """Learning data for a model combination."""
    combo_key: str          # e.g. "ml+pulse2+emel"
    symbol: str
    regime: str
    total_signals: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    avg_profit_pips: float = 0.0
    avg_loss_pips: float = 0.0


@dataclass
class MetaSignal:
    """Final meta-engine output."""
    symbol: str
    direction: str              # BUY, SELL, HOLD
    confidence: float           # 0-100
    strength: str               # STRONG, MODERATE, WEAK
    source_combo: str           # "ml+pulse2+emel"
    regime: str
    agreement_ratio: float      # 0-1
    technical_score: float      # 0-1
    passed_conditions: List[str] = field(default_factory=list)
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    risk_reward: float = 0.0
    model_breakdown: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Dict] = field(default_factory=list)
    timestamp: float = 0.0


# ═══════════════════════════════════════════════════════════
# META-ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════

# In-memory cache for meta signals (TTL = 60 seconds)
_meta_cache: Dict[str, Tuple[float, MetaSignal]] = {}
META_CACHE_TTL = 55  # seconds


class MetaAnalysisEngine:
    """Orchestrates the 5-layer meta-analysis pipeline."""

    # ── Layer 1: Signal Collection ───────────────────────
    @staticmethod
    async def collect_signals(symbol: str) -> List[ModelSignal]:
        """Fetch live signals from all 6 models in parallel using direct function calls."""
        import json
        from fastapi.responses import Response

        from services.ml_prediction_service import get_ml_prediction
        from routers.emel_pulse import get_pulse_analysis, get_pulse_ml_analysis, get_pulse_v3_analysis, get_emel_analysis
        from services.smc_calculator_service import calculate_smc_with_gaps
        from services.data_hub import get_candles

        signals: List[ModelSignal] = []

        async def fetch_signal_direct(model_id: str) -> ModelSignal:
            try:
                data = None
                if model_id == "ml":
                    # returns dataclass/dict
                    resp = await get_ml_prediction(symbol, "balanced")
                    from dataclasses import asdict
                    data = asdict(resp) if hasattr(resp, '__dataclass_fields__') else (resp if isinstance(resp, dict) else {})
                elif model_id == "pulse1":
                    # returns Pydantic or dict
                    resp = await get_pulse_analysis(symbol)
                    data = resp.dict() if hasattr(resp, 'dict') else resp
                elif model_id == "pulse2":
                    resp = await get_pulse_ml_analysis(symbol)
                    data = resp.dict() if hasattr(resp, 'dict') else resp
                elif model_id == "pulse3":
                    resp = await get_pulse_v3_analysis(symbol)
                    data = resp.dict() if hasattr(resp, 'dict') else resp
                elif model_id == "emel":
                    resp = await get_emel_analysis(symbol)
                    data = resp.dict() if hasattr(resp, 'dict') else resp
                elif model_id == "smc":
                    candles = get_candles(symbol, "1d", limit=50)
                    if not candles or len(candles) < 20:
                        from services.market_data_service import get_ohlcv_data
                        candles = await get_ohlcv_data(symbol, "1D", limit=50)
                    if candles and len(candles) >= 20:
                        # return raw dict, wrap it to match standard
                        resp = await calculate_smc_with_gaps(symbol, candles)
                        data = {"data": resp} 
                    else:
                        data = {"error": "Insufficient data"}

                # Handle Pydantic V2 model_dump vs dict
                if hasattr(data, "model_dump"):
                    data = data.model_dump()
                elif hasattr(data, "dict"):
                    data = data.dict()
                elif isinstance(data, Response):
                    try:
                        data = json.loads(data.body.decode('utf-8'))
                    except Exception:
                        data = {}
                
                if isinstance(data, dict) and ("error" in data or data.get("success") is False):
                    return ModelSignal(model_id=model_id, direction="HOLD", confidence=0, is_available=False)

                return _parse_model_response(model_id, data)
                
            except Exception as e:
                logger.warning(f"[MetaEngine] {model_id} fetch failed for {symbol}: {e}")
                return ModelSignal(
                    model_id=model_id,
                    direction="HOLD",
                    confidence=0,
                    is_available=False
                )

        model_ids = ["ml", "pulse1", "pulse2", "pulse3", "emel", "smc"]
        tasks = [fetch_signal_direct(mid) for mid in model_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, ModelSignal):
                signals.append(r)
            elif isinstance(r, Exception):
                logger.error(f"[MetaEngine] Signal collection loop error: {r}")

        return signals

    # ── Layer 2: Combination Mining ──────────────────────
    @staticmethod
    async def get_best_combinations(
        symbol: str,
        direction: str,
        regime: str,
        agreeing_models: List[str],
    ) -> List[CombinationInfo]:
        """Find top-performing model combos from historical data."""
        try:
            from database.supabase_client import get_supabase_client
            client = get_supabase_client()
            if not client:
                return []

            result = client.table("meta_combination_stats") \
                .select("*") \
                .eq("symbol", symbol) \
                .eq("regime", regime) \
                .gte("total_signals", 5) \
                .order("win_rate", desc=True) \
                .limit(10) \
                .execute()

            rows = result.get("data", []) if isinstance(result, dict) else (result.data if hasattr(result, "data") else [])
            combos = []
            if rows:
                for row in rows:
                    combos.append(CombinationInfo(
                        combo_key=row.get("combo_key", ""),
                        symbol=row.get("symbol", symbol),
                        regime=row.get("regime", regime),
                        total_signals=row.get("total_signals", 0),
                        wins=row.get("wins", 0),
                        losses=row.get("losses", 0),
                        win_rate=row.get("win_rate", 0),
                        profit_factor=row.get("profit_factor", 0),
                        expectancy=row.get("expectancy", 0),
                        avg_profit_pips=row.get("avg_profit_pips", 0),
                        avg_loss_pips=row.get("avg_loss_pips", 0),
                    ))
                return combos

            from services.permutation_batch_service import get_latest_model_batch_results

            batch_result = await asyncio.to_thread(get_latest_model_batch_results, symbol, direction, 10)
            batch_rows = batch_result.get("results", []) if isinstance(batch_result, dict) and not batch_result.get("error") else []
            if not batch_rows:
                return []

            agreeing_model_set = {model for model in agreeing_models if model}
            for row in batch_rows:
                combo_key = str(row.get("combination") or "").strip()
                if not combo_key:
                    continue
                combos.append(CombinationInfo(
                    combo_key=combo_key,
                    symbol=symbol,
                    regime=regime,
                    total_signals=int(row.get("total_signals") or 0),
                    wins=int(row.get("wins") or 0),
                    losses=int(row.get("losses") or 0),
                    win_rate=float(row.get("win_rate") or 0.0),
                    profit_factor=float(row.get("profit_factor") or 0.0),
                    expectancy=float(row.get("expectancy") or 0.0),
                    avg_profit_pips=0.0,
                    avg_loss_pips=0.0,
                ))

            combos.sort(
                key=lambda combo: (
                    -sum(1 for model in combo.combo_key.split("+") if model in agreeing_model_set),
                    -combo.win_rate,
                    -combo.total_signals,
                    -combo.profit_factor,
                )
            )
            return combos[:10]
        except Exception as e:
            logger.error(f"[MetaEngine] Combination fetch error: {e}")
            return []

    # ── Layer 3: Technical Validation ────────────────────
    @staticmethod
    async def get_technical_snapshot(symbol: str) -> TechnicalSnapshot:
        """Build technical indicator snapshot from DataHub."""
        try:
            from services.data_hub import get_candles
            candles = get_candles(symbol, "1h")

            if not candles or len(candles) < 200:
                # Fallback: try fetching
                from services.market_data_service import get_ohlcv_data
                raw = await get_ohlcv_data(symbol, "1H", 250)
                if raw and len(raw) >= 50:
                    candles = raw
                else:
                    logger.warning(f"[MetaEngine] Insufficient candles for {symbol}")
                    return TechnicalSnapshot()

            closes = [float(c.get("close", 0)) for c in candles]
            highs = [float(c.get("high", 0)) for c in candles]
            lows = [float(c.get("low", 0)) for c in candles]
            volumes = [float(c.get("volume", 0)) for c in candles]

            price = closes[-1] if closes else 0

            # EMA calculations (alpha = 2 / (period + 1))
            def ema(data, period):
                if len(data) < period:
                    return data[-1] if data else 0
                alpha = 2.0 / (period + 1)
                result = data[0]
                for v in data[1:]:
                    result = alpha * v + (1 - alpha) * result
                return result

            ema_20 = ema(closes, 20)
            ema_50 = ema(closes, 50)
            ema_200 = ema(closes, 200) if len(closes) >= 200 else ema(closes, len(closes))

            # RSI
            def calc_rsi(data, period=14):
                if len(data) < period + 1:
                    return 50
                deltas = [data[i] - data[i - 1] for i in range(1, len(data))]
                gains = [max(0, d) for d in deltas]
                losses_val = [abs(min(0, d)) for d in deltas]
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses_val[-period:]) / period
                if avg_loss == 0:
                    return 100
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))

            rsi = calc_rsi(closes)

            # MACD
            macd_val = ema(closes, 12) - ema(closes, 26)
            # For signal line, we'd need MACD history — simplified
            macd_signal = ema(closes[-26:], 9) - ema(closes[-26:], 18) if len(closes) >= 26 else 0

            # ADX (simplified using ATR-based approach)
            def calc_adx(highs_l, lows_l, closes_l, period=14):
                if len(highs_l) < period + 1:
                    return 25
                tr_list = []
                plus_dm_list = []
                minus_dm_list = []
                for i in range(1, len(highs_l)):
                    high_low = highs_l[i] - lows_l[i]
                    high_close = abs(highs_l[i] - closes_l[i - 1])
                    low_close = abs(lows_l[i] - closes_l[i - 1])
                    tr_list.append(max(high_low, high_close, low_close))
                    up_move = highs_l[i] - highs_l[i - 1]
                    down_move = lows_l[i - 1] - lows_l[i]
                    plus_dm_list.append(up_move if up_move > down_move and up_move > 0 else 0)
                    minus_dm_list.append(down_move if down_move > up_move and down_move > 0 else 0)

                atr_sum = sum(tr_list[-period:])
                if atr_sum == 0:
                    return 25

                plus_di = 100 * sum(plus_dm_list[-period:]) / atr_sum
                minus_di = 100 * sum(minus_dm_list[-period:]) / atr_sum
                di_sum = plus_di + minus_di
                if di_sum == 0:
                    return 25
                dx = 100 * abs(plus_di - minus_di) / di_sum
                return dx

            adx = calc_adx(highs, lows, closes)

            # ATR
            def calc_atr(highs_l, lows_l, closes_l, period=14):
                if len(highs_l) < 2:
                    return 0
                tr_list = []
                for i in range(1, len(highs_l)):
                    high_low = highs_l[i] - lows_l[i]
                    high_close = abs(highs_l[i] - closes_l[i - 1])
                    low_close = abs(lows_l[i] - closes_l[i - 1])
                    tr_list.append(max(high_low, high_close, low_close))
                return sum(tr_list[-period:]) / min(period, len(tr_list)) if tr_list else 0

            atr_14 = calc_atr(highs, lows, closes)

            # Volume ratio
            avg_vol = sum(volumes[-20:]) / max(1, len(volumes[-20:])) if volumes else 1
            vol_ratio = volumes[-1] / avg_vol if avg_vol > 0 and volumes else 1.0

            # Bollinger Bands
            sma_20 = sum(closes[-20:]) / min(20, len(closes)) if closes else 0
            import math
            if len(closes) >= 20:
                variance = sum((c - sma_20) ** 2 for c in closes[-20:]) / 20
                std_dev = math.sqrt(variance)
            else:
                std_dev = 0
            bb_upper = sma_20 + 2 * std_dev
            bb_lower = sma_20 - 2 * std_dev

            return TechnicalSnapshot(
                price=price,
                ema_20=ema_20,
                ema_50=ema_50,
                ema_200=ema_200,
                rsi_14=rsi,
                macd_value=macd_val,
                macd_signal=macd_signal,
                adx=adx,
                atr_14=atr_14,
                volume_ratio=vol_ratio,
                bb_upper=bb_upper,
                bb_lower=bb_lower,
                bb_middle=sma_20,
            )
        except Exception as e:
            logger.error(f"[MetaEngine] Technical snapshot error for {symbol}: {e}")
            return TechnicalSnapshot()

    # ── Layer 4: Confidence Fusion ───────────────────────
    @staticmethod
    def fuse_confidence(
        signals: List[ModelSignal],
        direction: str,
        regime: str,
        tech_score: float,
        best_combo: Optional[CombinationInfo],
    ) -> float:
        """Compute final weighted confidence score (0-100)."""
        if not signals:
            return 0.0

        # Get regime-adjusted weights
        regime_mults = REGIME_WEIGHT_MULTIPLIERS.get(regime, {})

        weighted_sum = 0.0
        weight_total = 0.0

        for sig in signals:
            if not sig.is_available or sig.direction == "HOLD":
                continue

            base_weight = DEFAULT_MODEL_WEIGHTS.get(sig.model_id, 0.1)
            regime_mult = regime_mults.get(sig.model_id, 1.0)
            effective_weight = base_weight * regime_mult

            # Direction alignment bonus
            if sig.direction == direction:
                alignment_bonus = 1.0
            else:
                alignment_bonus = -0.5  # penalize disagreement

            weighted_sum += sig.confidence * effective_weight * alignment_bonus
            weight_total += effective_weight

        if weight_total == 0:
            return 0.0

        base_confidence = weighted_sum / weight_total

        # Technical boost/penalty (±15%)
        tech_boost = (tech_score - 0.5) * 30  # -15 to +15

        # Historical combo boost (if we have data)
        combo_boost = 0
        if best_combo and best_combo.total_signals >= 10:
            combo_boost = (best_combo.win_rate - 0.5) * 20  # -10 to +10

        final = max(0, min(100, base_confidence + tech_boost + combo_boost))
        return round(final, 1)

    # ── Layer 5: Risk Calculator ─────────────────────────
    @staticmethod
    def calculate_risk(
        symbol: str,
        direction: str,
        price: float,
        atr: float,
        risk_profile: str = "balanced",
    ) -> Dict[str, float]:
        """Calculate Entry/TP1/TP2/SL from ATR."""
        params = RISK_PARAMS.get(symbol, RISK_PARAMS["XAUUSD"])

        # Risk profile adjustments
        profile_mult = {"conservative": 0.8, "balanced": 1.0, "aggressive": 1.3}
        mult = profile_mult.get(risk_profile, 1.0)

        sl_distance = atr * params["sl_atr"] * mult
        tp1_distance = atr * params["tp1_atr"] * mult
        tp2_distance = atr * params["tp2_atr"] * mult

        if direction == "BUY":
            entry = price
            sl = price - sl_distance
            tp1 = price + tp1_distance
            tp2 = price + tp2_distance
        else:  # SELL
            entry = price
            sl = price + sl_distance
            tp1 = price - tp1_distance
            tp2 = price - tp2_distance

        risk = abs(entry - sl)
        reward = abs(tp1 - entry)
        rr = round(reward / risk, 2) if risk > 0 else 0

        return {
            "entry_price": round(entry, 4),
            "stop_loss": round(sl, 4),
            "take_profit_1": round(tp1, 4),
            "take_profit_2": round(tp2, 4),
            "risk_reward": rr,
        }

    # ── Main Pipeline ────────────────────────────────────
    async def generate_meta_signal(
        self,
        symbol: str,
        risk_profile: str = "balanced",
        min_confidence: float = 40,
    ) -> Optional[MetaSignal]:
        """Run the full 5-layer meta-analysis pipeline."""
        start_ts = time.time()

        # Check cache
        cached = _meta_cache.get(symbol)
        if cached:
            cache_ts, cache_signal = cached
            if time.time() - cache_ts < META_CACHE_TTL:
                logger.info(f"[MetaEngine] Cache hit for {symbol}")
                return cache_signal

        # === LAYER 1: Collect all model signals ===
        signals = await self.collect_signals(symbol)
        available_signals = [s for s in signals if s.is_available and s.direction != "HOLD"]

        if len(available_signals) < 2:
            logger.info(f"[MetaEngine] Not enough signals for {symbol}: {len(available_signals)}")
            return None

        # === Determine majority direction ===
        buy_count = sum(1 for s in available_signals if s.direction == "BUY")
        sell_count = sum(1 for s in available_signals if s.direction == "SELL")
        total_active = buy_count + sell_count

        if total_active == 0:
            return None

        if buy_count > sell_count:
            direction = "BUY"
            agreement_ratio = buy_count / total_active
        elif sell_count > buy_count:
            direction = "SELL"
            agreement_ratio = sell_count / total_active
        else:
            # Tie — use weighted confidence to break
            buy_conf = sum(s.confidence for s in available_signals if s.direction == "BUY")
            sell_conf = sum(s.confidence for s in available_signals if s.direction == "SELL")
            direction = "BUY" if buy_conf >= sell_conf else "SELL"
            agreement_ratio = 0.5

        agreeing_models = [s.model_id for s in available_signals if s.direction == direction]
        current_combo = "+".join(sorted(agreeing_models))

        # === Get market regime ===
        regime = "UNKNOWN"
        try:
            from services.market_regime_service import detect_regime
            regime_data = await detect_regime(symbol)
            if regime_data and isinstance(regime_data, dict):
                regime = regime_data.get("regime", "UNKNOWN")
            elif regime_data and hasattr(regime_data, "regime"):
                regime = regime_data.regime
        except Exception as e:
            logger.warning(f"[MetaEngine] Regime detection failed: {e}")

        # === LAYER 2: Find best historical combination ===
        combos = await self.get_best_combinations(symbol, direction, regime, agreeing_models)
        best_combo = combos[0] if combos else None

        # If we have historical data and a better combo exists, prefer it
        if best_combo and best_combo.combo_key != current_combo:
            # Check if current combo is in the list
            current_in_list = next(
                (c for c in combos if c.combo_key == current_combo), None
            )
            if current_in_list and current_in_list.win_rate > 0.5:
                best_combo = current_in_list

        display_combo = best_combo.combo_key if best_combo and best_combo.combo_key else current_combo

        # === LAYER 3: Technical Validation ===
        tech = await self.get_technical_snapshot(symbol)
        conditions = tech.get_conditions(direction)
        passed = [c for c in conditions if c.passed]
        tech_score = len(passed) / len(conditions) if conditions else 0

        # === LAYER 4: Confidence Fusion ===
        confidence = self.fuse_confidence(
            signals=available_signals,
            direction=direction,
            regime=regime,
            tech_score=tech_score,
            best_combo=best_combo,
        )

        # Check minimum confidence
        if confidence < min_confidence:
            direction = "HOLD"

        # Determine strength
        if confidence >= 75:
            strength = "STRONG"
        elif confidence >= 55:
            strength = "MODERATE"
        else:
            strength = "WEAK"

        # === LAYER 5: Risk Calculation ===
        risk_params = self.calculate_risk(
            symbol=symbol,
            direction=direction if direction != "HOLD" else "BUY",
            price=tech.price,
            atr=tech.atr_14,
            risk_profile=risk_profile,
        )

        # Build model breakdown
        model_breakdown = {}
        for sig in signals:
            model_breakdown[sig.model_id] = {
                "direction": sig.direction,
                "confidence": sig.confidence,
                "is_available": sig.is_available,
                "agrees": sig.direction == direction,
            }

        # Build alternatives (other combos)
        alternatives = []
        for combo in combos:
            if combo.combo_key == display_combo:
                continue
            alternatives.append({
                "combo_key": combo.combo_key,
                "win_rate": combo.win_rate,
                "total_signals": combo.total_signals,
                "profit_factor": combo.profit_factor,
            })
            if len(alternatives) >= 3:
                break

        meta_signal = MetaSignal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            strength=strength,
            source_combo=display_combo,
            regime=regime,
            agreement_ratio=round(agreement_ratio, 2),
            technical_score=round(tech_score, 2),
            passed_conditions=[c.name for c in passed],
            entry_price=risk_params["entry_price"],
            stop_loss=risk_params["stop_loss"],
            take_profit_1=risk_params["take_profit_1"],
            take_profit_2=risk_params["take_profit_2"],
            risk_reward=risk_params["risk_reward"],
            model_breakdown=model_breakdown,
            alternatives=alternatives,
            timestamp=time.time(),
        )

        # Cache
        _meta_cache[symbol] = (time.time(), meta_signal)

        elapsed = (time.time() - start_ts) * 1000
        logger.info(
            f"[MetaEngine] {symbol}: {direction} ({confidence:.0f}%) "
            f"combo={display_combo} regime={regime} "
            f"tech={tech_score:.0%} in {elapsed:.0f}ms"
        )

        return meta_signal


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _parse_model_response(model_id: str, data: Any) -> ModelSignal:
    """Parse varied API response formats into a ModelSignal."""
    try:
        if not data:
            return ModelSignal(model_id=model_id, direction="HOLD", confidence=0, is_available=False)

        # Handle nested "data" key
        if isinstance(data, dict) and "data" in data:
            inner = data["data"]
            if isinstance(inner, dict):
                data = inner

        direction = "HOLD"
        confidence = 0.0
        entry = 0.0
        tp = 0.0
        sl = 0.0

        # ML model response
        if model_id == "ml":
            direction = data.get("signal", data.get("ml_direction", "HOLD"))
            conf_raw = data.get("confidence", data.get("ml_confidence", 0))
            confidence = float(conf_raw) * 100 if float(conf_raw) <= 1 else float(conf_raw)
            entry = float(data.get("current_price", data.get("ml_entry_price", 0)) or 0)
            tp = float(data.get("target_price", data.get("ml_target_price", 0)) or 0)
            sl = float(data.get("stop_price", data.get("ml_stop_price", 0)) or 0)

        # Pulse 1/2/3 response
        elif model_id.startswith("pulse"):
            direction = data.get("signal", data.get("direction", "HOLD"))
            conf_raw = data.get("confidence", data.get("meta_confidence", 0))
            confidence = float(conf_raw) * 100 if float(conf_raw) <= 1 else float(conf_raw)
            entry = float(data.get("entry_price", data.get("current_price", 0)) or 0)
            tp = float(data.get("take_profit", data.get("tp1", 0)) or 0)
            sl = float(data.get("stop_loss", data.get("sl", 0)) or 0)

        # EMEL response
        elif model_id == "emel":
            direction = data.get("signal", data.get("direction", "HOLD"))
            conf_raw = data.get("confidence", data.get("total_score", 0))
            confidence = float(conf_raw) * 100 if float(conf_raw) <= 1 else float(conf_raw)
            # EMEL uses checkpoint scoring
            if "total_score" in data:
                confidence = min(100, float(data["total_score"]) * 10)  # score 0-10 → 0-100
            entry = float(data.get("entry_price", data.get("current_price", 0)) or 0)

        # SMC response
        elif model_id == "smc":
            direction = data.get("signal", data.get("bias", "HOLD"))
            conf_raw = data.get("confidence", data.get("score", 0))
            confidence = float(conf_raw) * 100 if float(conf_raw) <= 1 else float(conf_raw)
            entry = float(data.get("entry_price", data.get("current_price", 0)) or 0)

        # Normalize direction
        direction = direction.upper()
        if direction not in ("BUY", "SELL", "HOLD"):
            if direction in ("BULLISH", "LONG", "UP"):
                direction = "BUY"
            elif direction in ("BEARISH", "SHORT", "DOWN"):
                direction = "SELL"
            else:
                direction = "HOLD"

        return ModelSignal(
            model_id=model_id,
            direction=direction,
            confidence=min(100, max(0, confidence)),
            entry_price=entry,
            take_profit=tp,
            stop_loss=sl,
            is_available=True,
        )
    except Exception as e:
        logger.warning(f"[MetaEngine] Parse error for {model_id}: {e}")
        return ModelSignal(model_id=model_id, direction="HOLD", confidence=0, is_available=False)


# Singleton instance
_engine = MetaAnalysisEngine()


async def get_meta_signal(
    symbol: str,
    risk_profile: str = "balanced",
    min_confidence: float = 40,
) -> Optional[MetaSignal]:
    """Public API for getting a meta-signal."""
    return await _engine.generate_meta_signal(symbol, risk_profile, min_confidence)


async def get_meta_dashboard() -> Dict[str, Any]:
    """Get meta-signals for all 4 symbols."""
    results = {}
    tasks = [get_meta_signal(sym) for sym in SUPPORTED_SYMBOLS]
    signals = await asyncio.gather(*tasks, return_exceptions=True)

    for sym, sig in zip(SUPPORTED_SYMBOLS, signals):
        if isinstance(sig, MetaSignal):
            results[sym] = asdict(sig)
        elif isinstance(sig, Exception):
            logger.error(f"[MetaEngine] Dashboard error for {sym}: {sig}")
            results[sym] = {"symbol": sym, "direction": "HOLD", "confidence": 0, "error": str(sig)}
        else:
            results[sym] = {"symbol": sym, "direction": "HOLD", "confidence": 0}

    return results
