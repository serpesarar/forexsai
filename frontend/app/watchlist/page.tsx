"use client";

import { Star, Plus, Search, ArrowUpDown, TrendingUp, TrendingDown, MoreHorizontal, Bell } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  high: number;
  low: number;
}

const watchlistData: WatchlistItem[] = [
  { symbol: "XAUUSD", name: "Gold", price: 4988.57, change: 42.30, changePercent: 0.85, volume: "125K", high: 5010.20, low: 4945.30 },
  { symbol: "NDX", name: "NASDAQ", price: 22500.00, change: 125.50, changePercent: 0.56, volume: "2.1M", high: 22650.00, low: 22320.00 },
  { symbol: "DAX", name: "DAX 40", price: 22500.00, change: -180.20, changePercent: -0.79, volume: "850K", high: 22700.00, low: 22350.00 },
  { symbol: "USOIL", name: "WTI Crude", price: 75.80, change: 1.20, changePercent: 1.61, volume: "3.2M", high: 76.50, low: 74.20 },
  { symbol: "VIX", name: "VIX", price: 18.50, change: -0.85, changePercent: -4.40, volume: "450K", high: 20.20, low: 17.80 },
  { symbol: "DXY", name: "Dollar Index", price: 104.25, change: 0.12, changePercent: 0.12, volume: "1.8M", high: 104.80, low: 103.90 },
];

export default function WatchlistPage() {
  const [items] = useState<WatchlistItem[]>(watchlistData);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <Star className="w-6 h-6 text-yellow-400" />
              Watchlist
            </h1>
            <p className="text-gray-500 mt-1">Track your favorite markets</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search symbols..."
                className="pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 w-64"
              />
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors">
              <Plus className="w-4 h-4" />
              Add Symbol
            </button>
          </div>
        </div>

        {/* Watchlist Table */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-800">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Symbol</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Price</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Change</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Change %</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Volume</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">High</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Low</th>
                <th className="text-center text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {items.map((item) => (
                <tr key={item.symbol} className="hover:bg-gray-800/50 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <button className="text-yellow-400 hover:text-yellow-300">
                        <Star className="w-4 h-4 fill-current" />
                      </button>
                      <div>
                        <p className="font-semibold">{item.symbol}</p>
                        <p className="text-xs text-gray-500">{item.name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="text-right p-4 font-mono">${item.price.toLocaleString()}</td>
                  <td className={cn("text-right p-4 font-mono", item.change > 0 ? "text-green-400" : "text-red-400")}>
                    <div className="flex items-center justify-end gap-1">
                      {item.change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {item.change > 0 ? "+" : ""}{item.change.toFixed(2)}
                    </div>
                  </td>
                  <td className={cn("text-right p-4 font-mono", item.changePercent > 0 ? "text-green-400" : "text-red-400")}>
                    {item.changePercent > 0 ? "+" : ""}{item.changePercent.toFixed(2)}%
                  </td>
                  <td className="text-right p-4 text-gray-400">{item.volume}</td>
                  <td className="text-right p-4 font-mono text-gray-400">${item.high.toLocaleString()}</td>
                  <td className="text-right p-4 font-mono text-gray-400">${item.low.toLocaleString()}</td>
                  <td className="text-center p-4">
                    <div className="flex items-center justify-center gap-2">
                      <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                        <Bell className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
