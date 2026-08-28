"use client";

/**
 * Bot İşlem Defteri — DeciderTradeLog'un gerçek MT5 işlemleri karşılığı.
 *
 * Aynı gün-gruplu / satır-açılır yapı, ama veri kaynağı farklı: decider'da
 * LLM gerekçesi + MFE/MAE yol izi var, bot'ta bunlar YOK — MT5 yalnız
 * giriş/çıkış fiyatı, planlanan SL/TP ve $ sonucu taşır. 2026-08-27'den
 * önceki işlemlerde giriş/SL/TP hiç kaydedilmemişti (agent 1.2 ile
 * zenginleştirme başladı); böyle satırlarda `entry`/`sl`/`tp`/`r` null
 * gelir ve bileşen bunu "geometri yok" olarak sessizce atlar — uydurmaz.
 *
 * Birincil metrik NET $'dır (bot'un gerçek kâr/zararı budur); R yalnızca
 * geometri mevcutsa (giriş+SL bilinen işlemler) ikincil olarak gösterilir.
 */

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

import type { BotTradeRow } from "@/lib/api/evolution";
import { Badge, cx } from "./ui";

function netColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return "#64748B";
  if (v > 0) return "#34D399";
  if (v < 0) return "#FB7185";
  return "#94A3B8";
}

function fmtNet(v: number): string {
  return `${v >= 0 ? "+" : ""}${v.toLocaleString("tr-TR", { maximumFractionDigits: 2 })} $`;
}

function fmtR(v: number | null): string {
  if (v === null) return "—";
  return `${v > 0 ? "+" : ""}${v.toFixed(2)}R`;
}

function fmtPrice(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("tr-TR", { maximumFractionDigits: 3 });
}

function hhmm(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

function dayLabel(day: string): string {
  const d = new Date(`${day}T12:00:00Z`);
  return d.toLocaleDateString("tr-TR", {
    day: "numeric", month: "long", weekday: "short", timeZone: "UTC",
  });
}

/** Girişten TP ve SL'e uzaklığı gösteren şerit — yalnız ikisi de biliniyorsa. */
function GeometryBar({ t }: { t: BotTradeRow }) {
  if (t.entry === null || t.sl === null || t.tp === null) return null;
  const tpDist = Math.abs(t.tp - t.entry);
  const slDist = Math.abs(t.entry - t.sl);
  if (!tpDist || !slDist) return null;
  const total = tpDist + slDist;
  const tpPct = (tpDist / total) * 100;
  const won = t.exit_reason === "TP";
  const lost = t.exit_reason === "SL";
  const rr = slDist > 0 ? tpDist / slDist : null;
  return (
    <div className="mt-2">
      <div className="flex h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className={cx("transition-opacity", lost ? "opacity-100" : "opacity-40")}
          style={{ width: `${100 - tpPct}%`, background: "#FB7185" }}
          title={`SL mesafesi ${slDist.toFixed(2)} puan`}
        />
        <div
          className={cx("transition-opacity", won ? "opacity-100" : "opacity-40")}
          style={{ width: `${tpPct}%`, background: "#34D399" }}
          title={`TP mesafesi ${tpDist.toFixed(2)} puan`}
        />
      </div>
      <div className="mt-0.5 flex justify-between text-[9.5px] tabular-nums text-slate-600">
        <span>SL {slDist.toFixed(2)} puan</span>
        <span className={cx(rr && rr < 1 ? "text-amber-500/80" : "text-slate-600")}>
          {rr !== null ? `planlı RR ${rr.toFixed(2)}` : ""}
        </span>
        <span>TP {tpDist.toFixed(2)} puan</span>
      </div>
    </div>
  );
}

function Field({
  label, value, tone, strong,
}: {
  label: string; value: string; tone?: "green" | "red"; strong?: boolean;
}) {
  return (
    <div>
      <div className="text-[9.5px] text-slate-600">{label}</div>
      <div
        className={cx(
          strong ? "font-semibold text-slate-200" : "text-slate-300",
          tone === "green" && "text-emerald-300",
          tone === "red" && "text-rose-300",
        )}
      >
        {value}
      </div>
    </div>
  );
}

function TradeRow({ t }: { t: BotTradeRow }) {
  const [open, setOpen] = useState(false);
  const hasGeometry = t.entry !== null;

  return (
    <div className="rounded-xl odd:bg-white/[0.02]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-2.5 py-1.5 text-left text-[11px] transition hover:bg-white/[0.03]"
      >
        <span className="w-[38px] shrink-0 tabular-nums text-slate-500">{hhmm(t.ts)}</span>
        <span
          className={cx(
            "w-[38px] shrink-0 font-semibold",
            t.direction === "BUY" ? "text-emerald-300"
              : t.direction === "SELL" ? "text-rose-300" : "text-slate-500",
          )}
        >
          {t.direction ?? "?"}
        </span>
        {hasGeometry ? (
          <span className="shrink-0 tabular-nums text-slate-500">
            {fmtPrice(t.entry)}
            <span className="mx-1 text-slate-700">→</span>
            <span className={t.win ? "text-emerald-300/80" : "text-rose-300/80"}>
              {fmtPrice(t.exit)}
            </span>
          </span>
        ) : (
          <span className="shrink-0 tabular-nums text-slate-500">{fmtPrice(t.exit)}</span>
        )}
        <span className="ml-auto flex shrink-0 items-center gap-2">
          {t.r !== null && (
            <span className="tabular-nums text-slate-500">{fmtR(t.r)}</span>
          )}
          <span className="font-semibold tabular-nums" style={{ color: netColor(t.net) }}>
            {fmtNet(t.net)}
          </span>
          <Badge tone={t.exit_reason === "TP" ? "green" : t.exit_reason === "SL" ? "red" : "slate"}>
            {t.exit_reason === "manuel" ? "manuel" : t.exit_reason}
          </Badge>
          <ChevronDown
            size={12}
            className={cx("text-slate-600 transition-transform", open && "rotate-180")}
          />
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="px-2.5 pb-2.5 pt-0.5">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10.5px] tabular-nums sm:grid-cols-4">
                <Field label="giriş" value={fmtPrice(t.entry)} />
                <Field label="hedef (TP)" value={fmtPrice(t.tp)} tone="green" />
                <Field label="stop (SL)" value={fmtPrice(t.sl)} tone="red" />
                <Field
                  label="çıkış"
                  value={fmtPrice(t.exit)}
                  tone={t.win ? "green" : "red"}
                />
                <Field label="net" value={fmtNet(t.net)} strong />
                <Field label="R (planlı SL'e göre)" value={fmtR(t.r)} />
                <Field label="lot" value={t.volume !== null ? `${t.volume}` : "—"} />
                <Field label="seans" value={t.session} />
                <Field
                  label="komisyon"
                  value={t.commission !== null ? `${t.commission.toFixed(2)} $` : "—"}
                />
                <Field label="swap" value={t.swap !== null ? `${t.swap.toFixed(2)} $` : "—"} />
              </div>
              <GeometryBar t={t} />
              {!hasGeometry && (
                <p className="mt-2 text-[10px] leading-snug text-slate-600">
                  Bu işlem 2026-08-27 zenginleştirmesinden ÖNCE kaydedilmiş — giriş/SL/TP/R yok.
                </p>
              )}
              {t.comment && (
                <p className="mt-2 text-[10px] leading-snug text-slate-600">
                  <span className="text-slate-700">MT5 · </span>{t.comment}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function DayHeader({
  day, rows, expanded, onToggle,
}: {
  day: string; rows: BotTradeRow[]; expanded: boolean; onToggle: () => void;
}) {
  const tp = rows.filter((r) => r.exit_reason === "TP").length;
  const sl = rows.filter((r) => r.exit_reason === "SL").length;
  const net = rows.reduce((a, r) => a + r.net, 0);

  return (
    <button
      onClick={onToggle}
      className="sticky top-0 z-10 flex w-full items-center gap-2 rounded-lg bg-[#0B0F17]/95 px-2.5 py-1.5 text-left backdrop-blur transition hover:bg-white/[0.04]"
    >
      <ChevronDown
        size={13}
        className={cx("shrink-0 text-slate-600 transition-transform", !expanded && "-rotate-90")}
      />
      <span className="text-[11.5px] font-semibold text-slate-300">{dayLabel(day)}</span>
      <span className="text-[10.5px] text-slate-600">{rows.length} işlem</span>
      <span className="ml-auto flex items-center gap-2 text-[10.5px] tabular-nums">
        {(tp > 0 || sl > 0) && (
          <span>
            <span className="text-emerald-400">{tp} TP</span>
            <span className="mx-1 text-slate-700">/</span>
            <span className="text-rose-400">{sl} SL</span>
          </span>
        )}
        <span className="font-semibold" style={{ color: netColor(net) }}>
          {fmtNet(net)}
        </span>
      </span>
    </button>
  );
}

export default function BotTradeLog({ decisions }: { decisions: BotTradeRow[] }) {
  const [only, setOnly] = useState<"all" | "BUY" | "SELL">("all");
  const [collapsed, setCollapsed] = useState<Set<string>>(() => new Set());

  const byDay = useMemo(() => {
    const rows = decisions.filter((d) => (only === "all" ? true : d.direction === only));
    const map = new Map<string, BotTradeRow[]>();
    for (const r of rows) {
      const list = map.get(r.day);
      if (list) list.push(r);
      else map.set(r.day, [r]);
    }
    return Array.from(map.entries()).sort((a, b) => b[0].localeCompare(a[0]));
  }, [decisions, only]);

  const toggle = (day: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });

  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5">
        {([["all", "hepsi"], ["BUY", "BUY"], ["SELL", "SELL"]] as const).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setOnly(k)}
            className={cx(
              "rounded-full px-2.5 py-0.5 text-[11px] transition",
              only === k
                ? "bg-white/10 text-slate-200 ring-1 ring-white/20"
                : "text-slate-500 hover:text-slate-300",
            )}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto text-[10px] text-slate-600">
          satıra tıkla → giriş / TP / SL
        </span>
      </div>

      {byDay.length === 0 && (
        <p className="py-6 text-center text-[12px] text-slate-500">Bu filtrede işlem yok.</p>
      )}

      <div className="space-y-2">
        {byDay.map(([day, rows]) => {
          const expanded = !collapsed.has(day);
          return (
            <div key={day}>
              <DayHeader day={day} rows={rows} expanded={expanded} onToggle={() => toggle(day)} />
              {expanded && (
                <div className="mt-0.5 space-y-0.5">
                  {rows.map((r, i) => (
                    <TradeRow key={`${r.ts}-${i}`} t={r} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
