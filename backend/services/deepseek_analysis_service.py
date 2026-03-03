"""
DeepSeek-R1 Analysis Service
==============================
Provides institutional-grade market analysis using DeepSeek-R1's reasoning capabilities.
Supports: Master Analysis, SMC (Smart Money Concepts), Risk Optimization, Seasonality.
"""

import json
import logging
import hashlib
import time
from typing import Literal, Optional, Dict, Any

logger = logging.getLogger(__name__)

# In-memory cache (TTL = 2 hours for cost optimization)
_cache: Dict[str, Any] = {}
_cache_ts: Dict[str, float] = {}
CACHE_TTL = 7200  # 2 hours - DeepSeek analysis doesn't change frequently

SYSTEM_PROMPT = """Sen bir Institutional Quantitative Analyst'sin. 
Görevin: Verilen veri paketinden BÜYÜK RESİM analizi yapıp, net bir pozisyon kararı vermek.

KURALLAR:
1. Önce veri kalitesini kontrol et (eksik/bozuk veri varsa belirt)
2. Multi-timeframe confluence analizi yap (1H trend vs 4H trend çelişiyorsa "caution" olarak işaretle)
3. Smart Money Concepts (Liquidity sweep, Order Blocks) varsa öncelik ver
4. Makro veriler (DXY, VIX) ile teknik analizi ilişkilendir
5. ML tahmini ile kendi analizini çeliştir - hangisi daha güçlü argümanlar sunuyor?
6. Asla "belki" deme. Net karar: BUY/SELL/HOLD/NO_TRADE

YANIT FORMATI (JSON):
{
  "analysis_meta": {
    "confidence_score": 0-100,
    "data_quality": "complete|partial|corrupted",
    "timeframe_alignment": "confluent|mixed|conflicting"
  },
  "market_regime": {
    "trend": "strong_bullish|bullish|neutral|bearish|strong_bearish",
    "volatility_regime": "compression|normal|expansion",
    "market_structure": "accumulation|markup|distribution|markdown",
    "liquidity_status": "swept_higher|swept_lower|building"
  },
  "technical_confluence": {
    "ema_alignment": "bullish_stack|bearish_stack|mixed",
    "momentum": "overbought_bullish|neutral|oversold_bearish",
    "divergence": "bullish_hidden|bearish_hidden|regular_bull|regular_bear|none",
    "key_level_proximity": "at_support|at_resistance|mid_range",
    "volume_confirmation": "confirming|diverging|neutral"
  },
  "smart_money_signals": {
    "order_blocks": [{"type": "bullish|bearish", "price": 0, "strength": 1-10}],
    "fair_value_gaps": [{"direction": "up|down", "fill_status": "open|filled"}],
    "liquidity_sweep": "swept_buy_side|swept_sell_side|none",
    "breaker_block": "active|tested|none"
  },
  "decision": {
    "direction": "BUY|SELL|HOLD|NO_TRADE",
    "confidence": 0-100,
    "position_size": "large|medium|small|micro",
    "urgency": "immediate|wait_for_setup|pending",
    "invalidation_price": 0
  },
  "execution_plan": {
    "entry_zone": {"min": 0, "max": 0, "logic": "string"},
    "stop_loss": {"price": 0, "type": "technical|volatility|structure"},
    "take_profits": [{"price": 0, "portion": 0.5, "rr_ratio": 2.0}],
    "breakeven_trigger": 0
  },
  "risk_assessment": {
    "primary_risk": "string",
    "red_flags": [],
    "correlation_warning": "dxy_aligned|dxy_contra|none",
    "news_risk": "high_impact_pending|low_impact|clear"
  },
  "thesis": {
    "summary": "2-3 cümlede ana fikir",
    "key_catalyst": "Ne piyasayı hareket ettirecek?",
    "alternative_scenario": "Yanlışsam ne olur?"
  }
}"""

SMC_PROMPT = """Sen bir Smart Money Concepts (SMC) uzmanısın. Fiyat hareketini institutional lens ile analiz et.

Görevlerin:
1. Order Block'ları tespit et (son swing high/low'lardan)
2. Fair Value Gap'leri bul (3 mumluk boşluklar)
3. Liquidity Pool'ları işaretle (equal highs/lows)
4. Breaker Block ve Mitigation Block var mı kontrol et
5. Break of Structure (BOS) ve Change of Character (CHoCH) tespiti yap

YANIT FORMATI (JSON):
{
  "market_structure": {
    "current_trend": "bullish|bearish|ranging",
    "last_bos": {"direction": "up|down", "price": 0, "confirmed": true},
    "last_choch": {"direction": "up|down", "price": 0, "confirmed": false},
    "swing_high": 0,
    "swing_low": 0
  },
  "order_blocks": [
    {"type": "bullish|bearish", "price_high": 0, "price_low": 0, "strength": 1-10, "status": "fresh|tested|mitigated", "timeframe": "string"}
  ],
  "fair_value_gaps": [
    {"direction": "bullish|bearish", "high": 0, "low": 0, "fill_pct": 0, "status": "open|partial|filled"}
  ],
  "liquidity_pools": [
    {"type": "buy_side|sell_side", "price": 0, "strength": "weak|moderate|strong", "swept": false}
  ],
  "breaker_blocks": [
    {"type": "bullish|bearish", "price_high": 0, "price_low": 0, "status": "active|tested"}
  ],
  "bias": {
    "direction": "bullish|bearish|neutral",
    "confidence": 0-100,
    "key_level_to_watch": 0,
    "invalidation": 0,
    "narrative": "2-3 cümlede SMC hikayesi"
  }
}"""

RISK_PROMPT = """Sen bir Risk Management uzmanısın. Verilen trading setup için optimal pozisyon boyutlandırma ve risk yönetimi planı oluştur.

Görevlerin:
1. Kelly Criterion'a göre optimum pozisyon boyutunu hesapla
2. Volatilite bazlı ATR çarpanını öner
3. Partial TP seviyelerini belirle (1:2, 1:3 R:R noktaları)
4. Correlation risk varsa position size'ı düşür
5. Maximum portfolio heat hesapla

YANIT FORMATI (JSON):
{
  "position_sizing": {
    "kelly_fraction": 0.15,
    "adjusted_size": 0.10,
    "reason": "string",
    "max_risk_pct": 2.0
  },
  "stop_loss": {
    "price": 0,
    "atr_multiplier": 1.8,
    "type": "technical|atr_based|structure",
    "distance_pct": 0.5
  },
  "take_profits": [
    {"level": 0, "close_pct": 50, "rr_ratio": 2.0, "logic": "string"},
    {"level": 0, "close_pct": 30, "rr_ratio": 3.5, "logic": "string"}
  ],
  "trail_stop": {
    "activation_price": 0,
    "trail_distance_atr": 1.5,
    "enabled": true
  },
  "portfolio_heat": {
    "current_exposure_pct": 0,
    "max_allowed_pct": 6,
    "correlation_adjustment": 1.0,
    "final_heat_pct": 0
  },
  "risk_score": {
    "overall": 0-100,
    "factors": ["string"],
    "recommendation": "string"
  }
}"""

SEASONALITY_PROMPT = """Sen bir Quantitative Seasonality Analyst'sin. Verilen sembol ve tarih için tarihsel istatistiksel analiz yap.

Görevlerin:
1. Bu ayın historik performansını analiz et (son 10 yıl win rate)
2. Haftanın gününe göre edge var mı kontrol et
3. Yaklaşan yüksek etkili haberlerin volatilite üzerine etkisini değerlendir
4. Session bazlı (Asia/London/NY) pattern'leri incele
5. Anomali tespiti yap

YANIT FORMATI (JSON):
{
  "monthly_stats": {
    "month": "string",
    "historical_win_rate": 0-100,
    "avg_return_pct": 0,
    "best_year": {"year": 2024, "return_pct": 0},
    "worst_year": {"year": 2024, "return_pct": 0},
    "current_performance": "above_avg|avg|below_avg"
  },
  "day_of_week": {
    "day": "string",
    "historical_bias": "bullish|bearish|neutral",
    "win_rate": 0-100,
    "avg_range_pct": 0
  },
  "session_analysis": {
    "asian": {"bias": "bullish|bearish|neutral", "avg_range": 0},
    "london": {"bias": "bullish|bearish|neutral", "avg_range": 0},
    "new_york": {"bias": "bullish|bearish|neutral", "avg_range": 0},
    "gap_fill_rate_pct": 0
  },
  "upcoming_events": [
    {"event": "string", "impact": "high|medium|low", "expected_volatility_pct": 0, "direction_bias": "bullish|bearish|neutral"}
  ],
  "anomalies": [
    {"type": "string", "description": "string", "significance": "high|medium|low"}
  ],
  "seasonal_edge": {
    "direction": "bullish|bearish|neutral",
    "confidence": 0-100,
    "summary": "string"
  }
}"""


def _cache_key(symbol: str, analysis_type: str) -> str:
    return f"{symbol}:{analysis_type}"


def _get_cached(key: str) -> Optional[dict]:
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < CACHE_TTL:
        return _cache[key]
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = data
    _cache_ts[key] = time.time()


async def _build_data_pack(symbol: str) -> dict:
    """Build a compact data pack from existing services."""
    pack: Dict[str, Any] = {"symbol": symbol, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}

    try:
        from services.data_fetcher import fetch_latest_price
        price = await fetch_latest_price(symbol)
        pack["price"] = {"current": price}
    except Exception:
        pack["price"] = {"current": 0}

    # Try to get TA data
    try:
        from services.mtf_analysis_service import get_mtf_analysis
        mtf = await get_mtf_analysis(symbol, None)
        if mtf.get("success"):
            pack["mtf_data"] = {
                "confluence": mtf.get("confluence", {}),
                "current_price": mtf.get("current_price", 0),
            }
            # Extract timeframe summaries
            tfs = mtf.get("timeframes", {})
            pack["timeframes"] = {}
            for tf_key, tf_data in tfs.items():
                if isinstance(tf_data, dict):
                    pack["timeframes"][tf_key] = {
                        "trend": tf_data.get("trend", {}).get("direction", "neutral"),
                        "rsi": tf_data.get("momentum", {}).get("rsi", 50),
                        "ema_stack": tf_data.get("trend", {}).get("ema_alignment", "mixed"),
                    }
    except Exception as e:
        logger.warning(f"MTF data unavailable for {symbol}: {e}")

    # Try to get ML prediction
    try:
        from services.claude_signal_analyzer import get_full_analysis
        full = await get_full_analysis(symbol)
        ml = full.get("ml_prediction", {})
        pack["ml_prediction"] = {
            "direction": ml.get("direction", "neutral"),
            "confidence": ml.get("confidence", 0),
            "target": ml.get("target_price", 0),
            "stop": ml.get("stop_price", 0),
        }
    except Exception as e:
        logger.warning(f"ML prediction unavailable for {symbol}: {e}")

    return pack


async def analyze_with_deepseek(
    symbol: str,
    analysis_type: Literal["master", "smc", "risk", "seasonality"] = "master",
    extra_context: Optional[dict] = None,
) -> dict:
    """Run DeepSeek-R1 analysis."""
    from config import settings

    cache_key = _cache_key(symbol, analysis_type)
    cached = _get_cached(cache_key)
    if cached:
        return cached

    if not settings.deepseek_api_key:
        return {"error": "DeepSeek API key not configured", "analysis_type": analysis_type}

    prompts = {
        "master": SYSTEM_PROMPT,
        "smc": SMC_PROMPT,
        "risk": RISK_PROMPT,
        "seasonality": SEASONALITY_PROMPT,
    }

    try:
        import openai

        client = openai.OpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
        )

        data_pack = await _build_data_pack(symbol)
        if extra_context:
            data_pack.update(extra_context)

        # DeepSeek-R1 doesn't support system role well - prepend to user message
        user_content = prompts[analysis_type] + "\n\n--- VERİ PAKETİ ---\n" + json.dumps(data_pack, ensure_ascii=False)

        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "user", "content": user_content},
            ],
            max_tokens=2000,
        )

        content = response.choices[0].message.content or "{}"

        # Try to parse JSON from the response
        try:
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            result = json.loads(content)
        except json.JSONDecodeError:
            result = {"raw_response": content, "parse_error": True}

        # Add reasoning if available
        reasoning = getattr(response.choices[0].message, "reasoning_content", None)
        if reasoning:
            result["_reasoning"] = reasoning

        result["analysis_type"] = analysis_type
        result["symbol"] = symbol
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        _set_cache(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"DeepSeek analysis error ({analysis_type}): {e}")
        return {
            "error": str(e),
            "analysis_type": analysis_type,
            "symbol": symbol,
            "decision": {"direction": "NO_TRADE"},
        }
