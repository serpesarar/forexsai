"use client";

import { useState, useEffect } from "react";
import { Calendar, Clock, TrendingUp, TrendingDown, Minus, AlertCircle, Filter, Info } from "lucide-react";
import { useI18nStore } from "../lib/i18n/store";

interface EconomicEvent {
  id: string;
  timestamp: string;
  title: string;
  title_tr: string;
  currency: string;
  impact: "High" | "Medium" | "Low";
  actual: string | null;
  forecast: string | null;
  previous: string | null;
  predicted_direction: "bullish" | "bearish" | "neutral" | "volatile";
  affected_symbols: string[];
  impact_analysis: string;
  impact_analysis_tr: string;
  description: string;
  description_tr: string;
  why_it_matters: string;
  why_it_matters_tr: string;
  typical_market_reaction: string;
  typical_market_reaction_tr: string;
  is_upcoming: boolean;
  minutes_until: number | null;
}

interface EconomicCalendarProps {
  onEventClick?: (event: EconomicEvent) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://upbeat-flow-production.up.railway.app";

const impactStyles = {
  High: "bg-red-500/20 text-red-200 border-red-500/40",
  Medium: "bg-yellow-500/20 text-yellow-200 border-yellow-500/40",
  Low: "bg-green-500/20 text-green-200 border-green-500/40",
};

const directionIcons = {
  bullish: <TrendingUp className="w-4 h-4 text-emerald-400" />,
  bearish: <TrendingDown className="w-4 h-4 text-red-400" />,
  neutral: <Minus className="w-4 h-4 text-gray-400" />,
  volatile: <AlertCircle className="w-4 h-4 text-yellow-400" />,
};

const directionLabels = {
  bullish: { en: "Bullish", tr: "Yükseliş" },
  bearish: { en: "Bearish", tr: "Düşüş" },
  neutral: { en: "Neutral", tr: "Nötr" },
  volatile: { en: "Volatile", tr: "Volatil" },
};

function formatTimeUntil(minutes: number | null, locale: string): string {
  if (!minutes) return locale === "en" ? "Soon" : "Yakında";
  
  if (minutes < 60) {
    return `${minutes} ${locale === "en" ? "min" : "dk"}`;
  }
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} ${locale === "en" ? "hours" : "saat"}`;
  }
  
  const days = Math.floor(hours / 24);
  return `${days} ${locale === "en" ? "days" : "gün"}`;
}

function formatDate(dateStr: string, locale: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(locale === "en" ? "en-US" : "tr-TR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function EconomicCalendar({ onEventClick }: EconomicCalendarProps) {
  const { locale } = useI18nStore();
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "High" | "Medium" | "Low">("all");

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/calendar/economic?days=30`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch");
      }
      
      const data = await response.json();
      if (data.success) {
        setEvents(data.events);
      }
    } catch (err) {
      setError(locale === "en" ? "Failed to load calendar" : "Takvim yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = filter === "all" 
    ? events 
    : events.filter(e => e.impact === filter);

  if (loading) {
    return (
      <div className="glass-premium p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Calendar className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold">
            {locale === "en" ? "Economic Calendar" : "Ekonomik Takvim"}
          </h2>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-20 w-full rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-premium p-6">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-semibold">
            {locale === "en" ? "Economic Calendar" : "Ekonomik Takvim"}
          </h2>
        </div>
        <div className="flex flex-col items-center py-8 text-center">
          <AlertCircle className="w-10 h-10 text-danger/50 mb-3" />
          <p className="text-sm text-danger">{error}</p>
          <button
            onClick={fetchEvents}
            className="mt-4 text-xs text-emerald-400 hover:underline"
          >
            {locale === "en" ? "Try again" : "Tekrar dene"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-premium p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/30 to-green-500/30">
            <Calendar className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs text-textSecondary uppercase tracking-wider">
              {locale === "en" ? "High Impact Events" : "Yüksek Etkili Olaylar"}
            </p>
            <h2 className="text-base font-semibold">
              {locale === "en" ? "Economic Calendar" : "Ekonomik Takvim"}
            </h2>
          </div>
        </div>
        
        {/* Filter */}
        <div className="flex items-center gap-1">
          <Filter className="w-3 h-3 text-textSecondary mr-1" />
          {(["all", "High", "Medium", "Low"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-1 text-[10px] rounded-md transition ${
                filter === f 
                  ? "bg-emerald-500/30 text-emerald-300" 
                  : "bg-white/5 text-textSecondary hover:bg-white/10"
              }`}
            >
              {f === "all" 
                ? (locale === "en" ? "All" : "Tümü")
                : f
              }
            </button>
          ))}
        </div>
      </div>

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Calendar className="w-12 h-12 text-textSecondary/30 mb-4" />
          <p className="text-sm text-textSecondary">
            {locale === "en" ? "No upcoming events" : "Yaklaşan olay yok"}
          </p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
          {filteredEvents.map((event, index) => (
            <div
              key={event.id}
              className="border border-white/10 rounded-xl p-4 bg-white/5 hover:bg-white/10 transition cursor-pointer group animate-fadeIn"
              style={{ animationDelay: `${index * 0.05}s` }}
              onClick={() => onEventClick?.(event)}
            >
              {/* Top Row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase ${impactStyles[event.impact]}`}>
                    {event.impact}
                  </span>
                  <span className="text-[10px] text-textSecondary bg-white/5 px-2 py-0.5 rounded">
                    {event.currency}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[10px] text-textSecondary">
                  <Clock className="w-3 h-3" />
                  {event.is_upcoming && event.minutes_until !== null && event.minutes_until < 1440 ? (
                    <span className="text-emerald-400 font-medium">
                      {formatTimeUntil(event.minutes_until, locale)}
                    </span>
                  ) : (
                    <span>{formatDate(event.timestamp, locale)}</span>
                  )}
                </div>
              </div>

              {/* Title */}
              <h3 className="text-sm font-semibold text-white mb-2 group-hover:text-emerald-400 transition">
                {locale === "en" ? event.title : event.title_tr}
              </h3>

              {/* Predicted Direction */}
              <div className="flex items-center gap-2 mb-2">
                {directionIcons[event.predicted_direction]}
                <span className="text-xs text-textSecondary">
                  {locale === "en" ? "Expected: " : "Beklenen: "}
                  <span className={
                    event.predicted_direction === "bullish" ? "text-emerald-400" :
                    event.predicted_direction === "bearish" ? "text-red-400" :
                    event.predicted_direction === "volatile" ? "text-yellow-400" :
                    "text-gray-400"
                  }>
                    {directionLabels[event.predicted_direction][locale]}
                  </span>
                </span>
              </div>

              {/* Affected Symbols */}
              <div className="flex flex-wrap gap-1 mt-2">
                {event.affected_symbols.map((symbol) => (
                  <span
                    key={symbol}
                    className="text-[10px] bg-white/10 text-textSecondary px-2 py-0.5 rounded"
                  >
                    {symbol}
                  </span>
                ))}
              </div>

              {/* View Details Hint */}
              <div className="flex items-center justify-end mt-2 pt-2 border-t border-white/5">
                <span className="text-[10px] text-emerald-400/70 flex items-center gap-1 group-hover:text-emerald-400 transition">
                  <Info className="w-3 h-3" />
                  {locale === "en" ? "Click for analysis" : "Analiz için tıkla"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-textSecondary pt-2 border-t border-white/10">
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          {locale === "en" ? "Auto-updates daily" : "Günlük otomatik güncellenir"}
        </span>
        <span>{filteredEvents.length} {locale === "en" ? "events" : "olay"}</span>
      </div>
    </div>
  );
}
