# Rastgele giriş → sonraki yapı → ortak ön özellik (2026-11-17)

Ön kayıt `PROTOCOL.md` (+ EK-1). Kod `src/build.py` (örnekleme + etiket + 23 özellik), `src/analyze.py` (A1–A3), `src/orb_trend.py` (EK-1).
Veri Dukascopy NDX 1m 2018-01 → 2026-11. Dönemler KEŞİF 2022–23, TEST 2024–26, BAĞIMSIZ 2018–21.

## Örnekleme
Her işlem günü ASYA (18:00–02:59 ET), AVRUPA (03:00–09:29), NY (09:30–15:59) seanslarının her birinde 10 rastgele dakika (tohum 20261117)
→ **62.802 giriş** (dönem × seans dengeli). Girişten sonraki 60 dk: ±1U yön yarışı (U = 4 × önceki 60 barın ort. 1m aralığı) ve yapı tipi.
| seans | TREND | KARARSIZ | SAKİN | ARA | yukarı / aşağı / çözülmedi |
|---|---|---|---|---|---|
| ASYA | %16,4 | %4,0 | %27,3 | %52,3 | %38,3 / %38,8 / %22,9 |
| AVRUPA | **%20,3** | %5,3 | %17,1 | %57,3 | %42,9 / %42,5 / %14,5 |
| NY | %12,3 | %2,5 | **%31,6** | %53,6 | %36,8 / %37,8 / %25,4 |

## Sonuçlar
| ID | soru | sonuç | hüküm |
|---|---|---|---|
| RG-01 | A1 kazanan (önce +U) vs kaybeden girişlerin ortak ön özelliği, 23 özellik × 3 dönem | Ölçütü (üç dönemde aynı işaret, |d| ≥ 0,05, min |t| ≥ 3) geçen yok. En tutarlılar seans içi konum (d +0,02 / +0,07 / +0,06), son 4 sa getirisi (+0,02 / +0,07 / +0,04) — KEŞİF'te t < 2 | X |
| RG-02 | A1 TREND vs KARARSIZ girişlerin ortak ön özelliği | Ölçüt geçen yok; en tutarlı seans içi dakika (erken → trend, d −0,10 / −0,16 / −0,12) ve oynaklık rejimi | X (bilgi: zaman/oynaklık) |
| RG-03 | A2 model AUC (KEŞİF'te eğit) | **Yön** 0,505 / 0,516 (şans %95 0,520 / 0,514) → X. **Yapı (TREND)** 0,684 / 0,695 (şans 0,51) → öngörülüyor; ama yalnız oynaklık + seans zamanı modeli 0,680 / 0,690 → bilgi oynaklıkta, mumda değil | yön X · yapı A (oynaklık) |
| RG-04 | A3 kurallar (±1U braket, 60 dk, spread dahil) | trend bekleniyor → momentum −0,08 / −0,13 / −0,10R; yön modeli üst %10 KEŞİF +0,31 (örneklem içi) → TEST −0,08, BAĞIMSIZ −0,04R; taban momentum −0,10…−0,12R (maliyet ≈ 0,13R) | X |
| RG-05 | EK-1 trend olasılığı × ORB × VIX (TP 3R) | Ters: düşük p_trend +0,43 / +0,24R, yüksek +0,12 / +0,20R (P yüksek>düşük 0,13); kitap dozu Sharpe 1,69 → 1,65 / 2,18 → 2,13 | X (NX-06 "dar açılış iyi" iziyle tutarlı) |

## Hüküm
Rastgele girişlerin kazananları giriş anında görülebilen ortak bir özellik taşımıyor; geçmiş ve gelecek dönemde tekrarlanan tek bilgi
**ne kadar hareket olacağı** (oynaklık rejimi + seans zamanı: Avrupa açılışı ve seans başı trend, NY öğleden sonrası sakin), **hangi yöne olacağı değil**.
Bu, GF-01 (rastgele girişte durum kapısı yok) ve NOM/YL (oynaklık A, yön X) sonuçlarını seans dengeli 62.802 girişle ve yapı tipi hedefiyle yeniden doğruluyor.
Yapı bilgisi bir kırılım kuralını da iyileştirmedi (RG-05, ters). Canlı koda bağlanacak bir şey yok.
