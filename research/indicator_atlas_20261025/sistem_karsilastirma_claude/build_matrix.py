"""TradingView göstergeleri × ForexSAI (backend / bot / decider) kullanım + yön-kanıtı matrisi.

Elle küratörlü veri (kod okuması 2026-10-25, kaynak satırları RAPOR.md'de). Çalıştır:
    python3 research/indicator_atlas_20261025/sistem_karsilastirma_claude/build_matrix.py
MATRIS.md ve MATRIS.json üretir. Ağ, DB, broker kullanmaz.

Durum kodları (bileşen başına, virgülle birden fazla):
    K  karar/kapı — sinyal yönü, puan, veto veya emir kararını değiştirir
    M  ML modeli girdisi
    R  risk/geometri — SL/TP/boyut ölçeği (yön değil)
    B  bağlam — LLM/panel gösterimi, karar formülüne girmez
    G  gölge — ölçülür/kaydedilir, emir/blok yok
    Ky yalnız kayıt (veri kaydedici)
    A  yalnız istekle çalışan araç / araştırma endpoint'i
    Y  yer tutucu — sütun adı var, gerçek hesap yok
    ~  benzeri var, aynı formül değil
    -  yok
"""
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).parent

# (kategori, TradingView adı, kaynak, backend, bot, decider, formül/kapsam notu, yön kanıtı — Kapı Kayıt Defteri)
ROWS = [
    # ── Trend / hareketli ortalamalar (resmî yerleşik) ──
    ("Trend/MA", "Simple Moving Average", "resmi", "M", "Ky", "-", "ML sma_20/50/200; bot kaydedicide SMA20", "ayrı sınanmadı"),
    ("Trend/MA", "Exponential Moving Average", "resmi", "K,M", "K", "B",
     "Pulse/EMEL trend_direction (EMA20>50>200), meta ema_stack, bot TREND_GATE 1h EMA50, bot_router M15 EMA20 mesafesi",
     "A− B4 hizalı %63,3 vs karşı %43,4 · X HK-01 EMA10/25/50 kesişimi giriş olarak"),
    ("Trend/MA", "Double Exponential Moving Average", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Triple EMA", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Weighted Moving Average", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Hull Moving Average", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Arnaud Legoux Moving Average", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Kaufman's Adaptive Moving Average (KAMA)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "McGinley Dynamic", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Volume-Weighted Moving Average (VWMA)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Smoothed Moving Average (RMA/Wilder)", "resmi", "~", "~", "-", "yalnız ADX/ATR içinde iç yumuşatma", "—"),
    ("Trend/MA", "Least Squares Moving Average", "resmi", "~", "~", "~", "regresyon kanalının orta çizgisi olarak", "bkz. Linear Regression"),
    ("Trend/MA", "Linear Regression (kanal)", "resmi", "K,M", "K", "K,B",
     "fakeout kanal kırılımı, trend_analyzer, XAU v2 chan_slope/chan_pct; bot CHREV kanal z-skoru; decider gates kanal",
     "B OLD-09 araştırmada %44→72-84, canlı n=26 −1.024$"),
    ("Trend/MA", "MA Cross / MovingAvg Cross / MovingAvg2Line Cross", "resmi", "~", "-", "-", "EMA dizilim İŞARETİ var, kesişim OLAYI yok", "X HK-01 · X OLD-12 (MACD kesişimi)"),
    ("Trend/MA", "Moving Average Ribbon", "resmi", "~", "-", "-", "EMA20/50/200 dizilimi şerit mantığına yakın", "—"),
    ("Trend/MA", "Ichimoku Cloud", "resmi", "Y", "-", "-", "NDX ML'de 'ichimoku' adlı sütunlar varsayılanla doluyor", "sınanmadı"),
    ("Trend/MA", "Williams Alligator", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend/MA", "Median", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Supertrend", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Parabolic SAR (SAR)", "resmi", "K,M", "K,Ky", "-",
     "XAU pulse1 SAR kuralları; bot_router momentum filtresi H1 SAR (botun emrini veto eder); XAU v2 sar_above/sar_dist",
     "OLD-20 momentum filtresi (stoch+EMA20+SAR) NDX'te +0,054R ama ancak ATR 2/1 hedefte paraya dönüyor · X BTC-T06"),
    ("Trend", "Average Directional Index (ADX)", "resmi", "K,M", "K", "B",
     "rejim servisi (tüm model ağırlıkları), meta adx koşulu; bot CHREV ADX(30m)≥25; decider regime_meter",
     "C B7 (tek vaka −687$)"),
    ("Trend", "Directional Movement (DMI)", "resmi", "K,M", "Ky", "-", "+DI/−DI rejim ve kayıt", "—"),
    ("Trend", "Aroon Indicator / Aroon Oscillator", "resmi", "~", "-", "-", "XAU v2 bars_since_high/low_30 = Aroon'un çekirdek ölçüsü (osilatör yok)", "sınanmadı"),
    ("Trend", "Vortex Indicator", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Choppiness Index (CHOP)", "resmi", "A", "-", "-", "yalnız strategy_optimizer aracı", "sınanmadı"),
    ("Trend", "Chop Zone", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Trend Strength Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Chande Kroll Stop", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Chandelier Exit", "resmi", "~", "-", "-", "rebound_filter ATR×3 kuralı, EMEL/Pulse geri-dönüş notu", "sınanmadı"),
    ("Trend", "Volatility Stop", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Trend", "Zigzag indicator", "resmi", "-", "-", "-", "", "sınanmadı"),
    # ── Seviyeler / yapı ──
    ("Seviye", "Williams fractal indicator", "resmi", "K", "-", "-", "fraktal pivot S/R: fakeout dedektörü, trend_analyzer, rejim", "X HK-03 (dokunuş sayısı)"),
    ("Seviye", "Pivot Points High Low", "resmi", "K", "K", "B", "swing H/L: SMC, trend_analyzer; bot sr_zones S/R bölgeleri", "X OLD-05 (4H S/R reaksiyon girişi) · X HK-03"),
    ("Seviye", "Pivot Points Standard", "resmi", "~", "~", "-", "EMEL/Pulse 'pivot' son 20 barın H/L/C'sinden — günlük pivot DEĞİL; bot CAPREV önceki gün dibi", "sınanmadı"),
    ("Seviye", "Auto key levels", "resmi", "~", "~", "-", "fraktal S/R kümeleri", "X HK-03"),
    ("Seviye", "Auto Fib Retracement / Auto fib extension", "resmi", "B", "-", "B", "price_projection: debate + decider projections + panel; bilinçli olarak karar katmanına bağlanmadı", "sınanmadı (kodda 'edge yok, çapa')"),
    ("Seviye", "Auto Pitchfork", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Seviye", "Auto trendlines", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Seviye", "Rob Booker (6 yerleşik: ADX Breakout, Knoxville Div., Intraday/Missed/Ziv Ghost Pivots, Reversal)", "resmi", "-", "-", "-", "", "sınanmadı"),
    # ── Momentum / osilatörler ──
    ("Momentum", "Relative Strength Index (RSI)", "resmi", "K,M", "G,Ky", "B",
     "Pulse/EMEL momentum (RSI>50∧MACD>0∧Stoch>50), meta rsi koşulu, USOIL kurallı ML; bot SELL_RSI 5m>55 gölge. ML/Pulse hattında düz ortalama RSI (Wilder değil)",
     "C OLD-02 · C IO-05 (diverjans vetosu adayı) · X HK-04"),
    ("Momentum", "RSI divergence indicator", "resmi", "K", "-", "B", "trend_analyzer + rebound filtresi", "X HK-04 (giriş olarak) · C IO-05 (veto olarak, ileri doğrulama bekliyor)"),
    ("Momentum", "Stochastic (STOCH)", "resmi", "K,M", "K,Ky", "-",
     "Pulse momentum stoch_k>50; bot_router momentum filtresi %K>70 (NDX/DAX/USOIL BUY). ML/Pulse hattında %D=%K, bot_router hattında gerçek %D",
     "OLD-20 (filtre üyesi) · X BTC-T06"),
    ("Momentum", "Stochastic RSI", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Stochastic Momentum Index (SMI)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "MACD", "resmi", "K,M", "~", "-",
     "Pulse/EMEL MACD puanı, meta macd, USOIL kurallı ML. ML/Pulse hattında sinyal=0 ve histogram=MACD çizgisi → 'macd_hist>0' fiilen EMA12>EMA26; XAU v2 ve snapshot hattı gerçek. Bot: USOIL SELL filtresinde ama USOIL SELL zaten yasak",
     "X OLD-12 (MACD kesişimi scalp)"),
    ("Momentum", "Percentage Price Oscillator (PPO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Momentum", "resmi", "K,M", "K", "B", "momentum_3/10; bot MOM scope gerilmesi; sr_zones momentum_stretch", "A OLD-05/OLD-20 momentum-devam tek doğrulanmış giriş ailesi"),
    ("Momentum", "Rate of Change (ROC)", "resmi", "M", "K", "-", "ret1/5/20 ATR, ret_20_z; bot CAPREV günlük değişim", "B GF-21 CAPREV kartı (stres günü)"),
    ("Momentum", "Commodity Channel Index (CCI)", "resmi", "A", "-", "-", "yalnız permutation araştırma endpoint'i", "sınanmadı"),
    ("Momentum", "Woodies CCI", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Williams %R (%R)", "resmi", "M", "-", "-", "NDX/DAX ML sütunları", "sınanmadı"),
    ("Momentum", "Awesome Oscillator (AO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Chande Momentum Oscillator (CMO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "True Strength Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "TRIX", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Ultimate Oscillator (UO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Know Sure Thing (KST)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Coppock Curve", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Detrended Price Oscillator (DPO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Fisher Transform", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Connors RSI (CRSI)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "SMI Ergodic Indicator / Oscillator", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Relative Vigor Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Balance of Power (BOP)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Bull Bear Power", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Rank Correlation Index (RCI) / RCI Ribbon", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Pring's Special K", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Price Momentum Oscillator (PMO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Momentum", "Mass Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    # ── Oynaklık / bantlar ──
    ("Oynaklık", "Average True Range (ATR)", "resmi", "K,R,M", "K,R", "K,R",
     "signal_gates ATR geometrisi, ATR merdiveni TP/SL, fakeout; bot geometri/sıkışma/gerilme; decider erken kesme. ML hattı düz ortalama TR",
     "risk ölçeği, yön göstergesi değil · X M8 (TP=2,5×ATR70: WR↑ para↓)"),
    ("Oynaklık", "Average Daily Range (ADR)", "resmi", "B", "-", "B", "price_projection → debate/decider", "sınanmadı (GF-02 ADR tükenmesi hücresi elendi)"),
    ("Oynaklık", "Bollinger Bands (BB)", "resmi", "K,M", "Ky", "-", "meta bb koşulu, precision veto, USOIL kurallı ML z-skoru, fakeout", "C MK-07 (XAU BB sıkışma kırılımı gölge adayı)"),
    ("Oynaklık", "Bollinger Bands %b", "resmi", "M", "Ky", "-", "XAU v2 bb_pctb, fakeout", "sınanmadı"),
    ("Oynaklık", "Bollinger BandWidth (BBW)", "resmi", "M", "Ky", "-", "ML boll_width, fakeout", "sınanmadı"),
    ("Oynaklık", "Bollinger Bars", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Oynaklık", "BBTrend", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Oynaklık", "Keltner Channels (KC)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Oynaklık", "Donchian Channels (DC)", "resmi", "~", "G", "-", "XAU v2 swing uzaklıkları; bot USOIL breakout GÖLGE + XAU günlük swing GÖLGE",
     "X USOIL breakout P(EV>0) %0,3 · B XS-01 XAU günlük Golden Donchian bağımsız dönemde tuttu (n küçük)"),
    ("Oynaklık", "Envelope (ENV)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Oynaklık", "Historical Volatility", "resmi", "M", "K", "B", "ML vol_20, fakeout; bot CAPREV σ20", "B GF-21"),
    ("Oynaklık", "Relative Volatility Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Oynaklık", "Ulcer Index", "resmi", "-", "-", "-", "", "sınanmadı"),
    # ── Hacim ──
    ("Hacim", "Volume", "resmi", "K,M", "-", "G", "fakeout hacim patlaması, meta volume koşulu, Pulse hacim; decider entry_quality vol≥1,5 (gölge)", "X IO-03 (hacim SL'yi ayırmıyor) · X SY H2/H3"),
    ("Hacim", "Relative Volume at Time", "resmi", "~", "-", "~", "göreli hacim var ama saat-eşli değil", "sınanmadı"),
    ("Hacim", "On Balance Volume (OBV)", "resmi", "K,M", "-", "-", "rebound filtresi OBV teyidi, ML", "sınanmadı"),
    ("Hacim", "Money Flow (MFI)", "resmi", "M", "-", "-", "NDX/DAX ML", "sınanmadı"),
    ("Hacim", "Chaikin Money Flow (CMF)", "resmi", "Y", "-", "-", "ML sütun adı, hesap yok", "sınanmadı"),
    ("Hacim", "Chaikin Oscillator", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Accumulation Distribution (ADL)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Price Volume Trend (PVT)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Elder's Force Index (EFI)", "resmi", "A", "-", "-", "yalnız permutation araştırma endpoint'i", "sınanmadı"),
    ("Hacim", "Ease of Movement (EOM)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Klinger Oscillator", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Negative / Positive Volume Index (NVI/PVI)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Net Volume / Up/Down Volume / Volume Delta", "resmi", "-", "-", "-", "gerçek alış/satış ayrımı verisi yok", "sınanmadı"),
    ("Hacim", "Cumulative Volume Delta", "resmi", "~", "-", "-", "oil_analysis sentetik CVD (yeşil mum +0,6×hacim) → AI panel bağlamı; gerçek delta değil", "sınanmadı"),
    ("Hacim", "Percentage Volume Oscillator (PVO)", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Volume Weighted Average Price (VWAP)", "resmi", "K,B", "K", "K,B", "fakeout vwap_day özelliği; bot CHREV VWAP z-skoru; decider evidence/gates",
     "B CHREV: vwap kaynaklı tetikler zehirli (30m kapı GDAXI BUY %73,7 vs %28,6) · X OLD-15 vwap_rev · X BTC-SC-VS06/07"),
    ("Hacim", "VWAP Auto Anchored", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Time Weighted Average Price", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Visible Average Price", "resmi", "-", "-", "-", "", "sınanmadı"),
    ("Hacim", "Open Interest", "resmi", "~", "-", "-", "yalnız COT haftalık açık pozisyon", "sınanmadı"),
    ("Genişlik", "Advance/Decline Line, Ratio, Ratio (Bars), Cumulative Volume Index", "resmi", "-", "-", "-", "piyasa genişliği verisi alınmıyor", "sınanmadı"),
    # ── Diğer yerleşik ──
    ("Diğer", "Correlation Coefficient", "resmi", "M", "-", "-", "XAU v2 DXY/US10Y/VIX corr60", "X XAU'da makro yön yok (bellek: xauusd-macro-direction-no-edge)"),
    ("Diğer", "Seasonality", "resmi", "B", "-", "-", "oil_analysis + seasonality calc (AI panel)", "sınanmadı"),
    ("Diğer", "Trading Sessions", "resmi", "K", "K", "K", "seans kapıları, TQ, NDX ASIA/Cuma yasakları", "A B2 NDX Cuma · B B3 ASIA · B B6 TQ"),
    ("Diğer", "Technical Ratings", "resmi", "-", "-", "-", "TradingView'un MA+osilatör oylaması; bizdeki karşılığı meta 8 koşul (benzer fikir, farklı set)", "sınanmadı"),
    ("Diğer", "Performance / Multi-Time Period Charts / Moon Phases", "resmi", "-", "-", "-", "", "sınanmadı"),
    # ── Formasyonlar / profiller ──
    ("Formasyon", "Grafik formasyonları (TV 16: flag, pennant, cup, H&S, double/triple, wedge, rectangle, triangle)", "formasyon", "K,G,B", "-", "-",
     "harmonic_pattern_service 10 klasik (double/triple top-bottom, H&S, inv H&S, asc/desc triangle, wedge) — flag/pennant/cup/rectangle YOK; Pulse/EMEL bonusu, shadow tracker, debate",
     "X formasyon SELL %22,6 (n=115, p≈3e-9) → PATTERN_BONUS_GATE · BUY ≈%50 (n=124)"),
    ("Formasyon", "Elliott wave", "formasyon", "-", "-", "-", "", "sınanmadı"),
    ("Formasyon", "Mum formasyonları (All Candlestick Patterns, ~40)", "formasyon", "K,M", "-", "-", "precision veto: engulfing/shooting star…; XAU v2 mum anatomisi (gövde/fitil)", "X MK-01/02 · X MK-05"),
    ("Profil", "Hacim profilleri (Fixed/Session/Visible/Periodic/Auto Anchored, POC/VAH/VAL)", "profil", "B", "-", "B", "price_projection Market Profile (5g×5m) + oil_analysis VP", "sınanmadı ayrıca"),
    ("Profil", "TPO / Session TPO", "profil", "-", "-", "-", "", "X HK-02 (değer alanı %80 kuralı)"),
    # ── Topluluk aileleri (Public Library, resmî değil) ──
    ("Topluluk", "Smart Money Concepts (BOS/CHoCH, OB, FVG, liquidity — LuxAlgo vb.)", "topluluk", "K", "-", "B", "SMC modeli + rebound filtresi", "B NDX SMC SELL kapısı (14g 1W/28L)"),
    ("Topluluk", "Harmonik formasyonlar (Gartley, Bat, Crab, Shark, Cypher, Three Drives)", "topluluk", "K,G,B", "-", "-", "harmonic_pattern_service 8 harmonik", "formasyon kaynağıyla birlikte X (SELL)"),
    ("Topluluk", "Sahte kırılım / breakout dedektörleri", "topluluk", "K", "K", "B", "kendi fakeout dedektörümüz (NDX'te BLOK); bot FAKEOUT_VETO", "A OLD-17 (yalnız NDX) · B CK-04 · X CK-02 (işlem stratejisi olarak)"),
    ("Topluluk", "TTM Squeeze / Squeeze Momentum (LazyBear)", "topluluk", "~", "G", "-", "bot SQZ = ATR14/ATR100 oranı (BB-Keltner sıkışması değil)", "C/X B14 + IO-22 (ileri dönemde tutmadı)"),
    ("Topluluk", "Opening Range Breakout / Initial Balance", "topluluk", "B", "-", "B", "price_projection ORB (kodda 'edge yok' etiketi)", "X FG açılış aralığı kırılımı −0,89R"),
    ("Topluluk", "Lorentzian / k-NN sınıflandırma", "topluluk", "~", "-", "-", "CORTEX analog-kNN (enjeksiyon kapalı); Mum Benzerlik Tarayıcısı", "X OLD-13 · X ME-02/03"),
    ("Topluluk", "VIX rejimi / CM Williams VIX Fix", "topluluk", "K", "K", "B", "gerçek VIX (yfinance) ile VIX_REGIME_GATE BLOK + bot VIXREG; VIX Fix (sentetik) yok", "A OLD-10 (+24,9pp, OOS +17) · B GF-05 (işlem başına ≈0,01R)"),
    ("Topluluk", "COT raporu", "topluluk", "B", "-", "-", "DAX ve USOIL yanlışlıkla altın kontratına eşleniyor", "sınanmadı"),
    ("Topluluk", "WaveTrend (LazyBear) / VuManChu Cipher B", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "QQE / QQE MOD", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "HalfTrend", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "UT Bot Alerts", "topluluk", "-", "-", "-", "ATR trailing-stop yön değişimi", "sınanmadı"),
    ("Topluluk", "SSL Channel / Range Filter / Twin Range Filter", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "Nadaraya-Watson Envelope / Kernel Regression", "topluluk", "-", "-", "-", "LuxAlgo sürümü yeniden çiziyor (repaint)", "sınanmadı"),
    ("Topluluk", "Schaff Trend Cycle", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "Ehlers filtreleri (MESA/MAMA, SuperSmoother, Roofing)", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "Kalman filtresi", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "Wyckoff şemaları", "topluluk", "-", "-", "-", "", "sınanmadı"),
    ("Topluluk", "Trendlines with Breaks / Liquidity Swings (LuxAlgo)", "topluluk", "~", "-", "-", "fraktal S/R + SMC likidite benzeri", "X HK-03"),
]

# Pine Script v6 ta.* gösterge fonksiyonları (yardımcılar — cross, highest, valuewhen vb. — hariç)
PINE_TA = {
    "ta.accdist": "-", "ta.alma": "-", "ta.atr": "var", "ta.bb": "var", "ta.bbw": "var", "ta.cci": "araç",
    "ta.change": "var", "ta.cmo": "-", "ta.cog": "-", "ta.correlation": "var", "ta.dev": "-", "ta.dmi": "var",
    "ta.ema": "var", "ta.hma": "-", "ta.iii": "-", "ta.kc": "-", "ta.kcw": "-", "ta.linreg": "var",
    "ta.macd": "kusurlu (ML/Pulse hattı)", "ta.mfi": "var", "ta.mom": "var", "ta.nvi": "-", "ta.obv": "var",
    "ta.percentrank": "~", "ta.pivot_point_levels": "~", "ta.pivothigh": "var", "ta.pivotlow": "var",
    "ta.pvi": "-", "ta.pvt": "-", "ta.rci": "-", "ta.rma": "var", "ta.roc": "var", "ta.rsi": "var (ML/Pulse hattı Wilder değil)",
    "ta.sar": "var", "ta.sma": "var", "ta.stdev": "var", "ta.stoch": "var (ML/Pulse hattında %D yok)",
    "ta.supertrend": "-", "ta.swma": "-", "ta.tr": "var", "ta.tsi": "-", "ta.variance": "~", "ta.vwap": "var",
    "ta.vwma": "-", "ta.wad": "-", "ta.wma": "-", "ta.wpr": "var", "ta.wvad": "-",
}

# Birden fazla resmî yardım sayfasını birleştiren satırlar (geri kalan resmî satırlar = 1 sayfa).
# Resmî 209 sayfanın 83'ü kripto/on-chain/temel/rehber; kalan 126 teknik sayfa + Open Interest = 127.
PAGES = {
    "MA Cross / MovingAvg Cross / MovingAvg2Line Cross": 3, "Aroon Indicator / Aroon Oscillator": 2,
    "Auto Fib Retracement / Auto fib extension": 2, "SMI Ergodic Indicator / Oscillator": 2,
    "Rank Correlation Index (RCI) / RCI Ribbon": 2, "Negative / Positive Volume Index (NVI/PVI)": 2,
    "Net Volume / Up/Down Volume / Volume Delta": 3, "Advance/Decline Line, Ratio, Ratio (Bars), Cumulative Volume Index": 4,
    "Performance / Multi-Time Period Charts / Moon Phases": 3,
    "Rob Booker (6 yerleşik: ADX Breakout, Knoxville Div., Intraday/Missed/Ziv Ghost Pivots, Reversal)": 6,
}

DECISION = {"K", "M", "R"}
TOUCH = {"B", "G", "Ky", "A", "~", "Y"}


def codes(cell: str) -> set:
    return {c.strip() for c in cell.split(",") if c.strip() and c.strip() != "-"}


def level(row) -> str:
    allc = codes(row[3]) | codes(row[4]) | codes(row[5])
    if allc & DECISION:
        return "karar yolunda"
    if allc - {"Y", "~"}:
        return "dokunuyor, karar değil"
    if allc:
        return "yalnız benzeri / yer tutucu"
    return "yok"


def main() -> None:
    lv = Counter(level(r) for r in ROWS)
    by_src = Counter((r[2], level(r)) for r in ROWS)
    comp = {name: Counter() for name in ("backend", "bot", "decider")}
    for r in ROWS:
        for name, cell in zip(("backend", "bot", "decider"), r[3:6]):
            cs = codes(cell)
            comp[name]["karar (K/M/R)" if cs & DECISION else ("dokunuyor" if cs - {"Y", "~"} else ("benzeri/yer tutucu" if cs else "yok"))] += 1
    tested = Counter("sınanmadı" if r[7].startswith("sınanmadı") or r[7] == "—" else "defterde kaydı var" for r in ROWS)
    pine = Counter(v.split(" ")[0] for v in PINE_TA.values())
    pages = Counter()
    for r in ROWS:
        if r[2] == "resmi":
            pages[level(r)] += PAGES.get(r[1], 1)

    lines = ["# TradingView göstergeleri × ForexSAI — kullanım ve yön-kanıtı matrisi", "",
             "Üretici: `build_matrix.py` (elle küratörlü, kod okuması 2026-10-25). Durum kodları dosyanın başında.", "",
             f"Satır: **{len(ROWS)}** (bir satır bazen aynı ailedeki birkaç yerleşik sayfayı birleştirir).", "",
             "| Seviye | Satır |", "|---|---:|"]
    lines += [f"| {k} | {v} |" for k, v in lv.most_common()]
    lines += ["", "| Bileşen | karar (K/M/R) | dokunuyor | benzeri/yer tutucu | yok |", "|---|---:|---:|---:|---:|"]
    for name, c in comp.items():
        lines.append(f"| {name} | {c['karar (K/M/R)']} | {c['dokunuyor']} | {c['benzeri/yer tutucu']} | {c['yok']} |")
    lines += ["", "| Kaynak × seviye | sayı |", "|---|---:|"]
    lines += [f"| {s} · {l} | {n} |" for (s, l), n in sorted(by_src.items())]
    lines += ["", f"Resmî teknik yardım sayfası düzeyinde ({sum(pages.values())} sayfa): {dict(pages)}", "",
              f"Yön kanıtı: {dict(tested)}", "",
              "| Kategori | Gösterge | Kaynak | Backend | Bot | Decider | Seviye | Not | Yön kanıtı (defter) |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in ROWS:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {level(r)} | {r[6]} | {r[7]} |")
    lines += ["", "## Pine Script v6 `ta.*` gösterge fonksiyonları", "",
              f"Özet: {dict(pine)}", "", "| Fonksiyon | Bizde |", "|---|---|"]
    lines += [f"| `{k}` | {v} |" for k, v in PINE_TA.items()]
    (OUT / "MATRIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    keys = ["kategori", "gosterge", "kaynak", "backend", "bot", "decider", "not", "yon_kaniti"]
    json.dump({"rows": [dict(zip(keys, r), seviye=level(r)) for r in ROWS], "pine_ta": PINE_TA,
               "ozet": {"seviye": dict(lv), "resmi_sayfa": dict(pages), "bilesen": {k: dict(v) for k, v in comp.items()}, "kanit": dict(tested), "pine": dict(pine)}},
              open(OUT / "MATRIS.json", "w"), ensure_ascii=False, indent=1)
    print(dict(lv)); print({k: dict(v) for k, v in comp.items()}); print(dict(tested)); print(dict(pine))
    print(sorted(by_src.items())); print("resmi sayfa:", dict(pages), sum(pages.values()))


if __name__ == "__main__":
    main()
