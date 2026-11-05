"""Haber kaynak kataloğu — hangi kaynak, nereden geldi, ne sıklıkla, hangi anahtarla.

Liste elle seçilmiş tahmin değil: `research/github_haber_sekil_20261104/degerlendirme/kaynak_yoklama.py` 109 adayı
2026-11-04'te yokladı; yanıt veren + taze + piyasa ilgili olanlar buraya girdi. Eski `rss_aggregator` kaynaklarından
reuters/zerohedge/marketwatch-realtime/kitco ölü çıktığı için alınmadı.

`repo` alanı adayın hangi GitHub deposundan geldiğini söyler (karne bu alanla kaynak ölçümünü repoya bağlar).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDef:
    """Tek bir haber kaynağının tanımı."""

    id: str
    name: str
    kind: str                     # rss | telegram | truth | finnhub | alpaca_ws | benzinga_ws | ws_1322
    url: str
    tier: str                     # official | squawk | wire | media | aggregator
    repo: str                     # kaynağın geldiği depo
    base_interval_s: int = 60
    needs_env: tuple[str, ...] = ()
    unofficial: bool = False      # kaynağın resmi/izinli bir akışı değil (sayfa ayrıştırma vb.)


FX_DESK = "chinedumsunday/fx-news-desk"
FIN_MON = "liang9733/finance_monitor"
TRUTHB = "w2rc/truthbrush"
TELETHON_ALT = "LonamiWebs/Telethon (alternatif: t.me/s açık önizleme)"
ALPACA = "alpacahq/alpaca-py"
BENZINGA = "Benzinga/benzinga-python-client"
FINNHUB = "Finnhub-Stock-API/finnhub-python"
R1322 = "1322monitors/1322-python"
OWN = "ForexSAI"

_CNBC = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id="

SOURCES: tuple[SourceDef, ...] = (
    # ── Squawk: en sık yayın (yoklama: kayıt arası medyan 1–2 dk) ────────────
    SourceDef("financialjuice_rss", "FinancialJuice RSS", "rss", "https://www.financialjuice.com/feed.ashx?xy=rss",
              "squawk", FX_DESK, 60),   # 20 sn sorguda HTTP 429 (2026-11-05 pilot)
    SourceDef("financialjuice_tg", "FinancialJuice Telegram", "telegram", "https://t.me/s/financialjuice",
              "squawk", TELETHON_ALT, 20, unofficial=True),
    SourceDef("marketfeed_tg", "Market Feed Telegram", "telegram", "https://t.me/s/marketfeed",
              "squawk", TELETHON_ALT, 20, unofficial=True),
    SourceDef("walterbloomberg_tg", "Walter Bloomberg Telegram", "telegram", "https://t.me/s/WalterBloomberg",
              "squawk", TELETHON_ALT, 20, unofficial=True),
    SourceDef("seekingalpha_currents", "Seeking Alpha Market Currents", "rss",
              "https://seekingalpha.com/market_currents.xml", "squawk", FIN_MON, 30),
    SourceDef("investinglive", "investingLive (eski ForexLive)", "rss", "https://www.investinglive.com/feed/",
              "squawk", OWN, 30),
    # ── Doğrudan kişi hattı ──────────────────────────────────────────────────
    SourceDef("truth_trump", "Trump — Truth Social (doğrudan)", "truth",
              "https://truthsocial.com/api/v1/accounts/107780257626128497/statuses?limit=10&exclude_replies=true",
              "official", TRUTHB, 60, unofficial=True),   # 20 sn'de HTTP 429; bulut IP'lerinden engellenebilir, yedek: trumpstruth_rss
    SourceDef("trumpstruth_rss", "trumpstruth.org RSS (üçüncü taraf)", "rss", "https://www.trumpstruth.org/feed",
              "aggregator", TRUTHB, 60, unofficial=True),
    # ── Resmi kurumlar ───────────────────────────────────────────────────────
    SourceDef("fed_press", "Federal Reserve basın", "rss", "https://www.federalreserve.gov/feeds/press_all.xml",
              "official", FX_DESK, 60),
    SourceDef("fed_monetary", "Federal Reserve para politikası", "rss",
              "https://www.federalreserve.gov/feeds/press_monetary.xml", "official", FX_DESK, 60),
    SourceDef("fed_speeches", "Federal Reserve konuşmalar", "rss",
              "https://www.federalreserve.gov/feeds/speeches_and_testimony.xml", "official", FX_DESK, 120),
    SourceDef("ecb_press", "ECB basın", "rss", "https://www.ecb.europa.eu/rss/press.html", "official", FX_DESK, 60),
    SourceDef("boe_news", "Bank of England", "rss", "https://www.bankofengland.co.uk/rss/news", "official", FX_DESK, 120),
    SourceDef("boj_news", "Bank of Japan", "rss", "https://www.boj.or.jp/en/rss/whatsnew.xml", "official", FX_DESK, 120),
    SourceDef("whitehouse_news", "Beyaz Saray haberler", "rss", "https://www.whitehouse.gov/news/feed/",
              "official", OWN, 60),
    SourceDef("whitehouse_actions", "Beyaz Saray başkanlık kararları", "rss",
              "https://www.whitehouse.gov/presidential-actions/feed/", "official", OWN, 60),
    SourceDef("eia_press", "EIA basın", "rss", "https://www.eia.gov/rss/press_rss.xml", "official", OWN, 120),
    # ── Ana akım finans ──────────────────────────────────────────────────────
    SourceDef("cnbc_top", "CNBC Top News", "rss", f"{_CNBC}100003114", "media", FX_DESK, 30),
    SourceDef("cnbc_markets", "CNBC Markets", "rss", f"{_CNBC}20910258", "media", FIN_MON, 45),
    SourceDef("cnbc_world", "CNBC World", "rss", f"{_CNBC}100727362", "media", FIN_MON, 60),
    SourceDef("bloomberg_markets", "Bloomberg Markets", "rss", "https://feeds.bloomberg.com/markets/news.rss",
              "media", FIN_MON, 30),
    SourceDef("investing_news", "Investing.com haberler", "rss", "https://www.investing.com/rss/news.rss",
              "media", FIN_MON, 30),
    SourceDef("investing_stocks", "Investing.com borsa", "rss", "https://www.investing.com/rss/news_25.rss",
              "media", OWN, 45),
    SourceDef("investing_macro", "Investing.com makro gösterge", "rss", "https://www.investing.com/rss/news_95.rss",
              "media", OWN, 45),
    SourceDef("investing_commod", "Investing.com emtia", "rss", "https://www.investing.com/rss/news_11.rss",
              "media", OWN, 45),
    SourceDef("fxstreet", "FXStreet", "rss", "https://www.fxstreet.com/rss/news", "media", OWN, 60),
    SourceDef("marketwatch_top", "MarketWatch", "rss", "https://feeds.marketwatch.com/marketwatch/topstories",
              "media", FIN_MON, 60),
    SourceDef("nasdaq_markets", "Nasdaq.com", "rss", "https://www.nasdaq.com/feed/rssoutbound?category=Markets",
              "media", FX_DESK, 60),
    SourceDef("oilprice", "OilPrice.com", "rss", "https://oilprice.com/rss/main", "media", FIN_MON, 60),
    SourceDef("mining_com", "Mining.com", "rss", "https://www.mining.com/feed/", "media", FIN_MON, 120),
    SourceDef("thehill_economy", "The Hill ekonomi", "rss", "https://thehill.com/category/economy/feed/",
              "media", FX_DESK, 60),
    # ── Jeopolitik ───────────────────────────────────────────────────────────
    SourceDef("disclosetv_tg", "Disclose.tv Telegram", "telegram", "https://t.me/s/disclosetv",
              "squawk", TELETHON_ALT, 30, unofficial=True),
    SourceDef("aljazeera", "Al Jazeera", "rss", "https://www.aljazeera.com/xml/rss/all.xml", "media", FX_DESK, 60),
    SourceDef("guardian_world", "Guardian World", "rss", "https://www.theguardian.com/world/rss", "media", FIN_MON, 120),
    SourceDef("bbc_world", "BBC World", "rss", "https://feeds.bbci.co.uk/news/world/rss.xml", "media", FIN_MON, 120),
    SourceDef("fox_latest", "Fox News", "rss", "https://moxie.foxnews.com/google-publisher/latest.xml",
              "media", FX_DESK, 120),
    # ── Toplayıcı ────────────────────────────────────────────────────────────
    SourceDef("google_news_macro", "Google News makro sorgu", "rss",
              "https://news.google.com/rss/search?q=fed+OR+tariff+OR+opec+OR+nasdaq+OR+gold+when:1h&hl=en-US&gl=US&ceid=US:en",
              "aggregator", FIN_MON, 90),
    # ── Anahtarlı sağlayıcılar: anahtar yoksa hiç başlamaz, gerçek bağlantıları henüz doğrulanmadı ──
    SourceDef("finnhub_general", "Finnhub genel haber", "finnhub", "https://finnhub.io/api/v1/news?category=general",
              "wire", FINNHUB, 30, needs_env=("FINNHUB_API_KEY",)),
    SourceDef("alpaca_news", "Alpaca News WebSocket", "alpaca_ws", "wss://stream.data.alpaca.markets/v1beta1/news",
              "wire", ALPACA, 0, needs_env=("ALPACA_API_KEY", "ALPACA_SECRET_KEY")),
    SourceDef("benzinga_ws", "Benzinga News Stream", "benzinga_ws", "wss://api.benzinga.com/api/v1/news/stream",
              "wire", BENZINGA, 0, needs_env=("BENZINGA_API_KEY",)),
)


def active_sources() -> list[SourceDef]:
    """Anahtarı tanımlı olan ve env ile kapatılmamış kaynakları döndürür."""
    disabled = {s.strip() for s in os.getenv("NEWSFEED_DISABLED_SOURCES", "").split(",") if s.strip()}
    return [
        s for s in SOURCES
        if s.id not in disabled and all(os.getenv(k, "").strip() for k in s.needs_env)
    ]


def inactive_sources() -> list[dict[str, str]]:
    """Başlatılmayan kaynaklar ve nedenleri (panel 'neden kapalı' sütunu için)."""
    disabled = {s.strip() for s in os.getenv("NEWSFEED_DISABLED_SOURCES", "").split(",") if s.strip()}
    out: list[dict[str, str]] = []
    for s in SOURCES:
        missing = [k for k in s.needs_env if not os.getenv(k, "").strip()]
        if s.id in disabled:
            out.append({"id": s.id, "name": s.name, "reason": "env ile kapalı", "repo": s.repo})
        elif missing:
            out.append({"id": s.id, "name": s.name, "reason": "anahtar yok: " + ", ".join(missing), "repo": s.repo})
    return out
