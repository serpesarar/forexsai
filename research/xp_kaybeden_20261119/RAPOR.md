# Korku gecesi + XP: kaybeden vs kazanan derin karşılaştırma — RAPOR (2026-11-19)

- **Ön kayıt:** `PROTOCOL.md` (+ EK-1, sonradan kontrol).
- **Kod:** `src/ozellik.py` (özellikler), `src/analiz.py` (tarama, kümeleme, kesişim, modeller), `src/saglamlik.py` (EK-1).
- **Sonuçlar:** `results/analiz.json`, `results/saglamlik.json`.

## Veri
- **İşlemler:** 754 işlem (MT5 NAS100/US500/US30/US2000, M30, tik hacmi): KEŞİF 300 (71 kaybeden), TEST 454 (118 kaybeden). Duka NDX ek kontrol.
- **Özellikler:** 117 = 87 yeni + 30 eski (XG-01), 9 aile, yalnız 16:00 öncesi kapanmış mumlardan:
  - 30 dk ve 1 sa göstergeler: RSI14/2, Stokastik, CCI, MACD ve eğimi, Bollinger %B ve genişlik, ATR, ADX/DI, EMA9/21/50/200 uzaklığı ve dizilimi, MFI;
  - fiyat–RSI/MACD uyumsuzluğu (30 dk, 1 sa);
  - tik hacmi: gün, son saat, kırmızı/yeşil oranı, en büyük mum, dip mumu, düşüş bacağı, VWAP;
  - son mum formasyonu: gövde, fitiller, çekiç, yutan, iç mum, kırmızı seri;
  - destek/direnç: 5/20/60/250 gün diplerine uzaklık, üstte kırık destek sayısı ve uzaklığı, dip kümesi;
  - trend kanalı: 20/60 gün, 80 saat ve seans regresyonu (eğim, R², z);
  - düşüş yapısı: tepeden düşüş, en büyük mum payı, dipten sekme, sabah payı, düşen gün serisi;
  - piyasalar arası: göreli zayıflık, yayılım, aynı gün K1 sayısı.

## 1. Tek tek
- Çoklu test eşiği (1.000 permütasyon, |AUC − 0,5| ≥ 0,133): yalnız **son yarım saat** geçti. TEST'te veto X: vetolananlar +59, kalanlar +64.
- KEŞİF ile TEST AUC'leri arasında korelasyon 0,43. İlk 20 özelliğin %85'i TEST'te aynı yönde, ama etkiler küçük (TEST AUC 0,40–0,56).
- Donmuş KEŞİF eşiğiyle TEST vetoları (her biri tek başına, en alt veya üst %20):

| Özellik | Anlamı | TEST veto ort / kalan | kâr× | zarar× | yön | Hüküm |
|---|---|---|---|---|---|---|
| T_1sa_z | fiyat 80 saatlik 1 sa kanalının en altında | +1,8 / +84,0 | 0,99 | 0,57 | 4/4, Duka +6,5 / +99,5 | **C** |
| m30_atr_bp | 30 dk oynaklık düşük | +26 / +76 | 0,89 | 0,80 | 4/4 | C |
| vix | VIX düşük (XG-03 P2 tekrarı) | +32 / +79 | 0,82 | 0,75 | 4/4 | C |
| H_maks_mum_oran | seansın en büyük mumunda hacim patlaması | +7,9 / +70 | 0,98 | 0,84 | 3/4 | C |
| h1_rsi14 (büyük kayıp etiketi) | 1 sa RSI çok düşük | +12,9 / +81 | 0,94 | 0,63 | 4/4 | C |
| uyumsuzluk (U_h1_macd_fark), son 30 dk mum aralığı, MACD eğimi, son saat | — | TEST'te ters ya da yok | — | — | 0–2/4 | X |

## 2. Kümeleme
- **KMeans (siluete göre k = 2):** kaybeden oranı iki kümede aynı (%23,7 / %23,6), yani kaybedenleri ayıran bir küme yok. EMA'ların altında kalan, düşüş trendindeki küme daha çok kazanıyor (KEŞİF +104 vs +60, TEST +74 vs +53), ama daha az kaybetmiyor.
- **Kaybeden tipleri (giriş sonrası yola göre):** iki tip var.
  - **Çöküş tipi:** 12 işlem, ortalama −295 bp. 20:00'dan itibaren kesintisiz düşüş, en derin nokta −899 bp. Sayı sınamaya yetmiyor.
  - **Sıradan kaybeden:** 177 işlem, ortalama −149 bp. Girişte tanınmıyor (TEST AUC 0,557; KEŞİF içi 0,82 = aşırı uyum).

## 3. Kombinasyon
- **İkili VE kesişim (190 çift):** KEŞİF'in en iyisi (son saat ∧ 1 sa MACD uyumsuzluğu) şans P 0,03 ile "anlamlıydı", TEST'te çöktü (veto +97 vs +56). Diğer dört aday da X ya da C.
- **Modeller (KEŞİF'te eğitim, TEST'te veto: en riskli %15):**

| Model | KEŞİF OOF AUC | TEST AUC | Duka AUC | TEST veto ort / kalan | kâr× | zarar× | Hüküm |
|---|---|---|---|---|---|---|---|
| Karar ağacı d2/d3 | 0,55–0,56 | 0,52 | 0,56 | +57 / +66 | 0,60 | 0,57 | X |
| L1 lojistik | 0,56 | 0,52 | 0,50 | +67 / +61 | 0,67 | 0,80 | X |
| **GBM** | 0,59 | **0,615** | **0,632** | **−1,8 / +76** | **1,005** | **0,72** | **C** (4/4, Duka −24 / +90) |

- GBM'in en önemli özellikleri: 1 sa RSI, **düşüş bacağındaki hacim**, son 30 dk mumun ATR'ye oranı, VIX değişimi, VIX, son yarım saat, 3 günlük getiri, 1 sa kanal z.
- XG-04'te (yalnız eski özellikler) TEST AUC 0,50–0,62 idi. Yeni aileler GBM'i alt sınırdan üst sınıra taşıdı.

## EK-1 sağlamlık (sonradan kontrol, hüküm değiştirmez)
- **Kanal uzunluğu × eşik (12 hücre):** yön 4 piyasanın en az 3'ünde 11/12 hücrede tutuyor. Ama kâr korunması (≥ 0,95) yalnız 80 saatte var (q10 ×1,08, q20 ×1,00, q30 ×0,95). 40/120/200 saatte kâr ×0,74–0,97. Yani **80 saatte keskin bir tepe var**, komşular zayıf.
- **Kanal neyi ölçüyor:** 1 sa RSI ile korelasyonu 0,72, gün getirisiyle 0,45, VIX ile 0,39. Kısa vadede ne kadar aşırı satıldığını ölçüyor.
- **Kanal yıl yıl:** vetolanlar kalanlardan 7/9 yılda kötü (MT5 havuzu ve Duka). Vetolanlar çoğu yıl artıda (+2…+42); eksi yıllar 2019 ve 2022. Yani bu bir **kalite filtresi**, kaybeden avcısı değil.
- **VIX üçte birlikleri içinde (TEST):** düşük VIX'te etki yok (+32 / +33), orta VIX'te güçlü (−54 / +41), yüksek VIX'te kalite takası (+30 / +189).
- **GBM:**
  - 5 tohumda kararlı: kâr ×0,995–1,041, zarar ×0,70–0,72.
  - TEST'in 6 yılının 6'sında vetolanlar kalanlardan kötü.
  - 4 piyasanın 4'ünde aynı (US500 +50 / +82).
- **Kanal ∪ GBM (sonradan, ön kayıtta yok):** 160 veto, vetolananlar +7,9; **kâr ×0,956, zarar ×0,46**. Bu, "kâr aynı, zarar yarıya" hedefine TEST'te ilk kez yaklaşan sonuç. Sonradan kurulduğu için kanıt değil; ileri gölge sınaması gerekir.

## Hüküm
- **Kaybedeni tek başına eleyen bir fark bulunamadı.** Vetolanlar ortalamada sıfıra yakın (eksi değil). Kaybedenlerin %75'i giriş anında kazananlardan ayırt edilemiyor.
- **Riski azaltan kalite filtreleri var: C.**
  - 1 sa kanal dibi (z80, en alt %20);
  - GBM vetosu;
  - hacim patlaması, düşük ATR ve düşük VIX (zayıf).
  - Birleşimleri TEST'te zararı yarıya indiriyor, kâr ≈ %4 düşüyor; ama birleşim sonradan kuruldu → ileri GÖLGE adayı.
- **Kullanıcı hipotezleri tek tek:**
  - Uyumsuzluk: **X**.
  - Formasyon: **X**.
  - Destek/direnç konumu: **X** (büyük kayıpta kırık destek sayısı zayıf iz).
  - Düşüşteki hacim: **C** (hacim patlaması; GBM'in ikinci özelliği).
  - Trend kanalı: **C** (en güçlü tek özellik ama 80 saatte keskin tepe).
- **Sayılar:**
  - 117 özellik × 2 etiket tarandı; 1.000 permütasyon.
  - 2 × 190 çift (her biri 300 permütasyon).
  - 2 × 4 model; 5 küme sayısı; 2 kaybeden tipi.
  - EK-1'de 12 kanal hücresi.
