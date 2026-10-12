# Sonuç — tekrar tekrar SL olan ortak işlem tipleri (2026-10-09)

Ön-kayıt: [PROTOCOL.md](PROTOCOL.md) · `run.py hazirla|analiz` · rapor `results/` + bu dosya.
Bot: 565 karar (NDX BUY 72 / SELL 237, USOIL BUY 102 / SELL 45, DAX 67, XAU 42). Giriş anı ≈100 özellik (islem_otopsi
`pre_*`/`geo_*`, 56 gösterge 1m–1h, panel modelleri, VIX, önceki işlem). NASDAQ bağımsız dönem: 2025-01 → 2026-06
(Dukascopy + cache 1m), 9.512 bot benzeri sentetik giriş (SL oranı BUY %42,8 / SELL %44,6). Not: özellikler yönle işaretli
(SELL'de "1h EMA50 uzaklığı yüksek" = fiyat EMA50'nin ÇOK ALTINDA; "1h RSI yüksek" = RSI DÜŞÜK).

## Sembol sembol
| sembol | alt-grup (plasebolu, ileri/geri) | benzer işlemler tekrar SL? (k=10 AUC / plasebo üst) | SL kümesi | hüküm |
|---|---|---|---|---|
| **NDX SELL** | **ileri GEÇTİ (+12pp vs %90 üst +5,5) · geri GEÇTİ (+20,7 vs +3,8)** | 0,51–0,53 / 0,56 | yok | **tek bulgu — aşağıda** |
| NDX BUY | ileri/geri geçmedi | gösterge 0,635 / 0,630 (sınırda), diğerleri geçmedi | yok | yok |
| USOIL BUY / SELL | geçmedi | bar 0,598 / 0,590 (sınırda) · SELL 0,33–0,44 (n=45) | tutarsız | yok |
| DAX | geçmedi | 0,40–0,45 | yok | yok (n=67) |
| XAU | "geçti" görünümü yapay (en iyi 10'un farkı 0) | 0,43–0,49 | — | yok (n=42) |
| NDX genel piyasa 2025-26 | — | 0,46–0,50 / 0,52 | — | benzer kurulum sonucu tekrarlamıyor |

## Tek bulgu: NDX SELL'de "düşüşü kovalamak" (çoğu VIXREG)
1h grafikte zaten çok düşmüşken açılan SELL'ler:
| koşul (giriş anı) | bot işlem | SL oranı (diğerleri) | engelleseydin | yarılar | 2025-26 genel piyasada |
|---|---:|---|---:|---|---|
| fiyat 1h EMA50'nin ≥2 ATR altında | 66 (VIXREG 60) | %59 (%36) | **+16,0R** [işlem başı +0,01…+0,46] | +9,2 / +6,8 | SL %41,1 vs %45,3 — tersi |
| 1h RSI ≤ 35 | 44 (VIXREG 41) | %64 (%37) | **+15,8R** [+0,10…+0,61] | +5,4 / +10,3 | SL %41,9 vs %44,9 — tersi |
| 1h RSI ≤ 40 | 78 | %55 (%36) | +15,2R | +4,7 / +10,5 | tersi |
| fiyat ≥1,5 ATR altında | 104 | %51 (%35) | +11,8R | +5,4 / +6,4 | tersi |
| 15m RSI ≤ 35 (kontrol) | 38 | %42 (%42) | +0,1R | −1,6 / +1,7 | — |
Aylar: Temmuz 57 işlem %60 SL −0,30R · Ağustos 14 işlem %43 · Eylül 8 işlem %62 (aynı yönde).

**Yorum:** genel piyasada aşırı düşmüşken satmak SL'ye yatkın DEĞİL (hatta biraz daha iyi); botta yatkın → etki BOTA ÖZGÜ.
En olası mekanizma: VIXREG'in SELL oyu panel (pulse) sinyallerinden geliyor ve bunlar düşüşün sonunda geç ateşliyor
→ bot tükenmiş düşüşte satıyor ("korku döner", meta-ders 2). Defterdeki **GF-15 kovalama endeksi** (C+, "bota özgü,
gölgeye bağlanmadı") ile aynı bulgu, bağımsız yöntemle; iki kronolojik yarıda da tutarlı. Eşik seçimi örneklem-içi →
kanıt sınıfı **B−**; canlı öncesi GÖLGE ölçüm gerekir. Defter IO-18.
