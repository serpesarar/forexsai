# Ön kayıt — NASDAQ V / W dip sistemi: farklı giriş ve TP'lerle kâr kapısı araması (2026-11-17)

Bu dosya sonuçlara bakılmadan yazıldı.

## 0. Kaynak ve gerekçe

**Kullanıcı hedefi:** 3,5 sa alt fitil sistemini (`research/fitil210_15m_20261117`, defter §2.65) farklı TP'ler ve giriş noktalarıyla
geçmişte deneyip kâr kapısı bul. Sistemin mantığı **V ya da W**: büyük düşüşten sonra (çift) dip, ardından yükseliş.

**Defter bağlantısı:**
- §2.65: 3,5 sa fitil, 15m seviyeler X.
- FR-07/FR-10/FR-15: 1h çekiç, tepe kırılımı ve teyitli çekiç, B/B−.
- GF-16 CAPREV: stres ∧ VIX ≥ 18,4 kapitülasyon alımı, B+.

Meta-dersler:
- 2: korku döner.
- 3: teyit sinyal ölçeğinde iyi.
- 5: braket ≠ zaman.
- 15: süpürme tek başına dönüş değil.
- 19: limit giriş öder.

Çift dip (W) defterde hiç sınanmadı → yeni tanım. V ailesi FR/§2.65'in 15m/210m karşılığı.

## 1. Veri ve dönemler

- **Yol:** Dukascopy NDX 1m (ndx_tf_yapilandirma birleşik kaynağı), ask = bid + spr.
- 15m ve 210m mumlar NY 17:00 çapasıyla (`research/fitil210_15m_20261117/src/veri.py`).
- **KEŞİF** 2018-01-02 → 2021-10-31: tüm seçim burada.
- **TEST** 2021-11-01 → 2026-11-15: dondurulmuş adaylar, bir kez.
- **Bağımsız besleme:** kutu MT5 NAS100 M15, 2022-08 → 2026-11-17 (15m çözünürlük, aynı mumda TP+SL → SL).
- **VIX:** önceki günün kapanışı (`macro_daily.parquet`).

## 2. Çapalar (L1 = birinci dip)

- **A210 (kullanıcının sistemi):** 210m mumda alt fitil ≥ %0,50 ∧ üst fitil ≤ alt/2 (§2.65 E1 tanımı, Dukascopy).
  L1 = mumun dibi. Karar anı = 210m kapanışı.
- **AG (genel düşüş dibi):** 15m mum m, son 192 mumun (≈2 işlem günü) en düşük dibi ve o pencerenin tepesinden ≥ %1,5 aşağıda;
  fraktal teyidi m+1 ve m+2'nin dipleri daha yüksek. Karar anı = m+2 kapanışı. Aynı çapadan sonra 96 mum soğuma.

## 3. Girişler (8 tip; hepsi karar mumunun kapanışından sonraki 1m açılışında, ask)

| kod | çapa | giriş |
|---|---|---|
| V1 | A210 | 210m kapanışında |
| V2 | A210 | 96 mum içinde ilk 15m kapanış > 210m mumunun tepesi |
| V3 | A210 | 96 mum içinde ilk 15m kapanış > ana mum üstü (210m'nin 14 mumunda en büyük kırmızı gövdenin açılışı) |
| VG | AG | fraktal teyidinde |
| W1b / WGb | A210 / AG | ikinci dip L2 teyidinde: L2 fraktal (±2 mum en düşük), L2 ∈ [L1·(1−%0,25), L1·(1+%0,40)], L2 ≥ L1'den 3 mum sonra ve çapa kararından sonra; boyun N = L1–L2 arası en yüksek tepe, (N − L1)/L1 ≥ %0,30; teyit mumu kapanışı > L2 mumunun kapanışı. L2'den önce fiyat L1·(1−%0,25) altına inerse W iptal. Arama 96 mum |
| W1a / WGa | A210 / AG | W'den sonra 32 mum içinde ilk 15m kapanış > N (boyun kırılımı) |

**Stop:**
- V: L1 · (1 − %0,10).
- W: min(L1, L2) · (1 − %0,10).
- En az 5 bp.

## 4. Bağlam × çıkış ızgarası

- **Düşüş:** düşüş = (son 192 mum tepesi − L1) / tepe. Seviyeler {hepsi, ≥ %1,5, ≥ %3}. AG'de "hepsi" = ≥ %1,5.
- **VIX:** {hepsi, ≥ 18,4}.
- **TP:** {1R, 2R, 3R, 5R, yok}.
- **Zaman:** {4 sa, 24 sa, ertesi işlem günü NY 16:00}.

Toplam hücre: 8 × 3 × 2 × 5 × 3 = **720**.

İcra:
- TP ve stop 1m bid yolunda; aynı barda ikisi → stop.
- Uzunda gecelik finansman (FR-18).
- R = net getiri / stop mesafesi.

## 5. Seçim (yalnız KEŞİF)

Aday hücre:
- n ≥ 40,
- ort R > 0,
- gün-küme bootstrap P(EV>0) ≥ %90,
- spread × 1,5'te > 0.

**Izgara plasebosu:** her gerçek giriş, ±5 işlem günü içinde aynı NY saatindeki rastgele bir 15m kapanışına taşınır. Stop aynı %
mesafede, çıkışlar aynı. 20 kopyada "aday sayısı" dağılımı çıkarılır. Gerçek aday sayısı plasebo %95'ini aşmazsa ızgara şans
düzeyindedir.

Dondurma:
- KEŞİF t-istatistiğine göre en iyi **en fazla 5 hücre**.
- Aynı giriş tipinden en fazla 2.

## 6. Doğrulama (dondurulmuş adaylar)

Geçme ölçütü, hepsi birden:
1. TEST ort R > 0 ve küme P ≥ %90.
2. MT5 bağımsız ort R > 0.
3. Spread × 1,5 > 0.
4. Tek pozisyon kısıtıyla > 0.
5. Eşli plasebodan iyi (P ≥ %90).
6. İcra farkı (iyimser − gerçek) < 0,5 × |gerçek|.
7. Toplam n ≥ 150 (2. KURAL kartı).

Geçen olursa CAPREV ile gün örtüşmesi ve CAPREV dışındaki günlerde sonucu ayrıca raporlanır. Kart
`backend/data/evolution/go_live_cards/ndx_vw_<kod>.json`'a yazılır; canlıya bağlanmaz (2. KURAL, kullanıcı kararı).

**Hüküm:**
- Hepsi geçerse B.
- TEST + MT5 artı ama başka ölçüt düşerse C.
- Aksi hâlde X.

## EK-1 (2026-11-17, 1. tur sonuçları görülmeden yazıldı) — çok turlu arama kuralı

Kullanıcı "kâr kapısı bulana kadar" istedi. Tur sayısı arttıkça şans eseri geçme olasılığı büyür. Bu yüzden:

1. Her tur yeni bir **mekanizma gerekçesiyle** açılır (sonuçtan türetilmiş parametre ince ayarı değil). Izgarası tur başında yazılır;
   seçim yalnız KEŞİF'te yapılır.
2. **Birikimli Bonferroni:** k. turda TEST'e giden adayların toplam sayısı K ise (önceki turlar dahil), TEST küme P eşiği
   1 − 0,10 / K olur (ilk tur 5 aday → %98). Diğer §6 ölçütleri aynen kalır.
3. **Önceden belirlenmiş tur planı** (1. tur geçmezse sırayla):
   - **Tur 2 — zaman çıkışı ("braket ≠ zaman", GF-17):** aynı 8 giriş; çıkış 2/3/5 işlem günü sonra NY 16:00, stop yalnız felaket stopu
     (2 × yapı riski) ya da yapı stopu; bağlam düşüş {≥ %3, ≥ %5}, VIX {≥ 18,4, ≥ 22}.
   - **Tur 3 — W'nin kendi hedefi:** W girişleri için ölçülen hareket TP'si (boyun + (boyun − dip)) ve boyun-geri-test girişi
     (kırılımdan sonra boyuna dönüp üstünde kapanış, 32 mum).
   - **Tur 4 — bağımsız piyasa taşıması:** tur 1–3'te TEST'i geçen en iyi tanım, değiştirilmeden kutu MT5 GER40/US500 M15 2022-08 →.
     Hiçbiri geçmediyse: üç turun en iyi KEŞİF hücresi, yalnız taşıma bilgisi için.
4. Dört tur sonunda geçen yoksa arama durur ve aile X olarak deftere yazılır. "Bulana kadar" sonsuz döngüye çevrilmez: sınırsız arama
   her veride bir şey "bulur" (E51, E84).

## EK-2 (2026-11-17, sonuçlardan önce) — veri kaynağı sabitlendi

Ortak yükleyici `ndx_tf_yapilandirma/src/kaynak.py::load_duka_1m` koşu sırasında başka bir oturumca değiştirildi (commit f54cad72,
2025 yeniden indirme birleşimi) ve bir uyuşmazlık denetiminde durdu. Bu araştırma sabit kaynağa bağlandı: `lib.load_m1()`
(ana Dukascopy 1m v3; NDX 9 yıllık 1m çalışmasının önbelleği). Fark yalnız M1 dışa aktarımından gelen ~16.800 ek dakika
(birkaç 210m mumu); tanımlar değişmedi.

## Tur 1–2 sonuçları (kayıt)

**Tur 1:** 720 hücrenin 39'u KEŞİF ölçütünü geçti. Izgara plasebosunda aday sayıları 0…51, gerçek değer plasebonun %80'inde →
ızgara şans düzeyinde. Dondurulan 5 aday kör TEST'te (Bonferroni P ≥ %98):

| aday | TEST | MT5 | ölçüt |
|---|---|---|---|
| W1b, düşüş ≥ %1,5, VIX ≥ 18,4, TP 2R, ertesi gün 16:00 | +0,192R (n 145, P %94,9) | +0,121R | 6/7 (yalnız Bonferroni eşiği düştü) → **C+** |
| V3, VIX ≥ 18,4, 1R, 24 sa | +0,022 | — | 5/7 |
| V3, VIX ≥ 18,4, 1R, ertesi gün 16:00 | +0,029 | — | 6/7, TEST P %70 |
| W1b, düşüş ≥ %1,5, 2R, 24 sa | +0,005 | −0,096 | 3/7 |
| VG, 5R, 24 sa | −0,144 | — | 2/7 |

**Tur 2:** 192 hücrede 1 aday (plasebo %95 = 1) → şans. V3, düşüş ≥ %3, VIX ≥ 18,4, 5 gün: TEST −0,288, MT5 −0,280 → X.

## EK-3 (tur 3 sonuçlarından önce) — W'nin kendi hedefi

Girişler:
- W1b, W1a, WGb, WGa (tur 1 tanımları).
- Yeni **W1r / WGr — boyun geri-testi:** boyun kırılımından (W·a sinyal mumu) sonra 32 mum içinde dibi boyun·(1+%0,10)'a inip
  boyun üstünde kapanan ilk 15m mum.

Stop: min(L1, L2)·(1 − %0,10).

Izgara:
- TP: {**ölçülen hareket** MM = boyun + (boyun − min(L1, L2)), 2R, yok}.
- Zaman: {24 sa, ertesi gün 16:00, 3. işlem günü 16:00}.
- Düşüş: {≥ %1,5, ≥ %3}.
- VIX: {hepsi, ≥ 18,4}.

6 × 3 × 3 × 2 × 2 = 216 hücre. Seçim ve doğrulama §5–6 ve EK-1 ile aynı. Birikimli K = 6 + bu turda dondurulan sayı.

## EK-4 (2026-11-18, DAX sonuçlarından önce) — dondurulmuş en iyi kuralın bağımsız piyasada uzun doğrulaması

Bu yeni bir arama değil. Kural değiştirilmeden taşınır:
- W1b ∧ düşüş ≥ %1,5 ∧ VIX ≥ 18,4, TP 2R, ertesi gün NY 16:00.
- Ön kayıtlı tur 3 hücresi (W1b ∧ düşüş ≥ %1,5, 2R, 3. gün 16:00).

Veri: Dukascopy DAX (DEUIDXEUR) 1m BID 2018-01 → 2026-11 + spread modeli (`fibo_altin_bolge_20261116/cache/DAX_1m.npz`). 4. turdaki
GER40 sınaması yalnız 2022 sonrası broker verisiydi (n 84).

**Doğrulama ölçütü** (hepsi):
- DAX 2018–26 ort R > 0 ve küme P ≥ %90,
- kronolojik iki yarı ≥ 0,
- spread × 1,5 > 0,
- eşli plasebodan iyi (P ≥ %90).

Geçerse aday C+ → B− olur (iki bağımsız piyasa). Kart SHADOW kalır; LIVE kararı kullanıcıdadır. Geçmezse aile kapanır.
