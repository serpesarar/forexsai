# XAU mekanik giriş kuralları — ÖN KAYIT (PROTOCOL)

**Yazıldı: 2026-10-15 00:45 EDT (Mac sistem saati; = 04:45 UTC).** Dukascopy verisinden HİÇBİR sonuç görülmeden,
indirme sürerken yazıldı. Bu dosya sonuçlardan sonra DEĞİŞTİRİLMEZ; sapma olursa §9'a tarihli ek yazılır.

## 0. Önceden bilinenler (dürüstlük beyanı)
- MK-03/04/05 (`research/pinbar_20261010/`) aynı fikir ailesini candle_cache 1h 2016-05→2026-09 üzerinde gördü:
  MK-04 "1h yeni 20-mum tepesi BUY, SL 1,5×ATR, 20 mum" +0,107R vs aynı stoplu rastgele BUY +0,042, icra ölçütü ✗.
- XAU günlük Donchian55+EMA200 BUY (+0,69R) ve H4 Donch30 + D1 uyum (2/4 ATR, 30 bar, +0,33R) — `xau_swing_research/`
  (xauusdegitim 2021-05→2026-04).
- Ölü fikirler (TEKRAR EDİLMEZ): M15 dip/bounce ve M15 breakout (OLD-07), 1m/5m scalp (OLD-01), mum formasyonları
  (MK-01/02/05), dipten-al / oversold (swing Stage 4), makro yön (OLD-10), fakeout işlemi (CK-02), BE/kilit (M9),
  gösterge-eşik kuralları (IO-12), her türlü XAU SELL (B1) — SELL burada YALNIZ kontrol.
- 2016-2026 dönemine bu proje en az 3 tur baktı (E23). **2008-01→2016-05 Dukascopy bu proje için hiç görülmemiş
  veridir** ve 2011-2015 altın ayı piyasasını içerir → en temiz bağımsız kanıt bu alt-dönemden gelir; ayrı raporlanır.

## 1. Veri
- Ana: Dukascopy XAUUSD H1 BID + ASK (UTC, bar başlangıç damgası), 2008-01-01 → 2026-06-16. Hacmi 0 olan (kapalı
  piyasa) barlar atılır. Fiyat = int/1000.
- Bağımsız son kasa (holdout): broker (Pepperstone) 1m BID UTC `../data/xau_1m_utc.csv.gz` 2026-06-17 → 10-14;
  H1/H4/D1 buradan türetilir, yol 1m çözünürlükte.
- Kalibrasyon: Duka H1 ↔ broker H1 (aynı saat) kapanış farkı ve saat ekseni hizası ölçülür (ofset 0 beklenir).
- Günlük (D1) ve H4 barlar H1'den **New York 17:00 gün sınırıyla** türetilir (forex/broker konvansiyonu);
  H4 sınırları NY 17/21/01/05/09/13. Bir karar anında yalnız KAPANMIŞ D1/H4 barı kullanılır.

## 2. Ortak tanımlar
- ATR = son 14 KAPANMIŞ barın TR ortalaması (aynı TF). D1 EMA200 / H4 EMA50: kapanmış barlardan.
- TREND_UP = son kapanmış D1 kapanışı > D1 EMA200.
- Sinyal H1 (veya H4) bar KAPANIŞINDA değerlendirilir; giriş = **sonraki barın açılışı** (= sonraki M1 açılışı) + spread.
- BUY: giriş = bid_open + spread; TP/SL bid high/low ile; aynı barda TP ve SL → **LOSS**; giriş barında SL/TP de
  geçerli (o barın high/low'u) ama aynı-bar kuralı uygulanır. Zaman çıkışı = son barın bid kapanışı.
- Hafta sonu/tatil: sonraki bar ile >3 saat boşluk varsa pozisyon boşluktan önceki son bar kapanışında kapanır.
- SELL (kontrol): giriş = bid_open; çıkış ask = bid + spread.
- R = (çıkış − giriş)/SL mesafesi (SL'siz geometri yok; her geometride SL var).
- Spread modelleri: **A = sabit $0,12** (karar modeli; canlı Pepperstone ölçümü), A×1,5 = $0,18 (ölçüt 4),
  B = Dukascopy'nin o saatteki gerçek ask−bid'i (bilgi amaçlı, tarihsel ECN maliyeti).
- Aynı kuralın 1 saatten sık tekrarlanan sinyalleri: kural tanımı gereği "ilk" tetik olanlar sayılır (aşağıda).

## 3. Kurallar (6 BUY kuralı × ≤3 geometri = 18 birincil test) + SELL aynaları (kontrol)
**R0 — MK-04 bağımsız replikasyonu (tanım aynen):** H1 high ≥ önceki 20 H1 barın en yükseği → BUY; filtre yok.
  G1: SL 1,5×ATR_H1, TP yok, 20 bar zaman çıkışı (MK-04'ün kendisi). G2: TP 1,0 / SL 1,0 ATR_H1, 12 bar.
  G3: TP 2,0 / SL 1,5 ATR_H1, 24 bar.
**R1 — H1 48-bar kapanış kırılımı + trend:** H1 close > önceki 48 H1 barın en yüksek high'ı VE TREND_UP VE son
  kapanmış H4 close > H4 EMA50. G1: TP 2,0 / SL 1,5 ATR_H1, 24 bar. G2: TP 1,0 / SL 1,0, 12 bar. G3: SL 1,5, TP yok, 8 bar.
**R2 — Londra Asya-aralığı kırılımı:** Asya aralığı = Londra yerel 00:00–06:59 H1 barlarının high'ı. Londra yerel
  07:00–11:59 arasında kapanışı Asya high'ının üstünde olan GÜNÜN İLK H1 barı → BUY; TREND_UP şart.
  G1: TP 1,5 / SL 1,0 ATR_H1, 8 bar. G2: TP 1,0 / SL 1,0, 8 bar. G3: SL 1,0, TP yok, NY 16:00 yerel saatine kadar tut.
**R3 — NY sabah gücü (gün-içi momentum):** NY yerel 10:00'da kapanan H1 barında (09:00–09:59 bar) kapanış > o işlem
  gününün açılışı (NY 17:00 önceki gün) VE kapanış > NY 08:00 bar açılışı; TREND_UP şart → BUY.
  G1: SL 1,5 ATR_H1, TP yok, NY 16:00'ya kadar. G2: TP 1,5 / SL 1,0, NY 16:00'ya kadar. G3: TP 1,0 / SL 1,0, NY 16:00.
**R4 — Oynaklık genişlemesi (sıkışma→kırılım):** önceki H1 barda Bollinger(20,2) bant genişliği/orta, son 120 barın
  en düşük %20'sinde VE bu H1 kapanışı üst bandın üstünde; TREND_UP şart → BUY (sıkışma epizodu başına ilk tetik:
  önceki 12 barda bu kural tetiklendiyse atla). G1: TP 2,0 / SL 1,5, 24 bar. G2: TP 1,0 / SL 1,0, 12 bar.
  G3: SL 1,5, TP yok, 12 bar.
**R5 — H4 20-bar kapanış kırılımı + D1 trend (gün ölçeği):** H4 close > önceki 20 H4 barın en yüksek high'ı VE
  TREND_UP → sonraki H4 açılışında BUY. G1: TP 2,0 / SL 1,5 ATR_H4, 6 H4 bar (1 gün). G2: TP 1,0 / SL 1,0 ATR_H4,
  6 bar. G3: SL 1,0 ATR_H4, TP yok, 6 bar.
**SELL aynaları (kontrol, verdikt yok):** her kuralın simetriği (low ≤ önceki N low / kapanış altı / Asya low kırılımı /
  NY zayıflık / alt band; TREND_DOWN = D1 close < EMA200), aynı geometriler.

## 4. Taban / plasebo (sürüklenme kontrolü)
- P1 (sürüklenme): her sinyal için **aynı takvim yılı + aynı UTC saati**nden rastgele bir H1 bar → aynı geometri, aynı
  çıkış kuralı (NY 16:00 gibi saat-çıkışları aynen). 200 tekrar. Kural, P1 ortalamasını geçmeli: fark > 0 ve kural
  ortalaması P1 dağılımının ≥ %95'inde.
- P2 (filtre-koşullu): P1 ile aynı ama rastgele bar da TREND_UP'ı (ve kuralın varsa saat penceresini) sağlar → tetiğin
  filtrenin ötesindeki katkısı. Bilgi amaçlı; ayrıca raporlanır.
- Seçim düzeltmesi (E24): 18 birincil hücre için her plasebo tekrarında "max(kural − plasebo-ort)" yerine, plasebo
  tekrarının kendi max(ortR) değeri hesaplanır; gerçek max hücrenin bu dağılımdaki yüzdeliği raporlanır. Ayrıca
  gün-kümeli t için Holm-Bonferroni (m=18, α=0,05 tek yönlü).

## 5. Canlıya alma kartı (2. KURAL) — her birincil hücre için, spread A ile
1 hacim ≥150 · 2 ortR>0 ve gün-blok bootstrap P(EV>0) ≥ %90 · 3 iki kronolojik yarı ≥0 · 4 spread ×1,5 > 0 ·
5 |iyimser (sinyal bar kapanışı, spread 0) − gerçek| ≤ 0,5×|gerçek ortR| · 6 tek pozisyon ortR > 0.
**Ek zorunlu ölçütler (bu araştırma için, kartın üstüne):** 7 P1 sürüklenme plasebosunu ≥ %95 yüzdelikle geç ·
8 2008–2015 (görülmemiş) alt-döneminde ortR > 0 · 9 Holm düzeltmesinden geç · 10 broker kasasında (2026-06→10)
ortR'nin işareti pozitif (n küçük olduğundan yalnız işaret).
- **LIVE**: 1–10 hepsi. **SHADOW**: kart 1–6'dan en fazla biri düşer VEYA kart geçer ama 7–10'dan biri düşer, ve
  ortR − P1 > 0. **RED**: ortR ≤ P1 (sürüklenmeyi geçemiyor) veya 2+ kart ölçütü düşer.

## 6. Yol çözünürlüğü
H1 barlarla çözülen yol aynı-bar=LOSS ile kötümser; aynı-bar=WIN (iyimser sınır) ile de koşulur. İkisi arasındaki
fark raporlanır; broker kasasında H1-yol ↔ 1m-yol farkı ölçülür.

## 7. Raporlanacak
Her hücre: n, n/hafta, WR, başabaş WR, ortR (A, A×1,5, B), %95 CI, P, yarılar, yıllık, 2008–15 vs 2016–26, P1/P2,
tek pozisyon, iyimser fark, kasa. $ = R × SL$ × (lot/0,01) (0,01 lot = 1 ons).

## 8. Kapsam dışı
M15 pullback (OLD-07 ile ölü), mum formasyonları, SELL'in canlıya alınması, parametre taraması (N, eşik).

## 9. Sapmalar (tarihli)
- 2026-10-15 00:48 EDT (sonuç GÖRÜLMEDEN, kod yazarken): sinyal barı ile giriş barı farklı segmentteyse (arada >3 saat
  boşluk: hafta sonu/tatil) olay atılır — decider'ın hafta sonu korumasına (kapanışa 2 s kala OPEN yok) denk; aksi
  hâlde 'sonraki açılış' Pazartesi gap'i olur. Plasebo havuzu da aynı koşulla kurulur.
- 2026-10-15 00:48 EDT: R5'in 6 H4 bar zaman çıkışı H1 yol üzerinde 24 H1 bar olarak uygulanır (H4 grupları hafta
  başında kısmi olabildiğinden yaklaşık eşdeğer).
- 2026-10-15 00:55 EDT (sonuç görülmeden): P1 uygulaması = **gün-kaydırma** — olayın UTC tarihini aynı yıldan rastgele
  bir işlem gününe taşı, aynı UTC saatindeki barı al (gün içi kümelenme korunur; §4 "aynı yıl + aynı UTC saati"ni
  sağlar). Tutma süresi = olayın kendi bar sayısı. P2 = aynı yıl+UTC saat+trend koşullu bağımsız bar çekimi.
  Seçim düzeltmesi: hücre başına z = (gerçek − P1 ort)/P1 sd; gerçek max z, plasebo tekrarlarının max z dağılımıyla kıyaslanır.
- 2026-10-15 (devralan ajan, ana sonuçlar `results/cells.csv` GÖRÜLDÜKTEN SONRA): kural/geometri/ölçüt DEĞİŞMEDİ.
  (1) `holdout.py` tz karşılaştırma hatası (çöküş) düzeltildi — mantık aynı. (2) `analyze.py` taslağındaki §5'te olmayan
  "n<150 → RED" ek kuralı kaldırıldı (§5 aynen; hiçbir hücreyi etkilemedi, tüm n ≥ 865). (3) §5'in tanımlamadığı durum
  "kart geçer, 7–10'dan 2+ düşer" `analyze.py`'de SHADOW'a düşer — protokol boşluğu olarak raporlandı, düzeltilmedi.
  (4) `posthoc.py`, `posthoc_holdout.py`, `posthoc_onepos.py` = **POST-HOC KEŞİF**, verdikte girmez.
