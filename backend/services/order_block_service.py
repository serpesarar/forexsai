from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

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
        self._data_hub_task: asyncio.Task | None = None

    @staticmethod
    def _get_field(item: Any, key: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(key, default)
        return getattr(item, key, default)

    @classmethod
    def _normalize_reason_lists(cls, combined_signal: dict | None) -> dict:
        payload = dict(combined_signal or {})
        reasons = payload.get("reasons")
        reasoning = payload.get("reasoning")

        if not isinstance(reasons, list):
            reasons = list(reasoning) if isinstance(reasoning, list) else []
        if not isinstance(reasoning, list):
            reasoning = list(reasons)

        payload["reasons"] = reasons
        payload["reasoning"] = reasoning
        return payload

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
    def _normalize_market_symbol(symbol: str) -> str:
        sym = (symbol or "").strip().upper()
        aliases = {
            "NASDAQ": "NDX.INDX",
            "NAS100": "NDX.INDX",
            "NDX": "NDX.INDX",
            "NDX.INDX": "NDX.INDX",
            "DAX": "GDAXI.INDX",
            "GDAXI": "GDAXI.INDX",
            "GDAXI.INDX": "GDAXI.INDX",
            "XAU": "XAUUSD",
            "XAUUSD": "XAUUSD",
            "USOIL": "USOIL.FOREX",
            "WTI": "USOIL.FOREX",
            "CL": "USOIL.FOREX",
            "USOIL.FOREX": "USOIL.FOREX",
        }
        return aliases.get(sym, symbol)

    @staticmethod
    def _rows_to_candles(rows: List[dict]) -> List[Candle]:
        candles: List[Candle] = []
        for idx, row in enumerate(rows):
            candles.append(
                Candle(
                    timestamp=float(row.get("timestamp") or idx),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume") or 0.0),
                )
            )
        return candles

    def _enrich_order_blocks(self, structure: Any, n: int = 0) -> List[Dict[str, Any]]:
        enriched_obs: List[Dict[str, Any]] = []
        choch_list = list(self._get_field(structure, "choch_list", []) or [])
        bos_list = list(self._get_field(structure, "bos_list", []) or [])
        fvg_list = list(self._get_field(structure, "fvg_list", []) or [])
        recent_start = max(0, n - 15) if n > 0 else 0

        for ob in list(self._get_field(structure, "ob_list", []) or [])[:10]:
            ob_dict = ob.to_dict()
            ob_index = int(self._get_field(ob, "index", -1) or -1)
            ob_type = self._get_field(ob, "type")

            def _near_ob_or_recent(idx):
                return (ob_index <= idx <= ob_index + 15) or (n > 0 and idx >= recent_start)

            bullish_choch = any(
                _near_ob_or_recent(self._get_field(c, "index", -1))
                and self._get_field(c, "type") == "bullish"
                for c in choch_list
            )
            bearish_choch = any(
                _near_ob_or_recent(self._get_field(c, "index", -1))
                and self._get_field(c, "type") == "bearish"
                for c in choch_list
            )
            bullish_bos = any(
                _near_ob_or_recent(self._get_field(b, "index", -1))
                and self._get_field(b, "type") == "bullish"
                for b in bos_list
            )
            bearish_bos = any(
                _near_ob_or_recent(self._get_field(b, "index", -1))
                and self._get_field(b, "type") == "bearish"
                for b in bos_list
            )
            bullish_fvg = any(
                _near_ob_or_recent(self._get_field(f, "index", -1))
                and self._get_field(f, "direction") == "bullish"
                for f in fvg_list
            )
            bearish_fvg = any(
                _near_ob_or_recent(self._get_field(f, "index", -1))
                and self._get_field(f, "direction") == "bearish"
                for f in fvg_list
            )

            ob_dict["has_bullish_choch"] = bullish_choch
            ob_dict["has_bearish_choch"] = bearish_choch
            ob_dict["has_bullish_bos"] = bullish_bos
            ob_dict["has_bearish_bos"] = bearish_bos
            ob_dict["has_bullish_fvg"] = bullish_fvg
            ob_dict["has_bearish_fvg"] = bearish_fvg
            if ob_type == "bullish":
                ob_dict["has_choch"] = bullish_choch
                ob_dict["has_bos"] = bullish_bos
                ob_dict["has_fvg"] = bullish_fvg
            else:
                ob_dict["has_choch"] = bearish_choch
                ob_dict["has_bos"] = bearish_bos
                ob_dict["has_fvg"] = bearish_fvg
            enriched_obs.append(ob_dict)

        return enriched_obs

    async def _ensure_backtest_data_ready(self) -> None:
        from services.data_hub import get_hub_status, start_data_hub

        status = get_hub_status()
        if status.get("running"):
            return

        if self._data_hub_task is None or self._data_hub_task.done():
            self._data_hub_task = asyncio.create_task(start_data_hub())

        await asyncio.sleep(0.1)

    async def _fetch_candles_for_backtest(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        """
        Fetch real candles using EODH data source.
        Mirror the exact fetch pattern used in detect() — do NOT use synthetic fallback here.
        If data is unavailable, return empty list (caller handles it).
        """
        normalized_symbol = self._normalize_market_symbol(symbol)
        try:
            await self._ensure_backtest_data_ready()
            for _ in range(20):
                data = await fetch_ohlc_data(normalized_symbol, timeframe=timeframe, limit=limit)
                if not data:
                    data = await fetch_eod_candles(normalized_symbol, limit=limit)
                if data:
                    return self._rows_to_candles(data)
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Backtest data fetch failed: {e}")
            return []
        return []

    @staticmethod
    def _calc_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        n = len(closes)
        if n < 2:
            return float(closes[-1]) * 0.001 if n else 1.0
        trs = []
        for i in range(1, n):
            tr = max(
                float(highs[i]) - float(lows[i]),
                abs(float(highs[i]) - float(closes[i - 1])),
                abs(float(lows[i]) - float(closes[i - 1])),
            )
            trs.append(tr)
        if len(trs) < period:
            return float(trs[-1]) if trs else (float(closes[-1]) * 0.001 if n else 1.0)
        return float(np.mean(trs[-period:]))

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        if len(data) < period:
            return data.copy()
        ema = np.zeros_like(data, dtype=np.float64)
        ema[0] = float(data[0])
        k = 2.0 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = float(data[i]) * k + ema[i - 1] * (1 - k)
        return ema

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
                    clusters.append(
                        {
                            "center": price,
                            "prices": [price],
                            "indices": [idx],
                            "latest_idx": idx,
                        }
                    )
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
            levels.append(
                {
                    "type": "resistance",
                    "name": f"R{idx + 1}" + (f" (×{touches})" if touches >= 2 else ""),
                    "price": price,
                    "distance": round(distance, 1),
                    "distance_display": f"+{round(distance, 1)} {unit}",
                    "strength": "strong" if touches >= 2 else "normal",
                    "is_next": idx == 0,
                    "touch_count": touches,
                }
            )

        levels.append(
            {
                "type": "current",
                "name": "Current Price",
                "price": round(current_price, 2),
                "distance": 0,
                "distance_display": "HERE",
                "strength": "current",
            }
        )

        for idx, cluster in enumerate(sup_nearest):
            price = round(float(cluster["center"]), 2)
            distance = abs(price - current_price) / pip_value
            touches = int(cluster.get("touch_count", 1) or 1)
            levels.append(
                {
                    "type": "support",
                    "name": f"S{idx + 1}" + (f" (×{touches})" if touches >= 2 else ""),
                    "price": price,
                    "distance": round(distance, 1),
                    "distance_display": f"-{round(distance, 1)} {unit}",
                    "strength": "strong" if touches >= 2 else "normal",
                    "is_next": idx == 0,
                    "touch_count": touches,
                }
            )

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
        cache_key = f"v6:{symbol}:{timeframe}:{limit}:{config}"  # noqa: S608 - cache key
        if use_cache:
            with self._lock:
                cached = self._cache.get(cache_key)
                if cached and self._utc_now() - cached.timestamp < self.ttl:
                    return cached.payload

        candles, warning = await self._load_candles_with_warning(symbol=symbol, timeframe=timeframe, limit=limit)
        if warning:
            payload = {
                "symbol": symbol,
                "timeframe": timeframe,
                "total_order_blocks": 0,
                "bearish_obs": 0,
                "bullish_obs": 0,
                "order_blocks": [],
                "active_signals": [],
                "combined_signal": {
                    "action": "NEUTRAL",
                    "confidence": 0.0,
                    "reasoning": [warning],
                    "reasons": ["Synthetic fallback blocked"],
                },
                "structure": {
                    "choch": [],
                    "bos": [],
                    "fvg": [],
                    "order_blocks": [],
                    "trend": None,
                    "counts": {"choch": 0, "bos": 0, "fvg": 0, "ob": 0},
                },
                "choch_list": [],
                "bos_list": [],
                "fvg_list": [],
                "trend": None,
                "support_resistance": {
                    "all_levels": [],
                    "nearest_resistance": None,
                    "nearest_support": None,
                    "pivot": None,
                    "range_high": None,
                    "range_low": None,
                    "method": "swing_cluster_fib",
                },
                "timestamp": self._utc_now().isoformat().replace("+00:00", "Z"),
                "warning": warning,
            }
            with self._lock:
                self._cache[cache_key] = CacheEntry(timestamp=self._utc_now(), payload=payload)
            return payload

        # Use NEW detector with independent algorithms (symbol-aware TP/SL)
        structure = MarketStructureAnalyzer.analyze(candles, symbol=symbol)

        # Prepare enriched order blocks with structure info
        enriched_obs = self._enrich_order_blocks(structure, n=len(candles))

        current_price = float(getattr(candles[-1], "close", 0.0) or 0.0) if candles else 0.0
        combined_signal = self._normalize_reason_lists(
            await self._combine_signals(
                structure=structure,
                order_blocks=enriched_obs,
                current_price=current_price,
                candles=candles,
            )
        )
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
            "structure": structure.to_dict(),  # Full structure data
            "choch_list": [c.to_dict() for c in structure.choch_list],
            "bos_list": [b.to_dict() for b in structure.bos_list],
            "fvg_list": [f.to_dict() for f in structure.fvg_list],
            "swing_points": [
                {"index": s.index, "price": round(s.price, 2), "type": s.type}
                for s in structure.swing_list[-20:]
            ],
            "projection": structure.projection.to_dict() if structure.projection else None,
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

    async def backtest(self, request: Any) -> dict:
        """
        Real backtest implementation with rule-by-rule analysis.
        Simulates trading signals over historical data and tracks which rules correlate with wins/losses.
        """
        symbol = self._normalize_market_symbol(self._get_field(request, "symbol", "NDX.INDX"))
        timeframe = self._get_field(request, "timeframe", "5m")
        candles = await self._fetch_candles_for_backtest(symbol=symbol, timeframe=timeframe, limit=500)
        if not candles or len(candles) < 100:
            return {
                "error": "Insufficient data",
                "total_signals": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "wins": 0,
                "losses": 0,
                "results": [],
                "avg_risk_reward": 0.0,
                "total_profit": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "rule_performance": {},
                "grade": "N/A",
            }

        trades: List[dict[str, Any]] = []
        rule_stats: dict[str, dict[str, float | int]] = {}
        min_lookback = 100

        for i in range(min_lookback, len(candles) - 30):
            window = candles[: i + 1]
            future_candles = candles[i + 1 : i + 31]
            current_price = float(candles[i].close)
            structure = MarketStructureAnalyzer.analyze(window, symbol=symbol)

            enriched_obs = self._enrich_order_blocks(structure, n=len(window))

            signal = self._normalize_reason_lists(
                await self._combine_signals(
                    structure=structure,
                    order_blocks=enriched_obs,
                    current_price=current_price,
                    candles=window,
                )
            )

            direction = signal.get("action")
            if direction not in {"BUY", "SELL"}:
                continue

            atr = self._calc_atr(
                np.array([c.high for c in window[-20:]], dtype=np.float64),
                np.array([c.low for c in window[-20:]], dtype=np.float64),
                np.array([c.close for c in window[-20:]], dtype=np.float64),
                14,
            )
            entry_price = current_price
            reasons = list(signal.get("reasons") or [])

            if direction == "BUY":
                tp = entry_price + atr * 1.0
                sl = entry_price - atr * 2.0
            else:
                tp = entry_price - atr * 1.0
                sl = entry_price + atr * 2.0

            outcome = None
            exit_price = entry_price
            for candle in future_candles:
                candle_high = float(candle.high)
                candle_low = float(candle.low)
                candle_close = float(candle.close)
                if direction == "BUY":
                    if candle_low <= sl:
                        outcome = "loss"
                        exit_price = sl
                        break
                    if candle_high >= tp:
                        outcome = "win"
                        exit_price = tp
                        break
                else:
                    if candle_high >= sl:
                        outcome = "loss"
                        exit_price = sl
                        break
                    if candle_low <= tp:
                        outcome = "win"
                        exit_price = tp
                        break
                exit_price = candle_close

            if outcome is None:
                outcome = "timeout"

            pnl = (exit_price - entry_price) if direction == "BUY" else (entry_price - exit_price)
            risk_reward = abs(tp - entry_price) / abs(entry_price - sl) if sl != entry_price else 0.0
            trades.append(
                {
                    "signal": direction,
                    "entry": round(entry_price, 4),
                    "exit": round(exit_price, 4),
                    "outcome": outcome,
                    "reasons": reasons,
                    "pnl": round(pnl, 4),
                    "risk_reward": risk_reward,
                }
            )

            for reason in reasons:
                if reason not in rule_stats:
                    rule_stats[reason] = {"wins": 0, "losses": 0, "timeouts": 0, "total_pnl": 0.0}
                if outcome == "win":
                    rule_stats[reason]["wins"] += 1
                elif outcome == "loss":
                    rule_stats[reason]["losses"] += 1
                else:
                    rule_stats[reason]["timeouts"] += 1
                rule_stats[reason]["total_pnl"] += pnl

        if not trades:
            return {
                "total_signals": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "wins": 0,
                "losses": 0,
                "results": [],
                "avg_risk_reward": 0.0,
                "total_profit": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "rule_performance": {},
                "grade": "N/A",
            }

        wins = sum(1 for trade in trades if trade["outcome"] == "win")
        losses = sum(1 for trade in trades if trade["outcome"] == "loss")
        total = len(trades)
        total_profit = float(sum(float(trade["pnl"]) for trade in trades))
        avg_risk_reward = float(sum(float(trade["risk_reward"]) for trade in trades) / total) if total else 0.0

        equity_curve = 0.0
        peak_equity = 0.0
        max_drawdown = 0.0
        returns: List[float] = []
        for trade in trades:
            trade_pnl = float(trade["pnl"])
            returns.append(trade_pnl)
            equity_curve += trade_pnl
            peak_equity = max(peak_equity, equity_curve)
            max_drawdown = max(max_drawdown, peak_equity - equity_curve)

        avg_return = float(np.mean(returns)) if returns else 0.0
        std_return = float(np.std(returns)) if len(returns) > 1 else 0.0
        sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0.0

        rule_performance: dict[str, dict[str, Any]] = {}
        for rule, stats in sorted(
            rule_stats.items(),
            key=lambda item: int(item[1]["wins"]) + int(item[1]["losses"]) + int(item[1].get("timeouts", 0)),
            reverse=True,
        ):
            count = int(stats["wins"]) + int(stats["losses"]) + int(stats.get("timeouts", 0))
            rule_win_rate = (int(stats["wins"]) / count) * 100 if count else 0.0
            total_rule_pnl = float(stats["total_pnl"])
            grade = "A" if rule_win_rate >= 60 and total_rule_pnl > 0 else "B" if rule_win_rate >= 50 else "C" if rule_win_rate >= 40 else "D"
            rule_performance[rule] = {
                "win_rate": round(rule_win_rate, 1),
                "count": count,
                "wins": int(stats["wins"]),
                "losses": int(stats["losses"]),
                "timeouts": int(stats.get("timeouts", 0)),
                "total_pnl": round(total_rule_pnl, 2),
                "grade": grade,
            }

        overall_win_rate = (wins / total) * 100 if total else 0.0
        grade = "A" if overall_win_rate >= 60 and total_profit > 0 else "B" if overall_win_rate >= 50 else "C" if overall_win_rate >= 40 else "D"

        return {
            "total_signals": total,
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(overall_win_rate, 1),
            "timeouts": sum(1 for trade in trades if trade["outcome"] == "timeout"),
            "results": [{"signal": trade["signal"], "entry": trade["entry"], "exit": trade["exit"], "outcome": trade["outcome"], "pnl": trade["pnl"]} for trade in trades[-50:]],
            "avg_risk_reward": round(avg_risk_reward, 2),
            "total_profit": round(total_profit, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "rule_performance": rule_performance,
            "grade": grade,
        }

    async def _combine_signals(
        self,
        structure=None,
        order_blocks: List[Dict[str, Any]] | None = None,
        current_price: float = 0.0,
        candles: List | None = None,
    ) -> dict:
        _neutral = {
            "action": "NEUTRAL",
            "confidence": 0.40,
            "reasoning": ["Insufficient data"],
            "reasons": [],
        }
        if not structure:
            return _neutral

        order_blocks = order_blocks or []
        n = len(candles) if candles else 0

        # ── 1. LOCAL TREND — last 100 candles only (avoid lagging full-history EMA) ──
        if candles and n >= 50:
            local_n = min(100, n)
            local_closes = np.array(
                [c.close for c in candles[-local_n:]], dtype=np.float64
            )
            ema10 = self._ema(local_closes, 10)
            ema30 = self._ema(local_closes, 30)
            ema_bullish = ema10[-1] > ema30[-1]
            ema_bearish = ema10[-1] < ema30[-1]
            ema_slope = (
                (ema10[-1] - ema10[-5]) / ema10[-5] * 100
                if len(ema10) >= 5
                else 0.0
            )
        else:
            ema_bullish = False
            ema_bearish = False
            ema_slope = 0.0

        struct_trend = self._get_field(structure, "trend", "ranging")
        if ema_bullish and (struct_trend == "bullish" or ema_slope > 0.02):
            trend = "bullish"
        elif ema_bearish and (struct_trend == "bearish" or ema_slope < -0.02):
            trend = "bearish"
        else:
            trend = "ranging"

        # ── 2. PREMIUM / DISCOUNT ZONE ──
        if candles and n >= 50:
            lookback = min(100, n)
            range_high = max(c.high for c in candles[-lookback:])
            range_low = min(c.low for c in candles[-lookback:])
            range_size = range_high - range_low
            price_pct = (
                (current_price - range_low) / range_size if range_size > 0 else 0.5
            )
        else:
            price_pct = 0.5

        in_discount = price_pct < 0.5
        in_premium = price_pct > 0.5
        deep_discount = price_pct < 0.3
        deep_premium = price_pct > 0.7

        # ── 3. OB PROXIMITY FILTER (recency removed — proximity naturally filters stale OBs) ──
        bullish_obs = [
            ob
            for ob in order_blocks
            if self._get_field(ob, "type") == "bullish"
            and not self._get_field(ob, "mitigated", False)
            and self._get_field(ob, "score", 0) >= 50
            and self._get_field(ob, "zone_low", 0.0)
            <= current_price
            <= self._get_field(ob, "zone_high", 0.0) * 1.005
        ]

        bearish_obs = [
            ob
            for ob in order_blocks
            if self._get_field(ob, "type") == "bearish"
            and not self._get_field(ob, "mitigated", False)
            and self._get_field(ob, "score", 0) >= 50
            and self._get_field(ob, "zone_low", 0.0) * 0.995
            <= current_price
            <= self._get_field(ob, "zone_high", 0.0)
        ]

        # ── 4. BULLISH SCORING ──
        bull_score = 0
        bull_reasons: List[str] = []

        if bullish_obs and trend != "bearish" and in_discount:
            best = max(bullish_obs, key=lambda x: self._get_field(x, "score", 0))
            bull_score += 25
            bull_reasons.append("bullish OB in discount")

            if self._get_field(best, "strength") == "strong":
                bull_score += 15
                bull_reasons.append("strong OB")
            elif self._get_field(best, "strength") == "moderate":
                bull_score += 8

            if deep_discount:
                bull_score += 10
                bull_reasons.append("deep discount")

            conf = 0
            if self._get_field(best, "has_bullish_choch", False):
                conf += 1
                bull_score += 10
                bull_reasons.append("CHoCH confirms")
            if self._get_field(best, "has_bullish_bos", False):
                conf += 1
                bull_score += 8
                bull_reasons.append("BOS confirms")
            if self._get_field(best, "has_bullish_fvg", False):
                conf += 1
                bull_score += 8
                bull_reasons.append("FVG confluence")
            if self._get_field(best, "tested", False):
                bull_score += 5
                bull_reasons.append("OB revisited")

            if conf == 0:
                bull_score -= 20
                bull_reasons.append("no struct confirmation")

        # ── 5. BEARISH SCORING ──
        bear_score = 0
        bear_reasons: List[str] = []

        if bearish_obs and trend != "bullish" and in_premium:
            best = max(bearish_obs, key=lambda x: self._get_field(x, "score", 0))
            bear_score += 25
            bear_reasons.append("bearish OB in premium")

            if self._get_field(best, "strength") == "strong":
                bear_score += 15
                bear_reasons.append("strong OB")
            elif self._get_field(best, "strength") == "moderate":
                bear_score += 8

            if deep_premium:
                bear_score += 10
                bear_reasons.append("deep premium")

            conf = 0
            if self._get_field(best, "has_bearish_choch", False):
                conf += 1
                bear_score += 10
                bear_reasons.append("CHoCH confirms")
            if self._get_field(best, "has_bearish_bos", False):
                conf += 1
                bear_score += 8
                bear_reasons.append("BOS confirms")
            if self._get_field(best, "has_bearish_fvg", False):
                conf += 1
                bear_score += 8
                bear_reasons.append("FVG confluence")
            if self._get_field(best, "tested", False):
                bear_score += 5
                bear_reasons.append("OB revisited")

            if conf == 0:
                bear_score -= 20
                bear_reasons.append("no struct confirmation")

        # ── 6. Recent CHoCH boost ──
        choch_list = self._get_field(structure, "choch_list", []) or []
        if choch_list:
            latest = choch_list[-1]
            age = self._get_field(latest, "candle_index_ago", 99)
            if age <= 8:
                ctype = self._get_field(latest, "type")
                if ctype == "bullish" and bull_score > 0:
                    bull_score += 10
                    bull_reasons.append("fresh CHoCH")
                elif ctype == "bearish" and bear_score > 0:
                    bear_score += 10
                    bear_reasons.append("fresh CHoCH")

        # ── 7. FVG magnet (closest only, requires OB base) ──
        fvg_list = self._get_field(structure, "fvg_list", []) or []
        bull_fvg_added = False
        bear_fvg_added = False
        best_bull_fvg_dist = 1.0
        best_bear_fvg_dist = 1.0
        for fvg in fvg_list:
            if self._get_field(fvg, "filled", False):
                continue
            mid = self._get_field(fvg, "mid", 0.0)
            if mid == 0.0:
                continue
            dist_pct = abs(current_price - mid) / current_price if current_price else 1.0
            if dist_pct < 0.003:
                fvg_dir = self._get_field(fvg, "direction")
                if fvg_dir == "bullish" and not bull_fvg_added and bull_score > 0 and dist_pct < best_bull_fvg_dist:
                    best_bull_fvg_dist = dist_pct
                    bull_fvg_added = True
                    bull_score += 5
                    bull_reasons.append("FVG magnet")
                elif fvg_dir == "bearish" and not bear_fvg_added and bear_score > 0 and dist_pct < best_bear_fvg_dist:
                    best_bear_fvg_dist = dist_pct
                    bear_fvg_added = True
                    bear_score += 5
                    bear_reasons.append("FVG magnet")

        # ── 8. Candle rejection confirmation ──
        if candles and n >= 2:
            last = candles[-1]
            full_range = last.high - last.low
            if full_range > 0:
                lower_wick = min(last.open, last.close) - last.low
                upper_wick = last.high - max(last.open, last.close)
                if lower_wick / full_range > 0.5 and bull_score > 0:
                    bull_score += 8
                    bull_reasons.append("rejection candle")
                if upper_wick / full_range > 0.5 and bear_score > 0:
                    bear_score += 8
                    bear_reasons.append("rejection candle")

        # ── 9. DECISION (symmetric thresholds for balanced signals) ──
        bull_threshold = 60
        bear_threshold = 60

        bull_pass = bull_score >= bull_threshold
        bear_pass = bear_score >= bear_threshold

        if bull_pass and bear_pass:
            action = "NEUTRAL"
            score = 0
            reasons: List[str] = ["conflicting signals"]
        elif bull_pass:
            action = "BUY"
            score = bull_score
            reasons = bull_reasons
        elif bear_pass:
            action = "SELL"
            score = -bear_score
            reasons = bear_reasons
        else:
            action = "NEUTRAL"
            score = 0
            reasons = []

        confidence = min(0.95, 0.40 + abs(score) / 180)
        reasoning = (
            [f"Confluence score: {score}", *reasons]
            if reasons
            else [f"Confluence score: {score}"]
        )

        return {
            "action": action,
            "confidence": round(float(confidence), 2),
            "reasoning": reasoning,
            "reasons": reasons,
        }

    async def _load_candles_with_warning(self, symbol: str, timeframe: str, limit: int) -> Tuple[List[Candle], Optional[str]]:
        """Load reliable candles and block synthetic fallback for analytical endpoints."""
        candles = await self._load_candles(symbol=symbol, timeframe=timeframe, limit=limit)
        if candles:
            return candles, None
        return [], f"No reliable candle data available for {symbol} on {timeframe}. Synthetic fallback was blocked."

    async def _load_candles(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        """
        Load candles from DataHub for the requested timeframe.
        Falls back: requested tf → EOD → empty.
        DataHub supports: 5m, 15m, 30m, 1h, 4h, eod
        """
        symbol = self._normalize_market_symbol(symbol)
        # Try requested timeframe first
        data = await fetch_ohlc_data(symbol, timeframe=timeframe, limit=limit)

        # Fallback to EOD if the requested timeframe returned nothing
        if not data:
            data = await fetch_eod_candles(symbol, limit=limit)

        if data:
            return self._rows_to_candles(data)

        return []

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
