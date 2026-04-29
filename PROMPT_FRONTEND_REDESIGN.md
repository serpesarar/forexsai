# 🎨 Claude Code Prompt — Frontend Panel Reorganizasyonu

Aşağıdaki prompt'u Claude Code'a yapıştır. Önce NASDAQ sayfasını prototip olarak yapacak, onayından sonra diğer sembollere genişletecek.

---

```
Projemin frontend'inde ciddi organizasyon sorunu var: aynı paneller farklı yerlerde tekrar ediyor (Smart Money 2-3 yerde, EMEL 2-3 yerde), grafikler her panelde ayrı ayrı var, sekme yapısı mantıksız. Tüm frontend'i sembol-merkezli (symbol-centric) mimariye geçiriyoruz.

## HEDEF MİMARİ

Dashboard → Sembol kartlarına tıkla → O sembolün tüm panelleri tek sayfada

### Sayfa Yapısı (Yukarıdan Aşağıya — Önem Sırası)

**Bölüm 1 — Üst Bar (sayfa %8'i)**
Sol: Canlı fiyat + % değişim + spread
Sağ: Meta Signal özet kartı (BUY/SELL/HOLD + confidence + güç seviyesi)

**Bölüm 2 — Ortak Grafik (sayfa %25'i — en büyük alan)**
- TEK chart component, tüm paneller bunu paylaşır
- Timeframe sekmeleri: 5m | 15m | 1H | 4H | 1D
- Toggle overlay'ler: EMA lines, Order Block zones, Support/Resistance, Bollinger Bands
- Chart üzerinde aktif sinyallerin entry/TP/SL çizgileri
- Bu bölüm scroll'da sticky olmasın ama sayfanın en görünür yeri olsun

**Bölüm 3 — Sinyal Panelleri (sayfa %35'i — karar alanı)**
2×3 responsive grid:
| ML Prediction (0.25) | EMEL 9-Check (0.20) | Smart Money (0.10) |
| Pulse 1 Algo (0.15)  | Pulse 2 ML+TA (0.15) | Pulse 3 MTF (0.15)  |

Her panel kartı göstersin:
- Yön: BUY/SELL/HOLD (renk kodlu)
- Confidence: yüzde + progress bar
- Son sinyal zamanı
- Skor breakdown (mini bar chart veya radar)
- Status badge: CONFIRM / SCOUT / HOLD
- Kart tıklanınca expand → detaylı skor tablosu

Renk kodlaması tutarlı olsun:
- BUY = yeşil tonları
- SELL = kırmızı tonları  
- HOLD = gri/nötr
- CONFIRM = solid renk
- SCOUT = çizgili/yarı saydam

**Bölüm 4 — Piyasa Bağlamı (sayfa %12'si)**
3 kart yan yana:
| Market Regime | COT / Whale Tracker | AI Panel Özet |
- Market Regime: STRONG_TREND_UP/DOWN, RANGING, TRANSITION + ADX değeri
- COT: Whale pressure gauge (-1 to +1) + alert badge'leri
- AI Panel: DeepSeek'in son saatlik analiz özeti

**Bölüm 5 — Model Performans Scoreboard (sayfa %20'si)**
Yatay kaydırılabilir (horizontal scroll) kart dizisi:
Her model için bir kart: ML, PULSE 1, PULSE 2, PULSE 3, EMEL, SMC, AI Panel
Her kartta:
- Win Rate (büyük font, renk kodlu: >60% yeşil, 50-60% sarı, <50% kırmızı)
- Toplam sinyal sayısı
- Profit Factor
- Son 7 gün mini sparkline (win/loss pattern)
- Bu sembol için scope bazlı breakdown (ML kartında: ultra_safe, balanced, aggressive vs.)

## KRİTİK KURALLAR

1. **TEKRAR YOK:** Her panel tam olarak 1 kez görünür. Smart Money tek yerde, EMEL tek yerde.

2. **TEK GRAFİK:** Grafik component'i shared, props olarak sembol ve timeframe alır. Hiçbir panel kendi grafiğini render etmez.

3. **RESPONSIVE:**
   - Desktop: 2×3 grid sinyal panelleri, 3 kolon bağlam kartları
   - Tablet: 2×3 → 2 kolon
   - Mobil: tek kolon stack, scoreboard yatay scroll korunur

4. **SIMETRI:** Grid gap'ler eşit (16px), kart yükseklikleri satır içinde eşit (min-height), padding tutarlı

5. **RENK KODLAMASI (tutarlı, tüm panellerde aynı):**
   - Model renkleri: ML=mavi, EMEL=mor, PULSE'lar=turuncu/coral, SMC=teal, AI=amber
   - Sinyal renkleri: BUY=yeşil, SELL=kırmızı, HOLD=gri
   - Bu renkler hem sinyal kartlarında hem scoreboard'da hem chart overlay'de tutarlı

6. **GÖZ YORMAYAN TASARIM:**
   - Arka plan: soft/nötr
   - Kart kenarlıkları: ince (0.5-1px), yuvarlak köşeler
   - Font: okunabilir boyut (min 13px body, 16px değerler)
   - Beyaz alan: kartlar arası yeterli boşluk
   - Dark mode desteği zorunlu

7. **STATE YÖNETİMİ:**
   - Aktif sembol → URL param veya route param (/dashboard/NDX.INDX)
   - Tüm paneller aynı sembol context'inden okur
   - WebSocket bağlantısı tek, sembol bazlı subscribe

## UYGULAMA PLANI

### Adım 1: Önce mevcut durumu tara
- Tüm sayfa/sekme/panel component'lerini listele
- Tekrar edenleri işaretle
- Hangi component'in nerede kullanıldığını çıkar

### Adım 2: Yeni component yapısı oluştur
```
components/
├── layout/
│   ├── SymbolPage.tsx          ← ana sembol sayfası (5 bölümlü layout)
│   ├── SymbolSelector.tsx      ← üst navigation
│   └── SectionDivider.tsx      ← bölümler arası ayırıcı
├── price/
│   └── LivePriceBar.tsx        ← Bölüm 1 sol
├── meta/
│   └── MetaSignalCard.tsx      ← Bölüm 1 sağ
├── chart/
│   └── SharedChart.tsx         ← Bölüm 2 (TEK chart)
├── signals/
│   ├── SignalGrid.tsx          ← Bölüm 3 container (2×3 grid)
│   ├── SignalCard.tsx          ← Tekil model kartı (reusable)
│   ├── SignalCardExpanded.tsx  ← Detaylı görünüm
│   └── ConfidenceBar.tsx       ← Reusable confidence göstergesi
├── context/
│   ├── RegimeCard.tsx          ← Bölüm 4
│   ├── WhaleCard.tsx
│   └── AIPanelCard.tsx
├── performance/
│   ├── PerformanceScoreboard.tsx ← Bölüm 5 (horizontal scroll)
│   ├── ModelScoreCard.tsx       ← Tekil model performans kartı
│   └── WinRateSparkline.tsx     ← Mini grafik
└── shared/
    ├── StatusBadge.tsx         ← CONFIRM/SCOUT/HOLD badge
    ├── DirectionIndicator.tsx  ← BUY/SELL/HOLD ok + renk
    └── SkeletonLoader.tsx      ← Loading state
```

### Adım 3: SADECE NASDAQ sayfasını oluştur
- Route: /dashboard/NDX.INDX (veya /dashboard/nasdaq)
- Tüm 5 bölümü implement et
- Gerçek API endpoint'lerine bağla
- Loading, error, empty state'leri ekle
- Dark mode test et
- Responsive kontrol et (en az 3 breakpoint)

### Adım 4: Mevcut tekrar eden panelleri temizle
- Eski Smart Money duplicate'leri sil
- Eski EMEL duplicate'leri sil
- Eski ayrı grafik component'lerini kaldır (SharedChart'a geç)
- Kullanılmayan import'ları temizle

BİR UYARI: Eski panellerin hiçbirinin backend bağlantısını kırma. Sadece frontend reorganizasyonu.

Önce mevcut durumu tara ve bana raporla, sonra NASDAQ sayfasını oluştur. Diğer sembolleri sonra yapacağız.
```
