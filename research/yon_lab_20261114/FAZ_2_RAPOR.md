# FAZ 2 — Katalog (Yön Lab, 2026-11-14)

Kod: `src/refs.py` (referanslar), `src/extras.py` (ek durumlar), NOM `backend/services/nom/features.py` (132 özellik).

## A. Referans noktaları — 13 aile, 685 seviye sütunu
| Aile | Üyeler | Sayı |
|---|---|---|
| EMA | EMA 9/21/50/100/200 × M5, M15, H1, H4; D1 EMA 20/50/200 | 23 |
| SMA | SMA 20/50/200 × M15, H1, D1 | 9 |
| BB | Bollinger(20,2) üst/alt × M15, H1, H4 | 6 |
| KC | Keltner(EMA20 ± 2 ATR) × M15, H1 | 4 |
| DON | Donchian(20) tepe/dip × M15, H1, H4, D1 | 8 |
| TWAP | nakit seans, CFD seansı, hafta + ±1σ/±2σ (hacim tanımı beslemeler arası tutarsız → VWAP yerine TWAP) | 15 |
| PIV | fraktal pivot k = 2/3/5/8 × M15, H1, H4; her biri son 48 teyitli pivot | 576 (+ 24 "en yakın" türevi) |
| CAL | önceki gün O/H/L/C, önceki hafta H/L, önceki ay H/L, gece H/L, ORB 15/30/60 H/L, nakit açılış, hafta açılışı | 17 |
| RND | 50/100/250/500/1000 üst/alt | 10 |
| FIB | son H1 (k=5) salınımı: %38,2/50/61,8 geri çekilme, %127,2/161,8 uzatma | 5 |
| ICHI | tenkan, kijun, senkou A/B (26 kaydırmalı) × H1, H4 | 8 |
| TRD | Parabolic SAR H1, SuperTrend(10,3) M15/H1 | 3 |
| CLU | ≥2 ailenin en yakın seviyesi ±0,3 ATR içinde → bölge | türetilmiş |
Hacim profili (POC/VAH/VAL, HVN/LVN): **yok** — Dukascopy 2024+ parquet'te hacim alanı yok, MT5 tick hacmi farklı tanım
(NOM Faz 0). Opsiyon strike/gamma flip: ücretsiz güvenilir kaynak yok; toplam GEX günlük katmanda (L1). Order block/FVG/BOS/CHoCH:
defterde SM-01…05 ile X (yeniden açma gerekçesi yok).

## B. Durumlar — 750 tekli koşul (Faz 4D)
- NOM 132 özelliği × KEŞİF beşte birlik kovaları (sürekli olanlar) veya değerleri (ayrık olanlar).
- 114 ek ikili durum (M15/H1/D1): EMA 9/21 kesişimi (son 3 bar), 50/200 altın/ölüm kesişimi (son 10 bar), 8>21>50>200 dizilim,
  fiyat ↔ EMA21/50/200, çekiç, ters çekiç, yutan ↑/↓, doji, iç/dış bar, 3 asker/karga, sabah/akşam yıldızı, NR4/NR7, Aroon > 70,
  CCI ±100, Williams %R ±80, StochRSI uçları, Vortex, TRIX işareti, Ultimate Osc ±70/30, BB-Keltner sıkışması; opsiyon vade haftası,
  çeyrek sonu haftası, tatil öncesi; GEX<0, DIX z ±1, GEX z<−1 (günlük, ertesi gün kullanılabilir).
- 26 referans yakınlığı: "en yakın X ailesi seviyesi ≤ 0,25 ATR üstte/altta".
MFI/OBV/A-D/CMF (hacim tabanlı): hacim tutarsızlığı nedeniyle yok.

## C. Kombinasyonlar
İkili: her etikette KEŞİF |t| en yüksek 40 tekliden 780 çift; üçlü: en iyi 10 ikili × en iyi 20 tekli. Toplam kombinasyon hücresi 3.413.

## Sızıntı
Hepsi yalnız kapanmış barlarla; HTF `end ≤ t`; pivot k bar sonra teyit; hafta/ay dönemi sonu takvimden (veriden değil); Ichimoku
bulutu 26 bar kaydırılmış. Kesme testi (t'de kesilmiş veri = tam veri): referanslarda ve ek durumlarda **0 uyuşmazlık**
(`tests/test_yonlab_leak.py`).
