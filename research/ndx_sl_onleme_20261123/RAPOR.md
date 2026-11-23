# NDX DAYCOMBO + REENTRY — 2026-11-23 SL'leri ve SL önleme araştırması (SL-01…08)

**Hüküm:** Giriş/bekleme/atlama kuralı yok — SL'lerin %60'ını engelleyen her kural TP'lerin de aynı oranını kesiyor (41 adayda
korelasyon **0,996**; IO-26/TD-01'in 2018–2023'te teyidi). **Ama braket geliştirilebilir (§7, EK-4):** oynak piyasada SL = max(110,
2,5×ATR5), TP = SL×80/110, lot = 30×110/SL (eşit $ risk). Canlıya gerçekçi tabanda (lag 1) ön kayıtlı 1. ölçüt ✓, kart **6/6**,
braket plasebosu p = 0,000; **bugünkü canlı 4 SL'nin 3'ü (%75) stopsuz kalırdı, 6 TP'nin 5'i korunurdu.** Zayıf yan: 2021 ve 2025
eksi (kullanıcının son-4-yıl ölçütü ✗) → sınıf **B**. Bota bağlandı (`yeni deneme/vol_bracket.py`, kapatılabilir).

## 1. Bugün ne oldu (vaka, kanıt değil)
| UTC | aile | giriş | sonuç | sinyalden kaçış | gürültü oranı* |
|---|---|---|---|---|---|
| 14:06 | DC | 26.725,4 | TP | +132 p | 0,24 |
| 14:22 | RE | 26.814,2 | TP | | 0,34 |
| 14:55 | DC | 26.625,8 | TP | +53 p | 0,22 |
| 15:05 | RE | 26.733,1 | TP | | 0,28 |
| **15:21** | **DC** | **26.947,8** | **SL** | **+170 p** | 0,32 |
| **15:47** | **RE** | 26.827,5 | **SL** (SL'den 1 dk sonra) | | 0,38 |
| **17:06** | **DC** | 26.770,9 | **SL** | −18 p | 0,54 |
| 17:47 | RE | 26.657,5 | TP | | 0,66 |
| 18:01 | DC | 26.766,9 | TP | −2 p | 0,68 |
| **18:31** | **RE** | 26.801,9 | **SL** | | 0,78 |

\*SL / (ATR14(1m)·√30): 110 puanlık stopun 30 dk'lık beklenen hareketin kaçta kaçı olduğu. Y25'te medyan ≈ 1,1; bugün 0,22–0,78.

- 13:45–14:00 UTC'de **+750 p (+%2,9)** şok (15m gövdesi 20 günlük medyanın 28,7 katı); sonra 26.400–27.050 arası yönsüz ±300 p.
- 1m mumların aralığı 100–150 p'ye çıktı; 80/110 braketi 3–25 dk'da çözüldü → sonuç yazı-tura. 6 TP / 4 SL = %60 isabet,
  başabaş %57,9. 30 lotta +14.325 − 13.242 = **+1.083 $**: gün kârda kapandı, ama kâr başabaşa yakın.
- Canlıda probasyon bandı 274 / 276 / 180 p (SL 110 p'den geniş) → probasyon bu oynaklıkta süzme yapmıyor; 15:21 girişi sinyalin
  +171 p üstünden geldi.

## 2. Ne sınandı (ön kayıt, 9 aile, 41 aday)
Motor TD-01 canlı akış taklidi (DAYCOMBO sinyali, probasyon, REENTRY TP+5 / SL+1 dk, spread). **Yeni veri:** Dukascopy 1m
2018–2023 (bu kurallarda ilk kez; yüzde geometri), 2024, 2025–26, 2026-07-29 → 11-20 broker + kutu MT5.
Taban: ESKİ-A +0,053R (1.228) · ESKİ-B +0,026R (1.309) · 2024 +0,031R · Y25 −0,004R · Y26b +0,116R.

| aile | fikir | sonuç |
|---|---|---|
| A | gün kâr kilidi (+2/+3/+4R'de dur) | bugünü kurtarırdı; +2R 9 yılın **9'unda eksi** (−64R) |
| B | gün içi N. SL'den sonra dur | 2020 −31R, 2023 −9R; işaret yıldan yıla dönüyor |
| C | geri verme freni (tepeden −1,5/2/3R) | 9 yılın 6–7'sinde eksi |
| D | buy-stop teyidi (+x·ATR5, w dk) | lag 0'da plato ve S4 ✓, **lag 1 (canlı) tabanında S4 ✗** (§3) |
| E | probasyon 10/15 bar, kayıpsız bitiş, bant tavanı | E10 1. ölçütü geçti; kazanç gecikme etkisi (§3) |
| F | SL sonrası REENTRY yalnız geri alınca | 2018–20 ve 2025 eksi |
| G | çalkantı (verimlilik oranı ER60/120) | 2018–20 ve 2023 eksi |
| H | şok sonrası 3 saat bekle | **X:** şok sonrası işlemler geçmişte kârlı (−40…−74R) |
| I | gürültü/braket oranı düşükse atla | 2025 eksi, P ≤ 0,85 |
| R | TD-01'in yakın kalanları (G8 kaçış, PV limit, G7) | G8≥50 1. ölçütü geçti ama atladığı 111 işlem +0,011R → zincir kayması (E89) |

## 3. Tek gerçek bulgu: ilk dakikada girmek en kötü an — ama canlı bunu zaten almıyor
Filtresiz ek gecikme taraması (yıl başına Σ R, 2018-01 → 2026-11-20):

| ek gecikme (dk) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 15 | 20 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Σ R | 119,8 | 149,5 | 154,5 | 142,5 | 183,4 | 212,4 | 163,5 | 139,1 | 139,5 | 134,5 | 131,7 | 122,0 |

Probasyon biter bitmez (lag 0) girmek 13 gecikmenin en kötüsü. Güçlü yeşil 5m mum + probasyon sonrası fiyat çoğu zaman kısa bir
geri çekilme yapıyor. **Canlı bot zaten ≈1 dk geç giriyor** (log 14:06:12 vs replay 14:05). Lag 1 tabanına karşı:
- E probasyon 10 bar: ΔΣ +13,1R, 9 yılın 4'ü artı, 2023 −9,3 / 2024 −7,1 → S4 ✗.
- D buy-stop +0,5 ATR5 / 30 dk: ΔΣ +11,1R, 4/9 yıl, 2024 −3,1 / 2026 −11,2 → S4 ✗ (spread ×1,5'te +19,6R, 6/9, yine ✗).
- 4–6 dk ek bekleme (lag 5'in tepesi 212R) komşularıyla tutarsız (lag 4 2023'te, lag 6 2025'te lag 1'in altında) → gürültülü tepe.

## 4. Kullanıcının ölçüsü — "SL'lerin %60'ı engellenebilir miydi?"
Havuz (2018 → 2026-11-20), her aday için engellenen SL % ve kaybedilen TP % (`results/sinir_egrisi.csv`):

| aday | SL engel | TP kayıp | Δ Σ R |
|---|---|---|---|
| şok ≥3× | %86 | %84 | −74 |
| şok ≥4× | %73 | %71 | −52 |
| buy-stop +1 ATR5 / 15 dk | %66 | %63 | −34 |
| buy-stop +1 ATR5 / 30 dk | %57 | %54 | −20 |
| buy-stop +0,5 ATR5 / 30 dk | %37 | %30 | +57 (lag 0) / +11 (lag 1) |
| probasyon 10 bar | %10 | %4 | +77 (lag 0) / +13 (lag 1) |

41 adayda SL-engel ile TP-kayıp korelasyonu **0,996**, ortalama fark 2 puan. Bugün 23 aday SL'lerin ≥%60'ını engellerdi; 9 yılda
≥%60'a ulaşan 3 aday TP'lerin %63–84'ünü de kesiyor. **SL'lerin %60'ını engellemek = TP'lerin %60'ını engellemek.** Bu stratejide SL
girişin değil, braketin (80/110) gürültü içindeki doğal sonucu.

## 5. Ne yapılabilir (dürüst seçenekler)
1. **Giriş kuralı değiştirmemek** — hiçbir aday kanıt çıtasını geçmedi; canlıya bağlanacak kural yok (2. KURAL).
2. **Kaldıraç = lot.** 30 lotta 1R ≈ 3.300 $; 9 yılın gün dağılımında %20,5 gün ≥3 SL (ort. −1,19R), en kötü %1 gün −4R
   (≈ −13.200 $). Bu günler stratejinin normal dağılımı, istisna değil. Lot küçültmenin beklenen $ bedeli MA-05'te sıfırdan ayırt
   edilemedi (B) — kayıp günleri küçültür, kazançları da aynı oranda.
3. **İzlenecek (gölge değil, not):** D buy-stop +0,5 ATR5 / 30 dk işlem başı R'yi yükseltiyor (+0,068 vs +0,043, lag 1) ve SL'yi
   %34 azaltıyor (TP %30); ama toplamda yıllar arası tutarsız → C. Yeni kanıt için 2026-11-24 sonrası canlı akışta ileri sınama.

## 7. Geliştirme: oynaklığa göre braket + eşit $ risk (EK-4, `src/s6_vol_braket.py`, `src/s7_kart.py`)
SL'yi engellemek yerine, oynak günde braket gürültünün dışına taşınır ve lot küçülerek $ riski sabit tutulur. Sakin piyasada
(2,5×ATR5 ≤ 110) davranış birebir eskisi.

| aday (lag 1 tabanı, Σ R 149,5) | Δ Σ R | 1. ölçüt | P (gün blok) | spread ×1,5 Δ | yıl artı |
|---|---|---|---|---|---|
| V1 2×ATR5 | +32,5 | ✓ | 0,96 | +33,9 | 6/9 |
| **V1 2,5×ATR5** | **+39,4** | ✓ | 0,95 | +44,0 | 6/9 |
| V1 3×ATR5 | +27,1 | ✗ | 0,83 | +40,4 | 6/9 |
| V3 0,75×ATR1h | +42,5 | ✗ | 1,00 | +42,1 | 5/9 |
| V4 1×ATR1·√30 | +40,7 | ✗ | 0,95 | +45,2 | 6/9 |
| V4 2×ATR1·√30 | −59,6 | ✗ | 0,08 | −39,1 | 3/9 |

**Kart (V1 2,5×, 2. KURAL):** n 3.089, ort. R +0,061 (taban +0,043), P %99,9, yarılar +0,043 / +0,080, spread ×1,5 +0,052, icra farkı
(lag 0 +0,048) ölçüt içinde, tek pozisyon (DC) +0,039 → **6/6 LIVE**. **Braket plasebosu** (aynı SL genişlik dağılımı, işlemlere rastgele
atanmış, 30 koşu): medyan −31,6R, %90 −4,7R vs gerçek +39,4R → **p = 0,000** — kazanç geniş stoptan değil, genişliğin oynaklığa göre
seçilmesinden. Yıllar (Δ): 2018 +12,1 · 2019 −3,2 · 2020 +11,5 · 2021 −8,5 · 2022 +22,5 · 2023 +4,5 · 2024 +0,1 · 2025 −1,5 · 2026 +1,8.

**Bugünkü canlı 10 işlem, aynı giriş fiyatı/saatiyle:** 80/110 → 6 TP / 4 SL (+1.200 $ sim); V1 2× → 2/4 SL kurtulur, 5/6 TP (+5.342 $);
**V1 2,5× → 3/4 SL kurtulur, 5/6 TP (+8.334 $)**. Kurtulan SL'ler gün sonunda (21:58) hâlâ açıktı, son fiyattan değerlendirildi.
Tarihsel SL-engel %13 / TP-kayıp %10: kural "SL'yi tanımıyor", oynak günde gürültü SL'lerini azaltıyor ve lotu küçülttüğü için o
günlerin $ salınımını da düşürüyor.

**Bugüne benzer geçmiş günler (lag 1, tabanda ≥4 SL'li 75 gün):** SL 389 → 240 (**engel %38**; 2025 %46, 2026 %48, 2023 %17,
2024 %12), TP 348 → 245, gün R ort. **−1,81 → −0,82**. ≥3 SL'li 162 günde engel %28, gün R −1,53 → −0,97. Diğer 735 günde
+0,542 → +0,470R (sakin günlerde lot küçülmez; fark oynak ama kötü olmayan günlerden). **%60 engel bugün sağlanıyor (%75); tarihsel
kötü günlerde ortalama %38 — %60'ı sürekli verecek kural yok.**

**Bağlandı:** `yeni deneme/vol_bracket.py` (saf fonksiyonlar, fail-open) + `open_trade` kancası, kapsam `NDX.INDX:BUY:DAYCOMBO` ve
`NDX.INDX:BUY:REENTRY`; `DAYCOMBO_VOL_BRACKET=True`, `DAYCOMBO_VOL_K=2.5` (config getattr). Test `test_vol_bracket.py` (araştırma ATR
paritesi dahil). Kart `backend/data/evolution/go_live_cards/ndx_daycombo_vol_braket.json`. Durdurma: genişletilmiş işlemler n=60'ta
ort. R < 0 → `DAYCOMBO_VOL_BRACKET=False`.

## 6. Yan bulgu (operasyon)
`indicator_snapshots` dört sembolde **2026-11-19 05:03 UTC'den beri yazılmıyor**; kutu sağlığı `recorder_alive=True` diyor,
kaydedici her dakika döngüde ama "tick yok". Aynı dakikalarda DBG klonu yeniden başladı → kaydedicinin yanlış MT5 terminaline
(DBG 303733) bağlanmış olması güçlü olasılık. Etkisi: otopsi aracı ve panel 11-19 sonrasını göremiyor (bu çalışma kutudan MT5
M1 çekerek tamamlandı).

## Dosyalar
`PROTOCOL.md` (ön kayıt + EK-1/2) · `src/eng.py` (motor) · `src/s0_taban.py` · `src/s1_tarama.py` · `src/s2_derin.py` ·
`src/s3_yillik.py` · `src/s4_gecikme.py` · `src/s5_lag1.py` · `results/` (tarama.csv, yillik_delta.csv, gecikme.csv, lag1.log,
sinir_egrisi.csv, derin*.log). Veri `data/` git dışı.

## 8. Aşırı oynak rejime özel strateji (EK-5, `src/s8_rejim.py`, `results/rejim_tarama.csv`)
Rejim: σ30 = ATR14(1m)·√30 / fiyat ≥ θ (bugün %1,89). θ = %1,0 → 9 yılda 258 gün; θ = %0,8 → 522 gün.

| strateji (θ = %1,0) | n | ort. R | SL payı | 2018–20 | 2021–23 | 2024–26 | 2023 / 2024 / 2025 / 2026 Σ R |
|---|---|---|---|---|---|---|---|
| **K0 mevcut DAYCOMBO+REENTRY (V1 braket)** | 105 | **+0,184** | %31 | +0,190 | +0,152 | +0,223 | −1,8 / +0,2 / +4,5 / +0,6 |
| DIP m=2, TP 1,5 / SL 1,5 ATR5 (en iyi yeni) | 505 | +0,066 | %45 | +0,109 | +0,035 | +0,035 | −4,5 / +1,5 / +1,6 / 0,0 |
| DIP m=1, TP 1,5 / SL 1,5 | 715 | +0,030 | %47 | +0,029 | +0,034 | +0,022 | −6,5 / +7,5 / −0,9 / −4,0 |
| KIRILIM 30 dk, TP 1,5 / SL 1,5 | 303 | +0,027 | %47 | +0,057 | +0,004 | +0,009 | 0,0 / +2,0 / +2,4 / −4,0 |

θ = %0,8'de yeni adayların hepsi eksi (2024–26 −0,06…−0,19R). DIP m=2 plasebo p 0,015 (rastgele rejim dakikası medyan −0,012R) ama
24 hücrede çoklu sınama eşiği ≈ 0,004 → geçmedi; K0'dan zayıf.
**Hüküm:** bugünkü gibi aşırı oynak günler için en iyi strateji yeni bir strateji değil, **mevcut DAYCOMBO + oynaklığa göre braket (SL-08)**.
Bu rejimde işlem başı +0,18R ile kitabın en iyi dilimi, SL oranı %31 (normal günlerde ~%40). "Daha çok işlem" isteyen dip/kırılım
türevleri işlem sayısını 3–7 kat artırıyor ama işlem başı kazancı düşürüyor ve son yıllarda tutmuyor. Bağlanmadı.
