# Pattern Mining Raporu
_2026-07-16T03:28:40.817818Z — son 60 gün — 43237 resolved sinyal_

**Yöntem:** Decision Tree (max_depth=4) + Random Forest feature importance.
Her leaf bir kural. min_samples_leaf=20, class_weight=balanced.

**Yorum kılavuzu:**
- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)
- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)
- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli

---

## GLOBAL — tüm sembol & model
- Toplam çözülmüş: **43237**  ·  Baseline win-rate: **42.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.1%** (97 W / 17 L = 114 trade · +42.9pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `adx_H4 = [25,35)`
   - `rsi_H1 ≠ [30,50)`
   - `regime_label = strong_trend_down`

**2. Win-rate 84.9%** (952 W / 169 L = 1121 trade · +42.7pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `consec_red_M30 ≠ [0,2)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.6%** (65 W / 925 L = 990 trade · -35.6pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `adx_H4 ≠ [25,35)`
   - `H4_ema_stack = down`
   - `M30_ema_stack = up`

**2. Win-rate 14.0%** (58 W / 356 L = 414 trade · -28.2pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`
   - `bb_extreme_upper ≠ False`
   - `session ≠ overlap`

**3. Win-rate 24.3%** (37 W / 115 L = 152 trade · -17.9pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `consec_red_M30 = [0,2)`
   - `bb_extreme_upper = True`

**4. Win-rate 31.3%** (1553 W / 3412 L = 4965 trade · -10.9pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `adx_H4 ≠ [25,35)`
   - `H4_ema_stack ≠ down`
   - `macro_alignment = weak_pro`

**5. Win-rate 32.7%** (289 W / 595 L = 884 trade · -9.5pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`
   - `bb_extreme_upper = False`
   - `M30_adx_label = ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[30,50)` | 0.0344 |
| 2 | `rsi_H1=[30,50)` | 0.0264 |
| 3 | `macro_alignment=strong_pro` | 0.0258 |
| 4 | `H1_ema_stack=down` | 0.0236 |
| 5 | `M30_adx_label=trending` | 0.0225 |
| 6 | `H4_ema_stack=NA` | 0.0205 |
| 7 | `macro_alignment=strong_against` | 0.0205 |
| 8 | `adx_M30=[35,+∞)` | 0.0193 |
| 9 | `macro_alignment=weak_pro` | 0.0171 |
| 10 | `bb_extreme_upper=False` | 0.0170 |
| 11 | `dow=Mon` | 0.0163 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0163 |
| 13 | `M30_ema_stack=down` | 0.0159 |
| 14 | `bb_extreme_upper=True` | 0.0147 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0143 |

---

## GDAXI.INDX · ai_panel
- Toplam çözülmüş: **131**  ·  Baseline win-rate: **58.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.1%** (27 W / 2 L = 29 trade · +35.1pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `session = europe`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.9%** (7 W / 19 L = 26 trade · -31.1pp vs baseline)
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0630 |
| 2 | `rsi_H1=[30,50)` | 0.0612 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0522 |
| 4 | `rsi_H1=[50,65)` | 0.0521 |
| 5 | `sar_bearish=True` | 0.0420 |
| 6 | `sar_bearish=False` | 0.0385 |
| 7 | `adx_H1=[25,35)` | 0.0359 |
| 8 | `macro_alignment=strong_against` | 0.0354 |
| 9 | `dow=Mon` | 0.0345 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0344 |
| 11 | `hour_bucket=08-12` | 0.0288 |
| 12 | `session=europe` | 0.0255 |
| 13 | `H1_ema_stack=mixed` | 0.0218 |
| 14 | `regime_label=ranging` | 0.0190 |
| 15 | `H1_adx_label=ranging` | 0.0172 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **478**  ·  Baseline win-rate: **43.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.0%** (24 W / 1 L = 25 trade · +52.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H4 = [25,35)`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 81.5%** (22 W / 5 L = 27 trade · +37.8pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack = mixed`
   - `macro_alignment = neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.8%** (13 W / 75 L = 88 trade · -28.9pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack ≠ mixed`
   - `rsi_H1 ≠ [30,50)`
   - `rsi_H4 = [50,65)`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -18.7pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ strong_pro`

**3. Win-rate 30.3%** (23 W / 53 L = 76 trade · -13.4pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack ≠ mixed`
   - `rsi_H1 ≠ [30,50)`
   - `rsi_H4 ≠ [50,65)`

**4. Win-rate 31.2%** (10 W / 22 L = 32 trade · -12.5pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack = mixed`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0807 |
| 2 | `sar_bearish=True` | 0.0541 |
| 3 | `rsi_H1=[30,50)` | 0.0404 |
| 4 | `bb_extreme_upper=False` | 0.0266 |
| 5 | `bb_extreme_upper=True` | 0.0254 |
| 6 | `rsi_H1=[65,75)` | 0.0233 |
| 7 | `H4_adx_label=ranging` | 0.0230 |
| 8 | `H4_ema_stack=mixed` | 0.0224 |
| 9 | `H1_adx_label=trending` | 0.0196 |
| 10 | `adx_H4=[−∞,18)` | 0.0195 |
| 11 | `macro_alignment=neutral` | 0.0190 |
| 12 | `H4_ema_stack=NA` | 0.0179 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0169 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0168 |
| 15 | `H4_adx_label=weak_trend` | 0.0164 |

---

## GDAXI.INDX · ml:balanced
- Toplam çözülmüş: **250**  ·  Baseline win-rate: **65.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.7%** (42 W / 1 L = 43 trade · +32.1pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_ema_stack ≠ down`
   - `vix_chg1d = [0,3)`

**2. Win-rate 84.8%** (28 W / 5 L = 33 trade · +19.2pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_ema_stack ≠ down`
   - `vix_chg1d ≠ [0,3)`

**3. Win-rate 76.9%** (30 W / 9 L = 39 trade · +11.3pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `adx_H1 = [18,25)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 19.4%** (6 W / 25 L = 31 trade · -46.2pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `adx_H1 ≠ [18,25)`
   - `sar_bearish ≠ True`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[50,65)` | 0.0644 |
| 2 | `sar_bearish=False` | 0.0538 |
| 3 | `rsi_H1=[30,50)` | 0.0494 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0460 |
| 5 | `sar_bearish=True` | 0.0409 |
| 6 | `H1_ema_stack=down` | 0.0386 |
| 7 | `adx_H1=[−∞,18)` | 0.0362 |
| 8 | `macro_alignment=strong_against` | 0.0352 |
| 9 | `H4_ema_stack=up` | 0.0331 |
| 10 | `H1_adx_label=ranging` | 0.0310 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0260 |
| 12 | `H4_ema_stack=NA` | 0.0229 |
| 13 | `H1_adx_label=weak_trend` | 0.0210 |
| 14 | `adx_H1=[18,25)` | 0.0200 |
| 15 | `macro_alignment=neutral` | 0.0196 |

---

## GDAXI.INDX · ml:full_power
- Toplam çözülmüş: **275**  ·  Baseline win-rate: **60.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +39.3pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Tue`

**2. Win-rate 83.1%** (49 W / 10 L = 59 trade · +22.4pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Tue`
   - `H4_ema_stack = up`

**3. Win-rate 81.5%** (22 W / 5 L = 27 trade · +20.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_H4 = [50,65)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -53.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H1 = [50,65)`
   - `H1_adx_label ≠ weak_trend`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0754 |
| 2 | `sar_bearish=True` | 0.0731 |
| 3 | `rsi_H1=[30,50)` | 0.0609 |
| 4 | `rsi_H1=[50,65)` | 0.0569 |
| 5 | `adx_H1=[−∞,18)` | 0.0398 |
| 6 | `H1_adx_label=ranging` | 0.0327 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0285 |
| 8 | `macro_alignment=strong_against` | 0.0252 |
| 9 | `vix_chg1d=[0,3)` | 0.0247 |
| 10 | `H4_ema_stack=NA` | 0.0227 |
| 11 | `H1_adx_label=weak_trend` | 0.0217 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0214 |
| 13 | `H1_ema_stack=down` | 0.0200 |
| 14 | `H1_ema_stack=up` | 0.0179 |
| 15 | `bb_extreme_lower=True` | 0.0173 |

---

## GDAXI.INDX · ml:main
- Toplam çözülmüş: **275**  ·  Baseline win-rate: **60.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +39.3pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Tue`

**2. Win-rate 83.1%** (49 W / 10 L = 59 trade · +22.4pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Tue`
   - `H4_ema_stack = up`

**3. Win-rate 81.5%** (22 W / 5 L = 27 trade · +20.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_H4 = [50,65)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -53.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H1 = [50,65)`
   - `H1_adx_label ≠ weak_trend`
   - `adx_H4 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[50,65)` | 0.0837 |
| 2 | `sar_bearish=False` | 0.0723 |
| 3 | `sar_bearish=True` | 0.0627 |
| 4 | `rsi_H1=[30,50)` | 0.0367 |
| 5 | `H1_adx_label=ranging` | 0.0352 |
| 6 | `H4_ema_stack=NA` | 0.0319 |
| 7 | `adx_H1=[−∞,18)` | 0.0295 |
| 8 | `H4_ema_stack=up` | 0.0282 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0277 |
| 10 | `macro_alignment=strong_against` | 0.0274 |
| 11 | `H1_ema_stack=down` | 0.0237 |
| 12 | `vix_chg1d=[0,3)` | 0.0189 |
| 13 | `H1_adx_label=weak_trend` | 0.0184 |
| 14 | `adx_H1=[18,25)` | 0.0183 |
| 15 | `bb_extreme_lower=True` | 0.0182 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **1293**  ·  Baseline win-rate: **25.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 221 L = 221 trade · -25.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish ≠ True`

**2. Win-rate 2.5%** (2 W / 77 L = 79 trade · -22.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 5.3%** (5 W / 90 L = 95 trade · -19.7pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish = True`

**4. Win-rate 6.7%** (2 W / 28 L = 30 trade · -18.3pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `bb_extreme_upper = True`

**5. Win-rate 14.3%** (3 W / 18 L = 21 trade · -10.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `rsi_H1 = [65,75)`

**6. Win-rate 17.4%** (4 W / 19 L = 23 trade · -7.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `ml_confidence_bucket = [−∞,50)`
   - `macro_alignment = weak_against`

**7. Win-rate 21.1%** (16 W / 60 L = 76 trade · -3.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

**8. Win-rate 22.2%** (6 W / 21 L = 27 trade · -2.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label = NA`
   - `session = europe`

**9. Win-rate 25.9%** (90 W / 257 L = 347 trade · 0.9pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `bb_extreme_upper ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1666 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0679 |
| 3 | `bb_extreme_upper=True` | 0.0459 |
| 4 | `bb_extreme_upper=False` | 0.0434 |
| 5 | `near_resistance=True` | 0.0257 |
| 6 | `regime_label=ranging` | 0.0247 |
| 7 | `near_resistance=False` | 0.0218 |
| 8 | `vix_chg1d=[0,3)` | 0.0215 |
| 9 | `vix_chg1d=[-3,0)` | 0.0210 |
| 10 | `adx_H4=[−∞,18)` | 0.0184 |
| 11 | `H4_adx_label=weak_trend` | 0.0166 |
| 12 | `dow=Fri` | 0.0164 |
| 13 | `mtf_trend=mixed` | 0.0157 |
| 14 | `rsi_H1=[50,65)` | 0.0152 |
| 15 | `adx_H4=[18,25)` | 0.0145 |

---

## GDAXI.INDX · pulse1_inv
- Toplam çözülmüş: **141**  ·  Baseline win-rate: **36.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.6%** (8 W / 29 L = 37 trade · -15.3pp vs baseline)
   - `macro_alignment = weak_against`

**2. Win-rate 26.1%** (6 W / 17 L = 23 trade · -10.8pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `dxy_chg1d = [0.5,+∞)`

**3. Win-rate 33.3%** (8 W / 16 L = 24 trade · -3.6pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label = ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0660 |
| 2 | `dow=Thu` | 0.0429 |
| 3 | `H1_adx_label=trending` | 0.0391 |
| 4 | `H1_adx_label=ranging` | 0.0362 |
| 5 | `H1_ema_stack=mixed` | 0.0359 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0345 |
| 7 | `hour_bucket=12-16` | 0.0310 |
| 8 | `adx_H1=[−∞,18)` | 0.0306 |
| 9 | `adx_H1=[25,35)` | 0.0303 |
| 10 | `session=overlap` | 0.0300 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0271 |
| 12 | `H1_ema_stack=up` | 0.0264 |
| 13 | `sar_bearish=False` | 0.0247 |
| 14 | `rsi_H1=[50,65)` | 0.0226 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0225 |

---

## GDAXI.INDX · pulse2
- Toplam çözülmüş: **555**  ·  Baseline win-rate: **44.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.7%** (42 W / 1 L = 43 trade · +53.7pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +43.9pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `dow = Tue`

**3. Win-rate 75.9%** (22 W / 7 L = 29 trade · +31.9pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `hour_bucket = 12-16`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 30 L = 30 trade · -44.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = True`
   - `rsi_H4 = [50,65)`

**2. Win-rate 6.2%** (2 W / 30 L = 32 trade · -37.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper ≠ True`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 7.7%** (2 W / 24 L = 26 trade · -36.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = True`
   - `rsi_H4 ≠ [50,65)`

**4. Win-rate 16.1%** (5 W / 26 L = 31 trade · -27.9pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend = mixed`
   - `us10y_chg1d = [0.5,+∞)`

**5. Win-rate 23.3%** (7 W / 23 L = 30 trade · -20.7pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ strong_pro`

**6. Win-rate 32.9%** (26 W / 53 L = 79 trade · -11.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend = mixed`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `regime_label = transition`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0993 |
| 2 | `sar_bearish=True` | 0.0724 |
| 3 | `bb_extreme_upper=False` | 0.0423 |
| 4 | `bb_extreme_upper=True` | 0.0341 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0230 |
| 6 | `vix_chg1d=[0,3)` | 0.0221 |
| 7 | `regime_label=transition` | 0.0207 |
| 8 | `dow=Mon` | 0.0201 |
| 9 | `H4_adx_label=ranging` | 0.0197 |
| 10 | `regime_label=ranging` | 0.0197 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0196 |
| 12 | `near_resistance=False` | 0.0190 |
| 13 | `H4_ema_stack=NA` | 0.0189 |
| 14 | `volatility_regime=high` | 0.0177 |
| 15 | `bb_extreme_lower=True` | 0.0174 |

---

## GDAXI.INDX · pulse2_inv
- Toplam çözülmüş: **128**  ·  Baseline win-rate: **48.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.5%** (9 W / 25 L = 34 trade · -21.9pp vs baseline)
   - `macro_alignment ≠ strong_pro`
   - `macro_alignment ≠ neutral`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0596 |
| 2 | `macro_alignment=strong_pro` | 0.0503 |
| 3 | `adx_H4=NA` | 0.0450 |
| 4 | `H4_ema_stack=up` | 0.0445 |
| 5 | `volatility_regime=normal` | 0.0372 |
| 6 | `H1_ema_stack=down` | 0.0355 |
| 7 | `H1_ema_stack=up` | 0.0354 |
| 8 | `hour_bucket=08-12` | 0.0327 |
| 9 | `rsi_H1=[50,65)` | 0.0282 |
| 10 | `rsi_H4=NA` | 0.0257 |
| 11 | `H4_adx_label=NA` | 0.0237 |
| 12 | `rsi_H4=[75,+∞)` | 0.0230 |
| 13 | `dow=Tue` | 0.0227 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0216 |
| 15 | `ml_confidence_bucket=[−∞,50)` | 0.0213 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **1160**  ·  Baseline win-rate: **36.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.6%** (55 W / 15 L = 70 trade · +42.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [50,65)`
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_H4 ≠ NA`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 106 L = 106 trade · -36.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 = [50,65)`
   - `bb_extreme_upper = True`
   - `macro_alignment ≠ neutral`

**2. Win-rate 3.7%** (1 W / 26 L = 27 trade · -32.8pp vs baseline)
   - `sar_bearish = True`
   - `H1_adx_label = ranging`
   - `vix_chg1d ≠ [3,+∞)`
   - `hour_bucket ≠ 12-16`

**3. Win-rate 9.5%** (2 W / 19 L = 21 trade · -27.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 = [50,65)`
   - `bb_extreme_upper = True`
   - `macro_alignment = neutral`

**4. Win-rate 11.1%** (3 W / 24 L = 27 trade · -25.4pp vs baseline)
   - `sar_bearish = True`
   - `H1_adx_label ≠ ranging`
   - `dxy_chg1d = [0.5,+∞)`

**5. Win-rate 11.4%** (10 W / 78 L = 88 trade · -25.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 = [50,65)`
   - `bb_extreme_upper ≠ True`
   - `ml_confidence_bucket = [60,70)`

**6. Win-rate 20.5%** (31 W / 120 L = 151 trade · -16.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [50,65)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [0,3)`

**7. Win-rate 25.9%** (7 W / 20 L = 27 trade · -10.6pp vs baseline)
   - `sar_bearish = True`
   - `H1_adx_label = ranging`
   - `vix_chg1d ≠ [3,+∞)`
   - `hour_bucket = 12-16`

**8. Win-rate 30.7%** (23 W / 52 L = 75 trade · -5.8pp vs baseline)
   - `sar_bearish = True`
   - `H1_adx_label ≠ ranging`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `macro_alignment = strong_pro`

**9. Win-rate 32.3%** (10 W / 21 L = 31 trade · -4.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [50,65)`
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_H4 = NA`

**10. Win-rate 33.3%** (9 W / 18 L = 27 trade · -3.2pp vs baseline)
   - `sar_bearish = True`
   - `H1_adx_label = ranging`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.0416 |
| 2 | `sar_bearish=False` | 0.0367 |
| 3 | `H1_adx_label=trending` | 0.0325 |
| 4 | `bb_extreme_upper=False` | 0.0324 |
| 5 | `sar_bearish=True` | 0.0300 |
| 6 | `adx_H1=[−∞,18)` | 0.0294 |
| 7 | `bb_extreme_upper=True` | 0.0267 |
| 8 | `overbought=True` | 0.0238 |
| 9 | `rsi_H1=[30,50)` | 0.0217 |
| 10 | `H1_adx_label=ranging` | 0.0212 |
| 11 | `H1_ema_stack=mixed` | 0.0207 |
| 12 | `overbought=False` | 0.0201 |
| 13 | `rsi_H4=[50,65)` | 0.0185 |
| 14 | `vix_chg1d=[-3,0)` | 0.0181 |
| 15 | `session=europe` | 0.0167 |

---

## GDAXI.INDX · pulse3_inv
- Toplam çözülmüş: **177**  ·  Baseline win-rate: **43.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +33.8pp vs baseline)
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 19.0%** (4 W / 17 L = 21 trade · -24.5pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [−∞,-3)`

**2. Win-rate 24.1%** (7 W / 22 L = 29 trade · -19.4pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[0,0.5)` | 0.0464 |
| 2 | `H4_adx_label=trending` | 0.0400 |
| 3 | `H4_adx_label=NA` | 0.0356 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0297 |
| 5 | `macro_alignment=strong_pro` | 0.0293 |
| 6 | `H1_adx_label=trending` | 0.0281 |
| 7 | `dow=Thu` | 0.0273 |
| 8 | `rsi_H4=NA` | 0.0272 |
| 9 | `adx_H4=NA` | 0.0266 |
| 10 | `rsi_H4=[75,+∞)` | 0.0259 |
| 11 | `H4_ema_stack=NA` | 0.0250 |
| 12 | `mtf_trend=all_up` | 0.0250 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0240 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0217 |
| 15 | `adx_H1=[35,+∞)` | 0.0202 |

---

## GDAXI.INDX · smc
- Toplam çözülmüş: **112**  ·  Baseline win-rate: **41.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.0%** (17 W / 4 L = 21 trade · +39.9pp vs baseline)
   - `adx_H4 = [−∞,18)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.3%** (1 W / 22 L = 23 trade · -36.8pp vs baseline)
   - `adx_H4 ≠ [−∞,18)`
   - `us10y_chg1d = [0.5,+∞)`

**2. Win-rate 18.5%** (5 W / 22 L = 27 trade · -22.6pp vs baseline)
   - `adx_H4 ≠ [−∞,18)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[0.5,+∞)` | 0.0699 |
| 2 | `adx_H4=[−∞,18)` | 0.0636 |
| 3 | `macro_alignment=strong_against` | 0.0523 |
| 4 | `H4_adx_label=ranging` | 0.0508 |
| 5 | `sar_bearish=False` | 0.0402 |
| 6 | `regime_label=ranging` | 0.0381 |
| 7 | `H1_ema_stack=up` | 0.0360 |
| 8 | `sar_bearish=True` | 0.0313 |
| 9 | `H4_adx_label=trending` | 0.0309 |
| 10 | `rsi_H1=[50,65)` | 0.0279 |
| 11 | `dow=Fri` | 0.0278 |
| 12 | `us10y_chg1d=[-0.5,0)` | 0.0267 |
| 13 | `rsi_H1=[65,75)` | 0.0257 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0251 |
| 15 | `regime_label=strong_trend_up` | 0.0250 |

---

## NDX.INDX · ai_panel
- Toplam çözülmüş: **134**  ·  Baseline win-rate: **62.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +28.6pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack = up`
   - `sar_bearish ≠ False`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +12.3pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack = up`
   - `sar_bearish = False`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0704 |
| 2 | `sar_bearish=True` | 0.0535 |
| 3 | `H4_ema_stack=up` | 0.0427 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0380 |
| 5 | `H4_adx_label=trending` | 0.0352 |
| 6 | `sar_bearish=False` | 0.0332 |
| 7 | `macro_alignment=weak_pro` | 0.0288 |
| 8 | `H1_adx_label=ranging` | 0.0263 |
| 9 | `adx_H1=[−∞,18)` | 0.0248 |
| 10 | `mtf_trend=all_up` | 0.0236 |
| 11 | `mtf_trend=mixed` | 0.0231 |
| 12 | `rsi_H4=[30,50)` | 0.0218 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0217 |
| 14 | `session=overlap` | 0.0204 |
| 15 | `rsi_H1=[50,65)` | 0.0203 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **307**  ·  Baseline win-rate: **47.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.5%** (55 W / 16 L = 71 trade · +30.3pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `rsi_H1 ≠ [65,75)`
   - `H1_ema_stack ≠ up`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.8%** (3 W / 31 L = 34 trade · -38.4pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `adx_H4 ≠ [25,35)`
   - `sar_bearish ≠ True`

**2. Win-rate 20.0%** (5 W / 20 L = 25 trade · -27.2pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `rsi_H1 = [65,75)`

**3. Win-rate 25.0%** (7 W / 21 L = 28 trade · -22.2pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `adx_H4 ≠ [25,35)`
   - `sar_bearish = True`

**4. Win-rate 30.8%** (12 W / 27 L = 39 trade · -16.4pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `rsi_H1 ≠ [65,75)`
   - `H1_ema_stack = up`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0749 |
| 2 | `rsi_H1=[65,75)` | 0.0548 |
| 3 | `sar_bearish=True` | 0.0437 |
| 4 | `H1_ema_stack=up` | 0.0401 |
| 5 | `H1_adx_label=trending` | 0.0371 |
| 6 | `H1_ema_stack=mixed` | 0.0370 |
| 7 | `sar_bearish=False` | 0.0351 |
| 8 | `mtf_trend=mixed` | 0.0257 |
| 9 | `adx_H4=[25,35)` | 0.0248 |
| 10 | `dow=Mon` | 0.0233 |
| 11 | `rsi_H4=[30,50)` | 0.0224 |
| 12 | `bb_extreme_upper=True` | 0.0207 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0196 |
| 14 | `adx_H1=[18,25)` | 0.0194 |
| 15 | `H1_adx_label=weak_trend` | 0.0187 |

---

## NDX.INDX · ml:balanced
- Toplam çözülmüş: **273**  ·  Baseline win-rate: **53.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.7%** (26 W / 4 L = 30 trade · +32.9pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `H4_ema_stack ≠ mixed`
   - `session_phase = open_drive`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.0%** (3 W / 20 L = 23 trade · -40.8pp vs baseline)
   - `us10y_chg1d = [0,0.5)`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 28.6%** (8 W / 20 L = 28 trade · -25.2pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `H4_ema_stack = mixed`
   - `adx_H4 ≠ [35,+∞)`

**3. Win-rate 32.0%** (8 W / 17 L = 25 trade · -21.8pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `H4_ema_stack ≠ mixed`
   - `session_phase ≠ open_drive`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0466 |
| 2 | `session_phase=mid_session` | 0.0358 |
| 3 | `H4_ema_stack=mixed` | 0.0355 |
| 4 | `macro_alignment=weak_pro` | 0.0304 |
| 5 | `sar_bearish=False` | 0.0299 |
| 6 | `rsi_H1=[30,50)` | 0.0295 |
| 7 | `H4_ema_stack=up` | 0.0277 |
| 8 | `mtf_trend=mixed` | 0.0256 |
| 9 | `us10y_chg1d=[0,0.5)` | 0.0249 |
| 10 | `sar_bearish=True` | 0.0238 |
| 11 | `adx_H4=[35,+∞)` | 0.0236 |
| 12 | `session_phase=open_drive` | 0.0224 |
| 13 | `vix_chg1d=[-3,0)` | 0.0206 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0205 |
| 15 | `us10y_chg1d=[-0.5,0)` | 0.0201 |

---

## NDX.INDX · ml:full_power
- Toplam çözülmüş: **275**  ·  Baseline win-rate: **55.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.1%** (27 W / 4 L = 31 trade · +31.8pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Mon`
   - `dxy_chg1d ≠ [0,0.5)`
   - `adx_H4 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.3%** (7 W / 23 L = 30 trade · -32.0pp vs baseline)
   - `macro_alignment = weak_pro`

**2. Win-rate 29.4%** (10 W / 24 L = 34 trade · -25.9pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Mon`
   - `dxy_chg1d = [0,0.5)`
   - `sar_bearish ≠ True`

**3. Win-rate 35.0%** (7 W / 13 L = 20 trade · -20.3pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow = Mon`
   - `volatility_regime ≠ high`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0511 |
| 2 | `macro_alignment=weak_pro` | 0.0468 |
| 3 | `H4_ema_stack=mixed` | 0.0338 |
| 4 | `sar_bearish=True` | 0.0280 |
| 5 | `rsi_H1=[30,50)` | 0.0274 |
| 6 | `volatility_regime=high` | 0.0260 |
| 7 | `rsi_H1=[50,65)` | 0.0251 |
| 8 | `adx_H4=[35,+∞)` | 0.0249 |
| 9 | `sar_bearish=False` | 0.0243 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0233 |
| 11 | `session_phase=mid_session` | 0.0228 |
| 12 | `H4_ema_stack=up` | 0.0225 |
| 13 | `macro_alignment=neutral` | 0.0221 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0218 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0217 |

---

## NDX.INDX · ml:main
- Toplam çözülmüş: **275**  ·  Baseline win-rate: **56.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.3%** (7 W / 23 L = 30 trade · -32.7pp vs baseline)
   - `macro_alignment = weak_pro`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -21.0pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow = Mon`
   - `volatility_regime = normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0517 |
| 2 | `macro_alignment=weak_pro` | 0.0469 |
| 3 | `session_phase=mid_session` | 0.0340 |
| 4 | `H4_ema_stack=up` | 0.0318 |
| 5 | `H4_ema_stack=mixed` | 0.0317 |
| 6 | `adx_H4=[35,+∞)` | 0.0311 |
| 7 | `macro_alignment=neutral` | 0.0293 |
| 8 | `us10y_chg1d=[0,0.5)` | 0.0282 |
| 9 | `sar_bearish=True` | 0.0263 |
| 10 | `sar_bearish=False` | 0.0263 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0246 |
| 12 | `H1_adx_label=weak_trend` | 0.0225 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0219 |
| 14 | `mtf_trend=mixed` | 0.0217 |
| 15 | `dow=Wed` | 0.0209 |

---

## NDX.INDX · ml:main_inv
- Toplam çözülmüş: **123**  ·  Baseline win-rate: **56.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.8%** (18 W / 4 L = 22 trade · +25.7pp vs baseline)
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.0%** (6 W / 14 L = 20 trade · -26.1pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack = up`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -22.8pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack ≠ up`
   - `regime_label = transition`
   - `volatility_regime ≠ normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0540 |
| 2 | `session=us` | 0.0467 |
| 3 | `dow=Mon` | 0.0447 |
| 4 | `regime_label=transition` | 0.0424 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0376 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0376 |
| 7 | `session=overlap` | 0.0334 |
| 8 | `rsi_H1=[30,50)` | 0.0312 |
| 9 | `rsi_H1=[50,65)` | 0.0290 |
| 10 | `H4_adx_label=ranging` | 0.0269 |
| 11 | `volatility_regime=high` | 0.0249 |
| 12 | `volatility_regime=normal` | 0.0228 |
| 13 | `H4_adx_label=trending` | 0.0221 |
| 14 | `sar_bearish=False` | 0.0217 |
| 15 | `H4_ema_stack=down` | 0.0213 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **1187**  ·  Baseline win-rate: **36.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 73 L = 73 trade · -36.9pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `H1_ema_stack ≠ mixed`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 0.0%** (0 W / 23 L = 23 trade · -36.9pp vs baseline)
   - `bb_extreme_upper = False`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H4 = [65,75)`
   - `adx_H1 ≠ [18,25)`

**3. Win-rate 2.1%** (1 W / 47 L = 48 trade · -34.8pp vs baseline)
   - `bb_extreme_upper = False`
   - `rsi_H1 = [65,75)`
   - `H4_ema_stack ≠ down`
   - `ml_confidence_bucket = [80,+∞)`

**4. Win-rate 9.7%** (3 W / 28 L = 31 trade · -27.2pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `H1_ema_stack ≠ mixed`
   - `ml_confidence_bucket ≠ [80,+∞)`

**5. Win-rate 15.2%** (5 W / 28 L = 33 trade · -21.7pp vs baseline)
   - `bb_extreme_upper = False`
   - `rsi_H1 = [65,75)`
   - `H4_ema_stack ≠ down`
   - `ml_confidence_bucket ≠ [80,+∞)`

**6. Win-rate 18.5%** (5 W / 22 L = 27 trade · -18.4pp vs baseline)
   - `bb_extreme_upper = False`
   - `rsi_H1 ≠ [65,75)`
   - `rsi_H4 = [65,75)`
   - `adx_H1 = [18,25)`

**7. Win-rate 26.5%** (9 W / 25 L = 34 trade · -10.4pp vs baseline)
   - `bb_extreme_upper ≠ False`
   - `H1_ema_stack = mixed`

**8. Win-rate 29.2%** (7 W / 17 L = 24 trade · -7.7pp vs baseline)
   - `bb_extreme_upper = False`
   - `rsi_H1 = [65,75)`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0417 |
| 2 | `bb_extreme_upper=False` | 0.0391 |
| 3 | `rsi_H1=[65,75)` | 0.0379 |
| 4 | `sar_bearish=False` | 0.0355 |
| 5 | `rsi_H1=[30,50)` | 0.0302 |
| 6 | `sar_bearish=True` | 0.0302 |
| 7 | `H1_adx_label=trending` | 0.0265 |
| 8 | `bb_extreme_upper=True` | 0.0241 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0239 |
| 10 | `macro_alignment=weak_pro` | 0.0206 |
| 11 | `vix_chg1d=[-3,0)` | 0.0203 |
| 12 | `rsi_H4=[30,50)` | 0.0197 |
| 13 | `overbought=False` | 0.0197 |
| 14 | `adx_H1=[35,+∞)` | 0.0190 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0181 |

---

## NDX.INDX · pulse1_inv
- Toplam çözülmüş: **327**  ·  Baseline win-rate: **50.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.2%** (16 W / 5 L = 21 trade · +26.0pp vs baseline)
   - `overbought ≠ True`
   - `dow ≠ Fri`
   - `session_phase = after_hours`
   - `H4_adx_label = ranging`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.1%** (7 W / 22 L = 29 trade · -26.1pp vs baseline)
   - `overbought ≠ True`
   - `dow = Fri`

**2. Win-rate 32.1%** (18 W / 38 L = 56 trade · -18.1pp vs baseline)
   - `overbought ≠ True`
   - `dow ≠ Fri`
   - `session_phase ≠ after_hours`
   - `H1_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `overbought=True` | 0.0368 |
| 2 | `vix_chg1d=[−∞,-3)` | 0.0364 |
| 3 | `session_phase=mid_session` | 0.0356 |
| 4 | `overbought=False` | 0.0342 |
| 5 | `session_phase=after_hours` | 0.0294 |
| 6 | `H4_ema_stack=mixed` | 0.0274 |
| 7 | `adx_H4=[35,+∞)` | 0.0262 |
| 8 | `macro_alignment=neutral` | 0.0247 |
| 9 | `dow=Fri` | 0.0221 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0217 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0199 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0197 |
| 13 | `rsi_H1=[50,65)` | 0.0193 |
| 14 | `rsi_H1=[65,75)` | 0.0191 |
| 15 | `rsi_H4=[50,65)` | 0.0189 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **510**  ·  Baseline win-rate: **46.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 28 L = 28 trade · -46.1pp vs baseline)
   - `bb_extreme_upper = True`
   - `session_phase ≠ after_hours`

**2. Win-rate 3.3%** (1 W / 29 L = 30 trade · -42.8pp vs baseline)
   - `bb_extreme_upper ≠ True`
   - `adx_H1 = [18,25)`
   - `us10y_chg1d = [-0.5,0)`

**3. Win-rate 8.3%** (2 W / 22 L = 24 trade · -37.8pp vs baseline)
   - `bb_extreme_upper ≠ True`
   - `adx_H1 ≠ [18,25)`
   - `rsi_H4 = [65,75)`

**4. Win-rate 17.4%** (4 W / 19 L = 23 trade · -28.7pp vs baseline)
   - `bb_extreme_upper = True`
   - `session_phase = after_hours`

**5. Win-rate 30.0%** (21 W / 49 L = 70 trade · -16.1pp vs baseline)
   - `bb_extreme_upper ≠ True`
   - `adx_H1 = [18,25)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dxy_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0515 |
| 2 | `sar_bearish=True` | 0.0471 |
| 3 | `bb_extreme_upper=True` | 0.0457 |
| 4 | `bb_extreme_upper=False` | 0.0372 |
| 5 | `adx_H1=[18,25)` | 0.0306 |
| 6 | `H1_adx_label=weak_trend` | 0.0301 |
| 7 | `rsi_H1=[30,50)` | 0.0273 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0273 |
| 9 | `H1_adx_label=trending` | 0.0255 |
| 10 | `macro_alignment=weak_pro` | 0.0229 |
| 11 | `mtf_trend=mixed` | 0.0215 |
| 12 | `adx_H1=[25,35)` | 0.0197 |
| 13 | `volatility_regime=high` | 0.0194 |
| 14 | `dow=Mon` | 0.0191 |
| 15 | `H4_ema_stack=up` | 0.0190 |

---

## NDX.INDX · pulse2_inv
- Toplam çözülmüş: **156**  ·  Baseline win-rate: **59.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +26.7pp vs baseline)
   - `bb_extreme_lower = False`
   - `mtf_trend ≠ mixed`
   - `hour_bucket = 16-20`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (7 W / 14 L = 21 trade · -25.7pp vs baseline)
   - `bb_extreme_lower = False`
   - `mtf_trend = mixed`
   - `hour_bucket ≠ 12-16`
   - `dow = Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0466 |
| 2 | `dow=Tue` | 0.0310 |
| 3 | `session=us` | 0.0308 |
| 4 | `hour_bucket=12-16` | 0.0292 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0290 |
| 6 | `rsi_H4=[30,50)` | 0.0273 |
| 7 | `bb_extreme_lower=True` | 0.0269 |
| 8 | `ml_confidence_bucket=[50,60)` | 0.0264 |
| 9 | `rsi_H4=[50,65)` | 0.0257 |
| 10 | `mtf_trend=all_down` | 0.0256 |
| 11 | `session=overlap` | 0.0239 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0237 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0236 |
| 14 | `sar_bearish=False` | 0.0216 |
| 15 | `H1_ema_stack=up` | 0.0205 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **1231**  ·  Baseline win-rate: **43.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.8%** (36 W / 5 L = 41 trade · +43.9pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [−∞,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 78.9%** (30 W / 8 L = 38 trade · +35.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `sar_bearish = True`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 21 L = 21 trade · -43.9pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = weak_pro`
   - `dow = Mon`

**2. Win-rate 10.4%** (27 W / 233 L = 260 trade · -33.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `sar_bearish ≠ True`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 15.6%** (7 W / 38 L = 45 trade · -28.3pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend ≠ mixed`
   - `sar_bearish ≠ True`

**4. Win-rate 25.0%** (7 W / 21 L = 28 trade · -18.9pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = weak_pro`
   - `dow ≠ Mon`

**5. Win-rate 25.9%** (7 W / 20 L = 27 trade · -18.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [−∞,50)`
   - `us10y_chg1d = [−∞,-0.5)`

**6. Win-rate 27.1%** (58 W / 156 L = 214 trade · -16.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `sar_bearish = True`
   - `dow ≠ Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0679 |
| 2 | `sar_bearish=False` | 0.0411 |
| 3 | `sar_bearish=True` | 0.0370 |
| 4 | `adx_H1=[35,+∞)` | 0.0360 |
| 5 | `rsi_H1=[65,75)` | 0.0350 |
| 6 | `adx_H4=[25,35)` | 0.0294 |
| 7 | `macro_alignment=weak_pro` | 0.0281 |
| 8 | `rsi_H4=[30,50)` | 0.0244 |
| 9 | `H1_adx_label=weak_trend` | 0.0213 |
| 10 | `mtf_trend=all_up` | 0.0207 |
| 11 | `H1_ema_stack=up` | 0.0203 |
| 12 | `dow=Fri` | 0.0192 |
| 13 | `mtf_trend=mixed` | 0.0191 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0167 |
| 15 | `macro_alignment=strong_against` | 0.0163 |

---

## NDX.INDX · pulse3_inv
- Toplam çözülmüş: **393**  ·  Baseline win-rate: **55.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +44.5pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack ≠ down`
   - `adx_H1 = [18,25)`
   - `H4_ema_stack = up`

**2. Win-rate 79.6%** (39 W / 10 L = 49 trade · +24.1pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack ≠ down`
   - `adx_H1 = [18,25)`
   - `H4_ema_stack ≠ up`

**3. Win-rate 75.0%** (21 W / 7 L = 28 trade · +19.5pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack ≠ down`
   - `adx_H1 ≠ [18,25)`
   - `ml_confidence_bucket = [50,60)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -47.8pp vs baseline)
   - `dow = Fri`
   - `us10y_chg1d = [-0.5,0)`

**2. Win-rate 19.0%** (4 W / 17 L = 21 trade · -36.5pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack = down`
   - `session ≠ overlap`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0.5,+∞)` | 0.0450 |
| 2 | `H4_ema_stack=down` | 0.0422 |
| 3 | `dow=Fri` | 0.0396 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0350 |
| 5 | `H1_adx_label=weak_trend` | 0.0313 |
| 6 | `rsi_H1=[50,65)` | 0.0293 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0290 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0270 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0239 |
| 10 | `adx_H1=[18,25)` | 0.0234 |
| 11 | `adx_H4=[−∞,18)` | 0.0224 |
| 12 | `H4_adx_label=trending` | 0.0219 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0212 |
| 14 | `regime_label=ranging` | 0.0207 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0201 |

---

## NDX.INDX · smc
- Toplam çözülmüş: **106**  ·  Baseline win-rate: **31.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 24 L = 24 trade · -31.1pp vs baseline)
   - `macro_alignment = weak_pro`

**2. Win-rate 20.7%** (6 W / 23 L = 29 trade · -10.4pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.1135 |
| 2 | `macro_alignment=weak_pro` | 0.0915 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0568 |
| 4 | `dow=Thu` | 0.0513 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0506 |
| 6 | `adx_H4=[35,+∞)` | 0.0434 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0389 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0352 |
| 9 | `sar_bearish=True` | 0.0288 |
| 10 | `session_phase=mid_session` | 0.0226 |
| 11 | `adx_H1=[25,35)` | 0.0200 |
| 12 | `session_phase=after_hours` | 0.0186 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0185 |
| 14 | `mtf_trend=mixed` | 0.0182 |
| 15 | `volatility_regime=high` | 0.0173 |

---

## USOIL.FOREX · ai_panel
- Toplam çözülmüş: **118**  ·  Baseline win-rate: **51.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +36.8pp vs baseline)
   - `M30_ema_stack = down`
   - `macd_atr_M30 ≠ [0,0.3)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +23.3pp vs baseline)
   - `M30_ema_stack = down`
   - `macd_atr_M30 = [0,0.3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.4%** (4 W / 31 L = 35 trade · -40.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0860 |
| 2 | `rsi_H4=[50,65)` | 0.0712 |
| 3 | `rsi_M30=[50,65)` | 0.0505 |
| 4 | `M30_ema_stack=up` | 0.0485 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0482 |
| 6 | `mtf_trend=all_down` | 0.0477 |
| 7 | `H1_ema_stack=down` | 0.0436 |
| 8 | `rsi_H4=[30,50)` | 0.0408 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0350 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0348 |
| 11 | `macro_alignment=neutral` | 0.0321 |
| 12 | `H4_adx_label=weak_trend` | 0.0285 |
| 13 | `H1_ema_stack=up` | 0.0283 |
| 14 | `adx_H4=[18,25)` | 0.0262 |
| 15 | `dist_high_M30=[0.7,1.5)` | 0.0229 |

---

## USOIL.FOREX · emel
- Toplam çözülmüş: **220**  ·  Baseline win-rate: **27.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +55.5pp vs baseline)
   - `H4_ema_stack = mixed`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 48 L = 48 trade · -27.3pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 8.6%** (3 W / 32 L = 35 trade · -18.7pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dxy_chg1d = [-0.5,0)`

**3. Win-rate 19.4%** (7 W / 29 L = 36 trade · -7.9pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label ≠ trending`

**4. Win-rate 25.0%** (5 W / 15 L = 20 trade · -2.3pp vs baseline)
   - `H4_ema_stack = mixed`
   - `session = overlap`

**5. Win-rate 33.3%** (10 W / 20 L = 30 trade · 6.0pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0833 |
| 2 | `mtf_trend=mixed` | 0.0712 |
| 3 | `H4_ema_stack=mixed` | 0.0622 |
| 4 | `rsi_H4=[65,75)` | 0.0321 |
| 5 | `adx_H4=[18,25)` | 0.0290 |
| 6 | `H4_ema_stack=down` | 0.0288 |
| 7 | `H4_adx_label=weak_trend` | 0.0278 |
| 8 | `mtf_trend=all_down` | 0.0253 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0236 |
| 10 | `H1_ema_stack=up` | 0.0210 |
| 11 | `regime_label=transition` | 0.0197 |
| 12 | `adx_H4=[−∞,18)` | 0.0196 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0194 |
| 14 | `dow=Mon` | 0.0190 |
| 15 | `M30_ema_stack=down` | 0.0170 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **832**  ·  Baseline win-rate: **48.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.6%** (44 W / 3 L = 47 trade · +44.9pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_M30 ≠ [30,50)`
   - `H1_adx_label ≠ ranging`
   - `dow = Tue`

**2. Win-rate 93.4%** (228 W / 16 L = 244 trade · +44.7pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_M30 = [30,50)`
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**3. Win-rate 76.1%** (51 W / 16 L = 67 trade · +27.4pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_M30 = [30,50)`
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 175 L = 175 trade · -48.7pp vs baseline)
   - `M30_ema_stack = up`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H4_adx_label ≠ trending`
   - `atr_ratio_M30 ≠ [1,1.3)`

**2. Win-rate 2.7%** (2 W / 71 L = 73 trade · -46.0pp vs baseline)
   - `M30_ema_stack = up`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H4_adx_label ≠ trending`
   - `atr_ratio_M30 = [1,1.3)`

**3. Win-rate 13.1%** (8 W / 53 L = 61 trade · -35.6pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_M30 ≠ [30,50)`
   - `H1_adx_label = ranging`
   - `macd_atr_M30 ≠ [-0.3,0)`

**4. Win-rate 19.2%** (5 W / 21 L = 26 trade · -29.5pp vs baseline)
   - `M30_ema_stack = up`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H4_adx_label = trending`

**5. Win-rate 27.8%** (10 W / 26 L = 36 trade · -20.9pp vs baseline)
   - `M30_ema_stack = up`
   - `bb_pctb_M30 = [−∞,0.2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=up` | 0.1080 |
| 2 | `rsi_H4=[30,50)` | 0.0888 |
| 3 | `rsi_H4=[50,65)` | 0.0756 |
| 4 | `rsi_M30=[30,50)` | 0.0629 |
| 5 | `rsi_H1=[30,50)` | 0.0432 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0413 |
| 7 | `H1_ema_stack=up` | 0.0353 |
| 8 | `M30_ema_stack=down` | 0.0352 |
| 9 | `rsi_H1=[50,65)` | 0.0317 |
| 10 | `mtf_trend=all_down` | 0.0301 |
| 11 | `rsi_M30=[50,65)` | 0.0290 |
| 12 | `mtf_trend=all_up` | 0.0246 |
| 13 | `H1_ema_stack=down` | 0.0204 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0156 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0150 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **734**  ·  Baseline win-rate: **58.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (101 W / 0 L = 101 trade · +41.4pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session ≠ europe`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +36.6pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 89.6%** (69 W / 8 L = 77 trade · +31.0pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 ≠ [18,25)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 86.1%** (62 W / 10 L = 72 trade · +27.5pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`

**5. Win-rate 84.0%** (21 W / 4 L = 25 trade · +25.4pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -58.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -53.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -44.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 27.3%** (21 W / 56 L = 77 trade · -31.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`
   - `vix_chg1d = [0,3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.1111 |
| 2 | `H4_ema_stack=up` | 0.0837 |
| 3 | `mtf_trend=all_up` | 0.0689 |
| 4 | `M30_ema_stack=down` | 0.0470 |
| 5 | `H4_ema_stack=down` | 0.0328 |
| 6 | `mtf_trend=all_down` | 0.0328 |
| 7 | `M30_adx_label=trending` | 0.0285 |
| 8 | `rsi_H4=[50,65)` | 0.0237 |
| 9 | `H4_ema_stack=mixed` | 0.0204 |
| 10 | `dow=Mon` | 0.0173 |
| 11 | `H1_ema_stack=mixed` | 0.0152 |
| 12 | `adx_M30=[35,+∞)` | 0.0151 |
| 13 | `H1_adx_label=ranging` | 0.0148 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0140 |
| 15 | `adx_H1=[−∞,18)` | 0.0136 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **734**  ·  Baseline win-rate: **58.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (101 W / 0 L = 101 trade · +41.6pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session ≠ europe`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +36.8pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 89.6%** (69 W / 8 L = 77 trade · +31.2pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 ≠ [18,25)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 86.1%** (62 W / 10 L = 72 trade · +27.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`

**5. Win-rate 84.0%** (21 W / 4 L = 25 trade · +25.6pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -58.4pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -53.4pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -44.4pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 17.1%** (7 W / 34 L = 41 trade · -41.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`
   - `macro_alignment = strong_against`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.1166 |
| 2 | `H4_ema_stack=up` | 0.0688 |
| 3 | `mtf_trend=all_up` | 0.0620 |
| 4 | `M30_ema_stack=down` | 0.0506 |
| 5 | `H4_ema_stack=down` | 0.0353 |
| 6 | `mtf_trend=all_down` | 0.0310 |
| 7 | `M30_adx_label=trending` | 0.0266 |
| 8 | `dow=Mon` | 0.0250 |
| 9 | `rsi_H4=[50,65)` | 0.0227 |
| 10 | `H4_ema_stack=mixed` | 0.0216 |
| 11 | `adx_H1=[−∞,18)` | 0.0198 |
| 12 | `H1_ema_stack=mixed` | 0.0185 |
| 13 | `adx_M30=[35,+∞)` | 0.0184 |
| 14 | `H1_ema_stack=up` | 0.0176 |
| 15 | `M30_ema_stack=mixed` | 0.0148 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **732**  ·  Baseline win-rate: **58.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (101 W / 0 L = 101 trade · +41.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session ≠ europe`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +36.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 89.6%** (69 W / 8 L = 77 trade · +30.9pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 ≠ [18,25)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 88.9%** (56 W / 7 L = 63 trade · +30.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `dist_low_M30 = [1.5,+∞)`

**5. Win-rate 84.0%** (21 W / 4 L = 25 trade · +25.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -58.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -53.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -44.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 27.3%** (21 W / 56 L = 77 trade · -31.4pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`
   - `vix_chg1d = [0,3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.1267 |
| 2 | `H4_ema_stack=up` | 0.0765 |
| 3 | `mtf_trend=all_up` | 0.0667 |
| 4 | `M30_ema_stack=down` | 0.0499 |
| 5 | `H4_ema_stack=down` | 0.0437 |
| 6 | `mtf_trend=all_down` | 0.0325 |
| 7 | `H4_ema_stack=mixed` | 0.0220 |
| 8 | `rsi_H4=[50,65)` | 0.0213 |
| 9 | `M30_adx_label=trending` | 0.0191 |
| 10 | `adx_M30=[35,+∞)` | 0.0180 |
| 11 | `dow=Mon` | 0.0154 |
| 12 | `M30_ema_stack=mixed` | 0.0145 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0144 |
| 14 | `H1_ema_stack=mixed` | 0.0144 |
| 15 | `dow=Fri` | 0.0139 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **738**  ·  Baseline win-rate: **58.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (101 W / 0 L = 101 trade · +41.9pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session ≠ europe`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +37.1pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 89.7%** (70 W / 8 L = 78 trade · +31.6pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 ≠ [18,25)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 86.1%** (62 W / 10 L = 72 trade · +28.0pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`

**5. Win-rate 84.0%** (21 W / 4 L = 25 trade · +25.9pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -58.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -53.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -44.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 34.3%** (46 W / 88 L = 134 trade · -23.8pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.1366 |
| 2 | `H4_ema_stack=up` | 0.0798 |
| 3 | `mtf_trend=all_up` | 0.0599 |
| 4 | `M30_ema_stack=down` | 0.0477 |
| 5 | `M30_adx_label=trending` | 0.0347 |
| 6 | `H4_ema_stack=down` | 0.0334 |
| 7 | `mtf_trend=all_down` | 0.0262 |
| 8 | `adx_M30=[35,+∞)` | 0.0194 |
| 9 | `H1_adx_label=ranging` | 0.0176 |
| 10 | `dow=Mon` | 0.0176 |
| 11 | `H4_ema_stack=mixed` | 0.0164 |
| 12 | `rsi_H4=[50,65)` | 0.0162 |
| 13 | `adx_H1=[−∞,18)` | 0.0157 |
| 14 | `M30_ema_stack=mixed` | 0.0154 |
| 15 | `H1_ema_stack=mixed` | 0.0147 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **737**  ·  Baseline win-rate: **58.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (101 W / 0 L = 101 trade · +41.8pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session ≠ europe`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +37.0pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 89.7%** (70 W / 8 L = 78 trade · +31.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 ≠ [18,25)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 86.1%** (62 W / 10 L = 72 trade · +27.9pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`

**5. Win-rate 84.0%** (21 W / 4 L = 25 trade · +25.8pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `adx_H4 = [18,25)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -58.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -53.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -44.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 34.3%** (46 W / 88 L = 134 trade · -23.9pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.1293 |
| 2 | `H4_ema_stack=up` | 0.0732 |
| 3 | `mtf_trend=all_up` | 0.0615 |
| 4 | `M30_ema_stack=down` | 0.0481 |
| 5 | `M30_adx_label=trending` | 0.0313 |
| 6 | `mtf_trend=all_down` | 0.0311 |
| 7 | `H4_ema_stack=down` | 0.0309 |
| 8 | `H4_ema_stack=mixed` | 0.0235 |
| 9 | `rsi_H4=[50,65)` | 0.0205 |
| 10 | `adx_M30=[35,+∞)` | 0.0183 |
| 11 | `dow=Mon` | 0.0166 |
| 12 | `H1_ema_stack=up` | 0.0148 |
| 13 | `H1_ema_stack=mixed` | 0.0141 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0138 |
| 15 | `M30_ema_stack=mixed` | 0.0133 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **4173**  ·  Baseline win-rate: **41.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.0%** (96 W / 3 L = 99 trade · +55.8pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 = [35,+∞)`

**2. Win-rate 84.2%** (117 W / 22 L = 139 trade · +43.0pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 ≠ [35,+∞)`

**3. Win-rate 77.2%** (169 W / 50 L = 219 trade · +36.0pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H1_adx_label = ranging`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.0%** (18 W / 340 L = 358 trade · -36.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 9.4%** (6 W / 58 L = 64 trade · -31.8pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `M30_adx_label ≠ weak_trend`

**3. Win-rate 16.7%** (53 W / 264 L = 317 trade · -24.5pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 = [0,2)`
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = strong_against`

**4. Win-rate 17.7%** (23 W / 107 L = 130 trade · -23.5pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `H4_ema_stack ≠ mixed`

**5. Win-rate 24.4%** (98 W / 303 L = 401 trade · -16.8pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**6. Win-rate 34.8%** (8 W / 15 L = 23 trade · -6.4pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label = trending`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0736 |
| 2 | `consec_green_M30=[0,2)` | 0.0697 |
| 3 | `consec_red_M30=[2,4)` | 0.0560 |
| 4 | `consec_green_M30=[2,4)` | 0.0379 |
| 5 | `bb_pctb_M30=[−∞,0.2)` | 0.0287 |
| 6 | `bb_extreme_lower=False` | 0.0242 |
| 7 | `bb_pctb_M30=[0.8,+∞)` | 0.0242 |
| 8 | `macro_alignment=strong_against` | 0.0230 |
| 9 | `adx_H1=[−∞,18)` | 0.0214 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0206 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0193 |
| 12 | `adx_M30=[35,+∞)` | 0.0183 |
| 13 | `bb_extreme_lower=True` | 0.0175 |
| 14 | `macro_alignment=strong_pro` | 0.0153 |
| 15 | `H1_adx_label=ranging` | 0.0152 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **2270**  ·  Baseline win-rate: **43.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +56.2pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 92.8%** (362 W / 28 L = 390 trade · +49.0pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `adx_H4 ≠ [35,+∞)`

**3. Win-rate 84.6%** (44 W / 8 L = 52 trade · +40.8pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 ≠ [50,65)`
   - `dow = Tue`

**4. Win-rate 81.6%** (146 W / 33 L = 179 trade · +37.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 = [30,50)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `adx_M30 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 54 L = 54 trade · -43.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 = [30,50)`
   - `ml_confidence_bucket = [70,80)`
   - `H4_adx_label = weak_trend`

**2. Win-rate 2.5%** (15 W / 580 L = 595 trade · -41.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 ≠ [30,50)`
   - `H4_ema_stack ≠ mixed`
   - `rsi_H1 ≠ [30,50)`

**3. Win-rate 3.0%** (1 W / 32 L = 33 trade · -40.8pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**4. Win-rate 17.9%** (7 W / 32 L = 39 trade · -25.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 ≠ [30,50)`
   - `H4_ema_stack ≠ mixed`
   - `rsi_H1 = [30,50)`

**5. Win-rate 21.7%** (5 W / 18 L = 23 trade · -22.1pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 = [30,50)`
   - `ml_confidence_bucket = [70,80)`
   - `H4_adx_label ≠ weak_trend`

**6. Win-rate 26.9%** (7 W / 19 L = 26 trade · -16.9pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d = [−∞,-0.5)`

**7. Win-rate 32.5%** (80 W / 166 L = 246 trade · -11.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_M30 ≠ [30,50)`
   - `H4_ema_stack = mixed`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0531 |
| 2 | `mtf_trend=all_down` | 0.0528 |
| 3 | `rsi_M30=[30,50)` | 0.0503 |
| 4 | `rsi_H1=[30,50)` | 0.0481 |
| 5 | `rsi_M30=[50,65)` | 0.0382 |
| 6 | `M30_adx_label=trending` | 0.0307 |
| 7 | `rsi_H1=[50,65)` | 0.0296 |
| 8 | `rsi_H4=[30,50)` | 0.0266 |
| 9 | `mtf_trend=all_up` | 0.0248 |
| 10 | `H4_ema_stack=mixed` | 0.0244 |
| 11 | `rsi_H4=[50,65)` | 0.0244 |
| 12 | `dist_high_M30=[1.5,+∞)` | 0.0237 |
| 13 | `mtf_trend=mixed` | 0.0190 |
| 14 | `adx_H4=[18,25)` | 0.0185 |
| 15 | `dow=Mon` | 0.0182 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **3601**  ·  Baseline win-rate: **45.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.2%** (910 W / 122 L = 1032 trade · +42.7pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_H1 ≠ [50,65)`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`

**2. Win-rate 80.6%** (25 W / 6 L = 31 trade · +35.1pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `macd_atr_M30 = [0.3,+∞)`
   - `H4_ema_stack = mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 44 L = 44 trade · -45.5pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `macd_atr_M30 = [0.3,+∞)`
   - `H4_ema_stack ≠ mixed`

**2. Win-rate 7.0%** (65 W / 868 L = 933 trade · -38.5pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `macd_atr_M30 ≠ [0.3,+∞)`
   - `rsi_H1 ≠ [30,50)`

**3. Win-rate 8.8%** (9 W / 93 L = 102 trade · -36.7pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_H1 = [50,65)`
   - `M30_ema_stack = mixed`
   - `M30_adx_label = ranging`

**4. Win-rate 12.3%** (10 W / 71 L = 81 trade · -33.2pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label = trending`
   - `H1_adx_label ≠ trending`
   - `sar_bearish = False`

**5. Win-rate 21.0%** (35 W / 132 L = 167 trade · -24.5pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `macd_atr_M30 ≠ [0.3,+∞)`
   - `rsi_H1 = [30,50)`

**6. Win-rate 25.0%** (5 W / 15 L = 20 trade · -20.5pp vs baseline)
   - `M30_ema_stack = up`
   - `H4_adx_label = trending`
   - `H1_adx_label = trending`
   - `rsi_H1 = [30,50)`

**7. Win-rate 25.4%** (15 W / 44 L = 59 trade · -20.1pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_H1 = [50,65)`
   - `M30_ema_stack ≠ mixed`
   - `session_phase ≠ off_hours`

**8. Win-rate 32.7%** (52 W / 107 L = 159 trade · -12.8pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_H1 ≠ [50,65)`
   - `dow = Mon`
   - `vix_chg1d ≠ [−∞,-3)`

**9. Win-rate 34.6%** (91 W / 172 L = 263 trade · -10.9pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `rsi_H1 = [50,65)`
   - `M30_ema_stack = mixed`
   - `M30_adx_label ≠ ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=up` | 0.0688 |
| 2 | `rsi_H4=[50,65)` | 0.0611 |
| 3 | `rsi_H4=[30,50)` | 0.0526 |
| 4 | `rsi_H1=[30,50)` | 0.0497 |
| 5 | `M30_ema_stack=down` | 0.0462 |
| 6 | `mtf_trend=all_down` | 0.0395 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0352 |
| 8 | `H1_ema_stack=up` | 0.0261 |
| 9 | `rsi_H1=[50,65)` | 0.0224 |
| 10 | `M30_adx_label=trending` | 0.0205 |
| 11 | `dow=Mon` | 0.0198 |
| 12 | `mtf_trend=all_up` | 0.0182 |
| 13 | `H1_ema_stack=down` | 0.0177 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0171 |
| 15 | `rsi_M30=[30,50)` | 0.0159 |

---

## USOIL.FOREX · smc
- Toplam çözülmüş: **597**  ·  Baseline win-rate: **51.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (58 W / 0 L = 58 trade · +48.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`
   - `vix_chg1d = [0,3)`
   - `H4_adx_label ≠ ranging`

**2. Win-rate 100.0%** (42 W / 0 L = 42 trade · +48.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`
   - `vix_chg1d = [0,3)`
   - `H4_adx_label = ranging`

**3. Win-rate 96.3%** (26 W / 1 L = 27 trade · +44.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`
   - `vix_chg1d ≠ [0,3)`
   - `bb_pctb_M30 = [0.2,0.5)`

**4. Win-rate 89.7%** (35 W / 4 L = 39 trade · +37.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 = [50,65)`
   - `session ≠ asia`
   - `us10y_chg1d = [−∞,-0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.9%** (2 W / 49 L = 51 trade · -48.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `hour_bucket ≠ 00-04`
   - `consec_green_M30 ≠ [0,2)`

**2. Win-rate 15.4%** (6 W / 33 L = 39 trade · -36.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 = [50,65)`
   - `session = asia`
   - `us10y_chg1d = [0.5,+∞)`

**3. Win-rate 18.2%** (6 W / 27 L = 33 trade · -33.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`

**4. Win-rate 26.2%** (32 W / 90 L = 122 trade · -25.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `hour_bucket ≠ 00-04`
   - `consec_green_M30 = [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0545 |
| 2 | `mtf_trend=all_down` | 0.0495 |
| 3 | `vix_chg1d=[0,3)` | 0.0460 |
| 4 | `rsi_H1=[50,65)` | 0.0395 |
| 5 | `volatility_regime=high` | 0.0352 |
| 6 | `adx_H1=[−∞,18)` | 0.0328 |
| 7 | `H1_adx_label=ranging` | 0.0310 |
| 8 | `rsi_H1=[30,50)` | 0.0303 |
| 9 | `M30_ema_stack=down` | 0.0270 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0228 |
| 11 | `M30_adx_label=trending` | 0.0227 |
| 12 | `M30_ema_stack=mixed` | 0.0223 |
| 13 | `dist_high_M30=[1.5,+∞)` | 0.0222 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0176 |
| 15 | `dist_low_M30=[0.7,1.5)` | 0.0152 |

---

## XAUUSD · ai_panel
- Toplam çözülmüş: **176**  ·  Baseline win-rate: **67.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +23.7pp vs baseline)
   - `dist_low_M30 = [0.3,0.7)`

**2. Win-rate 87.0%** (20 W / 3 L = 23 trade · +19.4pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `mtf_trend = mixed`
   - `rsi_M30 = [30,50)`

**3. Win-rate 77.8%** (21 W / 6 L = 27 trade · +10.2pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `mtf_trend ≠ mixed`
   - `dow = Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.4%** (7 W / 16 L = 23 trade · -37.2pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `mtf_trend ≠ mixed`
   - `dow ≠ Tue`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_green_M30=[0,2)` | 0.0434 |
| 2 | `H1_adx_label=trending` | 0.0422 |
| 3 | `adx_H1=[18,25)` | 0.0337 |
| 4 | `dist_low_M30=[0.3,0.7)` | 0.0331 |
| 5 | `dow=Tue` | 0.0309 |
| 6 | `M30_ema_stack=mixed` | 0.0307 |
| 7 | `sar_bearish=True` | 0.0304 |
| 8 | `H1_adx_label=weak_trend` | 0.0288 |
| 9 | `rsi_M30=[50,65)` | 0.0282 |
| 10 | `us10y_chg1d=[0,0.5)` | 0.0259 |
| 11 | `adx_M30=[25,35)` | 0.0236 |
| 12 | `mtf_trend=mixed` | 0.0219 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0207 |
| 14 | `near_support=False` | 0.0202 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0182 |

---

## XAUUSD · emel
- Toplam çözülmüş: **246**  ·  Baseline win-rate: **79.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +20.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 = [−∞,0.2)`

**2. Win-rate 100.0%** (33 W / 0 L = 33 trade · +20.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [1,1.3)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 95.0%** (19 W / 1 L = 20 trade · +15.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [1,1.3)`
   - `us10y_chg1d = [0.5,+∞)`

**4. Win-rate 87.5%** (21 W / 3 L = 24 trade · +7.8pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**5. Win-rate 82.6%** (19 W / 4 L = 23 trade · +2.9pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment ≠ weak_against`
   - `atr_ratio_M30 ≠ [0.7,1)`

**6. Win-rate 81.8%** (27 W / 6 L = 33 trade · +2.1pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -44.7pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend ≠ all_down`
   - `M30_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0629 |
| 2 | `dxy_chg1d=[-0.5,0)` | 0.0544 |
| 3 | `macro_alignment=weak_against` | 0.0509 |
| 4 | `adx_H1=[35,+∞)` | 0.0453 |
| 5 | `adx_M30=[35,+∞)` | 0.0393 |
| 6 | `M30_ema_stack=down` | 0.0373 |
| 7 | `mtf_trend=all_down` | 0.0347 |
| 8 | `dist_low_M30=[1.5,+∞)` | 0.0308 |
| 9 | `atr_ratio_M30=[1,1.3)` | 0.0240 |
| 10 | `atr_ratio_M30=[0.7,1)` | 0.0218 |
| 11 | `rsi_H1=[30,50)` | 0.0206 |
| 12 | `consec_red_M30=[2,4)` | 0.0194 |
| 13 | `rsi_M30=[50,65)` | 0.0190 |
| 14 | `rsi_M30=[30,50)` | 0.0185 |
| 15 | `rsi_H1=[50,65)` | 0.0184 |

---

## XAUUSD · emel_inv
- Toplam çözülmüş: **119**  ·  Baseline win-rate: **27.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 28 L = 28 trade · -27.7pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 = [1,1.3)`

**2. Win-rate 14.3%** (3 W / 18 L = 21 trade · -13.4pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_pro`

**3. Win-rate 30.8%** (8 W / 18 L = 26 trade · 3.1pp vs baseline)
   - `dxy_chg1d ≠ [0,0.5)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**4. Win-rate 34.8%** (8 W / 15 L = 23 trade · 7.1pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment ≠ weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0697 |
| 2 | `dxy_chg1d=[0,0.5)` | 0.0692 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0662 |
| 4 | `adx_H1=[35,+∞)` | 0.0626 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0473 |
| 6 | `adx_H1=[18,25)` | 0.0463 |
| 7 | `macro_alignment=weak_pro` | 0.0348 |
| 8 | `bb_pctb_M30=[0.5,0.8)` | 0.0335 |
| 9 | `H1_adx_label=trending` | 0.0329 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0241 |
| 11 | `rsi_H1=[50,65)` | 0.0205 |
| 12 | `H1_adx_label=weak_trend` | 0.0202 |
| 13 | `adx_M30=[25,35)` | 0.0195 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0181 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0172 |

---

## XAUUSD · meta
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **62.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +32.3pp vs baseline)
   - `session ≠ asia`
   - `bb_pctb_M30 = [0.5,0.8)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.0795 |
| 2 | `M30_adx_label=ranging` | 0.0784 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0580 |
| 4 | `adx_M30=[−∞,18)` | 0.0565 |
| 5 | `dist_low_M30=[1.5,+∞)` | 0.0440 |
| 6 | `sar_bearish=True` | 0.0400 |
| 7 | `vix_chg1d=[0,3)` | 0.0350 |
| 8 | `macd_atr_M30=[0,0.3)` | 0.0329 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0329 |
| 10 | `macd_atr_M30=[-0.3,0)` | 0.0327 |
| 11 | `sar_bearish=False` | 0.0301 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0297 |
| 13 | `M30_adx_label=trending` | 0.0273 |
| 14 | `macro_alignment=weak_against` | 0.0267 |
| 15 | `ml_confidence_bucket=[70,80)` | 0.0267 |

---

## XAUUSD · ml:aggressive
- Toplam çözülmüş: **520**  ·  Baseline win-rate: **50.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +32.4pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `us10y_chg1d = [−∞,-0.5)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +24.6pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dist_high_M30 = [0.3,0.7)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -42.7pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**2. Win-rate 25.9%** (7 W / 20 L = 27 trade · -24.5pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `mtf_trend ≠ mixed`
   - `H1_adx_label = trending`

**3. Win-rate 30.0%** (6 W / 14 L = 20 trade · -20.4pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0385 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0340 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0316 |
| 4 | `bb_pctb_M30=[−∞,0.2)` | 0.0295 |
| 5 | `macro_alignment=strong_pro` | 0.0197 |
| 6 | `consec_red_M30=[2,4)` | 0.0187 |
| 7 | `macro_alignment=weak_against` | 0.0178 |
| 8 | `H1_adx_label=trending` | 0.0176 |
| 9 | `consec_green_M30=[0,2)` | 0.0167 |
| 10 | `adx_H1=[35,+∞)` | 0.0167 |
| 11 | `rsi_M30=[50,65)` | 0.0151 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0147 |
| 13 | `rsi_M30=[30,50)` | 0.0145 |
| 14 | `us10y_chg1d=[0,0.5)` | 0.0145 |
| 15 | `consec_red_M30=[0,2)` | 0.0144 |

---

## XAUUSD · ml:balanced
- Toplam çözülmüş: **526**  ·  Baseline win-rate: **49.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.0%** (21 W / 4 L = 25 trade · +34.4pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 80.0%** (16 W / 4 L = 20 trade · +30.4pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dist_high_M30 = [0.3,0.7)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -41.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `adx_M30 = [35,+∞)`

**2. Win-rate 22.2%** (6 W / 21 L = 27 trade · -27.4pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ mixed`
   - `H1_adx_label = trending`

**3. Win-rate 30.0%** (6 W / 14 L = 20 trade · -19.6pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0420 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0328 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0299 |
| 4 | `bb_pctb_M30=[−∞,0.2)` | 0.0299 |
| 5 | `macro_alignment=weak_against` | 0.0211 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0194 |
| 7 | `consec_green_M30=[0,2)` | 0.0192 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0172 |
| 9 | `H1_adx_label=trending` | 0.0171 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0167 |
| 11 | `session=asia` | 0.0167 |
| 12 | `adx_M30=[35,+∞)` | 0.0162 |
| 13 | `rsi_M30=[30,50)` | 0.0156 |
| 14 | `consec_red_M30=[2,4)` | 0.0153 |
| 15 | `rsi_H1=[30,50)` | 0.0152 |

---

## XAUUSD · ml:full_power
- Toplam çözülmüş: **516**  ·  Baseline win-rate: **49.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.3%** (20 W / 4 L = 24 trade · +33.9pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +25.6pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dist_high_M30 = [0.3,0.7)`

**3. Win-rate 75.0%** (18 W / 6 L = 24 trade · +25.6pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -41.7pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**2. Win-rate 25.9%** (7 W / 20 L = 27 trade · -23.5pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ mixed`
   - `H1_adx_label = trending`

**3. Win-rate 30.0%** (6 W / 14 L = 20 trade · -19.4pp vs baseline)
   - `macro_alignment = weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0357 |
| 2 | `bb_pctb_M30=[−∞,0.2)` | 0.0311 |
| 3 | `macro_alignment=weak_pro` | 0.0271 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0254 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0206 |
| 6 | `consec_red_M30=[2,4)` | 0.0199 |
| 7 | `H1_adx_label=trending` | 0.0182 |
| 8 | `consec_green_M30=[0,2)` | 0.0179 |
| 9 | `adx_H1=[35,+∞)` | 0.0177 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0173 |
| 11 | `adx_M30=[35,+∞)` | 0.0173 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0172 |
| 13 | `rsi_M30=[50,65)` | 0.0160 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0149 |
| 15 | `vix_chg1d=[-3,0)` | 0.0142 |

---

## XAUUSD · ml:main
- Toplam çözülmüş: **517**  ·  Baseline win-rate: **50.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +32.7pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `macro_alignment ≠ weak_pro`
   - `us10y_chg1d = [−∞,-0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.1%** (3 W / 24 L = 27 trade · -39.0pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 27.6%** (8 W / 21 L = 29 trade · -22.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 30.0%** (9 W / 21 L = 30 trade · -20.1pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `consec_green_M30 ≠ [0,2)`
   - `rsi_M30 = [50,65)`

**4. Win-rate 32.1%** (9 W / 19 L = 28 trade · -18.0pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 = [0.7,1)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0469 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0331 |
| 3 | `macro_alignment=weak_pro` | 0.0313 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0257 |
| 5 | `macro_alignment=weak_against` | 0.0230 |
| 6 | `consec_green_M30=[0,2)` | 0.0191 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0185 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0179 |
| 9 | `adx_M30=[35,+∞)` | 0.0166 |
| 10 | `H1_adx_label=trending` | 0.0165 |
| 11 | `macro_alignment=strong_pro` | 0.0160 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0152 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0150 |
| 14 | `rsi_M30=[50,65)` | 0.0149 |
| 15 | `macd_atr_M30=[0,0.3)` | 0.0149 |

---

## XAUUSD · ml:main_inv
- Toplam çözülmüş: **234**  ·  Baseline win-rate: **48.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (24 W / 4 L = 28 trade · +37.4pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment ≠ weak_pro`
   - `session = asia`
   - `atr_ratio_M30 = [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -28.3pp vs baseline)
   - `consec_red_M30 = [2,4)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -15.0pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment = weak_pro`
   - `rsi_M30 ≠ [30,50)`

**3. Win-rate 34.6%** (9 W / 17 L = 26 trade · -13.7pp vs baseline)
   - `consec_red_M30 = [2,4)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[2,4)` | 0.0606 |
| 2 | `consec_red_M30=[0,2)` | 0.0522 |
| 3 | `macro_alignment=weak_pro` | 0.0359 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0298 |
| 5 | `bb_extreme_lower=True` | 0.0279 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0225 |
| 7 | `adx_H1=[35,+∞)` | 0.0222 |
| 8 | `adx_M30=[35,+∞)` | 0.0220 |
| 9 | `session=asia` | 0.0218 |
| 10 | `bb_pctb_M30=[−∞,0.2)` | 0.0210 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0202 |
| 12 | `mtf_trend=all_up` | 0.0195 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0194 |
| 14 | `H1_adx_label=trending` | 0.0193 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0192 |

---

## XAUUSD · ml:ultra_safe
- Toplam çözülmüş: **518**  ·  Baseline win-rate: **49.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (18 W / 2 L = 20 trade · +40.2pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `rsi_H1 = [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.8%** (4 W / 23 L = 27 trade · -35.0pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `us10y_chg1d = [0,0.5)`

**2. Win-rate 22.5%** (9 W / 31 L = 40 trade · -27.3pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dist_high_M30 = [1.5,+∞)`

**3. Win-rate 27.3%** (6 W / 16 L = 22 trade · -22.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [60,70)`
   - `vix_chg1d = [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0424 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0322 |
| 3 | `macro_alignment=weak_pro` | 0.0301 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0243 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0233 |
| 6 | `consec_red_M30=[2,4)` | 0.0195 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0193 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0192 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0188 |
| 10 | `adx_M30=[35,+∞)` | 0.0184 |
| 11 | `consec_green_M30=[0,2)` | 0.0171 |
| 12 | `sar_bearish=True` | 0.0167 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0154 |
| 14 | `macro_alignment=weak_against` | 0.0153 |
| 15 | `H1_adx_label=trending` | 0.0150 |

---

## XAUUSD · ml_cross_xau_nasdaq
- Toplam çözülmüş: **727**  ·  Baseline win-rate: **42.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.6%** (70 W / 1 L = 71 trade · +56.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 67 L = 67 trade · -42.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 9.5%** (2 W / 19 L = 21 trade · -32.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `consec_red_M30 = [2,4)`

**3. Win-rate 12.5%** (3 W / 21 L = 24 trade · -29.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `hour_bucket = 16-20`

**4. Win-rate 16.5%** (14 W / 71 L = 85 trade · -25.6pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow ≠ Mon`

**5. Win-rate 23.7%** (9 W / 29 L = 38 trade · -18.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 = [1.5,+∞)`
   - `macro_alignment = weak_pro`

**6. Win-rate 28.6%** (8 W / 20 L = 28 trade · -13.5pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 = [1.5,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `H1_adx_label ≠ trending`

**7. Win-rate 32.2%** (29 W / 61 L = 90 trade · -9.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `consec_red_M30 ≠ [2,4)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0711 |
| 2 | `M30_ema_stack=down` | 0.0588 |
| 3 | `adx_M30=[35,+∞)` | 0.0471 |
| 4 | `macro_alignment=weak_pro` | 0.0439 |
| 5 | `dist_high_M30=[1.5,+∞)` | 0.0426 |
| 6 | `dxy_chg1d=[0.5,+∞)` | 0.0418 |
| 7 | `macro_alignment=weak_against` | 0.0399 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0293 |
| 9 | `M30_ema_stack=NA` | 0.0254 |
| 10 | `mtf_trend=NA` | 0.0252 |
| 11 | `H1_adx_label=ranging` | 0.0233 |
| 12 | `adx_H1=[−∞,18)` | 0.0224 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0206 |
| 14 | `ml_confidence_bucket=[80,+∞)` | 0.0183 |
| 15 | `dow=Mon` | 0.0162 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv
- Toplam çözülmüş: **517**  ·  Baseline win-rate: **27.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 53 L = 53 trade · -27.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `dxy_chg1d = [0,0.5)`
   - `hour_bucket ≠ 12-16`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -22.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `dxy_chg1d = [0,0.5)`
   - `hour_bucket ≠ 12-16`
   - `bb_pctb_M30 = [−∞,0.2)`

**3. Win-rate 17.7%** (25 W / 116 L = 141 trade · -10.2pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `M30_ema_stack ≠ down`
   - `volatility_regime = normal`
   - `M30_adx_label = trending`

**4. Win-rate 24.1%** (7 W / 22 L = 29 trade · -3.8pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `M30_ema_stack = down`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 25.0%** (5 W / 15 L = 20 trade · -2.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `dxy_chg1d = [0,0.5)`
   - `hour_bucket = 12-16`

**6. Win-rate 31.2%** (25 W / 55 L = 80 trade · 3.3pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `M30_ema_stack ≠ down`
   - `volatility_regime = normal`
   - `M30_adx_label ≠ trending`

**7. Win-rate 32.0%** (8 W / 17 L = 25 trade · 4.1pp vs baseline)
   - `macro_alignment = weak_pro`
   - `dxy_chg1d ≠ [0,0.5)`

**8. Win-rate 34.6%** (9 W / 17 L = 26 trade · 6.7pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `M30_ema_stack = down`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dist_high_M30 ≠ [1.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0565 |
| 2 | `M30_ema_stack=down` | 0.0544 |
| 3 | `mtf_trend=all_down` | 0.0541 |
| 4 | `dist_high_M30=[1.5,+∞)` | 0.0415 |
| 5 | `mtf_trend=NA` | 0.0273 |
| 6 | `M30_ema_stack=NA` | 0.0224 |
| 7 | `dow=Mon` | 0.0206 |
| 8 | `dist_high_M30=[0.3,0.7)` | 0.0188 |
| 9 | `rsi_M30=[50,65)` | 0.0179 |
| 10 | `macro_alignment=weak_against` | 0.0174 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0170 |
| 12 | `adx_M30=[35,+∞)` | 0.0166 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0151 |
| 14 | `sar_bearish=False` | 0.0150 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0145 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **3229**  ·  Baseline win-rate: **24.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 63 L = 63 trade · -24.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `M30_ema_stack = NA`
   - `macro_alignment = weak_pro`

**2. Win-rate 0.0%** (0 W / 46 L = 46 trade · -24.5pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dxy_chg1d = [0.5,+∞)`

**3. Win-rate 0.0%** (0 W / 75 L = 75 trade · -24.5pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `us10y_chg1d = [-0.5,0)`
   - `M30_adx_label ≠ trending`

**4. Win-rate 0.0%** (0 W / 32 L = 32 trade · -24.5pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label = weak_trend`
   - `dow = Mon`
   - `session ≠ asia`

**5. Win-rate 5.2%** (3 W / 55 L = 58 trade · -19.3pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `us10y_chg1d = [-0.5,0)`
   - `M30_adx_label = trending`

**6. Win-rate 5.3%** (3 W / 54 L = 57 trade · -19.2pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label = weak_trend`
   - `dow ≠ Mon`
   - `dow = Fri`

**7. Win-rate 5.9%** (6 W / 95 L = 101 trade · -18.6pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `M30_ema_stack = NA`
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 = [1.5,+∞)`

**8. Win-rate 9.1%** (2 W / 20 L = 22 trade · -15.4pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label = weak_trend`
   - `dow = Mon`
   - `session = asia`

**9. Win-rate 13.1%** (56 W / 370 L = 426 trade · -11.4pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dxy_chg1d ≠ [0.5,+∞)`

**10. Win-rate 15.0%** (71 W / 403 L = 474 trade · -9.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `M30_ema_stack ≠ NA`
   - `vix_chg1d = [3,+∞)`
   - `consec_green_M30 ≠ [2,4)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0307 |
| 2 | `mtf_trend=NA` | 0.0304 |
| 3 | `bb_pctb_M30=[−∞,0.2)` | 0.0300 |
| 4 | `M30_ema_stack=NA` | 0.0274 |
| 5 | `adx_M30=[35,+∞)` | 0.0260 |
| 6 | `dxy_chg1d=[0.5,+∞)` | 0.0222 |
| 7 | `dow=Fri` | 0.0186 |
| 8 | `sar_bearish=True` | 0.0183 |
| 9 | `dow=Tue` | 0.0169 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0169 |
| 11 | `consec_red_M30=[0,2)` | 0.0168 |
| 12 | `sar_bearish=False` | 0.0162 |
| 13 | `vix_chg1d=[0,3)` | 0.0150 |
| 14 | `bb_extreme_lower=True` | 0.0148 |
| 15 | `bb_extreme_lower=False` | 0.0145 |

---

## XAUUSD · pulse1_inv
- Toplam çözülmüş: **761**  ·  Baseline win-rate: **49.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.6%** (146 W / 33 L = 179 trade · +32.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment ≠ weak_pro`
   - `macro_alignment ≠ strong_against`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.8%** (1 W / 20 L = 21 trade · -44.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`
   - `us10y_chg1d ≠ [0.5,+∞)`

**2. Win-rate 15.4%** (4 W / 22 L = 26 trade · -33.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `atr_ratio_M30 = [0.7,1)`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 21.4%** (6 W / 22 L = 28 trade · -27.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`
   - `us10y_chg1d = [0.5,+∞)`

**4. Win-rate 21.6%** (8 W / 29 L = 37 trade · -27.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**5. Win-rate 22.2%** (6 W / 21 L = 27 trade · -26.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `ml_confidence_bucket = [−∞,50)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -17.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment = weak_pro`

**7. Win-rate 34.8%** (49 W / 92 L = 141 trade · -14.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `atr_ratio_M30 = [0.7,1)`
   - `ml_confidence_bucket ≠ [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0908 |
| 2 | `adx_H1=[35,+∞)` | 0.0477 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0457 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0449 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0398 |
| 6 | `M30_adx_label=trending` | 0.0373 |
| 7 | `dist_high_M30=[1.5,+∞)` | 0.0244 |
| 8 | `macro_alignment=weak_against` | 0.0238 |
| 9 | `macro_alignment=weak_pro` | 0.0223 |
| 10 | `adx_M30=[18,25)` | 0.0180 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0175 |
| 12 | `adx_M30=[25,35)` | 0.0174 |
| 13 | `macro_alignment=neutral` | 0.0146 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0140 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0137 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **2766**  ·  Baseline win-rate: **27.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 82 L = 82 trade · -27.7pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ NA`
   - `dxy_chg1d = [0.5,+∞)`
   - `hour_bucket ≠ 16-20`

**2. Win-rate 0.0%** (0 W / 53 L = 53 trade · -27.7pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = NA`
   - `dow = Mon`

**3. Win-rate 4.4%** (7 W / 152 L = 159 trade · -23.3pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 ≠ [25,35)`
   - `bb_pctb_M30 = [−∞,0.2)`

**4. Win-rate 5.0%** (1 W / 19 L = 20 trade · -22.7pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ NA`
   - `dxy_chg1d = [0.5,+∞)`
   - `hour_bucket = 16-20`

**5. Win-rate 5.3%** (4 W / 72 L = 76 trade · -22.4pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = NA`
   - `dow ≠ Mon`
   - `sar_bearish ≠ False`

**6. Win-rate 12.3%** (51 W / 364 L = 415 trade · -15.4pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 ≠ [25,35)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**7. Win-rate 16.1%** (15 W / 78 L = 93 trade · -11.6pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 = [25,35)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**8. Win-rate 16.9%** (21 W / 103 L = 124 trade · -10.8pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 = [18,25)`
   - `hour_bucket ≠ 20-24`
   - `macro_alignment ≠ strong_pro`

**9. Win-rate 17.4%** (64 W / 303 L = 367 trade · -10.3pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ NA`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow = Wed`

**10. Win-rate 18.8%** (9 W / 39 L = 48 trade · -8.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = NA`
   - `dow ≠ Mon`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0591 |
| 2 | `dow=Wed` | 0.0403 |
| 3 | `M30_ema_stack=NA` | 0.0299 |
| 4 | `dow=Fri` | 0.0286 |
| 5 | `adx_M30=[35,+∞)` | 0.0275 |
| 6 | `mtf_trend=NA` | 0.0240 |
| 7 | `dxy_chg1d=[0.5,+∞)` | 0.0224 |
| 8 | `M30_adx_label=trending` | 0.0200 |
| 9 | `dow=Tue` | 0.0199 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0185 |
| 11 | `vix_chg1d=[0,3)` | 0.0181 |
| 12 | `bb_pctb_M30=[−∞,0.2)` | 0.0179 |
| 13 | `M30_ema_stack=mixed` | 0.0173 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0171 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0170 |

---

## XAUUSD · pulse2_inv
- Toplam çözülmüş: **740**  ·  Baseline win-rate: **45.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.3%** (42 W / 3 L = 45 trade · +47.5pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 ≠ [25,35)`
   - `dxy_chg1d = [0,0.5)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 78.4%** (40 W / 11 L = 51 trade · +32.6pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 ≠ [25,35)`
   - `dxy_chg1d = [0,0.5)`
   - `dist_high_M30 = [1.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.6%** (5 W / 53 L = 58 trade · -37.2pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 20.0%** (5 W / 20 L = 25 trade · -25.8pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_H1 ≠ [35,+∞)`

**3. Win-rate 27.9%** (12 W / 31 L = 43 trade · -17.9pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ weak_pro`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment = strong_against`

**4. Win-rate 28.6%** (8 W / 20 L = 28 trade · -17.2pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 = [25,35)`

**5. Win-rate 31.8%** (7 W / 15 L = 22 trade · -14.0pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `dxy_chg1d ≠ [0,0.5)`

**6. Win-rate 32.2%** (58 W / 122 L = 180 trade · -13.6pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ weak_pro`
   - `adx_M30 ≠ [35,+∞)`
   - `dxy_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0809 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0597 |
| 3 | `macro_alignment=weak_pro` | 0.0567 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0516 |
| 5 | `adx_M30=[35,+∞)` | 0.0434 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0279 |
| 7 | `adx_H1=[35,+∞)` | 0.0245 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0235 |
| 9 | `macro_alignment=strong_against` | 0.0201 |
| 10 | `M30_adx_label=weak_trend` | 0.0161 |
| 11 | `mtf_trend=NA` | 0.0150 |
| 12 | `adx_M30=[18,25)` | 0.0141 |
| 13 | `M30_ema_stack=NA` | 0.0138 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0133 |
| 15 | `M30_adx_label=trending` | 0.0133 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **3158**  ·  Baseline win-rate: **28.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.3%** (148 W / 41 L = 189 trade · +49.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ down`
   - `M30_ema_stack ≠ NA`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.1%** (11 W / 256 L = 267 trade · -24.3pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `vix_chg1d ≠ [0,3)`

**2. Win-rate 5.8%** (25 W / 403 L = 428 trade · -22.6pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Mon`
   - `dow ≠ Sun`
   - `dist_high_M30 = [1.5,+∞)`

**3. Win-rate 6.5%** (8 W / 116 L = 124 trade · -21.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ down`
   - `M30_ema_stack = NA`
   - `sar_bearish ≠ False`

**4. Win-rate 9.1%** (13 W / 130 L = 143 trade · -19.3pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dow = Mon`
   - `adx_H1 = [35,+∞)`
   - `rsi_M30 ≠ [50,65)`

**5. Win-rate 15.4%** (35 W / 192 L = 227 trade · -13.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = down`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `us10y_chg1d = [-0.5,0)`

**6. Win-rate 17.5%** (37 W / 175 L = 212 trade · -10.9pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Mon`
   - `dow ≠ Sun`
   - `dist_high_M30 ≠ [1.5,+∞)`

**7. Win-rate 22.4%** (28 W / 97 L = 125 trade · -6.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `vix_chg1d = [0,3)`

**8. Win-rate 26.7%** (24 W / 66 L = 90 trade · -1.7pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dow = Mon`
   - `adx_H1 ≠ [35,+∞)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**9. Win-rate 29.0%** (9 W / 22 L = 31 trade · 0.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_ema_stack ≠ down`
   - `M30_ema_stack = NA`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0638 |
| 2 | `rsi_H1=[50,65)` | 0.0313 |
| 3 | `bb_pctb_M30=[−∞,0.2)` | 0.0240 |
| 4 | `M30_ema_stack=down` | 0.0233 |
| 5 | `dow=Fri` | 0.0228 |
| 6 | `bb_extreme_lower=False` | 0.0215 |
| 7 | `M30_ema_stack=up` | 0.0206 |
| 8 | `mtf_trend=all_down` | 0.0204 |
| 9 | `oversold=False` | 0.0187 |
| 10 | `dow=Wed` | 0.0187 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0182 |
| 12 | `rsi_M30=[30,50)` | 0.0172 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0167 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0159 |
| 15 | `M30_ema_stack=NA` | 0.0154 |

---

## XAUUSD · pulse3_inv
- Toplam çözülmüş: **726**  ·  Baseline win-rate: **41.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.7%** (115 W / 37 L = 152 trade · +34.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dxy_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.3%** (9 W / 99 L = 108 trade · -33.3pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime = normal`
   - `bb_extreme_upper ≠ True`
   - `H1_adx_label ≠ weak_trend`

**2. Win-rate 17.9%** (7 W / 32 L = 39 trade · -23.7pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**3. Win-rate 23.5%** (8 W / 26 L = 34 trade · -18.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket = 20-24`

**4. Win-rate 24.2%** (8 W / 25 L = 33 trade · -17.4pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime = normal`
   - `bb_extreme_upper ≠ True`
   - `H1_adx_label = weak_trend`

**5. Win-rate 33.3%** (10 W / 20 L = 30 trade · -8.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment = weak_pro`

**6. Win-rate 33.3%** (11 W / 22 L = 33 trade · -8.3pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime = normal`
   - `bb_extreme_upper = True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0773 |
| 2 | `sar_bearish=True` | 0.0661 |
| 3 | `macro_alignment=weak_pro` | 0.0527 |
| 4 | `adx_M30=[35,+∞)` | 0.0400 |
| 5 | `macro_alignment=weak_against` | 0.0372 |
| 6 | `adx_H1=[35,+∞)` | 0.0323 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0288 |
| 8 | `rsi_H1=[50,65)` | 0.0275 |
| 9 | `adx_H1=[25,35)` | 0.0232 |
| 10 | `rsi_M30=[30,50)` | 0.0230 |
| 11 | `rsi_M30=[50,65)` | 0.0218 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0212 |
| 13 | `adx_M30=[25,35)` | 0.0209 |
| 14 | `rsi_H1=[30,50)` | 0.0205 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0181 |

---

## XAUUSD · smc
- Toplam çözülmüş: **676**  ·  Baseline win-rate: **49.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +50.9pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**2. Win-rate 90.5%** (19 W / 2 L = 21 trade · +41.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `atr_ratio_M30 = [1,1.3)`

**3. Win-rate 85.2%** (23 W / 4 L = 27 trade · +36.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `us10y_chg1d = [0,0.5)`
   - `macro_alignment = weak_against`

**4. Win-rate 82.5%** (47 W / 10 L = 57 trade · +33.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `H1_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 19.0%** (33 W / 141 L = 174 trade · -30.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `vix_chg1d ≠ [0,3)`

**2. Win-rate 32.4%** (12 W / 25 L = 37 trade · -16.7pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 ≠ [1.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0603 |
| 2 | `mtf_trend=all_down` | 0.0373 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0368 |
| 4 | `M30_ema_stack=down` | 0.0358 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0354 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0347 |
| 7 | `bb_pctb_M30=[0.2,0.5)` | 0.0258 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0222 |
| 9 | `us10y_chg1d=[0,0.5)` | 0.0203 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0198 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0182 |
| 12 | `macro_alignment=strong_pro` | 0.0182 |
| 13 | `vix_chg1d=[-3,0)` | 0.0164 |
| 14 | `volatility_regime=low` | 0.0148 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0146 |

---

## XAUUSD · smc_inv
- Toplam çözülmüş: **193**  ·  Baseline win-rate: **48.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.0%** (19 W / 1 L = 20 trade · +46.3pp vs baseline)
   - `dow ≠ Tue`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `mtf_trend = all_up`

**2. Win-rate 77.3%** (17 W / 5 L = 22 trade · +28.6pp vs baseline)
   - `dow ≠ Tue`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `mtf_trend ≠ all_up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.0%** (3 W / 20 L = 23 trade · -35.7pp vs baseline)
   - `dow = Tue`
   - `rsi_H1 = [50,65)`

**2. Win-rate 17.4%** (4 W / 19 L = 23 trade · -31.3pp vs baseline)
   - `dow ≠ Tue`
   - `dist_high_M30 = [1.5,+∞)`
   - `H1_adx_label = trending`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_high_M30=[1.5,+∞)` | 0.0975 |
| 2 | `dow=Tue` | 0.0594 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0569 |
| 4 | `mtf_trend=mixed` | 0.0374 |
| 5 | `macro_alignment=weak_against` | 0.0363 |
| 6 | `vix_chg1d=[0,3)` | 0.0300 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0295 |
| 8 | `atr_ratio_M30=[0.7,1)` | 0.0238 |
| 9 | `M30_ema_stack=mixed` | 0.0225 |
| 10 | `adx_M30=[35,+∞)` | 0.0224 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0197 |
| 12 | `H1_adx_label=trending` | 0.0193 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0190 |
| 14 | `hour_bucket=16-20` | 0.0183 |
| 15 | `dow=Wed` | 0.0178 |

---

## GDAXI.INDX · ai_panel · BUY
- Toplam çözülmüş: **97**  ·  Baseline win-rate: **51.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.5%** (31 W / 8 L = 39 trade · +28.0pp vs baseline)
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.9%** (5 W / 23 L = 28 trade · -33.6pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `H4_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.1303 |
| 2 | `rsi_H1=[50,65)` | 0.0986 |
| 3 | `sar_bearish=True` | 0.0707 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0628 |
| 5 | `sar_bearish=False` | 0.0570 |
| 6 | `H4_ema_stack=up` | 0.0465 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0419 |
| 8 | `us10y_chg1d=[-0.5,0)` | 0.0311 |
| 9 | `H1_ema_stack=mixed` | 0.0282 |
| 10 | `volatility_regime=high` | 0.0277 |
| 11 | `H1_ema_stack=down` | 0.0245 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0242 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0215 |
| 14 | `dow=Mon` | 0.0193 |
| 15 | `bb_extreme_lower=True` | 0.0183 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **352**  ·  Baseline win-rate: **40.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +51.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 = [30,50)`
   - `vix_chg1d = [0,3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 45 L = 45 trade · -40.3pp vs baseline)
   - `sar_bearish = False`
   - `dow ≠ Fri`
   - `adx_H4 ≠ NA`
   - `bb_extreme_upper ≠ False`

**2. Win-rate 21.6%** (21 W / 76 L = 97 trade · -18.7pp vs baseline)
   - `sar_bearish = False`
   - `dow ≠ Fri`
   - `adx_H4 ≠ NA`
   - `bb_extreme_upper = False`

**3. Win-rate 33.3%** (7 W / 14 L = 21 trade · -7.0pp vs baseline)
   - `sar_bearish = False`
   - `dow = Fri`
   - `rsi_H4 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1173 |
| 2 | `sar_bearish=True` | 0.0910 |
| 3 | `rsi_H1=[30,50)` | 0.0536 |
| 4 | `bb_extreme_lower=False` | 0.0310 |
| 5 | `dow=Mon` | 0.0258 |
| 6 | `overbought=False` | 0.0233 |
| 7 | `bb_extreme_upper=False` | 0.0229 |
| 8 | `volatility_regime=normal` | 0.0219 |
| 9 | `overbought=True` | 0.0213 |
| 10 | `adx_H1=[18,25)` | 0.0212 |
| 11 | `bb_extreme_upper=True` | 0.0201 |
| 12 | `bb_extreme_lower=True` | 0.0191 |
| 13 | `H1_adx_label=weak_trend` | 0.0181 |
| 14 | `H4_adx_label=weak_trend` | 0.0163 |
| 15 | `macro_alignment=neutral` | 0.0146 |

---

## GDAXI.INDX · meta · SELL
- Toplam çözülmüş: **126**  ·  Baseline win-rate: **53.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.8%** (28 W / 5 L = 33 trade · +31.6pp vs baseline)
   - `H1_adx_label = trending`
   - `regime_label ≠ transition`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.7%** (6 W / 23 L = 29 trade · -32.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_adx_label ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0822 |
| 2 | `adx_H1=[18,25)` | 0.0665 |
| 3 | `H1_adx_label=weak_trend` | 0.0637 |
| 4 | `dow=Mon` | 0.0533 |
| 5 | `adx_H1=[25,35)` | 0.0406 |
| 6 | `H1_ema_stack=down` | 0.0381 |
| 7 | `sar_bearish=False` | 0.0362 |
| 8 | `regime_label=ranging` | 0.0305 |
| 9 | `regime_label=transition` | 0.0300 |
| 10 | `dow=Fri` | 0.0292 |
| 11 | `adx_H4=[−∞,18)` | 0.0269 |
| 12 | `H1_ema_stack=mixed` | 0.0262 |
| 13 | `dow=Wed` | 0.0253 |
| 14 | `ml_confidence_bucket=[80,+∞)` | 0.0242 |
| 15 | `sar_bearish=True` | 0.0228 |

---

## GDAXI.INDX · ml:balanced · BUY
- Toplam çözülmüş: **181**  ·  Baseline win-rate: **59.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +40.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +35.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.1%** (3 W / 24 L = 27 trade · -48.0pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d = [0.5,+∞)`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -25.8pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.1008 |
| 2 | `sar_bearish=True` | 0.0895 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0858 |
| 4 | `sar_bearish=False` | 0.0803 |
| 5 | `rsi_H1=[50,65)` | 0.0655 |
| 6 | `H4_ema_stack=up` | 0.0511 |
| 7 | `bb_extreme_upper=True` | 0.0312 |
| 8 | `us10y_chg1d=[−∞,-0.5)` | 0.0255 |
| 9 | `volatility_regime=high` | 0.0246 |
| 10 | `adx_H1=[−∞,18)` | 0.0238 |
| 11 | `H1_adx_label=ranging` | 0.0217 |
| 12 | `H1_ema_stack=down` | 0.0178 |
| 13 | `adx_H1=[25,35)` | 0.0174 |
| 14 | `macro_alignment=neutral` | 0.0157 |
| 15 | `volatility_regime=normal` | 0.0154 |

---

## GDAXI.INDX · ml:full_power · BUY
- Toplam çözülmüş: **195**  ·  Baseline win-rate: **53.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +46.7pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +41.7pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (3 W / 27 L = 30 trade · -43.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d = [0.5,+∞)`

**2. Win-rate 20.7%** (6 W / 23 L = 29 trade · -32.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1321 |
| 2 | `sar_bearish=False` | 0.1045 |
| 3 | `rsi_H1=[30,50)` | 0.1033 |
| 4 | `rsi_H1=[50,65)` | 0.0710 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0587 |
| 6 | `H4_ema_stack=up` | 0.0488 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0342 |
| 8 | `bb_extreme_upper=True` | 0.0235 |
| 9 | `bb_extreme_lower=True` | 0.0228 |
| 10 | `adx_H1=[−∞,18)` | 0.0209 |
| 11 | `rsi_H4=[50,65)` | 0.0187 |
| 12 | `bb_extreme_lower=False` | 0.0186 |
| 13 | `H1_ema_stack=down` | 0.0180 |
| 14 | `volatility_regime=high` | 0.0178 |
| 15 | `adx_H1=[25,35)` | 0.0161 |

---

## GDAXI.INDX · ml:full_power · SELL
- Toplam çözülmüş: **80**  ·  Baseline win-rate: **78.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +21.2pp vs baseline)
   - `H4_adx_label ≠ NA`
   - `dxy_chg1d = [-0.5,0)`

**2. Win-rate 82.9%** (29 W / 6 L = 35 trade · +4.1pp vs baseline)
   - `H4_adx_label ≠ NA`
   - `dxy_chg1d ≠ [-0.5,0)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[50,65)` | 0.1034 |
| 2 | `rsi_H4=NA` | 0.0773 |
| 3 | `H4_ema_stack=NA` | 0.0761 |
| 4 | `adx_H4=NA` | 0.0690 |
| 5 | `rsi_H1=[65,75)` | 0.0485 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0386 |
| 7 | `adx_H4=[18,25)` | 0.0378 |
| 8 | `H4_adx_label=NA` | 0.0362 |
| 9 | `H1_ema_stack=up` | 0.0360 |
| 10 | `H1_ema_stack=mixed` | 0.0313 |
| 11 | `regime_label=transition` | 0.0255 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0241 |
| 13 | `H4_adx_label=weak_trend` | 0.0238 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0229 |
| 15 | `dow=Wed` | 0.0215 |

---

## GDAXI.INDX · ml:main · BUY
- Toplam çözülmüş: **196**  ·  Baseline win-rate: **53.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +46.9pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +41.9pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (3 W / 27 L = 30 trade · -43.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d = [0.5,+∞)`

**2. Win-rate 20.7%** (6 W / 23 L = 29 trade · -32.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `adx_H4 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1403 |
| 2 | `sar_bearish=False` | 0.1125 |
| 3 | `rsi_H1=[30,50)` | 0.0814 |
| 4 | `rsi_H1=[50,65)` | 0.0735 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0413 |
| 6 | `H4_ema_stack=up` | 0.0412 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0395 |
| 8 | `volatility_regime=high` | 0.0260 |
| 9 | `bb_extreme_lower=False` | 0.0212 |
| 10 | `bb_extreme_lower=True` | 0.0202 |
| 11 | `H1_adx_label=trending` | 0.0186 |
| 12 | `bb_extreme_upper=False` | 0.0178 |
| 13 | `adx_H1=[25,35)` | 0.0176 |
| 14 | `bb_extreme_upper=True` | 0.0155 |
| 15 | `rsi_H4=[50,65)` | 0.0150 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **880**  ·  Baseline win-rate: **24.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.9%** (46 W / 3 L = 49 trade · +69.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `H1_adx_label ≠ trending`
   - `vix_chg1d = [0,3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 217 L = 217 trade · -24.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish = False`

**2. Win-rate 1.6%** (1 W / 60 L = 61 trade · -23.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 3.3%** (1 W / 29 L = 30 trade · -21.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `H1_adx_label = trending`
   - `sar_bearish = False`

**4. Win-rate 8.3%** (3 W / 33 L = 36 trade · -16.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `bb_extreme_upper ≠ False`

**5. Win-rate 10.0%** (2 W / 18 L = 20 trade · -14.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish ≠ False`

**6. Win-rate 19.7%** (13 W / 53 L = 66 trade · -5.1pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

**7. Win-rate 23.7%** (41 W / 132 L = 173 trade · -1.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `bb_extreme_upper = False`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1240 |
| 2 | `bb_extreme_upper=False` | 0.0553 |
| 3 | `sar_bearish=True` | 0.0471 |
| 4 | `bb_extreme_upper=True` | 0.0459 |
| 5 | `sar_bearish=False` | 0.0412 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0331 |
| 7 | `dow=Fri` | 0.0263 |
| 8 | `near_resistance=False` | 0.0257 |
| 9 | `H4_adx_label=weak_trend` | 0.0236 |
| 10 | `overbought=True` | 0.0218 |
| 11 | `overbought=False` | 0.0217 |
| 12 | `near_resistance=True` | 0.0200 |
| 13 | `adx_H4=[−∞,18)` | 0.0190 |
| 14 | `vix_chg1d=[0,3)` | 0.0185 |
| 15 | `regime_label=ranging` | 0.0182 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **413**  ·  Baseline win-rate: **25.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.5%** (22 W / 5 L = 27 trade · +56.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 66 L = 66 trade · -25.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 = [30,50)`
   - `sar_bearish = True`
   - `H4_ema_stack ≠ NA`

**2. Win-rate 0.0%** (0 W / 45 L = 45 trade · -25.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket = 12-16`
   - `macro_alignment = strong_pro`

**3. Win-rate 4.0%** (1 W / 24 L = 25 trade · -21.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d = [−∞,-3)`

**4. Win-rate 10.3%** (3 W / 26 L = 29 trade · -15.1pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket = 12-16`
   - `macro_alignment ≠ strong_pro`

**5. Win-rate 18.8%** (12 W / 52 L = 64 trade · -6.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `dow ≠ Mon`
   - `hour_bucket ≠ 08-12`

**6. Win-rate 25.0%** (7 W / 21 L = 28 trade · -0.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d ≠ [−∞,-3)`

**7. Win-rate 30.4%** (7 W / 16 L = 23 trade · 5.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 = [30,50)`
   - `sar_bearish = True`
   - `H4_ema_stack = NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0580 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0491 |
| 3 | `hour_bucket=08-12` | 0.0446 |
| 4 | `hour_bucket=12-16` | 0.0435 |
| 5 | `sar_bearish=False` | 0.0352 |
| 6 | `bb_extreme_lower=True` | 0.0349 |
| 7 | `sar_bearish=True` | 0.0341 |
| 8 | `adx_H4=[25,35)` | 0.0300 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0299 |
| 10 | `H4_ema_stack=up` | 0.0291 |
| 11 | `bb_extreme_lower=False` | 0.0285 |
| 12 | `rsi_H1=[50,65)` | 0.0280 |
| 13 | `volatility_regime=normal` | 0.0276 |
| 14 | `H4_adx_label=trending` | 0.0263 |
| 15 | `session=europe` | 0.0237 |

---

## GDAXI.INDX · pulse1_inv · SELL
- Toplam çözülmüş: **83**  ·  Baseline win-rate: **37.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -17.3pp vs baseline)
   - `session ≠ overlap`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0733 |
| 2 | `macro_alignment=weak_against` | 0.0552 |
| 3 | `hour_bucket=12-16` | 0.0469 |
| 4 | `session=europe` | 0.0436 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0433 |
| 6 | `rsi_H1=[30,50)` | 0.0392 |
| 7 | `macro_alignment=strong_pro` | 0.0378 |
| 8 | `rsi_H1=[50,65)` | 0.0374 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0366 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0348 |
| 11 | `adx_H1=[−∞,18)` | 0.0323 |
| 12 | `mtf_trend=mixed` | 0.0319 |
| 13 | `H1_adx_label=weak_trend` | 0.0305 |
| 14 | `macro_alignment=neutral` | 0.0283 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0255 |

---

## GDAXI.INDX · pulse2 · BUY
- Toplam çözülmüş: **469**  ·  Baseline win-rate: **44.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.8%** (44 W / 1 L = 45 trade · +53.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 ≠ [50,65)`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +41.4pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 = [50,65)`

**3. Win-rate 83.7%** (36 W / 7 L = 43 trade · +39.4pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `H1_adx_label = trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 30 L = 30 trade · -44.3pp vs baseline)
   - `sar_bearish = False`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = True`
   - `rsi_H4 = [50,65)`

**2. Win-rate 3.3%** (1 W / 29 L = 30 trade · -41.0pp vs baseline)
   - `sar_bearish = False`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper ≠ True`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 8.0%** (2 W / 23 L = 25 trade · -36.3pp vs baseline)
   - `sar_bearish = False`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = True`
   - `rsi_H4 ≠ [50,65)`

**4. Win-rate 15.4%** (4 W / 22 L = 26 trade · -28.9pp vs baseline)
   - `sar_bearish = False`
   - `mtf_trend = mixed`
   - `dow ≠ Fri`
   - `H4_adx_label = weak_trend`

**5. Win-rate 23.3%** (7 W / 23 L = 30 trade · -21.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d = [3,+∞)`

**6. Win-rate 30.4%** (14 W / 32 L = 46 trade · -13.9pp vs baseline)
   - `sar_bearish = False`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1203 |
| 2 | `sar_bearish=True` | 0.0852 |
| 3 | `bb_extreme_upper=False` | 0.0451 |
| 4 | `bb_extreme_upper=True` | 0.0316 |
| 5 | `bb_extreme_lower=True` | 0.0300 |
| 6 | `regime_label=ranging` | 0.0284 |
| 7 | `bb_extreme_lower=False` | 0.0280 |
| 8 | `mtf_trend=mixed` | 0.0255 |
| 9 | `near_resistance=False` | 0.0252 |
| 10 | `dow=Mon` | 0.0237 |
| 11 | `rsi_H1=[30,50)` | 0.0226 |
| 12 | `H4_adx_label=ranging` | 0.0215 |
| 13 | `near_resistance=True` | 0.0189 |
| 14 | `regime_label=transition` | 0.0180 |
| 15 | `vix_chg1d=[0,3)` | 0.0173 |

---

## GDAXI.INDX · pulse2 · SELL
- Toplam çözülmüş: **86**  ·  Baseline win-rate: **41.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.2%** (7 W / 26 L = 33 trade · -20.7pp vs baseline)
   - `regime_label = transition`
   - `dow ≠ Wed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.0579 |
| 2 | `H1_ema_stack=mixed` | 0.0574 |
| 3 | `regime_label=transition` | 0.0485 |
| 4 | `adx_H1=[18,25)` | 0.0477 |
| 5 | `H4_ema_stack=up` | 0.0430 |
| 6 | `H1_adx_label=weak_trend` | 0.0396 |
| 7 | `H4_adx_label=NA` | 0.0395 |
| 8 | `adx_H4=NA` | 0.0375 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0342 |
| 10 | `H4_ema_stack=NA` | 0.0336 |
| 11 | `rsi_H1=[−∞,30)` | 0.0326 |
| 12 | `rsi_H4=NA` | 0.0299 |
| 13 | `vix_chg1d=[-3,0)` | 0.0298 |
| 14 | `H4_adx_label=trending` | 0.0266 |
| 15 | `adx_H1=[−∞,18)` | 0.0254 |

---

## GDAXI.INDX · pulse2_inv · SELL
- Toplam çözülmüş: **83**  ·  Baseline win-rate: **48.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (6 W / 18 L = 24 trade · -23.2pp vs baseline)
   - `macro_alignment ≠ strong_pro`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=NA` | 0.0828 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0789 |
| 3 | `H4_ema_stack=NA` | 0.0658 |
| 4 | `adx_H4=NA` | 0.0622 |
| 5 | `H4_ema_stack=up` | 0.0552 |
| 6 | `macro_alignment=strong_pro` | 0.0503 |
| 7 | `H1_adx_label=trending` | 0.0493 |
| 8 | `rsi_H4=NA` | 0.0432 |
| 9 | `mtf_trend=mixed` | 0.0415 |
| 10 | `H1_ema_stack=up` | 0.0387 |
| 11 | `mtf_trend=all_up` | 0.0323 |
| 12 | `rsi_H4=[75,+∞)` | 0.0224 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0223 |
| 14 | `adx_H1=[35,+∞)` | 0.0215 |
| 15 | `sar_bearish=False` | 0.0189 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **874**  ·  Baseline win-rate: **35.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (57 W / 0 L = 57 trade · +64.6pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 = [30,50)`
   - `adx_H4 = [25,35)`
   - `H1_adx_label = trending`

**2. Win-rate 96.3%** (26 W / 1 L = 27 trade · +60.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 08-12`
   - `bb_extreme_lower ≠ False`

**3. Win-rate 86.4%** (19 W / 3 L = 22 trade · +51.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 = [30,50)`
   - `adx_H4 = [25,35)`
   - `H1_adx_label ≠ trending`

**4. Win-rate 75.6%** (31 W / 10 L = 41 trade · +40.2pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow = Fri`
   - `dxy_chg1d ≠ [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 64 L = 64 trade · -35.4pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow ≠ Fri`
   - `overbought = True`

**2. Win-rate 1.7%** (2 W / 114 L = 116 trade · -33.7pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket = [60,70)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `rsi_H4 = [50,65)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -30.6pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket = [60,70)`
   - `us10y_chg1d = [−∞,-0.5)`
   - `vix_chg1d = [-3,0)`

**4. Win-rate 6.7%** (2 W / 28 L = 30 trade · -28.7pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket = 08-12`
   - `adx_H4 = [18,25)`

**5. Win-rate 7.7%** (3 W / 36 L = 39 trade · -27.7pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket = [60,70)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `rsi_H4 ≠ [50,65)`

**6. Win-rate 15.0%** (3 W / 17 L = 20 trade · -20.4pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow = Fri`
   - `dxy_chg1d = [0,0.5)`

**7. Win-rate 28.3%** (65 W / 165 L = 230 trade · -7.1pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dow ≠ Fri`
   - `overbought ≠ True`

**8. Win-rate 33.3%** (7 W / 14 L = 21 trade · -2.1pp vs baseline)
   - `sar_bearish = False`
   - `ml_confidence_bucket = [60,70)`
   - `us10y_chg1d = [−∞,-0.5)`
   - `vix_chg1d ≠ [-3,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0921 |
| 2 | `rsi_H1=[30,50)` | 0.0652 |
| 3 | `sar_bearish=True` | 0.0557 |
| 4 | `bb_extreme_upper=False` | 0.0368 |
| 5 | `overbought=False` | 0.0346 |
| 6 | `bb_extreme_upper=True` | 0.0334 |
| 7 | `bb_extreme_lower=False` | 0.0318 |
| 8 | `overbought=True` | 0.0288 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0237 |
| 10 | `dow=Mon` | 0.0234 |
| 11 | `dow=Tue` | 0.0220 |
| 12 | `bb_extreme_lower=True` | 0.0215 |
| 13 | `volatility_regime=normal` | 0.0184 |
| 14 | `dow=Fri` | 0.0181 |
| 15 | `rsi_H1=[65,75)` | 0.0174 |

---

## GDAXI.INDX · pulse3 · SELL
- Toplam çözülmüş: **286**  ·  Baseline win-rate: **39.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.2%** (25 W / 1 L = 26 trade · +56.3pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `sar_bearish ≠ True`

**2. Win-rate 87.5%** (28 W / 4 L = 32 trade · +47.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `sar_bearish ≠ True`
   - `H4_adx_label ≠ NA`
   - `rsi_H1 ≠ [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 1.4%** (1 W / 68 L = 69 trade · -38.5pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `sar_bearish = True`
   - `adx_H4 ≠ NA`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 16.7%** (5 W / 25 L = 30 trade · -23.2pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `sar_bearish ≠ True`
   - `H4_adx_label = NA`

**3. Win-rate 25.7%** (9 W / 26 L = 35 trade · -14.2pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `sar_bearish = True`
   - `adx_H4 ≠ NA`
   - `dxy_chg1d = [-0.5,0)`

**4. Win-rate 29.2%** (7 W / 17 L = 24 trade · -10.7pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `sar_bearish = True`
   - `adx_H4 = NA`
   - `hour_bucket = 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0731 |
| 2 | `sar_bearish=False` | 0.0724 |
| 3 | `sar_bearish=True` | 0.0608 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0494 |
| 5 | `dow=Mon` | 0.0488 |
| 6 | `H1_adx_label=trending` | 0.0446 |
| 7 | `rsi_H1=[50,65)` | 0.0355 |
| 8 | `H1_ema_stack=down` | 0.0327 |
| 9 | `H4_ema_stack=mixed` | 0.0315 |
| 10 | `H4_adx_label=NA` | 0.0254 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0218 |
| 12 | `bb_extreme_lower=False` | 0.0200 |
| 13 | `rsi_H1=[30,50)` | 0.0198 |
| 14 | `dow=Fri` | 0.0184 |
| 15 | `bb_extreme_lower=True` | 0.0172 |

---

## GDAXI.INDX · pulse3_inv · SELL
- Toplam çözülmüş: **99**  ·  Baseline win-rate: **45.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -35.5pp vs baseline)
   - `adx_H4 = NA`
   - `macro_alignment ≠ neutral`
   - `session = europe`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -12.2pp vs baseline)
   - `adx_H4 = NA`
   - `macro_alignment ≠ neutral`
   - `session ≠ europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=NA` | 0.0799 |
| 2 | `rsi_H4=NA` | 0.0791 |
| 3 | `adx_H4=NA` | 0.0740 |
| 4 | `H4_ema_stack=NA` | 0.0640 |
| 5 | `H4_adx_label=trending` | 0.0617 |
| 6 | `H4_ema_stack=up` | 0.0439 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0432 |
| 8 | `macro_alignment=strong_pro` | 0.0383 |
| 9 | `H1_adx_label=trending` | 0.0368 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0326 |
| 11 | `macro_alignment=weak_against` | 0.0248 |
| 12 | `H1_ema_stack=down` | 0.0234 |
| 13 | `rsi_H4=[75,+∞)` | 0.0219 |
| 14 | `dow=Thu` | 0.0214 |
| 15 | `dow=Mon` | 0.0207 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **43.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +48.1pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `dxy_chg1d ≠ [0,0.5)`

**2. Win-rate 76.0%** (19 W / 6 L = 25 trade · +32.8pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `dxy_chg1d = [0,0.5)`
   - `adx_H4 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 2.8%** (1 W / 35 L = 36 trade · -40.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket = [70,80)`

**2. Win-rate 11.5%** (3 W / 23 L = 26 trade · -31.7pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket ≠ [70,80)`
   - `volatility_regime = high`

**3. Win-rate 34.6%** (9 W / 17 L = 26 trade · -8.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket ≠ [70,80)`
   - `volatility_regime ≠ high`
   - `us10y_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1319 |
| 2 | `sar_bearish=False` | 0.1254 |
| 3 | `rsi_H1=[30,50)` | 0.0932 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0552 |
| 5 | `bb_extreme_upper=False` | 0.0449 |
| 6 | `bb_extreme_upper=True` | 0.0426 |
| 7 | `rsi_H1=[65,75)` | 0.0299 |
| 8 | `rsi_H1=[50,65)` | 0.0225 |
| 9 | `H1_ema_stack=up` | 0.0217 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0210 |
| 11 | `adx_H1=[25,35)` | 0.0185 |
| 12 | `near_resistance=False` | 0.0183 |
| 13 | `volatility_regime=high` | 0.0175 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0169 |
| 15 | `mtf_trend=mixed` | 0.0169 |

---

## NDX.INDX · meta · SELL
- Toplam çözülmüş: **108**  ·  Baseline win-rate: **54.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +32.9pp vs baseline)
   - `dow = Thu`

**2. Win-rate 75.0%** (18 W / 6 L = 24 trade · +20.4pp vs baseline)
   - `dow ≠ Thu`
   - `rsi_H1 ≠ [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.0%** (3 W / 17 L = 20 trade · -39.6pp vs baseline)
   - `dow ≠ Thu`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0882 |
| 2 | `H1_ema_stack=mixed` | 0.0791 |
| 3 | `H1_adx_label=trending` | 0.0692 |
| 4 | `dow=Thu` | 0.0549 |
| 5 | `sar_bearish=True` | 0.0424 |
| 6 | `macro_alignment=strong_against` | 0.0401 |
| 7 | `dow=Wed` | 0.0398 |
| 8 | `adx_H4=[25,35)` | 0.0317 |
| 9 | `sar_bearish=False` | 0.0292 |
| 10 | `adx_H1=[35,+∞)` | 0.0287 |
| 11 | `adx_H1=[18,25)` | 0.0274 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0211 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0210 |
| 14 | `H4_adx_label=trending` | 0.0205 |
| 15 | `dow=Tue` | 0.0200 |

---

## NDX.INDX · ml:balanced · BUY
- Toplam çözülmüş: **165**  ·  Baseline win-rate: **50.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.3%** (29 W / 5 L = 34 trade · +34.4pp vs baseline)
   - `sar_bearish = True`
   - `H4_adx_label ≠ ranging`
   - `vix_chg1d ≠ [3,+∞)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (6 W / 33 L = 39 trade · -35.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H1 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1086 |
| 2 | `sar_bearish=True` | 0.0999 |
| 3 | `rsi_H1=[30,50)` | 0.0506 |
| 4 | `volatility_regime=normal` | 0.0409 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0333 |
| 6 | `adx_H4=[35,+∞)` | 0.0327 |
| 7 | `rsi_H1=[50,65)` | 0.0313 |
| 8 | `H4_ema_stack=mixed` | 0.0302 |
| 9 | `H4_ema_stack=up` | 0.0290 |
| 10 | `session_phase=mid_session` | 0.0242 |
| 11 | `rsi_H4=[30,50)` | 0.0226 |
| 12 | `volatility_regime=high` | 0.0211 |
| 13 | `rsi_H4=[50,65)` | 0.0192 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0188 |
| 15 | `session_phase=open_drive` | 0.0183 |

---

## NDX.INDX · ml:balanced · SELL
- Toplam çözülmüş: **108**  ·  Baseline win-rate: **58.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.6%** (22 W / 6 L = 28 trade · +20.3pp vs baseline)
   - `H1_ema_stack ≠ mixed`
   - `session_phase ≠ mid_session`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0637 |
| 2 | `sar_bearish=False` | 0.0544 |
| 3 | `adx_H1=[18,25)` | 0.0516 |
| 4 | `H1_ema_stack=up` | 0.0405 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0387 |
| 6 | `volatility_regime=normal` | 0.0357 |
| 7 | `dow=Thu` | 0.0352 |
| 8 | `H1_ema_stack=mixed` | 0.0340 |
| 9 | `H1_adx_label=weak_trend` | 0.0322 |
| 10 | `H4_ema_stack=mixed` | 0.0304 |
| 11 | `session_phase=mid_session` | 0.0299 |
| 12 | `mtf_trend=mixed` | 0.0285 |
| 13 | `H1_adx_label=trending` | 0.0284 |
| 14 | `regime_label=transition` | 0.0279 |
| 15 | `us10y_chg1d=[0,0.5)` | 0.0277 |

---

## NDX.INDX · ml:full_power · BUY
- Toplam çözülmüş: **160**  ·  Baseline win-rate: **51.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +34.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_H4 ≠ [−∞,18)`
   - `rsi_H1 = [30,50)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.8%** (5 W / 19 L = 24 trade · -30.4pp vs baseline)
   - `sar_bearish = False`
   - `session_phase = mid_session`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0858 |
| 2 | `sar_bearish=True` | 0.0737 |
| 3 | `rsi_H1=[30,50)` | 0.0555 |
| 4 | `rsi_H1=[50,65)` | 0.0486 |
| 5 | `volatility_regime=high` | 0.0407 |
| 6 | `volatility_regime=normal` | 0.0397 |
| 7 | `adx_H4=[35,+∞)` | 0.0359 |
| 8 | `macro_alignment=weak_pro` | 0.0347 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0333 |
| 10 | `H4_adx_label=trending` | 0.0286 |
| 11 | `H4_adx_label=ranging` | 0.0277 |
| 12 | `macro_alignment=neutral` | 0.0268 |
| 13 | `dow=Mon` | 0.0258 |
| 14 | `adx_H1=[−∞,18)` | 0.0220 |
| 15 | `H4_ema_stack=up` | 0.0207 |

---

## NDX.INDX · ml:full_power · SELL
- Toplam çözülmüş: **115**  ·  Baseline win-rate: **60.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +30.0pp vs baseline)
   - `us10y_chg1d = [−∞,-0.5)`
   - `session = overlap`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -40.9pp vs baseline)
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_H1 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[−∞,-0.5)` | 0.0792 |
| 2 | `sar_bearish=False` | 0.0556 |
| 3 | `H1_adx_label=trending` | 0.0422 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0419 |
| 5 | `regime_label=transition` | 0.0394 |
| 6 | `adx_H1=[18,25)` | 0.0372 |
| 7 | `sar_bearish=True` | 0.0371 |
| 8 | `H1_adx_label=weak_trend` | 0.0360 |
| 9 | `session_phase=mid_session` | 0.0357 |
| 10 | `adx_H4=[−∞,18)` | 0.0336 |
| 11 | `H4_ema_stack=mixed` | 0.0335 |
| 12 | `H1_ema_stack=mixed` | 0.0334 |
| 13 | `mtf_trend=all_up` | 0.0320 |
| 14 | `H4_adx_label=ranging` | 0.0310 |
| 15 | `H1_ema_stack=up` | 0.0300 |

---

## NDX.INDX · ml:main · BUY
- Toplam çözülmüş: **161**  ·  Baseline win-rate: **51.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +36.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_H4 ≠ [−∞,18)`
   - `ml_confidence_bucket ≠ [−∞,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.8%** (5 W / 19 L = 24 trade · -30.8pp vs baseline)
   - `sar_bearish = False`
   - `session_phase = mid_session`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1126 |
| 2 | `sar_bearish=False` | 0.0964 |
| 3 | `dow=Mon` | 0.0467 |
| 4 | `rsi_H1=[30,50)` | 0.0392 |
| 5 | `volatility_regime=normal` | 0.0369 |
| 6 | `rsi_H1=[50,65)` | 0.0352 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0352 |
| 8 | `macro_alignment=neutral` | 0.0299 |
| 9 | `macro_alignment=weak_pro` | 0.0278 |
| 10 | `H4_adx_label=trending` | 0.0276 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0262 |
| 12 | `adx_H4=[35,+∞)` | 0.0254 |
| 13 | `volatility_regime=high` | 0.0203 |
| 14 | `adx_H1=[−∞,18)` | 0.0196 |
| 15 | `adx_H4=[−∞,18)` | 0.0192 |

---

## NDX.INDX · ml:main · SELL
- Toplam çözülmüş: **114**  ·  Baseline win-rate: **62.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.3%** (21 W / 2 L = 23 trade · +29.0pp vs baseline)
   - `us10y_chg1d = [−∞,-0.5)`
   - `mtf_trend ≠ mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.7%** (4 W / 20 L = 24 trade · -45.6pp vs baseline)
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `H1_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=up` | 0.0702 |
| 2 | `H1_ema_stack=mixed` | 0.0601 |
| 3 | `mtf_trend=all_up` | 0.0542 |
| 4 | `adx_H1=[18,25)` | 0.0503 |
| 5 | `regime_label=transition` | 0.0488 |
| 6 | `H1_adx_label=weak_trend` | 0.0454 |
| 7 | `session_phase=mid_session` | 0.0414 |
| 8 | `us10y_chg1d=[−∞,-0.5)` | 0.0409 |
| 9 | `dow=Thu` | 0.0313 |
| 10 | `mtf_trend=mixed` | 0.0292 |
| 11 | `H4_ema_stack=mixed` | 0.0288 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0265 |
| 13 | `hour_bucket=16-20` | 0.0233 |
| 14 | `adx_H1=[25,35)` | 0.0222 |
| 15 | `hour_bucket=12-16` | 0.0219 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **654**  ·  Baseline win-rate: **26.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (20 W / 0 L = 20 trade · +73.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 = [30,50)`
   - `vix_chg1d = [0,3)`
   - `rsi_H4 ≠ [30,50)`

**2. Win-rate 77.8%** (21 W / 6 L = 27 trade · +51.3pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 = [30,50)`
   - `vix_chg1d = [0,3)`
   - `rsi_H4 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -26.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `macro_alignment = weak_pro`
   - `session = us`

**2. Win-rate 0.0%** (0 W / 100 L = 100 trade · -26.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack ≠ mixed`
   - `macro_alignment ≠ strong_pro`

**3. Win-rate 0.0%** (0 W / 25 L = 25 trade · -26.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack = mixed`
   - `H4_ema_stack = up`

**4. Win-rate 3.6%** (1 W / 27 L = 28 trade · -22.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack ≠ mixed`
   - `macro_alignment = strong_pro`

**5. Win-rate 4.5%** (1 W / 21 L = 22 trade · -22.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow = Mon`

**6. Win-rate 15.6%** (5 W / 27 L = 32 trade · -10.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow ≠ Mon`
   - `macro_alignment = neutral`

**7. Win-rate 16.0%** (12 W / 63 L = 75 trade · -10.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `macro_alignment ≠ weak_pro`
   - `ml_confidence_bucket = [50,60)`

**8. Win-rate 19.0%** (4 W / 17 L = 21 trade · -7.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `macro_alignment = weak_pro`
   - `session ≠ us`

**9. Win-rate 19.2%** (5 W / 21 L = 26 trade · -7.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack = mixed`
   - `H4_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0725 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0717 |
| 3 | `sar_bearish=True` | 0.0646 |
| 4 | `sar_bearish=False` | 0.0595 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0308 |
| 6 | `bb_extreme_upper=False` | 0.0290 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0260 |
| 8 | `H1_ema_stack=up` | 0.0257 |
| 9 | `volatility_regime=high` | 0.0236 |
| 10 | `bb_extreme_upper=True` | 0.0233 |
| 11 | `H4_ema_stack=NA` | 0.0226 |
| 12 | `vix_chg1d=[-3,0)` | 0.0221 |
| 13 | `rsi_H1=[50,65)` | 0.0212 |
| 14 | `rsi_H1=[65,75)` | 0.0183 |
| 15 | `volatility_regime=normal` | 0.0177 |

---

## NDX.INDX · pulse1 · SELL
- Toplam çözülmüş: **533**  ·  Baseline win-rate: **49.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.3%** (36 W / 3 L = 39 trade · +42.6pp vs baseline)
   - `H1_adx_label = trending`
   - `dow ≠ Tue`
   - `adx_H1 = [35,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**2. Win-rate 75.8%** (25 W / 8 L = 33 trade · +26.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `volatility_regime ≠ high`
   - `ml_confidence_bucket = [60,70)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.9%** (7 W / 72 L = 79 trade · -40.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `volatility_regime = high`
   - `mtf_trend = mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 30.2%** (13 W / 30 L = 43 trade · -19.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `volatility_regime = high`
   - `mtf_trend = mixed`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 33.3%** (7 W / 14 L = 21 trade · -16.4pp vs baseline)
   - `H1_adx_label = trending`
   - `dow = Tue`
   - `H1_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0813 |
| 2 | `adx_H1=[35,+∞)` | 0.0398 |
| 3 | `volatility_regime=high` | 0.0371 |
| 4 | `volatility_regime=normal` | 0.0288 |
| 5 | `adx_H1=[18,25)` | 0.0285 |
| 6 | `dow=Tue` | 0.0246 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0220 |
| 8 | `H4_adx_label=trending` | 0.0214 |
| 9 | `adx_H1=[−∞,18)` | 0.0206 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0195 |
| 11 | `rsi_H1=[50,65)` | 0.0183 |
| 12 | `rsi_H4=[30,50)` | 0.0179 |
| 13 | `H1_adx_label=ranging` | 0.0179 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0176 |
| 15 | `dow=Fri` | 0.0176 |

---

## NDX.INDX · pulse1_inv · BUY
- Toplam çözülmüş: **146**  ·  Baseline win-rate: **47.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.7%** (5 W / 18 L = 23 trade · -26.2pp vs baseline)
   - `session_phase = mid_session`
   - `H1_ema_stack = up`

**2. Win-rate 34.8%** (8 W / 15 L = 23 trade · -13.1pp vs baseline)
   - `session_phase ≠ mid_session`
   - `dow = Wed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=mid_session` | 0.0453 |
| 2 | `dxy_chg1d=[-0.5,0)` | 0.0392 |
| 3 | `H1_adx_label=weak_trend` | 0.0375 |
| 4 | `H1_adx_label=ranging` | 0.0371 |
| 5 | `adx_H1=[25,35)` | 0.0288 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0286 |
| 7 | `H4_ema_stack=down` | 0.0281 |
| 8 | `dow=Wed` | 0.0273 |
| 9 | `H1_ema_stack=down` | 0.0261 |
| 10 | `H4_adx_label=trending` | 0.0258 |
| 11 | `adx_H1=[−∞,18)` | 0.0253 |
| 12 | `adx_H4=[18,25)` | 0.0236 |
| 13 | `H1_adx_label=trending` | 0.0230 |
| 14 | `rsi_H4=[50,65)` | 0.0226 |
| 15 | `H1_ema_stack=up` | 0.0218 |

---

## NDX.INDX · pulse1_inv · SELL
- Toplam çözülmüş: **181**  ·  Baseline win-rate: **51.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (18 W / 2 L = 20 trade · +38.1pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (3 W / 18 L = 21 trade · -37.6pp vs baseline)
   - `dow = Fri`

**2. Win-rate 27.7%** (13 W / 34 L = 47 trade · -24.2pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session_phase ≠ after_hours`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[−∞,-3)` | 0.0647 |
| 2 | `H4_ema_stack=mixed` | 0.0503 |
| 3 | `rsi_H1=[50,65)` | 0.0420 |
| 4 | `dow=Fri` | 0.0404 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0403 |
| 6 | `overbought=True` | 0.0350 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0315 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0268 |
| 9 | `us10y_chg1d=[0,0.5)` | 0.0259 |
| 10 | `hour_bucket=12-16` | 0.0243 |
| 11 | `dow=Tue` | 0.0227 |
| 12 | `overbought=False` | 0.0222 |
| 13 | `rsi_H1=[65,75)` | 0.0220 |
| 14 | `macro_alignment=neutral` | 0.0218 |
| 15 | `session_phase=mid_session` | 0.0217 |

---

## NDX.INDX · pulse2 · BUY
- Toplam çözülmüş: **305**  ·  Baseline win-rate: **40.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.5%** (21 W / 1 L = 22 trade · +55.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [-3,0)`
   - `rsi_H1 ≠ [50,65)`

**2. Win-rate 79.2%** (19 W / 5 L = 24 trade · +39.2pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [-3,0)`
   - `rsi_H1 = [50,65)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 27 L = 27 trade · -40.0pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ False`
   - `session_phase ≠ after_hours`

**2. Win-rate 8.0%** (2 W / 23 L = 25 trade · -32.0pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = False`
   - `mtf_trend = all_up`
   - `dxy_chg1d = [-0.5,0)`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -30.0pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ False`
   - `session_phase = after_hours`

**4. Win-rate 25.0%** (8 W / 24 L = 32 trade · -15.0pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = False`
   - `mtf_trend = all_up`
   - `dxy_chg1d ≠ [-0.5,0)`

**5. Win-rate 25.9%** (7 W / 20 L = 27 trade · -14.1pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = False`
   - `mtf_trend ≠ all_up`
   - `rsi_H4 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1338 |
| 2 | `sar_bearish=True` | 0.1164 |
| 3 | `bb_extreme_upper=True` | 0.0533 |
| 4 | `rsi_H1=[30,50)` | 0.0493 |
| 5 | `bb_extreme_upper=False` | 0.0397 |
| 6 | `dow=Thu` | 0.0263 |
| 7 | `dow=Wed` | 0.0209 |
| 8 | `H1_adx_label=weak_trend` | 0.0204 |
| 9 | `rsi_H1=[50,65)` | 0.0197 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0184 |
| 11 | `volatility_regime=high` | 0.0181 |
| 12 | `dow=Mon` | 0.0168 |
| 13 | `adx_H1=[18,25)` | 0.0167 |
| 14 | `macro_alignment=weak_pro` | 0.0161 |
| 15 | `rsi_H1=[65,75)` | 0.0159 |

---

## NDX.INDX · pulse2 · SELL
- Toplam çözülmüş: **205**  ·  Baseline win-rate: **55.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.3%** (48 W / 7 L = 55 trade · +32.2pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow ≠ Tue`
   - `dow ≠ Wed`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.0%** (3 W / 20 L = 23 trade · -42.1pp vs baseline)
   - `us10y_chg1d = [0,0.5)`

**2. Win-rate 31.2%** (10 W / 22 L = 32 trade · -23.9pp vs baseline)
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow = Tue`
   - `H4_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[18,25)` | 0.0555 |
| 2 | `H1_adx_label=trending` | 0.0540 |
| 3 | `dow=Thu` | 0.0450 |
| 4 | `H4_ema_stack=up` | 0.0448 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0447 |
| 6 | `dxy_chg1d=[0.5,+∞)` | 0.0421 |
| 7 | `dow=Fri` | 0.0399 |
| 8 | `us10y_chg1d=[0,0.5)` | 0.0376 |
| 9 | `dow=Tue` | 0.0330 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0302 |
| 11 | `H1_adx_label=weak_trend` | 0.0299 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0268 |
| 13 | `session=overlap` | 0.0238 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0231 |
| 15 | `macro_alignment=strong_pro` | 0.0200 |

---

## NDX.INDX · pulse2_inv · BUY
- Toplam çözülmüş: **97**  ·  Baseline win-rate: **60.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +24.2pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `H4_ema_stack = down`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0779 |
| 2 | `rsi_H1=[30,50)` | 0.0557 |
| 3 | `mtf_trend=mixed` | 0.0530 |
| 4 | `sar_bearish=True` | 0.0510 |
| 5 | `sar_bearish=False` | 0.0491 |
| 6 | `mtf_trend=all_down` | 0.0439 |
| 7 | `session_phase=mid_session` | 0.0417 |
| 8 | `rsi_H1=[50,65)` | 0.0414 |
| 9 | `hour_bucket=12-16` | 0.0372 |
| 10 | `volatility_regime=high` | 0.0311 |
| 11 | `adx_H4=[25,35)` | 0.0283 |
| 12 | `session=us` | 0.0271 |
| 13 | `session=overlap` | 0.0237 |
| 14 | `adx_H1=[25,35)` | 0.0237 |
| 15 | `H4_ema_stack=down` | 0.0228 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **600**  ·  Baseline win-rate: **30.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (34 W / 0 L = 34 trade · +69.8pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [-0.5,0)`
   - `H4_ema_stack = up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 117 L = 117 trade · -30.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `mtf_trend ≠ mixed`

**2. Win-rate 3.6%** (1 W / 27 L = 28 trade · -26.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `near_resistance = True`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -25.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `mtf_trend = mixed`

**4. Win-rate 8.3%** (2 W / 22 L = 24 trade · -21.9pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session_phase = mid_session`

**5. Win-rate 9.1%** (2 W / 20 L = 22 trade · -21.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session_phase ≠ mid_session`

**6. Win-rate 18.1%** (17 W / 77 L = 94 trade · -12.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `near_resistance ≠ True`

**7. Win-rate 19.2%** (5 W / 21 L = 26 trade · -11.0pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `vix_chg1d = [-3,0)`

**8. Win-rate 22.7%** (5 W / 17 L = 22 trade · -7.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow = Tue`

**9. Win-rate 32.0%** (8 W / 17 L = 25 trade · 1.8pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `vix_chg1d ≠ [-3,0)`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1322 |
| 2 | `sar_bearish=False` | 0.1090 |
| 3 | `bb_extreme_upper=False` | 0.0391 |
| 4 | `rsi_H1=[30,50)` | 0.0291 |
| 5 | `bb_extreme_upper=True` | 0.0254 |
| 6 | `rsi_H1=[65,75)` | 0.0248 |
| 7 | `H4_ema_stack=NA` | 0.0220 |
| 8 | `us10y_chg1d=[−∞,-0.5)` | 0.0217 |
| 9 | `overbought=False` | 0.0215 |
| 10 | `H1_ema_stack=up` | 0.0211 |
| 11 | `macro_alignment=weak_pro` | 0.0189 |
| 12 | `near_resistance=True` | 0.0181 |
| 13 | `near_resistance=False` | 0.0167 |
| 14 | `dow=Fri` | 0.0163 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0162 |

---

## NDX.INDX · pulse3 · SELL
- Toplam çözülmüş: **631**  ·  Baseline win-rate: **56.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (44 W / 0 L = 44 trade · +43.1pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 95.7%** (22 W / 1 L = 23 trade · +38.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [−∞,50)`
   - `session = us`
   - `volatility_regime = high`

**3. Win-rate 94.1%** (32 W / 2 L = 34 trade · +37.2pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow = Fri`
   - `session_phase ≠ mid_session`

**4. Win-rate 91.3%** (21 W / 2 L = 23 trade · +34.4pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 = [30,50)`

**5. Win-rate 76.9%** (30 W / 9 L = 39 trade · +20.0pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow = Fri`
   - `session_phase = mid_session`

**6. Win-rate 75.8%** (25 W / 8 L = 33 trade · +18.9pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow ≠ Fri`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.7%** (13 W / 108 L = 121 trade · -46.2pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `sar_bearish = True`
   - `H4_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0927 |
| 2 | `adx_H1=[35,+∞)` | 0.0497 |
| 3 | `sar_bearish=True` | 0.0376 |
| 4 | `sar_bearish=False` | 0.0330 |
| 5 | `us10y_chg1d=[0,0.5)` | 0.0304 |
| 6 | `dow=Tue` | 0.0295 |
| 7 | `H1_adx_label=ranging` | 0.0274 |
| 8 | `adx_H1=[18,25)` | 0.0260 |
| 9 | `adx_H4=[25,35)` | 0.0247 |
| 10 | `adx_H1=[−∞,18)` | 0.0241 |
| 11 | `adx_H4=[35,+∞)` | 0.0237 |
| 12 | `dow=Fri` | 0.0224 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0221 |
| 14 | `macro_alignment=strong_against` | 0.0214 |
| 15 | `H1_adx_label=weak_trend` | 0.0208 |

---

## NDX.INDX · pulse3_inv · BUY
- Toplam çözülmüş: **194**  ·  Baseline win-rate: **58.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +41.2pp vs baseline)
   - `H4_ema_stack = up`
   - `H1_adx_label = weak_trend`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (4 W / 16 L = 20 trade · -38.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_H4 ≠ [35,+∞)`
   - `oversold ≠ True`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0414 |
| 2 | `session_phase=close_drive` | 0.0376 |
| 3 | `H4_ema_stack=up` | 0.0352 |
| 4 | `H4_adx_label=trending` | 0.0333 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0329 |
| 6 | `rsi_H4=[50,65)` | 0.0323 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 8 | `adx_H1=[18,25)` | 0.0307 |
| 9 | `volatility_regime=high` | 0.0284 |
| 10 | `H1_adx_label=trending` | 0.0280 |
| 11 | `regime_label=ranging` | 0.0276 |
| 12 | `rsi_H4=[30,50)` | 0.0269 |
| 13 | `H1_ema_stack=down` | 0.0260 |
| 14 | `H1_adx_label=weak_trend` | 0.0258 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0252 |

---

## NDX.INDX · pulse3_inv · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **52.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.2%** (33 W / 4 L = 37 trade · +36.9pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 80.0%** (20 W / 5 L = 25 trade · +27.7pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session ≠ us`
   - `dxy_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -44.6pp vs baseline)
   - `dow = Fri`
   - `us10y_chg1d = [-0.5,0)`

**2. Win-rate 29.7%** (11 W / 26 L = 37 trade · -22.6pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session = us`
   - `volatility_regime ≠ high`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0735 |
| 2 | `dxy_chg1d=[0,0.5)` | 0.0563 |
| 3 | `dxy_chg1d=[0.5,+∞)` | 0.0447 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0420 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0354 |
| 6 | `session=overlap` | 0.0349 |
| 7 | `overbought=False` | 0.0343 |
| 8 | `overbought=True` | 0.0320 |
| 9 | `H4_adx_label=ranging` | 0.0304 |
| 10 | `hour_bucket=12-16` | 0.0294 |
| 11 | `H4_ema_stack=mixed` | 0.0228 |
| 12 | `H1_adx_label=weak_trend` | 0.0222 |
| 13 | `H1_adx_label=ranging` | 0.0198 |
| 14 | `rsi_H1=[50,65)` | 0.0194 |
| 15 | `macro_alignment=strong_pro` | 0.0189 |

---

## USOIL.FOREX · emel · BUY
- Toplam çözülmüş: **220**  ·  Baseline win-rate: **27.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +55.5pp vs baseline)
   - `H4_ema_stack = mixed`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 48 L = 48 trade · -27.3pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 8.6%** (3 W / 32 L = 35 trade · -18.7pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dxy_chg1d = [-0.5,0)`

**3. Win-rate 19.4%** (7 W / 29 L = 36 trade · -7.9pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label ≠ trending`
   - `M30_adx_label ≠ trending`

**4. Win-rate 25.0%** (5 W / 15 L = 20 trade · -2.3pp vs baseline)
   - `H4_ema_stack = mixed`
   - `session = overlap`

**5. Win-rate 33.3%** (10 W / 20 L = 30 trade · 6.0pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0833 |
| 2 | `mtf_trend=mixed` | 0.0712 |
| 3 | `H4_ema_stack=mixed` | 0.0622 |
| 4 | `rsi_H4=[65,75)` | 0.0321 |
| 5 | `adx_H4=[18,25)` | 0.0290 |
| 6 | `H4_ema_stack=down` | 0.0288 |
| 7 | `H4_adx_label=weak_trend` | 0.0278 |
| 8 | `mtf_trend=all_down` | 0.0253 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0236 |
| 10 | `H1_ema_stack=up` | 0.0210 |
| 11 | `regime_label=transition` | 0.0197 |
| 12 | `adx_H4=[−∞,18)` | 0.0196 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0194 |
| 14 | `dow=Mon` | 0.0190 |
| 15 | `M30_ema_stack=down` | 0.0170 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **374**  ·  Baseline win-rate: **1.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 93 L = 93 trade · -1.6pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 ≠ [50,65)`

**2. Win-rate 0.0%** (0 W / 64 L = 64 trade · -1.6pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_H4 = [18,25)`
   - `hour_bucket ≠ 20-24`

**3. Win-rate 0.0%** (0 W / 144 L = 144 trade · -1.6pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `session_phase ≠ early_pit`

**4. Win-rate 0.0%** (0 W / 26 L = 26 trade · -1.6pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `session_phase = early_pit`

**5. Win-rate 4.8%** (1 W / 20 L = 21 trade · 3.2pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_H4 = [18,25)`
   - `hour_bucket = 20-24`

**6. Win-rate 19.2%** (5 W / 21 L = 26 trade · 17.6pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_H4 ≠ [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0532 |
| 2 | `adx_H4=[18,25)` | 0.0472 |
| 3 | `H1_adx_label=trending` | 0.0462 |
| 4 | `M30_adx_label=ranging` | 0.0421 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0417 |
| 6 | `H1_adx_label=ranging` | 0.0326 |
| 7 | `adx_H1=[−∞,18)` | 0.0317 |
| 8 | `H4_adx_label=trending` | 0.0313 |
| 9 | `mtf_trend=all_up` | 0.0311 |
| 10 | `H4_ema_stack=up` | 0.0291 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0266 |
| 12 | `mtf_trend=mixed` | 0.0262 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0199 |
| 14 | `H4_ema_stack=mixed` | 0.0196 |
| 15 | `adx_M30=[−∞,18)` | 0.0194 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **458**  ·  Baseline win-rate: **87.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (40 W / 0 L = 40 trade · +12.9pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_low_M30 = [0.7,1.5)`
   - `macro_alignment = neutral`
   - `H1_adx_label ≠ trending`

**2. Win-rate 100.0%** (162 W / 0 L = 162 trade · +12.9pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label ≠ weak_trend`
   - `adx_H4 ≠ [35,+∞)`

**3. Win-rate 100.0%** (29 W / 0 L = 29 trade · +12.9pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label = weak_trend`
   - `dow = Tue`

**4. Win-rate 92.6%** (25 W / 2 L = 27 trade · +5.5pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label ≠ weak_trend`
   - `adx_H4 = [35,+∞)`

**5. Win-rate 91.3%** (21 W / 2 L = 23 trade · +4.2pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_low_M30 = [0.7,1.5)`
   - `macro_alignment ≠ neutral`
   - `adx_H1 = [18,25)`

**6. Win-rate 88.9%** (24 W / 3 L = 27 trade · +1.8pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `vix_chg1d = [−∞,-3)`

**7. Win-rate 87.1%** (27 W / 4 L = 31 trade · +0.0pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_low_M30 = [0.7,1.5)`
   - `macro_alignment = neutral`
   - `H1_adx_label = trending`

**8. Win-rate 85.7%** (18 W / 3 L = 21 trade · -1.4pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H4_adx_label = weak_trend`
   - `dow ≠ Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.0%** (4 W / 21 L = 25 trade · -71.1pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0574 |
| 2 | `dist_low_M30=[1.5,+∞)` | 0.0551 |
| 3 | `dist_low_M30=[0.3,0.7)` | 0.0373 |
| 4 | `macro_alignment=neutral` | 0.0366 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0361 |
| 6 | `dow=Mon` | 0.0320 |
| 7 | `bb_pctb_M30=[−∞,0.2)` | 0.0313 |
| 8 | `bb_pctb_M30=[0.2,0.5)` | 0.0295 |
| 9 | `dow=Fri` | 0.0283 |
| 10 | `adx_H1=[35,+∞)` | 0.0250 |
| 11 | `macro_alignment=strong_against` | 0.0244 |
| 12 | `H4_adx_label=weak_trend` | 0.0212 |
| 13 | `vix_chg1d=[-3,0)` | 0.0200 |
| 14 | `sar_bearish=False` | 0.0188 |
| 15 | `H1_ema_stack=down` | 0.0177 |

---

## USOIL.FOREX · ml:aggressive · BUY
- Toplam çözülmüş: **307**  ·  Baseline win-rate: **29.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +48.0pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `adx_H4 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -29.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -29.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack ≠ down`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -24.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack = down`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -21.2pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · 0.7pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `adx_H4 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0882 |
| 2 | `H4_ema_stack=down` | 0.0816 |
| 3 | `H4_ema_stack=mixed` | 0.0560 |
| 4 | `H4_adx_label=trending` | 0.0392 |
| 5 | `H1_ema_stack=up` | 0.0350 |
| 6 | `H1_ema_stack=down` | 0.0316 |
| 7 | `vix_chg1d=[0,3)` | 0.0240 |
| 8 | `regime_label=transition` | 0.0225 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0207 |
| 10 | `adx_H4=[−∞,18)` | 0.0205 |
| 11 | `rsi_H4=[65,75)` | 0.0203 |
| 12 | `macro_alignment=strong_against` | 0.0195 |
| 13 | `dow=Mon` | 0.0187 |
| 14 | `adx_H4=[35,+∞)` | 0.0169 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0167 |

---

## USOIL.FOREX · ml:aggressive · SELL
- Toplam çözülmüş: **427**  ·  Baseline win-rate: **79.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (35 W / 0 L = 35 trade · +20.4pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 100.0%** (123 W / 0 L = 123 trade · +20.4pp vs baseline)
   - `H4_ema_stack = up`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +15.6pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack = down`
   - `dow = Fri`

**4. Win-rate 85.0%** (34 W / 6 L = 40 trade · +5.4pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -59.6pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack ≠ down`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0792 |
| 2 | `mtf_trend=all_up` | 0.0607 |
| 3 | `adx_M30=[35,+∞)` | 0.0513 |
| 4 | `M30_adx_label=trending` | 0.0410 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0408 |
| 6 | `M30_ema_stack=up` | 0.0397 |
| 7 | `mtf_trend=mixed` | 0.0385 |
| 8 | `M30_ema_stack=mixed` | 0.0309 |
| 9 | `H4_ema_stack=down` | 0.0246 |
| 10 | `dist_low_M30=[1.5,+∞)` | 0.0234 |
| 11 | `H1_ema_stack=mixed` | 0.0215 |
| 12 | `adx_H4=[18,25)` | 0.0212 |
| 13 | `H1_ema_stack=up` | 0.0209 |
| 14 | `dow=Fri` | 0.0203 |
| 15 | `mtf_trend=all_down` | 0.0159 |

---

## USOIL.FOREX · ml:balanced · BUY
- Toplam çözülmüş: **308**  ·  Baseline win-rate: **28.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -28.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -28.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack ≠ down`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -23.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack = down`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -20.8pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0744 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0709 |
| 3 | `H4_ema_stack=mixed` | 0.0540 |
| 4 | `H4_adx_label=trending` | 0.0469 |
| 5 | `H1_ema_stack=down` | 0.0439 |
| 6 | `H1_ema_stack=up` | 0.0295 |
| 7 | `adx_H4=[−∞,18)` | 0.0229 |
| 8 | `adx_H4=[35,+∞)` | 0.0222 |
| 9 | `regime_label=transition` | 0.0215 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0208 |
| 11 | `adx_H4=[18,25)` | 0.0193 |
| 12 | `regime_label=ranging` | 0.0178 |
| 13 | `vix_chg1d=[0,3)` | 0.0175 |
| 14 | `H4_adx_label=weak_trend` | 0.0167 |
| 15 | `M30_ema_stack=up` | 0.0162 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **426**  ·  Baseline win-rate: **79.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (35 W / 0 L = 35 trade · +20.2pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 100.0%** (123 W / 0 L = 123 trade · +20.2pp vs baseline)
   - `H4_ema_stack = up`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +15.4pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack = down`
   - `dow = Fri`

**4. Win-rate 85.0%** (34 W / 6 L = 40 trade · +5.2pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -59.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack ≠ down`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0785 |
| 2 | `mtf_trend=all_up` | 0.0599 |
| 3 | `mtf_trend=mixed` | 0.0511 |
| 4 | `M30_ema_stack=up` | 0.0464 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0461 |
| 6 | `M30_adx_label=trending` | 0.0422 |
| 7 | `adx_M30=[35,+∞)` | 0.0411 |
| 8 | `H4_ema_stack=down` | 0.0307 |
| 9 | `M30_ema_stack=mixed` | 0.0280 |
| 10 | `dow=Fri` | 0.0258 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0222 |
| 12 | `H1_ema_stack=mixed` | 0.0204 |
| 13 | `adx_H4=[18,25)` | 0.0168 |
| 14 | `adx_H1=[−∞,18)` | 0.0166 |
| 15 | `H4_adx_label=weak_trend` | 0.0160 |

---

## USOIL.FOREX · ml:full_power · BUY
- Toplam çözülmüş: **307**  ·  Baseline win-rate: **29.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +48.0pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `adx_H4 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -29.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -29.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack ≠ down`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -24.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack = down`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -21.2pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · 0.7pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `adx_H4 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0870 |
| 2 | `H4_ema_stack=down` | 0.0833 |
| 3 | `H4_ema_stack=mixed` | 0.0529 |
| 4 | `H4_adx_label=trending` | 0.0416 |
| 5 | `H1_ema_stack=up` | 0.0360 |
| 6 | `H1_ema_stack=down` | 0.0314 |
| 7 | `regime_label=transition` | 0.0263 |
| 8 | `vix_chg1d=[0,3)` | 0.0246 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0205 |
| 10 | `macro_alignment=strong_against` | 0.0190 |
| 11 | `rsi_H4=[65,75)` | 0.0188 |
| 12 | `regime_label=ranging` | 0.0187 |
| 13 | `dow=Mon` | 0.0183 |
| 14 | `H4_adx_label=weak_trend` | 0.0181 |
| 15 | `adx_H4=[−∞,18)` | 0.0178 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **425**  ·  Baseline win-rate: **80.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (35 W / 0 L = 35 trade · +20.0pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 100.0%** (123 W / 0 L = 123 trade · +20.0pp vs baseline)
   - `H4_ema_stack = up`

**3. Win-rate 85.0%** (34 W / 6 L = 40 trade · +5.0pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

**4. Win-rate 83.3%** (80 W / 16 L = 96 trade · +3.3pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.7%** (13 W / 34 L = 47 trade · -52.3pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0885 |
| 2 | `adx_M30=[35,+∞)` | 0.0530 |
| 3 | `mtf_trend=all_up` | 0.0478 |
| 4 | `mtf_trend=mixed` | 0.0459 |
| 5 | `M30_ema_stack=up` | 0.0442 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0431 |
| 7 | `M30_adx_label=trending` | 0.0358 |
| 8 | `dist_low_M30=[1.5,+∞)` | 0.0293 |
| 9 | `M30_ema_stack=mixed` | 0.0248 |
| 10 | `H1_ema_stack=up` | 0.0239 |
| 11 | `H4_ema_stack=down` | 0.0237 |
| 12 | `adx_H4=[18,25)` | 0.0231 |
| 13 | `H1_ema_stack=mixed` | 0.0176 |
| 14 | `dow=Fri` | 0.0174 |
| 15 | `dow=Mon` | 0.0173 |

---

## USOIL.FOREX · ml:main · BUY
- Toplam çözülmüş: **308**  ·  Baseline win-rate: **28.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -28.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -28.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack ≠ down`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -23.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `H1_ema_stack = down`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -20.5pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ mixed`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · 1.4pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `adx_H4 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0735 |
| 2 | `H4_ema_stack=down` | 0.0728 |
| 3 | `H4_ema_stack=mixed` | 0.0518 |
| 4 | `H4_adx_label=trending` | 0.0430 |
| 5 | `H1_ema_stack=down` | 0.0407 |
| 6 | `H1_ema_stack=up` | 0.0285 |
| 7 | `adx_H4=[−∞,18)` | 0.0276 |
| 8 | `vix_chg1d=[0,3)` | 0.0228 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0221 |
| 10 | `adx_H4=[18,25)` | 0.0205 |
| 11 | `macro_alignment=strong_against` | 0.0198 |
| 12 | `adx_H4=[35,+∞)` | 0.0189 |
| 13 | `regime_label=transition` | 0.0182 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0168 |
| 15 | `rsi_H4=[65,75)` | 0.0158 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **430**  ·  Baseline win-rate: **79.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (35 W / 0 L = 35 trade · +20.7pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 100.0%** (123 W / 0 L = 123 trade · +20.7pp vs baseline)
   - `H4_ema_stack = up`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +15.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack = down`
   - `dow = Fri`

**4. Win-rate 85.4%** (35 W / 6 L = 41 trade · +6.1pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -59.3pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack ≠ down`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0671 |
| 2 | `mtf_trend=mixed` | 0.0563 |
| 3 | `adx_M30=[35,+∞)` | 0.0556 |
| 4 | `mtf_trend=all_up` | 0.0484 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0461 |
| 6 | `M30_adx_label=trending` | 0.0406 |
| 7 | `M30_ema_stack=up` | 0.0397 |
| 8 | `H1_ema_stack=mixed` | 0.0261 |
| 9 | `H1_ema_stack=up` | 0.0228 |
| 10 | `M30_ema_stack=mixed` | 0.0223 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0217 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0211 |
| 13 | `H4_ema_stack=down` | 0.0201 |
| 14 | `dow=Fri` | 0.0164 |
| 15 | `dow=Mon` | 0.0160 |

---

## USOIL.FOREX · ml:ultra_safe · BUY
- Toplam çözülmüş: **308**  ·  Baseline win-rate: **28.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -28.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 0.0%** (0 W / 21 L = 21 trade · -28.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [30,50)`
   - `H1_adx_label ≠ trending`

**3. Win-rate 0.0%** (0 W / 23 L = 23 trade · -28.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [30,50)`
   - `H1_adx_label = trending`

**4. Win-rate 5.0%** (1 W / 19 L = 20 trade · -23.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [30,50)`

**5. Win-rate 8.1%** (3 W / 34 L = 37 trade · -20.5pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ mixed`

**6. Win-rate 30.0%** (6 W / 14 L = 20 trade · 1.4pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `adx_H4 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0748 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0735 |
| 3 | `H4_ema_stack=mixed` | 0.0525 |
| 4 | `H4_adx_label=trending` | 0.0438 |
| 5 | `H1_ema_stack=down` | 0.0422 |
| 6 | `H1_ema_stack=up` | 0.0289 |
| 7 | `adx_H4=[−∞,18)` | 0.0275 |
| 8 | `vix_chg1d=[0,3)` | 0.0228 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0224 |
| 10 | `adx_H4=[18,25)` | 0.0206 |
| 11 | `adx_H4=[35,+∞)` | 0.0196 |
| 12 | `macro_alignment=strong_against` | 0.0194 |
| 13 | `regime_label=transition` | 0.0171 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0164 |
| 15 | `macro_alignment=neutral` | 0.0159 |

---

## USOIL.FOREX · ml:ultra_safe · SELL
- Toplam çözülmüş: **429**  ·  Baseline win-rate: **79.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (35 W / 0 L = 35 trade · +20.5pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 100.0%** (123 W / 0 L = 123 trade · +20.5pp vs baseline)
   - `H4_ema_stack = up`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +15.7pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack = down`
   - `dow = Fri`

**4. Win-rate 85.4%** (35 W / 6 L = 41 trade · +5.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -59.5pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_M30 ≠ [35,+∞)`
   - `H1_ema_stack ≠ down`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0745 |
| 2 | `adx_M30=[35,+∞)` | 0.0564 |
| 3 | `mtf_trend=all_up` | 0.0557 |
| 4 | `M30_ema_stack=up` | 0.0484 |
| 5 | `mtf_trend=mixed` | 0.0428 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0418 |
| 7 | `M30_adx_label=trending` | 0.0407 |
| 8 | `H4_ema_stack=down` | 0.0238 |
| 9 | `H1_ema_stack=mixed` | 0.0232 |
| 10 | `M30_ema_stack=mixed` | 0.0227 |
| 11 | `H1_ema_stack=up` | 0.0219 |
| 12 | `dist_low_M30=[1.5,+∞)` | 0.0209 |
| 13 | `dow=Fri` | 0.0206 |
| 14 | `adx_H4=[18,25)` | 0.0190 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0152 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **2427**  ·  Baseline win-rate: **13.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 42 L = 42 trade · -13.7pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_adx_label ≠ trending`
   - `H1_adx_label ≠ ranging`
   - `volatility_regime = high`

**2. Win-rate 0.0%** (0 W / 53 L = 53 trade · -13.7pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**3. Win-rate 0.0%** (0 W / 36 L = 36 trade · -13.7pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `atr_ratio_M30 = [1,1.3)`

**4. Win-rate 0.0%** (0 W / 132 L = 132 trade · -13.7pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow = Thu`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H4 ≠ [25,35)`

**5. Win-rate 0.3%** (2 W / 578 L = 580 trade · -13.4pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [1.5,+∞)`
   - `H4_adx_label ≠ trending`

**6. Win-rate 0.6%** (1 W / 178 L = 179 trade · -13.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_adx_label ≠ trending`
   - `H1_adx_label = ranging`
   - `dist_high_M30 ≠ [1.5,+∞)`

**7. Win-rate 0.8%** (1 W / 124 L = 125 trade · -12.9pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `adx_M30 ≠ [25,35)`

**8. Win-rate 2.6%** (1 W / 38 L = 39 trade · -11.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow ≠ Thu`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `vix_chg1d = [−∞,-3)`

**9. Win-rate 4.1%** (6 W / 141 L = 147 trade · -9.6pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [1.5,+∞)`
   - `H4_adx_label = trending`

**10. Win-rate 8.7%** (2 W / 21 L = 23 trade · -5.0pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow = Thu`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H4 = [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=mixed` | 0.0635 |
| 2 | `vix_chg1d=[−∞,-3)` | 0.0533 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0366 |
| 4 | `H4_ema_stack=up` | 0.0327 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 6 | `mtf_trend=mixed` | 0.0278 |
| 7 | `macro_alignment=strong_pro` | 0.0238 |
| 8 | `mtf_trend=all_up` | 0.0228 |
| 9 | `dow=Mon` | 0.0222 |
| 10 | `M30_adx_label=trending` | 0.0213 |
| 11 | `dow=Thu` | 0.0174 |
| 12 | `H4_ema_stack=down` | 0.0167 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0155 |
| 14 | `adx_H1=[−∞,18)` | 0.0142 |
| 15 | `regime_label=transition` | 0.0139 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **1746**  ·  Baseline win-rate: **79.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +20.5pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d = [3,+∞)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 100.0%** (335 W / 0 L = 335 trade · +20.5pp vs baseline)
   - `H4_ema_stack = up`
   - `atr_ratio_M30 ≠ [1.7,+∞)`
   - `dist_low_M30 ≠ [0.3,0.7)`

**3. Win-rate 100.0%** (25 W / 0 L = 25 trade · +20.5pp vs baseline)
   - `H4_ema_stack = up`
   - `atr_ratio_M30 ≠ [1.7,+∞)`
   - `dist_low_M30 = [0.3,0.7)`

**4. Win-rate 98.9%** (279 W / 3 L = 282 trade · +19.4pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label = trending`
   - `regime_label = ranging`

**5. Win-rate 97.4%** (37 W / 1 L = 38 trade · +17.9pp vs baseline)
   - `H4_ema_stack = up`
   - `atr_ratio_M30 = [1.7,+∞)`

**6. Win-rate 81.0%** (209 W / 49 L = 258 trade · +1.5pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `M30_ema_stack ≠ down`

**7. Win-rate 81.0%** (315 W / 74 L = 389 trade · +1.5pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label = trending`
   - `regime_label ≠ ranging`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.9%** (17 W / 78 L = 95 trade · -61.6pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d = [3,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `H4_ema_stack = mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0638 |
| 2 | `M30_adx_label=trending` | 0.0634 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0590 |
| 4 | `mtf_trend=all_up` | 0.0482 |
| 5 | `adx_M30=[35,+∞)` | 0.0341 |
| 6 | `adx_H1=[−∞,18)` | 0.0310 |
| 7 | `H1_adx_label=ranging` | 0.0253 |
| 8 | `M30_adx_label=ranging` | 0.0206 |
| 9 | `H4_ema_stack=mixed` | 0.0197 |
| 10 | `adx_M30=[−∞,18)` | 0.0187 |
| 11 | `H4_adx_label=trending` | 0.0186 |
| 12 | `dow=Mon` | 0.0181 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0179 |
| 14 | `H1_ema_stack=up` | 0.0175 |
| 15 | `H4_ema_stack=down` | 0.0163 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **1156**  ·  Baseline win-rate: **15.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 501 L = 501 trade · -15.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `dow ≠ Wed`
   - `us10y_chg1d ≠ [0,0.5)`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -15.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `dow ≠ Wed`
   - `us10y_chg1d = [0,0.5)`
   - `session_phase ≠ late_pit`

**3. Win-rate 0.0%** (0 W / 101 L = 101 trade · -15.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `dow = Wed`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 0.0%** (0 W / 84 L = 84 trade · -15.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `adx_M30 ≠ [−∞,18)`

**5. Win-rate 0.0%** (0 W / 22 L = 22 trade · -15.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `adx_M30 = [−∞,18)`

**6. Win-rate 2.1%** (1 W / 47 L = 48 trade · -13.0pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `H4_adx_label ≠ trending`

**7. Win-rate 9.5%** (2 W / 19 L = 21 trade · -5.6pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `dow ≠ Wed`
   - `us10y_chg1d = [0,0.5)`
   - `session_phase = late_pit`

**8. Win-rate 23.7%** (9 W / 29 L = 38 trade · 8.6pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `dow = Wed`
   - `adx_M30 ≠ [35,+∞)`

**9. Win-rate 32.4%** (11 W / 23 L = 34 trade · 17.3pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d = [3,+∞)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=mixed` | 0.1440 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0947 |
| 3 | `H4_ema_stack=down` | 0.0469 |
| 4 | `mtf_trend=mixed` | 0.0456 |
| 5 | `H4_adx_label=trending` | 0.0412 |
| 6 | `H1_ema_stack=down` | 0.0411 |
| 7 | `mtf_trend=all_up` | 0.0396 |
| 8 | `H4_ema_stack=up` | 0.0346 |
| 9 | `H4_adx_label=weak_trend` | 0.0296 |
| 10 | `H1_ema_stack=up` | 0.0221 |
| 11 | `rsi_H4=[65,75)` | 0.0210 |
| 12 | `vix_chg1d=[0,3)` | 0.0208 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0202 |
| 14 | `H1_adx_label=trending` | 0.0198 |
| 15 | `adx_H4=[18,25)` | 0.0187 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **1114**  ·  Baseline win-rate: **73.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +26.4pp vs baseline)
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `H4_ema_stack = up`

**2. Win-rate 97.6%** (483 W / 12 L = 495 trade · +24.0pp vs baseline)
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `rsi_H4 = [30,50)`

**3. Win-rate 93.3%** (28 W / 2 L = 30 trade · +19.7pp vs baseline)
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `vix_chg1d = [−∞,-3)`

**4. Win-rate 81.2%** (26 W / 6 L = 32 trade · +7.6pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label = strong_trend_down`

**5. Win-rate 79.7%** (59 W / 15 L = 74 trade · +6.1pp vs baseline)
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `rsi_H4 ≠ [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.3%** (4 W / 51 L = 55 trade · -66.3pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label ≠ strong_trend_down`
   - `rsi_H1 ≠ [30,50)`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 23.3%** (7 W / 23 L = 30 trade · -50.3pp vs baseline)
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `vix_chg1d ≠ [−∞,-3)`
   - `ml_confidence_bucket ≠ [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.1094 |
| 2 | `adx_M30=[35,+∞)` | 0.0908 |
| 3 | `dow=Mon` | 0.0364 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0360 |
| 5 | `M30_adx_label=ranging` | 0.0327 |
| 6 | `vix_chg1d=[−∞,-3)` | 0.0325 |
| 7 | `adx_M30=[−∞,18)` | 0.0312 |
| 8 | `M30_adx_label=weak_trend` | 0.0306 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0279 |
| 10 | `adx_M30=[18,25)` | 0.0273 |
| 11 | `mtf_trend=mixed` | 0.0171 |
| 12 | `macro_alignment=neutral` | 0.0147 |
| 13 | `rsi_M30=[30,50)` | 0.0142 |
| 14 | `H1_ema_stack=down` | 0.0132 |
| 15 | `H1_ema_stack=mixed` | 0.0130 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **1935**  ·  Baseline win-rate: **13.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 210 L = 210 trade · -13.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack ≠ up`
   - `H1_ema_stack = down`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 0.0%** (0 W / 559 L = 559 trade · -13.1pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack = up`
   - `vix_chg1d ≠ [3,+∞)`
   - `session_phase ≠ active_pit`

**3. Win-rate 0.0%** (0 W / 21 L = 21 trade · -13.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow ≠ Thu`
   - `dow = Fri`
   - `ml_confidence_bucket ≠ [60,70)`

**4. Win-rate 0.0%** (0 W / 31 L = 31 trade · -13.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow ≠ Thu`
   - `dow = Fri`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 0.0%** (0 W / 135 L = 135 trade · -13.1pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow = Thu`
   - `adx_H4 ≠ [25,35)`

**6. Win-rate 1.5%** (3 W / 196 L = 199 trade · -11.6pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack = up`
   - `vix_chg1d = [3,+∞)`
   - `dow = Mon`

**7. Win-rate 2.3%** (1 W / 43 L = 44 trade · -10.8pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack = up`
   - `vix_chg1d ≠ [3,+∞)`
   - `session_phase = active_pit`

**8. Win-rate 6.9%** (4 W / 54 L = 58 trade · -6.2pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack ≠ up`
   - `H1_ema_stack ≠ down`
   - `adx_H1 = [−∞,18)`

**9. Win-rate 7.4%** (2 W / 25 L = 27 trade · -5.7pp vs baseline)
   - `H4_ema_stack = mixed`
   - `dow = Thu`
   - `adx_H4 = [25,35)`
   - `rsi_H4 ≠ [50,65)`

**10. Win-rate 11.8%** (10 W / 75 L = 85 trade · -1.3pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `M30_ema_stack ≠ up`
   - `H1_ema_stack = down`
   - `dist_high_M30 = [1.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=mixed` | 0.0695 |
| 2 | `mtf_trend=mixed` | 0.0482 |
| 3 | `H4_adx_label=trending` | 0.0422 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0421 |
| 5 | `H4_ema_stack=up` | 0.0386 |
| 6 | `mtf_trend=all_up` | 0.0376 |
| 7 | `H4_adx_label=weak_trend` | 0.0356 |
| 8 | `adx_H4=[18,25)` | 0.0267 |
| 9 | `H1_ema_stack=down` | 0.0264 |
| 10 | `H1_ema_stack=up` | 0.0246 |
| 11 | `vix_chg1d=[0,3)` | 0.0246 |
| 12 | `adx_H4=[25,35)` | 0.0208 |
| 13 | `H1_adx_label=trending` | 0.0206 |
| 14 | `H1_adx_label=ranging` | 0.0167 |
| 15 | `macro_alignment=strong_pro` | 0.0152 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **1666**  ·  Baseline win-rate: **83.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +16.9pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 100.0%** (58 W / 0 L = 58 trade · +16.9pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 100.0%** (23 W / 0 L = 23 trade · +16.9pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow = Mon`
   - `rsi_H1 = [50,65)`

**4. Win-rate 100.0%** (453 W / 0 L = 453 trade · +16.9pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow ≠ Mon`

**5. Win-rate 100.0%** (22 W / 0 L = 22 trade · +16.9pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow = Mon`
   - `atr_ratio_M30 = [1,1.3)`

**6. Win-rate 97.3%** (367 W / 10 L = 377 trade · +14.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`

**7. Win-rate 93.4%** (71 W / 5 L = 76 trade · +10.3pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [3,+∞)`

**8. Win-rate 85.0%** (17 W / 3 L = 20 trade · +1.9pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow = Mon`
   - `atr_ratio_M30 ≠ [1,1.3)`

**9. Win-rate 80.3%** (191 W / 47 L = 238 trade · -2.8pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow ≠ Mon`
   - `H4_adx_label = trending`

**10. Win-rate 78.8%** (26 W / 7 L = 33 trade · -4.3pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `regime_label = strong_trend_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -59.3pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 34.4%** (74 W / 141 L = 215 trade · -48.7pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `regime_label ≠ strong_trend_down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0829 |
| 2 | `adx_M30=[35,+∞)` | 0.0590 |
| 3 | `vix_chg1d=[−∞,-3)` | 0.0432 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0388 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0373 |
| 6 | `dow=Mon` | 0.0365 |
| 7 | `adx_M30=[−∞,18)` | 0.0355 |
| 8 | `M30_adx_label=ranging` | 0.0352 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0255 |
| 10 | `H4_ema_stack=up` | 0.0254 |
| 11 | `H4_ema_stack=mixed` | 0.0190 |
| 12 | `mtf_trend=mixed` | 0.0186 |
| 13 | `M30_adx_label=weak_trend` | 0.0184 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0174 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0155 |

---

## USOIL.FOREX · smc · BUY
- Toplam çözülmüş: **305**  ·  Baseline win-rate: **14.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 63 L = 63 trade · -14.8pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack ≠ mixed`

**2. Win-rate 0.0%** (0 W / 66 L = 66 trade · -14.8pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `hour_bucket ≠ 16-20`
   - `H1_adx_label ≠ trending`

**3. Win-rate 0.0%** (0 W / 22 L = 22 trade · -14.8pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `hour_bucket ≠ 16-20`
   - `H1_adx_label = trending`

**4. Win-rate 4.8%** (1 W / 20 L = 21 trade · -10.0pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `hour_bucket = 16-20`

**5. Win-rate 13.0%** (3 W / 20 L = 23 trade · -1.8pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack = mixed`

**6. Win-rate 14.3%** (5 W / 30 L = 35 trade · -0.5pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d = [0,0.5)`

**7. Win-rate 26.5%** (9 W / 25 L = 34 trade · 11.7pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_ema_stack ≠ down`
   - `rsi_M30 ≠ [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0615 |
| 2 | `M30_adx_label=ranging` | 0.0451 |
| 3 | `mtf_trend=mixed` | 0.0422 |
| 4 | `M30_adx_label=trending` | 0.0406 |
| 5 | `adx_M30=[−∞,18)` | 0.0351 |
| 6 | `M30_ema_stack=mixed` | 0.0316 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0307 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0288 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0256 |
| 10 | `rsi_H1=[30,50)` | 0.0229 |
| 11 | `hour_bucket=00-04` | 0.0227 |
| 12 | `us10y_chg1d=[0,0.5)` | 0.0217 |
| 13 | `M30_ema_stack=down` | 0.0215 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0211 |
| 15 | `rsi_H4=[30,50)` | 0.0209 |

---

## USOIL.FOREX · smc · SELL
- Toplam çözülmüş: **292**  ·  Baseline win-rate: **90.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +9.2pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label ≠ ranging`
   - `vix_chg1d ≠ [−∞,-3)`

**2. Win-rate 100.0%** (176 W / 0 L = 176 trade · +9.2pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label = ranging`
   - `adx_H4 ≠ [35,+∞)`

**3. Win-rate 95.8%** (23 W / 1 L = 24 trade · +5.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label = ranging`
   - `adx_H4 = [35,+∞)`

**4. Win-rate 84.4%** (27 W / 5 L = 32 trade · -6.4pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label ≠ ranging`
   - `vix_chg1d = [−∞,-3)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0930 |
| 2 | `vix_chg1d=[0,3)` | 0.0677 |
| 3 | `adx_M30=[35,+∞)` | 0.0539 |
| 4 | `H4_ema_stack=up` | 0.0478 |
| 5 | `adx_H1=[−∞,18)` | 0.0471 |
| 6 | `H1_ema_stack=down` | 0.0455 |
| 7 | `H1_adx_label=ranging` | 0.0412 |
| 8 | `M30_adx_label=trending` | 0.0411 |
| 9 | `H1_adx_label=trending` | 0.0314 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0266 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0220 |
| 12 | `mtf_trend=mixed` | 0.0220 |
| 13 | `adx_M30=[−∞,18)` | 0.0193 |
| 14 | `session=asia` | 0.0174 |
| 15 | `mtf_trend=all_up` | 0.0161 |

---

## XAUUSD · ai_panel · BUY
- Toplam çözülmüş: **126**  ·  Baseline win-rate: **75.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +24.6pp vs baseline)
   - `adx_H1 ≠ [25,35)`
   - `rsi_H1 ≠ [50,65)`
   - `vix_chg1d = [3,+∞)`

**2. Win-rate 90.0%** (27 W / 3 L = 30 trade · +14.6pp vs baseline)
   - `adx_H1 ≠ [25,35)`
   - `rsi_H1 ≠ [50,65)`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`

**3. Win-rate 75.0%** (15 W / 5 L = 20 trade · -0.4pp vs baseline)
   - `adx_H1 ≠ [25,35)`
   - `rsi_H1 ≠ [50,65)`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[25,35)` | 0.0527 |
| 2 | `dist_low_M30=[1.5,+∞)` | 0.0491 |
| 3 | `H1_adx_label=trending` | 0.0456 |
| 4 | `mtf_trend=all_up` | 0.0394 |
| 5 | `rsi_M30=[50,65)` | 0.0381 |
| 6 | `adx_H1=[18,25)` | 0.0377 |
| 7 | `H1_adx_label=weak_trend` | 0.0359 |
| 8 | `M30_ema_stack=up` | 0.0335 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0287 |
| 10 | `dist_low_M30=[0.3,0.7)` | 0.0270 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0264 |
| 12 | `sar_bearish=False` | 0.0243 |
| 13 | `atr_ratio_M30=[0.7,1)` | 0.0243 |
| 14 | `rsi_H1=[30,50)` | 0.0218 |
| 15 | `mtf_trend=mixed` | 0.0210 |

---

## XAUUSD · emel · BUY
- Toplam çözülmüş: **246**  ·  Baseline win-rate: **79.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +20.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 = [−∞,0.2)`

**2. Win-rate 100.0%** (33 W / 0 L = 33 trade · +20.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [1,1.3)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 95.0%** (19 W / 1 L = 20 trade · +15.3pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [1,1.3)`
   - `us10y_chg1d = [0.5,+∞)`

**4. Win-rate 87.5%** (21 W / 3 L = 24 trade · +7.8pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**5. Win-rate 82.6%** (19 W / 4 L = 23 trade · +2.9pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment ≠ weak_against`
   - `atr_ratio_M30 ≠ [0.7,1)`

**6. Win-rate 81.8%** (27 W / 6 L = 33 trade · +2.1pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -44.7pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend ≠ all_down`
   - `M30_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0629 |
| 2 | `dxy_chg1d=[-0.5,0)` | 0.0544 |
| 3 | `macro_alignment=weak_against` | 0.0509 |
| 4 | `adx_H1=[35,+∞)` | 0.0453 |
| 5 | `adx_M30=[35,+∞)` | 0.0393 |
| 6 | `M30_ema_stack=down` | 0.0373 |
| 7 | `mtf_trend=all_down` | 0.0347 |
| 8 | `dist_low_M30=[1.5,+∞)` | 0.0308 |
| 9 | `atr_ratio_M30=[1,1.3)` | 0.0240 |
| 10 | `atr_ratio_M30=[0.7,1)` | 0.0218 |
| 11 | `rsi_H1=[30,50)` | 0.0206 |
| 12 | `consec_red_M30=[2,4)` | 0.0194 |
| 13 | `rsi_M30=[50,65)` | 0.0190 |
| 14 | `rsi_M30=[30,50)` | 0.0185 |
| 15 | `rsi_H1=[50,65)` | 0.0184 |

---

## XAUUSD · emel_inv · SELL
- Toplam çözülmüş: **119**  ·  Baseline win-rate: **27.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 28 L = 28 trade · -27.7pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 = [1,1.3)`

**2. Win-rate 14.3%** (3 W / 18 L = 21 trade · -13.4pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_pro`

**3. Win-rate 30.8%** (8 W / 18 L = 26 trade · 3.1pp vs baseline)
   - `dxy_chg1d ≠ [0,0.5)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**4. Win-rate 34.8%** (8 W / 15 L = 23 trade · 7.1pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment ≠ weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0697 |
| 2 | `dxy_chg1d=[0,0.5)` | 0.0692 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0662 |
| 4 | `adx_H1=[35,+∞)` | 0.0626 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0473 |
| 6 | `adx_H1=[18,25)` | 0.0463 |
| 7 | `macro_alignment=weak_pro` | 0.0348 |
| 8 | `bb_pctb_M30=[0.5,0.8)` | 0.0335 |
| 9 | `H1_adx_label=trending` | 0.0329 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0241 |
| 11 | `rsi_H1=[50,65)` | 0.0205 |
| 12 | `H1_adx_label=weak_trend` | 0.0202 |
| 13 | `adx_M30=[25,35)` | 0.0195 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0181 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0172 |

---

## XAUUSD · ml:aggressive · BUY
- Toplam çözülmüş: **321**  ·  Baseline win-rate: **63.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.3%** (28 W / 3 L = 31 trade · +27.1pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 88.0%** (22 W / 3 L = 25 trade · +24.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (14 W / 28 L = 42 trade · -29.9pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[0.5,+∞)` | 0.0363 |
| 2 | `macro_alignment=weak_against` | 0.0294 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0285 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0256 |
| 5 | `session=overlap` | 0.0227 |
| 6 | `M30_ema_stack=down` | 0.0227 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0224 |
| 8 | `mtf_trend=all_down` | 0.0194 |
| 9 | `adx_M30=[25,35)` | 0.0192 |
| 10 | `adx_H1=[35,+∞)` | 0.0191 |
| 11 | `adx_H1=[25,35)` | 0.0184 |
| 12 | `M30_adx_label=ranging` | 0.0179 |
| 13 | `macro_alignment=weak_pro` | 0.0170 |
| 14 | `adx_M30=[35,+∞)` | 0.0167 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0155 |

---

## XAUUSD · ml:aggressive · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **29.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -26.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 13.0%** (3 W / 20 L = 23 trade · -16.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `macro_alignment = weak_pro`

**3. Win-rate 18.5%** (5 W / 22 L = 27 trade · -11.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**4. Win-rate 30.4%** (7 W / 16 L = 23 trade · 0.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `macro_alignment ≠ weak_pro`

**5. Win-rate 31.0%** (9 W / 20 L = 29 trade · 1.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment = neutral`

**6. Win-rate 33.3%** (8 W / 16 L = 24 trade · 3.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment ≠ neutral`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0882 |
| 2 | `adx_H1=[35,+∞)` | 0.0522 |
| 3 | `macro_alignment=weak_pro` | 0.0258 |
| 4 | `macro_alignment=strong_against` | 0.0243 |
| 5 | `dist_low_M30=[1.5,+∞)` | 0.0237 |
| 6 | `M30_ema_stack=up` | 0.0232 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0221 |
| 8 | `mtf_trend=all_down` | 0.0214 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0208 |
| 10 | `rsi_M30=[30,50)` | 0.0200 |
| 11 | `mtf_trend=mixed` | 0.0199 |
| 12 | `adx_M30=[25,35)` | 0.0197 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0185 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0171 |
| 15 | `M30_ema_stack=down` | 0.0169 |

---

## XAUUSD · ml:balanced · BUY
- Toplam çözülmüş: **327**  ·  Baseline win-rate: **63.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.3%** (28 W / 3 L = 31 trade · +27.3pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 88.9%** (24 W / 3 L = 27 trade · +25.9pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (14 W / 28 L = 42 trade · -29.7pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[0.5,+∞)` | 0.0294 |
| 2 | `macro_alignment=weak_against` | 0.0289 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0280 |
| 4 | `adx_H1=[25,35)` | 0.0235 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0223 |
| 6 | `adx_H1=[35,+∞)` | 0.0221 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0209 |
| 8 | `M30_ema_stack=down` | 0.0209 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0200 |
| 10 | `dist_low_M30=[1.5,+∞)` | 0.0194 |
| 11 | `mtf_trend=all_down` | 0.0192 |
| 12 | `M30_ema_stack=up` | 0.0171 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0165 |
| 14 | `macro_alignment=weak_pro` | 0.0165 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0158 |

---

## XAUUSD · ml:balanced · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **27.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.1%** (1 W / 31 L = 32 trade · -24.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 8.3%** (2 W / 22 L = 24 trade · -19.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `sar_bearish ≠ False`

**3. Win-rate 14.8%** (4 W / 23 L = 27 trade · -12.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**4. Win-rate 27.3%** (6 W / 16 L = 22 trade · -0.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `sar_bearish = False`

**5. Win-rate 28.6%** (8 W / 20 L = 28 trade · 1.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment = neutral`

**6. Win-rate 33.3%** (8 W / 16 L = 24 trade · 5.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment ≠ neutral`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0906 |
| 2 | `adx_H1=[35,+∞)` | 0.0556 |
| 3 | `macro_alignment=strong_against` | 0.0323 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0269 |
| 5 | `mtf_trend=mixed` | 0.0257 |
| 6 | `dist_low_M30=[0.7,1.5)` | 0.0250 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0243 |
| 8 | `macro_alignment=weak_pro` | 0.0236 |
| 9 | `M30_adx_label=weak_trend` | 0.0231 |
| 10 | `dow=Thu` | 0.0230 |
| 11 | `H1_adx_label=trending` | 0.0203 |
| 12 | `M30_ema_stack=mixed` | 0.0185 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0183 |
| 14 | `mtf_trend=all_down` | 0.0178 |
| 15 | `M30_adx_label=trending` | 0.0177 |

---

## XAUUSD · ml:full_power · BUY
- Toplam çözülmüş: **320**  ·  Baseline win-rate: **62.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.0%** (23 W / 2 L = 25 trade · +29.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `macro_alignment = neutral`

**2. Win-rate 88.0%** (22 W / 3 L = 25 trade · +25.5pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 31.7%** (13 W / 28 L = 41 trade · -30.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0397 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0343 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0327 |
| 4 | `adx_H1=[25,35)` | 0.0259 |
| 5 | `macro_alignment=weak_against` | 0.0215 |
| 6 | `mtf_trend=all_down` | 0.0205 |
| 7 | `adx_H1=[35,+∞)` | 0.0204 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0202 |
| 9 | `rsi_M30=[30,50)` | 0.0195 |
| 10 | `consec_red_M30=[0,2)` | 0.0182 |
| 11 | `session=asia` | 0.0163 |
| 12 | `macd_atr_M30=[-0.3,0)` | 0.0158 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0158 |
| 14 | `adx_M30=[35,+∞)` | 0.0156 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0154 |

---

## XAUUSD · ml:full_power · SELL
- Toplam çözülmüş: **196**  ·  Baseline win-rate: **28.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -24.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`

**2. Win-rate 13.6%** (3 W / 19 L = 22 trade · -14.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 14.8%** (4 W / 23 L = 27 trade · -13.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**4. Win-rate 26.1%** (6 W / 17 L = 23 trade · -2.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`
   - `ml_confidence_bucket ≠ [80,+∞)`

**5. Win-rate 27.6%** (8 W / 21 L = 29 trade · -0.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment = neutral`

**6. Win-rate 34.8%** (8 W / 15 L = 23 trade · 6.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment ≠ neutral`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0849 |
| 2 | `adx_H1=[35,+∞)` | 0.0531 |
| 3 | `macro_alignment=strong_against` | 0.0332 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0276 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0276 |
| 6 | `dow=Thu` | 0.0220 |
| 7 | `M30_adx_label=trending` | 0.0219 |
| 8 | `mtf_trend=mixed` | 0.0217 |
| 9 | `H1_adx_label=trending` | 0.0216 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0215 |
| 11 | `rsi_H1=[30,50)` | 0.0213 |
| 12 | `macd_atr_M30=[0,0.3)` | 0.0211 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0206 |
| 14 | `macro_alignment=weak_pro` | 0.0194 |
| 15 | `hour_bucket=12-16` | 0.0188 |

---

## XAUUSD · ml:main · BUY
- Toplam çözülmüş: **319**  ·  Baseline win-rate: **63.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.3%** (28 W / 2 L = 30 trade · +29.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 92.0%** (23 W / 2 L = 25 trade · +28.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.6%** (14 W / 29 L = 43 trade · -31.3pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0464 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0389 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0322 |
| 4 | `macro_alignment=weak_against` | 0.0274 |
| 5 | `adx_H1=[25,35)` | 0.0263 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0246 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0235 |
| 8 | `bb_pctb_M30=[−∞,0.2)` | 0.0211 |
| 9 | `adx_H1=[35,+∞)` | 0.0211 |
| 10 | `mtf_trend=all_down` | 0.0203 |
| 11 | `M30_ema_stack=down` | 0.0199 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0191 |
| 13 | `rsi_M30=[30,50)` | 0.0174 |
| 14 | `rsi_H1=[30,50)` | 0.0164 |
| 15 | `H1_adx_label=trending` | 0.0153 |

---

## XAUUSD · ml:main · SELL
- Toplam çözülmüş: **198**  ·  Baseline win-rate: **27.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.1%** (1 W / 31 L = 32 trade · -24.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`

**2. Win-rate 14.3%** (3 W / 18 L = 21 trade · -13.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 14.8%** (4 W / 23 L = 27 trade · -13.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**4. Win-rate 27.6%** (8 W / 21 L = 29 trade · -0.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment = neutral`

**5. Win-rate 28.0%** (7 W / 18 L = 25 trade · 0.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`
   - `ml_confidence_bucket ≠ [80,+∞)`

**6. Win-rate 33.3%** (8 W / 16 L = 24 trade · 5.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment ≠ neutral`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0697 |
| 2 | `adx_H1=[35,+∞)` | 0.0475 |
| 3 | `macro_alignment=strong_against` | 0.0303 |
| 4 | `mtf_trend=mixed` | 0.0254 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0249 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0222 |
| 7 | `dist_low_M30=[1.5,+∞)` | 0.0220 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0218 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0217 |
| 10 | `vix_chg1d=[0,3)` | 0.0213 |
| 11 | `macro_alignment=weak_pro` | 0.0206 |
| 12 | `rsi_H1=[30,50)` | 0.0196 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0192 |
| 14 | `mtf_trend=all_up` | 0.0187 |
| 15 | `M30_ema_stack=down` | 0.0182 |

---

## XAUUSD · ml:main_inv · SELL
- Toplam çözülmüş: **164**  ·  Baseline win-rate: **39.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.0%** (19 W / 6 L = 25 trade · +36.4pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [0,2)`
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -29.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 = [2,4)`

**2. Win-rate 23.3%** (7 W / 23 L = 30 trade · -16.3pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 ≠ [2,4)`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 35.0%** (7 W / 13 L = 20 trade · -4.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0935 |
| 2 | `adx_M30=[35,+∞)` | 0.0717 |
| 3 | `consec_red_M30=[2,4)` | 0.0524 |
| 4 | `consec_red_M30=[0,2)` | 0.0398 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0384 |
| 6 | `macro_alignment=weak_pro` | 0.0376 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0277 |
| 8 | `dist_high_M30=[1.5,+∞)` | 0.0273 |
| 9 | `session=asia` | 0.0223 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0184 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0183 |
| 12 | `H1_adx_label=trending` | 0.0174 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0173 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0166 |
| 15 | `mtf_trend=all_up` | 0.0161 |

---

## XAUUSD · ml:ultra_safe · BUY
- Toplam çözülmüş: **324**  ·  Baseline win-rate: **63.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.0%** (23 W / 2 L = 25 trade · +29.0pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 90.3%** (28 W / 3 L = 31 trade · +27.3pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (14 W / 28 L = 42 trade · -29.7pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[0.5,+∞)` | 0.0326 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0285 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0277 |
| 4 | `mtf_trend=all_down` | 0.0273 |
| 5 | `macro_alignment=weak_against` | 0.0271 |
| 6 | `M30_ema_stack=down` | 0.0250 |
| 7 | `adx_H1=[25,35)` | 0.0240 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0226 |
| 9 | `adx_M30=[25,35)` | 0.0219 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0208 |
| 11 | `M30_adx_label=trending` | 0.0202 |
| 12 | `adx_H1=[35,+∞)` | 0.0190 |
| 13 | `H1_adx_label=trending` | 0.0175 |
| 14 | `rsi_M30=[30,50)` | 0.0172 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0169 |

---

## XAUUSD · ml:ultra_safe · SELL
- Toplam çözülmüş: **194**  ·  Baseline win-rate: **27.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -24.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 9.5%** (2 W / 19 L = 21 trade · -18.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `macd_atr_M30 = [-0.3,0)`

**3. Win-rate 14.8%** (4 W / 23 L = 27 trade · -13.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**4. Win-rate 25.9%** (7 W / 20 L = 27 trade · -1.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment = neutral`

**5. Win-rate 29.2%** (7 W / 17 L = 24 trade · 1.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**6. Win-rate 34.8%** (8 W / 15 L = 23 trade · 7.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `macro_alignment ≠ neutral`
   - `consec_green_M30 ≠ [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0814 |
| 2 | `adx_H1=[35,+∞)` | 0.0399 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0331 |
| 4 | `macro_alignment=strong_against` | 0.0326 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0262 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0239 |
| 7 | `adx_M30=[18,25)` | 0.0227 |
| 8 | `mtf_trend=all_down` | 0.0220 |
| 9 | `M30_ema_stack=mixed` | 0.0212 |
| 10 | `mtf_trend=mixed` | 0.0205 |
| 11 | `vix_chg1d=[0,3)` | 0.0202 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0201 |
| 13 | `rsi_H1=[30,50)` | 0.0194 |
| 14 | `dow=Thu` | 0.0189 |
| 15 | `macd_atr_M30=[0,0.3)` | 0.0178 |

---

## XAUUSD · ml_cross_xau_nasdaq · BUY
- Toplam çözülmüş: **485**  ·  Baseline win-rate: **56.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (68 W / 0 L = 68 trade · +43.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ neutral`

**2. Win-rate 86.0%** (49 W / 8 L = 57 trade · +29.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 85.0%** (17 W / 3 L = 20 trade · +28.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment = neutral`

**4. Win-rate 75.9%** (22 W / 7 L = 29 trade · +19.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = neutral`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.0%** (27 W / 96 L = 123 trade · -34.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ neutral`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 00-04`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1251 |
| 2 | `macro_alignment=weak_against` | 0.0533 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0488 |
| 4 | `adx_H1=[35,+∞)` | 0.0365 |
| 5 | `M30_adx_label=trending` | 0.0339 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0275 |
| 7 | `M30_adx_label=weak_trend` | 0.0264 |
| 8 | `dow=Mon` | 0.0222 |
| 9 | `adx_M30=[18,25)` | 0.0214 |
| 10 | `mtf_trend=NA` | 0.0201 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0198 |
| 12 | `dow=Fri` | 0.0197 |
| 13 | `macro_alignment=neutral` | 0.0190 |
| 14 | `M30_ema_stack=NA` | 0.0189 |
| 15 | `vix_chg1d=[0,3)` | 0.0185 |

---

## XAUUSD · ml_cross_xau_nasdaq · SELL
- Toplam çözülmüş: **242**  ·  Baseline win-rate: **12.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 26 L = 26 trade · -12.4pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow ≠ Mon`
   - `rsi_M30 = [−∞,30)`

**2. Win-rate 0.0%** (0 W / 69 L = 69 trade · -12.4pp vs baseline)
   - `dxy_chg1d = [0.5,+∞)`

**3. Win-rate 7.8%** (6 W / 71 L = 77 trade · -4.6pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow ≠ Mon`
   - `rsi_M30 ≠ [−∞,30)`
   - `hour_bucket ≠ 00-04`

**4. Win-rate 30.4%** (7 W / 16 L = 23 trade · 18.0pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow = Mon`
   - `dist_low_M30 = [0.7,1.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0.5,+∞)` | 0.0905 |
| 2 | `dow=Thu` | 0.0808 |
| 3 | `us10y_chg1d=[−∞,-0.5)` | 0.0597 |
| 4 | `dow=Mon` | 0.0579 |
| 5 | `hour_bucket=00-04` | 0.0425 |
| 6 | `adx_H1=[−∞,18)` | 0.0337 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0333 |
| 8 | `near_support=False` | 0.0244 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0220 |
| 10 | `macro_alignment=weak_pro` | 0.0214 |
| 11 | `H1_adx_label=ranging` | 0.0212 |
| 12 | `near_support=True` | 0.0199 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0182 |
| 14 | `adx_H1=[35,+∞)` | 0.0174 |
| 15 | `macro_alignment=neutral` | 0.0166 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · BUY
- Toplam çözülmüş: **113**  ·  Baseline win-rate: **52.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (23 W / 5 L = 28 trade · +29.9pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.9%** (8 W / 27 L = 35 trade · -29.3pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0941 |
| 2 | `adx_H1=[35,+∞)` | 0.0736 |
| 3 | `dow=Mon` | 0.0597 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0416 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0411 |
| 6 | `adx_H1=[25,35)` | 0.0388 |
| 7 | `H1_adx_label=trending` | 0.0373 |
| 8 | `adx_H1=[18,25)` | 0.0350 |
| 9 | `consec_red_M30=[0,2)` | 0.0323 |
| 10 | `adx_M30=[25,35)` | 0.0297 |
| 11 | `atr_ratio_M30=[0.7,1)` | 0.0291 |
| 12 | `hour_bucket=00-04` | 0.0250 |
| 13 | `dist_low_M30=[0.7,1.5)` | 0.0246 |
| 14 | `bb_pctb_M30=[−∞,0.2)` | 0.0243 |
| 15 | `sar_bearish=True` | 0.0237 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · SELL
- Toplam çözülmüş: **404**  ·  Baseline win-rate: **21.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -21.0pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend ≠ mixed`

**2. Win-rate 3.1%** (1 W / 31 L = 32 trade · -17.9pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -16.5pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 = NA`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 4.8%** (1 W / 20 L = 21 trade · -16.2pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend = mixed`

**5. Win-rate 6.7%** (2 W / 28 L = 30 trade · -14.3pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 ≠ NA`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [-3,0)`

**6. Win-rate 9.5%** (2 W / 19 L = 21 trade · -11.5pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 = [50,65)`

**7. Win-rate 11.4%** (4 W / 31 L = 35 trade · -9.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [3,+∞)`

**8. Win-rate 20.0%** (4 W / 16 L = 20 trade · -1.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 = NA`
   - `adx_M30 ≠ [35,+∞)`

**9. Win-rate 25.0%** (10 W / 30 L = 40 trade · 4.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 ≠ NA`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `bb_pctb_M30 = [0.2,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0613 |
| 2 | `adx_M30=[35,+∞)` | 0.0418 |
| 3 | `M30_adx_label=trending` | 0.0405 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0342 |
| 5 | `macro_alignment=weak_pro` | 0.0332 |
| 6 | `hour_bucket=12-16` | 0.0219 |
| 7 | `vix_chg1d=[0,3)` | 0.0211 |
| 8 | `mtf_trend=all_up` | 0.0206 |
| 9 | `adx_H1=[25,35)` | 0.0204 |
| 10 | `M30_ema_stack=up` | 0.0200 |
| 11 | `dist_high_M30=[1.5,+∞)` | 0.0198 |
| 12 | `bb_pctb_M30=[0.2,0.5)` | 0.0188 |
| 13 | `H1_adx_label=trending` | 0.0187 |
| 14 | `macro_alignment=strong_pro` | 0.0184 |
| 15 | `rsi_H1=[30,50)` | 0.0183 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **1055**  ·  Baseline win-rate: **42.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.2%** (47 W / 4 L = 51 trade · +49.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment ≠ strong_pro`
   - `dow = Fri`

**2. Win-rate 79.0%** (188 W / 50 L = 238 trade · +36.5pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_M30 ≠ [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 2.9%** (1 W / 33 L = 34 trade · -39.6pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [−∞,-0.5)`
   - `macd_atr_M30 = [0,0.3)`
   - `H1_adx_label ≠ trending`

**2. Win-rate 3.8%** (4 W / 102 L = 106 trade · -38.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `macro_alignment = strong_pro`
   - `dist_low_M30 = [1.5,+∞)`

**3. Win-rate 12.5%** (3 W / 21 L = 24 trade · -30.0pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment = strong_pro`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -28.2pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_M30 = [35,+∞)`

**5. Win-rate 18.5%** (10 W / 44 L = 54 trade · -24.0pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [3,+∞)`
   - `atr_ratio_M30 = [0.7,1)`

**6. Win-rate 21.4%** (6 W / 22 L = 28 trade · -21.1pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `macro_alignment = strong_pro`
   - `dist_low_M30 ≠ [1.5,+∞)`

**7. Win-rate 22.7%** (47 W / 160 L = 207 trade · -19.8pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `macro_alignment ≠ strong_pro`
   - `macd_atr_M30 ≠ [-0.3,0)`

**8. Win-rate 26.1%** (6 W / 17 L = 23 trade · -16.4pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [−∞,-0.5)`
   - `macd_atr_M30 = [0,0.3)`
   - `H1_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0492 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0449 |
| 3 | `macro_alignment=strong_pro` | 0.0410 |
| 4 | `M30_ema_stack=down` | 0.0407 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0335 |
| 6 | `dow=Fri` | 0.0257 |
| 7 | `adx_H1=[35,+∞)` | 0.0243 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0239 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0225 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0204 |
| 11 | `rsi_M30=[65,75)` | 0.0192 |
| 12 | `macro_alignment=weak_pro` | 0.0186 |
| 13 | `M30_ema_stack=up` | 0.0184 |
| 14 | `H1_adx_label=trending` | 0.0174 |
| 15 | `session=asia` | 0.0145 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **2174**  ·  Baseline win-rate: **15.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 37 L = 37 trade · -15.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme ≠ False`
   - `H1_adx_label = weak_trend`

**2. Win-rate 0.0%** (0 W / 111 L = 111 trade · -15.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d = [−∞,-3)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**3. Win-rate 0.0%** (0 W / 225 L = 225 trade · -15.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `dow ≠ Mon`
   - `macro_alignment ≠ weak_against`

**4. Win-rate 0.0%** (0 W / 81 L = 81 trade · -15.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `dow = Tue`

**5. Win-rate 2.9%** (1 W / 34 L = 35 trade · -12.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `hour_bucket = 08-12`

**6. Win-rate 3.8%** (3 W / 77 L = 80 trade · -11.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `macd_atr_M30 = [-0.3,0)`

**7. Win-rate 3.8%** (1 W / 25 L = 26 trade · -11.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d = [−∞,-3)`
   - `bb_pctb_M30 = [0.5,0.8)`

**8. Win-rate 4.6%** (4 W / 83 L = 87 trade · -11.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `dow = Mon`
   - `hour_bucket ≠ 12-16`

**9. Win-rate 7.7%** (3 W / 36 L = 39 trade · -8.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `dow ≠ Mon`
   - `macro_alignment = weak_against`

**10. Win-rate 8.2%** (5 W / 56 L = 61 trade · -7.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme ≠ False`
   - `H1_adx_label ≠ weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0393 |
| 2 | `adx_M30=[35,+∞)` | 0.0381 |
| 3 | `vix_chg1d=[0,3)` | 0.0352 |
| 4 | `macro_alignment=neutral` | 0.0342 |
| 5 | `dow=Tue` | 0.0285 |
| 6 | `dow=Thu` | 0.0206 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0197 |
| 8 | `dxy_chg1d=[0.5,+∞)` | 0.0184 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0164 |
| 10 | `M30_ema_stack=mixed` | 0.0152 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0147 |
| 12 | `atr_ratio_M30=[1,1.3)` | 0.0146 |
| 13 | `adx_H1=[35,+∞)` | 0.0145 |
| 14 | `M30_ema_stack=NA` | 0.0144 |
| 15 | `mtf_trend=mixed` | 0.0143 |

---

## XAUUSD · pulse1_inv · BUY
- Toplam çözülmüş: **517**  ·  Baseline win-rate: **57.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.3%** (150 W / 18 L = 168 trade · +31.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `volatility_regime = normal`
   - `us10y_chg1d ≠ [0,0.5)`
   - `adx_H1 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.3%** (4 W / 26 L = 30 trade · -44.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_resistance = False`
   - `macro_alignment = weak_pro`

**2. Win-rate 20.0%** (6 W / 24 L = 30 trade · -37.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_resistance = False`
   - `macro_alignment ≠ weak_pro`
   - `volatility_regime ≠ normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0954 |
| 2 | `adx_H1=[35,+∞)` | 0.0703 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0530 |
| 4 | `M30_adx_label=trending` | 0.0435 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0425 |
| 6 | `adx_M30=[25,35)` | 0.0363 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0320 |
| 8 | `adx_M30=[18,25)` | 0.0264 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0231 |
| 10 | `M30_adx_label=weak_trend` | 0.0223 |
| 11 | `macro_alignment=weak_against` | 0.0220 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0216 |
| 13 | `H1_adx_label=trending` | 0.0213 |
| 14 | `volatility_regime=normal` | 0.0158 |
| 15 | `adx_H1=[25,35)` | 0.0145 |

---

## XAUUSD · pulse1_inv · SELL
- Toplam çözülmüş: **244**  ·  Baseline win-rate: **30.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.8%** (1 W / 25 L = 26 trade · -26.9pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment = weak_pro`

**2. Win-rate 8.3%** (2 W / 22 L = 24 trade · -22.4pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `consec_green_M30 ≠ [2,4)`
   - `hour_bucket = 04-08`

**3. Win-rate 26.1%** (6 W / 17 L = 23 trade · -4.6pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `consec_green_M30 = [2,4)`
   - `H1_adx_label = trending`

**4. Win-rate 28.2%** (24 W / 61 L = 85 trade · -2.5pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `consec_green_M30 ≠ [2,4)`
   - `hour_bucket ≠ 04-08`

**5. Win-rate 31.8%** (7 W / 15 L = 22 trade · 1.1pp vs baseline)
   - `session = overlap`
   - `atr_ratio_M30 = [0.7,1)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0337 |
| 2 | `session=overlap` | 0.0319 |
| 3 | `macro_alignment=weak_pro` | 0.0312 |
| 4 | `adx_H1=[35,+∞)` | 0.0249 |
| 5 | `hour_bucket=12-16` | 0.0242 |
| 6 | `atr_ratio_M30=[0.7,1)` | 0.0235 |
| 7 | `dist_high_M30=[0.3,0.7)` | 0.0227 |
| 8 | `adx_M30=[35,+∞)` | 0.0211 |
| 9 | `consec_red_M30=[2,4)` | 0.0198 |
| 10 | `consec_green_M30=[0,2)` | 0.0195 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0191 |
| 12 | `M30_ema_stack=mixed` | 0.0176 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0175 |
| 14 | `consec_green_M30=[2,4)` | 0.0174 |
| 15 | `dist_low_M30=[0.7,1.5)` | 0.0159 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **1291**  ·  Baseline win-rate: **42.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 76.9%** (20 W / 6 L = 26 trade · +34.0pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label = weak_trend`
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -42.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Wed`
   - `macro_alignment = strong_against`

**2. Win-rate 3.4%** (1 W / 28 L = 29 trade · -39.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Wed`
   - `H1_adx_label ≠ NA`
   - `dxy_chg1d = [0.5,+∞)`

**3. Win-rate 5.6%** (4 W / 67 L = 71 trade · -37.3pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label ≠ weak_trend`
   - `rsi_M30 = [30,50)`
   - `mtf_trend ≠ all_down`

**4. Win-rate 5.9%** (2 W / 32 L = 34 trade · -37.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Wed`
   - `H1_adx_label = NA`

**5. Win-rate 14.3%** (5 W / 30 L = 35 trade · -28.6pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label = weak_trend`
   - `dow ≠ Mon`
   - `macro_alignment ≠ strong_pro`

**6. Win-rate 15.9%** (10 W / 53 L = 63 trade · -27.0pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label ≠ weak_trend`
   - `rsi_M30 = [30,50)`
   - `mtf_trend = all_down`

**7. Win-rate 21.2%** (25 W / 93 L = 118 trade · -21.7pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label ≠ weak_trend`
   - `rsi_M30 ≠ [30,50)`
   - `session ≠ overlap`

**8. Win-rate 25.0%** (21 W / 63 L = 84 trade · -17.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Wed`
   - `macro_alignment ≠ strong_against`
   - `adx_H1 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0619 |
| 2 | `dow=Fri` | 0.0419 |
| 3 | `dow=Wed` | 0.0364 |
| 4 | `vix_chg1d=[−∞,-3)` | 0.0328 |
| 5 | `macro_alignment=weak_pro` | 0.0248 |
| 6 | `M30_adx_label=trending` | 0.0224 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0201 |
| 8 | `atr_ratio_M30=[0.7,1)` | 0.0198 |
| 9 | `M30_ema_stack=down` | 0.0177 |
| 10 | `M30_ema_stack=up` | 0.0175 |
| 11 | `mtf_trend=all_down` | 0.0174 |
| 12 | `mtf_trend=all_up` | 0.0168 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0162 |
| 14 | `adx_M30=[−∞,18)` | 0.0161 |
| 15 | `dxy_chg1d=[0.5,+∞)` | 0.0159 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **1475**  ·  Baseline win-rate: **14.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 45 L = 45 trade · -14.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 ≠ [35,+∞)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 0.0%** (0 W / 223 L = 223 trade · -14.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `session ≠ us`
   - `vix_chg1d ≠ [3,+∞)`

**3. Win-rate 0.0%** (0 W / 30 L = 30 trade · -14.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `session ≠ us`
   - `vix_chg1d = [3,+∞)`
   - `session = europe`

**4. Win-rate 1.9%** (5 W / 261 L = 266 trade · -12.5pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 = [35,+∞)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `dow ≠ Mon`

**5. Win-rate 2.0%** (1 W / 49 L = 50 trade · -12.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 = [35,+∞)`
   - `dist_low_M30 = [0.7,1.5)`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 10.4%** (16 W / 138 L = 154 trade · -4.0pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 ≠ [35,+∞)`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `dow = Wed`

**7. Win-rate 11.9%** (8 W / 59 L = 67 trade · -2.5pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 = [35,+∞)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `dow = Mon`

**8. Win-rate 14.3%** (3 W / 18 L = 21 trade · -0.1pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `session ≠ us`
   - `vix_chg1d = [3,+∞)`
   - `session ≠ europe`

**9. Win-rate 23.8%** (5 W / 16 L = 21 trade · 9.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `session = us`

**10. Win-rate 25.8%** (32 W / 92 L = 124 trade · 11.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_M30 = [35,+∞)`
   - `dist_low_M30 = [0.7,1.5)`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0584 |
| 2 | `adx_H1=[35,+∞)` | 0.0336 |
| 3 | `vix_chg1d=[0,3)` | 0.0333 |
| 4 | `dow=Tue` | 0.0332 |
| 5 | `adx_M30=[35,+∞)` | 0.0284 |
| 6 | `H1_adx_label=trending` | 0.0276 |
| 7 | `macro_alignment=strong_against` | 0.0258 |
| 8 | `rsi_H1=[30,50)` | 0.0213 |
| 9 | `mtf_trend=NA` | 0.0186 |
| 10 | `H1_adx_label=weak_trend` | 0.0184 |
| 11 | `macro_alignment=strong_pro` | 0.0183 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0180 |
| 13 | `M30_ema_stack=NA` | 0.0176 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0174 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0169 |

---

## XAUUSD · pulse2_inv · BUY
- Toplam çözülmüş: **374**  ·  Baseline win-rate: **64.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (36 W / 0 L = 36 trade · +35.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 = [1,1.3)`
   - `sar_bearish ≠ False`

**2. Win-rate 93.8%** (45 W / 3 L = 48 trade · +29.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`

**3. Win-rate 93.8%** (30 W / 2 L = 32 trade · +29.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 = [1,1.3)`
   - `sar_bearish = False`

**4. Win-rate 80.0%** (16 W / 4 L = 20 trade · +15.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.7%** (24 W / 66 L = 90 trade · -37.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `consec_red_M30 = [0,2)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1618 |
| 2 | `adx_H1=[35,+∞)` | 0.0764 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0442 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0425 |
| 5 | `adx_M30=[25,35)` | 0.0412 |
| 6 | `M30_adx_label=weak_trend` | 0.0398 |
| 7 | `adx_M30=[18,25)` | 0.0390 |
| 8 | `macro_alignment=weak_against` | 0.0312 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0289 |
| 10 | `M30_adx_label=trending` | 0.0248 |
| 11 | `adx_H1=[25,35)` | 0.0197 |
| 12 | `H1_adx_label=trending` | 0.0191 |
| 13 | `M30_ema_stack=down` | 0.0185 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0154 |
| 15 | `mtf_trend=all_down` | 0.0150 |

---

## XAUUSD · pulse2_inv · SELL
- Toplam çözülmüş: **366**  ·  Baseline win-rate: **27.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -27.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 8.3%** (2 W / 22 L = 24 trade · -18.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d = [0,3)`
   - `H1_adx_label = weak_trend`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -17.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment = weak_pro`

**4. Win-rate 10.7%** (3 W / 25 L = 28 trade · -16.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d = [3,+∞)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -7.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment ≠ weak_pro`

**6. Win-rate 27.6%** (21 W / 55 L = 76 trade · 0.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d ≠ [0,3)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `adx_H1 ≠ [35,+∞)`

**7. Win-rate 28.6%** (8 W / 20 L = 28 trade · 1.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d ≠ [3,+∞)`

**8. Win-rate 33.3%** (13 W / 26 L = 39 trade · 6.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d = [0,3)`
   - `H1_adx_label ≠ weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0621 |
| 2 | `macro_alignment=weak_pro` | 0.0491 |
| 3 | `rsi_H1=[30,50)` | 0.0289 |
| 4 | `dist_high_M30=[1.5,+∞)` | 0.0244 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0225 |
| 6 | `adx_H1=[35,+∞)` | 0.0217 |
| 7 | `atr_ratio_M30=[0.7,1)` | 0.0217 |
| 8 | `dow=Mon` | 0.0214 |
| 9 | `rsi_M30=[30,50)` | 0.0212 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0183 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0182 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0181 |
| 13 | `session=us` | 0.0174 |
| 14 | `hour_bucket=12-16` | 0.0174 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0153 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **1268**  ·  Baseline win-rate: **49.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.0%** (120 W / 5 L = 125 trade · +46.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Wed`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 70 L = 70 trade · -49.1pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 2.9%** (1 W / 33 L = 34 trade · -46.2pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**3. Win-rate 5.7%** (2 W / 33 L = 35 trade · -43.4pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 = [−∞,0.2)`

**4. Win-rate 14.6%** (12 W / 70 L = 82 trade · -34.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `M30_ema_stack ≠ up`
   - `mtf_trend ≠ NA`

**5. Win-rate 24.0%** (6 W / 19 L = 25 trade · -25.1pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `M30_ema_stack = up`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 28.1%** (9 W / 23 L = 32 trade · -21.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow = Wed`

**7. Win-rate 29.0%** (9 W / 22 L = 31 trade · -20.1pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d = [−∞,-0.5)`

**8. Win-rate 30.0%** (9 W / 21 L = 30 trade · -19.1pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.1186 |
| 2 | `dow=Fri` | 0.0450 |
| 3 | `vix_chg1d=[−∞,-3)` | 0.0436 |
| 4 | `dow=Wed` | 0.0328 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0315 |
| 6 | `adx_H1=[35,+∞)` | 0.0273 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0269 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0227 |
| 9 | `macro_alignment=strong_pro` | 0.0215 |
| 10 | `vix_chg1d=[-3,0)` | 0.0154 |
| 11 | `mtf_trend=NA` | 0.0153 |
| 12 | `adx_M30=[35,+∞)` | 0.0150 |
| 13 | `M30_ema_stack=NA` | 0.0137 |
| 14 | `mtf_trend=all_up` | 0.0134 |
| 15 | `sar_bearish=True` | 0.0133 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **1890**  ·  Baseline win-rate: **14.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 105 L = 105 trade · -14.5pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme ≠ False`
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `ml_confidence_bucket ≠ [70,80)`

**2. Win-rate 0.0%** (0 W / 25 L = 25 trade · -14.5pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme ≠ False`
   - `dist_low_M30 = [0.3,0.7)`
   - `H1_adx_label ≠ trending`

**3. Win-rate 0.0%** (0 W / 230 L = 230 trade · -14.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Mon`
   - `dow ≠ Tue`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 0.0%** (0 W / 44 L = 44 trade · -14.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `session ≠ europe`

**5. Win-rate 1.9%** (3 W / 152 L = 155 trade · -12.6pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme = False`
   - `dow = Thu`
   - `dxy_chg1d ≠ [0,0.5)`

**6. Win-rate 2.9%** (2 W / 66 L = 68 trade · -11.6pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme = False`
   - `dow ≠ Thu`
   - `M30_ema_stack = NA`

**7. Win-rate 4.0%** (1 W / 24 L = 25 trade · -10.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Mon`
   - `dow = Tue`
   - `consec_red_M30 ≠ [0,2)`

**8. Win-rate 4.4%** (2 W / 43 L = 45 trade · -10.1pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Mon`
   - `dow ≠ Tue`
   - `bb_pctb_M30 = [0.5,0.8)`

**9. Win-rate 5.7%** (2 W / 33 L = 35 trade · -8.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_extreme ≠ False`
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `ml_confidence_bucket = [70,80)`

**10. Win-rate 9.5%** (2 W / 19 L = 21 trade · -5.0pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0685 |
| 2 | `dow=Thu` | 0.0634 |
| 3 | `vix_chg1d=[0,3)` | 0.0260 |
| 4 | `dow=Mon` | 0.0239 |
| 5 | `bb_extreme_lower=False` | 0.0221 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0218 |
| 7 | `mtf_trend=NA` | 0.0211 |
| 8 | `bb_pctb_M30=[−∞,0.2)` | 0.0177 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0176 |
| 10 | `dxy_chg1d=[0.5,+∞)` | 0.0156 |
| 11 | `M30_ema_stack=NA` | 0.0154 |
| 12 | `rsi_extreme=False` | 0.0150 |
| 13 | `sar_bearish=False` | 0.0146 |
| 14 | `bb_extreme_lower=True` | 0.0130 |
| 15 | `oversold=False` | 0.0129 |

---

## XAUUSD · pulse3_inv · BUY
- Toplam çözülmüş: **357**  ·  Baseline win-rate: **62.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (54 W / 0 L = 54 trade · +37.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 85.5%** (53 W / 9 L = 62 trade · +23.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 = [1.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.6%** (21 W / 61 L = 82 trade · -36.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`
   - `near_support = False`
   - `adx_M30 ≠ [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1354 |
| 2 | `adx_H1=[35,+∞)` | 0.0630 |
| 3 | `adx_M30=[25,35)` | 0.0500 |
| 4 | `M30_adx_label=trending` | 0.0378 |
| 5 | `adx_H1=[25,35)` | 0.0369 |
| 6 | `dist_low_M30=[1.5,+∞)` | 0.0338 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0320 |
| 8 | `M30_adx_label=weak_trend` | 0.0309 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0274 |
| 10 | `macro_alignment=weak_against` | 0.0245 |
| 11 | `adx_M30=[18,25)` | 0.0223 |
| 12 | `M30_ema_stack=down` | 0.0206 |
| 13 | `H1_adx_label=trending` | 0.0200 |
| 14 | `mtf_trend=all_down` | 0.0194 |
| 15 | `atr_ratio_M30=[1,1.3)` | 0.0168 |

---

## XAUUSD · pulse3_inv · SELL
- Toplam çözülmüş: **369**  ·  Baseline win-rate: **21.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 27 L = 27 trade · -21.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 0.0%** (0 W / 50 L = 50 trade · -21.7pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 = [50,65)`

**3. Win-rate 9.7%** (3 W / 28 L = 31 trade · -12.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**4. Win-rate 11.4%** (4 W / 31 L = 35 trade · -10.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 ≠ [50,65)`

**5. Win-rate 15.4%** (4 W / 22 L = 26 trade · -6.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

**6. Win-rate 16.0%** (4 W / 21 L = 25 trade · -5.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket = 20-24`

**7. Win-rate 31.3%** (36 W / 79 L = 115 trade · 9.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket ≠ 20-24`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0778 |
| 2 | `dist_high_M30=[1.5,+∞)` | 0.0309 |
| 3 | `macro_alignment=weak_pro` | 0.0278 |
| 4 | `adx_H1=[35,+∞)` | 0.0236 |
| 5 | `M30_adx_label=trending` | 0.0235 |
| 6 | `rsi_H1=[50,65)` | 0.0220 |
| 7 | `volatility_regime=normal` | 0.0210 |
| 8 | `dow=Mon` | 0.0200 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0198 |
| 10 | `macro_alignment=strong_pro` | 0.0177 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0175 |
| 12 | `rsi_M30=[50,65)` | 0.0168 |
| 13 | `dist_high_M30=[0.7,1.5)` | 0.0167 |
| 14 | `M30_ema_stack=mixed` | 0.0163 |
| 15 | `ml_confidence_bucket=[−∞,50)` | 0.0160 |

---

## XAUUSD · smc · BUY
- Toplam çözülmüş: **316**  ·  Baseline win-rate: **71.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (56 W / 0 L = 56 trade · +28.2pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`
   - `dow ≠ Tue`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +23.4pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`
   - `dow = Tue`

**3. Win-rate 94.9%** (37 W / 2 L = 39 trade · +23.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `M30_ema_stack = down`
   - `volatility_regime = low`

**4. Win-rate 86.5%** (32 W / 5 L = 37 trade · +14.7pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend ≠ all_down`

**5. Win-rate 75.9%** (41 W / 13 L = 54 trade · +4.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `M30_ema_stack = down`
   - `volatility_regime ≠ low`
   - `rsi_M30 ≠ [50,65)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -51.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `M30_ema_stack ≠ down`
   - `H1_adx_label ≠ weak_trend`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.1336 |
| 2 | `mtf_trend=all_down` | 0.0747 |
| 3 | `M30_ema_stack=down` | 0.0725 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0399 |
| 5 | `M30_ema_stack=up` | 0.0335 |
| 6 | `mtf_trend=all_up` | 0.0301 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0241 |
| 8 | `volatility_regime=low` | 0.0204 |
| 9 | `volatility_regime=normal` | 0.0195 |
| 10 | `macro_alignment=strong_pro` | 0.0194 |
| 11 | `H1_adx_label=weak_trend` | 0.0178 |
| 12 | `adx_H1=[18,25)` | 0.0178 |
| 13 | `macd_atr_M30=[0,0.3)` | 0.0172 |
| 14 | `macro_alignment=neutral` | 0.0159 |
| 15 | `macd_atr_M30=[-0.3,0)` | 0.0152 |

---

## XAUUSD · smc · SELL
- Toplam çözülmüş: **360**  ·  Baseline win-rate: **29.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +59.3pp vs baseline)
   - `dow = Fri`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 28 L = 28 trade · -29.2pp vs baseline)
   - `dow ≠ Fri`
   - `macd_atr_M30 ≠ [-0.3,0)`
   - `adx_M30 ≠ [25,35)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**2. Win-rate 8.3%** (2 W / 22 L = 24 trade · -20.9pp vs baseline)
   - `dow ≠ Fri`
   - `macd_atr_M30 = [-0.3,0)`
   - `atr_ratio_M30 = [1,1.3)`

**3. Win-rate 14.1%** (14 W / 85 L = 99 trade · -15.1pp vs baseline)
   - `dow ≠ Fri`
   - `macd_atr_M30 ≠ [-0.3,0)`
   - `adx_M30 ≠ [25,35)`
   - `dist_low_M30 = [1.5,+∞)`

**4. Win-rate 24.3%** (18 W / 56 L = 74 trade · -4.9pp vs baseline)
   - `dow ≠ Fri`
   - `macd_atr_M30 = [-0.3,0)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0486 |
| 2 | `dow=Fri` | 0.0462 |
| 3 | `adx_M30=[35,+∞)` | 0.0355 |
| 4 | `macd_atr_M30=[-0.3,0)` | 0.0351 |
| 5 | `macro_alignment=strong_pro` | 0.0351 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0337 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0318 |
| 8 | `bb_pctb_M30=[0.2,0.5)` | 0.0275 |
| 9 | `H1_adx_label=ranging` | 0.0275 |
| 10 | `adx_H1=[−∞,18)` | 0.0274 |
| 11 | `macd_atr_M30=[0,0.3)` | 0.0230 |
| 12 | `H1_adx_label=trending` | 0.0229 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0220 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0220 |
| 15 | `vix_chg1d=[-3,0)` | 0.0191 |

---

## XAUUSD · smc_inv · BUY
- Toplam çözülmüş: **133**  ·  Baseline win-rate: **54.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +45.1pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0,0.5)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**2. Win-rate 81.0%** (17 W / 4 L = 21 trade · +26.1pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0,0.5)`
   - `us10y_chg1d = [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.1%** (8 W / 30 L = 38 trade · -33.8pp vs baseline)
   - `dow = Tue`

**2. Win-rate 33.3%** (8 W / 16 L = 24 trade · -21.6pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d ≠ [0,0.5)`
   - `macd_atr_M30 = [0,0.3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_high_M30=[1.5,+∞)` | 0.0845 |
| 2 | `dow=Tue` | 0.0792 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0565 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0523 |
| 5 | `adx_M30=[35,+∞)` | 0.0352 |
| 6 | `macro_alignment=weak_against` | 0.0331 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0321 |
| 8 | `atr_ratio_M30=[0.7,1)` | 0.0288 |
| 9 | `adx_M30=[25,35)` | 0.0266 |
| 10 | `macd_atr_M30=[0,0.3)` | 0.0251 |
| 11 | `us10y_chg1d=[0,0.5)` | 0.0238 |
| 12 | `dist_low_M30=[0.7,1.5)` | 0.0238 |
| 13 | `M30_ema_stack=mixed` | 0.0234 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0228 |
| 15 | `dist_high_M30=[0.7,1.5)` | 0.0226 |

---
