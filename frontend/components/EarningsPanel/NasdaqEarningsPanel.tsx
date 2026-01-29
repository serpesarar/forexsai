"use client";

import { useState, useEffect } from "react";
import { 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  ChevronRight,
  RefreshCw,
  X,
  Clock,
  DollarSign,
  Target,
  Loader2
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Scenario {
  name: string;
  probability: number;
  scenario_type: string;
  confidence: number;
  nasdaq_direction: string;
  color: string;
  expected_move_pips: number;
  timeframe: string;
  risk_level: string;
  reasoning: string;
}

interface EarningsEvent {
  symbol: string;
  company_name: string;
  date: string;
  time: string;
  expected_eps: number | null;
  expected_revenue: number | null;
  importance: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  nasdaq_weight: string;
  scenarios: Scenario[];
  color: string;
}

const importanceColors = {
  CRITICAL: "bg-red-500/20 border-red-500/40 text-red-300",
  HIGH: "bg-orange-500/20 border-orange-500/40 text-orange-300",
  MEDIUM: "bg-yellow-500/20 border-yellow-500/40 text-yellow-300",
  LOW: "bg-green-500/20 border-green-500/40 text-green-300",
};

const importanceBadgeColors = {
  CRITICAL: "bg-red-500 text-white",
  HIGH: "bg-orange-500 text-white",
  MEDIUM: "bg-yellow-500 text-black",
  LOW: "bg-green-500 text-white",
};

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("tr-TR", { day: "numeric", month: "short" });
}

function formatWeekday(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("tr-TR", { weekday: "short" });
}

function getNext7Days(): string[] {
  const days: string[] = [];
  const today = new Date();
  for (let i = 0; i < 7; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    days.push(d.toISOString().split("T")[0]);
  }
  return days;
}

export default function NasdaqEarningsPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [events, setEvents] = useState<EarningsEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<EarningsEvent | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEarnings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/earnings/calendar?days_ahead=7`);
      if (!res.ok) throw new Error("Failed to fetch earnings");
      const data = await res.json();
      setEvents(data.events || []);
    } catch (err) {
      setError("Earnings verisi alınamadı");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && events.length === 0) {
      fetchEarnings();
    }
  }, [isOpen]);

  const eventsByDate = events.reduce((acc, event) => {
    if (!acc[event.date]) acc[event.date] = [];
    acc[event.date].push(event);
    return acc;
  }, {} as Record<string, EarningsEvent[]>);

  const criticalCount = events.filter(e => e.importance === "CRITICAL").length;

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed top-32 right-4 z-40 flex items-center gap-2 px-3 py-2 rounded-lg 
          ${isOpen ? "bg-purple-500 text-white" : "bg-white/10 hover:bg-white/20"} 
          transition-all duration-200 shadow-lg backdrop-blur-sm border border-white/10`}
      >
        <Calendar className="w-4 h-4" />
        <span className="text-sm font-medium">Earnings</span>
        {criticalCount > 0 && (
          <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full animate-pulse">
            {criticalCount}
          </span>
        )}
        <ChevronRight className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {/* Panel */}
      <div
        className={`fixed top-16 right-0 h-[calc(100vh-4rem)] w-[420px] bg-slate-900/95 backdrop-blur-xl 
          border-l border-purple-500/30 shadow-2xl z-30 transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-purple-500/20 bg-gradient-to-r from-purple-900/30 to-slate-900/30">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Calendar className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-bold text-white">NASDAQ Earnings</h3>
              <p className="text-xs text-gray-400">Haftalık Takvim & Senaryo</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchEarnings}
              disabled={isLoading}
              className="p-2 hover:bg-white/10 rounded-lg transition disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 text-purple-400" />
              )}
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 hover:bg-white/10 rounded-lg transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-500/10 border-b border-red-500/20 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Calendar Grid */}
        <div className="p-3 border-b border-white/10">
          <div className="grid grid-cols-7 gap-1">
            {getNext7Days().map((date) => {
              const dayEvents = eventsByDate[date] || [];
              const hasCritical = dayEvents.some(e => e.importance === "CRITICAL");
              
              return (
                <div
                  key={date}
                  className={`p-2 rounded-lg text-center transition-all ${
                    dayEvents.length > 0
                      ? hasCritical
                        ? "bg-red-500/10 border border-red-500/30"
                        : "bg-purple-500/10 border border-purple-500/20"
                      : "bg-white/5"
                  }`}
                >
                  <div className="text-[10px] text-gray-500">{formatWeekday(date)}</div>
                  <div className="text-xs font-bold text-white">{formatDate(date)}</div>
                  <div className="mt-1 space-y-0.5 max-h-16 overflow-y-auto">
                    {dayEvents.slice(0, 3).map((event) => (
                      <button
                        key={event.symbol}
                        className={`w-full text-[9px] px-1 py-0.5 rounded cursor-pointer font-medium hover:scale-105 transition-transform
                          ${importanceColors[event.importance]}`}
                        onClick={() => setSelectedEvent(event)}
                      >
                        {event.symbol}
                      </button>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-[9px] text-gray-500">+{dayEvents.length - 3}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Events List */}
        <div className="overflow-y-auto h-[calc(100%-280px)] p-3">
          <p className="text-xs text-gray-400 mb-2 font-medium">BU HAFTA</p>
          
          {events.length === 0 && !isLoading && (
            <div className="text-center text-gray-500 py-8">
              <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Earnings verisi yok</p>
            </div>
          )}

          {events.map((event) => (
            <div
              key={`${event.symbol}-${event.date}`}
              className={`p-3 rounded-xl mb-2 cursor-pointer border transition-all hover:scale-[1.01]
                ${selectedEvent?.symbol === event.symbol
                  ? "ring-2 ring-purple-500 " + importanceColors[event.importance]
                  : importanceColors[event.importance]
                }`}
              onClick={() => setSelectedEvent(selectedEvent?.symbol === event.symbol ? null : event)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${importanceBadgeColors[event.importance]}`}>
                    {event.symbol}
                  </span>
                  <span className="text-xs text-gray-400">{event.nasdaq_weight}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <Clock className="w-3 h-3" />
                  {formatDate(event.date)} {event.time}
                </div>
              </div>
              
              <p className="text-sm text-white mt-1 truncate">{event.company_name}</p>
              
              <div className="flex items-center gap-3 mt-2 text-xs">
                {event.expected_eps && (
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-3 h-3 text-green-400" />
                    <span>EPS: ${event.expected_eps.toFixed(2)}</span>
                  </div>
                )}
                {event.expected_revenue && (
                  <div className="flex items-center gap-1">
                    <Target className="w-3 h-3 text-blue-400" />
                    <span>Rev: ${event.expected_revenue.toFixed(1)}B</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Scenario Detail Panel */}
        {selectedEvent && selectedEvent.scenarios.length > 0 && (
          <div
            className="absolute bottom-0 left-0 right-0 bg-slate-800/95 border-t border-purple-500/30 p-4 max-h-[50%] overflow-y-auto animate-in slide-in-from-bottom duration-300"
          >
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-bold text-white">
                  {selectedEvent.symbol} Senaryolar
                </h4>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="p-1 hover:bg-white/10 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                {selectedEvent.scenarios.map((scenario, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg border"
                    style={{ 
                      borderColor: scenario.color + "40",
                      backgroundColor: scenario.color + "10"
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {scenario.scenario_type === "bullish" ? (
                          <TrendingUp className="w-4 h-4" style={{ color: scenario.color }} />
                        ) : scenario.scenario_type === "bearish" ? (
                          <TrendingDown className="w-4 h-4" style={{ color: scenario.color }} />
                        ) : (
                          <AlertTriangle className="w-4 h-4" style={{ color: scenario.color }} />
                        )}
                        <span className="font-medium text-sm text-white">{scenario.name}</span>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/10">
                        {scenario.probability}%
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs mb-2">
                      <div>
                        <span className="text-gray-500">NASDAQ</span>
                        <p className="font-bold" style={{ color: scenario.color }}>
                          {scenario.nasdaq_direction.toUpperCase()}
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Move</span>
                        <p className="font-mono font-bold text-white">
                          {scenario.expected_move_pips > 0 ? "+" : ""}{scenario.expected_move_pips} pips
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-500">Risk</span>
                        <p className={`font-bold ${
                          scenario.risk_level === "HIGH" ? "text-red-400" :
                          scenario.risk_level === "MEDIUM" ? "text-yellow-400" : "text-green-400"
                        }`}>
                          {scenario.risk_level}
                        </p>
                      </div>
                    </div>

                    <p className="text-xs text-gray-400">{scenario.reasoning}</p>
                    <p className="text-[10px] text-gray-500 mt-1">⏱️ {scenario.timeframe}</p>
                  </div>
                ))}
              </div>
          </div>
        )}
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
