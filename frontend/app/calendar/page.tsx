"use client";

import { Calendar, Clock, Filter, AlertTriangle, TrendingUp, TrendingDown, Minus, Globe } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { format, addDays, startOfWeek } from "date-fns";

interface EconomicEvent {
  id: string;
  time: string;
  currency: string;
  event: string;
  impact: "high" | "medium" | "low";
  forecast: string;
  previous: string;
  actual?: string;
}

const mockEvents: EconomicEvent[] = [
  { id: "1", time: "08:30", currency: "USD", event: "Non-Farm Payrolls", impact: "high", forecast: "185K", previous: "175K" },
  { id: "2", time: "10:00", currency: "USD", event: "ISM Manufacturing PMI", impact: "high", forecast: "49.5", previous: "49.1" },
  { id: "3", time: "14:00", currency: "USD", event: "Fed Chair Powell Speech", impact: "high", forecast: "-", previous: "-" },
  { id: "4", time: "09:00", currency: "EUR", event: "ECB Interest Rate Decision", impact: "high", forecast: "4.50%", previous: "4.50%" },
  { id: "5", time: "11:30", currency: "GBP", event: "BOE Governor Speech", impact: "medium", forecast: "-", previous: "-" },
  { id: "6", time: "22:30", currency: "AUD", event: "Retail Sales m/m", impact: "medium", forecast: "0.3%", previous: "0.1%" },
];

const weekDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export default function CalendarPage() {
  const [selectedDay, setSelectedDay] = useState(0);
  const [filter, setFilter] = useState<"all" | "high" | "medium" | "low">("all");

  const filteredEvents = mockEvents.filter(e => filter === "all" || e.impact === filter);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <Calendar className="w-6 h-6 text-blue-400" />
              Economic Calendar
            </h1>
            <p className="text-gray-500 mt-1">Track high-impact economic events</p>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
              <Globe className="w-4 h-4" />
              All Currencies
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">
              <Filter className="w-4 h-4" />
              Filter
            </button>
          </div>
        </div>

        {/* Week Navigation */}
        <div className="flex items-center gap-2 mb-6">
          {weekDays.map((day, idx) => (
            <button
              key={day}
              onClick={() => setSelectedDay(idx)}
              className={cn(
                "flex-1 py-3 rounded-lg text-sm font-medium transition-all",
                selectedDay === idx
                  ? "bg-blue-500 text-white"
                  : "bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-white"
              )}
            >
              {day}
            </button>
          ))}
        </div>

        {/* Impact Filter */}
        <div className="flex items-center gap-2 mb-6">
          {["all", "high", "medium", "low"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f as any)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                filter === f
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              )}
            >
              {f !== "all" && (
                <span className={cn(
                  "w-2 h-2 rounded-full",
                  f === "high" && "bg-red-500",
                  f === "medium" && "bg-yellow-500",
                  f === "low" && "bg-gray-500"
                )} />
              )}
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Events List */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-800">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Time</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Currency</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Event</th>
                <th className="text-center text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Impact</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Forecast</th>
                <th className="text-right text-xs font-medium text-gray-500 uppercase tracking-wider p-4">Previous</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filteredEvents.map((event) => (
                <tr key={event.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="p-4 text-gray-400 font-mono">{event.time}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-gray-800 rounded text-xs font-semibold">{event.currency}</span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{event.event}</span>
                      {event.impact === "high" && <AlertTriangle className="w-4 h-4 text-red-500" />}
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <span className={cn(
                      "px-2 py-1 rounded text-xs font-medium uppercase",
                      event.impact === "high" && "bg-red-500/10 text-red-400 border border-red-500/20",
                      event.impact === "medium" && "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
                      event.impact === "low" && "bg-gray-700 text-gray-400"
                    )}>
                      {event.impact}
                    </span>
                  </td>
                  <td className="p-4 text-right font-mono text-gray-400">{event.forecast}</td>
                  <td className="p-4 text-right font-mono text-gray-500">{event.previous}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
