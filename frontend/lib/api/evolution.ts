/**
 * Evrim Paneli API istemcisi — /api/evolution/*
 * Tüm veri erişimi bu katmandan; component'te fetch YOK.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API = getApiBase();

/**
 * Canlı yenileme aralıkları (2026-08-26).
 *
 * Önceki hâlde detay sorgularının HİÇBİRİNDE `refetchInterval` yoktu; yalnız
 * `staleTime` vardı. `staleTime` "veri bayat sayılsın mı" sorusunu cevaplar,
 * yeniden çekmeyi TETİKLEMEZ — tetikleyici (odak/aralık/mount) yoksa panel
 * açık kaldığı sürece ilk yüklenen veriyi gösterir. Decider işlem geçmişinin
 * günlerce eski görünmesinin sebebi buydu.
 *
 * Aralıklar veri kaynağının GERÇEK tazelenme hızına göre seçildi:
 * decider ~1 dk'da bir karar yazar, MT5 işlemleri kapanışta senkronlanır,
 * katalog/kayıt dosyaları elle değişir.
 */
export const LIVE = {
  /** Karar/işlem akışı — dakikalık tazelenen kaynaklar. */
  fast: 30_000,
  /** Kırılım/karne sorguları — hesabı ağır, dakikada bir yeter. */
  normal: 60_000,
  /** Yavaş değişen kataloglar. */
  slow: 5 * 60_000,
} as const;

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

/** Ufuk hücresi — ham isabet + baseline-göreli beceri (2026-07-30). */
export interface BiasHorizonCell {
  n: number;
  correct: number;
  accuracy_pct: number | null;
  /** Aynı satırlarda en iyi SABİT yönün (hep-boğa/hep-ayı) isabeti. */
  baseline_acc_pct: number | null;
  /** Beceri = isabet − baseline. Pozitif değilse öngörü yok demektir. */
  skill_vs_baseline_pp: number | null;
  avg_signed_ret_pct: number | null;
  /** n<30 → erken gözlem, kanıt değil. */
  early_observation: boolean;
}

export interface PrimarySymbolStat {
  horizon_min: number;
  n: number;
  correct: number;
  accuracy_pct: number | null;
  baseline_acc_pct: number | null;
  skill_vs_baseline_pp: number | null;
  early_observation: boolean;
  avg_signed_ret_pct: number | null;
  abstain_n: number;
  abstain_rate_pct: number | null;
  abstain_quiet_day_pct: number | null;
  /** Kronolojik son 20 karar — panel ısı şeridi (eski→yeni). */
  timeline?: BiasTimelineCell[];
}

/** Yön dağılımı izleme — ayı/boğa çağrı sayısı + yöne göre isabet (2026-07-30). */
export interface DirectionBalance {
  bearish: { n: number; accuracy_pct: number | null; avg_signed_ret_pct: number | null };
  bullish: { n: number; accuracy_pct: number | null; avg_signed_ret_pct: number | null };
  bearish_share_pct: number | null;
}

/**
 * Karar ömrü (2026-08-02). `alive_until_min` = kararın merdiven üzerinde
 * KESİNTİSİZ lehte kaldığı son ufuk; 0 = ilk 10 dakikada bile tutmadı.
 * `by_session_clock` sembolün KENDİ seans saatinde ölçülür — 08:00'de verilen
 * kararın +240dk'sı ile 09:45'te verilenin +240dk'sı aynı saate düşmediği için
 * "hangi saatten sonra bozuluyor" ancak duvar saatiyle sorulabilir.
 */
/** Tek bir kararın izi: "29.000'de BUY dendi, fiyat ne yaptı?" */
export interface DecisionTrace {
  ny_date: string;
  symbol: string;
  run_label: string;
  /** Kararın verildiği an (UTC, HH:MM). */
  utc_time: string;
  bias: "bullish" | "bearish";
  confidence: number | null;
  /** Karar anındaki fiyat — tüm ölçümlerin referans çizgisi. */
  anchor_price: number | null;
  /** Karardan hemen sonra KESİNTİSİZ doğru tarafta kalınan dakika. */
  follow_min: number | null;
  /** Seans içindeki EN UZUN kesintisiz doğru-taraf serisi (dk). */
  max_run_min: number | null;
  /** Seansın yüzde kaçında fiyat karar fiyatının doğru tarafındaydı. */
  time_on_side_pct: number | null;
  /** Karar fiyatının bar İÇİNDE ilk kez delindiği dakika. */
  first_adverse_cross_min: number | null;
  session_close: { at: string; pct: number; ok: boolean | null } | null;
  /** Seans saati → karar yönünde işaretli % (pozitif = karar tutuyor). */
  clock: Record<string, number>;
}

export interface FollowStat {
  n: number;
  median: number | null;
  avg: number | null;
}

export interface DecisionDurability {
  n: number;
  median_alive_min: number | null;
  alive_buckets: Record<string, number>;
  /** Takip süresi özeti — üçü BİRLİKTE okunur, tek başına hiçbiri yeterli değil. */
  follow_summary?: {
    immediate_follow_min: FollowStat;
    longest_run_min: FollowStat;
    first_adverse_cross_min: FollowStat;
    time_on_side_pct: FollowStat;
    session_close_accuracy_pct: number | null;
    session_close_n: number;
  };
  /** Son 30 yönlü kararın tek tek izi. */
  traces?: DecisionTrace[];
  dead_within_10min_pct: number | null;
  by_session_clock: Record<string, {
    n: number;
    accuracy_pct: number;
    avg_signed_ret_pct: number;
    early_observation: boolean;
  }>;
  reached_own_target_n: number;
  median_minutes_to_target: number | null;
  levels_prebreached_pct: number | null;
  note: string;
}

export interface BiasReport {
  total_graded: number;
  /** ANA METRİK (2026-07-18): sembolün birincil ufkunda yönlü isabet; çekimserler hariç. */
  primary_intraday?: {
    per_symbol: Record<string, PrimarySymbolStat>;
    overall: {
      n: number;
      correct: number;
      accuracy_pct: number | null;
      /** Genel baseline (sembollerin birincil ufuklarında havuzlanmış) + beceri. */
      baseline_acc_pct?: number | null;
      skill_vs_baseline_pp?: number | null;
      early_observation?: boolean;
    };
  };
  /** Yön dağılımı (ayı/boğa dengesi + yöne göre isabet) — yanlılık takibi. */
  direction_balance?: Record<string, DirectionBalance>;
  /** KARAR ÖMRÜ (2026-08-02): karar kaç dakika lehte kalıyor, hangi saatte bozuluyor. */
  decision_durability?: DecisionDurability;
  /** LEGACY gün-kapanışı metriği — yanıltıcı olabilir, ana metrik değil. */
  overall: BiasRate;
  by_symbol: Record<string, BiasRate>;
  by_run_label: Record<string, BiasRate>;
  by_confidence_bucket: Record<string, BiasRate>;
  by_horizon?: Record<string, BiasHorizonCell>;
  by_symbol_horizon?: Record<string, Record<string, BiasHorizonCell>>;
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
  /** İşlem senkron sağlığı — 'çevrimiçi' ile aynı şey değildir. */
  trade_sync?: TradeSyncHealth;
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
  /** Son işlemin üstünden geçen saat — 72+ ise senkron durmuş olabilir. */
  data_age_hours: number | null;
}

/** bot_trades senkronunun durduğunu sayan eşik (backend ile aynı). */
export const TRADE_STALE_HOURS = 72;

/**
 * Ajanın MT5 işlem senkronu sağlığı (ajan ≥1.1). `reported=false` ise kutuda
 * eski ajan sürümü çalışıyordur — durum BİLİNMİYOR, uyarı basılmaz.
 */
export interface TradeSyncHealth {
  ok: boolean | null;
  last_push: string | null;
  error: string | null;
  fail_streak: number;
  reported: boolean;
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
    refetchInterval: LIVE.fast,
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
    refetchInterval: LIVE.normal,
  });
}

export function useBacklog() {
  return useQuery<{ items: BacklogItem[] }>({
    queryKey: ["evolution", "backlog"],
    queryFn: () => getJson("/api/evolution/backlog"),
    refetchInterval: LIVE.normal,
    placeholderData: (prev) => prev,
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
    refetchInterval: LIVE.normal,
    placeholderData: (prev) => prev,
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
    refetchInterval: LIVE.normal,
    placeholderData: (prev) => prev,
    retry: 1,
  });
}

export function useDeciderStats(days = 30) {
  return useQuery<DeciderStats>({
    queryKey: ["evolution", "remote", "decider-stats", days],
    queryFn: () => getJson(`/api/evolution/remote/decider-stats?days=${days}`),
    refetchInterval: LIVE.fast,
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
    staleTime: LIVE.normal,
    refetchInterval: LIVE.normal,
    placeholderData: (prev) => prev,
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
    staleTime: LIVE.fast,
    refetchInterval: LIVE.fast,
    placeholderData: (prev) => prev,
  });
}

// ── Decider kırılımı + Bot↔Decider diyaloğu ──────────────────────────────

export interface DeciderBreakdown {
  days: number;
  by_symbol: Record<string, {
    waits: number;
    opens: number;
    wins: number;
    losses: number;
    open_pending: number;
    win_rate: number | null;
    by_direction: Record<string, { n: number; wins: number; losses: number; win_rate: number | null }>;
  }>;
  recent: { ts: string; symbol: string; direction: string; outcome: string | null; reason: string }[];
}

/** Bir kırılım kovası — gün, yön, seans ve saat hepsinde aynı şekil. */
export interface DeciderBucket {
  opens: number;
  wins: number;
  losses: number;
  pending: number;
  resolved: number;
  net_r: number;
  win_rate: number | null;
  avg_r: number | null;
}

export interface DeciderDay extends DeciderBucket {
  day: string;
  waits: number;
  foregone_r: number;
  BUY: DeciderBucket;
  SELL: DeciderBucket;
}

export interface DeciderDirection extends DeciderBucket {
  avg_size: number | null;
  missed: { n: number; wins: number; r: number };
  by_session: Record<string, DeciderBucket>;
  by_hour: (DeciderBucket & { hour: number })[];
}

export interface DeciderDecision {
  ts: string;
  day: string;
  session: string;
  action: string;
  direction: string | null;
  outcome: "WIN" | "LOSS" | null;
  /** Brüt R (geometriden). */
  r: number | null;
  /** Spread SONRASI R — gerçek sonuç budur, `r` değil. */
  r_net: number | null;
  cost_usd: number | null;
  cf_direction: string | null;
  cf_outcome: string | null;
  cf_r: number | null;
  size_factor: number | null;
  entry: number | null;
  sl: number | null;
  tp: number | null;
  /** Hedefin girişe puan cinsinden uzaklığı ("ne kadar TP"). */
  tp_distance: number | null;
  /** Stop'un girişe puan cinsinden uzaklığı ("ne kadar SL"). */
  sl_distance: number | null;
  /** Gerçekleşen çıkış fiyatı: WIN→TP, LOSS→SL. */
  exit_price: number | null;
  /** Maximum Favorable Excursion — lehte gidilen en uzak nokta (R). */
  mfe_r: number | null;
  /** Maximum Adverse Excursion — aleyhte görülen en dip nokta (R). */
  mae_r: number | null;
  /** Hedefe ne kadar yaklaşıldı (0-1). */
  tp_progress: number | null;
  bars_to_outcome: number | null;
  outcome_at: string | null;
  atr: number | null;
  spread: number | null;
  rr: number | null;
  mode: string | null;
  shadow_model: string | null;
  management: string;
  reason: string;
}

export interface DeciderSymbolHistory {
  symbol: string;
  days: number;
  total_rows: number;
  summary: DeciderBucket & {
    waits: number;
    foregone_r: number;
    missed_wins: number;
    rr_typical: number | null;
    breakeven_wr: number | null;
    above_breakeven: boolean;
    active_days: number;
    best_day: { day: string; net_r: number } | null;
    worst_day: { day: string; net_r: number } | null;
    first_ts: string | null;
    last_ts: string | null;
  };
  by_day: DeciderDay[];
  by_direction: Record<string, DeciderDirection>;
  decisions: DeciderDecision[];
}

export function useDeciderSymbolHistory(symbol: string | null, days = 30) {
  return useQuery<DeciderSymbolHistory>({
    queryKey: ["evolution", "remote", "decider-symbol-history", symbol, days],
    queryFn: () =>
      getJson(`/api/evolution/remote/decider-symbol-history?symbol=${encodeURIComponent(symbol!)}&days=${days}`),
    enabled: !!symbol,
    staleTime: LIVE.fast,
    refetchInterval: LIVE.fast,
    placeholderData: (prev) => prev,
  });
}

// ── Bot sembol geçmişi — decider'ınkiyle AYNI şekil, gerçek MT5 işlemleri ──
// 2026-08-27: bot_trades'e giriş/SL/TP zenginleştirmesi eklendi (bkz.
// evolution_agent._lookup_entry); bu uç decider'ın gün/yön/işlem-defteri
// panelinin bot karşılığıdır. R, planlanan SL'den hesaplanır (sembol-
// agnostik — pip dönüşümü yok). Eski satırlarda (agent 1.2 öncesi) entry/
// sl/tp/r alanları null gelebilir; bileşenler bunu zarifçe gösterir.

/** Bir kırılım kovası — gün, yön, seans, saat hepsinde aynı şekil (bot). */
export interface BotBucket {
  n: number;
  wins: number;
  losses: number;
  /** MT5 exit reason=5 (TP) ile kapanan işlem sayısı. */
  tp_hits: number;
  /** MT5 exit reason=4 (SL) ile kapanan işlem sayısı. */
  sl_hits: number;
  /** Net $ (profit + commission + swap). */
  net: number;
  win_rate: number | null;
  avg_net: number | null;
  /** Ortalama R — yalnız giriş+SL bilinen işlemlerden (bkz. summary.with_geometry). */
  avg_r: number | null;
}

export interface BotDay extends BotBucket {
  day: string;
  BUY: BotBucket;
  SELL: BotBucket;
}

export interface BotDirection extends BotBucket {
  by_session: Record<string, BotBucket>;
  by_hour: (BotBucket & { hour: number })[];
}

export interface BotTradeRow {
  ts: string;
  day: string;
  session: string;
  direction: string | null;
  /** Giriş fiyatı — agent 1.2 öncesi satırlarda null. */
  entry: number | null;
  exit: number | null;
  /** Planlanan stop (trailing sonradan değiştirmiş olabilir; bu İLK plandır). */
  sl: number | null;
  tp: number | null;
  /** Gerçekleşen hareket / planlanan stop mesafesi. null → geometri yok. */
  r: number | null;
  net: number;
  win: boolean;
  /** MT5 deal reason'dan: "TP" | "SL" | "manuel". */
  exit_reason: "TP" | "SL" | "manuel";
  volume: number | null;
  commission: number | null;
  swap: number | null;
  comment: string | null;
}

export interface BotSymbolHistory {
  symbol: string;
  days: number;
  total_rows: number;
  summary: BotBucket & {
    rr_typical: number | null;
    breakeven_wr: number | null;
    above_breakeven: boolean;
    active_days: number;
    best_day: { day: string; net: number } | null;
    worst_day: { day: string; net: number } | null;
    first_ts: string | null;
    last_ts: string | null;
    /** Kaç işlemde R hesaplanabildi (giriş+SL mevcuttu) — şeffaflık için. */
    with_geometry: number;
  };
  by_day: BotDay[];
  by_direction: Record<string, BotDirection>;
  decisions: BotTradeRow[];
}

export function useBotSymbolHistory(symbol: string | null, days = 30) {
  return useQuery<BotSymbolHistory>({
    queryKey: ["evolution", "remote", "bot-symbol-history", symbol, days],
    queryFn: () =>
      getJson(`/api/evolution/remote/bot-symbol-history?symbol=${encodeURIComponent(symbol!)}&days=${days}`),
    enabled: !!symbol,
    staleTime: LIVE.fast,
    refetchInterval: LIVE.fast,
    placeholderData: (prev) => prev,
  });
}

export interface BotVsDecider {
  days: number;
  window_hours: number;
  stats: {
    agree_n: number; agree_bot_win: number; agree_decider_win: number;
    conflict_n: number; conflict_bot_win: number; conflict_decider_win: number;
    decider_korudu: number; decider_kacirdi: number;
    bot_korundu: number; bot_kacirdi: number;
  };
  lessons: { to: "bot" | "decider" | "both"; text: string }[];
  recent_pairs: {
    time: string; symbol: string; category: string;
    bot_direction: string | null; bot_net: number;
    decider_action: string; decider_direction: string | null; decider_outcome: string | null;
  }[];
}

export function useDeciderBreakdown(days = 30, enabled = true) {
  return useQuery<DeciderBreakdown>({
    queryKey: ["evolution", "remote", "decider-breakdown", days],
    queryFn: () => getJson(`/api/evolution/remote/decider-breakdown?days=${days}`),
    enabled,
    staleTime: LIVE.fast,
    refetchInterval: LIVE.fast,
    placeholderData: (prev) => prev,
  });
}

export function useBotVsDecider(days = 30) {
  return useQuery<BotVsDecider>({
    queryKey: ["evolution", "remote", "bot-vs-decider", days],
    queryFn: () => getJson(`/api/evolution/remote/bot-vs-decider?days=${days}`),
    refetchInterval: LIVE.normal,
    placeholderData: (prev) => prev,
    retry: 1,
  });
}

// ── Gölge Modu paneli ────────────────────────────────────────────────────
// Sistemde GÖLGE çalışan her şeyin tek karnesi: kapılar, ters modeller,
// kâğıt-işlemler. Backend: services/shadow_overview.py.

/** signal_metrics kanonik karnesi — WR asla yalnız okunmaz. */
export interface CanonMetrics {
  n: number;
  wins: number;
  partials: number;
  losses: number;
  ambiguous: number;
  neutral: number;
  open: number;
  win_rate: number | null;
  /** ASIL karar metriği. Negatifse WR yüksek olsa da kenar yoktur. */
  expectancy_r: number | null;
  median_r: number | null;
  /** Geometrinin gerektirdiği başabaş WR = 1/(1+RR). */
  breakeven_wr: number | null;
  edge_pp: number | null;
  avg_rr_geometry: number | null;
  total_r: number;
  excluded_r: number;
  mixed_epochs: boolean;
  warnings: string[];
  by_epoch: Record<string, Omit<CanonMetrics, "by_epoch" | "headline">>;
  headline: string;
}

export interface ShadowGateVerdict {
  code: "ac" | "acma" | "notr" | "veri_yok";
  label: string;
  detail: string;
}

export interface ShadowGate {
  id: string;
  label: string;
  note: string;
  flag: string;
  enabled: boolean;
  blocking: boolean;
  mode: "BLOK" | "GÖLGE";
  would_block_total: number;
  metrics: CanonMetrics;
  verdict: ShadowGateVerdict;
  recent: {
    id: string;
    at: string;
    symbol: string;
    model: string;
    direction: string;
    status: string;
    reason: string | null;
  }[];
}

export interface ShadowGateReport {
  days: number;
  signals_with_shadow_verdict: number;
  gates: ShadowGate[];
  measured_gates: number;
  since_instrumented: string;
  note: string;
}

export interface ShadowModelFamily {
  id: string;
  label: string;
  note: string;
  total: number;
  metrics: CanonMetrics;
  models: { model_type: string; total: number; metrics: CanonMetrics }[];
}

export interface ShadowModelReport {
  days: number;
  families: ShadowModelFamily[];
  alerts: { level: string; text: string }[];
}

export interface ShadowTradeBucket {
  key: string;
  label: string;
  total: number;
  resolved: number;
  wins: number;
  losses: number;
  expired: number;
  open: number;
  ambiguous: number;
  degenerate: number;
  win_rate: number | null;
  median_rr: number | null;
  breakeven_wr: number | null;
  expectancy_r: number | null;
  total_r: number;
  edge_pp: number | null;
  warnings: string[];
  by_symbol?: ShadowTradeBucket[];
  by_direction?: ShadowTradeBucket[];
}

export interface ShadowTradeReport {
  days: number;
  total: number;
  enabled: boolean;
  sources: ShadowTradeBucket[];
  recent: {
    at: string;
    resolved_at: string | null;
    source: string;
    symbol: string;
    direction: string;
    pattern: string | null;
    timeframe: string | null;
    confidence: number | null;
    status: string;
    entry: number | null;
    tp: number | null;
    sl: number | null;
    exit: number | null;
    r: number | null;
    ambiguous: boolean;
    rr: number | null;
  }[];
  last_at: string | null;
}

export interface ShadowFlags {
  gates: {
    id: string;
    label: string;
    enabled_flag: string;
    block_flag: string;
    enabled: boolean;
    blocking: boolean;
    mode: "KAPALI" | "BLOK" | "GÖLGE";
  }[];
  experiments: { flag: string; label: string; on: boolean }[];
}

export interface ShadowOverview {
  days: number;
  generated_at: string;
  errors: { block: string; error: string }[];
  gates: ShadowGateReport | null;
  models: ShadowModelReport | null;
  trades: ShadowTradeReport | null;
  flags: ShadowFlags | null;
}

export function useShadowOverview(days = 30) {
  return useQuery<ShadowOverview>({
    queryKey: ["evolution", "shadow", "overview", days],
    queryFn: () => getJson(`/api/evolution/shadow/overview?days=${days}`),
    refetchInterval: LIVE.normal,
    staleTime: LIVE.normal,
    placeholderData: (prev) => prev,
    retry: 1,
  });
}
