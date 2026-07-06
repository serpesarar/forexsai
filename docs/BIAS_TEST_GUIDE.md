# MiroShark Bias Doğruluk Testi — Kullanım Rehberi

Bu altyapı **ölçüm** içindir, otomasyon değil. Amaç: MiroShark'ı farklı
saatlerde çalıştırıp hangi seans/saat penceresinin en isabetli NASDAQ günlük
bias'ını ürettiğini **veriyle** bulmak — sonra canlıya bağlamaya karar vermek.

> **İzolasyon garantisi:** Bu harness `bias_test_log` tablosuna yazar. Canlı
> `daily_bias` tablosuna ve Precision Veto Engine'e **dokunmaz**. Canlı scalp
> sinyallerini hiçbir şekilde etkilemez.

---

## 0. Migration

Supabase'de çalıştır: `supabase/migrations/20260703_bias_test_log.sql` (idempotent — tekrar çalıştırılabilir).

---

## 🤖 Otomatik Mod (önerilen — sen çalıştırmazsın)

Native **debate motoru** (DeepSeek + Kimi) + **auto-runner** kurulu. Açarsan
backend, trading günlerinde NY saatiyle 08:00 ve 09:45'te debate'i kendi
çalıştırır, bias'ı loglar; 16:15 ET'de gün sonu sonuçları doldurur.

**`.env` (backend):**
```
# Model yönlendirmesi — önemli/debate → Kimi, normal → DeepSeek
DEEPSEEK_API_KEY=...            # (zaten olabilir)
KIMI_API_KEY=...               # Moonshot/Kimi anahtarı (MOONSHOT_API_KEY da olur)
KIMI_MODEL=kimi-k2-0711-preview   # gerçek Kimi 2.6 model id'siyle değiştir
# Otomatik çalışma (varsayılan KAPALI — token harcar):
BIAS_AUTO_RUN_ENABLED=1
BIAS_RUN_WINDOWS_ET=08:00=0800_main,09:45=0945_confirm
BIAS_FILL_TIME_ET=16:15
```

> **Not:** Auto-runner backend çalışırken tetiklenir. 7/24 için Railway'e deploy
> et; yerelde sadece backend açıkken çalışır. Model çağrıları ücretlidir — bu
> yüzden `BIAS_AUTO_RUN_ENABLED` varsayılan **kapalı**, sen açarsın.

Durumu kontrol: `GET /api/bias-test/routing-status` veya panelin üstündeki rozet
(`önemli→kimi · normal→deepseek · OTO✓`).

Manuel tetikleme (test için): `POST /api/bias-test/run-debate?run_label=test`
veya panelde **"🧠 Şimdi debate çalıştır"**.

---

## Manuel Mod (MiroShark çıktısını elle logla)

## 1. Zamanlamayı SABİTLEME — sen çalıştır, sistem loglar

Kod içinde saat yok. Sen MiroShark'ı istediğin saatte çalıştırır, çıkan JSON'u
`run_label` ile loglarsın. Sistem her çalıştırmaya seans bağlamını (NY saati,
DST-doğru seans, premarket/Asya/Londra, yarım gün/tatil, overlap) ekler.

**Önerilen iki pencere (ET):**
- **08:00 ET** — premarket olgunlaşmış, Londra yönü belli → `run_label=0800_main`
- **09:45 ET** — açılış ilk 15 dk teyidi → `run_label=0945_confirm`

İkisini de aynı gün logla; accuracy-report hangisinin daha isabetli olduğunu
gösterecek.

## 2. Her çalıştırmada bias'ı logla

MiroShark UI'dan (:3000) çıkan CIO JSON'unu gönder:

```bash
curl -sS -X POST http://localhost:8000/api/bias-test/log \
  -H "Content-Type: application/json" \
  -d '{
        "run_label": "0945_confirm",
        "nasdaq_daily_bias": "bullish",
        "confidence": 72,
        "trade_mode": "buy_dips_only",
        "main_support": 20150,
        "main_resistance": 20520,
        "invalid_if": "NQ breaks below premarket low",
        "reason_summary": "..."
      }'
```

Dönen cevap `current_session` ve `predicted_bias`'ı teyit eder. Geçmiş bir
çalıştırmayı backfill için `"run_timestamp_utc": "2026-07-06T13:30:00Z"` ekle.

## 3. Gün kapandıktan sonra sonuçları doldur

ABD kapanışından sonra (16:00 ET+) o günün gerçek NDX kapanış yönünü hesaplat:

```bash
# Bugün (NY) için:
curl -sS -X POST http://localhost:8000/api/bias-test/fill-outcomes
# Belirli bir gün için:
curl -sS -X POST "http://localhost:8000/api/bias-test/fill-outcomes?ny_date=2026-07-06"
```

Bu, o gün loglanan tüm satırların `was_correct` ve `invalid_if_triggered`
alanlarını doldurur. İdempotent — tekrar çalıştırırsan yeniden hesaplar.

## 4. 15-20 iş günü sonra raporu oku

```bash
curl -sS http://localhost:8000/api/bias-test/accuracy-report | jq
```

Örnek çıktı:

```
overall: 27/45 doğru (%60)
by_run_label:
  0800_main:    12/18 doğru (%67)
  0945_confirm: 14/18 doğru (%78)   ← daha isabetli pencere
by_confidence_bucket:
  high(>75): 10/12 (%83)            ← yüksek confidence gerçekten daha doğru
  med(60-75): 12/20 (%60)
  low(<60):  5/13 (%38)
by_session_overlap / by_half_day / by_holiday: ...
```

## 5. Canlıya bağlama kararı

| Isabet oranı | Karar |
|--------------|-------|
| **< %55** | Bağlama. Prompt'ları iyileştir, yeniden test et. |
| **%55–65** | Minimum eşik — dikkatle, düşük confidence'ları filtreleyerek bağlanabilir. |
| **> %65** | İyi — canlıya bağlamayı düşün (`daily_bias` + veto engine). |

En isabetli `run_label` + confidence bucket kombinasyonunu seç; canlı köprüde
(`/api/miroshark/webhook`) o saatte çalıştır.

---

## AŞAMA D — 9 Ajan Prompt'larına Seans Farkındalığı

> Bu repoda MiroShark'ın `9_AGENT_SYSTEM_PROMPTS.md` dosyası **yok** (MiroShark
> ayrı bir projede). Aşağıdaki eklemeleri MiroShark tarafındaki ilgili ajan
> system prompt'larına ekle. ForexSAI `session_context_service` bu bağlamı zaten
> `bias_test_log`'a nesnel olarak yazıyor; bu eklemeler ajanların o bağlamı
> muhakemede kullanmasını sağlar.

**Teknik Yapı ajanı:**
> "Londra seansının bugünkü yönünü ve ABD premarket'inin onu teyit edip
> etmediğini değerlendir. Londra güçlü ama premarket zayıfsa bu divergence'ı
> belirt — açılışta yön değişebilir."

**Volatilite ajanı:**
> "Session overlap (09:30-11:30 ET Londra+ABD çakışması) yüksek volatilite
> penceresidir. Yarım gün veya tatil arifesi ise likidite düşük, chop riski
> yüksek — bunu day_type'a yansıt."

**Makro ajanı:**
> "Asya gecesinde risk-off oldu mu (Asya overnight change negatifse) kontrol et
> — bu Avrupa ve ABD açılışına taşınabilir."

**CIO ajanı:**
> "Seans zincirini dikkate al: Asya → Londra → ABD yön aktarımı. Ama
> korelasyonun sabit OLMADIĞINI unutma — faiz şoku veya sektör ayrışması
> günlerinde Londra-NASDAQ bağı kopar. Korelasyonu veri olarak değerlendir,
> otomatik varsayma."
