# Mum Eşleştirme — Bağlam ve çapraz-sembol testi (ME-03, 2026-10-12/13)

**İstek:** "Başarı yakalayacak özellikler ekle — VIX rejimlerinde aynı anda tespit, başka sembollerle beraber, kombinasyonlar."
**Ön-kayıt:** `PROTOCOL_BAGLAM.md` (sonuçlardan önce; tek değişiklik: ikincil, bilgi amaçlı Brier ölçütü — dosyada kayıtlı).
**Betikler:** `baglam_testi.py` (baglam | capraz), `baglam_ozet.py`. **Ham çıktı:** `results/baglam/`, `results/capraz/`
(git dışı), `results/baglam_*.csv`, `results/capraz_*.csv`.

## Sonuç (tek paragraf)

Bağlam ve çapraz-sembol eklemek şekil eşleştirmesine **yön** başarısı kazandırmadı. VIX rejimi, stres, VIX × stres (CAPREV hücresi dahil),
saat ve oynaklık rejimi için 69 hücrede başarılı hücre 0–1 (tesadüf beklentisi ~1,7). Bağlamların kendisi de bu ufuklarda
çoğunluk yönünü değiştirmiyor; NDX'te iki VIX rejiminde de yükselen gün çoğunlukta. Olasılık kalibrasyonu (Brier) da
iyileşmiyor. **Büyüklükte** şekil + bağlam, bağlamın saate bakmayan medyanını 4 sembolde anlamlı geçiyor; ön-kayıt ölçütü
bu yüzden "katkı var" diyor. Ama aynı tahmin, **saatin tipik hareketini 69 hücrenin hiçbirinde** geçemiyor (45–55 hücrede
anlamlı kötü). "Kaç pips" sorusunun en iyi cevabı hâlâ o saatin tipik hareketi. İki sembolün aynı andaki şekli de (12 çift × 4 TF) yönde kendi şeklinden iyi değil; büyüklükte iyi ve kötü hücre sayısı eşit (§5).

## 1. Bağlam testi — tüm havuz (98.260 sorgu anı × 3 ufuk; P33 ve R7 aynı tabloyu veriyor)

| Bağlam | Model yön isabeti | Yalnız bağlam (aynı bağlamın çoğunluğu) | Koşulsuz taban | Rastgele komşu (aynı bağlam) | Büyüklük: bağlam medyanına göre | Büyüklük: saatin tipik hareketine göre |
|---|---|---|---|---|---|---|
| yok (ME-02) | %51,91 | %53,37 | %53,37 | %51,50 | −%4,8 | −%4,8 |
| VIX rejimi | %51,89 | %53,22 | %53,37 | %51,43 | +%1,7 | −%5,0 |
| stres | %51,91 | %53,28 | %53,36 | %51,44 | +%1,8 | −%4,8 |
| VIX × stres | %51,80 | %52,98 | %53,32 | %51,35 | +%1,6 | −%5,1 |
| saat | %52,01 | %53,00 | %53,36 | %51,49 | −%0,9 | −%0,9 |
| oynaklık rejimi | %51,93 | %53,11 | %53,27 | %51,53 | +%0,6 | −%3,3 |

(P33 satırları; R7 farkları ±0,2 puan.) Hedef (±1 ATR önce hangisi): model %50,4–50,8 ↔ bağlam tabanı %50,5–50,9.
Brier (ikincil): bağlam-koşullu oran koşulsuz orandan −%0,06…−%0,39 kötü; model bağlam tabanından −%1,6…−%1,9 kötü.

## 2. Anlamlılık (hücre = sembol × TF × ufuk; 69 hücre; başarı = P ≥ 0,975 ve iki yarı > 0)

| Test | VIX | stres | VIX × stres | saat | oynaklık |
|---|---|---|---|---|---|
| B1 yön: şekil+bağlam > yalnız bağlam (P33 / R7) | 0 / 0 | 0 / 0 | 1 (OIL) / 0 | 0 / 0 | 0 / 0 |
| B1 büyüklük: > bağlamın medyanı (P33 / R7) | 24 / 19 | 25 / 20 | 24 / 17 | 0 / 0 | 17 / 15 |
| aynı tahmin > **saatin tipik hareketi** (P33 / R7) | **0 / 0** | **0 / 1** | **0 / 0** | — | **0 / 0** |
| B2: bağlamın kendisi > koşulsuz taban (yön) | 0 | 0 | 0 | 0 | 0 |

Okuma: büyüklükteki "katkı", şeklin oynaklık/saat durumunu kısmen yansıtmasından geliyor (saate bakmayan bir medyanı
geçiyor). Saat doğrudan kullanıldığında şekil ek bilgi vermiyor.

## 3. Sembol bazında (P33): bağlam eklemek yönü değiştirmiyor

| Sembol | yok | VIX | stres | VIX × stres | saat | oynaklık | (yalnız bağlam tabanı, VIX) |
|---|---|---|---|---|---|---|---|
| NDX | %53,6 | %53,7 | %53,8 | %53,4 | %53,6 | %53,6 | %55,1 |
| DAX | %51,9 | %51,6 | %51,7 | %51,8 | %52,2 | %52,3 | %53,5 |
| XAU | %51,4 | %51,2 | %51,3 | %50,9 | %51,3 | %51,2 | %52,9 |
| OIL | %50,8 | %51,0 | %50,9 | %51,2 | %51,0 | %50,8 | %51,5 |

## 4. VIX ve stres hücreleri (NDX/DAX, P33, tüm ufuklar)

| Sembol / TF | Hücre | Sorgu | Gerçekleşen yukarı | Yalnız bağlam isabeti | Şekil+bağlam isabeti |
|---|---|---|---|---|---|
| NDX 1h | VIX < 18,4 | 22.101 | %55,0 | %55,0 | %53,7 |
| NDX 1h | VIX ≥ 18,4 | 17.032 | %55,1 | %55,1 | %54,0 |
| NDX 1h | stres ∧ VIX yüksek (CAPREV) | 4.543 | %57,1 | %57,0 | %55,9 |
| NDX 4h | CAPREV | 768 | %60,3 | %60,2 | %58,1 |
| NDX 1d | VIX < 18,4 / ≥ 18,4 | 3.613 / 2.633 | %61,7 / %59,5 | %61,7 / %59,1 | %60,2 / %57,5 |
| NDX 1d | CAPREV | 706 | %56,7 | %56,1 | %55,6 |
| DAX 1h | sakin → CAPREV | 11.685 → 1.575 | %53,3 → %57,3 | %52,0 → %57,3 | %51,2 → %57,3 |
| DAX 4h | CAPREV | 244 | %59,0 | %59,0 | %58,1 |
| DAX 1d | CAPREV | 216 | %61,1 | %61,1 | %60,9 |

Stres ∧ yüksek VIX anlarında yükseliş oranı 1h/4h'te sakin günlere göre +2…+5 puan artıyor; bu GF-16/22'deki CAPREV mekanizmasıyla
tutarlı ve zaten canlıda ayrı bir strateji olarak kullanılıyor. Şekil eşleştirmesi bu hücrelerde bağlamın kendisinin
üstüne bir şey eklemiyor (isabeti hep eşit ya da düşük).

## 5. Çapraz-sembol testi (12 sıralı çift × 30m/1h/4h/1d, 48 hücre, 670.569 değerlendirme)

| Temsil | Varyant | Yön isabeti | Hep-çoğunluk tabanı | Rastgele komşu | Büyüklük: saatin tipik hareketine göre | Hedef ±1 ATR |
|---|---|---|---|---|---|---|
| P33 | kendi şekli | %52,01 | %53,39 | %51,51 | −%4,2 | %50,6 |
| P33 | yalnız ortağın şekli | %51,87 | %53,37 | %51,48 | −%4,9 | %50,4 |
| P33 | **ikisi aynı anda** | %52,09 | %53,35 | %51,46 | −%4,2 | %50,6 |
| R7 | kendi | %51,74 | %53,36 | %51,49 | −%5,3 | %50,4 |
| R7 | **ikisi** | %51,76 | %53,36 | %51,48 | −%4,9 | %50,2 |

Çift bazında "ikisi − kendi" yön farkı −0,41…+0,60 puan (12 çiftin hepsi tabanın 1–2 puan altında). En iyi görünen
NDX+DAX (+0,6 puan) da tabanın (%54,3) altında: %53,2.

| Test (144 hücre = 12 çift × 4 TF × 3 ufuk) | P33 iyi / kötü | R7 iyi / kötü | Karar |
|---|---|---|---|
| ikisi > kendi (yön) | 6 / 4 (binom p = 0,15) | 3 / 5 | yok |
| ikisi > ortağın şekli (yön) | 4 / 6 | 2 / 6 | yok |
| ikisi > hep-çoğunluk (yön) | 1 / 47 | 1 / 59 | yok |
| ikisi > kendi (büyüklük) | 15 / **16** | 23 / **18** | ön-kayıt kuralı "katkı var" der; ama eşit sayıda anlamlı kötü hücre → sistematik değil (havuz farkı 0 / +%0,3) |

**Ön-kayıt kuralının zayıflığı (ders):** kural yalnız "iyi" hücre sayısını tesadüfe karşı sınıyor; aynı ölçüde anlamlı
"kötü" hücre varsa bu, iki temsilin farklı ama eşit derecede gürültülü olduğunu gösterir, katkıyı değil. Bundan sonra karar
iyi ↔ kötü simetrisiyle (işaret testi) ve havuz etkisiyle birlikte verilmeli (defter E26).

## 6. Ne çıktı, ne çıkmadı

- **Yön:** şekil, VIX rejimi, stres, CAPREV hücresi, saat, oynaklık rejimi, diğer sembollerle ortak şekil — hiçbir
  kombinasyon yön isabetini tabanın üstüne çıkarmadı; hepsi rastgele komşu düzeyinde.
- **Büyüklük ("kaç pips"):** en iyi tek tahminci o saatin tipik hareketi (ATR biriminde). Şekil + bağlam/ortak sembol onu
  hiçbir hücrede geçemedi.
- **Bağlamın kendisi:** stres ∧ yüksek VIX anlarında NDX/DAX yükseliş oranı 1h/4h'te +2…+5 puan yüksek (CAPREV ile tutarlı,
  canlıda ayrı strateji). Bu bilgi şekil eşleştirmesinden değil, bağlamın kendisinden geliyor.
