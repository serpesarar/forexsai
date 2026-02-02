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

export const TRADING_INFO: Record<string, InfoData> = {
  // ═══════════════════════════════════════════════════════════════════
  // TEMEL GÖSTERGELER
  // ═══════════════════════════════════════════════════════════════════
  
  rsi: {
    title: "RSI (Relative Strength Index)",
    description: "Fiyatın aşırı alım veya aşırı satım bölgesinde olup olmadığını gösteren momentum göstergesi.",
    usage: "Trend dönüşlerini ve aşırı hareketleri tespit etmek için kullanılır.",
    levels: [
      { value: "< 30", meaning: "Aşırı Satım", action: "🟢 LONG fırsatı ara" },
      { value: "30-50", meaning: "Zayıf/Düşüş", action: "⚠️ Dikkatli ol" },
      { value: "50-70", meaning: "Güçlü/Yükseliş", action: "📈 Trend devam" },
      { value: "> 70", meaning: "Aşırı Alım", action: "🔴 SHORT fırsatı ara" },
    ],
    example: "RSI 25 → Fiyat çok düştü, toparlanma gelebilir",
    importance: "high",
  },

  macd: {
    title: "MACD (Moving Average Convergence Divergence)",
    description: "İki hareketli ortalama arasındaki farkı gösteren trend takip göstergesi.",
    usage: "Trend yönü ve momentum değişimlerini tespit eder.",
    levels: [
      { value: "MACD > Signal", meaning: "Bullish Crossover", action: "🟢 LONG sinyali" },
      { value: "MACD < Signal", meaning: "Bearish Crossover", action: "🔴 SHORT sinyali" },
      { value: "Histogram +", meaning: "Yükseliş momentumu", action: "📈 Trend güçleniyor" },
      { value: "Histogram -", meaning: "Düşüş momentumu", action: "📉 Trend zayıflıyor" },
    ],
    example: "MACD signal'ı yukarı keserse → BUY sinyali",
    importance: "high",
  },

  adx: {
    title: "ADX (Average Directional Index)",
    description: "Trendin gücünü ölçer (yön göstermez, sadece güç).",
    usage: "Piyasanın trendde mi yoksa yatay mı olduğunu anlamak için.",
    levels: [
      { value: "< 20", meaning: "Zayıf/Yatay Piyasa", action: "⚠️ Range trading yap" },
      { value: "20-40", meaning: "Gelişen Trend", action: "📊 Trend takip et" },
      { value: "40-60", meaning: "Güçlü Trend", action: "🚀 Trendle git" },
      { value: "> 60", meaning: "Aşırı Güçlü Trend", action: "⚡ Dikkat, tükenme yakın" },
    ],
    example: "ADX 50 + DI+ > DI- → Güçlü yükseliş trendi",
    importance: "critical",
  },

  di_spread: {
    title: "DI Spread (+DI / -DI Farkı)",
    description: "Trendin yönünü ve gücünü birlikte gösteren ADX bileşeni.",
    usage: "ADX yüksek ama DI spread düşükse → Gerçek trend yok!",
    levels: [
      { value: "+DI >> -DI", meaning: "Güçlü Bullish", action: "🟢 LONG" },
      { value: "-DI >> +DI", meaning: "Güçlü Bearish", action: "🔴 SHORT" },
      { value: "+DI ≈ -DI", meaning: "Kararsız/Ranging", action: "⚠️ BEKLE" },
    ],
    example: "ADX=50, DI Spread=5 → ADX yüksek ama trend yok, FAKE!",
    importance: "critical",
  },

  atr: {
    title: "ATR (Average True Range)",
    description: "Volatiliteyi (fiyat dalgalanmasını) ölçer.",
    usage: "Stop loss ve position sizing için kritik.",
    levels: [
      { value: "Düşük ATR", meaning: "Düşük Volatilite", action: "📊 Küçük SL, büyük pozisyon" },
      { value: "Normal ATR", meaning: "Normal Piyasa", action: "✅ Standart parametreler" },
      { value: "Yüksek ATR", meaning: "Yüksek Volatilite", action: "⚠️ Geniş SL, küçük pozisyon" },
    ],
    example: "ATR 30 → SL en az 30-45 pip olmalı",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // MTF ANALİZ
  // ═══════════════════════════════════════════════════════════════════

  market_regime: {
    title: "Market Regime (Piyasa Rejimi)",
    description: "Piyasanın mevcut durumunu belirler: Trend mi, Range mi?",
    usage: "Strateji seçimi için kritik. Trend piyasada trend takip, range'de scalping.",
    levels: [
      { value: "STRONG_TREND", meaning: "Güçlü Trend", action: "🚀 Trend takip stratejisi" },
      { value: "WEAK_TREND", meaning: "Zayıf Trend", action: "📊 Dikkatli trend takip" },
      { value: "RANGING", meaning: "Yatay Piyasa", action: "📈📉 Range trading" },
      { value: "VOLATILE", meaning: "Volatil", action: "⚠️ Küçük pozisyon" },
      { value: "CHOPPY", meaning: "Dalgalı", action: "🚫 Trade yapma" },
    ],
    importance: "critical",
  },

  liquidity_sweep: {
    title: "Liquidity Sweep (Stop Avlama)",
    description: "Büyük oyuncuların stop loss'ları tetikleyip geri döndüğü durum.",
    usage: "Fakeout tespiti için kritik. Sweep sonrası ters yöne trade aç.",
    levels: [
      { value: "DETECTED", meaning: "Sweep Tespit Edildi", action: "⚠️ Geri dönüşü bekle" },
      { value: "FAKEOUT_TRAP", meaning: "Tuzak Hareketi", action: "🔴 Confidence ×0.5" },
      { value: "NONE", meaning: "Normal Hareket", action: "✅ Normal işlem" },
    ],
    example: "Fiyat direnç kırdı, 30 pip yukarı gitti, hemen geri döndü → SWEEP",
    importance: "critical",
  },

  session: {
    title: "Trading Session (İşlem Seansı)",
    description: "Hangi piyasanın açık olduğunu gösterir.",
    usage: "Her seansın farklı volatilite ve davranışı var.",
    levels: [
      { value: "ASIA", meaning: "Tokyo Seansı", action: "⚠️ Düşük volatilite, -15% confidence" },
      { value: "LONDON", meaning: "Londra Seansı", action: "🚀 Yüksek volatilite, trend başlangıcı" },
      { value: "NY", meaning: "New York Seansı", action: "⚡ En yüksek volatilite" },
      { value: "OVERLAP", meaning: "Londra-NY Kesişimi", action: "🔥 Maksimum likidite" },
    ],
    importance: "high",
  },

  pivot_points: {
    title: "Fibonacci Pivot Points",
    description: "Gün içi destek/direnç seviyeleri. Fibonacci oranlarıyla hesaplanır.",
    usage: "Entry, exit ve stop loss seviyeleri için kullan.",
    levels: [
      { value: "R2 (0.618)", meaning: "Güçlü Direnç", action: "🔴 Short için ideal" },
      { value: "R1", meaning: "İlk Direnç", action: "📊 Kar al seviyesi" },
      { value: "Pivot", meaning: "Denge Noktası", action: "↔️ Yön belirleyici" },
      { value: "S1", meaning: "İlk Destek", action: "📊 Kar al seviyesi" },
      { value: "S2 (0.618)", meaning: "Güçlü Destek", action: "🟢 Long için ideal" },
    ],
    example: "Fiyat S2'ye düştü + RSI <30 → Güçlü LONG fırsatı",
    importance: "high",
  },

  hvn_levels: {
    title: "HVN (High Volume Node) Seviyeleri",
    description: "En çok işlem hacminin gerçekleştiği fiyat seviyeleri.",
    usage: "POC'dan daha güvenilir S/R seviyeleri. Fiyat buralarda tepki verir.",
    levels: [
      { value: "HVN Resistance", meaning: "Hacim Direnci", action: "🔴 Satış baskısı güçlü" },
      { value: "HVN Support", meaning: "Hacim Desteği", action: "🟢 Alım baskısı güçlü" },
    ],
    example: "Fiyat HVN direncine yaklaştı → Geri dönüş beklenir",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // COT & INSTITUTIONAL
  // ═══════════════════════════════════════════════════════════════════

  cot_commercials: {
    title: "COT Commercials (Hedgers)",
    description: "Büyük şirketler ve hedger'ların pozisyonları. 'Smart Money' olarak bilinir.",
    usage: "Genellikle trend sonlarında doğru taraftadırlar.",
    levels: [
      { value: "Net Long", meaning: "Alım Yapıyorlar", action: "🟢 Bullish sinyal" },
      { value: "Net Short", meaning: "Satış Yapıyorlar", action: "🔴 Bearish sinyal" },
    ],
    example: "Commercials 50K net long → Güçlü yükseliş sinyali",
    importance: "high",
  },

  cot_speculators: {
    title: "COT Speculators (Funds)",
    description: "Hedge fonlar ve spekülatörlerin pozisyonları. Genellikle trend ortasında doğru.",
    usage: "Ekstrem pozisyonlarda TERS yöne dikkat et!",
    levels: [
      { value: "< 30% Long", meaning: "Aşırı Pessimist", action: "🟢 Contrarian BUY" },
      { value: "30-70% Long", meaning: "Normal", action: "📊 Trend takip" },
      { value: "> 80% Long", meaning: "Aşırı Crowded", action: "⚠️ TREND EXHAUSTION riski" },
    ],
    example: "Speculators 85% long → Trend sonu yakın, dikkat!",
    importance: "critical",
  },

  slippage: {
    title: "Slippage (Kayma)",
    description: "Sinyal fiyatı ile gerçekleşen fiyat arasındaki fark.",
    usage: "Yüksek slippage = broker sorunlu veya volatilite çok yüksek.",
    levels: [
      { value: "< 1 pip", meaning: "Mükemmel", action: "✅ Normal pozisyon" },
      { value: "1-3 pip", meaning: "Kabul Edilebilir", action: "📊 Normal işlem" },
      { value: "> 3 pip", meaning: "Yüksek", action: "⚠️ Pozisyon %30 azalt" },
      { value: "> 5 pip", meaning: "Aşırı", action: "🚫 Trade yapma" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // ML & AI SİNYALLER
  // ═══════════════════════════════════════════════════════════════════

  confidence: {
    title: "Sinyal Güveni (Confidence)",
    description: "ML modelinin sinyale olan güven yüzdesi.",
    usage: "Düşük güven = küçük pozisyon veya trade yapma.",
    levels: [
      { value: "< 50%", meaning: "Düşük Güven", action: "🚫 Trade yapma" },
      { value: "50-65%", meaning: "Orta Güven", action: "📊 Küçük pozisyon" },
      { value: "65-80%", meaning: "İyi Güven", action: "✅ Normal pozisyon" },
      { value: "> 80%", meaning: "Yüksek Güven", action: "🚀 Tam pozisyon" },
    ],
    importance: "critical",
  },

  direction: {
    title: "Sinyal Yönü",
    description: "ML modelinin tahmin ettiği fiyat yönü.",
    usage: "Diğer göstergelerle teyit et, tek başına kullanma.",
    levels: [
      { value: "BUY", meaning: "Yükseliş Beklentisi", action: "🟢 LONG pozisyon aç" },
      { value: "SELL", meaning: "Düşüş Beklentisi", action: "🔴 SHORT pozisyon aç" },
      { value: "HOLD", meaning: "Belirsiz", action: "⏸️ Bekle, işlem yapma" },
    ],
    importance: "critical",
  },

  risk_reward: {
    title: "Risk/Reward Oranı",
    description: "Potansiyel kar / potansiyel zarar oranı.",
    usage: "Minimum 1:2 olmalı, ideal 1:3+",
    levels: [
      { value: "< 1:1", meaning: "Kötü", action: "🚫 Trade yapma" },
      { value: "1:1 - 1:2", meaning: "Kabul Edilebilir", action: "⚠️ Sadece güçlü sinyallerde" },
      { value: "1:2 - 1:3", meaning: "İyi", action: "✅ Normal trade" },
      { value: "> 1:3", meaning: "Mükemmel", action: "🚀 Ideal setup" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // HIGH IMPACT EVENTS
  // ═══════════════════════════════════════════════════════════════════

  nfp_day: {
    title: "NFP (Non-Farm Payrolls)",
    description: "ABD istihdam verileri. Ayda bir kez, en önemli ekonomik veri.",
    usage: "NFP günü trade yapma! Aşırı volatilite ve spread genişlemesi.",
    levels: [
      { value: "DETECTED", meaning: "NFP Günü", action: "🚫 TRADE YAPMA" },
    ],
    example: "Her ayın ilk Cuma'sı 15:30 TR saati",
    importance: "critical",
  },

  fomc: {
    title: "FOMC (Fed Faiz Kararı)",
    description: "Federal Reserve faiz kararı ve basın toplantısı.",
    usage: "FOMC günleri çok volatil. Karar öncesi trade kapatın.",
    levels: [
      { value: "POTENTIAL", meaning: "FOMC Yaklaşıyor", action: "⚠️ Maksimum SMALL pozisyon" },
    ],
    importance: "critical",
  },

  cpi: {
    title: "CPI (Enflasyon Verisi)",
    description: "Tüketici fiyat endeksi. Enflasyonu ölçer.",
    usage: "CPI günü altın ve dolar çok hareketli.",
    levels: [
      { value: "POTENTIAL", meaning: "CPI Yaklaşıyor", action: "⚠️ Dikkatli ol" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // CORRELATION
  // ═══════════════════════════════════════════════════════════════════

  dxy_correlation: {
    title: "DXY (Dolar Endeksi) Korelasyonu",
    description: "XAUUSD ile negatif korelasyon. DXY yükselirse altın düşer.",
    usage: "Sinyal ile DXY çelişiyorsa güveni azalt.",
    levels: [
      { value: "CONFIRMS", meaning: "Sinyal Teyit", action: "✅ Güven artır" },
      { value: "CONFLICTS", meaning: "Çelişki Var", action: "⚠️ Confidence -25%" },
    ],
    importance: "high",
  },

  vix: {
    title: "VIX (Korku Endeksi)",
    description: "Piyasa volatilitesi ve risk iştahı göstergesi.",
    usage: "VIX yüksekken risk off, altın yükselir.",
    levels: [
      { value: "< 15", meaning: "Düşük Korku", action: "📈 Risk on, hisse al" },
      { value: "15-25", meaning: "Normal", action: "📊 Normal işlem" },
      { value: "> 25", meaning: "Yüksek Korku", action: "⚠️ Risk off, altın güçlü" },
      { value: "> 35", meaning: "Panik", action: "🚨 Altın çok güçlü" },
    ],
    importance: "medium",
  },

  // ═══════════════════════════════════════════════════════════════════
  // PATTERN & STRUCTURE
  // ═══════════════════════════════════════════════════════════════════

  order_block: {
    title: "Order Block (Emir Bloğu)",
    description: "Büyük kurumsal emirlerin bıraktığı ayak izleri.",
    usage: "Fiyat order block'a döndüğünde tepki beklenir.",
    levels: [
      { value: "Bullish OB", meaning: "Alım Bölgesi", action: "🟢 Long için bekle" },
      { value: "Bearish OB", meaning: "Satım Bölgesi", action: "🔴 Short için bekle" },
    ],
    importance: "high",
  },

  fvg: {
    title: "FVG (Fair Value Gap)",
    description: "Fiyatın boşluk bırakarak geçtiği bölge. Doldurulması beklenir.",
    usage: "Fiyat genellikle FVG'yi doldurmak için geri döner.",
    levels: [
      { value: "Bullish FVG", meaning: "Aşağıda Boşluk", action: "🟢 Destek görevi görür" },
      { value: "Bearish FVG", meaning: "Yukarıda Boşluk", action: "🔴 Direnç görevi görür" },
    ],
    importance: "medium",
  },

  equal_highs_lows: {
    title: "Equal Highs/Lows (Eşit Tepeler/Dipler)",
    description: "Fiyatın aynı seviyeye birden fazla kez dokunması.",
    usage: "Buralarda stop loss'lar birikir. Sweep için hedef!",
    levels: [
      { value: "Equal Highs", meaning: "Likidite Havuzu (Üst)", action: "⚠️ Fake breakout riski" },
      { value: "Equal Lows", meaning: "Likidite Havuzu (Alt)", action: "⚠️ Fake breakdown riski" },
    ],
    example: "3 kez aynı dirençe dokundu → Sweep gelecek",
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // POSITION SIZING
  // ═══════════════════════════════════════════════════════════════════

  position_size: {
    title: "Pozisyon Büyüklüğü",
    description: "Risk yönetimine göre hesaplanan lot miktarı.",
    usage: "Hesap bakiyesinin %1-2'sinden fazla riske girme.",
    levels: [
      { value: "SMALL", meaning: "Küçük Pozisyon", action: "📊 %0.5 risk" },
      { value: "MEDIUM", meaning: "Normal Pozisyon", action: "✅ %1 risk" },
      { value: "LARGE", meaning: "Büyük Pozisyon", action: "⚠️ %2 risk (max)" },
    ],
    importance: "critical",
  },

  volatility_adjustment: {
    title: "Volatilite Ayarlaması",
    description: "ATR'ye göre pozisyon büyüklüğü ayarı.",
    usage: "Yüksek volatilitede pozisyonu küçült.",
    levels: [
      { value: "> 1.0", meaning: "Düşük Volatilite", action: "📈 Pozisyon büyütülebilir" },
      { value: "0.7-1.0", meaning: "Normal", action: "✅ Standart pozisyon" },
      { value: "< 0.7", meaning: "Yüksek Volatilite", action: "⚠️ Pozisyon küçült" },
    ],
    importance: "high",
  },

  // ═══════════════════════════════════════════════════════════════════
  // CANDLESTICK PATTERNS (MUM FORMASYONLARI)
  // ═══════════════════════════════════════════════════════════════════

  candlestick_engulfing: {
    title: "Engulfing (Yutan Formasyon)",
    description: "Önceki mumun gövdesini tamamen kaplayan büyük mum. Güçlü dönüş sinyali.",
    usage: "Trend dönüşlerinde kullan. Destek/dirençte daha güvenilir.",
    levels: [
      { value: "Bullish Engulfing", meaning: "Yeşil mum kırmızıyı yutar", action: "🟢 LONG ara" },
      { value: "Bearish Engulfing", meaning: "Kırmızı mum yeşili yutar", action: "🔴 SHORT ara" },
    ],
    example: "Düşüş sonrası büyük yeşil mum → Dönüş başlıyor",
    importance: "high",
  },

  candlestick_hammer: {
    title: "Hammer (Çekiç)",
    description: "Küçük gövde, uzun alt fitil (gövdenin 2+ katı). Alıcılar düşük fiyatları reddetti.",
    usage: "Düşüş trendi sonunda ara. Onay mumu bekle.",
    levels: [
      { value: "Hammer", meaning: "Dipte çekiç", action: "🟢 Potansiyel dip" },
      { value: "Hanging Man", meaning: "Tepede çekiç", action: "🔴 Potansiyel tepe" },
    ],
    example: "Destek seviyesinde hammer → LONG için hazırlan",
    importance: "high",
  },

  candlestick_doji: {
    title: "Doji",
    description: "Açılış = Kapanış. Piyasada kararsızlık var.",
    usage: "Tek başına sinyal değil! Sonraki mumu bekle.",
    levels: [
      { value: "Normal Doji", meaning: "Kararsızlık", action: "⏸️ Bekle" },
      { value: "Dragonfly Doji", meaning: "Dipte uzun alt fitil", action: "🟢 Bullish potansiyel" },
      { value: "Gravestone Doji", meaning: "Tepede uzun üst fitil", action: "🔴 Bearish potansiyel" },
    ],
    importance: "medium",
  },

  candlestick_harami: {
    title: "Harami",
    description: "Küçük mum, önceki büyük mumun gövdesi içinde kalır. Hamile anlamına gelir.",
    usage: "Trend dönüş sinyali ama onay gerekli.",
    levels: [
      { value: "Bullish Harami", meaning: "Düşüş sonrası küçük yeşil", action: "🟢 Dönüş başlıyor olabilir" },
      { value: "Bearish Harami", meaning: "Yükseliş sonrası küçük kırmızı", action: "🔴 Dönüş başlıyor olabilir" },
    ],
    importance: "medium",
  },

  candlestick_star: {
    title: "Morning/Evening Star (Sabah/Akşam Yıldızı)",
    description: "3 mumlu güçlü dönüş formasyonu. Ortadaki küçük mum 'yıldız'.",
    usage: "En güvenilir dönüş formasyonlarından biri.",
    levels: [
      { value: "Morning Star", meaning: "Büyük kırmızı → Küçük → Büyük yeşil", action: "🟢 Güçlü LONG" },
      { value: "Evening Star", meaning: "Büyük yeşil → Küçük → Büyük kırmızı", action: "🔴 Güçlü SHORT" },
    ],
    example: "Destek + Morning Star = %90 güvenilir LONG",
    importance: "critical",
  },

  candlestick_shooting_star: {
    title: "Shooting Star (Kayan Yıldız)",
    description: "Küçük gövde altta, uzun üst fitil. Satıcılar yüksek fiyatları reddetti.",
    usage: "Yükseliş trendi tepesinde ara.",
    levels: [
      { value: "Shooting Star", meaning: "Tepede uzun üst fitil", action: "🔴 Dönüş uyarısı" },
      { value: "Inverted Hammer", meaning: "Dipte uzun üst fitil", action: "🟢 Potansiyel dönüş" },
    ],
    importance: "high",
  },

  candlestick_soldiers_crows: {
    title: "Three White Soldiers / Black Crows",
    description: "Üst üste 3 güçlü mum. Trend başlangıcı veya devamı.",
    usage: "Momentum sinyali. Trendle işlem aç.",
    levels: [
      { value: "3 White Soldiers", meaning: "3 yeşil mum yükseliyor", action: "🟢 Güçlü yükseliş başladı" },
      { value: "3 Black Crows", meaning: "3 kırmızı mum düşüyor", action: "🔴 Güçlü düşüş başladı" },
    ],
    importance: "high",
  },
};

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
  const { t } = useI18nStore();
  const info = customData || TRADING_INFO[infoKey];
  
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
