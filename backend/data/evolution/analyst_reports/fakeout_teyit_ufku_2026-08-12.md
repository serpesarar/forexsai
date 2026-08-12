# Kırılım dedektörü — teyit ufku (+1 bar mı, +20 bar mı?) + veri onarımı

**Tarih:** 2026-08-12 · **Betik:** `backend/research/fakeout_confirm_horizon.py`
**Soru (kullanıcı):** "Dedektör bir sonraki muma bakarak teyit almasın, sonraki
20 muma bakarak alsa sonuçlar nasıl değişir?"

---

## 1. Cevap: 20 bar beklemek YAPISAL OLARAK mümkün değil

Dedektörün etiketi ±1×ATR yarışıdır (kırılım gerçek mi, sahte mi). K bar
beklerken o yarışın büyük kısmı **zaten bitmiş** olur — kalanı "tahmin" değil
"gözlem"dir (üretimdeki `resolved_observed` aşamasının gölge takipçiden
dışlanma sebebi de bu).

NDX, 847 etiketli olay (onarılmış veri, 2026-02-24 → 08-07):

| K (bar) | dakika | yarışı hâlâ açık | kapsam | o kümede taban sahte |
|---|---|---|---|---|
| 1 | 5 | 587 | %69,3 | %51,6 |
| 2 | 10 | 373 | %44,0 | %53,1 |
| 3 | 15 | 252 | %29,8 | %52,8 |
| 4 | 20 | 191 | %22,6 | %55,5 |
| 6 | 30 | 115 | %13,6 | %54,8 |
| 8 | 40 | 76 | %9,0 | %50,0 |
| 12 | 60 | 50 | %5,9 | %46,0 |
| **20** | **100** | **32** | **%3,8** | %53,1 |

**K=20'de olayların yalnız %3,8'i hâlâ karara açık (n=32).** Bu küme
train/val/test bölmesine bile yetmiyor — eşik üretilemiyor. Yani "20 muma bakıp
teyit al" kuralı, olayların %96'sında karar anını kaçırmak demek.

## 2. İsabet — kullanılabilir K aralığı 2–3

Hâlâ açık kümede, K barlık dalga özellikleriyle (kronolojik train/val/test,
eşik VAL'de):

| K | aksiyon kümesi | SAHTE kesinliği | GERÇEK kesinliği |
|---|---|---|---|
| 1 | 587 (%69) | eşik çıkmadı | %59,3 (n=113, kaps %64,6) |
| 2 | 373 (%44) | eşik çıkmadı | %66,0 (n=50, kaps %45,5) |
| 3 | 252 (%30) | **%70,0** (n=40, kaps %52,6) | %56,6 (n=53, kaps %69,7) |
| ≥4 | ≤191 | örneklem yetersiz — ölçülemedi | — |

Aynı kümede +1-bar özellik seti karşılaştırması K=2 ve K=3'te eşik bile
üretemedi; yani beklemenin bir faydası var, ama **K=3'te tavan yapıyor ve
bedeli kapsamın %30'a düşmesi.**

## 3. ⚠️ Yan bulgu: dedektörün eğitim etiketleri kısmen bozuktu

`candle_cache` 1m serisi 2026-05-07 öncesinde broker saatinde (UTC+3)
etiketlenmiş; 5m serisi gerçek UTC (bkz. 2026-07-28 bulgusu). Yarış etiketi 1m
ile üretildiği için **onarılmadan koşan her fakeout çalışması yanlış zaman
penceresinde etiketlemiş** olur.

Bu koşuda 1m −3 saat kaydırıldı ve gün bazında 5m ile tutarsız günler atıldı:
**158 günün yalnız 67'si temiz** (91 gün atıldı). Temiz pencerede olay sayısı
847 — Temmuz'daki lab ~1.400 olayla çalışıyordu, yani o çalışmanın veri
tabanının kabaca yarısı kaymış eksenle etiketlenmişti.

Bu, canlı gölge karnesiyle laboratuvar arasındaki farkı da açıklıyor olabilir:
lab NDX'te SAHTE %70 / GERÇEK %83 diyordu; gölge takipçide NDX SAHTE çağrısı
**%40 (n=20)**, tüm semboller %57.

**Öneri:** `model_fakeout_ndx_5m.joblib` + `fakeout_rules.json` eşikleri
onarılmış veriyle yeniden üretilmeli (`fakeout_lab.py` → `fakeout_finalize.py`),
diğer 3 sembol de aynı denetimden geçmeli. Yeniden üretilene kadar dedektör
çıktısı "kanıtı yeniden doğrulanacak" etiketiyle okunmalı.

## 4. Sonuç

- 20 bar teyidi **uygulanabilir değil** — karar penceresi kapanıyor.
- Üretimdeki akış (+1 bar → +2 bar dalga) zaten bu tavanın içinde; K=3'e
  çıkarmak SAHTE tarafında kesinliği artırabilir ama kapsamı %30'a düşürür.
- Asıl iş K'yı büyütmek değil: **etiketleri onarılmış veriyle dedektörü
  yeniden eğitmek.**
