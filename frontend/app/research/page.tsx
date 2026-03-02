"use client";

import { FileText, Download, Clock, Eye, Star, Filter, Search, TrendingUp, TrendingDown, BarChart3, Globe, Zap } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Report {
  id: string;
  title: string;
  type: "technical" | "fundamental" | "sentiment";
  symbol: string;
  author: string;
  date: string;
  views: number;
  rating: number;
  summary: string;
}

const reports: Report[] = [
  {
    id: "1",
    title: "Gold Technical Analysis: Breakout Above $5,000",
    type: "technical",
    symbol: "XAUUSD",
    author: "AI Research Team",
    date: "2024-03-01",
    views: 1250,
    rating: 4.8,
    summary: "Comprehensive analysis of Gold's breakout with key support/resistance levels and price targets.",
  },
  {
    id: "2",
    title: "NASDAQ Q1 2024 Outlook: AI Boom Continues",
    type: "fundamental",
    symbol: "NDX",
    author: "Market Analysis Dept",
    date: "2024-02-28",
    views: 890,
    rating: 4.6,
    summary: "Deep dive into technology sector performance and AI-related stock momentum.",
  },
  {
    id: "3",
    title: "Oil Market Sentiment: Supply vs Demand",
    type: "sentiment",
    symbol: "USOIL",
    author: "Commodities Team",
    date: "2024-02-27",
    views: 650,
    rating: 4.5,
    summary: "Analysis of current oil market dynamics and geopolitical factors affecting prices.",
  },
];

export default function ResearchPage() {
  const [filter, setFilter] = useState<"all" | "technical" | "fundamental" | "sentiment">("all");

  const filteredReports = reports.filter(r => filter === "all" || r.type === filter);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <FileText className="w-6 h-6 text-purple-400" />
              Research Reports
            </h1>
            <p className="text-gray-500 mt-1">In-depth market analysis and insights</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search reports..."
                className="pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500 w-64"
              />
            </div>
            <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
              <Filter className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 mb-6">
          {["all", "technical", "fundamental", "sentiment"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f as any)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                filter === f ? "bg-purple-500 text-white" : "text-gray-400 hover:text-white hover:bg-gray-800"
              )}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Reports Grid */}
        <div className="grid grid-cols-2 gap-4">
          {filteredReports.map((report) => (
            <div
              key={report.id}
              className="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-purple-500/30 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className={cn(
                    "px-2 py-1 rounded text-xs font-medium",
                    report.type === "technical" && "bg-blue-500/10 text-blue-400 border border-blue-500/20",
                    report.type === "fundamental" && "bg-green-500/10 text-green-400 border border-green-500/20",
                    report.type === "sentiment" && "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                  )}>
                    {report.type}
                  </span>
                  <span className="text-xs text-gray-500">{report.symbol}</span>
                </div>
                <button className="p-2 text-gray-500 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100">
                  <Download className="w-4 h-4" />
                </button>
              </div>

              <h3 className="text-lg font-semibold mb-2 group-hover:text-purple-400 transition-colors">
                {report.title}
              </h3>
              <p className="text-sm text-gray-400 mb-4">{report.summary}</p>

              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    {report.author}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {report.date}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {report.views}
                  </span>
                  <span className="flex items-center gap-1 text-yellow-400">
                    <Star className="w-3 h-3 fill-current" />
                    {report.rating}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
