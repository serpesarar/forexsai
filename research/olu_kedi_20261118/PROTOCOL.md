# Ön kayıt — Korku sonrası "ölü kedi sıçraması" SAT (2026-11-18)

Sonuçlara bakılmadan yazıldı. Kullanıcı: "farklı yönlerde işlemler de dene".

## Gerekçe
"Korku döner, coşku dönmez" (§3-2). CC-01 koşulsuz coşkuyu satmak: X. Yeni soru, koşullu coşku: korku gecesinin (K1) ertesi günü güçlü
toparlanma olduysa (yüksek oynaklık rejimi sürüyor), sonraki gece fiyat geri düşüyor mu? Defterde yok.

## Tanım (16:00 → 16:00, NY)
- d: K1 günü (§2.71). d+1: toparlanma günü. R = P16(d+1) / P16(d) − 1.
- **OK(e):** K1(d) ∧ R ≥ e, e ∈ {%1, %2}. d+1 16:00'da SAT (bid), d+2 16:00'da kapat (ask). Finansman uzunla simetrik kabul edilip
  düşülür (muhafazakâr).
- Karşılaştırma 1 (koşulun değeri): K1 olmadan R ≥ e olan günlerden sonra aynı SAT.
- Karşılaştırma 2 (taban): koşulsuz her günden sonra SAT.

## Ölçütler (tek hücre / eşik; seçim yok)
- NDX Duka ESKİ ve YENİ ikisinde de OK SAT ort > 0 ∧ > karşılaştırma 1.
- Kör taşıma MT5 US30, US2000: ikisinde de OK SAT ort > 0.
- Tüm dönem P(OK − karşılaştırma 1 > 0) ≥ 0,95 (iki eşik → 0,975).
- Hepsi → B; NDX iki dönem + taşıma 1/2 → C; değilse X.
