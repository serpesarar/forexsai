# 🔬 ForexSAI — DERİN MODEL ANALİZİ VE SİSTEM İNCELEME KILAVUZU

> **ÖNEMLİ:** Bu dosya, `.kimi/AGENTS.md` ve `.kimi/context/master-config.md` dosyalarını
> TAMAMLAYICIDIR. Kimi Code önce onları okuyarak sistemin nasıl çalıştığını, modellerin nerede
> işlem/sinyal ürettiğini, bağlantıları öğrenir. SONRA bu kılavuzla derinlemesine analiz yapar.
> **Yöntem:** Her analizde en az 3 farklı perspektif kullanılır.
> **Hedef:** Başarısızlık kök nedenlerini bulmak, sistem bağlantı hatalarını tespit etmek,
> başarı oranını artırmak.
>
> **DOĞRULUK NOTU (2026-08-01):** Bu kılavuzun eski sürümü var olmayan model adlarına
> ("Cloud Desa", "MetaBrain / Meta5 Bot", "Stage 4 ML pipeline") ve sistemden 2026-06'da
> kaldırılmış veri sağlayıcılarına (EODHD, Tiingo, marketaux) atıf yapıyordu. Bu sürüm gerçek
> mimariye göre yeniden yazıldı. Tek doğru kaynak `AGENTS.md` + `master-config.md`'dir.

---

## 📖 BAŞLANGIÇ PROTOKOLÜ (Sakın Atla!)

Her analiz oturumu başladığında SIRASIYLA:

1. **AGENTS.md'yi oku:** `.kimi/AGENTS.md` — sistem mimarisi, dizin yapısı, komutlar, kurallar.
2. **master-config.md'yi oku:** `.kimi/context/master-config.md` — veri akışı (MT5→Redis→DataHub),
   6-model bağımlılık haritası, Supabase şeması, sinyal kapıları, env katalogu, sembol kuralları.
   Bu dosya sık değişir; **tek gerçek kaynak burasıdır.**
3. **Proje yapısını doğrula:** `${KIMI_WORK_DIR_LS}` ile mevcut dosya yapısını kontrol et.
4. **Git durumunu kontrol et:** `git branch --show-current` ve `git log --oneline -8`.
5. **Sapmayı bildir:** AGENTS.md/master-config.md'de yazan bir dosya/tablo yoksa veya yapı
   değişmişse, YENİ baştan haritalama çıkarma — sapmayı tespit et ve kullanıcıya bildir.

> **Kural:** Var olan haritalamayı KULLAN. Model adı, tablo adı veya env bayrağı uydurma —
> emin değilsen `grep` ile kodda doğrula, sonra yaz.

---

## 🧠 GERÇEK MODEL/SİSTEM ENVANTERİ

Sistemde **6 canlı sinyal modeli** + **1 füzyon katmanı** + **1 NY-seans AI paneli** +
**2 otonom yürütücü (Windows kutusu)** + **doğrulama/kapı altyapısı** vardır. İsimleri ve
sorumlu dosyaları AGENTS.md/master-config.md ile birebir aynıdır:

### Panel sinyal modelleri (backend, `prediction_logs`'a yazar)
| Model | `model_type` | Pazar | Timeframe | Teknoloji | Sorumlu dosya | Endpoint |
|-------|--------------|-------|-----------|-----------|---------------|----------|
| **ML (LightGBM)** | `ml:main`, `ml:balanced`, `ml:aggressive`, `ml:full_power`, `ml:ultra_safe`, `ml:nasdaq_precision` | 4 sembol | çok-TF, 15dk log | LightGBM, 150+ feature (`.joblib`) | `services/ml_prediction_service.py`, `models/model_lgbm_{nasdaq,xauusd}.joblib` | `/api/prediction/{symbol}` |
| **PULSE 1** | `pulse1` | 4 sembol | scalp (5m ağırlıklı) | 6-bileşenli algo skor | `routers/emel_pulse.py` | `/api/panel/pulse/{symbol}` |
| **PULSE 2** | `pulse2` | 4 sembol | 5m+TA | ML+TA hibrit | `routers/emel_pulse.py` | `/api/panel/pulse-ml/{symbol}` |
| **PULSE 3** | `pulse3` | 4 sembol | 5m+1H+4H | MTF hibrit | `routers/emel_pulse.py` | `/api/panel/pulse-v3/{symbol}` |
| **EMEL** | `emel`, `emel_inverse` | 4 sembol | çok-TF | 10-kontrol stratejik | `routers/emel_pulse.py`, `services/emel_pulse.py` | `/api/panel/emel/{symbol}` |
| **SMC** | `smc` | 4 sembol | 5m/1h/4h | ICT/order-block (OB/FVG/CHoCH/BOS) | `services/order_block_service.py`, `order_block_detector_v2.py` | `/api/panel/smc/{symbol}` |

### Füzyon + AI panel
| Sistem | `model_type` | Rol | Sorumlu dosya | Endpoint |
|--------|--------------|-----|---------------|----------|
| **Meta (Ensemble)** | `meta` | 6 modeli rejim-farkında ağırlıkla birleştirir | `services/meta_analysis_engine.py`, `meta_signal_logger.py` | `/api/meta/analyze/{symbol}` |
| **AI Panel** | `ai_panel` | NY seansında DeepSeek analizi (60dk) | ilgili router/servis | `/api/learning/ai-panel-performance` |

### Otonom yürütücüler (Windows kutusu — canlı para/karar)
| Sistem | Kaynak | Yazdığı tablo | Rol |
|--------|--------|---------------|-----|
| **Claude Decider** | `claude_decider/run_decider.py`, `memory/journal.jsonl` | `decider_journal` | Kanıt-tabanlı otonom karar ajanı (Opus). Kendi PLAYBOOK/LESSONS'ından okur. *(Eski kılavuzdaki "Cloud Desa" bu sistemin bozuk yazımıydı.)* |
| **MT5 Botu** | `yeni deneme/forexsai_demo_bot.py` | `bot_trades` | Canlı MT5 botu. Aileler (magic): momentum `52890969`, CHREV `+1`, VIXREG `+2`, Reflex `+3`, DAYCOMBO `+4`. *(Eski kılavuzdaki "MetaBrain / Meta5 Bot" buydu — "Stage 4 pipeline" diye bir yapı YOK.)* |

### Doğrulama / kapı / araştırma altyapısı
| Sistem | Dosya | Rol |
|--------|-------|-----|
| **Sinyal kapıları** | `services/signal_gates.py` | Merkezi veto/kapı katmanı (XAU SELL, seans, takvim, entry-score, fakeout, debate-bias, TQ zaman-kalitesi…). Çoğu default GÖLGE. |
| **Fakeout dedektörü** | `services/fakeout_service.py` + `research/fakeout_lab.py` | Sahte kırılım radarı (4 sembol OOS %70/%70+). |
| **Shadow trade tracker** | `services/shadow_trade_tracker.py` → `shadow_pattern_trades` | Formasyon + fakeout çağrılarının sızıntısız paper-trade doğrulaması. |
| **Bias debate motoru** | `services/bias_debate_engine.py`, `llm_router.py` → `bias_test_log` | 8-ajanlı makro bias tartışması (Kimi/DeepSeek). İZOLE — canlı sinyale bağlı değil. |
| **Reflex motoru** | `services/reflex_engine_service.py` → `reflex_signals` | NDX momentum-continuation (default gölge). |
| **Precision Veto** | `services/precision_veto_service.py` → `signal_vetoes` | MiroShark makro bias yumuşak katmanı (NASDAQ-only). |

---

## 🔍 ANALİZ PERSPEKTİFLERİ (5 Farklı Beyin)

Her modeli/sistemi incelerken SIRAYLA:

### 1️⃣ MÜHENDİS / SİSTEM MİMARİ
- Kod kalitesi, exception handling, sessiz fail var mı?
- Veri akışı: MT5→Redis→DataHub→model→sinyal→`prediction_logs`→lifecycle→sonuç.
- DataHub'a doğrudan MT5/Redis bağlantısı sızmış mı? (`data_fetcher.py`/`market_data_service.py`
  yalnız DataHub okumalı — kural ihlali ara.)
- WebSocket reconnect, race condition, timeout, loglama eksikliği.

### 2️⃣ TRADER / STRATEJİST
- Giriş/çıkış kuralları net mi? TP/SL mantığı var mı?
- Trend/seans yönüne ters pozisyon açıyor mu? (Kapılar bunu yakalıyor mu?)
- Overfitting: geçmişe uyumlu, OOS'ta çöküyor mu?

### 3️⃣ DATA SCIENTIST / İSTATİSTİKÇİ
- Kronolojik train/val/test split doğru mu? Eşik VAL'de mi seçilmiş (TEST'te DEĞİL)?
- Class imbalance, feature importance, walk-forward, OOS performansı.
- Örneklem büyüklüğü (n), p-değeri, placebo/bootstrap yapılmış mı?

### 4️⃣ RİSK YÖNETİMİ
- Position sizing var mı? Çoklu açık pozisyon korelasyon kontrolü?
- SL/TP geometrisi RR≥1 mi? (Başabaş WR eşiği: RR 0.67 → %60.)
- Cascading failure önlemi (cooldown, dedup, günlük zarar limiti)?

### 5️⃣ SİSTEM ENTEGRASYON
- Modeller birbirinin sinyalini eziyor mu? Zıt sinyalde ne oluyor? (Meta füzyon + kapılar.)
- Aynı sembolde çoklu model aynı `prediction_logs` tablosuna yazıyor — dedup/lifecycle sağlam mı?
- Decider ↔ MT5 botu etkileşimi (ör. TQ çukur köprüsü: bot çukurda decider onayı okur).
- Zaman senkronizasyonu: broker saati (UTC+3) vs UTC — `bot_trades`/`candle_cache` kayması bilinen tuzak.

---

## 🎯 SİSTEM BAŞINA DETAYLI İNCELEME PROTOKOLÜ

> Model adlarını ve dosyaları master-config.md'den doğrula. Her sistemin kodunu, sinyal
> geçmişini ve bağlantılarını incele.

### A) Panel modelleri (ML / PULSE 1-3 / EMEL / SMC)
1. **Kod:** `routers/emel_pulse.py` (pulse+emel), `ml_prediction_service.py`,
   `order_block_service.py` (smc). Giriş/çıkış koşulları, skorlama, eşikler.
2. **Sinyal geçmişi:** `prediction_logs`'ta `model_type` + `symbol` kırılımıyla son N sinyal;
   WR = completed / (completed+stopped). Ort. kazanç/kayıp (R/R).
3. **Kök neden (5 Whys):** Neden başarısız? → her adımda kanıt (log/kod/DB satırı).
4. **Kapı etkileşimi:** `signal_gates.py`'da bu modele uygulanan kapılar hangileri? Gölge mi,
   blok mu? `factors.target_type` (static_pips vs atr_ladder_v1) ve `factors.time_quality`
   (golden/cool/normal) epoch'larını KARIŞTIRMA.

### B) Meta (ensemble füzyon)
1. `meta_analysis_engine.py` — 5 katmanlı pipeline (collection→combination→technical→fusion→risk).
2. Rejim→ağırlık eşlemesi doğru mu? Min 2 model aynı yön yoksa HOLD mu?
3. `meta` satırlarında hangi `source_combo` en çok kazandırıyor? (`prediction_logs.factors`.)

### C) Claude Decider (otonom karar ajanı, kutu)
1. **Kod:** `claude_decider/run_decider.py`, `decide.py`, `evidence.py`, `PLAYBOOK.md`, `LESSONS.md`.
2. **Karar geçmişi:** `decider_journal` — `decision.action` (OPEN/WAIT), `decision.direction`,
   `outcome.result` (WIN/LOSS). Sembol/yön/seans kırılımlı WR.
3. **Kanıt disiplini:** PLAYBOOK yalnız OOS+placebo doğrulanmış edge'lere dayanır mı? LESSONS'a
   kanıt-kapısını geçmeden madde girmiş mi?
4. **Bot köprüsü:** TQ çukur pencerelerinde bot `journal.jsonl`'den decider onayı okuyor —
   `_tq_decider_approval` (yeni deneme/forexsai_demo_bot.py) taze/aynı-yön/size eşiğini doğru mu?

### D) MT5 Botu (canlı yürütme, kutu)
1. **Mimari:** `yeni deneme/forexsai_demo_bot.py` — scope aileleri (momentum/CHREV/VIXREG/
   DAYCOMBO/Reflex), her biri ayrı magic. `check_scope`/`check_vix_regime`/`check_channel_reversion`.
2. **Gerçek sonuç:** `bot_trades` (kutunun `evolution_agent.py`'si MT5 deal history'den yazar).
   magic → aile eşlemesiyle WR + net PnL. **Saat analizinde broker UTC+3 kaymasını düzelt.**
3. **İşlem-sonrası yönetim:** `trade_manager.py` — BE@30dk + kazananı-koştur (NDX/DAX BUY),
   SELL'e BE/trail UYGULANMAZ. Kapılar (trend/konum/TQ) girişten önce mi çalışıyor?
4. **Kod tazeliği:** kutu `main`'i 10dk'da çeker; açık pozisyonda restart ertelenir → **borç**
   mekanizması (72s zorla). Bot eski kodla mı çalışıyor kontrol et (`ayar ... (config|varsayılan)`
   açılış dökümü + `git log` kutuda).

### E) EMEL detayı + kapı katmanı
1. **EMEL:** 10-kontrol stratejik skor; sembol-spesifik ağırlıklar (master-config'de tablo).
   `emel_inverse` adanmış ters model — üçlü loglama tuzağına dikkat.
2. **Kapılar:** `signal_gates.py::apply_signal_gates` sırası — GDAXI pulse1 askısı, XAU trend/scalp
   SELL, NDX SMC SELL, seans, takvim, entry-score, bot-taşıması (trend/wave/VIX), fakeout,
   debate-bias, TQ. Her birinin `_ENABLED`/`_BLOCK` default'u fail-open mı?

---

## 🔗 SİSTEMLER ARASI BAĞLANTI KONTROLÜ (ÇAPRAZ ANALİZ)

- [ ] **Zıt sinyal çatışması:** Model A AL, Model B SAT → Meta füzyon + kapılar nasıl çözüyor?
- [ ] **Decider ↔ bot etkileşimi:** WAIT dediğinde bot yine de açıyor mu? TQ köprüsü doğru mu?
- [ ] **Veri gecikmesi:** VIX/makro yfinance saatlik, fiyat DataHub canlı — karar anında hangisi?
- [ ] **DB yazım çakışması:** Çok model tek `prediction_logs`'a yazıyor — dedup (symbol, model_type,
      direction, status=active) unique çalışıyor mu?
- [ ] **Zaman senkronu:** broker UTC+3 vs UTC vs ET; DST; seans-sınırı drift (`market_closed_invalid`).
- [ ] **DataHub tek-okuyucu kuralı:** hiçbir yeni servis MT5/Redis'e doğrudan bağlanmamalı.
- [ ] **WebSocket reconnect:** DataHub broadcast koparsa panel donar — self-healing var mı?
- [ ] **Kod tazeliği:** Railway (backend) + kutu (bot/decider) aynı commit'te mi? Eski-kod yazarı?

---

## 📊 SİNYAL GEÇMİŞİ ANALİZ PROTOKOLÜ

Gerçek tablolar: `prediction_logs` (panel modelleri), `bot_trades` (canlı MT5), `decider_journal`
(decider), `shadow_pattern_trades` (gölge doğrulama). Erişim: proje Supabase MCP'si veya
`scripts/remote.py` (kutu tarafı).

### Panel modelleri — gerçek şema (`prediction_logs`)
```sql
-- Son 30 gün, model × sembol WR (inv/deney hariç)
SELECT model_type, symbol,
       SUM((status='completed')::int) AS win,
       SUM((status='stopped')::int)   AS loss,
       ROUND(100.0*SUM((status='completed')::int)
             / NULLIF(SUM((status IN ('completed','stopped'))::int),0), 1) AS wr,
       ROUND(AVG(stop_loss_pips)::numeric, 0) AS avg_sl_pips
FROM prediction_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status IN ('completed','stopped')
  AND model_type NOT LIKE '%inv%'
  AND model_type NOT LIKE 'ml_cross%'
GROUP BY 1,2
HAVING SUM((status IN ('completed','stopped'))::int) >= 20
ORDER BY 1,2;
```
> Not: `status` → completed=WIN(TP), stopped=LOSS(SL), expired=nötr. `resolution_reason='flip_closed'`
> SL kaybı DEĞİLDİR (WR'a girmez). Fiyat/mum verisi MT5→Redis→DataHub'dan gelir — harici vendor YOK.

### Canlı bot (`bot_trades`) — broker saatini düzelt
```sql
-- Aile × sembol gerçek PnL (magic → aile); saat analizinde close_time - 3h (broker UTC+3)
SELECT CASE magic WHEN 52890969 THEN 'momentum' WHEN 52890970 THEN 'chrev'
                  WHEN 52890971 THEN 'vixreg' WHEN 52890973 THEN 'daycombo'
                  ELSE 'diger' END AS aile,
       normalized_symbol AS sym, COUNT(*) AS n,
       ROUND(100.0*SUM((profit>0)::int)/COUNT(*),1) AS wr,
       ROUND(SUM(profit+COALESCE(commission,0)+COALESCE(swap,0))::numeric,0) AS net_usd
FROM bot_trades WHERE close_time IS NOT NULL
GROUP BY 1,2 ORDER BY net_usd;
```

### Analiz metrikleri
1. Genel WR (kazanan/toplam) · 2. Pazar bazlı (NDX/GDAXI/XAUUSD/USOIL) · 3. Timeframe bazlı ·
4. Model bazlı · 5. **Saat bazlı** (broker kayması düzeltilmiş UTC; London/NY seansı) ·
6. **Gün bazlı** (haftanın günü) · 7. Ardışık kayıp (max drawdown) · 8. Recovery factor.

---

## 🚨 BAŞARISIZLIK KÖK NEDEN MATRİKSİ

| # | Belirti | Kök Neden | Etkilenen Sistem | Kanıt (Log/Kod/DB) | Şiddet (1-5) | Çözüm |
|---|---------|-----------|------------------|--------------------|--------------|-------|
| 1 | ??? | ??? | ??? | ??? | ??? | ??? |
| 2 | ??? | ??? | ??? | ??? | ??? | ??? |

---

## 🛠️ İYİLEŞTİRME YOL HARİTASI

### Faz 1: Acil (Bu Hafta)
- [ ] Loglama/hata kontrolü — sessiz fail var mı? (`except: pass` ara.)
- [ ] DataHub tazeliği — MT5 Redis bridge kopuk mu? (`/health/ready`, reconnect logic.)
- [ ] WebSocket reconnect self-healing çalışıyor mu?
- [ ] Kod tazeliği — kutu botu/decider ile Railway backend aynı commit'te mi?

### Faz 2: Model Sağlığı (Bu Ay)
- [ ] Her model için ayrı OOS/backtest raporu (kronolojik split, eşik VAL'de).
- [ ] Feature importance güncellemesi (LightGBM).
- [ ] Kapıların etki ölçümü — gölge kapılar gerçekten kanamayı önlüyor mu? (`gate_audit.py`,
      `signal_vetoes`, `factors.time_quality`.)
- [ ] Shadow-tracker karnesi — formasyon/fakeout çağrıları canlıda tutuyor mu?

### Faz 3: Stratejik (3 Ay)
- [ ] Meta ensemble ağırlık optimizasyonu (rejim-farkında).
- [ ] MTF confirmation sıkılaştırma (5m+1H+4H hizası).
- [ ] Risk engine (position sizing, korelasyon-farkında maruziyet).
- [ ] Decider ↔ bot köprüsünün genişletilmesi (kanıt biriktikçe blok modu).

---

## 🎓 KİMİ CODE'A ÖZEL TALİMATLAR

1. **Önce AGENTS.md + master-config.md'yi oku.** Haritalamayı oradan al; yeni baştan çıkarma.
2. **Varsayım yapma.** Model/tablo/env adı emin değilsen `grep` ile kodda doğrula.
3. **Kanıt göster.** "Başarısız" derken log, DB satırı veya kod parçası koy.
4. **Karşılaştır.** Model A vs Model B, gölge vs canlı, epoch A vs B yan yana.
5. **Görselleştir.** Tablo, akış şeması, karşılaştırma matrisi.
6. **Önceliklendir.** 10 sorun bulduysan en kritik 3'ünü öne çıkar.
7. **Tekrar etme.** Her sistem için aynı protokol; hiçbirini atlama.
8. **Uydurma isim kullanma.** "Cloud Desa / MetaBrain / Stage 4" gibi adlar bu sistemde YOKTUR —
   gerçek adlar: ML, PULSE 1/2/3, EMEL, SMC, Meta, AI Panel, Claude Decider, MT5 Botu.
9. **Kanıt kültürüne uy.** OOS+placebo doğrulanmamış edge'i "gerçek" sayma; yeni kural önce
   GÖLGE kapı (`_GATE_BLOCK=0`).
10. **Anlamlı oturumu Evrim Paneli'ne logla** (`backend/scripts/evolution_session_log.py`).

---

## 📝 RAPOR FORMATI

```
# SİSTEM ADI — DERİN ANALİZ RAPORU
## 1. Genel Durum (🟢 İyi / 🟡 Orta / 🔴 Kritik)
## 2. master-config.md'deki Tanım (Özet)
## 3. Bulgular (En az 5 madde, kanıtlı)
## 4. Kök Nedenler (5 Whys)
## 5. Sistemler Arası Etkileşim (Varsa)
## 6. İyileştirme Önerileri (Önceliklendirilmiş)
## 7. Hemen Yapılacaklar (Action Items)
```

---

> **Son Not:** Bu dosya canlı bir dokümandır. Sistem değiştikçe (yeni model, yeni kapı, tablo
> değişikliği) AGENTS.md/master-config.md ile birlikte güncellenmelidir. Model/vendor adı
> eklerken gerçek koda karşı doğrula — bu dosyanın eski sürümü tam da bu yüzden yanlış isimlerle
> dolmuştu.
