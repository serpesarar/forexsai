# Korku gecesinin ertesi seansı: yalnız 09:30 → 16:00 AL (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/es.py`, kart `backend/data/evolution/go_live_cards/ndx_korku_ertesi_seans.json` (6/6, SHADOW).

## Sonuç: B (gün içi sürüm)
| besleme | ESKİ ort / taban | YENİ ort / taban | tüm n | σ | en kötü | P |
|---|---|---|---|---|---|---|
| NDX Duka | +51,8 / −0,1 | **+26,4 / −0,3** | 251 | 165 | −610 (YENİ −335) | 0,9998 |
| MT5 NAS100 | +44,6 / −2,2 | +23,1 / −0,4 | 234 | 165 | −607 | 0,9995 |
| EET30 | +39,3 / −5,0 | +23,0 / −1,6 | 222 | 164 | −600 | 0,999 |
| NQ 5m | +59,7 / −1,1 | +17,0 / +0,8 | 138 | 131 | −335 | 0,999 |
| **US30 (kör)** | +34,4 / −3,8 | +24,7 / +0,7 | 162 | 138 | −353 | 0,999 |
| **US2000 (kör)** | +13,9 / −8,1 | +27,1 / −4,4 | 234 | 156 | −473 | 0,994 |
| **US500 (kör, 2021→)** | +10,4 / +4,2 | +20,0 / +0,1 | 117 | 147 | −352 | 0,91 |

- Korku gecesinin (K1) ertesi günü nakit seansı tek başına +37 bp (tüm dönem). Taban ≈ 0. Gece boşluğu ve finansman riski yok.
- **Bağımsız bir kenar değil:** X1 (16:00 → ertesi 16:00) kazancının seans parçası, korelasyon 0,79. İşlem başına Sharpe 0,22, X1'de 0,27.
- **Kullanım:** gece pozisyon taşıyamayan (bot kuralı, risk sınırı) biri için korku gecesinin gün içi sürümü. Gece kuralıyla birlikte
  açılmaz, aynı riski iki kez alır.
- Defterdeki "toparlanmanın büyük kısmı ertesi seansta" notunun (§2.71) ölçülmüş hâli: X1'in ~%70'i seansta.
