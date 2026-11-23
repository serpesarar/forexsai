# SC — Soma PureGold altın stratejisi: çözümleme turu 1 (2026-11-22)

Ön kayıt ve tüm ham sonuçlar: `PROTOCOL.md` (SC-00…07). Deneme defteri: `results/deneme_defteri.jsonl`.

## Kısa sonuç
1. **Soma'nın altın kenarı örneklem içinde gerçek ve kopyalanabilir.** 2024-11 → 2026-11 arasında 448 sinyal var. 1 dk gecikmeli kopya sinyal başına +6,3 bp (P 0,99).
   5 dk gecikmede +6,0, 15 dk gecikmede +5,2 bp. Alış ve satış ikisi de artıda, 9 çeyreğin 9'u artı. Rastgele anlarda aynı trend yönüyle girmek bu dönemde 0 bp getiriyor.
2. **Önceki "kopyada zamanlama kenarı yok" hükmü (KH-03/09) sızıntılı bir plasebodan geliyordu.** O plasebo, giriş öncesi günlere haftanın
   sonradan gerçekleşen yönünü veriyordu: +14,9 bp. Dürüst yarı −5,9 bp. Düzeltilmiş kıyasla Soma'nın an seçimi ~12 bp değer katıyor.
3. **Kural henüz çıkarılamadı.** Soma, sert bir itkiden (son 60 dk'da 6,6 ATR, oynaklık günlük medyanın 1,7 katı, 60 dk aralığın tepesinde)
   sonra trend yönünde giriyor. Ama bu tarifin kendisi kârsız: aynı kural 2018–21'de −1,9 bp, rastgele trend girişiyle aynı (SC-03 X).
   Soma bu itkilerin ~1/10'unu seçiyor ve ayırıcı bilgi gözlediğimiz özelliklerde yok.
4. **Kendi stratejimiz olarak canlıya alınacak bir şey yok.** Uygulanabilir yol, Soma'yı **ileriye dönük gölgede** kopyalamak (SC-07, ölçütler donduruldu).
   Seçim yanlılığı var (Soma'yı kârlı olduğu için seçtik), bu yüzden örneklem içi sayılar bağımsız kanıt değil.

## Altyapı (SC-00) — neyi garanti ediyor
| Parça | Garanti |
|---|---|
| `sc_veri.py` | Tek veri kaynağı. Bar bütünlüğü denetimi (monoton zaman, OHLC, spread, sıçrama), bozuksa durur. Saat modeli fiyat hizalamasıyla seçilir: Soma ny7 %96,9, CWDT %89,6. Spread (yıl × saat) bp cinsinden. Kısmi indirme bar setini sessizce değiştiremez. |
| `sc_kernel.c` + `sc_sim.py` | Bid/ask ayrı. Aynı barda stop ve TP → stop. Açılış boşluğunda açılışta dolum. İz/başabaş bir sonraki bardan geçerli. Zaman çıkışı en az bir bar. C çekirdeği ile bağımsız Python ikizi 25 rastgele piyasada × 300 emirde birebir eşit. |
| `sc_ozellik.py` | Gelecek barlar bozulunca geçmiş özellik ve sinyaller değişmiyor (test). |
| `sc_degerlendir.py` | Gün bloklu bootstrap, yarılar, yıllık, tek pozisyon, stres. Her koşu deftere yazılır (bar sürümü + git hash). **2010–2017 KASA kodla kilitli:** ön kayıtlı kimlik, ortam anahtarı, kimlik başına bir kez. |
| `tests/` | 43 test (senaryo, bulanık eşitlik, nedensellik, saat ekseni, kopya sadakati kor ≥ 0,95, kasa kilidi). `.venv/bin/python -m pytest -q research/soma_cozum_20261122/tests` |

## SC-01 — kâr nereden geliyor (Soma, 448 sinyal, bp)
| Kol | Ort. | Okuma |
|---|---|---|
| Sağlayıcının kendi fiyatı | +7,97 | |
| Kopya (+1 dk, spread, komisyon) | **+6,16** (P 0,99) | sadakat kor 0,98 |
| Aynı giriş, tutuşlar karıştırılmış | +2,69 | çıkış zamanlaması sınırda (fark P 0,945) |
| Giriş +5 / +15 / +60 dk geç | +6,0 / +5,4 / +5,3 | dakika seçimi önemsiz |
| +4 sa / +1 gün / +7 gün geç | +2,2 / −0,0 / −1,4 | bilgi saatler içinde sönüyor |
| Aynı anlar, hep AL | +0,73 | "altın yükseldi" değil |
| Aynı anlar, rastgele yön | −2,23 | yön = EMA240/1440 trendi (%100 uyum) |
| Rastgele anda trend izleme (Soma'nın bacak yapısıyla) | +0,08 (2018–21: −1,75) | becerisiz trend izleme kârsız |

## Sıradaki turlar (backlog'a yazıldı)
- **SC-07 ileri gölge:** 2026-11-21 sonrası sinyaller, 5 dk gecikmeli kopya. Kart n ≥ 100 sinyalde (~5–6 ay). Kullanıcı ayda bir export alır.
  Betik hazır (`src/sc07_ileri_golge.py`).
- **SC-08 birebir tetik:** Dukascopy tick verisiyle giriş saniyesindeki koşul (seviye kırılımı / bekleyen emir / tick hızı).
  Hedef: HESAP'ın kronolojik ileri yarısında Soma girişlerini kesinlik ≥ %50 ve yakalama ≥ %50 ile bulmak. Ancak o zaman klon GELISTIRME → DOGRULAMA → KASA'ya gider.
- **SC-09 yönetim:** Soma ile CWDT ortak girişlerde farklı yönetimle +6,2'ye +3,6 getiriyor. Hangi yönetim farkı bunu yaratıyor (piramit, kademeli TP, hızlı kesme)?
- **Kasa verisi:** 2010–2017 indirmesi arka planda sürüyor (`data/duka_indir.log`). Bitince `sc_veri.bar_kur()` yıl × saat spread modeliyle yeniden kurulur.
  2018–24 maliyeti 2025'in bp profilinden alınıyordu; SC-03 sayıları yeniden koşulur.

## Deneme sayımı
SC-01 (2 hesap × 17 kol + L5 × 2 dönem), SC-03 (3 a × 3 T × 2 dönem = 18 hücre), SC-05 (2 hesap × 3 gecikme). DOGRULAMA ve KASA bu turda **hiç açılmadı.**

---

# Tur 2 — Soma giriş sistemini çok zaman dilimli çözümleme (SC-08) ve klonun kârı (SC-10) — 2026-11-22

## Soma neye göre açıyor (çözülen kısım)
Ölçüm: 7 zaman dilimi (M1…D1, mumlar Soma'nın broker sunucu saatine hizalı), her birinde EMA 9/20/50/100/200, RSI, MACD, Bollinger, Stokastik,
ADX/DI, ATR, Donchian 20/55, mum gövdesi/rengi/seri, hacim; seviyeler (önceki gün H/L/C, pivot, Asya seansı, hafta, yuvarlak sayılar); saat.
Toplam 300 özellik, hepsi nedensel. 300 bin rastgele trend dakikasıyla kıyaslandı. Motor pandas referansına eşit (test).

| Bileşen | Soma | CWDT | Rastgele |
|---|---|---|---|
| **Yön:** EMA1440 ∧ EMA240 trendi | %100 | %99 | — |
| **Yer:** fiyat H4 son 20 mum kanal sınırının ±0,25 ATR'sinde | %63 | %64 | %11 |
| **Yer:** fiyat H1 son 55 mum sınırının ±0,25 ATR'sinde | %55 | %48 | %6 |
| **Yer:** fiyat günün uç %5'inde | %77 | %74 | %10 |
| **Aşırılık:** D1 stokastik ≥ 95 | %56 | %51 | %12 |
| **Tetik:** 1 dk mumu yönde güçlü (gövde ≥ %50) | %65 | %65 | %26 |
| Saat: 09–10 ET (NY açılışı) yoğun; 09:30/10:00 ET ±10 dk | %7 | | %1,8 |

Sözle sistem: **altın günlük trend yönündeyken fiyat 3–4 günlük (H4 20 mum) ve 55 saatlik kanalın sınırına, günün tepesine/dibine geldiğinde,
güçlü bir 1 dakikalık itki mumuyla kanal sınırı kırılırken trend yönünde paket halinde (1–34 pozisyon, %66'sı aynı 2 saniyede) girer.**
Kademeli TP'lerle kâr alır, stopu taşır; fiyat kırılan kanalın içine geri dönerse birkaç dakikada küçük zararla çıkar.
Bekleyen emir yok (giriş fiyatı tek seviyede kümelenmiyor). Diğer enstrümanlarla eş zamanlılık yok, haber botu değil.

## Ne kadar çözüldü
| Yöntem | İleri yarı yakalama | İleri yarı kesinlik | CWDT |
|---|---|---|---|
| Okunabilir 8 koşullu kural | %40 | %16 | %35 / %19 |
| 300 özellikli model, dakika başı | %30 | %39 | %30 / %53 |
| 300 özellikli model, dakika kapanışı (1 dk gecikmeli klon) | **%40** | **%37** | %38 / %45 |
| aynı, sıkı eşik | %24 | %56 | %22 / %66 |
Ölçüt ≥ %50 / ≥ %50 idi → **kısmen çözüldü.** Model Soma'nın işlem yaptığı günlerin %90'ını buluyor; Soma koşulların sağlandığı anların ~1/6'sında
giriyor ve o son seçimi bar verisindeki hiçbir gösterge tam açıklamıyor (aday: tick hızı, broker fiyatı, iç sayaçlar).
Stop ve TP mesafeleri hiçbir birimde sabit değil; ilk stop export'ta yok (kapanış seviyesi taşınmış stop).

## Çözülen sistem Soma'sız kazanıyor mu (SC-10): **X**
Soma'nın kârlı döneminde, modelin görmediği ileri yarıda: 4 sa tutuş +7,3 bp (taban −1,7), 8 sa +20 bp. **2018–2021'de −2,7 bp,
rastgele trend girişinden kötü, 4 yılın 4'ü eksi.** Tarz 2024–26 altın boğasında taşıyor, başka rejimde taşımıyor. Bu, KH-12/14'ün bulgusuyla aynı yönde.
Deneme sayısı bu turda: SC-08 3 yöntem × eşik/soğuma ızgarası (~60 hücre, yalnız HESAP), SC-10 6 hücre. DOGRULAMA/KASA açılmadı.

---

# Tur 3 — son seçim tik düzeyinde mi? (SC-11) — 2026-11-23

Dukascopy saatlik tik verisi: 1.585 saat, Soma/CWDT'nin her ilk bacağı ve modelin her adayı için. Tikten kurulan mumlar Dukascopy 1m mumlarıyla
%99,995 eşit. Soma'nın saati Dukascopy'ye **saniye düzeyinde** oturuyor (çoğu ay 0/−1 sn). Giriş fiyatı ask'tan medyan ~0,1 $ sapıyor;
sağlayıcının fiyat akışı Dukascopy'ninkine çok yakın.

## Soma hangi saniyede giriyor (çözülen kısım)
| Özellik (giriş saniyesi) | Soma | Rastgele aday saniyesi | AUC |
|---|---|---|---|
| Son 30 sn trend yönünde getiri (1m ATR birimi) | 0,72 | 0,05 | 0,86 |
| Günün ucuna uzaklık (ATR) | 0,12 | 1,25 | 0,85 |
| Günün yeni ucundan bu yana | **0 sn** (%63'ü ≤ 2 sn) | 285 sn | 0,76 |
| Son 30 sn tiklerin yönde payı | %55 | %51 | 0,73 |
| Tik hızı, spread, hacim, dakika içi saniye | farksız | | ≤ 0,63 |

Sözle: **koşullar varken fiyat 30 saniyelik bir itkiyle günün yeni tepesini (satışta dibini) yaptığı saniyede girer.** Bekleyen emir değil,
"yeni uç kırılımı" piyasa emri.

## Hangi gün/pencerede gireceği: çözülemedi
Bu tetik anı, Soma'nın girmediği aday pencerelerin de **%84'ünde** oluşuyor (Soma'nın girdiği pencerelerde %87). Tik kuralı ve tik + skor modeli
ileri yarıda kesinliği hiç artırmadı (%25,5'e karşı %25,4; model %58/%27). Ön kayıtlı hüküm: **son seçim kamuya açık fiyat akışında yok.**
Kalan adaylar fiyatla ilgisiz: hesap durumu (açık pozisyon / günlük kâr hedefi / kayıp sonrası bekleme), sağlayıcının elle onayı,
haber/takvim filtresi ya da paralel çalışan başka bir sinyal.

---

# Tur 4 — daha derin: hesap durumu (SC-12) ve türetilmiş strateji ailesi (SC-13) — 2026-11-23

## SC-12: Soma'nın seçimi hesap durumundan mı? **X**
Açık pozisyon, günün kârı/zararı, son sinyalin sonucu, son 5 sinyal, haftalık sonuç, son sinyalden geçen süre: hiçbiri ayırmıyor (AUC ≤ 0,58).
Soma koşulların olduğu anların çoğunda zaten pozisyonda değil; "doluyken girmiyor" açıklaması tutmuyor. Fiyat (mum + tik) ve hesap durumu birlikte
seçimin ancak ~%40'ını açıklıyor. Kalanı büyük olasılıkla dışarıdan (elle onay / başka bir girdi).

## SC-13: çözülen girişten kendi stratejimiz
Ön kayıtlı aile: 4 giriş (model ateşlemesi iki yön / yalnız alış; modelsiz Soma tetiği iki yön / yalnız alış) × 4 çıkış (240 dk, 480 dk,
1 ATR_H1 stop + 480 dk, 1,5 ATR stop + iz süren stop + 20 sa). Keşif 2018–21, tek atış doğrulama 2022–24, kasa 2010–17 kilitli.

| Dönem | E2X3: model alış + 1 ATR_H1 stop + 8 sa (işlem başı bp) | Aynı stoplu rastgele alış | fark P | ort. R |
|---|---|---|---|---|
| 2018–21 keşif (16 hücreden tek geçen) | **+6,3** (n 629, 4/4 yıl ≥ 0) | −1,7 | 0,987 | +0,25 |
| 2022–24 doğrulama (tek atış) | **+4,7** (n 500, iki yarı +, 2022 −0,8) | +0,7 | **0,886** | +0,15 |
| 2024–26 Soma dönemi (betimleyici) | +8,2 (n 559) | −0,5 | 0,96 | +0,30 |

**Hüküm: ön kayıtlı doğrulama ölçütü (P ≥ 0,95) tutmadı → X; uygulamada C** (üç dönemin üçünde de taban üstünde, yön tutarlı ama bağımsız dönemde
anlamlılık yetmiyor). Kasa protokol gereği açılmadı. İsabet %35–42; kâr az sayıda uzun kazanandan, işlemlerin ~%56'sı stopla −0,2 % civarında kapanıyor.
Öğrenilen: Soma'nın kenarının sağlam kısmı **giriş anı seçimi + kırılım bozulunca hızlı kesmek**; zaman çıkışı ya da modelsiz kaba kural bunu taşımıyor.
