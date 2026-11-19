# SN / VS / HP / SB — son dört kapı adayı, hepsi zaman çıkışlı (TP/SL yok)

Ön kayıt: 2026-11-18, sonuçlara bakılmadan. Kullanıcı isteği: son 4 geçerli kapı; olay → giriş → belirli süre sonra çıkış.
Ortak kurallar: §3-43 (durum ya da olay sinyali **epizot** olarak, tutuşta yeni giriş yok, aynı yıl rastgele başlangıç plasebosu
2.000 kez), §3-42/§3-44 (tek çağ kanıt değil: her adayda en az bir hiç dokunulmamış dönem ya da besleme). Maliyet: günlük 2 bp +
uzunda `FIN_BP_PER_DAY` × takvim günü; gün içi gerçek spread (Duka) / broker spread (MT5), ×1,5 stres.
Hüküm ölçeği: B = ön kayıtlı birincil hücre bağımsız dönemde / beslemede aynı yönde, plasebo yüzdeliği ≥ 0,95 (havuz) ve 2. KURAL
kartı ≥ 5/6; C+ = aynı yön, yüzdelik ≥ 0,90; aksi C/X. Birincil hücre aşağıda yazılıdır; komşular yalnız dayanıklılık için.

## SN — NASDAQ yükseliş serisi momentumu (NQ-03 C+ genişletmesi)
^NDX günlük 1985-10 →, QQQ 1999-03 →, MT5 NAS100 broker günlük (2008-08 →, 17:00 ET gün kapanışı). Seri = art arda yükselen
kapanış sayısı. **Birincil: seri 6'ya ulaştığı gün kapanışta AL → 5 işlem günü sonra kapanışta SAT** (tutuşta yeni giriş yok).
Komşular: seri 5/7, tutuş 3/10 gün. Dönemler 1985–1999-02 / 1999-03–2009 / 2010–2017 / 2018 → (NQ-03 ile aynı) + son 5 yıl.
İcra (kart 5): sinyal kapanışta bilinir → gerçekçi giriş ertesi açılış (QQQ) / broker 16:00 sonrası ilk fiyat; iyimser = kapanış.
B için ayrıca: kör SPY/DIA/IWM'de yön zorunlu değil (NQ-03 NASDAQ'a özgü buldu), broker 2008+ artı olmalı.

## VS — VIX vade (uzlaşma) haftası (yeni)
VIX vade günü = sonraki takvim ayının üçüncü Cuma'sından 30 gün önceki Çarşamba (tatilse önceki işlem günü). Uzlaşma Çarşamba
açılışındaki SPX opsiyon fiyatlarından (SOQ). VIX vadelisi 2004-03'te başladı → **1990–2003 aynı takvim = mekanizmasız plasebo çağı.**
Pencereler (QQQ/^NDX açılış-kapanış; ^NDX açılışı 1990'larda güvenilmez → plasebo çağında SPY ve QQQ 1999+):
W1 Pazartesi kapanış → Çarşamba açılış (uzlaşmaya doğru), W2 Çarşamba açılış → kapanış, W3 Çarşamba kapanış → Cuma kapanış,
W4 vade haftası Pazartesi kapanış → Çarşamba kapanış. Taban: aynı pencerenin vade dışı haftalardaki ortalaması.
Yön KEŞİF 2004-03 → 2015'te seçilir; TEST 2016 → 2026 (son 5 yıl ayrıca). B: TEST yüzdelik/P ≥ 1 − 0,10/4 seçilen yönde, plasebo
çağında fark yok (|t| < 1,5), SPY aynı yön.

## HP — aynı saat diliminin sürekliliği (Heston–Korajczyk–Sadka 2010 periyodikliği, yeni)
Saatlik RTH dilimleri 10–11, 11–12, 12–13, 13–14, 14–15, 15–16 ET (saat başı fiyatları; Duka 1m ve MT5 NAS100 H1 aynı ızgara).
s_{d,j} = j diliminin son L = 20 işlem günündeki ortalama getirisi (d hariç). **Birincil P1: her gün her dilimde sign(s_{d,j})
yönünde işlem, dilim başında gir dilim sonunda çık.** P2: yalnız en yüksek s dilimde AL + en düşük s dilimde SAT. P3: L = 40.
Plasebo: s'yi başka dilimin (j + 3 mod 6) geçmişinden almak (gün etkisi korunur, dilim kimliği bozulur). Dönemler: MT5 H1
2016-01 → 2018-04 (hiç kullanılmamış gün içi dönem), Duka 2018-04 → 2021-10 / 2021-11 → 2026-11; MT5 H1 2018+ bağımsız besleme.
B: P1 net > 0 ve gerçek − plasebo > 0 üç dönemde ve iki beslemede, havuz P ≥ 0,95.

## SB — sabah trendine katıl (AL-02 C+ genişletmesi + haber ayrımı)
R = p13:00 / p09:30 − 1 (H1 beslemede p13:00 / p10:00), σ20 = R'nin önceki 20 gün std'si. **Birincil: |R| ≥ 1,0·σ20 → 13:00'te
R yönünde gir, 16:00'da çık.** Haber ayrımı (§3-38 haber hareketi sürer): olay günü = CPI/NFP/FOMC/Jackson Hole (takvim 2008+);
ön kayıtlı öngörü olay günü ≥ olaysız gün. Komşu k = 1,5. Beslemeler: Duka NDX 1m (AL-02'de kullanıldı), **kör**: MT5 NAS100 H1
2016-01 → 2018-04, MT5 US500/US30/US2000 M30 2018+, NQ 5m 2019–24, EET30 2016+. B: kör beslemelerin havuzunda net > 0, P ≥ 0,95
ve kart ≥ 5/6 (Duka).

## EK-1 (2026-11-18, VS sonucu görüldükten sonra) — W3 aslında OPEX haftası Perşembe–Cuma etkisi mi?
Gözlem: W3 (vade Çarşambası kapanış → Cuma kapanış) KEŞİF'te SAT seçildi; TEST QQQ fark +37,8 (P 0,981 ≥ 0,975), SPY +30 (P 0,984);
ama VIX vadelisi öncesi 1993–2004'te de SPY +25,5 (t 1,68) → mekanizma VIX değil. VIX vade Çarşambası çoğu ay aylık OPEX
(ayın 3. Cuma'sı) haftasının Çarşamba'sı. Yeni tanım (**OX**): OPEX Cuma'sı F (tatilse önceki işlem günü), giriş F'den 2 işlem günü
önceki kapanış (Çarşamba), çıkış F kapanışı, **SAT**. Taban: diğer haftaların Çarşamba kapanış → Cuma kapanış.
Sınamalar (hiçbiri VS'de kullanılmadı): (a) ^NDX 1985-10 → 1999-02; (b) ^GSPC 1983-04 → 1998 (endeks opsiyonu var);
(c) **mekanizma plasebosu ^GSPC 1950 → 1983-03** (endeks opsiyonu yok, etki beklenmez); (d) gün içi kör: Duka NDX 2018+,
MT5 NAS100 H1 2016+, MT5 US500/US30/US2000 M30 2018+ (Çar 16:00 → Cum 16:00); (e) çeyrek OPEX (Mar/Haz/Eyl/Ara) vs diğer aylar
(bilgi). Geçme B: (a) ve (b) fark > 0 ve P ≥ 0,90, (c) |t| < 1,5, (d) havuz fark > 0 ve P ≥ 0,90, + 2. KURAL kartı ≥ 5/6.

## EK-2 (2026-11-18) — OPEX Perşembe–Cuma vetosu kanıtlı uzun kurallarda
OX iz verdi (NDX 4 dönem fark > 0, gün içi kör havuz P 0,993) ama B değil. Kapı olarak sınama: kanıtlı uzun kuralların günlük vekilleri
(C3b RSI2 < 10 → ilk yükselen kapanış ≤ 5 g; K1 V1 → ertesi kapanış; ES K1 → ertesi seans açılış–kapanış) için tutuşu OPEX Perşembe'si
veya Cuma'sını içeren işlemler ("pencere içi") − diğerleri. Setler: C3b QQQ 1999+, C3b ^NDX 1985–1999 (yalnız kapanış), K1 QQQ, K1 SPY,
ES QQQ. Veto geçer: pencere içi ortalama < dışı en az 4/5 sette ve havuz P(fark < 0) ≥ 0,95 → B (veto kapısı); 3/5 ve P ≥ 0,90 → C+.

## EK-3 (2026-11-18) — EK-2 düzeltmesi (sızıntı) + gerçek gün içi K1
EK-2'de C3b için "tutuş OPEX Perşembe/Cuma içeriyor" etiketi **çıkışa bağlı** (kaybeden işlem 5 güne kadar kalır, pencereye daha sık
düşer) → sızıntılı. Düzeltme: C3b için etiket yalnız **giriş günü** OPEX Çarşamba'sı veya Perşembe'si (ex-ante). K1/ES sabit 1 gün
tutuşlu olduğundan etkilenmez. Ek doğrulama: canlı K1 tanımı (`gn.nts`, 16:00 → ertesi 16:00) Duka NDX, MT5 NAS100 M30, US500, US30,
US2000; pencere içi = ertesi gün OPEX Perşembe'si veya Cuma'sı. Geçme: düzeltilmiş C3b QQQ ve ^NDX 1985–99 eksi, gün içi K1'de
5 beslemenin ≥ 4'ünde eksi ve havuz P ≥ 0,95.

## EK-4 (2026-11-18) — haftanın günü kontrolü + kapının genişlemesi
(a) Kontrol: OPEX haftası Çar/Per girişleri vs **OPEX dışı haftaların Çar/Per girişleri** (C3b QQQ ex-ante, K1 QQQ/SPY günlük, K1 gün içi
5 besleme). Geçme: fark < 0 setlerin ≥ 4/5'inde (yoksa etki gün etkisidir → X).
(b) Vade sonrası doz: OPEX Cuma'sı girişleri (tutuş vade sonrasında) vs diğerleri (bilgi; ≥ 0 beklenir).
(c) Genişleme: KSG vekili (QQQ kapanış → ertesi açılış, her gece) ve gerçek KSG (Duka/MT5 16:00 → 09:30): OPEX Çar/Per geceleri vs diğer
Çar/Per geceleri. Geçme (ayrı kapı sayılmaz, aynı kapının kapsamı): fark < 0, P ≥ 0,90 iki beslemede.

## EK-5 (2026-11-18) — kart ölçütleri + vade sonrası doz
Kapı 1 (veto) kartı: vetolanacak işlemler = OPEX haftası Çar/Per/Cum girişli C3b/K1/ES; ölçütler (1) ≥ 150 vetolanan işlem (havuz),
(2) vetolanan işlemlerin ortalaması < 0 ve bootstrap P(EV < 0) ≥ 0,90, (3) kronolojik iki yarıda ikisi de < 0, (4) spread ×1,5'te veto
yine kazançlı (vetolananlar daha da eksi), (5) gerçek icra: gün içi K1 (gerçek spread) ile günlük vekil aynı yönde, (6) veto yalnız
işlem siler (tek pozisyon kısıtını bozmaz). Doz adayı (Kapı 2'ye aday, ayrı ölçülür): **vade sonrası Pazartesi/Salı girişleri** vs
diğer haftaların Pazartesi/Salı girişleri; geçme setlerin ≥ 4/5'inde fark > 0 ve havuz P ≥ 0,95.

## EK-6 (2026-11-18) — OPEX penceresi canlı 8 kural kitabında + haftalık vade doğal deneyi
(a) `ndx_10y_1m_20261116/results/a_trades.parquet` (canlı kuralların Duka 1m 2018–26 dondurulmuş yeniden sınaması; daha önce OPEX'e
bakılmadı). Her kural için OPEX haftası Çar/Per/Cum girişleri vs diğer haftaların Çar/Per/Cum girişleri (birim kuralın kendi birimi:
bp ya da R). Ön kayıtlı öngörü: dönüş kuralları (C3B, C3, CAPREV, ÇEKİÇ) eksi; **ORB×VIX kırılımı da eksi** (vade yakını "pinleme"
kırılımı söndürür); KSG/AYSONU/FOMC etkisiz. Bir kural için kapı geçer: fark < 0, P ≥ 0,90 ve ESKİ (2018–21) / YENİ iki yarıda < 0.
(b) Haftalık vade doğal deneyi (**Kapı 2 adayı**): haftalık SPX/QQQ opsiyonları 2005'te başladı. K1/C3b günlük vekilleri, OPEX dışı haftalarda
**Perşembe** girişleri (tutuş haftalık vade Cuma'sı) vs Pazartesi–Çarşamba girişleri. Öngörü: 2005-01 → 2022-10'da fark < 0, 1993–2004'te
fark ≈ 0 ya da > 0; 2022-11 sonrası (her gün vade) gün özgüllüğü kaybolur (bilgi). Geçme: 2005–2022 fark < 0 P ≥ 0,95 QQQ ve SPY'de,
1993–2004 farkı bundan büyük (fark-farkı P ≥ 0,90).

## EK-7 (2026-11-18) — ORB×VIX OPEX vetosu bağımsız beslemede
EK-6'da ORB×VIX (uzun kol) OPEX Çar/Per/Cum girişleri −0,30R (P 0,976), ESKİ ve YENİ ikisi eksi. Bağımsız besleme: kuralın genel bar
sürümü (OR 09:30–09:45, kapanış OR tepesi üstü → sonraki bar açılışı + spread, SL OR ortası, TP 2R, 15:55 zaman çıkışı, aynı barda iki
seviye → SL) NQ 5m 2019-08 → 2024-08 ve MT5 NAS100 M15 2022-08 → 2026-11; sağlama: aynı genel sürüm Duka 5m'de canlı kural sonucunu
yeniden üretmeli (aynı işaret). Geçme: iki bağımsız beslemede fark < 0 ve havuz P ≥ 0,90 → ORB×VIX OPEX vetosu B.
