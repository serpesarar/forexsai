"use client";

import { BarChart3, TrendingUp, TrendingDown, Newspaper, Clock, Sparkles, AlertTriangle, Filter, Download, Calendar } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface NewsAnalysis {
  id: string;
  date: string;
  symbol: string;
  headline: string;
  sentiment: "positive" | "negative" | "neutral";
  impact: "high" | "medium" | "low";
  aiScore: number;
  priceChange: number;
  accuracy: number;
}

const analyses: NewsAnalysis[] = [
  { id: "1", date: "2024-03-01", symbol: "XAUUSD", headline: "Gold surges on safe haven demand", sentiment: "positive", impact: "high", aiScore: 85, priceChange: 1.2, accuracy: 92 },
  { id: "2", date: "2024-03-01", symbol: "NDX", headline: "Tech stocks rally on AI optimism", sentiment: "positive", impact: "high", aiScore: 78, priceChange: 0.8, accuracy: 88 },
  { id: "3", date: "2024-02-29", symbol: "USOIL", headline: "Oil drops on inventory build", sentiment: "negative", impact: "medium", aiScore: 72, priceChange: -1.5, accuracy: 85 },
  { id: "4", date: "2024-02-28", symbol: "DAX", headline: "German manufacturing PMI misses", sentiment: "negative", impact: "medium", aiScore: 68, priceChange: -0.9, accuracy: 79 },
];

export default function NewsAnalysisPage() {
  const [filter, setFilter] = useState<"all" | "high" | "medium">("all");

  const filteredAnalyses = analyses.filter(a => filter === "all" || a.impact === filter);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <BarChart3 className="w-6 h-6 text-orange-400" />
              News Analysis
            </h1>
            <p className="text-gray-500 mt-1">AI-powered news impact analysis</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
              <Calendar className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
              <Download className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Avg AI Accuracy</p>
            <p className="text-2xl font-bold mt-1 text-purple-400">86%</p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">High Impact News</p>
            <p className="text-2xl font-bold mt-1 text-red-400">24</p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Positive Sentiment</p>
            <p className="text-2xl font-bold mt-1 text-green-400">58%</p>
          </div>
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-500 text-sm">Avg Price Impact</p>
            <p className="text-2xl font-bold mt-1 text-blue-400">0.82%</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-1 bg-gray-900 rounded-lg p-1">
            {["all", "high", "medium"].map((f) => (
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
          <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
            <Filter className="w-5 h-5" />
          </button>
        </div>

        {/* Analysis List */}
        <div className="space-y-3">
          {filteredAnalyses.map((item) => (
            <div
              key={item.id}
              className="bg-gray-900/50 border border-gray-800 rounded-xl p-5 hover:border-orange-500/30 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-semibold text-gray-400">{item.symbol}</span>
                    <span className="text-xs text-gray-600">{item.date}</span>
                    <span className={cn(
                      "px-2 py-0.5 rounded text-xs font-medium",
                      item.impact === "high" && "bg-red-500/10 text-red-400 border border-red-500/20",
                      item.impact === "medium" && "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                    )}>
                      {item.impact.toUpperCase()}
                    </span>
                  </div>
                  <h3 className="font-semibold mb-3">{item.headline}</h3>
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-purple-400" />
                      <span className="text-sm text-gray-400">AI Score:</span>
                      <span className="font-semibold">{item.aiScore}/100</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Sentiment:</span>
                      <span className={cn(
                        "flex items-center gap-1 text-sm",
                        item.sentiment === "positive" && "text-green-400",
                        item.sentiment === "negative" && "text-red-400",
                        item.sentiment === "neutral" && "text-gray-400"
                      )}>
                        {item.sentiment === "positive" && <TrendingUp className="w-3 h-3" />}
                        {item.sentiment === "negative" && <TrendingDown className="w-3 h-3" />}
                        {item.sentiment.charAt(0).toUpperCase() + item.sentiment.slice(1)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Price Impact:</span>
                      <span className={cn(
                        "font-semibold",
                        item.priceChange >= 0 ? "text-green-400" : "text-red-400"
                      )}>
                        {item.priceChange >= 0 ? "+" : ""}{item.priceChange}%
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-400">{item.accuracy}%</div>
                  <div className="text-xs text-gray-500">AI Accuracy</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
