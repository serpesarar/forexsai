"use client";

/**
 * Hata Analizi Çalıştırıcı — kataloğdaki analiz araçlarını tek tıkla koşturur,
 * canlı çıktıyı gösterir ve "Öğret" ile çıktıyı derse damıtıp motorlara enjekte eder.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Ban,
  BrainCog,
  CheckCircle2,
  ChevronDown,
  Loader2,
  Play,
  Sparkles,
  Terminal,
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
import { Badge, Card, EmptyState, PulseDot, Section, catLabel, timeAgo } from "./ui";

const LEARN_TARGET_LABELS: Record<string, string> = {
  bias_debate: "Ajan Tartışması (CIO)",
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

function StatusBadge({ status }: { status: RunMeta["status"] }) {
  if (status === "running")
    return (
      <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400">
        <PulseDot /> çalışıyor
      </span>
    );
  if (status === "done")
    return (
      <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
        <CheckCircle2 size={12} /> bitti
      </span>
    );
  if (status === "timeout")
    return (
      <span className="flex items-center gap-1 text-[11px] font-medium text-amber-400">
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
    <span className="flex items-center gap-1 text-[11px] font-medium text-rose-400">
      <XCircle size={12} /> hata
    </span>
  );
}

function AnalysisCard({
  analysis,
  activeRun,
  onOpen,
}: {
  analysis: Analysis;
  activeRun: RunMeta | undefined;
  onOpen: (runId: string) => void;
}) {
  const startRun = useStartRun();
  const disabled = analysis.runnable_here === false;
  const running = activeRun?.status === "running";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`rounded-xl border p-3 transition-colors ${
        running
          ? "border-emerald-500/40 bg-emerald-500/5"
          : "border-slate-800 bg-[#0d1420] hover:border-slate-600"
      } ${disabled ? "opacity-55" : ""}`}
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <h4 className="text-[13px] font-semibold leading-snug text-slate-200">{analysis.name}</h4>
        {running ? (
          <button
            onClick={() => activeRun && onOpen(activeRun.run_id)}
            className="shrink-0 rounded-lg bg-emerald-500/15 p-1.5 text-emerald-400"
            title="Çıktıyı izle"
          >
            <Loader2 size={14} className="animate-spin" />
          </button>
        ) : disabled ? (
          <span className="shrink-0 rounded-lg bg-slate-700/40 p-1.5 text-slate-500" title={analysis.run_note}>
            <Ban size={14} />
          </span>
        ) : (
          <button
            onClick={() =>
              startRun.mutate(
                { analysisId: analysis.id },
                { onSuccess: (run) => onOpen(run.run_id) }
              )
            }
            disabled={startRun.isPending}
            className="shrink-0 rounded-lg bg-[#4F8CFF]/15 p-1.5 text-[#4F8CFF] transition hover:bg-[#4F8CFF]/30 disabled:opacity-50"
            title="Çalıştır"
          >
            <Play size={14} />
          </button>
        )}
      </div>
      <p className="mb-2 text-[11px] leading-relaxed text-slate-400">{analysis.what_it_does}</p>
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone="slate">{analysis.est_runtime === "seconds" ? "saniyeler" : analysis.est_runtime === "minutes" ? "dakikalar" : "uzun"}</Badge>
        {analysis.kind === "endpoint" && <Badge tone="blue">API</Badge>}
        {(analysis.learn_targets?.length ?? 0) > 0 && (
          <Badge tone="purple">
            <Sparkles size={10} className="mr-1" /> öğretilebilir
          </Badge>
        )}
        {disabled && <Badge tone="amber">MT5 kutusu</Badge>}
        {startRun.isError && <Badge tone="red">{(startRun.error as Error).message}</Badge>}
      </div>
    </motion.div>
  );
}

/** Çıktı + Öğret çekmecesi. */
function RunDrawer({ runId, analyses, onClose }: { runId: string; analyses: Analysis[]; onClose: () => void }) {
  const { data: run } = useRunDetail(runId);
  const learn = useLearnFromRun();
  const analysis = analyses.find((a) => a.id === run?.analysis_id);
  const [targets, setTargets] = useState<string[]>(["panel"]);
  const [targetsSeeded, setTargetsSeeded] = useState(false);
  const outputRef = useRef<HTMLPreElement>(null);

  // run verisi sonradan gelir; analiz çözülünce learn_targets'ı BİR KEZ uygula
  // (kullanıcı seçimini ezmemek için sonraki güncellemelerde dokunma)
  useEffect(() => {
    if (!targetsSeeded && analysis) {
      if (analysis.learn_targets?.length) setTargets(analysis.learn_targets);
      setTargetsSeeded(true);
    }
  }, [analysis, targetsSeeded]);

  // Canlı log takibi: run koşarken yeni çıktı geldikçe en alta kaydır
  useEffect(() => {
    if (run?.status === "running" && outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [run?.output, run?.status]);

  const toggleTarget = (t: string) =>
    setTargets((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 backdrop-blur-sm sm:items-center"
      onClick={onClose}
    >
      <motion.div
        initial={{ y: 60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 60, opacity: 0 }}
        transition={{ type: "spring", damping: 26, stiffness: 300 }}
        className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-slate-700 bg-[#0d1420] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-[#4F8CFF]" />
            <span className="text-sm font-semibold text-slate-200">{run?.analysis_name ?? "…"}</span>
            {run && <StatusBadge status={run.status} />}
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <XCircle size={18} />
          </button>
        </div>

        <pre ref={outputRef} className="flex-1 overflow-auto whitespace-pre-wrap px-4 py-3 font-mono text-[11px] leading-relaxed text-slate-300">
          {run?.output?.trim() || (run?.status === "running" ? "Çıktı bekleniyor…" : "(çıktı yok)")}
        </pre>

        {/* Öğret bölümü */}
        <div className="border-t border-slate-800 px-4 py-3">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="flex items-center gap-1 text-xs font-semibold text-slate-300">
              <BrainCog size={14} className="text-violet-400" /> Öğret →
            </span>
            {Object.entries(LEARN_TARGET_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggleTarget(key)}
                className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition ${
                  targets.includes(key)
                    ? "bg-violet-500/25 text-violet-300 ring-1 ring-violet-500/50"
                    : "bg-slate-800 text-slate-400 hover:text-slate-300"
                }`}
              >
                {label}
              </button>
            ))}
            <button
              onClick={() => run && learn.mutate({ runId: run.run_id, targets })}
              disabled={!run || run.status === "running" || learn.isPending || targets.length === 0}
              className="ml-auto flex items-center gap-1.5 rounded-lg bg-violet-500/20 px-3 py-1.5 text-xs font-semibold text-violet-300 transition hover:bg-violet-500/35 disabled:opacity-40"
            >
              {learn.isPending ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {learn.isPending ? "Damıtılıyor…" : "Derse Damıt & Enjekte Et"}
            </button>
          </div>
          {learn.isSuccess && (
            <p className="text-[11px] text-emerald-400">
              ✓ Ders kaydedildi: “{learn.data.title}” — seçilen motorlar bir sonraki
              çalışmalarında bu dersi görecek.
            </p>
          )}
          {learn.isError && (
            <p className="text-[11px] text-rose-400">{(learn.error as Error).message}</p>
          )}
          <p className="mt-1 text-[10px] text-slate-500">
            Çıktı LLM ile 5 cümlelik eyleme dönük derse çevrilir; Ajan Tartışması CIO
            prompt'una ve Claude Decider LESSONS.md'ye otomatik enjekte edilir.
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

  const analyses = useMemo(() => analysesData?.analyses ?? [], [analysesData]);
  const runs = runsData?.runs ?? [];

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return analyses;
    return analyses.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.what_it_does.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q)
    );
  }, [analyses, search]);

  const grouped = useMemo(() => {
    const g: Record<string, Analysis[]> = {};
    for (const a of filtered) (g[a.category] ??= []).push(a);
    return g;
  }, [filtered]);

  // Sabit sıra + katalogda çıkabilecek yeni kategoriler (sessizce gizlenmesin)
  const orderedCats = useMemo(() => {
    const extras = Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c));
    return [...CATEGORY_ORDER, ...extras].filter((c) => grouped[c]?.length);
  }, [grouped]);

  const latestRunFor = (analysisId: string): RunMeta | undefined =>
    runs.find((r) => r.analysis_id === analysisId);

  const searching = search.trim().length > 0;

  return (
    <Section
      id="analiz"
      title="Hata Analizi & Geliştirme Araçları"
      icon={<Terminal size={18} />}
      subtitle="Tek tıkla çalıştır → çıktıyı gör → Öğret ile motorlara enjekte et"
    >
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={`${analyses.length} araç içinde ara… (isim / ne yaptığı)`}
        className="mb-4 w-full rounded-xl border border-slate-800 bg-[#0d1420] px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-[#4F8CFF] focus:outline-none"
      />
      {isLoading && <EmptyState text="Katalog yükleniyor…" />}
      {!isLoading && searching && filtered.length === 0 && (
        <EmptyState text={`"${search}" ile eşleşen araç yok.`} />
      )}
      <div className="space-y-4">
        {orderedCats.map((cat) => {
          // Arama varken tüm eşleşen kategorileri aç — sonuç görünmez kalmasın
          const isOpen = searching ? true : (expanded[cat] ?? false);
          return (
            <Card key={cat}>
              <button
                onClick={() => setExpanded((p) => ({ ...p, [cat]: !isOpen }))}
                className="flex w-full items-center justify-between"
              >
                <span className="text-sm font-semibold text-slate-300">
                  {catLabel(cat)}{" "}
                  <span className="text-xs font-normal text-slate-500">({grouped[cat].length})</span>
                </span>
                <ChevronDown
                  size={16}
                  className={`text-slate-500 transition-transform ${isOpen ? "rotate-180" : ""}`}
                />
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                      {grouped[cat].map((a) => (
                        <AnalysisCard
                          key={a.id}
                          analysis={a}
                          activeRun={latestRunFor(a.id)}
                          onOpen={setOpenRunId}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
      </div>

      {/* Son çalıştırmalar */}
      {runs.length > 0 && (
        <Card className="mt-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">Son Çalıştırmalar</h3>
          <div className="space-y-1.5">
            {runs.slice(0, 8).map((r) => (
              <button
                key={r.run_id}
                onClick={() => setOpenRunId(r.run_id)}
                className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-left text-xs hover:bg-slate-800/60"
              >
                <span className="truncate text-slate-300">{r.analysis_name}</span>
                <span className="ml-3 flex shrink-0 items-center gap-3 text-slate-500">
                  <StatusBadge status={r.status} />
                  {timeAgo(r.started_at)}
                </span>
              </button>
            ))}
          </div>
        </Card>
      )}

      <AnimatePresence>
        {openRunId && (
          <RunDrawer runId={openRunId} analyses={analyses} onClose={() => setOpenRunId(null)} />
        )}
      </AnimatePresence>
    </Section>
  );
}
