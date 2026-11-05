"""Başlık kümeleme: aynı haberi farklı kaynaklardan tek 'hikâye'de toplar; ilk gören kazanır.

Eşleştirme fikri `chinedumsunday/fx-news-desk` (MIT) `utils/squawk_dedup.py`'den uyarlandı: normalize edilmiş token
kapsama oranı. Farklar: disk yerine bellek, kaynak başına ayrı görülme zamanı (yarış ölçümü bunun üstüne kurulu)
ve durak sözcüklerin çıkarılması (farklı yayın evlerinin yeniden yazdığı başlıklarda sahte eşleşmeyi azaltır).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

WINDOW_S = 45 * 60
MIN_TOKENS = 5
SIMILARITY = 0.8
_STOP = frozenset(
    "a an and are as at be been but by for from has have he her his in is it its of on or she that the their they this "
    "to was were will with would after amid over under says said say new".split()
)
_PREFIX = re.compile(r"\b(breaking|just in|watch|alert|update|exclusive|urgent|flash)\b[:\s-]*", re.I)
_URL = re.compile(r"https?://\S+")
_NON = re.compile(r"[^a-z0-9%$. ]")
_DOT = re.compile(r"(?<!\d)\.(?!\d)")
_WS = re.compile(r"\s+")


def normalize(title: str) -> str:
    """Başlığı karşılaştırılabilir küçük harf metne indirger; sayı, % ve $ korunur."""
    t = _URL.sub(" ", (title or "").lower())
    t = _PREFIX.sub(" ", t)
    t = _DOT.sub(" ", _NON.sub(" ", t))
    return _WS.sub(" ", t).strip()


def tokens(norm: str) -> frozenset[str]:
    """Durak sözcükleri atılmış token kümesi."""
    return frozenset(w for w in norm.split() if w not in _STOP)


def is_same_story(a_norm: str, a_tok: frozenset[str], b_norm: str, b_tok: frozenset[str]) -> bool:
    """Birebir aynı normal metin ya da küçük kümenin ≥ %80'i diğerinde (en az 5 token)."""
    if a_norm == b_norm:
        return True
    small = min(len(a_tok), len(b_tok))
    if small < MIN_TOKENS:
        return False
    return len(a_tok & b_tok) / small >= SIMILARITY


@dataclass
class Sighting:
    """Bir kaynağın bir hikâyeyi ilk gördüğü an."""

    source_id: str
    first_seen_ts: float
    published_ts: float | None
    url: str
    poll_interval_s: float
    seeded: bool


@dataclass
class Story:
    """Aynı olayı anlatan başlıklar kümesi."""

    id: str
    headline: str
    norm: str
    toks: frozenset[str]
    first_seen_ts: float
    first_source: str
    url: str
    sightings: dict[str, Sighting] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


def story_id(norm: str, first_seen_ts: float) -> str:
    """Süreçler arası kararlı olması gerekmez; tek yazar politikası var."""
    return hashlib.sha1(f"{norm}|{int(first_seen_ts)}".encode()).hexdigest()[:24]


class StoryIndex:
    """Son WINDOW_S içindeki hikâyelerin bellek dizini."""

    def __init__(self, window_s: int = WINDOW_S) -> None:
        self.window_s = window_s
        self._stories: list[Story] = []

    def purge(self, now_ts: float) -> None:
        cutoff = now_ts - self.window_s
        if self._stories and self._stories[0].first_seen_ts < cutoff:
            self._stories = [s for s in self._stories if s.first_seen_ts >= cutoff]

    def find(self, norm: str, toks: frozenset[str]) -> Story | None:
        """En yeniden eskiye tarar: aynı başlık tekrar ederse en yakın hikâyeye bağlanır."""
        for st in reversed(self._stories):
            if is_same_story(norm, toks, st.norm, st.toks):
                return st
        return None

    def add(self, story: Story) -> None:
        self._stories.append(story)

    def __len__(self) -> int:
        return len(self._stories)
