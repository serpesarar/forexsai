# Konum kapısı deneyleri: eşik, pencere, kapsam + sistemin HTF körlüğü

**Veri:** 282 tarihsel NAS100 işlemi + bu haftanın 8 işlemi + botun kendi
946 kayıtlık gölge ölçümü · sızıntısız

## 0. Kullanıcının sorusu: "sistem eski/üst-TF seviyelere bakıyor mu?"

**HAYIR — gerçek bir kör nokta var.** Giriş yolunda kullanılan zaman dilimleri:

| bileşen | TF × bar | ne görüyor |
|---|---|---|
| **Giriş S/R bölgeleri** (`detect_zones`) | **1m × 100 (~1,7 saat)** | **tek gerçek seviye tespiti** |
| Konum kapısı (`entry_position`) | 5m × 48 (4 saat) | yalnız aralık tepe/dip, pivot DEĞİL |
| Trend hizası | 1h EMA50 × 60 | yön, seviye değil |
| Sahte-kırılım vetosu | 5m × 400 (~33 saat) | en geriye bakan bileşen |
| CHREV | 30m regresyon kanalı × 60 | kanal, pivot değil |

M15/M30/H1 **pivot destek-direnç seviyeleri hiç kontrol edilmiyor.**
(Ama bu boşluğu doldurma denemesi ayrı raporda dış-örneklemde çöktü:
`htf_seviye_hipotezi_2026-09-02.md`.)

## 1. Doğrudan cevap: 0,40 → 0,50 ne yapıyor? **KÖTÜLEŞTİRİYOR**

Kapılı ailelerde (MOM/SR + VIXREG), 4 saatlik pencere:

| eşik | tüm sistem USD |
|---|---:|
| 0,40 (mevcut) | +5.704 |
| 0,45 | +5.742 |
| **0,50** | **+5.193** ← düşüş |
| 0,55 | +7.430 |
| 0,60 | +7.258 |
| 0,70 | +5.850 |

**0,50 bir çukur.** Yüzey monoton değil — bu, gürültüye uyum sinyali.

## 2. Pencere × eşik ızgarası (20 hücre)

| pencere \ eşik | 0,40 | 0,50 | 0,60 | 0,70 |
|---|---:|---:|---:|---:|
| 2 saat | 2.102 | 853 | 3.548 | 3.088 |
| 4 saat | 5.304 | 4.391 | 7.006 | 6.699 |
| **6 saat** | 6.087 | 6.461 | **8.401** | 8.154 |
| 8 saat | 4.955 | 5.233 | 6.074 | 7.454 |
| 12 saat | 2.152 | 2.143 | 7.072 | 6.794 |
| filtresiz | **4.290** | | | |

Yön tutarlı: **yüksek eşik + geniş pencere daha iyi.** En iyi 6s/0,60.

## 3. Ayrıştırma: kazanç nereden?

| varyant | tarihsel | bu hafta |
|---|---:|---:|
| MEVCUT 4s/0,40 (MOM+VIXREG) | +5.704 | +405 |
| **6s/0,60, kapsam AYNI** | **+9.203** | +650 |
| kapsam TÜM, eşik aynı | +5.304 | +954 |
| 6s/0,60 + kapsam TÜM | +8.401 | +1.199 |

**Kazancın tamamı VIXREG'den** (211 işlem, +3.292 → +8.205). Kapsam genişletmek
REENTRY'de **−802$ zarar** veriyor. Yani doğru hamle kapsam değil, parametre.

## 4. Bu hafta (gerçek dış-örneklem): kural İŞE YARIYOR

6s/0,60 bu haftanın **4 SL'inin dördünü de** engelliyor, 4 TP'nin 3'ünü geçiriyor:
filtreli **+1.199$** vs filtresiz +105$. (Sizin sorduğunuz SL'ler tam olarak bunlar.)

## 5. ⚠️ AMA botun KENDİ gölge ölçümü çelişiyor

Bot `POS_TIGHT_SELL_MIN=0,60`'ı zaten gölgede ölçüyor. 946 kayıt, NDX SELL'de 59:

| | değer |
|---|---:|
| ort MFE (lehte hareket) | **28,5 puan** |
| ort MAE (aleyhte hareket) | 20,9 puan |
| MAE>MFE (kapı haklı) | 29/59 = **%49,2** (yazı-tura) |

**Bloklanacak sinyaller ortalama LEHTE hareket etmiş.** Bu, backtest'imin tersi.

⚠️ Ama bu ölçüm de kusurlu: takip penceresi **yalnız 10 bar** — TP'si 80,
SL'i 110 puan olan bir işlemi çözmeye yetmez. Yani gölge verisi kapıyı
çürütmüyor, sadece **doğrulamıyor.**

## 6. Hüküm: canlıya ALINMADI

| kanıt | yön |
|---|---|
| 282 işlemlik backtest (+9.203 vs +4.290) | ✅ lehte |
| bu hafta OOS (4/4 SL engellendi, +1.199 vs +105) | ✅ lehte |
| botun 59 kayıtlık gölge ölçümü (MFE>MAE) | ❌ aleyhte |
| Bonferroni (20 hücre, p=0,024 → 0,48) | ❌ geçemiyor |
| davranış değişikliği: VIXREG'in **%68'i** bloklanır | ⚠️ çok büyük |

VIXREG botun ana motoru (282 işlemin 211'i). %68'ini kesmek parametre ayarı
değil **stratejik değişiklik**. Çelişen kanıtla ve Bonferroni geçilmeden
yapılmaz.

## 7. Somut sonraki adım (ölçüm altyapısı düzeltmesi)

Gölge takip penceresi 10 bar → işlemin gerçek TP/SL geometrisiyle çözülmeli
(1m replay, tıpkı `gate_audit` gibi). O düzeltilirse `POS_TIGHT` için
gerçek bir karne çıkar ve bu tartışma kanıtla kapanır. **Backlog'a eklendi.**
