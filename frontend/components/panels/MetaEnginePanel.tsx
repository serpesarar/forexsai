"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import ConsensusComboBoard, { type ConsensusSymbolView } from "./ConsensusComboBoard";
import { useI18nStore } from "../../lib/i18n/store";
import { useDashboardStore } from "../../lib/store";
import { buildApiUrl } from "../../lib/api/base";

// ── Types ──────────────────────────────────────────────
interface ModelBreakdown {
  direction: string;
  confidence: number;
  is_available: boolean;
  agrees: boolean;
}

interface MetaSignalData {
  symbol: string;
  direction: string;
  confidence: number;
  strength: string;
  source_combo: string;
  regime: string;
  agreement_ratio: number;
  technical_score: number;
  passed_conditions: string[];
  entry_price: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  risk_reward: number;
  model_breakdown: Record<string, ModelBreakdown>;
  alternatives: Array<{
    combo_key: string;
    win_rate: number;
    total_signals: number;
    profit_factor: number;
  }>;
  timestamp: number;
  message?: string;
}

const SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"];
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL",
};

const MODEL_LABELS: Record<string, string> = {
  ml: "ML Model",
  pulse1: "Pulse 1",
  pulse2: "Pulse 2",
  pulse3: "Pulse 3",
  emel: "EMEL",
  smc: "SMC",
};

const TECH_CONDITION_LABELS: Record<string, string> = {
  ema_stack: "EMA Stack",
  ema200_position: "EMA 200",
  rsi_momentum: "RSI",
  macd_alignment: "MACD",
  adx_trending: "ADX",
  volume_confirmed: "Volume",
  bb_position: "Bollinger",
  atr_valid: "ATR",
};

const ALL_CONDITIONS = [
  "ema_stack", "ema200_position", "rsi_momentum", "macd_alignment",
  "adx_trending", "volume_confirmed", "bb_position", "atr_valid",
];

// ── Helper Components ──────────────────────────────────

function ConfidenceRing({ value, size = 100, direction }: { value: number; size?: number; direction: string }) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;
  const strokeColor = direction === "BUY" ? "#16C784" : direction === "SELL" ? "#EA3943" : "#4F8CFF";

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={5} />
        <circle
          cx={size / 2} cy={size / 2} r={radius} fill="none"
          stroke={strokeColor} strokeWidth={5} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold" style={{ color: strokeColor }}>
          {Math.round(value)}%
        </span>
        <span className="text-[10px] font-semibold tracking-wider opacity-70">
          {direction}
        </span>
      </div>
    </div>
  );
}

interface ComboInsight {
  bestWinRate: number;
  bestCombo: string;
  isPending: boolean;
  pendingCombo: string;
  pendingComboWR: number;
}

function analyzeModelCombos(
  modelId: string,
  modelBreakdown: Record<string, ModelBreakdown>,
  consensus: ConsensusSymbolView | undefined,
  metaDirection: string,
): ComboInsight {
  const result: ComboInsight = { bestWinRate: 0, bestCombo: "", isPending: false, pendingCombo: "", pendingComboWR: 0 };
  if (!consensus) return result;

  const dirSection = metaDirection === "BUY" ? consensus.buy : metaDirection === "SELL" ? consensus.sell : null;
  if (!dirSection) return result;

  const allCombos = [...(dirSection.best_stable || []), ...(dirSection.most_frequent || [])];
  const seen = new Set<string>();
  const uniqueCombos = allCombos.filter((c: any) => {
    const k = c.combination;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  const agreeingModels = new Set(
    Object.entries(modelBreakdown)
      .filter(([, info]) => info.agrees && info.is_available)
      .map(([id]) => id)
  );

  for (const combo of uniqueCombos) {
    const comboStr = (combo as any).combination || "";
    const wr = Number((combo as any).win_rate || 0);
    const models = comboStr.split("+").map((m: string) => m.trim().toLowerCase());
    if (!models.includes(modelId)) continue;

    // Best combo this model is part of (where model agrees)
    if (agreeingModels.has(modelId) && wr > result.bestWinRate) {
      const allAgree = models.every((m: string) => agreeingModels.has(m));
      if (allAgree) {
        result.bestWinRate = wr;
        result.bestCombo = comboStr;
      }
    }

    // Pending: model does NOT agree, but all OTHER models in combo DO agree
    if (!agreeingModels.has(modelId) && wr >= 0.55) {
      const othersAgree = models.filter((m: string) => m !== modelId).every((m: string) => agreeingModels.has(m));
      if (othersAgree && wr > result.pendingComboWR) {
        result.isPending = true;
        result.pendingCombo = comboStr;
        result.pendingComboWR = wr;
      }
    }
  }

  return result;
}

function ModelDot({ label, modelId, direction, agrees, confidence, insight }: {
  label: string; modelId: string; direction: string; agrees: boolean; confidence: number;
  insight: ComboInsight;
}) {
  let color: string;
  let glow = "none";
  let animClass = "";
  let tooltip = `${label}: ${direction} (${Math.round(confidence)}%)`;

  if (insight.isPending) {
    // Pending confirmation — blink yellow
    color = "#F5A623";
    glow = "0 0 8px #F5A623";
    animClass = "animate-pulse";
    tooltip += ` \u2014 Awaiting for combo: ${insight.pendingCombo} (${Math.round(insight.pendingComboWR * 100)}% WR)`;
  } else if (!agrees) {
    color = "rgba(255,255,255,0.15)";
  } else if (insight.bestWinRate >= 0.60) {
    // Strong combo — bright green with intense glow
    color = direction === "SELL" ? "#EA3943" : "#16C784";
    glow = `0 0 10px ${color}, 0 0 20px ${color}40`;
    tooltip += ` \u2014 Active combo: ${insight.bestCombo} (${Math.round(insight.bestWinRate * 100)}% WR)`;
  } else if (insight.bestWinRate >= 0.50) {
    color = direction === "SELL" ? "#EA3943" : "#16C784";
    glow = `0 0 6px ${color}`;
    tooltip += ` \u2014 Combo: ${insight.bestCombo} (${Math.round(insight.bestWinRate * 100)}% WR)`;
  } else if (agrees) {
    color = direction === "BUY" ? "#16C784" : direction === "SELL" ? "#EA3943" : "rgba(255,255,255,0.3)";
    glow = `0 0 4px ${color}`;
  } else {
    color = "rgba(255,255,255,0.15)";
  }

  const shortLabel = label.replace("Model ", "").replace("Pulse ", "P");

  return (
    <div className="flex flex-col items-center gap-1" title={tooltip}>
      <div
        className={`w-3.5 h-3.5 rounded-full transition-all duration-500 ${animClass}`}
        style={{
          backgroundColor: color,
          boxShadow: glow,
          border: insight.isPending ? "1.5px solid #F5A623" : insight.bestWinRate >= 0.60 ? `1.5px solid ${color}` : "none",
        }}
      />
      <span className={`text-[9px] font-medium ${
        insight.isPending ? "text-yellow-400" : agrees ? "text-[#E6EDF3]/70" : "text-[#6B7280]/60"
      }`}>{shortLabel}</span>
    </div>
  );
}

function TechConditionDot({ name, passed }: { name: string; passed: boolean }) {
  return (
    <div className="flex items-center gap-1.5 text-[11px]">
      <div
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{
          backgroundColor: passed ? "#16C784" : "rgba(255,255,255,0.12)",
          boxShadow: passed ? "0 0 4px #16C784" : "none",
        }}
      />
      <span className={passed ? "text-[#E6EDF3]" : "text-[#6B7280]"}>
        {TECH_CONDITION_LABELS[name] || name}
      </span>
    </div>
  );
}

// ── Main Panel ─────────────────────────────────────────

interface MetaEnginePanelProps {
  symbol?: string;
}

export default function MetaEnginePanel({ symbol }: MetaEnginePanelProps) {
  const { t } = useI18nStore();
  const initialSymbol = symbol ?? "NDX.INDX";
  const isSymbolLocked = Boolean(symbol);
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [signals, setSignals] = useState<Record<string, MetaSignalData>>({});
  const [consensusViews, setConsensusViews] = useState<Record<string, ConsensusSymbolView>>({});
  const consensusFetchedAt = useRef<Record<string, number>>({});
  const CONSENSUS_TTL_MS = 5 * 60 * 1000; // 5 minutes
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fetchRef = useRef(false);

  useEffect(() => {
    setActiveSymbol(initialSymbol);
  }, [initialSymbol]);

  const fetchDashboard = useCallback(async () => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 45000);
    try {
      setError(null);
      const response = await fetch(buildApiUrl("/api/meta/dashboard"), {
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Failed to load meta analysis");
      }
      const resp = await response.json();
      if (resp?.success && resp.data) {
        setSignals(resp.data);
      } else if (resp?.data) {
        setSignals(resp.data);
      }
    } catch (err: any) {
      if (err?.name === "AbortError") {
        setError("Meta dashboard request timed out");
      } else {
        setError(err?.message || "Failed to load meta analysis");
      }
    } finally {
      window.clearTimeout(timeout);
      setLoading(false);
    }
  }, []);

  const fetchConsensus = useCallback(async (targetSymbol: string) => {
    try {
      const response = await fetch(buildApiUrl(`/api/permutation-analysis/consensus/${targetSymbol}?top=4`), {
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        return;
      }
      const resp = await response.json();
      if (resp?.success && resp.data) {
        setConsensusViews((prev) => ({
          ...prev,
          [targetSymbol]: resp.data as ConsensusSymbolView,
        }));
        consensusFetchedAt.current[targetSymbol] = Date.now();
      }
    } catch {
      return;
    }
  }, []);

  // Initial fetch + polling
  useEffect(() => {
    if (fetchRef.current) return;
    fetchRef.current = true;
    fetchDashboard();

    const interval = setInterval(fetchDashboard, 60000);

    // Listen for dashboard refresh
    const handler = () => fetchDashboard();
    window.addEventListener("dashboard-refresh", handler);

    return () => {
      clearInterval(interval);
      window.removeEventListener("dashboard-refresh", handler);
    };
  }, [fetchDashboard]);

  useEffect(() => {
    if (!activeSymbol) return;
    const lastFetch = consensusFetchedAt.current[activeSymbol] || 0;
    const isStale = Date.now() - lastFetch > CONSENSUS_TTL_MS;
    if (!consensusViews[activeSymbol] || isStale) {
      fetchConsensus(activeSymbol);
    }
  }, [activeSymbol, fetchConsensus]);

  const currentSignal = signals[activeSymbol] as MetaSignalData | undefined;
  const currentConsensus = consensusViews[activeSymbol] as ConsensusSymbolView | undefined;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827] overflow-hidden">
      {/* ── Header ── */}
      <div className="px-5 pt-5 pb-3 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#4F8CFF]/15 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F8CFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <h3 className="text-base font-semibold text-[#E6EDF3]">
                {t("meta_engine.title")}
              </h3>
              <p className="text-[11px] text-[#6B7280] mt-0.5">
                {t("meta_engine.subtitle")}
              </p>
            </div>
          </div>

          {currentSignal?.regime && (
            <span className="px-2.5 py-1 rounded-md text-[10px] font-semibold tracking-wider bg-white/[0.06] text-[#9AA4B2]">
              {currentSignal.regime.replace(/_/g, " ")}
            </span>
          )}
        </div>

        {/* Symbol Tabs */}
        <div className="flex gap-1 mt-3">
          {(isSymbolLocked ? [activeSymbol] : SYMBOLS).map((sym) => {
            const sig = signals[sym] as MetaSignalData | undefined;
            const isActive = sym === activeSymbol;
            const dir = sig?.direction || "HOLD";
            const dotColor = dir === "BUY" ? "#16C784" : dir === "SELL" ? "#EA3943" : "rgba(255,255,255,0.2)";

            return (
              <button
                key={sym}
                onClick={() => !isSymbolLocked && setActiveSymbol(sym)}
                className={`flex-1 px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all flex items-center justify-center gap-1.5 ${
                  isActive ? "bg-white/[0.08] text-[#E6EDF3]" : "text-[#6B7280] hover:bg-white/[0.04] hover:text-[#9AA4B2]"
                }`}
              >
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dotColor }} />
                {SYMBOL_LABELS[sym] || sym}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Body ── */}
      <div className="p-5">
        {loading ? (
          <div className="flex items-center justify-center h-40 gap-2">
            <div className="w-5 h-5 border-2 border-[#4F8CFF]/30 border-t-[#4F8CFF] rounded-full animate-spin" />
            <span className="text-sm text-[#6B7280]">{t("meta_engine.analyzing")}</span>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-[#6B7280] text-sm">{error}</div>
        ) : !currentSignal ? (
          <div className="text-center py-8 text-[#6B7280] text-sm">
            {t("meta_engine.no_signal")}
          </div>
        ) : (
          <div className="space-y-5">
            {/* Row 1: Confidence Ring + Agreement + Combo */}
            <div className="flex items-start gap-4">
              {/* Confidence Ring */}
              <ConfidenceRing
                value={currentSignal.confidence || 0}
                size={96}
                direction={currentSignal.direction || "HOLD"}
              />

              <div className="flex-1 space-y-3">
                {/* Strength Badge */}
                <div className="flex items-center gap-2">
                  <span
                    className="px-3 py-1 rounded-full text-xs font-bold tracking-wide"
                    style={{
                      backgroundColor:
                        currentSignal.strength === "STRONG" ? "rgba(22,199,132,0.15)"
                        : currentSignal.strength === "MODERATE" ? "rgba(79,140,255,0.15)"
                        : "rgba(255,255,255,0.06)",
                      color:
                        currentSignal.strength === "STRONG" ? "#16C784"
                        : currentSignal.strength === "MODERATE" ? "#4F8CFF"
                        : "#6B7280",
                    }}
                  >
                    {currentSignal.strength || "—"}
                  </span>
                  <span className="text-[11px] text-[#6B7280]">
                    {t("meta_engine.agreement")}: {Math.round((currentSignal.agreement_ratio || 0) * 100)}%
                  </span>
                </div>

                {/* Best Combo */}
                {currentSignal.source_combo && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] tracking-wider text-[#6B7280] uppercase">{t("meta_engine.best_combo")}</span>
                    <span className="px-2 py-0.5 rounded bg-[#4F8CFF]/10 text-[#4F8CFF] text-[11px] font-mono font-semibold">
                      {currentSignal.source_combo}
                    </span>
                  </div>
                )}

                {/* Model Agreement Dots */}
                {(() => {
                  const breakdown = currentSignal.model_breakdown || {};
                  const insights: Record<string, ComboInsight> = {};
                  Object.keys(breakdown).forEach((id) => {
                    insights[id] = analyzeModelCombos(id, breakdown, currentConsensus, currentSignal.direction);
                  });
                  const pendingModels = Object.entries(insights).filter(([, ins]) => ins.isPending);

                  return (
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-3">
                        {Object.entries(breakdown).map(([id, info]) => (
                          <ModelDot
                            key={id}
                            modelId={id}
                            label={MODEL_LABELS[id] || id}
                            direction={info.direction}
                            agrees={info.agrees}
                            confidence={info.confidence}
                            insight={insights[id] || { bestWinRate: 0, bestCombo: "", isPending: false, pendingCombo: "", pendingComboWR: 0 }}
                          />
                        ))}
                      </div>
                      {pendingModels.length > 0 && (
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                          <span className="text-yellow-400/80">
                            {pendingModels.map(([id, ins]) => `${MODEL_LABELS[id] || id} → ${ins.pendingCombo} (${Math.round(ins.pendingComboWR * 100)}%)`).join(" • ")}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            </div>

            {currentConsensus && (
              <div className="rounded-xl bg-white/[0.03] border border-white/[0.04] p-3">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] uppercase tracking-[0.15em] text-[#6B7280] font-medium">
                    Directional combo map
                  </span>
                  <span className="text-[11px] text-[#6B7280]">
                    {currentConsensus.parameters?.lookback_days || 0}D • {currentConsensus.parameters?.bucket_minutes || 0}m
                  </span>
                </div>
                <ConsensusComboBoard data={currentConsensus} compact maxRows={2} />
              </div>
            )}

            {/* Row 2: Technical Score + Conditions */}
            <div className="rounded-xl bg-white/[0.03] border border-white/[0.04] p-3">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-[10px] uppercase tracking-[0.15em] text-[#6B7280] font-medium">
                  {t("meta_engine.tech_validation")}
                </span>
                <span className="text-sm font-bold" style={{
                  color: (currentSignal.technical_score || 0) >= 0.6 ? "#16C784" : (currentSignal.technical_score || 0) >= 0.4 ? "#F5A623" : "#EA3943"
                }}>
                  {Math.round((currentSignal.technical_score || 0) * 100)}%
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 rounded-full bg-white/[0.06] mb-3">
                <div
                  className="h-1.5 rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.round((currentSignal.technical_score || 0) * 100)}%`,
                    backgroundColor: (currentSignal.technical_score || 0) >= 0.6 ? "#16C784" : (currentSignal.technical_score || 0) >= 0.4 ? "#F5A623" : "#EA3943",
                  }}
                />
              </div>

              {/* Condition dots grid */}
              <div className="grid grid-cols-4 gap-1.5">
                {ALL_CONDITIONS.map((cond) => (
                  <TechConditionDot
                    key={cond}
                    name={cond}
                    passed={(currentSignal.passed_conditions || []).includes(cond)}
                  />
                ))}
              </div>
            </div>

            {/* Row 3: Risk Parameters */}
            {currentSignal.direction !== "HOLD" && currentSignal.entry_price > 0 && (
              <div className="rounded-xl bg-white/[0.03] border border-white/[0.04] p-3">
                <span className="text-[10px] uppercase tracking-[0.15em] text-[#6B7280] font-medium block mb-2">
                  {t("meta_engine.risk_params")}
                </span>
                <div className="grid grid-cols-5 gap-2">
                  {[
                    { label: "Entry", value: currentSignal.entry_price, color: "#E6EDF3" },
                    { label: "TP1", value: currentSignal.take_profit_1, color: "#16C784" },
                    { label: "TP2", value: currentSignal.take_profit_2, color: "#16C784" },
                    { label: "SL", value: currentSignal.stop_loss, color: "#EA3943" },
                    { label: "R:R", value: currentSignal.risk_reward, color: "#4F8CFF" },
                  ].map((item) => (
                    <div key={item.label} className="text-center">
                      <div className="text-[9px] text-[#6B7280] mb-0.5">{item.label}</div>
                      <div className="text-xs font-bold font-mono" style={{ color: item.color }}>
                        {item.label === "R:R"
                          ? `${item.value}x`
                          : item.value?.toLocaleString(undefined, { maximumFractionDigits: 2 })
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Row 4: Alternative Combos */}
            {currentSignal.alternatives && currentSignal.alternatives.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-[0.15em] text-[#6B7280] font-medium">
                  {t("meta_engine.alt_combos")}
                </span>
                {currentSignal.alternatives.map((alt, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.03]">
                    <span className="text-[11px] font-mono text-[#9AA4B2]">{alt.combo_key}</span>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-[#6B7280]">{alt.total_signals} {t("meta_engine.signals")}</span>
                      <span className="font-semibold" style={{ color: (alt.win_rate || 0) >= 0.6 ? "#16C784" : "#F5A623" }}>
                        {Math.round((alt.win_rate || 0) * 100)}% WR
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
