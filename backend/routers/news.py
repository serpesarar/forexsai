from __future__ import annotations

from datetime import datetime
import hashlib
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from services.marketaux_service import fetch_marketaux_headlines
from services.translation_service import translate_texts


router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/feed")
async def news_feed(
    impact: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    lang: str = Query(default="en"),
) -> Dict[str, Any]:
    """
    Minimal live news feed backed by Marketaux.
    Frontend expects: { total: number, news: NewsItem[] }
    """
    _ = impact
    _ = category

    # Marketaux symbols can be picky; service will return [] if key missing.
    headlines = await fetch_marketaux_headlines(["NDX", "XAUUSD"])
    titles = [(h.get("title") or "").strip() for h in headlines]
    translated_titles = await translate_texts(titles, target_lang=lang)
    news = []
    for item, title in zip(headlines, translated_titles):
        title = (title or "").strip()
        source = (item.get("source") or "").strip() or "marketaux"
        if not title:
            continue
        stable_id = hashlib.md5(f"{title}|{source}".encode("utf-8")).hexdigest()
        news.append(
            {
                "type": "market_news",
                "id": stable_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "title": title,
                "content": "",
                "link": "",
                "category": "market_news",
            }
        )

    return {"total": len(news), "news": news}


