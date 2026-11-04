# ON — NDX gece sürüklenmesi ("overnight drift / night effect") ön-kaydı

Yazıldı: 2026-10-13, **sonuçlara bakılmadan** (yalnız saat ekseni denetimi `axis_check.py` koşuldu — getiri hesaplamaz).
Kod: `research/nasdaq_derin_20261013/overnight/` (yalnız bu klasör). Canlı bot/backend/DB'ye dokunulmaz.

## 0. Defter kontrolü (3. KURAL) — neden yeni

* **GF-03** gün×saat sürüklenme *takvimi* (168 hücre, 2016-20 ↔ 2021-26 korelasyonu ≈0) çağlar arası taşınmadı. Bu
  çalışma takvim madenciliği DEĞİL: pencere **literatürden önceden belirlenmiş** (Boyarchenko-Larsen-Whelan 2023:
  02:00–03:00 ET; Bondarenko-Muravyev: 23:30–03:30 ET; Cliff-Cooper-Gulen: kapanış→açılış) ve **tek** pencere ailesi
  sınanıyor. Yeni gerekçe: yayımlanmış bir iddianın (S&P e-mini, 1998–2020) **farklı endekste (NDX CFD) ve büyük
  ölçüde yayın-sonrası dönemde** (2021+) sınaması + CFD maliyetleri (spread + gece finansmanı).
* **CP (ndx_caprev_paths)**: CAPREV 2. bacağının gece taşınması daha kötüydü — o, dip-alım pozisyonunun taşınmasıydı;
  burada koşulsuz ve önceki-gün-koşullu pencere tutma sınanıyor. CAPREV ile ilişki (korku döner) ayrıca raporlanır.
* Tuzaklar: E2/E4 (saat ekseni) → `axis_check.py`: 1m 2025-01…2026-09 en büyük medyan aralık 09:30–09:31 ET
  (Şub–Nis 2025'te 10:00 makro verisi, 09:31 ikinci); 30m 2021–26 her yıl 09:30 ET; 1h 09:00/10:00 barı; DAX 30m/1h
  2019+ her yıl 09:00 Berlin. Eksen doğru. E7 (giriş = sonraki bar açılışı + spread), E13/E15 (taban = aynı dönem,
  aynı süre, gelecek bilgisi yok), E23 (NDX'e çok bakıldı → DAX + kasa), E24 (aile içinde çoklu test → Bonferroni notu).

## 1. Veri

| Set | Kaynak | Dönem (keşif) |
|---|---|---|
| NDX 1h | `ndx_gate_forge.long_data.load_long('1h')` (UTC, bar başlangıcı) | 2016-05-29 → 2026-06-30 |
| NDX 30m | `load_long('30m')` | 2021-06-29 → 2026-06-30 |
| NDX 1m | `ndx_pattern_motifs/data/bars_1m.parquet` | 2025-01-02 → 2026-06-30 (2026-01-01→02-10 boşluk) |
| DAX 1h | `ndx_gate_forge/data/dax_1h.parquet` | yoğun veri 2019+ → 2019-01-01 → 2026-06-30 |
| DAX 30m | `dax_30m.parquet` | 2021-03-17 → 2026-06-30 |
| Makro | `macro_daily_patched.csv` (VIX_close; yalnız ÖNCEKİ gün) | |

**Kasa (lockbox):** 2026-07-01 → 2026-10-02, NDX 1m + 30m (bars_30m, ndx_pattern_motifs) ve DAX 1h/30m —
tüm stratejiler keşif bittikten sonra **bir kez** açılır. Kasada n≈65 gün → yalnız işaret kontrolü (kart değil).

Fiyat(T) = başlangıcı tam T olan barın **açılışı** (T ET saati). Bar yoksa olay atlanır (doldurma yok).

## 2. Stratejiler (hepsi yalnız LONG)

Saatler America/New_York (DST'li). D = NY işlem günü (Pzt–Cum).

| Kod | Giriş | Çıkış | 1h vekili | Swap |
|---|---|---|---|---|
| **S1 NIGHT** | 18:00 ET, D'den önceki açık seans günü (Pzt için Pazar 18:00) | D 09:30 | çıkış 09:00 barı açılışı | yok (17:00 rollover'ı geçmez) |
| **S2 CTO** | D−1 16:00 (Cuma→Pzt dahil) | D 09:30 | çıkış 09:00 | 1 gece; Cuma rollover ×3 |
| **S3 EU** | D 01:00 | D 04:00 | birebir | yok |
| **S4 OD** (literatür kopyası, ikincil) | D 02:00 | D 03:00 | birebir | yok |
| **S5** | S3, önceki nakit gün getirisi ≤ −%0,5 | | | |
| **S6** | S3, önceki gün ≤ −%1,0 | | | |
| **S7** | S1, önceki gün ≤ −%0,5 | | | |
| **S8** | S1, önceki gün ≤ −%1,0 | | | |
| **S9** | S3, VIX(D−1 kapanış) ≥ 18,4 | | | |
| **S10** | S3, önceki gün ≤ −%0,5 ∧ VIX ≥ 18,4 | | | |
| INTRA (kıyas) | D 09:30 | D 16:00 | 10:00 → 16:00 | yok |
| HOLD (kıyas) | D−1 16:00 | D 16:00 (her gün sürekli long) | birebir | her gece |

*Önceki nakit gün getirisi* = P(16:00, D−1)/P(16:00, D−2) − 1 (enstrümanın kendi 16:00 ET bar açılışı; S1/S7/S8 için
giriş 18:00 D−1'de bu bilinir). VIX: `macro` satırı tarih = D−1 (S1'de giriş 18:00 D−1 → VIX 16:15'te bilinir).

## 3. Maliyet, birim

* **Spread:** 1,5 puan / gidiş-dönüş (sabit puan; 2016'da fiyat 4.500 iken bu ~3 bp → erken yıllarda muhafazakâr).
  Duyarlılık: ×1,5 = 2,25 puan (kart ölçütü 4) ve **gece spread'i 3,0 puan** (ek rapor).
* **Gece finansmanı (long):** P_rollover × (ARR + %2,5)/360 her 17:00 ET rollover'ında; Cuma ×3 (Pepperstone
  "Kosten und Gebühren": endeks formülü Nominal × (ARR ± %2,5)/360, endekslerde Cuma üçlü swap). ARR (yıllık ort., ≥0'a
  tabanlı, yaklaşık): USD 2016 0,40 · 2017 1,00 · 2018 1,83 · 2019 2,16 · 2020 0,38 · 2021 0,08 · 2022 1,68 ·
  2023 5,02 · 2024 5,14 · 2025 4,21 · 2026 3,64 (2026 değeri kutunun gerçek NAS100 swap'ından kalibre: 5 lot BUY
  29.503'te −25,16$/gece = −5,03 puan/lot = %6,14 yıllık). EUR (€STR/EONIA, 0 tabanı): 2016–2022 0 · 2023 3,25 ·
  2024 3,65 · 2025 2,20 · 2026 2,19 (kutu GER40 SELL swap'ından kalibre).
* **R birimi:** R = net puan / (σ20 × P_giriş); σ20 = enstrümanın kendi 16:00 ET (DAX: 17:00 Berlin) günlük
  getirilerinin D−1'e kadar son 20 günlük std'si (nedensel). Puan ve bp da raporlanır.

## 4. Kart (2. KURAL) — her S için, ana veri NDX 1h 2016-05 → 2026-06 (net: spread + swap)

1. ≥150 olay. 2. ortR > 0 ve **ay-blok bootstrap** (takvim ayları yeniden örneklenir, 5.000) P(EV>0) ≥ %90.
3. Kronolojik iki yarı (olay sayısına göre) ikisi de ≥ 0. 4. spread ×1,5 ile ortR > 0.
5. İcra: **1m veride** (2025-01 → 2026-06) gerçekçi = T+1 dk barının açılışı + spread (çıkış da T+1 dk), iyimser =
   T barının açılışı, spread'siz; (iyimser − gerçekçi) < gerçekçi ortR/2 (gerçekçi ortR > 0 şart).
6. Tek pozisyon: pencereler günlük ve çakışmasız → yapısal olarak sağlanır; kod çakışmayı denetler.

**Ek zorunlu kıyaslar (karta ek, verdikte yazılır):**
* **Taban A — aynı süre, her saatte long:** aynı günlerde, aynı uzunlukta, 24 başlangıç saatinin hepsinden pencere
  (ham bp). Pencerenin sırası (kaçıncı) ve "diğer saatlerin ortalaması" farkı. Literatür iddiası: S3/S4 en üst sırada.
* **Taban B — koşul katkısı:** S5–S10 için koşullu − koşulsuz (aynı pencere) farkı, ay-blok bootstrap P(fark>0).
* **Taban C — INTRA ve HOLD** aynı dönemde, yıllık % ve Sharpe (net).
* Yıl yıl tablo; çağlar 2016–2020 / 2021–2026H1; en iyi 5 gün çıkarılınca ortR.
* Saat-saat ortalama getiri tablosu (1h 10 y, iki çağ; 1m 2025–26), t-istatistiği.
* Aile: 10 strateji → Bonferroni ilavesi P(EV>0) ≥ %99 "güçlü" etiketi (verdikt bunu ayrıca söyler).

## 5. Bağımsız piyasa — DAX (aynı tanım, sonuçlara bakmadan sabit)
* **DX-EU:** 01:00 → 04:00 **ET** (aynı küresel saat; Berlin 07:00→10:00, Xetra açılışını içerir), DAX 1h 2019+.
* **DX-PRE:** 08:00 → 09:00 **Berlin** (Avrupa açılış öncesi saat = OD saatinin Berlin karşılığı), DAX 1h.
* **DX-NIGHT:** 17:30 Berlin → ertesi işlem günü 09:00 Berlin, DAX 30m 2021+, swap EUR tablosu.
* **DX-EU|dn0.5 / dn1.0:** DX-EU, DAX önceki gün (17:00 Berlin bar açılışı → 17:00) ≤ −%0,5 / −%1,0.
* Spread 1,5 puan; aynı kart ve kasa.

## 6. Verdikt kuralı
Bir varyant ancak NDX 1h kartının 6/6'sını geçer **ve** taban A/B'yi geçer **ve** DAX karşılığı aynı işarette **ve**
kasada negatif değilse "LIVE adayı" denir; aksi hâlde SHADOW/RED. Kasa sonucu verdikti yalnız düşürebilir.
Sonuçtan sonra pencere/eşik değiştirilmez; ek keşifsel inceleme yapılırsa "post-hoc" olarak etiketlenir.

## 7. Uygulama ayrıntısı (sonuçlardan önce eklendi)
* 1m veride fiyat(T) = başlangıcı ≥T olan ilk barın açılışı, en çok T+5 dk (task: "first 1m open at/after");
  gerçekçi = başlangıcı ≥T+1 dk olan ilk bar (≤T+6 dk) + spread. 1h/30m: tam T barı, yoksa olay atlanır.
* Swap gece sayısı = giriş ve çıkış NY tarihleri arasındaki takvim günü (Cuma→Pzt = 3 = Cuma üçlü swap'ı).
* Taban A brüt bp ile (maliyetler pencereler arasında farklı olduğu için ayrıca net de verilir).
