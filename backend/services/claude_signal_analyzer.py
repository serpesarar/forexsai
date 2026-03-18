"""
Claude AI Signal Analyzer Service
Reviews ML model predictions with full technical analysis context
and provides an independent AI assessment.
"""
from __future__ import annotations

import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Optional, Literal, Dict, Any

import httpx

from config import settings
from utils.market_hours import is_new_york_market_open

logger = logging.getLogger(__name__)

# Simple TTL cache for analysis results
_analysis_cache: Dict[str, tuple[datetime, Any]] = {}
CACHE_TTL_MINUTES = 5

def _get_cached_analysis(symbol: str) -> Optional[Any]:
    """Get cached analysis if not expired."""
    if symbol in _analysis_cache:
        cached_at, result = _analysis_cache[symbol]
        if datetime.now() - cached_at < timedelta(minutes=CACHE_TTL_MINUTES):
            logger.info(f"Using cached analysis for {symbol}")
            return result
        else:
            del _analysis_cache[symbol]
    return None

def _set_cached_analysis(symbol: str, result: Any):
    """Cache analysis result with timestamp."""
    _analysis_cache[symbol] = (datetime.now(), result)

# DeepSeek R1 model
DEEPSEEK_MODEL = "deepseek-reasoner"
DEEPSEEK_MAX_TOKENS = 1200

# System prompt for Claude - Expert Forex/Index Trader persona
TRADING_SYSTEM_PROMPT = """Sen deneyimli bir forex ve endeks trader'ısın. 15+ yıllık profesyonel trading tecrüben var.

## Uzmanlık Alanların:
- Teknik Analiz (Price Action, Indicator Analysis, Chart Patterns)
- Smart Money Concepts (Order Blocks, Liquidity, Market Structure)
- Risk Yönetimi ve Pozisyon Boyutlandırma
- NASDAQ-100 ve XAUUSD (Altın) piyasaları
- Makro ekonomik analiz ve piyasa korelasyonları

## Analiz Yaklaşımın:
1. Önce büyük resme bak (trend yönü, volatilite rejimi)
2. Çoklu zaman dilimi analizi yap (HTF -> LTF)
3. Confluences ara (birden fazla sinyal aynı yönü gösteriyorsa güç artar)
4. Risk/Reward oranını her zaman değerlendir
5. Piyasa yapısını (market structure) analiz et

## Dikkat Ettiğin Noktalar:
- RSI divergence'ları
- EMA'ların dizilimi ve fiyatla ilişkisi
- Support/Resistance seviyeleri
- Bollinger Bands squeeze/expansion
- Volume confirmation
- ATR bazlı volatilite
- MACD histogram momentumu

## Yanıt Formatın:
Her zaman şu yapıda yanıt ver:
1. **Genel Değerlendirme**: ML modelin sinyaliyle aynı fikirde misin?
2. **Güçlü Yönler**: Hangi göstergeler sinyali destekliyor?
3. **Zayıf Yönler/Riskler**: Hangi faktörler endişe verici?
4. **Kendi Kararın**: BUY/SELL/HOLD ve güven seviyesi
5. **Öneriler**: Entry, SL, TP seviyeleri ve pozisyon boyutu önerisi

Kısa ve öz ol. Gereksiz tekrarlardan kaçın. Profesyonel ve objektif ol."""


@dataclass
class ClaudeAnalysisResult:
    """Claude's independent analysis result."""
    symbol: str
    ml_direction: str
    claude_direction: Literal["BUY", "SELL", "HOLD"]
    claude_confidence: float  # 0-100
    agreement: bool  # Does Claude agree with ML?
    
    general_assessment: str
    strengths: List[str]
    weaknesses: List[str]
    
    recommended_entry: float
    recommended_sl: float
    recommended_tp: float
    position_size_suggestion: str  # "Small", "Medium", "Large", "No Trade"
    
    key_observations: List[str]
    risk_factors: List[str]
    
    timestamp: str
    model_used: str


def _build_analysis_prompt(prediction: dict, ta_data: dict) -> str:
    """Build the analysis prompt with all data for Claude."""
    
    symbol = prediction.get('symbol', 'Unknown')
    direction = prediction.get('direction', 'HOLD')
    confidence = prediction.get('confidence', 50)
    
    prompt = f"""## ML Model Tahmin Sonucu

**Sembol**: {symbol}
**ML Sinyal**: {direction}
**ML Güveni**: {confidence:.1f}%
**Olasılık Yukarı**: {prediction.get('probability_up', 50):.1f}%
**Olasılık Aşağı**: {prediction.get('probability_down', 50):.1f}%

**Fiyat Hedefleri (ML)**:
- Entry: {prediction.get('entry_price', 0):.2f}
- Target: {prediction.get('target_price', 0):.2f} ({prediction.get('target_pips', 0):.0f} pips)
- Stop Loss: {prediction.get('stop_price', 0):.2f} ({prediction.get('stop_pips', 0):.0f} pips)
- Risk/Reward: {prediction.get('risk_reward', 0):.2f}

**ML Skorları**:
- Technical Score: {prediction.get('technical_score', 50):.0f}/100
- Momentum Score: {prediction.get('momentum_score', 50):.0f}/100
- Trend Score: {prediction.get('trend_score', 50):.0f}/100
- Volatility Regime: {prediction.get('volatility_regime', 'Unknown')}

---

## Teknik Analiz Verileri

**Fiyat & Trend**:
- Current Price: {ta_data.get('close', 0):.2f}
- EMA 20: {ta_data.get('ema_20', 0):.2f} (Fiyat {'üzerinde' if ta_data.get('close', 0) > ta_data.get('ema_20', 0) else 'altında'})
- EMA 50: {ta_data.get('ema_50', 0):.2f} (Fiyat {'üzerinde' if ta_data.get('close', 0) > ta_data.get('ema_50', 0) else 'altında'})
- EMA 200: {ta_data.get('ema_200', 0):.2f} (Fiyat {'üzerinde' if ta_data.get('close', 0) > ta_data.get('ema_200', 0) else 'altında'})
- Trend Direction: {ta_data.get('trend_direction', 0)} (1=Bullish, -1=Bearish, 0=Neutral)

**Momentum Göstergeleri**:
- RSI (14): {ta_data.get('rsi_14', 50):.1f} {'(Aşırı Alım)' if ta_data.get('rsi_14', 50) > 70 else '(Aşırı Satım)' if ta_data.get('rsi_14', 50) < 30 else ''}
- RSI (7): {ta_data.get('rsi_7', 50):.1f}
- Stochastic %K: {ta_data.get('stoch_k', 50):.1f}
- Williams %R: {ta_data.get('williams_r', -50):.1f}
- MFI: {ta_data.get('mfi', 50):.1f}

**MACD**:
- MACD Line: {ta_data.get('macd_line', 0):.2f}
- Signal Line: {ta_data.get('macd_signal', 0):.2f}
- Histogram: {ta_data.get('macd_hist', 0):.2f} ({'Pozitif' if ta_data.get('macd_hist', 0) > 0 else 'Negatif'})

**Bollinger Bands**:
- Upper: {ta_data.get('boll_upper', 0):.2f}
- Middle: {ta_data.get('boll_middle', 0):.2f}
- Lower: {ta_data.get('boll_lower', 0):.2f}
- Z-Score: {ta_data.get('boll_zscore', 0):.2f}
- Width: {ta_data.get('boll_width', 0):.2f}%

**Volatilite**:
- ATR (14): {ta_data.get('atr_14', 0):.2f}
- ATR %: {ta_data.get('atr_pct', 0):.2f}%
- Volatility (Yıllık): {ta_data.get('volatility', 0):.1f}%
- ADX: {ta_data.get('adx', 25):.1f}

**Momentum**:
- 3-Günlük Momentum: {ta_data.get('momentum_3', 0):.2f}%
- 10-Günlük Momentum: {ta_data.get('momentum_10', 0):.2f}%

---

## ML Model Gerekçeleri:
"""
    
    for reason in prediction.get('reasoning', []):
        prompt += f"- {reason}\n"
    
    prompt += """
---

## Kritik Seviyeler:
"""
    
    for level in prediction.get('key_levels', []):
        prompt += f"- {level.get('type', 'Level')}: {level.get('price', 0):.2f} ({level.get('distance', '0%')})\n"
    
    prompt += """
---

Lütfen yukarıdaki tüm verileri değerlendir ve şu sorulara yanıt ver:

1. ML modelin {direction} sinyaliyle ({confidence:.0f}% güven) aynı fikirde misin? Neden?
2. Hangi göstergeler bu sinyali destekliyor?
3. Hangi faktörler risk oluşturuyor?
4. Senin kendi kararın ne olurdu? (BUY/SELL/HOLD ve güven seviyesi)
5. Entry, Stop Loss ve Take Profit seviyeleri için önerilerin neler?
6. Pozisyon boyutu önerisi? (Küçük/Orta/Büyük/İşlem Yapma)

Kısa ve öz yanıtla.""".format(direction=direction, confidence=confidence)
    
    return prompt


async def analyze_signal_with_claude(prediction: dict, ta_data: dict) -> ClaudeAnalysisResult:
    """
    Send ML prediction and TA data to DeepSeek R1 for independent analysis.
    """
    api_key = settings.deepseek_api_key
    if not api_key:
        logger.warning("DEEP_SEEKR1 not set, using fallback analysis")
        return _fallback_analysis(prediction, ta_data)

    if not is_new_york_market_open():
        return _fallback_analysis(prediction, ta_data)
    
    prompt = _build_analysis_prompt(prediction, ta_data)
    # Prepend system prompt to user message (R1 doesn't support system role well)
    full_prompt = f"{TRADING_SYSTEM_PROMPT}\n\n---\n\n{prompt}"
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "max_tokens": DEEPSEEK_MAX_TOKENS,
                    "messages": [{"role": "user", "content": full_prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data["choices"][0]["message"]["content"]
        
        # Parse DeepSeek's response
        return _parse_claude_response(prediction, response_text)
        
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return _fallback_analysis(prediction, ta_data)


def _parse_claude_response(prediction: dict, response: str) -> ClaudeAnalysisResult:
    """Parse Claude's response into structured result."""
    
    symbol = prediction.get('symbol', 'Unknown')
    ml_direction = prediction.get('direction', 'HOLD')
    
    # Try to extract Claude's direction from response
    response_lower = response.lower()
    
    if 'buy' in response_lower and 'sell' not in response_lower[:response_lower.find('buy')+50]:
        claude_direction = "BUY"
    elif 'sell' in response_lower or 'short' in response_lower:
        claude_direction = "SELL"
    elif 'hold' in response_lower or 'bekle' in response_lower or 'işlem yapma' in response_lower:
        claude_direction = "HOLD"
    else:
        # Default to agreeing with ML
        claude_direction = ml_direction
    
    # Check agreement
    agreement = claude_direction == ml_direction
    
    # Extract confidence (rough estimate from text)
    confidence = 70.0  # Default
    import re
    
    # Look for confidence-related patterns specifically
    # Patterns like "güven: 75%", "confidence: 80%", "%75 güven", "75% güven"
    confidence_patterns = [
        r'güven[:\s]+(\d+)%',
        r'confidence[:\s]+(\d+)%',
        r'%(\d+)\s*güven',
        r'(\d+)%\s*güven',
        r'(\d+)%\s*confidence',
        r'güven\s*seviye[si]*[:\s]+(\d+)',
        r'güven\s*oran[ıi][:\s]+(\d+)',
    ]
    
    for pattern in confidence_patterns:
        match = re.search(pattern, response.lower())
        if match:
            conf_val = float(match.group(1))
            # Sanity check: confidence should be between 40-100
            if 40 <= conf_val <= 100:
                confidence = conf_val
                break
    
    # If no specific pattern found, look for reasonable % values in context
    if confidence == 70.0:
        # Find all percentages and filter for likely confidence values (40-100 range)
        all_percentages = re.findall(r'(\d+)%', response)
        for pct in all_percentages:
            pct_val = float(pct)
            if 40 <= pct_val <= 100:
                confidence = pct_val
                break
    
    # Extract strengths and weaknesses from response
    strengths = []
    weaknesses = []
    observations = []
    
    lines = response.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'güçlü' in line.lower() or 'destekl' in line.lower() or 'strength' in line.lower():
            current_section = 'strengths'
        elif 'zayıf' in line.lower() or 'risk' in line.lower() or 'weak' in line.lower() or 'endişe' in line.lower():
            current_section = 'weaknesses'
        elif line.startswith('-') or line.startswith('•'):
            point = line.lstrip('-•').strip()
            if current_section == 'strengths':
                strengths.append(point)
            elif current_section == 'weaknesses':
                weaknesses.append(point)
            else:
                observations.append(point)
    
    # If we couldn't parse, use the whole response as assessment
    if not strengths:
        strengths = ["ML modeli ile uyumlu analiz"]
    if not weaknesses:
        weaknesses = ["Detaylı risk analizi için tam veri gerekli"]
    
    # Use ML's price levels as defaults
    entry = prediction.get('entry_price', 0)
    sl = prediction.get('stop_price', 0)
    tp = prediction.get('target_price', 0)
    
    # Position size based on confidence
    if confidence >= 75:
        pos_size = "Medium"
    elif confidence >= 60:
        pos_size = "Small"
    else:
        pos_size = "No Trade"
    
    if claude_direction == "HOLD":
        pos_size = "No Trade"
    
    return ClaudeAnalysisResult(
        symbol=symbol,
        ml_direction=ml_direction,
        claude_direction=claude_direction,
        claude_confidence=confidence,
        agreement=agreement,
        general_assessment=response[:500] + "..." if len(response) > 500 else response,
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        recommended_entry=entry,
        recommended_sl=sl,
        recommended_tp=tp,
        position_size_suggestion=pos_size,
        key_observations=observations[:5] if observations else ["Claude analizi tamamlandı"],
        risk_factors=weaknesses[:3],
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_used="claude-sonnet-4-5-20250514"
    )


def _fallback_analysis(prediction: dict, ta_data: dict = None) -> ClaudeAnalysisResult:
    """Independent TA-based analysis when DeepSeek API is unavailable.
    Uses raw technical indicators to form its OWN opinion, separate from ML."""
    
    symbol = prediction.get('symbol', 'Unknown')
    ml_direction = prediction.get('direction', 'HOLD')
    ta = ta_data or {}
    
    # ── Independent scoring from raw TA indicators ──
    buy_score = 0
    sell_score = 0
    strengths = []
    weaknesses = []
    observations = []
    
    close = ta.get('close', 0)
    ema_20 = ta.get('ema_20', close)
    ema_50 = ta.get('ema_50', close)
    ema_200 = ta.get('ema_200', close)
    rsi = ta.get('rsi_14', 50)
    macd_h = ta.get('macd_hist', 0)
    stoch_k = ta.get('stoch_k', 50)
    adx = ta.get('adx', 20)
    boll_z = ta.get('boll_zscore', 0)
    atr = ta.get('atr_14', 0)
    williams = ta.get('williams_r', -50)
    mfi = ta.get('mfi', 50)
    
    # 1) EMA Stack Analysis
    if close > ema_20 > ema_50 > ema_200:
        buy_score += 3
        strengths.append("EMA dizilimi tam yükseliş trendi (20>50>200)")
    elif close < ema_20 < ema_50 < ema_200:
        sell_score += 3
        strengths.append("EMA dizilimi tam düşüş trendi (20<50<200)")
    else:
        observations.append("EMA'lar karışık — net trend yok")
        if close > ema_200:
            buy_score += 1
        else:
            sell_score += 1
    
    # 2) RSI Analysis
    if rsi > 70:
        sell_score += 2
        weaknesses.append(f"RSI aşırı alım bölgesinde ({rsi:.0f})")
    elif rsi < 30:
        buy_score += 2
        strengths.append(f"RSI aşırı satım bölgesinde ({rsi:.0f}) — dönüş fırsatı")
    elif rsi > 55:
        buy_score += 1
        observations.append(f"RSI pozitif bölgede ({rsi:.0f})")
    elif rsi < 45:
        sell_score += 1
        observations.append(f"RSI negatif bölgede ({rsi:.0f})")
    
    # 3) MACD Histogram
    if macd_h > 0:
        buy_score += 1
        strengths.append("MACD histogram pozitif — momentum yukarı")
    else:
        sell_score += 1
        weaknesses.append("MACD histogram negatif — momentum aşağı")
    
    # 4) Stochastic
    if stoch_k > 80:
        sell_score += 1
        weaknesses.append(f"Stochastic aşırı alımda ({stoch_k:.0f})")
    elif stoch_k < 20:
        buy_score += 1
        strengths.append(f"Stochastic aşırı satımda ({stoch_k:.0f})")
    
    # 5) ADX Trend Strength
    if adx >= 25:
        observations.append(f"ADX güçlü trend gösteriyor ({adx:.0f})")
    else:
        weaknesses.append(f"ADX zayıf — trend gücü yetersiz ({adx:.0f})")
    
    # 6) Bollinger Z-Score
    if boll_z > 2:
        sell_score += 1
        weaknesses.append("Fiyat Bollinger üst bandına yakın — geri çekilme riski")
    elif boll_z < -2:
        buy_score += 1
        strengths.append("Fiyat Bollinger alt bandında — sıçrama potansiyeli")
    
    # 7) Williams %R
    if williams > -20:
        sell_score += 1
    elif williams < -80:
        buy_score += 1
    
    # 8) MFI
    if mfi > 80:
        sell_score += 1
        observations.append("MFI aşırı alım — para akışı tersine dönebilir")
    elif mfi < 20:
        buy_score += 1
        observations.append("MFI aşırı satım — alım fırsatı")
    
    # ── Determine independent direction ──
    total_score = buy_score + sell_score
    if buy_score >= sell_score + 2:
        ai_direction = "BUY"
        ai_confidence = min(85, 50 + (buy_score - sell_score) * 5)
    elif sell_score >= buy_score + 2:
        ai_direction = "SELL"
        ai_confidence = min(85, 50 + (sell_score - buy_score) * 5)
    else:
        ai_direction = "HOLD"
        ai_confidence = 45
        observations.append("Göstergeler dengeli — net sinyal yok, beklemek mantıklı")
    
    agreement = ai_direction == ml_direction
    
    # ── Build assessment text ──
    if agreement:
        assessment = f"Bağımsız teknik analiz ML modelin {ml_direction} sinyalini DESTEKLIYOR. "
        assessment += f"Buy skoru: {buy_score}, Sell skoru: {sell_score}. "
        if ai_direction != "HOLD":
            assessment += "Göstergeler aynı yönü işaret ediyor — güvenilirlik yüksek."
        else:
            assessment += "Her iki sistem de bekle diyor — akıllıca."
    else:
        assessment = f"⚠️ Bağımsız teknik analiz ML modelden FARKLI düşünüyor! "
        assessment += f"ML: {ml_direction}, AI Teknik: {ai_direction}. "
        assessment += f"Buy skoru: {buy_score}, Sell skoru: {sell_score}. "
        assessment += "İki sistem uyuşmuyor — dikkatli ol."
    
    if not strengths:
        strengths = ["Analiz tamamlandı"]
    if not weaknesses:
        weaknesses = ["Belirgin risk faktörü tespit edilmedi"]
    
    # ── Price levels (independent from ML) ──
    entry = close
    if atr > 0:
        if ai_direction == "BUY":
            sl = close - atr * 1.5
            tp = close + atr * 2.5
        elif ai_direction == "SELL":
            sl = close + atr * 1.5
            tp = close - atr * 2.5
        else:
            sl = close - atr * 1.0
            tp = close + atr * 1.0
    else:
        sl = prediction.get('stop_price', 0)
        tp = prediction.get('target_price', 0)
    
    pos_size = "Medium" if ai_confidence >= 70 else "Small" if ai_confidence >= 55 else "No Trade"
    if ai_direction == "HOLD":
        pos_size = "No Trade"
    
    return ClaudeAnalysisResult(
        symbol=symbol,
        ml_direction=ml_direction,
        claude_direction=ai_direction,
        claude_confidence=ai_confidence,
        agreement=agreement,
        general_assessment=assessment,
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        recommended_entry=round(entry, 2),
        recommended_sl=round(sl, 2),
        recommended_tp=round(tp, 2),
        position_size_suggestion=pos_size,
        key_observations=observations[:5] if observations else ["Teknik göstergeler analiz edildi"],
        risk_factors=weaknesses[:3],
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_used="independent-ta-engine"
    )


async def get_full_analysis(symbol: str, force_refresh: bool = False) -> dict:
    """
    Get ML prediction and Claude analysis together.
    Cached for 5 minutes to prevent timeout issues.
    """
    from services.ai_panel_analysis_service import get_ai_panel_analysis

    return await get_ai_panel_analysis(symbol, force_refresh=force_refresh)
