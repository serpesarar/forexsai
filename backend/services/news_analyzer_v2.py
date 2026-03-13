"""
GERÇEK News Analyzer V2
Her haberi gerçekten analiz eden, içeriğe göre dinamik sonuç üreten sistem
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp

DEEPSEEK_API_KEY = os.getenv("DEEP_SEEKR1", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

logger = logging.getLogger(__name__)

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
DATE: {datetime.utcnow().isoformat()}
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
        content = ""
        
        logger.info(f"[DeepSeek] Calling API with key present: {bool(self.api_key)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "deepseek-reasoner",
                    "messages": [
                        {"role": "user", "content": "You are an expert financial analyst. Analyze news precisely and only report ACTUAL impacts, not generic patterns. Respond ONLY with valid JSON.\n\n" + prompt}
                    ],
                    "max_tokens": 800
                }
                
                logger.info(f"[DeepSeek] Sending request to {DEEPSEEK_API_URL}")
                
                async with session.post(
                    DEEPSEEK_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    logger.info(f"[DeepSeek] Response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[DeepSeek] API error {response.status}: {error_text}")
                        raise Exception(f"API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    logger.info(f"[DeepSeek] Raw response preview: {content[:200]}...")
                    
                    # Clean up response - sometimes DeepSeek adds markdown
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    # Try to fix incomplete JSON (truncated responses)
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError as json_err:
                        # Try to fix common truncation issues
                        if "Unterminated string" in str(json_err):
                            logger.warning(f"[DeepSeek] Incomplete JSON, attempting to fix...")
                            # Add closing braces/brackets
                            open_braces = content.count('{') - content.count('}')
                            open_brackets = content.count('[') - content.count(']')
                            fixed_content = content
                            for _ in range(open_brackets):
                                fixed_content += "]"
                            for _ in range(open_braces):
                                fixed_content += "}"
                            # Remove trailing commas before closing braces
                            fixed_content = fixed_content.replace(',}', '}').replace(',]', ']')
                            try:
                                result = json.loads(fixed_content)
                                logger.info("[DeepSeek] JSON fixed successfully!")
                            except:
                                raise json_err
                        else:
                            raise
                    
                    summary_en = self._coerce_text(result.get("summary_en"), headline)
                    headline_tr = self._coerce_text(
                        result.get("headline_tr"),
                        self._coerce_text(result.get("summary_tr"), self._simple_translate(headline or summary_en))
                    )
                    summary_tr = self._coerce_text(result.get("summary_tr"), headline_tr)
                    analysis_en = self._coerce_text(
                        result.get("analysis_en"),
                        self._coerce_text(result.get("logic"), article_content[:280] if article_content else headline)
                    )
                    analysis_tr = self._coerce_text(
                        result.get("analysis_tr"),
                        self._coerce_text(result.get("content_tr"), self._simple_translate(analysis_en))
                    )
                    content_tr = self._coerce_text(result.get("content_tr"), analysis_tr)

                    logger.info(f"[DeepSeek] Parsed result: headline_tr={headline_tr[:50]}...")
                    
                    # Parse impacts
                    raw_impacts = result.get("affected_instruments", [])
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
                                reasoning_tr=imp.get("reasoning_tr", imp.get("reasoning", ""))
                            ))
                    
                    if not impacts:
                        logger.info("[DeepSeek] No tracked instruments were materially affected by this news item")

                    raw_conf = result.get("analysis_confidence", 50)
                    try:
                        confidence = float(raw_conf)
                    except (TypeError, ValueError):
                        confidence = 50.0
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
                        sentiment=result.get("market_sentiment", "neutral"),
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
                    
        except json.JSONDecodeError as e:
            import traceback
            logger.error(f"[DeepSeek] JSON parse error: {e}")
            logger.error(f"[DeepSeek] Failed content: {content[:500] if 'content' in locals() else 'N/A'}")
            logger.error(f"[DeepSeek] Traceback: {traceback.format_exc()}")
            raise
        except Exception as e:
            import traceback
            logger.error(f"[DeepSeek] Exception during API call: {type(e).__name__}: {e}")
            logger.error(f"[DeepSeek] Full traceback: {traceback.format_exc()}")
            raise
    
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
        headline_tr = self._simple_translate(headline)
        summary_tr = headline_tr
        analysis_seed = content[:240].strip() if content else summary_en
        analysis_en = analysis_seed
        if impact_summary_en:
            analysis_en = f"{analysis_seed} Market impact: {impact_summary_en}".strip()
        elif not analysis_en:
            analysis_en = "No direct effect detected on tracked instruments from this headline."
        analysis_tr = self._simple_translate(analysis_en)
        content_tr = analysis_tr
        
        return NewsAnalysisResult(
            impacts=impacts,
            sentiment="neutral",
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
