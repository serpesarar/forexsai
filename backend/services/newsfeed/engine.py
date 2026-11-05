"""Çok kaynaklı haber motoru: her kaynak kendi döngüsünde, ilk gören kazanır, başlık yapay zekâyı beklemez.

Akış: sorgu/WS → RawItem → yeni mi? → hikâye kümesi → sınıflandır → bellek + canlı yayın (burada milisaniyeler) →
arka planda toplu veritabanı yazımı. Yeni bir başlığın önündeki tek bekleme kaynağın kendisi ve sorgu aralığıdır.

Tasarım notları:
- Koşullu GET (ETag/Last-Modified): değişmemiş besleme için gövde indirilmez, sık sorgulamak ucuz ve kibardır.
- 429/403/5xx → üstel geri çekilme + Retry-After; bir kaynağın arızası diğerlerini etkilemez.
- Veri yayın pencerelerinde (ET 08:30, 10:00, 14:00; CET 14:15) resmi + squawk 8 sn'ye iner (fx-news-desk `release_racer` fikri).
- İlk sorgu `seeded`: kayıtlar saklanır ama yarışa ve canlı yayına girmez (yeniden başlatmada sahte 'yeni haber' yok).
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from collections import deque
from datetime import datetime
from typing import Any, AsyncIterator
from zoneinfo import ZoneInfo

import aiohttp

from services.newsfeed.adapters import POLL_PARSERS, RawItem, alpaca_handshake, parse_alpaca_frame, parse_benzinga_frame
from services.newsfeed.catalog import SourceDef, active_sources, inactive_sources
from services.newsfeed.classifier import RELEVANCE_MIN, classify
from services.newsfeed.dedup import Sighting, Story, StoryIndex, normalize, story_id, tokens
from services.newsfeed.scoreboard import Scoreboard
from services.newsfeed.store import FLUSH_INTERVAL_S, NewsStore, iso

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; ForexSAI-newsfeed/1.0)"
HTTP_TIMEOUT_S = 12
MAX_CONCURRENT_FETCH = 12
BACKOFF_BASE_S = 30.0
BACKOFF_MAX_S = 900.0
BUFFER_MAX = 2000
SEEN_MAX_PER_SOURCE = 3000
STALE_S = 6 * 3600
SEEDED_MAX_AGE_S = 24 * 3600
JITTER = 0.15
WS_RECONNECT_S = 15.0
SUBSCRIBER_QUEUE = 200
_ET = ZoneInfo("America/New_York")
_CET = ZoneInfo("Europe/Berlin")
# (saat dilimi, HH:MM başlangıç, süre dk): yüksek etkili verilerin yayınlandığı sabit saatler
_RELEASE_WINDOWS = ((_ET, "08:28", 12), (_ET, "09:58", 12), (_ET, "13:58", 42), (_CET, "14:13", 35))


def in_release_window(now_ts: float) -> bool:
    """Hafta içi sabit veri saatlerinden birinin içinde miyiz?"""
    for tz, start, minutes in _RELEASE_WINDOWS:
        dt = datetime.fromtimestamp(now_ts, tz)
        if dt.weekday() >= 5:
            continue
        hh, mm = map(int, start.split(":"))
        elapsed = (dt.hour * 60 + dt.minute) - (hh * 60 + mm)
        if 0 <= elapsed < minutes:
            return True
    return False


class NewsEngine:
    """Tüm kaynak döngülerini ve hikâye dizinini yöneten tekil motor."""

    def __init__(self, sources: list[SourceDef] | None = None, store: NewsStore | None = None) -> None:
        self.sources = sources if sources is not None else active_sources()
        self.board = Scoreboard(self.sources)
        self.store = store or NewsStore()
        self.index = StoryIndex()
        self.buffer: deque[dict[str, Any]] = deque(maxlen=BUFFER_MAX)
        self._by_id: dict[str, dict[str, Any]] = {}
        self._seen: dict[str, dict[str, None]] = {s.id: {} for s in self.sources}
        self._seeded: set[str] = set()
        self._validators: dict[str, dict[str, str]] = {}
        self._subs: set[asyncio.Queue] = set()
        self._tasks: list[asyncio.Task] = []
        self._sem = asyncio.Semaphore(MAX_CONCURRENT_FETCH)
        self._session: aiohttp.ClientSession | None = None
        self.adaptive = os.getenv("NEWSFEED_ADAPTIVE", "1") != "0"
        self.started_ts: float | None = None
        self.ingest_ms: deque[float] = deque(maxlen=500)

    # ── Haber işleme (saf çekirdek: ağ yok, testlidir) ────────────────────────
    def _item_row(self, st: Story, src: SourceDef) -> dict[str, Any]:
        cl = classify(st.headline, src.tier)
        return {
            "id": st.id, "headline": st.headline, "url": st.url, "first_seen_at": iso(st.first_seen_ts),
            "first_seen_ts": st.first_seen_ts, "first_source": st.first_source, "first_source_name": src.name,
            "tier": src.tier, "event_type": cl.event_type, "symbols": list(cl.symbols), "urgency": cl.urgency,
            "relevance": cl.relevance, "confirmation": cl.confirmation, "is_opinion": cl.is_opinion,
            "n_sources": len(st.sightings), "sources": list(st.sightings),
            "published_at": iso(st.sightings[st.first_source].published_ts),
        }

    def ingest(self, src: SourceDef, item: RawItem, now_ts: float, seeded: bool, interval_s: float) -> dict[str, Any] | None:
        """Tek başlığı işler. Yeni hikâye ise satırını döndürür; başka kaynağın hikâyesine katıldıysa onu günceller."""
        seen = self._seen[src.id]
        if item.ext_id in seen:
            return None
        seen[item.ext_id] = None
        if len(seen) > SEEN_MAX_PER_SOURCE:
            seen.pop(next(iter(seen)))
        norm = normalize(item.title)
        if not norm:
            return None
        stale = bool(item.published_ts and now_ts - item.published_ts > STALE_S)
        seeded = seeded or stale
        toks = tokens(norm)
        self.index.purge(now_ts)
        sight = Sighting(src.id, now_ts, item.published_ts, item.url, interval_s, seeded)
        if not seeded and item.published_ts and 0 <= now_ts - item.published_ts:
            self.board.record_publish_lag(src.id, now_ts - item.published_ts)
        story = self.index.find(norm, toks)
        return self._join(story, src, sight) if story else self._new_story(src, item, norm, toks, sight, now_ts)

    def _join(self, story: Story, src: SourceDef, sight: Sighting) -> None:
        if src.id in story.sightings:
            return None
        story.sightings[src.id] = sight
        self.board.record_story_join(story, src.id)
        row = self._by_id.get(story.id)
        if row is not None:
            row["n_sources"] = len(story.sightings)
            row["sources"] = list(story.sightings)
            if row["relevance"] >= RELEVANCE_MIN:   # düşük ilgili hikâye tabloya yazılmaz: sighting FK'yı kırmasın
                self.store.queue_story(self._db_row(row))
                self.store.queue_sighting(self._sighting_row(story, sight))
            if not sight.seeded:
                self._publish({"type": "story_update", "id": story.id, "n_sources": row["n_sources"], "sources": row["sources"]})
        return None

    def _new_story(self, src: SourceDef, item: RawItem, norm: str, toks: frozenset[str], sight: Sighting, now_ts: float) -> dict:
        st = Story(story_id(norm, now_ts), item.title, norm, toks, now_ts, src.id, item.url)
        st.sightings[src.id] = sight
        self.index.add(st)
        row = self._item_row(st, src)
        row["seeded"] = sight.seeded
        # İlk yüklemede görülme saati anlamsızdır: ekranda ve sıralamada yayın saati kullanılır.
        row["display_ts"] = (item.published_ts or now_ts) if sight.seeded else now_ts
        row["display_at"] = iso(row["display_ts"])
        self.buffer.append(row)
        self._by_id[st.id] = row
        while len(self._by_id) > BUFFER_MAX:
            self._by_id.pop(next(iter(self._by_id)))
        if row["relevance"] >= RELEVANCE_MIN:
            self.store.queue_story(self._db_row(row))
            self.store.queue_sighting(self._sighting_row(st, sight))
            if not sight.seeded:
                self.store.queue_legacy(self._legacy_row(row))
        if not sight.seeded:
            self._publish({"type": "story", "story": row})
        return row

    @staticmethod
    def _db_row(row: dict[str, Any]) -> dict[str, Any]:
        keep = ("id", "headline", "url", "first_seen_at", "first_source", "tier", "event_type", "symbols", "urgency",
                "relevance", "confirmation", "is_opinion", "n_sources", "published_at", "seeded")
        return {k: row.get(k) for k in keep}

    @staticmethod
    def _sighting_row(st: Story, s: Sighting) -> dict[str, Any]:
        return {"story_id": st.id, "source_id": s.source_id, "first_seen_at": iso(s.first_seen_ts),
                "published_at": iso(s.published_ts), "lag_s": round(s.first_seen_ts - st.first_seen_ts, 2),
                "poll_interval_s": round(s.poll_interval_s, 1), "seeded": s.seeded}

    @staticmethod
    def _legacy_row(row: dict[str, Any]) -> dict[str, Any]:
        """Eski panellerin (/api/rss/news, news-correlation, market-events) okuduğu tablo; AI alanları boş kalır."""
        return {
            "id": f"nf_{row['id']}", "timestamp": row["first_seen_at"], "source": row["first_source_name"],
            "headline": row["headline"], "content": "", "category": row["event_type"], "url": row["url"] or "", "impacts": [],
            "sentiment": "neutral", "volatility_expectation": "high" if row["urgency"] in ("breaking", "high") else "medium",
            "urgency": row["urgency"], "sources": row["sources"], "importance_score": row["relevance"],
            "ai_model": "newsfeed_rule", "ai_confidence": 0, "event_duration": "short_term",
            "show_on_chart": row["urgency"] in ("breaking", "high"), "marker_type": "news", "marker_color": "#3B82F6",
        }

    # ── Canlı yayın ───────────────────────────────────────────────────────────
    def _publish(self, event: dict[str, Any]) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:   # yavaş istemci akışı tıkamaz; eskiyi at
                q.get_nowait()
                q.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        """SSE/WS tüketicileri için olay akışı."""
        q: asyncio.Queue = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE)
        self._subs.add(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs.discard(q)

    # ── Ağ döngüleri ──────────────────────────────────────────────────────────
    def _handle_failure(self, src: SourceDef, reason: str, retry_after: float | None = None) -> None:
        h = self.board.health[src.id]
        h.errors += 1
        h.consecutive_errors += 1
        h.last_error = reason[:160]
        wait = retry_after or min(BACKOFF_MAX_S, BACKOFF_BASE_S * 2 ** min(h.consecutive_errors - 1, 6))
        h.backoff_until_ts = time.time() + wait

    async def _fetch(self, src: SourceDef) -> bytes | None:
        """Koşullu GET; 304 → None. Anahtarlar URL'ye yalnız burada eklenir, loga yazılmaz."""
        headers = dict(self._validators.get(src.id, {}))
        url = src.url
        if src.kind == "finnhub":
            headers["X-Finnhub-Token"] = os.getenv("FINNHUB_API_KEY", "")
        h = self.board.health[src.id]
        t0 = time.perf_counter()
        async with self._sem:
            async with self._session.get(url, headers=headers) as resp:
                h.polls += 1
                if resp.status == 304:
                    h.not_modified += 1
                    h.last_ok_ts = time.time()
                    h.consecutive_errors = 0
                    return None
                if resp.status != 200:
                    ra = resp.headers.get("Retry-After", "")
                    self._handle_failure(src, f"HTTP {resp.status}", float(ra) if ra.isdigit() else None)
                    return None
                body = await resp.read()
                val = {}
                if resp.headers.get("ETag"):
                    val["If-None-Match"] = resp.headers["ETag"]
                if resp.headers.get("Last-Modified"):
                    val["If-Modified-Since"] = resp.headers["Last-Modified"]
                self._validators[src.id] = val
        h.fetch_ms.append((time.perf_counter() - t0) * 1000)
        h.last_ok_ts = time.time()
        h.consecutive_errors = 0
        return body

    def _absorb(self, src: SourceDef, items: list[RawItem], interval_s: float) -> None:
        """Bir sorgunun tüm kayıtlarını aynı anda işler; ilk sorgu seed sayılır."""
        now = time.time()
        seeded = src.id not in self._seeded
        h = self.board.health[src.id]
        t0 = time.perf_counter()
        fresh = 0
        for item in reversed(items):   # besleme yeniden eskiye gelir; eski önce işlensin
            before = len(self._seen[src.id])
            self.ingest(src, item, now, seeded, interval_s)
            fresh += len(self._seen[src.id]) != before
        self._seeded.add(src.id)
        if fresh and not seeded:
            h.items_new += fresh
            h.last_item_ts = now
            self.ingest_ms.append((time.perf_counter() - t0) * 1000)

    async def _poll_loop(self, src: SourceDef) -> None:
        parser = POLL_PARSERS[src.kind]
        await asyncio.sleep(random.uniform(0, 3))
        while True:
            burst = in_release_window(time.time())
            interval = self.board.interval_for(src.id, burst=burst, adaptive=self.adaptive)
            h = self.board.health[src.id]
            if time.time() >= h.backoff_until_ts:
                try:
                    body = await self._fetch(src)
                    if body is not None:
                        self._absorb(src, parser(body), interval)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001 — tek kaynak döngüsü asla ölmez
                    self._handle_failure(src, f"{type(exc).__name__}: {exc}")
            await asyncio.sleep(interval * random.uniform(1 - JITTER, 1 + JITTER))

    async def _ws_loop(self, src: SourceDef) -> None:
        """Push sağlayıcıları: bağlantı koparsa yeniden bağlanır; anahtar yoksa zaten başlatılmaz."""
        import websockets  # gecikmeli içe aktarma: yalnız anahtar tanımlıysa gerekir

        url, parser, hello = src.url, parse_benzinga_frame, ()
        if src.kind == "alpaca_ws":
            parser = parse_alpaca_frame
            hello = tuple(alpaca_handshake(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"]))
        else:
            url = f"{src.url}?token={os.environ['BENZINGA_API_KEY']}"
        while True:
            try:
                async with websockets.connect(url, open_timeout=HTTP_TIMEOUT_S, ping_interval=20) as ws:
                    for m in hello:
                        await ws.send(m)
                    self._seeded.add(src.id)      # push akışında geçmiş yok: her ileti canlıdır
                    self.board.health[src.id].consecutive_errors = 0
                    async for frame in ws:
                        h = self.board.health[src.id]
                        h.polls += 1
                        h.last_ok_ts = time.time()
                        self._absorb(src, parser(frame), 0.0)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                # Bağlantı dizesi token içerir: istisna metni loga/panele YAZILMAZ.
                self._handle_failure(src, type(exc).__name__)
            await asyncio.sleep(WS_RECONNECT_S)

    async def _store_loop(self) -> None:
        while True:
            await asyncio.sleep(FLUSH_INTERVAL_S)
            now = time.monotonic()
            await self.store.flush(now)
            await self.store.prune_if_due(now)

    # ── Yaşam döngüsü ─────────────────────────────────────────────────────────
    async def start(self) -> None:
        """Tüm döngüleri başlatır."""
        if self._tasks:
            return
        self.started_ts = time.time()
        await self._restore_scoreboard()
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_S)
        self._session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, timeout=timeout)
        for src in self.sources:
            loop = self._ws_loop(src) if src.kind.endswith("_ws") else self._poll_loop(src)
            self._tasks.append(asyncio.create_task(loop, name=f"newsfeed:{src.id}"))
        self._tasks.append(asyncio.create_task(self._store_loop(), name="newsfeed:store"))
        logger.info("[newsfeed] %d kaynak başlatıldı", len(self.sources))

    async def _restore_scoreboard(self) -> None:
        """Yeniden dağıtımda karne sıfırlanmasın: son 7 günün canlı görülmelerini geri yükler (fail-open)."""
        loader = getattr(self.store, "recent_sightings_sync", None)
        if loader is None:
            return
        try:
            rows = await asyncio.to_thread(loader)
            logger.info("[newsfeed] karne geri yüklendi: %d yarış", self.board.restore(rows))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[newsfeed] karne geri yüklenemedi: %s", exc)

    async def stop(self) -> None:
        """Döngüleri durdurur ve kalanı yazar."""
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        await self.store.flush(time.monotonic())
        if self._session:
            await self._session.close()
            self._session = None

    # ── Okuma ─────────────────────────────────────────────────────────────────
    def latest(self, symbol: str | None = None, min_relevance: int = RELEVANCE_MIN, limit: int = 100,
               include_opinion: bool = False) -> list[dict[str, Any]]:
        """En yeni hikâyeler; seed kayıtları dahil (panel açılışta boş kalmasın), `seeded` işaretli."""
        now = time.time()
        out: list[dict[str, Any]] = []
        for row in self.buffer:
            if row["relevance"] < min_relevance or (row["is_opinion"] and not include_opinion):
                continue
            if symbol and symbol not in row["symbols"]:
                continue
            if row.get("seeded") and now - row["display_ts"] > SEEDED_MAX_AGE_S:
                continue
            out.append(row)
        out.sort(key=lambda r: r["display_ts"], reverse=True)
        return out[:limit]

    def status(self) -> dict[str, Any]:
        """Motorun sağlık özeti."""
        rows = self.board.table()
        now = time.time()
        alive = sum(1 for r in rows if r["last_ok_ago_s"] is not None and r["last_ok_ago_s"] < 300)
        ms = sorted(self.ingest_ms)
        return {
            "running": bool(self._tasks), "uptime_s": round(now - self.started_ts) if self.started_ts else 0,
            "sources_total": len(rows), "sources_alive": alive, "adaptive": self.adaptive,
            "stories_in_buffer": len(self.buffer), "in_release_window": in_release_window(now),
            "ingest_p50_ms": round(ms[len(ms) // 2], 2) if ms else None, "subscribers": len(self._subs),
            "store": self.store.stats, "inactive_sources": inactive_sources(),
        }


_engine: NewsEngine | None = None


def get_engine() -> NewsEngine:
    """Süreç başına tek motor."""
    global _engine
    if _engine is None:
        _engine = NewsEngine()
    return _engine


async def start_newsfeed() -> bool:
    """`NEWSFEED_ENABLED=1` ise motoru başlatır. Tek yazar politikası: kutu ve yerel kopyada kapalı tutulur."""
    if os.getenv("NEWSFEED_ENABLED", "0") != "1":
        logger.info("[newsfeed] kapalı (NEWSFEED_ENABLED!=1)")
        return False
    await get_engine().start()
    return True


async def stop_newsfeed() -> None:
    """Uygulama kapanışında çağrılır."""
    if _engine is not None:
        await _engine.stop()
