# FAZ 7 — Model: şansın üstüne öğren (Yön Lab, 2026-11-14)

Kod: `src/faz7_model.py`. Çıktı: `results/faz7_ozet.json`, `faz7_oos_<etiket>.parquet`.
LightGBM ikili, **`init_score = logit(eşlenmiş taban)`** (NY saati × oynaklık ondalığı, eğitimden) → model yalnız tabandan sapmayı
öğrenir. Girdiler: NOM 132 + 114 ek durum + 24 doğrulanmış hücre bayrağı + 13 ailenin en yakın üst/alt uzaklığı. NOM WF şeması
(2023H1 … 2025H2, genişleyen, 1 g + 4 s arındırma), isotonic. KÖR 2026 burada kullanılmadı.

## Zorunlu yön testi (WF OOS 2023–2025)
| Etiket | AUC (taban) | Brier becerisi vs taban | |P−0,5| ≥ 3 p | ≥ 5 p | ≥ 8 p | ≥ 10 p |
|---|---|---|---|---|---|---|
| **sym_1** (±1 ATR, yalnız bir taraf çözüldü) | 0,500 (0,495) | −0,012 | %49,8 [48,9–50,7] n 22.839 | %50,3 [49,2–51,4] | %50,1 [48,5–51,6] | %49,9 [48,2–51,6] |
| NOM, aynı satırlar (P_long_TP − P_short_TP) | 0,500 | — | %49,8 n 16.230 | %49,5 n 7.254 | %49,3 n 2.015 | %52,7 [48,2–57,5] n 778 |
| dir_1h (işaret) | 0,505 (0,500) | −0,009 | **%51,4** [50,7–52,1] | %51,5 [50,7–52,3] | %51,5 [50,2–52,8] | %51,3 [49,4–53,1] |
| dir_15m (işaret) | 0,508 (0,500) | −0,004 | **%51,8** [51,2–52,3] | %51,9 [51,1–52,8] | %52,3 [51,1–53,4] | %52,3 [50,8–53,8] |

- **P2 karıştırılmış etiket** (sym_1, 20 tekrar): AUC p95 0,507; gerçek 0,500 → **plaseboyu geçmiyor**.
- Hedefi (simetrik yarış) yön bilgisi olarak sorduğumuzda yeni model de NOM gibi **yazı-tura** (%49,8–50,3). İşaret etiketlerinde
  %51,4–52,3'lük küçük ama güven aralığı %50'nin üstünde bir iz var — Faz 5'in 15 dk dönüş bilgisiyle aynı; Brier becerisi tabana
  göre eksi (olasılık değerleri ham tabandan iyi değil; bilgi yalnız sıralamada ve çok küçük).
- Derin model: Faz 4–5 boosting tabanına anlamlı fark üretmediği ve ortamda torch olmadığı için denenmedi (NOM Faz 4 kuralı).
