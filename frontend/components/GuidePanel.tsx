"use client";

import { X, Target, AlertTriangle, Lightbulb, BarChart3, Activity } from "lucide-react";

interface GuideMetric {
  name: string;
  desc: string;
}

interface GuideAction {
  condition: string;
  action: string;
  direction: string;
}

interface GuidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  type: "orderblock" | "rtyhiim" | null;
  symbol?: string;
}

const ORDER_BLOCK_GUIDE = {
  title: "Order Block (SMC) Kullanım Kılavuzu",
  description: "Smart Money Concept (SMC) metodolojisine dayalı kurumsal alım/satım bölgelerini tespit eden bir sistemdir. Büyük oyuncuların (bankalar, hedge fonlar) işlem yaptığı bölgeleri belirler.",
  metrics: [
    { name: "Order Block", desc: "Kurumsal oyuncuların büyük hacimli işlem yaptığı fiyat bölgeleri. Bullish OB = alım bölgesi (fiyat buradan yukarı döner), Bearish OB = satım bölgesi (fiyat buradan aşağı döner)." },
    { name: "Score (0-100)", desc: "Order Block'un gücünü gösterir. 70+ = güçlü ve güvenilir OB, 50-70 = orta güçte, 50 altı = zayıf OB, dikkatli ol." },
    { name: "CHoCH (Change of Character)", desc: "Trend değişim sinyali. CHoCH varsa OB çok daha güvenilir çünkü piyasa yapısı değişmiş demektir." },
    { name: "BOS (Break of Structure)", desc: "Yapı kırılımı. Önceki swing high/low kırıldığında oluşur. Trendin devamını veya değişimini gösterir." },
    { name: "FVG (Fair Value Gap)", desc: "Dolmamış fiyat boşluğu. Fiyatın hızlı hareket ettiği ve 'adil değere' dönme ihtimalinin yüksek olduğu bölge." },
    { name: "Fib Level", desc: "Fibonacci geri çekilme seviyesi. 0.618 (Golden Ratio), 0.705 ve 0.786 en güçlü geri dönüş noktalarıdır." },
  ],
  actions: [
    { condition: "Bullish OB + Score >70 + CHoCH ✓", action: "LONG pozisyon aç", direction: "⬆️ Yukarı yön beklentisi", detail: "OB zone'unun alt sınırında limit order koy, stop-loss zone altına" },
    { condition: "Bearish OB + Score >70 + CHoCH ✓", action: "SHORT pozisyon aç", direction: "⬇️ Aşağı yön beklentisi", detail: "OB zone'unun üst sınırında limit order koy, stop-loss zone üstüne" },
    { condition: "OB + BOS + FVG (3'lü onay)", action: "Güçlü sinyal, pozisyon boyutunu artır", direction: "💪 Yüksek güvenilirlik", detail: "Confluence (üst üste gelen sinyaller) en güçlü trade fırsatlarıdır" },
    { condition: "Score <50 veya CHoCH yok", action: "Dikkatli ol veya bekle", direction: "⚠️ Riskli", detail: "Küçük pozisyon al veya daha iyi fırsat bekle" },
    { condition: "Fib 0.618-0.786 + OB overlap", action: "En iyi giriş noktası", direction: "🎯 Optimal R:R", detail: "Fibonacci ve OB'nin kesiştiği yer ideal giriş" },
  ],
  tips: [
    "Stop-loss'u her zaman OB zone'unun dışına koy (bullish için zone altı, bearish için zone üstü)",
    "Higher timeframe OB'ler (4H, Daily) lower timeframe'lerden (5m, 15m) daha güçlüdür",
    "Birden fazla OB üst üste geliyorsa (confluence) güvenilirlik artar",
    "Active Entry Signals kısmında gerçek zamanlı giriş fırsatlarını takip et",
    "Combined Signal bölümü ML modeli + Claude + Sentiment birleşik sonucunu gösterir",
  ],
};

const RTYHIIM_GUIDE = {
  title: "Ritim Dedektörü (RTYHIIM) Kullanım Kılavuzu",
  description: "Real-Time Rhythm Intelligence - Piyasadaki fiyat döngülerini ve ritimlerini tespit eden gelişmiş bir algoritmadır. Fiyatın periyodik hareketlerini analiz ederek tahmin yapar.",
  metrics: [
    { name: "Pattern Type", desc: "Tespit edilen dalga tipi. 'sine' = düzgün sinüs dalgası (en öngörülebilir), 'triangle' = üçgen dalga, 'square' = keskin dönüşler (volatil piyasa)." },
    { name: "Dominant Period", desc: "Baskın döngü periyodu (saniye cinsinden). Düşük değer (30-60s) = hızlı ritim, scalping için uygun. Yüksek değer (120s+) = yavaş ritim, swing için uygun." },
    { name: "Confidence (%)", desc: "Ritim tespitinin güvenilirliği. 70%+ = güçlü ve güvenilir sinyal, 50-70% = orta, 50% altı = zayıf, işlem yapma." },
    { name: "Regularity (%)", desc: "Ritmin düzenliliği/tutarlılığı. Yüksek = öngörülebilir hareket, düşük = kaotik/düzensiz piyasa." },
    { name: "Amplitude", desc: "Dalga genliği (fiyat aralığı). Yüksek = volatil piyasa, büyük hareketler. Düşük = dar range, küçük hareketler." },
    { name: "Predictions", desc: "30s, 60s, 120s sonrası için fiyat tahminleri. Confidence ile birlikte değerlendir." },
  ],
  actions: [
    { condition: "Confidence >70% + Regularity >70%", action: "Ritim güvenilir, döngüye göre işlem planla", direction: "✅ Güvenilir sinyal", detail: "Döngünün dip noktasında al, tepe noktasında sat" },
    { condition: "Direction = BUY + Should Trade = true", action: "LONG pozisyon aç", direction: "⬆️ Yukarı", detail: "Döngünün dip noktasına yaklaşılıyor, alım zamanı" },
    { condition: "Direction = SELL + Should Trade = true", action: "SHORT pozisyon aç", direction: "⬇️ Aşağı", detail: "Döngünün tepe noktasına yaklaşılıyor, satım zamanı" },
    { condition: "Direction = HOLD", action: "Bekle, işlem yapma", direction: "➡️ Yatay", detail: "Döngü ortasında veya geçiş aşamasında, sinyal yok" },
    { condition: "Confidence <50% veya Regularity <50%", action: "İşlem yapma", direction: "⚠️ Riskli", detail: "Ritim güvenilir değil, kaotik piyasa" },
  ],
  tips: [
    "Dominant Period değerine göre işlem süresini ayarla (period/2 kadar pozisyonda kal)",
    "Sine pattern en güvenilir, square pattern en riskli döngü tipidir",
    "Predictions bölümündeki fiyat tahminlerini support/resistance ile karşılaştır",
    "Order Block sinyalleri ile birleştirince güvenilirlik artar (confluence)",
    "Yüksek volatilite dönemlerinde (amplitude yüksek) stop-loss'u geniş tut",
  ],
};

export default function GuidePanel({ isOpen, onClose, type, symbol }: GuidePanelProps) {
  if (!isOpen || !type) return null;

  const guide = type === "orderblock" ? ORDER_BLOCK_GUIDE : RTYHIIM_GUIDE;
  const Icon = type === "orderblock" ? BarChart3 : Activity;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="fixed right-0 top-0 z-50 h-full w-full max-w-lg overflow-y-auto bg-background border-l border-white/10 shadow-2xl animate-slide-in-right">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-white/10 bg-background/95 backdrop-blur-sm px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20">
              <Icon className="h-5 w-5 text-accent" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">{guide.title}</h2>
              {symbol && <p className="text-xs text-textSecondary">{symbol}</p>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-white/10 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          <div className="rounded-xl bg-white/5 p-4">
            <p className="text-sm text-textSecondary leading-relaxed">{guide.description}</p>
          </div>

          {/* Metrics */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-accent mb-4">
              <Target className="h-4 w-4" />
              Metrikler ve Anlamları
            </h3>
            <div className="space-y-3">
              {guide.metrics.map((m) => (
                <div key={m.name} className="rounded-xl bg-white/5 p-4">
                  <p className="text-sm font-semibold text-white">{m.name}</p>
                  <p className="text-xs text-textSecondary mt-2 leading-relaxed">{m.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-success mb-4">
              <AlertTriangle className="h-4 w-4" />
              İşlem Kararları
            </h3>
            <div className="space-y-3">
              {guide.actions.map((a, i) => (
                <div key={i} className="rounded-xl bg-white/5 p-4 border-l-2 border-accent">
                  <p className="text-xs font-mono text-accent">{a.condition}</p>
                  <p className="text-sm font-semibold mt-2">{a.action}</p>
                  <p className="text-xs text-success mt-1">{a.direction}</p>
                  {"detail" in a && <p className="text-xs text-textSecondary mt-2">→ {a.detail}</p>}
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-warning mb-4">
              <Lightbulb className="h-4 w-4" />
              İpuçları
            </h3>
            <ul className="space-y-2">
              {guide.tips.map((tip, i) => (
                <li key={i} className="flex gap-2 text-sm text-textSecondary">
                  <span className="text-warning">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
