"""data/scripts.jsonl → gösterge ailesi sınıflaması + sistem karşılaştırması.

Çıktı: AILELER.md, AILELER.json, data/unique_scripts.jsonl.
Bir script birden fazla aileye düşebilir (çok etiketli); aile sayıları toplanmaz.
"""
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
TOP_N = 6

# (aile kodu, grup, Türkçe ad, regex (ad + açıklama), sistemde, defter kanıtı)
# sistemde: K karar · M ML girdisi · B bağlam · G gölge · ~ benzeri (aynı formül değil) · - yok
FAMILIES = [
    # ── SMC / ICT ──
    ("smc_structure", "SMC/ICT", "Piyasa yapısı (BOS/CHoCH/MSS)", r"\bbos\b|choch|market structure|\bmss\b|break of structure|change of character", "K", "B NDX SMC SELL kapısı (14g 1W/28L)"),
    ("order_block", "SMC/ICT", "Order block / breaker / mitigation", r"order ?blocks?|\bob\b|breaker|mitigation block", "K", "SMC modeliyle birlikte"),
    ("fvg", "SMC/ICT", "Fair value gap / imbalance / IFVG", r"\bi?fvgs?\b|fair value gap|imbalance|\bbpr\b|volume imbalance", "K", "SMC modeliyle birlikte"),
    ("liquidity", "SMC/ICT", "Likidite süpürmesi / SFP / stop hunt", r"liquidity|sweep|stop.?hunt|\bsfp\b|swing failure|liquidity grab|\braid\b", "K", "A NDX fakeout (OLD-17) · X FG süpürme SELL"),
    ("ict_time", "SMC/ICT", "ICT zaman modelleri (killzone, silver bullet, PO3, CRT, macro)", r"kill ?zones?|silver bullet|power of (?:3|three)|\bpo3\b|\bamd\b|judas|candle range theory|\bcrt\b|ict macro|turtle soup|\bcisd\b|\bsmt\b", "~", "seans kapıları var; ICT zaman modelleri sınanmadı"),
    ("premium_discount", "SMC/ICT", "Premium/discount, OTE", r"premium|discount zone|\bote\b|optimal trade entry|equilibrium", "K", "B OLD-28 premium_zone_buy vetosu (NDX haklı, USOIL muaf)"),
    # ── Trend ──
    ("supertrend", "Trend", "Supertrend ve türevleri", r"super ?trend", "-", "sınanmadı"),
    ("halftrend_utbot", "Trend", "HalfTrend / UT Bot / SSL / Range Filter", r"half ?trend|ut ?bot|\bssl\b|range filter|twin range", "-", "sınanmadı"),
    ("ma_adaptive", "Trend", "Gelişmiş/uyarlanabilir MA (Hull, KAMA, ALMA, T3, ZLEMA, JMA, VIDYA, FRAMA, McGinley)", r"\bhull\b|\bhma\b|\bkama\b|kaufman|\balma\b|\bt3\b|zlema|zero.?lag|jurik|\bjma\b|vidya|frama|mcginley|\bdema\b|\btema\b", "-", "sınanmadı"),
    ("ma_basic_cross", "Trend", "MA kesişimi / şerit / EMA bulutu", r"ma cross|ema cross|golden cross|death cross|ribbon|moving average cross|ema cloud", "~", "X HK-01 EMA 10/25/50 · A− B4 EMA50 hizası"),
    ("ichimoku", "Trend", "Ichimoku", r"ichimoku|kumo|tenkan|kijun", "-", "sınanmadı"),
    ("psar", "Trend", "Parabolic SAR", r"parabolic|\bpsar\b|\bsar\b", "K", "OLD-20 momentum filtresinin üyesi"),
    ("adx_dmi", "Trend", "ADX / DMI", r"\badx\b|\bdmi\b|directional movement", "K", "C B7"),
    ("regression_channel", "Trend", "Regresyon / standart sapma kanalı", r"regression|linreg|lsma|standard deviation channel|std channel", "K", "B OLD-09 CHREV (canlı zayıf)"),
    ("trendlines", "Trend", "Otomatik trend çizgisi / kırılımı", r"trend ?lines?|trendline break", "-", "X HK-03 (S/R dokunuş)"),
    ("donchian_turtle", "Trend", "Donchian / Turtle kırılımı", r"donchian|turtle", "G", "X USOIL breakout · B XS-01 XAU günlük"),
    ("keltner", "Trend", "Keltner kanalı", r"keltner", "-", "sınanmadı"),
    ("atr_trailing", "Trend", "ATR trailing stop / Chandelier / volatilite stop", r"chandelier|trailing stop|atr stop|volatility stop|atr trailing", "~", "X BE/kilit çıkışları (bellek be-lock-exit-rules-rejected)"),
    ("heikin_renko", "Trend", "Heikin Ashi / Renko / Kagi / P&F", r"heikin|heiken|renko|kagi|point (?:and|&) figure", "-", "sınanmadı"),
    # ── Osilatörler ──
    ("rsi", "Osilatör", "RSI türevleri", r"\brsi\b", "K", "C IO-05 · X HK-04 · C OLD-02"),
    ("stoch", "Osilatör", "Stochastic / Stoch RSI", r"stoch", "K", "OLD-20 filtre üyesi · X BTC-T06"),
    ("macd", "Osilatör", "MACD türevleri", r"\bmacd\b", "K", "X OLD-12"),
    ("wavetrend_cipher", "Osilatör", "WaveTrend / Market Cipher / VuManChu", r"wave ?trend|cipher|vumanchu", "-", "sınanmadı"),
    ("qqe", "Osilatör", "QQE", r"\bqqe", "-", "sınanmadı"),
    ("cci", "Osilatör", "CCI", r"\bcci\b|commodity channel", "-", "sınanmadı (yalnız araştırma endpoint'i)"),
    ("fisher_schaff", "Osilatör", "Fisher Transform / Schaff Trend Cycle", r"fisher|schaff|\bstc\b", "-", "sınanmadı"),
    ("other_osc", "Osilatör", "Diğer klasik osilatörler (TSI, TRIX, KST, CMO, AO, UO, Williams %R, Aroon, Vortex, Coppock)", r"\btsi\b|true strength|\btrix\b|\bkst\b|\bcmo\b|awesome osc|ultimate osc|williams ?%?r|aroon|vortex|coppock|andean|bulls? (?:or|vs) bears?|bull vs bear", "M", "Williams %R yalnız ML girdisi; diğerleri sınanmadı"),
    ("divergence", "Osilatör", "Diverjans tarayıcıları", r"divergen", "K", "X HK-04 (giriş) · C IO-05 (veto)"),
    ("squeeze", "Osilatör", "Squeeze / TTM sıkışma", r"squeeze|\bttm\b", "~", "C/X B14 + IO-22"),
    ("momentum_roc", "Osilatör", "Momentum / ROC / hız", r"momentum|rate of change|\broc\b|velocity|acceleration", "K", "A OLD-20 momentum-devam (uzak hedef)"),
    # ── Oynaklık / istatistik ──
    ("bollinger", "Oynaklık", "Bollinger türevleri", r"bollinger|\bbb\b|%b\b|bandwidth", "K", "C MK-07 XAU BB sıkışma"),
    ("atr_vol", "Oynaklık", "ATR / oynaklık ölçüleri", r"\batr\b|average true range|volatility", "K", "risk ölçeği · X M8"),
    ("zscore_meanrev", "Oynaklık", "Z-skoru / ortalamaya dönüş / sapma bantları", r"z-?score|mean reversion|deviation band|std ?dev|standard deviation", "~", "B OLD-09 CHREV z · X OLD-15 vwap_rev"),
    ("vix_regime", "Oynaklık", "VIX / oynaklık rejimi / risk-on-off", r"\bvix\b|risk.?on|risk.?off|volatility regime|fear", "K", "A OLD-10 VIXREG"),
    ("regime_entropy", "İstatistik", "Rejim / entropi / Hurst / fraktal boyut / choppiness", r"regime|entropy|hurst|fractal dimension|chop(?:piness)?|efficiency ratio", "~", "rejim servisi ADX tabanlı; entropi/Hurst sınanmadı"),
    ("stats_prob", "İstatistik", "Olasılık / dağılım / persentil / Monte Carlo", r"probabilit|distribution|percentile|monte carlo|statistic|expectancy|win ?rate", "~", "sınanmadı (yöntem olarak defterin kendisi)"),
    # ── Hacim / emir akışı ──
    ("vwap", "Hacim", "VWAP (seans / çapalı / bant)", r"vwap", "K", "B CHREV vwap tetiği zehirli · X BTC-SC-VS06/07"),
    ("volume_profile", "Hacim", "Hacim profili / POC / VAH-VAL / Market Profile / TPO", r"volume profile|\bpoc\b|\bvah\b|\bval\b|value area|market profile|\btpo\b", "B", "X HK-02 değer alanı %80"),
    ("orderflow_delta", "Hacim", "Delta / CVD / footprint / emir akışı", r"\bcvd\b|cumulative delta|volume delta|footprint|order ?flow|bid.?ask|aggress|absorption", "~", "sentetik CVD (petrol bağlamı); gerçek tick-delta yok"),
    ("volume_classic", "Hacim", "OBV / MFI / CMF / ADL / PVT / Klinger / Force", r"\bobv\b|on balance|\bmfi\b|money flow|\bcmf\b|chaikin|accumulation.?distribution|\bpvt\b|klinger|force index|price volume trend", "K", "OBV rebound filtresi, MFI ML; diğerleri sınanmadı"),
    ("relative_volume", "Hacim", "Göreli hacim / hacim patlaması / klimaks", r"relative volume|\brvol\b|volume spike|volume surge|climax|unusual volume|N:\\bvolume\\b", "K", "X IO-03 · X SY H2/H3"),
    # ── Seviyeler / zaman ──
    ("pivot_points", "Seviye", "Pivot noktaları (klasik/Camarilla/Fib/Woodie)", r"pivot points?|camarilla|woodie|\bcpr\b|central pivot", "~", "EMEL pivot'u 20-bar; günlük pivot sınanmadı"),
    ("prior_levels_orb", "Seviye", "Önceki gün/hafta uçları, açılış aralığı (ORB), initial balance", r"previous day|prior day|\bpdh\b|\bpdl\b|weekly open|opening range|\borb\b|initial balance|first candle|daily open", "~", "X FG açılış aralığı −0,89R · GF-02 önceki gün uçları"),
    ("sr_zones", "Seviye", "Destek/direnç / arz-talep bölgeleri", r"support|resistance|supply|demand|\bs/r\b|\bsnr\b|key levels", "K", "X OLD-05 · X HK-03"),
    ("fibonacci", "Seviye", "Fibonacci (oto fib, golden pocket, uzatma)", r"fib(?:onacci)?\b|golden pocket|retracement|extension", "B", "sınanmadı (bağlam-only)"),
    ("gann_round", "Seviye", "Gann / yuvarlak sayı / psikolojik seviye", r"\bgann\b|square of 9|round number|psycholog|quarter level|big figure|murrey", "-", "GF-02 yuvarlak sayı hücresi elendi"),
    ("sessions", "Zaman", "Seans kutuları / seans uçları / zaman filtresi", r"session|asia|london|new york|\bny\b|market hours", "K", "A B2 · B B3 · B B6"),
    ("seasonality_time", "Zaman", "Mevsimsellik / gün-saat istatistiği / döngü zamanlaması", r"seasonal|day of week|time of day|hour of day|cycle low|cycles?\b|timing", "K", "B B6 TQ (saat/gün) · E35/E17 uyarıları"),
    # ── Formasyonlar ──
    ("harmonic", "Formasyon", "Harmonik formasyonlar", r"harmonic|gartley|butterfly|\bbat\b|crab|cypher|shark|abcd|xabcd|three drives", "K", "X formasyon SELL %22,6"),
    ("chart_patterns", "Formasyon", "Klasik grafik formasyonları (H&S, çift tepe, takoz, üçgen, bayrak)", r"head (?:and|&) shoulders|double (?:top|bottom)|triple (?:top|bottom)|wedge|triangle|\bflags?\b|pennant|cup (?:and|&) handle|cup finder|1-2-3 pattern|chart pattern", "K", "X formasyon SELL · BUY ≈%50"),
    ("candlestick", "Formasyon", "Mum formasyonları (engulfing, pin bar, inside bar…)", r"engulf|pin ?bar|doji|hammer|inside bar|outside bar|morning star|evening star|harami|candlesticks? patterns?|marubozu|body candle|candle strength", "K", "X MK-01/02/05"),
    ("elliott_wyckoff", "Formasyon", "Elliott dalgası / Wyckoff", r"ellio?tt?\b|elliot wave|wyckoff|accumulation phase|spring|upthrust", "-", "sınanmadı"),
    ("zigzag_swing", "Formasyon", "ZigZag / swing / fraktal noktaları", r"zig ?zag|swing high|swing low|swings?\b|fractals?", "K", "X HK-03 · fakeout fraktal S/R"),
    # ── ML / filtre / çapraz piyasa ──
    ("ml_classification", "ML/İstatistik", "Makine öğrenmesi (kNN, Lorentzian, sinir ağı, SVM, lojistik)", r"machine learning|\bml\b|\bknn\b|k-nn|nearest neighbo|lorentzian|neural|\bai\b|svm|logistic|random forest|classifier|perceptron", "~", "X OLD-13 analog-kNN · X ME-02/03 · X BTC-SC-ML01"),
    ("kernel_regression", "ML/İstatistik", "Kernel regresyon / Nadaraya-Watson / Gaussian", r"nadaraya|kernel|gaussian process|gaussian filter", "-", "sınanmadı"),
    ("ehlers_dsp", "ML/İstatistik", "Ehlers / sinyal işleme (SuperSmoother, MESA, Hilbert, Roofing)", r"ehlers|super ?smoother|\bmesa\b|hilbert|roofing|decycler|instantaneous trend|laguerre|butterworth", "-", "sınanmadı"),
    ("kalman", "ML/İstatistik", "Kalman filtresi", r"kalman", "-", "sınanmadı"),
    ("intermarket", "Çapraz piyasa", "Korelasyon / güç sepeti / DXY / intermarket / SMT", r"correlat|intermarket|currency strength|strength meter|basket|\bdxy\b|dollar index|relative strength vs|\bsmt\b", "M", "X XAU makro yön yok · A OLD-10 VIX→NDX"),
    ("sentiment_cot", "Çapraz piyasa", "COT / duyarlılık / put-call / genişlik", r"\bcot\b|commitment of traders|sentiment|put.?call|breadth|advance.?decline|max pain|options? (?:flow|oi|open interest)|gamma exposure|\\bgex\\b", "B", "COT bağlam (DAX/USOIL yanlış eşleme)"),
    # ── Meta / araç ──
    ("all_in_one", "Meta", "Hepsi-bir-arada AL/SAT sinyal / confluence / dashboard / screener", r"all.?in.?one|buy.?sell signals?|confluence|dashboard|screener|scanner|multi.?timeframe table|signals? suite", "~", "meta füzyon motoru (6 model) benzer fikir"),
    ("fakeout", "Meta", "Sahte kırılım / tuzak / başarısız kırılım", r"fake ?out|false break|failed break|bull trap|bear trap|\btrap\b", "K", "A OLD-17 (yalnız NDX) · B CK-04"),
    ("risk_tools", "Meta", "Pozisyon büyüklüğü / risk / TP-SL hedef hesaplayıcı", r"position siz|risk calculator|lot size|risk.?reward|\brr\b|N:targets?\b|take profit|stop loss", "R", "ATR merdiveni / bot geometrisi"),
    # 2. tur: ilk geçişte sınıflanmayan popüler script'lerden türetildi
    ("ma_general", "Trend", "Genel / çoklu MA araçları (MTF MA, Sling Shot, ActionZone, TMA bant)", r"N:moving averages?|N:\bma\b|N:\bemas?\b|N:\bsma\b|sling shot|action ?zone|\btma\b|triangular moving", "K", "A− B4 EMA50 · X HK-01"),
    ("reversal_detect", "Formasyon", "N-bar dönüş / tepe-dip / dönüş sinyali dedektörleri", r"N:reversal|N:tops?.?/.?bottoms?|turning point|three bar reversal|n bar reversal", "~", "rebound filtresi · X OLD-15 dönüş aileleri · B CAPREV 'korku döner'"),
    ("range_consolidation", "Seviye", "Aralık / konsolidasyon / Darvas kutusu tespiti", r"range detector|consolidation|darvas|N:\branges?\b|box breakout|range breakout", "~", "X MK-07 R1 48-bar kırılım · B14 sıkışma"),
    ("buy_sell_pressure", "Hacim", "Alım-satım baskısı / balina / emir defteri tahmini", r"buy.?sell volume|buy.?sell pressure|volume pressure|market buy|whale|orderbook|order book|N:pressure", "~", "Whale tracker (COT tabanlı, bağlam); gerçek defter verisi yok"),
    ("daily_bias", "Meta", "Günlük bias / yön önyargısı modelleri", r"daily bias|N:\bbias\b|htf bias", "B", "X OLD-18 tartışma-bias (temiz ölçüm %42,6)"),
    ("htf_overlay", "Zaman", "Üst zaman dilimi mum katmanı / MTF mum", r"higher time ?frame|htf candles?|multi time ?frame candles|mtf candles|N:\bhtf\b", "~", "Pulse3 5m+1H+4H MTF; mum katmanı yok"),
    ("automation_tools", "Araç", "Alarm / bot köprüsü / backtest çatısı / strateji kurucu (gösterge değil)", r"N:alerts?\b|3commas|webhook|N:\bbot\b|strategy builder|backtesting (?:&|and) trading engine|N:framework|N:template|mt4|mt5|N:backtest", "-", "kapsam dışı (araç)"),
    ("econ_calendar", "Zaman", "Ekonomik takvim / haber olayı göstergeleri", r"economic calendar|news|N:events?\b|fomc|cpi|nfp", "K", "C CALENDAR_GATE ±30 dk (K6)"),
    ("trend_followers_other", "Trend", "Diğer trend takipçileri (G-Channel, Trend Levels, Trend Trigger…)", r"N:\btrend\b", "~", "EMA/ADX/kanal ailesiyle örtüşür; özel formüller sınanmadı"),
]


def _compile(rx: str):
    """'N:' önekli alternatifler yalnız script adında aranır; diğerleri ad + açıklamada."""
    name_parts = [p[2:] for p in rx.split("|") if p.startswith("N:")]
    full_parts = [p for p in rx.split("|") if not p.startswith("N:")]
    full = re.compile("|".join(full_parts), re.I) if full_parts else None
    name = re.compile("|".join(name_parts), re.I) if name_parts else None
    return full, name


def matches(compiled, name: str, text: str) -> bool:
    full, name_rx = compiled
    return bool((full and full.search(text)) or (name_rx and name_rx.search(name)))


COMPILED = [(f, g, n, _compile(rx), s, e) for f, g, n, rx, s, e in FAMILIES]


def load() -> dict:
    uniq: dict = {}
    lines = [ln for name in ("scripts.jsonl", "scripts_search.jsonl") if (DATA / name).exists()
             for ln in (DATA / name).open()]
    for line in lines:
        r = json.loads(line)
        cur = uniq.setdefault(r["id"], {**r, "tags": set()})
        cur["tags"].add(r["tag"])
        cur["boosts"] = max(cur.get("boosts") or 0, r.get("boosts") or 0)
    return uniq


def main() -> None:
    uniq = load()
    fam_rows = defaultdict(list)
    unclassified = []
    for s in uniq.values():
        text = f"{s['name']} {s['desc']}"
        hits = [f for f, _, _, rx, _, _ in COMPILED if matches(rx, s["name"], text)]
        s["families"] = hits
        for f in hits:
            fam_rows[f].append(s)
        if not hits:
            unclassified.append(s)

    with (DATA / "unique_scripts.jsonl").open("w") as out:
        for s in uniq.values():
            out.write(json.dumps({**s, "tags": sorted(s["tags"])}, ensure_ascii=False) + "\n")
    with (HERE / "KATALOG.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ad", "yazar", "boost", "yil", "tur", "aileler", "baglanti"])
        for s in sorted(uniq.values(), key=lambda r: -(r.get("boosts") or 0)):
            url = s.get("url") or ""
            w.writerow([s["name"], s.get("author"), s.get("boosts"), (s.get("created_at") or "")[:4], s.get("type"),
                        ";".join(s["families"]), url if url.startswith("http") else f"https://www.tradingview.com{url}"])

    n = len(uniq)
    types = defaultdict(int)
    years = defaultdict(int)
    for s in uniq.values():
        types[s.get("type")] += 1
        years[(s.get("created_at") or "????")[:4]] += 1

    summary = []
    for f, g, name, _, status, ev in COMPILED:
        rows = fam_rows.get(f, [])
        b = [r.get("boosts") or 0 for r in rows]
        top = sorted(rows, key=lambda r: -(r.get("boosts") or 0))[:TOP_N]
        summary.append({
            "kod": f, "grup": g, "aile": name, "script": len(rows),
            "toplam_boost": sum(b), "medyan_boost": statistics.median(b) if b else 0,
            "sistemde": status, "kanit": ev,
            "en_populer": [f"{r['name']} — {r['author']} ({r.get('boosts')}, {(r.get('created_at') or '')[:4]})" for r in top],
        })
    json.dump({"benzersiz_script": n, "tur": types, "yil": dict(sorted(years.items())),
               "siniflanmayan": len(unclassified), "aileler": summary,
               "siniflanmayan_en_populer": [f"{r['name']} ({r.get('boosts')})" for r in
                                            sorted(unclassified, key=lambda r: -(r.get('boosts') or 0))[:60]]},
              (HERE / "AILELER.json").open("w"), ensure_ascii=False, indent=1, default=list)
    write_md(n, types, years, summary, unclassified)
    print(n, "benzersiz;", len(unclassified), "sınıflanmadı;", dict(types))


def write_md(n, types, years, summary, unclassified) -> None:
    L = ["# TradingView topluluk göstergeleri — aile atlası", "",
         f"Benzersiz script: **{n}** · tür: {dict(types)}", "",
         "Kaynak erişimi (açık/korumalı) liste verisinden ayrışmadığı için raporlanmadı.", "",
         "Yıl dağılımı: " + ", ".join(f"{y}: {c}" for y, c in sorted(years.items())), "",
         "Sistemde: K karar · M ML girdisi · R risk · B bağlam · G gölge · ~ benzeri (aynı formül değil) · - yok", "",
         "| Grup | Aile | Script | Toplam boost | Medyan boost | Sistemde | Defter kanıtı | En popüler örnekler |",
         "|---|---|---:|---:|---:|---|---|---|"]
    for s in sorted(summary, key=lambda x: -x["toplam_boost"]):
        L.append(f"| {s['grup']} | {s['aile']} | {s['script']} | {s['toplam_boost']:,} | "
                 f"{s['medyan_boost']:.0f} | {s['sistemde']} | {s['kanit']} | {'<br>'.join(s['en_populer'][:4])} |")
    L += ["", f"## Hiçbir aileye düşmeyen en popüler {min(40, len(unclassified))} script (elle bakılacak)", ""]
    for r in sorted(unclassified, key=lambda r: -(r.get("boosts") or 0))[:40]:
        L.append(f"- {r['name']} — {r['author']} ({r.get('boosts')}, {(r.get('created_at') or '')[:4]})")
    (HERE / "AILELER.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
