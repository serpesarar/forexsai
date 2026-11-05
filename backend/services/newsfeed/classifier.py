"""Kural tabanlı anlık sınıflandırma: olay türü, ilgili semboller, aciliyet, teyit durumu.

Yapay zekâ beklemez (mikrosaniye); bu yüzden başlık hiç gecikmeden yayınlanır. Bilinçli olarak YÖN (BUY/SELL) üretmez:
"tarife arttı" cümlesinin NDX ve altın üzerindeki yönü kanıtlanmadı; yön iddiası ancak olay çalışması geçerse eklenir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

ALL_SYMBOLS = ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX")
_NDX = "NDX.INDX"
_DAX = "GDAXI.INDX"
_XAU = "XAUUSD"
_OIL = "USOIL.FOREX"


def _rx(*words: str) -> re.Pattern[str]:
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.I)


# (olay türü, desen, etkilenen semboller, taban ilgi puanı). Sıra önemlidir: ilk eşleşme türü belirler.
_RULES: tuple[tuple[str, re.Pattern[str], tuple[str, ...], int], ...] = (
    ("cb_decision", _rx(r"rate (?:decision|cut|hike|hold)s?", r"(?:cuts?|raises?|holds?|keeps?) (?:\w+ )?rates?",
                        "fomc statement", "monetary policy decision",
                        # "baz puan" tek başına faiz kararı değildir ("endeksi 460 baz puan geçti"): banka/faiz sözcüğü şart
                        r"(?:fed|fomc|ecb|boe|boj|central bank|rates?)\b.{0,60}\b(?:\d+ ?bps?|basis points?)"), ALL_SYMBOLS, 90),
    ("cb_speak", _rx("powell", "fomc", "federal reserve", "fed chair", r"fed'?s \w+", "waller", "williams", "jefferson",
                     "bowman", "goolsbee", "kashkari", "bostic", "daly", "hammack", "logan", "lagarde", "ecb", "schnabel",
                     "nagel", "bank of japan", "boj", "ueda", "bank of england", "boe", "bailey", "hawkish", "dovish"),
     ALL_SYMBOLS, 70),
    ("macro_print", _rx("cpi", "ppi", "pce", "nonfarm", "non-farm", "nfp", "payrolls?", "jobless claims", "unemployment rate",
                        "gdp", "ism", "pmi", "retail sales", "durable goods", "consumer confidence", "umich", "jolts",
                        "adp", "ifo", "zew", "inflation"), ALL_SYMBOLS, 75),
    ("tariff_trade", _rx("tariffs?", "trade (?:war|deal|talks?)", "export controls?", "chip curbs?", "sanctions?",
                         "section 232", "section 301", "customs duty"), (_NDX, _DAX, _XAU, _OIL), 75),
    ("energy", _rx("opec", "opec\\+", "crude", "wti", "brent", "oil (?:price|output|supply|production|inventor\\w+)",
                   "eia", "api inventor\\w+", "strategic petroleum", "spr", "refiner\\w*", "natural gas", "lng",
                   "strait of hormuz", "barrels?"), (_OIL,), 70),
    ("metals", _rx("gold", "bullion", "xau", "xauusd", "precious metals?", "silver", "comex", "spdr gold"), (_XAU,), 65),
    ("geopolitics", _rx("war", "missiles?", "airstrikes?", "strikes? on", "invasion", "ceasefire", "truce", "nuclear",
                        "attack(?:s|ed)?", "military", "troops", "hezbollah", "hamas", "houthis?", "iran", "israel", "gaza",
                        "ukraine", "russia", "putin", "zelensky", "taiwan", "north korea", "pentagon"),
     (_XAU, _OIL, _NDX, _DAX), 65),
    ("politics_us", _rx("trump", "white house", "treasury secretary", "bessent", "government shutdown", "debt ceiling",
                        "executive order", "congress", "senate"), (_NDX, _XAU, _OIL), 45),   # genel siyaset gürültülü: resmi/squawk kaynak ister
    ("big_tech", _rx("nvidia", "nvda", "apple", "aapl", "microsoft", "msft", "alphabet", "google", "amazon", "amzn", "meta",
                     "tesla", "tsla", "broadcom", "avgo", "netflix", "amd", "tsmc", "openai"), (_NDX,), 55),
    ("germany_eu", _rx("dax", "germany", "german", "bundesbank", "merz", "euro ?zone", "siemens", "sap", "volkswagen",
                       "allianz"), (_DAX,), 55),
    ("market_move", _rx("nasdaq", "s&p", "s&p 500", "dow", "futures", "stocks?", "wall street", "yields?", "treasur(?:y|ies)",
                        "dollar", "dxy", "vix", "selloff", "sell-off", "rally", "plunge\\w*", "surge\\w*"),
     (_NDX, _DAX), 40),
)
_BREAKING = _rx("breaking", "urgent", "flash", "just in", "alert", "emergency")
_HEDGED = _rx("sources?", "reportedly", "rumou?rs?", "said to", "according to", "people familiar", "may", "could",
              "considering", "weighs?", "mulls?", "expected", "plans? to", "in talks")
_OPINION = _rx("opinion", "analysis", "explainer", "podcast", "what to know", "here's why", "here's what", "best stocks",
               "should you", "\\d+ stocks", "top \\d+", "review", "recap", "preview", "week ahead", "morning bid",
               "technical analysis", "price forecast", "price analysis", "elliott wave")
_HEADLINE_NUM = re.compile(r"\d")
_CAPS_MIN_LEN = 12
_CAPS_RATIO = 0.7
_TIER_BONUS = {"official": 15, "squawk": 10, "wire": 8, "media": 0, "aggregator": -5}
RELEVANCE_MIN = 50


@dataclass(frozen=True)
class Classification:
    event_type: str
    symbols: tuple[str, ...]
    urgency: str          # breaking | high | medium | low
    relevance: int        # 0-100
    confirmation: str     # official | reported | unconfirmed
    is_opinion: bool


def _is_caps(title: str) -> bool:
    letters = [c for c in title if c.isalpha()]
    return len(letters) >= _CAPS_MIN_LEN and sum(c.isupper() for c in letters) / len(letters) >= _CAPS_RATIO


def _urgency(relevance: int, title: str, is_opinion: bool) -> str:
    if is_opinion:
        return "low"
    if relevance >= 85 and (_BREAKING.search(title) or _is_caps(title)):
        return "breaking"
    if relevance >= 75:
        return "high"
    return "medium" if relevance >= RELEVANCE_MIN else "low"


def classify(title: str, tier: str) -> Classification:
    """Başlığı olay türü + sembol + ilgi puanına çevirir; yön üretmez."""
    text = title or ""
    event, syms, base = "other", (), 15
    for name, rx, s, b in _RULES:
        if rx.search(text):
            event, syms, base = name, s, b
            break
    is_opinion = bool(_OPINION.search(text))
    relevance = base + _TIER_BONUS.get(tier, 0)
    if _BREAKING.search(text):
        relevance += 10
    if event != "other" and _HEADLINE_NUM.search(text):
        relevance += 5
    if is_opinion:
        relevance -= 35
    relevance = max(0, min(100, relevance))
    confirmation = "official" if tier == "official" else "unconfirmed" if _HEDGED.search(text) else "reported"
    return Classification(event, syms, _urgency(relevance, text, is_opinion), relevance, confirmation, is_opinion)
