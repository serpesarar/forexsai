# NDX 1h / 4h büyük fitil → ters yön (ret) — rapor (2026-11-06)

Ön kayıt: `PROTOCOL.md` (sonuçlardan önce). Kod: `engine.py` (tüm mumlar × yön × gecikme × SL × TP sonuç matrisi),
`run.py` (hüküm), `diag.py` (tanılar, post-hoc). Çıktılar: `results/hukum.json`, `results/tani.json`, `logs/*.log`.

## Soru
Büyük üst fitilli 1h/4h mum kapandıktan 0–20 dk sonra SAT, büyük alt fitilli mumdan sonra AL; TP/SL ızgarasıyla
kârlı bir kapı var mı? Kullanıcının gerekçesi: büyük hareketlerin sonunda fitiller büyür, yön kırılır, düzeltme gelir.

## Veri ve icra
- NDX 1m Dukascopy bid/ask, KEŞİF 2024-01 → 2025-06, TEST 2025-07 → 2026-11 (mühürlü). Saat ekseni denetlendi: aylık en
  oynak dakika 34 ayın 29'unda 09:30 ET.
- Giriş HTF kapanışından D dk sonraki 1m açılışı (SAT bid, AL ask), çıkış 1m'de ask/bid ile, aynı barda SL+TP → SL.
- BAĞIMSIZ: NDX 1h arşivi 2016-06 → 2023-12 (giriş sonraki 1h açılışı, spread 1,5).
- Motor iki bağımsız yoldan (matris ↔ tek işlem simülatörü) 5.129 rastgele işlemde birebir aynı sonucu verdi.

## 1. Ön-kayıtlı 8 hipotez (s ≥ 0,5, w ≥ 0,5 ATR, SL = fitil ucu + 0,1 ATR, TP 1R, D = 5 dk)

| ID | TF / yön / bağlam | KEŞİF n · R | TEST n · R · P | TEST ayna (devam) | BAĞIMSIZ 2016-23 | hüküm |
|---|---|---|---|---|---|---|
| H1 | 1h üst → SAT | 429 · −0,106 | 341 · **−0,127** · 0,008 | +0,028 | 2.305 · −0,128 | X |
| H2 | 1h alt → AL | 706 · −0,043 | 584 · **−0,095** · 0,007 | +0,014 | 3.182 · −0,081 | X |
| H3 | 4h üst → SAT | 59 · +0,002 | 51 · +0,129 · 0,84 | −0,172 | (4h, tanı) 337 · −0,185 | X |
| H4 | 4h alt → AL | 123 · −0,001 | 105 · −0,023 · 0,38 | −0,071 | (4h, tanı) 602 · +0,074 | X |
| H5 | 1h üst → SAT, ≥2 ATR yükseliş sonrası | 52 · −0,150 | 39 · +0,006 · 0,51 | −0,068 | 316 · −0,168 | X |
| H6 | 1h alt → AL, ≥2 ATR düşüş sonrası | 91 · +0,017 | 77 · −0,165 · 0,07 | −0,015 | 416 · −0,063 | X |
| H7 | 4h üst → SAT, yükseliş sonrası | 10 · +0,276 | 7 · −0,731 | +0,714 | (4h, tanı) 27 · −0,084 | X |
| H8 | 4h alt → AL, düşüş sonrası | 23 · +0,124 | 16 · −0,173 · 0,21 | −0,178 | (4h, tanı) 60 · **+0,288** · 0,994 | X (iz, aşağıda) |

1h'te iki yön de üç dönemde (2016-23, 2024-25, 2025-26) negatif. Ters yön (devam) sıfır civarında, yani fitilin
ret yönü devamdan kötü. 4h üst fitil SAT'ın TEST'teki +0,13'ü 2016-23'te −0,19 çıktı.

## 2. Deneme-yanılma ızgarası (14.400 hücre) ve seçim düzeltmesi

**Tuzak (E100):** Fitil-ucu stoplu kuralın tabanı "tüm mumlarda aynı kural" diye kurulursa yanıltır. Rastgele mumun ucu
kapanışa yapışık olduğundan stop dar kalır, spread R'yi eritir (taban −0,34R). Büyük fitilli mumda ise stop kendiliğinden
geniş. Bu yüzden ilk koşuda 1h hücreleri tabana göre +0,26R "fark" ve p_sel = 0,00 gösterdi, oysa mutlak R hep negatifti
(en iyi 1h hücresi TEST −0,093R, isabet %60, TP 0,5R). Tanı koşusu ızgarayı yalnız ATR stoplarıyla tekrarladı:

| TF / yön | t_max | boş %95 | p_sel | en iyi hücre TEST farkı | ilk-20 TEST farkı (pozitif) | KEŞİF R > 0,10 olan hücrelerin TEST R'si (pozitif oranı) |
|---|---|---|---|---|---|---|
| 1h üst → SAT | 2,79 | 3,79 | 0,44 | −0,040 | −0,027 (4/20) | 73 hücre → −0,091 (%22) |
| 1h alt → AL | 3,68 | 3,89 | 0,11 | −0,022 | −0,009 (6/20) | 495 → −0,051 (%29) |
| 4h üst → SAT | 3,42 | 3,45 | 0,055 | +0,053 (n 37) | +0,058 (15/20) | 236 → −0,036 (%38) |
| 4h alt → AL | 1,97 | 3,54 | 0,70 | −0,136 | −0,092 (2/20) | 442 → −0,103 (%13) |

Izgaranın en iyileri tesadüften ayırt edilemiyor. KEŞİF'te kârlı görünen yüzlerce TP/SL/gecikme kombinasyonu TEST'te
ortalama negatife dönüyor. 4h üst SAT'ın sınırdaki izini (p 0,055) 2016-23 bağımsız dönemi çürütüyor (−0,12…−0,19R).

## 3. Tanılar
- **Gecikme (5/10/15/20 dk):** etkisi yok. 1h SAT her D'de −0,01…−0,10. Hiçbir D iki dönemde birden artı değil.
- **Teyit** (girişte fiyat sinyal kapanışından ret yönüne gitmiş mi): 1h'te teyitli işlemler teyitsizlerden iyi değil
  (AL: teyitli −0,05/−0,08, teyitsiz +0,00/−0,02).
- **Yıl / seans:** H1 2024 −0,14, 2025 −0,07, 2026 −0,14. Hiçbir seans iki dönemde artı değil. En iyi 5 gün çıkınca H1 −106R, H2 −103R.
- **Tek pozisyon, spread ×1,5:** sonucu değiştirmiyor.

## 4. Tek iz: 4h alt fitil + öncesinde ≥ 2 ATR düşüş → AL ("korku döner")
- 2016-23 (1h icra): n 60, +0,29R (tip stop) / +0,33R (1 ATR stop), P %99,4–99,7, 8 yılın 5'i artı.
- 2024-26, aynı 1h icra: n 42, −0,01 / +0,10, P %47–75; 2026 −0,20…−0,33.
- 2024-26, 1m icra (ön-kayıtlı H8): KEŞİF +0,12 (23), TEST −0,17 (16).
- Sonuç: **C**. Mekanizma projenin tek sağlam ilkesiyle ("korku döner, coşku dönmez", §3-11; CAPREV, TR-C3) tutarlı.
  Ama son 3 yılda tutmuyor ve olay sayısı yılda ~10. Aynası (yükseliş sonrası üst fitil SAT) her dönemde negatif.

## Hüküm
**X.** NDX 1h/4h büyük fitilden sonra ters yönde (fitilin ret yönünde) gecikmeli girişin, 14.400 TP/SL/gecikme/eşik
kombinasyonunun hiçbirinde tesadüften ayırt edilebilen, bağımsız dönemde tutan bir kârı yok. Önceki bulgularla aynı yön:
fitil süpürmesi dönüş değil, devam eğilimli (MZ, §3-15). Üst fitil SAT ("coşku dönmez") her dönemde en kötü kol.
"Büyük hareketten sonra fitil" bağlamı (k = 1…3) da artıya çevirmiyor.

Canlıya ya da gölgeye bağlanacak bir kural yok. 4h düşüş sonrası alt fitil AL izi C olarak deftere yazıldı;
yeni veri birikirse (≥ 30 yeni olay) yeniden bakılabilir.
