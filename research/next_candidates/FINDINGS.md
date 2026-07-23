# Sıradaki Adaylar Denetimi — 2026-07-23

Yöntem: sızıntısız 1m replay (giriş = olay anı fiyatı, çözüm sonraki barlar, SL-önce
konservatif), 30 gün (2026-06-20 → 07-23), epizod-dedup (60dk boşluk). `audit.py`.

## A) premium_zone_buy vetosu (Precision Veto likidite katmanı)

| Sembol | Bloklanan epizod | WR | totR | Başabaş | Karar |
|---|---|---|---|---|---|
| NDX.INDX | 18 | **%16.7** | **−12.8R** | %57.9 | ✅ **VETO HAKLI — kalsın** |
| USOIL.FOREX | 83 | **%71.1** | **+17.2R** | %58.9 | ❌ **VETO PARA KAYBETTİRİYOR** |

Yorum: USOIL momentum-continuation edge'i tanım gereği fiyat range tepesindeyken
(premium) tetikleniyor — "premium'da alma" SMC kuralı bu sembolün doğrulanmış
edge'iyle yapısal çelişkide. **Aksiyon:** `PREMIUM_ZONE_BUY_EXEMPT=USOIL.FOREX`
(default) — USOIL premium-BUY vetodan muaf, NDX'te veto aynen duruyor.

## B) CHREV (mean-reversion) rejim kapısı — 30m z-epizod taraması

Kapı adayı: **kaynak=channel VE kanal eğimi lehte** (BUY→eğim≥0, SELL→eğim≤0).

| Sembol/Yön | Tümü WR (totR) | Kapı GEÇEN | Kapı ELEYEN | Başabaş | Karar |
|---|---|---|---|---|---|
| GDAXI BUY | %54.5 (−4.9R) | **%73.7 (+2.9R)** | %28.6 (−7.8R) | %64.0 | **KAPILI devam** |
| NDX SELL | %59.0 (+0.7R) | **%68.8 (+3.0R)** | %52.2 (−2.3R) | %57.9 | **KAPILI devam** |
| NDX BUY | %40.0 (−13.9R) | %31.8 (−9.9R) | — | %57.9 | **KAPALI** (kapı da kurtarmıyor) |
| USOIL SELL | %40.6 (−9.9R) | %50.0 (−1.2R) | — | %58.9 | **KAPALI** |

Çarpıcı yan bulgu: **vwap-kaynaklı tetikler zehirli** (GDAXI BUY vwap: WR %25,
−7.3R; kanal-kaynak: %71.4, +2.5R) — eski "vwap additive" damıtması bu dönem
için tutmadı. Kapı vwap'ı zaten eliyor.

Uygulama: `check_channel_reversion` içinde kanıt tablosu (config
`CHREV_MODE_OVERRIDE` ile ezilebilir) + `channel_filter.channel_slope_atr`.
Dünkü canlı kanamayla tutarlı (GER40 CHREV düşen-kanal günü 1W/3L −1657$).

⚠️ Sınırlama: tarama pulse3-teyidi olmadan saf z-koşulunu test eder (botun gerçek
tetiklerinin üst kümesi); n'ler 32-45. Kapılar canlıda logla izlenmeli.

## C) VIXREG SELL terfi kriteri (ana scope'a alma)

Canlı kanıt henüz yetersiz: sabır-kapılı dönemde n=11 (7W/4L, +600$ — umut verici
ama küçük). **Ön-kayıtlı terfi kriteri:** magic ...71 SELL işlemlerinde
n≥30 VE WR > %57.9 (80/110 başabaşı) VE toplam R > 0 → NDX:SELL ana scope'a
(momentum filtresi + sabır kapısıyla) eklenir. Ölçüm: MT5 deal geçmişi export'u,
~2026-08-05 civarı. Karar o güne kadar BEKLEMEDE.
