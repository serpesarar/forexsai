# NASDAQ zaman dilimi yapılandırması — 2 dk, 3 dk, 90 dk, 210 dk (2026-11-17)

İstek: elimizdeki tüm NASDAQ mumlarından sırasıyla 2 dk, 3 dk, 1,5 saatlik ve 3,5 saatlik mum üret; zaman dilimleri
birbiriyle uyumlu, fitiller doğru olsun.

**Sonuç: diskteki 55 NASDAQ mum dosyasının tamamı sınıflandı. Üç bağımsız fiyat beslemesinin her birinde dört zaman dilimi
üretildi. 108 kontrolün 108'i geçti: 68 birebir karşılaştırma (%100, fark 0,0), 12 biçim, 18 bölüntü, 6 saat ekseni, 4 fitil bayrağı.**
Yeniden üretim: `zsh research/ndx_tf_yapilandirma_20261117/calistir.sh` (~4 dk). Çıktılar git dışında (`out/`, ham veri kuralı).
Dosya dosya hüküm listesi: [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md).

## 1. Hangi veri — üç besleme, birbirine karıştırılmadan

| Besleme | Kaynak | 1 dk kapsamı (UTC) | Üretilen |
|---|---|---|---|
| **DUKA** — Dukascopy USATECHIDXUSD BID | `nom_20261113/data/ndx_1m_v3_duka.parquet` + aynı klasördeki ham bi5'lerden sonraki günler (11-13, 11-15; `ndx_1m_v1` ile birebir) | 2018-01-02 → 2026-11-15, 2.964.406 bar | 2/3/90/210 dk, hepsi 1 dk'dan |
| **MT5** — Pepperstone NAS100 (bugünkü broker) | 4 eski M1 dosyası + 2026-11-17'de kutudan taze M1/M5/M15/M30/H1 + MT5'in kendi M5'iyle gün gün doğrulanmış 125 kopya günü | M1 2026-05-07 → 11-17 · M5 2025-06 → · M15 2022-08 → · M30 2018-05 → | 2/3 dk M1'den; 90/210 dk her mum için onu tamamen kapsayan en ince kaynaktan (M1 > M5 > M15 > M30) |
| **USTEC** — önceki broker hesabı | `1MDATA/` ve `RECOVER/mt5_ustec_1m_bars.json` (sunucu saati) | 2026-02-10 → 06-12, 119.140 bar | 2/3/90/210 dk, hepsi 1 dk'dan |

**Neden ayrı tutuldular.** Üç besleme aynı saat ekseninde: her çift için 90 ve 210 dk getiri korelasyonunun en iyi gecikmesi 0
(r = 0,977–0,9995). Ama fiyatları farklı:
- DUKA ↔ MT5: medyan −1,0 puan, IQR 3,9
- USTEC ↔ MT5: medyan −7,4 puan, IQR 22,9

İki beslemeden birleştirilmiş bir mumun fitili, iki ayrı fiyat akışının uçlarını karıştırırdı.

**Saat eksenleri:**
- MT5 ve USTEC dosyalarındaki `t` sunucu duvar saatidir (NY+7; `yeni deneme/broker_time.py`). `kaynak.server_to_utc` ile çevrildi.
- **Kanıt:** sunucu saatli ve UTC damgalı MT5 dosyaları ortak barlarda %100 birebir (6 çift). Çevrilmiş USTEC, Dukascopy'ye karşı 18 haftanın 18'inde gecikme 0.
- **Taze kutu verisi** eski dosyalarla ortak her barda birebir. Kutudaki hesap numarası değişmiş (61551449 → 61628380), fiyat beslemesi değişmemiş.

**Önemli bulgu: 2026-05-06 öncesi panel verisi NAS100 değil, USTEC.**
- Panel candle_cache'i 2026-05-06 öncesinde bugünkü NAS100 ile tek bar bile tutmuyor (hiçbir kaydırmada); USTEC json'uyla ise gün gün
  birebir. Ondan türeyen dosyalar da aynı durumda: `sr_rejection_research`, `ndx_reflex_engine`, `fcr` önbelleği, panel `candle_history` 5m'nin bir kısmı.
- Panel kaydedicisi 2026-05-06'da NAS100'e geçmiş. Bot tarafı dışa aktarımlarında (`bot_live_audit`, `sim_bot`) Haziran'a kadar USTEC günleri var.
- Yani o tarihlerden önceki "NDX" verisi başka bir CFD'nin fiyatı.
- Bazı dosyalar `time_utc` etiketli ama sunucu saatinde (`analiz_paketi`, `sr_rejection_research`, `bot_live_audit`). Bilinen
  kaymalar: candle_cache 2026-02 → 03-08 arası +60 dk (E4), 07-08/09'da ~12 dk.

## 2. Mum kuralı (üç besleme ve dört zaman dilimi için aynı)

- **Çapa: işlem günü New York 17:00'de başlar, her gün sıfırlanır.** Bu, MT5 sunucu gece yarısı (MT5'in kendi H1/H4/D1 sınırı) ve
  CME günlük arasının bitişi. DST doğru: geçiş Pazar 02:00 NY'de piyasa kapalıyken olur. Motor bunu her çalıştırmada ikinci bir
  yoldan doğrular.
- 2, 3 ve 90 dakika 1440'ı tam böler. **90 dk ızgarası 09:30 ET'ye tam düşer** (09:30–11:00 = RTH'nin ilk 90 dk'sı).
- 210 dk 1440'ı bölmez. Barlar 17:00, 20:30, 00:00, 03:30, 07:00, 10:30, 14:00 ET'de başlar; **son bar 14:00–17:00 (180 dk,
  `sure_dk=180`)**. Hiçbir mum iki güne taşmaz ve **7×90 dk = 3×210 dk** (180 dk kuyrukta 2×90 = 1×210).
- OHLC: open = penceredeki ilk barın açılışı, close = son barın kapanışı, high/low = penceredeki uç değerler. Yani her fitil, kaynak
  barlardan birinin gerçek fitili. Hacim toplanır, spread ortalaması alınır. **Eksik kaynak barı uydurulmaz.** `n_alt` / `n_nominal`
  / `tam` sütunlarıyla işaretlenir.
- Günlük kapalı pencereler ölçüldü: DUKA 16:15–18:00 ET; MT5 ve USTEC 17:00–18:00 (Cuma 16:55/16:59 kapanış → son Cuma barı
  `tam=False`, gerçek kısa seans). Yarım günler ve tatiller de `tam=False`.
- Verinin başında ve sonunda yarım kalan kovalar atılır. Veri işlem gününün son 10 dk'sında bitiyorsa o gün tam sayılır.

## 3. Fitiller — iki katman

**a) Kaynak 1 dk'da sahte tik** (`s02`; ölçüt önceden sabit: fitil > 12 × günün 1 dk aralık medyanı **ve** iki komşu barın ucunu da
aynı kadar aşıyor):
- **MT5: 0 aday. USTEC: 0 aday.**
- **DUKA: 25 aday.** 24'ü MT5'in M30 barında da görülüyor; hepsi 08:30 ET (CPI/NFP/PPI) ve 14:00 ET (FOMC) dakikaları, yani gerçek
  haber hareketi. Teyitsiz olan 1 aday 2024-09-18 FOMC; iki CFD'nin derinlik farkı.
- **Kaynak veri değiştirilmedi.**

**b) Dukascopy'nin eksik dakikası fitili kesebiliyor** (bu turda bulundu). 2026-03-23 11:05 UTC'de USTEC ve NAS100 ikisi de +%3,5
gösteriyor. Dukascopy'de 11:06–11:14 yok ve 10:50 barının tepesi 46 puan eksik. Bu yüzden her DUKA mumuna `fitil_durumu` eklendi.
Eksik dakikalı mum, aynı penceredeki MT5 (yoksa USTEC) mumuyla seviye farkı düzeltilerek kıyaslanır:

| DUKA | tam | eksik_dakika_teyitli | eksik_dakika_supheli | eksik_dakika_teyitsiz |
|---|---|---|---|---|
| 2m | 1.482.585 | 6 | 72 | 1.274 |
| 3m | 987.300 | 17 | 65 | 1.348 |
| 90m | 34.341 | 772 | **375** | 245 |
| 210m | 14.473 | 833 | **208** | 220 |

`supheli` = eksik dakika var **ve** fitil karşı beslemeden aralığının %20'sinden fazla sapıyor. Bu mumlarda Dukascopy fitili büyük
olasılıkla eksiktir. Fitilin kesin doğru olması gereken işler için bu mumlar ayıklanmalı ya da MT5 dosyası kullanılmalı.
`teyitsiz` = karşı besleme yok (2026 öncesi 2/3 dk; 90/210'da 2018-05 öncesi).

## 4. Doğrulama — `src/s04_dogrulama.py` (motorun gruplama kodunu kullanmaz)

Doğrulayıcı işlem günü sınırlarını kendisi kurar: her takvim günü için 17:00 NY'yi zoneinfo ile UTC'ye çevirir ve searchsorted
kullanır. Pencere toplamları `np.maximum/minimum.reduceat` ile yapılır. Tolerans 1e-9.

| Grup | Kontrol | DUKA | USTEC | MT5 |
|---|---|---|---|---|
| V1 biçim | OHLC ihlali, sıra/duplike, NaN, ızgara dışı, güne taşan, süre hatası, fazla alt bar | 0 (4 TF) | 0 | 0 |
| V2 kaynaktan yeniden hesap | her mumun O/H/L/C ve n_alt değeri kaynak barlardan ayrıca hesaplanır | %100 (2m 1.483.937 … 210m 15.734) | %100 | %100 (2/3 dk M1+kopya; 90/210 M1, M5, M15, M30 ayrı ayrı) |
| V2 bölüntü | her kaynak barı tam bir muma düşer | 2.964.405 / 2.964.405 | 119.140 / 119.140 | 189.152 / 189.152 |
| V3 hiyerarşi | 2m→6m = 3m→6m · 2m,3m→90m/210m = dosya · 90m×7 = 210m×3 · 1m/2m/3m/90m/210m → günlük OHLC | 10/10 %100 | 10/10 %100 | 10/10 %100 |
| V4 MT5 yerli barlar | yerli M5/M15/M30/H1 = M1'den/birbirinden kurulanı (tik hacmi dahil) · 3m→M15, 3m→M30, 2m→M30 = yerli (kopya günleri dahil) · 90m×2 = H1×3 · 210m×2 = H1×7 · 90/210'un dört kaynaktan ayrı ayrı kurulmuş sürümleri birbirine eşit | — | — | 20/20 %100 |
| V5 saat ekseni | DUKA↔MT5, DUKA↔USTEC, USTEC↔MT5, 90 ve 210 dk en iyi gecikme | 0 / 0 / 0 (6/6) | | |
| V6 fitil bayrağı | `fitil_durumu == tam` ⇔ `tam` | 4/4 tutarlı | | |

Birleşimler de ayrıca bir kontroldür. Aynı beslemenin üst üste binen her dosyası (4 eski MT5 M1, taze kutu, 125 kopya günü, iki USTEC
json, ham bi5 ↔ v1) ortak her barda birebir olmak zorunda; değilse üretim durur. Hiçbiri durmadı.

**Önceki turlarda yakalanıp düzeltilen hatalar:**
1. Kapalı saat beklenen bar sayısına giriyordu.
2. Kalın kaynakta kısmen açık dilim (M30 16:30) düşülüyordu.
3. MT5'in 16:55 kapanışı yalnız Cuma'ya aitti, her güne uygulanıyordu.
4. Doğrulayıcının takvimi kısa kesiliyordu.

## 5. Çıktılar — `research/ndx_tf_yapilandirma_20261117/out/` (git dışında; her biri `.parquet` + `.csv.gz`)

| Dosya | Bar | Kapsam (UTC açılış) | `tam` |
|---|---|---|---|
| `DUKA/NDX_DUKA_2m` | 1.483.937 | 2018-01-02 07:06 → 2026-11-15 23:58 | %99,91 |
| `DUKA/NDX_DUKA_3m` | 988.730 | 2018-01-02 07:06 → 2026-11-15 23:57 | %99,86 |
| `DUKA/NDX_DUKA_90m` | 35.733 | 2018-01-02 08:30 → 2026-11-15 22:00 | %96,10 |
| `DUKA/NDX_DUKA_210m` | 15.734 | 2018-01-02 08:30 → 2026-11-13 19:00 | %91,99 |
| `MT5/NDX_MT5_2m` | 94.645 | 2026-05-07 22:00 → 2026-11-17 20:24 | %99,85 |
| `MT5/NDX_MT5_3m` | 63.107 | 2026-05-07 22:00 → 2026-11-17 20:24 | %99,78 |
| `MT5/NDX_MT5_90m` | 34.985 | 2018-05-14 13:30 → 2026-11-17 17:30 | %99,18 |
| `MT5/NDX_MT5_210m` | 15.303 | 2018-05-14 14:30 → 2026-11-17 15:30 | %98,14 |
| `USTEC/NDX_USTEC_2m` | 59.575 | 2026-02-10 23:00 → 2026-06-12 01:20 | %99,98 |
| `USTEC/NDX_USTEC_3m` | 39.718 | 2026-02-10 23:00 → 2026-06-12 01:18 | %99,98 |
| `USTEC/NDX_USTEC_90m` | 1.384 | 2026-02-10 22:00 → 2026-06-11 22:30 | %99,13 |
| `USTEC/NDX_USTEC_210m` | 606 | 2026-02-10 22:00 → 2026-06-11 21:00 | %98,02 |

Sütunlar: `t` (UTC epoch, bar açılışı), `zaman_utc`, `zaman_ny`, `open/high/low/close`, `vol` (DUKA'da yok), `spr` (ortalama
spread, fiyat birimi; DUKA'nın 11-13 sonrası barlarında yok), `sure_dk`, `n_alt`, `n_nominal`, `tam`, `kaynak_tf`
(MT5'te `M1_kopya` = doğrulanmış kopya günü). DUKA'da ek olarak `karsi_besleme`, `fitil_sapma_orani`, `fitil_durumu`.

**Hangisini kullanmalı:**
- Bot/MT5 grafiğiyle birebir aynı mum isteniyorsa **MT5**.
- 2018'e inen 2/3 dk geçmişi isteniyorsa **DUKA** (`fitil_durumu=eksik_dakika_supheli` mumları ayıklanarak).
- USTEC yalnızca 2026-02 → 06 dönemindeki eski panel/bot kayıtlarıyla kıyas için.

## 6. Sınırlar

- MT5 2/3 dk 2026-05-07'den önceye inemez. Terminal M1'i ~100 gün tutuyor ve daha eski NAS100 1 dk kopyası diskte yok (o tarih
  öncesi kopyaların hepsi USTEC çıktı).
- DUKA 2026-11-16 ve 11-17'yi içermez: ham bi5 dosyası boş veya yok. Yeni internet indirmesi yapılmadı (istek "elimizdeki veri").
  `research/nom_20261113/src/duka_fetch.py` ile indirilirse `calistir.sh` kendiliğinden uzatır.
- Günlük (Yahoo ^NDX) ve 1 saatlik (NQ vadeli, panel 1h/4h) dosyalardan bu dört zaman dilimi matematiksel olarak kurulamaz:
  2/3 dk ancak 1 dk'dan, 90/210 dk 60'ın katı değil. Liste [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md)'de.
- 210 dk için başka bir çapa da makul (ör. 09:30 RTH). Seçilen çapa MT5/CME gün sınırı; böylece 90 dk 09:30'a oturur ve 90 ile 210
  her gün aynı sınırlarda buluşur. Değiştirmek gerekirse `tf_motor.DAY_START_H` tek yerden değişir.
