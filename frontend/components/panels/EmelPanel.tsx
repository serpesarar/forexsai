"use client";

import { useState, useEffect } from "react";
import { useI18nStore } from "../../lib/i18n/store";
import { useWSPanelData } from "../../contexts/WebSocketContext";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Target,
  Layers,
  Gauge,
  Volume2,
  Brain,
  Shield,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
} from "lucide-react";

const API_BASE = "https://upbeat-flow-production.up.railway.app";

interface CheckItem {
  id: number;
  name: string;
  subtitle: string;
  status: "pass" | "warning" | "fail";
  direction: "up" | "down" | "neutral";
  color: "green" | "yellow" | "red";
  label: string;
  details: Record<string, any>;
  comment: string;
}

interface EmelData {
  symbol: string;
  timeframe: string;
  signal: string;
  confidence: number;
  price: number;
  checks: CheckItem[];
  summary: {
    green_count: number;
    yellow_count: number;
    red_count: number;
    decision: string;
    rejections: string[];
    entry_conditions: string[];
  };
}

interface EmelPanelProps {
  symbol?: string;
  onSwitchMode?: () => void;
}

const SYMBOLS = [
  { key: "NDX.INDX", label: "NASDAQ" },
  { key: "XAUUSD", label: "XAUUSD" },
];

const CHECK_ICONS: Record<number, any> = {
  1: TrendingUp,
  2: Activity,
  3: Layers,
  4: Target,
  5: BarChart3,
  6: Gauge,
  7: Volume2,
  8: Brain,
  9: Shield,
};

export default function EmelPanel({ symbol: initialSymbol = "NDX.INDX", onSwitchMode }: EmelPanelProps) {
  const { t } = useI18nStore();
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [data, setData] = useState<EmelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState("1H");

  // WebSocket data — real-time, no polling needed
  const { data: wsData, wsConnected } = useWSPanelData(activeSymbol, "emel");

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/panel/emel/${activeSymbol}?timeframe=${timeframe}`);
      const json = await res.json();
      if (!json.error) {
        setData(json);
      }
    } catch (e) {
      console.error("EMEL fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  // Use WS data when available
  useEffect(() => {
    if (wsData) {
      setData(wsData);
      setLoading(false);
    }
  }, [wsData]);

  // HTTP fetch on mount + polling only when WS is NOT connected
  useEffect(() => {
    if (!wsData) fetchData();
    if (!wsConnected) {
      const interval = setInterval(fetchData, 120000);
      return () => clearInterval(interval);
    }
  }, [activeSymbol, timeframe, wsConnected]);

  const getColorClass = (color: string) => {
    switch (color) {
      case "green":
        return "bg-green-500/20 border-green-500 text-green-400";
      case "yellow":
        return "bg-yellow-500/20 border-yellow-500 text-yellow-400";
      case "red":
        return "bg-red-500/20 border-red-500 text-red-400";
      default:
        return "bg-gray-500/20 border-gray-500 text-gray-400";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass":
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case "fail":
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return null;
    }
  };

  if (loading && !data) {
    return (
      <div className="rounded-2xl p-6 animate-pulse" style={{ background: 'rgba(10,15,30,0.5)', backdropFilter: 'blur(20px)', border: '1px solid rgba(0,224,198,0.1)' }}>
        <div className="h-8 bg-white/5 rounded-xl w-1/3 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[...Array(9)].map((_, i) => (
            <div key={i} className="h-28 bg-white/5 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const signalColor = data?.signal === "BUY" ? "#00ff88" : data?.signal === "SELL" ? "#ff3366" : "#fbbf24";

  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: 'rgba(10,15,30,0.5)', backdropFilter: 'blur(24px)', border: '1px solid rgba(0,224,198,0.08)', boxShadow: '0 0 40px rgba(0,224,198,0.03)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.25)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.2), rgba(0,224,198,0.2))', border: '1px solid rgba(168,85,247,0.3)' }}>
            <Brain className="w-4 h-4" style={{ color: '#a855f7' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold font-mono tracking-wide" style={{ color: '#a855f7', textShadow: '0 0 10px rgba(168,85,247,0.3)' }}>{t("emel.title")}</h2>
            <p className="text-[9px] uppercase tracking-[0.25em] text-white/25">{t("emel.subtitle")}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
            {SYMBOLS.map((s) => (
              <button key={s.key} onClick={() => setActiveSymbol(s.key)}
                className="px-3 py-1.5 text-[10px] font-bold font-mono transition-all"
                style={{ backgroundColor: activeSymbol === s.key ? 'rgba(168,85,247,0.15)' : 'rgba(255,255,255,0.03)', color: activeSymbol === s.key ? '#a855f7' : 'rgba(255,255,255,0.35)', borderRight: '1px solid rgba(255,255,255,0.05)' }}>
                {s.label}
              </button>
            ))}
          </div>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
            className="text-[10px] font-mono font-bold px-2 py-1.5 rounded-lg appearance-none cursor-pointer" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <option value="15m">15m</option><option value="1H">1H</option><option value="4H">4H</option><option value="1D">1D</option>
          </select>
          <button onClick={fetchData} className="p-1.5 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} style={{ color: 'rgba(255,255,255,0.35)' }} />
          </button>
          {onSwitchMode && (
            <button onClick={onSwitchMode} className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold font-mono" style={{ background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)', color: '#fbbf24' }}>
              <Zap className="w-3 h-3" /> PULSE
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      {data && (
        <div className="grid grid-cols-4 gap-3 p-4" style={{ background: 'rgba(0,0,0,0.15)' }}>
          <div className="rounded-xl p-3 text-center" style={{ background: `${signalColor}08`, border: `1px solid ${signalColor}20` }}>
            <p className="text-[9px] uppercase tracking-widest text-white/30 font-mono mb-1">{t("emel.signal")}</p>
            <p className="text-xl font-bold font-mono" style={{ color: signalColor, textShadow: `0 0 12px ${signalColor}60` }}>{data.signal}</p>
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(168,85,247,0.06)', border: '1px solid rgba(168,85,247,0.15)' }}>
            <p className="text-[9px] uppercase tracking-widest text-white/30 font-mono mb-1">{t("emel.confidence")}</p>
            <p className="text-xl font-bold font-mono" style={{ color: '#a855f7', textShadow: '0 0 10px rgba(168,85,247,0.4)' }}>%{data.confidence.toFixed(0)}</p>
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <p className="text-[9px] uppercase tracking-widest text-white/30 font-mono mb-1">{t("emel.price")}</p>
            <p className="text-xl font-bold font-mono text-white">{data.price.toFixed(2)}</p>
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <p className="text-[9px] uppercase tracking-widest text-white/30 font-mono mb-1">{t("emel.score")}</p>
            <div className="flex items-center justify-center gap-2 text-sm font-bold font-mono">
              <span style={{ color: '#00ff88' }}>{data.summary.green_count}🟢</span>
              <span style={{ color: '#fbbf24' }}>{data.summary.yellow_count}🟡</span>
              <span style={{ color: '#ff3366' }}>{data.summary.red_count}🔴</span>
            </div>
          </div>
        </div>
      )}

      {/* 9 Checkpoint Cards */}
      <div className="p-4">
        <h3 className="text-[10px] uppercase tracking-[0.2em] font-mono flex items-center gap-2 mb-3" style={{ color: 'rgba(255,255,255,0.35)' }}>
          📋 {t("emel.checkpoints")} ({data?.checks.length || 0}/9 {t("emel.active")})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data?.checks.map((check) => {
            const Icon = CHECK_ICONS[check.id] || Activity;
            const checkColor = check.color === "green" ? "#00ff88" : check.color === "yellow" ? "#fbbf24" : "#ff3366";
            return (
              <div key={check.id} className="rounded-xl p-3.5 transition-all duration-200 hover:scale-[1.01]"
                style={{ background: `${checkColor}06`, border: `1px solid ${checkColor}20`, boxShadow: `0 0 15px ${checkColor}05` }}>
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                      style={{ background: `${checkColor}15`, border: `1px solid ${checkColor}25` }}>
                      <Icon className="w-3.5 h-3.5" style={{ color: checkColor }} />
                    </div>
                    <div>
                      <p className="text-xs font-bold font-mono text-white">{check.id}️⃣ {check.name}</p>
                      <p className="text-[10px] text-white/30">{check.subtitle}</p>
                    </div>
                  </div>
                  {getStatusIcon(check.status)}
                </div>
                
                <div className="text-xs font-bold font-mono mb-2 px-2 py-1 rounded-md inline-block"
                  style={{ color: checkColor, background: `${checkColor}10`, textShadow: `0 0 6px ${checkColor}40` }}>
                  {check.label}
                </div>

                {/* Details */}
                <div className="text-[10px] font-mono space-y-0.5 mb-2">
                  {Object.entries(check.details).slice(0, 3).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-white/25 capitalize">{key.replace(/_/g, " ")}:</span>
                      <span className="text-white/50">
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>

                <p className="text-[10px] text-white/40 italic leading-relaxed">📝 {check.comment}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decision Summary */}
      {data && (
        <div className="p-4 border-t" style={{ borderColor: 'rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.15)' }}>
          <div className="rounded-xl p-4" style={{ background: `${signalColor}06`, border: `1px solid ${signalColor}20` }}>
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5" style={{ color: signalColor }} />
              <span className="font-bold font-mono text-white">{t("emel.decision")}</span>
              <span className="font-bold font-mono text-sm px-2 py-0.5 rounded" style={{ color: signalColor, background: `${signalColor}15`, textShadow: `0 0 8px ${signalColor}40` }}>{data.summary.decision}</span>
            </div>

            {data.summary.rejections.length > 0 && (
              <div className="mb-3">
                <p className="text-[10px] uppercase tracking-widest text-white/30 font-mono mb-1.5">{t("emel.why")}</p>
                <div className="space-y-1">
                  {data.summary.rejections.map((r, i) => (
                    <p key={i} className="text-xs font-mono" style={{ color: '#ff3366' }}>✕ {r}</p>
                  ))}
                </div>
              </div>
            )}

            {data.summary.entry_conditions.length > 0 && (
              <div>
                <p className="text-[10px] uppercase tracking-widest text-white/30 font-mono mb-1.5">{t("emel.whenToTrade")}</p>
                <div className="space-y-1">
                  {data.summary.entry_conditions.map((c, i) => (
                    <p key={i} className="text-xs font-mono" style={{ color: '#00ccff' }}>→ {c}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <p className="text-[10px] text-white/25 font-mono">
                💡 {t("emel.alternative")}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
