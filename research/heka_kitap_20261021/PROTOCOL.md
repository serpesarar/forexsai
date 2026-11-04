# HEKA kitabı → kapı/strateji adayları — ön kayıt (2026-10-21)

Kaynak: "NEXT LEVEL TRADING — HEKATRADER" (Hüseyin Kıral, 123 sayfa, genel TA ders kitabı; yazara göre %30'u
yapay zekâ ile yazılmış). Kitapta parametreli kural az; çoğu fikir `docs/KAPI_KAYIT_DEFTERI.md`'de zaten sınanmış:

| Kitap fikri | Defterdeki karşılığı | Karar |
|---|---|---|
| 10 mum deseni, pin bar, engulfing, doji, morning star, three soldiers… | MK-01, MK-02, MK-05 (X) | tekrar YOK |
| Grafik/harmonik formasyonlar (OBO, çift dip, bayrak, Gartley, Bat…) | formasyon SELL %22,6 (PATTERN_BONUS_GATE), PM/PM-2 (X) | tekrar YOK |
| MACD kesişimi | OLD-12 (X) | tekrar YOK |
| Bollinger sıkışma kırılımı | MK-07 R4 (C/X) | tekrar YOK |
| Kırılım sonrası retest girişi / kapanış teyidiyle bayrak girişi | fakeout lab: retest-tut −0,10R, sonraki-bar teyidi −0,07R | tekrar YOK |
| Trailing stop / BE | M9, OLD-15 (X) | tekrar YOK |
| Psikolojik (yuvarlak) seviye | GF-02 H8 (X) | tekrar YOK |
| Hacimli kırılım daha güvenilir | GF-14 T3 (C+), IO-03 (X) | tekrar YOK |
| CVD tükenme/emilim | gerçek emir akışı (bid/ask delta) verimiz YOK; tick hacmi vekili delta değildir | sınanamaz |
| **3 EMA (10/25/50) kesişim stratejisi** | yok (yalnız EMA50 hizası B4/K9) | **HK-1** |
| **Açık artırma teorisi: değer alanı dışı açılış → değer alanına dönüş → karşı kenara sürüklenme** | yok (POC/VAH/VAL yalnız bağlam, price_projection) | **HK-2** |
| **"S/R ne kadar çok test edilirse kırılma olasılığı o kadar yüksek"** | fakeout madencisinde `touches` özelliği var, tek başına sınanmadı | **HK-3** |
| **RSI Sınıf A diverjansı (giriş olarak)** | IO-05 yalnız *veto* olarak (C aday) | **HK-4** |

## Veri (hepsi UTC, bar başı damgalı; `src=="yahoo"` atılır — E21)
NDX 1h 2016-05→2026-07, NDX 30m 2021-07→2026-07 (`research/ndx_gate_forge/data`, +60 dk onarımlı);
DAX 1h 2019+ (öncesi seyrek), DAX 30m 2021-03→2026-10; XAU/OIL broker 1h 2016-05→2026-09, 30m 2021-07→2026-09
(`research/pinbar_20261010/data`).
**Dönem:** GELİŞTİRME < 2024-01-01 ≤ SINAMA. Hiçbir parametre sonuca göre ayarlanmayacak; iki dönem de raporlanır.

## Ortak icra kuralları
- Karar yalnız KAPANMIŞ barlarla; giriş = karar barından sonraki barın AÇILIŞI (E7).
- Maliyet: tam spread her işlemde düşülür: NDX 1,3 · DAX 1,5 puan · XAU 0,12 $ · OIL 0,028 $. Stres: ×1,5.
- Aynı barda TP ve SL → SL (kötümser). Çıkış/sonuç yalnız giriş barı ve sonrası high/low ile (giriş barı dahil: açılışta girildi).
- R = (çıkış − giriş)·yön − spread, SL mesafesine bölünür. ATR = ATR14 (aynı TF, karar barı dahil).
- Hafta sonu / veri boşluğu (> 3× TF) pozisyonu o boşluktan önceki son barın kapanışında kapatır.
- Bağımsızlık: aynı sembol+yönde açık pozisyon varken yeni sinyal alınmaz (tek pozisyon/sembol/yön).

## Kontroller (her hipotez)
- **P1 plasebo:** aynı sembol, yön, yıl, UTC saati (HK-2'de NY saati) eşli rastgele girişler, AYNI çıkış kuralıyla
  (stop/TP mesafeleri ATR biriminde aynı; çıkış kuralı fiyat-yoluna bağlıysa süre-eşli). Her sinyal için 20 plasebo.
- Fark = ortR(kural) − ortR(P1). Gün-blok bootstrap (2.000) ile P(fark>0).
- HK-4'te ek yapısal kontrol: aynı "daha düşük pivot dibi" yapısı ama RSI diverjansı YOK (RSI katkısını yalıtır).

## Hipotezler ve hücreler

### HK-1 — 3 EMA (10/25/50) dizilim kesişimi
Sinyal: 10>25>50 dizilimi bu barda oluştu (önceki barda yoktu) → BUY; 10<25<50 oluştu → SELL.
TF {30m, 1h} × 4 sembol × 2 yön × 3 çıkış:
- **X1 kitap çıkışı:** EMA10 EMA25'i ters kesince bar kapanışında çık (sonraki açılış); koruma SL 2×ATR.
- **X2 kitap R:Ö 1:2:** SL 1,5×ATR, TP 3×ATR, en çok 60 bar.
- **X3 zaman:** 20 bar tut, felaket SL 3×ATR.
Kitap öngörüsü: pozitif beklenti (trend takibi). Defter öngörüsü (§3/2): BUY > SELL.

### HK-2 — Değer alanı dönüşü (Dalton/AMT "%80 kuralı")
Önceki seansın 30m TPO profili (her barın aralığı fiyat kovalarına eşit dağıtılır; kova = 0,02×önceki seans aralığı),
POC etrafında TPO'nun %70'i = değer alanı [VAL, VAH]. Seanslar (yerel saat, DST doğru): NDX NY 09:30–16:00,
DAX Berlin 09:00–17:30, XAU NY 08:30–13:30, OIL NY 09:00–14:30.
Sinyal: seansın ilk 30m barının AÇILIŞI VA dışında (VAH üstü → SELL adayı, VAL altı → BUY adayı) ve seans içinde
ardışık İKİ 30m kapanış VA içinde → sonraki bar açılışında VA'nın karşı kenarına doğru gir. Seansta en çok 1 işlem;
seans bitimine < 60 dk kalmışsa alma.
TP = karşı VA kenarı; SL = seansın o ana kadarki dış ucu (SELL'de seans tepesi) + 0,1×ATR, en az 0,5×ATR(30m);
seans kapanışında kapat. Ayrıca "karşı kenara ulaşma oranı" raporlanır (iddia: %80).
4 sembol × 2 yön = 8 hücre (yalnız 30m).

### HK-3 — Dokunuş sayısı → kırılım
Seviyeler: fraktal pivotlar (w=3, pivot ancak 3 bar sonra bilinir), 0,5×ATR içinde kümelenir; dokunuş = kümeye düşen
pivot sayısı; seviye son 300 barda doğmuş olmalı. Kırılım olayı: kapanış seviyeyi ≥0,1×ATR aşar, önceki kapanış
öbür taraftaydı, seviye ≥2 dokunuşlu; aynı seviyede 12 bar soğuma.
(a) **Kırılım-yönlü işlem:** sonraki açılışta kırılım yönünde gir, ±1×ATR yarışı (SL=TP=1×ATR), en çok 24 bar.
(b) **Yaklaşma→kırılım olasılığı:** fiyat seviyeye 0,3×ATR yaklaştığında sonraki 12 barda kırılım olur mu.
Kovalar: dokunuş {2, 3, ≥4}. Kitap öngörüsü: dokunuş arttıkça (b) artar ve (a) iyileşir.
TF {30m, 1h} × 4 sembol.

### HK-4 — RSI Sınıf A diverjansı
Pivot dipler (w=3; teyit i+3). Boğa Sınıf A: yeni pivot dip fiyatı < önceki pivot dip (5–60 bar önce) VE RSI14(yeni) ≥
RSI14(önceki)+2. Değişke V2: ek olarak önceki dipte RSI<30. Ayı aynası tepelerde (V2: önceki tepede RSI>70).
Giriş teyit barı kapanışından sonraki açılış. Çıkış {X2: SL 1,5×ATR / TP 3×ATR / 60 bar, X3: 20 bar + felaket 3×ATR}.
TF {30m, 1h} × 4 sembol × 2 yön × 2 değişke × 2 çıkış. Defter öngörüsü: boğa diverjansı ayıdan iyi ("korku döner").

## Geçme ölçütü (önceden; sonuçtan sonra değiştirilmez)
Birincil hücreler = sembollerin HAVUZU (HK-1: TF×yön×çıkış = 12; HK-2: yön = 2; HK-3a: TF×kova = 6 (kova 2 tabana karşı
≥4 farkı); HK-4: TF×yön×değişke×çıkış = 16) → toplam 36 birincil sınama, **Holm** (tek yönlü bootstrap p).
Bir hücre **ADAY (gölge)** sayılır ancak HEPSİ tutarsa:
1. Holm sonrası anlamlı (α=0,05) fark > 0 (P1'e karşı; HK-3a'da kova ≥4 − kova 2; HK-4'te ek olarak yapısal kontrole karşı fark > 0),
2. Geliştirme VE sınama döneminde fark > 0,
3. 4 sembolün ≥3'ünde fark > 0,
4. Mutlak ortR spread×1,5'te > 0,
5. ≥150 bağımsız işlem (havuz),
6. En iyi 5 gün çıkarılınca ortR > 0.
Hiçbir hücre geçmezse sonuç "kitaptan kapı çıkmadı" olarak deftere yazılır. Geçen hücre canlıya değil, yalnız
2. KURAL kartına ve gölgeye aday olur.

## EK-1 (2026-10-21, ana sonuçlar görüldükten SONRA, ileri veri görülmeden ÖNCE yazıldı)
Ana tur: 36 birincil hücrenin hiçbiri geçmedi. Tek sınır hücre **HK-1 30m BUY X1** (fark +0,096, p 0,002 > Holm eşiği
0,0014; diğer 5 ölçüt geçti). Sonradan eklenen kontrol (`hk1_x1_check.py`): aynı çıkışla rastgele giriş (C1) farkı
değiştirmiyor; zaten dizilim içindeki rastgele barlardan girişe (C2) karşı fark +0,061 (P 0,95) → kesişim anının katkısı
yaklaşık yarısı, kalanı "yükselen dizilimde ol + trend çıkışı".
**İleri sınama (tek, bağlayıcı):** broker `indicator_snapshots` 15m (lag kuralıyla UTC'ye düzeltilmiş) → 30m'e
yeniden örneklenir; kural AYNEN (EMA 10/25/50 BUY dizilimi oluştu, sonraki açılış, X1 çıkış + 2×ATR koruma, spread aynı).
Yalnız giriş zamanı ana veri setinin bittiği andan SONRA olan işlemler sayılır (NDX >07-14, XAU/OIL >09-02, DAX >10-02).
Geçme: havuz ortR > 0 VE plaseboya farkı > 0 VE ≥3/4 sembolde (n≥5 olanlar) fark ≥ 0. Geçmezse X (kitaptan kapı yok).
Geçerse yalnız GÖLGE adayı (n küçük; kart değil). SELL ve 1h yalnız betimsel raporlanır.
