"use client";

import React, { createContext, useContext, useCallback, useEffect, useRef, useState } from "react";
import { buildWebSocketUrl } from "../lib/api/base";

// Aggressive reconnection for real-time data
const RECONNECT_BASE_MS = 500; // Start with 500ms (was 2000ms)
const RECONNECT_MAX_MS = 10000; // Max 10s (was 30s)
const HEARTBEAT_INTERVAL_MS = 15000; // Send ping every 15s
const HEARTBEAT_TIMEOUT_MS = 30000; // Consider dead if no pong in 30s

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
  panels?: {
    pulse_v3?: any;
    emel?: any;
    mtf?: any;
    clear_trend?: any;
  };
  news?: any;
}

type WSStatus = "connecting" | "connected" | "disconnected" | "error";

function parseWsTimestamp(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1_000_000_000_000 ? Math.floor(value) : Math.floor(value * 1000);
  }

  if (typeof value === "string") {
    const numeric = Number(value);
    if (Number.isFinite(numeric) && value.trim() !== "") {
      return numeric > 1_000_000_000_000 ? Math.floor(numeric) : Math.floor(numeric * 1000);
    }
    const parsed = new Date(value).getTime();
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

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
  reconnect: () => { },
});

export function useWSData() {
  return useContext(WebSocketContext);
}

/** Get data for a specific symbol from the WS context */
export function useWSSymbolData(symbol: string): SymbolData | null {
  const { symbolData } = useContext(WebSocketContext);
  // Null safety check
  if (!symbolData) return null;
  return symbolData[symbol] ?? null;
}

/** Get specific panel data for a symbol from the WS stream.
 *  panelKey: "pulse_v3" | "emel" | "mtf" | "clear_trend" */
export function useWSPanelData(symbol: string, panelKey: string): { data: any | null; wsConnected: boolean } {
  const { symbolData, status } = useContext(WebSocketContext);
  const wsConnected = status === "connected";
  // Null safety checks
  if (!symbolData) return { data: null, wsConnected };
  const symbolInfo = symbolData[symbol];
  if (!symbolInfo) return { data: null, wsConnected };
  const panels = symbolInfo.panels;
  if (!panels) return { data: null, wsConnected };
  const data = panels[panelKey as keyof typeof panels] ?? null;
  return { data, wsConnected };
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
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastPongTime = useRef<number>(Date.now());

  const cleanup = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
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
        try {
          wsRef.current.close(1000, "cleanup");
        } catch (e) {
          // Ignore close errors
        }
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    cleanup();
    setStatus("connecting");

    const url = buildWebSocketUrl("/ws/all");

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        reconnectAttempt.current = 0;
        lastPongTime.current = Date.now();
        console.log("[WS] Connected to broadcast stream");

        // Start heartbeat
        if (heartbeatTimer.current) {
          clearInterval(heartbeatTimer.current);
        }
        heartbeatTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            // Check if we've received a pong recently
            const timeSinceLastPong = Date.now() - lastPongTime.current;
            if (timeSinceLastPong > HEARTBEAT_TIMEOUT_MS) {
              console.warn("[WS] Heartbeat timeout, reconnecting...");
              cleanup();
              connect();
              return;
            }
            // Send ping
            try {
              ws.send(JSON.stringify({ type: "ping" }));
            } catch (e) {
              console.error("[WS] Failed to send ping:", e);
            }
          }
        }, HEARTBEAT_INTERVAL_MS);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const receiveTime = Date.now(); // The moment we received the message

          // Tracking lag for debugging
          if (msg.timestamp || msg?.data?.updated_at) {
            const msgTime = parseWsTimestamp(msg.timestamp || msg.data?.updated_at);
            const lag = msgTime == null ? null : receiveTime - msgTime;
            if (lag !== null && lag > 5000) {
              console.warn(`[WS] HIGH LAG DETECTED: ${lag}ms - Message timestamp: ${msg.timestamp}`);
            }
          }

          // Keepalive
          if (msg.type === "ping") {
            try {
              ws.send(JSON.stringify({ type: "pong" }));
            } catch (e) {
              console.error("[WS] Failed to send pong:", e);
            }
            return;
          }
          if (msg.type === "pong") {
            lastPongTime.current = Date.now();
            return;
          }

          // Partial update message for instant real-time ticks
          if (msg.type === "price_update" && msg.symbol && msg.price !== undefined) {
            const now = new Date().toISOString();
            setSymbolData((prev) => {
              const existing = prev[msg.symbol] || ({} as Partial<SymbolData>);
              const existingData = existing.data || {
                symbol: msg.symbol,
                updated_at: now,
                ml_prediction: null,
                ta_snapshot: null,
                current_price: null,
                macro: null,
                session: null,
                volume: null,
                volatility: null,
              };

              return {
                ...prev,
                [msg.symbol]: {
                  ...existing,
                  symbol: msg.symbol, // ensure symbol is set
                  timestamp: now, // ALWAYS refresh timestamp to trigger re-renders
                  data: {
                    ...existingData,
                    current_price: msg.price,
                    updated_at: now, // refresh data updated_at too
                    ...(existingData.ta_snapshot ? {
                      ta_snapshot: {
                        ...existingData.ta_snapshot,
                        current_price: msg.price
                      }
                    } : {})
                  }
                } as SymbolData,
              };
            });
            setLastUpdate(new Date());
            return;
          }

          // Update message — contains full symbol data
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

        // Clear heartbeat
        if (heartbeatTimer.current) {
          clearInterval(heartbeatTimer.current);
          heartbeatTimer.current = null;
        }

        if (event.code === 1000) return; // intentional close

        // Aggressive exponential backoff for faster reconnection
        // First retry: 500ms, Second: 750ms, Third: 1125ms, Max: 10s
        const delay = Math.min(
          RECONNECT_BASE_MS * Math.pow(1.3, reconnectAttempt.current),
          RECONNECT_MAX_MS
        );
        reconnectAttempt.current += 1;
        console.log(
          `[WS] Connection closed (code: ${event.code}). Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempt.current})`
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
