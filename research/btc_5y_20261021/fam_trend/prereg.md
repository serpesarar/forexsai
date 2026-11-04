# ÖN-KAYIT — BTC trend / kırılım / momentum ailesi (fam_trend)

Yazım: 2026-10-21 22:05 UTC. Bu dosya HİÇBİR sonuç hesaplanmadan yazıldı (yalnız veri şekli/sütunları görüldü).
Sonradan DEĞİŞTİRİLMEZ; gerekirse en alta "Amendments" bölümü tarih + gerekçeyle eklenir.

## 0. Veri ve ortak kurallar
- Veri: `research/btc_5y_20261021/data/` Binance BTCUSDT spot; `btc_1m` (yol çözümü), `btc_5m/15m/1h/4h/1d` (sinyal TF'leri;
  `ts` = bar AÇILIŞI, kapanış = ts + TF). Bir bar ancak `ts + TF ≤ karar anı` ise kullanılır (sızıntısız; E16).
- Dışlama: 2023-03-24 11:28–14:00 UTC 1m barları yol çözümünden silinir (eksik dakika gibi davranır); karar anı bu aralıkta
  olan veya sinyal barı bu aralığa değen olaylar atlanır.
- Makro (yalnız H3 gün takvimi için): `merge_asof(avail_utc ≤ karar anı)`.
- Bölmeler (karar anına göre): DISCOVERY 2021-06-01→2023-12-31 · OOS 2024-01-11→2025-06-30 · BLIND 2025-07-01→2026-10-20.
  2024-01-01→01-10 hiçbir bölmeye girmez. İndikatör ısınması 2021-06'dan (EMA200(D1) ilk 200 gün NaN → o günlerde sinyal yok).
- İcra: karar = sinyal barı kapanışı; giriş = karar anından sonraki ilk 1m barın `open`'ı (≤10 dk içinde yoksa olay atlanır).
  Binance fiyatı = mid. LONG: giriş ask = open + h; SL/TP **bid** seviyeleridir (tetik: mid_low − h ≤ SL / mid_high − h ≥ TP);
  zaman çıkışı bid = close − h. SHORT ayna (giriş bid = open − h; tetik ask = mid ± h; çıkış ask = close + h).
  h = yarım spread. Aynı 1m barda SL ve TP → SL. Giriş barında da SL/TP geçerli. SL dolumu boşlukta açılış daha kötüyse açılıştan;
  TP dolumu TP fiyatından (muhafazakâr). Zaman çıkışı = karar + tutuş süresindeki son 1m barın kapanışı.
- Maliyet (Pepperstone BTCUSD CFD): taban gidiş-dönüş spread = %0,0185 × fiyat (h = %0,00925×open); stres (kart 4) = %0,028;
  ek varyant sabit 15 $ (h = 7,5 $). Swap: sunucu gece yarısı = 17:00 New York (21:00 UTC yaz / 22:00 UTC kış) anında açık
  pozisyon için her gece (hafta sonu dahil): long −%14/365 × giriş fiyatı, short +%2/365 × giriş fiyatı (alacak). Gece sayısı =
  giriş_ts < rollover < çıkış anı.
- R = net PnL / ilk risk (giriş − SL mesafesi, $). Ayrıca nominal net % getiri raporlanır (E32).
- İyimser varyant (kart 5): giriş = sinyal barı kapanışı, h = 0, swap aynı.

## 1. Ölçütler
Kart (hepsi gerekli): (1) ≥150 çözülmüş olay; (2) ortR > 0 ∧ gün-blok bootstrap (giriş UTC günü blok, 2000 tekrar) P(EV>0) ≥ %90;
(3) kart penceresinin kronolojik iki yarısı (olay sayısına göre ortadan) ≥ 0; (4) spread %0,028'de ortR > 0;
(5) |ortR(iyimser) − ortR(gerçek)| ≤ 0,5·|ortR(gerçek)|; (6) tek-pozisyon (önceki çıkıştan önce gelen olay atlanır; çıkış anında
yeni giriş serbest) ortR > 0.
Genişletilmiş: (7) P1 plasebo = her olay için aynı takvim yılı × aynı UTC saat:dakika'dan (aynı TF bar kapanışı) rastgele bar,
aynı yön, aynı geometri ve çıkış kuralı, o barın kendi ATR'si; 200 tekrar; gerçek ortR'nin yüzdeliği ≥ %95;
(8) BLIND ortR > 0; (9) Holm (tek yönlü gün-kümeli z, α=0,05) tüm strateji hücreleri üzerinde; (10) sürüklenme-üstü fark için
max-z seçim düzeltmesi p_sel ≤ 0,10 (her hücre z = (ortR − ort(P1))/sd(P1); boş dağılım = her plasebo tekrarında hücreler
üzerinden max z).
Her zaman raporlanır: kapısız taban (aynı TF'nin uygun TÜM barlarında aynı yön + aynı geometri = P1'in beklentisi),
başabaş WR = ort|kayıp R| / (ort kazanç R + ort|kayıp R|), n_olay, n_gün, n_tekpoz, WR, ortR, %95 GA, yıl bazında ortR,
tek-pozisyon setinde en iyi 5/20 gün hariç ortR (E31: set = tek-poz, gün = giriş UTC günü), sabit 15 $ varyantı.

Kart penceresi: dondurulmuş (başka piyasadan aynen taşınan) BİRİNCİL hücreler için TAM dönem (üç bölme birleşik) — BTC'de
parametre seçilmediği için hepsi örneklem dışıdır; ayrıca bölme bazında rapor. H3 (ETF sonrası hipotezi) için kart penceresi
OOS ∪ BLIND. DISCOVERY'de seçilen (birincilden farklı) hücreler için kart penceresi OOS ∪ BLIND.
Seçim kuralı: her hipotez ızgarasında DISCOVERY gerçek-maliyet ortR'si en yüksek hücre "seçilen"dir.

Verdikt: LIVE = 1–10 hepsi. SHADOW = LIVE değil ama ortR > taban ∧ kart 2–6'dan en fazla biri düşer (yalnız hacim düşüyorsa da
SHADOW: "yapısal olarak geçilemez"). RED = ortR ≤ taban VEYA kart 2–6'dan 2+ düşer.
Defter sınıfı: geçen/çoğu tutan ama hacim düşen → B; tutarsız/taban altı → X; negatif kontrol beklendiği gibi düşerse "X (beklenen)".

## 2. Hipotezler, tanımlar, ızgaralar (★ = birincil, dondurulmuş)

### BT-GD — Günlük Golden Donchian (XAU XS-01 kuralı aynen)
- Sinyal (D1, gün UTC 00:00): kapanış ≥ önceki N günün high maksimumu (o gün hariç) ∧ kapanış > EMA200(D1 kapanış, adjust=False)
  → karar = gün kapanışı (ertesi 00:00), BUY. SL 2×ATR14(D1, Wilder, sinyal günü dahil), TP 4×ATR14, zaman stopu 20×24 saat.
- Hücreler: ★GD55-L; GD40-L, GD70-L (plato); GD55-L-noEMA (EMA filtresi yok, bilgi); GD55-S (ayna: kapanış ≤ önceki 55 low ∧
  kapanış < EMA200 → SELL).
- Taban: her gün BUY (SELL hücresi için her gün SELL) aynı geometri; ek P2 = EMA200 üstündeki her gün BUY.
- Not: ~5,4 yılda n ≥ 150 beklenmez → ölçüt 1 "yapısal olarak geçilemez" diye önceden yazılır; en iyi verdikt SHADOW.

### BT-MX — Literatür MAX10/MIN10 (Padysak & Vojtko)
- MAX10: günlük kapanış = son 10 kapanışın (bugün dahil) maksimumu. MIN10: minimumu. Karar = gün kapanışı.
- Hücreler: ★MX10-L-1d (MAX10 → BUY, 24 saat tut; SL 2×ATR14(D1) felaket stopu, TP yok);
  ★MN10-S-1d (MIN10 → SELL, aynı geometri; "iki yön" = bu iki hücrenin birleşimi ayrıca raporlanır: MXMN10-LS-1d);
  MN10-L-1d (MIN10 → BUY, literatürün dip kolu, bilgi); MX20-L-1d (plato);
  MX10-L-H6 (BUY; çıkış: kapanış ≤ son 10 kapanış minimumu olan ilk gün kapanışında, en geç 20 gün; SL 2×ATR14 felaket stopu);
  MN10-S-H6 (ayna).
- Taban: her gün BUY / SELL, aynı tutuş ve stop.

### BT-H4 — H4 Donchian kırılımı
- Sinyal: H4 kapanış ≥ önceki N H4 high maksimumu → BUY; kapanış ≤ önceki N low minimumu → SELL. SL 2×ATR14(H4), TP 4×ATR14(H4),
  zaman 30 H4 bar (120 saat).
- Hücreler: N ∈ {20, 55} × yön {L, S} × trend {yok, D1 hizalı (son kapalı D1 kapanışı EMA200(D1) üstü/altı)} = 8.
  ★H4D20-L ve ★H4D20-S (filtresiz) birincil; diğerleri ızgara.
- Taban: her H4 kapanışında aynı yön, aynı geometri.

### BT-R0B — 1h yeni 20-bar tepesi (XAU R0B_G1 aynen) + S2
- Sinyal: H1 high ≥ önceki 20 H1 high'ın maksimumu → BUY; SL 1,5×ATR14(H1, sinyal barı dahil), TP yok, zaman 20 saat;
  tek-pozisyon ölçütünde çıkış anında yeni sinyal açılabilir.
- Hücreler: ★R0B-L; R0B-S (ayna: low ≤ önceki 20 low → SELL);
  ★R0B-L-S2σ: önceki tam UTC günü getirisi > +1,0×dvol20 ise ATLA (dvol20 = o güne kadarki son 20 günlük kapanış-kapanış
  getirisinin std'si; atlanan olay pozisyonu kilitlemez); R0B-L-S2σ0.75, R0B-L-S2σ1.25 (plato); R0B-L-S2lit (literal +%1);
  R0B-S-S2σ (ayna: önceki gün < −1,0×dvol20 ise SELL'i atla).
- S2 geçme (MK-13 deseni): atlanan grup ortR < kalan grup, filtreli tek-poz ortR > filtresiz, BLIND'da aynı işaret.
- Taban: her H1 kapanışında aynı yön, aynı geometri.

### BT-MOM — Momentum filtresi (bot MOMENTUM_FILTER) + geometri
- BUY koşulu (son kapalı 15m bar): stoch %K(14, ham/fast) > 70 ∧ (close − EMA20)/ATR14(15m) > 0,8 ∧ son kapalı H1 barda
  Parabolic SAR(0,02; 0,2) < H1 kapanışı. SELL aynası: %K < 30 ∧ dist < −0,8 ∧ SAR > kapanış.
  Epizod bastırma: koşul önceki 15m barda da doğruysa olay değil (ilk geçiş).
- Geometri G1: TP 2,0×ATR14(H1) / SL 1,0×ATR14(H1); G2 (bot yakın hedef, ölçeklenmiş): TP 0,73×ATR14(H1) / SL 1,0×ATR14(H1).
  İkisinde de 24 saat sınırında piyasa çıkışı.
- Hücreler: ★MOM-L-G1, MOM-L-G2, MOM-S-G1, MOM-S-G2. Beklenti: G2 başabaş altı (OLD-20).
- Taban: her 15m kapanışında aynı yön + geometri.

### BT-H3 — ETF sonrası gün-içi momentum (Shen-Urquhart-Wang; not 03 H3)
- Gün: NYSE işlem günü (macro_daily'de ndx_close dolu tarih). İlk yarım saat getirisi r1 = BTC 09:30→10:00 New York
  (09:30 1m open → 09:59 1m close). Karar 15:30 NY: yön = sign(r1) (r1=0 → olay yok); giriş 15:30 1m open, çıkış 16:00 NY
  (15:59 1m close); SL 1,0×ATR14(H1) (son kapalı H1), TP yok.
- Hücreler: ★H3-L30; H3-L30-HV (yalnız ATR14(D1) > son 60 günün ATR14(D1) medyanı olan günler; Shen yan tahmini: HV ortR > tüm);
  H3-ROD (bilgi: karar 10:00, 10:00→16:00 tut, aynı SL).
- Kart penceresi OOS ∪ BLIND (ETF sonrası); DISCOVERY kıyas için.
- Taban: aynı günlerde aynı pencerede her zaman BUY (ve her zaman SELL) aynı SL.

### BT-N5 — Negatif kontrol: 5m Donchian48 (USOIL breakout kuralı)
- Sinyal: 5m kapanış > önceki 48 bar high maks. ∧ önceki bar kapanışı ≤ kendi önceki-48 maks. (ilk geçiş) ∧ kapanış > EMA200(5m)
  ∧ (kapanış − seviye)/ATR14(5m) ≤ 0,5 → BUY; TP = SL = 1×ATR14(5m); 24 saat sınırı. Ayna SELL ★N5-S. ★N5-L.
- Beklenti: geçmemeli; iyimser−gerçek farkı kart 5'in BTC duyarlılığını kalibre eder.

## 3. Aile ve düzeltme
- Strateji hücreleri (tabanlar hariç) tek aile: Holm + max-z bunların hepsi üzerinde. Negatif kontrol de aileye dahildir.
- Izgara dışında hücre koşulursa "Amendments"e yazılır ve aileye eklenir.

## Amendments
(boş)

### A1 — 2026-10-21 22:40 UTC (ilk koşudan SONRA eklendi; gerekçe)
İlk koşuda prereg §2 BT-H4'te trend filtreli hücreler (H4D*-T-*) için **P2 (trend-koşullu taban)** yazılmamıştı; oysa girdi
notu 01/H07 bunu "zorunlu kontrol" diye ön-kaydetmişti (MK-07: D1 trend filtresi sürüklenmeyi seçer). Eksik ölçüt eklendi:
P2 = aynı D1 trend durumundaki (L: son kapalı D1 kapanışı > EMA200; S: <) TÜM H4 kapanışlarında aynı yön + aynı geometri;
P2 plasebosu = trend durumundaki barlardan aynı yıl × UTC saati rastgele çekiliş (200 tekrar). Geçme: hücre ortR > P2 ortR ve
P2-plasebo yüzdeliği ≥ %95. Kararlar (verdikt) bu ek ölçütle sertleşebilir, gevşeyemez.
Ayrıca bilgi amaçlı (verdikti değiştirmez): seçili uzun tutuşlu hücrelerde swap=0 ile ortR (swap'ın R maliyeti) ve
motor yansızlık testi (`diag_synth.py`, karıştırılmış 1m bar yolu) ile stop-sonrası devam teşhisi (`diag_stop.py`).
