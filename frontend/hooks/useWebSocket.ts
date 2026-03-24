"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { buildWebSocketUrl } from "../lib/api/base";

// Reconnect with exponential backoff
const RECONNECT_BASE_MS = 2000;
const RECONNECT_MAX_MS = 30000;

export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseWebSocketOptions {
  /** Symbol to subscribe to (e.g. "NDX.INDX", "XAUUSD", "all") */
  symbol: string;
  /** Called when a message is received */
  onMessage?: (data: any) => void;
  /** Auto-connect on mount (default: true) */
  autoConnect?: boolean;
  /** Enable the hook (default: true) — set false to disable */
  enabled?: boolean;
}

interface UseWebSocketReturn {
  status: WSStatus;
  lastMessage: any | null;
  lastUpdate: Date | null;
  send: (data: any) => void;
  reconnect: () => void;
}

export function useWebSocket({
  symbol,
  onMessage,
  autoConnect = true,
  enabled = true,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<WSStatus>("disconnected");
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onMessageRef = useRef(onMessage);
  const symbolRef = useRef(symbol);
  const enabledRef = useRef(enabled);

  // Keep refs current
  onMessageRef.current = onMessage;
  symbolRef.current = symbol;
  enabledRef.current = enabled;

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
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close(1000, "cleanup");
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!enabledRef.current) return;

    cleanup();
    setStatus("connecting");

    const url = buildWebSocketUrl(`/ws/${encodeURIComponent(symbolRef.current)}`);
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        reconnectAttempt.current = 0;
        console.log(`[WS] Connected: ${symbolRef.current}`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle keepalive pings
          if (data.type === "ping") {
            ws.send(JSON.stringify({ type: "pong" }));
            return;
          }
          if (data.type === "pong") return;

          setLastMessage(data);
          setLastUpdate(new Date());
          onMessageRef.current?.(data);
        } catch {
          // Non-JSON message, ignore
        }
      };

      ws.onclose = (event) => {
        setStatus("disconnected");
        wsRef.current = null;

        // Don't reconnect if intentionally closed
        if (event.code === 1000) return;

        // Exponential backoff reconnect
        if (enabledRef.current) {
          const delay = Math.min(
            RECONNECT_BASE_MS * Math.pow(1.5, reconnectAttempt.current),
            RECONNECT_MAX_MS
          );
          reconnectAttempt.current += 1;
          console.log(`[WS] Reconnecting in ${Math.round(delay / 1000)}s (attempt ${reconnectAttempt.current})`);
          reconnectTimer.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        setStatus("error");
      };
    } catch (e) {
      console.error("[WS] Connection error:", e);
      setStatus("error");
    }
  }, [cleanup]);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const reconnect = useCallback(() => {
    reconnectAttempt.current = 0;
    connect();
  }, [connect]);

  // Connect on mount / symbol change
  useEffect(() => {
    if (autoConnect && enabled) {
      connect();
    }
    return cleanup;
  }, [symbol, enabled, autoConnect, connect, cleanup]);

  // Handle symbol change without full reconnect — send subscribe command
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "subscribe", symbol }));
    }
  }, [symbol]);

  return { status, lastMessage, lastUpdate, send, reconnect };
}
