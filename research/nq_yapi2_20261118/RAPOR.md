# NB-01…04 — NASDAQ yeni yapılar (2026-11-18)

Ön kayıt `PROTOCOL.md`. Kod `src/gunluk2.py`, `src/strike.py`; çıktılar `results/gunluk2.json`, `results/strike.json`.
KEŞİF → 2021-10, TEST 2021-11 → 2026-11 (günlük); NB-04 çağları ESKİ 2018-04 → 2022-10 / 0DTE 2022-11 →.

| ID | Yapı | Sonuç | Hüküm |
|---|---|---|---|
| NB-01 | Gece/gün içi çekişmesi (Σ20 gece − Σ20 gün içi) | QQQ: üst %20 → 5 g AL KEŞİF +7,7 bp (P 0,59), TEST +34 (P 0,87); 20 g TEST −72. **SPY'de güçlü**: üst %20 → 5 g KEŞİF +16 (P 0,90), TEST +60 (P 0,997, 6/6 yıl) — NASDAQ'a taşınmıyor | NASDAQ C · (SPY'de B adayı, kapsam dışı) |
| NB-02 | Yoğunlaşma (QQQ/QQQE 20 g göreli) | Dar liderlik → AL KEŞİF 5 g +27 (P 0,85), TEST +34 (P 0,92), 20 g TEST +79 (P 0,81); SPY/RSP KEŞİF'te ters yön seçti, TEST 20 g +90 (P 0,95). Geniş liderlik KEŞİF artı → TEST −74 / −194 (yön döndü) | C (son 5 yıl mega-cap devamı) |
| NB-03 | Hisse–kredi uyumsuzluğu (HYG/IEF) | D1 kredi bozulurken hisse yükseliyor → 20 g SAT: KEŞİF fark +106 / SPY +108 (P 0,84 / 0,97), TEST +43 / +25 (P 0,57) — net hâlâ eksi (uzun sürüklenme). D2 n 45, SPY'de ters | D1 C · D2 X |
| NB-04 | QQQ strike çekimi 15:00 → 16:00 (0DTE çağı) | Gerçek ızgara dokunuşu = plasebo (0DTE Cuma dışı %75,1 vs %76,9; Cuma %80,0 vs %80,6), fark ≈ 0 bp, MT5 aynı; vekil hatası medyan $0,07 | X |

Dersler: (1) 0DTE hacmi QQQ fiyatını gün sonunda strike'a çekmiyor (en azından $1 ızgarada, 15:00 sonrası). (2) Gece/gün içi çekişmesi
geniş piyasada (SPY) bilgi taşıyor, teknoloji endeksinde zayıf. (3) Yoğunlaşma ve kredi çaprazları yön değiştiriyor ya da TEST'te
zayıflıyor; rejim etiketi olarak bile yetersiz. Kart yok.
