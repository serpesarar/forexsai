# GX-01…04 — takvimi kanıtlı kuralın açılma/doz kapısı olarak kullanmanın genişletilmesi

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Temel §3-46/§3-47: takvim yön değil, kanıtlı kuralın ne zaman çalıştığını söyler.
Setler (vm.nasdaq_sets, 9): C3b QQQ 1999+, C3b ^NDX 1985–99, K1 QQQ/SPY günlük, gün içi K1 Duka + MT5 NAS100/US500/US30/US2000.
Ölçü: alt küme − diğerleri, set içi z, havuz bootstrap. Etiket giriş gününe göre (E147).

## GX-01 — vade döngüsü × canlı kural kitabı
`ndx_10y_1m_20261116/results/a_trades.parquet` (Duka 2018–26): her kural için k0–2 (veto) ve a3–7 (vade sonrası) kovaları vs diğerleri.
Öngörü: dönüş kuralları (C3B, C3, CAPREV, ÇEKİÇ) korku ailesiyle aynı profil; ORB×VIX uzun k0–2'de kötü (SV-02); KSG/AYSONU/FOMC etkisiz.
Bağımsız: ORB genel sürümü NQ 5m + MT5 M15 (örtüşmesiz). Kural başına kapı: fark P ≥ 0,95 ve ESKİ/YENİ iki yarı aynı işaret → B adayı.

## GX-02 — FOMC döngüsü çift haftası × korku alımı ("Fed put" mekanizması, Cieslak–Morse–Vissing-Jorgensen 2019)
FOMC tarihleri: Fed tarihsel takvim sayfaları 1994–2007 (`data/fomc_1994_2007.csv`) + `calendar.csv` 2008+. Hafta t = ⌊(k + 1)/5⌋,
k = son FOMC'den işlem günü (FOMC'den önceki gün hafta 0). Çift t ∈ {0, 2, 4, 6}. **Öngörü (makale, düşüş sonrası Fed iletişimi): çift
haftada açılan korku alımı daha iyi.** Geçme B: havuz P(artı) ≥ 0,95; yayın öncesi 1994–2016 ve **yayın sonrası 2017+** ikisi de artı,
2017+ P ≥ 0,90; ≥ 6/9 set artı.

## GX-03 — mega-cap bilanço sezonu × korku alımı (§3-38 haber hareketi sürer)
Bilanço yoğunluğu = Ocak/Nisan/Temmuz/Ekim'in 18.–30. takvim günleri (ayın son işlem günü hariç, ay dönümü karışmasın). Öngörü: bu
pencerede korku alımı daha kötü (düşüş haber kaynaklı). Geçme B: havuz P(eksi) ≥ 0,95, ≥ 6/9 set eksi, ^NDX 1985–99 aynı işaret.

## GX-04 — tatil öncesi korku alımı (iki yönlü)
Giriş günü ABD borsa tatilinden (hafta sonu dışı) önceki son işlem günü; tutuş tatili aşar. QS-03 R2 tatil öncesi sürüklenme artı;
TS-01 tatili aşan KSG −17,5 (n 26). İki yönlü: havuz |fark| P ≥ 0,975 ve 1985–99 aynı işaret → aday.

## Sonuç (ilk koşu) ve EK-1
GX-02 Fed put: 1994–2016 +0,083z (P 0,97) → **2017+ −0,103z (P(eksi) 0,985)** → X (yayın sonrası döndü). GX-03 bilanço sezonu X (≈ 0).
GX-04 tatil öncesi C (n küçük). GX-01: C3B/C3 veto teyit; **canlı KSG (son nakit saati aşağı → gece) OPEX k0–2'de −13 bp (P 0,971),
ESKİ −16 / YENİ −10** → B adayı; ÇEKİÇ hem veto hem vade sonrası kovasında eksi (korku profili değil).
**EK-1 — KSG OPEX vetosu bağımsız beslemelerde:** `ksg_dogrulama.ksg_m30` (15:00→16:00 aşağı → 16:00 AL → ertesi 09:30) MT5 NAS100 M30
2018+, MT5 NAS100 H1 2016–18, EET30 2016–25, NQ 5m 2019–24; kör piyasa MT5 US500/US30/US2000. Giriş günü k ∈ {0,1,2} vs diğerleri.
Geçme B: kör 3 piyasa + NDX beslemelerinin ≥ 5/7'si eksi, örtüşmesiz havuz (NDX: H1 2016–18 + MT5 2018+; + 3 kör) z P(eksi) ≥ 0,95.
