"use client";

/**
 * Canlı Bot & Decider — MT5 kutusunun panelden görünümü ve uzaktan kumandası.
 * Evrim Ajanı köprüsü: kalp atışı, gerçek işlem performansı, decider karnesi,
 * ders gönderme / git pull / güvenli yeniden başlatma.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Bot,
  GitPullRequest,
  Loader2,
  MonitorSmartphone,
  Power,
  Sparkles,
  Wifi,
  WifiOff,
} from "lucide-react";

import {
  type RemoteCommandSummary,
  useBotPerformance,
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

export default function RemoteBotBoard({ days }: { days: number }) {
  const { data: status, isLoading: statusLoading, isError } = useRemoteStatus();
  const { data: bot } = useBotPerformance(days);
  const { data: decider } = useDeciderStats(days);
  const command = useRemoteCommand();
  const [confirmRestart, setConfirmRestart] = useState(false);

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
              <div className="mt-4 w-full space-y-2">
                {Object.entries(bot.by_symbol).map(([sym, s], i) => (
                  <motion.div key={sym} {...stagger(i)} className="flex items-center gap-2 text-xs">
                    <span className="w-20 shrink-0 truncate font-medium text-slate-300">{sym}</span>
                    <div className="flex-1">
                      <ProgressBar pct={s.win_rate ?? 0} color={wrColor(s.win_rate)} delay={i * 0.05} />
                    </div>
                    <span className="w-24 shrink-0 text-right tabular-nums text-slate-500">
                      %{s.win_rate ?? "—"} · {s.n} işlem
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </GlassCard>

        {/* ── Decider karnesi + komut geçmişi ── */}
        <GlassCard>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-300">
            <Wifi size={15} /> Decider & Komutlar
          </h3>
          {decider && decider.total_decisions > 0 ? (
            <div className="mb-4">
              <div className="mb-2 flex items-baseline justify-between text-xs">
                <span className="text-slate-400">{decider.total_decisions} karar · {decider.resolved} sonuçlandı</span>
                {decider.win_rate !== null && (
                  <span className="text-base font-bold" style={{ color: wrColor(decider.win_rate) }}>
                    %{decider.win_rate}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(decider.decisions).map(([d, n]) => (
                  <Badge key={d} tone={d.includes("BUY") ? "green" : d.includes("SELL") ? "red" : "slate"}>
                    {d} × {n}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <p className="mb-4 rounded-xl border border-dashed border-white/10 p-3 text-center text-[11px] text-slate-500">
              Decider kararı henüz gelmedi.
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
    </Section>
  );
}
