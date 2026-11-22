# FX-YI — Forex'te yüksek isabetli (%80+) strateji araştırması — ÖN KAYIT (2026-11-20, sonuçlara bakmadan)

Kullanıcı: "Döviz paritelerinde %80 başarı oranına sahip en az 3 strateji bulana kadar her şeyi dene."
Bağlam: botun 17 Kasım'da açtığı 16 FX pozisyonu (VIXREG-FX, H12) tek bir "risk para birimi uzun" bahsi; hepsinin birlikte
zararda olması tasarım gereği (ρ yüksek). Bu çalışma VIXREG-FX'ten bağımsızdır.

## Yeniden açma gerekçesi (Defter §0.1)
§2.53 / §2.82 / FS-03 / UD-05'te sınanan: fiks dönüşü, seans mevsimselliği, korku dönüşü (D1 RSI2), çapraz z20 dönüşü, D1 trend,
taşıma, hafta sonu boşluğu, Tokyo çıkışı, ay dönümü, tick yoğunluğu, aylık/haftalık momentum, fan kırılımı, büyük gün → ertesi gün.
**Hiç sınanmamış:** (F1) gün-içi M15 bant dönüşü — özellikle NY kapanışı sonrası sessiz saatler ("gece scalp"), (F2) gün-içi
günlük-ATR cinsinden aşırı uzamanın aynı gün içinde sönmesi, (F3) Asya aralığının Londra açılışındaki taşmasının geri dönmesi.
Üçü de yapısı gereği yüksek isabet (küçük TP / geniş SL) üretir; asıl soru beklentinin maliyet sonrası > 0 olup olmadığıdır.

## Çıplak WR yasak — "%80 strateji" tanımı (hepsi KÖR dönemde)
Bir hücre ancak şunların HEPSİNİ geçerse "bulundu" sayılır:
1. İsabet (net kârlı işlem oranı) ≥ %80 — KEŞİF'te de ≥ %80.
2. Ortalama net getiri > 0 bp, gün-kümeli bootstrap P(EV>0) ≥ 0,90.
3. Maliyet ×1,5 stresinde ortalama > 0.
4. KÖR'ün iki kronolojik yarısı ≥ 0.
5. Plasebo: aynı çift × aynı saat dağılımında rastgele zaman + rastgele yön, aynı geometri (40 çekiliş) → hücrenin EV'si plasebo
   dağılımının %95'inin üstünde (isabetin geometriden değil girişten geldiğini gösterir).
6. KÖR'de ≥ 150 işlem ve ≥ 100 bağımsız gün.
Ek olarak (sınıf A için): seçilen hücre görülmemiş çiftlerde / bağımsız beslemede (Dukascopy, 2022 öncesi) yön ve işaret korur.

## Veri ve icra
- Pepperstone MT5 M15, 25 çift (USDTRY/EURTRY hariç: swap −35…−52 bp/gece), 2022-11-07 → 2026-11-13 (`../fx_secim_20261113/data/fx`).
- KEŞİF 2022-11-07 → 2024-12-31 · KÖR 2025-01-01 → 2026-11-13. Seçim yalnız KEŞİF'te; KÖR seçimden sonra bir kez.
- Saat: sunucu = New York + 7 (srv 00:00 = 17:00 ET devir). Devir penceresi srv 23:00–00:59 hiçbir ailede giriş yok.
- Giriş: sinyal barı KAPANIŞINDAN sonraki barın AÇILIŞI (E7). Çıkış: TP/SL dokunuşu veya zaman çıkışı (bar kapanışı).
- Aynı barda TP ve SL → SL (muhafazakâr). Çift başına aynı anda tek pozisyon.
- Maliyet bp = max(bar spread, 2026-11 tick spread'i saat bazında; yoksa bar) + Razor komisyonu 7$/lot RT (E125).
- Swap: işlemler gece devrini geçmez (F2/F3 srv 23:00'te kapanır; F1 zaman çıkışı devirden önce kesilir).

## Aileler (dondurulmuş ızgara)
**F1 GECE-BANT** — BB(20, k) kapanışı; kapanış üst bandın üstünde → SAT, alt bandın altında → AL.
- Pencere (sinyal barı açılış saati, srv): A 01–03 (18:00–20:59 ET), B 01–08 (Asya tamamı), C 09–21 (gündüz kontrol).
- k ∈ {2,0; 2,5; 3,0} · TP ∈ {MID = sinyal anındaki SMA20 uzaklığı, 0,5×ATR14, 1,0×ATR14} · SL ∈ {1,5; 2,5; 4,0}×ATR14
- Zaman çıkışı ∈ {8, 24} bar (devir srv 23:00'ü geçmez). 3×3×3×3×2 = 162 hücre.
**F2 GÜN-UZAMA** — gün açılışı srv 00:00; kapanış − açılış ≥ m×ATR20(günlük, yalnız önceki günler) → sönmesine (ters) gir.
- Sinyal saatleri srv 02–20; gün başına çift başına ilk tetik. m ∈ {0,7; 1,0; 1,3} · TP ∈ {0,15; 0,30}×ATR_D · SL ∈ {0,5; 1,0}×ATR_D
- Çıkış en geç srv 23:00. 12 hücre.
**F3 ASYA-TAŞMA** — Asya aralığı R = srv 02:00–08:59 yüksek/düşük. Londra penceresi srv 09:00–12:59'da kapanış R'nin dışına
  ≥ b×(R yüksekliği) taşarsa → içeri doğru gir. b ∈ {0,25; 0,5}; TP ∈ {aralık kenarı, aralık ortası}; SL ∈ {0,5; 1,0}×R;
  zaman çıkışı ∈ {16, 40} bar (en geç srv 23:00). Gün başına çift başına ilk tetik. 16 hücre.

## Seçim (yalnız KEŞİF)
(a) Havuz hücresi (25 çift birlikte, çift seçimi yok): isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 200.
(b) Çift hücresi: isabet ≥ %80 ∧ ort > 0 ∧ t ≥ 2 ∧ n ≥ 60; aile başına t'ye göre en iyi 10 → KÖR (çoklu sınama bedeli bilinçli
    olarak plasebo + KÖR + bağımsız beslemeyle ödenir).
Tüm KÖR sonuçları (geçen ve geçmeyen) raporlanır.

---
## EK-1 (2026-11-20, F1–F3 KEŞİF sonucu görüldükten sonra, G ailesi sonuçlarına bakılmadan)
F1–F3 KEŞİF: hiçbir havuz/çift hücresi seçim koşulunu sağlamadı (F1 gece A k=3 brüt +1 bp ama maliyet 1,7 bp) → **X**, KÖR'e gidilmedi.
Gerekçe: M15'te maliyet/σ oranı yüksek. Günlük ölçekte maliyet hareketin küçük bir kesri; FX-01 H4'te JPY çaprazlarında iki uç da
DEVAM ediyordu (görülen veri 2010→, 6 çift). Bu yüzden seçim 2010 öncesinde yapılır, 2010 sonrası iki kör dönem.

**Veri:** Pepperstone D1 (sunucu günü NY 17:00→17:00), 25 çift, 1993→2026-11-13 (çift başına ilk tarih farklı).
**Dönemler:** KEŞİF 1993–2009 · TEST 2010–2017 · KÖR 2018-01 → 2026-11-13. Seçim yalnız KEŞİF'te.
**İcra:** sinyal d kapanışında belli; giriş d+1 açılışı; TP/SL D1 bar yüksek/düşükle (aynı barda ikisi → SL); zaman çıkışı H gün sonra kapanış.
**Maliyet bp:** 1,5 × max(bar spread, çiftin 2018+ M15 medyan spread'i) + Razor komisyonu; 2010 öncesi ×2. Swap: bugünkü swap
(probe.json, puan/lot/gece; Çarşamba ×3) tutulan her gece için düşülür (E72: bugünkü swap geçmişi temsil etmez — bilgi notu).
**Sinyaller** (her biri iki yönde: DEVAM ve DÖNÜŞ aynası):
- G1 RSI2(d) < 10 / > 90 · G2 |r_d| ≥ 1,5σ20 · G2b ≥ 2σ20 · G3 üç ardışık aynı yönlü kapanış · G4 trend içi geri çekilme
  (C > SMA200 ∧ RSI2 < 10 → AL; C < SMA200 ∧ RSI2 > 90 → SAT; ayna ters) · G6 Donchian20 kapanış kırılımı
- G5 VIX(d) ≥ 18,4 → risk para birimi uzun (VIXREG_PAIRS yönleri, yalnız o 16 çift; ayna = kısa).
**Geometri:** TP ∈ {0,25; 0,5}×ATR20 · SL ∈ {1,0; 2,0}×ATR20 · tutma H ∈ {1, 3, 5} gün → 12.
**Seçim (KEŞİF):** havuz hücresi (çift seçimi yok) isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 200; çift hücresi isabet ≥ %80 ∧ ort > 0 ∧ t ≥ 2 ∧
n ≥ 60 (aile başına t'ye göre ilk 10). **Geçme:** TEST ve KÖR'ün İKİSİNDE de ana ölçütler 1–4 + 6 (n eşiği dönem başına ≥ 100);
plasebo (ölçüt 5) KÖR'de. Tüm sonuçlar raporlanır.

---
## EK-2 (2026-11-20, EK-1 sonucu görüldükten sonra; EK-2 sonuçlarına bakılmadan)
EK-1 sonucu: 7 sinyal × 2 yön × 12 geometri; hiçbir hücrede brüt kenar üç dönemde de > 2 bp değil → **X** (seçim boş; bilgi notu:
2010 öncesi maliyet tarihsel bar spread'i zaten içerdiği için ×2 çarpanı çift sayımdı — brüt bile geçmediğinden hükmü değiştirmez).

**Gerekçe:** fx_haber_20261118 (UD-05) USD majörlerinde ABD olay günü (NFP/CPI/FOMC/JH) büyük hareketinin ertesi gün SÜRDÜĞÜNÜ üç
dönemde gösterdi (dönüş işlemi k1,5 −7,2 / −8,5 / −6,5 bp → devam ≈ +5 bp net). İşaret 2008–2026'da GÖRÜLDÜ; bu yüzden
**hiç bakılmamış dönem 1994–2007** bağımsız sınavdır (yalnız NFP + FOMC; CPI tarihleri o dönem için yok).
- Takvim: 2008→ `xau_best_days_20261015/makro/out/calendar.csv`; FOMC 1994–2007 `kapi_genis_20261118/data/fomc_1994_2007.csv`;
  NFP 1994–2007 BLS kuralıyla (12'sini içeren haftanın Cumartesisi + 20 gün; Temmuz 3/4 → bir gün önce). **Ocak NFP'leri kural
  güvenilmez olduğu için 1994–2007'de dışarıda.** Kural 2008–2026'da gerçek takvimle %90 eşleşiyor (yanlış tarih etkiyi sulandırır, sızdırmaz).
- Evren: 7 USD majörü. Sinyal: olay günü d, |r_d| ≥ k·σ20 (σ20 önceki 20 gün), yön = sign(r_d) (DEVAM). Giriş d+1 D1 açılışı,
  TP/SL D1 yüksek/düşükle (aynı gün ikisi → SL), zaman çıkışı H gün sonra kapanış.
- Izgara: k ∈ {1,0; 1,5; 2,0} × TP ∈ {0,15; 0,25; 0,35}×ATR20 × SL ∈ {1,0; 1,5; 2,0}×ATR20 × H ∈ {1, 2} = 54 hücre, havuz.
- Maliyet: 2008→ 1,5 × max(bar spread, 2022+ M15 medyan) + Razor; 1994–2007 1,5 × tarihsel bar spread + Razor. Swap bugünkü (E72).
- Seçim: KEŞİF 2008–2016 (tüm olaylar), isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 150; en yüksek t'li 3 hücre.
- Geçme: (i) 2017–2026-11 ölçüt 1–4 (P ≥ 0,90), (ii) 1994–2007 bağımsız: isabet ≥ %80 ∧ ort > 0 ∧ P ≥ 0,80, (iii) plasebo:
  aynı çiftlerde HABERSİZ günlerin aynı kuralı (|r| ≥ kσ) ortalamanın altında kalmalı ve rastgele gün (aynı yön dağılımı) 40 çekiliş
  %95 üstü. Hepsi → B (sinyal yönü önceden görüldüğü için A değil).

---
## EK-2 sonucu: X (KEŞİF'te isabet ≥ %80 hücrelerin hepsi net < 0; TP küçülünce devam kenarı maliyetin altına iniyor).

## EK-3 (2026-11-20; F1 KEŞİF çift tablosu GÖRÜLDÜKTEN sonra — seçim sonradan, bu yüzden kör sınav tek şans)
- **N1 GECE-BANT-DÜŞÜK-MALİYET:** F1 hücre 53 = pencere A (srv 01–03), BB(20; 3,0), TP 1,0×ATR14, SL 4,0×ATR14, 24 bar;
  çiftler USDJPY, GBPJPY, EURCHF, CHFJPY (KEŞİF'te gece brütü > maliyet olan 4 çift). Seçim kuralı: 4 çift havuzunda isabet ≥ %80
  hücreler içinde en yüksek ort (KEŞİF: n 374, isabet %84,5, +0,80 bp, t 1,35).
- KÖR (2025-01 → 2026-11) tek koşu, ölçüt 1–6. Plasebo: aynı çift × aynı saat, rastgele bar + rastgele yön, aynı ATR geometrisi, 40 çekiliş.
- Bağımsız besleme (A için): Dukascopy 1m 2012–2021, aynı kural (M15'e toplanmış), maliyet = bugünkü tick spread ×1,5 + Razor.

---
## EK-3 sonucu: X — KÖR n 266, isabet %77,4, net −0,98 bp (brüt 0,00), P 0,10, yarılar −/−; plasebo isabet medyanı %72,5.
KEŞİF'teki gece brütü (+1,8 bp) taşınmadı; çift seçimi sonradan yapılmıştı (E12 tipi).

## EK-4 (2026-11-20, sonuçlara bakılmadan) — NY 10:00 ET opsiyon vadesi sabitlemesi (pinning), yuvarlak seviyeler
Gerekçe: FX vanilla opsiyonların büyük kısmı NY cut 10:00 ET'de vadelenir; büyük kullanım fiyatları yuvarlak seviyelerde kümelenir;
uzun-gamma riskten korunma alım-satımı fiyatı vadeye kadar kullanım fiyatına çeker. Defterde FX'te hiç sınanmadı (endeks yuvarlak
sayı GF-02/YL-01 farklı mekanizma: vade saati yok).
- Çiftler: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, EURJPY. Pip: JPY 0,01, diğer 0,0001.
- Seviye: adım A ∈ {50, 100} pip katları. Sinyal: srv 16:00 (09:00 ET) veya 16:30 (09:30 ET) açılan barın ÖNCEKİ barının kapanışı
  (giriş = o barın açılışı); en yakın seviyeye uzaklık 2 pip < |d| ≤ D, D ∈ {10, 20} pip → seviyeye doğru gir.
- TP = seviye; SL = S pip, S ∈ {15, 30}; zaman çıkışı 10:00 ET (srv 16:45 barının kapanışı). 16 hücre, havuz.
- **Kontroller:** (K1) hayalet seviye = adım + A/2 kaydırma (aynı kural); (K2) aynı kural 03:00 ET ve 13:00 ET (vade yok), 1 saat.
  Mekanizma varsa: gerçek − hayalet > 0 ve gerçek(09–10) − gerçek(03/13) > 0.
- Seçim KEŞİF (2022-11 → 2024): isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 200 ∧ gerçek > hayalet; en iyi 3 t → KÖR, ölçüt 1–6 (plasebo = K1 + K2).

---
## EK-4 sonucu: X — 16 hücrenin hepsi KEŞİF'te net < 0 (isabet %52–70), gerçek seviye ≈ hayalet seviye ≈ vade dışı saat.

## EK-5 (2026-11-20, veri kutudan çekilirken, sonuçlara bakılmadan) — resmî bant/sabit kur mekanizması
Gerekçe: yön tahmini gerektirmeyen tek FX yapısı resmî müdahale taahhüdüdür. HKMA 7,75/7,85'te sınırsız alım-satım taahhüdü verir
(Convertibility Undertaking); Danmarks Nationalbank EURDKK'yı merkez 7,46038 çevresinde tutar. Defterde hiç sınanmadı.
- **HK1 (USDHKD zayıf uç):** H1 kapanış ≥ 7,8450 → SAT; TP ∈ {20, 50} pip (pip 0,0001); SL = 7,8530 (sabit, taahhüdün 30 pip
  ötesi); tutma ∈ {24, 120} H1 bar. **HK2 (güçlü uç ayna):** kapanış ≤ 7,7550 → AL; SL 7,7470. Aynı geometri.
- **DK1 (EURDKK):** |kapanış − 7,46038| ≥ z pip, z ∈ {30, 60} → merkeze doğru; TP = uzaklığın yarısı; SL = 2× uzaklık; tutma {24, 120}.
- Tek pozisyon; giriş sonraki H1 açılışı; aynı barda TP+SL → SL. Maliyet 1,5 × bar spread + Razor; swap bugünkü (her gece, Çar ×3).
- Dönem: verinin kronolojik ilk yarısı KEŞİF, ikinci yarısı KÖR. Geçme: iki yarıda da isabet ≥ %80 ∧ ort > 0 ∧ stres ×1,5 > 0;
  KÖR P ≥ 0,90; ≥ 60 işlem/yarı (bağımsız epizod az olacağı için "epizod" = 5 iş günü içinde ardışık işlemler bir sayılır, raporlanır).

---
## EK-5 sonucu: X — EURDKK spread'i (≈ 6 bp × 1,5) bant içi hareketten büyük, isabet %0–3; USDHKD zayıf uç SAT'ta swap −0,64 bp/gece
ve fiyat uçta haftalarca kalıyor (isabet %9–50); güçlü uç AL (HK2) isabet %46–62, net ≈ 0 → hiçbiri %80'e yaklaşmıyor.

## EK-6 (2026-11-20, Dukascopy indirmesi sürerken, veri görülmeden) — ABD veri anı sıçraması, 1 dakika
Gerekçe: EK-1/2/3 dersi — yüksek isabet geometrisi küçük TP ister; TP küçülünce sabit maliyet kenarı yer. Olay anında hareket
20–50 bp, yani küçük kesirli TP bile maliyetin birkaç katı. Yön: ya ilk tepkinin aşırılığı geri alınır (GERİ) ya sürer (DEVAM, EK-2).
- Veri: Dukascopy 1m BID + ASK (gerçek spread), 5 USD majörü (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD), 2012-01 → 2026-11, ABD olay
  günleri (calendar.csv). Olay anı T: NFP/CPI 08:30 ET, FOMC 14:00 ET (JH hariç).
- Sıçrama S = orta fiyat kapanışı(T+k dk) − orta açılış(T), k ∈ {1, 3}. Koşul |S| ≥ q × ATR20 (Pepperstone D1, önceki gün), q ∈ {0,15; 0,30}.
- Giriş T+k+1. dakika açılışı (AL ask, SAT bid); yol orta fiyatla; maliyet = (giriş spread'i + çıkış dakikası spread'i)/2 + Razor.
- Yön ∈ {DEVAM = sign S, GERİ = −sign S}; TP ∈ {0,25; 0,5}×|S|; SL ∈ {1,0; 2,0}×|S|; zaman ∈ {15, 60} dk. 64 hücre.
- Dönem: KEŞİF 2012–2018 · TEST 2019–2022 · KÖR 2023→. Seçim KEŞİF (isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 150, havuz; en iyi 3 t).
  Geçme TEST ve KÖR'de ölçüt 1–4 + n ≥ 100. Plasebo: aynı kural T − 60 dk'da (haber yok), aynı günler.

## EK-6 sonucu: KEŞİF'te seçilen 2 hücre (51, 35). Hücre 51 (k3, q0,3, DEVAM, TP 0,25|S|, SL 2|S|, 60 dk): KEŞİF n 340 %82,4 +3,12 bp
(t 3,8, P 0,997) → TEST n 180 %81,1 +1,45 (P 0,73 < 0,90) → KÖR n 288 %74,3 −1,23 (P 0,26), ayna da −2,33. Hücre 35 TEST −0,40 / KÖR −2,26.
**X (canlı için); geçmiş için C — haber anı devam kenarı 2012–2022'de vardı, 2023'ten beri yok.**

---
## EK-7 (2026-11-20, Dukascopy tüm günler indirilirken, veri görülmeden) — ABD DIŞI planlı veri anı sıçraması
Gerekçe: EK-6'da ABD haber anı devamı 2012–22 çalıştı, 2023'te söndü (büyük olasılıkla en kalabalık takvim). ABD dışı açıklamalar
(RBA/AU iş gücü 00:30–03:30 UTC, UK/EU 06:00–10:00 UTC, Kanada 12:30/13:30 UTC, ISM 14:00/15:00 UTC…) daha az rekabetli olabilir.
Takvim yok → vekil: planlı açıklamalar dakika :00 / :30'da yapılır.
- Veri: Dukascopy 1m BID+ASK, 5 USD majör, 2015-01 → 2026-11-13, tüm hafta içi günler.
- Aday an T = UTC dakikası :00 veya :30. S = orta kapanış(T+2) − orta açılış(T) (3 dk). Koşul |S| ≥ q·ATR20_D (Pepperstone D1, önceki gün),
  q ∈ {0,15; 0,25}. ABD olay anları (calendar.csv NFP/CPI/FOMC T) ayrı grup "ABD"; geri kalan "DİĞER" (sınanan grup).
- Giriş T+3 açılışı; DEVAM (sign S) ve GERİ (ayna, kontrol); TP ∈ {0,25; 0,5}|S|; SL ∈ {1; 2}|S|; zaman ∈ {15, 60} dk; maliyet
  = (giriş + çıkış spread'i)/2 + Razor. Çift başına aynı anda tek pozisyon. 32 hücre × grup.
- **Plasebo:** aynı kural T = :13 / :43 dakikalarında (plansız sıçrama).
- Dönem: KEŞİF 2015–2019 · TEST 2020–2022 · KÖR 2023→. Seçim KEŞİF/DİĞER: isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 150, en iyi 3 t.
  Geçme TEST ve KÖR: ölçüt 1–4, n ≥ 100, ve KÖR ort > plasebo (:13/:43) ort.

## EK-8 (2026-11-20, sonuçlara bakılmadan) — USDHKD taahhüt ucu, zaman çıkışı YOK
EK-5'te HK1/HK2 zaman çıkışıyla (24/120 saat) elendi; uçta haftalarca bekleme olduğundan TP'ye ulaşmadan kesildi. Taahhüt fiyatın
uca geri dönmesini değil, ucun ötesine geçmemesini garanti eder → zaman sınırı yerine yalnız TP/SL.
- HK3: H1 kapanış ≤ 7,7520 → AL, SL 7,7470, TP ∈ {+20, +50} pip, en çok 1.500 H1 bar (≈ 3 ay). HK4: kapanış ≥ 7,8480 → SAT, SL 7,8530, aynı TP.
- Swap bugünkü (E72: geçmiş faiz farkı farklıydı — bilgi; swapsız brüt de raporlanır). Epizod = 7 günden uzun boşlukla ayrılan işlem kümesi.
- Geçme: iki kronolojik yarıda isabet ≥ %80 ∧ net > 0 ∧ ≥ 10 epizod/yarı (epizod azsa en fazla C).

## EK-8 sonucu: HK3 GEÇTİ (B), HK4 X.
HK3 TP20: yarı 1 (2010–2020) n 47 / 29 epizod %89,4 +1,73 bp; yarı 2 (2020–2026) n 24 / 11 epizod %95,8 +2,82; swapsız %85,9 / +0,60.
TP50 de geçer (%86,4 / %100). Duyarlılık (eşik 7,7510–7,7550 × SL 7,7460–7,7480 × TP 20/30): isabet %85–98, swapsız ort > 0 hepsinde.
**Hayalet seviye plasebosu** (7,77/7,78/7,79/7,80/7,82, aynı geometri): isabet %53–62, net −1,0…−1,6, SL oranı %34–43 vs gerçek %93 / +2,19 /
SL %1,4 → kazanç taahhüt mekanizmasından. Zararların 4/6'sı devir saatinde (srv 23–01) geniş spread'le giriş. HK4: TP oranı %100 ama
bugünkü swap (−0,64 bp/gece) ile isabet %20–52 → X.
**EK-7 değişikliği (indirme hızı yüzünden, sonuç görülmeden):** çiftler AUDUSD, GBPUSD, EURUSD, USDCAD; dönem 2018-01 → 2026-11;
BID tüm günler, ASK yalnız Çarşamba → spread = çift × UTC saati × yıl medyanı (Çarşamba ASK−BID), olay dakikası için o saatin medyanı ×3
(haber anı genişlemesi; muhafazakâr). KEŞİF 2018–2020 · TEST 2021–2022 · KÖR 2023→.
**EK-8 icra notu:** kutu salt-okuma (`swap_probe.py`): USDHKD ve USDAED `trade_mode = 0` (DISABLED) — veri görünür ama emir verilemez.
HK3 araştırma bulgusu olarak B; bu hesapta canlı/gölge icra mümkün değil (başka broker gerekir). USDAED swap taşıma fikri de aynı nedenle düşer.

## EK-7 sonucu: X — KEŞİF 2018–20'de 32 hücrenin hepsi net < 0 (brüt +0,1…+0,9 bp, maliyet 2,4 bp; isabet ≤ %73); seçim boş.
ABD dışı planlı açıklamalarda (:00/:30 vekili) sıçrama ne sürüyor ne dönüyor.

---
## EK-9 (2026-11-20, EURDKK günlük verisinin yalnız tarih aralığı görüldükten sonra, sapma dağılımı görülmeden) — DKK taahhüt bandında büyük sapma
Gerekçe: HK3 (B) mekanizması taahhüt; USDHKD bu hesapta işleme kapalı (trade_mode 0). İşleme açık tek taahhütlü kur EURDKK (ERM-II, merkez
7,46038; Danmarks Nationalbank pratikte ±%0,5 tutar). EK-5'te küçük sapma (≥ 4 bp) + yarı yol TP spread'e yenildi; burada sapma büyük, TP merkeze yakın.
- Sinyal: D1 kapanış sapması s = (C / 7,46038 − 1)·1e4 bp; |s| ≥ z, z ∈ {15, 25} → merkeze doğru gir (sonraki gün açılışı).
- TP: sapma 5 bp'ye inince (merkezin 5 bp yakını). SL: sapma |s| + {20, 40} bp (dışarı). Süre sınırı yok (en çok 250 gün). Aynı barda TP+SL → SL.
- Maliyet: 1,5 × max(bar spread, bugünkü 5,8 bp) + Razor 0,6; swap bugünkü (uzun −0,13, kısa −0,30 bp/gece, Çar ×3).
- Geçme: verinin iki kronolojik yarısında isabet ≥ %80 ∧ net > 0 ∧ ≥ 8 epizod/yarı; hayalet kontrol: aynı kural EURSEK/EURNOK
  (taahhütsüz) uzun dönem medyanına göre (bilgi). Epizod = 20 iş gününden uzun boşlukla ayrılan küme.

## EK-9 sonucu: X — EURDKK (ECB fiksi 1999–2026): z15/z25 × SL iki yarıda isabet %0–14, net −33…−44 bp; merkeze dönüş medyan ≈ 350 gün,
TP oranı %14–53, 250 gün sınırında swap + maliyetle kapanıyor. DN merkezden 15–25 bp sapmaya yıllarca izin veriyor (HKD'nin sert bandından farklı).
Hayalet EURSEK/EURNOK (taahhütsüz) de eksi/kuyruklu (−1.646 bp'ye kadar). Bilgi: icra kontrolü (trade_probe.py) — 98 FX sembolünden yalnız
USDHKD ve USDAED işleme kapalı; ikisi de sabit kur.

---
## EK-10 (2026-11-20, sonuçlara bakılmadan) — USDCNH ↔ kıyı içi CNY farkının kapanması
Gerekçe: CNH (kıyı dışı, işleme açık) ile CNY (kıyı içi, PBOC fiksi ±%2 bandı, sermaye kontrolü) arbitrajla bağlı; fark açılınca
PBOC CNH likiditesini sıkarak/gevşeterek kapatır. Defterde hiç sınanmadı. Tek bacak (CNH) işlem görür → fark CNY'nin hareketiyle de
kapanabilir (bu risk sınanır, gizlenmez).
- Veri: ECB günlük EURUSD + EURCNY (14:15 CET) → USDCNY_ecb = CNY/USD; Pepperstone USDCNH H1, ECB anını içeren UTC saatinin (kışın 13,
  yazın 12) kapanışı. d = (CNH / CNY_ecb − 1)·1e4 bp.
- Sinyal: d ≥ z → SAT USDCNH (CNH görece zayıf), d ≤ −z → AL. z ∈ {30, 60, 100}. Giriş sinyal barından sonraki H1 açılışı.
- Çıkış: sonraki ECB günlerinde |d| ≤ z/3 olduğu günün aynı saat kapanışı veya en çok H ∈ {5, 20} iş günü. Fiyat stopu yok (bilgi: en kötü işlem).
- Maliyet 1,5 × max(bar spread, bugünkü 4,0 bp) + Razor 0,7; swap bugünkü (uzun +0,21, kısa −1,33 bp/gece; Çar ×3).
- Geçme: iki kronolojik yarıda isabet ≥ %80 ∧ net > 0 ∧ ≥ 15 epizod/yarı; ayrıca aynı günlerde rastgele yön tabanından iyi.

## EK-10 sonucu: X — USDCNH↔CNY farkı (2015-11 → 2026-11, 2.814 ECB günü; fark p5/p50/p95 −21/+5/+40 bp): z30/60/100 × H5/20, iki yarıda
isabet %44–75, net −22…+21 (yalnız z100-H5 yarı 1 +21, n 6), en kötü −135…−547 bp. Fark tek bacakla (CNH) yakalanmıyor.

---
## EK-11 (2026-11-21, kullanıcı: "bulduklarından yola çıkarak daha derin araştır"; sonuçlara bakılmadan) — zorunlu akış takvimi × yüksek isabet geometrisi
Gerekçe (YI-01…12 dersi): %80 isabet küçük TP / geniş SL geometrisinden gelir; bunun kâra dönmesi için **brüt kenarın maliyetin birkaç
katı** olması gerekir. FX'te brüt kenarı maliyetin üstünde kalan tek aile takvime kilitli zorunlu akıştır (§2.53): H8c gotobi (+3,3 brüt /
1,4 maliyet), H9 ay sonu fiksi, H3b FOMC duyuru öncesi USD zayıflığı. Bunların yönü 2010→ verisinde **görüldü** → bu tur yalnız
**geometri** seçimini kör yapar; geçse bile en çok **B** (yön önceden görülmüş).
- Veri: Pepperstone H1 2010-10 → 2026-11-13. Giriş penceresi açılış barının AÇILIŞI; TP/SL H1 yüksek/düşükle (aynı barda ikisi → SL);
  zaman çıkışı pencere sonu (son barın kapanışı). Maliyet = max(bar spread, 2026-11 tick spread'i sunucu saatine göre) + Razor; stres ×1,5.
  Pencereler devri (17:00 ET) geçmez → swap yok.
- **A GOTOBI** (H8c): gotobi günü (hyp.gotobi_days), push = 23:00→01:00 UTC getirisi > 0 → 01:00 UTC SAT, pencere 5 saat (→06:00).
  Çiftler USDJPY, EURJPY, GBPJPY, AUDJPY (hepsi, seçim yok).
- **B AY SONU** (H9): ayın son iş günü, r_pre = 10:00→16:00 Londra; |r_pre| > 0 → 16:00 Londra'da −sign(r_pre), pencere 4 saat (→20:00).
  Çiftler EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD.
- **C FOMC** (H3b): FOMC günü d, önceki iş günü 18:00 ET → d 14:00 ET USD kısa (USD_BASKET yönleri), 6 çift.
- Doz varyantı (A, B): itme/r_pre mutlak değeri aynı çift × aynı pencerenin önceki 250 iş günü dağılımının 67. yüzdeliğinin üstünde (yalnız geçmiş).
- Geometri birimi U = ATR14(H1, giriş öncesi bar) × √(pencere saati). TP ∈ {0,25; 0,5; 1,0}·U · SL ∈ {1; 2; 4; ∞}·U → 12; × doz {yok, D67}
  (A, B) → A 24, B 24, C 12 = 60 hücre.
- Dönem: KEŞİF 2010-10 → 2017 · TEST 2018–2021 · KÖR 2022 → 2026-11. Seçim yalnız KEŞİF: aile başına isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 150
  hücreler içinde en yüksek t (aile başına 1 hücre).
- Geçme (TEST ve KÖR'de ayrı ayrı): ölçüt 1–4 (P olay-günü kümeli ≥ 0,90; KÖR yarıları ≥ 0) + n ≥ 100 işlem; **plasebo** = aynı kural aynı
  çiftlerde OLAY OLMAYAN günlerde (A: gotobi olmayan iş günü, B: ay sonu olmayan iş günü, C: FOMC ile aynı haftagünü olan FOMC dışı gün) →
  olay ort − kontrol ort > 0 ve P_fark ≥ 0,90 (KÖR). C'de KÖR bağımsız gün ≈ 38 → ölçüt 6 yapısal olarak tutmaz, en çok C.
- **D TAKVİM SEPETİ:** seçilen A/B/C hücreleri tek strateji (her olay kendi kuralıyla); KÖR'de aynı ölçütler, bağımsız gün = birleşim.

## EK-11 sonucu: X — KEŞİF'te %80 koşulunu yalnız B (ay sonu fiksi) D67 TP 0,25U geçti (n 192, %80,7, +3,22 bp, P 0,994, kontrol günleri −1,29).
TEST 2018–21 n 115 %69,6 −0,89 (P 0,30, kontrol farkı +0,17 P 0,42); KÖR 2022–26 n 134 %72,4 +0,11 (P 0,55, yarılar +2,3/−2,1; 2024 −6,8,
2025 −0,8, 2026 −0,5). A gotobi en iyi isabet %67,7 (TP 0,25U'da brüt 0,6–1,3 < maliyet 2,5–3,2), C FOMC en iyi %73,3 net < 0.
Ay sonu fiksi dönüşü 2011–2017'de vardı (yılların 6/7'si +), 2018'den beri yok — H9 kartının "son yıllar zayıf" uyarısıyla aynı.

---
## EK-12 (2026-11-21, EK-11 sonucundan sonra, model eğitilmeden) — meta-etiketleme: bant dönüşü işlemlerinden %80'lik alt küme seçilebilir mi?
Gerekçe: F1'in tek tek kuralları brüt ≈ 0 verdi; soru, karar anındaki bağlamın (saat, oynaklık rejimi, gün içi konum, eğim, VIX, maliyet/TP
oranı) kazananları önceden ayırıp ayırmadığı. Defter §3: tek göstergeli filtreler X; çok değişkenli öğrenici bu çalışmada denenmedi.
- Taban olaylar: F1 BB(20; 2,0) kapanış dışı → içeri, TP 0,5×ATR14, SL 2,5×ATR14, 24 bar; pencere B (srv 01–08) ∪ C (09–21); 25 çift
  (trades_F1 hücreleri ('B',2.0,0.5,2.5,24) ve ('C',2.0,0.5,2.5,24)). Etiket: net > 0.
- Özellikler (yalnız sinyal barı ve öncesi): saat, haftagünü, çift (kategorik), z = (C−SMA20)/SD20, ATR14/fiyat bp, ATR14/ATR14'ün 96 bar ort.,
  (C − gün açılışı)/ATR_D, önceki gün aralığı/ATR_D, SMA20 eğimi (20 bar)/ATR, son bar gövdesi/ATR, maliyet/TP, önceki gün VIX, yön.
- Model LightGBM (sabit: 200 ağaç, lr 0,03, 15 yaprak, min_child 100, subsample 0,8). KEŞİF 2022-11 → 2024-12, KÖR 2025-01 →.
- Eşik seçimi yalnız KEŞİF içi genişleyen 4 kat (çeyrek blokları, 5 gün arınma); kat 2–4 OOS tahminlerinde olasılık eşiği ∈ {üst %5, 10, 20, 30}:
  isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 200, en yüksek t. Yoksa X. Seçilen eşik (olasılık değeri) tüm KEŞİF'te eğitilen modele KÖR'de bir kez uygulanır.
- Geçme: KÖR ölçüt 1–4, n ≥ 150, ≥ 100 gün; plasebo = KÖR taban olaylarından aynı sayıda rastgele alt küme (400 çekiliş), model alt kümesinin
  ort'u %95 üstü. Bağımsız besleme yok → en çok B.

## EK-12 sonucu: X — KEŞİF içi CV'de model isabeti %84'e çıkarıyor (üst %5–30: %83,7–84,4, n 3.869–23.212) ama brüt +0,07…+0,13 bp,
net −1,1 bp; seçilen dilim yok, KÖR'e gidilmedi. Öğrenici isabeti **TP'ye ulaşma olasılığı yüksek bağlamı** (düşük maliyet/TP, oynaklık) seçerek
yükseltiyor, yönü değil: %80 isabet maliyetin altında kalan brütle geliyor (YI genel dersinin çok değişkenli teyidi).

---
## EK-13 (2026-11-21, EK-12'den sonra, sonuçlara bakılmadan) — VIXREG-FX yönü × gün içi geri çekilme girişi × yüksek isabet geometrisi
Gerekçe: FX'te 6/6 kartlı tek yön kaynağı H12 (VIX ≥ 18,4 → risk para birimi uzun, +3,75 bp/gün). EK-1 G5 bunu gün açılışında girip
TP 0,25 ATR_D / SL 2 ATR_D / 5 gün ile sınadı: TEST/KÖR isabet %86 ama net −4,4 / −0,7 (maliyet 1,5×). Burada giriş, rejim yönündeki
gün içi geri çekilmeye bağlanır (dönüş zamanlaması + rejim sürüklenmesi toplanır mı?). Yön 2010→ görüldü → en çok B.
- Veri Pepperstone H1 2010-10 →. Çiftler ve yönler `yeni deneme/fx_fiks_shadow.py` VIXREG_PAIRS (16). Rejim: barın ET tarihinden önceki
  son VIX kapanışı ≥ 18,4.
- Sinyal: rejimde, risk yönü uzun için H1 kapanış < BB(20, k) alt bandı (risk yönü kısa çiftlerde kapanış > üst bant) → risk yönünde gir
  (sonraki bar açılışı). k ∈ {1,5; 2,0}. TP ∈ {0,5; 1,0}×ATR14(H1) · SL ∈ {3; 6}×ATR14(H1) · zaman ∈ {24, 72} bar → 16 hücre.
- Maliyet max(bar, tick spread) + Razor; stres ×1,5; swap bugünkü (Çarşamba devri ×3), E72 notu. Çift başına tek pozisyon.
- Kontroller: (K1) aynı geri çekilme kuralı rejim DIŞINDA (VIX < 18,4) aynı yönde; (K2) rejimde ayna (yükselişte risk kısa).
- KEŞİF 2010-10 → 2017 · TEST 2018–21 · KÖR 2022 →. Seçim KEŞİF: isabet ≥ %80 ∧ ort > 0 ∧ n ≥ 150, en yüksek t (1 hücre).
- Geçme TEST ve KÖR: ölçüt 1–4 + n ≥ 100 + ≥ 60 gün; KÖR'de K1 ve K2 ortalamasından büyük (P_fark ≥ 0,90).

## EK-13 sonucu: X — 16 hücrenin hepsi KEŞİF'te net < 0 (isabet %73–87, brüt −0,7…+0,9 bp, maliyet 4,2–4,4 bp: EM ve çaprazların 2010–17
bar spread'i). Rejim içinde geri çekilmeden girmek ≈ rejim dışında aynı kural (K1 brüt +0,1…+0,5) ≈ rejime karşı ayna (K2 brüt +0,4…+0,9):
rejimin günlük sürüklenmesi saat ölçeğindeki geri çekilme girişine ek bilgi katmıyor. (İlk koşuda swap fiyatla bölünmemişti, düzeltildi.)

---
## EK-14 (2026-11-21, kullanıcı yeni hedef: "oranı %70'e düşür, araştırmayı yenile, daha fazla ara, ayda en az 3 kez görülen strateji"; sonuçlara bakılmadan)
**Yeni "bulundu" tanımı (S70)** — değerlendirilen her sonraki dönemde (TEST varsa TEST ve KÖR, ayrı ayrı):
1. isabet (net > 0 işlem oranı) ≥ %70 (KEŞİF'te de ≥ %70); 2. ort net > 0 ∧ gün-kümeli P ≥ 0,90; 3. maliyet ×1,5 > 0 (G ve EK-2 tablolarında
temel maliyet zaten 1,5× spread → temel > 0 yeter); 4. dönemin iki kronolojik yarısı ≥ 0; 5. **sıklık: ayda ort. ≥ 3 sinyal günü** (çift
hücresinde o çiftin kendi günleri); 6. dönemde n ≥ 60; 7. kontrol: tablonun kendi kontrolü varsa (G ayna, SPIKE ayna/plasebo, EK-11 olay-dışı gün,
EK-13 K1/K2) ana > kontrol; F ailelerinde KÖR'ü geçen hücreye rastgele zaman + rastgele yön plasebosu (aynı çift × saat, aynı geometri, 200 çekiliş) %95 üstü.
**Yeniden tarama (EK-14a):** var olan 9 işlem tablosu (F1, F2, F3, G, EK2, SPIKE, SPIKE7, EK11, EK13; yalnız ana grup). Birim: havuz hücresi
ve çift hücresi. Seçim yalnız KEŞİF: isabet ≥ %70 ∧ ort > 0 ∧ t ≥ 2 ∧ n ≥ 100 ∧ sıklık ≥ 3/ay; tablo başına t'ye göre ilk 5 → değerlendirme.
**Görülmüş hücre uyarısı:** EK-3 hücre 53 KÖR'ü, EK-6 hücre 51/35 TEST/KÖR'ü, EK-11 B|D1|tp0,25 TEST/KÖR'ü, G5 tüm geometrilerin dönem tablosu
daha önce görüldü → bunlar seçilirse en çok C. Diğer geçenler B (bağımsız besleme yok), bağımsız beslemede (Dukascopy) tutarsa A.

## EK-14a sonucu: X — 9 tablo ≈ 10.700 hücrede KEŞİF'te S70 seçimini 4 çift hücresi geçti (F2 EURCHF/EURAUD, G1/G3 USDMXN DEVAM); dördü de
sonraki dönemde düştü (isabet %54,7–77,4, net −2,6…+0,2, P ≤ 0,54).

---
## EK-15 (2026-11-21, EK-14a'dan sonra; yalnız sinyal SIKLIĞI görüldü, getiri görülmeden) — NDX korku gecesi → risk para birimi gecesi
Gerekçe: endekste B dereceli korku gecesi (K1/V1: kapanış gün ortasının altında, kırmızı gün → ertesi gün toparlanma, 33 yıl) DAX/CAC/BTC'ye
taşındı (§2.80–2.82), FX'e hiç taşınmadı. Mekanizma risk iştahı ise risk para birimleri (AUD/NZD/CAD/MXN/ZAR/NOK/SEK) de aynı gece toparlanmalı.
- Sinyal günü d (QQQ günlük, 1999→): **V1** C ≤ (Y+D)/2 × 0,995 ∧ C < A (ayda ort. 2,8 — KEŞİF'te 2,1, sıklık ölçütü riskli);
  **V0** (C − D)/(Y − D) ≤ 0,25 ∧ C < A (ayda 4,4). Varyant: ∧ önceki gün VIX ≥ 18,4.
- İşlem: d günü 16:00 ET açılan H1 barında VIXREG_PAIRS'in 16 çiftinde risk yönüne gir; çıkış X0 = ertesi iş günü 09:00 ET (17 saat) veya
  X1 = 16:00 ET (24 saat). U = ATR14(H1) × √saat; TP ∈ {0,5; 1,0}·U · SL ∈ {1,5; 3; ∞}·U. 2 tanım × 2 VIX × 2 TP × 3 SL × 2 çıkış = 48 hücre (havuz).
- Maliyet max(bar, tick) + Razor, swap bugünkü (1 gece, Çarşamba ×3), stres ×1,5. Kontrol: aynı kural sinyal OLMAYAN günlerde (16:00 ET giriş).
- KEŞİF 2010-10 → 2017 · TEST 2018–21 · KÖR 2022 →. Seçim KEŞİF: isabet ≥ %70 ∧ ort > 0 ∧ t ≥ 2 ∧ sıklık ≥ 3/ay, en yüksek t'li 2 hücre.
- Geçme: TEST ve KÖR'de S70 1–6 + ana − kontrol > 0, P_fark ≥ 0,90. Yön önceden görülmedi (FX'te) → geçerse B; Dukascopy ile A adayı.

## EK-15 sonucu: X — 48 hücrenin hepsi KEŞİF'te net < 0 (isabet %45–55, kontrol günleri %46–53; brüt −7,4…+1,8 bp, 16:00 ET girişinde maliyet
4,9–6,3 bp). NDX korku gecesi risk para birimlerinde ertesi güne toparlanma üretmiyor; VIX ≥ 18,4 ile birlikte daha kötü.

---
## EK-16 (2026-11-21, EK-15'ten sonra, sonuçlara bakılmadan) — gün içi para birimi gücü (kesitsel) dönüş / devam
Gerekçe: defterde FX kesitsel güç yalnız günlük z20 çapraz dönüşüyle (H5, X) sınandı; saat ölçeğinde 8 para birimi sıralaması hiç sınanmadı.
- Güç: 7 USD majörü (EUR, GBP, AUD, NZD, CAD, CHF, JPY karşı USD; USD = 0) H1 kapanışlarından L ∈ {4, 24} saatlik log getiri. Karar saatleri
  00, 04, 08, 12, 16, 20 UTC. Uç fark D = güç_maks − güç_min; z = D / (önceki 250 karar anının D std'si). z ≥ k, k ∈ {1,5; 2,0}.
- İşlem: en güçlü/en zayıf para biriminden oluşan çift 25 çift listesinde varsa (yoksa atla): **DÖNÜŞ** güçlüyü sat/zayıfı al, **DEVAM** tersi.
  Giriş karar saatinde açılan H1 barı; U = ATR14 × √H, H ∈ {4, 8} saat; TP 0,5·U; SL ∈ {1; 2}·U. 2 L × 2 k × 2 yön × 2 H × 2 SL = 32 hücre (havuz).
- Maliyet max(bar, tick) + Razor, stres ×1,5; devir (srv 23:00–00:59) girişleri atlanır, tutuş devri geçmez → swap yok.
- KEŞİF 2010-10 → 2017 · TEST 2018–21 · KÖR 2022 →; seçim KEŞİF: S70 (isabet ≥ %70 ∧ ort > 0 ∧ t ≥ 2 ∧ sıklık ≥ 3/ay), en yüksek t'li 2 hücre;
  geçme TEST ve KÖR S70 1–6; kontrol = aynı hücrenin karşı yönü (DÖNÜŞ↔DEVAM).

## EK-16 sonucu: X — **ilk koşu ileriye bakıyordu** (güç t0 barının kapanışıyla hesaplanıp aynı barın AÇILIŞINDA girilmişti → DEVAM L4 %75–77
isabet, +7,5…+11 bp, t 15). Giriş sonraki bar açılışına alınınca 32 hücrenin hepsi net < 0: isabet %51–56, brüt −1,2…+0,8, maliyet 3,4–4,5 bp.
Saat ölçeğinde kesitsel güç ne dönüyor ne sürüyor. (E7'nin FX kesitsel sürümü — yeni kanıt hatası değil, var olan kural.)

---
## EK-17 (2026-11-21, kullanıcı: "daha derin, daha fazla strateji"; sonuçlara bakılmadan) — saat × önceki hareket kural madencisi, üç aşamalı süzgeç
Gerekçe: tek tek mekanizma turları tükendi; geniş ama dürüst bir arama — her kural basit (saat + önceki hareket + yön), çoklu sınama bedeli
üç bağımsız dönemle ödenir. Kapsar: Londra kırılımı devamı (F3'ün aynası), NY'nin Londra hareketini sürdürmesi/söndürmesi (F2'nin aynası),
saat başı aşırı hareket dönüşü.
- Veri Pepperstone H1 2010-10 →, 25 çift. Karar barı saati h (UTC, 0–23; srv 23 ve 00 hariç), önceki hareket r_L = C_t / C_{t−L} − 1, L ∈ {1, 4, 8} saat,
  z = r_L / (ATR14 · √L). |z| ≥ q, q ∈ {1,0; 2,0}. Yön: DEVAM sign(z) / DÖNÜŞ −sign(z). Giriş sonraki bar açılışı (E7).
- Geometri sabit: U = ATR14 · √H, H ∈ {2, 4, 8} saat; TP 0,5·U, SL 1,5·U, zaman çıkışı H; devri (srv 23:00) geçmez.
- 22 saat × 3 L × 2 q × 2 yön × 3 H × 25 çift = 19.800 çift-kural. Maliyet max(bar, tick) + Razor, stres ×1,5.
- **Aşama 1 KEŞİF 2010-10 → 2017:** isabet ≥ %70 ∧ ort > 0 ∧ **t ≥ 3** ∧ n ≥ 100 ∧ sıklık ≥ 3/ay.
- **Aşama 2 TEST 2018–21:** S70 1–6 (P ≥ 0,90, stres > 0, yarılar ≥ 0, sıklık ≥ 3/ay, n ≥ 60). Aşama 3 KÖR 2022 →: aynı.
- Şans beklentisi raporlanır: Aşama 1'de t ≥ 3 için ~%0,13 × 19.800 ≈ 27 yanlış aday; TEST'i şansla geçme olasılığı ≈ %10 → KÖR'e ~3 yanlış,
  KÖR'ü şansla geçme ≈ %10 → beklenen yanlış son aday ≈ 0,3. Üç aşamayı geçen kural B (bağımsız beslemede Dukascopy 1m 2018→ tutarsa A adayı).
  Ayrıca aynı süzgeç **yön rastgele** (her işlem için yazı-tura) ve **saat kaydırmalı** (h+12) plasebo madencide koşulur; plasebo son aday sayısı raporlanır.

## EK-17 sonucu (ana): 12.006 çift-kural (n < 50 olanlar düştü) — Aşama 1 = 0. Yapısal neden: tek saatlik kural ayda 0,1–1 kez tetikleniyor
(sıklık ölçütü ≥ 3/ay hiçbirinde tutmadı; t ≥ 3 olan 9 kuralın hepsi ayda < 1); ayrıca TP 0,5U / SL 1,5U geometrisinde taban isabet medyanı
%54,6 (zaman çıkışı baskın) → %70 yapısal olarak nadir. Bilgi: t ≥ 3 olan 9 kuralın TEST'te 7'si eksi.
**EK-17b değişikliği (kural getirileri değil, yalnız taban isabet ve sıklık görüldükten sonra):** saat yerine seans bloğu — Asya 00–06,
Londra 07–11, NY 12–16, geç 17–21 UTC (srv 23/00 hariç); TP 0,25·U, SL 1,5·U; diğer her şey (L, q, yön, H, aşamalar, eşikler) aynı.
4 × 3 × 2 × 2 × 3 × 25 = 3.600 çift-kural + aynı süzgeçle yön-rastgele plasebo madenci.

## EK-17b sonucu: X — 2.974 seans-kuralında Aşama 1 = 0 (t ≥ 3 olan 2 kuralın sıklığı ayda < 0,5). **Plasebo madenci (yön yazı-tura) aynı
sayılarda "iyi" kural üretiyor:** ort > 0 208 vs 184, isabet ≥ %70 ∧ ort > 0 176 vs 149, t ≥ 3 2 vs 4; taban isabet medyanı ikisinde de %69,3.
Saat/seans × önceki hareket uzayında şans dışı yön bilgisi yok.

---
## EK-18 (2026-11-21, veri indirildi, yalnız sütun adları görüldü; sonuçlara bakılmadan) — CFTC COT pozisyonu (fiyat dışı yeni veri)
Gerekçe: EK-17 fiyat/saat uzayında yön bilgisi bulamadı; yeniden açma yeni veriyle olur (Defter §0.1). CFTC TFF (Traders in Financial Futures,
yalnız vadeli) haftalık raporu, defterde FX için hiç sınanmadı. Kaynak `cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip`, 2010–2026.
- Para birimleri (kod): EUR 099741, GBP 096742, JPY 097741, AUD 232741, CAD 090741, CHF 092741, NZD 112741, MXN 095741 → çiftler EURUSD, GBPUSD,
  USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, USDMXN (para birimi uzun = çiftte +1/−1).
- Rapor Salı pozisyonu, yayın Cuma 15:30 ET → sinyal barı o Cuma'nın D1 barı, giriş sonraki D1 açılışı (Pazartesi). Kapanma dönemi gecikmeleri
  sızıntı yaratmasın diye rapor tarihi 2013-10-01→11-01, 2018-12-18→2019-03-08, 2025-09-30→2026-01-31 olan haftalar atlanır.
- Sinyaller (z = değer − önceki 52 haftanın ort. / std; mevcut hafta dışarıda): **P-LEV** kaldıraçlı fon net/OI; **F-LEV** kaldıraçlı fon net/OI'nin
  1 haftalık değişimi; **P-AM** varlık yöneticisi net/OI. |z| ≥ k, k ∈ {1,5; 2,0}; yön **TERS** (−sign z) veya **DEVAM**.
- Geometri D1: TP ∈ {0,5; 1,0}×ATR20 · SL ∈ {2; 3}×ATR20 · H ∈ {5, 10} gün. 3 × 2 × 2 × 8 = 96 hücre (havuz, 8 çift). Maliyet d1.py
  (1,5 × spread + Razor + bugünkü swap; E72).
- KEŞİF 2010–2017 · TEST 2018–21 · KÖR 2022 →. Seçim KEŞİF S70 (isabet ≥ %70 ∧ ort > 0 ∧ t ≥ 2 ∧ sıklık ≥ 3/ay), en yüksek t'li 3 hücre;
  geçme TEST ve KÖR S70 1–6 + aynı hücrenin ayna yönünden iyi. Kontrol: ayna; ek bilgi: rastgele hafta (aynı sayı) 200 çekiliş.

## EK-18 sonucu: X (ön kayıtlı seçim boş). Not: ilk koşuda 2010–2012 dosyalarının tarih sütunu farklıydı (KEŞİF 2013'ten başlıyordu);
`As_of_Date_In_Form_YYMMDD` ile düzeltildi, TFF 2010-06'da başlıyor. Düzeltilmiş KEŞİF'te t ≥ 2 hücre yok (en yüksek 1,20).
**İz (seçimden SONRA bakıldı → en çok C):** KEŞİF t sırasında ilk 3 hücrenin ikisi üç dönemde de artı —
hücre 19 P-LEV z ≥ 2 TERS, TP 0,5 / SL 3 ATR, 10 g: %82,5 +6,8 (P 0,86) / %84,6 +7,8 (0,85) / %80,1 +2,3 (0,63), ayda 1,9–2,5;
hücre 39 F-LEV z ≥ 1,5 TERS, TP 1 / SL 3 ATR, 10 g: %67,4 +9,1 (0,86) / %65,4 +10,4 (0,88) / %69,0 +15,6 (0,97), ayda 2,1–2,3.
(3. hücre P-LEV 1,5 TERS TP 0,5 SL 3: %82,2 +4,6 → TEST −2,9, KÖR −3,8.)

## EK-18b (2026-11-21, EK-18 izinden SONRA; aşağıdakilerin sonuçlarına bakılmadan) — COT-TERS sağlamlık
Hücreler 19 ve 39 birebir (ızgara dokunulmaz). Sınamalar:
- (a) **Gecikme:** giriş bir D1 bar sonra (tatil haftası yayın gecikmesi sızıntısına karşı).
- (b) **Yalnız fiyat kontrolü:** COT z yerine aynı Salı→Salı haftalık getirinin z'si (F-LEV karşılığı) / fiyatın 52 haftalık z'si (P-LEV karşılığı),
  aynı eşik, yön, geometri. COT kontrolden iyi değilse kenar fiyat dönüşüdür.
- (c) **Görülmemiş enstrümanlar:** USDZAR (122741, 2014→), EURGBP (299741, 2014→), EURJPY (399741, 2017→); tüm dönem, tek koşu.
- (d) **Bağımsız dönem 1993–2009:** CFTC eski rapor (legacy, yalnız vadeli) **ticari olmayan** (non-commercial) net/OI → aynı z tanımı;
  Pepperstone D1, maliyet d1.py (2010 öncesi ×2, muhafazakâr). 7 majör (MXN yoksa atla).
- (e) **COT-TERS sepeti** (19 ∪ 39, çift başına tek pozisyon, 39 öncelikli değil — tarih sırası): 2018 → ölçüt S70; seçim sonradan → en çok C.
Geçme (B için): (a) iki hücrede de işaret korunur; (b) COT − kontrol > 0; (c) havuz net > 0 ve isabet hücrenin ±5 puan bandında;
(d) 1993–2009 net > 0 ∧ P ≥ 0,90 ∧ isabet: 19 ≥ %75, 39 ≥ %62. Hepsi → B; (d) düşerse en çok C.

## EK-18b sonucu: X (iz en çok C, yalnız 2010→)
- Hücre 19 (P-LEV z ≥ 2 TERS): (a) 1 gün gecikmeyle KEŞİF −0,7 / TEST +8,6 / KÖR +0,2; (b) **yalnız fiyat kontrolü aynı ya da daha iyi**
  (%83,1 +6,7 / %84,5 +13,6 / %81,1 −0,9) → COT bilgi katmıyor, iz haftalık fiyat dönüşü; (c) görülmemiş USDZAR/EURGBP/EURJPY n 79 −7,5;
  (d) 1993–2009 ticari olmayan net: n 396 %81,3 **−10,2** (P 0,07). → X.
- Hücre 39 (F-LEV z ≥ 1,5 TERS): (a) +10,9 / −1,6 / +9,3; (b) fiyat kontrolü +7,5 / +4,2 / +11,4 (COT 2–6 bp önde); (c) görülmemiş n 113 −0,3;
  (d) 1993–2009 n 641 %63,8 **−5,6** (P 0,17). → X.
- (e) Sepet 19 ∪ 39: %71,8 +5,2 (P 0,77) / %74,1 +7,7 (0,84) / %74,5 +11,0 (0,92); ayda 2,3–2,6 sinyal (< 3), bağımsız dönem eksi → C (gölge adayı değil).

---
## EK-19 (2026-11-21, kullanıcı: "daha derin, daha fazla strateji"; veri indirilmeden önce) — emtia para birimi adil değer sapması
Gerekçe: defterde FX için emtia bağlantısı sınanmadı. CAD/NOK petrol, AUD bakır+altın, ZAR altınla eşbütünleşik sayılır; kısa vadeli
sapma (artık) kapanıyorsa yön bilgisi fiyat dışı bir seriden gelir.
- Veri: yfinance günlük CL=F (WTI), HG=F (bakır), GC=F (altın), plasebo ZC=F (mısır, ilgisiz); 2000 →. Pepperstone D1.
- Eşleme (para birimi değeri y = s·log fiyat, s: para birimi uzun yönü): USDCAD↔CL, USDNOK↔CL, AUDUSD↔HG, AUDUSD↔GC, USDZAR↔GC.
- Her gün: önceki 120 günde y_t'nin log emtia x_t'ye OLS'u (yalnız geçmiş + bugün), artık e = y − (a + b·x); z = (e − ort120(e)) / std120(e),
  b > 0 değilse işlem yok (ilişki tersse). |z| ≥ k, k ∈ {1,5; 2,0} → para birimini adil değere doğru (−sign z). Giriş sonraki D1 açılışı.
- Geometri: TP ∈ {0,5; 1,0}×ATR20 · SL ∈ {2; 3}×ATR20 · H ∈ {5, 10} → 2 k × 8 = 16 hücre (havuz, 5 eşleme). Maliyet d1.py (2010 öncesi ×2), swap bugünkü.
- Dönem: KEŞİF 2001–2009 · TEST 2010–2017 · KÖR 2018 →. Seçim KEŞİF S70 (isabet ≥ %70 ∧ ort > 0 ∧ t ≥ 2 ∧ sıklık ≥ 3/ay); en yüksek t'li 2 hücre.
- Geçme TEST ve KÖR S70 1–6; **plasebo**: aynı kural mısır (ZC=F) ile → gerçek − plasebo > 0 her iki dönemde. Geçerse B.

## EK-20 (2026-11-21, sonuçlara bakılmadan) — hisse endeksi göreli getirisi → para birimi (Hau–Rey yeniden dengeleme)
Gerekçe: yabancı borsa ABD'yi geçince portföyler yeniden dengelenir → o para birimi satılır (Hau & Rey 2006). Defterde yalnız ay sonu fiks
penceresinde (H1) sınandı; günlük/haftalık hiç.
- Veri yerel (qs03 data, 1985 →): GSPC, GDAXI (EUR; 1999 öncesi yok sayılır), FTSE (GBP), N225 (JPY). Pepperstone D1 EURUSD (1999 →), GBPUSD, USDJPY (1993 →).
- d günü: D = (yabancı L günlük log getiri) − (SPX L günlük log getiri), L ∈ {5, 20}; z = D / std(D, önceki 250 gün). |z| ≥ k, k ∈ {1,5; 2,0}.
  Yön **TERS** (ana hipotez: yabancı borsa önde → o para birimi SAT) ve **DEVAM** (ayna). Giriş d+1 D1 açılışı (SPX kapanışı 16:00 ET'den sonra).
- Geometri EK-19 ile aynı (8) → 2 L × 2 k × 2 yön × 8 = 64 hücre (havuz, 3 çift).
- Dönem: KEŞİF 1993–2009 · TEST 2010–2017 · KÖR 2018 →. Seçim ve geçme EK-19 gibi; kontrol = ayna yön.

## EK-19 sonucu: X — 16 hücrenin hepsi KEŞİF'te net < 0 (isabet %56–78, brüt −12…+4,7 bp); mısır plaseboyla aynı düzeyde (brüt −15…−2).
## EK-20 sonucu: X — KEŞİF'te S70'i geçen yok (d1.py'nin 2010 öncesi ×2 çift sayımı düzeltilince de: t ≤ 0,80). Bilgi: TERS yönü 1993–2009'da brüt
+5,6…+11,9 bp (Hau–Rey işareti) ama aynı hücreler TEST/KÖR'de eksi (ör. L5 k1,5 TERS TP 0,5/SL 2/10 g: %81,8 +0,3 → %80,0 −5,3 → %76,1 −10,9).
Not: EK-1/19/20 KEŞİF'indeki 2010 öncesi ×2 maliyet EK-2'de belgelenen çift sayımdır; hükümler düzeltilmiş maliyetle de aynı.

---
## EK-21 (2026-11-21, sonuçlara bakılmadan) — faiz farkı adil değeri + Fed net likiditesi → USD
- **A FAİZ:** EURUSD ↔ ABD 10Y − Euro AAA 10Y (ECB, 2004-09 →), USDJPY ↔ ABD 10Y (TNX). EK-19 artık kuralı birebir (120 g OLS, z120, k 1,5/2,
  8 geometri); beklenen işaret EURUSD b < 0, USDJPY b > 0, aksi gün işlem yok. Plasebo: faiz serisi 260 iş günü geciktirilmiş (bayat). 16 hücre.
  Dönem KEŞİF 2005–2012 · TEST 2013–2018 · KÖR 2019 →.
- **B LİKİDİTE:** QS-03 R4 tanımı (WALCL − TGA − RRP, 4 haftalık % değişim; Çarşamba düzeyi, Perşembe 16:30 ET yayını) → sinyal barı Perşembe D1,
  giriş sonraki açılış. Kural: artış → USD kısa (7 majör: EURUSD, GBPUSD, AUDUSD, NZDUSD uzun; USDJPY, USDCHF, USDCAD kısa), ayna kontrol.
  Eşik {işaret; |z52| ≥ 1}. 2 eşik × 2 yön × 8 geometri = 32 hücre. KEŞİF 2003–2012 · TEST 2013–2018 · KÖR 2019 →.
- Maliyet d1.py, 2010 öncesi çift sayım düzeltilmiş (×2 yok). Seçim/geçme S70 (EK-19 gibi); A'da plasebo, B'de ayna gerçek − kontrol > 0.

## EK-21 sonucu: X — A faiz adil değeri 16 hücre KEŞİF net −3,6…−13,6 (plasebo −11,8…−20,4; gerçek plasebodan iyi ama eksi, ayda ≤ 1,5);
B likidite: en iyi Z1 ANA (artış → USD kısa) %76,6–83,6 isabet, +0,1…+3,2 bp ama t ≤ 0,99 ve ayda 1,3 sinyal; işaret kuralı (ayda 4,2) eksi. Seçim boş.

---
## EK-22 (2026-11-21, kullanıcı: "USDHKD yoksa onunla aynı yönde giden bir enstrüman bulup onda işlem aç") — HK3 sinyali vekile taşınır mı?
**(1) Eş hareket (tanımlayıcı, sonuç):** Pepperstone'da işlem görebilen 13 aday, 2017-09 →. |ρ| en çok 0,31 (FXI aylık −0,31); aynı yön oranı
en çok %59 (USDSGD aylık, USDX haftalık). Pozitif: USDCNH/USDSGD/USDX ρ ≈ +0,2; negatif: HK50/CHINAH/FXI/EWH/CN50/HKEX ρ ≈ −0,2…−0,3; altın ≈ 0.
**"Sürekli aynı yönde giden" enstrüman yok.**
**(2) Sinyal taşıma (sonuçlara bakılmadan):** HK3 tetiği (USDHKD H1 kapanış ≤ 7,7520 — fiyat görünür, işlem gerekmez) olan günler; vekilde ρ işaretine
göre yön (USDCNH/USDSGD/USDX uzun; HK50/CHINAH/CN50/FXI/EWH kısa). Giriş tetik gününün ertesi D1 açılışı; aynı vekilde açık pozisyon varken yeni giriş yok.
Çıkış: (a) USDHKD 7,7540'a (HK3 TP'si) ulaştığı günün kapanışı, en çok 60 iş günü; (b) sabit 5 / 20 iş günü. Stop yok (bilgi: en kötü işlem).
Maliyet: 1,5 × bar spread + komisyon (endekslerde spread), swap bugünkü. Kontrol: aynı vekilde rastgele eşit sayıda gün, aynı yön ve süre (200 çekiliş).
Geçme: işlem ≥ 30 ∧ bağımsız epizod ≥ 8 ∧ isabet ≥ %70 ∧ ort > 0 ∧ rastgele günlerin %95 üstü; geçerse kart (ölçüt 1–6).

## EK-22 (2) sonucu: X — 8 vekil × 3 çıkış: isabet %8–56 (CHINAH TP n 5 hariç), ort. çoğunlukla eksi, hiçbiri rastgele günlerin %95'ini geçmiyor;
en kötü işlemler −140…−1.370 bp. HK3'ün TP'si çoğu kez 1 gün içinde gelen 2,6 bp'lik bant içi hareket; vekillerin oynaklığı bunu yutuyor.
**Sonuç: Pepperstone'da USDHKD yerine geçen, aynı yönde giden ya da HK3 sinyalini taşıyan işlem görebilir enstrüman yok.**

---
## EK-23 (2026-11-21, kullanıcı: "C düzeyi izleri canlıya alacak kadar geliştir"; sonuçlara bakılmadan) — COT-TERS geliştirme
İz: EK-18b sepeti 2010→ %72–75 ama 1993–2009 legacy eksi ve ayda < 3. Mekanizma temelli iki geliştirme, ızgara yok:
- **G1 KALABALIK ∧ HÂLÂ EKLİYOR:** seviye z ≥ 1,5 ∧ aynı işaretli haftalık değişim z ≥ 1,0 → TERS.
- **G2 KESİTSEL:** her yayın haftası 8 para biriminin (USD = 0 kabul, yalnız 7'si ölçülür) seviye z'leri sıralanır; en uzun-kalabalık para birimini sat,
  en kısa-kalabalığı al — çiftleri 25 çift listesinde varsa; yoksa USD karşısında tek bacak (en büyük |z|). Uç farkı ≥ 2,0 (z_maks − z_min).
- Geometri iki sabit: A TP 0,5 / SL 3 ATR / 10 g, B TP 1 / SL 3 ATR / 10 g. → 2 × 2 = 4 hücre.
- Üç bağımsız sınav: TFF 2010–2017, TFF 2018–2026, legacy ticari olmayan 1993–2009 (ayrı sınıflandırma, ayrı dönem). Maliyet d1.py, 2010 öncesi ×2 düzeltilmiş.
- Geçme (B): üçünde de ort > 0, isabet A'da ≥ %75 / B'de ≥ %62, TFF dönemlerinde P ≥ 0,90, ayda ≥ 3 sinyal (G2 için), kart 6/6. Biri tutmazsa C kalır.

## EK-23 sonucu: G1 X (2018–26 −12,3 / −17,3). **G2 kesitsel A** (TP 0,5 / SL 3 ATR / 10 g): 2010–17 n 283 %82,7 +5,7 (P 0,82), 2018–26 n 337 %85,5
+11,3 (P 0,998, yarılar +14,5/+8,1, stres +10,6, ayda 3,2); **legacy 1993–2009 n 474 %78,7 −15,6 (P 0,007)** → ön kayda göre C.
G2 B: 2010–17 +10,2 (0,88), 2018–26 +10,6 (0,96), legacy −19,0.
Uyarı: legacy "ticari olmayan" sınıfı TFF "kaldıraçlı fon" ile aynı değil (varlık yöneticileri de içinde).

## EK-23b (2026-11-21, EK-23'ten sonra; aşağıdakinin sonucuna bakılmadan) — aynı sınıflandırmayla görülmemiş dönem
CFTC TFF geçmişi `fin_fut_txt_2006_2016.zip` 2006-06'dan başlıyor. G2 A ve B birebir (z ısınması 40 hafta → sinyaller ≈ 2007-04 →),
**yalnız 2010-06 öncesi işlemler** değerlendirilir (hiç görülmedi). Geçme: ort > 0 ∧ isabet A ≥ %75 / B ≥ %62. Geçerse G2 → B adayı ve kart.

## EK-23b sonucu: X — G2 A TFF 2007-05 → 2010-05 n 129 %78,3 **−40,0 bp** (P 0,05; 2007 −15,5, **2008 −104,3**, 2009 −7,4; en kötü −1.864),
G2 B n 123 %64,2 −43,5. Kalabalığa karşı işlem kriz çözülmesinde çöküyor; 2010–26 iyi, 2007–10 kötü → **C (canlıya uygun değil)**.
Diğer C izleri: haber anı devamı (2023→ söndü), Hau–Rey (2010→ eksi), ay sonu fiksi (2018→ söndü) — geliştirme ancak sönmenin görüldüğü
veriden seçilebilir (aşırı uyum); dürüst yol yalnız ileri gölge kaydı.

## EK-23c (2026-11-21, EK-23b'nin 2008 çöküşü GÖRÜLDÜKTEN sonra → sonradan, en çok C+) — COT-G2 kriz filtresi
Mekanizma: kalabalığa karşı (dönüş) stratejileri kriz rejiminde çöker (Daniel–Moskowitz momentum çöküşü). Eşikler yaygın, ayarlanmadı:
önceki gün VIX < 30 (ana) ve < 25 (duyarlılık) iken yeni giriş. Dört dönem (TFF 2007–10, 2010–17, 2018–26; legacy 1993–2009 bilgi) raporlanır.
Geçme (C+ → gölge adayı): dört dönemin hepsinde ort ≥ 0 ve TFF dönemlerinde isabet ≥ %75.

## EK-23c sonucu: X — VIX < 30: TFF 2007–10 −14,6 (en kötü −508), legacy −12,9; VIX < 25: −28,6 / −17,8. 2010–26 iki dönemde +4,4…+12,8 (%83–88).
Kayıp yalnız 2008 krizinden değil, 2010 öncesinin tamamından geliyor → çağ bağımlılığı, kriz filtresiyle düzelmiyor. COT-G2 C'de kalır.

## EK-23d (2026-11-21) — ileri gölge kaydı (C izini canlı kanıta taşımanın tek dürüst yolu)
`yeni deneme/cot_g2_shadow.py`: Cuma 21:00 UTC sonrası CFTC TFF yıllık dosyası (önbellek `cot_cache/`), kural EK-23 G2 A birebir, sanal giriş
ertesi D1 açılışı, TP 0,5 / SL 3 ATR20, 10 bar; EMİR YOK. Birebirlik `parity_cot_g2.py`: 870 haftanın 870'inde aynı (çift, yön). Birim testleri
`test_cot_g2_shadow.py` (5). Bota bağlandı (`forexsai_demo_bot.py`, `COT_G2_SHADOW_ENABLED`, varsayılan açık). İlk sinyal: rapor 2026-11-17 →
CHFJPY AL (JPY z +1,26 uzun-kalabalık, CHF z −2,12 kısa-kalabalık). Karne ölçütü: ≥ 40 ileri işlem, isabet ≥ %75 ∧ ort > 0 → ancak o zaman kart.
