# Önceki bulgular envanteri — NDX/DAX/XAU/USOIL'de denenen kenar, kapı, filtre ve stratejiler (BTC'ye taşımak için)

> Kapsam: yalnız depo + hafıza notları (salt okunur tarama, 2026-10-21). Kaynak "URL"leri depo köküne göre göreli
> yollardır (`/Users/melihcanodacioglu/Desktop/panel/`); hafıza notları `~/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/`.
> Defter = `docs/KAPI_KAYIT_DEFTERI.md` (son güncelleme 2026-10-21), Envanter = `docs/KAPI_ENVANTERI_2026-09-30.md`.
> Durum etiketleri: **LIVE** (canlı, emir açar/bloklar) · **SHADOW** (ölçer/loglar, emir yok) · **REJECTED** (elendi/çürütüldü/kapalı).
> Kanıt sınıfı (defter §0): A gerçek para/bağımsız ikinci veri/OOS+plasebo · B tek veri/n küçük · C tek olay/mantık · X çürütüldü/sızıntılı.

---

## S1. Bot (`yeni deneme/`) içinde şu an LIVE / doğrulanmış strateji ve yönetim kuralları — tam tanımlar ve kanıt sayıları

### Takeaway
Botun canlı giriş ailelerinden **hiçbiri** canlı-işlem kartını geçmedi (VIXREG +0,010R, MOMSR −0,014R, CHREV −0,016R; DAYCOMBO/REENTRY pozitif ama n=31/19); kartı 6/6 geçen tek strateji nadir ve uç-gün bağımlı **CAPREV portföyü (NDX+DAX)**. Bar verisinden yeniden üretilebilen ve bağımsız dönemde/piyasada tutan kurallar sadece üç tane: CAPREV (B+/A−), XAU 1h "yeni 20-bar tepesi BUY" (R0B_G1, B+, gölge) ve XAU günlük Golden Donchian (B, gölge). Momentum filtresi gerçek ama yalnız uzak (ATR 2,0/1,0) hedefle ödüyor.

### Cited Findings

**Giriş aileleri (canlı)**
- **MOM/SR momentum-continuation — LIVE (kart: SHADOW).** Scope'lar `ROBUST_SCOPES`: NDX BUY TP 80 / SL 110 puan; GDAXI BUY TP 67 / SL 119 puan; USOIL BUY ve SELL TP %1,04 / SL %1,49 (is_pct); sinyal kaynağı backend pulse1/2/3 oyu (MIN_MODEL_VOTES=1, CONFIRM). USOIL SELL ayrıca `BLOCKED_SYMBOL_DIRECTIONS` ile yasak → fiilen NDX BUY, GDAXI BUY, USOIL BUY. — [yeni deneme/config.py](yeni deneme/config.py)
- Momentum filtresi (backend kapısı, `MOMENTUM_FILTER`): BUY = `M15_stoch_k>70 ∧ M15_dist_ema20_atr>0,8 ∧ H1_sar_dist_atr>0` (USOIL BUY'da M30); USOIL SELL = `M30_dist_ema20_atr<0 ∧ M30_macd_hist<0 ∧ H1_sar_dist_atr<0`. Veri yoksa BLOK. — [backend/routers/bot_router.py](backend/routers/bot_router.py)
- Filtrenin ilk kanıtı (2026-06-12/14): NDX BUY filtresiz TEST %51,4 → filtreli %78,6; GDAXI BUY/USOIL BUY 3/3 bölmede +EV, plasebo p=0,000; XAU SELL sürtünmede öldü (0× +0,32R → 2× −0,06R); NDX SELL marjinal. Uyarı: tek ~45 günlük veri, n küçük (GDAXI BUY son bölme n=9). — [memory/bot-momentum-5dir-2026-06.md](memory/bot-momentum-5dir-2026-06.md)
- Momentum filtresinin 11 yıllık (NDX 1h) doğrulaması: saat-eşlemeli ve sürüklenme çıkarılmış testten geçen tek şey (lift +0,054R) — ama bot geometrisinde (TP80/SL110, RR 0,73 ≈ 0,67 ATR hedef) +0,003R; **ATR 2,0/1,0'da +0,079R, P(EV>0) %96,4, 4/4 yıl**. Bot geometrisi 11 yılda EV −0,0562R [−0,068, −0,044]. 82 filtre adayının hiçbiri kör TEST'i geçmedi (TRAIN +0,15 → TEST −0,24). — [memory/ndx-buy-geometry-not-filters.md](memory/ndx-buy-geometry-not-filters.md); [Defter OLD-20](docs/KAPI_KAYIT_DEFTERI.md)
- MOMSR canlı kart: 182 karar, WR %52,7, ortR −0,014, P %42,1, yarılar −0,148/+0,121, tek-poz −0,047 → SHADOW. — [backend/data/evolution/go_live_cards/momsr_canli.json](backend/data/evolution/go_live_cards/momsr_canli.json)
- HİBRİT giriş: M15 `dist(EMA20)/ATR` > 2,0 (seans çarpanı high 0,7 / quiet 1,4 / EIA 0,55) ise market, değilse 1m S/R bölgesinden limit (ZONE_LOOKBACK 100, ≥4 dokunuş, limit 30 dk). USOIL SELL'in −21,7R kanaması bu S/R-limit yolundan geldi (hiç doğrulanmamış geometri). — [yeni deneme/config.py](yeni deneme/config.py)

- **VIXREG — LIVE (kart: SHADOW).** VIX (önceki gün) ≥ 18,4 → BUY favori, < 18,4 → SELL favori; yalnız NDX; pulse1/pulse2 favori yönde CONFIRM verirse market; TP 80 / SL 110 (kod varsayılanında `VIXREG_SL_ATR_ENABLED=True`, `VIXREG_SL_ATR_MULT=2,0`, SL 60–200 puan aralığı); trend kapısı + konum kapısı + Asya/Cuma yasağı uygulanır. — [yeni deneme/config.py](yeni deneme/config.py); [yeni deneme/forexsai_demo_bot.py](yeni deneme/forexsai_demo_bot.py)
- Araştırma kanıtı: VIX-favori yön %69,7 vs karşı %44,7 (+24,9pp), OOS +17,1pp, plasebo p=0,000 (prediction_logs sinyalleri, 60 dk dedup). VIX tek başına kazan/kaybet ayırmıyor (AUC 0,44); etki YÖNDE. Ertesi-gün açılış→kapanış yönüne uzanmıyor. XAU'da makro yön çalışmıyor. — [memory/macro-ndx-vix-direction.md](memory/macro-ndx-vix-direction.md)
- Genel (sinyalsiz) girişte VIX rejimi yönü 9/10–10/11 yılda doğru ama **işlem başına ≈0,01R** (GF-05). Canlı kart 209 karar ortR +0,010, P %57, 2. yarı −0,035, tek-poz 0 → SHADOW; 206 SELL ortR 0,000. Düşüş aylarında VIXREG BUY (VIX≥18,4) 9 yılın 7'sinde negatif (30m −0,10R, n=975). — [Defter GF-05, CK-01, IO-15](docs/KAPI_KAYIT_DEFTERI.md); [vixreg_canli.json](backend/data/evolution/go_live_cards/vixreg_canli.json)

- **CHREV kanal-sınır dönüşü (mean-reversion) — LIVE (kart: RED).** 30m linreg kanal n=50; BUY z ≤ −2,0 / SELL z ≥ +2,0 VEYA rolling VWAP z ≥ 1,5; kaynak sinyal pulse3; ADX(30m) ≥ 25 ise BLOK; sembol-yön: NDX BUY/SELL 80/110, GDAXI BUY/SELL 67/119, USOIL SELL %1,04/%1,49. — [yeni deneme/channel_filter.py](yeni deneme/channel_filter.py); [yeni deneme/config.py](yeni deneme/config.py)
- Araştırma: 97.155 sinyalde kanal-sınırı WR %44–50 → %72–84; plasebo p95 +17,5pp vs gerçek +25–33pp; 4/4 sembolde +27–29pp; 1m zayıf (+14–15pp), tatlı nokta 5m–1h; ADX<18'de %79,5. **Ama** bu "yakın TP1'e dokunma" WR'ı; sabit uzak TP'de M15 mean-reversion filtresi edge'i TERSİNE çevirdi (NDX BUY %61–69 → %38–50). — [memory/channel-rejection-edge.md](memory/channel-rejection-edge.md); [memory/indicator-discrimination-2026-06.md](memory/indicator-discrimination-2026-06.md)
- Düşen kanalda GDAXI BUY CHREV WR %28,6 (−7,8R) vs yatay/yükselen %73,7 (+2,9R) (`channel_slope_atr`). Canlı: 07-01→08-27 n=26 −1.024$; canlı kart 66 karar ortR −0,016, P %44,8 → RED. — [yeni deneme/channel_filter.py](yeni deneme/channel_filter.py); [chrev_canli.json](backend/data/evolution/go_live_cards/chrev_canli.json); [Envanter §6](docs/KAPI_ENVANTERI_2026-09-30.md)

- **DAYCOMBO — LIVE (kart: RED hacim; bağımsız veride X).** NDX BUY: (1) gün 00:00→13:20/13:25 UTC getirisi > 0, (2) son kapalı 15m kapanış > EMA20 ∧ EMA20 3-bar eğimi yukarı, (3) son kapalı 5m yeşil ∧ gövde/aralık > 0,5, (4) pencere 14:00–19:30 UTC → market BUY, TP 80 / SL 110, BE/trail yok, lot faktörü 0,2. Kanıt: 160 kombodan üç dilimde pozitif kalan tek kombo, n=165/57 gün, WR %63,0 (çıta %58,6), +0,077R. — [yeni deneme/forexsai_demo_bot.py L2197–2302](yeni deneme/forexsai_demo_bot.py)
- Canlı kart 31 işlem +0,281R P %95,5 → RED (hacim). **Görülmemiş 2025 Dukascopy'de kural birebir: 195 işlem −0,030R** → canlı kenar seçim + yükseliş dönemine özgü (CK-03, X). 2026-10-19 zincir: DAYCOMBO+REENTRY 4 SL −8.629$ (fren magic hatası, IO-21). — [daycombo_canli.json](backend/data/evolution/go_live_cards/daycombo_canli.json); [Defter CK-03, IO-21](docs/KAPI_KAYIT_DEFTERI.md)

- **REENTRY — LIVE kutuda (repo varsayılanı shadow; kanıt C).** Ana işlem kapanınca aynı yönde bir kez daha: TP sonrası +5 dk, SL sonrası +1 dk, zincir yok, yalnız NDX, ayrı magic +6. İç örneklem plasebo p=0,000; **dış örneklem plasebo p=0,187 ❌**. Canlı kart 19 işlem +0,446R → RED (hacim). — [yeni deneme/reentry_exec.py](yeni deneme/reentry_exec.py); [reentry_canli.json](backend/data/evolution/go_live_cards/reentry_canli.json)

- **CAPREV kapitülasyon alımı — LIVE (2026-10-09, 1 lot, NDX+DAX; kart 6/6 portföy).** Gün koşulu: önceki işlem günü getirisi ≤ −%1,5 VEYA 5 günlük ≤ −%4 (piyasanın kendi seans kapanışlarından) ∧ önceki takvim günü VIX kapanışı ≥ 18,4; yerel Pzt–Per. Tetik: pencere içindeki (NDX NY 03:00–15:00; DAX Berlin 08:00–16:30) ilk KAPANMIŞ 1h bar, kapanışı < önceki günün seans (RTH) dibi. Giriş: market BUY (≤600 sn gecikme). Stop: giriş × (1 − günlük vol), günlük vol = son 20 seans kapanış getirisinin std'si. **TP yok.** Çıkış: aynı gün seans kapanışı (NDX 16:00 NY, DAX 18:00 Berlin). Aynı anda tek CAPREV pozisyonu. — [yeni deneme/caprev_live.py](yeni deneme/caprev_live.py)
- CAPREV kanıtı: NDX 10y 1h 9/11 yıl, 30m 6/6, 15m 4/4; aynı günlerde rastgele-saat plasebosunun %100 üstü; **stressiz ∧ yüksek VIX ≈0; stres ∧ düşük VIX negatif** (iki şart birlikte gerekli); aynı olayda SELL negatif; DAX'ta kural aynen ertesi gün +0,35/+0,47 (P≈0,97); QQQ günlük 10/11 yıl, NDX nakit 11/11; SPX zayıf 6/11. — [Defter GF-16…GF-18](docs/KAPI_KAYIT_DEFTERI.md); [memory/ndx-gate-forge-2026-09.md](memory/ndx-gate-forge-2026-09.md)
- Kartlar: NDX tek: 107 olay, WR %56,1, ortR +0,240, P %98,6, yarılar +0,021/+0,454, ×1,5 spread +0,236, kapanış-girişi farkı 0,007, çakışma 0 → 5/6, hacim RED. Portföy NDX+DAX: 161 işlem / 134 bağımsız gün, ortR +0,217, P %99,0, yarılar +0,064/+0,367, ×1,5 +0,213, tek-poz +0,160 → **6/6 LIVE**. Uyarılar: toplamın %64–65'i en iyi 5 günden (NDX +25,65R → +8,92R), ilk yarı ≈0, NDX geçmişine 4+ tur bakıldı (E23). — [caprev.json](backend/data/evolution/go_live_cards/caprev.json); [caprev_portfoy.json](backend/data/evolution/go_live_cards/caprev_portfoy.json); [Defter GF-21, GF-22](docs/KAPI_KAYIT_DEFTERI.md)
- CAPREV-2 (kademe 1 açılış + kademe 2) **geri çekildi**: "223 olay günü" iki risk birimini topluyordu; risk birimine bölününce ≈+0,135R/gün. Kenar zamanda: ertesi gün 16:00 en iyi stoplu çıkış; **TP80/SL110 kenarı öldürür**; +1R/−1R çıkış toplamı düşük ama iki yarıda dengeli. VIX 18,4–25 kovası zayıf (+0,09…+0,26), asıl kenar VIX 25+. — [Defter GF-17, GF-19, GF-20, §4](docs/KAPI_KAYIT_DEFTERI.md)

- **XAU 1h "yeni 20-bar tepesi BUY" (MK-04 / R0B_G1) — SHADOW (`xau_shadow.py`, kart 10/10 LIVE ama canlıya alma kullanıcıda).** Sinyal: kapanmış H1 barın high'ı ≥ önceki 20 H1 high → sonraki bar açılışı + $0,12 BUY; SL 1,5×ATR14_H1 (sinyal barı dahil); TP yok; 20 bar zaman çıkışı; segment (>3 s boşluk) sonunda kapanış; tek pozisyon, çıkış barında yeni sinyal açılabilir. — [yeni deneme/xau_shadow.py](yeni deneme/xau_shadow.py)
- Kanıt (Dukascopy H1 2008-01→2026-06): 12.403 olay +0,102R [+0,044, +0,160] vs P1 (aynı yıl + UTC saati rastgele BUY) +0,049; görülmemiş 2008-15 +0,081; yarılar +0,087/+0,117; ×1,5 +0,088; icra farkı 0,025 ✓; tek pozisyon 3,8/hafta +0,079 vs P1 +0,030; Holm ✓; broker kasası +0,145 (n 205). **Ama** max-z seçim düzeltmeli p_sel 0,47; maks. düşüş −59R; tek-pozisyonda en iyi 20 gün toplamın %61,6'sı (hariç +0,031); R≥5 olan %1,9 işlem net toplamın %165'i. — [Defter MK-06, MK-08](docs/KAPI_KAYIT_DEFTERI.md)
- Filtre S2 "önceki UTC günü altın > +%1 ise ATLA": ortR +0,079 → +0,110, maks DD −59 → −49R, p_sel 0,016, 4/4 çağ, ileride broker −0,42 → **A (kural içi filtre)**; gölgede yan yana. Etkinin ~%70'i "kırılım-kovalama cezası". — [Defter MK-13](docs/KAPI_KAYIT_DEFTERI.md)
- Aynı kural bağımsız piyasada (MK-03): XAU+USOIL 15m/30m/1h "yeni 20-mum tepesi BUY, 20 mum" **geçmedi** — USOIL taban altı; "yeni dip SELL" aynası da pozitif → davranış piyasaya özgü (NDX yukarı momentum, XAU iki yönlü trend, USOIL dönüş). — [Defter MK-03](docs/KAPI_KAYIT_DEFTERI.md)

- **XAU günlük "Golden Donchian" — SHADOW (`xau_swing_shadow.py`).** D1 kapanışı ≥ önceki 55 D1 high ∧ kapanış > EMA200(D1) → sonraki D1 açılışında BUY; SL 2×ATR14(D1), TP 4×ATR14; 480 H1 bar (~20 gün) zaman stopu; tek pozisyon; sürtünme $0,40. — [yeni deneme/xau_swing_shadow.py](yeni deneme/xau_swing_shadow.py)
- Kanıt: broker D1 2021-05→2026-04: 31 işlem, WR %64,5, +0,686R, PF 3,04, 5/5 WF katı +, N∈{40..70} × 4 çıkışın hepsi +0,51…+0,94 (plato), $8 sürtünmeye dayanıklı; SELL tarafı −EV. Bağımsız dönem (XS-01, Dukascopy 2008-01→2021-04, kural değişmeden): 54 işlem WR %50, **ortR +0,39 vs her gün BUY tabanı +0,15**, P %98, yarılar +0,41/+0,37; 2014-17 zayıf (−4,4R). 18 yılda 86 işlem → kart hacmi yapısal olarak geçilemez → gölge. H4 varyantı (H4_DONCH30, 2/4 ATR, 30 bar): ~24 işlem/yıl, +0,33R, maxDD 6,6R. — [memory/xauusd-daily-swing-edge.md](memory/xauusd-daily-swing-edge.md); [Defter XS-01](docs/KAPI_KAYIT_DEFTERI.md)

- **USOIL BREAKOUT — SHADOW (X).** Donchian 48 (5m) kırılımı ∧ 5m EMA200 üstü → BUY, TP=SL=1×ATR14(5m); aşım freni 0,5×ATR. Gerçek icrada 368 olay WR %42,7/%43,8, ortR −0,125/−0,147, P(EV>0) %0,3–0,7; iyimser (kapanış girişi, spread 0) −0,005R vs gerçek −0,125R → kartın 5. ölçütünü doğuran vaka; canlı 19 işlem −895$. 30 geometrinin 30'u negatif. — [usoil_breakout.json](backend/data/evolution/go_live_cards/usoil_breakout.json); [memory/usoil-breakout-no-edge.md](memory/usoil-breakout-no-edge.md)

**Giriş sonrası yönetim / icra**
- **Probasyon MOD-E — LIVE kutuda (NDX).** Sinyalde emir gönderme; 5×1m bar bekle; bu sürede aleyhe hareket > 1,28×ATR14(1m)×√5 ise iptal; değilse market giriş, sabit geometri (hedef küçültülmez — "probasyon + küçük TP" daha kötü). Dış örneklem n=112 WR %61,6 +3.691$ (ref +1.607$), iç n=126 +7.582$ (ref +2.842$) → B+. — [yeni deneme/probation_exec.py](yeni deneme/probation_exec.py)
- **NDX BUY BE@30 dk + kazananı-koştur (TP'de TP'yi kaldır, 0,6R iz) — LIVE; GDAXI BUY yalnız koştur; USOIL BREAKOUT koştur 1,0R iz.** Kanıt 223 NDX + 122 DAX gerçek işlem, 1m replay: NDX Δ+29,5R [16,4, 43,5] P %100; DAX Δ+12,1R P %98,3 (tek dönem, örneklem içi, B). SELL'e BE/trail Δ−7,5R; BUY'da giriş geciktirme −41R. **2026-10-20 kritik:** kazananı-koştur canlıda HİÇ tetiklenmedi (37 TP, 0 runner) — sunucu TP'si trade_manager'dan önce doluyor; BE de 07-31'den beri tetiklenmedi. BE modu artık `conditional_mfe` (MFE ≥ 0,5R). — [yeni deneme/trade_manager.py](yeni deneme/trade_manager.py); [memory/trade-mgmt-be30-runner-2026-07.md](memory/trade-mgmt-be30-runner-2026-07.md); [yeni deneme/phase_rules.py](yeni deneme/phase_rules.py)
- **Decider XAU BUY erken kesme — LIVE (2026-10-21).** Açılıştan ≥5 dk sonra ilk kez, son kapalı 1m kapanışıyla R = (kapanış−giriş)/(giriş−ilk SL) ≤ −0,5 ise kapat; tek karar; >10 dk gecikmede dokunma. Gölge 566 +0,013R P %97,9, ileri +0,037 P %99,7, plato 24/25 hücre ≥0; SELL'e ve **DAX'a taşınmadı (DAX'ta −0,016, plato 23/25 negatif)**. Etki: decider XAU'yu başabaşa getirir, kârlı yapmaz. — [yeni deneme/decider_early_cut.py](yeni deneme/decider_early_cut.py); [Defter DX-04, DX-05](docs/KAPI_KAYIT_DEFTERI.md)
- **USOIL haftalık açılış kapısı — LIVE (C).** Hafta sonu boşluğundan (≥24 s) sonraki ilk 60 dk USOIL'de yeni giriş yok; kenar iddiası yok, risk azaltıcı kullanıcı kuralı. — [yeni deneme/phase_rules.py](yeni deneme/phase_rules.py); [Defter B21](docs/KAPI_KAYIT_DEFTERI.md)

**Canlı giriş kapıları (bot)**
- B1 XAU SELL + USOIL SELL yasağı (USOIL SELL 47 işlem WR %21,3 −21,7R) — LIVE A/B. B2 NDX Cuma yasağı (Cuma ≥12 UTC n=24 −4.050$, permütasyon p=0,0146; DAX'ta Cuma pozitif → NDX'e özgü) — LIVE A. B3 NDX Asya 22–07 UTC yasağı (n=36 WR %50 −2.139$) — LIVE B. B4 TREND_GATE 1h EMA50 hizası (332 işlem: hizalı %63,3 +9.710$ / karşı %43,4 −13.161$; engellenen SELL'ler tabanın 16–22 puan altında) — LIVE A−. B5 POSITION_GATE (SELL ≥0,40 / BUY ≤0,60 dalga konumu) — LIVE C/B. B6 TQ (Cuma + 15–17 UTC çukur) — LIVE B. B7 CHREV ADX≥25 — LIVE C (tek vaka −687$). B8 FAKEOUT_VETO — LIVE A(NDX)/C. M12 BACKEND_BASIS_TOL %0,25 — LIVE A (olay). — [Envanter §1–2](docs/KAPI_ENVANTERI_2026-09-30.md); [Defter §2.1](docs/KAPI_KAYIT_DEFTERI.md)
- Bot ayarlarına dair uyarı: yerel `config.py` ≠ kutu (kutuda lot 5,0, `ONLY_CONFIRM_SIGNALS=False`, `ZONE_MIN_TOUCH_CANDLES=2`, broker sembolleri NAS100/SpotCrude/GER40); varsayılanlar `getattr(config, AD, varsayılan)` + `phase_rules.DEFAULTS`'ta. — [memory/mt5-box-operational-facts.md](memory/mt5-box-operational-facts.md); [Defter E11](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- MOM/SR, VIXREG, CHREV backend **pulse/panel sinyallerine** dayanıyor; BTC için panel sinyali yok → BTC'de bunlar ancak bar-tabanlı vekillerle (ör. IO-22'deki "VIXREG vekili": pulse ∧ VIX-lehte yön, Asya/Cuma hariç, 80/110) sınanabilir. Defter E22: panel-sinyali scope'ları bar verisinden yeniden üretilemez.
- Bar verisinden birebir taşınabilecek "kural" adayları yalnız: CAPREV, R0B_G1 (+S2), Golden Donchian, momentum filtresi + ATR 2/1 geometri, CHREV kanal z-skoru, DAYCOMBO (seans-bağımlı), USOIL breakout (negatif kontrol), probasyon ve BE/runner yönetim katmanları.
- Runner'ın canlıda hiç tetiklenmemesi, BTC'ye yönetim katmanı taşınırken "sunucu TP'si koymadan sanal TP" tasarımının şart olduğunu gösteriyor.

### Gaps
- Kutudaki gerçek `config.py` değerleri bu oturumda okunmadı (yalnız repo varsayılanları + 2026-08-14/09-30 dökümleri).
- VIXREG SL'inin canlıda sabit 110 mı ATR×2 mi kullandığı, kutu config'i görülmeden kesin değil.

---

## S2. Elenen fikirler ve nedenleri (defter §0–§3, kompakt)

### Takeaway
Projede denenen fikirlerin büyük çoğunluğu ya **sızıntı/saat ekseni/sahte çoğaltma** hatalarıyla şişmiş, ya **sürüklenme tabanını** geçemedi, ya da **WR'ı artırıp R'yi düşürdü**. Dayanan ilkeler: rastgele girişte tek-özellikli durum kapısı yok; korku döner coşku dönmez; braket ≠ zaman; fiyat-konumu kapıları stratejiye özgü, günlük rejim kapıları taşınır.

### Cited Findings

**§0 zorunlu sıra (yeni araştırma):** §2'de ara → §1 tuzak kontrolü → §3 ilke → **ön-kayıt `PROTOCOL.md`** (tanım/eşik/geçme ölçütü sonuca bakmadan) → kapısız taban (aynı dönem × yön × saat), başabaş, bağımsız sonraki dönem, birden fazla geometri, bağımsız karar sayısı, plasebo → canlıya yalnız kartla, önce GÖLGE → deftere satır + Evrim Paneli notu. "Çıplak WR yasak — beklenti (R) + epoch." — [Defter §0](docs/KAPI_KAYIT_DEFTERI.md)

**Elenen giriş stratejileri / sinyaller (REJECTED)**
- 1m scalp (XAU/NDX/USOIL/DAX), %70 WR veya sağlam +EV: yok; NDX = drift, USOIL = whipsaw (iki yön ~%44), DAX en büyük brüt sinyal ama spread net CI [−1,39, −0,40]; yüksek-WR pencereleri örtüşen-örneklem yanılsaması (~5 gerçek gün). — [memory/multi-asset-scalp-no-edge.md](memory/multi-asset-scalp-no-edge.md); [memory/xauusd-scalp-no-edge.md](memory/xauusd-scalp-no-edge.md); [Defter OLD-01](docs/KAPI_KAYIT_DEFTERI.md)
- 4H S/R + kanal REAKSİYON girişleri (NDX BUY/USOIL BUY): hepsi −EV (OLD-05). S/R pivot rejection zayıf/zararlı. — [Defter OLD-05](docs/KAPI_KAYIT_DEFTERI.md)
- NDX Reflex `mom_cont` (M15 gerilme >2×ATR + 1m geri çekilme-devam): sızıntılı +0,88R → sızıntısız −0,08R (P %13); 15m `label=left` örnekleme + teyit aynı dilimde (E16). sweep, orb, sr_react, vwap_rev/chan_rev ailesi sürtünmeye yenik; trailing kârı dolum artefaktı. — [Defter GF-13, OLD-15](docs/KAPI_KAYIT_DEFTERI.md); [memory/ndx-reflex-engine-2026-07.md](memory/ndx-reflex-engine-2026-07.md)
- NDX SELL büyük kırmızı mum (gövde ≥1×ATR14, gövde/menzil ≥0,55; 5.574 olay): 80/110'da −0,010R, ATR 1:1 −0,118R; ayna (büyük yeşil → BUY) de negatif → "5m büyük mum devamı" ailesi ölü; küçük-offset limit giriş ters seçilim (dolmayan %13 sinyalin market beklentisi +43 p). Tek ayakta: +1,0×ATR büyük-offset limit (gölge adayı). — [memory/ndx-sell-red-candle-no-edge.md](memory/ndx-sell-red-candle-no-edge.md); [Defter OLD-21](docs/KAPI_KAYIT_DEFTERI.md)
- USOIL Donchian breakout (yukarıda) X; XAU M15 bounce/breakout sürtünmeye yenik; XAU makro yön modeli işaret değiştirdi (OLD-07); MACD cross (OLD-12); CORTEX analog-kNN (OLD-13); pulse ters çevirme bedava değil (OLD-08, dürüst WR %55–62). — [Defter §2.4](docs/KAPI_KAYIT_DEFTERI.md)
- Mum formasyonları (20 klasik × 2 yön × 5 çıkış; NDX/DAX/XAU/USOIL): tur 1 0/200; pin bar @tepe TERS derin testte çürüdü (NDX 1h 10y taban farkı −0,076); XAU 6 geçen vs plasebo ort 5,1. — [Defter MK-01, MK-02, MK-05](docs/KAPI_KAYIT_DEFTERI.md)
- Formasyon tekrarı / mum eşleştirme (ME-00…ME-12, PM, PM-2): yön isabeti %51,4–51,9 = rastgele komşu < hep-çoğunluk %53; 69 hücrede tabanı geçen 0; DTW/MASS/SAX vb. 2.002 yapılandırmada 0 aday; bağlam (VIX/stres/saat/çapraz-sembol) eklemek de katkısız. — [Defter §2.8](docs/KAPI_KAYIT_DEFTERI.md); [Defter PM](docs/KAPI_KAYIT_DEFTERI.md)
- XAU mekanik kurallar (MK-07): braketli (TP'li) geometrilerin hepsi taban düzeyi/altında (TP1/SL1 her kuralda −0,02…−0,07); Londra Asya-high kırılımı her geometride negatif; D1 trend filtresi sürüklenmeyi seçiyor, tetik katkı vermiyor; 2016-26'da hiçbir SELL aynası pozitif değil. — [Defter MK-07](docs/KAPI_KAYIT_DEFTERI.md)
- HEKA kitabı: EMA 10/25/50 dizilim (ileride 109 işlem −0,247R), %80 değer alanı kuralı (karşı kenar %44–50), "çok test edilen S/R kırılır" (kırılma her kovada ≈%77), RSI A diverjansı (16 hücrede 0) → hepsi X. — [Defter HK-01…HK-05](docs/KAPI_KAYIT_DEFTERI.md)
- Gün-içi akış: gamma-koşullu son yarım saat momentumu P=0,80 (C); günlük endeks geri dönüşü: olgu gerçek (β=−0,12, P 0,999; DAX −0,10) ama strateji net −3,0 bp/gün; kazancın tamamı düşüş sonrası (+14,7 vs +0,2 bp) → B (olgu)/X (strateji)/C+ (düşüş sonrası al). — [Defter GM-01, GR-01](docs/KAPI_KAYIT_DEFTERI.md)
- Fakeout dedektörü işlem stratejisi olarak: 786 karar net −0,068R, P %1 → X; dedektör %70/%70'i yalnız NDX'te geçti (DAX/XAU/USOIL geçmedi, 2026-08-12 yeniden üretim). Kapı olarak NDX'te canlı (işaretlenen %25,6 vs geçen %53,6). — [Defter CK-02, CK-04, OLD-17](docs/KAPI_KAYIT_DEFTERI.md)
- Decider: gösterge-eşik kuralı yok (gerçek 138 vs plasebo medyan 142); XAU seçim alfası gün eşlemeli +0,06 [−0,12, +0,22]. — [Defter IO-12, DX-02, DX-03](docs/KAPI_KAYIT_DEFTERI.md)

**Elenen kapı/filtreler (REJECTED / zayıf)**
- GF-01: 780 hücre tek-özellik taraması (78 özellik × 4 ufuk × 5 dilim × 2 yön) → 13 geçen vs plasebo ort. 16,4 → **rastgele girişte durum kapısı yok**. GF-02 (16 ön-kayıtlı: kapanış akışı, Avrupa açılışı, gap fade/go, premarket, ADR tükenmesi, VR, yuvarlak sayı, VWAP σ-bandı, önceki gün uçları, ay dönümü, OPEX, VIX vade yapısı) dört dönemde tutarsız. GF-03 gün×saat takvimi çağlar arası korelasyon 0,0085. GF-04 p-değeriyle seçilen 6 koşulun 1'i tuttu. — [Defter §2.5](docs/KAPI_KAYIT_DEFTERI.md)
- ENTRY_SCORE (8 koşul): ilk +2.943$ sızıntılı (E1), sızıntısız eşiklerin dördü de negatif. VIX_REGIME_MICRO aynı otopsi. POS_TIGHT sahte çoğaltma (8,1× şişme). SQZ ATR14/ATR100<1: ileri dönemde tutmadı (engel −2,0R). USOIL 13 UTC öncesi BUY yok: ileride −0,4R. — [Defter B10, B11, B13, B14, B15, IO-22, IO-24](docs/KAPI_KAYIT_DEFTERI.md)
- Çıkış kuralları: BE/kilit/zikzak 50+ varyant (487 işlem) ve 44.064 varyant — her BE eşiğinde kurtarandan çok kazanan ölür (BE@%60: 54 kurtar / 75 öldür, −4.007$); zaman stopu 240 dk dış örneklem −1.900$; TP=2,5×ATR70 WR↑ para↓; erken çıkış R≤−0,3/−0,5 @5–30 dk hepsi negatif (bot ailesinde); SL/TP çarpanı 15 varyant −0,06…+0,03R; TP'nin %80'inde SL kilidi 16/16 ikinci yarıda negatif. — [memory/be-lock-exit-rules-rejected.md](memory/be-lock-exit-rules-rejected.md); [Defter M7–M9, IO-07, IO-08, IO-10, IO-16](docs/KAPI_KAYIT_DEFTERI.md)
- Brute-force SL-önleme vetoları: eğitim↔sınama Spearman +0,03/−0,08; eğitimde +16R → sınamada −12R. TP/SL optimizasyonu son 45 gün → önceki dönemde 56/56 kötü. Kovalama vetosu (IO-18) seçim düzeltmeli p=0,57 → C. — [Defter IO-11, IO-13, IO-18, IO-20](docs/KAPI_KAYIT_DEFTERI.md)
- Coşku aynası (dün ≥ +%1,5 → BUY yok) 1/5 — K6 (200g +%10 → BUY yok) vekilde zararlı; FOMC öncesi SELL yok ters işaret; VR pürüzlülük botta ters; "stres günü teyitli SELL (yeni dip)" = kapitülasyonu satmak, en kötüsü. — [Defter GF-07, GF-09, GF-12, GF-14](docs/KAPI_KAYIT_DEFTERI.md)

**§1 kanıt hataları (BTC testinde de geçerli olanlar):** E1 `copy_rates_from` ileri bar; E2 MT5 `time` broker saati (UTC+2/+3); E5 export offset (+1230 dk); E6 aynı koşulun her taramada tekrar kaydı (n şişmesi, epizod bastırma şart); E7 giriş = sinyal barı kapanışı + spread'siz; E9 bölünmüş bacaklar; E12 küçük alt kümede %100; E13 sürüklenme (yükselen piyasada kapısız BUY tabanı %92); E14 WR↑ ≠ para↑; **E15 "aynı günün ortalamasına göre fark" geleceğe bakar** (taban = dönem × yön × UTC saati); **E16 sol-etiketli çok-TF örnekleme sızıntısı** (`label/closed="right"`, "bar bitişi ≤ karar" testi); E17 çok-koşullu skorlar ve p-değeriyle seçim dönemler arası taşınmaz; E18 kapıyı başka popülasyona taşıma; E19 grup kaybı ≠ veto kazancı (portföyde yeniden yürüt); E21 besleme farkı (Yahoo vadeli vs broker); E23 aynı geçmişe tekrar tekrar bakma; **E24** seçim düzeltmeli maks. istatistik (dairesel kaydırma, aramanın tamamını tekrarla); **E25 sabit % payı/eşik semboller arasında farklı katılık** (ATR biriminde ver); E26–E28 iyi↔kötü hücre simetrisi; E27 %50 hedeflerde "hep çoğunluk" tabanı yazı-tura; E29 kontrol kümesi başka dönemden; E30 sürüklenme-üstü fark için max-z p ≤ 0,10; **E31 en iyi N gün payı örtüşmeli vs tek-pozisyon setine bağlı**; **E32 ATR-normalize R'de ince piyasa/tatil saatleri ATR'yi sıkıştırır → sahte 10R günler** (hem R hem nominal % ile raporla); **E33 aynı-hafta sürüklenme kontrolü olayın sonucuyla seçilen dönemde geleceğe bakar**; E34 iç içe iki post-hoc bayrak (2×2 raporla); E35 sabit mum adımlı sorgu ızgarası saate kayar (saat eşle); E39 iki farklı 1m tablo farklı sonuç. — [Defter §1](docs/KAPI_KAYIT_DEFTERI.md)

**§3 meta-dersler:** (1) rastgele girişte tek-özellikli durum kapısı yok; kenar günlük rejimde (VIX/stres) veya stratejinin yapısında (geometri, zaman çıkışı). (2) **Korku döner, coşku dönmez** (NDX ve DAX). (3) Teyit sinyal ölçeğinde iyi, günlük ölçekte ters. (4) Kovalama cezası ölçekler arası birikir ama bota özgü kalabilir. (5) **Braket ≠ zaman** (TP80/SL110 toparlanma sürüklenmesini yakalayamaz). (6) Fiyat-konumu kapıları stratejiye özgü; bilgi-şoku ve günlük rejim kapıları taşınır. (7) Yüksek WR ≠ kenar (TP80/SL110'da başabaş %57,9). (8) Teori: E[PnL]=μ·E[τ], E[τ]≈TP·SL/σ² (μ∝σ² kanıtlanmadı). (9) Sızıntı denetimi önce (prefix testi). (10) Veto katkısını portföyde ölç; ≤20 günlük alt kümeyi kanıt sayma. — [Defter §3](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- Defterdeki "çökenler" listesinin ortak paydası: (a) yön/WR'ı ölçen ama R'yi ölçmeyen etiketler, (b) tek dönem/tek piyasa, (c) seçim yükü. BTC testlerinde bu üçü baştan kilitlenmeli (R metriği, bağımsız dönem/piyasa, aile-içi seçim düzeltmesi).
- BTC, NDX geçmişine "4+ tur bakılmış" olmasının (E23) yarattığı aşırı uyum riskine karşı **gerçekten bağımsız bir piyasa** sunuyor — bu yüzden mevcut kuralların DONDURULMUŞ hâlde tek seferlik sınanması en değerli kullanım.

### Gaps
- `research/` altındaki her alt klasörün RAPOR'u tek tek okunmadı; sayılar defter ve hafıza özetlerinden alındı (defter kendisi bu raporların özetidir).

---

## S3. Canlıya alma kartı (`backend/research/go_live_gate.py`) — yeniden uygulanabilir metodoloji ve mevcut kartlar

### Takeaway
Kart, bir giriş kuralını **sonraki M1 açılışı + gerçek spread** ile 1m yol üzerinde TP/SL yarışına sokar ve 6 ölçütün hepsini ister; 10 ölçütlü "genişletilmiş kart" (MK-06 protokolü) buna sürüklenme plasebosu, görülmemiş alt dönem, Holm ve ileri broker işaretini ekler. MT5'e bağımlı kısım yalnız veri çekimi (`fetch`, `get_spread`); simülasyon saf numpy olduğundan CSV/parquet BTC verisine birebir taşınabilir.

### Cited Findings
- **Ölçütler ve eşikler:** `MIN_EVENTS=150`, `MIN_P_EV=0,90`, `SPREAD_STRESS=1,5`. (1) hacim ≥150 çözülmüş olay; (2) ortR > 0 ∧ bootstrap P(EV>0) ≥ %90; (3) zaman sıralı ilk yarı ve son yarı ortR'nin ikisi de ≥ 0; (4) spread×1,5'te ortR > 0; (5) |ortR(kapanış-girişi, spread 0) − ortR(gerçek)| ≤ 0,5×|ortR(gerçek)|; (6) "aynı anda tek pozisyon" (`as_traded`) ortR > 0. Verdikt: hacim düşerse RED; hepsi geçerse LIVE; aksi SHADOW. — [backend/research/go_live_gate.py](backend/research/go_live_gate.py)
- **`simulate()` (BUY):** olay `{t, atr, close}`; sinyal barı 5m, kapanış = `t+300`; `k` = kapanıştan sonraki ilk M1 indeksi (600 sn'den geç ise atla); giriş = `o1[k] + spread` (iyimser modda `close`); `unit = sl_atr×atr`; TP = giriş + tp_atr×atr; SL = giriş − unit; en fazla 1440 M1 bar (24 s) taranır; **aynı barda önce SL kontrol edilir** (SL ve TP aynı barda → kayıp); isteğe bağlı BE-trail (TP'ye dokununca runner, SL = max(SL, TP−unit), sonra tepe−unit izi); R = (çıkış − giriş)/unit; 24 s içinde çözülmeyen olay **atılır**. — [backend/research/go_live_gate.py](backend/research/go_live_gate.py)
- **`boot_p()`:** R dizisinden 5.000 iade-li yeniden örnekleme (i.i.d., `default_rng(11)`), n<20 ise P=0; %95 aralık 2,5/97,5 yüzdelikleri. **`as_traded()`:** olaylar zamana göre; önceki pozisyonun `k + hold` M1 indeksi bitmeden gelen olay atlanır. — [backend/research/go_live_gate.py](backend/research/go_live_gate.py)
- Kartın kayıtlı tek bar-scope'u `usoil_breakout` (Donchian48 + 5m EMA200, TP=SL=1×ATR); panel sinyali scope'ları için karşılığı ≥100 gölge/canlı işlemlik **canlı işlem kartı** (`live_card.py`, karar bazında; sürtünme ölçütü orada "+0,5×spread"). — [backend/research/go_live_gate.py](backend/research/go_live_gate.py); [momsr_canli.json](backend/data/evolution/go_live_cards/momsr_canli.json)
- **Genişletilmiş 10 ölçütlü kart (MK-06 protokolü):** BUY giriş = bid_open + spread, TP/SL bid high/low ile, aynı bar TP+SL → LOSS, giriş barında da SL/TP geçerli; >3 s boşlukta pozisyon boşluktan önceki son barda kapanır; R = (çıkış−giriş)/SL mesafesi. Ek ölçütler: (7) **P1 sürüklenme plasebosu** — her sinyal için aynı takvim yılı + aynı UTC saatinden rastgele bar, aynı geometri ve çıkış, 200 tekrar, kural ≥ %95 yüzdelik; (8) görülmemiş alt dönemde ortR > 0; (9) Holm (gün-kümeli t, tek yönlü α=0,05); (10) broker kasasında işaret pozitif. Seçim düzeltmesi: her plasebo tekrarının max(ortR)'si ile gerçek max hücre kıyası (max-z). LIVE = 1–10 hepsi; SHADOW = kart 1–6'dan en fazla biri düşer veya 7–10'dan biri düşer ∧ ortR − P1 > 0; RED = ortR ≤ P1 veya 2+ kart ölçütü düşer. Gün-blok bootstrap kullanılır. — [research/decider_xau_tpsl_20261015/mekanik/PROTOCOL.md](research/decider_xau_tpsl_20261015/mekanik/PROTOCOL.md)
- **Sızıntısız bar kesimi:** bar `t` ancak `t + periyot ≤ karar anı` ise kapanmıştır; koşan bar dahil edilmez (`_bars_upto.rates_upto`). — [backend/research/_bars_upto.py](backend/research/_bars_upto.py)
- **Mevcut kartlar** (`backend/data/evolution/go_live_cards/`): `caprev.json` RED (hacim 107; diğer 5 ✓) · `caprev_portfoy.json` **LIVE** (161/134 gün, +0,217) · `chrev_canli.json` RED (66, −0,016) · `daycombo_canli.json` RED (31, +0,281) · `momsr_canli.json` SHADOW (182, −0,014) · `reentry_canli.json` RED (19, +0,446) · `sqz_filter_ndx.json` GÖLGE (45, ileri kart) · `usoil_breakout.json` SHADOW (368, −0,125, P %0,7; icra ✗: −0,005 vs −0,125) · `vixreg_canli.json` SHADOW (209, +0,010) · `xau_1h_yeni_tepe_buy.json` LIVE (stopsuz, 1.563, +0,324; en kötü −21,7R) · `xau_1h_yeni_tepe_buy_sl15.json` SHADOW (1.857, +0,107, icra ✗ +0,169 vs +0,107). — [go_live_cards/](backend/data/evolution/go_live_cards/)

### Inferences
- BTC için yeniden uygulama reçetesi: (i) 1m OHLC (tercihen bid/ask veya broker spread serisi) + sinyal TF barları `label=right` ile türetilmiş; (ii) giriş = sinyal barı kapanışından sonraki ilk 1m açılışı + spread (BTC'de spread $ cinsinden broker ölçümü; Binance spot verisinde bid/ask yok → sabit spread modeli A, ×1,5 stres); (iii) aynı bar TP+SL = kayıp; (iv) 24 s sınırı zaman-çıkışlı kurallar için kuralın kendi çıkışıyla değiştirilmeli (orijinal kod çözülmeyeni atıyor → zaman çıkışlı stratejilerde yanlılık yaratır); (v) i.i.d. bootstrap yerine **gün-blok bootstrap** (BTC 24/7, gün = UTC 00:00); (vi) P1 plasebosu = aynı yıl × aynı UTC saati rastgele giriş; (vii) yarılar zaman sıralı.
- `go_live_gate.py` 24 s içinde çözülmeyen olayları düşürdüğü için CAPREV/R0B_G1 gibi TP'siz zaman-çıkışlı kurallarda doğrudan kullanılamaz; ilgili kartlar ayrı betiklerle (`caprev_card.py`, `xau_card*.py`) üretilmiş.

### Gaps
- `caprev_card.py` / `caprev_pooled.py` içindeki gün-blok bootstrap blok boyu ve tekrar sayısı okunmadı.
- `live_card.py`'nin "+0,5×spread" sürtünme tanımının tam formülü okunmadı.

---

## S4. Taşınabilirlik: mekanizma-düzeyi bulgular vs. seans/borsa saatine bağlı bulgular

### Takeaway
Taşınma ihtimali en yüksek olanlar **günlük rejim / bilgi şoku** mekanizmaları (stres ∧ korku → kapitülasyon alımı; düşüş sonrası geri dönüş; korku döner coşku dönmez) ve **yapı/geometri dersleri** (braket ≠ zaman, momentum filtresi yalnız uzak hedefle öder, yeni-tepe kırılımında kovalama cezası). Seans/saat takvimleri, nakit açılış kuralları ve sembole özgü yön yasakları taşınmaz — projenin kendi verisi bunların sembol ve çağ değiştirince çöktüğünü gösteriyor.

### Cited Findings
- Fiyat-konumu kapıları stratejiye özgü, bilgi-şoku ve günlük rejim kapıları taşınır (E18, GF-14). — [Defter §3.6](docs/KAPI_KAYIT_DEFTERI.md)
- Korku döner (NDX + DAX): CAPREV DAX'ta kural aynen tuttu; QQQ/NDX günlük 10–11/11 yıl; coşku aynası 1/5. RSI diverjansında da boğa > ayı, ama farkı yapının kendisi yaratıyor. Günlük geri dönüş olgusu SPX/DAX'ta da var ve kazancın tamamı düşüş sonrası. — [Defter GF-12, GF-18, HK-04, GR-01](docs/KAPI_KAYIT_DEFTERI.md)
- "Yeni tepede al" piyasaya özgü: NDX yukarı momentum, XAU iki yönlü trend (yeni dip SELL de +), USOIL dönüş (taban altı). — [Defter MK-02, MK-03](docs/KAPI_KAYIT_DEFTERI.md)
- Momentum-continuation→uzak TP davranışı 8 scope'un 7'sinde görüldü ("beta-benzeri özellik"); ayırıcı olan TP genişliği vs sürtünme (dar TP'li XAU SELL öldü). — [memory/bot-momentum-5dir-2026-06.md](memory/bot-momentum-5dir-2026-06.md)
- Kanal-sınır dönüşü 4/4 sembolde +27–29pp (WR olarak), ama sabit uzak hedefte tersine dönüyor; 1m'de zayıf. — [memory/channel-rejection-edge.md](memory/channel-rejection-edge.md); [memory/indicator-discrimination-2026-06.md](memory/indicator-discrimination-2026-06.md)
- Yön asimetrileri sembole özgü: XAU BUY ~%70 / SELL ~%21; USOIL SELL ~%84 / BUY ~%10 (lifecycle etiketleri, 45 gün); botta USOIL SELL ise −21,7R → asimetrinin işareti bile dönem/geometriye bağlı. — [memory/indicator-discrimination-2026-06.md](memory/indicator-discrimination-2026-06.md); [Envanter B1](docs/KAPI_ENVANTERI_2026-09-30.md)
- Seans/saat bağımlı ve çağ/sembol değişince çöken kurallar: NDX Cuma yasağı (DAX'ta Cuma pozitif), NDX Asya yasağı, TQ 15–17 UTC çukuru, SESSION_GATES (aynı otopsiden, sızıntı denetlenmedi), gün×saat sürüklenme takvimi (çağlar arası r≈0), DAYCOMBO (gece 00→13:25 UTC + 14:00–19:30 UTC ABD nakit penceresi; 2025'te −0,030R), CAPREV'in RTH dibi tanımı, Londra Asya-high kırılımı (her geometride negatif), NY sabah gücü (yalnız 2016-26), son nakit saati→gece etkisi (DAX'ta nokta sıfır), gamma son yarım saat, ay sonu dengeleme (K3), OPEX, EIA penceresi, USOIL haftalık açılış kapısı. — [Defter §2.1, §2.5, MK-07, ME-07, GM-01, CK-03](docs/KAPI_KAYIT_DEFTERI.md); [yeni deneme/config.py](yeni deneme/config.py)
- Decider kapıları bota ters çıktı (chz_dir≥2,0 bıçak kapısı decider'da A−, botta ters) → popülasyon transferi E18. VIX rejim etkisi decider journal'ında ölçülemedi çünkü journal tek düşük-VIX rejiminde (VIX 15,1–19,6, VIX≥20 kaydı 0). — [memory/decider-breakeven-entry-quality.md](memory/decider-breakeven-entry-quality.md)
- XAU'da makro (reel faiz/dolar/VIX) yön bağları 2024-26'da işaret değiştirdi → makro→yön ilişkisi varlığa ve çağa özgü olabilir. — [memory/macro-ndx-vix-direction.md](memory/macro-ndx-vix-direction.md); [Defter OLD-07](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- **BTC'ye taşınabilir aday mekanizmalar:** (1) kapitülasyon alımı (stres ∧ korku göstergesi ∧ önceki gün dibi altı ilk kapanış → BUY, vol-stop, zaman çıkışı); (2) düşüş sonrası günlük geri dönüş; (3) coşku aynasının başarısızlığı (SELL kontrolü); (4) yeni-tepe kırılımı + "dün çok yükseldiyse atla" kovalama cezası; (5) günlük Donchian + EMA200 swing; (6) momentum filtresi + ATR 2/1 geometri; (7) kanal z-skoru dönüşü (zaman çıkışı ile); (8) probasyon (5 bar gürültü bandı) ve "braket ≠ zaman" yönetim dersleri.
- **Taşınmaz / yeniden tanım gerektirir:** RTH/nakit açılış/kapanış referanslı her şey (BTC'de seans yok; "gün" UTC 00:00 veya NY 17:00 olarak ön-kayıtla seçilmeli), Cuma/Asya/saat yasakları, EIA/OPEX/ay sonu akışları, haftalık açılış boşluğu (borsa BTC'si 24/7 işlem görür; MT5 CFD'nin hafta sonu durumu belirsiz — Gaps), sembole özgü yön yasakları (BTC'nin kendi asimetrisi ayrı ölçülmeli).
- **Korku göstergesi seçimi:** NDX kuralı VIX ≥ 18,4 kullanıyor; BTC için (a) VIX'i aynen kullanmak (risk varlığı korelasyonu varsayımı; bağımsız sınav niteliğinde), (b) BTC'nin kendi gerçekleşmiş oynaklığı (ör. 30 g RV'nin 1 yıllık medyan üstü) — ikisi de ön-kayıtla, ayrı hücre olarak. NDX'te "stressiz ∧ yüksek VIX ≈ 0" bulgusu, iki şartın birlikte gerektiğini; BTC'de de çapraz hücreler (stres×korku 2×2) raporlanmalı.
- **Eşik ölçeği (E25):** NDX'in −%1,5 / −%4 eşikleri BTC'nin günlük oynaklığında (NDX'in kabaca birkaç katı) sıradan gün olur; birincil tanım σ-birimli (dvol20 katı), literal % eşik ikincil sağlamlık hücresi olmalı. (BTC/NDX oynaklık oranı bu taramada ölçülmedi — Gaps.)

### Gaps
- BTC'nin gerçekleşmiş oynaklığı, BTC–NDX korelasyonu, VIX–BTC ilişkisi depoda ölçülmüş değil (`macro_context_service.py`'deki BTC–NDX ayrışma katsayıları "piyasa gözlemi" yorumuyla elle yazılmış, kanıt dosyası yok).
- MT5 kutusundaki brokerın BTCUSD CFD'sinin sembol adı, spread'i, swap'ı ve hafta sonu işlem saatleri depoda kayıtlı değil.

---

## S5. Hafıza notlarından ek sayılar ve dersler (yukarıda kullanılmayanlar)

### Takeaway
Hafıza notları defterle tutarlı; BTC tasarımına doğrudan girecek ek dersler: "tek-pozisyon ve dedup olmadan WR şişer", "geometri yanlışsa doğru yön kaybettirir", "runner canlıda tetiklenmeyebilir", "gerçek dolum simülasyonu canlıyı yakalıyor".

### Cited Findings
- USOIL breakout simülatörü aynı pencerede canlıyı doğru yakaladı (sim %24,1 vs canlı %26,3) → dürüst 1m simülasyon canlıyla tutarlı; spread=0 dünyasında bile %49,2. — [memory/usoil-breakout-no-edge.md](memory/usoil-breakout-no-edge.md)
- Decider XAU: stop 2,5→1,5 ATR yapılınca WR %65,0→%60,1 düştü ama EV −0,081R→+0,004R yükseldi (başabaş %71,4→%59,9) → "yön değil geometri yanlıştı". Decider genelde başabaşta (WR %61,1 vs başabaş %59,9). — [memory/decider-breakeven-entry-quality.md](memory/decider-breakeven-entry-quality.md)
- BE/kilit: TP'yle biten 279 kazananın 75'i %60'a varıp girişe dönmüş sonra TP vurmuş — izlenen "önce zarar sonra kâr" şekli kazananlarda da var; 1m ölçekte fiyat ortalamaya dönüyor. Motor yazarken iki iyimser yanlılık: kilit fiyatın üstündeyken stop'tan dolum, gecikmesiz "kapat". — [memory/be-lock-exit-rules-rejected.md](memory/be-lock-exit-rules-rejected.md)
- Reflex V1 yüksek-WR modu: tüm 10 grupta ≥%70 WR (taban %77,8) ama EV ≈ −0,06R (başabaş %86) — WR hedefi kenar değildir. — [memory/ndx-reflex-engine-2026-07.md](memory/ndx-reflex-engine-2026-07.md)
- NAS100 5m büyük kırmızı mum sonrası her geometride isabet başabaşın 1,5–3,4 puan altında ("isabet-oranı vergisi"); artıya geçen tek profil %15–26 isabet, 2,7–4,8:1 RR, kârın tamamı zaman-stopu çıkışlarından. — [memory/ndx-sell-red-candle-no-edge.md](memory/ndx-sell-red-candle-no-edge.md)
- MT5 operasyon: `copy_rates_from_pos` tavanı ~99.000 bar (M1 ≈ 68 gün); kutuda scipy/sklearn yok (saf numpy); üç saat dilimi (sunucu UTC+3, kutu UTC−4, log UTC). — [memory/mt5-box-operational-facts.md](memory/mt5-box-operational-facts.md)
- Günlük fren hatası: yeni magic eklendiğinde `_bot_magics()`'e eklenmeli; `history_deals_get` broker saatiyle çağrılmalı. — [memory/daily-brake-bug-sqz-verdict-2026-10.md](memory/daily-brake-bug-sqz-verdict-2026-10.md)
- HEKA: genel TA kitaplarının fikirleri çoğunlukla zaten sınanmış; ileri veri için broker 15m (`indicator_snapshots`). — [memory/heka-book-no-edge.md](memory/heka-book-no-edge.md)

### Inferences
- BTC botu yeni bir magic ile eklenirse günlük fren (`_bot_magics`), `MAX_TOTAL_POSITIONS`, broker saat ofseti ve trade_manager kapsamı birlikte güncellenmeli (IO-21 dersi).
- MT5'in ~68 günlük M1 tavanı, BTC broker verisinin yalnız "ileri kasa" (ölçüt 10) için yeterli olduğunu, ana sınamanın dış veriyle (Binance vb.) yapılacağını gösteriyor.

### Gaps
- Hafıza notlarında BTC/kripto ile ilgili hiçbir kayıt yok (grep: yalnız MEMORY.md'nin konu dışı satırları).

---

## S6. Depoda önceki BTC / kripto çalışması

### Takeaway
BTC'ye özgü **hiçbir sınanmış kenar, kapı veya kart yok**. Tek BTC izi: (a) bugün (2026-10-21 17:41) oluşturulmuş, veri indirme aşamasındaki `research/btc_5y_20261021/` (Binance BTCUSDT spot 1m, 2021-06→2026-10-20), (b) makro serviste BTC-USD'nin yfinance göstergesi ve elle yazılmış BTC–NDX ayrışma katkısı (kanıtsız), (c) bir bias-motoru testinde `symbol="BTCUSD"` çağrısı.

### Cited Findings
- `research/btc_5y_20261021/scripts/01_download_binance.py`: data.binance.vision spot BTCUSDT 1m kline; aylık zip 2021-06→2026-09 + Ekim 2026 günlük 01–20; her zip SHA256 `.CHECKSUM` ile doğrulanır, zip içeriği çalıştırılmaz; tarama anında `data/raw/monthly/` 32 MB (2021-06…2021-10+ zip'leri), `daily/` boş, `02_build.py` henüz yok. — [research/btc_5y_20261021/scripts/01_download_binance.py](research/btc_5y_20261021/scripts/01_download_binance.py)
- `macro_data_service.py`: `"BTC": "BTC-USD"` (yfinance) — yorum "correlated tech-beta proxy". `macro_context_service.py`: `_BIAS_BTC_NDX_DIVERGENCE` (NDX (−0,45, +0,25), GDAXI (−0,20, +0,10), XAU (+0,30, −0,15), USOIL (−0,15, +0,10)); 5 günlük NDX−BTC getiri farkı; docstring "My market observation (2024-2026)" — ölçüm/plasebo kanıtı yok. — [backend/services/macro_data_service.py](backend/services/macro_data_service.py); [backend/services/macro_context_service.py](backend/services/macro_context_service.py)
- `backend/tests/test_bias_engine.py`: `engine.run_debate(symbol="BTCUSD")` (birim testi; strateji değil). Defterde, envanterde, `yeni deneme/` kodunda, go-live kartlarında BTC geçmiyor. — [backend/tests/test_bias_engine.py](backend/tests/test_bias_engine.py)

### Inferences
- BTC araştırması temiz sayfa: önceki BTC sonucu olmadığından "aynı sınamayı tekrarlama" riski yok; ama NDX/XAU kurallarının BTC'de sınanması, o kuralların **bağımsız piyasa sınavı** sayılır ve tek seferlik kullanılmalı (holdout bir kez harcanır — ME-07 dersi).
- Binance spot BTCUSDT ≠ MT5 broker BTCUSD CFD (fiyat tabanı, spread, swap, hafta sonu); E21 (besleme farkı) türünden bir tuzak — ileri kasa broker verisiyle ayrıca ölçülmeli.

### Gaps
- `research/btc_5y_20261021/` başka bir ajan/oturum tarafından paralel üretiliyor; içeriği (build adımı, saat damgası birimi) bu taramada henüz yoktu.
- Binance public data spot kline'larında 2025 başından itibaren zaman damgası biriminin mikro-saniyeye geçtiği bilgisi bu modelin genel bilgisidir, depoda doğrulanmadı → build betiğinde ms/µs ayrımı kontrol edilmeli.

---

## S7. BTC'de sınanacak aday hipotezler (ön-kayıtlı) ve zorunlu yöntem korumaları

### Takeaway
Aşağıdaki 16 hipotez, projede **en az B sınıfı kanıtı olan** veya **elenmiş olup BTC'de negatif kontrol işlevi görecek** kurallardan, DONDURULMUŞ tanımlarla türetildi. Hepsi aynı geçme ölçütüne (genişletilmiş 10 ölçütlü kart) tabi; aile içi seçim düzeltmesi zorunlu. Veri: BTC 1m (Binance BTCUSDT spot, 2021-06→2026-10-20) + türetilmiş 5m/15m/30m/1h/1d (`label=right, closed=right`); ileri kasa = MT5 broker BTCUSD.

### Ortak ön-kayıt (tüm hipotezler)
- **Gün tanımı:** UTC 00:00–24:00 (birincil). NY 17:00 kesimi yalnız sağlamlık hücresi. Haftanın 7 günü dahil (hafta sonu ayrı raporlanır).
- **Giriş:** sinyal barı KAPANDIKTAN sonraki ilk 1m barın açılışı + spread (BUY: ask = open + s; SELL çıkışında + s). Spread modeli A = sabit $ (broker BTCUSD canlı ölçümünden, ölçülene kadar ön-kayıtta tek değer yazılır), A×1,5 = ölçüt 4. Aynı 1m barda TP ve SL → kayıp. Zaman çıkışı = çıkış barının kapanışı.
- **R:** (çıkış − giriş)/SL mesafesi; SL'siz geometri yok. Ayrıca nominal % getiri raporlanır (E32).
- **Ölçütler (10):** 1 n ≥ 150 bağımsız olay · 2 ortR > 0 ∧ gün-blok bootstrap P(EV>0) ≥ %90 · 3 kronolojik iki yarı ≥ 0 · 4 spread×1,5 > 0 · 5 |iyimser (bar kapanışı, spread 0) − gerçek| ≤ 0,5×|gerçek| · 6 tek-pozisyon ortR > 0 · 7 P1 plasebosunu (aynı yıl × aynı UTC saati rastgele giriş, aynı geometri/çıkış, 200 tekrar) ≥ %95 yüzdelikle geç · 8 sona ayrılmış holdout'ta (2025-12-01→2026-10-20; tek kez açılır) ortR > 0 · 9 aile içi Holm + max-z seçim düzeltmesi (p_sel ≤ 0,10) · 10 broker BTCUSD kasasında (MT5 M1, ~68 gün) işaret pozitif. LIVE = hepsi; SHADOW/RED şeması S3'teki gibi.
- **Ek raporlar:** en iyi 5/20 gün hariç ortR (tek-pozisyon setinde, E31), yıl bazında işaret, birden fazla geometri, 2×2 bayrak etkileşimleri (E34).

### Hipotezler

1. **H01 — BTC CAPREV (σ-ölçekli stres ∧ VIX):** *Gün koşulu:* önceki UTC günü getirisi ≤ −1,25×dvol20 VEYA 5 günlük getiri ≤ −1,25×dvol20×√5 (dvol20 = son 20 UTC gün kapanış getirisinin std'si) ∧ önceki ABD işlem günü VIX kapanışı ≥ 18,4. *Tetik:* gün içinde (00:00–20:00 UTC) ilk kapanmış 1h bar, kapanışı < önceki UTC gününün dibi. *Yön:* BUY. *Stop:* giriş×(1−dvol20). *TP:* yok. *Çıkış (a)* aynı UTC gün sonu 23:59, *(b)* ertesi gün sonu, *(c)* +1R/−1R. Tek pozisyon. *Kontrol hücreleri (aynı tetik):* stres ∧ VIX<18,4; stressiz ∧ VIX≥18,4; aynı olayda SELL. *Geçme:* 10 ölçüt + kontrol hücreleri ≈0/negatif (NDX deseni). *Köken:* GF-16/GF-18/GF-21/GF-22, `caprev_live.py`.
2. **H02 — BTC CAPREV, BTC'nin kendi korku göstergesi:** H01 ile aynı, VIX yerine "BTC 30 g gerçekleşmiş oynaklığı > önceki 365 günün medyanı". *Köken:* aynı; amaç VIX bağımlılığını ayırmak. H01/H02 tek aile içinde düzeltilir.
3. **H03 — Literal eşik sağlamlığı (E25 kontrolü):** H01'i NDX eşikleriyle aynen (−%1,5 / −%4) koş. *Beklenti:* olay sayısı çok yüksek, etki seyrelir. Karar H01'e göre verilir; H03 yalnız bilgi.
4. **H04 — Coşku aynası (negatif kontrol, "korku döner coşku dönmez"):** önceki gün ≥ +1,25×dvol20 (veya 5 g ≥ +1,25×dvol20×√5) ∧ gün içinde ilk 1h kapanış > önceki gün tepesi → SELL; stop giriş×(1+dvol20), gün sonu çıkış. *Beklenti (NDX'ten):* geçmemeli. Geçerse BTC'nin asimetrisi NDX'ten farklı demektir (yazılır). *Köken:* GF-12.
5. **H05 — Düşüş sonrası günlük geri dönüş:** önceki UTC günü getirisi < 0 → 00:00 UTC'de BUY, 23:59 çıkış, stop giriş×(1−2×dvol20) (felaket stopu). *Taban:* her gün BUY (hep-uzun) aynı çıkışla. *Geçme:* ortR − hep-uzun > 0 ve 10 ölçüt; ayrıca β (bugün getirisi ~ dün getirisi) işareti ve önceki düşüş büyüklüğüne göre monotonluk. *Köken:* GR-01 (β=−0,12, kazancın tamamı düşüş sonrası).
6. **H06 — Golden Donchian (D1, BUY):** UTC-D1 kapanışı ≥ önceki 55 D1 high ∧ kapanış > EMA200(D1, adjust=False) → sonraki D1 açılışı BUY; SL 2×ATR14(D1, sinyal barı dahil), TP 4×ATR14, 20 gün zaman stopu, tek pozisyon. Plato: N ∈ {40, 50, 55, 60, 70}. *Taban:* aynı geometride her gün BUY. *Not:* ~5 yıllık veride n muhtemelen <150 → en iyi ihtimal SHADOW (XS-01 gibi); ölçüt 1 baştan "yapısal olarak geçilemez" diye ön-kayda yazılır. *Köken:* xauusd-daily-swing-edge, XS-01.
7. **H07 — H4 Donchian 30 (BUY) + D1 trend:** H4 kapanışı ≥ önceki 30 H4 high ∧ D1 kapanış > EMA200 → sonraki H4 açılışı BUY, SL 2×ATR14(H4), TP 4×ATR14, 30 H4 bar zaman çıkışı. *Köken:* Golden Donchian H4 varyantı (+0,33R XAU). *Uyarı:* MK-07'de "D1 trend filtresi sürüklenmeyi seçiyor" — P2 (aynı TREND_UP koşulunda rastgele giriş) zorunlu kontrol.
8. **H08 — 1h yeni 20-bar tepesi BUY (R0B_G1):** H1 high ≥ önceki 20 H1 high → sonraki H1 açılışı BUY; SL 1,5×ATR14(H1, sinyal barı dahil); TP yok; 20 bar zaman çıkışı; tek pozisyon (çıkış barında yeni sinyal açılabilir). *Ayna kontrolü:* H1 low ≤ önceki 20 low → SELL, aynı geometri. *Geçme:* 10 ölçüt; P1'e karşı fark. *Köken:* MK-04/MK-06 (+0,102 vs P1 +0,049); MK-03 davranışın piyasaya özgü olduğunu gösterdiği için BTC sonucu önceden bilinmiyor.
9. **H09 — H08 + S2 kovalama atlaması:** önceki UTC günü getirisi > +1,0×dvol20 ise kırılımı ATLA (atlanan olay pozisyonu kilitlemez). Literal sağlamlık: XAU'nun +%1'i yerine σ-birimli birincil; eşik ×0,75 / ×1,25 plato. *Geçme:* H08 içinde fark < 0 (atlanan grup), tek-poz filtreli ortR > filtresiz, P1-F (yıl × saat × bayrak) DiD < 0. *Köken:* MK-13 (A).
10. **H10 — Momentum-continuation + uzak geometri:** 15m barda (kapanmış) `stoch_k(14)>70 ∧ (close−EMA20)/ATR14 > 0,8` ∧ son kapanmış 1h'te Parabolic SAR fiyatın altında → BUY; epizod bastırma: koşul önceki 15m barda da doğruysa olay değil (ilk geçiş). Geometri G1: TP 2,0×ATR14(H1) / SL 1,0×ATR14(H1), 24 s zaman sınırı; G2 (bot benzeri): TP 0,73×SL, SL 1,0×ATR(H1). SELL şablonu (kontrol): 30m `(close−EMA20)/ATR<0 ∧ macd_hist<0` ∧ 1h SAR üstte. *Geçme:* G1'de 10 ölçüt + aynı koşul durumunda rastgele zamanlı girişe karşı fark; *beklenti* G2 başabaş altı (OLD-20 deseni). *Köken:* ndx-buy-geometry-not-filters (+0,079R ATR 2/1), bot_router MOMENTUM_FILTER.
11. **H11 — Kanal-sınır dönüşü, zaman çıkışlı:** 30m (ve 15m sağlamlık) linreg n=50; BUY: z ≤ −2,0 ∧ ADX14(30m) < 25 ∧ kanal eğimi ≥ 0 (`channel_slope_atr`); SELL ayna; epizod başına ilk tetik. Çıkış G1: 12 bar zaman, SL 1,5×ATR14(30m); G2: TP 1,0 / SL 1,5 ATR. *Geçme:* 10 ölçüt; ADX ve eğim şartlarının 2×2'si raporlanır. *Köken:* channel-rejection-edge (WR liftleri), GDAXI düşen kanal %28,6 bulgusu; canlı kart −0,016R → önsel düşük.
12. **H12 — Stres günü SELL yasağı (kapı, K5b):** bir taban SELL üretecinde (ör. her UTC saati başı SELL, sabit SL 1×ATR14(H1)/TP 0,73×SL ve 24 bar zaman çıkışı ayrı ayrı) "stres günü (H01 tanımı) ∧ fiyat < önceki gün dibi" hücresindeki SELL'lerin ortR'si, diğer SELL'lerden düşük mü? *Geçme:* fark < 0, iki yarıda da, yıl × saat eşli tabanla; portföyde veto katkısı (E19). *Köken:* GF-10/GF-11 (−0,18R 4/4).
13. **H13 — Probasyon (MOD-E) katmanı:** H08, H10 ve H11'in olaylarında giriş 5×1m bar ertelenir; 5 barda aleyhe max hareket > 1,28×ATR14(1m)×√5 ise iptal; değilse market giriş, geometri aynı. *Geçme:* iptal edilmeyenlerin ortR'si (aynı olay setinde) anında girişten yüksek, iki yarıda da, ve iptal edilenlerin anında-giriş ortR'si < 0 (ters seçilim kontrolü — OLD-21 limit dersi). *Köken:* probation_exec (B+).
14. **H14 — Kazananı-koştur yönetimi:** H10-G1 ve H08 ile TP'si olan varyantlarda: fiyat TP'ye değince TP kaldırılır, SL = max(SL, TP−0,6R) ve sonra tepe − 0,6R izi (sanal TP; sunucu TP'si yok). BE@30 dk ayrıca ayrı hücre. *Geçme:* Δ ortR > 0, haftalık dilimlerin ≥%75'inde ≥0, iki yarıda +. *Beklenti:* BE hücresi geçmemeli (M9). *Köken:* trade-mgmt-be30-runner (Δ+29,5R), be-lock-exit-rules-rejected.
15. **H15 — Braket vs zaman (geometri dersi doğrulaması):** H01, H05, H08 olaylarının her biri üç çıkışla: (a) TP 1/SL 1 ATR, (b) TP 0,73R/SL 1R (bot 80/110 oranı), (c) kuralın zaman çıkışı. *Ön-kayıtlı beklenti:* (c) > (a), (b). Bu hipotez kenar değil, BTC'de "braket ≠ zaman" ilkesinin geçerliliğini sınar. *Köken:* §3.5, GF-17, MK-07.
16. **H16 — Donchian48 5m breakout + EMA200 (negatif kontrol):** 5m kapanış > önceki 48 bar high ∧ 5m kapanış > EMA200(5m) ∧ kırılım aşımı ≤ 0,5×ATR14(5m) → BUY, TP=SL=1×ATR14(5m). *Beklenti:* geçmemeli (USOIL −0,125R, P %0,7); ayrıca iyimser (kapanış, spread 0) vs gerçek farkı ölçülür — kart ölçüt 5'in BTC'deki duyarlılığını kalibre eder. *Köken:* usoil_breakout kartı.

### Sınanmayacaklar (gerekçeli, tekrar etme)
- 1m scalp / %70 WR hedefi (OLD-01, xauusd-scalp-no-edge, Reflex V1: WR ≠ kenar).
- Mum formasyonları, pin bar, formasyon tekrarı/mum eşleştirme, DTW/MASS vb. benzerlik tahmini (MK-01/02/05, PM, ME-02…ME-12).
- EMA 10/25/50 dizilimi, %80 değer alanı, çok-dokunuşlu S/R kırılımı, RSI diverjansı girişi, MACD cross (HK-01…04, OLD-12).
- BE/kilit/zikzak/zaman stopu/erken kesme varyantları (M7–M9, IO-07, IO-10; DX-05'te erken kesme DAX'a bile taşınmadı).
- Çok koşullu skor kapıları ve p-değeriyle koşul madenciliği (E17, B10, GF-04, IO-11).
- Fakeout dedektörü işlem stratejisi olarak (CK-02) ve seans/saat takvimleri (GF-03).

### Yöntem tuzakları — BTC testleri bunlara karşı korunmalı
- **Sızıntı:** sinyal TF barları `label="right", closed="right"`; karar anında yalnız `bar_bitişi ≤ t` barlar (E16, `_bars_upto` mantığı); prefix testi (geleceği değiştir → geçmiş özellik değişmemeli); D1/ATR/EMA'lar karar anına kadar; dvol20/VIX önceki gün kapanışından; "aynı gün/hafta ortalamasına göre fark" taban olarak YASAK (E15, E33).
- **Saat ekseni:** Binance zaman damgası birimi (ms/µs) ve UTC olduğu doğrulanmalı; MT5 broker BTCUSD barları sunucu saatinde (UTC+2/+3) — ofset ölç + çıkar (E2/E5); VIX tarihleri ABD işlem günü, BTC günü UTC → "önceki VIX kapanışı" eşlemesi karar anına göre (hafta sonu Cuma VIX'i).
- **Taban:** her hipotezde kapısız taban = aynı dönem × yön × UTC saati (P1) + gerekiyorsa filtre-koşullu taban (P2); yükselen BTC çağlarında hep-uzun tabanı yüksek (E13); "hep çoğunluk" tabanının kendi isabeti raporlanır (E27).
- **Bağımsızlık:** n yerine bağımsız karar/gün sayısı; epizod bastırma (E6); örtüşen pozisyonlar → tek-pozisyon seti ayrıca; gün-blok bootstrap; en iyi 5/20 gün hariç sonuç (tek-pozisyon setinde, E31).
- **Plasebo ve seçim:** 200 tekrar P1; aile içi max-z/Holm (E24, E30); iyi↔kötü hücre simetrisi (E26, E28); holdout (2025-12→) tek kez açılır.
- **Ölçek:** eşikler σ/ATR birimiyle (E25); ATR-normalize R'de ince piyasa saatleri (BTC'de hafta sonu/Asya gecesi) ATR'yi sıkıştırıp sahte büyük R üretir → nominal % ile de raporla (E32).
- **İcra:** spread ×1,5 stresi; iyimser–gerçek farkı (E7); broker CFD ile Binance spot arasındaki taban/spread/swap farkı ileri kasada ayrıca (E21 benzeri); hafta sonu spread genişlemesi ayrı hücre.
- **Popülasyon transferi:** NDX/XAU'dan gelen bir filtrenin BTC'de çalışması ayrı ölçülür, varsayılmaz (E18); veto katkısı portföyde (E19).

### Inferences
- En yüksek önsel olasılıklı adaylar H01/H05/H08–H09 (mekanizma bağımsız piyasada da tutmuştu: CAPREV DAX/QQQ, günlük geri dönüş SPX/DAX, R0B_G1 18 yıl XAU); en düşük H11/H16 (canlı/kart negatif).
- BTC'nin 24/7 yapısı nedeniyle CAPREV/"önceki gün dibi" tanımlarındaki "seans" kavramı yok; UTC günü birincil seçilip NY 17:00 sağlamlık hücresi olarak tutulmazsa sonuç gün tanımına aşırı-uyabilir.

### Gaps
- Broker BTCUSD spread/swap/hafta sonu verisi yok → spread modeli A şimdilik varsayım; ilk iş olarak kutudan ölçülmeli (remote.py ile, salt okunur).
- ~5,3 yıllık Binance verisi CAPREV ve Golden Donchian gibi seyrek kurallar için n ≥ 150'yi büyük olasılıkla vermez; 2021-06 öncesi BTC verisi (ör. başka borsa) bu taramada mevcut değil.
