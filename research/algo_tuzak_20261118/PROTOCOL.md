# Ön kayıt — "Algoları ters köşeye yatıran" tuzak yapıları, son 5 yıl odaklı (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "son 5 yılda yapay zekâ ve algo trading ile yapı değişti; balinalar önce kazandırır, sonra
tersine çevirip algoları ve işlem açanları ters bırakır; onların sistemine karşı işlem türet."

## Dönemler (yapı değişimi hipotezi)
- **ESKİ YAPI** 2018-04 → 2021-10 (yalnız karşılaştırma; seçimde kullanılmaz).
- **KEŞİF** 2021-11 → 2024-06 (seçim). **TEST** 2024-07 → 2026-11 (kör).
Veri: NDX Dukascopy 1m (ana); MT5 NAS100 M30 (TEST döneminde bağımsız teyit). Maliyet: giriş/çıkış barı spread'i.

## Hipotezler (önceden tanımlı yön = TUZAK/DÖNÜŞ; ayna "devam" bilgi olarak raporlanır)
σ = aynı ölçünün önceki 20 gündeki standart sapması (karar günü hariç).
- **T1a** sabah trendi: R = P(12:00)/P(09:30) − 1, |R| ≥ k·σ → 12:00'de R'nin tersine gir, 16:00'da çık. k ∈ {1, 1,5}.
- **T1b** aynısı 13:00 (R = 09:30 → 13:00). k ∈ {1, 1,5}.
- **T2** açılış itmesi: R = P(10:00)/P(09:30) − 1, |R| ≥ k·σ → 10:00'de ters; çıkış 11:30 veya 16:00. k ∈ {1, 1,5} → 4 hücre.
- **T5** kapanış saati: R = P(15:00)/P(09:30) − 1, |R| ≥ k·σ → 15:00'te ters, 16:00'da çık. k ∈ {1, 1,5}.
- **T3** kırılım tuzağı: 10:00–14:00 arası fiyat önceki günün nakit seansı tepesini (PDH) ≥ %0,1 aşar ve 30 dk içinde 1m kapanış PDH
  altına döner → sonraki 1m açılışında SAT, 16:00'da çık. Ayna: PDL aşağı kırılıp 30 dk içinde geri alınırsa AL. Günde yön başına bir. 2 hücre.
  Taban: aynı yön, aynı günlerde 10:00–14:30 rastgele dakikada giriş.
- **T4** sakin ralli tuzağı: 10 günlük getiri ≥ +%4 ∧ 10 günlük gerçekleşen oynaklık önceki 250 günün alt üçte birinde → 16:00'da SAT,
  5 / 10 işlem günü sonra 16:00'da kapat (finansman düşülür). 2 hücre. Taban: tüm günlerde aynı ufukta SAT.
Toplam 14 hücre.

## Seçim (yalnız KEŞİF)
n ≥ 30, net ort > 0, ort > taban (T1/T2/T5 tabanı 0, yani yönsüz), gün-küme P ≥ 0,90 → t'ye göre en iyi ≤ 4 hücre dondurulur.

## Doğrulama
1. TEST: net ort > 0 ∧ P ≥ 1 − 0,10/4 = 0,975.
2. MT5 NAS100, TEST döneminde: net ort > 0 (T3 M30 çözünürlükte 30 dk = 1 bar).
3. Sürtünme: spread × 1,5 ile TEST ort > 0.
Hepsi → B; 1 (P hariç) + 2 → C+; değilse X.
**Yapı değişimi bilgisi:** ESKİ YAPI'da aynı hücre; "son 5 yıla özgü" yalnız ESKİ ≤ 0 iken KEŞİF ve TEST > 0 ise yazılır.

## EK-1 — "Devam" (momentum) aynası (KEŞİF sonuçları görüldükten sonra; TEST hiç görülmedi)
KEŞİF'te 14 tuzak hücresinin 13'ü eksi → son 5 yılda baskın yapı devam. Aynı 14 hücrenin yönü çevrilmiş hâli (maliyet yeniden hesaplanır):
- T1a/T1b/T2/T5: R yönünde gir. T3: PDH aşılıp geri dönünce AL (sahte başarısızlık), PDL kırılıp geri alınınca SAT. T4: sakin rallide AL.
- Seçim yine yalnız KEŞİF'te, aynı kurallarla (n ≥ 30, ort > 0, ort > taban, P ≥ 0,90; ≤ 4 hücre, t'ye göre). Doğrulama ölçütleri ve
  MT5 TEST teyidi aynı. Bonferroni tuzak + devam = 28 hücre üzerinden değil, dondurulan ≤ 4 üzerinden (P ≥ 0,975).
