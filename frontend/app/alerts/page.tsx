"use client";

import { Bell, Plus, Filter, Search, Trash2, Edit3, AlertTriangle, CheckCircle2, Clock } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Alert {
  id: string;
  symbol: string;
  condition: string;
  target: number;
  type: "price" | "indicator" | "news";
  status: "active" | "triggered" | "paused";
  createdAt: string;
}

const mockAlerts: Alert[] = [
  { id: "1", symbol: "XAUUSD", condition: "Above", target: 5000, type: "price", status: "active", createdAt: "2024-03-01" },
  { id: "2", symbol: "NDX", condition: "Below", target: 22000, type: "price", status: "active", createdAt: "2024-03-01" },
  { id: "3", symbol: "USOIL", condition: "RSI Above", target: 70, type: "indicator", status: "triggered", createdAt: "2024-02-28" },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [filter, setFilter] = useState<"all" | "active" | "triggered">("all");

  const filteredAlerts = alerts.filter(a => filter === "all" || a.status === filter);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <Bell className="w-6 h-6 text-purple-400" />
              Price Alerts
            </h1>
            <p className="text-gray-500 mt-1">Get notified when your conditions are met</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg transition-colors">
            <Plus className="w-4 h-4" />
            Create Alert
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: "Active Alerts", value: alerts.filter(a => a.status === "active").length, color: "text-green-400" },
            { label: "Triggered Today", value: alerts.filter(a => a.status === "triggered").length, color: "text-yellow-400" },
            { label: "Total Alerts", value: alerts.length, color: "text-white" },
            { label: "Success Rate", value: "87%", color: "text-purple-400" },
          ].map((stat) => (
            <div key={stat.label} className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-500 text-sm">{stat.label}</p>
              <p className={cn("text-2xl font-bold mt-1", stat.color)}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-1 bg-gray-900 rounded-lg p-1">
            {["all", "active", "triggered"].map((f) => (
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
          <div className="flex-1" />
          <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
            <Search className="w-5 h-5" />
          </button>
          <button className="p-2 text-gray-400 hover:text-white bg-gray-900 rounded-lg">
            <Filter className="w-5 h-5" />
          </button>
        </div>

        {/* Alerts List */}
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={cn(
                "flex items-center justify-between p-4 rounded-xl border transition-all",
                alert.status === "active" && "bg-gray-900/50 border-gray-800",
                alert.status === "triggered" && "bg-yellow-500/5 border-yellow-500/30",
                alert.status === "paused" && "bg-gray-900/30 border-gray-800 opacity-60"
              )}
            >
              <div className="flex items-center gap-4">
                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center",
                  alert.status === "active" && "bg-green-500/10 text-green-400",
                  alert.status === "triggered" && "bg-yellow-500/10 text-yellow-400",
                )}>
                  {alert.status === "active" && <Bell className="w-5 h-5" />}
                  {alert.status === "triggered" && <CheckCircle2 className="w-5 h-5" />}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{alert.symbol}</span>
                    <span className="text-gray-500">•</span>
                    <span className="text-sm text-gray-400">{alert.condition}</span>
                    <span className="text-sm font-mono text-purple-400">${alert.target}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Created {alert.createdAt}
                    </span>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full",
                      alert.type === "price" && "bg-blue-500/10 text-blue-400",
                      alert.type === "indicator" && "bg-purple-500/10 text-purple-400",
                      alert.type === "news" && "bg-red-500/10 text-red-400",
                    )}>
                      {alert.type}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
                  <Edit3 className="w-4 h-4" />
                </button>
                <button className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
