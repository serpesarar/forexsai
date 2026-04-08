from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

HARMONIC_PATTERNS: Dict[str, Dict[str, Any]] = {
    "GARTLEY": {"name": "Gartley", "name_tr": "Gartley", "B": {"min": 0.55, "max": 0.68, "ideal": 0.618}, "C": {"min": 0.382, "max": 0.886, "ideal": 0.618}, "D_XA": {"min": 0.746, "max": 0.826, "ideal": 0.786}, "D_BC": {"min": 1.272, "max": 1.618, "ideal": 1.272}},
    "BUTTERFLY": {"name": "Butterfly", "name_tr": "Kelebek", "B": {"min": 0.72, "max": 0.85, "ideal": 0.786}, "C": {"min": 0.382, "max": 0.886, "ideal": 0.618}, "D_XA": {"min": 1.20, "max": 1.68, "ideal": 1.272}, "D_BC": {"min": 1.618, "max": 2.618, "ideal": 1.618}},
    "BAT": {"name": "Bat", "name_tr": "Yarasa", "B": {"min": 0.35, "max": 0.55, "ideal": 0.382}, "C": {"min": 0.382, "max": 0.886, "ideal": 0.618}, "D_XA": {"min": 0.82, "max": 0.92, "ideal": 0.886}, "D_BC": {"min": 1.618, "max": 2.618, "ideal": 2.0}},
    "CRAB": {"name": "Crab", "name_tr": "Yengeç", "B": {"min": 0.35, "max": 0.65, "ideal": 0.618}, "C": {"min": 0.382, "max": 0.886, "ideal": 0.618}, "D_XA": {"min": 1.55, "max": 1.70, "ideal": 1.618}, "D_BC": {"min": 2.618, "max": 3.618, "ideal": 2.618}},
    "DEEP_CRAB": {"name": "Deep Crab", "name_tr": "Derin Yengeç", "B": {"min": 0.82, "max": 0.92, "ideal": 0.886}, "C": {"min": 0.382, "max": 0.886, "ideal": 0.618}, "D_XA": {"min": 1.55, "max": 1.70, "ideal": 1.618}, "D_BC": {"min": 2.0, "max": 3.618, "ideal": 2.618}},
    "SHARK": {"name": "Shark", "name_tr": "Köpekbalığı", "B": {"min": 0.35, "max": 0.65, "ideal": 0.446}, "C": {"min": 1.08, "max": 1.68, "ideal": 1.13}, "D_XA": {"min": 0.82, "max": 0.92, "ideal": 0.886}, "D_BC": {"min": 1.618, "max": 2.236, "ideal": 1.618}},
    "CYPHER": {"name": "Cypher", "name_tr": "Şifre", "B": {"min": 0.382, "max": 0.618, "ideal": 0.382}, "C": {"min": 1.13, "max": 1.414, "ideal": 1.272}, "D_XA": {"min": 0.72, "max": 0.82, "ideal": 0.786}, "D_BC": {"min": 1.272, "max": 2.0, "ideal": 1.414}},
    "THREE_DRIVES": {"name": "Three Drives", "name_tr": "Üç Sürüş", "B": {"min": 0.55, "max": 0.72, "ideal": 0.618}, "C": {"min": 1.20, "max": 1.68, "ideal": 1.272}, "D_XA": {"min": 1.20, "max": 1.68, "ideal": 1.272}, "D_BC": {"min": 0.55, "max": 0.72, "ideal": 0.618}},
}

CLASSIC_PATTERNS: Dict[str, Dict[str, str]] = {
    "DOUBLE_TOP": {"name": "Double Top", "name_tr": "Çift Tepe"},
    "DOUBLE_BOTTOM": {"name": "Double Bottom", "name_tr": "Çift Dip"},
    "ASCENDING_TRIANGLE": {"name": "Ascending Triangle", "name_tr": "Yükselen Üçgen"},
    "DESCENDING_TRIANGLE": {"name": "Descending Triangle", "name_tr": "Alçalan Üçgen"},
    "HEAD_SHOULDERS": {"name": "Head & Shoulders", "name_tr": "Omuz Baş Omuz"},
    "INV_HEAD_SHOULDERS": {"name": "Inv. Head & Shoulders", "name_tr": "Ters Omuz Baş Omuz"},
    "RISING_WEDGE": {"name": "Rising Wedge", "name_tr": "Yükselen Kama"},
    "FALLING_WEDGE": {"name": "Falling Wedge", "name_tr": "Düşen Kama"},
    "TRIPLE_TOP": {"name": "Triple Top", "name_tr": "Üçlü Tepe"},
    "TRIPLE_BOTTOM": {"name": "Triple Bottom", "name_tr": "Üçlü Dip"},
}

DEFAULT_OPTIONS: Dict[str, float] = {"deviation": 0.015, "fib_tolerance": 0.04, "min_confidence": 25.0}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _as_unix(value: Any, fallback: int) -> int:
    if value is None:
        return fallback
    if isinstance(value, (int, float)):
        numeric = int(value)
        return numeric // 1000 if numeric > 10_000_000_000 else numeric
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return fallback
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return int(datetime.fromisoformat(text).timestamp())
        except Exception:
            return fallback
    return fallback


def _normalize_timeframe(timeframe: str) -> str:
    text = (timeframe or "4h").strip().lower()
    aliases = {"4H": "4h", "1H": "1h", "30M": "30m", "15M": "15m", "5M": "5m"}
    return aliases.get(timeframe, text)


def _normalize_candles(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for idx, candle in enumerate(candles or []):
        open_price = _as_float(candle.get("open", candle.get("o")))
        high_price = _as_float(candle.get("high", candle.get("h")))
        low_price = _as_float(candle.get("low", candle.get("l")))
        close_price = _as_float(candle.get("close", candle.get("c")))
        if high_price <= 0 or low_price <= 0:
            continue
        normalized.append(
            {
                "time": _as_unix(candle.get("time", candle.get("timestamp", candle.get("date", candle.get("datetime")))), idx),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": _as_float(candle.get("volume", candle.get("v"))),
                "index": idx,
            }
        )
    return normalized


def _find_pivots(candles: List[Dict[str, Any]], deviation: float) -> List[Dict[str, Any]]:
    if len(candles) < 5:
        return []
    pivots: List[Dict[str, Any]] = []
    last_pivot_high = candles[0]["high"]
    last_pivot_low = candles[0]["low"]
    trend = 0
    for idx in range(2, len(candles) - 2):
        prev2, prev1, curr, next1, next2 = candles[idx - 2], candles[idx - 1], candles[idx], candles[idx + 1], candles[idx + 2]
        is_pivot_high = curr["high"] >= prev1["high"] and curr["high"] >= prev2["high"] and curr["high"] >= next1["high"] and curr["high"] >= next2["high"]
        is_pivot_low = curr["low"] <= prev1["low"] and curr["low"] <= prev2["low"] and curr["low"] <= next1["low"] and curr["low"] <= next2["low"]
        if is_pivot_high:
            change = abs(curr["high"] - last_pivot_low) / max(last_pivot_low, 1e-9)
            if change >= deviation:
                if trend == 1 and pivots and pivots[-1]["type"] == "high":
                    if curr["high"] > pivots[-1]["high"]:
                        pivots.pop()
                    else:
                        is_pivot_high = False
                if is_pivot_high:
                    pivots.append({"time": curr["time"], "price": curr["high"], "high": curr["high"], "low": curr["low"], "type": "high", "index": idx})
                    last_pivot_high = curr["high"]
                    trend = 1
        if is_pivot_low:
            change = abs(last_pivot_high - curr["low"]) / max(last_pivot_high, 1e-9)
            if change >= deviation:
                if trend == -1 and pivots and pivots[-1]["type"] == "low":
                    if curr["low"] < pivots[-1]["low"]:
                        pivots.pop()
                    else:
                        is_pivot_low = False
                if is_pivot_low:
                    pivots.append({"time": curr["time"], "price": curr["low"], "high": curr["high"], "low": curr["low"], "type": "low", "index": idx})
                    last_pivot_low = curr["low"]
                    trend = -1
    return pivots


def _in_range(value: float, definition: Dict[str, float], tolerance: float) -> bool:
    return value >= definition["min"] - tolerance and value <= definition["max"] + tolerance


def _range_score(value: float, definition: Dict[str, float]) -> int:
    if value < definition["min"] or value > definition["max"]:
        distance = definition["min"] - value if value < definition["min"] else value - definition["max"]
        return max(0, int(80 - distance * 300))
    span = definition["max"] - definition["min"]
    if span == 0:
        return 100
    normalized = abs(value - definition["ideal"]) / span
    return int(round(100 - normalized * 40))


def _indices_between(start_idx: int, end_idx: int) -> List[int]:
    lo = min(start_idx, end_idx)
    hi = max(start_idx, end_idx)
    return list(range(lo, hi + 1))


def _serialize_point(point: Dict[str, Any]) -> Dict[str, Any]:
    return {"time": point["time"], "price": round(point["price"], 4), "type": point["type"], "index": point["index"]}


def _build_pattern(pattern_type: str, definition: Dict[str, Any], timeframe: str, direction: str, confidence: int, status: str, candle_indices: List[int], points: Dict[str, Dict[str, Any]], target_price: float | None = None, stop_loss: float | None = None, fib_ratios: Dict[str, float] | None = None, projected: Dict[str, Any] | None = None) -> Dict[str, Any]:
    signal = direction.lower()
    pattern: Dict[str, Any] = {
        "type": pattern_type,
        "name": definition["name"],
        "name_tr": definition.get("name_tr", definition["name"]),
        "timeframe": timeframe,
        "category": "harmonic" if len(points) == 5 else "classic",
        "pattern_source": "harmonic_visualizer_4h",
        "signal": signal,
        "direction": direction,
        "confidence": int(confidence),
        "status": status,
        "candle_indices": candle_indices,
        "points": {label: _serialize_point(point) for label, point in points.items()},
    }
    if target_price is not None:
        pattern["target_price"] = round(target_price, 2)
    if stop_loss is not None:
        pattern["stop_loss"] = round(stop_loss, 2)
    if fib_ratios is not None:
        pattern["fib_ratios"] = fib_ratios
    if projected is not None:
        pattern["projected_d"] = projected
    return pattern


def _dedupe_harmonics(patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    for pattern in patterns:
        has_overlap = False
        for existing in unique:
            if existing["type"] != pattern["type"]:
                continue
            existing_d = existing.get("points", {}).get("D", {})
            current_d = pattern.get("points", {}).get("D", {})
            existing_x = existing.get("points", {}).get("X", {})
            current_x = pattern.get("points", {}).get("X", {})
            if abs(existing_d.get("index", -999) - current_d.get("index", 999)) <= 8 and abs(existing_x.get("index", -999) - current_x.get("index", 999)) <= 8:
                has_overlap = True
                break
        if not has_overlap:
            unique.append(pattern)
    return unique


def _dedupe_classics(patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    for pattern in patterns:
        if not any(existing["type"] == pattern["type"] and abs(existing["candle_indices"][-1] - pattern["candle_indices"][-1]) <= 8 for existing in unique):
            unique.append(pattern)
    return unique


def _detect_harmonic_patterns(candles: List[Dict[str, Any]], timeframe: str, deviation: float, fib_tolerance: float, min_confidence: float) -> List[Dict[str, Any]]:
    pivots = _find_pivots(candles, deviation)
    if len(pivots) < 4:
        return []
    patterns: List[Dict[str, Any]] = []
    max_idx = len(pivots)
    for xi in range(max_idx - 3):
        x_point = pivots[xi]
        for ai in range(xi + 1, min(xi + 4, max_idx)):
            a_point = pivots[ai]
            if x_point["type"] == a_point["type"]:
                continue
            xa = abs(a_point["price"] - x_point["price"])
            if xa == 0:
                continue
            for bi in range(ai + 1, min(ai + 4, max_idx)):
                b_point = pivots[bi]
                if b_point["type"] == a_point["type"]:
                    continue
                ab = abs(b_point["price"] - a_point["price"])
                if ab == 0:
                    continue
                ab_ratio = ab / xa
                for ci in range(bi + 1, min(bi + 4, max_idx)):
                    c_point = pivots[ci]
                    if c_point["type"] == b_point["type"]:
                        continue
                    bc = abs(c_point["price"] - b_point["price"])
                    if bc == 0:
                        continue
                    bc_ratio = bc / ab
                    for di in range(ci + 1, min(ci + 4, max_idx)):
                        d_point = pivots[di]
                        if d_point["type"] == c_point["type"]:
                            continue
                        cd = abs(d_point["price"] - c_point["price"])
                        ad = abs(d_point["price"] - x_point["price"])
                        cd_ratio = cd / bc if bc > 0 else 0
                        xd_ratio = ad / xa if xa > 0 else 0
                        for pattern_type, definition in HARMONIC_PATTERNS.items():
                            if not _in_range(ab_ratio, definition["B"], fib_tolerance) or not _in_range(bc_ratio, definition["C"], fib_tolerance):
                                continue
                            d_xa_ok = _in_range(xd_ratio, definition["D_XA"], fib_tolerance)
                            d_bc_ok = _in_range(cd_ratio, definition["D_BC"], fib_tolerance)
                            if not d_xa_ok and not d_bc_ok:
                                continue
                            scores = [_range_score(ab_ratio, definition["B"]), _range_score(bc_ratio, definition["C"])]
                            if d_xa_ok:
                                scores.append(_range_score(xd_ratio, definition["D_XA"]))
                            if d_bc_ok:
                                scores.append(_range_score(cd_ratio, definition["D_BC"]))
                            confidence = int(round(sum(scores) / len(scores)))
                            if confidence < min_confidence:
                                continue
                            direction = "BULLISH" if x_point["type"] == "low" else "BEARISH"
                            ad_leg = abs(d_point["price"] - a_point["price"])
                            target_price = d_point["price"] + ad_leg * 0.618 if direction == "BULLISH" else d_point["price"] - ad_leg * 0.618
                            stop_loss = d_point["price"] - abs(d_point["price"] - x_point["price"]) * 0.1 if direction == "BULLISH" else d_point["price"] + abs(d_point["price"] - x_point["price"]) * 0.1
                            patterns.append(_build_pattern(pattern_type, definition, timeframe, direction, confidence, "COMPLETED", _indices_between(x_point["index"], d_point["index"]), {"X": x_point, "A": a_point, "B": b_point, "C": c_point, "D": d_point}, target_price, stop_loss, {"ab": round(ab_ratio, 3), "bc": round(bc_ratio, 3), "cd": round(cd_ratio, 3), "xd": round(xd_ratio, 3)}))
                    if ci >= max_idx - 10:
                        for pattern_type, definition in HARMONIC_PATTERNS.items():
                            if not _in_range(ab_ratio, definition["B"], fib_tolerance) or not _in_range(bc_ratio, definition["C"], fib_tolerance):
                                continue
                            confidence = int(round((_range_score(ab_ratio, definition["B"]) + _range_score(bc_ratio, definition["C"])) / 2 * 0.7))
                            if confidence < min_confidence:
                                continue
                            d_xa_ideal = definition["D_XA"]["ideal"]
                            projected_price = a_point["price"] - xa * d_xa_ideal if a_point["price"] > x_point["price"] else a_point["price"] + xa * d_xa_ideal
                            duration = c_point["index"] - b_point["index"]
                            projected_index = min(len(candles) - 1, c_point["index"] + max(duration, 1))
                            synthetic_d = {"time": candles[projected_index]["time"], "price": projected_price, "high": projected_price, "low": projected_price, "type": "low" if c_point["type"] == "high" else "high", "index": projected_index}
                            direction = "BULLISH" if x_point["type"] == "low" else "BEARISH"
                            patterns.append(_build_pattern(pattern_type, definition, timeframe, direction, confidence, "FORMING", _indices_between(x_point["index"], c_point["index"]), {"X": x_point, "A": a_point, "B": b_point, "C": c_point, "D": synthetic_d}, None, None, {"ab": round(ab_ratio, 3), "bc": round(bc_ratio, 3), "cd": 0.0, "xd": round(d_xa_ideal, 3)}, {"price": round(projected_price, 2), "time": candles[projected_index]["time"]}))
    patterns.sort(key=lambda item: item["confidence"], reverse=True)
    return _dedupe_harmonics(patterns)


def _detect_classic_patterns(candles: List[Dict[str, Any]], timeframe: str, min_confidence: float) -> List[Dict[str, Any]]:
    if len(candles) < 20:
        return []
    highs: List[Dict[str, Any]] = []
    lows: List[Dict[str, Any]] = []
    for idx in range(2, len(candles) - 2):
        curr = candles[idx]
        if curr["high"] > candles[idx - 1]["high"] and curr["high"] > candles[idx - 2]["high"] and curr["high"] > candles[idx + 1]["high"] and curr["high"] > candles[idx + 2]["high"]:
            highs.append({"time": curr["time"], "price": curr["high"], "high": curr["high"], "low": curr["low"], "type": "high", "index": idx})
        if curr["low"] < candles[idx - 1]["low"] and curr["low"] < candles[idx - 2]["low"] and curr["low"] < candles[idx + 1]["low"] and curr["low"] < candles[idx + 2]["low"]:
            lows.append({"time": curr["time"], "price": curr["low"], "high": curr["high"], "low": curr["low"], "type": "low", "index": idx})
    patterns: List[Dict[str, Any]] = []
    for idx in range(len(highs) - 1):
        h1, h2 = highs[idx], highs[idx + 1]
        price_diff = abs(h1["price"] - h2["price"]) / max(h1["price"], 1e-9)
        time_dist = h2["index"] - h1["index"]
        confidence = int(round((1 - price_diff / 0.025) * 75 + 25)) if price_diff < 0.025 and 5 <= time_dist <= len(candles) * 0.8 else 0
        if confidence >= min_confidence:
            between = candles[h1["index"]:h2["index"] + 1]
            neckline = min(item["low"] for item in between)
            top_avg = (h1["price"] + h2["price"]) / 2
            height = top_avg - neckline
            patterns.append(_build_pattern("DOUBLE_TOP", CLASSIC_PATTERNS["DOUBLE_TOP"], timeframe, "BEARISH", confidence, "COMPLETED", _indices_between(h1["index"], h2["index"]), {"A": h1, "B": h2}, neckline - height, top_avg))
    for idx in range(len(lows) - 1):
        l1, l2 = lows[idx], lows[idx + 1]
        price_diff = abs(l1["price"] - l2["price"]) / max(l1["price"], 1e-9)
        time_dist = l2["index"] - l1["index"]
        confidence = int(round((1 - price_diff / 0.025) * 75 + 25)) if price_diff < 0.025 and 5 <= time_dist <= len(candles) * 0.8 else 0
        if confidence >= min_confidence:
            between = candles[l1["index"]:l2["index"] + 1]
            neckline = max(item["high"] for item in between)
            bottom_avg = (l1["price"] + l2["price"]) / 2
            height = neckline - bottom_avg
            patterns.append(_build_pattern("DOUBLE_BOTTOM", CLASSIC_PATTERNS["DOUBLE_BOTTOM"], timeframe, "BULLISH", confidence, "COMPLETED", _indices_between(l1["index"], l2["index"]), {"A": l1, "B": l2}, neckline + height, bottom_avg))

    for idx in range(len(highs) - 2):
        left_shoulder, head, right_shoulder = highs[idx], highs[idx + 1], highs[idx + 2]
        shoulder_diff = abs(left_shoulder["price"] - right_shoulder["price"]) / max(left_shoulder["price"], 1e-9)
        if head["price"] > left_shoulder["price"] and head["price"] > right_shoulder["price"] and shoulder_diff < 0.035:
            confidence = int(round((1 - shoulder_diff / 0.035) * 70 + 30))
            if confidence >= min_confidence:
                shoulder_avg = (left_shoulder["price"] + right_shoulder["price"]) / 2
                head_height = head["price"] - shoulder_avg
                patterns.append(_build_pattern("HEAD_SHOULDERS", CLASSIC_PATTERNS["HEAD_SHOULDERS"], timeframe, "BEARISH", confidence, "COMPLETED", _indices_between(left_shoulder["index"], right_shoulder["index"]), {"A": left_shoulder, "B": head, "C": right_shoulder}, shoulder_avg - head_height, head["price"]))

    for idx in range(len(lows) - 2):
        left_shoulder, head, right_shoulder = lows[idx], lows[idx + 1], lows[idx + 2]
        shoulder_diff = abs(left_shoulder["price"] - right_shoulder["price"]) / max(left_shoulder["price"], 1e-9)
        if head["price"] < left_shoulder["price"] and head["price"] < right_shoulder["price"] and shoulder_diff < 0.035:
            confidence = int(round((1 - shoulder_diff / 0.035) * 70 + 30))
            if confidence >= min_confidence:
                shoulder_avg = (left_shoulder["price"] + right_shoulder["price"]) / 2
                head_depth = shoulder_avg - head["price"]
                patterns.append(_build_pattern("INV_HEAD_SHOULDERS", CLASSIC_PATTERNS["INV_HEAD_SHOULDERS"], timeframe, "BULLISH", confidence, "COMPLETED", _indices_between(left_shoulder["index"], right_shoulder["index"]), {"A": left_shoulder, "B": head, "C": right_shoulder}, shoulder_avg + head_depth, head["price"]))

    for idx in range(len(highs) - 2):
        h1, h2, h3 = highs[idx], highs[idx + 1], highs[idx + 2]
        avg_high = (h1["price"] + h2["price"] + h3["price"]) / 3
        max_diff = max(abs(h1["price"] - avg_high), abs(h2["price"] - avg_high), abs(h3["price"] - avg_high)) / max(avg_high, 1e-9)
        if max_diff < 0.02:
            confidence = int(round((1 - max_diff / 0.02) * 75 + 25))
            if confidence >= min_confidence:
                between = candles[h1["index"]:h3["index"] + 1]
                neckline = min(item["low"] for item in between)
                height = avg_high - neckline
                patterns.append(_build_pattern("TRIPLE_TOP", CLASSIC_PATTERNS["TRIPLE_TOP"], timeframe, "BEARISH", confidence, "COMPLETED", _indices_between(h1["index"], h3["index"]), {"A": h1, "B": h2, "C": h3}, neckline - height, avg_high))

    for idx in range(len(lows) - 2):
        l1, l2, l3 = lows[idx], lows[idx + 1], lows[idx + 2]
        avg_low = (l1["price"] + l2["price"] + l3["price"]) / 3
        max_diff = max(abs(l1["price"] - avg_low), abs(l2["price"] - avg_low), abs(l3["price"] - avg_low)) / max(avg_low, 1e-9)
        if max_diff < 0.02:
            confidence = int(round((1 - max_diff / 0.02) * 75 + 25))
            if confidence >= min_confidence:
                between = candles[l1["index"]:l3["index"] + 1]
                neckline = max(item["high"] for item in between)
                height = neckline - avg_low
                patterns.append(_build_pattern("TRIPLE_BOTTOM", CLASSIC_PATTERNS["TRIPLE_BOTTOM"], timeframe, "BULLISH", confidence, "COMPLETED", _indices_between(l1["index"], l3["index"]), {"A": l1, "B": l2, "C": l3}, neckline + height, avg_low))

    if len(highs) >= 2 and len(lows) >= 2:
        recent_highs = highs[-3:]
        recent_lows = lows[-3:]
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            top_flat = abs(recent_highs[-1]["price"] - recent_highs[-2]["price"]) / max(recent_highs[0]["price"], 1e-9) < 0.018
            bottom_rising = recent_lows[-1]["price"] > recent_lows[-2]["price"]
            bottom_flat = abs(recent_lows[-1]["price"] - recent_lows[-2]["price"]) / max(recent_lows[0]["price"], 1e-9) < 0.018
            top_falling = recent_highs[-1]["price"] < recent_highs[-2]["price"]

            if top_flat and bottom_rising:
                resistance = recent_highs[-1]["price"]
                support = recent_lows[-1]["price"]
                triangle_height = resistance - support
                patterns.append(_build_pattern("ASCENDING_TRIANGLE", CLASSIC_PATTERNS["ASCENDING_TRIANGLE"], timeframe, "BULLISH", 65, "COMPLETED", _indices_between(min(recent_highs[-2]["index"], recent_lows[-2]["index"]), max(recent_highs[-1]["index"], recent_lows[-1]["index"])), {"A": recent_highs[-2], "B": recent_highs[-1], "C": recent_lows[-2], "D": recent_lows[-1]}, resistance + triangle_height, support))

            if bottom_flat and top_falling:
                resistance = recent_highs[-1]["price"]
                support = recent_lows[-1]["price"]
                triangle_height = resistance - support
                patterns.append(_build_pattern("DESCENDING_TRIANGLE", CLASSIC_PATTERNS["DESCENDING_TRIANGLE"], timeframe, "BEARISH", 65, "COMPLETED", _indices_between(min(recent_highs[-2]["index"], recent_lows[-2]["index"]), max(recent_highs[-1]["index"], recent_lows[-1]["index"])), {"A": recent_highs[-2], "B": recent_highs[-1], "C": recent_lows[-2], "D": recent_lows[-1]}, support - triangle_height, resistance))

    if len(highs) >= 3 and len(lows) >= 3:
        recent_highs = highs[-3:]
        recent_lows = lows[-3:]
        highs_rising = recent_highs[2]["price"] > recent_highs[1]["price"] > recent_highs[0]["price"]
        lows_rising = recent_lows[2]["price"] > recent_lows[1]["price"] > recent_lows[0]["price"]
        highs_falling = recent_highs[2]["price"] < recent_highs[1]["price"] < recent_highs[0]["price"]
        lows_falling = recent_lows[2]["price"] < recent_lows[1]["price"] < recent_lows[0]["price"]
        converging = (recent_highs[2]["price"] - recent_lows[2]["price"]) < (recent_highs[0]["price"] - recent_lows[0]["price"])

        if highs_rising and lows_rising and converging:
            patterns.append(_build_pattern("RISING_WEDGE", CLASSIC_PATTERNS["RISING_WEDGE"], timeframe, "BEARISH", 60, "COMPLETED", _indices_between(min(recent_highs[0]["index"], recent_lows[0]["index"]), max(recent_highs[2]["index"], recent_lows[2]["index"])), {"A": recent_highs[0], "B": recent_highs[2], "C": recent_lows[0], "D": recent_lows[2]}, recent_lows[0]["price"], recent_highs[2]["price"]))

        if highs_falling and lows_falling and converging:
            patterns.append(_build_pattern("FALLING_WEDGE", CLASSIC_PATTERNS["FALLING_WEDGE"], timeframe, "BULLISH", 60, "COMPLETED", _indices_between(min(recent_highs[0]["index"], recent_lows[0]["index"]), max(recent_highs[2]["index"], recent_lows[2]["index"])), {"A": recent_highs[0], "B": recent_highs[2], "C": recent_lows[0], "D": recent_lows[2]}, recent_highs[0]["price"], recent_lows[2]["price"]))

    patterns.sort(key=lambda item: item["confidence"], reverse=True)
    return _dedupe_classics(patterns)


def _summarize(patterns: List[Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
    bullish_count = sum(1 for pattern in patterns if pattern.get("signal") == "bullish")
    bearish_count = sum(1 for pattern in patterns if pattern.get("signal") == "bearish")
    strongest_signal = "NEUTRAL"
    recommendation = "HOLD"
    adjustment = 0.0
    if bullish_count > bearish_count and bullish_count > 0:
        strongest_signal = "BULLISH"
        recommendation = "BUY"
        adjustment = min(0.2, sum(pattern.get("confidence", 0) for pattern in patterns if pattern.get("signal") == "bullish") / 1000)
    elif bearish_count > bullish_count and bearish_count > 0:
        strongest_signal = "BEARISH"
        recommendation = "SELL"
        adjustment = min(0.2, sum(pattern.get("confidence", 0) for pattern in patterns if pattern.get("signal") == "bearish") / 1000)
    elif bullish_count > 0 and bearish_count > 0:
        strongest_signal = "MIXED"
        adjustment = -0.08
    return {
        "timeframe": timeframe,
        "patterns": patterns,
        "has_patterns": len(patterns) > 0,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": 0,
        "strongest_signal": strongest_signal,
        "recommendation": recommendation,
        "confidence_adjustment": adjustment,
        "patterns_summary": [f"{pattern.get('name_tr', pattern.get('name'))} ({pattern.get('timeframe', timeframe)})" for pattern in patterns[:5]],
        "top_pattern": patterns[0] if patterns else None,
    }


def detect_chart_patterns_from_candles(candles: List[Dict[str, Any]], timeframe: str = "4h", options: Dict[str, Any] | None = None) -> Dict[str, Any]:
    normalized_timeframe = _normalize_timeframe(timeframe)
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    normalized = _normalize_candles(candles)
    if len(normalized) < 10:
        return _summarize([], normalized_timeframe)
    harmonic = _detect_harmonic_patterns(normalized, normalized_timeframe, float(opts["deviation"]), float(opts["fib_tolerance"]), float(opts["min_confidence"]))
    classic = _detect_classic_patterns(normalized, normalized_timeframe, float(opts["min_confidence"]))
    patterns = sorted(harmonic + classic, key=lambda item: (item.get("category") != "harmonic", -item.get("confidence", 0)))
    summary = _summarize(patterns, normalized_timeframe)
    summary["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return summary


async def detect_chart_patterns(symbol: str, timeframe: str = "4h", limit: int = 260, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from services.data_fetcher import fetch_ohlc_data

    normalized_timeframe = _normalize_timeframe(timeframe)
    try:
        candles = await fetch_ohlc_data(symbol, timeframe=normalized_timeframe, limit=limit)
        result = detect_chart_patterns_from_candles(candles or [], normalized_timeframe, options)
        result["symbol"] = symbol
        return result
    except Exception as exc:
        logger.warning("Shared pattern detection failed for %s %s: %s", symbol, normalized_timeframe, exc)
        result = _summarize([], normalized_timeframe)
        result["symbol"] = symbol
        result["error"] = str(exc)
        return result


async def get_pattern_adjustment(symbol: str, timeframe: str = "4h") -> Dict[str, Any]:
    result = await detect_chart_patterns(symbol, timeframe=timeframe)
    return {
        "has_patterns": result.get("has_patterns", False),
        "patterns": result.get("patterns", []),
        "bullish_count": result.get("bullish_count", 0),
        "bearish_count": result.get("bearish_count", 0),
        "neutral_count": result.get("neutral_count", 0),
        "strongest_signal": result.get("strongest_signal", "NEUTRAL"),
        "recommendation": result.get("recommendation", "HOLD"),
        "confidence_adjustment": result.get("confidence_adjustment", 0),
        "patterns_summary": result.get("patterns_summary", []),
        "timeframe": result.get("timeframe", _normalize_timeframe(timeframe)),
        "top_pattern": result.get("top_pattern"),
        "source": "harmonic_visualizer_4h",
    }
