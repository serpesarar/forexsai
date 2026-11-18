# NDX korku gecesi → Avrupa endeksleri ertesi gün (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md) (EK-1 dahil), kod `src/na.py` (`ana`, `sabah`).

## Sonuç: B (ön kayıt), ama küçük ve gece boşluğundan geliyor
**İlk koşu geçersiz.** Dukascopy CAC/Stoxx verisi 21:59 Berlin'de bitiyor. Bu yüzden NDX 16:00 (22:00 Berlin) yalnız yaz saati uyumsuz
haftalarda eşleşti (n 44 / 22) ve sonuç şişti (Stoxx +94 bp). EK-1 ile giriş "NY 16:00'da ya da sonrasındaki ilk bar" oldu:

| endeks | ESKİ ort / taban | YENİ ort / taban | tüm n | P |
|---|---|---|---|---|
| DAX (22:00 giriş → ertesi 17:30) | +28,1 / −2,6 | +5,2 / −1,3 | 245 | 0,978 |
| CAC (ertesi 08:00 → 17:30) | +26,3 / −4,8 | +6,5 / −2,8 | 212 | 0,988 |
| STOXX (ertesi 08:00 → 17:30) | +22,3 / −9,9 | +8,4 / −6,9 | 209 | 0,997 |
| UK100 (22:00 → ertesi 16:30) | +22,2 / −3,3 | −4,7 / −0,7 | 242 | 0,86 |
Havuz P 0,987, 3/4 → **B**.

**Ama:**
- YENİ'deki etki +5…+8 bp (tabana göre +7…+15), NDX'in kendisinde +44 bp.
- EK-1 (b): Avrupa'nın sonraki nakit seansında (09:00 → 17:30) almak ≈ 0 (DAX +3,5 vs +0,6, UK100 −3,7).
  Kazanç ABD'nin gece toparlanmasının Avrupa açılışından önce fiyatlanan kısmı.
- **Pratik sonuç:** korku gecesini Avrupa endeksiyle işlemenin NDX'e göre bir üstünlüğü yok. Avrupa'nın kendi seansı NDX korkusundan bilgi
  almıyor. Bulgu mekanizmayı doğruluyor: toparlanma ABD'de üretiliyor, Avrupa yalnız gece yansımasını taşıyor.
