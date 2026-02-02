"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings2, X, ChevronRight, RotateCcw, RefreshCw, Loader2, Shield, Zap, Target, Flame } from "lucide-react";
import { fetchPredictionWithStrategy } from "../lib/api/prediction";
import { useI18nStore } from "../lib/i18n/store";

// Katman tabanlı yapılandırma
type Layer = {
  id: string;
  name: string;
  nameEn: string;
  description: string;
  weight: number;
  logic: "harmonic" | "geometric" | "arithmetic";
  factors: string[];
  enabled: boolean;
  color: string;
};

const LAYERS: Layer[] = [
  {
    id: "critical",
    name: "Kritik Katman",
    nameEn: "Critical Layer",
    description: "Trend & Market Regime (Harmonic Mean)",
    weight: 0.50,
    logic: "harmonic",
    factors: ["trend", "regime"],
    enabled: true,
    color: "from-red-500 to-orange-500"
  },
  {
    id: "technical",
    name: "Teknik Katman",
    nameEn: "Technical Layer",
    description: "S/R & Pattern Analysis (Geometric Mean)",
    weight: 0.30,
    logic: "geometric",
    factors: ["sr", "pattern", "candle"],
    enabled: true,
    color: "from-blue-500 to-cyan-500"
  },
  {
    id: "context",
    name: "Context Katman",
    nameEn: "Context Layer",
    description: "News, COT & Session (Arithmetic Mean)",
    weight: 0.20,
    logic: "arithmetic",
    factors: ["news", "cot", "session", "confluence"],
    enabled: true,
    color: "from-purple-500 to-pink-500"
  }
];

// Preset stratejiler
type Strategy = {
  id: string;
  name: string;
  nameEn: string;
  description: string;
  icon: React.ReactNode;
  enabledLayers: string[];
  threshold: number;
  color: string;
};

const STRATEGIES: Strategy[] = [
  {
    id: "ultra_safe",
    name: "Ultra Güvenli",
    nameEn: "Ultra Safe",
    description: "Yüksek win rate, az trade",
    icon: <Shield className="w-4 h-4" />,
    enabledLayers: ["critical", "technical"],
    threshold: 0.58,
    color: "bg-emerald-500"
  },
  {
    id: "balanced",
    name: "Dengeli",
    nameEn: "Balanced",
    description: "Optimal win rate/trade",
    icon: <Target className="w-4 h-4" />,
    enabledLayers: ["critical", "technical", "context"],
    threshold: 0.55,
    color: "bg-blue-500"
  },
  {
    id: "full_power",
    name: "Full Power",
    nameEn: "Full Power",
    description: "Tüm faktörler aktif",
    icon: <Zap className="w-4 h-4" />,
    enabledLayers: ["critical", "technical", "context"],
    threshold: 0.52,
    color: "bg-yellow-500"
  },
  {
    id: "aggressive",
    name: "Agresif",
    nameEn: "Aggressive",
    description: "Çok trade, düşük filtre",
    icon: <Flame className="w-4 h-4" />,
    enabledLayers: ["critical"],
    threshold: 0.50,
    color: "bg-red-500"
  }
];

type Props = {
  baseConfidence: number;
  symbol?: string;
  onStrategyChange?: (strategy: string, confidence: number) => void;
  locale?: string;
};

export default function MLFactorPanel({ baseConfidence, symbol = "NDX.INDX", onStrategyChange, locale = "tr" }: Props) {
  const { t } = useI18nStore();
  const [isOpen, setIsOpen] = useState(false);
  const [layers, setLayers] = useState<Layer[]>(LAYERS);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("balanced");
  const [liveConfidence, setLiveConfidence] = useState(baseConfidence);
  const [isLoading, setIsLoading] = useState(false);

  // Strateji seçildiğinde katmanları güncelle
  const selectStrategy = useCallback((strategyId: string) => {
    const strategy = STRATEGIES.find(s => s.id === strategyId);
    if (!strategy) return;
    
    setSelectedStrategy(strategyId);
    setLayers(prev => prev.map(layer => ({
      ...layer,
      enabled: strategy.enabledLayers.includes(layer.id)
    })));
  }, []);

  // Backend'den gerçek confidence al
  const fetchWithStrategy = useCallback(async () => {
    setIsLoading(true);
    try {
      const prediction = await fetchPredictionWithStrategy(symbol, selectedStrategy);
      setLiveConfidence(prediction.confidence);
      onStrategyChange?.(selectedStrategy, prediction.confidence);
    } catch (err) {
      console.error("Strategy prediction fetch failed:", err);
      setLiveConfidence(baseConfidence);
    } finally {
      setIsLoading(false);
    }
  }, [symbol, selectedStrategy, baseConfidence, onStrategyChange]);

  // Katman toggle
  const toggleLayer = (layerId: string) => {
    setLayers(prev => prev.map(l => 
      l.id === layerId ? { ...l, enabled: !l.enabled } : l
    ));
    setSelectedStrategy(""); // Custom mode
  };

  const resetToBalanced = () => {
    selectStrategy("balanced");
  };

  const activeLayerCount = layers.filter(l => l.enabled).length;
  const confidenceChange = liveConfidence - baseConfidence;
  const currentStrategy = STRATEGIES.find(s => s.id === selectedStrategy);

  return (
    <>
      {/* Toggle Button - now inside fixed container */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-center gap-2 px-5 py-4 rounded-xl 
          ${isOpen ? "bg-accent text-white" : "bg-gradient-to-r from-accent/80 to-blue-500/80 text-white hover:from-accent hover:to-blue-500"} 
          transition-all duration-200 shadow-xl backdrop-blur-sm border border-white/20`}
      >
        <Settings2 className="w-6 h-6" />
        <span className="text-base font-semibold">{t("mlStrategy.title")}</span>
        <span className="text-xs bg-white/30 px-2 py-0.5 rounded-full font-bold">{activeLayerCount}/3</span>
        <ChevronRight className={`w-5 h-5 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Sliding Panel */}
      <div
        className={`fixed top-16 right-0 h-[calc(100vh-4rem)] w-96 bg-background/95 backdrop-blur-xl 
          border-l border-white/10 shadow-2xl z-30 transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <div>
            <h3 className="font-semibold">{t("mlStrategy.strategySelection")}</h3>
            <p className="text-xs text-textSecondary mt-0.5">
              {currentStrategy ? (locale === "en" ? currentStrategy.nameEn : currentStrategy.name) : t("mlStrategy.customMode")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchWithStrategy}
              disabled={isLoading}
              className="p-1.5 hover:bg-white/10 rounded-lg transition disabled:opacity-50"
              title={t("mlStrategy.updateFromBackend")}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-accent animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 text-accent" />
              )}
            </button>
            <button
              onClick={resetToBalanced}
              className="p-1.5 hover:bg-white/10 rounded-lg transition"
              title={t("mlStrategy.resetToBalanced")}
            >
              <RotateCcw className="w-4 h-4 text-textSecondary" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1.5 hover:bg-white/10 rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Confidence Display */}
        <div className="p-4 border-b border-white/10 bg-white/5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-textSecondary">{t("mlStrategy.base")}</span>
            <span className="font-mono text-sm">{baseConfidence.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{t("mlStrategy.final")}</span>
            <div className="flex items-center gap-2">
              <span className={`text-xs ${confidenceChange >= 0 ? "text-success" : "text-danger"}`}>
                {confidenceChange >= 0 ? "+" : ""}{confidenceChange.toFixed(1)}%
              </span>
              <span className={`font-mono text-lg font-bold ${
                liveConfidence >= 70 ? "text-success" : 
                liveConfidence >= 55 ? "text-yellow-400" : "text-danger"
              }`}>
                {liveConfidence.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                liveConfidence >= 70 ? "bg-success" : 
                liveConfidence >= 55 ? "bg-yellow-400" : "bg-danger"
              }`}
              style={{ width: `${liveConfidence}%` }}
            />
          </div>
        </div>

        {/* Strategy Presets */}
        <div className="p-3 border-b border-white/10">
          <p className="text-xs text-textSecondary mb-2 font-medium">{t("mlStrategy.presetStrategies")}</p>
          <div className="grid grid-cols-2 gap-2">
            {STRATEGIES.map((strategy, index) => (
              <motion.button
                key={strategy.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => selectStrategy(strategy.id)}
                className={`flex items-center gap-2 p-2.5 rounded-lg transition-colors text-left
                  ${selectedStrategy === strategy.id 
                    ? `${strategy.color} text-white shadow-lg shadow-${strategy.color.replace('bg-', '')}/30` 
                    : "bg-white/5 hover:bg-white/10 border border-white/10"
                  }`}
              >
                <motion.div 
                  className={`p-1 rounded ${selectedStrategy === strategy.id ? "bg-white/20" : "bg-white/10"}`}
                  animate={{ rotate: selectedStrategy === strategy.id ? [0, -10, 10, 0] : 0 }}
                  transition={{ duration: 0.5 }}
                >
                  {strategy.icon}
                </motion.div>
                <div>
                  <p className="text-xs font-medium">{locale === "en" ? strategy.nameEn : strategy.name}</p>
                  <p className="text-[10px] opacity-70">{strategy.description}</p>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Layer List */}
        <div className="overflow-y-auto flex-1 p-3">
          <p className="text-xs text-textSecondary mb-2 font-medium">{t("mlStrategy.layers")}</p>
          {layers.map((layer, index) => (
            <motion.div
              key={layer.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02, x: 4 }}
              onClick={() => toggleLayer(layer.id)}
              className={`p-3 rounded-xl mb-2 cursor-pointer transition-colors border
                ${layer.enabled 
                  ? "bg-gradient-to-r " + layer.color + " bg-opacity-20 border-white/20" 
                  : "bg-white/5 border-transparent hover:bg-white/10"
                }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div className={`w-4 h-4 rounded flex items-center justify-center border-2
                    ${layer.enabled ? "bg-white border-white" : "border-white/30"}`}
                  >
                    {layer.enabled && (
                      <svg className="w-2.5 h-2.5 text-gray-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className={`font-medium text-sm ${layer.enabled ? "text-white" : "text-textSecondary"}`}>
                    {locale === "en" ? layer.nameEn : layer.name}
                  </span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${layer.enabled ? "bg-white/20" : "bg-white/10"}`}>
                  {(layer.weight * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs opacity-70 ml-6">{layer.description}</p>
              <div className="flex gap-1 mt-2 ml-6">
                {layer.factors.map(f => (
                  <span key={f} className="text-[10px] px-1.5 py-0.5 bg-white/10 rounded">
                    {f}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-white/10 bg-background/95">
          <p className="text-[10px] text-textSecondary text-center">
            {t("mlStrategy.footerTip")}
          </p>
        </div>
      </div>

      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-20 lg:hidden"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
}
