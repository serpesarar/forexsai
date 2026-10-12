# MOM-H "20 mumluk yeni tepede al" — bağımsız piyasa sınavı (ön kayıt, 2026-10-10, XAU/USOIL verisine BAKILMADAN)
Köken: deep.py T5'te NDX/DAX'ta (görülmüş veri) "yeni tepe → BUY T20" rastgele BUY'ı 7 setin 6'sında geçti.
H1: high ≥ önceki 20 mumun en yükseği → sonraki açılışta BUY, 20 mum sonra kapanış. H1b: + üst fitil < aralık/3.
Ayna (kontrol): low ≤ önceki 20 mumun en düşüğü → SELL T20 (korku döner ilkesine göre çalışmamalı).
Setler: XAUUSD ve USOIL 15m / 30m / 1h (candle_cache; 2026-09-03+ Yahoo vadelisi — ayrıca hariç tutulmuş sürüm raporlanır).
Maliyet: spread XAU 0,25 / USOIL 0,03 (ATR'ye bölünür). Taban: aynı set, aynı yön, tüm mumlarda giriş (her 3. mum).
GEÇME: 6 setin hepsinde (a) ort.R − taban > 0, (b) tek pozisyonla ort.R − taban > 0, (c) en iyi 5 gün çıkınca taban
farkı toplamı > 0; ve havuzda iki kronolojik yarı > 0. Biri düşerse H1 bu piyasalarda TUTMAZ.

## Diğer semboller için tam mum taraması (ön kayıt, 2026-10-10)
`scan_symbol.py`: mum_kural tur 2 protokolü aynen (20 formasyon × 2 yön × 5 çıkış; her TF'de n≥100, R>0, PF≥1,05,
taban farkı>0; iki yarı; 20 dairesel-kaydırma plasebosu). Semboller: XAUUSD (spread 0,25), USOIL (0,03); TF 15m/30m/1h.
Keşif: < 2026-06-01. Kilitli kasa: 2026-06-01 → 2026-09-03 (Yahoo öncesi), 3 TF'de ort.R > 0.
