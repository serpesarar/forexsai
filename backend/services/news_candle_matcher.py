"""
INTELLIGENT NEWS-CANDLE MATCHING SERVICE
Büyük mum hareketlerini gerçekten açıklayan haberleri tespit eder

Algoritma:
1. Mum hareketinin büyüklüğünü ve volatilitesini analiz et
2. Mum zaman aralığına denk düşen haberleri getir
3. Haberlerin impact score'unu ve urgency'sini değerlendir
4. Heuristic adayları DeepSeek ile yeniden sırala
5. Sadece anlamlı eşleşmeleri döndür (max 5 haber)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import statistics

from database.supabase_client import get_supabase_client
from services.deepseek_json_client import call_deepseek_json


logger = logging.getLogger(__name__)

GLOBAL_IMPACT_SYMBOLS = {"*", "ALL"}

SYMBOL_FAMILIES = {
    "NDX": {"NDX", "NDX.INDX", "NASDAQ", "QQQ"},
    "DAX": {"DAX", "GDAXI", "GDAXI.INDX", "DE40"},
    "XAUUSD": {"XAUUSD", "XAU", "GOLD", "GC"},
    "USOIL": {"USOIL", "USOIL.FOREX", "WTI", "CL", "OIL", "CL.COMM"},
    "VIX": {"VIX", "VIX.INDX"},
    "DXY": {"DXY", "DXY.INDX", "DOLLAR", "USD"},
}

SYMBOL_CANONICAL_MAP = {
    alias: canonical
    for canonical, aliases in SYMBOL_FAMILIES.items()
    for alias in aliases
}


def normalize_symbol(symbol: Optional[str]) -> str:
    """Normalize symbol aliases into a canonical symbol family."""
    if not symbol:
        return ""

    cleaned = str(symbol).upper().replace("/", "").strip()
    for suffix in (".INDX", ".FOREX", ".COMM"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break

    return SYMBOL_CANONICAL_MAP.get(cleaned, cleaned)


def get_symbol_variants(symbol: Optional[str]) -> List[str]:
    """Return all known aliases for a symbol family."""
    if not symbol:
        return []

    raw = str(symbol).upper().replace("/", "").strip()
    normalized = normalize_symbol(raw)
    variants: Set[str] = {raw, normalized}

    for suffix in (".INDX", ".FOREX", ".COMM"):
        if raw.endswith(suffix):
            variants.add(raw[: -len(suffix)])

    family = SYMBOL_FAMILIES.get(normalized)
    if family:
        variants.update(family)

    return sorted(v for v in variants if v)


def symbols_match(target_symbol: Optional[str], impact_symbol: Optional[str]) -> bool:
    """Check whether an impact symbol belongs to the requested symbol family."""
    if not target_symbol or not impact_symbol:
        return False

    impact_clean = str(impact_symbol).upper().replace("/", "").strip()
    if impact_clean in GLOBAL_IMPACT_SYMBOLS:
        return True

    return normalize_symbol(target_symbol) == normalize_symbol(impact_clean)


def get_matching_impact(
    impacts: Optional[List[Dict[str, Any]]],
    symbol: Optional[str],
    include_global: bool = True,
) -> Optional[Dict[str, Any]]:
    """Find the best impact for a symbol, preferring direct family matches over global impacts."""
    if not impacts or not symbol:
        return None

    direct_matches: List[Dict[str, Any]] = []
    global_match: Optional[Dict[str, Any]] = None

    for impact in impacts:
        impact_symbol = impact.get("symbol", "")
        impact_clean = str(impact_symbol).upper().replace("/", "").strip()

        if impact_clean in GLOBAL_IMPACT_SYMBOLS:
            if include_global and global_match is None:
                global_match = impact
            continue

        if symbols_match(symbol, impact_clean):
            direct_matches.append(impact)

    if direct_matches:
        return max(direct_matches, key=lambda impact: impact.get("score", 0))

    return global_match


def _parse_iso_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


@dataclass
class CandleInfo:
    """Mum verisi"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def change_pct(self) -> float:
        """Yüzdelik değişim"""
        if self.open == 0:
            return 0
        return ((self.close - self.open) / self.open) * 100
    
    @property
    def range_pct(self) -> float:
        """Mum range'i (high-low) yüzdesi"""
        if self.open == 0:
            return 0
        return ((self.high - self.low) / self.open) * 100
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def body_size_pct(self) -> float:
        """Mum gövdesi yüzdesi"""
        if self.open == 0:
            return 0
        return abs(self.close - self.open) / self.open * 100


@dataclass
class MatchedNews:
    """Eşleşen haber"""
    id: str
    headline: str
    headline_tr: str
    timestamp: datetime
    urgency: str
    score: int
    direction: str
    confidence: float
    reasoning_tr: str
    relevance_score: float  # 0-1 arası eşleşme kalitesi
    time_diff_minutes: float
    url: str


class NewsCandleMatcher:
    """Akıllı haber-mum eşleştirme servisi"""
    
    def __init__(self):
        self.supabase = get_supabase_client()

    def _build_candle(self,
                      candle_timestamp: str,
                      candle_open: float,
                      candle_close: float,
                      candle_high: float,
                      candle_low: float) -> CandleInfo:
        return CandleInfo(
            timestamp=_parse_iso_timestamp(candle_timestamp),
            open=candle_open,
            high=candle_high,
            low=candle_low,
            close=candle_close,
            volume=0,
        )

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        timeframe_value = str(timeframe or "1h").strip().lower()
        try:
            value = int(timeframe_value[:-1])
        except (TypeError, ValueError):
            return 60

        unit = timeframe_value[-1:] or "h"
        if unit == "m":
            return max(1, value)
        if unit == "h":
            return max(1, value * 60)
        if unit == "d":
            return max(60, value * 24 * 60)
        return 60

    def _urgency_weight(self, urgency: Optional[str]) -> float:
        return {
            "breaking": 1.0,
            "high": 0.8,
            "medium": 0.45,
            "low": 0.15,
        }.get(str(urgency or "medium").lower(), 0.35)

    def _normalize_confidence(self, value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0

        if numeric <= 1:
            return max(0.0, min(1.0, numeric))
        return max(0.0, min(1.0, numeric / 100.0))

    def _direction_alignment_score(self, expected_direction: Optional[str], candle: CandleInfo) -> float:
        direction = str(expected_direction or "neutral").lower()
        if direction == "bullish" and candle.is_bullish:
            return 1.0
        if direction == "bearish" and candle.is_bearish:
            return 1.0
        if direction in {"neutral", "volatile"}:
            return 0.45
        return 0.05

    def _importance_level(self, score: float) -> str:
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    def _event_time_window_minutes(self, timeframe: str, significance: Dict[str, Any]) -> int:
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        return max(90, min(12 * 60, max(timeframe_minutes * 3, significance.get("time_window_minutes", 120) * 3)))

    def _build_context_candidates(self, symbol: str, candle: CandleInfo, timeframe: str) -> List[Dict[str, Any]]:
        context_window = max(90, self._timeframe_to_minutes(timeframe) * 2)
        news_candidates = self._collect_matches(
            symbol,
            candle,
            self.fetch_relevant_news(
                symbol=symbol,
                candle_time=candle.timestamp,
                time_window_minutes=context_window,
                min_impact_score=3,
                expected_urgency=["breaking", "high", "medium", "low"],
            ),
        )
        event_candidates = self._fetch_calendar_candidates(symbol, candle, timeframe, context_window)
        merged = self._select_top_matches(news_candidates + event_candidates)
        for item in merged:
            item.setdefault("match_quality", "context")
        return merged

    def _build_event_candidate(
        self,
        symbol: str,
        candle: CandleInfo,
        raw_event: Dict[str, Any],
        event_type: str,
        time_window_minutes: int,
    ) -> Optional[Dict[str, Any]]:
        timestamp = raw_event.get("timestamp")
        if not timestamp:
            return None

        try:
            event_time = _parse_iso_timestamp(str(timestamp))
        except Exception:
            return None

        time_diff_minutes = (event_time - candle.timestamp).total_seconds() / 60
        if abs(time_diff_minutes) > time_window_minutes:
            return None

        affected_symbols = [normalize_symbol(item) for item in raw_event.get("affected_symbols", []) if item]
        if affected_symbols and normalize_symbol(symbol) not in affected_symbols and "ALL" not in affected_symbols:
            return None

        importance_score = raw_event.get("importance_score")
        if importance_score is None:
            impact_label = str(raw_event.get("impact") or "Medium").lower()
            importance_score = {"high": 85, "medium": 65, "low": 45}.get(impact_label, 60)

        direction = raw_event.get("predicted_direction") or "volatile"
        confidence = self._normalize_confidence(raw_event.get("confidence") or 65)
        proximity_weight = max(0.0, 1.0 - (abs(time_diff_minutes) / max(30.0, float(time_window_minutes))))
        relevance = min(
            1.0,
            (float(importance_score) / 100.0) * 0.45
            + proximity_weight * 0.3
            + self._direction_alignment_score(direction, candle) * 0.15
            + confidence * 0.1,
        )

        reasoning_en = (
            raw_event.get("impact_analysis")
            or raw_event.get("analysis")
            or raw_event.get("importance_reason")
            or raw_event.get("why_it_matters")
            or raw_event.get("description")
            or raw_event.get("title")
            or raw_event.get("company")
            or ""
        )
        reasoning_tr = (
            raw_event.get("impact_analysis_tr")
            or raw_event.get("analysis_tr")
            or raw_event.get("why_it_matters_tr")
            or raw_event.get("description_tr")
            or raw_event.get("title_tr")
            or reasoning_en
        )
        headline = raw_event.get("title") or raw_event.get("company") or raw_event.get("ticker") or raw_event.get("id")
        headline_tr = raw_event.get("title_tr") or raw_event.get("company_tr") or headline
        urgency = "breaking" if float(importance_score) >= 85 else "high" if float(importance_score) >= 70 else "medium"

        return {
            "id": raw_event.get("id"),
            "timestamp": timestamp,
            "source": "economic_calendar" if event_type == "economic" else "earnings_calendar",
            "headline": headline,
            "headline_tr": headline_tr,
            "summary_en": reasoning_en,
            "summary_tr": reasoning_tr,
            "analysis_en": reasoning_en,
            "analysis_tr": reasoning_tr,
            "url": raw_event.get("url") or "",
            "urgency": urgency,
            "relevance_score": round(relevance, 4),
            "time_diff_minutes": time_diff_minutes,
            "catalyst_type": event_type,
            "match_quality": "matched" if relevance >= 0.45 else "context",
            "importance_score": int(float(importance_score)),
            "importance_level": raw_event.get("importance_level") or self._importance_level(float(importance_score)),
            "event_payload": raw_event,
            "symbol_impact": {
                "symbol": normalize_symbol(symbol),
                "direction": direction,
                "score": max(4, min(10, round(float(importance_score) / 10))),
                "confidence": confidence,
                "reasoning": reasoning_en,
                "reasoning_tr": reasoning_tr,
            },
        }

    def _fetch_calendar_candidates(
        self,
        symbol: str,
        candle: CandleInfo,
        timeframe: str,
        time_window_minutes: int,
    ) -> List[Dict[str, Any]]:
        try:
            from routers.economic_calendar_router import generate_upcoming_earnings, generate_upcoming_events
        except Exception:
            logger.exception("[NewsCandleMatcher] Unable to import calendar generators")
            return []

        candidates: List[Dict[str, Any]] = []
        try:
            for event in generate_upcoming_events(days_ahead=7):
                candidate = self._build_event_candidate(symbol, candle, event, "economic", time_window_minutes)
                if candidate:
                    candidates.append(candidate)

            for event in generate_upcoming_earnings(days_ahead=14):
                candidate = self._build_event_candidate(symbol, candle, event, "earnings", time_window_minutes)
                if candidate:
                    candidates.append(candidate)
        except Exception:
            logger.exception("[NewsCandleMatcher] Error building calendar candidates")
            return []

        candidates.sort(
            key=lambda item: (
                item.get("relevance_score", 0),
                item.get("importance_score", 0),
                -abs(float(item.get("time_diff_minutes", 0))),
            ),
            reverse=True,
        )
        return candidates[:8]

    def _collect_matches(self, symbol: str, candle: CandleInfo, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matched: List[Dict[str, Any]] = []

        for news in news_items:
            relevance = self.calculate_relevance(news, candle, symbol)
            if relevance < 0.3:
                continue

            symbol_impact = get_matching_impact(news.get("impacts", []), symbol)
            if not symbol_impact:
                continue

            news_time = _parse_iso_timestamp(news.get("timestamp", ""))
            time_diff = (news_time - candle.timestamp).total_seconds() / 60

            matched.append(
                {
                    **news,
                    "catalyst_type": "news",
                    "match_quality": "matched",
                    "relevance_score": relevance,
                    "symbol_impact": symbol_impact,
                    "time_diff_minutes": time_diff,
                }
            )

        matched.sort(key=lambda x: x["relevance_score"], reverse=True)
        return matched

    def _select_top_matches(self, matched: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ranked = sorted(
            matched,
            key=lambda item: (
                item.get("relevance_score", 0),
                item.get("importance_score", 0) or ((item.get("symbol_impact") or {}).get("score", 0) * 10),
                self._urgency_weight(item.get("urgency")),
                self._normalize_confidence((item.get("symbol_impact") or {}).get("confidence")),
            ),
            reverse=True,
        )
        return ranked[:5]

    async def _rerank_with_ai(
        self,
        symbol: str,
        candle: CandleInfo,
        timeframe: str,
        significance: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        serialized_candidates = []
        for item in candidates[:5]:
            impact = item.get("symbol_impact") or {}
            serialized_candidates.append(
                {
                    "id": item.get("id"),
                    "catalyst_type": item.get("catalyst_type", "news"),
                    "source": item.get("source"),
                    "headline": item.get("headline_tr") or item.get("headline"),
                    "timestamp": item.get("timestamp"),
                    "urgency": item.get("urgency"),
                    "heuristic_relevance": round(float(item.get("relevance_score", 0)), 4),
                    "time_diff_minutes": round(float(item.get("time_diff_minutes", 0)), 2),
                    "impact_direction": impact.get("direction", "neutral"),
                    "impact_score": impact.get("score", 0),
                    "impact_reasoning_tr": impact.get("reasoning_tr") or impact.get("reasoning") or "",
                }
            )

        prompt = f"""You are matching already AI-analyzed market catalysts to a specific market candle. Return ONLY valid JSON.

JSON schema:
{{
  "confidence": 0-100,
  "matches": [
    {{
      "id": "candidate-id",
      "reasoning_tr": "Bu catalystin bu mumu neden açıkladığını kısa Türkçe açıkla",
      "importance_level": "critical|high|medium|low",
      "importance_score": 0-100
    }}
  ]
}}

Rules:
- Sadece aşağıdaki candidate id'lerini kullan.
- Sıralama en güçlü eşleşmeden en zayıfa doğru olsun.
- Haber ile mum yönü uyumsuzsa reasoning_tr içinde bunu açıkça belirt.
- Haber, ekonomik veri veya earnings olabilir.
- Eğer hiçbir catalyst ikna edici değilse matches boş olsun.

CANDLE:
{{
  "symbol": "{symbol}",
  "timeframe": "{timeframe}",
  "timestamp": "{candle.timestamp.isoformat()}",
  "open": {candle.open},
  "high": {candle.high},
  "low": {candle.low},
  "close": {candle.close},
  "change_pct": {round(candle.change_pct, 4)},
  "range_pct": {round(candle.range_pct, 4)},
  "movement_type": "{significance.get('movement_type', 'unknown')}"
}}

CANDIDATES:
{serialized_candidates}
"""

        ai_payload = await call_deepseek_json(prompt, max_tokens=900, temperature=0.2, timeout_seconds=30)
        ai_matches = (ai_payload or {}).get("matches")
        if not isinstance(ai_matches, list):
            return candidates[:5]

        candidate_map = {str(item.get("id")): dict(item) for item in candidates if item.get("id")}
        ordered: List[Dict[str, Any]] = []
        used_ids: Set[str] = set()
        ai_confidence = (ai_payload or {}).get("confidence")

        for index, ai_match in enumerate(ai_matches):
            if not isinstance(ai_match, dict):
                continue

            news_id = str(ai_match.get("id") or "").strip()
            if not news_id or news_id in used_ids or news_id not in candidate_map:
                continue

            item = dict(candidate_map[news_id])
            rank_bonus = max(0.0, 1.0 - (index * 0.18))
            item["relevance_score"] = round(min(1.0, item.get("relevance_score", 0) * 0.7 + rank_bonus * 0.3), 4)
            item["ai_reasoning_tr"] = str(ai_match.get("reasoning_tr") or "").strip()
            item["importance_level"] = ai_match.get("importance_level")
            item["importance_score"] = ai_match.get("importance_score")
            item["ai_match_confidence"] = ai_confidence
            ordered.append(item)
            used_ids.add(news_id)

        for candidate in candidates:
            candidate_id = str(candidate.get("id") or "")
            if candidate_id and candidate_id not in used_ids:
                ordered.append(candidate)

        return ordered[:5]

    def _prepare_candidates(self, symbol: str, candle: CandleInfo, timeframe: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        atr = candle.range_pct * 0.5
        significance = self.calculate_candle_significance(candle, atr, atr)
        if not significance["is_significant"]:
            return significance, self._build_context_candidates(symbol, candle, timeframe)

        news_items = self.fetch_relevant_news(
            symbol=symbol,
            candle_time=candle.timestamp,
            time_window_minutes=significance["time_window_minutes"],
            min_impact_score=significance["min_impact_score"],
            expected_urgency=significance["expected_news_urgency"],
        )
        news_candidates = self._collect_matches(symbol, candle, news_items) if news_items else []
        event_candidates = self._fetch_calendar_candidates(
            symbol=symbol,
            candle=candle,
            timeframe=timeframe,
            time_window_minutes=self._event_time_window_minutes(timeframe, significance),
        )
        merged = self._select_top_matches(news_candidates + event_candidates)
        if merged:
            return significance, merged

        return significance, self._build_context_candidates(symbol, candle, timeframe)
    
    def calculate_candle_significance(self, candle: CandleInfo, 
                                     avg_range: float, 
                                     atr: float) -> Dict[str, Any]:
        """
        Mumun ne kadar önemli olduğunu hesapla
        
        Returns:
            {
                "is_significant": bool,
                "significance_score": float,  # 0-10 arası
                "movement_type": "major" | "moderate" | "minor",
                "expected_news_urgency": ["breaking", "high"] | ["high", "medium"] | ["medium"],
                "min_impact_score": int
            }
        """
        change_pct = abs(candle.change_pct)
        range_pct = candle.range_pct
        
        # ATR'e göre normalize et
        atr_multiple = range_pct / atr if atr > 0 else 0
        
        # Volatilite skoru (0-10)
        significance_score = min(10, atr_multiple * 2 + change_pct * 2)
        
        # Mum önem derecesi
        if significance_score >= 7 or atr_multiple >= 2.5:
            return {
                "is_significant": True,
                "significance_score": significance_score,
                "movement_type": "major",
                "expected_news_urgency": ["breaking", "high"],
                "min_impact_score": 7,
                "time_window_minutes": 30  # Dar zaman penceresi
            }
        elif significance_score >= 4 or atr_multiple >= 1.5:
            return {
                "is_significant": True,
                "significance_score": significance_score,
                "movement_type": "moderate",
                "expected_news_urgency": ["high", "medium"],
                "min_impact_score": 5,
                "time_window_minutes": 60
            }
        else:
            return {
                "is_significant": False,
                "significance_score": significance_score,
                "movement_type": "minor",
                "expected_news_urgency": ["medium"],
                "min_impact_score": 4,
                "time_window_minutes": 120
            }
    
    def fetch_relevant_news(self, 
                           symbol: str, 
                           candle_time: datetime,
                           time_window_minutes: int,
                           min_impact_score: int,
                           expected_urgency: List[str]) -> List[Dict]:
        """
        Muma yakın zamanda etkili haberleri getir
        """
        start_time = candle_time - timedelta(minutes=time_window_minutes)
        end_time = candle_time + timedelta(minutes=time_window_minutes//2)
        
        try:
            # Önce yüksek urgency haberleri dene
            result = (
                self.supabase.table("enriched_news")
                .select("*")
                .gte("timestamp", start_time.isoformat())
                .lte("timestamp", end_time.isoformat())
                .in_("urgency", expected_urgency)
                .order("timestamp", desc=False)
                .limit(20)
                .execute()
            )
            
            items = result.data if hasattr(result, 'data') else result.get('data', [])
            
            # Eğer yeterli haber yoksa, tüm haberleri dene ama skor filtresi uygula
            if len(items) < 3:
                result_all = (
                    self.supabase.table("enriched_news")
                    .select("*")
                    .gte("timestamp", start_time.isoformat())
                    .lte("timestamp", end_time.isoformat())
                    .order("ai_confidence", desc=True)
                    .limit(10)
                    .execute()
                )
                items_all = result_all.data if hasattr(result_all, 'data') else result_all.get('data', [])
                
                # Skor filtresi uygula
                filtered = []
                for item in items_all:
                    symbol_impact = get_matching_impact(item.get("impacts", []), symbol)
                    if symbol_impact and symbol_impact.get("score", 0) >= min_impact_score:
                        filtered.append(item)
                
                items = filtered
            
            return items or []
            
        except Exception as e:
            logger.exception("[NewsCandleMatcher] Error fetching news")
            return []
    
    def calculate_relevance(self, 
                           news: Dict,
                           candle: CandleInfo,
                           symbol: str) -> float:
        """
        Haberin mumla ne kadar alakalı olduğunu hesapla (0-1 arası)
        
        Faktörler:
        - Zaman yakınlığı (haber mumdan önce mi sonra mı)
        - Yön uyumu (haber bullish, mum bullish mi)
        - Impact score
        - Urgency seviyesi
        - Confidence
        """
        symbol_impact = get_matching_impact(news.get("impacts", []), symbol)
        
        if not symbol_impact:
            return 0
        
        relevance = 0.0
        
        # 1. Impact score ağırlığı (0-0.3)
        impact_score = symbol_impact.get("score", 5)
        relevance += (impact_score / 10) * 0.3
        
        # 2. Urgency ağırlığı (0-0.25)
        urgency = news.get("urgency", "medium")
        relevance += self._urgency_weight(urgency) * 0.25
        
        # 3. Yön uyumu (0-0.25)
        news_direction = symbol_impact.get("direction", "neutral")
        if news_direction == "bullish" and candle.is_bullish:
            relevance += 0.25
        elif news_direction == "bearish" and candle.is_bearish:
            relevance += 0.25
        elif news_direction == "neutral":
            relevance += 0.1
        
        # 4. AI confidence (0-0.1)
        ai_confidence = self._normalize_confidence(news.get("ai_confidence", 50))
        relevance += ai_confidence * 0.1
        
        # 5. Zaman faktörü (0-0.1)
        # Haber mumdan hemen önceyse daha iyi
        news_time = _parse_iso_timestamp(news.get("timestamp", ""))
        time_diff = abs((news_time - candle.timestamp).total_seconds() / 60)
        if time_diff < 15:
            relevance += 0.1
        elif time_diff < 30:
            relevance += 0.05
        
        return min(1.0, relevance)
    
    def match_news_to_candle(self,
                            symbol: str,
                            candle: CandleInfo,
                            historical_candles: List[CandleInfo]) -> List[MatchedNews]:
        """
        Ana eşleştirme fonksiyonu
        
        Returns:
            Önem sırasına göre sıralanmış en fazla 5 haber
        """
        # ATR hesapla (son 20 mum)
        if len(historical_candles) >= 20:
            recent_ranges = [c.range_pct for c in historical_candles[-20:]]
            atr = statistics.mean(recent_ranges)
            avg_range = atr
        else:
            atr = 0.5  # Default
            avg_range = 0.5
        
        # Mum önemini analiz et
        significance = self.calculate_candle_significance(candle, avg_range, atr)
        
        logger.info(
            "[NewsCandleMatcher] Candle significance=%s score=%.1f urgency=%s",
            significance["movement_type"],
            significance["significance_score"],
            significance["expected_news_urgency"],
        )
        
        # Önemsiz mumlar için az haber döndür
        if not significance["is_significant"]:
            logger.info("[NewsCandleMatcher] Insignificant candle, returning empty")
            return []
        
        # Haberleri getir
        news_items = self.fetch_relevant_news(
            symbol=symbol,
            candle_time=candle.timestamp,
            time_window_minutes=significance["time_window_minutes"],
            min_impact_score=significance["min_impact_score"],
            expected_urgency=significance["expected_news_urgency"]
        )
        
        if not news_items:
            logger.info("[NewsCandleMatcher] No news found for this candle")
            return []
        
        # Her haber için relevance hesapla
        matched = []
        for news in news_items:
            relevance = self.calculate_relevance(news, candle, symbol)
            
            # Minimum relevance threshold
            if relevance < 0.3:
                continue
            
            symbol_impact = get_matching_impact(news.get("impacts", []), symbol)
            
            if not symbol_impact:
                continue
            
            news_time = _parse_iso_timestamp(news.get("timestamp", ""))
            time_diff = (news_time - candle.timestamp).total_seconds() / 60
            
            matched.append(MatchedNews(
                id=news.get("id", ""),
                headline=news.get("headline", ""),
                headline_tr=news.get("headline_tr", news.get("headline", "")),
                timestamp=news_time,
                urgency=news.get("urgency", "medium"),
                score=symbol_impact.get("score", 5),
                direction=symbol_impact.get("direction", "neutral"),
                confidence=symbol_impact.get("confidence", 0.5),
                reasoning_tr=symbol_impact.get("reasoning_tr", ""),
                relevance_score=relevance,
                time_diff_minutes=time_diff,
                url=news.get("url", "")
            ))
        
        # Relevance'a göre sırala ve en iyi 5'i al
        matched.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Eğer çok fazla "medium" varsa ve "high" azsa, filtrele
        high_news = [n for n in matched if n.urgency in ["breaking", "high"]]
        
        if len(high_news) >= 2:
            # Sadece high urgency haberleri göster
            result = high_news[:5]
        else:
            # High + en iyi medium haberleri
            result = matched[:5]
        
        logger.info(
            "[NewsCandleMatcher] Found %s relevant news items (filtered from %s matches)",
            len(result),
            len(matched),
        )
        
        return result

    async def match_news_to_candle_simple_ai(self,
                                             symbol: str,
                                             candle_timestamp: str,
                                             candle_open: float,
                                             candle_close: float,
                                             candle_high: float,
                                             candle_low: float,
                                             timeframe: str = "1h") -> List[Dict[str, Any]]:
        try:
            candle = self._build_candle(
                candle_timestamp=candle_timestamp,
                candle_open=candle_open,
                candle_close=candle_close,
                candle_high=candle_high,
                candle_low=candle_low,
            )
            significance, candidates = self._prepare_candidates(symbol, candle, timeframe)
            if not candidates:
                return []
            if not significance["is_significant"]:
                return candidates[:5]
            return await self._rerank_with_ai(symbol, candle, timeframe, significance, candidates)
        except Exception:
            logger.exception("[NewsCandleMatcher] Error in AI-assisted simple match")
            return self.match_news_to_candle_simple(
                symbol=symbol,
                candle_timestamp=candle_timestamp,
                candle_open=candle_open,
                candle_close=candle_close,
                candle_high=candle_high,
                candle_low=candle_low,
            )
    
    def match_news_to_candle_simple(self,
                                   symbol: str,
                                   candle_timestamp: str,
                                   candle_open: float,
                                   candle_close: float,
                                   candle_high: float,
                                   candle_low: float) -> List[Dict]:
        """
        Basit API versiyonu - direkt değerlerle çalışır
        """
        try:
            candle = self._build_candle(
                candle_timestamp=candle_timestamp,
                candle_open=candle_open,
                candle_close=candle_close,
                candle_high=candle_high,
                candle_low=candle_low,
            )
            significance, candidates = self._prepare_candidates(symbol, candle, "1h")
            if not candidates:
                return []
            return candidates
        except Exception:
            logger.exception("[NewsCandleMatcher] Error in simple match")
            return []


# Singleton instance
_matcher: Optional[NewsCandleMatcher] = None


def get_news_candle_matcher() -> NewsCandleMatcher:
    """Get or create matcher singleton"""
    global _matcher
    if _matcher is None:
        _matcher = NewsCandleMatcher()
    return _matcher
