# Ön kayıt — Gizli korku: VIX sıçradı ama fiyat düşmedi (2026-11-18)

Sonuçlara bakılmadan yazıldı.

## Gerekçe
VE-02: koşulsuz VIX sıçraması (≥ +%15/+%25) → ertesi gün X; 5 gün tutuşta −41 bp. Yeni tanım: **opsiyon ile fiyat arasındaki ayrışma**.
VIX yükselirken NDX nakit seansı düşmemişse korunma talebi fiyata yansımamış demektir. İki yön de önceden tanımlı:
- H-düşüş: opsiyon piyasası önden gidiyor, fiyat sonra düşer.
- H-yükseliş: korunma alındı, satış baskısı oluşmadı, fiyat yükselir.

## Tanım
- Sinyal günü d: VIX_close(d) / VIX_close(d−1) − 1 ≥ v, v ∈ {%8, %12} ∧ NDX d 09:30 → 16:00 getirisi > −%0,3 (gizli).
- Karşılaştırma: aynı VIX sıçraması ∧ NDX ≤ −%0,3 (açık korku), ayrıca koşulsuz taban.
- VIX kapanışı 16:15'te bilinir → giriş **d+1 09:30** (ask), çıkış d+1 16:00 veya d+2 16:00 (bid). AL getirisi ölçülür; SAT bunun
  aynasıdır (maliyetler ayrıca).
- 2 eşik × 2 çıkış = 4 hücre.

## Ölçüt
- D = ort(gizli) − ort(koşulsuz taban). NDX Duka'da ESKİ ve YENİ'de aynı işaret ∧ tüm dönem |P| ≥ 1 − 0,05/4 = 0,9875 ∧ MT5 NAS100,
  US30 ve US2000'de (M30, kör) aynı işaret.
- Hepsi → B (işaretin yönünde AL ya da SAT kuralı); aynı işaret iki dönem + 3/3 besleme, P eşik altı → C+; yalnız iki dönem → C; değilse X.
