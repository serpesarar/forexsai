# ME-10 — "Dalgalı tepe aralığı" kural tabanlı tanım — sonuç (2026-10-19)

Ön-kayıt: `PROTOCOL.md` (sonuçtan önce donduruldu). Betikler: `tepe_ozellik.py` (özellik çekirdeği, önek-sızıntı testi
`results/00_sizinti_denetimi.txt`: kesilmiş veride özellik farkı 0), `01_sablon_ozellikleri.py` (yalnız özellik),
`02_kural_testi.py` (bir kez), `03_duyarlilik_W.py` (aile dışı). Şekil-benzerliği tarafı paralel araştırmacıda (`../sablon/`).

## 1. Şablonların ölçülen profili (W = 9 gün; geliştirme yüzdeliği)
- Ortak ve seçici olan tek şey **"düşüşle pencerenin dibinde bitmek"**: pos 0,04–0,22 (3.–14. yüzdelik), 9 günlük net
  −1,5…−6,0 σ (−%1,6…−%6,4). Pencere tepesi son 60 günün tepesinin %1,7–5,2 altında (gevşek; günlerin %83'ü bu kadar yakın).
- "Oynak / çalkantılı" izlenim ölçüde **yok** (T2 hariç): oynaklık oranı 0,74 / 1,12 / 1,59 (20./61./84. yüzdelik; T3 yıllıklandırılmış
  %13,8), ≥1σ salınım 3 / 6 / 11, verimlilik 0,06–0,13 (medyan civarı), alçalan tepe 0 / 1 / 4.
- Kullanıcının T1 sonu (07-21) kısmi toparlanmayı içeriyor (pos 0,55); "düşüşle biter" tarifine göre 07-17'ye inceltildi.

## 2. Kurallar ve sıklık (NDX geliştirme 2017-03 → 2025-11, 8,7 yıl)
| kural | tanım (özet) | yanan gün | oluşum bölümü (yılda) | tamamlanma | şablonlar |
|---|---|---|---|---|---|
| K1 gevşek (3 şablon) | pos ≤ 0,222, net ≤ −1,524σ, tepeye ≤ 4,83σ, rv ≥ 0,742×, ≥3 salınım, eff ≤ 0,129 | %3,8 | 36 (4,1) | 14 | T1 T2 T3 ✓ (kullanıcı T1 sonu ✗) |
| K2 çalkantı (T1+T2) | + net ≤ −3,9σ, rv ≥ 1,115×, ≥6 salınım, ≥1 alçalan tepe | %1,2 | 16 (1,8) | 4 | T1 T2 ✓, T3 ✗ |
| K3 tepe-şartsız | K1 − yakın-tepe koşulu | %5,6 | 46 (5,3) | 20 | T1 T2 T3 ✓ |
DAX (2020-09 → 2025-11): K1 %4,7 / 27 bölüm / 10 tamamlanma; K2 3 bölüm; K3 30 / 14.

## 3. Sonuç (eşli = 9 günlük getiri ondalığı × 9 günlük oynaklık ondalığı; bp; P = ay-blok bootstrap)
| NDX K1 | n | +1 saat | +1 gün | +5 gün |
|---|---|---|---|---|
| oluşum (ilk yanan gün) | 36 | +6,8 (P>0 0,88) | +23 (0,76) | +26 (0,68; yarılar −7 / +56) |
| tamamlanma (≥2 gün yandı, söndü) | 14 / 13 | +8,7 (0,97) | +52 (0,82) | +65 (0,82) |
| DAX K1 oluşum / tamamlanma | 27 / 10–9 | +5,6 / −0,6 | +12,5 / +40,5 (0,97) | −55 / **−184** (P<0 0,95) |
- Aile 18 hücre (3 kural × 2 olay × 3 ufuk), iki yön: **P ≥ 0,975 olan hücre 0 / 0** → hiçbir hücre geçmedi (H1 "tepe → aşağı" da,
  H2 "korku döner" de). Tamamlanma hücreleri K1'de 14, K2'de 4 olayla ≥ 20 ölçütünü zaten karşılayamıyor.
- İşaret: NDX 18 hücrenin 15'inde nokta tahmini pozitif (tabanın üstünde sıçrama), DAX 15'in 8'inde; NDX–DAX aynı işaret 10/15
  (+1s/+1g'de 9/10, +5g'de 1/5). +5g'de DAX ters ve W'ya duyarlı (W = 12'de DAX tamamlanma +148, W = 9'da −184, n ≈ 10).
- Olay düzeyi (E6): NDX K1 oluşumun en kötü olayları 2018-02 / 2018-03 (+5g fark −%5,5 / −%6,2) ve 2019-08 (+1g −%5,7); +5g medyan
  fark +25 bp, olayların %47'si negatif → ortalama ve medyan aynı (zayıf pozitif) yönde, tek olaya dayanmıyor ama anlamsız.
- Aile dışı: K1-lit (kullanıcının 07-21 sonu) tamamlanma +1g +34 bp, P 0,99, yarılar +16/+49, n = 46 → temel ölçütleri geçiyor ama
  aile dışı, Bonferroni (0,9986) altında, DAX'ta +11 (P 0,73), +5g yarıları +178/−26; 24 hücre × 2 yönde ~1,2 tesadüfi geçiş beklenir.
- Doğrulama (2025-12 → 2026-10, şablon çakışması hariç): NDX K1 6 oluşum (+1g ort. fark +86, +5g +109), 1 tamamlanma; MDE₈₀ +1g
  223 bp, +5g 397 bp → **güç yok**.

## 4. Bugün (son veri 2026-10-02 04:00 UTC; gerçek bugün 10-19 → 17 gün veri yok)
- NDX: yapı **yok** — kapanış 30.527 (10-01) / 30.674 (son bar), pencere 60 günlük tepede, pos 0,71, net +2,5σ. Son K1 günü 2026-08-20 (= T3).
- DAX: 10-01 19:00 kapanışında K1 ve K3 **yanıyor** (pos 0,14, net −1,7σ, tepenin %3,0 altı, 8 salınım, 3 alçalan tepe); son barda
  pos 0,24 → sınırın hemen üstünde, K1 sönük. Tarihsel karşılığı yön bilgisi taşımadığından işlem anlamı yok.

## 5. Okuma
Kullanıcının üç örneği yorumlanabilir kurallarla **tespit edilebiliyor** (yılda ~4 bölüm), ama kural, şablonların ortak
özelliği olarak yalnız "yakın-tepeden pencerenin dibine düşüş"ü yakalıyor; sonrası (+1 s / +1 g / +5 g) aynı getiri + oynaklık
durumundaki günlerden ayrışmıyor. NDX'te nokta tahminleri hafif pozitif (düşüş sonrası toparlanma tabanın biraz üstünde) ama
anlamsız, yarılarda ve DAX'ta tutarsız. Sınıf **X** (tahmin); dedektör tanımlayıcı olarak kullanılabilir. Şekil-benzerliği
(ME-02…08) ile aynı sonuç — tanım yönteminden bağımsız.
