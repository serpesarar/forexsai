# "Alfa Keşif" raporunun denetimi (dış AI, 2026-08-30)

**Motor:** 282 NAS100 işlemi + 100.000 adet 1m bar, sızıntısız, 2pt sürtünme
**Yer gerçeği:** canlı gerçekleşen P&L — Haz +646$ / **Tem 240 işlem +1.579$** /
**Ağu 42 işlem +2.799$** = +5.023$

## Karne: 5 iddianın 2'si doğru, 1'i matematiksel olarak imkânsız, 2'si üretilemedi

| # | İddia | Verdikt |
|---|---|---|
| 3 | Cuma ≥12 UTC bloğu | ✅ **DOĞRULANDI** |
| 5 | TP sonrası yön sürüklenmesi | ✅ **DOĞRULANDI** |
| 4 | SL sonrası "her iki yön de kazanıyor" | ❌ **ÖLÇÜM ARTEFAKTI** (kanıtlı) |
| 1 | R-kilit (1.0R→+0.25R) | ❌ üretilemedi (nötr/negatif) |
| 2 | k×ATR15 hedefi, "plato 2-3, 4'te çöküş" | ⚠️ yön doğru, sayılar ve plato üretilemedi |

---

## ✅ #3 — Cuma ≥12 UTC (raporun en güçlü bulgusu)

| | n | USD |
|---|---:|---:|
| Cuma tamamı | 40 | −4.002 |
| **Cuma ≥12 UTC** | **24** | **−4.050** |
| Cuma <12 UTC | 16 | +48 |

Rapor −4.091$ demişti; bağımsız ölçüm −4.050$. Rafinman doğru: hasarın tamamı
öğleden sonra. Bloklayınca kalan +8.340$ (filtresiz +4.290$).
**Plasebo p=0,0150 → GEÇTİ** (rapor p=0,013 demişti, tutarlı).
En kötü hücre Cuma 15 UTC: n=9, −3.557$ — raporun sayısıyla birebir.

⚠️ **Ama "yeni kural" değil:** bot'ta `TQ_FRIDAY_COOL=True` **ve**
`TQ_COOL_HOURS_UTC=(15,16,17)` zaten canlı. Bu 24 işlem o soğutmadan **geçmiş**
işlemler — yani soğutma (ek oy / decider onayı) yetmiyor. Soru "kural ekleyelim mi"
değil, **"soğutmayı bloğa yükseltelim mi"**. Ayrıca −3.557$'ın tek bir 9-işlemlik
hücreden gelmesi, örneklemin ne kadar ince olduğunu gösteriyor.

## ✅ #5 — TP sonrası yön sürüklenmesi

Doğru yöntemle (ilk-dokunuş, ±1R simetrik bariyer):
**aynı yön 98/162 = %60,5** · ters yön %39,5 · toplam %100 ✓
z≈2,67 → **p≈0,008**. Gerçek bir yönlü kenar; canlı REENTRY scope'unun
arkasındaki mekanizma bu. Raporun "TP+5dk sihirli değil, ~2 saatlik pencere var"
yorumu makul.

## ❌ #4 — "SL sonrası her iki yön de kazanıyor" — ARTEFAKT

Rapor: aynı yön %63 **ve** ters yön %63 → "alfa yönde değil volatilitede".

**Bu matematiksel olarak imkânsız.** Simetrik ±1R bariyerlerde uzun ve kısa
birbirinin tümleyenidir: P(uzun kazanır) + P(kısa kazanır) = 1. %63+%63=%126.

İki yöntemi de koşturdum:

| yöntem | aynı yön | ters yön | toplam |
|---|---:|---:|---:|
| **İlk dokunuş (doğru)** | **%50,0** | **%50,0** | %100 ✓ |
| "Hiç dokundu mu" (MFE) | %67,5 | %66,7 | **%134,2** ❌ |

Raporun %63/%63'ü MFE yöntemini yeniden üretiyor. Doğru ölçümde **tam yazı-tura**:
kenar YOK. `POST_SL_REENTRY` adaylıktan düşürülmeli.

## ❌ #1 — R-kilit üretilemedi

| varyant | orijinal TP | TP=2,5×ATR15 |
|---|---:|---:|
| kilit yok (baz) | +3.425 | +2.898 |
| **1.0R → +0.25R (öneri)** | +3.475 (**+50**) | **+2.561 (−337)** |
| 1.0R → 0.0R (klasik BE) | +3.725 | +2.519 |
| 0.75R → +0.25R | +3.068 | +781 |

Raporun manşeti "+3.958$" idi; bende orijinal TP'de **+50$ (gürültü)**,
2,5×ATR'de **−337$ (zararlı)**. Yalnız *şekil* uyuşuyor (erken kilit kötü).

## ⚠️ #2 — TP büyütme: yön doğru, sayılar değil

| TP | Temmuz (ben) | Ağustos (ben) | Temmuz (rapor) |
|---|---:|---:|---:|
| orijinal | −172 | +2.817 | +2.185 |
| 3,0×ATR15 | +1.023 | +3.074 | **+13.390** |
| 4,0×ATR15 | **+4.051** | +3.115 | **−2.996** |

Rapor 3,0×'te Temmuz'da +13.390$ diyor — ama **Temmuz'un tüm gerçekleşen kârı
240 işlemde +1.579$**. Ayrıca rapor 4,0×'te çöküş görüyor, bende 4,0× en iyi;
yani "plato 2-3" dayanıklı değil, simülatöre bağlı.

**Kök sorun — simülatör kalibrasyonu:** raporun bazı +6.110$, canlı gerçek
+5.023$ (sürtünme yokmuş gibi, %22 iyimser). 2,5×ATR varyantında baz olarak
13.814$ alıyor; ben aynı varyantta +2.898$ buluyorum. Bu 4,8× fark, "icat"
büyüklüklerinin neden üretilemediğini açıklıyor.

**Raporun kendi dürüstlük notu da yanlış yönde:** "Δ'nın %90'ı Temmuz'dan"
diyor; yer gerçeğinde Temmuz **zayıf** ay (240 işlem +1.579$), Ağustos güçlü
(42 işlem +2.799$).

## Sonuç
Rapor önceki turlardan **belirgin şekilde daha iyi** (plasebo kullanıyor, ölü
fikirleri listeliyor, dürüstlük bandı koyuyor) ve iki gerçek bulgu içeriyor
(#3, #5). Ama simülatörü canlıya kalibre edilmemiş ve #4'te temel bir
olasılık hatası var. **Canlıya alınacak hiçbir şey yok**; #3 için mevcut
soğutma→blok yükseltmesi ölçülmeli (zaten backlog'da), #5 mevcut REENTRY'yi
açıklıyor ve pencere gevşetmesi ayrıca sınanabilir.
