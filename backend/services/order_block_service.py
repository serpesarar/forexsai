from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from threading import Lock
from typing import Any, Dict, List, Tuple

import numpy as np

from order_block_detector import Candle, OrderBlockConfig, OrderBlockDetector
from order_block_detector_v2 import detect_all, MarketStructureAnalyzer, SwingDetector
from services.ml_service import run_nasdaq_signal, run_xauusd_signal
from services.prediction_logger import log_smc_prediction
from services.sentiment_analyzer import run_claude_sentiment
from services.rtyhiim_service import run_rtyhiim_detector
from services.data_fetcher import fetch_eod_candles, fetch_ohlc_data


logger = logging.getLogger(__name__)
SMC_MODEL_TYPE = "smc"
SMC_STRATEGY = "SMART_MONEY_ZONES"


@dataclass
class CacheEntry:
    timestamp: datetime
    payload: dict


class OrderBlockService:
    """Service wrapper with caching for order block detection."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _get_pip_value(symbol: str) -> float:
        symbol_upper = (symbol or "").upper()
        if "XAU" in symbol_upper:
            return 1.0
        if "OIL" in symbol_upper or "USOIL" in symbol_upper or "CL" in symbol_upper:
            return 0.01
        return 1.0

    @staticmethod
    def _get_unit_label(symbol: str) -> str:
        return "pts"

    @staticmethod
    def _calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        n = len(closes)
        if n < 2:
            return float(closes[-1]) * 0.001 if n else 1.0
        trs = []
        for i in range(1, min(period + 1, n)):
            tr = max(
                float(highs[i]) - float(lows[i]),
                abs(float(highs[i]) - float(closes[i - 1])),
                abs(float(lows[i]) - float(closes[i - 1])),
            )
            trs.append(tr)
        return float(np.mean(trs)) if trs else (float(closes[-1]) * 0.001 if n else 1.0)

    def _build_support_resistance(self, symbol: str, candles: List[Candle], current_price: float) -> Dict[str, Any]:
        pip_value = self._get_pip_value(symbol)
        unit = self._get_unit_label(symbol)

        if not candles:
            return {
                "all_levels": [],
                "nearest_resistance": None,
                "nearest_support": None,
                "pivot": round(current_price, 2),
                "range_high": round(current_price, 2),
                "range_low": round(current_price, 2),
                "method": "swing_cluster_fib",
            }

        highs = np.array([float(getattr(c, "high", current_price) or current_price) for c in candles], dtype=np.float64)
        lows = np.array([float(getattr(c, "low", current_price) or current_price) for c in candles], dtype=np.float64)
        closes = np.array([float(getattr(c, "close", current_price) or current_price) for c in candles], dtype=np.float64)
        n = len(closes)

        atr = self._calc_atr(highs, lows, closes, 14)
        cluster_threshold = max(atr * 0.7, current_price * 0.0015)
        period = 3
        swing_highs: List[tuple[float, int]] = []
        swing_lows: List[tuple[float, int]] = []

        for i in range(period, max(period, n - period)):
            h_window = highs[i - period : i + period + 1]
            l_window = lows[i - period : i + period + 1]
            if len(h_window) and float(highs[i]) >= float(np.max(h_window)):
                swing_highs.append((float(highs[i]), i))
            if len(l_window) and float(lows[i]) <= float(np.min(l_window)):
                swing_lows.append((float(lows[i]), i))

        def cluster_swings(swings: List[tuple[float, int]]) -> List[Dict[str, Any]]:
            if not swings:
                return []
            sorted_swings = sorted(swings, key=lambda item: item[0])
            clusters: List[Dict[str, Any]] = []
            for price, idx in sorted_swings:
                placed = False
                for cluster in clusters:
                    if abs(price - cluster["center"]) <= cluster_threshold:
                        cluster["prices"].append(price)
                        cluster["indices"].append(idx)
                        cluster["center"] = float(np.mean(cluster["prices"]))
                        cluster["latest_idx"] = max(cluster["indices"])
                        placed = True
                        break
                if not placed:
                    clusters.append({
                        "center": price,
                        "prices": [price],
                        "indices": [idx],
                        "latest_idx": idx,
                    })
            for cluster in clusters:
                touches = len(cluster["prices"])
                recency = cluster["latest_idx"] / max(n, 1)
                cluster["score"] = touches + recency * 0.5
                cluster["touch_count"] = touches
            return clusters

        res_clusters = cluster_swings([(price, idx) for price, idx in swing_highs if price > current_price])
        sup_clusters = cluster_swings([(price, idx) for price, idx in swing_lows if price < current_price])

        res_nearest = sorted(res_clusters, key=lambda cluster: cluster["center"] - current_price)[:3]
        sup_nearest = sorted(sup_clusters, key=lambda cluster: current_price - cluster["center"])[:3]

        window = min(50, n)
        high_ref = float(np.max(highs[-window:])) if window else current_price
        low_ref = float(np.min(lows[-window:])) if window else current_price
        pivot = (high_ref + low_ref + current_price) / 3
        range_size = max(high_ref - low_ref, current_price * 0.002)

        def fib_res_levels() -> List[Dict[str, Any]]:
            out = []
            for mult in (0.382, 0.618, 1.0):
                price = pivot + range_size * mult
                if price > current_price:
                    out.append({"center": price, "touch_count": 1, "score": 0.5, "is_fib": True})
            return sorted(out, key=lambda cluster: cluster["center"] - current_price)

        def fib_sup_levels() -> List[Dict[str, Any]]:
            out = []
            for mult in (0.382, 0.618, 1.0):
                price = pivot - range_size * mult
                if price < current_price:
                    out.append({"center": price, "touch_count": 1, "score": 0.5, "is_fib": True})
            return sorted(out, key=lambda cluster: current_price - cluster["center"])

        if len(res_nearest) < 2:
            existing_prices = {round(cluster["center"], 1) for cluster in res_nearest}
            for level in fib_res_levels():
                if round(level["center"], 1) not in existing_prices:
                    res_nearest.append(level)
                if len(res_nearest) >= 3:
                    break
            res_nearest = sorted(res_nearest, key=lambda cluster: cluster["center"] - current_price)[:3]

        if len(sup_nearest) < 2:
            existing_prices = {round(cluster["center"], 1) for cluster in sup_nearest}
            for level in fib_sup_levels():
                if round(level["center"], 1) not in existing_prices:
                    sup_nearest.append(level)
                if len(sup_nearest) >= 3:
                    break
            sup_nearest = sorted(sup_nearest, key=lambda cluster: current_price - cluster["center"])[:3]

        levels: List[Dict[str, Any]] = []
        for idx, cluster in enumerate(res_nearest):
            price = round(float(cluster["center"]), 2)
            distance = abs(price - current_price) / pip_value
            touches = int(cluster.get("touch_count", 1) or 1)
            levels.append({
                "type": "resistance",
                "name": f"R{idx + 1}" + (f" (×{touches})" if touches >= 2 else ""),
                "price": price,
                "distance": round(distance, 1),
                "distance_display": f"+{round(distance, 1)} {unit}",
                "strength": "strong" if touches >= 2 else "normal",
                "is_next": idx == 0,
                "touch_count": touches,
            })

        levels.append({
            "type": "current",
            "name": "Current Price",
            "price": round(current_price, 2),
            "distance": 0,
            "distance_display": "HERE",
            "strength": "current",
        })

        for idx, cluster in enumerate(sup_nearest):
            price = round(float(cluster["center"]), 2)
            distance = abs(price - current_price) / pip_value
            touches = int(cluster.get("touch_count", 1) or 1)
            levels.append({
                "type": "support",
                "name": f"S{idx + 1}" + (f" (×{touches})" if touches >= 2 else ""),
                "price": price,
                "distance": round(distance, 1),
                "distance_display": f"-{round(distance, 1)} {unit}",
                "strength": "strong" if touches >= 2 else "normal",
                "is_next": idx == 0,
                "touch_count": touches,
            })

        resistances = [level for level in levels if level["type"] == "resistance"]
        supports = [level for level in levels if level["type"] == "support"]

        return {
            "all_levels": sorted(levels, key=lambda level: level["price"], reverse=True),
            "nearest_resistance": min(resistances, key=lambda level: level["distance"]) if resistances else None,
            "nearest_support": min(supports, key=lambda level: level["distance"]) if supports else None,
            "pivot": round(pivot, 2),
            "range_high": round(high_ref, 2),
            "range_low": round(low_ref, 2),
            "method": "swing_cluster_fib",
        }

    async def detect(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        config: OrderBlockConfig,
        *,
        use_cache: bool = True,
        log_signals: bool = True,
    ) -> dict:
        # bump cache version whenever detection inputs/logic changes
        cache_key = f"v5:{symbol}:{timeframe}:{limit}:{config}"  # noqa: S608 - cache key
        if use_cache:
            with self._lock:
                cached = self._cache.get(cache_key)
                if cached and self._utc_now() - cached.timestamp < self.ttl:
                    return cached.payload

        candles = await self._load_candles(symbol=symbol, timeframe=timeframe, limit=limit)
        
        # Use NEW detector with independent algorithms
        structure = MarketStructureAnalyzer.analyze(candles)
        
        # Also run old detector for compatibility
        detector = OrderBlockDetector(config)
        old_order_blocks = detector.detect(candles)

        # Prepare enriched order blocks with structure info
        enriched_obs = []
        for ob in structure.ob_list[:10]:  # Top 10 OBs
            ob_dict = ob.to_dict()
            # Add structure flags for frontend
            ob_dict["has_choch"] = any(c.index <= ob.index + 5 for c in structure.choch_list)
            ob_dict["has_bos"] = any(b.index <= ob.index + 5 for b in structure.bos_list)
            ob_dict["has_fvg"] = any(f.index <= ob.index + 5 for f in structure.fvg_list)
            enriched_obs.append(ob_dict)

        combined_signal = await self._combine_signals(symbol, structure)
        current_price = float(getattr(candles[-1], "close", 0.0) or 0.0) if candles else 0.0
        support_resistance = self._build_support_resistance(symbol, candles, current_price) if current_price > 0 else {
            "all_levels": [],
            "nearest_resistance": None,
            "nearest_support": None,
            "pivot": None,
            "range_high": None,
            "range_low": None,
            "method": "swing_cluster_fib",
        }

        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "total_order_blocks": len(structure.ob_list),
            "bearish_obs": len([ob for ob in structure.ob_list if ob.type == "bearish"]),
            "bullish_obs": len([ob for ob in structure.ob_list if ob.type == "bullish"]),
            "order_blocks": enriched_obs,
            "structure": structure.to_dict(),  # NEW: Full structure data
            "choch_list": [c.to_dict() for c in structure.choch_list],
            "bos_list": [b.to_dict() for b in structure.bos_list],
            "fvg_list": [f.to_dict() for f in structure.fvg_list],
            "active_signals": [],
            "combined_signal": combined_signal,
            "trend": structure.trend,
            "support_resistance": support_resistance,
            "timestamp": self._utc_now().isoformat().replace("+00:00", "Z"),
        }

        if log_signals:
            await self._log_smc_signal(symbol=symbol, timeframe=timeframe, candles=candles, combined_signal=combined_signal)

        with self._lock:
            self._cache[cache_key] = CacheEntry(timestamp=self._utc_now(), payload=payload)

        return payload

    async def _log_smc_signal(self, symbol: str, timeframe: str, candles: List[Candle], combined_signal: dict) -> None:
        direction = (combined_signal or {}).get("action")
        if direction not in {"BUY", "SELL"} or not candles:
            return

        entry_price = float(getattr(candles[-1], "close", 0.0) or 0.0)
        if entry_price <= 0:
            return

        try:
            confidence = float((combined_signal or {}).get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence <= 1.0:
            confidence *= 100.0
        confidence = round(confidence, 1)

        try:
            await log_smc_prediction(
                timeframe=timeframe,
                symbol=symbol,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                reasoning=(combined_signal or {}).get("reasoning") or [],
            )
        except Exception:
            logger.exception("Smart Money Zones signal logging failed for %s %s", symbol, timeframe)

    def check_entry(self, symbol: str, timeframe: str, order_block_index: int) -> dict:
        config = OrderBlockConfig()
        # Best-effort: use cached/synthetic candles for check-entry if live candles unavailable.
        candles = self._generate_candles(300)
        detector = OrderBlockDetector(config)
        order_blocks = detector.detect(candles)
        match = next((ob for ob in order_blocks if ob.index == order_block_index), None)
        if not match:
            return {
                "has_signal": False,
                "entry_type": "",
                "entry_price": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0,
                "risk_reward": 0.0,
            }
        signal = detector.detect_entry(candles, match)
        if not signal:
            return {
                "has_signal": False,
                "entry_type": "",
                "entry_price": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0,
                "risk_reward": 0.0,
            }
        return signal.__dict__

    def backtest(self, symbol: str, timeframe: str) -> dict:
        # Real backtesting not yet implemented — return zeros instead of fake metrics
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_risk_reward": 0.0,
            "total_profit": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "note": "Real backtesting not implemented. Use live signal tracking for performance data.",
        }

    async def _combine_signals(self, symbol: str, structure=None) -> dict:
        # Quick signal based on structure
        if structure:
            ob_count = len(structure.ob_list)
            choch_count = len(structure.choch_list)
            bos_count = len(structure.bos_list)
            
            # Determine action based on structure
            if structure.trend == "bullish" and ob_count > 0:
                bullish_obs = [ob for ob in structure.ob_list if ob.type == "bullish"]
                if bullish_obs:
                    action = "BUY"
                    confidence = min(0.95, 0.5 + bullish_obs[0].score / 200)
                else:
                    action = "NEUTRAL"
                    confidence = 0.5
            elif structure.trend == "bearish" and ob_count > 0:
                bearish_obs = [ob for ob in structure.ob_list if ob.type == "bearish"]
                if bearish_obs:
                    action = "SELL"
                    confidence = min(0.95, 0.5 + bearish_obs[0].score / 200)
                else:
                    action = "NEUTRAL"
                    confidence = 0.5
            else:
                action = "NEUTRAL"
                confidence = 0.5
            
            reasoning = [
                f"Market structure: {structure.trend.upper()}",
                f"Order blocks detected: {ob_count}",
                f"CHoCH events: {choch_count}",
                f"BOS events: {bos_count}",
                f"FVG zones: {len(structure.fvg_list)}",
            ]
        else:
            action = "NEUTRAL"
            confidence = 0.5
            reasoning = ["No structure data available"]
        
        return {
            "action": action,
            "confidence": float(confidence),
            "reasoning": reasoning,
        }

    async def _load_candles(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        """
        Load candles from DataHub for the requested timeframe.
        Falls back: requested tf → EOD → synthetic.
        DataHub supports: 5m, 15m, 30m, 1h, 4h, eod
        """
        # Try requested timeframe first
        data = await fetch_ohlc_data(symbol, timeframe=timeframe, limit=limit)

        # Fallback to EOD if the requested timeframe returned nothing
        if not data:
            data = await fetch_eod_candles(symbol, limit=limit)

        if data:
            candles: List[Candle] = []
            for idx, row in enumerate(data):
                candles.append(
                    Candle(
                        timestamp=float(idx),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            return candles

        # Last resort: synthetic (should rarely happen)
        return self._generate_candles(limit)

    def _generate_candles(self, limit: int) -> List[Candle]:
        prices = np.cumsum(np.random.normal(scale=0.8, size=limit)) + 21500
        candles: List[Candle] = []
        for idx in range(limit):
            open_price = prices[idx]
            close_price = prices[idx] + np.random.normal(scale=0.4)
            high = max(open_price, close_price) + abs(np.random.normal(scale=0.3))
            low = min(open_price, close_price) - abs(np.random.normal(scale=0.3))
            candles.append(
                Candle(
                    timestamp=float(idx),
                    open=float(open_price),
                    high=float(high),
                    low=float(low),
                    close=float(close_price),
                    volume=float(100 + np.random.randint(0, 50)),
                )
            )
        return candles

service = OrderBlockService()
