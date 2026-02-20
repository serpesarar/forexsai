"use client";

import { useWSData } from "../contexts/WebSocketContext";
import { Wifi, WifiOff } from "lucide-react";
import { useState, useEffect } from "react";

export default function WSStatusBadge() {
  const { status, lastUpdate } = useWSData();
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const config = {
    connected: { color: "bg-success", text: "Live", icon: Wifi },
    connecting: { color: "bg-yellow-500", text: "Connecting...", icon: Wifi },
    disconnected: { color: "bg-white/20", text: "Offline", icon: WifiOff },
    error: { color: "bg-danger", text: "Error", icon: WifiOff },
  }[status];

  const Icon = config.icon;

  return (
    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/5 border border-white/10 text-[10px]">
      <span className={`w-1.5 h-1.5 rounded-full ${config.color} ${status === "connected" ? "animate-pulse" : ""}`} />
      <Icon className="w-3 h-3 text-textSecondary" />
      <span className="text-textSecondary font-mono">{config.text}</span>
      {lastUpdate && status === "connected" && now && (
        <span className="text-textSecondary/50 ml-0.5">
          {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
        </span>
      )}
    </div>
  );
}
