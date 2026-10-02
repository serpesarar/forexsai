# Kapı ve strateji envanteri — 2026-09-30

Amaç: yeni kapı/strateji ararken **neyin işe yaradığını, neyin yaramadığını ve neden** tek yerde görmek.
Claude ve Codex aynı dosyayı örnek olarak kullanabilir.

## Nasıl okunur

**Durum**

| Etiket | Anlamı |
|---|---|
| **AKTİF** | Canlı/etkin, gerçekten bloklar veya uygular |
| **GÖLGE** | Ölçer ve loglar, bloklamaz |
| **KAPALI** | Devre dışı (çoğu kanıt yetersizliğinden) |
| **ELENDİ** | Test edildi, çöktü veya geri alındı |

**Kanıt sınıfı** (kapının kendi kanıtı için, bu envanterde kullanılan kaba ölçek)

| Sınıf | Anlamı |
|---|---|
| **A** | Gerçek para/işlem, bağımsız ikinci veri veya OOS, plasebo/permütasyon geçti |
| **B** | Tek veri seti, veya yön tutarlı ama n küçük / plasebo yok |
| **C** | Tek olay, mantık, ya da kanıtı kontrol edilmemiş |
| **X** | Çürütüldü, sızıntılı çıktı veya geri alındı |

**Kaynaklar ve güvenilirlik**
- **Bot (MT5 kutusu) durumu** 2026-09-30 01:07 UTC bot başlangıç logundan (`ayar ... (config|varsayılan)` satırları) ve kutunun `config.py`'sinden anahtar adlarıyla okundu. Mac'teki `yeni deneme/config.py` kutununkinden **farklı**; kutu esas alındı.
- **Backend (Railway) ve decider** durumu kod varsayılanları + CLAUDE.md. Railway env ve kutudaki `decider_config.py` bu oturumda **doğrulanmadı**.
- "Replay" sütunu, 2026-09-30'da `audit_skipped.py` ile yapılan reddedilen-fırsat analizidir (bkz. §5). Orada n küçük; hiçbir kapı %95'te kanıtlı değil.

---

## 1. BOT (MT5 kutusu) — giriş kapıları

| # | Kapı | Durum | Başarı / kanıt | Sınıf |
|---|---|---|---|---|
| B1 | **Sembol-yön yasağı** XAU SELL, USOIL SELL | AKTİF | USOIL SELL: 47 işlem/5 hf, WR %21,3, −0,46R/işlem, toplam −21,7R. XAU SELL araştırmada %54 (başabaş altı) | A (USOIL) / B (XAU) |
| B2 | **NDX Cuma yasağı** (Cuma tümü; hafta sonu tutma dahil) | AKTİF | Cuma ≥12 UTC n=24 −4.050$; <12 UTC n=16 +48$; permütasyon p=0,0146; hafta-çıkarma 9/9. **NDX'e özgü:** GER40'ta Cuma ≥12 pozitif (+1.047$, n=7) | A |
| B3 | **NDX ASIA yasağı** 22:00–07:00 UTC | AKTİF | n=36, WR %50, −2.139$. Faz-1 filtre paketi (ASIA+Cuma+S/R kolu kapalı+CONFIRM) iki dönemde de pozitif: dış +3.831$ (+2.224 fark), iç +4.720$ (+1.878). Replay: engellenen BUY'lar ortalamadan farksız ama Asya BUY tabanı zaten başabaşın altında | B |
| B4 | **TREND_GATE** 1h EMA50 hizası (+VIXREG) | AKTİF | 30g, 332 canlı işlem: trend-yönü n=210 WR %63,3 +9.710$; karşı-trend n=122 WR %43,4 −13.161$. 0/1/2/4/8 saat gecikmeyle hindsight testi dayandı. Replay: engellenen SELL'ler taban WR'ın **16–22 puan** altında (3 geometride de) | A− |
| B5 | **POSITION_GATE** dalga konumu (SELL ≥0,40 / BUY ≤0,60) | AKTİF | Kanıt dosyası `konum_kapisi_deneyleri_2026-09-02.md`. Replay: lift −3…−5 puan, n=52–72, yarılar geometriye göre çelişiyor | C/B |
| B6 | **TQ kapısı** Cuma + 15–17 UTC çukur (vixreg/chrev); çukurda yalnız "çok emin" | AKTİF | 385 işlem: Cuma WR %46 −3.933$ (diğer günler %57–60); VIXREG 15–17 UTC %44 −5.483$ (12–14 %67 +4.095$); CHREV 15–17 %38 −1.820$. Decider onayı istisna. Replay: lift −4…−11, n=13–14 | B |
| B7 | **CHREV ADX kapısı** ADX(30m) ≥25 | AKTİF (kod varsayılanı; kutu config'inde yok) | Tek vaka: 2026-08-05 GDAXI BUY, ADX 30,1, −687$. Replay n=3–4 | C |
| B8 | **FAKEOUT_VETO** sahte kırılım dedektörü | AKTİF (env `FAKEOUT_VETO`, varsayılan açık) | Doğru etiketlerle yalnız **NDX** OOS %70/%70'i geçiyor (SAHTE %75,4 / GERÇEK %74,2). DAX/XAU/USOIL geçmiyor. 1.757 karar satırında yalnız **1** FAKEOUT_VETO → canlı etkisi ölçülemez | A (NDX) / C (canlı) |
| B9 | **Backend Precision Veto** (MOM/SR scope'ları) | AKTİF (VETO 1.052 kayıt, 07-20→) | Alt kurallar replay'de: `premium_zone_buy` engellenenler taban −19…−27 puan (n=6–8, haklı eğilim); `mtf_strong_opposition` ayırt etmiyor (taban Temmuz rallisinde %76–92) | C/B |
| B10 | **ENTRY_SCORE_GATE** (8 koşullu skor <7) | GÖLGE | İlk kanıt +2.943$ **sızıntılıydı** (`copy_rates_from` ileri bar). Sızıntısız 45 gün: engellenecek küme +5.308$ kazandırmış; 5/6/7/8 eşiklerinin dördü de negatif. Replay lift −11/0/−3 | X |
| B11 | **VIX_REGIME_MICRO** (EMA200 karşı-rejim) | GÖLGE | Aynı otopsiden geldiği için aynı şüphe. Replay lift −11/−3/−4, yarılar çelişiyor | X/C |
| B12 | **Backend advice/veto** (VIXREG, CHREV) | GÖLGE | "Veto etseydi ne olurdu" verisi bekleniyor. Replay `backend_veto_shadow` lift −5/−1/−5 (n=9–12) | C |
| B13 | **POS_TIGHT** sıkı konum (SELL ≥0,60 / BUY ≤0,40) | GÖLGE (09-02 canlıya alındı, **09-05 geri alındı**) | Kanıt sahte çoğaltmayla şişmişti: GDAXI "22W/55L, z=−6,47" aslında **14 bağımsız epizod** (8,1× şişme). Epizod bazında GDAXI BUY 2W/6L p=0,022 → Bonferroni (p<0,0083) geçmiyor. Replay: engellenen SELL'ler ortalamanın **üstünde** (+4…+21, n=10) → kapı yanlış olabilir ipucu | X |
| B14 | **SQZ filtresi** ATR14/ATR100(1m) ≥1,0 | GÖLGE | Elenecek küme dış n=122 −4.399$, kalan +6.802$; 4 ailenin 4'ünde aynı yön. **Ama** plasebo yalnız 1,00'da geçiyor (p=0,043; 0,95→0,217; 1,05→0,073); 3. çeyrek filtreyle de negatif. Go-live kartı ölçüt 3 geçilmedi | B |
| B15 | **USOIL_SESSION_GATE** 13 UTC öncesi USOIL BUY | GÖLGE | 950 pulse BUY: 13–23 UTC +8,8 cR vs 0–12 UTC −4,5 cR; bot 74 giriş 2.276$→3.937$. Kart geçilemedi: gün-blok bootstrap %81 (<%90), tek-pozisyon kısıtında toplam kazanç yok | B |
| B16 | **SELL_RSI** (5m RSI >55 "güce sat") | GÖLGE | Yalnız ölçüm | C |
| B17 | **USOIL_BREAKOUT** scope | GÖLGE (`USOIL_BREAKOUT_LIVE=False`) | 368 olay, gerçek M1+spread: WR %42,7, ort −0,147R, P(EV>0)=%0,3. Rapor %58,8 demişti; giriş bar kapanışından ve spread'siz ölçülmüştü | X |
| B18 | **S/R-limit giriş kolu** (NDX) | KAPALI (kutu config) | Faz-1 paketinin parçası | B |
| B19 | **CONFIRM zorunlu + zone çıtası 4** | AKTİF (`PHASE1_CONFIG_RESTORE=True`) | Faz-1 paketiyle birlikte ölçüldü (B3), tek başına ayrılmadı | C |

## 2. BOT — giriş sonrası / yürütme

| # | Mekanizma | Durum | Başarı / kanıt | Sınıf |
|---|---|---|---|---|
| M1 | **Probasyon MOD-E** (sinyalden 5 bar sonra, gürültü bandı geçilmediyse gir) | **Kutuda CANLI** (`PROBATION_LIVE=True` config; repo varsayılanı gölge) | Dış n=112 +3.691$ / iç n=126 +7.582$, filtresiz. Faz-0'ın elenen kurallarının aksine iki dönemde pozitif. Replay: `probation_cancel` n=2 | B+ |
| M2 | **REENTRY** (ana işlem kapanınca aynı yönde bir kez daha) | **Kutuda CANLI** (`REENTRY_MODE=live` config; repo varsayılanı gölge) | Bağımsızlık ✓, eşit-risk alfa ✓ (iç +12.462$ / dış +3.850$), **plasebo dış örneklemde ❌ (p=0,187)**. Belge "2–4 hafta gölge sonrası live" diyordu | C |
| M3 | **NDX BUY: BE@30dk + kazananı-koştur (TP kaldır, 0,6R trail)** | AKTİF (`TRADE_MGMT_ENABLED`) | 223 NDX işlem: Δ+29,5R P=%100 (haftalık dilim doğrulamalı). **Tek dönem, örneklem içi** | B |
| M4 | **DAX BUY kazananı-koştur** | AKTİF | Δ+12,1R P=%98,3 | B |
| M5 | **VIXREG SELL sabır kapısı** (10 dk) | **KAPALI** (kutuda `VIXREG_SELL_PATIENCE=False` varsayılan) | Δ+39,3R. Hafıza "canlıya bağlandı" diyor; kutu log'u kapalı → **tutarsızlık** | B |
| M6 | **Koşullu BE** (MFE ≥0,5R) | AKTİF | Belge: replay BE'siz koşuyor, koşullu hâli test **edilemedi**; eski zaman-tabanlı BE aleyhe olduğu için bırakıldı. 09-29 analizi "kâra geçince BE kurtardığından çok kazanan öldürür" diyor (farklı eşik, yine de çelişki riski) | C |
| M7 | **Zaman stopu 240 dk** | KAPALI | Dış örneklem −1.900$ (iç +760$); işaret kararsız | X |
| M8 | **TP = 2,5×ATR70(1m)** | KAPALI | WR iki dönemde yükseldi (+9/+11,8 puan) ama para yalnız iç örneklemde: dış −211$. "Küçük hedef yüksek WR kozmetiği" | X |
| M9 | **BE/kilit/zikzak kuralları (50+ varyant, 487 işlem)** | ELENDİ | Her eşikte kurtarılandan çok kazanan ölüyor (BE@%60: 54 kurtar / 75 öldür, −4.007$). Zikzak kilidi 44.064 varyantta hiçbir (sembol,yön) grubunda 6/6 dilim tutmadı; USOIL BUY kilidi bağımsız sette −8,1R | X |
| M10 | **SHADOW_LOCK** (USOIL, zikzak kâr kilidi) | GÖLGE | Yalnız "tetiklendi/vurulurdu" kaydı | X |
| M11 | **USOIL_BUY_TP_RR=1,0** | KAPALI | RR 1,0 > RR 0,7 her kesitte (bootstrap P=%99,6), **ama scope'un kendisi 1. yarıda negatif** | B |
| M12 | **BACKEND_BASIS_TOL 0,25%** (backend SL fiyat tabanı koruması) | AKTİF | 2026-09-29 olay: backend emtia mumları Yahoo vadelisine düşünce SL mesafesi besleme farkına eşitlenmişti (ticket 390567007 SL 3.064$). Olay-bazlı | A (olay) |
| M13 | **Reflex engine** | GÖLGE (`REFLEX_LIVE=False`) — **canlıya alınmamalı** | ~~mom_cont 2026 transfer +0,29R~~ → 2026-09-30: araştırma dedektörü (`triggers/detect.py`) teyidi gerilme kararını veren 15m diliminin İÇİNDE arıyor (geleceğe bakma). Aynı icrayla sızıntılı +0,88R, sızıntısız (üretim servisinin kodu) **−0,08R** (P(EV>0)=%13), araştırma geometrisinde −0,19R. Kanıt `research/ndx_gate_forge/momcont.py` | X |

## 3. BACKEND (panel, `signal_gates.py`) — sinyal kapıları

| # | Kapı | Durum (kod varsayılanı / CLAUDE.md) | Başarı / kanıt | Sınıf |
|---|---|---|---|---|
| K1 | **VIX_REGIME_GATE** (VIX ≥18,4 → BUY lehte, altı → SELL) | AKTİF (`BLOCK=1`) | Ön-kanıt plasebo p=0, OOS +17pp. 30g gölge-eşdeğeri n=1.098: lehte %58,0 vs karşıt %42,5 (+15,5pp) | A |
| K2 | **PATTERN_BONUS_GATE** (formasyon teyit bonusunu ölçülen kaybeden yönlerde geri çek) | AKTİF, salt supresif | Formasyon SELL 26/115 = %22,6 (p≈3e-9, 4 sembolün 4'ü kaybediyor); NDX BUY 2/22 = %9,1. Formasyon BUY %50 (n=124) → dokunulmadı | A |
| K3 | **NDX SMC SELL kapısı** (H4 close>EMA50'de counter-trend SELL) | AKTİF | 14 gün: 1 kazanç / 28 kayıp. Kısa pencere | B |
| K4 | **TQ_GATE** (NDX 16/17/19 UTC, USOIL Perşembe çukuru; güven <80 → HOLD; NDX 13–14 UTC altın) | AKTİF (`BLOCK=1`) | NDX 13–14 UTC %58 (n=683, p<1e-4); 16/19 UTC %45; USOIL Perşembe %35 (n=941). **Not:** panel `prediction_logs` sonuçlarına dayanıyor (çözümleme geçmişte güvenilmez çıktı) | B− |
| K5 | **SESSION_GATES** (XAU 20, 01–02; GDAXI 07; NDX 03–04, 18, 22; USOIL 00–11 UTC) | AKTİF | NDX {3,4,18,22} ΔPnL +5.078$, USOIL 00–11 +1.868$ — **aynı otopsi raporundan** (entry-score ile aynı; saat bölümü sızıntısızlık açısından yeniden doğrulanmadı) | C |
| K6 | **CALENDAR_GATE** (yüksek etkili olay ±30 dk) | AKTİF, fail-open | Ölçülmüş kanıt yok | C |
| K7 | **XAU trend SELL kapısı**, **GDAXI pulse1 askısı** (60g WR %25) | AKTİF | Gösterge denetimi 2026-07-01. XAU intraday zaten kapalı | B/C |
| K8 | **ENTRY_SCORE_GATE** (backend) | GÖLGE (kod varsayılanı `BLOCK=0`; CLAUDE.md'de "blokluyor" yazıyor → **tutarsız**, Railway env doğrulanmadı) | Kapı sinyallerin %63'ünü eliyor, toplam R +1.580 → +626; eşiklerin hiçbiri kapısız hâli geçmiyor | X |
| K9 | **TREND_ALIGN_GATE** (NDX pulse 1h EMA50) | GÖLGE | Bot'ta B4 olarak kanıtlı (%63,3 vs %43,4); backend'de gölge ölçüm sürüyor | A− (bot verisiyle) |
| K10 | **WAVE_POSITION_GATE** (4h dalga) | GÖLGE | Bkz. B5/B13 | C |
| K11 | **FAKEOUT_GATE** | GÖLGE (`BLOCK=0`) | Bkz. B8 | A (NDX) |
| K12 | **XAU_SCALP_GATE** | GÖLGE | 30g pulse WR %16–18; atr_ladder epoch'u ölçülmeden bloklanmıyor | C |
| K13 | **DEBATE_BIAS_GATE** | GÖLGE | n=18 erken kanıt; debate tersine çevirme "bedava öğle yemeği değil" (NDX %52,9, USOIL negatif) | X/C |
| K14 | **Precision Veto — MiroShark makro bias** (NDX-only) | Bayrak açık (`MACRO_BIAS_ENABLED=1`); bias kaynağı (webhook/manual) kurulmadığı için büyük olasılıkla **fiilen etkisiz** (hafıza 07-08, doğrulanmadı) | Bias isabeti temiz ölçümde %42,6 vs baseline %57,4, %70 ayı yanlılığı → kanıt olumsuz; etkisi ayrı ölçülmedi | X/C |

## 4. CLAUDE DECIDER (kod varsayılanları; kutudaki `decider_config.py` doğrulanmadı)

| # | Kapı | Durum | Başarı / kanıt | Sınıf |
|---|---|---|---|---|
| D1 | **ALLOW listesi**: NDX BUY/SELL, GDAXI BUY/SELL, USOIL SELL, XAU BUY; yasak USOIL BUY, XAU SELL | AKTİF | Yeniden damıtma (nested-CV OOS, plasebo p=0). Canlıda vaat şişik çıktı (%90–100 vaadi canlıda %55) | B |
| D2 | **Giriş kalitesi**: `chz_dir ≥2,0` (bıçak yakalama) veya `vol_ratio ≥1,5` | GÖLGE | Gerçek n=1.515: elenen n=434 EV −0,069R (P(EV>0)=%4,2), kalan +0,036R (%93,7); karşı-olgu n=4.350 aynı yön; her iki yarı ve 4 sembol aynı işaret; plasebo p=0,0085. **Yine de sistem başabaşta: "seçim alfası yok"** | A− |
| D3 | **Rejim kapısı**: VIX ≥18,4'te NDX SELL açma | GÖLGE | Gerçek n=21 WR %38,1 EV −0,364R; karşı-olgu n=25 %40,0; plasebo p=0,020. Havuz geneli çürüdü, USOIL SELL gergin bantta tersine (+0,113R) → kapsam yalnız NDX | B |
| D4 | **Fakeout köprüsü** | AKTİF (bağlam) | Bkz. B8 | B |
| D5 | **Takvim yakınlığı** ±30 dk | AKTİF | Backend CALENDAR_GATE ile aynı | C |

## 5. Reddedilen-fırsat replay sonucu (2026-09-30)

Yöntem: kapı-atlama kayıtları 1m barla, aynı niyet tek fırsat sayılarak çözüldü; simülatör botun gerçek TP/SL'lerinin **%98,6'sını** (274/278) yeniden üretiyor. "Taban" = aynı tarih ve saat dağılımında kapısız giriş. Fark = engellenen WR − taban. Üç geometri: 80/110 · 80/60 · 80/80.

| Kapı (yön) | Fırsat n (3 geo.) | Fark, puan (3 geo.) | Okuma |
|---|---|---|---|
| trend_gate (SELL) | 11 / 18 / 15 | −22 / −16 / −18 | Engellenenler gerçekten kötü → kapı bilgi taşıyor |
| premium_zone_buy vetosu (BUY) | 6 / 8 / 8 | −23 / −19 / −27 | Aynı, n çok küçük |
| tq_cool (SELL) | 13 / 14 / 13 | −11 / −4 / −9 | Hafif haklı eğilim |
| position_gate (SELL) | 52 / 72 / 59 | −3 / −4 / −5 | Zayıf haklı eğilim |
| backend_veto_shadow (SELL) | 9 / 12 / 11 | −5 / −1 / −5 | Ayırt etmiyor |
| entry_score_gate_shadow (SELL) | 16 / 19 / 19 | −11 / 0 / −3 | Ayırt etmiyor (bkz. X) |
| vixreg_micro_gate_shadow (SELL) | 11 / 14 / 14 | −11 / −3 / −4 | Ayırt etmiyor |
| entry_window_gate (BUY) | 136 / 241 / 182 | +3 / −1 / +4 | Kapı seçici değil; ama Asya BUY tabanı zaten −EV, yasak parayı tutuyor |
| mtf_strong_opposition (BUY) | 7 / 7 / 7 | −6 / +10 / −2 | Temmuz rallisinde BUY tabanı %92 → "yanlış görünmesi" sürüklenme |
| **shadow:pos_tight (SELL)** | 10 / 10 / 10 | **+4 / +21 / +16** | Tek "kapı yanlış olabilir" ipucu; yarılar çelişiyor |

**Hiçbir kapı %95'te kanıtlı değil** (kapı başına 10–20 bağımsız fırsat; ±25 puan güven aralığı).

## 6. Stratejiler (kapı değil, giriş kaynağı)

| Strateji | Durum | Sonuç |
|---|---|---|
| **VIXREG** (VIX rejimi → NDX yönü, 80/110) | AKTİF | 07-01→08-27: n=211, 123 TP / 87 SL, +3.291$. Makro→NDX plasebo p=0, OOS +17pp |
| **CHREV** (kanal-sınır dönüşü, mean-reversion) | AKTİF | Araştırma OOS WR %44→72–84; canlı 07-01→08-27 n=26, −1.024$ (canlı araştırmanın altında) |
| **MOM/SR** momentum-continuation | AKTİF | n=21, +381$. Doğrulanmış tek giriş tipi; S/R reaksiyon girişleri −EV |
| **DAYCOMBO** | AKTİF | n=19 (14 TP/5 SL), +583$; kendi geometrisiyle WR %72–79 |
| **REENTRY** | AKTİF (kutu) | n=5, +1.056$ (çok küçük) |
| **XAU günlük swing** (Donchian kırılımı + EMA200, yalnız BUY) | (hafıza: doğrulanmış) | %64,5 WR, +0,69R, tüm walk-forward katlar pozitif. XAU intraday kapalı |
| **USOIL breakout**, **NDX reflex** | GÖLGE | Bkz. B17, M13 |
| **Pulse1/2/3 ters çevirme (inversion)** | GÖLGE | Dürüst WR ~%55–62 (%90 değil), trend-bağımlı |

## 7. Örüntüler — yeni kapı ararken bunlardan çıkan dersler

**Tutanlar**
1. **Zaman/takvim hücreleri, gerçek parayla ve permütasyonla** (Cuma, ASIA, TQ çukuru). Ama **NDX'e özgü**; DAX'ta Cuma pozitif çıktı, genellenmedi.
2. **Trend yönü hizası ve VIX rejimi** iki bağımsız veri setinde aynı yönde (TREND_GATE 332 işlem, VIX 1.098 sinyal + OOS).
3. **Yön-bazlı kayıp kaynağı** (USOIL SELL, formasyon SELL, NDX SMC SELL): tek bir yön sistematik kaybediyorsa, "hiç açma" en ucuz kapı.
4. **Girişi geciktiren doğrulama** (probasyon, fakeout +1-bar teyit): iki dönemde pozitif çıkan nadir fikirler.

**Çökenler**
1. **Çok koşullu skor kapıları** (ENTRY_SCORE, 8 koşul): sızıntısız ölçümde aleyhe.
2. **"WR yükselir" ≠ "para yükselir"**: ATR-TP, BE/kilit, zaman stopu WR'ı artırıp parayı azalttı (kazançlar küçülür, kayıplar aynı kalır).
3. **Backtest'te iyi, gölge/canlıda kötü**: konum kapısı sıkı eşik (backtest +8.401$ vs +4.290$ derken canlı gölge tersini söyledi).
4. **Küçük alt kümede %100**: tMP 19/19 → bağımsız dönemde 10/20 (−2.151$); en kötü görünen kova sonra en iyi çıktı.
5. **Sürüklenme**: Temmuz rallisinde kapısız BUY tabanı %92 → "engellenen BUY kazanırdı" bulgusu kapı hakkında bir şey söylemiyor.

## 8. Kanıt hataları — kapıyı önermeden önce bunlara karşı kontrol et

| Vaka | Etki |
|---|---|
| `mt5.copy_rates_from` tarihten **ileriye** bar döndürür (`research/_bars_upto.py` kullan) | Entry-score kapısının ilk kanıtı +2.943$ sızıntılıydı, sızıntısızda aleyhe |
| `candle_cache` 1m 2026-02→05 partisi broker saatinde (+3s), 315.730 satır | Fakeout dedektör etiketleri kaymıştı; yalnız NDX çıtayı geçti |
| Export offset +1230 dk (2026-08-30) | Sahte "Cumartesi anomalisi" (aslında Cuma −4.002$) |
| Tarama döngüsü aynı koşulu 60–75 sn'de bir kaydetti | POS_TIGHT GDAXI "p≈1e-10" → 8,1× şişme, gerçekte p=0,022 ve Bonferroni geçmiyor |
| Giriş = sinyal barı kapanışı + spread'siz | USOIL breakout %58,8 → gerçek icrada %42,7 / −0,147R; 5 günde −895$ |
| Backend sonuç çözümlemesi | XAU pulse2 SELL backend %2,9 vs 1m dürüst %61 |
| Aynı dakikada bölünmüş bacaklar | n şişer; bağımsız karar sayısı çok daha az |
| Panel BUY'ın demo ML sabitinden gelmesi; meta %77/%79 epoch karışımı | Sızıntısız gerçek WR %62,9, ort R −0,059 |
| Yerel `config.py` ≠ kutu config'i | Envanter yanlış durumu gösterir |

**Zorunlu kıyas:** her aday kapıyı (a) kapısız taban WR ile (aynı dönem+saat), (b) başabaş WR'la, (c) bağımsız sonraki dönemde, (d) birden fazla TP/SL geometrisinde, (e) karar sayısıyla (n değil) değerlendir. Wilson aralığı başabaşı içeriyorsa "kanıtlı" deme. Araç: `.agents/skills/trade-edge-lab/` (`audit_trades.py`, `audit_skipped.py`).

## 9. Takip edilmesi gereken tutarsızlıklar

1. **PROBATION ve REENTRY kutuda canlı**, repo varsayılanı gölge; REENTRY'nin plasebosu dış örneklemde geçmedi (p=0,187).
2. **VIXREG_SELL_PATIENCE** hafızada "canlıya bağlandı", kutuda kapalı.
3. **Koşullu BE** açık; 09-29 analizi BE/kilit kurallarını reddediyor. Aynı kural değil ama çelişki riski; koşullu BE replay'de hiç test edilmedi.
4. **Backend ENTRY_SCORE**: CLAUDE.md "blokluyor", kod varsayılanı gölge. Railway env doğrulanmalı.
5. **Yerel vs kutu config**: örn. yerelde `VIXREG_SELL_PATIENCE=True`, kutuda yok.
6. **SESSION_GATES (K5)** entry-score ile aynı otopsiden; sızıntı kontrolü yapılmadı.
7. **Decider** kutu config'i bu envanterde okunmadı.

## 10. 2026-09-30 Kapı Dökümhanesi adayları (`research/ndx_gate_forge/RAPOR.md`)

Genel girişlerde tek-özellikli piyasa-durumu kapıları plasebodan ayırt edilemedi (780 hücre: 13 geçen vs plasebo 16,4);
saat/gün sürüklenme takvimi çağlar arasında taşınmıyor (2016-20 → 2021-26 korelasyon 0,0085). Kalan adaylar (hepsi GÖLGE önerisi):

| # | Aday | Kanıt özeti | Sınıf |
|---|---|---|---|
| K5 | Stres-dönüş: dün NDX ≤ −%1,5 veya 5g ≤ −%4 → SELL yok | 10y iki çağda aynı işaret; 30m 4/6, 1m 3/4; **bot SELL: bloklanan−kalan −17 p, gün-bloklu P=0,974 (10 gün)** | B− |
| K6 | Aşırı uzama: NDX 200g ort. +%10 üstü → BUY yok | 10y 7/9; 30m 5/6, 15m 4/4, 1m 4/5; bot BUY +4,6 p vs +46,8 p; vekil portföyde zararlı | C+ |
| K1 | Pazartesi SELL yok | 30m 6/6, 15m 4/4, 1m 4/5, 10y 8/11 — son çağa özgü; bot kararlarında nötr | B− genel / C bot |
| K3 | Ay sonu son 2 gün, ay-içi ±%4 → akışa karşı yön yok | 10y 6/8 & 4/4; 1m 4/5 (19 gün); nadir | C+ |

Veri hatası: candle_cache NDX 1m 2026-02-10→03-08 etiketleri **60 dk erken** (bu dönemi saat-bazlı kullanan araştırmalar etkilenir).

### 10.1 Tur 3 (2026-10-02, iki ajan raporunun karşılaştırması — `research/ndx_gate_forge/NIHAI_RAPOR.md`)
| # | Aday | Kanıt | Sınıf |
|---|---|---|---|
| S1 | **CAPREV kapitülasyon alımı** (yeni strateji): stres günü + VIX≥18,4 + NY 03–15 önceki RTH dibi altında ilk kapanış → BUY, 1×gvol stop, 16:00 çıkış | 10y 1h +0,31 gvol 8/10 yıl; 30m +0,48 6/6; 15m +0,87 4/4; stressiz-gün/rastgele-saat kontrolleri ≈0, aynı olayda SELL −0,29…−0,48 | B+ |
| K8 | **Kovalama endeksi ≥3 → SELL yok** (5m kanal yönde ≥1σ, M15 hizalı, önceki RTH dibi altı, çok-günlük düşüş) | bot SELL monoton +28,8/+3,1/−1,2/−5,9/−38,9 p; genel 1m 4/5 P=.95 | B− |
| — | VIXREG M15 karşıtlığı (diğer ajanın betimsel bulgusu) | botta −5,1 vs +10,4 p ama genel 5 dönemde 3/5 karışık → genelleşmiyor | C |

### 10.2 Tur 4 (2026-10-02, `ndx_synthesis_20261002` ile karşılaştırma — NIHAI_RAPOR v2)
| # | Aday | Kanıt | Sınıf |
|---|---|---|---|
| S1' | **CAPREV-2** stres(dün≤−%1,5 / 5g≤−%4) ∧ VIX≥18,4 günü: kademe 1 NY 09:30 BUY → 16:00; kademe 2 önceki RTH dibi altında ilk kapanış → BUY → ertesi gün 16:00; 1×gvol stop | NDX 1h/30m/15m ertesi gün +0,34/+0,45/+0,77; **DAX (bağımsız) +0,35/+0,47**; QQQ günlük 10/11 yıl; saat plasebosu %100; 10y 223 olay günü | B+ |
| — | Stressiz ∧ yüksek VIX dip kırılımı alımı | NDX ≈0, DAX ≈0 → elendi | X |
| — | Kovalama endeksi | diğer ajanın portföyünde +0,30R → bota özgü (C+); K5b'yi içermez | C+ |
