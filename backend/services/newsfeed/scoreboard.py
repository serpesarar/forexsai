"""Kaynak hız karnesi: 'hangisi önce getiriyor' ölçümü ve buna göre sorgu aralığı.

Ölçüm kuralları (hepsi sonucu bozan gerçek tuzaklar):
- Yarışa yalnız en az iki kaynağın, ikisi de CANLI (ilk yükleme değil) gördüğü hikâyeler girer. İlk sorguda gelen eski
  kayıtların görülme zamanı anlamsızdır (`seeded`).
- Bir kaynağın gecikmesi kendi sorgu aralığını da içerir. `raw` sistemin gerçekte yaşadığı farktır; `adj` ortalama sorgu
  beklemesini (aralık / 2) çıkarır ve kaynağın kendi hızına yaklaşır. Kıyasta adj kullanılır.
- Geri besleme: hızlı sorgulanan kaynak hızlı görünür. Bu yüzden öncelik `adj` üzerinden hesaplanır, her kaynak en az
  `MIN_SAMPLES` yarış görmeden tabana dokunulmaz ve hiçbir kaynak `MAX_INTERVAL_S` üstüne çıkmaz (ölçüm sürer).
"""
from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from services.newsfeed.catalog import SourceDef
from services.newsfeed.dedup import Story

ROLLING_MAX = 5000
ROLLING_SECONDS = 7 * 86400
MIN_SAMPLES = 30
MIN_INTERVAL_S = 15.0
MAX_INTERVAL_S = 180.0
BURST_INTERVAL_S = 8.0
SCORE_CACHE_S = 30.0
_SPEEDUP = 0.5     # en iyi kaynak: taban × 0,5
_SLOWDOWN = 2.0    # en kötü kaynak: taban × 2


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


@dataclass
class SourceHealth:
    """Tek kaynağın anlık çalışma sayaçları."""

    polls: int = 0
    errors: int = 0
    not_modified: int = 0
    items_new: int = 0
    last_ok_ts: float | None = None
    last_error: str | None = None
    last_item_ts: float | None = None
    backoff_until_ts: float = 0.0
    consecutive_errors: int = 0
    fetch_ms: deque = field(default_factory=lambda: deque(maxlen=200))


class Scoreboard:
    """Yarış ölçümlerini biriktirir, kaynak başına karne ve sorgu aralığı üretir."""

    def __init__(self, sources: list[SourceDef]) -> None:
        self.sources = {s.id: s for s in sources}
        self.health = {s.id: SourceHealth() for s in sources}
        self._races: dict[str, deque] = {s.id: deque(maxlen=ROLLING_MAX) for s in sources}
        self._pub_lag: dict[str, deque] = {s.id: deque(maxlen=ROLLING_MAX) for s in sources}
        self._cache: tuple[float, list[dict]] | None = None

    def record_publish_lag(self, source_id: str, lag_s: float) -> None:
        """Yayın zamanı → ilk görülme farkı (zaman damgası güvenilir kaynaklar için anlamlı)."""
        self._pub_lag[source_id].append((time.time(), lag_s))

    def record_story_join(self, story: Story, source_id: str) -> None:
        """Hikâyeye ikinci/sonraki kaynak katıldığında iki tarafın yarış kaydını yazar."""
        joined = story.sightings[source_id]
        if joined.seeded:
            return
        live = {sid: s for sid, s in story.sightings.items() if not s.seeded}
        if len(live) < 2:
            return
        first_ts = min(s.first_seen_ts for s in live.values())
        first_sid = min(live, key=lambda k: live[k].first_seen_ts)
        if len(live) == 2:   # ilk gören ancak ikinci kaynak gelince yarışa girer
            head = live[first_sid]
            self._races[first_sid].append((head.first_seen_ts, 0.0, 0.0, True))
        if source_id != first_sid:
            raw = joined.first_seen_ts - first_ts
            adj = max(0.0, raw - joined.poll_interval_s / 2 + live[first_sid].poll_interval_s / 2)
            self._races[source_id].append((joined.first_seen_ts, raw, adj, False))

    def restore(self, rows: list[dict]) -> int:
        """`news_sightings` satırlarından yarış kayıtlarını yeniden kurar; kaç yarış kaydı eklendiğini döndürür."""
        by_story: dict[str, list[dict]] = {}
        for row in rows:
            if row.get("source_id") in self._races and row.get("first_seen_at"):
                by_story.setdefault(row["story_id"], []).append(row)
        added = 0
        for group in by_story.values():
            if len(group) < 2:
                continue
            parsed = [(datetime.fromisoformat(g["first_seen_at"]).timestamp(), g) for g in group]
            parsed.sort(key=lambda p: p[0])
            t0, head = parsed[0]
            head_poll = float(head.get("poll_interval_s") or 0)
            self._races[head["source_id"]].append((t0, 0.0, 0.0, True))
            for ts, g in parsed[1:]:
                raw = ts - t0
                adj = max(0.0, raw - float(g.get("poll_interval_s") or 0) / 2 + head_poll / 2)
                self._races[g["source_id"]].append((ts, raw, adj, False))
            added += len(parsed)
        return added

    def _source_row(self, sid: str, now: float) -> dict:
        s, h = self.sources[sid], self.health[sid]
        races = [r for r in self._races[sid] if now - r[0] <= ROLLING_SECONDS]
        raw, adj = [r[1] for r in races], [r[2] for r in races]
        pub = [p[1] for p in self._pub_lag[sid] if now - p[0] <= ROLLING_SECONDS]
        wins = sum(1 for r in races if r[3])
        fm = list(h.fetch_ms)
        return {
            "id": sid, "name": s.name, "tier": s.tier, "kind": s.kind, "repo": s.repo, "unofficial": s.unofficial,
            "races": len(races), "first_count": wins, "first_rate": round(wins / len(races), 3) if races else None,
            "lag_raw_p50_s": round(statistics.median(raw), 1) if raw else None,
            "lag_raw_p95_s": round(_pct(raw, 0.95), 1) if raw else None,
            "lag_adj_p50_s": round(statistics.median(adj), 1) if adj else None,
            "publish_lag_p50_s": round(statistics.median(pub), 1) if pub else None,
            "polls": h.polls, "errors": h.errors, "not_modified": h.not_modified, "items_new": h.items_new,
            "error_rate": round(h.errors / h.polls, 3) if h.polls else None,
            "fetch_p50_ms": round(statistics.median(fm)) if fm else None,
            "last_ok_ago_s": round(now - h.last_ok_ts) if h.last_ok_ts else None,
            "last_item_ago_s": round(now - h.last_item_ts) if h.last_item_ts else None,
            "last_error": h.last_error,
            "interval_s": round(self.interval_for(sid), 1) if s.base_interval_s else None,
        }

    def table(self) -> list[dict]:
        """Karne: önce çok yarış görmüş ve önde gelenler."""
        now = time.time()
        if self._cache and now - self._cache[0] < SCORE_CACHE_S:
            return self._cache[1]
        rows = [self._source_row(sid, now) for sid in self.sources]
        rows.sort(key=lambda r: (r["races"] < MIN_SAMPLES, r["lag_adj_p50_s"] if r["lag_adj_p50_s"] is not None else 1e9,
                                 -(r["first_rate"] or 0)))
        self._cache = (now, rows)
        return rows

    def _rank_factor(self, sid: str) -> float:
        """Yeterli yarış görmüş kaynaklar arasında adj p50 sırasına göre 0,5×…2× çarpanı."""
        now = time.time()
        scored = []
        for key, rows in self._races.items():
            adj = [r[2] for r in rows if now - r[0] <= ROLLING_SECONDS]
            if len(adj) >= MIN_SAMPLES:
                scored.append((statistics.median(adj), key))
        if len(scored) < 3 or sid not in {k for _, k in scored}:
            return 1.0
        scored.sort()
        pos = [k for _, k in scored].index(sid) / (len(scored) - 1)
        return _SPEEDUP + (_SLOWDOWN - _SPEEDUP) * pos

    def interval_for(self, sid: str, burst: bool = False, adaptive: bool = True) -> float:
        """Sonraki sorguya kadar beklenecek süre (s). Veri yayın penceresinde resmi + squawk hızlanır."""
        src = self.sources[sid]
        if burst and src.tier in ("official", "squawk"):
            return BURST_INTERVAL_S
        factor = self._rank_factor(sid) if adaptive else 1.0
        return max(MIN_INTERVAL_S, min(MAX_INTERVAL_S, src.base_interval_s * factor))
