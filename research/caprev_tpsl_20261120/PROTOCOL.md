# CAPREV — SL / TP ayrıştırma, daha az SL, daha çok kâr — ÖN KAYIT (2026-11-20, sonuçlardan önce)

## Kullanıcı isteği
"İkinci sıradaki stratejiyi araştırmaya başla" → seçim: **CAPREV** (canlı 2. kural, NDX + DAX, lot 1.0, magic +7).
KORKU ve KSG'de yapılan iş: SL ve TP olan işlemleri ayrıştır, farkı çözümle, SL'leri azalt, TP'leri artır.

## CAPREV (canlı kural, dondurulmuş — `yeni deneme/caprev_live.py`)
- Gün koşulu (gün başında bilinir): önceki seans kapanışı getirisi ≤ −%1,5 VEYA 5 seanslık ≤ −%4 (o piyasanın kendi
  kapanışlarından) ∧ önceki takvim gününün VIX kapanışı ≥ 18,4 ∧ yerel Pzt–Per ∧ erken kapanış günü değil.
- Tetik: pencere içindeki ilk KAPANMIŞ 1 saatlik mum, kapanışı < önceki işlem gününün seans dibi.
  NDX: NY 03:00 ≤ mum başı, mum sonu ≤ 15:00; dip 09:00–16:00 NY. DAX: Berlin 08:00 ≤ mum başı, mum sonu ≤ 16:30; dip 09:00–18:00.
- Giriş tetik mumu bitişinde ask. Stop giriş × (1 − dvol), dvol = son 20 seans kapanış getirisinin std'si. TP yok.
- Çıkış aynı yerel gün seans kapanışı (NDX 16:00 NY, DAX 18:00 Berlin), bid.
- **Canlı lot sabit (1.0)** → stop genişliği değişince R birimi değişir. Bu yüzden ANA ÖLÇÜ R DEĞİL, sabit lotta
  **işlem başına net bp** (spread + gece başına 1,756 bp finansman) ve **kitap Sharpe**'ı (iş günü bazlı günlük bp serisi).
  R ve isabet betimleyici raporlanır.

## Defter kontrolü (3. KURAL) — tekrar edilmeyenler
GF-16/17/18/20/21/22 (kural, stres×VIX hücreleri, çıkış eğrisi "ertesi gün 16:00 en iyi", TP80/SL110 öldürür, +1R hedefi),
CP (`ndx_caprev_paths`: yeni dip, nakit seans, 10:00 başarısız geri alım, düşen VIX → elendi; artan VIX + tam +1R tek başına düşük),
KT-01 D (dokunuş limiti X, derin limit / geç giriş yapma), CK2-02/03 (çakışma dozu C+, dün son saat aşağı → NX-08'de C),
DB-03/04 (VXN primi, artan VIX tanımsız), NX-01 (1m: n 103, +0,278R, ESKİ +0,065 P 0,64 zayıf; ertesi gün 16:00 ESKİ +0,18 dP 0,81).
**Sınanmamış (bu çalışma):**
(S) stop GENİŞLİĞİ ekseni (sabit lotla; şimdiye dek yalnız 1×dvol ölçüldü);
(H) zarardaki işlemi kurtarma — D0 16:00'da zarardaysa tut (KSG KZ-02 / KORKU XP mantığı), stoplu ve stopsuz;
(T) gün içi TP 0,5 / 2,0 × dvol (1,0 = CP'nin +1R'si, yeni beslemelerde yeniden ölçülür, bilgi amaçlı);
(E) giriş anında SL'yi TP'den ayıran özellik (KA-01'in CAPREV karşılığı, KSG'de X);
**bağımsız uzun dönem**: ^NDX günlük 1990–2015 (CAPREV çıkış aileleri için hiç bakılmadı).

## Veri
- **Duka NDX 1m** 2018-01 → 2026-11 (birincil; h/l bid, sp kolonu). KEŞİF ≤ 2021-10-31, TEST sonrası.
- **MT5 NAS100 M30** 2018-05 → 2026-11 (ikinci besleme; 1 sa mum = iki M30). Aynı günler → bağımsız DEĞİL, besleme teyidi.
- Kör ABD endeksleri: MT5 US500 (2018-06+), US30, US2000 M30 (kendi kapanışlarından stres, VIX ortak).
- **DAX**: Duka DAX 1m 2018–26 (canlı ikinci bacak; ayrı piyasa), MT5 GER40 M30 (DAX ikinci besleme, betimleyici). Spread sabit 1,0 puan.
- **U: ^NDX günlük 1990-01 → 2015-12** + VIX 1990+ (bağımsız dönem). Günlük vekil: stres/VIX/Pzt–Per aynı; tetik = gün dibi <
  önceki gün dibi, giriş = min(açılış, önceki dip) (açılış dibin altındaysa açılış), maliyet gidiş-dönüş 2 bp.
  Fiyat sürekliliği: giriş önceki dibin geçildiği an olduğundan gün dibi girişten SONRA gelir → stop dokunuşu günlük veride kesin
  (dolum min(stop, açılış) yalnız gece boşluğunda). Gün içi TP ↔ stop sırası belirsizse stop sayılır (muhafazakâr).
  Saat bilgisi yok → E ailesinde tetik saati özelliği U'da yok.
- Betimleyici ek beslemeler: EET30 30m (2016-11 → 2025-10), NQ 5m (2019-08 → 2024-08), MT5 uzun 1h (2016-05 → 2026-07; kartın
  verisi, E23: çok kez bakıldı).

## Aileler (hücreler sabit)
- **S — stop genişliği, D0 16:00 çıkışı:** k ∈ {0,5; 0,75; 1,5; 2,0; yok (acil %7)} × dvol → 5 hücre (taban 1,0).
- **H — tutuş / kurtarma** (D0 içinde stop aynı; H1–H4 stop 1,0 çıkışa kadar sürer, H5–H8 stopsuz, acil %7):
  H1/H5 D1 09:30 · H2/H6 D1 16:00 · H3/H7 **XP**: D0 16:00'da kârdaysa çık, değilse ilk "yükselen 16:00 kapanışı"nda
  (16:00 > önceki 16:00), en çok 5 işlem günü · H4/H8 **R0**: D0 16:00'da zarardaysa D1 16:00'a tut, kârdaysa çık → 8 hücre.
  (DAX'ta 16:00 yerine 18:00 Berlin, 09:30 yerine 09:00 Berlin.)
- **T — gün içi TP (stop 1,0, D0 16:00):** TP ∈ {0,5; 1,0; 2,0} × dvol → 3 hücre. Aynı mumda TP+stop → stop.
- **E — giriş anında SL/TP ayrımı.** Sınıflar: **SL** = stop dokundu; **TP** = D0 kapanışı artı; **ZK** = stopsuz eksi kapanış.
  Önceden belirlenen 12 özellik (hepsi girişte bilinir): dünkü VIX, VIX d−1 değişimi, r1, r5, dvol, tetik saati (açılış öncesi mi),
  tetik derinliği (pdl − tetik kapanışı)/(giriş×dvol), dünkü kapanıştan girişe değişim / dvol, 20 seans zirvesinden uzaklık / dvol,
  dün son saat yönü (15:00→16:00), hafta günü, vadeye 0–2 işlem günü (OPEX). Betimleyici: SL ↔ TP ortalama farkı + permütasyon p.
  Seçim: KEŞİF'te (Duka ≤ 2021-10 ∪ MT5 uzun 1h 2016-05 → 2021-10, gün bazında tekil) her özelliğin tertil kesimiyle "en kötü
  tertili atla" filtresinin bp farkı; en iyi **1** (özellik, tertil) dondurulur.

## Seçim ve geçme (sabit)
- S, H, T: Duka KEŞİF'te tabana göre işlem başına net bp farkı en yüksek **2 hücre** dondurulur.
- **B:** dondurulan hücre (i) Duka TEST'te ve MT5 NAS100'de (tüm dönem) tabandan iyi; (ii) **bağımsız havuz** (Duka TEST + Duka DAX
  + U günlük 1990–2015) eşli farkı ay bloklu bootstrap P ≥ 0,975 (Bonferroni 2 hücre, NB 3000); (iii) kör üç ABD endeksinin ≥ 2'sinde
  fark > 0; (iv) U ve Duka DAX'ta ayrı ayrı fark > 0; (v) kitap Sharpe Duka ve MT5 NAS100'de artar.
  **C:** (i) geçer ama (ii)–(v)'den biri düşer. **X:** Duka TEST'te ya da MT5 NAS100'de tabandan kötü.
- E: dondurulan filtre Duka TEST, MT5 NAS100 TEST dönemi, Duka DAX ve U'da (tetik saati değilse) fark > 0 ve havuz P ≥ 0,975 → B;
  biri düşerse C; TEST'te eksiyse X.
- Hacim notu: CAPREV yılda ~10 NDX + ~5 DAX olayı. Duka KEŞİF ≈ 40 işlem → seçim gürültülü; bunu düzeltmek için ölçüt sayısı
  artırılmaz, hüküm yukarıdaki gibi verilir.
- Canlıya bağlama bu çalışmadan VERİLMEZ; B çıkarsa ayrı kart + kullanıcı kararı. Sonuçlardan sonra yazılan her ek "EK-n" başlığıyla
  bu dosyanın sonuna eklenir ve hükmü değiştirmez.
