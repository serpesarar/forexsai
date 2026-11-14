# YÖN LAB — ÖN KAYIT (2026-11-14, sonuçlara bakılmadan; değişiklikler yalnız "EK-n" olarak eklenir)

Soru: Fiyat herhangi bir andayken yukarı mı aşağı mı gideceğini önceden söyleyen, şanstan ayırt edilebilir bilgi var mı?

## 1. Veri ve dönemler (kilitli)
- NDX: `data/ndx_1m_v2.parquet` (Dukascopy BID 1m, UTC, 2021-11-01 → 2026-11-04). Yollar BID üzerinden (yarış/etiket
  için spread yok; işlem çevrimi Faz 9'da bid/ask + gerçek spread).
- **KEŞİF** 2021-11-01 → 2024-06-30 (deneme-yanılma yalnız burada) · **DOĞRULAMA** 2024-07-01 → 2025-12-31 (yalnız seçilenler)
  · **KÖR TEST** 2026-01-01 → veri sonu (tek açılış, `results/FINAL_OPENED.json`) · **KÖR TAŞIMA** Pepperstone M5
  US500/US30/US2000/GER40, 2026-01-01 → 2026-11-13, aynı kural sıfır ayar (yalnız ≥M15 tanımlı koşullar taşınabilir).
- Isınma: her dönem başında ilk 30 gün karar yok (göstergeler önceki veriyle ısınır; etiket penceresi dönem sınırını geçemez).

## 2. Karar noktaları
- **Izgara:** her 15 dk (t mod 900 = 0), piyasa açık, t'de kapanmış 1m bar var. Fiyat p_t = son kapanmış 1m BID kapanışı.
- **Olay noktaları:** ızgara noktalarından, ilgili referansa uzaklığı ≤ 0,25 ATR(H1) olanlar (ızgara örneklemesi refrakteri
  sağlar; aynı referansa ardışık yaklaşmalar ≥ 60 dk aralıkla bağımsız sayılır).

## 3. ATR birimi
ATR14 Wilder, KAPANMIŞ barlar: 15 dk ve 1 s ufkunda M15; 4 s, seans ve referans yarışında H1.

## 4. Etiketler (hepsi yalnız t'den SONRA açılan 1m barlarla)
1. **Yön** `dir_h` = sign(p_{t+h} − p_t), h ∈ {15m, 1h, 4h, seans sonu (16:00 ET, yalnız 09:30–15:30 ET)}; büyüklük ATR cinsinden.
2. **Simetrik yarış** `sym_k`: ±k·ATR (k ∈ {0,5; 1; 1,5}) hangisine önce değdi; pencere 15m/1s için ufkun kendisi, k yarışında
   ATR(H1) ve 8 saat. Aynı 1m barda ikisi → belirsiz (çıkarılır, sayısı raporlanır).
3. **Referans yarışı** `race_f`: aile f'nin p_t'nin üstündeki en yakın seviyesi (uzaklık U) ve altındaki en yakını (D),
   0,05 ≤ U, D ≤ 3 ATR(H1); 8 saat içinde hangisine önce değdi (high ≥ üst / low ≤ alt), dakika olarak süre.
4. **Değdikten sonra** `react_f`: olay noktasında seviye L'ye ilk değişten itibaren, L'den ±0,5 ATR: geri dönüş (ret) mi,
   içinden geçiş (kırılım) mı önce (4 saat pencere).

## 5. Referans katalogu (Faz 2 §A; her biri t'de yalnız kapanmış barlarla)
| Aile | Tanım |
|---|---|
| EMA | EMA {9, 21, 50, 100, 200} × {M5, M15, H1, H4}; D1 EMA {20, 50, 200} |
| SMA | SMA {20, 50, 200} × {M15, H1, D1} |
| BB | Bollinger(20, 2σ) üst/alt × {M15, H1, H4} |
| KC | Keltner(EMA20 ± 2·ATR) × {M15, H1} |
| DON | Donchian(20) tepe/dip × {M15, H1, H4, D1} |
| TWAP | (hacim tutarsız → VWAP yerine zaman ağırlıklı) nakit seans (09:30 ET), CFD seansı (18:00 ET), hafta; ±1σ, ±2σ |
| PIV | fraktal pivot k ∈ {2, 3, 5, 8} × {M15, H1, H4}, son 48 teyitli pivot (k bar sonra teyit) |
| CAL | önceki gün O/H/L/C, önceki hafta H/L, önceki ay H/L, gece H/L (gelişen), ORB 15/30/60 H/L, nakit açılış, hafta açılışı |
| RND | yuvarlak sayılar 50 / 100 / 250 / 500 / 1000 |
| FIB | son teyitli H1 (k=5) salınımı: geri çekilme %38,2/50/61,8, uzatma %127,2/161,8 |
| ICHI | Ichimoku H1/H4: tenkan, kijun, senkou A/B (bulut kenarları, kaydırılmış = nedensel) |
| TRD | Parabolic SAR H1, SuperTrend(10, 3) M15/H1 |
| CLU | ±0,3 ATR içinde ≥ 2 farklı aileden seviye → bölge (en yakın üst/alt bölge) |
| HAY | hayalet (aşağıda §6-2) |
Toplam aile = 13 (CLU dahil); her ailede "en yakın üst/alt" alt-üye düzeyinde de raporlanır (ör. EMA200-H1).

## 6. Dört sıfır model
1. **Analitik:** sürüklenmesiz, çözülmüş yarışta P0 = D/(U+D). Sürüklenme düzeltmesi: KEŞİF'ten ölçülen μ/σ² ile
   Brown hareketi formülü (μ ≈ 0 ise aynı). Çözülmeyen yarış oranı ayrıca raporlanır.
2. **Hayalet referans:** gerçek yol aynen; gerçek olayla AYNI (U, D) uzaklığında (0,05 ATR kovası) sahte seviyeler, aynı NY saati
   × oynaklık ondalığı (H1 ATR oranı, KEŞİF eşikleri) × dönem yarısı kovasındaki BAŞKA zamanlarda. P_hay = o kovadaki tüm
   ızgara noktalarının aynı uzaklıktaki yarış sonucu ortalaması. Ret/kırılım hayaleti: aynı kovada, son 15 dk hareketi aynı
   yönde ve aynı büyüklük kovasında (yaklaşma) olan rastgele anlarda ±0,5 ATR yarışı.
3. **Eşlenmiş taban** (durumlar): etiketin NY saati × oynaklık ondalığı × dönem yarısı kovasındaki koşulsuz ortalaması
   (yarış etiketlerinde ek olarak U/(U+D) kovası). FAZLA = ortalama(y − taban) koşul içinde.
4. **Martingal piyasa:** 1m log getirileri 30 dakikalık bloklar hâlinde, aynı NY yarım-saat dilimi ve aynı takvim yarıyılı
   içinde günler arasında karıştırılır (gün-içi oynaklık profili ve oynaklık rejimi korunur, seviye belleği ve koşullu
   bağımlılık yok edilir); bar şekli (o/h/l'nin c'ye göre konumu) korunur. **R = 10** sentetik piyasa. Faz 4–5 taramasının
   TAMAMI (aynı hücreler) her birinde koşulur; **eşik T* = 10 tekrarın en büyük |t|'sinin maksimumu** (≈ q90–95, korumacı).
   Ayrıca Holm ve BH-FDR (q = 0,05) raporlanır.
İstatistik: t = gün-kümeli (günlük toplam / sayı) ortalama farkın t'si; bağımsız n = ≥ 60 dk aralıklı olay sayısı.

## 7. Durum katalogu (Faz 2 §B)
- NOM'un 132 özelliği (sızıntı testli) → KEŞİF'te belirlenen beşte birlik kovalar (Q1…Q5) = 660 hücre.
- Ek ikili durumlar (~90): EMA kesişimleri (9/21 M15-H1, 50/200 H1-D1, son 3 bar içinde), fiyat ↔ EMA tarafı, EMA dizilimi
  8>21>50>200, mum formasyonları M15/H1 (çekiç, ters çekiç, yutan ↑/↓, doji, iç/dış bar, 3 asker/karga, sabah/akşam yıldızı),
  NR4/NR7 (H1, D1), Aroon(25) üst/alt > 70, CCI(20) ±100, Williams %R(14) ±80, StochRSI(14) uçları, Vortex(14) kesişimi,
  TRIX(15) işareti, Ultimate Osc. ±70/30, BB-içinde-Keltner sıkışması, ay sonu/başı, opsiyon vade haftası (3. Cuma haftası),
  çeyrek sonu, tatil öncesi gün, VIX ≥ 18,4, VIX9D/VIX > 1, GEX < 0, DIX üst beşte birlik (Faz 6 günlük katmanı).
- Etiketler: dir_15m, dir_1h, dir_4h, dir_seans, sym_1 (1 s ATR-M15 ±1). → tekli hücre sayısı ≈ (660 + 90) × 5 = 3.750.

## 8. Kombinasyon sınırları ve seçim
- **İkili:** KEŞİF'te tekli |t| en yüksek 40 hücreden (her etiket için ayrı) ikili kesişimler: 40·39/2 × 5 etiket ≤ 3.900.
- **Üçlü:** en iyi 10 ikili × en iyi 20 tekli × 5 etiket ≤ 1.000.
- Tüm denemeler `results/deneme_sayaci.csv`'ye yazılır (aile, düzey, etiket, n, FAZLA, t, sıfır türü).
- **KEŞİF geçişi:** |t| > T* (martingal) ∧ iki kronolojik yarıda aynı işaret ∧ bağımsız n ≥ 100 ∧ |FAZLA| ≥ 1 puan.
- **Simetri / yoğunluk testi:** |t| > T* hücre sayısı martingal piyasalardaki ortalamayı anlamlı (Poisson p < 0,05) geçmiyorsa
  sonuç gürültü sayılır (E26).
- **DOĞRULAMA'ya en çok 30 hücre** (|t| sırasıyla; aynı aileden en çok 5). DOĞRULAMA geçişi: aynı işaret, t ≥ 2,0,
  |FAZLA| ≥ KEŞİF'in %50'si.

## 9. Referans/ret atlası (Faz 4) — hayaletten ayrılma ölçütü
Aile (ve alt-üye) "hayaletten ayrılır" sayılır ⟺ KEŞİF'te |FAZLA_hay| t > T*_ref (aynı atlasın martingal max-|t|'si) ∧ iki
yarıda aynı işaret ∧ bağımsız n ≥ 200. Ayrılanlar Faz 5'e referans koşulu ("en yakın seviye X ailesinden") olarak girer.

## 10. Fiyat dışı katmanlar (Faz 6) — kendi dönemleri (veri kapsamı farklı)
| Katman | KEŞİF | DOĞRULAMA | KÖR | Not |
|---|---|---|---|---|
| DIX/GEX günlük → NDX (nakit seans, gece, kapanış-kapanış) | 2011-05 → 2021-10 | 2021-11 → 2025-12 | 2026 | NDX günlük: yfinance ^NDX |
| Çapraz varlık M5 (US500/US30/US2000 → NAS100) | 2025-06 → 2025-10 | 2025-11 → 2025-12 | 2026 | MT5 |
| Mega-cap/SOX/VIX/DXY/TNX saatlik → NDX | 2024-11 → 2025-06 | 2025-07 → 2025-12 | 2026 | yfinance 1h |
| Tick mikroyapısı (2025) | 2025-01 → 06 | 2025-07 → 12 | YOK | en çok sınıf B; Faz 9'u geçemez (kör yok) |
Her katman aynı dört sıfır mantığıyla (eşlenmiş taban + katman içi permütasyon max-|t|) sınanır.

## 11. Model (Faz 7)
LightGBM ikili (dir_1h ve sym_1), `init_score = logit(eşlenmiş taban)`, girdiler: NOM 132 + DOĞRULAMA'yı geçen hücre bayrakları
+ geçen katmanlar. NOM WF şeması, isotonic. **Zorunlu yön testi:** sym_1'de yalnız bir tarafın çözüldüğü satırlarda, model
P(yukarı) − 0,5 ≥ X puan (X ∈ {3, 5, 8, 10}) olduğunda yön isabeti ve AUC; NOM'un aynı satırlardaki (P_long_TP − P_short_TP)
sonucuyla yan yana. Yön bilgisi iddiası için: isabet KEŞİF-dışı tüm dönemlerde > %50 ve gün-blok bootstrap %95 alt sınırı > %50,
P2 (karıştırılmış etiket, 20 tekrar) p95 üstü.

## 12. İşlem (Faz 9) — geçme ölçütleri (HEPSİ)
Giriş sonraki 1m açılışı + gerçek spread (LONG ask, SHORT bid) + 1 p kayma; çıkış kuralın ufku (zaman) ya da ±1 ATR braketi.
DOĞRULAMA'da EV > 0 ve P(EV>0) ≥ %90 · 2× sürtünmede EV > 0 · hayalet/eşlenmiş plasebonun p95'i üstü · iki kronolojik yarı ≥ 0 ·
KÖR TEST'te EV > 0 · KÖR TAŞIMA'da ≥ 2/4 endekste aynı işaret. Geçen her kural için go_live kartı; LIVE çıkmadıkça GÖLGE.

## 13. DUR koşulları
Faz 4'te hiçbir aile hayaletten / hiçbir durum eşlenmiş tabandan ayrılmıyor VE hiçbir Faz 6 katmanına erişilemiyor → Faz 5'e
geçilmez. KÖR TEST dramatik kötü → raporla, yeniden ayar yok. Ücretli veri / canlı bot-decider-kapı değişikliği → sor.

---
## EK-1 (2026-11-14, Faz 6 katman sonuçlarından ÖNCE; Faz 4–5 sonuçları görülmüştü — katman tanımları onlardan türetilmedi)
**Gerekçe:** yfinance saatlik hisse verisi beklenenden uzun çıktı (2023-12-18 →). §10 tablosu şöyle güncellenir; tanımlar donar.

| Katman | Koşul hücreleri (KEŞİF beşte birlikleri) | Etiketler | KEŞİF / DOĞRULAMA / KÖR | Sıfır (max-|t|) |
|---|---|---|---|---|
| L1 DIX/GEX günlük (d günü değeri d+1 09:30 ET'den itibaren) | gex<0; gex Q1–Q5; dix Q1–Q5; dix_z>1, <−1; gex_z>1, <−1; ΔDIX(5g) Q1–Q5 | NDX nakit seans yönü (açılış→kapanış), gece (kapanış→ertesi açılış), ertesi gün kapanış→kapanış | 2011-05→2021-10 / 2021-11→2025-12 / 2026 | GEX/DIX serisi ≥60 gün dairesel kaydırma, 200 tekrar |
| L2 Saatlik çapraz varlık (NY 10:30…15:30 ET saat kapanışları) | 8 mega-cap genişliği (son saat getirisi > 0 payı), NVDA−QQQ, SOXX−QQQ, IWM−QQQ, SPY−QQQ, mega-cap getiri dağılımı (std), VIX/DXY/TNX son saat değişimi — her biri Q1–Q5 | NDX dir_15m, dir_1h, dir_sess (Dukascopy, ana etiketler) | 2023-12→2024-06 / 2024-07→2025-12 / 2026 | özellik serisi ≥5 gün dairesel kaydırma, 200 tekrar |
| L3 M5 çapraz endeks (MT5; sunucu = NY+7) | US2000/US30/US500 son 15 dk ve 60 dk getirisi − NAS100'ünki (bp) ve 3 endeksin son 15 dk yön uyumu — Q1–Q5 | NDX dir_15m, dir_1h | 2025-06-12→2025-10 / 2025-11→12 / 2026 | aynı kaydırma |
| L4 Tick mikroyapısı (2025) | tick-yönü dengesizliği 5/15/60 dk, kotasyon hızı oranı (15 dk / 20 gün aynı dakika medyanı), spread oranı, mid yol verimliliği 15 dk — Q1–Q5 | NDX dir_15m, dir_1h | 2025-01→06 / 2025-07→12 / YOK | aynı kaydırma |
Geçiş: |t| > katmanın kendi max-|t| q95'i ∧ iki yarı aynı işaret ∧ bağımsız n ≥ 100 (günlükte gün sayısı) → DOĞRULAMA: aynı işaret,
t ≥ 2, etkinin ≥ %50'si. Zorunlu akışlar (ay sonu/başı, vade haftası, çeyrek sonu, tatil öncesi) ana durum taramasında (§7) zaten var.

**Faz 5 yorumu (EK-1b):** KEŞİF geçişindeki T*, geçişle aynı popülasyonda (bağımsız n ≥ 100 hücreler) ölçülen martingal maksimumudur
(tekli 6,42; kombinasyon 5,97). Tüm hücreler üzerinden alınan daha katı değer (kombinasyon 10,89) ile hiçbir kombinasyon geçmez;
iki okuma da raporlanır.

---
## EK-2 (2026-11-14, KÖR TEST açılmadan ÖNCE; DOĞRULAMA ve Faz 7 WF sonuçları görülmüştü)
**İşlem kuralları (Faz 9) — donduruldu:**
- **R-H (hücre birliği):** DOĞRULAMA'yı geçen 24 hücreden herhangi biri aktif → **SHORT**; giriş t'den sonraki 1m açılışı (BID − 1 p
  kayma), çıkış 15 dk sonra (ASK kapanışı + 1 p) — ana çıkış; ek çıkış ±1·ATR(M15) braketi (aynı bar → aleyhte), 15 dk zaman sınırı.
  Tek pozisyon: 15 dk ızgarada pozisyonlar doğal olarak örtüşmez. R birimi = 1·ATR(M15). Spread = NOM koruyucu NY-saati modeli.
- **R-M (model):** Faz 7 dir_15m modeli; |P−0,5| ≥ X → o yönde, 15 dk zaman çıkışı. X yalnız KEŞİF içi WF bloklarında (2023H1–2024H1)
  EV'yi en büyükleyen {0,03; 0,05; 0,08; 0,10} değeri.
- Plasebo: aynı sayıda, aynı NY saati dağılımında rastgele SHORT (R-M için aynı yön dağılımı), 1.000 tekrar → p95.
- **KÖR TAŞIMA** (US500, US30, US2000, GER40): Pepperstone **M1** (2026-07-21/08-05 → 11-13; M5 1m-ölçekli özellikleri doğru üretmez),
  hücreler ve kurallar aynı (beşte birlik eşikleri NDX KEŞİF'ten, ATR birimli olduğundan aynen), taban kendi örneklemi içinde
  NY saati × oynaklık ondalığı. Spread: MT5 bar spread alanı (×0,1) ile NOM modelinin büyüğü.
- KÖR TEST NDX: 2026-01-01 → 2026-11-04 (v2 veri sonu), tek açılış.
