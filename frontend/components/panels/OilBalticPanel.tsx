"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  lat?: number;
  lon?: number;
  signal: string;
  bias: "bullish" | "bearish" | "neutral";
  intensity: number;
  narrative: string;
  vessel_count?: number;
  storage_estimate_mm_bbl?: number;
}

interface Tanker {
  mmsi: number;
  vessel_name?: string | null;
  lat: number;
  lon: number;
  speed_knots?: number | null;
  heading?: number | null;
  region?: string | null;
  status?: string | null;
  idle_days?: number | null;
  last_seen_at?: string | null;
  estimated_barrels?: number | null;
  ship_category?: string | null;
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
  tankers?: Tanker[];
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

type MapboxRuntime = {
  accessToken: string;
  Map: new (options: Record<string, unknown>) => any;
  Marker: new (options?: Record<string, unknown>) => any;
  Popup: new (options?: Record<string, unknown>) => any;
  NavigationControl: new (options?: Record<string, unknown>) => any;
};

declare global {
  interface Window {
    mapboxgl?: MapboxRuntime;
  }
}

const ENDPOINT = "/api/panel/oil-baltic-intelligence";
const ENABLE_MAPBOX_OIL_PANEL = process.env.NEXT_PUBLIC_ENABLE_MAPBOX_OIL_PANEL === "true";
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const MAPBOX_SCRIPT_ID = "forexsai-mapbox-runtime-js";
const MAPBOX_CSS_ID = "forexsai-mapbox-runtime-css";
const MAPBOX_JS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.5.1/mapbox-gl.js";
const MAPBOX_CSS_URL = "https://api.mapbox.com/mapbox-gl-js/v3.5.1/mapbox-gl.css";
const CHOKEPOINT_SOURCE_ID = "oil-baltic-chokepoints";
const CHOKEPOINT_CIRCLE_LAYER_ID = "oil-baltic-chokepoint-circles";
const CHOKEPOINT_STROKE_LAYER_ID = "oil-baltic-chokepoint-strokes";
const CHOKEPOINT_LABEL_LAYER_ID = "oil-baltic-chokepoint-labels";

let mapboxLoaderPromise: Promise<MapboxRuntime> | null = null;

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    if (char === "&") return "&amp;";
    if (char === "<") return "&lt;";
    if (char === ">") return "&gt;";
    if (char === '"') return "&quot;";
    return "&#39;";
  });
}

function getChokepointColor(signal?: string, bias?: string): string {
  const normalized = String(signal || "").toLowerCase();
  if (normalized.includes("storage") || normalized.includes("stress") || bias === "bearish") return "#ff4d6d";
  if (normalized.includes("rush") || normalized.includes("demand") || normalized.includes("drawdown") || bias === "bullish") return "#00ff88";
  if (normalized.includes("calm") || normalized.includes("watch") || normalized.includes("balanced")) return "#ffaa00";
  return "#00ff41";
}

function getTankerColor(status?: string): string {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "floating_storage") return "#ff4d6d";
  if (normalized === "transit") return "#00ff88";
  if (normalized === "anchored" || normalized === "idle") return "#ffaa00";
  return "#00ff41";
}

function buildPopupHtml(title: string, rows: Array<[string, string]>): string {
  const content = rows
    .map(
      ([label, value]) =>
        `<div style="display:flex;justify-content:space-between;gap:12px;margin-top:6px;"><span style="opacity:0.62;">${escapeHtml(label)}</span><span style="text-align:right;">${escapeHtml(value)}</span></div>`,
    )
    .join("");

  return `<div style="min-width:190px;background:#03100b;color:#8effba;font-family:var(--font-jetbrains-mono,ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace);font-size:11px;line-height:1.45;"><div style="color:#ecfff4;font-size:12px;font-weight:800;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">${escapeHtml(title)}</div>${content}</div>`;
}

function ensureMapboxAssets(): Promise<MapboxRuntime> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Map can only initialize in the browser."));
  }

  if (!document.getElementById(MAPBOX_CSS_ID)) {
    const link = document.createElement("link");
    link.id = MAPBOX_CSS_ID;
    link.rel = "stylesheet";
    link.href = MAPBOX_CSS_URL;
    document.head.appendChild(link);
  }

  if (window.mapboxgl) {
    return Promise.resolve(window.mapboxgl);
  }

  if (mapboxLoaderPromise) {
    return mapboxLoaderPromise;
  }

  mapboxLoaderPromise = new Promise<MapboxRuntime>((resolve, reject) => {
    const fail = (message: string) => {
      mapboxLoaderPromise = null;
      reject(new Error(message));
    };

    const existing = document.getElementById(MAPBOX_SCRIPT_ID) as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => {
        if (window.mapboxgl) {
          resolve(window.mapboxgl);
          return;
        }
        fail("Mapbox runtime loaded but window.mapboxgl is unavailable.");
      });
      existing.addEventListener("error", () => fail("Mapbox script failed to load."));
      return;
    }

    const script = document.createElement("script");
    script.id = MAPBOX_SCRIPT_ID;
    script.src = MAPBOX_JS_URL;
    script.async = true;
    script.onload = () => {
      if (window.mapboxgl) {
        resolve(window.mapboxgl);
        return;
      }
      fail("Mapbox runtime loaded but window.mapboxgl is unavailable.");
    };
    script.onerror = () => fail("Mapbox script failed to load.");
    document.body.appendChild(script);
  });

  return mapboxLoaderPromise;
}

function syncChokepointLayer(map: any, chokepoints: Chokepoint[]): void {
  const featureCollection = {
    type: "FeatureCollection",
    features: chokepoints
      .filter((point) => typeof point.lon === "number" && typeof point.lat === "number")
      .map((point) => ({
        type: "Feature",
        properties: {
          label: point.label,
          color: getChokepointColor(point.signal, point.bias),
          intensity: point.intensity,
        },
        geometry: {
          type: "Point",
          coordinates: [point.lon, point.lat],
        },
      })),
  };

  const existingSource = map.getSource(CHOKEPOINT_SOURCE_ID);
  if (existingSource) {
    existingSource.setData(featureCollection);
  } else {
    map.addSource(CHOKEPOINT_SOURCE_ID, {
      type: "geojson",
      data: featureCollection,
    });
  }

  if (!map.getLayer(CHOKEPOINT_CIRCLE_LAYER_ID)) {
    map.addLayer({
      id: CHOKEPOINT_CIRCLE_LAYER_ID,
      type: "circle",
      source: CHOKEPOINT_SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "intensity"], 0, 16, 100, 34],
        "circle-color": ["get", "color"],
        "circle-opacity": 0.14,
        "circle-blur": 0.4,
      },
    });
  }

  if (!map.getLayer(CHOKEPOINT_STROKE_LAYER_ID)) {
    map.addLayer({
      id: CHOKEPOINT_STROKE_LAYER_ID,
      type: "circle",
      source: CHOKEPOINT_SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "intensity"], 0, 8, 100, 18],
        "circle-color": "transparent",
        "circle-stroke-width": 2,
        "circle-stroke-color": ["get", "color"],
        "circle-stroke-opacity": 0.85,
      },
    });
  }

  if (!map.getLayer(CHOKEPOINT_LABEL_LAYER_ID)) {
    map.addLayer({
      id: CHOKEPOINT_LABEL_LAYER_ID,
      type: "symbol",
      source: CHOKEPOINT_SOURCE_ID,
      layout: {
        "text-field": ["get", "label"],
        "text-size": 11,
        "text-offset": [0, 2.2],
      },
      paint: {
        "text-color": "#d9ffea",
        "text-halo-color": "rgba(2, 11, 9, 0.96)",
        "text-halo-width": 1.2,
      },
    });
  }
}

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
  const [mapStatus, setMapStatus] = useState<string | null>(
    ENABLE_MAPBOX_OIL_PANEL ? (MAPBOX_TOKEN ? "Initializing map..." : "NEXT_PUBLIC_MAPBOX_TOKEN missing") : "Mapbox disabled (safe mode)"
  );
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const tankerMarkersRef = useRef<any[]>([]);
  const chokepointMarkersRef = useRef<any[]>([]);
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

  const chokepoints = useMemo(() => data?.chokepoints || [], [data]);
  const tankers = useMemo(() => data?.tankers || [], [data]);
  const mapboxEnabled = ENABLE_MAPBOX_OIL_PANEL && Boolean(MAPBOX_TOKEN);

  useEffect(() => {
    if (!ENABLE_MAPBOX_OIL_PANEL) {
      setMapStatus("Mapbox disabled (safe mode)");
      return;
    }

    if (!MAPBOX_TOKEN) {
      setMapStatus("NEXT_PUBLIC_MAPBOX_TOKEN missing");
      return;
    }

    let cancelled = false;

    const initMap = async () => {
      if (!mapContainerRef.current || mapRef.current) {
        return;
      }

      try {
        const mapboxgl = await ensureMapboxAssets();
        if (cancelled || !mapContainerRef.current) {
          return;
        }

        mapboxgl.accessToken = MAPBOX_TOKEN;
        const map = new mapboxgl.Map({
          container: mapContainerRef.current,
          style: "mapbox://styles/mapbox/dark-v10",
          center: [20, 20],
          zoom: 1.8,
          projection: "globe",
          attributionControl: false,
        });

        mapRef.current = map;
        map.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "top-right");

        map.on("load", () => {
          if (cancelled) {
            return;
          }
          try {
            map.setFog({
              color: "rgb(5, 22, 16)",
              "high-color": "rgb(9, 52, 40)",
              "space-color": "rgb(2, 11, 9)",
              "star-intensity": 0.08,
            });
          } catch {}
          syncChokepointLayer(map, chokepoints);
          window.setTimeout(() => map.resize(), 120);
          setMapStatus(null);
        });
      } catch (mapError) {
        if (!cancelled) {
          setMapStatus(mapError instanceof Error ? mapError.message : "Map initialization failed.");
        }
      }
    };

    void initMap();

    return () => {
      cancelled = true;
    };
  }, [chokepoints]);

  useEffect(() => {
    return () => {
      tankerMarkersRef.current.forEach((marker) => marker.remove());
      tankerMarkersRef.current = [];
      chokepointMarkersRef.current.forEach((marker) => marker.remove());
      chokepointMarkersRef.current = [];
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapboxEnabled) {
      return;
    }
    const map = mapRef.current;
    const mapboxgl = typeof window !== "undefined" ? window.mapboxgl : undefined;
    if (!map || !mapboxgl) {
      return;
    }

    const renderMapState = () => {
      syncChokepointLayer(map, chokepoints);

      tankerMarkersRef.current.forEach((marker) => marker.remove());
      tankerMarkersRef.current = [];
      chokepointMarkersRef.current.forEach((marker) => marker.remove());
      chokepointMarkersRef.current = [];

      chokepoints.forEach((point) => {
        if (typeof point.lon !== "number" || typeof point.lat !== "number") {
          return;
        }

        const color = getChokepointColor(point.signal, point.bias);
        const element = document.createElement("div");
        element.className = styles.chokepointPin;

        const ring = document.createElement("div");
        ring.className = styles.chokepointRing;
        ring.style.borderColor = color;
        ring.style.boxShadow = `0 0 22px ${color}33`;

        const core = document.createElement("div");
        core.className = styles.chokepointCore;
        core.style.background = color;
        core.style.boxShadow = `0 0 16px ${color}`;

        element.appendChild(ring);
        element.appendChild(core);

        const popup = new mapboxgl.Popup({ offset: 18, closeButton: false }).setHTML(
          buildPopupHtml(point.label, [
            ["Signal", titleize(point.signal)],
            ["Bias", titleize(point.bias)],
            ["Intensity", fmt(point.intensity, 0)],
            ["Flow", point.narrative],
          ]),
        );

        const marker = new mapboxgl.Marker({ element, anchor: "center" })
          .setLngLat([point.lon, point.lat])
          .setPopup(popup)
          .addTo(map);

        chokepointMarkersRef.current.push(marker);
      });

      tankers.slice(0, 120).forEach((tanker) => {
        const color = getTankerColor(tanker.status);
        const element = document.createElement("div");
        element.className = styles.tankerMarker;
        element.style.background = color;
        element.style.boxShadow = `0 0 12px ${color}, 0 0 22px ${color}66`;

        const popup = new mapboxgl.Popup({ offset: 12 }).setHTML(
          buildPopupHtml(tanker.vessel_name || `MMSI ${tanker.mmsi}`, [
            ["MMSI", String(tanker.mmsi)],
            ["Speed", `${fmt(tanker.speed_knots, 1)} kn`],
            ["Status", titleize(tanker.status)],
            ["Region", titleize(tanker.region)],
          ]),
        );

        const marker = new mapboxgl.Marker({ element, anchor: "center" })
          .setLngLat([tanker.lon, tanker.lat])
          .setPopup(popup)
          .addTo(map);

        tankerMarkersRef.current.push(marker);
      });
    };

    if (map.loaded() && map.isStyleLoaded()) {
      renderMapState();
      map.resize();
      return;
    }

    map.once("load", renderMapState);
  }, [chokepoints, tankers, mapboxEnabled]);

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
            {mapboxEnabled ? <div ref={mapContainerRef} className={styles.mapCanvas} /> : null}
            {!mapboxEnabled ? <div className={styles.worldMap} /> : null}
            <div className={styles.mapGrid} />
            <div className={styles.radarSweep} />
            <div className={styles.orbit} />
            <div className={styles.mapOverlay}>
              <div className={styles.mapTopBar}>
                <div className={styles.mapLabel}><Anchor size={14} /> Satellite theater</div>
                <div className={styles.mapLabel}><Waves size={14} /> Oil-only maritime watch</div>
                <div className={styles.mapLabel}><Activity size={14} /> Baltic {titleize(data?.baltic?.source_mode || "proxy")}</div>
                <div className={styles.mapLabel}><Radar size={14} /> {tankers.length} tankers</div>
                <div className={styles.mapLabel}><ShieldAlert size={14} /> {mapboxEnabled ? "Mapbox live" : "Mapbox off"}</div>
                <button className={styles.mapLabel} onClick={fetchPanel} disabled={loading}>
                  <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
                </button>
              </div>

              {mapStatus ? <div className={styles.mapStatus}>{mapStatus}</div> : null}

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
