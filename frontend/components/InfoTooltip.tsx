"use client";

import { useState, useCallback, ReactNode } from "react";
import { X, Info, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, HelpCircle } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

// ═══════════════════════════════════════════════════════════════════
// TRADING INFO DATABASE - Tüm göstergeler ve değerlerin açıklamaları
// ═══════════════════════════════════════════════════════════════════

export interface InfoData {
  title: string;
  description: string;
  usage: string;
  levels?: { value: string; meaning: string; action: string }[];
  example?: string;
  importance: "critical" | "high" | "medium" | "low";
}

// Locale-based trading info
export function getTradingInfo(locale: string): Record<string, InfoData> {
  const isEn = locale === "en";
  
  return {
  // ═══════════════════════════════════════════════════════════════════
  // BASIC INDICATORS
  // ═══════════════════════════════════════════════════════════════════
  
  rsi: {
    title: "RSI (Relative Strength Index)",
    description: isEn 
      ? "Momentum indicator showing whether price is in overbought or oversold territory."
      : "Fiyatın aşırı alım veya aşırı satım bölgesinde olup olmadığını gösteren momentum göstergesi.",
    usage: isEn 
      ? "Used to detect trend reversals and extreme moves."
      : "Trend dönüşlerini ve aşırı hareketleri tespit etmek için kullanılır.",
    levels: [
      { value: "< 30", meaning: isEn ? "Oversold" : "Aşırı Satım", action: isEn ? "🟢 Look for LONG" : "🟢 LONG fırsatı ara" },
      { value: "30-50", meaning: isEn ? "Weak/Bearish" : "Zayıf/Düşüş", action: isEn ? "⚠️ Be careful" : "⚠️ Dikkatli ol" },
      { value: "50-70", meaning: isEn ? "Strong/Bullish" : "Güçlü/Yükseliş", action: isEn ? "📈 Trend continues" : "📈 Trend devam" },
      { value: "> 70", meaning: isEn ? "Overbought" : "Aşırı Alım", action: isEn ? "🔴 Look for SHORT" : "🔴 SHORT fırsatı ara" },
    ],
    example: isEn ? "RSI 25 → Price dropped a lot, recovery may come" : "RSI 25 → Fiyat çok düştü, toparlanma gelebilir",
    importance: "high",
  },

  macd: {
    title: "MACD (Moving Average Convergence Divergence)",
    description: isEn ? "Trend-following indicator showing difference between two moving averages." : "İki hareketli ortalama arasındaki farkı gösteren trend takip göstergesi.",
    usage: isEn ? "Detects trend direction and momentum changes." : "Trend yönü ve momentum değişimlerini tespit eder.",
    levels: [
      { value: "MACD > Signal", meaning: "Bullish Crossover", action: isEn ? "🟢 LONG signal" : "🟢 LONG sinyali" },
      { value: "MACD < Signal", meaning: "Bearish Crossover", action: isEn ? "🔴 SHORT signal" : "🔴 SHORT sinyali" },
      { value: "Histogram +", meaning: isEn ? "Rising momentum" : "Yükseliş momentumu", action: isEn ? "📈 Trend strengthening" : "📈 Trend güçleniyor" },
      { value: "Histogram -", meaning: isEn ? "Falling momentum" : "Düşüş momentumu", action: isEn ? "📉 Trend weakening" : "📉 Trend zayıflıyor" },
    ],
    example: isEn ? "MACD crosses signal upward → BUY signal" : "MACD signal'ı yukarı keserse → BUY sinyali",
    importance: "high",
  },

  adx: {
    title: "ADX (Average Directional Index)",
    description: isEn ? "Measures trend strength (not direction, only strength)." : "Trendin gücünü ölçer (yön göstermez, sadece güç).",
    usage: isEn ? "To understand if market is trending or sideways." : "Piyasanın trendde mi yoksa yatay mı olduğunu anlamak için.",
    levels: [
      { value: "< 20", meaning: isEn ? "Weak/Sideways" : "Zayıf/Yatay Piyasa", action: isEn ? "⚠️ Range trading" : "⚠️ Range trading yap" },
      { value: "20-40", meaning: isEn ? "Developing Trend" : "Gelişen Trend", action: isEn ? "📊 Follow trend" : "📊 Trend takip et" },
      { value: "40-60", meaning: isEn ? "Strong Trend" : "Güçlü Trend", action: isEn ? "🚀 Go with trend" : "🚀 Trendle git" },
      { value: "> 60", meaning: isEn ? "Very Strong Trend" : "Aşırı Güçlü Trend", action: isEn ? "⚡ Caution, exhaustion near" : "⚡ Dikkat, tükenme yakın" },
    ],
    example: isEn ? "ADX 50 + DI+ > DI- → Strong uptrend" : "ADX 50 + DI+ > DI- → Güçlü yükseliş trendi",
    importance: "critical",
  },

  di_spread: {
    title: isEn ? "DI Spread (+DI / -DI Difference)" : "DI Spread (+DI / -DI Farkı)",
    description: isEn ? "ADX component showing trend direction and strength together." : "Trendin yönünü ve gücünü birlikte gösteren ADX bileşeni.",
    usage: isEn ? "If ADX high but DI spread low → No real trend!" : "ADX yüksek ama DI spread düşükse → Gerçek trend yok!",
    levels: [
      { value: "+DI >> -DI", meaning: isEn ? "Strong Bullish" : "Güçlü Bullish", action: "🟢 LONG" },
      { value: "-DI >> +DI", meaning: isEn ? "Strong Bearish" : "Güçlü Bearish", action: "🔴 SHORT" },
      { value: "+DI ≈ -DI", meaning: isEn ? "Indecisive/Ranging" : "Kararsız/Ranging", action: isEn ? "⚠️ WAIT" : "⚠️ BEKLE" },
    ],
    example: isEn ? "ADX=50, DI Spread=5 → ADX high but no trend, FAKE!" : "ADX=50, DI Spread=5 → ADX yüksek ama trend yok, FAKE!",
    importance: "critical",
  },

  atr: {
    title: "ATR (Average True Range)",
    description: isEn ? "Measures volatility (price fluctuation)." : "Volatiliteyi (fiyat dalgalanmasını) ölçer.",
    usage: isEn ? "Critical for stop loss and position sizing." : "Stop loss ve position sizing için kritik.",
    levels: [
      { value: isEn ? "Low ATR" : "Düşük ATR", meaning: isEn ? "Low Volatility" : "Düşük Volatilite", action: isEn ? "📊 Small SL, large position" : "📊 Küçük SL, büyük pozisyon" },
      { value: isEn ? "Normal ATR" : "Normal ATR", meaning: isEn ? "Normal Market" : "Normal Piyasa", action: isEn ? "✅ Standard parameters" : "✅ Standart parametreler" },
      { value: isEn ? "High ATR" : "Yüksek ATR", meaning: isEn ? "High Volatility" : "Yüksek Volatilite", action: isEn ? "⚠️ Wide SL, small position" : "⚠️ Geniş SL, küçük pozisyon" },
    ],
    example: isEn ? "ATR 30 → SL should be at least 30-45 pips" : "ATR 30 → SL en az 30-45 pip olmalı",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // MTF ANALİZ
  // ═══════════════════════════════════════════════════════════════════

  market_regime: {
    title: isEn ? "Market Regime" : "Market Regime (Piyasa Rejimi)",
    description: isEn ? "Determines market's current state: Trending or Ranging?" : "Piyasanın mevcut durumunu belirler: Trend mi, Range mi?",
    usage: isEn ? "Critical for strategy selection. Trend following in trends, scalping in ranges." : "Strateji seçimi için kritik. Trend piyasada trend takip, range'de scalping.",
    levels: [
      { value: "STRONG_TREND", meaning: isEn ? "Strong Trend" : "Güçlü Trend", action: isEn ? "🚀 Trend following strategy" : "🚀 Trend takip stratejisi" },
      { value: "WEAK_TREND", meaning: isEn ? "Weak Trend" : "Zayıf Trend", action: isEn ? "📊 Careful trend following" : "📊 Dikkatli trend takip" },
      { value: "RANGING", meaning: isEn ? "Sideways Market" : "Yatay Piyasa", action: "📈📉 Range trading" },
      { value: "VOLATILE", meaning: isEn ? "Volatile" : "Volatil", action: isEn ? "⚠️ Small position" : "⚠️ Küçük pozisyon" },
      { value: "CHOPPY", meaning: isEn ? "Choppy" : "Dalgalı", action: isEn ? "🚫 Don't trade" : "🚫 Trade yapma" },
    ],
    importance: "critical",
  },

  liquidity_sweep: {
    title: isEn ? "Liquidity Sweep (Stop Hunt)" : "Liquidity Sweep (Stop Avlama)",
    description: isEn ? "Situation where big players trigger stop losses and reverse." : "Büyük oyuncuların stop loss'ları tetikleyip geri döndüğü durum.",
    usage: isEn ? "Critical for fakeout detection. Trade opposite direction after sweep." : "Fakeout tespiti için kritik. Sweep sonrası ters yöne trade aç.",
    levels: [
      { value: "DETECTED", meaning: isEn ? "Sweep Detected" : "Sweep Tespit Edildi", action: isEn ? "⚠️ Wait for reversal" : "⚠️ Geri dönüşü bekle" },
      { value: "FAKEOUT_TRAP", meaning: isEn ? "Trap Move" : "Tuzak Hareketi", action: "🔴 Confidence ×0.5" },
      { value: "NONE", meaning: isEn ? "Normal Move" : "Normal Hareket", action: isEn ? "✅ Normal trade" : "✅ Normal işlem" },
    ],
    example: isEn ? "Price broke resistance, went 30 pips up, immediately reversed → SWEEP" : "Fiyat direnç kırdı, 30 pip yukarı gitti, hemen geri döndü → SWEEP",
    importance: "critical",
  },

  session: {
    title: isEn ? "Trading Session" : "Trading Session (İşlem Seansı)",
    description: isEn ? "Shows which market is open." : "Hangi piyasanın açık olduğunu gösterir.",
    usage: isEn ? "Each session has different volatility and behavior." : "Her seansın farklı volatilite ve davranışı var.",
    levels: [
      { value: "ASIA", meaning: isEn ? "Tokyo Session" : "Tokyo Seansı", action: isEn ? "⚠️ Low volatility, -15% confidence" : "⚠️ Düşük volatilite, -15% confidence" },
      { value: "LONDON", meaning: isEn ? "London Session" : "Londra Seansı", action: isEn ? "🚀 High volatility, trend start" : "🚀 Yüksek volatilite, trend başlangıcı" },
      { value: "NY", meaning: isEn ? "New York Session" : "New York Seansı", action: isEn ? "⚡ Highest volatility" : "⚡ En yüksek volatilite" },
      { value: "OVERLAP", meaning: isEn ? "London-NY Overlap" : "Londra-NY Kesişimi", action: isEn ? "🔥 Maximum liquidity" : "🔥 Maksimum likidite" },
    ],
    importance: "high",
  },

  pivot_points: {
    title: "Fibonacci Pivot Points",
    description: isEn ? "Intraday support/resistance levels. Calculated with Fibonacci ratios." : "Gün içi destek/direnç seviyeleri. Fibonacci oranlarıyla hesaplanır.",
    usage: isEn ? "Use for entry, exit and stop loss levels." : "Entry, exit ve stop loss seviyeleri için kullan.",
    levels: [
      { value: "R2 (0.618)", meaning: isEn ? "Strong Resistance" : "Güçlü Direnç", action: isEn ? "🔴 Ideal for short" : "🔴 Short için ideal" },
      { value: "R1", meaning: isEn ? "First Resistance" : "İlk Direnç", action: isEn ? "📊 Take profit level" : "📊 Kar al seviyesi" },
      { value: "Pivot", meaning: isEn ? "Balance Point" : "Denge Noktası", action: isEn ? "↔️ Direction determiner" : "↔️ Yön belirleyici" },
      { value: "S1", meaning: isEn ? "First Support" : "İlk Destek", action: isEn ? "📊 Take profit level" : "📊 Kar al seviyesi" },
      { value: "S2 (0.618)", meaning: isEn ? "Strong Support" : "Güçlü Destek", action: isEn ? "🟢 Ideal for long" : "🟢 Long için ideal" },
    ],
    example: isEn ? "Price dropped to S2 + RSI <30 → Strong LONG opportunity" : "Fiyat S2'ye düştü + RSI <30 → Güçlü LONG fırsatı",
    importance: "high",
  },

  hvn_levels: {
    title: isEn ? "HVN (High Volume Node) Levels" : "HVN (High Volume Node) Seviyeleri",
    description: isEn ? "Price levels where most trading volume occurred." : "En çok işlem hacminin gerçekleştiği fiyat seviyeleri.",
    usage: isEn ? "More reliable S/R levels than POC. Price reacts at these levels." : "POC'dan daha güvenilir S/R seviyeleri. Fiyat buralarda tepki verir.",
    levels: [
      { value: "HVN Resistance", meaning: isEn ? "Volume Resistance" : "Hacim Direnci", action: isEn ? "🔴 Strong selling pressure" : "🔴 Satış baskısı güçlü" },
      { value: "HVN Support", meaning: isEn ? "Volume Support" : "Hacim Desteği", action: isEn ? "🟢 Strong buying pressure" : "🟢 Alım baskısı güçlü" },
    ],
    example: isEn ? "Price approached HVN resistance → Reversal expected" : "Fiyat HVN direncine yaklaştı → Geri dönüş beklenir",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // COT & INSTITUTIONAL
  // ═══════════════════════════════════════════════════════════════════

  cot_commercials: {
    title: "COT Commercials (Hedgers)",
    description: isEn ? "Positions of large corporations and hedgers. Known as 'Smart Money'." : "Büyük şirketler ve hedger'ların pozisyonları. 'Smart Money' olarak bilinir.",
    usage: isEn ? "Usually on the right side at trend endings." : "Genellikle trend sonlarında doğru taraftadırlar.",
    levels: [
      { value: "Net Long", meaning: isEn ? "Buying" : "Alım Yapıyorlar", action: isEn ? "🟢 Bullish signal" : "🟢 Bullish sinyal" },
      { value: "Net Short", meaning: isEn ? "Selling" : "Satış Yapıyorlar", action: isEn ? "🔴 Bearish signal" : "🔴 Bearish sinyal" },
    ],
    example: isEn ? "Commercials 50K net long → Strong bullish signal" : "Commercials 50K net long → Güçlü yükseliş sinyali",
    importance: "high",
  },

  cot_speculators: {
    title: "COT Speculators (Funds)",
    description: isEn ? "Positions of hedge funds and speculators. Usually right in the middle of trends." : "Hedge fonlar ve spekülatörlerin pozisyonları. Genellikle trend ortasında doğru.",
    usage: isEn ? "Watch for OPPOSITE direction at extreme positions!" : "Ekstrem pozisyonlarda TERS yöne dikkat et!",
    levels: [
      { value: "< 30% Long", meaning: isEn ? "Extremely Pessimistic" : "Aşırı Pessimist", action: "🟢 Contrarian BUY" },
      { value: "30-70% Long", meaning: "Normal", action: isEn ? "📊 Follow trend" : "📊 Trend takip" },
      { value: "> 80% Long", meaning: isEn ? "Extremely Crowded" : "Aşırı Crowded", action: isEn ? "⚠️ TREND EXHAUSTION risk" : "⚠️ TREND EXHAUSTION riski" },
    ],
    example: isEn ? "Speculators 85% long → Trend end near, be careful!" : "Speculators 85% long → Trend sonu yakın, dikkat!",
    importance: "critical",
  },

  slippage: {
    title: isEn ? "Slippage" : "Slippage (Kayma)",
    description: isEn ? "Difference between signal price and execution price." : "Sinyal fiyatı ile gerçekleşen fiyat arasındaki fark.",
    usage: isEn ? "High slippage = broker issue or volatility too high." : "Yüksek slippage = broker sorunlu veya volatilite çok yüksek.",
    levels: [
      { value: "< 1 pip", meaning: isEn ? "Excellent" : "Mükemmel", action: isEn ? "✅ Normal position" : "✅ Normal pozisyon" },
      { value: "1-3 pip", meaning: isEn ? "Acceptable" : "Kabul Edilebilir", action: isEn ? "📊 Normal trade" : "📊 Normal işlem" },
      { value: "> 3 pip", meaning: isEn ? "High" : "Yüksek", action: isEn ? "⚠️ Reduce position 30%" : "⚠️ Pozisyon %30 azalt" },
      { value: "> 5 pip", meaning: isEn ? "Extreme" : "Aşırı", action: isEn ? "🚫 Don't trade" : "🚫 Trade yapma" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // ML & AI SİNYALLER
  // ═══════════════════════════════════════════════════════════════════

  confidence: {
    title: isEn ? "Signal Confidence" : "Sinyal Güveni (Confidence)",
    description: isEn ? "ML model's confidence percentage in the signal." : "ML modelinin sinyale olan güven yüzdesi.",
    usage: isEn ? "Low confidence = small position or don't trade." : "Düşük güven = küçük pozisyon veya trade yapma.",
    levels: [
      { value: "< 50%", meaning: isEn ? "Low Confidence" : "Düşük Güven", action: isEn ? "🚫 Don't trade" : "🚫 Trade yapma" },
      { value: "50-65%", meaning: isEn ? "Medium Confidence" : "Orta Güven", action: isEn ? "📊 Small position" : "📊 Küçük pozisyon" },
      { value: "65-80%", meaning: isEn ? "Good Confidence" : "İyi Güven", action: isEn ? "✅ Normal position" : "✅ Normal pozisyon" },
      { value: "> 80%", meaning: isEn ? "High Confidence" : "Yüksek Güven", action: isEn ? "🚀 Full position" : "🚀 Tam pozisyon" },
    ],
    importance: "critical",
  },

  direction: {
    title: isEn ? "Signal Direction" : "Sinyal Yönü",
    description: isEn ? "Price direction predicted by ML model." : "ML modelinin tahmin ettiği fiyat yönü.",
    usage: isEn ? "Confirm with other indicators, don't use alone." : "Diğer göstergelerle teyit et, tek başına kullanma.",
    levels: [
      { value: "BUY", meaning: isEn ? "Bullish Expectation" : "Yükseliş Beklentisi", action: isEn ? "🟢 Open LONG position" : "🟢 LONG pozisyon aç" },
      { value: "SELL", meaning: isEn ? "Bearish Expectation" : "Düşüş Beklentisi", action: isEn ? "🔴 Open SHORT position" : "🔴 SHORT pozisyon aç" },
      { value: "HOLD", meaning: isEn ? "Uncertain" : "Belirsiz", action: isEn ? "⏸️ Wait, don't trade" : "⏸️ Bekle, işlem yapma" },
    ],
    importance: "critical",
  },

  risk_reward: {
    title: isEn ? "Risk/Reward Ratio" : "Risk/Reward Oranı",
    description: isEn ? "Potential profit / potential loss ratio." : "Potansiyel kar / potansiyel zarar oranı.",
    usage: isEn ? "Should be minimum 1:2, ideal 1:3+" : "Minimum 1:2 olmalı, ideal 1:3+",
    levels: [
      { value: "< 1:1", meaning: isEn ? "Bad" : "Kötü", action: isEn ? "🚫 Don't trade" : "🚫 Trade yapma" },
      { value: "1:1 - 1:2", meaning: isEn ? "Acceptable" : "Kabul Edilebilir", action: isEn ? "⚠️ Only on strong signals" : "⚠️ Sadece güçlü sinyallerde" },
      { value: "1:2 - 1:3", meaning: isEn ? "Good" : "İyi", action: isEn ? "✅ Normal trade" : "✅ Normal trade" },
      { value: "> 1:3", meaning: isEn ? "Excellent" : "Mükemmel", action: "🚀 Ideal setup" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // HIGH IMPACT EVENTS
  // ═══════════════════════════════════════════════════════════════════

  nfp_day: {
    title: "NFP (Non-Farm Payrolls)",
    description: isEn ? "US employment data. Once a month, most important economic data." : "ABD istihdam verileri. Ayda bir kez, en önemli ekonomik veri.",
    usage: isEn ? "Don't trade on NFP day! Extreme volatility and spread widening." : "NFP günü trade yapma! Aşırı volatilite ve spread genişlemesi.",
    levels: [
      { value: "DETECTED", meaning: isEn ? "NFP Day" : "NFP Günü", action: isEn ? "🚫 DON'T TRADE" : "🚫 TRADE YAPMA" },
    ],
    example: isEn ? "First Friday of each month 8:30 AM EST" : "Her ayın ilk Cuma'sı 15:30 TR saati",
    importance: "critical",
  },

  fomc: {
    title: isEn ? "FOMC (Fed Interest Rate Decision)" : "FOMC (Fed Faiz Kararı)",
    description: isEn ? "Federal Reserve interest rate decision and press conference." : "Federal Reserve faiz kararı ve basın toplantısı.",
    usage: isEn ? "FOMC days are very volatile. Close trades before decision." : "FOMC günleri çok volatil. Karar öncesi trade kapatın.",
    levels: [
      { value: "POTENTIAL", meaning: isEn ? "FOMC Approaching" : "FOMC Yaklaşıyor", action: isEn ? "⚠️ Maximum SMALL position" : "⚠️ Maksimum SMALL pozisyon" },
    ],
    importance: "critical",
  },

  cpi: {
    title: isEn ? "CPI (Inflation Data)" : "CPI (Enflasyon Verisi)",
    description: isEn ? "Consumer Price Index. Measures inflation." : "Tüketici fiyat endeksi. Enflasyonu ölçer.",
    usage: isEn ? "Gold and dollar very volatile on CPI day." : "CPI günü altın ve dolar çok hareketli.",
    levels: [
      { value: "POTENTIAL", meaning: isEn ? "CPI Approaching" : "CPI Yaklaşıyor", action: isEn ? "⚠️ Be careful" : "⚠️ Dikkatli ol" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // CORRELATION
  // ═══════════════════════════════════════════════════════════════════

  dxy_correlation: {
    title: isEn ? "DXY (Dollar Index) Correlation" : "DXY (Dolar Endeksi) Korelasyonu",
    description: isEn ? "Negative correlation with XAUUSD. If DXY rises, gold falls." : "XAUUSD ile negatif korelasyon. DXY yükselirse altın düşer.",
    usage: isEn ? "If signal conflicts with DXY, reduce confidence." : "Sinyal ile DXY çelişiyorsa güveni azalt.",
    levels: [
      { value: "CONFIRMS", meaning: isEn ? "Signal Confirmed" : "Sinyal Teyit", action: isEn ? "✅ Increase confidence" : "✅ Güven artır" },
      { value: "CONFLICTS", meaning: isEn ? "Conflict Exists" : "Çelişki Var", action: "⚠️ Confidence -25%" },
    ],
    importance: "high",
  },

  vix: {
    title: isEn ? "VIX (Fear Index)" : "VIX (Korku Endeksi)",
    description: isEn ? "Market volatility and risk appetite indicator." : "Piyasa volatilitesi ve risk iştahı göstergesi.",
    usage: isEn ? "When VIX is high, risk off, gold rises." : "VIX yüksekken risk off, altın yükselir.",
    levels: [
      { value: "< 15", meaning: isEn ? "Low Fear" : "Düşük Korku", action: isEn ? "📈 Risk on, buy stocks" : "📈 Risk on, hisse al" },
      { value: "15-25", meaning: "Normal", action: isEn ? "📊 Normal trading" : "📊 Normal işlem" },
      { value: "> 25", meaning: isEn ? "High Fear" : "Yüksek Korku", action: isEn ? "⚠️ Risk off, gold strong" : "⚠️ Risk off, altın güçlü" },
      { value: "> 35", meaning: isEn ? "Panic" : "Panik", action: isEn ? "🚨 Gold very strong" : "🚨 Altın çok güçlü" },
    ],
    importance: "medium",
  },

  // ═══════════════════════════════════════════════════════════════════
  // PATTERN & STRUCTURE
  // ═══════════════════════════════════════════════════════════════════

  order_block: {
    title: isEn ? "Order Block" : "Order Block (Emir Bloğu)",
    description: isEn ? "Footprints left by large institutional orders." : "Büyük kurumsal emirlerin bıraktığı ayak izleri.",
    usage: isEn ? "Price reaction expected when returning to order block." : "Fiyat order block'a döndüğünde tepki beklenir.",
    levels: [
      { value: "Bullish OB", meaning: isEn ? "Buy Zone" : "Alım Bölgesi", action: isEn ? "🟢 Wait for long" : "🟢 Long için bekle" },
      { value: "Bearish OB", meaning: isEn ? "Sell Zone" : "Satım Bölgesi", action: isEn ? "🔴 Wait for short" : "🔴 Short için bekle" },
    ],
    importance: "high",
  },

  fvg: {
    title: "FVG (Fair Value Gap)",
    description: isEn ? "Area where price passed leaving a gap. Expected to be filled." : "Fiyatın boşluk bırakarak geçtiği bölge. Doldurulması beklenir.",
    usage: isEn ? "Price usually returns to fill the FVG." : "Fiyat genellikle FVG'yi doldurmak için geri döner.",
    levels: [
      { value: "Bullish FVG", meaning: isEn ? "Gap Below" : "Aşağıda Boşluk", action: isEn ? "🟢 Acts as support" : "🟢 Destek görevi görür" },
      { value: "Bearish FVG", meaning: isEn ? "Gap Above" : "Yukarıda Boşluk", action: isEn ? "🔴 Acts as resistance" : "🔴 Direnç görevi görür" },
    ],
    importance: "medium",
  },

  equal_highs_lows: {
    title: isEn ? "Equal Highs/Lows" : "Equal Highs/Lows (Eşit Tepeler/Dipler)",
    description: isEn ? "Price touching the same level multiple times." : "Fiyatın aynı seviyeye birden fazla kez dokunması.",
    usage: isEn ? "Stop losses accumulate here. Target for sweep!" : "Buralarda stop loss'lar birikir. Sweep için hedef!",
    levels: [
      { value: "Equal Highs", meaning: isEn ? "Liquidity Pool (Top)" : "Likidite Havuzu (Üst)", action: isEn ? "⚠️ Fake breakout risk" : "⚠️ Fake breakout riski" },
      { value: "Equal Lows", meaning: isEn ? "Liquidity Pool (Bottom)" : "Likidite Havuzu (Alt)", action: isEn ? "⚠️ Fake breakdown risk" : "⚠️ Fake breakdown riski" },
    ],
    example: isEn ? "Touched same resistance 3 times → Sweep coming" : "3 kez aynı dirençe dokundu → Sweep gelecek",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // POSITION SIZING
  // ═══════════════════════════════════════════════════════════════════

  position_size: {
    title: isEn ? "Position Size" : "Pozisyon Büyüklüğü",
    description: isEn ? "Lot amount calculated based on risk management." : "Risk yönetimine göre hesaplanan lot miktarı.",
    usage: isEn ? "Don't risk more than 1-2% of account balance." : "Hesap bakiyesinin %1-2'sinden fazla riske girme.",
    levels: [
      { value: "SMALL", meaning: isEn ? "Small Position" : "Küçük Pozisyon", action: "📊 0.5% risk" },
      { value: "MEDIUM", meaning: isEn ? "Normal Position" : "Normal Pozisyon", action: "✅ 1% risk" },
      { value: "LARGE", meaning: isEn ? "Large Position" : "Büyük Pozisyon", action: "⚠️ 2% risk (max)" },
    ],
    importance: "critical",
  },

  volatility_adjustment: {
    title: isEn ? "Volatility Adjustment" : "Volatilite Ayarlaması",
    description: isEn ? "Position size adjustment based on ATR." : "ATR'ye göre pozisyon büyüklüğü ayarı.",
    usage: isEn ? "Reduce position in high volatility." : "Yüksek volatilitede pozisyonu küçült.",
    levels: [
      { value: "> 1.0", meaning: isEn ? "Low Volatility" : "Düşük Volatilite", action: isEn ? "📈 Can increase position" : "📈 Pozisyon büyütülebilir" },
      { value: "0.7-1.0", meaning: "Normal", action: isEn ? "✅ Standard position" : "✅ Standart pozisyon" },
      { value: "< 0.7", meaning: isEn ? "High Volatility" : "Yüksek Volatilite", action: isEn ? "⚠️ Reduce position" : "⚠️ Pozisyon küçült" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // CANDLESTICK PATTERNS (MUM FORMASYONLARI)
  // ═══════════════════════════════════════════════════════════════════

  candlestick_engulfing: {
    title: isEn ? "Engulfing Pattern" : "Engulfing (Yutan Formasyon)",
    description: isEn ? "Large candle completely covering previous candle's body. Strong reversal signal." : "Önceki mumun gövdesini tamamen kaplayan büyük mum. Güçlü dönüş sinyali.",
    usage: isEn ? "Use at trend reversals. More reliable at support/resistance." : "Trend dönüşlerinde kullan. Destek/dirençte daha güvenilir.",
    levels: [
      { value: "Bullish Engulfing", meaning: isEn ? "Green candle engulfs red" : "Yeşil mum kırmızıyı yutar", action: isEn ? "🟢 Look for LONG" : "🟢 LONG ara" },
      { value: "Bearish Engulfing", meaning: isEn ? "Red candle engulfs green" : "Kırmızı mum yeşili yutar", action: isEn ? "🔴 Look for SHORT" : "🔴 SHORT ara" },
    ],
    example: isEn ? "Large green candle after downtrend → Reversal starting" : "Düşüş sonrası büyük yeşil mum → Dönüş başlıyor",
    importance: "high",
  },

  candlestick_hammer: {
    title: isEn ? "Hammer" : "Hammer (Çekiç)",
    description: isEn ? "Small body, long lower wick (2x+ body). Buyers rejected low prices." : "Küçük gövde, uzun alt fitil (gövdenin 2+ katı). Alıcılar düşük fiyatları reddetti.",
    usage: isEn ? "Look at end of downtrend. Wait for confirmation candle." : "Düşüş trendi sonunda ara. Onay mumu bekle.",
    levels: [
      { value: "Hammer", meaning: isEn ? "Hammer at bottom" : "Dipte çekiç", action: isEn ? "🟢 Potential bottom" : "🟢 Potansiyel dip" },
      { value: "Hanging Man", meaning: isEn ? "Hammer at top" : "Tepede çekiç", action: isEn ? "🔴 Potential top" : "🔴 Potansiyel tepe" },
    ],
    example: isEn ? "Hammer at support level → Prepare for LONG" : "Destek seviyesinde hammer → LONG için hazırlan",
    importance: "high",
  },

  candlestick_doji: {
    title: "Doji",
    description: isEn ? "Open = Close. Market indecision." : "Açılış = Kapanış. Piyasada kararsızlık var.",
    usage: isEn ? "Not a signal alone! Wait for next candle." : "Tek başına sinyal değil! Sonraki mumu bekle.",
    levels: [
      { value: "Normal Doji", meaning: isEn ? "Indecision" : "Kararsızlık", action: isEn ? "⏸️ Wait" : "⏸️ Bekle" },
      { value: "Dragonfly Doji", meaning: isEn ? "Long lower wick at bottom" : "Dipte uzun alt fitil", action: isEn ? "🟢 Bullish potential" : "🟢 Bullish potansiyel" },
      { value: "Gravestone Doji", meaning: isEn ? "Long upper wick at top" : "Tepede uzun üst fitil", action: isEn ? "🔴 Bearish potential" : "🔴 Bearish potansiyel" },
    ],
    importance: "medium",
  },

  candlestick_harami: {
    title: "Harami",
    description: isEn ? "Small candle stays inside previous large candle's body." : "Küçük mum, önceki büyük mumun gövdesi içinde kalır. Hamile anlamına gelir.",
    usage: isEn ? "Trend reversal signal but confirmation needed." : "Trend dönüş sinyali ama onay gerekli.",
    levels: [
      { value: "Bullish Harami", meaning: isEn ? "Small green after downtrend" : "Düşüş sonrası küçük yeşil", action: isEn ? "🟢 Reversal may be starting" : "🟢 Dönüş başlıyor olabilir" },
      { value: "Bearish Harami", meaning: isEn ? "Small red after uptrend" : "Yükseliş sonrası küçük kırmızı", action: isEn ? "🔴 Reversal may be starting" : "🔴 Dönüş başlıyor olabilir" },
    ],
    importance: "medium",
  },

  candlestick_star: {
    title: isEn ? "Morning/Evening Star" : "Morning/Evening Star (Sabah/Akşam Yıldızı)",
    description: isEn ? "3-candle strong reversal pattern. Middle small candle is the 'star'." : "3 mumlu güçlü dönüş formasyonu. Ortadaki küçük mum 'yıldız'.",
    usage: isEn ? "One of the most reliable reversal patterns." : "En güvenilir dönüş formasyonlarından biri.",
    levels: [
      { value: "Morning Star", meaning: isEn ? "Big red → Small → Big green" : "Büyük kırmızı → Küçük → Büyük yeşil", action: isEn ? "🟢 Strong LONG" : "🟢 Güçlü LONG" },
      { value: "Evening Star", meaning: isEn ? "Big green → Small → Big red" : "Büyük yeşil → Küçük → Büyük kırmızı", action: isEn ? "🔴 Strong SHORT" : "🔴 Güçlü SHORT" },
    ],
    example: isEn ? "Support + Morning Star = 90% reliable LONG" : "Destek + Morning Star = %90 güvenilir LONG",
    importance: "critical",
  },

  candlestick_shooting_star: {
    title: isEn ? "Shooting Star" : "Shooting Star (Kayan Yıldız)",
    description: isEn ? "Small body at bottom, long upper wick. Sellers rejected high prices." : "Küçük gövde altta, uzun üst fitil. Satıcılar yüksek fiyatları reddetti.",
    usage: isEn ? "Look at top of uptrend." : "Yükseliş trendi tepesinde ara.",
    levels: [
      { value: "Shooting Star", meaning: isEn ? "Long upper wick at top" : "Tepede uzun üst fitil", action: isEn ? "🔴 Reversal warning" : "🔴 Dönüş uyarısı" },
      { value: "Inverted Hammer", meaning: isEn ? "Long upper wick at bottom" : "Dipte uzun üst fitil", action: isEn ? "🟢 Potential reversal" : "🟢 Potansiyel dönüş" },
    ],
    importance: "high",
  },

  candlestick_soldiers_crows: {
    title: "Three White Soldiers / Black Crows",
    description: isEn 
      ? "3 consecutive strong candles. Trend start or continuation."
      : "Üst üste 3 güçlü mum. Trend başlangıcı veya devamı.",
    usage: isEn 
      ? "Momentum signal. Trade with the trend."
      : "Momentum sinyali. Trendle işlem aç.",
    levels: [
      { value: "3 White Soldiers", meaning: isEn ? "3 green candles rising" : "3 yeşil mum yükseliyor", action: isEn ? "🟢 Strong uptrend started" : "🟢 Güçlü yükseliş başladı" },
      { value: "3 Black Crows", meaning: isEn ? "3 red candles falling" : "3 kırmızı mum düşüyor", action: isEn ? "🔴 Strong downtrend started" : "🔴 Güçlü düşüş başladı" },
    ],
    importance: "high",
  },
  };
}

// Legacy export for compatibility
export const TRADING_INFO = getTradingInfo("tr");

// ═══════════════════════════════════════════════════════════════════
// INFO MODAL COMPONENT
// ═══════════════════════════════════════════════════════════════════

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  infoKey: string;
  customData?: Partial<InfoData>;
}

export function InfoModal({ isOpen, onClose, infoKey, customData }: InfoModalProps) {
  const { t, locale } = useI18nStore();
  const tradingInfo = getTradingInfo(locale);
  const info = customData || tradingInfo[infoKey];
  
  if (!isOpen || !info) return null;

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case "critical": return "bg-red-500/20 text-red-400 border-red-500/30";
      case "high": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
      case "medium": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  const getImportanceLabel = (importance: string) => {
    switch (importance) {
      case "critical": return t("infoTooltip.importance.critical");
      case "high": return t("infoTooltip.importance.high");
      case "medium": return t("infoTooltip.importance.medium");
      default: return t("infoTooltip.importance.low");
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop with blur */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      
      {/* Modal */}
      <div 
        className="relative bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl max-w-lg w-full max-h-[80vh] overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 px-5 py-4 border-b border-gray-700/50">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Info className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">{info.title}</h3>
              </div>
              <span className={`inline-block text-xs px-2 py-0.5 rounded border ${getImportanceColor(info.importance)}`}>
                {getImportanceLabel(info.importance)} {t("infoTooltip.importanceLabel")}
              </span>
            </div>
            <button 
              onClick={onClose}
              className="p-1 hover:bg-gray-700/50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto max-h-[60vh] space-y-4">
          {/* Description */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-1">📖 {t("infoTooltip.description")}</h4>
            <p className="text-sm text-gray-400">{info.description}</p>
          </div>

          {/* Usage */}
          <div>
            <h4 className="text-sm font-semibold text-gray-300 mb-1">🎯 {t("infoTooltip.usage")}</h4>
            <p className="text-sm text-gray-400">{info.usage}</p>
          </div>

          {/* Levels */}
          {info.levels && info.levels.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-2">📊 {t("infoTooltip.levelsAndActions")}</h4>
              <div className="space-y-2">
                {info.levels.map((level, idx) => (
                  <div 
                    key={idx}
                    className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/30"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-mono text-cyan-400">{level.value}</span>
                      <span className="text-xs text-gray-400">{level.meaning}</span>
                    </div>
                    <div className="text-sm text-white">{level.action}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Example */}
          {info.example && (
            <div className="bg-blue-900/20 rounded-lg p-3 border border-blue-500/20">
              <h4 className="text-sm font-semibold text-blue-400 mb-1">💡 {t("infoTooltip.example")}</h4>
              <p className="text-sm text-gray-300">{info.example}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-800/50 px-5 py-3 border-t border-gray-700/50">
          <p className="text-xs text-gray-500 text-center">
            {t("infoTooltip.closeHint")}
          </p>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// CLICKABLE INFO WRAPPER
// ═══════════════════════════════════════════════════════════════════

interface InfoClickableProps {
  infoKey: string;
  children: ReactNode;
  className?: string;
  customData?: Partial<InfoData>;
}

export function InfoClickable({ infoKey, children, className = "", customData }: InfoClickableProps) {
  const { t, locale } = useI18nStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <span 
        className={`cursor-help hover:opacity-80 transition-opacity ${className}`}
        onClick={() => setIsOpen(true)}
        title={locale === "en" ? "Click for info" : "Bilgi için tıklayın"}
      >
        {children}
      </span>
      <InfoModal 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
        infoKey={infoKey}
        customData={customData}
      />
    </>
  );
}

// ═══════════════════════════════════════════════════════════════════
// INFO BADGE (Small clickable badge with ? icon)
// ═══════════════════════════════════════════════════════════════════

interface InfoBadgeProps {
  infoKey: string;
  className?: string;
}

export function InfoBadge({ infoKey, className = "" }: InfoBadgeProps) {
  const { locale } = useI18nStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className={`inline-flex items-center justify-center w-4 h-4 rounded-full bg-gray-700/50 hover:bg-gray-600/50 transition-colors ${className}`}
        title={locale === "en" ? "Click for info" : "Bilgi için tıklayın"}
      >
        <HelpCircle className="w-3 h-3 text-gray-400" />
      </button>
      <InfoModal 
        isOpen={isOpen} 
        onClose={() => setIsOpen(false)} 
        infoKey={infoKey}
      />
    </>
  );
}

export default InfoClickable;
