# Kapı / Filtre / Strateji Kayıt Defteri

**Amaç:** bu projede bugüne kadar denenen HER kapı, filtre ve strateji fikrinin tek yerde kalıcı kaydı:
ne denendi, sonuç ne, neden tuttu / tutmadı, kanıt nerede. Yeni bir kapı veya strateji aranmadan ÖNCE bu dosya
taranır (CLAUDE.md **3. KURAL**); araştırma bitince sonuç buraya eklenir — olumlu da olumsuz da.
`docs/KAPI_ENVANTERI_2026-09-30.md` bu defterin 30 Eylül tarihli anlık görüntüsüdür (bot/backend/decider *durumları*
için oraya bak); bu defter tüm dönemleri ve ajanları kapsar ve güncel tutulur.

Son güncelleme: **2026-10-02**.

## 0. Yeni araştırmaya başlamadan önce (zorunlu sıra)

1. **§2'de ara.** Fikir (veya yakını) var mı? Varsa: ne zaman, hangi veride, neden elendi/ayakta? Aynı sınamayı, aynı veriyle
   tekrarlama; yalnız *yeni veri, yeni tanım veya yeni gerekçe* varsa yeniden aç ve nedenini yaz.
2. **§1'deki kanıt hatalarına karşı kontrol listesi** (sızıntı, saat ekseni, taban, bağımsızlık). Bu projede kanıtların çoğu buralarda çöktü.
3. **§3 meta-derslerine bak**; aday fikrin hangi ilkeye dayandığını ve hangi ilkeyi ihlal ettiğini belirt.
4. **Ön-kayıt:** tanımları, eşikleri ve geçme ölçütlerini sonuçlara bakmadan bir `PROTOCOL.md`'ye yaz; sonuçtan sonra eşik seçme.
5. Zorunlu kıyaslar: kapısız **taban** (aynı dönem × yön × saat), **başabaş**, **bağımsız sonraki dönem**, **birden fazla geometri**,
   **bağımsız karar sayısı** (n değil), **plasebo/kontrol hücresi**. Çıplak WR yasak — beklenti (R) + epoch.
6. Canlıya alma yalnız 2. KURAL (canlıya alma kartı) ile; yeni kapı önce GÖLGE.
7. **Bittiğinde:** bu defterin ilgili bölümüne satır ekle (§2), kanıt hatası bulduysan §1'e ekle, 1. KURAL ile Evrim Paneli'ne oturum notu yaz.

Durum etiketleri: **AKTİF** (canlı, bloklar/uygular) · **GÖLGE** (ölçer, bloklamaz) · **ADAY** (gölgeye bağlanmadı) · **KAPALI** · **ELENDİ**.
Kanıt sınıfı: **A** gerçek para/bağımsız ikinci veri/OOS+plasebo · **B** tek veri seti veya n küçük · **C** tek olay/mantık · **X** çürütüldü/sızıntılı/geri alındı.

---

## 1. Kanıt hataları ve yöntem tuzakları (bu projede yaşanmış — aynı hatayı tekrarlama)

| ID | Tuzak | Bedeli (vaka) | Önlem |
|---|---|---|---|
| E1 | `mt5.copy_rates_from(sym, tf, tarih, n)` tarihten **İLERİYE** bar döndürür | ENTRY_SCORE kapısının ilk kanıtı +2.943$ sızıntılıydı; sızıntısızda aleyhe | `backend/research/_bars_upto.py` |
| E2 | MT5 `time` alanı **broker sunucu saati** (UTC+2/+3), UTC değil; candle_cache'e UTC diye yazılmış | tüm sinyal↔bar analizleri 3 saat kaymış; "momentum filtresi %51→%78" sahte çıktı | ölç + çıkar; teşhis: ABD açılış sıçraması 13:30/14:30 UTC'de mi |
| E3 | candle_cache 1m 2026-02→05 partisi broker saatinde (+3s), 315.730 satır | fakeout dedektör etiketleri kaymış; yalnız NDX çıtayı geçti | onarıldı; yapısal koruma `persist_candles` |
| E4 | candle_cache NDX 1m **2026-02-10→03-08 arası 60 dk ERKEN** (kışta −180 uygulanmış, doğrusu −120) | saat-bazlı her analiz o dönemde yanlış | +60 dk düzelt; DB onarımı backlog'da (bl_60556b3caa) |
| E5 | MT5 export'unda +1230 dk offset (ilk-tick sembolü bayat) | sahte "Cumartesi anomalisi" (aslında Cuma −4.002$) | çoklu sembolden medyan; ölçemezse dur |
| E6 | Tarama döngüsü aynı koşulu 60–75 sn'de bir kaydediyor | POS_TIGHT GDAXI "p≈1e-10" → 8,1× şişme, gerçek p=0,022 | epizod bastırma (`shadow_log.EPIZOD_SESSIZLIK`); n yerine bağımsız karar |
| E7 | Giriş = sinyal barı kapanışı + spread'siz | USOIL breakout %58,8 → gerçek icrada %42,7/−0,147R | giriş = sonraki M1 açılışı + gerçek spread |
| E8 | Backend sonuç çözümlemesi güvenilmez | XAU pulse2 SELL backend %2,9 vs 1m dürüst %61 | 1m replay |
| E9 | Aynı dakikada bölünmüş bacaklar | n şişer | karar bazında say |
| E10 | Demo ML sabitinden gelen panel BUY'ları; meta %77/%79 epoch karışımı | sızıntısız gerçek WR %62,9 ama ort R −0,059 | epoch ayır (`factors.target_type`) |
| E11 | Yerel `config.py` ≠ kutu config'i | envanter yanlış durumu gösterir | `box_dump_bot_settings.py` |
| E12 | Küçük alt kümede %100 (tMP 19/19 → bağımsız dönemde 10/20) | kapı önerisi çöktü | keşfedilen kovayı HİÇ bakılmamış sonraki dönemde doğrula |
| E13 | Sürüklenme: yükselen piyasada kapısız BUY tabanı %92 | "engellenen BUY kazanırdı" bulgusu kapı hakkında bilgi vermez | kapısız taban WR ile kıyasla |
| E14 | WR↑ ≠ para↑ (ATR-TP, BE/kilit, zaman stopu WR'ı artırıp parayı azalttı) | birçok çıkış kuralı elendi | R/$ ile raporla; başabaş WR'a bak |
| E15 | **"Aynı günün ortalamasına göre fark" GELECEĞE BAKAR** (günün kalan yolu ortalamaya girer) | konum/VWAP kapıları sahte iyi, trend kapısı sahte kötü göründü (ngf tur 1) | taban = dönem × yön × UTC saati |
| E16 | **Sol-etiketli çok-zaman-dilimi örnekleme sızıntısı** — 15m bar `label=left` ile örneklenip teyit aynı dilimde aranınca gerilme kararı 15 dk gelecekten geliyor | REFLEX `mom_cont` "+0,29R transfer" tamamen sızıntı; sızıntısız −0,08R | `label/closed="right"` veya teyidi sonraki dilimde ara; "bar bitişi ≤ karar" testi |
| E17 | Çok-koşullu skor kapıları (8 koşul) ve p-değeriyle koşul seçimi dönemler arası taşınmaz | ENTRY_SCORE; 2016-20'de seçilen 6 gün-düzeyi koşul 2021+'da 1/6 | ileri-yürüme: bir çağda seç, diğerinde test et |
| E18 | Kapıyı başka popülasyona taşıma | decider bıçak kapısı (A−) botta ters; kovalama endeksi bot'ta monoton ama portföye taşınmadı | hedef popülasyonda ayrıca ölç |
| E19 | Bir grubun ortalama kaybı ≠ onu engellemenin portföy kazancı | boşalan zamana başka işlemler girer (diğer ajan portföy testi) | veto katkısını portföyde yeniden yürüt |
| E20 | `ndx_buy_lab/data/macro_daily.csv` 2026-07-28'de donmuş; yfinance'tan gelen "bugünkü" günlük değer gün içi değer olabilir | bayat VIX/NDX; 30 Eylül kapanışı 30.556→doğrusu 30.408,50 | tamamlanmış kapanış; `ndx_gate_forge/data/macro_daily_patched.csv` |
| E21 | Backend emtia mumları 09-03'ten beri Yahoo vadelisi (USOIL/XAU), broker değil | bot SL = besleme farkı hatası (ticket 390567007) | broker gerçeği `indicator_snapshots`; `BACKEND_BASIS_TOL_PCT` |
| E22 | Panel sinyali tabanlı scope'lar bar verisinden yeniden üretilemez | bar-replay yanıltır | canlı/gölge işlem kartı |
| E23 | Aynı geçmişe dönerek çok strateji seçmek (aşırı uyum); tek NDX geçmişine 4+ tur bakıldı | bootstrap P değeri seçim yükünü temizlemez | bağımsız piyasa (DAX/QQQ/SPX), yeni dönem, gölge |

---

## 2. Ana kayıt (alan → ID → sonuç)

> NDX = NASDAQ-100 (MT5 `NAS100`). Bot/backend/decider *güncel durumu* için `KAPI_ENVANTERI_2026-09-30.md` §1–6.

### 2.1 Bot giriş kapıları ve yönetimi (canlı + gölge) — ayrıntı envanterde
| ID | Fikir | Durum | Sınıf | Özet / neden |
|---|---|---|---|---|
| B1 | XAU SELL, USOIL SELL yasağı | AKTİF | A/B | USOIL SELL 47 işlem WR %21,3 −21,7R |
| B2 | NDX Cuma yasağı (hafta sonu tutma dahil) | AKTİF | A | Cuma ≥12 UTC n=24 −4.050$, permütasyon p=0,0146; DAX'ta Cuma pozitif → NDX'e özgü |
| B3 | NDX ASIA (22:00–07:00 UTC) yasağı | AKTİF | B | n=36 WR %50 −2.139$ |
| B4 | TREND_GATE (1h EMA50 hizası) | AKTİF | A− | 332 işlem: hizalı %63,3 +9.710$ / karşı %43,4 −13.161$ |
| B5 | POSITION_GATE (SELL ≥0,40 / BUY ≤0,60 dalga konumu) | AKTİF | C/B | replay lift −3…−5, yarılar çelişkili |
| B6 | TQ (Cuma + 15–17 UTC çukuru; yalnız çok-emin) | AKTİF | B | Cuma %46 −3.933$; VIXREG 15–17 UTC %44 −5.483$ |
| B7 | CHREV ADX(30m)≥25 | AKTİF | C | tek vaka −687$ |
| B8 | FAKEOUT_VETO | AKTİF | A(NDX)/C(canlı) | 1.757 satırda yalnız 1 veto |
| B9 | Backend Precision Veto | AKTİF | C/B | premium_zone_buy haklı eğilim; mtf_strong_opposition ayırt etmez |
| B10 | ENTRY_SCORE_GATE (8 koşullu skor<7) | GÖLGE | X | ilk kanıt sızıntılı (E1); sızıntısız 5/6/7/8 eşiklerinin dördü negatif |
| B11 | VIX_REGIME_MICRO (EMA200 karşı-rejim) | GÖLGE | X/C | aynı otopsi, aynı şüphe |
| B12 | Backend advice/veto VIXREG/CHREV | GÖLGE | C | veri bekleniyor |
| B13 | POS_TIGHT (SELL ≥0,60 / BUY ≤0,40) | GÖLGE (geri alındı) | X | sahte çoğaltma (E6) |
| B14 | SQZ ATR14/ATR100 ≥1,0 | GÖLGE | B | plasebo yalnız 1,00'da geçiyor |
| B15 | USOIL_SESSION_GATE (13 UTC öncesi BUY) | GÖLGE | B | kart geçilemedi (bootstrap %81) |
| B16 | SELL_RSI (5m RSI>55) | GÖLGE | C | ölçüm |
| B17 | USOIL_BREAKOUT | GÖLGE | X | 368 olay P(EV>0)=%0,3; −895$/5 gün |
| B18 | S/R-limit giriş kolu (NDX) | KAPALI | B | faz-1 paketi |
| B19 | CONFIRM zorunlu + zone çıtası 4 | AKTİF | C | paketle ölçüldü |
| M1 | Probasyon MOD-E (5 bar bekle + gürültü bandı) | CANLI (kutu) | B+ | iki dönemde pozitif (+3.691$/+7.582$) |
| M2 | REENTRY | CANLI (kutu) | C | plasebo dış örneklemde ❌ (p=0,187) |
| M3 | NDX BUY BE@30dk + kazananı-koştur | AKTİF | B | +29,5R P=%100 (tek dönem) |
| M4 | DAX BUY kazananı-koştur | AKTİF | B | +12,1R P=%98,3 |
| M5 | VIXREG SELL sabır kapısı | KAPALI | B | hafıza↔kutu tutarsız |
| M6 | Koşullu BE (MFE≥0,5R) | AKTİF | C | M9 ile çelişki riski |
| M7 | Zaman stopu 240 dk | KAPALI | X | dış örneklem −1.900$ |
| M8 | TP=2,5×ATR70 | KAPALI | X | WR↑ para↓ (E14) |
| M9 | BE/kilit/zikzak (50+ varyant, 487 işlem) | ELENDİ | X | her eşikte kurtarandan çok kazanan öldürür; USOIL kilidi −8,1R |
| M10 | SHADOW_LOCK (USOIL) | GÖLGE | X | — |
| M11 | USOIL_BUY_TP_RR=1,0 | KAPALI | B | scope 1. yarıda negatif |
| M12 | BACKEND_BASIS_TOL 0,25% | AKTİF | A(olay) | E21 |
| M13 | Reflex engine | GÖLGE — **canlıya alınmasın; kod kilidi 2026-10-02** | X | E16 |

### 2.2 Backend kapıları (`signal_gates.py`) ve decider — ayrıntı envanterde §3–4
K1 VIX_REGIME_GATE (AKTİF, A) · K2 PATTERN_BONUS_GATE (A) · K3 NDX SMC SELL (B) · K4 TQ_GATE (B−) · K5 SESSION_GATES (C) · K6 CALENDAR_GATE (C) ·
K7 XAU trend SELL/GDAXI pulse1 askı (B/C) · K8 ENTRY_SCORE backend (GÖLGE, X) · K9 TREND_ALIGN (GÖLGE) · K10 WAVE_POSITION (GÖLGE, C) ·
K11 FAKEOUT_GATE (GÖLGE) · K12 XAU_SCALP_GATE (GÖLGE) · K13 DEBATE_BIAS_GATE (GÖLGE, X/C) · K14 MiroShark makro bias (fiilen etkisiz?, X/C) ·
D1 decider ALLOW listesi (B) · D2 giriş kalitesi `chz_dir≥2,0 veya vol≥1,5` (GÖLGE, A− decider'da; **bota taşınmaz — botta ters**, GF-14) ·
D3 rejim kapısı VIX≥18,4'te NDX SELL açma (GÖLGE, B) · D4 fakeout köprüsü · D5 takvim yakınlığı.

### 2.3 Ana giriş stratejileri
| Strateji | Durum | Sonuç |
|---|---|---|
| VIXREG (VIX rejimi → NDX yönü, 80/110) | AKTİF | n=211 +3.291$; makro→NDX plasebo p=0, OOS +17pp; *genel girişlerde işlem başına ≈0,01R* (GF-05) |
| CHREV (kanal-sınır dönüşü) | AKTİF | araştırma OOS %44→72–84, canlı n=26 −1.024$; vwap kaynaklı tetikler zehirli (30m kapı: GDAXI BUY %73,7 geçen vs %28,6 eleyen) |
| MOM/SR momentum-continuation | AKTİF | n=21 +381$; yapı-reaksiyon girişleri −EV |
| DAYCOMBO | AKTİF | n=19 +583$ (kendi geometrisi %72–79) |
| XAU günlük swing (Donchian + EMA200, yalnız BUY) | doğrulanmış | %64,5 WR +0,69R tüm WF katları +; XAU intraday kapalı |
| NDX Reflex `mom_cont` | **ELENDİ (sızıntı)** | bkz. GF-13 |
| Pulse1/2/3 ters çevirme | GÖLGE | dürüst WR ~%55–62 (%90 değil), trend-bağımlı |

### 2.4 Eski araştırma hatları (hafıza/rapor kaynaklı)
| ID | Tarih | Fikir | Sonuç | Sınıf |
|---|---|---|---|---|
| OLD-01 | 2026-05-29 | XAU/NDX/USOIL/DAX 1m scalp, %70 WR veya sağlam +EV | **yok** (NDX drift, USOIL whipsaw, XAU/DAX zayıf brüt sinyal spread'e yenik); yüksek-WR pencereleri drift | X |
| OLD-02 | 2026-06-10 | WIN/LOSS gösterge ayırımı (AUC) | endekslerde M15 mean-reversion (filtre WR %25-37→%77-83; sonradan yeniden doğrulanmadı); XAU yalnız BUY, USOIL yalnız SELL | C |
| OLD-03 | 2026-06-10 | Bot sabit TP/SL EV (1m replay) | yalnız NDX BUY +EV; GDAXI kaybeder; USOIL ≈başabaş | A |
| OLD-04 | 2026-06-14 | 5 yeni yön (OOS+friction+plasebo) | GDAXI BUY ve USOIL BUY onaylı; XAU SELL friction'a yenik; NDX SELL/XAU BUY tutuldu | A |
| OLD-05 | 2026-06-15 | 4H S/R + kanal REAKSİYON girişleri | NDX BUY/USOIL BUY hepsi −EV; momentum-continuation tek doğrulanmış giriş | X |
| OLD-06 | 2026-06-15 | SELL rejection + türetilmiş TP/SL | umut verici ama pooled deduped n=22, P=%96,5 — bağlanmadı | C |
| OLD-07 | 2026-06-16/17 | XAU intraday + makro yön + meta stop | M15 bounce/breakout friction'a yenik; makro bağlar 2024-26'da işaret çevirdi; yalnız günlük swing çalışıyor; "yüksek WR" geniş stop gerektiriyor | X |
| OLD-08 | 2026-06-17 | Pulse anti-edge → ters çevirme | pulse1/2 gerçek anti-edge (~%75 SL); ters çevirme dürüst WR %55-62; USOIL hariç | C |
| OLD-09 | 2026-06-25 | Kanal-sınır rejection (CHREV) | model WR %44→72-84 OOS+plasebo; canlıda zayıf | B |
| OLD-10 | 2026-06-27 | Makro→NDX yön (VIX) | VIX-favored yön %69,7 vs %44,7 (+24,9pp, OOS +17, plasebo p=0) → VIXREG; XAU'da makro YOK | A |
| OLD-11 | 2026-07-02 | XAU inverse-shadow 1m dürüst | backend çözümleme güvenilmez; ters -EV ama RR≥0,8 +EV, trend-bağımlı | C |
| OLD-12 | 2026-07-03 | MACD cross scalp | keskinlik/yön/kanal katkısı yok | X |
| OLD-13 | 2026-07-03 | CORTEX analog-kNN (epizodik hafıza) | yön öngörmüyor (Q4−Q1 negatif/sıfır); enjeksiyon kapalı | X |
| OLD-14 | 2026-07-03 | CORTEX confluence 11ET → 24h (supervised ML) | gerçek ama rejim-bağımlı (AUC 0,60 OOS 2023-24; 2022 ayı BAŞARISIZ) | B |
| OLD-15 | 2026-07-04/06 | NDX Reflex V1/V2/PEF, vwap_rev/chan_rev, sweep, orb, trailing | reversion aileleri friction'a yenik; trailing kâr = dolum artefaktı; **mom_cont sızıntı (E16)**; yön tahmini 5/60 dk = taban (ilk %70 de sızıntı) | X |
| OLD-16 | 2026-07-10 | MT5 otopsi → entry_score + seans blokları | entry_score X (B10); seans blokları aynı otopsiden (K5, C) | X/C |
| OLD-17 | 2026-07-16/17 | Fakeout dedektörü 4 sembol | 08-12 yeniden üretimde yalnız **NDX** %70/%70'i geçti | A(NDX) |
| OLD-18 | 2026-07-18/26 | Tartışma-bias çok-ufuklu notlama + ayı yanlılığı düzeltmesi | karne ekseni bozuktu (%51→%42,6 temiz); tersine çevirme bedava değil (NDX %52,9) | X |
| OLD-19 | 2026-07-21 | Trade mgmt BE30+runner, dwell-dodge | NDX BUY BE30+runner +29,5R (M3); dwell-dodge/SELL yönetimi kanıtsız | B |
| OLD-20 | 2026-07-28 | NDX BUY: 82 filtre adayı | **hepsi kör TEST'te çöktü**; sorun geometri (TP80/SL110 11 yılda −0,056R); momentum filtresi gerçek ama yalnız ATR 2,0/1,0 hedefte +0,079R | A |
| OLD-21 | 2026-07-28/29 | NDX SELL büyük kırmızı mum + destek yok | kenar yok, destek filtresi tersine; hacim×TP/SL grid seçim gücü sıfır; **limit-emir varyantı reddedildi (ters seçilim)**; tek ayakta: +1,0 ATR büyük-offset limit (gölge `redcandle`) | X/C |
| OLD-22 | 2026-07-28 | Pulse NDX ATR merdiveni | kök neden sabit TP30/SL50 (başabaş %62,5); `atr_ladder_v1` + 3 gölge bot kapısı | B |
| OLD-23 | 2026-08-11/20 | USOIL breakout; USOIL v3 filtreleri | breakout kenarsız (X); F1 gürültü, F2 zaten canlı | X |
| OLD-24 | 2026-09-02 | Geri çekilme limit, teyit-bekleme girişi, HTF seviye, konum kapısı deneyleri | `analyst_reports/` | — |
| OLD-25 | 2026-09-14 | Decider tam denetim | başabaşta, seçim alfası yok; tek gerçek kapı chz_dir≥2,0/vol≥1,5 (D2) | A− |
| OLD-26 | 2026-09-29 | BE/kilit çıkış kuralları | reddedildi (M9) | X |
| OLD-27 | 2026-09-30 | trade-edge-lab tMP "2/3 uyum 6/6" | ileri dönemde %50/−2.151$ | X |
| OLD-28 | 2026-07-23 | `next_candidates`: premium_zone_buy vetosu, CHREV rejim kapısı | NDX'te veto haklı (−12,8R), USOIL'de para kaybettirir (+17,2R → muaf); CHREV kapısı GDAXI BUY/NDX SELL'de haklı, NDX BUY/USOIL SELL kapalı | B |

### 2.5 NDX Kapı Dökümhanesi (`research/ndx_gate_forge/`, 2026-09-30 → 10-02, bu oturum)
Veri: Dukascopy 2025 (bid/ask), cache 2026 (+60 dk onarımlı), MT5 M1, Eylül `indicator_snapshots`; 10 yıl 1h, 5y 30m, 3,4y 15m; DAX, QQQ/SPX günlük.

| ID | Fikir | Sonuç | Sınıf |
|---|---|---|---|
| GF-01 | 780 hücre tek-özellik taraması (78 özellik × 1/5/15/60 dk × 5 dilim × 2 yön) + dairesel-kaydırma plasebosu | 13 geçen vs plasebo ort. 16,4 → **rastgele girişte durum kapısı yok** | X |
| GF-02 | H1–H16 ön-kayıtlı: kapanış akışı, Avrupa açılışı, boşluk fade/go, premarket, 10:00 dönüşü, ADR tükenmesi, VR pürüzlülük, yuvarlak sayı, emilim, ölü piyasa, VWAP σ-bandı, önceki gün uçları, çarpıklık, ay dönümü, OPEX, VIX vade yapısı | saat-eşlemeli tabanla dört dönemde tutarsız (ilk sürüm E15 yüzünden yanıltıcıydı) | X |
| GF-03 | Gün×saat sürüklenme takvimi (2016-20 → 2021-26 ve ters) | korelasyon 0,0085 / −0,016 | X |
| GF-04 | Gün-düzeyi koşul seçimi p-değeriyle (2016-20'de seç, 2021+'da test) | seçilen 6'nın 1'i doğru (seçilmeyenler 17/26) | X (E17) |
| GF-05 | 34 gün-düzeyi koşul × 10 yıl 2s z (VIX, VIX3M, dünkü getiri, MTD, DXY, HYG, TLT…) | VIXREG yönü gerçek (9/10, 10/11 yıl) ama işlem başına ~0,01R | B |
| GF-06 | K1 Pazartesi SELL yok | 30m 6/6, 15m 4/4, 1m 4/5; son çağa özgü; bot Pazartesi SELL'leri nötr (+6,6 p/34) | B−/C |
| GF-07 | K2 FOMC öncesi 24s SELL yok | ters işaret (+0,22R, 1/5) | X |
| GF-08 | K3 ay sonu dengeleme (son 2 gün, ay-içi ±%4) | 10y 6/8 ve 4/4; 1m 4/5; nadir (yılda ~6 gün); botta tetiklenmedi | C+ |
| GF-09 | K4 pürüzlülük VR>1,2 (+K4b fade koruması) | 1m 5/5 −0,02R ama botta ters, uzun TF'de yok | X |
| GF-10 | K5 stres günü (dün ≤−%1,5 / 5g ≤−%4) SELL yok | 10y iki çağda aynı işaret; bot SELL farkı −17 p (P=0,974, 10 gün); diğer ajan portföyünde dönemsel kararsız (−12,4R/+8,0R) | B− |
| GF-11 | **K5b** stres + fiyat < önceki RTH dibi → SELL yok | genel −0,18R 4/4 P=0,98; bot −12,8 p/41 karar (5 gün); diğer ajan portföy katkısı +6,1R ama 11 gün, anlamsız | B− → **GÖLGE (2026-10-02 bota bağlandı: `k5b_stress_dip`)** |
| GF-12 | K6 NDX 200g+%10 → BUY yok; K6b; coşku aynası (dün ≥+%1,5 → BUY yok) | K6 C+ (vekilde zararlı); K6b ek fayda yok; **coşku aynası 1/5 — korku döner, coşku dönmez** | C+/X |
| GF-13 | REFLEX `mom_cont` | sızıntı (E16): +0,88R → −0,08R | X (A kanıt) |
| GF-14 | T1 vol-normalize gerilme pusulası · T2 decider bıçak kapısını bota taşı · T3 5m hacim patlaması ≥1,5 · T4 kapı etkisi vol tertiline göre · T5 stres günü teyitli SELL · T6 16:55'te SELL kapat · kanal-z ölçek haritası 1–60 dk | T1 X · T2 X (botta ters) · **T3 C+** (3 popülasyonda aynı yön ama 1m/15m'de tutmuyor) · T4 X (teori düzeltildi) · T5 ters → K5b · T6 X · harita X | karışık |
| GF-15 | V1 kovalama endeksi ≥3 → SELL yok · V2 M15 zaten hizalı SELL | bot SELL'lerinde monoton (+28,8 → −38,9 p); genel 4/5; **diğer ajanın portföyünde +0,30R → bota özgü**; "K5b'yi içerir" iddiam yanlıştı | C+ |
| GF-16 | **CAPREV — kapitülasyon alımı** (stres ∧ VIX≥18,4, önceki RTH dibi altı ilk kapanış → BUY) | 10y 1h 9/11 yıl, 30m 6/6, 15m 4/4; saat plasebosu %100 üstü; stressiz ∧ yüksek VIX ≈0; stres ∧ düşük VIX negatif | B+ |
| GF-17 | W1–W7: stres×VIX hücreleri, plasebo, dip tanımı, çıkış eğrisi, geri alım vs anında, açılış vs kırılım | kenar zamanda (ertesi gün 16:00 en iyi; TP80/SL110 öldürür); geri alım yarı etkili; iki şart birlikte gerekli | — |
| GF-18 | CAPREV bağımsız piyasa (kural aynen) | DAX ertesi gün +0,35/+0,47 (P≈0,97); QQQ günlük 10/11 yıl, NDX nakit 11/11; SPX zayıf (6/11) | B+ |
| **GF-19** | **CAPREV-2 (kademe 1 açılış + kademe 2 dip kırılımı)** | 10y 223 olay günü; **GÖLGE scope olarak bota yazıldı 2026-10-02** (`caprev_shadow.py`, `caprev_shadow.jsonl`) — emir yok | **B+ ADAY** |

### 2.6 Diğer ajanların çalışmaları (Codex)
| ID | Klasör | Sonuç |
|---|---|---|
| FG | `ndx_five_gates_20260930` | 432 + 1.620 değerlendirme; beş son aday Eylül'de elendi/ gölge adayı; **beş kanıtlı kapı bulunamadı**. Adaylar: açılış aralığı kırılımı (−0,89R), aşırı-hareketten dönüş SELL (+2,30R/38, seçim çıtası geçmedi), süpürme SELL (+0,23R), varyans oranı rejim (−8,13R, elendi), başarısız-kırılım geri alma BUY (−2,63R). Donmuş beşli portföy Eylül 123 karar +11,27R, %95 CI sıfırı içerir → yalnız gölge hipotezi. İlk tur beş kural (exhaustion_60_none_buy, sweep_60_quiet_buy, failed_break_60_h1_both, efficient_pullback_30_efficiency_both, midpoint_reclaim_30_quiet_sell) düzeltilmiş saatle tekrarlandı: değişmedi. Cache +60 dk hatasını bağımsız buldu (E4) |
| MR | `ndx_mechanism_round2_20260930` | 20 türev tanım (D1–D5 × 2 varyant × 2 çıkış): **hiçbiri doğrulanmadı**. D3 "bekle + gürültü bandı + fiyatı kovalama" en ilginç ama 2025 H1 negatif; D4 stres sonrası teyitli BUY çöktü (iki pozitif özellik birleşince −3,01R). Gözlem: VIXREG'de M15 zaten hizalı SELL 115 karar −5,86 p vs diğerleri +11,03 (bota özgü, GF-15/V2 genel veride tekrarlanmadı). Yeni beşli portföy Eylül 73/+1,97R, Mayıs–Ağustos 286/−8,54R |
| SY | `ndx_synthesis_20261002` | H1 (=K5b) +6,11R (11 gün, anlamsız) · H2 hacim vetosu reddedildi · H3 hacim şokunda bekleme reddedildi · H4 MA200+%10 & 4s aralık üst %20 BUY vetosu 5/5 dönemde zarar · H5 stres sonrası dibi geri alan BUY seyrek · CHASE +0,30R · **CAPREV M1 katı icrada 11 işlem +11,12R ama en iyi 5 gün çıkınca −1,35R; TP80/SL110 +1,07R**. Ders: spread×3'te taban portföy −88,7R → veto pozitif katkısı canlı strateji yapmaz |
| CP | `ndx_caprev_paths_20261002` | CAPREV olay zamanı/kâr taşıma (FRESH_CROSS, CASH_ONLY, FAIL_10, HALF_RUNNER, VIX_COOLING + HALF_RISING/TP1_RISING) — **protokol yazılı, sonuç raporu henüz yok** (bitince buraya işle) |
| PM | `ndx_pattern_motifs` | NAS100 mum-dizisi atlası (tekrar eden motifler, plasebolu) — **rapor taslak** |

---

## 3. Meta-dersler (kalıcı ilkeler)

1. **Rastgele girişte tek-özellikli durum kapısı yok** (GF-01). Kenar ya günlük rejimde (VIX/stres) ya stratejinin kendi yapısında (geometri, zaman çıkışı) aranmalı.
2. **Korku döner, coşku dönmez.** NDX'te işe yarayan kapıların çoğu SELL bloğu; yukarı aşırılık devam ediyor (GF-12). Stres sonrası aşağı aşırılık geri dönüyor (hem NDX hem DAX).
3. **Teyit sinyal ölçeğinde iyi, günlük ölçekte ters.** Probasyon/fakeout teyidi gürültüyü süzer; stres sonrası yeni dipte satmak kapitülasyonu satmaktır (T5, D4, GF-16).
4. **Kovalama cezası ölçekler arası birikir** ama bota özgü kalabilir; tek ölçek ayırt etmez (GF-15).
5. **Braket ≠ zaman.** TP80/SL110 toparlanma sürüklenmesini yakalayamaz; kenar zaman çıkışında (GF-17).
6. **Fiyat-konumu kapıları stratejiye özgü, bilgi-şoku ve günlük rejim kapıları taşınır** (E18, GF-14).
7. **Yüksek WR ≠ kenar** (başabaş WR; E14). Sabit braket martingalde TP80/SL110 hedefe önce erişme olasılığı 110/190≈%57,9.
8. **Teori:** E[PnL]=μ·E[τ], E[τ]≈TP·SL/σ² (sabit sürüklenmeli modelde). *μ∝σ² iddiası kanıtlanmadı — yalnız olası açıklama* (diğer ajanın düzeltmesi).
9. **Sızıntı denetimi önce:** "bar bitişi ≤ karar anı" testi, geleceği değiştirince geçmiş özelliklerin değişmediği prefix testi (E1, E15, E16).
10. **Veto katkısı portföyde ölç** (E19); küçük alt kümeyi (≤20 gün) kanıt sayma.

## 4. Açık iş / sıradaki araştırma yönleri
- **CAPREV-2 gölge verisi** birikiyor (yılda ~22 gün; ileri doğrulama yıllar sürer → 10 yıllık geçmiş birincil kanıt). Gölge çıktısı: `yeni deneme/caprev_shadow.jsonl`.
- **K5b gölge karnesi:** `gate_skipped.jsonl` içinde `shadow:k5b_stress_dip`, sonuç `shadow_followup.jsonl`; ≥30 bağımsız epizod sonrası oku.
- CAPREV: VIX 18,4–25 kovası zayıf (+0,09…+0,26); asıl kenar VIX 25+; düşük-VIX stres negatif. VIX tabanını yükseltme sonradan yapılacaksa yeni veri ister.
- Gece taşıma (kademe 2) boşluk/dolum maliyeti canlıda doğrulanmadı; DAX için gölge henüz Berlin saat dilimiyle kuruldu, NDX'ten sonra değerlendir.
- Kovalama endeksi: yalnız bot SELL'lerinde; gölgeye bağlanmadı (bl_d2b0bbbcea).
- `ndx_caprev_paths`, `ndx_pattern_motifs` sonuçları gelince §2.6'ya işle.
- Cache NDX 1m 2026-02-10→03-08 +60 dk DB onarımı (bl_60556b3caa).

## 5. Rapor dizini
`research/ndx_gate_forge/` (RAPOR.md, NIHAI_RAPOR.md, PROTOCOL*.md, results/) · `research/ndx_five_gates_20260930/RAPOR.md` ·
`research/ndx_mechanism_round2_20260930/RAPOR.md` · `research/ndx_synthesis_20261002/NIHAI_RAPOR.md` · `research/ndx_buy_lab/RAPOR.md` ·
`research/RAPOR_SELL_MUM_DESTEK_2026-07-28.md` · `ndx_reflex_engine/*.md` · `backend/data/evolution/analyst_reports/*.md` ·
`research/next_candidates/FINDINGS.md` · `docs/KAPI_ENVANTERI_2026-09-30.md` · `docs/TRADE_EDGE_LAB_OZET.md` · hafıza notları (`~/.claude/projects/.../memory/`).

## 6. Bu deftere satır ekleme biçimi
`| ID | Tarih | Fikir (kural, parametreler) | Sonuç (sayılar + hangi veri/dönem) | Sınıf |` — ID: `GF-nn` (gate forge), `OLD-nn`, yeni ajan klasörü için 2 harfli ön ek.
Olumsuz sonuç da yazılır (ne denendiği silinirse aynı fikir yeniden denenir). Sonuç değişirse satırı güncelle, silme; neden değiştiğini yaz.
