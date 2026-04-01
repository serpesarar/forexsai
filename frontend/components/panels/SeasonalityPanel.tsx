/**
 * Seasonality Panel
 * ==================
 * Historical statistics analysis for seasonal patterns.
 * NO DeepSeek/AI - Database aggregation of 15+ years of data.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { fetcher } from '../../lib/api';
import { 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  RefreshCw,
  Sun,
  Moon,
  Activity
} from 'lucide-react';

const SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"];
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL"
};

interface SeasonalityData {
  symbol: string;
  timestamp: string;
  current_period: {
    month: number;
    day_of_week: string;
    quarter: string;
  };
  monthly: {
    current_month: number;
    avg_return_pct: number;
    win_rate: number;
    volatility: number;
    return_rank: number;
    win_rate_rank: number;
    bias: string;
  };
  day_of_week: {
    day: string;
    avg_return_pct: number;
    win_rate: number;
    bias: string;
  };
  quarterly: {
    quarter: string;
    avg_return_pct: number;
    win_rate: number;
    volatility: number;
    bias: string;
  };
  session_analysis: {
    asian: { activity_pct: number; trend_continuation: number; avg_range_pct: number };
    london: { activity_pct: number; trend_continuation: number; avg_range_pct: number };
    new_york: { activity_pct: number; trend_continuation: number; avg_range_pct: number };
  };
  recent_anomalies: Array<{
    date: string;
    return_pct: number;
    type: string;
    magnitude: string;
  }>;
  bias: {
    direction: string;
    confidence: number;
    score: number;
    factors: string[];
  };
  best_months: Array<{
    month: number;
    avg_return: number;
    win_rate: number;
  }>;
  worst_months: Array<{
    month: number;
    avg_return: number;
    win_rate: number;
  }>;
}

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

interface SeasonalityPanelProps {
  symbol?: string;
}

export default function SeasonalityPanel({ symbol }: SeasonalityPanelProps) {
  const initialSymbol = symbol ?? "NDX.INDX";
  const isSymbolLocked = Boolean(symbol);
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<SeasonalityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setActiveSymbol(initialSymbol);
  }, [initialSymbol]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetcher<{ success?: boolean; data?: SeasonalityData; error?: string }>(`/api/deepseek/seasonality/${activeSymbol}`);
      
      if (result.success) {
        setData(result.data || null);
      } else {
        setError(result.error || 'Failed to fetch seasonality data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [activeSymbol]);

  useEffect(() => {
    fetchData();
  }, [fetchData, activeSymbol]);

  // Refresh every hour (seasonality doesn't change often)
  useEffect(() => {
    const interval = setInterval(fetchData, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const getBiasColor = (bias: string) => {
    switch (bias) {
      case 'bullish': return 'text-green-400';
      case 'bearish': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getBiasBg = (bias: string) => {
    switch (bias) {
      case 'bullish': return 'bg-green-400/10 border-green-400/20';
      case 'bearish': return 'bg-red-400/10 border-red-400/20';
      default: return 'bg-yellow-400/10 border-yellow-400/20';
    }
  };

  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-5 h-5 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
          <span className="text-sm">Loading historical data...</span>
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-400 text-sm">{error}</p>
          <button 
            onClick={fetchData}
            className="mt-3 px-3 py-1.5 bg-orange-500/20 text-orange-400 rounded text-xs hover:bg-orange-500/30 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { monthly, day_of_week, quarterly, session_analysis, bias, best_months, worst_months } = data;

  return (
    <div className="h-full flex flex-col p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-orange-400" />
          <span className="text-sm font-semibold text-white">Seasonality</span>
          <span className="text-xs text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded">FREE</span>
        </div>
        <div className="flex items-center gap-2">
          {isSymbolLocked ? (
            <span className="bg-gray-800 text-xs text-white rounded px-2 py-1 border border-gray-700">
              {SYMBOL_LABELS[activeSymbol] || activeSymbol}
            </span>
          ) : (
            <select
              value={activeSymbol}
              onChange={(e) => setActiveSymbol(e.target.value)}
              className="bg-gray-800 text-xs text-white rounded px-2 py-1 border border-gray-700"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>{SYMBOL_LABELS[s]}</option>
              ))}
            </select>
          )}
          <button 
            onClick={fetchData}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Overall Bias */}
      <div className={`rounded-lg p-3 mb-3 border ${getBiasBg(bias.direction)}`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Seasonal Bias</span>
          <span className={`text-lg font-bold ${getBiasColor(bias.direction)}`}>
            {bias.direction.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Confidence</span>
          <span className="text-sm text-white">{bias.confidence}%</span>
        </div>
        <div className="mt-2 text-xs text-gray-300">
          Score: {bias.score > 0 ? '+' : ''}{bias.score}
        </div>
      </div>

      {/* Monthly Stats */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <Sun className="w-3 h-3" />
          {MONTH_NAMES[monthly.current_month - 1]} Statistics
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-gray-500">Avg Return</div>
            <div className={`text-lg font-mono ${monthly.avg_return_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {monthly.avg_return_pct > 0 ? '+' : ''}{monthly.avg_return_pct.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Win Rate</div>
            <div className="text-lg font-mono text-white">{monthly.win_rate}%</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Rank (Returns)</div>
            <div className="text-sm font-mono text-blue-400">#{monthly.return_rank}/12</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Volatility</div>
            <div className="text-sm font-mono text-yellow-400">{monthly.volatility.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Day of Week */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <Activity className="w-3 h-3" />
          {day_of_week.day} Statistics
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500">Avg Return</div>
            <div className={`text-lg font-mono ${day_of_week.avg_return_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {day_of_week.avg_return_pct > 0 ? '+' : ''}{day_of_week.avg_return_pct.toFixed(2)}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Bias</div>
            <div className={`text-sm font-medium ${getBiasColor(day_of_week.bias)}`}>
              {day_of_week.bias}
            </div>
          </div>
        </div>
      </div>

      {/* Quarterly */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2">{quarterly.quarter} Performance</div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500">Avg Return</div>
            <div className={`text-lg font-mono ${quarterly.avg_return_pct > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {quarterly.avg_return_pct > 0 ? '+' : ''}{quarterly.avg_return_pct.toFixed(1)}%
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Win Rate</div>
            <div className="text-sm font-mono text-white">{quarterly.win_rate}%</div>
          </div>
        </div>
      </div>

      {/* Session Analysis */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2">Session Activity</div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Asian</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-purple-400"
                  style={{ width: `${session_analysis.asian.activity_pct}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-8">{session_analysis.asian.activity_pct}%</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">London</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-400"
                  style={{ width: `${session_analysis.london.activity_pct}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-8">{session_analysis.london.activity_pct}%</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">New York</span>
            <div className="flex items-center gap-2">
              <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-400"
                  style={{ width: `${session_analysis.new_york.activity_pct}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-8">{session_analysis.new_york.activity_pct}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Best/Worst Months */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-gray-800/30 rounded-lg p-2">
          <div className="text-xs text-green-400 mb-1">Best Months</div>
          <div className="space-y-1">
            {best_months.map((m, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{MONTH_NAMES[m.month - 1]}</span>
                <span className="text-green-400">+{m.avg_return.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-gray-800/30 rounded-lg p-2">
          <div className="text-xs text-red-400 mb-1">Worst Months</div>
          <div className="space-y-1">
            {worst_months.map((m, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-gray-300">{MONTH_NAMES[m.month - 1]}</span>
                <span className="text-red-400">{m.avg_return.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Factors */}
      {bias.factors.length > 0 && (
        <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
          <div className="text-xs text-gray-400 mb-2">Key Factors</div>
          <ul className="space-y-1">
            {bias.factors.map((factor, i) => (
              <li key={i} className="text-xs text-gray-300 flex items-start gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-400 mt-1 flex-shrink-0" />
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto pt-2 border-t border-gray-700 text-center">
        <p className="text-xs text-gray-500">
          15+ year historical analysis
        </p>
      </div>
    </div>
  );
}
