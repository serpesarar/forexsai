# Ön-kayıt — USOIL son haftanın 2 SL'sinden türetilen hipotezler (2026-10-20)

Kaynak: `output/islem_otopsi/2026-10-20_2335_usoil/otopsi_405554591.md`, `otopsi_406667349.md`, bot logu
`results/log_sl.txt`. Defter: B10 ENTRY_SCORE (X, NDX+USOIL birlikte, eşik 5–8 negatif), GF-14 T2 (decider bıçak
kapısı bota taşınınca ters — genel bot), B15 seans (C), E21 (backend Yahoo tabanı, basis_gap), B18 (NDX S/R-limit kolu).
Yeni olan: USOIL BUY'a özgü, botun KENDİ `entry_gate.compute_entry_score` bileşenleriyle, tek tek bileşen düzeyinde sınama.

## İki SL'nin ortak noktaları (gözlem)
İkisi de MOMSR BUY, "FALLBACK_MARKET → S/R pullback" yolundan LIMIT emirle girdi; ikisinde de giriş skoru <7 ve ihlaller
arasında `bicak_yakalama` + `ema200_tarafi`; ikisinde de backend SL basis_gap yüzünden reddedildi; #405554591 Pazar
22:09 UTC (haftalık açılışın ilk dakikaları, 15 dk'da −5,8 ATR5), #406667349 gün +%2,4 yükselmişken 12:15 UTC.

## Hipotezler (yön ve eşik sonuçtan ÖNCE; bot tanımları birebir, kapanmış barlar)
- H1 bıçak yakalama: son 30×1m hareket ≤ −1,5×ATR14(1m) (yönle) → SL'ye yatkın.
- H2 1m EMA200'ün yanlış tarafı.
- H3 H1 ∧ H2 (iki SL'nin ortak imzası).
- H4 haftalık açılışın ilk 2 saati (Pazar 22:00–24:00 UTC).
- H5 giriş skoru ≤ 5 (iki SL: 4 ve 5).
- H6 gün içi hareket ≥ +%2 (yönle; #406667349) — "geç kalınmış ralli".

## Popülasyonlar
P1 bot MOMSR USOIL BUY gerçek işlemleri (06-30 → 10-20, iki SL HARİÇ — hipotezin kaynağı), gerçek R.
P2 panel USOIL BUY sinyalleri 02-18 → 10-20 (model başına 30 dk'da bir), sabit TP %1,04 / SL %1,49, sonraki 1m açılış.
P3 botun engellenen USOIL BUY sinyalleri (konum/trend kapısı), aynı simülasyon.

## Ölçü ve geçme
Her H × P: işaretli n, ortR işaretli vs diğer, Δ, gün-blok P(Δ<0), kurtarılan R ve P(>0), rastgele/saat-eşli plasebo,
kronolojik yarılar. **Uygulanabilir düzeltme:** P1'de Δ<0 ve P(kurt>0) ≥ %90, P2'de Δ<0 ve P(Δ<0) ≥ %90 ve iki yarıda <0,
P3'te aynı işaret. 6 hipotez × 3 popülasyon denendi (çoklu test notu). Geçen bile önce GÖLGE (2. KURAL).
