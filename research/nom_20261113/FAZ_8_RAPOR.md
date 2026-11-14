# FAZ 8 — Loglama, gölge (paper) mod ve canlı kalibrasyon (NOM, 2026-11-13)

## Tablo: `public.nom_predictions` (Supabase, **uygulandı**)
Migration: `supabase/migrations/20261113_nom_predictions.sql` (proje `trading-ai-learning`, apply_migration ile).
Kolonlar: `t_dec` (karar anı), `horizon`, `geometry`, `model_version`, `price`, `atr` (ufkun ATR birimi), `t_end`,
LONG/SHORT `p_*_tp|sl|to` + `exp_r_*`, `status`, `feature_summary` (jsonb: yön başına 5 SHAP nedeni, rejim, seans,
VIX), `source`; sonuç: `outcome_long_cls|r`, `outcome_short_cls|r` (0 TP · 1 SL · 2 zaman · −1 çözülemedi),
`outcome_filled_at`. Tekil anahtar `(t_dec, horizon, geometry, model_version)` → upsert idempotent.
**RLS açık, anon politikası yok** (service-role yazar/okur; `shadow_pattern_trades` kalıbı). İndeksler: (ufuk, geometri,
t_dec desc) ve sonuç bekleyen kısmi indeks. `prediction_logs` / `signal_lifecycle`'dan tamamen izole.

## Gölge modu
- Kod: `backend/services/nom/shadow.py` — `record_once()` (tahmin → upsert), `fill_outcomes()` (ufku dolan satırları
  **eğitimdeki aynı `labels.label_batch`** ile, karar anında kaydedilen ATR'yle, NY-saati koruyucu spread modeliyle çözer),
  `shadow_loop()`.
- Çalıştırma: `NOM_SHADOW_ENABLED=1` (backend `main.py` döngüsü, **varsayılan KAPALI** — canlı sistemi kendiliğinden
  değiştirmemek için) veya `python backend/scripts/nom_shadow.py --loop|--once|--fill`. Kalıp `yeni deneme/*_shadow.py`
  ile aynı ilke: karar anında sonuç bilinmeden yaz, sonra çöz, fail-open, emir akışına dokunma.
- Varsayılan hedefler (`NOM_SHADOW_TARGETS`): 15m:1x1, 1h:1x1, 1h:1.5x1, 4h:1x1, 4h:1.5x1.5, session:1x1;
  aralık `NOM_SHADOW_INTERVAL_MIN=15`. Piyasa kapalıyken tahmin yazılmaz; sonuç doldurma her turda.
- Sızıntı: tahmin satırı yalnız `t_dec`'e kadar kapanmış barlarla üretilir; sonuç yalnız `t_end + 2 dk` sonrasında,
  giriş barından itibaren 1m barlarla.

## Canlı kalibrasyon raporu
`backend/services/nom/calibration.py` → `GET /api/probability/nasdaq/calibration?horizon=&geometry=&days=56`:
P(TP) kovası başına beklenen vs gerçekleşen oran, WF %95 bandıyla karşılaştırma (`bant_icinde`), haftalık (rolling)
Brier becerisi (gerçekleşen taban orana göre), ortalama gerçekleşen R, kalibrasyon eğimi, son 14 gün becerisi,
drift uyarısı. Panelde reliability grafiği olarak çizilir.

## MEZUNİYET KRİTERİ (sistem ancak bunlar sağlanınca "güvenilir" sayılır)
Her (ufuk, geometri, yön) hedefi için ayrı:
1. **Süre:** canlı gölgede ≥ **4 hafta** (≥ 28 gün) — tercihen 8 hafta, en az bir yüksek-VIX (≥18,4) haftası içermeli.
2. **Örneklem:** ≥ **300 bağımsız** çözülmüş tahmin (≥ 60 dk arayla; 15 dk ızgaradaki komşu tahminler bağımsız sayılmaz).
3. **Kalibrasyon:** P(TP) kovalarının **hepsinde** (n ≥ 20 olanlarda) gerçekleşen oran WF %95 bandının (±2 puan tolerans)
   içinde; kalibrasyon eğimi **0,7–1,3**.
4. **Beceri:** rolling Brier becerisi (taban orana göre) **≥ 0**; son 14 günün becerisi önceki dönemden ≥ 0,03 düşük
   değil (aksi hâlde drift).
5. **Ekonomi (yalnız yön önerisi için):** "kanıtlı" işaretli hedefte eşik üstü tahminlerin gerçekleşen ortalama R'si
   > 0 ve WF EV bandının alt sınırının üstünde. Kanıtsız hedefler ne olursa olsun yön önerisi vermez.
Biri tutmazsa: "güvenilir değil" — panel olasılıkları bilgi amaçlı gösterir, yön önerisi NÖTR kalır.
Uygulama: `calibration.side_report().mezuniyet` (1–4 otomatik; 5 Faz 5 kanıt bayrağına bağlı).

## Durum (bu oturum sonunda)
Tabloda yalnız örneklem dışı geri doldurma kayıtları var (aşağıda); canlı gölge döngüsü varsayılan KAPALI (açma kararı
kullanıcıda). Piyasa bu rapor anında kapalı (Cuma 17:00 ET sonrası).

## Örneklem dışı geri doldurma (2026-11-13, `scripts/nom_shadow.py --backfill 2026-11-04 2026-11-13T20:00 60`)
Model eğitim sonu 2026-11-03 → 11-04 sonrası gerçek örneklem dışı. Saatlik 175 karar anı × 6 hedef = 923 satır
(`source='backfill_oos'`), hepsi aynı etiket koduyla çözüldü (4 s'te hafta sonunu geçen 3 satır −1).
| Hedef | ort. P(TP) long → gerçekleşen | ort. P(TP) short → gerçekleşen | ort. R long / short |
|---|---|---|---|
| 15m 1/1 | 0,262 → 0,286 | 0,280 → **0,383** | −0,18 / −0,01 |
| 1h 1/1 | 0,323 → 0,303 | 0,349 → 0,349 | −0,06 / −0,03 |
| 1h 1,5/1 | 0,183 → 0,160 | 0,201 → 0,189 | −0,04 / −0,06 |
| 4h 1/1 | 0,321 → 0,320 | 0,346 → 0,366 | −0,03 / −0,00 |
| 4h 1,5/1,5 | 0,202 → 0,192 | 0,223 → 0,209 | −0,02 / −0,04 |
| seans 1/1 | 0,309 → **0,208** | 0,296 → **0,396** | −0,25 / +0,23 |
Ortalama düzeyde 1 s / 4 s iyi kalibre; 15 dk short ve seans ufkunda sapma = o haftanın düşüş yönü (model yön bilmiyor,
beklenen). 1 s 1/1 Brier becerisi long −0,003 / short +0,019 (9,8 gün, 175 bağımsız saatlik karar) → **mezun değil**
(süre < 28 gün); short tarafta drift uyarısı (son 14 gün / önceki ayrımı bu kısa pencerede anlamsız — ilk hafta).
Bu kayıtlar `source` ile ayrılır; panel tümünü gösterir, **resmi mezuniyet yalnız canlı gölge kayıtlarıyla**:
`GET /api/probability/nasdaq/calibration?…&source=shadow`.
