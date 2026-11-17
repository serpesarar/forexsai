# FB — "Altın bölge" Fibonacci geri çekilmesi + yutan mum (AKN TRADE Reel) — RAPOR

2026-11-16 · ön kayıt `PROTOCOL.md` (+ EK-1, EK-2) · kod `src/` · sonuçlar `results/`

## Hüküm (tek cümle)

Videonun kuralı NDX'te 6 zaman diliminde, iki yönde, 4 seansta, 5 günde ve 24 saatte **kârlı değil**. 233 bin hücrelik ızgarada bulunan
en iyi NDX adayları bağımsız piyasalara taşınmıyor. NDX'te görülen artı Fibonacci'den değil, **güçlü yükselişten sonra fiyatın devam
etmesinden** geliyor; o da NDX dışına taşınmıyor. Sınıf **X**; iz **C** (NDX 5m "coşku dönmez", TK-05 ailesi).

**EK-3 (2026-11-17):** aynı batarya DAX ve altında (Duka 1m 2018-26) — ikisi de **X**, ızgara iki piyasada da plasebonun altında, 6
dondurulmuş aday bağımsız piyasalarda eksi, DAX'ın Avrupa ailesi CAC 40 / Euro Stoxx 50'ye taşınmıyor (§9).

## 1. Kural (tanım §0)
İtki S ≥ 4 ATR ve ≥ 0,5 ATR/bar · geri çekilme 0,5'e değmiş, 0,786 kırılmamış · bölgede gövde yutan mum · sonraki 1m açılışı + spread ·
SL itki dibinin 0,1 ATR altı · TP önceki tepe · 100 bar zaman çıkışı. Veri: Dukascopy NDX 1m 2018-01 → 2026-11, gerçek spread modeli,
1m yolla çözüm (aynı bar SL+TP → SL). KEŞİF 2018–21 / TEST 2022–24H1 / KÖR 2024H2–2026-11. Önek (sızıntı) testi iki yönde geçti.
Örnek çizim: `results/ornek_15m.png`.

## 2. Birincil 12 hücre (ort R, n)

| TF | UZUN tüm | KEŞİF | TEST | KÖR | KISA tüm | Plasebo farkı U / K |
|---|---|---|---|---|---|---|
| 1m | −0,128 (1.928) | −0,147 | −0,130 | −0,092 | −0,122 (3.119) | −0,02 / +0,03 |
| 5m | −0,026 (492) | +0,030 | −0,004 | −0,174 | −0,105 (989) | −0,00 / −0,03 |
| 15m | −0,101 (170) | −0,141 | −0,096 | −0,050 | −0,087 (464) | −0,09 / −0,02 |
| 30m | +0,006 (108) | +0,087 | −0,004 | −0,155 | −0,064 (252) | +0,02 / −0,01 |
| 1h | −0,278 (23) | −0,417 | −0,064 | −0,150 | +0,008 (97) | −0,21 / +0,11 |
| 4h | −1,03 (3) | | | | −0,260 (32) | |

Holm: en iyi tek yönlü p 0,47 → hiçbiri. Ortalama başabaş isabeti %56–65: TP'ye %45–60 ulaşıyor ama hedef girişe yakın
(yutan mum bölgeden çoktan uzaklaşmış kapanıyor), R:R < 1 (E111).

**Videonun iki iddiası:**
- *"Altın bölge özel":* değil. Aynı kural 0,236–0,382 bandında 15m UZUN −0,005, 30m UZUN +0,053 (altın −0,101 / +0,006); hiçbir TF'de
  altın bölge diğer bantlardan sistematik iyi değil (YL-01 hayalet seviye bulgusuyla aynı).
- *"Yutan mumu bekle":* kaybı azaltıyor (1m −0,159 → −0,128, 5m −0,069 → −0,026) ama artıya çevirmiyor (meta-ders 15).

## 3. Seans / saat / gün (videonun kuralı, `results/birincil_kirilim.csv`)
- **Seans:** üç dönemde de artı olan seans × TF × yön hücresi yok. En az kötü NY (5m UZUN +0,013; 15m UZUN −0,012); en kötü Asya
  (1m UZUN −0,213, 15m KISA −0,174). Küçük artılar (1h KISA Avrupa +0,45, n 28) tek dönemlik.
- **Saat (ET, tüm TF):** 24 saatin hiçbiri üç dönemde artı değil; en az kötü 04–05 ve 10–11 ET, en kötü 19–23 ET (−0,16…−0,23).
- **Gün:** hiçbir gün artı değil; Çarşamba en az kötü (UZUN −0,067), Pazar akşamı açılışı en kötü (UZUN −0,256).

## 4. Keşif ızgarası (233.280 hücre; TF × yön × itki gücü × örüntü × bant × SL × TP × tutuş × seans/gün)
| | Gerçek | Plasebo (aynı braket, rastgele zaman) |
|---|---|---|
| KEŞİF t tavanı (n ≥ 60) | 3,49 | **3,98** |
| t > 2 hücre | 322 | 360 |
| Üç dönem min-t tavanı | 1,26 | 1,23 |
| İlk 20'nin TEST/KÖR'de ikisi de artı | 6/20 | — |
Aile ortalamaları (`grid_aile.csv`): hiçbir boyutun hiçbir değeri hiçbir dönemde artı değil. **Seçim şans düzeyinde.**

## 5. Dondurulan adaylar → bağımsız piyasa (EK-1 A)
| Aday | NDX TEST+KÖR | NDX plasebo farkı P | Bağımsız (GER40 / XAU / Petrol / US500) | Havuz |
|---|---|---|---|---|
| C1 5m UZUN teyitsiz 0,382, S≥6, TP 1,618, NY | +0,116 (P 0,99), sp×1,5 +0,11, tek poz +0,14 | 0,97 | −0,11 / +0,08 / +0,13 / −0,02 | +0,02 (P 0,65) **X** |
| C2 15m UZUN tam yutan 0,618–0,786, TP 1,272, NY | +0,20 (P 0,95) | 0,89 | −0,15 / −0,11 / −0,19 / −0,06 | −0,13 **X** |
| C3 15m UZUN gövde yutan altın, TP 2R, NY (videoya en yakın) | +0,18 (P 0,94) | 0,99 | −0,13 / −0,06 / −0,08 / +0,11 | −0,04 **X** |
NAS100 broker beslemesi (aynı piyasa, 2022/2025→) üçünde de artı: etki NDX'e özgü.

## 6. Ek açılar
- **VIX ≥ 18,4 (korku rejimi, EK-1 B):** UZUN 5m +0,13 / +0,08 / **−0,11**, 30m P 0,885, plasebo farkı P ≤ 0,72 → **X**.
- **Günlük grafik, 18 endeks, 1990→ (EK-1 C):** uzun kurulum çok seyrek (35 yılda 44 işlem), KÖR −0,07 vs plasebo +0,04; kısa her yerde
  eksi (KÖR −0,14) → **X**.
- **C1'in doğası (EK-2):** komşuların yalnız %15'i TEST ve KÖR'de artı (plato yok, tepe). **Aynı itkide Fib'i beklemeden hemen al**
  kontrolü: +0,064R, n 5.440, üç dönem +0,059 / +0,091 / +0,043, P 0,997. C1'in bunun üstüne kattığı +0,034R (P 0,80) anlamsız →
  kenar Fibonacci değil, itki sonrası devam. O kontrol de bağımsızda taşınmıyor: NAS100 +0,035, US30 +0,008, US500 −0,053, US2000 −0,075,
  GER40 −0,035, XAU +0,014, petrol −0,018 (M5 2025-06→).

## 7. Neden çalışmıyor
1. Hedef önceki tepe, giriş yutan mum kapanışı: mum bölgeden çıkmış kapandığı için ödül riskten küçük; isabet başabaşın altında kalıyor.
2. 0,5/0,618/0,786 seviyeleri fiyat için özel yer değil (YL-01: 13 referans ailesi hayaletten ayrılmıyor; burada da diğer bantlar aynı).
3. Kalan tek bilgi "güçlü yükselişten sonra NDX biraz daha yükselir" (meta-ders 2, TK-05). Bu, Fib beklemeden de alınıyor ve NDX dışına
   taşınmıyor.

## 8. Tuzak notu (yeni, E144)
Seviyeye dayalı geri çekilme kuralı yalnız rastgele zaman plasebosuyla sınanırsa itkinin kendi devam etkisi seviyenin hanesine yazılır.
Doğru kontrol, **aynı itkide seviye beklemeden giriş**tir (burada C1'in +0,10R plasebo farkının üçte ikisi itkiden geliyordu).

---

## 9. EK-3 — Aynı batarya DAX ve altında (2026-11-17)

Kullanıcı isteği: "sırasıyla DAX'ta ve altında, aynı başarıyı arayarak". Ön kayıt PROTOCOL EK-3 / EK-3b (sonuçlardan önce).
Veri Dukascopy 1m BID 2018-01 → 2026-11-13 (DAX 2,92 M, XAU 3,14 M dakika; `src/duka_pull.py`; DAX 2026-07-15 sunucuda kalıcı 503, boş gün).
Spread NY saati başına max(Duka 2025 ask−bid, Pepperstone M1): DAX 1,4–7,5 puan, XAU 0,53–0,67 $. Saat ekseni broker M1 ile eşleşiyor
(±1 saat kaydırınca fark 2×–25× büyüyor); önek testi iki piyasada iki yönde geçti. Dönemler, TF'ler, kontroller NDX ile birebir.

### 9.1 DAX — birincil (videonun kuralı, ort R)
| TF | UZUN tüm (n) | KEŞİF | TEST | KÖR | KISA tüm (n) | KEŞİF | TEST | KÖR | Plasebo farkı U / K |
|---|---|---|---|---|---|---|---|---|---|
| 1m | -0,107 (2059) | -0,097 | -0,110 | -0,124 | -0,147 (2659) | -0,190 | -0,151 | -0,067 | +0,031 / -0,004 |
| 5m | -0,061 (617) | -0,033 | -0,117 | -0,054 | -0,098 (831) | -0,119 | -0,024 | -0,135 | +0,002 / +0,016 |
| 15m | -0,016 (199) | +0,048 | -0,110 | -0,028 | -0,145 (336) | -0,178 | -0,081 | -0,145 | +0,057 / -0,079 |
| 30m | -0,112 (98) | -0,075 | -0,117 | -0,171 | -0,102 (188) | -0,200 | +0,031 | -0,055 | -0,070 / -0,006 |
| 1h | -0,350 (19) | -0,682 | -0,164 | -0,402 | -0,060 (77) | -0,008 | -0,274 | +0,075 | -0,376 / +0,019 |
| 4h | +0,425 (6) | +0,742 |  | -0,208 | -0,019 (22) | +0,319 | +0,087 | -0,495 | +0,295 / +0,193 |

Holm en iyi 4h UZUN p 0,08 (n 6) → hiçbiri. Seans: dördünde de iki yön eksi (en az kötü AVRUPA UZUN −0,011). Gün: hepsi eksi.
Saat: 24 saatin yalnız 05 ET (Frankfurt 11:00) iki yönde artı (+0,05/+0,10), üç dönemde artı küçük hücre 3/408 (şans düzeyi).
Videonun iddiaları DAX'ta da tutmuyor: altın bölge diğer bantlardan iyi değil, teyitsiz/itkisiz kontroller benzer.

### 9.2 DAX — ızgara + dondurulan adaylar
| | Gerçek | Plasebo |
|---|---|---|
| KEŞİF t tavanı | 2,74 | **3,25** |
| t > 2 hücre | 52 | **214** |
| Üç dönemde artı hücre | 794 | **1.316** |
| Üç dönem min-t tavanı | 1,09 | **1,53** |

Gerçek ızgara plasebonun **altında**: Fib kuralları DAX'ta rastgele zamanda aynı braketle girmekten kötü.

| Aday (mekanik dondurma) | Kendi TEST+KÖR | Plasebo | Fark P | En iyi 5 hariç | NDX / XAU Duka | Petrol / US500 | GER40 besleme | Havuz |
|---|---|---|---|---|---|---|---|---|
| DAX1 15m UZUN gövde yutan altın, SL 0,786, TP 1,272, Avrupa | +0,171 (151) | +0,086 | 0,77 | +0,06 | −0,05 / −0,08 | +0,14 / −0,32 | +0,18 | −0,04 (P 0,21) **X** |
| DAX2 5m UZUN teyitsiz altın, TP 1,272, Perşembe | +0,114 (250) | −0,04 | 0,91 | +0,06 | −0,06 / −0,06 | −0,05 / −0,16 | +0,06 | −0,07 **X** |
| DAX3 15m UZUN teyitsiz 0,382, S≥6, Çarşamba | +0,107 (180) | +0,09 | 0,54 | +0,06 | +0,01 / −0,11 | −0,07 / −0,19 | +0,14 | −0,07 **X** |

DAX1 **videonun kendi örüntüsü** (altın bölge + gövde yutan) ve 4 dönemde de artı görünüyor, ama: (i) aynı stop/hedefle rastgele zamanda
uzun +0,086R (DAX 2022–26 yükselişi + R:R 1,3 braketi); (ii) fark anlamsız; (iii) 5 işlem kenarın üçte ikisi; (iv) ızgarada plasebo bundan
iyi hücreler üretiyor; (v) 4 bağımsız piyasanın 1'inde artı. "Fib katkısı" (aday − itki anında giriş) +0,13R P 0,95 görünüyor ama
seçilmiş bir hücre seçilmemiş bir kontrolü hep yener (E145) → kanıt değil.

### 9.3 Altın (XAU) — birincil
| TF | UZUN tüm (n) | KEŞİF | TEST | KÖR | KISA tüm (n) | KEŞİF | TEST | KÖR | Plasebo farkı U / K |
|---|---|---|---|---|---|---|---|---|---|
| 1m | -0,229 (2731) | -0,280 | -0,263 | -0,114 | -0,189 (2938) | -0,238 | -0,196 | -0,121 | -0,011 / +0,034 |
| 5m | -0,153 (776) | -0,178 | -0,142 | -0,118 | -0,150 (880) | -0,217 | -0,240 | +0,018 | -0,012 / -0,012 |
| 15m | -0,138 (229) | -0,065 | -0,330 | -0,025 | -0,108 (316) | -0,102 | -0,151 | -0,084 | -0,059 / +0,013 |
| 30m | -0,116 (117) | -0,075 | -0,266 | +0,015 | -0,132 (192) | -0,110 | -0,276 | -0,021 | -0,061 / -0,016 |
| 1h | -0,166 (52) | -0,103 | -0,280 | -0,112 | +0,030 (73) | -0,058 | +0,160 | +0,089 | -0,189 / +0,147 |
| 4h | +0,066 (10) | +0,312 | +0,408 | -1,014 | -0,068 (16) | -0,093 | -0,151 | +0,012 | +0,091 / +0,044 |

Holm en iyi 1h KISA p 0,38. 1m–30m'de iki yönde de −0,11…−0,23R (spread altın 1m'de bedeli büyütüyor). Seans/gün/saat: üç dönemde artı
hücre yalnız 5m UZUN 01 ET (n 25); en az kötü saat 14 ET (−0,09), en kötü 16 ET (−0,41).

### 9.4 Altın — ızgara + adaylar
| | Gerçek | Plasebo |
|---|---|---|
| KEŞİF t tavanı | **1,87** | 3,62 |
| t > 2 hücre | **0** | 33 |
| Üç dönemde artı hücre | 184 | 380 |

| Aday | Kendi TK | Plasebo | Fark P | NDX / DAX Duka | Petrol / US500 | XAU besleme | Havuz |
|---|---|---|---|---|---|---|---|
| XAU1 30m UZUN teyitsiz 0,382, 2R, Avrupa | +0,153 (331) | +0,05 | 0,87 | +0,06 / −0,04 | +0,02 / −0,06 | +0,14 | −0,01 (P 0,36) **X** |
| XAU2 15m UZUN tam yutan 0,382, 2R, Avrupa | +0,181 (145) | +0,02 | 0,88 | −0,03 / −0,15 | +0,01 / +0,37 | +0,23 | −0,04 **X** |
| XAU3 1h UZUN teyitsiz derin, SL bozulma, 1,618, Çarşamba | +0,252 (76) | +0,12 | 0,65 | +0,05 / −0,20 | +0,02 / +0,00 | +0,21 | −0,03 **X** |
2× finansmanla XAU1–3 TK +0,12 / +0,15 / +0,20 (değişmez). VIX ≥ 18,4 ayrımı iki piyasada da üç dönem tutarlı hücre vermiyor (DAX UZUN öngörüsü X).

### 9.5 Çapraz
- **NDX C1–C3 → Duka DAX / XAU 2018-26:** C1 −0,01 / −0,03, C2 −0,07 / −0,07, C3 −0,04 / −0,09 → EK-1'in broker sonucu 8 yılda teyit (X).
- DAX ve XAU adaylarının ikisi de "Avrupa seansında uzun" çıktı; ama DAX1 altında −0,08, XAU1/2 DAX'ta −0,04/−0,15 → ortak bir Avrupa
  sabahı etkisi de yok.

### 9.6 EK-3b — DAX Avrupa ailesi, CAC 40 ve Euro Stoxx 50'de (Duka 1m 2018-26, aynı Avrupa saatleri)
| | CAC 40 | Euro Stoxx 50 | Havuz |
|---|---|---|---|
| Donmuş DAX1 ort R (n) | −0,169 (282), üç dönem −0,10 / −0,21 / −0,25 | −0,081 (265), −0,03 / −0,04 / −0,26 | −0,126 (P 0,01) |
| Plasebo | −0,076 | −0,160 | −0,117 (fark P 0,44) |
| Aile (15m UZUN Avrupa, eng/engf): plasebodan iyi oranı | %65 (912 hücre) | %44 (816) | eşik %70 → **X** |
DAX ile dakikada 0,86 korelasyonlu piyasada bile kural eksi. DAX'taki görüntü DAX'a özgü ve plasebo düzeyinde.

### 9.7 EK-3 hükmü
**DAX: X. Altın: X.** NDX'te en azından bir iz (itki devamı, C) kalmıştı; DAX ve altında o da yok: ızgaranın kendisi aynı braketle rastgele
zamanda girmekten **kötü** (DAX t>2 hücre 52 vs plasebo 214; altında 0 vs 33). "Aynı başarıyı" arayan mekanik aday seçimi her piyasada
kendi verisinde +0,11…+0,25R'lik hücreler buluyor; hiçbiri plasebodan anlamlı ayrılmıyor ve hiçbiri başka piyasaya taşınmıyor (9 aday,
DAX ve altının 6 adayı ile NDX'in 3 adayı; bağımsız havuzların hepsi −0,01…−0,13R). Yeni tuzak E145: seçilmiş adayın "Fib katkısı" seçimden gelir.
