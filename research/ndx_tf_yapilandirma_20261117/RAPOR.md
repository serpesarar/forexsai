# NASDAQ zaman dilimi yapılandırması — 2 dk, 3 dk, 90 dk, 210 dk (2026-11-17)

İstek: bilgisayarda bulunan tüm NASDAQ mumlarını (farklı zaman dilimleri, yıllık 1 dk ve 30 dk dahil) alıp sırasıyla 2 dk,
3 dk, 1,5 saatlik ve 3,5 saatlik mum üret; zaman dilimleri birbiriyle uyumlu, fitiller doğru olsun.

**Sonuç:**
- Proje klasöründeki 55 ve ev dizinindeki (Masaüstü, İndirilenler, `~/dukascopy_us100` …) NASDAQ adlı dosyaların tamamı
  sınıflandı. Liste: [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md).
- **Beş bağımsız fiyat beslemesi** kendi içinde, birbirine karıştırılmadan mumlandı.
- **144 kontrolün 144'ü geçti**: 82 birebir karşılaştırma %100 (fark 0,0), 16 biçim, 26 bölüntü, 15 saat ekseni, 4 fitil
  bayrağı, 1 dışa aktarım uyumu.
- Reddedilen 1.097 kopya gününün **hepsi** son çıktılardan birinde kapsanıyor; kapsanmayan gün 0.

Yeniden üretim: `zsh research/ndx_tf_yapilandirma_20261117/calistir.sh`. Çıktılar git dışında (`out/`, ham veri kuralı).

## 1. Hangi veri — beş besleme

| Besleme | Ne | Kaynaklar | Üretilen | Kapsam |
|---|---|---|---|---|
| **DUKA** | Dukascopy USATECHIDXUSD BID (spot endeks CFD) | ana 1 dk dosyası + ham bi5 kuyruğu + **`~/Downloads/USATECHIDXUSD_M1.csv`** (16.772 ek dakika) + **`~/Downloads/USATECHIDXUSD30.csv`** (2016–17) + **Dukascopy'den yeniden indirilen 2025 resmi 1 dk mumları** (onayınla; şimdiye kadar 109 gün, +4.282 dk) | 2/3 dk: 1 dk'dan · 90/210 dk: 1 dk'dan, 2018 öncesi M30 dışa aktarımından | 2/3 dk 2018-01 → 2026-11-15 · 90/210 dk **2016-03-31** → 2026-11-15 |
| **MT5** | Pepperstone NAS100 (bot/kutu) | 4 eski M1 dosyası + 2026-11-17'de kutudan taze M1–H1 + **kutudaki MT5 yıl geçmiş dosyaları (`history/NAS100/*.hcc`, salt okuma)** + gün gün doğrulanmış 125 kopya günü | 2/3 dk: M1'den · 90/210 dk: her işlem günü o günü tam kapsayan en ince kaynaktan (M1 > M5 > M15 > M30 > geçmiş M1) | 2/3 dk **2017-06-08** → 2026-11-17 · 90/210 dk **2017-06-08** → 2026-11-16 |
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
`eksik_dakika_supheli` olur. MT5 M1 artık 2017'den geldiği için çok daha fazla mum gerçekten sınanabildi; teyitsiz 2 dk mum
1.283'ten 116'ya indi:

| DUKA | tam | teyitli | **şüpheli** | teyitsiz (karşı besleme yok) |
|---|---|---|---|---|
| 2m | 1.493.204 | 365 | 880 | 116 |
| 3m | 994.374 | 507 | 827 | 105 |
| 90m | 39.040 | 881 | **470** | 23 |
| 210m | 16.324 | 1.088 | **384** | 238 |

**Onarım (onayınla).** 2025'in tik indirmesinde işlem saatlerinde 626 saat tamamen boştu, yani indirme hatası. Dukascopy'nin
resmi 2025 1 dk mumları yeniden indiriliyor (`src/s11_duka_2025_indir.py`).
- Şu ana kadar 109 gün indi: +4.282 dakika eklendi.
- Resmi mum, ana dosyayla yalnız 6 dakikada ayrıştı (‰0,05). Ayrışma ‰1'i aşarsa üretim durur.
- Dukascopy sunucusu sık istekte 503 dönüyor; indirici 15 dk bekleyerek sürüyor. Bitince `calistir.sh` yeni günleri kendiliğinden
  katar.

**Onarılamayanlar.** Kalan şüpheli mumların önemli kısmı Dukascopy'nin o dakikalarda gerçekten hiç kaydı olmadığı anlara düşüyor.
Örnek: 2026-03-23 11:06–11:15 UTC ham dosyada düz, sıfır hacimli barlar. Hiçbir indirme bunları onarmaz. **Fitilin kesin doğru
olması gereken işlerde bu mumları ayıklayın ya da aynı pencerenin MT5/EET30 mumunu kullanın.** Bu pencerelerin hepsinde 2017
sonrası için MT5 mumu var.

## 4. Doğrulama — `src/s04_dogrulama.py` (motorun gruplama kodunu kullanmaz)

Doğrulayıcı işlem günü sınırlarını kendisi kurar (zoneinfo + searchsorted) ve pencereleri `reduceat` ile toplar. Tolerans 1e-9.

| Grup | Kontrol | Sonuç |
|---|---|---|
| V1 biçim | OHLC ihlali, sıra/duplike, NaN, ızgara dışı, güne taşan, süre hatası, fazla alt bar — 5 besleme × TF | 16/16, hepsi 0 |
| V2 kaynaktan yeniden hesap | her mumun O/H/L/C ve n_alt değeri, kendi kaynağından (DUKA 1m ve M30 dışa aktarımı; MT5 M1/geçmiş M1/M5/M15/M30; EET30 30m; NQ 5m) ayrıca hesaplanır | %100 |
| V2 bölüntü | her kaynak barı tam bir muma düşer | 26/26 |
| V3 hiyerarşi | 2m→6m = 3m→6m · 2m,3m→90m/210m = dosya · 90m×7 = 210m×3 · her TF → günlük OHLC = kaynak→gün | %100 (DUKA, USTEC, MT5 10'ar; EET30, NQ 3'er) |
| V4 MT5 yerli barlar | yerli M5/M15/M30/H1 = M1'den/birbirinden kurulanı (tik hacmi dahil) · 3m→M15/M30, 2m→M30 = yerli (2017+ geçmiş M1 günleri dahil) · 90m×2 = H1×3 · 210m×2 = H1×7 · 90/210'un dört kaynaktan ayrı ayrı kurulmuş sürümleri birbirine eşit | 20/20 %100 |
| V5 saat ekseni | 15 besleme çifti/TF + DUKA'nın 11-13/15 kuyruğu ↔ MT5 M1 (r 0,9975) | hepsinde en iyi gecikme 0 |
| V6 fitil bayrağı | `fitil_durumu == tam` ⇔ `tam` | 4/4 |
| V7 dışa aktarım | Dukascopy M30 dışa aktarımı ↔ 1m→30m | %99,955 |

Aynı beslemenin üst üste binen her dosyası ortak her barda birebir olmak zorunda; değilse üretim durur. Buna 4 MT5 M1 dosyası,
taze kutu verisi, MT5 geçmiş M1'i, 125 kopya günü, iki USTEC json, ham bi5 ↔ v1 ve Dukascopy M1 dışa aktarımı ↔ ana 1 dk dahil.
Hiçbiri durmadı. MT5 90/210 dk'da her işlem günü tek kaynaktan gelir. Bu kural, 2018-05-14 sınırında 90 ile 210'un farklı
kaynaktan gelip bir 630 dk bloğu bozduğu görülünce eklendi.

**MT5 geçmiş dosyaları (`src/s12_hcc.py`).** Kutudaki `bases/Pepperstone-Demo/history/NAS100/<YIL>.hcc` dosyaları salt okunarak
ayrıştırıldı (MqlRates, 60 bayt). Her gün, o gün için en ince yerli MT5 barıyla (M5 → M15 → M30 → H1) birebir sınandı. Ek koşul:
gün gerçekten M1 olmalı (medyan bar aralığı 60 sn, dakika sayısı ≥ yerli kapsamın %80'i). Bu koşul gerekliydi, çünkü 2009–2016
dosyaları M1 değil H1/D1 kaydı tutuyor ve bunlar yerli H1 ile kendiliğinden eşleşir.

| Yıl | Kabul edilen gün |
|---|---|
| 2017 | 131 / 257 (112 gün M1 değil) |
| 2018 | 249 / 257 |
| 2019–2025 | 1.805 / 1.808 |
| 2026 | dosya terminal kilidinde, okunamadı |

## 5. Çıktılar — `research/ndx_tf_yapilandirma_20261117/out/<BESLEME>/NDX_<BESLEME>_<tf>m.{parquet,csv.gz}` (git dışı)

| Besleme | 2m | 3m | 90m | 210m |
|---|---|---|---|---|
| DUKA | 1.494.565 (2018-01 → 2026-11-15) | 995.813 | 40.414 (2016-03 → 2026-11-15) | 18.034 |
| MT5 | 1.580.500 (**2017-06-08** → 2026-11-17) | 1.054.061 | 38.348 (**2017-06-08** → 2026-11-16) | 16.809 |
| USTEC | 59.575 (2026-02-10 → 06-12) | 39.718 | 1.384 | 606 |
| EET30 | — | — | 33.299 (2016-11 → 2025-10) | 14.586 |
| NQ | — | — | 18.627 (2019-08 → 2024-08) | 8.234 |

Sütunlar: `t` (UTC epoch, bar açılışı), `zaman_utc`, `zaman_ny`, `open/high/low/close`, `vol`, `spr`, `sure_dk`, `n_alt`,
`n_nominal`, `tam`, `kaynak_tf`. `kaynak_tf` değerleri: MT5'te `M1`/`M1_gecmis`/`M1_kopya`/`M5`/`M15`/`M30`; DUKA'da
`1m`/`M30_disaktarim`. DUKA'da ek olarak `karsi_besleme`, `fitil_sapma_orani`, `fitil_durumu`.

**Hangisini kullanmalı:**
- Bot/MT5 grafiğiyle birebir aynısı ve doğrulanmış fitil için **MT5** (2017-06 →).
- Daha eski 2/3 dk için **DUKA** (2018-01 →; şüpheli fitilleri ayıklayarak).
- 2016–2017 için 90/210 dk: **DUKA** (M30 dışa aktarımından) veya **EET30**.
- Vadeli işlem fiyatı gereken iş için **NQ** (seviye geriye ayarlı).

## 6. Bilgisayardaki tüm NASDAQ dosyalarının hükmü (`s05`, `s09`, `s10`, `s12` → [DOSYA_HUKUMLERI.md](DOSYA_HUKUMLERI.md))

**Proje içi (55 dosya).** Her dosya bir beslemenin ana kaynağı ya da gün gün sınanmış kopyası. Reddedilen 1.097 kopya gününün
hepsi son çıktılardan birinde kapsanıyor; kapsanmayan gün yok:

| Kapsam | Gün |
|---|---|
| MT5 1 dk birleşiminde tam | 678 |
| USTEC'te birebir | 360 |
| USTEC + MT5 90/210 | 56 |
| MT5 90/210 yerli barlardan | 3 (panel `candle_history` 5 dk kopyası) |

**Ev dizini (304 dosya):**

| Hüküm | Dosya |
|---|---|
| mum değil (model, sinyal, olay, rapor, temel veri, OHLC'siz) | 172 |
| 2/3/90/210 dk'ya türetilemez (günlük, haftalık, aylık, 1 sa, 4 sa) | 75 |
| Dukascopy kopyası/dışa aktarımı | 40 |
| Dukascopy'den çok-TF geniş birleşik tablo | 5 |
| NQ_5Years türevi | 4 |
| projedeki bir dosyanın md5 ikizi | 3 |
| arşiv | 3 |
| **ana kaynak: EET30, NQ** | 2 |

**Kutu (MT5 terminali):** `history/NAS100/2008…2025.hcc` ayrıştırıldı (yukarıda); 2026.hcc kilitli.

## 7. Sınırlar (veri yok ya da matematiksel olarak imkânsız — üretim hatası değil)

- **EET30 (30 dk) ve NQ (5 dk) dosyalarından 2/3 dk mum kurulamaz.** 2 ve 3 dakikalık mum ancak 1 dakikalık veriden kurulur; 30 dk
  ya da 5 dk mumun içindeki dakika hareketi dosyada yok. Uydurmak, fitillerin doğruluğunu bozardı. Bu iki besleme yalnız 90/210 dk
  verir. Aynı dönemin 2/3 dk'sı MT5 (2017-06 →) ve DUKA (2018-01 →) dosyalarında var.
- **MT5 NAS100 1 dk, 2017-06 öncesinde diskte yok.** Kutudaki dosyalar o yıllarda yalnız H1/D1 tutuyor. **2026-01 → 05-06 arası
  NAS100 1 dk ise 2026.hcc'de duruyor ama terminal dosyayı kilitli tutuyor.** Bu dönemin 90/210 dk'sı MT5 yerli M5/M15/M30'dan,
  2/3 dk'sı DUKA'dan var. Kilitli dosya terminal kapatılarak okunabilir; canlı bot terminali olduğu için kapatmadım.
- **DUKA 2026-11-16/17** ham dosyada boş.
- **Dukascopy 2025 yeniden indirmesi** sunucu engeli yüzünden henüz tamamlanmadı (109/~310 gün). Kalan günler indikçe
  `calistir.sh` onları katar.
- **Kalibrasyonda reddedilen haftalar** (EET30 %8, NQ %5,4) kullanılmadı; liste `results/s08_ek_besleme.json`.
