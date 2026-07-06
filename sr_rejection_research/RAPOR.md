# S/R & Trend-Channel Rejection × Model Deney Sistemi — Bulgular

**Soru:** Mevcut modellerimizin hangisi, hangi timeframe'de, hangi pips-toleransıyla,
S/R/trend-channel **rejection**'larından doğru sinyal verir?
**Veri:** 97,155 resolved model sinyali (pulse1/2/3, meta, smc, emel, ml:*, …), Mart-Haziran 2026,
4 sembol. S/R+linreg-channel motoru, **lookahead'siz** (seviye ancak teyit edildikten sonra aktif).

---

## 🏆 ANA BULGU: Trend-Channel Sınır Rejection'ı güçlü, sağlam, EVRENSEL bir WR-yükselticisi

Sinyal, fiyat **linreg trend-channel sınırında** iken geldiğinde (BUY→alt band / SELL→üst band,
fiyatın %T toleransı içinde), WR **%44-50 → %72-84**'e fırlıyor.

| Kaynak | Sonuç |
|---|---|
| **S/R pivot rejection** | Zayıf/karışık — geniş toleransta ZARAR (ters sinyal adayı) |
| **Trend-channel rejection** | ✅ **GÜÇLÜ** — aşağıdaki tüm bulgular bundan |

### En iyi config'ler (model başına, channel)
| Model | TF / tol% | n | WR | base | lift |
|---|---|---|---|---|---|
| **meta** | 5m / 0.1 | 218 | **83.9%** | 50.5% | +33.5 |
| **pulse2** | 15m / 0.06 | 194 | **77.3%** | 51.2% | +26.1 |
| **pulse3** | 15m / 0.06 | 309 | **75.7%** | 44.2% | +31.6 |
| **pulse3** | 30m / 0.2 | **1003** | 71.6% | 44.1% | +27.5 |
| **pulse1** | 30m / 0.06 | 210 | 72.4% | 42.0% | +30.4 |
| smc | 1h / 0.3 | 209 | 78.9% | 53.9% | +25.1 |
| ml:main | 5m / 0.1 | 168 | 82.1% | 61.4% | +20.7 |

---

## ✅ TİTİZLİK — bulgu sağlam mı? (EVET)

- **Placebo (697 combo, etiket karışık):** şansla en iyi lift p95 = **+17.5pp**, max +18.7pp.
  Gerçek lift'ler **+25-33pp** → bu barı net geçiyor (şans DEĞİL).
- **Walk-forward (zaman 60/40 OOS):** lift OOS'ta tutuyor:
  - pulse3 30m ch tol0.2: IS +27.5 → **OOS +26.3** (n=1003)
  - pulse3 30m ch tol0.15: IS +28.3 → **OOS +28.3** (birebir)
  - pulse3 30m ch tol0.1: IS +30.4 → **OOS +32.3**
- **Evrensel (per-symbol):** pulse3 30m channel tüm sembollerde +27-29pp (NDX +28, GDAXI +29,
  USOIL +28, XAU +27.5) — tek sembol sürüklemiyor.
- **Model-agnostik:** kanal-tek-başına (tüm modeller havuz) bile +20-26pp → asıl edge KANAL.

---

## 🔑 Detay içgörüler

1. **BUY (alt-band bounce) en güçlü:** pulse1/3 BUY @ alt-band → **%75 WR** (base %39-40, **+35pp**).
   SELL @ üst-band daha zayıf (+13-18pp). = oversold-bounce mean-reversion.
2. **En iyi TF: 15m-30m** (tatlı nokta). 5m ve 1h de çalışıyor; 4h biraz zayıf, daha az n.
3. **En iyi tolerans: %0.06-0.2** (dar = yüksek WR az sinyal; geniş = çok sinyal hafif düşük WR).
   pulse TP1 mesafesi medyan %0.1 = tolerans tatlı-noktasıyla aynı (tutarlı).
4. **Ekonomi:** pulse RR ≈ 0.67 (TP1 1.0×ATR / SL 1.5×ATR), breakeven WR %59.9.
   Kanal-WR %72-76 → **EV ≈ +0.23R/işlem** (sağlam +EV).

---

## ⚠️ Stratejik içgörü + ADX keskinleştirmesi

Bu bir **MEAN-REVERSION** edge'i (kanal ekstremlerinden dönüş) — botun momentum-continuation
tasarımının zıttı. AMA test edildi: **her ADX rejiminde tutuyor**, ranging'de daha güçlü:

| ADX (30m, kanal-rejection) | n | WR |
|---|---|---|
| <18 (ranging) | 351 | **79.5%** |
| 18-25 | 671 | 72.1% |
| 25-35 | 1206 | 71.8% |
| >35 (güçlü trend) | 1680 | **69.9%** |

→ Güçlü trendde bile %69.9 (base %49) — "düşen bıçak" korkusu DOĞRULANMADI; edge rejim-sağlam.
ADX-tek-başına düz (~%47-51) → asıl sürücü KANAL, ADX modülatör.
**Birleşik filtre (pulse3 30m): base %44 → +kanal %71.6 → +kanal+ADX<25 = %80.8** (n=239).

---

## 🎯 Deploy edilebilir reçete

> **Bir sinyal AÇ, ancak 15m veya 30m grafikte fiyat linreg trend-channel sınırının %0.1-0.15
> içindeyse, sinyal yönünde (BUY→alt band, SELL→üst band).** Özellikle BUY tarafı + düşük-ADX.
> Bu, pulse sinyallerini %44 (zarar) → %72-76 (+0.23R) yapar; meta için %84.

**En yüksek güven kombosu:** pulse3 (veya meta/pulse1) × 30m channel × tol 0.15 → n büyük, OOS +28pp.

---

---

# 🔬 NİHAİ — 4 adım tamamlandı + DOĞRULUK düzeltmeleri + z=2.5 inceltmesi

## ⚠️ Doğruluk düzeltmesi (kritik): LOOKAHEAD giderildi
`candle_time`=açılış; sinyal anında forming bar (henüz kapanmamış) kullanılıyordu →
2-5dk gelecek sızıntısı. `bar_at` artık yalnız **TAM KAPANMIŞ** barı kullanır
(open+tf_sec ≤ sinyal). **Edge düzeltmeden SONRA da aynı kaldı** (+26-36pp) → sızıntı yoktu, bulgu gerçek.

## 🏆 GÜNCELLENMİŞ ANA BULGU — kanal z-skoru z≥2.5 (orijinalden çok daha güçlü)
"Sınıra yakın" yerine **"trend çizgisinden ≥2.5σ ötede"** (aşırı oversold/overbought)
parametrelemesi WR'ı **%72 → %86-93**'e çıkardı, yüksek n + OOS-sağlam:

| model | TF | n | na | IS WR | **OOS WR** | OOS lift |
|---|---|---|---|---|---|---|
| **pulse3** | 5m | 30 | 3183 | 86.6% | **82.4%** | +42.7 |
| **pulse3** | 15m | 30 | 2209 | 86.6% | 82.4% | +42.6 |
| **pulse3** | 30m | 50 | 1154 | 88.2% | **87.5%** | +47.7 |
| **pulse1** | 1h | 80 | 572 | 88.3% | **90.7%** | +54.6 |
| **meta** | 15m | 80 | 333 | 93.1% | **92.7%** | +45.4 |

- **Placebo p95 = +11.8pp** → gerçek +42-54pp, EZİYOR.
- **Walk-forward OOS (sonraki %40):** test WR %82-92, base ~%40 → +42-55pp. Çok sağlam.
- n=30/50/80 hepsi çalışıyor (n az duyarlı). **z=2.5 tatlı nokta** (z=2.0'dan çok daha iyi).

## Adım sonuçları
- **Adım 1 — Çok-model anlaşması:** 2-model %72.3 vs solo %67.2 (+5pp); 3-model ek fayda yok.
  → Mütevazı bonus; asıl işi kanal yapıyor.
- **Adım 2 — Kanal-param:** z=2.5 >> z=2.0; n=30-80 hepsi iyi; **5m-30m en iyi**.
- **Adım 3 — 1m TF:** ZAYIF (+14-15pp, WR %60-66) — gürültülü. Tatlı nokta 5m-1h.
- **Adım 4 — Bota bağlama:** `yeni deneme/channel_filter.py` (z≥2.5 rejection filtresi, opt-in).

## 🎯 NİHAİ DEPLOY REÇETESİ
> Sinyali yalnız, **5m/15m/30m linreg trend çizgisinden ≥2.5σ ötede** + yönünde iken aç
> (BUY: z≤−2.5 = aşırı oversold / SELL: z≥+2.5). Pulse'u %44 → **%82-88 (OOS)** yapar; meta %93.
> En yüksek-n: pulse3 5m/15m n30 z2.5 (n=2000-3000). `channel_filter.is_channel_rejection()`.

## Stratejik sonuç
Bu **mean-reversion** edge'i botun momentum tasarımıyla çelişir → AYRI opt-in 'channel_reversion'
yolu olarak kur, momentum scope'larına dokunma. Önce `LIVE_TRADING=False` gözlemde fill+WR ölç.
