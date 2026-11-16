# 1m mum anatomisi — gözle keşif → algoritma (ÖN KAYIT, 2026-11-17)

Kullanıcı: "1 dakikalık grafiği kafanda grafiğe dönüştür, gözle incele; kapanış yeri, fitiller, mum şekilleriyle bir algoritmanın
yakalayabileceği yeni bir yapı keşfet." Veri: `research/nom_20261113/data/ndx_1m_v3_duka.parquet` (Dukascopy BID 1m 2018-01→2026-11),
motor `research/ndx_10y_1m_20261116/src/lib.py` (maliyet: ask = BID + spr, aynı bar stop+TP → stop).

## 0. Defterden ön bilgi (tekrar etmemek için)
YL-03/04: 1m "her an yön" bilgisi ≈ 0,3–0,6 puan, maliyet 3,4–5,4 puan → **genel gün içi yön kuralı beklenmez**. M19 (tek büyük 1m gövde devamı),
FR-01…18 (1h/4h fitil), ME/GC/PN (desen/gösterge eşleştirme) X. Bu nedenle 1m anatomisi iki yerde aranır:
(i) maliyetin zaten ödendiği kanıtlı bir kenarın içinde (ORB × VIX tetik anı) — süzgeç/doz olarak; (ii) seyrek ve büyük olaylarda
(çok mumlu itki bacağı, aşırı fitil) — hareket büyüklüğü maliyeti aşabilir mi?

## 1. Gözle inceleme (charts/, `src/draw.py`) — görülenler
2020-03-12, 2023-07-18, 2024-08-05, 2019-05-13 tam seans; ORB × VIX en iyi/en kötü sabahları 2026-04-02 (+3,3R), 2022-05-26 (+3,0R),
2024-10-24 (−1R), 2018-02-28 (−1R). Gözlemler:
- G1 **İtki bacağı**: art arda aynı renk, ucuna yakın kapanan (CLV ≥ 0,7), karşı fitili kısa 1m mumlar. Sıkışmadan çıkan bacak (2023-07-18 11:35)
  kazancını korudu; uzamış hareketin ucundaki bacak (2020-03-12 13:00, 2024-08-05 12:30) geri verildi.
- G2 **Temiz vs dağınık kırılım (ORB)**: kazanan sabahlarda kırılım öncesi mumlar tepesine yakın kapanıyor, renk değişimi az, üst fitil kısa;
  kaybedenlerde renkler sürekli değişiyor, iki yönlü uzun fitiller, kırılım denemesi uzun üst fitille reddediliyor.
- G3 **Uçta ret fitili**: hareketin ucunda tek büyük fitilli mum ve onu yutan karşı renk mum (2020-03-12 13:05).

## 2. Hipotezler ve ölçüler (sonuçlara bakmadan)
### P1 — ORB × VIX içinde kırılım anatomisi (TP 3R canlı geometri; giriş anına kadar kapanmış 1m barlar)
- f_clv: 09:30 → giriş arası 1m barların ortalama kapanış konumu (c−l)/(h−l). Öngörü: yüksek iyi.
- f_uw5: girişten önceki son 5 1m barda üst fitil toplamı / aralık toplamı. Öngörü: düşük iyi.
- f_flip: 09:30 → giriş arası ardışık barlarda renk değişim oranı. Öngörü: düşük iyi.
- f_run: girişe biten ardışık yeşil 1m bar sayısı. Öngörü yok (iki yön de raporlanır).
Bölme: KEŞİF = 2021-11 → 2026-11 (YENİ, 400 işlem), TEST = 2018-01 → 2021-10 (ESKİ, 341 işlem; bu ayrımda hiç bakılmadı).
Tertil eşikleri KEŞİF'te sabitlenir. Seçim: KEŞİF'te öngörü yönünde (iyi tertil − kötü tertil) en büyük fark; maxT permütasyonu (1.000) ile
dört özellik üzerinden düzeltilmiş p. Geçer: seçilen özellik TEST'te aynı yönde ∧ fark P ≥ 0,90 ∧ kitap düzeyinde doz (iyi ×1,5 / kötü ×0,5,
ortalama sabit) iki dönemde aylık Sharpe'ı artırır (E110).
### P2 — İtki bacağı (G1), tüm RTH 09:45–15:30
Olay: k ≥ 4 ardışık aynı renk 1m bar, her biri CLV ≥ 0,7 (yeşil) / ≤ 0,3 (kırmızı), bacak hareketi |c_son − o_ilk| ≥ 4 × a60
(a60 = önceki 60 barın ortalama aralığı). Bağlam: s30 = bacaktan önceki 30 barın (max h − min l) / a60. Tertiller KEŞİF'te.
- P2a sıkışma (s30 alt tertil) → bacak YÖNÜNDE gir; P2b uzama (s30 üst tertil) → bacağın TERSİNE gir.
Giriş: bacaktan sonraki barın açılışı (ask/bid), çıkış 30 dk sonra; çakışan olay yok (pozisyon açıkken yeni olay atlanır). Ölçü net bp.
### P3 — 1m aşırı fitil reddi (G3), RTH 09:45–15:30
Olay: tek 1m barda fitil ≥ 6 × a60 ve fitil/aralık ≥ 0,6 → fitilin TERSİ yönünde (üst fitil → SAT, alt → AL), sonraki bar açılışı, 30 dk.
Dönemler (P2, P3): KEŞİF 2022-01 → 2023-12, TEST 2024-01 → 2026-11, BAĞIMSIZ 2018-01 → 2021-12. Geçer: üç dönemde net ort > 0 ∧
TEST ve BAĞIMSIZ'da P ≥ 0,90 ∧ spr×1,5 > 0 ∧ aynı saatte rastgele giriş plasebosundan iyi.

## 3. Tuzak kontrolü
E1/E16 sızıntı: özellikler yalnız giriş anından önce kapanmış barlardan (önek testi). E58: aynı bar stop+TP → stop. E109: olay barı kapanınca
tek ve belli emir. E105: P3 seviye değil, bar olayı. E110: doz iddiası aylık Sharpe ile. E23: NDX'e çok bakıldı → TEST ve BAĞIMSIZ birlikte geçmeli.

## EK-1 (2026-11-17, P1/P2/P3 sonuçları görüldükten SONRA; aşağıdakiler koşulmadan önce yazıldı) — en fazla C+/B−
P1'de ön kayıtlı seçim geçmedi, ama öngörüsüz ölçülen f_run (girişe biten ardışık yeşil 1m) ve ters yönde f_uw5 (son 5 barda üst fitil
payı YÜKSEK iyi) iki dönemde aynı yönde. Sorular:
- EK1-a **Kitap dozu (E110):** canlı kitap (ORB TP 3R) aylık Sharpe'ı, ORB lotu (i) f_run ≥ 3 → ×1,5, aksi ×0,5 normalize; (ii) f_uw5 > KEŞİF üst
  tertil eşiği (0,2525) → ×1,5, aksi normalize; (iii) ikisinden biri → ×1,5. Geçer: iki dönemde Sharpe artar ∧ birleşik P ≥ 0,90.
- EK1-b **Mekanizma (bilgi):** "yoklama sayısı" = 09:30–giriş arası OR tepesine değen (h ≥ OR_hi) 1m bar sayısı; f_uw5 ile ilişkisi ve R'ye etkisi.
  Öngörü: yüksek üst fitil = OR tepesinin daha önce yoklanmış olması ("ikinci deneme kırılımı").
- EK1-c **Veto değil eleme sınaması:** f_run ≤ 1 ∧ f_uw5 ≤ alt tertil (0,1815) olan "en kötü hücre" ORB işlemleri iki dönemde de < 0 mı?

## EK-2 (2026-11-17, koşulmadan önce) — 1m anatomisinin GÜNLÜK izi, gece/ertesi gün ufkunda
Gerekçe: 30 dk ufukta 1m yapılarının bilgisi maliyetin altında (AN-05). Aynı anatomi gün boyunca toplanınca günlük mumda (OHLC/IBS)
görünmeyen bir iz bırakır: fiyatın gün içinde nerede "kabul gördüğü". Ufuk gece/ertesi gün olunca hareket ≫ maliyet (≈ 1 bp).
Her tam RTH günü için (09:30–16:00 1m barları, yalnız o gün 16:00'dan önce kapanmış barlar):
- W_gun = (Σ alt fitil − Σ üst fitil) / Σ aralık — alt fitil baskınlığı = gün boyu alıcı emilimi. Öngörü: yüksek W → gece/ertesi gün yukarı.
- CLV_gun = 1m barların ortalama kapanış konumu. Öngörü: düşük (satış baskısı) → dönüş yukarı ("korku döner") — iki yön de raporlanır.
- W_son = aynı ölçü yalnız 15:00–16:00 (KSG penceresi).
Hedefler: GECE = 16:00 açılışı (ask) → ertesi işlem günü 09:30 (bid), finansmanlı net bp; GUN = 16:00 → ertesi 16:00 net bp.
Kontroller: günün getirisi r_gun (açılış→16:00) ve günlük IBS (kapanışın günlük aralıktaki yeri). Kısmi etki = OLS hedef ~ özellik(z) + r_gun(z) + IBS(z),
dönem içi. Kural: W_gun KEŞİF üst tertilinde ise 16:00 AL → ertesi 09:30 (Q1); 16:00 → ertesi 16:00 (Q2).
Dönemler KEŞİF 2022–23 / TEST 2024–26 / BAĞIMSIZ 2018–21. Geçer: (a) kural net > 0 üç dönemde, TEST ve BAĞIMSIZ P ≥ 0,90; (b) üst tertil −
alt tertil > 0 üç dönemde; (c) kısmi OLS katsayısı üç dönemde aynı işaret ve havuz t ≥ 2. Hepsi geçerse kart + kitap katkısı.

## EK-3 (2026-11-17, koşulmadan önce) — 1m getiri dağılımının şekli (günlük mumda olmayan bilgi)
EK-2'de 1m izi günlük getiri/IBS'nin kopyası çıktı. Günlük OHLC'den hesaplanamayan iki ölçü:
- RSK = gerçekleşen çarpıklık (RTH 1m log getirileri, Amaya vd. 2015): √N·Σr³ / (Σr²)^1,5; 5 günlük ort. RSK5. Öngörü: en eksi tertil
  (çöküş benzeri gün içi yol) → ileri getiri yukarı.
- JMP = sıçrama payı = max(0, 1 − BV/RV), BV = (π/2)·Σ|r_t||r_{t−1}|. Öngörü yok, iki yön raporlanır.
Hedefler: GUN (16:00 → ertesi 16:00), HAFTA (16:00 → 5. işlem günü 16:00), finansmanlı net bp. Kontroller: r_gun, r5 (5 günlük getiri), IBS, log RV.
Kural: RSK5 KEŞİF alt tertili → 16:00 AL, HAFTA çıkış (tek pozisyon, örtüşme yok). Geçer ölçütleri EK-2 ile aynı (üç dönem net > 0, TEST/BAĞIMSIZ
P ≥ 0,90, uç fark > 0 üç dönemde, kısmi OLS aynı işaret ve havuz |t| ≥ 2).

## EK-4 (2026-11-17, koşulmadan önce) — TESLİMİYET MUMU: korku rejiminde 1m ret fitili, uzun ufuk
Gerekçe: 1m anatomisi tek başına maliyeti aşmıyor; defterin tek sağlam mekanizması "korku döner" (§3-2, C3b/CAPREV/ORB×VIX). Birleşim:
korku günü gün içi sert düşüşte gelen uzun alt fitilli, üst yarıda kapanan 1m mum = satıcı tükenmesinin mum izi. Ufuk seans sonu / ertesi gün.
Kural T (dondurulmuş):
- Gün şartı: dünkü VIX ≥ 18,4; tam RTH günü.
- An şartı (10:00 ≤ bar ≤ 15:00 ET): o ana kadar kapanmış barlarla gün içi düşüş (açılıştan bar kapanışına) ≤ −1 × dvol20 (CAPREV dvol'u).
- Mum şartı: alt fitil ≥ 3 × a60 ∧ alt fitil / aralık ≥ 0,5 ∧ kapanış konumu ≥ 0,5.
- Giriş: sonraki bar açılışı (ask), günde ≤ 1. Çıkış T0 = aynı gün 15:55; T1 = ertesi işlem günü 16:00. Stop yok (zaman çıkışı; acil stop ayrıca raporlanır).
Kontrol K: aynı gün ve an şartını ilk karşılayan dakika (mum şartı yok) → aynı giriş/çıkış. Fitilin katkısı = T − K.
Dönemler KEŞİF 2022–23 / TEST 2024–26 / BAĞIMSIZ 2018–21. Geçer: T net > 0 üç dönemde ∧ TEST ve BAĞIMSIZ P ≥ 0,90 ∧ T > K üç dönemde ∧
spr×1,5 > 0. Geçerse: 2. KURAL kartı + mevcut kitaba katkı (aylık Sharpe, E110).

## EK-4b (2026-11-17) — eşik düzeltmesi, getiriye BAKILMADAN
EK-4'teki "alt fitil ≥ 3 × a60" 9 yılda 0 olay üretti (sınanamaz). Eşik yalnız olay SIKLIĞIYLA seçildi (getiri hesaplanmadan): 183 korku-düşüş
gününde olay oranı 0,5× %78 · 0,75× %64 · 1,0× %28 · 1,5× %3 · 2,0× %0. Kural: günlerin ≥ %50'sinde olay veren en sıkı eşik → **0,75 × a60**.
Diğer her şey EK-4 ile aynı; geçme ölçütleri değişmedi.

## EK-5 (2026-11-17, koşulmadan önce) — S4 × sabah 1m anatomisi ("alıcı kabulü")
S4 (ndx_10y_1m_20261116 EK-2: dünkü VIX ≥ 18,4 ∧ 12:00 > 09:30 açılışı → 12:00 AL, 15:55) tek başına kart 6/6 ama kitaba eklenince Sharpe artmadı.
Soru: 09:30–12:00 1m anatomisi S4'ün güçlü alt kümesini ayırır mı?
- A_clv = 09:30–11:59 1m barların ortalama kapanış konumu; A_w = (Σ alt fitil − Σ üst fitil)/Σ aralık aynı pencerede.
- Öngörü: yüksek A_clv ve yüksek A_w (sabah boyunca alıcı kabulü) → öğleden sonra sürüklenme güçlü.
Tertiller KEŞİF (2022–23) S4 olaylarında. Kural S4+: S4 ∧ A_clv KEŞİF üst tertili. Geçer: S4+ net > 0 üç dönemde (KEŞİF/TEST/BAĞIMSIZ),
TEST ve BAĞIMSIZ P ≥ 0,90, S4+ > S4 alt tertil üç dönemde ∧ canlı kitaba (ORB 3R'li) 0,5 lot eklenince aylık Sharpe ESKİ ve YENİ'de artar.
A_w aynı biçimde ikinci (bağımsız) sınama olarak raporlanır; ikisi için Holm.
