# Ön kayıt — Rejime bağlı SAT ve coşku devamı (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "başka yapılar ara".

## Gerekçe
§3-37: NDX'te SAT kuralları (coşku SAT CC-01, ölü kedi GN-07) yalnız 2018 Q4 ve 2020 Mart ayı epizodlarında çalıştı. Hipotez: SAT
kenarı **ayı rejimine** bağlıdır. Rejim önceden ölçülürse SAT yalnız orada açılabilir. Ayna hipotez: boğa rejiminde coşku dönmez,
devam eder → AL. YENİ dönemde 2022 ayı piyasası var; bu yüzden ayı kolunun iki dönemde de bağımsız sınavı mümkün. Sinyaller daha önce
koşulsuz sınandı. Yeni tanım rejim koşulu (yeniden açma gerekçesi).

## Tanımlar (NDX Duka, gün d, 16:00 → d+1 16:00; SAT bid giriş / ask çıkış, finansman her iki yönde düşülür)
- **Rejim:** P16(d) < SMA200(P16, d dahil son 200 işlem günü) → AYI, değilse BOĞA. d'nin 16:00 fiyatı girişte bilinir.
- **C1 coşku:** P16 ≥ TWAP(09:30–16:00) × 1,005 ∧ son saat yukarı (K1 aynası).
- **C3 son saat rallisi:** 15:00 → 16:00 ≥ +%0,3 (K3 aynası).
- **OK ölü kedi:** K1(d−1) ∧ P16(d) / P16(d−1) − 1 ≥ +%1.

## Hipotezler (6 hücre)
- H-SAT: AYI ∧ {C1, C3, OK} → SAT. Taban: AYI'da koşulsuz SAT.
- H-AL: BOĞA ∧ {C1, C3, OK} → AL. Taban: BOĞA'da koşulsuz AL.

## Ölçütler (her hücre)
1. NDX ESKİ (→ 2021-10) ve YENİ'de ikisinde de ort > 0 ∧ > rejim tabanı.
2. Kör taşıma MT5 US30 ve US2000 (aynı tanım, kendi SMA200'leri): ikisinde de ort > rejim tabanı.
3. NDX tüm dönem P(tetik − taban > 0) ≥ 1 − 0,05/6 = 0,992.
Hepsi → B; 1+2 → C+; yalnız 1 → C; değilse X. Bilgi: n, σ, en kötü, yıllar.
