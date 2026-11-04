# Claude Decider XAUUSD işlemleri — TP/SL karşı-olgu çalışması (2026-10-15)

> Kapsam: decider'ın XAUUSD için açtığı TÜM işlemler (MT5 demo icraları + journal'daki gölge OPEN kararları), broker 1m BID barları üzerinde sızıntısız yeniden simülasyon ve TP/SL geometri ızgarası.
> Kaynaklar web değil, yereldeki veri ve kod. "Kaynak" bağlantıları dosya yollarıdır. Kod + ara sonuçlar: `/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/` (01…11 numaralı scriptler, `results/`, `data/`).
> Veri seti (bir satır = bir karar/işlem, 817 satır): `/Users/melihcanodacioglu/Desktop/panel/research_notes/Decider XAUUSD TPSL ve giriş kuralları/decider_xau_trades.csv`.
> **Broker 1m önbelleği (yeniden indirmeden kullanılabilir):** `research/decider_xau_tpsl_20261015/data/xau_1m_utc.csv.gz`. Sütunlar `t_utc, open, high, low, close, volume`; UTC'ye düzeltilmiş, MT5 BID barları, 2026-06-17 00:16 → 2026-10-14 06:57 UTC, 111.436 satır. Ham indirmeler (zaman düzeltmesi yok): `data/xau_{1m,5m,15m,1h}_raw.csv`. Düzeltme kuralı `03_build_bars.py` içinde.

## 1. Kaç decider XAUUSD işlemi var? Kaynak, yön, tarih, icra/gölge; orijinal TP/SL mesafeleri, sonuç, R, P&L

### Takeaway
Analize giren 706 karar var: BUY 609 (68'i gerçek MT5 demo icrası, 541'i gölge) ve SELL 97 (hepsi gölge). Dönem 2026-06-30 → 2026-10-14. Orijinal geometride BUY tam başabaşta: WR %60,9, başabaş WR %61,1, EV −0,000R. SELL ise −0,092R. Gerçek demo icraları (68 BUY, 10-05→10-14) WR %66,2 ile net **+29,20$** yaptı (sim +0,103R/işlem). Ancak bu sonuç 9 güne dayanıyor ve %95 aralığı sıfırı kapsıyor.

### Cited Findings
**Veri kaynakları ve doğrulama**
- Kutu (Windows) çevrimdışı. Ajanın son kalp atışı 2026-10-14 06:58 UTC, `remote.py sh` komutu kuyrukta takıldı. Bu yüzden kutudaki `journal.jsonl`, `live_orders.jsonl` ve MT5 deal geçmişi doğrudan okunamadı; Supabase aynaları kullanıldı. — [remote.py health çıktısı](/Users/melihcanodacioglu/Desktop/panel/scripts/remote.py)
- `decider_journal` (Supabase) içinde 2.930 XAUUSD kaydı var. 817'si OPEN: BUY 706 `free` + 6 `evidence` (06-30), SELL 105 `free` (FREE_EXPLORER gölgesi; XAU SELL canlıda HARD_BAN). Geri kalanlar WAIT: 1.764 free, 290 gold_brain, 48 evidence, 11 yön-etiketli WAIT. — [01_dump_journal.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/01_dump_journal.py), [data/journal_xau_raw.jsonl](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/data/journal_xau_raw.jsonl)
- Gerçek icralar `bot_trades` tablosunda, `magic=52890989` (execute_mt5 `DECIDER_MAGIC`). 68 XAUUSD kaydının hepsi BUY. Tarihler 10-05 → 10-14, lot dağılımı 0,01×40 / 0,02×25 / 0,03×3, sonuçlar 45 TP / 23 SL. `open_time` broker saatinde (UTC+3). 3 saat çıkarılınca 68 kaydın 68'i journal OPEN kaydıyla eşleşti (fark −0,97…+0,07 sn). — [02_dump_broker_bars.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/02_dump_broker_bars.py), [claude_decider/execute_mt5.py](/Users/melihcanodacioglu/Desktop/panel/claude_decider/execute_mt5.py)
- **Yinelenen kayıtlar:** 76 OPEN, aynı yönde başka bir OPEN'dan ≤10 sn sonra yazılmış. Hepsi 10-05/06/07 tarihli (canlıya geçişte çift süreç). İlk kayıt tutuldu. Ayrıca 43 karar kullanılamadı, çünkü karar anından sonraki ilk bar 30 dakikadan geç geliyordu: hafta sonu kararları (07-25/26, 10-04), 07-28 15–21 UTC ve 08-27/28 kaydedici boşlukları. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)
- **Fiyat verisi:** broker 1m barları `indicator_snapshots` tablosundan geldi (kutu kaydedicisi). `candle_cache` kullanılmadı, çünkü emtia satırları 09-03'ten beri Yahoo vadelisi. Zaman ekseni satır bazında ölçüldü (`lag = created_at − candle_time`):
  - lag ≤ −60 dk → broker etiketi; 3 saat geri kaydırıldı (28.104 satır).
  - −60 < lag < 0 → güvenilmez etiket; atıldı (360 satır).
  - 07-28 18–21 UTC etiketleri lag −178 ile tutarlı. Bunlar gerçekte 15–18 UTC verisi; kaydırılarak korundu. Gerçek 18–21 UTC verisi kayıp. — [03_build_bars.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/03_build_bars.py)
- **Eksen doğrulaması:** journal'daki karar fiyatı ile düzeltilmiş 1m kapanışı arasındaki medyan |Δ|, iki dönemde de karar−1 dk'da en küçük çıktı: 07-28 öncesi 0,33$, sonrası 0,41$. ±60 dk kaydırmada 5,3–8,8$, ±180 dk'da 7,6–13,3$'a çıkıyor. En oynak saat 13 UTC (ABD verisi/açılış). Ardışık 1m barlarda |open−önceki close| medyanı 0,01$. — [results/leak_checks.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/leak_checks.txt)
- **Simülatör kalibrasyonu:** 68 gerçek icranın 68'inde orijinal TP/SL'nin 1m simülasyon sonucu gerçek MT5 sonucuyla aynı (23 LOSS / 45 WIN). Lot ile ölçeklenen simüle brüt $ (32,88$) broker brüt kârına (32,88$) birebir eşit; komisyon sonrası net 29,20$. — [results/leak_checks.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/leak_checks.txt)
- Journal'ın kendi WIN/LOSS notu ile bizim notumuz gölge kararların %10,7'sinde farklı. Journal 5m barla, spread'siz ve karar fiyatından notluyor; biz 1m bar, spread ve sonraki M1 açılışı kullanıyoruz. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt), [claude_decider/outcomes.py](/Users/melihcanodacioglu/Desktop/panel/claude_decider/outcomes.py)

**Envanter (analiz kümesi n=706)**
- BUY: 609. Aylara göre: 06: 6, 07: 177, 08: 113, 09: 115, 10: 198. Modele göre: claude-opus-5 226, claude-sonnet-5 177, claude-sonnet-5-5 192, opus 14.
- SELL: 97. Aylara göre: 07: 85, 08: 8, 10: 4. Modele göre: opus-5 54, opus 39, sonnet-5-5 4. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)
- Ağustos-başı (gold_brain 07-30..08-09, yalnız WAIT) ve 09-11 → 10-02 (CLI oturumu düştü, sahte WAIT) haftalarında OPEN kararı yok. — [hafıza: decider-cli-auth-silent-death](/Users/melihcanodacioglu/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/decider-cli-auth-silent-death.md)

**Orijinal geometri** (decide.py `DEFAULT_STOP_ATR=(1.0,1.5)`, ATR = decider'ın 5m ATR14'ü; 07-27 öncesi SL 2,5×ATR)

| Dönem | n | TP $ | SL $ | TP / SL (ATR5) | TP / SL (ATR M15) | TP / SL (ATR H1) | spread |
|---|---|---|---|---|---|---|---|
| BUY rr0,67 | 549 | 4,20 | 6,30 | 0,99 / 1,48 | ≈0,58 / 0,90 | ≈0,27 / 0,43 | 0,13$ |
| BUY rr0,40 | 60 | 3,34 | 8,36 | 1,00 / 2,50 | — | — | — |

ATR'ler kapalı barlardan hesaplandı. Medyan ATR5 4,19$, ATR15 7,09$, ATRH1 15,2$. — [claude_decider/decide.py](/Users/melihcanodacioglu/Desktop/panel/claude_decider/decide.py), [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)

**Sonuçlar** (orijinal geometri, 1m, spread dahil, aynı bar = LOSS)

| Küme | n | WR | Başabaş WR | EV (R) | $ / 0,01 lot |
|---|---|---|---|---|---|
| BUY tümü | 609 | %60,9 | %61,1 | −0,000 | +0,019 (toplam +11,5$) |
| BUY gölge rr0,67 | 481 | %59,9 | %60,0 | −0,000 | — |
| BUY rr0,40 | 60 | %63,3 | %71,4 | −0,113 | — |
| BUY icra | 68 | %66,2 | %60,0 | +0,103 | ort. TP +5,30$ / SL −9,09$ (gerçek lotla) |
| SELL tümü | 97 | %58,8 | %66,4 | −0,092 | −1,26 (toplam −122$) |
| SELL rr0,40 | 54 | — | — | −0,203 | — |
| SELL rr0,67 | 43 | — | — | +0,047 | — |

Medyan tutma süresi BUY 14 dk, SELL 21 dk. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)
- Ekim BUY'ları icra edildi mi diye ayrıldı. İcra edilmeyen 130 karar −0,096R (WR %53,8), icra edilen 68 karar +0,103R. İcra edilmeyenlerin yalnız 18'i açık bir decider pozisyonu varken geldi (−0,074R). Kalan 112 kararın (−0,100R) icra edilmeme nedeni `live_orders.jsonl` olmadan doğrulanamadı. Olası nedenler: canlıya geçiş öncesi (10-05 00:20–03:08 UTC), günlük 10 emir tavanı (tüm semboller), spread/ATR>0,15, kill-switch. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)

**Sızıntı kontrolleri**
1. Zaman ekseni ölçülerek düzeltildi (yukarıda).
2. Gölge girişi = journal ts'den (Claude çağrısı bittikten sonra yazılır) sonraki ilk 1m barın açılışı + ölçülen spread (BUY'da ask). Medyan gecikme 0,48 dk. İcra edilen işlemde giriş gerçek dolum fiyatı, yol dolum dakikasından sonraki tam barla başlıyor.
3. ATR yalnız `bar_end ≤ giriş` olan barlardan hesaplandı (örneklemde 0 ihlal).
4. Çıkış yalnız girişten sonraki barlarla belirlendi. Aynı barda TP ve SL → LOSS. BE ve iz-süren stop seviyeleri yalnız önceki barların uç değerleriyle güncellendi.
5. `copy_rates_from` hiç kullanılmadı; barlar kaydedicinin sakladığı veriden geldi.
6. Plasebo girişleri de aynı kurallarla kuruldu.
7. Gerçek icralarda sim = gerçek (68/68).

— [core.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/core.py), [04_build_trades.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/04_build_trades.py), [05_leak_checks.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/05_leak_checks.py)

### Inferences
- XAU BUY'da 07-27 geometri değişikliği (SL 2,5 → 1,5 ATR) doğru yöndeydi: rr0,40 −0,113R iken rr0,67 ≈0R. Ama sistem hâlâ tam başabaşta. 2026-09-14 denetiminin "seçim alfası yok" bulgusuyla uyumlu.
- Ekim icralarının +29$'ı aynı haftanın icra edilmeyen kararlarından (−0,096R) belirgin şekilde iyi. İcra seçimi rastgele değil; olası nedenler gün içi sıra, günlük tavan ve canlıya geçiş saati. Bu yüzden 68 icranın sonucu decider'ın genel XAU BUY kalitesinin tahmini olarak kullanılmamalı. Sıra-bağımlı (tek pozisyon) filtre de EV'yi orijinal geometride +0,003'ten +0,035R'ye çıkarıyor (Q4).
- SELL kayıpları tamamen 07 ayına ve rr0,40 geometrisine yoğunlaşmış. Gerçek fiyat yolu yükselen altına karşı satış.

### Gaps
- Kutu çevrimdışı olduğu için `live_orders.jsonl` (atlanan/reddedilen emir nedenleri) ve kutu journal'ı ile Supabase aynasının satır sayısı karşılaştırılamadı. Ayna son kaydı 10-14 06:51 UTC; kutu sonrasında yazdıysa eksik.
- Broker 1m verisi 10-14 06:57 UTC'de bitiyor. Son birkaç kararın yolu kısa (1 BUY + 1 SELL TIMEOUT).
- 115 erken kayıtta spread yok; ölçülen medyan 0,14$ kullanıldı. Simüle $'a komisyon eklenmedi (gerçekte 68 işlemde −3,68$, ≈0,05$/0,01 lot).
- `gold_brain` (290 WAIT) ve CLI ölümü dönemindeki kararlar OPEN olmadığı için kapsam dışı.

## 2. MFE/MAE profili — kazananlar ve kaybedenler dönmeden önce lehte ne kadar gitti?

### Takeaway
Decider'ın XAU girişleri çok kısa ömürlü bir tepki yakalıyor: kazananlar TP'ye medyan 11 dk'da ulaşıyor. Kaybedenler ise SL'ye gitmeden önce lehte medyan yalnız ~0,33×ATR5 gidiyor. Orijinal geometride SL olan BUY'ların %10,7'si önce +0,5R'yi gördü; +1R görmeleri yapısal olarak imkânsız (TP = 0,667R). SL olan BUY'ların %60'ı SL'den sonraki 240 dk'da orijinal TP'ye ulaşıyor (48 saatte %90). Bu, yükselen altının sürüklenmesi.

### Cited Findings
**Ufuk bazlı MFE/MAE** (giriş barından itibaren, ATR5 birimi, medyan)

| Küme | MFE30 / MAE30 | MFE60 / MAE60 | MFE120 / MAE120 | MFE240 / MAE240 | Seans sonuna kadar MFE / MAE |
|---|---|---|---|---|---|
| BUY WIN (n=371) | 1,59 / 0,65 | 2,09 / 0,80 | 2,87 / 1,24 | 3,54 / 1,92 | 5,24 / 3,81 |
| BUY LOSS (n=237) | 0,41 / 2,02 | 0,51 / 2,69 | 0,71 / 3,78 | 1,24 / 4,43 | 3,47 / 6,91 |
| SELL WIN (n=57) | 1,39 / 0,56 | — | — | 2,89 / 2,58 | — |
| SELL LOSS (n=39) | 0,40 / 2,08 | — | — | 0,80 / 3,93 | — |

$ cinsinden BUY LOSS: MFE30 1,53$ / MAE30 7,85$; BUY WIN: MFE30 6,54$ / MAE30 2,71$. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)
- **Tüm BUY'lar, sonuçtan bağımsız** (medyan MFE / MAE, ATR5; ortalama getiri):
  - 30 dk: 1,05 / 1,05, getiri −0,016
  - 60 dk: 1,50 / 1,48, getiri +0,005
  - 120 dk: 2,08 / 2,14, getiri +0,180
  - 240 dk: 2,84 / 3,08, getiri +0,205
- **Tüm SELL'ler:** 240 dk ortalama getiri −1,468 ATR5. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)

**SL otopsisi**
- **BUY rr0,67 LOSS (n=210):**
  - SL'ye medyan 16 dk; %49'u ilk 15 dk içinde.
  - SL'den önce lehte en az 0,25 ATR5: %59; 0,5: %32; 0,75: %11 (medyan 0,33).
  - SL'den sonraki 240 dk'da girişe dönüş %73, orijinal TP'ye ulaşma %60 (48 saatte %90).
- **BUY rr0,40 LOSS (n=21):** SL'ye medyan 30 dk; SL sonrası 240 dk'da TP %33 (48 saatte %86). — [results/sl_autopsy.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/sl_autopsy.txt)
- **R cinsinden** (orijinal SL = 1R; SL barının lehte kısmı sayılmadı):
  - BUY LOSS (n=237): en az +0,25R %43,5, en az +0,5R %9,7, en az +1R %0 (medyan 0,21R).
  - SELL LOSS (n=39): en az +0,5R %7,7. — [results/describe.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/describe.txt)
- **Kazananlar ne kadar ters gitti:**
  - BUY WIN (n=363): TP'ye medyan 11 dk (%24'ü ≤5 dk). TP'den önce aleyhte medyan 0,43 ATR5; en az 0,5 ATR %45, en az 0,75 ATR %26, en az 1,0 ATR %16.
  - SELL WIN: aleyhte en az 0,75 ATR %31. — [results/sl_autopsy.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/sl_autopsy.txt)

### Inferences
- Kaybedenlerde MFE30 medyanı 0,41 ATR, kazananlarda 1,59 ATR. Ayrışma ilk dakikalarda oluyor: işlem ya hemen tepki veriyor ya hiç vermiyor. Bu yüzden "TP'yi biraz küçültürsem SL'leri kurtarırım" kolu zayıf: SL olanların yalnız ~%10'u +0,5R'yi gördü.
- "SL sonrası TP'ye ulaşma %60–90" stop'un dar olduğuna kanıt DEĞİL. Aynı yükselen dönemde rastgele BUY'lar da bunu yapar (E13: sürüklenme). Q3/Q4'te geniş SL'nin EV'yi düşürdüğü ölçüldü.
- Kazananların %26'sı TP öncesi 0,75 ATR ters gitti. SL'yi 0,75 ATR'ye daraltmak bunları öldürür, buna rağmen bu hücre EV'de biraz daha iyi (Q3). Daraltma, kaybedenleri daha ucuza kapatarak kazandırıyor.

### Gaps
- MFE/MAE 1m bar çözünürlüğünde. Tick verisi olmadığı için bar içi sıra bilinmiyor; konservatif varsayım kullanıldı.
- "Seans sonu" 21:00 UTC (broker günlük kapanışı, ABD yaz saati) varsayıldı. Bu, 11-01 sonrası veride değişecek.

## 3. Karşı-olgu TP/SL ızgarası, zaman çıkışları, BE, iz-süren stop, kısmi TP — EV (R ve $), WR, başabaş, %95 aralık, P(EV>0)

### Takeaway
BUY'da (n=595, 35 gün) 165 ATR hücresinin 23'ü EV>0. Hiçbiri gün-kümeli bootstrap ile P(EV>0)>0,95'e ulaşmıyor. En iyi bölge dar SL (0,75×ATR5) + TP 1,25–1,5×ATR5: +0,072…+0,075R, %95 aralık [−0,05, +0,19], P≈0,87. Geniş SL (≥2,25 ATR) ve geniş TP (≥3 ATR) belirgin negatif. BE, kısmi TP ve iz-süren stop varyantlarının hiçbiri orijinali anlamlı iyileştirmiyor. SELL'de (n=81, 12 gün) hiçbir hücre güvenilir değil.

### Cited Findings
**BUY, ATR ızgarası** (SL 0,5…3,0 × TP 0,5…4,0, ATR5 = kapalı-bar 5m ATR14, R = hücrenin SL'si, n=595)
- Orijinal: +0,003R [−0,064, +0,074], P %53, +0,06$/0,01 lot.
- En iyi hücreler:

| TP / SL (ATR5) | WR | EV (R) | %95 aralık | P(EV>0) | $ / 0,01 lot |
|---|---|---|---|---|---|
| 1,5 / 0,75 | %35,8 | +0,075 | [−0,060, +0,204] | 0,85 | +0,38 |
| 1,25 / 0,75 | %40,2 | +0,072 | [−0,047, +0,194] | 0,87 | +0,36 [−0,06, +0,78] |
| 1,25 / 1,0 | %46,2 | +0,041 | — | 0,79 | — |

- TP ≥3,0 satırları ve SL ≥2,25 sütunları her yerde −0,02…−0,12R. — [results/grid_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/grid_summary.txt), [results/grid_BUY.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/grid_BUY.csv)

**BUY, diğer aileler**
- Sabit-$ ızgarası (99 hücre): 6 hücre >0, en iyisi TP 10$ / SL 2$ +0,062R (WR %17,8, P 0,68).
- Orijinal TP/SL ölçekleri (35 hücre): en iyisi TP×1,25 / SL×0,5 +0,049R (P 0,78).
- Yalnız zaman çıkışı (R = 1 ATR5): 30 dk −0,009, 60 dk +0,008, 120 dk +0,212 [−0,29, +0,70], 240 dk +0,260 [−0,70, +1,23].
- Zaman + SL 1,0 ATR, 240 dk: +0,109.
- Orijinal TP/SL'ye 30/60/120/240 dk tavan: −0,004…+0,008. — [results/grid_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/grid_summary.txt)

**BUY, yol-bağımlı kurallar** (konservatif sıra)
- Orijinal + BE: +0,25 ATR'de +0,015R, +0,5'te +0,014, +0,75'te 0,000.
- TP1,25 / SL0,75 + BE: +0,038…+0,043 (sabit hâlinden kötü).
- İz-süren stop (SL 1,5, TP yok): −0,005…+0,034 (en iyisi d=1,0 ATR, aktivasyon 0).
- Kısmi TP %50 @0,5–0,75 ATR, kalan @1,5/2/3, BE'li ve BE'siz 12 varyantın hepsi: −0,062…−0,006. — [results/path_rules_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/path_rules_summary.txt)

**SELL** (n=81, 12 gün)
- Orijinal −0,054R [−0,215, +0,261].
- ATR ızgarasında en iyi TP1,5 / SL0,75 +0,126 [−0,197, +0,846]; sabit-$ ızgarasında TP 10$ / SL 2$ +0,201 [−0,22, +1,11].
- Yalnız zaman çıkışı 240 dk −2,03R. BE, iz-süren ve kısmi TP varyantlarının hepsi ≤0. — [results/grid_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/grid_summary.txt), [results/path_rules_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/path_rules_summary.txt)

**Yalnız gerçek icralar** (n=68, 9 gün)
- Orijinal +0,103R [−0,055, +0,237], P 0,91.
- TP1,25 / SL0,75 +0,255 [+0,067, +0,524], P 0,998.
- TP4,0 / SL0,5 +0,721 [−0,26, +2,26].
- Orijinal + BE@0,25 ATR +0,074 [+0,035, +0,129]. — [results/grid_BUY_exec.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/grid_BUY_exec.csv), [results/path_rules_BUY_exec.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/path_rules_BUY_exec.csv)

**Yöntem**
- Başabaş WR = SL / (TP+SL); TP1,25 / SL0,75 için %37,5.
- Bootstrap: gün-kümeli, 2.000–3.000 tekrar.
- $ = fiyat farkı × 1 ons (= 0,01 lot), sabit lot.
- 30 veri-boşluklu karar (ilk 240 dk'da >5 dk boşluk) ızgaradan çıkarıldı.

— [grid_lib.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/grid_lib.py)

### Inferences
- BUY'da geometrinin "kârlı yapma" potansiyeli küçük. Yaklaşık +0,07R/işlem, 0,01 lotta ≈ +0,36$/işlem. Bu, sistemin başabaş noktasından yalnız tek kollu bir sapma.
- "Geniş SL ver, sabırlı WR" fikri (07-27 öncesi 2,5 ATR) bu veride de çürüyor: SL 2,25–3,0 sütunu −0,005…−0,11R.
- Zaman-çıkışı "kazancı" (+0,21/+0,26R) decider'a değil altının yükselişine ait (Q4 plasebo). Değişkenliği çok yüksek ([−0,70, +1,23]).
- Yalnız icra kümesindeki parlak hücreler (TP4/SL0,5 +0,72R) 9 günlük, 68 işlemlik örneklemin ürünü. Seçim düzeltmesinden geçemiyor (Q4).

### Gaps
- Izgara ATR5 (decider'ın birimi) üzerinde. M15 ve H1 ATR tabanlı ayrı ızgara koşulmadı; yalnız orijinal mesafelerin M15/H1 karşılıkları raporlandı.
- Limit emirle giriş ve kademeli giriş denenmedi (kapsam dışı).

## 4. Aşırı-uyum kontrolleri: kronolojik yarılar, rastgele-giriş plasebosu, çoklu sınama

### Takeaway
Hiçbir hücre çoklu sınama düzeltmesinden geçmiyor. BUY'da 356 hücre/kural test edildi. Bonferroni eşiği z*=3,63; en iyi hücrenin t'si 0,55, aday TP1,25/SL0,75'in t'si 1,16. White Reality Check p: BUY 0,34, SELL 0,69, BUY-rr0,67 0,13, icra 0,24. Tek ilginç sinyal şu: decider'ın BUY girişleri dar-stop geometride rastgele BUY girişlerinden ~0,16R daha iyi (plasebo yüzdeliği %100). Yine de mutlak EV'nin %95 aralığı sıfırı kapsıyor ve bu fark 1 dakikalık gecikmeye dayanmıyor.

### Cited Findings
**(a) Kronolojik yarılar** (BUY; H1 06-30→09-02, H2 →10-14; her biri ~298 işlem)
- Orijinal: +0,005 / +0,002.
- TP1,25 / SL0,75: +0,029 / +0,116.
- TP1,25 / SL1,0: +0,042 / +0,040.
- İki yarıda da >0 olan hücre: 33/356.
- H1'de seçilen en iyi (zaman 240 dk): +0,090 → H2'de +0,431. H2'de seçilen en iyi (zaman 120 dk): +0,451 → H1'de −0,027.
- Yalnız rr0,67 dönemi (n=541): TP1,25 / SL0,75 H1 +0,141 / H2 +0,069, t=1,73; orijinal +0,070 / −0,034. — [results/robust_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/robust_summary.txt), [results/halves_BUY.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/halves_BUY.csv)
- **SELL:** iki yarıda da >0 olan 5/356 hücre (en iyisi $ TP8/SL2 +0,128 / +0,250). Ancak H1 yalnız 07-24 → 07-28 (5 gün). — [results/robust_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/robust_summary.txt)

**(b) Rastgele-giriş plasebosu** (K=30 set; her decider işlemi için aynı yön + aynı gün-içi dakika + dönem içinden rastgele gün, aynı spread, kapalı-bar ATR)
- BUY plasebo:
  - Hücre ortalaması EV medyanı −0,055R.
  - Orijinal: plasebo −0,054 ± 0,031, decider +0,003 → yüzdelik %93.
  - TP1,25 / SL0,75: plasebo −0,088 ± 0,055, decider +0,072 → %100.
  - TP1,5 / SL0,75: −0,083 vs +0,075 → %100.
  - Zaman çıkışı 120 / 240 dk: plasebo +0,070 / +0,123 → decider yüzdeliği %73 / %70.
  - Plasebo setlerinde ızgara maksimumunun medyanı +0,162 (%90'lık +0,437). Decider'ın sabit-hücre maksimumu (+0,260) bunların yalnız %67'sini geçiyor. — [results/robust_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/robust_summary.txt), [results/placebo_BUY.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/placebo_BUY.csv)
- SELL plasebo: orijinal yüzdelik %37; en iyi hücreler %73–87; ızgara maksimumu plasebo maksimumlarının yalnız %20'sini geçiyor. — [results/placebo_SELL.csv](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/placebo_SELL.csv)

**(c) Çoklu sınama**
- Grup başına M=356 test: 165 ATR + 99 $ + 35 ölçek + 4 zaman + 16 zaman×SL + 4 tavan + 33 yol kuralı. Dört grupta toplam 1.424.
- Bonferroni z*=3,63 (tek yönlü α=0,05/356).
- En iyi t: BUY 0,55, SELL 0,57, BUY-rr0,67 1,19, icra 1,46. Hepsi geçmez.
- White RC (gün-kümeli, merkezlenmiş bootstrap maksimumu): p = 0,344 / 0,690 / 0,125 / 0,238. — [09_robust.py](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/09_robust.py)

**Aday TP1,25 / SL0,75 (BUY) stres testleri**
- Spread ×1,5: +0,036.
- Giriş +1 dk gecikme: +0,013 (orijinal −0,008).
- Journal ATR tabanı (karar anı, oluşan bar dahil): +0,018.
- Aynı anda tek pozisyon (n=527): +0,089, P 0,96, H1 +0,054 / H2 +0,124, +0,415$/0,01 lot. Aynı filtreyle orijinal (n=471): +0,035, P 0,86.
- Pozitif hafta oranı %60. Tek hafta dışarıda bırakılınca EV aralığı [+0,029, +0,129].
- Modele göre: opus-5 +0,057, sonnet-5 +0,143, sonnet-5-5 +0,045. — [results/candidates.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/candidates.txt)

**Önceki defter bulgularıyla tutarlılık**
- IO-08: bot için SL/TP çarpanlarının hepsi −0,06…+0,03.
- IO-13: son-45-gün TP/SL optimizasyonu önceki dönemde çöktü.
- E24: iki yarı + bootstrap seçim yükünü temizlemez; seçim düzeltmeli maksimum istatistik gerekir.

— [docs/KAPI_KAYIT_DEFTERI.md](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- Decider'ın XAU BUY girişleri rastgele BUY'dan biraz daha iyi; fark dar stoplarda belirginleşiyor. Bu, mevcut "XAU BUY seçim değeri +" bulgusuyla (IO-12: OPEN +0,06 vs WAIT-cf −0,14) tutarlı. Ama mutlak EV'yi sıfırdan güvenle ayıracak büyüklükte değil.
- Avantaj ilk 1 dakikada yoğunlaşıyor: +1 dk gecikme dar-stop hücrenin EV'sini 0,072'den 0,013'e indiriyor. Gerçek icra gecikmesi, slipaj ve ATR tanımına bu kadar duyarlı bir kenar canlıya taşınmaz (E7 dersi).
- Zaman çıkışı ve geniş TP'nin görünen kazancı plasebo ile aynı büyüklükte. Bu, dönemin altın sürüklenmesi, decider'a özgü değil (E13).

### Gaps
- Plasebo, sabit TP/SL ve zaman ailelerinde koşuldu; yol kuralları (BE / iz / kısmi) için plasebo koşulmadı.
- Örneklem tek bir düşük oynaklık rejiminde (VIX 15–20; bkz. decider-breakeven-entry-quality). Farklı rejimde geçerlilik bilinmiyor.
- Ön-kayıtlı bir PROTOCOL.md yazılmadı. Izgara ve ölçütler görevde verilenlerdi; aday hücre sonuçlara bakılarak seçildi, bu yüzden "keşif" sınıfında.

## 5. Her iki yarıda da sağlam ve plaseboyu yenen bir geometri var mı?

### Takeaway
**Hayır, sağlam pozitif bir geometri yok.** BUY'da en yakın aday TP 1,25×ATR5 / SL 0,75×ATR5 (RR 1,67, başabaş WR %37,5):
- Tüm örneklem +0,072R / +0,36$ (0,01 lot); iki yarı +0,029 / +0,116; plasebo yüzdeliği %100; tek pozisyonla +0,089R.
- Buna karşın %95 aralığı [−0,047, +0,194], t=1,16 (Bonferroni 3,63), White RC p=0,34.
- 1 dk gecikmede +0,013'e, journal-ATR tabanında +0,018'e düşüyor.

Kanıt sınıfı **C** (yalnız gölge izleme adayı). SELL için hiçbir geometri ayakta değil. Mevcut geometri (TP1,0 / SL1,5) başabaşta: değiştirmek "kârlı yapmaz", en fazla gölgede ölçülecek küçük bir iyileşme adayı verir.

### Cited Findings
- TP1,25 / SL0,75 değerleri (tüm örneklem, yarılar, plasebo, tek pozisyon, LOWO, gecikme, spread ×1,5): bölüm 3–4'teki rakamlar. — [results/robust_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/robust_summary.txt), [results/candidates.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/candidates.txt)
- Orijinal geometri: BUY +0,003R, H1 +0,005 / H2 +0,002, plasebo yüzdeliği %93. SELL −0,054R, plasebo %37. — [results/robust_summary.txt](/Users/melihcanodacioglu/Desktop/panel/research/decider_xau_tpsl_20261015/results/robust_summary.txt)
- Canlıya alma kartının (2. Kural) ölçütleriyle karşılaştırma:
  - Hacim ≥150: BUY'da sağlanıyor.
  - P(EV>0) ≥%90: tek pozisyonla 0,96, tümünde 0,87.
  - İki yarıda da ≥0: sağlanıyor.
  - Spread ×1,5 stresinde pozitif: +0,036.
  - İcra ölçütü (5): +1 dk gecikmede EV'nin %82'si kayboluyor. Kartın "iyimser varsayımla fark ≤ ort. R'nin yarısı" eşiği aşılıyor → **geçmez**. — [CLAUDE.md 2. Kural](/Users/melihcanodacioglu/Desktop/panel/CLAUDE.md)

### Inferences
- Pratik sonuç: decider XAU'yu "kârlı yapacak" bir TP/SL ayarı bu veride yok. Sistemin EV'si girişin ilk dakikalarındaki zayıf tepkiden geliyor; geometri ancak bu tepkiyi biraz daha verimli paraya çevirebiliyor.
- Varsayılanı değiştirmek yerine (seçim yükü, E24) en mantıklı adım şu: TP1,25 / SL0,75'i journal'a ek bir `policy_*` gölge notu olarak eklemek (USOIL `trail_1.0` örneğindeki gibi). Bağımsız ileri dönemde (≥150 yeni işlem) ölçüldükten sonra karar verilir.
- Ekim icralarının görece iyi sonucu (+0,103R), seçilmiş bir alt kümeye ait. Aynı haftanın icra edilmeyen kararları −0,096R. Gölge ölçüm, icrayla aynı kısıtlarla (tek pozisyon, günlük tavan) ayrıca raporlanmalı; yoksa canlı ile gölge karşılaştırılamaz.

### Gaps
- İleri (görülmemiş) dönem yok: tüm veri 10-14'te bitiyor. Aday bundan sonra gelecek kararlarda sınanmalı.
- Farklı ATR tanımları (Wilder, 1m-ATR, M15) ile adayın sağlamlığı denenmedi; journal ATR'sine duyarlılık zaten görüldü.
