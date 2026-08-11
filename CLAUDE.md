# ForexSAI — Claude Code Master Configuration

> Bu dosya proje kökünde `CLAUDE.md` olarak yerleştirilmelidir.
> Claude Code her oturumda bu dosyayı otomatik okur ve tüm talimatları uygular.

@CLAUDE-REASONING.md

---

## 🖥️ İKİ BİLGİSAYAR — Panel (Mac) ↔ MT5 Kutusu (Windows)

Bu proje **iki makinede** çalışır. Mac'te geliştirme + panel backend'i; Windows
kutusunda MT5 terminali, canlı bot (`yeni deneme/`), `claude_decider` ve
`remote_agent/evolution_agent.py`. **Kutuda da Claude Code kurulu** ve oradaki
ajan üzerinden ona iş verilebilir.

### Kutuya iş verme (bu makineden, doğrudan sen çalıştır)
```bash
python3 scripts/remote.py ask "botun son 2 saatteki TREND KAPISI satırlarını say"
python3 scripts/remote.py sh "git log --oneline -5"    # kabuk komutu
python3 scripts/remote.py pull                          # kutuda git pull
python3 scripts/remote.py restart decider|bot|backend|agent
python3 scripts/remote.py status | watch <id> | health
```
`ask` → kutudaki **Claude Code headless** çalışır, çıktı canlı akar; sonunda
`=== SONUÇ ===` bloğu (durum/özet/bulgular/önerilen_adım) döner ve panel onu
ayrıştırır. Yani kullanıcıya "şu komutu kutuda çalıştır" DEME — köprüden kendin
yap, sonucu raporla. Model seçimi: `--model opus` (varsayılan sonnet).

Kanal: Supabase `evolution_commands` kuyruğu → ajan 30 sn'de bir çeker.
Güvenlik: cwd repo köküne kilitli, prompt/timeout tavanlı, görev protokolü
kutudaki Claude'a "canlı süreçlere izinsiz dokunma, MT5'te elle emir açma" der.

### Kod dağıtımı — push YETERLİ
Ajan 10 dk'da bir `git fetch`; `main` gerideyse pull + değişen klasöre göre
ilgili süreci yeniden başlatır (`yeni deneme/`→bot, `claude_decider/`→decider,
`backend/`→backend, `remote_agent/`→ajan). **Bu yüzden `main`'e push et** —
feature branch'te bırakırsan kutu görmez.
Bot restart'ı açık pozisyon varken ertelenir; erteleme artık **borç** olarak
yazılır ve pozisyon kapanınca ödenir (72 saat sonra zorla). *2026-07-23'te bu
borç mekanizması yokken bot 3 gün eski kodla çalıştı ve düzeltmeler sessizce
devre dışı kaldı — tekrarlarsa ilk bakılacak yer burasıdır.*

### Kutunun `config.py`'si gitignore'da
`yeni deneme/config.py` (şifre içerir) push edilemez → yeni ayarlar koda
`getattr(config, "AD", varsayılan)` ile yazılır. Yani **varsayılan koddadır**,
kutunun config'inde görünmez. Bot açılışta aktif ayarları `ayar <AD> = <değer>
(config|varsayılan)` satırlarıyla loglar. Bir ayarı kapatmak kutuda config'e
elle yazmayı gerektirir.

---

## 🥇 1. KURAL — Evrim Paneli Senkronu (HER OTURUMDA ZORUNLU)

Bu projede anlamlı bir değişiklik yapan HER Claude Code oturumu, işi bitirmeden önce
değişikliği Evrim Paneli'ne kaydeder. İki mekanizma:

1. **Oturum notu** — çalışmanın sonunda tek komut:
   ```bash
   python3 backend/scripts/evolution_session_log.py "kısa Türkçe özet" \
       --files degisen/dosya1.py,degisen/dosya2.tsx
   ```
   (Backend çalışıyorsa alternatif: `POST /api/evolution/session-note`.)
2. **Backlog** — oturumda yarım kalan, test edilmemiş veya "sonra bakılacak" denen
   HER iş backlog'a eklenir (unutulan deneyler bir daha kaybolmasın):
   ```bash
   python3 backend/scripts/evolution_session_log.py "özet" \
       --backlog "başlık|detay|experiment|high"
   ```
   Kategoriler: `experiment | wiring | retrain | decision | idea`. Ayrıca yeni bir
   motor/servis/analiz scripti eklendiyse `backend/data/evolution/system_registry.json`
   veya `analyses.json` kataloğuna girdisi eklenir.

Panel: `frontend /evolution` — sistem haritası, model başarıları, hata-analizi
çalıştırıcı (Çalıştır → Öğret), bekleyen işler ve değişiklik akışı buradan izlenir.
Git commit'leri changelog'a otomatik düşer; oturum notu commit'lenmeyen bağlamı taşır.

---

## 🚦 2. KURAL — Canlıya Alma Kartı (yeni scope/strateji için ZORUNLU)

Hiçbir yeni işlem scope'u, **canlıya alma kartı** çıkarılmadan `LIVE` moda geçmez:

```bash
python backend/research/go_live_gate.py <scope_adi>     # kutuda çalışır (MT5 gerekir)
```

Kart 6 ölçütü ölçer; **hepsi geçmeden verdikt LIVE olmaz** (aksi hâlde SHADOW/RED):

| # | ölçüt | eşik |
|---|---|---|
| 1 | hacim | ≥150 çözülmüş olay |
| 2 | beklenti | ort. R > 0 **ve** bootstrap P(EV>0) ≥ %90 |
| 3 | kararlılık | kronolojik iki yarının **ikisi de** ≥ 0 |
| 4 | sürtünme | spread ×1.5 stresinde hâlâ pozitif |
| 5 | **icra** | giriş = sinyal barı kapanışı DEĞİL, **sonraki M1 açılışı + gerçek spread**; iyimser varsayımla arasındaki fark ort.R'nin yarısını aşmamalı |
| 6 | sıra-bağımlı | "aynı anda tek pozisyon" kısıtıyla da pozitif |

Kart `backend/data/evolution/go_live_cards/<scope>.json`'a yazılır ve Evrim
Paneli'nden izlenir. **Neden zorunlu:** 2026-08-06'da USOIL BREAKOUT scope'u
"kronolojik TEST %58.8" diyen bir raporla canlıya alındı; rapor girişi bar
kapanışından ve spread'siz ölçmüştü. Aynı kural gerçek icra koşullarında %42.7 /
−0.147R çıkıyor — 5 günde −895$. Kartın 5. ölçütü tam bu farkı yakalar
(iyimser −0.005R vs gerçek −0.125R).

Panel sinyaline dayanan scope'lar (pulse/emel/smc oylu MOM/SR, VIXREG…) bar
verisinden yeniden üretilemez; onların karşılığı **canlı işlem kartıdır**:
`entry_gate_live_validation.py` tarzı, ≥100 gölge/canlı işlem + aynı 6 ölçüt.

⚠️ Geçmiş bir karar anını yeniden kuran her analizde `backend/research/_bars_upto.py`
kullan: `mt5.copy_rates_from(sym, tf, tarih, n)` verilen tarihten **İLERİYE** bar
döndürür ve sessizce geleceğe baktırır.

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
- **Data Source (Fiyat/Mum):** MetaTrader 5 Bridge → Redis (pub/sub + streams) → DataHub (tek kaynak)
- **Data Source (Makro):** yfinance — DXY, VIX, US10Y, EURUSD, USDTRY (`macro_data_service`, saatlik)
- **Haber:** Yakında Telegram haber dedektörü bağlanacak (şu an RSS aggregator). Harici haber vendor'ları sistemden tamamen kaldırıldı (2026-06).
- **Veri Modu:** `MARKET_DATA_SOURCE=mt5_redis` (.env)
- **Redis Host:** Railway (uzak sunucu)
- **Deployment:** Railway (backend), Vercel/Netlify (frontend)

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
│   │   ├── market_data_service.py        # OHLCV veri servisi (DataHub üzerinden)
│   │   ├── mt5_redis_client.py           # ⭐ MT5 Bridge dinleyici (pub/sub + stream)
│   │   ├── order_block_service.py        # SMC/ICT analiz
│   │   ├── order_block_detector_v2.py    # OB/FVG/CHoCH/BOS detection
│   │   ├── signal_lifecycle.py           # Sinyal yaşam döngüsü (2dk interval)
│   │   ├── prediction_logger.py          # Supabase loglama
│   │   ├── ml_scope_policy.py            # Risk/scope presets
│   │   ├── cot_report_service.py         # CFTC COT raporları
│   │   ├── whale_tracker_service.py      # Whale pressure hesaplama
│   │   ├── macro_data_service.py         # ⭐ Makro (DXY/VIX/US10Y...) — yfinance, saatlik
│   │   └── data_fetcher.py               # DataHub proxy (harici vendor çağrısı YOK, DataHub'a yönlendirir)
│   ├── models/                  # ML model dosyaları
│   │   ├── model_lgbm_nasdaq.joblib      # NDX + GDAXI
│   │   └── model_lgbm_xauusd.joblib      # XAUUSD + USOIL
│   └── services/data_hub.py    # ⭐ In-memory cache merkezi + WebSocket broadcast (services/ altında, import: services.data_hub)
└── supabase/
    └── migrations/              # SQL migration dosyaları
```

---

## 🔌 Veri Akışı Mimarisi (MT5 → Redis → DataHub)

```
┌─────────────┐    ┌──────────────────────────┐    ┌─────────────────────┐
│    MT5      │    │     Redis (Railway)       │    │  FastAPI Backend    │
│   (EA/Bot)  │    │                          │    │                     │
│             │───▶│  Pub/Sub: mt5:tick        │───▶│  mt5_redis_client   │
│  Tick data  │    │  Stream:  mt5:bar:5m      │    │  (dinleyici servis) │
│  Bar data   │    │           mt5:bar:1h      │    │         │           │
│             │    │           mt5:bar:1d      │    │         ▼           │
└─────────────┘    └──────────────────────────┘    │     DataHub         │
                                                    │  (in-memory cache)  │
                   ┌──────────────────────────┐    │         │           │
                   │  yfinance (Makro)        │    │  _prices, _candles  │
                   │  DXY / VIX / US10Y / FX   │───▶│  _candles_5m→4h    │
                   └──────────────────────────┘    │         │           │
                                                    │         ▼           │
                                                    │  data_fetcher.py    │
                                                    │  (DataHub proxy)    │
                                                    └─────────┬───────────┘
                                                              │
                                              ┌───────────────┴───────────────┐
                                              │   WebSocket / HTTP API         │
                                              │   Frontend / Signal Models     │
                                              └───────────────────────────────┘
```

**Redis Veri Yapısı:**
| Kanal/Stream | Tip | İçerik |
|---|---|---|
| `mt5:tick` | Pub/Sub | Anlık tick — symbol, price, bid, ask, timestamp |
| `mt5:bar:5m` | Stream | Kapalı 5m bar — symbol, O/H/L/C/V, timestamp |
| `mt5:bar:1h` | Stream | Kapalı 1h bar |
| `mt5:bar:1d` | Stream | Günlük bar (EOD) |

**DataHub Source Etiketleri:**
```
"mt5_redis"        → Direkt MT5'ten gelen ham veri
"derived_from_5m"  → 5m'den resample edilmiş (15m, 30m)
"derived_from_30m" → 30m'den resample edilmiş (1h, 4h — özellikle XAUUSD)
"persistent_cache" → Startup'ta Supabase candle_cache'ten yüklenmiş
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
│ LightGBM │ │  Algo    │ │  ML+TA   │ │  MTF     │ │ 10-Check │ │  ICT/OB  │
│ 150feat  │ │ 6-comp   │ │ Hybrid   │ │ 5m+1H+4H│ │ Strategic│ │ OB/FVG   │
│ .joblib  │ │ scalp    │ │ ML+EMA   │ │ 3-layer  │ │ 10-point │ │ CHoCH    │
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
| `signal_checks` | ⚠️ DEPRECATED — 2026-06-10'da donduruldu (commit 4a1bbd6). Per-check snapshot artık `signal_trajectory_snapshots`'a yazılıyor (deterioration skoru + features ile daha zengin). | signal_id, check_time, current_price, status |
| `signal_trajectory_snapshots` | Aktif sinyallerin periyodik snapshot'ı (signal_checks'in yerini aldı) | signal_id, current_price, current_profit_pips, current_drawdown_pips, deterioration_score |
| `outcome_results` | Sonuç analizleri | signal_id, outcome, highest_profit_pips, lowest_drawdown_pips, exit_price |
| `candle_cache` | Kalıcı OHLCV cache | symbol, timeframe, timestamp, o, h, l, c, v |
| `signal_vetoes` | Precision Veto Engine denetim logu (+2026-07-03: `macro_bias_adjustment`, `macro_bias_state`) | symbol, veto_stage, veto_reason, liquidity_zone_position, macro_bias_adjustment |
| `daily_bias` | ⭐ MiroShark günlük NASDAQ makro bias'ı (günde 1, UPSERT `bias_date`+`symbol`). Precision Veto Engine yumuşak katman olarak okur. NASDAQ-only. | bias_date, symbol, nasdaq_daily_bias, confidence, main_support/resistance, invalid_if, is_invalidated |
| `cortex_episodes` | ⭐ CORTEX Faz 1 epizodik hafıza (hipokampus). Her NASDAQ karar-günü: situation vektörü + karar + (kapanışta) sonuç. Analog retrieval bundan base-rate üretip debate CIO'ya besler. NASDAQ-only, izole. | ny_date, vix_regime (⭐ en ağır), market_regime, qqq_premarket_change, predicted_bias, actual_close_direction, was_correct |
| `cot_data` | ⚠️ Bu tablo Supabase'de YOK. COT verisi `cot_report_service` tarafından canlı çekilip in-memory tutuluyor, persist EDİLMİYOR. | (tablo mevcut değil) |

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
| `GET /api/panel/emel/{symbol}` | EMEL (10-Check) |
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
| `GET /api/learning/dashboard` | Tüm model stats |
| `GET /api/learning/model-performance/{model}` | Model detay analizi |
| `GET /api/learning/smc-performance` | SMC performansı |
| `GET /api/whale/dashboard` | Whale Tracker |
| `GET /api/cot/history/{symbol}` | COT rapor geçmişi |

### Fakeout Radar — Sahte Kırılım (2026-07-16/17, 4 sembol)
**ÇOK-SEMBOL (2026-07-17):** aynı lab protokolü DAX/XAU/USOIL'e koşuldu; 4 sembolün 4'ü OOS %70/%70+ geçti (hepsi 5m + LGBM + karar kırılımdan +1 bar sonra):
| Sembol | Geometri | SAHTE çağrısı | GERÇEK çağrısı | Dosyalar |
|---|---|---|---|---|
| NDX | tp1.0/sl1.0 | %70.0 (kaps %50.7) | %83.1 (kaps %34.6) + dalga K=2 %71/%74 | `fakeout_rules.json`, `model_fakeout_ndx_5m(.wave)` |
| GDAXI | tp1.0/sl1.0 | %74.6 (kaps %61.1) | %88.9 (kaps %20.2) | `fakeout_rules_GDAXI.json`, `model_fakeout_gdaxi_5m` |
| XAUUSD | tp0.75/sl1.0 | %71.7 (kaps %54.2) | %93.1 (kaps %18.3) | `fakeout_rules_XAUUSD.json`, `model_fakeout_xauusd_5m` |
| USOIL | tp1.0/sl1.0 | %86.0 (kaps %27.3) | %81.0 (kaps %15.1) | `fakeout_rules_USOIL.json`, `model_fakeout_usoil_5m` |
Notlar: dalga aşaması yalnız NDX'te %70/%70 geçti (diğerlerine EKLENMEDİ — yarış çözülünce `resolved_observed` gözlemi devrede). USOIL eşikleri `val_quantile_fallback` (%20 kapsam/side; val'de kesinlik-hedefli eşik yoktu, test yine %86/%81). XAU dedektör geometrisi tp0.75 (tp1.0'da GERÇEK sıralaması güçlü ama val eşiği çıkmadı — veri büyüyünce yeniden dene). Kural dosyası çözümü: `fakeout_service._rules_path_for` (NDX legacy ad, diğerleri `fakeout_rules_<BASE>.json`); model dosyası `detector.model_file`'dan. Yarış-durumu kontrolü sembolün kendi tp/sl'siyle (`detector.tp_atr/sl_atr`).
| Endpoint | Açıklama |
|----------|----------|
| `GET /api/fakeout/assess/{symbol}` | Canlı: taze S/R/kanal kırılımı + sahte olasılığı + eşleşen OOS kurallar (60s cache). |
| `GET /api/fakeout/rules` | Yüklü kural seti (`backend/data/fakeout_rules.json`) + meta. |
| `GET /api/fakeout/report` | Madencilik raporu (markdown). |
| `POST /api/fakeout/mine?symbol=` | Madenciyi yeniden çalıştır (research dir gerekir; prod'da unavailable). |

- Madenci: `backend/research/fakeout_miner.py` — causal S/R (fraktal pivot kümeleme, ≥2 dokunuş) + linreg kanal kırılımları; ±1×ATR iki-hedef yarışıyla GERÇEK/SAHTE etiketi (1m çözünürlük); ~22 özellik, kronolojik %70/30 OOS doğrulamalı koşul madenciliği + **birleşik kırılım skoru** (GERÇEK-pozitif, 8 bileşen, kova kalibrasyonu) + **teyit protokolü backtest'i** (sonraki-bar teyidi, retest-tut; 1:1 ve 1.5:1).
- **Bulgular (v2, NDX 5m, 1005 olay):** taban ~%66 SAHTE. Skor ≤ −2 (klimaks: derin penetrasyon, hacim patlaması, hızlı yaklaşım, VWAP'tan ≥2.4 ATR uzaklık, dik EMA50) → **OOS %87.5 sahte** (n=88) = FADE kanıtı. Skor ≥ +2 (sakin imza) → OOS yalnız %55.6 gerçek (n=45) — **gerçek-kırılım tarafında bağımsız edge YOK**; kırılım-yönlü TÜM giriş varyantları −EV (breakout bar −0.29R, sonraki-bar teyidi −0.07R, retest-tut −0.10R). Teyit ELEME filtresi olarak güçlü: teyit gelmezse gerçeklik %13'e düşer. **Sonuç: NDX 5m'de edge kırılımı almakta değil, klimaks kırılımı söndürmekte (fade) + kırılım-yönlü sinyali frenlemekte.**
- **v3 DEDEKTÖR (2026-07-16, %70/%70 hedefi VURULDU):** `research/fakeout_lab.py` 32 konfig taradı (4 TF × 4 geometri × instant/+1bar × LGBM; kronolojik train/val/test, eşik VAL'de, purge'lü). Kazanan: **5m, tp1.0/sl1.0 (hedef küçültülmedi), LightGBM, karar = kırılımdan +1 bar sonra** → OOS test n=428: **SAHTE çağrısı %70.0 isabet (kapsam %50.7), GERÇEK çağrısı %83.1 isabet (kapsam %34.6)**. En önemli özellikler teyit barı davranışı (`c1_move_atr`, `c1_body_ratio`, `c1_beyond_atr`). Instant mod hiçbir konfigde %70/%70 veremedi — kesin karar teyit barı İSTER. Model: `backend/models/model_fakeout_ndx_5m.joblib` + eşikler `fakeout_rules.json.detector` (üretici: `research/fakeout_finalize.py`; deploy edilen artefakt test edilenin TA KENDİSİ). Yeniden üretim: lab → finalize.
- **AŞAMA-2 DALGA-VERDİKTİ (kullanıcı dalga hipotezi, doğrulandı):** `research/fakeout_wave_lab.py` — kırılımdan K bar sonra, ±1ATR yarışı HÂLÂ AÇIK olaylarda (taban ~%52, en belirsiz küme) dalga-yapısı özellikleri (pullback/impuls oranı, yönlü-vs-ters bar hacim ORANI, seviye-ötesi kapanış oranı, retest, RSI delta). K=2 kazandı: **OOS SAHTE %71.4 / GERÇEK %73.5**; aynı kümede +1-bar özellikleri kör (%54/—). K=3,4,6 geçemedi. Model: `model_fakeout_ndx_5m_wave.joblib` + `fakeout_rules.json.detector_wave` (`research/fakeout_finalize_wave.py`). Runtime akışı: `pending` → `confirm_bar` (+1 bar, %70/%83) → `wave_k2` (+2 bar, yarış açıksa, %71/%74) → `resolved_observed` (yarış bittiyse gözlemlenen gerçek). `detector.stage` alanı hangi aşamada olduğunu söyler; FRESH_BARS 3→5.
- Runtime: `services/fakeout_service.py` (saf çekirdek `assess_bars`; **detector.call**: `fake|genuine|abstain|pending_next_bar` — olasılıkların birincil kaynağı; + skor + 4-sınıf öneri + canlı teyit durumu + **levels** (en yakın S/R+kanal, mesafe puan/ATR/%) + **pre_forecast** ("şimdi kırılsa" iki yön ≈tahmini); veri `data_fetcher.fetch_ohlc_data`'dan — market_data_service timestamp düşürür, kullanma). claude_decider `fakeout_bridge.py` → `situation.fakeout` (prompt: detector.call en güçlü kanıt; avoid→açma; fade→mean-rev hizalıysa konviksiyon). Kapı: `signal_gates.fakeout_gate` (NDX pulse+smc, **default GÖLGE**; dedektör SAHTE çağrısı da kanıt sayılır). Panel: Neural "Kırılım Radarı — Destek/Direnç" (`BreakoutRadarPanel.tsx`): SVG seviye merdiveni + ikiz 1-100 göstergeler (GERÇEK/SAHTE) + mesafe satırları + AI dedektör rozeti + teyit çipleri.

### Shadow Trade Tracker — Formasyon + Fakeout Doğrulama (2026-07-19)
| Endpoint | Açıklama |
|----------|----------|
| `GET /api/shadow-tracker/report?days=&symbol=` | Kaynak/sembol/formasyon/güven-kovası kırılımlı isabet raporu. |
| `GET /api/shadow-tracker/status` | Döngü durumu + konfigürasyon. |
| `POST /api/shadow-tracker/run-once` | Bir tarama+çözümleme turunu şimdi çalıştır. |

- Servis: `services/shadow_trade_tracker.py` — 120s döngü (main.py, `SHADOW_TRACKER_ENABLED=1` default açık). İki kaynak: (1) **pattern** — harmonic_pattern_service tespitleri, confidence ≥ %60, status=COMPLETED, TAZE (son pivot ≤4 bar; fraktal teyit +2 bar ister), 4h+1h; (2) **fakeout** — dedektör `call=fake|genuine`, `stage=confirm_bar|wave_k2` (**`resolved_observed` HARİÇ** — gözlem, tahmin değil → hindsight olur), fake→fade yönü, genuine→kırılım yönü, TP/SL=dedektör geometrisi×ATR14(5m).
- **Sızıntı garantileri:** giriş = karar anındaki son KAPANMIŞ 5m bar kapanışı (koşan bar elenir); çözüm yalnız girişten SONRA açılan barların high/low'u ile (giriş barı dahil değil); aynı barda TP+SL → konservatif LOSS+`ambiguous`; geç tespit → geometri sanity reddeder; piyasa bayatsa (son 5m bar >30dk) işlem açılmaz.
- Tablo: `shadow_pattern_trades` (RLS kilitli, anon politikası yok; service-role yazar; unique anchor dedup). prediction_logs/signal_lifecycle'dan TAMAMEN İZOLE. DB yoksa in-memory fail-open.
- Panel: `ShadowAccuracyCard` — Kırılım Radarı (fakeout kaynağı) + Tespit Edilen Formasyonlar (pattern kaynağı) altında canlı karne; n<10 iken "veri birikiyor" uyarısı.

### MiroShark Makro Bias (NASDAQ-only)
| Endpoint | Açıklama |
|----------|----------|
| `POST /api/miroshark/webhook` | MiroShark CIO push — HMAC-SHA256 imza (`X-MiroShark-Signature`, `WEBHOOK_SECRET`). 401 imza / 400 JSON / 503 DB. UPSERT. |
| `POST /api/miroshark/manual-bias` | İmzasız fallback — CIO JSON'u elle yapıştır. Aynı UPSERT. |
| `GET /api/miroshark/current-bias?symbol=NDX.INDX` | Bugünkü bias veya `no_bias_today`. Frontend + veto engine okur. |

- Servis: `services/daily_bias_service.py` (normalize + UPSERT + read-cache 60s + `compute_alignment` + invalidation). Router: `routers/miroshark_router.py`. Kurulum: `docs/MIROSHARK_SETUP.md`.

### Bias Doğruluk Test Harness'ı (2026-07-03, İZOLE — canlıya dokunmaz)
| Endpoint | Açıklama |
|----------|----------|
| `POST /api/bias-test/log` | Bias run'ını seans bağlamıyla `bias_test_log`'a yazar (`run_label` ile). |
| `POST /api/bias-test/fill-outcomes?ny_date=` | Gün kapanınca NDX gerçek yönüne göre `was_correct` doldurur. |
| `GET /api/bias-test/accuracy-report` | run_label / confidence / seans kırılımlı isabet oranı. |
| `GET /api/bias-test/lab` | Çift-tıkla kontrol paneli UI (self-contained HTML, `routers/bias_lab.html`, same-origin). |
| `POST /api/bias-test/run-debate` | Native debate motorunu ŞİMDİ çalıştır + logla. |
| `GET /api/bias-test/routing-status` | LLM sağlayıcı yönlendirmesi + auto-run durumu. |

- Çift-tıkla başlatıcı: `Bias Lab.command` (proje kökü) — backend'i (yoksa) başlatır, paneli tarayıcıda açar.
- **ÇOK-SEMBOL (2026-07-08):** Debate motoru sembol-parametrik (`SYMBOL_PROFILES`: NDX/XAUUSD/GDAXI/USOIL — her biri kendi ajan uzmanlıkları + sızıntısız kanıtlanmış edge'ler enjekte). Günde-1 otomatik pencereler: NDX 08:00+09:45 ET, **XAU 08:00 & DAX 08:10 UTC** (aynı tick'te iki debate çakışmasın diye kaydırıldı), **USOIL 13:05 UTC** (`BIAS_SYMBOL_RUNS_UTC`); notlama 16:15 ET + **22:20 UTC** (`BIAS_SYMBOL_FILL_UTC`). 2026-07-19: bu pencereler lokal `bias_auto_runner`'a geri inşa edildi (önceki deploy yalnız-NDX'ti). Satırlar `run_label` önekiyle sembole bağlanır (`xau_daily`/`dax_daily`/`usoil_daily`; `raw_payload.symbol` kesin kaynak → `bts.symbol_for_row`). Notlama sembol-bazlı seans penceresi: NDX RTH open→close (legacy), diğerleri **karar-fiyatı→seans kapanışı** (DAX Berlin 17:30, XAU NY 17:00, OIL NY 14:30 settle; 1h'ten sentetik). CORTEX epizodik hafıza NDX-izole kalır. `GET /recent-runs` panel sembol kartlarını besler; `POST /run-debate?symbol=`. Çok-turlu adversaryal debate: `DEBATE_ROUNDS=3` (boğa/ayı karşılıklı çürütme, CIO tam transkripti görür).
- **Debate motoru (native):** `services/bias_debate_engine.py` — 8 ajan; model yönlendirmesi `services/llm_router.py` (önemli/CIO/debate → **Kimi**, normal → **DeepSeek Reasoner**; OpenAI-uyumlu, key yoksa fail-open fallback). Core: `services/bias_test_service.py` (router+auto-runner paylaşır, DRY).
- **Hedef-seviye motoru (2026-07-10):** `services/price_projection_service.py` — 8 klasik hedef tekniği GERÇEK veriden: Fibonacci retr/ext (son impuls swing'inden; 20000→19000'de %61.8=19618 birebir testli), measured-move hedefi, ADR-20 (+bugün tükenme %'si), volatilite squeeze/expansion (ATR+BB yüzdelik), mean-rev stretch (günlük EMA20'den ATR-birimlik), ORB (⚠ context-only, backtest edge'i yok), Market Profile POC/VAH/VAL (5g×5m hacim histogramı, %70 VA). Koşullu-olasılık AYRICA yazılmadı — sistemin sızıntısız confluence playbook'u zaten o. Veri: data_fetcher → candle_cache fallback (standalone da çalışır), 5dk TTL. **Tüketiciler:** (1) debate 9. ajan `price_targets` + CIO S/R tercihi, (2) `claude_decider/run_decider.build_situation` → `situation.projections` (saf compute_fib/compute_vol_state, kendi MT5 barlarından; prompt kuralı: fib=çapa, giriş sebebi DEĞİL), (3) panel HEDEF/FİBO nöronu. Model karar katmanına (signal_gates) BAĞLANMADI — fib seviyeleri için doğrulanmış edge yok, dürüstlük ilkesi.
- **Gerçek yapı ajanları (2026-07-10):** 3 ek DeepSeek ajanı sistemin KENDİ analiz motorlarını okur (LLM tahmini değil): `smc_structure` → `order_block_service.service.detect()` (OB/FVG/CHoCH/BOS + SMC S/R; **`log_signals=False`** — debate asla `prediction_logs`'a SMC sinyali yazmaz), `trend_channel` → `trend_analyzer.run_trend_analysis()` (regresyon kanalı + fraktal-pivot S/R, dokunuş sayılarıyla), `chart_patterns` → `harmonic_pattern_service.detect_chart_patterns()` (harmonic+klasik formasyon, 4h). CIO'nun `main_support`/`main_resistance`'ı artık bu gerçek seviyelere dayanıyor; halüsinasyon clamp'i (>%10 fiyat sapması) artık null'a değil **en yakın gerçek seviyeye snap** ediyor. Panelin nöron ağında 3 yeni düğüm (`bias_lab.html`).
- **Yan beslemeler (context):** `QQQ.US` premarket proxy (NDX cash premarket işlem görmez) + DXY/VIX/US10Y makro göstergeleri (`macro_data_service.get_macro_dict`). QQQ, `data_hub.REFERENCE_SYMBOLS`'e eklendi — **tradable DEĞİL** (sinyal/scheduler/model yok), sadece fiyat/mum ingest'i (`ingest_live_price`/`ingest_candles` guard'ları REFERENCE'ı kabul eder). MT5 bridge `QQQ.US` tick'ini zaten yolluyor.
- **CORTEX Faz 1 (epizodik hafıza + analog retrieval):** `services/cortex_memory.py` — `build_situation` (seans+makro+QQQ+regime+takvim, hepsi nullable), `record_episode`/`fill_outcomes` (bias_test flow'a kancalı), `find_analogs` (ağırlıklı kNN, k=8; shrinkage prior 0.55 = ölçülen drift; `p_up_calibrated` gain 0.20 — ham p_up aşırı-özgüvenli olduğu için). Debate CIO'ya kalibre base-rate **0 LLM** ile enjekte edilir ("MILD tilt" diliyle). Flag `CORTEX_ENABLED`, `CORTEX_ANALOG_K`. Plan: `docs/CORTEX_PLAN.md`.
- **CORTEX backfill + doğrulama (2026-07-03):** `services/cortex_backfill.py` — DOĞRU hedef (kullanıcı düzeltmesi): karar anı intraday (09:30/10:00/11:00 ET), tahmin **ileriye NQ futures net yönü** +6h ve +24h (gece Asya/Avrupa dahil). 3567 sızıntısız epizod (2019-24, 1189 gün × 3 saat), NQ karışık-TZ ay-bazlı hacim-çıpasıyla çözüldü. ⚠️ **SONUÇ: analog-kNN bu hedef için YÖN ÖNGÖRMÜYOR** — Q4−Q1 kalibrasyon farkı çoğu hücrede negatif/sıfır; tek pozitif (11:00×24h) holdout'ta −11pp (aşırı-uyum); momentum baseline ~%50. Verimli-fiyatlama ile tutarlı. **Karar:** analog enjeksiyonu debate'e VARSAYILAN KAPALI (`CORTEX_ANALOG_INJECT=0`); hafıza kaydı açık (Faz 2/3 için). Yön edge'i kNN'de yok — haber/mikroyapı/LLM'de aranmalı. Bulgular: `research/cortex_backfill/FINDINGS.md`.
- **Auto-runner:** `services/bias_auto_runner.py` — main.py'de 60s loop; trading günü NY 08:00 & 09:45'te debate→log, 16:15'te fill-outcomes. **Opt-in** `BIAS_AUTO_RUN_ENABLED=1` (token harcar). Env: `KIMI_API_KEY`/`KIMI_MODEL`, `BIAS_RUN_WINDOWS_ET`, `BIAS_FILL_TIME_ET`.

- **AYI YANLILIĞI DÜZELTMESİ + KANIT ENJEKSİYONU (2026-07-26, `agent_debate_hour_audit.md`):** Denetim: 32 yönlü çağrının 25'i bearish (%78) iken piyasa 29 yukarı/28 aşağı (binom **p=0.002**); bearish çağrılar 240dk'da −0.077%, bullish +0.316%. Kök neden formasyon dedektörüydü — `shadow_trade_tracker` ölçümünde **formasyon SELL %22.6 (n=115, p≈3e-9)**, 4 sembolün 4'ünde de kaybediyor; ajanlar bunu "ayı kanıtı" sayıp yanlılığı besliyordu. Dört müdahale: (1) `recent_track_record`'a **yön dengesi bloğu** — çağrı dağılımı piyasanın KENDİ asimetrisiyle kıyaslanır, fark ≥20pp ise tilt uyarısı (gerçekten düşen piyasada ayı ağırlığı cezalandırılmaz); (2) yeni `services/debate_evidence.py` — canlı sızıntısız **dedektör karnesi** + direktifler **veriden hesaplanır** (sabit kodlu değil; n<30 veya p>0.01 ise direktif üretilmez), CONTRARIAN işaretli kaynak o yönde kanıt olarak kullanılamaz; (3) **fakeout dedektörü** (4/4 sembol OOS ≥%70 — sistemin en sıkı doğrulanmış bileşeni) tartışmaya İLK KEZ bağlandı; (4) CIO'ya **SYMMETRY RULE** — ayı anlatısı ("değerleme yüksek", "dirençte") kanıt değildir, iki yön aynı çıtaya tabidir, çekimserlik cezalandırılmaz. Ayrıca canlı sinyal tarafında `pattern_bonus_allowed` kapısı (yukarıdaki env).
- Servis: `services/session_context_service.py` — `get_session_context(ts)` (DST-doğru, `zoneinfo`; seans/premarket/overlap/yarım-gün/tatil; statik NYSE 2026 takvimi + opsiyonel `pandas_market_calendars`). Router: `routers/bias_test_router.py`. Rehber: `docs/BIAS_TEST_GUIDE.md`. **Amaç: hangi çalıştırma saatinin en isabetli bias verdiğini ölçmek → canlıya bağlama kararı (≥%65 iyi, ≥%55 min).** Ayrı tablo, ayrı router; `daily_bias`/veto engine'e DOKUNMAZ.
- **ÇOK-UFUKLU NOTLAMA (2026-07-18, `agent_debate_analysis_report.md`):** `bias_test_log`'a `ret_10m/30m/60m/240m + mfe_60m/mae_60m + horizon_filled_at` kolonları; `fill_outcomes` bunları 5m mumlardan doldurur (gün verisi olmasa da). Ana bulgu: gün-kapanışı metriği yanıltıcı — NDX bearish gün 0/4 ama +60dk 4/6, +240dk 4/5; tartışma kararı **≤240dk intraday bias** olarak tüketilmeli. `accuracy_report` → `by_horizon` + `by_symbol_horizon`; öz-kalibrasyon `recent_track_record(symbol=)` artık sembol-bazlı + ufuk karnesi içerir (eski `.not_` çağrısı wrapper'da yoktu → blok baştan beri ölüydü, düzeltildi). Uzman ajanlar nota `STANCE: ... | CONVICTION: n` satırı ekler → `_debate.agent_stances`; `agent_agreement` bu beyanlardan HESAPLANIR (CIO'ya sorulmaz — 18/18 "mixed" ölü alandı). `record_run` idempotent (aynı gün+label ikinci insert atlanır; "manual" hariç) — 07-15/16 çift-yazar kayıtları `run_label='*_dup'` ile işaretli, istatistik dışı. Startup'ta `fill_pending` catch-up. Tüketici: `signal_gates.debate_bias_gate` (NDX+USOIL, pulse+smc; karşıt sinyal freni, default GÖLGE; winner=balanced/geçersiz-seviye/NDX 14:00 ET sonrası etkisiz; LLM confidence ters-kalibre olduğu için KULLANILMAZ).

---

## ⚡ Sembol-Spesifik Kurallar

### Desteklenen Semboller
- `NDX.INDX` — NASDAQ 100
- `GDAXI.INDX` — DAX 40
- `XAUUSD` — Altın (MT5'te XAUUSD, DataHub'da da XAUUSD olarak saklanır)
- `USOIL.FOREX` — WTI Ham Petrol

### Model-Sembol Routing
```
NDX.INDX + GDAXI.INDX  → model_lgbm_nasdaq.joblib
XAUUSD + USOIL.FOREX   → model_lgbm_xauusd.joblib
```

### XAUUSD Özel Durum (KRİTİK)
MT5 Bridge XAUUSD için 5m barları doğrudan gönderir. Üst timeframe'ler DataHub'da türetilir:
- MT5 → Redis `mt5:bar:5m` stream → DataHub `_candles_5m`
- 5m → resample → 15m, 30m (derived_from_5m)
- 30m → resample → 1h, 4h (derived_from_30m)
- **2026-07-01:** `mt5:bar:1h` stream'inden veya persistent cache'ten GERÇEK 1h barı varsa, 30m türevi artık onu ezmez; 4h de gerçek 1h'ten türetilir (`derived_from_1h`). `XAU_REAL_H1_ENABLED=0` ile eski davranış.
- Bu türetme mantığı `data_hub.py` içinde, `mt5_redis_client.py`'ın ingest ettiği veriden yapılır
- `data_fetcher.py` ve `market_data_service.py` sadece DataHub'dan okur, doğrudan MT5/Redis'e bağlanmaz

### Enstrüman-Spesifik EMEL Ağırlıkları (2026-07-01 revizyonu)
```
NDX.INDX:   trend=25, mtf=20, regime=15, momentum=20, volume=15, sr=10, pattern=15, macro=5
GDAXI.INDX: trend=25, mtf=25, regime=15, momentum=20, volume=8,  sr=12, pattern=10, macro=5
XAUUSD:     trend=15, mtf=20, regime=15, momentum=25, volume=10, sr=20, pattern=15, macro=15
USOIL:      trend=20, mtf=15, regime=20, momentum=20, volume=20, sr=15, pattern=10, macro=10
```
- `macro` = 10. EMEL kontrolü (DXY/US10Y emtia, VIX endeks — yfinance, fail-open nötr)
- GDAXI: volume 15→8 (sentetik tick volume), sr 15→12 (pivot zayıf referans), trend 20→25

---

## 🛡️ Sinyal Güvenlik Katmanları

Her sinyal üretiminde bu kontrolleri sırasıyla uygula:

0. **Merkezi Kapılar (2026-07-01):** `services/signal_gates.py::apply_signal_gates()` — panel endpoint'lerinde (pulse1/2/3) regime filtresinden hemen sonra + `prediction_logger.log_prediction`'da güvenlik ağı olarak. Kapsam: XAU trend-yönü SELL kapısı (pulse+smc), GDAXI pulse1 askısı, seans kapıları (XAU 20 & 01-02 UTC, GDAXI 07 UTC), takvim kapısı (±30dk, pulse+smc+emel). Hepsi fail-open, env ile kapatılabilir.
1. **Regime Filter:** `filter_signal_by_regime()` — izin verilen yön kontrolü
2. **Confidence Threshold:** Scope preset'e göre minimum confidence
3. **Cooldown:** 15dk yön değişimi cooldown, sinyal bitişi 30dk bekleme
4. **Fake Signal Timeout:** Son 5'ten 3+ kayıp → 6 saat timeout
5. **Portfolio Risk:** Günlük %3 limit, anlık %1.5 uyarı
6. **Dedup:** (symbol, model_type, direction, status=active) unique
7. **ATH Protocol:** ATH zone'da SELL bloklanır, threshold düşer

### Precision Veto Engine — Makro Bias Katmanı (2026-07-03, NASDAQ-only)
`services/precision_veto_service.py::check_signal()` Aşama 1 içinde (likidite + MTF'ten SONRA) MiroShark günlük bias'ını uygular:
- Hizalı sinyal → confidence bonus `+min(15, C×0.2)`; karşıt → penaltı `−min(20, C×0.25)`; karşıt & `C>75` → **soft veto** (`macro_bias_opposition`, HOLD).
- `choppy` → tüm sinyaller `−10` (`wait_and_see` → `−20`). `neutral`/bias-yok/invalidated → **etkisiz** (sinyal eskisi gibi).
- Bias yoksa veya `is_invalidated` ise nötr. Gün-içi `invalid_if` izleme lifecycle'da (`_check_daily_bias_invalidation`, support/resistance kırılımı).
- Flag: `PRECISION_VETO_CONFIG["macro_bias_enabled"]` / env `MACRO_BIAS_ENABLED=0`. Bonus/penaltı `signal_vetoes.macro_bias_*` kolonlarına loglanır. **Diğer semboller (DAX/XAU/USOIL) etkilenmez.**
- ⚠️ Stage 4 meta modeli türev bias feature'larını (`daily_bias_is_*`, `signal_aligns_with_bias`) ancak **yeniden eğitilirse** tüketir.

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
- Makro: yfinance saatlik (`macro_data_service`) — düşük çağrı hacmi, harici trading-veri vendor'ı yok
- Redis: MT5 bridge bağlantısı kopunca DataHub donabilir — reconnect logic'i kontrol et
- MT5 Bridge: Tick pub/sub (`mt5:tick`) + Bar stream (`mt5:bar:5m`, `mt5:bar:1h`, `mt5:bar:1d`) ayrı dinlenir

---

## ⚠️ Bilinen Kısıtlamalar ve Özel Durumlar

1. **MT5 Bridge Kesintisi:** Redis bağlantısı koparsa DataHub'daki veriler eskir — `mt5_redis_client.py` reconnect logic'ini koru
2. **Redis Stream Lag:** MT5 bar kapanışı ile Redis'e yazılması arasında küçük gecikme olabilir (genellikle <500ms)
3. **DataHub Türetme:** XAUUSD 1h/4h verileri 30m'den türetilir; 30m verisi eksikse üst timeframe'ler boş kalır
4. **Makro (yfinance):** DXY/VIX/US10Y/EURUSD/USDTRY `macro_data_service` üzerinden yfinance'tan saatlik gelir. Harici trading-veri ve haber vendor'ları sistemden tamamen kaldırıldı (2026-06); hiçbiri kullanılmıyor.
5. **DeepSeek API:** Rate limit değişken (R1 model)
6. **CFTC COT:** Haftalık, Cuma yayınlanır
7. **Signal Lifecycle:** 2dk interval (main.py asyncio.sleep(120)) — daha sık kontrol CPU yükü artırır
8. **Model Files:** joblib format, Python sürüm uyumu kritik

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

# Redis (MT5 Bridge - Primary Data Source)
REDIS_URL=                        # Railway Redis URL
REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=

# Veri Modu
MARKET_DATA_SOURCE=mt5_redis      # mt5_redis (default) | hybrid (commodity Yahoo fallback)

# Makro: yfinance (API key gerekmez). Haber: yakında Telegram dedektörü.

# DeepSeek (AI Analiz)
DEEPSEEK_API_KEY=

# Pulse inversion SHADOW deneyi (indeksler) — ana sistemi etkilemez
PULSE_SHADOW_INVERSION_ENABLED=1
PULSE_SHADOW_INVERSION_SYMBOLS=NDX.INDX,GDAXI.INDX

# ─── 2026-07-01 Gösterge Denetimi bayrakları (services/signal_gates.py) ───
SIGNAL_BREAKEVEN_AFTER_TP1=1      # TP1 vurmuş sinyal flip-close'da completed sayılır
XAU_TREND_SELL_GATE=1             # XAU trend/ATH ortamında pulse+smc SELL → HOLD
SESSION_GATES_ENABLED=1           # XAU 20,01-02 / GDAXI 07 / NDX 03-04,18,22 / USOIL 00-11 UTC blok
CALENDAR_GATE_ENABLED=1           # High-impact takvim olayı ±30dk sinyal blok (fail-open)
CALENDAR_GATE_MINUTES=30
GDAXI_PULSE1_ENABLED=0            # GDAXI pulse1 ASKIDA (60g WR %25) — 1 ile açılır
PULSE_ATR_GEOMETRY=1              # Endekslerde TP≥ATR×1.5 / SL≥ATR×1.0 taban
PULSE3_REGIME_WEIGHTS=1           # Trend/ATH'de pulse3: 4H %40 / 1H %35 / 5m %25
XAU_REAL_H1_ENABLED=1             # Gerçek mt5:bar:1h varsa 30m türevini ezme
CROSS_MODEL_EXPERIMENT_ENABLED=0  # ml_cross_xau_nasdaq KAPALI (SELL %6.9 WR kanıtı)

# ─── 2026-07-10 MT5 otopsi kapıları (analiz_paketi_2026-07-09/RAPOR_MT5_ISLEM_OTOPSISI.md) ───
ENTRY_SCORE_GATE_ENABLED=1        # 8 koşullu giriş skoru kapısı (NDX+USOIL, pulse+smc; fail-open)
ENTRY_SCORE_MIN=7                 # min skor (0-8); kanıt: NDX ≥7 WR 60→65, USOIL ≥7 WR 49→72
# ⚠️ 2026-08-11 (1): BOT tarafı bu tarihe kadar HİÇ bağlı değildi — `yeni deneme/
# entry_gate.py` yazılmış ama commit edilmemişti (git stash e7dedf8), kutuya
# hiç gitmedi. Artık takipli ve `_entry_score_blocks()` ile _route_open (MOM/SR)
# + check_vix_regime (VIXREG) yollarına bağlı.
# ⚠️ 2026-08-11 (2) — BOT TARAFI VARSAYILAN GÖLGE (ENTRY_SCORE_GATE_BLOCK=0):
# sızıntısız canlı doğrulama kapının ALEYHİNE çıktı. 45 gün, botun kendi
# işlemleri, MOM/SR+VIXREG ∩ NDX+USOIL: kapısız n=319 WR %55.8 +1.444$;
# kapı skor<7'yi eleseydi kalan n=154 WR %54.5 −3.864$ — eleyeceği küme
# (n=165, WR %57.0) +5.308$ KAZANDIRMIŞ. Eşiklerin dördü de (5,6,7,8) negatif.
# İlk turdaki +2.943$ SIZINTILIYDI: mt5.copy_rates_from tarihten İLERİYE bar
# döndürüyor → skor gelecekteki barlarla hesaplanmıştı (bkz. research/_bars_upto.py).
# VIXREG mikro kapısı da aynı otopsiden geldiği için gölgede (VIX_REGIME_MICRO_BLOCK=0).
# ⚠️ Bu backend kapısının (aşağıdaki satır) kendisi de aynı otopsiye dayanıyor ve
# panel sinyallerini GERÇEKTEN bloklıyor — sızıntısız yeniden ölçümü backlog'da.

# ─── 2026-07-16 sahte kırılım (fakeout) kapısı — services/fakeout_service.py ───
FAKEOUT_GATE_ENABLED=1            # sahte kırılım radarı (değerlendir + logla; fail-open)
FAKEOUT_GATE_BLOCK=0              # 1 → gerçekten bloklar (default GÖLGE: sadece log; canlı sinyal-bazlı doğrulama sonrası aç)
FAKEOUT_BLOCK_PROB=80             # blok için min sahte-kırılım olasılığı (%)

# ─── 2026-07-26 formasyon teyit-bonusu yön kapısı (services/signal_gates.py) ───
PATTERN_BONUS_GATE_ENABLED=1      # formasyon "teyidi" +6/+10 skor bonusunu ölçülen
# kaybeden yönlerde geri çeker. Kanıt (shadow_trade_tracker, sızıntısız, 60g):
# formasyon SELL 26/115=%22.6 (p≈3e-9, 4 sembolün 4'ünde de kaybediyor),
# NDX BUY 2/22=%9.1 (p≈1e-4). formasyon BUY global %50 (n=124) → dokunulmadı.
# SALT SUPRESİF: yeni sinyal üretmez, yön çevirmez; yalnız bonusu vermez.

# ─── 2026-07-28 Pulse NDX denetimi: ATR merdiveni + bot-taşıması kapılar ───
# Rapor: backend/data/evolution/analyst_reports/pulse_ndx_denetimi_2026-07-28.md
# Kök neden: pulse satırları DB'de sabit TP30/SL50 (RR 0.6, başabaş %62.5) +
# 10dk pencereyle notlanıyordu; PULSE_ATR_GEOMETRY yalnız ml_target/stop'a
# yazıyordu, lifecycle okumuyordu (±%15 statik bant + SL yeniden hesaplama).
PULSE_ATR_LADDER=1                # sinyalin SL mesafesinden (d) RR≥1 merdiven:
                                  # TP1..4 = 1.0/1.5/2.0/2.5×d; factors.target_type=atr_ladder_v1
                                  # (epoch etiketi — eski static_pips dönemiyle KARIŞTIRMA)
PULSE_ATR_LADDER_SYMBOLS=NDX.INDX,XAUUSD,USOIL.FOREX
# 2026-08-01: XAU+USOIL eklendi (XAU pulse %16-18 WR'ın kök nedeni 15-pip statik
# SL'di; USOIL statik SL ~0-1 pip bozuk veriydi). DAX hâlâ DIŞARIDA — ayrı ölçüm.
PULSE_ATR_FLOOR_SYMBOLS=XAUUSD,USOIL.FOREX  # dar-stop koruması: merdiven SL mesafesi
PULSE_ATR_FLOOR_MULT=1.5                    # 1.5×ATR(TF'e uygun snapshot) altına inmez
PULSE_ATR_LADDER_MODELS=pulse1,pulse2,pulse3,ml,emel,emel_inverse,meta,smc
# (aynı gün genellendi — env adları tarihsel, pulse'ta doğdu. Mesafe kaynağı:
#  pulse=panel _scalp_tp_sl SL'i; ml/emel=ML prediction stop'u; meta=risk
#  katmanının canlı stop_loss'u (meta_signal_logger); smc=feature snapshot'ın
#  TF'e uygun ATR'si (_snapshot_atr_distance; 5m/15m→M15, 1h→H1, 4h→H4).
#  ai_panel kapsam DIŞI — NY-seans DeepSeek analizi kendi seviyelerini taşır.)
PULSE_ATR_LADDER_MULTS=1.0,1.5,2.0,2.5
PULSE_ATR_WINDOW_MIN=60           # ATR-merdivenli sinyalin lifecycle çözüm penceresi (dk)
TREND_ALIGN_GATE_ENABLED=1        # NDX pulse 1h EMA50 hizası (bot 30g/332: %63.3 vs %43.4) — GÖLGE
TREND_ALIGN_GATE_BLOCK=0          # 1 → gerçekten bloklar (≥2-3 hafta gölge ölçümü sonrası)
WAVE_POSITION_GATE_ENABLED=1      # 4h dalga (48×5m) pozisyonu: tepe %60+ BUY / dip %40− SELL — GÖLGE
WAVE_POSITION_GATE_BLOCK=0
VIX_REGIME_GATE_ENABLED=1         # VIX≥18.4→BUY lehte, altı→SELL (plasebo p=0, OOS +17pp)
VIX_REGIME_GATE_BLOCK=1           # 2026-08-01 GÖLGE→BLOK: 30g gölge-eşdeğeri ölçüm
                                  # (NDX pulse1-3, n=1098, factors.macro_vix_price):
                                  # lehte %58.0 vs karşıt %42.5 (+15.5pp). 0 → gölge.
VIX_REGIME_GATE_THRESHOLD=18.4

# ─── 2026-08-01 AI işlem envanteri denetimi kapıları ───
XAU_SCALP_GATE_ENABLED=1          # XAU pulse1/2/3+smc scalp kapısı (30g pulse %16-18 WR)
XAU_SCALP_GATE_BLOCK=0            # default GÖLGE — atr_ladder_v1 epoch'u XAU'da ölçülmeden
                                  # bloklanmaz; epoch da kurtarmazsa 1 yap

# ─── 2026-08-01 zaman-kalitesi (TQ) katmanı — gün/saat denetimi ───
# Kanıt: NDX 13-14 UTC %58 (n=683, p<1e-4) ALTIN; NDX 16/19 UTC %45 ÇUKUR;
# USOIL Perşembe %35 (n=941) ÇUKUR. Çukurda tam blok değil "yalnız çok-emin"
# çıtası. Cuma freni PANELDE YOK (panel NDX Cuma %53) — Cuma kuralı bot'ta.
TQ_GATE_ENABLED=1                 # pulse1/2/3+smc; çukurda güven<eşik → HOLD
TQ_GATE_BLOCK=1                   # 0 → gölge (sadece log)
TQ_COOL_MIN_CONF=80               # "çok emin" güven eşiği (0-100)
TQ_NDX_COOL_HOURS=16,17,19        # NDX çukur saatleri (15 hariç: panel %53)
TQ_USOIL_COOL_DOWS=4              # USOIL çukur günü (ISO 4=Perşembe)
TQ_SESSION_EXCEPTION=1            # NDX 18 UTC hard-bloğuna altın-istisna:
                                  # güven ≥ TQ_COOL_MIN_CONF ise sinyal geçer
# log_prediction her satıra factors.time_quality=golden|cool|normal etiketi yazar.
# Bot tarafı (yeni deneme/, config getattr): TQ_ENABLED=True, TQ_FRIDAY_COOL=True
# (Cuma bot %46 WR/−3.9k$: momentum +1 ek oy, vixreg ≥TQ_COOL_MIN_VOTERS=2 oy,
# chrev açılmaz), TQ_COOL_HOURS_UTC=(15,16,17) yalnız TQ_COOL_FAMILIES=
# (vixreg,chrev) — momentum'un en iyi dilimi 15-17 (%62) olduğundan saat freni YOK.
# TQ_DECIDER_APPROVAL=True: çukurda oy/eşik tutmasa bile claude_decider'ın taze
# (≤TQ_DECIDER_FRESH_MIN=45dk) aynı-yön OPEN kararı (size≥TQ_DECIDER_MIN_SIZE=0.3,
# lokal journal.jsonl kuyruğundan) "çok emin" onayı sayılır — kanıt: çukur
# pencerelerde decider %57-67 (Cuma) / NDX %65 (15-17 UTC); fail-closed.
# Bot (yeni deneme): MGMT_INCLUDE_CHREV=True default — CHREV BUY pozisyonları da
# BE30/koştur yönetimine dahil (kanıt seti CHREV işlemlerini içeriyordu; SELL kapsam dışı).
# ml_cross: log_prediction'a kill-switch güvenlik ağı eklendi — bayrak 0 iken
# ml_cross* satırı hiçbir yazardan DB'ye giremez (eski deploy dahil, o pull edince).

# ─── 2026-08-11 USOIL BREAKOUT scope GÖLGEYE alındı (bot config, getattr) ───
# USOIL_BREAKOUT_LIVE=False (varsayılan)  → sinyal üretilir+kaydedilir, emir YOK.
# USOIL_BREAKOUT_MAX_OVERSHOOT=0.5        → kırılım seviyesinin >0.5×ATR üstünde
#                                            alım yapma ("tepeden alma" freni).
# Kanıt: backend/data/evolution/analyst_reports/usoil_breakout_denetimi_2026-08-11.md
# 368 olay, gerçek MT5 M1 + spread(0.028): WR %42.7, ort −0.147R, %95
# [−0.250,−0.043], P(EV>0)=%0.3. 30 TP/SL geometrisinin 30'u negatif; geri-
# çekilme limiti / gecikmeli giriş / seans / 1h-trend / dar-kanal kapılarının
# hiçbiri artıya çıkarmıyor. Canlı: 19 işlem WR %26.3, −895$ (simülasyon aynı
# pencerede %24.1 — simülatör canlıyı doğru yakalıyor).

# ─── 2026-07-19 shadow trade tracker (services/shadow_trade_tracker.py) ───
SHADOW_TRACKER_ENABLED=1          # %60+ formasyon + fakeout dedektör çağrıları için sızıntısız paper-trade doğrulaması
SHADOW_TRACKER_MIN_CONF=60        # sanal işlem açma güven eşiği (%)
SHADOW_TRACKER_INTERVAL_SECONDS=120

# ─── 2026-07-18 tartışma-bias kapısı + bias notlama (agent_debate_analysis_report.md) ───
DEBATE_BIAS_GATE_ENABLED=1        # debate kararına KARŞIT pulse/smc sinyalini frenle (NDX+USOIL; fail-open)
DEBATE_BIAS_GATE_BLOCK=0          # 1 → gerçekten bloklar (default GÖLGE; n=18 erken kanıt — n≥30 + ≥%55 60dk isabet olmadan açma)
DEBATE_BIAS_VALID_MIN=240         # tartışma kararının geçerlilik penceresi (dk); NDX'te 14:00 ET sonrası her durumda etkisiz
BIAS_FILL_CATCHUP_ENABLED=1       # startup'ta fill_pending catch-up (token harcamaz; sadece notlama)

# ─── 2026-07-19 çok-sembol auto-runner (lokal koda geri inşa) + DAX düzeltmesi ───
BIAS_SYMBOL_RUNS_UTC=08:00=xau_daily:XAUUSD,08:10=dax_daily:GDAXI.INDX,13:05=usoil_daily:USOIL.FOREX
BIAS_SYMBOL_FILL_UTC=22:20        # geç kapanan sembollerin notlaması (fill_outcomes idempotent)
# Ana başarı metriği: primary_intraday (sembolün birincil ufkunda YÖNLÜ isabet;
# NDX 240dk, DAX/XAU/USOIL 60dk — bias_test_service.PRIMARY_HORIZON_MIN).
# Nötr/choppy = "çekimser", doğruluk oranına karışmaz (rapor EK C: DAX'ta
# gün-içi yön basit yapıyla öngörülemiyor — çekimserlik çoğu gün doğru karar).

# ─── 2026-07-15 model denetimi kapıları/düzeltmeleri ───
NDX_SMC_SELL_GATE=1               # NDX'te SMC counter-trend SELL blok (H4 close>EMA50; kanıt 14g: 1W/28L)
SHADOW_INVERSION_MODELS=          # default artık 'emel' İÇERMEZ (emel_inverse zaten adanmış ters model; üçlü loglama fix)
# Ayrıca: flip-close muhasebesi (direction_flip + realized < SL×0.5 → nötr 'flip_closed',
# WR'a girmez); pulse1/2/3 confidence [0,100] clamp; pulse2 confidence = hibrit skor
# (ham ml_confidence değil); pattern_rules.json win_rate birim normalizasyonu (kesir→yüzde).

# ─── MiroShark makro bias köprüsü (2026-07-03, NASDAQ-only) ───
WEBHOOK_SECRET=                   # MiroShark ↔ ForexSAI ortak HMAC-SHA256 secret'ı (iki tarafta aynı)
MACRO_BIAS_ENABLED=1              # Precision Veto makro bias katmanı; 0 ile tamamen kapat

# ─── Bias debate motoru + auto-runner (2026-07-03) ───
KIMI_API_KEY=                     # Kimi/Moonshot (önemli+CIO+debate ajanları). MOONSHOT_API_KEY de kabul.
KIMI_MODEL=kimi-k2-0711-preview   # gerçek Kimi 2.6 model id'siyle değiştir
KIMI_BASE_URL=https://api.moonshot.ai/v1
DEEPSEEK_MODEL=deepseek-reasoner  # normal/veri ajanları
BIAS_AUTO_RUN_ENABLED=0           # 1 → NY 08:00 & 09:45'te oto debate+log, 16:15 fill (token harcar)
BIAS_RUN_WINDOWS_ET=08:00=0800_main,09:45=0945_confirm
BIAS_FILL_TIME_ET=16:15

# App Config
ENVIRONMENT=development|production
LOG_LEVEL=INFO
WEBSOCKET_HEARTBEAT_INTERVAL=30
```

### Veri Kaynağı Seçim Mantığı
```
MARKET_DATA_SOURCE=mt5_redis → ✅ DEFAULT — Fiyat/Mum: Sadece MT5 Redis (harici vendor fallback yok)
                               Makro: yfinance (bağımsız servis)
MARKET_DATA_SOURCE=hybrid   → Fiyat/Mum: MT5 Redis (primary), emtia için Yahoo Finance fallback (MT5 stale ise)
                               Makro: yfinance
```

---

## 📊 Performans Panelleri — Sinyal Analiz Sistemi

### Panel Listesi ve Endpoint'ler
| # | Panel | Endpoint | Veri Kaynağı | Kapsam |
|---|-------|----------|-------------|--------|
| 1 | Meta Signal Analysis | `GET /api/meta/analyze/{symbol}` | 6 model ensemble | Tüm modeller |
| 2 | Strategy Performance | `GET /api/learning/strategy-performance?days=N` | prediction_logs | Sadece ML scope'ları |
| 3 | Signal Performance | `GET /api/learning/accuracy-by-model?days=N` | prediction_logs | Tüm model_type'lar |
| 4 | AI Panel Performance | `GET /api/learning/ai-panel-performance?days=N` | prediction_logs | model_type="ai_panel" |
| 5 | SMC Performance | `GET /api/learning/smc-performance?days=N` | prediction_logs | model_type="smc" |

### Meta Signal Analysis — 5 Katmanlı Pipeline
```
Katman 1: Signal Collection → 6 model paralel (ml, pulse1/2/3, emel, smc)
Katman 2: Combination Mining → meta_combination_stats tablosu, regime-filtered
Katman 3: Technical Validation → 8 koşul (EMA stack, RSI, MACD, ADX, Volume, BB, ATR)
Katman 4: Confidence Fusion → base + tech_boost[-15,+15] + combo_boost[-10,+10]
Katman 5: Risk Calculation → ATR×1.5 SL, ATR×1.0/2.0 TP
```
- Cache TTL: 55s
- Min 2 model BUY/SELL gerekli, yoksa HOLD
- Güç: ≥75 STRONG, ≥55 MODERATE, <55 WEAK, <40 → HOLD override

### Model Ağırlıkları (Meta Signal)
| Model | Base Ağırlık | STRONG_TREND çarpanı | RANGING çarpanı | VOLATILE çarpanı |
|-------|-------------|---------------------|-----------------|-----------------|
| ml | 0.25 | 1.2× | 0.8× | 0.7× |
| emel | 0.20 | 1.0× | 1.0× | 1.0× |
| pulse1/2/3 | 0.15 each | 1.0/1.0/1.3× | 1.0/1.0/0.9× | 1.0/1.0/0.8× |
| smc | 0.10 | 0.7× | 1.3× | 1.4× |

### Sinyal Loglama Sıklıkları
| Model | Log Aralığı | Koşul |
|-------|------------|-------|
| ML | 15 dakika | Her zaman |
| Pulse/EMEL | 3 dakika | Aktif sinyal varsa |
| SMC | 3 dakika | Cadence'e göre (5m→5dk, 1h→60dk) |
| AI Panel | 60 dakika | Sadece NY session açıkken |
| Fiyat/TA | 10 saniye | Sürekli |
| Outcome Check | 2 dakika | Aktif sinyal varsa |

### Sinyal Durum Akışı
```
active → completed (TP hit = WIN)
      → stopped (SL hit = LOSS)
      → expired (zaman doldu = NÖTR)
      → market_closed_invalid (filtrelenir)
```

### Performans Skor Formülleri
```
quality_score   = 100 × reliability × (0.45×win_rate + 0.30×tp_depth + 0.25×profit)
scalp_score     = 100 × reliability × (0.40×win_rate + 0.20×tp1_rate + 0.15×profit + 0.25×speed)
long_term_score = 100 × reliability × (0.35×win_rate + 0.30×tp_depth + 0.25×profit + 0.10×endurance)
reliability     = clamp(0-1, resolved/8)
```

### Risk Profil Çarpanları
| Profil | SL (ATR×) | TP1 (ATR×) | TP2 (ATR×) |
|--------|----------|-----------|-----------|
| conservative | 1.5 × 0.8 | 1.0 × 0.8 | 2.0 × 0.8 |
| balanced | 1.5 × 1.0 | 1.0 × 1.0 | 2.0 × 1.0 |
| aggressive | 1.5 × 1.3 | 1.0 × 1.3 | 2.0 × 1.3 |

---

## 🔬 Funnel / Pipeline Gözlemleri (2026-04-17 audit)

### Toplam Hacim (2 ay, 75,672 kayıt)
| Aşama | Kayıt | % |
|---|---|---|
| prediction_logs (ham) | 75,672 | 100% |
| resolved (completed + stopped) | 41,174 | 54.4% |
| expired (normal) | 2,852 | 3.8% |
| **market_closed_invalid (faz dışı)** | **31,636** | **41.9%** |
| active | 10 | 0.0% |

### market_closed_invalid Dağılımı — ANA DARBOĞAZ
| Model | MCI sayısı | Modelin toplamı | MCI oranı |
|---|---|---|---|
| smc | 10,286 | 14,106 | 72.9% |
| pulse3 | 6,842 | 17,835 | 38.4% |
| pulse1 | 6,558 | 18,400 | 35.6% |
| pulse2 | 4,619 | 13,029 | 35.5% |
| meta | 748 | 1,512 | 49.5% |

**Sebep:** `signal_lifecycle.py:593` — signal'in `created_at` zamanı `is_symbol_market_open()` testini geçemiyor. `prediction_logger._check_session_filter()` insert öncesi zaten filtreliyor ama lifecycle zamanında aynı değerlendirme farklı sonuç veriyor. En olası açıklama: eski veriler (session_filter eklenmeden önce logged) + market boundary timing drift (örn. 21:59 UTC XAUUSD SELL, lifecycle Cuma 22:05'te koşar, `created_at` 22:00 olarak kaydedilmiş olabilir).

**Etki:** Panel endpoint'leri `filter_market_closed_invalid_signals()` ile bu kayıtları SİLİYOR — yani "76-80 resolved" düşüklüğünün ana sebebi: toplam volume'un %42'si zaten panellerde görünmüyor.

### Loglama Öncesi Düşüşler (DB'ye hiç ulaşmıyor)
- `direction == "HOLD"` → atılır, asla loglanmaz
- `_check_session_filter()` (piyasa kapalı veya 5m candle >20dk bayat) → atılır
- Cooldown aşılmamış (5m=5dk, 1h=30dk, 4h=120dk, 1d=480dk) → `return None`
- Aktif sinyal var aynı yönde → dedup, `return None`
- AI Panel: BUY/SELL değilse veya entry/stop/target eksikse → sadece `ai_panel_signal_snapshots`'a yazılır, `prediction_logs`'a yazılmaz

**Telemetri eksikliği:** Bu drop'lar log seviyesinde (`logger.debug/info`) sayılıyor ama DB'ye metrik yok. Üretken çalışmada kaç sinyalin cooldown/dedup nedeniyle kaybolduğunu görmek zor.

### Threshold Değerleri — Uygulanan Değişiklikler (2026-04-17)
| Konum | Eski → Yeni | Gerekçe |
|---|---|---|
| `learning.py:285` reliability formula | `resolved/8` → `resolved/5` | Küçük scope'lar (ör. ml:nasdaq_precision 23 resolved) full score kazanabilsin |
| `learning.py:335` _pick_scope_leader min | `≥3` → `≥2` | Düşük hacimli scope'lar lider seçilebilsin |
| `meta_analysis_engine.py:379` combo gate | `total_signals ≥5` → `≥3` | Seyrek kombinasyonlar aktif hale gelir |
| `meta_engine_router.py:21` min_confidence | `40` → `45` | Zayıf meta sinyalleri HOLD'a düşsün |
| `background_scheduler.py:634` SMC min_score | `45` → `50` | SMC MCI oranı %72.9 — daha sıkı zone kalitesi |
| `background_scheduler.py:633` min_displacement_atr | `1.0` → `1.2` | Küçük displacement yapıları elenir |
| `learning.py:160` SMC bootstrap min_score | `45` → `50` | Prod ile aynı eşik |
| `learning.py:159` SMC bootstrap displacement | `1.0` → `1.2` | Prod ile aynı eşik |
| `signal_lifecycle.py:593` MCI gate | Her zaman uygular → 30dk grace buffer | Boundary drift (21:59 UTC vs 22:00 UTC) retroaktif kills'i engeller; derin kapalı periyotta hâlâ yakalar |
| `meta_analysis_engine.py` MIN_MODELS | `2` (değişmedi) | HOLD eşiği doğru |

### Panel Duplikasyonu Analizi
| Panel | Ana model_type | Ana niyet | Overlap |
|---|---|---|---|
| Strategy Performance | yalnızca ml:* varyantları | Scope-level lider seçimi (quality/scalp/long_term) | Signal Perf ile (aynı ML sinyalleri) |
| Signal Performance | tüm model_type'lar | Model bazlı ham accuracy | Strategy ile ML scope'ları overlap eder |
| SMC Performance | yalnızca smc | Cadence-collapsed SMC | Signal Perf içinde smc satırı ile overlap |
| AI Panel Performance | yalnızca ai_panel | NY session DeepSeek analizleri | Yok |
| Meta Signal Analysis | canlı (6 model fusion) | Gerçek zamanlı sinyal | Diğerleri geçmiş; overlap yok |

**Birleştirme önerisi:** Strategy + Signal Performance aynı UI sekmesinde tab olarak sunulabilir; ML scope'lar Strategy'de, diğer modeller Signal'de. SMC ayrı kalabilir (cadence collapse farklı istatistik üretiyor).

### Uygulanan Düzeltmeler (2026-04-17 audit)
1. **`routers/learning.py::get_accuracy_by_model`** — `expired + any_target_hit` artık `target_hit` sayısına eklenmiyor; ayrı `partial_target_hit` alanına gidiyor. Düzeltme öncesi: `target_hit_rate` teorik olarak >1.0 olabilirdi.
2. **`services/meta_analysis_engine.py::TechnicalSnapshot.get_conditions`** — `atr_valid` artık gerçek kontrol: ATR/price oranı %0.05–%3.0 arasında olmalı (önceden sadece `atr_14 > 0`, trivial geçer).

### Yeni Log Aralığı Kuralları (2026-04-17 teyitli)
| Model | Gerçek aralık (30d median) | Beklenen | Durum |
|---|---|---|---|
| pulse1 | 1.1dk median, 3.7dk avg | 3dk | ✓ |
| pulse2 | 1.6dk median | 3dk | ✓ |
| pulse3 | 1.1dk median | 3dk | ✓ |
| smc | 0.0dk median | cadence bazlı | ⚠ Aynı bucket birden fazla → collapse filtresi yakalıyor |
| emel | 8.0dk median | 3dk | ✓ |
| emel_inverse | 3.0dk median | 3dk | ✓ |
| ml:main | 15.0dk median | 15dk | ✓ |
| ai_panel | 61.9dk median | 60dk | ✓ |
| meta | 2.2dk median | canlı, log değil | - |

---

## 🎨 Frontend Tasarım Sistemi — Panel Organizasyonu

### Navigasyon Yapısı
```
/ (Dashboard)
├── Sembol Kartları: NDX | DAX | XAUUSD | USOIL
│   └── Tıkla → /dashboard/{symbol}
│
/dashboard/{symbol} (Sembol Sayfası)
├── Bölüm 1: Üst Bar (fiyat + meta signal)
├── Bölüm 2: Ortak Grafik (SharedChart)
├── Bölüm 3: Sinyal Grid (6 model, 2×3)
├── Bölüm 4: Piyasa Bağlamı (regime + COT + AI)
└── Bölüm 5: Performans Scoreboard (horizontal scroll)
```

### Sayfa Oranları (Altın Oran Bazlı)
| Bölüm | Oran | İçerik | Öncelik |
|-------|------|--------|---------|
| Üst Bar | %8 | Fiyat + Meta Signal | Anlık durum |
| Grafik | %25 | Shared chart + TF tabs | Görsel analiz |
| Sinyal Grid | %35 | 6 model kart | Karar verme |
| Bağlam | %12 | Regime + COT + AI | Destekleyici |
| Scoreboard | %20 | Model performans | Güvenilirlik |

### Renk Kodlaması (Tüm Sistemde Tutarlı)
| Amaç | Renk | Tailwind |
|------|------|---------|
| ML modeli | Mavi | blue-500/600 |
| EMEL | Mor | purple-500/600 |
| PULSE 1/2/3 | Turuncu/Coral | orange-500/600 |
| SMC | Teal | teal-500/600 |
| AI Panel | Amber | amber-500/600 |
| BUY sinyal | Yeşil | green-500 |
| SELL sinyal | Kırmızı | red-500 |
| HOLD sinyal | Gri | gray-400 |
| CONFIRM | Solid arka plan | bg-{renk}-500 |
| SCOUT | Çizgili/yarı saydam | bg-{renk}-100 border |

### Component Yapısı
```
components/
├── layout/          → SymbolPage, SymbolSelector
├── price/           → LivePriceBar
├── meta/            → MetaSignalCard
├── chart/           → SharedChart (TEK grafik component)
├── signals/         → SignalGrid, SignalCard, ConfidenceBar
├── context/         → RegimeCard, WhaleCard, AIPanelCard
├── performance/     → PerformanceScoreboard, ModelScoreCard
└── shared/          → StatusBadge, DirectionIndicator, SkeletonLoader
```

### Responsive Breakpoints
| Breakpoint | Grid | Scoreboard |
|------------|------|------------|
| Desktop (≥1280px) | 2×3 sinyal, 3 bağlam | Yatay scroll |
| Tablet (768-1279px) | 2 kolon | Yatay scroll |
| Mobil (<768px) | 1 kolon stack | Yatay scroll korunur |

### Panel Tekrar Kuralı
Her panel sisteme **tam olarak 1 kez** görünür — sembol sayfası içinde.
Dashboard (/) sadece sembol kartlarını gösterir, panel içermez.
