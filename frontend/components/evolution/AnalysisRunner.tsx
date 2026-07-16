"use client";

/**
 * Hata Analizi Çalıştırıcı — araçları tek tıkla koşturur, canlı çıktı gösterir,
 * "Öğret" ile çıktıyı derse damıtıp motorlara enjekte eder.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BrainCog,
  CheckCircle2,
  ChevronDown,
  Loader2,
  Play,
  Search,
  Sparkles,
  Terminal,
  X,
  XCircle,
} from "lucide-react";

import {
  type Analysis,
  type RunMeta,
  useAnalyses,
  useLearnFromRun,
  useRunDetail,
  useRuns,
  useStartRun,
} from "@/lib/api/evolution";
import { onOpenRun } from "./events";
import { toast } from "./toast";
import { Badge, EmptyState, GlassCard, PulseDot, Section, Skeleton, catLabel, cx, stagger, timeAgo } from "./ui";

const LEARN_TARGET_LABELS: Record<string, string> = {
  bias_debate: "Ajan Tartışması",
  claude_decider: "Claude Decider",
  panel: "Sadece Panel",
};

const CATEGORY_ORDER = [
  "error_analysis",
  "performance",
  "pattern_mining",
  "calibration",
  "backtest",
  "data_repair",
  "other",
];

const CAT_ACCENT: Record<string, string> = {
  error_analysis: "#FB7185",
  performance: "#5EEAD4",
  pattern_mining: "#C4B5FD",
  calibration: "#FCD34D",
  backtest: "#60A5FA",
  data_repair: "#FB923C",
  other: "#94A3B8",
};

function StatusBadge({ status }: { status: RunMeta["status"] }) {
  if (status === "running")
    return (
      <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-300">
        <PulseDot /> çalışıyor
      </span>
    );
  if (status === "done")
    return (
      <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-300">
        <CheckCircle2 size={12} /> bitti
      </span>
    );
  if (status === "timeout")
    return (
      <span className="flex items-center gap-1 text-[11px] font-medium text-amber-300">
        <XCircle size={12} /> zaman aşımı
      </span>
    );
  if (status === "interrupted")
    return (
      <span className="flex items-center gap-1 text-[11px] font-medium text-slate-400">
        <XCircle size={12} /> yarıda kesildi
      </span>
    );
  return (
    <span className="flex items-center gap-1 text-[11px] font-medium text-rose-300">
      <XCircle size={12} /> hata
    </span>
  );
}

function AnalysisCard({
  analysis,
  accent,
  activeRun,
  onOpen,
  index,
}: {
  analysis: Analysis;
  accent: string;
  activeRun: RunMeta | undefined;
  onOpen: (runId: string) => void;
  index: number;
}) {
  const startRun = useStartRun();
  const isRemote = analysis.runnable_here === false; // MT5 kutusunda, Evrim Ajanı üzerinden koşar
  const running = activeRun?.status === "running";

  return (
    <motion.div
      {...stagger(index)}
      whileHover={{ y: -3 }}
      className={cx(
        "group relative flex flex-col overflow-hidden rounded-2xl border p-4 transition-colors",
        running ? "border-emerald-400/30 bg-emerald-400/[0.04]" : "border-white/[0.07] bg-white/[0.025] hover:border-white/15"
      )}
    >
      {/* üst renk şeridi */}
      <span className="absolute inset-x-0 top-0 h-[2px]" style={{ background: `linear-gradient(90deg, ${accent}, transparent)` }} />

      <div className="mb-1.5 flex items-start justify-between gap-2">
        <h4 className="text-[13px] font-semibold leading-snug text-slate-100">{analysis.name}</h4>
        {running ? (
          <button onClick={() => activeRun && onOpen(activeRun.run_id)} className="shrink-0 rounded-xl bg-emerald-400/15 p-2 text-emerald-300" title="Çıktıyı izle">
            <Loader2 size={15} className="animate-spin" />
          </button>
        ) : (
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() =>
              startRun.mutate(
                { analysisId: analysis.id },
                {
                  onSuccess: (run) => {
                    toast.success(isRemote ? `"${analysis.name}" MT5 kutusuna gönderildi` : `"${analysis.name}" başlatıldı`);
                    onOpen(run.run_id);
                  },
                  onError: (e) => toast.error(`Başlatılamadı: ${(e as Error).message}`),
                }
              )
            }
            disabled={startRun.isPending}
            className="shrink-0 rounded-xl p-2 text-white shadow-lg transition disabled:opacity-50"
            style={
              isRemote
                ? { background: "linear-gradient(135deg, #F59E0B, #FB923Cbb)", boxShadow: "0 6px 18px -6px #F59E0B" }
                : { background: `linear-gradient(135deg, ${accent}, ${accent}bb)`, boxShadow: `0 6px 18px -6px ${accent}` }
            }
            title={isRemote ? "MT5 kutusunda çalıştır (Evrim Ajanı)" : "Çalıştır"}
          >
            <Play size={15} />
          </motion.button>
        )}
      </div>

      <p className="mb-3 flex-1 text-[11px] leading-relaxed text-slate-400">{analysis.what_it_does}</p>

      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone="slate">{analysis.est_runtime === "seconds" ? "saniyeler" : analysis.est_runtime === "minutes" ? "dakikalar" : "uzun"}</Badge>
        {analysis.kind === "endpoint" && <Badge tone="blue">API</Badge>}
        {(analysis.learn_targets?.length ?? 0) > 0 && (
          <Badge tone="purple">
            <Sparkles size={10} /> öğretilebilir
          </Badge>
        )}
        {isRemote && <Badge tone="amber">MT5 kutusunda koşar</Badge>}
      </div>
      {startRun.isError && <p className="mt-1.5 text-[10px] text-rose-300">{(startRun.error as Error).message}</p>}
    </motion.div>
  );
}

function RunDrawer({ runId, analyses, onClose }: { runId: string; analyses: Analysis[]; onClose: () => void }) {
  const { data: run } = useRunDetail(runId);
  const learn = useLearnFromRun();
  const analysis = analyses.find((a) => a.id === run?.analysis_id);
  const [targets, setTargets] = useState<string[]>(["panel"]);
  const [seeded, setSeeded] = useState(false);
  const outputRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (!seeded && analysis) {
      if (analysis.learn_targets?.length) setTargets(analysis.learn_targets);
      setSeeded(true);
    }
  }, [analysis, seeded]);

  useEffect(() => {
    if (run?.status === "running" && outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [run?.output, run?.status]);

  const toggle = (t: string) => setTargets((p) => (p.includes(t) ? p.filter((x) => x !== t) : [...p, t]));

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
        className="flex max-h-[86vh] w-full max-w-3xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#0B0F17] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300">
              <Terminal size={15} />
            </span>
            <span className="text-sm font-semibold text-slate-100">{run?.analysis_name ?? "…"}</span>
            {run && <StatusBadge status={run.status} />}
            {run?.remote && <Badge tone="amber">MT5 kutusu</Badge>}
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-white">
            <X size={18} />
          </button>
        </div>

        <pre ref={outputRef} className="flex-1 overflow-auto whitespace-pre-wrap bg-black/20 px-5 py-4 font-mono text-[11px] leading-relaxed text-slate-300">
          {run?.output?.trim() || (run?.status === "running" ? "Çıktı bekleniyor…" : "(çıktı yok)")}
        </pre>

        <div className="border-t border-white/[0.07] px-5 py-4">
          <div className="mb-2.5 flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <BrainCog size={15} className="text-violet-300" /> Öğret →
            </span>
            {Object.entries(LEARN_TARGET_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggle(key)}
                className={cx(
                  "rounded-full px-3 py-1 text-[11px] font-medium transition",
                  targets.includes(key) ? "bg-violet-500/25 text-violet-200 ring-1 ring-violet-400/50" : "bg-white/5 text-slate-400 hover:text-slate-200"
                )}
              >
                {label}
              </button>
            ))}
            <motion.button
              whileTap={{ scale: 0.96 }}
              onClick={() =>
                run &&
                learn.mutate(
                  { runId: run.run_id, targets },
                  {
                    onSuccess: (l) => toast.success(`Ders kaydedildi: "${l.title}"`),
                    onError: (e) => toast.error(`Öğretilemedi: ${(e as Error).message}`),
                  }
                )
              }
              disabled={!run || run.status === "running" || learn.isPending || targets.length === 0}
              className="ml-auto flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 px-3.5 py-2 text-xs font-semibold text-white shadow-lg shadow-violet-500/25 transition disabled:opacity-40"
            >
              {learn.isPending ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {learn.isPending ? "Damıtılıyor…" : "Derse Damıt & Enjekte Et"}
            </motion.button>
          </div>
          {learn.isSuccess && (
            <p className="text-[11px] text-emerald-300">✓ Ders kaydedildi: "{learn.data.title}" — seçilen motorlar bir sonraki çalışmalarında görecek.</p>
          )}
          {learn.isError && <p className="text-[11px] text-rose-300">{(learn.error as Error).message}</p>}
          <p className="mt-1.5 text-[10px] text-slate-500">
            Çıktı LLM ile eyleme dönük derse çevrilir; Ajan Tartışması CIO prompt'una ve Claude Decider LESSONS.md'ye otomatik enjekte edilir.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function AnalysisRunner() {
  const { data: analysesData, isLoading } = useAnalyses();
  const { data: runsData } = useRuns(30);
  const [openRunId, setOpenRunId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ error_analysis: true, performance: true });

  // Komut paletinden başlatılan run'ın çekmecesini aç
  useEffect(() => onOpenRun(setOpenRunId), []);

  const analyses = useMemo(() => analysesData?.analyses ?? [], [analysesData]);
  const runs = runsData?.runs ?? [];

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return analyses;
    return analyses.filter((a) => a.name.toLowerCase().includes(q) || a.what_it_does.toLowerCase().includes(q) || a.id.toLowerCase().includes(q));
  }, [analyses, search]);

  const grouped = useMemo(() => {
    const g: Record<string, Analysis[]> = {};
    for (const a of filtered) (g[a.category] ??= []).push(a);
    return g;
  }, [filtered]);

  const orderedCats = useMemo(() => {
    const extras = Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c));
    return [...CATEGORY_ORDER, ...extras].filter((c) => grouped[c]?.length);
  }, [grouped]);

  const latestRunFor = (id: string) => runs.find((r) => r.analysis_id === id);
  const searching = search.trim().length > 0;

  return (
    <Section
      id="analiz"
      title="Hata Analizi & Geliştirme"
      subtitle="Tek tıkla çalıştır → çıktıyı gör → Öğret ile motorlara işlet"
      accent="#FB7185"
      icon={<Terminal size={22} />}
    >
      <div className="relative mb-5">
        <Search size={16} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={`${analyses.length} araç içinde ara…`}
          className="w-full rounded-2xl border border-white/[0.07] bg-white/[0.03] py-3 pl-11 pr-4 text-sm text-slate-200 placeholder:text-slate-500 transition focus:border-violet-400/50 focus:bg-white/[0.05] focus:outline-none"
        />
      </div>

      {searching && filtered.length === 0 && <EmptyState text={`"${search}" ile eşleşen araç yok.`} />}
      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-2/3" />
        </div>
      )}

      <div className="space-y-4">
        {orderedCats.map((cat) => {
          const isOpen = searching ? true : expanded[cat] ?? false;
          const accent = CAT_ACCENT[cat] ?? "#94A3B8";
          return (
            <GlassCard key={cat}>
              <button onClick={() => setExpanded((p) => ({ ...p, [cat]: !isOpen }))} className="flex w-full items-center justify-between">
                <span className="flex items-center gap-2.5 text-sm font-semibold text-slate-200">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: accent, boxShadow: `0 0 8px ${accent}` }} />
                  {catLabel(cat)}
                  <span className="text-xs font-normal text-slate-500">{grouped[cat].length}</span>
                </span>
                <ChevronDown size={17} className={cx("text-slate-500 transition-transform", isOpen && "rotate-180")} />
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28 }} className="overflow-hidden">
                    <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                      {grouped[cat].map((a, i) => (
                        <AnalysisCard key={a.id} analysis={a} accent={accent} activeRun={latestRunFor(a.id)} onOpen={setOpenRunId} index={i} />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </GlassCard>
          );
        })}
      </div>

      {runs.length > 0 && (
        <GlassCard className="mt-4">
          <h3 className="mb-2.5 text-sm font-semibold text-slate-300">Son Çalıştırmalar</h3>
          <div className="space-y-1">
            {runs.slice(0, 8).map((r) => (
              <button key={r.run_id} onClick={() => setOpenRunId(r.run_id)} className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-xs transition hover:bg-white/[0.04]">
                <span className="truncate text-slate-300">{r.analysis_name}</span>
                <span className="ml-3 flex shrink-0 items-center gap-3 text-slate-500">
                  <StatusBadge status={r.status} />
                  {timeAgo(r.started_at)}
                </span>
              </button>
            ))}
          </div>
        </GlassCard>
      )}

      <AnimatePresence>{openRunId && <RunDrawer runId={openRunId} analyses={analyses} onClose={() => setOpenRunId(null)} />}</AnimatePresence>
    </Section>
  );
}
