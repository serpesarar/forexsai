# QS-06 — Ay sonu akışının anatomisi (S&P 500 + Nasdaq) + geri alım yasağı: rapor (2026-11-11)

Ön kayıt `PROTOCOL_QS06.md`. Kod `qs06_harita.py` (A1 + A2), `qs06_v2.py` (sonradan birleştirme), `qs06_geri_alim.py` (C), `qs06_kart.py`.
Sonuçlar `results/qs06*.json`; kart `go_live_cards/qs06_son_seans.json`. Deneme sayacı: QS-03…05 11 + QS-06 6 (A1 2 hücre, A2 3, C 1).

## Özet
| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| **A1 GÜN+0** | **Ayın son seansı 09:30→16:00, akış yönünde** (2002-13'te seçildi) | 2014-26 net +31,3 bp (P 1,00), SPY 1993-2002 +13,5, broker NAS100 +38,3 (P 0,998), US500 +43,9 (P 1,00, %70); **kart 6/6** | **B−** (kart 6/6) |
| A1 GECE+1 | Son günün gecesi, akışın TERSİNE (kapanış baskısı geri döner) | 2014-26 +19,3 (P 0,994), 1993-2002 +0,5, broker +15 / +10 — ama broker kazancı KSG gecelerinde | B− (bot için KSG'nin kopyası) |
| A2b | D−2 kapanış yarım saati, akış yönünde | NAS100 +7,4 · US500 +6,3 (P 0,95) · US30 +4,9 · US2000 +5,6 · Dukascopy +9,2 (P 0,99) | B− (küçük) |
| A2a | D−1 kapanış yarım saati | dördü artı, +2…+4, P < 0,9 | C |
| A2c | D+1 açılış yarım saati, E2 uzun | NAS100 +6 ama US30 −6, US2000 −15 | X |
| C | Hisse geri alım yasağı [Q−10, Q+15] | ABD AÇIK − YASAK −4,6 bp/gün (ters), yabancı plasebo da −4,6 (0/16 artı) → küresel çeyrek takvimi etkisi, geri alım değil | X |

## A1 — akış haritası (QQQ+SPY, R1 yönüyle işaretli, brüt bp)
| hücre | 2002-13 (t) | 2014-26 (t) | 1993-2002 |
|---|---|---|---|
| GÜN D−2 | +9,3 (1,0) | +9,1 (0,9) | +2,5 |
| GÜN D−1 | −4,2 (−0,3) | +7,0 (0,8) | +1,0 |
| GECE D | +2,4 (0,4) | −5,9 (−1,0) | +5,8 |
| **GÜN D (son seans)** | **+19,0 (2,1)** | **+33,3 (4,0)** | **+15,5** |
| **GECE D+1** | **−17,6 (−2,4)** | **−21,3 (−2,8)** | −2,5 |
| GÜN D+1 | −12,1 | −4,0 | −5,4 |
| diğerleri | |t| < 1 | |t| < 1,7 | |
Okuma: dengeleme akışı **ayın son seansında** fiyatı iter (en çok son yarım saatte, F1), **o gece geri verir**. R1'in 3 günlük tutuşunun
büyük kısmı tek seansta; geri kalan günler gürültü.

## Döngü v2 (sonradan birleştirme, karar dışı) — QQQ+SPY 2002-26, ay başına
| | ort bp | Sharpe | artı yıl | en kötü ay |
|---|---|---|---|---|
| R1 (D−3→D) | 28,0 | 0,61 | 19/25 | −513 |
| QS-04 döngüsü (R1 + E2 uzun) | 54,0 | 0,92 | 22/25 | −570 |
| **Son seans (GÜN+0)** | 17,2 | 0,81 | 20/25 | −237 |
| **v2 = son seans + gece tersi** | 29,5 | **1,11** | **24/25** | **−255** |
2014-26: v2 Sharpe 1,31, 13/13 yıl. Gece tersi bacakları: **uzun** (fonlar satıyordu) +23,9 (n 128, %74, P 1,00) · kısa +6,6 (P 0,74).
Broker 2018-26: v2 NAS100 +53,6 / US500 +54,1 bp/işlem ayı. **Ama** gece bacağının broker kazancı büyük ölçüde KSG'nin zaten uzun
olduğu gecelerde (KSG ile çakışan: NAS100 +28 / US500 +21; çakışmayan +8 / +0,4) → bot için gece bacağı KSG'ye ek değil.
Son seans ise KSG'den bağımsız (gün içi) ve R1'den çok daha kısa risk (6,5 saat vs 3 gün) ile aynı yönü yakalıyor.

## Son seans kartı (2. KURAL): 6/6
hacim 204 ay · +24,3 bp P 1,00 (ETF ortalaması) · yarılar +17,3 / +31,3 · broker NAS100+US500 ×1,5 spread +39,9 (P 1,00) · icra (Dukascopy
2021-26, 09:31 + spread vs 09:30) 72,7 / 75,8 · ayda bir seans. NAS100 broker ilk yarı +2,1 / ikinci +74,5; US500 +50,8 / +37,0.

## C — geri alım yasağı: X (ve bir olgu)
Ölçülen fark ters ve yabancı piyasalarda aynı büyüklükte → geri alım değil. Olgu (sonradan, karar dışı): ay dönümü günleri hariç
**çeyrek dönümü penceresi [Q−10, Q+15] 2004-26'da 16/16 yabancı + ABD'de günlük ~4,6 bp daha yüksek**; ABD 1993-2003'te yok. Olası
açıklama: bilanço sezonu primi (Savor–Wilson). Ayrı ön kayıt gerekir (backlog).

## Öneri
1. **Gölge listesine ekle: "son seans"** — ayın son işlem günü 09:30 ET'de R1 yönünde gir, 16:00'da çık (NAS100 ve US500). Döngünün en
   verimli parçası; R1'in yerine ya da R1 küçük lot + son seans büyük lot şeklinde düşünülebilir (karar kullanıcıda).
2. Gece tersi bacağını ayrıca bağlama (KSG zaten büyük kısmını alıyor). D−2 kapanış yarım saati (+5…+9 bp) küçük, düşük öncelik.
3. Uyarı: aynı ABD geçmişine bugün 17 hipotezle bakıldı; bu turun kararları seçimde kullanılmamış veride (2014-26, 1993-2002, broker,
   kör semboller) verildi ama hepsi aynı mekanizmanın parçaları — gölge ölçümü (≥ 12 ay) şart.
