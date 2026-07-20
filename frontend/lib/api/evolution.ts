/**
 * Evrim Paneli API istemcisi — /api/evolution/*
 * Tüm veri erişimi bu katmandan; component'te fetch YOK.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API = getApiBase();

// ── Tipler ───────────────────────────────────────────────────────────────

export interface ModelAccuracy {
  strategy: string;
  total_predictions: number;
  with_outcome: number;
  ml_accuracy: number | null;
  target_hit_rate: number | null;
  stop_hit_rate: number | null;
  expired: number;
  partial_target_hit: number;
}

export interface BiasRate {
  n: number;
  correct: number;
  accuracy_pct: number | null;
}

export interface BiasTimelineCell {
  d: string; // ny_date
  ok: boolean | null; // true=isabet, false=ıska, null=çekimser (nötr/choppy)
  bias: string;
  label: string | null;
}

export interface PrimarySymbolStat {
  horizon_min: number;
  n: number;
  correct: number;
  accuracy_pct: number | null;
  avg_signed_ret_pct: number | null;
  abstain_n: number;
  abstain_rate_pct: number | null;
  abstain_quiet_day_pct: number | null;
  /** Kronolojik son 20 karar — panel ısı şeridi (eski→yeni). */
  timeline?: BiasTimelineCell[];
}

export interface BiasReport {
  total_graded: number;
  /** ANA METRİK (2026-07-18): sembolün birincil ufkunda yönlü isabet; çekimserler hariç. */
  primary_intraday?: {
    per_symbol: Record<string, PrimarySymbolStat>;
    overall: { n: number; correct: number; accuracy_pct: number | null };
  };
  /** LEGACY gün-kapanışı metriği — yanıltıcı olabilir, ana metrik değil. */
  overall: BiasRate;
  by_symbol: Record<string, BiasRate>;
  by_run_label: Record<string, BiasRate>;
  by_confidence_bucket: Record<string, BiasRate>;
  by_horizon?: Record<string, { n: number; correct: number; accuracy_pct: number | null; avg_signed_ret_pct: number | null }>;
  by_symbol_horizon?: Record<string, Record<string, { n: number; correct: number; accuracy_pct: number | null; avg_signed_ret_pct: number | null }>>;
  go_live_hint: string;
}

export interface Overview {
  generated_at: string;
  days: number;
  models: { models: ModelAccuracy[]; total: number } | null;
  bias: BiasReport | null;
  /** Soğuk başlangıç: kaynak arka planda ısınıyor, sonraki yenilemede gelir. */
  models_warming?: boolean;
  bias_warming?: boolean;
  counts: {
    registry: number;
    analyses: number;
    backlog_pending: number;
    backlog_total: number;
    lessons_active: number;
  };
  active_runs: RunMeta[];
}

export interface RegistryComponent {
  id: string;
  name: string;
  file: string;
  category: string;
  purpose: string;
  key_functions: string[];
  status_hint: string;
  agents?: { id: string; role: string }[];
}

export interface Analysis {
  id: string;
  name: string;
  kind?: "script" | "endpoint";
  command?: string;
  method?: string;
  path?: string;
  category: string;
  what_it_does: string;
  output: string;
  needs_backend: boolean;
  est_runtime: string;
  runnable_here?: boolean;
  run_note?: string;
  learn_targets?: string[];
}

export interface RunMeta {
  run_id: string;
  analysis_id: string;
  analysis_name: string;
  command: string;
  status: "running" | "done" | "failed" | "timeout" | "interrupted";
  started_at: string;
  finished_at: string | null;
  return_code: number | null;
  output?: string;
  output_truncated?: boolean;
  /** true → MT5 kutusundaki Evrim Ajanı'nda koşuyor (run_id 'cmd_' öneklidir) */
  remote?: boolean;
}

// ── Evrim Ajanı köprüsü (MT5 kutusu) ─────────────────────────────────────

export interface RemoteCommandSummary {
  id: string;
  created_at: string;
  kind: string;
  status: "pending" | "running" | "done" | "failed" | "timeout";
  requested_by: string;
  analysis_id: string | null;
  analysis_name: string | null;
  finished_at: string | null;
  return_code: number | null;
}

export interface RemoteStatus {
  host: string;
  online: boolean;
  last_seen: string | null;
  last_seen_ago_s: number | null;
  meta: { open_positions?: number; mt5?: boolean; [k: string]: unknown };
  pending_commands: number;
  running_commands: number;
  recent_commands: RemoteCommandSummary[];
}

export interface BotPerformance {
  days: number;
  total_trades: number;
  win_rate: number | null;
  net_profit: number;
  by_symbol: Record<string, { n: number; wins: number; net: number; win_rate: number | null }>;
  last_trade_at: string | null;
}

export interface DeciderStats {
  days: number;
  total_decisions: number;
  wait_count: number;
  open_count: number;
  decisions: Record<string, number>;
  resolved: number;
  win_rate: number | null;
  last_decision_at: string | null;
  last_trade_decision_at: string | null;
  active: boolean;
}

export interface BacklogItem {
  id: string;
  title: string;
  detail: string;
  category: string;
  priority: "high" | "medium" | "low";
  status: "pending" | "in_progress" | "done" | "dropped";
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ChangelogEntry {
  kind: "commit" | "session" | "worktree";
  id: string;
  ts: string;
  author: string;
  summary: string;
  files?: string[];
  backlog_added?: string[];
}

export interface Lesson {
  id: string;
  created_at: string;
  title: string;
  summary: string;
  symbol: string | null;
  targets: string[];
  source: Record<string, unknown>;
  status: "active" | "archived";
}

// ── fetch yardımcıları ───────────────────────────────────────────────────

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json();
}

async function sendJson<T>(path: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = String(data.detail);
    } catch {
      /* gövde JSON değilse durum kodu yeter */
    }
    throw new Error(detail);
  }
  return res.json();
}

// ── Query hook'ları ──────────────────────────────────────────────────────

export function useOverview(days = 30) {
  return useQuery<Overview>({
    queryKey: ["evolution", "overview", days],
    queryFn: () => getJson(`/api/evolution/overview?days=${days}`),
    refetchInterval: 60_000,
    // Gün aralığı değişince sayaçlar 0'a düşmesin — eski veri, yenisi gelene dek kalır
    placeholderData: (prev) => prev,
  });
}

export function useRegistry() {
  return useQuery<{ components: RegistryComponent[] }>({
    queryKey: ["evolution", "registry"],
    queryFn: () => getJson("/api/evolution/registry"),
    staleTime: 10 * 60_000,
  });
}

export function useAnalyses() {
  return useQuery<{ analyses: Analysis[] }>({
    queryKey: ["evolution", "analyses"],
    queryFn: () => getJson("/api/evolution/analyses"),
    staleTime: 10 * 60_000,
  });
}

export function useChangelog(limit = 60) {
  return useQuery<{ entries: ChangelogEntry[] }>({
    queryKey: ["evolution", "changelog", limit],
    queryFn: () => getJson(`/api/evolution/changelog?limit=${limit}`),
    refetchInterval: 120_000,
  });
}

export function useBacklog() {
  return useQuery<{ items: BacklogItem[] }>({
    queryKey: ["evolution", "backlog"],
    queryFn: () => getJson("/api/evolution/backlog"),
  });
}

export function useRuns(limit = 40) {
  return useQuery<{ runs: RunMeta[] }>({
    queryKey: ["evolution", "runs", limit],
    queryFn: () => getJson(`/api/evolution/runs?limit=${limit}`),
    refetchInterval: 15_000,
  });
}

/** Aktif run çıktısını 3sn'de bir izle (running değilse durur). */
export function useRunDetail(runId: string | null) {
  return useQuery<RunMeta>({
    queryKey: ["evolution", "run", runId],
    queryFn: () => getJson(`/api/evolution/runs/${runId}`),
    enabled: !!runId,
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 3_000 : false,
  });
}

export function useLessons() {
  return useQuery<{ lessons: Lesson[] }>({
    queryKey: ["evolution", "lessons"],
    queryFn: () => getJson("/api/evolution/lessons"),
  });
}

// ── Mutation hook'ları ───────────────────────────────────────────────────

export function useStartRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ analysisId, extraArgs }: { analysisId: string; extraArgs?: string }) =>
      sendJson<RunMeta>(`/api/evolution/analyses/${analysisId}/run`, "POST", {
        extra_args: extraArgs ?? "",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evolution", "runs"] });
      qc.invalidateQueries({ queryKey: ["evolution", "overview"] });
    },
  });
}

export function useLearnFromRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      runId,
      targets,
      symbol,
      instruction,
    }: {
      runId: string;
      targets: string[];
      symbol?: string | null;
      instruction?: string;
    }) =>
      sendJson<Lesson>(`/api/evolution/runs/${runId}/learn`, "POST", {
        targets,
        symbol: symbol ?? null,
        instruction: instruction ?? "",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evolution", "lessons"] }),
  });
}

export function useUpdateBacklog() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...fields }: { id: string } & Partial<BacklogItem>) =>
      sendJson<BacklogItem>(`/api/evolution/backlog/${id}`, "PATCH", fields),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evolution", "backlog"] }),
  });
}

export function useAddBacklog() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; detail?: string; category?: string; priority?: string }) =>
      sendJson<BacklogItem>("/api/evolution/backlog", "POST", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evolution", "backlog"] }),
  });
}

export function useArchiveLesson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: "active" | "archived" }) =>
      sendJson<Lesson>(`/api/evolution/lessons/${id}`, "PATCH", { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evolution", "lessons"] }),
  });
}

// ── Evrim Ajanı köprüsü hook'ları (MT5 kutusu) ───────────────────────────

export function useRemoteStatus() {
  return useQuery<RemoteStatus>({
    queryKey: ["evolution", "remote", "status"],
    queryFn: () => getJson("/api/evolution/remote/status"),
    refetchInterval: 30_000,
    retry: 1,
  });
}

export function useBotPerformance(days = 30) {
  return useQuery<BotPerformance>({
    queryKey: ["evolution", "remote", "bot-performance", days],
    queryFn: () => getJson(`/api/evolution/remote/bot-performance?days=${days}`),
    refetchInterval: 120_000,
    placeholderData: (prev) => prev,
    retry: 1,
  });
}

export function useDeciderStats(days = 30) {
  return useQuery<DeciderStats>({
    queryKey: ["evolution", "remote", "decider-stats", days],
    queryFn: () => getJson(`/api/evolution/remote/decider-stats?days=${days}`),
    refetchInterval: 120_000,
    placeholderData: (prev) => prev,
    retry: 1,
  });
}

/** Kutuya komut gönder: sync_lessons | git_pull | restart_bot */
export function useRemoteCommand() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ kind, payload }: { kind: "sync_lessons" | "git_pull" | "restart_bot"; payload?: Record<string, unknown> }) =>
      sendJson<RunMeta>("/api/evolution/remote/command", "POST", { kind, payload: payload ?? {} }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evolution", "remote"] }),
  });
}

// ── Model detayı (tıkla → sembol/yön kırılımı) ───────────────────────────

export interface DirectionStat {
  total: number;
  wins: number;
  losses: number;
  win_rate: number | null;
}

export interface SymbolBreakdown {
  total: number;
  wins: number;
  losses: number;
  flips: number;
  expired: number;
  win_rate: number | null;
  by_direction: Record<string, DirectionStat>;
}

export interface ModelDetail {
  strategy: string;
  days: number;
  total: number;
  wins: number;
  losses: number;
  flips: number;
  expired: number;
  win_rate: number | null;
  by_symbol: Record<string, SymbolBreakdown>;
  recent: {
    symbol: string;
    direction: string;
    outcome: string;
    profit_pips: number | null;
    created_at: string;
  }[];
}

export function useModelDetail(strategy: string | null, days = 30) {
  return useQuery<ModelDetail>({
    queryKey: ["evolution", "model-detail", strategy, days],
    queryFn: () => getJson(`/api/learning/model-symbol-breakdown?strategy=${encodeURIComponent(strategy!)}&days=${days}`),
    enabled: !!strategy,
    staleTime: 5 * 60_000,
  });
}

export interface BotTrade {
  ticket: number;
  symbol: string;
  direction: string;
  volume: number | null;
  close_time: string;
  close_price: number | null;
  net: number;
  comment: string | null;
}

export function useBotTrades(symbol: string | null, days = 30) {
  return useQuery<{ symbol: string; days: number; trades: BotTrade[] }>({
    queryKey: ["evolution", "remote", "bot-trades", symbol, days],
    queryFn: () => getJson(`/api/evolution/remote/bot-trades?symbol=${encodeURIComponent(symbol!)}&days=${days}`),
    enabled: !!symbol,
    staleTime: 60_000,
  });
}
