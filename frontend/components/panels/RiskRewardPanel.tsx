/**
 * Risk/Reward Panel
 * ==================
 * Pure mathematical calculation for risk management.
 * NO DeepSeek/AI - Kelly Criterion, ATR, position sizing formulas.
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { fetcher } from '../../lib/api';
import { 
  Shield, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  RefreshCw,
  DollarSign,
  Target,
  Percent
} from 'lucide-react';

const SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"];
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL"
};

interface RiskData {
  symbol: string;
  timestamp: string;
  current_price: number;
  direction: 'long' | 'short';
  atr_14: number;
  kelly_criterion: {
    kelly_pct: number;
    fractional_kelly: number;
    recommendation: string;
    reason: string;
    edge_ratio: number;
  };
  stop_loss: {
    price: number;
    distance: number;
    distance_pct: number;
    method: string;
  };
  take_profits: Array<{
    level: number;
    price: number;
    r_r_ratio: number;
    distance_pct: number;
  }>;
  position_sizing: {
    units: number;
    adjusted_units: number;
    position_value: number;
    risk_amount: number;
    risk_pct: number;
    volatility_adjustment: number;
  };
  trailing_stop: {
    activated: boolean;
    activation_rr: number;
    current_rr: number;
    trail_price: number;
  };
  volatility: {
    adjustment: number;
    volatility_regime: string;
    current_volatility: number;
    historical_volatility: number;
  };
  recommendations: {
    position_size: string;
    max_risk: string;
    stop_loss: string;
    primary_target: string;
  };
}

interface RiskRewardPanelProps {
  symbol?: string;
}

export default function RiskRewardPanel({ symbol }: RiskRewardPanelProps) {
  const initialSymbol = symbol ?? "NDX.INDX";
  const isSymbolLocked = Boolean(symbol);
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [direction, setDirection] = useState<'long' | 'short'>('long');
  const [accountSize, setAccountSize] = useState(10000);
  const [riskPerTrade, setRiskPerTrade] = useState(1.0);

  useEffect(() => {
    setActiveSymbol(initialSymbol);
  }, [initialSymbol]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetcher<{ success?: boolean; data?: RiskData; error?: string }>(
        `/api/deepseek/risk/${activeSymbol}?direction=${direction}&account_size=${accountSize}&risk_per_trade=${riskPerTrade}`
      );
      
      if (result.success) {
        setData(result.data || null);
      } else {
        setError(result.error || 'Failed to fetch risk data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, direction, accountSize, riskPerTrade]);

  useEffect(() => {
    fetchData();
  }, [fetchData, activeSymbol]);

  // Refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const getKellyColor = (recommendation: string) => {
    switch (recommendation) {
      case 'avoid': return 'text-red-400';
      case 'minimal': return 'text-orange-400';
      case 'conservative': return 'text-yellow-400';
      case 'moderate': return 'text-blue-400';
      case 'aggressive': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-5 h-5 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <span className="text-sm">Calculating risk...</span>
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
            className="mt-3 px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded text-xs hover:bg-blue-500/30 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { kelly_criterion, stop_loss, take_profits, position_sizing, volatility, trailing_stop } = data;

  return (
    <div className="h-full flex flex-col p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-white">Risk/Reward</span>
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

      {/* Direction & Settings */}
      <div className="flex items-center gap-2 mb-3">
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
        <select 
          value={riskPerTrade}
          onChange={(e) => setRiskPerTrade(Number(e.target.value))}
          className="bg-gray-800/50 text-xs text-white rounded px-2 py-1 border border-gray-700"
        >
          <option value={0.5}>0.5% Risk</option>
          <option value={1.0}>1% Risk</option>
          <option value={1.5}>1.5% Risk</option>
          <option value={2.0}>2% Risk</option>
        </select>
      </div>

      {/* Kelly Criterion */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          Kelly Criterion
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-300">Optimal Position</span>
          <span className="text-lg font-bold text-blue-400">{kelly_criterion.fractional_kelly.toFixed(2)}%</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-300">Recommendation</span>
          <span className={`text-sm font-medium ${getKellyColor(kelly_criterion.recommendation)}`}>
            {kelly_criterion.recommendation}
          </span>
        </div>
        <div className="mt-2 text-xs text-gray-500">{kelly_criterion.reason}</div>
      </div>

      {/* Stop Loss & Take Profits */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <Target className="w-3 h-3" />
          Levels
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Entry</span>
            <span className="text-sm font-mono text-white">{data.current_price.toFixed(2)}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-300">Stop Loss</span>
            <div className="text-right">
              <span className="text-sm font-mono text-red-400">{stop_loss.price.toFixed(2)}</span>
              <span className="text-xs text-gray-500 ml-2">({stop_loss.distance_pct.toFixed(1)}%)</span>
            </div>
          </div>
          
          {take_profits.map((tp) => (
            <div key={tp.level} className="flex items-center justify-between">
              <span className="text-xs text-gray-300">TP{tp.level}</span>
              <div className="text-right">
                <span className="text-sm font-mono text-green-400">{tp.price.toFixed(2)}</span>
                <span className="text-xs text-blue-400 ml-2">{tp.r_r_ratio}:1 R:R</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Position Sizing */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
          <DollarSign className="w-3 h-3" />
          Position Sizing
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-gray-500">Units</div>
            <div className="text-lg font-mono text-white">{position_sizing.adjusted_units.toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Position Value</div>
            <div className="text-lg font-mono text-white">${position_sizing.position_value.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Risk Amount</div>
            <div className="text-sm font-mono text-red-400">${position_sizing.risk_amount.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Risk %</div>
            <div className="text-sm font-mono text-yellow-400">{position_sizing.risk_pct.toFixed(1)}%</div>
          </div>
        </div>
        
        {volatility.adjustment !== 1 && (
          <div className="mt-2 text-xs">
            <span className="text-gray-500">Volatility Adjustment: </span>
            <span className={volatility.adjustment > 1 ? 'text-green-400' : 'text-red-400'}>
              {volatility.adjustment > 1 ? '+' : ''}{((volatility.adjustment - 1) * 100).toFixed(0)}%
            </span>
            <span className="text-gray-500 ml-1">({volatility.volatility_regime} volatility)</span>
          </div>
        )}
      </div>

      {/* Trailing Stop */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2">Trailing Stop</div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-300">Status</span>
          <span className={`text-xs ${trailing_stop.activated ? 'text-green-400' : 'text-gray-400'}`}>
            {trailing_stop.activated ? 'Activated' : 'Not Active'}
          </span>
        </div>
        {trailing_stop.activated && (
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-gray-300">Trail Price</span>
            <span className="text-sm font-mono text-blue-400">{trailing_stop.trail_price.toFixed(2)}</span>
          </div>
        )}
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-gray-300">Current R:R</span>
          <span className="text-sm font-mono text-white">{trailing_stop.current_rr.toFixed(2)}:1</span>
        </div>
      </div>

      {/* Summary */}
      <div className={`rounded-lg p-3 ${
        kelly_criterion.recommendation === 'avoid' ? 'bg-red-500/10 border border-red-500/20' :
        kelly_criterion.recommendation === 'conservative' ? 'bg-yellow-500/10 border border-yellow-500/20' :
        'bg-green-500/10 border border-green-500/20'
      }`}>
        <div className="text-xs text-gray-400 mb-2">Summary</div>
        <ul className="space-y-1">
          <li className="text-xs text-gray-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            {data.recommendations.position_size}
          </li>
          <li className="text-xs text-gray-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            {data.recommendations.stop_loss}
          </li>
          <li className="text-xs text-gray-300 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
            {data.recommendations.primary_target}
          </li>
        </ul>
      </div>

      {/* Footer */}
      <div className="mt-auto pt-2 border-t border-gray-700 text-center">
        <p className="text-xs text-gray-500">
          Pure math • ATR: {data.atr_14.toFixed(2)}
        </p>
      </div>
    </div>
  );
}
