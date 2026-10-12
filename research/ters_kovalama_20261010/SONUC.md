# Sonuç — "düşüşü kovalayan" NDX SELL anlarında TERS (BUY) işlem (2026-10-10)

`run.py` (ön-kayıt docstring'de) · `results/rapor.txt`. Koşullar IO-18'den sabit: C1 = 1h fiyat EMA50'nin ≥2 ATR altında,
C2 = 1h RSI ≤ 35. Ters işlem BUY, sinyalden sonraki dakika açılışı + spread; 12 ATR(1h) braketi + 5 zaman çıkışı.

| kaynak | n (C1/C2) | sonuç | yorum |
|---|---|---|---|
| 1) botun gerçek SELL'lerinin tersi | 70 / 43 | brakettlerin çoğu + ve iki yarıda + (ör. C1 SL1/TP2 **+0,63R**, C2 SL1/TP1.5 **+0,63R**) | ÖRNEKLEM-İÇİ: koşul bu işlemlerin SL'ye yatkın olmasından bulundu (IO-18) → döngüsel |
| 2) panel pulse1/2 SELL sinyallerinin tersi (VIXREG'in oy kaynağı) | 52 / 33 (VIX<18,4: 43 / 28) | braketler ≈0 ya da −; yalnız C2 60 dk +0,17…+0,21R geçti; ertesi gün 16:00 **−0,42R** | yarı-bağımsız kaynakta etki büyük ölçüde kayboluyor; 68 testte 2 "geçen" ≈ tesadüf beklentisi (~3) |
| 3) sinyalsiz genel piyasa 2025-26 (aşırı düşmüşken BUY) | 720 / 471 | braketler **−0,06…−0,09R**, zaman çıkışları ≈0 | "aşırı düşmüşte al" genel bir kenar DEĞİL |

## Hüküm
Tersine çevirme yalnız botun kendi işlemlerinde (koşulun bulunduğu veride) kazandırıyor; aynı mantık VIXREG'in sinyal
kaynağında zayıflıyor, genel piyasada negatif. Elimizdeki kanıt "bu SELL'leri açma" (IO-18 veto, B−) yönünde; "tersine BUY aç"
ek risk alıp örneklem-içi bir etkiye bahis yapmak olur → ELENDİ (canlı strateji olarak). Gölge kayıtta veto ile birlikte
"ters BUY olsaydı (SL1/TP1,5 ATR1h ve 120 dk)" sonucu da bedavaya ölçülebilir. Defter IO-19.
