from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from backend.models.news import NewsFeedResponse, NewsItem
from backend.services.news_fetcher import classify_sentiment, fetch_economic_events, fetch_market_news, infer_category

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/feed", response_model=NewsFeedResponse)
async def get_news_feed(
    limit: int = Query(default=20, ge=5, le=100),
    impact: Optional[str] = Query(default=None, pattern="^(high|medium|low)$"),
    category: Optional[str] = Query(default=None, pattern="^(fed|inflation|jobs)$"),
) -> NewsFeedResponse:
    economic_events = await fetch_economic_events(days=7)
    market_news = await fetch_market_news(limit=30)

    feed: list[NewsItem] = []

    for event in economic_events:
        event_name = event.get("event", "Economic Event")
        impact_label = event.get("impact", "Medium")
        sentiment = classify_sentiment(event)
        feed.append(
            NewsItem(
                type="economic_event",
                id=f"event_{event.get('date')}_{event_name}",
                timestamp=_normalize_timestamp(event.get("date")),
                title=event_name,
                impact=impact_label,
                actual=event.get("actual"),
                expected=event.get("estimate"),
                previous=event.get("previous"),
                sentiment=sentiment,
                category=infer_category(event_name),
                market_reaction=_market_reaction_label(sentiment),
            )
        )

    for news in market_news:
        title = news.get("title", "Market News")
        sentiment = classify_sentiment({"title": title})
        feed.append(
            NewsItem(
                type="market_news",
                id=str(news.get("link") or news.get("date") or title),
                timestamp=_normalize_timestamp(news.get("date")),
                title=title,
                content=(news.get("content") or "")[:200] + "...",
                link=news.get("link"),
                sentiment=sentiment,
                category=infer_category(title),
            )
        )

    feed.sort(key=lambda item: item.timestamp, reverse=True)

    if impact:
        feed = [item for item in feed if (item.impact or "").lower() == impact.lower()]

    if category:
        feed = [item for item in feed if item.category == category]

    return NewsFeedResponse(total=len(feed), news=feed[:limit])


def _normalize_timestamp(value: Optional[str]) -> str:
    if not value:
        return datetime.utcnow().isoformat() + "Z"
    return value if value.endswith("Z") else f"{value}Z"


def _market_reaction_label(sentiment: str) -> str:
    if sentiment == "bullish":
        return "Positive reaction expected"
    if sentiment == "bearish":
        return "Risk-off reaction expected"
    return "Muted reaction expected"
