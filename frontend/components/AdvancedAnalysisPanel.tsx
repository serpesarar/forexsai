"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  Shield,
  BarChart3,
  Zap,
  Droplets,
  RefreshCw,
  HelpCircle,
  ChevronDown,
  X,
  Info,
} from "lucide-react";
import { InfoBadge } from "./InfoTooltip";
import { useI18nStore } from "../lib/i18n/store";

interface MTFAdvancedData {
  market_regime: {
    regime: string;
    adx: number;
    plus_di: number;
    minus_di: number;
    di_spread: number;
    confidence_level: string;
    trend_direction: string | null;
    regime_quality: number;
  };
  price_action: {
    structure: string;
    structure_quality: string;
    liquidity_sweep: boolean;
    equal_highs_count: number;
    equal_lows_count: number;
    break_of_structure: boolean;
  };
  volume_profile: {
    poc: number;
    hvn_resistances: number[];
    hvn_supports: number[];
    poc_is_relevant: boolean;
  };
  pivot_points: {
    pivot: number;
    r1: number;
    r2: number;
    r3: number;
    s1: number;
    s2: number;
    s3: number;
    pivot_type: string;
  };
  position_sizing: {
    recommended_risk_percent: number;
    volatility_adjustment: number;
    session: string;
    session_volatility: string;
    high_impact_event: string | null;
  };
  correlation: {
    dxy_trend: string;
    vix_level: number;
    vix_regime: string;
    correlation_confirms: boolean;
    conflicting_signals: string[];
  } | null;
}

// Sembol tanımları - API key ve görünen isim
const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ", display: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD", display: "XAU/USD" },
  { key: "GDAXI.INDX", label: "DAX", display: "DAX" },
  { key: "CL.COMM", label: "US Oil", display: "WTI Oil" },
];

const API_BASE = "https://upbeat-flow-production.up.railway.app";

// Kullanım Kılavuzu Modalı
function UserGuideModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { t, locale } = useI18nStore();
  const isEn = locale === "en";

  if (!isOpen) return null;

  const steps = [
    {
      icon: "🎯",
      title: isEn ? "Check Market Regime" : "Market Rejimini Kontrol Et",
      desc: isEn 
        ? "ADX > 30 + High DI Spread = Strong Trend. ADX < 20 = Range market."
        : "ADX > 30 + Yüksek DI Spread = Güçlü Trend. ADX < 20 = Yatay piyasa.",
      tip: isEn ? "Avoid trading when regime is CHOPPY" : "Rejim CHOPPY olduğunda trade yapma",
    },
    {
      icon: "📊",
      title: isEn ? "Analyze Price Action" : "Price Action Analiz Et",
      desc: isEn
        ? "VALID_BREAKOUT = Best setup. FAKEOUT_TRAP = Avoid. AWAITING_CONFIRMATION = Wait."
        : "VALID_BREAKOUT = En iyi setup. FAKEOUT_TRAP = Kaçın. AWAITING_CONFIRMATION = Bekle.",
      tip: isEn ? "3+ Equal Highs/Lows = Liquidity sweep coming" : "3+ Eşit Tepe/Dip = Likidite süpürmesi gelebilir",
    },
    {
      icon: "⚠️",
      title: isEn ? "Watch for Liquidity Sweep" : "Likidite Süpürmesine Dikkat",
      desc: isEn
        ? "If sweep detected, price may reverse sharply. Reduce position size or wait."
        : "Sweep tespit edilirse fiyat sert dönebilir. Pozisyonu küçült veya bekle.",
      tip: isEn ? "Sweep = Stop hunting by big players" : "Sweep = Büyük oyuncuların stop avlaması",
    },
    {
      icon: "📍",
      title: isEn ? "Find S/R Levels" : "D/D Seviyelerini Bul",
      desc: isEn
        ? "R2/S2 (0.618 Fib) are strongest. Use HVN levels for real support/resistance."
        : "R2/S2 (0.618 Fib) en güçlüsüdür. Gerçek destek/direnç için HVN seviyelerini kullan.",
      tip: isEn ? "POC is NOT resistance - it's just high volume" : "POC direnç DEĞİLDİR - sadece yüksek hacimdir",
    },
    {
      icon: "⚡",
      title: isEn ? "Check Correlation" : "Korelasyonu Kontrol Et",
      desc: isEn
        ? "Gold bullish needs DXY bearish. High VIX usually supports gold."
        : "Altın yükseliş için DXY düşüş gerekir. Yüksek VIX genelde altını destekler.",
      tip: isEn ? "Conflicting signals = Reduce confidence by 25%" : "Çelişkili sinyaller = Güveni %25 azalt",
    },
    {
      icon: "💰",
      title: isEn ? "Position Sizing" : "Pozisyon Büyüklüğü",
      desc: isEn
        ? "NFP day = 30% normal risk. High volatility = Reduce size. Asia session = Lower liquidity."
        : "NFP günü = Normal riskin %30'u. Yüksek volatilite = Küçült. Asya seansı = Düşük likidite.",
      tip: isEn ? "Never risk more than 2% of account" : "Asla hesabın %2'sinden fazla riske atma",
    },
  ];

  const indicators = [
    { name: "ADX", meaning: isEn ? "Trend strength (not direction)" : "Trend gücü (yön değil)", critical: true },
    { name: "DI Spread", meaning: isEn ? "Trend direction confirmation" : "Trend yönü teyidi", critical: true },
    { name: "HVN", meaning: isEn ? "High Volume Node = Real S/R" : "Yüksek Hacim = Gerçek D/D", critical: true },
    { name: "POC", meaning: isEn ? "Point of Control = Most traded price" : "En çok işlem gören fiyat", critical: false },
    { name: "R2/S2", meaning: isEn ? "0.618 Fib = Strongest pivot" : "0.618 Fib = En güçlü pivot", critical: true },
    { name: "VIX", meaning: isEn ? "Fear index >25 = Risk off" : "Korku endeksi >25 = Risk off", critical: false },
  ];

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      
      {/* Modal */}
      <div 
        className="relative bg-gray-900/95 backdrop-blur-xl rounded-2xl border border-gray-700/50 shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-6 py-4 border-b border-gray-700/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                <HelpCircle className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">
                  {isEn ? "MTF Advanced Analysis - User Guide" : "MTF Advanced Analysis - Kullanım Kılavuzu"}
                </h2>
                <p className="text-xs text-gray-400">
                  {isEn ? "How to use this panel effectively" : "Bu paneli etkili kullanma rehberi"}
                </p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh] space-y-6">
          {/* Quick Steps */}
          <div>
            <h3 className="text-sm font-semibold text-indigo-400 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4" />
              {isEn ? "6-Step Analysis Process" : "6 Adımlık Analiz Süreci"}
            </h3>
            <div className="space-y-3">
              {steps.map((step, idx) => (
                <div 
                  key={idx}
                  className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/30 hover:border-indigo-500/30 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{step.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-white">{step.title}</span>
                        <span className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                          {isEn ? "Step" : "Adım"} {idx + 1}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{step.desc}</p>
                      <p className="text-xs text-yellow-400/80 mt-1">💡 {step.tip}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Indicators Reference */}
          <div>
            <h3 className="text-sm font-semibold text-indigo-400 mb-3">
              {isEn ? "Key Indicators Reference" : "Kritik Göstergeler Referansı"}
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {indicators.map((ind, idx) => (
                <div 
                  key={idx}
                  className={`bg-gray-800/30 rounded-lg p-2 border ${ind.critical ? 'border-red-500/20' : 'border-gray-700/30'}`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-mono font-bold ${ind.critical ? 'text-red-400' : 'text-gray-400'}`}>
                      {ind.name}
                    </span>
                    {ind.critical && (
                      <span className="text-[8px] text-red-400 bg-red-500/10 px-1 rounded">
                        {isEn ? "CRITICAL" : "KRİTİK"}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-500 mt-0.5">{ind.meaning}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Warnings */}
          <div className="bg-red-900/20 rounded-lg p-4 border border-red-500/30">
            <h3 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              {isEn ? "Critical Warnings" : "Kritik Uyarılar"}
            </h3>
            <ul className="space-y-1 text-xs text-gray-400">
              <li>• {isEn ? "Never trade against the Market Regime" : "Asla Market Regime'e karşı işlem yapma"}</li>
              <li>• {isEn ? "High ADX alone doesn't mean trend - check DI Spread" : "Yüksek ADX tek başına trend demek değil - DI Spread'i kontrol et"}</li>
              <li>• {isEn ? "Liquidity sweep = Stop hunting - wait for confirmation" : "Likidite süpürmesi = Stop avlama - onay bekle"}</li>
              <li>• {isEn ? "NFP day: Reduce risk to 30% or don't trade" : "NFP günü: Riski %30'a indir veya trade yapma"}</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-800/50 px-6 py-3 border-t border-gray-700/50">
          <p className="text-xs text-gray-500 text-center">
            {isEn ? "Press ESC or click outside to close" : "Kapatmak için ESC'ye basın veya dışarı tıklayın"}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AdvancedAnalysisPanel({ className = "" }: { className?: string }) {
  const [symbol, setSymbol] = useState("XAUUSD");
  const [data, setData] = useState<MTFAdvancedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [showGuide, setShowGuide] = useState(false);
  const { locale } = useI18nStore();
  const isEn = locale === "en";

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const normalizedSymbol = symbol.toUpperCase() === "NASDAQ" ? "NDX.INDX" : symbol;
      const res = await fetch(`${API_BASE}/api/mtf/analysis?symbol=${encodeURIComponent(normalizedSymbol)}`);
      
      if (!res.ok) throw new Error(isEn ? "Failed to fetch MTF analysis" : "MTF analizi alınamadı");
      
      const json = await res.json();
      
      if (json.success && json.confluence) {
        const advanced: MTFAdvancedData = {
          market_regime: json.confluence.market_regime || {
            regime: "UNKNOWN",
            adx: 0,
            plus_di: 0,
            minus_di: 0,
            di_spread: 0,
            confidence_level: "LOW_CONFIDENCE",
            trend_direction: null,
            regime_quality: 0
          },
          price_action: json.confluence.price_action || {
            structure: "CHOPPY",
            structure_quality: "CHOPPY",
            liquidity_sweep: false,
            equal_highs_count: 0,
            equal_lows_count: 0,
            break_of_structure: false
          },
          volume_profile: json.confluence.volume_profile || {
            poc: 0,
            hvn_resistances: [],
            hvn_supports: [],
            poc_is_relevant: false
          },
          pivot_points: json.confluence.pivot_points || {
            pivot: 0,
            r1: 0, r2: 0, r3: 0,
            s1: 0, s2: 0, s3: 0,
            pivot_type: "CLASSIC"
          },
          position_sizing: json.confluence.position_sizing || {
            recommended_risk_percent: 1,
            volatility_adjustment: 0,
            session: "UNKNOWN",
            session_volatility: "NORMAL",
            high_impact_event: null
          },
          correlation: json.confluence.correlation || null
        };
        setData(advanced);
        setLastUpdate(new Date());
        setError(null);
      } else {
        setError(isEn ? "No advanced data available" : "Gelişmiş veri mevcut değil");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : isEn ? "Unknown error" : "Bilinmeyen hata");
    } finally {
      setLoading(false);
    }
  }, [symbol, isEn]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ESC tuşu ile kapatma
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowGuide(false);
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  if (loading && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center h-48">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-red-700/50 p-4 ${className}`}>
        <div className="text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  if (!data) return null;

  const { market_regime, price_action, volume_profile, pivot_points, position_sizing, correlation } = data;

  // Renk belirleme
  const regimeColor = market_regime.regime === "TRENDING" 
    ? "text-green-400" 
    : market_regime.regime === "RANGING" 
      ? "text-yellow-400" 
      : "text-red-400";

  const confidenceColor = market_regime.confidence_level === "HIGH_CONFIDENCE"
    ? "text-green-400"
    : market_regime.confidence_level === "LOW_CONFIDENCE"
      ? "text-yellow-400"
      : "text-red-400";

  const structureColor = price_action.structure_quality === "VALID_BREAKOUT"
    ? "text-green-400"
    : price_action.structure_quality === "FAKEOUT_TRAP"
      ? "text-red-400"
      : "text-yellow-400";

  const sessionColor = position_sizing.session === "OVERLAP"
    ? "text-purple-400"
    : position_sizing.session === "NEW_YORK"
      ? "text-blue-400"
      : position_sizing.session === "LONDON"
        ? "text-cyan-400"
        : "text-gray-400";

  const activeSymbolLabel = SYMBOLS.find(s => s.key === symbol)?.display || symbol;

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* User Guide Modal */}
      <UserGuideModal isOpen={showGuide} onClose={() => setShowGuide(false)} />

      {/* Header with Symbol Selector and Guide Button */}
      <div className="bg-gradient-to-r from-indigo-900/50 to-purple-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold text-white">{isEn ? "MTF Advanced Analysis" : "MTF Gelişmiş Analiz"}</span>
            
            {/* Sembol Seçici */}
            <div className="relative ml-2">
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="appearance-none bg-gray-800/80 border border-gray-600/50 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500/50 cursor-pointer min-w-[100px]"
              >
                {SYMBOLS.map((s) => (
                  <option key={s.key} value={s.key}>{s.display}</option>
                ))}
              </select>
              <ChevronDown className="w-3 h-3 text-gray-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Kullanım Kılavuzu Butonu */}
            <button
              onClick={() => setShowGuide(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 border border-indigo-500/30 rounded-lg transition-colors"
              title={isEn ? "User Guide" : "Kullanım Kılavuzu"}
            >
              <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-xs font-medium text-indigo-300">{isEn ? "Guide" : "Kılavuz"}</span>
            </button>

            {lastUpdate && (
              <span className="text-xs text-gray-500">
                {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button 
              onClick={fetchData}
              className="p-1.5 hover:bg-gray-700/50 rounded-lg transition-colors"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* High Impact Event Warning */}
        {position_sizing.high_impact_event && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-3 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <div className="text-red-400 font-semibold text-sm">
                {position_sizing.high_impact_event === "NFP_DAY" && (isEn ? "🔴 NFP DAY - Trade Not Recommended!" : "🔴 NFP GÜNÜ - Trade Önerilmez!")}
                {position_sizing.high_impact_event === "FOMC_POTENTIAL" && (isEn ? "🟠 FOMC Potential - Be Careful" : "🟠 FOMC Potansiyeli - Dikkatli Ol")}
                {position_sizing.high_impact_event === "CPI_WEEK" && (isEn ? "🟡 CPI Week - Volatility Expected" : "🟡 CPI Haftası - Volatilite Bekleniyor")}
              </div>
              <div className="text-red-300/70 text-xs">
                {isEn ? `Risk reduced by ${(position_sizing.volatility_adjustment * 100).toFixed(0)}%` : `Risk %${(position_sizing.volatility_adjustment * 100).toFixed(0)} oranında azaltıldı`}
              </div>
            </div>
          </div>
        )}

        {/* Liquidity Sweep Warning */}
        {price_action.liquidity_sweep && (
          <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-3 flex items-center gap-3">
            <Droplets className="w-5 h-5 text-yellow-400 flex-shrink-0" />
            <div>
              <div className="text-yellow-400 font-semibold text-sm">
                {isEn ? "💧 Liquidity Sweep Detected" : "💧 Likidite Süpürmesi Tespit Edildi"}
              </div>
              <div className="text-yellow-300/70 text-xs">
                {isEn ? "Reversal risk - Be careful" : "Ters hareket riski - Dikkatli ol"}
              </div>
            </div>
          </div>
        )}

        {/* Grid Layout */}
        <div className="grid grid-cols-2 gap-3">
          {/* Market Regime */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <span className="text-xs text-gray-400">{isEn ? "Market Regime" : "Market Rejimi"}</span>
              <InfoBadge infoKey="market_regime" />
            </div>
            <div className={`text-lg font-bold ${regimeColor}`}>
              {market_regime.regime}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500">ADX: {market_regime.adx.toFixed(1)}</span>
              <span className="text-xs text-gray-500">|</span>
              <span className={`text-xs ${confidenceColor}`}>
                {market_regime.confidence_level.replace("_", " ")}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {isEn ? "DI Spread" : "DI Spread"}: {market_regime.di_spread.toFixed(1)}
            </div>
          </div>

          {/* Price Action */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              {price_action.structure.includes("HH") ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : price_action.structure.includes("LL") ? (
                <TrendingDown className="w-4 h-4 text-red-400" />
              ) : (
                <Activity className="w-4 h-4 text-yellow-400" />
              )}
              <span className="text-xs text-gray-400">{isEn ? "Price Action" : "Price Action"}</span>
              <InfoBadge infoKey="liquidity_sweep" />
            </div>
            <div className={`text-lg font-bold ${structureColor}`}>
              {price_action.structure_quality.replace("_", " ")}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {isEn ? "Structure" : "Yapı"}: {price_action.structure}
            </div>
            {(price_action.equal_highs_count >= 2 || price_action.equal_lows_count >= 2) && (
              <div className="text-xs text-yellow-400 mt-1">
                {price_action.equal_highs_count >= 2 && `🎯 ${price_action.equal_highs_count}x EQ Highs`}
                {price_action.equal_lows_count >= 2 && ` 🎯 ${price_action.equal_lows_count}x EQ Lows`}
              </div>
            )}
          </div>

          {/* Session Info */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span className="text-xs text-gray-400">{isEn ? "Trading Session" : "İşlem Seansı"}</span>
              <InfoBadge infoKey="session" />
            </div>
            <div className={`text-lg font-bold ${sessionColor}`}>
              {position_sizing.session}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {isEn ? "Volatility" : "Volatilite"}: {position_sizing.session_volatility}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {isEn ? "Risk Adj" : "Risk Ayarı"}: {(position_sizing.volatility_adjustment * 100).toFixed(0)}%
            </div>
          </div>

          {/* Position Sizing */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span className="text-xs text-gray-400">{isEn ? "Position Sizing" : "Pozisyon Boyutu"}</span>
              <InfoBadge infoKey="position_size" />
            </div>
            <div className="text-lg font-bold text-emerald-400">
              %{position_sizing.recommended_risk_percent.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {isEn ? "Recommended Risk" : "Önerilen Risk"}
            </div>
          </div>
        </div>

        {/* Pivot Points */}
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-amber-400" />
            <span className="text-xs text-gray-400">{isEn ? "Fibonacci Pivot Points" : "Fibonacci Pivot Noktaları"}</span>
            <InfoBadge infoKey="pivot_points" />
            <span className="text-xs text-amber-400/70 ml-auto">{pivot_points.pivot_type}</span>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-xs">
            <div className="bg-red-900/30 rounded p-1">
              <div className="text-red-400 font-medium">R3</div>
              <div className="text-gray-300">{pivot_points.r3.toFixed(1)}</div>
            </div>
            <div className="bg-red-900/50 rounded p-1 ring-1 ring-red-500/50">
              <div className="text-red-400 font-bold">R2★</div>
              <div className="text-gray-300">{pivot_points.r2.toFixed(1)}</div>
            </div>
            <div className="bg-red-900/30 rounded p-1">
              <div className="text-red-400 font-medium">R1</div>
              <div className="text-gray-300">{pivot_points.r1.toFixed(1)}</div>
            </div>
            <div className="bg-gray-700/50 rounded p-1">
              <div className="text-gray-400 font-medium">P</div>
              <div className="text-white">{pivot_points.pivot.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/30 rounded p-1">
              <div className="text-green-400 font-medium">S1</div>
              <div className="text-gray-300">{pivot_points.s1.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/50 rounded p-1 ring-1 ring-green-500/50">
              <div className="text-green-400 font-bold">S2★</div>
              <div className="text-gray-300">{pivot_points.s2.toFixed(1)}</div>
            </div>
            <div className="bg-green-900/30 rounded p-1">
              <div className="text-green-400 font-medium">S3</div>
              <div className="text-gray-300">{pivot_points.s3.toFixed(1)}</div>
            </div>
          </div>
          <div className="text-xs text-amber-400/70 mt-2 text-center">
            ★ {isEn ? "R2/S2 (0.618 Fib) = Strongest Levels" : "R2/S2 (0.618 Fib) = En Güçlü Seviyeler"}
          </div>
        </div>

        {/* HVN Support/Resistance */}
        {(volume_profile.hvn_resistances.length > 0 || volume_profile.hvn_supports.length > 0) && (
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-3">
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400">{isEn ? "HVN S/R (Real Levels)" : "HVN D/D (Gerçek Seviyeler)"}</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-red-400 mb-1">{isEn ? "Resistances" : "Dirençler"}</div>
                <div className="space-y-1">
                  {volume_profile.hvn_resistances.slice(0, 3).map((r, i) => (
                    <div key={i} className="text-xs text-gray-300 bg-red-900/20 rounded px-2 py-1">
                      {r.toFixed(2)}
                    </div>
                  ))}
                  {volume_profile.hvn_resistances.length === 0 && (
                    <div className="text-xs text-gray-500">{isEn ? "Not detected" : "Tespit edilemedi"}</div>
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-green-400 mb-1">{isEn ? "Supports" : "Destekler"}</div>
                <div className="space-y-1">
                  {volume_profile.hvn_supports.slice(0, 3).map((s, i) => (
                    <div key={i} className="text-xs text-gray-300 bg-green-900/20 rounded px-2 py-1">
                      {s.toFixed(2)}
                    </div>
                  ))}
                  {volume_profile.hvn_supports.length === 0 && (
                    <div className="text-xs text-gray-500">{isEn ? "Not detected" : "Tespit edilemedi"}</div>
                  )}
                </div>
              </div>
            </div>
            {volume_profile.poc_is_relevant && (
              <div className="text-xs text-purple-400 mt-2">
                POC: {volume_profile.poc.toFixed(2)} {isEn ? "(Near price)" : "(Fiyat yakınında)"}
              </div>
            )}
          </div>
        )}

        {/* Correlation */}
        {correlation && (
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-400">{isEn ? "Correlation Analysis" : "Korelasyon Analizi"}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-gray-500">DXY</div>
                <div className={correlation.dxy_trend === "BULLISH" ? "text-green-400" : correlation.dxy_trend === "BEARISH" ? "text-red-400" : "text-gray-400"}>
                  {correlation.dxy_trend}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">VIX</div>
                <div className={correlation.vix_regime === "HIGH" || correlation.vix_regime === "EXTREME" ? "text-red-400" : "text-green-400"}>
                  {correlation.vix_level?.toFixed(1)} ({correlation.vix_regime})
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-500">{isEn ? "Confirm" : "Onay"}</div>
                <div className={correlation.correlation_confirms ? "text-green-400" : "text-red-400"}>
                  {correlation.correlation_confirms ? (isEn ? "✓ Confirmed" : "✓ Onaylı") : (isEn ? "✗ Conflict" : "✗ Çelişki")}
                </div>
              </div>
            </div>
            {correlation.conflicting_signals && correlation.conflicting_signals.length > 0 && (
              <div className="mt-2 text-xs text-red-400">
                ⚠️ {correlation.conflicting_signals.join(", ")}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
