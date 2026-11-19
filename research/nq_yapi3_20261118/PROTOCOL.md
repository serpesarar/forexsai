# MC / YC / FD / OS — NASDAQ'a dört farklı bakış: iç yapı korelasyonu, yen carry çözülmesi, FOMC döngüsü, öğle sıkışması

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Defter kontrolü: dördü de defterde yok (DB-02 tahvil satışı × KSG, SD-01 koşulsuz
öğle seansı, GS NR7/inside gün düzeyi; FOMC öncesi gece ve FOMC ertesi veto var, döngünün çift haftaları yok).
§3-43 gereği **durum sinyalleri epizotla** sınanır: giriş = duruma geçiş günü (önceki 5 gün durum dışı), h gün tut, tutuşta yeni giriş
yok; plasebo = aynı yılda aynı sayıda rastgele başlangıç (2.000). Ölçü: gerçek ortalama − plasebo, yüzdelik.
Hedef QQQ (temettü düzeltmeli), bağımsız eş SPY; maliyet 2 bp + uzunda `FIN_BP_PER_DAY` × takvim günü. KEŞİF → 2021-10,
TEST 2021-11 →. Hüküm: KEŞİF'te seçilen yön TEST'te yüzdelik ≥ 0,95 ve SPY aynı yön → B; TEST yüzdelik ≥ 0,90 → C+; aksi X.

## MC — mega-cap iç korelasyonu (12 uzun ömürlü NDX hissesi, 1999+)
AAPL MSFT AMZN INTC CSCO QCOM ADBE AMGN COST PEP CMCSA NVDA. ρ20 = 20 günlük günlük getirilerin ortalama ikili korelasyonu;
yüzdelik (504 g). MC1: ρ20 üst %20'ye geçiş, MC2: alt %20'ye geçiş; h ∈ {5, 20}. Yön KEŞİF'te seçilir (4 hücre).
MC3 (iç genişlik): QQQ 20 g yeni tepe ∧ 12 hissenin ≤ 4'ü 20 g tepesinin %2 yakınında → h 5/20 SAT (yön ön kayıtlı: daralan liderlik
zayıflık). Tetik olay olduğundan epizot = tetik günü, tutuşta yeni giriş yok.

## YC — yen carry çözülmesi (JPY=X 1996+)
USDJPY 5 g getirisi ≤ −2,5 % (yen hızla güçleniyor) → QQQ AL/SAT h ∈ {5, 20}, epizot. Yön KEŞİF'te seçilir (2 hücre).
Ek bilgi: aynı gün QQQ 5 g getirisi ≤ −3 % alt kümesi (carry çözülmesi ∧ hisse düşüşü).

## FD — FOMC döngüsü çift haftaları (Cieslak–Morse–Vissing-Jorgensen 2019)
FOMC günleri: `research/xau_best_days_20261015/makro/out/calendar.csv` (2008+). Döngü günü k = son FOMC'den beri işlem günü
(FOMC günü 0). Hafta t = k ∈ [5t − 1, 5t + 3]. Çift hafta (t = 0, 2, 4, 6) günlük getirisi vs tek hafta (QQQ kapanış → kapanış).
Hücreler: ortalama fark çift − tek, gün-blok bootstrap (blok 5). Makale örneklemi 1994–2016 → 2008–2016 iç örneklem, 2017–2021-10
yayın sonrası, TEST 2021-11 →. Geçme: yayın sonrası ve TEST ikisinde fark > 0, TEST P ≥ 0,90, SPY aynı.

## OS — öğle sıkışması kırılımı (Duka NDX 1m; MT5 NAS100 2m)
Öğle aralığı 12:00–13:30 ET; genişlik / önceki 60 günün aynı penceresi medyanı = s. Sıkışma: s ≤ 0,6. 13:30 → 15:55 arası ilk 1m
kapanış öğle tepesinin üstünde / dibinin altında → sonraki bar açılışında kırılım yönünde giriş, çıkış 16:00 (zaman), stop yok.
Taban: aynı kural tüm günlerde (s her değer). Ölçü: sıkışık − taban, net bp, gerçek spread. Dönemler ESKİ 2018-04 → 2021-10,
KEŞİF 2021-11 → 2024-06, TEST 2024-07 →. Yön ön kayıtlı (kırılım yönü); ayna (kırılımı tersle) yalnız bilgi.
Geçme: KEŞİF ve TEST ikisinde sıkışık net > 0 ve fark > 0, TEST P ≥ 0,90, MT5 aynı yön.
