# USOIL BREAKOUT scope denetimi + kayıp giriş kapılarının bağlanması

**Tarih:** 2026-08-11
**Tetikleyici:** Kullanıcı ekran görüntüsü — dün SpotCrude'da art arda açılan 5 BUY
pozisyonu, "hep fiyat yüksekken alım yapıldı, oysa kapı ayarlarını yapmıştım".
**Veri:** Kutunun gerçek MT5 işlem geçmişi + MT5 M5/M1 barları (spread dahil).

---

## 1. Dün ne oldu — işlem işlem

Ekrandaki 5 pozisyonun tamamı **magic 52890974 = `USOIL_BREAKOUT_MAGIC`** (2026-08-06'da
canlıya alınan Donchian48 kırılım scope'u). MOM/SR ya da CHREV değil.

| # | UTC | seviye | kırılım barı kapanışı | aşım (×ATR) | dolum | sonuç |
|---|-----|--------|----------------------|-------------|-------|-------|
| 1 | 08-09 22:05 | 78.648 | 79.364 | **2.50** | 79.541 | SL −143.0$ |
| 2 | 08-10 17:05 | 81.794 | 81.819 | 0.12 | 81.847 | SL −100.5$ |
| 3 | 08-10 17:35 | 81.871 | 81.951 | 0.40 | 81.983 | TP +94.5$ |
| 4 | 08-10 18:21 | 82.176 | 82.411 | **1.38** | 82.405 | SL −85.0$ |
| 5 | 08-11 01:45 | 82.589 | 82.592 | 0.02 | 82.635 | SL −79.5$ |

Kullanıcının gözlemi doğru: giriş **tanımı gereği** 4 saatlik kanalın tepesinden yapılıyor
(Donchian kırılımı = yeni zirve). İki işlemde (1 ve 4) fiyat kırılım seviyesinin
1.4–2.5 ATR üstüne çıkmışken alım yapılmış — yani zirvenin de tepesi kovalanmış.

**Scope'un canlı toplamı (2026-08-06 → 08-11, 19 işlem): WR %26.3, net −895$.**
Scope'u devreye alan araştırma TEST'te %58.8 vaat ediyordu.

## 2. Kapılar neden uygulanmadı — kök neden

İki ayrı kusur:

1. **`entry_gate.py` hiç commit edilmemişti.** 2026-07-10 MT5 otopsisinden çıkan
   8 koşullu giriş skoru + seans saat bloğu modülü yazılmış, yerelde `.pyc`'si bile
   üretilmiş, ama `git stash` (e7dedf8) içinde kalmış. Kutuya kod `git pull` ile
   gittiği için **modül kutuya hiç ulaşmadı** ve botta onu çağıran tek satır yoktu.
   `config.py`'deki `ENTRY_SCORE_GATE_ENABLED = True` / `SESSION_BLOCK_HOURS_UTC`
   ayarları bu yüzden hiçbir şey yapmıyordu. (Backend tarafındaki
   `services/signal_gates.py` karşılığı çalışıyordu — ama o yalnız panel sinyallerini
   süzer, botun kendi girişlerine dokunmaz.)
2. **BREAKOUT scope'u zaten hiçbir kapının arkasında değildi.** `check_usoil_breakout`
   doğrudan `open_trade`'e gidiyor; trend/konum/TQ/seans kapılarının hiçbiri bu yola
   bağlı değil. USOIL için tanımlı 00–11 UTC seans bloğu da bu yüzden 5. işlemi
   (01:45 UTC) durduramadı.

## 3. Kırılım kuralının dürüst yeniden ölçümü

`backend/research/usoil_breakout_lab*.py` — botun `check_usoil_breakout` kuralı birebir
yeniden üretildi (canlı log'daki 19 olayın 17'si seviye/kapanış/ATR düzeyinde **birebir**
eşleşti; kalan 2'si bar-hizalama farkı). Giriş = kırılım barı kapanışından sonraki ilk
M1 açılışı **+ spread (0.028)**; çözümleme M1 bid barlarıyla; aynı barda TP+SL →
konservatif kayıp.

**368 olay (3,5 ay, gerçek broker verisi):**

| ölçüm | sonuç |
|---|---|
| TABAN (canlı kural, TP=SL=1×ATR) | WR **%42.7**, ort **−0.147R**, %95 [−0.250, −0.043], **P(EV>0)=%0.3** |
| spread=0 varsayımı | WR %49.2 — *rapor bu dünyada ölçmüştü* |
| BE+kazananı-koştur yönetimi | ort −0.042R (hâlâ negatif) |
| 2026-08-06→ dilim (canlı pencere) | WR %24.1 — **canlı %26.3 ile tutarlı** |

**Hiçbir varyant kurtarmıyor:**
- 30 TP/SL geometrisi (0.75–3.0 TP × 0.75–1.5 SL, ±koştur) → **30'u da negatif**.
- Geri-çekilme limiti (seviyeye dönüşte al, k=−0.25…+0.10, 3/6/12 bar geçerli, 72 varyant)
  → en iyisi ≈0.00R, kronolojik yarılarda işaret değiştiriyor.
- Gecikmeli giriş (+1/+2/+3 bar) → daha kötü.
- Ön-tanımlı kapılar: seans 12–23 UTC (−0.189R), 1h EMA50 hizası (−0.203R),
  1h EMA200 (−0.183R), dar kanal (−0.065R), ADX 18–35 (−0.095R), gün-içi tepe
  değil (−0.083R), birleşik (−0.134R) — **hepsi negatif**.
- Tek anlamlı iyileşme **aşım freni**: aşım ≤0.50×ATR → WR %47.9, ort −0.041R
  (kaybın ~%72'si "kırılım barının tepesini kovalama" alt kümesinden geliyor).
  Ama bu da artıya çıkarmıyor: P(EV>0)=%27.

**Karar:** Bu giriş kuralının gerçek icra koşullarında kenarı yok. Scope **GÖLGEYE**
alındı (`USOIL_BREAKOUT_LIVE=False`, varsayılan): sinyal üretilmeye ve kaydedilmeye
devam eder, emir gönderilmez. Ayrıca aşım freni (`USOIL_BREAKOUT_MAX_OVERSHOOT=0.5`)
eklendi — scope canlıya dönerse tepeden alım baştan elenir.

## 4. Giriş skoru kapısı — doğrulama ve DÜZELTME

Kapı, botun **kendi gerçek 45 günlük işlemleri** üzerinde geriye dönük ölçüldü
(`backend/research/entry_gate_live_validation.py`).

### 4a. İlk tur GEÇERSİZDİ — sızıntı

İlk ölçüm `mt5.copy_rates_from(sym, tf, açılış_zamanı, n)` kullanıyordu. Bu fonksiyon
verilen tarihten **İLERİYE** bar döndürür (geriye değil) → skor, işlemden SONRAKİ
barlarla hesaplandı ve doğal olarak "kazananları tanıdı". O turun sonucu
(+2.943$, WR %60.0) **çöp**. Düzeltme: `backend/research/_bars_upto.py` —
`copy_rates_range` penceresi + karar anından sonraki (ve koşan) barların kesilmesi.
Doğrulama: düzeltilmiş çekimle dünkü 5 işlemin Donchian seviyeleri canlı logla
**birebir** eşleşti (78.648 / 81.794 / 81.871 / 82.176 / 82.589) ve son-bar yaşı
M1'de 1–2 dk çıktı (ne sızıntı ne bayatlık).

### 4b. Sızıntısız sonuç — kapı ZARARLI

**Bağlanan kapsam — MOM/SR + VIXREG, sembol NDX+USOIL:**

| | n | WR | net PnL |
|---|---|---|---|
| kapı YOKken (bugünkü canlı) | 319 | %55.8 | +1.444$ |
| kapı VARken (skor≥7 açılır) | 154 | %54.5 | **−3.864$** |
| **kapının engelleyeceği küme** | 165 | **%57.0** | **+5.308$** |

**→ Kapının 45 günlük etkisi: −5.308$.** Yani kapı **kârlı işlemleri eliyor**.
Eşiklerin **dördü de** (5/6/7/8) negatif. En sık ihlal edilen koşullar trend-hizası
tipinde (`ema200_tarafi` 118, `bicak_yakalama` 117, `1h_karsi_momentum` 112,
`5m_trend` 112) — bu bot için giriş anındaki trend hizası ayırt edici değil, ters.

**Karar:** kapı **ölçer ama bloklamaz** (`ENTRY_SCORE_GATE_BLOCK=False`, varsayılan).
Aynı otopsiden gelen VIXREG mikro-yapı kapısı da aynı nedenle gölgeye alındı
(`VIX_REGIME_MICRO_BLOCK=False`). Elenecek girişler `gate_skip.jsonl`'e yazılmaya
devam eder → kanıt birikir.

⚠️ **Yayılan şüphe:** Backend'deki `services/signal_gates.py` ENTRY_SCORE kapısı
(panel sinyallerini gerçekten bloklayan, `ENTRY_SCORE_GATE_ENABLED=1`) **aynı
2026-07-10 otopsisine** dayanıyor. O otopsinin de aynı sızıntıyı taşıyıp taşımadığı
denetlenmeli — backlog'a alındı.

## 5. Uygulanan değişiklikler

| dosya | değişiklik |
|---|---|
| `yeni deneme/entry_gate.py` | **repoya geri alındı** (artık takipli → kutuya gidiyor) |
| `forexsai_demo_bot.py` | `_entry_score_blocks()` + `_vix_micro_blocks()` yardımcıları |
| `forexsai_demo_bot.py` | `_route_open` (MOM/SR) ve `check_vix_regime` (VIXREG) kapıya bağlandı — **GÖLGE** (blok yok) |
| `forexsai_demo_bot.py` | CHREV'e kapı **gölge** modda bağlandı (ölçüm; `ENTRY_SCORE_GATE_CHREV=True` ile bloklar) |
| `forexsai_demo_bot.py` | BREAKOUT: aşım freni + gölge modu (`USOIL_BREAKOUT_LIVE`) |

Tüm kapılar **fail-open** (veri/modül hatası girişi engellemez) ve config bayrağıyla
kapatılabilir. Elenen her giriş `gate_skip.jsonl`'e yazılır → "filtre haklı mıydı?"
sorusu sonradan 1m replay ile ölçülebilir.

## 6. Açık kalanlar (backlog)

- **CHREV kanaması:** 45 günde n=52, net **−3.562$**. Sızıntısız ölçümde skor kapısı
  burada da işe yaramıyor (skor≥7 kümesi n=1) — CHREV'in kaybı ayrı bir kök neden
  analizini hak ediyor (kapıyla çözülmüyor).
- **Backend ENTRY_SCORE kapısı denetimi:** `services/signal_gates.py` panel
  sinyallerini aynı (şüpheli) otopsiye dayanarak bloklıyor — sızıntısız yeniden ölçüm şart.
- **Kapı karnesi:** `gate_skip.jsonl`'deki gölge kayıtlar 2–3 hafta sonra 1m replay ile
  çözülüp "bu kapı gerçekten ne eliyordu" ölçülecek.
- **BREAKOUT gölge karnesi:** 3–4 hafta sonra gölge sinyaller replay edilip scope
  tamamen kaldırılacak mı, aşım freniyle geri mi açılacak kararı verilecek.
- **Kayıp modül dersi:** `yeni deneme/` altındaki yeni modüller commit edilmezse
  kutuya ulaşmaz ve ayar sessizce ölü kalır — `config.py` dışındaki her dosya takipli olmalı.

---

## 7. BACKEND giriş skoru kapısı — sızıntısız ölçüm (2026-08-11, ek tur)

`backend/research/backend_entry_gate_validation.py`. Kapı `services/signal_gates.py`
içinde pulse1/2/3 + smc sinyallerini (NDX+USOIL) **gerçekten bloklıyor** ve
2026-07-15'te (commit f080e5d) canlıya girdi → o tarihten sonra bloklanan sinyaller
DB'ye hiç yazılmadı. **Tarafsız pencere: 2026-05-01 → 07-14.**

Yöntem: backend'in KENDİ `compute_entry_score`'u, karar anında KAPANMIŞ MT5 M5/M30
barlarıyla; sonuç `prediction_logs.status` ile DEĞİL, M1 yarışıyla (aynı barda TP+SL
→ konservatif kayıp). İki geometri: (A) **nötr** TP=SL=1×ATR(5m) → saf yön kalitesi,
(B) **dönem geometrisi** (satırın TP1'i + `stop_loss_pips`).

**n = 20.732 sinyal (sansürsüz pencere):**

| küme | n | WR (nötr) | ort.R (nötr) | toplam R |
|---|---|---|---|---|
| tümü (kapı yokken) | 20.732 | %53.8 | +0.076 | **+1.580R** |
| kapıdan geçecek (skor≥7) | 7.648 | %54.1 | +0.082 | +626R |
| kapının eleyeceği (skor<7) | 13.084 | %53.6 | **+0.073** | +954R |

**Sonuç: kapının ayırt etme gücü YOK.** Elenen küme geçenlerden pratikte farksız
(+0.073 vs +0.082); gün-bloklu bootstrap'ta P(elenen > geçen) = **%44** — yani fark
şansla ayırt edilemiyor. Kapı sinyallerin **%63'ünü** eliyor ve toplam R'yi
+1.580R'den +626R'ye düşürüyor. Eşiklerin hiçbiri (5/6/7/8) toplam R'yi kapısız
hâlin üstüne çıkarmıyor; yalnız ≥8'de işlem-başına R yükseliyor (+0.162) ama hacmin
%86'sı gidiyor.

Sembol×model: NDX pulse3'te kapı işe yarıyor (elenen +0.066 vs tümü +0.160), ama
USOIL pulse1'de **ters** (elenen +0.112 vs tümü +0.079). Tutarlı bir yön yok.

**Kanıt tabanı doğrulanamadı:** raporun dayandığı "NDX skor≥7 WR %60→%65, USOIL
%49→%72" iddiası 20.7k sızıntısız panel sinyalinde yeniden üretilemiyor.

### 7b. Asıl sorun kapı değil, GEOMETRİ

Aynı sinyaller nötr 1:1 geometride **+1.580R** kazandırırken, dönemin kendi
geometrisiyle (TP1 dar, SL geniş) **−1.574R** veriyor. Yani panel sinyallerinin
girişinde küçük ama gerçek bir kenar var; onu yiyen şey TP/SL oranı.
Bu, 2026-07-28 ATR-merdiveni bulgusunun bağımsız bir teyidi.

### 7c. Kapı zaten yarı-etkili

Öz-denetim: skor<7 satırlarının oranı kapı öncesi %63.1 → kapı sonrası %31.5.
Düşüş kapının çalıştığını (ve skor yeniden üretiminin doğru olduğunu) gösteriyor,
ama bloklanması gerekenlerin yaklaşık yarısı hâlâ DB'ye giriyor (muhtemel nedenler:
backend DataHub mumları ile MT5 farkı, fail-open veri hataları, `log_prediction`
güvenlik-ağı yolundan giren yazarlar).

Sızma kırılımı (kapı sonrası, skor<7 çıkan satırlar):

| model | n | skor<7 | pay |
|---|---|---|---|
| pulse1 | 630 | 169 | %26.8 |
| pulse2 | 428 | 145 | %33.9 |
| pulse3 | 617 | 162 | %26.3 |
| **smc** | 97 | 83 | **%85.6** |
| NDX | 652 | 165 | %25.3 |
| USOIL | 1.120 | 394 | %35.2 |

`bypass_quality_filters` bunu açıklamıyor — o bayrak yalnız gölge-ters modellerde
(`*_inv`) kullanılıyor ve onlar bu kümede yok; `log_prediction` güvenlik ağı
`apply_signal_gates`'i tam olarak çağırıyor. Geriye iki olası neden kalıyor:
(1) kapı skoru **DataHub** mumlarından hesaplıyor, ben MT5'ten — sızanların en sık
ihlalleri de mum farkına en duyarlı göstergeler (`adx_dusuk` 289, `1h_karsi_momentum`
284, `5m_trend` 262); (2) veri hatasında kapı fail-open geçiyor
(`entry_score_gate fail-open` WARNING'leri Railway logunda sayılmalı).
smc'deki %85.6 ayrıca incelenmeli.

**Öneri:** backend kapısını da **gölgeye** al (`ENTRY_SCORE_GATE_ENABLED=0`, ya da
bot tarafındaki gibi ayrı bir BLOCK bayrağı) — kanıt yokken sinyallerin %63'ünü
elemek panel istatistiklerini ve bota giden oy akışını gereksiz daraltıyor.
⚠️ Bu değişiklik canlı sinyal hacmini ARTIRIR (bot daha çok oy görür) → kullanıcı
onayı ile yapılmalı.
