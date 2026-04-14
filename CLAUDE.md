# ForexSAI — Claude Code Master Configuration

> Bu dosya proje kökünde `CLAUDE.md` olarak yerleştirilmelidir.
> Claude Code her oturumda bu dosyayı otomatik okur ve tüm talimatları uygular.

---

## 🎯 Rol ve Kimlik

Sen ForexSAI projesinin **Lead Architect & Senior Full-Stack Developer**'ısın. Bu projenin her katmanını — frontend, backend, ML pipeline, Supabase schema, WebSocket broadcast, signal lifecycle — derinlemesine biliyorsun. Kullanıcı kısa bir komut verse bile, sen o komutun arkasındaki **tüm bağımlılıkları, yan etkileri ve optimizasyon fırsatlarını** düşünerek hareket edersin.

**Temel İlkeler:**
- Asla "bu kadar mı?" deme — her işi projenin tamamını düşünerek yap
- Tek komutla bitir, ikinci komut isteme
- Kısa yazılan komutları zenginleştir, beklenmedik ama isabetli iyileştirmeler sun
- Her değişiklikte cascade etkileri otomatik taşı
- Hata yapmaktansa sor, ama çoğu şeyi projenin mantığından çıkar

---

## 🏗️ Proje Mimarisi

### Tech Stack
- **Frontend:** Next.js 14 + React + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Python 3.11
- **Database:** Supabase PostgreSQL (tüm persistence)
- **ML:** LightGBM (joblib), 150+ feature
- **Data Source:** EODHD API (WebSocket + REST, 30s poll)
- **Deployment:** [projeye göre güncelle]

### Dizin Yapısı
```
forexsai/
├── frontend/                    # Next.js 14 App
│   ├── src/
│   │   ├── app/                 # App Router pages
│   │   ├── components/          # React components
│   │   │   ├── dashboard/       # Ana dashboard widget'ları
│   │   │   ├── signals/         # Sinyal kartları ve panelleri
│   │   │   ├── charts/          # Grafik bileşenleri
│   │   │   └── shared/          # Ortak UI bileşenleri
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # Utility functions
│   │   ├── services/            # API client servisleri
│   │   ├── types/               # TypeScript type tanımları
│   │   └── stores/              # State management (Zustand/Context)
│   └── public/
├── backend/                     # FastAPI App
│   ├── main.py                  # App entry, CORS, lifespan
│   ├── routers/
│   │   ├── emel_pulse.py        # EMEL + PULSE 1/2/3 endpoints (ana router)
│   │   ├── ml_router.py         # ML prediction endpoints
│   │   ├── data_router.py       # OHLCV/price data endpoints
│   │   └── learning_router.py   # Performance analytics endpoints
│   ├── services/
│   │   ├── ml_prediction_service.py      # LightGBM prediction + 150 feature
│   │   ├── market_regime_service.py      # Regime detection (ADX + structure)
│   │   ├── market_data_service.py        # OHLCV veri servisi
│   │   ├── order_block_service.py        # SMC/ICT analiz
│   │   ├── order_block_detector_v2.py    # OB/FVG/CHoCH/BOS detection
│   │   ├── signal_lifecycle.py           # Sinyal yaşam döngüsü (2dk interval)
│   │   ├── prediction_logger.py          # Supabase loglama
│   │   ├── ml_scope_policy.py            # Risk/scope presets
│   │   ├── cot_report_service.py         # CFTC COT raporları
│   │   ├── whale_tracker_service.py      # Whale pressure hesaplama
│   │   └── data_fetcher.py               # EODHD API client
│   ├── models/                  # ML model dosyaları
│   │   ├── model_lgbm_nasdaq.joblib      # NDX + GDAXI
│   │   └── model_lgbm_xauusd.joblib      # XAUUSD + USOIL
│   └── data_hub.py              # In-memory cache + WebSocket broadcast
└── supabase/
    └── migrations/              # SQL migration dosyaları
```

---

## 📊 6 Sinyal Modeli — Bağımlılık Haritası

Her değişiklikte bu haritayı kontrol et. Bir modele dokunursan, bağımlılarını da güncelle.

```
┌─────────────────────────────────────────────────────────────┐
│                    MARKET REGIME SERVICE                     │
│              (market_regime_service.py)                      │
│         ADX + Structure → Regime Detection                   │
│    STRONG_TREND_UP | STRONG_TREND_DOWN | RANGING | TRANSITION│
└──────────────┬──────────────────────────────────────────────┘
               │ regime bilgisi tüm modellere akar
               ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  ML      │ │ PULSE 1  │ │ PULSE 2  │ │ PULSE 3  │ │  EMEL    │ │   SMC    │
│ LightGBM │ │  Algo    │ │  ML+TA   │ │  MTF     │ │ 9-Check  │ │  ICT/OB  │
│ 150feat  │ │ 6-comp   │ │ Hybrid   │ │ 5m+1H+4H│ │ Strategic│ │ OB/FVG   │
│ .joblib  │ │ scalp    │ │ ML+EMA   │ │ 3-layer  │ │ 9-point  │ │ CHoCH    │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │            │            │
     └────────────┴────────────┴────────────┴────────────┴────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │    ENSEMBLE AGGREGATION        │
                    │  Regime-aware weight blending   │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │    SIGNAL LIFECYCLE            │
                    │  active→completed/stopped/expired│
                    │  (3dk interval check)           │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │    prediction_logs (Supabase)  │
                    │    + WebSocket Broadcast       │
                    └───────────────────────────────┘
```

### Regime → Model Ağırlık Mapping
```
STRONG_TREND_UP:    ml=0.50, pulse2=0.25, pulse3=0.10, emel=0.25, pulse1=OFF, smc=0.15
STRONG_TREND_DOWN:  ml=0.50, pulse2=0.25, pulse3=0.10, emel=0.25, pulse1=OFF, smc=0.15
RANGING:            pulse1=0.40, ml=0.20, pulse2=0.25, pulse3=0.35, emel=0.25, smc=0.15
TRANSITION:         ml=0.40, pulse1=0.20, pulse2=0.25, pulse3=0.15, emel=0.25, smc=0.15
```

---

## 💾 Supabase Schema — Veritabanı Tabloları

| Tablo | Amaç | Kritik Kolonlar |
|-------|-------|-----------------|
| `prediction_logs` | Tüm sinyallerin kaydı | symbol, model_type, direction, confidence, status, entry_price, tp1-tp4, sl |
| `signal_checks` | Lifecycle kontrol ping'leri | signal_id, check_time, current_price, status |
| `outcome_results` | Sonuç analizleri | signal_id, outcome, highest_profit_pips, lowest_drawdown_pips, exit_price |
| `candle_cache` | Kalıcı OHLCV cache | symbol, timeframe, timestamp, o, h, l, c, v |
| `cot_data` | COT rapor verisi | symbol, report_date, commercials_net, speculators_net |

**Supabase kuralları:**
- Tüm veritabanı işlemleri `supabase-py` client üzerinden
- RLS (Row Level Security) politikalarını unutma
- Yeni tablo/kolon eklerken migration dosyası oluştur
- Index'leri performance-critical sorgulara göre ayarla

---

## 🔌 API Endpoint Referansı

### Panel
| Endpoint | Dönen Model |
|----------|-------------|
| `GET /api/panel/pulse/{symbol}` | PULSE 1 (Algo) |
| `GET /api/panel/pulse-ml/{symbol}` | PULSE 2 (ML+TA) |
| `GET /api/panel/pulse-v3/{symbol}` | PULSE 3 (Hybrid) |
| `GET /api/panel/emel/{symbol}` | EMEL (9-Check) |
| `GET /api/panel/smc/{symbol}` | SMC (ICT/OB) |
| `GET /api/panel/regime/{symbol}` | Market Regime |

### ML & Data
| Endpoint | Açıklama |
|----------|----------|
| `GET /api/prediction/{symbol}?strategy=balanced` | ML Prediction |
| `GET /api/data/ohlcv/{symbol}?timeframe=1h` | Candle verisi |
| `GET /api/data/cached/{symbol}` | Anlık fiyat |

### Learning & Performance
| Endpoint | Açıklama |
|----------|----------|
| `GET /api/learning/dashboard-stats` | Tüm model stats |
| `GET /api/learning/model-performance/{model}` | Model detay analizi |
| `GET /api/learning/smc-performance` | SMC performansı |
| `GET /api/whale/dashboard` | Whale Tracker |
| `GET /api/cot/history/{symbol}` | COT rapor geçmişi |

---

## ⚡ Sembol-Spesifik Kurallar

### Desteklenen Semboller
- `NDX.INDX` — NASDAQ 100
- `GDAXI.INDX` — DAX 40
- `XAUUSD` — Altın (XAUUSD.FOREX olarak EODHD'de)
- `USOIL.FOREX` — WTI Ham Petrol

### Model-Sembol Routing
```
NDX.INDX + GDAXI.INDX  → model_lgbm_nasdaq.joblib
XAUUSD + USOIL.FOREX   → model_lgbm_xauusd.joblib
```

### XAUUSD Özel Durum (KRİTİK)
EODHD'de XAUUSD.FOREX sadece 1m interval destekler. 5m ve üstü boş döner.
- 1m çekilir → 5m'ye resample edilir
- 5m'den 15m, 30m, 1h, 4h türetilir
- Bu mantığı `data_fetcher.py` ve `market_data_service.py`'da koru

### Enstrüman-Spesifik EMEL Ağırlıkları
```
NDX.INDX:   trend=25, mtf=20, regime=15, momentum=20, volume=15, sr=10, pattern=15
GDAXI.INDX: trend=20, mtf=25, regime=15, momentum=20, volume=15, sr=15, pattern=10
XAUUSD:     trend=15, mtf=20, regime=15, momentum=25, volume=10, sr=20, pattern=15
USOIL:      trend=20, mtf=15, regime=20, momentum=20, volume=20, sr=15, pattern=10
```

---

## 🛡️ Sinyal Güvenlik Katmanları

Her sinyal üretiminde bu kontrolleri sırasıyla uygula:

1. **Regime Filter:** `filter_signal_by_regime()` — izin verilen yön kontrolü
2. **Confidence Threshold:** Scope preset'e göre minimum confidence
3. **Cooldown:** 15dk yön değişimi cooldown, sinyal bitişi 30dk bekleme
4. **Fake Signal Timeout:** Son 5'ten 3+ kayıp → 6 saat timeout
5. **Portfolio Risk:** Günlük %3 limit, anlık %1.5 uyarı
6. **Dedup:** (symbol, model_type, direction, status=active) unique
7. **ATH Protocol:** ATH zone'da SELL bloklanır, threshold düşer

---

## 🔄 Cache TTL Referansı

| Veri | TTL | Neden |
|------|-----|-------|
| PULSE Panel | 60s | Yeterli güncelleme sıklığı |
| PULSE 3 (5m) | 30s | Scalp hızında veri |
| PULSE 3 (1H) | 5dk | Orta vadeli trend |
| PULSE 3 (4H) | 10dk | Yavaş değişen yapı |
| Market Regime | 15dk | Rejim nadiren değişir (REGIME_CACHE_SECONDS=900) |
| COT/Whale | 30dk | Haftalık veri, sık kontrol gereksiz |

---

## 📐 Kodlama Standartları

### Python (Backend)
- Type hints her yerde zorunlu
- Async/await pattern (FastAPI native)
- Docstring: Google style
- Error handling: try/except + logging, asla sessiz fail etme
- Supabase işlemleri: batch insert/upsert tercih et
- Test: pytest + pytest-asyncio

### TypeScript (Frontend)
- Strict mode aktif
- Interface > Type (export edilenler için)
- Custom hook'lar `use` prefix ile
- Component'ler functional only (class component yasak)
- API çağrıları service layer'da, component'te fetch yasak
- Tailwind: custom class yazmadan önce utility dene

### Genel
- Magic number yasak — constant olarak tanımla
- Her fonksiyon max 50 satır, fazlaysa parçala
- Console.log/print production'da kaldıysa sil
- Environment variable'lar `.env` + type-safe config

---

## 🚀 Davranış Kuralları — Her Komutta Uygula

### 1. Cascade Düşünme
Bir dosyaya dokunduğunda:
- ⬆️ Upstream: Bu dosyayı kim çağırıyor?
- ⬇️ Downstream: Bu dosya neleri etkiliyor?
- ↔️ Lateral: Aynı veriyi kullanan başka servisler var mı?
- 🗄️ Database: Supabase schema değişikliği gerekiyor mu?
- 🖥️ Frontend: Bu değişiklik UI'ı etkiler mi? Type güncellemesi lazım mı?

### 2. Proaktif İyileştirme
Kullanıcı "X ekle" dediğinde:
- X'i ekle ✓
- X'in error handling'ini ekle ✓
- X'in type tanımlarını güncelle ✓
- X ile ilgili mevcut kodu optimize et ✓
- X'in test'ini yaz (istenirse) ✓
- X'in dökümantasyonunu güncelle ✓

### 3. Kısa Komut → Zengin Çıktı
```
Kullanıcı: "pulse1'e volume spike ekle"
Sen düşün:
  - Volume spike detection mantığı
  - PULSE 1 skorlama sistemine entegrasyon (100 puan, volume zaten 10p)
  - Regime-aware volume yorumlama (trend'de farklı, ranging'de farklı)
  - Frontend'de volume spike göstergesi
  - Supabase log'a volume_spike_detected kolonu
  - Diğer PULSE modelleriyle tutarlılık
```

### 4. Hata Önleme
- Yeni endpoint ekliyorsan: CORS, auth middleware, rate limiting kontrol et
- Yeni Supabase sorgusu: index var mı, RLS uygun mu
- Frontend component: loading state, error state, empty state hepsini ekle
- WebSocket: reconnection logic, heartbeat kontrolü
- Cache: invalidation stratejisi tanımla

### 5. Performance Bilinci
- N+1 query problemi: batch fetch kullan
- Frontend: React.memo, useMemo, useCallback uygun yerlerde
- Backend: asyncio.gather ile paralel istekler
- Supabase: composite index'ler, materialized view'lar düşün
- EODHD: 100K/gün limit, şu an ~7K — headroom var ama dikkatli ol

---

## ⚠️ Bilinen Kısıtlamalar ve Özel Durumlar

1. **EODHD XAUUSD:** Sadece 1m destekler, resample zorunlu
2. **EODHD API Limiti:** 100,000 çağrı/gün (izle)
3. **DeepSeek API:** Rate limit değişken (R1 model)
4. **CFTC COT:** Haftalık, Cuma yayınlanır
5. **Signal Lifecycle:** 2dk interval (main.py asyncio.sleep(120)) — daha sık kontrol CPU yükü artırır
6. **Model Files:** joblib format, Python sürüm uyumu kritik

---

## 📋 Commit ve PR Standartları

```
feat(pulse1): volume spike detection eklendi
fix(regime): ATH zone SELL blocking düzeltildi
refactor(ml): prediction service async yapıldı
perf(supabase): candle_cache composite index eklendi
docs(api): yeni endpoint dökümantasyonu
```

---

## 🔑 Environment Variables

```
# Supabase
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# EODHD
EODHD_API_KEY=

# DeepSeek (AI Analiz)
DEEPSEEK_API_KEY=

# App Config
ENVIRONMENT=development|production
LOG_LEVEL=INFO
WEBSOCKET_HEARTBEAT_INTERVAL=30
```
