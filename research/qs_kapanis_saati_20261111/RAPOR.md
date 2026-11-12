# QS-01 — QQQ kapanış saati stratejisi: rapor (2026-11-11)

Ön kayıt: `PROTOCOL.md`. Kod: `qs01.py` (broker M30, birincil + kör), `qs01_duka.py` (Dukascopy 1m, 15:05 birebir).
Sonuçlar: `results/m30.json`, `results/duka.json`, `results/islemler_<sembol>.csv`.

## Kural ne diyor
Ayı rejiminde (dün QQQ < SMA50) güne ≥ %0,6 boşlukla yukarı açılıp 15:00'te hâlâ açılışın üstünde ve gün aralığının
üst %23'ünde duran günlerde 15:05'te al, 16:00'da kapat. Fikir: düşüş trendinde gün boyu tutunan ralli, kapanışa doğru
açığa satıcıların kapatmasıyla (ve gün içi momentumla) son saatte de sürer. %1 stop pratikte süs: NAS100'de 67
işlemin hiçbirinde tetiklenmedi, en kötü işlem −46 bp (1m).

## Sonuç (ön-kayıtlı ölçütler)
| # | Ölçüt | Sonuç | |
|---|---|---|---|
| 1 | NAS100 M30 2018-05→2026-11 net ort > 0, P ≥ %90 | n 67, **+10,5 bp** (brüt +11,9), isabet %54, P 0,986 | ✓ |
| 2 | İki yarı ≥ 0 | +15,4 / +5,7 | ✓ |
| 3 | Spread × 1,5 | +9,8 | ✓ |
| 4 | Özgüllük (T0'a göre plasebo yüzdeliği ≥ %90) | T0 (her gün 15→16 uzun) −1,6 bp; yüzdelik %98,1 | ✓ |
| 5 | Kör US500 / US30 / US2000 havuz > 0, ≥ 2/3 artı | +3,4 (n 39, P 0,81) / −0,8 (n 46) / −2,0 (n 66); havuz ≈ −0,3 | **✗** |
| 6 | Dukascopy 1m birebir (15:05 girişi) > 0 | n 37, +9,0 bp (P 0,98); 15:00 girişi +9,9 | ✓ |
| — | Hacim ≥ 150 | 67 (yılda ~8; video "10 yılda 256" diyor, yeniden üretilemedi) | ✗ |

**Hüküm: C** (ön kayıt: 1–4 geçer, 5 düşer → C). Canlıya alma kartı açılmadı.

## Neden C, neden daha iyi değil
- **Yoğunlaşma:** en iyi 5 işlem hariç ortalama +10,5 → +2,6 bp. Kazanç 2020 (+44 bp, n 10) ve 2022 (+23 bp, n 16)
  ayı yıllarından. 2023→2026 arası 22 işlem ≈ −1,5 bp ort. Dukascopy'de de aynı: 2022 +21,5, sonrası ≈ 0 (yarı2 −0,04).
- **Kör endekslerde yok:** mekanizma (ayı rallisinde kapanış baskısı) genel olsaydı S&P / Dow / Russell'da da görünmeliydi.
- **Hangi koşul taşıyor (ablasyon, betimsel):** SMA50 koşulu çıkarılınca +2,7 bp → kenarın tamamı "ayı rejimi"nden.
  "15:00'te açılışın üstünde" (koşul 3) hiçbir şey katmıyor (çıkarılınca +13,4). Saf gün içi güç (koşul 3+4, rejimsiz)
  +2,3 bp → defterdeki zayıf son saat momentumu (GM-01, C) ile aynı mertebe.
- **Ekonomik boyut:** yılda ~8 işlem × ~10 bp ≈ 80 bp/yıl (KSG ≈ 860 bp/yıl). 100 bin $ pozisyonda ≈ 800 $/yıl, o da
  2020/2022 gibi bir ayı yılı gelirse.

## Sistemde var mı?
Yok. Canlı kurallar (C3b, CAPREV, KSG, ORB × VIX, çekiç) içinde ne bot ne backend ne decider bu kuralı uyguluyor.
En yakın akraba KSG (NK-06/07) ters yönden çalışır: son saat AŞAĞI kapanırsa 16:00'da alıp geceyi tutar. Bu kural son
saati yukarı oynar ve 16:00'da çıkar; ikisi aynı güne denk gelirse sırayla çalışabilirler (çakışma yok).

## Kanıt hatası / yöntem notu
Yeni tuzak yok. Videodaki işlem sayısının (256/10 yıl) bizim tanımla ~3 kat fazla olması, kaynağın farklı dönem ya da
gevşek tanım kullandığını düşündürüyor; sayı doğrulanamadı.
