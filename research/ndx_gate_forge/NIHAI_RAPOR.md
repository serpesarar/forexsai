# NASDAQ Kapı/Strateji Araştırması — NİHAİ RAPOR v3 (2026-10-02)

Bu klasörün beş turu ile diğer ajanın dört çalışması (`ndx_five_gates_20260930`, `ndx_mechanism_round2_20260930`,
`ndx_synthesis_20261002`, `ndx_caprev_paths_20261002`) karşılaştırıldı. v2'deki üç iddia bu sürümde **düzeltildi** (§5).
Birimler: **R** = başlangıç riski (1R = 1 × önceki 20 işlem gününün günlük volatilitesi × giriş fiyatı). Dolar vaadi yok.
Bütün dönemler geçmişe dönüktür; aynı NASDAQ geçmişine çok kez bakıldı (seçim yükü). Hiçbir aday canlıya hazır değildir.

## 1. Tek cümle sonuç

Beş kanıtlı kapı yok. İki ajanın birbirinden bağımsız ulaştığı **tek ciddi aday CAPREV**: stresli ve korkulu bir günde
(önceki gün NASDAQ ≤ −%1,5 veya 5 günde ≤ −%4, VIX ≥ 18,4) fiyat önceki seansın dibini kırınca **teyit beklemeden almak**.
Bunun dışındaki her şey ya elendi ya da botun kendi örneklemine özgü zayıf gölge işaretidir.

## 2. Önerilen aday — CAPREV (dondurulmuş kural)

| Öğe | Kural |
|---|---|
| Gün koşulu | önceki nakit gün NDX ≤ −%1,5 **veya** son 5 gün ≤ −%4, **ve** önceki gün VIX ≥ 18,4; Pzt–Per |
| Tetik | NY 03:00–15:00 arasında, önceki RTH (09:30–16:00) dibinin altındaki **ilk** kapanmış bar → sonraki bar açılışında BUY |
| Risk | stop = giriş × (1 − günlük vol); lot bu mesafeye göre risk-eşitlenir (~300 puan; botun 110 p SL'iyle aynı lot KULLANILMAZ) |
| Çıkış (iki aday, gölgede birlikte ölçülecek) | **(a) seans sonu 16:00** — en yüksek toplam, büyük günlere daha bağımlı · **(b) +1R hedef / −1R stop, en geç 16:00** — toplam daha düşük, dönemler arası daha dengeli, sermayeyi erken boşaltır |
| Opsiyonel filtre | **artan VIX** (önceki VIX ≥ ondan önceki gün) — diğer ajanın sonradan bulduğu; DAX'ta aynı yönde (§3.3) |
| Sıklık | yılda ~10 gün; sakin dönemlerde (ör. Temmuz–Eylül 2026) hiç yok |

## 3. Kanıt

### 3.1 NASDAQ — iki ajanın bağımsız kodu aynı sayıyı veriyor
| Kaynak | Olay | (a) 16:00 toplam R / ort | (b) +1R hedef toplam / ort | (a) ilk–ikinci yarı ort | (b) ilk–ikinci yarı ort | En iyi 5 gün hariç (a) / (b) |
|---|---|---|---|---|---|---|
| 1h 2016–26 | 107 | +25,7 / +0,24 | +15,7 / +0,15 | +0,02 / +0,45 | +0,08 / +0,22 | +8,9 / +10,7 |
| 30m 2021–26 | 72 | +28,5 / +0,40 | +20,5 / +0,29 | +0,15 / +0,64 | +0,23 / +0,34 | +11,4 / +15,5 |
| 15m 2023–26 | 24 | +19,7 / +0,82 | +14,2 / +0,59 | +0,36 / +1,28 | +0,66 / +0,52 | +4,2 / +9,2 |
| 1m 2025–26 gerçek bid/ask (diğer ajan) | 11 | +11,1 | +4,2 | — | — | en iyi 3 hariç +0,3 / +1,2 |

Diğer ajanın sayıları: 1h +25,75 / +16,11 · 30m +27,62 / +19,91 · 15m +19,73 / +14,32 → **uyum**.
Okuma: (a) daha çok kazanıyor ama 10 yılın ilk yarısında neredeyse sıfır (+0,02) ve büyük günlere yaslı. (b) her iki yarıda
ve en iyi günler çıkarılınca daha sağlam. Kontroller (stressiz gün aynı olay ≈0, aynı olayda SELL negatif, aynı günlerde
rastgele saat alımı gerçek sonucun altında) önceki turlarda geçti.

### 3.2 Bağımsız piyasa: DAX (kural aynen, VIX = ABD VIX'i)
| | Olay | (a) seans sonu | (b) +1R hedef | Ertesi gün kapanış (tur 4) |
|---|---|---|---|---|
| DAX 1h 2019–26 | 54 | +0,17 (P=0,89) | +0,12 | +0,35 (P=0,98) |
| DAX 30m 2021–26 | 37 | +0,12 (P=0,78) | +0,08 | +0,47 (P=0,97) |
| DAX 15m 2023–26 | 13 | +0,18 | −0,01 | +0,87 |

DAX'ta aynı gün sonucu zayıf ve büyük günlere bağımlı; kenar ertesi güne taşınınca belirginleşiyor (DAX Xetra 17:30'da,
ABD öğleden sonrası toparlanmasından ÖNCE kapanıyor — bu mekanizmayla tutarlı). Yön NASDAQ ile aynı, güç daha düşük.

### 3.3 "Artan VIX" filtresi (diğer ajanın adayı) — bağımsız piyasada sınandı
| | NDX 1h artan / düşen | NDX 30m artan / düşen | **DAX 1h artan / düşen** | **DAX 30m artan / düşen** |
|---|---|---|---|---|
| (a) ort R | +0,27 (85) / +0,13 (22) | +0,49 (58) / +0,02 (14) | **+0,26 (45) / −0,29 (9)** | **+0,19 (32) / −0,35 (5)** |

DAX bu filtreyle hiç seçilmemişti; yön aynı çıktı. Ama düşen-VIX hücreleri çok küçük (9 ve 5 olay) ve NDX 1h artan-VIX'in
ilk yarısı (a)'da −0,03. Filtre **gölgede ayrı etiketle ölçülmeli**, kurala gömülmemeli.

## 4. Diğer çıktılar (değişmedi)

| Çıktı | Durum | Not |
|---|---|---|
| K5b: stres günü + önceki RTH dibi altında SELL yok | GÖLGE (bota bağlı) | CAPREV'in aynası; botta 41 karar/5 gün −12,8 p; diğer ajanın portföyünde +6,1R ama 11 gün, anlamsız |
| Kovalama endeksi ≥3 → SELL yok | bota özgü, bağlanmadı | portföye taşınmadı (+0,30R) |
| Pazartesi SELL yok · 5m hacim patlaması · 200g+%10 BUY yok · ay sonu | zayıf/tutarsız | diğer ajan hacim ve uzama vetolarını reddetti |
| REFLEX `mom_cont` | **canlıya alınamaz** (kod kilidi) | kenarın tamamı geleceğe bakma sızıntısıydı |

## 5. Düzeltmeler (v2'deki hatalarım — diğer ajanın denetimi haklı)

1. **"CAPREV-2 iki kademe, 223 olay günü → kart hacmi" yanlıştı.** `w7.py` açılış ve dip bacaklarını ayrı ayrı çözüp R'lerini
   topluyordu; açık pozisyon varken ikinci giriş engellenmiyordu → gün başına **iki risk birimi**. Risk birimine bölününce
   ≈ +0,135R/gün; tek açılış bacağından (+0,154) bile düşük. Tek pozisyonla yeniden yürütüldüğünde (diğer ajan) M1'de
   +14,7R ama düşüş 1,1 → 3,9R ve risk başına getiri yarıya iniyor. **CAPREV-2 önerisini geri çekiyorum; ana aday tek
   kademeli CAPREV (dip kırılımı).** Açılış alımı ayrı ve daha zayıf bir ölçümdür.
2. **"Ertesi gün 16:00 en iyi stoplu çıkış" yalnız 1h/30m'de doğru.** Tek pozisyonla M1 ve 15m'de aynı gün daha iyi; gece
   taşıma boşluk ve finansman riski ekliyor. Birincil çıkış aynı gün; ertesi gün yalnız DAX için anlamlı.
3. **Günlük QQQ/NDX/SPX testinde stop yoktu** ve günlük OHLC'den stop/hedef sırası çıkarılamaz → zayıf destek, kanıt değil.
4. **Saat plasebosu** yalnız dip olayının gerçekleştiği günlerde yapıldı: zamanlamanın önemini gösterir, uygulanabilir bir
   sıfır hipotezi değildir.
5. (Daha önce) "kovalama endeksi K5b'yi içerir" yanlıştı; μ∝σ² yalnız olası bir açıklama.

## 6. Durum ve sonraki adım

- Botta **CAPREV gölge kaydı çalışıyor** (`yeni deneme/caprev_shadow.py`, emir yok; NDX+DAX; aynı gün ve ertesi gün sonucu).
  Ana aday tek kademe olduğu için analizde **k2 (dip kırılımı) kayıtları esas alınır**; k1 (açılış) ayrı ölçümdür.
  ✅ Gölge artık **(b) +1R/−1R sonucunu (`R_tp1`, `tp1_how`), karışımı (`R_half`) ve VIX önceki-gün değişimini (`vix_chg_prev`, `vix_rising`)** da kaydediyor (2026-10-02, 6 yeni birim testi; VIX geçmişi bot tarafından günlük son değerden biriktirilir, ilk 2 işlem gününde alanlar None).
- Canlıya alma için: tamamen yeni dönemde ≥150 tek-pozisyon olay, iki yarı, gerçek dolum/spread/gece boşluğu kartı.
  Yılda ~10 olayla bu yıllar alır; o yüzden 10 yıllık geçmiş birincil kanıt olarak kalacak ve karar risk iştahına bağlı.
- Bütün sonuçlar `docs/KAPI_KAYIT_DEFTERI.md`'de kayıtlı (GF-16…GF-20, CP).

Dosyalar: `final_check.py` → `results/final_check.json` (ajanlar arası tekrar + DAX artan-VIX / +1R testi);
önceki turlar `RAPOR.md`, `PROTOCOL*.md`, `round3.py`, `round4.py`, `cross_market.py`, `w7.py`.
