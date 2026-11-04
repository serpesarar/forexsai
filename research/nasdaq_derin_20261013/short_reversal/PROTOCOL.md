# ÖN KAYIT — Kısa vadeli (1–5 gün) "dibi al" ortalamaya dönüş kuralları, NDX (+DAX)

Tarih: 2026-10-13 · Yazıldı: sonuçlara BAKILMADAN (veri yalnız kapsam/sütun kontrolü için açıldı).
Kod: bu klasör. Canlı bot / backend / DB'ye dokunulmaz, commit yok.

## 0. Defterle ilişki (3. KURAL)
- Yeni olan: CAPREV (GF-16..22) gün-içi, stres∧VIX'e bağlı, tek seans tutuyor. Burada **günlük çizelgede, kapanışta karar, 1–10 gün
  tutma** — Connors RSI(2), N-gün dibi, IBS, ardışık düşüş günü, büyük düşüş günü. Defterde bu aile (çok-günlü tutma, günlük
  osilatör) hiç sınanmadı. GF-05 gün-düzeyi koşullar (dünkü getiri dahil) **gün-içi saat başı yön** için bakıldı; burada hedef
  çok-günlü tutma + zaman/MA çıkışı.
- Dayandığı ilke: §3/2 "korku döner, coşku dönmez", §3/5 "braket ≠ zaman" (ana çıkışlar zaman/MA; stop yalnız koruma).
- Tuzaklar: E15 (taban dönem × tutma uzunluğu ile, gelecek ortalaması yok), E7 (giriş sinyal kapanışı değil, sonraki bar açılışı
  + spread), E20 (makro dosyanın 07-28 sonrası günlük yüksek/düşükleri tutarsız → IBS CFD barlarından), E23 (NDX'e çok bakıldı →
  DAX bağımsız, kasa), E24 (çok hücreden seçme → ızgaranın pozitif ORANI ve komşuluk düzgünlüğüyle karar; seçilen hücre ayrıca
  işaretlenir), E6/E9 (olay = karar günü; pozisyon açıkken yeni sinyal yok).

## 1. Veri
- **Ana (keşif):** NDX CFD 1h `ndx_gate_forge.long_data.load_long('1h')` (UTC; 2016-05-29 → 2026-07-14). Keşif penceresi giriş
  tarihi **< 2026-07-01**.
- **Günlük seri (karar):** NY işlem günü t için C_t = 16:00 ET'de biten barın kapanışı (15:00 barı). H_t / L_t = 09:00–16:00 ET
  barlarının (1h'te 09:00 barı 30 dk ön-seans içerir — yaklaşık RTH; kasada 30m'den 09:30–16:00 tam RTH) yüksek/düşüğü.
  IBS = (C−L)/(H−L). Kontrol: 1h-IBS ile makro dosyadaki nakit IBS korelasyonu raporlanır (≤2026-07-28).
  MA200 ısınması için CFD başlangıcından önceki günler makro `NDXCASH_close` ile (oranla eklenmiş) doldurulur.
- **VIX:** makro `VIX_close` **önceki gün** (t−1) değeri (VIX 16:15'te kapanır → t günü kapanışı karar anında bilinmez).
- **Kasa (bir kez açılır):** NDX 30m `ndx_pattern_motifs/data/bars_30m.parquet` (2023-10 → 2026-10-02). Kasa = giriş tarihi
  2026-07-01 → 2026-10-01 (son tam gün). Göstergeler 30m günlük serisinden; 1h ile örtüşen dönemde (2023-10 → 2026-06) iki
  kaynağın günlük kapanışı karşılaştırılır.
- **DAX (bağımsız piyasa, yeniden ayar YOK):** `dax_1h.parquet`, Berlin saati; C = 17:00 Berlin'de başlayan barın kapanışı
  (≈17:30 kapanışın yaklaşımı → 18:00 bar bitişi, `cross_market.build_dax` ile aynı), H/L 09:00–18:00. 2016-06 → 2026-10-01.
  VIX filtresi aynı (ABD VIX t−1).

## 2. İcra ve maliyet
- Karar: t günü kapanışında (C_t bilinir). **Gerçek giriş (E1):** 16:00 ET'de başlayan barın AÇILIŞI (CFD seans sonrası işlem
  görür; DAX'ta 18:00 Berlin barı) + maliyet. **İyimser giriş:** C_t, maliyetsiz (5. ölçüt için).
- **Yan giriş (E2):** ertesi gün ilk RTH barının açılışı (1h: 10:00 ET barı; kasada 30m 09:30 barı). Yalnız rapor.
- Çıkış: çıkış günü d'nin 16:00 barının açılışı (aynı mekanik). Çıkış koşulu C_d ile değerlendirilir.
- Maliyet: **spread 1,5 puan + 2×0,2 kayma = 1,9 puan/işlem** (DAX aynı puan). 4. ölçüt: spread ×1,5 (2,65 puan).
- **Swap (gece finansmanı, uzun):** nominalin yıllık %6'sı / 360 × tutulan takvim gecesi (hafta sonu 3 gece). Muhafazakâr sabit
  (2016–21 faizleri ~0'dı; ek rapor %3). DAX aynı.
- Koruyucu stop: giriş − s × σ_d × giriş, σ_d = önceki 20 günlük günlük getiri std'si (t'de bilinen). s ∈ {yok, 1,5, 2}.
  Stop seans içi ve gece barlarının düşüğüyle; boşlukta bar açılışından dolum.
- **Birim:** PnL / (σ_d × giriş) = "σR" (tüm varyantlar karşılaştırılabilir; stop'lu varyantın gerçek R'si σR/s).
- Pozisyon açıkken aynı kuraldan yeni sinyal alınmaz (tek pozisyon zaten tanım gereği; 6. ölçüt ayrıca portföy için).

## 3. Ön-kayıtlı ızgara (keşif, < 2026-07-01)
Sinyaller (t kapanışı):
- S-RSI θ: Wilder RSI(2) < θ, θ ∈ {5, 10, 15}
- S-LOW N: C_t ≤ min(C_{t−N+1..t}) (N-gün kapanış dibi), N ∈ {3, 5, 10}
- S-IBS q: IBS < q, q ∈ {0,2, 0,3}
- S-DN3: 3 ardışık düşüş kapanışı
- S-DROP X: günlük getiri ≤ −X, X ∈ {%1, %1,5, %2}
Filtreler: F0 yok · F-MA: C_t > MA200 · F-VIX: VIX_{t−1} ≥ 18,4 · F-MAVIX: ikisi birden.
Çıkışlar: k ∈ {1, 3, 5} gün (k. işlem gününün kapanışında) · MA5: ilk C_d > MA5_d (en çok 10 gün).
Stop: yok / 1,5σ / 2σ.
→ 12 sinyal × 4 filtre × 4 çıkış × 3 stop = **576 hücre**.

**Taban (always-long, E15'siz):** aynı dönem, her işlem günü E1 ile alıp aynı tutma uzunluğu h ve aynı stop ile çıkan ortalama
σR (`base[s][h]`). Olay başı **fazla getiri** = σR − base[s][h_olay]. Taban dönem-eşli: keşif tabanı keşif günlerinden, DAX tabanı
DAX'tan, kasa tabanı kasadan.

**Izgara kararı (ön-kayıtlı):**
- Aile kanıtı: hücrelerin fazla getiri > 0 oranı; sinyal başına parametre komşuluğu monoton/düzgün mü (θ 5→15, N 3→10, q
  0,2→0,3 aynı işaret).
- Yıllık: hücre başına pozitif-fazla yıl sayısı; **2022 ayrı raporlanır**.
- VIX/MA200 bağımlılığı: aynı sinyal×çıkış×stop için F0/F-MA/F-VIX/F-MAVIX fazla getiri karşılaştırması.

## 4. Ön-kayıtlı birincil adaylar (kart bunlar için; seçim yükü yok)
- **H1 (Connors klasik):** RSI(2) < 10 ∧ C > MA200, çıkış MA5, stop yok.
- **H2:** RSI(2) < 10, filtresiz, çıkış MA5, stop 2σ.
- **H3:** IBS < 0,2, filtresiz, k = 1.
- **H4 (Nagel/CAPREV koşulu):** RSI(2) < 10 ∧ VIX_{t−1} ≥ 18,4, çıkış MA5, stop 2σ.
- **H5:** 3-gün dibi (S-LOW 3) ∧ C > MA200, çıkış MA5, stop yok.
Izgaradan en iyi hücre de karta sokulur ama **"seçilmiş (E24)"** damgasıyla; LIVE önerisi için ayrıca DAX ve kasa işareti aynı
olmalı.

## 5. Canlıya alma kartı (2. KURAL, aynı 6 ölçüt) — tam dönem (keşif + kasa), NDX
1 hacim ≥150 olay · 2 ortσR > 0 ve gün-bloklu bootstrap P(EV>0) ≥ %90 · 3 iki kronolojik yarı ≥ 0 · 4 spread×1,5'te > 0 ·
5 |iyimser − gerçek| < 0,5 × |gerçek ortσR| · 6 tek pozisyon (aynı kural + CAPREV ile birlikte portföy: çakışan günde önce açılan
tutulur) > 0. **Ek (karar ölçütü olarak raporlanır):** fazla getiri (always-long tabanına karşı) > 0 ve P ≥ %90; yıl yıl; en iyi
5/10 gün hariç toplam; DAX işareti; kasa işareti.
Kart verdiği: 6/6 → LIVE adayı (karar kullanıcıda, önce gölge) · hacim geçip başka ölçüt düşerse SHADOW · fazla getiri ≤0 ise
"kenar = sürüklenme" notu ile RED.

## 6. CAPREV ilişkisi
CAPREV olay günleri `round4.events(build(load_long('1h'),60,540),'stress','hi')`. Rapor: aday kuralın CAPREV günlerinde pozisyonda
olma / aynı gün sinyal oranı; günlük PnL serileri korelasyonu (aday: pozisyondayken günlük kapanıştan kapanışa σR; CAPREV: olay
günü R_d0), yalnız en az birinin aktif olduğu günlerde ve tüm günlerde.

## 7. Kasa ve DAX
Kasa 2026-07-01 → 2026-10-01 bir kez açılır; H1–H5 + seçilmiş hücre. DAX: aynı ızgara ve H1–H5, yeniden ayar yok.
