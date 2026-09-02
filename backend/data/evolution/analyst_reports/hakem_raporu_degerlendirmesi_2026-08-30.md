# Hakem raporunun değerlendirmesi (2026-08-30)

## 1. Hakem HAKLI — ispatımı düzelttim

`alfa_kesif_denetimi` raporumda #4 için *"P(uzun)+P(kısa)=1, %126 matematiksel
olarak imkânsız"* demiştim. **Bu ispat fazla genelleyici.** Sayısal doğrulama:

| geometri | null P(uzun) | null P(kısa) | toplam |
|---|---:|---:|---:|
| Simetrik ±1R (benim testim) | 0,500 | 0,500 | **1,000** → tümleyen, %126 imkânsız |
| Asimetrik TP80/SL110 (onların testi) | 0,579 | 0,579 | **1,158** → tümleyen DEĞİL, %126 mümkün |

Driftsiz yürüyüşte P(+a'ya önce) = b/(a+b). Barajlar asimetrikse uzun ve kısa
farklı baraj kümeleri kullanır ve ikisi de kazanabilir. **Hükmüm doğruydu, ispatım
eksikti.** Hakemin yerine koyduğu argüman doğru: %63 gözlem vs %57,9 null,
n=114 → **z=1,10, p≈0,27 — anlamsız.** POST_SL_REENTRY yine ölü, ama doğru gerekçeyle.

## 2. Hakemin kök-neden bulgusu (ufuk varsayımı) GERÇEK — ama önerdiği düzeltme yanlı

"4,8× fark"ın kaynağını doğru buldular: benim/onların simülasyonu işlemi botun
kapattığından çok daha uzun tutuyor. Ama çözüm olarak koydukları **"botun gerçek
kapanışında kes"** yöntemi, TP değişikliğini ölçmek için **yapısal olarak yanlı**:

> İşlemlerin **%59'u (165/282) orijinal TP'sini vurarak kapandı.** O ana kadar
> kesince büyütülmüş TP'ye zaten ulaşılamaz — büyütmenin faydası tanım gereği silinir.

Ölçtüm — capping herkesi kırpıyor ama büyük hedefi orantısız kırpıyor:

| TP | capped | serbest | kayıp |
|---|---:|---:|---:|
| orijinal | +2.710 | +3.425 | −%21 |
| 2,5×ATR15 | +1.046 | +2.898 | **−%64** |
| 4,0×ATR15 | +4.037 | +7.322 | −%45 |

Yani capped yöntem hakemin kendi "TP büyütme = gürültü" hükmünü üretmeye
meyilli. Tarafsız hakem değil.

## 3. DÜRÜST TEST — ikimizin de yapmadığı: slot-farkındalı simülasyon

Asıl fırsat maliyeti capping değil, **`MAX_OPEN_PER_SCOPE=1`**: büyük TP = uzun
tutuş = sonraki sinyal bloklanır. Sinyalleri kronolojik işleyip slot doluysa
atlayarak:

| TP | açılan | atlanan | USD |
|---|---:|---:|---:|
| orijinal | 272 | 10 | +1.425 |
| 2,0×ATR15 | 274 | 8 | −1.350 |
| 2,5×ATR15 | 263 | 19 | +70 |
| 3,0×ATR15 | 254 | 28 | +171 |
| 4,0×ATR15 | 239 | 43 | +1.449 |
| **5,0×ATR15** | 217 | 65 | **+5.588** |

**Hakemin "plato 2-3" bölgesi slot maliyeti altında çöküyor** (baz'ın altında).
Fayda yalnız 5×'te çıkıyor — ve orada sinyallerin %23'ü feda ediliyor.
Bu, önceki denetimimde 4 kronolojik çeyreğin 4'ünde de 5×'in pozitif çıkmasıyla
tutarlı (ve 6×'te çöküyordu → tepe ~5×).

## 4. Kendi zaafım (hakemin eleştirisi bana da uyuyor)

Slot-farkındalı sim'de **baz +1.425$, canlı gerçek +5.023$** — benim simülatörüm
bazı **3,5× eksik** gösteriyor (BUY'lardaki BE30+trail yönetimini modellemiyor,
2pt sürtünme yüklüyor). Hakemin sim'i +6.110$ ile fazla gösteriyordu.
**İkimizin simülatörü de canlıyı üretemiyor.** Bu yüzden ortak referans
simülatör önerileri doğru; büyüklük iddiaları (benimki dahil) askıda kalmalı.

## 5. Nihai tablo — hakemin listesine tek itiraz

| # | Bulgu | Ortak hüküm |
|---|---|---|
| 1 | Cuma ≥12 UTC blok | ✅ iki taraf doğruladı, plasebo geçti (p 0,013/0,015) → gölge |
| 2 | TP sonrası yön sürüklenmesi | ✅ iki taraf doğruladı (%59 / %60,5) |
| 3 | Export offset kırılganlığı | ✅ düzeltildi + canlı koruma yakaladı |
| 4 | R-kilit, POST_SL_REENTRY, zaman-aşımı, ladder | ✅ C — mezarlık |
| 5 | **TP büyütme** | ⚠️ **İTİRAZ: C değil, AÇIK SORU.** Hakem 2,5× ile test edip "gürültü" dedi; slot-farkındalı testte 2-4× gerçekten gürültü ama **5×'te +5.588 vs +1.425**. Kapatmak için erken. |

## Ders
Hakem raporu bu serinin en iyisi: kendi 5 icadından 3'ünü geri çekti, kök nedeni
buldu ve benim ispatımdaki gerçek kusuru yakaladı. Karşılığında ben de kabul
ediyorum: "matematiksel olarak imkânsız" demeden önce karşı tarafın geometrisini
sormalıydım. Kalan tek anlaşmazlık (TP büyütme) simülatör kalibrasyonuna bağlı
ve ancak canlı gölge ölçümüyle çözülür — zaten backlog'daki plan bu.
