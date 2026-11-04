# Zaman-serisi momentumu / kırılım devamı — NASDAQ-100 (gün içi → çok günlü, ZAMAN çıkışlı)

> Yerel kanıtın tamamı: `research/nasdaq_derin_20261013/breakout_momentum/` — ön kayıt `PROTOCOL.md` (sonuçlardan ÖNCE
> yazıldı), kod `bm.py` (ızgara + kasa + kartlar), `diag.py` (kasadan SONRA, yalnız betimleyici), çıktılar `results/`
> (`grid.log`, `kasa.log`, `diag.log`, `grid_*.csv`, `placebo_ndx_kesif.csv`, `kasa.json`, `secim.json`, `yil_ndx.csv`).
> Aşağıda `[grid.log]` vb. bu klasördeki dosyalardır:
> `/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/breakout_momentum/results/`.
> Birim: ızgarada ATR(14, sinyal mumundan ÖNCEKİ 14 mum); kartlarda stop mesafesi (R). Giriş = sinyal mumunun kapanışından
> sonraki mumun açılışı + 1,5 puan spread. "Fazla" = olayın R'si − aynı (takvim yılı × UTC saat) hücresindeki aynı
> TF/tutma/stop/yönlü **rastgele işlem** ortalaması (NDX'in yukarı sürüklenmesi çıkarılmış).

## 1. Literatür: hisse endeksi vadelilerinde TSMOM / kırılım ne diyor (Sharpe, sönümlenme, rejim, çöküş riski)?

### Takeaway
Hisse endeksi vadelilerinde TSMOM'un akademik kanıtı **aylık ufukta** (1–12 ay geriye bakış, ~1 ay tutma) güçlüdür; **kısa
geriye bakışta zayıftır** ve son on yıllarda kısa trendler sönümlenmiştir. Endekslerin **günlük** seri bağımlılığı 2000'lerden
beri NEGATİF (NASDAQ-100 dahil). Gün içinde ise ayrı bir "piyasa gün içi momentumu" (gün içi getiri → son 30 dk) belgelenmiştir
ve 2000–2020'de hisse vadelilerinde daha da güçlüdür. Yani "gün içi momentum + günlük dönüş" ikiliği literatürle uyumludur.

### Cited Findings
- MOP (2012): 58 vadeli (9 gelişmiş endeks dahil) için "significant 'time series momentum'"; getiriler 1–12 ay sürer, daha uzun
  ufukta kısmen geri döner; çeşitlendirilmiş portföy uç piyasalarda en iyi — [Moskowitz, Ooi, Pedersen 2012, JFE (PDF)](https://fairmodel.econ.yale.edu/ec439/jpde.pdf)
- MOP Tablo 2 Panel C (hisse endeksi vadelileri, faktör-düzeltilmiş alfa t-istatistikleri): 12 ay geriye bakış/1 ay tutma
  t=3,77; 9 ay/1 ay t=4,21; ama **1 ay geriye bakış/1 ay tutma t=1,05** (kısa sinyal endekslerde zayıf); 24+ ay tutmada t sönüyor — [MOP 2012](https://fairmodel.econ.yale.edu/ec439/jpde.pdf)
- MOP: çeşitlendirilmiş TSMOM Sharpe > 1 (pasif hisse piyasasının ~2,5 katı); TSMOM getirisi piyasa getirisinin karesine
  pozitif yükleniyor ("smile" — büyük yukarı ve aşağı aylarda en iyi); 2009 gibi kriz bitişlerindeki sert dönüşlerde kaybediyor — [MOP 2012](https://fairmodel.econ.yale.edu/ec439/jpde.pdf)
- MOP: TSMOM'u "her zaman long" stratejisine regresyonla karşılaştırınca durumların %90'ında pozitif alfa ama yalnız %26'sı
  anlamlı — yani tek enstrümanda kenarın önemli kısmı pasif uzun pozisyondan ayırt edilmesi zor — [MOP 2012](https://fairmodel.econ.yale.edu/ec439/jpde.pdf)
- Hurst/Ooi/Pedersen (2017): 1880–2016, 67 piyasa (11 hisse endeksi); her on yılda pozitif; piyasa başına ortalama Sharpe ≈0,4;
  60/40'ın en kötü 10 düşüşünün 8'inde pozitif; ama **1987 gibi çok hızlı çöküşlerde** pozisyonu çeviremediği için iyi
  değil; sinyal 1 ay geciktirilince performans özellikle kısa sinyallerde bozuluyor — [Hurst, Ooi, Pedersen 2017, JPM (PDF)](https://fairmodel.econ.yale.edu/ec439/hurst.pdf)
- Lempérière ve ark. (CFM, 2014): trend fazla getirisi sürüklenme çıkarıldıktan sonra t≈5 (1960+), t≈10 (1800+); "no sign of a
  statistical degradation of long trends, whereas **shorter trends have significantly withered**" — [arXiv 1404.3274](https://arxiv.org/abs/1404.3274)
- Huang/Li/Wang/Zhou (2020): varlık-varlık zaman serisi regresyonlarında TSMOM kanıtı zayıf; havuzlanmış t-istatistiği
  bootstrap kritik değerlerini geçmiyor; TSMOM stratejisinin performansı tahmin gücü gerektirmeyen tarihsel-ortalama
  stratejisiyle "virtually the same" — [JFE 135(3) özet, RePEc](https://ideas.repec.org/a/eee/jfinec/v135y2020i3p774-794.html)
- Baltussen/van Bekkum/Da (JFE 2019): 20 endekste seri bağımlılık 1990'lara kadar pozitif, **2000'lerden beri negatif**;
  endeks ürünlerinin (vadeli, ETF) yaygınlaşmasına bağlanıyor. Tablo 1: **Nasdaq 100 günlük AR(1) önce +0,071, sonra
  −0,065 (fark t=−3,45)**; S&P 500 +0,103 → −0,076; DAX +0,066 → −0,016 (Mart 1999 öncesi/sonrası) — [kabul edilmiş el yazması PDF](https://personal.eur.nl/vanbekkum/2018%20JFE%20BaltussenVanBekkumDa.pdf)
- Baltussen/Da/Lammers/Martens (JFE 2021): 60+ vadeli, 1974–2020; son 30 dk getirisi günün geri kalanının getirisiyle
  pozitif öngörülüyor ve **sonraki günlerde geri dönüyor**; mekanizma kısa-gamma hedge talebi (opsiyon piyasa yapıcıları,
  kaldıraçlı ETF'ler). Hisse vadelilerinde eğim 1974–99'da 3,73 (R² %0,53) → 2000–2020'de 4,97 (R² %1,67). NASDAQ-100 (NQ)
  örneklemde. Hisse endeksi vadelileri zamanlama stratejisi η(r_ROD) Sharpe 1,73 vs "her zaman long" 0,11 (maliyetsiz) — [Baltussen ve ark. 2021 (PDF)](https://academicweb.nd.edu/~zda/intramom.pdf)
- Zarattini/Aziz/Barbon (2024, SPY): gün içi "gürültü alanı" kırılımı + iz süren stop; 2007–2024 Sharpe 1,33, yıllık %19,6
  (maliyet sonrası, örneklem içi geriye test) — [Concretum özet](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/); [SFI 24-97](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy)
- Bajgrowicz/Scaillet (JFE 2012): DJIA günlük 1897–2011, binlerce teknik kural, FDR ile veri madenciliği düzeltmesi:
  yatırımcı en iyi kuralları **önceden seçemezdi**; düşük işlem maliyeti bile performansı tamamen siliyor — [RePEc](https://ideas.repec.org:443/a/eee/jfinec/v106y2012i3p473-491.html); [CFA Digest](https://rpc.cfainstitute.org/research/cfa-digest/2013/02/technical-trading-revisited-false-discoveries-persistence-tests-and-transaction-costs-digest)
- Goulding/Harvey/Mazzoleni (JFE 2023): TSMOM'un zayıf noktası dönüş noktaları — yavaş sinyal geç kalır, hızlı sinyal yanlış
  alarm üretir; "Bear" durumları yüksek risk ama negatif beklenen getiri; hızı döngü durumuna göre ayarlamak Sharpe'ı artırıyor — [Duke Scholars kaydı](https://scholars.duke.edu/publication/1586630); [Alpha Architect özeti](https://alphaarchitect.com/momentum-trends/)
- Çapraz-kesit momentum "çöküşleri" ayı piyasası sonrası, yüksek oynaklıkta, toparlanma ile eşzamanlı (1932, 2009) — [Daniel & Moskowitz, NBER w20439](https://www.nber.org/system/files/working_papers/w20439/w20439.pdf)

### Inferences
- Aylık TSMOM'un kanıtı bizim 30m–günlük ızgaramıza doğrudan taşınmaz: MOP'ta endeks paneli 1 aylık geriye bakışta zaten
  anlamsız (t=1,05). Bizim en uzun penceremiz (günlük N=60 ≈ 3 ay, H=40 gün) bile tek enstrüman + 10 yıl → istatistiksel güç düşük.
- Literatürün iki gerçeği (günlük negatif oto-korelasyon NDX'te −0,065; gün içi momentum hisse vadelilerinde güçlenmiş)
  birlikte "kırılım devamı gün içinde var, gün ölçeğinde yok/ters" öngörür — yerel sonuçlarımız tam bu deseni verdi (§2).
- Bajgrowicz-Scaillet ve Huang ve ark. "ızgaranın en iyi hücresi"ne güvenmenin klasik tuzağını belgeliyor → ızgara-düzeyi
  karar + seçim-düzeltmeli plasebo zorunlu (defter E23/E24 ile aynı ders).

### Gaps
- MOP'ta hisse endeksi başına (S&P 500 ayrı) TSMOM Sharpe'ı Şekil 2'de grafik; sayısal değeri PDF metninden çıkaramadım.
- NASDAQ-100'e özgü gün içi kırılım/Donchian akademik çalışması bulamadım; Zarattini ve ark. SPY üzerine ve örneklem içi.
- Hurst ve ark.'nın on yıl bazında hisse endeksi alt-kırılımı (son on yılda endekslerde sönüm) metinde yok; yalnız tüm-portföy.

## 2. NDX'te hangi ön-kayıtlı kural ailesi aynı-TF rastgele BUY'ı geçiyor? (ızgara oranı ve düzgünlük; en iyi hücre değil)

### Takeaway
**Genel "TSMOM/kırılım" hipotezi ızgara düzeyinde GEÇMEDİ:** keşifte (NDX, <2026-07-01) BUY hücrelerinin fazla getirisi
>0 oranı stopsuz %29, 1,5 ATR stoplu %48, 2 ATR %47 — ön kayıt eşiği %75 ve plasebo %95'i (%70–75) altında. Ama sonuç
TF'ye göre **keskin biçimde ikiye ayrılıyor**: 30m ve 1h'te (stoplu) neredeyse tüm hücreler pozitif ve düzgün; 4h ve
günlükte neredeyse tümü negatif. Kenar, kırılımın **ilk saatinde** ve **ABD seansında** yoğunlaşıyor (post-hoc teşhis).

### Cited Findings
- Izgara: 4 aile (F1 yeni tepe, F2 kapanış Donchian, F3 F2+EMA200, F4 TSMOM işareti) × N{10,20,40,60} × H{10,20,40} × TF{30m,1h,4h,D}
  × stop{yok,1,5,2 ATR} × yön; keşif BUY pozitif oranı %29/%48/%47, medyan fazla −0,074/−0,007/−0,013 ATR; dairesel-kaydırma
  plasebosu (50 tekrar) ort %46–47, %95 %70–75 → **G1 ✗** — [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- TF × aile pozitif hücre (/12), BUY stop 1,5: 1h F1/F2/F3/F4 = 12/12/12/9; 30m 11/11/11/12; **4h 1/0/0/1; günlük 0/0/0/0**.
  Stopsuz: 1h 5/11/11/1, 30m 7/7/8/6, 4h 0, günlük 0 — [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- Örnek yüzeyler (keşif, fazla ATR): 1h stop 1,5 F3 satırları +0,087…+0,174 (tüm N×H pozitif, N ve H büyüdükçe artıyor);
  4h stopsuz F2 −0,098…−0,630; günlük F1 N20 H20 BUY ham +0,735 vs rastgele +0,864 — [grid_ndx_kesif.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid_ndx_kesif.csv)
- MK-02 ipucu hücresinin (F1 N20 H20 30m) yeniden ölçümü: tüm-sinyal stopsuz ham +0,159 vs eşlemesiz taban +0,058 (fark +0,101);
  **yıl×saat eşli fazla +0,056**; tek-pozisyon işlem listesinde fazla **+0,004** (P %51) — yani T5'in "+0,167"si büyük ölçüde
  saat karışımı ve 2023-10 sonrası dönem seçimiydi — [grid_ndx_kesif.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid_ndx_kesif.csv), [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- Seçim-düzeltmeli kontrol (E24): keşifte komşuluk-yumuşatılmış en iyi stoplu BUY hücresi +0,150; aynı arama plasebo
  olay kümelerinde yapılınca maks ortalaması +0,239, %95 +0,504 → **p=0,60** (tüm ızgara). Yalnız 1h içinde: 1h stoplu
  F1–F3 ort. fazla +0,097 vs plasebo %95 +0,100 (p=0,10); maks p=0,10. H-S hücresinin kendisi plasebo ort −0,001, sd 0,107,
  gözlenen +0,174 → p=0,08 — [placebo_ndx_kesif.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/placebo_ndx_kesif.csv) (hesap bu oturumda, `grid.log` sonrası)
- POST-HOC teşhis (H-S kuralı NDX 1h F3 N60 H40 stop 1,5, tüm sinyaller): girişi d mum geciktirince fazla d=0 +0,136 · d=1
  +0,043 · d=2 +0,042 · d=4 −0,027 · d=8 −0,025 (stop birimi). Sinyal saatine göre: ABD 13–20 UTC +0,296 (n=1.443), Avrupa
  07–13 +0,051, Asya 22–07 −0,100, akşam 20–22 +0,168. Aynı kural 4h N10 H10 ≈0,000 — [diag.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/diag.log)

### Inferences
- "Yeni N-mum tepesi"nin bilgi içeriği yalnız ilk 1–2 saatte; 4h/günlük mum kapandığında o hareket zaten fiyatlanmış ve geri
  kalan ufukta günlük ölçekte dönüş (literatürdeki NDX negatif AR(1)) baskın. Bu, 1h-pozitif / 4h-negatif kopukluğunu açıklar.
- ABD seansı yoğunlaşması Baltussen ve ark.'nın gamma-hedge gün içi momentumuyla uyumlu ama burada mekanizma ayrıca
  sınanmadı (gamma verisi yok).
- Izgara kararı ön kayda göre olumsuz; "kırılım devamı" ancak **dar bir rejimde** (1h/30m, stoplu, ABD seansı, ilk saat) var.

### Gaps
- Gecikme/seans teşhisleri kasa okunduktan sonra yapıldı (post-hoc) → yeni ön kayıt + ileri gölge olmadan kural olarak kullanılmamalı.
- 5m/15m TF'ler ön kayıtta yoktu (MK-02'de NDX 5m −0,020); "ilk saat" bulgusu daha kısa TF'de sınanmadı.

## 3. Kenar yalnız BUY mı? (SELL aynası: yeni N-mum dibi → SELL)

### Takeaway
Evet — NDX'te SELL aynası her yerde rastgele SELL'den KÖTÜ (keşif %20–31 pozitif, kasa %6–7), **2022 ayı piyasasında bile**.
"Korku döner, coşku dönmez" meta-dersiyle tutarlı. DAX'ta ise gün içi SELL aynası da pozitif (iki yönlü trend) → asimetri NDX'e özgü.

### Cited Findings
- NDX keşif SELL fazla>0 oranı: stopsuz %20, 1,5 ATR %25, 2 ATR %31 (plasebo %95 %73–76); 1h F1–F3 2–9/12; 4h ve günlük 0/12 — [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- NDX kasa (2026-07→10) SELL: %30 / %6 / %7 pozitif; medyan fazla −0,09…−0,29 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- 2022 (NDX ayı yılı), tüm TF'ler: SELL hücrelerinin yalnız %21'i rastgele SELL'i geçiyor (medyan fazla −0,164); ham SELL
  medyan +0,198 ATR ama rastgele SELL +0,406. H-S'nin aynası (1h F3 N60 H40 stop 1,5) 2022'de SELL −0,167 vs rastgele SELL
  +0,420 (fazla −0,555) — [yil_ndx.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/yil_ndx.csv), [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- DAX (tüm dönem) SELL stop 1,5: 1h F1/F2/F3 12/11/11, 30m 11/11/12 pozitif; günlük 0/3/8 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)

### Inferences
- NDX'te yeni dipte satmak ayı yılında bile rastgele satıştan kötü: dipler (gün içi ölçekte bile) toparlanıyor; defterdeki
  GF-12/GF-16 (CAPREV) ve meta-ders 2 ile aynı yön. Bu bir *momentum SELL yasağı* gerekçesi olarak okunabilir (gölge kapı adayı değil, betim).
- DAX'ta iki yönlü gün içi trend → mekanizma "NDX'in dip alıcıları" gibi piyasaya özgü bir şey; genel TSMOM değil.

### Gaps
- SELL aynası için kart yapılmadı (ön kayıtta yalnız BUY kartı vardı).

## 4. Sadece NDX'in yukarı sürüklenmesine beta mı? (yıl-eşli taban, 2022)

### Takeaway
Ham pozitif R'nin çoğu beta: rastgele BUY bile aynı stop/çıkışla **6 ölçütlü kartın 1–6'sını geçiyor** (1h H40 stop 1,5:
+0,115R, P %99,9). Ama H-S hücresinin yıl×saat eşli fazlası (+0,240R) sürüklenmeden fazlası; ve gecikme testi kenarın
ay-düzeyi rejim değil **kırılım anı** olduğunu gösteriyor (4 saat gecikmede fazla sıfıra iniyor). 2022'de H-S BUY para
kaybetti (−0,071 ATR) ama rastgele BUY'dan iyiydi (+0,054 fazla).

### Cited Findings
- KONTROL kartı "rastgele BUY, 1h H40 stop 1,5": n=3.360, ortR +0,115, P(EV>0) %99,9, yarılar +0,096/+0,134, spread×1,5 +0,094
  → ölçüt 1–6 ✓, ölçüt 7 (taban) ✗ — **CLAUDE.md kartı tek başına NDX'te sürüklenmeyi ölçüyor** — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- Aynı kontrol 30m H20 stop 2: ortR +0,017, P %75,5 (2. ölçüt ✗) — sürüklenmenin kartı geçirmesi ufka bağlı — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- H-S yıl yıl fazla (R): 2016 −0,215, 2017 +0,354, 2018 +0,346, 2019 −0,082, 2020 +0,164, 2021 +0,512, 2022 +0,137, 2023 +0,314,
  2024 +0,320, 2025 +0,184, 2026 +0,555 → 9/11 yıl pozitif — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- 2022, 1h F3 N60 H40: BUY stop 1,5 ham −0,071 vs rastgele −0,131 (fazla +0,054); stopsuz −0,873 vs −0,911 — [yil_ndx.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/yil_ndx.csv)
- Tüm ızgarada 2022 BUY: %37 hücre pozitif fazla, ham medyan −0,359 vs taban −0,275; 2020: %26 pozitif; 2018: %59 — [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- Yıl-ay eşli taban (ikincil, ön kayıtta "ticari değil" diye işaretli): hem BUY hem SELL hücrelerinde sistematik negatif
  (keşif BUY stopsuz yalnız %7, SELL %5 pozitif) → ayın kendi yolunu içerdiği için iki yöne de aleyhte yanlı (E15'in ay
  ölçeğinde tekrarı), karar için kullanılmadı — [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- Gecikme testi: d=4 saatte fazla −0,027 (ay-düzeyi rejim aynı kalırken) — [diag.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/diag.log)

### Inferences
- Kart ölçütlerine "aynı stoplu rastgele BUY tabanına göre fazla" (bizim 7. ölçüt) eklenmeden NDX BUY kartları sürüklenme
  ölçer. Bu, 2. KURAL için bir yöntem önerisidir (defter §1'e E-adayı).
- Kalan fazla getiri "beta" ile açıklanamıyor ama 2022 gibi ayı yılında mutlak olarak para kaybettiriyor → canlıda rejim riski var.

### Gaps
- Geçmişe bakan (yalnız geçmiş verili) trend-durumu eşli taban (ör. "aynı EMA200/60-mum getirisi durumundaki rastgele mum")
  sistematik yapılmadı; F4 (yalnız trend durumu) hücrelerinin ≈0 fazlası dolaylı kanıt.

## 5. Koruyucu stopla (1,5×ATR, 2×ATR) yaşıyor mu?

### Takeaway
Paradoks: NDX'te kenar **stopla ortaya çıkıyor**. Stopsuz uç kayıplar felaket (−42 ATR), stopla en kötü −2,4R. H-S kuralında
stopsuz fazla +0,052 ATR iken 1–1,5 ATR stopla +0,136–0,138 (stop birimi). Ama getiri profili piyango: WR %29, medyan −1R,
kârın %181'i en iyi %10 işlemden.

### Cited Findings
- H-S kuralı (tüm sinyaller) stop duyarlılığı, fazla: stopsuz +0,052 (ATR) · 1,0 ATR +0,138 · 1,5 +0,136 · 2,0 +0,097 · 3,0 +0,057
  (stop birimi) — [diag.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/diag.log)
- Stopsuz ipucu hücresi (H-A) en kötü işlem −42,18 ATR; en iyi 5 gün çıkınca toplam +121,6 → −40,2; kontrol rastgele BUY stopsuz en kötü −39,07 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- H-S tek-pozisyon listesi: 796 işlem, 712 bağımsız giriş günü, WR %29,4, ort +0,368R, medyan −1,0R, dağılım q75 +1,32R, q95
  +6,25R, q99 +8,88R; maks düşüş −20,9R; en uzun kayıp serisi 12; ort tutma 18,4 mum; yılda ~77 işlem — [diag.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/diag.log)
- Stop sim doğrulaması: vektörize stop/çıkış, 3.000 rastgele mumda döngüyle birebir (BUY/SELL 0 uyuşmazlık) — bu oturumda `bm.outcome` kontrolü

### Inferences
- Martingalde stop beklentiyi değiştiremez; stoplu sürümün rastgeleye üstünlüğü, kırılım sonrası yolların daha "trendli"
  olduğunu (başarısız kırılımın düşüşü sürüyor, başarılının yükselişi sürüyor) gösterir — mekanizma tutarlı ama ince.
- Medyan −1R, 12'lik kayıp serisi ve −21R düşüş: psikolojik/operasyonel olarak zor; canlıda "kazananı koştur" mantığı (M3/M4) ile aynı aileden.

### Gaps
- Stop dolumu 1h mum üzerinden (mum içi sıra bilinmez, stop önce varsayıldı; boşlukta açılış). 1m ile katı icra sınanmadı
  (MK-02 T6 benzeri); ABD açılışı oynaklığında stop kayması modelde yok.

## 6. Kasa (2026-07-01 → 10-02, bir kez) ve DAX (bağımsız piyasa, ayar yok)

### Takeaway
Kasa güçlü pozitif (BUY stoplu hücrelerin %92–93'ü pozitif; H-S 13 işlem +1,155R) ama tek rejim ve küçük. DAX karışık: H-S
hücresi DAX 1h'te pozitif ama zayıf (fazla +0,083R, P %81); DAX 30m'de stoplu BUY F1–F3 0/12 (ters), 4h'te 10–12/12;
**DAX günlük 2008–2018 (tek gerçekten görülmemiş örneklem): 48 BUY hücresinin 0'ı pozitif** — günlük kırılım iki piyasada da yok.

### Cited Findings
- NDX kasa ızgarası: BUY pozitif oran stopsuz %77 (medyan +0,182), 1,5 ATR %93 (+0,514), 2 ATR %92; 1h ve 30m F1–F4 12/12 —
  ⚠ kasa 3 ay, güçlü yükseliş dönemi — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- H-S kasa: 13 tek-poz işlem, ortR +1,155, fazla +1,155, P %89,7, en iyi 5 gün çıkınca −8,0 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- H-A (ipucu, stop 2) kasa: 79 işlem ortR +0,142, fazla +0,157 (P %79); H-A stopsuz kasa −0,023 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- DAX tüm dönem BUY pozitif oranı: stopsuz %36, 1,5 ATR %46, 2 ATR %47; TF × aile (stop 1,5) 1h 11/6/6/12, 30m 0/0/0/11, 4h 10/12/10/5, D 2/3/1/0 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- DAX günlük 2008–2018: BUY fazla>0 %0 (stopsuz medyan −0,450), %2 (1,5), %0 (2); SELL %0 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- DAX H-S kartı (1h F3 N60 H40 stop 1,5): 498 işlem, ortR +0,183, P %97,8, yarılar +0,166/+0,200, spread×1,5 +0,179, icra
  farkı +0,067, fazla +0,083 (P %81,0, taban +0,101); yıl fazla 2019 −0,053, 2020 +0,401, 2021 +0,165, 2022 −0,123, 2023 +0,253,
  2024 −0,076, 2025 +0,056, 2026 −0,039 (4/8); tüm-sinyal fazlasının 2. yarısı −0,028 — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log), [grid_dax.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid_dax.csv)
- H-A DAX stop 2: fazla +0,040 (P %85), yarılar −0,012/+0,158 (3. ölçüt ✗) — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)

### Inferences
- DAX "teyit" sayılmaz: işaret pozitif ama anlamlı değil, yıllar yarı yarıya, 30m'de ters. Görülmüş DAX ≥2019 verisinde
  bile zayıf; görülmemiş DAX günlükte günlük kırılım tamamen ölü.
- Kasanın büyüklüğü (medyan +0,5 ATR) tek bir trendli çeyreğin etkisi; ızgara-düzeyi keşif sonucuyla (%48) birlikte okununca
  rejim-bağımlı olduğu açık.

### Gaps
- DAX gün içi verisi 2019 öncesinde yok (dax_1h 2019 öncesi haftalık/günlük/4h karışık) → gün içi bağımsız uzun örneklem yok.
- QQQ/SPX gün içi veri yerelde yok; SPX/QQQ ile bağımsız sınama yapılmadı.

## 7. En iyi ön-kayıtlı varyant canlıya alma kartını geçiyor mu? (E23 dikkate alınarak)

### Takeaway
**H-S (NDX 1h F3: kapanış > önceki 60 mumun tepesi ve > EMA200 → BUY, 40 mum zaman çıkışı, 1,5×ATR stop) kartın 6/6'sını
ve ön kayıttaki ek 7–9'u (rastgele-BUY'a göre fazla P %99,7, kasa > 0, DAX > 0) GEÇTİ → protokol verdikti "LIVE adayı, önce
gölge".** Ama dürüst sınıf **B− / GÖLGE**: ızgara-düzeyi hipotez reddedildi, seçim-düzeltmeli p=0,60 (1h içinde 0,10),
plasebo kümelenmesi bootstrap'ın %99,7'sini p≈0,08'e indiriyor, DAX yalnız P %81, kasa 13 işlem, NDX 1h geçmişine 5. tur bakış (E23).

### Cited Findings
- H-S tüm dönem (keşif+kasa) kartı: 796 işlem ✓; ortR +0,368, P %100,0 ✓; yarılar +0,270/+0,465 ✓; spread×1,5 +0,327 ✓;
  iyimser giriş +0,414 vs gerçek +0,368 (fark +0,047 < 0,184) ✓; tek-poz +0,368 (tüm sinyal n=3.034 +0,261) ✓; fazla +0,240
  P %99,7 ✓; en iyi 5 gün hariç toplam 292,6 → 229,2R, 10 gün hariç 184,3R; fazla 5 gün hariç +128,4R — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- Seçim: keşifte F1–F3 × stop{1,5;2} BUY hücreleri arasında komşuluk-yumuşatılmış fazla en yüksek (+0,150), iki yarı +0,108/+0,240,
  keşif tek-poz n=782 — [secim.json](../../research/nasdaq_derin_20261013/breakout_momentum/results/secim.json), [grid.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/grid.log)
- H-A (a priori ipucu hücresi 30m F1 N20 H20 stop 2): 1–6 ✓ ama fazla +0,018 P %67 ✗ → RED/SHADOW; stopsuz sürüm P %70, icra ✗ — [kasa.log](../../research/nasdaq_derin_20261013/breakout_momentum/results/kasa.log)
- Seçim düzeltmesi ve plasebo: tüm ızgara maks-istatistik p=0,60; 1h p=0,10; H-S hücresi p=0,08 (dairesel kaydırma, 50 tekrar) — bu oturumdaki hesap, [placebo_ndx_kesif.csv](../../research/nasdaq_derin_20261013/breakout_momentum/results/placebo_ndx_kesif.csv)
- Defter: E23 "tek NDX geçmişine 4+ tur bakıldı"; E24 "gün-blok bootstrap yeterli sanılır" — [docs/KAPI_KAYIT_DEFTERI.md](../../docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- Gün-bloklu bootstrap olay kümelenmesini (trendli haftalarda art arda kırılımlar) görmüyor; dairesel kaydırma plasebosu
  gerçek belirsizliği ~3× büyük gösteriyor. Kart P değerleri bu tür sinyallerde iyimser.
- Önerilen sonraki adım (karar kullanıcıda): H-S'yi kural aynen **gölgeye** almak (emir yok, yılda ~77 işlem → 6 ayda ~40);
  ön-kayıtlı ileri doğrulama: ≥100 gölge işlem, fazla > 0. Post-hoc "yalnız ABD seansı" süzgeci yeni ön kayıt ister.
- Canlı bot uyumu riskleri: NDX Cuma yasağı (B2) ve ASIA yasağı (B3) 40 saatlik tutmayla çakışır (hafta sonu taşıma); Asya
  sinyalleri zaten negatif (−0,100) olduğundan B3 uyumlu.

### Gaps
- 1m katı icra (stop kayması dahil) yapılmadı. Bot kısıtlarıyla (Cuma, tek pozisyon/portföy) birlikte portföy katkısı (E19) ölçülmedi.
- Defter (§2) ve Evrim Paneli oturum notu bu araştırmacı tarafından yazılmadı (talimat: yalnız araştırma klasörü);
  önerilen defter satırı rapor ekinde.
