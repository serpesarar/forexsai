# Kısa vadeli (1–5 gün) "dibi al" ortalamaya dönüş kuralları — NASDAQ-100 (CAPREV'in sık akrabaları)

Kapsam: Connors RSI(2), N-gün kapanış dibi, IBS, 3 ardışık düşüş, büyük düşüş günü; günlük kapanışta karar, 1–10 gün tutma,
NDX CFD 1h (2016-06 → 2026-06 keşif), kasa 2026-07-01 → 10-01 (30m), DAX 1h bağımsız piyasa (2019-10 → 2026-10).
Ön kayıt: `/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/PROTOCOL.md` (sonuçlardan önce yazıldı).
Kod/çıktı: aynı klasör (`engine.py`, `grid.py`, `card.py`, `placebo.py`, `extra.py`, `tail_risk.py`, `results/`).
Birim: **σR** = PnL / (σ_d × giriş), σ_d = son 20 günlük günlük getiri std'si. 2025–26 düzeyinde 1 σR ≈ **284 NDX puanı**
(σ_d medyan %1,15 × kapanış medyan 24.752). Tüm sonuçlar spread 1,5 puan + 2×0,2 kayma ve **%6/yıl swap** (takvim gecesi başına) dahil.
Giriş = karar kapanış barından SONRAKİ barın açılışı (16:00 ET CFD barı); iyimser = sinyal kapanışı, maliyetsiz.

Defterle ilişki (3. KURAL): bu aile (çok-günlü tutma, günlük osilatör) defterde hiç sınanmamıştı. CAPREV (GF-16..22) gün-içi ve
tek seans; GF-05 gün-düzeyi koşulları gün-içi saat başı yön için ölçmüştü. Dayandığı ilkeler: §3/2 "korku döner", §3/5 "braket ≠ zaman".

---

## 1. Literatür ve uygulayıcı tekrarları ne diyor? (etki büyüklüğü, 2010 sonrası zayıflama, 200g MA, VIX, çöküş riski, QQQ/NDX)

### Takeaway
Akademik literatür endeks düzeyinde günlük **negatif seri bağımlılığın 2000'lerden beri** var olduğunu ve kısa vadeli dönüş getirisinin
**VIX ile güçlü biçimde arttığını** (likidite sağlama primi) söylüyor; uygulayıcı RSI(2)/IBS tekrarları yüksek isabet ama düşük
yatırımda-kalma nedeniyle düşük toplam getiri raporluyor ve sayıları maliyet/dolum varsayımlarına çok duyarlı. NDX/QQQ'ya özgü güvenilir,
maliyetli ve kayıt-dışı-örneklem bir yayın bulunamadı.

### Cited Findings
- Nagel (2012, RFS 25(7)): kısa vadeli dönüş stratejilerinin getirisi likidite sağlama getirisinin vekili; beklenen getiri **zamanla
  değişiyor ve VIX ile güçlü biçimde tahmin ediliyor**; kriz dönemlerinde (2007–09) beklenen getiri ve koşullu Sharpe "muazzam" artıyor;
  koşulsuz getirisi düşük endüstri-portföyü dönüşleri bile yüksek VIX'te yüksek getiri veriyor — [NBER w17653](https://nber.org/papers/w17653)
- Sonraki bir çalışma (büyük hisse dönüş portföyleri): VIX'te 1 puanlık artış sonraki 5 günde dönüş getirisini **+5,37 bp** artırıyor;
  Nagel'in ana sonucunu teyit ediyor (ön çalışma) — [AEA 2020 ön bildiri](https://aeaweb.org/conference/2020/preliminary/paper/EdTAYHe3) (arama özetinden; tam metin okunmadı)
- Baltussen, van Bekkum & Da (JFE 2019, 132(1)): 15 ülkeden 20 endekste günlük getirinin birinci derece otokorelasyonu 1951'den beri
  ~+0,05 civarındaydı, **2000'lerde işaret değiştirip negatif kaldı**; nedeni endeksleme (vadeli/ETF/endeks fonu) ile ilişkilendiriliyor;
  MAC(5)'e karşı işlem yapan strateji 1999-03 sonrası tüm endekslerde yıllık Sharpe **0,63**, yalnız S&P 500'de **0,67** —
  [JFE makale (yazar sayfası)](https://personal.eur.nl/vanbekkum/2018%20JFE%20BaltussenVanBekkumDa.pdf); [RePEc](https://ideas.repec.org/a/eee/jfinec/v132y2019i1p26-48.html)
  (rakamlar arama özetinden; PDF metni araçla çıkarılamadı)
- Martin (2021): opsiyon fiyatlarından S&P 500 otokorelasyonu subprime öncesi ~0, sonrasında **−%20…−%30** — [J. Financial Econometrics](https://academic.oup.com/jfec/article/19/1/39/6124729) (arama özetinden)
- So & Wang (JFE 2014): kazanç açıklaması dönemlerinde kısa vadeli dönüş **6 kat** artıyor (piyasa yapıcı envanter riski); yeniden üretimde
  etki küçülmüş (1996–2011 3 günlük %1,45 vs sahte dönem %0,22; 2007–2016 Quantopian tekrarında %0,449 vs makalede %1,448). **Hisse
  düzeyi**, endeks düzeyine doğrudan uygulanmaz — [MIT DSpace](https://dspace.mit.edu/handle/1721.1/119665); [Quantpedia](https://quantpedia.com/Screener/Details/307)
- Connors & Alvarez kitabı (2008) 1995–2007 hisse/S&P 500 verisinde "pozitif ortalama getiri" raporluyor; ilkeler: geri çekilmede al,
  200g MA üstünde al, korkuyu al, **stop kullanma**, gece tut, RSI(2). CXO eleştirisi: veri madenciliği düzeltmesi/OOS yok, maliyet yok,
  kuyruk (çöküş) riski incelenmemiş, sinyaller aynı haftalarda kümeleniyor — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/a-few-notes-on-short-term-trading-strategies-that-work/)
- NAS100 CFD günlük, RSI(2)<5 ∧ 200g SMA üstü, çıkış 5g SMA üstü kapanış, 2016-10 → 2026-10: **65 işlem, %75,4 isabet**, ort. kazanç
  +%1,58 / kayıp −%3,11, PF 1,55, toplam +%26,9 (al-tut +%528), YBBO %2,4 vs %20,2, maks DD −%25 — [Backtrex NDX](https://backtrex.com/en/backtests/connors-rsi-2-nasdaq-100)
- Aynı kural S&P 500 CFD 2016–2026: 73 işlem, %71,2 isabet, YBBO +%1,7 vs al-tut %13,5; 2022'de 8 işlem +%0,9 — [Backtrex SPX](https://backtrex.com/en/backtests/connors-rsi-2-sp-500)
- RSI(2)<15 SPY (QuantConnect tekrarı) 2010–2022: 852 işlem, %62 isabet, net +%158, YBBO %7,6 — [QuantConnect forum](https://quantconnect.com/forum/discussion/15754/an-overview-of-a-simple-rsi-based-trading-strategy)
- IBS: Pagonidis (2013) "IBS<0,2 kapanan ETF ertesi gün yükselir, >0,8 düşer"; Pandey & Joshi (2023) ülke ETF'lerinde 10 yılda teyit,
  maliyetlerin (özellikle açığa satış) performansı düşürebileceği uyarısı — [arXiv 2306.12434](https://arxiv.org/abs/2306.12434v1)
- QQQ IBS tekrarı anlaşmazlığı: Quantified Strategies Amibroker'da YBBO %15,1 / DD %28 raporladı; QuantConnect tekrarı YBBO **%5,5** /
  DD %33 (düzeltilmiş fiyat, aracı modeli farkı olabilir) — [QuantConnect forum](https://www.quantconnect.com/forum/discussion/12403/who-039-s-wrong-me-or-amibroker/)
- Ortalamaya dönüş sistemlerinin en büyük düşüşü Ekim 2018 satışında geldi (nitel) — [StockCharts SystemTrader](https://articles.stockcharts.com/article/articles-arthurhill-2018-10-systemtrader---update-to-rsi-mean-reversion-strategy-and-dealing-with-the-dreaded-drawdown/)

### Inferences
- Literatürün iki güçlü ayağı (endeks negatif seri bağımlılığı 2000+ ve VIX-koşullu dönüş primi) bu projenin CAPREV bulgusuyla ve
  "korku döner" ilkesiyle aynı mekanizmayı tarif ediyor: likidite sağlayıcı çekildiğinde aşağı aşırılık geri alınıyor.
- Uygulayıcı sayıları (isabet %62–78) yüksek görünse de hep **kapanışta dolum** varsayıyor ve yatırımda kalma süresi kısa olduğu için
  al-tut'tan çok düşük toplam getiri veriyor; bu yüzden doğru kıyas "al-tut toplamı" değil **aynı tutma süresindeki her-gün-al tabanı**.

### Gaps
- NDX/QQQ için maliyetli, sonraki-bar icralı, 2010 sonrası alt-dönem ayrıştırmalı yayınlanmış bir tekrar bulunamadı.
- Connors & Alvarez kitabının isabet/işlem sayısı tabloları birincil kaynaktan doğrulanamadı (kitap çevrimiçi değil).
- Quantified Strategies RSI(2)/IBS QQQ makaleleri ücretli; rakamlar doğrulanamadı. Nagel'in VIX katsayıları makale metninden alınamadı.
- 2015 öncesi NDX günlük verisi yerel olarak yok (makro dosyası 2015+); indirme izin gerektirdiği için 1985+ uzun geçmiş sınanmadı.

---

## 2. NDX'te ön-kayıtlı ızgara: hangi kurallar aynı tutma süresindeki "her gün al" tabanını yeniyor?

### Takeaway
576 hücrenin **%86,1'i** tabanın üstünde (σR>0 olan %97,9); fazla getiri parametrelerde düzgün (daha aşırı dip → işlem başına daha
büyük, daha seyrek). Ama seçim-yükü plasebosunda aile kanıtı **sınırda**: ortalama fazla getiri p=0,04, pozitif-hücre oranı p=0,07.
En iyi çıkışlar MA5 ve k=1; **stop kenarın ~2/3'ünü yiyor**, k=5 en zayıf.

### Cited Findings
(Hepsi yerel ölçüm; keşif < 2026-07-01, NDX 1h CFD.)
- Taban (her gün al, aynı mekanik/maliyet, stopsuz): h=1 +0,036 σR, h=3 +0,149, h=5 +0,261, h=10 +0,546 — [grid_NDX.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_NDX.log)
- Izgara: fazla>0 %86,1; P(fazla>0)≥%90 %27,1; iki kronolojik yarıda da fazla≥0 %60,2; **n≥150 ∧ P≥%90 ∧ iki yarı ≥0 olan 59 hücre** — [grid_NDX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_NDX.csv)
- Sinyal ailesine göre ortalama fazla / pozitif hücre oranı: RSI15 +0,193/%92 · DN3 +0,186/%90 · DROP2 +0,187/%88 · IBS20 +0,152/%94 ·
  LOW5 +0,147/%94 · RSI5 +0,146/%67 · DROP15 +0,137/%92 · IBS30 +0,127/%100 · RSI10 +0,127/%83 · LOW3 +0,085/%92 · DROP1 +0,078/%73 ·
  LOW10 +0,067/%71 — [grid_NDX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_NDX.csv)
- Çıkışa göre: MA5 +0,202 (%91 pozitif) · k1 +0,156 (%97) · k3 +0,094 (%81) · k5 +0,092 (%76). Stopa göre: **stopsuz +0,240 (%94)** ·
  1,5σ +0,077 (%83) · 2σ +0,091 (%82) — aynı kaynak
- Düzgünlük (F0, stopsuz, MA5): RSI θ 5/10/15 → fazla +0,685 / +0,446 / +0,383 (n 57/108/153); LOW N 3/5/10 → +0,072 / +0,189 / +0,276;
  k1'de IBS 0,2/0,3 → +0,129 / +0,116; DROP %1/%1,5/%2 → +0,105 / +0,113 / +0,125 — aynı kaynak
- **Seçim-yükü plasebosu (E24)**: alt ızgara 12 sinyal × {F0, VIX} × 4 çıkış × stopsuz (96 hücre), sinyal maskesi ≥20 gün dairesel
  kaydırılarak 100 tekrar: gerçek pozitif oran 0,938 vs plasebo ort 0,650 (%95 = 0,939, max 1,0) → **p=0,07**; gerçek ort. fazla +0,226 vs
  plasebo ort +0,060 (%95 +0,189, max +0,327) → **p=0,04** — [placebo_NDX.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/placebo_NDX.log)
- Veri sağlığı: 1h günlük kapanış ↔ makro nakit NDX getiri korelasyonu 0,996; IBS korelasyonu 0,989 (IBS<0,2 uyumu %98; 1h'te 09:00 barı
  30 dk ön-seans içeriyor); RSI(2)<10 uyumu %99,4; 1h ↔ 30m örtüşen 688 günde kapanışlar birebir — [check_data.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/check_data.py)
- Kuyruk riski (stopsuz): en kötü işlemler kriz başlangıçlarında — RSI15·F0·MA5 en kötü −5,3 σR (2020-02-21), maks DD −6,6 σR, toplam
  +85,3; LOW3·MA·MA5 en kötü −8,5 σR (2018-01-30), maks DD −18,3; IBS20·k1 en kötü −5,4 (2025-07-31), maks DD −10,7. 2σ stoplu RSI15 en kötü
  −2,4 ama maks DD −14,5 ve toplam +45,2 — [tail_risk.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/tail_risk.log)

### Inferences
- Kenar gerçek görünüyor ama "çok güçlü" değil: ön-kayıtlı ailenin tamamı plaseboya karşı yalnız p≈0,04–0,07. Bu, defterin E24 dersiyle
  uyumlu — tekil hücrelerin P(EV>0)=%99'ları seçim yükünü temizlemiyor.
- Stopun zararı ve MA5/zaman çıkışının üstünlüğü "braket ≠ zaman" ilkesinin çok-günlü ölçekte de geçerli olduğunu gösteriyor; bedeli
  çöküş başlangıçlarında −5…−8 σR'lik tekil kayıplar (Connors'ın "stop kullanma" önerisinin karşı yüzü).
- Daha aşırı dip → işlem başına daha büyük fazla getiri; sıklık–sağlamlık takası parametre içinde düzgün, kopuk tepe yok (aşırı uyum işareti değil).

### Gaps
- Plasebo yalnız stopsuz ve F0/VIX alt ızgarasında, 100 tekrarla koşuldu (tam 576 hücre için koşulmadı; p'nin çözünürlüğü 0,01).
- Ön-seans karışık 1h H/L'nin IBS'ye etkisi yalnız korelasyonla kontrol edildi (0,989); 2016–2023 için 30m ile tam RTH IBS yok.

---

## 3. Kenar VIX ≥ 18,4 / 200g MA'ya bağlı mı? 2022'de yaşıyor mu?

### Takeaway
**VIX'e bağlı, 200g MA'ya bağlı değil.** Aynı işlemler VIX_{t−1}≥18,4'te ortalama +0,165 σR, altında +0,022 σR fazla getiri veriyor
(F0 hücrelerinin %78,5'inde yüksek-VIX tarafı daha iyi) — Nagel ve CAPREV ile aynı yön. 200g MA filtresi fazla getiriyi artırmıyor
(yalnız yükseliş sürüklenmesini yakalıyor). 2022'de ham getiri çoğu hücrede negatif (%85), ama **2022'nin kendi tabanına göre** hücrelerin
%74'ü pozitif.

### Cited Findings
- F0 hücrelerinde işlem bazlı ayrışım (48 hücre ortalaması): fazla VIX-yüksek +0,165 / VIX-düşük +0,022; MA200 üstü +0,101 / altı +0,088;
  VIX-yüksek > düşük oranı %78,5; MA200 altı > üstü oranı %45,8 — [state_split_NDX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/state_split_NDX.csv), [extra.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/extra.log)
- Örnekler (stopsuz): RSI5·k1 VIX-yüksek +0,617 vs düşük −0,161; LOW5·k5 +0,406 vs −0,293; DN3·k3 +0,468 vs −0,157; istisna IBS20·k1
  +0,132 vs +0,127 (VIX'ten bağımsız) — aynı kaynak
- Filtre düzeyinde (ızgara): ortalama fazla F0 +0,095 · MA +0,101 · VIX +0,155 · MAVIX +0,194; ama VIX/MAVIX hücrelerinin medyan n'i 124/66 —
  [grid_NDX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_NDX.csv)
- 2022: F0 hücrelerinde ham R>0 yalnız %15,3, 2022-kendi-tabanına göre fazla>0 %73,6 (ort +0,115). Tam-dönem tabanına göre 2022 fazla
  toplamı ızgaranın yalnız %6,4'ünde pozitif — aynı kaynaklar
- Aday bazında 2022 (kendi tabanına göre ort. fazla): RSI15·F0·MA5 +0,458 (24 işlem, ham +3,1 σR) · IBS20·k1 +0,108 (55 işlem, ham −0,04) ·
  LOW5·F0·MA5 +0,279 (31 işlem, ham −2,1) · RSI10·MA·MA5 (H1) −0,825 (2 işlem) · LOW3·MA·MA5 (H5) −2,78 (2 işlem) · LOW5·MA·k1 −0,72 (4) —
  [card.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card.log), [card_posthoc.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card_posthoc.log)
- H4 (RSI10 ∧ VIX≥18,4, 2σ stop): 82 işlem, ort +0,180, fazla +0,059 (P %62); 2022'de 21 işlem −9,5 σR — stop + yüksek VIX ayı piyasasında kanar — card.log

### Inferences
- 200g MA filtresinin (Connors) işlevi fazla getiri yaratmak değil, ayı piyasasında **hiç işlem açmamak** (H1/H5 2022'de 2 işlem). Bu
  kuyruk riskini azaltır ama örneklemi yarıya indirip 150 olay çıtasını kaçırtır.
- VIX bağımlılığı Nagel'in likidite-sağlama yorumuyla ve defterin "korku döner" ilkesiyle tutarlı; ama yüksek-VIX + stop birleşimi
  (H4) 2022 gibi süren ayıda en kötü sonucu veriyor — VIX'li sürümde zaman çıkışı stoptan güvenli.
- IBS<0,2'nin VIX'ten bağımsız olması onun farklı (mikroyapı/gece) bir mekanizma olabileceğine işaret ediyor (bkz. §5 DAX ve E2).

### Gaps
- 2022 tek ayı yılı; 2008 ve 2000–02 yerel veride yok (2015+). "Ayı piyasasında da çalışır mı" sorusu tek yılla yanıtlanamaz.
- VIX-yüksek alt kümede n yarıya düşüyor; VIX eşiği yeniden ayarlanmadı (ön kayıt 18,4).

---

## 4. Sıklık–sağlamlık takası CAPREV'e göre; CAPREV günleriyle çakışma ve getiri korelasyonu

### Takeaway
Aileden **yılda 15–38 işlem** çıkıyor (CAPREV ~10–16/yıl) ve işlem başına fazla getiri en iyi 5 gün çıkarılınca büyük ölçüde kalıyor
(CAPREV'de toplamın %64–65'i en iyi 5 günden geliyordu; burada %20–35). CAPREV ile günlük getiri korelasyonu düşük (**0,07–0,33**), ama
aday kurallar CAPREV günlerinin %24–79'unda zaten pozisyonda ve o gün ortalama **zarar** ediyor (stres günü düşmeye devam ediyor).

### Cited Findings
- Sıklık × fazla (stopsuz, keşif, NDX): IBS30·F0·k1 52/yıl +0,116 · IBS20·F0·k1 38/yıl +0,129 · LOW5·F0·k1 36/yıl +0,139 · DROP1·MA·k1
  24/yıl +0,147 · LOW5·F0·MA5 22/yıl +0,189 · RSI15·F0·MA5 16/yıl +0,383 · RSI10·MA·MA5 8/yıl +0,424 · RSI5·VIX·MA5 4/yıl +1,027 —
  [grid_NDX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_NDX.csv)
- En iyi 5 / 10 gün hariç toplam (tam dönem): RSI15·F0·MA5 87,5 → 68,3 / 54,9 σR · IBS20·k1 65,4 → 43,2 / 30,8 · LOW5·F0·MA5 82,7 → 66,2 / 52,5 ·
  LOW3·MA·MA5 65,4 → 49,3 / 37,8 · RSI10·F0·MA5·2σ 25,8 → 9,2 / −5,6 · H4 14,8 → −1,3 / −14,6 — [card.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card.json), [card_posthoc.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card_posthoc.json)
- CAPREV (107 olay günü, 1h, 2016–2026-07) ile ilişki — pozisyonda olunan CAPREV günü / aynı gün sinyal / günlük PnL korelasyonu /
  CAPREV gününde adayın ort. MTM σR:
  RSI10·MA·MA5 22/3/0,065/−0,45 · RSI10·F0·MA5·2σ 50/19/0,238/−0,41 · IBS20·k1 64/11/0,232/−0,08 · RSI10·VIX·MA5·2σ 41/22/0,332/−0,01 ·
  LOW3·MA·MA5 51/3/0,098/−0,41 · RSI15·F0·MA5 60/10/0,224/−0,24 · LOW5·F0·MA5 84/14/0,233/−0,24 · LOW5·MA·k1 26/15/0,070/−0,03 ·
  DROP1·MA·k1 36/7/0,080/−0,00 — aynı kaynaklar
- Tek pozisyon portföyü (aday pozisyondayken CAPREV atlanır): RSI15·F0·MA5 + CAPREV 90,7 σR (aday tek 85,3, CAPREV tek 25,6; 60 CAPREV
  atlandı); IBS20·k1 + CAPREV 69,1 (64 atlandı); LOW5·MA·k1 + CAPREV 55,8 (26 atlandı); DROP1·MA·k1 + CAPREV 53,8 — aynı kaynaklar

### Inferences
- Bu aile CAPREV'in **daha sık ve daha az uç-güne bağımlı** akrabası; ama CAPREV'in kendi günlerinde aynı yönde yüklü olduğu için iki
  strateji aynı stres epizodlarında birlikte kaybeder (aday MTM −0,24…−0,45 σR o gün). Birlikte işletilecekse toplam NDX uzun riski
  sınırlanmalı; "tek pozisyon" kuralı CAPREV işlemlerinin çoğunu atlatıyor.
- k=1 ve LOW5·MA sürümleri CAPREV günlerinde en az çakışan/zarar eden (MTM ≈0) — portföy açısından en tamamlayıcı adaylar.

### Gaps
- CAPREV verisi 1h ile 2026-07-14'te bitiyor; kasa döneminde CAPREV ilişkisi ölçülmedi.
- İkili portföy için ağırlık/lot optimizasyonu yapılmadı (yalnız tek-pozisyon kuralı).

---

## 5. Kasa (2026-07-01 → 10-01, bir kez) ve DAX bağımsız piyasa

### Takeaway
Kasa olay sayısı küçük (1–12) ama ön-kayıtlı adayların **5'inden 4'ü kasada pozitif** (H4 tek işlemde −2,06). DAX'ta **RSI/LOW/DROP +
MA5 aileleri taşınıyor**, **IBS ise taşınmıyor** (DAX'ta açıkça negatif, 17:30 nakit kapanışla da). DAX ızgarası bütün olarak plaseboyu
geçmiyor (p=0,58–0,66) — çünkü IBS hücreleri aileyi aşağı çekiyor. SPX/QQQ günlük (iyimser) kontrolü ABD'de dördünü de pozitif buluyor.

### Cited Findings
- Kasa (30m, giriş 16:00 barı): H1 4 işlem +0,426 ort (fazla +0,158) · H2 5 işlem +0,455 · **H3 IBS20·k1 12 işlem +0,216 (fazla +0,218)** ·
  H4 1 işlem −2,06 · H5 11 işlem +0,178 (fazla −0,004) · SEL RSI15·F0·MA5 5 işlem +0,451 (fazla +0,185); post-hoc LOW5·F0·MA5 7 işlem +0,439,
  LOW5·MA·k1 12 işlem +0,169, DROP1·MA·k1 10 işlem +0,186 — [card.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card.log), [card_posthoc.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card_posthoc.log)
- DAX ızgarası (1h, 2019-10 → 2026-10, kural aynen, taban h1 −0,012 / h5 +0,009): fazla>0 %67,5; NDX ile hücre işaret uyumu %62,7,
  fazla korelasyonu 0,006; NDX'te sağlam 59 hücrenin %55,9'u DAX'ta pozitif, %10,2'si P≥%90 — [grid_DAX.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/grid_DAX.csv)
- DAX sinyal ailesine göre ort. fazla / pozitif oran: LOW5 +0,161/%90 · DROP1 +0,162/%92 · RSI5 +0,144/%90 · DROP15 +0,134/%85 · DN3 +0,098/%83 ·
  LOW3 +0,084/%90 · RSI10 +0,082/%85 · **IBS20 −0,142/%0 · IBS30 −0,086/%21** · RSI15 −0,041/%46 — aynı kaynak
- DAX plasebo (aynı alt ızgara): gerçek pozitif oran 0,521 vs plasebo 0,568 (p=0,58); ort fazla −0,008 vs +0,022 (p=0,66) —
  [placebo_DAX.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/placebo_DAX.log)
- DAX tanım teşhisi (30m, 2021-12+, 17:30 nakit kapanışı, yeniden ayar yok): IBS20·k1 191 işlem fazla **−0,130** (P %7); RSI15·F0·MA5 +0,270 (P %92);
  LOW5·F0·MA5 +0,224 (P %91); LOW3·MA·MA5 +0,139 (P %87); RSI10·MA·MA5 +0,313 (n=39) — [extra.log](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/extra.log)
- Kartlardaki DAX karşılıkları (1h): H1 +0,359 (60 işlem, P %86) · H2 +0,154 · **H3 −0,126 (259, P %5, iki yarı negatif)** · H4 +0,014 ·
  H5 +0,183 (225, P %91,5) · SEL RSI15 +0,122 (111, P %69, ilk yarı −0,08) · LOW5·F0·MA5 +0,255 (186, P %91) · LOW5·MA·k1 +0,164 (199, P %96) ·
  DROP1·MA·k1 +0,172 (112, P %92, ikinci yarı 0,00) — card.log / card_posthoc.log
- ABD günlük kontrol (makro dosyası, kapanışta karar+giriş, maliyetsiz = iyimser, 2015-10 → 2026-07): fazla getiri SPX / QQQ / NDX nakit —
  IBS20·k1 +0,088 / +0,150 / +0,155; RSI10∧MA·MA5 +0,458 / +0,401 / +0,352; RSI15·MA5 +0,244 / +0,359 / +0,467; LOW3∧MA·MA5 +0,130 / +0,095 / +0,137 — extra.log

### Inferences
- IBS kenarı **ABD'ye (ve büyük olasılıkla ABD kapanış/gece akışına) özgü**: SPX/QQQ'da var, DAX'ta iki farklı kapanış tanımında da ters.
  Ayrıca §6'daki E2 sonucu (ertesi açılışta girince kenar küçülüyor) IBS/k1 kenarının bir kısmının gece taşınmasından geldiğini gösteriyor.
  Pagonidis'in ETF bulgusu ve gece-getirisi literatürüyle tutarlı ama "evrensel ortalamaya dönüş" değil.
- "N-gün kapanış dibi + MA5 çıkışı" (LOW5) ve "büyük düşüş günü" (DROP1) iki piyasada da aynı işarette ve büyüklükte — ailenin en
  taşınabilir çekirdeği. Ancak bunlar ızgaradan sonra (DAX'a bakılarak) seçildi → E23/E24 damgalı.
- DAX'ın 1h verisi 2019 öncesi seyrek olduğundan DAX testi 7 yıl; DAX penceresi kasa aylarını da içeriyor (kasa DAX için ayrı açılmadı).

### Gaps
- Kasa n'leri (1–12) istatistik için yetersiz; yalnız işaret kontrolü.
- DAX'ta 2016–2018 1h verisi seyrek (4h benzeri) → kullanılmadı; DAX'ın 2022'si tek ayı yılı.

---

## 6. Hangi varyant ≥150 olayla 6 ölçütlü canlıya alma kartını geçiyor?

### Takeaway
Ön-kayıtlı 5 adaydan **H3 (IBS<0,2, filtresiz, 1 gün tut)** ve **H5 (3-gün dibi ∧ MA200, MA5 çıkışı)** 6/6 geçiyor; H1 (Connors klasik)
işlem başına en güçlüsü ama yalnız 85 olay → hacimden RED (CAPREV'in sorunu). Ama ek ölçütlerle: **H3 DAX'ta ters**, **H5'in kenarı
çoğunlukla sürüklenme** (fazla P %78,6, kasada fazla ≈0). Seçilmiş/post-hoc adaylardan **RSI(2)<15 · MA5** ve **5-gün dibi · MA5** 6/6 +
fazla getiri P≥%95 + DAX aynı işaret + kasa pozitif — en ikna edici iki aday, ama E24/E23 damgalı, önce gölge.

### Cited Findings
(Tam dönem = keşif 1h + kasa 30m; 1. hacim ≥150 · 2. ortσR>0 ∧ gün-blok P≥%90 · 3. iki yarı ≥0 · 4. spread×1,5 >0 · 5. |iyimser−gerçek| < 0,5×ortR ·
6. tek pozisyon (+CAPREV portföyü) >0. "fazla" = always-long tabanına göre.)

| Aday | Ön-kayıt | n (yıl başı) | ortσR | P | yarılar | ×1,5 | iyimser | fazla (P) | fazla+ yıl | 5 gün hariç | Kart | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 RSI10∧MA·MA5 | evet | 85 (8) | +0,596 | %99,9 | +0,43/+0,76 | +0,588 | +0,711 | +0,411 (%97,7) | 9/11 | 35,2/50,6 | **RED (hacim)** | DAX +0,36 |
| H2 RSI10·MA5·2σ | evet | 154 (15) | +0,168 | %86,9 | +0,19/+0,14 | +0,160 | +0,231 | +0,041 (%61) | 7/11 | 9,2/25,8 | SHADOW (P) | E2 −0,01 |
| **H3 IBS<0,2·k1** | evet | 392 (38) | +0,167 | %99,7 | +0,22/+0,11 | +0,160 | +0,210 | +0,132 (%98,3) | 6/11 | 43,2/65,4 | **LIVE 6/6** | **DAX −0,126 (P %5)**; kasa +0,216/12 |
| H4 RSI10∧VIX·MA5·2σ | evet | 82 (8) | +0,180 | %81,7 | +0,19/+0,17 | +0,175 | +0,199 | +0,059 (%62) | 7/10 | −1,3/14,8 | RED | 2022 −9,5 σR |
| H5 LOW3∧MA·MA5 | evet | 296 (29) | +0,221 | %98,9 | +0,18/+0,26 | +0,212 | +0,326 | +0,076 (%78,6) | 5/11 | 49,3/65,4 | LIVE 6/6 | fazla zayıf; kasa fazla −0,004 |
| SEL RSI15·MA5 | seçilmiş | 158 (15) | +0,554 | %100 | +0,40/+0,71 | +0,547 | +0,657 | +0,377 (%99,9) | 8/11 | 68,3/87,5 | LIVE 6/6 | DAX +0,12 (P %69), DAX30m +0,27; kasa +0,45/5 |
| PH LOW5·MA5 | post-hoc | 227 (22) | +0,364 | %100 | +0,26/+0,47 | +0,357 | +0,467 | +0,190 (%95,4) | 7/11 | 66,2/82,7 | LIVE 6/6 | DAX +0,255 (P %91); kasa +0,44/7 |
| PH LOW5∧MA·k1 | post-hoc | 285 (28) | +0,161 | %98,5 | +0,19/+0,14 | +0,152 | +0,211 | +0,126 (%95,6) | 8/11 | 29,7/45,8 | LIVE 6/6 | DAX +0,164 (P %96); **E2 +0,03** |
| PH DROP1∧MA·k1 | post-hoc | 241 (23) | +0,183 | %99,6 | +0,15/+0,21 | +0,177 | +0,221 | +0,149 (%98,2) | 8/11 | 31,0/44,1 | LIVE 6/6 | DAX +0,172 (2. yarı 0); E2 +0,06 |

— [card.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card.json), [card_posthoc.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/results/card_posthoc.json)

- Yan icra/maliyet ölçümleri: ertesi RTH açılışında giriş (E2): H3 +0,110 (fazla +0,074), SEL +0,392, LOW5·MA5 +0,353 (fazla +0,180),
  LOW5∧MA·k1 +0,027 (fazla −0,009), DROP1∧MA·k1 +0,057; swap %3 ile ortσR: H3 +0,176, SEL +0,598, LOW5·MA5 +0,403; %6 swap'ın işlem başı
  maliyeti 0,02 (k1) – 0,08 σR (MA5) — aynı kaynaklar
- Puan karşılığı (2025–26 σ düzeyi, 1 σR ≈ 284 puan): H3 ≈ +47 puan/işlem, SEL ≈ +157, LOW5·MA5 ≈ +103, LOW5∧MA·k1 ≈ +46 (hepsi 1,9 puan
  maliyet + swap sonrası) — [check](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/short_reversal/engine.py)

### Inferences
- **Karar önerisi (kullanıcıya):** hiçbiri doğrudan LIVE'a değil — 2. KURAL kartı bazıları için 6/6 olsa da E24 (seçim yükü, aile
  plasebosu p≈0,04) ve E23 (NDX'e 5+ tur bakıldı) nedeniyle **gölge**. Gölgeye öncelik sırası:
  1. **LOW5 · MA5 çıkışı (filtresiz, stopsuz)** — iki piyasada aynı işaret/büyüklük, fazla P %95, 22/yıl, en iyi 5 gün hariç %80'i kalıyor,
     E2'de de kenar korunuyor (gece taşıma artefaktı değil). Zayıf yanı: CAPREV günlerinin %79'unda pozisyonda (o gün −0,24 σR).
  2. **RSI(2)<15 · MA5** — NDX'te en güçlü (fazla +0,38, 2022'de bile kendi tabanına +0,46), DAX'ta zayıf-pozitif; 15/yıl.
  3. **IBS<0,2 · 1 gün** — sık (38/yıl) ve NDX/SPX/QQQ'da tutarlı ama DAX'ta ters → yalnız ABD endeksine özgü kabul edilmeli; kenarın bir
     kısmı gece taşınmasında (E2'de 1/3 kayıp) → CFD swap/boşluk icrası gölgede ölçülmeli.
- k=1 sürümlerin (LOW5∧MA·k1, DROP1∧MA·k1) kenarı ertesi-açılış girişinde **yok oluyor** → kenar kapanış sonrası + gece; canlıda 16:00–17:00
  ET CFD likiditesine ve gece swap'ına tam bağımlı. Kart 5. ölçütü (iyimser kapanış vs sonraki 1h bar açılışı) bunu yakalamıyor çünkü iki
  giriş de kapanıştan sonra; sonraki-gün açılışı ayrı bir risktir.
- Stopsuz kuralların kuyruk riski gerçek (−5…−8,5 σR tekil işlem, 2018-02, 2020-02, 2025-02); canlıda "felaket stopu" (≥3σ) + pozisyon
  boyutu σ'ya göre ayarlanmalı — stopun kenar maliyeti ızgarada ölçüldü (1,5–2σ stop kenarın ~2/3'ünü yiyor).

### Gaps
- Kartlar yerel CFD barlarıyla; M1 düzeyinde 16:00 ET sonrası gerçek spread/dolum (seans-sonu spread genişlemesi) ölçülmedi — gölgenin işi.
- Swap sabit %6 varsayıldı; broker'ın gerçek NAS100 uzun swap oranı ve Çarşamba/Cuma üçlü gece kuralı doğrulanmadı.
- İleri gölge verisi yok; post-hoc adaylar için kasa ikinci kez açıldı (ön kayıt "bir kez" diyordu → bu bakış kanıt sayılmamalı, yalnız işaret).
- Ön kayıt sapmaları açıkça: (a) DAX 30m 17:30 teşhisi, SPX/QQQ/NDX-nakit günlük kontrolü, 2022 kendi-taban fazlası ve post-hoc kartlar sonradan
  eklendi; (b) DAX 1h 2019 öncesi kullanılmadı (veri seyrek); (c) KAPI_KAYIT_DEFTERI ve Evrim Paneli notu bu ajan tarafından yazılmadı
  (kısıt: kod yalnız bu klasörde) — önerilen defter satırları: SR-01 ızgara (B, aile p≈0,04), SR-02 IBS·k1 (B−, ABD'ye özgü, DAX X),
  SR-03 LOW5·MA5 (B, iki piyasa, gölge adayı), SR-04 RSI15·MA5 (B−, seçilmiş), SR-05 H1/H4 (RED hacim / X), yeni tuzak önerisi E27:
  "kapanış-sonrası CFD girişiyle ölçülen k=1 kenarı ertesi-açılış girişinde yok olabilir; kenarın gece bileşenini ayrıca raporla".
