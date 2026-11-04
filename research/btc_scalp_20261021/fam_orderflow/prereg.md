# Ön kayıt — BTC scalp ailesi: EMİR AKIŞI (fam_orderflow)

Tarih: 2026-10-22 (sonuçlar hesaplanmadan ÖNCE yazıldı). Bu dosya bir daha düzenlenmez; değişiklikler yalnız
sonuna "Ek A…" olarak, gerekçesiyle eklenir.

Girdiler: `research_notes/BTC scalping strateji araştırması/01…03`, `docs/KAPI_KAYIT_DEFTERI.md` §0/§1 (E1–E50)/§2.11/§3.
Defterde BTC için emir-akışı (taker dengesizliği, CVD, hacim patlaması, spot–perp akış ayrışması, büyük işlem) sınaması
YOK (BTC-S/T/M/X hepsi OHLCV + makro). En yakın: GF-14 T3 (NDX 5m hacim patlaması ≥1,5; başka varlık, yönsüz),
BTC-S05/S06 (1 s fiyat şoku fade — akış verisi yok), HEKA §2.10 "CVD sınanamaz (emir akışı verisi yok)". Yeni veri
(Binance perp+spot taker hacmi, aggTrades 1 s) = yeniden açma gerekçesi.

## 1. Veri ve nedensellik
- Fiyat yolu (giriş/çıkış): Binance **spot** BTCUSDT 1m OHLC (`btc_scalp_1m.parquet` `spot_*`; CFD spot'u izler; not 03 ile aynı).
- Akış özellikleri: perp `perp_taker_buy_base`, `perp_volume`, `perp_trades`, `perp_open/close`; spot `spot_taker_buy_base`, `spot_volume`.
  delta = 2·taker_buy − volume (BTC).
- Satır ts değeri ts+60 s'de bilinir; karar dakikası t, giriş barı e=t+1, fiyat open[e].
- Dışlama: 2023-03-24 11:28–14:00 UTC; spot'ta ≥5 dk eksik bloklar (lib.load_grid); özellik penceresinde `perp_zero_vol=1`
  veya `spot_missing=1` olan dakika varsa sinyal üretilmez; izleme penceresi [e, e+60) dışlanmış dakika içeriyorsa giriş yok.
- Bütün z-skorlarının ortalama/std'si yalnız geçmişten: 30 günlük (43.200 dk) kayan pencere, `shift(1)`, min 10 gün.
  OF07 (1 s) için 7 günlük pencere (veri 6 ay).
- Önek (sızıntı) testi: t'den sonraki tüm veriyi bozunca t'deki özellikler değişmemeli — kodda zorunlu kontrol.

## 2. Bölmeler
DISCOVERY 2021-06-01→2023-12-31 · OOS 2024-01-11→2025-06-30 · BLIND 2025-07-01→2026-10-20. POST = OOS∪BLIND.
Bölme, GİRİŞ dakikasına göre. Parametre/geometri seçimi YALNIZ DISCOVERY'de.

## 3. Geometri (not 03 kuralları)
- ATR5m = lib.atr_5m (son 14 tamamlanmış 5m bar, girişten önce kapanmış). SL kuralları:
  **S1** SL = max(19 bp, 1,1×ATR5m) · **S2** SL = max(28 bp, 2,0×ATR5m).
- TP/SL oranı ρ ∈ {1, 1,5, 2}; zaman stopu H ∈ {15, 30, 60} dk. → 2×3×3 = **18 geometri**.
- Ölçüm: aynı barda TP+SL → SL (ana); ayrıca iyimser (→TP) ve OHLC-sezgisel (açılış hangi uca yakınsa) raporlanır.
- SL dolumu boşluk-duyarlı min(SL, open[hit]) **− kayma**: 1 bp; vuruş dakikasının spot |1m getirisi| DISCOVERY'nin
  %99 yüzdeliğinin üstündeyse 5 bp. TP limit, seviyeden. Zaman çıkışı bar e+H′−1 kapanışı.
- Rollover: RO = 17:00 America/New_York (yaz 21:00 / kış 22:00 UTC). Zorunlu kapanış RO−2 dk (20:58/21:58) açılışı
  (= RO−3 dakikasının kapanışı): H′ = min(H, (RO−2)−e). H′ < 5 ise giriş yok. [RO−2, RO+3) içinde giriş yok. Swap yok.
- Stratejinin kendi aynı-bar oranı < %0,5 olmalı (değilse hücre geçersiz).

## 4. Maliyet
Gidiş-dönüş, fiyatın bp'si: **PEP 1,85** (ana) · PEP stres 2,78 · sabit 15 $ (15/fiyat) · Binance maker 4 · taker 10.
R = net getiri bp / SL bp. Her tabloda R ve bp birlikte (E50).

## 5. Hipotezler (sinyal hücreleri), a priori birincil mod (E49)
Her tanım simetrik (BUY ve SELL olayları), havuzlanmış değerlendirilir, yönler ayrıca raporlanır. Epizod bastırma:
aynı hücre × yön için olaydan sonra 30 dk yeni olay yok (E6). Olay "yönü" = akışın işareti; mod onu işleme çevirir.

- **OF01 Taker dengesizliği uç (perp)**: D_W = son W dakikanın perp delta toplamı; z_D(W) (30g). |z_D| ≥ θ.
  W ∈ {1, 5, 15}, θ ∈ {3, 5}. Birincil mod **TERS** (likidite sağlama primi; Makarov–Schoar negatif akış–getiri,
  çeyrek-saat makalesinde ilk yarım saat negatif profil). İkincil DEVAM (raporlanır, seçime girmez).
- **OF02 Emilim (absorption)**: |z_D(W)| ≥ θ **ve** |z_r(W)| ≤ 0,5, z_r(W) = W dakikalık spot log getirisinin 30g z'si.
  W ∈ {1, 5, 15}, θ ∈ {3, 5}. Birincil **akışın TERSİ** (H2). İkincil akış yönü.
- **OF03 Spot–perp akış ayrışması**: Δ = z_Dspot(W) − z_Dperp(W); |Δ| ≥ k → yön sign(Δ). W ∈ {5, 15}, k ∈ {3, 4}.
  Birincil **SPOT'u izle** (kaldıraçsız talep; perp-önderli hareketler söner). İkincil perp'i izle (= sign(Δ) tersi).
- **OF04a CVD–fiyat ayrışması (fiyat yeni uç, CVD teyit etmiyor)**: perp kapanış ≥ önceki N kapanışın max'ı ve
  CVD_t < max(CVD[t−N..t−1]) − g·σ_N (σ_N = önceki 1440 dk 1m delta std × √N); ayna: dip. N ∈ {30, 60}, g ∈ {0, 0,5}.
  Birincil **TERS** (ayrışma → dönüş; pratisyen iddiası). İkincil fiyat yönü.
- **OF04b CVD yeni uç, fiyat teyit etmiyor**: CVD_t ≥ önceki N max **ve** perp kapanış ≤ önceki N kapanış max'ı − g·σp_N
  (σp_N = önceki 1440 dk 1m log getiri std × √N × fiyat); ayna. N ∈ {30, 60}, g ∈ {0,5, 1}. Birincil **CVD yönünü izle**.
  İkincil ters.
- **OF05 Hacim / işlem-sayısı patlaması**: x ∈ {log perp hacmi, log perp işlem sayısı}, pencere W ∈ {1, 5} dk toplamı,
  z_x ≥ θ, θ ∈ {3, 5}; yön = sign(perp close_t − perp open_{t−W+1}) (0 ise olay yok). Birincil **DEVAM** ("coşku dönmez";
  bilgili akış). İkincil TERS.
- **OF06 Çeyrek-saat kalibrasyonu** (arXiv 2607.09426): ts dakikası ∈ {00,15,30,45} olan bar (çeyreğin ilk dakikası),
  yön = sign(perp delta), |z_D(1)| ≥ θ, θ ∈ {0, 2}. Birincil **TERS** (makale: ilk yarım saat negatif). Kalibrasyon:
  beklenti maliyet sonrası ≤ 0; geçerse şüphe (sızıntı denetimi).
- **OF07 Keşif — 1 s / büyük işlem (yalnız 2026-04-20→10-20, BLIND içinde; karta ulaşamaz, ayrı rapor)**:
  (a) büyük-işlem net = agg_large_buy − agg_large_sell (≥5 BTC aggTrade), z(7g) ≥ 3, yön işareti;
  (b) 1 s patlama net = agg_max_1s_buy_qty − agg_max_1s_sell_qty, z(7g) ≥ 3;
  (c) eşleştirme kontrolü: aynı dönemde OF01 W=1 θ=3 (1m delta).
  Sabit geometri S1, ρ=1, H=30; iki mod da raporlanır; seçim yok; DISCOVERY yok.

DISCOVERY hücre ailesi: OF01 12 + OF02 12 + OF03 8 + OF04a 8 + OF04b 8 + OF05 16 + OF06 4 = **68 sinyal hücresi
(iki mod dahil) × 18 geometri = 1.224 hücre**.

## 6. Değerlendirme
- **Plasebo:** aynı geometri, aynı yön, aynı (yıl, UTC saati) kovasından rastgele geçerli giriş dakikası; ≥200 çekiliş;
  stratejinin ort. net R'sinin plasebo dağılımındaki yüzdeliği. Analitik karşılık: fazlalık
  x_i = R_i − μ(yön, yıl, saat, geometri) (μ = kovadaki tüm geçerli dakikaların ort. net R'si).
- **z** = ort(x)/SE, SE gün-kümeli (giriş UTC günü). Bootstrap = gün-blok, 2.000 tekrar.
- **Seçim (her hipotez için tek hücre):** yalnız birincil mod hücreleri; DISCOVERY'de n ≥ 100 (epizod bastırmalı)
  ve aynı-bar < %0,5 olanlar arasında en büyük DISCOVERY z (PEP net, kötümser). Eşitlikte küçük θ/W.
- **Seçim düzeltmesi:** (i) max-z: DISCOVERY'deki 1.224 hücrenin max z'si, olay dizisinin tam-gün katlı dairesel
  kaydırmalarıyla (200 kaydırma, DISCOVERY içinde sarmalı; saat korunur, E48) kurulan boş dağılıma karşı → p_sel;
  (ii) Holm: seçilen 7 hücrenin POST tek-yönlü p'leri (z_POST'tan) üzerinde, α=0,05.
- **Kart (POST, seçilen hücre):** 1 n ≥ 150 · 2 ort. R > 0 ve gün-blok P(EV>0) ≥ %90 · 3 POST'un iki kronolojik
  yarısı ≥ 0 · 4 spread ×1,5 (2,78 bp) ile > 0 · 5 |iyimser − gerçekçi| ≤ 0,5·|ort. R| (iyimser = maliyet/kayma yok,
  aynı-bar → TP; Binance'te open[e]≈close[t]) · 6 tek-pozisyon zinciriyle > 0.
  **Ek:** plasebo yüzdeliği ≥ 95 · BLIND ort. R > 0 · brüt fazlalık (plaseboya göre) ≥ 0,15R **veya** brüt ort. ≥ 2×maliyet
  (3,7 bp) · Holm p < 0,05 · max-z p_sel ≤ 0,10 · aynı-bar < %0,5.
- **Verdikt şeması (tüm kombinasyonlar):** LIVE = 6/6 kart + tüm Ek ölçütler. SHADOW = kart ≥ 4/6 ve POST ort. R > 0 ve
  plasebo ≥ 90 ve BLIND > 0 (Ek'lerin bir kısmı düşse de). Diğer her durum RED. (Bu ailede LIVE beklenmiyor; not 03:
  rastgele brüt ≈ 0, gereken brüt ≥ 0,15R.)
- Raporlanan her hücre: n, WR, ort. R, bp, %95 GA, P(EV>0), yarılar, stres, icra farkı, tek-poz, plasebo yüzdeliği,
  BLIND, yıl-yıl işaretler, işlem/gün; ayrıca maker 4 / taker 10 bp ve sabit 15 $ varyantları.
- Tüm 1.224 hücrenin DISCOVERY/OOS/BLIND sonuçları `results/all_cells.csv`'ye yazılır.

## 7. Ön beklenti
Literatür (not 01): 1 dk dengesizliğin öngörüsü "çok zayıf", akış–fiyat ilişkisi çoğunlukla eşzamanlı; kenar sub-bp.
Not 03: brüt kenar ≥ 0,15R gerekir; projede dürüst kısa-vade kenarları 0,03–0,1R. Beklenti: **hiçbir hücre LIVE değil**.

---
## Ek A1 (2026-10-22, olay sayımı sonrası, getiri HESAPLANMADAN önce)
`01_build.py`: önek testi OK (cut sonrası fiyat/hacim bozuldu, önceki 3.000 dk özellikleri birebir). Geçerli giriş dakikası
2.815.426. Olay sayıları `results/event_counts.csv`. DISCOVERY'de n < 100 olan (seçime girmez, ön kayıt kuralı):
OF02_W5_th5 (54), OF02_W15_th5 (22), OF05_v_W1_th5 (13), OF05_v_W5_th5 (8), OF05_t_W5_th5 (37). OF05 θ=5 hücreleri
POST'ta neredeyse boş (log-hacim z≥5 2024+ rejiminde ~0) → kart hacmine yapısal olarak ulaşamaz. Izgara değiştirilmedi.
Ek uygulama notu: max-z boş dağılımı hem ön-kayıtlı tanımla (1.224 hücrenin tamamı) hem de n_DISC ≥ 30 hücrelerle
raporlanır (küçük n'li hücrelerin aşırı z'si boşu şişirir → ilki daha tutucu); karar ön-kayıtlı (tamamı) olanla verilir.

## Ek A2 (2026-10-22, SONUÇLARDAN SONRA — post-hoc, kanıt değeri düşük)
Ön-kayıtlı 7 seçimin hepsi RED. POST tablosunun taranmasıyla (yani POST'a bakılarak — seçim yükü tam) şu post-hoc
incelemeler eklendi; hiçbiri ön-kayıtlı verdikti değiştirmez, yalnız "yakın aday / sonraki ön kayıt" önerisi üretir:
(1) OF02 emilim-fade eşik platosu: W ∈ {1,5,15} × θ ∈ {3,4,5,6} × |z_r| ≤ {0,5}, geometri S1_r1_H15 ve S2_r2_H60,
yıl-yıl, gün yoğunlaşması (en iyi 5 gün payı), yön dağılımı; (2) OF06 çeyrek-saat etkisinin özgüllüğü: aynı kural
çeyrek-dışı dakikalarda {07,22,37,52} (kontrol), brüt bp yıl-yıl; (3) E49: DISCOVERY'nin ikincil-mod liderlerinin POST'u.
