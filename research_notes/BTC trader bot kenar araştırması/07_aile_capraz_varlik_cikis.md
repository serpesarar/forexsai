# Aile "çapraz varlık rejimi + çıkış mekaniği + hafta sonu": BTC 5 yıllık sızıntısız sınama (2026-10-21)

> Kapsam ve kanıt kaynağı: bu notun tüm sayıları yerel, sızıntısız backtest çıktılarından geliyor (web kaynağı yok). "Kaynak"
> bağlantıları dosya yollarıdır. Kök: `research/btc_5y_20261021/fam_capraz_cikis/`.
> - Ön-kayıt: [prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/prereg.md). Hiçbir sonuç hesaplanmadan önce yazıldı. Sonradan yalnız iki betimsel ek yapıldı (A1 ve A2). İkisi de verdikti değiştirmez.
> - Betikler: `common.py` (1m ızgara, broker kapalı dakikaları, swap, eşli çok-varyant 1m simülatörü, bootstrap, kart), `10_regime.py` (C01, C03–C07), `20_exits.py` (C02, X1–X10, swap, hafta sonu), `30_c04_posthoc.py` (A1), `31_circular_placebo.py` (A2), `40_summary.py` (Holm).
> - Çıktılar: `results/regime.json`, `exits.json`, `summary.json`, `c04_posthoc.json`, `circular_placebo.json`.
>
> Protokol görevdekiyle birebir aynı:
> - Dönemler: DISC 2021-06→2023-12, OOS 2024-01-11→2025-06-30, BLIND 2025-07-01→2026-10-20.
> - Giriş, sonraki 1m barın open'ı ± s/2. Aynı barda TP ve SL → SL.
> - Spread: taban s = %0,0185, stres s = %0,028, ayrıca sabit 15 $ varyantı.
> - Swap: long −%14/365, short +%2/365, rollover = NY 17:00 (yaz 21:00 / kış 22:00 UTC). Hafta sonu dahil her gece.
> - Makro yalnız `merge_asof(avail_utc ≤ karar)` ile. Tek istisna C04'teki QQQ **açılışı**: ön-kayıtta tanımlandığı gibi 10:00 ET'de bilinir sayıldı.
> - Broker kapalı dakikaları (günlük 2 dk, Cuma 6 dk) modellendi: bu dakikalarda dolum yok, boşluktan sonra SL open'dan dolar. 2023-03-24 11:28–14:00 dışlandı.
> - Bootstrap gün-blok, 2.000 tekrar.
>
> Kart nasıl hesaplandı: her hipotezde DISC'te seçilen hücre için OOS∪BLIND ("POST") üzerinde hesaplandı.

---

## 1. VIXREG (VIX ≥ 18,4 → BUY, altı → SELL) BTC'ye taşınıyor mu? (C01 günlük kural, C02 nötr giriş filtresi)

### Takeaway
**Hayır.** NDX'teki VIX-rejim kenarı BTC'de seçim sonrası veride sıfır çıktı. C01'de OOS∪BLIND ortR +0,0002 (P %49,5), aynı pencerelerde hep-long +0,0068. C02 hep-long'u geçemedi (+0,021 vs +0,024). DISC'teki pozitif görüntü iki şeyden geliyor: 2021 ve 2023 yükselişinin zamanlaması, ve kalıcı rejim sinyaline karşı fazla gevşek bir plasebo. Dairesel kaydırma plasebosunda DISC yüzdeliği yalnız %77,5.

### Cited Findings
**C01, günlük kural.** Karar 22:30 UTC'de, son bilinen VIX ile. Pencere sonraki rollover − 2 dk'ya kadar sürüyor, yani swap yok. Felaket stopu k × dvol20, seçilen hücre k = 1. Tüm günler sayıldı, 1.946 pencere. Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)

| hücre | DISC n / ortR / P | OOS n / ortR / P | BLIND n / ortR / P | POST hep-long |
|---|---|---|---|---|
| k1 (seçildi) | 923 / +0,0525 / %94,9 | 537 / −0,0097 / %40,3 | 476 / +0,0114 / %58,5 | +0,0068 |
| k2 | 923 / +0,0223 / %90,0 | 537 / −0,0104 / %31,3 | 476 / +0,0149 / %71,7 | −0,0071 |

**C01 kartı (POST, k1).** Toplam 2/6.
- Hacim n = 1.013 ✓.
- ortR +0,0002, %95 GA [−0,058, +0,060], P %49,5 ✗.
- Yarılar −0,017 / +0,018 ✗.
- Stres −0,0030 ✗.
- İcra farkı 0,0084 ✗. Eşik 0,5·|ortR| = 0,0001 olduğu için ölçüt anlamsız ölçüde küçük kalıyor.
- Tek-poz +0,0002 ✓.
- Sabit 15 $ spread ile +0,0011.
- WR %45,4, başabaş WR %45,4.
- Plasebo (yıl-içi permütasyon) %52. BLIND +0,011, işaret pozitif ama hep-long'dan ayırt edilemez. Holm p = 0,497 ✗.

**Kollar (k1).**
- BUY kolu (VIX≥18,4 günleri long): DISC +0,071, OOS +0,043, BLIND −0,061.
- SELL kolu: DISC +0,026, OOS −0,033, BLIND +0,041.
- Hafta içi karar günleri: DISC +0,063, OOS +0,005, BLIND +0,003.
- Hafta sonu karar günleri: DISC +0,027, OOS −0,046, BLIND +0,033. Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json) `C01_kollar`

**Yıllık tablo (k2).** Kural ortR ile hep-long ortR yan yana:

| yıl | yüksek-VIX gün payı | kural ortR | hep-long ortR | not |
|---|---|---|---|---|
| 2021 | %40 | +0,024 | +0,020 | |
| 2022 | %98,6 | −0,031 | −0,042 | kural fiilen "ayıda long" |
| 2023 | %32 | +0,075 | +0,070 | |
| 2024 | %16 | −0,017 | +0,019 | düşük VIX → SELL, boğada kaybetti |
| 2025 | | +0,001 | −0,027 | |
| 2026 | | +0,019 | −0,010 | |

Kaynak: aynı dosya, `C01_yillik`.

**Plasebo duyarlılığı (A2).**
- Yıl-içi permütasyonla DISC max-z p_sel = 0,003 çıkıyor.
- VIX serisini ≥60 gün dairesel kaydırınca (1.000 çekiliş) gerçek DISC ortR'si yalnız %77,5 yüzdelikte (kaydırma medyanı +0,025). POST'ta %41.
- Kaynak: [circular_placebo.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/circular_placebo.json)

**C02, nötr giriş filtresi.** Her UTC saat başı yön VIX rejimine göre veriliyor. SL 1×ATR14(1h). Çıkış iki varyantla sınandı: X4 = 4 s, X5 = 24 s. 47.172 saatlik olay var. Kaynak: [exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json) `C02_VIXREG_notr`

| hücre | DISC ortR (hep-long / karşıt) | OOS | BLIND | POST (hep-long) |
|---|---|---|---|---|
| X5 (seçildi) | +0,045 (+0,011 / −0,063) | +0,033 (long +0,072) | +0,008 (long −0,030) | +0,021 (long +0,024) |
| X4 | −0,009 | −0,019 | −0,018 | −0,019 (long −0,022) |

**C02 X5 kartı (POST).** Toplam 3/6.
- n = 24.309 olay / 1.013 gün ✓.
- ortR +0,021, GA [−0,072, +0,121], P %65,7 ✗.
- Yarılar +0,047 / −0,005 ✗.
- Stres +0,003 ✓.
- İcra farkı 0,033 > 0,010 ✗.
- Tek-poz +0,040 (n 2.343) ✓.
- Plasebo %89, BLIND +0,008. Holm p = 0,333 ✗.

### Inferences
- VIX rejimi BTC'de yön bilgisi taşımıyor. BTC 2022'de yüksek VIX altında düştü, NDX'teki "korku döner" toparlanması BTC'de gün ölçeğinde görülmedi. Yani VIX→NDX bağı, sinyal üretmeyen bir risk-varlığı korelasyonundan ibaret. Sonuç 03 notunun "literatürde yanıtsız" tespitine uygun.
- DISC'teki pozitiflik, persistent bir sinyalin trendli bir varlıkla rastlantısal hizalanması. Yıl-içi permütasyon bu otokorelasyonu yok ettiği için yanıltıcı derecede küçük p verdi (aşağıda "Yeni yöntem tuzakları").

### Gaps
- BTC'nin kendi korku göstergesi (RV, fonlama, opsiyon IV) bu ailede sınanmadı. H02 ve diğer aileler kapsıyor.

---

## 2. Nasdaq öncülüğü: önceki ABD günü QQQ getirisi, QQQ açılış boşluğu, BTC–QQQ korelasyon rejimi (C03, C04, C05)

### Takeaway
- **Günlük QQQ getirisi BTC'nin sonraki sunucu gününü öngörmüyor (C03 X).** DISC'te seçilen "takip" modu POST'ta −0,007R. θ=0 hücresinde mod OOS'ta işaret değiştirdi: takip −0,048, ters +0,046.
- **Korelasyon koşullayıcısı yardım etmiyor (C05 X).**
- **Tek ilginç sinyal C04, QQQ açılış boşluğunu tersine işlemek** (|boşluk| > 0,5σ, 10:00 ET → 16:58 ET).
  - DISC'te +0,211R, P %100, max-z p_sel 0,003.
  - Seçim sonrası OOS +0,044, BLIND +0,024, POST +0,034R. Kart 5/6'da yalnız P(EV>0) %79 düşüyor.
  - Plasebo %81, Holm ✗.
  - Ön-kayda göre **RED**. Defter sınıfı **C**: sönümlenen, ancak işareti üç dönemde de pozitif kalan bir aday.

### Cited Findings
**C03, QQQ günü → BTC sunucu günü.** Yalnız yeni QQQ kapanışı olan günler; k = 2. Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)

| hücre | DISC n / ortR / P | OOS n / ortR / P | BLIND n / ortR / P |
|---|---|---|---|
| θ0 takip | 635 / +0,017 / %77 | 367 / −0,048 / %3,7 | 328 / −0,011 / %35 |
| θ0 ters | 635 / +0,002 / %54 | 367 / +0,046 / %96 | 328 / +0,017 / %69 |
| θ0,5 takip | 400 / +0,037 / %90 | 204 / −0,022 / %30 | 201 / −0,020 / %28 |
| θ0,5 ters | 400 / −0,016 / %25 | 204 / +0,024 / %72 | 201 / +0,023 / %73 |
| **θ1,0 takip (seçildi)** | 215 / +0,065 / %93 | 120 / −0,007 / %46 | 104 / −0,007 / %47 |
| θ1,0 ters | 215 / −0,044 / %10 | 120 / +0,013 / %60 | 104 / +0,015 / %59 |

Kart (POST) 1/6:
- n 224 ✓.
- ortR −0,0070, P %43, yarılar +0,005 / −0,019.
- Stres −0,009, tek-poz −0,007.
- Plasebo %39, DISC max-z p_sel 0,45. POST hep-long −0,046.

**C04, QQQ açılış boşluğu → BTC gün-içi.** Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)

| hücre | DISC n / ortR / P | OOS | BLIND |
|---|---|---|---|
| θ0 takip | 628 / −0,047 / %5 | −0,011 | −0,035 |
| θ0 ters | 628 / +0,086 / %99,7 | +0,010 | −0,003 |
| θ0,5 takip | 207 / −0,171 / %0 | −0,057 | −0,071 |
| **θ0,5 ters (seçildi)** | 207 / +0,211 / %100 | 132 / +0,044 / %74 | 135 / +0,024 / %66 |

C04 kartı (POST): 5/6.

| ölçüt | değer | sonuç |
|---|---|---|
| hacim | n 267 | ✓ |
| ortR / %95 GA | +0,0342 [−0,048, +0,119] | — |
| P(EV>0) | %79,3 | ✗ |
| yarılar | +0,046 / +0,023 | ✓ |
| stres | +0,027 | ✓ |
| icra farkı | 0,0075 ≤ 0,017 | ✓ |
| tek-poz | +0,034 | ✓ |

Ek ölçümler:
- Sabit 15 $ spread ile +0,033.
- WR %51,7, başabaş WR %48,6.
- Plasebo %81. BLIND +0,024 > 0.
- POST hep-long −0,035, yani taban aşılıyor. Holm p = 0,214 ✗.

**C04 post-hoc ayrıştırma (A1, betimsel).** Kaynak: [c04_posthoc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/c04_posthoc.json)
- **Yıllık ortR:** 2021 +0,18, 2022 +0,19, 2023 +0,26, 2024 +0,015, 2025 +0,078, 2026 +0,014. Yani ETF sonrası belirgin sönümleme var.
- **Kollar.** İki kol simetrik çalışıyor, "korku döner" asimetrisi yok:
  - Boşluk yukarı → SELL: DISC +0,215, OOS +0,054, BLIND +0,026.
  - Boşluk aşağı → BUY: DISC +0,215, OOS +0,028, BLIND +0,022.
- **Kontrol olarak BTC'nin kendi gece hareketi** (önceki 16:00 ET → 10:00 ET, ters çevrilmiş, |z| > 0,5): DISC −0,033, OOS +0,008, BLIND −0,065. Yani etkiyi taşıyan BTC'nin kendi dönüşü değil, **QQQ boşluğu**.
  - Boşluk ile gece hareketinin korelasyonu `c04_posthoc.json` içinde.
- **Hücreler:**
  - QQQ boşluğu BTC gecesine *zıt* olduğunda: DISC +0,41 (n 48), OOS +0,25 (n 30), BLIND +0,03 (n 32).
  - Aynı yönde olduğunda: DISC +0,15, OOS −0,015, BLIND +0,022.
  - Küçük n ve post-hoc olduğu için kanıt değil.

**C05, korelasyon koşullayıcı (C03 seçimi üzerine).** Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)
- ρ60 > 0,2: DISC +0,062 → OOS −0,002, BLIND −0,007.
- ρ60 > 0,4 (seçildi): DISC +0,069 → OOS −0,043, BLIND −0,012. POST kartı 1/6, plasebo %35.
- ρ60 medyanı: DISC 0,37, OOS 0,39, BLIND 0,49. ρ > 0,4 payı BLIND'da %53.

### Inferences
- BTC ile QQQ arasındaki bağ **gün ölçeğinde bir öncülük değil**. BTC, ABD kapanışından sonraki saatlerde QQQ'nun yönünü taşımıyor. Korelasyonun yükselmesi (BLIND ρ medyanı 0,49) öngörü gücüne dönüşmüyor. Bu, 03 notundaki "Nasdaq güvenilir ileri gösterge değil" bulgusuyla tutarlı.
- **C04'ün olası mekanizması** literatürdeki "hisse büyük salınımı sonrası BTC gün-içi dönüşü" (aşırı tepki). ABD açılışında QQQ boşluğunun yönüne gitmiş BTC hareketi gün içinde kısmen geri veriliyor.
  - Etki 2021–23'te büyük (~0,2R/gün), 2024+ küçük (~0,01–0,08R).
  - Bu çürüme ETF sonrası ABD-saati likidite artışıyla uyumlu (Kaiko, 03 notu §5). Yine de bir çıkarım, doğrulanmadı.
  - Bugünkü büyüklükle (~+0,03R, P %79) kart geçilemez.
- C03'te θ=0 hücresinin modu OOS'ta işaret değiştirdi. Bu, ızgarada seçim yapmanın sahte öngörü ürettiğinin tipik bir örneği.

### Gaps
- QQQ açılışı yfinance günlük "Open" alanından alındı. Gerçek açılış müzayedesi fiyatı ile farkı doğrulanmadı. Bilinir anı 10:00 ET varsayıldı, böylece 30 dk tampon bırakıldı.
- NQ vadelisi ile gerçek gece/premarket hareketi elimizde yok. Bu yüzden C04'ün daha erken karar anlı (ör. 09:30 ET) versiyonu sınanamadı.

---

## 3. DXY ve US10Y günlük değişimi yön filtresi olarak (C06, C07)

### Takeaway
İkisi de kart geçmiyor. **DXY↑ → SELL** zayıf ama işareti tutarlı (POST +0,006R, P %62, BLIND +0,024). **US10Y** sıfır. Proje önseli doğrulandı: makro yön, XAU'da olduğu gibi BTC'de de çalışmıyor.

### Cited Findings
- **C06 DXY** (ters mod: DXY↑ → SELL BTC). Kaynak: [regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)
  - θ0 (seçildi): DISC +0,031 (P %92), OOS −0,010, BLIND +0,024.
  - θ0,5: DISC +0,026, OOS +0,003, BLIND +0,049.
  - Kart (POST θ0) 3/6:
    - n 686 ✓.
    - ortR +0,0061, GA [−0,034, +0,047], P %62 ✗.
    - Yarılar −0,006 / +0,019 ✗.
    - Stres +0,004 ✓, icra farkı 0,004 ✗, tek-poz +0,006 ✓.
  - Plasebo %57, max-z p_sel 0,25. POST hep-long −0,025.
- **C07 US10Y** (faiz↑ → SELL). Aynı kaynak.
  - θ0: DISC +0,004, OOS −0,024, BLIND +0,019.
  - Kart 1/6: ortR −0,0043, P %43.
  - Plasebo %35, p_sel 0,69.

### Inferences
- DXY'nin BLIND'daki küçük pozitifliği bir kenar adayı değil; dolar-zayıflığı/BTC rejimi 2025-26'ya özgü olabilir. XAU'da işaret değiştiren makro bağların (OLD-07) BTC'deki karşılığı. "Sıfırdan ayırt edilemez" sınıfında kalıyor.

### Gaps
- Gün-içi DXY (ör. 14:00 UTC) verisi yok. Yalnız günlük kapanış sınandı.

---

## 4. Çıkış mekaniği: braket ve zaman, BE, kazananı-koştur (nötr ve bot-tarzı momentum girişlerinde)

### Takeaway
**Hiçbir yönetim kuralı negatif EV'yi pozitife çevirmiyor.** Bütün braketli varyantlar her girişte negatif. Eşli farklar küçük:
1. **Koştur (X8) ve BE30+koştur (X9) long girişlerde sağlam ama küçük bir artı veriyor:** +0,01…+0,02R. Short'ta etkisi yok.
2. **BE (MFE ≥ 0,5R, botun bugünkü modu) bot geometrisinde zararsız, hatta küçük bir artı:** +0,008…+0,012R. Projede BE'nin reddi (M7–M9) BTC'de **yeniden üretilmedi**, ama kazanç ihmal edilebilir.
3. **"Braket ≠ zaman" long tarafta görüldü:** 24 s zaman çıkışı, 1R braketten +0,05…+0,06R daha iyi. Fark BTC'nin long sürüklenmesini yakalamaktan geliyor. Short'ta yok, BLIND'da zayıf.

### Cited Findings
**Girişler.**
- **N-L ve N-S:** her UTC saat başı, 24.309 POST olay. SL 1×ATR14(1h).
- **M:** bot momentum BUY. Kapanmış 15m'de Stoch%K(14,3) > 70 ∧ (C−EMA20)/ATR14 > 0,8 ∧ 1h PSAR altta, yalnız ilk geçiş. Toplam 5.563 olay, POST 3.126.
- Tüm varyantlarda 24 s tavan ve swap uygulandı.
- Kaynak: [exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json) `varyantlar`.

**Varyantların mutlak ortR'si (DISC / OOS / BLIND).** Başabaş WR parantez içinde.

| varyant | N-L | N-S | M-L |
|---|---|---|---|
| X1 TP1/SL1 | −0,041 / −0,018 / −0,059 (≈%50,3) | −0,025 / −0,049 / −0,023 | −0,045 / −0,001 / −0,052 |
| X2 TP0,73/SL1 (bot) | −0,034 / −0,025 / −0,063 (≈%58) | −0,018 / −0,051 / −0,023 | −0,035 / −0,018 / −0,064 |
| X3 TP2/SL1 | −0,062 / −0,011 / −0,063 | −0,031 / −0,071 / −0,038 | −0,040 / −0,015 / −0,041 |
| X4 zaman 4 s | −0,025 / −0,006 / −0,039 | −0,026 / −0,039 / −0,020 | +0,019 / −0,046 / −0,017 |
| X5 zaman 24 s | +0,011 / +0,072 / −0,030 | −0,029 / −0,054 / −0,001 | **+0,083 / +0,050 / −0,001** |
| X6 X3+BE@0,5R | −0,044 / −0,007 / −0,038 | −0,031 / −0,045 / −0,016 | −0,018 / −0,035 / −0,038 |
| X7 X3+BE@1R | −0,055 / −0,012 / −0,053 | −0,036 / −0,054 / −0,024 | −0,041 / −0,029 / −0,035 |
| X8 koştur | −0,029 / +0,001 / −0,056 | −0,024 / −0,046 / −0,014 | −0,013 / +0,018 / −0,037 |
| X9 BE30+koştur | −0,026 / +0,002 / −0,042 | −0,025 / −0,040 / −0,012 | −0,021 / −0,004 / −0,029 |
| X10 X2+BE@0,5R (bot bugünkü) | −0,030 / −0,017 / −0,047 | −0,016 / −0,041 / −0,017 | −0,023 / −0,010 / −0,056 |

**Eşli karşılaştırmalar.** Δ ortR, gün-blok P(Δ>0), ön-kayıtlı benimseme ölçütü uygulandı. Kaynak: aynı dosya, `karsilastirma`.

| karşılaştırma | giriş | DISC Δ (P) | OOS Δ | BLIND Δ | POST Δ (P) | verdikt |
|---|---|---|---|---|---|---|
| K1 X5−X1 | N-L | +0,052 (%86) | +0,090 | +0,029 | +0,062 (%93) | belirsiz |
| K1 X5−X1 | N-S | −0,004 | −0,005 | +0,022 | +0,008 (%60) | belirsiz |
| K1 X5−X1 | M-L | +0,127 (%94) | +0,051 | +0,051 | +0,051 (%79) | BENİMSE |
| K1 X5−X2 | M-L | +0,118 (%91) | +0,067 | +0,063 | +0,065 (%85) | BENİMSE |
| K2 X6−X3 | M-L | +0,022 (%82) | −0,019 | +0,003 | −0,009 (%33) | belirsiz |
| K2 X10−X2 | N-L | +0,005 (%89) | +0,008 | +0,016 | +0,012 (%100) | belirsiz (DISC P %89,5) |
| K2 X10−X2 | N-S | +0,003 (%77) | +0,010 | +0,006 | +0,008 (%99,6) | belirsiz |
| K2 X10−X2 | M-L | +0,012 (%93) | +0,008 | +0,008 | +0,008 (%84) | BENİMSE |
| K3 X8−X1 | N-L | +0,012 (%99) | +0,019 | +0,003 | +0,012 (%98) | BENİMSE |
| K3 X8−X1 | M-L | +0,031 (%99) | +0,019 | +0,015 | +0,017 (%92) | BENİMSE |
| K3 X9−X1 | N-L | +0,015 (%99) | +0,020 | +0,017 | +0,019 (%99,8) | BENİMSE |
| K3 X9−X1 | N-S | −0,000 | +0,010 | +0,011 | +0,010 (%95) | belirsiz |
| K3 X9−X1 | M-L | +0,023 (%94) | −0,002 | +0,023 | +0,009 (%73) | belirsiz |

- Dolum yalnız boşluktan olan SL'lerin payı ≈ %0,1. Kayıp R'ye etkisi ≈ 0,000R/işlem. Kaynak: aynı dosya, `haftasonu`.
- X9'daki BE30 ön-kayıt gereği tek kontrol: 30. dakikanın kapanışında bakılıyor. Botun eski `time30` modu sürekli kontrol eder. Fark notta belirtildi.

### Inferences
- **Momentum girişi bağlamı.** Bu girişin kenar kararı başka ailede. M-L girişi yalnız 24 s zaman çıkışında pozitif ve sönümleniyor: DISC +0,083 → OOS +0,050 → BLIND −0,001. Braketli her geometride negatif. Bu, NDX'teki "momentum filtresi yalnız uzak hedef/zamanla öder" dersinin (OLD-20) BTC'deki karşılığı, ama BLIND'da sıfıra düşmüş.
- **"Braket ≠ zaman" BTC'de yalnız long yönde geçerli.** Mekanizma yön sürüklenmesi: 24 s'lik pencerede BTC 5 yılda ort. +5,4 bp gross. BLIND düşüş döneminde fark küçülüyor: N-L +0,029, P %65.
- **Koştur'un faydası küçük ama tutarlı.**
  - Yalnız long girişte üç dönemde de pozitif (N-L, M-L). Short'ta etkisi yok, bu da aynı sürüklenme mekanizmasını işaret ediyor.
  - +0,01–0,02R'lik fark, sanal TP'nin operasyonel riskini (sunucu TP'si yok) ancak dengeleyebilir.
- **BE: BTC'de zararlı değil.** NDX ve bot ailesindeki "BE kurtardığından fazla kazanan öldürür" bulgusu (M7–M9, IO-07) bu girişlerde görülmedi. Olası nedenler:
  1. BE ancak MFE ≥ 0,5R'de devreye giriyor (koşulsuz time30 değil).
  2. Hedef yakın (0,73R), bu yüzden BE'ye dönen "sonra TP" yolları az.
  - Etki yine de +0,01R mertebesinde. Mevcut bot modunu BTC'de değiştirmek için bir gerekçe yok.

### Gaps
- Yönetim kuralları canlı dolum ve kayma olmadan simüle edildi. Sanal-TP koşturmanın canlıda hiç tetiklenmediği vakası (2026-10-20) BTC'ye aynen taşınırsa ölçülen Δ sıfıra iner.
- Kısmi kapama (TP'de yarım) sınanmadı.

---

## 5. Swap ekonomisi: −%14/yıl long swap hangi tutma süresini ekonomik olmaktan çıkarır?

### Takeaway
- Long swap **3,84 bp/gece**. 1×ATR14(1h) stoplu bir işlem için bu ≈ **0,05R/gece** demek. Bu ailede ve önceki projede görülen kenarların tamamı ±0,01–0,05R, yani **ATR(1h) ölçekli bir BTC long'u tek bir rollover'ı bile geçmemeli.**
- Gün ölçekli stoplarda (k·dvol20 ≈ %2,5–3) swap ≈ 0,013R/gece. Çok günlü tutuşta 5 yıllık ort. BTC sürüklenmesinin **~%70'ini** yiyor: 24 s gross +5,4 bp, swap −3,8 bp.
- Short +0,55 bp/gece alıyor, ama bu ihmal edilebilir.

### Cited Findings
**SL'siz zaman çıkışı, nötr long saat başı girişler (spread dahil).** Kaynak: [exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json) `swap`

| H | gece | ALL gross | ALL net | DISC net | OOS net | BLIND net | swap |
|---|---|---|---|---|---|---|---|
| 1 s | 0,04 | −1,55 | −1,71 | −1,76 | −1,24 | −2,16 | −0,16 |
| 8 s | 0,33 | +0,59 | −0,69 | −1,10 | +3,20 | −4,26 | −1,28 |
| 24 s | 1 | +5,45 | +1,61 | +0,38 | +13,0 | −8,87 | −3,84 |
| 72 s | 3 | +20,9 | +9,44 | +5,61 | +45,5 | −23,8 | −11,5 |
| 240 s | 10 | +80,0 | +41,7 | +29,2 | +164 | −74,0 | −38,4 |

- Tüm değerler bp cinsinden. 24 s'lik getirinin std'si ≈ 274 bp.
- Medyan ATR14(1h)/fiyat: hafta içi %0,734, hafta sonu %0,537. Buradan swap/gece: hafta içi 3,84 / 73,4 ≈ 0,052R, hafta sonu ≈ 0,072R. Kaynak: aynı dosya, `haftasonu.N-L`.
- Rollover'ı kesmeyen "sunucu günü" penceresi (22:30 UTC → sonraki rollover − 2 dk) swap'ı tamamen sıfırlıyor. Karşılığında broker'ın günlük 2 dk kapanışına denk gelen rollover dakikalarında pozisyon tutulmuyor.

### Inferences
- **Maksimum tutma süresi önerisi.** ATR(1h)-stoplu gün-içi işlemler rollover'dan (yaz 21:00 / kış 22:00 UTC) önce kapatılmalı. Zaman stopu "rollover − 2 dk" olmalı.
- **Çok günlü swing (ör. H06 Golden Donchian).** Gecelik ~0,013R'lik (1×dvol stop) bedeli işlem başı beklentiye eklemek gerekir. 10 gün tutuş ≈ 0,13R eder ki bu, XAU'daki Donchian kenarının (+0,39…+0,69R) önemli bir kısmı.
- **Short tarafın küçük artı swap'ı** short'a yapısal bir avantaj sağlamıyor: +0,55 bp, ≈ 0,007R/gece.

### Gaps
- Gerçek swap tahakkuk anı (bölen 360 mı 365 mi; hafta sonu üçlü mü) BTC pozisyonu olmadığı için doğrulanmadı (02 notu). MQL5 tanımına göre 360 gün olursa maliyet %1,4 daha yüksek.

---

## 6. Hafta sonu ve hafta içi: bot BTC'yi hafta sonu işlemeli mi?

### Takeaway
**Ön-kayıtlı "hafta sonu bloğu" ölçütlerinin hiçbiri geçmedi:**
- M-L DISC P(Δ<0) %84,5 ve %86, eşik %90.
- Spread/SL oranı hafta sonu 1,37–1,43×, eşik 1,5×.
- Boşluk kaybı ≈ 0R.

Yani hafta sonunu kapatmak için kanıt yok. Ancak hafta sonu:
- ATR ~%27 daha dar,
- spread'in R içindeki payı ~%40 daha yüksek,
- momentum girişleri DISC ve OOS'ta hafta içinden kötü (BLIND'da tersine).

**Öneri: hafta sonu işlem açık kalsın, ama ayrı etiketle gölgede izlensin.** Pepperstone'da ölçülen hafta sonu spread'i neredeyse aynı (tw-ort 16,33 $ vs 15,85 $), FXNX'in "100–350 $" iddiası bu broker için geçerli değil.

### Cited Findings
- **Spread/SL ve ATR.** Kaynak: [exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json) `haftasonu`

  | ölçü (medyan) | hafta içi | hafta sonu |
  |---|---|---|
  | spread/SL, % modeli | 0,025 | 0,034 (1,37×) |
  | spread/SL, 15 $ modeli | 0,035 | 0,050 (1,43×) |
  | ATR14(1h)/fiyat | %0,734 | %0,537 |

  Hafta sonu payı olayların %30'u.
- **Hafta sonu − hafta içi Δ ortR** (P(Δ<0)):
  - M-L X1: DISC −0,055 (%84,5), OOS −0,109 (%94), BLIND +0,070 (%18), POST −0,029 (%70).
  - M-L X5: DISC −0,214 (%86), OOS −0,265 (%93), BLIND +0,110, POST −0,096 (%75).
  - N-S X3: POST −0,089 (%95).
  - N-L X5: DISC −0,114, BLIND +0,194.
- **Broker kapalı penceresi boyunca Binance hareketi.**
  - Günlük 2 dk (n 1.687): medyan 3,9 bp, p99 44,9 bp (0,49 ATR), maks 114 bp. Normal saatlerin kontrol penceresinde p99 46,8 bp.
  - Cuma 6 dk (n 281): p99 54 bp (0,58 ATR), maks 73 bp.
  - Boşluktan dolan SL payı ~%0,1, işlem başı ek kayıp ≈ 0,000R.
- **Broker ölçümü (02 notu, 14 gün tick):** hafta sonu tw-ort spread 16,33 $ (hafta içi 15,85 $), p99 47,5 $ (39,9 $). Hafta sonu düzensiz bakım boşlukları gözlendi: 6–129 dk, ör. 2026-10-17 Cumartesi 06:09–08:18 UTC. Kaynak: [02_veri_ve_broker.md](file:///Users/melihcanodacioglu/Desktop/panel/research_notes/BTC%20trader%20bot%20kenar%20ara%C5%9Ft%C4%B1rmas%C4%B1/02_veri_ve_broker.md)

### Inferences
- Bilinen kapalı pencerelerdeki boşluk riski ihmal edilebilir: BTC hareketi o 2–6 dakikada normal dakikalardan farklı değil.
- Gerçek risk **modellenemeyen düzensiz hafta sonu bakımları**. 129 dk'lık bir kesinti, 1×ATR(1h) stopu kolayca atlayabilir (2 saatlik BTC std'si ~0,8–1 ATR(1h)). Bu boşlukların 5 yıllık sıklığı bilinmiyor.
- Hafta sonu ATR sıkışması (E32), R cinsinden maliyeti ve stop sıkılığını kötüleştiriyor. ATR(1h)-stoplu bir kuralda hafta sonu SL'leri pratikte daha dar oluyor.

### Gaps
- 2021–2025 için broker hafta sonu spread ve bakım geçmişi yok, yalnız son 14 gün tick ve 60 gün M1 var. Düzensiz bakım boşlukları simülasyona katılmadı.

---

## Defter satırı taslağı (`docs/KAPI_KAYIT_DEFTERI.md` §6 biçimi; yeni bölüm önerisi "§2.11 BTC aileleri")

Ortak kanıt yolu: `research/btc_5y_20261021/fam_capraz_cikis/` (prereg.md + results/*.json). Notlar:
`research_notes/BTC trader bot kenar araştırması/07_aile_capraz_varlik_cikis.md`.

| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |
|---|---|---|---|---|
| BTC-X01 | 2026-10-21 | **VIXREG günlük BTC'ye taşıma**: son bilinen VIX ≥18,4 → BUY, altı → SELL; karar 22:30 UTC, çıkış sonraki rollover−2 dk (swap yok), felaket stopu k·dvol20 (k∈{1,2}) | Binance 1m 2021-06→2026-10. DISC +0,053R (k1), OOS∪BLIND n 1.013 **+0,0002R** P %49,5, yarılar −0,017/+0,018, kart 2/6, plasebo %52, Holm p 0,50; hep-long +0,007. 2022'de günlerin %99'u yüksek VIX → "ayıda long". DISC "anlamlılığı" yıl-içi permütasyon artefaktı (dairesel kaydırmada %77,5) | X |
| BTC-X02 | 2026-10-21 | VIXREG nötr saat başı giriş filtresi (yön = rejim; SL 1×ATR14(1h); 4 s / 24 s zaman çıkışı) | POST X5 +0,021R vs hep-long +0,024 (taban aşılmıyor), P %66, kart 3/6, plasebo %89; X4 −0,019 | X |
| BTC-X03 | 2026-10-21 | Önceki ABD günü QQQ getirisi → BTC sunucu günü (θ∈{0;0,5;1}σ20 × takip/ters, k=2) | Seçilen θ1 takip DISC +0,065 → POST −0,007 (kart 1/6, plasebo %39, p_sel 0,45); θ0'da mod OOS'ta işaret değiştirdi (takip −0,048 / ters +0,046) | X |
| BTC-X04 | 2026-10-21 | **QQQ açılış boşluğunu ters işle**: \|log(QQQ open/önceki close)\| > 0,5σ20 → boşluğun tersi yönde BTC, 10:00 ET giriş → 16:58 ET çıkış, SL 1×dvol20 | DISC n 207 **+0,211R** P %100 (max-z p_sel 0,003); OOS +0,044, BLIND +0,024; POST n 267 +0,034 [−0,048, +0,119] P %79, yarılar +0,046/+0,023, stres +0,027, kart 5/6, plasebo %81, Holm p 0,21 → ön-kayda göre RED. Yıllık 2021-23 ≈ +0,2 → 2024-26 +0,01…+0,08 (ETF sonrası sönüm); iki kol simetrik; BTC'nin kendi gece dönüşü kontrolü negatif (etki QQQ boşluğundan) | C (aday: yeni ön-kayıtla ileri gölge) |
| BTC-X05 | 2026-10-21 | BTC–QQQ 60g korelasyon rejimi koşullayıcısı (ρ>0,2 / 0,4) BTC-X03 üzerine | ρ>0,4 DISC +0,069 → OOS −0,043, BLIND −0,012; kart 1/6. ρ medyanı BLIND'da 0,49'a çıktı ama öngörüye dönüşmüyor | X |
| BTC-X06 | 2026-10-21 | DXY günlük değişimi → BTC ters yön (θ∈{0;0,5}σ) | POST n 686 +0,006R P %62, kart 3/6, plasebo %57; BLIND +0,024 (tek dönem) | X |
| BTC-X07 | 2026-10-21 | US10Y günlük değişimi → BTC ters yön | POST −0,004R P %43, kart 1/6, plasebo %35 | X |
| BTC-X08 | 2026-10-21 | Braket (TP1/SL1, TP0,73/SL1) vs 24 s zaman çıkışı (SL 1×ATR1h) — nötr saat başı ve bot momentum BUY girişleri | Long'da zaman > braket: N-L POST Δ +0,062 (P %93), M-L +0,051 (P %79; ön-kayıt "benimse"); short'ta ≈0. Mekanizma long sürüklenmesi; BLIND'da zayıf. Mutlak: braketlilerin hepsi negatif; M-L X5 DISC +0,083 → BLIND −0,001 | B |
| BTC-X09 | 2026-10-21 | BE @ MFE≥0,5R (botun conditional_mfe modu) TP0,73/SL1 geometride; BE@0,5/1R TP2 geometride | X10−X2: N-L +0,012 (P %100 POST), N-S +0,008, M-L +0,008 (benimse ölçütü yalnız M-L'de); TP2 geometride karışık (M-L −0,009). **BTC'de BE zararlı değil** — proje reddi (M7–M9) burada yeniden üretilmedi, ama etki ≈+0,01R | B |
| BTC-X10 | 2026-10-21 | Kazananı-koştur (TP1R'de TP kalk, SL=+0,4R, iz tepe−0,6R) ve BE30+koştur | X8−X1: N-L +0,012 (P %98), M-L +0,017 (P %92) → ön-kayıt "benimse"; X9−X1 N-L +0,019 (üç dönemde +); short'ta ≈0. Küçük; sanal TP gerektirir (sunucu TP'si koştur'u öldürür, 2026-10-20 vakası) | B |
| BTC-X11 | 2026-10-21 | Swap ekonomisi (long −%14/yıl) | 3,84 bp/gece ≈ 0,05R/gece (1×ATR1h stop, hafta sonu 0,07R) ≈ 0,013R/gece (1×dvol20 stop); 24 s'de 5 yıllık ort. long sürüklenmenin %70'i. ATR(1h)-ölçekli işlemler rollover'dan önce kapanmalı | A (olgu/maliyet) |
| BTC-X12 | 2026-10-21 | Hafta sonu işlem bloğu (ön-kayıtlı 3 ölçüt) | Hiçbiri geçmedi: M-L Δ DISC −0,055 (P %84,5) / OOS −0,109 / BLIND +0,070; spread/SL 1,37–1,43× (<1,5); kapalı pencere boşluk kaybı ≈0R (p99 hareket 0,49–0,58 ATR). Hafta sonu ATR %27 dar. Blok için kanıt yok; ayrı etiketle gölge | B |

---

## Yeni yöntem tuzakları

- **E40 (öneri): Kalıcı rejim sinyalinde yıl-içi etiket permütasyonu plaseboyu iyimser yapar.**
  - Sorun: VIX rejimi gibi otokorelasyonu yüksek bir sinyal, trendli bir varlıkla (BTC) yıl içinde rastlantısal biçimde hizalanabilir. Günleri karıştıran plasebo bu kalıcılığı yok eder ve boş dağılımı fazla dar çizer.
  - Vaka: BTC-X01'de DISC max-z p_sel 0,003 (yıl-içi permütasyon) çıktı, ama aynı istatistik dairesel kaydırma plasebosunda yalnız %77,5 yüzdelikte. OOS∪BLIND'da etki sıfır.
  - Önlem: kalıcı sinyallerde plasebo olarak **dairesel kaydırma / blok permütasyon** kullan (≥ sinyalin yarı-ömrü). Yıl-içi permütasyonu yalnız gün-içi bağımsız sinyallerde kullan.
- **E41 (öneri): ATR-normalize R'de swap maliyeti stop ölçeğiyle büyür.** Sabit bp maliyet, dar stoplu (ATR 1h) işlemde 0,05R/gece, geniş stoplu (dvol) işlemde 0,013R/gece eder. Çok-ufuklu kıyaslarda swap'ı R cinsinden ve stop ölçeğiyle birlikte raporla. Aksi hâlde "zaman çıkışı daha iyi" sonucu, swap'ı yanlış ölçeklenen bir ufka taşınabilir.
- **(Doğrulama notu) Izgarada mod seçimi.** "Takip" ile "ters" mod aynı ızgarada seçilince, DISC'te kazanan mod OOS'ta işaret değiştirebilir (BTC-X03 θ0). E17/E24'ün yön versiyonu: iki mod birlikte raporlanmalı, mod seçimi ön-kayıtta a priori yapılmalı.

---

## Bot entegrasyonu için icra önerileri

1. **Hafta sonu işlem: evet, açık kalsın**, çünkü ön-kayıtlı bloklama ölçütleri geçmedi. Uygulama koşulları:
   - Hafta sonu işlemleri ayrı etiketle (magic veya alt-scope) gölge karnede izlenmeli.
   - Momentum girişleri DISC ve OOS'ta hafta sonu daha kötüydü.
   - Pozisyon açıkken düzensiz hafta sonu bakım boşluklarına (6–129 dk) karşı **sunucu-tarafı SL zorunlu**.
   - Pepperstone hafta sonu spread'i hafta içiyle neredeyse aynı (16,3 $ vs 15,9 $). Spread kapısı gerekirse `spread > 40 $` (tick p99 ≈ 40–47 $) iyi bir girişte-veto eşiği olur. Bu bir öneri, sınanmadı.
2. **Maksimum tutma süresi (swap).**
   - ATR(1h)-ölçekli işlemler **rollover'dan önce kapatılmalı**: zaman stopu = NY 16:58 = yaz 20:58 / kış 21:58 UTC. Tek gece ≈ 0,05R maliyet, bu ailedeki her etkiden büyük.
   - Rollover'dan sonraki ilk dakikalar (21:01/22:01 UTC) yeni giriş için uygun. Hem swap hem broker'ın 2 dk kapanışı geride kalır.
   - Gün ölçekli (dvol stoplu) swing'lerde gecelik ~0,013R bedel beklentiye eklenmeli.
   - Short'lar swap alır (+0,007R/gece), ama karar etkileyecek büyüklükte değil.
3. **Sunucu-tarafı TP mı?**
   - Kazananı-koştur long girişlerde küçük bir artı veriyor (+0,01–0,02R). Bu artı ancak **sunucu TP'si koymadan** (sanal TP, bot yönetir) alınabilir. NDX'te sunucu TP'si koştur'u hiç tetiklemedi.
   - Öneri: **sunucu SL her zaman**. TP ya sunucuda (basit, bot çökmesine dayanıklı) ya sanal (koştur). Fark küçük olduğu için sanal TP seçilirse, bot kesintisine karşı sunucuda uzak bir "felaket TP'si" önerilir (ör. 3R). Bu bir çıkarım, sınanmadı.
   - BE @ MFE ≥ 0,5R (mevcut mod) BTC'de zararsız. BE30 koşulsuz moduna dönmek gerekmiyor.
4. **Lot boyutu (1 lot = 1 BTC; 1 $ hareket = 1 $/lot).**
   - BLIND'da medyan ATR14(1h) = **467 $** (p90 779 $), fiyat ~82.300 $. 1×ATR(1h) stoplu 1 lot ≈ 467 $/R. dvol20 stoplu (~%2,5) 1 lot ≈ 2.000 $/R.
   - Formül: `lot = hedef_risk_$ / SL_mesafesi_$`, 0,01 adıma yuvarlanır. Örnek: 250 $ risk ve 467 $ stop → 0,53 lot.
   - **Endeks botunun 5,0 lot ayarı BTC'ye kopyalanmamalı:** 5 BTC ≈ 410 bin $ nominal, ≈ 2.300 $/R.
   - 1 lot marjin ≈ %5 (~4.100 $). Hesap 1:200 olsa da kripto 1:20.
   - Günlük fren ve `_bot_magics()` listesine yeni BTC magic'i eklenmeli (IO-21 dersi).
5. **Bu aileden canlıya giden kural yok.** Çapraz-varlık yön filtrelerinin (VIX, QQQ, DXY, US10Y) hiçbiri BTC bot girişine kapı olarak bağlanmamalı. Tek aday BTC-X04 (QQQ açılış boşluğu tersi, C). Yeni bir ön-kayıtla (2026-10-21 sonrası veri, sabit θ=0,5, 10:00 ET) **gölge karne** olarak ileriye izlenebilir. ETF sonrası büyüklüğü (~+0,03R) kartı geçmeye yetmiyor.
