"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Zap, CheckCircle2, Circle } from "lucide-react";
import { buildApiUrl } from "../../lib/api/base";

interface ComboMember {
  model: string;
  direction: "BUY" | "SELL" | "HOLD";
  available: boolean;
  confidence: number;
}

interface Combo {
  label: string;
  models: string[];
  win_rate: number;
  trades: number | null;
  members: ComboMember[];
  aligned: boolean;
  direction: "BUY" | "SELL" | "HOLD";
}

interface BestComboData {
  symbol: string;
  supported: boolean;
  triggered: boolean;
  direction: "BUY" | "SELL" | "HOLD";
  fired_combo: string | null;
  fired_win_rate: number | null;
  combos: Combo[];
}

const POLL_MS = 12000;

const MODEL_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  ml: { bg: "bg-blue-500/15", text: "text-blue-300", label: "ML" },
  emel: { bg: "bg-purple-500/15", text: "text-purple-300", label: "EMEL" },
  pulse1: { bg: "bg-orange-500/15", text: "text-orange-300", label: "PULSE1" },
  pulse2: { bg: "bg-orange-500/15", text: "text-orange-300", label: "PULSE2" },
  pulse3: { bg: "bg-orange-500/15", text: "text-orange-300", label: "PULSE3" },
  smc: { bg: "bg-teal-500/15", text: "text-teal-300", label: "SMC" },
};

function dirColor(d: string): string {
  if (d === "BUY") return "text-green-400";
  if (d === "SELL") return "text-red-400";
  return "text-slate-500";
}

function DirectionIcon({ direction, className }: { direction: string; className?: string }) {
  if (direction === "BUY") return <TrendingUp className={className} />;
  if (direction === "SELL") return <TrendingDown className={className} />;
  return <Circle className={className} />;
}

export default function NewCombinationPanel({ symbol }: { symbol: string }) {
  const [data, setData] = useState<BestComboData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(buildApiUrl(`/api/meta/best-combo/${encodeURIComponent(symbol)}`));
        const json = await res.json();
        if (cancelled) return;
        if (json?.success && json?.data) {
          setData(json.data as BestComboData);
          setError(null);
        } else {
          setError(json?.error || "No data");
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Fetch failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    timer.current = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      if (timer.current) clearInterval(timer.current);
    };
  }, [symbol]);

  if (!loading && data && !data.supported) return null;

  const triggered = data?.triggered ?? false;
  const fireDir = data?.direction ?? "HOLD";
  const isBuy = fireDir === "BUY";

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="relative overflow-hidden rounded-2xl border bg-slate-950/80 backdrop-blur-sm"
      style={{
        borderColor: triggered ? (isBuy ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)") : "rgba(250,204,21,0.25)",
      }}
    >
      {/* Flashing glow overlay when a combo is fully aligned */}
      <AnimatePresence>
        {triggered && (
          <motion.div
            key="glow"
            className="pointer-events-none absolute inset-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0.05, 0.45, 0.05] }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
            style={{
              background: isBuy
                ? "radial-gradient(circle at 50% 0%, rgba(34,197,94,0.55), transparent 70%)"
                : "radial-gradient(circle at 50% 0%, rgba(239,68,68,0.55), transparent 70%)",
            }}
          />
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="relative flex items-center justify-between border-b border-yellow-500/20 bg-yellow-500/5 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-yellow-400" />
          <span className="text-sm font-extrabold uppercase tracking-wide text-yellow-300">
            New Combination
          </span>
          <span className="hidden text-[11px] text-slate-500 sm:inline">
            · en başarılı kombinasyonlar · onaylı sinyal
          </span>
        </div>
        {error && <span className="text-[11px] text-red-400">offline</span>}
      </div>

      {/* Fired banner — flashing */}
      <AnimatePresence>
        {triggered && (
          <motion.div
            key="banner"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className={`relative flex items-center justify-between gap-3 px-4 py-3 ${
              isBuy ? "bg-green-500/10" : "bg-red-500/10"
            }`}
          >
            <motion.div
              className="flex items-center gap-3"
              animate={{ opacity: [1, 0.35, 1] }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }}
            >
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-full ${
                  isBuy ? "bg-green-500/25" : "bg-red-500/25"
                }`}
              >
                <DirectionIcon direction={fireDir} className={`h-6 w-6 ${dirColor(fireDir)}`} />
              </div>
              <div>
                <div className={`text-lg font-black ${dirColor(fireDir)}`}>
                  {isBuy ? "YUKARI YÖNLÜ ONAY" : "AŞAĞI YÖNLÜ ONAY"} · {fireDir}
                </div>
                <div className="text-[11px] text-slate-300">
                  {data?.fired_combo}{" "}
                  {data?.fired_win_rate != null && (
                    <span className="font-bold text-yellow-300">· {data.fired_win_rate}% WR</span>
                  )}
                </div>
              </div>
            </motion.div>
            <motion.span
              className={`hidden rounded-full px-3 py-1 text-xs font-bold sm:inline ${
                isBuy ? "bg-green-500/20 text-green-300" : "bg-red-500/20 text-red-300"
              }`}
              animate={{ scale: [1, 1.08, 1] }}
              transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }}
            >
              ● CANLI
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Combo rows */}
      <div className="relative flex flex-col divide-y divide-slate-800/60">
        {loading && !data && (
          <div className="px-4 py-4 text-xs text-slate-500">Yükleniyor…</div>
        )}
        {data?.combos.map((combo) => (
          <div key={combo.label} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-1.5">
              {combo.aligned ? (
                <CheckCircle2 className={`h-4 w-4 ${dirColor(combo.direction)}`} />
              ) : (
                <Circle className="h-4 w-4 text-slate-600" />
              )}
              {combo.members.map((m, i) => {
                const style = MODEL_STYLE[m.model] ?? { bg: "bg-slate-700/30", text: "text-slate-300", label: m.model.toUpperCase() };
                return (
                  <span key={m.model} className="flex items-center">
                    {i > 0 && <span className="px-1 text-slate-600">+</span>}
                    <span
                      className={`flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-semibold ${style.bg} ${style.text} ${
                        !m.available ? "opacity-40" : ""
                      }`}
                      title={m.available ? `${m.direction} (${m.confidence}%)` : "veri yok"}
                    >
                      {style.label}
                      <DirectionIcon direction={m.direction} className={`h-3 w-3 ${dirColor(m.direction)}`} />
                    </span>
                  </span>
                );
              })}
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-yellow-500/10 px-2 py-0.5 text-[11px] font-bold text-yellow-300">
                {combo.win_rate}% WR
                {combo.trades ? <span className="ml-1 font-normal text-slate-500">N={combo.trades}</span> : null}
              </span>
              <span
                className={`min-w-[64px] text-right text-xs font-bold ${
                  combo.aligned ? dirColor(combo.direction) : "text-slate-600"
                }`}
              >
                {combo.aligned ? combo.direction : "bekliyor"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
