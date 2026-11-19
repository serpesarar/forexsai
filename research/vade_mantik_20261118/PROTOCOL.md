# MX-01…03 — "vade yaklaşırken korku dönüşü çalışmaz" mantığının genişletilmesi

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Temel: §2.91 SV-01 (OPEX Çar/Per korku alımı vetosu, B).
Kurallar (günlük vekiller, defterde doğrulanmış): **C3b** RSI2(kapanış) < 10 → kapanışta AL, ilk yükselen kapanışta çık (≤ 5 g);
**K1** V1 (K ≤ (Y+D)/2 × 0,995 ∧ K < A) → kapanış → ertesi kapanış; gün içi K1 = `gn.nts` (16:00 TWAP, 5 besleme). Etiket her zaman
**giriş gününe** göre (E147). Maliyet 2 bp + finansman (uzun).

## MX-01 — vade döngüsü haritası (NASDAQ)
k = girişten sonraki aylık OPEX Cuma'sına kalan işlem günü. Kovalar: {0} vade günü, {1,2} veto (bilinen), {3–7}, {8–12}, {13–17}, {≥ 18}.
Setler: C3b QQQ 1999+, C3b ^NDX 1985–1999, K1 QQQ/SPY günlük, gün içi K1 5 besleme. Ölçü: kova − diğer kovalar (set içinde z, havuz).
Yeni kova adayı yalnız: havuz iki yönlü P ≥ 0,99 **ve** ^NDX 1985–99 ile 1999+ aynı işaret.

## MX-02 — çeyreklik vade ve kontrat devri
(a) Veto bölgesi (k ∈ {1,2}) çeyreklik (Mar/Haz/Eyl/Ara) vs aylık ayrı; (b) devir haftası = çeyreklik OPEX'ten önceki hafta
(k ∈ 5…9 ve ay çeyreklik): girişler vs diğerleri. Bilgi + P ≥ 0,95 ise aday.

## MX-03 — mekanizma doğal deneyi: yerel vade takvimleri
Günlük C3b ve K1, yabancı endekslerde. Yerel vade günü E: Nikkei 225 (2. Cuma, SQ), KOSPI (2. Perşembe), Hang Seng (ayın sondan bir
önceki iş günü), ASX 200 (3. Perşembe), Nifty 50 (son Perşembe; 2025-09 sonrası son Salı), TAIEX (3. Çarşamba); ABD ile aynı takvim
(3. Cuma, kopya değil replikasyon): DAX, Euro Stoxx 50, CAC 40, FTSE 100. Tatilse önceki işlem günü.
Yerel pencere = E'den önceki 2 işlem günü girişi. ABD penceresi = ABD OPEX Çar/Per girişi (aynı endekste).
Öngörü: farklı takvimli 6 piyasada **yerel** pencere eksi; **ABD** penceresi daha az eksi.
Geçme (mekanizma teyidi): yerel pencere farkı < 0 en az 4/6'da, havuz z P(< 0) ≥ 0,95 ve havuzda yerel farkı ABD farkından daha eksi.
3. Cuma piyasaları ayrıca: pencere farkı < 0 en az 3/4.

## Sonuç özeti (ilk koşu)
MX-01: k0 (vade Cuma'sı girişi) −0,23z P 0,9996 → veto bölgesi k ∈ {0,1,2}; **k13–17 +0,15z, 9/9 set artı, P(artı) ≈ 1,00, 1985–99 aynı işaret**
(ön kayıtlı aday ölçütünü geçti). MX-02: çeyreklik ≈ aylık; devir haftası X. MX-03: farklı yerel takvimli 6 piyasada yerel pencere
havuzu **artı** (P(eksi) 0,02) → mekanizma "her vade" değil, ABD OPEX'ine özgü; X.

## EK-1 (2026-11-18) — k13–17 ay dönümü etkisi mi?
k13–17 takvimde çoğunlukla ay dönümüne düşüyor (bir sonraki OPEX'ten ~3,5 hafta önce). Ay dönümü (TOM) = ayın son işlem günü + ilk 3
işlem günü (Lakonishok–Smidt). Ölçümler (aynı 9 set, z havuz): (a) TOM − TOM dışı; (b) k13–17 ∧ TOM dışı − diğer TOM dışı;
(c) TOM ∧ k13–17 dışı − diğer k13–17 dışı. Karar: (b) P(artı) ≥ 0,95 ise k13–17 bağımsız bilgi (vade döngüsü dozu); (b) ≈ 0 ve (a)
güçlüyse etki ay dönümü dozudur (ayrı kapı adayı: "ay dönümü korku alımı dozu"); ikisi de değilse X.

## EK-1 sonucu
k13–17'nin yalnız %27'si TOM; (b) TOM dışında k13–17 +0,151z P(artı) ≈ 1,00 → ay dönümü değil. TOM kendisi korku alımında zayıf (−0,065z).
Ama ^NDX 1985–99 C3b bu kovada −7 (n 40), C3b QQQ +10 zayıf; taşıyıcı K1 setleri.

## EK-2 (2026-11-18) — vade sonrası eksen: son OPEX'ten bu yana geçen işlem günü a
a = 1 vade sonrası Pazartesi. Kovalar a1–2 (bilinen X), **a3–7 (birincil: k13–17'nin 4 haftalık döngüdeki karşılığı, vade sonrası
Çarşamba → ertesi Salı)**, a8–12, a13–17, a18+. Aynı 9 set, z havuz. Geçme (doz kapısı B): birincil kova havuz P(artı) ≥ 0,99,
K1 günlük QQQ ve SPY ikisi de artı, gün içi K1 ≥ 4/5 artı, ^NDX 1985–99 C3b ≥ 0, iki kronolojik yarı (havuz) artı. TOM dışı alt küme ayrıca.
