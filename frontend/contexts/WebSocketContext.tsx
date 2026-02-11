"use client";

import React, { createContext, useContext, useCallback, useEffect, useRef, useState } from "react";

const WS_BASE = "wss://upbeat-flow-production.up.railway.app";

const RECONNECT_BASE_MS = 2000;
const RECONNECT_MAX_MS = 30000;

// ─── Types ───────────────────────────────────────────────────────────────────

export interface SymbolData {
  symbol: string;
  timestamp: string;
  data: {
    symbol: string;
    updated_at: string;
    ml_prediction: any;
    ta_snapshot: any;
    current_price: number | null;
    macro: any;
    session: any;
    volume: any;
    volatility: any;
  };
  news?: any;
}

type WSStatus = "connecting" | "connected" | "disconnected" | "error";

interface WebSocketContextValue {
  /** Current connection status */
  status: WSStatus;
  /** Latest data per symbol */
  symbolData: Record<string, SymbolData>;
  /** When the last update was received */
  lastUpdate: Date | null;
  /** Force reconnect */
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue>({
  status: "disconnected",
  symbolData: {},
  lastUpdate: null,
  reconnect: () => {},
});

export function useWSData() {
  return useContext(WebSocketContext);
}

/** Get data for a specific symbol from the WS context */
export function useWSSymbolData(symbol: string): SymbolData | null {
  const { symbolData } = useContext(WebSocketContext);
  return symbolData[symbol] ?? null;
}

// ─── Provider ────────────────────────────────────────────────────────────────

interface Props {
  children: React.ReactNode;
}

export function WebSocketProvider({ children }: Props) {
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [symbolData, setSymbolData] = useState<Record<string, SymbolData>>({});
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cleanup = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      if (
        wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING
      ) {
        wsRef.current.close(1000, "cleanup");
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    cleanup();
    setStatus("connecting");

    // Connect to /ws/all to receive updates for all symbols in one connection
    const url = `${WS_BASE}/ws/all`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        reconnectAttempt.current = 0;
        console.log("[WS] Connected to broadcast stream");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          // Keepalive
          if (msg.type === "ping") {
            ws.send(JSON.stringify({ type: "pong" }));
            return;
          }
          if (msg.type === "pong") return;

          // Update message — contains symbol data
          if (msg.type === "update" && msg.symbol) {
            setSymbolData((prev) => ({
              ...prev,
              [msg.symbol]: msg as SymbolData,
            }));
            setLastUpdate(new Date());
          }
        } catch {
          // non-JSON, ignore
        }
      };

      ws.onclose = (event) => {
        setStatus("disconnected");
        wsRef.current = null;

        if (event.code === 1000) return; // intentional close

        // Exponential backoff
        const delay = Math.min(
          RECONNECT_BASE_MS * Math.pow(1.5, reconnectAttempt.current),
          RECONNECT_MAX_MS
        );
        reconnectAttempt.current += 1;
        console.log(
          `[WS] Reconnecting in ${Math.round(delay / 1000)}s (attempt ${reconnectAttempt.current})`
        );
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        setStatus("error");
      };
    } catch (e) {
      console.error("[WS] Connection error:", e);
      setStatus("error");
    }
  }, [cleanup]);

  const reconnect = useCallback(() => {
    reconnectAttempt.current = 0;
    connect();
  }, [connect]);

  // Connect on mount
  useEffect(() => {
    connect();
    return cleanup;
  }, [connect, cleanup]);

  return (
    <WebSocketContext.Provider value={{ status, symbolData, lastUpdate, reconnect }}>
      {children}
    </WebSocketContext.Provider>
  );
}
