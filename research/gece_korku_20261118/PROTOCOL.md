# Ön kayıt — Gece seansı (ETH) korkusu → sabah alımı (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "daha fazla keşfet".

## Gerekçe (defter 3. KURAL)
Korku ailesi (§2.68–2.77) yalnız **nakit seansı kapanışındaki** korkuyu ölçtü. GI-01 seans içi karar saatlerini (10:30/12:00/14:00)
sınadı → X. SD-01 gece seanslarının **koşulsuz** yönünü sınadı → X. IG-02 "400 puan düşüş sabahı AM uzun" ölçüsü bir Instagram
iddiasının sınamasıydı (kendi ön kaydıyla değil). **Yeni tanım:** önceki 16:00 kapanışından sonra gece seansında (ince Asya/Avrupa
likiditesi) oluşan korku. Mekanizma "korku döner" (§3-2); soru, gece korkusunun sabah/nakit seansında dönüp dönmediği.

## Veri
Dukascopy NDX 1m (lib.load_m1, 2018-04 →), seçim. Bağımsız: MT5 NAS100 M30, EET30 30m, NQ 5m (gece barları var; kontrol edildi).

## Tanımlar (gün D, önceki işlem günü D−1; NY saati)
- P0 = D−1 16:00 fiyatı. Pencere = D−1 18:00 → D T (gece seansı; Pazartesi için Pazar 18:00'dan itibaren).
- Karar saati T ∈ {03:00 (Londra açılışı), 08:00, 09:30}. Giriş T barının açılışı + spread (ask).
- **G1 gece düşüşü:** P_T / P0 − 1 ≤ −eşik, eşik ∈ {%0,5, %1,0}.
- **G2 gece TWAP altı:** P_T ≤ pencere TWAP × (1 − eşik) ∧ son 60 dk aşağı; eşik ∈ {%0,3, %0,5}.
- **G3 gece dibine yakın:** (P_T − dip)/(tepe − dip) ≤ eşik ∧ pencere aralığı ≥ %1; eşik ∈ {0,10, 0,20}.
- Çıkış (bid): 09:30 (yalnız T < 09:30), D 16:00, D+1 16:00. Finansman takvim gecesi başına.
- Hücre: 3 tetik × 2 eşik × (03:00: 3 çıkış, 08:00: 3, 09:30: 2) = 48.
- Taban: aynı giriş/çıkış tetiksiz günler. P = gün-küme bootstrap (fark > 0).

## Seçim (ESKİ 2018-04 → 2021-10)
Geçen: n ≥ 25, tetik ort > 0, fark > 0, P ≥ 0,90. Izgara plasebosu: tetik maskesi rastgele ±1…10 işlem günü kaydırılır (20 tekrar);
gerçek aday sayısı plasebonun %95'ini geçmezse ızgara şans düzeyidir. t'ye göre en iyi ≤ 4 hücre dondurulur (tetik başına ≤ 2).

## Doğrulama (dondurulan her hücre)
1. YENİ (2021-11 → 2026-11, kör): ort > 0 ∧ P ≥ 1 − 0,10/4 = 0,975.
2. Beslemeler MT5 / EET30 / NQ (tüm dönem): üçünde de tetik ort > taban ∧ > 0.
3. **Korku gecesinden bağımsızlık:** D−1 korku skoru S = 0 olan günlerde (§2.75 bayrakları) de ort > 0, fark > 0, P ≥ 0,90
   (yoksa bu, zaten açık olan korku gecesi pozisyonunun devamıdır).
4. Sürtünme: spread × 1,5 ile ort > 0. 5. Hacim: tüm dönem n ≥ 150.
Hepsi → B; 1+2 → C+; değilse X. B çıkarsa 2. KURAL kartı (SHADOW).

## Ayna (bilgi, seçimsiz)
Aynı üç tetiğin yukarı hâli (gece coşkusu) → SAT, dondurulan hücrelerin giriş/çıkışıyla; yalnız raporlanır.
