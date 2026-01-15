from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from services.data_fetcher import fetch_eod_candles, fetch_latest_price
from services.marketaux_service import fetch_marketaux_headlines
from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
from services.ta_service import compute_ta_snapshot

logger = logging.getLogger(__name__)


DETAILED_SYSTEM_PROMPT = """Sen deneyimli bir forex, endeks ve emtia trader'ısın. 15+ yıllık profesyonel trading tecrüben var.

Görevin: Sana verilen ML tahmini + teknik veri paketi + haber başlıkları + makro proxy verilerini birleştirerek tek bir karar raporu üretmek.

Kurallar:
- Sadece verilen verileri kullan; uydurma değer üretme.
- Çelişkileri açıkça belirt.
- Yüksek risk ortamında (yüksek volatilite, zayıf hacim teyidi, haber yoğunluğu) pozisyon boyutunu küçült.
- Yanıtı MUTLAKA geçerli JSON olarak döndür (ek metin yok).

Beklenen JSON şeması:
{
  "final_decision": "BUY"|"SELL"|"HOLD",
  "confidence": 0-100,
  "summary": "...",
  "thesis": ["..."],
  "key_levels": {
    "nearest_support": {"price": number|null, "distance_pct": number|null},
    "nearest_resistance": {"price": number|null, "distance_pct": number|null},
    "ema_distances_pct": {"ema20": number|null, "ema50": number|null, "ema200": number|null}
  },
  "market_regime": {
    "trend": "BULLISH"|"BEARISH"|"NEUTRAL"|"UNKNOWN",
    "volatility": "LOW"|"MEDIUM"|"HIGH"|"UNKNOWN",
    "volume_confirmation": "STRONG"|"WEAK"|"MIXED"|"UNKNOWN"
  },
  "macro_view": {
    "dxy": {"price": number|null, "note": ""},
    "vix": {"price": number|null, "note": ""},
    "usdtry": {"price": number|null, "note": ""}
  },
  "news_impact": {
    "headline_count": number,
    "tone": "POSITIVE"|"NEGATIVE"|"MIXED"|"NEUTRAL"|"UNKNOWN",
    "notes": ["..."]
  },
  "risk_management": {
    "recommended_entry": number|null,
    "recommended_sl": number|null,
    "recommended_tp": number|null,
    "position_size": "NO_TRADE"|"SMALL"|"MEDIUM"|"LARGE",
    "invalidation": "..."
  },
  "red_flags": ["..."],
  "timestamp": "ISO-8601",
  "model_used": "claude-sonnet-4-20250514"|"fallback"
}
"""


def _parse_claude_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if m:
        candidate = m.group(1).strip()
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    return None


def _pct_distance(a: float, b: float) -> Optional[float]:
    if a is None or b is None:
        return None
    if a == 0:
        return None
    return float(((a - b) / a) * 100.0)


def _nearest_level(current: float, levels: List[dict], kind: str) -> dict:
    if not levels or current == 0:
        return {"price": None, "distance_pct": None, "kind": kind}
    if kind == "support":
        candidates = [lv for lv in levels if float(lv.get("price", 0)) <= current]
        if not candidates:
            return {"price": None, "distance_pct": None, "kind": kind}
        lv = sorted(candidates, key=lambda x: current - float(x.get("price", 0)))[0]
    else:
        candidates = [lv for lv in levels if float(lv.get("price", 0)) >= current]
        if not candidates:
            return {"price": None, "distance_pct": None, "kind": kind}
        lv = sorted(candidates, key=lambda x: float(x.get("price", 0)) - current)[0]

    price = float(lv.get("price", 0))
    return {"price": price, "distance_pct": _pct_distance(current, price), "kind": kind}


def _trend_channel_features(closes: np.ndarray, current: float) -> dict:
    if closes is None or len(closes) < 40 or current == 0:
        return {"slope": None, "position": None, "width_pct": None}

    y = closes[-120:] if len(closes) >= 120 else closes
    x = np.arange(len(y), dtype=float)
    try:
        slope, intercept = np.polyfit(x, y.astype(float), 1)
        fitted = slope * x + intercept
        residual = y - fitted
        resid_std = float(np.std(residual)) if len(residual) else 0.0
        center = float(fitted[-1])
        width = max(1e-9, 2.0 * resid_std)
        pos = float((current - center) / width)
        return {
            "slope": float(slope),
            "position": pos,
            "width_pct": float((width / current) * 100.0) if current else None,
        }
    except Exception:
        return {"slope": None, "position": None, "width_pct": None}


async def build_context_pack(symbol: str) -> Dict[str, Any]:
    normalized_symbol = "NDX.INDX" if (symbol or "").upper() in ["NASDAQ", "NDX.INDX", "NDX"] else (symbol or "").upper()

    ml_prediction = await get_ml_prediction(normalized_symbol)

    candles = await fetch_eod_candles(normalized_symbol, limit=260)
    live_price = await fetch_latest_price(normalized_symbol)

    closes = np.array([c["close"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    highs = np.array([c["high"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    lows = np.array([c["low"] for c in candles], dtype=float) if candles else np.array([], dtype=float)
    volumes = np.array([c.get("volume", 0) for c in candles], dtype=float) if candles else np.array([], dtype=float)

    current_price = float(live_price) if live_price is not None else (float(closes[-1]) if len(closes) else 0.0)

    ta = _compute_technical_indicators(closes, highs, lows, volumes) if len(closes) else {"close": 0.0}
    ta["close"] = current_price

    ta_snapshot = await compute_ta_snapshot(normalized_symbol)

    ema20 = float(ta.get("ema_20", 0.0))
    ema50 = float(ta.get("ema_50", 0.0))
    ema200 = float(ta.get("ema_200", 0.0))

    distances = {
        "ema20_pct": _pct_distance(current_price, ema20),
        "ema50_pct": _pct_distance(current_price, ema50),
        "ema200_pct": _pct_distance(current_price, ema200),
        "boll_zscore": float(ta.get("boll_zscore", 0.0)),
        "atr_pct": float(ta.get("atr_pct", 0.0)),
    }

    supports = ta_snapshot.get("supports", []) or []
    resistances = ta_snapshot.get("resistances", []) or []
    nearest_support = _nearest_level(current_price, supports, "support")
    nearest_resistance = _nearest_level(current_price, resistances, "resistance")

    vol_last = float(volumes[-1]) if len(volumes) else 0.0
    vol_avg20 = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else (float(np.mean(volumes)) if len(volumes) else 0.0)
    vol_ratio = float(vol_last / vol_avg20) if vol_avg20 > 0 else None

    channel = _trend_channel_features(closes, current_price)

    macro_symbols = {
        "dxy": "DXY.INDX",
        "vix": "VIX.INDX",
        "usdtry": "USDTRY",
    }
    macro = {}
    for k, sym in macro_symbols.items():
        price = await fetch_latest_price(sym)
        macro[k] = {"symbol": sym, "price": float(price) if price is not None else None}

    news_symbols = ["XAUUSD", "GOLD", "DXY", "USD"] if "XAU" in normalized_symbol else ["NDX", "NASDAQ", "VIX", "DXY"]
    headlines = await fetch_marketaux_headlines(news_symbols)

    prediction_dict = {
        "symbol": ml_prediction.symbol,
        "direction": ml_prediction.direction,
        "confidence": ml_prediction.confidence,
        "probability_up": ml_prediction.probability_up,
        "probability_down": ml_prediction.probability_down,
        "target_pips": ml_prediction.target_pips,
        "stop_pips": ml_prediction.stop_pips,
        "risk_reward": ml_prediction.risk_reward,
        "entry_price": ml_prediction.entry_price,
        "target_price": ml_prediction.target_price,
        "stop_price": ml_prediction.stop_price,
        "technical_score": ml_prediction.technical_score,
        "momentum_score": ml_prediction.momentum_score,
        "trend_score": ml_prediction.trend_score,
        "volatility_regime": ml_prediction.volatility_regime,
        "reasoning": ml_prediction.reasoning,
        "key_levels": ml_prediction.key_levels,
    }

    return {
        "symbol": normalized_symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ml_prediction": prediction_dict,
        "ta": ta,
        "ta_snapshot": ta_snapshot,
        "distances": distances,
        "levels": {
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
        },
        "volume": {
            "last": vol_last,
            "avg20": vol_avg20,
            "ratio": vol_ratio,
        },
        "trend_channel": channel,
        "macro": macro,
        "news": {"headlines": headlines, "count": len(headlines)},
    }


def _fallback_detailed_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    ml = context.get("ml_prediction", {}) or {}
    levels = context.get("levels", {}) or {}
    distances = context.get("distances", {}) or {}
    volume = context.get("volume", {}) or {}

    direction = ml.get("direction", "HOLD")
    confidence = float(ml.get("confidence", 50.0))

    vol_ratio = volume.get("ratio")
    vol_note = ""
    if vol_ratio is not None:
        if vol_ratio < 0.8:
            vol_note = "Hacim zayıf (ortalamanın altında)"
        elif vol_ratio > 1.2:
            vol_note = "Hacim güçlü (ortalamanın üzerinde)"
        else:
            vol_note = "Hacim ortalama seviyede"

    return {
        "final_decision": direction,
        "confidence": float(np.clip(confidence * 0.9, 0.0, 100.0)),
        "summary": "Claude devre dışı; fallback detaylı analiz kullanıldı.",
        "thesis": [
            f"ML yönü: {direction} ({confidence:.0f}%)",
            f"EMA20 uzaklık: {distances.get('ema20_pct')}",
            f"En yakın destek: {levels.get('nearest_support')}",
            f"En yakın direnç: {levels.get('nearest_resistance')}",
            vol_note,
        ],
        "key_levels": {
            "nearest_support": {
                "price": (levels.get("nearest_support") or {}).get("price"),
                "distance_pct": (levels.get("nearest_support") or {}).get("distance_pct"),
            },
            "nearest_resistance": {
                "price": (levels.get("nearest_resistance") or {}).get("price"),
                "distance_pct": (levels.get("nearest_resistance") or {}).get("distance_pct"),
            },
            "ema_distances_pct": {
                "ema20": distances.get("ema20_pct"),
                "ema50": distances.get("ema50_pct"),
                "ema200": distances.get("ema200_pct"),
            },
        },
        "market_regime": {
            "trend": (context.get("ta_snapshot") or {}).get("trend", "UNKNOWN"),
            "volatility": ml.get("volatility_regime", "UNKNOWN").upper() if ml.get("volatility_regime") else "UNKNOWN",
            "volume_confirmation": "UNKNOWN",
        },
        "macro_view": {
            "dxy": {"price": ((context.get("macro") or {}).get("dxy") or {}).get("price"), "note": ""},
            "vix": {"price": ((context.get("macro") or {}).get("vix") or {}).get("price"), "note": ""},
            "usdtry": {"price": ((context.get("macro") or {}).get("usdtry") or {}).get("price"), "note": ""},
        },
        "news_impact": {
            "headline_count": int(((context.get("news") or {}).get("count") or 0)),
            "tone": "UNKNOWN",
            "notes": [],
        },
        "risk_management": {
            "recommended_entry": ml.get("entry_price"),
            "recommended_sl": ml.get("stop_price"),
            "recommended_tp": ml.get("target_price"),
            "position_size": "SMALL" if direction != "HOLD" else "NO_TRADE",
            "invalidation": "Fiyatın EMA'lar ve yakın seviyeler etrafında ters sinyal üretmesi.",
        },
        "red_flags": ["Claude API bağlantısı yok"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model_used": "fallback",
    }


async def analyze_detailed_with_claude(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import anthropic
    except ImportError:
        return _fallback_detailed_analysis(context)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_detailed_analysis(context)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = "Aşağıdaki JSON context pack'i analiz et ve sadece JSON yanıt döndür:\n\n" + json.dumps(
        context, ensure_ascii=False
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1800,
            system=DETAILED_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        response_text = message.content[0].text if getattr(message, "content", None) else ""

        parsed = _parse_claude_json(response_text)
        if parsed is not None:
            parsed["timestamp"] = parsed.get("timestamp") or (datetime.utcnow().isoformat() + "Z")
            parsed["model_used"] = parsed.get("model_used") or "claude-sonnet-4-20250514"
            return parsed

        return {
            "final_decision": context.get("ml_prediction", {}).get("direction", "HOLD"),
            "confidence": float(context.get("ml_prediction", {}).get("confidence", 50.0)),
            "summary": response_text[:2000],
            "thesis": [],
            "key_levels": {},
            "market_regime": {},
            "macro_view": {},
            "news_impact": {},
            "risk_management": {},
            "red_flags": ["Claude JSON parse failed"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_used": "claude-sonnet-4-20250514",
        }
    except Exception as e:
        logger.error(f"Claude detailed analysis error: {e}")
        return _fallback_detailed_analysis(context)


async def get_detailed_analysis(symbol: str, log_to_db: bool = True) -> Dict[str, Any]:
    context = await build_context_pack(symbol)
    analysis = await analyze_detailed_with_claude(context)
    
    if log_to_db:
        try:
            from services.prediction_logger import log_prediction
            await log_prediction(
                symbol=context.get("symbol", symbol),
                context=context,
                analysis=analysis,
                timeframe="1d"
            )
        except Exception as e:
            logger.warning(f"Failed to log prediction to database: {e}")
    
    return {"symbol": context.get("symbol", symbol), "context": context, "analysis": analysis}
