"use client";

/**
 * Canlı Bot & Decider — MT5 kutusunun panelden görünümü ve uzaktan kumandası.
 * Evrim Ajanı köprüsü: kalp atışı, gerçek işlem performansı, decider karnesi,
 * ders gönderme / git pull / güvenli yeniden başlatma.
 */

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bot,
  GitPullRequest,
  Loader2,
  MessagesSquare,
  MonitorSmartphone,
  Power,
  Sparkles,
  Wifi,
  WifiOff,
  X,
} from "lucide-react";

import {
  type RemoteCommandSummary,
  useBotPerformance,
  useBotTrades,
  useBotVsDecider,
  useDeciderBreakdown,
  useDeciderStats,
  useRemoteCommand,
  useRemoteStatus,
} from "@/lib/api/evolution";
import { emitOpenRun } from "./events";
import { toast } from "./toast";
import { Badge, GlassCard, ProgressBar, PulseDot, Ring, Section, Skeleton, cx, stagger, timeAgo } from "./ui";

const KIND_LABELS: Record<string, string> = {
  run_analysis: "analiz",
  sync_lessons: "ders senkronu",
  git_pull: "git pull",
  restart_bot: "bot restart",
};

function wrColor(pct: number | null): string {
  if (pct === null) return "#64748B";
  if (pct >= 55) return "#34D399";
  if (pct >= 45) return "#FBBF24";
  return "#FB7185";
}

function CommandRow({ cmd }: { cmd: RemoteCommandSummary }) {
  const tone =
    cmd.status === "done" ? "green" : cmd.status === "failed" || cmd.status === "timeout" ? "red" : "blue";
  return (
    <button
      onClick={() => emitOpenRun(`cmd_${cmd.id}`)}
      className="flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left text-xs transition hover:bg-white/[0.04]"
      title="Çıktıyı aç"
    >
      <span className="min-w-0 truncate text-slate-300">
        {cmd.analysis_name ?? KIND_LABELS[cmd.kind] ?? cmd.kind}
      </span>
      <span className="flex shrink-0 items-center gap-2 text-slate-500">
        {cmd.requested_by === "scheduler" && <Badge tone="purple">haftalık</Badge>}
        <Badge tone={tone}>{cmd.status === "pending" ? "kuyrukta" : cmd.status === "running" ? "çalışıyor" : cmd.status === "done" ? "bitti" : cmd.status}</Badge>
        {timeAgo(cmd.created_at)}
      </span>
    </button>
  );
}

/** Decider yüzdesine tıkla → sembol × yön kırılımı + son kararlar (gerekçeli). */
function DeciderDetailSheet({ days, onClose }: { days: number; onClose: () => void }) {
  const { data, isLoading } = useDeciderBreakdown(days);
  const symbols = Object.entries(data?.by_symbol ?? {}).sort((a, b) => b[1].opens - a[1].opens);
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-3 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 40, opacity: 0, scale: 0.98 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 40, opacity: 0, scale: 0.98 }}
        transition={{ type: "spring", damping: 28, stiffness: 320 }}
        className="flex max-h-[86vh] w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <Wifi size={15} className="text-violet-300" /> Claude Decider — istatistik
            <Badge tone="slate">son {days} gün</Badge>
          </span>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <div className="overflow-y-auto px-5 py-4">
          {isLoading && <Skeleton className="h-32 w-full" />}
          {symbols.length > 0 && (
            <div className="space-y-3">
              {symbols.map(([sym, s], i) => (
                <motion.div
                  key={sym}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-3.5"
                >
                  <div className="mb-2 flex items-baseline justify-between">
                    <span className="text-[13px] font-semibold text-slate-200">
                      {sym.replace(".INDX", "").replace(".FOREX", "")}
                    </span>
                    <span className="text-xs tabular-nums text-slate-500">
                      <span className="text-sm font-bold" style={{ color: wrColor(s.win_rate) }}>
                        {s.win_rate !== null ? `%${Math.round(s.win_rate)}` : "—"}
                      </span>{" "}
                      · {s.opens} işlem kararı
                    </span>
                  </div>
                  <ProgressBar pct={s.win_rate ?? 0} color={wrColor(s.win_rate)} />
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {Object.entries(s.by_direction)
                      .sort((a, b) => b[1].n - a[1].n)
                      .map(([dir, d]) => (
                        <Badge key={dir} tone={dir === "BUY" ? "green" : dir === "SELL" ? "red" : "slate"}>
                          {dir} {d.win_rate !== null ? `%${Math.round(d.win_rate)}` : "—"} ({d.wins}K/{d.losses}Z)
                        </Badge>
                      ))}
                    <Badge tone="slate">{s.waits} bekle</Badge>
                    {s.open_pending > 0 && <Badge tone="blue">{s.open_pending} sonuç bekliyor</Badge>}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
          {(data?.recent?.length ?? 0) > 0 && (
            <div className="mt-5">
              <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Son kararlar — gerekçeleriyle
              </h4>
              <div className="space-y-1.5">
                {data!.recent.filter((r) => r.direction !== "?").slice(0, 10).map((r, i) => (
                  <div key={i} className="rounded-xl px-2.5 py-1.5 text-[11px] odd:bg-white/[0.02]">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-slate-300">
                        <span className={cx("font-semibold", r.direction === "BUY" ? "text-emerald-300" : "text-rose-300")}>
                          {r.direction}
                        </span>
                        {r.symbol.replace(".INDX", "").replace(".FOREX", "")}
                      </span>
                      <span className="flex items-center gap-2 text-slate-500">
                        {r.outcome && (
                          <Badge tone={r.outcome === "WIN" ? "green" : "red"}>
                            {r.outcome === "WIN" ? "kazandı" : "kaybetti"}
                          </Badge>
                        )}
                        {timeAgo(r.ts)}
                      </span>
                    </div>
                    {r.reason && <p className="mt-1 leading-snug text-slate-500">{r.reason}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

const PAIR_CATEGORY: Record<string, { label: string; tone: "green" | "red" | "amber" | "blue" | "slate" }> = {
  agree: { label: "aynı yön", tone: "blue" },
  conflict: { label: "çatışma", tone: "amber" },
  decider_korudu: { label: "decider korudu", tone: "green" },
  decider_kacirdi: { label: "decider kaçırdı", tone: "red" },
};

/** Bot ↔ Decider diyaloğu — yakın-zaman kıyası + karşılıklı dersler. */
function BotVsDeciderCard({ days }: { days: number }) {
  const { data } = useBotVsDecider(days);
  if (!data) return null;
  const s = data.stats;
  const total = s.agree_n + s.conflict_n + s.decider_korudu + s.decider_kacirdi;
  return (
    <GlassCard className="mt-5">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold text-slate-300">
        <MessagesSquare size={15} className="text-cyan-300" /> Bot ↔ Decider Diyaloğu
        <span className="text-xs font-normal text-slate-500">
          aynı sembol, ±{data.window_hours} saat penceresi · son {days} gün
        </span>
      </h3>
      {total === 0 && s.bot_kacirdi + s.bot_korundu === 0 ? (
        <p className="rounded-xl border border-dashed border-white/10 p-4 text-center text-[12px] text-slate-500">
          Örtüşen işlem penceresi henüz yok — iki sistem veri ürettikçe kıyas burada belirecek.
        </p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Sol: sayılar */}
          <div className="space-y-2 text-[12px]">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-xl border border-sky-400/15 bg-sky-400/[0.05] p-2.5">
                <span className="block text-lg font-bold tabular-nums text-sky-300">{s.agree_n}</span>
                <span className="text-slate-400">aynı yönde açtılar</span>
                <span className="block text-[10px] text-slate-500">bot {s.agree_bot_win}K · decider {s.agree_decider_win}K</span>
              </div>
              <div className="rounded-xl border border-amber-400/15 bg-amber-400/[0.05] p-2.5">
                <span className="block text-lg font-bold tabular-nums text-amber-300">{s.conflict_n}</span>
                <span className="text-slate-400">zıt yönde (çatışma)</span>
                <span className="block text-[10px] text-slate-500">bot {s.conflict_bot_win} · decider {s.conflict_decider_win} haklı</span>
              </div>
              <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.05] p-2.5">
                <span className="block text-lg font-bold tabular-nums text-emerald-300">{s.decider_korudu}</span>
                <span className="text-slate-400">decider WAIT dedi, bot kaybetti</span>
                <span className="block text-[10px] text-slate-500">bekleme haklıydı (fren değeri)</span>
              </div>
              <div className="rounded-xl border border-rose-400/15 bg-rose-400/[0.05] p-2.5">
                <span className="block text-lg font-bold tabular-nums text-rose-300">{s.decider_kacirdi}</span>
                <span className="text-slate-400">decider WAIT dedi, bot kazandı</span>
                <span className="block text-[10px] text-slate-500">fazla temkin (kaçan fırsat)</span>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="flex-1 rounded-xl border border-white/[0.07] bg-white/[0.02] p-2.5">
                <span className="block text-base font-bold tabular-nums text-slate-200">{s.bot_kacirdi}</span>
                <span className="text-[10px] text-slate-500">decider solo kazandı — bot görmedi</span>
              </div>
              <div className="flex-1 rounded-xl border border-white/[0.07] bg-white/[0.02] p-2.5">
                <span className="block text-base font-bold tabular-nums text-slate-200">{s.bot_korundu}</span>
                <span className="text-[10px] text-slate-500">decider solo kaybetti — bot uzak durdu</span>
              </div>
            </div>
          </div>

          {/* Sağ: karşılıklı dersler */}
          <div>
            <h4 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Birbirlerine dersleri
            </h4>
            <div className="space-y-2">
              {data.lessons.map((l, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className={cx(
                    "rounded-2xl border p-3 text-[11px] leading-relaxed",
                    l.to === "bot"
                      ? "border-orange-400/15 bg-orange-400/[0.05] text-orange-100/90"
                      : l.to === "decider"
                        ? "border-violet-400/15 bg-violet-400/[0.05] text-violet-100/90"
                        : "border-cyan-400/15 bg-cyan-400/[0.05] text-cyan-100/90"
                  )}
                >
                  <span className="mb-0.5 block text-[9px] font-bold uppercase tracking-wide opacity-70">
                    {l.to === "bot" ? "🤖 Bot'a ders" : l.to === "decider" ? "🧠 Decider'a ders" : "⚖ Ortak ders"}
                  </span>
                  {l.text}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Son eşleşmeler */}
      {(data.recent_pairs?.length ?? 0) > 0 && (
        <div className="mt-4">
          <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Son eşleşmeler</h4>
          <div className="space-y-0.5">
            {data.recent_pairs.slice(0, 8).map((p, i) => {
              const cat = PAIR_CATEGORY[p.category] ?? { label: p.category, tone: "slate" as const };
              return (
                <div key={i} className="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-[11px] odd:bg-white/[0.02]">
                  <span className="flex min-w-0 items-center gap-2 text-slate-300">
                    <span className="shrink-0 font-medium">{p.symbol.replace(".INDX", "").replace(".FOREX", "")}</span>
                    <span className={cx("shrink-0", (p.bot_net ?? 0) >= 0 ? "text-emerald-300/80" : "text-rose-300/80")}>
                      bot {p.bot_direction} {p.bot_net >= 0 ? "+" : ""}{p.bot_net}$
                    </span>
                    <span className="truncate text-slate-500">
                      decider {p.decider_action === "WAIT" ? "bekledi" : `${p.decider_direction ?? ""} ${p.decider_outcome === "WIN" ? "kazandı" : p.decider_outcome === "LOSS" ? "kaybetti" : ""}`}
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2 text-slate-500">
                    <Badge tone={cat.tone}>{cat.label}</Badge>
                    {timeAgo(p.time)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </GlassCard>
  );
}

/** Sembole tıkla → o sembolün son MT5 işlemleri. */
function TradesSheet({ symbol, days, onClose }: { symbol: string; days: number; onClose: () => void }) {
  const { data, isLoading } = useBotTrades(symbol, days);
  const trades = data?.trades ?? [];
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-3 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 40, opacity: 0, scale: 0.98 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: 40, opacity: 0, scale: 0.98 }}
        transition={{ type: "spring", damping: 28, stiffness: 320 }}
        className="w-full max-w-lg overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <span className="flex items-center gap-2 text-sm font-semibold text-slate-100">
            <Bot size={15} className="text-orange-300" /> {symbol} — son işlemler
            <Badge tone="slate">son {days} gün</Badge>
          </span>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
          {isLoading && <Skeleton className="h-24 w-full" />}
          {!isLoading && trades.length === 0 && (
            <p className="rounded-xl border border-dashed border-white/10 p-4 text-center text-[12px] text-slate-500">
              Bu pencerede işlem yok.
            </p>
          )}
          <div className="space-y-0.5">
            {trades.map((t) => (
              <div key={t.ticket} className="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-[11px] odd:bg-white/[0.02]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className={cx("font-semibold", t.direction === "BUY" ? "text-emerald-300" : "text-rose-300")}>
                    {t.direction}
                  </span>
                  {t.volume != null && <span className="text-slate-500">{t.volume} lot</span>}
                  {t.comment && <span className="truncate text-slate-600">{t.comment}</span>}
                </span>
                <span className="flex shrink-0 items-center gap-2.5 text-slate-500">
                  <span className={cx("font-semibold tabular-nums", t.net >= 0 ? "text-emerald-300" : "text-rose-300")}>
                    {t.net >= 0 ? "+" : ""}{t.net} $
                  </span>
                  {timeAgo(t.close_time)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function RemoteBotBoard({ days }: { days: number }) {
  const { data: status, isLoading: statusLoading, isError } = useRemoteStatus();
  const { data: bot } = useBotPerformance(days);
  const { data: decider } = useDeciderStats(days);
  const command = useRemoteCommand();
  const [confirmRestart, setConfirmRestart] = useState(false);
  const [openSymbol, setOpenSymbol] = useState<string | null>(null);
  const [deciderDetail, setDeciderDetail] = useState(false);

  const online = status?.online ?? false;
  const openPositions = status?.meta?.open_positions;

  const send = (kind: "sync_lessons" | "git_pull" | "restart_bot", label: string, payload?: Record<string, unknown>) =>
    command.mutate(
      { kind, payload },
      {
        onSuccess: (run) => {
          toast.success(`${label} kuyruğa alındı — ajan 30 sn içinde başlatır`);
          emitOpenRun(run.run_id);
        },
        onError: (e) => toast.error(`${label} gönderilemedi: ${(e as Error).message}`),
      }
    );

  const handleRestart = () => {
    if (!confirmRestart) {
      setConfirmRestart(true);
      setTimeout(() => setConfirmRestart(false), 4000);
      return;
    }
    setConfirmRestart(false);
    send("restart_bot", "Bot yeniden başlatma", { wait_max_minutes: 120 });
  };

  return (
    <Section
      id="canli-bot"
      title="Canlı Bot & Decider"
      subtitle="MT5 kutusu — gerçek işlem sonuçları ve uzaktan kumanda"
      accent="#FB923C"
      icon={<Bot size={22} />}
    >
      <div className="grid gap-5 lg:grid-cols-3">
        {/* ── Kutu durumu + kumanda ── */}
        <GlassCard glow={online ? "#34D399" : "#FB7185"}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-300">
              <MonitorSmartphone size={15} /> MT5 Kutusu
            </h3>
            {statusLoading ? (
              <Skeleton className="h-6 w-24" />
            ) : online ? (
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1 text-[11px] font-medium text-emerald-300">
                <PulseDot /> çevrimiçi
              </span>
            ) : (
              <span className="flex items-center gap-1.5 rounded-full border border-rose-400/30 bg-rose-400/10 px-2.5 py-1 text-[11px] font-medium text-rose-300">
                <WifiOff size={11} /> çevrimdışı
              </span>
            )}
          </div>

          {!online && !statusLoading && (
            <p className="mb-4 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] p-3 text-[11px] leading-relaxed text-amber-200/90">
              {isError || !status?.last_seen
                ? "Evrim Ajanı henüz hiç bağlanmadı. Kurulum: MT5 kutusunda remote_agent/README.md — 5 dakika, tek seferlik."
                : `Ajan son ${timeAgo(status.last_seen)} görüldü. Kutuda start_agent.bat çalışıyor mu?`}
            </p>
          )}

          <div className="space-y-2 text-[12px] text-slate-400">
            <div className="flex justify-between">
              <span>Son kalp atışı</span>
              <span className="text-slate-200">{status?.last_seen ? timeAgo(status.last_seen) : "—"}</span>
            </div>
            <div className="flex justify-between">
              <span>Açık pozisyon</span>
              <span className="text-slate-200">{typeof openPositions === "number" && openPositions >= 0 ? openPositions : "—"}</span>
            </div>
            <div className="flex justify-between">
              <span>Kuyruk</span>
              <span className="text-slate-200">
                {status ? `${status.pending_commands} bekliyor · ${status.running_commands} çalışıyor` : "—"}
              </span>
            </div>
          </div>

          <div className="mt-5 grid gap-2">
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => send("sync_lessons", "Ders senkronu")}
              disabled={command.isPending}
              className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 px-3 py-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 transition disabled:opacity-40"
            >
              {command.isPending ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              Dersleri Decider'a Gönder
            </motion.button>
            <div className="grid grid-cols-2 gap-2">
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={() => send("git_pull", "Git pull")}
                disabled={command.isPending}
                className="flex items-center justify-center gap-1.5 rounded-xl bg-white/[0.06] px-3 py-2.5 text-xs font-medium text-slate-300 transition hover:bg-white/[0.1] disabled:opacity-40"
              >
                <GitPullRequest size={13} /> Git Pull
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.97 }}
                onClick={handleRestart}
                disabled={command.isPending}
                className={cx(
                  "flex items-center justify-center gap-1.5 rounded-xl px-3 py-2.5 text-xs font-medium transition disabled:opacity-40",
                  confirmRestart
                    ? "bg-rose-500/25 text-rose-200 ring-1 ring-rose-400/60"
                    : "bg-white/[0.06] text-slate-300 hover:bg-white/[0.1]"
                )}
                title="Açık pozisyon varsa kapanmasını bekler"
              >
                <Power size={13} /> {confirmRestart ? "Emin misin?" : "Botu Başlat"}
              </motion.button>
            </div>
            <p className="text-center text-[10px] text-slate-600">
              Yeniden başlatma güvenlidir: açık pozisyon varsa kapanana dek bekler.
            </p>
          </div>
        </GlassCard>

        {/* ── Bot performansı ── */}
        <GlassCard>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Bot size={15} /> Bot İşlem Sonuçları
            <span className="text-xs font-normal text-slate-500">son {days} gün</span>
          </h3>
          {!bot || bot.total_trades === 0 ? (
            <p className="rounded-xl border border-dashed border-white/10 p-4 text-center text-[12px] text-slate-500">
              {online
                ? "Henüz işlem verisi gelmedi — ilk push 5 dk içinde."
                : "Ajan bağlanınca son 30 günün MT5 işlemleri otomatik yüklenecek."}
            </p>
          ) : (
            <div className="flex flex-col items-center">
              <Ring pct={bot.win_rate ?? 0} color={wrColor(bot.win_rate)} size={120}>
                <span className="text-3xl font-bold tabular-nums text-white">
                  {bot.win_rate !== null ? `%${bot.win_rate}` : "—"}
                </span>
                <span className="text-[10px] text-slate-500">{bot.total_trades} işlem</span>
              </Ring>
              <p className={cx("mt-2 text-sm font-bold tabular-nums", bot.net_profit >= 0 ? "text-emerald-300" : "text-rose-300")}>
                {bot.net_profit >= 0 ? "+" : ""}
                {bot.net_profit.toLocaleString("tr-TR")} $
              </p>
              <div className="mt-4 w-full space-y-1">
                {Object.entries(bot.by_symbol).map(([sym, s], i) => (
                  <motion.button
                    key={sym}
                    {...stagger(i)}
                    onClick={() => setOpenSymbol(sym)}
                    className="flex w-full items-center gap-2 rounded-lg px-1.5 py-1.5 text-xs transition hover:bg-white/[0.04]"
                    title="Son işlemleri aç"
                  >
                    <span className="w-20 shrink-0 truncate text-left font-medium text-slate-300">{sym}</span>
                    <div className="flex-1">
                      <ProgressBar pct={s.win_rate ?? 0} color={wrColor(s.win_rate)} delay={i * 0.05} />
                    </div>
                    <span className="w-24 shrink-0 text-right tabular-nums text-slate-500">
                      %{s.win_rate ?? "—"} · {s.n} işlem
                    </span>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </GlassCard>

        {/* ── Decider karnesi + komut geçmişi ── */}
        <GlassCard>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Wifi size={15} /> Claude Decider
            {decider && decider.total_decisions > 0 && (
              decider.active ? (
                <span className="flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                  <PulseDot /> aktif
                </span>
              ) : (
                <span className="rounded-full border border-slate-500/30 bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-400">
                  {decider.last_decision_at ? `son karar ${timeAgo(decider.last_decision_at)}` : "beklemede"}
                </span>
              )
            )}
          </h3>
          {decider && decider.total_decisions > 0 ? (
            <div className="mb-4">
              {/* İşlem kararlarının kazanma oranı (WAIT'ler sonuçsuz — WR'a girmez) */}
              <div className="mb-2.5 flex items-center gap-3">
                {decider.win_rate !== null && (
                  <button
                    onClick={() => setDeciderDetail(true)}
                    className="rounded-full transition hover:scale-105"
                    title="Sembol × yön istatistiğini aç"
                  >
                    <Ring pct={decider.win_rate} color={wrColor(decider.win_rate)} size={64} stroke={6}>
                      <span className="text-lg font-bold tabular-nums text-white">%{Math.round(decider.win_rate)}</span>
                    </Ring>
                  </button>
                )}
                <div className="text-xs leading-relaxed text-slate-400">
                  <div><span className="font-semibold text-slate-200">{decider.open_count}</span> işlem kararı · <span className="font-semibold text-slate-200">{decider.resolved}</span> sonuçlandı</div>
                  <div><span className="font-semibold text-slate-300">{decider.wait_count}</span> bekle (WAIT) kararı</div>
                  <div className="text-slate-500">toplam {decider.total_decisions} karar / son {decider.days} gün</div>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(decider.decisions)
                  .sort((a, b) => b[1] - a[1])
                  .map(([d, n]) => (
                    <Badge key={d} tone={d.includes("BUY") ? "green" : d.includes("SELL") ? "red" : "slate"}>
                      {d === "WAIT" ? "bekle" : d} × {n}
                    </Badge>
                  ))}
              </div>
            </div>
          ) : (
            <p className="mb-4 rounded-xl border border-dashed border-white/10 p-3 text-center text-[11px] text-slate-500">
              Decider kararı henüz gelmedi — MT5 kutusundaki ajan push edince görünür.
            </p>
          )}

          <h4 className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Son komutlar</h4>
          {(status?.recent_commands?.length ?? 0) === 0 ? (
            <p className="py-3 text-center text-[11px] text-slate-600">Henüz komut gönderilmedi.</p>
          ) : (
            <div className="space-y-0.5">
              {status!.recent_commands.slice(0, 7).map((c) => (
                <CommandRow key={c.id} cmd={c} />
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Bot ↔ Decider yakın-zaman kıyası + karşılıklı dersler */}
      <BotVsDeciderCard days={days} />

      <AnimatePresence>
        {openSymbol && <TradesSheet symbol={openSymbol} days={days} onClose={() => setOpenSymbol(null)} />}
        {deciderDetail && <DeciderDetailSheet days={days} onClose={() => setDeciderDetail(false)} />}
      </AnimatePresence>
    </Section>
  );
}
