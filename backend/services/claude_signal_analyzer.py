"""
Claude AI Signal Analyzer Service
Reviews ML model predictions with full technical analysis context
and provides an independent AI assessment.
"""
from __future__ import annotations

import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Literal

from config import settings

logger = logging.getLogger(__name__)

# Haiku 4.5 - better quality, still cost-effective
CLAUDE_MODEL = "claude-haiku-4-5-20250514"
CLAUDE_MAX_TOKENS = 1200

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
    Send ML prediction and TA data to Claude for independent analysis.
    """
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed")
        return _fallback_analysis(prediction)
    
    api_key = settings.anthropic_api_key
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, using fallback analysis")
        return _fallback_analysis(prediction)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = _build_analysis_prompt(prediction, ta_data)
    
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=TRADING_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        # Parse Claude's response
        return _parse_claude_response(prediction, response_text)
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return _fallback_analysis(prediction)


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


def _fallback_analysis(prediction: dict) -> ClaudeAnalysisResult:
    """Fallback when Claude API is unavailable."""
    
    symbol = prediction.get('symbol', 'Unknown')
    ml_direction = prediction.get('direction', 'HOLD')
    confidence = prediction.get('confidence', 50)
    
    # Simple rule-based assessment
    tech_score = prediction.get('technical_score', 50)
    mom_score = prediction.get('momentum_score', 50)
    trend_score = prediction.get('trend_score', 50)
    
    avg_score = (tech_score + mom_score + trend_score) / 3
    
    if avg_score >= 70 and confidence >= 65:
        assessment = f"ML sinyali güçlü görünüyor. {ml_direction} yönünde yüksek güven."
        strengths = ["Teknik skorlar pozitif", "Momentum destekliyor", "Trend uyumlu"]
        weaknesses = ["Claude API bağlantısı yok - detaylı analiz yapılamadı"]
        claude_direction = ml_direction
        claude_conf = confidence * 0.9
    elif avg_score >= 50:
        assessment = f"ML sinyali orta güçte. {ml_direction} yönünde dikkatli yaklaşım önerilir."
        strengths = ["Bazı göstergeler destekliyor"]
        weaknesses = ["Mixed signals", "Claude API bağlantısı yok"]
        claude_direction = ml_direction
        claude_conf = confidence * 0.7
    else:
        assessment = "Sinyal zayıf. İşlem önerilmez."
        strengths = []
        weaknesses = ["Düşük skorlar", "Belirsiz yön", "Claude API bağlantısı yok"]
        claude_direction = "HOLD"
        claude_conf = 40
    
    return ClaudeAnalysisResult(
        symbol=symbol,
        ml_direction=ml_direction,
        claude_direction=claude_direction,
        claude_confidence=claude_conf,
        agreement=claude_direction == ml_direction,
        general_assessment=assessment,
        strengths=strengths,
        weaknesses=weaknesses,
        recommended_entry=prediction.get('entry_price', 0),
        recommended_sl=prediction.get('stop_price', 0),
        recommended_tp=prediction.get('target_price', 0),
        position_size_suggestion="Small" if claude_direction != "HOLD" else "No Trade",
        key_observations=["Fallback analiz modu - Claude API bağlantısı gerekli"],
        risk_factors=["API bağlantısı yok", "Tam analiz yapılamadı"],
        timestamp=datetime.utcnow().isoformat() + "Z",
        model_used="fallback"
    )


async def get_full_analysis(symbol: str) -> dict:
    """
    Get ML prediction and Claude analysis together.
    """
    from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
    from services.data_fetcher import fetch_eod_candles, fetch_latest_price
    import numpy as np
    
    # Get ML prediction
    ml_prediction = await get_ml_prediction(symbol)
    prediction_dict = {
        'symbol': ml_prediction.symbol,
        'direction': ml_prediction.direction,
        'confidence': ml_prediction.confidence,
        'probability_up': ml_prediction.probability_up,
        'probability_down': ml_prediction.probability_down,
        'target_pips': ml_prediction.target_pips,
        'stop_pips': ml_prediction.stop_pips,
        'risk_reward': ml_prediction.risk_reward,
        'entry_price': ml_prediction.entry_price,
        'target_price': ml_prediction.target_price,
        'stop_price': ml_prediction.stop_price,
        'technical_score': ml_prediction.technical_score,
        'momentum_score': ml_prediction.momentum_score,
        'trend_score': ml_prediction.trend_score,
        'volatility_regime': ml_prediction.volatility_regime,
        'reasoning': ml_prediction.reasoning,
        'key_levels': ml_prediction.key_levels,
    }
    
    # Get TA data for Claude
    normalized_symbol = "NDX.INDX" if symbol.upper() in ["NASDAQ", "NDX.INDX", "NDX"] else symbol.upper()
    candles = await fetch_eod_candles(normalized_symbol, limit=250)
    live_price = await fetch_latest_price(normalized_symbol)
    
    if candles:
        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c["high"] for c in candles], dtype=float)
        lows = np.array([c["low"] for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)
        
        ta_data = _compute_technical_indicators(closes, highs, lows, volumes)
        ta_data["close"] = float(live_price) if live_price else float(closes[-1])
    else:
        ta_data = {"close": 0}
    
    # Get Claude analysis
    claude_result = await analyze_signal_with_claude(prediction_dict, ta_data)
    
    return {
        "ml_prediction": prediction_dict,
        "claude_analysis": {
            "symbol": claude_result.symbol,
            "ml_direction": claude_result.ml_direction,
            "claude_direction": claude_result.claude_direction,
            "claude_confidence": claude_result.claude_confidence,
            "agreement": claude_result.agreement,
            "general_assessment": claude_result.general_assessment,
            "strengths": claude_result.strengths,
            "weaknesses": claude_result.weaknesses,
            "recommended_entry": claude_result.recommended_entry,
            "recommended_sl": claude_result.recommended_sl,
            "recommended_tp": claude_result.recommended_tp,
            "position_size_suggestion": claude_result.position_size_suggestion,
            "key_observations": claude_result.key_observations,
            "risk_factors": claude_result.risk_factors,
            "timestamp": claude_result.timestamp,
            "model_used": claude_result.model_used,
        },
        "ta_snapshot": {
            "close": ta_data.get("close", 0),
            "ema_20": ta_data.get("ema_20", 0),
            "ema_50": ta_data.get("ema_50", 0),
            "ema_200": ta_data.get("ema_200", 0),
            "rsi_14": ta_data.get("rsi_14", 50),
            "macd_hist": ta_data.get("macd_hist", 0),
            "atr_14": ta_data.get("atr_14", 0),
            "boll_zscore": ta_data.get("boll_zscore", 0),
        }
    }
