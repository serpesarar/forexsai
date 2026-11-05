/** Çok kaynaklı haber beslemesi istemcisi (`/api/newsfeed/*`). Haber yön sinyali değildir: HB-01 olay çalışması. */
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { getApiBase } from "./base";

const API = getApiBase();
const LATEST_LIMIT = 150;
const MAX_LIVE_ITEMS = 300;
const SOURCES_REFETCH_MS = 30_000;
const STATUS_REFETCH_MS = 15_000;
const SSE_RETRY_MS = 5_000;

export type NewsUrgency = "breaking" | "high" | "medium" | "low";

export interface NewsStory {
  id: string;
  headline: string;
  url: string;
  first_seen_at: string;
  first_source: string;
  first_source_name: string;
  tier: string;
  event_type: string;
  symbols: string[];
  urgency: NewsUrgency;
  relevance: number;
  confirmation: "official" | "reported" | "unconfirmed";
  is_opinion: boolean;
  n_sources: number;
  sources: string[];
  published_at: string | null;
  seeded?: boolean;
  display_at: string;
}

export interface SourceScore {
  id: string;
  name: string;
  tier: string;
  kind: string;
  repo: string;
  unofficial: boolean;
  races: number;
  first_count: number;
  first_rate: number | null;
  lag_raw_p50_s: number | null;
  lag_raw_p95_s: number | null;
  lag_adj_p50_s: number | null;
  publish_lag_p50_s: number | null;
  polls: number;
  errors: number;
  items_new: number;
  error_rate: number | null;
  fetch_p50_ms: number | null;
  last_ok_ago_s: number | null;
  last_item_ago_s: number | null;
  last_error: string | null;
  interval_s: number | null;
}

export interface InactiveSource {
  id: string;
  name: string;
  reason: string;
  repo: string;
}

export interface NewsFeedStatus {
  running: boolean;
  uptime_s: number;
  sources_total: number;
  sources_alive: number;
  adaptive: boolean;
  stories_in_buffer: number;
  in_release_window: boolean;
  ingest_p50_ms: number | null;
  subscribers: number;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as T;
}

export function useNewsSources() {
  return useQuery({
    queryKey: ["newsfeed", "sources"],
    queryFn: () => getJson<{ sources: SourceScore[]; inactive: InactiveSource[] }>("/api/newsfeed/sources"),
    refetchInterval: SOURCES_REFETCH_MS,
  });
}

export function useNewsStatus() {
  return useQuery({
    queryKey: ["newsfeed", "status"],
    queryFn: () => getJson<NewsFeedStatus>("/api/newsfeed/status"),
    refetchInterval: STATUS_REFETCH_MS,
  });
}

export interface RepoScore {
  repo: string;
  url: string;
  lisans: string;
  son_kod_gun: number;
  arsiv: boolean;
  puan: number;
  karar: string;
  karar_tr: string;
  rol: string;
  kullanim: string;
  kar_kaniti: string;
  kanit_sinifi: string;
}

export function useRepoScorecard() {
  return useQuery({
    queryKey: ["newsfeed", "repo-scorecard"],
    queryFn: () => getJson<{ uretim: string | null; repolar: RepoScore[] }>("/api/newsfeed/repo-scorecard"),
  });
}

interface StreamEvent {
  type: "story" | "story_update";
  story?: NewsStory;
  id?: string;
  n_sources?: number;
  sources?: string[];
}

/** İlk listeyi REST'ten alır, sonra SSE ile canlı tutar; bağlantı koparsa yeniden bağlanır. */
export function useNewsStream(symbol: string | null, minRelevance: number) {
  const [items, setItems] = useState<NewsStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [live, setLive] = useState(false);
  const filter = useRef({ symbol, minRelevance });
  filter.current = { symbol, minRelevance };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const query = new URLSearchParams({ limit: String(LATEST_LIMIT), min_relevance: String(minRelevance) });
    if (symbol) query.set("symbol", symbol);
    getJson<{ items: NewsStory[] }>(`/api/newsfeed/latest?${query}`)
      .then((d) => {
        if (cancelled) return;
        setItems(d.items);
        setError(null);
      })
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [symbol, minRelevance]);

  useEffect(() => {
    let source: EventSource | null = null;
    let retry: ReturnType<typeof setTimeout> | undefined;
    let closed = false;
    const connect = () => {
      source = new EventSource(`${API}/api/newsfeed/stream`);
      source.onopen = () => setLive(true);
      source.onerror = () => {
        setLive(false);
        source?.close();
        if (!closed) retry = setTimeout(connect, SSE_RETRY_MS);
      };
      source.onmessage = (msg) => {
        const ev = JSON.parse(msg.data) as StreamEvent;
        const f = filter.current;
        if (ev.type === "story" && ev.story) {
          const s = ev.story;
          if (s.relevance < f.minRelevance || s.is_opinion || (f.symbol && !s.symbols.includes(f.symbol))) return;
          setItems((prev) => [s, ...prev.filter((p) => p.id !== s.id)].slice(0, MAX_LIVE_ITEMS));
        } else if (ev.type === "story_update" && ev.id) {
          setItems((prev) => prev.map((p) => (p.id === ev.id ? { ...p, n_sources: ev.n_sources ?? p.n_sources, sources: ev.sources ?? p.sources } : p)));
        }
      };
    };
    connect();
    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      source?.close();
    };
  }, []);

  return { items, loading, error, live };
}
