# NDX Gate Forge — ön-kayıt protokolü (2026-09-30, sonuçlara bakmadan yazıldı)

Amaç: NASDAQ için botun mevcut kapılarına (Cuma, ASIA, TREND_GATE, POSITION, TQ,
FAKEOUT, VIXREG…) **ortogonal** yeni kapı/strateji adayları bulmak ve her birini
birden fazla bağımsız dönemde + zaman diliminde + geometride doğrulamak.
Canlı sisteme dokunulmaz; çıktı aday listesidir (gölge → go-live kartı).

## Veri (tek saat ekseni: gerçek UTC, NY yerel saati türetilir)

| Kod | Kaynak | Dönem | Fiyat | Not |
|---|---|---|---|---|
| D25a | Dukascopy USATECHIDXUSD tick → 1m | 2025-01-02 → 06-30 | bid+ask gerçek | bağımsız kaynak |
| D25b | aynı | 2025-07-01 → 12-30 | bid+ask gerçek | |
| C26 | candle_cache 1m (panel DB) | 2026-02-10 → 05-19 | bid, spread 1,3 varsayım | **2026-03-08 öncesi etiketler 60 dk erken → +60 dk düzeltildi** (açılış sıçraması 13:30'da görünüyordu, kış saatinde 14:30 olmalı) |
| M26 | MT5 NAS100 M1 (kutu) | 2026-05-19 → 08-28 | bid + bar spread×0,1 | botun gerçek icra verisi |
| L15/L30/L60 | candle_cache 15m/30m/1h (broker saati = NY+7s) | 2023-03 / 2021-06 / 2016-05 → 2026-07-15 | bid | uzun ufuk / takvim kapıları |

Keşif = D25 (iki yarı ayrı ayrı), doğrulama = C26 + M26 (iki ayrı kaynak).
Takvim/günlük kapılar ayrıca L60 ile 10 yıl yıl-yıl.

## Birim ve etiket

- Evren U: Pzt–Per (Cuma botta yasak), 07:00–21:59 UTC (ASIA yasağı dışı) her kapanmış 1m bar.
- Karar = bar i kapanışı; giriş = bar i+1 açılışı. BUY ask'tan açar, bid'den çıkar;
  SELL bid'den açar, ask'tan çıkar. Aynı barda TP+SL → SL. SL'yi aşan açılış boşluğu → açılış fiyatı.
  Dolum başına 0,2 puan ek kayma. En uzun tutma 720 dk; >120 dk veri boşluğu → son kapanış.
- Geometriler: **G80** = TP 80 / SL 110 puan (bot VIXREG); **GS** = TP=SL=D, D=6×ATR70(1m)
  ∈[40,250]; **GR** = TP 2D / SL D. Sonuç R = pnl/SL.
- Ayrıca yön ölçüsü: 60 ve 240 dk ileri net getiri (spread dahil).

## Kapı metriği

Kapı = (koşul C, bloklanan yön s). Ölçüt **bloklanan kümenin gün-içi farkı**:
lift = ort(R − aynı gün aynı yön U-ortalaması | C). İyi kapı → lift < 0.
Ek olarak bloklanan kümenin mutlak EV'si (R) ve dönem tabanı raporlanır.
Güven: gün-bloklu bootstrap (2000). Bağımsızlık: koşulun geçerli olduğu gün sayısı raporlanır.
Takvim (gün düzeyi) kapılarında gün-içi fark anlamsız → dönem tabanına göre fark + yıl-yıl işaret.

## Ön-kayıtlı hipotezler (parametreler standart değerler, ayar YOK)

| # | Hipotez | Koşul (kararda bilinen) | Bloklanan |
|---|---|---|---|
| H1 | Kapanış akışı (LETF/gamma, Baltussen+ 2021) | 15:00–15:50 ET, |gün getirisi (önceki 16:00'dan)| ≥ %1 | güne KARŞI yön |
| H2 | Avrupa açılışı gece sürüklenmesi (Boyarchenko+ 2023) | 02:00–05:00 ET (07–09 UTC kısmı) | SELL (önceki RTH günü düşüşse güçlü) |
| H3 | Açılış boşluğu | 09:30–10:15 ET, |boşluk| ≥ %0,5 | iki yön ayrı test (yön keşifte seçilir) |
| H4 | Açılış öncesi pozisyon | 09:00–09:29 ET | premarket (04:00→) trend yönü |
| H5 | 10:00 dönüşü | 10:00–10:30 ET, |09:30→10:00| ≥ %0,4 | o hareketin yönü |
| H6 | ADR tükenmesi | gün aralığı ≥ 1,0×ADR20 ve fiyat aralığın uç %20'sinde | uzama yönü |
| H7 | **Geometri–pürüzlülük uyumu** (yeni matematik) | VR(15) son 240 dk > 1,2 (kalıcı) | TP<SL geometrisi her iki yön |
| H8 | Yuvarlak sayı bariyeri | TP yolunda ilk 0,5×TP içinde 100'lük seviye | o yön; plasebo +25/+50/+75 kaydırma |
| H9 | Efor–sonuç (emilim) | 15 dk tick hacmi z≥2 ve aralık < medyan | önceki 60 dk trend yönü |
| H10 | Ölü piyasa | RV30 / aynı dakika 20g medyanı < 0,6 | iki yön |
| H11 | VWAP σ-bandı | RTH, fiyat VWAP±2σ dışında | uzama yönü |
| H12 | Önceki gün uçları | TP yolunda ilk 0,5×TP içinde PDH/PDL | o yön; plasebo kaydırılmış seviye |
| H13 | Gerçekleşen çarpıklık | 120 dk çarpıklık < −1 / > +1 | SELL / BUY |
| H14 | Ay dönümü | ayın son + ilk 3 işlem günü | SELL |
| H15 | OPEX haftası / sonrası | 3. Cuma haftası Pzt–Per / sonraki hafta | SELL / BUY |
| H16 | VIX vade yapısı (VIXREG'in durağan hâli) | önceki gün VIX/VIX3M ≥ 1 (ters eğri) / ≤ 0,85 | SELL / BUY |

Her hipotez en fazla 2 varyant; toplam test sayısı raporda yazılır, Holm düzeltmesi uygulanır.

## Geçme ölçütleri (dört katman)

1. **Dönem**: lift işareti D25a, D25b, C26, M26'nın dördünde doğru; doğrulama (C26+M26)
   bootstrap P(lift<0) ≥ %95.
2. **Geometri**: G80 ve GS'de aynı işaret.
3. **Zaman dilimi**: koşul 1m yerine 5m (ve uygunsa 15m) barlardan hesaplanınca işaret korunur.
4. **Bot**: bot'un gerçek NAS100 işlemlerinde (07-01→08-27) kapının bloklayacağı işlemlerin $/işlem'i
   kapısız ortalamanın altında (n küçük → yalnız tutarlılık kontrolü, kanıt değil).

Takvim kapıları: L60 10 yılda yılların ≥ %70'inde doğru işaret + D25 + 2026.
Geçemeyen her hipotez raporda yazılır. Seçimden sonra ölçüt değiştirilmez.
