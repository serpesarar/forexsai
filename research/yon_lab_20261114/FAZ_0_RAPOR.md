# FAZ 0 — Önce oku, tekrarlama, mevcut motorları yeniden kullan (Yön Lab, 2026-11-14)

Kaynak: `docs/KAPI_KAYIT_DEFTERI.md` §0, §1 (E1–E128), §2 (2.1–2.54), §3 (meta-dersler 1–34), CLAUDE.md, NOM raporları.

## 1. Ölü listesi (denenmiş, X — aynı veriyle aynı tanım tekrarlanmaz)
| Araç / fikir | Defter | Neden öldü (kanıt) |
|---|---|---|
| Tüm TradingView göstergelerinin eş zamanlı durum kombinasyonları (133 gösterge, 353 durum, L1–L3) | GC-01/04 | 4 sembol × 1m…1d yön X; çok-hücre plasebo eşiğinin altında |
| Tüm göstergeler tek modelde | GC-02 | kasa AUC +0,0065 (spread mertebesi), C |
| 32.741 Pine scripti birebir + ikili etkileşim taraması | PN-01…07 | NDX 1h/15m/tüm TF X; tespit sınırı +5 p |
| Mum eşleştirme / benzerlik (ham, DTW, MASS, kNN) | ME-02…13 | yön = rastgele komşu |
| Zaman Makinesi Monte Carlo "hedef önce" | TM-01, DTS-03/07 | Brier iklim tabanından kötü; aralık A, yön 0/210 |
| Trend kanalı kenar sekmesi, çok-TF çakışma | TK-01…05 | plasebo altı; yalnız NDX 1h yükselen kanal üst kırılımı C |
| ≥3 dokunuşlu trend çizgisi, kalıcı çizgi | TL-01…06, KC-01…04 | gerçek = hayalet; dokunuş arttıkça tutma azalıyor |
| Geri çekilme limiti (çizgisiz) | Y-01 | limit veren öder; E109 seçim sızıntısı |
| Tepe/destek kuralları, destekte alım | TD-01, KS-01 | 0/89; destekte olmak C3b'yi kötüleştiriyor |
| SMC (OB/FVG/CHoCH/BOS), likidite süpürmesi, MTF süpürme | SM-01…05, MZ-01…04 | süpürme dönüş değil devam |
| HH/HL piyasa yapısı | HL-01/02 | en yüksek t martingalin altında |
| FCR ilk mum, ORB tekli, Orca VAH/VAL/POC × APPD | FC-01…07, OR-01 | X (ORB × VIX hariç) |
| Fitil ret (üst fitil SAT, tüm anatomi) | FR-01…08 | çoğu X; yalnız teyitli çekiç AL B |
| Haber yönü, makro sürpriz, FinBERT | HB-01/02 | yön X; haber oynaklık taşır |
| Koşulsuz saat/seans yönü | SD-01, GF-03 | X; gece sürüklenmesi bilinen olgu |
| MACD kesişimi | 2026-07-03 | keskinlik/yön yok |
| Ters çevirme / rejime göre ters | QS-13 | 0/694 |
| Gamma koşullu son yarım saat momentumu (GEX<0) | GM-01 | C (P 0,80; yayın sonrası zayıf) |
| Günlük geri dönüş (−sign(dün)) | GR-01 | brüt olgu var, net −3 bp |
| Bot ↔ decider uzlaşması, çapraz varlık H12 | OK-01/02 | X |
| NOM: 132 özellikli kalibre P(TP önce) | NOM-02/03 | oynaklık bilgisi B, **yön 0/40**; LONG−SHORT farkı ≥10 p iken isabet 1 s %45, 4 s %50 |

**Ölü bilgi sınıfı (meta-ders §3-21):** *aynı sembolün kendi OHLC'sinden gün-içi yön* — gösterge, seviye, çizgi, formasyon,
yapı, benzerlik ailelerinin hepsi şans tabanını geçmedi; bu sınıfta yalnız **büyüklük** öngörülebilir (DTS-03 A, NOM-02 B).

## 2. Canlı / kanıtlı liste ve ortak mekanizmaları
| Kural | Sınıf | Mekanizma |
|---|---|---|
| C3b NDX RSI2<10 → ilk yükselen kapanış (9/9 yıl, 21/21 endeks) | A−/B | **korku döner** (endeks özgü, XAU/USOIL'de yok) |
| CAPREV (stres ∧ VIX≥18,4 → açılış/dip AL) | B+ | korku döner, rejim kesişimi |
| VIXREG (VIX≥18,4 → NDX BUY lehte; FX'te H12 risk para birimi) | B (6/6) | **günlük korku rejimi**, piyasalar arası taşınıyor |
| ORB uzun × VIX≥18,4 | B (kart 6/6) | korku rejiminde açılış gücü devam |
| KSG (son nakit saati aşağı → gece uzun) | C+ | zorunlu akış / gece primi |
| Ay sonu dengeleme (R1, son seans, E2 ay başı) | B | **zorunlu akış** (kim işlem yapmak zorunda?) |
| FOMC öncesi gece, Tokyo gotobi, Londra ay sonu fiksi | B / B− | zorunlu akış + olay öncesi prim |
| Teyitli çekiç AL (1h) | B | korku fitili döner + teyit |
| NDX 1h yükselen kanal üst kırılımı, tepe kırılımı | C | **coşku dönmez** (yukarı devam) |
| Fakeout Radar NDX (sahte/gerçek kırılım OOS %75/%74; canlı NDX blok kapısı) | B (yalnız NDX çıtayı geçti) | **teyit barı** ölçeğinde gürültü süzme; seviyede yön bilgisinin tek kanıtlı yeri |
Ortak yapı (§3-21): hisse endeksi, uzun yön, korku/stres veya zorunlu akış, zaman çıkışı, saatler–günler tutuş.

## 3. Yeni olan ne (bu çalışmada yeniden açma gerekçesi)
| # | Yeni | Neden aynı sınama değil |
|---|---|---|
| Y1 | **Kumarbazın iflası analitik sıfırı** D/(U+D) + **hayalet referans** + eşlenmiş taban + martingal piyasa — **her referans ailesi** (EMA/SMA 8…200 × TF, VWAP, BB/Keltner/Donchian, pivotlar k=2…8, önceki gün/hafta, gece, ORB, yuvarlak sayılar, Fib, Ichimoku, SAR/SuperTrend) tek tabloda | Önceki seviye çalışmaları tek aileye (çizgi/kanal/S-R) bakıyordu; geometri sıfırı açıkça çıkarılmamıştı (TM-01 yön olasılığını sıfıra karşı değil iklime karşı ölçtü) |
| Y2 | Referansa **değdikten sonra** ret/kırılım, gerçek vs hayalet, her aile | Fakeout Radar yalnız S/R+kanal kırılımı; diğer ailelerde ret/kırılım ölçülmedi |
| Y3 | **Durumların eşlenmiş tabana (saat × oynaklık ondalığı × U/D) göre farkı**, aynı sayıda denemeli martingal max-t eşiğiyle | GC/PN saat-tabanlı isabet kullandı; oynaklık ve geometri eşlenmesi yeni |
| Y4 | **SqueezeMetrics DIX + GEX** günlük, NDX seans/gece/ertesi gün yönü (2011→) | GM-01 yalnız son yarım saat momentumu ve GEX<0; DIX hiç sınanmadı |
| Y5 | **Çapraz varlık öncülüğü**: US500/US30/US2000 M5 (MT5, 2025-06→) ve mega-cap/SOX/VIX/DXY/TNX saatlik (yfinance, 2024-11→) | OK-01 H12 decider kararlarına bakıyordu; NDX'in gün-içi yönünü öncülük ile sorgulamadı |
| Y6 | **Tick mikroyapısı** (2025 tam yıl Dukascopy bid/ask tick: kotasyon hızı, spread, tick-yönü dengesizliği) | reflex Tier-B yalnız olay ailelerinde; hacim alanı yok (yalnız bid/ask) |
| Y7 | **Sıfır-ofsetli model** (LightGBM `init_score` = logit(sıfır)) + **zorunlu yön testi** (NOM'un %45–50'siyle kıyas) | NOM ham sınıf olasılığını öğrendi; geometri beceri sanılabiliyordu |

## 4. Yeniden kullanılan altyapı
- Veri: NOM `data_layer.py` kuralları → **`data/ndx_1m_v2.parquet`** (2021-11 → 2026-11-04; NOM v1 + 2026-01-01→02-07 bu
  oturumda inen günler; NOM'un v1 dosyasına dokunulmadı). Makro/takvim: `research/nom_20261113/data/macro/`.
- Özellikler: `backend/services/nom/features.py` (132 özellik, sızıntı testli) + `bars.py` (HTF `end ≤ t`).
- Etiket mantığı: `backend/services/nom/labels.py` (aynı bar → muhafazakâr).
- Doğrulama: NOM `validation.py` (gün-blok bootstrap, saat-eşli plasebo).
- Kör taşıma: kutudan bu oturumda salt-okunur çekilen **Pepperstone M5 US500/US30/US2000/GER40/NAS100 (2025-06 → 2026-11-14)**
  + M1 (2026-08 →). Saat: sunucu = NY + 7 (E2/E68; dışa aktarmanın ölçtüğü −12.600 sn bayat tick, E5 — kullanılmadı).
- GÇM/Pine motorları: bu çalışmada **yeniden koşulmadı** — onların durum kütüphanesi NDX'te zaten X; durum taraması NOM'un
  132 özelliği + ek gösterge durumlarıyla eşlenmiş-taban yöntemiyle yapılır (Y3 yenilik yöntemde, gösterge listesinde değil).

## 5. Erişim denetimi (Faz 6 ön kontrolü)
| Katman | Erişim | Kapsam | Canlıda karşılık |
|---|---|---|---|
| DIX/GEX | ✅ `squeezemetrics.com/monitor/static/DIX.csv` (ücretsiz) | 2011-05-02 → 2026-11-13 günlük | günlük, ertesi gün kullanılabilir |
| Çapraz varlık M5 | ✅ MT5 kutu | 2025-06 → | ✅ kutu |
| Mega-cap/SOX/VIX saatlik | ✅ yfinance 1h | ≈ son 730 gün | ✅ yfinance |
| Tick mikroyapısı | ✅ yerel 2025 (364 gün, bid/ask, hacim yok) | 2025 | canlıda MT5 tick_recorder (farklı besleme) |
| Opsiyon strike / gamma flip | ❌ ücretsiz güvenilir kaynak yok | — | — (GEX günlük toplamı vekil) |
| Haber (`news_stories`) | kapsam 2026-11-05 → | çok kısa | yalnız ileri not |
| Dukascopy 2018–21 | ❌ sunucu 503 (indirici arka planda sürüyor) | — | — |
