# MT5 Gerçek İşlem Otopsisi — analiz_paketi_2026-07-09

> Veri: `trades/mt5_deals_son_14gun.csv` (326 deal → 161 eşlenmiş pozisyon, 2026-06-25 → 07-09)
> + 4 sembolün 1m OHLCV'si. Tüm göstergeler (EMA/RSI/ATR/ADX/VWAP/Donchian/momentum, 1m+5m+30m)
> giriş anındaki bara hizalanarak hesaplandı. Simülasyonlar **pesimistik intrabar** (aynı barda
> SL+TP → SL sayılır). Ham çıktılar: `_otopsi_out/analiz_ciktisi_tur{1-4}.txt`,
> zenginleştirilmiş işlem tablosu: `_otopsi_out/trades_enriched_v3.csv`.

---

## 0. Yönetici Özeti

| Sembol | n | WR | PnL | Teşhis |
|---|---|---|---|---|
| NDX (NAS100) | 103 (62 TP / 41 SL) | %60 | **+2.625** | Kenar var ama ince; kötü saatler + karşı-trend girişler kârın yarısını yiyor |
| USOIL (SpotCrude) | 51 (25 TP / 26 SL) | %49 | **−2.640** | **Geometri hatası**: TP mesafesi SL'in 0.37'si → %73 WR gerekir, %49'la kanama |
| GDAXI (GER40) | 5 (2 TP / 3 SL) | %40 | **−1.097** | **Stop konfigürasyon hatası**: SL mesafeleri 14–23 ATR (!) |
| Toplam | 161 | %56 | **−353** | |

Üç kök neden, önem sırasıyla:
1. **TP/SL asimetrisi (en büyük kanama).** TP < SL her sembolde. Kazanınca az, kaybedince çok.
2. **Giriş yeri: bot lokal ekstremde giriyor.** SL işlemlerinde giriş dakikası, ±30dk penceresindeki
   EN KÖTÜ giriş noktası (U-eğrisi kanıtı, §4).
3. **Filtre boşlukları:** karşı-trend, düşük-ADX, bıçak-yakalama ve kötü-saat girişleri
   hiçbir kapıya takılmıyor.

---

## 1. Sembol / yön / bot (magic) kırılımı

```
sym   magic     yön    n   WR    PnL
NDX   52890971  SELL  82  0.61  +2277   ← Reflex/ana motor: tek kârlı blok
NDX   52890971  BUY    2  1.00   +800
NDX   52890970  BUY   10  0.50   −750
NDX   52890969  BUY    7  0.57   +447
USOIL 52890969  BUY   26  0.58   −998   ← WR %58 olduğu halde ZARAR (geometri!)
USOIL 52890969  SELL  22  0.41   −943
USOIL 52890970  SELL   3  0.33   −697
GDAXI (hepsi)          5  0.40  −1097
```

**Dikkat:** USOIL BUY %58 kazanıyor ama para KAYBEDİYOR — ortalama kazanç 194$, ortalama kayıp
−355$. Sorun seçicilikte değil, kazanç/kayıp oranında.

## 2. Kök neden #1 — TP/SL geometri asimetrisi

Gerçek çıkış mesafeleri (ATR cinsinden, medyan):

| Sembol | SL mesafe | TP mesafe | RR (TP/SL) | Breakeven WR | Gerçek WR |
|---|---|---|---|---|---|
| NDX | 4.66 ATR | 3.04 ATR | **0.65** | %61 | %60 → sınırda |
| USOIL | 7.58 ATR | 3.21 ATR | **0.42** | %70 | %49 → derin kanama |
| GDAXI | 17–23 ATR | 9–13 ATR | ~0.55 | %65 | %40 |

Aynı girişler + aynı SL ile TP genişletme simülasyonu (154 işlem, pesimistik):

```
USOIL RR=1.0 → WR %45, EV −0.078R   (mevcut: EV ≈ −0.32R)
USOIL RR=1.5 → WR %39, EV  0.000R
USOIL skor-kapısı (§6) + RR=1.0 → EV +0.22R  ← nihai reçete
NDX  hiçbir simetrik RR'de tek başına +EV değil → NDX kenarı filtre+saatten geliyor, geometriden değil
```

**GDAXI ayrıca:** 5 işlemde SL mesafesi 14–23 ATR. `2.5 lot × 120+ puan` stoplar tek işlemde
−678$ üretiyor. Bu bir strateji sorunu değil, **konfigürasyon hatası** (stop hesabı GER40'ın
puan değerine göre kalibre edilmemiş).

## 3. SL otopsisi — kayıplar nasıl kaybetti (MFE yol analizi)

SL olan 67 işlemin, SL yemeden önce lehe gittiği maksimum mesafe (R cinsinden):

```
anlık kayıp   (<0.1R)  17 (%26)  → giriş anı itibarıyla yanlış
0.1–0.3R               21 (%32)  → giriş yeri kötü (momentum tükenmiş)
0.3–0.6R               18 (%27)
0.6–1R                  6 (%9)   → çıkış/yönetim sorunu
>1R (TP'ye yaklaşıp döndü) 4 (%6)
```

**%58'i hiç 0.3R'yi göremedi** → sorun ezici biçimde GİRİŞ, çıkış değil.
(Journal tabanlı bağımsız otopsi `02_sl_otopsi.txt` aynı sonucu vermişti: %82 "anlık kayıp".)

## 4. "Grafiğin neresinde açılsaydı TP olurdu?" — giriş-kaydırma kanıtı

67 SL işlemi, **aynı fiyat mesafeleriyle** farklı zamanda/yerde açılsaydı (pesimistik sim):

```
giriş kaydırma   TP olurdu
   −30 dk           %54  ←── impulsun BAŞINDA girseydi yarısından çoğu TP
   −15 dk           %42
    −5 dk           %31
    ±0 dk           %19  ←── GERÇEK GİRİŞ ANI = pencerenin EN KÖTÜ noktası
    +3 dk           %34
   +15 dk           %36
   +30 dk           %43  ←── düzeltmeyi bekleyip girseydi de daha iyi
```

Mükemmel U-eğrisi: **sinyal, hareketin ortasında/sonunda ateşliyor ve bot tam lokal ekstremde
market emriyle giriyor.** Diğer yer testleri:

- **Retrace-limit girişi** (girişten x·ATR geri çekilmede limit): 0.3–0.8 ATR işe yaramıyor
  (%21–24, baz %19); ancak **2.0 ATR derin retrace → %39** (ama dolum riski).
- **SL fiyatından aynı yönde re-entry: %55 TP** — yani "doğru fiyat" çoğu kez tam stopun
  olduğu yerdi; stop dar + giriş erken.
- **⭐ SL anında TERS yöne giriş: %70 TP** (NDX %68 → EV +0.23R; USOIL %73).
  İki yarıda da tutuyor (NDX H1 %81 / H2 %55; USOIL %77/%69). **SL'lerimiz gürültü değil,
  gerçek trend-devam hareketleri tarafından yeniyor** — stop avı değil, yanlış yön.

## 5. Hangi filtreler eksikti / yanlıştı — what-if tablosu

İşlem bloklanmış olsaydı etkisi (ΔPnL = kurtarılan para; temporal split H1/H2 **7/7 tutarlı ✅**):

| Filtre (blok koşulu) | Blok | SL kurt. | TP kayb. | ΔPnL | WR |
|---|---|---|---|---|---|
| **NDX kötü saat {3,4,18,22} UTC** | 23 | 15 | 8 | **+5.078** | 60→68 |
| NDX (5m & 30m karşı-trend) veya kötü saat | 40 | 22 | 18 | +4.911 | 60→70 |
| Havuz: 5m karşı-trend (`trend5_s<0`) | 56 | 30 | 26 | +4.269 | 56→61 |
| **USOIL: 1h karşı-momentum veya ADX(1m)<20** | 22 | 15 | 7 | **+3.408** | 49→62 |
| Havuz: EMA200 karşı taraf | 58 | 30 | 28 | +3.413 | 56→60 |
| Havuz: ADX(1m)<20 (trendsiz piyasa) | 34 | 18 | 16 | +3.282 | 56→58 |
| NDX bıçak yakalama (`run30 < −1.5 ATR`) | 38 | 19 | 19 | +2.258 | 60→66 |
| USOIL NY-öncesi (<12 UTC) | 19 | 13 | 6 | +1.868 | 49→59 |
| Havuz: hacim patlaması (`vol_ratio>1.5`) | 18 | 11 | 7 | +2.509 | 56→58 |

**Yanlış hipotezler (uygulamayın):**
- "Kovalamaca filtresi" (`run30 > 1.5 ATR` blok) **ZARARLI**: NDX −1.974, USOIL −1.152.
  Bu motorlar momentum-devam motoru; koşmuş harekete binmek KAZANDIRIYOR (TP'lerin run30
  ortalaması +1.11 ATR). Geç kalma sorunu kovalamada değil, **karşı yöne açılan** işlemlerde.
- VWAP-kovalamaca bloğu (`rev_vwap>1`) havuzda −1.926 → mevcut motorlara uygulanmaz
  (journal'daki decider mean-reversion kapılarında geçerliydi, momentum botlarında değil).

**Bağımsız çapraz doğrulama:** journal tabanlı `02_sl_otopsi.txt` (n=663, farklı karar katmanı)
aynı yönde: kayıplarda ADX düşük ✓, vol_ratio yüksek ✓, trend-hizasızlık ✓. İki bağımsız veri
seti aynı üç filtreyi işaret ediyor.

## 6. TP'lerin ortak paydası → GİRİŞ SKORU (0–8)

TP ve SL popülasyonlarında koşul sağlanma oranları (Δ = TP% − SL%):

| Koşul | NDX Δ | USOIL Δ |
|---|---|---|
| İyi saat (NDX ∉{3,4,18,22}; OIL ≥12 UTC) | **+24** | **+26** |
| 1h momentum lehte (`mom60_s > −1`) | −1 | **+27** |
| 30m trend hizalı | −1 | **+22** |
| EMA200 doğru tarafta | +10 | +18 |
| 5m trend hizalı | **+16** | +15 |
| Bıçak değil (`run30 > −1.5`) | **+16** | +6 |
| ADX(1m) ≥ 20 | +4 | +15 |
| Hacim sakin (`vol_ratio < 1.5`) | +5 | +3 |

8 koşulun kaçı sağlanıyor → skor. Sonuç (gerçek işlemlerle):

```
NDX   skor=8 → WR %71, PnL +4.499 (n=34) | skor≤2 → WR %0, PnL −3.305 (n=6)
NDX   skor≥7 → n=51, WR %65, PnL +3.282   [baz: %60, +2.625]
USOIL skor≥7 → n=18, WR %72, PnL +1.151   [baz: %49, −2.640]
USOIL skor≥7 + RR=1.0 geometri → EV +0.22R (sim)
Skor kapısının bloklayacağı işlemlerin toplam PnL'i: NDX −658, USOIL −3.790 → kapı her iki sembolde net KÂRLI
Temporal split: skor≥6 dört alt-dilimde de (NDX/OIL × H1/H2) bazdan iyi ✅
```

## 7. MÜKEMMEL GİRİŞ REÇETESİ — uygulama sırası

### A. Acil (konfig düzeltmeleri, kod değişikliği minimal)
1. **GDAXI'yi askıya al** ya da stop hesabını düzelt: SL ≤ 6 ATR taban kuralı. Mevcut 14–23 ATR
   stoplar tek başına −1.860$ üretti.
2. **USOIL geometri:** `TP ≥ 1.0 × SL mesafesi` zorunlu (şu an 0.37). Tercihen SL'i 7.6 ATR'den
   ~4 ATR'ye çek + TP'yi eşitle. (`PULSE_ATR_GEOMETRY` benzeri bir `SR_BOT_MIN_RR=1.0` bayrağı.)
3. **Saat pencereleri** (`signal_gates.py` seans kapılarına ekle):
   - NDX: 03,04,18,22 UTC'de yeni giriş yok (ΔPnL +5.078, işlemlerin sadece %22'si bloklanıyor).
   - USOIL: 12 UTC öncesi yeni giriş yok (NY enerji seansı dışında kenar yok).

### B. Giriş Skoru Kapısı (yeni: `entry_score_gate`)
Sinyal anında 8 koşulu say; **skor < 7 → işlem açma** (log'a `entry_score` yaz):
```
1. saat penceresi uygun          5. 5m trend hizalı (close vs EMA50)
2. mom60 yön-işaretli > −1 ATR   6. run30 > −1.5 ATR (bıçak değil)
3. 30m trend hizalı              7. ADX(1m) ≥ 20
4. EMA200 doğru tarafta          8. vol_ratio(1m,60) < 1.5
```
Fail-open: veri eksikse koşul sağlanmış sayılır (mevcut kapı felsefesiyle uyumlu).

### C. SL-flip gölge protokolü (yaratıcı kısım — önce SHADOW)
SL gerçekleştiğinde **aynı yönde re-entry cooldown'u koru**, ama SL fiyatından **ters yöne**
gölge sinyal logla (`sl_flip_shadow`): TP = 1.0R, SL = 1.0R. Bu pakette %61–70 TP, EV +0.23R.
2 hafta gölge doğrulama → tutarsa gerçek modüle terfi. (Mantık: stopu yiyen şey trend-devamı;
stop bölgesi ters yön için momentum-teyitli giriş noktası.)

### D. Giriş yeri (U-eğrisinin çözümü)
"30dk önce girmek" mümkün değil; eşdeğeri **sinyalin tetiklendiği impulsu erken yakalamak**:
- Reflex/sr botlarında tetik değerlendirmesini bar kapanışı yerine bar-içi (tick) yap;
  sinyal koşulu ilk sağlandığı anda gir — mevcut gecikme, girişleri impulsun sonuna itiyor.
- Girişten sonra 0.3R'lik erken teyit: pozisyon 10 barda 0.3R MFE göremediyse yarım kapat
  (SL'lerin %58'i bu profilde; kazananların TP'ye medyan yolu 4 bar).

### Beklenen birleşik etki (bu 14 günlük örneklemde, in-sample)
```
Mevcut:  161 işlem, PnL −353
Reçete:  GDAXI askı (+1.097) + NDX skor≥7 (+657) + USOIL skor≥7&RR1.0 (≈ +3.8k swing)
         → aynı dönemde tahmini +4.4k ile +5.5k arası, işlem sayısı ~%55 azalır
```

## 8. Dürüstlük notları (okumadan uygulama)
- 14 gün / 154 çözümlü işlem **küçük örneklem**; filtre eşikleri bu veri üzerinde seçildi
  (in-sample). Temporal split 7/7 tutarlı ve journal-tabanlı bağımsız otopsiyle uyumlu olsa da,
  **önce gölge/paralel logla, 2 hafta sonra karşılaştır** — `bias_test` altyapısındaki
  run_label deseni aynen kullanılabilir.
- Simülasyonlar pesimistik intrabar; spread/komisyon dahil değil (deal'lerde commission=0 demo).
- USOIL RR tahmini (0.37) medyan bazlı; işlem bazında gerçek TP seviyeleri deal CSV'de yok.
- SL-flip %70'in H2'de NDX'te %55'e düşmesi rejim bağımlılığı işareti — terfi kriteri
  "iki bağımsız pencerede ≥%55 + EV>0" olmalı.

---

## 9. NDX DERİN OTOPSİ (2026-07-10 eki) — işlem işlem SL forensiği

Kaynak: `_otopsi_out/ndx_sl_forensik.csv` + `analiz_ciktisi_tur5_ndx.txt`.
Magic → strateji eşlemesi (`yeni deneme/config.py` + `claude_decider/allocator.py`):
`52890969=MOM/SR` (momentum-devam + S/R), `52890970=CHREV` (kanal-dönüş mean-reversion),
`52890971=VIXREG` (VIX-rejim NDX yön stratejisi).

### 9.1 Hangi model neyi açtı, ne kazandı/kaybetti
```
VIXREG SELL: 82 işlem (50 TP / 32 SL, %61)  net +2.277   ← ana motor
VIXREG BUY:   2 işlem (2 TP)                net   +800
CHREV  BUY:  10 işlem (5 TP / 5 SL)         net   −750
CHREV  SELL:  2 işlem (1/1)                 net   −150
MOM/SR BUY:   7 işlem (4 TP / 3 SL)         net   +447
```

### 9.2 SELL SL'ler neden oldu (33 adet, −18.174$) — hepsi VIXREG (1 CHREV hariç)
Etiket dağılımı (bir işlem birden çok etiket alabilir):
```
BIÇAK (30dk'da >1.5 ATR ralliye satış)  14 işlem  −7.720$   ← en büyük tekil neden
KÖTÜ-SAAT {03,04,18,22 UTC}             13 işlem  −7.178$
TEMİZ-KAYIP (tüm koşullar uygundu)      10 işlem  −5.498$   ← geometrinin doğal maliyeti
1H-KARŞI-MOMENTUM                        9 işlem  −4.952$
CHOP (ADX1m<20)                          7 işlem  −3.868$
KARŞI-TREND (≥2/3 TF hizasız)           12 işlem  −6.618$
```
- **Skor<7 kapısı 17/33'ünü yakalardı (−9.370$ kurtarır).** Kalan 16'nın 10'u
  "temiz kayıp" — bunlar filtreyle değil ancak geometriyle (TP/SL oranı) iyileşir.
- **Flip testi: 33 SELL SL'in 23'ü (%70) ters yönde TP olurdu** — stopları yiyen şey
  gürültü değil, gerçek yukarı hareketler.

**VIXREG'in yanılgı mekanizması (asıl cevap):** VIXREG makro VIX rejimine bakarak
gün-yönü SELL kararı veriyor ve **gün-içi mikro-yapıyı hiç kontrol etmiyor**:
```
Fiyat EMA200(1m) ALTINDAyken satış: 58 işlem, WR %66, +4.078$  ← model burada haklı
Fiyat EMA200(1m) ÜSTÜNDEyken satış: 24 işlem, WR %50, −1.800$  ← tüm fazla kayıp burada
```
Yani strateji doğru (makro yön edge'i gerçek, +2.277 net), ama **"ne zaman" sorusunu
hiç sormuyor**: taze 30dk rallisinin ortasına, ölü saatlere ve fiyat gün-içi yukarı
rejimdeyken satıyor. 07-02 (10 SL) ve 07-08 (12 SL) tek başına SELL kayıplarının
%55'i — ikisi de gün içinde sert yukarı dönüşlerin olduğu günler.

### 9.3 BUY SL'ler neden oldu (8 adet, −3.307$)
- **5'i CHREV**: kanal alt bandında düşen bıçağı satın alma — tipik profil
  `KARŞI-TREND(3/3) + BIÇAK + 1H-KARŞI-MOM` (07-07 04:14 skor=1!). CHREV'in
  araştırmadaki edge'i "kanal sınırından RED (rejection) teyidi" idi; canlı giriş
  teyit beklemeden dokunuşta açıyor. 12 CHREV işleminin neti −900$ (araştırma
  %72-84 WR vaat ediyordu, canlı %50).
- **3'ü MOM/SR** (küçük kayıplar −166/−188/−202): 07-09 satış günü karşı-trend BUY.
- Skor<7 kapısı 8'in 6'sını yakalardı (−2.555$); flip 5/8 TP.

### 9.4 Çürütülen hipotez: günlük devre kesici
"Aynı gün N SL sonrası dur" kuralı test edildi ve **ZARARLI çıktı**: gün içi 3+ SL
sonrası açılan işlemler WR %60-69 / net +2.190$. Kayıp günlerinde bile sonraki
işlemler kazanıyor (VIXREG'in gün-yönü edge'i gün boyu geçerli). Devre kesici KOYMA.

### 9.5 NDX-özel aksiyonlar (öncelik sırasıyla)
1. ✅ **UYGULANDI (2026-07-10):** `signal_gates.py`'a NDX {03,04,18,22} UTC seans
   bloğu + 8-koşullu `entry_score_gate` (ENTRY_SCORE_MIN=7) eklendi — panel
   modelleri (pulse/smc) için. **Bot tarafı (`yeni deneme/`) henüz bağlanmadı** —
   MT5 işlemlerini etkilemesi için VIXREG/MOM-SR emir öncesi aynı skorun
   çağrılması gerekir (CHREV hariç, bkz. madde 3).
2. **VIXREG'e mikro-yapı kapısı:** fiyat EMA200(1m/5m eşleniği) üstündeyken SELL
   açma (24 işlem, −1.800$ → sıfırlanır); run30 > +1.5 ATR ralli ortasında SELL
   erteleme (tetiği ralli soğuyana — örn. run30 < 0.5 ATR — kadar beklet).
3. **CHREV'e skor kapısı UYGULANMAZ** (mean-reversion doğası gereği karşı-trend;
   TP'leri de düşük skorlu). CHREV'in asıl eksiği **rejection teyidi**: dokunuşta
   değil, banttan dönüş barı (1m kapanışı bant içine geri) teyidiyle gir.
4. **SL-flip gölge modülü** NDX'te en güçlü: SELL SL'lerin %70'i ters (BUY) TP.
   `sl_flip_shadow` logger'ı VIXREG stop-out'larına bağla, 2 hafta ölç.
5. Temiz kayıplar (10/33) filtreyle iyileşmez → TP/SL geometrisi: NDX RR şu an
   0.65-0.73; skor≥7 altkümede RR=1.0 denemesi gölge olarak loglanmalı.

---

## 10. BOT TARAFI BAĞLANDI (2026-07-10) — `yeni deneme/entry_gate.py`

§9.5 madde 1'deki "bot tarafı bağlanmadı" eksiği kapatıldı. Panel kapıları
(`backend/services/signal_gates.py`) yalnız panel modellerini koruyordu; MT5
emirlerini açan bot artık kendi giriş kapısına sahip.

**Neden ayrı modül:** Bot MT5'ten **gerçek 1m** çekiyor (backend'de 1m stream yok,
5m'e yaklaşıyordu). `entry_gate.py` otopsideki §6 eşiklerini **orijinal 1m-ATR
tabanıyla** hesaplar → en yüksek sadakat. `indicators.py`'ın kanıtlanmış
`_ema/_atr/_adx`'ini yeniden kullanır (DRY).

**Bağlantı noktaları (`forexsai_demo_bot.py`):**
| Giriş yolu | Magic | Kapı | Gerekçe |
|---|---|---|---|
| `check_vix_regime` (VIXREG) | 52890971 | skor + **VIXREG mikro** (EMA200 tarafı + ralli ertele) | SELL SL kanamasının ana kaynağı (§9.2) |
| `check_scope` (MOM/SR momentum) | 52890969 | skor (NDX/USOIL) | §6 skor kanıtı |
| `check_channel_reversion` (CHREV) | 52890970 | **kapı YOK** | mean-reversion doğası karşı-trend; skor yanlış negatif üretir |

`entry_gate_check()` merkezi yardımcı: 1m/5m/30m mumları çeker, skoru hesaplar,
blok halinde `_log_trade("GATE_SCORE"/"GATE_VIXMICRO", …)` ile CSV'ye yazar +
`return False`. **Fail-open**: veri/hata → açar (mevcut kapı felsefesi).

**Config bayrakları (`config.py`):** `ENTRY_SCORE_GATE_ENABLED=True`,
`ENTRY_SCORE_MIN=7`, `ENTRY_SCORE_SYMBOLS={NDX,USOIL}`, `SESSION_BLOCK_HOURS_UTC`
(NDX {3,4,18,22}, USOIL 0-11), `VIX_REGIME_MICRO_GATE=True`.

**Testler:** `yeni deneme/test_entry_gate.py` — 13/13 geçti (skor, saat, hacim,
bıçak, VIXREG mikro EMA200-tarafı, fail-open). Senaryo doğrulaması: otopsideki
tipik kayıp kurulumu (yükselen fiyatta 03 UTC SELL) skor 2/8 + mikro → çift blok;
sağlıklı kurulum (düşen trendde 16 UTC SELL) skor 8/8 → geçer.

**Kalan (bilerek yapılmadı — ayrı karar/gözlem gerektirir):**
- GDAXI stop-geometri fixi (§7-A.1) ve USOIL RR≥1.0 (§7-A.2): TP/SL hesabı
  `_fixed_distances`/`ROBUST_SCOPES` ve VIXREG TP/SL'de; risk-mesafesi değişikliği
  canlı davranışı doğrudan etkilediği için gözlem penceresi sonrası önerilir.
- `sl_flip_shadow` modülü (§7-C): ayrı gölge-log altyapısı; VIXREG stop-out'larına
  bağlanacak, 2 hafta ölçülüp terfi edilecek.
