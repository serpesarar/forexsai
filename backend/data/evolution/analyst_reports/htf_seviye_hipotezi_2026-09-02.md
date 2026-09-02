# Kullanıcı hipotezi: "HTF destek/direnç yakınında kırılım doğrulanmadan girme"

**Tarih:** 2026-09-02 · **Veri:** 282 tarihsel NAS100 işlemi + bu haftanın 8 işlemi
+ 113.000 adet 1m bar · sızıntısız (yalnız girişten önce kapanmış barlar)

## Hipotez
> Bot 1m/5m kapanışıyla kırılım tespit edip giriyor; sonra fiyat M15/M30'daki
> 30-40 bar önceki bir destekten dönüp ters yöne gidiyor. M30/H1 seviyelerini
> (100 bar) belirleyip 40-50 puan ötesinde kapanış olmadıkça girme.

## VERDİKT: sinyal gerçek ama işe yaramıyor — canlıya ALINMADI

### 1. Yön doğru, güç yetersiz
Girişin önündeki en yakın HTF seviyesine mesafe:
**SL işlemleri medyan 36,6 puan · TP işlemleri 44,1 puan.**
Yani SL'ler gerçekten seviyeye daha yakın açılıyor — gözlem doğru. Ama fark küçük.

### 2. Önerilen mesafe kuralı para kaybettiriyor
"Önünde D puandan yakın seviye varsa açma":

| D | kalan USD | | D | kalan USD |
|---|---:|---|---|---:|
| 10 | +5.720 | | **40** | **+3.845** |
| 20 | +833 | | **50** | **+2.332** |
| 30 | −193 | | 60 | +3.096 |
| — | | | filtresiz | **+4.290** |

Eğri düzensiz (plato yok) ve **kullanıcının önerdiği 40-50 puan bandı bazın
altında.** Elenen kümeler D=20/30'da POZİTİF (+3.457/+4.483) — kârlı işlem eliyor.

### 3. Rafine sürüm: in-sample MÜKEMMEL, out-of-sample ÇÖKTÜ
Fikre en iyi şansı vermek için 27 varyant denendi (M15/M30/H1 × 30/50/100 bar ×
1/2/3 dokunuş). Kural "giriş ile TP arasında ≥2 dokunuşlu seviye varsa açma".

**Tarihsel veride her testi geçti:**
* plato: "≥2 dokunuş"un **9/9 hücresi** bazı geçiyor (+4.616…+8.298), elenen
  kümelerin **9/9'u negatif**
* hafta-çıkarma: **9/9**
* permutasyon: kalan ortR +0,076 vs elenen −0,434 → **p=0,0033**
* aile: 3 iyileşme, 2 nötr, 0 kötüleşme
* en iyi (M15/50/≥2): 23 işlem eler (−4.009$), kalan **+8.298$** vs baz +4.290$

**BU HAFTA (kural geliştirilirken hiç kullanılmadı) — tam tersi:**

| zaman | sonuç | USD | kural |
|---|---|---:|---|
| 09-01 14:06 | SL | −352 | geç |
| 09-01 14:34 | TP | +400 | **ENGELLE** |
| 09-02 07:13 | TP | +400 | **ENGELLE** |
| 09-02 08:53 | SL | −549 | geç |
| 09-02 09:12 | SL | −300 | geç |
| 09-02 11:44 | SL | −297 | geç |
| 09-02 12:30 | TP | +400 | **ENGELLE** |

Engellediği **3 işlemin 3'ü de TP** (+1.199$); geçirdiği kümede **4 SL'in dördü de var**.
Filtreli −1.094$ vs filtresiz +105$. Kural, çözmesi istenen SL'lerin **hiçbirini**
engellemiyor.

Ayrıca 27 kombinasyon denendiği için Bonferroni: p = 0,0033 × 27 = **0,089** (>0,05).

### 4. Alternatif hipotez de çürüdü
Bu haftanın SL'leri gün-içi konumla açıklanıyor gibiydi (SL ort. konum 0,20 vs
TP 0,47; en büyük kayıp tam günün dibinde). Tarihsel 221 SELL'de **tersine dönüyor**:
SL medyan konum **0,432**, TP **0,363**. Her eşikte kalan küme bazın altında.

⚠️ Ama bu mekanizma zaten botta var ve **çalışıyor**: mevcut konum kapısı
**4 saatlik** dalga penceresi kullanıyor (`POS_SELL_MIN=0,40`) — elediği 97 işlem
−1.015$, kalan +5.304$ (baz +4.290$). Yani doğru pencere gün değil, 4 saat.

## Sonuç
Bu haftanın 4 SL'i (−1.498$) normal varyans içinde: hafta NAS100'de net **+105$**
kapandı, üstüne +134$'lık açık pozisyon var. İki farklı hipotez de — HTF seviye ve
gün-içi konum — dış-örneklemde çöktü.

**Ders:** rafine kural in-sample'da plato + 9/9 hafta + p=0,003 verdi ve yine de
yeni veride ters döndü. İç-örneklem dayanıklılık testleri (plato, leave-one-out,
permutasyon) **gerçek dış-örneklemin yerini tutmuyor.** Bu oturumun üçüncü kez
doğruladığı kural: yeni veri gelene kadar hiçbir şey kanıtlanmış sayılmaz.
