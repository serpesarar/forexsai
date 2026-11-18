# Bitcoin'de ABD korkusu ve haber ayrımı (2026-11-18)
Ön kayıt [PROTOCOL.md](PROTOCOL.md), kod `src/bh.py`. Binance 5m 2017-08 → 2026-10; CFD maliyeti 4 bp + 3,84 bp/gece.

| hipotez | ESKİ ort / taban | YENİ ort / taban | P | hüküm |
|---|---|---|---|---|
| H1a NDX K1 → BTC gece (16:00 → 09:30) | +6,8 / +15,7 | +21,8 / +2,1 | 0,61 | X |
| **H1b NDX K1 → BTC ertesi ABD seansı (09:30 → 16:00)** | +12,1 / +4,5 | **+37,3 / −16,4** | 0,975 | **C+** |
| H1c tam gün (YK-06 referansı) | +20,4 / +24,2 | +61,9 / −10,3 | 0,92 | X (ESKİ taban altı) |
| H2 habersiz ABD günü BTC 30 dk ≤ −3σ → ertesi 16:00 | +37,8 / +27,2 | +34,1 / +1,7 | 0,77 | C+ (zayıf) |
| H2 −4σ | +8,4 / +27,2 | −5,3 / +1,7 | 0,41 | X |
| H3 olay günü büyük BTC hareketi devam (2σ) | +394 / −10 (n 10) | +51,5 / +46,3 (n 12) | 0,92 | C+ (birkaç uç olay; pratikte X) |

- NDX korkusunun BTC'ye taşınan kısmı ertesi ABD seansında. NDX'te de aynı (YK-08 B). Toparlanma ABD seans akışında üretiliyor.
- Habersiz ABD günündeki sert BTC düşüşü olay günündekinden iyi (olay günü ESKİ −130, n 14). İlke BTC'de de var, ama zayıf.
- BTC'nin kendi kenarlarını arayan 36 fikirlik eski aileye (§2.11–2.12) yeni bir B eklenmedi.
