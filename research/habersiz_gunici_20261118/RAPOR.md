# Habersiz gün içi sert düşüş → dönüş (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/hg.py`. Taban: aynı gruptaki günlerde rastgele 30 dk bar kapanışı girişi.

## Sonuç: C+ (ertesi gün çıkışı); aynı gün çıkışı X
Habersiz gün (CPI/NFP/FOMC/JH yok), 10:00–15:30 arası ilk 30 dk bar ≤ −e → sonraki 1m açılışında AL:

| e, çıkış | NDX ESKİ ort / taban | NDX YENİ | NDX tüm (n), P | olay günü aynı işlem | US30 (kör) | US2000 (kör) |
|---|---|---|---|---|---|---|
| %1, ertesi 16:00 | +37 / +12 | **+98 / +9** | +74 (86), 0,983 | **−126** (18) | +31 / +4 | +52 / +1 |
| %0,6, ertesi 16:00 | +26 / +12 | +30 / +9 | +29 (345), 0,936 | −64 (79) | +27 / +4 | +20 / +1 |
| %1 / %0,6, aynı gün 16:00 | −23 / −5 | +28 / +7 | +8 / +2 | | | |

- Habersiz günde sert düşüş ertesi güne kadar dönüyor; makro olay gününde aynı düşüş sürüyor (−64…−126 bp). §3-38'in en açık örneği.
- B eşiğinin (P 0,9875) hemen altında → C+.
- **K1 ile ilişki (bilgi):** %0,6 olaylarının %34'ü aynı gün K1 gecesine dönüşüyor. Dönüşmeyen 227 olay +52 bp (ESKİ +45, YENİ +56).
  K1'e dönüşen günlerde erken almak −16 bp (fiyat kapanışa kadar düşüyor). Yapı büyük ölçüde K1'den bağımsız. K1 girişte bilinmediği
  için filtre olarak kullanılamaz.
- **Öneri:** gölge etiketi ve ileri ölçüm. Olay günlerinde kesinlikle açılmamalı.

## EK-1 — bağımsız eski dönem ve besleme teyidi
- 2016–17 (Duka M30 + EET30): düşük oynaklık, olay yok denecek kadar az (n 10 / 2; %1'de n 1 / 0). Bilgi vermiyor → **C+ kalır**.
- Besleme teyidi güçlü: habersiz %1 düşüş → ertesi 16:00 MT5 NAS100 +73,8 (n 88), NQ +92,5 (22), US500 +148 (16); taban +4…+8.
  Olay günü aynı işlem her beslemede eksi (−26…−126). Olay günü SAT ayrı ön kayıtla sınandı: `olay_sat_20261118` (C+).
