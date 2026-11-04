# CAPREV portföyü (NDX + DAX) — DAX saat ekseni hatası sonrası kanıtın yeniden doğrulanması

**Kısa sonuç:**
- Hata gerçek. `research/ndx_gate_forge/data/dax_{15m,30m,1h}.parquet` etiketleri, New York standart saatindeyken
  (ABD'de 1. Pazar Kasım → 2. Pazar Mart) tam olarak 60 dk erken.
- Mart ve Ekim–Kasım omuz haftaları (NY yaz saati, Berlin kış saati) doğru. Mekanizma: broker saati (NY+7) sabit
  −3 saatle UTC'ye çevrilmiş. Bu, E4 ile aynı aile.
- Düzeltmeden sonra DAX bacağı zayıflamadı, biraz güçlendi: 54 işlem, ortR **+0,171 → +0,212**, P(EV>0) %89,1 → %93,9.
- Portföy kartı 161 işlem / 134 bağımsız gün, ortR **+0,217 → +0,231**, P %99,0 → %99,5 ve **6/6**.
- NDX long_1h'deki 2017-11 → 2018-02 "60 dk geç" hatası da doğrulandı. CAPREV NDX bacağını hiç değiştirmiyor
  (iki olay da iki versiyonda −1R stop).
- Canlı modül `caprev_live.py` doğru Berlin seansını uyguluyor. Kanıt hatalı eksende üretilmişti, canlı kod ise doğru
  eksende işlem yapıyor; düzeltilmiş kanıt canlıyla birebir (54/54) eşleşiyor.
- **CAPREV portföy kartı düzeltmeden sonra: LIVE.** Canlı botta zorunlu değişiklik yok; yalnız küçük sağlamlık önerileri
  var (aşağıda).

Kod ve çıktılar: `research/nasdaq_derin_20261013/caprev_dax_recheck/`. Orijinal veri, kart JSON'u, bot ve backend
değiştirilmedi.

| betik | iş |
|---|---|
| `axis_dax.py` | ay × DST-sınıfı tepe dakikası, iki çapa (Xetra açılışı + ABD nakit açılışı), UTC'de |
| `axis_volume.py` | gün bazında tik-hacmi sıçraması, iki çapa |
| `axis_1h_crosscheck.py` | 1h ↔ 30m hizası + yıllık saat profili |
| `axis_ndx_long.py`, `axis_ndx_long_std.py` | NDX long_1h ↔ NDXCASH 16:00 kapanışı |
| `fix_data.py` | düzeltilmiş kopyalar → `data_fixed/` |
| `recheck_card.py` | kart yeniden üretimi, 5 senaryo; kart JSON'una yazmaz |
| `compare_dax_events.py` | olay-olay fark |
| `recheck_gf18.py` | GF-18 çapraz-piyasa tablosu |
| `live_fidelity_fixed.py` | canlı kod ↔ düzeltilmiş veri |

`axis_days.py` ve `axis_jump.py` (aralık oranı ile gün-bazlı oylama) gürültülü çıktı. Karar için kullanılmadılar;
çıktıları `results/`'ta duruyor.

---

## 1. Saat ekseni hatası gerçek mi, tam olarak ne zaman geçerli?

### Takeaway
Gerçek ve kayma tam 60 dk. Etiketler yalnız NY standart saatindeyken (≈ Kasım başı → Mart'ın 2. Pazarı) erken; bu
dönemde Berlin de kış saatindedir. NY yaz ∧ Berlin kış omuz haftaları **doğru**; "NY kış ∧ Berlin yaz" hiç oluşmuyor.
Kural "Berlin ve NY'nin DST durumu farklıyken" değil, **"NY standart saatteyken"**. Önceki araştırmacının düzeltme
kuralı (`imcore.load_dax`: NY DST değilse +60 dk) doğru.

Hata 2019-01'den 2026-02'ye kadar her kışta aynı. 2026-02-10 → 03-08 (NDX'te E4 penceresi) DAX'ta ayrı bir istisna
oluşturmuyor.

### Cited Findings
**Aylık tepe (çapa A: Xetra 09:00 Berlin).** Doğru UTC yaz saatinde 07:00, kışta 08:00. Hafta içi medyan bar aralığının
05:00–10:00 UTC arasındaki tepe dakikası ay × DST sınıfı başına bulundu.
— [axis_dax.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/axis_dax.py),
[results/axis_stdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_stdout.txt)

| sınıf | 1h | 30m | 15m |
|---|---|---|---|
| NY kış ∧ Berlin kış | −60 dk: 36/38 ay | −60: 24/25 | −60: 20/20 |
| NY yaz ∧ Berlin kış (omuz) | 0: 14/15 | 0: 11/11 | 0: 4/7 (+15: 2, +45: 1; hücre başına 3–5 gün) |
| NY yaz ∧ Berlin yaz | 0: 57/58 | 0: 43/44 | 0: 28/28 |

1h istisnaları üç tane:
- Kış sınıfında 2019-03'ün 6 günü ve 2026-03'ün 5 günü kaymasız çıkıyor (her ikisi de kısa hücre).
- Omuz sınıfında 2026-03 +60 çıkıyor (yüksek oynaklık haftaları).

Bu istisnalar hacim testinde (aşağıda) kaybolan küçük-örnek gürültüsü.

**Gün bazında tik-hacmi testi.** İki bağımsız çapa kullanıldı: Xetra açılışı ve ABD 09:30 açılışı. Skor
log(v[t+s]/v[t+s−adım]) toplamı; s ∈ {−60, 0, +60}. 30m ve 15m sonuçları:
- **NY kış ∧ Berlin kış:** her sezonda günlerin %100'ünde s = −60. 15m'de 2022/23–2025/26, 345 gün; 30m'de 2021/22–2025/26,
  434 gün.
- **Omuz:** s = 0, %68–95 (15m), %73–95 (30m).
- **Yaz:** s = 0, %86–97 (15m), %88–97 (30m).
- Modele ("NY standart → −60, değilse 0") uymayan güçlü gün sayısı 15m'de 8/991, 30m'de 10/1412. Hepsi tek tük yaz
  günü; sistematik bölüt yok. Tek +60 günü: 2026-03-24.

— [axis_volume.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/axis_volume.py),
[results/axis_volume_15m.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_volume_15m.txt),
[results/axis_volume_30m.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_volume_30m.txt)

**1h dosyası 30m ile aynı eksende.** 1h etiketi + 0 dk = 30m'den toplanmış saat:
- high/low eşleşmesi %99,5 (n = 31.003)
- ±60 dk kaymayla %0,1–0,2

1h ile 30m'nin ortak dönemi 2021-03+. 2019–2020 için yıllık saatlik profil: medyan aralık tepesi her yıl hem NY-yaz hem
NY-kış satırında 07:00 UTC etiketinde. Oysa kışta doğrusu 08:00 UTC. Yani 2019'dan beri aynı kış hatası 1h'te de var.
— [axis_1h_crosscheck.py / results/axis_1h_crosscheck.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_1h_crosscheck.txt)

**Düzeltme sonrası.** NY standart saatindeki barlara +60 dk eklendi (çakışma 0 bar). Sonra tüm hücreler 0 kaymada:
15m kış 20/20, 1h kış 36/38. Kalan 2 hücre, yukarıdaki kısa Mart hücreleri.
— [fix_data.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/fix_data.py),
[results/fix_data_stdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/fix_data_stdout.txt)

Etkilenen bar sayısı: 1h 17.145/51.532, 30m 19.148/62.025, 15m 29.815/83.915.

**Önceki araştırmacının bulgusu ve düzeltmesi bağımsız yeniden üretimle uyumlu.**
- Bulgu: "ABD standart saatinde Berlin 08:00 etiketinde 80,5 puan, 09:00'da 54,4".
- Düzeltme: `imcore.load_dax`; sonrasında açılış tepesi 68/68 ayda 09:00 Berlin.

— [intraday_momentum.md](/Users/melihcanodacioglu/Desktop/panel/research_notes/NASDAQ%20gün%20içi%20kenar%20araştırması/intraday_momentum.md),
[imcore.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/intraday_momentum/imcore.py)

**Kaynak verinin tanımı.** `pull_dax.py`, candle_cache GDAXI'yi "07-28 onarımı sonrası UTC" diyerek çekiyor ve olduğu
gibi yazıyor. `cross_market.build_dax` bu dosyayı düzeltmeden `tz_convert("Europe/Berlin")` ile okuyor.
— [pull_dax.py](/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/pull_dax.py),
[cross_market.py](/Users/melihcanodacioglu/Desktop/panel/research/ndx_gate_forge/cross_market.py)

**Ay-ay tablo.** 1h/30m/15m için Xetra açılış tepesinin etiket UTC'si ve kayması (dk; −60 = etiket 60 dk erken). Tam
tablo: [results/axis_month_table.md](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_month_table.md)

| ay | DST durumu | gün(1h) | 1h tepe UTC (kayma dk) | 30m | 15m |
|---|---|---|---|---|---|
| 2019-01 | NY kış/Berlin kış | 22 | 07:00 (-60) | — | — |
| 2019-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | — | — |
| 2019-03 | NY yaz/Berlin kış (omuz) | 15 | 08:00 (+0) | — | — |
| 2019-03 | NY kış/Berlin kış | 6 | 08:00 (+0) | — | — |
| 2019-04 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | — | — |
| 2019-05 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | — | — |
| 2019-06 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | — | — |
| 2019-07 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | — | — |
| 2019-08 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | — | — |
| 2019-09 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | — | — |
| 2019-10 | NY yaz/Berlin kış (omuz) | 4 | 08:00 (+0) | — | — |
| 2019-10 | NY yaz/Berlin yaz | 19 | 07:00 (+0) | — | — |
| 2019-11 | NY kış/Berlin kış | 20 | 07:00 (-60) | — | — |
| 2019-12 | NY kış/Berlin kış | 21 | 07:00 (-60) | — | — |
| 2020-01 | NY kış/Berlin kış | 23 | 07:00 (-60) | — | — |
| 2020-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | — | — |
| 2020-03 | NY yaz/Berlin kış (omuz) | 15 | 08:00 (+0) | — | — |
| 2020-03 | NY kış/Berlin kış | 5 | 07:00 (-60) | — | — |
| 2020-04 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | — | — |
| 2020-05 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | — | — |
| 2020-06 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | — | — |
| 2020-07 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | — | — |
| 2020-08 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | — | — |
| 2020-09 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | — | — |
| 2020-10 | NY yaz/Berlin kış (omuz) | 5 | 08:00 (+0) | — | — |
| 2020-10 | NY yaz/Berlin yaz | 17 | 07:00 (+0) | — | — |
| 2020-11 | NY kış/Berlin kış | 21 | 07:00 (-60) | — | — |
| 2020-12 | NY kış/Berlin kış | 22 | 07:00 (-60) | — | — |
| 2021-01 | NY kış/Berlin kış | 20 | 07:00 (-60) | — | — |
| 2021-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | — | — |
| 2021-03 | NY yaz/Berlin kış (omuz) | 10 | 08:00 (+0) | 08:00 (+0) | — |
| 2021-03 | NY kış/Berlin kış | 10 | 07:00 (-60) | — | — |
| 2021-03 | NY yaz/Berlin yaz | 3 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-04 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-05 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-06 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-07 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-08 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-09 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-10 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | — |
| 2021-11 | NY yaz/Berlin kış (omuz) | 5 | 08:00 (+0) | 08:00 (+0) | — |
| 2021-11 | NY kış/Berlin kış | 17 | 07:00 (-60) | 07:00 (-60) | — |
| 2021-12 | NY kış/Berlin kış | 21 | 07:00 (-60) | 07:00 (-60) | — |
| 2022-01 | NY kış/Berlin kış | 21 | 07:00 (-60) | 07:00 (-60) | — |
| 2022-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | — |
| 2022-03 | NY yaz/Berlin kış (omuz) | 10 | 08:00 (+0) | 08:00 (+0) | — |
| 2022-03 | NY kış/Berlin kış | 9 | 07:00 (-60) | 07:00 (-60) | — |
| 2022-03 | NY yaz/Berlin yaz | 4 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-04 | NY yaz/Berlin yaz | 19 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-05 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-06 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-07 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-08 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-09 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-10 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | — |
| 2022-11 | NY yaz/Berlin kış (omuz) | 4 | 08:00 (+0) | 08:00 (+0) | — |
| 2022-11 | NY kış/Berlin kış | 18 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2022-12 | NY kış/Berlin kış | 22 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2023-01 | NY kış/Berlin kış | 22 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2023-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2023-03 | NY yaz/Berlin kış (omuz) | 10 | 08:00 (+0) | 08:00 (+0) | 08:00 (+0) |
| 2023-03 | NY kış/Berlin kış | 8 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2023-03 | NY yaz/Berlin yaz | 5 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-04 | NY yaz/Berlin yaz | 19 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-05 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-06 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-07 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-08 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-09 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-10 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2023-11 | NY yaz/Berlin kış (omuz) | 3 | 08:00 (+0) | 08:00 (+0) | 08:15 (+15) |
| 2023-11 | NY kış/Berlin kış | 19 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2023-12 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2024-01 | NY kış/Berlin kış | 23 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2024-02 | NY kış/Berlin kış | 21 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2024-03 | NY yaz/Berlin kış (omuz) | 14 | 08:00 (+0) | 08:00 (+0) | 08:00 (+0) |
| 2024-03 | NY kış/Berlin kış | 6 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2024-04 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-05 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-06 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-07 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-08 | NY yaz/Berlin yaz | 22 | 08:00 (+60) | 08:00 (+60) | 07:00 (+0) |
| 2024-09 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-10 | NY yaz/Berlin kış (omuz) | 4 | 08:00 (+0) | 08:00 (+0) | 08:00 (+0) |
| 2024-10 | NY yaz/Berlin yaz | 19 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2024-11 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2024-12 | NY kış/Berlin kış | 19 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2025-01 | NY kış/Berlin kış | 23 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2025-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2025-03 | NY yaz/Berlin kış (omuz) | 15 | 08:00 (+0) | 08:00 (+0) | 08:15 (+15) |
| 2025-03 | NY kış/Berlin kış | 5 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2025-04 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-05 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-06 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-07 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-08 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-09 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-10 | NY yaz/Berlin kış (omuz) | 5 | 08:00 (+0) | 08:00 (+0) | 08:00 (+0) |
| 2025-10 | NY yaz/Berlin yaz | 18 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2025-11 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2025-12 | NY kış/Berlin kış | 19 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2026-01 | NY kış/Berlin kış | 22 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2026-02 | NY kış/Berlin kış | 20 | 07:00 (-60) | 07:00 (-60) | 07:00 (-60) |
| 2026-03 | NY yaz/Berlin kış (omuz) | 15 | 09:00 (+60) | 08:00 (+0) | 08:45 (+45) |
| 2026-03 | NY kış/Berlin kış | 5 | 08:00 (+0) | 08:00 (+0) | 07:00 (-60) |
| 2026-04 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2026-05 | NY yaz/Berlin yaz | 20 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2026-06 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2026-07 | NY yaz/Berlin yaz | 23 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2026-08 | NY yaz/Berlin yaz | 21 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |
| 2026-09 | NY yaz/Berlin yaz | 22 | 07:00 (+0) | 07:00 (+0) | 07:00 (+0) |

### Inferences
- **Mekanizma:** broker sunucu saati NY+7'dir (kış UTC+2, yaz UTC+3; ABD DST tarihleriyle değişir). Bu saatten her zaman
  3 saat çıkarılırsa tam olarak bu desen çıkar:
  - NY kış: 60 dk erken.
  - NY yaz (Berlin kış omuzu dahil): doğru.

  Bu, E2/E4'teki "kışta −180 uygulanmış, doğrusu −120" hatasının DAX geçmişinin tamamına (2019+) yayılmış hâli.
- **Araştırmadaki DAX kuralı kışın aslında başka saatlerde çalışmış.** Kış ayları yılın ≈%35'i; DAX olaylarının 14/54'ü
  bu aylarda.
  - Tetik penceresi gerçekte 09:00–17:30 Berlin olmuş (08:00–16:30 yerine).
  - Önceki gün dibi gerçekte 10:00–19:00'dan alınmış.
  - Stres/dvol kapanışları ve çıkış gerçekte 19:00 Berlin olmuş (18:00 yerine).

### Gaps
- 2019 öncesi DAX 1h (1999–2018) kontrol edilmedi; CAPREV ≥2019 kullanıyor.
- Hatanın candle_cache GDAXI tablosunun kendisinde de olduğu varsayılıyor ama DB'ye bakılmadı (kısıt gereği).
  Backend'in DAX saat-bazlı analizleri (MK-01/02 DAX dahil) aynı riski taşıyor; ayrıca doğrulanmalı.

---

## 2. Düzeltilmiş CAPREV DAX olayları ve kartı

### Takeaway
Düzeltilmiş eksende DAX: **n = 54, WR %55,6, ortR +0,212, toplam +11,47R, P(EV>0) %93,9** (gün-bloklu bootstrap,
CI95 [−0,056; +0,502]). Yarılar +0,144 / +0,281; pozitif yıl 5/8.

Orijinal 54 olaydan:
- 52'sinin tarihi korunuyor; 1 olay düşüyor, 1 olay ekleniyor.
- 7 olayın tetik barı değişiyor; hepsi kış günü ve hepsi gerçek 09:00 → 08:00 Berlin.
- 4 olayın pdl'i değişiyor.
- Kış olaylarının 14'ünün 14'ü bir şekilde değişiyor.
- 28 olay birebir aynı.

DAX bacağı düzeltmeyle güçlendi ama tek başına hâlâ geniş belirsizlikte (CI sıfırı içeriyor).

### Cited Findings
**Yeniden üretim kontrolü.** ORJ senaryosu kartı birebir veriyor: 161 / 134, ortR +0,217, P %99,0, yarılar
+0,064/+0,367, ×1,5 +0,213, kapanış-girişi farkı 0,008, tek-poz +0,160, DAX 54 / +0,171, NDX 107 / +0,240.
— [recheck_card.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/recheck_card.py),
[results/recheck_card_stdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/recheck_card_stdout.txt);
orijinal kart [caprev_portfoy.json](/Users/melihcanodacioglu/Desktop/panel/backend/data/evolution/go_live_cards/caprev_portfoy.json)

**DAX bacağı, eski ↔ düzeltilmiş**
— [results/recheck_card.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/recheck_card.json)

| ölçü | ORJ (hatalı eksen) | düzeltilmiş |
|---|---|---|
| n | 54 | 54 |
| WR | %53,7 | %55,6 |
| ortR | +0,171 | **+0,212** |
| toplam R | +9,22 | +11,47 |
| P(EV>0), bacak bootstrap | %89,1 | %93,9 |
| CI95 | [−0,089; +0,453] | [−0,056; +0,502] |
| yarılar | +0,063 / +0,278 | +0,144 / +0,281 |
| pozitif yıl | 4/8 | 5/8 |

**Olay-olay fark** — [compare_dax_events.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/compare_dax_events.py),
[results/dax_event_diff.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/dax_event_diff.txt) / `.csv`

Orijinaldeki kış olayları 14 tane. Hepsinin gerçek çıkışı 19:00 Berlin (bar başı 18:00); düzeltilmişte tüm çıkışlar
18:00 Berlin. Orijinal kış tetiklerinin gerçek Berlin saatleri: 09:00 ×9, 11:00, 12:00 ×3, 14:00.

- **Düşen:** 2022-03-01 (orijinal R −1,007).
- **Eklenen:** 2020-03-05 (−0,127). Stres ve dvol artık 18:00 kapanışından hesaplanıyor.
- **Tetik barı değişen 7 olay:** hepsinde 09:00 → 08:00 Berlin. Orijinalin kaymış penceresinde 08:00 Berlin barı
  pencere dışıydı.

  | tarih | R (eski → yeni) |
  |---|---|
  | 2020-02-26 | +0,854 → −1,009 |
  | 2021-11-30 | −0,041 → −0,306 |
  | 2022-02-22 | −0,301 → +1,592 |
  | 2022-02-24 | −1,011 → +0,683 |
  | 2022-03-02 | +1,072 → +0,804 |
  | 2022-03-07 | +0,528 → +0,710 |
  | 2026-03-03 | −1,014 → −1,014 |

- **pdl değişen 4 olay:**

  | tarih | pdl (eski → yeni) |
  |---|---|
  | 2020-02-25 | 12976,0 → 12979,4 |
  | 2020-02-26 | 12755,1 → 12757,9 |
  | 2022-03-02 | 13763,3 → 13799,8 |
  | 2023-03-13 | 15319,5 → 15312,1 |

  2023-03-13 bir yaz Pazartesisi; pdl'in değişmesinin nedeni önceki Cuma'nın kış günü olması.
- **Yalnız dvol/r1'i değişen 12 yaz olayı:** 20 günlük pencerede kış kapanışları var. R farkları küçük (toplam +0,15R).
  Örnekler: 2020-03-09 −0,646 → −0,655; 2026-03-09 +1,690 → +1,767.
- **R toplam farkı +2,25R:**
  - kış olaylarındaki değişim: +1,22
  - yaz dvol etkisi: +0,15
  - düşen/eklenen olaylar: +0,88

**GF-18 çapraz-piyasa tablosu (DAX, stres ∧ VIX ≥ 18,4), eski → düzeltilmiş**
— [recheck_gf18.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/recheck_gf18.py),
[results/recheck_gf18_stdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/recheck_gf18_stdout.txt)

| TF | aynı gün n / ortR / P | ertesi gün ortR / P | ayna SELL | saat plasebosu yüzdeliği |
|---|---|---|---|---|
| 1h | 54 / +0,171 / 0,889 → 54 / **+0,212 / 0,939** | +0,348 / 0,976 → **+0,467 / 0,991** | −0,187 → −0,206 | 1,00 → 1,00 (plasebo ort −0,037) |
| 30m | 37 / +0,120 / 0,775 → 36 / **+0,190 / 0,860** | +0,472 / 0,972 → **+0,560 / 0,986** | −0,168 → −0,254 | 0,835 → 0,85 |
| 15m | 13 / +0,183 / 0,719 → 14 / +0,109 / 0,648 | +0,872 / 0,970 → +0,674 / 0,940 | −0,196 → −0,052 | 0,495 → 0,60 |

Kontrol hücreleri düzeltilmiş 1h'te:
- stressiz ∧ VIX-yüksek: +0,002 (n = 205)
- stres ∧ VIX-düşük: +0,197 (n = 6)

### Inferences
- **Düzeltme kanıtı zayıflatmıyor.** 1h ve 30m'de güçlendiriyor. 15m'de n = 13–14 ile anlamsız; zaten önceki raporda da
  yalnız yan ölçümdü.
- "İki şart birlikte gerekli" yapısı korunuyor: stressiz ∧ yüksek VIX ≈ 0.
- **Uyarı (E23/E24 ruhunda):** 7 tetik değişikliğinin R'yi her iki yönde ±1,7R oynatması, DAX bacağının olay-düzeyinde
  çok gürültülü olduğunu gösteriyor. 54 olayla bacak tek başına %95 güvenle sıfırdan ayrılmıyor.
- Düzeltme sonuçlara bakılarak seçilmedi: kural, eksen kanıtından (hacim/aralık) önce ve CAPREV'e bakmadan sabitlendi.
  Yine de "düzeltme iyileştirdi" bulgusunu ek kenar kanıtı olarak değil, **en az eski kadar sağlam** diye okumak doğru.

### Gaps
- M1 katı icra (sonraki M1 açılışı + gerçek GER40 spread'i) DAX için hiç yapılmadı. Kartın 5. ölçütü 1h bar açılışıyla
  ölçülüyor.
- DAX spread'i SPR = 0,00006 (≈1,4 puan @24.000) varsayımıyla; ölçülmedi.

---

## 3. Düzeltilmiş portföy kartı (NDX + DAX) — verdikt hâlâ LIVE mı?

### Takeaway
**Evet, LIVE (6/6).** Ön kayıtlı ek şart (≥100 bağımsız gün) de sağlanıyor: 134. Her ölçüt eskisinden aynı ya da biraz
daha iyi. NDX 1h düzeltmesi CAPREV NDX bacağında hiçbir sayıyı değiştirmiyor. 2017-11 → 2018-03'ü tamamen dışlamak
(diğer araştırmacının yolu) portföyü 159 / 132 / +0,246'ya çıkarıyor; o da LIVE.

### Cited Findings
— [results/recheck_card_stdout.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/recheck_card_stdout.txt),
[results/recheck_card.json](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/recheck_card.json)

Senaryolar:
- **ORJ:** orijinal veri.
- **TAM_a:** DAX +60 (NY std) ve NDX −60, 2017-11-05…2018-02-26.
- **TAM_b:** aynı, NDX bitişi 2018-03-02.
- **TAM_x:** DAX düzeltilmiş, NDX 2017-11-05…2018-03-11 dışlanmış.

| # | ölçüt (eşik) | ORJ — mevcut kart | **TAM_a / TAM_b (düzeltilmiş)** | TAM_x (NDX kışı dışlanmış) |
|---|---|---|---|---|
| 1 | hacim (≥150 işlem ve ≥100 bağımsız gün) | 161 / 134 ✓ | **161 / 134 ✓** | 159 / 132 ✓ |
| 2 | beklenti (ortR > 0 ve P ≥ %90) | +0,217, P %99,0 ✓ | **+0,231, P %99,5 ✓** | +0,246, P %99,5 ✓ |
| 3 | kararlılık (iki yarı ≥ 0) | +0,064 / +0,367 ✓ | **+0,091 / +0,369 ✓** | +0,105 / +0,386 ✓ |
| 4 | sürtünme (spread ×1,5 > 0) | +0,213 ✓ | **+0,227 ✓** | +0,242 ✓ |
| 5 | icra (fark < 0,5 × ortR) | +0,225 vs +0,217, fark 0,008 < 0,108 ✓ | **+0,238 vs +0,231, fark 0,008 < 0,115 ✓** | fark 0,008 < 0,123 ✓ |
| 6 | sıra-bağımlı (gün başına tek poz. > 0) | n 134, +0,160 ✓ | **n 134, +0,176 ✓** | n 132, +0,194 ✓ |
| — | WR | %55,3 | %55,9 | %56,6 |
| — | toplam R | +34,87 | +37,12 | +39,13 |
| — | CI95 (gün-bloklu) | [+0,031; +0,402] | [+0,052; +0,423] | [+0,064; +0,435] |
| — | en iyi 5 gün hariç toplam (payı) | +12,40 (%64) | +14,58 (%61) | +16,60 (%58) |
| — | pozitif yıl | 7/10 | 7/10 | 8/10 |
| — | NDX bacağı | 107 / +0,240 / P 0,986 | 107 / +0,240 (değişmedi) | 105 / +0,263 |
| — | DAX bacağı | 54 / +0,171 / P 0,891 | 54 / +0,212 / P 0,939 | 54 / +0,212 |
| — | **verdikt** | LIVE | **LIVE** | LIVE |

DAX'ı düzeltip NDX'i olduğu gibi bırakan DAXfix senaryosu TAM_a/b ile birebir aynı.

**NDX long_1h 2017-11 → 2018-03 hatası doğrulandı.**
- **Ay bazında std testi.** 16:00 NY'de biten bar kapanışı ile NDXCASH kapanışı arasındaki farkın std'si, sabit vadeli
  bazını yok eden ölçü. 122 ayın 119'unda en düşük std 0 kaymada. Yalnız 3 ayda +60 (etiket geç):

  | ay | std (0 kayma) | std (+60) |
  |---|---|---|
  | 2017-12 | 16,2 bp | 5,0 bp |
  | 2018-01 | 17,0 bp | 4,0 bp |
  | 2018-02 | 79,9 bp | 17,4 bp |

- **Gün bazında.** Geç etiket 2017-11-06 civarında başlıyor (11-09: 23 bp marj) ve 2018-02-26'da bitiyor. 02-27'den
  itibaren 15:00 barı nakitle eşleşiyor.
- **Haftalık seans açılışı.** 2017-11-05 → 2018-02-25 haftalarında Pazar 19:00, sonrasında 18:00. Bitiş ±4 gün belirsiz;
  bu yüzden iki varyant (a/b) çalıştırıldı.

— [results/axis_ndx_long_std.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_ndx_long_std.txt),
[results/axis_ndx_long.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/axis_ndx_long.txt)

2025-01'deki karışık |fark| oyları zaman hatası değil. 15:00 barı her gün ≈ −20 bp sabit baz farkı taşıyor (std 4 bp)
ve en düşük std yine 0 kaymada.

**NDX CAPREV bu pencerede yalnız iki olay içeriyor: 2018-02-06 ve 2018-02-08.**
- Düzeltmeyle 02-06'nın tetik barı 03:00 → 04:00 NY'ye kayıyor ve pdl 6616,4 → 6493,8 oluyor (5 Şubat'ın 15:00 çöküş
  barı artık RTH'de).
- İki olay da her iki versiyonda −1,01R stop. Bu yüzden NDX bacağı 107 / +0,240 / 25,65R'de değişmedi.

— [results/trades_ORJ.csv, trades_TAM_a.csv](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/)

### Inferences
- **Verdikt korunuyor.** Kartın hiçbir ölçütü eşiğe yaklaşmadı. En dar marj 3. ölçütün ilk yarısı: +0,064 → +0,091.
- Kartın değişmeyen uyarıları:
  - toplamın %61'i en iyi 5 günden
  - E23 (NDX geçmişine 4+ tur bakıldı)
  - ileri gölge/canlı olay sayısı hâlâ ≈0
- Kart JSON'u bu oturumda güncellenmedi (kısıt). Koordinatör `caprev_portfoy.json`'u düzeltilmiş veriyle yeniden
  üretmek isterse `caprev_pooled.py`'nin `cm.DATA`'yı düzeltilmiş dosyaya yönlendirmesi yeterli.
  `recheck_card.py` bunun nasıl yapılacağını gösteriyor.

### Gaps
- NDX bitiş günü (2018-02-26 ile 03-02 arası) kesinleştirilemedi. CAPREV için önemsiz: o günlerde olay yok.
- Bootstrap tohumları `common.block_boot`'un kendi varsayılanları. P değerleri ±0,5 puan oynayabilir.

---

## 4. Canlı modül (`yeni deneme/caprev_live.py`) etkileniyor mu?

### Takeaway
**Canlı icra etkilenmiyor; aksine doğru eksende çalışıyor.**
- Bot MT5 GER40 H1 barlarını ölçülmüş broker ofsetiyle gerçek UTC'ye çeviriyor.
- Berlin yerel saatine geçiş kendi DST kurallarıyla yapılıyor ve bu kurallar doğru.
- Böylece seans 09:00–18:00, tetik penceresi 08:00–16:30 ve çıkış 18:00 Berlin, her mevsimde doğru uygulanıyor.

Hatalı olan araştırma kanıtıydı: kışın 1 saat kaymış bir kuralı ölçmüştü. Düzeltilmiş kanıt (bölüm 2–3) canlı kodla
birebir eşleşiyor: 54/54 gün, aynı tetik barı.

Önceki sadakat testi (54/54) bunu kanıtlamıyordu, çünkü canlı mantığa ve karta aynı hatalı veriyi veriyordu.

Küçük, ölçülmüş bir yan etki var: tek anlık ofset. Ayrıca bir sağlamlık riski var: bayat tik ve ortak önbellek.
İkisi de değişiklik zorunluluğu doğurmuyor.

### Cited Findings
**Saat dönüşümü.** `caprev_shadow.tz_offset_min`:
- EU: son Pazar Mart 01:00Z → son Pazar Ekim 01:00Z arası +120, aksi hâlde +60.
- US: 2. Pazar Mart 07:00Z → 1. Pazar Kasım 06:00Z arası −240, aksi hâlde −300.

`to_local` UTC epoch'u bu ofsetle yerel tarih/dakikaya çeviriyor; `local_to_utc` tersini yapıyor. Bunlar resmî AB ve
ABD DST kuralları.
— [caprev_shadow.py](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/caprev_shadow.py) (satır ~55–90)

**Profil.** `PROFILES["GDAXI.INDX"] = {"tz": "EU", "rth": (540, 1080), "close": 1080, "win": (480, 990), "need_from": 540}`.
Bu, araştırmadaki `cross_market` 1h tanımının yerel-saat karşılığı:
- seans 09:00–18:00
- kapanış barı bitişi 18:00
- tetik barı başı ≥ 08:00 ve bitişi ≤ 16:30
- Pzt–Per

— [caprev_live.py](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/caprev_live.py)

**Bar zamanı.** `_h1(rates, off_s)` her bar için `t = rates.time − off` hesaplıyor. `off`, botun `_daycombo_offset(sym)`
fonksiyonundan geliyor:
- `round((tick.time − now)/900) × 900`
- tek bir global önbellek, 1 saat geçerli

— [forexsai_demo_bot.py:2089–2103, 2561](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/forexsai_demo_bot.py)

Anlık ofset doğruysa, bugünkü tüm barlar ve tetik doğru UTC'de. Broker ofseti tam saat (UTC+2/+3) olduğundan H1 bar
sınırları Berlin saatine hizalı.

**Eski sadakat testi neden yetersizdi.** `caprev_live_fidelity.py`, `cm.build_dax("1h")` çerçevesinin hatalı `ts`'ini
"UTC" diye canlı fonksiyonlara verip `cm.events` ile kıyaslıyor. İki taraf aynı kaymış saatte çalıştığı için 54/54
eşleşme kod eşdeğerliğini kanıtlıyor, ekseni değil.
— [caprev_live_fidelity.py](/Users/melihcanodacioglu/Desktop/panel/research/canli_kart_20261009/caprev_live_fidelity.py)

**Yeni sadakat testi (A), düzeltilmiş gerçek-UTC barlarla.** Canlı kod 54 olay üretiyor; düzeltilmiş kartla ortak 54 gün,
54'ünde aynı tetik barı. Yalnız bir tarafta olan olay yok.
— [live_fidelity_fixed.py](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/live_fidelity_fixed.py),
[results/live_fidelity_fixed.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/live_fidelity_fixed.txt)

**Tek-ofset yan etkisi (B).** Bot 1500 H1 barın (≈ 2,5–3 ay) hepsini o anki ofsetle çeviriyor. Broker saati ABD DST
tarihlerinde değiştiği için son ABD geçişinden önceki barlar kayıyor:
- Mart geçişinden sonra 60 dk erken (araştırma hatasıyla aynı yön).
- Kasım geçişinden sonra 60 dk geç.

2019–2026'daki her geçişten sonraki 35 takvim günü taklit edildi (300 işlem günü, 14'ünde olay):
- **Hiçbir olay eklenmiyor ya da düşmüyor; hiçbir tetik barı değişmiyor.**
- 1 pdl farkı var (2023-03-13: 15312,1 → 15319,5; aynı tetik).
- 12 olayda dvol küçük oranda farklı (en büyük fark 2026-03-09: 0,01185 → 0,01239, ≈%4,6). Yani stop mesafesi en çok
  ≈%5 oynuyor.

— [results/live_fidelity_fixed.txt](/Users/melihcanodacioglu/Desktop/panel/research/nasdaq_derin_20261013/caprev_dax_recheck/results/live_fidelity_fixed.txt)

**Ofset ölçümünün sağlamlık riski (kod okuması, ölçülmedi):**
- `_daycombo_offset` tek bir global önbellek tutuyor (sembol başına değil) ve tik yaşını kontrol etmiyor.
- Önbellek bayat bir tikle yenilenirse ofset 15 dk'nın katları kadar hatalı olur ve 1 saat öyle kalır. Bayat tik örnekleri:
  NAS100'ün 21–22 UTC arası, hafta sonu.
- E5'teki "+1230 dk" vakası bu sınıftan.

CAPREV tetik pencereleri NDX 07–19 UTC ve DAX 06–14:30 UTC. Bu saatlerde NAS100 ve GER40 tikleri sürekli olduğu için
risk düşük, ama sıfır değil.
— [forexsai_demo_bot.py:2089–2103](/Users/melihcanodacioglu/Desktop/panel/yeni%20deneme/forexsai_demo_bot.py);
[KAPI_KAYIT_DEFTERI.md §1 E5](/Users/melihcanodacioglu/Desktop/panel/docs/KAPI_KAYIT_DEFTERI.md)

### Inferences
- **Canlı bot zaten "doğru" kuralı uyguluyor.** Kartta kanıtlanan kural ise kışın 1 saat kaymış bir versiyondu.
  2026-10-09'dan beri canlı ile kart arasında kış aylarında fark vardı. Bu fark ilk kez 2026-11-01'de (ABD standart
  saatine geçiş) devreye girecekti. Düzeltilmiş kanıt bu canlı kuralı en az eski kadar destekliyor. **Botta değişiklik
  gerekmiyor.**
- **Öneriler (zorunlu değil, yalnız öneri):**
  1. Ofseti barın kendi tarihine göre hesapla: broker = NY+7 kuralı ya da bar başına DST. Böylece geçiş sonrası 4 haftalık
     dvol/pdl kirlenmesi sıfırlanır (ölçülen etki ihmal edilebilir).
  2. `_daycombo_offset`'e sembol başına önbellek ve tik-yaşı koruması ekle; ör. `now − tick.time > 120 s` ise eski ofseti
     koru.
  3. Kart JSON'unu düzeltilmiş veriyle yeniden yaz ve E27'yi deftere ekle.
- **Deftere önerilen satırlar** (bu oturum yazmadı; koordinatör eklemeli):
  - §1, E27: `ndx_gate_forge/data/dax_{15m,30m,1h}.parquet` 2019+ her ABD standart saatinde (1. Pazar Kasım → 2. Pazar
    Mart) 60 dk ERKEN; omuz haftaları doğru (broker NY+7 − sabit 3 saat). `long_1h` NDX 2017-11-06 → 2018-02-26 60 dk
    GEÇ. Önlem: açılış/hacim sıçramasını ay × DST-sınıfı bazında iki çapayla kontrol et; nakit kapanış eşleşmesinde
    |fark| değil std kullan (vadeli bazı).
  - GF-22'ye ek: düzeltilmiş eksende 161 / 134, ortR +0,231, P %99,5, yarılar +0,091/+0,369, ×1,5 +0,227, tek-poz
    +0,176 → 6/6 LIVE korunuyor. DAX 54 / +0,212 (eski +0,171). Canlı kod düzeltilmiş olaylarla 54/54.

### Gaps
- Broker'ın NY+7 olduğu proje belgelerinden (`long_data.py` notu, E2) ve hatanın desenine uymasından çıkarıldı. Kutudaki
  canlı ofset log'u (`ayar`/ofset satırları) bu oturumda okunmadı.
- Canlı DAX tarafında henüz gerçek CAPREV işlemi yok; canlı tetik saatleri gözle doğrulanamadı.
- Evrim Paneli oturum notu (1. KURAL) ve defter satırı görev kısıtı nedeniyle yazılmadı. Koordinatör
  `python3 backend/scripts/evolution_session_log.py "CAPREV DAX saat ekseni yeniden doğrulaması: kart LIVE korunuyor" --files research/nasdaq_derin_20261013/caprev_dax_recheck/recheck_card.py`
  çalıştırmalı.

---

**CAPREV portföy kartı düzeltmeden sonra: LIVE.** Canlı botta (`yeni deneme/caprev_live.py`) değişiklik gerekmiyor.
Doğru Berlin seansını zaten uyguluyor. Yalnız sağlamlık önerileri var: bar-bazlı broker ofseti, sembol başına ve tik
yaşına duyarlı ofset önbelleği.
