# Canlıya alma kartları + aday araştırması (2026-10-09)

Ön kayıt: `PROTOCOL.md`. Ölçütler CLAUDE.md 2. Kural. Kartlar `backend/data/evolution/go_live_cards/`.

## 1. VIX rejimi (VIXREG) — canlı işlem kartı (`live_card.py`)
209 karar (06-30 → 09-24), WR %56,9, **ortR +0,010**, P(EV>0) %56,8, yarılar +0,056/−0,035, tek pozisyon −0,000 →
**SHADOW**. Pozitif $'ın çoğu 3 BUY işleminden; 206 SELL ortR 0,000. GF-05'in "≈0,01R" bulgusunu canlı veri tekrarlıyor.
Aynı kart diğer canlı aileler: MOMSR 182 karar −0,014 (SHADOW) · CHREV 66 −0,016 (RED) · DAYCOMBO 31 **+0,281** (RED, hacim) ·
REENTRY 19 **+0,446** (RED, hacim; M2 dış-örneklem plasebosu zaten geçmemişti).

## 2. Sahte kırılım dedektörü — gölge işlem kartı (`fakeout_shadow_card.py`)
786 gölge karar (07-19 → 10-09), brüt +0,019R, spread sonrası **−0,068R**, P %1 → **SHADOW / elendi** (işlem stratejisi olarak).
NDX 88 karar +0,022R (RED), XAU −0,068, USOIL −0,130. Lab isabeti (%75) kırılım seviyesinden başlayan yarışı ölçüyor; teyit
mumundan sonra giren işlem yarışın bir kısmını kaçırıyor → isabet kazanca dönmüyor.

## 3. DAYCOMBO — görülmemiş veride yeniden kurulum (`daycombo_oos.py`)
Kural birebir (gece pozitif + 15m EMA20 trend + gövdeli yeşil 5m, 14:00–19:30 UTC, 80/110 puan, Cuma yok).
| dönem | n | ortR |
|---|---|---|
| OOS-A 2025 (Dukascopy, seçimde hiç görülmedi) | 195 | **−0,030** |
| IS 2026-02 → 07 (seçim verisi) | 130 | +0,090 |
| OOS-B 2026-07-29 → 10-02 | 31 | +0,226 |
| **Kart OOS-A+B** | 226 | +0,005, P %53 → **SHADOW** |
Yüzde ölçekli geometride 2025 −0,028 (254); Cuma dahil 2025 −0,015. Sadakat: canlı 31 işlemin 14'ü kopyada ±15 dk içinde
(bot kapıları/veri kaynağı farkı). Sonuç: canlıdaki +0,28R seçim dönemi + Ağustos–Ekim yükselişine özgü (IO-14 ile tutarlı).

## 4. CAPREV portföyü NDX + DAX (`ndx_gate_forge/caprev_pooled.py`)
NDX 107 (+0,240) + DAX 54 (+0,171, 2019+) = **161 işlem / 134 bağımsız gün**, WR %55,3, **ortR +0,217**, P(EV>0) %99,0,
CI [+0,031, +0,402], yarılar +0,064/+0,367, spread ×1,5 +0,213, kapanış-girişi +0,225, gün başına tek pozisyon +0,160,
pozitif yıl 7/10 → **6/6 → LIVE** (ön kayıttaki ≥100 bağımsız gün koşulu da tutuyor).
Uyarılar (kartı geçersiz kılmaz, boyutlandırmayı belirler): toplamın %64'ü en iyi 5 günden (+34,9 → +12,4R); ilk yarı zayıf;
NDX geçmişine 4+ tur bakıldı (E23) — DAX kuralı değiştirilmeden sınanmış bağımsız piyasa; M1 katı icra yalnız NDX 11 işlem;
ileri gölge kanıtı henüz 0 olay. Yılda ~16 işlem.

## Sonuç
Sınanan 5 adaydan (VIXREG, sahte kırılım fade, DAYCOMBO, CAPREV-NDX, CAPREV-portföy) kartı geçen tek scope **CAPREV portföyü**.
Öneri: küçük lotla canlı + DAX gölge kaydının Berlin saatiyle doğrulanması; kayıp senaryosu = 1R/işlem, yılda ~16 işlem.
