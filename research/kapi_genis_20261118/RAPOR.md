# GX-01…05 — takvimi kanıtlı kuralın açılma/doz kapısı olarak genişletmek (2026-11-18)

Ön kayıt `PROTOCOL.md` + EK-1. Kod `src/gx.py`, `src/ek1_ksg.py`; çıktılar `results/`. Kart `go_live_cards/ndx_ksg_opex_vetosu.json` (6/6).

| ID | Kapı | Sonuç | Hüküm |
|---|---|---|---|
| **GX-05** | **KSG OPEX vetosu** — canlı KSG (15:00→16:00 aşağı → 16:00 AL → ertesi 09:30) OPEX'e 0–2 işlem günü kala açılmaz | Duka canlı kitap −13 bp fark (P 0,971; ESKİ −16 / YENİ −10); bağımsız 6/6 besleme eksi: MT5 NAS100 −9, EET30 −12, NQ −14, kör US500 −16, US30 −9, US2000 −22; örtüşmesiz havuz −0,18z P 1,00; vetolananlar Duka −4,7 bp vs kalan +8,4, kör −9,2 (P 0,99); toplam +%11, işlem −%15; kart 6/6 | **B** (veto) |
| GX-01 | Vade döngüsü × canlı kitap | C3B −104 / C3 −74 (iki yarı eksi, SV-01 teyidi); ORB×VIX −0,3R (C+ kalır, bağımsız zayıf); ÇEKİÇ veto −0,3R (P 0,95, ESKİ zayıf) **ve** vade sonrası da −0,3R → korku profili değil; CAPREV n 8; AYSONU/FOMC kovaya düşmüyor | ÇEKİÇ C |
| GX-02 | FOMC çift haftası × korku alımı ("Fed put") | 1994–2016 +0,083z (P 0,97) → **2017+ −0,103z (P(eksi) 0,985)**; set 2/9 artı | X (yayın sonrası döndü) |
| GX-03 | Mega-cap bilanço sezonu (Ocak/Nisan/Temmuz/Ekim 18–30) × korku alımı | +0,035z, 3/9 set; 1985–99 −0,10 | X |
| GX-04 | Tatil öncesi korku alımı (tutuş tatili aşar) | −0,11z P 0,87; K1 QQQ/SPY −32 bp; n küçük | C |

Ders: OPEX veto bölgesi yalnız RSI2/korku gecesi değil, **canlı KSG** gibi "kapanışa doğru satıştan sonra gece al" kurallarını da
bozuyor; ORB×VIX'te zayıf, çekiçte farklı profil. Yayınlanmış "Fed put" döngüsü korku alımı dozu olarak da yayın sonrası döndü (§3-44).
