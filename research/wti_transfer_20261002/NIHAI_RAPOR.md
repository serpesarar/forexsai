# WTI / USOIL — Nasdaq kapılarının aktarımı ve petrol varyasyonları

**Sonuç: Nasdaq’ta seçilen kapılar WTI’ye aynı başarıyla taşınmadı. Beş petrol fikrini 20 varyasyonla sınadım; bu çalışma beş kârlı veya canlıya hazır kapı bulmadı. EIA sonrası kırılım ve normalize stres sonrası alış küçük örneklem araştırma fikirleri olarak kaldı.**

## 1. Veri bütünlüğü: sonuçtan önce dikkat edilmesi gereken bulgu

Panelin petrol M1 geçmişinde farklı fiyat tabanları iç içe geçiyor. Doğrudan MT5 ile 46.806 ortak mum karşılaştırmasında 20.820 kapanış aynı; 233 ardışık dakika geçişinde iki serinin fiyat farkı 10 centten fazla değişiyor. İlk gözlenen geçiş 28 Ağustos 03: 36UTC. Eylül 21 gibi günlerde bu fark yaklaşık 4,6 dolarlık sıçramalar yaratıyor. Bu, saat kaymasından farklı bir fiyat bütünlüğü sorunu; akışın kök nedeni bu araştırmada değiştirilmedi. Projenin mevcut `bl_ab30ec56db` ve `bl_5830306710` kayıtlarında Yahoo/MT5 fiyat tabanı karışması ve geçmiş cache onarımı zaten açık; bulgum bu kayıtlarla uyumlu, güncel üretim durumunun doğrulaması değildir.

Tam çakışmada ±1 saat kaydırınca günlük fiyat farkından arındırılmış medyan hata yaklaşık 0,294–0,295 dolar; doğru saatle 0,003 dolar. Saat eşlemesi geçiyor, panel fiyat tutarlılığı geçmiyor. İlk 180 mumluk referans kontrolü tek başına bu sorunu yakalamamıştı; tam geçmiş kontrolü yakaladı.

**Kanıt kapsamı:** Panel VALID döneminde 20 Mayıs–27 Ağustos NY kullanılır. 28 Ağustos sonrası panel sonuçları yalnız tanı çıktısıdır. Nihai Eylül–1 Ekim testinde doğrudan SpotCrude serisi kullanılır. Fiyat mumları birbirine eklenmedi; rapordaki birleşik işlem istatistiği bu iki çakışmayan dönemin ayrı yürütülmüş R defterlerini toplar. Bu veri bütünlüğü kararı sonuçlar görüldükten sonra yapılan bir düzeltmedir; temiz yeni dış örneklem veya bağımsız sağlayıcı doğrulaması olarak sunulmuyor.

Önceki M1/M5 eşleşmesi keşifte hareket korelasyonu 0,995–0,999, VALID_A’da 0,9997; yine de fiyat tabanı ve geçmiş gerçek spread tam kanıtlanmış değildir. Bu eski bölüm de gerçek işlem PnL kanıtı değildir. Ayrıntılar: `historical_price_integrity.json`, `price_basis_overlap.csv`, `verification.json`.

## 2. İndirilen veri ve saatler

| Seri | Kullanılan mum | Başlangıç UTC | Son UTC |
|---|---:|---|---|
| cache M1 | 228,310 | 2026-02-10 22: 00: 00+00: 00 | 2026-10-01 23: 59: 00+00: 00 |
| direct M1 | 46,806 | 2026-08-16 22: 00: 00+00: 00 | 2026-10-01 23: 59: 00+00: 00 |
| native M5 | 93,218 | 2025-06-10 19: 40: 00+00: 00 | 2026-10-01 23: 55: 00+00: 00 |
| native M15 | 84,446 | 2023-03-09 03: 30: 00+00: 00 | 2026-10-01 23: 45: 00+00: 00 |
| native M30 | 62,255 | 2021-06-30 17: 00: 00+00: 00 | 2026-10-01 23: 30: 00+00: 00 |
| native M60 | 61,150 | 2016-05-31 06: 00: 00+00: 00 | 2026-10-01 23: 00: 00+00: 00 |

Altı zaman diliminin ham cache geçmişi ve VIX/OVX/DXY/CL=F referansları indirildi. Broker SpotCrude: point 0,001,100 barrel/lot. MT5 ham mum saati bu Ağustos–Eylül döneminde UTC+3; normalleştirme−10.800 s. Panel/native saat UTC: Nasdaq’a uygulanan eski NY+7 veya erken Mart düzeltmesi petrole uygulanmadı. İstenen USO, USOIL.FOREX/WTI olarak yorumlandı; USO ETF testi yapılmadı.

MT5 terminalindeki sınırlı geçmiş indirme sırasında ilerledi: metadata 13 Ağustos başlangıcı gösterse de nihai kullanılan doğrudan M1 başlangıcı 16 Ağustos 22: 00UTC. Ham indirmede 46.807 satır; 2 Ekim sınırındaki mum çıkarılınca 46.806. D1 ham geçmişi 2010’dan geliyor ama 28 Temmuz 2026’da bitiyor; güncel makro etiketi olarak kullanılmadı. Önceki tamamlanmış 16: 00NY CFD kapanışı kullanıldı, futures settlement diye adlandırılmadı.

Dukascopy 2025 M1 indirmesi HTTP429, alternatif host 403 nedeniyle veri sağlamadı. Bu nedenle 2025 M1 testini yapılmış saymıyorum. Çok yıllı M15/M30/H1 inceleme M1 yürütmenin yerine geçmez. H1 enerji varyasyonunda 14: 30 OHLC içinden bilinemez: 14: 00 açılış vekili kullanıldı, sonraki saat içi hareketler okunmadı.

## 3. Hangi önceki testler taşındı?

| Araştırma bölümü | Kapsam | Sonuç hücresi |
|---|---|---:|
| İlk 432 ve genişletilmiş 1620 tanım | 540 sinyal ×3 risk/çıkış geometrisi; ilk 432 altküme | 16200 |
| Keşif ayrı kayıt | Aynı 1620 tanım, iki keşif yarısı; tekrar gözlenen testler | 3240 |
| Dondurulmuş 10 strateji /20 mekanizma /kapılar |87 isimli test ve ebeveyn/kör/makro/mikro kontrolleri | 6090 |
| CAPREV / çıkış /VIX /overnight /sermaye |19 günlük-yol tanımı +6 overnight +4 portföy kolu | 3340 |
| Petrole özgü 5 aile |20 varyasyon; M1/M3/M5/M15 ve stres ailesinin native testi | 1544 |
| Ek geometri tanıları |10 seçilmiş strateji ×1: 1 /literal 35 /literal 80–110 | 300 |
| **Toplam hesaplanan dönem hücresi** | Keşif tekrarları ve bağımlı kontroller dahil | **30714** |

Tarama 1620 + ayrıntılı 87 + günlük 29 + petrol 20 +tanı 30 =1786 adlandırılmış konfigürasyon; ekonomik olarak benzersiz 1786 kapı değildir. Dondurulmuş adaylar taramanın altkümesi; BASE/CAPREV/DIP_SAME, O4_OVX_TP1/O5_LONG gibi tanımlar aynı olayları paylaşır. TF/maliyet/sağlayıcı/split sayısı işlem örneklemi sayısı değildir.

Aktarılan kapılar: H1/K5b, K5, H2, RAWVOL, H3, WAITALL, H4, K6, COMBINED, H5 ve geri-alım kontrolleri; diğer rapordaki K1 Pazartesi satış, K2 FOMC, K3 ay sonu, K4a/bVR15/240, CHASE ve birleşimleri. K3 son iki iş günü standart hafta takvimidir; tatil duyarlı exchange takvimi değildir. Bazı önceki miner/gerçek-bot analizleri botun niyet/log evrenini gerektirir; OHLC’den aynı kapı-atlama, HOLD, cooldown, broker dolumu veya bot USD kazancı üretilmedi.

## 4. Yürütme ve kronoloji

M1/M3/M5/M15 sinyali yalnız kapanmış mumlar; yürütme sonraki tam M1 açılışı. ATR70/ATR14 ve makro yalnız o anda bilinen geçmiş. İlk araştırma penceresi Mon–Thu 03: 00–15: 30, son çıkış 15: 55. Petrole uyarlanan minimum stop 0,05USD/barrel; hızlı 2ATR/15 dk/RR2, ana 5ATR/90 dk/RR1,5, yavaş 8ATR/240 dk/RR2. Sabit petrol geometri TP%1,04/SL%1,49, önceki fiyat üzerinden risk. Nasdaq 35/80/110 nominal dolar mesafeleri ayrı tanı olarak saklandı.

Cache spread 0,03USD vekil; doğrudan MT5 M1 kayıtlı bar spreadi medyan 0,024USD. Bu bar spreadi gerçek tarihsel giriş anı bid/ask spreadi değildir. Her tarafta 0,002 slip; ek test spread×3, slip 0,01 ve giriş +1 M1. Komisyon ve gerçek geçmiş finansman bilinmiyor; overnight için 5 bp/gece yalnız duyarlılık. Sonuçlar maliyet modeli sonrası R, broker hesap USD veya kâr tahmini değildir.

DISC_A11Şub–31Mar; DISC_B1Nis–15May. VALID_A20May–30Haz; VALID_B1Tem–28Ağu (kanıtta 28Ağustos çıkarıldı). FINAL_A1–15Eyl; FINAL_B16Eyl–1Eki. Split sınırını geçen sonuçlar dışarıda. Doğrudan makro kendi kapanışlarından hesaplanır; 20 gün volatilite ve 200 gün uzama ısınması veri başında yoktur. H4/K6 gibi 200 gün isteyen kapı için doğrudan kısa geçmiş sıfır etki gösteriyorsa bu doğrulama değildir.

Her defterde tek pozisyon ve 600 s yeniden giriş aralığı. Stop/TP aynı mumsa stop öncelikli; açılış hedefi sonraki stop hareketinden önce; stopgap kötü açılıştan dolabilir. Gün içi bilinmeyen veri boşluğunda son gözlenen fiyatla vekil R hesaplanır; `data_gap` etiketi ve en az−1R duyarlılığı korunur. Bu gerçek dolum değildir. Gece işleminin terminal seansı eksikse sonuç çözülememiş olarak ayrı tutulur. Native M15/30/H1 OHLC stop sırası belirsiz ve spread vekil olduğundan go-live yürütme kanıtı sayılmaz.

## 5. Beş petrol fikri: ayrı doğrulama ve nihai MT5 dönemi

Aşağıdaki temsilciler kârlı diye seçilmiş yeni beşli portföy değildir; 20 sabit varyasyondan her mekanizmayı anlatan örneklerdir. Birleştirilmiş sonuç, VALID cache (<28Ağu) + FINAL direct (Eyl–1Eki); aynı olaylar çift sayılmadı.

| Fikir | n | Toplam R | EV R | WR ve Wilson%95 | Gün-bootstrap EV%95 | MaxDD R |
|---|---:|---:|---:|---|---|---:|
| O1_ENERGY_NO_EIA: Enerji seansı / EIA çevresi veto | 77 | -15.40 | -0.20 | 35.1% [25.3,46.2] | [-0.372,-0.005] | 16.39 |
| O2_SPREAD10: Spread/risk kontrollü geri çekilme | 76 | -12.43 | -0.16 | 32.9% [23.4,44.1] | [-0.360,+0.045] | 17.16 |
| O3_BREAK5: EIA sonrası 5 dk kırılım kabulü | 17 | +3.23 | +0.19 | 52.9% [31.0,73.8] | [-0.284,+0.670] | 2.01 |
| O4_OVX_TP1: OVX / normalize düşüş / +1R hedef | 18 | +1.43 | +0.08 | 55.6% [33.7,75.4] | [-0.159,+0.315] | 1.58 |
| O5_BOTH: Simetrik şok sonrası geri dönüş | 26 | +0.28 | +0.01 | 46.2% [28.8,64.5] | [-0.211,+0.224] | 2.39 |

**O1:**15 dakikalık orta seviyeyi yönsel/verimli hareketle geri alma. Keşifte seçilen LEGACY iyi görünmesine rağmen ileri döneme taşınmadı. Enerji penceresi ve EIA çevresi veto maliyet/yoğunluğu değiştirdi; kalıcı pozitif kenar yaratmadı.

**O2:**30 dakikalık verimli geri çekilme; spread/risk≤%10/20. Bu stop boyutlarında her iki spread filtresi BASE ile aynı işlem kümesini bıraktı. Bir şey elemediği için başarı katmış kabul edilemez. 3 dakika bekleme de güvenilir iyileştirme üretmedi.

**O3:**EIA öncesi tam 60M1 range, yayın+5 veya+15 dakika sonrasında gövdeli kırılım; release+45 e kadar ilk olay,5ATR/90 dk/RR1,5. BREAK5 küçük pozitif; 5 ve 15 dakika tetiklerde VALID bölümü negatif. Keşif BREAK5 negatifken sonraki pozitif olduğu için bu zaten istikrarlı iki-yarı başarı değildir. Yayın sonrası range içi FADE5 çoğunlukla negatif. Haber sürprizi/beklenti verisi kullanılmadı.

**O4:**Önceki petrol getirisi−1σ veya 5 gün−√5σ, önceki 09: 00–14: 30 seans düşük seviyesi altında ilk kapanış; OVX önceki 252 gün medyanı üstünde, günlük σ risk, +1R veya 14: 30. VIX 18,4 yerine petrolün kendi volatilitesini kullanma fikri mantıklı ama örneklem küçüktür. Native sonuçlar yıl/TF arasında işaret değiştirir.

**O5:**Aynı stressin yukarı aynasıyla satış veya aşağı stres sonrası alış; BOTH geri dönüş, CONTINUE şoku takip. Yönü ters çevirmek istikrarlı fark üretmedi. Native H1 BOTH: 265 olayına rağmen yakın dönemi negatiftir; uzun örneklem tek başına geçiş bileti değildir.

### 20 varyasyonun tamamı — hiçbir başarısız kol gizlenmedi

| Varyasyon | VALID cache n/R (<28Ağu) | FINAL direct n/R | Birleşik n/R |
|---|---|---|---|
| O1_LEGACY | 112/-32.71 | 38/-2.46 | 150/-35.17 |
| O1_ENERGY | 47/-5.36 | 20/-1.90 | 67/-7.26 |
| O1_ENERGY_5D | 55/-9.51 | 23/-3.89 | 78/-13.40 |
| O1_ENERGY_NO_EIA | 54/-11.51 | 23/-3.89 | 77/-15.40 |
| O2_BASE | 52/-13.78 | 24/+1.35 | 76/-12.43 |
| O2_SPREAD10 | 52/-13.78 | 24/+1.35 | 76/-12.43 |
| O2_SPREAD20 | 52/-13.78 | 24/+1.35 | 76/-12.43 |
| O2_WAIT3 | 46/-11.38 | 19/-2.05 | 65/-13.43 |
| O3_BREAK5 | 12/+1.85 | 5/+1.38 | 17/+3.23 |
| O3_BREAK15 | 12/+1.31 | 5/+0.87 | 17/+2.18 |
| O3_FADE5 | 12/-5.06 | 4/-2.60 | 16/-7.66 |
| O3_FADE15 | 9/-0.84 | 3/-1.59 | 12/-2.44 |
| O4_BASE | 16/+0.96 | 3/+1.29 | 19/+2.25 |
| O4_OVX | 15/+0.39 | 3/+1.29 | 18/+1.68 |
| O4_OVX_TP1 | 15/+0.14 | 3/+1.29 | 18/+1.43 |
| O4_OVX_HALF | 15/+0.27 | 3/+1.29 | 18/+1.56 |
| O5_LONG | 15/+0.14 | 3/+1.29 | 18/+1.43 |
| O5_SHORT | 7/-0.15 | 1/-1.00 | 8/-1.15 |
| O5_BOTH | 22/-0.01 | 4/+0.29 | 26/+0.28 |
| O5_CONTINUE | 22/-0.48 | 4/-0.48 | 26/-0.96 |

### Zaman dilimi doğrulaması — aynı M1 yürütme

| Temsilci | M1 n/R | M3 n/R | M5 n/R | M15 n/R |
|---|---|---|---|---|
| O1_ENERGY_NO_EIA | 77/-15.40 | 104/+2.63 | 118/-5.25 | 87/-11.70 |
| O2_SPREAD10 | 76/-12.43 | 94/-13.87 | 68/+7.55 | 56/-0.84 |
| O3_BREAK5 | 17/+3.23 | 15/+1.59 | 16/-0.53 | 9/+1.08 |
| O4_OVX_TP1 | 18/+1.43 | 18/+1.52 | 18/+1.29 | 17/+0.88 |
| O5_BOTH | 26/+0.28 | 26/+0.49 | 26/+0.15 | 23/-1.42 |

TFler aynı piyasa günlerini paylaştığından örnek sayıları toplanamaz. Özellikle O2M5 pozitif görülüp M1/M3 negatif çıkması başarılıM5 yeniden seçimi için izin değildir; yeni dönem testi gerektirir.

### Maliyet ve gecikme — M1 net toplamR

| Temsilci | Baz | Spread×3 | Slip 0,01 | +1M1 |
|---|---:|---:|---:|---:|
| O1_ENERGY_NO_EIA | -15.40 | -19.25 | -16.44 | -13.94 |
| O2_SPREAD10 | -12.43 | -14.75 | -13.42 | -11.88 |
| O3_BREAK5 | +3.23 | +1.89 | +2.66 | +3.39 |
| O4_OVX_TP1 | +1.43 | +1.06 | +1.32 | +1.42 |
| O5_BOTH | +0.28 | -0.19 | +0.14 | +0.35 |

### Çok yıllı stres varyasyonları — ayrı nativeOHLC, yalnız 2025 sonuna kadar

| Kural | M15 n/R | M30 n/R | H1 n/R |
|---|---|---|---|
| O4_BASE | 82/-1.13 | 114/+1.08 | 215/+2.34 |
| O4_OVX_TP1 | 41/-0.47 | 60/+3.45 | 114/-0.68 |
| O5_SHORT | 23/-2.28 | 54/-0.67 | 102/+1.81 |
| O5_BOTH | 64/-2.76 | 114/+2.78 | 216/+1.13 |
| O5_CONTINUE | 64/+0.21 | 114/-6.55 | 216/-11.19 |

Yıl bloklarının tüm istatistikleri `oil_variants.json` içinde. H1 ilk 2016–2020 dönemi ile 2021–2023/2024–2025 aynı değildir. Buradaki 200+OHLColayı 150 gerçek nextM1/actualspread koşulunu karşılamaz.

## 6. Nasdaq’taki kazanç fikri WTI’de ne oldu?

| Önceden dondurulmuş Nasdaq stratejisi | WTI kanıt dönemi n/R |
|---|---|
| exhaustion_60_none_buy | 368/-34.20 |
| sweep_60_quiet_buy | 116/-18.34 |
| failed_break_60_h 1_both | 276/-2.54 |
| efficient_pullback_30_efficiency_both | 194/-41.98 |
| midpoint_reclaim_30_quiet_sell | 194/-10.90 |
| opening_break_60_quiet_both_fast | 135/-15.62 |
| exhaustion_15_none_sell_core | 158/-15.02 |
| sweep_30_none_sell_slow | 261/-21.57 |
| variance_switch_30_quiet_both_core | 326/-11.52 |
| failed_break_60_none_buy_fast | 343/-72.90 |

Nasdaq beşli araştırma portföyü ve ek CAPREV, bütün fırsatlarla tekrar yürütüldü; yalnız kabul edilmiş eski işlemlerden türetilmedi.

| Portföy | n | Toplam R | Taban farkıR | Gün-eşli fark güven aralığı |
|---|---:|---:|---:|---|
| NONE | 545 | -51.16 | +0.00 | [+0.000,+0.000] günlükR |
| BASE | 508 | -50.54 | +0.62 | [-0.168,+0.196] günlükR |
| HALF_RISING | 519 | -51.82 | -0.66 | [-0.122,+0.100] günlükR |
| TP1_RISING | 519 | -51.82 | -0.66 | [-0.122,+0.100] günlükR |

Nasdaq’ta daha önceki +9,40R katkı WTI için varsayılmadı. RisingVIX/+1Rburada petrolmekanizması olarak doğrulanmadı; CAPeklemek kaybeden taban portföyünü otomatik kârlı yapmıyor.

| Günlük yol / negatif kontrol | n | ToplamR |
|---|---:|---:|
| BASE | 6 | -1.07 |
| FRESH_CROSS | 3 | +0.38 |
| CASH_ONLY | 5 | -2.03 |
| FAIL_10 | 6 | -0.64 |
| HALF_RUNNER | 6 | -1.22 |
| VIX_COOLING | 2 | +0.72 |
| ALREADY_BELOW | 5 | -0.07 |
| FULL_TP1 | 6 | -1.36 |
| ALWAYS_10 | 6 | -0.45 |
| VIX_RISING | 4 | -1.79 |
| HALF_RISING | 4 | -1.79 |
| TP1_RISING | 4 | -1.79 |
| CAPREV | 6 | -1.07 |
| CAP_ALLVIX | 29 | -0.61 |
| CAP_LOWVIX | 23 | +0.46 |
| CAP_CALM | 3 | -0.13 |
| CAP_SELL | 6 | +1.61 |
| CAP_FIXED | 6 | +2.48 |
| CAP_RECLAIM | 3 | +0.30 |
| ON_OPEN_SAME | 9 | -0.67 |
| ON_DIP_SAME | 6 | -1.07 |
| ON_DIP_NEXT | 6 | -1.86 |
| ON_OPEN_NEXT | 7 | -3.30 |
| ON_UNION_SAME | 10 | -0.61 |
| ON_UNION_MIXED | 10 | -1.40 |

Açılış/gece kombinasyonu tek pozisyon altında ölçüldü. İki ayrı bacağın toplamı iki katsermaye veya birbirini örten pozisyonlarla başarı diye raporlanmadı. Fonlama duyarlılığı ve çözülememiş işlemler `daily.json` içinde.

## 7. Kontroller, belirsizlik ve karar

Seçim 1620 deneme yükü taşır. Bootstraplar gün bloklarıyla 4000 tekrar, işlemWRWilson%95, iki kronolojik yarı ve eniyi 5 işlem çıkarma çıktıları korunmuştur. Çoklu testten bağımsız alfa iddiası yok. BREAK5 eniyi 5 işlem çıkarılınca pozitiflik kaybolur; +R örneklerin küçük sayısına dayanır. Her işleme eşitRrisk yaklaşımı kullanıldı; sabitlot ve eşitRkazanç aynı şey değildir.

EIA BREAK5 pozitif net R gösterse de aynı gün/saat/yön/geometri genel dakika girişlerinden daha iyi değildir: VALID lift yaklaşık−0,27R, FINAL lift−0,38R. Dolayısıyla pozitif toplamı kanıtlanmış giriş becerisi diye yorumlamıyorum. Aynı gün/saat/yön/geometri genel dakika girişleriyle O1/O2/O3 matchedEV karşılaştırması yapıldı (`controls.json`). Bu genel fırsatlar örtüşür; yürütülebilir portföy PnL olarak sunulmaz. EIA için bu genel saat kontrolü haberçevresi etkisini bütünüyle ayırmaz. OVX/BASE, EIA veto/ebeveyn, WAIT3/ebeveyn ve dönüş/devam gün eşli karşılaştırmaları da saklandı. Veto ardından boşalan sermayenin alacağı farklı fırsatlar defterde yeniden yürütüldü.

| Kontrol | n | Aynı gün/saat/yön tabanEV | Aday liftEV | Lift%95 |
|---|---:|---:|---:|---|
| cache/O1_ENERGY_NO_EIA | 54 | -0.04 | -0.17 | [-0.243,-0.107] |
| cache/O2_SPREAD10 | 52 | +0.07 | -0.34 | [-0.519,-0.187] |
| cache/O3_BREAK5 | 12 | +0.42 | -0.27 | [-0.523,-0.009] |
| direct/O1_ENERGY_NO_EIA | 23 | +0.01 | -0.18 | [-0.327,-0.028] |
| direct/O2_SPREAD10 | 24 | +0.09 | -0.03 | [-0.214,+0.137] |
| direct/O3_BREAK5 | 5 | +0.65 | -0.38 | [-0.656,-0.059] |

Denetimler: 12 yürütme fikstürü; dört TF’de  540 sinyal tanımının prefix testi ve günlük/makro prefixleri; 2056 işlem defteri tek pozisyon/600 s kontrolü geçti. Yeni mumlar eklenince geçmiş sinyal değişmedi. Başlangıçta bir Python ortamındaki rolling hesabı boş valid kümesi üretti; o çıktı `INVALID_runtime_empty_discovery.json` adıyla geçersiz saklandı, sistem Python/pandas 3 ile tekrarlandı. Bu rapor geçersiz ilk çıktıyı kullanmaz.

**Durum:** O1/O2 mevcut kurallarla reddedildi. O3 ve O4 yalnız yeni temiz veriyle incelenecek araştırma adayları. O5 yön aynası kalıcı kenar göstermedi. Beş aileden hiçbirine LIVE kartı verilmedi; bot veya gölge çalışan kapı eklenmedi.

Öncelikli sonraki çalışma: petrol fiyat kaynağı geçişlerini kaynak kimliğiyle teşhis edip tek tutarlı kontratla arşivlemek; ardından bu 20 dondurulmuş varyasyonu yeni dönem gerçek spread/dolum/komisyonla en az 150 uygun çözümlenmiş olaya kadar doğrulamak. Bu raporun ölçmediği bot HOLD/WAIT/kapı atlama evreni ayrı gerçek karar logları gerektirir.

## 8. Grafikler ve kaynaklar

![Kanıt dönemlerinin ayrı yürütülmüş R çizgileri](/Users/melihcanodacioglu/Desktop/panel/research/wti_transfer_20261002/results/equity.png)

![İlk kronolojik kazanan/kaybeden EIA örnekleri](/Users/melihcanodacioglu/Desktop/panel/research/wti_transfer_20261002/results/first_win_loss.png)

Grafikler betimleyicidir. İki örnek başarı oranı kanıtı değildir; olumlu örnekler elle ayıklanmadı.

- [EIA resmi Weekly Petroleum Status Report yayın takvimi](https://www.eia.gov/petroleum/supply/weekly/schedule.php): Çarşamba 10: 30NY ve 2025/2026 tatil değişimleri. İlk Ocak 2026 belirsiz sınır haftaları takvimden çıkarıldı; M1 zaten Şubatta başlıyor.
- [Fed resmi FOMC takvimi](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm): K2 bilinen toplantı günleri.
- [CME petrol kontrat özellikleri](https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.contractSpecs.html) ve [resmi settlement yöntemi](https://www.cmegroup.com/trading/energy/files/NYMEX_Energy_Futures_Daily_Settlement_Procedure.pdf): petrol seans referansı. CFD16: 00 kapanışı CME settlement değildir.
- [Dukascopy resmi petrol CFD ürün sayfası](https://www.dukascopy.com/swiss/english/cfd/range-of-markets/cfd-commodities/): denenmiş 2025 veri kaynağı; veri indirilemedi.
- [Bailey vd., backtest overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): büyük taramalarda seçim yanlılığı.

## 9. Dosyalar ve yeniden üretim

`PROTOCOL.md`, `PROTOCOL_OIL_VARIANTS.md`; ham ve temiz indirmeler yerel `data/` içinde. Sonuç JSON/CSV’leri `results/` içinde. `aggregate.json` raporun kalite kapsamına göre hesaplanan ana ölçümleri; kapsam hücreleri ham deney JSON’larında, clock/price/fill denetimleri ayrı. Kaynaktaki Nasdaq araştırma dosyaları değiştirilmedi.

```bash
python3 research/wti_transfer_20261002/micro.py scan
python3 research/wti_transfer_20261002/micro.py detailed
python3 research/wti_transfer_20261002/daily.py
python3 research/wti_transfer_20261002/oil_variants.py
python3 research/wti_transfer_20261002/diagnostics.py
python3 research/wti_transfer_20261002/verify.py
python3 research/wti_transfer_20261002/make_report.py
```

Hesap runtimeı sistem Python 3/pandas 3; indirme ve parquet hazırlığı `.venv` ile yapıldı. `make_report.py` yalnız yerel kayıtlı veriyi okur. Veriyi yeniden indirme komutları `pull.py` içindedir; ağ ve salt okunur MT5 köprüsü gerektirir.
