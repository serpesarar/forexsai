"""Kaynak uyarlayıcıları: yanıtı ortak `RawItem` listesine çevirir. Ağ katmanı engine'dedir; ayrıştırıcılar saf ve testlidir.

Kod kökenleri (yeniden yazıldı, kopyalanmadı): Truth uç noktası `w2rc/truthbrush`, Alpaca protokolü `alpacahq/alpaca-py`,
Finnhub uç noktası `Finnhub-Stock-API/finnhub-python`. Bu depolar bağımlılık olarak EKLENMEDİ: üçü de tek HTTP/WS çağrısına
iniyor; truthbrush tarayıcı taklidi için ek paket, alpaca-py ise msgpack + pydantic zinciri getiriyordu.
"""
from __future__ import annotations

import calendar
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import feedparser

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
MAX_TITLE = 400
_TG_SPLIT = re.compile(r'(?=<div class="tgme_widget_message_wrap)')
_TG_POST = re.compile(r'data-post="([^"]+)"')
_TG_TEXT = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
_TG_TIME = re.compile(r'<time datetime="([^"]+)"')


@dataclass(frozen=True)
class RawItem:
    """Kaynaktan çıkan tek başlık."""

    ext_id: str
    title: str
    url: str
    published_ts: float | None


def clean_text(raw: str) -> str:
    """HTML etiketlerini ve fazla boşlukları temizler."""
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", raw or ""))).strip()


def parse_iso(value: str | None) -> float | None:
    """ISO-8601 zamanı epoch saniyeye çevirir; bozuksa None."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def parse_rss(body: bytes) -> list[RawItem]:
    """RSS/Atom gövdesini ayrıştırır. Kimlik: guid, yoksa bağlantı, yoksa başlık."""
    out: list[RawItem] = []
    for e in feedparser.parse(body).entries:
        title = clean_text(e.get("title", ""))[:MAX_TITLE]
        if not title:
            continue
        link = e.get("link", "") or ""
        stamp = e.get("published_parsed") or e.get("updated_parsed")
        out.append(RawItem(str(e.get("id") or link or title), title, link, calendar.timegm(stamp) if stamp else None))
    return out


def parse_telegram(body: bytes) -> list[RawItem]:
    """t.me/s/<kanal> açık önizleme sayfasını ayrıştırır (oturum/anahtar gerektirmez)."""
    out: list[RawItem] = []
    for block in _TG_SPLIT.split(body.decode("utf-8", "ignore")):
        post, text = _TG_POST.search(block), _TG_TEXT.search(block)
        if not post or not text:
            continue
        title = clean_text(text.group(1).replace("<br/>", " ").replace("<br>", " "))[:MAX_TITLE]
        if not title:
            continue
        when = _TG_TIME.search(block)
        out.append(RawItem(post.group(1), title, f"https://t.me/{post.group(1)}", parse_iso(when.group(1) if when else None)))
    return out


def parse_truth(body: bytes) -> list[RawItem]:
    """Truth Social (Mastodon uyumlu) gönderi listesi. Yalnız bağlantı/medya içeren gönderiler de kaydedilir."""
    out: list[RawItem] = []
    for st in json.loads(body or b"[]"):
        inner = st.get("reblog") or st
        title = clean_text(inner.get("content", ""))[:MAX_TITLE]
        if not title:
            title = "[Metinsiz gönderi: bağlantı/medya]"
        title = f"Trump (Truth Social): {title}"
        out.append(RawItem(str(st.get("id")), title, st.get("url") or "", parse_iso(st.get("created_at"))))
    return out


def parse_finnhub(body: bytes) -> list[RawItem]:
    """Finnhub /news yanıtı."""
    out: list[RawItem] = []
    for it in json.loads(body or b"[]"):
        title = clean_text(it.get("headline", ""))[:MAX_TITLE]
        if title:
            stamp = it.get("datetime")
            out.append(RawItem(str(it.get("id")), title, it.get("url", ""), float(stamp) if stamp else None))
    return out


def parse_alpaca_frame(frame: str | bytes) -> list[RawItem]:
    """Alpaca haber WebSocket JSON çerçevesi: yalnız `T == 'n'` iletileri haberdir."""
    out: list[RawItem] = []
    data = json.loads(frame)
    for m in data if isinstance(data, list) else [data]:
        if m.get("T") == "n" and m.get("headline"):
            out.append(RawItem(str(m.get("id")), clean_text(m["headline"])[:MAX_TITLE], m.get("url") or "",
                               parse_iso(m.get("created_at"))))
    return out


def alpaca_handshake(key: str, secret: str) -> Iterable[str]:
    """Alpaca kimlik doğrulama + tüm haberlere abonelik iletileri."""
    yield json.dumps({"action": "auth", "key": key, "secret": secret})
    yield json.dumps({"action": "subscribe", "news": ["*"]})


def parse_benzinga_frame(frame: str | bytes) -> list[RawItem]:
    """Benzinga News Stream çerçevesi; yalnız yeni haberler (güncelleme/silme ayrı olay, yarışa girmez)."""
    msg: dict[str, Any] = json.loads(frame)
    data = msg.get("data") or {}
    if str(data.get("action", "")).lower() != "created":
        return []
    content = data.get("content") or {}
    title = clean_text(content.get("title", ""))[:MAX_TITLE]
    if not title:
        return []
    return [RawItem(str(data.get("id") or content.get("id")), title, content.get("url", ""), parse_iso(content.get("created_at")))]


POLL_PARSERS = {"rss": parse_rss, "telegram": parse_telegram, "truth": parse_truth, "finnhub": parse_finnhub}
