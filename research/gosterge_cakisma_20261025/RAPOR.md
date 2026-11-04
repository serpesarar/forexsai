# Gösterge Çakışma Motoru (GÇM) — rapor

Tarih: 2026-10-25 · Ön kayıt: [PROTOCOL.md](PROTOCOL.md) (EK-1…4 dahil) · Tablolar: [SONUCLAR.md](SONUCLAR.md) ·
Kullanım: [README.md](README.md) · Mum-mum inceleme: [inceleme/index.html](inceleme/index.html)

## 1. Ne kuruldu

TradingView'da bulunan göstergeleri her sembolün tüm geçmişine uygulayan, her mumda **353 gösterge tepkisini**
çıkaran ve bu tepkilerin eş zamanlı kombinasyonlarının sonraki **1, 2, 4, 8, 16, 32 barın** yönünü öngörüp
öngörmediğini sınayan bir hat.

**Kapsam:**
- 133 nedensel gösterge, 55 aile.
- TradingView topluluğundan topladığımız 33.389 scriptin sınıflanabilen 30.246'sının **%93,2'si** (boost ağırlıklı **%95,0**) bu ailelerin içinde.
- Resmî kataloğun teknik göstergeleri de bunlara dahil: Ichimoku, Supertrend, Keltner, Stoch RSI, WaveTrend, QQE, Hull/KAMA/ALMA/T3, Fisher, Schaff, TTM Squeeze, Nadaraya-Watson (nedensel), Ehlers, Kalman, SMC yapısı, order block, FVG, likidite süpürmesi, Fibonacci golden pocket, hacim/zaman profili ve diğerleri.
- 29.628 scriptin her biri ayrı çalıştırılmadı: kodları Pine ve çoğu korumalı. Her aile nedensel bir temsilciyle uygulandı (PROTOCOL §1).

**Veri:** dört sembolde elimizdeki tüm zaman dilimleri, 24 (sembol, TF) çifti.

| Sembol | TF'ler | En uzun geçmiş |
|---|---|---|
| NDX | 1m, 5m, 15m, 30m, 1h, 4h, 1d | 1d 2008→2026, 1h 2016→2026, 1m 2025-01→2026-10 (533 bin bar) |
| DAX | 15m, 30m, 1h, 4h, 1d | 2020→2026 |
| XAU | 5m, 15m, 30m, 1h, 4h, 1d | 1h 2016→2026 |
| USOIL | 5m, 15m, 30m, 1h, 4h, 1d | 1h 2016→2026 |

**Ölçek:**
- 144 (sembol, TF, ufuk) hücresi.
- ~12,8 milyon tekli/ikili kombinasyon (L1, L2) + ~30 milyon üçlü genişletme (L3) değerlendirildi.
- Her hücrede en iyi 30 tanesi (toplam 4.212) doğrulama ve kasaya gitti.

**Dürüstlük kuralları** (kodda gömülü):
- Giriş sonraki barın açılışında.
- Taban aynı dönemin aynı UTC saati.
- Örtüşen olaylar bastırıldı.
- Seçim eşiği, aramanın tamamının dairesel kaydırma plasebosuyla (max|z|, ~5,0–5,8) kuruldu.
- Kronolojik %60 keşif / %20 doğrulama / %20 kasa; kasa yalnız sonda okundu.
- Nedensellik testi: geleceği değiştirmek geçmiş hiçbir durumu değiştirmiyor.

## 2. Hüküm

### 2.1 Göstergelerin eş zamanlı çakışma kombinasyonları yönü öngörmüyor (dört sembolde, tüm TF ve ufuklarda)

| Ölçü | Bulunan | Tesadüf beklentisi | p |
|---|---:|---:|---:|
| Keşifte plasebo eşiğini aşan hücre | 11 / 141 | 7,1 | 0,10 |
| Bu 11 hücreden kasada kanıtlı çıkan | **0** | — | — |
| Kanıtlı aday (doğrulama + kasa + lift ≥ 2 puan + maliyeti aşan getiri) | 13 / 4.212 | 10,5 (q99 = 19) | 0,26 |
| Kanıtlı adaylardan aynı sembolün başka bir TF'sinde (yeterli n ile) yine kanıtlı çıkan | **0 / 13** | — | — |

13 kanıtlı adayın sembol dağılımı: NDX 2, DAX 4, XAU 1, USOIL 6 (ayrıntı SONUCLAR.md). Ön kayıttaki tekrarlanma
kuralına (§7.8: komşu ufukta ya da başka bir TF'de de kanıtlı) göre bakınca
([results/kanitli_tekrar_ayrinti.csv](results/kanitli_tekrar_ayrinti.csv), her bölmede n ≥ n_min/4):

| Kaynak aday | Tekrarlandığı hücre | Tür |
|---|---|---|
| DAX 15m h=2 SAT: `BOP14 sıfır üstü & RangeFilter aşağı & fiyat < TWAP` | DAX 15m h=4 | komşu ufuk |
| aynı aday | **NDX 5m h=1** (kasa z 1,78, isabet tabanın +5,1 puan üstünde, n 369, 0,8 bp vs 0,4 bp maliyet) | **başka sembol** |
| NDX 4h h=2 AL: `PVO genişleme & fiyat > R1 & Roofing yukarı` | NDX 4h h=1 | komşu ufuk |
| USOIL 30m h=16 AL: `Coppock sıfır altı & TSI aşağı & BOP < 0` | USOIL 30m h=8 | komşu ufuk |

- Komşu ufuklar aynı olay kümesini paylaştığı için bağımsız kanıt sayılmaz.
- Aynı sembolün başka bir TF'sinde yeterli n ile tekrarlanan aday **yok**.
- Sembol değiştiren tek örnek DAX → NDX (iki endeks, aynı gün-içi yapı: düşüş içinde kısa alım baskısı satılıyor).
  Ama o bile bir sonraki bar ölçeğinde ve maliyetin ancak iki katı.
- Başka hücrelerde yeterli n ile doğrulama + kasada aynı yönde anlamlı 5, ters yönde anlamlı 2 kombinasyon var.

**Sonuç:** kanıtlı adaylar, 4.212 seçimden tesadüfen beklenen sayıdan fazla değil ve zaman dilimleri arasında
tekrarlanmıyor. Bunlar kenar değil, çoklu sınama gürültüsü. Tek izlenmeye değer iz DAX 15m → NDX 5m satış kombinasyonu.

### 2.2 Bir zayıf toplu eğilim var, ama tekrarlanma tesadüf oranında

- Doğrulamayı geçen 238 kombinasyon, her bölmede yeterli olayı olan 18.091 başka (sembol, TF, h) hücresinde aynı tanımla
  yeniden ölçüldü. Kasada keşif yönünde anlamlı **%4,9** (894), ters yönde anlamlı **%4,1** (736) çıktı. Boş beklenti
  her biri için %5, yani tekrarlanma **tesadüf düzeyinde**.
- "Tüm dönem" sayıları (1.342 / 655) daha olumlu görünüyor, ama aynı sembolün TF'leri aynı fiyat yolunu ve keşif
  dönemini paylaştığı için bağımsız değil.
- Seçilen 4.212 kombinasyonun doğrulama ve kasada **ters yönde** anlamlı çıkma oranı tesadüften düşük: doğrulama 238
  geçen / 158 ters, kasa 200 / 148 (boş beklenti ≈ 210 / 210). Kombinasyonların keşif yönünde çok hafif bir
  kalıcılığı var, ama bu, işlem kenarı olacak büyüklükte değil.

### 2.3 Tüm göstergeler birlikte (HistGradientBoosting): çok zayıf ama gerçek bilgi; en güçlü iz XAU'da bir sonraki bar

- Kasa AUC'si saat-eşli tabanın ortalama **+0,006** üstünde; 144 hücrenin 100'ünde pozitif.
- En emin %10'luk dilimde 12 hücre anlamlı pozitif, 0 hücre anlamlı negatif (simetri p = 0,0005). Bu, göstergelerin
  toplamda yön hakkında **bir miktar** bilgi taşıdığını gösteriyor.
- Büyüklük spread mertebesinde:

| Hücre | En emin %10 isabet | Taban | z | Brüt getiri | Maliyet (1 spread) |
|---|---:|---:|---:|---:|---:|
| XAU 15m, 1 bar | %57,3 | %50,5 | 5,5 | 1,4 bp | 0,55 bp |
| XAU 1h, 1 bar | %56,3 | %50,4 | 4,1 | 1,7 bp | 0,73 bp |
| NDX 1m, 1 bar | %51,4 | %50,0 | 3,0 | 0,06 bp | 0,41 bp |
| NDX 30m, 1 bar | %56,0 | %51,9 | 2,8 | 0,55 bp | 0,48 bp |
| USOIL 5m, 1 bar | %53,5 | %50,2 | 2,7 | 0,41 bp | 3,67 bp |

Bilgi en kısa ufukta (1 bar) yoğunlaşıyor ve ufuk uzadıkça kayboluyor. Kayma, komisyon ve gerçek icra (sonraki M1 +
gerçek spread) eklenmeden bile çoğu hücrede maliyeti ancak karşılıyor ya da karşılamıyor. Defterin §3.12 dersiyle
aynı: "gerçek mikro sinyaller ≤ 2–7 bp/işlem, maliyet mertebesinde".

### 2.4 Ne anlama geliyor

1. TradingView'daki göstergelerin %93'ünü temsil eden 133 göstergenin hiçbir tekli, ikili veya üçlü eş zamanlı
   tepkisi, dört piyasamızda ve 1m'den 1d'ye hiçbir zaman diliminde, tekrarlanabilir bir yön kenarı vermiyor. Bu,
   defterdeki tekil sonuçların (HK-01…04, OLD-12, MK-01/05, GF-01, meta-ders §3.1) sistematik ve kapsamlı teyidi.
2. Göstergelerin içindeki zayıf bilgi ancak hepsi birlikte ve en kısa ufukta görünüyor; büyüklüğü icra maliyetine
   denk.
3. Defterde ayakta kalan kenarlar (VIX rejimi, büyük TF trend hizası, seans, stres-günü CAPREV, NDX fakeout) hep
   **fiyat-türevi göstergelerin dışındaki bilgiden** ya da strateji geometrisinden geliyor. Bu çalışma o ayrımı
   güçlendiriyor.

## 3. Sınırlar

- **Scriptler tek tek çalıştırılmadı;** aile temsilcileri kullanıldı. Bir yazarın özel parametre veya özel kuralı
  burada yoksa o script'in kendisi sınanmış sayılmaz. Kapsama aile düzeyinde %93.
- **Bilerek dışarıda bırakılanlar** (EK-1):
  - Seans, mevsimsellik, takvim, ICT zaman modelleri: taban saat-eşli olduğu için tanım gereği dışarıda.
  - VIX / DXY / COT: dış veri, bu fiyat hattında yok.
  - Harmonik ve Elliott: yeniden çizer.
- **Maliyet yalnız tek spread.** Kayma ve komisyon eklenirse sonuçlar daha da kötüleşir.
- **Kombinasyon yönü KEŞİF'te belirleniyor;** rejim değişince işaret dönebilir (E49). Bu, yöntemin kendisinin parçası.
- **Kısa geçmiş:** NDX 1m/5m ve XAU/USOIL 5m yalnız ~1,5 yıl. 1d hücrelerinde olay sayısı küçük.
- **NDX 1m hücresi 86 dakika sürdü** (L3 plasebosu). Daha büyük geçmiş gelirse paralel çalıştırma gerekecek.

## 4. Sistem yeniden nasıl kullanılır

Hat genel bir **gösterge/kapı fikri sınama hattı** olarak kalıyor:
- Yeni bir gösterge `indicators.py`'ye bir satırla eklenir ve aynı ön-kayıtlı protokolle dört sembol × tüm TF × 6 ufukta
  sınanır.
- `inceleme/` sayfaları her mumda hangi göstergenin hangi tepkiyi verdiğini, seçilen kombinasyonların nerede
  ateşlendiğini gösteriyor.

## 5. Sonraki adımlar (backlog)

1. **XAU 15m / 1h bir-sonraki-bar modeli:** sistemin bulduğu en güçlü iz (z 5,5 / 4,1). 2. KURAL kartıyla, gerçek icra
   koşullarında (sonraki M1 açılışı + ölçülmüş spread + kayma) ve ileri dönemde sınanmalı. Beklenti: maliyeti geçmez
   (bellek: xauusd-scalp-no-edge). Yine de ucuz bir sınama.
2. **DAX 15m → NDX 5m satış kombinasyonu** (`BOP14 sıfır üstü & RangeFilter aşağı & fiyat < TWAP → SAT`):
   sembol değiştirerek tekrarlanan tek aday. Yalnız gölge izleme. Bir sonraki bar ölçeğinde, maliyetin ~2 katı.
