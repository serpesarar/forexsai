# Decider XAUUSD — önceki kanıt, ölü/canlı mekanizmalar ve decider'ın XAU karar mantığı (2026-10-15)

> Kapsam: repo içi belge/kod/hafıza + Supabase (salt-okuma) + kutu sağlık kontrolü. Web araması yok.
> Kaynak biçimi: `dosya:satır` (repo kökü `/Users/melihcanodacioglu/Desktop/panel`), hafıza notları
> `~/.claude/projects/-Users-melihcanodacioglu-Desktop-panel/memory/<ad>.md`, Supabase sorguları "SQL:" ile.

---

## 1. Kapı kayıt defterinde XAU için denenmiş her fikir — verdikt, sayı, neden

### Takeaway
XAU'da **ayakta kalan tek sağlam kanıt yapısal BUY yanlılığı + yavaş zaman ölçeğinde trend takibi**dir (günlük Donchian BUY+EMA200; 1h "yeni 20-mum tepesi BUY" gölgede). SELL'in her biçimi, 1m/5m scalp, makro yön, mum formasyonları, fakeout-işlem, gösterge-eşik kuralları ve BE/kilit çıkışları **ölü**. Decider'ın XAU'daki tek ölçülmüş "yanlış→doğru" geçişi yön değil **geometri** (SL 2,5→1,5 ATR) oldu.

### Cited Findings
**Defterin zorunlu süreci ve tuzakları (yeni XAU araştırmasına doğrudan uygulanır)**
- §0: önce §2'de ara; ön-kayıt (`PROTOCOL.md`), kapısız **taban (dönem × yön × UTC saati)**, başabaş, bağımsız sonraki dönem, birden fazla geometri, bağımsız karar sayısı, plasebo zorunlu; "Çıplak WR yasak — beklenti (R) + epoch" — [docs/KAPI_KAYIT_DEFTERI.md:11-21](docs/KAPI_KAYIT_DEFTERI.md)
- XAU'yu doğrudan vuran §1 tuzakları: E1 `copy_rates_from` ileriye bakar (`_bars_upto.py`); E2 MT5 `time` = broker sunucu saati UTC+2/+3; E6 aynı koşulun 60–75 sn'de bir tekrar kaydı (n şişmesi); E7 giriş = sinyal barı kapanışı+spread'siz (doğrusu sonraki M1 açılışı + gerçek spread); E8 backend çözümlemesi güvenilmez (**XAU pulse2 SELL backend %2,9 vs 1m dürüst %61**); E13 sürüklenme tabanı ("yükselen piyasada kapısız BUY tabanı %92"); E14 WR↑≠para↑; E21 **backend emtia mumları 09-03'ten beri Yahoo vadelisi (USOIL/XAU)**; E22 panel-sinyali scope'ları bar verisinden yeniden üretilemez; E23 aynı geçmişe çok tur bakma; E24 çok özellikten seçilen alt grup için seçim-düzeltmeli maks. istatistik şart — [docs/KAPI_KAYIT_DEFTERI.md:30-59](docs/KAPI_KAYIT_DEFTERI.md)

**XAU satırları (ID → durum → sayı → neden)**
- **B1** XAU SELL (ve USOIL SELL) yasağı — AKTİF, A/B — [KAPI_KAYIT_DEFTERI.md:70](docs/KAPI_KAYIT_DEFTERI.md); envanterde "XAU SELL araştırmada %54 (başabaş altı)", sınıf B — [docs/KAPI_ENVANTERI_2026-09-30.md:37](docs/KAPI_ENVANTERI_2026-09-30.md)
- **K7** XAU trend SELL kapısı (backend) — AKTİF B/C; **K12** XAU_SCALP_GATE — GÖLGE, C ("30g pulse WR %16–18") — [KAPI_KAYIT_DEFTERI.md:105-106](docs/KAPI_KAYIT_DEFTERI.md); [KAPI_ENVANTERI_2026-09-30.md:85,90](docs/KAPI_ENVANTERI_2026-09-30.md)
- **K5** SESSION_GATES içinde XAU 20 ve 01–02 UTC bloğu — AKTİF ama **C** (aynı otopsiden, saat bölümü sızıntısızlık açısından yeniden doğrulanmadı) — [KAPI_ENVANTERI_2026-09-30.md:83](docs/KAPI_ENVANTERI_2026-09-30.md)
- **D1** decider ALLOW listesi XAU BUY izinli / XAU SELL yasak — AKTİF, B ("canlıda vaat şişik çıktı (%90–100 vaadi canlıda %55)") — [KAPI_ENVANTERI_2026-09-30.md:98](docs/KAPI_ENVANTERI_2026-09-30.md)
- **D2** decider giriş-kalitesi `chz_dir≥2,0 veya vol≥1,5` — GÖLGE, A− (decider'da; bota taşınmaz) — [KAPI_KAYIT_DEFTERI.md:107](docs/KAPI_KAYIT_DEFTERI.md)
- **XAU günlük swing (Donchian + EMA200, yalnız BUY)** — "doğrulanmış", %64,5 WR +0,69R, tüm WF katları +; "XAU intraday kapalı" — [KAPI_KAYIT_DEFTERI.md:117](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-01** (2026-05-29) XAU/NDX/USOIL/DAX 1m scalp: "yok … XAU/DAX zayıf brüt sinyal spread'e yenik" — X — [KAPI_KAYIT_DEFTERI.md:124](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-02** (2026-06-10) WIN/LOSS gösterge AUC: "XAU yalnız BUY" — C — [KAPI_KAYIT_DEFTERI.md:125](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-04** (2026-06-14) 5 yeni yön: "XAU SELL friction'a yenik; NDX SELL/XAU BUY tutuldu" (onaylanmadı, bağlanmadı) — A — [KAPI_KAYIT_DEFTERI.md:127](docs/KAPI_KAYIT_DEFTERI.md); backlog `bl_ndx_sell_xau_buy` "bataryayı (momentum_5dir_oos.py) taze veriyle tekrar koş" hâlâ açık — [backend/data/evolution/backlog.json:36-38](backend/data/evolution/backlog.json)
- **OLD-07** (2026-06-16/17) XAU intraday + makro yön + meta stop: "M15 bounce/breakout friction'a yenik; makro bağlar 2024-26'da işaret çevirdi; yalnız günlük swing çalışıyor; 'yüksek WR' geniş stop gerektiriyor" — X — [KAPI_KAYIT_DEFTERI.md:130](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-10** makro→yön: "XAU'da makro YOK" — [KAPI_KAYIT_DEFTERI.md:133](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-11** (2026-07-02) XAU inverse-shadow 1m dürüst: "ters -EV ama RR≥0,8 +EV, trend-bağımlı" — C — [KAPI_KAYIT_DEFTERI.md:134](docs/KAPI_KAYIT_DEFTERI.md)
- **OLD-17** fakeout dedektörü: 08-12 yeniden üretimde yalnız NDX %70/%70 geçti; XAU SAHTE %66,3 / GERÇEK %71,4 (eski iddia %71,7/%93,1) ❌ — [KAPI_KAYIT_DEFTERI.md:140](docs/KAPI_KAYIT_DEFTERI.md); tablo: CLAUDE.md "Fakeout Radar" bölümü
- **CK-02** fakeout dedektörü işlem kartı: 786 karar net −0,068R P %1; **XAU −0,068** → işlem stratejisi olarak elendi — X — [KAPI_KAYIT_DEFTERI.md:224](docs/KAPI_KAYIT_DEFTERI.md)
- **IO-18** tekrar-SL ortak tipleri: "DAX/USOIL/XAU/NDX BUY: yok; benzer işlemler sonucu tekrarlamıyor (genel piyasa AUC 0,46–0,50)" — [KAPI_KAYIT_DEFTERI.md:212](docs/KAPI_KAYIT_DEFTERI.md)
- **IO-12** (2026-10-08) decider sembol başına kural araması: "iki yönde geçen kural gerçek 138 vs plasebo medyan 142 (79–177) → gösterge-eşik kuralı YOK. Seçim değeri: XAU BUY +0,20R (OPEN +0,06 vs WAIT-cf −0,14, iki yarıda +)" — X (eşik kuralları) — [KAPI_KAYIT_DEFTERI.md:218](docs/KAPI_KAYIT_DEFTERI.md); ayrıntı: XAU BUY OPEN +0,06 (n=99) vs WAIT-cf −0,14 (n=208, P(>0)=%0), yarılar +0,05/+0,07; **XAU SELL −0,21 (n=19)**; XAU Spearman eğitim↔sınama +0,25/+0,08 — [research/decider_kural_20261008/SONUC.md:12-26](research/decider_kural_20261008/SONUC.md)
- **MK-03** "Yeni 20-mum tepesinde BUY, 20 mum" bağımsız piyasa sınavı XAU+USOIL 15m/30m/1h: **geçmedi** (genel hipotez); "altında ayna 'yeni dip SELL' de pozitif → altın iki yönlü trend, petrol dönüş" — X (genel) — [KAPI_KAYIT_DEFTERI.md:192](docs/KAPI_KAYIT_DEFTERI.md)
- **MK-04** XAU 1h yeni tepe BUY (post-hoc alt küme): stopsuz kart 6/6 (1.563 işlem, +0,324R vs rastgele BUY +0,160, 9/11 yıl, en iyi 5 gün hariç +420R) ama en kötü −21,7R; **SL 1,5×ATR** sürümü +0,107R vs aynı stoplu rastgele +0,042 (max +0,093), 9/11 yıl, P %99,2 — **icra ölçütü ✗** (kapanış-girişi +0,169) → SHADOW, B−; gölge 2026-10-12'de kuruldu (`yeni deneme/xau_shadow.py`, `xau_shadow.jsonl`, sadakat 1856/1857) — [KAPI_KAYIT_DEFTERI.md:193](docs/KAPI_KAYIT_DEFTERI.md)
  - Kart JSON'u: 1.857 olay, ortR +0,107, taban (rastgele BUY aynı stop) +0,042 (max +0,093), P %99,2, yarılar +0,068/+0,147, spread×1,5 +0,081, **kapanış-girişi +0,169 vs gerçek +0,107 → 5. ölçüt ✗**, yıllar 2016 +0,095 … 2018 **−0,255**, 2021 **−0,044**, 2025 +0,346; uyarı "SL 1,5 dört stoptan seçildi; 2016-26 altın boğa piyasası" — [backend/data/evolution/go_live_cards/xau_1h_yeni_tepe_buy_sl15.json](backend/data/evolution/go_live_cards/xau_1h_yeni_tepe_buy_sl15.json)
- **MK-05** mum formasyonu taraması XAU 15m/30m/1h: 6 geçen vs plasebo ort 5,1 (%95 9,1) → kenar yok; 6'sının 6'sı kasada (2026-06→09) düştü — X — [KAPI_KAYIT_DEFTERI.md:194](docs/KAPI_KAYIT_DEFTERI.md); ham log [research/pinbar_20261010/results/scan_symbol.log](research/pinbar_20261010/results/scan_symbol.log)
- **M9** BE/kilit/zikzak (50+ varyant, 487 işlem) ELENDİ; **IO-07/IO-08/IO-10** erken çıkış, SL×/TP× geometri, TP%f→kilit hepsi negatif/sıfır — [KAPI_KAYIT_DEFTERI.md:97,207-208,222](docs/KAPI_KAYIT_DEFTERI.md)

**§3 meta-dersler (XAU tasarımına bağlanan)**
- (1) "Rastgele girişte tek-özellikli durum kapısı yok… kenar ya günlük rejimde ya stratejinin kendi yapısında (geometri, zaman çıkışı) aranmalı"; (2) "Korku döner, coşku dönmez" (NDX/DAX için kanıtlandı); (5) "Braket ≠ zaman… kenar zaman çıkışında"; (7) "Yüksek WR ≠ kenar"; (8) E[PnL]=μ·E[τ], E[τ]≈TP·SL/σ²; (9) sızıntı denetimi önce — [KAPI_KAYIT_DEFTERI.md:245-254](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- **"Korku döner, coşku dönmez" XAU'ya taşınmaz.** NDX/DAX'ta kanıtlanan ilke (yukarı aşırılık devam, aşağı aşırılık döner) XAU'da ters işaretli görünüyor: MK-03'te XAU "yeni dip SELL" de pozitif ("iki yönlü trend"), ama XAU SELL'in her uygulaması (decider −0,21R n=19, evidence base OOS %15, araştırma %54 başabaş altı) kaybetti. XAU'nun kanıtlı mekanizması **trend devamı (kırılımı al)** + **pozitif sürüklenme**; mean-reversion ("dipten al") değil — günlük swing'de "Oversold-DIP 2nd entry REJECTED… gold edge is buying strength not weakness" (bkz. §2).
- XAU'da kanıt sınıfı A olan hiçbir giriş kuralı yok; en güçlüler: günlük Donchian (B — tek boğa döngüsü, 31 işlem) ve MK-04 (B− — post-hoc, icra ölçütü ✗). Her ikisi de **saatler-günler** ölçeğinde; decider'ın 5m/~17 dk ölçeği bu kanıtların hiçbirinin kapsamında değil.
- Yeni XAU kuralı tasarlayan araştırmacı, aynı 2016–2026 1h candle_cache serisine MK-03/04/05 ile zaten en az 3 tur bakıldığını hesaba katmalı (E23) → bağımsız veri (Dukascopy XAU, farklı broker, 2026-10 sonrası ileri gölge) gerekli.

### Gaps
- XAU "timelapse" gölge scope'unun (bot `check_shadow_scopes`, iddia "B varyantı BUY +55,3R / SELL +103,7R") 1m replay karnesinin sonucu bulunamadı; commit e241f102 yalnız aracı ekliyor (`backend/research/xau_shadow_replay.py`), sonuç raporu repoda yok.
- MK-04 gölgesinin (2026-10-12'den beri) ilk sonuçları kutuda (`yeni deneme/xau_shadow.jsonl`); kutu çevrimdışı olduğu için okunamadı (bkz. §5).

---

## 2. Hafıza notları — iddialar ve kodla doğrulama

### Takeaway
Hafıza notlarının çoğu kodla tutarlı, ancak **XAU stop kuralı konusunda iki çelişkili ders hâlâ prompt'lara giriyor**: kod 2026-07-27'de XAU stop'unu 2,5→1,5 ATR'ye çekti, fakat `LESSONS.md` #1, `build_prompt` ve serbest-zekâ prompt'u hâlâ "geniş stop şart / SL 2,5×ATR (başabaş ~%71)" diyor.

### Cited Findings
- **xauusd-scalp-no-edge (2026-05-29):** 1m, TP=SL=$5; 6 basit kural %48–50; GBM %51–53 (spread sonrası %49,7); 13 cep 0/13 test; en iyi EV +$0,19/işlem CI [−0,005,+0,366]; 132-koşul tarama en iyi en-kötü-blok WR %52; rejim filtresi spread sonrası negatif — `memory/xauusd-scalp-no-edge.md`; yazı `xau_scalp_research/FINDINGS.md`. Veri `1MDATA/mt5_xauusd_1m_bars.json` (96.334 bar; ilk bar t=1770771600 → 2026-02-11, son t=1779333660 → 2026-05-21; Mac'te doğrulandı).
- **xauusd-daily-swing-edge (2026-06-16):** kural "günlük kapanış yeni N-gün tepesi (N≈40–55) VE kapanış > EMA200 → sonraki D1 açılışında BUY; SL 2,0×ATR14, TP 4,0×ATR14, 20 gün zaman stopu, tek pozisyon"; N=55: 31 işlem/5y, WR %64,5, ortR +0,686, PF 3,04, maxDD 2,0R, bootstrap CI (0,217, 1,154); her yıl + (2021 tek işlem hariç), 5/5 WF katı +, N∈{40..70} plato, $8 sürtünmeye dayanıklı; **H4 varyantı** (H4_DONCH30, 2/4 ATR, 30 bar) ~24 işlem/yıl, WR %47,7, ortR +0,33, PF 1,65, maxDD 6,6R, CI (0,103, 0,562); "Oversold-DIP 2nd entry REJECTED"; tüm SELL varyantları −EV — `memory/xauusd-daily-swing-edge.md`; [xau_swing_research/FINDINGS.md](xau_swing_research/FINDINGS.md) (veri `xauusdegitim/data/raw/` D1 1.289 bar 2021-05→2026-04, H1 29,5k; "Gold rose +157% over the window").
- **xauusd-macro-direction-no-edge (2026-06-16):** gerçek faiz +0,20→−0,11, nominal +0,20→−0,09, VIX +0,10→−0,11 (ileri-20g korelasyon, 2021-23 → 2024-26 işaret değişimi); GBM OOS yön isabeti %62,3 vs taban %72,9 — `memory/xauusd-macro-direction-no-edge.md`.
- **xauusd-meta-stop-sizing (2026-06-17):** meta XAU WR %65,5 ama kazananların kazanmadan önceki düşüşü ≈8 puan; stop 5p→%27 E−0,2 | 8p→%40 | 13p→%54 +1,4 | 15p→%57 +1,4 | 25p→%63 E−0,8; "ai_panel + ml:ultra_safe tradeable, pulse2/smc −EV"; uyarı: kaydedilmiş excursion'lar (spread yok) → üst sınır — `memory/xauusd-meta-stop-sizing.md`.
- **xauusd-trading-disabled (2026-06-16):** `backend/routers/bot_router.py` `TRADING_DISABLED_SYMBOLS={"XAUUSD"}`; "both XAUUSD trades MT5 opened hit SL" — `memory/xauusd-trading-disabled.md` (o tarihteki bot `otosignal/`; bugünkü bot `yeni deneme/`).
- **xau-inverse-shadow-2026-07:** pulse2 SELL tersi 817→275 işlem (saatlik dedup), spread 0,05R; mirror RR=0,58 EV −0,056; RR=1,0 +0,135, RR=1,5 +0,36R; RR=1,0 ilk yarı %64,8 → son yarı %52,6; "candle_cache '1m' TICK-KİRLİ — sadece second=0 mumları"; plasebo yapılmadı — `memory/xau-inverse-shadow-2026-07.md`, [research/xau_inverse_shadow.py](research/xau_inverse_shadow.py)
- **decider-breakeven-entry-quality (2026-09-14):** "TEK gerçek 'yanlış → doğru' geçişi: XAU geometrisi" — ÖNCE n=123 RR 0,40 başabaş %71,4 WR %65,0 EV **−0,081R**; SONRA n=409 RR 0,67 başabaş %59,9 WR %60,1 EV **+0,004R**; XAU tüm geçmiş n=532 WR %61,3 EV −0,015R; serbest-zekâ `hybrid_v1` n=435 kenar +0,1pp EV −0,005R; gold_brain 290 karar 290 WAIT, cf 290/290 None; tüm journal VIX 15,1–19,6 (VIX≥20 sıfır) — `memory/decider-breakeven-entry-quality.md`; [backend/data/evolution/analyst_reports/decider_tam_denetim_2026-09-14.md:40-92](backend/data/evolution/analyst_reports/decider_tam_denetim_2026-09-14.md). Kod kanıtı: commit 85dc9b1a (2026-07-27) "XAU 1.0/2.5 ELENDİ → ev varsayılanı 1.0/1.5 … baz, 12 politikada karşı-olgu havuzunda 10., gerçek OPEN havuzunda 11. sırada" ve [claude_decider/decide.py:98-107](claude_decider/decide.py) `DEFAULT_STOP_ATR=(1.0,1.5)`, `STOP_ATR={}` (XAU'ya özel giriş yok) ✔.
- **decider-learning-loop-2026-10:** LIVE_ALLOWED = XAU BUY, DAX BUY, NDX SELL; "İlk distill (kutu journal'ı) XAU BUY'ı 'belirsiz' (yarılar −0,09/+0,20) çıkardı — Supabase analizindeki 'iki yarıda +' ile çelişiyor; izin listesi gözden geçirilmeli" — `memory/decider-learning-loop-2026-10.md`. Kod ✔: [claude_decider/decide.py:179-182](claude_decider/decide.py) `LIVE_ALLOWED` env varsayılanı `"XAUUSD:BUY,GDAXI.INDX:BUY,NDX.INDX:SELL"`.
- **decider-live-execution-2026-10:** execute() 2026-10-05 demo'ya bağlandı, lot=0,10×min(size_factor,0,3), magic 52890989, kill-switch `EXECUTE_OFF`/`DECIDER_EXECUTE=0`; replay 09-11→10-02 OPEN 280 WR %58,6 EV −0,022R P %34, taban −0,076R, **XAU −0,051R** — `memory/decider-live-execution-2026-10.md`. Kod ✔: [claude_decider/execute_mt5.py:30-38](claude_decider/execute_mt5.py).
- **decider-cli-auth-silent-death:** CLI hatası `{"action":"WAIT","reason":"claude exit …"}` olarak journal'a normal WAIT gibi düşer; 2026-09-11→09-26 978 sahte WAIT; analizde `reason` "claude exit"/"claude spawn" ile başlayanları at — `memory/decider-cli-auth-silent-death.md`; kod ✔ [claude_decider/decide.py:435-466](claude_decider/decide.py).
- **backend-commodity-feed-yahoo-2026-09:** 2026-09-03'ten beri backend XAU/USOIL mumları Yahoo vadelisi (XAU −32…−46$ fark); broker gerçeği `indicator_snapshots`; ⚠ `indicator_snapshots` 2026-07-28 18:00 UTC'den ÖNCE +3 s broker saatinde etiketli (onarılmadı; `research/sl_pattern_2026-09-29/fixbars.py`) — `memory/backend-commodity-feed-yahoo-2026-09.md`.
- **candle-cache-broker-time-offset:** candle_cache 2026-07-28'de UTC'ye onarıldı; NDX 1m 2026-02-10→03-08 60 dk erken; MT5 deal zamanları hâlâ broker saatinde — `memory/candle-cache-broker-time-offset.md`. Not: `research/pinbar_20261010/pull_other.py` başlığı "2026-07-15 öncesi broker saati (NY+7)" diyor — [research/pinbar_20261010/pull_other.py:1-3](research/pinbar_20261010/pull_other.py).
- **mt5-box-operational-facts:** sunucu UTC+3, kutu yerel UTC−4, bot log UTC; `copy_rates_from_pos` tavanı ~99.000 bar (NAS100 M5 99k ≈ 2025-03-05'ten, M1 99k ≈ 68 gün); `copy_rates_range` geniş aralıkta None → dilimli çek; kutuda numpy+pandas var, scipy/sklearn/lightgbm/pytest yok; `research/` kutuda sparse-checkout dışı — `memory/mt5-box-operational-facts.md`.
- **be-lock-exit-rules-rejected:** 487 işlem, BE@TP %60: 54 kurtar / 75 öldür, −4.007$; 44.064 varyantta hiçbir (sembol,yön) grubunda 6/6 dilim pozitif kural yok — `memory/be-lock-exit-rules-rejected.md`.
- **trade-mgmt-be30-runner-2026-07:** 146 XAU gerçek MT5 işlemi de örneklemdeydi; canlıya bağlananlar yalnız NDX/DAX; LESSONS'ta XAU SELL kazananı-koştur Δ+9,4R P %95 "İHTİYATLI — tek kohort", "XAU işlemleri 30dk'dan hızlı ölüyor" — `memory/trade-mgmt-be30-runner-2026-07.md`; [claude_decider/memory/LESSONS.md:23-24](claude_decider/memory/LESSONS.md). Decider tarafında be30_runner "NEGATİF — decider'ın 5m mean-reversion girişlerine TRANSFER OLMADI" (commit 85dc9b1a).
- **canonical-signal-metrics:** XAU meta BUY n=400 çıplak WR %80 → `static_pips` RR 0,533 kenar +17,9pp / +0,35R ama güncel `atr_ladder_v1` WR %13,3 RR 1,808 kenar −22,3pp / −0,31R; `backend/services/signal_metrics.py` tek doğruluk kaynağı — `memory/canonical-signal-metrics.md`.

**Kodla çelişen/bayat kalan iddialar (doğrulandı)**
- `LESSONS.md` #1: "XAU BUY geniş stop ister. Gate WR %84 (OOS)…" — [claude_decider/memory/LESSONS.md:8-10](claude_decider/memory/LESSONS.md) (evidence tablosunda XAU BUY gate artık %70/OOS %72, kapaklı).
- `build_prompt` görev listesi: "XAU BUY ise: 'patient WR', GENİŞ stop şart (management'a yaz, boyut düşür)" — [claude_decider/decide.py:304](claude_decider/decide.py).
- Serbest-zekâ prompt'u: "canlı XAU geometrisi TP 1.0×ATR / SL 2.5×ATR (RR 0.4 → breakeven WR ~%71)" — [claude_decider/decide.py:576-577](claude_decider/decide.py); oysa kod `stop_mults("XAUUSD")` → (1,0, 1,5).
- `PLAYBOOK.md` ise güncel: "2026-07-28 ölçümü 2.5×ATR'yi de ELEDİ … TP1.0/SL1.5, breakeven %60. Canlı %67 (n=150); NY seansında canlı %15 (n=20)"; "XAU Salı zayıf: %49 (n=74) vs Pzt/Perş/Cuma %65-67" — [claude_decider/memory/PLAYBOOK.md:51,76](claude_decider/memory/PLAYBOOK.md).

### Inferences
- Decider'a giden XAU prompt'u aynı anda "SL 2,5 ATR / başabaş %71" (free prompt) ve "SL 1,5 / başabaş %60" (PLAYBOOK) diyor; model `management` alanına geniş stop yazabilir ama **icra bunu okumuyor** (TP/SL sabit `stop_mults`'tan gelir, §3). Yani bu çelişki P&L'i doğrudan değiştirmez ama modelin "çıta" muhakemesini (başabaş %71 → aşırı temkin veya yanlış kalibrasyon) bozabilir. Yeni kural ön-kayda alınırken prompt metinleri de aynı geometriyle hizalanmalı.
- `xauusd-meta-stop-sizing`'deki "13–25 puan" stop ölçeği ($13–25) ile decider'ın bugünkü stop'u (1,5×ATR5m ≈ $6, bkz. §3) farklı ölçekler; commit 85dc9b1a'daki "1.5×ATR hâlâ o ölçekten çok geniş" cümlesi **XAU fiyatı $4.000+ iken ATR5m ≈ $4 olduğunda yanlış** görünüyor — 1,5×ATR5m ≈ $6, meta-stop notunun "%27 WR'a çöktüğü" 5–8 puan bandına yakın. Bu, "dar stop XAU'yu öldürür" mekanizmasının bugünkü decider geometrisinde hâlâ geçerli olabileceğini düşündürür (doğrulanmadı; ölçek $/puan tanımı notta belirsiz).

### Gaps
- `xauusd-meta-stop-sizing` "puan" biriminin $ mı 0,1$ mı olduğu notta açık değil; ölçek karşılaştırması bu yüzden kesin değil.
- `xauusdegitim/data/raw/*.csv` saat damgalarının (sonu "Z") gerçekten UTC mi broker saati mi olduğu ve hangi broker'dan geldiği belgelenmemiş.

---

## 3. Decider XAU mantığı — yön, giriş, SL, TP, boyut, yasaklar, kayıt yerleri

### Takeaway
XAU decider'da **ayrı bir "serbest-zekâ/hibrit" akışta** değerlendirilir: 5m kanal/VWAP aşırılığı ≥1,6 olunca LLM'e çok-TF ham bağlam + XAU BUY 5m mean-rev kanıt paketi verilir; LLM yön ve size seçer (gölgede SELL dahil), ama **giriş = piyasa (ask), TP = +1,0×ATR5m, SL = −1,5×ATR5m (RR 0,67, başabaş %60), boyut = 0,10×min(size,0,3) lot** tamamen koddan gelir. Canlı (demo) icra yalnız XAU **BUY** için açık; 2026-10-05'ten beri 68 demo XAU BUY işlemi var (WR %66,2, ort +0,103R, ort tutma 16,7 dk).

### Cited Findings
**Akış ve tetikleme**
- `FREE_SYMBOL = "XAUUSD"` — XAU kanıt-temelli `build_situation` akışından dışlanır, ayrı free akışa gider — [claude_decider/run_decider.py:45,497-501](claude_decider/run_decider.py)
- Döngü `CADENCE_SEC = 1200` (20 dk) — [run_decider.py:39](claude_decider/run_decider.py); danışma eşiği `CONSULT_REV = 1.6` — [run_decider.py:44](claude_decider/run_decider.py)
- XAU tetikleyicisi: `extremity = max(|channel_z_5m|, |vwap_z_5m|)`; `< CONSULT_REV` ise LLM'e sorulmaz (2026-08-17 düzeltmesi; öncesinde her turda tetikleniyordu: "48 günde … %44.5'i (1678/3766, $369.62)") — [run_decider.py:563-574](claude_decider/run_decider.py); commit 13f6908b. **Not: tetik işaretsiz (|z|) — hem yukarı hem aşağı aşırılık çağrıyı tetikler.**
- Olay-tetikli tekrar bastırma `(bar_time_5m, round(cz*2)/2)` imzası; donuk-feed filtresi; olay takvimi; hafta sonu kapanışına 2 s kala OPEN → WAIT — [run_decider.py:557-615](claude_decider/run_decider.py), [run_decider.py:279-296,352-366](claude_decider/run_decider.py)
- `FREE_EVIDENCE=1` (varsayılan) "HİBRİT": `evidence_pack("XAUUSD","BUY", live_features(5m), tablolar)` + PLAYBOOK/LESSONS/LESSONS_AUTO/REGIME prompt'a eklenir — [run_decider.py:592-607](claude_decider/run_decider.py), [decide.py:517-524,553-585](claude_decider/decide.py)
- `FREE_EXPLORER=1` (varsayılan) "KEŞİF": prompt "HER değerlendirmede … bir YÖN SEÇ — BUY veya SELL (ikisi de serbest). WAIT yalnız veri bozuk/eksikse meşrudur"; `decide_free` `_enforce_guardrails(..., allow_banned=FREE_EXPLORER)` → **gölgede XAU SELL yasağı atlanır** — [decide.py:509-515,537-550,603-618](claude_decider/decide.py)
- Model: `DECIDE_MODEL = claude-sonnet-5-5`, `DECIDE_EFFORT=high` (env ile ezilebilir) — [decide.py:77,80](claude_decider/decide.py)
- Sonradan uygulanan mekanik kapılar (free akış): `_drift_guard` (son 30 sonuç vaadin ≥25pp altı + ≥5 gün → OPEN→WAIT), `_weekend_guard`, `entry_quality.apply_gate` (`chz_dir≥2,0` veya `vol≥1,5`; `ENTRY_QUALITY_BLOCK=False` → **gölge**) — [run_decider.py:613-618,46-69](claude_decider/run_decider.py), [claude_decider/entry_quality.py:36-39](claude_decider/entry_quality.py). **`evidence_rules` (D4/D5) ve `regime_meter.vix_sell_gate` free akışta çağrılmıyor** (yalnız kanıt akışında, [run_decider.py:537-546](claude_decider/run_decider.py)); D4/D5 zaten XAU'ya dokunmuyor — [claude_decider/evidence_rules.py:24-33](claude_decider/evidence_rules.py).

**Yön kuralları / yasaklar**
- `HARD_BANS = {("XAUUSD","SELL"), ("USOIL.FOREX","BUY")} ∪ decider_config.BLOCKED_SYMBOL_DIRECTIONS` (decider_config'te de `{("XAUUSD","SELL")}`) — [decide.py:155-156](claude_decider/decide.py), [claude_decider/decider_config.py:29](claude_decider/decider_config.py)
- `gates.ALLOW["XAUUSD"] = {"BUY"}`; yorum "XAU SELL (OOS %20, kalıcı yasak)"; `GATE_WR[("XAUUSD","BUY")] = (70, 72)`; fiziksel kapı `CHAN_Z=2.0`, `VWAP_Z=1.5`, `WIN_N=50` — [claude_decider/gates.py:19-46](claude_decider/gates.py)
- `live_eligible`: HARD_BANS → "SERT YASAK"; `LIVE_BLOCKED={("NDX.INDX","BUY")}`; `LIVE_ALLOWED` dışı → reddedilir. XAU BUY izinli, XAU SELL hem HARD_BANS hem LIVE_ALLOWED dışı — [decide.py:158-193](claude_decider/decide.py). Free akışta icra öncesi aynı kilit: "FREE_EXPLORER gölge akışta XAU SELL'i … İCRA yoluna ASLA inmemeli" — [run_decider.py:622-631](claude_decider/run_decider.py)
- Evidence tablosu XAU|BUY: base WR 78 (n=3.981, OOS 76/1.593), **gate 70 (n=1.578, OOS 72/579, live_n 150, capped)**; rev_chan kovaları 63–81, "2–2.5" %81 (n=211, live_n 21); XAU|SELL base 27 (OOS 15), gate 42 (OOS 21) — `claude_decider/evidence_tables.json` (Mac'te okundu). Free prompt uyarısı: "Yukarıdaki WR'lar cf/araştırma geometrisiyle ölçüldü … Kalibrasyon (2026-07, 928 canlı çift): %80-90 vaadi → canlı %64" — [decide.py:575-582](claude_decider/decide.py)

**Giriş / SL / TP / boyut (kod)**
- Kâğıt (journal) trade: `build_trade` → `entry = karar anı price`, `tp = price ± 1.0×atr`, `sl = price ∓ 1.5×atr`, `rr = 0.67`, ölçülen `spread`/`spread_atr` yazılır; `EXIT_POLICY` yalnız USOIL `trail_1.0` (gölge-grade) — [decide.py:95-137](claude_decider/decide.py). XAU free'de `atr = ctx["atr_5m"]` — [decide.py:620-627](claude_decider/decide.py)
- **Karşı-olgu her XAU kaydında yalnız BUY** ("açsaydı BUY") — [decide.py:629-646](claude_decider/decide.py)
- Canlı emir: `execute({"symbol","price"}, dec)` → `directions` boş olduğu için `atr=None` → `execute_mt5._atr14` (son 40 M5 barın son 14 TR ortalaması; **koşan bar dahil**) ile yeniden hesaplanır; `entry = tick.ask` (BUY); `tp/sl = entry ± tp_atr/sl_atr × atr` (stop_mults → 1,0/1,5); `spread/ATR > 0,15` ise atla; broker min stop kontrolü; lot = `0.10 × min(size_factor, 0.3)` adıma aşağı yuvarlanır (≥ volume_min); sembol başına 1, toplam 3 decider pozisyonu, günlük 10 emir; yalnız DEMO hesap; `DEVIATION_POINTS=30`; sabit TP/SL, yönetim yok — [run_decider.py:639-653](claude_decider/run_decider.py), [claude_decider/execute_mt5.py:30-38,64-95,139-207](claude_decider/execute_mt5.py)
- LLM'in `management` metni (ör. "geniş stop") icrada kullanılmıyor — `send_order` yalnız `direction` ve `size_factor` okur — [execute_mt5.py:139-188](claude_decider/execute_mt5.py)

**Sonuç ölçümü (grading)**
- Çözüm Pepperstone M5 barlarıyla (`copy_rates_from_pos(...,M5,0,800)`, DataContract doğrulamalı), giriş barı zamanından sonra; aynı barda TP+SL → LOSS; 48 saat içinde çözülmezse EXPIRE=0R; `pnl_r_net = brüt − spread_atr/risk_atr` — [run_decider.py:170-182](claude_decider/run_decider.py), [claude_decider/outcomes.py:24-40,164-195](claude_decider/outcomes.py). (M5 bid barları → BUY girişi bid kapanışından ölçülür; spread ayrı düşülür.)

**Kayıt yerleri**
- Kutu: `claude_decider/memory/journal.jsonl` (yerel; `decide.JOURNAL_JSONL`), `claude_decider/live_orders.jsonl` (her emir denemesi) — [execute_mt5.py:25-27](claude_decider/execute_mt5.py); `memory/LESSONS_AUTO.md` git-dışı (`memory/decider-learning-loop-2026-10.md`).
- Supabase `decider_journal` (id, host, ts, symbol, decision, confidence, outcome jsonb, raw jsonb) — SQL: `information_schema.columns`. XAU kayıtlarında `raw->>'mode'` = `free` / `gold_brain` / (yok=evidence).
- Supabase `bot_trades` — decider demo işlemleri `magic = 52890989`, comment `CDEC XAUUSD BUY` ([execute_mt5.py:58-61](claude_decider/execute_mt5.py)); otopsi aracında aile `DECIDER` (offset 20) — [scripts/islem_otopsi/settings.py:15-25](scripts/islem_otopsi/settings.py)

**Ölçülen performans (Supabase, 2026-10-15 sorguları; "claude exit/spawn" satırları hariç, HAM — tekrar kayıtlar ayıklanmamış)**
- SQL (`decider_journal`, XAU): free OPEN BUY RR 0,67 (2026-07-28→10-14) **n=649, 384W/264L, ort brüt −0,010R, net −0,035R**; free OPEN BUY RR 0,40 (07-03→07-28) n=57, ort −0,091R, net −0,323R; free OPEN SELL RR 0,40 n=60 ort −0,137R; **free OPEN SELL RR 0,67 n=45 ort −0,035R (net −0,065R)**; free WAIT n=885; gold_brain WAIT 290; evidence-akışı OPEN BUY (06-30) n=6 ort −0,533R.
- SQL (09-01 sonrası free OPEN, n=396): ort spread **$0,121**, ort ATR5m **$4,07** (medyan $3,87), spread/ATR **%3,26**; aynı kayıtların karşı-olgu (hep BUY) ort **−0,011R** (n=395).
- SQL (`bot_trades`, magic 52890989, XAUUSD): **68 işlem (hepsi BUY), 45 kazanan (%66,2), ort R +0,103, medyan R +0,666, RR 0,67, ort SL mesafesi $5,99, ort lot 0,015, toplam +$32,88, ort süre 16,7 dk**, 2026-10-05 07:23 → 10-14 04:43 (zamanlar tabloda nasıl kaydedildiyse; broker saati olabilir). Aynı dönemde NAS100 decider 11 işlem −$0,48; GER40 decider işlemi yok.
- Bağımsızlaştırılmış seçim değeri: XAU BUY OPEN +0,06R (n=99) vs WAIT-cf −0,14R (n=208) — [research/decider_kural_20261008/SONUC.md:12](research/decider_kural_20261008/SONUC.md); replay (09-11→10-02) XAU −0,051R — `memory/decider-live-execution-2026-10.md`; commit 13f6908b mesajı: "XAU free-mode 312 gercek acilan islemde %58.7 WR / ort -0.086R (breakeven esigi RR=0.67 icin %60 WR gerektiriyor, tutmuyor)".
- `PLAYBOOK.md`: "NY seansında canlı %15 (n=20)" ve "XAU Salı zayıf %49 (n=74)" — [PLAYBOOK.md:51,76](claude_decider/memory/PLAYBOOK.md) (küçük n, ön-kayıtsız gözlem).

### Inferences
- Decider'ın XAU geometrisi (TP ≈ $4, SL ≈ $6, tipik tutma ~17 dk) **ölçek olarak 2026-05-29 "XAU 1m scalp edge yok" araştırmasının (TP=SL=$5) alanına düşüyor**; o çalışmanın spread varsayımı $0,30–0,40 idi, Pepperstone'da ölçülen $0,12 (≈0,02R) çok daha ucuz — yani "spread'e yenik" hükmü bu broker'da kısmen gevşeyebilir ama "yönsel kenar yok" hükmü değil.
- Evidence tablosunda XAU BUY **gate WR (70) < base WR (78)**: mean-rev "aşırılık" koşulu XAU BUY'da tabandan kötü. Decider'ın XAU tetikleyicisi tam bu aşırılık (|z|≥1,6) → XAU'da kanıtlı mekanizmanın (trend/kırılım devamı, sürüklenme) tersine bir çerçevede karar veriyor. Hafıza notundaki "ORTAK KAÇIRMA … XAU 147 … profil trend-yönlü + aşırılıksız (rev~0.5)" bulgusu da bunu destekliyor (`memory/claude-decider-architecture.md`, 2026-07-09 bölümü).
- Ham journal'da XAU BUY açılışları ≈ başabaş (−0,010R brüt, −0,035R net) ve karşı-olgu tabanı ≈ −0,011R → seçim alfası en fazla küçük; bağımsızlaştırılmış analizde (+0,06 vs −0,14) görülen "seçim değeri" pozitif ama ham seride görünmüyor (E6 şişmesi/ayıklama farkı). Demo canlı 68 işlemin +0,103R'si 9 günlük tek pencere, bağımsızlık ayıklanmamış — kanıt sınıfı C.
- LLM'in seçtiği hiçbir giriş parametresi (limit fiyat, stop genişliği, hedef) icraya ulaşmıyor; LLM yalnızca "aç/açma + size" belirliyor. Yani decider-XAU için ön-kayıtlı bir "giriş kuralı + TP/SL geometrisi" fiilen `stop_mults` + tetik (CONSULT_REV / |z|) + LIVE_ALLOWED kodunu değiştirmek demektir; LLM filtresi bunun üstünde bir seçici katmandır.

### Gaps
- `free_context.build_free_context` içindeki `atr_5m`'in tam tanımı (Wilder mi basit ortalama mı, koşan bar dahil mi) bu turda okunmadı; `_atr14` (icra) koşan barı içeriyor → kâğıt ve canlı ATR farklı olabilir.
- Canlı demo XAU işlemlerinin kâğıt (journal) karşılıklarıyla eşlemesi ve kayma (slippage) ölçümü yapılmadı.
- `live_orders.jsonl` (atlanan/reddedilen XAU emirleri, ör. spread/ATR veya günlük sınır) kutuda; okunamadı (kutu çevrimdışı).

---

## 4. `yeni deneme/` botunda XAU durumu ve son commitler

### Takeaway
Botta XAU **gün-içi canlı işlemi kapalı**; yalnız iki gölge kayıt var: (a) `check_shadow_scopes` pulse-oylu XAU BUY/SELL gölge sinyalleri, (b) MK-04 "1h yeni 20-mum tepesi BUY" gölgesi (`xau_shadow.py`, 2026-10-12). XAU'ya şu an gerçek emir gönderen tek bileşen **decider demo icrası** (magic 52890989).

### Cited Findings
- Yerel `yeni deneme/config.py` (⚠ kutudaki config gitignore'da ve farklı olabilir, E11): "DOKUNMAZ: XAUUSD (edge yok)"; XAU ROBUST_SCOPES satırları yorum satırı; `BLOCKED_SYMBOL_DIRECTIONS = {("XAUUSD","SELL"), ("USOIL.FOREX","SELL")}` — [yeni deneme/config.py:12,57-66,204-206,291-299](yeni%20deneme/config.py)
- Bot sembol-yön yasağı uygulaması: `if (forexsai_sym, direction) in BLOCKED_SYMBOL_DIRECTIONS: return  # kalıcı yasak (ör. XAUUSD SELL)` — [yeni deneme/forexsai_demo_bot.py:1791-1792,1943](yeni%20deneme/forexsai_demo_bot.py)
- Gölge scope'lar: `check_shadow_scopes()` — "timelapse deneyi XAUUSD'yi trend+konum kapılarıyla en kârlı sembol gösterdi (B varyantı: BUY +55.3R/6-9 hafta, SELL +103.7R/8-9 …) AMA … XAU canlıya AÇILMIYOR; kapıdan geçen sinyaller gölgede kaydedilip … karşılaştırılacak"; varsayılan `SHADOW_SCOPES = {"XAUUSD:BUY":{}, "XAUUSD:SELL":{}}` — [forexsai_demo_bot.py:1318-1332](yeni%20deneme/forexsai_demo_bot.py); karne aracı [backend/research/xau_shadow_replay.py](backend/research/xau_shadow_replay.py) (`gate_skipped.jsonl` reason=shadow_signal, `SERVER_OFFSET_H = 3`).
- MK-04 gölgesi: "BU MODÜL HİÇBİR EMİR GÖNDERMEZ"; kural: son kapanmış 1h barın yükseği ≥ önceki 20 barın en yükseği; ATR = sinyal barından önceki 14 bar; giriş = ask; stop = giriş − 1,5×ATR; çıkış = 20. 1h barın kapanışı; tek pozisyon; `slip_r = (entry_ask − paper_close)/stop_dist` ölçülür; parametreler donduruldu — [yeni deneme/xau_shadow.py:1-46](yeni%20deneme/xau_shadow.py); bot içine fail-open import — [forexsai_demo_bot.py:43-46](yeni%20deneme/forexsai_demo_bot.py)
- Bot tarafı XAU BUY probasyon gözlemi: "XAUUSD BUY: 17W/19L= %47,2 vs %42,9 → fark +4,4 p=0,597 (kanıt yok)" — [yeni deneme/phase_rules.py:98](yeni%20deneme/phase_rules.py)
- Tek manuel XAU işlemi: `bot_trades` magic 0, 2026-07-06, +$13.818 (SQL).

**Son commitler (XAU veya decider'a dokunan, `git log`)**
- dae08288 (10-12) docs(kapi): MK-04 XAU gölge kuruldu · 0f55aa3a (10-12) feat(bot): XAU 1h yeni-tepe BUY gölge kaydı (emir yok) + MK-01..05 · 0b980eee (10-07) feat(decider): kanıt kuralları, canlı izin listesi, haftalık öğrenme · ee405c0e (10-05) fix(decider): order_check filling-mode döngüsü (10030) · f1bf9d60 (10-04) feat(decider): execute() MT5 demo emrine bağlandı · ba7933c8 (10-04) varsayılan model Sonnet 5.5 · 5c884a6f/5713c09c/17a6e641 (09-14) rejim kapısı, rejim ölçer, giriş-kalitesi kapısı (gölge) · da92fa87 (09-14) EPOCH analizi — XAU geometrisi · 13f6908b (08-17) XAU serbest-zekâ aşırı tüketim düzeltmesi · e241f102 (08-12) XAU gölge scope 1m replay karnesi · 0c368c54 (08-01) XAU/USOIL ATR merdiveni · e7c654ad (07-28) NDX BUY LIVE_BLOCKED · **85dc9b1a (07-27) XAU stop 2.5→1.5 ATR** · 695d5634/7c3406f3 (07-27) olay takvimi, hafta sonu koruması, ölçülen-spread net grade — `git log` çıktısı (Mac, 2026-10-15).

### Inferences
- Bot ile decider XAU konusunda farklı politika uyguluyor: bot gün-içi XAU'yu hiç açmıyor (B1 + "DOKUNMAZ"), decider 5m ölçeğinde demo'da XAU BUY açıyor. Decider-XAU araştırmasının sonucu, botun XAU kararını otomatik değiştirmez (E18 — popülasyon taşıma).

### Gaps
- Kutudaki gerçek `config.py`'de `SHADOW_SCOPES`, `BLOCKED_SYMBOL_DIRECTIONS` ve XAU'nun sembol listesinde olup olmadığı doğrulanmadı (`python backend/research/box_dump_bot_settings.py` gerekir; kutu çevrimdışı).

---

## 5. Geriye dönük test için mevcut XAU verisi — kaynak, derinlik, tuzak, önerilen yol

### Takeaway
Elde **çok yıllık broker-gerçeği M1/M5 XAU verisi yok.** Broker gerçeği yalnız: `indicator_snapshots` (2026-06-17 → 10-14, ~4 ay; 07-28 öncesi +3 s kayık) ve kutudaki MT5 (99k bar tavanı, dilimli çekimle M1 ~2–3 ay / M5 ~1,3 yıl tahmini — doğrulanamadı). Çok yıllık seriler (candle_cache 1h 2016+, 30m 2021+, xauusdegitim H1/M15 2021/22+) kaynağı/saati karışık ve **09-03 sonrası Yahoo vadelisi**. Çok yıllık temiz M1/M5 için en uygulanabilir yol **Dukascopy XAU/USD tick → 1m bid/ask** (repo'da NDX için hazır boru hattı var) + kutu MT5'ten son aylar için broker kalibrasyonu.

### Cited Findings
**Supabase (SQL, 2026-10-15)**
- `indicator_snapshots` XAUUSD: 1m 114.288 satır 2026-06-17 00:16 → **2026-10-14 06:57**; 5m 22.929 (06-17 → 10-14); 15m 7.598; 30m 3.783; 1h 1.959 (06-17 → 10-14). Broker gerçeği bu tablo (E21); 07-28 18:00 UTC öncesi +3 s — `memory/backend-commodity-feed-yahoo-2026-09.md`; kaydedici `yeni deneme/data_recorder.py`.
- `candle_cache` XAUUSD (Mac'te `research/pinbar_20261010/data/*.parquet` üzerinden, 2026-10-10 çekimi; second=0 ve TF-hizalı filtreli): **5m 94.851 bar 2025-06-11 → 2026-10-09; 15m 84.989 2023-03-09 →; 30m 62.526 2021-07-01 →; 1h 61.284 2016-05-31 →** (yıl başına ~5.900 1h bar). Kaynak etiketi: 09-03 sonrası `yahoo`, öncesi "broker" varsayılmış; başlık notu "2026-07-15 öncesi broker saati (NY+7)" — [research/pinbar_20261010/pull_other.py:1-25](research/pinbar_20261010/pull_other.py). candle_cache 1m tick-kirli ("sadece second=0") — `memory/xau-inverse-shadow-2026-07.md`.

**Yerel dosyalar (Mac)**
- `xauusdegitim/data/raw/`: D1 1.289 satır 2021-05-03 → 2026-04-29; H1 29.546 (2021-04-30 →); H4 7.729; M30 59.061; **M15 100.000 (2022-02-03 →)**; **M5 100.000 (2024-11-27 → 2026-04-29)** — 100k satır tavanı MT5 export'una işaret ediyor; saat damgası "Z" etiketli, broker/saat dilimi belgelenmemiş (Mac'te `wc`/`head` ile ölçüldü). Ayrıca DXY/VIX/US10Y D1/H1.
- `1MDATA/mt5_xauusd_1m_bars.json` ve `RECOVER/mt5_xauusd_1m_bars.json`: 96.334 1m bar 2026-02-11 → 2026-05-21 (MT5).
- Diğer kısa paketler: `analiz_paketi_2026-07-09/prices/XAUUSD_1m_son_14gun.csv`, `research/sim_bot/bars_XAUUSD_{1m,5m,1h}.json`, `sr_rejection_research/data/XAUUSD_{1m,5m,30m,1h}.json`, `bot_live_audit/bars/XAUUSD_{1m,1h}.json`, `research/trade_mgmt_ndx/bars_XAUUSD.csv`, `research/cortex_confluence/data/GOLD_1h.csv`, `research/cortex_confluence/intraday/GOLD_F.csv` (vadeli) — `find` çıktısı.
- Dukascopy boru hattı: `~/dukascopy_us100/download_us100_2025.sh` (`npx dukascopy-node -i usatechidxusd -t tick -f csv`, gün gün, 5 deneme, `done/` işaretleri) → [research/ndx_gate_forge/build_duka.py](research/ndx_gate_forge/build_duka.py) (tick → 1m bid OHLC + ask OHLC + medyan spread, **UTC, bar BAŞLANGIÇ damgası**). Defter: "Veri: Dukascopy 2025 (bid/ask)…" — [KAPI_KAYIT_DEFTERI.md:154](docs/KAPI_KAYIT_DEFTERI.md). XAU için Dukascopy indirmesi repoda **yok**.

**Kutu MT5 (Pepperstone = decider, IC Markets = bot)**
- Çekim kuralları: `copy_rates_from_pos` tavanı ~99.000 bar; geniş `copy_rates_range` None → 20 günlük dilimler (`usoil_breakout_lab.fetch`, `DAYS=420`, `.npy` önbellek) — [backend/research/usoil_breakout_lab.py:25-66](backend/research/usoil_breakout_lab.py); sızıntısız tarih-öncesi çekim `rates_upto(symbol, tf, when, n)` (`copy_rates_range` + `t ≤ when − periyot` kesimi; `when` = **sunucu saati**) — [backend/research/_bars_upto.py:1-42](backend/research/_bars_upto.py). NAS100 referansı: M5 99k ≈ 2025-03-05'ten, M1 99k ≈ 68 gün — `memory/mt5-box-operational-facts.md`.
- **Kutu şu an çevrimdışı:** `remote.py health` → "🔴 mt5_box 2026-10-14T06:58:25 (1288 dk önce) … open_positions=1"; `remote.py status` → 10-14 22:45 `sync_lessons` dâhil tüm komutlar `pending`. Bu yüzden XAU derinlik sorgusu (salt-okuma `python -c` MT5 sorgusu, 10-15 04:16) **kuyrukta bekliyor, çalışmadı**; kutu geri gelince çalışıp sonucu kuyruğa yazacak (değişiklik yapmaz). `indicator_snapshots` ve decider/demo işlemlerinin 10-14 ~07:00 UTC'de durması da aynı kesintiyle tutarlı.

### Inferences — önerilen temiz çok yıllık XAU M1/M5 edinme yolu
1. **Çok yıllık gövde (keşif + ileri-yürüme):** Dukascopy `xauusd` tick → `build_duka.py` mantığıyla 1m **bid ve ask** barları (UTC, bar-başı damga), 2019→2026-09. Avantaj: gerçek ask (BUY girişi için), medyan spread, saat ekseni net UTC, 100k tavanı yok. Dezavantaj: broker ≠ Pepperstone (fiyat seviyesi/spread farklı) → yalnız mekanizma/yön kanıtı; maliyet Pepperstone ölçümüyle ($0,12 ort., spread/ATR5m %3,3; SQL) ayrıca stres edilmeli. (Dukascopy XAU enstrüman kodu repo'da yok — doğrulanmalı.)
2. **Broker kalibrasyon katmanı (son aylar):** kutu Pepperstone terminalinden `XAUUSD` M1/M5 20 günlük dilimlerle (`usoil_breakout_lab.fetch` kalıbı, SYMBOL parametreli), `time − 3 s` (yaz; kışta −2 s — offset'i tick'ten ÖLÇ) ile UTC'ye çevir; geçmiş karar anı kurulumunda yalnız `_bars_upto.rates_upto`. Dukascopy ile çakışan dönemde fiyat farkını ve saat eksenini (ABD açılışı 13:30/14:30 UTC sıçraması testi, E2) doğrula.
3. **Supabase `indicator_snapshots`** (06-17 → 10-14, 07-28 öncesi −3 s düzeltmeli; `research/sl_pattern_2026-09-29/fixbars.py`) → decider journal kararlarını yeniden oynatmak için en yakın broker-gerçeği (ama decider Pepperstone'da, kaydedici IC Markets'ta olabilir — sembol/broker eşleşmesi doğrulanmalı).
4. **Kullanma:** candle_cache XAU (09-03 sonrası Yahoo GC=F; 1m tick-kirli; geçmiş saat ekseni karışık), `copy_rates_from` (E1), backend sonuç sütunları (E8).

### Gaps
- Kutu Pepperstone/IC Markets XAU M1/M5/H1/D1 gerçek derinliği **ölçülemedi** (kutu 10-14 06:58 UTC'den beri çevrimdışı; sorgu kuyrukta).
- `indicator_snapshots` XAU'nun hangi terminal/broker'dan geldiği (bot IC Markets mı, Pepperstone mu) doğrulanmadı; yerel config'te `RECORDER_SYMBOLS` NDX/DE40/XTIUSD listeliyor, XAU satırı görünen ilk 4 satırda yok — [yeni deneme/config.py:172-176](yeni%20deneme/config.py) (tam liste okunmadı).
- Dukascopy'nin XAU tick geçmişinin başlangıç yılı ve enstrüman kimliği repo içinde belgelenmemiş.

---

## 6. Canlıya alma kartı (2. KURAL) ve `go_live_gate.py` — decider-XAU kuralı kartlanabilir mi?

### Takeaway
`go_live_gate.py` şu hâliyle **yalnız USOIL BREAKOUT'a bağlı, yalnız BUY, sabit TP/SL braketli, zaman çıkışsız** bir kart üretici; decider-XAU için **ya mekanik bir XAU giriş kuralı bar verisinden kartlanmalı (aracın genelleştirilmesi gerekir)** ya da LLM-filtreli decider kararları için **canlı/gölge işlem kartı** (≥100 bağımsız karar + aynı 6 ölçüt; `research/canli_kart_20261009/live_card.py`, aile `DECIDER`) kullanılmalı.

### Cited Findings
- 6 ölçüt: (1) ≥150 çözülmüş olay; (2) ortR>0 ve bootstrap P(EV>0) ≥ %90; (3) iki kronolojik yarının ikisi ≥0; (4) spread×1,5'te pozitif; (5) giriş = **sonraki M1 açılışı + spread**, kapanış-girişiyle fark ≤ 0,5×|ortR|; (6) tek pozisyonla pozitif. Verdikt: hacim düşerse RED, 2/3/4/6'dan biri düşerse SHADOW, hepsi → LIVE — [backend/research/go_live_gate.py:1-34](backend/research/go_live_gate.py); CLAUDE.md "2. KURAL".
- Arayüz: `SCOPES[name] = {"symbol", "events": fn(m5)->[{t, atr, close,…}], "tp_atr", "sl_atr", "be_trail", "aciklama"}`; tek kayıtlı scope `usoil_breakout` (symbol "SpotCrude") — [go_live_gate.py:49-57](backend/research/go_live_gate.py)
- Sınırlamalar (koddan): `fetch`/`get_spread`/`DAYS=420` `usoil_breakout_lab`'dan import edilir ve `SYMBOL="SpotCrude"` sabit — [go_live_gate.py:45](backend/research/go_live_gate.py), [usoil_breakout_lab.py:25-28,68-72](backend/research/usoil_breakout_lab.py); `simulate` yalnız BUY (`tp = entry + …`, `sl = entry − unit`); giriş `k = searchsorted(t1, e.t + 300)` → olay zamanını **5m bar açılışı** varsayar; en fazla 1.440 M1 bar, **çözülmeyen olaylar atılır (zaman çıkışı/EXPIRE yok)**; spread anlık `symbol_info.spread×point` (sabit); bootstrap i.i.d. (gün-blok değil) — [go_live_gate.py:60-129](backend/research/go_live_gate.py)
- Mevcut XAU kartları: `xau_1h_yeni_tepe_buy.json` ve `_sl15.json` (verdikt SHADOW; 5. ölçüt ✗) — kendi betikleriyle (`research/pinbar_20261010/xau_card*.py`) üretildi, `go_live_gate.py` ile değil: 1h candle_cache 2016-05 → 2026-09-02, giriş "sonraki 1h açılışı + 0,25 spread", 20 mum zaman çıkışı, gün-blok bootstrap — [research/pinbar_20261010/xau_card.py:1-40](research/pinbar_20261010/xau_card.py)
- Canlı işlem kartı: ön-kayıtlı (2026-10-09) kaynak `bot_trades` + broker 1m `indicator_snapshots`; birim = KARAR (2 dk içindeki bacaklar tek karar); R = net $ / ilk risk $; ölçütler ≥100 karar, gün-bloklu bootstrap P ≥ %90, iki yarı ≥0, +0,5×spread stres, kâğıt giriş (önceki kapanmış 1m kapanışı) vs gerçek dolum farkı < 0,5×|ortR|, tek pozisyon; kullanım `python3 research/canli_kart_20261009/live_card.py <AİLE>` — [research/canli_kart_20261009/live_card.py:1-35](research/canli_kart_20261009/live_card.py); aile eşlemesi `20: "DECIDER"` — [scripts/islem_otopsi/settings.py:15-25](scripts/islem_otopsi/settings.py). Decider XAU şu an 68 demo işlem (SQL) → 1. ölçüt (≥100 karar) henüz karşılanmıyor.
- E22: "Panel sinyali tabanlı scope'lar bar verisinden yeniden üretilemez … canlı/gölge işlem kartı" — [KAPI_KAYIT_DEFTERI.md:53](docs/KAPI_KAYIT_DEFTERI.md)

### Inferences — decider-XAU kuralını kartlamak için gerekenler
- **Mekanik kural yolu (önerilen, ön-kayıt için):** `go_live_gate.py`'yi sembol-parametrik yap (`fetch(symbol, tf, days)`, sembol başına spread ve sunucu-saati ofseti), olay zamanını açıkça "karar barı kapanışı" olarak tanımla, **zaman çıkışı/EXPIRE** ekle (çözülmeyeni atmak hayatta kalma yanlılığı yaratır; decider 48 s EXPIRE=0R kullanıyor), gün-blok bootstrap ve sürüklenme tabanı (aynı dönem × yön × UTC saati rastgele BUY, aynı braket) ekle. Kutu MT5'in ~1,3 yıllık M5/~2–3 aylık M1 derinliği (tahmin) 150 olay için yetebilir ama 2. ve 3. ölçütün çok yıllık sınaması için Dukascopy gövdesi gerekir.
- **LLM-filtreli yol:** kural mekanik tetik + LLM vetosu olarak kalacaksa, mekanik tetiğin kendisi bar verisiyle kartlanmalı (taban); LLM'in katkısı yalnız canlı/gölge işlem kartıyla (aile DECIDER, sembol=XAUUSD filtresi eklenerek — `live_card.py` şu an aileye göre filtreliyor, sembol ayrımı yok) ve journal'daki karşı-olgu (OPEN vs WAIT-cf) karşılaştırmasıyla ölçülebilir.
- Kart 5 (icra) XAU'da kritik: MK-04'te kapanış-girişi ile sonraki-açılış girişi arasındaki fark (+0,169 vs +0,107) kartı düşürdü; decider'ın piyasa (ask) girişi + Pepperstone $0,12 spread bunu küçültür ama `live_card.py`'nin "kâğıt giriş" kıyası (IC Markets `indicator_snapshots` 1m) Pepperstone dolumuyla farklı broker fiyatını karşılaştırabilir → broker eşleşmesi doğrulanmalı.

### Gaps
- `go_live_gate.py`'nin `build_events` dışında başka scope'la hiç koşturulmadığı varsayımı (kartlar klasöründe yalnız `usoil_breakout.json` bu araçtan) dosya adlarından çıkarıldı; diğer kartlar ayrı betiklerle üretilmiş.
- Decider-XAU için bugüne kadar hiçbir canlı işlem kartı üretilmemiş (go_live_cards klasöründe yok).
