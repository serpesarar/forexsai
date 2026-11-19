# VK-01…05 + KM-01 — varyans primini genişlet, kanıtlı kurallar × yeni boyutlar (2026-11-18)

Ön kayıt `PROTOCOL.md` + EK-1…4. Kod `src/vk.py`, `ek1.py`…`ek4.py`; çıktılar `results/`.

## VK — VP1 (varyans primi yüksek → 20 g AL) genişletmesi: düştü
| ID | Sınama | Sonuç |
|---|---|---|
| VK-01 | ^NDX 1990–2000, VIX − RV20 | 20 g fark **−78 bp** (P 0,24), 5 g +4 |
| VK-02 | SPY 1993+, VIX − RV20 | KEŞİF 5 g +23 (P 0,97), 20 g +54; TEST +25 / +60 (P 0,85 / 0,77) |
| VK-03 | örtüşmesiz epizot (eşiğe geçiş günü, 20 g) | QQQ KEŞİF n 88 +41,5 vs plasebo +79,7 (yüzdelik 0,25), TEST n 24 +34 vs +104 (0,27); SPY 0,66 / 0,72; NDX 1990–2000 0,82 |
| VK-04 | ufuk | fark ufukla doğrusal büyüyor (h1 +9 → h60 +275): kalıcı durumun sürüklenmesi, olay değil |
| VK-05 | zamanlama portföyü | 2003+ Sharpe 0,64 vs al-tut 0,78 (maxDD −57 / −53); yalnız TEST 0,92 vs 0,60 |
**Hüküm: X** (§2.85 NA-02 C+ geri alındı). Gün sayımlı fark E102 (örtüşmeli ortalama) şişmesiydi.

## KM-01 — kanıtlı kurallar (günlük vekil) × yeni boyutlar (QQQ 2001+, SPY eş)
| Hücre | KEŞİF | TEST | Bağımsız / kopya | Hüküm |
|---|---|---|---|---|
| C3b × VP1 | +56 (P 0,99) | +59 (P 0,95) | VIX içi/dışı ikisi artı, ama **^NDX 1990–2000 −84 (P 0,025)**, SPY 93–00 −7 | X |
| C3b/K1/ES × VRP düşük (veto) | −66 / −7 / −6 | −74 / −93 / −46 | 1990'larda ters (C3b +67 / +113) | X |
| **K1 × çekişme üst %20** | +34 (P 0,97) | +34 (P 0,94) | SPY +25/+25, SPY 1993–2000 +29 (P 0,92); VIX üstü/altı, ardışık/tekil, r20 ±, SMA200 ± alt kümelerinin 15/16'sında artı; taşıyıcı gün içi satış bileşeni. **Gerçek gün içi K1 (EK-4):** YENİ Duka +52 / MT5 NAS100 +66 / US500 +22, ESKİ 2018–21 üçü de eksi (−28…−37), havuz P 0,83 | **C+** |
| ES × kredi zayıf | +36 (P 0,98) | +44 (P 0,95) | SPY KEŞİF +3; 2007 öncesi veri yok | C+ |
| C3b × çekişme | +8 | +42 (P 0,88) | SPY 93–00 +40 (P 0,93) | C |
| K1 × dar liderlik | +12 | −26 | — | X |

## Ana ders
Kalıcı bir **durum** değişkeni (VRP yüzdeliği) gün gün sayılınca hem P hem fark şişer; epizot ve bağımsız dönem sınaması gerçeği
gösterir. Yeni boyutların kanıtlı kurallarla kesişiminde tek dayanıklı iz "son 20 günde gün içi satış baskın iken korku gecesi
daha iyi" — mekanizma korku gecesinin kendisi (gün içi sat, gece geri al) son dönemde çalışıyorsa sürmesi; canlı kuralda
yalnız 2021 sonrası görünüyor → gölge etiketi.
