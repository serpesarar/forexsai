# Pine Motoru — TradingView topluluk scriptlerinin eş zamanlı tepkileri yön öngörüyor mu?

Tarih: 2026-10-28 · Ön kayıt: `PROTOCOL.md` (+ EK-P1…P6) · Tablolar: `SONUCLAR.md`, `results/hukum_pine.json` ·
Mum mum inceleme: `inceleme/index.html` · Önceki aşama: `../gosterge_cakisma_20261025/RAPOR.md` (GÇM, GC-01…04)

## Hüküm

**X — Kenar yok.** TradingView'deki kaynağı açık topluluk scriptleri kendi Pine motorumuzla birebir çalıştırıldı.
Ne tek başına tepkileri (A1) ne de başka bir scriptle ya da GÇM göstergesiyle çakışmaları (A2) tekrarlanabilir bir
yön öngörüsü veriyor. Bu sonuç GÇM'nin aile temsilcileriyle verdiği hükmü (GC-01 X) scriptlerin kendisiyle teyit ediyor.

## Ne yapıldı

| Aşama | Sayı |
|---|---|
| İndirilen kaynak (gösterge + strateji; kütüphaneler bağımlılık olarak) | 32.741 script, 643+ kütüphane |
| En az bir sembolde çalışıp ≥1 tepki üreten | **23.361 (%71,4)** (popülerlikten bağımsız: çeyreklerde %66–75) |
| Uygulanamayan başlıca nedenler | başka sembol verisi (DXY vb.) 2.064, desteklenmeyen grafik geçişi ~1.140, footprint/renko |
| `lookahead_on` (geleceği gören) script — aramadan çıkarıldı (EK-P5) | 1.380 |
| Tepki durumu (sembol başına) | 292–304 bin |
| Arama | 4 sembol × 1h son 12.000 bar × 6 ufuk (1…32 bar); A1 tek tepki + A2 tepki ∧ eş (script veya GÇM durumu) |
| Seçim | Keşif %60 / doğrulama %20 / kasa %20; eşik = tüm aramanın 20 dairesel kaydırma plasebosundan max\|z\| (≈ 5,2–5,4) |
| Tekrar sınaması | Doğrulamayı geçen 73 aday: önceki 12.000 bar, 2014'ten bu yana tüm geçmiş, diğer 3 sembol, 1m/5m/15m/4h/1d |

## Sonuç

**Keşif:** 4 sembolün 20 ölçülebilir ufkundan yalnız 5'inde plasebo eşiğini aşan bir aday çıktı. Hiçbiri
kasada kanıtlı olmadı.

**Kanıtlı (doğrulama z ≥ 1,645, kasa z ≥ 1,645, lift ≥ 2 puan, getiri > maliyet):**

| Sembol | Kanıtlı | Boş beklenti (q99) | Doğrulama geçen / ters | Kasa geçen / ters |
|---|---:|---:|---:|---:|
| NDX | 2 | 1,25 (4) | 12 / 21 | 10 / 24 |
| DAX | 0 | 1,25 (4) | 16 / 15 | 10 / 14 |
| XAU | 2 | 1,25 (4) | 22 / 8 | 12 / 12 |
| USOIL | 2 | 1,25 (4) | 23 / 4 | 28 / 6 |
| **Toplam** | **6** | **5** | 73 / 48 | 60 / 56 |

- Kanıtlı sayısı şans beklentisinin üstüne çıkmıyor: 6'ya karşı 5.
- USOIL'in kasa asimetrisi (28/6) script becerisi değil, yön sürüklenmesi. USOIL adaylarının %87'si AL yönünde ve
  kasa dönemi yükselişe denk geliyor. Aynı adaylar önceki 12.000 barda ort. z −0,47, tüm geçmişte −0,15 veriyor.

**Tekrarlanma (aday başına 478 ölçüm; şans beklentisi her yönde %5):**

| Pencere | Ölçüm | Aynı yön | Ters yön | Ort. z |
|---|---:|---:|---:|---:|
| Önceki 12.000 bar (1h) | 70 | 0 | 1 | −0,08 |
| 2014'ten bu yana tüm geçmiş (1h) | 68 | 4 | 3 | +0,06 |
| Diğer semboller (aynı dönem) | 196 | 12 | 8 | +0,10 |
| 1m | 62 | 5 | 5 | −0,08 |
| 5m | 67 | 7 | 1 | +0,34 |
| 15m | 72 | 6 | 1 | +0,22 |
| 4h | 70 | 8 | 2 | +0,01 |
| 1d | 69 | 2 | 3 | −0,05 |

- Aday düzeyinde ortalama tekrar z'si sıfırdan ayrışmıyor (t = 1,06; n = 73).
- Bağımsız dönemlerde ise sıfır ya da negatif: önceki 12.000 bar ve tüm geçmiş.
- 5m/15m'deki hafif artı en güçlü USOIL'de, ama orada spread 3,3–3,6 bp ve tekrar eden adayların getirisi
  spread mertebesinde. Aynı adaylar 1m ve 1d'de ters işaret veriyor.

## Pozitif kontroller — hat sızıntıyı yakalıyor

1. **`lookahead_on` doygunluğu (EK-P5).** İlk değerlendirmede ~1.600 "kanıtlı" çıktı, isabetler %73–92 aralığındaydı.
   Hepsi, üst zaman diliminin kapanmamış mumunu gören scriptlerdi. Aramadan çıkarıldılar; o koşu
   `results_lookahead_kontrol/` klasöründe saklandı.
2. **Grafiği tam bölmeyen alt zaman dilimi sızıntısı (EK-P6, motorun kendi hatası).** "MTF VWAP" NDX SAT adayı
   diğer 3 sembolde z 2,3–3,8 ile tekrar etti. Script 1h grafikte 45 dakikalık veri istiyordu. Motor alt barları
   açılış zamanına göre eşlediği için 10:00–11:00 mumu 10:30–11:15 barını, yani kapanıştan sonraki 15 dakikayı
   görüyordu. Eşleme kapanış zamanına göre düzeltildi ve etkilenen 8.059 script yeniden koşuldu. Düzeltmeden önceki
   sonuçlar `results_v3_ltf_sizinti/` klasöründe saklandı. Düzeltmeden sonra aday yok oldu, VWAP'lı adayların
   çapraz sembol z'leri −1,6…+2,0 aralığında, yani şans düzeyinde.

Her iki durumda da sızıntı hem çok güçlü hem de çapraz sembolde tekrar eden bir sinyal olarak öne çıktı. Hattın gerçek
bir bilgi avantajını gözden kaçırmayacağının kanıtı bu.

## Konsensüs çizgisi (EK-P7) — inceleme sayfalarındaki "tüm scriptler" çizgisi de yön vermiyor

İnceleme sayfalarındaki mavi çizgi C_t, her barda etkin boğa tepkisi eksi ayı tepkisinin tepki üreten script sayısına
bölümü. Ön kayıtla sınandı: C, keşif dilimindeki %90 kantilini yukarı kestiğinde AL, %10 kantilini aşağı kestiğinde SAT.
Kapsam 4 sembol × 2 yön × 6 ufuk = 48 hücre (`consensus_test.py`, `results/konsensus.csv`).

- Kanıtlı **1/48**. C'nin 20 dairesel kaydırma plasebosunda ortalama 0,05, en çok 1, p 0,05.
- Doğrulamada 2 aynı yön / 2 ters, kasada 3 aynı yön / 2 ters.
- Tek "kanıtlı" hücre (DAX h=16 AL) küçük n artefaktı (E75): doğrulamada **n=3**, kasada n=10 ve keşif z'si −1,7, yani
  ters yönde. DAX'ta 16+ barlık ufuk seans sınırına takıldığı için olay sayısı çöküyor.
- Ön kayıttaki 5m/15m/4h tekrarı bu hücre için yapılmadı. Sebep: konsensüs tüm scriptleri gerektiriyor (o zaman
  dilimlerinde ~31 bin script × ~9 saat) ve hücrenin n'i 3. Bu sapma burada açıkça yazılıdır.

Tüm scriptlerin toplu "boğa/ayı" ağırlığı da, uç değerlerinde bile, yön tahmini yapmıyor. Çizgi inceleme sayfalarında
betimleyici olarak kalır.

## Kombinasyon Madencisi (EK-P8) — 1–4'lü çakışmalar, h = 1…15 her bar ayrı: X

Kullanıcı isteğiyle: her scriptin "aktif" / "taze (≤3 bar)" durumları + karışım kovaları, 1–4'lü VE kombinasyonları
(ışın araması, havuz 1.000 / ışın 100), eşik = 10 dairesel kaydırmanın max|z| %95'i; her h = 1…15 için ayrı ayrı ilk
100 aday → 4 sembol × 15 h × 100 = **6.000 aday / pencere**; ayrıca her h için tüm-özellik LightGBM.

| pencere | aday | doğrulama geçen | kanıtlı | boş beklenti | doğr.-geçenlerin kasası (aynı/ters) | model kasa AUC (60 hücre) |
|---|---|---|---|---|---|---|
| 1h son 12k bar | 6.000 | 177 | **8** | ≈15 | 10 / 5 | 0,452 – 0,571 |
| 15m son 12k bar | 6.000 | 148 | **4** | ≈15 | 4 / 8 | 0,455 – 0,533 |

- Kanıtlı sayısı iki pencerede de boş beklentinin **altında**; doğrulamayı geçenler kasada iki yöne dağılıyor.
- USOIL adaylarının %99–100'ü AL (pencere sürüklenmesi); NDX adaylarının %79–89'u SAT — yön ağırlığı veri dönemine ait.
- Çapraz tekrar (`results_kombo/<pencere>/tekrar.csv`): 1h doğrulama-geçenleri diğer sembollerde 513 ölçümde 15 aynı /
  11 ters (ort. z +0,10), 15m'de 501 ölçümde 8/11; 15m doğrulama-geçenleri diğer sembollerde 442 ölçümde 17/18 (ort. z −0,02).
  Kanıtlıların hiçbiri başka sembolde ya da diğer TF'de anlamlı tekrar etmiyor (en iyisi USOIL-h14 15m XAU'da z 1,77,
  tek ölçüm; aynı aday 15m USOIL'in kendisinde z −0,91).
- Model: 120 hücrenin hiçbirinde kasa AUC 0,57'yi geçmiyor, ortalaması ≈0,50; en emin %10'luk AL/SAT kasa z'leri
  −1,8 … +1,6 aralığında, işaret dengeli.
- **Pozitif kontrol (E82):** ilk 15m koşusu 5.382/6.000 "kanıtlı", çapraz-sembol z ~9, AUC 0,65 verdi — 187 "HTF Candles"
  tipi `lookahead_on` script 1h'te hata verdiği için dışlama listesine girmemişti. Hat sızıntıyı yine yakaladı; liste
  tüm pencerelerin bayrakları + kaynak taraması birleşimine çevrildi (2.750 script), sızıntılı koşu
  `results_kombo_lookahead_sizinti/`'de arşivli. Düzeltilmiş 15m konsensüs: kanıtlı 0/48.

- **Tüm zaman dilimlerinde tekrar** (doğrulama-geçen 177 + 148 kombinasyon, aynı tanımla tek blok; önceki 12k bar + 1m/5m/15m/4h/1d,
  4 sembol; tüm eski tarih penceresi v2'ye bırakıldı): her pencere × aynı/diğer sembol hücresinde z ≥ 1,645 aynı/ters sayıları
  boş beklentinin (~%5 / %5) çevresinde ve iki yöne dağınık (ör. 1h→5m diğer semboller 15/37, 1h→1d 30/13, 15m→4h aynı sembol
  1/14). Kanıtlı 8 + 4 kombinasyonun 223 tekrar ölçümünde aynı yön anlamlı 7, ters 7.

Dar ufuktan (1 bar) geniş ufka (15 bar) her bar ayrı ölçüldüğünde de, 1–4 scriptin eş zamanlı tepkileri yön vermiyor.
**Duyarlılık uyarısı (EK-P9):** enjeksiyon sınaması bu madencinin 12k barda yalnız çok güçlü kenarları (≈ +9…12 p isabet,
~750+ olay) gördüğünü ve tek başına zayıf bileşenli ikilileri hiç göremediğini gösterdi; bu hüküm "bu büyüklükte kenar yok"
diye okunmalı. v2 (tüm tarih + isabet puanı + ikili tarama) ayrı bölümde.

## Kombinasyon Madencisi v2 (EK-P9) — NDX tüm 1h tarihi, yön isabeti puanı, ikili etkileşim taraması: X

Pencere `full_1h_NDX` (59.829 bar, 2016-05 → 2026-07; %60/20/20), 17.628 script koşuldu (17.508 ok, 117 zaman aşımı,
3 hata), 2.750 lookahead hariç → 303.212 özellik. Puan e = 1[r>0] − p_up(bölme × saat). Çift taraması K = 3.000 →
~4,5 milyon çift, h = 1…15 her biri; ışın araması + LightGBM aynı puanla. Kod: `kombo_madenci_v2.py`,
`kombo_enjeksiyon_v2.py`, `run_full.py`. Çıktı: `results_kombo_v2/full_1h_NDX/NDX/`.

**Önce duyarlılık (aynı pencere, sahte özellikler gerçek evrene eklendi):**

| ufuk | tek sinyal — kanıtlı yakalanan en zayıf | saf etkileşim (A, B tek başına kenarsız) |
|---|---|---|
| h=1 | +3 p @ %30 sıklık, +5 p @ %8, +12 p @ %4 | 6/6 aday, 5/6 kanıtlı (+5 p'den itibaren) |
| h=4 | +5 p @ %16, +8 p @ %16, +12 p @ %8 (+3 p hiç) | +8 p @ %8 ve +12 p: 3/3 kanıtlı; +5 p: 0/2 |
| h=12 | yalnız güçlü/sık sinyaller | 0/6 |

Yani v2, kısa ufukta EK-P8'den 2–4 kat daha zayıf kenarları ve saf ikili etkileşimi görüyor; uzun ufukta (h ≥ 12)
gücü hâlâ düşük (ızgara örtüşmesiz etiket → az bağımsız olay).

**Gerçek veri (1.500 çift + 1.500 ışın adayı):**
- Çiftler: doğrulama aynı/ters **46 / 82** (boşta simetrik), kasa 82/69; kanıtlı **3** (boş beklenti ≈ 3,75); en yüksek
  kasa z 2,36 (n=260, h=3 SAT, getiri 1,6 bp).
- Işın: kanıtlı 11, ama 6'sı h=2'de aynı çekirdek ("Volume Price Confirmation z+" ∧ "SMC 4H SELL SL dn" → AL,
  kasa z 1,7–2,7, lift 4–8 p, getiri 1,8–3,6 bp) → ~5 bağımsız aile ≈ boş. Yön sürüklenmesi: ışın SAT adayları
  doğrulamada 97/27 tutup kasada 35/27'ye (ort z −0,01) düşüyor; AL adayları doğrulamada 41/51 iken kasada 59/19 —
  dönem rejimine yaslanma, kalıcı kenar değil. 3.000 adayın çoklu sınama düzeltmesinde (Bonferroni kasa z ≈ 3,4)
  hiçbiri geçmiyor.
- LightGBM (tekli ilk 3.000 ∪ K): kasa AUC 15 ufukta **0,494 – 0,530** (enjeksiyonda aynı model h=1'de 0,635 veriyordu);
  AL/SAT ayrı kasa z en yüksek 2,37.

**Hüküm (tespit sınırıyla):** NDX 1h'te 1–15 bar ufkunda, scriptlerin tekli, ikili ve 4'e kadar çakışmalarında
**h ≤ 4 için ≈ +5 p isabet (orta sıklık) üstü kenar yok; saf ikili etkileşimde ≈ +8 p üstü yok**. Daha küçük kenarlar
bu veriyle ayırt edilemez; olsa da spread sonrası anlamsız büyüklükte (1–4 bp). h ≥ 12'de "yok" değil "ölçülemez".

### v2 — tüm semboller ve zaman dilimleri (NDX 1h/15m, DAX, XAU, USOIL 1h; tüm tarih)

Aynı akış her pencerede: tüm geçmiş, 16–17,6 bin script, ~300 bin özellik, K=3.000 ikili tarama + ışın + LightGBM, h=1…15;
önce enjeksiyon. (Çıktı: `results_kombo_v2/<pencere>/`, `enjeksiyon_*.csv`; zincir `zincir_v2.sh`.)

| pencere | bar | tespit sınırı: sahte tek sinyal yakalanan h=1/4/12 | saf etkileşim h=1/4/12 | çift kanıtlı | ışın kanıtlı | AL/SAT | model kasa AUC |
|---|---|---|---|---|---|---|---|
| NDX 1h | 59.829 | 11/6/3 (16'dan) | 5/3/0 (6'dan) | 3 | 11 (~5 aile) | 12/2 | 0,494–0,530 |
| DAX 1h | 38.485 | 11/3/0 | 4/0/0 | 9 | 10 | 18/1 | 0,491–0,550 |
| XAU 1h | 60.631 | 8/6/4 | 3/2/0 | 10 | 6 | 9/7 | 0,492–0,522 |
| USOIL 1h | 60.632 | 10/8/2 | 4/1/0 | 1 | 4 | 3/2 | 0,485–0,514 |
| NDX 15m | 79.108 | 12/8/3 | 4/1/0 | 4 | 3 | 3/4 | 0,489–0,516 |

Boş beklenti ≈ 3,75 / 1.500 aday: toplam kanıtlı 61 vs ≈ 37 beklenen; fazlalık DAX (19) ve XAU (16)'dan, ikisinde de
doğrulama→kasa sürüklenmesi var (DAX tümü AL = uzun dönem yükseliş). Kanıtlı kombinasyonlarda geçen script adlarının
pencereler arası örtüşmesi şans düzeyinde (10 çiftten toplam 7 ortak script, beklenen ≈ 3,7; aynı kombinasyon hiçbir
yerde tekrar etmiyor). Getiriler 1–22 bp (spread mertebesi). Model AUC'si en yüksek 0,550 (DAX h=14).
**Hüküm: 5 pencerenin hepsinde X** — tespit sınırı: h≤4'te ≈ +5 p tek / +8 p etkileşim, h≥12'de yetersiz güç. Not: resmî
çapraz-pencere tekrar sınaması (kanıtlı kombinasyonların diğer sembol/TF'de yeniden ölçümü) v2 formatı için ayrıca yazılmadı;
yerine script-örtüşmesi ölçüldü. DAX/XAU'nun 1h dışındaki TF'leri (15m, 5m, 4h, 1d tüm tarih) koşulmadı.

### v2 — kalan zaman dilimleri ve çapraz tekrar (2026-11-04, kullanıcı kararıyla durduruldu)

| pencere | bar | sahte tek sinyal h=1/4/12 | saf etkileşim h=1/4/12 | çift | ışın | AL/SAT | model AUC medyan |
|---|---|---|---|---|---|---|---|
| NDX 1d | 4.802 | 0/0/0 | 0/0/0 | 2 | 0 | 1/1 | 0,490 |
| DAX 1d | 2.005 | 0/0/0 | 0/0/0 | 0 | 0 | 0/0 | 0,528 |
| XAU 1d | 3.191 | 0/0/0 | 0/0/0 | 1 | 0 | 0/1 | 0,508 |
| USOIL 1d | 3.193 | 0/0/0 | 0/0/0 | 2 | 0 | 2/0 | 0,492 |
| NDX 4h | 16.175 | 5/3/0 | 2/0/0 | 4 | 7 | 5/6 | 0,508 |
| DAX 4h | 10.149 | 3/2/0 | 1/0/0 | 4 | 4 | 8/0 | 0,497 |
| XAU 4h | 16.409 | 9/1/1 | 2/0/0 | 5 | 3 | 2/6 | 0,512 |
| USOIL 4h | 16.412 | 6/0/0 | 1/0/0 | 1 | 2 | 3/0 | 0,501 |
| DAX 15m | 83.915 | 11/6/4 | 4/3/1 | 0 | 2 | 1/1 | 0,496 |
| XAU 15m | 82.464 | 11/8/3 | 4/3/1 | 6 | 28 | 32/2 | 0,511 |

Toplam (15 pencere): 43.631 aday, 132 kanıtlı; boş beklenti ≈ 109 (%0,25). XAU 15m (34) çıkarılınca 98, yani beklentinin altı.
Çapraz tekrar (`capraz_tekrar_v2.py`, |Δh|≤2): aynı koşul kümesi başka pencerede 45 kez aday çıktı, 21 aynı / 24 ters yön
(binom p=0,72); kanıtlı kümede hiç tekrar yok. XAU 15m fazlalığı: 32/34 AL, medyan kasa getirisi 1,2 bp (maliyet 0,55 bp), 74
script içinde kümelenme; kenar sayılmadı ama bağımsız sınanmadı ve E78 eksen şüphesi denetlenmedi.
**Hüküm: X.** 1d'de sahte sinyal hiç yakalanmadığı için oradaki sonuç "kenar yok" değil "ölçülemedi"dir.
Koşulmayanlar: 15m USOIL madencisi (script koşusu bitti, sahte sinyal testi yarıda kesildi) ve 5m'nin tamamı.

## Sınırlar

- Arama 1h'te yapıldı. Diğer zaman dilimleri yalnız tekrar sınamasında kullanıldı (EK-P1).
- Başka sembol verisi isteyen (~2.000), footprint ve renko tabanlı scriptler uygulanamadı. Bunlar "kenarsız"
  değil, "sınanamadı" sayılır.
- 60 sn sınırı: 995 script zaman aşımına uğradı.
- Script çıktıları sabit kurallarla ikili durumlara çevrildi (`signals.py`): plot geçişi, z uçları, renk, şekil,
  alarm ve strateji girişi. Scriptin yazarının kastettiği yorumdan farklı olabilir.
- Strateji scriptlerinin kendi TP/SL'li kâr/zararı burada ölçülmedi. Ölçülen, giriş anının yön isabetidir.

## Ne anlama geliyor

TradingView'deki gösterge ve stratejilerin eş zamanlı tepkileri, tek tek ya da ikili çakışmalarla, sızıntısız ve
bağımsız dönemde yön tahmini yapmıyor. Bu, defterdeki GC-01/02/04, HK-01…04, FC ve SM satırlarıyla aynı yönde: bu
projede ayakta kalan kenarlar gösterge değil rejim/bağlam (VIX, seans, CAPREV) ve geometri. Tüm göstergelerin birlikte
modellenmesi (GC-02) spread mertebesinde bir iz bırakıyor; yeni bir topluluk scripti bu tabloyu değiştirmiyor.
