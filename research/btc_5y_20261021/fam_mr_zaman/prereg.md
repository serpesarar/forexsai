# Ön-kayıt — BTC aile "ortalamaya dönüş + zaman" (fam_mr_zaman)

Yazıldı: 2026-10-21, **hiçbir sonuç hesaplanmadan önce** (yalnız veri dosyalarının şeması/ilk satırları görüldü).
Bu dosya sonradan DEĞİŞTİRİLMEZ; gerekirse en alta "Değişiklikler (amendments)" bölümü gerekçeyle eklenir.

## 0. Veri, dönemler, dışlamalar
- Veri: `research/btc_5y_20261021/data/` Binance BTCUSDT spot; 1m (yol çözümü), 15m/1h (göstergeler; `ts` = bar açılışı,
  bar `t` karar anında yalnız `ts + TF ≤ karar` ise kullanılır).
- Dakika ızgarası: 2021-06-01 00:00 → 2026-10-20 23:59 UTC; eksik dakika = NaN (ne giriş ne SL/TP).
- Dışlama: 2023-03-24 11:28–14:00 UTC dakikaları NaN; pozisyon penceresi ([giriş, çıkış]) bu aralıkla veya Binance
  kesintileriyle (2021-08-13 01:59–06:30, 2021-09-29 06:59–09:00) kesişen olaylar ATILIR. Kanal göstergesi penceresi
  (50 bar) bu aralıklarla kesişen olaylar da atılır.
- **Broker kapanış dakikaları** (Pepperstone sunucu 23:59 ve 00:00; Cuma 23:55–00:00): sunucu = UTC+3 (ABD yaz saati) /
  UTC+2 (diğer) → yaz 20:59–21:00 UTC, kış 21:59–22:00 UTC (Cuma 20:55/21:55'ten itibaren). Bu dakikalar işlem/dolum
  için NaN sayılır (giriş sonraki açık dakikaya kayar; SL/TP orada tetiklenemez, sonraki açık dakikada açılış fiyatından
  dolar). Zaman çıkışı hedef dakika kapalıysa ondan önceki son açık dakikanın kapanışında yapılır.
- Dönemler (giriş anına göre): **KEŞİF** 2021-06-01→2023-12-31 · **OOS** 2024-01-11→2025-06-30 · **KÖR** 2025-07-01→2026-10-20.
  2024-01-01→01-10 arası hiçbir dönemde yok. "TAM" = üç dönemin birleşimi.

## 1. İcra ve maliyet (tüm hipotezler)
- Karar bir barın kapanışında → giriş SONRAKİ 1m açılışı (10 dk içinde açık dakika yoksa olay atlanır).
- Binance fiyatı = mid. BUY giriş = open + s/2, BUY çıkış = fiyat − s/2; SELL ayna.
- s: taban **%0,0185 × giriş fiyatı** (gidiş-dönüş); stres **%0,028** (kart ölçütü 4); varyant **sabit 15 $**.
- SL/TP 1m barlarda, giriş dakikası DAHİL; BUY için SL tetik: low − s/2 ≤ SL; TP tetik: high − s/2 ≥ TP. Aynı dakikada
  ikisi → SL. SL dolumu min(SL, open − s/2) (boşluk), TP dolumu TP seviyesi. Zaman çıkışı = ilgili dakikanın kapanışı − s/2.
- Swap: pozisyon broker rollover anını (yaz 21:00 UTC, kış 22:00 UTC; ABD DST'si New York yerel takvimiyle) geçerse her gece
  long −%14/365, short +%2/365 × giriş fiyatı (hafta sonu dahil her gece). "Geçti" = giriş < rollover ≤ çıkış.
- İyimser icra (ölçüt 5): giriş = karar barının kapanışı, s = 0 (swap aynen).
- R = net PnL / başlangıç risk (SL mesafesi). Stopsuz zaman-çıkışlı kurallarda **nominal stop = 1,0 × ATR14(1h)**
  (karar anındaki son 14 kapanmış 1h barın TR ortalaması, basit ortalama); ayrıca net getiri **bp** raporlanır ve
  kart ölçütlerinin bp ile aynı işareti vermesi beklenir (vermezse yazılır).
- Broker 1m, Binance'ten ~%12 daha oynak → **SL < %0,3** olan kurallar "broker verisiyle teyit gerekir" diye bayraklanır.

## 2. Kart ve ek ölçütler (aynı tanım her hücrede)
Kart TAM dönemde hesaplanır (yarılar = olay sırasına göre kronolojik iki yarı):
1. n ≥ 150 çözülmüş olay · 2. ortR > 0 ∧ gün-blok bootstrap (UTC giriş günü, 5.000 tekrar) P(EV>0) ≥ %90 ·
3. iki yarının ortR'si ≥ 0 · 4. s = %0,028'de ortR > 0 · 5. |ortR(iyimser) − ortR(gerçek)| ≤ 0,5·|ortR(gerçek)| ·
6. tek-pozisyon (zaman sırasıyla, önceki çıkıştan önce gelen olay atlanır) ortR > 0.
Ek: (7) plasebo yüzdeliği ≥ %95 (TAM); (8) KÖR ortR > 0; (9) çoklu sınama (aşağıda) düzeltilmiş p ≤ 0,10; (10) OOS ortR > 0.
Ayrıca her hücrede: WR, başabaş WR (= −ort.kayıp/(ort.kazanç − ort.kayıp)), %95 GA (gün-blok), kapısız taban, sabit-15$ varyantı.

**Verdikt şeması:** LIVE-adayı = 1–6 + 7 + 8 + 9 + 10 · SHADOW = kart 1–6'dan en fazla biri düşer **ve** OOS > 0 **ve** KÖR > 0 ·
RED = diğer. Defter sınıfı: LIVE-adayı → B (tek veri seti; broker ileri kasası yok), SHADOW → C, RED → X.

**Çoklu sınama:** Aile birincil hücreleri (aşağıdaki 110 hücre) için KEŞİF'te tek yönlü p (gün-kümeli t, hücrenin yönünde
net ortalama > 0) → **Holm (110)**. Saat-of-gün taraması için ayrıca **max-z** (her gün 24 saatlik getiriler rastgele dairesel
kaydırılır, 48 hücrenin max t'si, 500 tekrar). Literatür hipotezleri (21–23, funding, turn-of-candle; 12 hücre) yayın
dönemi sonrası örneklemde (OOS ∪ KÖR) ayrıca Holm (12) ile değerlendirilir. KEŞİF'te "seçilen" = Holm-düzeltilmiş p ≤ 0,10 ∧
ort > 0. Hiçbir hücre seçilmezse her alt aileden en yüksek t'li hücre "bilgi amaçlı" OOS/KÖR'e taşınır (geçmiş sayılmaz).

## 3. Hipotezler ve ızgaralar (birincil hücreler)

### CH — Kanal-sınır dönüşü (CHREV portu) — 32 hücre
- TF ∈ {15m, 1h}; doğrusal regresyon kanalı n = 50 kapanış; σ = artıkların std'si (ddof 0); zt = 2,0 (bot değeri).
- Tetik **CZ (bot birebir):** z = (kapanış_t − doğru_t)/σ (pencere t−49…t); BUY z ≤ −2, SELL z ≥ +2.
- Tetik **RJ (dokun-reddet mumu):** kanal t−50…t−1 barlarından, t'ye uzatılmış: orta = a·50 + b, alt = orta − 2σ, üst = orta + 2σ.
  BUY: low_t ≤ alt ∧ kapanış_t > alt ∧ (kapanış_t − low_t) ≥ 0,5·(high_t − low_t). SELL ayna.
- Epizod bastırma: koşul t−1'de de doğruysa olay değil.
- Geometri (SL/TP mesafeleri karar anında sabitlenir; ATR = ATR14(TF), basit TR ortalaması, son kapanmış 14 bar):
  **Gbot** TP %1,04 / SL %1,49 (bot USOIL is_pct scope'u birebir), 24 s üst sınır ·
  **Gatr** TP 1,0×ATR / SL 1,5×ATR, 48 bar üst sınır ·
  **Gtime** SL 1,5×ATR, TP yok, 12 bar zaman çıkışı ·
  **Gmid** TP = kanal orta çizgisi (karar anındaki değer; giriş fiyatına uzaklığı < 0,25×ATR ise olay atlanır),
  SL 1,5×ATR, 48 bar üst sınır.
- Hücreler: 2 TF × 2 tetik × 2 yön × 4 geometri = 32.
- Plasebo: her olay için aynı yıl × aynı UTC saatinden rastgele TF bar kapanışı, aynı yön/geometri (Gmid'de TP mesafesi =
  olay setinin medyan (TP mesafesi/ATR)'si sabit), 200 tekrar. Kapısız taban = tüm bar kapanışlarında aynı yön/geometri.
- Tanı (yalnız seçilen/en iyi hücrede, karar vermez): ADX14(TF, Wilder) < 25 ve kanal eğimi ≥ 0 (BUY) / ≤ 0 (SELL)
  2×2 kırılımı; zt = 2,5 sağlamlığı.

### Q — Literatür 21:00–23:00 UTC long (Quantpedia) — 4 hücre (her gün, 7/7)
- **QA-swap:** giriş hedefi 21:00 UTC açılışı (karar 20:59 kapanışı; yazın broker kapalı → 21:01), çıkış 23:00 (22:59 kapanışı), swap dahil.
- **QA-noswap:** QA ile aynı, swap sıfır (literatür maliyetsiz eşdeğeri; yalnız bilgi).
- **QB-postroll:** giriş rollover + 1 dk (yaz 21:01, kış 22:01), çıkış 23:00; swap yok.
- **QC-preexit:** giriş 21:00; rollover (21:00, 23:00] aralığına düşüyorsa (kış 22:00) çıkış rollover'dan önceki son açık
  dakikanın kapanışı (21:58), değilse 23:00.
- Alt raporlar (karar vermez): Pzt–Cum, yaz/kış, yıl bazında, ETF öncesi/sonrası.
- Plasebo: aynı günler, rastgele başlangıç saati (0–23), aynı uzunluk, aynı yön, 200 tekrar.

### HOD — Saat-of-gün — 48 hücre
- Her UTC saati h: giriş h:00 açılışı, çıkış h:59 kapanışı (1 saat), BUY ve SELL. Swap kuralı genel tanımdaki gibi.
- Plasebo: aynı günler × rastgele saat. Max-z (yukarıda). Taban = tüm saatlerin ortalaması.

### DOW — Haftanın günü ve hafta sonu — 16 hücre
- DOW: her UTC günü 00:00 açılışı → 23:59 kapanışı, BUY/SELL × 7 gün = 14 hücre (1 gece swap).
- WE: Cumartesi 00:00 → Pazartesi 00:00 (Pazar 23:59 kapanışı), BUY/SELL = 2 hücre (2 gece swap).
- Plasebo: aynı yıldan rastgele gün(ler), aynı uzunluk. Max-z: haftalık blokta günlük getirilerin dairesel kaydırılması.

### USC — ABD nakit saatleri (ETF sonrası yoğunlaşma) — 2 hücre + betimsel test
- Hafta içi NY 09:30→16:00 (DST'ye göre 13:30–20:00 / 14:30–21:00 UTC), BUY/SELL.
- **H12 betimsel:** hafta içi günlerde Σ|5m log getiri|'nin 13:30–21:00 UTC payı; 2022-01-01→2023-12-31 vs 2024-01-11→2026-10-20.
  GEÇER (yapısal değişim) = fark ≥ 5 puan ∧ gün-blok bootstrap %95 GA'sı > 0.

### FUND — Funding saati (H10, öldürme testi) — 6 hücre
- h ∈ {00, 08, 16} UTC: giriş (h−15 dk) açılışı, çıkış h:14 kapanışı (30 dk), BUY/SELL = 6 hücre.
- Öldürme testi: 24 saatin her biri için aynı 30 dk merkezli pencerenin brüt getirisi; Bonferroni (24) p < 0,05 ∧
  ort |getiri| > 1,85 bp (gidiş-dönüş taban spread) olmadıkça funding etkisi YOK. Ayrıca funding saatleri − diğer saatler farkı.
- Beklenti: geçmez.

### TOC — Turn-of-the-candle (H11, maliyet kalibrasyonu) — 2 hücre
- :00/:15/:30/:45 dakikaları: giriş o dakikanın açılışı, çıkış aynı dakikanın kapanışı, BUY/SELL.
- Beklenti: brüt küçük pozitif olabilir (Shanaev vd. 0,58 bp, 2022'de çürüme), net kesin negatif. Net negatif çıkmazsa
  maliyet modeli hatalı sayılır ve bütün aile durdurulur.

Toplam birincil hücre: 32 + 4 + 48 + 16 + 2 + 6 + 2 = **110**.

## 4. Raporlama
Her hücre × dönem (KEŞİF/OOS/KÖR/TAM) için: n, WR, başabaş WR, ortR, ort bp, %95 GA, P(EV>0), yarılar, stres, 15$,
icra farkı, tek-poz, plasebo yüzdeliği, taban. Hepsi `results/*.csv`; özet not
`research_notes/BTC trader bot kenar araştırması/06_aile_ortalamaya_donus_zaman.md`.
