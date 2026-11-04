# BTC sınavı canlıya hazır kenar çıkarmadı

Bitcoin için canlıya alınabilir, doğrulanmış bir kenar yok. Dört hipotez ailesi koşuldu: stres dönüşü, trend/kırılım, ortalamaya dönüş ve zaman, çapraz varlık ve çıkış. Toplam 230'u aşkın hücre Binance BTCUSDT 1m verisinde (2021-06 → 2026-10-20) sınandı. Giriş sonraki 1m açılışında gerçek spread ve swap ile yapıldı. **Hiçbir hücre genişletilmiş go-live kartının tamamını, Holm'u ve max-z seçim düzeltmesini birlikte geçmedi.** NDX/DAX/XAU'dan taşınan kuralların çoğu BTC'de çöktü. VIX ayağı (CAPREV ve VIXREG), "düşüş sonrası al", XAU'nun R0B_G1 + S2 kuralı, Golden Donchian, momentum filtresi ve kanal-sınır dönüşü bunlar arasında. Taşınan şey kurallar değil, mekanizmalar oldu. **"Coşku dönmez"** BTC'de güçlü: 1 saatlik yukarı şoku satmak −0,194R, plasebonun %0,5 yüzdeliğinde. "Korku döner" ancak korku BTC'nin kendi oynaklığıyla ölçülünce ve yalnız sonradan okunan bir hücrede görülüyor. En güçlü gölge adayı **H4 Donchian kırılımı + D1 EMA200 hizalı BUY**: +0,236R, kartın 1–8. ölçütleri geçiyor, kanıt sınıfı B. Ama aile düzeltmesini geçmiyor, kazancı en iyi ~20 güne bağlı ve 2022 ayısında neredeyse hiç işlem açmadı. Bu yüzden BTC bota **yalnız GÖLGE** olarak eklenmeli. Gölgede adaylar ve vetolar ileri veride ön-kayıtla izlenir. Ayrıca icra kuralları baştan BTC'ye göre kurulmalı: rollover öncesi kapanış, sunucu SL'si, risk tabanlı lot ve hafta sonu etiketi.

## Dört aile, 230'u aşkın hücre ve düzeltmeyi geçen sıfır hücre

Sınama tasarımı projenin kendi kurallarına bağlı kaldı. Her aile önce bir ön-kayıt yazdı, sonra koştu. Dönemler şöyle ayrıldı: KEŞİF 2021-06→2023-12, ETF sonrası OOS 2024-01-11→2025-06, KÖR 2025-07→2026-10-20. Parametre seçimi yalnız KEŞİF'te yapıldı, onay OOS∪KÖR üzerinde hesaplandı. Spread tabanı %0,0185, stres %0,028; ayrıca sabit 15 $ varyantı koşuldu. Long swap −%14/yıl, short +%2/yıl, rollover NY 17:00'de uygulandı. Bootstrap gün-bloklu yapıldı. Plasebo P1 aynı yıl ve aynı UTC saatinden rastgele giriş çekti (ön-kayıtlar: [fam_stres/prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/prereg.md), [fam_trend/prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/prereg.md), [fam_mr_zaman/prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/prereg.md), [fam_capraz_cikis/prereg.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/prereg.md)).

Simülatörlerin kendisi de sınandı. Trend motoru 3.000 rastgele sorguda kaba taramayla **sıfır uyuşmazlık** verdi. Önek (sızıntı) testinden ve karıştırılmış-bar martingal yansızlık testinden geçti ([fam_trend/lib_trend.py](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/lib_trend.py)). Bir kalibrasyon da yapıldı: maliyet modeli bilinen ölü bir kenarı öldürüyor mu? "Turn-of-the-candle" etkisi 2021'de **+0,57 bp** brüt çıktı. Bu, literatürdeki 0,58 bp ile birebir örtüşüyor ([Shanaev vd. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/)). Etki sonraki yıllarda sıfıra çürüdü ve net −1,72 bp'de öldü ([toc_gross_by_year.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/results/toc_gross_by_year.csv)). Yani aşağıdaki negatif sonuçlar model hatasından gelmiyor.

Çoklu sınama sonucu dört ailede de aynı:

| Aile | Hücre | Holm sonrası en iyi p | max-z p_sel en iyi |
|---|---|---|---|
| Stres dönüşü | 75 | 1,0 (4 onay testinin hepsi) | 0,005 (G2, KEŞİF'te; onayda tutmadı) |
| Trend/kırılım | 43 | 0,0147 ham p, eşik 0,0012 → **0/43** | 0,185 |
| MR + zaman | 110 | 1,0 (KEŞİF) | 0,37–0,90 |
| Çapraz + çıkış | 7 hipotez + 10 çıkış varyantı | 0,21 (X04) | 0,003 (X04, KEŞİF'te; POST'ta sönümlendi) |

Kaynaklar: [fam_stres analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json), [fam_trend cells.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/cells.json), [fam_mr_zaman all_cells_verdict.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv), [fam_capraz_cikis summary.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/summary.json).

Aşağıdaki tablo her defter satırı taslağını tek yerde topluyor. Dönemler ailelere göre farklı: stres ailesinde "onay" (OOS∪KÖR), trend ve MR/zaman ailelerinde TAM dönem, çapraz ailesinde POST (OOS∪BLIND). "Kart" altı ölçütlü go-live kartının skorudur.

| Aile | ID | Hipotez | n | ortR | Kart | Verdikt · sınıf |
|---|---|---|---|---|---|---|
| Stres | BTC-S01 | CAPREV-BTC, VIX ≥ 18,4 (seçilen k1,5/US/D1) | 20 | +0,091 | 4/6 | RED · X |
| Stres | BTC-S02 | CAPREV-BTC, BTC RV korkusu (ön-kayıtlı seçim k1,0/UTC/H4) | 44 | +0,047 | 3/6 | RED · C (sonradan D0 hücresi: 44, +0,247, 5/6) |
| Stres | BTC-S03 | Stres ∧ sakin RV günü dip-altı BUY (kontrol hücresi) | 103 (TÜM) | −0,224 | — | B− **veto adayı** |
| Stres | BTC-S04 | Düşüş sonrası ertesi gün BUY (GR-01 portu) | 129 | −0,090 | 1/6 | RED · X |
| Stres | BTC-S05 | 1 sa negatif şok fade BUY | 339 | −0,021 | 1/6 | X |
| Stres | BTC-S06 | 1 sa yukarı şok fade SELL | 322 | −0,194 | 2/6 | X strateji · B **veto adayı** |
| Stres | BTC-S07 | Coşku aynası SELL (gün-içi k1) | 119 | −0,052 | — | X (beklenen) |
| Stres | BTC-S08 | Stres günü SELL yasağı (K5b portu) | 963 saat | fark −0,042 | — | X |
| Trend | BTC-T01 | XAU Golden Donchian 55 BUY | 53 | +0,208 | mekanik SHADOW | C |
| Trend | BTC-T02 | MAX10 / MAX20 günlük long | 353 / 263 | +0,034 / +0,047 | SHADOW (7, 9, 10 ✗) | B− |
| Trend | BTC-T03 | **H4 Donchian 20 + D1 EMA200 BUY** | 305 (SEL 224) | **+0,236** (SEL +0,206) | 1–8 ✓, 9–10 ✗ | **SHADOW · B** |
| Trend | BTC-T04 | XAU R0B_G1 (1h yeni 20-bar tepesi) | 4.429 | +0,078 | SHADOW (8–10 ✗) | B− |
| Trend | BTC-T05 | R0B + S2 kovalama atlaması (SEL) | — | +0,036 | RED | X |
| Trend | BTC-T06 | Bot momentum filtresi, ATR 2/1 | 7.664 | −0,028 | RED | X |
| Trend | BTC-T07 | Gün-içi TSMOM (ETF sonrası) | 696 | −0,039 | RED | X |
| Trend | BTC-T08 | 5m Donchian48 (negatif kontrol) | 5.544 | −0,204 | RED | X (beklenen) |
| MR/zaman | BTC-M01 | Kanal-sınır dönüşü, 32 hücre (ör. 15m RJ BUY ATR) | 7.332 | −0,084 | 1/6 | X |
| MR/zaman | BTC-M02 | **21:01→23:00 UTC long (QB)** | 1.958 | +0,029 (+3,7 bp) | 5/6 (ölçüt 5 ✗) | SHADOW · C |
| MR/zaman | BTC-M03 | Saat-of-gün, 48 hücre | — | 46/48 negatif | — | X |
| MR/zaman | BTC-M04 | Haftanın günü (Çarşamba L) | ~280 | +33,8 bp/gün | 6/6 mekanik | X |
| MR/zaman | BTC-M05 | ABD nakit saatleri + ETF yoğunlaşması | — | L −7,4 / S +3,7 bp | 4/6 | X |
| MR/zaman | BTC-M06 | Funding saati | ~1.967/pencere | −0,8…−2,9 bp | 1/6 | X |
| MR/zaman | BTC-M07 | Turn-of-the-candle | 185.914 | −1,72 bp | 1/6 | X (kalibrasyon ✓) |
| MR/zaman | BTC-M08 | 1h kanal RJ SELL + zaman çıkışı | 1.676 | +0,042 (+0,3 bp) | 5/6 | X |
| Çapraz | BTC-X01 | VIXREG günlük kural | 1.013 | +0,0002 | 2/6 | X |
| Çapraz | BTC-X02 | VIXREG nötr giriş filtresi | 24.309 | +0,021 | 3/6 | X |
| Çapraz | BTC-X03 | Önceki QQQ günü → BTC günü | 224 | −0,007 | 1/6 | X |
| Çapraz | BTC-X04 | **QQQ açılış boşluğunu ters işle** | 267 | +0,034 | 5/6 (P ✗) | RED · C |
| Çapraz | BTC-X05 | BTC–QQQ korelasyon rejimi | — | OOS −0,043 | 1/6 | X |
| Çapraz | BTC-X06 | DXY ↑ → BTC SELL | 686 | +0,006 | 3/6 | X |
| Çapraz | BTC-X07 | US10Y ↑ → BTC SELL | — | −0,004 | 1/6 | X |
| Çıkış | BTC-X08 | Braket vs 24 sa zaman çıkışı | eşli | Δ +0,062 (nötr long) | — | B |
| Çıkış | BTC-X09 | BE @ MFE ≥ 0,5R | eşli | Δ +0,008…+0,012 | — | B |
| Çıkış | BTC-X10 | Kazananı-koştur | eşli | Δ +0,012…+0,019 | — | B |
| Çıkış | BTC-X11 | Swap ekonomisi | — | ≈0,05R/gece (ATR1h stop) | — | A (olgu) |
| Çıkış | BTC-X12 | Hafta sonu işlem bloğu | — | 3 ölçüt ✗ | — | B (blok gerekmez) |

Tablonun dili net. Pozitif ortalama veren hücreler ya kartın bir ölçütünden düşüyor ya da seçim düzeltmesinden. Kartın 6/6'sını geçen tek hücreler Çarşamba long ve hafta sonu long. Bunlar ~280 haftalık gürültüden çıkan ve Holm p'si 1,0 olan takvim artefaktları ([all_cells_verdict.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/results/all_cells_verdict.csv)). Bu sonuç literatürle de uyumlu: [Mueller (2024)](https://ideas.repec.org/a/eee/finlet/v64y2024ics1544612324004598.html) kriptoda sağlam bir mevsimsellik bulamadı.

## Dört gölge adayı ayakta, hiçbiri B'yi aşmıyor

**H4 Donchian 20 + D1 EMA200 hizalı BUY (BTC-T03, sınıf B)** ailenin en güçlü hücresi. Kural XAU'daki H4_DONCH30 varyantının BTC karşılığı. Giriş koşulu: H4 kapanışı önceki 20 H4 tepesine ulaşmış ve D1 kapanışı EMA200'ün üstünde olmalı. Stop 2×ATR14(H4), hedef 4×ATR14, süre 30 bar. TAM dönemde 305 olay, **+0,236R [+0,027, +0,453]**, P %99. Yarılar +0,254 / +0,218, P1 plasebo yüzdeliği %97,5, BLIND +0,270 (n 62). N=55 platosu daha da iyi: +0,269R, BLIND +0,481 ([summary.md](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/summary.md)). Önemli bir kontrol de geçildi. XAU'da "D1 trend filtresi yalnız sürüklenmeyi seçiyor" uyarısı (MK-07) BTC'de tutmuyor. Trend koşullu rastgele BUY tabanı P2 −0,020 kalıyor ve kırılım tetiği bunun %99,5–100 yüzdeliğinde ([amend_p2_swap.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_trend/results/amend_p2_swap.json)). Swap kenarın yalnız ~%12'sini yiyor (0,033R).

Buna rağmen hücre LIVE değil, dört nedenle. Birincisi, ön-kayıtlı birincil hücre filtresiz H4D20-L'ydi ve o RED çıktı (BLIND −0,107). Filtreli hücre KEŞİF'te seçildi ve max-z p_sel 0,39–0,74. İkincisi, tek pozisyonlu sette en iyi 20 gün çıkarılınca beklenti **−0,157**'ye dönüyor. Üçüncüsü, filtre 2022 ayısında yalnız 3 işlem açtı. KEŞİF'teki 81 olayın 78'i 2023'te, yani kenar fiilen tek bir ayı rejiminde hiç sınanmadı. Dördüncüsü, yılda ~26 tek-pozisyon işlemle ileri gölgede n=100'e ulaşmak ~4 yıl alır.

**CAPREV-BTC, RV korkulu, D0 çıkışı (BTC-S02'nin sonradan okunan hücresi, sınıf C).** Ön-kayıtlı seçim çıkış boyutunda H4'ü seçti ve onayda tutmadı: +0,047R, OOS −0,063. Seçilmeyen gün sonu çıkışı (`G2_k1.0_UTC_D0`) ise üç segmentte de pozitif. TAM dönemde n 64, +0,225R. Onayda n 44, +0,247R, plasebo %96,5 ve kart 5/6; yalnız hacimden düşüyor ([analysis.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/analysis.json)). k=0,75…2,0 ve RV>%50–60 eşiklerinde desen plato veriyor ([posthoc_g2.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/posthoc_g2.json)). Ama hücre ön-kayıtlı seçim değildi ve yılda ~12 olay üretiyor. Bu bir bulgu sayılmaz; ileri veride dondurulmuş k=1,0/D0 ile sınanacak bir adaydır. BTC CAPREV günlerinin NDX/DAX CAPREV günleriyle ne kadar örtüştüğü ölçülmedi. Örtüşme yüksekse BTC portföye bağımsız işlem değil, kaldıraç ekler.

**21:01 → 23:00 UTC long, swap'tan kaçan biçim (BTC-M02 QB, sınıf C).** Quantpedia'nın Gemini verisinde bulduğu 21–23 UTC etkisinin yönü BTCUSDT'de tutuyor ([Quantpedia](https://quantpedia.com/the-seasonality-of-bitcoin/)). Net +3,7 bp/işlem, plasebo yüzdeliği %100; OOS ve KÖR pozitif. Ancak kenar yaklaşık iki spread büyüklüğünde. Bu yüzden kartın icra ölçütü düşüyor ve yayın sonrası Holm p'si 0,88. 2022 +0,3 bp, 2026 −3,2 bp. Net toplamın **%93'ü en iyi 20 günden** geliyor ([timing_cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_mr_zaman/results/timing_cells.csv)). Biçim kritik. "21:00'de gir" varyantı kışın 22:00 rollover'ını kesiyor, swap ödüyor ve kış alt kümesinde −2,55 bp ediyor. Bu nedenle yalnız rollover'dan bir dakika sonra giren biçim anlamlı.

**QQQ açılış boşluğunu ters işlemek (BTC-X04, sınıf C).** Kural: |QQQ boşluğu| > 0,5σ ise 10:00 ET'de boşluğun tersine gir, 16:58 ET'de çık. KEŞİF'te +0,211R çıktı (max-z p_sel 0,003). POST'ta +0,034R'ye sönümlendi: P %79, kart 5/6, Holm p 0,21 ([regime.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/regime.json)). Yıllık seyir 2021–23 ≈ +0,2R'den 2024–26'da +0,01…+0,08R'ye düşüyor. Bu çürüme ETF sonrası ABD saatlerindeki likidite artışıyla uyumlu ([Kaiko](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure)). İki kol simetrik çalışıyor. BTC'nin kendi gece dönüşünü kullanan kontrol negatif çıktı, yani etkiyi taşıyan QQQ boşluğunun kendisi ([c04_posthoc.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/c04_posthoc.json)).

İki zayıf aday daha var. MAX10/MAX20 günlük long (B−) üç bölmede de pozitif, ama her gün BUY tabanının yalnız birkaç baz puan üstünde: +0,034 / +0,047R. Literatürdeki yüksek Sharpe iddiası gerçek spread, swap ve R ölçüsünde bu kadar küçülüyor ([PapersWithBacktest](https://paperswithbacktest.com/blog/bitcoin-never-sleeps-exploiting-seasonality)). R0B_G1 (B−) KEŞİF ve OOS'ta XAU desenini tekrarlıyor (+0,078 vs P1 +0,023), ancak BLIND'da işaret dönüyor (−0,054). Bu iki kural ileri gölgeye alınmaya değmez, bilgi olarak kaydedilir.

## Coşku dönmez taşındı; VIX ve düşüş sonrası alım taşınmadı

En temiz taşınan ders **"coşku dönmez"**. Son 60 dakikada ≥ +3,5σ yükselmiş BTC'yi satmak (BTC-S06) onayda **−0,194R** verdi: %95 GA [−0,309, −0,079], P(EV>0) %0,1, plasebo yüzdeliği %0,5. KEŞİF, OOS ve KÖR'ün üçünde de −0,13…−0,19 ([fam_stres cells.csv](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_stres/results/cells.csv)). Günlük ölçekte de aynı. Yükseliş gününün ertesinde SELL açan coşku aynası (BTC-S07) sekiz hücrenin sekizinde ≤ 0. Pratik karşılığı bir veto: **"60 dk ≥ +3,5σ ise BTC'de SELL açma"** (B). Aynı kalıbın aynası da var: yukarı şoktan sonra BUY devamı +0,113R. Ama bu getiri segmentlere göre +0,184 → +0,061 → +0,020 diye sönüyor; kenar değil.

"Korku döner" ise yarım taşındı. NDX'teki CAPREV iki şart istiyor: stres ve yüksek VIX. BTC'de VIX ayağı yön ayırmıyor; VIX'in 2×2 hücreleri dönemler arasında işaret değiştiriyor. Korku BTC'nin kendi 30 günlük RV'siyle ölçülünce NDX'in deseni geri geliyor. Stres ∧ yüksek RV pozitif, **stres ∧ sakin RV ise üç segmentte de negatif**: −0,234 / −0,334 / −0,123, onay P(EV>0) %2,1, nominal −44 bp/işlem. Bu ikinci hücre ön-kayıtlı bir kontrol hücresiydi. Bu yüzden **"stres ∧ sakin RV günü dip-altı BUY yok"** vetosu (B−) pozitif CAPREV-RV hücresinden daha sağlam. Her gün "dip altına inince al" (filtresiz) ise rastgele girişten kötü: onay −0,101R, plasebo yüzdeliği %1. 1 saatlik negatif şok fade'i maliyet sonrası kenarsız (−0,021R). [De Nicola (2021)](https://epub.ub.uni-muenchen.de/97651/)'nın 1–4 saatlik negatif otokorelasyonu, spread ve sonraki-1m icrasıyla paraya dönüşmüyor.

Taşınmayanların listesi uzun ve öğretici. **"Düşüş sonrası al" (GR-01)** BTC'de tersine dönüyor. Büyük düşüşün (k=2) ertesi günü long, onayda −0,338R, P %0,8. Literatürdeki "büyük ve likit coin'ler günlük momentum gösterir" bulgusuyla tutarlı ([Zaremba vd. 2021](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002349.html)). **VIXREG** POST'ta tam sıfır (+0,0002R), çünkü 2022'de günlerin %98,6'sı yüksek VIX'ti ve kural fiilen "ayıda long" oldu. **Momentum filtresi + ATR 2/1** NDX'te +0,079R iken BTC'de −0,028R. Yakın hedefte WR %55,9 çıkıyor ama başabaş %58,0. **Kanal-sınır dönüşü** 32 hücrenin 31'inde ≤ 0. Alt banttan BUY'un plasebo yüzdeliği %0–1,5, yani BTC'de alt bant düşen bıçak. **NDX'in K5b "stres günü SELL yok"** kapısı BTC'de desteklenmiyor. XAU'nun A sınıfı **S2 kovalama atlaması** bölmeler arasında işaret değiştiriyor. **Golden Donchian** BLIND'da −0,41 (n 8). **QQQ, DXY ve US10Y** günlük yön öncülüğü yok. **Funding saati** ve **saat/gün takvimleri** de ölü. Bu tablo projedeki GF-03 dersini ("takvimler çağlar arası taşınmaz") ve MK-03 dersini ("yeni-tepe davranışı piyasaya özgü") BTC'de bir kez daha doğruluyor ([KAPI_KAYIT_DEFTERI.md](file:///Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)).

Çıkış mekaniğinde bir projede reddedilmiş bir bulgu BTC'de tekrarlanmadı. **BE @ MFE ≥ 0,5R** (botun bugünkü `conditional_mfe` modu) BTC'de zararsız, hatta küçük bir artı veriyor: +0,008…+0,012R. NDX ve bot ailesindeki "BE kurtardığından çok kazanan öldürür" (M7–M9) burada görülmedi. "Braket ≠ zaman" yalnız long tarafta geçerli: 24 saatlik zaman çıkışı 1R braketten +0,05…+0,06R iyi. Mekanizma BTC'nin long sürüklenmesi, short'ta fark yok. Kazananı-koştur long'da üç dönemde de küçük bir artı (+0,012…+0,019R). Ancak hiçbir yönetim kuralı negatif bir girişi pozitife çevirmiyor ([exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json)).

## Pepperstone BTCUSD: 15 dolar spread, −%14 swap, UTC+3 sunucu

**Veri ve broker gerçekleri.** Kaynak Binance spot BTCUSDT 1m. 84/84 dosya SHA256 ile doğrulandı. 2025-01'den itibaren zaman damgası mikrosaniye ([binance-public-data](https://github.com/binance/binance-public-data)). Seri 2.833.450 satır; 470 eksik dakikanın hepsi üç kesintiden geliyor. 2023-03-24'teki Binance spot durdurması 72 sıfır-hacimli bar bıraktı ve backtest'ten dışlandı ([btc_quality_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/btc_quality_report.json)). Kutudaki hesap **Pepperstone-Demo**. Sembol `BTCUSD`, CFD, 1 lot = 1 BTC, min lot 0,01, maks 22, stops_level 0, IOC dolum. Marjin ≈ %5, yani hesap 1:200 olsa da kripto 1:20. Swap modu INTEREST_CURRENT: long −%14/yıl, short +%2/yıl. Sembol Market Watch'ta **gizli** (`visible=False`), bu yüzden bot tick ve bar almak için önce `symbol_select` yapmalı ([box_01_specs_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_01_specs_out.txt)).

Spread neredeyse sabit **15,00 $** (≈ %0,018). 14 günlük tick verisinde zaman-ağırlıklı ortalama 15,99 $, p99 ~40 $. Hafta sonu ortalaması 16,33 $ ([box_03_ticks_out.txt](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker/box_03_ticks_out.txt)). Yani FXNX'in "hafta sonu 100–350 $" iddiası bu broker için geçerli değil ([FXNX](https://fxnx.com/en/blog/btcusd-cfd-contract-specs-lot-size-margin-weekend-swap)).

Sunucu saati **UTC+3**. Ofset hem doğrudan ölçüldü hem Binance korelasyonuyla doğrulandı: +180 dk'da r 0,888. Ofset **2026-11-01'de UTC+2'ye** dönecek ([Pepperstone trading hours](https://pepperstone.com/en-au/ways-to-trade/trading-hours)). Broker her gün 2 dk kapanıyor: yazın 20:59–21:01 UTC. Cuma kapanışı 6 dk. Hafta sonunda düzensiz bakım boşlukları var; 2026-10-17'de 129 dk sürdü. Broker USD fiyatını izliyor; Coinbase BTC-USD'ye göre fark ±8 $. Binance USDT fiyatı ise USDT iskontosu kadar, yani ~%0,1 yukarıda. Getiri korelasyonu 1m'de 0,889, 1h'de 0,997. Bu yüzden ≥5m kurallarda Binance broker'ın iyi bir vekili ([broker_compare_report.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/broker_compare_report.json), [basis_check.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/data/basis_check.json)).

Swap rakamında çelişki var. MT5 spesifikasyonu −%14 diyor, Pepperstone'un Haziran 2026 maliyet belgesindeki örnek −%22,5 ([Pepperstone Cost & Charges](https://eu-assets.contentstack.com/v3/assets/bltaec35894448c7261/bltb3f65365f20ef593/6a1ebf2ab3c954c1e626efea/Pepperstone_Limited_Cost_and_Charges_-_June_2026.pdf)). −%22,5 geçerliyse Golden Donchian ~+0,16R'ye, H4 adayı ~+0,21R'ye iner. Doğrulanmayanlar şunlar: komisyon, 360/365 bölücü, hafta sonu tahakkuku ve gerçek dolum/kayma. BTC'de hiç pozisyon açılmadığı için bunlar ölçülemedi.

**Bot BTC'yi nasıl ele almalı?** Cevap: **gölge**. Hiçbir aday canlı emir açmaz. Canlıya geçiş ancak ileri gölge kartı 6/6 ve 2. Kural'daki go-live kartı ile olur. İcra kuralları bulgulardan doğrudan türüyor. Gün-içi, ATR(1h) ölçekli bir BTC long'u **rollover'ı geçmemeli**. Tek gece swap'ı ≈ 0,05R (hafta sonu 0,07R) ve bu, bu çalışmada görülen her kenardan büyük. Zaman stopu NY 16:58 olmalı (yaz 20:58 / kış 21:58 UTC). Yeni girişler rollover'dan bir dakika sonra açılabilir. Gün ölçekli swing'lerde (dvol stoplu) gecelik ~0,013R bedel beklentiye eklenmeli ([exits.json](file:///Users/melihcanodacioglu/Desktop/panel/research/btc_5y_20261021/fam_capraz_cikis/results/exits.json) `swap`).

**Hafta sonu** işleme açık kalabilir. Ön-kayıtlı üç blok ölçütünün hiçbiri geçmedi; kapalı pencere boşluk kaybı ≈ 0R. Ancak hafta sonu işlemleri ayrı etiketle izlenmeli, çünkü momentum girişleri KEŞİF ve OOS'ta hafta sonu daha kötüydü ve ATR %27 daha dar. **Sunucu SL'si zorunlu**: 129 dakikalık düzensiz bir bakım 1×ATR(1h) stopu kolayca atlar. TP konusunda iki seçenek var. Basit yol sunucu TP'si. Koştur'un +0,01–0,02R'sini almak isteniyorsa sanal TP gerekir, artı bot çökmesine karşı sunucuda uzak bir felaket TP'si (ör. 3R; bu sınanmadı). NDX'te sunucu TP'si koştur'u bir kez bile tetiklememişti; aynı tuzak BTC'de tekrar etmemeli.

**Lot** risk tabanlı olmalı: `lot = hedef_risk_$ / SL_mesafesi_$`, 0,01 adıma yuvarlanır. BLIND'da medyan ATR14(1h) 467 $ olduğu için 1 lot ≈ 467 $/R. Örneğin 250 $ risk → 0,53 lot. **Endeks botunun 5,0 lot ayarı kopyalanmamalı.** 5 BTC ≈ 410 bin $ nominal ve ≈ 2.300 $/R eder. Yeni BTC magic'i `_bot_magics()`'e ve günlük frene eklenmeli (IO-21 dersi). Broker saat çevrimi sabit +3 ile değil, DST'ye duyarlı yapılmalı.

**Vetolar** gölgede kayıt olarak çalışmalı. Bunlar: "60 dk ≥ +3,5σ → SELL yok", "stres ∧ sakin RV → dip-altı BUY yok" ve kanal alt bandından BUY yasağı. Katkıları ancak botun gerçek BTC sinyal popülasyonunda ölçülebilir (E18/E19). Çapraz varlık filtreleri (VIX, QQQ, DXY, US10Y) kapı olarak bağlanmamalı. Girişte `spread > 40 $` vetosu makul görünüyor (tick p99 ≈ 40–47 $), ama sınanmadı.

## Çakışan E40–E43 önerileri ayrı ayrı yazılmalı

Dört ajan deftere bağımsız olarak yöntem tuzağı önerdi. Birkaçı aynı ID'yi (E40, E41) kullandı. Aşağıda dokuz öneri **kesin ID atanmadan** ayrı ayrı veriliyor. Ajanın önerdiği ID parantez içinde. Deftere girerken §1'in son numarasından sırayla numaralanmalı.

| Öneri | Kaynak aile (önerilen ID) | Tuzak | Vaka |
|---|---|---|---|
| A | Stres (E40) | Uzun ısınmalı rejim göstergesi (365 g RV medyanı) KEŞİF'i sessizce kısaltıyor. Seçim 12–20 olayla yapılıyor ve en gürültülü boyutu seçiyor | G2 KEŞİF'te H4'ü seçti (p_sel 0,005), onayda OOS negatif. Seçilmeyen D0 üç segmentte de pozitifti |
| B | Stres (E41) | BUY-fade − SELL-fade asimetrisi "korku döner" teyidi sanılabilir. Fark SELL kolunun kaybından gelebilir | BTC-S06: fark +0,173 ama BUY kolu −0,021 |
| C | Trend (E40) | Yansızlık testinde yalnız kapanış getirilerini karıştırmak bar-içi sürekliliği bozar ve sahte stop dokunuşları üretir | İlk sentetik deneme martingalde −0,41R verdi |
| D | Trend (E41) | Stoplu + zaman çıkışlı taban yönsüz bir kenar taşıyabilir; iki yön de pozitif çıkar | 10:00→16:00 ET'de rastgele long +0,087, short +0,067 |
| E | Trend (E42) | 7/24 piyasada ≥1h TF'de kartın icra ölçütü neredeyse boş kalır | Fark 0,001–0,024R; yalnız 5m'de 0,136R |
| F | Trend (E43) | Trend filtresi ayı yılını boşaltır; KEŞİF fiilen tek bir boğa yılına dayanır | H4-T-L KEŞİF'teki 81 olayın 78'i 2023'te |
| G | MR/zaman (E40) | Sabit UTC penceresi + DST'li broker rollover'ı maliyeti mevsime bağlar | "21:00 gir": yaz +4,26 bp, kış −2,55 bp |
| H | Çapraz (E40) | Kalıcı rejim sinyalinde yıl-içi permütasyon plaseboyu fazla iyimser yapar. Dairesel kaydırma kullanılmalı | VIXREG KEŞİF p_sel 0,003; dairesel kaydırmada %77,5 yüzdelik |
| I | Çapraz (E41) | ATR-normalize R'de swap maliyeti stop ölçeğiyle büyür | 0,05R/gece (ATR1h) vs 0,013R/gece (dvol) |

Bunlara ek olarak iki yan not var. Birincisi, mevcut E32'nin ("R ile bp ayrışması") iki yeni BTC örneği: BTC-M08'de +0,042R'ye karşılık +0,3 bp, G4'te ise −0,092R'ye karşılık −0,6 bp. İkincisi, BTC'de 15m ATR stopları barların %24'ünde %0,3'ün altına iniyor. Bu stoplar, Binance'e göre %12 daha gürültülü broker 1m kotasyonunda farklı tetiklenir.

## İleri gölge testi, tek gerçek yeni veri kaynağı

KÖR dönem bu turda bir kez açıldı ve harcandı. Aynı veride yeni bir tarama yapmak E23'ün ("aynı geçmişe tekrar tekrar bakma") BTC versiyonu olur. Bundan sonra kanıt yalnız iki yerden gelebilir. Birincisi **2026-10-22 sonrası ileri veri**. İkincisi **2021-06 öncesi bağımsız BTC 1m geçmişi** (Coinbase/Bitstamp 2017–2021). Bu ikinci kaynak hiç bakılmamış veridir ve defterin "yeniden açmak için yeni veri" şartını karşılar. 21–23 UTC kuralı için ise bağımsız sayılmaz, çünkü literatürdeki Gemini 2015–2023 örneklemiyle örtüşür.

Önerilen ön-kayıt, kurallar dondurularak aşağıdaki gibidir. Ön-kayıtın yazılmasında sonuçlar kullanılmaz. Hesaplamalar şöyle yapılır: broker BTCUSD M1 üzerinde, broker bid/ask ile, sonraki M1 açılışından, gerçek spread ve tahakkuk eden swapla. Geçme ölçütleri altı ölçütlü kart, artı P1 plasebo ≥ %95, artı kronolojik iki yarının ikisi ≥ 0.

| Kural (dondurulmuş) | Sınıf | Beklenen hız | Ara kontrol | Nihai karar |
|---|---|---|---|---|
| BTC-M02 QB: rollover+1 dk long → 23:00 UTC, swap yok | C | ~365/yıl | n=100'de ortR<0 ∧ P<%20 → bırak | n=150 (~5 ay) |
| BTC-X04: \|QQQ boşluğu\| > 0,5σ20 → ters yön, 10:00→16:58 ET | C | ~95/yıl | n=50 | n=150 (~1,5 yıl) |
| BTC-T03: H4D20 + D1 EMA200 BUY, 2/4 ATR, 30 bar (H4D55 bilgi) | B | ~26/yıl tek-poz | yıllık | n=100 (~4 yıl) veya 2017–21 geçmişiyle tek seferlik sınav |
| BTC-S02 D0: stres k=1,0 ∧ RV>365g medyanı → dip-altı ilk 1h kapanış BUY, gün sonu | C | ~12/yıl | yalnız betimsel | 2017–21 geçmişi + NDX/DAX CAPREV ile gün örtüşmesi |
| Vetolar: +3,5σ SELL yok · stres ∧ sakin RV dip-alımı yok · kanal alt bandı BUY yok | B/B− | bot sinyaline bağlı | tetiklendiği her kayıt | botun BTC sinyallerinde veto katkısı (E19) |

Bu takvim dürüst bir gerçeği gösteriyor. Bir yıl içinde karar verilebilecek tek aday QB. Onun beklentisi de iki spread büyüklüğünde ve tek pozisyonla yılda ~0,03R/işlem getiriyor. H4 adayı ve CAPREV-RV için ileri gölge yıllar alır. Bu ikisini hızlandırmanın meşru yolu 2021 öncesi bağımsız geçmişte **tek seferlik**, dondurulmuş bir sınamadır.

Ölçülmemiş broker belirsizlikleri de var: swap'ın gerçek tahakkuk anı ve bölücüsü, komisyon, kayma. Bunları kapatmak için iki seçenek var. Biri, 0,01 lotluk ve strateji iddiası taşımayan bir demo "icra probu". Bu bir emir açılması demektir; kararı kullanıcıya aittir. Diğeri, gölge karnenin bu kalemleri ilk gerçek işlemlerde ayrıca loglaması.

Son olarak açık işler var. Ajanlar yazma kısıtı nedeniyle 1. ve 3. Kural'ın gerektirdiklerini yapmadı. Defterde yeni bir "§2.11 BTC kenar araştırması" bölümü açılmalı ve S01–S08, T01–T08, M01–M08, X01–X12 satırları oraya girmeli. Dokuz yöntem tuzağı önerisi §1'e numaralanarak eklenmeli. Evrim Paneli oturum notu ve backlog girdileri yazılmalı: ileri gölge, 2017–21 sınavı ve icra probu. Kod henüz commit edilmedi ve kutuya hiçbir şey gönderilmedi.

## Sonuç

BTC, NDX/DAX/XAU kurallarının ilk gerçekten bağımsız sınavıydı ve sonuç projenin meta-derslerini sertleştirdi. Kurallar, eşikler ve takvimler bir piyasadan diğerine taşınmıyor. Kısmen taşınan şey yapısal asimetri: yükseliş şoku devam ediyor, düşüş ise ancak piyasanın kendi korku ölçüsü yüksekken dönüyor. NDX'te bu korku ölçüsü VIX'ti; BTC'de VIX işe yaramadı, BTC'nin kendi RV'si işe yaradı. Bu, "korku döner" ilkesinin harici bir gösterge değil, varlığa özgü bir oynaklık rejimi istediğini düşündürüyor. Bunu sınamak NDX'te de yeni bir ön-kayıt sorusu olabilir.

İkinci ders maliyet ölçeğiyle ilgili. BTC'de bulunan bütün pozitif etkiler ±0,03–0,25R aralığında. Tek bir long gecesinin swap'ı (≈0,05R) bu etkilerin çoğunu siler. Dolayısıyla BTC botunun ilk mühendislik kazancı bir sinyalden değil, rollover disiplininden, risk tabanlı lottan ve sunucu SL'sinden gelecek. Bu altyapıyı bugün gölgede kurmak, yarın bir aday kartı geçtiğinde onu doğru icra etmenin önkoşulu.
