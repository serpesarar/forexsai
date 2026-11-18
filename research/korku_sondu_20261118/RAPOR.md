# "Korku söndü": VIX zirveden hızlı iniş → çok günlü AL (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/ks.py`. Günlük QQQ/SPY + VIX, 1999–2026; maliyet 2 bp + CFD finansmanı (taban da öder).

## Sonuç: C+ (az epizod, büyük kuyruk)
Dondurulan (KEŞİF 1999–2011 t'sine göre): VIX ≤ 10 günlük zirvenin %80'i ∧ zirve ≥ 30 → ertesi kapanış AL.

| hücre | KEŞİF 99–11 fark (n) | TEST 12–21 fark (n) | YENİ 21–26 fark (n) | TEST+YENİ P | SPY (kör) | en kötü |
|---|---|---|---|---|---|---|
| 10 gün tut | +156 (26) | +206 (11) | +227 (8) | 0,91 | +75 | −1.630 |
| 20 gün tut | +177 (26) | +295 (11) | +216 (8) | 0,92 | +127 | −1.946 |

- Üç dönemde ve SPY'da artı, ama TEST+YENİ yalnız 19 epizod → P B eşiğinin (0,975) altında.
- Seçilmemiş bir hücre (zirve ≥ 25, 20 gün) üç dönemde +98 / +315 / +107, P 0,985. Bilgi; seçimden sonra bakıldı, kanıt sayılmaz.
- Daha sert iniş eşiği (%30) 1999–2011'de eksi (dot-com ayısında VIX'in inmesi dip değildi).
- Mekanizma (oynaklık hedefleyen fonların yeniden kaldıraç alımı) uyumlu. Uzun ayı piyasasında çalışmıyor; kuyruk riski büyük.
