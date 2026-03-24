/**
 * Smart Setup Generator Panel
 * ============================
 * Combines SMC, Risk/Reward, and Seasonality into one unified view.
 * Uses rule-based calculations (FREE, instant) instead of DeepSeek API calls.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboardStore } from "@/lib/store";
import { fetcher } from '../../lib/api';
import { 
  Target, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  Calendar, 
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  BarChart3,
  Layers,
  Clock,
  ChevronDown,
  ChevronUp,
  Info
} from 'lucide-react';

const SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"];
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL"
};

interface SmartSetupData {
  symbol: string;
  direction: 'long' | 'short';
  current_price: number;
  timestamp: string;
  setup: {
    grade: 'A' | 'B' | 'C' | 'D' | 'F';
    score: number;
    verdict: string;
    alignment_factors: string[];
    warnings: string[];
    recommendation: 'proceed' | 'caution' | 'avoid';
    confidence: number;
  };
  smc: {
    market_structure: {
      current_trend: string;
      swing_high: number;
      swing_low: number;
    };
    order_blocks: Array<{
      type: 'bullish' | 'bearish';
      price_high: number;
      price_low: number;
      strength: number;
      status: string;
    }>;
    fair_value_gaps: Array<{
      direction: string;
      high: number;
      low: number;
      fill_pct: number;
      status: string;
    }>;
    liquidity_pools: Array<{
      type: string;
      price: number;
      strength: string;
      swept: boolean;
    }>;
    bias: {
      direction: string;
      confidence: number;
      key_level_to_watch: number;
      invalidation: number;
      narrative: string;
    };
  };
  risk: {
    atr_14: number;
    kelly_criterion: {
      kelly_pct: number;
      fractional_kelly: number;
      recommendation: string;
    };
    stop_loss: {
      price: number;
      distance_pct: number;
    };
    take_profits: Array<{
      level: number;
      price: number;
      r_r_ratio: number;
    }>;
    position_sizing: {
      adjusted_units: number;
      risk_amount: number;
    };
    volatility: {
      volatility_regime: string;
      adjustment: number;
    };
  };
  seasonality: {
    monthly: {
      avg_return_pct: number;
      win_rate: number;
      bias: string;
    };
    day_of_week: {
      day: string;
      avg_return_pct: number;
      bias: string;
    };
    bias: {
      direction: string;
      confidence: number;
      factors: string[];
    };
  };
}

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-400 bg-green-400/20 border-green-400/30',
  B: 'text-emerald-400 bg-emerald-400/20 border-emerald-400/30',
  C: 'text-yellow-400 bg-yellow-400/20 border-yellow-400/30',
  D: 'text-orange-400 bg-orange-400/20 border-orange-400/30',
  F: 'text-red-400 bg-red-400/20 border-red-400/30',
};

const RECOMMENDATION_COLORS: Record<string, string> = {
  proceed: 'text-green-400',
  caution: 'text-yellow-400',
  avoid: 'text-red-400',
};

export default function SmartSetupPanel() {
  const [activeSymbol, setActiveSymbol] = useState("NDX.INDX");
  
  const [data, setData] = useState<SmartSetupData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [direction, setDirection] = useState<'long' | 'short'>('long');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    smc: true,
    risk: false,
    seasonality: false,
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetcher<{ success?: boolean; data?: SmartSetupData; error?: string }>(
        `/api/deepseek/smart-setup/${activeSymbol}?direction=${direction}&account_size=10000&risk_per_trade=1.0`
      );
      
      if (result.success) {
        setData(result.data || null);
      } else {
        setError(result.error || 'Failed to fetch data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, direction]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData, activeSymbol]);

  // Refresh every 5 minutes (rule-based is cheap, can refresh more often)
  useEffect(() => {
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const toggleSection = (section: string) => {
    setExpanded(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm">Calculating setup...</span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-400 text-sm">{error}</p>
          <button 
            onClick={fetchData}
            className="mt-3 px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { setup, smc, risk, seasonality } = data;

  return (
    <div className="h-full flex flex-col p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-semibold text-white">Smart Setup</span>
          <span className="text-xs text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded">FREE</span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={activeSymbol}
            onChange={(e) => setActiveSymbol(e.target.value)}
            className="bg-gray-800 text-xs text-white rounded px-2 py-1 border border-gray-700"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>{SYMBOL_LABELS[s]}</option>
            ))}
          </select>
          <div className="flex items-center gap-1 bg-gray-800/50 rounded p-0.5">
          <button
            onClick={() => setDirection('long')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              direction === 'long' 
                ? 'bg-green-500/20 text-green-400' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Long
          </button>
          <button
            onClick={() => setDirection('short')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              direction === 'short' 
                ? 'bg-red-500/20 text-red-400' 
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Short
          </button>
          </div>
        </div>
      </div>

      {/* Grade Card */}
      <div className={`rounded-lg p-3 mb-3 border ${GRADE_COLORS[setup.grade]}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-3xl font-bold">{setup.grade}</div>
            <div className="text-xs opacity-80">{setup.verdict}</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{setup.score}</div>
            <div className="text-xs opacity-80">Setup Score</div>
          </div>
        </div>
        <div className="mt-2 flex items-center gap-2">
          <div className={`text-xs font-medium ${RECOMMENDATION_COLORS[setup.recommendation]}`}>
            {setup.recommendation.toUpperCase()}
          </div>
          <div className="text-xs text-gray-400">
            Confidence: {setup.confidence}%
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-400">SMC</div>
          <div className={`text-sm font-medium ${
            smc.bias.direction === 'bullish' ? 'text-green-400' :
            smc.bias.direction === 'bearish' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {smc.bias.direction}
          </div>
        </div>
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-400">R:R</div>
          <div className="text-sm font-medium text-blue-400">
            {risk.take_profits[0]?.r_r_ratio.toFixed(1) || 'N/A'}:1
          </div>
        </div>
        <div className="bg-gray-800/30 rounded p-2 text-center">
          <div className="text-xs text-gray-400">Season</div>
          <div className={`text-sm font-medium ${
            seasonality.bias.direction === 'bullish' ? 'text-green-400' :
            seasonality.bias.direction === 'bearish' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {seasonality.bias.direction}
          </div>
        </div>
      </div>

      {/* Key Levels */}
      <div className="bg-gray-800/30 rounded-lg p-2 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <Target className="w-3 h-3" />
          Key Levels
        </div>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Entry</span>
            <span className="text-white font-mono">{data.current_price.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Stop Loss</span>
            <span className="text-red-400 font-mono">{risk.stop_loss.price.toFixed(2)}</span>
          </div>
          {risk.take_profits.slice(0, 2).map((tp) => (
            <div key={tp.level} className="flex justify-between">
              <span className="text-gray-400">TP{tp.level} ({tp.r_r_ratio}:1)</span>
              <span className="text-green-400 font-mono">{tp.price.toFixed(2)}</span>
            </div>
          ))}
          <div className="flex justify-between pt-1 border-t border-gray-700">
            <span className="text-gray-400">Key Level</span>
            <span className="text-blue-400 font-mono">{smc.bias.key_level_to_watch.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* SMC Section */}
      <div className="mb-2">
        <button 
          onClick={() => toggleSection('smc')}
          className="w-full flex items-center justify-between p-2 bg-gray-800/30 rounded hover:bg-gray-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span className="text-sm font-medium">Smart Money</span>
          </div>
          {expanded.smc ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {expanded.smc && (
          <div className="mt-2 space-y-2">
            {/* Order Blocks */}
            {smc.order_blocks.length > 0 && (
              <div className="bg-gray-800/20 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Order Blocks</div>
                <div className="space-y-1">
                  {smc.order_blocks.slice(0, 3).map((ob, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className={ob.type === 'bullish' ? 'text-green-400' : 'text-red-400'}>
                        {ob.type === 'bullish' ? 'Bull' : 'Bear'} OB
                      </span>
                      <span className="text-gray-400">{ob.price_low.toFixed(1)}-{ob.price_high.toFixed(1)}</span>
                      <span className={`text-xs px-1 rounded ${
                        ob.status === 'fresh' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {ob.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* FVGs */}
            {smc.fair_value_gaps.length > 0 && (
              <div className="bg-gray-800/20 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Fair Value Gaps</div>
                <div className="space-y-1">
                  {smc.fair_value_gaps.map((fvg, i) => (
                    <div key={i} className="flex items-center justify-between text-xs">
                      <span className={fvg.direction === 'bullish' ? 'text-green-400' : 'text-red-400'}>
                        {fvg.direction}
                      </span>
                      <span className="text-gray-400">{fvg.fill_pct.toFixed(0)}% filled</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bias */}
            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Bias Narrative</div>
              <p className="text-xs text-gray-300">{smc.bias.narrative}</p>
            </div>
          </div>
        )}
      </div>

      {/* Risk Section */}
      <div className="mb-2">
        <button 
          onClick={() => toggleSection('risk')}
          className="w-full flex items-center justify-between p-2 bg-gray-800/30 rounded hover:bg-gray-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium">Risk Management</span>
          </div>
          {expanded.risk ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {expanded.risk && (
          <div className="mt-2 space-y-2">
            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Kelly Criterion</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300">Optimal Position</span>
                <span className="text-blue-400">{risk.kelly_criterion.fractional_kelly.toFixed(2)}%</span>
              </div>
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-gray-300">Recommendation</span>
                <span className={`${
                  risk.kelly_criterion.recommendation === 'avoid' ? 'text-red-400' :
                  risk.kelly_criterion.recommendation === 'conservative' ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {risk.kelly_criterion.recommendation}
                </span>
              </div>
            </div>

            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Position Sizing</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300">Units</span>
                <span className="text-white font-mono">{risk.position_sizing.adjusted_units.toFixed(2)}</span>
              </div>
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-gray-300">Risk Amount</span>
                <span className="text-white font-mono">${risk.position_sizing.risk_amount.toFixed(0)}</span>
              </div>
            </div>

            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Volatility</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300">Regime</span>
                <span className={`${
                  risk.volatility.volatility_regime === 'high' ? 'text-red-400' :
                  risk.volatility.volatility_regime === 'low' ? 'text-green-400' :
                  'text-yellow-400'
                }`}>
                  {risk.volatility.volatility_regime}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-gray-300">ATR (14)</span>
                <span className="text-white font-mono">{risk.atr_14.toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Seasonality Section */}
      <div className="mb-2">
        <button 
          onClick={() => toggleSection('seasonality')}
          className="w-full flex items-center justify-between p-2 bg-gray-800/30 rounded hover:bg-gray-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-orange-400" />
            <span className="text-sm font-medium">Seasonality</span>
          </div>
          {expanded.seasonality ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {expanded.seasonality && (
          <div className="mt-2 space-y-2">
            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Monthly Stats</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300">Avg Return</span>
                <span className={seasonality.monthly.avg_return_pct > 0 ? 'text-green-400' : 'text-red-400'}>
                  {seasonality.monthly.avg_return_pct > 0 ? '+' : ''}{seasonality.monthly.avg_return_pct.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between text-xs mt-1">
                <span className="text-gray-300">Win Rate</span>
                <span className="text-white">{seasonality.monthly.win_rate}%</span>
              </div>
            </div>

            <div className="bg-gray-800/20 rounded p-2">
              <div className="text-xs text-gray-400 mb-1">Day of Week</div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{seasonality.day_of_week.day}</span>
                <span className={seasonality.day_of_week.avg_return_pct > 0 ? 'text-green-400' : 'text-red-400'}>
                  {seasonality.day_of_week.avg_return_pct > 0 ? '+' : ''}{seasonality.day_of_week.avg_return_pct.toFixed(2)}%
                </span>
              </div>
            </div>

            {seasonality.bias.factors.length > 0 && (
              <div className="bg-gray-800/20 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Factors</div>
                <ul className="space-y-0.5">
                  {seasonality.bias.factors.slice(0, 3).map((factor, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-1">
                      <CheckCircle className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Warnings */}
      {setup.warnings.length > 0 && (
        <div className="mt-2 bg-red-500/10 border border-red-500/20 rounded p-2">
          <div className="flex items-center gap-1 text-red-400 text-xs font-medium mb-1">
            <AlertTriangle className="w-3 h-3" />
            Warnings
          </div>
          <ul className="space-y-0.5">
            {setup.warnings.map((warning, i) => (
              <li key={i} className="text-xs text-red-300 flex items-start gap-1">
                <XCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Alignment Factors */}
      {setup.alignment_factors.length > 0 && (
        <div className="mt-2 bg-green-500/10 border border-green-500/20 rounded p-2">
          <div className="flex items-center gap-1 text-green-400 text-xs font-medium mb-1">
            <CheckCircle className="w-3 h-3" />
            Alignment Factors
          </div>
          <ul className="space-y-0.5">
            {setup.alignment_factors.map((factor, i) => (
              <li key={i} className="text-xs text-green-300 flex items-start gap-1">
                <CheckCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-2 border-t border-gray-700 text-center">
        <p className="text-xs text-gray-500">
          Rule-based calculation • Updated {new Date(data.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
