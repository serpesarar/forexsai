# Ön kayıt — Haftalık korku: hafta, haftanın ortalamasının çok altında kapandıysa (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
K1 gün ölçeğinde B (§2.71). Bir üst ölçek sınanmadı. BG ailesi (zirveden %8, 3 düşen hafta) çok haftalık geri çekilmelere baktı;
"Cuma K1" K1'in bir alt kümesiydi (X). Yeni tanım: **hafta içi TWAP**'a göre kapanış.

## Tanım (haftanın son işlem günü F, 16:00)
- Hafta TWAP = haftanın nakit seansı (09:30–16:00) 1m kapanışlarının ortalaması.
- **W1:** P16(F) ≤ hafta TWAP × (1 − %1) ∧ F günü 15:00 → 16:00 aşağı.
- **W2:** hafta getirisi (önceki F 16:00 → F 16:00) ≤ −%3.
- F 16:00 AL (ask). Çıkış: sonraki işlem günü 16:00 (hafta sonu taşıması) veya sonraki haftanın son günü 16:00. Finansman takvim gecesi başına.
- 2 tetik × 2 çıkış = 4 hücre. Taban: tetiksiz hafta sonları (aynı gün türü, E114 karıştırıcısı yok).

## Ölçüt
NDX Duka ESKİ ve YENİ'de ikisinde de ort > 0 ∧ > taban; tüm dönem P ≥ 1 − 0,05/4 = 0,9875; kör MT5 NAS100, US30, US2000'de ort > taban.
Hepsi → B; P hariç hepsi → C+; yalnız iki dönem → C; değilse X. Bilgi: K1 haftasonlarıyla örtüşme (W1 ∧ ¬K1(F) ayrıca).

## EK-1 — Bağımsız eski dönem: günlük ETF 1993/1999 → 2017 (YK-03 sonuçları görüldükten sonra, tek hücre, seçimsiz)
W2 (hafta getirisi ≤ −%3, haftanın son işlem günü kapanışından ölçülür) → o kapanışta AL, sonraki haftanın son kapanışında çık.
Veri: `qs03_akis_takvim_20261111/data/` QQQ (1999-03 →), SPY (1993 →), DIA, IWM; **dönem 1993/1999 → 2017-12** (Duka/MT5 dönemiyle
örtüşmez). Maliyet: 2 bp + CFD finansmanı `lib.FIN_BP_PER_DAY` × takvim günü (taban da öder). Taban: tüm haftalar.
Ölçüt: QQQ'da ort > taban ∧ > 0, hafta-bootstrap P(fark) ≥ 0,95; SPY/DIA/IWM'nin ≥ 2'sinde fark > 0 → W2 **B**'ye yükselir.
Değilse C+ kalır (ya da her şey ters ise X). Bilgi: alt dönemler 1999–2002 / 2003–2007 / 2008–2009 / 2010–2017, en kötü hafta.
