"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { PanelInfoButton } from "../PanelInfoButton";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  ArrowUpRightIcon as TrendingUp,
  ActivityIcon as Activity,
  ChartsIcon as BarChart3,
  TargetIcon as Target,
  AnalysisIcon as Layers,
  ChartsIcon as Gauge,
  SignalsIcon as Volume2,
  SecurityShieldIcon as Shield,
  RotateIcon as RefreshCw,
  AlertIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle,
  CloseIcon as XCircle,
  ArrowUpRightIcon as ArrowUpRight,
  ArrowDownRightIcon as ArrowDownRight,
  MinusIcon as Minus,
} from "../ui/CustomIcons";
import { EmelIcon, PulseIcon, SignalsIcon } from "../ui/CustomIcons";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface CheckItem {
  id: number; name: string; subtitle: string;
  status: "pass" | "warning" | "fail"; direction: "up" | "down" | "neutral";
  color: "green" | "yellow" | "red"; label: string;
  details: Record<string, any>; comment: string;
}

interface EmelData {
  symbol: string; timeframe: string; signal: string; confidence: number; price: number;
  checks: CheckItem[];
  summary: { green_count: number; yellow_count: number; red_count: number; decision: string; rejections: string[]; entry_conditions: string[]; };
}

interface EmelPanelProps { symbol?: string; onSwitchMode?: () => void; }

const SYMBOLS = [{ key: "NDX.INDX", label: "NASDAQ" }, { key: "XAUUSD", label: "XAUUSD" }, { key: "GDAXI.INDX", label: "DAX" }, { key: "CL.COMM", label: "US Oil" }];

const CHECK_ICONS: Record<number, any> = {
  1: TrendingUp, 2: Activity, 3: Layers, 4: Target, 5: BarChart3, 6: Gauge, 7: Volume2, 8: SignalsIcon, 9: Shield,
};

const FONT = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
const N = {
  g: { c: "#16C784", bg: "rgba(22,199,132,0.05)", b: "rgba(22,199,132,0.15)", gw: "rgba(22,199,132,0.06)" },
  y: { c: "#F5A623", bg: "rgba(245,166,35,0.05)", b: "rgba(245,166,35,0.15)", gw: "rgba(245,166,35,0.06)" },
  r: { c: "#EA3943", bg: "rgba(234,57,67,0.05)", b: "rgba(234,57,67,0.15)", gw: "rgba(234,57,67,0.06)" },
  p: { c: "#4F8CFF", bg: "rgba(79,140,255,0.05)", b: "rgba(79,140,255,0.15)", gw: "rgba(79,140,255,0.06)" },
};

function cn(color: string) { return color === "green" ? N.g : color === "red" ? N.r : N.y; }

function MtfPills({ tf }: { tf: Array<{ tf: string; dir: string }> }) {
  return (
    <div className="flex gap-1.5 flex-wrap mt-1">
      {tf.map((t) => {
        const c = t.dir === "up" ? N.g : t.dir === "down" ? N.r : N.y;
        const I = t.dir === "up" ? ArrowUpRight : t.dir === "down" ? ArrowDownRight : Minus;
        return (
          <div key={t.tf} className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono font-bold"
            style={{ background: c.bg, border: `1px solid ${c.b}`, color: c.c }}>
            <I className="w-3 h-3" />{t.tf}
          </div>
        );
      })}
    </div>
  );
}

function DetailRow({ k, v }: { k: string; v: any }) {
  if (k === "timeframes" && Array.isArray(v)) return <MtfPills tf={v} />;
  const display = typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2))
    : typeof v === "object" && v !== null ? Object.values(v).join(", ") : String(v);
  return (
    <div className="flex justify-between items-center">
      <span className="text-white/30 capitalize text-[10px]">{k.replace(/_/g, " ")}</span>
      <span className="text-white/65 font-semibold text-[10px]">{display}</span>
    </div>
  );
}

function Badge({ n, color }: { n: number; color: string }) {
  return (
    <div className="w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-black font-mono shrink-0"
      style={{ background: `${color}15`, border: `1px solid ${color}30`, color, textShadow: `0 0 6px ${color}50` }}>
      {n}
    </div>
  );
}

function StatusIcon({ s }: { s: string }) {
  if (s === "pass") return <CheckCircle className="w-4 h-4" style={{ color: N.g.c }} />;
  if (s === "warning") return <AlertTriangle className="w-4 h-4" style={{ color: N.y.c }} />;
  if (s === "fail") return <XCircle className="w-4 h-4" style={{ color: N.r.c }} />;
  return null;
}

export default function EmelPanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: EmelPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<EmelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");
  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "emel");

  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener("dashboard-refresh", handler);
    return () => window.removeEventListener("dashboard-refresh", handler);
  }, [activeSymbol, timeframe]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) setData(json);
    } catch (e) { console.error("EMEL fetch error:", e); }
    finally { setLoading(false); }
  };

  useEffect(() => { if (wsData) { setData(wsData); setLoading(false); } }, [wsData]);
  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) { const iv = setInterval(fetchData, 120000); return () => clearInterval(iv); }
  }, [activeSymbol, timeframe, wsConnected]);

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="h-8 rounded-xl w-1/3 mb-6" style={{ background: 'rgba(255,255,255,0.04)' }} />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[...Array(9)].map((_, i) => <div key={i} className="h-32 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)' }} />)}
        </div>
      </div>
    );
  }

  const sig = data?.signal === "BUY" ? N.g : data?.signal === "SELL" ? N.r : N.y;
  const gc = data?.summary.green_count || 0;
  const yc = data?.summary.yellow_count || 0;
  const rc = data?.summary.red_count || 0;
  const tot = gc + yc + rc || 1;

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: '#0B0F17', border: '1px solid rgba(255,255,255,0.06)' }}>

      {/* ── HEADER ── */}
      <div className="flex items-center justify-between px-5 py-3" style={{ background: '#111827', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'rgba(79,140,255,0.12)', border: '1px solid rgba(79,140,255,0.25)' }}>
              <EmelIcon size={20} style={{ color: N.p.c }} />
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full" style={{ background: sig.c }} />
          </div>
          <div>
            <h2 style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: N.p.c }}>{t("emel.title")}</h2>
            <p style={{ fontFamily: FONT, fontSize: 10, color: 'rgba(155,170,195,0.6)', letterSpacing: '0.1em', textTransform: 'uppercase' as const }}>STRATEGIC CONTROL · 9 CHECKPOINTS</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid rgba(168,85,247,0.15)' }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setActiveSymbol(s.key)}
                className="px-3 py-1.5 text-[10px] font-bold font-mono transition-all"
                style={{ backgroundColor: activeSymbol === s.key ? 'rgba(168,85,247,0.2)' : 'transparent', color: activeSymbol === s.key ? N.p.c : 'rgba(255,255,255,0.3)', borderRight: '1px solid rgba(168,85,247,0.1)' }}>
                {s.label}
              </button>
            ))}
          </div>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg appearance-none cursor-pointer" style={{ backgroundColor: 'rgba(168,85,247,0.08)', color: 'rgba(192,132,252,0.6)', border: '1px solid rgba(168,85,247,0.15)' }}>
            <option value="15m">15m</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option>
          </select>
          <button onClick={fetchData} className="p-1.5 rounded-lg" style={{ backgroundColor: 'rgba(168,85,247,0.08)', border: '1px solid rgba(168,85,247,0.15)' }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: 'rgba(192,132,252,0.5)' }} />
          </button>
          <PanelInfoButton panelId="emel-panel" />
          {onSwitchMode && (
            <button onClick={onSwitchMode} className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold font-mono" style={{ background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.25)', color: '#fbbf24' }}>
              <PulseIcon size={12} style={{ color: '#fbbf24' }} /> PULSE
            </button>
          )}
        </div>
      </div>

      {/* ── HERO SIGNAL STRIP ── */}
      {data && (
        <div className="px-5 py-4 flex items-center gap-5 flex-wrap" style={{ background: 'rgba(0,0,0,0.2)' }}>
          <div className="rounded-xl px-5 py-2.5 text-center" style={{ background: `${sig.c}08`, border: `1px solid ${sig.b}` }}>
            <p style={{ fontFamily: FONT, fontSize: 9, color: `${sig.c}70`, letterSpacing: '0.2em', textTransform: 'uppercase' as const, marginBottom: 4 }}>Signal</p>
            <p style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px', color: sig.c }}>{data.signal}</p>
          </div>
          <div className="text-center">
            <p style={{ fontFamily: FONT, fontSize: 9, color: 'rgba(155,170,195,0.5)', letterSpacing: '0.2em', textTransform: 'uppercase' as const, marginBottom: 4 }}>Confidence</p>
            <p style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, letterSpacing: '-0.5px', color: N.p.c }}>%{data.confidence.toFixed(0)}</p>
          </div>
          <div className="text-center">
            <p className="text-[8px] uppercase tracking-[0.3em] mb-0.5" style={{ color: 'rgba(255,255,255,0.25)' }}>Price</p>
            <p className="text-2xl font-black font-mono text-white/90">{data.price.toFixed(2)}</p>
          </div>
          {/* Score bar */}
          <div className="flex-1 min-w-[120px]">
            <p className="text-[8px] uppercase tracking-[0.3em] mb-1.5" style={{ color: 'rgba(255,255,255,0.25)' }}>Checkpoint Score</p>
            <div className="flex gap-0.5 rounded-full overflow-hidden" style={{ height: 6, background: 'rgba(255,255,255,0.04)' }}>
              <div className="rounded-full" style={{ width: `${(gc / tot) * 100}%`, background: N.g.c }} />
              <div className="rounded-full" style={{ width: `${(yc / tot) * 100}%`, background: N.y.c }} />
              <div className="rounded-full" style={{ width: `${(rc / tot) * 100}%`, background: N.r.c }} />
            </div>
            <div className="flex gap-3 mt-1.5">
              <span className="text-[10px] font-mono font-bold" style={{ color: N.g.c }}>{gc} Pass</span>
              <span className="text-[10px] font-mono font-bold" style={{ color: N.y.c }}>{yc} Warn</span>
              <span className="text-[10px] font-mono font-bold" style={{ color: N.r.c }}>{rc} Fail</span>
            </div>
          </div>
        </div>
      )}

      {/* ── 9 CHECKPOINT CARDS ── */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data?.checks.map((check) => {
            const Icon = CHECK_ICONS[check.id] || Activity;
            const cc = cn(check.color);
            return (
              <div key={check.id} className="rounded-xl p-3.5 transition-all duration-200 hover:translate-y-[-1px]"
                style={{ background: cc.bg, border: `1px solid ${cc.b}` }}>
                {/* Card header */}
                <div className="flex items-start justify-between mb-2.5">
                  <div className="flex items-center gap-2.5">
                    <Badge n={check.id} color={cc.c} />
                    <div>
                      <p className="text-[11px] font-bold font-mono text-white/90 leading-tight">{check.name}</p>
                      <p className="text-[9px] text-white/30 font-mono">{check.subtitle}</p>
                    </div>
                  </div>
                  <StatusIcon s={check.status} />
                </div>
                {/* Status label */}
                <div className="text-[11px] font-bold font-mono mb-2.5 px-2.5 py-1 rounded-md inline-flex items-center gap-1.5"
                  style={{ fontFamily: FONT, color: cc.c, background: `${cc.c}10`, border: `1px solid ${cc.c}18` }}>
                  <Icon className="w-3 h-3" style={{ color: cc.c }} />
                  {check.label}
                </div>
                {/* Details */}
                <div className="space-y-1 mb-2.5 font-mono">
                  {Object.entries(check.details).map(([k, v]) => (
                    <DetailRow key={k} k={k} v={v} />
                  ))}
                </div>
                {/* Comment */}
                <p className="text-[10px] leading-relaxed font-mono" style={{ color: 'rgba(255,255,255,0.4)' }}>
                  {check.comment}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── DECISION SUMMARY ── */}
      {data && (
        <div className="px-4 pb-4">
          <div className="rounded-xl p-4" style={{ background: `${sig.c}05`, border: `1px solid ${sig.b}` }}>
            <div className="flex items-center gap-2.5 mb-3">
              <EmelIcon size={20} style={{ color: sig.c }} />
              <span className="font-bold font-mono text-white/80 text-sm">{t("emel.decision")}</span>
              <span style={{ fontFamily: FONT, fontSize: 13, fontWeight: 600, color: sig.c, background: `${sig.c}12`, border: `1px solid ${sig.c}20` }} className="px-3 py-0.5 rounded-md">
                {data.summary.decision}
              </span>
            </div>

            {data.summary.rejections.length > 0 && (
              <div className="mb-3">
                <p className="text-[9px] uppercase tracking-[0.2em] font-mono mb-1.5" style={{ color: 'rgba(255,51,102,0.5)' }}>Risk Factors</p>
                <div className="space-y-1">
                  {data.summary.rejections.map((r, i) => (
                    <p key={i} className="text-[11px] font-mono flex items-center gap-1.5" style={{ color: N.r.c }}>
                      <XCircle className="w-3 h-3 shrink-0" /> {r}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {data.summary.entry_conditions.length > 0 && (
              <div>
                <p className="text-[9px] uppercase tracking-[0.2em] font-mono mb-1.5" style={{ color: 'rgba(0,224,198,0.5)' }}>{t("emel.whenToTrade")}</p>
                <div className="space-y-1">
                  {data.summary.entry_conditions.map((c, i) => (
                    <p key={i} className="text-[11px] font-mono" style={{ color: '#00e0c6' }}>→ {c}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
