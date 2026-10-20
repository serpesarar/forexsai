# Ön-kayıt — XAU "Golden Donchian" günlük swing, bağımsız dönem (2008-01 → 2021-04) — XS-01

2026-10-20, sonuç görülmeden. Orijinal bulgu (2026-06-16, `xau_swing_research/`) 2021-05→2026-04 broker D1 verisinden;
kural parametreleri o veriden seçildi. Bu test kuralı DEĞİŞTİRMEDEN, hiç görmediği Dukascopy 2008-01→2021-04 döneminde sınar.
Amaç: bota gölge olarak bağlamadan önce "çalışıyor mu" kanıtı.

- Veri: `research/decider_xau_tpsl_20261015/mekanik/data/duka_h1.parquet` (H1); D1 = NY 17:00 sınırlı.
- Kural: D1 kapanış ≥ önceki 55 günün en yükseği ∧ kapanış > EMA200(D1) → ertesi D1 açılışında BUY; SL = −2×ATR14,
  TP = +4×ATR14 (H1 içinde, aynı barda önce SL), 20 gün (480 H1 bar) zaman stopu; tek pozisyon; sürtünme $0,40.
- Taban: aynı geometriyle HER gün BUY (sürüklenme tabanı), tek-pozisyon değil ortalama R.
- Geçme: ortR > 0, bootstrap P(EV>0) ≥ 0,90, ortR > taban ortR, iki yarıda (2008-14 / 2015-21-04) ortR > 0.
