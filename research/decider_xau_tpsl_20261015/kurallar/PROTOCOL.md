# ÖN-KAYIT — Decider XAUUSD giriş kuralları × TP/SL geometrisi (DX-02)

**Dondurulma zamanı: 2026-10-15 04:41 UTC** (sonuç hesaplanmadan önce). Bu dosyadan sonra yazılan her şey
"keşif" olarak işaretlenir. Bu ana kadar yalnız ÖZELLİK dağılımlarına bakıldı (`results/01_feature_marginals.txt`
— kural eşiklerinin yeterli n verip vermediğini görmek için); hiçbir kural için sonuç (R, WR, $) hesaplanmadı.
Önceki DX-01 çalışması (aynı veri, aynı kişi-oturumu ailesi) tüm-örneklem geometri sonuçlarını biliyor —
G2 geometrisi o çalışmada **sonuçlara bakılarak** seçildi (post-hoc), bu yüzden G2 satırları ek çoklu-sınama
yükü taşır (aşağıda).

## Veri
- Karar kümesi: DX-01 analiz kümesi (`../data/grid_set.pkl`): kullanılabilir + yinelenmemiş + 240 dk veri boşluksuz
  OPEN kararları. BUY n=595 (35 gün), SELL n=81 (12 gün). 2026-06-30 → 2026-10-14.
- Barlar: broker 1m BID, UTC (`../data/xau_1m_utc.csv.gz`).
- Karar anı T = journal `ts`. Giriş = T'den sonraki ilk 1m açılışı + journal'da ölçülen spread (yoksa 0,14$) —
  **icra edilmiş 68 işlem dahil herkes için aynı taban** (kontrol popülasyonlarıyla kıyaslanabilirlik için;
  gerçek dolum tabanı DX-01'de raporlandı).
- Çıkış: `core.sim_grid` (aynı bar TP+SL = LOSS, 48 s ufuk). ATR = T anında kapanmış 5m barlardan basit ATR14.

## Özellikler (yalnız t_end ≤ T barlar veya karar-öncesi journal anlık görüntüsü)
- `trig_sign`: journal `multi_tf.5m` channel_z ve vwap_z'den mutlak değeri büyük olanın işareti
  (+ = fiyat kanal/VWAP'ın ÜSTÜNDE aşırı = güç/kırılım; − = altında = dip).
- `eq_block_buy/sell`: decider'ın kendi `entry_quality.assess` (D2: chz_dir ≥ 2,0 veya 5m vol_ratio ≥ 1,5).
- `h1_above_ema50`: son kapalı 1h kapanışı > EMA50(1h kapanışları).
- `d1_up`: son kapalı günlük (21:00 UTC sınırlı) kapanış > son 10 günlük kapanışın SMA'sı.
- `sess_ldn_ny`: T saat(UTC) ∈ [07, 16].
- `atr5_ratio`: ATR14(5m) / son 288 kapalı 5m barın ATR14 medyanı.
- `dist_hi20_h1_atr`: (son 20 kapalı 1h barın en yükseği − son kapalı 1m kapanış) / ATR14(1h). SELL aynası `dist_lo20`.
- `size_factor`: decider'ın kendi OPEN boyutu.

## Aday kurallar (≤8; her biri bir mekanizmaya bağlı) — BUY tanımı / SELL aynası
| ID | BUY kuralı (tut) | SELL aynası (tut) | Mekanizma (kanıt) |
|---|---|---|---|
| R1 | `trig_sign > 0` (yukarı aşırılıkta al = güç) | `trig_sign < 0` | XAU kenarı gücü almak, zayıflığı değil (günlük swing "Oversold-DIP REJECTED", MK-04 yeni-tepe BUY; evidence tablosu XAU BUY kapı WR 70 < taban 78) |
| R2 | D2 engellemiyor (`eq_block_buy == False`) | `eq_block_sell == False` | bıçak yakalama + hacim patlaması (D2, 09-14 denetimi; 09-14 sonrası veri D2 için örneklem-dışı) |
| R3 | `h1_above_ema50` | `not h1_above_ema50` | yavaş trend devamı (XAU tek sağlam kanıt: trend/kırılım BUY + sürüklenme) |
| R4 | `d1_up` | `not d1_up` | günlük rejim (§3 ders 1: kenar günlük rejimde) |
| R5 | `sess_ldn_ny` | `sess_ldn_ny` | likidite/akış seansları trend taşır; Asya aralık (K5 C sınıfı saat bloğu; saat takvimleri genelde taşınmaz — zayıf önsel) |
| R6 | `atr5_ratio < 1,5` (oynaklık patlaması yok) | aynı | haber/şok anında 5m aşırılık bıçaktır (D2'nin hacim kolu, aralık-tabanlı) |
| R7 | `dist_hi20_h1_atr ≤ 1,0` (20 saatlik tepeye yakın) | `dist_lo20_h1_atr ≤ 1,0` | güç/yeni tepe (MK-04 B−) |
| R8 | `size_factor ≥ 0,20` (lot ≥ 0,02 — decider boyutu büyüttü) | aynı | decider'ın kendi konviksiyonu bilgi taşıyor mu (seçim alfası) |

Eşikler yukarıdaki gibi DONDURULDU (R2/R6'daki 1,5 ve 2,0 mevcut D2 eşikleri; R7'deki 1,0 ATR ve R8'deki 0,20
yuvarlak değer/lot kademesi). Tamamlayıcı kümeler (ör. R1'in dip BUY'ları) yalnız KARŞITLIK olarak raporlanır,
verdikt almaz. Kural birleşimleri (R1∧R3 vb.) yalnız keşif olarak raporlanabilir, verdikt almaz.

## Geometriler (yalnız bu üçü — ızgara yok)
G1 TP1,0/SL1,5×ATR5 (mevcut) · G2 TP1,25/SL0,75 (DX-01 adayı, post-hoc) · G3 TP3,0/SL1,5 + 120 dk zaman çıkışı.
R = pnl / SL mesafesi; spread girişte.

## Kontroller
- **C1 rastgele alt küme:** aynı yönün decider kümesinden kural alt kümesiyle aynı büyüklükte rastgele alt küme
  (4.000 tekrar) → kural EV yüzdeliği. Aile-bazlı (seçim düzeltmeli) sürüm: sonuç satırları karıştırılır (maskeler
  sabit), 24 test (8 kural × 3 geometri) için standart z'nin maksimumu → p_FW.
- **C2 rastgele zaman:** her kural işlemi için aynı UTC dakikası, ±10 takvim günü içinden rastgele geçerli gün
  (girişe ≤2 dk mesafede bar, 240 dk boşluksuz), aynı spread, kapalı-bar ATR; 300 set → kural EV yüzdeliği.
- **C3 tetik popülasyonu (bağımsız kontrol):** free moddaki tüm danışmalar (extremity ≥ 1,6; OPEN olmayanlar =
  gerçek + sahte WAIT; ≤10 sn yinelenen kayıt atılır) BUY olarak simüle edilir. Kuralın etkisi
  (kural − kural-dışı) OPEN olmayan danışmalarda AYNI İŞARETLİ mi → mekanizma piyasaya mı ait.
- Gecikme: giriş +1 bar (1 dk). Spread ×1,5 ve tek-pozisyon yalnız bilgi.

## Geçme ölçütleri (kural × geometri × yön başına)
1. EV_R > 0 (spread sonrası)
2. gün-blok bootstrap P(EV>0) ≥ 0,90 (B=4.000)
3. kural alt kümesinin kronolojik iki yarısı (medyan karar zamanında bölünür) ≥ 0
4. C1 yüzdeliği ≥ %90 **ve** C2 yüzdeliği ≥ %90
5. +1 dk gecikmede EV > 0 ve kayıp ≤ EV'nin yarısı
6. aile-bazlı seçim düzeltmesi: p_FW < 0,10 (24 test/yön; G2 post-hoc olduğu için ayrıca Bonferroni z* raporlanır)
7. C3 OPEN-olmayanlarda aynı işaretli etki (yalnız A için)
- n < 60 veya < 10 gün → **RED (güçsüz)**.

**Verdikt:** A = 1–7 hepsi · B = 1–5 geçer, 6 veya 7 düşer · C = 1 ve 3 geçer, 2/4/5'ten biri düşer ·
RED = EV ≤ 0 veya bir yarı < 0 veya güçsüz.

## Seçim alfası (Soru 5) — ön-kayıtlı analizler
(i) Spearman(size_factor, R) her geometride, gün-blok bootstrap CI; (ii) lot kademesine göre EV (0,01/0,02/0,03);
(iii) OPEN BUY vs C3 OPEN-olmayan danışmalar (BUY simüle), aynı günlerde; (iv) gerçek WAIT vs sahte WAIT (CLI
hatası — model seçimi yok) karşı-olguları.
