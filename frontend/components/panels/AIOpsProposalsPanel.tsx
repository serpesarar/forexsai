"use client";
/**
 * AI-Ops Proposals Panel
 *
 * Lists DeepSeek-generated improvement proposals from the AI-ops orchestrator.
 * User can: view details, approve (optionally creating a GitHub issue), reject,
 * and manually trigger a fresh orchestration cycle.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  aiOps, type Proposal, type Severity, type ProposalStatus, type SimulatedMetric,
  type TpSlRecommendation, type DiscriminatorAnalysis, type AutoDecision,
} from "../../lib/api/aiOps";

const SEVERITY_COLOR: Record<Severity, { bg: string; border: string; text: string; emoji: string }> = {
  critical: { bg: "rgba(239,68,68,0.10)", border: "#EF4444", text: "#FCA5A5", emoji: "🔴" },
  high:     { bg: "rgba(249,115,22,0.10)", border: "#F97316", text: "#FDBA74", emoji: "🟠" },
  medium:   { bg: "rgba(234,179,8,0.10)",  border: "#EAB308", text: "#FDE68A", emoji: "🟡" },
  low:      { bg: "rgba(34,197,94,0.10)",  border: "#22C55E", text: "#86EFAC", emoji: "🟢" },
};

const STATUS_LABEL: Record<ProposalStatus, string> = {
  pending: "Bekliyor",
  reviewed: "İncelendi",
  approved: "Onaylandı",
  rejected: "Reddedildi",
  implemented: "Uygulandı",
  rolled_back: "Geri Alındı",
};

export default function AIOpsProposalsPanel() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState<ProposalStatus | "all">("pending");
  const [autoDecisionFilter, setAutoDecisionFilter] = useState<AutoDecision | "all">("all");
  const [symbolFilter, setSymbolFilter] = useState<string>("all");
  const [minSampleSize, setMinSampleSize] = useState<number>(0);
  const [expanded, setExpanded] = useState<string | null>(null);

  const stats = useQuery({ queryKey: ["ai-ops-stats"], queryFn: () => aiOps.stats(), refetchInterval: 60000 });
  const miningStatus = useQuery({
    queryKey: ["ai-ops-mining-status"],
    queryFn: () => aiOps.miningStatus(),
    refetchInterval: 120000,
  });
  const triggerMine = useMutation({
    mutationFn: () => aiOps.triggerMining(60),
    onSuccess: () => alert("Pattern mining tetiklendi — 1-3 dakika içinde yeni kurallar yüklenecek."),
    onError: (e: any) => alert(`Tetiklenemedi: ${e?.message ?? "bilinmiyor"}`),
  });
  const proposals = useQuery({
    queryKey: ["ai-ops-proposals", filter, symbolFilter, autoDecisionFilter],
    queryFn: () => aiOps.listProposals({
      ...(filter === "all" ? {} : { status: filter }),
      ...(symbolFilter !== "all" ? { symbol: symbolFilter } : {}),
      ...(autoDecisionFilter !== "all" ? { auto_decision: autoDecisionFilter } : {}),
      limit: 100,
    }),
    refetchInterval: 60000,
  });
  const triageStats = useQuery({
    queryKey: ["ai-ops-auto-triage-stats"],
    queryFn: () => aiOps.autoTriageStats(),
    refetchInterval: 60000,
  });
  const triageRun = useMutation({
    mutationFn: () => aiOps.autoTriageRun(500),
    onSuccess: () => alert("Auto-triage tetiklendi — 1-3 dakika içinde sonuçlar dolar."),
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => aiOps.approve(id, { create_github_issue: true, reviewer: "user" }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["ai-ops-proposals"] });
      qc.invalidateQueries({ queryKey: ["ai-ops-stats"] });
      if (data.issue_url) {
        window.open(data.issue_url, "_blank");
      } else if (data.github_error) {
        const e = data.github_error;
        const reasonHint: Record<string, string> = {
          no_token: "Railway dashboard → Variables → GITHUB_TOKEN ekle, Redeploy bas.",
          token_invalid_or_expired: "Token geçersiz veya süresi dolmuş — yenile.",
          token_lacks_issues_write_permission:
            "Token'da 'Issues: Read & Write' izni yok. Fine-grained PAT'a bu repo + Issues yetkisi ver.",
          repo_not_found_or_token_no_access:
            `Repo "${e.repo}" bulunamadı veya token bu repo'ya erişemiyor. GITHUB_REPO env var yanlış olabilir.`,
          github_validation_error: "GitHub validation hatası — issue title/body sorunlu.",
          network_error: "GitHub'a bağlanılamadı.",
        };
        const hint = reasonHint[e.reason] ?? "";
        alert(
          `Onaylandı, ama GitHub issue açılamadı.\n\n` +
          `Sebep: ${e.reason}\n` +
          `Detay: ${e.detail}\n` +
          (e.token_source ? `Token bulundu (${e.token_source}) ama API çağrısı reddedildi.\n` : "Token hiç bulunamadı.\n") +
          `\nÇözüm: ${hint}`
        );
      } else {
        alert("Onaylandı. (GitHub issue açılmadı, sebep bilinmiyor)");
      }
    },
    onError: (e: any) => alert(`Onay başarısız: ${e?.message ?? "bilinmiyor"}`),
  });

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      aiOps.reject(id, { reason, reviewer: "user" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-ops-proposals"] });
      qc.invalidateQueries({ queryKey: ["ai-ops-stats"] });
    },
    onError: (e: any) => alert(`Reddetme başarısız: ${e?.message ?? "bilinmiyor"}`),
  });

  const runMut = useMutation({
    mutationFn: () => aiOps.manualRun(7),
    onSuccess: () => alert("Orchestration tetiklendi — 1-3 dakika içinde yeni öneriler görünür."),
    onError: (e: any) => alert(`Tetiklenemedi: ${e?.message ?? "bilinmiyor"}`),
  });

  const allList = proposals.data?.proposals ?? [];
  const list = minSampleSize > 0
    ? allList.filter((p: Proposal) => {
        const sample = (p.simulated_metric?.original?.n_signals ?? 0)
                     || (p.pre_change_metric?.sample_size ?? 0);
        return sample >= minSampleSize;
      })
    : allList;

  return (
    <div style={{
      background: "#0B0F17", color: "#E5E7EB", padding: 20, borderRadius: 12,
      fontFamily: "'Inter', -apple-system, sans-serif", minHeight: "100vh",
    }}>
      {/* Header + stats */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>🤖 AI-Ops İyileştirme Önerileri</h1>
          <p style={{ fontSize: 13, color: "#9CA3AF", margin: "4px 0 0 0" }}>
            DeepSeek tarafından üretilen öneriler · İnsan onayı zorunlu · Otomatik kod değişikliği yok
          </p>
        </div>
        <button
          onClick={() => runMut.mutate()}
          disabled={runMut.isPending}
          style={{
            background: "#4F8CFF", color: "#fff", border: "none", padding: "10px 16px",
            borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 13,
            opacity: runMut.isPending ? 0.5 : 1,
          }}
        >
          {runMut.isPending ? "Tetikleniyor..." : "Manuel Çalıştır (7g pencere)"}
        </button>
      </div>

      {/* Pattern mining status — self-feeding indicator */}
      <PatternMiningStatusBadge
        status={miningStatus.data}
        onTrigger={() => triggerMine.mutate()}
        triggering={triggerMine.isPending}
      />

      {/* TP/SL Optimizer Section */}
      <TpSlOptimizerSection />

      {/* Stats row */}
      {stats.data?.available && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                      gap: 12, marginBottom: 20 }}>
          {(Object.keys(SEVERITY_COLOR) as Severity[]).map((sev) => {
            const c = SEVERITY_COLOR[sev];
            const count = stats.data?.by_severity?.[sev] ?? 0;
            return (
              <div key={sev} style={{
                background: c.bg, borderLeft: `3px solid ${c.border}`,
                padding: "12px 14px", borderRadius: 8,
              }}>
                <div style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: 0.5 }}>
                  {c.emoji} {sev}
                </div>
                <div style={{ fontSize: 22, fontWeight: 700, color: c.text }}>{count}</div>
              </div>
            );
          })}
          <div style={{ background: "#141C2B", padding: "12px 14px", borderRadius: 8 }}>
            <div style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: 0.5 }}>
              Toplam Cluster
            </div>
            <div style={{ fontSize: 22, fontWeight: 700, color: "#E5E7EB" }}>
              {stats.data?.clusters_total ?? 0}
            </div>
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        {(["pending", "approved", "rejected", "implemented", "all"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              background: filter === s ? "#4F8CFF" : "transparent",
              color: filter === s ? "#fff" : "#9CA3AF",
              border: `1px solid ${filter === s ? "#4F8CFF" : "#1F2937"}`,
              padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontSize: 12,
              textTransform: "capitalize",
            }}
          >
            {s === "all" ? "Tümü" : STATUS_LABEL[s as ProposalStatus]}
            {stats.data?.by_status?.[s] ? ` (${stats.data.by_status[s]})` : ""}
          </button>
        ))}
      </div>

      {/* Auto-triage filter row */}
      <div style={{ marginBottom: 12, padding: "10px 14px", background: "#0F1623",
                    borderRadius: 8, border: "1px solid #1F2937" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <div>
            <div style={{ fontSize: 11, color: "#6B7280", textTransform: "uppercase",
                          letterSpacing: 0.5 }}>
              🤖 Auto-Triage (sistemin otomatik sınıflandırması)
            </div>
            <div style={{ fontSize: 11, color: "#9CA3AF", marginTop: 2 }}>
              Sistem objektif kriterlerle her öneriyi: ✅ auto_apply (PR aday), 👁 human_review (sen bak), ❌ auto_reject (zaten kapatıldı).
            </div>
          </div>
          <button
            onClick={() => triageRun.mutate()}
            disabled={triageRun.isPending}
            style={{
              background: "#A855F7", color: "#fff", border: "none",
              padding: "5px 10px", borderRadius: 4, cursor: "pointer", fontSize: 11,
              opacity: triageRun.isPending ? 0.5 : 1, whiteSpace: "nowrap",
            }}
          >
            {triageRun.isPending ? "..." : "Şimdi Triage Et"}
          </button>
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {([
            ["all", "Tüm Auto", "#374151", null],
            ["auto_apply", "✅ Auto-Apply", "#22C55E", "auto_apply"],
            ["human_review", "👁 Human Review", "#EAB308", "human_review"],
            ["auto_reject", "❌ Auto-Reject", "#EF4444", "auto_reject"],
          ] as const).map(([key, label, color, statsKey]) => {
            const count = statsKey != null ? (triageStats.data?.counts?.[statsKey] ?? 0) : null;
            const active = autoDecisionFilter === key;
            return (
              <button
                key={key}
                onClick={() => setAutoDecisionFilter(key as any)}
                style={{
                  background: active ? color : "transparent",
                  color: active ? "#fff" : "#9CA3AF",
                  border: `1px solid ${active ? color : "#1F2937"}`,
                  padding: "5px 10px", borderRadius: 4, cursor: "pointer", fontSize: 11,
                  fontWeight: active ? 600 : 400,
                }}
              >
                {label}{count != null ? ` (${count})` : ""}
              </button>
            );
          })}
          {triageStats.data?.counts?.untriaged ? (
            <span style={{ fontSize: 11, color: "#9CA3AF", marginLeft: 8, alignSelf: "center" }}>
              · {triageStats.data.counts.untriaged} henüz triaged değil
            </span>
          ) : null}
        </div>
      </div>

      {/* Symbol + sample-size filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, color: "#6B7280", textTransform: "uppercase",
                       letterSpacing: 0.5 }}>Sembol:</span>
        {(["all", "XAUUSD", "NDX.INDX", "GDAXI.INDX", "USOIL.FOREX"] as const).map(sym => (
          <button
            key={sym}
            onClick={() => setSymbolFilter(sym)}
            style={{
              background: symbolFilter === sym ? "#16C784" : "transparent",
              color: symbolFilter === sym ? "#000" : "#9CA3AF",
              border: `1px solid ${symbolFilter === sym ? "#16C784" : "#1F2937"}`,
              padding: "5px 10px", borderRadius: 4, cursor: "pointer", fontSize: 11,
              fontWeight: symbolFilter === sym ? 600 : 400,
            }}
          >
            {sym === "all" ? "Tümü"
             : sym === "XAUUSD" ? "XAUUSD (Altın)"
             : sym === "NDX.INDX" ? "NDX (Nasdaq)"
             : sym === "GDAXI.INDX" ? "DAX"
             : "OIL"}
          </button>
        ))}
        <span style={{ fontSize: 11, color: "#6B7280", marginLeft: 14,
                       textTransform: "uppercase", letterSpacing: 0.5 }}>Min sample:</span>
        {[0, 10, 20, 50].map(n => (
          <button
            key={n}
            onClick={() => setMinSampleSize(n)}
            style={{
              background: minSampleSize === n ? "#A855F7" : "transparent",
              color: minSampleSize === n ? "#fff" : "#9CA3AF",
              border: `1px solid ${minSampleSize === n ? "#A855F7" : "#1F2937"}`,
              padding: "5px 10px", borderRadius: 4, cursor: "pointer", fontSize: 11,
            }}
          >
            {n === 0 ? "All" : `≥${n}`}
          </button>
        ))}
        <span style={{ fontSize: 11, color: "#6B7280", marginLeft: "auto" }}>
          {list.length} / {allList.length} öneri gösteriliyor
        </span>
      </div>

      {/* Loading / empty */}
      {proposals.isLoading && <div style={{ color: "#9CA3AF" }}>Yükleniyor...</div>}
      {proposals.isError && (
        <div style={{ color: "#EF4444" }}>
          Öneri listesi alınamadı: {(proposals.error as Error)?.message}
        </div>
      )}
      {proposals.data && list.length === 0 && (
        <div style={{
          padding: 40, textAlign: "center", color: "#6B7280",
          background: "#141C2B", borderRadius: 12,
        }}>
          Bu filtrede öneri yok. {filter === "pending" && "Sistemin failure cluster üretmesi için en az 5+ benzer fail bekleniyor."}
        </div>
      )}

      {/* Proposal cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {list.map((p) => (
          <ProposalCard
            key={p.id}
            proposal={p}
            expanded={expanded === p.id}
            onToggle={() => setExpanded(expanded === p.id ? null : p.id)}
            onApprove={() => approveMut.mutate(p.id)}
            onReject={(reason) => rejectMut.mutate({ id: p.id, reason })}
            isWorking={approveMut.isPending || rejectMut.isPending}
          />
        ))}
      </div>
    </div>
  );
}

function TpSlOptimizerSection() {
  const qc = useQueryClient();
  const [showAll, setShowAll] = useState(false);
  const list = useQuery({
    queryKey: ["tp-sl-list", showAll],
    queryFn: () => aiOps.tpSlList({ status: showAll ? undefined : "pending", limit: 60 }),
    refetchInterval: 120000,
  });
  const runMut = useMutation({
    mutationFn: () => aiOps.tpSlRun(60),
    onSuccess: () => alert("TP/SL analizi tetiklendi — ~1 dk içinde sonuçlar görünür."),
  });
  const applyMut = useMutation({
    mutationFn: (id: string) => aiOps.tpSlApply(id, { reviewer: "user" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tp-sl-list"] }),
  });
  const rejectMut = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      aiOps.tpSlReject(id, { reason, reviewer: "user" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tp-sl-list"] }),
  });

  const recs = list.data?.recommendations ?? [];
  // Filter to material recommendations (severity != none) for default view
  const visible = showAll ? recs : recs.filter(r => r.severity !== "none");

  return (
    <div style={{
      marginBottom: 16, padding: 14, background: "#0F1623",
      borderRadius: 8, border: "1px solid #1F2937",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: "#6B7280", textTransform: "uppercase", letterSpacing: 0.5 }}>
            🎯 TP/SL Optimizasyon Önerileri
          </div>
          <div style={{ fontSize: 13, color: "#E5E7EB", marginTop: 4 }}>
            Modellerin geçmiş MFE/MAE dağılımına göre **optimal TP/SL** çiftleri.
            {visible.length > 0 ? ` ${visible.length} öneri.` : " Henüz pending öneri yok."}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setShowAll(!showAll)}
            style={{
              background: "transparent", color: "#9CA3AF",
              border: "1px solid #374151", padding: "6px 10px",
              borderRadius: 4, cursor: "pointer", fontSize: 11,
            }}
          >
            {showAll ? "Sadece Aksiyonlu" : "Tümünü Göster"}
          </button>
          <button
            onClick={() => runMut.mutate()}
            disabled={runMut.isPending}
            style={{
              background: "#4F8CFF", color: "#fff", border: "none",
              padding: "6px 12px", borderRadius: 4, cursor: "pointer", fontSize: 11,
              opacity: runMut.isPending ? 0.5 : 1,
            }}
          >
            {runMut.isPending ? "..." : "Şimdi Analiz Et"}
          </button>
        </div>
      </div>

      {visible.length === 0 ? (
        <div style={{ padding: 20, textAlign: "center", color: "#6B7280", fontSize: 12 }}>
          {list.isLoading ? "Yükleniyor..." :
            "Aksiyonlu öneri yok. Sistem yeterli sample biriktirdiğinde optimal TP/SL'leri burada gösterir."}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {visible.map(r => (
            <TpSlRecCard
              key={r.id}
              rec={r}
              onApply={() => applyMut.mutate(r.id)}
              onReject={() => {
                const reason = prompt("Reddetme nedeni:") || "";
                rejectMut.mutate({ id: r.id, reason });
              }}
              isWorking={applyMut.isPending || rejectMut.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TpSlRecCard({ rec, onApply, onReject, isWorking }: {
  rec: TpSlRecommendation;
  onApply: () => void;
  onReject: () => void;
  isWorking: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const sevColor: Record<string, string> = {
    critical: "#EF4444", high: "#F97316", medium: "#EAB308",
    low: "#22C55E", none: "#6B7280",
  };
  const accent = sevColor[rec.severity] ?? "#6B7280";
  const tpChange = rec.recommended_tp_pips - (rec.current_tp_pips ?? 0);
  const slChange = rec.recommended_sl_pips - (rec.current_sl_pips ?? 0);
  const pnlDelta = rec.expected_pnl_delta_pips ?? 0;
  const dirIcon = rec.direction === "BUY" ? "🔺" : rec.direction === "SELL" ? "🔻" : "↕";

  return (
    <div style={{
      background: "#141C2B", borderRadius: 6,
      border: `1px solid ${accent}33`, borderLeft: `3px solid ${accent}`,
      overflow: "hidden",
    }}>
      <div onClick={() => setExpanded(!expanded)} style={{
        cursor: "pointer", padding: "10px 14px",
        display: "grid",
        gridTemplateColumns: "auto 1fr auto auto auto auto",
        gap: 12, alignItems: "center", fontSize: 12,
      }}>
        <span style={{
          padding: "2px 8px", borderRadius: 3, fontSize: 9, fontWeight: 700,
          background: accent + "22", color: accent, textTransform: "uppercase",
        }}>
          {rec.severity}
        </span>
        <span style={{ color: "#E5E7EB", fontWeight: 500 }}>
          {rec.symbol} {dirIcon} <span style={{ color: "#6B7280" }}>{rec.direction ?? "BOTH"}</span>
        </span>
        <span style={{ fontFamily: "monospace", color: "#9CA3AF" }}>
          TP: <span style={{ color: "#FCA5A5" }}>{rec.current_tp_pips ?? "—"}</span> →{" "}
          <span style={{ color: "#86EFAC" }}>{rec.recommended_tp_pips}</span>
          {tpChange !== 0 && (
            <span style={{ marginLeft: 4, color: tpChange > 0 ? "#86EFAC" : "#FCA5A5" }}>
              ({tpChange > 0 ? "+" : ""}{tpChange.toFixed(0)})
            </span>
          )}
        </span>
        <span style={{ fontFamily: "monospace", color: "#9CA3AF" }}>
          SL: <span style={{ color: "#FCA5A5" }}>{rec.current_sl_pips ?? "—"}</span> →{" "}
          <span style={{ color: "#86EFAC" }}>{rec.recommended_sl_pips}</span>
          {slChange !== 0 && (
            <span style={{ marginLeft: 4, color: slChange < 0 ? "#86EFAC" : "#FCA5A5" }}>
              ({slChange > 0 ? "+" : ""}{slChange.toFixed(0)})
            </span>
          )}
        </span>
        <span style={{ color: pnlDelta > 0 ? "#86EFAC" : "#FCA5A5", fontWeight: 600 }}>
          {pnlDelta > 0 ? "+" : ""}{pnlDelta.toFixed(0)} pips
        </span>
        <span style={{ color: "#6B7280", fontSize: 10 }}>n={rec.sample_size}</span>
      </div>

      {expanded && (
        <div style={{ padding: "10px 14px 14px", borderTop: "1px solid #1F2937", fontSize: 11 }}>
          {rec.reasoning && (
            <div style={{ marginBottom: 10, color: "#D1D5DB", lineHeight: 1.6 }}>
              💬 {rec.reasoning}
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 10 }}>
            <DistBlock title="MFE Dağılımı" stats={rec.mfe_distribution} positive />
            <DistBlock title="MAE Dağılımı" stats={rec.mae_distribution} positive={false} />
          </div>
          {rec.per_tp_level_simulated && rec.per_tp_level_simulated.length > 0 && (
            <>
              <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase",
                            marginBottom: 4, marginTop: 8 }}>
                🪜 Mevcut TP Ladder — Her seviye için simülasyon
              </div>
              <div style={{ background: "#0B0F17", padding: 6, borderRadius: 4, marginBottom: 8 }}>
                {rec.per_tp_level_simulated.map((lvl) => (
                  <div key={lvl.name} style={{
                    display: "flex", justifyContent: "space-between", padding: "3px 0",
                    fontFamily: "monospace", fontSize: 11, color: "#D1D5DB",
                  }}>
                    <span>
                      <span style={{ color: "#9CA3AF" }}>{lvl.name}</span>
                      {" "}TP={lvl.tp_pips} SL={lvl.sl_pips}
                    </span>
                    <span>
                      <span style={{ color: "#86EFAC" }}>{lvl.wins}W</span>
                      {" / "}
                      <span style={{ color: "#FCA5A5" }}>{lvl.losses}L</span>
                      {" / "}
                      <span style={{ color: "#9CA3AF" }}>{lvl.timeouts}T</span>
                      {" · "}WR {lvl.win_rate ?? "—"}%
                      {" · net "}
                      <span style={{ color: lvl.net_pnl > 0 ? "#86EFAC" : "#FCA5A5", fontWeight: 600 }}>
                        {lvl.net_pnl > 0 ? "+" : ""}{lvl.net_pnl.toFixed(1)}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
          {rec.grid_top5 && rec.grid_top5.length > 0 && (
            <>
              <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase",
                            marginBottom: 4, marginTop: 8 }}>
                🏆 Grid Search Top 5
                {rec.grid_dim && (
                  <span style={{ marginLeft: 6, textTransform: "none", color: "#4B5563", fontWeight: 400 }}>
                    ({rec.grid_dim.tp_candidates}×{rec.grid_dim.sl_candidates} grid;
                    {" "}TP {rec.grid_dim.tp_range?.[0]}–{rec.grid_dim.tp_range?.[1]},
                    {" "}SL {rec.grid_dim.sl_range?.[0]}–{rec.grid_dim.sl_range?.[1]})
                  </span>
                )}
              </div>
              <div style={{ background: "#0B0F17", padding: 6, borderRadius: 4 }}>
                {rec.grid_top5.map((g, i) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between", padding: "3px 0",
                    fontFamily: "monospace", fontSize: 11,
                    color: i === 0 ? "#86EFAC" : "#9CA3AF",
                  }}>
                    <span>#{i + 1} TP={g.tp} SL={g.sl} R/R={g.rr_ratio ?? "—"}</span>
                    <span>net={g.net_pnl > 0 ? "+" : ""}{g.net_pnl} pips · WR {g.win_rate ?? "—"}%</span>
                  </div>
                ))}
              </div>
            </>
          )}
          {rec.status === "pending" && (
            <div style={{ display: "flex", gap: 8, marginTop: 12, paddingTop: 10,
                          borderTop: "1px solid #1F2937" }}>
              <button
                disabled={isWorking}
                onClick={onApply}
                style={{
                  background: "#22C55E", color: "#000", border: "none",
                  padding: "6px 14px", borderRadius: 4, cursor: "pointer", fontSize: 11, fontWeight: 600,
                  opacity: isWorking ? 0.5 : 1,
                }}
              >
                ✓ Uyguladım (target_config.py'i güncelledim)
              </button>
              <button
                disabled={isWorking}
                onClick={onReject}
                style={{
                  background: "transparent", color: "#FCA5A5",
                  border: "1px solid #7F1D1D", padding: "6px 14px",
                  borderRadius: 4, cursor: "pointer", fontSize: 11,
                }}
              >
                ✗ Reddet
              </button>
            </div>
          )}
          {rec.status !== "pending" && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid #1F2937",
                          fontSize: 11, color: "#6B7280" }}>
              Status: <b style={{ color: "#9CA3AF" }}>{rec.status}</b>
              {rec.applied_at && ` · Uygulandı: ${new Date(rec.applied_at).toLocaleString("tr-TR")}`}
              {rec.reviewed_at && ` · İnceleme: ${new Date(rec.reviewed_at).toLocaleString("tr-TR")}`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DistBlock({ title, stats, positive }: {
  title: string; stats: Record<string, number>; positive: boolean;
}) {
  const color = positive ? "#86EFAC" : "#FCA5A5";
  const keys = ["p25", "p50", "p70", "p80", "p90", "p95"];
  return (
    <div style={{ background: "#0B0F17", padding: 8, borderRadius: 4 }}>
      <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase", marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 4, fontSize: 11 }}>
        {keys.map(k => (
          <div key={k} style={{ color: "#9CA3AF" }}>
            {k}: <span style={{ color, fontFamily: "monospace" }}>
              {stats?.[k] != null ? stats[k].toFixed(0) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}


function PatternMiningStatusBadge({
  status, onTrigger, triggering,
}: { status: any; onTrigger: () => void; triggering: boolean }) {
  if (!status) return null;
  const latest = status.latest_run;
  const generatedAt = latest?.generated_at || status.local_generated_at;
  const rulesCount = latest?.rules_count ?? status.local_rules_count ?? 0;
  let ageText = "henüz koşmadı";
  let ageColor = "#9CA3AF";
  if (generatedAt) {
    const ageHours = (Date.now() - new Date(generatedAt).getTime()) / (1000 * 60 * 60);
    if (ageHours < 24) {
      ageText = `${Math.round(ageHours)}sa önce güncellendi`;
      ageColor = "#22C55E";
    } else if (ageHours < 24 * 7) {
      ageText = `${Math.round(ageHours / 24)}g önce güncellendi`;
      ageColor = "#22C55E";
    } else if (ageHours < 24 * 14) {
      ageText = `${Math.round(ageHours / 24)}g önce güncellendi (yenileme yaklaştı)`;
      ageColor = "#F59E0B";
    } else {
      ageText = `${Math.round(ageHours / 24)}g önce — eski!`;
      ageColor = "#EF4444";
    }
  }
  return (
    <div style={{
      marginBottom: 16, padding: "10px 14px", background: "#0F1623",
      borderRadius: 8, border: "1px solid #1F2937",
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, flex: 1 }}>
        <div>
          <div style={{ fontSize: 11, color: "#6B7280", textTransform: "uppercase",
                        letterSpacing: 0.5 }}>
            🔄 Self-Feeding Pattern Mining
          </div>
          <div style={{ fontSize: 13, color: "#E5E7EB", marginTop: 2 }}>
            <b>{rulesCount}</b> kural aktif · <span style={{ color: ageColor }}>{ageText}</span>
            {latest?.triggered_by && (
              <span style={{ color: "#6B7280", fontSize: 11, marginLeft: 8 }}>
                ({latest.triggered_by === "cron" ? "haftalık otomatik" : "manuel"})
              </span>
            )}
          </div>
        </div>
        {status.recent_runs && status.recent_runs.length > 0 && (
          <div style={{ display: "flex", gap: 4 }}>
            {status.recent_runs.slice(0, 5).reverse().map((r: any) => (
              <div
                key={r.id}
                title={`${new Date(r.generated_at).toLocaleString("tr-TR")} · ${r.rules_count} rules · ${r.triggered_by}`}
                style={{
                  width: 24, height: 4, borderRadius: 2,
                  background: r.triggered_by === "cron" ? "#22C55E" : "#4F8CFF",
                  opacity: 0.7,
                }}
              />
            ))}
          </div>
        )}
      </div>
      <button
        onClick={onTrigger}
        disabled={triggering}
        style={{
          background: "#4F8CFF", color: "#fff", border: "none", padding: "6px 12px",
          borderRadius: 6, cursor: "pointer", fontWeight: 500, fontSize: 11,
          opacity: triggering ? 0.5 : 1,
        }}
      >
        {triggering ? "Çalışıyor..." : "Şimdi Yeniden Mine Et"}
      </button>
    </div>
  );
}


function ProposalCard({
  proposal: p,
  expanded,
  onToggle,
  onApprove,
  onReject,
  isWorking,
}: {
  proposal: Proposal;
  expanded: boolean;
  onToggle: () => void;
  onApprove: () => void;
  onReject: (reason: string) => void;
  isWorking: boolean;
}) {
  const sev = SEVERITY_COLOR[p.severity];
  const fixes = Array.isArray(p.proposed_fixes) ? p.proposed_fixes : [];
  const detail = useQuery({
    queryKey: ["ai-ops-proposal", p.id],
    queryFn: () => aiOps.getProposal(p.id),
    enabled: expanded,
  });

  return (
    <div style={{
      background: "#141C2B", borderRadius: 12, border: `1px solid ${expanded ? sev.border : "#1F2937"}`,
      overflow: "hidden",
    }}>
      {/* Header (clickable) */}
      <div onClick={onToggle} style={{
        cursor: "pointer", padding: "14px 18px",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <div style={{
          background: sev.bg, color: sev.text, padding: "4px 10px",
          borderRadius: 4, fontSize: 11, fontWeight: 700, textTransform: "uppercase",
          border: `1px solid ${sev.border}`,
        }}>
          {sev.emoji} {p.severity}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#E5E7EB" }}>
            {p.symbol} · <span style={{ color: "#9CA3AF" }}>{p.model_type}</span>
            {p.status !== "pending" && (
              <span style={{
                marginLeft: 10, fontSize: 10, padding: "2px 6px", borderRadius: 3,
                background: p.status === "approved" ? "#1E40AF" : p.status === "rejected" ? "#7F1D1D" : "#374151",
                color: "#fff",
              }}>
                {STATUS_LABEL[p.status]}
              </span>
            )}
          </div>
          <div style={{ fontSize: 12, color: "#9CA3AF", marginTop: 2 }}>
            {p.root_cause?.slice(0, 140)}{p.root_cause && p.root_cause.length > 140 ? "..." : ""}
          </div>
        </div>
        <div style={{ fontSize: 11, color: "#6B7280" }}>
          {new Date(p.created_at).toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" })}
        </div>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div style={{ padding: "0 18px 18px 18px", borderTop: "1px solid #1F2937" }}>
          {/* Simulation result — counterfactual replay (TOP PRIORITY DISPLAY) */}
          <SimulationBlock proposal={p} />

          {/* Cluster stats */}
          {detail.data?.cluster && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, margin: "16px 0", fontSize: 12 }}>
              <Stat label="Sample" value={`${detail.data.cluster.sample_size} fails`} />
              <Stat label="Win Rate" value={`${detail.data.cluster.win_rate}%`}
                    color={detail.data.cluster.win_rate < 40 ? "#EF4444" : "#F97316"} />
              <Stat label="P/L Total" value={`${detail.data.cluster.total_pnl_pips} pips`}
                    color={detail.data.cluster.total_pnl_pips < 0 ? "#EF4444" : "#22C55E"} />
              <Stat label="Avg Conf" value={`${detail.data.cluster.avg_confidence}%`} />
            </div>
          )}

          {/* Root cause */}
          <SectionHeader>Root Cause</SectionHeader>
          <p style={{ fontSize: 13, color: "#D1D5DB", lineHeight: 1.6, margin: "8px 0 16px 0" }}>
            {p.root_cause}
          </p>

          {/* Cluster signature */}
          {detail.data?.cluster && (
            <>
              <SectionHeader>Cluster Signature</SectionHeader>
              <code style={{
                display: "block", background: "#0B0F17", padding: 10, borderRadius: 6,
                fontSize: 11, color: "#86EFAC", margin: "8px 0 16px 0",
              }}>
                {detail.data.cluster.cluster_signature}
              </code>
              {detail.data.cluster.common_tags?.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
                  {detail.data.cluster.common_tags.map((tag) => (
                    <span key={tag} style={{
                      background: "#1F2937", color: "#FCA5A5", padding: "3px 8px",
                      borderRadius: 3, fontSize: 11, fontWeight: 500,
                    }}>{tag}</span>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Proposed fixes */}
          <SectionHeader>Önerilen Düzeltmeler ({fixes.length})</SectionHeader>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, margin: "10px 0 16px 0" }}>
            {fixes.map((fix, i) => (
              <div key={i} style={{
                background: "#0B0F17", borderRadius: 6, padding: 12,
                borderLeft: `3px solid ${fix.risk === "high" ? "#EF4444" : fix.risk === "medium" ? "#F97316" : "#22C55E"}`,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#E5E7EB" }}>
                    {i + 1}. {fix.description}
                  </span>
                  <span style={{ fontSize: 10, color: "#9CA3AF", textTransform: "uppercase" }}>
                    {fix.type} · risk: {fix.risk}
                  </span>
                </div>
                {fix.implementation_hint && (
                  <pre style={{
                    background: "#000", color: "#86EFAC", padding: 10, borderRadius: 4,
                    fontSize: 11, overflow: "auto", margin: "6px 0", whiteSpace: "pre-wrap",
                  }}>{fix.implementation_hint}</pre>
                )}
                {fix.estimated_impact && (
                  <div style={{ fontSize: 11, color: "#9CA3AF", fontStyle: "italic" }}>
                    Tahmini etki: {fix.estimated_impact}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Alternatives */}
          {p.alternative_explanations?.length > 0 && (
            <>
              <SectionHeader>Alternatif Açıklamalar</SectionHeader>
              <ul style={{ fontSize: 12, color: "#9CA3AF", paddingLeft: 20, margin: "8px 0 16px 0" }}>
                {p.alternative_explanations.map((alt, i) => <li key={i}>{alt}</li>)}
              </ul>
            </>
          )}

          {/* Action buttons */}
          {p.status === "pending" && (
            <div style={{ display: "flex", gap: 10, paddingTop: 12, borderTop: "1px solid #1F2937" }}>
              <button
                disabled={isWorking}
                onClick={onApprove}
                style={{
                  background: "#22C55E", color: "#000", border: "none", padding: "10px 20px",
                  borderRadius: 6, cursor: "pointer", fontWeight: 600, fontSize: 13,
                  opacity: isWorking ? 0.5 : 1,
                }}
              >
                ✓ Onayla & GitHub Issue Aç
              </button>
              <button
                disabled={isWorking}
                onClick={() => {
                  const reason = prompt("Reddetme nedeni (opsiyonel):") || "";
                  onReject(reason);
                }}
                style={{
                  background: "transparent", color: "#FCA5A5", border: "1px solid #7F1D1D",
                  padding: "10px 20px", borderRadius: 6, cursor: "pointer", fontWeight: 500, fontSize: 13,
                }}
              >
                ✗ Reddet
              </button>
              {p.pr_url && (
                <a href={p.pr_url} target="_blank" rel="noreferrer" style={{
                  marginLeft: "auto", color: "#4F8CFF", fontSize: 13, alignSelf: "center",
                }}>
                  Issue → ↗
                </a>
              )}
            </div>
          )}
          {p.status !== "pending" && (
            <div style={{ paddingTop: 12, borderTop: "1px solid #1F2937", fontSize: 12, color: "#9CA3AF" }}>
              {p.reviewed_by && <>İnceleyen: <b>{p.reviewed_by}</b> · </>}
              {p.reviewed_at && <>Tarih: {new Date(p.reviewed_at).toLocaleString("tr-TR")}</>}
              {p.pr_url && (
                <a href={p.pr_url} target="_blank" rel="noreferrer" style={{
                  marginLeft: 12, color: "#4F8CFF",
                }}>
                  GitHub'da görüntüle ↗
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SimulationBlock({ proposal: p }: { proposal: Proposal }) {
  const qc = useQueryClient();
  const sim: SimulatedMetric | null = p.simulated_metric;
  const reSimMut = useMutation({
    mutationFn: () => aiOps.simulate(p.id, 60),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-ops-proposals"] });
      qc.invalidateQueries({ queryKey: ["ai-ops-proposal", p.id] });
    },
  });

  if (!sim) {
    return (
      <div style={{
        margin: "16px 0", padding: 12, background: "#111827", borderRadius: 8,
        border: "1px dashed #374151", display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ fontSize: 12, color: "#9CA3AF" }}>
          📊 Simülasyon henüz çalıştırılmadı.
        </div>
        <button
          onClick={() => reSimMut.mutate()}
          disabled={reSimMut.isPending}
          style={{
            background: "#374151", color: "#E5E7EB", border: "none",
            padding: "6px 12px", borderRadius: 4, fontSize: 11, cursor: "pointer",
          }}
        >
          {reSimMut.isPending ? "Çalışıyor..." : "Şimdi Simüle Et"}
        </button>
      </div>
    );
  }
  if (sim.status === "manual_review_required") {
    return (
      <div style={{
        margin: "16px 0", padding: 12, background: "rgba(234,179,8,0.10)", borderRadius: 8,
        borderLeft: "3px solid #EAB308", fontSize: 12, color: "#FDE68A",
      }}>
        ⚠ Bu önerinin türü otomatik simüle edilemez (feature_addition / weight_adjustment / retrain).
        İmplementasyon sonrası 7-gün canlı tracking yapılacak.
      </div>
    );
  }
  if (sim.status === "error" || sim.error === "no_historical_signals_in_window") {
    return (
      <div style={{
        margin: "16px 0", padding: 12, background: "rgba(239,68,68,0.10)", borderRadius: 8,
        borderLeft: "3px solid #EF4444", fontSize: 12, color: "#FCA5A5",
      }}>
        ⚠ Simülasyon başarısız: {sim.error ?? "bilinmeyen hata"}
      </div>
    );
  }

  const dWin = sim.deltas.win_rate_pp;
  const dPnl = sim.deltas.pnl_pips ?? 0;
  const dDrawdown = sim.deltas.max_drawdown_pp ?? 0;
  const dPF = sim.deltas.profit_factor_delta;
  const blocked = sim.deltas.n_signals_blocked ?? 0;
  const blockedLoss = sim.deltas.blocked_was_loss ?? 0;
  const blockedWin = sim.deltas.blocked_was_win ?? 0;
  const verdict = sim.deltas.verdict;
  const ciLow = sim.simulated.ci_low_pct;
  const ciHigh = sim.simulated.ci_high_pct;
  // Verdict-driven coloring (multi-metric, not just win-rate)
  const accent =
    verdict === "unanimously_better" ? "#22C55E"
    : verdict === "unanimously_worse" ? "#EF4444"
    : verdict === "insignificant" ? "#6B7280"
    : (dWin ?? 0) > 0 ? "#22C55E"
    : (dWin ?? 0) < 0 ? "#EF4444"
    : "#F97316";
  const winColor = (dWin ?? 0) > 0 ? "#86EFAC" : (dWin ?? 0) < 0 ? "#FCA5A5" : "#FDE68A";
  const pnlColor = dPnl > 0 ? "#86EFAC" : dPnl < 0 ? "#FCA5A5" : "#FDE68A";
  const ddColor = dDrawdown < 0 ? "#86EFAC" : dDrawdown > 5 ? "#FCA5A5" : "#FDE68A";

  return (
    <div style={{
      margin: "16px 0", padding: 14, background: "#0B0F17",
      borderRadius: 8, borderLeft: `3px solid ${accent}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <span style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: 0.5 }}>
          📊 Counterfactual Simülasyon (Son {sim.window_days}g)
        </span>
        <button
          onClick={() => reSimMut.mutate()}
          disabled={reSimMut.isPending}
          style={{
            background: "transparent", color: "#9CA3AF", border: "1px solid #374151",
            padding: "3px 10px", borderRadius: 4, fontSize: 10, cursor: "pointer",
          }}
        >
          {reSimMut.isPending ? "..." : "↻ Yenile"}
        </button>
      </div>
      {verdict && (
        <div style={{
          marginBottom: 10, padding: "5px 10px",
          background: accent + "22", borderRadius: 4, display: "inline-block",
          fontSize: 10, fontWeight: 700, color: accent, textTransform: "uppercase",
        }}>
          Verdict: {verdict === "unanimously_better" ? "🟢 Tüm metrikler iyileşti"
                   : verdict === "unanimously_better_but_noisy_filter"
                       ? "🟡 Metrikler iyi AMA filtre kazançları da öldürüyor"
                   : verdict === "noisy_filter" ? "🔴 Kirli filtre — kazançları öldürüyor"
                   : verdict === "unanimously_worse" ? "🔴 Hiçbir metrik iyileşmedi"
                   : verdict === "insignificant" ? "⚪ Anlamlı değişim yok"
                   : verdict === "insufficient_data" ? "❓ Veri yetersiz"
                   : "🟠 Karışık (bazısı iyi, bazısı kötü)"}
        </div>
      )}
      {/* Selectivity warning — user's "kazançları da öldürmesin" check */}
      {sim.deltas.selectivity_pct != null && (sim.deltas.n_signals_blocked ?? 0) > 0 && (
        <SelectivityBlock sel={sim.deltas} />
      )}

      {/* Discriminator deep-dive — only meaningful when selectivity is sub-optimal */}
      {sim.deltas.selectivity_label && sim.deltas.selectivity_label !== "clean"
        && (sim.deltas.blocked_was_win ?? 0) >= 5 && p.id && (
        <DiscriminatorBlock proposalId={p.id} />
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, fontSize: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Win-Rate Δ</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: winColor }}>
            {dWin == null ? "—" : `${dWin > 0 ? "+" : ""}${dWin.toFixed(2)}pp`}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            {sim.original.win_rate ?? "—"}% → {sim.simulated.win_rate ?? "—"}%
          </div>
          {ciLow != null && ciHigh != null && (
            <div style={{ fontSize: 9, color: "#6B7280", marginTop: 2 }}>
              CI95: [{ciLow.toFixed(1)}, {ciHigh.toFixed(1)}]%
            </div>
          )}
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>P/L Δ</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: pnlColor }}>
            {dPnl > 0 ? "+" : ""}{dPnl.toFixed(1)}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            pips: {sim.original.total_pnl_pips ?? 0} → {sim.simulated.total_pnl_pips ?? 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Max DD Δ</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: ddColor }}>
            {dDrawdown > 0 ? "+" : ""}{dDrawdown.toFixed(1)}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            pips: {sim.original.max_drawdown_pips ?? 0} → {sim.simulated.max_drawdown_pips ?? 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Blocked</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#E5E7EB" }}>{blocked}</div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            <span style={{ color: "#86EFAC" }}>{blockedLoss} fail</span>
            {" · "}
            <span style={{ color: "#FCA5A5" }}>{blockedWin} win</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Sample</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#E5E7EB" }}>
            {sim.original.n_signals ?? 0}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            {dPF != null ? `PF Δ ${dPF > 0 ? "+" : ""}${dPF.toFixed(2)}` : "signals replayed"}
          </div>
        </div>
      </div>
      {/* Walk-forward robustness (overfitting check) */}
      {sim.deltas.robustness && (
        <RobustnessBlock robustness={sim.deltas.robustness} sim={sim} />
      )}

      {sim.fixes_skipped?.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 11, color: "#9CA3AF" }}>
          {sim.fixes_skipped.length} fix simülasyon dışı (manuel inceleme gerekli):
          {" "}{sim.fixes_skipped.map(f => f.type).join(", ")}
        </div>
      )}
    </div>
  );
}

function SelectivityBlock({ sel }: { sel: any }) {
  const pct = sel.selectivity_pct;
  const label = sel.selectivity_label;
  const lossN = sel.blocked_was_loss ?? 0;
  const winN = sel.blocked_was_win ?? 0;
  const totalBlocked = lossN + winN;

  const meta: Record<string, { color: string; emoji: string; text: string; explainer: string }> = {
    clean: { color: "#22C55E", emoji: "✅", text: "TEMİZ FİLTRE",
             explainer: "Filtre çoğunlukla gerçek fail'leri yakalıyor — kazançları öldürmüyor." },
    acceptable: { color: "#EAB308", emoji: "🟡", text: "KABUL EDİLEBİLİR",
                  explainer: "Filtre çoğu fail'i yakalıyor ama bazı kazançları da bloklayabilir." },
    noisy: { color: "#EF4444", emoji: "❌", text: "KİRLİ FİLTRE",
             explainer: "Filtre kazançları aşırı bloklarken yeterli fail'i yakalamıyor — kullanma." },
    no_blocks: { color: "#6B7280", emoji: "⚪", text: "BLOCK YOK",
                 explainer: "Filtre hiçbir sinyali etkilemiyor — geçerli koşul tetiklenmedi." },
  };
  const m = meta[label as string] ?? meta.no_blocks;

  return (
    <div style={{
      margin: "10px 0", padding: 10, background: "#0B0F17", borderRadius: 6,
      borderLeft: `3px solid ${m.color}`, fontSize: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                    marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase",
                       letterSpacing: 0.5 }}>
          🎯 Filter Selectivity (Kazançları Öldürüyor mu?)
        </span>
        <span style={{
          padding: "3px 10px", borderRadius: 4, fontSize: 10, fontWeight: 700,
          background: m.color + "22", color: m.color, letterSpacing: 0.5,
        }}>
          {m.emoji} {m.text}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Precision</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: m.color }}>
            {pct != null ? `${pct.toFixed(1)}%` : "—"}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            {lossN}/{totalBlocked} blocked were fails
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Önlenen Fail</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#86EFAC" }}>{lossN}</div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>true positives</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Kaybedilen Win</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: "#FCA5A5" }}>{winN}</div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>false positives — collateral</div>
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: "#D1D5DB", fontStyle: "italic" }}>
        💬 {m.explainer}
      </div>
    </div>
  );
}


function DiscriminatorBlock({ proposalId }: { proposalId: string }) {
  const [result, setResult] = useState<DiscriminatorAnalysis | null>(null);
  const [open, setOpen] = useState(false);
  const mut = useMutation({
    mutationFn: () => aiOps.discriminatorAnalysis(proposalId, 60),
    onSuccess: (data) => { setResult(data.result); setOpen(true); },
    onError: (e: any) => alert(`Discriminator analizi başarısız: ${e?.message ?? "bilinmiyor"}`),
  });

  return (
    <div style={{
      margin: "10px 0", padding: 12, background: "#0B0F17", borderRadius: 6,
      borderLeft: "3px solid #A855F7",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase",
                        letterSpacing: 0.5 }}>
            🔬 Discriminator Deep-Dive
          </div>
          <div style={{ fontSize: 11, color: "#D1D5DB", marginTop: 4 }}>
            Bloklanan win'lerle fail'leri ayıran gizli feature'ları bul — filter'ı keskinleştir.
          </div>
        </div>
        <button
          onClick={() => result ? setOpen(!open) : mut.mutate()}
          disabled={mut.isPending}
          style={{
            background: "#A855F7", color: "#fff", border: "none",
            padding: "6px 12px", borderRadius: 4, cursor: "pointer", fontSize: 11,
            opacity: mut.isPending ? 0.5 : 1, whiteSpace: "nowrap",
          }}
        >
          {mut.isPending ? "Analiz Ediliyor..." : result ? (open ? "Gizle" : "Sonucu Aç") : "Derin Analiz Çalıştır"}
        </button>
      </div>

      {open && result && (
        <DiscriminatorResult result={result} />
      )}
    </div>
  );
}

function DiscriminatorResult({ result }: { result: DiscriminatorAnalysis }) {
  if (result.status === "insufficient_data") {
    return (
      <div style={{ marginTop: 10, fontSize: 11, color: "#FDE68A" }}>
        ⚠ Yeterli örnek yok: {result.n_wins} win, {result.n_fails} fail bulundu
        (min {result.min_required?.wins ?? 5}/{result.min_required?.fails ?? 5} gerekli).
      </div>
    );
  }
  if (result.status === "error") {
    return (
      <div style={{ marginTop: 10, fontSize: 11, color: "#FCA5A5" }}>
        ❌ {result.error}{result.note ? ` — ${result.note}` : ""}
      </div>
    );
  }

  const orig = result.original;
  const top = result.discriminators_top ?? [];
  const refine = result.recommended_refinement;

  return (
    <div style={{ marginTop: 12 }}>
      {orig && (
        <div style={{ fontSize: 11, color: "#9CA3AF", marginBottom: 10 }}>
          Bloklanan toplam: <b>{orig.n_blocked}</b> · Fails: <b style={{ color: "#86EFAC" }}>{orig.n_fails_blocked}</b>
          {" · "}Wins kaybı: <b style={{ color: "#FCA5A5" }}>{orig.n_wins_blocked}</b>
          {" · "}Precision: <b>{orig.precision_pct}%</b>
        </div>
      )}

      <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase",
                    letterSpacing: 0.5, marginBottom: 6 }}>
        🏆 En Güçlü Ayırıcı Feature'lar (top {top.length})
      </div>
      <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: "#6B7280", fontSize: 10, textTransform: "uppercase",
                       textAlign: "left", borderBottom: "1px solid #1F2937" }}>
            <th style={{ padding: "6px 4px" }}>Feature</th>
            <th style={{ padding: "6px 4px" }}>Win Ort.</th>
            <th style={{ padding: "6px 4px" }}>Fail Ort.</th>
            <th style={{ padding: "6px 4px" }}>Eşik / Kategori</th>
            <th style={{ padding: "6px 4px", textAlign: "right" }}>Rescue / Leak</th>
          </tr>
        </thead>
        <tbody>
          {top.map((d, i) => {
            const sepColor = Math.abs(d.separation) >= 0.3 ? "#22C55E"
                           : Math.abs(d.separation) >= 0.15 ? "#EAB308" : "#9CA3AF";
            return (
              <tr key={i} style={{ borderBottom: "1px solid #111827",
                                    background: i === 0 ? "#A855F710" : "transparent" }}>
                <td style={{ padding: "6px 4px", fontFamily: "monospace", color: "#E5E7EB" }}>
                  {d.feature}
                </td>
                <td style={{ padding: "6px 4px", color: "#86EFAC" }}>
                  {d.type === "numeric" ? d.win_mean?.toFixed(2) : "—"}
                </td>
                <td style={{ padding: "6px 4px", color: "#FCA5A5" }}>
                  {d.type === "numeric" ? d.fail_mean?.toFixed(2) : "—"}
                </td>
                <td style={{ padding: "6px 4px", color: sepColor, fontFamily: "monospace" }}>
                  {d.type === "numeric"
                    ? `${d.direction === "above" ? ">" : "<"} ${d.threshold?.toFixed(2)}`
                    : `= ${d.category}`}
                  {" "}
                  <span style={{ color: "#6B7280" }}>(Δ {(d.separation * 100).toFixed(1)}%)</span>
                </td>
                <td style={{ padding: "6px 4px", textAlign: "right", color: "#9CA3AF" }}>
                  <span style={{ color: "#86EFAC" }}>+{d.wins_in_rescue}w</span>
                  {" / "}
                  <span style={{ color: "#FCA5A5" }}>+{d.fails_re_allowed}f</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {refine && (
        <div style={{ marginTop: 14, padding: 12, background: "#111827",
                      borderLeft: "3px solid #22C55E", borderRadius: 4 }}>
          <div style={{ fontSize: 10, color: "#86EFAC", textTransform: "uppercase",
                        letterSpacing: 0.5, marginBottom: 6, fontWeight: 700 }}>
            ✨ Önerilen Refinement
          </div>
          <div style={{ fontSize: 12, color: "#E5E7EB", marginBottom: 10, lineHeight: 1.5 }}>
            {refine.rule}
          </div>
          <pre style={{
            background: "#000", padding: 10, borderRadius: 4, margin: 0,
            fontSize: 11, color: "#86EFAC", overflow: "auto",
          }}>
{`${refine.extra_predicate.field} ${refine.extra_predicate.op} ${JSON.stringify(refine.extra_predicate.value)}`}
          </pre>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
                        gap: 12, marginTop: 12, fontSize: 11 }}>
            <Stat label="Kurtarılan Win" value={`${refine.expected.wins_rescued}`} color="#86EFAC" />
            <Stat label="Yeniden Geçen Fail" value={`${refine.expected.fails_re_allowed}`} color="#FCA5A5" />
            <Stat label="Yeni Precision" value={`${refine.expected.new_precision_pct ?? "—"}%`} color="#E5E7EB" />
            <Stat label="Fail Block Kaybı" value={`${refine.expected.fail_block_efficacy_loss_pct}%`} color="#FDE68A" />
          </div>
          <div style={{ marginTop: 10, fontSize: 10, color: "#6B7280", fontStyle: "italic" }}>
            Bu refinement'i implement etmek için yeni proposal_simulator kuralı yaz veya
            mevcut PR'a `extra_predicate`'i ekle.
          </div>
        </div>
      )}
    </div>
  );
}


function RobustnessBlock({ robustness, sim }: { robustness: any; sim: SimulatedMetric }) {
  const status = robustness.status;
  const inDelta = robustness.in_sample_winrate_delta;
  const oosDelta = robustness.oos_winrate_delta;
  const ratio = robustness.robustness_ratio;
  const inN = sim.deltas.in_sample?.n_signals ?? 0;
  const oosN = sim.deltas.out_of_sample?.n_signals ?? 0;

  const statusMeta: Record<string, { label: string; color: string; emoji: string }> = {
    robust: { label: "ROBUST", color: "#22C55E", emoji: "✅" },
    marginally_overfit: { label: "MARGINALLY OVERFIT", color: "#F59E0B", emoji: "⚠️" },
    overfit: { label: "OVERFIT", color: "#F97316", emoji: "🟠" },
    highly_overfit: { label: "HIGHLY OVERFIT", color: "#EF4444", emoji: "🔴" },
    broken: { label: "BROKEN IN-SAMPLE", color: "#EF4444", emoji: "❌" },
    insufficient_data: { label: "INSUFFICIENT DATA", color: "#6B7280", emoji: "❓" },
    insignificant_in_sample: { label: "EFFECT TOO SMALL", color: "#6B7280", emoji: "⚪" },
  };
  const meta = statusMeta[status] ?? statusMeta.insufficient_data;

  return (
    <div style={{
      marginTop: 14, padding: 12, background: "#0B0F17", borderRadius: 6,
      borderLeft: `3px solid ${meta.color}`,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontSize: 11, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: 0.5 }}>
          🔬 Walk-Forward Overfitting Check
        </span>
        <span style={{
          padding: "3px 10px", borderRadius: 4, fontSize: 10, fontWeight: 700,
          background: meta.color + "22", color: meta.color, letterSpacing: 0.5,
        }}>
          {meta.emoji} {meta.label}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, fontSize: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>
            In-Sample (DeepSeek'in gördüğü {sim.deltas.training_window_days ?? 7} gün)
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#FCA5A5" }}>
            {inDelta == null ? "—" : `${inDelta > 0 ? "+" : ""}${inDelta.toFixed(2)}pp`}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>{inN} signal</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>
            Out-of-Sample (DeepSeek'in görmediği {sim.window_days - (sim.deltas.training_window_days ?? 7)} gün)
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#86EFAC" }}>
            {oosDelta == null ? "—" : `${oosDelta > 0 ? "+" : ""}${oosDelta.toFixed(2)}pp`}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>{oosN} signal</div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Robustness Ratio</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: meta.color }}>
            {ratio == null ? "—" : ratio.toFixed(2)}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>OOS / In-Sample</div>
        </div>
      </div>
      {robustness.interpretation && (
        <div style={{ marginTop: 10, fontSize: 11, color: "#D1D5DB", fontStyle: "italic" }}>
          {robustness.interpretation}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, color = "#E5E7EB" }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color }}>{value}</div>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 11, color: "#9CA3AF", textTransform: "uppercase", letterSpacing: 0.5,
      fontWeight: 600, marginTop: 8,
    }}>{children}</div>
  );
}
