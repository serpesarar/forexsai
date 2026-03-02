"use client";

import { LineChart, TrendingUp, TrendingDown, DollarSign, Calendar, Target, Percent, MoreHorizontal, Plus, Filter, Download } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Trade {
  id: string;
  symbol: string;
  type: "long" | "short";
  entry: number;
  exit?: number;
  size: string;
  pnl?: number;
  pnlPercent?: number;
  status: "open" | "closed";
  date: string;
  strategy: string;
}

const trades: Trade[] = [
  { id: "1", symbol: "XAUUSD", type: "long", entry: 4950, exit: 4988, size: "1.5 lots", pnl: 570, pnlPercent: 0.77, status: "closed", date: "2024-03-01", strategy: "Breakout" },
  { id: "2", symbol: "NDX", type: "long", entry: 22200, size: "2.0 lots", status: "open", date: "2024-03-01", strategy: "Trend Following" },
  { id: "3", symbol: "USOIL", type: "short", entry: 76.50, exit: 75.20, size: "1.0 lots", pnl: 130, pnlPercent: 1.70, status: "closed", date: "2024-02-28", strategy: "Mean Reversion" },
  { id: "4", symbol: "DAX", type: "short", entry: 22700, exit: 22500, size: "1.5 lots", pnl: -300, pnlPercent: -0.88, status: "closed", date: "2024-02-27", strategy: "News Based" },
];

export default function TradesPage() {
  const [filter, setFilter] = useState<"all" | "open" | "closed">("all");

  const filteredTrades = trades.filter(t => filter === "all" || t.status === filter);
  
  const totalPnL = trades.reduce((acc, t) => acc + (t.pnl || 0), 0);
  const winRate = (trades.filter(t => (t.pnl || 0) > 0).length / trades.filter(t => t.status === "closed").length * 100).toFixed(0);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <LineChart className="w-6 h-6 text-blue-400" />
              My Trades
            </h1>
            <p className="text-gray-500 mt-1">Track your trading performance</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors">
            <Plus className="w-4 h-4" />
            New Trade
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Total P&L</p>
            <p className={cn("text-2xl font-bold mt-1", totalPnL >= 0 ? "text-green-400" : "text-red-400")}>
              {totalPnL >= 0 ? "+" : ""}${totalPnL}
            </p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Win Rate</p>
            <p className="text-2xl font-bold mt-1 text-blue-400">{winRate}%</p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Open Trades</p>
            <p className="text-2xl font-bold mt-1">{trades.filter(t => t.status === "open").length}</p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Total Trades</p>
            <p className="text-2xl font-bold mt-1">{trades.length}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-1 bg-gray-900 rounded-lg p-1">
            {["all", "open", "closed"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f as any)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  filter === f ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"
                )}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
              <Filter className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
              <Download className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Trades Table */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-800">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Symbol</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Type</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Entry</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Exit</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Size</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">P&L</th>
                <th className="text-center text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Strategy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filteredTrades.map((trade) => (
                <tr key={trade.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="p-4 font-semibold">{trade.symbol}</td>
                  <td className="p-4">
                    <span className={cn(
                      "flex items-center gap-1 text-sm",
                      trade.type === "long" ? "text-green-400" : "text-red-400"
                    )}>
                      {trade.type === "long" ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {trade.type.toUpperCase()}
                    </span>
                  </td>
                  <td className="text-right p-4 font-mono">${trade.entry.toLocaleString()}</td>
                  <td className="text-right p-4 font-mono">{trade.exit ? `$${trade.exit.toLocaleString()}` : "-"}</td>
                  <td className="text-right p-4">{trade.size}</td>
                  <td className="text-right p-4">
                    {trade.pnl !== undefined ? (
                      <span className={cn(
                        "font-mono",
                        trade.pnl >= 0 ? "text-green-400" : "text-red-400"
                      )}>
                        {trade.pnl >= 0 ? "+" : ""}${trade.pnl}
                        <span className="text-xs text-gray-500 ml-1">({trade.pnlPercent}%)</span>
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="p-4 text-center">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-medium",
                      trade.status === "open" ? "bg-green-500/10 text-green-400" : "bg-gray-700 text-gray-400"
                    )}>
                      {trade.status}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-400">{trade.strategy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
