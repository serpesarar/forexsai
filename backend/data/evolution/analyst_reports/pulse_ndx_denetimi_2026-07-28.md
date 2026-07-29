# PULSE 1/2/3 — NASDAQ Denetimi (2026-07-28)

**Soru:** Pulse modelleri NDX'te bireysel olarak neden başarısız? Görünür açık var mı?
Bottaki filtre/stoplar Pulse'a taşınabilir mi?

**Kısa cevap:** Evet, görünür ve ölçülü açıklar var. En büyüğü giriş kalitesi değil
**geometri + muhasebe**: tüm Pulse sinyalleri DB'de sabit **TP 30 / SL 50 puan** (RR 0.6)
merdiveniyle, üstelik **10 dakikalık** çözüm penceresiyle notlanıyor. Bu çıtada başabaş
için %62.5 WR gerekir; hiçbir Pulse akışı (yön, saat, güven dilimi fark etmeksizin) buna
ulaşmıyor. İkinci büyük açık: **BUY tarafı yapısal anti-edge** (yukarı günlerde bile %33).
Botun filtreleri taşınmaya değer; botun sabit stopları (80/110) taşınmaya DEĞMEZ —
kendisi de kanıtlı −EV.

Veri: `prediction_logs` son 60 gün (NDX.INDX), 45 günlük MFE/MAE ve gerçekleşen-puan
kesitleri. Not: backend çözümlemesi tarihsel olarak kusurluydu; 06-10 onarımı ve 07-15
flip-close düzeltmesi sonrası dönem ağırlıklı okundu. Mum-bazlı doğrulamalarda
[candle_cache 3 saat broker-saat kayması] düzeltmesi şart (fix_time.py).

---

## 1. Ham tablo (60 gün, NDX)

| Model | Yön | W | L | WR | Not |
|---|---|---|---|---|---|
| pulse1 | BUY | 130 | 272 | **%32.3** | 70 expired |
| pulse1 | SELL | 276 | 239 | %53.6 | |
| pulse2 | BUY | 58 | 83 | %41.1 | |
| pulse2 | SELL | 157 | 109 | %59.0 | filonun en iyisi |
| pulse3 | BUY | 131 | 243 | **%35.0** | |
| pulse3 | SELL | 408 | 268 | %60.4 | |

Ters gölgeler de başabaşın altında: pulse1_inv %50.1, pulse2_inv %55.2, pulse3_inv %53.2
(60g). Yani bu geometri çıtasında ne modeller ne aynaları kazanıyor — "evi" RR asimetrisi
kazanıyor.

**Gerçekleşen puan (45 gün, exit_price bazlı):**
pulse1 BUY −8.9 puan/sinyal (toplam −3.107), pulse3 BUY −3.8 (−1.360), pulse1 SELL −1.4,
pulse2 BUY −1.3, pulse3 SELL −1.1, pulse2 SELL −0.9. **Altı akışın altısı da negatif;
filo toplamı ~−5.730 puan/45g.** SELL'ler bile −8.1%'lik ayı bandında ancak sıfıra yakın.

**Bağlam:** son 44 işlem gününde NDX 30.340 → 27.886 (**−%8.1**, sadece 18 yukarı gün).
Pulse SELL'in %54-60'ı büyük ölçüde bu rüzgâr. Ayrıştırma: SELL WR aşağı günlerde %55.6,
yukarı günlerde %52.9 (fark küçük); **BUY ise yukarı günde %33.7, aşağı günde %32.8 —
yani BUY başarısızlığı piyasa yönünden bağımsız, girişin kendisi kötü** (spike kovalayıp
lokal tepeden alma deseni: kaybedenlerin medyan MFE'si +1.7…+4.8 puan — giriş anında yanlış).

---

## 2. Kök nedenler (kod kanıtlı)

### KN-1: Çift geometri — ölçülen merdiven panelde gösterilenden farklı (EN KRİTİK)
- Panel `_scalp_tp_sl` (emel_pulse.py:439-476) endeksler için ATR tabanı uygular:
  `tp=max(20, ATR14_5m×1.5)`, `sl=max(12, ATR14_5m×1.0)` → `ml_target_price/ml_stop_price`.
- Ama `log_prediction` `targets` merdivenini **target_config.py:55-68'den yeniden hesaplar**:
  NDX **TP1=TP2=TP3=TP4=30 puan, SL=50 puan** — ATR yok. `tf_addition_distance` hesaplanıp
  hiç uygulanmıyor (target_config.py:239/249, 278/281 — ölü kod).
- Lifecycle **yalnız `targets`'ı okur** (signal_lifecycle.py `_resolve_target_prices:324`);
  `ml_target_price` hiç okunmaz. Yani 07-01'deki `PULSE_ATR_GEOMETRY` yaması ölçüme hiç değmedi.
- Sonuç: RR 0.6. TP30/SL50'de sadece başabaş için %62.5 WR lazım (spread 1.5 + slippage hariç).
  Ayrıca rejim `min_rr` denetimi (1.2-1.5) panelin KURGUSAL 1.5 RR'ına bakıp geçiyor —
  gerçek loglanan RR 0.6.
- Yan etki: merdiven düz (TP1=TP4) olduğundan her TP dokunuşu `tp4_hit` yazıyor
  (signal_lifecycle.py:859) → tp-derinliği metrikleri ve `quality_score` şişik.

### KN-2: 10 dakikalık çözüm penceresi — sinyal "sinyal" değil mikro-bahis
- Pencereler (signal_lifecycle.py:181-190): **5m→10 dk**, 15m→15 dk. pulse1/pulse3 (5m) 10
  dakikada, pulse2 (15m) 15 dakikada zorla çözülür: MFE≥%95·TP → completed; olumlu kapanış →
  expired; aksi → `window_resolve_negative` = **stopped**.
- 45 günde kayıpların ~üçte biri gerçek `sl_hit` değil pencere/flip muhasebesi
  (örn. pulse1 BUY: 93 sl_hit + 63 window_neg + 25 flip). 50 puanlık SL'in 10 dakikada test
  edilme şansı bile çoğu zaman yok — TP/SL geometrisi ile pencere birbiriyle uyumsuz.
- Expired'lar ortalama 13. dakikada kapanıyor, medyan MFE +18-25 puan (TP'ye yetişemeden).

### KN-3: BUY tarafında yapısal anti-edge + rejim körlüğü
- −%8.1'lik bantta filo 654 çözülmüş BUY üretti (%32-41 WR). Rejim yön filtresi var
  (STRONG_TREND_DOWN → BUY bloklanır; market_regime_service.py:485) ama akış gösteriyor ki
  rejim çoğunlukla RANGING/TRANSITION teşhisi koyup iki yönü de açık bırakmış.
- "pulse1 trend'de kapanır" davranışı hiç çalışmıyor: emel_pulse.py:1555'teki koşul
  `weight==0` arıyor, ağırlık matrisi hiç 0 üretmiyor (min 0.15) → **ulaşılamaz dal**.
- Bugünkü NDX BUY laboratuvarı bulgusuyla tutarlı: pulse sinyalleri saat-eşitlenmiş kıyasta
  yön seçim değeri katmıyor; BUY'ın 07-28 araştırmasındaki gerçek kenarı momentum filtresi +
  UZAK hedef (ATR 2.0/1.0, +0.079R) kombinasyonunda.

### KN-4: Güven skoru kalibrasyonsuz (dekoratif)
60 günde WR güven dilimine göre: <40→%46.8, 40-50→**%60.0**, 50-60→%44.8, 60-70→%49.4,
70-80→%46.2, 80-90→%50.0, **90+→%46.2**. Monoton ilişki yok; panelde %90 güven yazan sinyal
yazı-turadan farksız. (Güven = bileşik skorun kendisi; olasılık değil.)

### KN-5: Öğleden sonra çürümesi + 18 UTC kapı kaçağı
- Saatlik WR (45g): 13→%56.3, 14→%53.1, 15→%50.8, 16→%43.3, **17→%37.4**, 18→%40.6, 19→%43.2.
- NDX seans bloğu {03,04,18,22} ve entry_score 1. koşulu 18'i kapsamasına rağmen 07-10
  SONRASI 18 UTC'de 38 satır var → kapı bu yolda deliniyor (fail-open istisna, sınır
  zamanlaması veya cache kaynaklı; log incelemesi gerekli). 16-17 UTC hiç bloklu değil ve
  en kanamalı dilim.
- Entry-score kapısının (07-10) ölçülebilir etkisi mütevazı: öncesi %47.3 → sonrası %52.5
  (+5.2pp, tape ile karışık).

### KN-6: Kazanan yönetimi ters
Kazananlar ortalama +45-55 puana gidiyor (medyan +36-42) ama 30'da kesiliyor; kaybedenler
neredeyse hiç yeşil görmüyor. Yani BE-taşıma kaybedenleri kurtarmaz (medyan MFE 2-5 puan) —
kazanç, koşucuyu uzatmakta (botta kanıtlı: BE30dk + trail 0.6R "kazananı koştur" +29.5R).

### KN-7 (hijyen): `check_interval_min` alanına unix timestamp yazılıyor
Örn. 1785261663 — dakika değil epoch. Ölçümü bozmuyor ama alan çöp.

---

## 3. Bottan ne alınır, ne alınmaz

Bot zaten Pulse uçlarını oylayıcı olarak kullanıyor (forexsai_demo_bot.py:54-58) —
Pulse düzelirse botun oylayıcıları da düzelir.

**AL (panelde karşılığı yok, bot tarafında kanıtlı):**
1. **1h EMA50 trend kapısı** (forexsai_demo_bot.py:847-870, 1043-1060): hizalı WR %63.3 /
   +9.710$ vs karşıt %43.4 / −13.161$ (30g, 332 işlem).
2. **4h dalga pozisyon kapısı** (:873-939): son 48×M5 hi-lo aralığında pozisyon;
   üst %60'ta BUY yok, alt %40'ta SELL yok. (NDX VIXREG SELL dip-üçlükte %53.4/−3.738$ vs
   tepe-üçlükte %65.8/+2.860$.)
3. **VIX rejim yönü** (VIX≥18.4→BUY, aksi SELL; plasebo p=0.000, OOS +17pp) — Pulse'a yön
   önceliği/confidence düzeltici olarak.
4. **Fakeout hizalı-kırılım vetosu** (fakeout_veto.py:24-70) — panelde kapı var ama gölgede;
   bot canlıda veto ediyor.
5. **Yönetim şablonu**: BE-30-dakika + TP kaldır & 0.6R trail (trade_manager.py:122-145) —
   lifecycle'a "TP2 sonrası trail" olarak uyarlanabilir.

**ALMA:**
- **Sabit 80/110 stop/hedef** — 11 yılda EV −0.056R kanıtlı (bot bugün de bununla çalışıyor;
  ATR geometri anahtarı botta kapalı). Pulse'ın 30/50'siyle aynı hastalık: ödül < risk.
- **M15 momentum filtresini kısa hedefle birleştirme** — etiket uyuşmazlığı tuzağı:
  botun momentum filtresi UZAK hedefle (+0.054R) çalışır; yakın-TP (lifecycle) etiketinde
  tam tersi M15 mean-reversion filtresi kazanıyordu (in-sample +45-55pp) ve o da botun uzak
  hedefinde kenarı TERSİNE çeviriyordu. Önce geometrik kimlik seçilir, filtre ona göre gelir.

---

## 4. Önerilen plan (sıralı)

**P0 — Geometri + muhasebe (bunlar olmadan hiçbir filtre ölçülemez): ✅ UYGULANDI (bu oturum)**
1. ✅ ATR merdiveni: `prediction_logger._pulse_atr_ladder` — pulse1/2/3 NDX satırları
   panel SL mesafesinden (1.0×ATR) RR≥1 merdivenle yazılır: SL=1.0×d, TP1..4 =
   1.0/1.5/2.0/2.5×d. Satır `factors.target_type="atr_ladder_v1"` ile etiketlenir
   (epoch ayrımı; eski satırlar `static_pips` olarak kalır ve eski kurala göre çözülür).
   `target_config.py`'ın statik değerlerine DOKUNULMADI.
   **GÜNCELLEME (aynı gün, kullanıcı isteğiyle):** ameliyat ml/emel/emel_inverse/meta/smc'ye
   genellendi (`PULSE_ATR_LADDER_MODELS`). Mesafe kaynakları: ml/emel → ML prediction
   stop'u; meta → risk katmanının canlı `stop_loss`u (meta_signal_logger.py kendi insert
   yolunda merdiven kurar); smc → zaten çekilen feature snapshot'ın TF'e uygun ATR'si
   (`_snapshot_atr_distance`: 5m/15m→M15, 1h→H1, 4h→H4); smc_inv aynalı stop alır.
   ai_panel bilinçli kapsam dışı (kendi seviyelerini taşır, NDX 60g %63.1 ile tek
   başabaş-üstü akış). NDX'te artık TÜM ölçülen modeller RR≥1 merdivende; 60g kanıtı:
   ml:main %54.5, meta %55.1, emel %58.0, smc %33.3 — hepsi %62.5 çıtasının altındaydı.
2. ✅ Lifecycle: `_resolve_target_prices(honor_stored=)` — etiketli satırın kendi
   merdiveni ±%15 statik banda takılmadan esas alınır; SL de satırın kendi seviyesi
   (statik 50p yeniden-hesap ezmesi kaldırıldı); pencere 5m/15m için
   `PULSE_ATR_WINDOW_MIN=60` dk'ya uzar. Scheduler cache-hit yolu artık TP/SL taşıyor
   (satırların ~%13'ü geometrisiz kalıyordu).
3. ✅ `_inv` gölgeleri ayna geometriyle yazılır (düz/ters kıyas aynı çıtada).
   ⚠ `check_interval_min` bug'ının yazarı GÜNCEL kodda yok — Railway'deki eski-kod
   yazarından geliyor (bilinen sorun); lokalde düzeltilecek yer bulunamadı.
   18 UTC kaçağı backlog'da (log incelemesi gerekli).

**P1 — Yön/bağlam kapıları: ✅ GÖLGE modda UYGULANDI (signal_gates.py)**
4. ✅ `trend_align_gate` — 1h EMA50 hizası (NDX pulse; TREND_ALIGN_GATE_BLOCK=0 gölge).
5. ✅ `wave_position_gate` — 48×5m dalga pozisyonu, tepe %60+ BUY / dip %40− SELL.
6. ✅ `vix_regime_gate` — VIX≥18.4→BUY lehte, karşıt yön frenlenir (gölge).
   Üçü de fail-open; log deseni fakeout kapısıyla aynı ("GÖLGE ... bloklanMADI" grep'i
   ile sayılır). ≥2-3 hafta gölge ölçümü + n≥100 çözülmüş sinyal olmadan *_BLOCK=1 yapma.
7. ⏳ 16-17 UTC seans bloğu değerlendirmesi (en kanamalı saatler hâlâ blok dışı) — gölge
   kapı ölçümüyle birlikte karar.

**P2 — Kimlik ayrışması + kalibrasyon:**
8. pulse1 = mean-reversion scalp (yalnız RANGING; M15 osilatör filtresi; TP=SL=1×ATR),
   pulse3 = trend koşucusu (momentum filtresi; SL 1.0 / TP 2.0×ATR; trail),
   pulse2 = ML kapılı hibrit. Üç modelin bugün ürettiği sinyaller yüksek korelasyonlu —
   ayrışma hem çeşitlilik hem ensemble değeri katar.
9. Güven → son 30g yuvarlanan empirik WR eşlemesi (model×yön×rejim); panelde "kalibre WR"
   alanı.
10. Kadans/tekrar: 63-76 satır/gün (NDX) korele spam; yön başına min fiyat-mesafesi veya
    15-30dk cooldown değerlendir.

**Ölçüm protokolü:** her değişiklik sızıntısız bar-bazlı doğrulanır (broker-saat düzeltmesi
uygulanmış 5m/1m mumlar); başarı çıtası WR değil **gerçekleşen R / sinyal** (WR tek başına
RR 0.6'da yanılttı). Gölge süresi ≥2-3 hafta veya n≥100 çözülmüş sinyal.

---

## 5. Ek: kanıt sorguları
- 60g durum/yön kırılımı, haftalık trend, saatlik WR, güven dilimleri, MFE/MAE,
  gerçekleşen puan, up/down-gün ayrıştırması: bu oturumda Supabase MCP üzerinden koşuldu
  (prediction_logs; NDX.INDX; pulse1/2/3 + _inv gölgeleri).
- Kod referansları: emel_pulse.py (:289, :434-476, :1555, :1525/2169/2904),
  prediction_logger.py (:1013-1041, :1109-1110), target_config.py (:55-68, :239-281),
  signal_lifecycle.py (:181-190, :324, :859, :874-917), signal_gates.py (:66-71, :289,
  :357-422), market_regime_service.py (:473-508); bot: config.py (:45, :96-99),
  forexsai_demo_bot.py (:372-392, :847-939, :1043-1060, :1432), trade_manager.py (:122-145).
