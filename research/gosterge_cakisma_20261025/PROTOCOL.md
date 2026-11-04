# Gösterge Çakışma Motoru (GÇM) — ön kayıt

**Kayıt zamanı:** 2026-10-25, hiçbir sonuç görülmeden önce. Bu dosyada sonuç sonrası yapılacak her değişiklik
"EK-n" başlığıyla, nedeniyle birlikte aşağıya eklenir; yukarıdaki metin değiştirilmez.

## 0. Soru

TradingView'daki göstergelerin (resmî 127 teknik + topluluktaki 71 aile; bkz. `research/indicator_atlas_20261025/`)
**eş zamanlı tepkileri ve tepki kombinasyonları**, bir sonraki 1…32 barın **yönünü** zaman-dilimi-eşli tabandan
daha iyi öngörüyor mu? Bu, dar ufuktan (1 bar) geniş ufka (32 bar) ve 1m'den 1d'ye tüm zaman dilimlerinde sınanır.
Bulunan bir kombinasyon başka zaman dilimlerinde ve sonraki dönemde **tekrarlanıyor mu**?

**Önsel beklenti (defter §3.1, GF-01, HK-01…04, OLD-12):** tek tek fiyat-türevi göstergelerin yön kenarı yok. Sistem
bu beklentiyi çürütmeye çalışır; çürütemezse sonuç "yok" olarak yazılır.

## 1. Kapsam ve dürüst sınır

- 29.628 topluluk göstergesinin kodu indirilmedi ve çoğu korumalı/Pine → **her biri ayrı çalıştırılmaz**.
- Bunun yerine her ailenin nedensel bir (ya da birkaç) temsilcisi parametre varyantlarıyla uygulanır.
- Her uygulama `aile` koduyla `topluluk_taramasi/classify.py` ailelerine bağlanır. Kapsama oranı = uygulanan ailelere
  düşen topluluk scriptlerinin payı; raporda yazılır.
- 643 kütüphane (yardımcı kod) ve yalnız alarm/otomasyon araçları gösterge değildir, dışarıda.
- Yeniden çizen (repaint) tanımlar **nedensel** sürümle yazılır:
  - Fraktal / swing: sağ kanat barları kapanınca onaylı sayılır.
  - Ichimoku: Chikou kullanılmaz; bulut 26 bar önce hesaplanmış değerlerle.
  - Nadaraya-Watson: yalnız geçmiş ağırlıklı uç-nokta tahmini.
  - ZigZag: kullanılmaz.

## 2. Veri

NDX ile başlanır, sonra DAX → XAU → USOIL. Kaynaklar `config.py`'de sabit; hepsi UTC, bar başlangıcı damgalı.

**NDX:**

| TF | Kaynak | Aralık |
|---|---|---|
| 1m, 5m | `ndx_pattern_motifs/data` | 2025-01 → 2026-10 |
| 15m, 30m, 1h | `ndx_gate_forge/data/long_*_utc` | 15m 2023-03, 30m 2021-06, 1h 2016-05 → 2026-07 |
| 4h | 1h'ten UTC 00/04/08… sınırlarıyla | — |
| 1d | `ndx_buy_lab/data/long_1d.csv` | 2008 → 2026-07 |

**Diğer semboller:**
- DAX: `ndx_gate_forge/data/dax_{15m,30m,1h}`.
- XAU / USOIL: `pinbar_20261010/data`; yalnız broker satırları, `src=='yahoo'` atılır (E21).
- 4h ve 1d bu sembollerde 1h'ten türetilir.

**Temizlik ve boşluklar:**
- H ≥ max(O, C), L ≤ min(O, C), fiyat > 0 olmayan satırlar atılır.
- Barlar arası boşluk > 3 × TF olan yerde yeni segment başlar.
- Hiçbir ufuk segment sınırını geçemez (o satırın etiketi NaN olur).

## 3. Göstergeler → tepkiler (durumlar)

- Her gösterge yalnız t anına kadarki barlarla hesaplanır. Doğrulama `test_causality.py` prefix testiyle yapılır:
  geleceği değiştirmek geçmiş değerleri değiştirmemeli.
- Her gösterge 2–6 ikili **durum** üretir (ör. RSI14>70, fiyat>Supertrend, MACD hist>0, BB üst bant dışı, squeeze açık).
- **Tetik:** bir durumun başladığı bar (önceki bar 0, bu bar 1).
- **Yakın tetik:** tetik son w = 3 bar içinde ateşlendi.
- Hacim isteyen göstergeler hacmi olmayan TF'lerde (NDX 1m/5m) atlanır.

## 4. Kombinasyonlar ("eş zamanlı çakışma / tepki")

| Seviye | Tanım | Ne ölçer |
|---|---|---|
| L1 | Tetik_i | tek göstergenin tepkisi |
| L2a | Tetik_i ∧ Durum_j | bir tepki, başka bir göstergenin durumu varken |
| L2b | Tetik_i ∧ YakınTetik_j | iki göstergenin ≤3 bar içinde birlikte tepkisi |
| L3 | L2'nin en iyi 300 kombinasyonu ∧ Durum_k | üçlü çakışma; yalnız KEŞİF'te seçilenler genişletilir |

- Aynı göstergeden türeyen durumlar (ör. RSI>70 ile RSI>50) aynı kombinasyonda birleşmez.
- **Örtüşme bastırma (E6/E9):** her tetik sütunu, ufuk h için bir kez ateşledikten sonra h bar susturulur. Olaylar bu
  yüzden bağımsız karar noktalarıdır, n şişmez.

## 5. Etiket ve taban

- **Giriş:** sonraki barın açılışı O[t+1] (E7). Getiri r_h = ln(C[t+h] / O[t+1]); h ∈ {1, 2, 4, 8, 16, 32} bar.
- **Yön isabeti:** sign(r_h) = öngörülen yön. r_h = 0 olanlar sayılmaz.
- **Taban (E13/E15/E27):**
  - Gün-içi TF'lerde aynı bölmenin UTC saat kovası, 1d'de haftanın günü.
  - Her olay için taban isabet = o kovada öngörülen yönün görülme oranı.
  - **Lift** = isabet − taban isabet.
  - Artık getiri e = r_h − μ_kova(bölme). Kova ortalaması bölmenin tamamından alınır, gün içinden değil (E15).
- **Maliyet:** sembol spread'i fiyata bölünür (NDX 1,2 · DAX 1,2 · XAU 0,25 · USOIL 0,03 fiyat birimi; `config.py`).

## 6. Bölmeler

Her (sembol, TF) kendi bar zaman ekseninde kronolojik bölünür: **KEŞİF %60 · DOĞRULAMA %20 · KASA %20**.

- KASA yalnız son raporda, kural donduktan sonra bir kez okunur.
- Eşikler, kova ortalamaları ve yön seçimi yalnız KEŞİF'te yapılır.

## 7. Seçim ve geçme ölçütleri (önceden sabit)

1. **Asgari olay:**
   - KEŞİF'te n ≥ 200 (gün-içi TF'ler), ≥ 100 (4h), ≥ 60 (1d).
   - DOĞRULAMA ve KASA'da ≥ n_min / 4.
2. **İstatistik:** z = ortalama(d·e) / (sd(e)/√n), d = KEŞİF'teki işaret.
3. **Seçim:** her (TF, h) hücresinde KEŞİF |z|'ye göre ilk K = 30 kombinasyon. Olay kümesi daha önce seçilenle %80+
   örtüşen atlanır. L3 için L2'nin ilk 300'ü genişletilir; seçim havuzu L1 + L2 + L3.
4. **Seçim düzeltmeli boş dağılım (E24/E48):**
   - Etiket dizisi KEŞİF içinde ≥ %5 n'lik rastgele ofsetlerle 20 kez dairesel kaydırılır.
   - Tüm kombinasyonların max|z|'si yeniden hesaplanır; %95'lik dilim = **seçim eşiği**.
   - Bu eşiği aşan KEŞİF hücresi "seçimden sağ" sayılır (raporlanır, tek başına geçme değildir).
5. **Doğrulama:** KEŞİF yönüyle aynı işaret ve z ≥ 1,645.
6. **Kasa:** aynı işaret, z ≥ 1,645, **lift ≥ +2 puan** ve ortalama yönlü getiri > maliyet.
7. **Kanıtlı aday** = 5 ∧ 6.
8. **Tekrarlanan:**
   - kanıtlı aday ≥ 2 komşu ufukta (h ve 2h), veya
   - aynı tanım ≥ 2 zaman diliminde kanıtlı.
9. **Sistem düzeyi hüküm (E26/E28):**
   - Kanıtlı aday sayısı boş beklentiyle kıyaslanır: seçilen sayı × 0,05 × 0,05, binom %99 dilimi.
   - Ayrıca DOĞRULAMA ve KASA'da **ters yönde anlamlı** çıkan sayıyla simetri kontrolü yapılır.
   - Fazla değilse sonuç: "kombinasyon kenarı tesadüf düzeyinde".
10. **Tüm-gösterge modeli (karşılaştırma):**
    - Her (TF, h) için KEŞİF'te eğitilen HistGradientBoosting (tüm durumlar + gösterge değerleri).
    - DOĞRULAMA'da erken durdurma; KASA'da AUC ve en güvenli %10'un isabeti vs taban (E62/E63).
    - Model, kombinasyonların toplamda bilgi taşıyıp taşımadığını gösterir. Tek başına canlıya alma kanıtı değildir
      (2. KURAL kartı gerekir).

## 8. Çıktılar

- `results/<SYM>/<TF>/` altında `cells.csv` (her h için seçilen kombinasyonlar + 3 bölme sayıları), `null.csv`,
  `model.csv`.
- `results/ozet_<SYM>.md`: TF × h ısı haritası (kanıtlı aday sayısı, boş beklenti, model AUC).
- `inceleme/` mum-mum inceleme hattı (HTML): seçilen TF'nin son N barı, altında her göstergenin durum şeridi,
  kanıtlı/aday kombinasyonların işaretleri.
- Bittiğinde defter satırı (§2) ve Evrim Paneli notu.

## 9. Yapılmayacaklar

- Sonuca bakıp ufuk, eşik veya bölme değiştirmek.
- KASA'yı birden fazla kez okumak.
- Tek hücrede çıkan sonucu "kenar" diye yazmak (E12/E53).
- Canlıya bağlamak (bu çalışma yalnız araştırma; aday çıkarsa 2. KURAL kartı ayrı iş).

## EK-1 (2026-10-25, NDX 1h duman testinden sonra) — kapsam genişletmesi

İlk kütüphane (118 gösterge, 40 aile) topluluk scriptlerinin %78,5'ini kapsıyordu. Ön kayıt §1 her aileye bir
temsilci istediği için fiyattan nedensel hesaplanabilen 15 aile eklendi:

- RSI diverjansı (fraktal), S/R yakınlığı, premium/discount, swing bacağı, Fibonacci golden pocket
- Darvas/aralık kırılımı, N-bar dönüş, order block retesti, oto trend çizgisi kırılımı, çift tepe/dip boyun kırılımı
- Hacim (yoksa zaman) profili POC'u, persentil, sentetik delta, günlük/haftalık açılış (üst-TF), yuvarlak sayı

Sonuç: 133 gösterge, 353 durum, 55 aile, kapsama %93,2 (boost ağırlıklı ayrıca raporlanır).

Eklenen aileler sonuçlara göre seçilmedi: liste `coverage.json`'daki eksik aileler listesinin kendisi. Tanımlar,
ufuklar, bölmeler ve ölçütler değişmedi. Duman testinin 1h sonuçları atıldı; tüm hücreler yeni kütüphaneyle baştan koşuldu.

**Bilerek dışarıda kalanlar:**
- Seans, mevsimsellik, ekonomik takvim, ICT zaman modelleri: saat kovası zaten tabanda; zaman göstergesi tabana karşı tanım gereği bilgi taşımaz.
- VIX / DXY / COT / duyarlılık: dış veri; bu fiyat hattında yok.
- Harmonik ve Elliott: yeniden çizer / öznel.
- Hepsi-bir-arada ve risk araçları: yön göstergesi değil. Hepsi-bir-arada'nın karşılığı L2/L3 kombinasyonları ve tüm-gösterge modelinin kendisi.

## EK-2 (2026-10-25) — 4h segment kuralı

§2'deki "boşluk > 3×TF → yeni segment" kuralı 4h'te her hafta sonunu kırıyordu. Bir haftada ~30 adet 4h bar olduğu için
h=32 hiç etiket alamıyor, h=16 da yalnız hafta başı barlarından ölçülüyordu (yanlı). 1d için hafta sonu istisnası
zaten vardı, 4h için unutulmuştu. 4h'te ≤ 80 saatlik planlı boşluk artık segment kırmıyor; diğer TF'ler değişmedi.
Ayrıca havuzu boş kalan hücreler çökme yerine "ölçülemez" diye yazılıyor.

## EK-3 (2026-10-25) — boş dağılım tüm aramayı kapsar

İlk kod boş dağılımı yalnız L1+L2 üzerinden kuruyordu. §7.4 "tüm kombinasyonların max|z|"sini istediği için her
kaydırmada L3 genişletmesi de (o kaydırmanın en iyi 300 L2'si × 3. durum) tekrarlanıyor. Bu ön kayda uyum düzeltmesi;
eşik yükseldi (NDX 1h ≈ 4,6 → 5,4).

## EK-4 (2026-10-25, kasa okunduktan sonra) — küçük-n z artefaktı

- **Sorun:** tekrarlanma ölçümünde bazı hücrelerde olay sayısı 1–6 idi. n = 1'de varyans tabanı (1e-18) z'yi milyonlara
  çıkarıyordu. Örneğin "NDX 5m adayı NDX 1d'de 5/5 tekrar" sonucu kasada tek olaydı.
- **Düzeltme:**
  - n < 2'de z = 0.
  - Tekrarlanma ve ters-yön sayımlarında §7.1'deki asgari n (her bölmede ≥ n_min/4) uygulanır. Bu kural ön kayıtta
    DOĞRULAMA/KASA için zaten vardı, ters-yön ve tekrarlanma sayımlarına taşınmamıştı.
- **Etkisi:** seçim, eşikler ve kanıtlı bayrakları değişmedi (hepsi zaten n şartlıydı). Değişen yalnız ters-yön
  sayıları ile tekrarlanma tablosu.

## EK-5 (2026-10-25, ilk tam koşudan sonra) — atlanmış 1m kaynakları

§2 envanteri DAX/XAU/USOIL için 1m yok sanıyordu; bu bir envanter hatasıydı. Bulunan kaynaklar `data_prep.py` ile
UTC'ye hizalanıp eklendi:

| Hücre | Kaynak | Aralık | Not |
|---|---|---|---|
| DAX 1m | `ndx_buy_lab` (candle_cache dökümü) | 2026-02 → 07 | 04-24 öncesi broker saati (E3): 03-01'e kadar −2 s, sonrası −3 s. Doğrulama: Xetra açılış tepesi haftalık 08/07 UTC |
| DAX 5m | 1m'den türetildi | 2026-02 → 07 | — |
| XAU 1m | `decider_xau_ileri` (indicator_snapshots broker, satır bazlı UTC) | 2026-06 → 10 | — |
| USOIL 1m | `wti_transfer` (temiz broker 1m) | 2026-02 → 10 | — |

Tanımlar, ufuklar ve ölçütler aynı. Kısa geçmiş (4–8 ay) nedeniyle bu hücreler zayıf kanıttır.

## EK-6 (2026-10-25) — parametre varyantı kütüphanesi (script düzeyine yaklaşma)

29.628 scriptin her biri çalıştırılamadığı için ana kütüphane her aileyi varsayılan parametreyle temsil ediyordu.
Topluluk scriptlerinin çoğu aynı ailenin farklı parametreleri. `indicators_variants.py` bu yaygın setleri ekliyor
(62 yapılandırma, 176 durum):

- EMA 5/13/34/89/100, SMA 5/10/100, HMA 9/55
- EMA kesişimi 5/13, 8/21, 13/34, 20/50; SMA kesişimi 10/30, 20/50
- Supertrend (7,3) (10,1) (14,2) (20,5) (22,3); UT Bot (2,10) (1,14) (3,10); PSAR 0,01/0,04
- RSI 3/5/9/21/28; Stoch 5/9/21; MACD (5,35,5) (8,17,9) (19,39,9); CCI 14/50; W%R 21; ADX 7/21
- WaveTrend (9,12) (5,10); QQE (6,3,2,62)
- BB (20,1,5) (20,2,5) (50,2) (10,2); KC (20,1,5) (50,2); Donchian 10/34/100
- LR kanal 50/200, z 100, Ichimoku (20,60,120), fraktal BOS / süpürme k = 3 ve 10

Ayrı koşu: `GCM_LIB=variants` → `results_V/`. Protokolün kalanı aynı: L1/L2/L3, ufuklar, bölmeler, plasebo, ölçütler.
Ayrı bir arama ailesi olarak raporlanır. Ana koşuyla birlikte düşünülürse toplam sınama yükü artar; her koşunun
kendi plasebo eşiği kendi aramasını düzeltir.
