# FAZ 5 — Kombinatoryal tarama (KEŞİF) + DOĞRULAMA (Yön Lab, 2026-11-14)

Kod: `src/atlas.py` (combos), `src/faz5_validate.py`. Çıktı: `results/kombinasyon_taramasi.csv`, `faz5_secilen.csv`,
`faz5_dogrulama.csv`, `faz5_ozet.json`, `deneme_sayaci.csv`.

- Hücreler: tekli 3.642 + ikili/üçlü 3.413 (+ atlas 1.307) = **8.362** (Faz 6–9 ile toplam **8.680** deneme). Aynı tarama 10 martingal
  piyasada baştan koşuldu (83.620 sıfır hücresi).
- **Eşikler** (bağımsız n ≥ 100 popülasyonu, EK-1b): tekli T* = 6,42, kombinasyon T* = 5,97. Katı okuma (tüm kombinasyonlar): 10,89 →
  **hiçbir kombinasyon geçmez**. Holm/Bonferroni (8.362 deneme, α 0,05 → |t| > 4,53) ile tekli 22, kombinasyon 342 hücre geçer; BH-FDR (q 0,05) 1.551 hücre — hepsi aynı ailenin tekrarları.
- **Simetri / yoğunluk (E26):** |t| > 4 kombinasyon: gerçek 570 vs martingal ortalama 50 (tekrarlar 6…160 — 30 dk blok karıştırma
  blok-içi kısa dönüşü korur, sıfır bu yüzden yüksek ve korumacı). Fazlalık gürültü değil, ama çeşitlilik de değil: hücrelerin ezici
  çoğunluğu aynı mekanizmayı (15 dk dönüş) farklı göstergelerle tekrar ölçüyor — bağımsız bulgu sayısı ≈ 1.
- KEŞİF geçen 89 aday → aile başına ≤ 5 kuralıyla **28 seçildi** (hepsi `dir_15m`, hepsi "yukarı aşırı uzama → aşağı").

## DOĞRULAMA (2024-07 → 2025-12, yalnız 28 seçilen)
**24/28 geçti** (aynı işaret, |t| ≥ 2, etki ≥ KEŞİF'in %50'si). Örnekler: TWAP z üst %20 → KEŞİF −3,26 p (t −7,49) / DOĞRULAMA −1,96 p
(t −3,11); Williams %R tepe ∧ M5 ROC3 üst %20 → −4,22 / −2,77 (t −3,41); M5 RSI14 üst ∧ M5 ROC3 üst → −4,24 / −3,28 (t −3,79);
3 beyaz asker ∧ ret60 üst → −4,68 / −2,84. Etki DOĞRULAMA'da KEŞİF'in ≈ %55–75'i (küçülüyor).
Kalan 4 (ret60 ∧ RSI eğimi kombinasyonları) aynı işaretli ama |t| ya da oran ölçütünü kaçırdı.

**Okuma:** Sistemin ölçebildiği yüzlerce durumdan şanstan ayrılan tek yön bilgisi, **15 dakikalık bir gürültü-dönüşü**: yukarı
aşırı uzamadan sonra fiyatın aşağı kapanma olasılığı %50 yerine ≈ %52–53. Bu, mikro yapıdaki kısa vadeli ortalamaya dönüşün
(teklif yanlılığı/ani hareket sonrası geri çekilme) bilinen izidir; 1 s, 4 s ve seans sonunda kayboluyor.
