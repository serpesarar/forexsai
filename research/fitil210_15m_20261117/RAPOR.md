# NASDAQ 3,5 saatlik alt fitil ≥ %0,50 → dört işlem kuralı — rapor (son, 2026-11-17)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md) + EK-1…EK-4. Kod: `src/`, yeniden üretim `zsh calistir.sh` (~30 sn). Sonuçlar `results/`
(git dışı).

Doğrulama sayfaları:
- [results/grafikler.html](results/grafikler.html): her grafikte üstte 3,5 saatlik mumlar, altta 15 dk çizgileri ve işlemler.
  Dukascopy, MT5 3,5 sa ve MT5 H4 mumlarının alt/üst fitil ve gövde yüzdeleri yazılı. İşaretlediğiniz 4 eski örnek elenme
  nedenleriyle birlikte.
- [results/galeri.html](results/galeri.html): rastgele 24 olay.
- `results/olaylar_ANA.csv`: 232 olayın tam listesi (üç mumun ölçüleri).

## Sonuç

Tespit sizin düzeltmelerinize göre baştan kuruldu ve **tüm arama yeniden yapıldı**. İşaretlediğiniz dört örneğin dördü artık kural
dışında; sizin 17 Kasım örneğiniz içeride.

| Örnek | Gözleminiz | Ölçüm | Sonuç |
|---|---|---|---|
| 1 (23.05.2022) | büyük fitil yukarıda | sizin grafiğinizdeki H4 mumu (NY 09:00–13:00): **üst fitil %0,57**, alt %0,94 | **elendi** |
| 2 (07.12.2022) | büyük fitil yukarıda | 3,5 sa mumunda **üst fitil %0,66**, alt %0,63 | **elendi** |
| 4 (08.04.2026) | fitil yeterince uzun değil | MT5 mumunda **alt fitil %0,49** (< %0,50) | **elendi** |
| 5 (12.07.2022) | fitil yeterince uzun değil | alt fitil %0,54 ama **gövde %1,08**: fitil mumun küçük parçası | **elendi** |
| 17 Kas 2026 | geçerli | 3,5 sa alt %1,14 / üst %0,03 / gövde %0,66 · H4 alt %1,15 / üst %0,01 | **kuralda** |

**Tespit kuralı (sizin seçiminiz — "görünüşe göre"; seçenekler yalnız 3,5 sa eşiği / eşik + gövde / görünüşe göre idi):**
1. **3,5 saatlik mum** (Dukascopy ve sizin MT5 mumunuz):
   - alt fitil ≥ fiyatın %0,50'si,
   - üst fitil ≤ alt fitilin yarısı (büyük fitil yukarıda olmasın),
   - alt fitil ≥ gövde (fitil mumun en uzun parçası; kısa görünmesin).
2. **Fitilin dibini içeren MT5 H4 mumu.** MT5'te 3,5 saat yok, siz H4'e bakıyorsunuz; orada da alt fitil ≥ %0,50 ve üst fitil ≤ alt
   fitilin yarısı olmalı. H4'te gövde şartı yok, çünkü sizin 17 Kasım örneğinizi eliyordu.

**Doğrulama:**
- 2018-07 → 2026-11 arasında **232 olay**. 232'sinin hepsi üç mumda kuralın her koşulunu sağlıyor; en küçük alt fitil %0,50 / %0,503
  / %0,503.
- Sentetik birim testleri geçiyor: üst fitili büyük mum eleniyor, gövdesi büyük mum eleniyor, broker teyidi ve H4 teyidi olay
  düşürüyor, eksik pencerede kurulum açılmıyor.
- 17 Kasım mumunun kuralda kaldığı kodda ayrıca denetleniyor.
- Bütün SVG grafikleri XML olarak denetlendi.

**İşlem sonuçları: canlıya alınacak kural yok.** Önceden yazılmış ölçütü (§5: iki dönemde artı, TEST P ≥ %90, plasebodan iyi, MT5'te
artı, spread ×1,5'te artı) hiçbiri geçmiyor.

| | Dukascopy (232 olay) | KEŞİF 18–21 / TEST 21–26 | MT5 bağımsız (113 olay) | Hüküm |
|---|---|---|---|---|
| S1 AL, TP %0,30, 30 dk | +0,02 bp | −0,09 / +0,13 (P %53) | +3,1 bp (P %91) | C — ölçütü geçmiyor |
| S2 AL, TP %0,18, SL gövde altı | +0,108R (n 92) | +0,079 / +0,148 (P %81) | −0,007R | C — MT5'te yok |
| S3 SAT %48 üstü | −0,308R | +0,059 / **−0,717** | −0,357R | X |
| S4 SAT %50 fitil reddi | −0,130R | −0,022 / −0,315 | −0,379R | X |

## 1. Ayrıntı — Dukascopy 1 dk

| | n (kurulum) | ort. | medyan | isabet | spread ×1,5 | en iyi 5 hariç | plasebo farkı (P) |
|---|---|---|---|---|---|---|---|
| S1 (bp) | 232 | +0,02 | +2,0 | %51,7 | −1,04 | −0,64 | +0,47 (0,58) |
| S2 (R) | 92 (52) | +0,108 | +0,25 | %57,6 | +0,029 | −0,096 | +0,15 (0,81) |
| S3 (R) | 57 (34) | −0,308 | −1,0 | %22,8 | −0,453 | −0,689 | −0,05 (0,39) |
| S4 (R) | 27 (25) | −0,130 | +0,05 | %59,3 | −0,166 | −0,349 | +0,11 (0,79) |

- **S1:** koşulsuz taban (her 3,5 saatlik kapanışta AL) −1,35 bp; olay +1,4 bp daha iyi ama ≈ 0.
- **S1 yıllar:** 2018 +1,4 · 2019 −10,0 · 2020 −0,7 · 2021 +2,2 · 2022 −5,1 · 2023 −5,8 · 2024 +4,3 · 2025 +3,2 · 2026 +9,7.
- **S2'de R uç değerlere dikkat (E146):** en iyi 5 işlem çıkarılınca −0,096; risk ≥ 10 bp alt kümesinde +0,032.
- **Eksik 15 dk pencere:** 62 olayda (14:00 dilimi; Dukascopy 16:15 sonrası boş) S2–S4 açılmadı; MT5 sınamasında açıldı.

## 2. MT5 bağımsız (kutu NAS100 M15, 2022-08 → 2026-11-17, 15 dk çözünürlük)

| | n | ort. | en iyi 5 hariç | spread ×1,5 | plasebo farkı (P) |
|---|---|---|---|---|---|
| S1 | 113 | +3,1 bp | +1,8 | +2,4 | +6,7 (0,99) |
| S2 | 54 | −0,007 | −0,285 | −0,083 | +0,10 (0,66) |
| S3 | 33 | −0,357 | −0,940 | −0,475 | −0,16 (0,30) |
| S4 | 18 | −0,379 | −0,831 | −0,423 | −0,27 (0,14) |

S1 MT5 yılları: 2022 +7,0 · 2023 −5,8 · 2024 +2,8 · 2025 −2,2 · 2026 +10,2.

## 3. Varyantlar (önceden sayılmış; hükme girmez)

Ortalamalar; parantezde KEŞİF/TEST.

| varyant | olay | S1 bp | S2 R | S3 R | S4 R |
|---|---|---|---|---|---|
| **ANA** | 232 | +0,0 (−0,1/+0,1) | +0,108 (+0,079/+0,148) | −0,308 | −0,130 |
| E1 yalnız eşik + üst fitil (örnek 1 ve 5'i tutar) | 820 | −1,7 (−2,6/−1,1) | −0,144 | −0,133 | −0,053 |
| G1 H4 teyidi yok / H4 3,5 sa gövde şartı yok / H4G H4'te de gövde | 625 / 326 / 180 | −1,9 / +0,8 / −1,4 | −0,141 / +0,030 / +0,229 | −0,051 / −0,389 / −0,311 | −0,082 / −0,046 / −0,267 |
| W14 tüm 14 mum (17 Kas çiziminiz) | 232 | +0,0 | +0,237 (+0,405/+0,101) | −0,323 | −0,353 |
| W3 / F3 | 232 | +0,0 | −0,143 / −0,503 | −0,497 / −0,430 | −0,336 / −0,395 |
| eşik %0,40 / %0,75 / %1,00 | 350 / 85 / 33 | −0,1 / +1,3 / +11,7 | +0,029 / +0,018 / +0,056 | −0,279 / +0,064 / +0,813 | −0,132 / −0,158 / −0,385 |
| S1 tutuş 15 / 60 dk | 232 | −0,9 / +2,5 | | | |
| S1 TP %0,20 / %0,50 | 232 | −0,2 / −0,5 | | | |
| U1 üst < alt / U3 üst ≤ alt/3 | 359 / 158 | −1,5 / +0,1 | −0,020 / +0,091 | −0,310 / −0,556 | −0,096 / −0,021 |
| DT Dukascopy tek / MD broker tanımlı | 251 / 259 | +0,2 / −0,1 | +0,096 / +0,073 | −0,321 / −0,308 | −0,130 / −0,049 |
| v1 ilk tanım (yalnız alt ≥ %0,50) | 1.136 | −2,2 | −0,092 | −0,141 | −0,064 |

Varyant hücreleri:
- Dukascopy'de 100 hücrenin 65'i eksi; MT5'te 56 hücrenin 41'i eksi.
- Artıların çoğu S1 ve S2'de; S3 ve S4 neredeyse her hücrede eksi.
- E1'de (fitil kısa görünen ve H4'te üst fitili büyük mumlar dahil) dört kural da eksi. "Gerçek uzun alt fitil" şartı S1'i tabandan
  yukarı taşıyor, ama ölçüte yetmiyor.

## 4. Neden tutmuyor

1. **Fitil kapanışta büyük ölçüde fiyatlanmış.** Gerçek çekiçte S1 tabandan iyi (MT5 +3,1 bp), ama Dukascopy'de ≈ 0 ve ilk dönemde
   eksi. 1 saatlik çekiç bulgusunun (defter FR-07/FR-15) aynı yönde ama daha zayıf karşılığı.
2. **15 dk gövde seviyeleri hayalet seviye.** S2–S4'ün spread'siz hâli de ≈ 0 ya da eksi. Fiyat BT/BB/%48/%50 çizgilerinde rastgele
   bir çizgiden farklı davranmıyor (defter §2.30–2.33).
3. **Çekiçten sonra satmak "korku döner" ilkesine ters** (S3/S4 her tanımda eksi).

## 5. Bu çalışmada düzelttiklerim

- **İlk koşu:** yalnız "alt fitil ≥ %0,50" sayıyordu. İki uçlu mumlar ve Dukascopy'nin eksik 14:00 mumları içerideydi; grafikler
  yalnız 15 dk mumları gösteriyordu.
- **Tanımlar:**
  - v1: 1.136 olay.
  - E1: + üst fitil ≤ alt/2 + MT5 teyidi + 15 dk pencere eksiksizliği; 820 olay.
  - ANA: + alt fitil ≥ gövde + H4 görünümü; 232 olay. Sizin 5 etiketinizi doğru sınıflandıran tek tanım.
- **Dürüstlük notu:** aynı veride dört tanım denendi. ANA tanımı sizin etiketlerinizden geldi; P&L'ye göre ayarlanmadı. Yine de artı
  hücreler önceden kayıtsız hipotezdir. S1 izi Evrim Paneli backlog'unda; tanım değiştirmeden bağımsız dönemde sınanmalı.

## 6. Sınırlar

- MT5 sınaması 15 dk çözünürlükte. Aynı mumda TP ve SL → SL varsayımı muhafazakâr. Spread bar spread'i; Dukascopy modelinden düşük
  olabilir.
- H4 teyidi kutu MT5 H1'den kuruldu (sunucu = NY+7). 3,5 sa teyidi MT5 210m dosyasından (2018-05 →).
- Dukascopy 16:15–17:00 ET boş. 14:00 dilimi 15 dk kurulumu yalnız MT5'te ölçüldü.

## 7. Sizin günün tam sonucu — 17 Kasım 2026 (kutudan taze MT5 verisi, NY 20:36'ya kadar)

`src/bugun_17kasim.py`; grafik [results/bugun_17kasim.html](results/bugun_17kasim.html).

Olay: NY 10:30–14:00 mumu. Alt fitil %1,14, üst %0,03, gövde %0,66; H4'te alt %1,15, üst %0,01. Günün tek olayı bu.

| | ANA (son 6 mum: 13:30 mumu) | W14 (tüm 14 mum: 10:30 mumu, sizin çiziminiz) |
|---|---|---|
| S1 AL | 1/1 kazandı, +30 bp (14:00 → 14:15 TP) | aynı |
| S2 AL | 0/1, −24,6 bp | 5/6 kazandı, +22,0 bp |
| S3 SAT | 1/1, +15,3 bp | 1/3, −0,6 bp |
| S4 SAT | — | 1/2, −20,9 bp |

Bugünün win rate'i (W14): 8/12 = %67. Kâr: +30 + 22 − 0,6 − 20,9 ≈ +30 bp (çoğu S1'den).

Tek gün, kuralın değerini ölçmez. Ölçüyü geçmişteki 232 olay verir:

| kural | win rate | başabaş win rate | sonuç |
|---|---|---|---|
| S1 | %51,7 | %51,7 | ≈ 0 |
| S2 | %57,6 | %52,0 | +0,108R (MT5 −0,007) |
| S3 | %22,8 | %33,0 | eksi |
| S4 | %59,3 | %68,1 | eksi |

## 8. "Canlı mum" varyantı — 3,5 sa kapanmadan işlem (`src/canli_mum.py`, EK-5)

Sorunuz: 17 Kasım'da 10:30 ana mumundan sonra 11:00–13:45 arasında neden işlem açılmadı?

**Neden açılmadı:** Ana kural tespiti 3,5 saatlik mum kapanınca (14:00) yapıyor. O saatten önce mumun nasıl kapanacağı bilinmiyor.

**Gerçek zamanlı yapılırsa:** oluşan 3,5 sa mumu 10:45 mumunun kapanışında (11:00) kuralı zaten sağlıyor: o ana kadar alt %0,99,
üst %0,03, gövde %0,82. Ana mum 10:30 mumu (sizin çiziminiz).

| 17 Kasım, canlı mum | işlem | kazanan | net |
|---|---|---|---|
| S2 AL | 12 | 8 | −10,5 bp |
| S3 SAT | 5 | 3 | +77,0 bp |
| S4 SAT | 3 | 2 | +21,6 bp |

Bugün işaretlediğiniz bölgede açılan işlemler net +88 bp; buna mum kapanışındaki S1 +30 bp ayrıca ekleniyor.
Grafik: [results/canli_bugun.html](results/canli_bugun.html).

**Ama geçmişte (aynı varyant, sızıntısız):**

| | Dukascopy 2018–26 (1.244 canlı tespit) | KEŞİF / TEST | MT5 2022–26 (531) |
|---|---|---|---|
| S2 AL | −0,140R (n 1.277, win %48) | −0,054 / −0,206 | −0,155R |
| S3 SAT | −0,040R (n 873, win %33) | −0,090 / +0,000 | +0,014R |
| S4 SAT | +0,036R (n 428, win %70) | −0,002 / +0,063 (küme P 0,85) | −0,019R |

- Canlı tespitlerin yalnız %54'ü (MT5 %59) mum kapandığında da kuralı sağlıyor; kalanı yanlış alarm.
- S4 Dukascopy'de ≈ +0,04R; ama ilk dönem 0, spread ×1,5'te 0, MT5'te eksi.
- **Hüküm:** canlı mum da kenar üretmiyor (S2 X, S3/S4 ≈ 0 → X/C). Bugünkü kâr tek günün sonucu.
- Not: S3'ün iyimser icra değeri (+1,04R) E146 tuzağı: SL'ye birkaç puan kalan girişler spread'siz büyük R yazıyor.
