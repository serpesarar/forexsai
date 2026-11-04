# Çapalı / koşullu mum eşleştirme — ön-kayıt (2026-10-13, sonuçlara BAKILMADAN yazıldı)

Amaç: "son mumları geçmişle eşleştir → sonra ne oldu" fikrini genel kayan pencere yerine **yapısal anlarda**
(seans açılışı, gece yolu, ilk yarım saat, olay mumu, önceki gün + boşluk, kapanış baskısı) çapalayarak
NDX'te +15 dk / +1 s / +1 g yönünü öngörüp öngörmediğini sınamak. ME-02/ME-03 (genel pencere, kNN, piramit,
bağlam) zaten X; burada yalnız çapalı tanımlar.

## 0. Mutlak kurallar
- **HOLDOUT:** `ts ≥ 2025-12-01 00:00 UTC` olan hiçbir bar/gün yüklenmez (yükleme anında kesilir); her sorgunun sonuç
  penceresi bu sınırdan önce biter (açık kontrol `t_end < HOLDOUT`). Günlük dosyada `date < 2025-12-01`.
- Yalnız kapanmış barlar; özellik = sorgu anında biten barlar. Komşu yalnız sonucu sorgu anında kapanmışsa
  (`end_j ≤ t_q`). NY saati `zoneinfo America/New_York` (DST doğru). Aynı-gün ortalaması yok (E15), üst-TF sol etiket yok (E16).
- Sorgu günleri = günlük NDX nakit dosyasındaki işlem günleri; erken kapanış günleri (Şükran sonrası Cuma, 24 Aralık,
  3 Temmuz) gün-içi fikirlerde dışarıda.

## 1. Veri (hepsi bar BAŞLANGICI UTC damgalı; 09:30 NY açılış sıçraması her kaynakta doğru dilimde — kontrol edildi)
| TF | Kaynak | Dönem (holdout öncesi) |
|---|---|---|
| 5m | Dukascopy 2025 (1m'den) | 2025-01-02 → 2025-11-28 (≈225 gün; 08-22→27 boşluk) |
| 15m | Pepperstone | 2023-10 → 2025-11 |
| 30m | Pepperstone | 2021-06-29 → 2025-11 |
| 1h | Pepperstone | 2016-05-29 → 2025-11 (1h barı tam saat başlar; 09:00 barı açılışı içerir) |
| 1d | NDX nakit (`macro_daily_patched.csv`) | 2015-01-02 → 2025-11-28 |

`px(t)` = bitişi tam `t` olan barın kapanışı (yoksa NaN → sorgu düşer). Gece yolu örnek noktalarında tolerans 3 saat
(t'den önce biten son bar, en fazla 3 s eski). Günlük ATR14 = önceki 14 nakit günün TR ortalaması (D−1 dahil, D hariç).
Bar ATR14 = önceki 14 barın TR ortalaması (olay barı hariç).

## 2. Ortak motor
- Sorgu q: özellik vektörü x_q, sorgu anı t_q, sonuç y_q = px(t_end) − px(t_ref) (puan), bitiş end_q.
- Kütüphane L(q) = aynı konfigürasyonun `end_j ≤ t_q` olayları. **MIN_LIB = 100** (altında sorgu değerlendirilmez; K=20 ve 50 aynı sorgu kümesi).
- Komşu: L(q) içinde Öklid uzaklığına göre en yakın K (özellikler aynı birimde, standartlaştırma yok).
- Karar: pu = komşularda pay(y > 0) (y = 0 komşu oy vermez); pu > 0,5 → YUKARI, < 0,5 → AŞAĞI, = 0,5 → çekimser.
- Kural tabanlı alt-fikirler (c1, c2, c4, f-kural) komşu kullanmaz; çağrı kuralın kendisi.
- y_q = 0 sorgular dışarıda.

## 3. Ölçütler (her konfig × ufuk)
- **Taban:** kütüphanenin koşulsuz yukarı oranı (aynı çapa / aynı saat, nedensel) → hep-çoğunluk çağrısı; aynı çağrılı sorgularda isabet.
- **Plasebo:** kNN için aynı kütüphaneden aynı sayıda (K) rastgele komşu (iadeli), 40 tekrar; kural için çağrı vektörünün
  çağrılı sorgular arasında karıştırılması, 40 tekrar. "Plaseboyu geçer" = (1 + #{tekrar ≥ model})/41 ≤ 0,05.
- İşaretli hareket: ort(çağrı × y) puan; eşik **> 1,5 puan** (spread).
- Gün-blok bootstrap: fark = model_doğru − taban_doğru; 5 işlem günlük sabit bloklar, B = 2000; P(fark > 0).
- İki kronolojik yarı (çağrılı sorguların zaman medyanı): iki yarıda da fark > 0.
- Bağımsız olay = çağrılı sorguların farklı gün sayısı.
- **ADAY** = hepsi: bağımsız ≥ 200 · isabet − taban ≥ +2,0 puan · plaseboyu geçer · P ≥ 0,975 · iki yarı > 0 ·
  işaretli hareket > 1,5 puan · seçim düzeltmesinden geçer.
- **Seçim düzeltmesi (ailenin TAMAMI):** S = 200 kaydırma. Her kaydırmada her TF'nin gün listesi içinde sonuçlar tam
  gün kaydırılır (aynı saat korunur, dairesel; kaydırma u·n_gün, u ~ U(0,02, 0,98), aynı u tüm TF'lerde). Komşu kümeleri
  ve kural çağrıları sabit kalır; taban kaydırılmış sonuçlardan yeniden hesaplanır. Her konfigürasyonun t = ort(fark)/se
  istatistiği; boş dağılım = ailedeki maks t. Düzeltilmiş p = (1 + #{maks t_null ≥ t_gözlenen})/201 ≤ 0,05.
  Ayrıca: "bootstrap hariç aday ölçütlerini geçen konfig sayısı" (P yerine t ≥ 1,96) gerçek vs boş dağılım. Yedek: Bonferroni.
- Tüm konfigürasyonlar `results/aile.csv`'ye yazılır.

## 4. Fikirler ve varyantlar (sonuçtan sonra eklenen/çıkarılan yok; değişiklik olursa §6'ya yazılır)

**(a) Seans-çapalı gün yolu.** Çapa 09:30 NY; ilk N dk barları; özellik her bar k için (H_k−O₀, L_k−O₀, C_k−O₀)/ölçek,
O₀ = 09:30 barının açılışı. Sorgu t_q = 09:30+N. Ölçek: `atr` (günlük ATR14) | `pct` (O₀/100). K ∈ {20, 50}.
TF/N: 5m N∈{15,30,60,90} (2025, yetersiz beklenir) · 15m N∈{15,30,60,90} · 30m N∈{30,60,90}.
Ufuklar: h15 = px(t_q+15)−px(t_q) (30m'de yok) · h60 · hROS = px(16:00)−px(t_q) · h1d = px(ertesi işlem günü aynı saat)−px(t_q).
GF-02 farkı: H3 (boşluk ≥%0,5 fade/go) ve H5 (|09:30→10:00| ≥ %0,4 dönüşü) eşik-kuralı kapılarıdır, bot geometrisiyle
gün-içi farka göre ölçüldü; burada eşik yok, açılış yolunun ŞEKLİ geçmiş günlerle eşleştirilir ve hedef yöndür.

**(b) Gece yolu analoğu.** Önceki nakit kapanışı C_P = px(P 16:00). Özellik: aşağıdaki saatlerde px − C_P (3 s tolerans):
P 17:00, (D−1 takvim) 20:00, 23:00, D 02:00, 04:00, 06:00, 08:00, 09:00 (+ 09:30, 15m/30m) ve gece yüksek/düşük
(bar başlangıcı ∈ [P 16:00, D 09:30) için; 1h'te [P 16:00, D 09:00)) − C_P; ölçek `atr` | `pct`(C_P/100); K ∈ {20,50}.
Sorgu: 15m/30m 09:30; 1h 09:00. Ufuklar: 15m → o15 (09:30→09:45), o60 (09:30→10:30); 30m → o30 (09:30→10:00), o60;
1h → o60 (09:00→10:00, açılışın ilk 30 dk'sını kapsar), o120 (09:00→11:00).

**(c) Piyasa gün-içi momentumu (Gao, Han, Li & Zhou 2018).** r1 = px(10:00) − px(P 16:00); r12 = px(15:30) − px(15:00);
sonuç r13 = px(16:00) − px(15:30); sorgu 15:30. Kurallar: c1 çağrı = işaret(r1) · c2 = işaret(r1) yalnız işaret(r1)=işaret(r12)
(diğer günler çekimser) · c4 = c2 ∧ önceki gün VIX ≥ 20 (QuantRocket uygulamasının VIX süzgeci). TF: 5m, 15m, 30m.
1h: sonuç "son saat" 15:00→16:00, sorgu 15:00; yalnız c1 ve c4' (c1 ∧ VIX ≥ 20).
Analog c3: özellik = [O(09:30)−C_P, ilk yarım saatin barları için (H−C_P, L−C_P, C−C_P)] / ölçek (1h: [px(09:00)−C_P,
09:00 barının H/L/C − C_P]); ölçek `atr`|`pct`; K ∈ {20, 50}; TF 5m/15m/30m/1h; sonuç r13 (1h: son saat).
GF-02 H1 farkı: H1 gün getirisi ≥ %1 iken güne karşı bot işlemlerini kapı olarak blokluyordu; burada yayımlanmış r1 → r13 kuralı aynen.

**(d) Olay-tetikli eşleştirme.** TF 5m, 15m, 30m. Olay tipleri (olay barı başlangıcı NY [10:00, 15:30) — açılış sıçraması
bar-ATR'sini bozduğu için 09:30–10:00 hariç; açılış GAP tipinde):
E2 aralık ≥ 2×ATR14 · E3 aralık ≥ 3×ATR14 · HI20 kapanış > önceki 20 barın en yükseği · LO20 kapanış < önceki 20 barın en düşüğü ·
GAP |O(09:30) − C_P| ≥ 0,5 × günlük ATR14 (olay barı = 09:30 barı).
Tekilleştirme: tip × TF içinde kronolojik, önceki tutulan olaydan ≥ 60 dk sonra. Eşleşme penceresi = olay barı + sonraki m bar,
m ∈ {1, 3, 5}; özellik her bar (H−O_e, L−O_e, C−O_e)/ATR14_e (O_e olay barı açılışı; GAP'te ek olarak boşluk/günlük ATR);
sorgu t_q = penceredeki son barın bitişi (barlar kesintisiz olmalı). K ∈ {20, 50}. Ufuklar: +15m (5m/15m), +1h, +1d (ertesi gün aynı saat).
Kütüphane = aynı tip/TF/m'nin geçmiş olayları.

**(e) Önceki gün şekli + açılış boşluğu (günlük nakit, 2015–2025).** Sorgu D açılışı. Özellik: son L gün için her gün
(O−C₋₁, H−C₋₁, L−C₋₁, C−C₋₁) (kendi önceki kapanışına göre) + bugünkü boşluk (O_D − C_{D−1}); ölçek `atr` (ATR14) | `pct`;
L ∈ {1, 3}; K ∈ {20, 50}. Ufuklar: OC = C_D − O_D, OO = O_{D+1} − O_D.

**(f) Kendi fikrim — kapanış baskısının dönüşü.** *Mekanizma (sınamadan önce):* kapanışa doğru bilgi taşımayan akışlar
(LETF yeniden dengeleme — günün yönünde, MOC dengesizlikleri, kapanışa endeksli fon akışı) son yarım saatte fiyatı iter;
akış bilgi değilse likidite talebi bitince baskı kısmen geri döner → son yarım saatin getirisi gece/ertesi sabah ters işaretle
devam etmeli. r_last = px(16:00) − px(15:30) (1h'te 15:00→16:00). Kural f1: çağrı = −işaret(r_last), her gün · f2: yalnız
|r_last| ≥ kütüphanedeki |r_last|'in nedensel %67'lik dilimi (≥100 gün). Sorgu 16:00. Ufuklar: pc = 16:00→17:00 (CFD kapanış
sonrası), on = 16:00→ertesi 09:30 (1h: 09:00), om = 16:00→ertesi 10:30 (1h: 10:00). TF 5m, 15m, 30m, 1h.
Analog f3: son saatin barları (15:00→16:00) (H−p₁₅, L−p₁₅, C−p₁₅)/günlük ATR, K ∈ {20, 50}, TF 15m/30m/1h, aynı ufuklar.

## 5. Beklenen yetersizlikler (önceden)
5m konfigürasyonları 2025'in ~225 gününe dayanır; MIN_LIB=100 ile ≤ ~125 sorgu → "yetersiz". GAP olayı yılda ~40–60 → yetersiz olabilir.

## 6. Ön-kayıttan sapmalar
- Tanım/eşik değişikliği YOK. Aile 513 konfigürasyon (§4'ün tam açılımı) tek seferde koşuldu.
- `capali_test.py`'ye yalnız zamanlama için `S_NULL` ortam değişkeni eklendi; S=2'lik bir kuru koşu yapıldı (özet görüldü),
  ardından ön-kayıtlı S=200 ile tam koşu. Hiçbir tanım bu kuru koşudan sonra değişmedi.
- Sonuçlardan SONRA eklenen tanımsal analizler (`capali_ek.py`): MIM'in yayımlanmış regresyon biçimi, (f) için koşullu
  gece yükseliş oranı / ortalama puan, (a) 30m oy kovaları ve (f)'nin yıl/dönem kırılımı. Bunlar aday ailesine GİRMEZ;
  yalnız açıklama/yeni ön-kayıt önerisi içindir.
- Önek sızıntı testi (`capali_sizinti_testi.py`, veri 2025-06-02'de kesilerek yeniden kurulum): 509 konfig, 271.461 olay,
  fark 0.
