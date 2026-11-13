# OK-02 — DAX: bot ↔ decider ortak kazanç kapısı (OK-01'in DAX tekrarı) · ön kayıt 2026-11-13

Kullanıcı: "aynı şeyi XAUUSD bittikten sonra DAX'ta yap". OK-01 yöntemi (research/ortak_kapi_20261113/PROTOCOL.md) DAX'a
uygulanır; veri ve kodlar oradan (aynı yükleyiciler). DP-00 (111 DAX işlemi, 65 özellik, kapı yok) TEKRARLANMAZ.
OK-01'in havuz tablolarında DAX satırları görüldü (aile ortalamaları); aşağıdaki DAX'a özgü sınamaların sonuçları görülmedi.

Popülasyonlar: bot DAX pozisyonları (MOMSR BUY, CHREV BUY/SELL, CEKIC) 06-29→11-13; decider DAX journal (OPEN + WAIT cf, net R);
decider DAX gerçek icraları (magic +20).

- **D1 uzlaşma:** bot DAX girişinden önceki 30 dk'da decider DAX kararı AGREE/OPPOSE/… ; decider DAX OPEN anında bot DAX aynı/ters.
- **D2 tahsis/engel:** DAX aile-yön grupları (bot icra; decider journal OPEN epizod + icra), ENGEL = iki yarı < 0 ∧ gün-blok P(<0) ≥ %90 ∧
  ön dönem (06-25→08-12) < 0 (B) / ön dönem yok-artı (C). n ≥ 30.
- **D3 icra açığı (yeni):** decider DAX icralarının gerçek R'si − aynı journal kararının simüle `cf_pnl_r_net`'i (karar eşleşmesi ts ±2 dk).
  Açık < 0 ve gün-blok P(<0) ≥ %90 ise canlı DAX BUY "simülasyon kazanıyor, gerçek kaybediyor" → canlı engel adayı. Ayrıca açığın
  kaynağı: giriş kayması (gerçek giriş − karar fiyatı, yön-işaretli, ATR biriminde), SL/TP mesafe farkı, yönetim (BE/erken kesme).
- **D4 mekanik tetik + LLM seçimi (DAX):** gate_fired epizodları; OPEN − SAHTE_WAIT ve OPEN − LLM_WAIT aynı hafta eşli (OK-01 H7 yöntemi).
- **D5 kendi karnesi (DAX):** bot DAX aileleri + decider DAX tek-poz dizisi; OK-01 H10 kuralı. (OK-01'de genel X; DAX'a özgü bilgi için raporlanır.)
- **D6 çapraz varlık (DAX):** eş NDX, 30 dk; F1/F2 (OK-01 H12); yalnız gerçek girişli popülasyonlar (bot, decider) — panel E124 nedeniyle kullanılmaz.

Geçme ölçütleri OK-01 ile aynı (iki yarı aynı işaret, gün-blok P ≥ %95 kapı için / ≥ %90 engel için, n ≥ 30, bağımsız ikinci popülasyon).
Geçen engel kod düzeyinde uygulanır (decider LIVE_ALLOWED veya bot config varsayılanı) ve main'e push edilir; yeni kapı ise yalnız GÖLGE.

## EK-1 (D1–D6 sonuçlarından SONRA, D7 sonucundan ÖNCE — 2026-11-13)
D1–D6: engel/kapı yok. **D7 — DAX BUY × VIX rejimi** (mekanizma: §3-2 "korku döner", NDX'te VIXREG/OLD-10; DAX'ta girişler için hiç sınanmadı).
Rejim = ÖNCEKİ günün VIX kapanışı (E20) < 18,4 "SAKİN" / ≥ 18,4 "KORKU". Öngörü (yön önceden): DAX BUY SAKİN'de KORKU'dan kötü.
Popülasyonlar: (a) bot DAX BUY (MOMSR + CHREV), (b) decider DAX BUY journal OPEN epizodları (net R) + mekanik tetik BUY, (c) **bağımsız uzun
vekil**: `ndx_gate_forge/data/dax_30m.parquet` / `dax_1h.parquet` üzerinde her işlem saatinde DAX BUY, tek pozisyon, 80/110 oranlı braket
(OK-01 H11 simülatörü), Xetra saatleri 07:00–15:30 UTC, sonraki bar açılışı + yarım spread.
ENGEL ölçütü: SAKİN'de ort R < 0 ve SAKİN − KORKU < 0; (a) ve (b)'de aynı işaret, (c)'de iki kronolojik yarıda da aynı işaret ve gün-blok P(fark<0) ≥ %95.
Geçerse: decider ve bot DAX BUY için "VIX < 18,4 iken açma" — decider'da `LIVE_ALLOWED` yolunda kural, bot'ta config varsayılanı (önce GÖLGE değil
doğrudan engel, çünkü engel yeni pozisyon üretmez; 2. KURAL yeni scope'lar içindir).
Sapma (sonuçtan önce): DAX vekil dosyalarında saat ekseni belirsiz (kış Xetra tepesi 07, yaz ABD tepesi 14) → seans filtresi KALDIRILDI;
(c) hafta içi her bar. VIX önceki gün kapanışı olduğundan saat kayması rejim etiketini etkilemez.

## EK-2 (D7 sonuç kaydı)
(a) bot DAX BUY SAKİN −0,016 (54) vs KORKU +0,303 (11), fark −0,32, yarılar −/−, P(fark<0) 0,81; (b) decider OPEN fark +0,02; (b2) mekanik fark −0,14
(P(<0) 0,88); (c) bağımsız vekil 2021-26 fark **+0,025** (yarılar +/+), 2016-21 **+0,045** (P(>0) 0,95) → uzun veride TERS. Engel ölçütü tutmadı → X.

## EK-3 (2026-11-13, sonradan uygulama — açıkça işaretli)
D2 ENGEL ölçütü (değiştirilmeden) decider mekanik tetik popülasyonlarına da uygulandı (D2'de yalnız OPEN vardı):
DAX SELL 3 ay n 333 −0,076R, yarılar −0,055/−0,097, P(<0) 0,956, ön dönem n 50 −0,292 → **ENGEL B** (`LIVE_BLOCKED`, 073d01fe, kutuda 19:27 UTC).
DAX BUY 3 ay n 301 −0,109R, yarılar −/−, P 0,985, ön dönem +0,026 → ENGEL C; ama canlıda işlem gören LLM-OPEN alt kümesi +0,035R (D2'yi geçmiyor)
→ DAX BUY canlı kalır (engellenen şey icra edilen popülasyon olmalı).
