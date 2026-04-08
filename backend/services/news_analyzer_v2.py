"""
GERÇEK News Analyzer V2
Her haberi gerçekten analiz eden, içeriğe göre dinamik sonuç üreten sistem
"""

import json
import os
import logging
import re
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from anthropic import Anthropic

from services.deepseek_json_client import call_deepseek_json, extract_json_object

DEEPSEEK_API_KEY = os.getenv("DEEP_SEEKR1", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

logger = logging.getLogger(__name__)

_SYMBOL_ALIASES = {
    "XAUUSD": "XAUUSD",
    "GOLD": "XAUUSD",
    "NDX": "NDX",
    "NASDAQ": "NDX",
    "DAX": "DAX",
    "GDAXI": "DAX",
    "USOIL": "USOIL",
    "OIL": "USOIL",
    "WTI": "USOIL",
    "CL": "USOIL",
    "VIX": "VIX",
    "DXY": "DXY",
    "USD": "DXY",
}

_GEOPOLITICAL_TERMS = {
    "iran", "israel", "gaza", "hamas", "hezbollah", "middle east", "hormuz", "strait of hormuz",
    "war", "conflict", "military", "attack", "strike", "missile", "ceasefire", "truce", "peace talks",
    "savaş", "çatışma", "askeri", "saldırı", "füze", "ateşkes", "barış", "gerilim", "iran cumhurbaşkanı",
}

_DEESCALATION_TERMS = {
    "does not want war", "doesn't want war", "not seeking war", "avoid war", "end the war", "end war",
    "ready to end the war", "ready to end war", "open to a solution", "open to solution", "de-escalation",
    "deescalation", "ceasefire", "truce", "peace talks", "wants peace", "seeking peace", "cooling tensions",
    "savaş istemiyor", "savaşa son", "savaşı sonlandır", "çözümüne açıklık", "çözüme açıklık", "ateşkes",
    "barış görüşmeleri", "gerilimin azalması", "gerilim azalıyor", "çatışmayı bitirmeye hazır",
}

_ESCALATION_TERMS = {
    "war declaration", "escalation", "escalates", "retaliation", "retaliate", "airstrike", "missile strike",
    "military strike", "attack", "attacks", "invasion", "troops", "bombing", "threatens", "supply disruption",
    "tırmanma", "tırmanıyor", "misilleme", "hava saldırısı", "saldırı", "işgal", "bombardıman", "tehdit",
}

_OIL_SENSITIVE_GEO_TERMS = {
    "iran", "hormuz", "strait of hormuz", "middle east", "oil", "crude", "petrol", "opec", "energy",
}

_USD_STRENGTH_TERMS = {
    "hawkish fed", "rate hike", "higher rates", "strong dollar", "dollar strength", "fed sıkı", "faiz artışı",
    "güçlü dolar", "şahin fed",
}

_EXPLICIT_DIRECTION_PHRASES = {
    "USOIL": {
        "bullish": {"oil rose", "oil rises", "oil rallied", "oil climbs", "crude rose", "crude rallied", "petrol yükseldi", "petrol arttı", "petrol tırmandı"},
        "bearish": {"oil fell", "oil falls", "oil dropped", "oil drops", "oil slides", "crude fell", "crude dropped", "petrol düştü", "petrol geriledi", "petrol düștü"},
    },
    "VIX": {
        "bullish": {"vix rose", "vix rises", "vix jumped", "vix spikes", "vix increased", "vix yükseldi", "vix arttı"},
        "bearish": {"vix fell", "vix falls", "vix eased", "vix dropped", "vix declined", "vix düştü", "vix geriledi", "vix düștü"},
    },
    "NDX": {
        "bullish": {"nasdaq rose", "nasdaq rises", "nasdaq rallied", "nasdaq jumps", "tech stocks rose", "nasdaq yükseldi", "nasdaq toparlandı", "nasdaq ralli"},
        "bearish": {"nasdaq fell", "nasdaq falls", "nasdaq dropped", "nasdaq slides", "tech stocks fell", "nasdaq düştü", "nasdaq geriledi", "nasdaq düștü"},
    },
    "XAUUSD": {
        "bullish": {"gold rose", "gold rises", "gold climbed", "gold gains", "bullion rose", "altın yükseldi", "altın arttı"},
        "bearish": {"gold fell", "gold falls", "gold dropped", "gold slides", "bullion fell", "altın düştü", "altın geriledi", "altın düștü"},
    },
    "DXY": {
        "bullish": {"dxy rose", "dxy rises", "dollar rose", "dollar strengthens", "usd strengthened", "dxy yükseldi", "dolar güçlendi", "dolar yükseldi"},
        "bearish": {"dxy fell", "dxy falls", "dollar weakened", "usd weakened", "dxy düştü", "dolar zayıfladı", "dolar geriledi", "dxy düștü"},
    },
}


def _normalize_symbol_alias(symbol: Any) -> str:
    return _SYMBOL_ALIASES.get(str(symbol or "").strip().upper(), str(symbol or "").strip().upper())


def _contains_any(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_consistency_text(*parts: Any) -> str:
    normalized_parts: List[str] = []
    for part in parts:
        if isinstance(part, str) and part.strip():
            normalized_parts.append(part.strip().lower())
    return "\n".join(normalized_parts)


def _infer_explicit_direction(symbol: str, text: str) -> Optional[str]:
    phrase_map = _EXPLICIT_DIRECTION_PHRASES.get(symbol)
    if not phrase_map:
        return None
    if _contains_any(text, phrase_map["bearish"]):
        return "bearish"
    if _contains_any(text, phrase_map["bullish"]):
        return "bullish"
    return None


def _override_reason(symbol: str, direction: str, cause: str, lang: str) -> str:
    if cause == "explicit_price_move":
        if lang == "tr":
            return f"Metin {symbol} ile ilişkili varlığın fiyat yönünü açıkça {direction == 'bullish' and 'yukarı' or 'aşağı'} gösterdiği için etki {direction == 'bullish' and 'yükseliş' or 'düşüş'} olarak hizalandı."
        return f"The article explicitly states a {direction} price move for {symbol}, so the impact was aligned to that direct move."
    if cause == "geopolitical_deescalation":
        if lang == "tr":
            return f"Jeopolitik gerilimin azalması {symbol} üzerindeki güvenli liman/korku primini zayıflattığı için etki {direction == 'bullish' and 'yükseliş' or 'düşüş'} yönünde düzeltildi."
        return f"Geopolitical de-escalation reduces the fear or safe-haven premium around {symbol}, so the impact was corrected to {direction}."
    if cause == "geopolitical_escalation":
        if lang == "tr":
            return f"Jeopolitik tırmanma {symbol} üzerinde riskten kaçış ve arz primi yarattığı için etki {direction == 'bullish' and 'yükseliş' or 'düşüş'} yönünde düzeltildi."
        return f"Geopolitical escalation increases fear, safe-haven demand, or supply risk around {symbol}, so the impact was corrected to {direction}."
    if lang == "tr":
        return f"Metindeki makro bağlam ile uyum için {symbol} etkisi {direction == 'bullish' and 'yükseliş' or 'düşüş'} yönüne düzeltildi."
    return f"The {symbol} impact was corrected to {direction} to stay consistent with the article context."


def enforce_news_analysis_consistency(
    *,
    headline: str = "",
    content: str = "",
    summary_en: str = "",
    analysis_en: str = "",
    summary_tr: str = "",
    analysis_tr: str = "",
    impacts: Optional[List[Dict[str, Any]]] = None,
    sentiment: str = "neutral",
) -> tuple[List[Dict[str, Any]], str]:
    text = _build_consistency_text(headline, content, summary_en, analysis_en, summary_tr, analysis_tr)
    has_geo_context = _contains_any(text, _GEOPOLITICAL_TERMS)
    is_deescalation = has_geo_context and _contains_any(text, _DEESCALATION_TERMS)
    is_escalation = has_geo_context and _contains_any(text, _ESCALATION_TERMS) and not is_deescalation
    adjusted_impacts: List[Dict[str, Any]] = []

    for raw_impact in impacts or []:
        if not isinstance(raw_impact, dict):
            continue
        impact = dict(raw_impact)
        symbol = _normalize_symbol_alias(impact.get("symbol"))
        original_direction = str(impact.get("direction") or "neutral").strip().lower()
        override_direction = _infer_explicit_direction(symbol, text)
        override_cause: Optional[str] = "explicit_price_move" if override_direction else None

        if override_direction is None and is_deescalation:
            if symbol == "VIX":
                override_direction = "bearish"
            elif symbol == "NDX":
                override_direction = "bullish"
            elif symbol == "XAUUSD":
                override_direction = "bearish"
            elif symbol == "USOIL" and _contains_any(text, _OIL_SENSITIVE_GEO_TERMS):
                override_direction = "bearish"
            elif symbol == "DXY" and not _contains_any(text, _USD_STRENGTH_TERMS):
                override_direction = "bearish"
            if override_direction:
                override_cause = "geopolitical_deescalation"
        elif override_direction is None and is_escalation:
            if symbol == "VIX":
                override_direction = "bullish"
            elif symbol == "NDX":
                override_direction = "bearish"
            elif symbol == "XAUUSD":
                override_direction = "bullish"
            elif symbol == "USOIL" and _contains_any(text, _OIL_SENSITIVE_GEO_TERMS):
                override_direction = "bullish"
            elif symbol == "DXY" and not _contains_any(text, {"dollar weakened", "usd weakened", "dolar zayıfladı"}):
                override_direction = "bullish"
            if override_direction:
                override_cause = "geopolitical_escalation"

        if override_direction and override_direction != original_direction:
            score_key = "impact_score" if "impact_score" in impact else "score"
            impact["direction"] = override_direction
            impact[score_key] = max(_safe_int(impact.get(score_key), 0), 7 if override_cause == "explicit_price_move" else 6)
            impact["confidence"] = round(max(_safe_float(impact.get("confidence"), 0.0), 0.74 if override_cause == "explicit_price_move" else 0.68), 2)
            impact["reasoning"] = _override_reason(symbol, override_direction, override_cause or "context", "en")
            impact["reasoning_tr"] = _override_reason(symbol, override_direction, override_cause or "context", "tr")

        adjusted_impacts.append(impact)

    normalized_sentiment = str(sentiment or "neutral").strip().lower()
    if is_deescalation:
        normalized_sentiment = "risk_on"
    elif is_escalation:
        normalized_sentiment = "risk_off"

    return adjusted_impacts, normalized_sentiment

@dataclass
class SymbolImpact:
    symbol: str
    direction: str  # bullish, bearish, neutral
    score: int  # 1-10
    confidence: float  # 0-1
    reasoning: str
    reasoning_tr: str = ""

@dataclass
class NewsAnalysisResult:
    impacts: List[SymbolImpact]
    sentiment: str  # risk_on, risk_off, neutral
    volatility_expectation: str  # high, medium, low
    urgency: str  # breaking, high, medium, low
    confidence: float  # 0-100
    summary_en: str = ""
    summary_tr: str = ""
    analysis_en: str = ""
    analysis_tr: str = ""
    headline_tr: str = ""
    content_tr: str = ""
    importance_level: str = "medium"
    importance_score: int = 60
    importance_reason: str = ""
    ai_model: str = "deepseek-reasoner"


class RealNewsAnalyzer:
    """
    GERÇEK haber analizi - Her haberi özgün olarak değerlendirir
    """
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY

    def _coerce_text(self, value: Any, fallback: str = "") -> str:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        if isinstance(fallback, str):
            return fallback.strip()
        return ""

    @staticmethod
    def _validate_turkish(text: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        cleaned = re.sub(r"^\s*\[(?:TR|TURKISH)\]\s*", "", text.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"^\s*(?:tr|turkish)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return ""

        turkish_chars = set("çÇğĞıİöÖşŞüÜ")
        has_turkish_chars = any(c in turkish_chars for c in cleaned)
        lower = cleaned.lower()

        forbidden_english_terms = {
            "bullish", "bearish", "neutral", "volatility", "confidence",
            "summary", "analysis", "headline", "breaking", "impact",
        }
        tokens = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü']+", cleaned)
        lower_tokens = [token.lower() for token in tokens]
        if any(token in forbidden_english_terms for token in lower_tokens):
            return ""

        turkish_markers = {
            "için", "ile", "olan", "bir", "ve", "veya", "ancak", "ise", "olarak",
            "üzerinde", "etki", "piyasa", "yükseliş", "düşüş", "beklenti",
            "açıkladı", "artış", "azalış", "gösterge", "fiyat", "oran",
            "faiz", "karar", "sonrası", "destekledi", "baskıladı", "veri",
            "güçlü", "zayıf", "sınırlı", "bekleniyor", "nedeniyle", "çünkü",
            "altın", "petrol", "dolar", "endeks", "hisse", "talep", "arz",
        }
        english_markers = {
            "the", "and", "for", "with", "after", "before", "from", "this",
            "that", "market", "price", "gold", "oil", "stock", "shares",
            "rise", "fall", "higher", "lower", "expected", "guidance",
        }

        turkish_marker_count = sum(1 for token in lower_tokens if token in turkish_markers)
        english_marker_count = sum(1 for token in lower_tokens if token in english_markers)

        if not has_turkish_chars and turkish_marker_count == 0:
            return ""

        if len(lower_tokens) >= 5 and english_marker_count >= max(2, turkish_marker_count + 1):
            return ""

        if len(lower_tokens) >= 8 and english_marker_count > (len(lower_tokens) * 0.35):
            return ""

        return cleaned

    def _normalize_importance_level(self, value: Any, score: int) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"critical", "high", "medium", "low"}:
            return normalized
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    def _normalize_urgency(
        self,
        raw_urgency: Any,
        confidence: float,
        impacts: List[Dict[str, Any]],
        importance_score: int,
    ) -> str:
        urgency = str(raw_urgency or "medium").strip().lower()
        if urgency not in {"breaking", "high", "medium", "low"}:
            urgency = "medium"

        max_impact_score = max((int(imp.get("impact_score", 0)) for imp in impacts), default=0)
        has_directional_high_impact = any(
            str(imp.get("direction", "neutral")).lower() in {"bullish", "bearish"}
            and int(imp.get("impact_score", 0)) >= 8
            for imp in impacts
        )

        # Guardrail: avoid under-classifying clearly market-moving headlines.
        if urgency in {"medium", "low"} and (
            (max_impact_score >= 9 and confidence >= 80)
            or (importance_score >= 88 and has_directional_high_impact)
        ):
            return "high"

        return urgency
        
    async def analyze(self, headline: str, content: str = "", source: str = "", market_context: Optional[Dict[str, Any]] = None) -> NewsAnalysisResult:
        """
        Haberi gerçekten analiz et - Rule-based değil, AI-based.
        market_context: optional dict with current prices/direction for richer analysis.
        """
        logger.info(f"[RealAnalyzer] Analyzing: {headline[:60]}...")
        logger.info(f"[RealAnalyzer] API key present: {bool(self.api_key)}")

        if not self.api_key:
            logger.warning("[RealAnalyzer] No API key, using fallback")
            return self._fallback_analysis(headline, content)

        try:
            prompt = self._build_prompt(headline, content, source, market_context=market_context)
            logger.info(f"[RealAnalyzer] Prompt built, calling DeepSeek...")
            result = await self._call_deepseek(prompt, headline=headline, article_content=content)
            
            logger.info(f"[RealAnalyzer] AI analysis successful: confidence={result.confidence}")
            return result
            
        except Exception as e:
            import traceback
            logger.error(f"[RealAnalyzer] AI failed: {e}")
            logger.error(f"[RealAnalyzer] Traceback: {traceback.format_exc()}")
            print(f"[RealAnalyzer] AI failed: {e}")
            print(f"[RealAnalyzer] Traceback: {traceback.format_exc()}")
            if ANTHROPIC_API_KEY:
                try:
                    logger.info("[RealAnalyzer] Attempting Anthropic fallback")
                    result = await self._call_anthropic(prompt, headline=headline, article_content=content)
                    logger.info(f"[RealAnalyzer] Anthropic analysis successful: confidence={result.confidence}")
                    return result
                except Exception as anthropic_error:
                    logger.error(f"[RealAnalyzer] Anthropic fallback failed: {anthropic_error}")
            return self._fallback_analysis(headline, content)
    
    @staticmethod
    def _format_market_context(ctx: Optional[Dict[str, Any]]) -> str:
        if not ctx:
            return ""
        lines = ["\nCURRENT MARKET SNAPSHOT (live prices at analysis time):"]
        for sym, info in ctx.items():
            if isinstance(info, dict):
                lines.append(f"  {sym}: price={info.get('price','?')}, chg={info.get('change_pct','?')}%")
            else:
                lines.append(f"  {sym}: {info}")
        return "\n".join(lines) + "\n"

    def _build_prompt(self, headline: str, content: str, source: str, *, market_context: Optional[Dict[str, Any]] = None) -> str:
        """
        DeepSeek için prompt oluştur - Her haber için özel
        URGENCY belirleme kritik - Büyük fiyat hareketlerini tetikleyen haberleri tespit et
        """
        mkt = self._format_market_context(market_context)
        return f"""Analyze this financial news article and determine its ACTUAL market impact.

NEWS HEADLINE: {headline}
NEWS CONTENT: {content[:800] if content else "No additional content"}
SOURCE: {source}
DATE: {datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
{mkt}

INSTRUCTIONS:
1. Read the headline and content carefully
2. Identify the MAIN subject (which company, sector, country, or asset)
3. Determine if this is POSITIVE, NEGATIVE, or NEUTRAL news
4. Decide which financial instruments are ACTUALLY affected (not generic list)
5. Determine URGENCY level based on potential to cause IMMEDIATE price movement

URGENCY LEVEL CRITERIA - BE STRICT:
- "breaking": ONLY for major unexpected events that cause immediate volatility
  * Examples: War declarations, major central bank surprises, Trump policy shocks
  * Market impact: Immediate 1%+ price movement likely
  
- "high": Significant market-moving news with clear directional impact
  * Examples: Fed rate decisions, major earnings beats/misses, geopolitical escalation
  * Market impact: 0.5-1% price movement likely within minutes
  * Must have HIGH confidence (>75%) and score (>=7)
  
- "medium": Moderate impact news, market will react but less dramatically
  * Examples: Economic data releases (NFP, CPI), sector-specific news
  * Market impact: 0.2-0.5% price movement
  
- "low": Background news, minimal immediate impact
  * Examples: Analyst upgrades/downgrades, routine economic reports
  * Market impact: <0.2% or delayed reaction

SCORING GUIDE - BE CONSERVATIVE:
- 9-10: Market-defining events (Black swan, major war, 2008-style crisis)
- 7-8: Major market movers (Fed surprise, major conflict escalation)
- 5-6: Notable but expected (Scheduled economic data, earnings)
- 3-4: Minor impact (Sector news, analyst reports)
- 1-2: Almost no impact (Routine announcements)

EXAMPLES OF CORRECT ANALYSIS:

Example 1 - BREAKING:
Headline: "Trump announces 25% tariffs on all Chinese goods effective immediately"
→ Urgency: "breaking" - Immediate market shock
→ NASDAQ (bearish, 9/10) - Trade war escalation
→ XAUUSD (bullish, 8/10) - Safe haven rush
→ DXY (bullish, 7/10) - Flight to safety

Example 2 - HIGH:
Headline: "Fed unexpectedly cuts rates by 50bps amid recession fears"
→ Urgency: "high" - Major policy surprise
→ DXY (bearish, 8/10) - Rate cut weakens USD
→ XAUUSD (bullish, 8/10) - Lower rates boost gold
→ NASDAQ (bullish, 7/10) - Cheaper borrowing helps tech

Example 3 - MEDIUM:
Headline: "NFP comes in at 180k vs 200k expected, unemployment steady"
→ Urgency: "medium" - Expected data release, moderate impact
→ DXY (bearish, 5/10) - Slight miss but not shocking
→ XAUUSD (neutral, 4/10) - Minimal impact

Example 4 - LOW:
Headline: "Goldman Sachs upgrades Apple to buy, raises target to $220"
→ Urgency: "low" - Single stock, expected analyst action
→ NASDAQ (neutral, 3/10) - Minimal broad market impact
→ XAUUSD (neutral, 1/10) - No gold impact

Example 5 - DE-ESCALATION:
Headline: "Iran says it does not want war and is ready to end fighting if guarantees are met"
→ Urgency: "high" or "medium" depending on immediacy
→ VIX (bearish) - Fear premium eases
→ NASDAQ (bullish) - Risk appetite improves
→ XAUUSD (bearish) - Safe-haven demand eases
→ USOIL (bearish if Middle East supply risk eases)

Example 6 - EXPLICIT PRICE MOVE:
Headline: "Oil falls on signs of diplomatic progress between the US and Iran"
→ USOIL MUST be bearish, not bullish
→ If the article explicitly says an asset fell/dropped/slid, do NOT return bullish for that same asset

RESPONSE FORMAT (STRICT JSON - ALL FIELDS REQUIRED):
{{
    "summary_en": "English summary of the news in 1-2 clear sentences",
    "summary_tr": "Haberin Türkçe özeti - profesyonel finans Türkçesi ile 1-2 net cümle",
    "analysis_en": "English market impact analysis in 2-4 sentences explaining WHY markets react",
    "analysis_tr": "Piyasa etki analizi Türkçe olarak 2-4 cümle. Piyasaların NEDEN tepki verdiğini açıklayın.",
    "headline_tr": "Haber başlığının tam ve doğru Türkçe çevirisi",
    "content_tr": "Türkçe detaylı analiz içeriği - analysis_tr ile tutarlı olmalı",
    "urgency": "breaking|high|medium|low",
    "importance_level": "critical|high|medium|low",
    "importance_score": "<integer 0-100: importance for markets RIGHT NOW>",
    "importance_reason": "Short explanation of why this news matters right now",
    "market_sentiment": "risk_on|risk_off|neutral",
    "volatility_expectation": "high|medium|low",
    "analysis_confidence": "<integer 0-100: your confidence - VARY per news>",
    "affected_instruments": [
        {{
            "symbol": "XAUUSD|NDX|DAX|USOIL|VIX|DXY",
            "direction": "bullish|bearish|neutral",
            "impact_score": "<integer 1-10>",
            "confidence": "<float 0.0-1.0: MUST vary per instrument>",
            "reasoning": "English: specific causal explanation for THIS instrument",
            "reasoning_tr": "Türkçe: bu enstrümanın NEDEN etkilendiğinin spesifik açıklaması"
        }}
    ],
    "logic": "Brief explanation of your analysis logic"
}}

CRITICAL RULES FOR TURKISH (TR) FIELDS:
- headline_tr, summary_tr, analysis_tr, content_tr MUST be PURE Turkish. NO English words.
- Do NOT add Turkish suffixes to English words. Write natural, fluent Turkish.
- Do NOT prefix with "[TR]". Write as a native Turkish finance journalist would.
- Use professional financial Turkish: "yükseliş" not "bullish", "düşüş" not "bearish".
- reasoning_tr MUST be a complete Turkish sentence explaining the causal mechanism.

CRITICAL RULES FOR CONFIDENCE VALUES:
- analysis_confidence: 30-95 range. MUST NOT always be 75.
- Per-instrument confidence MUST vary per instrument:
  * Primary/direct impact: 0.80-0.95
  * Secondary/indirect: 0.55-0.79
  * Speculative/weak: 0.30-0.54

IMPORTANT RULES:
- summary_en, summary_tr, analysis_en, analysis_tr, headline_tr, content_tr MUST NOT be empty.
- summary_en/analysis_en MUST be English. summary_tr/analysis_tr MUST be Turkish.
- Be CONSERVATIVE with urgency - "breaking" RARE (<5%), "high" selective (<15%)
- Score and urgency CONSISTENT (high urgency = high score)
- ONLY include instruments ACTUALLY affected by this specific news

Analyze this news NOW:"""

    async def _call_deepseek(self, prompt: str, headline: str = "", article_content: str = "") -> NewsAnalysisResult:
        """DeepSeek AI çağrısı - Hata loglamalı ve robust"""
        logger.info(f"[DeepSeek] Calling API with key present: {bool(self.api_key)}")
        
        try:
            result = await call_deepseek_json(
                "You are an expert financial analyst. Analyze news precisely and only report ACTUAL impacts, not generic patterns. Respond ONLY with valid JSON.\n\n" + prompt,
                api_key=self.api_key,
                max_tokens=1800,
                temperature=0.1,
                timeout_seconds=75,
            )
            if not isinstance(result, dict):
                raise Exception("DeepSeek returned no parseable JSON payload")

            summary_en = self._coerce_text(result.get("summary_en"), headline)
            headline_tr = self._validate_turkish(self._coerce_text(result.get("headline_tr")))
            summary_tr = self._validate_turkish(self._coerce_text(result.get("summary_tr")))
            analysis_en = self._coerce_text(
                result.get("analysis_en"),
                self._coerce_text(result.get("logic"), article_content[:280] if article_content else headline)
            )
            analysis_tr = self._validate_turkish(self._coerce_text(result.get("analysis_tr")))
            content_tr = self._validate_turkish(self._coerce_text(result.get("content_tr")))

            logger.info(f"[DeepSeek] Parsed result: headline_tr={headline_tr[:50]}...")
            
            raw_impacts = result.get("affected_instruments", [])
            raw_impacts, normalized_sentiment = enforce_news_analysis_consistency(
                headline=headline,
                content=article_content,
                summary_en=summary_en,
                analysis_en=analysis_en,
                summary_tr=summary_tr,
                analysis_tr=analysis_tr,
                impacts=raw_impacts,
                sentiment=result.get("market_sentiment", "neutral"),
            )
            impacts = []
            for imp in raw_impacts:
                try:
                    imp_score = int(imp.get("impact_score", 0))
                except (TypeError, ValueError):
                    imp_score = 0
                try:
                    imp_conf = float(imp.get("confidence", 0))
                except (TypeError, ValueError):
                    imp_conf = 0.5
                if imp_score >= 4 or imp_conf >= 0.6:
                    impacts.append(SymbolImpact(
                        symbol=imp["symbol"],
                        direction=imp["direction"],
                        score=imp_score,
                        confidence=imp_conf,
                        reasoning=imp.get("reasoning", ""),
                        reasoning_tr=self._validate_turkish(self._coerce_text(imp.get("reasoning_tr")))
                    ))
            
            if not impacts:
                logger.info("[DeepSeek] No tracked instruments were materially affected by this news item")

            raw_conf = result.get("analysis_confidence", 50)
            try:
                confidence = float(raw_conf)
            except (TypeError, ValueError):
                confidence = 50.0
            confidence = max(0.0, min(100.0, confidence))
            importance_score_raw = result.get("importance_score", 0)
            try:
                importance_score = int(round(float(importance_score_raw)))
            except (TypeError, ValueError):
                importance_score = 0

            if importance_score <= 0:
                max_impact = max((int(item.get("impact_score", 0)) for item in raw_impacts), default=0)
                confidence_component = int(max(0, min(100, confidence)))
                importance_score = int(
                    round(
                        max_impact * 6.5
                        + confidence_component * 0.35
                    )
                )
            importance_score = max(0, min(100, importance_score))

            importance_level = self._normalize_importance_level(
                result.get("importance_level"),
                importance_score,
            )
            importance_reason = self._coerce_text(
                result.get("importance_reason"),
                self._coerce_text(result.get("logic"), "AI classified this headline based on directional impact and confidence."),
            )
            urgency = self._normalize_urgency(
                result.get("urgency", "medium"),
                confidence,
                raw_impacts,
                importance_score,
            )
            
            logger.info(f"[DeepSeek] Successfully parsed result: confidence={result.get('analysis_confidence', 0)}, headline_tr={result.get('headline_tr', 'N/A')[:50]}...")
            
            return NewsAnalysisResult(
                impacts=impacts,
                sentiment=normalized_sentiment,
                volatility_expectation=result.get("volatility_expectation", "medium"),
                urgency=urgency,
                confidence=confidence,
                summary_en=summary_en,
                summary_tr=summary_tr,
                analysis_en=analysis_en,
                analysis_tr=analysis_tr,
                headline_tr=headline_tr,
                content_tr=content_tr,
                importance_level=importance_level,
                importance_score=importance_score,
                importance_reason=importance_reason,
                ai_model=result.get("ai_model") or "deepseek-reasoner",
            )
        except Exception as e:
            import traceback
            logger.error(f"[DeepSeek] Exception during API call: {type(e).__name__}: {e}")
            logger.error(f"[DeepSeek] Full traceback: {traceback.format_exc()}")
            raise

    async def _call_anthropic(self, prompt: str, headline: str = "", article_content: str = "") -> NewsAnalysisResult:
        logger.info(f"[Anthropic] Calling API with key present: {bool(ANTHROPIC_API_KEY)}")
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        def _invoke():
            return client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1800,
                temperature=0.1,
                system="You are an expert financial analyst. Analyze news precisely and only report ACTUAL impacts, not generic patterns. Respond ONLY with valid JSON.",
                messages=[{"role": "user", "content": prompt}],
            )

        response = await asyncio.to_thread(_invoke)

        text = ""
        for block in getattr(response, "content", []) or []:
            if getattr(block, "type", "") == "text":
                text = str(getattr(block, "text", "") or "")
                break

        result = extract_json_object(text)
        if not isinstance(result, dict):
            raise Exception("Anthropic returned no parseable JSON payload")

        summary_en = self._coerce_text(result.get("summary_en"), headline)
        headline_tr = self._validate_turkish(self._coerce_text(result.get("headline_tr")))
        summary_tr = self._validate_turkish(self._coerce_text(result.get("summary_tr")))
        analysis_en = self._coerce_text(
            result.get("analysis_en"),
            self._coerce_text(result.get("logic"), article_content[:280] if article_content else headline)
        )
        analysis_tr = self._validate_turkish(self._coerce_text(result.get("analysis_tr")))
        content_tr = self._validate_turkish(self._coerce_text(result.get("content_tr")))

        raw_impacts = result.get("affected_instruments", [])
        raw_impacts, normalized_sentiment = enforce_news_analysis_consistency(
            headline=headline,
            content=article_content,
            summary_en=summary_en,
            analysis_en=analysis_en,
            summary_tr=summary_tr,
            analysis_tr=analysis_tr,
            impacts=raw_impacts,
            sentiment=result.get("market_sentiment", "neutral"),
        )
        impacts = []
        for imp in raw_impacts:
            try:
                imp_score = int(imp.get("impact_score", 0))
            except (TypeError, ValueError):
                imp_score = 0
            try:
                imp_conf = float(imp.get("confidence", 0))
            except (TypeError, ValueError):
                imp_conf = 0.5
            if imp_score >= 4 or imp_conf >= 0.6:
                impacts.append(SymbolImpact(
                    symbol=imp["symbol"],
                    direction=imp["direction"],
                    score=imp_score,
                    confidence=imp_conf,
                    reasoning=imp.get("reasoning", ""),
                    reasoning_tr=self._validate_turkish(self._coerce_text(imp.get("reasoning_tr")))
                ))

        try:
            confidence = float(result.get("analysis_confidence", 50))
        except (TypeError, ValueError):
            confidence = 50.0
        confidence = max(0.0, min(100.0, confidence))

        try:
            importance_score = int(round(float(result.get("importance_score", 0))))
        except (TypeError, ValueError):
            importance_score = 0
        if importance_score <= 0:
            max_impact = max((int(item.get("impact_score", 0)) for item in raw_impacts), default=0)
            importance_score = int(round(max_impact * 6.5 + confidence * 0.35))
        importance_score = max(0, min(100, importance_score))

        importance_level = self._normalize_importance_level(
            result.get("importance_level"),
            importance_score,
        )
        importance_reason = self._coerce_text(
            result.get("importance_reason"),
            self._coerce_text(result.get("logic"), "AI classified this headline based on directional impact and confidence."),
        )
        urgency = self._normalize_urgency(
            result.get("urgency", "medium"),
            confidence,
            raw_impacts,
            importance_score,
        )

        return NewsAnalysisResult(
            impacts=impacts,
            sentiment=normalized_sentiment,
            volatility_expectation=result.get("volatility_expectation", "medium"),
            urgency=urgency,
            confidence=confidence,
            summary_en=summary_en,
            summary_tr=summary_tr,
            analysis_en=analysis_en,
            analysis_tr=analysis_tr,
            headline_tr=headline_tr,
            content_tr=content_tr,
            importance_level=importance_level,
            importance_score=importance_score,
            importance_reason=importance_reason,
            ai_model=result.get("ai_model") or "claude-3-haiku-20240307",
        )
    
    def _fallback_analysis(self, headline: str, content: str) -> NewsAnalysisResult:
        """
        AI çalışmazsa basit keyword analizi - ama yine de spesifik
        """
        text = f"{headline} {content}".lower()
        
        impacts = []
        
        # === GEOPOLITICAL: Iran-specific ===
        if any(word in text for word in ["iran", "iranian", "tehran", "strait of hormuz"]):
            if any(word in text for word in ["war", "strike", "attack", "military", "escalation", "conflict"]):
                impacts.append(SymbolImpact(symbol="USOIL", direction="bullish", score=9, confidence=0.75,
                    reasoning="Iran military conflict threatens oil supply via Strait of Hormuz",
                    reasoning_tr="İran askeri çatışması Hürmüz Boğazı üzerinden petrol arzını tehdit ediyor"))
                impacts.append(SymbolImpact(symbol="XAUUSD", direction="bullish", score=8, confidence=0.7,
                    reasoning="Geopolitical escalation drives safe haven demand",
                    reasoning_tr="Jeopolitik tırmanma güvenli liman talebini artırıyor"))
                impacts.append(SymbolImpact(symbol="VIX", direction="bullish", score=7, confidence=0.65,
                    reasoning="Military conflict increases market uncertainty",
                    reasoning_tr="Askeri çatışma piyasa belirsizliğini artırıyor"))
            elif any(word in text for word in ["crypto", "outflow", "capital flight"]):
                impacts.append(SymbolImpact(symbol="VIX", direction="bullish", score=6, confidence=0.6,
                    reasoning="Capital flight signals instability in region",
                    reasoning_tr="Sermaye kaçışı bölgede istikrarsızlığa işaret ediyor"))
                impacts.append(SymbolImpact(symbol="DXY", direction="bullish", score=5, confidence=0.55,
                    reasoning="Safe haven flows may benefit USD",
                    reasoning_tr="Güvenli liman akışları USD'yi destekleyebilir"))
        
        # === GEOPOLITICAL: General conflict ===
        elif any(word in text for word in ["war", "conflict", "military", "invasion", "missile", "airstrike"]):
            if any(word in text for word in ["middle east", "israel", "gaza", "palestine", "hamas", "hezbollah"]):
                impacts.append(SymbolImpact(symbol="XAUUSD", direction="bullish", score=8, confidence=0.7,
                    reasoning="Middle East conflict drives safe haven demand",
                    reasoning_tr="Orta Doğu çatışması güvenli liman talebini artırıyor"))
                impacts.append(SymbolImpact(symbol="USOIL", direction="bullish", score=7, confidence=0.65,
                    reasoning="Regional instability raises oil supply concerns",
                    reasoning_tr="Bölgesel istikrarsızlık petrol arzı endişelerini artırıyor"))
            elif any(word in text for word in ["russia", "ukraine", "nato"]):
                impacts.append(SymbolImpact(symbol="XAUUSD", direction="bullish", score=7, confidence=0.65,
                    reasoning="Russia-Ukraine tension increases safe haven demand",
                    reasoning_tr="Rusya-Ukrayna gerginliği güvenli liman talebini artırıyor"))
                impacts.append(SymbolImpact(symbol="USOIL", direction="bullish", score=6, confidence=0.6,
                    reasoning="Eastern European conflict may affect energy supply",
                    reasoning_tr="Doğu Avrupa çatışması enerji arzını etkileyebilir"))
            else:
                impacts.append(SymbolImpact(symbol="VIX", direction="bullish", score=6, confidence=0.6,
                    reasoning="Military conflict creates uncertainty",
                    reasoning_tr="Askeri çatışma belirsizlik yaratıyor"))
        
        # === SANCTIONS / TRADE WAR ===
        elif any(word in text for word in ["sanction", "tariff", "trade war", "embargo", "ban"]):
            impacts.append(SymbolImpact(symbol="VIX", direction="bullish", score=6, confidence=0.6,
                reasoning="Trade tensions increase market volatility",
                reasoning_tr="Ticaret gerginlikleri piyasa volatilitesini artırıyor"))
            if any(word in text for word in ["china", "chinese"]):
                impacts.append(SymbolImpact(symbol="NDX", direction="bearish", score=7, confidence=0.65,
                    reasoning="US-China trade tensions hurt tech supply chains",
                    reasoning_tr="ABD-Çin ticaret gerginlikleri teknoloji tedarik zincirlerini olumsuz etkiliyor"))
        
        # === DEFENSE / MILITARY STOCKS ===
        elif any(word in text for word in ["defense stock", "defense sector", "aerospace", "hanwha", "lockheed", "raytheon", "northrop"]):
            impacts.append(SymbolImpact(symbol="NDX", direction="neutral", score=4, confidence=0.5,
                reasoning="Defense sector movement, limited broad market impact",
                reasoning_tr="Savunma sektörü hareketi, geniş piyasa etkisi sınırlı"))
            impacts.append(SymbolImpact(symbol="VIX", direction="bullish", score=4, confidence=0.5,
                reasoning="Defense sector rally often signals geopolitical tension",
                reasoning_tr="Savunma sektörü rallisi genellikle jeopolitik gerginliğe işaret eder"))
        
        # === OIL-SPECIFIC ===
        elif any(word in text for word in ["oil", "crude", "opec", "petroleum", "barrel"]):
            impacts.append(SymbolImpact(
                symbol="USOIL",
                direction="bullish" if any(w in text for w in ["cut", "shortage", "rise", "surge"]) else "bearish" if any(w in text for w in ["glut", "fall", "drop", "crash"]) else "neutral",
                score=8, confidence=0.7,
                reasoning="Direct oil market news",
                reasoning_tr="Doğrudan petrol piyasası haberi"))
        
        # === GOLD-SPECIFIC ===
        elif any(word in text for word in ["gold", "xau", "bullion", "precious metal"]):
            impacts.append(SymbolImpact(
                symbol="XAUUSD",
                direction="bullish" if any(w in text for w in ["safe haven", "rise", "surge", "rally"]) else "bearish" if any(w in text for w in ["fall", "drop", "sell"]) else "neutral",
                score=8, confidence=0.7,
                reasoning="Direct gold market news",
                reasoning_tr="Doğrudan altın piyasası haberi"))
        
        # === TECH-SPECIFIC ===
        elif any(word in text for word in ["nasdaq", "tech", "apple", "microsoft", "google", "amazon", "nvidia", "tesla"]):
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="bullish" if any(w in text for w in ["beat", "strong", "growth", "rally"]) else "bearish" if any(w in text for w in ["miss", "weak", "fall", "drop", "concern"]) else "neutral",
                score=7, confidence=0.6,
                reasoning="Tech sector related news",
                reasoning_tr="Teknoloji sektörü ile ilgili haber"))
        
        # === FED / MONETARY POLICY ===
        elif any(word in text for word in ["fed", "federal reserve", "rate", "powell", "interest"]):
            impacts.append(SymbolImpact(
                symbol="DXY",
                direction="bullish" if any(w in text for w in ["hike", "raise", "strong", "hawkish"]) else "bearish" if any(w in text for w in ["cut", "lower", "dovish"]) else "neutral",
                score=8, confidence=0.7,
                reasoning="Federal Reserve policy news affects USD",
                reasoning_tr="Fed politikası USD'yi etkiler"))
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="bearish" if any(w in text for w in ["hike", "raise", "hawkish"]) else "bullish" if any(w in text for w in ["cut", "lower", "dovish"]) else "neutral",
                score=7, confidence=0.6,
                reasoning="Interest rates affect tech stocks",
                reasoning_tr="Faiz oranları teknoloji hisselerini etkiler"))
        
        # === CRYPTO-SPECIFIC ===
        elif any(word in text for word in ["crypto", "bitcoin", "ethereum", "blockchain"]):
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="neutral", score=3, confidence=0.4,
                reasoning="Crypto news has limited direct impact on traditional markets",
                reasoning_tr="Kripto haberlerin geleneksel piyasalara doğrudan etkisi sınırlı"))
        
        if not impacts:
            logger.info("[RealAnalyzer] Fallback analysis found no direct effect on tracked instruments")

        max_score = max((impact.score for impact in impacts), default=0)
        fallback_confidence = 50 if impacts else 35
        fallback_importance_score = int(min(100, max_score * 10 * 0.7 + fallback_confidence * 0.3))
        fallback_importance_level = self._normalize_importance_level(None, fallback_importance_score)
        
        impact_summary_en = "; ".join(
            f"{imp.symbol}: {imp.reasoning}"
            for imp in impacts[:3]
            if imp.reasoning
        )
        summary_en = headline.strip() or "Market news update"
        # Fallback path: prefer empty Turkish over fake _simple_translate output.
        # The frontend will gracefully fall back to English when TR fields are empty.
        headline_tr = ""
        summary_tr = ""
        analysis_seed = content[:240].strip() if content else summary_en
        analysis_en = analysis_seed
        if impact_summary_en:
            analysis_en = f"{analysis_seed} Market impact: {impact_summary_en}".strip()
        elif not analysis_en:
            analysis_en = "No direct effect detected on tracked instruments from this headline."
        analysis_tr = ""
        content_tr = ""
        adjusted_impacts, adjusted_sentiment = enforce_news_analysis_consistency(
            headline=headline,
            content=content,
            summary_en=summary_en,
            analysis_en=analysis_en,
            summary_tr=summary_tr,
            analysis_tr=analysis_tr,
            impacts=[
                {
                    "symbol": impact.symbol,
                    "direction": impact.direction,
                    "score": impact.score,
                    "confidence": impact.confidence,
                    "reasoning": impact.reasoning,
                    "reasoning_tr": impact.reasoning_tr,
                }
                for impact in impacts
            ],
            sentiment="neutral",
        )
        impacts = [
            SymbolImpact(
                symbol=str(impact.get("symbol") or ""),
                direction=str(impact.get("direction") or "neutral"),
                score=_safe_int(impact.get("score"), 0),
                confidence=_safe_float(impact.get("confidence"), 0.0),
                reasoning=str(impact.get("reasoning") or ""),
                reasoning_tr=str(impact.get("reasoning_tr") or ""),
            )
            for impact in adjusted_impacts
        ]
        
        return NewsAnalysisResult(
            impacts=impacts,
            sentiment=adjusted_sentiment,
            volatility_expectation="medium",
            urgency="medium" if impacts else "low",
            confidence=fallback_confidence,
            summary_en=summary_en,
            summary_tr=summary_tr,
            analysis_en=analysis_en,
            analysis_tr=analysis_tr,
            headline_tr=headline_tr,
            content_tr=content_tr,
            importance_level=fallback_importance_level,
            importance_score=fallback_importance_score,
            importance_reason="Fallback rule-based classification (DeepSeek unavailable or parse failed).",
            ai_model="fallback",
        )
    
    def _simple_translate(self, text: str) -> str:
        """Basit çeviri - DeepSeek olmadığında kullanılır"""
        if not text:
            return ""
        
        # Basit kelime çevirileri
        translations = {
            "goldman sachs": "Goldman Sachs",
            "oil price": "petrol fiyatı",
            "impact": "etki",
            "asian earnings": "Asya kazançları",
            "says": "diyor ki",
            "could": "olabilir",
            "due to": "nedeniyle",
            "conflict": "çatışma",
            "corporate": "kurumsal",
            "earnings": "kazançlar",
            "price": "fiyat",
            "rise": "yükseliş",
            "fall": "düşüş",
            "market": "piyasa",
            "stock": "hisse",
            "trade": "ticaret",
            "rate": "oran",
            "fed": "Fed",
            "cut": "indirim",
            "hike": "artış",
        }
        
        result = text.lower()
        for en, tr in translations.items():
            result = result.replace(en, tr)
        
        # Baş harfi büyük yap
        return result.capitalize()


# Singleton
_analyzer_v2: Optional[RealNewsAnalyzer] = None

def get_real_analyzer() -> RealNewsAnalyzer:
    global _analyzer_v2
    if _analyzer_v2 is None:
        _analyzer_v2 = RealNewsAnalyzer()
    return _analyzer_v2
