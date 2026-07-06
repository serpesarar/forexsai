# CORTEX — ForexSAI Bilişsel Katman Planı

> Amaç: ForexSAI'nin ürettiği her şeyi (sinyal, veto, bias, debate, **sonuç**)
> bir **hafıza + öğrenme** döngüsüne çevirmek. Bugün sistem çok üretiyor ama
> kendi geçmişini okumuyor — loglar bir hafıza değil, mezarlık. CORTEX o logları
> geri-besleme döngüsüne çevirir.
>
> Kapsam: **önce NASDAQ** (bias motoruyla aynı sınır), sonra genelleştir.
> Her katman **shadow-önce** (ölç, sonra bağla), **flag ile opt-in**, mevcut
> sistemi bozmadan üstüne oturur.

---

## 1. Araştırma temeli (ne doğrulandı, neyi uyarladık)

| Kaynak | Aldığımız | Uyarlama |
|--------|-----------|----------|
| **TradingAgents** (Tauric, v0.2.0) | Kalıcı karar günlüğü → gerçekleşen getiri → tek-paragraf reflection → sonraki prompt'a enjekte | Reflection-injection'ı **Faz 3** yapıyoruz; bizim debate yapımız zaten birebir örtüşüyor (analist + bull/bear + CIO) |
| **FinMem** (AAAI) | Katmanlı hafıza (sığ/orta/derin), decay, recency/relevance/importance skoru | Katmanlamayı **decay yerine "işlem-günü granülaritesi"** ile alıyoruz; skorun tamamını değil, yapısal benzerliği kullanıyoruz |
| **Reflexion** (NeurIPS'23) | Ağırlık güncellemeden **sözel** pekiştirme; ders → epizodik buffer | **Faz 3** dersleri + **Faz 5** öz-eleştiri |
| **pgvector / Supabase** | Embedding'ler aynı Postgres'te, HNSW | **Faz 4**'e ertelendi (sadece serbest-metin/haber için; yapısal base-rate'e gerek yok) |

**Ana içgörü:** bizim "gün durumu" (situation) çoğunlukla **yapısal sayısal**
bir vektör (seans + makro + QQQ + önceki gün). Yapısal-kNN ile analog gün bulmak
embedding'den **daha ucuz (0 LLM), daha yorumlanabilir (gerçek base-rate) ve daha
hızlı**. Bu, planın en önemli verimlilik kararı.

---

## 2. Mimari — 4 hafıza katmanı (beyin analojisi)

```
                    ┌───────────────────────────────────────────┐
                    │                 CORTEX                     │
                    │                                            │
  gün durumu  ───▶  │  Hipokampus  →  cortex_episodes            │  epizodik hafıza
  (situation)       │  (ne oldu, ne dedik, ne çıktı)            │
                    │        │                                   │
                    │        ▼                                   │
  debate öncesi ◀── │  Neokorteks →  analog retrieval (kNN)      │  "bugüne benzer
  base-rate enjekte │  (top-K benzer gün → gerçek base-rate)    │   günlerde ne oldu"
                    │        │                                   │
                    │        ▼                                   │
  ajan parlaklığı ◀─│  Bazal ganglia → cortex_trust             │  kredi ataması
  + prompt ağırlığı │  (hangi ajan/saat/bağlam ne kadar isabetli)│  (dopamin)
                    │        │                                   │
                    │        ▼                                   │
  yarının prompt'u ◀│  Prefrontal → cortex_lessons (reflection)  │  öz-eleştiri
  + ders enjekte    │  (bugünkü hatadan çıkan ders)             │
                    └───────────────────────────────────────────┘
```

**Situation vektörü** (analog retrieval'ın anahtarı — hepsi nullable, retrieval
sadece mevcut alanları tartar):

| Grup | Alanlar |
|------|---------|
| Seans | current_session, session_overlap, is_half_day, minutes_to_us_open (bucket) |
| Yön aktarımı | london_direction (up/down/flat), asia_overnight_change (varsa) |
| Premarket | qqq_premarket_change (bucket: strong_up/up/flat/down/strong_down) |
| Makro | **vix_regime (⭐ EN AĞIR ALAN — 2026-06-27 doğrulanmış edge: VIX rejimi NDX yönünü +25pp tahmin ediyor, placebo p=0, OOS +17; macro_ndx_test'teki rejim tanımı aynen)**, vix_chg, dxy_chg, us10y_chg |
| Rejim | market_regime (`market_regime_service`: STRONG_TREND_UP/DOWN, RANGING, TRANSITION — zaten mevcut, cache'li) |
| Yapı | prior_day_dir + büyüklük, 5g range konumu |
| Takvim | day_of_week, **high_impact_event_today (FOMC/CPI/NFP — `economic_calendar_service` zaten mevcut, CALENDAR_GATE bunu kullanıyor)** |
| **Sonuç** | actual_close_direction, actual_change_pct (gün kapanınca dolar) |

> **Veri birikim beklentisi (gerçekçi):** günde 2 run ≈ ayda ~40 epizod. K=8
> analog için anlamlı havuz **~2-3 ay** ileriye-dönük veri ister. Backfill
> (NDX günlük + VIX/DXY/US10Y geçmişi + takvim) bunu kısaltır ama London/QQQ
> alanları geçmişte yoktur (partial-null eşleştirme bu yüzden zorunlu tasarım).
> İlk haftalarda base-rate'ler geniş shrinkage ile sunulur; "3. haftada
> çalışmıyor" yanılgısına düşme — bu katman zamanla değerlenen bir varlık.

**Mesafe:** mevcut (null olmayan) alanlar üzerinden ağırlıklı toplam
(kategorik: eşleşme 0/1; sayısal: normalize |fark|). Ağırlıklar başta eşit,
Faz 2'de kredi-atamasından öğrenilir. **Base-rate:** top-K'nın sonuç dağılımı,
**küçük-örneklem shrinkage** ile prior'a (%50) çekilir (n<20 → gürültü uyarısı).

---

## 3. Fazlar (build sırası)

### FAZ 1 — Epizodik hafıza + Analog retrieval  ⭐ EN YÜKSEK GETİRİ, BURADAN BAŞLA
**Ne:** Her bias-run (ve opsiyonel her NASDAQ sinyal) için situation vektörünü
sakla; gün kapanınca sonucu doldur (bias-test harness'ı zaten yapıyor). Debate
öncesi, bugüne en benzer K günü çekip **gerçek base-rate'i** CIO prompt'una
enjekte et: *"Londra yukarı + QQQ premarket zayıf + VIX yükseliyor olan son 8
günde NDX 6 kez soldu (ort −0.4%). Bunu tart."*

**Dosyalar:**
- Migration: `cortex_episodes` (situation kolonları + decision + outcome + partial-null destekli).
- `services/cortex_memory.py` — `record_episode()`, `fill_episode_outcome()` (bias-test fill'e kancalanır), `find_analogs(situation, k, weights) -> {analogs, base_rate, sample_n, shrunk_rate}`.
- `bias_debate_engine`: CIO prompt'una `find_analogs` base-rate bloğu (flag `CORTEX_ANALOGS_ENABLED`).
- Backfill: `candle_cache` NDX günlük (sonuç) + `macro_data_service` VIX/DXY/US10Y **geçmişi** (yfinance history var) → kısmi tarihsel epizodlar. QQQ/London ileriye doğru birikir.

**Ölçüm (shadow):** her debate'te "analog base-rate ne derdi" vs "debate ne dedi"
vs "gerçek" → bias-test harness'ına ek kolon. Analog isabeti debate'i geçiyorsa
enjeksiyon kalıcılaşır.

**Maliyet:** 0 LLM (SQL/in-memory kNN). **Risk:** düşük (sadece prompt zenginleştirme).

---

### FAZ 2 — Ajan-stance enstrümantasyonu + Kredi ataması (trust)
**Ne (önce enstrümantasyon):** Her ajan sadece serbest metin değil, **yapısal bir
duruş** da üretsin: `{lean: bullish|bearish|neutral, conviction: 0-100,
key_factor: "..."}`. Bu, ajanları **tek tek hesap verebilir** kılar (şu an
debate tek verdict veriyor, ajan bazında kredi atanamıyor — bu bunu çözer).

**Ne (sonra kredi):** Gece işi `cortex_learn`: notlanmış epizodlardan
(ajan × bağlam-bucket × run_saati × bias_state) yuvarlanan isabet hesapla,
`cortex_trust` tablosuna yaz. Geri-besleme:
- **Panel:** nöron parlaklığı = son 30g trust (beyin hangi nöronuna güveniyor).
- **CIO prompt:** *"Makro ajanın son dönemde %78 isabetli, Teknik %52 — buna göre tart."*
- **Meta-model:** trust + analog base-rate, mevcut Stage-4 meta-classifier'a **feature** olur (makro feature'ları zaten persist ediyoruz — sinerjik).

**Dosyalar:** `bias_debate_engine` (stance şeması), migration `cortex_trust`,
`services/cortex_learn.py` (auto-runner'ın fill adımından sonra çağrılır).

**Maliyet:** stance = 0 ek çağrı (aynı ajan cevabında). Learn = 0 LLM (SQL).

---

### FAZ 3 — Reflection Journal (Reflexion / TradingAgents deseni)
**Ne:** Sonuç dolunca `cortex_reflect`: LLM tek paragraf ders yazar —
*"bullish %71 dedim, soldu; hata = yükselen VIX ve kırmızı QQQ premarket'i
küçümsemek; ders = VIX +5%↑ ve QQQ premarket kırmızıysa bullish yapıyı iskonto et."*
`cortex_lessons`'a yaz. Sonraki debate'e **aynı-bağlam + son cross-bağlam
derslerini** enjekte et (TradingAgents birebir bu).

**Dosyalar:** migration `cortex_lessons`, `services/cortex_reflect.py`
(gün-sonu, günde 1 LLM çağrısı — Kimi/önemli tier), `bias_debate_engine` ders enjeksiyonu.

**Maliyet:** günde 1 LLM çağrısı. **Değer:** sistem sözel olarak öğrenir.

---

### FAZ 4 — Semantik hafıza (pgvector) — OPSİYONEL
**Ne:** Ajan gerekçesi / haber metinlerini gömüp pgvector HNSW ile **anlamsal**
benzer günleri de çağır ("son sıcak-CPI + Fed günü"). Yapısal analogun
yakalayamadığı anlatısal benzerlikler.

**Ön koşul:** Supabase'de `pgvector` extension (aç), bir embedding modeli seç
(OpenAI text-embedding-3-small 1536d veya offline model — maliyet/gizlilik kararı).

**Neden ertelendi:** Yapısal analog değerin %80'ini %20 maliyetle verir; pgvector
embedding başına ücret + model bağımlılığı getirir. Önce Faz 1-3'ün işe
yaradığını ölç.

---

### FAZ 5 — Meta-biliş / Öz-eleştiri (completeness critic)
**Ne:** Periyodik "beyin sistematik olarak neyi yanlış yapıyor?" analizi →
kör noktaları çıkarır, prompt/eşik değişikliği **önerir** (insan onayına). Örn:
"choppy günlerde %38 isabet — choppy tanımını sıkılaştır." Reflexion'ın üst-katı.

**Dosyalar:** `services/cortex_metacritic.py` (haftalık), öneriler `spawn_task`
tarzı insan-onaylı kuyruğa.

---

## 4. GÖZDEN GEÇİRME — verimlilik doğrulaması

Planı yazdıktan sonra tekrar elden geçirdim; şu optimizasyonları yaptım:

| Karar | Neden |
|-------|-------|
| **Faz 0 (episodes tablosu) ile Faz 1'i BİRLEŞTİRDİM** | Analog retrieval zaten episodes'a ihtiyaç duyuyor; ayrı faz yapay bölünme olurdu |
| **pgvector'ı Faz 4'e ERTELEDİM** | Yapısal-kNN base-rate'in %80 değeri %20 maliyeti; embedding'i erken kurmak israf |
| **Ajan-stance enstrümantasyonunu Faz 2'ye EKLEDİM** | Kredi ataması ve panel-parlaklığı vizyonu **imkânsızdı** (debate tek verdict veriyor); ajanların tek tek duruş üretmesi bunu açan gerçek kilit — review'de fark ettim |
| **Küçük-örneklem shrinkage EKLEDİM** | n<20 analogda ham base-rate gürültü; prior'a çekmezsek beyin erken dönemde yanlış öğrenir |
| **Backfill'i Faz 1'e dahil ettim** | Analog gücü tarih ister; VIX/DXY/US10Y + NDX günlük geçmişi zaten var → soğuk-başlangıcı kısaltır |
| **CORTEX → mevcut meta-model beslemesi** | Ayrı ML kurmak yerine trust+base-rate'i Stage-4 meta-classifier'a feature yapmak; makro feature'ları zaten persist ediyoruz (sinerji) |
| **(2. tur) vix_regime = en ağır alan** | Projenin KENDİ doğrulanmış edge'i (2026-06-27: VIX rejimi → NDX yönü +25pp, placebo p=0, OOS +17) vektörde birinci sınıf değildi — en güçlü bilinen sinyali analog eşleştirmenin merkezine koymamak israftı |
| **(2. tur) market_regime + takvim bayrağı eklendi** | `market_regime_service` ve `economic_calendar_service` zaten çalışıyor; FOMC/CPI günleri birbirine benzer — bedava ayırt edicilik |
| **(2. tur) veri-birikim beklentisi yazıldı** | Ayda ~40 epizod gerçeği; erken "çalışmıyor" yanılgısını önlemek için timeline netleştirildi |

**Nihai sıra (en verimli):**
`Faz 1 (analog, 0 LLM, en yüksek ROI)` → `Faz 2 (stance + trust)` →
`Faz 3 (reflection)` → `[ölç, işe yarıyorsa]` → `Faz 4 (pgvector)` → `Faz 5 (meta-critic)`.

Her faz kendi başına **ship edilebilir** ve **bias-test harness'ıyla ölçülür**;
bir faz değer katmıyorsa sonrakine geçmeyiz.

---

## 5. Ön koşullar, riskler, ölçüm

- **Ölçüm:** her katman bias-test accuracy harness'ına ek kolon olarak shadow ölçülür (analog-vs-debate-vs-gerçek). Katman isabeti artırmıyorsa bağlanmaz.
- **Maliyet:** Faz 1-2 = 0 ek LLM; Faz 3 = günde 1; Faz 4 = embedding başına ücret.
- **Riskler:** (a) küçük örneklem → shrinkage + sample_n gösterimi; (b) overfitting geçmişe → walk-forward, sadece ileriye doğru trust; (c) sızıntı → outcome dolmadan retrieval'a girmesin (episode outcome NULL ise base-rate'e katılmaz).
- **Kapsam:** NASDAQ-only; DAX/XAU/USOIL dokunulmaz. Flag'ler: `CORTEX_ANALOGS_ENABLED`, `CORTEX_TRUST_ENABLED`, `CORTEX_REFLECT_ENABLED`.
- **Görselleştirme:** nöral panel genişler — analog günler, trust-parlaklığı, bugünün dersi.

## 6. Öneri
**Faz 1'den başla.** 0 LLM maliyeti, en yüksek getiri, mevcut harness'la anında
ölçülebilir. İşe yaradığını görünce Faz 2-3'e geçeriz.
