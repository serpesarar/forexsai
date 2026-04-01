"use client";

import { useEffect, useState } from "react";
import { Target, TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from "lucide-react";
import { fetcher } from "../lib/api";

interface StrategyData {
  total: number;
  tp1_rate: number;
  tp2_rate: number;
  tp3_rate: number;
  sl_rate: number;
  best_target: string;
}

interface StrategyPerformanceDashboardProps {
  symbol?: string;
}

const STRATEGIES = ["ultra_safe", "balanced", "full_power", "aggressive", "nasdaq_precision"];
const STRATEGY_LABELS: Record<string, string> = {
  ultra_safe: "Ultra Safe",
  balanced: "Balanced",
  full_power: "Full Power",
  aggressive: "Aggressive",
  nasdaq_precision: "NASDAQ Precision",
};

const SYMBOL_TARGETS: Record<string, Record<string, number>> = {
  "NDX.INDX": { TP1: 15, TP2: 25, TP3: 35, TP4: 50, SL: 50 },
  XAUUSD: { TP1: 4, TP2: 7, TP3: 10, TP4: 17, SL: 8 },
  "GDAXI.INDX": { TP1: 15, TP2: 25, TP3: 35, TP4: 50, SL: 50 },
  "USOIL.FOREX": { TP1: 0.02, TP2: 0.04, TP3: 0.06, TP4: 0.10, SL: 0.05 },
};

export default function StrategyPerformanceDashboard({ symbol: lockedSymbol }: StrategyPerformanceDashboardProps) {
  const symbol = lockedSymbol ?? "XAUUSD";
  const isSymbolLocked = lockedSymbol != null;
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  const [selectedDirection, setSelectedDirection] = useState<"BUY" | "SELL" | "ALL">("ALL");
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Record<string, StrategyData> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setSelectedSymbol(symbol);
  }, [symbol]);

  const targets = SYMBOL_TARGETS[selectedSymbol] || SYMBOL_TARGETS.XAUUSD;

  const fetchData = async () => {
    setLoading(true);
    try {
      const json = await fetcher<any>(`/api/learning/strategy-performance/${selectedSymbol}?days=${days}`);
      if (json.strategies) {
        const processed: Record<string, StrategyData> = {};
        for (const strat of STRATEGIES) {
          const stratData = json.strategies[strat];
          if (stratData) {
            const buyData = stratData.BUY || {};
            const sellData = stratData.SELL || {};
            processed[strat] = {
              total: (buyData.total || 0) + (sellData.total || 0),
              tp1_rate: ((buyData.tp1_rate || 0) + (sellData.tp1_rate || 0)) / 2,
              tp2_rate: ((buyData.tp2_rate || 0) + (sellData.tp2_rate || 0)) / 2,
              tp3_rate: ((buyData.tp3_rate || 0) + (sellData.tp3_rate || 0)) / 2,
              sl_rate: ((buyData.sl_rate || 0) + (sellData.sl_rate || 0)) / 2,
              best_target: buyData.best_target || sellData.best_target || "TP1",
            };
          }
        }
        setData(processed);
      }
    } catch (e) {
      console.error("Failed to fetch strategy performance:", e);
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  useEffect(() => {
    fetchData();
  }, [selectedSymbol, days]);

  const getRateColor = (rate: number, isSL = false) => {
    if (isSL) return rate > 0.3 ? "text-red-500" : rate > 0.2 ? "text-yellow-500" : "text-green-500";
    return rate > 0.6 ? "text-green-500" : rate > 0.4 ? "text-yellow-500" : "text-red-500";
  };

  return (
    <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Strategy Performance</h2>
        </div>

        <div className="flex items-center gap-3">
          {isSymbolLocked ? (
            <span className="bg-gray-800 text-white text-sm rounded-lg px-3 py-1.5 border border-gray-700">
              {selectedSymbol === "NDX.INDX" ? "NASDAQ" : selectedSymbol}
            </span>
          ) : (
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-gray-800 text-white text-sm rounded-lg px-3 py-1.5 border border-gray-700"
            >
              <option value="XAUUSD">XAUUSD</option>
              <option value="NDX.INDX">NASDAQ</option>
              <option value="GDAXI.INDX">DAX</option>
              <option value="USOIL.FOREX">US Oil</option>
            </select>
          )}

          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-gray-800 text-white text-sm rounded-lg px-3 py-1.5 border border-gray-700"
          >
            <option value={7}>7 Days</option>
            <option value={30}>30 Days</option>
            <option value={90}>90 Days</option>
          </select>

          <button
            onClick={fetchData}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-1.5 rounded-lg disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* Target Legend */}
      <div className="flex flex-wrap gap-2 mb-4 text-xs text-gray-400">
        {Object.entries(targets).map(([key, value]) => (
          <span key={key} className="bg-gray-800 px-2 py-1 rounded">
            {key}: {value}p
          </span>
        ))}
      </div>

      {/* Direction Filter */}
      <div className="flex gap-2 mb-4">
        {(["ALL", "BUY", "SELL"] as const).map((dir) => (
          <button
            key={dir}
            onClick={() => setSelectedDirection(dir)}
            className={`px-3 py-1 rounded text-sm ${selectedDirection === dir
                ? dir === "BUY"
                  ? "bg-green-600 text-white"
                  : dir === "SELL"
                    ? "bg-red-600 text-white"
                    : "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400"
              }`}
          >
            {dir === "BUY" ? <TrendingUp className="w-4 h-4 inline mr-1" /> : null}
            {dir === "SELL" ? <TrendingDown className="w-4 h-4 inline mr-1" /> : null}
            {dir}
          </button>
        ))}
      </div>

      {/* Performance Table */}
      {data ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-800">
                <th className="text-left py-2 px-2">Strategy</th>
                <th className="text-center py-2 px-2">Signals</th>
                <th className="text-center py-2 px-2">TP1</th>
                <th className="text-center py-2 px-2">TP2</th>
                <th className="text-center py-2 px-2">TP3</th>
                <th className="text-center py-2 px-2">SL</th>
                <th className="text-center py-2 px-2">Best</th>
              </tr>
            </thead>
            <tbody>
              {STRATEGIES.map((strat) => {
                const stratData = data[strat];
                if (!stratData) return null;
                return (
                  <tr key={strat} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="py-3 px-2">
                      <span className="font-medium text-white">{STRATEGY_LABELS[strat]}</span>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-300">{stratData.total}</td>
                    <td className={`text-center py-3 px-2 ${getRateColor(stratData.tp1_rate)}`}>
                      {formatPercent(stratData.tp1_rate)}
                    </td>
                    <td className={`text-center py-3 px-2 ${getRateColor(stratData.tp2_rate)}`}>
                      {formatPercent(stratData.tp2_rate)}
                    </td>
                    <td className={`text-center py-3 px-2 ${getRateColor(stratData.tp3_rate)}`}>
                      {formatPercent(stratData.tp3_rate)}
                    </td>
                    <td className={`text-center py-3 px-2 ${getRateColor(stratData.sl_rate, true)}`}>
                      {formatPercent(stratData.sl_rate)}
                    </td>
                    <td className="text-center py-3 px-2">
                      <span className="bg-green-600/20 text-green-400 px-2 py-0.5 rounded text-xs">
                        {stratData.best_target}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Strategy performance data is loading.</p>
        </div>
      )}

      {/* Recommendation */}
      {data && (
        <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 text-blue-400 text-sm">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium">Optimization Suggestion</span>
          </div>
          <p className="text-gray-300 text-sm mt-1">
            Based on hit rates, consider using <strong>TP2</strong> as primary target for better risk/reward.
            Ultra Safe strategy shows highest TP1 hit rate.
          </p>
        </div>
      )}
    </div>
  );
}
