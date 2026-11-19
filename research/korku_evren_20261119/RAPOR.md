# Korku gecesi paketini genişletmek — RAPOR (2026-11-19)

- **Ön kayıt:** `PROTOCOL.md` (+ EK-1). **Kod:** `src/indir.py`, `src/evren.py` (eksen A), `src/esik.py` (eksen B), `src/doz.py` (EK-1).
- **Sonuçlar:** `results/evren.json`, `results/esik.json`, `results/doz.json`, `results/kutu_semboller.json`. Veri (`data/`, parquet) git dışı.
- Tüm dönemler 2026-11-05'te kesik (ileri gölge dönemi kullanılmadı). KEŞİF ≤ 2017 (A) / ≤ 2021-10 (B), TEST sonrası.

## Eksen B — eşik gevşetme (NDX ve ABD endeksleri, gerçek gün içi K1 + OPEX + XP)

| Hücre | Eklenen işlem (TEST, 4 MT5) | Eklenenlerin ort / isabet | KEŞİF eklenen ort | Duka TEST | Paket Sharpe artan besleme | Hüküm |
|---|---|---|---|---|---|---|
| **T30: TWAP ≤ −%0,3** | 268 (yılda ≈ 45) | **+38,9 bp / %74,6**, P 1,00, 4/4 piyasa | +32,9 (n 158) | +20,9 (n 74) | **5/5** (NAS100 1,90 → 2,08; US500 1,77 → 2,15; Duka 2,13 → 2,17) | **B** |
| T40: TWAP ≤ −%0,4 | 107 | +47,0 / %75,7 | +53,9 | **−8,3** (n 28) | 4/5 | C |
| K1 ∪ K3 | 296 | +33,1 / %72,3 | +8,8 | +29,4 | 3/5 | B (zayıf KEŞİF) |

- **NAS100'de yılda işlem 22,6 → 36,4 (+%61).** Eklenen işlemler K1'in yarısı kadar kazanıyor ama artı ve portföyü iyileştiriyor.
- **Doz eğrisi (EK-1, betimleyici)**, MT5 KEŞİF / TEST ort bp:

  | TWAP uzaklığı | KEŞİF | TEST |
  |---|---|---|
  | ≤ −%0,5 | +83 | +74 |
  | −%0,5…−%0,4 | +54 | +47 |
  | −%0,4…−%0,3 | +15 | +34 |
  | −%0,3…−%0,2 | +14 | +8 |
  | −%0,2…−%0,1 | +1 | +14 |
  | −%0,1…0 | −9 | +12 |

  Kenar korkunun derinliğiyle düzgün artıyor; −%0,3'ün ötesi maliyet seviyesine iniyor. T30 doğal sınır.

## Eksen A — yeni evren (günlük vekil V1 + OPEX + XP, kendi tabanına göre fark)

| Grup / alt küme | TEST yılda işlem | TEST fark (bp) | P | enstrüman artı | Hüküm | Eşit riskli birleşik Sharpe (NDX tek: 1,86) |
|---|---|---|---|---|---|---|
| Sektör ETF, tümü | 283 | +36,0 | 1,00 | %100 | B | 1,81 |
| Sektör ETF, yeni gün ∧ habersiz | 111 (60 yeni gün) | +22,5 | 0,988 | %89 | B | 1,73 |
| Sanayi/stil ETF, tümü | 343 | +31,5 | 1,00 | %100 | B | 1,83 |
| Sanayi/stil, yeni gün | 165 | +8,5 | 0,82 | %75 | C | — |
| Hisse, tümü | 950 | +28,9 | 1,00 | %95 | B | 1,66 |
| Hisse, **endeksle aynı gün** | 432 | **+61,6** | 1,00 | %95 | B | 1,84 |
| Hisse, **yeni gün** | 518 | **+1,7** (KEŞİF +23) | 0,62 | %60 | C (söndü) | — |
| Haberli büyük boşluk (≤ −%2), üç grupta | 2–19 | dağınık | — | — | X | — |

- **Korku gecesi piyasa geneline ait bir olgu:** hisselerde kenarın neredeyse tamamı endeksle aynı korku gecesinde; hisseye özgü korku
  2018 sonrası dönmüyor.
- **İşlem sayısı artıyor ama risk başına getiri artmıyor:** hiçbir bacak, eşit riskle eklense de NDX paketinin Sharpe'ını geçmiyor
  (1,64–1,84 vs 1,86); bacakların maksimum düşüşü −2.400…−3.300 bp. Ön kayıt gereği **portföy kabulü yok**.
- **Erişim:** kutudaki Pepperstone hesabında mega-cap hisselerin hepsi, ETF'lerden XLE, XLI, KRE, XBI, XHB, XRT, MDY var;
  XLK/XLF/XLV/XLY/XLP/XLB/XLU/SMH/IBB/RSP yok.

## Hüküm
- **T30 eşik gevşetmesi: B** — işlem sayısını ≈ %60 artıran, iki dönemde ve 5 beslemede tutan tek genişleme. Canlı değil;
  2. KURAL kartı + ileri gölge gerekli.
- **Sektör/sanayi ETF ve hisse: kenar var (B) ama portföye eklenince risk başına getiri düşüyor.** Ek sermaye ile daha fazla toplam bp isteniyorsa
  "hisse ∧ endeksle aynı gün" en iyi bacak (Sharpe 1,49, birleşik 1,84); yeni gün kaynağı olarak hisseler sönmüş.
- Toplam hücre: A 3 grup × 5 alt küme, B 3 + EK-1 doz eğrisi (6 kova, betimleyici).
