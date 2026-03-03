"""
GERÇEK News Analyzer V2
Her haberi gerçekten analiz eden, içeriğe göre dinamik sonuç üreten sistem
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

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
    headline_tr: str = ""
    content_tr: str = ""


class RealNewsAnalyzer:
    """
    GERÇEK haber analizi - Her haberi özgün olarak değerlendirir
    """
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        
    async def analyze(self, headline: str, content: str = "", source: str = "") -> NewsAnalysisResult:
        """
        Haberi gerçekten analiz et - Rule-based değil, AI-based
        """
        if not self.api_key:
            # API key yoksa fallback
            return self._fallback_analysis(headline, content)
        
        try:
            # DeepSeek AI'a gönder - HER haberi gerçekten analiz et
            prompt = self._build_prompt(headline, content, source)
            
            result = await self._call_deepseek(prompt)
            
            return result
            
        except Exception as e:
            print(f"[RealAnalyzer] AI failed: {e}")
            return self._fallback_analysis(headline, content)
    
    def _build_prompt(self, headline: str, content: str, source: str) -> str:
        """
        DeepSeek için prompt oluştur - Her haber için özel
        """
        return f"""Analyze this financial news article and determine its ACTUAL market impact.

NEWS HEADLINE: {headline}
NEWS CONTENT: {content[:800] if content else "No additional content"}
SOURCE: {source}
DATE: {datetime.utcnow().isoformat()}

INSTRUCTIONS:
1. Read the headline and content carefully
2. Identify the MAIN subject (which company, sector, country, or asset)
3. Determine if this is POSITIVE, NEGATIVE, or NEUTRAL news
4. Decide which financial instruments are ACTUALLY affected (not generic list)
5. Provide SPECIFIC reasoning for each affected instrument

EXAMPLES OF CORRECT ANALYSIS:

Example 1:
Headline: "Apple reports record iPhone sales, beats earnings estimates"
→ Affects: NASDAQ (bullish, 8/10) - Apple is major NASDAQ component
→ Affects: DXY (neutral) - Not directly related to USD
→ Affects: XAUUSD (neutral) - No relation to gold

Example 2:
Headline: "Saudi Arabia cuts oil production by 1 million barrels"
→ Affects: USOIL (bullish, 9/10) - Direct supply reduction
→ Affects: XAUUSD (neutral/slight bullish, 4/10) - Inflation hedge
→ Affects: NASDAQ (bearish, 6/10) - Higher oil = higher costs

Example 3:
Headline: "Fed Chair Powell signals rate cuts coming soon"
→ Affects: DXY (bearish, 8/10) - Lower rates weaken dollar
→ Affects: XAUUSD (bullish, 8/10) - Lower rates help gold
→ Affects: NASDAQ (bullish, 7/10) - Lower rates help growth stocks

Example 4:
Headline: "Devon Energy merges with Coterra in $50B deal"
→ Affects: USOIL (neutral, 5/10) - Company specific, not market wide
→ Affects: NASDAQ (neutral) - Energy sector specific
→ Affects: XAUUSD (neutral) - No relation to gold

Example 5:
Headline: "Australian pension funds hedge against currency surge"
→ Affects: DXY (neutral) - Australia specific
→ Affects: XAUUSD (neutral) - No direct gold impact
→ Affects: NASDAQ (neutral) - Regional news

RESPONSE FORMAT (STRICT JSON - ALL FIELDS REQUIRED):
{{
    "headline_tr": "Türkçe çeviri - haber başlığı tam olarak çevrilmeli",
    "content_tr": "Türkçe özet - haber içeriğinin kısa özeti Türkçe olmalı",
    "urgency": "breaking|high|medium|low",
    "market_sentiment": "risk_on|risk_off|neutral",
    "volatility_expectation": "high|medium|low",
    "analysis_confidence": 75,
    "affected_instruments": [
        {{
            "symbol": "XAUUSD|NDX|DAX|USOIL|VIX|DXY",
            "direction": "bullish|bearish|neutral",
            "impact_score": 8,
            "confidence": 0.85,
            "reasoning": "English explanation of why this instrument is affected",
            "reasoning_tr": "Türkçe açıklama - neden etkilendiği"
        }}
    ],
    "logic": "Brief explanation of your analysis logic"
}}

IMPORTANT: headline_tr and content_tr MUST be Turkish translations, NOT empty!

IMPORTANT RULES:
- ONLY include instruments ACTUALLY affected by this specific news
- If news is about oil company merger, don't say it affects gold
- If news is about Australian pension funds, don't say it affects US Dollar
- Be PRECISE and SPECIFIC - generic impacts are wrong
- Score 1-3 = minimal impact, 4-6 = moderate, 7-8 = significant, 9-10 = major

Analyze this news NOW:"""

    async def _call_deepseek(self, prompt: str) -> NewsAnalysisResult:
        """DeepSeek AI çağrısı"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are an expert financial analyst. Analyze news precisely and only report ACTUAL impacts, not generic patterns."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Düşük temperature = daha tutarlı, gerçekçi
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }
            
            async with session.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")
                
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)
                
                # Parse impacts
                impacts = []
                for imp in result.get("affected_instruments", []):
                    # Only include if actually affected (score > 3 and not neutral with low confidence)
                    if imp.get("impact_score", 0) >= 4 or imp.get("confidence", 0) >= 0.6:
                        impacts.append(SymbolImpact(
                            symbol=imp["symbol"],
                            direction=imp["direction"],
                            score=imp["impact_score"],
                            confidence=imp["confidence"],
                            reasoning=imp["reasoning"],
                            reasoning_tr=imp.get("reasoning_tr", imp["reasoning"])
                        ))
                
                # If no significant impacts, add neutral
                if not impacts:
                    impacts.append(SymbolImpact(
                        symbol="NDX",
                        direction="neutral",
                        score=3,
                        confidence=0.5,
                        reasoning="News does not have significant market impact",
                        reasoning_tr="Haberin önemli piyasa etkisi yok"
                    ))
                
                return NewsAnalysisResult(
                    impacts=impacts,
                    sentiment=result.get("market_sentiment", "neutral"),
                    volatility_expectation=result.get("volatility_expectation", "medium"),
                    urgency=result.get("urgency", "medium"),
                    confidence=result.get("analysis_confidence", 70),
                    headline_tr=result.get("headline_tr", ""),
                    content_tr=result.get("content_tr", "")
                )
    
    def _fallback_analysis(self, headline: str, content: str) -> NewsAnalysisResult:
        """
        AI çalışmazsa basit keyword analizi - ama yine de spesifik
        """
        text = f"{headline} {content}".lower()
        
        impacts = []
        
        # Gerçekten içerik tabanlı analiz
        if any(word in text for word in ["oil", "crude", "opec", "petroleum", "barrel"]):
            impacts.append(SymbolImpact(
                symbol="USOIL",
                direction="bullish" if any(w in text for w in ["cut", "shortage", "rise", "surge"]) else "bearish" if any(w in text for w in ["glut", "fall", "drop", "crash"]) else "neutral",
                score=8,
                confidence=0.7,
                reasoning="Direct oil market news",
                reasoning_tr="Doğrudan petrol piyasası haberi"
            ))
        
        if any(word in text for word in ["gold", "xau", "bullion", "precious metal"]):
            impacts.append(SymbolImpact(
                symbol="XAUUSD",
                direction="bullish" if any(w in text for w in ["safe haven", "rise", "surge", "rally"]) else "bearish" if any(w in text for w in ["fall", "drop", "sell"]) else "neutral",
                score=8,
                confidence=0.7,
                reasoning="Direct gold market news",
                reasoning_tr="Doğrudan altın piyasası haberi"
            ))
        
        if any(word in text for word in ["nasdaq", "tech", "apple", "microsoft", "google", "amazon", "nvidia", "tesla"]):
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="bullish" if any(w in text for w in ["beat", "strong", "growth", "rally"]) else "bearish" if any(w in text for w in ["miss", "weak", "fall", "drop", "concern"]) else "neutral",
                score=7,
                confidence=0.6,
                reasoning="Tech sector related news",
                reasoning_tr="Teknoloji sektörü ile ilgili haber"
            ))
        
        if any(word in text for word in ["fed", "federal reserve", "rate", "powell", "interest"]):
            impacts.append(SymbolImpact(
                symbol="DXY",
                direction="bullish" if any(w in text for w in ["hike", "raise", "strong", "hawkish"]) else "bearish" if any(w in text for w in ["cut", "lower", "dovish"]) else "neutral",
                score=8,
                confidence=0.7,
                reasoning="Federal Reserve policy news affects USD",
                reasoning_tr="Fed politikası USD'yi etkiler"
            ))
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="bearish" if any(w in text for w in ["hike", "raise", "hawkish"]) else "bullish" if any(w in text for w in ["cut", "lower", "dovish"]) else "neutral",
                score=7,
                confidence=0.6,
                reasoning="Interest rates affect tech stocks",
                reasoning_tr="Faiz oranları teknoloji hisselerini etkiler"
            ))
        
        if not impacts:
            # Hiçbir eşleşme yoksa nötr
            impacts.append(SymbolImpact(
                symbol="NDX",
                direction="neutral",
                score=3,
                confidence=0.4,
                reasoning="No significant market impact detected",
                reasoning_tr="Önemli piyasa etkisi tespit edilmedi"
            ))
        
        return NewsAnalysisResult(
            impacts=impacts,
            sentiment="neutral",
            volatility_expectation="medium",
            urgency="medium",
            confidence=50,
            headline_tr="",
            content_tr=""
        )


# Singleton
_analyzer_v2: Optional[RealNewsAnalyzer] = None

def get_real_analyzer() -> RealNewsAnalyzer:
    global _analyzer_v2
    if _analyzer_v2 is None:
        _analyzer_v2 = RealNewsAnalyzer()
    return _analyzer_v2
