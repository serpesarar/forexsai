"""
RSS News Aggregator Service
Fetches financial news from multiple RSS sources with intelligent filtering
"""

import asyncio
import hashlib
import html
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, asdict
import aiohttp
import feedparser
from difflib import SequenceMatcher

from services.news_analyzer import get_analyzer, NewsAnalysisResult
from database.supabase_client import get_supabase_client

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
    
    # Priority 3 - Commodities & Crypto
    "kitco_gold": {
        "url": "https://www.kitco.com/rss/gold-news.xml",
        "priority": 3,
        "category": "commodities",
        "fetch_interval": 600,  # 10 minutes
    },
    "coindesk": {
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "priority": 3,
        "category": "crypto",
        "fetch_interval": 600,
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/rss",
        "priority": 3,
        "category": "crypto",
        "fetch_interval": 600,
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
    
    async def analyze_with_ai(self, item: RSSNewsItem) -> RSSNewsItem:
        """Send news to REAL DeepSeek AI for analysis"""
        try:
            # Check pre-filter
            should_analyze, reason = self._should_analyze(item.title, item.content)
            
            if not should_analyze:
                # Mark as low priority, skip AI
                item.urgency = "low"
                item.ai_processed = True
                item.processed_at = datetime.utcnow()
                return item
            
            # Get REAL AI analysis (V2 - gerçek analiz)
            from services.news_analyzer_v2 import get_real_analyzer
            analyzer = get_real_analyzer()
            result = await analyzer.analyze(
                headline=item.title,
                content=item.content,
                source=item.source
            )
            
            # Map to item with translations
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
            
            # Store Turkish translations
            item.title_tr = result.headline_tr if result.headline_tr else item.title
            item.content_tr = result.content_tr if result.content_tr else item.content
            item.sentiment = result.sentiment
            item.volatility_expectation = result.volatility_expectation
            item.ai_confidence = result.confidence / 100.0
            item.urgency = result.urgency
            item.ai_processed = True
            item.processed_at = datetime.utcnow()
            
        except Exception as e:
            print(f"[RSS] AI analysis failed for {item.id}: {e}")
            # Fallback to rule-based if AI fails
            item = self._fallback_analysis(item)
        
        return item
    
    def _fallback_analysis(self, item: RSSNewsItem) -> RSSNewsItem:
        """Rule-based analysis when AI fails"""
        from services.news_analyzer import IMPACT_RULES
        
        text = f"{item.title} {item.content}".lower()
        
        for rule_name, rule in IMPACT_RULES.items():
            if any(keyword in text for keyword in rule["keywords"]):
                item.impacts = [
                    {
                        "symbol": imp["symbol"],
                        "direction": imp["direction"],
                        "score": imp["score"],
                        "confidence": 0.7,
                        "reasoning": imp["reasoning"],
                        "emoji": "📈" if imp["direction"] == "bullish" else "📉" if imp["direction"] == "bearish" else "➡️",
                    }
                    for imp in rule["impacts"]
                ]
                item.sentiment = rule["sentiment"]
                item.volatility_expectation = rule["volatility"]
                item.urgency = "high" if rule["volatility"] == "high" else "medium"
                item.ai_confidence = 0.75
                item.ai_processed = True
                item.processed_at = datetime.utcnow()
                return item
        
        # No rules matched
        item.ai_processed = True
        item.processed_at = datetime.utcnow()
        item.urgency = "low"
        return item
    
    async def store_in_database(self, item: RSSNewsItem) -> bool:
        """Store processed news in database"""
        try:
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
            
            # Insert new
            data = {
                "id": item.id,
                "timestamp": item.published_at.isoformat(),
                "source": item.source,
                "headline": item.title,
                "content": item.content,
                "category": item.category,
                "url": item.original_url,
                "impacts": item.impacts,
                "sentiment": item.sentiment,
                "volatility_expectation": item.volatility_expectation,
                "event_duration": "short_term",
                "ai_confidence": item.ai_confidence * 100,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "urgency": item.urgency,
                "duplicate_of": item.duplicate_of,
                "sources": item.sources,
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
                    
                    # Analyze with AI (with timeout) - if passes pre-filter
                    if not item.duplicate_of:
                        try:
                            # 15 second timeout for AI analysis per item
                            item = await asyncio.wait_for(
                                self.analyze_with_ai(item),
                                timeout=15.0
                            )
                            if item.ai_processed and item.urgency != "low":
                                stats["ai_analyzed"] += 1
                            elif item.ai_processed:
                                stats["rule_based"] += 1
                        except asyncio.TimeoutError:
                            print(f"[RSS] AI analysis timeout for: {item.title[:60]}...")
                            # Use fallback analysis when AI times out
                            item = self._fallback_analysis(item)
                            stats["rule_based"] += 1
                        except Exception as e:
                            print(f"[RSS] AI analysis error: {e}")
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
