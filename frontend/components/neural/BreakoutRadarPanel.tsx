"use client";

/**
 * BreakoutRadarPanel v2 — Kırılım Radarı (destek/direnç bölgesinin ana görseli).
 *
 * Backend: GET /api/fakeout/assess/{symbol} (fakeout_service v3+).
 * Görsel çekirdek: DEDEKTÖRLE AYNI 5m mumlar üzerinde gerçek mini-grafik —
 * S/R seviyeleri, kanal bandı, kırılım mumu vurgusu, ±1 ATR hedef/stop
 * çizgileri (yarışın görsel karşılığı) + ışıltılı ikiz 1-100 göstergeler.
 *
 * Dürüstlük: ön-tahmin "yaklaşık" etiketlidir; gösterge değerleri OOS-doğrulanmış
 * modellerden gelir, süs değildir.
 */

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { buildApiUrl } from "@/lib/api/base";
import { useNeuralLocale } from "@/components/neural/i18n";
import ShadowAccuracyCard from "@/components/neural/ShadowAccuracyCard";

// ── Tipler (backend sözleşmesi) ────────────────────────────────────────────

interface LevelInfo {
  price: number;
  touches: number;
  age_bars: number;
  attempts: number;
  distance_points: number;
  distance_atr: number;
  distance_pct: number;
}

interface LevelsSnapshot {
  price: number;
  atr: number;
  resistance: LevelInfo | null;
  support: LevelInfo | null;
  channel?: { upper: number; lower: number; slope_atr_per_bar: number; r2: number };
}

interface SideForecast {
  level_kind: string;
  level_price: number;
  distance_points: number | null;
  distance_atr: number | null;
  distance_pct: number | null;
  breakout_score: number | null;
  fake_probability: number;
  genuine_probability: number;
}

interface Candle { o: number; h: number; l: number; c: number }

interface DetectorOut {
  call: "fake" | "genuine" | "abstain" | "pending_next_bar";
  stage?: "pending" | "confirm_bar" | "wave_k2" | "resolved_observed";
  p_fake?: number | null;
  oos?: { fake_call?: { precision: number }; genuine_call?: { precision: number } };
}

interface Confirmation {
  next_bar_confirm: boolean | null;
  retest: "hold" | "fail" | "none" | "pending";
}

interface Assessment {
  status: "assessed" | "no_breakout" | "no_rules" | "unavailable";
  levels?: LevelsSnapshot;
  pre_forecast?: { up: SideForecast | null; down: SideForecast | null };
  candles?: Candle[];
  breakout?: {
    direction: "up" | "down"; level_kind: string; level_price: number;
    bars_ago: number; touches: number; bar_offset_from_end?: number;
  };
  breakout_score?: number | null;
  genuine_probability?: number | null;
  fake_probability?: number;
  recommendation?: "fade_candidate" | "avoid_breakout_direction" | "neutral_no_trade" | "breakout_leaning_genuine";
  detector?: DetectorOut | null;
  confirmation?: Confirmation;
  matched_rules?: { rule: string; pooled_fake_rate: number }[];
  base_fake_rate?: number;
}

const POLL_MS = 45_000;

// ── Işıltılı yarım-daire gösterge (1-100) ──────────────────────────────────

function Gauge({ value, label, color, colorDim, sub, gid }: {
  value: number; label: string; color: string; colorDim: string; sub?: string; gid: string;
}) {
  const v = Math.max(1, Math.min(100, Math.round(value)));
  const R = 46, CX = 60, CY = 66;
  const C = Math.PI * R;
  const ang = Math.PI * (1 - v / 100);                     // uç noktanın açısı
  const ex = CX + R * Math.cos(ang), ey = CY - R * Math.sin(ang);
  const hot = v >= 70;
  return (
    <div className="relative flex flex-col items-center rounded-2xl border border-white/[0.05] bg-gradient-to-b from-white/[0.03] to-transparent px-2 pt-3 pb-2">
      <svg viewBox="0 0 120 80" className="w-full max-w-[185px]">
        <defs>
          <linearGradient id={`${gid}-arc`} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor={colorDim} />
            <stop offset="1" stopColor={color} />
          </linearGradient>
          <filter id={`${gid}-glow`} x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="2.6" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <path d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`} fill="none"
          stroke="rgba(255,255,255,0.06)" strokeWidth="10" strokeLinecap="round" />
        <motion.path
          d={`M ${CX - R} ${CY} A ${R} ${R} 0 0 1 ${CX + R} ${CY}`}
          fill="none" stroke={`url(#${gid}-arc)`} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={C}
          initial={{ strokeDashoffset: C }}
          animate={{ strokeDashoffset: C * (1 - v / 100) }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
          filter={hot ? `url(#${gid}-glow)` : undefined}
        />
        {/* uç ışığı */}
        <motion.circle cx={ex} cy={ey} r={4} fill={color} filter={`url(#${gid}-glow)`}
          initial={{ opacity: 0 }} animate={{ opacity: [0.7, 1, 0.7] }}
          transition={{ delay: 1.0, repeat: Infinity, duration: 1.8 }} />
        {[0, 25, 50, 75, 100].map((t) => {
          const a = Math.PI * (1 - t / 100);
          const x1 = CX + (R + 8) * Math.cos(a), y1 = CY - (R + 8) * Math.sin(a);
          const x2 = CX + (R + 11) * Math.cos(a), y2 = CY - (R + 11) * Math.sin(a);
          return <line key={t} x1={x1} y1={y1} x2={x2} y2={y2}
            stroke="rgba(255,255,255,0.18)" strokeWidth="1.4" />;
        })}
        <text x="10" y="78" fontSize="6.5" fill="rgba(255,255,255,0.3)" fontFamily="ui-monospace,monospace">0</text>
        <text x="106" y="78" fontSize="6.5" fill="rgba(255,255,255,0.3)" fontFamily="ui-monospace,monospace">100</text>
        <text x={CX} y="54" textAnchor="middle" fontSize="26" fontWeight="800" fill={color}
          fontFamily="ui-monospace,monospace">{v}</text>
        <text x={CX} y="66" textAnchor="middle" fontSize="6.5" letterSpacing="2"
          fill="rgba(255,255,255,0.4)" fontFamily="ui-monospace,monospace">/100</text>
      </svg>
      <div className="mt-0.5 text-center">
        <div className="font-mono text-[9px] font-bold tracking-[0.2em] text-gray-300">{label}</div>
        {sub && <div className="mt-0.5 font-mono text-[8px] tracking-[0.1em] text-gray-600">{sub}</div>}
      </div>
    </div>
  );
}

// ── Gerçek mum grafiği + seviye/hedef katmanları ───────────────────────────

function CandleRadarChart({ data }: { data: Assessment }) {
  const { L } = useNeuralLocale();
  const candles = data.candles ?? [];
  const lv = data.levels!;
  const bo = data.status === "assessed" ? data.breakout : undefined;
  const W = 360, H = 252, PADL = 8, PADR = 58, PADT = 12, PADB = 12;
  const plotW = W - PADL - PADR, plotH = H - PADT - PADB;

  const dom = useMemo(() => {
    const ps: number[] = [];
    candles.forEach((k) => { ps.push(k.h, k.l); });
    if (lv.resistance) ps.push(lv.resistance.price);
    if (lv.support) ps.push(lv.support.price);
    if (lv.channel) ps.push(lv.channel.upper, lv.channel.lower);
    if (bo) ps.push(bo.level_price + lv.atr, bo.level_price - lv.atr);
    const lo = Math.min(...ps), hi = Math.max(...ps);
    const pad = (hi - lo) * 0.06 || 1;
    return { lo: lo - pad, hi: hi + pad };
  }, [candles, lv, bo]);

  const y = (p: number) => PADT + (1 - (p - dom.lo) / (dom.hi - dom.lo)) * plotH;
  const n = Math.max(candles.length, 1);
  const step = plotW / n;
  const cw = Math.max(2, step * 0.62);
  const x = (i: number) => PADL + i * step + step / 2;

  const fmt = (p: number) => p.toLocaleString(undefined, { maximumFractionDigits: lv.price > 500 ? 0 : 2 });
  const last = candles[candles.length - 1];
  const lastY = last ? y(last.c) : y(lv.price);
  const boIdx = bo ? candles.length - 1 - (bo.bar_offset_from_end ?? bo.bars_ago) : -1;

  // Seviye çizgisi çizici
  const LevelLine = ({ p, color, dash, label, broken, glowId }: {
    p: number; color: string; dash?: string; label: string; broken?: boolean; glowId: string;
  }) => (
    <g>
      <line x1={PADL} x2={W - PADR + 4} y1={y(p)} y2={y(p)} stroke={color}
        strokeWidth={broken ? 2.2 : 1.1} strokeDasharray={dash ?? "none"}
        strokeOpacity={broken ? 1 : 0.75} filter={broken ? `url(#${glowId})` : undefined} />
      <text x={PADL + 3} y={y(p) - 3.5} fontSize="7.5" fill={color} letterSpacing="1.2"
        fontFamily="ui-monospace,monospace" fontWeight={broken ? 700 : 400}>
        {broken ? "⚡ " : ""}{label}
      </text>
      <text x={W - 4} y={y(p) + 2.5} fontSize="8" fill={color} textAnchor="end"
        fontFamily="ui-monospace,monospace">{fmt(p)}</text>
    </g>
  );

  const dirUp = bo?.direction === "up";
  const tpPrice = bo ? bo.level_price + (dirUp ? 1 : -1) * lv.atr : null;
  const slPrice = bo ? bo.level_price - (dirUp ? 1 : -1) * lv.atr : null;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-gradient-to-b from-[#0a1020] to-[#060a14] p-1.5">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <defs>
          <filter id="brp-glow" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="2.2" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <linearGradient id="brp-tp" x1="0" y1={dirUp ? "1" : "0"} x2="0" y2={dirUp ? "0" : "1"}>
            <stop offset="0" stopColor="#34d399" stopOpacity="0" />
            <stop offset="1" stopColor="#34d399" stopOpacity="0.14" />
          </linearGradient>
          <linearGradient id="brp-sl" x1="0" y1={dirUp ? "0" : "1"} x2="0" y2={dirUp ? "1" : "0"}>
            <stop offset="0" stopColor="#f87171" stopOpacity="0" />
            <stop offset="1" stopColor="#f87171" stopOpacity="0.14" />
          </linearGradient>
        </defs>

        {/* ızgara */}
        {[0.2, 0.4, 0.6, 0.8].map((f) => (
          <line key={f} x1={PADL} x2={W - PADR + 4} y1={PADT + f * plotH} y2={PADT + f * plotH}
            stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
        ))}

        {/* kanal bandı */}
        {lv.channel && (
          <g>
            <rect x={PADL} width={plotW + 4} y={Math.min(y(lv.channel.upper), y(lv.channel.lower))}
              height={Math.abs(y(lv.channel.lower) - y(lv.channel.upper))}
              fill="#818cf8" fillOpacity="0.05" />
            <LevelLine p={lv.channel.upper} color="#818cf8" dash="5 4"
              label={L("KANAL ÜSTÜ", "CHAN TOP")} glowId="brp-glow"
              broken={bo?.level_kind === "channel_upper"} />
            <LevelLine p={lv.channel.lower} color="#818cf8" dash="5 4"
              label={L("KANAL ALTI", "CHAN BOT")} glowId="brp-glow"
              broken={bo?.level_kind === "channel_lower"} />
          </g>
        )}

        {/* canlı kırılımda ±1 ATR hedef/stop bölgeleri */}
        {bo && tpPrice !== null && slPrice !== null && (
          <g>
            <rect x={PADL} width={plotW + 4}
              y={Math.min(y(tpPrice), y(bo.level_price))}
              height={Math.abs(y(tpPrice) - y(bo.level_price))} fill="url(#brp-tp)" />
            <rect x={PADL} width={plotW + 4}
              y={Math.min(y(slPrice), y(bo.level_price))}
              height={Math.abs(y(slPrice) - y(bo.level_price))} fill="url(#brp-sl)" />
            <line x1={PADL} x2={W - PADR + 4} y1={y(tpPrice)} y2={y(tpPrice)}
              stroke="#34d399" strokeWidth="1.2" strokeDasharray="2 3" strokeOpacity="0.9" />
            <text x={W - 4} y={y(tpPrice) + 2.5} fontSize="7.5" fill="#34d399" textAnchor="end"
              fontFamily="ui-monospace,monospace">{L("GERÇEK✓", "REAL✓")} {fmt(tpPrice)}</text>
            <line x1={PADL} x2={W - PADR + 4} y1={y(slPrice)} y2={y(slPrice)}
              stroke="#f87171" strokeWidth="1.2" strokeDasharray="2 3" strokeOpacity="0.9" />
            <text x={W - 4} y={y(slPrice) + 2.5} fontSize="7.5" fill="#f87171" textAnchor="end"
              fontFamily="ui-monospace,monospace">{L("SAHTE✗", "FAKE✗")} {fmt(slPrice)}</text>
          </g>
        )}

        {/* S/R seviyeleri */}
        {lv.resistance && (
          <LevelLine p={lv.resistance.price} color="#f87171"
            label={`${L("DİRENÇ", "RES")} ×${lv.resistance.touches}`} glowId="brp-glow"
            broken={bo?.level_kind === "resistance"} />
        )}
        {lv.support && (
          <LevelLine p={lv.support.price} color="#34d399"
            label={`${L("DESTEK", "SUP")} ×${lv.support.touches}`} glowId="brp-glow"
            broken={bo?.level_kind === "support"} />
        )}

        {/* mumlar */}
        {candles.map((k, i) => {
          const up = k.c >= k.o;
          const col = up ? "#34d399" : "#f87171";
          const bodyT = y(Math.max(k.o, k.c)), bodyB = y(Math.min(k.o, k.c));
          const isBo = i === boIdx;
          return (
            <g key={i}>
              <line x1={x(i)} x2={x(i)} y1={y(k.h)} y2={y(k.l)} stroke={col} strokeWidth="1" />
              <rect x={x(i) - cw / 2} width={cw} y={bodyT}
                height={Math.max(1.2, bodyB - bodyT)} fill={col} rx="0.8"
                stroke={isBo ? "#fbbf24" : "none"} strokeWidth={isBo ? 1.4 : 0} />
              {isBo && (
                <motion.text x={x(i)} y={dirUp ? y(k.h) - 5 : y(k.l) + 11} textAnchor="middle"
                  fontSize="10" fill="#fbbf24" filter="url(#brp-glow)"
                  animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.2 }}>
                  ⚡
                </motion.text>
              )}
            </g>
          );
        })}

        {/* canlı fiyat çizgisi + etiket */}
        <motion.line x1={PADL} x2={W - PADR + 4} y1={lastY} y2={lastY} stroke="#22d3ee"
          strokeWidth="1.3" strokeDasharray="4 3"
          animate={{ opacity: [0.55, 1, 0.55] }} transition={{ repeat: Infinity, duration: 2.2 }} />
        <rect x={W - PADR + 6} y={lastY - 8} width={PADR - 8} height={16} rx="4"
          fill="#0e7490" fillOpacity="0.9" />
        <text x={W - PADR + 6 + (PADR - 8) / 2} y={lastY + 3.5} textAnchor="middle" fontSize="8.5"
          fontWeight="700" fill="#e0faff" fontFamily="ui-monospace,monospace">
          {fmt(last ? last.c : lv.price)}
        </text>
        <motion.circle cx={x(candles.length - 1)} cy={lastY} r={3} fill="#22d3ee"
          filter="url(#brp-glow)" animate={{ r: [2.6, 4.4, 2.6] }}
          transition={{ repeat: Infinity, duration: 2.2 }} />
      </svg>

      {/* mini lejant */}
      <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-0.5 pb-1 font-mono text-[7.5px] tracking-[0.12em] text-gray-600">
        <span><span className="text-red-300">──</span> {L("DİRENÇ", "RESISTANCE")}</span>
        <span><span className="text-emerald-300">──</span> {L("DESTEK", "SUPPORT")}</span>
        <span><span className="text-indigo-300">┅┅</span> {L("KANAL", "CHANNEL")}</span>
        {bo && <span><span className="text-amber-300">⚡</span> {L("KIRILIM MUMU", "BREAKOUT BAR")}</span>}
        {bo && <span>{L("bantlar: ±1 ATR yarış hedefleri", "bands: ±1 ATR race targets")}</span>}
      </div>
    </div>
  );
}

// ── Mesafe satırı ──────────────────────────────────────────────────────────

function DistanceRow({ side, fc }: { side: "up" | "down"; fc: SideForecast }) {
  const { L } = useNeuralLocale();
  const distAtr = Math.abs(fc.distance_atr ?? 9);
  const closeness = Math.max(0, Math.min(100, Math.round((1 - distAtr / 3) * 100)));
  const near = distAtr <= 0.5;
  const color = side === "up" ? "#f87171" : "#34d399";
  const kindLabel = fc.level_kind.startsWith("channel")
    ? (side === "up" ? L("KANAL ÜSTÜ", "CHANNEL TOP") : L("KANAL ALTI", "CHANNEL BOT"))
    : side === "up" ? L("DİRENÇ", "RESISTANCE") : L("DESTEK", "SUPPORT");
  return (
    <div className={`rounded-xl border px-3 py-2.5 ${near ? "border-amber-400/40 bg-amber-400/[0.05]" : "border-white/[0.06] bg-white/[0.02]"}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[9px] tracking-[0.18em]" style={{ color }}>
          {side === "up" ? "▲" : "▼"} {kindLabel} {fc.level_price.toLocaleString(undefined, { maximumFractionDigits: 1 })}
        </span>
        {near && (
          <motion.span animate={{ opacity: [1, 0.35, 1] }} transition={{ repeat: Infinity, duration: 1.1 }}
            className="font-mono text-[8px] tracking-[0.2em] text-amber-300">
            ⚡ {L("KIRILIM YAKIN", "BREAK IMMINENT")}
          </motion.span>
        )}
      </div>
      <div className="mt-1.5 flex items-center gap-2">
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
          <motion.div className="h-full rounded-full" style={{ background: color }}
            initial={{ width: 0 }} animate={{ width: `${closeness}%` }} transition={{ duration: 0.9 }} />
        </div>
        <span className="shrink-0 font-mono text-[9px] text-gray-400">
          {Math.abs(fc.distance_points ?? 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}p · {distAtr.toFixed(2)} ATR · %{Math.abs(fc.distance_pct ?? 0).toFixed(2)}
        </span>
      </div>
      <div className="mt-1.5 flex items-center gap-3 font-mono text-[9px]">
        <span className="text-emerald-300">{L("GERÇEK", "GENUINE")} {Math.round(fc.genuine_probability)}</span>
        <span className="text-red-300">{L("SAHTE", "FAKE")} {Math.round(fc.fake_probability)}</span>
        {typeof fc.breakout_score === "number" && (
          <span className="text-gray-500">{L("skor", "score")} {fc.breakout_score > 0 ? `+${fc.breakout_score}` : fc.breakout_score}</span>
        )}
        <span className="ml-auto text-[8px] tracking-[0.14em] text-gray-600">{L("ŞİMDİ KIRILSA (≈)", "IF BROKEN NOW (≈)")}</span>
      </div>
    </div>
  );
}

// ── Ana bileşen ────────────────────────────────────────────────────────────

export default function BreakoutRadarPanel({ symbol }: { symbol: string }) {
  const { L } = useNeuralLocale();
  const [data, setData] = useState<Assessment | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 12_000);
        const res = await fetch(buildApiUrl(`/api/fakeout/assess/${symbol}`), { signal: ctrl.signal });
        clearTimeout(t);
        if (!res.ok) throw new Error(String(res.status));
        const json = (await res.json()) as Assessment;
        if (alive) { setData(json); setError(false); }
      } catch { if (alive) setError(true); }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => { alive = false; clearInterval(id); };
  }, [symbol]);

  const live = data?.status === "assessed";
  const armedSide: "up" | "down" = useMemo(() => {
    if (live && data?.breakout) return data.breakout.direction;
    const up = data?.pre_forecast?.up, dn = data?.pre_forecast?.down;
    if (up && dn) return Math.abs(up.distance_atr ?? 9) <= Math.abs(dn.distance_atr ?? 9) ? "up" : "down";
    return up ? "up" : "down";
  }, [data, live]);

  if (!data && !error) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-52 rounded-2xl bg-white/[0.04]" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-28 rounded-2xl bg-white/[0.03]" />
          <div className="h-28 rounded-2xl bg-white/[0.03]" />
        </div>
      </div>
    );
  }
  if (error || !data || data.status === "unavailable") {
    return <p className="text-[12px] text-gray-500">{L("Kırılım radarına ulaşılamadı — backend kapalı veya eski sürüm olabilir.", "Breakout radar unreachable — backend may be offline or outdated.")}</p>;
  }
  if (data.status === "no_rules") {
    return <p className="text-[12px] text-gray-500">{L("Bu sembol için doğrulanmış kırılım kuralı yok.", "No validated breakout rules for this symbol yet.")}</p>;
  }
  if (!data.levels) {
    return <p className="text-[12px] text-gray-500">{L("Seviye verisi bekleniyor…", "Waiting for level data…")}</p>;
  }

  const fc = live
    ? { genuine: data.genuine_probability ?? (100 - (data.fake_probability ?? 66)), fake: data.fake_probability ?? 66 }
    : (() => {
        const side = data.pre_forecast?.[armedSide];
        return { genuine: side?.genuine_probability ?? 100 - (data.base_fake_rate ?? 66), fake: side?.fake_probability ?? data.base_fake_rate ?? 66 };
      })();

  const REC_TEXT: Record<string, [string, string]> = {
    fade_candidate: ["FADE ADAYI — KLİMAKS KIRILIM, TERS YÖN KANITI", "FADE CANDIDATE — CLIMAX BREAK, COUNTER-DIRECTION EVIDENCE"],
    avoid_breakout_direction: ["KIRILIM YÖNÜNDE İŞLEM AÇMA", "DO NOT TRADE THE BREAKOUT DIRECTION"],
    neutral_no_trade: ["BELİRSİZ — TABAN RİSK GEÇERLİ", "UNCERTAIN — BASE RISK APPLIES"],
    breakout_leaning_genuine: ["GERÇEĞE YATKIN — TEK BAŞINA EDGE DEĞİL", "LEANS GENUINE — NOT AN EDGE ALONE"],
  };
  const recColor = data.recommendation === "fade_candidate" ? "border-cyan-400/30 bg-cyan-400/[0.06] text-cyan-300"
    : data.recommendation === "avoid_breakout_direction" ? "border-red-400/30 bg-red-400/[0.06] text-red-300"
    : data.recommendation === "breakout_leaning_genuine" ? "border-emerald-400/30 bg-emerald-400/[0.06] text-emerald-300"
    : "border-amber-400/30 bg-amber-400/[0.06] text-amber-300";

  const conf = data.confirmation;
  const confirmChip = conf?.next_bar_confirm === true ? ["✓ " + L("sonraki bar teyitli", "next bar confirmed"), "text-emerald-300"]
    : conf?.next_bar_confirm === false ? ["✗ " + L("teyit gelmedi", "no confirmation"), "text-red-300"]
    : ["… " + L("teyit bekleniyor", "confirm pending"), "text-gray-500"];
  const retestChip = conf?.retest === "hold" ? [L("retest tuttu", "retest held"), "text-emerald-300"]
    : conf?.retest === "fail" ? [L("retest kırdı", "retest failed"), "text-red-300"]
    : conf?.retest === "none" ? [L("retest olmadı", "no retest"), "text-gray-400"]
    : [L("retest bekleniyor", "retest pending"), "text-gray-500"];

  return (
    <div className="space-y-3">
      {/* mod şeridi */}
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <motion.span className={`h-1.5 w-1.5 rounded-full ${live ? "bg-red-400" : "bg-cyan-400"}`}
            animate={{ opacity: [1, 0.3, 1] }} transition={{ repeat: Infinity, duration: live ? 0.9 : 2.2 }} />
          <span className="font-mono text-[9px] tracking-[0.25em] text-gray-400">
            {live ? L("CANLI KIRILIM DEĞERLENDİRMESİ", "LIVE BREAKOUT ASSESSMENT") : L("RADAR BEKLEMEDE — SEVİYELER İZLENİYOR", "RADAR ARMED — WATCHING LEVELS")}
          </span>
        </span>
        <span className="font-mono text-[8px] tracking-[0.15em] text-gray-600">OOS·5m·{symbol.split(".")[0]}</span>
      </div>

      {/* GERÇEK MUM GRAFİĞİ + seviye/hedef katmanları */}
      {data.candles && data.candles.length > 5 ? (
        <CandleRadarChart data={data} />
      ) : (
        <p className="text-[11px] text-gray-600">{L("Grafik verisi bekleniyor (backend yeniden başlatılınca gelir)…", "Waiting for chart data (arrives after backend restart)…")}</p>
      )}

      {/* canlı kırılım banner'ı */}
      {live && data.breakout && (
        <div className={`rounded-xl border px-4 py-3 ${recColor}`}>
          <div className="font-mono text-[10px] tracking-[0.18em]">
            ⚡ {data.breakout.direction === "up" ? "▲" : "▼"} {L(...(REC_TEXT[data.recommendation ?? "neutral_no_trade"] as [string, string]))}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-2">
            {data.detector?.call === "pending_next_bar" && (
              <motion.span animate={{ opacity: [1, 0.4, 1] }} transition={{ repeat: Infinity, duration: 1.2 }}
                className="rounded-full border border-amber-400/30 bg-amber-400/[0.08] px-2.5 py-0.5 font-mono text-[9px] text-amber-300">
                ⏳ {L("AI DEDEKTÖR: TEYİT BARI BEKLENİYOR (~5dk)", "AI DETECTOR: AWAITING CONFIRM BAR (~5min)")}
              </motion.span>
            )}
            {data.detector?.call === "fake" && (
              <span className="rounded-full border border-red-400/40 bg-red-400/[0.1] px-2.5 py-0.5 font-mono text-[9px] font-bold text-red-300">
                {data.detector.stage === "resolved_observed"
                  ? "📉 " + L("SONUÇLANDI: SAHTE ÇIKTI (gözlem)", "RESOLVED: WAS FAKE (observed)")
                  : "🤖 " + L(`AI ${data.detector.stage === "wave_k2" ? "DALGA" : "DEDEKTÖR"}: SAHTE — OOS %${Math.round(data.detector.oos?.fake_call?.precision ?? 70)} isabet`,
                        `AI ${data.detector.stage === "wave_k2" ? "WAVE" : "DETECTOR"}: FAKE — ${Math.round(data.detector.oos?.fake_call?.precision ?? 70)}% OOS`)}
              </span>
            )}
            {data.detector?.call === "genuine" && (
              <span className="rounded-full border border-emerald-400/40 bg-emerald-400/[0.1] px-2.5 py-0.5 font-mono text-[9px] font-bold text-emerald-300">
                {data.detector.stage === "resolved_observed"
                  ? "📈 " + L("SONUÇLANDI: GERÇEK ÇIKTI (gözlem)", "RESOLVED: WAS GENUINE (observed)")
                  : "🤖 " + L(`AI ${data.detector.stage === "wave_k2" ? "DALGA" : "DEDEKTÖR"}: GERÇEK — OOS %${Math.round(data.detector.oos?.genuine_call?.precision ?? 83)} isabet`,
                        `AI ${data.detector.stage === "wave_k2" ? "WAVE" : "DETECTOR"}: GENUINE — ${Math.round(data.detector.oos?.genuine_call?.precision ?? 83)}% OOS`)}
              </span>
            )}
            {data.detector?.call === "abstain" && (
              <span className="rounded-full border border-white/[0.1] bg-white/[0.03] px-2.5 py-0.5 font-mono text-[9px] text-gray-400">
                🤖 {L("AI DEDEKTÖR: KARARSIZ BÖLGE", "AI DETECTOR: ABSTAIN ZONE")}
              </span>
            )}
            <span className={`rounded-full border border-white/[0.08] bg-black/20 px-2.5 py-0.5 font-mono text-[9px] ${confirmChip[1]}`}>{confirmChip[0]}</span>
            <span className={`rounded-full border border-white/[0.08] bg-black/20 px-2.5 py-0.5 font-mono text-[9px] ${retestChip[1]}`}>{retestChip[0]}</span>
            {typeof data.breakout_score === "number" && (
              <span className="rounded-full border border-white/[0.08] bg-black/20 px-2.5 py-0.5 font-mono text-[9px] text-gray-300">
                {L("skor", "score")} {data.breakout_score > 0 ? `+${data.breakout_score}` : data.breakout_score}
              </span>
            )}
          </div>
        </div>
      )}

      {/* ikiz göstergeler */}
      <div className="grid grid-cols-2 gap-3">
        <Gauge value={fc.genuine} color="#34d399" colorDim="#0d9488" gid="brp-g1"
          label={L("GERÇEK KIRILIM TESPİTİ", "GENUINE BREAK DETECTION")}
          sub={live ? L("canlı kırılım", "live break") : L(`${armedSide === "up" ? "direnç" : "destek"} · şimdi kırılsa ≈`, `${armedSide === "up" ? "resistance" : "support"} · if broken now ≈`)} />
        <Gauge value={fc.fake} color="#f87171" colorDim="#b91c1c" gid="brp-g2"
          label={L("SAHTE KIRILIM TESPİTİ", "FAKE BREAK DETECTION")}
          sub={live ? L("canlı kırılım", "live break") : L("OOS-kalibre kova", "OOS-calibrated bucket")} />
      </div>

      {/* mesafe satırları */}
      <div className="space-y-2">
        {data.pre_forecast?.up && <DistanceRow side="up" fc={data.pre_forecast.up} />}
        {data.pre_forecast?.down && <DistanceRow side="down" fc={data.pre_forecast.down} />}
      </div>

      {live && data.matched_rules && data.matched_rules.length > 0 && (
        <div className="space-y-1">
          <div className="font-mono text-[8px] tracking-[0.2em] text-gray-600">{L("EŞLEŞEN KANIT KURALLARI", "MATCHED EVIDENCE RULES")}</div>
          {data.matched_rules.slice(0, 2).map((r) => (
            <div key={r.rule} className="flex items-center justify-between gap-2 rounded-lg border border-white/[0.05] bg-white/[0.02] px-2.5 py-1">
              <code className="truncate text-[9px] text-gray-400">{r.rule}</code>
              <span className="shrink-0 font-mono text-[9px] text-gray-300">%{Math.round(r.pooled_fake_rate)}</span>
            </div>
          ))}
        </div>
      )}

      {/* sanal işlem doğrulama karnesi — dedektör çağrıları gerçekten tutuyor mu? */}
      <div className="border-t border-white/[0.05] pt-3">
        <ShadowAccuracyCard symbol={symbol} sources={["fakeout"]} />
      </div>
    </div>
  );
}
