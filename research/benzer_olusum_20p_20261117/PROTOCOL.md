# Benzer oluşum taraması — 20 puan TP/SL, rastgele giriş (ÖN KAYIT, 2026-11-17)

Kullanıcı: "TP-SL'yi 20 pipse çek; her gün 10 rastgele giriş, BUY ve SELL; hangi yönde TP olmuşsa o alanı analiz et, o oluşumun benzer
yapılarını geçmiş mum grafiğinde tara, diğer oluşumlarda da aynı yapı var mı, aynı TP'ye gidiyor mu tespit et."
Veri: Dukascopy NDX BID 1m 2018-01 → 2026-11 (ask = BID + spr). Defter: ME-02 (eşleşme tahmini = rastgele komşu, X), mum benzerlik tarayıcısı
(yön tabandan farksız), YL (yön X). Yeni olan: sabit 20 puanlık braket ve işlem başına "geçmiş benzerler aynı TP'ye gitti mi" sorusu.

## 1. Girişler (tohum 20261118)
Her işlem günü (NY tarihi, 18:00 önceki akşam → 16:15) 10 rastgele dakika, Dukascopy 16:15–18:00 boşluğu hariç. Her girişte iki ayrı işlem:
BUY = ask'tan al, TP bid ≥ giriş + 20, SL bid ≤ giriş − 20; SELL = bid'den sat, TP ask ≤ giriş − 20, SL ask ≥ giriş + 20. Azami tutuş 240 dk
(çözülmezse o anki fiyatla kapat). Aynı barda TP+SL → SL. Etiket W = BUY_TP / SELL_TP / YOK (her iki yönün sonucu ayrıca saklanır).
Not: 20 puan sabit — 2018'de (≈ 6.500) ≈ 31 bp, 2026'da (≈ 25.000) ≈ 8 bp; spread de puandır (1–4). Bu yüzden sonuçlar yıl yıl raporlanır.

## 2. Oluşum ve benzerlik
Oluşum = girişten önce kapanmış son 30 adet 1m mum: her mumun (açılış, tepe, dip, kapanış) − son kapanış, **puan** cinsinden (20 puanlık hedefle
aynı ölçek) → 120 boyut. Uzaklık = Öklid (puan). Benzerler **yalnız geçmişten**: sorgudan en az 1 gün önce girilmiş ve sonucu kapanmış girişler.
K = 20 en yakın (ikincil K = 50).

## 3. Sorular ve geçme ölçütleri
- S1 **Benzerler aynı TP'ye gidiyor mu?** Her TP olmuş giriş için, K geçmiş benzerin aynı yönde TP oranı vs aynı dönemde K rastgele geçmiş girişin
  oranı (plasebo, 200 tekrar). Fark ve P raporlanır; dönemler BAĞIMSIZ 2018–21 / KEŞİF 2022–23 / TEST 2024–26.
- S2 **İşlem kuralı (yalnız geçmiş benzerler):** benzerlerin BUY_TP oranı − SELL_TP oranı ≥ +0,30 → BUY; ≤ −0,30 → SELL; arada işlem yok.
  Ölçü: net puan/işlem (spread dahil), isabet (başabaş ≈ %50 + spread etkisi), yıl tablosu. Plasebo: aynı sayıda rastgele geçmiş komşuyla aynı kural.
  Geçer: üç dönemde net > 0 ∧ TEST ve BAĞIMSIZ'da P ≥ 0,90 ∧ plasebo dağılımının %95'inin üstünde ∧ spr×1,5 > 0.
- S3 (bilgi) "En tutarlı oluşumlar": benzerlerinin aynı yönde TP oranı ≥ 0,70 olan oluşum kümeleri ileride (sonraki dönemde) de tutuyor mu.
