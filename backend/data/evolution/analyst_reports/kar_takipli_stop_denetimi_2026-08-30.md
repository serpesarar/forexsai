# Kullanıcı fikri: "TP'nin %50'sine ulaşınca, zirvenin yarısına kâr-stop" — denetim

**Tarih:** 2026-08-30 · **Veri:** 282 NAS100 işlemi + 100.000 adet 1m bar
(doğrulanmış eksen: lag=0'da %99,6 bar içi) · **Sürtünme:** 2 puan
**Bar içi kural (muhafazakâr):** (1) önceki bardan gelen stop, (2) TP,
(3) EN SON zirve güncelle → "trail yukarı kaçtı sonra iyi fiyattan doldu" iyimserliği yok.

## Sonuç: kural SL'leri gerçekten önlüyor, ama kazananları daha çok kesiyor

| | USD | WR | TP | SL | trail |
|---|---:|---:|---:|---:|---:|
| BAZ (düz TP/SL) | **+3.425** | %60,3 | 169 | 110 | — |
| **Kullanıcı kuralı** | **−1.681** | **%73,4** | 56 | 74 | 150 |
| fark | **−5.106** | +13,1 pp | | | |

## Mekanizma — sorunun tam cevabı

| geçiş | adet | USD etkisi |
|---|---:|---:|
| **SL → trail (kurtarılan)** | **36 / 110** | **+21.630** ✅ |
| **TP → trail (kırpılan)** | **113 / 169** | **−27.130** ❌ |
| timeout → trail | 1 | +395 |
| **NET** | | **−5.106** |

**Evet, SL'leri önlüyor:** 110 kaybeden işlemin **36'sı (%33) kâra dönüyor**,
değeri **+21.630$**. Kazanma oranı %60,3 → **%73,4** çıkıyor.
**Ama:** 169 kazananın **113'ü (%67) TP'ye varmadan kesiliyor**, bedeli −27.130$.

Kök sebep geometri: tetik anında MFE = 0,5×D olduğunda stop giriş+0,25×D'ye
oturuyor. NASDAQ'ın dakikalık gürültüsünde fiyatın 0,25×D geri çekilmesi,
kalan 0,5×D'yi katedip TP'ye varmasından **daha olası**.

⚠️ Bu, bu projede defalarca görülen **"kozmetik WR"** imzasının bir örneği daha:
kazanma oranı 13 puan yükselirken para 5.106$ azalıyor.

## Parametre taraması (USD, baz +3.425)

| tetik \ zirve oranı | %30 | %50 | %70 | %90 |
|---|---:|---:|---:|---:|
| %30 | −3.557 | −941 | −128 | +3.482 |
| **%50 (öneri)** | −2.092 | **−1.681** | −1.207 | +3.058 |
| %60 | +281 | +312 | −183 | +2.898 |
| **%70** | +1.745 | +1.241 | +955 | **+3.767** |
| %80 | −1.209 | −958 | −847 | +695 |

Hiçbir hücre bazı anlamlı geçmiyor. En iyi (%70 tetik + %90 zirve = "TP'ye çok
yaklaşınca çok sıkı takip") **+3.767 vs +3.425 = +342$ (gürültü)** — ve zaten
davranış olarak "TP'yi al"a yakınsıyor.

## Dayanıklılık: kural bir SİGORTA, kâr motoru değil

| dilim | baz | kural | fark |
|---|---:|---:|---:|
| Temmuz (n=238) | −172 | −4.119 | −3.947 |
| Ağustos (n=42) | +2.817 | +2.250 | −567 |
| Çeyrek 1 | +3.289 | +1.822 | −1.467 |
| Çeyrek 2 | +825 | −3.250 | −4.075 |
| **Çeyrek 3** | **−3.442** | **+14** | **+3.456** ✅ |
| Çeyrek 4 | +2.752 | −267 | −3.020 |

4 çeyreğin **yalnız birinde** artı — ve o çeyrek bazın en kötü olduğu dönem.
Yani kural **kötü dönemde koruyor, iyi dönemde bedel ödetiyor**: klasik sigorta
profili. Risk metrikleri de bunu söylüyor: işlem std'si 446 → 345 (volatilite
düşüyor) ama beklenti negatife dönüyor.

## Karşılaştırma

| varyant | USD | WR | std | maxDD |
|---|---:|---:|---:|---:|
| BAZ | +3.425 | %60,3 | 446 | −8.538 |
| Kullanıcı kuralı | −1.681 | %73,4 | 345 | −10.385 |
| Sadece başabaş (%50'de SL=giriş) | −1.631 | %38,7 | 369 | −11.569 |
| %70 tetik + %90 zirve | +3.767 | %67,7 | 384 | **−5.910** |

Not: kullanıcı kuralı volatiliteyi düşürüyor ama **maksimum düşüşü
iyileştirmiyor** (−8.538 → −10.385), çünkü kesilen kazançlar toparlanmayı
yavaşlatıyor. Tek gerçek maxDD iyileşmesi %70/%90 varyantında (−5.910).

## Hüküm
**Canlıya alınmaz.** Fikir mekanik olarak çalışıyor (SL'lerin üçte birini
kurtarıyor) ama bu geometride kazanandan aldığı, kaybedene verdiğinden fazla.
Yön doğru olsaydı tarama bir plato gösterirdi; göstermiyor.

Yararlı kalıntı: **%70 tetik + %90 zirve** varyantı beklentiyi bozmadan
(+342$, gürültü) maksimum düşüşü **−8.538 → −5.910** iyileştiriyor. Kâr
hedefiyle değil, **risk azaltma** hedefiyle bakılırsa ölçülmeye değer —
ama o da ayrı bir gölge işi.
