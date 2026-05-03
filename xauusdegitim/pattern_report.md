# Pattern Mining Raporu
_2026-05-03T23:03:47.447526Z — son 60 gün — 50000 resolved sinyal_

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

**1. Win-rate 99.0%** (585 W / 6 L = 591 trade · +33.8pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `volatility_regime = normal`

**2. Win-rate 97.9%** (138 W / 3 L = 141 trade · +32.7pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 ≠ NA`
   - `rsi_H1 = [50,65)`
   - `macro_alignment ≠ strong_pro`

**3. Win-rate 95.9%** (188 W / 8 L = 196 trade · +30.7pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `volatility_regime ≠ normal`

**4. Win-rate 84.8%** (78 W / 14 L = 92 trade · +19.6pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 ≠ NA`
   - `rsi_H1 = [50,65)`
   - `macro_alignment = strong_pro`

**5. Win-rate 78.6%** (3004 W / 820 L = 3824 trade · +13.4pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 = NA`
   - `dow ≠ Sun`
   - `hour_bucket = 20-24`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.5%** (137 W / 380 L = 517 trade · -38.7pp vs baseline)
   - `session_phase = any`
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket ≠ [−∞,50)`

**2. Win-rate 33.6%** (80 W / 158 L = 238 trade · -31.6pp vs baseline)
   - `session_phase = any`
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 34.4%** (45 W / 86 L = 131 trade · -30.8pp vs baseline)
   - `session_phase ≠ any`
   - `bb_pctb_M30 = NA`
   - `dow = Sun`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=any` | 0.3246 |
| 2 | `session_phase=off_hours` | 0.1292 |
| 3 | `session_phase=late_pit` | 0.0351 |
| 4 | `dow=Thu` | 0.0202 |
| 5 | `H4_ema_stack=NA` | 0.0189 |
| 6 | `H4_adx_label=trending` | 0.0186 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0158 |
| 8 | `adx_H4=NA` | 0.0157 |
| 9 | `H4_ema_stack=up` | 0.0153 |
| 10 | `adx_H4=[25,35)` | 0.0143 |
| 11 | `H4_adx_label=NA` | 0.0128 |
| 12 | `dow=Tue` | 0.0128 |
| 13 | `dow=Mon` | 0.0124 |
| 14 | `hour_bucket=12-16` | 0.0122 |
| 15 | `session_phase=after_hours` | 0.0111 |

---

## GDAXI.INDX · emel
- Toplam çözülmüş: **132**  ·  Baseline win-rate: **72.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.2%** (37 W / 4 L = 41 trade · +18.2pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.2150 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1354 |
| 3 | `dow=Tue` | 0.1095 |
| 4 | `session=europe` | 0.0814 |
| 5 | `hour_bucket=04-08` | 0.0784 |
| 6 | `hour_bucket=08-12` | 0.0689 |
| 7 | `session=asia` | 0.0613 |
| 8 | `hour_bucket=12-16` | 0.0530 |
| 9 | `session_phase=open_drive` | 0.0486 |
| 10 | `session=overlap` | 0.0421 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0420 |
| 12 | `dow=Mon` | 0.0369 |
| 13 | `session_phase=after_hours` | 0.0269 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **190**  ·  Baseline win-rate: **85.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +14.7pp vs baseline)
   - `session = overlap`
   - `session_phase = open_drive`

**2. Win-rate 96.7%** (29 W / 1 L = 30 trade · +11.4pp vs baseline)
   - `session = overlap`
   - `session_phase ≠ open_drive`

**3. Win-rate 93.3%** (28 W / 2 L = 30 trade · +8.0pp vs baseline)
   - `session ≠ overlap`
   - `hour_bucket = 08-12`
   - `dow ≠ Mon`
   - `dow = Tue`

**4. Win-rate 89.2%** (33 W / 4 L = 37 trade · +3.9pp vs baseline)
   - `session ≠ overlap`
   - `hour_bucket = 08-12`
   - `dow ≠ Mon`
   - `dow ≠ Tue`

**5. Win-rate 78.3%** (18 W / 5 L = 23 trade · -7.0pp vs baseline)
   - `session ≠ overlap`
   - `hour_bucket = 08-12`
   - `dow = Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1750 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.1238 |
| 3 | `dow=Thu` | 0.0881 |
| 4 | `dow=Tue` | 0.0761 |
| 5 | `session_phase=after_hours` | 0.0687 |
| 6 | `dow=Mon` | 0.0659 |
| 7 | `session=europe` | 0.0626 |
| 8 | `hour_bucket=08-12` | 0.0544 |
| 9 | `session_phase=open_drive` | 0.0542 |
| 10 | `session=asia` | 0.0535 |
| 11 | `hour_bucket=12-16` | 0.0441 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0380 |
| 13 | `dow=Fri` | 0.0336 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0310 |
| 15 | `hour_bucket=04-08` | 0.0266 |

---

## GDAXI.INDX · ml:balanced
- Toplam çözülmüş: **124**  ·  Baseline win-rate: **75.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +15.1pp vs baseline)
   - `hour_bucket ≠ 08-12`
   - `dow ≠ Mon`
   - `session ≠ overlap`

**2. Win-rate 83.3%** (20 W / 4 L = 24 trade · +7.5pp vs baseline)
   - `hour_bucket ≠ 08-12`
   - `dow = Mon`

**3. Win-rate 81.2%** (26 W / 6 L = 32 trade · +5.4pp vs baseline)
   - `hour_bucket ≠ 08-12`
   - `dow ≠ Mon`
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=08-12` | 0.1949 |
| 2 | `hour_bucket=12-16` | 0.1418 |
| 3 | `session=europe` | 0.1109 |
| 4 | `session=overlap` | 0.1002 |
| 5 | `dow=Tue` | 0.0827 |
| 6 | `dow=Mon` | 0.0661 |
| 7 | `session_phase=after_hours` | 0.0548 |
| 8 | `dow=Thu` | 0.0539 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0504 |
| 10 | `dow=Fri` | 0.0475 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0288 |
| 12 | `session_phase=open_drive` | 0.0280 |
| 13 | `hour_bucket=04-08` | 0.0176 |
| 14 | `dow=Wed` | 0.0138 |
| 15 | `session=asia` | 0.0085 |

---

## GDAXI.INDX · ml:full_power
- Toplam çözülmüş: **151**  ·  Baseline win-rate: **75.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.1%** (41 W / 4 L = 45 trade · +15.6pp vs baseline)
   - `hour_bucket = 12-16`
   - `session_phase ≠ open_drive`

**2. Win-rate 81.0%** (17 W / 4 L = 21 trade · +5.5pp vs baseline)
   - `hour_bucket = 12-16`
   - `session_phase = open_drive`

**3. Win-rate 76.2%** (16 W / 5 L = 21 trade · +0.7pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 08-12`

**4. Win-rate 76.2%** (16 W / 5 L = 21 trade · +0.7pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `hour_bucket = 08-12`
   - `dow = Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=08-12` | 0.1897 |
| 2 | `hour_bucket=12-16` | 0.1609 |
| 3 | `session=europe` | 0.0945 |
| 4 | `dow=Mon` | 0.0882 |
| 5 | `session=overlap` | 0.0851 |
| 6 | `dow=Fri` | 0.0767 |
| 7 | `session_phase=after_hours` | 0.0525 |
| 8 | `dow=Thu` | 0.0425 |
| 9 | `dow=Tue` | 0.0420 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0419 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0413 |
| 12 | `hour_bucket=04-08` | 0.0406 |
| 13 | `session_phase=open_drive` | 0.0260 |
| 14 | `dow=Wed` | 0.0137 |

---

## GDAXI.INDX · ml:main
- Toplam çözülmüş: **177**  ·  Baseline win-rate: **78.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +12.9pp vs baseline)
   - `hour_bucket = 12-16`
   - `session_phase = after_hours`
   - `session ≠ overlap`

**2. Win-rate 89.7%** (26 W / 3 L = 29 trade · +11.7pp vs baseline)
   - `hour_bucket = 12-16`
   - `session_phase = after_hours`
   - `session = overlap`

**3. Win-rate 87.5%** (21 W / 3 L = 24 trade · +9.5pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `dow = Thu`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · +1.2pp vs baseline)
   - `hour_bucket = 12-16`
   - `session_phase ≠ after_hours`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.1527 |
| 2 | `hour_bucket=08-12` | 0.1072 |
| 3 | `dow=Fri` | 0.1061 |
| 4 | `dow=Thu` | 0.0968 |
| 5 | `session=overlap` | 0.0830 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0667 |
| 7 | `session_phase=after_hours` | 0.0628 |
| 8 | `dow=Mon` | 0.0613 |
| 9 | `dow=Tue` | 0.0505 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0501 |
| 11 | `session_phase=open_drive` | 0.0483 |
| 12 | `session=europe` | 0.0403 |
| 13 | `session=asia` | 0.0383 |
| 14 | `dow=Wed` | 0.0194 |
| 15 | `hour_bucket=04-08` | 0.0166 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **1433**  ·  Baseline win-rate: **57.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.1%** (139 W / 12 L = 151 trade · +34.5pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 08-12`
   - `session_phase ≠ open_drive`
   - `hour_bucket ≠ 04-08`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.0%** (7 W / 81 L = 88 trade · -49.6pp vs baseline)
   - `dow ≠ Tue`
   - `ml_confidence_bucket = [50,60)`
   - `dow = Thu`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1273 |
| 2 | `dow=Tue` | 0.1254 |
| 3 | `dow=Thu` | 0.1192 |
| 4 | `hour_bucket=08-12` | 0.1051 |
| 5 | `hour_bucket=12-16` | 0.0897 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0571 |
| 7 | `dow=Mon` | 0.0571 |
| 8 | `session=overlap` | 0.0560 |
| 9 | `session=europe` | 0.0473 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0465 |
| 11 | `dow=Fri` | 0.0306 |
| 12 | `dow=Wed` | 0.0240 |
| 13 | `session=asia` | 0.0207 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0179 |
| 15 | `session_phase=mid_session` | 0.0174 |

---

## GDAXI.INDX · pulse2
- Toplam çözülmüş: **610**  ·  Baseline win-rate: **74.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (58 W / 2 L = 60 trade · +22.6pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session ≠ europe`

**2. Win-rate 95.5%** (42 W / 2 L = 44 trade · +21.4pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session = europe`

**3. Win-rate 89.8%** (53 W / 6 L = 59 trade · +15.7pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`

**4. Win-rate 85.7%** (18 W / 3 L = 21 trade · +11.6pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket = 12-16`
   - `session ≠ overlap`

**5. Win-rate 81.8%** (18 W / 4 L = 22 trade · +7.7pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket = 12-16`
   - `session = overlap`
   - `dow = Fri`

**6. Win-rate 78.0%** (39 W / 11 L = 50 trade · +3.9pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.2098 |
| 2 | `hour_bucket=12-16` | 0.1441 |
| 3 | `dow=Fri` | 0.1321 |
| 4 | `dow=Mon` | 0.0806 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0719 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0679 |
| 7 | `session=asia` | 0.0599 |
| 8 | `hour_bucket=04-08` | 0.0465 |
| 9 | `session=overlap` | 0.0416 |
| 10 | `hour_bucket=08-12` | 0.0378 |
| 11 | `dow=Wed` | 0.0261 |
| 12 | `session=europe` | 0.0207 |
| 13 | `ml_confidence_bucket=[−∞,50)` | 0.0194 |
| 14 | `session_phase=open_drive` | 0.0157 |
| 15 | `dow=Thu` | 0.0132 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **1249**  ·  Baseline win-rate: **70.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.4%** (76 W / 2 L = 78 trade · +26.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow ≠ Tue`
   - `dow = Thu`
   - `session ≠ overlap`

**2. Win-rate 95.1%** (39 W / 2 L = 41 trade · +24.6pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow ≠ Thu`
   - `hour_bucket = 12-16`
   - `dow = Tue`

**3. Win-rate 93.8%** (196 W / 13 L = 209 trade · +23.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow = Tue`
   - `session ≠ asia`
   - `session_phase ≠ open_drive`

**4. Win-rate 89.7%** (35 W / 4 L = 39 trade · +19.2pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow ≠ Thu`
   - `hour_bucket = 12-16`
   - `dow ≠ Tue`

**5. Win-rate 81.1%** (30 W / 7 L = 37 trade · +10.6pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow ≠ Tue`
   - `dow = Thu`
   - `session = overlap`

**6. Win-rate 77.8%** (21 W / 6 L = 27 trade · +7.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow = Tue`
   - `session ≠ asia`
   - `session_phase = open_drive`

**7. Win-rate 77.4%** (212 W / 62 L = 274 trade · +6.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow ≠ Tue`
   - `dow ≠ Thu`
   - `hour_bucket ≠ 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.8%** (11 W / 91 L = 102 trade · -59.7pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow = Thu`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1697 |
| 2 | `dow=Tue` | 0.1344 |
| 3 | `dow=Thu` | 0.1141 |
| 4 | `hour_bucket=08-12` | 0.1074 |
| 5 | `hour_bucket=12-16` | 0.0821 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0680 |
| 7 | `dow=Fri` | 0.0574 |
| 8 | `session=europe` | 0.0554 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0390 |
| 10 | `dow=Mon` | 0.0369 |
| 11 | `session=overlap` | 0.0341 |
| 12 | `session=asia` | 0.0337 |
| 13 | `hour_bucket=04-08` | 0.0233 |
| 14 | `session_phase=after_hours` | 0.0106 |
| 15 | `session_phase=open_drive` | 0.0105 |

---

## GDAXI.INDX · smc
- Toplam çözülmüş: **273**  ·  Baseline win-rate: **58.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.4%** (37 W / 1 L = 38 trade · +39.2pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket = 12-16`

**2. Win-rate 94.0%** (47 W / 3 L = 50 trade · +35.8pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dow = Thu`

**3. Win-rate 82.8%** (24 W / 5 L = 29 trade · +24.6pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dow ≠ Thu`

**4. Win-rate 81.8%** (18 W / 4 L = 22 trade · +23.6pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [80,+∞)`
   - `dow = Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.0%** (6 W / 69 L = 75 trade · -50.2pp vs baseline)
   - `dow = Fri`
   - `hour_bucket = 08-12`

**2. Win-rate 31.6%** (12 W / 26 L = 38 trade · -26.6pp vs baseline)
   - `dow = Fri`
   - `hour_bucket ≠ 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.2902 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.2155 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.1732 |
| 4 | `dow=Thu` | 0.1321 |
| 5 | `dow=Mon` | 0.0534 |
| 6 | `session=overlap` | 0.0444 |
| 7 | `hour_bucket=04-08` | 0.0285 |
| 8 | `dow=Tue` | 0.0194 |
| 9 | `session=europe` | 0.0161 |
| 10 | `session=asia` | 0.0106 |
| 11 | `hour_bucket=08-12` | 0.0077 |
| 12 | `hour_bucket=12-16` | 0.0062 |

---

## NDX.INDX · emel
- Toplam çözülmüş: **172**  ·  Baseline win-rate: **57.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.5%** (47 W / 8 L = 55 trade · +28.5pp vs baseline)
   - `session_phase = after_hours`

**2. Win-rate 78.1%** (25 W / 7 L = 32 trade · +21.1pp vs baseline)
   - `session_phase ≠ after_hours`
   - `dow ≠ Fri`
   - `dow ≠ Tue`
   - `ml_confidence_bucket ≠ [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.5%** (1 W / 21 L = 22 trade · -52.5pp vs baseline)
   - `session_phase ≠ after_hours`
   - `dow = Fri`

**2. Win-rate 13.6%** (3 W / 19 L = 22 trade · -43.4pp vs baseline)
   - `session_phase ≠ after_hours`
   - `dow ≠ Fri`
   - `dow = Tue`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=after_hours` | 0.1531 |
| 2 | `dow=Mon` | 0.1237 |
| 3 | `dow=Fri` | 0.1177 |
| 4 | `session_phase=mid_session` | 0.0991 |
| 5 | `hour_bucket=16-20` | 0.0833 |
| 6 | `dow=Tue` | 0.0737 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0689 |
| 8 | `session_phase=close_drive` | 0.0484 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0480 |
| 10 | `hour_bucket=12-16` | 0.0436 |
| 11 | `dow=Thu` | 0.0406 |
| 12 | `session=overlap` | 0.0322 |
| 13 | `session=us` | 0.0286 |
| 14 | `session_phase=open_drive` | 0.0255 |
| 15 | `ml_confidence_bucket=[−∞,50)` | 0.0137 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **189**  ·  Baseline win-rate: **78.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.0%** (19 W / 1 L = 20 trade · +16.2pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket ≠ 16-20`
   - `session_phase = after_hours`

**2. Win-rate 90.0%** (18 W / 2 L = 20 trade · +11.2pp vs baseline)
   - `session ≠ overlap`
   - `dow ≠ Fri`
   - `dow = Mon`

**3. Win-rate 89.7%** (26 W / 3 L = 29 trade · +10.9pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket ≠ 16-20`
   - `session_phase ≠ after_hours`

**4. Win-rate 88.0%** (22 W / 3 L = 25 trade · +9.2pp vs baseline)
   - `session ≠ overlap`
   - `dow = Fri`

**5. Win-rate 81.8%** (27 W / 6 L = 33 trade · +3.0pp vs baseline)
   - `session = overlap`
   - `dow = Fri`

**6. Win-rate 81.0%** (17 W / 4 L = 21 trade · +2.2pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket = 16-20`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1062 |
| 2 | `hour_bucket=12-16` | 0.0912 |
| 3 | `hour_bucket=16-20` | 0.0863 |
| 4 | `dow=Mon` | 0.0825 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0767 |
| 6 | `session_phase=close_drive` | 0.0630 |
| 7 | `session=overlap` | 0.0616 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0524 |
| 9 | `dow=Fri` | 0.0508 |
| 10 | `session_phase=mid_session` | 0.0397 |
| 11 | `dow=Wed` | 0.0371 |
| 12 | `session_phase=after_hours` | 0.0363 |
| 13 | `dow=Tue` | 0.0312 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0312 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0234 |

---

## NDX.INDX · ml:balanced
- Toplam çözülmüş: **115**  ·  Baseline win-rate: **79.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (28 W / 4 L = 32 trade · +8.4pp vs baseline)
   - `dow ≠ Thu`
   - `session_phase ≠ mid_session`

**2. Win-rate 84.0%** (21 W / 4 L = 25 trade · +4.9pp vs baseline)
   - `dow ≠ Thu`
   - `session_phase = mid_session`
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.1125 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1081 |
| 3 | `hour_bucket=16-20` | 0.0991 |
| 4 | `session=overlap` | 0.0929 |
| 5 | `session=us` | 0.0869 |
| 6 | `session_phase=mid_session` | 0.0814 |
| 7 | `dow=Tue` | 0.0788 |
| 8 | `session_phase=open_drive` | 0.0767 |
| 9 | `hour_bucket=12-16` | 0.0766 |
| 10 | `ml_confidence_bucket=[−∞,50)` | 0.0754 |
| 11 | `dow=Mon` | 0.0596 |
| 12 | `session_phase=after_hours` | 0.0246 |
| 13 | `session_phase=close_drive` | 0.0205 |
| 14 | `dow=Wed` | 0.0069 |

---

## NDX.INDX · ml:full_power
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **78.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.3%** (36 W / 3 L = 39 trade · +13.9pp vs baseline)
   - `hour_bucket = 12-16`

**2. Win-rate 80.0%** (20 W / 5 L = 25 trade · +1.6pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.1410 |
| 2 | `session=us` | 0.1309 |
| 3 | `session=overlap` | 0.1055 |
| 4 | `hour_bucket=16-20` | 0.0976 |
| 5 | `dow=Tue` | 0.0916 |
| 6 | `session_phase=mid_session` | 0.0911 |
| 7 | `dow=Thu` | 0.0775 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0721 |
| 9 | `session_phase=open_drive` | 0.0641 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0568 |
| 11 | `dow=Mon` | 0.0310 |
| 12 | `session_phase=close_drive` | 0.0242 |
| 13 | `session_phase=after_hours` | 0.0084 |
| 14 | `dow=Wed` | 0.0080 |

---

## NDX.INDX · ml:main
- Toplam çözülmüş: **115**  ·  Baseline win-rate: **73.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +18.3pp vs baseline)
   - `dow = Wed`

**2. Win-rate 85.7%** (30 W / 5 L = 35 trade · +12.7pp vs baseline)
   - `dow ≠ Wed`
   - `hour_bucket = 12-16`

**3. Win-rate 75.0%** (15 W / 5 L = 20 trade · +2.0pp vs baseline)
   - `dow ≠ Wed`
   - `hour_bucket ≠ 12-16`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.1601 |
| 2 | `session=us` | 0.1272 |
| 3 | `dow=Wed` | 0.1099 |
| 4 | `session=overlap` | 0.0961 |
| 5 | `dow=Thu` | 0.0730 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0694 |
| 7 | `hour_bucket=16-20` | 0.0657 |
| 8 | `session_phase=close_drive` | 0.0616 |
| 9 | `dow=Tue` | 0.0589 |
| 10 | `session_phase=open_drive` | 0.0504 |
| 11 | `session_phase=mid_session` | 0.0459 |
| 12 | `dow=Mon` | 0.0409 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0272 |
| 14 | `session_phase=after_hours` | 0.0137 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **1279**  ·  Baseline win-rate: **65.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (27 W / 9 L = 36 trade · +10.0pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Wed`
   - `dow ≠ Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.1%** (3 W / 70 L = 73 trade · -60.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow = Wed`
   - `session ≠ overlap`

**2. Win-rate 27.3%** (6 W / 16 L = 22 trade · -37.7pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow = Wed`
   - `session = overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1770 |
| 2 | `dow=Wed` | 0.1707 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0636 |
| 4 | `hour_bucket=12-16` | 0.0526 |
| 5 | `dow=Mon` | 0.0501 |
| 6 | `session=us` | 0.0480 |
| 7 | `hour_bucket=16-20` | 0.0369 |
| 8 | `session=overlap` | 0.0365 |
| 9 | `session_phase=close_drive` | 0.0321 |
| 10 | `session_phase=mid_session` | 0.0319 |
| 11 | `dow=Fri` | 0.0298 |
| 12 | `dow=Tue` | 0.0289 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0266 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0251 |
| 15 | `session_phase=open_drive` | 0.0178 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **843**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.5%** (138 W / 5 L = 143 trade · +24.6pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Thu`
   - `dow ≠ Tue`
   - `session_phase = mid_session`

**2. Win-rate 92.1%** (35 W / 3 L = 38 trade · +20.2pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session_phase ≠ close_drive`
   - `ml_confidence_bucket = [60,70)`
   - `hour_bucket ≠ 16-20`

**3. Win-rate 87.8%** (43 W / 6 L = 49 trade · +15.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Thu`
   - `dow ≠ Tue`
   - `session_phase ≠ mid_session`

**4. Win-rate 77.3%** (17 W / 5 L = 22 trade · +5.4pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Thu`
   - `dow = Tue`

**5. Win-rate 75.0%** (15 W / 5 L = 20 trade · +3.1pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow = Thu`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.2126 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1742 |
| 3 | `dow=Mon` | 0.0655 |
| 4 | `session_phase=mid_session` | 0.0573 |
| 5 | `dow=Fri` | 0.0473 |
| 6 | `dow=Wed` | 0.0423 |
| 7 | `dow=Tue` | 0.0413 |
| 8 | `dow=Thu` | 0.0293 |
| 9 | `hour_bucket=16-20` | 0.0277 |
| 10 | `session=us` | 0.0262 |
| 11 | `hour_bucket=12-16` | 0.0259 |
| 12 | `session_phase=close_drive` | 0.0249 |
| 13 | `session_phase=after_hours` | 0.0247 |
| 14 | `session=overlap` | 0.0222 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0197 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **1172**  ·  Baseline win-rate: **64.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.8%** (30 W / 2 L = 32 trade · +29.1pp vs baseline)
   - `dow = Wed`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 86.7%** (26 W / 4 L = 30 trade · +22.0pp vs baseline)
   - `dow ≠ Wed`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 81.8%** (283 W / 63 L = 346 trade · +17.1pp vs baseline)
   - `dow ≠ Wed`
   - `ml_confidence_bucket = [60,70)`
   - `H4_adx_label ≠ trending`
   - `session_phase ≠ after_hours`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (14 W / 84 L = 98 trade · -50.4pp vs baseline)
   - `dow = Wed`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `hour_bucket = 16-20`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -29.7pp vs baseline)
   - `dow ≠ Wed`
   - `ml_confidence_bucket = [60,70)`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1285 |
| 2 | `dow=Wed` | 0.1206 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.1147 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0781 |
| 5 | `dow=Mon` | 0.0603 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0466 |
| 7 | `session_phase=close_drive` | 0.0392 |
| 8 | `dow=Fri` | 0.0379 |
| 9 | `hour_bucket=16-20` | 0.0359 |
| 10 | `hour_bucket=12-16` | 0.0323 |
| 11 | `session=overlap` | 0.0320 |
| 12 | `session=us` | 0.0301 |
| 13 | `dow=Thu` | 0.0290 |
| 14 | `session_phase=mid_session` | 0.0283 |
| 15 | `dow=Tue` | 0.0241 |

---

## USOIL.FOREX · ai_panel
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **79.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +20.2pp vs baseline)
   - `session_phase = late_pit`

**2. Win-rate 76.0%** (19 W / 6 L = 25 trade · -3.8pp vs baseline)
   - `session_phase ≠ late_pit`
   - `session_phase = active_pit`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=late_pit` | 0.1572 |
| 2 | `session=us` | 0.1553 |
| 3 | `session=overlap` | 0.1427 |
| 4 | `hour_bucket=12-16` | 0.1332 |
| 5 | `session_phase=active_pit` | 0.1095 |
| 6 | `session_phase=early_pit` | 0.0868 |
| 7 | `hour_bucket=16-20` | 0.0559 |
| 8 | `dow=Tue` | 0.0461 |
| 9 | `dow=Mon` | 0.0380 |
| 10 | `dow=Fri` | 0.0371 |
| 11 | `dow=Thu` | 0.0306 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0078 |

---

## USOIL.FOREX · emel
- Toplam çözülmüş: **1002**  ·  Baseline win-rate: **65.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +21.7pp vs baseline)
   - `session ≠ closed`
   - `dow ≠ Fri`
   - `session_phase = late_pit`
   - `dow = Wed`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1049 |
| 2 | `dow=Tue` | 0.0986 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0851 |
| 4 | `dow=Mon` | 0.0743 |
| 5 | `dow=Fri` | 0.0701 |
| 6 | `dow=Wed` | 0.0540 |
| 7 | `hour_bucket=04-08` | 0.0479 |
| 8 | `session_phase=early_pit` | 0.0476 |
| 9 | `hour_bucket=00-04` | 0.0444 |
| 10 | `session=europe` | 0.0425 |
| 11 | `dow=Thu` | 0.0425 |
| 12 | `hour_bucket=20-24` | 0.0359 |
| 13 | `session=closed` | 0.0344 |
| 14 | `session=overlap` | 0.0320 |
| 15 | `session=asia` | 0.0311 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **728**  ·  Baseline win-rate: **73.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.4%** (37 W / 1 L = 38 trade · +23.5pp vs baseline)
   - `rsi_H1 = [30,50)`

**2. Win-rate 88.2%** (30 W / 4 L = 34 trade · +14.3pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `dow ≠ Fri`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 76.1%** (354 W / 111 L = 465 trade · +2.2pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `dow ≠ Fri`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0895 |
| 2 | `dow=Thu` | 0.0472 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0409 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0396 |
| 5 | `dow=Tue` | 0.0328 |
| 6 | `dow=Wed` | 0.0303 |
| 7 | `rsi_H1=[30,50)` | 0.0289 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0288 |
| 9 | `dow=Mon` | 0.0269 |
| 10 | `hour_bucket=20-24` | 0.0238 |
| 11 | `session_phase=active_pit` | 0.0220 |
| 12 | `session=us` | 0.0218 |
| 13 | `session_phase=late_pit` | 0.0214 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0210 |
| 15 | `session=europe` | 0.0203 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **82.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +17.6pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 100.0%** (42 W / 0 L = 42 trade · +17.6pp vs baseline)
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 83.8%** (31 W / 6 L = 37 trade · +1.4pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**4. Win-rate 76.8%** (53 W / 16 L = 69 trade · -5.6pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `dow ≠ Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.0621 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0476 |
| 3 | `overbought=False` | 0.0475 |
| 4 | `regime_label=transition` | 0.0450 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0399 |
| 6 | `dow=Thu` | 0.0395 |
| 7 | `exhaustion_down=False` | 0.0331 |
| 8 | `near_resistance=False` | 0.0324 |
| 9 | `M30_ema_stack=mixed` | 0.0320 |
| 10 | `mtf_trend=mixed` | 0.0303 |
| 11 | `H4_ema_stack=up` | 0.0293 |
| 12 | `session=us` | 0.0262 |
| 13 | `bb_extreme_lower=NA` | 0.0241 |
| 14 | `dow=Mon` | 0.0236 |
| 15 | `exhaustion_up=False` | 0.0224 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **1061**  ·  Baseline win-rate: **71.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.2%** (472 W / 156 L = 628 trade · +3.6pp vs baseline)
   - `H4_ema_stack = NA`
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow ≠ Wed`

**2. Win-rate 75.0%** (36 W / 12 L = 48 trade · +3.4pp vs baseline)
   - `H4_ema_stack = NA`
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket = [60,70)`
   - `dow ≠ Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=00-04` | 0.0547 |
| 2 | `dow=Mon` | 0.0505 |
| 3 | `session=asia` | 0.0449 |
| 4 | `dow=Wed` | 0.0440 |
| 5 | `dow=Tue` | 0.0415 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0407 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0380 |
| 8 | `dow=Thu` | 0.0372 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0339 |
| 10 | `hour_bucket=20-24` | 0.0316 |
| 11 | `session=europe` | 0.0274 |
| 12 | `hour_bucket=12-16` | 0.0249 |
| 13 | `hour_bucket=04-08` | 0.0240 |
| 14 | `session_phase=off_hours` | 0.0226 |
| 15 | `hour_bucket=08-12` | 0.0225 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **1096**  ·  Baseline win-rate: **71.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (33 W / 0 L = 33 trade · +28.2pp vs baseline)
   - `H4_adx_label = trending`

**2. Win-rate 80.7%** (134 W / 32 L = 166 trade · +8.9pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0507 |
| 2 | `dow=Wed` | 0.0463 |
| 3 | `dow=Thu` | 0.0415 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0414 |
| 5 | `session=asia` | 0.0411 |
| 6 | `hour_bucket=00-04` | 0.0411 |
| 7 | `dow=Tue` | 0.0411 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0387 |
| 9 | `session=us` | 0.0326 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0306 |
| 11 | `dow=Fri` | 0.0291 |
| 12 | `hour_bucket=20-24` | 0.0291 |
| 13 | `hour_bucket=12-16` | 0.0275 |
| 14 | `near_resistance=False` | 0.0260 |
| 15 | `session_phase=off_hours` | 0.0255 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **1225**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +13.8pp vs baseline)
   - `H4_ema_stack = NA`
   - `hour_bucket ≠ 00-04`
   - `dow = Fri`
   - `session = europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0583 |
| 2 | `dow=Mon` | 0.0560 |
| 3 | `dow=Wed` | 0.0468 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0467 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0445 |
| 6 | `dow=Fri` | 0.0403 |
| 7 | `hour_bucket=00-04` | 0.0368 |
| 8 | `dow=Tue` | 0.0353 |
| 9 | `hour_bucket=12-16` | 0.0287 |
| 10 | `hour_bucket=16-20` | 0.0260 |
| 11 | `session=asia` | 0.0258 |
| 12 | `session=us` | 0.0243 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0239 |
| 14 | `hour_bucket=20-24` | 0.0235 |
| 15 | `hour_bucket=04-08` | 0.0230 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **175**  ·  Baseline win-rate: **86.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.6%** (28 W / 1 L = 29 trade · +10.3pp vs baseline)
   - `H4_ema_stack = NA`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 87.1%** (27 W / 4 L = 31 trade · +0.8pp vs baseline)
   - `H4_ema_stack = NA`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`

**3. Win-rate 83.6%** (51 W / 10 L = 61 trade · -2.7pp vs baseline)
   - `H4_ema_stack = NA`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `dow ≠ Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0567 |
| 2 | `dow=Thu` | 0.0367 |
| 3 | `hour_bucket=20-24` | 0.0338 |
| 4 | `bb_pctb_M30=NA` | 0.0318 |
| 5 | `H4_adx_label=NA` | 0.0312 |
| 6 | `consec_red_M30=NA` | 0.0304 |
| 7 | `rsi_M30=NA` | 0.0271 |
| 8 | `adx_M30=NA` | 0.0259 |
| 9 | `volatility_regime=NA` | 0.0242 |
| 10 | `bb_extreme_lower=NA` | 0.0238 |
| 11 | `consec_green_M30=NA` | 0.0221 |
| 12 | `atr_ratio_M30=NA` | 0.0217 |
| 13 | `dist_low_M30=NA` | 0.0215 |
| 14 | `dow=Tue` | 0.0203 |
| 15 | `exhaustion_up=NA` | 0.0194 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **6731**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (134 W / 0 L = 134 trade · +27.2pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `consec_red_M30 ≠ [2,4)`
   - `hour_bucket ≠ 16-20`

**2. Win-rate 100.0%** (29 W / 0 L = 29 trade · +27.2pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `consec_red_M30 = [2,4)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**3. Win-rate 100.0%** (20 W / 0 L = 20 trade · +27.2pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 = [50,65)`
   - `macro_alignment ≠ strong_pro`
   - `macro_alignment ≠ neutral`

**4. Win-rate 98.0%** (50 W / 1 L = 51 trade · +25.2pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `consec_red_M30 ≠ [2,4)`
   - `hour_bucket = 16-20`

**5. Win-rate 95.7%** (22 W / 1 L = 23 trade · +22.9pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 = [50,65)`
   - `macro_alignment ≠ strong_pro`
   - `macro_alignment = neutral`

**6. Win-rate 91.4%** (32 W / 3 L = 35 trade · +18.6pp vs baseline)
   - `H1_ema_stack = NA`
   - `dow = Wed`
   - `hour_bucket = 20-24`
   - `ml_confidence_bucket = [70,80)`

**7. Win-rate 89.3%** (25 W / 3 L = 28 trade · +16.5pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 ≠ [50,65)`
   - `consec_red_M30 = [2,4)`
   - `dist_low_M30 = [1.5,+∞)`

**8. Win-rate 83.8%** (31 W / 6 L = 37 trade · +11.0pp vs baseline)
   - `H1_ema_stack ≠ NA`
   - `rsi_H1 = [50,65)`
   - `macro_alignment = strong_pro`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0522 |
| 2 | `dow=Tue` | 0.0459 |
| 3 | `dow=Wed` | 0.0420 |
| 4 | `exhaustion_up=False` | 0.0411 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0402 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0380 |
| 7 | `H4_adx_label=trending` | 0.0329 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0307 |
| 9 | `dow=Thu` | 0.0274 |
| 10 | `near_resistance=False` | 0.0259 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0258 |
| 12 | `overbought=False` | 0.0256 |
| 13 | `dow=Fri` | 0.0248 |
| 14 | `hour_bucket=20-24` | 0.0237 |
| 15 | `rsi_extreme=False` | 0.0222 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **4979**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (47 W / 0 L = 47 trade · +27.2pp vs baseline)
   - `dow ≠ Sun`
   - `near_resistance = False`
   - `atr_ratio_M30 = [1,1.3)`

**2. Win-rate 93.2%** (68 W / 5 L = 73 trade · +20.4pp vs baseline)
   - `dow ≠ Sun`
   - `near_resistance = False`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `consec_red_M30 ≠ [2,4)`

**3. Win-rate 85.0%** (17 W / 3 L = 20 trade · +12.2pp vs baseline)
   - `dow ≠ Sun`
   - `near_resistance = False`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `consec_red_M30 = [2,4)`

**4. Win-rate 80.5%** (214 W / 52 L = 266 trade · +7.7pp vs baseline)
   - `dow ≠ Sun`
   - `near_resistance ≠ False`
   - `hour_bucket = 00-04`
   - `dow = Tue`

**5. Win-rate 79.6%** (571 W / 146 L = 717 trade · +6.8pp vs baseline)
   - `dow ≠ Sun`
   - `near_resistance ≠ False`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket = 20-24`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Sun` | 0.1165 |
| 2 | `dow=Tue` | 0.0816 |
| 3 | `dow=Mon` | 0.0759 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0516 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0438 |
| 6 | `hour_bucket=00-04` | 0.0433 |
| 7 | `dow=Wed` | 0.0366 |
| 8 | `dow=Thu` | 0.0350 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0331 |
| 10 | `hour_bucket=20-24` | 0.0307 |
| 11 | `session=us` | 0.0296 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0236 |
| 13 | `session=closed` | 0.0224 |
| 14 | `hour_bucket=04-08` | 0.0221 |
| 15 | `dow=Fri` | 0.0206 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **6100**  ·  Baseline win-rate: **74.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (171 W / 0 L = 171 trade · +26.0pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 ≠ [50,65)`
   - `hour_bucket ≠ 04-08`
   - `consec_green_M30 ≠ [2,4)`

**2. Win-rate 100.0%** (20 W / 0 L = 20 trade · +26.0pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 = [50,65)`
   - `macro_alignment = strong_against`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +21.2pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 ≠ [50,65)`
   - `hour_bucket ≠ 04-08`
   - `consec_green_M30 = [2,4)`

**4. Win-rate 92.9%** (26 W / 2 L = 28 trade · +18.9pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 ≠ [50,65)`
   - `hour_bucket = 04-08`

**5. Win-rate 91.3%** (21 W / 2 L = 23 trade · +17.3pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 = [50,65)`
   - `macro_alignment ≠ strong_against`
   - `dist_high_M30 = [0.7,1.5)`

**6. Win-rate 84.0%** (21 W / 4 L = 25 trade · +10.0pp vs baseline)
   - `M30_adx_label ≠ NA`
   - `rsi_M30 = [50,65)`
   - `macro_alignment ≠ strong_against`
   - `dist_high_M30 ≠ [0.7,1.5)`

**7. Win-rate 83.5%** (96 W / 19 L = 115 trade · +9.5pp vs baseline)
   - `M30_adx_label = NA`
   - `session_phase = off_hours`
   - `dow = Wed`
   - `session = closed`

**8. Win-rate 76.9%** (40 W / 12 L = 52 trade · +2.9pp vs baseline)
   - `M30_adx_label = NA`
   - `session_phase ≠ off_hours`
   - `dow = Tue`
   - `ml_confidence_bucket = [−∞,50)`

**9. Win-rate 76.6%** (2522 W / 771 L = 3293 trade · +2.6pp vs baseline)
   - `M30_adx_label = NA`
   - `session_phase = off_hours`
   - `dow ≠ Wed`
   - `dow ≠ Sun`

**10. Win-rate 75.0%** (228 W / 76 L = 304 trade · +1.0pp vs baseline)
   - `M30_adx_label = NA`
   - `session_phase ≠ off_hours`
   - `dow ≠ Tue`
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.0618 |
| 2 | `dow=Tue` | 0.0485 |
| 3 | `dow=Mon` | 0.0402 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0381 |
| 5 | `dow=Thu` | 0.0369 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0320 |
| 7 | `session_phase=off_hours` | 0.0290 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0276 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0266 |
| 10 | `ml_confidence_bucket=[−∞,50)` | 0.0238 |
| 11 | `session=closed` | 0.0221 |
| 12 | `dow=Fri` | 0.0217 |
| 13 | `dow=Sun` | 0.0205 |
| 14 | `hour_bucket=04-08` | 0.0199 |
| 15 | `hour_bucket=00-04` | 0.0186 |

---

## USOIL.FOREX · smc
- Toplam çözülmüş: **2471**  ·  Baseline win-rate: **85.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +14.4pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session = closed`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 100.0%** (104 W / 0 L = 104 trade · +14.4pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket = 20-24`

**3. Win-rate 100.0%** (27 W / 0 L = 27 trade · +14.4pp vs baseline)
   - `dow = Thu`
   - `session = closed`
   - `ml_confidence_bucket = [70,80)`

**4. Win-rate 98.6%** (71 W / 1 L = 72 trade · +13.0pp vs baseline)
   - `dow ≠ Thu`
   - `dow ≠ Wed`
   - `dow = Fri`
   - `ml_confidence_bucket = [70,80)`

**5. Win-rate 97.2%** (35 W / 1 L = 36 trade · +11.6pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session ≠ closed`
   - `hour_bucket = 16-20`

**6. Win-rate 95.0%** (549 W / 29 L = 578 trade · +9.4pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket ≠ 20-24`

**7. Win-rate 93.3%** (98 W / 7 L = 105 trade · +7.7pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session = closed`
   - `ml_confidence_bucket ≠ [70,80)`

**8. Win-rate 88.9%** (24 W / 3 L = 27 trade · +3.3pp vs baseline)
   - `dow ≠ Thu`
   - `dow ≠ Wed`
   - `dow ≠ Fri`
   - `session = europe`

**9. Win-rate 88.9%** (160 W / 20 L = 180 trade · +3.3pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket = 04-08`
   - `ml_confidence_bucket ≠ [70,80)`

**10. Win-rate 88.3%** (53 W / 7 L = 60 trade · +2.7pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket = 04-08`
   - `ml_confidence_bucket = [70,80)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.2187 |
| 2 | `dow=Fri` | 0.1008 |
| 3 | `dow=Tue` | 0.0760 |
| 4 | `dow=Sun` | 0.0645 |
| 5 | `dow=Wed` | 0.0494 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0458 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0408 |
| 8 | `session=us` | 0.0397 |
| 9 | `dow=Mon` | 0.0353 |
| 10 | `hour_bucket=12-16` | 0.0289 |
| 11 | `hour_bucket=20-24` | 0.0278 |
| 12 | `session=closed` | 0.0268 |
| 13 | `session_phase=off_hours` | 0.0267 |
| 14 | `hour_bucket=08-12` | 0.0227 |
| 15 | `session_phase=late_pit` | 0.0224 |

---

## XAUUSD · ai_panel
- Toplam çözülmüş: **98**  ·  Baseline win-rate: **67.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.4%** (19 W / 3 L = 22 trade · +19.1pp vs baseline)
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.1559 |
| 2 | `hour_bucket=12-16` | 0.1347 |
| 3 | `session=overlap` | 0.1134 |
| 4 | `session=us` | 0.1090 |
| 5 | `hour_bucket=16-20` | 0.1039 |
| 6 | `dow=Mon` | 0.1021 |
| 7 | `dow=Thu` | 0.0779 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0740 |
| 9 | `session=europe` | 0.0735 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0274 |
| 11 | `dow=Wed` | 0.0227 |
| 12 | `dow=Fri` | 0.0055 |

---

## XAUUSD · emel
- Toplam çözülmüş: **444**  ·  Baseline win-rate: **39.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.8%** (4 W / 47 L = 51 trade · -31.6pp vs baseline)
   - `dow = Mon`
   - `hour_bucket = 16-20`

**2. Win-rate 19.3%** (11 W / 46 L = 57 trade · -20.1pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 16-20`
   - `session = closed`

**3. Win-rate 23.1%** (6 W / 20 L = 26 trade · -16.3pp vs baseline)
   - `dow ≠ Mon`
   - `session = asia`
   - `dow = Fri`

**4. Win-rate 29.5%** (13 W / 31 L = 44 trade · -9.9pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 16-20`
   - `session ≠ closed`
   - `ml_confidence_bucket ≠ [60,70)`

**5. Win-rate 34.4%** (11 W / 21 L = 32 trade · -5.0pp vs baseline)
   - `dow ≠ Mon`
   - `session ≠ asia`
   - `session = europe`
   - `ml_confidence_bucket = [60,70)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.2204 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.0916 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0830 |
| 4 | `hour_bucket=00-04` | 0.0634 |
| 5 | `hour_bucket=16-20` | 0.0628 |
| 6 | `session=closed` | 0.0615 |
| 7 | `dow=Tue` | 0.0441 |
| 8 | `session=us` | 0.0403 |
| 9 | `hour_bucket=12-16` | 0.0373 |
| 10 | `dow=Wed` | 0.0369 |
| 11 | `session=europe` | 0.0349 |
| 12 | `session=asia` | 0.0347 |
| 13 | `dow=Thu` | 0.0337 |
| 14 | `dow=Fri` | 0.0332 |
| 15 | `hour_bucket=20-24` | 0.0321 |

---

## XAUUSD · meta
- Toplam çözülmüş: **619**  ·  Baseline win-rate: **64.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.1%** (33 W / 1 L = 34 trade · +33.0pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 00-04`
   - `session = overlap`

**2. Win-rate 89.3%** (25 W / 3 L = 28 trade · +25.2pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 00-04`
   - `session ≠ overlap`
   - `hour_bucket = 20-24`

**3. Win-rate 85.0%** (17 W / 3 L = 20 trade · +20.9pp vs baseline)
   - `dow ≠ Tue`
   - `dow ≠ Wed`
   - `dow = Mon`
   - `ml_confidence_bucket = [50,60)`

**4. Win-rate 76.7%** (66 W / 20 L = 86 trade · +12.6pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 00-04`
   - `session ≠ overlap`
   - `hour_bucket ≠ 20-24`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.8%** (8 W / 18 L = 26 trade · -33.3pp vs baseline)
   - `dow ≠ Tue`
   - `dow = Wed`
   - `session = us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.1869 |
| 2 | `dow=Wed` | 0.0903 |
| 3 | `session=overlap` | 0.0681 |
| 4 | `session=us` | 0.0644 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0495 |
| 6 | `session=asia` | 0.0410 |
| 7 | `dow=Thu` | 0.0408 |
| 8 | `hour_bucket=16-20` | 0.0398 |
| 9 | `dow=Fri` | 0.0369 |
| 10 | `dow=Mon` | 0.0341 |
| 11 | `hour_bucket=00-04` | 0.0334 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0318 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0317 |
| 14 | `hour_bucket=12-16` | 0.0288 |
| 15 | `session=europe` | 0.0275 |

---

## XAUUSD · ml:aggressive
- Toplam çözülmüş: **168**  ·  Baseline win-rate: **51.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (23 W / 5 L = 28 trade · +30.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.8%** (19 W / 39 L = 58 trade · -19.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ overlap`
   - `session ≠ asia`
   - `hour_bucket ≠ 16-20`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0881 |
| 2 | `session=overlap` | 0.0837 |
| 3 | `dow=Thu` | 0.0744 |
| 4 | `session=us` | 0.0547 |
| 5 | `hour_bucket=20-24` | 0.0409 |
| 6 | `session=europe` | 0.0395 |
| 7 | `dow=Tue` | 0.0329 |
| 8 | `dist_low_M30=NA` | 0.0283 |
| 9 | `exhaustion_up=False` | 0.0266 |
| 10 | `dow=Fri` | 0.0263 |
| 11 | `regime_label=transition` | 0.0249 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0239 |
| 13 | `session=asia` | 0.0227 |
| 14 | `atr_ratio_M30=NA` | 0.0224 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0214 |

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
| 1 | `dow=Tue` | 0.0816 |
| 2 | `hour_bucket=12-16` | 0.0677 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0603 |
| 4 | `session=overlap` | 0.0517 |
| 5 | `session=us` | 0.0456 |
| 6 | `dow=Wed` | 0.0451 |
| 7 | `session=asia` | 0.0411 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0410 |
| 9 | `session=closed` | 0.0385 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0385 |
| 11 | `dow=Thu` | 0.0371 |
| 12 | `hour_bucket=16-20` | 0.0357 |
| 13 | `hour_bucket=04-08` | 0.0350 |
| 14 | `hour_bucket=00-04` | 0.0343 |
| 15 | `dow=Mon` | 0.0338 |

---

## XAUUSD · ml:full_power
- Toplam çözülmüş: **677**  ·  Baseline win-rate: **50.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.0%** (19 W / 6 L = 25 trade · +25.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ overlap`
   - `ml_confidence_bucket = [50,60)`
   - `hour_bucket = 04-08`

**2. Win-rate 75.8%** (25 W / 8 L = 33 trade · +25.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0881 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0826 |
| 3 | `hour_bucket=12-16` | 0.0704 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0589 |
| 5 | `dow=Wed` | 0.0568 |
| 6 | `dow=Tue` | 0.0525 |
| 7 | `session=asia` | 0.0440 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0439 |
| 9 | `dow=Mon` | 0.0425 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0396 |
| 11 | `hour_bucket=00-04` | 0.0329 |
| 12 | `session=us` | 0.0323 |
| 13 | `hour_bucket=04-08` | 0.0309 |
| 14 | `dow=Thu` | 0.0303 |
| 15 | `session=europe` | 0.0273 |

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
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.0682 |
| 2 | `session=overlap` | 0.0587 |
| 3 | `dow=Tue` | 0.0584 |
| 4 | `hour_bucket=16-20` | 0.0454 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0448 |
| 6 | `session=asia` | 0.0431 |
| 7 | `dow=Fri` | 0.0408 |
| 8 | `dow=Mon` | 0.0406 |
| 9 | `hour_bucket=08-12` | 0.0405 |
| 10 | `hour_bucket=12-16` | 0.0402 |
| 11 | `dow=Thu` | 0.0388 |
| 12 | `hour_bucket=04-08` | 0.0385 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0367 |
| 14 | `session=us` | 0.0339 |
| 15 | `session=europe` | 0.0338 |

---

## XAUUSD · ml:ultra_safe
- Toplam çözülmüş: **139**  ·  Baseline win-rate: **52.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.0%** (24 W / 6 L = 30 trade · +27.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.7%** (5 W / 17 L = 22 trade · -29.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dow ≠ Thu`
   - `session = asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0915 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0815 |
| 3 | `dow=Thu` | 0.0742 |
| 4 | `hour_bucket=20-24` | 0.0596 |
| 5 | `hour_bucket=16-20` | 0.0419 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0407 |
| 7 | `exhaustion_up=False` | 0.0344 |
| 8 | `hour_bucket=12-16` | 0.0315 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0255 |
| 10 | `session=us` | 0.0248 |
| 11 | `atr_ratio_M30=NA` | 0.0242 |
| 12 | `session=asia` | 0.0231 |
| 13 | `regime_label=transition` | 0.0224 |
| 14 | `near_resistance=False` | 0.0209 |
| 15 | `overbought=False` | 0.0204 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **4188**  ·  Baseline win-rate: **40.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +50.6pp vs baseline)
   - `dow ≠ Mon`
   - `dow = Sun`
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.6%** (5 W / 38 L = 43 trade · -29.1pp vs baseline)
   - `dow ≠ Mon`
   - `dow ≠ Sun`
   - `macd_atr_M30 = [-0.3,0)`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 23.0%** (51 W / 171 L = 222 trade · -17.7pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [60,70)`
   - `hour_bucket = 16-20`

**3. Win-rate 29.8%** (214 W / 503 L = 717 trade · -10.9pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [60,70)`
   - `hour_bucket ≠ 16-20`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1693 |
| 2 | `dow=Sun` | 0.0785 |
| 3 | `dow=Thu` | 0.0526 |
| 4 | `hour_bucket=20-24` | 0.0500 |
| 5 | `hour_bucket=16-20` | 0.0452 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0415 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0322 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0314 |
| 9 | `dow=Tue` | 0.0297 |
| 10 | `hour_bucket=00-04` | 0.0283 |
| 11 | `session=closed` | 0.0281 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0265 |
| 13 | `dow=Wed` | 0.0248 |
| 14 | `session=us` | 0.0225 |
| 15 | `dow=Fri` | 0.0206 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **2509**  ·  Baseline win-rate: **49.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.5%** (35 W / 9 L = 44 trade · +30.1pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `dow ≠ Mon`
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `dow = Sun`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 12.0%** (10 W / 73 L = 83 trade · -37.4pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow = Tue`
   - `ml_confidence_bucket = [60,70)`

**2. Win-rate 26.5%** (9 W / 25 L = 34 trade · -22.9pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `dow ≠ Mon`
   - `atr_ratio_M30 = [−∞,0.7)`
   - `adx_M30 ≠ [−∞,18)`

**3. Win-rate 28.6%** (14 W / 35 L = 49 trade · -20.8pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow = Tue`
   - `ml_confidence_bucket ≠ [60,70)`
   - `ml_confidence_bucket = [50,60)`

**4. Win-rate 31.4%** (22 W / 48 L = 70 trade · -18.0pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `dow = Mon`
   - `hour_bucket ≠ 16-20`
   - `ml_confidence_bucket = [−∞,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1017 |
| 2 | `hour_bucket=00-04` | 0.0862 |
| 3 | `dow=Tue` | 0.0809 |
| 4 | `session=asia` | 0.0576 |
| 5 | `dow=Sun` | 0.0573 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0538 |
| 7 | `dow=Thu` | 0.0419 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0383 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0374 |
| 10 | `session=overlap` | 0.0331 |
| 11 | `dow=Wed` | 0.0309 |
| 12 | `hour_bucket=16-20` | 0.0252 |
| 13 | `session=us` | 0.0242 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0239 |
| 15 | `dow=Fri` | 0.0214 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **3778**  ·  Baseline win-rate: **52.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.6%** (25 W / 2 L = 27 trade · +39.7pp vs baseline)
   - `dow ≠ Mon`
   - `rsi_M30 = [30,50)`
   - `macro_alignment ≠ weak_pro`

**2. Win-rate 76.0%** (19 W / 6 L = 25 trade · +23.1pp vs baseline)
   - `dow ≠ Mon`
   - `rsi_M30 = [30,50)`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket = [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.7%** (11 W / 51 L = 62 trade · -35.2pp vs baseline)
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 24.7%** (36 W / 110 L = 146 trade · -28.2pp vs baseline)
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1450 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0554 |
| 3 | `session=us` | 0.0553 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0531 |
| 5 | `dow=Tue` | 0.0498 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0436 |
| 7 | `hour_bucket=16-20` | 0.0380 |
| 8 | `dow=Fri` | 0.0375 |
| 9 | `session=overlap` | 0.0336 |
| 10 | `dow=Wed` | 0.0294 |
| 11 | `dow=Thu` | 0.0288 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0278 |
| 13 | `hour_bucket=04-08` | 0.0268 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0252 |
| 15 | `hour_bucket=12-16` | 0.0227 |

---

## XAUUSD · smc
- Toplam çözülmüş: **1431**  ·  Baseline win-rate: **50.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.3%** (61 W / 15 L = 76 trade · +30.3pp vs baseline)
   - `session ≠ us`
   - `session = europe`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dow ≠ Mon`

**2. Win-rate 78.4%** (40 W / 11 L = 51 trade · +28.4pp vs baseline)
   - `session ≠ us`
   - `session ≠ europe`
   - `dow ≠ Fri`
   - `hour_bucket = 12-16`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.6%** (14 W / 54 L = 68 trade · -29.4pp vs baseline)
   - `session = us`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `hour_bucket ≠ 16-20`
   - `dow = Fri`

**2. Win-rate 27.3%** (33 W / 88 L = 121 trade · -22.7pp vs baseline)
   - `session ≠ us`
   - `session = europe`
   - `ml_confidence_bucket = [80,+∞)`
   - `dow = Fri`

**3. Win-rate 31.6%** (60 W / 130 L = 190 trade · -18.4pp vs baseline)
   - `session = us`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `hour_bucket ≠ 16-20`
   - `dow ≠ Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1628 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0904 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0835 |
| 4 | `dow=Fri` | 0.0773 |
| 5 | `dow=Sun` | 0.0540 |
| 6 | `hour_bucket=20-24` | 0.0513 |
| 7 | `session=asia` | 0.0491 |
| 8 | `session=europe` | 0.0477 |
| 9 | `session=closed` | 0.0364 |
| 10 | `dow=Thu` | 0.0362 |
| 11 | `hour_bucket=04-08` | 0.0338 |
| 12 | `session=overlap` | 0.0337 |
| 13 | `dow=Wed` | 0.0270 |
| 14 | `hour_bucket=08-12` | 0.0236 |
| 15 | `dow=Mon` | 0.0233 |

---

## GDAXI.INDX · emel · BUY
- Toplam çözülmüş: **132**  ·  Baseline win-rate: **72.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.2%** (37 W / 4 L = 41 trade · +18.2pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.2150 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1354 |
| 3 | `dow=Tue` | 0.1095 |
| 4 | `session=europe` | 0.0814 |
| 5 | `hour_bucket=04-08` | 0.0784 |
| 6 | `hour_bucket=08-12` | 0.0689 |
| 7 | `session=asia` | 0.0613 |
| 8 | `hour_bucket=12-16` | 0.0530 |
| 9 | `session_phase=open_drive` | 0.0486 |
| 10 | `session=overlap` | 0.0421 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0420 |
| 12 | `dow=Mon` | 0.0369 |
| 13 | `session_phase=after_hours` | 0.0269 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **147**  ·  Baseline win-rate: **88.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (44 W / 0 L = 44 trade · +11.6pp vs baseline)
   - `session = overlap`

**2. Win-rate 94.4%** (34 W / 2 L = 36 trade · +6.0pp vs baseline)
   - `session ≠ overlap`
   - `dow = Tue`

**3. Win-rate 91.7%** (22 W / 2 L = 24 trade · +3.3pp vs baseline)
   - `session ≠ overlap`
   - `dow ≠ Tue`
   - `hour_bucket = 08-12`
   - `dow ≠ Mon`

**4. Win-rate 77.3%** (17 W / 5 L = 22 trade · -11.1pp vs baseline)
   - `session ≠ overlap`
   - `dow ≠ Tue`
   - `hour_bucket = 08-12`
   - `dow = Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1812 |
| 2 | `dow=Tue` | 0.1371 |
| 3 | `hour_bucket=12-16` | 0.1041 |
| 4 | `dow=Mon` | 0.1033 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0915 |
| 6 | `session_phase=after_hours` | 0.0584 |
| 7 | `dow=Thu` | 0.0554 |
| 8 | `session=europe` | 0.0490 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0418 |
| 10 | `session_phase=open_drive` | 0.0386 |
| 11 | `session=asia` | 0.0383 |
| 12 | `hour_bucket=08-12` | 0.0307 |
| 13 | `hour_bucket=04-08` | 0.0261 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0259 |
| 15 | `dow=Fri` | 0.0142 |

---

## GDAXI.INDX · ml:balanced · BUY
- Toplam çözülmüş: **80**  ·  Baseline win-rate: **75.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.0%** (20 W / 3 L = 23 trade · +12.0pp vs baseline)
   - `hour_bucket ≠ 08-12`
   - `session ≠ overlap`

**2. Win-rate 84.6%** (22 W / 4 L = 26 trade · +9.6pp vs baseline)
   - `hour_bucket ≠ 08-12`
   - `session = overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.2267 |
| 2 | `hour_bucket=08-12` | 0.1675 |
| 3 | `session=europe` | 0.1624 |
| 4 | `dow=Mon` | 0.1450 |
| 5 | `session=overlap` | 0.1220 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0754 |
| 7 | `dow=Fri` | 0.0417 |
| 8 | `dow=Wed` | 0.0335 |
| 9 | `dow=Thu` | 0.0139 |
| 10 | `session_phase=after_hours` | 0.0102 |

---

## GDAXI.INDX · ml:full_power · BUY
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **72.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.5%** (34 W / 4 L = 38 trade · +17.0pp vs baseline)
   - `hour_bucket = 12-16`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.2094 |
| 2 | `hour_bucket=08-12` | 0.1490 |
| 3 | `session=overlap` | 0.1280 |
| 4 | `dow=Fri` | 0.1207 |
| 5 | `session=europe` | 0.1082 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.1019 |
| 7 | `dow=Mon` | 0.0757 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0582 |
| 9 | `dow=Wed` | 0.0193 |
| 10 | `hour_bucket=04-08` | 0.0143 |
| 11 | `session=asia` | 0.0098 |

---

## GDAXI.INDX · ml:main · BUY
- Toplam çözülmüş: **126**  ·  Baseline win-rate: **77.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.4%** (42 W / 5 L = 47 trade · +12.4pp vs baseline)
   - `hour_bucket = 12-16`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +8.7pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `dow = Thu`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.1935 |
| 2 | `hour_bucket=08-12` | 0.1477 |
| 3 | `dow=Thu` | 0.1007 |
| 4 | `dow=Fri` | 0.0979 |
| 5 | `session=overlap` | 0.0882 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0848 |
| 7 | `session=europe` | 0.0692 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0634 |
| 9 | `dow=Mon` | 0.0630 |
| 10 | `session_phase=after_hours` | 0.0331 |
| 11 | `hour_bucket=04-08` | 0.0245 |
| 12 | `session=asia` | 0.0157 |
| 13 | `dow=Wed` | 0.0124 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **724**  ·  Baseline win-rate: **62.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +38.0pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session_phase = after_hours`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 89.2%** (58 W / 7 L = 65 trade · +27.2pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session_phase = after_hours`
   - `ml_confidence_bucket ≠ [70,80)`

**3. Win-rate 76.5%** (26 W / 8 L = 34 trade · +14.5pp vs baseline)
   - `dow ≠ Tue`
   - `session = overlap`
   - `dow = Fri`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.2156 |
| 2 | `dow=Mon` | 0.1566 |
| 3 | `hour_bucket=12-16` | 0.1242 |
| 4 | `hour_bucket=08-12` | 0.0982 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0581 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0508 |
| 7 | `session=europe` | 0.0466 |
| 8 | `session=overlap` | 0.0449 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0345 |
| 10 | `dow=Fri` | 0.0293 |
| 11 | `hour_bucket=04-08` | 0.0258 |
| 12 | `session=asia` | 0.0226 |
| 13 | `dow=Wed` | 0.0222 |
| 14 | `session_phase=after_hours` | 0.0172 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0169 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **709**  ·  Baseline win-rate: **53.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (22 W / 2 L = 24 trade · +38.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket ≠ 08-12`
   - `dow = Tue`
   - `session = europe`

**2. Win-rate 85.3%** (29 W / 5 L = 34 trade · +32.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket ≠ 08-12`
   - `dow = Tue`
   - `session ≠ europe`

**3. Win-rate 79.5%** (35 W / 9 L = 44 trade · +26.5pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket ≠ 08-12`
   - `dow ≠ Tue`
   - `dow = Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.8%** (4 W / 79 L = 83 trade · -48.2pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2468 |
| 2 | `dow=Thu` | 0.1455 |
| 3 | `hour_bucket=08-12` | 0.0724 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0709 |
| 5 | `dow=Tue` | 0.0649 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0608 |
| 7 | `session=europe` | 0.0585 |
| 8 | `hour_bucket=12-16` | 0.0520 |
| 9 | `dow=Mon` | 0.0346 |
| 10 | `hour_bucket=04-08` | 0.0328 |
| 11 | `session=overlap` | 0.0307 |
| 12 | `session=asia` | 0.0284 |
| 13 | `dow=Fri` | 0.0280 |
| 14 | `dow=Wed` | 0.0254 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0179 |

---

## GDAXI.INDX · pulse2 · BUY
- Toplam çözülmüş: **520**  ·  Baseline win-rate: **75.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (38 W / 0 L = 38 trade · +24.4pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session ≠ overlap`

**2. Win-rate 96.4%** (54 W / 2 L = 56 trade · +20.8pp vs baseline)
   - `dow = Tue`
   - `hour_bucket = 12-16`
   - `session = overlap`

**3. Win-rate 94.3%** (50 W / 3 L = 53 trade · +18.7pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [50,60)`
   - `session = europe`

**4. Win-rate 87.5%** (28 W / 4 L = 32 trade · +11.9pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket = 12-16`
   - `dow = Mon`

**5. Win-rate 82.8%** (24 W / 5 L = 29 trade · +7.2pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket = 12-16`
   - `dow ≠ Mon`
   - `dow = Fri`

**6. Win-rate 78.3%** (36 W / 10 L = 46 trade · +2.7pp vs baseline)
   - `dow = Tue`
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ europe`

**7. Win-rate 75.3%** (70 W / 23 L = 93 trade · -0.3pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket ≠ 12-16`
   - `dow ≠ Fri`
   - `hour_bucket ≠ 04-08`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.2103 |
| 2 | `hour_bucket=12-16` | 0.1507 |
| 3 | `dow=Fri` | 0.1298 |
| 4 | `session=asia` | 0.0706 |
| 5 | `session=overlap` | 0.0621 |
| 6 | `dow=Mon` | 0.0601 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0535 |
| 8 | `hour_bucket=04-08` | 0.0506 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0469 |
| 10 | `hour_bucket=08-12` | 0.0456 |
| 11 | `session=europe` | 0.0249 |
| 12 | `session_phase=open_drive` | 0.0235 |
| 13 | `dow=Wed` | 0.0220 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0197 |
| 15 | `session_phase=after_hours` | 0.0167 |

---

## GDAXI.INDX · pulse2 · SELL
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **65.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1696 |
| 2 | `session=europe` | 0.1613 |
| 3 | `dow=Mon` | 0.1587 |
| 4 | `hour_bucket=12-16` | 0.1015 |
| 5 | `hour_bucket=08-12` | 0.1004 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0985 |
| 7 | `session=overlap` | 0.0880 |
| 8 | `dow=Tue` | 0.0612 |
| 9 | `dow=Fri` | 0.0608 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **570**  ·  Baseline win-rate: **78.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (100 W / 0 L = 100 trade · +21.6pp vs baseline)
   - `dow = Tue`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket = 12-16`

**2. Win-rate 94.1%** (64 W / 4 L = 68 trade · +15.7pp vs baseline)
   - `dow = Tue`
   - `session ≠ asia`
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket ≠ 12-16`

**3. Win-rate 88.8%** (87 W / 11 L = 98 trade · +10.4pp vs baseline)
   - `dow ≠ Tue`
   - `hour_bucket = 12-16`
   - `ml_confidence_bucket ≠ [70,80)`
   - `dow ≠ Fri`

**4. Win-rate 78.1%** (25 W / 7 L = 32 trade · -0.3pp vs baseline)
   - `dow = Tue`
   - `session ≠ asia`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.2452 |
| 2 | `hour_bucket=12-16` | 0.1372 |
| 3 | `dow=Fri` | 0.0820 |
| 4 | `hour_bucket=08-12` | 0.0740 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0683 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0518 |
| 7 | `dow=Mon` | 0.0509 |
| 8 | `session=overlap` | 0.0443 |
| 9 | `session=asia` | 0.0375 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0372 |
| 11 | `hour_bucket=04-08` | 0.0357 |
| 12 | `session=europe` | 0.0353 |
| 13 | `dow=Thu` | 0.0310 |
| 14 | `dow=Wed` | 0.0282 |
| 15 | `ml_confidence_bucket=[80,+∞)` | 0.0154 |

---

## GDAXI.INDX · pulse3 · SELL
- Toplam çözülmüş: **679**  ·  Baseline win-rate: **63.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (43 W / 0 L = 43 trade · +36.1pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ asia`
   - `dow = Thu`
   - `session ≠ overlap`

**2. Win-rate 100.0%** (29 W / 0 L = 29 trade · +36.1pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = asia`
   - `dow = Mon`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 100.0%** (21 W / 0 L = 21 trade · +36.1pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = asia`
   - `dow = Mon`
   - `ml_confidence_bucket = [60,70)`

**4. Win-rate 100.0%** (26 W / 0 L = 26 trade · +36.1pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow ≠ Thu`
   - `hour_bucket ≠ 08-12`
   - `session = overlap`

**5. Win-rate 92.0%** (23 W / 2 L = 25 trade · +28.1pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow ≠ Thu`
   - `hour_bucket ≠ 08-12`
   - `session ≠ overlap`

**6. Win-rate 82.6%** (19 W / 4 L = 23 trade · +18.7pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session = asia`
   - `dow ≠ Mon`

**7. Win-rate 77.2%** (98 W / 29 L = 127 trade · +13.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ asia`
   - `dow ≠ Thu`
   - `hour_bucket = 12-16`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.6%** (6 W / 64 L = 70 trade · -55.3pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow = Thu`
   - `hour_bucket = 08-12`

**2. Win-rate 10.0%** (3 W / 27 L = 30 trade · -53.9pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `dow = Thu`
   - `hour_bucket ≠ 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2024 |
| 2 | `dow=Thu` | 0.1261 |
| 3 | `session=asia` | 0.0959 |
| 4 | `hour_bucket=08-12` | 0.0902 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0815 |
| 6 | `hour_bucket=04-08` | 0.0754 |
| 7 | `dow=Tue` | 0.0655 |
| 8 | `session=europe` | 0.0540 |
| 9 | `hour_bucket=12-16` | 0.0466 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0461 |
| 11 | `dow=Mon` | 0.0347 |
| 12 | `session=overlap` | 0.0222 |
| 13 | `dow=Fri` | 0.0197 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0146 |
| 15 | `session_phase=after_hours` | 0.0118 |

---

## GDAXI.INDX · smc · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **45.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.5%** (43 W / 4 L = 47 trade · +45.8pp vs baseline)
   - `dow ≠ Fri`
   - `ml_confidence_bucket ≠ [80,+∞)`

**2. Win-rate 82.1%** (23 W / 5 L = 28 trade · +36.4pp vs baseline)
   - `dow ≠ Fri`
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket = 08-12`

**3. Win-rate 75.0%** (15 W / 5 L = 20 trade · +29.3pp vs baseline)
   - `dow ≠ Fri`
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket ≠ 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.1%** (6 W / 68 L = 74 trade · -37.6pp vs baseline)
   - `dow = Fri`
   - `hour_bucket = 08-12`

**2. Win-rate 13.3%** (4 W / 26 L = 30 trade · -32.4pp vs baseline)
   - `dow = Fri`
   - `hour_bucket ≠ 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.2880 |
| 2 | `dow=Thu` | 0.2574 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.1627 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.1314 |
| 5 | `session=overlap` | 0.0892 |
| 6 | `session=europe` | 0.0295 |
| 7 | `dow=Mon` | 0.0125 |
| 8 | `hour_bucket=08-12` | 0.0116 |
| 9 | `hour_bucket=12-16` | 0.0105 |
| 10 | `session_phase=after_hours` | 0.0070 |

---

## NDX.INDX · emel · BUY
- Toplam çözülmüş: **139**  ·  Baseline win-rate: **64.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.5%** (47 W / 8 L = 55 trade · +21.5pp vs baseline)
   - `hour_bucket ≠ 16-20`
   - `session_phase = after_hours`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.2%** (8 W / 25 L = 33 trade · -39.8pp vs baseline)
   - `hour_bucket = 16-20`
   - `dow = Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.1650 |
| 2 | `session_phase=mid_session` | 0.1453 |
| 3 | `hour_bucket=12-16` | 0.1396 |
| 4 | `session_phase=after_hours` | 0.1305 |
| 5 | `hour_bucket=16-20` | 0.1186 |
| 6 | `session=us` | 0.0903 |
| 7 | `session=overlap` | 0.0811 |
| 8 | `dow=Mon` | 0.0698 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0253 |
| 10 | `session_phase=open_drive` | 0.0167 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0144 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **189**  ·  Baseline win-rate: **78.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.0%** (19 W / 1 L = 20 trade · +16.2pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket ≠ 16-20`
   - `session_phase = after_hours`

**2. Win-rate 90.0%** (18 W / 2 L = 20 trade · +11.2pp vs baseline)
   - `session ≠ overlap`
   - `dow ≠ Fri`
   - `dow = Mon`

**3. Win-rate 89.7%** (26 W / 3 L = 29 trade · +10.9pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket ≠ 16-20`
   - `session_phase ≠ after_hours`

**4. Win-rate 88.0%** (22 W / 3 L = 25 trade · +9.2pp vs baseline)
   - `session ≠ overlap`
   - `dow = Fri`

**5. Win-rate 81.8%** (27 W / 6 L = 33 trade · +3.0pp vs baseline)
   - `session = overlap`
   - `dow = Fri`

**6. Win-rate 81.0%** (17 W / 4 L = 21 trade · +2.2pp vs baseline)
   - `session = overlap`
   - `dow ≠ Fri`
   - `hour_bucket = 16-20`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1062 |
| 2 | `hour_bucket=12-16` | 0.0912 |
| 3 | `hour_bucket=16-20` | 0.0863 |
| 4 | `dow=Mon` | 0.0825 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0767 |
| 6 | `session_phase=close_drive` | 0.0630 |
| 7 | `session=overlap` | 0.0616 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0524 |
| 9 | `dow=Fri` | 0.0508 |
| 10 | `session_phase=mid_session` | 0.0397 |
| 11 | `dow=Wed` | 0.0371 |
| 12 | `session_phase=after_hours` | 0.0363 |
| 13 | `dow=Tue` | 0.0312 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0312 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0234 |

---

## NDX.INDX · ml:balanced · BUY
- Toplam çözülmüş: **99**  ·  Baseline win-rate: **76.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.6%** (22 W / 4 L = 26 trade · +7.8pp vs baseline)
   - `session = overlap`
   - `session_phase = mid_session`

**2. Win-rate 77.4%** (24 W / 7 L = 31 trade · +0.6pp vs baseline)
   - `session = overlap`
   - `session_phase ≠ mid_session`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.1238 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1148 |
| 3 | `hour_bucket=16-20` | 0.0945 |
| 4 | `dow=Thu` | 0.0911 |
| 5 | `dow=Tue` | 0.0819 |
| 6 | `hour_bucket=12-16` | 0.0816 |
| 7 | `session=us` | 0.0791 |
| 8 | `session_phase=mid_session` | 0.0785 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0748 |
| 10 | `session_phase=open_drive` | 0.0717 |
| 11 | `dow=Mon` | 0.0685 |
| 12 | `dow=Wed` | 0.0185 |
| 13 | `session_phase=after_hours` | 0.0133 |
| 14 | `session_phase=close_drive` | 0.0079 |

---

## NDX.INDX · ml:full_power · BUY
- Toplam çözülmüş: **85**  ·  Baseline win-rate: **77.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.2%** (31 W / 3 L = 34 trade · +13.6pp vs baseline)
   - `hour_bucket ≠ 16-20`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.1663 |
| 2 | `session=overlap` | 0.1459 |
| 3 | `session=us` | 0.1384 |
| 4 | `hour_bucket=16-20` | 0.1285 |
| 5 | `dow=Thu` | 0.1046 |
| 6 | `session_phase=mid_session` | 0.0755 |
| 7 | `dow=Tue` | 0.0591 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0551 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0442 |
| 10 | `dow=Mon` | 0.0307 |
| 11 | `session_phase=open_drive` | 0.0236 |
| 12 | `dow=Wed` | 0.0192 |
| 13 | `session_phase=after_hours` | 0.0088 |

---

## NDX.INDX · ml:main · BUY
- Toplam çözülmüş: **95**  ·  Baseline win-rate: **76.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.5%** (21 W / 1 L = 22 trade · +18.7pp vs baseline)
   - `dow = Wed`

**2. Win-rate 86.2%** (25 W / 4 L = 29 trade · +9.4pp vs baseline)
   - `dow ≠ Wed`
   - `hour_bucket ≠ 16-20`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1597 |
| 2 | `hour_bucket=16-20` | 0.1304 |
| 3 | `hour_bucket=12-16` | 0.1123 |
| 4 | `session=overlap` | 0.0968 |
| 5 | `dow=Thu` | 0.0968 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0882 |
| 7 | `dow=Wed` | 0.0788 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0647 |
| 9 | `session_phase=mid_session` | 0.0517 |
| 10 | `session_phase=open_drive` | 0.0458 |
| 11 | `dow=Mon` | 0.0305 |
| 12 | `dow=Tue` | 0.0253 |
| 13 | `session_phase=after_hours` | 0.0137 |
| 14 | `session_phase=close_drive` | 0.0052 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **895**  ·  Baseline win-rate: **67.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.0%** (83 W / 17 L = 100 trade · +15.6pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `session_phase ≠ close_drive`
   - `dow = Mon`
   - `session_phase ≠ mid_session`

**2. Win-rate 75.8%** (50 W / 16 L = 66 trade · +8.4pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `session_phase = close_drive`
   - `dow ≠ Mon`
   - `dow ≠ Wed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (4 W / 16 L = 20 trade · -47.4pp vs baseline)
   - `bb_extreme_upper = False`
   - `ml_confidence_bucket = [80,+∞)`
   - `regime_label ≠ ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0787 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0598 |
| 3 | `dow=Wed` | 0.0517 |
| 4 | `session_phase=close_drive` | 0.0514 |
| 5 | `dow=Tue` | 0.0472 |
| 6 | `session_phase=mid_session` | 0.0422 |
| 7 | `dow=Fri` | 0.0351 |
| 8 | `hour_bucket=12-16` | 0.0347 |
| 9 | `session_phase=open_drive` | 0.0332 |
| 10 | `session=overlap` | 0.0316 |
| 11 | `session_phase=after_hours` | 0.0313 |
| 12 | `hour_bucket=16-20` | 0.0309 |
| 13 | `dow=Thu` | 0.0280 |
| 14 | `bb_extreme_upper=False` | 0.0258 |
| 15 | `session=us` | 0.0240 |

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

**1. Win-rate 0.0%** (0 W / 54 L = 54 trade · -59.4pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session_phase = mid_session`
   - `session = us`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -34.4pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session_phase = mid_session`
   - `session ≠ us`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1936 |
| 2 | `dow=Wed` | 0.1429 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.1062 |
| 4 | `session=us` | 0.0926 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0632 |
| 6 | `session=overlap` | 0.0607 |
| 7 | `dow=Tue` | 0.0568 |
| 8 | `hour_bucket=12-16` | 0.0553 |
| 9 | `hour_bucket=16-20` | 0.0541 |
| 10 | `dow=Thu` | 0.0371 |
| 11 | `session_phase=open_drive` | 0.0360 |
| 12 | `session_phase=after_hours` | 0.0242 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0220 |
| 14 | `dow=Fri` | 0.0215 |
| 15 | `session_phase=mid_session` | 0.0191 |

---

## NDX.INDX · pulse2 · BUY
- Toplam çözülmüş: **753**  ·  Baseline win-rate: **73.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.6%** (73 W / 1 L = 74 trade · +24.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Tue`
   - `session_phase ≠ close_drive`
   - `dow = Mon`

**2. Win-rate 92.9%** (79 W / 6 L = 85 trade · +19.2pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Tue`
   - `session_phase ≠ close_drive`
   - `dow ≠ Mon`

**3. Win-rate 90.6%** (29 W / 3 L = 32 trade · +16.9pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = overlap`
   - `dow ≠ Mon`
   - `ml_confidence_bucket = [60,70)`

**4. Win-rate 89.3%** (25 W / 3 L = 28 trade · +15.6pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Tue`
   - `session_phase = close_drive`

**5. Win-rate 84.5%** (87 W / 16 L = 103 trade · +10.8pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session = overlap`
   - `dow = Mon`
   - `hour_bucket = 12-16`

**6. Win-rate 77.3%** (17 W / 5 L = 22 trade · +3.6pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.2435 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.1962 |
| 3 | `dow=Tue` | 0.0811 |
| 4 | `dow=Mon` | 0.0547 |
| 5 | `session_phase=mid_session` | 0.0440 |
| 6 | `session_phase=close_drive` | 0.0367 |
| 7 | `session=us` | 0.0282 |
| 8 | `dow=Wed` | 0.0271 |
| 9 | `session=overlap` | 0.0266 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0224 |
| 11 | `hour_bucket=12-16` | 0.0220 |
| 12 | `hour_bucket=16-20` | 0.0214 |
| 13 | `dow=Fri` | 0.0161 |
| 14 | `session_phase=after_hours` | 0.0109 |
| 15 | `dow=Thu` | 0.0101 |

---

## NDX.INDX · pulse2 · SELL
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **56.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.8%** (31 W / 6 L = 37 trade · +27.1pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket = 16-20`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.0%** (4 W / 21 L = 25 trade · -40.7pp vs baseline)
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.2088 |
| 2 | `hour_bucket=16-20` | 0.1621 |
| 3 | `dow=Thu` | 0.1572 |
| 4 | `session_phase=after_hours` | 0.0906 |
| 5 | `hour_bucket=12-16` | 0.0800 |
| 6 | `session=overlap` | 0.0649 |
| 7 | `session_phase=mid_session` | 0.0623 |
| 8 | `session=us` | 0.0570 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0539 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0499 |
| 11 | `session_phase=close_drive` | 0.0133 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **733**  ·  Baseline win-rate: **64.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.3%** (28 W / 3 L = 31 trade · +26.3pp vs baseline)
   - `dow ≠ Tue`
   - `session_phase = after_hours`
   - `dow = Fri`

**2. Win-rate 88.0%** (22 W / 3 L = 25 trade · +24.0pp vs baseline)
   - `dow = Tue`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 86.7%** (26 W / 4 L = 30 trade · +22.7pp vs baseline)
   - `dow ≠ Tue`
   - `session_phase = after_hours`
   - `dow ≠ Fri`
   - `ml_confidence_bucket ≠ [60,70)`

**4. Win-rate 78.4%** (29 W / 8 L = 37 trade · +14.4pp vs baseline)
   - `dow ≠ Tue`
   - `session_phase = after_hours`
   - `dow ≠ Fri`
   - `ml_confidence_bucket = [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (7 W / 21 L = 28 trade · -39.0pp vs baseline)
   - `dow ≠ Tue`
   - `session_phase ≠ after_hours`
   - `dow = Wed`
   - `ml_confidence_bucket = [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1152 |
| 2 | `dow=Tue` | 0.0989 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0611 |
| 4 | `dow=Fri` | 0.0549 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0466 |
| 6 | `session_phase=close_drive` | 0.0454 |
| 7 | `hour_bucket=12-16` | 0.0437 |
| 8 | `dow=Thu` | 0.0435 |
| 9 | `hour_bucket=16-20` | 0.0431 |
| 10 | `ml_confidence_bucket=[−∞,50)` | 0.0411 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0409 |
| 12 | `session_phase=mid_session` | 0.0371 |
| 13 | `session=us` | 0.0366 |
| 14 | `session=overlap` | 0.0357 |
| 15 | `session_phase=open_drive` | 0.0280 |

---

## NDX.INDX · pulse3 · SELL
- Toplam çözülmüş: **439**  ·  Baseline win-rate: **65.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.6%** (73 W / 1 L = 74 trade · +32.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase = mid_session`
   - `dow = Mon`

**2. Win-rate 97.1%** (33 W / 1 L = 34 trade · +31.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase = mid_session`
   - `dow ≠ Mon`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 88.4%** (61 W / 8 L = 69 trade · +22.6pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase ≠ mid_session`
   - `dow ≠ Fri`
   - `ml_confidence_bucket ≠ [70,80)`

**4. Win-rate 85.7%** (48 W / 8 L = 56 trade · +19.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase = mid_session`
   - `dow ≠ Mon`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 85.0%** (17 W / 3 L = 20 trade · +19.2pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase ≠ mid_session`
   - `dow = Fri`
   - `session_phase = open_drive`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.3%** (7 W / 68 L = 75 trade · -56.5pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `session ≠ overlap`

**2. Win-rate 12.5%** (3 W / 21 L = 24 trade · -53.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session_phase ≠ mid_session`
   - `dow = Fri`
   - `session_phase ≠ open_drive`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.2294 |
| 2 | `dow=Wed` | 0.1436 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.1157 |
| 4 | `dow=Mon` | 0.1075 |
| 5 | `session_phase=after_hours` | 0.0522 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0477 |
| 7 | `session_phase=mid_session` | 0.0456 |
| 8 | `hour_bucket=12-16` | 0.0385 |
| 9 | `session=overlap` | 0.0341 |
| 10 | `dow=Fri` | 0.0320 |
| 11 | `session=us` | 0.0290 |
| 12 | `session_phase=open_drive` | 0.0257 |
| 13 | `hour_bucket=16-20` | 0.0238 |
| 14 | `dow=Tue` | 0.0231 |
| 15 | `ml_confidence_bucket=[70,80)` | 0.0227 |

---

## USOIL.FOREX · emel · BUY
- Toplam çözülmüş: **973**  ·  Baseline win-rate: **66.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +21.5pp vs baseline)
   - `session ≠ closed`
   - `dow ≠ Fri`
   - `session_phase = late_pit`
   - `dow = Wed`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1010 |
| 2 | `dow=Tue` | 0.0995 |
| 3 | `dow=Mon` | 0.0802 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0751 |
| 5 | `dow=Fri` | 0.0627 |
| 6 | `dow=Wed` | 0.0582 |
| 7 | `session=europe` | 0.0502 |
| 8 | `session=closed` | 0.0433 |
| 9 | `hour_bucket=04-08` | 0.0421 |
| 10 | `hour_bucket=00-04` | 0.0417 |
| 11 | `session_phase=early_pit` | 0.0416 |
| 12 | `dow=Thu` | 0.0399 |
| 13 | `hour_bucket=20-24` | 0.0391 |
| 14 | `hour_bucket=12-16` | 0.0382 |
| 15 | `session=asia` | 0.0322 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **465**  ·  Baseline win-rate: **73.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.3%** (25 W / 3 L = 28 trade · +16.2pp vs baseline)
   - `dow ≠ Fri`
   - `session ≠ us`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 83.3%** (60 W / 12 L = 72 trade · +10.2pp vs baseline)
   - `dow ≠ Fri`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session_phase ≠ off_hours`

**3. Win-rate 75.4%** (187 W / 61 L = 248 trade · +2.3pp vs baseline)
   - `dow ≠ Fri`
   - `session ≠ us`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session_phase = off_hours`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.1189 |
| 2 | `dow=Thu` | 0.0643 |
| 3 | `session=overlap` | 0.0636 |
| 4 | `dow=Wed` | 0.0592 |
| 5 | `session=us` | 0.0581 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0571 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0559 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0514 |
| 9 | `dow=Tue` | 0.0446 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0426 |
| 11 | `hour_bucket=12-16` | 0.0418 |
| 12 | `session_phase=late_pit` | 0.0356 |
| 13 | `dow=Mon` | 0.0346 |
| 14 | `session=asia` | 0.0294 |
| 15 | `hour_bucket=20-24` | 0.0275 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **263**  ·  Baseline win-rate: **75.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (33 W / 0 L = 33 trade · +24.7pp vs baseline)
   - `bb_extreme_lower = False`

**2. Win-rate 90.6%** (29 W / 3 L = 32 trade · +15.3pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `dow = Tue`

**3. Win-rate 87.0%** (20 W / 3 L = 23 trade · +11.7pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `dow ≠ Tue`
   - `hour_bucket = 16-20`
   - `ml_confidence_bucket = [−∞,50)`

**4. Win-rate 75.0%** (36 W / 12 L = 48 trade · -0.3pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `dow ≠ Tue`
   - `hour_bucket ≠ 16-20`
   - `ml_confidence_bucket = [50,60)`

**5. Win-rate 75.0%** (15 W / 5 L = 20 trade · -0.3pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `dow ≠ Tue`
   - `hour_bucket = 16-20`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.0592 |
| 2 | `dow=Fri` | 0.0377 |
| 3 | `dow=Mon` | 0.0373 |
| 4 | `bb_extreme_lower=False` | 0.0326 |
| 5 | `exhaustion_up=NA` | 0.0312 |
| 6 | `near_support=NA` | 0.0269 |
| 7 | `dow=Wed` | 0.0248 |
| 8 | `session=us` | 0.0232 |
| 9 | `consec_red_M30=[0,2)` | 0.0227 |
| 10 | `ml_confidence_bucket=[−∞,50)` | 0.0215 |
| 11 | `rsi_H1=NA` | 0.0204 |
| 12 | `adx_H4=NA` | 0.0203 |
| 13 | `session=asia` | 0.0196 |
| 14 | `near_resistance=NA` | 0.0191 |
| 15 | `us10y_chg1d=NA` | 0.0177 |

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

**3. Win-rate 82.6%** (19 W / 4 L = 23 trade · +0.9pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `hour_bucket = 08-12`

**4. Win-rate 81.0%** (17 W / 4 L = 21 trade · -0.7pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ us`
   - `hour_bucket ≠ 08-12`
   - `hour_bucket = 12-16`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.1299 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1162 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0969 |
| 4 | `session_phase=off_hours` | 0.0631 |
| 5 | `session=us` | 0.0630 |
| 6 | `session=europe` | 0.0595 |
| 7 | `dow=Tue` | 0.0594 |
| 8 | `session=asia` | 0.0580 |
| 9 | `dow=Mon` | 0.0523 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0443 |
| 11 | `hour_bucket=08-12` | 0.0439 |
| 12 | `session=overlap` | 0.0415 |
| 13 | `hour_bucket=16-20` | 0.0315 |
| 14 | `hour_bucket=20-24` | 0.0310 |
| 15 | `session_phase=late_pit` | 0.0297 |

---

## USOIL.FOREX · ml:balanced · BUY
- Toplam çözülmüş: **549**  ·  Baseline win-rate: **75.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.1%** (32 W / 2 L = 34 trade · +19.1pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 90.6%** (29 W / 3 L = 32 trade · +15.6pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 20-24`
   - `dow = Mon`

**3. Win-rate 89.7%** (26 W / 3 L = 29 trade · +14.7pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket ≠ 20-24`
   - `hour_bucket = 12-16`
   - `dow = Mon`

**4. Win-rate 82.1%** (23 W / 5 L = 28 trade · +7.1pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket ≠ 20-24`
   - `hour_bucket ≠ 12-16`
   - `dow = Thu`

**5. Win-rate 79.2%** (19 W / 5 L = 24 trade · +4.2pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 20-24`
   - `dow ≠ Mon`
   - `session ≠ us`

**6. Win-rate 77.8%** (49 W / 14 L = 63 trade · +2.8pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket ≠ 20-24`
   - `hour_bucket = 12-16`
   - `dow ≠ Mon`

**7. Win-rate 75.0%** (15 W / 5 L = 20 trade · +0.0pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 20-24`
   - `dow ≠ Mon`
   - `session = us`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.0829 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0819 |
| 3 | `dow=Thu` | 0.0679 |
| 4 | `dow=Tue` | 0.0655 |
| 5 | `dow=Mon` | 0.0645 |
| 6 | `hour_bucket=20-24` | 0.0592 |
| 7 | `hour_bucket=12-16` | 0.0591 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0520 |
| 9 | `dow=Wed` | 0.0454 |
| 10 | `hour_bucket=08-12` | 0.0440 |
| 11 | `session=asia` | 0.0405 |
| 12 | `session_phase=off_hours` | 0.0386 |
| 13 | `hour_bucket=00-04` | 0.0373 |
| 14 | `hour_bucket=04-08` | 0.0316 |
| 15 | `session=europe` | 0.0300 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **512**  ·  Baseline win-rate: **68.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (29 W / 0 L = 29 trade · +32.0pp vs baseline)
   - `overbought = False`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0480 |
| 2 | `hour_bucket=00-04` | 0.0439 |
| 3 | `session=asia` | 0.0378 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0375 |
| 5 | `near_resistance=False` | 0.0361 |
| 6 | `dow=Wed` | 0.0312 |
| 7 | `overbought=False` | 0.0304 |
| 8 | `dow=Tue` | 0.0293 |
| 9 | `regime_label=transition` | 0.0292 |
| 10 | `session_phase=early_pit` | 0.0274 |
| 11 | `rsi_extreme=False` | 0.0271 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0246 |
| 13 | `exhaustion_down=False` | 0.0242 |
| 14 | `bb_extreme_lower=False` | 0.0242 |
| 15 | `M30_ema_stack=mixed` | 0.0237 |

---

## USOIL.FOREX · ml:full_power · BUY
- Toplam çözülmüş: **563**  ·  Baseline win-rate: **75.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.1%** (32 W / 2 L = 34 trade · +19.0pp vs baseline)
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 90.6%** (29 W / 3 L = 32 trade · +15.5pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 20-24`
   - `dow = Mon`

**3. Win-rate 89.3%** (25 W / 3 L = 28 trade · +14.2pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket ≠ 20-24`
   - `hour_bucket = 12-16`
   - `ml_confidence_bucket = [50,60)`

**4. Win-rate 81.5%** (22 W / 5 L = 27 trade · +6.4pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 20-24`
   - `dow ≠ Mon`
   - `dow ≠ Tue`

**5. Win-rate 77.3%** (51 W / 15 L = 66 trade · +2.2pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket ≠ 20-24`
   - `hour_bucket = 12-16`
   - `ml_confidence_bucket ≠ [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0949 |
| 2 | `dow=Thu` | 0.0739 |
| 3 | `dow=Mon` | 0.0728 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0704 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0623 |
| 6 | `dow=Tue` | 0.0598 |
| 7 | `hour_bucket=12-16` | 0.0547 |
| 8 | `hour_bucket=20-24` | 0.0546 |
| 9 | `dow=Wed` | 0.0505 |
| 10 | `hour_bucket=08-12` | 0.0473 |
| 11 | `session_phase=off_hours` | 0.0384 |
| 12 | `session=europe` | 0.0376 |
| 13 | `session_phase=active_pit` | 0.0319 |
| 14 | `session_phase=late_pit` | 0.0288 |
| 15 | `hour_bucket=04-08` | 0.0280 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **533**  ·  Baseline win-rate: **68.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.0%** (40 W / 6 L = 46 trade · +18.7pp vs baseline)
   - `regime_label = NA`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session ≠ asia`
   - `dow = Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -33.3pp vs baseline)
   - `regime_label = NA`
   - `ml_confidence_bucket = [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.0456 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0373 |
| 3 | `hour_bucket=16-20` | 0.0349 |
| 4 | `ml_confidence_bucket=[50,60)` | 0.0345 |
| 5 | `session=us` | 0.0344 |
| 6 | `hour_bucket=00-04` | 0.0344 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0314 |
| 8 | `dow=Tue` | 0.0313 |
| 9 | `dow=Mon` | 0.0295 |
| 10 | `dow=Wed` | 0.0272 |
| 11 | `session_phase=active_pit` | 0.0267 |
| 12 | `near_resistance=False` | 0.0246 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0234 |
| 14 | `session_phase=off_hours` | 0.0227 |
| 15 | `hour_bucket=20-24` | 0.0196 |

---

## USOIL.FOREX · ml:main · BUY
- Toplam çözülmüş: **645**  ·  Baseline win-rate: **74.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.5%** (29 W / 2 L = 31 trade · +18.9pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `dow ≠ Tue`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 90.0%** (36 W / 4 L = 40 trade · +15.4pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket = 12-16`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 87.0%** (20 W / 3 L = 23 trade · +12.4pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket = 12-16`
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ overlap`

**4. Win-rate 76.5%** (39 W / 12 L = 51 trade · +1.9pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `dow = Tue`
   - `hour_bucket = 08-12`

**5. Win-rate 75.0%** (222 W / 74 L = 296 trade · +0.4pp vs baseline)
   - `dow ≠ Fri`
   - `hour_bucket ≠ 12-16`
   - `dow ≠ Tue`
   - `ml_confidence_bucket ≠ [70,80)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0862 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.0799 |
| 3 | `dow=Mon` | 0.0729 |
| 4 | `dow=Tue` | 0.0683 |
| 5 | `dow=Fri` | 0.0639 |
| 6 | `hour_bucket=12-16` | 0.0548 |
| 7 | `dow=Wed` | 0.0541 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0537 |
| 9 | `ml_confidence_bucket=[70,80)` | 0.0514 |
| 10 | `hour_bucket=08-12` | 0.0459 |
| 11 | `hour_bucket=20-24` | 0.0321 |
| 12 | `session=europe` | 0.0306 |
| 13 | `session=asia` | 0.0302 |
| 14 | `session_phase=off_hours` | 0.0295 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0288 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **580**  ·  Baseline win-rate: **69.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (29 W / 0 L = 29 trade · +31.0pp vs baseline)
   - `overbought = False`

**2. Win-rate 85.5%** (59 W / 10 L = 69 trade · +16.5pp vs baseline)
   - `overbought ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`
   - `ml_confidence_bucket ≠ [60,70)`

**3. Win-rate 76.9%** (20 W / 6 L = 26 trade · +7.9pp vs baseline)
   - `overbought ≠ False`
   - `ml_confidence_bucket ≠ [70,80)`
   - `session = us`
   - `ml_confidence_bucket = [60,70)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.0503 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.0399 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0373 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0362 |
| 5 | `dow=Tue` | 0.0346 |
| 6 | `hour_bucket=16-20` | 0.0336 |
| 7 | `dow=Wed` | 0.0327 |
| 8 | `session=asia` | 0.0316 |
| 9 | `hour_bucket=00-04` | 0.0276 |
| 10 | `dow=Mon` | 0.0252 |
| 11 | `dow=Thu` | 0.0248 |
| 12 | `session_phase=off_hours` | 0.0235 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0222 |
| 14 | `session_phase=late_pit` | 0.0216 |
| 15 | `session_phase=active_pit` | 0.0197 |

---

## USOIL.FOREX · ml:ultra_safe · BUY
- Toplam çözülmüş: **98**  ·  Baseline win-rate: **88.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (29 W / 1 L = 30 trade · +7.9pp vs baseline)
   - `dow = Thu`

**2. Win-rate 92.9%** (26 W / 2 L = 28 trade · +4.1pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Mon`

**3. Win-rate 80.0%** (16 W / 4 L = 20 trade · -8.8pp vs baseline)
   - `dow ≠ Thu`
   - `dow ≠ Mon`
   - `session_phase ≠ off_hours`

**4. Win-rate 80.0%** (16 W / 4 L = 20 trade · -8.8pp vs baseline)
   - `dow ≠ Thu`
   - `dow ≠ Mon`
   - `session_phase = off_hours`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.1406 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.1295 |
| 3 | `session_phase=off_hours` | 0.0846 |
| 4 | `session=europe` | 0.0743 |
| 5 | `dow=Tue` | 0.0736 |
| 6 | `session=us` | 0.0718 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0604 |
| 8 | `session=asia` | 0.0577 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0543 |
| 10 | `hour_bucket=16-20` | 0.0534 |
| 11 | `dow=Mon` | 0.0439 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0347 |
| 13 | `session_phase=late_pit` | 0.0343 |
| 14 | `hour_bucket=08-12` | 0.0254 |
| 15 | `hour_bucket=12-16` | 0.0242 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **3724**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (78 W / 0 L = 78 trade · +27.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `dxy_chg1d ≠ [0,0.5)`

**2. Win-rate 100.0%** (25 W / 0 L = 25 trade · +27.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 = [0.7,1)`
   - `M30_adx_label ≠ ranging`

**3. Win-rate 96.8%** (30 W / 1 L = 31 trade · +24.0pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `dxy_chg1d = [0,0.5)`

**4. Win-rate 82.9%** (321 W / 66 L = 387 trade · +10.1pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `dow ≠ Sun`
   - `hour_bucket = 20-24`
   - `ml_confidence_bucket ≠ [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0575 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0474 |
| 3 | `dow=Mon` | 0.0468 |
| 4 | `dow=Tue` | 0.0433 |
| 5 | `dow=Wed` | 0.0414 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0332 |
| 7 | `hour_bucket=20-24` | 0.0310 |
| 8 | `dow=Thu` | 0.0304 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0297 |
| 10 | `hour_bucket=16-20` | 0.0272 |
| 11 | `session_phase=late_pit` | 0.0263 |
| 12 | `dow=Sun` | 0.0224 |
| 13 | `session=us` | 0.0219 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0196 |
| 15 | `session_phase=off_hours` | 0.0190 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **3007**  ·  Baseline win-rate: **72.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (68 W / 0 L = 68 trade · +27.1pp vs baseline)
   - `adx_H4 ≠ NA`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `bb_extreme_lower ≠ True`

**2. Win-rate 100.0%** (36 W / 0 L = 36 trade · +27.1pp vs baseline)
   - `adx_H4 ≠ NA`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `bb_extreme_lower = True`

**3. Win-rate 100.0%** (27 W / 0 L = 27 trade · +27.1pp vs baseline)
   - `adx_H4 ≠ NA`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 = [0,2)`

**4. Win-rate 91.7%** (22 W / 2 L = 24 trade · +18.8pp vs baseline)
   - `adx_H4 ≠ NA`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `consec_red_M30 ≠ [0,2)`

**5. Win-rate 89.5%** (34 W / 4 L = 38 trade · +16.6pp vs baseline)
   - `adx_H4 = NA`
   - `dow ≠ Wed`
   - `dow = Fri`
   - `hour_bucket = 08-12`

**6. Win-rate 79.3%** (46 W / 12 L = 58 trade · +6.4pp vs baseline)
   - `adx_H4 = NA`
   - `dow = Wed`
   - `session = closed`

**7. Win-rate 75.2%** (1564 W / 516 L = 2080 trade · +2.3pp vs baseline)
   - `adx_H4 = NA`
   - `dow ≠ Wed`
   - `dow ≠ Fri`
   - `ml_confidence_bucket ≠ [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.0%** (8 W / 17 L = 25 trade · -40.9pp vs baseline)
   - `adx_H4 = NA`
   - `dow = Wed`
   - `session ≠ closed`
   - `session_phase = late_pit`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0863 |
| 2 | `dow=Wed` | 0.0623 |
| 3 | `dow=Tue` | 0.0493 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0412 |
| 5 | `dow=Fri` | 0.0401 |
| 6 | `session=closed` | 0.0316 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0286 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0255 |
| 9 | `hour_bucket=20-24` | 0.0245 |
| 10 | `dow=Thu` | 0.0245 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0233 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0219 |
| 13 | `hour_bucket=00-04` | 0.0189 |
| 14 | `hour_bucket=16-20` | 0.0187 |
| 15 | `dist_high_M30=NA` | 0.0183 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **2741**  ·  Baseline win-rate: **72.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.6%** (137 W / 11 L = 148 trade · +19.7pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow = Tue`
   - `session_phase = off_hours`

**2. Win-rate 80.3%** (192 W / 47 L = 239 trade · +7.4pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow ≠ Tue`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 75.8%** (687 W / 219 L = 906 trade · +2.9pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket = [50,60)`
   - `dow ≠ Thu`
   - `session ≠ us`

**4. Win-rate 75.0%** (439 W / 146 L = 585 trade · +2.1pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dow ≠ Tue`
   - `ml_confidence_bucket ≠ [−∞,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 19.2%** (5 W / 21 L = 26 trade · -53.7pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow = Mon`
   - `ml_confidence_bucket = [60,70)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=00-04` | 0.1271 |
| 2 | `ml_confidence_bucket=[50,60)` | 0.0813 |
| 3 | `dow=Tue` | 0.0651 |
| 4 | `dow=Thu` | 0.0648 |
| 5 | `dow=Mon` | 0.0627 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0605 |
| 7 | `hour_bucket=04-08` | 0.0574 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0463 |
| 9 | `hour_bucket=12-16` | 0.0397 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0394 |
| 11 | `session=europe` | 0.0362 |
| 12 | `session=asia` | 0.0355 |
| 13 | `dow=Wed` | 0.0258 |
| 14 | `hour_bucket=08-12` | 0.0234 |
| 15 | `dow=Fri` | 0.0202 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **2238**  ·  Baseline win-rate: **72.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.7%** (172 W / 4 L = 176 trade · +25.0pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket = 20-24`
   - `dow = Mon`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 97.0%** (65 W / 2 L = 67 trade · +24.3pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket ≠ 20-24`
   - `rsi_extreme = False`
   - `consec_red_M30 ≠ [2,4)`

**3. Win-rate 87.5%** (21 W / 3 L = 24 trade · +14.8pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket ≠ 20-24`
   - `rsi_extreme = False`
   - `consec_red_M30 = [2,4)`

**4. Win-rate 86.7%** (26 W / 4 L = 30 trade · +14.0pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket = 20-24`
   - `dow = Mon`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 81.0%** (141 W / 33 L = 174 trade · +8.3pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket = 20-24`
   - `dow ≠ Mon`
   - `dow ≠ Tue`

**6. Win-rate 79.4%** (382 W / 99 L = 481 trade · +6.7pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket ≠ 20-24`
   - `rsi_extreme ≠ False`
   - `dow = Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.7%** (13 W / 47 L = 60 trade · -51.0pp vs baseline)
   - `dow = Sun`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Sun` | 0.1000 |
| 2 | `dow=Tue` | 0.0732 |
| 3 | `dow=Mon` | 0.0699 |
| 4 | `session=us` | 0.0575 |
| 5 | `dow=Wed` | 0.0476 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0416 |
| 7 | `hour_bucket=20-24` | 0.0391 |
| 8 | `session=overlap` | 0.0386 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0352 |
| 10 | `dow=Thu` | 0.0343 |
| 11 | `hour_bucket=12-16` | 0.0321 |
| 12 | `session_phase=late_pit` | 0.0305 |
| 13 | `session=closed` | 0.0283 |
| 14 | `session=asia` | 0.0254 |
| 15 | `session_phase=off_hours` | 0.0252 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **3389**  ·  Baseline win-rate: **74.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (34 W / 0 L = 34 trade · +26.0pp vs baseline)
   - `sar_bearish = True`

**2. Win-rate 78.2%** (692 W / 193 L = 885 trade · +4.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `dow ≠ Sun`
   - `hour_bucket ≠ 16-20`
   - `dow = Mon`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0773 |
| 2 | `dow=Wed` | 0.0754 |
| 3 | `dow=Tue` | 0.0608 |
| 4 | `dow=Thu` | 0.0603 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0592 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0497 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0449 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0394 |
| 9 | `hour_bucket=00-04` | 0.0376 |
| 10 | `hour_bucket=12-16` | 0.0318 |
| 11 | `dow=Sun` | 0.0282 |
| 12 | `dow=Fri` | 0.0266 |
| 13 | `session=us` | 0.0233 |
| 14 | `session=europe` | 0.0232 |
| 15 | `hour_bucket=04-08` | 0.0225 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **2711**  ·  Baseline win-rate: **73.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (152 W / 0 L = 152 trade · +26.1pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`
   - `ml_confidence_bucket ≠ [50,60)`

**2. Win-rate 96.3%** (26 W / 1 L = 27 trade · +22.4pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`
   - `ml_confidence_bucket = [50,60)`

**3. Win-rate 95.7%** (22 W / 1 L = 23 trade · +21.8pp vs baseline)
   - `dist_high_M30 = [1.5,+∞)`
   - `macd_atr_M30 = [−∞,-0.3)`

**4. Win-rate 86.2%** (144 W / 23 L = 167 trade · +12.3pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session ≠ overlap`
   - `dow ≠ Tue`
   - `session = closed`

**5. Win-rate 83.1%** (530 W / 108 L = 638 trade · +9.2pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session ≠ overlap`
   - `dow = Tue`
   - `session_phase = off_hours`

**6. Win-rate 75.0%** (18 W / 6 L = 24 trade · +1.1pp vs baseline)
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `session = overlap`
   - `dow = Tue`
   - `ml_confidence_bucket = [60,70)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.0801 |
| 2 | `dow=Mon` | 0.0455 |
| 3 | `session_phase=off_hours` | 0.0380 |
| 4 | `dow=Wed` | 0.0371 |
| 5 | `session=closed` | 0.0332 |
| 6 | `session_phase=early_pit` | 0.0294 |
| 7 | `session=overlap` | 0.0287 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0271 |
| 9 | `hour_bucket=20-24` | 0.0259 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0253 |
| 11 | `hour_bucket=12-16` | 0.0248 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0219 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0218 |
| 14 | `rsi_extreme=NA` | 0.0210 |
| 15 | `H1_ema_stack=NA` | 0.0210 |

---

## USOIL.FOREX · smc · BUY
- Toplam çözülmüş: **1600**  ·  Baseline win-rate: **85.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +14.2pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session = closed`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 100.0%** (44 W / 0 L = 44 trade · +14.2pp vs baseline)
   - `dow = Thu`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket ≠ 08-12`
   - `session_phase ≠ off_hours`

**3. Win-rate 98.8%** (79 W / 1 L = 80 trade · +13.0pp vs baseline)
   - `dow ≠ Thu`
   - `dow ≠ Wed`
   - `dow = Fri`
   - `hour_bucket = 20-24`

**4. Win-rate 96.6%** (28 W / 1 L = 29 trade · +10.8pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session ≠ closed`
   - `hour_bucket = 16-20`

**5. Win-rate 95.3%** (285 W / 14 L = 299 trade · +9.5pp vs baseline)
   - `dow = Thu`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket ≠ 08-12`
   - `session_phase = off_hours`

**6. Win-rate 93.3%** (98 W / 7 L = 105 trade · +7.5pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session = closed`
   - `ml_confidence_bucket ≠ [70,80)`

**7. Win-rate 90.6%** (48 W / 5 L = 53 trade · +4.8pp vs baseline)
   - `dow = Thu`
   - `hour_bucket = 04-08`
   - `ml_confidence_bucket ≠ [80,+∞)`

**8. Win-rate 90.3%** (130 W / 14 L = 144 trade · +4.5pp vs baseline)
   - `dow = Thu`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket = 08-12`

**9. Win-rate 86.3%** (88 W / 14 L = 102 trade · +0.5pp vs baseline)
   - `dow = Thu`
   - `hour_bucket = 04-08`
   - `ml_confidence_bucket = [80,+∞)`

**10. Win-rate 83.9%** (115 W / 22 L = 137 trade · -1.9pp vs baseline)
   - `dow ≠ Thu`
   - `dow = Wed`
   - `session ≠ closed`
   - `hour_bucket ≠ 16-20`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.1730 |
| 2 | `dow=Fri` | 0.1157 |
| 3 | `dow=Sun` | 0.0952 |
| 4 | `hour_bucket=08-12` | 0.0675 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0661 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0648 |
| 7 | `hour_bucket=12-16` | 0.0536 |
| 8 | `dow=Mon` | 0.0515 |
| 9 | `dow=Wed` | 0.0505 |
| 10 | `session=europe` | 0.0382 |
| 11 | `hour_bucket=20-24` | 0.0367 |
| 12 | `hour_bucket=00-04` | 0.0318 |
| 13 | `session_phase=late_pit` | 0.0291 |
| 14 | `hour_bucket=04-08` | 0.0260 |
| 15 | `session=us` | 0.0247 |

---

## USOIL.FOREX · smc · SELL
- Toplam çözülmüş: **871**  ·  Baseline win-rate: **85.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (33 W / 0 L = 33 trade · +14.8pp vs baseline)
   - `dow ≠ Thu`
   - `atr_ratio_M30 ≠ NA`

**2. Win-rate 100.0%** (87 W / 0 L = 87 trade · +14.8pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket ≠ 04-08`
   - `session = europe`

**3. Win-rate 97.4%** (147 W / 4 L = 151 trade · +12.2pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket ≠ 04-08`
   - `session ≠ europe`

**4. Win-rate 90.6%** (77 W / 8 L = 85 trade · +5.4pp vs baseline)
   - `dow = Thu`
   - `session ≠ closed`
   - `hour_bucket = 04-08`

**5. Win-rate 90.0%** (45 W / 5 L = 50 trade · +4.8pp vs baseline)
   - `dow ≠ Thu`
   - `atr_ratio_M30 = NA`
   - `dow ≠ Tue`
   - `session_phase ≠ off_hours`

**6. Win-rate 79.3%** (279 W / 73 L = 352 trade · -5.9pp vs baseline)
   - `dow ≠ Thu`
   - `atr_ratio_M30 = NA`
   - `dow ≠ Tue`
   - `session_phase = off_hours`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.1452 |
| 2 | `dow=Tue` | 0.0750 |
| 3 | `session=closed` | 0.0646 |
| 4 | `dow=Fri` | 0.0595 |
| 5 | `session=us` | 0.0584 |
| 6 | `session_phase=late_pit` | 0.0560 |
| 7 | `session_phase=off_hours` | 0.0559 |
| 8 | `session=europe` | 0.0416 |
| 9 | `hour_bucket=20-24` | 0.0355 |
| 10 | `session=asia` | 0.0347 |
| 11 | `hour_bucket=08-12` | 0.0332 |
| 12 | `hour_bucket=00-04` | 0.0315 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0307 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0307 |
| 15 | `hour_bucket=04-08` | 0.0200 |

---

## XAUUSD · emel · BUY
- Toplam çözülmüş: **341**  ·  Baseline win-rate: **38.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.3%** (18 W / 5 L = 23 trade · +39.6pp vs baseline)
   - `dow ≠ Mon`
   - `hour_bucket ≠ 00-04`
   - `dow ≠ Tue`
   - `ml_confidence_bucket = [−∞,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.2%** (3 W / 45 L = 48 trade · -32.5pp vs baseline)
   - `dow = Mon`
   - `session ≠ europe`
   - `session = us`

**2. Win-rate 19.6%** (11 W / 45 L = 56 trade · -19.1pp vs baseline)
   - `dow = Mon`
   - `session ≠ europe`
   - `session ≠ us`
   - `hour_bucket = 20-24`

**3. Win-rate 28.6%** (10 W / 25 L = 35 trade · -10.1pp vs baseline)
   - `dow = Mon`
   - `session ≠ europe`
   - `session ≠ us`
   - `hour_bucket ≠ 20-24`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.2182 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.0921 |
| 3 | `hour_bucket=00-04` | 0.0684 |
| 4 | `hour_bucket=16-20` | 0.0673 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0647 |
| 6 | `session=europe` | 0.0624 |
| 7 | `session=closed` | 0.0590 |
| 8 | `session=us` | 0.0482 |
| 9 | `hour_bucket=08-12` | 0.0447 |
| 10 | `dow=Wed` | 0.0420 |
| 11 | `hour_bucket=20-24` | 0.0344 |
| 12 | `hour_bucket=12-16` | 0.0341 |
| 13 | `dow=Thu` | 0.0320 |
| 14 | `dow=Tue` | 0.0320 |
| 15 | `session=asia` | 0.0240 |

---

## XAUUSD · emel · SELL
- Toplam çözülmüş: **103**  ·  Baseline win-rate: **41.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -31.7pp vs baseline)
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=08-12` | 0.1684 |
| 2 | `session=europe` | 0.1355 |
| 3 | `dow=Fri` | 0.1254 |
| 4 | `hour_bucket=00-04` | 0.0879 |
| 5 | `session=us` | 0.0760 |
| 6 | `dow=Tue` | 0.0744 |
| 7 | `session=asia` | 0.0707 |
| 8 | `hour_bucket=04-08` | 0.0612 |
| 9 | `dow=Thu` | 0.0594 |
| 10 | `hour_bucket=20-24` | 0.0546 |
| 11 | `dow=Mon` | 0.0537 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0129 |
| 13 | `hour_bucket=12-16` | 0.0071 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0065 |
| 15 | `session=overlap` | 0.0061 |

---

## XAUUSD · meta · BUY
- Toplam çözülmüş: **240**  ·  Baseline win-rate: **61.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.9%** (22 W / 7 L = 29 trade · +14.6pp vs baseline)
   - `dow = Tue`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.1327 |
| 2 | `hour_bucket=16-20` | 0.0737 |
| 3 | `hour_bucket=20-24` | 0.0727 |
| 4 | `session=asia` | 0.0695 |
| 5 | `hour_bucket=04-08` | 0.0654 |
| 6 | `session=us` | 0.0603 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0527 |
| 8 | `hour_bucket=00-04` | 0.0507 |
| 9 | `dow=Fri` | 0.0503 |
| 10 | `dow=Mon` | 0.0440 |
| 11 | `dow=Wed` | 0.0435 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0427 |
| 13 | `dow=Thu` | 0.0422 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0417 |
| 15 | `session=europe` | 0.0333 |

---

## XAUUSD · meta · SELL
- Toplam çözülmüş: **379**  ·  Baseline win-rate: **66.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +34.0pp vs baseline)
   - `dow = Tue`
   - `session = overlap`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +19.7pp vs baseline)
   - `dow = Tue`
   - `session ≠ overlap`
   - `hour_bucket = 04-08`

**3. Win-rate 81.8%** (18 W / 4 L = 22 trade · +15.8pp vs baseline)
   - `dow = Tue`
   - `session ≠ overlap`
   - `hour_bucket ≠ 04-08`
   - `hour_bucket = 08-12`

**4. Win-rate 80.6%** (29 W / 7 L = 36 trade · +14.6pp vs baseline)
   - `dow ≠ Tue`
   - `dow ≠ Wed`
   - `dow ≠ Thu`
   - `ml_confidence_bucket = [50,60)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.1649 |
| 2 | `dow=Wed` | 0.1151 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0778 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0693 |
| 5 | `session=us` | 0.0634 |
| 6 | `session=overlap` | 0.0604 |
| 7 | `dow=Thu` | 0.0589 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0408 |
| 9 | `hour_bucket=16-20` | 0.0397 |
| 10 | `hour_bucket=04-08` | 0.0382 |
| 11 | `dow=Fri` | 0.0367 |
| 12 | `hour_bucket=12-16` | 0.0354 |
| 13 | `hour_bucket=00-04` | 0.0320 |
| 14 | `session=asia` | 0.0275 |
| 15 | `session=closed` | 0.0251 |

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
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1738 |
| 2 | `dow=Tue` | 0.1081 |
| 3 | `dow=Thu` | 0.0862 |
| 4 | `session=overlap` | 0.0861 |
| 5 | `session=us` | 0.0847 |
| 6 | `dow=Mon` | 0.0706 |
| 7 | `session=asia` | 0.0653 |
| 8 | `hour_bucket=12-16` | 0.0502 |
| 9 | `session=europe` | 0.0468 |
| 10 | `hour_bucket=04-08` | 0.0452 |
| 11 | `hour_bucket=16-20` | 0.0418 |
| 12 | `hour_bucket=08-12` | 0.0417 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0355 |
| 14 | `dow=Fri` | 0.0246 |
| 15 | `hour_bucket=00-04` | 0.0206 |

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

**1. Win-rate 16.7%** (4 W / 20 L = 24 trade · -27.4pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 08-12`
   - `dow = Tue`

**2. Win-rate 30.4%** (17 W / 39 L = 56 trade · -13.7pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 08-12`
   - `dow ≠ Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1318 |
| 2 | `dow=Tue` | 0.0999 |
| 3 | `session=asia` | 0.0808 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0779 |
| 5 | `session=overlap` | 0.0756 |
| 6 | `dow=Thu` | 0.0658 |
| 7 | `hour_bucket=12-16` | 0.0648 |
| 8 | `dow=Wed` | 0.0610 |
| 9 | `hour_bucket=00-04` | 0.0487 |
| 10 | `hour_bucket=20-24` | 0.0452 |
| 11 | `dow=Mon` | 0.0424 |
| 12 | `session=europe` | 0.0331 |
| 13 | `hour_bucket=08-12` | 0.0320 |
| 14 | `session=us` | 0.0302 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0287 |

---

## XAUUSD · ml:balanced · SELL
- Toplam çözülmüş: **437**  ·  Baseline win-rate: **57.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=closed` | 0.0863 |
| 2 | `hour_bucket=04-08` | 0.0785 |
| 3 | `hour_bucket=16-20` | 0.0732 |
| 4 | `dow=Tue` | 0.0670 |
| 5 | `hour_bucket=00-04` | 0.0668 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0572 |
| 7 | `session=asia` | 0.0557 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0487 |
| 9 | `session=overlap` | 0.0474 |
| 10 | `hour_bucket=08-12` | 0.0433 |
| 11 | `hour_bucket=12-16` | 0.0432 |
| 12 | `dow=Mon` | 0.0421 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0412 |
| 14 | `session=us` | 0.0372 |
| 15 | `hour_bucket=20-24` | 0.0370 |

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

**1. Win-rate 5.0%** (1 W / 19 L = 20 trade · -36.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Wed`
   - `session = asia`
   - `dow = Tue`

**2. Win-rate 24.0%** (6 W / 19 L = 25 trade · -17.9pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Wed`
   - `session = asia`
   - `dow ≠ Tue`

**3. Win-rate 32.1%** (17 W / 36 L = 53 trade · -9.8pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `dow ≠ Wed`
   - `session ≠ asia`
   - `dow ≠ Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1193 |
| 2 | `dow=Tue` | 0.0944 |
| 3 | `dow=Wed` | 0.0847 |
| 4 | `session=overlap` | 0.0731 |
| 5 | `hour_bucket=12-16` | 0.0726 |
| 6 | `hour_bucket=00-04` | 0.0717 |
| 7 | `session=asia` | 0.0678 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0542 |
| 9 | `dow=Thu` | 0.0529 |
| 10 | `hour_bucket=08-12` | 0.0460 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0439 |
| 12 | `hour_bucket=20-24` | 0.0373 |
| 13 | `session=us` | 0.0339 |
| 14 | `dow=Mon` | 0.0335 |
| 15 | `session=europe` | 0.0273 |

---

## XAUUSD · ml:full_power · SELL
- Toplam çözülmüş: **462**  ·  Baseline win-rate: **54.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.2%** (16 W / 5 L = 21 trade · +22.1pp vs baseline)
   - `session ≠ overlap`
   - `ml_confidence_bucket = [50,60)`
   - `hour_bucket = 04-08`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1012 |
| 2 | `hour_bucket=12-16` | 0.0800 |
| 3 | `session=overlap` | 0.0771 |
| 4 | `hour_bucket=04-08` | 0.0664 |
| 5 | `hour_bucket=00-04` | 0.0618 |
| 6 | `session=asia` | 0.0588 |
| 7 | `dow=Thu` | 0.0574 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0565 |
| 9 | `dow=Tue` | 0.0533 |
| 10 | `hour_bucket=16-20` | 0.0442 |
| 11 | `session=closed` | 0.0413 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0408 |
| 13 | `dow=Fri` | 0.0367 |
| 14 | `hour_bucket=08-12` | 0.0355 |
| 15 | `dow=Mon` | 0.0354 |

---

## XAUUSD · ml:main · BUY
- Toplam çözülmüş: **223**  ·  Baseline win-rate: **43.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.0%** (16 W / 4 L = 20 trade · +36.5pp vs baseline)
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `dow = Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.7%** (5 W / 18 L = 23 trade · -21.8pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = asia`
   - `hour_bucket = 00-04`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -18.5pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session ≠ asia`
   - `session = us`

**3. Win-rate 29.2%** (7 W / 17 L = 24 trade · -14.3pp vs baseline)
   - `ml_confidence_bucket = [−∞,50)`
   - `session = asia`
   - `hour_bucket ≠ 00-04`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1153 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.1008 |
| 3 | `dow=Tue` | 0.0997 |
| 4 | `session=overlap` | 0.0798 |
| 5 | `hour_bucket=12-16` | 0.0701 |
| 6 | `session=asia` | 0.0675 |
| 7 | `dow=Thu` | 0.0557 |
| 8 | `dow=Mon` | 0.0437 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0424 |
| 10 | `dow=Wed` | 0.0400 |
| 11 | `hour_bucket=20-24` | 0.0398 |
| 12 | `hour_bucket=00-04` | 0.0370 |
| 13 | `dow=Fri` | 0.0327 |
| 14 | `session=europe` | 0.0324 |
| 15 | `session=us` | 0.0284 |

---

## XAUUSD · ml:main · SELL
- Toplam çözülmüş: **487**  ·  Baseline win-rate: **54.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=16-20` | 0.0764 |
| 2 | `session=closed` | 0.0707 |
| 3 | `session=europe` | 0.0659 |
| 4 | `dow=Mon` | 0.0581 |
| 5 | `hour_bucket=04-08` | 0.0573 |
| 6 | `session=asia` | 0.0563 |
| 7 | `hour_bucket=08-12` | 0.0559 |
| 8 | `dow=Fri` | 0.0533 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0510 |
| 10 | `hour_bucket=00-04` | 0.0509 |
| 11 | `dow=Tue` | 0.0472 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0456 |
| 13 | `session=overlap` | 0.0433 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0420 |
| 15 | `dow=Wed` | 0.0394 |

---

## XAUUSD · ml:ultra_safe · SELL
- Toplam çözülmüş: **95**  ·  Baseline win-rate: **44.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 31.8%** (7 W / 15 L = 22 trade · -12.4pp vs baseline)
   - `hour_bucket = 20-24`

**2. Win-rate 34.8%** (8 W / 15 L = 23 trade · -9.4pp vs baseline)
   - `hour_bucket ≠ 20-24`
   - `session = asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1059 |
| 2 | `hour_bucket=20-24` | 0.0955 |
| 3 | `dow=Thu` | 0.0946 |
| 4 | `session=europe` | 0.0760 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0672 |
| 6 | `session=asia` | 0.0644 |
| 7 | `hour_bucket=16-20` | 0.0634 |
| 8 | `hour_bucket=12-16` | 0.0578 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0471 |
| 10 | `dow=Wed` | 0.0448 |
| 11 | `dow=Tue` | 0.0435 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0349 |
| 13 | `hour_bucket=04-08` | 0.0311 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0306 |
| 15 | `dow=Fri` | 0.0259 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **2121**  ·  Baseline win-rate: **35.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 19.4%** (6 W / 25 L = 31 trade · -16.1pp vs baseline)
   - `dow ≠ Mon`
   - `hour_bucket = 12-16`
   - `dow ≠ Fri`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 20.0%** (83 W / 333 L = 416 trade · -15.5pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 08-12`
   - `session ≠ closed`

**3. Win-rate 30.9%** (17 W / 38 L = 55 trade · -4.6pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket = 08-12`
   - `ml_confidence_bucket ≠ [80,+∞)`

**4. Win-rate 33.3%** (10 W / 20 L = 30 trade · -2.2pp vs baseline)
   - `dow = Mon`
   - `hour_bucket = 00-04`
   - `ml_confidence_bucket ≠ [80,+∞)`

**5. Win-rate 34.8%** (278 W / 522 L = 800 trade · -0.7pp vs baseline)
   - `dow ≠ Mon`
   - `hour_bucket ≠ 12-16`
   - `dow ≠ Thu`
   - `session ≠ closed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1600 |
| 2 | `session=us` | 0.0711 |
| 3 | `hour_bucket=16-20` | 0.0626 |
| 4 | `dow=Thu` | 0.0607 |
| 5 | `dow=Fri` | 0.0477 |
| 6 | `dow=Tue` | 0.0432 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0350 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0324 |
| 9 | `hour_bucket=12-16` | 0.0323 |
| 10 | `hour_bucket=08-12` | 0.0304 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0298 |
| 12 | `hour_bucket=00-04` | 0.0297 |
| 13 | `session=europe` | 0.0291 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0290 |
| 15 | `ml_confidence_bucket=[50,60)` | 0.0275 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **2067**  ·  Baseline win-rate: **46.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.5%** (19 W / 2 L = 21 trade · +44.5pp vs baseline)
   - `hour_bucket = 20-24`
   - `dow ≠ Thu`
   - `dow = Sun`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 77.3%** (17 W / 5 L = 22 trade · +31.3pp vs baseline)
   - `hour_bucket = 20-24`
   - `dow ≠ Thu`
   - `dow = Sun`
   - `ml_confidence_bucket ≠ [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.1%** (3 W / 24 L = 27 trade · -34.9pp vs baseline)
   - `hour_bucket ≠ 20-24`
   - `dow = Mon`
   - `ml_confidence_bucket = [−∞,50)`
   - `hour_bucket = 04-08`

**2. Win-rate 15.4%** (4 W / 22 L = 26 trade · -30.6pp vs baseline)
   - `hour_bucket ≠ 20-24`
   - `dow ≠ Mon`
   - `near_support = True`

**3. Win-rate 27.3%** (9 W / 24 L = 33 trade · -18.7pp vs baseline)
   - `hour_bucket = 20-24`
   - `dow = Thu`
   - `session = closed`

**4. Win-rate 27.8%** (10 W / 26 L = 36 trade · -18.2pp vs baseline)
   - `hour_bucket ≠ 20-24`
   - `dow ≠ Mon`
   - `near_support ≠ True`
   - `sar_bearish = False`

**5. Win-rate 29.9%** (20 W / 47 L = 67 trade · -16.1pp vs baseline)
   - `hour_bucket ≠ 20-24`
   - `dow = Mon`
   - `ml_confidence_bucket = [−∞,50)`
   - `hour_bucket ≠ 04-08`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1003 |
| 2 | `hour_bucket=20-24` | 0.0868 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0734 |
| 4 | `dow=Sun` | 0.0730 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0487 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0470 |
| 7 | `dow=Tue` | 0.0427 |
| 8 | `dow=Thu` | 0.0406 |
| 9 | `session=us` | 0.0375 |
| 10 | `dow=Wed` | 0.0302 |
| 11 | `session=europe` | 0.0284 |
| 12 | `session=closed` | 0.0272 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0233 |
| 14 | `hour_bucket=04-08` | 0.0231 |
| 15 | `session=asia` | 0.0218 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **1099**  ·  Baseline win-rate: **41.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.8%** (4 W / 65 L = 69 trade · -35.5pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow = Tue`
   - `ml_confidence_bucket = [60,70)`

**2. Win-rate 16.2%** (6 W / 31 L = 37 trade · -25.1pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `dow = Mon`
   - `ml_confidence_bucket = [−∞,50)`

**3. Win-rate 17.5%** (7 W / 33 L = 40 trade · -23.8pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow = Tue`
   - `ml_confidence_bucket ≠ [60,70)`

**4. Win-rate 27.9%** (29 W / 75 L = 104 trade · -13.4pp vs baseline)
   - `hour_bucket ≠ 00-04`
   - `dow = Mon`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `session ≠ europe`

**5. Win-rate 28.6%** (6 W / 15 L = 21 trade · -12.7pp vs baseline)
   - `hour_bucket = 00-04`
   - `dow ≠ Tue`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=00-04` | 0.1069 |
| 2 | `dow=Mon` | 0.1052 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0868 |
| 4 | `dow=Tue` | 0.0702 |
| 5 | `dow=Fri` | 0.0595 |
| 6 | `session=asia` | 0.0583 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0483 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0389 |
| 9 | `session=europe` | 0.0336 |
| 10 | `dow=Thu` | 0.0294 |
| 11 | `dow=Wed` | 0.0251 |
| 12 | `hour_bucket=08-12` | 0.0251 |
| 13 | `session=overlap` | 0.0234 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0233 |
| 15 | `hour_bucket=12-16` | 0.0215 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **1410**  ·  Baseline win-rate: **55.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.0%** (21 W / 4 L = 25 trade · +28.3pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket = 16-20`
   - `dow = Tue`
   - `ml_confidence_bucket ≠ [60,70)`

**2. Win-rate 80.0%** (16 W / 4 L = 20 trade · +24.3pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket = 16-20`
   - `dow = Tue`
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 78.6%** (33 W / 9 L = 42 trade · +22.9pp vs baseline)
   - `dow = Sun`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.3%** (10 W / 23 L = 33 trade · -25.4pp vs baseline)
   - `dow ≠ Sun`
   - `hour_bucket ≠ 16-20`
   - `bb_extreme_upper = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0684 |
| 2 | `dow=Sun` | 0.0665 |
| 3 | `hour_bucket=16-20` | 0.0660 |
| 4 | `session=europe` | 0.0594 |
| 5 | `dow=Tue` | 0.0488 |
| 6 | `dow=Thu` | 0.0463 |
| 7 | `session=overlap` | 0.0462 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0458 |
| 9 | `session=us` | 0.0419 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0340 |
| 11 | `hour_bucket=08-12` | 0.0333 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0321 |
| 13 | `session=asia` | 0.0311 |
| 14 | `dow=Fri` | 0.0280 |
| 15 | `hour_bucket=12-16` | 0.0256 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **1688**  ·  Baseline win-rate: **45.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.2%** (26 W / 6 L = 32 trade · +36.1pp vs baseline)
   - `dow ≠ Mon`
   - `rsi_M30 = [30,50)`
   - `dow ≠ Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.5%** (3 W / 23 L = 26 trade · -33.6pp vs baseline)
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `hour_bucket ≠ 16-20`

**2. Win-rate 15.5%** (9 W / 49 L = 58 trade · -29.6pp vs baseline)
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `hour_bucket = 16-20`

**3. Win-rate 18.8%** (6 W / 26 L = 32 trade · -26.3pp vs baseline)
   - `dow = Mon`
   - `session = us`
   - `ml_confidence_bucket = [−∞,50)`

**4. Win-rate 20.4%** (10 W / 39 L = 49 trade · -24.7pp vs baseline)
   - `dow = Mon`
   - `session ≠ us`
   - `hour_bucket = 00-04`

**5. Win-rate 25.0%** (12 W / 36 L = 48 trade · -20.1pp vs baseline)
   - `dow = Mon`
   - `session ≠ us`
   - `hour_bucket ≠ 00-04`
   - `session = overlap`

**6. Win-rate 26.8%** (11 W / 30 L = 41 trade · -18.3pp vs baseline)
   - `dow ≠ Mon`
   - `rsi_M30 ≠ [30,50)`
   - `hour_bucket = 08-12`
   - `dow = Wed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1423 |
| 2 | `dow=Fri` | 0.0694 |
| 3 | `session=europe` | 0.0538 |
| 4 | `session=us` | 0.0495 |
| 5 | `dow=Thu` | 0.0456 |
| 6 | `dow=Tue` | 0.0455 |
| 7 | `dow=Wed` | 0.0450 |
| 8 | `hour_bucket=16-20` | 0.0377 |
| 9 | `hour_bucket=08-12` | 0.0370 |
| 10 | `hour_bucket=00-04` | 0.0336 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0336 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0331 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0310 |
| 14 | `hour_bucket=12-16` | 0.0254 |
| 15 | `hour_bucket=04-08` | 0.0226 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **2090**  ·  Baseline win-rate: **59.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (27 W / 3 L = 30 trade · +30.9pp vs baseline)
   - `dow ≠ Mon`
   - `session ≠ overlap`
   - `near_support = False`

**2. Win-rate 81.6%** (31 W / 7 L = 38 trade · +22.5pp vs baseline)
   - `dow ≠ Mon`
   - `session = overlap`
   - `ml_confidence_bucket ≠ [50,60)`
   - `hour_bucket ≠ 12-16`

**3. Win-rate 78.8%** (26 W / 7 L = 33 trade · +19.7pp vs baseline)
   - `dow = Mon`
   - `hour_bucket = 04-08`
   - `ml_confidence_bucket = [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.7%** (23 W / 63 L = 86 trade · -32.4pp vs baseline)
   - `dow = Mon`
   - `hour_bucket ≠ 04-08`
   - `session = us`
   - `hour_bucket ≠ 20-24`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1016 |
| 2 | `dow=Tue` | 0.0927 |
| 3 | `ml_confidence_bucket=[50,60)` | 0.0665 |
| 4 | `hour_bucket=16-20` | 0.0481 |
| 5 | `session=overlap` | 0.0408 |
| 6 | `session=us` | 0.0398 |
| 7 | `session=asia` | 0.0356 |
| 8 | `hour_bucket=04-08` | 0.0356 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0355 |
| 10 | `dow=Thu` | 0.0340 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0325 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0323 |
| 13 | `ml_confidence_bucket=[−∞,50)` | 0.0311 |
| 14 | `session=europe` | 0.0287 |
| 15 | `hour_bucket=08-12` | 0.0279 |

---

## XAUUSD · smc · BUY
- Toplam çözülmüş: **322**  ·  Baseline win-rate: **57.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +33.8pp vs baseline)
   - `session ≠ us`
   - `dow = Mon`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.1162 |
| 2 | `session=us` | 0.1057 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0853 |
| 4 | `session=asia` | 0.0739 |
| 5 | `hour_bucket=04-08` | 0.0715 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0706 |
| 7 | `dow=Thu` | 0.0706 |
| 8 | `session=europe` | 0.0516 |
| 9 | `hour_bucket=12-16` | 0.0489 |
| 10 | `hour_bucket=08-12` | 0.0470 |
| 11 | `hour_bucket=00-04` | 0.0404 |
| 12 | `dow=Fri` | 0.0391 |
| 13 | `hour_bucket=20-24` | 0.0334 |
| 14 | `session=overlap` | 0.0314 |
| 15 | `session=closed` | 0.0148 |

---

## XAUUSD · smc · SELL
- Toplam çözülmüş: **1109**  ·  Baseline win-rate: **47.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.9%** (30 W / 8 L = 38 trade · +31.0pp vs baseline)
   - `session ≠ us`
   - `session ≠ europe`
   - `dow ≠ Fri`
   - `hour_bucket = 12-16`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.5%** (17 W / 62 L = 79 trade · -26.4pp vs baseline)
   - `session = us`
   - `near_resistance ≠ False`
   - `dow = Fri`

**2. Win-rate 26.8%** (26 W / 71 L = 97 trade · -21.1pp vs baseline)
   - `session ≠ us`
   - `session = europe`
   - `ml_confidence_bucket ≠ [70,80)`
   - `dow = Fri`

**3. Win-rate 28.3%** (34 W / 86 L = 120 trade · -19.6pp vs baseline)
   - `session = us`
   - `near_resistance ≠ False`
   - `dow ≠ Fri`
   - `dow = Wed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=us` | 0.1581 |
| 2 | `dow=Fri` | 0.1160 |
| 3 | `session=asia` | 0.0815 |
| 4 | `dow=Sun` | 0.0714 |
| 5 | `session=closed` | 0.0599 |
| 6 | `hour_bucket=20-24` | 0.0588 |
| 7 | `session=europe` | 0.0460 |
| 8 | `hour_bucket=04-08` | 0.0454 |
| 9 | `session=overlap` | 0.0405 |
| 10 | `dow=Thu` | 0.0372 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0360 |
| 12 | `dow=Wed` | 0.0265 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0226 |
| 14 | `hour_bucket=08-12` | 0.0204 |
| 15 | `hour_bucket=00-04` | 0.0201 |

---
