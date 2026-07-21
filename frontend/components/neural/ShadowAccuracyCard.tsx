"use client";

/**
 * ShadowAccuracyCard — sızıntısız paper-trade doğrulama karnesi.
 *
 * Backend: GET /api/shadow-tracker/report?symbol=&days=
 * Kaynak başına (pattern | fakeout) canlı isabet istatistiği gösterir:
 * n, kazanç/kayıp, isabet %, ortalama R. n<10 iken "veri birikiyor" der —
 * küçük örneklemle isabet iddia etmez (dürüstlük ilkesi).
 *
 * Ölçüm sözleşmesi (shadow_trade_tracker): giriş = karar anındaki son
 * KAPANMIŞ 5m barın kapanışı; çözüm yalnız SONRAKİ barların high/low'u ile;
 * aynı barda TP+SL → konservatif LOSS. Geleceği görme / geriye bakma yok.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { buildApiUrl } from "@/lib/api/base";
import { useNeuralLocale } from "@/components/neural/i18n";

interface Agg {
  total: number;
  open: number;
  wins: number;
  losses: number;
  expired: number;
  win_rate: number | null;
  avg_r: number | null;
  sample_warning: boolean;
}

interface ShadowReport {
  success: boolean;
  db_degraded?: boolean;
  overall?: Agg;
  by_source?: Record<string, Agg>;
  by_confidence?: Record<string, Agg>;
  recent?: {
    id: number | string;
    source: string;
    pattern: string;
    direction: string;
    confidence: number;
    status: string;
    r_multiple: number | null;
  }[];
}

const POLL_MS = 60_000;

function SourceRow({ label, agg, accent }: { label: string; agg?: Agg; accent: string }) {
  const { L } = useNeuralLocale();
  if (!agg || agg.total === 0) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-white/[0.05] bg-white/[0.02] px-3 py-2">
        <span className="font-mono text-[9px] tracking-[0.15em] text-gray-500">{label}</span>
        <span className="text-[10px] text-gray-600">{L("henüz sanal işlem yok", "no shadow trades yet")}</span>
      </div>
    );
  }
  const resolved = agg.wins + agg.losses;
  return (
    <div className="rounded-lg border border-white/[0.05] bg-white/[0.02] px-3 py-2">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[9px] tracking-[0.15em] text-gray-400">{label}</span>
        <span className="font-mono text-[9px] text-gray-500">
          n={agg.total} · {L("açık", "open")} {agg.open}
        </span>
      </div>
      <div className="mt-1.5 flex items-center gap-3">
        {agg.win_rate !== null && resolved > 0 ? (
          <>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div
                className="h-full rounded-full"
                style={{ background: accent }}
                initial={{ width: 0 }}
                animate={{ width: `${agg.win_rate}%` }}
                transition={{ duration: 0.7 }}
              />
            </div>
            <span className="font-mono text-[11px] font-bold" style={{ color: accent }}>
              %{agg.win_rate}
            </span>
            <span className="font-mono text-[9px] text-gray-500">
              {agg.wins}W/{agg.losses}L
              {agg.avg_r !== null && ` · ${agg.avg_r >= 0 ? "+" : ""}${agg.avg_r}R`}
            </span>
          </>
        ) : (
          <span className="text-[10px] text-gray-500">
            {L("sonuçlanan işlem bekleniyor…", "awaiting resolved trades…")}
          </span>
        )}
      </div>
      {agg.sample_warning && resolved > 0 && (
        <div className="mt-1 font-mono text-[8px] tracking-[0.1em] text-amber-500/70">
          ⚠ n&lt;10 — {L("veri birikiyor, istatistik henüz güvenilir değil", "collecting data, stats not yet reliable")}
        </div>
      )}
    </div>
  );
}

export default function ShadowAccuracyCard({
  symbol,
  sources = ["fakeout", "pattern"],
}: {
  symbol?: string;
  sources?: ("fakeout" | "pattern" | "meta")[];
}) {
  const { L } = useNeuralLocale();
  const [report, setReport] = useState<ShadowReport | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const qs = symbol ? `?symbol=${encodeURIComponent(symbol)}&days=30` : "?days=30";
        const res = await fetch(buildApiUrl(`/api/shadow-tracker/report${qs}`));
        if (!res.ok) throw new Error(String(res.status));
        const json = (await res.json()) as ShadowReport;
        if (alive) {
          setReport(json.success ? json : null);
          setError(!json.success);
        }
      } catch {
        if (alive) setError(true);
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [symbol]);

  if (error) return null; // backend eski sürümse kartı hiç gösterme (sessiz)
  if (!report) {
    return <div className="h-16 animate-pulse rounded-xl bg-white/[0.03]" />;
  }

  const labels: Record<string, [string, string]> = {
    fakeout: ["KIRILIM ÇAĞRILARI (AI DEDEKTÖR)", "BREAKOUT CALLS (AI DETECTOR)"],
    pattern: ["FORMASYON TESPİTLERİ (%60+ GÜVEN)", "PATTERN DETECTIONS (60%+ CONF)"],
    meta: ["CORE ENSEMBLE SİNYALLERİ (6 MODEL)", "CORE ENSEMBLE SIGNALS (6 MODELS)"],
  };
  const accents: Record<string, string> = { fakeout: "#f59e0b", pattern: "#22d3ee", meta: "#34d399" };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[8px] tracking-[0.25em] text-gray-500">
          ◆ {L("CANLI DOĞRULAMA — SANAL İŞLEM KARNESİ (30G)", "LIVE VALIDATION — SHADOW TRADE SCORE (30D)")}
        </span>
        {report.db_degraded && (
          <span className="font-mono text-[8px] text-amber-500/70">
            {L("DB bağlantısı yok — geçici bellek", "DB offline — in-memory")}
          </span>
        )}
      </div>
      {sources.map((s) => (
        <SourceRow key={s} label={L(...labels[s])} agg={report.by_source?.[s]} accent={accents[s]} />
      ))}
      <p className="font-mono text-[8px] leading-relaxed tracking-[0.05em] text-gray-600">
        {L(
          "Her tespit anında sanal işlem açılır (giriş = son kapanmış 5m bar); TP/SL yalnız SONRAKİ barlarla ölçülür — geriye bakma yok.",
          "A shadow trade opens at detection (entry = last closed 5m bar); TP/SL measured only on SUBSEQUENT bars — no hindsight."
        )}
      </p>
    </div>
  );
}
