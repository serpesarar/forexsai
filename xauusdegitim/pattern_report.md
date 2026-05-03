# Pattern Mining Raporu
_2026-05-03T22:16:52.234092Z — son 60 gün — 50000 resolved sinyal_

**Yöntem:** Decision Tree (max_depth=4) + Random Forest feature importance.
Her leaf bir kural. min_samples_leaf=20, class_weight=balanced.

**Yorum kılavuzu:**
- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)
- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)
- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli

---

## GLOBAL — tüm sembol & model
- Toplam çözülmüş: **50000**  ·  Baseline win-rate: **65.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (30 W / 0 L = 30 trade · +34.8pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 = [65,75)`
   - `session = overlap`
   - `adx_H1 = [18,25)`

**2. Win-rate 98.8%** (514 W / 6 L = 520 trade · +33.6pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**3. Win-rate 97.9%** (141 W / 3 L = 144 trade · +32.7pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H1 ≠ [30,50)`
   - `adx_H4 = [25,35)`

**4. Win-rate 95.9%** (188 W / 8 L = 196 trade · +30.7pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

**5. Win-rate 87.9%** (131 W / 18 L = 149 trade · +22.7pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H1 ≠ [30,50)`
   - `adx_H4 ≠ [25,35)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.3%** (30 W / 80 L = 110 trade · -37.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `bb_extreme_upper = False`
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket = [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H4=[25,35)` | 0.0575 |
| 2 | `H4_ema_stack=NA` | 0.0463 |
| 3 | `H4_adx_label=trending` | 0.0443 |
| 4 | `H4_ema_stack=up` | 0.0428 |
| 5 | `H1_ema_stack=NA` | 0.0421 |
| 6 | `H4_adx_label=NA` | 0.0412 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0366 |
| 8 | `rsi_H4=[50,65)` | 0.0366 |
| 9 | `adx_H4=NA` | 0.0337 |
| 10 | `M30_ema_stack=mixed` | 0.0331 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0326 |
| 12 | `rsi_H4=NA` | 0.0304 |
| 13 | `session=overlap` | 0.0250 |
| 14 | `mtf_trend=mixed` | 0.0216 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0199 |

---

## GDAXI.INDX · emel
- Toplam çözülmüş: **132**  ·  Baseline win-rate: **72.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.4%** (38 W / 5 L = 43 trade · +16.4pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.3225 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.2046 |
| 3 | `session=europe` | 0.1748 |
| 4 | `session=overlap` | 0.1306 |
| 5 | `session=asia` | 0.0868 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0807 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **190**  ·  Baseline win-rate: **85.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +14.7pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 96.9%** (31 W / 1 L = 32 trade · +11.6pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [50,60)`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +9.9pp vs baseline)
   - `session ≠ overlap`
   - `session = europe`
   - `ml_confidence_bucket = [60,70)`

**4. Win-rate 85.7%** (42 W / 7 L = 49 trade · +0.4pp vs baseline)
   - `session ≠ overlap`
   - `session = europe`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [−∞,50)`

**5. Win-rate 75.6%** (34 W / 11 L = 45 trade · -9.7pp vs baseline)
   - `session ≠ overlap`
   - `session = europe`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2436 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.2249 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.1622 |
| 4 | `session=asia` | 0.1515 |
| 5 | `session=europe` | 0.1468 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0629 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0081 |

---

## GDAXI.INDX · ml:balanced
- Toplam çözülmüş: **124**  ·  Baseline win-rate: **75.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.1%** (40 W / 7 L = 47 trade · +9.3pp vs baseline)
   - `session = overlap`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · -0.8pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.3571 |
| 2 | `session=overlap` | 0.3566 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1589 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0934 |
| 5 | `session=asia` | 0.0339 |

---

## GDAXI.INDX · ml:full_power
- Toplam çözülmüş: **151**  ·  Baseline win-rate: **75.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.3%** (44 W / 7 L = 51 trade · +10.8pp vs baseline)
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.3041 |
| 2 | `session=overlap` | 0.2953 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1822 |
| 4 | `session=asia` | 0.1128 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.1056 |

---

## GDAXI.INDX · ml:main
- Toplam çözülmüş: **177**  ·  Baseline win-rate: **78.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.4%** (19 W / 3 L = 22 trade · +8.4pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`

**2. Win-rate 84.8%** (28 W / 5 L = 33 trade · +6.8pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 78.6%** (55 W / 15 L = 70 trade · +0.6pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.2779 |
| 2 | `session=overlap` | 0.2243 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1910 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1706 |
| 5 | `session=asia` | 0.1361 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **1433**  ·  Baseline win-rate: **57.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 31.1%** (66 W / 146 L = 212 trade · -26.5pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.3199 |
| 2 | `session=overlap` | 0.1850 |
| 3 | `session=europe` | 0.1558 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.1183 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0708 |
| 6 | `session=asia` | 0.0693 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0466 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0344 |

---

## GDAXI.INDX · pulse2
- Toplam çözülmüş: **610**  ·  Baseline win-rate: **74.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.2%** (23 W / 4 L = 27 trade · +11.1pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session ≠ asia`
   - `session ≠ europe`
   - `ml_confidence_bucket ≠ [50,60)`

**2. Win-rate 82.9%** (97 W / 20 L = 117 trade · +8.8pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session ≠ asia`
   - `session ≠ europe`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 77.7%** (171 W / 49 L = 220 trade · +3.6pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session ≠ asia`
   - `session = europe`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.2561 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.2473 |
| 3 | `session=asia` | 0.2117 |
| 4 | `session=overlap` | 0.1711 |
| 5 | `session=europe` | 0.0780 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0349 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **1249**  ·  Baseline win-rate: **70.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.1%** (51 W / 5 L = 56 trade · +20.6pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = asia`
   - `ml_confidence_bucket ≠ [60,70)`

**2. Win-rate 80.3%** (188 W / 46 L = 234 trade · +9.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session ≠ asia`
   - `session = overlap`

**3. Win-rate 80.0%** (20 W / 5 L = 25 trade · +9.5pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`
   - `session ≠ overlap`

**4. Win-rate 78.7%** (59 W / 16 L = 75 trade · +8.2pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`
   - `session = overlap`

**5. Win-rate 76.4%** (42 W / 13 L = 55 trade · +5.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = asia`
   - `ml_confidence_bucket = [60,70)`

**6. Win-rate 76.0%** (389 W / 123 L = 512 trade · +5.5pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session ≠ asia`
   - `session ≠ overlap`

**7. Win-rate 75.0%** (18 W / 6 L = 24 trade · +4.5pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.3207 |
| 2 | `session=europe` | 0.1560 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.1395 |
| 4 | `session=overlap` | 0.1279 |
| 5 | `session=asia` | 0.1040 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0927 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0437 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0154 |

---

## GDAXI.INDX · smc
- Toplam çözülmüş: **273**  ·  Baseline win-rate: **58.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +41.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ europe`

**2. Win-rate 87.6%** (78 W / 11 L = 89 trade · +29.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = europe`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.6%** (34 W / 89 L = 123 trade · -30.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.4614 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.4075 |
| 3 | `session=asia` | 0.0588 |
| 4 | `session=europe` | 0.0418 |
| 5 | `session=overlap` | 0.0305 |

---

## NDX.INDX · emel
- Toplam çözülmüş: **172**  ·  Baseline win-rate: **57.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.8%** (73 W / 22 L = 95 trade · +19.8pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session ≠ us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.7%** (2 W / 21 L = 23 trade · -48.3pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session ≠ us`

**2. Win-rate 32.4%** (11 W / 23 L = 34 trade · -24.6pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2930 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.2767 |
| 3 | `session=overlap` | 0.2149 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1780 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0373 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **189**  ·  Baseline win-rate: **78.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (22 W / 2 L = 24 trade · +12.9pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**2. Win-rate 87.2%** (34 W / 5 L = 39 trade · +8.4pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 83.8%** (31 W / 6 L = 37 trade · +5.0pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 82.5%** (33 W / 7 L = 40 trade · +3.7pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2242 |
| 2 | `session=overlap` | 0.1665 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1304 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.1060 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0708 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0541 |
| 7 | `rsi_extreme=False` | 0.0368 |
| 8 | `exhaustion_up=False` | 0.0216 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0212 |
| 10 | `volatility_regime=high` | 0.0181 |
| 11 | `bb_extreme_upper=False` | 0.0169 |
| 12 | `vix_chg1d=[-3,0)` | 0.0150 |
| 13 | `rsi_H1=[65,75)` | 0.0136 |
| 14 | `rsi_extreme=NA` | 0.0113 |
| 15 | `near_support=False` | 0.0104 |

---

## NDX.INDX · ml:balanced
- Toplam çözülmüş: **115**  ·  Baseline win-rate: **79.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.6%** (33 W / 6 L = 39 trade · +5.5pp vs baseline)
   - `session ≠ us`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 79.2%** (19 W / 5 L = 24 trade · +0.1pp vs baseline)
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [−∞,50)`

**3. Win-rate 75.0%** (39 W / 13 L = 52 trade · -4.1pp vs baseline)
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.3161 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.2516 |
| 3 | `session=overlap` | 0.2460 |
| 4 | `session=us` | 0.1863 |

---

## NDX.INDX · ml:full_power
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **78.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.0%** (47 W / 7 L = 54 trade · +8.6pp vs baseline)
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2821 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.2715 |
| 3 | `session=us` | 0.2532 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1931 |

---

## NDX.INDX · ml:main
- Toplam çözülmüş: **115**  ·  Baseline win-rate: **73.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.9%** (26 W / 5 L = 31 trade · +10.9pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 78.6%** (22 W / 6 L = 28 trade · +5.6pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.3137 |
| 2 | `session=overlap` | 0.2802 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.2108 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.1837 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0115 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **1279**  ·  Baseline win-rate: **65.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.7%** (15 W / 75 L = 90 trade · -48.3pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.3455 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1242 |
| 3 | `session=us` | 0.1031 |
| 4 | `session=overlap` | 0.0825 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0605 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0439 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0393 |
| 8 | `rsi_H4=[65,75)` | 0.0177 |
| 9 | `dxy_chg1d=[−∞,-0.5)` | 0.0168 |
| 10 | `rsi_extreme=False` | 0.0133 |
| 11 | `adx_H4=[35,+∞)` | 0.0106 |
| 12 | `bb_extreme_upper=False` | 0.0085 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0078 |
| 14 | `rsi_H1=[50,65)` | 0.0073 |
| 15 | `overbought=False` | 0.0070 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **843**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (44 W / 4 L = 48 trade · +19.8pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = overlap`

**2. Win-rate 91.1%** (41 W / 4 L = 45 trade · +19.2pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session ≠ us`
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 90.9%** (169 W / 17 L = 186 trade · +19.0pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.3113 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.2745 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0408 |
| 4 | `session=us` | 0.0336 |
| 5 | `session=overlap` | 0.0320 |
| 6 | `rsi_extreme=False` | 0.0229 |
| 7 | `exhaustion_up=False` | 0.0165 |
| 8 | `rsi_H1=NA` | 0.0136 |
| 9 | `H1_ema_stack=up` | 0.0128 |
| 10 | `vix_chg1d=NA` | 0.0128 |
| 11 | `H1_adx_label=ranging` | 0.0122 |
| 12 | `oversold=False` | 0.0108 |
| 13 | `H4_adx_label=ranging` | 0.0106 |
| 14 | `adx_H4=NA` | 0.0103 |
| 15 | `adx_H1=NA` | 0.0103 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **1172**  ·  Baseline win-rate: **64.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.9%** (34 W / 3 L = 37 trade · +27.2pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [−∞,50)`
   - `session = overlap`

**2. Win-rate 90.0%** (18 W / 2 L = 20 trade · +25.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [60,70)`
   - `volatility_regime ≠ normal`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 88.0%** (22 W / 3 L = 25 trade · +23.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`

**4. Win-rate 77.3%** (340 W / 100 L = 440 trade · +12.6pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [60,70)`
   - `volatility_regime ≠ normal`
   - `vix_chg1d ≠ [-3,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.1%** (28 W / 88 L = 116 trade · -40.6pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session = us`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -29.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [60,70)`
   - `volatility_regime = normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2488 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.2391 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1168 |
| 4 | `session=us` | 0.0632 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0626 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0593 |
| 7 | `session=overlap` | 0.0531 |
| 8 | `adx_H4=[35,+∞)` | 0.0118 |
| 9 | `regime_label=strong_trend_up` | 0.0114 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0082 |
| 11 | `adx_H4=[−∞,18)` | 0.0074 |
| 12 | `overbought=False` | 0.0065 |
| 13 | `regime_label=ranging` | 0.0064 |
| 14 | `dxy_chg1d=[−∞,-0.5)` | 0.0062 |
| 15 | `vix_chg1d=[-3,0)` | 0.0059 |

---

## USOIL.FOREX · ai_panel
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **79.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.2%** (31 W / 3 L = 34 trade · +11.4pp vs baseline)
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.6794 |
| 2 | `session=overlap` | 0.3077 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0129 |

---

## USOIL.FOREX · emel
- Toplam çözülmüş: **1004**  ·  Baseline win-rate: **65.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1933 |
| 2 | `session=closed` | 0.1586 |
| 3 | `session=europe` | 0.1451 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1335 |
| 5 | `session=asia` | 0.1243 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.1236 |
| 7 | `session=us` | 0.0722 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0493 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **725**  ·  Baseline win-rate: **73.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.1%** (34 W / 1 L = 35 trade · +23.3pp vs baseline)
   - `rsi_H1 = [30,50)`

**2. Win-rate 88.2%** (30 W / 4 L = 34 trade · +14.4pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 84.6%** (33 W / 6 L = 39 trade · +10.8pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = overlap`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0688 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0575 |
| 3 | `session=overlap` | 0.0543 |
| 4 | `session=europe` | 0.0517 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0499 |
| 6 | `volatility_regime=normal` | 0.0490 |
| 7 | `dist_high_M30=[1.5,+∞)` | 0.0473 |
| 8 | `rsi_H1=[30,50)` | 0.0467 |
| 9 | `session=asia` | 0.0462 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0418 |
| 11 | `session=us` | 0.0396 |
| 12 | `bb_extreme_lower=False` | 0.0376 |
| 13 | `rsi_M30=[30,50)` | 0.0243 |
| 14 | `session=closed` | 0.0188 |
| 15 | `adx_H4=[25,35)` | 0.0178 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **197**  ·  Baseline win-rate: **82.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +17.8pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 100.0%** (40 W / 0 L = 40 trade · +17.8pp vs baseline)
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 83.8%** (31 W / 6 L = 37 trade · +1.6pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**4. Win-rate 79.3%** (23 W / 6 L = 29 trade · -2.9pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.1148 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.0944 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0525 |
| 4 | `exhaustion_up=False` | 0.0507 |
| 5 | `M30_ema_stack=mixed` | 0.0359 |
| 6 | `session=us` | 0.0357 |
| 7 | `near_resistance=False` | 0.0333 |
| 8 | `session=overlap` | 0.0318 |
| 9 | `session=europe` | 0.0307 |
| 10 | `H4_ema_stack=up` | 0.0296 |
| 11 | `bb_extreme_upper=False` | 0.0292 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0289 |
| 13 | `rsi_extreme=False` | 0.0274 |
| 14 | `dist_high_M30=NA` | 0.0268 |
| 15 | `H4_adx_label=trending` | 0.0234 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **1059**  ·  Baseline win-rate: **71.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +13.4pp vs baseline)
   - `near_resistance = NA`
   - `session = asia`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 82.8%** (96 W / 20 L = 116 trade · +11.2pp vs baseline)
   - `near_resistance = NA`
   - `session ≠ asia`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.0998 |
| 2 | `session=us` | 0.0964 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0734 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0721 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0504 |
| 6 | `session=europe` | 0.0462 |
| 7 | `session=closed` | 0.0443 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0355 |
| 9 | `H1_adx_label=NA` | 0.0299 |
| 10 | `session=overlap` | 0.0292 |
| 11 | `dxy_chg1d=NA` | 0.0288 |
| 12 | `dist_low_M30=NA` | 0.0198 |
| 13 | `adx_H1=NA` | 0.0190 |
| 14 | `dist_high_M30=NA` | 0.0188 |
| 15 | `H4_adx_label=NA` | 0.0186 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **1094**  ·  Baseline win-rate: **71.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +13.2pp vs baseline)
   - `near_resistance = NA`
   - `session = asia`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 80.7%** (134 W / 32 L = 166 trade · +8.9pp vs baseline)
   - `near_resistance = NA`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1195 |
| 2 | `session=asia` | 0.1093 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0936 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0574 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0525 |
| 6 | `session=europe` | 0.0405 |
| 7 | `session=closed` | 0.0365 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0364 |
| 9 | `session=overlap` | 0.0357 |
| 10 | `dxy_chg1d=NA` | 0.0290 |
| 11 | `H1_adx_label=NA` | 0.0222 |
| 12 | `dist_high_M30=NA` | 0.0214 |
| 13 | `regime_label=NA` | 0.0206 |
| 14 | `exhaustion_up=NA` | 0.0188 |
| 15 | `H4_adx_label=NA` | 0.0188 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **1223**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.1%** (148 W / 39 L = 187 trade · +7.2pp vs baseline)
   - `near_resistance = NA`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**2. Win-rate 77.8%** (21 W / 6 L = 27 trade · +5.9pp vs baseline)
   - `near_resistance = NA`
   - `session = asia`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 77.3%** (17 W / 5 L = 22 trade · +5.4pp vs baseline)
   - `near_resistance = NA`
   - `session ≠ asia`
   - `ml_confidence_bucket = [70,80)`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.1024 |
| 2 | `session=us` | 0.0955 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0628 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0581 |
| 5 | `session=closed` | 0.0475 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0466 |
| 7 | `session=europe` | 0.0443 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0437 |
| 9 | `session=overlap` | 0.0363 |
| 10 | `dxy_chg1d=NA` | 0.0291 |
| 11 | `H1_adx_label=NA` | 0.0241 |
| 12 | `adx_M30=NA` | 0.0213 |
| 13 | `adx_H1=NA` | 0.0202 |
| 14 | `dist_high_M30=NA` | 0.0191 |
| 15 | `rsi_H4=NA` | 0.0176 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **173**  ·  Baseline win-rate: **86.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (31 W / 0 L = 31 trade · +13.9pp vs baseline)
   - `exhaustion_up = False`

**2. Win-rate 96.6%** (28 W / 1 L = 29 trade · +10.5pp vs baseline)
   - `exhaustion_up ≠ False`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 87.1%** (27 W / 4 L = 31 trade · +1.0pp vs baseline)
   - `exhaustion_up ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**4. Win-rate 82.8%** (24 W / 5 L = 29 trade · -3.3pp vs baseline)
   - `exhaustion_up ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.1062 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0501 |
| 3 | `session=us` | 0.0497 |
| 4 | `rsi_H4=NA` | 0.0325 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0313 |
| 6 | `dxy_chg1d=NA` | 0.0294 |
| 7 | `H4_adx_label=NA` | 0.0271 |
| 8 | `session=overlap` | 0.0268 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0248 |
| 10 | `adx_M30=NA` | 0.0236 |
| 11 | `macd_atr_M30=NA` | 0.0230 |
| 12 | `rsi_extreme=NA` | 0.0228 |
| 13 | `H1_adx_label=NA` | 0.0226 |
| 14 | `session=asia` | 0.0208 |
| 15 | `exhaustion_up=False` | 0.0206 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **6737**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (135 W / 0 L = 135 trade · +27.2pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 ≠ [50,65)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**2. Win-rate 100.0%** (28 W / 0 L = 28 trade · +27.2pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 = [50,65)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**3. Win-rate 98.6%** (68 W / 1 L = 69 trade · +25.8pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 ≠ [50,65)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 ≠ [2,4)`

**4. Win-rate 89.7%** (26 W / 3 L = 29 trade · +16.9pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 ≠ [50,65)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 = [2,4)`

**5. Win-rate 88.0%** (22 W / 3 L = 25 trade · +15.2pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 = [50,65)`
   - `dist_high_M30 = [1.5,+∞)`
   - `session ≠ asia`

**6. Win-rate 85.2%** (23 W / 4 L = 27 trade · +12.4pp vs baseline)
   - `rsi_extreme = False`
   - `rsi_H1 = [50,65)`
   - `dist_high_M30 = [1.5,+∞)`
   - `session = asia`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0618 |
| 2 | `overbought=False` | 0.0592 |
| 3 | `session=us` | 0.0500 |
| 4 | `rsi_extreme=False` | 0.0436 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0421 |
| 6 | `session=overlap` | 0.0376 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0356 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0330 |
| 9 | `near_resistance=False` | 0.0299 |
| 10 | `exhaustion_up=False` | 0.0297 |
| 11 | `session=closed` | 0.0295 |
| 12 | `session=asia` | 0.0282 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0278 |
| 14 | `M30_adx_label=NA` | 0.0248 |
| 15 | `ml_confidence_bucket=[50,60)` | 0.0247 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **4990**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +27.2pp vs baseline)
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `consec_red_M30 ≠ [2,4)`
   - `volatility_regime ≠ normal`

**2. Win-rate 100.0%** (29 W / 0 L = 29 trade · +27.2pp vs baseline)
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 = [1,1.3)`
   - `macd_atr_M30 ≠ [0,0.3)`

**3. Win-rate 100.0%** (20 W / 0 L = 20 trade · +27.2pp vs baseline)
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 = [1,1.3)`
   - `macd_atr_M30 = [0,0.3)`

**4. Win-rate 88.9%** (40 W / 5 L = 45 trade · +16.1pp vs baseline)
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `consec_red_M30 ≠ [2,4)`
   - `volatility_regime = normal`

**5. Win-rate 85.0%** (17 W / 3 L = 20 trade · +12.2pp vs baseline)
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `consec_red_M30 = [2,4)`

**6. Win-rate 82.5%** (160 W / 34 L = 194 trade · +9.7pp vs baseline)
   - `near_resistance = NA`
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`
   - `session = europe`

**7. Win-rate 78.5%** (466 W / 128 L = 594 trade · +5.7pp vs baseline)
   - `near_resistance = NA`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = us`
   - `ml_confidence_bucket ≠ [60,70)`

**8. Win-rate 78.3%** (358 W / 99 L = 457 trade · +5.5pp vs baseline)
   - `near_resistance = NA`
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1074 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0905 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.0848 |
| 4 | `session=europe` | 0.0669 |
| 5 | `session=overlap` | 0.0580 |
| 6 | `session=asia` | 0.0579 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0567 |
| 8 | `session=closed` | 0.0387 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0304 |
| 10 | `dxy_chg1d=NA` | 0.0220 |
| 11 | `M30_adx_label=NA` | 0.0196 |
| 12 | `H4_adx_label=NA` | 0.0182 |
| 13 | `near_support=NA` | 0.0176 |
| 14 | `dist_high_M30=NA` | 0.0170 |
| 15 | `consec_red_M30=NA` | 0.0143 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **6107**  ·  Baseline win-rate: **73.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (153 W / 0 L = 153 trade · +26.1pp vs baseline)
   - `near_resistance = False`
   - `rsi_M30 ≠ [50,65)`
   - `session ≠ asia`
   - `consec_green_M30 ≠ [2,4)`

**2. Win-rate 95.7%** (22 W / 1 L = 23 trade · +21.8pp vs baseline)
   - `near_resistance = False`
   - `rsi_M30 = [50,65)`
   - `consec_green_M30 ≠ [0,2)`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +21.3pp vs baseline)
   - `near_resistance = False`
   - `rsi_M30 ≠ [50,65)`
   - `session ≠ asia`
   - `consec_green_M30 = [2,4)`

**4. Win-rate 94.6%** (35 W / 2 L = 37 trade · +20.7pp vs baseline)
   - `near_resistance = False`
   - `rsi_M30 ≠ [50,65)`
   - `session = asia`

**5. Win-rate 88.9%** (40 W / 5 L = 45 trade · +15.0pp vs baseline)
   - `near_resistance = False`
   - `rsi_M30 = [50,65)`
   - `consec_green_M30 = [0,2)`

**6. Win-rate 75.5%** (2473 W / 802 L = 3275 trade · +1.6pp vs baseline)
   - `near_resistance ≠ False`
   - `session ≠ overlap`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0651 |
| 2 | `rsi_extreme=False` | 0.0602 |
| 3 | `exhaustion_up=False` | 0.0567 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0468 |
| 5 | `session=us` | 0.0445 |
| 6 | `session=asia` | 0.0432 |
| 7 | `session=closed` | 0.0424 |
| 8 | `overbought=False` | 0.0417 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0334 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0325 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0301 |
| 12 | `near_resistance=False` | 0.0282 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0271 |
| 14 | `session=europe` | 0.0256 |
| 15 | `H4_adx_label=trending` | 0.0252 |

---

## USOIL.FOREX · smc
- Toplam çözülmüş: **2471**  ·  Baseline win-rate: **85.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (46 W / 0 L = 46 trade · +14.4pp vs baseline)
   - `bb_extreme_lower = False`

**2. Win-rate 96.5%** (55 W / 2 L = 57 trade · +10.9pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = europe`

**3. Win-rate 94.0%** (63 W / 4 L = 67 trade · +8.4pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session = us`
   - `ml_confidence_bucket ≠ [80,+∞)`

**4. Win-rate 89.7%** (315 W / 36 L = 351 trade · +4.1pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session = us`
   - `ml_confidence_bucket = [80,+∞)`

**5. Win-rate 86.8%** (224 W / 34 L = 258 trade · +1.2pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ europe`

**6. Win-rate 83.8%** (1219 W / 236 L = 1455 trade · -1.8pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session ≠ us`
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ closed`

**7. Win-rate 81.4%** (193 W / 44 L = 237 trade · -4.2pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `session ≠ us`
   - `ml_confidence_bucket = [80,+∞)`
   - `session = closed`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1675 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1092 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.1027 |
| 4 | `session=asia` | 0.0805 |
| 5 | `session=closed` | 0.0511 |
| 6 | `session=europe` | 0.0486 |
| 7 | `exhaustion_up=False` | 0.0478 |
| 8 | `near_resistance=False` | 0.0310 |
| 9 | `H4_ema_stack=up` | 0.0280 |
| 10 | `session=overlap` | 0.0237 |
| 11 | `bb_extreme_upper=False` | 0.0235 |
| 12 | `H4_adx_label=trending` | 0.0223 |
| 13 | `exhaustion_down=False` | 0.0192 |
| 14 | `oversold=False` | 0.0188 |
| 15 | `regime_label=transition` | 0.0186 |

---

## XAUUSD · ai_panel
- Toplam çözülmüş: **98**  ·  Baseline win-rate: **67.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.3341 |
| 2 | `session=europe` | 0.1910 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1877 |
| 4 | `session=us` | 0.1661 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.1211 |

---

## XAUUSD · emel
- Toplam çözülmüş: **445**  ·  Baseline win-rate: **39.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.6%** (17 W / 55 L = 72 trade · -16.0pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session = us`

**2. Win-rate 27.5%** (19 W / 50 L = 69 trade · -12.1pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session ≠ us`
   - `session = closed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2323 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.1820 |
| 3 | `session=us` | 0.1342 |
| 4 | `session=asia` | 0.1192 |
| 5 | `session=overlap` | 0.1096 |
| 6 | `session=closed` | 0.1070 |
| 7 | `session=europe` | 0.0789 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0369 |

---

## XAUUSD · meta
- Toplam çözülmüş: **619**  ·  Baseline win-rate: **64.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (34 W / 6 L = 40 trade · +20.9pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1509 |
| 2 | `session=overlap` | 0.1199 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0956 |
| 4 | `session=europe` | 0.0909 |
| 5 | `session=asia` | 0.0720 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0718 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0707 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0651 |
| 9 | `session=closed` | 0.0507 |
| 10 | `consec_green_M30=[0,2)` | 0.0368 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0364 |
| 12 | `bb_extreme_upper=False` | 0.0211 |
| 13 | `mtf_trend=all_down` | 0.0130 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0072 |
| 15 | `bb_extreme_lower=False` | 0.0070 |

---

## XAUUSD · ml:aggressive
- Toplam çözülmüş: **168**  ·  Baseline win-rate: **51.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (23 W / 5 L = 28 trade · +30.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (14 W / 26 L = 40 trade · -16.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ overlap`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [−∞,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1252 |
| 2 | `session=overlap` | 0.1045 |
| 3 | `session=us` | 0.0819 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0508 |
| 5 | `session=europe` | 0.0490 |
| 6 | `session=asia` | 0.0478 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0354 |
| 8 | `near_resistance=False` | 0.0351 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0340 |
| 10 | `regime_label=transition` | 0.0313 |
| 11 | `rsi_M30=NA` | 0.0237 |
| 12 | `overbought=False` | 0.0212 |
| 13 | `exhaustion_up=NA` | 0.0207 |
| 14 | `bb_pctb_M30=NA` | 0.0185 |
| 15 | `oversold=NA` | 0.0170 |

---

## XAUUSD · ml:balanced
- Toplam çözülmüş: **641**  ·  Baseline win-rate: **53.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.5%** (26 W / 8 L = 34 trade · +23.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1313 |
| 2 | `session=closed` | 0.1031 |
| 3 | `session=asia` | 0.1030 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0943 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0787 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0728 |
| 7 | `session=europe` | 0.0649 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0647 |
| 9 | `session=us` | 0.0584 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0372 |
| 11 | `dist_low_M30=NA` | 0.0113 |
| 12 | `consec_red_M30=[0,2)` | 0.0108 |
| 13 | `exhaustion_up=NA` | 0.0106 |
| 14 | `oversold=NA` | 0.0105 |
| 15 | `adx_H1=NA` | 0.0100 |

---

## XAUUSD · ml:full_power
- Toplam çözülmüş: **677**  ·  Baseline win-rate: **50.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.9%** (20 W / 6 L = 26 trade · +26.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = overlap`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`

**2. Win-rate 75.8%** (25 W / 8 L = 33 trade · +25.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1663 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.1227 |
| 3 | `session=asia` | 0.0856 |
| 4 | `session=europe` | 0.0790 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0780 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0750 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0666 |
| 8 | `session=us` | 0.0651 |
| 9 | `session=closed` | 0.0402 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0246 |
| 11 | `near_resistance=False` | 0.0163 |
| 12 | `consec_red_M30=[0,2)` | 0.0136 |
| 13 | `exhaustion_down=False` | 0.0101 |
| 14 | `bb_pctb_M30=NA` | 0.0084 |
| 15 | `overbought=NA` | 0.0083 |

---

## XAUUSD · ml:main
- Toplam çözülmüş: **710**  ·  Baseline win-rate: **51.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.7%** (28 W / 9 L = 37 trade · +24.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.1116 |
| 2 | `session=europe` | 0.1054 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.1012 |
| 4 | `session=overlap` | 0.0980 |
| 5 | `session=closed` | 0.0916 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0902 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0686 |
| 8 | `session=us` | 0.0618 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0462 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0283 |
| 11 | `consec_red_M30=[0,2)` | 0.0128 |
| 12 | `exhaustion_up=NA` | 0.0101 |
| 13 | `regime_label=transition` | 0.0098 |
| 14 | `sar_bearish=NA` | 0.0091 |
| 15 | `consec_green_M30=NA` | 0.0079 |

---

## XAUUSD · ml:ultra_safe
- Toplam çözülmüş: **139**  ·  Baseline win-rate: **52.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.0%** (24 W / 6 L = 30 trade · +27.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1225 |
| 2 | `session=overlap` | 0.1117 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0745 |
| 4 | `near_resistance=False` | 0.0504 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0473 |
| 6 | `session=us` | 0.0470 |
| 7 | `session=asia` | 0.0441 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0407 |
| 9 | `regime_label=transition` | 0.0375 |
| 10 | `exhaustion_down=False` | 0.0302 |
| 11 | `session=europe` | 0.0240 |
| 12 | `bb_pctb_M30=NA` | 0.0225 |
| 13 | `rsi_extreme=False` | 0.0211 |
| 14 | `overbought=False` | 0.0204 |
| 15 | `rsi_M30=NA` | 0.0184 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **4183**  ·  Baseline win-rate: **40.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.0%** (1 W / 19 L = 20 trade · -35.6pp vs baseline)
   - `session ≠ closed`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `volatility_regime ≠ low`

**2. Win-rate 17.6%** (6 W / 28 L = 34 trade · -23.0pp vs baseline)
   - `session ≠ closed`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `consec_red_M30 = [2,4)`

**3. Win-rate 25.0%** (5 W / 15 L = 20 trade · -15.6pp vs baseline)
   - `session ≠ closed`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `volatility_regime = low`
   - `adx_H1 = [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=closed` | 0.1010 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.0724 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0718 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0672 |
| 5 | `session=us` | 0.0468 |
| 6 | `session=asia` | 0.0429 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0401 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0327 |
| 9 | `session=europe` | 0.0324 |
| 10 | `bb_pctb_M30=[0.2,0.5)` | 0.0264 |
| 11 | `dist_low_M30=[−∞,0.3)` | 0.0232 |
| 12 | `session=overlap` | 0.0226 |
| 13 | `macd_atr_M30=[0,0.3)` | 0.0193 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0193 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0173 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **2506**  ·  Baseline win-rate: **49.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.0%** (17 W / 4 L = 21 trade · +31.6pp vs baseline)
   - `session ≠ asia`
   - `ml_confidence_bucket = [80,+∞)`
   - `session = overlap`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.9%** (7 W / 19 L = 26 trade · -22.5pp vs baseline)
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `sar_bearish = True`

**2. Win-rate 33.3%** (9 W / 18 L = 27 trade · -16.1pp vs baseline)
   - `session = asia`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `near_support ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.1402 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1066 |
| 3 | `session=us` | 0.0723 |
| 4 | `session=overlap` | 0.0718 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0682 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0497 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0393 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0332 |
| 9 | `session=europe` | 0.0330 |
| 10 | `bb_pctb_M30=[0.2,0.5)` | 0.0303 |
| 11 | `session=closed` | 0.0288 |
| 12 | `consec_red_M30=[2,4)` | 0.0155 |
| 13 | `atr_ratio_M30=[1,1.3)` | 0.0144 |
| 14 | `atr_ratio_M30=[−∞,0.7)` | 0.0135 |
| 15 | `rsi_M30=[50,65)` | 0.0133 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **3774**  ·  Baseline win-rate: **52.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +35.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `rsi_M30 = [30,50)`
   - `session ≠ asia`

**2. Win-rate 75.0%** (18 W / 6 L = 24 trade · +22.2pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `rsi_M30 = [30,50)`
   - `session = asia`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.8%** (5 W / 19 L = 24 trade · -32.0pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 = [−∞,18)`

**2. Win-rate 27.1%** (26 W / 70 L = 96 trade · -25.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [−∞,50)`
   - `session = us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1046 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1035 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0904 |
| 4 | `session=us` | 0.0833 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0669 |
| 6 | `session=overlap` | 0.0548 |
| 7 | `rsi_M30=[30,50)` | 0.0394 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0347 |
| 9 | `session=asia` | 0.0276 |
| 10 | `session=closed` | 0.0229 |
| 11 | `rsi_extreme=False` | 0.0203 |
| 12 | `rsi_H1=[30,50)` | 0.0201 |
| 13 | `session=europe` | 0.0180 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0125 |
| 15 | `dist_high_M30=[1.5,+∞)` | 0.0120 |

---

## XAUUSD · smc
- Toplam çözülmüş: **1428**  ·  Baseline win-rate: **49.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 29.3%** (77 W / 186 L = 263 trade · -20.6pp vs baseline)
   - `session = us`
   - `dxy_chg1d = NA`
   - `ml_confidence_bucket = [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2586 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1240 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0979 |
| 4 | `session=asia` | 0.0947 |
| 5 | `session=europe` | 0.0910 |
| 6 | `session=closed` | 0.0631 |
| 7 | `session=overlap` | 0.0609 |
| 8 | `consec_red_M30=[0,2)` | 0.0298 |
| 9 | `bb_pctb_M30=[0.2,0.5)` | 0.0175 |
| 10 | `dist_low_M30=[0.7,1.5)` | 0.0157 |
| 11 | `sar_bearish=True` | 0.0136 |
| 12 | `consec_green_M30=[2,4)` | 0.0104 |
| 13 | `dist_high_M30=[1.5,+∞)` | 0.0093 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0088 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0078 |

---

## GDAXI.INDX · emel · BUY
- Toplam çözülmüş: **132**  ·  Baseline win-rate: **72.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.4%** (38 W / 5 L = 43 trade · +16.4pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.3225 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.2046 |
| 3 | `session=europe` | 0.1748 |
| 4 | `session=overlap` | 0.1306 |
| 5 | `session=asia` | 0.0868 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0807 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **147**  ·  Baseline win-rate: **88.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (44 W / 0 L = 44 trade · +11.6pp vs baseline)
   - `session = overlap`

**2. Win-rate 91.4%** (32 W / 3 L = 35 trade · +3.0pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**3. Win-rate 83.8%** (31 W / 6 L = 37 trade · -4.6pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.3038 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.2429 |
| 3 | `session=europe` | 0.1467 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1162 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0910 |
| 6 | `session=asia` | 0.0836 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0159 |

---

## GDAXI.INDX · ml:balanced · BUY
- Toplam çözülmüş: **80**  ·  Baseline win-rate: **75.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.6%** (22 W / 4 L = 26 trade · +9.6pp vs baseline)
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.4127 |
| 2 | `session=overlap` | 0.3937 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1530 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0310 |
| 5 | `session=asia` | 0.0096 |

---

## GDAXI.INDX · ml:full_power · BUY
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **72.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.2%** (23 W / 4 L = 27 trade · +12.7pp vs baseline)
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.3059 |
| 2 | `session=overlap` | 0.2896 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.2259 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.1488 |
| 5 | `session=asia` | 0.0297 |

---

## GDAXI.INDX · ml:main · BUY
- Toplam çözülmüş: **126**  ·  Baseline win-rate: **77.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.4%** (27 W / 5 L = 32 trade · +7.4pp vs baseline)
   - `session = overlap`

**2. Win-rate 80.0%** (44 W / 11 L = 55 trade · +3.0pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2660 |
| 2 | `session=europe` | 0.2524 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.2407 |
| 4 | `session=overlap` | 0.1999 |
| 5 | `session=asia` | 0.0411 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **724**  ·  Baseline win-rate: **62.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (28 W / 8 L = 36 trade · +15.8pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [70,80)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2533 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.2136 |
| 3 | `session=europe` | 0.1606 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.1039 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.1003 |
| 6 | `session=asia` | 0.0888 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0551 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0243 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **709**  ·  Baseline win-rate: **53.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.3%** (25 W / 5 L = 30 trade · +30.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ europe`
   - `ml_confidence_bucket = [−∞,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.9%** (22 W / 108 L = 130 trade · -36.1pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.4370 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1260 |
| 3 | `session=europe` | 0.0972 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0902 |
| 5 | `session=overlap` | 0.0883 |
| 6 | `session=asia` | 0.0846 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0469 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0298 |

---

## GDAXI.INDX · pulse2 · BUY
- Toplam çözülmüş: **520**  ·  Baseline win-rate: **75.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.5%** (34 W / 4 L = 38 trade · +13.9pp vs baseline)
   - `session ≠ asia`
   - `session ≠ europe`
   - `ml_confidence_bucket ≠ [50,60)`

**2. Win-rate 83.5%** (86 W / 17 L = 103 trade · +7.9pp vs baseline)
   - `session ≠ asia`
   - `session ≠ europe`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 78.8%** (160 W / 43 L = 203 trade · +3.2pp vs baseline)
   - `session ≠ asia`
   - `session = europe`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.2635 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.2359 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1819 |
| 4 | `session=overlap` | 0.1759 |
| 5 | `session=europe` | 0.0822 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0526 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0079 |

---

## GDAXI.INDX · pulse2 · SELL
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **65.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2759 |
| 2 | `session=overlap` | 0.2718 |
| 3 | `session=europe` | 0.2432 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.2091 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **570**  ·  Baseline win-rate: **78.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.5%** (76 W / 8 L = 84 trade · +12.1pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [60,70)`

**2. Win-rate 88.0%** (81 W / 11 L = 92 trade · +9.6pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 85.7%** (30 W / 5 L = 35 trade · +7.3pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [50,60)`

**4. Win-rate 81.8%** (18 W / 4 L = 22 trade · +3.4pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [70,80)`

**5. Win-rate 78.4%** (40 W / 11 L = 51 trade · +0.0pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [70,80)`

**6. Win-rate 76.6%** (128 W / 39 L = 167 trade · -1.8pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2785 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1469 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1426 |
| 4 | `session=europe` | 0.1306 |
| 5 | `session=asia` | 0.1211 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0847 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0729 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0226 |

---

## GDAXI.INDX · pulse3 · SELL
- Toplam çözülmüş: **679**  ·  Baseline win-rate: **63.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (29 W / 1 L = 30 trade · +32.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = asia`
   - `ml_confidence_bucket = [60,70)`

**2. Win-rate 93.0%** (40 W / 3 L = 43 trade · +29.1pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = asia`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 76.7%** (92 W / 28 L = 120 trade · +12.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ asia`
   - `ml_confidence_bucket = [60,70)`
   - `session = europe`

**4. Win-rate 76.0%** (38 W / 12 L = 50 trade · +12.1pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.6%** (56 W / 116 L = 172 trade · -31.3pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2879 |
| 2 | `session=asia` | 0.2420 |
| 3 | `session=europe` | 0.1679 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1251 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0857 |
| 6 | `session=overlap` | 0.0796 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0064 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0053 |

---

## GDAXI.INDX · smc · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **45.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.4%** (47 W / 5 L = 52 trade · +44.7pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.8%** (31 W / 89 L = 120 trade · -19.9pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.4470 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.4081 |
| 3 | `session=overlap` | 0.1035 |
| 4 | `session=europe` | 0.0414 |

---

## NDX.INDX · emel · BUY
- Toplam çözülmüş: **139**  ·  Baseline win-rate: **64.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.5%** (75 W / 23 L = 98 trade · +12.5pp vs baseline)
   - `session ≠ us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.1%** (14 W / 27 L = 41 trade · -29.9pp vs baseline)
   - `session = us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.4496 |
| 2 | `session=overlap` | 0.3657 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0882 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0538 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0427 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **189**  ·  Baseline win-rate: **78.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (22 W / 2 L = 24 trade · +12.9pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**2. Win-rate 87.2%** (34 W / 5 L = 39 trade · +8.4pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 83.8%** (31 W / 6 L = 37 trade · +5.0pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 82.5%** (33 W / 7 L = 40 trade · +3.7pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2242 |
| 2 | `session=overlap` | 0.1665 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1304 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.1060 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0708 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0541 |
| 7 | `rsi_extreme=False` | 0.0368 |
| 8 | `exhaustion_up=False` | 0.0216 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0212 |
| 10 | `volatility_regime=high` | 0.0181 |
| 11 | `bb_extreme_upper=False` | 0.0169 |
| 12 | `vix_chg1d=[-3,0)` | 0.0150 |
| 13 | `rsi_H1=[65,75)` | 0.0136 |
| 14 | `rsi_extreme=NA` | 0.0113 |
| 15 | `near_support=False` | 0.0104 |

---

## NDX.INDX · ml:balanced · BUY
- Toplam çözülmüş: **99**  ·  Baseline win-rate: **76.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.8%** (27 W / 6 L = 33 trade · +5.0pp vs baseline)
   - `session ≠ us`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 79.2%** (19 W / 5 L = 24 trade · +2.4pp vs baseline)
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.3266 |
| 2 | `session=overlap` | 0.2637 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.2634 |
| 4 | `session=us` | 0.1462 |

---

## NDX.INDX · ml:full_power · BUY
- Toplam çözülmüş: **85**  ·  Baseline win-rate: **77.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.2%** (41 W / 6 L = 47 trade · +9.6pp vs baseline)
   - `session ≠ us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2843 |
| 2 | `session=us` | 0.2771 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.2663 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1723 |

---

## NDX.INDX · ml:main · BUY
- Toplam çözülmüş: **95**  ·  Baseline win-rate: **76.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +18.4pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 78.6%** (22 W / 6 L = 28 trade · +1.8pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2858 |
| 2 | `session=us` | 0.2782 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.2342 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1903 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0115 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **895**  ·  Baseline win-rate: **67.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.3%** (29 W / 5 L = 34 trade · +17.9pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = overlap`
   - `ml_confidence_bucket = [70,80)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (4 W / 16 L = 20 trade · -47.4pp vs baseline)
   - `bb_extreme_upper = False`
   - `ml_confidence_bucket = [80,+∞)`
   - `regime_label ≠ ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0832 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0772 |
| 3 | `session=us` | 0.0743 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0671 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0498 |
| 6 | `rsi_extreme=False` | 0.0457 |
| 7 | `rsi_H4=[65,75)` | 0.0410 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0404 |
| 9 | `dxy_chg1d=[−∞,-0.5)` | 0.0396 |
| 10 | `bb_extreme_upper=False` | 0.0357 |
| 11 | `regime_label=strong_trend_up` | 0.0351 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0323 |
| 13 | `overbought=False` | 0.0319 |
| 14 | `adx_H4=[35,+∞)` | 0.0276 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0272 |

---

## NDX.INDX · pulse1 · SELL
- Toplam çözülmüş: **384**  ·  Baseline win-rate: **59.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.6%** (25 W / 2 L = 27 trade · +33.2pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 85.6%** (119 W / 20 L = 139 trade · +26.2pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [50,60)`

**3. Win-rate 80.8%** (21 W / 5 L = 26 trade · +21.4pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.8%** (5 W / 68 L = 73 trade · -52.6pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.3087 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.2088 |
| 3 | `session=overlap` | 0.1653 |
| 4 | `session=us` | 0.1405 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0871 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0555 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0342 |

---

## NDX.INDX · pulse2 · BUY
- Toplam çözülmüş: **753**  ·  Baseline win-rate: **73.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.0%** (38 W / 2 L = 40 trade · +21.3pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = overlap`

**2. Win-rate 92.3%** (156 W / 13 L = 169 trade · +18.6pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`

**3. Win-rate 91.1%** (41 W / 4 L = 45 trade · +17.4pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = overlap`
   - `ml_confidence_bucket = [60,70)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2724 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.2700 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0434 |
| 4 | `session=us` | 0.0337 |
| 5 | `rsi_extreme=False` | 0.0246 |
| 6 | `session=overlap` | 0.0233 |
| 7 | `vix_chg1d=NA` | 0.0198 |
| 8 | `exhaustion_up=False` | 0.0179 |
| 9 | `H1_adx_label=ranging` | 0.0179 |
| 10 | `oversold=NA` | 0.0145 |
| 11 | `adx_H1=NA` | 0.0136 |
| 12 | `near_resistance=True` | 0.0131 |
| 13 | `dxy_chg1d=NA` | 0.0129 |
| 14 | `sar_bearish=False` | 0.0123 |
| 15 | `adx_H1=[−∞,18)` | 0.0122 |

---

## NDX.INDX · pulse2 · SELL
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **56.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (21 W / 6 L = 27 trade · +21.1pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2872 |
| 2 | `session=us` | 0.2844 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.2170 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.2114 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **733**  ·  Baseline win-rate: **64.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.7%** (26 W / 4 L = 30 trade · +22.7pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 77.6%** (121 W / 35 L = 156 trade · +13.6pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [60,70)`
   - `dxy_chg1d ≠ [−∞,-0.5)`
   - `session ≠ us`

**3. Win-rate 76.5%** (26 W / 8 L = 34 trade · +12.5pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `overbought = False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -29.0pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [60,70)`
   - `dxy_chg1d = [−∞,-0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.1222 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1132 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1064 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.1033 |
| 5 | `session=overlap` | 0.0972 |
| 6 | `session=us` | 0.0907 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0508 |
| 8 | `regime_label=strong_trend_up` | 0.0212 |
| 9 | `dxy_chg1d=[−∞,-0.5)` | 0.0162 |
| 10 | `regime_label=ranging` | 0.0155 |
| 11 | `volatility_regime=high` | 0.0152 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0146 |
| 13 | `H4_adx_label=trending` | 0.0139 |
| 14 | `exhaustion_up=False` | 0.0132 |
| 15 | `H4_ema_stack=up` | 0.0118 |

---

## NDX.INDX · pulse3 · SELL
- Toplam çözülmüş: **439**  ·  Baseline win-rate: **65.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.7%** (89 W / 6 L = 95 trade · +27.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ overlap`
   - `ml_confidence_bucket = [60,70)`

**2. Win-rate 85.0%** (17 W / 3 L = 20 trade · +19.2pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 84.6%** (22 W / 4 L = 26 trade · +18.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket = [70,80)`
   - `session ≠ us`

**4. Win-rate 77.1%** (108 W / 32 L = 140 trade · +11.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = overlap`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.3%** (7 W / 68 L = 75 trade · -56.5pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.4326 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.2612 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0937 |
| 4 | `session=us` | 0.0820 |
| 5 | `session=overlap` | 0.0803 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0502 |

---

## USOIL.FOREX · emel · BUY
- Toplam çözülmüş: **975**  ·  Baseline win-rate: **65.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.2143 |
| 2 | `session=closed` | 0.1725 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1399 |
| 4 | `session=europe` | 0.1391 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.1217 |
| 6 | `session=asia` | 0.1022 |
| 7 | `session=us` | 0.0650 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0453 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **465**  ·  Baseline win-rate: **73.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (27 W / 3 L = 30 trade · +16.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 87.1%** (27 W / 4 L = 31 trade · +14.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`
   - `session = overlap`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1866 |
| 2 | `session=us` | 0.1625 |
| 3 | `session=overlap` | 0.1127 |
| 4 | `session=asia` | 0.0956 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0918 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0903 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0850 |
| 8 | `session=europe` | 0.0684 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0551 |
| 10 | `session=closed` | 0.0521 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **260**  ·  Baseline win-rate: **75.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (30 W / 0 L = 30 trade · +25.0pp vs baseline)
   - `bb_extreme_lower = False`

**2. Win-rate 81.8%** (36 W / 8 L = 44 trade · +6.8pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`

**3. Win-rate 75.0%** (30 W / 10 L = 40 trade · +0.0pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_extreme_upper=False` | 0.0466 |
| 2 | `adx_H4=[25,35)` | 0.0448 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0431 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0427 |
| 5 | `session=us` | 0.0419 |
| 6 | `bb_extreme_lower=False` | 0.0340 |
| 7 | `session=asia` | 0.0328 |
| 8 | `H4_adx_label=trending` | 0.0324 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0318 |
| 10 | `M30_ema_stack=mixed` | 0.0302 |
| 11 | `consec_red_M30=[0,2)` | 0.0299 |
| 12 | `session=europe` | 0.0284 |
| 13 | `mtf_trend=mixed` | 0.0273 |
| 14 | `overbought=False` | 0.0264 |
| 15 | `H4_ema_stack=up` | 0.0232 |

---

## USOIL.FOREX · ml:aggressive · BUY
- Toplam çözülmüş: **120**  ·  Baseline win-rate: **81.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +18.3pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 86.7%** (26 W / 4 L = 30 trade · +5.0pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**3. Win-rate 80.6%** (25 W / 6 L = 31 trade · -1.1pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.2500 |
| 2 | `session=us` | 0.1770 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1501 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1149 |
| 5 | `session=europe` | 0.1129 |
| 6 | `session=overlap` | 0.1103 |
| 7 | `session=asia` | 0.0743 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0105 |

---

## USOIL.FOREX · ml:balanced · BUY
- Toplam çözülmüş: **549**  ·  Baseline win-rate: **75.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.1%** (32 W / 2 L = 34 trade · +19.1pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 86.7%** (39 W / 6 L = 45 trade · +11.7pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`
   - `session ≠ asia`

**3. Win-rate 76.9%** (120 W / 36 L = 156 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ asia`
   - `session ≠ europe`

**4. Win-rate 75.6%** (31 W / 10 L = 41 trade · +0.6pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`
   - `session = asia`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.2341 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.1557 |
| 3 | `session=asia` | 0.1188 |
| 4 | `session=us` | 0.1077 |
| 5 | `session=closed` | 0.1044 |
| 6 | `session=europe` | 0.0995 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0892 |
| 8 | `session=overlap` | 0.0667 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0239 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **510**  ·  Baseline win-rate: **67.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +32.2pp vs baseline)
   - `exhaustion_up = False`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.0787 |
| 2 | `session=us` | 0.0764 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0690 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0681 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0489 |
| 6 | `session=closed` | 0.0414 |
| 7 | `session=europe` | 0.0371 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0336 |
| 9 | `session=overlap` | 0.0328 |
| 10 | `M30_ema_stack=mixed` | 0.0324 |
| 11 | `oversold=False` | 0.0311 |
| 12 | `near_support=False` | 0.0300 |
| 13 | `regime_label=transition` | 0.0297 |
| 14 | `H4_ema_stack=up` | 0.0242 |
| 15 | `mtf_trend=mixed` | 0.0231 |

---

## USOIL.FOREX · ml:full_power · BUY
- Toplam çözülmüş: **563**  ·  Baseline win-rate: **75.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.1%** (32 W / 2 L = 34 trade · +19.0pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 87.0%** (20 W / 3 L = 23 trade · +11.9pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`
   - `session = overlap`

**3. Win-rate 81.2%** (26 W / 6 L = 32 trade · +6.1pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = closed`

**4. Win-rate 77.9%** (53 W / 15 L = 68 trade · +2.8pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ overlap`
   - `session ≠ europe`

**5. Win-rate 77.8%** (56 W / 16 L = 72 trade · +2.7pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ closed`
   - `session = us`

**6. Win-rate 75.0%** (33 W / 11 L = 44 trade · -0.1pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ overlap`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.2602 |
| 2 | `session=us` | 0.1233 |
| 3 | `session=asia` | 0.1207 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1079 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.1030 |
| 6 | `session=closed` | 0.0992 |
| 7 | `session=europe` | 0.0823 |
| 8 | `session=overlap` | 0.0596 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0437 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **531**  ·  Baseline win-rate: **68.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.5%** (70 W / 18 L = 88 trade · +11.3pp vs baseline)
   - `dxy_chg1d = NA`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ asia`
   - `session = us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -33.2pp vs baseline)
   - `dxy_chg1d = NA`
   - `ml_confidence_bucket = [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1015 |
| 2 | `session=asia` | 0.0951 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0767 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0600 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0538 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0352 |
| 7 | `session=europe` | 0.0348 |
| 8 | `session=closed` | 0.0324 |
| 9 | `session=overlap` | 0.0276 |
| 10 | `bb_extreme_upper=NA` | 0.0268 |
| 11 | `macd_atr_M30=NA` | 0.0238 |
| 12 | `exhaustion_up=NA` | 0.0227 |
| 13 | `atr_ratio_M30=NA` | 0.0221 |
| 14 | `H4_adx_label=NA` | 0.0210 |
| 15 | `volatility_regime=NA` | 0.0204 |

---

## USOIL.FOREX · ml:main · BUY
- Toplam çözülmüş: **645**  ·  Baseline win-rate: **74.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (30 W / 3 L = 33 trade · +16.3pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = overlap`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 82.9%** (29 W / 6 L = 35 trade · +8.3pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ overlap`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = closed`

**3. Win-rate 82.5%** (47 W / 10 L = 57 trade · +7.9pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**4. Win-rate 75.9%** (22 W / 7 L = 29 trade · +1.3pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ overlap`
   - `ml_confidence_bucket = [50,60)`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.1696 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1495 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1473 |
| 4 | `session=overlap` | 0.1327 |
| 5 | `session=us` | 0.1075 |
| 6 | `session=europe` | 0.0995 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0860 |
| 8 | `session=closed` | 0.0608 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0472 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **578**  ·  Baseline win-rate: **68.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +31.1pp vs baseline)
   - `exhaustion_up = False`

**2. Win-rate 85.5%** (59 W / 10 L = 69 trade · +16.6pp vs baseline)
   - `exhaustion_up ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 76.9%** (20 W / 6 L = 26 trade · +8.0pp vs baseline)
   - `exhaustion_up ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`
   - `ml_confidence_bucket = [60,70)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1274 |
| 2 | `session=asia` | 0.0774 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0587 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0558 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0505 |
| 6 | `session=europe` | 0.0415 |
| 7 | `session=overlap` | 0.0378 |
| 8 | `oversold=False` | 0.0358 |
| 9 | `regime_label=transition` | 0.0357 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0339 |
| 11 | `overbought=False` | 0.0334 |
| 12 | `session=closed` | 0.0304 |
| 13 | `near_support=False` | 0.0301 |
| 14 | `bb_extreme_lower=False` | 0.0285 |
| 15 | `H4_adx_label=trending` | 0.0242 |

---

## USOIL.FOREX · ml:ultra_safe · BUY
- Toplam çözülmüş: **98**  ·  Baseline win-rate: **88.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.3%** (26 W / 1 L = 27 trade · +7.5pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 92.0%** (23 W / 2 L = 25 trade · +3.2pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**3. Win-rate 86.4%** (19 W / 3 L = 22 trade · -2.4pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `session ≠ europe`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · -9.6pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.1830 |
| 2 | `session=europe` | 0.1402 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1392 |
| 4 | `session=asia` | 0.1332 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.1271 |
| 6 | `session=us` | 0.1241 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.1017 |
| 8 | `session=overlap` | 0.0514 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **3733**  ·  Baseline win-rate: **72.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +27.3pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `vix_chg1d ≠ [0,3)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**2. Win-rate 100.0%** (47 W / 0 L = 47 trade · +27.3pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `vix_chg1d ≠ [0,3)`
   - `atr_ratio_M30 = [1,1.3)`

**3. Win-rate 100.0%** (25 W / 0 L = 25 trade · +27.3pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 = [0.7,1)`
   - `adx_M30 ≠ [−∞,18)`

**4. Win-rate 96.6%** (28 W / 1 L = 29 trade · +23.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `vix_chg1d = [0,3)`

**5. Win-rate 87.2%** (123 W / 18 L = 141 trade · +14.5pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `ml_confidence_bucket = [−∞,50)`
   - `session = us`

**6. Win-rate 77.2%** (61 W / 18 L = 79 trade · +4.5pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = europe`
   - `ml_confidence_bucket = [60,70)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.0896 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0765 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0711 |
| 4 | `session=asia` | 0.0547 |
| 5 | `session=overlap` | 0.0401 |
| 6 | `session=closed` | 0.0395 |
| 7 | `session=europe` | 0.0380 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0349 |
| 9 | `near_resistance=False` | 0.0347 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0340 |
| 11 | `near_support=False` | 0.0315 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0283 |
| 13 | `consec_red_M30=[0,2)` | 0.0277 |
| 14 | `rsi_extreme=False` | 0.0266 |
| 15 | `H4_adx_label=trending` | 0.0257 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **3004**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (102 W / 0 L = 102 trade · +27.2pp vs baseline)
   - `rsi_extreme = False`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**2. Win-rate 100.0%** (25 W / 0 L = 25 trade · +27.2pp vs baseline)
   - `rsi_extreme = False`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 = [0,2)`

**3. Win-rate 91.7%** (22 W / 2 L = 24 trade · +18.9pp vs baseline)
   - `rsi_extreme = False`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 ≠ [0,2)`

**4. Win-rate 87.6%** (127 W / 18 L = 145 trade · +14.8pp vs baseline)
   - `rsi_extreme ≠ False`
   - `session = closed`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 76.4%** (55 W / 17 L = 72 trade · +3.6pp vs baseline)
   - `rsi_extreme ≠ False`
   - `session = closed`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=closed` | 0.1112 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.0717 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0607 |
| 4 | `H4_adx_label=trending` | 0.0519 |
| 5 | `overbought=False` | 0.0439 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0406 |
| 7 | `H4_ema_stack=up` | 0.0370 |
| 8 | `session=overlap` | 0.0368 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0368 |
| 10 | `exhaustion_up=False` | 0.0336 |
| 11 | `rsi_extreme=False` | 0.0326 |
| 12 | `session=asia` | 0.0319 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0313 |
| 14 | `session=us` | 0.0286 |
| 15 | `session=europe` | 0.0273 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **2756**  ·  Baseline win-rate: **72.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +27.1pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 88.6%** (109 W / 14 L = 123 trade · +15.7pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = europe`

**3. Win-rate 86.4%** (19 W / 3 L = 22 trade · +13.5pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `near_resistance ≠ NA`
   - `atr_ratio_M30 = [0.7,1)`

**4. Win-rate 82.4%** (117 W / 25 L = 142 trade · +9.5pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ europe`
   - `session = asia`

**5. Win-rate 77.5%** (447 W / 130 L = 577 trade · +4.6pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `near_resistance = NA`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1561 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1491 |
| 3 | `session=europe` | 0.1368 |
| 4 | `session=asia` | 0.0883 |
| 5 | `session=overlap` | 0.0641 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0586 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0585 |
| 8 | `session=us` | 0.0531 |
| 9 | `session=closed` | 0.0288 |
| 10 | `consec_green_M30=[0,2)` | 0.0180 |
| 11 | `H1_ema_stack=NA` | 0.0113 |
| 12 | `M30_adx_label=NA` | 0.0090 |
| 13 | `rsi_H1=NA` | 0.0088 |
| 14 | `rsi_M30=NA` | 0.0076 |
| 15 | `near_support=NA` | 0.0072 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **2234**  ·  Baseline win-rate: **72.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.4%** (38 W / 1 L = 39 trade · +24.8pp vs baseline)
   - `session ≠ us`
   - `oversold = False`
   - `consec_red_M30 = [0,2)`

**2. Win-rate 97.1%** (33 W / 1 L = 34 trade · +24.5pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket ≠ [50,60)`
   - `near_support = False`

**3. Win-rate 88.5%** (262 W / 34 L = 296 trade · +15.9pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket = [50,60)`

**4. Win-rate 87.0%** (20 W / 3 L = 23 trade · +14.4pp vs baseline)
   - `session ≠ us`
   - `oversold = False`
   - `consec_red_M30 ≠ [0,2)`

**5. Win-rate 79.6%** (39 W / 10 L = 49 trade · +7.0pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket ≠ [50,60)`
   - `near_support ≠ False`
   - `ml_confidence_bucket = [−∞,50)`

**6. Win-rate 77.7%** (153 W / 44 L = 197 trade · +5.1pp vs baseline)
   - `session ≠ us`
   - `oversold ≠ False`
   - `session = asia`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2021 |
| 2 | `session=overlap` | 0.0973 |
| 3 | `session=europe` | 0.0723 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0629 |
| 5 | `session=asia` | 0.0529 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0495 |
| 7 | `session=closed` | 0.0354 |
| 8 | `H4_ema_stack=up` | 0.0283 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0263 |
| 10 | `near_resistance=False` | 0.0254 |
| 11 | `H4_adx_label=trending` | 0.0245 |
| 12 | `overbought=False` | 0.0241 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0238 |
| 14 | `rsi_extreme=False` | 0.0212 |
| 15 | `oversold=False` | 0.0163 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **3405**  ·  Baseline win-rate: **74.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (34 W / 0 L = 34 trade · +26.0pp vs baseline)
   - `sar_bearish = True`

**2. Win-rate 80.4%** (230 W / 56 L = 286 trade · +6.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ asia`
   - `session ≠ us`

**3. Win-rate 76.6%** (625 W / 191 L = 816 trade · +2.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`
   - `ml_confidence_bucket = [70,80)`

**4. Win-rate 75.2%** (91 W / 30 L = 121 trade · +1.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ asia`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.0953 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.0926 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0888 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0886 |
| 5 | `session=europe` | 0.0641 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0631 |
| 7 | `session=overlap` | 0.0611 |
| 8 | `session=asia` | 0.0575 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0407 |
| 10 | `session=closed` | 0.0367 |
| 11 | `sar_bearish=NA` | 0.0169 |
| 12 | `sar_bearish=True` | 0.0167 |
| 13 | `H4_ema_stack=NA` | 0.0142 |
| 14 | `bb_extreme_lower=NA` | 0.0116 |
| 15 | `rsi_M30=NA` | 0.0110 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **2702**  ·  Baseline win-rate: **73.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (113 W / 0 L = 113 trade · +26.2pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**2. Win-rate 100.0%** (50 W / 0 L = 50 trade · +26.2pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `session = us`

**3. Win-rate 93.3%** (28 W / 2 L = 30 trade · +19.5pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `session ≠ us`

**4. Win-rate 87.0%** (47 W / 7 L = 54 trade · +13.2pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session ≠ overlap`
   - `session = closed`
   - `ml_confidence_bucket = [70,80)`

**5. Win-rate 81.1%** (116 W / 27 L = 143 trade · +7.3pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session ≠ overlap`
   - `session = closed`
   - `ml_confidence_bucket ≠ [70,80)`

**6. Win-rate 75.6%** (717 W / 231 L = 948 trade · +1.8pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session ≠ overlap`
   - `session ≠ closed`
   - `session = asia`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1269 |
| 2 | `session=closed` | 0.0667 |
| 3 | `session=asia` | 0.0633 |
| 4 | `dist_high_M30=[1.5,+∞)` | 0.0500 |
| 5 | `session=europe` | 0.0357 |
| 6 | `session=us` | 0.0317 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0304 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0264 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0258 |
| 10 | `M30_adx_label=NA` | 0.0246 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0246 |
| 12 | `dxy_chg1d=NA` | 0.0236 |
| 13 | `near_support=NA` | 0.0214 |
| 14 | `M30_ema_stack=NA` | 0.0206 |
| 15 | `H4_adx_label=NA` | 0.0204 |

---

## USOIL.FOREX · smc · BUY
- Toplam çözülmüş: **1600**  ·  Baseline win-rate: **85.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.4%** (54 W / 2 L = 56 trade · +10.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session = us`

**2. Win-rate 93.2%** (69 W / 5 L = 74 trade · +7.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`
   - `session ≠ asia`

**3. Win-rate 90.9%** (110 W / 11 L = 121 trade · +5.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`
   - `session = asia`

**4. Win-rate 86.8%** (211 W / 32 L = 243 trade · +1.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ europe`
   - `session ≠ asia`
   - `session = us`

**5. Win-rate 85.9%** (171 W / 28 L = 199 trade · +0.1pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ europe`
   - `session ≠ asia`
   - `session ≠ us`

**6. Win-rate 85.1%** (451 W / 79 L = 530 trade · -0.7pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `session ≠ europe`
   - `session = asia`

**7. Win-rate 81.4%** (307 W / 70 L = 377 trade · -4.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.2977 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.2794 |
| 3 | `session=europe` | 0.1174 |
| 4 | `session=us` | 0.0825 |
| 5 | `session=closed` | 0.0659 |
| 6 | `session=asia` | 0.0484 |
| 7 | `session=overlap` | 0.0473 |
| 8 | `dist_low_M30=NA` | 0.0052 |

---

## USOIL.FOREX · smc · SELL
- Toplam çözülmüş: **871**  ·  Baseline win-rate: **85.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +14.8pp vs baseline)
   - `session ≠ us`
   - `session ≠ europe`
   - `bb_extreme_upper ≠ NA`

**2. Win-rate 96.5%** (55 W / 2 L = 57 trade · +11.3pp vs baseline)
   - `session ≠ us`
   - `session = europe`
   - `ml_confidence_bucket ≠ [80,+∞)`

**3. Win-rate 96.4%** (107 W / 4 L = 111 trade · +11.2pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket ≠ [70,80)`

**4. Win-rate 90.0%** (18 W / 2 L = 20 trade · +4.8pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket = [70,80)`

**5. Win-rate 88.5%** (146 W / 19 L = 165 trade · +3.3pp vs baseline)
   - `session ≠ us`
   - `session = europe`
   - `ml_confidence_bucket = [80,+∞)`

**6. Win-rate 81.1%** (326 W / 76 L = 402 trade · -4.1pp vs baseline)
   - `session ≠ us`
   - `session ≠ europe`
   - `bb_extreme_upper = NA`
   - `session ≠ closed`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2421 |
| 2 | `session=asia` | 0.1256 |
| 3 | `session=closed` | 0.1242 |
| 4 | `session=europe` | 0.0940 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0343 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0312 |
| 7 | `H1_adx_label=NA` | 0.0244 |
| 8 | `dxy_chg1d=NA` | 0.0205 |
| 9 | `session=overlap` | 0.0198 |
| 10 | `dist_low_M30=NA` | 0.0185 |
| 11 | `consec_green_M30=NA` | 0.0166 |
| 12 | `rsi_extreme=NA` | 0.0133 |
| 13 | `dist_high_M30=NA` | 0.0122 |
| 14 | `rsi_M30=NA` | 0.0112 |
| 15 | `near_resistance=NA` | 0.0110 |

---

## XAUUSD · emel · BUY
- Toplam çözülmüş: **342**  ·  Baseline win-rate: **38.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (8 W / 48 L = 56 trade · -24.6pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session = us`

**2. Win-rate 23.3%** (14 W / 46 L = 60 trade · -15.6pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session ≠ us`
   - `session = closed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.1982 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1773 |
| 3 | `session=europe` | 0.1534 |
| 4 | `session=us` | 0.1420 |
| 5 | `session=closed` | 0.1193 |
| 6 | `session=asia` | 0.0904 |
| 7 | `session=overlap` | 0.0843 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0349 |

---

## XAUUSD · emel · SELL
- Toplam çözülmüş: **103**  ·  Baseline win-rate: **41.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -21.7pp vs baseline)
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.3372 |
| 2 | `session=asia` | 0.3122 |
| 3 | `session=us` | 0.1883 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0801 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0509 |
| 6 | `session=closed` | 0.0215 |
| 7 | `session=overlap` | 0.0098 |

---

## XAUUSD · meta · BUY
- Toplam çözülmüş: **240**  ·  Baseline win-rate: **61.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (21 W / 7 L = 28 trade · +13.7pp vs baseline)
   - `session ≠ asia`
   - `session ≠ us`
   - `session ≠ overlap`
   - `ml_confidence_bucket = [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.1625 |
| 2 | `session=us` | 0.1554 |
| 3 | `session=europe` | 0.1445 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.1353 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.1164 |
| 6 | `session=overlap` | 0.0985 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0830 |
| 8 | `session=asia` | 0.0699 |
| 9 | `session=closed` | 0.0345 |

---

## XAUUSD · meta · SELL
- Toplam çözülmüş: **379**  ·  Baseline win-rate: **66.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.1%** (37 W / 5 L = 42 trade · +22.1pp vs baseline)
   - `session = overlap`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1624 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.1445 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1268 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1170 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0946 |
| 6 | `session=us` | 0.0886 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0790 |
| 8 | `session=asia` | 0.0767 |
| 9 | `session=closed` | 0.0636 |
| 10 | `session=europe` | 0.0416 |

---

## XAUUSD · ml:aggressive · BUY
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **55.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.8%** (26 W / 7 L = 33 trade · +22.9pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2900 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.1909 |
| 3 | `session=asia` | 0.1417 |
| 4 | `session=europe` | 0.1394 |
| 5 | `session=overlap` | 0.1374 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.1005 |

---

## XAUUSD · ml:balanced · BUY
- Toplam çözülmüş: **204**  ·  Baseline win-rate: **44.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.2%** (23 W / 4 L = 27 trade · +41.1pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.9%** (11 W / 35 L = 46 trade · -20.2pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = asia`

**2. Win-rate 25.0%** (6 W / 18 L = 24 trade · -19.1pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ asia`
   - `session = us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.2161 |
| 2 | `session=asia` | 0.1531 |
| 3 | `session=overlap` | 0.1360 |
| 4 | `session=us` | 0.1312 |
| 5 | `session=europe` | 0.1002 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0915 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0903 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0817 |

---

## XAUUSD · ml:balanced · SELL
- Toplam çözülmüş: **437**  ·  Baseline win-rate: **57.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=closed` | 0.2066 |
| 2 | `session=asia` | 0.1273 |
| 3 | `session=overlap` | 0.1101 |
| 4 | `session=europe` | 0.1040 |
| 5 | `session=us` | 0.0879 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0856 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0742 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0680 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0646 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0623 |

---

## XAUUSD · ml:full_power · BUY
- Toplam çözülmüş: **215**  ·  Baseline win-rate: **41.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (21 W / 6 L = 27 trade · +35.9pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `ml_confidence_bucket ≠ [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.0%** (6 W / 19 L = 25 trade · -17.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`
   - `session ≠ europe`
   - `session = us`

**2. Win-rate 27.4%** (17 W / 45 L = 62 trade · -14.5pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ overlap`
   - `session ≠ europe`
   - `session ≠ us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.2154 |
| 2 | `session=us` | 0.1643 |
| 3 | `session=asia` | 0.1202 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1148 |
| 5 | `session=europe` | 0.1126 |
| 6 | `session=overlap` | 0.1081 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0954 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0692 |

---

## XAUUSD · ml:full_power · SELL
- Toplam çözülmüş: **462**  ·  Baseline win-rate: **54.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1938 |
| 2 | `session=europe` | 0.1234 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.1182 |
| 4 | `session=us` | 0.1035 |
| 5 | `session=asia` | 0.0950 |
| 6 | `session=closed` | 0.0909 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0849 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0788 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0530 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0499 |

---

## XAUUSD · ml:main · BUY
- Toplam çözülmüş: **223**  ·  Baseline win-rate: **43.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.4%** (27 W / 7 L = 34 trade · +35.9pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [50,60)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (5 W / 15 L = 20 trade · -18.5pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ asia`
   - `session = us`

**2. Win-rate 25.5%** (12 W / 35 L = 47 trade · -18.0pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.2007 |
| 2 | `session=overlap` | 0.1433 |
| 3 | `session=asia` | 0.1392 |
| 4 | `session=us` | 0.1283 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.1130 |
| 6 | `session=europe` | 0.1096 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0821 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0523 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0316 |

---

## XAUUSD · ml:main · SELL
- Toplam çözülmüş: **487**  ·  Baseline win-rate: **54.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (8 W / 16 L = 24 trade · -21.3pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ closed`
   - `session = europe`
   - `ml_confidence_bucket = [60,70)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.1552 |
| 2 | `session=closed` | 0.1420 |
| 3 | `session=europe` | 0.1418 |
| 4 | `session=asia` | 0.1314 |
| 5 | `session=overlap` | 0.1242 |
| 6 | `session=us` | 0.0875 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0709 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0627 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0369 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0337 |
| 11 | `consec_green_M30=NA` | 0.0070 |

---

## XAUUSD · ml:ultra_safe · SELL
- Toplam çözülmüş: **95**  ·  Baseline win-rate: **44.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.8%** (8 W / 15 L = 23 trade · -9.4pp vs baseline)
   - `session = asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.1760 |
| 2 | `session=us` | 0.1649 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.1318 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.1260 |
| 5 | `session=europe` | 0.1135 |
| 6 | `session=overlap` | 0.0641 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0533 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0424 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0422 |
| 10 | `near_support=NA` | 0.0199 |
| 11 | `overbought=NA` | 0.0103 |
| 12 | `rsi_extreme=False` | 0.0103 |
| 13 | `exhaustion_up=NA` | 0.0103 |
| 14 | `overbought=False` | 0.0103 |
| 15 | `oversold=NA` | 0.0086 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **2116**  ·  Baseline win-rate: **35.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.0%** (3 W / 17 L = 20 trade · -20.4pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `dist_high_M30 = [1.5,+∞)`

**2. Win-rate 24.0%** (6 W / 19 L = 25 trade · -11.4pp vs baseline)
   - `session ≠ us`
   - `adx_M30 ≠ [25,35)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `consec_red_M30 = [0,2)`

**3. Win-rate 24.0%** (63 W / 200 L = 263 trade · -11.4pp vs baseline)
   - `session = us`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**4. Win-rate 26.4%** (14 W / 39 L = 53 trade · -9.0pp vs baseline)
   - `session ≠ us`
   - `adx_M30 ≠ [25,35)`
   - `ml_confidence_bucket = [70,80)`
   - `session = overlap`

**5. Win-rate 32.7%** (52 W / 107 L = 159 trade · -2.7pp vs baseline)
   - `session ≠ us`
   - `adx_M30 ≠ [25,35)`
   - `ml_confidence_bucket = [70,80)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1915 |
| 2 | `session=europe` | 0.0899 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0770 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0607 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0601 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0508 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0488 |
| 8 | `session=asia` | 0.0433 |
| 9 | `session=closed` | 0.0393 |
| 10 | `session=overlap` | 0.0358 |
| 11 | `adx_M30=[25,35)` | 0.0214 |
| 12 | `vix_chg1d=[-3,0)` | 0.0200 |
| 13 | `macd_atr_M30=[0,0.3)` | 0.0144 |
| 14 | `bb_pctb_M30=[0.5,0.8)` | 0.0140 |
| 15 | `mtf_trend=all_down` | 0.0126 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **2067**  ·  Baseline win-rate: **46.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.6%** (11 W / 40 L = 51 trade · -24.4pp vs baseline)
   - `session ≠ closed`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `near_resistance = False`

**2. Win-rate 28.1%** (9 W / 23 L = 32 trade · -17.9pp vs baseline)
   - `session ≠ closed`
   - `session = us`
   - `consec_green_M30 = [0,2)`

**3. Win-rate 32.3%** (20 W / 42 L = 62 trade · -13.7pp vs baseline)
   - `session ≠ closed`
   - `session ≠ us`
   - `ml_confidence_bucket = [−∞,50)`
   - `session = europe`

**4. Win-rate 33.8%** (53 W / 104 L = 157 trade · -12.2pp vs baseline)
   - `session ≠ closed`
   - `session ≠ us`
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1034 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1031 |
| 3 | `session=closed` | 0.0954 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0925 |
| 5 | `session=europe` | 0.0843 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0784 |
| 7 | `session=asia` | 0.0620 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0418 |
| 9 | `session=overlap` | 0.0379 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0365 |
| 11 | `consec_green_M30=[0,2)` | 0.0239 |
| 12 | `consec_red_M30=[2,4)` | 0.0122 |
| 13 | `near_support=True` | 0.0102 |
| 14 | `dist_low_M30=[−∞,0.3)` | 0.0098 |
| 15 | `mtf_trend=all_down` | 0.0090 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **1097**  ·  Baseline win-rate: **41.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.2%** (18 W / 93 L = 111 trade · -25.1pp vs baseline)
   - `ml_confidence_bucket = [60,70)`
   - `session = asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.1452 |
| 2 | `session=asia` | 0.1367 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.1314 |
| 4 | `session=europe` | 0.0546 |
| 5 | `session=overlap` | 0.0507 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0490 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0375 |
| 8 | `session=us` | 0.0258 |
| 9 | `bb_extreme_lower=False` | 0.0204 |
| 10 | `dist_low_M30=[1.5,+∞)` | 0.0201 |
| 11 | `volatility_regime=normal` | 0.0187 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0182 |
| 13 | `adx_H1=[18,25)` | 0.0179 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0164 |
| 15 | `session=closed` | 0.0164 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **1409**  ·  Baseline win-rate: **55.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.1%** (6 W / 17 L = 23 trade · -29.7pp vs baseline)
   - `bb_extreme_upper = False`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=europe` | 0.1391 |
| 2 | `session=us` | 0.1105 |
| 3 | `session=overlap` | 0.0913 |
| 4 | `session=asia` | 0.0655 |
| 5 | `dist_high_M30=[1.5,+∞)` | 0.0490 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0487 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0469 |
| 8 | `session=closed` | 0.0416 |
| 9 | `bb_extreme_upper=False` | 0.0393 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0388 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0287 |
| 12 | `bb_pctb_M30=[0.2,0.5)` | 0.0268 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0224 |
| 14 | `volatility_regime=low` | 0.0210 |
| 15 | `consec_green_M30=[0,2)` | 0.0139 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **1684**  ·  Baseline win-rate: **45.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +34.2pp vs baseline)
   - `rsi_M30 = [30,50)`
   - `M30_ema_stack ≠ mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.1%** (63 W / 146 L = 209 trade · -14.9pp vs baseline)
   - `rsi_M30 ≠ [30,50)`
   - `session = us`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1407 |
| 2 | `session=europe` | 0.1194 |
| 3 | `session=overlap` | 0.0632 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0624 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0580 |
| 6 | `session=asia` | 0.0505 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0472 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0462 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0403 |
| 10 | `rsi_M30=[30,50)` | 0.0285 |
| 11 | `session=closed` | 0.0267 |
| 12 | `volatility_regime=low` | 0.0260 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0202 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0178 |
| 15 | `dist_high_M30=[1.5,+∞)` | 0.0174 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **2090**  ·  Baseline win-rate: **59.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.8%** (33 W / 5 L = 38 trade · +27.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `near_support = False`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1228 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0897 |
| 3 | `session=overlap` | 0.0867 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0602 |
| 5 | `session=europe` | 0.0532 |
| 6 | `session=us` | 0.0439 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0423 |
| 8 | `session=asia` | 0.0409 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0402 |
| 10 | `near_support=False` | 0.0328 |
| 11 | `session=closed` | 0.0264 |
| 12 | `oversold=True` | 0.0229 |
| 13 | `rsi_H1=[30,50)` | 0.0210 |
| 14 | `H1_adx_label=weak_trend` | 0.0198 |
| 15 | `consec_red_M30=[0,2)` | 0.0188 |

---

## XAUUSD · smc · BUY
- Toplam çözülmüş: **320**  ·  Baseline win-rate: **57.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.3%** (18 W / 5 L = 23 trade · +21.1pp vs baseline)
   - `session ≠ us`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.2050 |
| 2 | `session=us` | 0.1764 |
| 3 | `session=asia` | 0.1676 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.1607 |
| 5 | `session=europe` | 0.1147 |
| 6 | `session=overlap` | 0.0499 |
| 7 | `session=closed` | 0.0248 |
| 8 | `near_resistance=NA` | 0.0100 |
| 9 | `volatility_regime=NA` | 0.0096 |
| 10 | `rsi_extreme=NA` | 0.0090 |
| 11 | `consec_red_M30=[0,2)` | 0.0086 |
| 12 | `M30_ema_stack=NA` | 0.0080 |
| 13 | `overbought=NA` | 0.0071 |
| 14 | `volatility_regime=low` | 0.0071 |
| 15 | `bb_extreme_lower=NA` | 0.0071 |

---

## XAUUSD · smc · SELL
- Toplam çözülmüş: **1108**  ·  Baseline win-rate: **47.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 29.4%** (73 W / 175 L = 248 trade · -18.4pp vs baseline)
   - `session = us`
   - `consec_green_M30 = NA`
   - `ml_confidence_bucket ≠ [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.2150 |
| 2 | `session=asia` | 0.1319 |
| 3 | `session=overlap` | 0.0869 |
| 4 | `session=closed` | 0.0862 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0817 |
| 6 | `session=europe` | 0.0768 |
| 7 | `consec_red_M30=[0,2)` | 0.0583 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0557 |
| 9 | `rsi_M30=[30,50)` | 0.0256 |
| 10 | `sar_bearish=True` | 0.0177 |
| 11 | `bb_pctb_M30=[0.2,0.5)` | 0.0169 |
| 12 | `exhaustion_down=False` | 0.0117 |
| 13 | `adx_M30=[25,35)` | 0.0100 |
| 14 | `oversold=False` | 0.0061 |
| 15 | `rsi_extreme=False` | 0.0061 |

---
