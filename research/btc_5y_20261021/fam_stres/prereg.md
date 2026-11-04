# ÖN-KAYIT — BTC "stres dönüşü" ailesi (fam_stres) — 2026-10-21

Bu dosya HİÇBİR sonuç hesaplanmadan yazıldı. Sonradan düzenlenmez; gerekirse en alta "Değişiklikler" eklenir (gerekçeli).

Okunanlar: `research_notes/BTC trader bot kenar araştırması/01_*.md, 02_*.md, 03_*.md`, `docs/KAPI_KAYIT_DEFTERI.md` §0–§1, §2.5 (GF-10…GF-22), §2.9 (GR-01), §3.
Köken: GF-16/18/21/22 (CAPREV), GF-10/11 (K5/K5b stres SELL yasağı), GF-12 (coşku aynası), GR-01 (günlük geri dönüş),
literatür H4/H5 (De Nicola 2021: 1–4 s negatif otokorelasyon). BTC'de daha önce sınanmış kural yok (envanter S6).

## 0. Veri ve ortak tanımlar
- Veri: `research/btc_5y_20261021/data/` Binance BTCUSDT spot 1m (UTC, `ts` = bar açılışı). Üst TF'ler 1m'den/parquet'ten;
  bir bar ancak `ts + periyot ≤ karar anı` ise kapanmış sayılır (E16).
- **Dışlama:** 2023-03-24 11:28–14:00 UTC aralığıyla tutuş aralığı kesişen her işlem düşer (plasebo dahil).
- **Gün** = UTC 00:00–24:00. Günlük getiri r_d = close_d / close_{d−1} − 1 (UTC gün kapanışları).
- **σ20(d)** = r_{d−20..d−1} std'si (ddof=1) — d gününün 00:00'ında bilinir. r1(d) = r_{d−1}; r5(d) = close_{d−1}/close_{d−6} − 1.
- **pdl(d) / pdh(d)** = d−1 UTC gününün en düşük / en yüksek fiyatı.
- **VIX(d)** = `avail_utc ≤ d 00:00 UTC` olan son VIX kapanışı (merge_asof, geriye) → önceki ABD işlem günü; hafta sonu Cuma'nınki.
- **RV rejimi(d)** = σ30(d) (son 30 günlük getiri std'si, d−1'e kadar) > σ30'un önceki 365 günlük medyanı (d−1'e kadar, min 120 gözlem).
  (RV hücreleri bu ısınma nedeniyle ~2021-11'den önce olay üretemez.)
- **Segmentler (sabit):** KEŞİF 2021-06-01→2023-12-31 · OOS 2024-01-11→2025-06-30 · KÖR 2025-07-01→2026-10-20. Segment = giriş anının UTC tarihi.
  2024-01-01→01-10 hiçbir segmentte değil.

## 1. İcra ve maliyet (tüm hücreler)
- Karar = sinyal barının kapanış anı t. Giriş = `ts ≥ t` olan ilk 1m barın `open`'ı; giriş 10 dk'dan geç ise olay düşer.
- Binance fiyatı = mid. BUY giriş = open + S/2, BUY çıkış = fiyat − S/2; SELL tersi.
- Stop (BUY): bid = mid − S/2 ≤ stop → tetik; dolum = min(o barın open − S/2, stop) (boşlukta kötü dolum; giriş barında stop).
  SELL simetrik (ask = mid + S/2 ≥ stop). TP varsa aynı 1m barda TP ve SL → SL.
- Zaman çıkışı T: `ts < T` olan son 1m barın kapanışı ± S/2.
- **Spread S (gidiş-dönüş):** taban %0,0185 × fiyat; stres (kart ölçüt 4) %0,028; ayrıca sabit 15 $ varyantı.
- **Swap:** her sunucu gece yarısı = 17:00 America/New_York (yaz 21:00 UTC, kış 22:00 UTC) anı (giriş, çıkış] içinde kalırsa bir gece.
  Long −%14/365 × giriş fiyatı, short +%2/365 × giriş fiyatı (alacak); hafta sonu dahil her gece.
- **R** = (net PnL) / D, D = başlangıç stop mesafesi (fiyat). Nominal % getiri de raporlanır (E32).
- **İyimser varyant (ölçüt 5):** giriş = sinyal barının kapanışı, spread 0 (swap aynen kalır — yalnız icra farkını ölçmek için).

## 2. Hipotezler ve ızgaralar (tüm hücreler raporlanır)

### G1/G2 — CAPREV-BTC (BUY) — 24 birincil hücre
- Stres(k): r1 ≤ −k·σ20 VEYA r5 ≤ −k·σ20·√5. k ∈ {1,0; 1,5}.
- Korku F: G1 = VIX(d) ≥ 18,4 · G2 = RV rejimi yüksek.
- Tetik penceresi W: **UTC** = d gününün 1h barları, başlangıç 00:00…19:00 (bitiş ≤ 20:00), kapanışı < pdl olan İLK bar ·
  **US** = 30m barlar, başlangıç 13:30…19:30 UTC (bitiş ≤ 20:00), kapanışı < pdl olan İLK bar. Gün başına en fazla 1 olay.
- Stop: giriş × (1 − σ20). TP yok.
- Çıkış X: **D0** = d günü sonu (24:00 UTC) · **H4** = girişten +4 saat · **D1** = d+1 günü sonu.
- Haftanın 7 günü dahil (NDX'teki Pzt–Per kısıtı seans artefaktı sayılır; Pzt–Per alt kümesi yalnız bilgi olarak).
- Hücre sayısı: G1 12, G2 12.
- **Kontrol hücreleri (bilgi, UTC×D0, her k ve iki F için):** stres ∧ ¬F; ¬stres ∧ F; stres (F yok); tetik her gün (stres ve F yok);
  aynı olaylarda SELL (stop giriş×(1+σ20)); literal eşik (r1 ≤ −%1,5 VEYA r5 ≤ −%4) ∧ F (H03 sağlamlık); "her gün 00:00 BUY, stop σ20, D0" tabanı.

### G3 — Düşüş sonrası günlük geri dönüş (BUY) — 6 birincil hücre
- Koşul: r1 ≤ −k·σ20, k ∈ {0 (yani r1 < 0); 1,0; 2,0}. Karar d 00:00 UTC (günlük bar kapanışı) → giriş 00:00 1m open.
- Stop giriş × (1 − 2·σ20) (felaket stopu); TP yok. Çıkış X ∈ {D0 (24 s), D1 (48 s)}.
- Taban: her gün BUY aynı geometri/çıkış.

### G4 — 1 saatlik negatif şok fade (BUY) — 8 birincil hücre; G5 ayna SELL — 8 hücre (asimetri)
- 5m bar kapanışlarında ret60(t) = C(t)/C(t−60 dk) − 1 (t−60 dk'da bar yoksa NaN).
- σ60(t) = ret60'ın önceki 30 günlük (8.640 adet 5m nokta) std'si, t hariç (shift 1), min 4.000 gözlem.
- G4 tetik: ret60 ≤ −z·σ60 → BUY. G5: ret60 ≥ +z·σ60 → SELL. z ∈ {2,5; 3,5}.
- Epizod bastırma: aynı yönde kabul edilmiş son olaydan ≥ 4 saat sonra yeni olay.
- Stop: s × ATR14(1h) (karar anında kapanmış son 14 1h barın TR ortalaması), s ∈ {1; 2}. TP yok. Tutuş N ∈ {1 s; 4 s}.
- Asimetri: ortR(G4) − ortR(G5) aynı hücre için.

### N1 — Coşku aynası (negatif kontrol, SELL)
- N1a günlük: r1 ≥ +k·σ20, k ∈ {0; 1,0; 2,0} → d 00:00 SELL, stop 2σ20, X ∈ {D0, D1} (6 hücre; G3'ün aynası).
- N1b gün-içi (H04): (r1 ≥ +k·σ20 VEYA r5 ≥ +k·σ20·√5), k ∈ {1,0; 1,5}, UTC penceresinde kapanışı > pdh olan ilk 1h bar → SELL,
  stop giriş × (1 + σ20), D0 (2 hücre).
- Beklenti (NDX'ten): geçmemeli.

### N2 — Stres günü SELL yasağı (kapı kontrolü)
- Taban SELL üreteci: her UTC saat başı (karar hh:00 = önceki 1h barın kapanışı) SELL, stop 1×ATR14(1h), TP yok, 4 s zaman çıkışı.
- Hücre: stres(k=1,0) günü ∧ son kapanmış 1h kapanışı < pdl. Ölçü: hücredeki SELL'lerin ortR'si − aynı yıl × UTC saati
  hücre-dışı SELL'lerin ortR'si (eşlenik fark), gün-blok bootstrap. Ayrıca CAPREV olaylarında aynı anda SELL (G1/G2 kontrol hücresi).
- Yasak lehine: fark < 0 ve iki kronolojik yarıda da < 0.

## 3. Seçim ve sınama prosedürü
1. Her birincil hücre tüm segmentlerde hesaplanır ve HEPSİ raporlanır.
2. **Seçim yalnız KEŞİF'te:** her grupta (G1, G2, G3, G4) KEŞİF n ≥ 20 olan hücreler arasından en yüksek KEŞİF ortR'li hücre seçilir
   (hiçbiri pozitif değilse yine en yükseği seçilir ve "keşifte bile negatif" yazılır). G5 için G4'te seçilen hücrenin aynası kullanılır.
3. Seçilen hücre OOS ve KÖR'de dokunulmadan raporlanır. **Onay örneklemi = OOS ∪ KÖR.**
4. **Kart (6 ölçüt) onay örnekleminde** hesaplanır: (1) n ≥ 150; (2) ortR > 0 ∧ gün-blok bootstrap P(EV>0) ≥ %90;
   (3) kronolojik iki yarı ≥ 0; (4) spread %0,028 ile ortR > 0; (5) |iyimser − gerçek| ≤ 0,5·|gerçek|; (6) tek-pozisyon ortR > 0.
   Kart verdikti: n<150 → RED; hepsi → LIVE; aksi SHADOW. Bilgi için tüm-dönem kartı da raporlanır.
5. **Genişletilmiş ölçütler (onay örnekleminde):** (7) P1 plasebo — her işlem için aynı takvim yılı × aynı UTC saat:dakika ×
   aynı segmentte rastgele gün, aynı yön ve aynı çıkış geometrisi (stop o günün σ20/ATR'siyle), 200 tekrar; gerçek ortR plasebo
   ortalamalarının ≥ %95 yüzdeliğinde. (8) KÖR'de ortR > 0. (9) Holm: 4 onay testinin (G1–G4 seçilen hücre, OOS∪KÖR,
   tek yönlü gün-blok bootstrap p = P(ortR ≤ 0)) Holm düzeltmesi α = 0,05. (10) KEŞİF seçim düzeltmesi max-z: her hücrede
   z = (gerçek ortR − plasebo ortalaması)/plasebo std; boş dağılım = her plasebo tekrarında hücreler üzerinden max z; p_sel ≤ 0,10.
   (Hücre plaseboları bağımsız çekildiği için boş max-z muhafazakâr.)
   Ek: tüm birincil hücreler (50) üzerinde onay örnekleminde Holm (seçimsiz, bilgi).
6. **Ek raporlar:** her-gün/kapısız taban, başabaş WR (= |ort. kayıp| / (ort. kazanç + |ort. kayıp|)), sabit 15 $ spread,
   tek-pozisyon setinde en iyi 5 gün hariç toplam, yıl bazında işaret, nominal % ortalama.
7. **Sınıf (defter):** A = kart 6/6 + 7–10 hepsi · B = onay ortR > 0, OOS ve KÖR ikisi de > 0, plasebo ≥ %90 ama kart/Holm'dan
   biri (ör. hacim) düşer · C = onayda yalnız bir segment pozitif veya plasebo < %90 iken pozitif · X = onay ortR ≤ 0 veya plasebo
   medyanının altında.
8. Asimetri (G4−G5): onay örnekleminde fark > 0 ve gün-blok bootstrap P > %95 → "korku döner, coşku dönmez" BTC'de 1–4 s ölçeğinde teyit.
9. Negatif kontroller (N1): onayda ortR ≤ 0 beklenir; pozitif ve P ≥ %90 çıkarsa "BTC asimetrisi NDX'ten farklı" yazılır.

## 4. Değişiklikler (sonradan; gerekçeli)
(boş)

### Değişiklik 1 — 2026-10-21, sonuçlar görüldükten SONRA (yalnız bilgi; verdikti değiştirmez)
Ön-kayıtlı seçim G2'de H4 çıkışlı hücreyi seçti (KEŞİF +0,29) ve onayda tutmadı; oysa G2'nin D0 çıkışlı hücreleri üç segmentte de
pozitif çıktı. Bunun bir plato mu yoksa tek hücre şansı mı olduğunu görmek için **sonradan** (post-hoc, seçim yükü taşıyan) bir
duyarlılık taraması eklendi: `posthoc_g2.py` — RV korkusu, UTC penceresi, D0 çıkışı; k ∈ {0,75; 1,0; 1,25; 1,5; 2,0}; RV eşiği
(σ30 > 365g medyan) yerine σ30 > 365g %60/%40 yüzdelik; 2×2 kontrol (stres×RV) ve G5 aynasının (yukarı şok SELL) BUY-devam karşılığı.
Bu sonuçlar ön-kayıtlı sınama DEĞİLDİR; deftere en fazla C (aday) olarak yazılır ve yeni (ileri) veriyle sınanmadan kanıt sayılmaz.
