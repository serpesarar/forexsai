# FB — "Altın bölge" Fibonacci geri çekilmesi + yutan mum (Instagram, AKN TRADE) — ÖN KAYIT

Tarih: 2026-11-16 · Yazıldı: sonuçlara bakılmadan, kod yazılmadan önce. Sonradan eklenen her şey `EK-n` başlığıyla.

Kullanıcı: "Stratejiyi analiz et, tüm backtestlerini yap; seans, saat, gün bazında ve farklı zaman dilimlerinde test et;
kârlı bir şey bulana kadar gelme." → Arama geniş yapılacak, ama hüküm seçim düzeltmeli (KEŞİF'te seç → TEST + KÖR + bağımsız
piyasada dondurulmuş sına). "Kârlı bir şey bulmak" ölçütü aşağıda (§6) önceden yazıldı; bulunamazsa bu da sonuçtur.

## 0. Videodaki kural (söylenen → tanım)

| Söylenen | Tanım (uzun; kısa = ayna) |
|---|---|
| "Güçlü hareket: büyük mumlarla tek seferde; yatay/kararsızsa geç" | İtki L→H: `S = (H−L)/ATR14(L anında) ≥ 4` ve `hız = S / (H_idx − L_idx) ≥ 0,5 ATR/bar` (≤ 8 barda 4 ATR) |
| "Fibonacci'yi dipten tepeye çek" | Seviye `f(x) = H − x·(H−L)` |
| "Altın bölge 0,5–0,618; buraya gelmeden girme" | Geri çekilme en az 0,5'e inmiş olmalı; dönüş mumu çifti bölgeye değmiş olmalı: `min(low[t−1], low[t]) ≤ f(0,5)` |
| "0,786 aşağı kırılırsa kurulum bozulur" | `min low (H, t] > f(0,786)` (fitil dahil, katı) |
| "Önceki mumu tamamen yutan büyük yeşil mum; mum kapanınca gir" | t yeşil, t−1 kırmızı, gövde yutma: `c[t] ≥ o[t−1] ∧ o[t] ≤ c[t−1]`; giriş t kapandıktan sonraki **ilk 1m açılışı + spread** (E7) |
| "Stop hareketin başladığı dibin altına" | `SL = L − 0,1·ATR14(t)` |
| "Hedef önceki tepe (cesursan biraz üstü)" | `TP = H` (birincil); 1,272 / 1,618 uzantı ızgarada |

İtki penceresi (gözle "son güçlü hareket"in nedensel karşılığı): `H_idx = argmax high[t−40 … t−1]`, `H_idx ≤ t−2` (en az bir
geri çekilme barı) ve `H_idx > t−40` (pencerenin kenarı değil); `L_idx = argmin low[H_idx−30 … H_idx]`. Yalnız t'ye kadar kapanmış
barlar kullanılır. Aynı (L_idx, H_idx) itkisi için **ilk** sinyal alınır. Daha yüksek yeni tepe → yeni itki (trader Fib'i yeniden çizer).
Zaman çıkışı: sinyal TF'inde 100 bar. TP'nin girişin altında kaldığı sinyal (giriş ≥ H) alınmaz.

## 1. Veri, maliyet, icra

- **NDX (ana):** Dukascopy USATECHIDXUSD BID 1m 2018-01-02 → 2026-11-13 (`research/nom_20261113/data/ndx_1m_v3_duka.parquet`),
  `spr` NY saatine göre spread modeli. Sinyal TF'leri 1m'den NY saatine hizalı kurulur: 1m, 5m, 15m, 30m, 1h, 4h (4h kovaları
  18/22/02/06/10/14 ET). Çıkış her TF'de **1m BID yolu** ile çözülür; uzunda ask = bid + spr. Aynı 1m barda SL ve TP → SL (E58).
  Bar açılışı SL'nin ötesindeyse (boşluk) açılıştan dolar.
- Dönemler: **KEŞİF 2018-01 → 2021-12**, **TEST 2022-01 → 2024-06**, **KÖR 2024-07 → 2026-11**.
- **Bağımsız piyasalar (dondurulmuş kural, yalnız sınama):** Pepperstone MT5 (`research/c1_turev_20261105/data/mt5/`, sunucu = NY + 7):
  GER40, XAUUSD, SpotCrude M15 (2022-08 →), M30 (2018-05 →), H1 (2018-05 →); US500 M30; NAS100 M15/M30/H1 yalnız **besleme
  kontrolü** (zamanca NDX ile örtüşür). Çözüm kendi TF barlarıyla (kaba yol, E104: aynı bar SL+TP → SL); giriş sonraki bar açılışı.
  Spread (puan): NAS100 1,3 · GER40 1,2 · US500 0,5 · XAUUSD 0,25 · SpotCrude 0,03.
- Finansman: tutulan her gece (17:00 ET devri) 1,76 bp × fiyat, iki yönde de (muhafazakâr).
- R = net getiri / (giriş − SL). Stres: spread × 1,5.

## 2. Birincil hipotez (videoya sadık, 12 hücre)

NDX × TF {1m, 5m, 15m, 30m, 1h, 4h} × {uzun (videonun anlattığı), kısa (ayna)}, §0 parametreleri. Holm 12 hücre üzerinde.

## 3. Kontroller (aynı motor)

- **K1 Yanlış bant (hayalet seviye, E105/E129):** bölge {0,236–0,382 / bozulma 0,5}, {0,382–0,5 / 0,618}, {0,618–0,786 / 1,0 (= L)}.
  Altın bölge özel ise birincilin bu bantlardan iyi olması gerekir.
- **K2 Teyitsiz:** yutan mum yok; bölgeye değen ilk bar kapanışından sonra gir (aynı SL/TP).
- **K3 İtkisiz:** S ≥ 1,5, hız ≥ 0 (her salınım) → "güçlü hareket" filtresinin katkısı.
- **K4 Zaman plasebosu:** her işlem için aynı TF, aynı yön, aynı NY saati ve yıl içinde rastgele bir bar kapanışında, **aynı braket**
  (SL ve TP mesafeleri işlemin ATR katı olarak) ile 5 çekiliş. Kural − plasebo farkı raporlanır.

## 4. Kırılımlar (her hücre için tablo)

Seans (ET; sinyal barının kapanışı): ASYA 18:00–02:59 · AVRUPA 03:00–09:29 · NY 09:30–15:59 · KAPANIŞ SONRASI 16:00–17:59;
saat (0–23 ET); haftanın günü (NY takvim günü); yıl; yön; R:R kovası; geri çekilme derinliği.

## 5. Keşif ızgarası (seçim KEŞİF'te, sınama TEST+KÖR+bağımsız)

TF 6 × yön 2 × S {3, 4, 6} × hız {0, 0,5, 1,0} × örüntü {gövde yutan, tam yutan (c[t] > h[t−1]), teyitsiz} × bölge {altın, sığ 0,382–0,5,
derin 0,618–0,786} × SL {L, f(0,786), yutan mumun dibi} (−0,1 ATR) × TP {H, 1,272, 1,618, 2R} × zaman çıkışı {100, 300 bar}
× filtre {tümü, tek seans (4), tek gün (5)}. Hücre KEŞİF'te n ≥ 60 ve gün-kümeli t ile sıralanır.
Seçim boşu: aynı ızgara K4 plasebo işlemleriyle (aynı sinyal sayısı) koşulur → plasebonun en yüksek t'si; gerçek tavan onu aşmıyorsa
seçim şans düzeyindedir (E141 notuyla). İlk 20 KEŞİF hücresi TEST ve KÖR'de raporlanır (kaç tanesi artı).

## 6. Hüküm ölçütü ("kârlı bir şey" tanımı — önceden)

Bir hücre/kural ancak hepsini geçerse **B (gölge adayı)**; NDX dışı bağımsız piyasada da tutarsa **A−**:
1. TEST ve KÖR'ün **ikisinde de** ort R > 0; KÖR'de gün-blok bootstrap P(EV>0) ≥ 0,90 (KÖR n ≥ 40).
2. spread × 1,5 ile TEST+KÖR ort R > 0.
3. Tek pozisyon kısıtıyla TEST+KÖR > 0.
4. K4 zaman plasebosundan iyi (TEST+KÖR fark > 0, P ≥ 0,90).
5. En büyük 5 işlem hariç TEST+KÖR ≥ 0 (§3-15).
6. Bağımsız piyasalar (dondurulmuş): en az 3/5 piyasada ort R > 0 ve havuz P ≥ 0,90 → A−.
Biri düşerse X (veya iz → C). Birincil hücreler için ayrıca: altın bölge K1 bantlarından ve K2 teyitsizden iyi mi (videonun iki iddiası).

## 7. Tuzak kontrolü (defter §1)

E1/E15/E16 sızıntı: önek testi (t sonrası barlar bozulunca t'nin sinyali değişmez) otomatik. E7/E97 icra: sonraki 1m açılışı + spread.
E58 1m çözüm: aynı bar → SL. E66/E105: giriş piyasa emriyle (limit yok). E111: yapı hedefli kural → isabet yerine ort R ve
**ortalama başabaş isabeti** birlikte raporlanır. E13/E73: uzun taraf NDX sürüklenmesine karşı K4 ile. E23: tek NDX geçmişi çok kez
görüldü → bağımsız piyasa şartı. E141: ızgara maxT gücü sınırlı → ilk 20'nin TEST/KÖR işaret oranı da raporlanır.
E90: geri çekilme derinliği tepeden ölçülür ama işlem fiyatı gerçek sonraki açılış; derinlik yalnız sınıflama.

---

# EK-1 — Aday dondurma + iki yeni açı (2026-11-16; birincil ve ızgara sonuçlarından SONRA, bağımsız sınamalardan ÖNCE)

Durum: birincil 12 hücre X (Holm en iyi p 0,47); ızgara gerçek t tavanı 3,49 < plasebo 3,98, t>2 hücre 322 vs plasebo 360 →
seçim şans düzeyinde. Üç dönemde de artı ve plasebodan iyi hücreler UZUN · NY seansı · 15m/5m · hedef H ötesinde kümeleniyor
(üç dönem min-t tavanı 1,26 vs plasebo 1,23). Bu hücreler TEST/KÖR'ü görerek seçildi → NDX'te artık kör değiller; **tek kör sınav
bağımsız piyasa**.

## A. Dondurulan adaylar (parametre değişmez)
| Kod | TF | Yön | Örüntü | Bölge (a / bozulma) | İtki | SL | TP | Tutuş | Filtre |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 5m | UZUN | teyitsiz (bölgeye değen bar) | 0,382 / 0,618 | S≥6, hız≥0 | L | 1,618 uzantı | 300 bar | NY 09:30–16:00 ET |
| C2 | 15m | UZUN | tam yutan | 0,618 / 1,0 | S≥3, hız≥0 | L | 1,272 uzantı | 300 bar | NY |
| C3 | 15m | UZUN | gövde yutan (video) | 0,5 / 0,786 (altın) | S≥3, hız≥0 | L | 2R | 100 bar | NY |
Bağımsız piyasalar: GER40, XAUUSD, SpotCrude, US500 (C1 → M5 2025-06→, US500 M5 yon_lab; C2/C3 → M15 2022-08→, US500 yalnız
M30). NAS100 broker yalnız besleme kontrolü. Geçer (A−): bağımsız 4 piyasanın ≥3'ünde ort R > 0 ve havuz gün-blok P ≥ 0,90;
ayrıca NDX'te §6.2–6.5. Biri düşerse X.

## B. Korku rejimi (meta-ders 2 "korku döner")
Birincil 12 hücre + C1–C3, dünkü VIX kapanışı ≥ 18,4 / < 18,4 ayrımı. Öngörü: UZUN, VIX ≥ 18,4'te daha iyi. Geçer: UZUN×yüksek-VIX
KEŞİF, TEST, KÖR üçünde ort R > 0, havuz P ≥ 0,90 ve plasebodan iyi. (Kısa için ayna öngörü yok, yalnız rapor.)

## C. Günlük grafik, çok endeks
Videonun kuralı (§0 parametreleri, K=40, M=30 bar) günlük barlarda; tutuş {20, 60} gün; iki yön; maliyet 3 bp gidiş-dönüş + 1,76 bp/gece;
giriş ertesi gün açılışı, çözüm günlük barla (aynı gün SL+TP → SL). Plasebo: aynı yıl rastgele gün, aynı braket. KEŞİF = IXIC + GSPC
≤ 2009 · TEST = ikisi 2010+ · KÖR = diğer 15 endeks (AEX, AXJO, BSESN, BVSP, DJI, FCHI, GSPTSE, IBEX, JKSE, KS11, MXX, RUT, SSMI,
TWII, GDAXI). Geçer: KEŞİF ve TEST > 0, KÖR'de ≥ %60 endekste > 0 ve havuz fark (kural − plasebo) P ≥ 0,90.

---

# EK-2 — C1'in doğası (2026-11-16; EK-1 sonuçlarından SONRA, aşağıdaki sınamalardan ÖNCE)

EK-1 hükmü: C1/C2/C3 bağımsız piyasa ölçütünü geçmedi (C1 2/4 artı, havuz +0,02R P 0,65; C2 0/4; C3 1/4) → A− yok. VIX (B) ve
günlük çok endeks (C) X. NDX'te 2018 öncesi gün içi veri yok → adaylar için NDX'te kör dönem kalmadı. Bu ek **hükmü değiştiremez**;
yalnız C1'in gölgeye değer olup olmadığını (C) ve kenarın Fibonacci'den mi geldiğini söyler.

1. **Plato:** C1 komşuları — örüntü {teyitsiz, gövde yutan} × bölge {0,236, 0,382, 0,5} × SL {L, bozulma} × TP {H, 1,272, 1,618, 2R} ×
   tutuş {100, 300} × S {4, 6}, hepsi 5m UZUN NY. C1 "platoda" sayılır: komşuların ≥ %70'i TEST ve KÖR'ün ikisinde de > 0.
2. **Fibonacci katkısı:** aynı itki tanımı (S ≥ 6, 5m, UZUN), itki ilk görülebildiği anda (H_idx + 2 kapanışı, NY) gir; SL L − 0,1 ATR,
   TP H + 0,618 (H−L), 300 bar. Geri çekilmesi olsun olmasın tüm itkiler. Fib katkısı = C1 − bu kontrol (her dönem). Kontrol C1 kadar
   iyiyse kenar "güçlü yükselişten sonra al" (momentum/coşku dönmez), Fibonacci değil.
3. **ABD endeksleri (bilgi, kurtarma değil):** US30, US2000 M5 2025-06→ donmuş C1.

---

# EK-3 — Aynı batarya DAX ve altında (2026-11-17; kullanıcı isteği "sırasıyla DAX ve altında, aynı başarıyı arayarak").
Bu ek DAX/XAU sonuçlarından ÖNCE yazıldı. NDX hükmü (X, iz C) değişmez; DAX ve XAU kendi keşif/test/kör dönemleriyle bağımsız sınanır.

**Veri:** Dukascopy 1m BID, DEUIDXEUR ve XAUUSD, 2018-01-01 → 2026-11-14 (`src/duka_pull.py`). Spread = NY saati başına
max(Dukascopy 2025 Çarşamba ask−bid medyanı, Pepperstone M1 medyanı) — NDX'in koruyucu modeliyle aynı (`results/<sym>/spread_modeli.csv`).
Finansman 1,76 bp/gece iki yönde (XAU için 2× finansmanla ayrıca raporlanır). Dönemler, seans kovaları (NY saati), TF'ler, K1–K4
kontrolleri, önek testi, Holm ve §6 geçme ölçütleri NDX ile birebir. Sıra: önce DAX tamamlanır, sonra XAU.

1. **Birincil:** videonun kuralı, 6 TF × 2 yön = 12 hücre, seans/saat/gün/yıl kırılımı (`results/<sym>/birincil*`).
2. **Izgara:** aynı 233.280 hücre + eşlenik zaman plasebosu; gerçek vs plasebo t tavanı, t>2 sayısı, aile ortalamaları.
3. **Aday dondurma (mekanik):** KEŞİF n ≥ 60, TEST ve KÖR n ≥ 30; üç dönemde de ort R > 0 ve üçünde de plasebodan iyi hücreler,
   üç dönemin en küçük t'sine göre sıralanır; (TF, örüntü) ailesi farklı ilk 3 hücre dondurulur. Böyle hücre yoksa aday yok → X.
   (Adaylar TEST/KÖR görülerek seçildiği için kendi piyasasında kör değildir; **tek kör sınav bağımsız piyasa**.)
4. **Bağımsız sınav:** DAX adayı → NDX Duka 2018-26, XAU Duka 2018-26, SpotCrude ve US500 broker (EK-1 ile aynı TF/dönem);
   XAU adayı → NDX Duka, DAX Duka, SpotCrude, US500. Aynı piyasanın broker beslemesi (GER40 / XAUUSD) yalnız besleme kontrolü.
   Geçer (A−): bağımsız 4 piyasanın ≥ 3'ünde ort R > 0 ve havuz gün-blok P ≥ 0,90; kendi piyasasında sp×1,5, tek pozisyon, en iyi 5
   hariç artı. Biri düşerse X.
5. **Fibonacci katkısı (E144):** her aday için aynı itki tanımı, itkinin ilk görülebildiği barda (H + 2 kapanışı) seviye beklemeden
   giriş, aynı SL/TP/tutuş/filtre. Fib katkısı = aday − kontrol; P(katkı > 0) ≥ 0,90 değilse kenar "Fib" sayılmaz.
6. **NDX adaylarının uzun bağımsız sınavı:** donmuş C1–C3, Duka DAX ve XAU 2018-26'da (EK-1'deki broker 2025-06→ yerine 8 yıl).
7. **VIX rejimi:** birincil 12 hücre, dünkü VIX ≥ 18,4 / < 18,4. Öngörü yalnız DAX UZUN için (korku döner); XAU yalnız rapor.

## EK-3b — DAX Avrupa ailesi için Avrupa endeksi sınavı (2026-11-17; DAX EK-3 sonuçlarından SONRA, CAC/Stoxx verisinden ÖNCE)
DAX EK-3: birincil 12 hücre X; ızgara gerçek t tavanı 2,74 < plasebo 3,25; üç dönem min-t tavanı 1,09 < plasebo 1,53. Donmuş DAX1
(15m UZUN, gövde yutan, altın bölge, SL bozulma, TP 1,272, 300 bar, AVRUPA seansı) kendi TK +0,17R ama plasebo +0,086, fark P 0,77;
bağımsız NDX −0,05, US500 −0,32 (bu piyasalarda AVRUPA = seans öncesi, doğal karşılık değil). Komşuluk (15m UZUN AVRUPA, 1.284 hücre)
TEST∧KÖR artı oranı %27 vs plasebo %16; yutan örüntülerde %45. Doğal bağımsız sınav: **aynı saat diliminde işlem gören Avrupa nakit
endeksleri.** Dukascopy FRAIDXEUR (CAC 40) ve EUSIDXEUR (Euro Stoxx 50), 1m 2018-01 → 2026-11, spread yalnız Duka 2025 ask−bid.
- Geçer (A−): donmuş DAX1 iki endeksin ikisinde de ort R > 0, havuz (kural − plasebo) gün-blok P ≥ 0,90 ve havuz ort R > 0.
- Aile (bilgi + B ölçütü): 15m UZUN AVRUPA × {eng, engf} komşularının TÜM-dönem ort R'sinin plasebodan iyi olma oranı ≥ %70 iki endekste de.
Biri düşerse DAX ailesi X kalır (en çok iz C).
