# C3D — C3b derin araştırma: zararlıları küçült, kazananları büyüt, "%40 iyileşme" — RAPOR (2026-11-24)

- **Ön kayıt:** `PROTOCOL.md` (TUR 1 + TUR 2 + TUR 3, her tur kendi sonuçlarından önce yazıldı).
- **Kod:** `src/motor.py` (ortak simülatör, dozlar), `src/duka.py` (Duka 1m işaretli $ kitabı), `src/bagimsiz.py` (MT5 + günlük setler),
  `src/otopsi.py`, `src/ayristir.py` (betimleyici).
- **Sonuç:** `results/duka*.json`, `results/dis*.json`, `results/dis_arac*.csv`, `results/ozet_tablo.csv`.
- **Koşma:** `src/` içinden `../../../.venv/bin/python duka.py [tur2|tur3]` ve `bagimsiz.py [tur2|tur3]` (≈ 15 sn).

## Kısa cevap
**Bağımsız veride ayakta kalan %40 iyileşme yok; bu yüzden garanti de verilemez.** 13 ön kayıtlı adayın 13'ü X.
- En yakını **K2** (stres ve derinliğe göre lot + 16:00 girişi). Duka NDX 2018–26'da aynı maks. düşüşte net **+%39,8**: zararlıların toplamı −%27, kârlıların +%24.
  **K1** aynı tabloda zararlıların toplamını **−%50** azaltıyor, kârlıları +%11 artırıyor, net +%30.
- Ama ikisi de C3b'de hiç kullanılmamış 38 ABD aracında (ETF'ler ve büyük hisseler, 1993–2026) çöküyor. Sharpe yalnız araçların yarısında artıyor,
  havuzda ×0,89–0,95. QQQ 1999–2026'da da düşüyor (0,99 → 0,93).
- Bu iyileşme 2018–26 NASDAQ'ının özelliği, C3b'nin genel yasası değil.

## Kaybedenlerin otopsisi (betimleyici)
- **132 işlem** (Duka 1m, birebir: +68,1 bp, isabet %77). Zararlıların toplamı −4.634 bp, kârlıların +13.621 bp.
- **Tutuşa göre:** ertesi gün dönen 82 işlem +126 bp. 3 gün tutulanlar −78, 5 gün tutulanlar −392 bp. Ama süre tavanı 3/5/8 daha önce denendi ve ≈ aynı çıktı (NX ızgarası).
- **Stres × derinlik** (dünkü VIX ≥ 18,4; z5 ≤ −1,072; KD-09'un yeniden üretimi):

| | sığ | derin |
|---|---|---|
| sakin | n 27, +37 bp | n 30, +31 bp |
| stres | n 35, +17 bp | **n 40, +162 bp (toplamın %72'si, isabet %95)** |

- Büyük zararlılar (2022-01, 2025-02, 2019-08, 2020-02) çoğunlukla sakin piyasada ya da zirveye yakın başlayan düşüşlerin ilk günleri. Zirveye %4'ten yakın 33 işlem ortalama +8 bp.
- **Seans ayrıştırması (sızıntısız):** pozisyon açıkken gece +32 bp, gün içi +12…+74 bp; ikisi de artı. Tek zayıf dilim girişin ilk yarım saati (15:30 → 16:00, −11 bp).
  - Tuzak: "çıkış olmayan günün gün içi dilimi" tanım gereği eksidir, çünkü çıkış kuralı yükselen günü arar. O tablo sızıntılı ve kullanılmadı (§1'e yazıldı).

## Adaylar ve sonuç
Ölçü Calmar (toplam / maks. düşüş, ölçekten bağımsız). "×1,40" = aynı maks. düşüşte net +%40. "Eşit risk" sütunları Duka'da aday, taban maks. düşüşüne ölçeklenince.

| aday | ne | Duka Calmar | Sharpe | ESKİ / YENİ Calmar | eşit risk: net / zarar / kâr | MT5 Calmar | taze 38 araç: Sharpe ↑ oranı / havuz | hüküm |
|---|---|---|---|---|---|---|---|---|
| taban | canlı C3b | 11,40 | 1,50 | — | — | — | — | — |
| D1 | stres∧derin 1, diğer ⅓ | ×1,07 | 1,53 | ×1,24 / ×1,05 | +%7 / **−%51** / −%7 | ×2,39 | %44 / ×0,89 | X |
| D2 | 0,25 + 0,375·stres + 0,375·derin | ×1,14 | 1,51 | ×1,04 / ×1,14 | +%14 / −%25 / +%5 | ×1,32 | %51 / ×0,95 | X |
| D3 | yalnız stres∧derin | ×0,91 | 1,39 | ×1,11 / ×0,88 | −%9 / **−%96** / −%29 | ×5,26 | %33 / ×0,73 | X |
| X1 | stres∧derin dışı ertesi gün çık | ×0,99 | 1,41 | ×1,04 / ×0,97 | −%1 / +%73 / +%16 | ×0,78 | %31 / ×0,93 | X |
| X2 | kâra dönmeden çıkma (≤ 5 gün) | ×0,89 | 1,28 | ×0,32 / ×0,99 | −%11 / +%31 / −%1 | ×0,69 | %49 / ×0,92 | X |
| K1 | D1 + 16:00 girişi | ×1,30 | 1,56 | ×1,87 / ×1,25 | +%30 / **−%50** / +%11 | ×3,43 | %44 / ×0,89 | X |
| **K2** | D2 + 16:00 girişi | **×1,398** | 1,58 | ×1,68 / ×1,37 | **+%40** / −%27 / +%24 | ×2,03 | %51 / ×0,95 | X (G1 1,398 < 1,40; G4 ✗) |
| V1 | VIX +%10 → çık (KQ-03'ten) | ×0,94 | 1,38 | ×0,99 / ×0,93 | −%6 / +%67 / +%11 | ×0,79 | %54 / ×0,83 | X |
| E16 | yalnız 16:00 girişi | ×1,30 | 1,61 (P 0,96) | ×1,49 / ×1,28 | +%30 / +%7 / +%25 | ×1,56 | (günlükte sınanamaz) | X (bilinen C+) |
| V1K2 | K2 + V1 | ×1,04 | 1,46 | ×1,85 / ×1,00 | +%4 / +%17 / +%7 | ×1,04 | %56 / ×0,81 | X |
| Y1 | çıkış 16:00 kapanışında | ×1,09 | 1,40 | ×1,11 / ×1,05 | +%9 / +%21 / +%12 | ×0,86 | (sınanamaz) | X |
| Y2 | çıkış gecesini tut (ertesi 09:30) | ×0,64 | 1,29 | ×0,51 / ×0,68 | −%36 / −%1 / −%28 | ×0,44 | %56 / ×1,04 | X |
| Y3 | E16 + Y2 | ×0,81 | 1,41 | ×0,74 / ×0,84 | −%19 / +%9 / −%12 | ×0,58 | %56 / ×1,04 | X |

- **Plasebo:** etiketler yıl içinde karıştırılınca D1/D2/K1/K2'nin Duka Calmar'ı plasebonun %95–100'ünü aşıyor. Yani 2018–26 NDX'inde yapı gerçek.
- **Görülmüş bağımsız setler** (karışık): ABD endeksleri 2018 öncesi D1 Sharpe ×1,53 (zayıf tabanlı GSPC/RUT'tan), NDX 1985–2018 0,69 → 0,73.
  Diğer dört broker endeksi ×0,85–1,03, 17 yabancı endeksin tabanı zaten eksi.
- **Neden Calmar artıyor da Sharpe artmıyor:** stres∧derin işlemleri aynı kriz aylarında kümeleniyor (E110). Doz maks. düşüşü kısaltıyor ama aylık oynaklığı azaltmıyor.
  Sakin dönemdeki zayıf işlemler ise zararlıları içerse de kitaba zaman çeşitlemesi getiriyor.
- **Koruyucu çıkışlar (V1, X1, X2) ve çıkış gecesi (Y2) zarar veriyor.** C3b'de çöküşün sürdüğü gün satmak dipte satmak demek; "korku döner" (§3) bir kez daha.

## Ne demek
1. **C3b'nin zararlı işlemleri, sakin dönem kârının bedeli.** Bunları azaltan her ağırlık 2018–26 NDX'inde Calmar'ı artırıyor, ama taze araçlarda ve uzun QQQ geçmişinde tutmuyor.
   Bu nedenle %40 bir "garanti" değil, tek dönemin ölçümü.
2. **Kanıtı en sağlam küçük iyileşme hâlâ 16:00 girişi (E16, C+):** Duka +%30 Calmar, Sharpe 1,50 → 1,61 (P 0,96), MT5 ×1,56. Ama diğer broker endekslerinde ×0,88; %40 çıtasının altında.
3. **Canlıya dokunulmadı.** Bir şey bağlanacaksa önerim yalnız E16'nın ya da K1/K2'nin GÖLGE izlemesi. Kart üretilmedi (2. KURAL için B gerekiyordu).
4. **Bu araştırma hattı kapandı.** Defterdeki önceki 40'a yakın C3b sınaması ve bu 13 aday birlikte okunduğunda, aynı veriyle yeni aday denemek gerçek iyileşme değil
   şans bulgusu üretir. Yeniden açmak için yeni veri (ör. 2027 ileri dönemi) ya da yeni bilgi sınıfı gerekir.

## Sınırlar
- Günlük setlerde karar = kapanış; 16:00 girişi ve Y1 sınanamaz (K ≡ D).
- I1 TUR 1'de doz için kullanıldı; TUR 2/3'te yarı taze.
- Calmar tek bir düşüş epizoduna bağlıdır; bu yüzden yarılar, MT5 ve taze set zorunlu tutuldu.
- Deneme sayacı: 13 aday (TUR 1: 7, TUR 2: 3, TUR 3: 3) + 2 betimleyici.
