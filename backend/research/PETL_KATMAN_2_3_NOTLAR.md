# Post-Entry Trajectory Learner — Katman 2 & 3 Not Defteri

> Bu dosya Katman 1 deploy edildikten sonra (commit `3ca5822`, 2026-05-19)
> Katman 2 ve 3'e devam etmek için referans not defteridir.
> Yeni bir Claude oturumunda direkt bu dosyayı oku → kaldığın yerden devam.

---

## ÖZET — Üç katmanlı strateji

| Katman | Veri kaynağı | Eğitim süresi | Durum | Güç |
|---|---|---|---|---|
| **1: Entry-Quality** | `prediction_logs.factors` (entry snapshot) | dakikalar | ✅ Deployed | Zayıf-orta (XAU AUC 0.53, USOIL 0.78) |
| **2: Synthetic Trajectory** | candle archive → reconstruct trajectory | 1-2 saat | ⏳ Hazır değil | Yüksek (entry → exit boyunca evolution) |
| **3: Real Trajectory** | `signal_trajectory_snapshots` (canlı) | 4-6 hafta sonra | 📊 Veri toplanıyor | En yüksek (gerçek tick + gerçek timing) |

Katman 1 zaten production'da. Katman 2 esas değer kazanımıdır.

---

## Katman 2 — Synthetic Trajectory Model (sıradaki iş)

### Konsept

Her tarihsel sinyalin **`created_at` → `exit_time`** aralığındaki mumları çek,
o aralıkta her N dakikada bir (örn. 3-5 dakika) **indikatör değerlerini yeniden hesapla**,
böylece o sinyale ait sentetik trajectory time-series oluştur.

Sonra exit-predictor classifier'ı bu trajectory'lerle eğit:
- Input: entry features + her timestep'te delta'lar + zaman dinamikleri
- Output: P(SL hit) given trajectory so far
- Use case: Canlı sinyal sırasında her lifecycle check'inde skor → eşiği geçerse abort

### Gerekli veriler (zaten DB'de mevcut)

| Tablo | Alan | Kullanım |
|---|---|---|
| `prediction_logs` | `id`, `symbol`, `model_type`, `ml_direction`, `factors`, `created_at`, `exit_time`, `status`, `highest_profit_pips`, `lowest_drawdown_pips`, `exit_price`, `ml_entry_price` | Etiketli sinyal listesi |
| `candle_cache` | symbol, timeframe, timestamp, OHLCV | Sentetik trajectory için ham veri |
| (alternatif) DataHub | `_candles_5m`, `_candles_15m`, `_candles_30m`, `_candles_1h` | Tek çağrıda çekilemez ama backup |

### Implementation iskeleti

Yeni dosya: `backend/research/train_synthetic_trajectory_model.py`

```python
# Pseudo-code
def reconstruct_trajectory(signal: dict, interval_minutes: int = 5) -> list[dict]:
    """For one signal, build a synthetic trajectory from candle_cache."""
    start = signal["created_at"]
    end = signal["exit_time"]
    candles = fetch_candles(
        symbol=signal["symbol"], timeframe="5m",
        start=start, end=end
    )
    snapshots = []
    for ts in iterate_intervals(start, end, interval_minutes):
        # Resample candles up to this timestamp
        partial = candles[candles.timestamp <= ts]
        if len(partial) < 50:  # need enough history for indicators
            continue
        features = compute_indicators(partial)  # RSI, MACD, EMA, ATR, SAR, etc
        snapshots.append({
            "age_minutes": (ts - start).total_seconds() / 60,
            "current_price": float(partial.close.iloc[-1]),
            "features": features,
        })
    return snapshots

def build_training_examples(signal: dict, trajectory: list[dict]) -> list[tuple]:
    """One signal → multiple training rows (one per snapshot).
    Label propagates: every snapshot of a stopped signal is labeled 1."""
    label = 1 if signal["status"] == "stopped" else 0
    entry_factors = signal["factors"]
    rows = []
    for snap in trajectory:
        feature_vec = build_feature_vector(entry_factors, snap)
        rows.append((feature_vec, label))
    return rows
```

### compute_indicators() — yeniden kullanılabilir mi?

`backend/services/signal_feature_snapshot.py` zaten benzer şey yapıyor ama o LIVE veri kullanıyor.
Sentetik için **partial candle array'inden** aynı indikatörleri hesaplayan bir
fonksiyon gerek. Mevcut kodu refactor edip historical_snapshot() variant'ı
eklenebilir. Veya tek seferlik bir script'te baştan implement:
- `pandas-ta` veya `ta` kütüphanesi kullan
- RSI, MACD, EMA-20/50/200, ATR, BBands, Parabolic SAR
- Volume z-score (rolling mean/std)

### Eğitim dataset boyutu

Tarihsel 75k sinyal × ortalama 30dk yaşam / 5dk interval = **~6 snapshot/sinyal**
→ Toplam **~450k training row**. LightGBM rahatlıkla işler.

### Hangi feature'lar dahil olmalı?

```
ENTRY: [60 entry feature]                 # signal başında nasıldı
CURRENT: [60 current feature]              # bu snapshot anında nasıl
DELTA: [60 delta = current - entry]        # ne kadar değişti
DYNAMICS: [
  age_minutes,                             # signal kaç dk yaşıyor
  current_profit_pips,                     # şu an kâr/zarar pip
  current_drawdown_pips,
  distance_to_tp1_pct,                     # TP1'e kaç % yol kaldı
  distance_to_sl_pct,                      # SL'e kaç % yol kaldı
  price_velocity,                          # son N dk fiyat eğimi
  volume_acceleration,
]
DIRECTION_HINT: [direction_is_buy]
```

### Walk-forward önemli

Sentetik trajectory'lerde *temporal leakage* riski yüksek — eğitim setinin
ilerideki sinyallerini eğitirken görmemen şart. Stratified split YERİNE:
- Train: tüm sinyallerin `created_at` < cutoff_date
- Val: cutoff_date < `created_at`

### Inference yolu

`backend/services/signal_trajectory_service.py` zaten var (Katman 1 deployment'tan).
İçine ekle:
```python
def predict_p_sl_with_model(signal, current_snapshot, age_minutes):
    """Load symbol-specific synthetic trajectory model, return P(SL)."""
    ...
```

`signal_lifecycle.py` zaten her check'te `capture_snapshot()` çağırıyor.
Onun yanına `predict_p_sl_with_model()` eklenir, threshold'u geçerse abort.

### Eğitim komutu

```bash
cd /Users/melihcanodacioglu/Desktop/panel
set -a && source .env && set +a
cd backend
python research/train_synthetic_trajectory_model.py \
    --symbol XAUUSD --days 180 --interval 5 --min-snapshots 3
```

### Beklenen sonuç

- AUC > 0.70 (Katman 1'in 0.53'üne göre büyük kazanç)
- Block threshold: precision ≥ 0.80 ile recall %30-50
- Pratik etki: ortalama bir XAUUSD SL trade'inin yarısı erken abort'lanır → loss yarıya iner

---

## Katman 3 — Real Trajectory Model (4-6 hafta sonra)

### Konsept

PETL v1 zaten her lifecycle check'te `signal_trajectory_snapshots` tablosuna
gerçek snapshot yazıyor (commit `e6d058f`, 2026-05-19'da deploy).

4-6 hafta sonra (≥1k signal × ≥3 snapshot biriktiğinde) bu gerçek veriyle eğit.
Hazır trainer: `backend/research/train_exit_model.py` (Katman 1 ile aynı commit'te).

### Komut

```bash
python research/train_exit_model.py --symbol XAUUSD --days 90 --min-snapshots 3
```

### Katman 3 vs Katman 2 farkı

| | Katman 2 (sentetik) | Katman 3 (gerçek) |
|---|---|---|
| Kaynak | candle_cache → indikatör hesabı | Gerçek tick'lerle yapılmış snapshot |
| Doğruluk | İndikatör hesabı tam reproducible | Hafif noise ama gerçek timing |
| Veri var mı | 75k sinyal × tarihsel mum | Yeni biriken trajectory |
| Hız | Hemen | 4-6 hafta sonra |
| Bağımsız | Katman 2'siz de işler | Katman 2'yi production'da kullanırken arka planda eğitilebilir |

İdeal sıralama: Katman 2 hemen → Katman 3 hazır olunca **karşılaştırma referansı**
olarak kullan. Katman 3'ün AUC'si Katman 2'den daha iyiyse production'a Katman 3'e geç.

---

## Mevcut altyapı haritası (ne nerede)

```
backend/
├── research/
│   ├── train_entry_quality_model.py     ✅ Katman 1 — DEPLOYED
│   ├── train_exit_model.py              📋 Katman 3 — hazır, veri bekliyor
│   └── train_synthetic_trajectory_model.py  ⏳ Katman 2 — YOK, yazılacak
├── services/
│   ├── entry_quality_service.py         ✅ Katman 1 inference
│   ├── signal_trajectory_service.py     ✅ Snapshot capture (v1 rule-based)
│   ├── signal_feature_snapshot.py       ✅ Feature builder (LIVE)
│   └── prediction_logger.py             ✅ Hook'lar var
├── models/
│   ├── entry_quality_XAUUSD.joblib + .meta.json     ✅
│   ├── entry_quality_USOIL_FOREX.joblib + .meta.json ✅
│   └── (gelecek) exit_model_XAUUSD.joblib            ⏳
│   └── (gelecek) synthetic_traj_XAUUSD.joblib        ⏳
└── routers/
    └── ai_ops_router.py:
        GET /api/ai-ops/entry-quality/status         ✅
        GET /api/ai-ops/entry-quality/block-stats    ✅
        GET /api/ai-ops/trajectory/stats             ✅
```

DB tabloları (`supabase/migrations/`):
- `20260519_signal_trajectory.sql` ✅ Katman 1 + Katman 3 için snapshot toplamayı sağlar
- (gelecek) Katman 2 için ekstra table'a gerek YOK — eğitim offline, model dosya olarak saklanır

---

## Önemli — eğitim öncesi kontroller

Yeni Claude oturumunda Katman 2'ye başlamadan önce çalıştır:

```bash
# 1. Mevcut signal count yeterli mi?
curl -s "https://upbeat-flow-production.up.railway.app/api/ai-ops/outcome-audit/XAUUSD?days=180" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('XAUUSD n_signals:', d.get('n_signals'))"

# 2. candle_cache'te yeterli historical data var mı?
# Supabase'de:
SELECT symbol, timeframe, count(*), min(timestamp), max(timestamp)
FROM candle_cache
WHERE symbol IN ('XAUUSD','USOIL.FOREX')
GROUP BY symbol, timeframe;

# 3. Katman 1 production'da gerçekten block yapıyor mu?
curl -s "https://upbeat-flow-production.up.railway.app/api/ai-ops/entry-quality/block-stats?days=7"
```

---

## Bilgi notu — neden Katman 1 zayıf çıktı

XAUUSD entry-quality AUC sadece 0.53. Sebebi:
- ML modelinin kendisi 150+ feature'a bakarak BUY/SELL kararı verirken aynı
  feature'lara bakıyor
- Yani ML'in BUY dediği setup ile SELL dediği setup zaten ayrılmış durumda
- Aynı feature'lara bakarak "bu BUY başarısız olacak mı?" sorusunu cevaplamak
  pek bilgi katmıyor — model zaten bu feature'lar üzerinden karar verdi
- Katman 2'de **entry'den sonra feature'ların nasıl değiştiği** kritik — bu
  bilgi ne ML model'inin kararına ne de entry snapshot'ına dahil

USOIL AUC 0.78 yüksek ama SL hit rate sadece %3.2 — class imbalance.
Bu yüzden block threshold 0.7'de recall 0% — modelin discriminative gücü var
ama "blockla" diyebilecek confidence'e ulaşamıyor. Inversion zaten USOIL'i
düzeltti, bu yüzden Katman 1 USOIL için kritik değil.

---

## Tutarlılık kontrolleri

Yeni eğitim yaparken her seferinde kontrol et:

1. **Feature order**: trainer ve inference SAME feature list kullanmalı. Meta JSON'daki `feature_names`'i hash'le.
2. **Walk-forward**: train_cutoff_date < val_cutoff_date — leakage olmasın.
3. **Class balance**: SL hit rate %5'in altıysa class_weight veya SMOTE.
4. **Precision-first**: block threshold öyle seçilmeli ki precision ≥ 0.75. Recall ikinci.
5. **Holdout test**: validate üzerinden seçilmiş threshold, ayrı bir holdout dilime de uygulayıp doğrulamak ideal.

---

## Hızlı başlangıç — yeni Claude oturumunda Katman 2

```
Merhaba Claude, PETL Katman 2'ye devam edeceğiz. Mevcut durum:

- Katman 1 deployed (commit 3ca5822) — XAUUSD AUC 0.53, USOIL AUC 0.78
- Katman 2 hazır değil, bu işi alıyoruz
- Not defteri: backend/research/PETL_KATMAN_2_3_NOTLAR.md (oku)
- Görev: train_synthetic_trajectory_model.py yaz, çalıştır, inference ekle

Başla.
```

Bu mesajı kopyalayıp yeni bir oturumda Claude'a verebilirsin.
