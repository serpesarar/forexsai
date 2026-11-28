# SY — NASDAQ'ta SL olan işlem tiplerini bulup yasaklamak (ön kayıt, 2026-11-28)

Kullanıcı: "Şimdiye kadar hep TP yapan işlemleri aradık; şimdi tüm geçmiş testleri gözden geçir, SL olan işlemlerin
ortak tiplerini, yanlış giriş yerlerini bul, kural olarak yasakla, kâr marjını yükselt."

## 0. Defterden ne biliniyor (tekrar edilmeyecek)
- IO-11 (2026-10-07): 4.104 tekli/ikili veto, eğitim↔sınama Spearman ≈ 0 → giriş vetosu genelleşmiyor (X).
- IO-18 / IO-20: NDX SELL kovalama C'ye düştü; IO-26 (10-29) ileri dönemde TERSİNE (X). RSI_DIV_KARSI TERSİNE (X).
- IO-26 T3: KEŞİF lojistiği AUC 0,73 → ileri 0,496. "Tanınan tek düzey aile/sembol-yön."
- SL-01…06 (11-23, DAYCOMBO+REENTRY, Duka 2018–26): 41 aday, SL-engel% ile TP-kayıp% korelasyonu 0,996.
- SL-08: SL'yi tanımıyor ama oynak piyasada gürültü SL'sini azaltan braket (2,5×ATR5) → B, CANLI (yalnız DC/RE BUY).
- IO-29 Y2 (zarardaki pozisyona başka aileden ekleme) GÖLGEDE, n ≥ 100'de yeniden ölçülecek.
- CK-01 (10-09): VIXREG 209 karar +0,010R → SHADOW önerisi; MOMSR −0,014 · CHREV −0,016.

**Yeni olan:** (1) CK-01'den sonra gelen 7 haftalık canlı veri (10-10 → 11-28) ve IO-26'dan sonraki 4 hafta (10-30 → 11-28),
hiçbir NDX SL çalışmasında görülmedi; (2) tanım: SL tipini tek bir ailede değil **tüm canlı NDX kitabında, aile tabakalı**
aramak; (3) kullanıcının ölçüsü (engellenen SL % − kaybedilen TP %) her aday için zorunlu.

## 1. Veri
Supabase `bot_trades`, NDX (NAS100/USTEC), 2026-06-01 → 2026-11-28; `scripts/islem_otopsi` hizalaması (saat ekseni fiyat
eşleştirmesiyle, E2); karar birimi = aynı aile+yön, 2 dk içindeki bacaklar (E9); R = karar net $ / ilk risk $ (live_card.py
birebir). Broker 1m (`indicator_snapshots`). Dönemler: ÖN = karar < 2026-10-10, İLERİ = ≥ 2026-10-10; İLERİ-2 = ≥ 2026-10-30.

## 2. A — Aile/yön yasağı (defterin "tanınan tek düzey"i)
Her aile×yön (≥ 30 karar). **Yasak önerisi** ancak hepsi: (a) tüm dönem ort R < 0; (b) gün-blok bootstrap P(EV<0) ≥ %80;
(c) ÖN ve İLERİ ort R ikisi de ≤ 0; (d) $ toplamı < 0. Yalnız (a)+(c) tutup ort R |·| < 0,03 ise **"ölü risk"** (kenar yok,
risk tüketiyor) etiketi: lot küçültme/gölge önerisi. Pozitif aileler için de aynı tablo (kıyas).

## 3. B — İşlem tipi (aile içi) yasakları, mekanizmadan türetilmiş, sonuçlara bakmadan donduruldu
Bayraklar girişte bilinen bilgiyle:
- **B1 gürültü/dar stop:** NR = SL puanı / (ATR14(1m)·√30) < 0,5 (SL-01 vakası; SL-08 yalnız DC/RE'yi düzeltti).
- **B2 Y2 yığılma:** aynı yönde başka NDX pozisyonu açık VE o pozisyon girişte zararda (IO-29, bot_trades'ten hesaplanır).
- **B3 Y1 yığılma:** aynı yönde başka NDX pozisyonu açık (zarar şartı yok).
- **B4 kötü gün:** aynı UTC gününde girişten önce kapanmış ≥ 2 NDX SL kararı.
- **B5 kovalama:** son 60 dk hareket işlem yönünde ≥ 1,5 × ATR14(5m) (IO-18/29 tanımı; ileri sınama amaçlı).

Ölçüt (her bayrak): Δ = bayraklı − bayraksız ort R, aile tabakalı (aile×yön içinde fark, karar ağırlıklı); bayraklı n ≥ 20;
gün-blok bootstrap P(Δ<0) ≥ %90; ÖN ve İLERİ'de Δ < 0; **SL-engel% − TP-kayıp% ≥ 10 puan**; Holm (5 bayrak) sonrası da
P ≥ %90. Geçen → yalnız GÖLGE etiketi (2. KURAL; canlı ≥ 100 işlem kartı olmadan blok yok). Ayrıca seçim düzeltmesi
yok sayılmasın diye **plasebo**: bayrak dizisini gün içinde dairesel kaydır ×1000, Δ'nın boş dağılımdaki yüzdeliği.

## 4. C — Kullanıcı ölçüsü sınırı (betimsel)
Tüm bayraklar için (SL-engel%, TP-kayıp%) noktası ve korelasyon; SL-06 frontier'ı (0,996) canlı kitapta tekrar ediyor mu.

## 5. Yasaklanmayacak olan
Sonuca bakıp eşik seçmek, yeni özellik eklemek, tek ayın kazancı. Ek tur gerekirse EK-n olarak buraya önce yazılır.

## EK-1 (2026-11-28, A/B sonuçlarından sonra, OLAY GÜNÜ sonuçlarına bakmadan) — makro olay günü SL tipi, DAYCOMBO+REENTRY 9 yıl
Gerekçe: defterde DC/RE için olay günü hiç sınanmadı; ORB'de "makro günü 5/5 set eksi" (TS-01 E, C), korku ailesinde ZA-04 olay
vetosu kör 3/3. Mekanizma: olay saatinde oynaklık sıçrar, 80/110 braket gürültüde çözülür (SL-01 vakası 13:45 UTC şoku).
- Veri: `research/ndx_sl_onleme_20261123/results/base_full.pkl` (TD-01 motoru, DC+RE, 2018-04 → 2026-11-20; VAKA satırları hariç).
- Takvim: `research/xau_best_days_20261015/makro/out/calendar.csv` (FOMC / CPI / NFP, ts_utc).
- Bayraklar: **E1** FOMC günü (tüm gün) · **E2** FOMC penceresi (giriş olaydan 120 dk önce → 60 dk sonra) · **E3** CPI ya da NFP günü ·
  **E4** E1 ∨ E3.
- Ölçüt (hepsi): bayraklı n ≥ 40; bayraklı ort R < 0 ve kalanın ort R > tabanın; gün-blok bootstrap P(bayraklı ortR < 0) ≥ %90;
  üç çağın üçünde (2018–20, 2021–23, 2024–26) bayraklı ort R < 0; bayraklı SL oranı ≥ taban SL oranı + 10 puan;
  **plasebo**: aynı sayıda olaysız gün (aynı haftanın günü dağılımı) ×1000, bayraklı ort R'nin yüzdeliği ≤ %5; Holm (4) sonrası P ≥ %90.
- Geçen → yalnız GÖLGE etiketi (bot log), canlı blok 2. KURAL kartıyla. Uyarı: TD-01 tabanı lag 0; lag 1 farkı gün düzeyi vetoyu
  etkilemez sayılır (SL-05: gecikme etkisi işlem içi), raporda belirtilir.
