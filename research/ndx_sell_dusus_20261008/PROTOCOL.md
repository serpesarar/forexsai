# Ön-kayıt — NDX SELL mantığı düşüş dönemlerinde (10 yıl) (2026-10-08)

Soru: piyasa satışa dönerse botun NDX SELL tarafı kazanır mı? Botun SELL kapsamları panel oylarına dayanır
(VIXREG, MOMSR) → birebir yeniden üretilemez (E22). Bar verisinden kurulabilen MANTIKLARI test edilir.

## Veri
`research/ndx_gate_forge/data/long_30m_utc` (2021-06 → 2026-07, ANA), `long_1h_utc` (2016-05 → 2021-06,
ikincil — 1h'de aynı-bar belirsizliği yüksek), `macro_daily_patched.csv` VIX (ÖNCEKİ gün kapanışı).

## Ortak icra
Karar: ABD seansında (14:00–19:30 UTC) bar KAPANIŞI; giriş = SONRAKİ bar açılışı (E7) − yarım spread;
geometri botun 80/110 puanının fiyata oranı: TP %0,258, SL %0,355 (RR 0,73, başabaş %57,9);
ek geometri TP×2 (%0,516). Aynı barda SL ve TP → SL. En çok 3 gün; çözülmezse son kapanış. Strateji başına
aynı anda tek pozisyon.

## Stratejiler (SELL)
- S0 taban: her karar anında SELL.
- S1 VIXREG mantığı: önceki gün VIX < 18,4 ise SELL. (+ S1b: VIX ≥ 18,4 iken VIXREG'in yaptığı BUY.)
- S2 momentum SELL: kapanış < EMA50 ve EMA20 < EMA50 ve son 2 bar getirisi < 0.
- S3 kanal dönüşü SELL (CHREV benzeri): kapanış ≥ Bollinger(20,2) üst bandı.

## Rejim (betimsel — geçmişe bakarak etiketlenir, kural DEĞİL)
- Ay: NDX ay getirisi ≤ −%3 DÜŞÜŞ, ≥ +%3 YÜKSELİŞ, arası YATAY.
- Ayı: 252 günlük tepeden ≥ %15 aşağıda geçen günler.
Metrik: işlem başına R, bootstrap %95, P(>0); rejim × strateji; yıl yıl.
