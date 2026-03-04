"""
RSS News Aggregator Service
Fetches financial news from multiple RSS sources with intelligent filtering
Optimized for cost: Redis cache + Smart filtering + 7min intervals
"""

import asyncio
import hashlib
import html
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
import aiohttp
import feedparser
from difflib import SequenceMatcher

from services.news_analyzer_v2 import get_real_analyzer
from database.supabase_client import get_supabase_client
from services.redis_client import cache_get, cache_set

# IMPORTANT SYMBOLS - Only analyze news affecting these
IMPORTANT_SYMBOLS = {"XAUUSD", "NDX", "DAX", "USOIL", "VIX", "DXY", "GOLD", "NASDAQ", "OIL"}

# News filtering keywords (for pre-filter before AI)
MARKET_KEYWORDS = {
    # Metals
    "gold", "xau", "silver", "metal", "precious",
    # Indices
    "nasdaq", "dax", "index", "indices", "stock", "hisse", "sp500", "s&p", "dow", "jones",
    # Forex
    "dollar", "eur", "usd", "fed", "rate", "interest", "faiz", "euro", "gbp", "pound", "yen", 
    "jpy", "sterling", "exchange rate", "doviz", "kurlar", "turkish lira", "lira", "tl",
    # Oil
    "oil", "petrol", "crude", "opec", "barrel", "wti", "brent", "gas", "natural gas", "energy",
    # Volatility
    "vix", "volatility", "fear index", "volatilite",
    
    # === CRITICAL EVENTS - Always analyze ===
    # War & Conflict (always affects all markets)
    "war", "savaş", "saldırı", "attack", "strike", "missile", "füze", "bomb", "bombing", "patlama",
    "explosion", "killed", "ölü", "dead", "casualties", " Yaralı", "injured", "conflict", "çatışma",
    "invasion", "işgal", "military", "askeri", "troop", "operation", "refugee", "mülteci",
    "iran", "israel", "gaza", "ukraine", "ukrayna", "russia", "rusya", "china", "çin", "taiwan",
    "tayvan", "middle east", "orta doğu", "tensions", "gerginlik", "escalation", "tırmanma",
    
    # Central Banks & Interest Rates (critical for all markets)
    "fed", "fomc", "interest rate", "faiz", "rate hike", "rate cut", "faiz artışı", "faiz indirimi",
    "powell", "ecb", "european central bank", "avm", "boe", "bank of england", "boj", 
    "merkez bankası", "central bank", "monetary policy", "para politikası", "hawkish", "dovish",
    
    # Economic Data (critical)
    "inflation", "enflasyon", "cpi", "ppi", "gdp", "growth", "büyüme", "recession", "resesyon",
    "nfp", "non-farm", "işsizlik", "unemployment", "jobless", "claims", "retail sales", 
    "consumer", "producer", "manufacturing", "pmi", "industrial production", "trade balance",
    "budget", "deficit", "borç", "debt", "credit rating", "kredi notu", "downgrade",
    
    # Earnings (always affects NDX/DAX)
    "earnings", "kazanç", "revenue", "gelir", "profit", "kâr", "loss", "zarar", "eps", "beat",
    "miss", "forecast", "guidance", "tahmin", "outlook", "guidance", "forecast", "apple", 
    "microsoft", "amazon", "google", "tesla", "nvidia", "meta", "berkshire", "jpmorgan",
    "earnings call", "conference call", "quarterly", "çeyrek", "q1", "q2", "q3", "q4",
    
    # Political Events (major impact)
    "trump", "biden", "election", "seçim", "vote", "oy", "bipartisan", "congress", "senate",
    "house", "white house", "beyaz saray", "government", "hükümet", "shutdown", "debt ceiling",
    "tariff", "gümrük vergisi", "sanctions", "yaptırım", "trade war", "ticaret savaşı",
    
    # Crisis Events
    "crisis", "kriz", "default", "bankruptcy", "iflas", "bailout", "kurtarma", "emergency",
    "acil durum", "black swan", "pandemic", "pandemi", "lockdown", "kapanma", "supply chain",
    "tedarik zinciri", "shortage", "kıtlık", "blackout", "kesinti",
    
    # General market terms
    "market", "piyasa", "trade", "trading", "yatırım", "invest", "rally", "selloff", "dump",
    "crash", "çöküş", "correction", "düzeltme", "bull", "bear", "boğa", "ayı", "rally", 
    "ralli", "surge", "yükseliş", "plunge", "düşüş", "tumble", "soar", "jump", "slide",
    "volatility", "volatilite", "liquidity", "likidite"
}

# RSS Feed Sources
RSS_SOURCES = {
    # Priority 1 - High frequency financial
    "forexlive": {
        "url": "https://www.forexlive.com/feed/news",
        "priority": 1,
        "category": "forex",
        "fetch_interval": 120,  # 2 minutes
    },
    "zerohedge": {
        "url": "https://feeds.zerohedge.com/zerohedge",
        "priority": 1,
        "category": "markets",
        "fetch_interval": 120,
    },
    "reuters_markets": {
        "url": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
        "priority": 1,
        "category": "markets",
        "fetch_interval": 120,
    },
    "investing": {
        "url": "https://www.investing.com/rss/news.rss",
        "priority": 1,
        "category": "markets",
        "fetch_interval": 120,
    },
    
    # Priority 2 - General business news
    "bbc_business": {
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "priority": 2,
        "category": "business",
        "fetch_interval": 300,  # 5 minutes
    },
    "marketwatch": {
        "url": "https://feeds.marketwatch.com/marketwatch/realtimeheadlines",
        "priority": 2,
        "category": "markets",
        "fetch_interval": 300,
    },
    "cnbc": {
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "priority": 2,
        "category": "markets",
        "fetch_interval": 300,
    },
    "bloomberg": {
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "priority": 2,
        "category": "markets",
        "fetch_interval": 300,
    },
    
    
    # Priority 3 - Commodities (directly affects XAUUSD and USOIL)
    "kitco_gold": {
        "url": "https://www.kitco.com/rss/gold-news.xml",
        "priority": 3,
        "category": "commodities",
        "fetch_interval": 600,  # 10 minutes
    },
    "oilprice": {
        "url": "https://oilprice.com/rss/main",
        "priority": 3,
        "category": "commodities",
        "fetch_interval": 600,
    },
}

# ENHANCED KEYWORD FILTERING - Expanded for broader coverage
HIGH_PRIORITY_KEYWORDS = [
    # Central Banks & Monetary Policy
    "fed", "federal reserve", "powell", "fomc", "rate decision", "rate cut", "rate hike",
    "interest rate", "monetary policy", "taper", "qe", "quantitative easing",
    "ecb", "european central bank", "lagarde", "bank of england", "boe", "bailey",
    "boj", "bank of japan", "people's bank of china", "pboc", "pbo c",
    "central bank", "benchmark rate", "policy rate", "discount rate",
    
    # Economic Indicators
    "nfp", "non-farm payrolls", "nonfarm payrolls", "jobs report", "employment",
    "unemployment", "cpi", "inflation", "ppi", "producer price", "consumer price",
    "gdp", "gross domestic product", "retail sales", "industrial production",
    "manufacturing", "services pmi", "pmi", "durable goods", "trade balance",
    "current account", "housing starts", "building permits", "consumer confidence",
    "sentiment", "business sentiment", "economic growth", "recession", "recovery",
    
    # Geopolitical & Safe Haven
    "trump", "biden", "election", "white house", "congress", "senate",
    "iran", "israel", "gaza", "palestine", "middle east", "conflict", "war",
    "tension", "escalation", "military", "strike", "attack", "ceasefire",
    "russia", "ukraine", "putin", "nato", "china", "taiwan", "north korea",
    "sanctions", "embargo", "trade war", "tariff", "diplomatic", "crisis",
    "terrorist", "terrorism", "security threat", "political instability",
    
    # Market Events
    "earnings", "revenue", "profit", "loss", "guidance", "outlook", "forecast",
    "ipo", "initial public offering", "merger", "acquisition", "takeover",
    "bankruptcy", "default", "debt ceiling", "government shutdown",
    "flash crash", "circuit breaker", "market halt", "trading suspended",
    "volatility spike", "vix", "fear index", "market crash", "sell-off",
    "rally", "surge", "plunge", "tumble", "soar", "rocket", "dump",
    
    # Gold & Precious Metals
    "gold", "xau", "xauusd", "precious metals", "bullion", "safe haven",
    "silver", "xag", "platinum", "palladium", "metals", "commodities",
    "gold reserve", "central bank gold", "gold etf", "gld", "gold price",
    "gold demand", "gold supply", "mining", "jewelry demand",
    
    # Oil & Energy
    "oil", "wti", "brent", "crude", "petroleum", "opec", "opec+",
    "production cut", "output cut", "supply disruption", "pipeline",
    "gasoline", "natural gas", "energy", "shale", "fracking",
    "strategic reserve", "spr", "inventory", "eia report", "api report",
    "renewable energy", "solar", "wind", "clean energy", "climate",
    "carbon", "emissions", "paris agreement", "cop", "green deal",
    
    # FX & Currencies
    "dxy", "dollar index", "usd", "euro", "eurusd", "cable", "gbpusd",
    "yen", "usdjpy", "swiss franc", "usdchf", "canadian dollar", "usdcad",
    "australian dollar", "audusd", "kiwi", "nzdusd", "emerging markets",
    "currency war", "devaluation", "peg", "intervention", "carry trade",
    
    # Indices & Stocks
    "nasdaq", "s&p 500", "spx", "sp500", "dow jones", "djia", "dow",
    "russell 2000", "rut", "ftse 100", "dax", "cac 40", "nikkei",
    "hang seng", "shanghai composite", "msci", "emerging markets index",
    "tech stocks", "faang", "magnificent seven", "big tech", "chip stocks",
    "semiconductor", "nvidia", "apple", "tesla", "amazon", "microsoft",
    "google", "alphabet", "meta", "facebook", "netflix",
    "bank stocks", "financial sector", "xlf", "regional banks",
    
    # Crypto
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "blockchain", "defi", "nft", "altcoin", "binance", "coinbase",
    "etf approval", "spot etf", "futures etf", "sec", "regulation",
    "mining", "halving", "wallet", "exchange", "hack", "scam",
    
    # Bonds & Fixed Income
    "treasury", "bond yield", "10-year", "2-year", "yield curve",
    "inversion", "credit spread", "junk bond", "high yield", "investment grade",
    "corporate bond", "municipal bond", "federal reserve balance sheet",
    
    # Specific Events
    "jackson hole", "symposium", "davos", "wto", "imf", "world bank",
    "g7", "g20", "brics", "summit", "meeting", "press conference",
    "testimony", "congressional hearing", "beige book",
]

# Spam keywords to filter out
SPAM_KEYWORDS = [
    "sponsored", "advertisement", "promoted", "promotion",
    "affiliate", "partner content", "paid content",
    "click here", "subscribe now", "limited time offer",
    "credit card", "mortgage rates", "personal loan",
    "sweepstakes", "lottery", "win", "prize",
]

# HTML entity patterns
HTML_ENTITY_PATTERN = re.compile(r'&(#?[a-zA-Z0-9]+?);')
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')


@dataclass
class RSSNewsItem:
    id: str
    source: str
    original_url: str
    published_at: datetime
    fetched_at: datetime
    title: str
    content: str
    category: str
    
    # AI Analysis
    impacts: List[Dict[str, Any]]
    sentiment: str
    volatility_expectation: str
    urgency: str  # breaking, high, medium, low
    ai_confidence: float
    ai_processed: bool
    processed_at: Optional[datetime]
    
    # Cross-source tracking
    duplicate_of: Optional[str]
    sources: List[str]
    
    # Turkish translations
    title_tr: str = ""
    content_tr: str = ""
    
    @property
    def should_display(self) -> bool:
        """Determine if this news should be displayed on chart"""
        if not self.ai_processed:
            return False
        if self.ai_confidence < 0.6:
            return False
        if self.urgency == "low":
            return False
        return True


class RSSAggregator:
    """Main RSS aggregation service"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.processed_urls: Set[str] = set()
        self.processed_titles: Dict[str, datetime] = {}  # title hash -> timestamp
        self.failed_sources: Dict[str, int] = {}  # source -> consecutive failures
        self.last_fetch: Dict[str, datetime] = {}  # source -> last fetch time
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "ForexsAI-Bot/1.0 (contact@forexsai.com)",
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
                timeout=aiohttp.ClientTimeout(total=10),
            )
        return self.session
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML entities and tags from text"""
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = HTML_TAG_PATTERN.sub('', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _truncate_content(self, text: str, max_chars: int = 500) -> str:
        """Truncate content for AI processing"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(' ', 1)[0] + "..."
    
    def _generate_id(self, title: str, date: datetime) -> str:
        """Generate canonical ID based on normalized title and date"""
        # Normalize: lowercase, remove special chars
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = ' '.join(normalized.split())  # Remove extra spaces
        
        # Use date without time for grouping
        date_str = date.strftime('%Y%m%d')
        
        # Create hash
        hash_input = f"{normalized}:{date_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _is_similar_title(self, title1: str, title2: str, threshold: float = 0.85) -> bool:
        """Check if two titles are similar using Levenshtein distance"""
        # Clean both titles
        clean1 = re.sub(r'[^\w\s]', '', title1.lower())
        clean2 = re.sub(r'[^\w\s]', '', title2.lower())
        
        # Calculate similarity
        similarity = SequenceMatcher(None, clean1, clean2).ratio()
        return similarity >= threshold
    
    def _should_analyze(self, title: str, content: str = "") -> tuple[bool, str]:
        """
        Pre-filter to decide if news should go to AI analysis
        Returns: (should_analyze, reason)
        """
        text = f"{title} {content}".lower()
        
        # Check spam
        for spam in SPAM_KEYWORDS:
            if spam in text:
                return False, "spam"
        
        # Check high priority keywords
        matched_keywords = []
        for keyword in HIGH_PRIORITY_KEYWORDS:
            if keyword in text:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            return True, f"keywords: {', '.join(matched_keywords[:3])}"
        
        # Check if it's market-related (broader check)
        market_terms = ["market", "stock", "trade", "trading", "investor", "investment",
                       "price", "rally", "decline", "gain", "loss", "session"]
        if any(term in text for term in market_terms):
            return True, "market_related"
        
        return False, "no_keywords"
    
    async def _fetch_feed(self, source_name: str, source_config: Dict) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        url = source_config["url"]
        
        # Check if source is paused due to failures
        if self.failed_sources.get(source_name, 0) >= 3:
            last_fail = self.last_fetch.get(source_name)
            if last_fail and datetime.utcnow() - last_fail < timedelta(minutes=30):
                print(f"[RSS] {source_name} is paused due to repeated failures")
                return []
            # Reset failure count after pause
            self.failed_sources[source_name] = 0
        
        # Rate limiting
        last_fetch = self.last_fetch.get(source_name)
        min_interval = source_config.get("fetch_interval", 120)
        
        if last_fetch and (datetime.utcnow() - last_fetch).seconds < min_interval:
            return []
        
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content = await response.text()
                
                # Parse feed
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    print(f"[RSS] {source_name} parse warning: {feed.bozo_exception}")
                
                # Update tracking
                self.last_fetch[source_name] = datetime.utcnow()
                self.failed_sources[source_name] = 0
                
                # Process entries
                items = []
                for entry in feed.entries[:20]:  # Limit to 20 most recent
                    item = {
                        "source": source_name,
                        "title": self._clean_html(entry.get("title", "")),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": self._clean_html(entry.get("summary", "")),
                        "content": self._clean_html(entry.get("content", [{}])[0].get("value", "")),
                    }
                    items.append(item)
                
                print(f"[RSS] {source_name}: fetched {len(items)} items")
                return items
                
        except Exception as e:
            print(f"[RSS] {source_name} error: {e}")
            self.failed_sources[source_name] = self.failed_sources.get(source_name, 0) + 1
            return []
    
    async def fetch_all_feeds(self) -> List[RSSNewsItem]:
        """Fetch all RSS feeds concurrently"""
        all_items = []
        
        # Create tasks for all sources
        tasks = []
        for source_name, config in RSS_SOURCES.items():
            task = self._fetch_feed(source_name, config)
            tasks.append((source_name, task))
        
        # Execute all fetches
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # Process results
        for (source_name, _), items in zip(tasks, results):
            if isinstance(items, Exception):
                print(f"[RSS] {source_name} failed: {items}")
                continue
            
            for item_data in items:
                # Parse date
                try:
                    published = feedparser._parse_date(item_data["published"])
                    published_dt = datetime(*published[:6])
                except:
                    published_dt = datetime.utcnow()
                
                # Skip old news (> 48 hours)
                if datetime.utcnow() - published_dt > timedelta(hours=48):
                    continue
                
                # Generate ID
                item_id = self._generate_id(item_data["title"], published_dt)
                
                # Check for duplicates
                duplicate_of = None
                for existing_id, existing_time in self.processed_titles.items():
                    if existing_time.date() == published_dt.date():
                        # Check similarity
                        if self._is_similar_title(item_data["title"], existing_id):
                            duplicate_of = existing_id
                            break
                
                # Pre-filter for AI analysis
                should_analyze, reason = self._should_analyze(
                    item_data["title"],
                    item_data.get("summary", "")
                )
                
                # Create item (without AI analysis yet)
                item = RSSNewsItem(
                    id=item_id,
                    source=source_name,
                    original_url=item_data["link"],
                    published_at=published_dt,
                    fetched_at=datetime.utcnow(),
                    title=item_data["title"],
                    content=self._truncate_content(item_data.get("summary", "")),
                    category=RSS_SOURCES[source_name]["category"],
                    impacts=[],
                    sentiment="neutral",
                    volatility_expectation="medium",
                    urgency="medium",
                    ai_confidence=0.0,
                    ai_processed=False,
                    processed_at=None,
                    duplicate_of=duplicate_of,
                    sources=[source_name] if not duplicate_of else [source_name, "duplicate"],
                )
                
                all_items.append(item)
                
                # Track processed titles for duplicate detection
                if not duplicate_of:
                    self.processed_titles[item_id] = published_dt
        
        # Sort by published date (newest first)
        all_items.sort(key=lambda x: x.published_at, reverse=True)
        
        return all_items
    
    def _is_market_related(self, title: str, content: str) -> bool:
        """Check if news is related to important financial markets"""
        text = f"{title} {content}".lower()
        
        # Check if any market keyword exists
        for keyword in MARKET_KEYWORDS:
            if keyword in text:
                return True
        
        return False
    
    def _get_cache_key(self, title: str) -> str:
        """Generate cache key for a news item"""
        # Normalize title for consistent cache keys
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        title_hash = hashlib.md5(normalized.encode()).hexdigest()[:16]
        return f"news_analysis:{title_hash}"
    
    async def analyze_with_ai(self, item: RSSNewsItem) -> RSSNewsItem:
        """Send news to DeepSeek AI with caching and smart filtering"""
        import os
        
        # Check if DeepSeek API key is configured
        api_key = os.getenv("DEEP_SEEKR1", "")
        if not api_key:
            print(f"[RSS] WARNING: DEEP_SEEKR1 not set! Using fallback for: {item.title[:50]}...")
            return self._fallback_analysis(item)
        
        # STEP 1: Check if news is market-related (skip non-financial news)
        if not self._is_market_related(item.title, item.content):
            print(f"[RSS] SKIP (not market-related): {item.title[:50]}...")
            item.urgency = "low"
            item.ai_processed = True
            item.processed_at = datetime.utcnow()
            item.ai_confidence = 0.3
            return item
        
        # STEP 2: Check Redis cache first
        cache_key = self._get_cache_key(item.title)
        cached_result = cache_get(cache_key)
        
        if cached_result:
            print(f"[RSS] CACHE HIT for: {item.title[:50]}...")
            # Restore cached analysis
            item.impacts = cached_result.get("impacts", [])
            item.title_tr = cached_result.get("title_tr", f"[TR] {item.title}")
            item.content_tr = cached_result.get("content_tr", item.content)
            item.sentiment = cached_result.get("sentiment", "neutral")
            item.volatility_expectation = cached_result.get("volatility_expectation", "medium")
            item.urgency = cached_result.get("urgency", "medium")
            item.ai_confidence = cached_result.get("ai_confidence", 0.7)
            item.ai_processed = True
            item.processed_at = datetime.utcnow()
            return item
        
        # STEP 3: Call DeepSeek AI (cache miss)
        print(f"[RSS] CACHE MISS - Calling DeepSeek for: {item.title[:50]}...")
        
        try:
            from services.news_analyzer_v2 import get_real_analyzer
            analyzer = get_real_analyzer()
            
            result = await analyzer.analyze(
                headline=item.title,
                content=item.content,
                source=item.source
            )
            
            # Check if any important symbol is affected
            important_impacts = [
                imp for imp in result.impacts 
                if imp.symbol in IMPORTANT_SYMBOLS and imp.score >= 5
            ]
            
            # Map to item
            item.impacts = [
                {
                    "symbol": imp.symbol,
                    "direction": imp.direction,
                    "score": imp.score,
                    "confidence": imp.confidence,
                    "reasoning": imp.reasoning,
                    "reasoning_tr": imp.reasoning_tr,
                    "emoji": "📈" if imp.direction == "bullish" else "📉" if imp.direction == "bearish" else "➡️",
                }
                for imp in result.impacts
            ]
            
            item.title_tr = result.headline_tr if result.headline_tr else f"[TR] {item.title}"
            item.content_tr = result.content_tr if result.content_tr else item.content
            item.sentiment = result.sentiment
            item.volatility_expectation = result.volatility_expectation
            item.ai_confidence = result.confidence / 100.0
            item.urgency = result.urgency
            item.ai_processed = True
            item.processed_at = datetime.utcnow()
            
            # STEP 4: Store in cache (2 hours TTL)
            cache_data = {
                "impacts": item.impacts,
                "title_tr": item.title_tr,
                "content_tr": item.content_tr,
                "sentiment": item.sentiment,
                "volatility_expectation": item.volatility_expectation,
                "urgency": item.urgency,
                "ai_confidence": item.ai_confidence,
            }
            cache_set(cache_key, cache_data, ttl=7200)  # 2 hours
            print(f"[RSS] Cached analysis for: {item.title[:50]}...")
            
        except asyncio.TimeoutError:
            print(f"[RSS] DeepSeek TIMEOUT for: {item.title[:50]}...")
            item = self._fallback_analysis(item)
        except Exception as e:
            print(f"[RSS] DeepSeek ERROR: {e}")
            item = self._fallback_analysis(item)
        
        return item
    
    def _fallback_analysis(self, item: RSSNewsItem) -> RSSNewsItem:
        """Rule-based analysis when AI fails - TURKISH TRANSLATIONS INCLUDED"""
        from services.news_analyzer import IMPACT_RULES
        
        text = f"{item.title} {item.content}".lower()
        
        # Simple translation dictionary for common financial terms
        translations = {
            "earnings": "kazanç",
            "revenue": "gelir",
            "profit": "kâr",
            "loss": "zarar",
            "beat": "tahminleri aştı",
            "miss": "tahminleri karşılayamadı",
            "growth": "büyüme",
            "decline": "düşüş",
            "surge": "yükseliş",
            "drop": "düşüş",
            "rise": "yükseliş",
            "fall": "düşüş",
            "strong": "güçlü",
            "weak": "zayıf",
            "bullish": "yükseliş trendi",
            "bearish": "düşüş trendi",
            "buy": "alım",
            "sell": "satım",
            "hold": "bekle",
            "outperform": "üstün performans",
            "underperform": "zayıf performans",
            "upgrade": "yükseltildi",
            "downgrade": "düşürüldü",
            "target": "hedef",
            "price": "fiyat",
            "market": "piyasa",
            "stock": "hisse",
            "trading": "ticaret",
            "investor": "yatırımcı",
            "analyst": "analist",
            "report": "rapor",
            "quarter": "çeyrek",
            "fiscal": "mali",
            "guidance": "tahmin",
            "outlook": "görünüm",
            "forecast": "öngörü",
            "expectation": "beklenti",
            "estimate": "tahmin",
            "result": "sonuç",
            "announcement": "duyuru",
            "statement": "açıklama",
            "conference": "konferans",
            "call": "toplantı",
            "meeting": "toplantı",
            "discussion": "tartışma",
            "update": "güncelleme",
            "news": "haber",
            "update": "güncelleme",
            "alert": "uyarı",
            "breaking": "son dakika",
        }
        
        # BEST-MATCH: Find the rule with the MOST keyword matches (not first-match)
        best_rule_name = None
        best_rule = None
        best_match_count = 0
        
        for rule_name, rule in IMPACT_RULES.items():
            match_count = sum(1 for keyword in rule["keywords"] if keyword in text)
            if match_count > best_match_count:
                best_match_count = match_count
                best_rule_name = rule_name
                best_rule = rule
        
        if best_rule and best_match_count > 0:
            print(f"[RSS] Fallback matched rule '{best_rule_name}' with {best_match_count} keyword hits for: {item.title[:60]}...")
            item.impacts = [
                {
                    "symbol": imp["symbol"],
                    "direction": imp["direction"],
                    "score": imp["score"],
                    "confidence": 0.7,
                    "reasoning": imp["reasoning"],
                    "reasoning_tr": f"{imp['symbol']} için {imp['direction'] == 'bullish' and 'yükseliş' or imp['direction'] == 'bearish' and 'düşüş' or 'nötr'} etki",
                    "emoji": "📈" if imp["direction"] == "bullish" else "📉" if imp["direction"] == "bearish" else "➡️",
                }
                for imp in best_rule["impacts"]
            ]
            item.sentiment = best_rule["sentiment"]
            item.volatility_expectation = best_rule["volatility"]
            item.urgency = "high" if best_rule["volatility"] == "high" else "medium"
            item.ai_confidence = 0.75
            item.ai_processed = True
            item.processed_at = datetime.utcnow()
            
            # Generate Turkish translations
            item.title_tr = self._quick_translate(item.title, translations)
            item.content_tr = self._quick_translate(item.content[:200] + "..." if len(item.content) > 200 else item.content, translations)
            
            return item
        
        # No rules matched - STILL ADD TURKISH TRANSLATIONS
        item.ai_processed = True
        item.processed_at = datetime.utcnow()
        item.urgency = "low"
        item.impacts = []
        
        # Generate Turkish translations even for low urgency
        item.title_tr = self._quick_translate(item.title, translations)
        item.content_tr = self._quick_translate(item.content[:200] + "..." if len(item.content) > 200 else item.content, translations)
        
        return item
    
    def _quick_translate(self, text: str, translations: dict) -> str:
        """Quick keyword-based translation"""
        if not text:
            return text
        
        translated = text
        for en, tr in translations.items():
            translated = translated.replace(en, tr).replace(en.capitalize(), tr.capitalize()).replace(en.upper(), tr.upper())
        
        # If no translation happened, add a marker
        if translated == text:
            return f"[TR] {text}"
        
        return translated
    
    async def _check_economic_calendar(self, item: RSSNewsItem) -> RSSNewsItem:
        """Check if news matches any economic calendar event"""
        try:
            from services.economic_calendar_service import get_calendar_service
            
            calendar = get_calendar_service()
            events = await calendar.fetch_today_events()
            
            news_title = item.title.lower()
            news_time = item.published_at
            
            for event in events:
                # Check time proximity (within 30 minutes)
                time_diff = abs((news_time - event.timestamp).total_seconds())
                
                if time_diff < 1800:  # 30 minutes
                    # Check if event keywords match
                    event_keywords = event.event_name.lower().split()
                    matches = sum(1 for kw in event_keywords if kw in news_title)
                    
                    if matches >= 2:  # At least 2 keywords match
                        # This news is about an economic event!
                        item.urgency = "high"
                        item.volatility_expectation = "high"
                        
                        # Add economic event info
                        if not item.impacts:
                            item.impacts = []
                        
                        # Add impacts for affected symbols
                        for symbol in event.affected_symbols:
                            if not any(imp.get("symbol") == symbol for imp in item.impacts):
                                item.impacts.append({
                                    "symbol": symbol,
                                    "direction": "neutral",  # Will be determined by AI
                                    "score": 7 if event.impact == "high" else 5,
                                    "confidence": 0.75,
                                    "reasoning": f"Related to {event.event_name}",
                                    "reasoning_tr": f"{event.event_name} ile ilgili",
                                    "emoji": "📊",
                                    "is_economic_event": True,
                                    "event_name": event.event_name
                                })
                        
                        print(f"[RSS] Matched economic event: {event.event_name} for news: {item.title[:50]}...")
                        break
            
            return item
        except Exception as e:
            print(f"[RSS] Economic calendar check error: {e}")
            return item
    
    async def store_in_database(self, item: RSSNewsItem) -> bool:
        """Store processed news in database with economic calendar integration"""
        try:
            # Check economic calendar first
            item = await self._check_economic_calendar(item)
            
            supabase = get_supabase_client()
            
            # Check if already exists
            existing = supabase.table("enriched_news").select("id").eq("id", item.id).execute()
            
            existing_data = []
            if hasattr(existing, 'data'):
                existing_data = existing.data or []
            elif isinstance(existing, dict):
                existing_data = existing.get('data', []) or []
            
            if existing_data:
                # Update sources list if duplicate from another source
                if item.duplicate_of:
                    supabase.table("enriched_news").update({
                        "sources": item.sources
                    }).eq("id", item.id).execute()
                return False
            
            # Prepare impacts with Turkish translations
            impacts_with_tr = []
            for imp in item.impacts:
                imp_copy = dict(imp)
                # Ensure reasoning_tr exists
                if "reasoning_tr" not in imp_copy or not imp_copy["reasoning_tr"]:
                    direction_tr = "yükseliş" if imp.get("direction") == "bullish" else "düşüş" if imp.get("direction") == "bearish" else "nötr"
                    imp_copy["reasoning_tr"] = f"{imp.get('symbol', 'Sembol')} için {direction_tr} etki"
                impacts_with_tr.append(imp_copy)
            
            # Determine marker type for chart
            marker_type = "news"
            marker_color = "#3B82F6"  # Blue for regular news
            
            if item.urgency == "breaking":
                marker_type = "breaking_news"
                marker_color = "#EF4444"  # Red
            elif item.urgency == "high":
                marker_type = "high_impact"
                marker_color = "#F59E0B"  # Orange
            elif any(imp.get("is_economic_event") for imp in item.impacts):
                marker_type = "economic_event"
                marker_color = "#8B5CF6"  # Purple
            
            # Insert new - WITH TURKISH TRANSLATIONS
            data = {
                "id": item.id,
                "timestamp": item.published_at.isoformat(),
                "source": item.source,
                "headline": item.title,
                "headline_tr": item.title_tr if item.title_tr else f"[TR] {item.title}",
                "content": item.content,
                "content_tr": item.content_tr if item.content_tr else item.content[:300] + "..." if len(item.content) > 300 else item.content,
                "category": item.category,
                "url": item.original_url,
                "impacts": impacts_with_tr,
                "sentiment": item.sentiment,
                "volatility_expectation": item.volatility_expectation,
                "event_duration": "short_term",
                "ai_confidence": item.ai_confidence * 100,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "urgency": item.urgency,
                "duplicate_of": item.duplicate_of,
                "sources": item.sources,
                # Chart marker data
                "marker_type": marker_type,
                "marker_color": marker_color,
                "show_on_chart": item.urgency in ["high", "breaking"] or any(imp.get("score", 0) >= 6 for imp in item.impacts),
            }
            
            supabase.table("enriched_news").insert(data).execute()
            return True
            
        except Exception as e:
            print(f"[RSS] Database error: {e}")
            return False
    
    async def run_aggregation_cycle(self) -> Dict[str, Any]:
        """Run one full aggregation cycle"""
        stats = {
            "fetched": 0,
            "new": 0,
            "duplicates": 0,
            "ai_analyzed": 0,
            "rule_based": 0,
            "errors": 0,
        }
        
        try:
            supabase = get_supabase_client()
            
            # Fetch all feeds
            items = await self.fetch_all_feeds()
            stats["fetched"] = len(items)
            print(f"[RSS] Fetched {len(items)} total items from RSS feeds")
            
            # Process each item
            for item in items:
                try:
                    # Check if already in database
                    existing = supabase.table("enriched_news").select("id").eq("id", item.id).execute()
                    
                    if hasattr(existing, 'data') and existing.data:
                        stats["duplicates"] += 1
                        continue
                    
                    # Analyze with AI (with timeout) - ALL NEWS GOES TO DEEPSEEK
                    if not item.duplicate_of:
                        try:
                            # 25 second timeout for DeepSeek AI analysis per item
                            item = await asyncio.wait_for(
                                self.analyze_with_ai(item),
                                timeout=25.0
                            )
                            # Check if it was real AI analysis or fallback
                            if item.ai_confidence >= 0.6 and item.title_tr and not item.title_tr.startswith("[TR]"):
                                stats["ai_analyzed"] += 1
                                print(f"[RSS] ✓ Real DeepSeek analysis for: {item.title[:50]}...")
                            else:
                                stats["rule_based"] += 1
                                print(f"[RSS] ⚠ Fallback used for: {item.title[:50]}...")
                        except asyncio.TimeoutError:
                            print(f"[RSS] ⏱ AI analysis TIMEOUT for: {item.title[:60]}...")
                            # Use fallback analysis when AI times out
                            item = self._fallback_analysis(item)
                            stats["rule_based"] += 1
                        except Exception as e:
                            print(f"[RSS] ❌ AI analysis ERROR: {e}")
                            item = self._fallback_analysis(item)
                            stats["rule_based"] += 1
                    
                    # ALWAYS store in database - filtering is done at read time
                    if await self.store_in_database(item):
                        stats["new"] += 1
                    
                except Exception as e:
                    print(f"[RSS] Error processing item {item.id}: {e}")
                    stats["errors"] += 1
            
            print(f"[RSS] Cycle complete: {stats}")
            
        except Exception as e:
            print(f"[RSS] Aggregation cycle error: {e}")
            stats["errors"] += 1
        
        return stats


# Singleton instance
_aggregator: Optional[RSSAggregator] = None


def get_rss_aggregator() -> RSSAggregator:
    """Get or create aggregator singleton"""
    global _aggregator
    if _aggregator is None:
        _aggregator = RSSAggregator()
    return _aggregator
