/**
 * NASDAQ Olasılık Motoru (NOM) API istemcisi — karar desteği, emir açmaz.
 * Backend: routers/nom_router.py
 *   GET /api/probability/nasdaq?horizon=&geometry=
 *   GET /api/probability/nasdaq/meta
 *   GET /api/probability/nasdaq/calibration?horizon=&geometry=&days=
 */

import { useQuery } from "@tanstack/react-query";
import { getApiBase } from "./base";

const API = getApiBase();
const REFRESH_MS = 60_000;
const CAL_REFRESH_MS = 10 * 60_000;

export type NomHorizon = "15m" | "1h" | "4h" | "session";
export const NOM_HORIZONS: { key: NomHorizon; label: string }[] = [
  { key: "15m", label: "15 dk" },
  { key: "1h", label: "1 saat" },
  { key: "4h", label: "4 saat" },
  { key: "session", label: "Seans sonu" },
];
export const NOM_GEOMETRIES = ["1.0x1.0", "1.5x1.0", "2.0x1.0", "1.0x1.5", "1.5x1.5"];

export interface NomBand {
  n: number;
  pred: number;
  obs: number;
  ci_lo: number;
  ci_hi: number;
  kova: [number, number];
  anahtar: string;
}

export interface NomReason {
  ozellik: string;
  ad: string;
  deger: number | null;
  katki: number;
  metin: string;
}

export interface NomSide {
  p_tp_once: number;
  p_sl_once: number;
  p_zaman_asimi: number;
  beklenen_r: number;
  p_tp_bandi: NomBand | null;
  beklenen_r_bandi: NomBand | null;
  taban: { p_tp: number | null; beklenen_r: number | null };
  esik: number | null;
  kanitli: boolean;
  neden: NomReason[];
}

export interface NomLevel {
  price: number;
  dist_atr: number;
  kind: string;
  tests: number;
}

export interface NomRsi {
  rsi14: number;
  asiri_alima_uzaklik: number;
  asiri_satima_uzaklik: number;
  bolge: string;
}

export interface NomContext {
  fiyat: number;
  atr_h1: number;
  destekler: NomLevel[];
  direncler: NomLevel[];
  rsi: Record<string, NomRsi>;
  trend: { h1_ema_dizilim: number | null; h1_psar_yon: number | null; h1_adx: number | null; h1_yapi_hh_hl: number | null };
  rejim: string;
  atr_rejim_h1: number | null;
  seans: string;
  vix: { deger: number; rejim: string } | null;
  yaklasan_olay: { olay: string; zaman_utc: string; dakika: number } | null;
}

export interface NomResponse {
  model: { surum: string; egitim_sonu: string | null; veri_surumu: string | null };
  ufuk: NomHorizon;
  geometri: string;
  not: string;
  yon_uyarisi?: string;
  durum: string;
  durum_nedeni?: string;
  aciklama?: string;
  veri?: { kaynak: string; son_bar_kapanis_utc: string; gecikme_sn: number };
  tahmin: { long: NomSide; short: NomSide } | null;
  yeniden_oynatma?: string;
  baglam?: NomContext;
  atr_ufuk?: { tf: string; deger: number };
}

export interface NomCalBucket {
  kova: [number, number];
  n: number;
  beklenen: number;
  gerceklesen: number;
  wf_bandi: [number, number];
  bant_icinde: boolean;
}

export interface NomCalSide {
  n: number;
  tp_orani?: number;
  ort_p_tp?: number;
  brier_beceri?: number | null;
  ort_R?: number;
  kovalar?: NomCalBucket[];
  haftalik?: { hafta: string; brier_beceri: number | null }[];
  mezuniyet?: { gun: number; bagimsiz_n: number; bant_disi_kova: number; brier_beceri: number; kalibrasyon_egimi: number; mezun: boolean };
  drift_uyarisi?: boolean;
  wf_referans: { lo: number; hi: number; n: number; pred: number; obs: number; ci_lo: number; ci_hi: number }[];
}

export interface NomCalibration {
  ufuk: string;
  geometri: string;
  gun: number;
  surum: string | null;
  n_satir: number;
  long: NomCalSide;
  short: NomCalSide;
  mezuniyet_olcutu: string;
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export const fetchNom = (h: NomHorizon, g: string, asof?: string | null) =>
  getJson<NomResponse>(
    `${API}/api/probability/nasdaq?horizon=${h}&geometry=${encodeURIComponent(g)}${asof ? `&asof=${encodeURIComponent(asof)}` : ""}`,
  );

export const fetchNomCalibration = (h: NomHorizon, g: string, days = 56) =>
  getJson<NomCalibration>(`${API}/api/probability/nasdaq/calibration?horizon=${h}&geometry=${encodeURIComponent(g)}&days=${days}`);

export function useNomProbability(h: NomHorizon, g: string, asof?: string | null) {
  return useQuery<NomResponse>({
    queryKey: ["nom", h, g, asof ?? ""],
    queryFn: () => fetchNom(h, g, asof),
    refetchInterval: REFRESH_MS,
    placeholderData: (prev) => prev,
  });
}

export function useNomCalibration(h: NomHorizon, g: string, days = 56) {
  return useQuery<NomCalibration>({
    queryKey: ["nom-cal", h, g, days],
    queryFn: () => fetchNomCalibration(h, g, days),
    refetchInterval: CAL_REFRESH_MS,
  });
}
