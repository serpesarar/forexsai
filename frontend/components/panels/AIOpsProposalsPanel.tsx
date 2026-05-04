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
    queryKey: ["ai-ops-proposals", filter],
    queryFn: () => aiOps.listProposals(filter === "all" ? {} : { status: filter, limit: 100 }),
    refetchInterval: 60000,
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => aiOps.approve(id, { create_github_issue: true, reviewer: "user" }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["ai-ops-proposals"] });
      qc.invalidateQueries({ queryKey: ["ai-ops-stats"] });
      if (data.issue_url) {
        window.open(data.issue_url, "_blank");
      } else {
        alert("Onaylandı. GitHub issue açılamadı (GITHUB_TOKEN backend env'de eksik olabilir).");
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

  const list = proposals.data?.proposals ?? [];

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
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
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
  const blocked = sim.deltas.n_signals_blocked ?? 0;
  const blockedLoss = sim.deltas.blocked_was_loss ?? 0;
  const blockedWin = sim.deltas.blocked_was_win ?? 0;
  const positive = (dWin ?? 0) > 0 && dPnl >= 0;
  const accent = positive ? "#22C55E" : (dWin ?? 0) < 0 ? "#EF4444" : "#F97316";
  const winColor = (dWin ?? 0) > 0 ? "#86EFAC" : (dWin ?? 0) < 0 ? "#FCA5A5" : "#FDE68A";
  const pnlColor = dPnl > 0 ? "#86EFAC" : dPnl < 0 ? "#FCA5A5" : "#FDE68A";

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
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, fontSize: 12 }}>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Win-Rate Δ</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: winColor }}>
            {dWin == null ? "—" : `${dWin > 0 ? "+" : ""}${dWin.toFixed(2)}pp`}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            {sim.original.win_rate ?? "—"}% → {sim.simulated.win_rate ?? "—"}%
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>P/L Δ (pips)</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: pnlColor }}>
            {dPnl > 0 ? "+" : ""}{dPnl.toFixed(1)}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            {sim.original.total_pnl_pips ?? 0} → {sim.simulated.total_pnl_pips ?? 0}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Blocked</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#E5E7EB" }}>{blocked}</div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>
            <span style={{ color: "#86EFAC" }}>{blockedLoss} fail önlendi</span>
            {" · "}
            <span style={{ color: "#FCA5A5" }}>{blockedWin} win kayıp</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, color: "#6B7280", textTransform: "uppercase" }}>Sample</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#E5E7EB" }}>
            {sim.original.n_signals ?? 0}
          </div>
          <div style={{ fontSize: 10, color: "#6B7280" }}>signals replayed</div>
        </div>
      </div>
      {sim.fixes_skipped?.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 11, color: "#9CA3AF" }}>
          {sim.fixes_skipped.length} fix simülasyon dışı (manuel inceleme gerekli):
          {" "}{sim.fixes_skipped.map(f => f.type).join(", ")}
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
