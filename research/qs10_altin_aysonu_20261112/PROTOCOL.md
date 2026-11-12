# QS-10 — Ay sonu dengeleme testlerinin altına (XAUUSD) taşınması — ön kayıt (2026-11-12)

Kullanıcı: "Aynı testleri, aynı denemeleri altın üzerinde yap." Aynı testler = QS-03…07 ay sonu ailesi (canlıya bağlanan son seans + ay başı uzun
bu aileden). QS-09'un günlük hücreleri XAUUSD'de zaten koşuldu (3 tur, X) — tekrarlanmaz. Sonuçlar görülmeden yazıldı.

## Öncül (sonuçtan önce)
Emeklilik dengelemesi hisse ↔ tahvil arasında; altın bu akışın doğrudan parçası değil. Altına geçiş ancak tahvil bacağı (faiz) veya risk-parite
fonları üzerinden olabilir → beklenti zayıf. Defterde altın için takvim/akış etkisi kanıtı yok (MK-07, XAU gün içi X'ler).

## Sinyaller (D = ayın son işlem günü, ABD takvimi)
- **S1** = SPY − TLT ay içi getiri farkı, D−3 kapanışında (canlı kuralın sinyali). |S1| ≥ %2 → işaret.
- **S2** = GLD'nin kendi ay içi getirisi, D−3 kapanışında (altının kendi ay itişinin dengelenmesi). |S2| ≥ %2 → işaret.
- E2 penceresinde sinyal D kapanışındaki değer (S1_D, S2_D), QS-04'teki gibi.

## Pencereler (GLD günlük, düzeltilmiş açılış/kapanış; 2 bp maliyet)
| kod | pencere | QS karşılığı |
|---|---|---|
| R1 | D−3 kapanış → D kapanış | QS-03 R1 |
| SON | D açılış 09:30 → D kapanış 16:00 | QS-06 son seans (canlı) |
| GECE | D kapanış → D+1 açılış | QS-06 gece tersi |
| E2 | D kapanış → D+3 kapanış | QS-04 E2 ay başı (canlı) |
Her hücre iki yönde (sinyalle AYNI / TERS) → 2 sinyal × 4 pencere × 2 yön = **16 hücre**.

## Seçim ve karar (tek seçim, E23)
1. KEŞİF 2004-12 → 2014-12: 16 hücre içinden net t'si en yüksek **tek** hücre seçilir.
2. Yalnız o hücre: (a) TEST 2015-01 → 2026-10 net ort > 0 ve bootstrap P ≥ %90; (b) TEST'in iki kronolojik yarısı ≥ 0;
   (c) broker XAUUSD 2018-06 → 2026-10 aynı pencere ET saatleriyle (09:30 / 16:00), gerçek maliyet × 1,5 + swap ile net > 0;
   (d) destek (karar dışı): GC=F günlük 2000-08 → 2004-11 aynı işaret mi (kısa, ~50 ay).
3. (a)(b)(c) → **B−** (sonra kart) · yalnız (a) → **C** · diğer → **X**. 16 hücrenin TEST sonucu ve Holm düzeltmesi şeffaflık için raporlanır.
4. Sıklık notu: bu aile ayda en çok 1 işlem açar; 15–20/ay hedefi için değildir.
