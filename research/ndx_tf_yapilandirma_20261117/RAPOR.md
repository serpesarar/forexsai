# NASDAQ zaman dilimi yapılandırması — 2 dk, 3 dk, 90 dk, 210 dk (2026-11-17)

İstek: bilgisayarda bulunan tüm NASDAQ mumlarını (farklı zaman dilimleri, yıllık 1 dk ve 30 dk dahil) alıp sırasıyla 2 dk,
3 dk, 1,5 saatlik ve 3,5 saatlik mum üret; zaman dilimleri birbiriyle uyumlu, fitiller doğru olsun.

**Sonuç:**
- Proje klasöründeki 55 ve ev dizinindeki (Masaüstü, İndirilenler, `~/dukascopy_us100` …) NASDAQ adlı dosyaların tamamı
  sınıflandı. Liste: [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md).
- **Beş bağımsız fiyat beslemesi** kendi içinde, birbirine karıştırılmadan mumlandı.
- **140 kontrolün 140'ı geçti**: 80 birebir karşılaştırma %100 (fark 0,0), 16 biçim, 24 bölüntü, 15 saat ekseni, 4 fitil
  bayrağı, 1 dışa aktarım uyumu.
- Reddedilen 1.097 kopya gününün **hepsi** son çıktılardan birinde kapsanıyor; kapsanmayan gün 0.

Yeniden üretim: `zsh research/ndx_tf_yapilandirma_20261117/calistir.sh`. Çıktılar git dışında (`out/`, ham veri kuralı).

## 1. Hangi veri — beş besleme

| Besleme | Ne | Kaynaklar | Üretilen | Kapsam |
|---|---|---|---|---|
| **DUKA** | Dukascopy USATECHIDXUSD BID (spot endeks CFD) | ana 1 dk dosyası + ham bi5 kuyruğu + **`~/Downloads/USATECHIDXUSD_M1.csv`** (16.772 ek dakika) + **`~/Downloads/USATECHIDXUSD30.csv`** (2016–17) | 2/3 dk: 1 dk'dan · 90/210 dk: 1 dk'dan, 2018 öncesi M30 dışa aktarımından | 2/3 dk 2018-01 → 2026-11-15 · 90/210 dk **2016-03-31** → 2026-11-15 |
| **MT5** | Pepperstone NAS100 (bot/kutu) | 4 eski M1 dosyası + 2026-11-17'de kutudan taze M1–H1 + gün gün doğrulanmış 125 kopya günü | 2/3 dk: M1'den · 90/210 dk: en ince tam kaynaktan (M1 > M5 > M15 > M30) | 2/3 dk 2026-05-07 → 11-17 · 90/210 dk 2018-05 → 2026-11-17 |
| **USTEC** | önceki broker hesabı | `1MDATA/` + `RECOVER/mt5_ustec_1m_bars.json` | 2/3/90/210 dk 1 dk'dan | 2026-02-10 → 06-12 |
| **EET30** | başka bir MT broker'ı, 30 dk | **`~/Desktop/Trading Projeleri/nasdaq/nasdaq100_30min_full.csv`** | 90/210 dk (2/3 dk 30 dk'dan kurulamaz) | 2016-11-15 → 2025-10-01 |
| **NQ** | NQ vadeli (CME), 5 dk, geriye ayarlı sürekli seri | **`~/Desktop/Trading Projeleri/nasdaq/NQ_5Years_8_11_2024.csv`** | 90/210 dk | 2019-08-11 → 2024-08-09 |

**Neden ayrı tutuldular.** Beş besleme aynı saat ekseninde: her çiftte 90/210 dk getiri korelasyonunun en iyi gecikmesi 0, r
0,95–0,9995. Ama fiyatları farklı:

| Çift | Medyan fark (puan) | IQR (puan) |
|---|---|---|
| DUKA ↔ MT5 | −1,0 | 3,9 |
| DUKA ↔ EET30 | −4,0 | 8,2 |
| USTEC ↔ MT5 | −7,4 | 22,9 |
| NQ ↔ CFD | ≈ +1.393 | — |

NQ'daki büyük fark, vade geçişlerinde geriye dönük ayarlamadan gelir. Birleştirilmiş bir mumun fitili iki ayrı fiyat
akışının uçlarını karıştırırdı.

**Saat eksenleri (hepsi ölçülerek kuruldu):**
- **MT5 ve USTEC** dosyalarında `t` sunucu saati (NY+7). Kanıt: sunucu saatli ve UTC damgalı MT5 dosyaları ortak barlarda %100
  birebir. Taze kutu verisi de eski dosyalarla birebir; hesap numarası değişmiş, besleme değişmemiş.
- **Dukascopy dışa aktarımları** UTC. M1 dışa aktarımı ana 1 dk ile ortak dakikalarda birebir aynı (birleşim bunu dayatır). M30
  dışa aktarımı, 1 dk'dan kurulan 30 dk ile 86.755 barda %99,955 aynı (2 ondalık yuvarlama payı).
- **EET30** Europe/Athens (UTC+2/+3, AB yaz saati), bar açılışı. **NQ** bar kapanışıyla etiketli ve saat dilimi dosya içinde
  değişiyor: 2019–22 Berlin / sabit UTC+1, 2022-12'den sonra New York.
- Bu iki dosya **hafta hafta** kalibre edildi. Kabul ölçütü önceden sabitti: referansa karşı en iyi gecikme 0, r(0) ≥ 0,90,
  r(0) − r(±1) ≥ 0,30. Veriyi gördükten sonra bir koşul eklendi: çevrilmiş saatte hafta sonuna düşen bar en çok 3 ve bunlar
  atılır. Nedeni, NQ 2021-10-31 ve 2022-03-13'te AB/ABD yaz saati ayrışma haftalarının korelasyonda geçip bir saat kayık
  kalmasıydı.
  - EET30: 463 haftanın 425'i, barların %92'si.
  - NQ: 259 haftanın 245'i, barların %94,6'sı.
  - Reddedilen haftaların hepsinde gecikme 0, ama r < 0,90 (2017'nin ince verisi, Noel haftaları, 2025-08).

**Bulgular (veri sağlığı):**
- **2026-05-06 öncesi panel candle_cache'i NAS100 değil, USTEC.** Ondan türeyen dosyalar da öyle. Bazı dosyalar `time_utc`
  etiketli ama aslında sunucu saatinde (`analiz_paketi`, `sr_rejection_research`, `bot_live_audit`).
- **Dukascopy'nin kendi verisinde boşluk var.** 2025 tik indirmesinde (`~/dukascopy_us100`) bazı aylar eksik saatli (Temmuz'da
  744 saatin 583'ü). Bu boşlukların 2025-06 → 10 kısmını M1 dışa aktarımı doldurdu. Bazı haber anlarında ise Dukascopy gerçekten
  donmuş: 2026-03-23 11:06–11:15 UTC ham dosyada düz, sıfır hacimli barlar. Bu fitil Dukascopy içinden onarılamaz.

## 2. Mum kuralı (beş besleme, dört zaman dilimi için aynı)

- **Çapa: işlem günü New York 17:00'de başlar ve her gün sıfırlanır.** Bu, MT5 sunucu gece yarısı (MT5'in kendi H1/H4/D1 sınırı)
  ve CME günlük arasının bitişi. DST doğru: geçiş Pazar 02:00 NY'de piyasa kapalıyken olur; motor bunu her çalıştırmada ikinci
  bir yoldan doğrular.
- 2, 3 ve 90 dk 1440'ı tam böler. **90 dk ızgarası 09:30 ET'ye tam düşer.**
- 210 dk barları 17:00, 20:30, 00:00, 03:30, 07:00, 10:30 ve 14:00 ET'de başlar. **Son bar 14:00–17:00'dir (180 dk,
  `sure_dk=180`).** Böylece hiçbir mum iki güne taşmaz ve **7×90 dk = 3×210 dk** olur.
- OHLC: open = penceredeki ilk barın açılışı, close = son barın kapanışı, high/low = penceredeki uç değerler. Her fitil, kaynak
  barlardan birinin gerçek fitilidir. Eksik kaynak barı uydurulmaz; `n_alt` / `n_nominal` / `tam` sütunlarıyla işaretlenir.
- Günlük kapalı pencereler ölçüldü: DUKA 16:15–18:00 ET, diğerleri 17:00–18:00. Kapalı pencerede gerçek bir kaynak barı varsa
  beklenen sayıya eklenir ve silinmez. Tek vaka: Dukascopy M30 2017-03-13 16:30 ET, ABD/AB yaz saati ayrışma günü.

## 3. Fitiller

**a) Kaynakta sahte tik:** MT5 0, USTEC 0. Dukascopy'de 25 aday var; 24'ü MT5'te de görülüyor ve hepsi CPI/NFP/FOMC dakikası,
yani gerçek haber hareketi. Hiçbir veri değiştirilmedi.

**b) Dukascopy'nin eksik dakikası.** Her DUKA mumuna `fitil_durumu` sütunu eklendi. Eksik dakikalı mum, aynı penceredeki MT5 →
USTEC → EET30 → NQ mumuyla (ilk bulunan) seviye farkı düzeltilerek kıyaslanır. Sapma karşı mumun aralığının %20'sini aşıyorsa
`eksik_dakika_supheli` olur:

| DUKA | tam | teyitli | **şüpheli** | teyitsiz (karşı besleme yok) |
|---|---|---|---|---|
| 2m | 1.490.972 | 6 | 72 | 1.283 |
| 3m | 992.886 | 17 | 65 | 1.358 |
| 90m | 38.966 | 975 | **353** | 87 |
| 210m | 16.284 | 1.100 | **286** | 358 |

Önceki turda 90 dk'da 245 teyitsiz mum vardı; EET30 ve NQ karşılaştırmaya girince 87'ye indi. Şüpheli mumlar Dukascopy'nin o
dakikalarda hiç verisi olmadığını gösterir; bu, besleme içinden onarılamaz. **Fitilin kesin doğru olması gereken işlerde bu
mumları ayıklayın ya da aynı pencerenin MT5/EET30 mumunu kullanın.**

## 4. Doğrulama — `src/s04_dogrulama.py` (motorun gruplama kodunu kullanmaz)

Doğrulayıcı işlem günü sınırlarını kendisi kurar (zoneinfo + searchsorted) ve pencereleri `reduceat` ile toplar. Tolerans 1e-9.

| Grup | Kontrol | Sonuç |
|---|---|---|
| V1 biçim | OHLC ihlali, sıra/duplike, NaN, ızgara dışı, güne taşan, süre hatası, fazla alt bar — 5 besleme × TF | 16/16, hepsi 0 |
| V2 kaynaktan yeniden hesap | her mumun O/H/L/C ve n_alt değeri, kendi kaynağından (DUKA 1m ve M30 dışa aktarımı; MT5 M1/M5/M15/M30; EET30 30m; NQ 5m) ayrıca hesaplanır | %100 |
| V2 bölüntü | her kaynak barı tam bir muma düşer | 24/24 |
| V3 hiyerarşi | 2m→6m = 3m→6m · 2m,3m→90m/210m = dosya · 90m×7 = 210m×3 · her TF → günlük OHLC = kaynak→gün | %100 (DUKA, USTEC, MT5 10'ar; EET30, NQ 3'er) |
| V4 MT5 yerli barlar | yerli M5/M15/M30/H1 = M1'den/birbirinden kurulanı (tik hacmi dahil) · 3m→M15/M30, 2m→M30 = yerli · 90m×2 = H1×3 · 210m×2 = H1×7 · 90/210'un dört kaynaktan ayrı ayrı kurulmuş sürümleri birbirine eşit | 20/20 %100 |
| V5 saat ekseni | 15 besleme çifti/TF + DUKA'nın 11-13/15 kuyruğu ↔ MT5 M1 (r 0,9975) | hepsinde en iyi gecikme 0 |
| V6 fitil bayrağı | `fitil_durumu == tam` ⇔ `tam` | 4/4 |
| V7 dışa aktarım | Dukascopy M30 dışa aktarımı ↔ 1m→30m | %99,955 (39 farklı barın 9'unda dışa aktarımın fitili daha uzun) |

Aynı beslemenin üst üste binen her dosyası ortak her barda birebir olmak zorunda; değilse üretim durur. Buna 4 MT5 M1 dosyası,
taze kutu verisi, 125 kopya günü, iki USTEC json, ham bi5 ↔ v1 ve Dukascopy M1 dışa aktarımı ↔ ana 1 dk dahil. Hiçbiri durmadı.

## 5. Çıktılar — `research/ndx_tf_yapilandirma_20261117/out/<BESLEME>/NDX_<BESLEME>_<tf>m.{parquet,csv.gz}` (git dışı)

| Besleme | 2m | 3m | 90m | 210m |
|---|---|---|---|---|
| DUKA | 1.492.333 (2018-01 → 2026-11-15) | 994.326 | 40.381 (2016-03 → 2026-11-15) | 18.028 |
| MT5 | 94.645 (2026-05-07 → 11-17) | 63.107 | 34.985 (2018-05 → 2026-11-17) | 15.303 |
| USTEC | 59.575 (2026-02-10 → 06-12) | 39.718 | 1.384 | 606 |
| EET30 | — | — | 33.299 (2016-11 → 2025-10) | 14.586 |
| NQ | — | — | 18.627 (2019-08 → 2024-08) | 8.234 |

Sütunlar: `t` (UTC epoch, bar açılışı), `zaman_utc`, `zaman_ny`, `open/high/low/close`, `vol`, `spr`, `sure_dk`, `n_alt`,
`n_nominal`, `tam`, `kaynak_tf`. `kaynak_tf` değerleri: MT5'te `M1`/`M1_kopya`/`M5`/`M15`/`M30`; DUKA'da `1m`/`M30_disaktarim`.
DUKA'da ek olarak `karsi_besleme`, `fitil_sapma_orani`, `fitil_durumu`.

**Hangisini kullanmalı:**
- Bot/MT5 grafiğiyle birebir aynısı için **MT5**.
- En uzun 2/3 dk geçmişi için **DUKA** (şüpheli fitilleri ayıklayarak).
- 2016–2018 için 90/210 dk: **DUKA** (M30 dışa aktarımından) veya **EET30**.
- Vadeli işlem fiyatı gereken iş için **NQ** (seviye geriye ayarlı).

## 6. Bilgisayardaki tüm NASDAQ dosyalarının hükmü (`s05`, `s09`, `s10` → [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md))

**Proje içi (55 dosya).** Her dosya bir beslemenin ana kaynağı ya da gün gün sınanmış kopyası. Reddedilen 1.097 kopya gününün
hepsi son çıktılardan birinde kapsanıyor; kapsanmayan gün yok:

| Kapsam | Gün |
|---|---|
| MT5 1 dk birleşiminde tam | 534 |
| USTEC'te birebir | 360 |
| USTEC + MT5 90/210 | 56 |
| MT5 90/210 yerli barlardan | 147 (panel `candle_history` 5/15/30 dk kopyaları; bunlardan zaten 2/3 dk kurulamaz) |

**Ev dizini (304 dosya):**

| Hüküm | Dosya |
|---|---|
| mum değil (model, sinyal, olay, rapor, temel veri, OHLC'siz) | 172 |
| 2/3/90/210 dk'ya türetilemez (günlük, haftalık, aylık, 1 sa, 4 sa) | 75 |
| Dukascopy kopyası/dışa aktarımı (M1, M5, M15, M30; 2 ve 3 ondalık sürümler) | 40 |
| Dukascopy'den çok-TF geniş birleşik tablo | 5 |
| NQ_5Years türevi (yeniden örneklenmiş) | 4 |
| projedeki bir dosyanın md5 ikizi | 3 |
| arşiv (zip içeriği açık kopya olarak ayrıca sınandı) | 3 |
| **ana kaynak: EET30, NQ** | 2 |

**Kullanılmamış yeni gün taşıyan dosya kalmadı.** Bu turda ev dizininden alınıp üretime giren veriler:
- Dukascopy M1 dışa aktarımı: +16.772 dk.
- Dukascopy M30 dışa aktarımı: 2016-03 → 2018-01.
- EET30 30 dk: 2016-11 → 2025-10.
- NQ 5 dk: 2019-08 → 2024-08.
- 2025 tikleri: ana 2025 verisiyle birebir aynı çıktı, ek dakika yok.

## 7. Sınırlar (veri yok — üretim hatası değil)

- **2/3 dk** ancak 1 dk veriden kurulur. Diskteki 1 dk NASDAQ verisinin tamamı kullanıldı: DUKA 2018-01 →, MT5 2026-05-07 →,
  USTEC 2026-02 → 06. Daha eski 1 dk yok. MT5 terminali M1 ve M30'u 100.000 barla sınırlı tutuyor (kutudaki "grafikteki azami
  bar" ayarı). Bu ayar artırılırsa sunucudan daha derin geçmiş çekilebilir; canlı bot terminali olduğu için ayara dokunmadım.
- **DUKA 2026-11-16/17 yok.** Ham dosya boş. Elimizdeki veriyle sınırlı kaldığım için internetten indirme yapmadım.
- **Kalibrasyonda reddedilen haftalar** (EET30 %8, NQ %5,4) kullanılmadı; liste `results/s08_ek_besleme.json`.
- **Günlük/haftalık/aylık ve 1/4 sa dosyalardan** bu dört zaman dilimi matematiksel olarak kurulamaz: 2/3 dk ancak 1 dk'dan,
  90/210 dk ancak 30'un bölenlerinden (1, 2, 3, 5, 6, 10, 15, 30 dk) kurulur. Dukascopy H1 dışa aktarımı 2013'e kadar iniyor
  ama 1 saatten 90 dk kurulamaz.
