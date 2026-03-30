/**
 * SMC Panel - Smart Money Concepts Analysis
 * ==========================================
 * Now uses rule-based geometric calculation (FREE, instant).
 * Previously used DeepSeek API (expensive, slow).
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { fetcher } from '../../lib/api';
import { useRefreshAge } from '../../hooks/useRefreshAge';
import { 
  Layers, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  RefreshCw,
  Zap,
  Clock3
} from 'lucide-react';

const SYMBOLS = ["NDX.INDX", "XAUUSD", "GDAXI.INDX", "USOIL.FOREX"];
const SYMBOL_LABELS: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "XAUUSD": "XAU/USD",
  "GDAXI.INDX": "DAX",
  "USOIL.FOREX": "US OIL"
};

interface GapInfo {
  date: string;
  prev_close: number;
  today_open: number;
  size: number;
  size_pct: number;
  atr_multiple: number;
  classification: string;
  direction: string;
  fill_probability: number;
  is_fvg: boolean;
  strength: string;
}

interface SMCData {
  symbol: string;
  timestamp: string;
  market_structure: {
    current_trend: string;
    last_bos: any;
    last_choch: any;
    swing_high: number;
    swing_low: number;
  };
  order_blocks: Array<{
    type: 'bullish' | 'bearish';
    price_high: number;
    price_low: number;
    strength: number;
    status: string;
    timeframe: string;
  }>;
  fair_value_gaps: Array<{
    direction: string;
    high: number;
    low: number;
    fill_pct: number;
    status: string;
    type?: string;
    strength?: string;
  }>;
  liquidity_pools: Array<{
    type: string;
    price: number;
    strength: string;
    swept: boolean;
  }>;
  breaker_blocks: Array<{
    type: string;
    price_high: number;
    price_low: number;
    status: string;
  }>;
  bias: {
    direction: string;
    confidence: number;
    key_level_to_watch: number;
    invalidation: number;
    narrative: string;
    score: number;
  };
  gaps: GapInfo[];
  atr_20: number;
  gap_analysis_enabled: boolean;
  calculation_method: string;
}

interface SMCPanelProps {
  lockedSymbol?: string;
}

export default function SMCPanel({ lockedSymbol }: SMCPanelProps) {
  const [activeSymbol, setActiveSymbol] = useState(lockedSymbol || "NDX.INDX");
  const [data, setData] = useState<SMCData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshAge, markRefreshed } = useRefreshAge(data?.timestamp ? new Date(data.timestamp) : null);

  useEffect(() => {
    if (lockedSymbol) {
      setActiveSymbol(lockedSymbol);
    }
  }, [lockedSymbol]);

  useEffect(() => {
    if (data?.timestamp) {
      markRefreshed(data.timestamp);
    }
  }, [data?.timestamp, markRefreshed]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetcher<{ success?: boolean; data?: SMCData; error?: string }>(`/api/deepseek/smc/${activeSymbol}`);
      
      if (result.success) {
        setData(result.data || null);
      } else {
        setError(result.error || 'Failed to fetch SMC data');
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

  // Refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-5 h-5 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
          <span className="text-sm">Analyzing price action...</span>
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
            className="mt-3 px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded text-xs hover:bg-purple-500/30 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { market_structure, order_blocks, fair_value_gaps, liquidity_pools, bias } = data;

  return (
    <div className="h-full flex flex-col p-3 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-semibold text-white">Smart Money</span>
          <span className="text-xs text-green-400 bg-green-400/10 px-1.5 py-0.5 rounded">FREE</span>
        </div>
        <div className="flex items-center gap-2">
          {lockedSymbol ? (
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

      {data?.timestamp && (
        <div className="mb-3 flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-gray-400">
          <div className="flex items-center gap-2">
            <Clock3 className="h-3.5 w-3.5" />
            <span>Last analysis: {new Date(data.timestamp).toLocaleString()}</span>
          </div>
          <span className="rounded-full bg-purple-500/10 px-2 py-0.5 font-medium text-purple-300">{refreshAge}</span>
        </div>
      )}

      {/* Market Structure */}
      <div className="bg-gray-800/30 rounded-lg p-3 mb-3">
        <div className="text-xs text-gray-400 mb-2">Market Structure</div>
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-sm font-medium ${
            market_structure.current_trend === 'bullish' ? 'text-green-400' :
            market_structure.current_trend === 'bearish' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {market_structure.current_trend.toUpperCase()}
          </span>
          <span className="text-xs text-gray-500">
            SH: {market_structure.swing_high.toFixed(1)} / SL: {market_structure.swing_low.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Bias */}
      <div className={`rounded-lg p-3 mb-3 ${
        bias.direction === 'bullish' ? 'bg-green-500/10 border border-green-500/20' :
        bias.direction === 'bearish' ? 'bg-red-500/10 border border-red-500/20' :
        'bg-yellow-500/10 border border-yellow-500/20'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Bias</span>
          <span className={`text-sm font-bold ${
            bias.direction === 'bullish' ? 'text-green-400' :
            bias.direction === 'bearish' ? 'text-red-400' : 'text-yellow-400'
          }`}>
            {bias.direction.toUpperCase()}
          </span>
        </div>
        <div className="text-xs text-gray-300 mb-2">{bias.narrative}</div>
        <div className="flex items-center gap-4 text-xs">
          <div>
            <span className="text-gray-500">Key Level: </span>
            <span className="text-blue-400 font-mono">{bias.key_level_to_watch.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-gray-500">Invalidation: </span>
            <span className="text-red-400 font-mono">{bias.invalidation.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Order Blocks */}
      {order_blocks.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-400 mb-2">Order Blocks ({order_blocks.length})</div>
          <div className="space-y-1.5">
            {order_blocks.map((ob, i) => (
              <div key={i} className="bg-gray-800/30 rounded p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${
                    ob.type === 'bullish' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {ob.type === 'bullish' ? 'Bull' : 'Bear'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {ob.price_low.toFixed(1)} - {ob.price_high.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-0.5">
                    {Array.from({ length: 10 }).map((_, j) => (
                      <div 
                        key={j} 
                        className={`w-1 h-3 rounded-sm ${
                          j < ob.strength ? 'bg-purple-400' : 'bg-gray-700'
                        }`}
                      />
                    ))}
                  </div>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    ob.status === 'fresh' ? 'bg-green-500/20 text-green-400' : 
                    ob.status === 'tested' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {ob.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fair Value Gaps */}
      {fair_value_gaps.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-400 mb-2">
            Fair Value Gaps ({fair_value_gaps.length})
            <span className="text-xs text-gray-500 ml-1">(Gap FVGs = Strong)</span>
          </div>
          <div className="space-y-1.5">
            {fair_value_gaps.map((fvg, i) => (
              <div key={i} className={`rounded p-2 flex items-center justify-between ${
                fvg.type === 'gap_fvg' ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-gray-800/30'
              }`}>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${
                    fvg.direction?.includes('bullish') ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {fvg.direction?.includes('gap') ? '⚡ ' : ''}{fvg.direction}
                  </span>
                  {fvg.type === 'gap_fvg' && (
                    <span className="text-xs text-yellow-400 bg-yellow-400/10 px-1 rounded">
                      GAP
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {fvg.low.toFixed(1)} - {fvg.high.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${
                        fvg.direction?.includes('bullish') ? 'bg-green-400' : 'bg-red-400'
                      }`}
                      style={{ width: `${fvg.fill_pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{fvg.fill_pct.toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Liquidity Pools */}
      {liquidity_pools.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-400 mb-2">Liquidity Pools ({liquidity_pools.length})</div>
          <div className="space-y-1.5">
            {liquidity_pools.map((pool, i) => (
              <div key={i} className="bg-gray-800/30 rounded p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium ${
                    pool.type === 'buy_side' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {pool.type === 'buy_side' ? 'Buy' : 'Sell'}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">
                    {pool.price.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs ${
                    pool.strength === 'strong' ? 'text-purple-400' :
                    pool.strength === 'moderate' ? 'text-blue-400' : 'text-gray-400'
                  }`}>
                    {pool.strength}
                  </span>
                  {pool.swept ? (
                    <span className="text-xs text-red-400">swept</span>
                  ) : (
                    <span className="text-xs text-green-400">active</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gap Analysis */}
      {data.gaps && data.gaps.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Gap Analysis (EOD)
            <span className="text-xs text-blue-400">ATR: {data.atr_20?.toFixed(2) || '--'}</span>
          </div>
          <div className="space-y-1.5">
            {data.gaps.slice(-3).map((gap, i) => (
              <div key={i} className={`bg-gray-800/30 rounded p-2 border-l-2 ${
                gap.direction === 'BULLISH' ? 'border-green-400' : 'border-red-400'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-medium ${
                      gap.direction === 'BULLISH' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {gap.direction === 'BULLISH' ? '↑' : '↓'} {gap.size_pct.toFixed(2)}%
                    </span>
                    <span className="text-xs text-gray-500">
                      {gap.atr_multiple.toFixed(1)}x ATR
                    </span>
                    {gap.is_fvg && (
                      <span className="text-xs text-yellow-400 bg-yellow-400/10 px-1 rounded">
                        FVG
                      </span>
                    )}
                  </div>
                  <span className={`text-xs ${
                    gap.classification === 'EXTREME_GAP' ? 'text-red-400' :
                    gap.classification === 'NORMAL_GAP' ? 'text-yellow-400' : 'text-gray-400'
                  }`}>
                    {gap.classification.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1 text-xs">
                  <span className="text-gray-500">
                    Fill Prob: {(gap.fill_probability * 100).toFixed(0)}%
                  </span>
                  <span className="text-gray-400">
                    {gap.prev_close.toFixed(1)} → {gap.today_open.toFixed(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-auto pt-2 border-t border-gray-700 text-center">
        <p className="text-xs text-gray-500">
          Gap-Aware • {data.gaps?.length || 0} gaps • ATR: {data.atr_20?.toFixed(2) || '--'}
        </p>
      </div>
    </div>
  );
}
