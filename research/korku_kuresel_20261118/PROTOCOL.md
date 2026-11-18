# Ön kayıt — Korku gecesi küresel mi? K1/K3'ün ABD dışı endekslere taşınması (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "daha fazla keşfet".

## Gerekçe
K1 (TWAP altı kapanış ∧ son saat aşağı) ve K3 (son saat ≤ −%0,3) NDX'te B (§2.71). Kurallar ABD'nin üç endeksine taşındı (GI-02 B+),
altına taşınmadı. Mekanizma "kapanışta emilen korku → toparlanma" ise başka nakit seanslarında da görülmeli. Görülmüyorsa etki ABD'ye
özgü akışlardan geliyor demektir (kapanış müzayedesi, 0DTE, ETF dengelemesi). §2.48 DAX-KSG (yalnız son saat aşağı → gece) X idi;
K1 ve K3 hiçbir yabancı endekste sınanmadı.

## Veri (Dukascopy 1m BID; spread = 2025 Çarşamba ASK − BID medyanı, sabit)
| endeks | saat dilimi | nakit açılış → kapanış (giriş) |
|---|---|---|
| DAX | Europe/Berlin | 09:00 → 17:30 |
| CAC | Europe/Paris | 09:00 → 17:30 |
| STOXX (EuroStoxx 50) | Europe/Berlin | 09:00 → 17:30 |
| UK100 (FTSE) | Europe/London | 08:00 → 16:30 |
| JPN225 (Nikkei) | Asia/Tokyo | 09:00 → 15:00 (2024-11 sonrası kapanış 15:30 oldu; ön kayıtla tüm yıllarda 15:00) |
Referans: NDX Duka (16:00 NY, §2.71 ile aynı).

## Kurallar (değiştirilmeden)
- **K1:** kapanış fiyatı ≤ açılış→kapanış TWAP × (1 − %0,5) ∧ kapanış < 60 dk önceki fiyat.
- **K3:** kapanış / 60 dk önceki − 1 ≤ −%0,3.
- Kapanış barında AL (ask), ertesi işlem günü aynı saatte çık (bid). Finansman `lib.FIN_BP_PER_DAY` (NDX değeri, yaklaşık).
- Geçerli gün: hafta içi, iki günde de kapanış barı ±5 dk içinde var.
- Taban: aynı giriş/çıkış, tetiksiz günler. P = gün-küme bootstrap (fark > 0).

## Ölçütler (seçim yok; her endeks × kural tek hücre)
- Endeks "taşındı": n ≥ 30 ∧ ESKİ (2018–2021-10) ve YENİ (2021-11 →) ikisinde de tetik ort > 0 ve > taban ∧ tüm dönem P ≥ 0,90.
- **Küresel B:** 5 endeksin ≥ 3'ünde taşındı ∧ havuzlanmış fark (tarih kümeli bootstrap) P ≥ 0,95.
- 1–2 endeks → "bölgesel iz" C; 0 → "ABD'ye özgü" (X olarak yazılır, mekanizma bilgisi).
- Bilgi: spread × 1,5, isabet, en kötü işlem, yıl yıl.
