# Gösterge Çakışma Motoru (GÇM) — rapor

Tarih: 2026-10-25/26 · Ön kayıt: [PROTOCOL.md](PROTOCOL.md) (EK-1…6) · Tablolar: [SONUCLAR.md](SONUCLAR.md) (ana
kütüphane), [SONUCLAR_V.md](SONUCLAR_V.md) (parametre varyantları) · Kullanım: [README.md](README.md) · Mum-mum
inceleme: [inceleme/index.html](inceleme/index.html)

## 1. Ne kuruldu

TradingView'da bulunan göstergeleri her sembolün tüm geçmişine uygulayan, her mumda gösterge tepkilerini çıkaran ve bu
tepkilerin eş zamanlı kombinasyonlarının sonraki **1, 2, 4, 8, 16, 32 barın** yönünü öngörüp öngörmediğini sınayan
bir hat.

**Göstergeler:**
- **Ana kütüphane:** 133 nedensel gösterge, 55 aile, 353 tepki durumu.
  - TradingView topluluğundan topladığımız 33.389 scriptin sınıflanabilen 30.246'sının **%93,2'si** (boost ağırlıklı **%95,0**) bu ailelerin içinde.
  - Resmî kataloğun teknik göstergeleri de dahil: Ichimoku, Supertrend, Keltner, Stoch RSI, WaveTrend, QQE, Hull/KAMA/ALMA/T3, Fisher, Schaff, TTM Squeeze, nedensel Nadaraya-Watson, Ehlers, Kalman, SMC yapısı, order block, FVG, likidite süpürmesi, Fibonacci golden pocket, hacim/zaman profili.
- **Parametre varyantı kütüphanesi (EK-6):** topluluktaki scriptlerin çoğu aynı ailenin farklı parametreleri. Ek olarak 62 yapılandırma, 176 durum: RSI 3/5/9/21/28, Supertrend 5 set, EMA/SMA kesişimleri, BB/KC/Donchian/MACD/CCI/ADX/WaveTrend/QQE/Ichimoku varyantları.
- 29.628 scriptin her biri ayrı çalıştırılmadı: kodları Pine ve çoğu korumalı. Her aile nedensel temsilcileri ve yaygın parametreleriyle uygulandı (PROTOCOL §1, EK-6).

**Veri:** dört sembolde elimizdeki tüm zaman dilimleri, **28 (sembol, TF) çifti**.

| Sembol | TF'ler | Geçmiş |
|---|---|---|
| NDX | 1m, 5m, 15m, 30m, 1h, 4h, 1d | 1d 2008→2026, 1h 2016→2026, 1m 2025-01→2026-10 (533 bin bar) |
| DAX | 1m, 5m, 15m, 30m, 1h, 4h, 1d | 1h/4h/1d 2020→2026, 1m 2026-02→07 (zaman ekseni düzeltildi, EK-5) |
| XAU | 1m, 5m, 15m, 30m, 1h, 4h, 1d | 1h 2016→2026, 1m 2026-06→10 (broker, UTC'ye çevrilmiş) |
| USOIL | 1m, 5m, 15m, 30m, 1h, 4h, 1d | 1h 2016→2026, 1m 2026-02→10 |

**Ölçek:**
- Ana kütüphanede 168 (sembol, TF, ufuk) hücresi.
- ~15 milyon tekli/ikili (L1, L2) + ~35 milyon üçlü (L3) kombinasyon değerlendirmesi.
- Her hücrede en iyi 30'u (toplam 4.932) doğrulama ve kasaya gitti.

**Dürüstlük kuralları** (kodda gömülü):
- Giriş sonraki barın açılışında.
- Taban aynı dönemin aynı UTC saati.
- Örtüşen olaylar bastırıldı.
- Seçim eşiği, aramanın tamamının dairesel kaydırma plasebosuyla (max|z| ≈ 5,0–6,0) kuruldu.
- Kronolojik %60 keşif / %20 doğrulama / %20 kasa; kasa yalnız sonda okundu.
- Nedensellik testi her iki kütüphanede temiz: geleceği değiştirmek geçmişi değiştirmiyor.

## 2. Hüküm (ana kütüphane)

### 2.1 Göstergelerin eş zamanlı çakışma kombinasyonları yönü öngörmüyor

| Ölçü | Bulunan | Tesadüf beklentisi | p |
|---|---:|---:|---:|
| Keşifte plasebo eşiğini aşan seçim içeren hücre | 13 / 165 | 8,2 | 0,07 |
| Bu 13 hücreden kasada kanıtlı aday çıkan | **0** | — | — |
| Kanıtlı aday (doğrulama + kasa + lift ≥ 2 puan + maliyeti aşan getiri) | 14 / 4.932 | 12,3 (q99 = 21) | 0,35 |
| Doğrulamayı geçen 278 kombinasyonun 25.047 başka hücrede kasa tekrarı: aynı / ters yönde anlamlı | %5,2 / %4,5 | %5 / %5 | — |

Kanıtlı aday sayısı tesadüfen beklenen düzeyde. Keşifte en güçlü görünen hücrelerin hiçbiri kasada tutmadı. Bir
kombinasyonun başka hücrelerde tekrarlanma oranı rastgele beklenen %5 civarında.

**Tekrarlanma ayrıntısı** ([results/kanitli_tekrar_ayrinti.csv](results/kanitli_tekrar_ayrinti.csv); ön kayıt §7.8,
her bölmede n ≥ n_min/4):

| Kaynak aday | Tekrarlandığı yer | Tür | Bağımsız mı |
|---|---|---|---|
| USOIL 15m h=8 AL `Chandelier aşağı ∧ son swing tepe ∧ fraktal yapı aşağı` | **DAX 1m h=2/4/8/16/32** (kasa z 1,8–3,1; lift +5…+10 p) | başka sembol + TF | tek bağımsız tekrar (5 ufuk aynı olaylar) |
| DAX 15m h=2 SAT `BOP14 > 0 ∧ RangeFilter aşağı ∧ fiyat < TWAP` | **NDX 5m h=1** (kasa z 1,78; lift +5,1 p) | başka sembol + TF | evet |
| DAX 15m h=2 (aynı) | DAX 15m h=4 | komşu ufuk | hayır |
| NDX 4h h=2 AL `PVO genişleme ∧ fiyat > R1 ∧ Roofing yukarı` | NDX 4h h=1 | komşu ufuk | hayır |
| USOIL 30m h=16 AL `Coppock < 0 ∧ TSI aşağı ∧ BOP < 0` | USOIL 30m h=8 | komşu ufuk | hayır |
| **Ters yönde** — USOIL 1h h=1 AL `ZLEMA ∧ HalfTrend ∧ Kalman` | DAX 15m h=4/8, XAU 1m h=4 | başka sembol | ters |

Bağımsız (sembol/TF değiştiren) tekrarlar 2 aynı yön, 2 ters yön, yani **simetrik**. Sistem düzeyinde bu tesadüf
görüntüsü. Yine de iki aday mekanizma açısından anlamlı ve izlenmeye değer:
- **"Stop çalıştı, yapı aşağı → AL" (USOIL → DAX):** defterin "korku döner" ilkesiyle (§3.2) aynı yönde.
- **"Düşüş içinde kısa alım baskısı satılır" (DAX → NDX):** iki endekste aynı gün-içi yapı.

İkisi de 14 aday içinden sonradan seçildi; kanıt değil, gölge izleme adayı.

### 2.2 Tüm göstergeler birlikte (HistGradientBoosting): zayıf ama gerçek bilgi, spread mertebesinde

- Kasa AUC'si saat-eşli tabanın ortalama **+0,0065** üstünde; 168 hücrenin 118'inde pozitif.
- En emin %10'luk dilimde **16 hücre anlamlı pozitif, 0 hücre anlamlı negatif** (tesadüf beklentisi her biri 8,4;
  simetri p = 0,00003). Göstergelerin toplamı yön hakkında gerçekten **bir miktar** bilgi taşıyor.
- Bilgi en kısa ufukta (1 bar) yoğunlaşıyor. En tutarlı olduğu yer **XAU**: 1m, 5m, 15m ve 1h'te aynı yönde.

| Hücre | En emin %10 isabet | Taban | z | Brüt getiri | Maliyet (1 spread) |
|---|---:|---:|---:|---:|---:|
| XAU 15m, 1 bar | %57,3 | %50,5 | 5,5 | 1,4 bp | 0,55 bp |
| XAU 1h, 1 bar | %56,3 | %50,4 | 4,1 | 1,7 bp | 0,73 bp |
| USOIL 1m, 1 bar | %52,4 | %49,9 | 3,2 | −0,03 bp | 3,27 bp |
| NDX 1m, 1 bar | %51,4 | %50,0 | 3,0 | 0,06 bp | 0,41 bp |
| NDX 30m, 1 bar | %56,0 | %51,9 | 2,8 | 0,55 bp | 0,48 bp |
| XAU 1m, 2 bar | %52,8 | %49,6 | 2,4 | 0,12 bp | 0,60 bp |

Maliyeti brüt olarak aşan yalnız XAU 15m/1h (ve sınırda NDX 30m). Kayma, komisyon ve gerçek icra eklenince büyük
olasılıkla erir. Defterin §3.12 dersiyle aynı: "gerçek mikro sinyaller maliyet mertebesinde".

### 2.3 Ne anlama geliyor

1. TradingView'daki göstergelerin %93'ünü temsil eden 133 göstergenin tekli, ikili veya üçlü eş zamanlı tepkileri,
   dört piyasamızda ve 1m'den 1d'ye hiçbir zaman diliminde tesadüften ayırt edilebilir, tekrarlanabilir bir yön kenarı
   vermiyor. Bu, defterdeki tekil sonuçların (HK-01…04, OLD-12, MK-01/05, GF-01, meta-ders §3.1) sistematik ve
   kapsamlı teyidi.
2. Göstergelerin içindeki zayıf bilgi ancak hepsi birlikte ve en kısa ufukta görünüyor; büyüklüğü icra maliyetine denk.
3. Defterde ayakta kalan kenarlar (VIX rejimi, büyük TF trend hizası, seans, stres-günü CAPREV, NDX fakeout) hep
   **fiyat-türevi göstergelerin dışındaki bilgiden** ya da strateji geometrisinden geliyor. Bu çalışma o ayrımı
   güçlendiriyor.

## 2.4 Parametre varyantları (EK-6): aynı sonuç

Ana kütüphanedeki varsayılan parametrelerin yerine topluluktaki yaygın setler kullanıldı: 62 yapılandırma, 176 durum,
22 aile. Aynı protokolle 28 (sembol, TF) × 6 ufukta koşuldu. Tablolar: [SONUCLAR_V.md](SONUCLAR_V.md).

| Ölçü | Bulunan | Tesadüf beklentisi | p |
|---|---:|---:|---:|
| Keşifte plasebo eşiğini aşan seçim içeren hücre | 18 / 165 | 8,2 | 0,002 |
| Bu 18 hücreden kasada kanıtlı çıkan | **1** | — | — |
| Kanıtlı aday | 8 / 4.924 | 12,3 (q99 = 21) | 0,92 |
| Doğrulama geçen / ters yönde anlamlı | 204 / 224 | ≈ 246 / 246 | — |
| Kasa geçen / ters yönde anlamlı | 209 / 188 | ≈ 246 / 246 | — |
| Başka hücrelerde kasa tekrarı aynı / ters yön (21.782 hücre) | %5,5 / %4,4 | %5 / %5 | — |
| Tam ölçütle tekrar: aynı yön / ters yön | 2 (ikisi de komşu ufuk) / 2 | — | — |
| Tüm-gösterge modeli: AUC farkı, en emin %10 anlamlı + / − | +0,0037; 14 / 1 | 8,4 / 8,4 | — |

Varyantlarda keşif aşaması tesadüften daha "başarılı" görünüyor: 18 hücre plaseboyu aştı. Ama bu başarı doğrulama ve
kasada kayboluyor (1/18). Klasik **aşırı uyum** örüntüsü bu: çok sayıda parametre varyantı geçmişteki gürültüye daha iyi
uyar, ama sonraki döneme taşınmaz (defter E12/E17/E40). Parametre değiştirmek, varsayılan göstergelerde olmayan bir
yön kenarı yaratmıyor.

## 3. Sınırlar

- **Scriptler tek tek çalıştırılmadı;** aile temsilcileri ve yaygın parametreleri kullanıldı. Bir yazarın özel
  formülü burada yoksa o script'in kendisi sınanmış sayılmaz. Kapsama aile düzeyinde %93.
- **Bilerek dışarıda bırakılanlar** (EK-1):
  - Seans, mevsimsellik, takvim, ICT zaman modelleri: taban saat-eşli olduğu için tanım gereği dışarıda.
  - VIX / DXY / COT: dış veri, bu fiyat hattında yok.
  - Harmonik ve Elliott: yeniden çizer.
- **Maliyet yalnız tek spread.** Kayma ve komisyon eklenirse sonuçlar daha da kötüleşir.
- **Kısa geçmiş:** 1m/5m hücreleri yalnız 4–21 ay; DAX 1m'in Şubat–Nisan dilimi broker saatinden düzeltildi (E3).
  1d hücrelerinde olay sayısı küçük.
- **Süre:** NDX 1m hücresi 86 dakika sürdü (L3 plasebosu); daha uzun geçmiş için paralelleştirme gerekecek (backlog).

## 4. Sistem yeniden nasıl kullanılır

Hat genel bir **gösterge/kapı fikri sınama hattı** olarak kalıyor:
- Yeni bir gösterge `indicators.py` (ya da `indicators_variants.py`) içine bir satırla eklenir ve aynı ön-kayıtlı
  protokolle dört sembol × tüm TF × 6 ufukta sınanır.
- `inceleme/` sayfaları her mumda hangi göstergenin hangi tepkiyi verdiğini ve seçilen kombinasyonların nerede
  ateşlendiğini gösteriyor (28 sayfa + dizin).

## 5. Sonraki adımlar (backlog)

1. **XAU bir-sonraki-bar tüm-gösterge modeli (GC-02):** 4 TF'de tutarlı iz. 2. KURAL kartıyla, gerçek icra koşullarında
   (sonraki M1 açılışı + ölçülmüş spread + kayma) ve ileri dönemde sınanmalı. Beklenti: maliyeti geçmez
   (bellek: xauusd-scalp-no-edge).
2. **Gölge adayları (GC-03):** "stop çalıştı, yapı aşağı → AL" (USOIL 15m → DAX 1m) ve "düşüşte alım baskısını sat"
   (DAX 15m → NDX 5m). Yalnız gölge kaydı; sonradan seçildikleri için yeni veriyle doğrulanmadan kanıt sayılmaz.
