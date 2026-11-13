# OK-02 — DAX: bot ↔ decider ortak kazanç kapısı · rapor (2026-11-13)

OK-01'in DAX tekrarı (ön kayıt `PROTOCOL.md`; veri ve kod OK-01'den, `01_dax.py`, `02_dax_rest.py`). DP-00 (111 işlem, 65 özellik) tekrarlanmadı.

## DAX işlemleri (06-29 → 11-13)
| grup | n | ort R | yarılar | net $ |
|---|---|---|---|---|
| bot CHREV BUY (5 lot) | 23 | +0,085 | −0,005 / +0,168 | +2.113 |
| bot CHREV SELL | 14 | −0,002 | +0,115 / −0,119 | +734 |
| bot MOMSR BUY (5–10 lot) | 42 | +0,013 | +0,032 / −0,007 | −919 |
| decider DAX BUY icra (0,1 lot) | 30 | −0,114 | −0,116 / −0,111 | −10 |
| decider DAX BUY journal OPEN (3 ay, net) | 86 epizod | +0,035 | +0,064 / +0,007 | — |
| decider DAX SELL journal OPEN (canlı değil) | 10 | −0,232 | — | — |

## Sınamalar
| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| D1 | Uzlaşma: bot DAX girişinden önce decider AGREE / WAIT; decider DAX OPEN anında bot aynı yönde | bot AGREE n 11 −0,27 vs +0,11 (Δ −0,38, P 0,22); decider BOT_SAME n 16 Δ +0,09 (P 0,77) → işaretler birbirine ters, n küçük | X |
| D2 | Engel (iki yarı < 0, P(<0) ≥ %90, ön dönem < 0) | hiçbir grup geçmiyor; en yakın decider DAX BUY icra P(<0) 0,856, ön dönem yok | — (engel yok) |
| D3 | **İcra açığı:** gerçek DAX icrası − aynı kararın simülasyonu | açık **+0,083R** (gerçek simülasyondan iyi; P(açık<0) 0,19); giriş kayması +0,06 ATR lehte, SL mesafesi oranı 1,00 → icra sorunu yok. İcra edilen 30 karar, simüle sonucu kötü (−0,197R) bir alt küme: DX-05'e göre DAX emirlerinin çoğu XAU'nun doldurduğu günlük 10 emir sınırına takılıyordu | X (açık yok) · seçilim notu |
| D4 | Mekanik tetik + LLM seçimi (DAX) | tetik BUY −0,092 / SELL −0,104 (OK-01 H6); BUY OPEN − kör tetik +0,126 (yarılar +0,02 / +0,25, P 0,83), OPEN − LLM-WAIT +0,087 (P 0,76); SELL n 9 | C (decider'ın en güçlü seçim izi, ölçüt altında) |
| D5 | Kendi karnesi (k=5) bot DAX | al +0,233 vs atla −0,052, Δ +0,285 (P 0,82); OK-01'de bağımsız popülasyonlarda genel X | X |
| D6 | Çapraz varlık (eş NDX 30 dk) | bot F1 Δ −0,20 (P 0,19), F2 −0,07; decider F1 −0,02, F2 −0,02 | X |
| D7 | **DAX BUY × VIX rejimi** (EK-1, "korku döner"; önceki gün VIX < 18,4 SAKİN) | canlıda SAKİN kötü: bot fark −0,32R (P(<0) 0,81, KORKU n 11), decider mekanik −0,14 (0,88), decider OPEN +0,02; **bağımsız uzun vekil TERS**: 2021-26 +0,025, 2016-21 +0,045 (P(>0) 0,95) → canlı fark kısa örnekleme özgü | X |

## Hüküm
- DAX'ta **engellenecek kaybettiren grup yok** ve **yeni kapı yok** (D1–D7); kod değişikliği yapılmadı (ölçüt dışı bir engel uydurulmadı).
- Decider DAX BUY yaklaşık başabaşta (+0,035R net) ve DAX'ın tek pozitif seçim izi burada (D4, C). XAU BUY'ın canlıdan çıkması
  (OK-01) günlük emir sınırını boşaltır → DAX BUY icraları artacak; beklenen etki ≈ 0, lot 0,1. İzlenecek.
- Bot DAX'ın parası CHREV'den (≈+0,09R × 5 lot); MOMSR DAX BUY 42 işlemde ≈ 0R, −919 $ → kaybettirmiyor ama katkısı yok (DP-00 ile aynı).
- DAX'a özgü tek B-sınıfı fikir hâlâ DP-03 FOMC öncesi uzun (gölgede, ilk olay 2026-12-08).
