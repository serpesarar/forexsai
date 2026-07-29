# ATR SL Testi — USOIL + DAX (2026-07-29)

Protokol NDX ile birebir aynı: 2026-02-11 → 07-29 (5.5 ay), zaman kayması
düzeltilmiş, trend+konum kapılı, karar anına kadarki barlar, çözüm sonraki 1m
barlarla, aynı barda TP+SL → konservatif SL, gün-bloklu bootstrap.
Veri: USOIL 39.852 sinyal / 164.600 1m bar · DAX 14.043 sinyal / 148.513 bar.

## Sonuçlar (kapılı, sabit TP + ATR-ölçekli SL)

### GDAXI (sabit: TP 67p / SL 119p)
| Geometri | n | WR | totR | aylık poz. | OUT-R |
|---|---|---|---|---|---|
| BUY sabit (canlı) | 110 | **%73.6** | +16.61 | 4/6 | +0.83 |
| BUY SL 2.0×ATR | 170 | %56.5 | **+72.41** | **6/6** | +17.22 |
| SELL sabit (canlı) | 182 | **%81.9** | +50.89 | 4/6 | +14.03 |
| SELL SL 1.5×ATR | 293 | %54.6 | **+130.12** | 5/6 | +45.77 |
| SELL SL 2.0×ATR | 238 | %64.7 | +110.36 | 5/6 | +40.00 |

### USOIL (sabit: TP %1.04 / SL %1.49)
| Geometri | n | WR | totR | aylık poz. | OUT-R |
|---|---|---|---|---|---|
| BUY sabit (canlı) | 402 | **%71.9** | +88.72 | 4/6 | +18.66 |
| BUY SL 2.0×ATR | 699 | %46.1 | +132.29 | 4/6 | +39.03 |
| BUY SL 3.0×ATR | 498 | %59.2 | +111.81 | 5/6 | +28.44 |
| SELL sabit (canlı) | 354 | **%71.5** | +75.59 | **6/6** | +31.57 |
| SELL SL 2.0×ATR | 520 | %51.9 | +150.41 | **6/6** | +84.15 |
| SELL SL 3.0×ATR | 396 | %63.6 | +108.92 | **6/6** | +53.35 |

Kapısız referans: USOIL BUY −13.29R · USOIL SELL −47.60R · DAX BUY −42.78R ·
DAX SELL +6.55R → **kapılar burada da belirleyici** (NDX bulgusunun teyidi).

## ⚠️ İki kritik uyarı

### 1. ATR-SL kazanma oranını DÜŞÜRÜYOR
Her sembolde aynı örüntü: SL daralıyor (DAX'ta 119→47p, USOIL'de 1.44→0.69),
RR yükseliyor, toplam kâr artıyor **ama WR düşüyor**:
- DAX BUY %73.6 → %56.5 · DAX SELL %81.9 → %64.7
- USOIL BUY %71.9 → %46.1 · USOIL SELL %71.5 → %51.9

Bu, `ATR_GEOMETRY_DEFAULT` notundaki kullanıcı kararıyla çelişiyor:
*"varsayılan KAPALI — kullanıcı yüksek kazanma oranı istiyor, uzak-hedef/
düşük-WR profili istemiyor"*.

**Aynı ödünleşim NDX SELL'de de vardı** (%73.4 → %61.1) ve ben uygulama
sırasında bunu yeterince vurgulamadım — burada açıkça kayda geçiriyorum.

### 2. USOIL kaymaya KIRILGAN, DAX değil
Sürtünmeyi 1×/2×/3× yaparak test ettim (totR):

| | 1× | 2× | 3× |
|---|---|---|---|
| **DAX** SELL SL2.0×ATR | +110 | +98 | **+90** |
| **DAX** SELL sabit | +51 | +43 | +40 |
| **USOIL** BUY SL1.5×ATR | +166 | **−85** | **−523** |
| **USOIL** BUY SL2.0×ATR | +132 | +30 | **−134** |
| **USOIL** BUY SL3.0×ATR | +112 | +57 | −1 |
| **USOIL** BUY sabit | +89 | +74 | **+59** |

Sebep yapısal: sürtünme/SL oranı DAX'ta %2.4, USOIL'de %4.4 (fiyat düşük,
spread oransal yüksek). USOIL'de icra sorunları ayrıca kanıtlı (07-24'te
15+ adet `retcode=10016`, hafızada "USOIL RR 0.37" otopsi bulgusu).
**DAX'ta ATR-SL her kayma seviyesinde sabitten iyi; USOIL'de 3× kaymada
sabit kazanıyor.**

## Önerim (uygulanmadı — karar senin)

| Sembol | Öneri | Gerekçe |
|---|---|---|
| **DAX BUY** | SL 2.0×ATR | 6/6 ay pozitif, 3× kaymada bile +34, kâr 4.4× |
| **DAX SELL** | SL 2.0×ATR | 3× kaymada +90 (sabit +40), kâr 2.2× |
| **USOIL** | **SL 3.0×ATR veya dokunma** | 2.0×ATR 3× kaymada −134; 3.0×ATR sabite yakın (SL'in %72-88'i) ama uyumlu |

Karar için iki soru: (a) WR düşüşünü kabul ediyor musun — daha az kazanan
işlem, ama kazandığında daha büyük? (b) USOIL'de ihtiyatlı 3.0×ATR mi, hiç
dokunmamak mı?

**Dosya:** `multi_grid.py`
