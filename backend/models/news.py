from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


class NewsItem(BaseModel):
    type: Literal["economic_event", "market_news"]
    id: str
    timestamp: str
    title: str
    impact: Optional[str] = None
    sentiment: Optional[str] = None
    actual: Optional[str] = None
    expected: Optional[str] = None
    previous: Optional[str] = None
    market_reaction: Optional[str] = None
    content: Optional[str] = None
    link: Optional[str] = None
    category: Optional[str] = None


class NewsFeedResponse(BaseModel):
    total: int
    news: List[NewsItem]
