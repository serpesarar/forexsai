"use client";

import { useState } from "react";
import EmelPanel from "./EmelPanel";
import PulsePanel from "./PulsePanel";

interface TradingPanelProps {
  symbol?: string;
}

export default function TradingPanel({ symbol = "XAUUSD" }: TradingPanelProps) {
  const [mode, setMode] = useState<"emel" | "pulse">("emel");
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);

  return (
    <div className="space-y-4">
      {/* Symbol Selector */}
      <div className="flex items-center gap-4">
        <select
          value={selectedSymbol}
          onChange={(e) => setSelectedSymbol(e.target.value)}
          className="bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700"
        >
          <option value="XAUUSD">🥇 XAUUSD (Gold)</option>
          <option value="NDX.INDX">📈 NASDAQ</option>
        </select>
        
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setMode("emel")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === "emel"
                ? "bg-blue-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            🧠 EMEL (Stratejik)
          </button>
          <button
            onClick={() => setMode("pulse")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === "pulse"
                ? "bg-yellow-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            ⚡ PULSE (Scalp)
          </button>
        </div>
      </div>

      {/* Panel Content */}
      {mode === "emel" ? (
        <EmelPanel symbol={selectedSymbol} onSwitchMode={() => setMode("pulse")} />
      ) : (
        <PulsePanel symbol={selectedSymbol} onSwitchMode={() => setMode("emel")} />
      )}
    </div>
  );
}
