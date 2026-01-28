"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Users,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  Activity,
  Gauge,
  BarChart3,
  Percent,
  Clock,
} from "lucide-react";
import { InfoClickable, InfoBadge } from "./InfoTooltip";

interface COTData {
  report_date: string;
  symbol: string;
  commercials_net: number;
  speculators_net: number;
  spec_long_percent: number;
  confidence_adjustment: number;
  signal: "BULLISH" | "BEARISH" | "NEUTRAL" | "TREND_EXHAUSTION";
  reason: string;
}

interface SlippageStats {
  average_slippage: number;
  max_slippage: number;
  favorable_count: number;
  unfavorable_count: number;
  total_trades: number;
  position_multiplier: number;
  high_slippage_mode: boolean;
}

interface InstitutionalDataPanelProps {
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function InstitutionalDataPanel({ className = "" }: InstitutionalDataPanelProps) {
  const [cotData, setCotData] = useState<{ XAUUSD: COTData; NASDAQ: COTData } | null>(null);
  const [slippageData, setSlippageData] = useState<SlippageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch COT and Slippage data in parallel
      const [cotRes, slippageRes] = await Promise.all([
        fetch(`${API_BASE}/api/cot/summary`),
        fetch(`${API_BASE}/api/slippage/stats`),
      ]);
      
      if (cotRes.ok) {
        const cotJson = await cotRes.json();
        if (cotJson.success) {
          setCotData(cotJson.data);
        }
      }
      
      if (slippageRes.ok) {
        const slippageJson = await slippageRes.json();
        if (slippageJson.success) {
          setSlippageData(slippageJson.data);
        }
      }
      
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [fetchData]);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case "BULLISH": return "text-green-400";
      case "BEARISH": return "text-red-400";
      case "TREND_EXHAUSTION": return "text-orange-400";
      default: return "text-gray-400";
    }
  };

  const getSignalBg = (signal: string) => {
    switch (signal) {
      case "BULLISH": return "bg-green-900/30 border-green-500/30";
      case "BEARISH": return "bg-red-900/30 border-red-500/30";
      case "TREND_EXHAUSTION": return "bg-orange-900/30 border-orange-500/30";
      default: return "bg-gray-800/50 border-gray-600/30";
    }
  };

  if (loading && !cotData && !slippageData) {
    return (
      <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-4 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-900/50 to-orange-900/50 px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-amber-400" />
            <span className="font-semibold text-white">Institutional Data</span>
            <span className="text-xs text-gray-400 ml-2">COT & Slippage</span>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                {lastUpdate.toLocaleTimeString()}
              </span>
            )}
            <button 
              onClick={fetchData}
              className="p-1 hover:bg-gray-700/50 rounded"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Slippage Monitor */}
        {slippageData && (
          <div className={`rounded-lg p-3 border ${slippageData.high_slippage_mode ? 'bg-red-900/20 border-red-500/30' : 'bg-gray-800/50 border-gray-700/30'}`}>
            <div className="flex items-center gap-2 mb-2">
              <Gauge className={`w-4 h-4 ${slippageData.high_slippage_mode ? 'text-red-400' : 'text-cyan-400'}`} />
              <span className="text-xs text-gray-400">Slippage Monitor</span>
              <InfoBadge infoKey="slippage" />
              {slippageData.high_slippage_mode && (
                <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full ml-auto">
                  ⚠️ HIGH
                </span>
              )}
            </div>
            
            <div className="grid grid-cols-3 gap-3 text-center">
              <InfoClickable infoKey="slippage">
                <div>
                  <div className={`text-lg font-bold ${slippageData.average_slippage > 3 ? 'text-red-400' : slippageData.average_slippage > 1.5 ? 'text-yellow-400' : 'text-green-400'}`}>
                    {slippageData.average_slippage.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">Avg Pips</div>
                </div>
              </InfoClickable>
              <div>
                <div className="text-lg font-bold text-white">
                  {(slippageData.position_multiplier * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">Position Size</div>
              </div>
              <div>
                <div className="text-lg font-bold text-gray-300">
                  {slippageData.total_trades}
                </div>
                <div className="text-xs text-gray-500">Trades</div>
              </div>
            </div>
            
            {slippageData.total_trades > 0 && (
              <div className="mt-2 flex items-center justify-center gap-4 text-xs">
                <span className="text-green-400">
                  ✓ {slippageData.favorable_count} favorable
                </span>
                <span className="text-red-400">
                  ✗ {slippageData.unfavorable_count} unfavorable
                </span>
              </div>
            )}
          </div>
        )}

        {/* COT Report - Gold */}
        {cotData?.XAUUSD && (
          <div className={`rounded-lg p-3 border ${getSignalBg(cotData.XAUUSD.signal)}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-medium text-white">GOLD COT</span>
                <InfoBadge infoKey="cot_speculators" />
              </div>
              <InfoClickable infoKey="cot_speculators">
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalColor(cotData.XAUUSD.signal)} cursor-help`}>
                  {cotData.XAUUSD.signal}
                </span>
              </InfoClickable>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mb-2">
              <InfoClickable infoKey="cot_commercials">
                <div className="text-center cursor-help hover:bg-gray-700/30 rounded p-1">
                  <div className="flex items-center justify-center gap-1">
                    <Users className="w-3 h-3 text-blue-400" />
                    <span className="text-xs text-gray-400">Commercials</span>
                  </div>
                  <div className={`text-sm font-bold ${cotData.XAUUSD.commercials_net > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {cotData.XAUUSD.commercials_net > 0 ? '+' : ''}{(cotData.XAUUSD.commercials_net / 1000).toFixed(0)}K
                  </div>
                </div>
              </InfoClickable>
              <InfoClickable infoKey="cot_speculators">
                <div className="text-center cursor-help hover:bg-gray-700/30 rounded p-1">
                  <div className="flex items-center justify-center gap-1">
                    <Activity className="w-3 h-3 text-purple-400" />
                    <span className="text-xs text-gray-400">Speculators</span>
                  </div>
                  <div className={`text-sm font-bold ${cotData.XAUUSD.speculators_net > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {cotData.XAUUSD.speculators_net > 0 ? '+' : ''}{(cotData.XAUUSD.speculators_net / 1000).toFixed(0)}K
                  </div>
                </div>
              </InfoClickable>
            </div>
            
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Spec Long: {cotData.XAUUSD.spec_long_percent.toFixed(0)}%</span>
              <span className={cotData.XAUUSD.confidence_adjustment > 0 ? 'text-green-400' : cotData.XAUUSD.confidence_adjustment < 0 ? 'text-red-400' : 'text-gray-400'}>
                Adj: {cotData.XAUUSD.confidence_adjustment > 0 ? '+' : ''}{(cotData.XAUUSD.confidence_adjustment * 100).toFixed(0)}%
              </span>
            </div>
            
            {cotData.XAUUSD.signal === "TREND_EXHAUSTION" && (
              <div className="mt-2 flex items-center gap-2 text-xs text-orange-400">
                <AlertTriangle className="w-3 h-3" />
                <span>{cotData.XAUUSD.reason}</span>
              </div>
            )}
          </div>
        )}

        {/* COT Report - NASDAQ */}
        {cotData?.NASDAQ && (
          <div className={`rounded-lg p-3 border ${getSignalBg(cotData.NASDAQ.signal)}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">NASDAQ COT</span>
              </div>
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalColor(cotData.NASDAQ.signal)}`}>
                {cotData.NASDAQ.signal}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mb-2">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1">
                  <Users className="w-3 h-3 text-blue-400" />
                  <span className="text-xs text-gray-400">Commercials</span>
                </div>
                <div className={`text-sm font-bold ${cotData.NASDAQ.commercials_net > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {cotData.NASDAQ.commercials_net > 0 ? '+' : ''}{(cotData.NASDAQ.commercials_net / 1000).toFixed(0)}K
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center gap-1">
                  <Activity className="w-3 h-3 text-purple-400" />
                  <span className="text-xs text-gray-400">Speculators</span>
                </div>
                <div className={`text-sm font-bold ${cotData.NASDAQ.speculators_net > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {cotData.NASDAQ.speculators_net > 0 ? '+' : ''}{(cotData.NASDAQ.speculators_net / 1000).toFixed(0)}K
                </div>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Spec Long: {cotData.NASDAQ.spec_long_percent.toFixed(0)}%</span>
              <span className={cotData.NASDAQ.confidence_adjustment > 0 ? 'text-green-400' : cotData.NASDAQ.confidence_adjustment < 0 ? 'text-red-400' : 'text-gray-400'}>
                Adj: {cotData.NASDAQ.confidence_adjustment > 0 ? '+' : ''}{(cotData.NASDAQ.confidence_adjustment * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="text-xs text-gray-500 text-center pt-2 border-t border-gray-700/30">
          <div className="flex items-center justify-center gap-4">
            <span>📊 COT: CFTC Weekly Data</span>
            <span>|</span>
            <span>⚡ Updates Friday</span>
          </div>
        </div>
      </div>
    </div>
  );
}
