/**
 * Fiyat alarmları API istemcisi — /api/alerts (backend/routers/price_alert_router.py).
 * Yönetici oturumu gerekir (alarm Telegram'a yazar); çağrılar authenticatedFetch ile.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiBase } from "./base";
import { authenticatedFetch } from "./authenticatedFetch";

const API = getApiBase();

export type AlertKind = "above" | "below" | "pct_move" | "time" | "stop" | "target";
export type AlertStatus = "active" | "triggered" | "disabled";

export interface PriceAlert {
  id: number;
  symbol: string;
  kind: AlertKind;
  price: number | null;
  pct: number | null;
  ref_price: number | null;
  at_utc: string | null;
  label: string | null;
  source: "manual" | "plan" | "signal";
  status: AlertStatus;
  one_shot: boolean;
  notify_telegram: boolean;
  created_at: string;
  triggered_at: string | null;
  triggered_price: number | null;
}

export interface AlertsResponse {
  alerts: PriceAlert[];
  service: { enabled: boolean; interval_s: number; last_run: { at: string | null; checked: number; triggered: number; error: string | null } };
}

export interface AlertInput {
  symbol: string;
  kind: AlertKind;
  price?: number;
  pct?: number;
  at_utc?: string;
  label?: string;
  one_shot?: boolean;
  notify_telegram?: boolean;
}

export interface PlanAlertInput {
  symbol: string;
  side: "buy" | "sell";
  entry: number;
  stop: number;
  target: number;
  horizon_min?: number;
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await authenticatedFetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const msg = typeof detail?.detail === "string" ? detail.detail : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

const KEY = ["price-alerts"];

export function useAlerts() {
  return useQuery<AlertsResponse>({
    queryKey: KEY,
    queryFn: () => call("/api/alerts"),
    refetchInterval: 30_000,
    retry: false,
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: KEY });
}

export function useCreateAlert() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: AlertInput) => call<{ created: PriceAlert[] }>("/api/alerts", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: invalidate,
  });
}

export function useCreatePlanAlerts() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: PlanAlertInput) =>
      call<{ created: PriceAlert[] }>("/api/alerts/from-plan", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: invalidate,
  });
}

export function useSetAlertStatus() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: "active" | "disabled" }) =>
      call(`/api/alerts/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
    onSuccess: invalidate,
  });
}

export function useDeleteAlert() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: number) => call(`/api/alerts/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}
