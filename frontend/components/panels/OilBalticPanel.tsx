"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Anchor, Droplets, Gauge, RefreshCw, Waves, Radar, Fuel, ShieldAlert } from "lucide-react";

import { buildApiUrl } from "../../lib/api/base";
import { useRefreshAge } from "../../hooks/useRefreshAge";
import styles from "./oil-baltic-panel.module.css";

interface SourceHealthItem {
  name: string;
  status: string;
  mode: string;
  note: string;
}

interface Chokepoint {
  id: string;
  label: string;
  x: number;
  y: number;
  signal: string;
  bias: "bullish" | "bearish" | "neutral";
  intensity: number;
  narrative: string;
  vessel_count?: number;
  storage_estimate_mm_bbl?: number;
}

interface TradeRecommendation {
  direction: string;
  instrument: string;
  entry: number | null;
  stop_loss: number | null;
  target: number | null;
  risk_reward: number | null;
  confidence: number;
  rationale: string;
}

interface OilBalticResponse {
  available: boolean;
  error?: string;
  generated_at?: string;
  price?: {
    current: number;
    change_4h_pct: number;
    change_1d_pct: number;
    change_5d_pct: number;
    change_20d_pct: number;
    atr_pct: number;
  };
  signal?: {
    market_regime: string;
    recession_probability: number;
    oil_bias: "bullish" | "bearish" | "neutral";
    confidence: number;
    time_horizon: string;
    summary: string;
    physical_score: number;
  };
  baltic?: {
    bdti_proxy: number;
    bcti_proxy: number;
    bcti_weakness: number;
    td3c_proxy: number;
    dirty_clean_spread: number;
    status: string;
    bdti_value?: number | null;
    bcti_value?: number | null;
    td3c_value?: number | null;
    bdti_change_percent?: number | null;
    bcti_change_percent?: number | null;
    td3c_change_percent?: number | null;
    source_mode?: string;
    td3c_source_mode?: string;
  };
  storage?: {
    floating_storage_proxy: number;
    contango_pressure: number;
    backwardation_pressure: number;
    inventory_actual: number | null;
    inventory_estimate: number | null;
    status: string;
    floating_storage_vessels?: number;
    floating_storage_mm_bbl?: number;
    source_mode?: string;
  };
  demand?: {
    refinery_stress: number;
    crack_spread_proxy: number;
    gasoline_demand_proxy: number;
    status: string;
  };
  regime?: {
    type: string;
    adx: number;
    atr_ratio: number;
    session: string;
    swing_structure: string;
    min_rr: number;
    allowed_directions: string[];
  };
  trade_recommendation?: TradeRecommendation;
  key_levels?: Record<string, number>;
  chokepoints?: Chokepoint[];
  source_health?: SourceHealthItem[];
  terminal_log?: string[];
  algorithm_notes?: string[];
  oil_engine?: {
    direction?: string;
    signal_type?: string;
    confidence?: number;
    composite_score?: number;
    reasons?: string[];
    risks?: string[];
    modifiers?: string[];
    macro?: {
      dxy_change?: number;
      correlation?: number;
      geo_override?: boolean;
    };
    temporal?: {
      is_eia_day?: boolean;
      is_rollover_zone?: boolean;
    };
  };
}

const ENDPOINT = "/api/panel/oil-baltic-intelligence";

function pctColor(value: number): string {
  if (value > 0.05) return "#7dffb2";
  if (value < -0.05) return "#ff8d88";
  return "#ffd77a";
}

function biasClass(bias?: string): string {
  if (bias === "bullish") return styles.bullish;
  if (bias === "bearish") return styles.bearish;
  return styles.neutral;
}

function statusClass(status: string): string {
  switch (status) {
    case "live":
      return styles.statusLive;
    case "proxy":
      return styles.statusProxy;
    case "partial":
      return styles.statusPartial;
    case "planned":
      return styles.statusPlanned;
    case "offline":
      return styles.statusOffline;
    case "error":
      return styles.statusError;
    default:
      return styles.statusProxy;
  }
}

function fmt(value?: number | null, digits: number = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return Number(value).toFixed(digits);
}

function signedPct(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  const n = Number(value);
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function titleize(value?: string | null): string {
  if (!value) return "--";
  return value.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

function MetricRow({ label, value, status }: { label: string; value: string; status?: string }) {
  return (
    <div className={styles.metricRow}>
      <div>
        <div className={styles.metricRowLabel}>{label}</div>
        {status ? <div className={styles.metricRowStatus}>{status}</div> : null}
      </div>
      <div className={styles.metricRowValue}>{value}</div>
    </div>
  );
}

function SignalBadge({ bias }: { bias?: string }) {
  return (
    <div className={`${styles.signalDirection} ${biasClass(bias)}`}>
      <Radar size={14} />
      {(bias || "neutral").toUpperCase()}
    </div>
  );
}

export default function OilBalticPanel() {
  const [data, setData] = useState<OilBalticResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { refreshAge, markRefreshed } = useRefreshAge();

  const fetchPanel = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(buildApiUrl(ENDPOINT), {
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = (await response.json()) as OilBalticResponse;
      setData(json);
      setError(json.available ? null : (json.error || null));
      markRefreshed(json.generated_at || new Date());
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Failed to load oil Baltic panel.");
    } finally {
      setLoading(false);
    }
  }, [markRefreshed]);

  useEffect(() => {
    fetchPanel();
    const timer = window.setInterval(fetchPanel, 60_000);
    const refreshHandler = () => fetchPanel();
    window.addEventListener("dashboard-refresh", refreshHandler);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("dashboard-refresh", refreshHandler);
    };
  }, [fetchPanel]);

  const summary = useMemo(() => {
    const signal = data?.signal;
    const price = data?.price;
    const trade = data?.trade_recommendation;
    const baltic = data?.baltic;
    return {
      currentPrice: price?.current ?? 0,
      confidence: signal?.confidence ?? 0,
      regime: signal?.market_regime ?? "transition",
      bias: signal?.oil_bias ?? "neutral",
      horizon: signal?.time_horizon ?? "immediate",
      summaryText: signal?.summary ?? "Baltic cache and AIS layers are active when their collectors are online.",
      spread: baltic?.dirty_clean_spread ?? 0,
      tradeDirection: trade?.direction ?? "wait",
    };
  }, [data]);

  if (loading && !data) {
    return (
      <section className={styles.shell}>
        <div className={styles.loader}>
          <div className={styles.spinner} />
        </div>
      </section>
    );
  }

  if ((!data || !data.available) && !loading) {
    return (
      <section className={styles.shell}>
        <div className={styles.empty}>
          <div>
            <div className={styles.errorText}>{error || data?.error || "Oil Baltic panel not available."}</div>
            <p className={styles.mutedText}>
              The panel expects live WTI candles plus optional Baltic and AIS collectors. If one data layer is offline, the panel now degrades only that layer instead of disabling the whole command view.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.shell}>
      <div className={styles.header}>
        <div className={styles.titleBlock}>
          <span className={styles.eyebrow}>Physical Oil Market Intelligence Engine</span>
          <div className={styles.titleRow}>
            <h2 className={styles.title}>Baltic Oil Command Center</h2>
            <SignalBadge bias={summary.bias} />
          </div>
          <p className={styles.subtitle}>
            A readable satellite-style command panel for WTI. Baltic indices now read from public-source cache when available, AIS chokepoint metrics can stream into Supabase, and missing layers stay explicitly marked as live, proxy, partial or planned.
          </p>
        </div>

        <div className={styles.headerMetrics}>
          <div className={styles.metricChip}>
            <span className={styles.metricLabel}>WTI</span>
            <span className={styles.metricValue}>${fmt(data?.price?.current, 2)}</span>
            <span className={styles.metricSub} style={{ color: pctColor(data?.price?.change_1d_pct ?? 0) }}>
              {signedPct(data?.price?.change_1d_pct)} 1D
            </span>
          </div>
          <div className={styles.metricChip}>
            <span className={styles.metricLabel}>Physical Score</span>
            <span className={styles.metricValue}>{fmt(data?.signal?.physical_score, 0)}</span>
            <span className={styles.metricSub}>{titleize(data?.signal?.market_regime)} • {titleize(data?.baltic?.source_mode || "proxy")}</span>
          </div>
          <div className={styles.metricChip}>
            <span className={styles.metricLabel}>Refresh Age</span>
            <span className={styles.metricValue}>{refreshAge}</span>
            <span className={styles.metricSub}>Auto-refresh 60s • AIS {titleize(data?.storage?.source_mode || "planned")}</span>
          </div>
        </div>
      </div>

      <div className={styles.body}>
        <div className={styles.topGrid}>
          <div className={styles.card}>
            <div className={styles.cardTitle}>Mission Readout</div>
            <div className={styles.titleRow}>
              <SignalBadge bias={summary.bias} />
              <div className={styles.metricRowStatus}>{titleize(summary.regime)} • {summary.horizon}</div>
            </div>
            <div className={styles.summaryGrid}>
              <div className={styles.statBox}>
                <div className={styles.statBoxLabel}>Confidence</div>
                <div className={styles.statBoxValue}>{fmt(data?.signal?.confidence, 0)}%</div>
                <div className={styles.statBoxHint}>Weighted from storage, tanker spread, regime and oil engine confluence.</div>
              </div>
              <div className={styles.statBox}>
                <div className={styles.statBoxLabel}>Recession Risk</div>
                <div className={styles.statBoxValue}>{fmt(data?.signal?.recession_probability, 0)}%</div>
                <div className={styles.statBoxHint}>Clean-product weakness and inventory build pressure dominate this score.</div>
              </div>
              <div className={styles.statBox}>
                <div className={styles.statBoxLabel}>Preferred Action</div>
                <div className={styles.statBoxValue}>{titleize(data?.trade_recommendation?.direction || "wait")}</div>
                <div className={styles.statBoxHint}>{summary.summaryText}</div>
              </div>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardTitle}>Baltic Feed Deck</div>
            <MetricRow label="BDTI" value={data?.baltic?.bdti_value != null ? `${fmt(data?.baltic?.bdti_value, 0)}` : fmt(data?.baltic?.bdti_proxy, 0)} status={data?.baltic?.bdti_value != null ? `Live ${signedPct(data?.baltic?.bdti_change_percent)}` : `Proxy ${titleize(data?.baltic?.status)}`} />
            <MetricRow label="BCTI" value={data?.baltic?.bcti_value != null ? `${fmt(data?.baltic?.bcti_value, 0)}` : fmt(data?.baltic?.bcti_proxy, 0)} status={data?.baltic?.bcti_value != null ? `Live ${signedPct(data?.baltic?.bcti_change_percent)}` : "Refined flow proxy"} />
            <MetricRow label="BCTI weakness" value={fmt(data?.baltic?.bcti_weakness, 0)} status="Demand stress" />
            <MetricRow label="TD3C" value={data?.baltic?.td3c_value != null ? `${fmt(data?.baltic?.td3c_value, 2)}` : fmt(data?.baltic?.td3c_proxy, 0)} status={data?.baltic?.td3c_value != null ? `Live ${signedPct(data?.baltic?.td3c_change_percent)}` : `Optional ${titleize(data?.baltic?.td3c_source_mode || "proxy")}`} />
            <MetricRow label="Dirty/Clean spread" value={fmt(summary.spread, 1)} status="Tanker divergence" />
          </div>

          <div className={styles.card}>
            <div className={styles.cardTitle}>Storage + Demand Matrix</div>
            <MetricRow label="Floating storage proxy" value={fmt(data?.storage?.floating_storage_proxy, 0)} status={titleize(data?.storage?.status)} />
            <MetricRow label="AIS storage" value={`${fmt(data?.storage?.floating_storage_mm_bbl, 2)}m bbl`} status={`${data?.storage?.floating_storage_vessels || 0} tankers`} />
            <MetricRow label="Contango pressure" value={fmt(data?.storage?.contango_pressure, 0)} status="Curve storage incentive" />
            <MetricRow label="Backwardation pressure" value={fmt(data?.storage?.backwardation_pressure, 0)} status="Prompt tightness" />
            <MetricRow label="Refinery stress" value={fmt(data?.demand?.refinery_stress, 0)} status={titleize(data?.demand?.status)} />
            <MetricRow label="Gasoline demand proxy" value={fmt(data?.demand?.gasoline_demand_proxy, 0)} status="Consumer burn" />
          </div>
        </div>

        <div className={styles.mainGrid}>
          <div className={styles.stack}>
            <div className={styles.card}>
              <div className={styles.cardTitle}>Regime Overlay</div>
              <MetricRow label="Trend regime" value={titleize(data?.regime?.type)} status={titleize(data?.regime?.session)} />
              <MetricRow label="ADX" value={fmt(data?.regime?.adx, 1)} status={titleize(data?.regime?.swing_structure)} />
              <MetricRow label="ATR ratio" value={fmt(data?.regime?.atr_ratio, 2)} status={`Min R/R ${fmt(data?.regime?.min_rr, 2)}`} />
              <MetricRow label="Oil engine" value={titleize(data?.oil_engine?.direction)} status={`${titleize(data?.oil_engine?.signal_type)} • ${fmt(data?.oil_engine?.confidence, 0)}%`} />
              <MetricRow label="DXY coupling" value={fmt(data?.oil_engine?.macro?.correlation, 2)} status={`DXY ${signedPct(data?.oil_engine?.macro?.dxy_change)}`} />
            </div>

            <div className={styles.card}>
              <div className={styles.cardTitle}>Key Levels</div>
              <MetricRow label="VWAP" value={`$${fmt(data?.key_levels?.vwap, 2)}`} status="Institutional pivot" />
              <MetricRow label="POC" value={`$${fmt(data?.key_levels?.poc, 2)}`} status="Volume magnet" />
              <MetricRow label="VAH" value={`$${fmt(data?.key_levels?.vah, 2)}`} status="Acceptance ceiling" />
              <MetricRow label="VAL" value={`$${fmt(data?.key_levels?.val, 2)}`} status="Acceptance floor" />
              <MetricRow label="EMA20 / EMA50" value={`$${fmt(data?.key_levels?.ema20, 2)} / $${fmt(data?.key_levels?.ema50, 2)}`} status="Trend rails" />
            </div>
          </div>

          <div className={styles.mapShell}>
            <div className={styles.worldMap} />
            <div className={styles.mapGrid} />
            <div className={styles.radarSweep} />
            <div className={styles.orbit} />
            <div className={styles.mapOverlay}>
              <div className={styles.mapTopBar}>
                <div className={styles.mapLabel}><Anchor size={14} /> Satellite theater</div>
                <div className={styles.mapLabel}><Waves size={14} /> Oil-only maritime watch</div>
                <div className={styles.mapLabel}><Activity size={14} /> Baltic {titleize(data?.baltic?.source_mode || "proxy")}</div>
                <button className={styles.mapLabel} onClick={fetchPanel} disabled={loading}>
                  <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
                </button>
              </div>

              <div>
                {(data?.chokepoints || []).map((point) => (
                  <div key={point.id} className={styles.marker} style={{ left: `${point.x}%`, top: `${point.y}%` }}>
                    <div className={styles.markerDot} style={{ background: point.bias === "bearish" ? "#ff8d88" : point.bias === "bullish" ? "#7dffb2" : "#ffd77a" }} />
                    <div className={styles.markerCard}>
                      <div className={styles.markerName}>{point.label}</div>
                      <div className={styles.markerSignal}>{point.signal}</div>
                      <div className={styles.markerNarrative}>{point.narrative}</div>
                      <div className={styles.markerIntensity}>
                        <div className={styles.barTrack}>
                          <div
                            className={`${styles.barFill} ${point.bias === "bearish" ? styles.barFillBearish : ""}`}
                            style={{ width: `${Math.max(4, Math.min(100, point.intensity))}%` }}
                          />
                        </div>
                        <div className={styles.barValue}>{fmt(point.intensity, 0)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className={styles.mapBottomBar}>
                <div className={styles.mapLabel}><Gauge size={14} /> ATR {fmt(data?.price?.atr_pct, 2)}%</div>
                <div className={styles.mapLabel}><Fuel size={14} /> 5D {signedPct(data?.price?.change_5d_pct)}</div>
                <div className={styles.mapLabel}><Droplets size={14} /> Storage {fmt(data?.storage?.floating_storage_mm_bbl, 2)}m</div>
                <div className={styles.mapLabel}><ShieldAlert size={14} /> EIA {data?.oil_engine?.temporal?.is_eia_day ? "active" : "clear"}</div>
              </div>
            </div>
          </div>

          <div className={styles.stack}>
            <div className={styles.card}>
              <div className={styles.cardTitle}>Source Health</div>
              <div className={styles.healthList}>
                {(data?.source_health || []).map((item) => (
                  <div key={item.name} className={styles.healthItem}>
                    <div className={styles.healthHeader}>
                      <div className={styles.healthName}>{item.name}</div>
                      <div className={`${styles.healthStatus} ${statusClass(item.status)}`}>{item.status}</div>
                    </div>
                    <div className={styles.healthMode}>{item.mode}</div>
                    <div className={styles.healthNote}>{item.note}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.card}>
              <div className={styles.cardTitle}>Algorithm Notes</div>
              <div className={styles.noteList}>
                {(data?.algorithm_notes || []).map((note) => (
                  <div key={note} className={styles.noteItem}>
                    <div className={styles.noteText}>{note}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.bottomGrid}>
          <div className={styles.card}>
            <div className={styles.cardTitle}>Trade Recommendation</div>
            <div className={styles.tradeBox}>
              <SignalBadge bias={data?.signal?.oil_bias} />
              <div className={styles.tradeGrid}>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>Instrument</div>
                  <div className={styles.tradeMetricValue}>{data?.trade_recommendation?.instrument || "CL_Futures"}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>Entry</div>
                  <div className={styles.tradeMetricValue}>{data?.trade_recommendation?.entry ? `$${fmt(data.trade_recommendation.entry, 2)}` : "Wait"}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>Stop</div>
                  <div className={styles.tradeMetricValue}>{data?.trade_recommendation?.stop_loss ? `$${fmt(data.trade_recommendation.stop_loss, 2)}` : "--"}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>Target</div>
                  <div className={styles.tradeMetricValue}>{data?.trade_recommendation?.target ? `$${fmt(data.trade_recommendation.target, 2)}` : "--"}</div>
                </div>
              </div>
              <div className={styles.tradeGrid}>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>R/R</div>
                  <div className={styles.tradeMetricValue}>{data?.trade_recommendation?.risk_reward ? fmt(data.trade_recommendation.risk_reward, 2) : "--"}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>Engine Score</div>
                  <div className={styles.tradeMetricValue}>{fmt(data?.oil_engine?.composite_score, 1)}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>4H Tape</div>
                  <div className={styles.tradeMetricValue} style={{ color: pctColor(data?.price?.change_4h_pct ?? 0) }}>{signedPct(data?.price?.change_4h_pct)}</div>
                </div>
                <div className={styles.tradeMetric}>
                  <div className={styles.tradeMetricLabel}>20D Tape</div>
                  <div className={styles.tradeMetricValue} style={{ color: pctColor(data?.price?.change_20d_pct ?? 0) }}>{signedPct(data?.price?.change_20d_pct)}</div>
                </div>
              </div>
              <div className={styles.tradeRationale}>{data?.trade_recommendation?.rationale || data?.signal?.summary}</div>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardTitle}>Terminal Log</div>
            <div className={styles.logList}>
              {(data?.terminal_log || []).map((line) => (
                <div key={line} className={styles.logItem}>
                  <div className={styles.logText}>{line}</div>
                </div>
              ))}
              {(data?.oil_engine?.reasons || []).slice(0, 2).map((line) => (
                <div key={line} className={styles.logItem}>
                  <div className={styles.logText}>{line}</div>
                </div>
              ))}
              {(data?.oil_engine?.risks || []).slice(0, 2).map((line) => (
                <div key={line} className={styles.logItem}>
                  <div className={styles.logText}>{line}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
