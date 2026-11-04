# Pine Motoru — sonuç tabloları (otomatik)

## Kapsama

- Çalıştırılan script: **32741** (kütüphaneler hariç)
- En az bir sembolde çalışıp ≥1 tepki üreten (uygulanan): **23361** (%71.4; boost ağırlıklı %72.7)
- NDX durum dağılımı: {'ok': 27552, 'unsupported': 3254, 'timeout': 995, 'runtime_error': 888, 'parse_error': 49, 'transpile_error': 3}
- Popülerliğe göre uygulanma oranı: {'en az popüler %25': 0.663, '2. çeyrek': 0.725, '3. çeyrek': 0.748, 'en popüler %25': 0.717}
- `lookahead_on` bayraklı script: 1380

En sık uygulanamama nedenleri:

- request.security başka sembol: 2064
- geçiş chart : 941
- PineError: 315
- bar : 304
- geçiş chart D: 201
- TypeError: 175
- IndexError: 113
- bilinmeyen ad footprint: 111
- ZoneInfoNotFoundError: 65
- alt TF S verisi yok: 57
- bilinmeyen fonksiyon syminfo.ticker: 56
- ValueError: 44
- çok fazla geçiş: 41
- renko: 40
- bilinmeyen fonksiyon offset_fn: 35

## Hüküm (sembol başına, 1h son 12.000 bar, 6 ufuk)

| Sembol | Tepki durumu | Seçilen | Kanıtlı | Boş beklenti (q99) | p | Doğr. geçen/ters | Kasa geçen/ters | Keşifte eşik üstü ufuk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NDX | 303,438 | 500 | **2** | 1.25 (4) | 0.355 | 12/21 | 10/24 | 1/5 |
| DAX | 303,510 | 500 | **0** | 1.25 (4) | 1.0 | 16/15 | 10/14 | 1/5 |
| XAU | 292,261 | 500 | **2** | 1.25 (4) | 0.355 | 22/8 | 12/12 | 3/5 |
| USOIL | 293,251 | 500 | **2** | 1.25 (4) | 0.355 | 23/4 | 28/6 | 0/5 |

## Tekrarlanma (doğrulamayı geçen adaylar; boş beklenti her yön için %5)

| Pencere | Ölçüm | Aynı yön anlamlı | Ters yön anlamlı |
|---|---:|---:|---:|
| geçmiş 12.000 bar (aynı sembol, 1h) | 70 | 0 (%0.0) | 1 (%1.4) |
| son pencereden önceki tüm tarih (aynı sembol, 1h) | 68 | 4 (%5.9) | 3 (%4.4) |
| diğer semboller (aynı dönem, 1h) | 196 | 12 (%6.1) | 8 (%4.1) |
| 15m (aynı sembol, son 12.000 bar) | 72 | 6 (%8.3) | 1 (%1.4) |
| 1d (aynı sembol, son 12.000 bar) | 69 | 2 (%2.9) | 3 (%4.3) |
| 1m (aynı sembol, son 12.000 bar) | 62 | 5 (%8.1) | 5 (%8.1) |
| 4h (aynı sembol, son 12.000 bar) | 70 | 8 (%11.4) | 2 (%2.9) |
| 5m (aynı sembol, son 12.000 bar) | 67 | 7 (%10.4) | 1 (%1.5) |

## Kanıtlı adaylar (6)

| Sembol | h | Script | Tepki | Eş | Yön | Keşif z | Doğr. z | Kasa z | Kasa isabet/taban | Past z |
|---|---:|---|---|---|---|---:|---:|---:|---|---:|
| NDX | 1 | Pivot HL Trading Setup | `plot12|Stoploss|px-` | `R:PUB;a63e062f0ebd4a169a01be7234a1cee4|plot18|F2|dn` | SELL | 3.74 | 2.16 | 1.93 | 0.545/0.469 | 0.12 |
| NDX | 1 | Test - Symbiotic Exiton Measure Enthropi | `plot18|F2|dn` | `R:PUB;75eb4ae17c234d60bcb66accbc5992af|plot50|Volatility|dn` | SELL | 3.71 | 1.77 | 1.79 | 0.587/0.471 | -0.61 |
| XAU | 2 | Fibonacci Retracement | `plot5|70.6%|px-` | `GCM:ALLIGATOR:stack+` | BUY | 4.37 | 1.72 | 1.80 | 0.593/0.477 | 0.95 |
| XAU | 4 | Undertow [WT + RSI] | `shape18|Buy (weak)|on` | `GCM:CKSTOP:brk+` | BUY | 4.23 | 1.98 | 2.01 | 0.528/0.445 | -0.79 |
| USOIL | 1 | Hurst Fractal Regime Atlas [JOAT] | `plot55|HFA atlas grade hidden|up` | `GCM:AO:color-` | BUY | 4.80 | 1.99 | 1.94 | 0.523/0.498 | -0.65 |
| USOIL | 1 | PSAR Laboratory [DAFE] | `alert164|PSAR Lab Flip|on` | `GCM:ROOFING:zero+` | BUY | 4.11 | 2.54 | 2.27 | 0.627/0.501 | 0.82 |
