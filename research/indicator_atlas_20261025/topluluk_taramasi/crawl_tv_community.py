"""TradingView Public Library topluluk script'lerini tag akışlarından topla.

Her tag sayfası (https://www.tradingview.com/scripts/<tag>/page-N/) 24 script'i gömülü JSON
(`prs.init-data+json` → ideas.data.items) olarak taşır; akış başına en fazla 1.000 kayıt döner.
Yalnız kamuya açık liste sayfaları okunur (giriş yok, script kodu indirilmez).

Kullanım:
    python3 crawl_tv_community.py probe            # tag başına toplam
    python3 crawl_tv_community.py crawl [maxpage]  # tüm sayfalar → data/scripts.jsonl
"""
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://www.tradingview.com/scripts/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
DATA = Path(__file__).parent / "data"
PER_PAGE = 24
FEED_CAP = 1000
WORKERS = 4
DELAY_S = 0.35
INIT_RE = re.compile(r'<script type="application/prs\.init-data\+json">(.*?)</script>', re.S)

TAGS = """
trendanalysis oscillators oscillator volatility movingaverages movingaverage momentum volume bandsandchannels
candlestickanalysis chartpatterns pivotpoints supportandresistance breadthindicators cycleanalysis cycles forecasting
statistics centeredoscillators nonlinear multitimeframe signal strategy backtesting machinelearning ai smartmoneyconcepts
smc ict orderblocks orderblock fairvaluegap fvg liquidity marketstructure wyckoff elliottwave harmonicpatterns harmonic
fibonacci gann volumeprofile marketprofile orderflow delta cvd vwap supertrend ichimoku rsi macd stochastic bollingerbands
atr adx cci ema sma hma kama alma parabolicsar keltnerchannel keltnerchannels donchian donchianchannels squeeze ttmsqueeze
wavetrend qqe halftrend utbot ssl rangefilter nadarayawatson kernelregression lorentzian knn kalman ehlers fisher
fishertransform schaff heikinashi renko zigzag divergence divergences regression linearregression trendlines breakout
scalping sessions openingrange killzones seasonality correlation vix gold xauusd nasdaq nasdaq100 dax oil crude futures
forex meanreversion library trailingstop chandelier pivots williamsr obv mfi cmf vwma tsi trix aroon vortex dmi
ultimateoscillator awesomeoscillator coppock kst cmo stochasticrsi ribbon cloud neuralnetwork zscore entropy hurst
fractal fractals pinescript volumedelta footprint tpo gaps candlestick patterns pricaction priceaction
""".split()

# 2. aşama: büyük tag akışları en yeni 1.000 kayıtla sınırlı → eski/ünlü script'ler için
# yazar ve isim aramaları + Editors' picks arşivi ("search/<q>" tag gibi sayfalanır).
AUTHORS = """
lazybear chrismoody luxalgo jdehorty kivancozbilgic everget loxx donovanwall hpotter alexgrover trendoscope
heWhoMustNotBeNamed ricardosantos quantnomad lonesometheblue bigbeluga chartprime algoalpha zeiierman ualgo bjorgum
dgtrd fluxchart quantvue projectsyndicate daveatt makit0 colinmck backtestrookies jason5480 peacefullizard50262
""".split()
NAMES = [
    "squeeze momentum", "wavetrend", "market cipher", "vumanchu", "ut bot", "lorentzian", "nadaraya", "halftrend",
    "qqe mod", "ssl hybrid", "chandelier exit", "range filter", "hull suite", "williams vix fix", "coral trend",
    "smart money concepts", "trendlines with breaks", "liquidity swings", "support resistance channels",
    "order block finder", "pivot point supertrend", "machine learning", "kernel regression", "volume profile",
    "zigzag", "elliott wave", "wyckoff", "sniper", "impulse macd", "insync", "laguerre", "mesa adaptive",
    "fisher transform", "schaff trend cycle", "kalman", "tdi traders dynamic index", "td sequential", "demark",
    "andean oscillator", "chop zone", "keltner", "ichimoku", "heikin ashi", "renko", "gann", "fibonacci",
    "anchored vwap", "footprint", "cvd", "market profile", "session", "killzone", "silver bullet", "breaker block",
]
SEARCHES = ["editors-picks"] + [f"search/{a}" for a in AUTHORS] + \
           [f"search/{urllib.request.quote(n)}" for n in NAMES]


def fetch(url: str, tries: int = 3) -> str | None:
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # 404 = tag yok, diğerleri yeniden dene
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(2 * (i + 1))
    return None


def feed(html: str | None) -> dict | None:
    if not html:
        return None
    for blob in INIT_RE.findall(html):
        if '"ideas"' not in blob:
            continue
        found = _find_ideas(json.loads(blob))
        if found is not None:
            return found
    return None


def _find_ideas(node):
    """Gömülü JSON'da `ideas.data` (total + items) düğümünü derinlemesine ara."""
    if isinstance(node, dict):
        ideas = node.get("ideas")
        if isinstance(ideas, dict) and isinstance(ideas.get("data"), dict) and "items" in ideas["data"]:
            return ideas["data"]
        children = node.values()
    elif isinstance(node, list):
        children = node
    else:
        return None
    for child in children:
        found = _find_ideas(child)
        if found is not None:
            return found
    return None


def slim(it: dict, tag: str) -> dict:
    return {
        "id": it.get("id"), "name": it.get("name"), "desc": (it.get("description") or "")[:600],
        "created_at": it.get("created_at"), "boosts": it.get("likes_count"), "comments": it.get("comments_count"),
        "type": it.get("script_type"), "access": it.get("script_access"), "picked": it.get("is_picked"),
        "author": (it.get("user") or {}).get("username"), "url": it.get("chart_url"),
        "symbol": (it.get("symbol") or {}).get("name"), "tag": tag,
    }


def page_url(tag: str, n: int) -> str:
    return f"{BASE}{tag}/" if n == 1 else f"{BASE}{tag}/page-{n}/"


def probe(feeds: list[str], totals_name: str) -> dict:
    def one(tag):
        time.sleep(DELAY_S)
        d = feed(fetch(page_url(tag, 1)))
        return tag, (d or {}).get("total", 0)
    with ThreadPoolExecutor(WORKERS) as ex:
        res = dict(ex.map(one, feeds))
    DATA.mkdir(exist_ok=True)
    (DATA / totals_name).write_text(json.dumps(res, indent=1))
    return res


def crawl(max_page: int, totals_name: str = "tag_totals.json", out_name: str = "scripts.jsonl") -> None:
    totals = json.loads((DATA / totals_name).read_text())
    jobs = [(t, n) for t, tot in totals.items() if tot
            for n in range(1, min(max_page, -(-min(tot, FEED_CAP) // PER_PAGE)) + 1)]
    print(f"{len(jobs)} sayfa")
    out = (DATA / out_name).open("w")

    def one(job):
        time.sleep(DELAY_S)
        tag, n = job
        d = feed(fetch(page_url(tag, n)))
        return [slim(it, tag) for it in (d or {}).get("items", [])]

    done = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for rows in ex.map(one, jobs):
            for r in rows:
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
            done += 1
            if done % 200 == 0:
                print(done, "sayfa", flush=True)
    out.close()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode in ("probe", "probe-search"):
        feeds, name = (TAGS, "tag_totals.json") if mode == "probe" else (SEARCHES, "search_totals.json")
        r = probe(feeds, name)
        print(sum(1 for v in r.values() if v), "akış var;", sum(min(v, FEED_CAP) for v in r.values()), "kayıt (tavanlı)")
        print(sorted(r.items(), key=lambda x: -x[1]))
    elif mode == "crawl-search":
        crawl(int(sys.argv[2]) if len(sys.argv) > 2 else 42, "search_totals.json", "scripts_search.jsonl")
    else:
        crawl(int(sys.argv[2]) if len(sys.argv) > 2 else 42)
