"use client";

/**
 * Neural panel live-data layer.
 * Pulls from the running FastAPI backend; every source is optional —
 * any fetch that fails simply leaves the demo value in place, so the
 * panel degrades gracefully when the backend (or one engine) is down.
 *
 * Sources:
 *  price+TA     GET /api/data/cached/{symbol}
 *  regime       GET /api/panel/regime/{symbol}
 *  votes        GET /api/panel/{emel|pulse|pulse-ml|pulse-v3|smc}/{symbol}
 *  macro/VIX    GET /api/macro-gauges
 *  news         GET /api/market-events/markers/{symbol}
 *  active sig   GET /api/signals/active
 *  candles      GET /api/data/ohlcv?symbol=&timeframe=1h&limit=64
 *  history      GET /api/learning/predictions?symbol=&limit=200
 *  patterns     GET /api/patterns/{symbol}?timeframe=4h  (+4h candles)
 *  debate       GET /api/bias-test/recent-runs
 *  whale/COT    GET /api/whale/dashboard
 *  oil intel    GET /api/panel/oil-baltic-intelligence   (USOIL only)
 */

import { useEffect, useRef, useState } from "react";
import { buildApiUrl } from "./base";

const TIMEOUT_MS = 9000;

async function get<T = any>(endpoint: string): Promise<T | null> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(buildApiUrl(endpoint), { signal: ctrl.signal });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

// ── helpers ────────────────────────────────────────────────────────────────

export type LiveDir = "BUY" | "SELL" | "HOLD";

function normDir(raw: unknown): LiveDir | null {
  const s = String(raw ?? "").toUpperCase();
  if (s.includes("BUY") || s === "LONG" || s === "UP" || s === "BULLISH") return "BUY";
  if (s.includes("SELL") || s === "SHORT" || s === "DOWN" || s === "BEARISH") return "SELL";
  if (s.includes("HOLD") || s.includes("WAIT") || s.includes("NEUTRAL") || s === "NONE") return "HOLD";
  return null;
}

function pickDir(o: any): LiveDir | null {
  if (!o || typeof o !== "object") return null;
  return (
    normDir(o.direction) ?? normDir(o.signal) ?? normDir(o.ml_direction) ??
    normDir(o.final_signal) ?? normDir(o.recommendation) ?? normDir(o?.data?.direction) ?? null
  );
}

function pickConf(o: any): number | null {
  if (!o || typeof o !== "object") return null;
  const cands = [o.confidence, o.ml_confidence, o.score, o.final_confidence, o?.data?.confidence];
  for (const c of cands) {
    const n = Number(c);
    if (Number.isFinite(n) && n > 0) return Math.round(n <= 1 ? n * 100 : n);
  }
  return null;
}

const fmtPrice = (p: number) =>
  p >= 1000 ? p.toLocaleString("en-US", { maximumFractionDigits: 1 }) : p.toFixed(2);

/** Whale dashboard uses short names. */
const WHALE_KEY: Record<string, string> = {
  "NDX.INDX": "NASDAQ",
  "GDAXI.INDX": "DAX",
  XAUUSD: "XAUUSD",
  "USOIL.FOREX": "USOIL",
};

// ── result shape ───────────────────────────────────────────────────────────

export interface LiveVote { id: string; dir: LiveDir; conf: number }
export interface LiveNews {
  time: string; title: string; titleEn: string;
  sentiment: "pos" | "neg" | "neu"; impact: 1 | 2 | 3; source: string;
}
export interface LiveCandle { o: number; h: number; l: number; c: number; ts: number }
export interface LiveSegment { from: number; to: number; dir: LiveDir }
export interface LiveActive {
  dir: LiveDir; entry: number; tps: number[]; sl: number; conf: number;
  targetsHit: boolean[]; model: string;
}

export interface LivePatternPoint { index: number; price: number; time?: number }
export interface LivePatternRaw {
  name: string;
  nameTr: string;
  category: string;
  signal: "bullish" | "bearish";
  status: "COMPLETED" | "FORMING";
  confidence: number;
  timeframe: string;
  points: Record<string, LivePatternPoint>;
  projected?: { price: number; time?: number };
  targetPrice?: number;
  stopLoss?: number;
  ratios?: Record<string, number>;
}

export interface LiveDebate {
  bias: string;
  conf: number;
  reason: string;
  label: string;
  mode?: string;
  date?: string;
}

export interface LiveWhale {
  pressure: number;
  label: string;
  specLongPct: number;
  specNet: number;
  commNet: number;
}

export interface LiveOil {
  regime: string;
  bias: string;
  conf: number;
  recession: number;
  bdti: number;
  bcti: number;
  storage: number;
  physical: number;
  summary: string;
}

export interface LiveTa {
  rsi14?: number;
  emaBullStack?: boolean;
  emaText?: string;
  trend?: string;
}

export interface NeuralLive {
  price?: { value: number; text: string; changePct: number; up: boolean };
  regime?: { raw: string };
  votes?: Partial<Record<string, LiveVote>>;
  vix?: { value: number; changeText: string };
  macroTiles?: { label: string; value: string; change: string; up: boolean }[];
  news?: LiveNews[];
  active?: LiveActive | null;
  candles?: LiveCandle[];
  segments?: LiveSegment[];
  patterns?: LivePatternRaw[];
  patternCandles?: LiveCandle[];
  debate?: LiveDebate;
  whale?: LiveWhale;
  oil?: LiveOil;
  ta?: LiveTa;
  sourcesOk: number;
  sourcesTotal: number;
  loading: boolean;
}

// ── fetch orchestration ────────────────────────────────────────────────────

async function fetchAll(code: string): Promise<Omit<NeuralLive, "loading">> {
  const enc = encodeURIComponent(code);
  const isOil = code === "USOIL.FOREX";

  const [
    cached, regime, emel, pulse, pulseMl, pulseV3, smc, gauges, markers, activeRes,
    ohlcv, history, patternsRes, patternOhlcv, recentRuns, whaleRes, oilRes,
  ] = await Promise.all([
    get(`/api/data/cached/${enc}`),
    get(`/api/panel/regime/${enc}`),
    get(`/api/panel/emel/${enc}`),
    get(`/api/panel/pulse/${enc}`),
    get(`/api/panel/pulse-ml/${enc}`),
    get(`/api/panel/pulse-v3/${enc}`),
    get(`/api/panel/smc/${enc}`),
    get(`/api/macro-gauges`),
    get(`/api/market-events/markers/${enc}?timeframe=1h&limit=8`),
    get(`/api/signals/active`),
    get(`/api/data/ohlcv?symbol=${enc}&timeframe=1h&limit=64`),
    get(`/api/learning/predictions?symbol=${enc}&limit=200`),
    get(`/api/patterns/${enc}?timeframe=4h&limit=260`),
    get(`/api/data/ohlcv?symbol=${enc}&timeframe=4h&limit=260`),
    get(`/api/bias-test/recent-runs?limit=8`),
    get(`/api/whale/dashboard`),
    isOil ? get(`/api/panel/oil-baltic-intelligence`) : Promise.resolve(null),
  ]);

  const out: Omit<NeuralLive, "loading"> = { sourcesOk: 0, sourcesTotal: isOil ? 12 : 11 };

  // price + TA snapshot
  const snap = (cached as any)?.data?.ta_snapshot ?? (cached as any)?.data ?? cached;
  const priceVal = Number(snap?.current_price ?? snap?.price);
  if (Number.isFinite(priceVal) && priceVal > 0) {
    const chg = Number(snap?.change_pct ?? 0);
    out.price = { value: priceVal, text: fmtPrice(priceVal), changePct: chg, up: chg >= 0 };
    out.sourcesOk++;

    const ta: LiveTa = {};
    const rsi = Number(snap?.rsi14);
    if (Number.isFinite(rsi) && rsi > 0) ta.rsi14 = Math.round(rsi);
    const ema = snap?.ema ?? {};
    const e20 = Number(ema?.ema20);
    const e50 = Number(ema?.ema50);
    const e200 = Number(ema?.ema200);
    if ([e20, e50, e200].every((n) => Number.isFinite(n) && n > 0)) {
      ta.emaBullStack = priceVal > e20 && e20 > e50 && e50 > e200;
      ta.emaText = ta.emaBullStack
        ? "20>50>200 ▲"
        : priceVal < e20 && e20 < e50 && e50 < e200
        ? "20<50<200 ▼"
        : "mixed";
    }
    if (typeof snap?.trend === "string") ta.trend = snap.trend;
    if (ta.rsi14 !== undefined || ta.emaText) out.ta = ta;
  }

  // regime
  const regRaw = (regime as any)?.regime ?? (regime as any)?.market_regime ?? (regime as any)?.data?.regime;
  if (typeof regRaw === "string" && regRaw) {
    out.regime = { raw: regRaw };
    out.sourcesOk++;
  }

  // votes
  const voteSrc: [string, any][] = [
    ["emel", emel], ["pulse1", pulse], ["pulse2", pulseMl], ["pulse3", pulseV3], ["smc", smc],
  ];
  const votes: Partial<Record<string, LiveVote>> = {};
  let anyVote = false;
  for (const [id, raw] of voteSrc) {
    const dir = pickDir(raw);
    if (dir) {
      votes[id] = { id, dir, conf: pickConf(raw) ?? 0 };
      anyVote = true;
    }
  }
  if (anyVote) {
    out.votes = votes;
    out.sourcesOk++;
  }

  // macro gauges → VIX + tiles
  const gaugeArr: any[] = (gauges as any)?.gauges ?? [];
  if (Array.isArray(gaugeArr) && gaugeArr.length) {
    const byKey = (k: string) => gaugeArr.find((g) => String(g.key).toLowerCase().includes(k));
    const vix = byKey("vix");
    if (vix && Number.isFinite(Number(vix.value))) {
      const z = Number(vix.z_score ?? 0);
      out.vix = { value: Number(vix.value), changeText: `z ${z >= 0 ? "+" : ""}${z.toFixed(2)}σ` };
    }
    const tiles: NeuralLive["macroTiles"] = [];
    for (const k of ["dxy", "us10", "eur"]) {
      const g = byKey(k);
      if (g && Number.isFinite(Number(g.value))) {
        const z = Number(g.z_score ?? 0);
        tiles.push({
          label: String(g.label ?? k).split(" ")[0].toUpperCase(),
          value: Number(g.value) >= 100 ? Number(g.value).toFixed(2) : String(g.value),
          change: `z${z >= 0 ? "+" : ""}${z.toFixed(1)}`,
          up: z >= 0,
        });
      }
    }
    if (tiles.length) out.macroTiles = tiles;
    if (out.vix || tiles.length) out.sourcesOk++;
  }

  // news markers
  const mk: any[] = (markers as any)?.markers ?? [];
  if (Array.isArray(mk) && mk.length) {
    out.news = mk.slice(0, 5).map((m) => {
      const d = new Date(m.time);
      const hh = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
      const dir = String(m.direction ?? "").toLowerCase();
      const score = Number(m.score ?? 0);
      return {
        time: hh,
        title: String(m.headline ?? m.text ?? ""),
        titleEn: String(m.headline_en ?? m.headline ?? ""),
        sentiment: dir === "bullish" ? "pos" : dir === "bearish" ? "neg" : "neu",
        impact: (score >= 7 ? 3 : score >= 4 ? 2 : 1) as 1 | 2 | 3,
        source: String(m.urgency ?? "event").toUpperCase(),
      };
    });
    out.sourcesOk++;
  }

  // active signal
  const sigs: any[] = (activeRes as any)?.signals ?? [];
  if (Array.isArray(sigs)) {
    const mine = sigs.filter((s) => String(s.symbol) === code && pickDir(s));
    if (mine.length) {
      mine.sort((a, b) => (pickConf(b) ?? 0) - (pickConf(a) ?? 0));
      const s = mine[0];
      const tgts = s.targets ?? {};
      const hit = s.targets_hit ?? {};
      const keys = Object.keys(tgts).sort();
      out.active = {
        dir: pickDir(s) as LiveDir,
        entry: Number(s.ml_entry_price ?? s.entry_price ?? 0),
        tps: keys.slice(0, 3).map((k) => Number(tgts[k])).filter((n) => Number.isFinite(n)),
        sl: Number(s.stop_loss ?? s.sl ?? 0),
        conf: pickConf(s) ?? 0,
        targetsHit: keys.slice(0, 3).map((k) => Boolean(hit[k])),
        model: String(s.model_type ?? s.strategy ?? "model"),
      };
    } else {
      out.active = null;
    }
    out.sourcesOk++;
  }

  // candles (1h, signal map)
  const parseCandles = (raw: any): LiveCandle[] | undefined => {
    const rows: any[] = raw?.data ?? raw?.candles ?? [];
    if (!Array.isArray(rows) || rows.length < 10) return undefined;
    const mapped = rows
      .map((r) => {
        const tsRaw = Number(r.timestamp ?? r.time ?? r.t ?? 0);
        return {
          o: Number(r.o ?? r.open),
          h: Number(r.h ?? r.high),
          l: Number(r.l ?? r.low),
          c: Number(r.c ?? r.close),
          ts: tsRaw * (tsRaw < 1e12 ? 1000 : 1),
        };
      })
      .filter((c) => [c.o, c.h, c.l, c.c].every(Number.isFinite));
    return mapped.length >= 10 ? mapped : undefined;
  };

  out.candles = parseCandles(ohlcv);
  if (out.candles) out.sourcesOk++;

  // prediction history → signal wave segments
  const hist: any[] = (history as any)?.predictions ?? (history as any)?.data ?? (history as any)?.items ?? [];
  if (out.candles && Array.isArray(hist) && hist.length) {
    const events = hist
      .map((h) => ({
        ts: Date.parse(h.created_at ?? h.timestamp ?? h.time ?? ""),
        dir: normDir(h.ml_direction ?? h.direction ?? h.signal),
      }))
      .filter((e) => Number.isFinite(e.ts) && e.dir) as { ts: number; dir: LiveDir }[];
    events.sort((a, b) => a.ts - b.ts);
    if (events.length) {
      const dirs: LiveDir[] = out.candles.map((c) => {
        let cur: LiveDir = "HOLD";
        for (const e of events) {
          if (e.ts <= c.ts + 3600_000) cur = e.dir;
          else break;
        }
        return cur;
      });
      const segments: LiveSegment[] = [];
      let start = 0;
      for (let i = 1; i <= dirs.length; i++) {
        if (i === dirs.length || dirs[i] !== dirs[start]) {
          segments.push({ from: start, to: i - 1, dir: dirs[start] });
          start = i;
        }
      }
      out.segments = segments;
      out.sourcesOk++;
    }
  }

  // chart patterns (4h) + matching candle series
  const rawPatterns: any[] = (patternsRes as any)?.patterns ?? [];
  out.patternCandles = parseCandles(patternOhlcv);
  if (Array.isArray(rawPatterns) && rawPatterns.length && out.patternCandles) {
    out.patterns = rawPatterns
      .filter((p) => p?.points && (p.signal === "bullish" || p.signal === "bearish"))
      .map((p) => ({
        name: String(p.name ?? "Pattern"),
        nameTr: String(p.name_tr ?? p.name ?? "Formasyon"),
        category: String(p.category ?? "classic"),
        signal: p.signal,
        status: p.status === "FORMING" ? "FORMING" : "COMPLETED",
        confidence: Math.round(Number(p.confidence ?? 0)),
        timeframe: String(p.timeframe ?? "4h").toUpperCase(),
        points: Object.fromEntries(
          Object.entries(p.points as Record<string, any>).map(([k, v]) => [
            k,
            { index: Number(v?.index ?? 0), price: Number(v?.price ?? 0), time: Number(v?.time ?? 0) },
          ])
        ),
        projected: p.projected_d
          ? { price: Number(p.projected_d.price), time: Number(p.projected_d.time ?? 0) }
          : undefined,
        targetPrice: Number.isFinite(Number(p.target_price)) ? Number(p.target_price) : undefined,
        stopLoss: Number.isFinite(Number(p.stop_loss)) ? Number(p.stop_loss) : undefined,
        ratios: p.ratios ?? undefined,
      }));
    out.sourcesOk++;
  }

  // debate council (latest CIO run for this symbol)
  const latest = (recentRuns as any)?.latest_by_symbol;
  if (latest && typeof latest === "object") {
    const entry = latest[code] ?? latest[code.split(".")[0]] ?? null;
    if (entry) {
      out.debate = {
        bias: String(entry.predicted_bias ?? "neutral"),
        conf: Math.round(Number(entry.confidence ?? 0)),
        reason: String(entry.reason_summary ?? ""),
        label: String(entry.run_label ?? ""),
        mode: entry.trade_mode ? String(entry.trade_mode) : undefined,
        date: entry.ny_date ? String(entry.ny_date) : undefined,
      };
      out.sourcesOk++;
    }
  }

  // whale / COT
  const wsym = (whaleRes as any)?.data?.symbols?.[WHALE_KEY[code] ?? ""];
  if (wsym) {
    out.whale = {
      pressure: Number(wsym.whale_pressure ?? 0),
      label: String(wsym.pressure_label ?? "Neutral"),
      specLongPct: Number(wsym.spec_long_percent ?? 0),
      specNet: Number(wsym.speculators_net ?? 0),
      commNet: Number(wsym.commercials_net ?? 0),
    };
    out.sourcesOk++;
  }

  // oil physical-market intelligence (USOIL only)
  if (isOil) {
    const o = oilRes as any;
    if (o?.available) {
      out.oil = {
        regime: String(o.signal?.market_regime ?? "-"),
        bias: String(o.signal?.oil_bias ?? "-"),
        conf: Math.round(Number(o.signal?.confidence ?? 0)),
        recession: Math.round(Number(o.signal?.recession_probability ?? 0)),
        bdti: Number(o.baltic?.bdti_value ?? o.baltic?.bdti_proxy ?? 0),
        bcti: Number(o.baltic?.bcti_value ?? o.baltic?.bcti_proxy ?? 0),
        storage: Math.round(Number(o.storage?.floating_storage_proxy ?? 0)),
        physical: Math.round(Number(o.signal?.physical_score ?? 0)),
        summary: String(o.signal?.summary ?? ""),
      };
      out.sourcesOk++;
    }
  }

  return out;
}

// ── hook ───────────────────────────────────────────────────────────────────

export function useNeuralLive(code: string, refreshMs = 45_000): NeuralLive {
  const [state, setState] = useState<NeuralLive>({ sourcesOk: 0, sourcesTotal: 11, loading: true });
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    setState((s) => ({ ...s, loading: true }));
    let timer: ReturnType<typeof setInterval> | null = null;

    const run = async () => {
      const r = await fetchAll(code);
      if (alive.current) setState({ ...r, loading: false });
    };
    run();
    timer = setInterval(run, refreshMs);

    return () => {
      alive.current = false;
      if (timer) clearInterval(timer);
    };
  }, [code, refreshMs]);

  return state;
}
