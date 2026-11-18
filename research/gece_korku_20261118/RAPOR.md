# Gece seansı (ETH) korkusu → sabah alımı (2026-11-18)

Ön kayıt: [PROTOCOL.md](PROTOCOL.md). Kod: `src/gk2.py` (`kesif`, `dogrula`, `ayna`).

## Sonuç: X

Önceki 16:00'dan sonra gece seansında oluşan korkuyu üç biçimde ölçtüm:
- gece düşüşü,
- gece ortalamasının (TWAP) altında kalma,
- gece dibine yakınlık.

Alım saati 03:00, 08:00 veya 09:30, çıkış 09:30, 16:00 veya ertesi gün 16:00. Toplam 48 hücre.

- **Izgara şans düzeyinde:** 2018–21'de 2 aday çıktı. Kaydırılmış tetik plasebosunda aday sayısının medyanı 4,5, %95'i 10.
- Dondurulan iki aday YENİ dönemde (kör) çöktü:
  - Gece TWAP'ının ≥ %0,3 altı, 03:00 AL, ertesi gün 16:00 çık: −14,7 bp, tabana göre −20,6. Korku gecesi dışında da eksi.
    EET30'da −0,6, NQ'da −10,9.
  - Aynı tetik, 08:00 AL, 09:30 çık: −1,9 bp. Sürtünme sonrası eksi.
- Ayna (gece coşkusunu satmak) da boş.

## Ne öğrendik
Korku gecesi ailesindeki toparlanma **nakit seansının kapanışında emilen korkuya** özgü. Gece seansındaki düşüş dönmüyor: büyük
olasılıkla haber ya da bilgi taşıyor (HB-03 "haber oynaklık taşır, yön taşımaz" ile tutarlı). Kapanış korkusu ise akış kaynaklı
(kapanış müzayedesi, günlük riskten çıkma) ve geri dönüyor. Bu yüzden korku ailesinde karar anı 15:00–16:00 kalmalı.
