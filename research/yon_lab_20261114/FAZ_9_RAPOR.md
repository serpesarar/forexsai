# FAZ 9 — İşleme çevir ve kanıtla (Yön Lab, 2026-11-14)

İcra (CLAUDE.md 2. kural, ölçüt 5): giriş t'den sonraki **M1 açılışı**, SHORT BID − 1 p / LONG ASK + 1 p; çıkış 15 dk sonra
kapanıştan karşı taraf ± 1 p; spread = NOM koruyucu NY-saati modeli (Pepperstone ile Dukascopy'nin büyüğü). R birimi = ATR14(M15)
(medyan 27 puan). Ayrı veri: Dukascopy (MT5 terminali değil) → `_bars_upto.py` gerekmedi (geçmiş karar anı Dukascopy 1m'den, yalnız
geçmiş barlar).

## R-H: doğrulanmış hücre birliği → SHORT 15 dk
| Dönem | n (bağımsız) | EV (R) | %95 GA | P(EV>0) | 2× sürtünme | isabet | plasebo p95 | yarılar |
|---|---|---|---|---|---|---|---|---|
| KEŞİF | 21.104 (3.912) | **−0,252** | [−0,265; −0,238] | 0,00 | −0,507 | %31,8 | −0,244 | −0,195 / −0,308 |
| DOĞRULAMA | 11.789 (2.163) | **−0,215** | [−0,231; −0,200] | 0,00 | −0,415 | %34,0 | −0,187 | −0,230 / −0,201 |
| KÖR TEST | 6.905 (1.211) | **−0,128** | [−0,149; −0,108] | 0,00 | −0,253 | %39,6 | −0,109 | −0,157 / −0,099 |
| KÖR TAŞIMA | US500 −0,37 · US30 −0,08 · US2000 −0,64 · GER40 −0,11 | | | | | | | |

## R-M: model (dir_15m, |P−0,5| ≥ 0,08, iki yön)
DOĞRULAMA n 1.625 EV **−0,145R** (P 0,00), 2× −0,31R, yön isabeti %53,4 · KÖR n 100 EV **−0,154R**, yön isabeti %53,0.

## Hüküm
Hiçbir kural ön-kayıtlı ölçütleri geçmiyor (DOĞRULAMA'da EV > 0 değil, P(EV>0) = 0). Plasebo bile kuraldan iyi değil çünkü ikisi de
aynı maliyeti ödüyor. **Neden:** yön bilgisi ≈ +2–3 puan isabet × ortalama |15 dk hareketi| (ort. 0,51, medyan 0,36 ATR(M15) ≈ 9–14 puan) ≈ **0,3–0,6 puan**
beklenen kazanç; maliyet spread (1,4–3,4 p) + 2 kayma ≈ **3,4–5,4 puan**. Bilgi maliyetin ~1/10'u. Bilginin para olabilmesi için
işlem başı toplam maliyetin < 0,4 puan olması gerekir (perakende CFD'de mümkün değil). → **go_live kartı çıkarılmadı; kural GÖLGE
bile önerilmez.**
