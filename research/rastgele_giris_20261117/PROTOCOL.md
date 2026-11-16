# Rastgele giriş → sonraki yapı → ortak ön özellik (ÖN KAYIT, 2026-11-17)

Kullanıcı: "Tüm 1 dakikalık grafikte her gün için 10 rastgele giriş noktası belirle, New York, Asya ve diğer seanslarda eşit dağıt; girişlerden sonraki
genel yapıları incele; bu yapılarda geçmişte ve gelecekte ortak bir özellik var mı, strateji biçimi ara."
Veri: Dukascopy NDX BID 1m 2018-01 → 2026-11 (`research/ndx_10y_1m_20261116` motoru, ask = BID + spr).
Defter: GF-01 (rastgele girişte tek özellikli durum kapısı X), YL-03 (15 dk dönüş, maliyetin altında), NOM (oynaklık A, yön X).
Yeni olan: seans dengeli örnekleme ve hedefin yalnız yön değil **sonraki yapı tipi** olması.

## 1. Örnekleme (sabit tohum 20261117)
Her işlem günü (NY tarihi) için üç seans, seans başına **10** rastgele dakika (kullanıcının "her gün 10" isteği seans başına uygulanır,
böylece seanslar eşit ağırlıkta): ASYA 18:00 (önceki akşam) – 02:59 ET, AVRUPA 03:00 – 09:29, NY 09:30 – 15:59. Giriş = seçilen dakikanın
açılışı. Ufuk 60 dk (seans sınırını aşabilir; 16:15–18:00 boşluğuna düşenler atılır).

## 2. Sonuç etiketleri (girişten SONRA)
Birim U = 4 × a60 (a60 = önceki 60 barın ortalama 1m aralığı; ≈ 15 dk'lık hareket ölçeği).
- YÖN: ±1U simetrik yarış (önce +U → +1, önce −U → −1, 60 dk'da hiçbiri → 0; aynı bar → 0).
- YAPI: TREND = |r60| ≥ 2U; KARARSIZ = hem +U hem −U'ya değdi ∧ |r60| < U; SAKİN = 60 dk aralığı < 1,5U; diğer = ARA.
## 3. Ön özellikler (yalnız giriş dakikasından ÖNCE kapanmış barlar, 26 adet)
Mum anatomisi: CLV son 1/5/15/60 bar ort., üst/alt fitil payı son 5/15, ardışık aynı renk dizisi, gövde/aralık son 5, renk değişim oranı son 15.
Bağlam: r5/r15/r60/r240 (U birimi), son 60 barın aralığı/U, a60/a1440 (oynaklık rejimi), seans içindeki konum (seans tepe/dip arası),
önceki NY kapanışına uzaklık (U), dakika-of-seans, seans kodu, haftanın günü, dünkü VIX.
## 4. Analiz ve geçme ölçütleri
Dönemler: KEŞİF 2022–23, TEST 2024–26, BAĞIMSIZ 2018–21.
- A1 **Ortak özellik:** her özellik için kazanan (YÖN = +1) vs kaybeden (−1) standart fark (Cohen d) ve TREND vs KARARSIZ farkı; "ortak" = üç dönemde
  aynı işaret ∧ |d| ≥ 0,05 ∧ en küçük dönem |t| ≥ 3 (maxT için 26 özellik). Plasebo: etiketleri gün içinde karıştır (200).
- A2 **Model:** HistGradientBoosting (KEŞİF'te eğit), TEST ve BAĞIMSIZ'da AUC; YÖN (+1 vs −1) ve TREND vs diğer. Şans tabanı: karıştırılmış
  etiketle AUC dağılımı (%95). Geçer: AUC her iki dönemde şans %95'inin üstünde.
- A3 **Kural:** A2'de geçen hedef için KEŞİF'te sabitlenen olasılık eşiği (üst %10) → işlem: YÖN modeli için tahmin yönünde ±1U braket, 60 dk;
  TREND modeli için "trend bekleniyorsa r15 yönünde, değilse r15 tersine" ±1U braket. Net bp ve R (spread dahil), spr×1,5, üç dönem.
  Geçer: R > 0 TEST ve BAĞIMSIZ'da ∧ P ≥ 0,90 ∧ aynı saat/seans rastgele işlem tabanından iyi. Geçerse 2. KURAL kartı.

## EK-1 (2026-11-17, A1–A3 sonuçlarından SONRA, koşulmadan önce yazıldı) — trend olasılığı × ORB × VIX
A2: yön öngörülemiyor (AUC 0,505/0,516) ama sonraki yapı tipi (TREND) güçlü öngörülüyor (AUC 0,684/0,695; çoğu oynaklık rejimi + seans zamanı);
A3: trend beklenen anda momentum −0,08…−0,13R. Bilginin doğal kullanımı yön değil, kırılım stratejisinin ne zaman çalıştığı.
Soru: KEŞİF'te eğitilmiş TREND modeli, ORB × VIX (TP 3R, canlı) girişlerinde p_trend'i hesaplar; p_trend tertilleri (eşikler rastgele
girişlerin KEŞİF NY dağılımından) ile R. Öngörü: yüksek p_trend → daha iyi R. Geçer: ESKİ (2018-21) ve YENİ (2021-11→) dönemlerinde
yüksek − düşük > 0 ∧ havuz P ≥ 0,90 ∧ kitap dozu (yüksek ×1,5 / düşük ×0,5, ortalama sabit) iki dönemde aylık Sharpe'ı artırır.
