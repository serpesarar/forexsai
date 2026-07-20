# Pattern Mining Raporu
_2026-07-20T05:01:13.408752Z — son 60 gün — 38906 resolved sinyal_

**Yöntem:** Decision Tree (max_depth=4) + Random Forest feature importance.
Her leaf bir kural. min_samples_leaf=20, class_weight=balanced.

**Yorum kılavuzu:**
- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)
- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)
- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli

---

## GLOBAL — tüm sembol & model
- Toplam çözülmüş: **38906**  ·  Baseline win-rate: **41.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.5%** (913 W / 168 L = 1081 trade · +43.2pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `consec_red_M30 ≠ [0,2)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`

**2. Win-rate 82.3%** (144 W / 31 L = 175 trade · +41.0pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label = trending`
   - `sar_bearish ≠ True`
   - `regime_label = strong_trend_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.7%** (118 W / 889 L = 1007 trade · -29.6pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label ≠ trending`
   - `session_phase = off_hours`
   - `H4_ema_stack = down`

**2. Win-rate 14.5%** (57 W / 335 L = 392 trade · -26.8pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`
   - `bb_extreme_upper ≠ False`
   - `session ≠ overlap`

**3. Win-rate 18.0%** (9 W / 41 L = 50 trade · -23.3pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `consec_red_M30 ≠ [0,2)`
   - `macd_atr_M30 = [−∞,-0.3)`

**4. Win-rate 24.3%** (37 W / 115 L = 152 trade · -17.0pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `consec_red_M30 = [0,2)`
   - `bb_extreme_upper ≠ False`

**5. Win-rate 28.2%** (1218 W / 3094 L = 4312 trade · -13.1pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label ≠ trending`
   - `session_phase ≠ off_hours`
   - `macro_alignment = weak_pro`

**6. Win-rate 30.8%** (60 W / 135 L = 195 trade · -10.5pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label = trending`
   - `sar_bearish = True`
   - `M30_ema_stack = mixed`

**7. Win-rate 32.7%** (288 W / 594 L = 882 trade · -8.6pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`
   - `bb_extreme_upper = False`
   - `M30_adx_label = ranging`

**8. Win-rate 33.6%** (917 W / 1810 L = 2727 trade · -7.7pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label = trending`
   - `sar_bearish ≠ True`
   - `regime_label ≠ strong_trend_down`

**9. Win-rate 34.4%** (245 W / 468 L = 713 trade · -6.9pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label ≠ trending`
   - `session_phase = off_hours`
   - `H4_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[30,50)` | 0.0388 |
| 2 | `H1_ema_stack=down` | 0.0287 |
| 3 | `H4_ema_stack=NA` | 0.0218 |
| 4 | `M30_ema_stack=down` | 0.0213 |
| 5 | `macro_alignment=weak_pro` | 0.0206 |
| 6 | `rsi_H1=[30,50)` | 0.0200 |
| 7 | `M30_ema_stack=up` | 0.0182 |
| 8 | `rsi_H4=[50,65)` | 0.0167 |
| 9 | `macro_alignment=strong_against` | 0.0160 |
| 10 | `rsi_H4=NA` | 0.0158 |
| 11 | `M30_adx_label=trending` | 0.0156 |
| 12 | `macro_alignment=strong_pro` | 0.0147 |
| 13 | `adx_H4=NA` | 0.0145 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0142 |
| 15 | `dow=Mon` | 0.0134 |

---

## GDAXI.INDX · ai_panel
- Toplam çözülmüş: **113**  ·  Baseline win-rate: **57.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.4%** (19 W / 3 L = 22 trade · +28.9pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `session = europe`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 28.6%** (6 W / 15 L = 21 trade · -28.9pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `regime_label = transition`
   - `rsi_H4 ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0887 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0612 |
| 3 | `rsi_H1=[50,65)` | 0.0533 |
| 4 | `sar_bearish=True` | 0.0450 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0424 |
| 6 | `H1_ema_stack=mixed` | 0.0335 |
| 7 | `macro_alignment=strong_against` | 0.0323 |
| 8 | `us10y_chg1d=[-0.5,0)` | 0.0321 |
| 9 | `us10y_chg1d=[−∞,-0.5)` | 0.0284 |
| 10 | `H4_ema_stack=up` | 0.0269 |
| 11 | `session=europe` | 0.0261 |
| 12 | `regime_label=transition` | 0.0243 |
| 13 | `macro_alignment=neutral` | 0.0240 |
| 14 | `hour_bucket=08-12` | 0.0239 |
| 15 | `sar_bearish=False` | 0.0224 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **413**  ·  Baseline win-rate: **47.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.0%** (24 W / 1 L = 25 trade · +49.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H4 = [25,35)`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +28.0pp vs baseline)
   - `sar_bearish = False`
   - `regime_label = ranging`
   - `H1_adx_label = trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.8%** (22 W / 95 L = 117 trade · -28.2pp vs baseline)
   - `sar_bearish = False`
   - `regime_label ≠ ranging`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 30.8%** (8 W / 18 L = 26 trade · -16.2pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d = [3,+∞)`
   - `H1_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0607 |
| 2 | `rsi_H1=[30,50)` | 0.0501 |
| 3 | `sar_bearish=True` | 0.0395 |
| 4 | `regime_label=ranging` | 0.0367 |
| 5 | `H4_adx_label=ranging` | 0.0337 |
| 6 | `rsi_H1=[50,65)` | 0.0331 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0294 |
| 8 | `adx_H4=[−∞,18)` | 0.0231 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0213 |
| 10 | `adx_H1=[25,35)` | 0.0205 |
| 11 | `H1_ema_stack=up` | 0.0195 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0183 |
| 13 | `hour_bucket=12-16` | 0.0182 |
| 14 | `H4_ema_stack=mixed` | 0.0167 |
| 15 | `macro_alignment=neutral` | 0.0166 |

---

## GDAXI.INDX · ml:balanced
- Toplam çözülmüş: **211**  ·  Baseline win-rate: **65.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +34.6pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `H1_adx_label = weak_trend`
   - `dxy_chg1d ≠ [0,0.5)`

**2. Win-rate 100.0%** (25 W / 0 L = 25 trade · +34.6pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H4_ema_stack = up`
   - `hour_bucket = 08-12`

**3. Win-rate 86.7%** (26 W / 4 L = 30 trade · +21.3pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H4_ema_stack = up`
   - `hour_bucket ≠ 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.0%** (9 W / 21 L = 30 trade · -35.4pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `H1_adx_label ≠ weak_trend`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `regime_label = transition`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0803 |
| 2 | `sar_bearish=False` | 0.0608 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0448 |
| 4 | `H4_ema_stack=up` | 0.0404 |
| 5 | `sar_bearish=True` | 0.0390 |
| 6 | `rsi_H1=[50,65)` | 0.0329 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0328 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0313 |
| 9 | `vix_chg1d=[0,3)` | 0.0301 |
| 10 | `adx_H1=[−∞,18)` | 0.0283 |
| 11 | `H1_adx_label=ranging` | 0.0250 |
| 12 | `adx_H1=[18,25)` | 0.0231 |
| 13 | `regime_label=transition` | 0.0222 |
| 14 | `macro_alignment=neutral` | 0.0213 |
| 15 | `H1_adx_label=weak_trend` | 0.0200 |

---

## GDAXI.INDX · ml:full_power
- Toplam çözülmüş: **235**  ·  Baseline win-rate: **60.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +40.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `H1_adx_label = trending`

**2. Win-rate 90.5%** (19 W / 2 L = 21 trade · +30.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `H1_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.7%** (5 W / 18 L = 23 trade · -38.3pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 23.8%** (5 W / 16 L = 21 trade · -36.2pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `macro_alignment = strong_against`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0797 |
| 2 | `rsi_H1=[30,50)` | 0.0740 |
| 3 | `sar_bearish=True` | 0.0651 |
| 4 | `rsi_H1=[50,65)` | 0.0559 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0437 |
| 6 | `H4_ema_stack=up` | 0.0355 |
| 7 | `regime_label=transition` | 0.0292 |
| 8 | `adx_H1=[−∞,18)` | 0.0269 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0253 |
| 10 | `vix_chg1d=[0,3)` | 0.0240 |
| 11 | `bb_extreme_lower=True` | 0.0192 |
| 12 | `H1_adx_label=ranging` | 0.0188 |
| 13 | `bb_extreme_lower=False` | 0.0186 |
| 14 | `macro_alignment=strong_against` | 0.0177 |
| 15 | `H4_ema_stack=NA` | 0.0166 |

---

## GDAXI.INDX · ml:main
- Toplam çözülmüş: **235**  ·  Baseline win-rate: **60.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +40.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `H1_adx_label = trending`

**2. Win-rate 90.0%** (18 W / 2 L = 20 trade · +30.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `H1_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.7%** (5 W / 18 L = 23 trade · -38.3pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 22.7%** (5 W / 17 L = 22 trade · -37.3pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `macro_alignment = strong_against`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0787 |
| 2 | `sar_bearish=True` | 0.0594 |
| 3 | `rsi_H1=[50,65)` | 0.0567 |
| 4 | `H4_ema_stack=up` | 0.0538 |
| 5 | `rsi_H1=[30,50)` | 0.0492 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0341 |
| 7 | `regime_label=transition` | 0.0235 |
| 8 | `H1_adx_label=ranging` | 0.0227 |
| 9 | `vix_chg1d=[0,3)` | 0.0205 |
| 10 | `adx_H1=[−∞,18)` | 0.0202 |
| 11 | `H1_adx_label=trending` | 0.0195 |
| 12 | `H1_ema_stack=down` | 0.0194 |
| 13 | `macro_alignment=strong_against` | 0.0190 |
| 14 | `bb_extreme_upper=True` | 0.0184 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0184 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **1039**  ·  Baseline win-rate: **27.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.7%** (55 W / 14 L = 69 trade · +52.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `rsi_H1 = [50,65)`
   - `hour_bucket = 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 147 L = 147 trade · -27.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish = False`

**2. Win-rate 3.7%** (2 W / 52 L = 54 trade · -23.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 6.8%** (5 W / 69 L = 74 trade · -20.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish ≠ False`

**4. Win-rate 20.8%** (5 W / 19 L = 24 trade · -6.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `rsi_H1 ≠ [50,65)`
   - `dxy_chg1d = [-0.5,0)`

**5. Win-rate 21.6%** (58 W / 210 L = 268 trade · -6.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket ≠ 04-08`
   - `ml_confidence_bucket ≠ [−∞,50)`

**6. Win-rate 22.2%** (6 W / 21 L = 27 trade · -5.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 = NA`
   - `adx_H1 = [18,25)`

**7. Win-rate 26.7%** (8 W / 22 L = 30 trade · -0.9pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket = 04-08`
   - `vix_chg1d = [−∞,-3)`

**8. Win-rate 30.6%** (15 W / 34 L = 49 trade · 3.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

**9. Win-rate 34.6%** (44 W / 83 L = 127 trade · 7.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket ≠ 04-08`
   - `ml_confidence_bucket = [−∞,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1349 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0516 |
| 3 | `adx_H4=[−∞,18)` | 0.0372 |
| 4 | `bb_extreme_upper=False` | 0.0345 |
| 5 | `regime_label=ranging` | 0.0336 |
| 6 | `bb_extreme_upper=True` | 0.0270 |
| 7 | `vix_chg1d=[0,3)` | 0.0237 |
| 8 | `vix_chg1d=[-3,0)` | 0.0196 |
| 9 | `hour_bucket=12-16` | 0.0195 |
| 10 | `H4_adx_label=ranging` | 0.0190 |
| 11 | `rsi_H1=[50,65)` | 0.0170 |
| 12 | `hour_bucket=08-12` | 0.0165 |
| 13 | `regime_label=transition` | 0.0160 |
| 14 | `macro_alignment=weak_pro` | 0.0156 |
| 15 | `dow=Fri` | 0.0155 |

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
- Toplam çözülmüş: **522**  ·  Baseline win-rate: **43.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.4%** (64 W / 6 L = 70 trade · +48.1pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`

**2. Win-rate 81.8%** (18 W / 4 L = 22 trade · +38.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `vix_chg1d = [0,3)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 2.2%** (1 W / 45 L = 46 trade · -41.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [0,3)`
   - `H1_adx_label = trending`
   - `regime_label ≠ transition`

**2. Win-rate 14.8%** (4 W / 23 L = 27 trade · -28.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [0,3)`
   - `H1_adx_label = trending`
   - `regime_label = transition`

**3. Win-rate 20.0%** (17 W / 68 L = 85 trade · -23.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [0,3)`
   - `H1_adx_label ≠ trending`
   - `dxy_chg1d ≠ [-0.5,0)`

**4. Win-rate 20.0%** (7 W / 28 L = 35 trade · -23.3pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [0.5,+∞)`
   - `oversold = False`

**5. Win-rate 22.2%** (6 W / 21 L = 27 trade · -21.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `vix_chg1d = [0,3)`
   - `volatility_regime = normal`
   - `hour_bucket ≠ 08-12`

**6. Win-rate 24.0%** (6 W / 19 L = 25 trade · -19.3pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0667 |
| 2 | `sar_bearish=True` | 0.0591 |
| 3 | `bb_extreme_upper=False` | 0.0417 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0371 |
| 5 | `bb_extreme_upper=True` | 0.0301 |
| 6 | `H4_adx_label=ranging` | 0.0295 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0268 |
| 8 | `regime_label=ranging` | 0.0254 |
| 9 | `dow=Mon` | 0.0244 |
| 10 | `session=asia` | 0.0217 |
| 11 | `adx_H4=[−∞,18)` | 0.0207 |
| 12 | `vix_chg1d=[0,3)` | 0.0203 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0199 |
| 14 | `volatility_regime=high` | 0.0189 |
| 15 | `dow=Wed` | 0.0184 |

---

## GDAXI.INDX · pulse2_inv
- Toplam çözülmüş: **134**  ·  Baseline win-rate: **49.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.3%** (7 W / 23 L = 30 trade · -26.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [−∞,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0636 |
| 2 | `volatility_regime=normal` | 0.0371 |
| 3 | `macro_alignment=strong_pro` | 0.0357 |
| 4 | `rsi_H4=NA` | 0.0312 |
| 5 | `rsi_H4=[75,+∞)` | 0.0305 |
| 6 | `macro_alignment=weak_against` | 0.0304 |
| 7 | `adx_H4=NA` | 0.0296 |
| 8 | `H1_adx_label=trending` | 0.0272 |
| 9 | `mtf_trend=all_up` | 0.0262 |
| 10 | `hour_bucket=08-12` | 0.0240 |
| 11 | `H4_ema_stack=up` | 0.0239 |
| 12 | `session=overlap` | 0.0233 |
| 13 | `adx_H1=[35,+∞)` | 0.0232 |
| 14 | `H4_adx_label=NA` | 0.0229 |
| 15 | `session=asia` | 0.0222 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **938**  ·  Baseline win-rate: **38.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.6%** (58 W / 6 L = 64 trade · +52.2pp vs baseline)
   - `H1_adx_label = trending`
   - `vix_chg1d ≠ [-3,0)`
   - `H1_ema_stack ≠ mixed`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -38.4pp vs baseline)
   - `H1_adx_label = trending`
   - `vix_chg1d ≠ [-3,0)`
   - `H1_ema_stack = mixed`
   - `session = europe`

**2. Win-rate 1.9%** (1 W / 53 L = 54 trade · -36.5pp vs baseline)
   - `H1_adx_label = trending`
   - `vix_chg1d = [-3,0)`
   - `sar_bearish = False`
   - `session = europe`

**3. Win-rate 3.4%** (2 W / 57 L = 59 trade · -35.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [60,70)`
   - `sar_bearish = False`
   - `macro_alignment ≠ neutral`

**4. Win-rate 4.0%** (1 W / 24 L = 25 trade · -34.4pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H4 = [30,50)`

**5. Win-rate 13.9%** (5 W / 31 L = 36 trade · -24.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [60,70)`
   - `sar_bearish ≠ False`
   - `session ≠ europe`

**6. Win-rate 17.1%** (6 W / 29 L = 35 trade · -21.3pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [60,70)`
   - `sar_bearish = False`
   - `macro_alignment = neutral`

**7. Win-rate 25.9%** (7 W / 20 L = 27 trade · -12.5pp vs baseline)
   - `H1_adx_label = trending`
   - `vix_chg1d = [-3,0)`
   - `sar_bearish = False`
   - `session ≠ europe`

**8. Win-rate 27.3%** (12 W / 32 L = 44 trade · -11.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dxy_chg1d = [-0.5,0)`
   - `us10y_chg1d = [−∞,-0.5)`

**9. Win-rate 31.3%** (71 W / 156 L = 227 trade · -7.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H4 ≠ [30,50)`

**10. Win-rate 34.5%** (10 W / 19 L = 29 trade · -3.9pp vs baseline)
   - `H1_adx_label = trending`
   - `vix_chg1d ≠ [-3,0)`
   - `H1_ema_stack = mixed`
   - `session ≠ europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0399 |
| 2 | `rsi_H1=[30,50)` | 0.0360 |
| 3 | `H1_adx_label=ranging` | 0.0278 |
| 4 | `adx_H1=[−∞,18)` | 0.0272 |
| 5 | `vix_chg1d=[-3,0)` | 0.0249 |
| 6 | `H1_ema_stack=mixed` | 0.0246 |
| 7 | `session=overlap` | 0.0229 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0227 |
| 9 | `sar_bearish=False` | 0.0221 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0219 |
| 11 | `sar_bearish=True` | 0.0213 |
| 12 | `hour_bucket=04-08` | 0.0199 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0195 |
| 14 | `hour_bucket=12-16` | 0.0195 |
| 15 | `session=europe` | 0.0186 |

---

## GDAXI.INDX · pulse3_inv
- Toplam çözülmüş: **187**  ·  Baseline win-rate: **44.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (24 W / 8 L = 32 trade · +30.6pp vs baseline)
   - `adx_H4 ≠ NA`
   - `macro_alignment = strong_pro`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (4 W / 24 L = 28 trade · -30.1pp vs baseline)
   - `adx_H4 = NA`
   - `H1_ema_stack ≠ mixed`
   - `mtf_trend = mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H4=NA` | 0.0446 |
| 2 | `H4_adx_label=NA` | 0.0396 |
| 3 | `H4_adx_label=trending` | 0.0388 |
| 4 | `macro_alignment=strong_pro` | 0.0385 |
| 5 | `rsi_H4=NA` | 0.0371 |
| 6 | `us10y_chg1d=[0,0.5)` | 0.0343 |
| 7 | `H4_ema_stack=NA` | 0.0338 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0318 |
| 9 | `H1_adx_label=trending` | 0.0300 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0270 |
| 11 | `rsi_H4=[75,+∞)` | 0.0250 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0239 |
| 13 | `mtf_trend=all_up` | 0.0233 |
| 14 | `adx_H4=[25,35)` | 0.0165 |
| 15 | `rsi_H1=[30,50)` | 0.0162 |

---

## GDAXI.INDX · smc
- Toplam çözülmüş: **93**  ·  Baseline win-rate: **47.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.8%** (21 W / 5 L = 26 trade · +33.5pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d ≠ [−∞,-3)`
   - `rsi_H1 = [50,65)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (3 W / 18 L = 21 trade · -33.0pp vs baseline)
   - `macro_alignment = strong_against`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0668 |
| 2 | `adx_H4=[25,35)` | 0.0584 |
| 3 | `macro_alignment=strong_against` | 0.0552 |
| 4 | `rsi_H1=[50,65)` | 0.0500 |
| 5 | `adx_H4=[−∞,18)` | 0.0493 |
| 6 | `rsi_H4=[50,65)` | 0.0449 |
| 7 | `H4_adx_label=ranging` | 0.0368 |
| 8 | `regime_label=strong_trend_up` | 0.0357 |
| 9 | `sar_bearish=False` | 0.0334 |
| 10 | `vix_chg1d=[0,3)` | 0.0252 |
| 11 | `regime_label=ranging` | 0.0250 |
| 12 | `H1_adx_label=trending` | 0.0248 |
| 13 | `sar_bearish=True` | 0.0240 |
| 14 | `us10y_chg1d=[0,0.5)` | 0.0233 |
| 15 | `session=asia` | 0.0209 |

---

## NDX.INDX · ai_panel
- Toplam çözülmüş: **124**  ·  Baseline win-rate: **63.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (30 W / 5 L = 35 trade · +22.0pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack = up`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0943 |
| 2 | `sar_bearish=False` | 0.0677 |
| 3 | `H4_ema_stack=up` | 0.0630 |
| 4 | `dow=Mon` | 0.0420 |
| 5 | `rsi_H1=[30,50)` | 0.0304 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0295 |
| 7 | `dow=Thu` | 0.0269 |
| 8 | `H1_ema_stack=down` | 0.0269 |
| 9 | `rsi_H1=[50,65)` | 0.0255 |
| 10 | `hour_bucket=12-16` | 0.0254 |
| 11 | `rsi_H4=[50,65)` | 0.0247 |
| 12 | `macro_alignment=weak_pro` | 0.0230 |
| 13 | `regime_label=transition` | 0.0210 |
| 14 | `rsi_H4=[30,50)` | 0.0200 |
| 15 | `adx_H1=[35,+∞)` | 0.0198 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **272**  ·  Baseline win-rate: **49.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (27 W / 3 L = 30 trade · +40.4pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `H1_ema_stack = mixed`
   - `dxy_chg1d ≠ [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 12.9%** (4 W / 27 L = 31 trade · -36.7pp vs baseline)
   - `rsi_H1 = [65,75)`

**2. Win-rate 13.3%** (4 W / 26 L = 30 trade · -36.3pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `H1_ema_stack ≠ mixed`
   - `sar_bearish ≠ True`
   - `H4_ema_stack = NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0553 |
| 2 | `H1_ema_stack=up` | 0.0535 |
| 3 | `rsi_H4=[30,50)` | 0.0496 |
| 4 | `sar_bearish=False` | 0.0444 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0386 |
| 6 | `rsi_H1=[65,75)` | 0.0359 |
| 7 | `H1_adx_label=weak_trend` | 0.0351 |
| 8 | `H1_ema_stack=mixed` | 0.0324 |
| 9 | `H4_ema_stack=NA` | 0.0319 |
| 10 | `H1_adx_label=trending` | 0.0312 |
| 11 | `rsi_H1=[30,50)` | 0.0257 |
| 12 | `adx_H4=[25,35)` | 0.0240 |
| 13 | `adx_H1=[18,25)` | 0.0237 |
| 14 | `H4_ema_stack=up` | 0.0229 |
| 15 | `mtf_trend=mixed` | 0.0191 |

---

## NDX.INDX · ml:balanced
- Toplam çözülmüş: **255**  ·  Baseline win-rate: **54.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +30.5pp vs baseline)
   - `H4_ema_stack = up`
   - `dow = Wed`

**2. Win-rate 80.0%** (20 W / 5 L = 25 trade · +25.5pp vs baseline)
   - `H4_ema_stack = up`
   - `dow ≠ Wed`
   - `session ≠ overlap`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.6%** (7 W / 27 L = 34 trade · -33.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 28.6%** (6 W / 15 L = 21 trade · -25.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0734 |
| 2 | `H4_ema_stack=mixed` | 0.0623 |
| 3 | `rsi_H1=[30,50)` | 0.0459 |
| 4 | `macro_alignment=weak_pro` | 0.0382 |
| 5 | `dow=Mon` | 0.0361 |
| 6 | `sar_bearish=False` | 0.0311 |
| 7 | `session_phase=mid_session` | 0.0311 |
| 8 | `sar_bearish=True` | 0.0282 |
| 9 | `dow=Thu` | 0.0239 |
| 10 | `hour_bucket=16-20` | 0.0231 |
| 11 | `us10y_chg1d=[0,0.5)` | 0.0219 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0208 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0207 |
| 14 | `adx_H1=[25,35)` | 0.0185 |
| 15 | `hour_bucket=12-16` | 0.0176 |

---

## NDX.INDX · ml:full_power
- Toplam çözülmüş: **260**  ·  Baseline win-rate: **55.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.9%** (30 W / 8 L = 38 trade · +23.1pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.5%** (9 W / 25 L = 34 trade · -29.3pp vs baseline)
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0611 |
| 2 | `H4_ema_stack=up` | 0.0514 |
| 3 | `H4_ema_stack=mixed` | 0.0389 |
| 4 | `dow=Mon` | 0.0377 |
| 5 | `macro_alignment=weak_pro` | 0.0367 |
| 6 | `macro_alignment=neutral` | 0.0343 |
| 7 | `adx_H1=[25,35)` | 0.0334 |
| 8 | `dow=Thu` | 0.0291 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0253 |
| 10 | `sar_bearish=True` | 0.0247 |
| 11 | `session_phase=mid_session` | 0.0246 |
| 12 | `adx_H4=[35,+∞)` | 0.0210 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0199 |
| 14 | `sar_bearish=False` | 0.0195 |
| 15 | `rsi_H1=[50,65)` | 0.0188 |

---

## NDX.INDX · ml:main
- Toplam çözülmüş: **261**  ·  Baseline win-rate: **56.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.5%** (9 W / 25 L = 34 trade · -29.8pp vs baseline)
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0494 |
| 2 | `dow=Mon` | 0.0463 |
| 3 | `macro_alignment=weak_pro` | 0.0431 |
| 4 | `H4_ema_stack=up` | 0.0420 |
| 5 | `macro_alignment=neutral` | 0.0335 |
| 6 | `H4_ema_stack=mixed` | 0.0312 |
| 7 | `sar_bearish=False` | 0.0309 |
| 8 | `sar_bearish=True` | 0.0266 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0219 |
| 10 | `dow=Thu` | 0.0219 |
| 11 | `adx_H1=[25,35)` | 0.0210 |
| 12 | `volatility_regime=normal` | 0.0204 |
| 13 | `session_phase=mid_session` | 0.0199 |
| 14 | `hour_bucket=16-20` | 0.0175 |
| 15 | `volatility_regime=high` | 0.0174 |

---

## NDX.INDX · ml:main_inv
- Toplam çözülmüş: **145**  ·  Baseline win-rate: **57.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.4%** (19 W / 3 L = 22 trade · +29.2pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack ≠ up`
   - `dxy_chg1d = [0,0.5)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 81.8%** (18 W / 4 L = 22 trade · +24.6pp vs baseline)
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.0%** (6 W / 14 L = 20 trade · -27.2pp vs baseline)
   - `dow ≠ Mon`
   - `H4_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0483 |
| 2 | `regime_label=transition` | 0.0468 |
| 3 | `dow=Mon` | 0.0452 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0382 |
| 5 | `session=us` | 0.0357 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0312 |
| 7 | `H4_ema_stack=down` | 0.0286 |
| 8 | `rsi_H1=[30,50)` | 0.0261 |
| 9 | `session_phase=mid_session` | 0.0256 |
| 10 | `H4_ema_stack=up` | 0.0251 |
| 11 | `session=overlap` | 0.0235 |
| 12 | `session_phase=after_hours` | 0.0231 |
| 13 | `hour_bucket=12-16` | 0.0229 |
| 14 | `adx_H4=[−∞,18)` | 0.0222 |
| 15 | `us10y_chg1d=[−∞,-0.5)` | 0.0216 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **1025**  ·  Baseline win-rate: **38.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.8%** (18 W / 4 L = 22 trade · +43.8pp vs baseline)
   - `H1_adx_label = trending`
   - `rsi_H4 ≠ [65,75)`
   - `sar_bearish = False`
   - `macro_alignment = weak_against`

**2. Win-rate 77.1%** (64 W / 19 L = 83 trade · +39.1pp vs baseline)
   - `H1_adx_label = trending`
   - `rsi_H4 ≠ [65,75)`
   - `sar_bearish ≠ False`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 92 L = 92 trade · -38.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish ≠ True`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 4.2%** (1 W / 23 L = 24 trade · -33.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `vix_chg1d = [-3,0)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 4.3%** (1 W / 22 L = 23 trade · -33.7pp vs baseline)
   - `H1_adx_label = trending`
   - `rsi_H4 = [65,75)`

**4. Win-rate 6.5%** (2 W / 29 L = 31 trade · -31.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish = True`
   - `adx_H4 = [25,35)`

**5. Win-rate 10.0%** (2 W / 18 L = 20 trade · -28.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `vix_chg1d = [-3,0)`
   - `us10y_chg1d = [0.5,+∞)`

**6. Win-rate 13.3%** (4 W / 26 L = 30 trade · -24.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish ≠ True`
   - `dxy_chg1d = [-0.5,0)`

**7. Win-rate 25.5%** (24 W / 70 L = 94 trade · -12.5pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `vix_chg1d ≠ [-3,0)`
   - `vix_chg1d = [−∞,-3)`

**8. Win-rate 33.1%** (51 W / 103 L = 154 trade · -4.9pp vs baseline)
   - `H1_adx_label = trending`
   - `rsi_H4 ≠ [65,75)`
   - `sar_bearish = False`
   - `macro_alignment ≠ weak_against`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0413 |
| 2 | `sar_bearish=False` | 0.0411 |
| 3 | `H1_adx_label=trending` | 0.0384 |
| 4 | `rsi_H1=[30,50)` | 0.0314 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0305 |
| 6 | `rsi_H4=[30,50)` | 0.0305 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0304 |
| 8 | `adx_H1=[35,+∞)` | 0.0291 |
| 9 | `H1_ema_stack=up` | 0.0259 |
| 10 | `rsi_H1=[65,75)` | 0.0221 |
| 11 | `macro_alignment=weak_pro` | 0.0195 |
| 12 | `macro_alignment=strong_pro` | 0.0180 |
| 13 | `bb_extreme_upper=False` | 0.0178 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0170 |
| 15 | `H4_ema_stack=NA` | 0.0170 |

---

## NDX.INDX · pulse1_inv
- Toplam çözülmüş: **349**  ·  Baseline win-rate: **50.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.4%** (27 W / 5 L = 32 trade · +34.3pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`
   - `rsi_H1 = [65,75)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.9%** (8 W / 27 L = 35 trade · -27.2pp vs baseline)
   - `dow = Fri`

**2. Win-rate 30.9%** (17 W / 38 L = 55 trade · -19.2pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session_phase ≠ after_hours`
   - `H1_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0427 |
| 2 | `session_phase=mid_session` | 0.0395 |
| 3 | `vix_chg1d=[−∞,-3)` | 0.0351 |
| 4 | `overbought=True` | 0.0347 |
| 5 | `session_phase=after_hours` | 0.0301 |
| 6 | `overbought=False` | 0.0257 |
| 7 | `adx_H4=[35,+∞)` | 0.0247 |
| 8 | `H4_ema_stack=mixed` | 0.0209 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0208 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0200 |
| 11 | `macro_alignment=neutral` | 0.0195 |
| 12 | `H4_ema_stack=down` | 0.0192 |
| 13 | `hour_bucket=16-20` | 0.0189 |
| 14 | `sar_bearish=False` | 0.0188 |
| 15 | `mtf_trend=mixed` | 0.0184 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **489**  ·  Baseline win-rate: **48.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.3%** (55 W / 8 L = 63 trade · +38.4pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_H1 ≠ [18,25)`
   - `volatility_regime = high`
   - `H4_ema_stack = up`

**2. Win-rate 75.0%** (21 W / 7 L = 28 trade · +26.1pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack ≠ NA`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -48.9pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack = NA`
   - `volatility_regime = high`

**2. Win-rate 9.1%** (2 W / 20 L = 22 trade · -39.8pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack = NA`
   - `volatility_regime ≠ high`
   - `H1_adx_label = weak_trend`

**3. Win-rate 19.3%** (11 W / 46 L = 57 trade · -29.6pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack ≠ NA`
   - `vix_chg1d ≠ [−∞,-3)`
   - `rsi_H4 ≠ [30,50)`

**4. Win-rate 20.0%** (4 W / 16 L = 20 trade · -28.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_H1 ≠ [18,25)`
   - `volatility_regime ≠ high`
   - `mtf_trend = all_up`

**5. Win-rate 21.2%** (7 W / 26 L = 33 trade · -27.7pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_H1 = [18,25)`
   - `volatility_regime ≠ normal`

**6. Win-rate 28.0%** (7 W / 18 L = 25 trade · -20.9pp vs baseline)
   - `sar_bearish = False`
   - `H4_ema_stack = NA`
   - `volatility_regime ≠ high`
   - `H1_adx_label ≠ weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0503 |
| 2 | `sar_bearish=True` | 0.0460 |
| 3 | `H1_adx_label=trending` | 0.0352 |
| 4 | `H4_ema_stack=up` | 0.0309 |
| 5 | `rsi_H1=[30,50)` | 0.0273 |
| 6 | `rsi_H4=[30,50)` | 0.0272 |
| 7 | `H1_ema_stack=up` | 0.0261 |
| 8 | `H1_adx_label=weak_trend` | 0.0257 |
| 9 | `adx_H1=[18,25)` | 0.0245 |
| 10 | `bb_extreme_upper=True` | 0.0228 |
| 11 | `bb_extreme_upper=False` | 0.0222 |
| 12 | `dow=Fri` | 0.0221 |
| 13 | `volatility_regime=high` | 0.0198 |
| 14 | `adx_H1=[25,35)` | 0.0192 |
| 15 | `H4_ema_stack=NA` | 0.0192 |

---

## NDX.INDX · pulse2_inv
- Toplam çözülmüş: **182**  ·  Baseline win-rate: **56.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (15 W / 5 L = 20 trade · +19.0pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `bb_extreme_lower ≠ True`
   - `regime_label = strong_trend_down`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0407 |
| 2 | `sar_bearish=False` | 0.0343 |
| 3 | `rsi_H4=[50,65)` | 0.0319 |
| 4 | `mtf_trend=all_down` | 0.0292 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0292 |
| 6 | `session=overlap` | 0.0290 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0288 |
| 8 | `rsi_H4=[30,50)` | 0.0252 |
| 9 | `bb_extreme_lower=True` | 0.0240 |
| 10 | `H1_ema_stack=mixed` | 0.0240 |
| 11 | `session=us` | 0.0236 |
| 12 | `session_phase=mid_session` | 0.0235 |
| 13 | `hour_bucket=12-16` | 0.0214 |
| 14 | `hour_bucket=16-20` | 0.0205 |
| 15 | `H4_ema_stack=down` | 0.0204 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **1117**  ·  Baseline win-rate: **46.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (25 W / 0 L = 25 trade · +53.2pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish = True`
   - `session ≠ overlap`
   - `dow = Fri`

**2. Win-rate 78.2%** (158 W / 44 L = 202 trade · +31.4pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend = mixed`
   - `H4_ema_stack = up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.7%** (8 W / 163 L = 171 trade · -42.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [3,+∞)`
   - `session_phase ≠ after_hours`

**2. Win-rate 7.7%** (3 W / 36 L = 39 trade · -39.1pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = weak_pro`
   - `adx_H1 ≠ [35,+∞)`

**3. Win-rate 15.6%** (7 W / 38 L = 45 trade · -31.2pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend ≠ mixed`
   - `sar_bearish ≠ True`

**4. Win-rate 18.8%** (21 W / 91 L = 112 trade · -28.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish = True`
   - `session = overlap`
   - `H4_ema_stack ≠ down`

**5. Win-rate 27.0%** (10 W / 27 L = 37 trade · -19.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish ≠ True`
   - `vix_chg1d = [3,+∞)`
   - `session ≠ overlap`

**6. Win-rate 29.7%** (11 W / 26 L = 37 trade · -17.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [3,+∞)`
   - `session_phase = after_hours`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0654 |
| 2 | `sar_bearish=False` | 0.0407 |
| 3 | `sar_bearish=True` | 0.0381 |
| 4 | `H1_ema_stack=up` | 0.0348 |
| 5 | `H1_adx_label=weak_trend` | 0.0315 |
| 6 | `macro_alignment=weak_pro` | 0.0297 |
| 7 | `adx_H4=[35,+∞)` | 0.0289 |
| 8 | `rsi_H1=[65,75)` | 0.0286 |
| 9 | `adx_H1=[35,+∞)` | 0.0244 |
| 10 | `dow=Tue` | 0.0236 |
| 11 | `H1_ema_stack=mixed` | 0.0220 |
| 12 | `mtf_trend=all_up` | 0.0214 |
| 13 | `adx_H1=[18,25)` | 0.0208 |
| 14 | `H4_ema_stack=NA` | 0.0202 |
| 15 | `rsi_H4=[30,50)` | 0.0178 |

---

## NDX.INDX · pulse3_inv
- Toplam çözülmüş: **427**  ·  Baseline win-rate: **54.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +45.7pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `H4_ema_stack = up`
   - `adx_H1 = [18,25)`

**2. Win-rate 81.8%** (36 W / 8 L = 44 trade · +27.5pp vs baseline)
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.1%** (3 W / 30 L = 33 trade · -45.2pp vs baseline)
   - `dow = Fri`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0470 |
| 2 | `dxy_chg1d=[0.5,+∞)` | 0.0389 |
| 3 | `H4_ema_stack=down` | 0.0371 |
| 4 | `H4_adx_label=trending` | 0.0343 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0306 |
| 6 | `adx_H1=[18,25)` | 0.0303 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0270 |
| 8 | `adx_H4=[−∞,18)` | 0.0251 |
| 9 | `session=us` | 0.0234 |
| 10 | `H1_adx_label=weak_trend` | 0.0233 |
| 11 | `volatility_regime=high` | 0.0228 |
| 12 | `us10y_chg1d=[-0.5,0)` | 0.0226 |
| 13 | `rsi_H4=[50,65)` | 0.0216 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0213 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0211 |

---

## NDX.INDX · smc
- Toplam çözülmüş: **104**  ·  Baseline win-rate: **29.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 24 L = 24 trade · -29.8pp vs baseline)
   - `macro_alignment = weak_pro`

**2. Win-rate 14.8%** (4 W / 23 L = 27 trade · -15.0pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.1072 |
| 2 | `macro_alignment=weak_pro` | 0.0931 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0545 |
| 4 | `dow=Thu` | 0.0504 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0474 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0472 |
| 7 | `adx_H4=[35,+∞)` | 0.0336 |
| 8 | `adx_H1=[−∞,18)` | 0.0298 |
| 9 | `session_phase=mid_session` | 0.0288 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0280 |
| 11 | `session=us` | 0.0256 |
| 12 | `adx_H1=[25,35)` | 0.0228 |
| 13 | `session_phase=close_drive` | 0.0213 |
| 14 | `H1_adx_label=trending` | 0.0212 |
| 15 | `session_phase=after_hours` | 0.0206 |

---

## USOIL.FOREX · ai_panel
- Toplam çözülmüş: **107**  ·  Baseline win-rate: **57.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +31.5pp vs baseline)
   - `M30_ema_stack = down`
   - `macd_atr_M30 ≠ [0,0.3)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +18.0pp vs baseline)
   - `M30_ema_stack = down`
   - `macd_atr_M30 = [0,0.3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.0%** (4 W / 21 L = 25 trade · -41.0pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0935 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0819 |
| 3 | `rsi_H4=[50,65)` | 0.0576 |
| 4 | `M30_ema_stack=up` | 0.0563 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0429 |
| 6 | `rsi_H4=[30,50)` | 0.0416 |
| 7 | `mtf_trend=all_down` | 0.0398 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0388 |
| 9 | `rsi_M30=[50,65)` | 0.0306 |
| 10 | `H1_ema_stack=down` | 0.0245 |
| 11 | `rsi_H1=[50,65)` | 0.0236 |
| 12 | `mtf_trend=mixed` | 0.0224 |
| 13 | `adx_H1=[18,25)` | 0.0215 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0204 |
| 15 | `H4_adx_label=weak_trend` | 0.0195 |

---

## USOIL.FOREX · emel
- Toplam çözülmüş: **203**  ·  Baseline win-rate: **31.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +51.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -31.0pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label = trending`

**2. Win-rate 4.5%** (1 W / 21 L = 22 trade · -26.5pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label ≠ trending`

**3. Win-rate 28.6%** (8 W / 20 L = 28 trade · -2.4pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label = trending`

**4. Win-rate 29.2%** (7 W / 17 L = 24 trade · -1.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session = overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0935 |
| 2 | `H1_ema_stack=up` | 0.0680 |
| 3 | `H4_ema_stack=mixed` | 0.0573 |
| 4 | `mtf_trend=all_down` | 0.0547 |
| 5 | `mtf_trend=mixed` | 0.0494 |
| 6 | `H4_adx_label=trending` | 0.0431 |
| 7 | `rsi_H4=[65,75)` | 0.0336 |
| 8 | `dow=Mon` | 0.0271 |
| 9 | `H4_adx_label=ranging` | 0.0204 |
| 10 | `H1_ema_stack=down` | 0.0171 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0167 |
| 12 | `regime_label=transition` | 0.0166 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0162 |
| 14 | `M30_ema_stack=up` | 0.0155 |
| 15 | `session=overlap` | 0.0154 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **614**  ·  Baseline win-rate: **57.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 99.1%** (108 W / 1 L = 109 trade · +41.3pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 = [30,50)`
   - `dist_low_M30 = [1.5,+∞)`
   - `dow ≠ Wed`

**2. Win-rate 95.5%** (21 W / 1 L = 22 trade · +37.7pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 = [18,25)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · +32.7pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 = [18,25)`
   - `H4_adx_label = weak_trend`

**4. Win-rate 86.8%** (33 W / 5 L = 38 trade · +29.0pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 = [30,50)`
   - `dist_low_M30 = [1.5,+∞)`
   - `dow = Wed`

**5. Win-rate 81.6%** (111 W / 25 L = 136 trade · +23.8pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 = [30,50)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 75 L = 75 trade · -57.8pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `M30_ema_stack = up`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 8.1%** (3 W / 34 L = 37 trade · -49.7pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `M30_ema_stack = up`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 24.1%** (21 W / 66 L = 87 trade · -33.7pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 ≠ [18,25)`
   - `mtf_trend = mixed`

**4. Win-rate 26.3%** (10 W / 28 L = 38 trade · -31.5pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `M30_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=up` | 0.0920 |
| 2 | `rsi_H4=[50,65)` | 0.0728 |
| 3 | `rsi_H4=[30,50)` | 0.0603 |
| 4 | `rsi_M30=[30,50)` | 0.0539 |
| 5 | `M30_ema_stack=down` | 0.0499 |
| 6 | `rsi_H1=[30,50)` | 0.0464 |
| 7 | `mtf_trend=all_down` | 0.0421 |
| 8 | `rsi_H1=[50,65)` | 0.0310 |
| 9 | `mtf_trend=mixed` | 0.0244 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0238 |
| 11 | `rsi_M30=[50,65)` | 0.0211 |
| 12 | `dist_high_M30=[1.5,+∞)` | 0.0208 |
| 13 | `H1_ema_stack=down` | 0.0206 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0191 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0169 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **639**  ·  Baseline win-rate: **49.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.5%** (79 W / 2 L = 81 trade · +47.9pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +38.3pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label ≠ trending`
   - `H4_adx_label ≠ ranging`

**3. Win-rate 83.3%** (30 W / 6 L = 36 trade · +33.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [0.7,1.5)`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · +29.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 43 L = 43 trade · -49.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 4.8%** (2 W / 40 L = 42 trade · -44.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -44.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d = [3,+∞)`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -35.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.6pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.1071 |
| 2 | `rsi_H4=[50,65)` | 0.0539 |
| 3 | `mtf_trend=all_down` | 0.0418 |
| 4 | `mtf_trend=mixed` | 0.0374 |
| 5 | `M30_adx_label=trending` | 0.0274 |
| 6 | `dow=Mon` | 0.0263 |
| 7 | `H1_ema_stack=down` | 0.0261 |
| 8 | `rsi_H1=[30,50)` | 0.0260 |
| 9 | `M30_ema_stack=up` | 0.0258 |
| 10 | `H4_ema_stack=down` | 0.0258 |
| 11 | `rsi_H4=[30,50)` | 0.0239 |
| 12 | `M30_ema_stack=mixed` | 0.0210 |
| 13 | `dow=Fri` | 0.0183 |
| 14 | `H4_ema_stack=mixed` | 0.0171 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0168 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **639**  ·  Baseline win-rate: **49.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.5%** (79 W / 2 L = 81 trade · +48.0pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +38.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label ≠ trending`
   - `H4_adx_label ≠ ranging`

**3. Win-rate 83.3%** (30 W / 6 L = 36 trade · +33.8pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [0.7,1.5)`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · +29.7pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 43 L = 43 trade · -49.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 4.8%** (2 W / 40 L = 42 trade · -44.7pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -44.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d = [3,+∞)`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -35.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.5pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.1051 |
| 2 | `rsi_H4=[50,65)` | 0.0608 |
| 3 | `mtf_trend=mixed` | 0.0440 |
| 4 | `mtf_trend=all_down` | 0.0420 |
| 5 | `M30_adx_label=trending` | 0.0291 |
| 6 | `H1_ema_stack=down` | 0.0272 |
| 7 | `M30_ema_stack=up` | 0.0253 |
| 8 | `H4_ema_stack=down` | 0.0247 |
| 9 | `rsi_H1=[30,50)` | 0.0239 |
| 10 | `dow=Mon` | 0.0234 |
| 11 | `rsi_H4=[30,50)` | 0.0226 |
| 12 | `dow=Fri` | 0.0218 |
| 13 | `M30_ema_stack=mixed` | 0.0195 |
| 14 | `rsi_H1=[50,65)` | 0.0171 |
| 15 | `rsi_M30=[30,50)` | 0.0167 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **637**  ·  Baseline win-rate: **49.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.5%** (79 W / 2 L = 81 trade · +47.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +38.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label ≠ trending`
   - `H4_adx_label ≠ ranging`

**3. Win-rate 83.3%** (30 W / 6 L = 36 trade · +33.5pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [0.7,1.5)`

**4. Win-rate 82.6%** (19 W / 4 L = 23 trade · +32.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 43 L = 43 trade · -49.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 4.8%** (2 W / 40 L = 42 trade · -45.0pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -44.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d = [3,+∞)`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -35.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.8pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.1083 |
| 2 | `rsi_H4=[50,65)` | 0.0544 |
| 3 | `mtf_trend=mixed` | 0.0434 |
| 4 | `mtf_trend=all_down` | 0.0415 |
| 5 | `M30_ema_stack=up` | 0.0277 |
| 6 | `H4_ema_stack=down` | 0.0267 |
| 7 | `rsi_H4=[30,50)` | 0.0266 |
| 8 | `M30_adx_label=trending` | 0.0261 |
| 9 | `rsi_H1=[30,50)` | 0.0253 |
| 10 | `dow=Mon` | 0.0237 |
| 11 | `H4_ema_stack=mixed` | 0.0209 |
| 12 | `M30_ema_stack=mixed` | 0.0206 |
| 13 | `H1_ema_stack=down` | 0.0204 |
| 14 | `rsi_M30=[30,50)` | 0.0200 |
| 15 | `rsi_H1=[50,65)` | 0.0180 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **642**  ·  Baseline win-rate: **49.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.6%** (80 W / 2 L = 82 trade · +48.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +38.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label ≠ trending`
   - `H4_adx_label ≠ ranging`

**3. Win-rate 83.3%** (30 W / 6 L = 36 trade · +34.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 43 L = 43 trade · -49.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 4.9%** (2 W / 39 L = 41 trade · -44.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -44.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d = [3,+∞)`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -35.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.2pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.1133 |
| 2 | `rsi_H4=[50,65)` | 0.0529 |
| 3 | `mtf_trend=mixed` | 0.0444 |
| 4 | `mtf_trend=all_down` | 0.0419 |
| 5 | `M30_adx_label=trending` | 0.0300 |
| 6 | `H1_ema_stack=down` | 0.0284 |
| 7 | `rsi_H4=[30,50)` | 0.0281 |
| 8 | `H4_ema_stack=down` | 0.0272 |
| 9 | `rsi_H1=[30,50)` | 0.0255 |
| 10 | `M30_ema_stack=up` | 0.0251 |
| 11 | `dow=Mon` | 0.0215 |
| 12 | `M30_ema_stack=mixed` | 0.0183 |
| 13 | `dow=Fri` | 0.0177 |
| 14 | `H4_ema_stack=mixed` | 0.0169 |
| 15 | `rsi_M30=[30,50)` | 0.0133 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **642**  ·  Baseline win-rate: **49.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.6%** (80 W / 2 L = 82 trade · +48.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +38.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label ≠ trending`
   - `H4_adx_label ≠ ranging`

**3. Win-rate 83.3%** (30 W / 6 L = 36 trade · +34.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `M30_adx_label = trending`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 43 L = 43 trade · -49.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 4.8%** (2 W / 40 L = 42 trade · -44.4pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -44.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `vix_chg1d = [3,+∞)`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -35.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.2pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.1152 |
| 2 | `rsi_H4=[50,65)` | 0.0576 |
| 3 | `mtf_trend=mixed` | 0.0429 |
| 4 | `mtf_trend=all_down` | 0.0379 |
| 5 | `M30_adx_label=trending` | 0.0307 |
| 6 | `rsi_H1=[30,50)` | 0.0276 |
| 7 | `H1_ema_stack=down` | 0.0268 |
| 8 | `dow=Mon` | 0.0261 |
| 9 | `rsi_H4=[30,50)` | 0.0256 |
| 10 | `H4_ema_stack=down` | 0.0243 |
| 11 | `M30_ema_stack=up` | 0.0226 |
| 12 | `H4_ema_stack=mixed` | 0.0196 |
| 13 | `M30_ema_stack=mixed` | 0.0185 |
| 14 | `dow=Fri` | 0.0168 |
| 15 | `rsi_H1=[50,65)` | 0.0156 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **3427**  ·  Baseline win-rate: **39.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.5%** (65 W / 1 L = 66 trade · +59.3pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`
   - `dow = Thu`

**2. Win-rate 82.4%** (103 W / 22 L = 125 trade · +43.2pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`
   - `dow ≠ Thu`

**3. Win-rate 81.8%** (27 W / 6 L = 33 trade · +42.6pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label = trending`
   - `session_phase ≠ off_hours`

**4. Win-rate 78.9%** (131 W / 35 L = 166 trade · +39.7pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H1_adx_label = ranging`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 55 L = 55 trade · -39.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 = [0,2)`
   - `rsi_H1 = [65,75)`
   - `regime_label ≠ transition`

**2. Win-rate 6.3%** (18 W / 266 L = 284 trade · -32.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 8.1%** (6 W / 68 L = 74 trade · -31.1pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `adx_M30 ≠ [18,25)`

**4. Win-rate 18.3%** (23 W / 103 L = 126 trade · -20.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `H4_ema_stack ≠ mixed`

**5. Win-rate 18.3%** (11 W / 49 L = 60 trade · -20.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 = [0,2)`
   - `rsi_H1 = [65,75)`
   - `regime_label = transition`

**6. Win-rate 23.6%** (85 W / 275 L = 360 trade · -15.6pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**7. Win-rate 31.1%** (237 W / 526 L = 763 trade · -8.1pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `consec_green_M30 = [0,2)`
   - `rsi_H1 ≠ [65,75)`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0903 |
| 2 | `consec_red_M30=[2,4)` | 0.0544 |
| 3 | `consec_green_M30=[0,2)` | 0.0540 |
| 4 | `consec_green_M30=[2,4)` | 0.0262 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0255 |
| 6 | `bb_pctb_M30=[−∞,0.2)` | 0.0204 |
| 7 | `macro_alignment=strong_against` | 0.0186 |
| 8 | `bb_pctb_M30=[0.8,+∞)` | 0.0184 |
| 9 | `H1_ema_stack=up` | 0.0153 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0153 |
| 11 | `H1_adx_label=ranging` | 0.0146 |
| 12 | `bb_extreme_upper=False` | 0.0127 |
| 13 | `bb_extreme_lower=True` | 0.0127 |
| 14 | `adx_H1=[−∞,18)` | 0.0124 |
| 15 | `dist_high_M30=[0.3,0.7)` | 0.0121 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **1883**  ·  Baseline win-rate: **49.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (43 W / 0 L = 43 trade · +50.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `adx_M30 = [35,+∞)`
   - `rsi_H4 = [30,50)`

**2. Win-rate 100.0%** (28 W / 0 L = 28 trade · +50.8pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `vix_chg1d = [−∞,-3)`

**3. Win-rate 93.1%** (362 W / 27 L = 389 trade · +43.9pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `adx_H4 ≠ [35,+∞)`

**4. Win-rate 84.6%** (44 W / 8 L = 52 trade · +35.4pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 ≠ [50,65)`
   - `dow = Tue`

**5. Win-rate 81.8%** (18 W / 4 L = 22 trade · +32.6pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `adx_M30 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.0%** (1 W / 32 L = 33 trade · -46.2pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**2. Win-rate 3.4%** (12 W / 345 L = 357 trade · -45.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `macro_alignment ≠ strong_pro`

**3. Win-rate 13.1%** (16 W / 106 L = 122 trade · -36.1pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = strong_against`

**4. Win-rate 26.9%** (7 W / 19 L = 26 trade · -22.3pp vs baseline)
   - `M30_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d = [−∞,-0.5)`

**5. Win-rate 27.3%** (6 W / 16 L = 22 trade · -21.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `macro_alignment = strong_pro`

**6. Win-rate 31.0%** (9 W / 20 L = 29 trade · -18.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0541 |
| 2 | `mtf_trend=all_down` | 0.0537 |
| 3 | `M30_adx_label=trending` | 0.0507 |
| 4 | `mtf_trend=mixed` | 0.0441 |
| 5 | `rsi_H4=[50,65)` | 0.0376 |
| 6 | `rsi_M30=[30,50)` | 0.0357 |
| 7 | `H4_ema_stack=down` | 0.0321 |
| 8 | `rsi_M30=[50,65)` | 0.0274 |
| 9 | `H4_ema_stack=mixed` | 0.0259 |
| 10 | `dist_high_M30=[1.5,+∞)` | 0.0225 |
| 11 | `rsi_H1=[30,50)` | 0.0221 |
| 12 | `rsi_H1=[50,65)` | 0.0215 |
| 13 | `bb_pctb_M30=[0.2,0.5)` | 0.0203 |
| 14 | `adx_M30=[−∞,18)` | 0.0180 |
| 15 | `adx_M30=[35,+∞)` | 0.0179 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **2869**  ·  Baseline win-rate: **49.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (144 W / 13 L = 157 trade · +41.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `regime_label ≠ transition`
   - `rsi_M30 = [30,50)`

**2. Win-rate 90.5%** (76 W / 8 L = 84 trade · +40.6pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment = neutral`
   - `us10y_chg1d ≠ [-0.5,0)`

**3. Win-rate 87.0%** (715 W / 107 L = 822 trade · +37.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `bb_extreme_upper = False`
   - `H1_ema_stack = down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.2%** (22 W / 333 L = 355 trade · -43.7pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label ≠ trending`
   - `H4_ema_stack = down`

**2. Win-rate 8.0%** (4 W / 46 L = 50 trade · -41.9pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment ≠ neutral`
   - `bb_pctb_M30 = [0.2,0.5)`

**3. Win-rate 19.5%** (47 W / 194 L = 241 trade · -30.4pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `regime_label = transition`
   - `H4_ema_stack = down`

**4. Win-rate 19.6%** (60 W / 246 L = 306 trade · -30.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label ≠ trending`
   - `H4_ema_stack ≠ down`

**5. Win-rate 24.3%** (9 W / 28 L = 37 trade · -25.6pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `bb_extreme_upper ≠ False`

**6. Win-rate 27.0%** (47 W / 127 L = 174 trade · -22.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label = trending`
   - `dow ≠ Fri`

**7. Win-rate 32.6%** (15 W / 31 L = 46 trade · -17.3pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `bb_extreme_upper = False`
   - `H1_ema_stack ≠ down`

**8. Win-rate 34.4%** (11 W / 21 L = 32 trade · -15.5pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment = neutral`
   - `us10y_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[50,65)` | 0.0728 |
| 2 | `M30_ema_stack=down` | 0.0654 |
| 3 | `mtf_trend=mixed` | 0.0527 |
| 4 | `mtf_trend=all_down` | 0.0455 |
| 5 | `M30_ema_stack=up` | 0.0354 |
| 6 | `rsi_H1=[30,50)` | 0.0327 |
| 7 | `rsi_H4=[30,50)` | 0.0298 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0273 |
| 9 | `M30_adx_label=trending` | 0.0220 |
| 10 | `H1_ema_stack=down` | 0.0211 |
| 11 | `adx_M30=[−∞,18)` | 0.0193 |
| 12 | `dow=Mon` | 0.0186 |
| 13 | `rsi_H1=[50,65)` | 0.0186 |
| 14 | `M30_adx_label=ranging` | 0.0161 |
| 15 | `H4_ema_stack=mixed` | 0.0158 |

---

## USOIL.FOREX · smc
- Toplam çözülmüş: **485**  ·  Baseline win-rate: **44.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +55.5pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d = [−∞,-0.5)`
   - `macd_atr_M30 = [-0.3,0)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 95.5%** (21 W / 1 L = 22 trade · +51.0pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d = [−∞,-0.5)`
   - `macd_atr_M30 = [-0.3,0)`
   - `dist_high_M30 = [1.5,+∞)`

**3. Win-rate 92.3%** (24 W / 2 L = 26 trade · +47.8pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack = down`

**4. Win-rate 75.8%** (25 W / 8 L = 33 trade · +31.3pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_M30 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.1%** (5 W / 93 L = 98 trade · -39.4pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `M30_ema_stack ≠ mixed`
   - `M30_adx_label ≠ ranging`
   - `H1_adx_label ≠ ranging`

**2. Win-rate 29.4%** (15 W / 36 L = 51 trade · -15.1pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ down`
   - `ml_confidence_bucket ≠ [−∞,50)`

**3. Win-rate 30.9%** (17 W / 38 L = 55 trade · -13.6pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `M30_ema_stack ≠ mixed`
   - `M30_adx_label ≠ ranging`
   - `H1_adx_label = ranging`

**4. Win-rate 33.3%** (23 W / 46 L = 69 trade · -11.2pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_M30 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=mixed` | 0.0440 |
| 2 | `rsi_H1=[30,50)` | 0.0406 |
| 3 | `rsi_H1=[50,65)` | 0.0393 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0380 |
| 5 | `mtf_trend=mixed` | 0.0377 |
| 6 | `adx_M30=[35,+∞)` | 0.0306 |
| 7 | `mtf_trend=all_down` | 0.0289 |
| 8 | `us10y_chg1d=[−∞,-0.5)` | 0.0285 |
| 9 | `vix_chg1d=[0,3)` | 0.0279 |
| 10 | `adx_H1=[−∞,18)` | 0.0275 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0231 |
| 12 | `dow=Mon` | 0.0216 |
| 13 | `H1_ema_stack=down` | 0.0214 |
| 14 | `H1_adx_label=trending` | 0.0179 |
| 15 | `dist_low_M30=[0.7,1.5)` | 0.0175 |

---

## XAUUSD · ai_panel
- Toplam çözülmüş: **172**  ·  Baseline win-rate: **66.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.9%** (24 W / 3 L = 27 trade · +22.0pp vs baseline)
   - `dist_low_M30 = [0.3,0.7)`

**2. Win-rate 87.0%** (20 W / 3 L = 23 trade · +20.1pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `near_support ≠ False`

**3. Win-rate 82.6%** (19 W / 4 L = 23 trade · +15.7pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `near_support = False`
   - `dow = Tue`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_low_M30=[0.3,0.7)` | 0.0471 |
| 2 | `H1_adx_label=trending` | 0.0441 |
| 3 | `dow=Tue` | 0.0319 |
| 4 | `sar_bearish=True` | 0.0311 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0294 |
| 6 | `dist_low_M30=[0.7,1.5)` | 0.0285 |
| 7 | `rsi_M30=[50,65)` | 0.0246 |
| 8 | `adx_M30=[25,35)` | 0.0246 |
| 9 | `consec_green_M30=[0,2)` | 0.0238 |
| 10 | `adx_H1=[18,25)` | 0.0238 |
| 11 | `M30_ema_stack=mixed` | 0.0237 |
| 12 | `dist_low_M30=[1.5,+∞)` | 0.0230 |
| 13 | `session=us` | 0.0202 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0196 |
| 15 | `near_support=False` | 0.0190 |

---

## XAUUSD · emel
- Toplam çözülmüş: **215**  ·  Baseline win-rate: **81.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (20 W / 0 L = 20 trade · +18.6pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 = [30,50)`
   - `dow = Wed`

**2. Win-rate 100.0%** (38 W / 0 L = 38 trade · +18.6pp vs baseline)
   - `macro_alignment = weak_against`
   - `M30_ema_stack = down`

**3. Win-rate 87.9%** (29 W / 4 L = 33 trade · +6.5pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 = [35,+∞)`

**4. Win-rate 86.2%** (25 W / 4 L = 29 trade · +4.8pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 = [30,50)`
   - `dow ≠ Wed`

**5. Win-rate 86.2%** (25 W / 4 L = 29 trade · +4.8pp vs baseline)
   - `macro_alignment = weak_against`
   - `M30_ema_stack ≠ down`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0693 |
| 2 | `adx_H1=[35,+∞)` | 0.0628 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0574 |
| 4 | `macro_alignment=weak_against` | 0.0546 |
| 5 | `mtf_trend=all_down` | 0.0414 |
| 6 | `dist_low_M30=[1.5,+∞)` | 0.0366 |
| 7 | `atr_ratio_M30=[1,1.3)` | 0.0345 |
| 8 | `adx_M30=[35,+∞)` | 0.0254 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0250 |
| 10 | `M30_ema_stack=down` | 0.0233 |
| 11 | `mtf_trend=all_up` | 0.0227 |
| 12 | `consec_red_M30=[2,4)` | 0.0210 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0205 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0185 |
| 15 | `M30_ema_stack=up` | 0.0152 |

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

## XAUUSD · ml:aggressive
- Toplam çözülmüş: **491**  ·  Baseline win-rate: **49.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +38.0pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 = [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.8%** (4 W / 23 L = 27 trade · -34.7pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `us10y_chg1d = [0,0.5)`

**2. Win-rate 22.2%** (10 W / 35 L = 45 trade · -27.3pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dist_high_M30 = [1.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0497 |
| 2 | `macro_alignment=weak_pro` | 0.0467 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0351 |
| 4 | `rsi_M30=[50,65)` | 0.0245 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0225 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0223 |
| 7 | `atr_ratio_M30=[0.7,1)` | 0.0178 |
| 8 | `rsi_M30=[30,50)` | 0.0173 |
| 9 | `consec_green_M30=[0,2)` | 0.0169 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0169 |
| 11 | `rsi_H1=[30,50)` | 0.0161 |
| 12 | `bb_extreme_lower=True` | 0.0161 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0156 |
| 14 | `H1_adx_label=trending` | 0.0143 |
| 15 | `bb_extreme_lower=False` | 0.0138 |

---

## XAUUSD · ml:balanced
- Toplam çözülmüş: **493**  ·  Baseline win-rate: **48.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +38.6pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 = [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 12.5%** (3 W / 21 L = 24 trade · -36.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 24.2%** (8 W / 25 L = 33 trade · -24.7pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 25.8%** (8 W / 23 L = 31 trade · -23.1pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0465 |
| 2 | `macro_alignment=weak_pro` | 0.0439 |
| 3 | `consec_green_M30=[0,2)` | 0.0294 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0284 |
| 5 | `rsi_M30=[50,65)` | 0.0249 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0245 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0198 |
| 8 | `macro_alignment=weak_against` | 0.0176 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0171 |
| 10 | `rsi_M30=[30,50)` | 0.0167 |
| 11 | `bb_extreme_lower=True` | 0.0164 |
| 12 | `adx_H1=[18,25)` | 0.0157 |
| 13 | `sar_bearish=False` | 0.0152 |
| 14 | `ml_confidence_bucket=[80,+∞)` | 0.0149 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0147 |

---

## XAUUSD · ml:full_power
- Toplam çözülmüş: **489**  ·  Baseline win-rate: **48.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.1%** (31 W / 5 L = 36 trade · +37.4pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [50,65)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.5%** (9 W / 49 L = 58 trade · -33.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ weak_against`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -13.7pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0369 |
| 2 | `macro_alignment=weak_pro` | 0.0335 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0279 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0271 |
| 5 | `rsi_M30=[50,65)` | 0.0258 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0238 |
| 7 | `consec_red_M30=[2,4)` | 0.0187 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0187 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0186 |
| 10 | `macro_alignment=weak_against` | 0.0164 |
| 11 | `consec_green_M30=[0,2)` | 0.0162 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0159 |
| 13 | `bb_extreme_lower=True` | 0.0158 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0156 |
| 15 | `consec_red_M30=[0,2)` | 0.0151 |

---

## XAUUSD · ml:main
- Toplam çözülmüş: **491**  ·  Baseline win-rate: **49.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.5%** (21 W / 3 L = 24 trade · +38.2pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 = [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.9%** (5 W / 31 L = 36 trade · -35.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `M30_adx_label = trending`

**2. Win-rate 24.2%** (8 W / 25 L = 33 trade · -25.1pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 28.6%** (6 W / 15 L = 21 trade · -20.7pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0595 |
| 2 | `macro_alignment=weak_pro` | 0.0370 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0328 |
| 4 | `consec_green_M30=[0,2)` | 0.0298 |
| 5 | `rsi_M30=[50,65)` | 0.0278 |
| 6 | `consec_red_M30=[2,4)` | 0.0225 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0213 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0197 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0186 |
| 10 | `sar_bearish=True` | 0.0180 |
| 11 | `consec_red_M30=[0,2)` | 0.0167 |
| 12 | `macro_alignment=weak_against` | 0.0164 |
| 13 | `bb_extreme_lower=True` | 0.0163 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0153 |
| 15 | `H1_adx_label=trending` | 0.0149 |

---

## XAUUSD · ml:main_inv
- Toplam çözülmüş: **252**  ·  Baseline win-rate: **49.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.4%** (49 W / 16 L = 65 trade · +26.2pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment ≠ weak_pro`
   - `ml_confidence_bucket ≠ [60,70)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -29.2pp vs baseline)
   - `consec_red_M30 = [2,4)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 23.8%** (5 W / 16 L = 21 trade · -25.4pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment = weak_pro`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 33.3%** (9 W / 18 L = 27 trade · -15.9pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment ≠ weak_pro`
   - `ml_confidence_bucket = [60,70)`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0513 |
| 2 | `consec_red_M30=[2,4)` | 0.0496 |
| 3 | `consec_red_M30=[0,2)` | 0.0452 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0371 |
| 5 | `H1_adx_label=trending` | 0.0266 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0265 |
| 7 | `adx_H1=[35,+∞)` | 0.0254 |
| 8 | `bb_pctb_M30=[−∞,0.2)` | 0.0225 |
| 9 | `session=asia` | 0.0204 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0201 |
| 11 | `macd_atr_M30=[-0.3,0)` | 0.0193 |
| 12 | `dist_low_M30=[−∞,0.3)` | 0.0191 |
| 13 | `macro_alignment=weak_against` | 0.0171 |
| 14 | `adx_M30=[35,+∞)` | 0.0170 |
| 15 | `adx_H1=[−∞,18)` | 0.0169 |

---

## XAUUSD · ml:ultra_safe
- Toplam çözülmüş: **491**  ·  Baseline win-rate: **49.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (30 W / 3 L = 33 trade · +41.8pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [50,65)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (8 W / 48 L = 56 trade · -34.8pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ weak_against`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0437 |
| 2 | `macro_alignment=weak_pro` | 0.0364 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0304 |
| 4 | `rsi_M30=[50,65)` | 0.0268 |
| 5 | `consec_green_M30=[0,2)` | 0.0254 |
| 6 | `consec_red_M30=[2,4)` | 0.0200 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0194 |
| 8 | `rsi_M30=[30,50)` | 0.0184 |
| 9 | `rsi_H1=[50,65)` | 0.0183 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0172 |
| 11 | `macd_atr_M30=[0,0.3)` | 0.0163 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0156 |
| 13 | `macro_alignment=weak_against` | 0.0156 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0154 |
| 15 | `sar_bearish=True` | 0.0154 |

---

## XAUUSD · ml_cross_xau_nasdaq
- Toplam çözülmüş: **799**  ·  Baseline win-rate: **40.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.6%** (70 W / 1 L = 71 trade · +57.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +34.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket = 00-04`
   - `macro_alignment ≠ strong_pro`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 67 L = 67 trade · -40.8pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 18.8%** (25 W / 108 L = 133 trade · -22.0pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `hour_bucket ≠ 16-20`

**3. Win-rate 18.9%** (7 W / 30 L = 37 trade · -21.9pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label = ranging`

**4. Win-rate 21.4%** (6 W / 22 L = 28 trade · -19.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label ≠ ranging`
   - `ml_confidence_bucket = [−∞,50)`

**5. Win-rate 24.6%** (34 W / 104 L = 138 trade · -16.2pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0722 |
| 2 | `M30_ema_stack=down` | 0.0651 |
| 3 | `adx_M30=[35,+∞)` | 0.0480 |
| 4 | `dxy_chg1d=[0.5,+∞)` | 0.0415 |
| 5 | `macro_alignment=weak_pro` | 0.0359 |
| 6 | `macro_alignment=weak_against` | 0.0342 |
| 7 | `dist_high_M30=[1.5,+∞)` | 0.0328 |
| 8 | `mtf_trend=NA` | 0.0272 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0251 |
| 10 | `M30_ema_stack=NA` | 0.0238 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0233 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0226 |
| 13 | `adx_H1=[−∞,18)` | 0.0212 |
| 14 | `dow=Mon` | 0.0203 |
| 15 | `H1_adx_label=ranging` | 0.0188 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv
- Toplam çözülmüş: **573**  ·  Baseline win-rate: **28.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 63 L = 63 trade · -28.4pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment = weak_pro`
   - `M30_ema_stack ≠ up`

**2. Win-rate 17.7%** (25 W / 116 L = 141 trade · -10.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment ≠ weak_pro`
   - `volatility_regime = normal`
   - `M30_adx_label = trending`

**3. Win-rate 20.0%** (4 W / 16 L = 20 trade · -8.4pp vs baseline)
   - `mtf_trend = all_down`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dist_high_M30 ≠ [0.7,1.5)`

**4. Win-rate 21.1%** (8 W / 30 L = 38 trade · -7.3pp vs baseline)
   - `mtf_trend = all_down`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 28.6%** (8 W / 20 L = 28 trade · 0.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment = weak_pro`
   - `M30_ema_stack = up`

**6. Win-rate 30.1%** (28 W / 65 L = 93 trade · 1.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment ≠ weak_pro`
   - `volatility_regime = normal`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0496 |
| 2 | `macro_alignment=weak_pro` | 0.0494 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0445 |
| 4 | `mtf_trend=all_down` | 0.0441 |
| 5 | `M30_ema_stack=NA` | 0.0215 |
| 6 | `mtf_trend=NA` | 0.0208 |
| 7 | `macro_alignment=weak_against` | 0.0183 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0181 |
| 9 | `dist_high_M30=[0.3,0.7)` | 0.0179 |
| 10 | `dow=Mon` | 0.0177 |
| 11 | `hour_bucket=12-16` | 0.0173 |
| 12 | `adx_M30=[35,+∞)` | 0.0171 |
| 13 | `vix_chg1d=[-3,0)` | 0.0157 |
| 14 | `adx_H1=[35,+∞)` | 0.0153 |
| 15 | `sar_bearish=True` | 0.0153 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **3012**  ·  Baseline win-rate: **21.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 101 L = 101 trade · -21.2pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime = normal`
   - `us10y_chg1d ≠ [0,0.5)`

**2. Win-rate 1.1%** (1 W / 94 L = 95 trade · -20.1pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket ≠ 20-24`
   - `vix_chg1d ≠ [-3,0)`

**3. Win-rate 3.7%** (1 W / 26 L = 27 trade · -17.5pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime = normal`
   - `us10y_chg1d = [0,0.5)`

**4. Win-rate 5.6%** (2 W / 34 L = 36 trade · -15.6pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 ≠ [4,6)`
   - `H1_adx_label = weak_trend`
   - `dow = Fri`

**5. Win-rate 7.0%** (3 W / 40 L = 43 trade · -14.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket ≠ 20-24`
   - `vix_chg1d = [-3,0)`

**6. Win-rate 8.3%** (2 W / 22 L = 24 trade · -12.9pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime ≠ normal`

**7. Win-rate 9.9%** (53 W / 481 L = 534 trade · -11.3pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 ≠ [4,6)`
   - `H1_adx_label ≠ weak_trend`
   - `ml_confidence_bucket ≠ [60,70)`

**8. Win-rate 13.6%** (3 W / 19 L = 22 trade · -7.6pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket = 20-24`

**9. Win-rate 13.9%** (62 W / 384 L = 446 trade · -7.3pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack ≠ NA`
   - `vix_chg1d = [3,+∞)`
   - `dist_low_M30 ≠ [0.7,1.5)`

**10. Win-rate 20.3%** (101 W / 396 L = 497 trade · -0.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack ≠ NA`
   - `vix_chg1d ≠ [3,+∞)`
   - `sar_bearish = True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0248 |
| 2 | `M30_ema_stack=NA` | 0.0244 |
| 3 | `bb_pctb_M30=[−∞,0.2)` | 0.0239 |
| 4 | `consec_green_M30=[2,4)` | 0.0238 |
| 5 | `M30_ema_stack=down` | 0.0229 |
| 6 | `rsi_M30=[65,75)` | 0.0223 |
| 7 | `H1_adx_label=weak_trend` | 0.0215 |
| 8 | `mtf_trend=NA` | 0.0212 |
| 9 | `sar_bearish=False` | 0.0210 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0205 |
| 11 | `adx_H1=[18,25)` | 0.0196 |
| 12 | `consec_red_M30=[4,6)` | 0.0191 |
| 13 | `dow=Fri` | 0.0188 |
| 14 | `sar_bearish=True` | 0.0186 |
| 15 | `adx_M30=[35,+∞)` | 0.0185 |

---

## XAUUSD · pulse1_inv
- Toplam çözülmüş: **833**  ·  Baseline win-rate: **46.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.6%** (146 W / 33 L = 179 trade · +34.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment ≠ weak_pro`
   - `macro_alignment ≠ strong_against`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.6%** (8 W / 29 L = 37 trade · -25.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**2. Win-rate 25.3%** (67 W / 198 L = 265 trade · -21.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 12-16`

**3. Win-rate 30.0%** (6 W / 14 L = 20 trade · -16.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `hour_bucket = 00-04`
   - `mtf_trend = all_down`

**4. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment = weak_pro`

**5. Win-rate 33.3%** (8 W / 16 L = 24 trade · -13.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper ≠ False`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `sar_bearish ≠ False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0917 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0427 |
| 3 | `adx_H1=[35,+∞)` | 0.0388 |
| 4 | `M30_adx_label=trending` | 0.0372 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0331 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0317 |
| 7 | `adx_H1=[−∞,18)` | 0.0249 |
| 8 | `H1_adx_label=ranging` | 0.0236 |
| 9 | `H1_adx_label=trending` | 0.0229 |
| 10 | `dist_high_M30=[1.5,+∞)` | 0.0208 |
| 11 | `macro_alignment=weak_against` | 0.0200 |
| 12 | `dow=Fri` | 0.0196 |
| 13 | `M30_adx_label=ranging` | 0.0195 |
| 14 | `adx_M30=[25,35)` | 0.0190 |
| 15 | `macro_alignment=weak_pro` | 0.0171 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **2682**  ·  Baseline win-rate: **24.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.0%** (50 W / 1 L = 51 trade · +73.8pp vs baseline)
   - `dow = Fri`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +50.8pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 = [35,+∞)`
   - `rsi_M30 = [65,75)`
   - `sar_bearish ≠ False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 50 L = 50 trade · -24.2pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 ≠ [35,+∞)`
   - `M30_ema_stack = NA`
   - `dow = Mon`

**2. Win-rate 3.4%** (1 W / 28 L = 29 trade · -20.8pp vs baseline)
   - `dow = Fri`
   - `vix_chg1d = [3,+∞)`
   - `macd_atr_M30 = [−∞,-0.3)`

**3. Win-rate 6.8%** (35 W / 476 L = 511 trade · -17.4pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 = [35,+∞)`
   - `rsi_M30 ≠ [65,75)`
   - `rsi_M30 ≠ [50,65)`

**4. Win-rate 9.7%** (3 W / 28 L = 31 trade · -14.5pp vs baseline)
   - `dow = Fri`
   - `vix_chg1d = [3,+∞)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`
   - `session = europe`

**5. Win-rate 10.7%** (9 W / 75 L = 84 trade · -13.5pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 ≠ [35,+∞)`
   - `M30_ema_stack = NA`
   - `dow ≠ Mon`

**6. Win-rate 13.3%** (4 W / 26 L = 30 trade · -10.9pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 = [35,+∞)`
   - `rsi_M30 = [65,75)`
   - `sar_bearish = False`

**7. Win-rate 14.3%** (13 W / 78 L = 91 trade · -9.9pp vs baseline)
   - `dow = Fri`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `rsi_M30 = [30,50)`

**8. Win-rate 15.7%** (46 W / 247 L = 293 trade · -8.5pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 ≠ [35,+∞)`
   - `M30_ema_stack ≠ NA`
   - `dow = Wed`

**9. Win-rate 17.1%** (37 W / 180 L = 217 trade · -7.1pp vs baseline)
   - `dow ≠ Fri`
   - `adx_M30 = [35,+∞)`
   - `rsi_M30 ≠ [65,75)`
   - `rsi_M30 = [50,65)`

**10. Win-rate 30.0%** (21 W / 49 L = 70 trade · 5.8pp vs baseline)
   - `dow = Fri`
   - `vix_chg1d = [3,+∞)`
   - `macd_atr_M30 ≠ [−∞,-0.3)`
   - `session ≠ europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0410 |
| 2 | `dow=Wed` | 0.0397 |
| 3 | `dow=Fri` | 0.0379 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0269 |
| 5 | `mtf_trend=NA` | 0.0240 |
| 6 | `M30_ema_stack=NA` | 0.0231 |
| 7 | `adx_M30=[35,+∞)` | 0.0224 |
| 8 | `adx_H1=[35,+∞)` | 0.0201 |
| 9 | `rsi_M30=[65,75)` | 0.0197 |
| 10 | `H1_adx_label=weak_trend` | 0.0187 |
| 11 | `adx_H1=[18,25)` | 0.0187 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0185 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0181 |
| 14 | `dxy_chg1d=[0.5,+∞)` | 0.0169 |
| 15 | `M30_ema_stack=mixed` | 0.0157 |

---

## XAUUSD · pulse2_inv
- Toplam çözülmüş: **806**  ·  Baseline win-rate: **44.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (29 W / 1 L = 30 trade · +52.4pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 ≠ [25,35)`
   - `adx_M30 = [35,+∞)`
   - `dow = Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.8%** (7 W / 58 L = 65 trade · -33.5pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `dxy_chg1d = [0,0.5)`

**2. Win-rate 17.9%** (5 W / 23 L = 28 trade · -26.4pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_H1 ≠ [35,+∞)`

**3. Win-rate 27.9%** (12 W / 31 L = 43 trade · -16.4pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ weak_pro`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment = strong_against`

**4. Win-rate 28.6%** (8 W / 20 L = 28 trade · -15.7pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 = [25,35)`

**5. Win-rate 31.2%** (60 W / 132 L = 192 trade · -13.1pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ weak_pro`
   - `adx_M30 ≠ [35,+∞)`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -12.5pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `macro_alignment = weak_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `dxy_chg1d ≠ [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0679 |
| 2 | `macro_alignment=weak_pro` | 0.0566 |
| 3 | `adx_M30=[35,+∞)` | 0.0516 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0498 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0400 |
| 6 | `adx_H1=[35,+∞)` | 0.0252 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0228 |
| 8 | `mtf_trend=NA` | 0.0212 |
| 9 | `macro_alignment=strong_against` | 0.0204 |
| 10 | `M30_ema_stack=NA` | 0.0175 |
| 11 | `adx_H1=[−∞,18)` | 0.0172 |
| 12 | `M30_adx_label=trending` | 0.0161 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0158 |
| 14 | `adx_M30=[18,25)` | 0.0152 |
| 15 | `adx_M30=[25,35)` | 0.0142 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **2864**  ·  Baseline win-rate: **25.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.3%** (148 W / 41 L = 189 trade · +52.8pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `mtf_trend ≠ NA`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 1.8%** (1 W / 55 L = 56 trade · -23.7pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label = weak_trend`
   - `oversold = True`

**2. Win-rate 3.0%** (5 W / 160 L = 165 trade · -22.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`

**3. Win-rate 4.1%** (15 W / 352 L = 367 trade · -21.4pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `adx_H1 ≠ [25,35)`

**4. Win-rate 5.6%** (7 W / 117 L = 124 trade · -19.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `mtf_trend = NA`
   - `sar_bearish ≠ False`

**5. Win-rate 5.8%** (19 W / 310 L = 329 trade · -19.7pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H1_adx_label = trending`
   - `dxy_chg1d ≠ [-0.5,0)`

**6. Win-rate 14.3%** (12 W / 72 L = 84 trade · -11.2pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label ≠ weak_trend`
   - `adx_H1 = [25,35)`

**7. Win-rate 15.2%** (24 W / 134 L = 158 trade · -10.3pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `M30_ema_stack ≠ up`

**8. Win-rate 23.0%** (17 W / 57 L = 74 trade · -2.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow = Mon`

**9. Win-rate 24.0%** (42 W / 133 L = 175 trade · -1.5pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H1_adx_label ≠ trending`
   - `bb_pctb_M30 = [0.2,0.5)`

**10. Win-rate 28.6%** (22 W / 55 L = 77 trade · 3.1pp vs baseline)
   - `M30_ema_stack = down`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `H1_adx_label = weak_trend`
   - `oversold ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0468 |
| 2 | `M30_ema_stack=up` | 0.0359 |
| 3 | `M30_ema_stack=down` | 0.0323 |
| 4 | `mtf_trend=all_down` | 0.0313 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0281 |
| 6 | `mtf_trend=all_up` | 0.0268 |
| 7 | `dow=Wed` | 0.0243 |
| 8 | `dist_low_M30=[1.5,+∞)` | 0.0240 |
| 9 | `dow=Fri` | 0.0230 |
| 10 | `rsi_H1=[50,65)` | 0.0217 |
| 11 | `rsi_M30=[30,50)` | 0.0201 |
| 12 | `oversold=False` | 0.0189 |
| 13 | `adx_H1=[35,+∞)` | 0.0187 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0171 |
| 15 | `rsi_M30=[65,75)` | 0.0166 |

---

## XAUUSD · pulse3_inv
- Toplam çözülmüş: **760**  ·  Baseline win-rate: **41.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.7%** (115 W / 37 L = 152 trade · +34.4pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dxy_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.0%** (10 W / 101 L = 111 trade · -32.3pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = False`
   - `volatility_regime = normal`
   - `H1_adx_label ≠ weak_trend`

**2. Win-rate 24.2%** (8 W / 25 L = 33 trade · -17.1pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = False`
   - `volatility_regime = normal`
   - `H1_adx_label = weak_trend`

**3. Win-rate 30.5%** (58 W / 132 L = 190 trade · -10.8pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `near_support = False`
   - `M30_adx_label ≠ ranging`

**4. Win-rate 30.6%** (11 W / 25 L = 36 trade · -10.7pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `near_support ≠ False`
   - `dxy_chg1d ≠ [0,0.5)`

**5. Win-rate 33.3%** (10 W / 20 L = 30 trade · -8.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0811 |
| 2 | `sar_bearish=True` | 0.0607 |
| 3 | `macro_alignment=weak_pro` | 0.0436 |
| 4 | `macro_alignment=weak_against` | 0.0338 |
| 5 | `adx_M30=[35,+∞)` | 0.0337 |
| 6 | `adx_H1=[35,+∞)` | 0.0333 |
| 7 | `rsi_H1=[30,50)` | 0.0264 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0246 |
| 9 | `rsi_H1=[50,65)` | 0.0240 |
| 10 | `adx_M30=[25,35)` | 0.0238 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0218 |
| 12 | `rsi_M30=[50,65)` | 0.0194 |
| 13 | `adx_H1=[25,35)` | 0.0178 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0176 |
| 15 | `rsi_M30=[30,50)` | 0.0168 |

---

## XAUUSD · smc
- Toplam çözülmüş: **595**  ·  Baseline win-rate: **47.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.4%** (85 W / 9 L = 94 trade · +43.2pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack ≠ up`
   - `session ≠ asia`
   - `vix_chg1d ≠ [0,3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -37.2pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d = [0,0.5)`
   - `macro_alignment = weak_pro`

**2. Win-rate 18.8%** (34 W / 147 L = 181 trade · -28.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `consec_green_M30 ≠ [2,4)`

**3. Win-rate 27.6%** (8 W / 21 L = 29 trade · -19.6pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack = up`

**4. Win-rate 30.0%** (6 W / 14 L = 20 trade · -17.2pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d = [0,0.5)`
   - `macro_alignment ≠ weak_pro`
   - `H1_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0852 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0425 |
| 3 | `us10y_chg1d=[−∞,-0.5)` | 0.0366 |
| 4 | `vix_chg1d=[-3,0)` | 0.0333 |
| 5 | `bb_pctb_M30=[0.2,0.5)` | 0.0310 |
| 6 | `H1_adx_label=trending` | 0.0291 |
| 7 | `adx_M30=[35,+∞)` | 0.0261 |
| 8 | `dist_high_M30=[1.5,+∞)` | 0.0258 |
| 9 | `M30_ema_stack=down` | 0.0216 |
| 10 | `mtf_trend=all_down` | 0.0209 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0207 |
| 12 | `H1_adx_label=weak_trend` | 0.0199 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0197 |
| 14 | `macro_alignment=strong_pro` | 0.0190 |
| 15 | `atr_ratio_M30=[1,1.3)` | 0.0172 |

---

## XAUUSD · smc_inv
- Toplam çözülmüş: **194**  ·  Baseline win-rate: **48.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.4%** (35 W / 8 L = 43 trade · +32.9pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -38.5pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 26.7%** (8 W / 22 L = 30 trade · -21.8pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d = [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_high_M30=[1.5,+∞)` | 0.1023 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0586 |
| 3 | `macro_alignment=weak_against` | 0.0581 |
| 4 | `dow=Tue` | 0.0483 |
| 5 | `us10y_chg1d=[0,0.5)` | 0.0299 |
| 6 | `mtf_trend=mixed` | 0.0278 |
| 7 | `vix_chg1d=[0,3)` | 0.0274 |
| 8 | `dist_high_M30=[0.7,1.5)` | 0.0226 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0220 |
| 10 | `atr_ratio_M30=[0.7,1)` | 0.0207 |
| 11 | `M30_ema_stack=mixed` | 0.0202 |
| 12 | `H1_adx_label=trending` | 0.0200 |
| 13 | `dow=Wed` | 0.0196 |
| 14 | `session=asia` | 0.0187 |
| 15 | `adx_M30=[35,+∞)` | 0.0177 |

---

## GDAXI.INDX · ai_panel · BUY
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **55.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.0%** (32 W / 8 L = 40 trade · +24.9pp vs baseline)
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.1%** (7 W / 22 L = 29 trade · -31.0pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `rsi_H4 ≠ [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.1576 |
| 2 | `rsi_H1=[50,65)` | 0.0892 |
| 3 | `sar_bearish=False` | 0.0634 |
| 4 | `sar_bearish=True` | 0.0508 |
| 5 | `H4_ema_stack=up` | 0.0444 |
| 6 | `H1_ema_stack=mixed` | 0.0324 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0299 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0279 |
| 9 | `us10y_chg1d=[−∞,-0.5)` | 0.0269 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0249 |
| 11 | `us10y_chg1d=[-0.5,0)` | 0.0242 |
| 12 | `regime_label=transition` | 0.0237 |
| 13 | `macro_alignment=strong_against` | 0.0233 |
| 14 | `volatility_regime=normal` | 0.0229 |
| 15 | `volatility_regime=high` | 0.0222 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **290**  ·  Baseline win-rate: **44.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.7%** (22 W / 1 L = 23 trade · +51.2pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 = [30,50)`
   - `vix_chg1d = [0,3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.1%** (11 W / 67 L = 78 trade · -30.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `regime_label ≠ ranging`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H1_adx_label ≠ weak_trend`

**2. Win-rate 29.5%** (13 W / 31 L = 44 trade · -15.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `regime_label ≠ ranging`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `H1_adx_label = weak_trend`

**3. Win-rate 30.4%** (7 W / 16 L = 23 trade · -14.1pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 ≠ [30,50)`
   - `H1_ema_stack = up`
   - `ml_confidence_bucket = [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1035 |
| 2 | `sar_bearish=True` | 0.0815 |
| 3 | `rsi_H1=[30,50)` | 0.0804 |
| 4 | `rsi_H1=[50,65)` | 0.0305 |
| 5 | `adx_H1=[18,25)` | 0.0264 |
| 6 | `volatility_regime=normal` | 0.0229 |
| 7 | `adx_H4=[18,25)` | 0.0227 |
| 8 | `H4_adx_label=weak_trend` | 0.0221 |
| 9 | `adx_H4=[−∞,18)` | 0.0197 |
| 10 | `bb_extreme_upper=True` | 0.0189 |
| 11 | `dow=Mon` | 0.0181 |
| 12 | `us10y_chg1d=[-0.5,0)` | 0.0180 |
| 13 | `H4_adx_label=ranging` | 0.0179 |
| 14 | `adx_H1=[−∞,18)` | 0.0175 |
| 15 | `bb_extreme_lower=False` | 0.0172 |

---

## GDAXI.INDX · meta · SELL
- Toplam çözülmüş: **123**  ·  Baseline win-rate: **52.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.9%** (26 W / 5 L = 31 trade · +31.1pp vs baseline)
   - `H1_adx_label = trending`
   - `regime_label = ranging`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.4%** (6 W / 22 L = 28 trade · -31.4pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `rsi_H4 ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0729 |
| 2 | `H1_adx_label=weak_trend` | 0.0681 |
| 3 | `adx_H1=[18,25)` | 0.0674 |
| 4 | `adx_H1=[25,35)` | 0.0369 |
| 5 | `dow=Mon` | 0.0367 |
| 6 | `H4_ema_stack=mixed` | 0.0353 |
| 7 | `H1_ema_stack=down` | 0.0334 |
| 8 | `dow=Wed` | 0.0315 |
| 9 | `dow=Fri` | 0.0302 |
| 10 | `sar_bearish=True` | 0.0272 |
| 11 | `H1_ema_stack=mixed` | 0.0266 |
| 12 | `sar_bearish=False` | 0.0244 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0243 |
| 14 | `regime_label=ranging` | 0.0242 |
| 15 | `H4_ema_stack=NA` | 0.0232 |

---

## GDAXI.INDX · ml:balanced · BUY
- Toplam çözülmüş: **166**  ·  Baseline win-rate: **63.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +36.7pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H4_ema_stack = up`
   - `hour_bucket = 08-12`

**2. Win-rate 89.3%** (25 W / 3 L = 28 trade · +26.0pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H4_ema_stack = up`
   - `hour_bucket ≠ 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.2%** (8 W / 25 L = 33 trade · -39.1pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `sar_bearish ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1028 |
| 2 | `rsi_H1=[30,50)` | 0.0982 |
| 3 | `rsi_H1=[50,65)` | 0.0831 |
| 4 | `sar_bearish=True` | 0.0772 |
| 5 | `H4_ema_stack=up` | 0.0485 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0387 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0321 |
| 8 | `vix_chg1d=[0,3)` | 0.0271 |
| 9 | `volatility_regime=high` | 0.0269 |
| 10 | `adx_H1=[−∞,18)` | 0.0264 |
| 11 | `macro_alignment=neutral` | 0.0238 |
| 12 | `H1_ema_stack=down` | 0.0231 |
| 13 | `volatility_regime=normal` | 0.0183 |
| 14 | `adx_H1=[25,35)` | 0.0178 |
| 15 | `H1_adx_label=ranging` | 0.0157 |

---

## GDAXI.INDX · ml:full_power · BUY
- Toplam çözülmüş: **179**  ·  Baseline win-rate: **57.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +43.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +38.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.8%** (6 W / 26 L = 32 trade · -38.2pp vs baseline)
   - `sar_bearish = False`
   - `adx_H4 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.1161 |
| 2 | `sar_bearish=False` | 0.1054 |
| 3 | `rsi_H1=[50,65)` | 0.0930 |
| 4 | `sar_bearish=True` | 0.0908 |
| 5 | `H4_ema_stack=up` | 0.0323 |
| 6 | `bb_extreme_lower=True` | 0.0302 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0300 |
| 8 | `vix_chg1d=[0,3)` | 0.0250 |
| 9 | `adx_H1=[25,35)` | 0.0244 |
| 10 | `adx_H4=[18,25)` | 0.0213 |
| 11 | `H4_adx_label=weak_trend` | 0.0213 |
| 12 | `bb_extreme_lower=False` | 0.0200 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0191 |
| 14 | `session=europe` | 0.0174 |
| 15 | `volatility_regime=high` | 0.0164 |

---

## GDAXI.INDX · ml:main · BUY
- Toplam çözülmüş: **180**  ·  Baseline win-rate: **56.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +43.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime = normal`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +38.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `volatility_regime ≠ normal`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.8%** (6 W / 26 L = 32 trade · -37.9pp vs baseline)
   - `sar_bearish = False`
   - `adx_H4 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1095 |
| 2 | `rsi_H1=[30,50)` | 0.1044 |
| 3 | `sar_bearish=True` | 0.0906 |
| 4 | `rsi_H1=[50,65)` | 0.0821 |
| 5 | `H4_ema_stack=up` | 0.0540 |
| 6 | `vix_chg1d=[0,3)` | 0.0416 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0407 |
| 8 | `H1_adx_label=trending` | 0.0226 |
| 9 | `rsi_H4=[50,65)` | 0.0162 |
| 10 | `H4_adx_label=weak_trend` | 0.0161 |
| 11 | `volatility_regime=high` | 0.0159 |
| 12 | `adx_H4=[18,25)` | 0.0157 |
| 13 | `H1_ema_stack=down` | 0.0150 |
| 14 | `bb_extreme_upper=False` | 0.0147 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0146 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **694**  ·  Baseline win-rate: **29.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.2%** (41 W / 3 L = 44 trade · +63.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `vix_chg1d = [0,3)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 130 L = 130 trade · -29.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `adx_H4 ≠ [−∞,18)`

**2. Win-rate 2.2%** (1 W / 44 L = 45 trade · -27.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 6.7%** (2 W / 28 L = 30 trade · -22.7pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `adx_H4 = [−∞,18)`

**4. Win-rate 17.4%** (30 W / 142 L = 172 trade · -12.0pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket ≠ 04-08`
   - `rsi_H1 ≠ [30,50)`

**5. Win-rate 26.9%** (7 W / 19 L = 26 trade · -2.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish ≠ True`

**6. Win-rate 30.0%** (12 W / 28 L = 40 trade · 0.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1095 |
| 2 | `adx_H4=[−∞,18)` | 0.0448 |
| 3 | `regime_label=ranging` | 0.0412 |
| 4 | `bb_extreme_upper=False` | 0.0396 |
| 5 | `bb_extreme_upper=True` | 0.0369 |
| 6 | `sar_bearish=True` | 0.0368 |
| 7 | `vix_chg1d=[0,3)` | 0.0317 |
| 8 | `sar_bearish=False` | 0.0305 |
| 9 | `H4_adx_label=ranging` | 0.0286 |
| 10 | `mtf_trend=all_up` | 0.0265 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0262 |
| 12 | `H4_adx_label=weak_trend` | 0.0244 |
| 13 | `vix_chg1d=[-3,0)` | 0.0229 |
| 14 | `adx_H4=[18,25)` | 0.0215 |
| 15 | `rsi_H1=[30,50)` | 0.0196 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **345**  ·  Baseline win-rate: **24.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 101 L = 101 trade · -24.1pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `sar_bearish = True`
   - `H4_adx_label ≠ NA`
   - `session_phase = after_hours`

**2. Win-rate 3.6%** (1 W / 27 L = 28 trade · -20.5pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `sar_bearish = True`
   - `H4_adx_label ≠ NA`
   - `session_phase ≠ after_hours`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -19.6pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `rsi_H4 ≠ [30,50)`
   - `hour_bucket ≠ 08-12`
   - `dow ≠ Fri`

**4. Win-rate 18.2%** (4 W / 18 L = 22 trade · -5.9pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `sar_bearish ≠ True`
   - `session ≠ europe`

**5. Win-rate 22.6%** (7 W / 24 L = 31 trade · -1.5pp vs baseline)
   - `rsi_H1 ≠ [50,65)`
   - `sar_bearish = True`
   - `H4_adx_label = NA`
   - `oversold = False`

**6. Win-rate 30.8%** (8 W / 18 L = 26 trade · 6.7pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `rsi_H4 ≠ [30,50)`
   - `hour_bucket = 08-12`
   - `ml_confidence_bucket ≠ [−∞,50)`

**7. Win-rate 35.0%** (7 W / 13 L = 20 trade · 10.9pp vs baseline)
   - `rsi_H1 = [50,65)`
   - `rsi_H4 ≠ [30,50)`
   - `hour_bucket ≠ 08-12`
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[50,65)` | 0.0756 |
| 2 | `rsi_H1=[30,50)` | 0.0573 |
| 3 | `adx_H4=[25,35)` | 0.0409 |
| 4 | `H4_adx_label=trending` | 0.0373 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0341 |
| 6 | `volatility_regime=normal` | 0.0321 |
| 7 | `bb_extreme_lower=True` | 0.0314 |
| 8 | `volatility_regime=high` | 0.0304 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0303 |
| 10 | `sar_bearish=False` | 0.0292 |
| 11 | `sar_bearish=True` | 0.0277 |
| 12 | `hour_bucket=12-16` | 0.0275 |
| 13 | `hour_bucket=08-12` | 0.0266 |
| 14 | `session=europe` | 0.0260 |
| 15 | `bb_extreme_lower=False` | 0.0216 |

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
- Toplam çözülmüş: **432**  ·  Baseline win-rate: **44.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.8%** (44 W / 1 L = 45 trade · +53.6pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 ≠ [50,65)`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +41.5pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 = [50,65)`

**3. Win-rate 82.2%** (37 W / 8 L = 45 trade · +38.0pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -44.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper ≠ False`
   - `us10y_chg1d = [−∞,-0.5)`

**2. Win-rate 4.0%** (1 W / 24 L = 25 trade · -40.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = False`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 9.1%** (2 W / 20 L = 22 trade · -35.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**4. Win-rate 19.4%** (6 W / 25 L = 31 trade · -24.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend = mixed`
   - `H1_adx_label = trending`

**5. Win-rate 22.9%** (8 W / 27 L = 35 trade · -21.3pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d = [3,+∞)`

**6. Win-rate 26.7%** (8 W / 22 L = 30 trade · -17.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend = mixed`
   - `H1_adx_label ≠ trending`
   - `adx_H4 = [18,25)`

**7. Win-rate 30.4%** (14 W / 32 L = 46 trade · -13.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend ≠ mixed`
   - `bb_extreme_upper = False`
   - `dxy_chg1d ≠ [0,0.5)`

**8. Win-rate 32.5%** (13 W / 27 L = 40 trade · -11.7pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0972 |
| 2 | `sar_bearish=True` | 0.0705 |
| 3 | `rsi_H1=[30,50)` | 0.0470 |
| 4 | `adx_H4=[−∞,18)` | 0.0362 |
| 5 | `bb_extreme_upper=False` | 0.0348 |
| 6 | `H4_adx_label=ranging` | 0.0333 |
| 7 | `regime_label=ranging` | 0.0322 |
| 8 | `dow=Mon` | 0.0237 |
| 9 | `mtf_trend=all_up` | 0.0231 |
| 10 | `bb_extreme_upper=True` | 0.0226 |
| 11 | `mtf_trend=mixed` | 0.0226 |
| 12 | `bb_extreme_lower=True` | 0.0215 |
| 13 | `vix_chg1d=[0,3)` | 0.0215 |
| 14 | `macro_alignment=strong_against` | 0.0199 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0196 |

---

## GDAXI.INDX · pulse2 · SELL
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **38.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.9%** (7 W / 30 L = 37 trade · -20.0pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `dow ≠ Wed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0750 |
| 2 | `dow=Wed` | 0.0650 |
| 3 | `mtf_trend=mixed` | 0.0602 |
| 4 | `ml_confidence_bucket=[−∞,50)` | 0.0456 |
| 5 | `macro_alignment=neutral` | 0.0434 |
| 6 | `H4_adx_label=NA` | 0.0408 |
| 7 | `H4_ema_stack=NA` | 0.0361 |
| 8 | `H4_adx_label=trending` | 0.0349 |
| 9 | `adx_H1=[18,25)` | 0.0313 |
| 10 | `adx_H4=NA` | 0.0312 |
| 11 | `adx_H4=[25,35)` | 0.0280 |
| 12 | `H1_adx_label=weak_trend` | 0.0250 |
| 13 | `H1_adx_label=ranging` | 0.0249 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0246 |
| 15 | `rsi_H4=NA` | 0.0245 |

---

## GDAXI.INDX · pulse2_inv · SELL
- Toplam çözülmüş: **86**  ·  Baseline win-rate: **47.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (6 W / 18 L = 24 trade · -22.7pp vs baseline)
   - `macro_alignment ≠ strong_pro`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0812 |
| 2 | `H4_ema_stack=up` | 0.0702 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0693 |
| 4 | `H4_ema_stack=NA` | 0.0688 |
| 5 | `adx_H4=NA` | 0.0602 |
| 6 | `H4_adx_label=NA` | 0.0533 |
| 7 | `macro_alignment=strong_pro` | 0.0418 |
| 8 | `rsi_H4=NA` | 0.0389 |
| 9 | `H1_ema_stack=up` | 0.0387 |
| 10 | `mtf_trend=all_up` | 0.0370 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0296 |
| 12 | `mtf_trend=mixed` | 0.0287 |
| 13 | `volatility_regime=normal` | 0.0255 |
| 14 | `adx_H1=[35,+∞)` | 0.0252 |
| 15 | `hour_bucket=08-12` | 0.0250 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **654**  ·  Baseline win-rate: **38.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +61.5pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H1_ema_stack = up`
   - `volatility_regime ≠ high`
   - `bb_extreme_lower = True`

**2. Win-rate 100.0%** (36 W / 0 L = 36 trade · +61.5pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H1_ema_stack = up`
   - `volatility_regime = high`

**3. Win-rate 85.0%** (34 W / 6 L = 40 trade · +46.5pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `session = asia`
   - `H1_adx_label = trending`

**4. Win-rate 84.4%** (27 W / 5 L = 32 trade · +45.9pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H1_ema_stack = up`
   - `volatility_regime ≠ high`
   - `bb_extreme_lower ≠ True`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -38.5pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `session = asia`
   - `H1_adx_label ≠ trending`
   - `mtf_trend ≠ mixed`

**2. Win-rate 18.2%** (66 W / 296 L = 362 trade · -20.3pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `session ≠ asia`
   - `H4_adx_label ≠ ranging`
   - `rsi_H4 ≠ [75,+∞)`

**3. Win-rate 22.6%** (7 W / 24 L = 31 trade · -15.9pp vs baseline)
   - `rsi_H1 = [30,50)`
   - `H1_ema_stack ≠ up`

**4. Win-rate 29.2%** (7 W / 17 L = 24 trade · -9.3pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `session ≠ asia`
   - `H4_adx_label = ranging`
   - `rsi_H4 ≠ [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0715 |
| 2 | `sar_bearish=False` | 0.0660 |
| 3 | `sar_bearish=True` | 0.0464 |
| 4 | `rsi_H1=[50,65)` | 0.0310 |
| 5 | `volatility_regime=normal` | 0.0268 |
| 6 | `vix_chg1d=[0,3)` | 0.0244 |
| 7 | `bb_extreme_lower=True` | 0.0219 |
| 8 | `vix_chg1d=[-3,0)` | 0.0213 |
| 9 | `session=asia` | 0.0196 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0187 |
| 11 | `session=europe` | 0.0180 |
| 12 | `bb_extreme_upper=True` | 0.0176 |
| 13 | `overbought=True` | 0.0170 |
| 14 | `bb_extreme_lower=False` | 0.0167 |
| 15 | `H1_adx_label=trending` | 0.0163 |

---

## GDAXI.INDX · pulse3 · SELL
- Toplam çözülmüş: **284**  ·  Baseline win-rate: **38.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.2%** (25 W / 1 L = 26 trade · +58.2pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `sar_bearish ≠ True`

**2. Win-rate 90.0%** (18 W / 2 L = 20 trade · +52.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 = [50,65)`
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -38.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `regime_label ≠ transition`
   - `bb_extreme_lower = True`

**2. Win-rate 12.2%** (6 W / 43 L = 49 trade · -25.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `regime_label = transition`
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 12.9%** (4 W / 27 L = 31 trade · -25.1pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `regime_label ≠ transition`
   - `bb_extreme_lower ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0723 |
| 2 | `sar_bearish=False` | 0.0612 |
| 3 | `H1_adx_label=trending` | 0.0546 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0502 |
| 5 | `dow=Mon` | 0.0481 |
| 6 | `H4_ema_stack=mixed` | 0.0467 |
| 7 | `sar_bearish=True` | 0.0425 |
| 8 | `rsi_H1=[50,65)` | 0.0286 |
| 9 | `H1_ema_stack=down` | 0.0251 |
| 10 | `H1_adx_label=weak_trend` | 0.0209 |
| 11 | `bb_extreme_lower=True` | 0.0202 |
| 12 | `rsi_H4=NA` | 0.0200 |
| 13 | `dow=Fri` | 0.0187 |
| 14 | `H4_adx_label=ranging` | 0.0179 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0177 |

---

## GDAXI.INDX · pulse3_inv · BUY
- Toplam çözülmüş: **86**  ·  Baseline win-rate: **43.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.8%** (8 W / 23 L = 31 trade · -17.2pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `H1_adx_label ≠ weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.1173 |
| 2 | `H1_ema_stack=down` | 0.0556 |
| 3 | `H1_adx_label=weak_trend` | 0.0531 |
| 4 | `adx_H1=[18,25)` | 0.0397 |
| 5 | `sar_bearish=False` | 0.0397 |
| 6 | `adx_H4=NA` | 0.0389 |
| 7 | `hour_bucket=12-16` | 0.0371 |
| 8 | `session=europe` | 0.0361 |
| 9 | `sar_bearish=True` | 0.0338 |
| 10 | `macro_alignment=strong_against` | 0.0333 |
| 11 | `H1_ema_stack=mixed` | 0.0315 |
| 12 | `H1_adx_label=ranging` | 0.0291 |
| 13 | `H1_adx_label=trending` | 0.0291 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0239 |
| 15 | `H4_ema_stack=NA` | 0.0226 |

---

## GDAXI.INDX · pulse3_inv · SELL
- Toplam çözülmüş: **101**  ·  Baseline win-rate: **45.5%**

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
| 1 | `rsi_H4=NA` | 0.0752 |
| 2 | `adx_H4=NA` | 0.0729 |
| 3 | `H4_ema_stack=NA` | 0.0670 |
| 4 | `H4_adx_label=trending` | 0.0612 |
| 5 | `H4_adx_label=NA` | 0.0590 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0470 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0410 |
| 8 | `H4_ema_stack=up` | 0.0399 |
| 9 | `H1_adx_label=trending` | 0.0385 |
| 10 | `H1_ema_stack=down` | 0.0334 |
| 11 | `macro_alignment=strong_pro` | 0.0311 |
| 12 | `dow=Mon` | 0.0225 |
| 13 | `rsi_H4=[75,+∞)` | 0.0206 |
| 14 | `sar_bearish=True` | 0.0190 |
| 15 | `mtf_trend=mixed` | 0.0173 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **173**  ·  Baseline win-rate: **43.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +47.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `dxy_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -43.9pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `volatility_regime ≠ normal`

**2. Win-rate 17.9%** (5 W / 23 L = 28 trade · -26.0pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `volatility_regime = normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1314 |
| 2 | `sar_bearish=True` | 0.1140 |
| 3 | `rsi_H1=[30,50)` | 0.0652 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0451 |
| 5 | `H4_ema_stack=NA` | 0.0293 |
| 6 | `rsi_H1=[65,75)` | 0.0288 |
| 7 | `adx_H1=[18,25)` | 0.0275 |
| 8 | `H1_adx_label=weak_trend` | 0.0271 |
| 9 | `rsi_H4=[30,50)` | 0.0262 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0262 |
| 11 | `bb_extreme_upper=True` | 0.0244 |
| 12 | `bb_extreme_upper=False` | 0.0239 |
| 13 | `mtf_trend=mixed` | 0.0198 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0162 |
| 15 | `rsi_H1=[50,65)` | 0.0162 |

---

## NDX.INDX · meta · SELL
- Toplam çözülmüş: **99**  ·  Baseline win-rate: **59.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.7%** (26 W / 3 L = 29 trade · +30.1pp vs baseline)
   - `H1_ema_stack = mixed`
   - `dxy_chg1d ≠ [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.9%** (7 W / 19 L = 26 trade · -32.7pp vs baseline)
   - `H1_ema_stack ≠ mixed`
   - `H4_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=mixed` | 0.1286 |
| 2 | `dow=Fri` | 0.0483 |
| 3 | `dow=Thu` | 0.0444 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0397 |
| 5 | `H1_ema_stack=down` | 0.0379 |
| 6 | `H4_ema_stack=up` | 0.0377 |
| 7 | `adx_H4=[25,35)` | 0.0372 |
| 8 | `macro_alignment=strong_against` | 0.0368 |
| 9 | `sar_bearish=True` | 0.0358 |
| 10 | `sar_bearish=False` | 0.0325 |
| 11 | `rsi_H4=[30,50)` | 0.0285 |
| 12 | `H1_adx_label=trending` | 0.0268 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0265 |
| 14 | `adx_H1=[25,35)` | 0.0255 |
| 15 | `dow=Wed` | 0.0248 |

---

## NDX.INDX · ml:balanced · BUY
- Toplam çözülmüş: **145**  ·  Baseline win-rate: **50.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.4%** (28 W / 6 L = 34 trade · +32.1pp vs baseline)
   - `sar_bearish = True`
   - `adx_H1 = [−∞,18)`

**2. Win-rate 81.0%** (17 W / 4 L = 21 trade · +30.7pp vs baseline)
   - `sar_bearish = True`
   - `adx_H1 ≠ [−∞,18)`
   - `vix_chg1d = [-3,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (6 W / 24 L = 30 trade · -30.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `H4_adx_label = trending`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -17.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `H4_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0997 |
| 2 | `sar_bearish=False` | 0.0918 |
| 3 | `H4_ema_stack=up` | 0.0563 |
| 4 | `rsi_H1=[30,50)` | 0.0396 |
| 5 | `vix_chg1d=[-3,0)` | 0.0368 |
| 6 | `us10y_chg1d=[-0.5,0)` | 0.0348 |
| 7 | `volatility_regime=normal` | 0.0324 |
| 8 | `H4_ema_stack=mixed` | 0.0268 |
| 9 | `mtf_trend=mixed` | 0.0257 |
| 10 | `session_phase=mid_session` | 0.0220 |
| 11 | `adx_H4=[35,+∞)` | 0.0216 |
| 12 | `adx_H1=[−∞,18)` | 0.0208 |
| 13 | `H1_adx_label=ranging` | 0.0208 |
| 14 | `volatility_regime=high` | 0.0204 |
| 15 | `rsi_H1=[50,65)` | 0.0200 |

---

## NDX.INDX · ml:balanced · SELL
- Toplam çözülmüş: **110**  ·  Baseline win-rate: **60.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +17.3pp vs baseline)
   - `dow = Thu`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (7 W / 14 L = 21 trade · -26.7pp vs baseline)
   - `dow ≠ Thu`
   - `session_phase = mid_session`
   - `dxy_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0664 |
| 2 | `hour_bucket=16-20` | 0.0437 |
| 3 | `vix_chg1d=[0,3)` | 0.0423 |
| 4 | `H4_ema_stack=mixed` | 0.0401 |
| 5 | `session_phase=mid_session` | 0.0381 |
| 6 | `H1_adx_label=weak_trend` | 0.0361 |
| 7 | `sar_bearish=True` | 0.0319 |
| 8 | `H4_ema_stack=up` | 0.0318 |
| 9 | `rsi_H1=[30,50)` | 0.0300 |
| 10 | `sar_bearish=False` | 0.0293 |
| 11 | `adx_H1=[25,35)` | 0.0268 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0266 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0256 |
| 14 | `H4_adx_label=ranging` | 0.0250 |
| 15 | `H1_adx_label=trending` | 0.0245 |

---

## NDX.INDX · ml:full_power · BUY
- Toplam çözülmüş: **141**  ·  Baseline win-rate: **51.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (18 W / 2 L = 20 trade · +38.9pp vs baseline)
   - `sar_bearish = True`
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (7 W / 21 L = 28 trade · -26.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0868 |
| 2 | `sar_bearish=True` | 0.0718 |
| 3 | `H4_ema_stack=up` | 0.0467 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0449 |
| 5 | `dow=Mon` | 0.0442 |
| 6 | `macro_alignment=weak_pro` | 0.0430 |
| 7 | `volatility_regime=normal` | 0.0337 |
| 8 | `volatility_regime=high` | 0.0307 |
| 9 | `adx_H1=[−∞,18)` | 0.0297 |
| 10 | `H4_adx_label=ranging` | 0.0280 |
| 11 | `adx_H4=[35,+∞)` | 0.0279 |
| 12 | `rsi_H1=[30,50)` | 0.0270 |
| 13 | `macro_alignment=neutral` | 0.0250 |
| 14 | `H4_adx_label=trending` | 0.0223 |
| 15 | `rsi_H1=[50,65)` | 0.0221 |

---

## NDX.INDX · ml:full_power · SELL
- Toplam çözülmüş: **119**  ·  Baseline win-rate: **61.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +24.4pp vs baseline)
   - `dow = Thu`
   - `volatility_regime = high`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (7 W / 14 L = 21 trade · -28.0pp vs baseline)
   - `dow ≠ Thu`
   - `session_phase = mid_session`
   - `H1_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0504 |
| 2 | `rsi_H1=[30,50)` | 0.0394 |
| 3 | `adx_H1=[25,35)` | 0.0387 |
| 4 | `hour_bucket=12-16` | 0.0382 |
| 5 | `vix_chg1d=[0,3)` | 0.0369 |
| 6 | `dow=Tue` | 0.0354 |
| 7 | `H4_ema_stack=mixed` | 0.0348 |
| 8 | `hour_bucket=16-20` | 0.0333 |
| 9 | `H1_adx_label=trending` | 0.0328 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0316 |
| 11 | `adx_H1=[18,25)` | 0.0307 |
| 12 | `H1_adx_label=weak_trend` | 0.0290 |
| 13 | `H1_ema_stack=up` | 0.0287 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0282 |
| 15 | `H1_ema_stack=down` | 0.0276 |

---

## NDX.INDX · ml:main · BUY
- Toplam çözülmüş: **142**  ·  Baseline win-rate: **50.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (18 W / 2 L = 20 trade · +39.3pp vs baseline)
   - `sar_bearish = True`
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (7 W / 21 L = 28 trade · -25.7pp vs baseline)
   - `sar_bearish ≠ True`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0985 |
| 2 | `sar_bearish=False` | 0.0713 |
| 3 | `dow=Mon` | 0.0522 |
| 4 | `H4_ema_stack=up` | 0.0486 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0384 |
| 6 | `volatility_regime=normal` | 0.0371 |
| 7 | `macro_alignment=weak_pro` | 0.0360 |
| 8 | `us10y_chg1d=[-0.5,0)` | 0.0352 |
| 9 | `adx_H1=[−∞,18)` | 0.0336 |
| 10 | `H1_adx_label=ranging` | 0.0284 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0276 |
| 12 | `rsi_H1=[50,65)` | 0.0259 |
| 13 | `rsi_H1=[30,50)` | 0.0206 |
| 14 | `macro_alignment=neutral` | 0.0203 |
| 15 | `rsi_H4=[50,65)` | 0.0198 |

---

## NDX.INDX · ml:main · SELL
- Toplam çözülmüş: **119**  ·  Baseline win-rate: **63.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +22.7pp vs baseline)
   - `dow = Thu`
   - `volatility_regime = high`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[0,3)` | 0.0563 |
| 2 | `dow=Thu` | 0.0520 |
| 3 | `hour_bucket=16-20` | 0.0459 |
| 4 | `session_phase=mid_session` | 0.0441 |
| 5 | `adx_H1=[25,35)` | 0.0388 |
| 6 | `hour_bucket=12-16` | 0.0348 |
| 7 | `rsi_H1=[30,50)` | 0.0337 |
| 8 | `H1_ema_stack=up` | 0.0337 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0331 |
| 10 | `H1_adx_label=trending` | 0.0327 |
| 11 | `H4_ema_stack=mixed` | 0.0307 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0252 |
| 13 | `H4_ema_stack=up` | 0.0237 |
| 14 | `H1_adx_label=weak_trend` | 0.0230 |
| 15 | `adx_H1=[18,25)` | 0.0209 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **553**  ·  Baseline win-rate: **24.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (15 W / 5 L = 20 trade · +50.2pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 = [30,50)`
   - `hour_bucket ≠ 16-20`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 32 L = 32 trade · -24.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `session ≠ overlap`

**2. Win-rate 0.0%** (0 W / 30 L = 30 trade · -24.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `us10y_chg1d ≠ [0,0.5)`
   - `bb_extreme_upper ≠ False`

**3. Win-rate 0.0%** (0 W / 80 L = 80 trade · -24.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `us10y_chg1d ≠ [0,0.5)`
   - `bb_extreme_upper = False`

**4. Win-rate 4.5%** (1 W / 21 L = 22 trade · -20.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow = Mon`

**5. Win-rate 9.5%** (2 W / 19 L = 21 trade · -15.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `us10y_chg1d = [0,0.5)`

**6. Win-rate 15.6%** (5 W / 27 L = 32 trade · -9.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow ≠ Mon`
   - `macro_alignment = neutral`

**7. Win-rate 17.1%** (12 W / 58 L = 70 trade · -7.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 ≠ [30,50)`
   - `ml_confidence_bucket = [50,60)`

**8. Win-rate 21.7%** (5 W / 18 L = 23 trade · -3.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `session = overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0891 |
| 2 | `H4_ema_stack=NA` | 0.0568 |
| 3 | `sar_bearish=False` | 0.0384 |
| 4 | `sar_bearish=True` | 0.0382 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0367 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0354 |
| 7 | `rsi_H1=[30,50)` | 0.0302 |
| 8 | `rsi_H4=[75,+∞)` | 0.0242 |
| 9 | `macro_alignment=weak_pro` | 0.0223 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0221 |
| 11 | `H1_ema_stack=up` | 0.0191 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0187 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0184 |
| 14 | `bb_extreme_upper=False` | 0.0183 |
| 15 | `rsi_H4=[30,50)` | 0.0178 |

---

## NDX.INDX · pulse1 · SELL
- Toplam çözülmüş: **472**  ·  Baseline win-rate: **53.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.2%** (41 W / 3 L = 44 trade · +39.8pp vs baseline)
   - `H1_adx_label = trending`
   - `dow ≠ Tue`
   - `adx_H1 = [35,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.3%** (1 W / 29 L = 30 trade · -50.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `dow = Tue`

**2. Win-rate 8.0%** (2 W / 23 L = 25 trade · -45.4pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ mixed`
   - `dow = Wed`
   - `adx_H4 = [35,+∞)`

**3. Win-rate 33.3%** (7 W / 14 L = 21 trade · -20.1pp vs baseline)
   - `H1_adx_label = trending`
   - `dow = Tue`
   - `H1_ema_stack ≠ down`

**4. Win-rate 35.0%** (7 W / 13 L = 20 trade · -18.4pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `dow ≠ Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0729 |
| 2 | `adx_H1=[35,+∞)` | 0.0525 |
| 3 | `adx_H1=[−∞,18)` | 0.0444 |
| 4 | `H1_adx_label=ranging` | 0.0397 |
| 5 | `dow=Tue` | 0.0318 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0268 |
| 7 | `dow=Mon` | 0.0245 |
| 8 | `rsi_H4=[50,65)` | 0.0233 |
| 9 | `rsi_H4=[30,50)` | 0.0226 |
| 10 | `H4_ema_stack=up` | 0.0196 |
| 11 | `adx_H4=[18,25)` | 0.0195 |
| 12 | `dow=Fri` | 0.0186 |
| 13 | `bb_extreme_lower=False` | 0.0181 |
| 14 | `H4_adx_label=trending` | 0.0171 |
| 15 | `H4_ema_stack=mixed` | 0.0156 |

---

## NDX.INDX · pulse1_inv · BUY
- Toplam çözülmüş: **168**  ·  Baseline win-rate: **48.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.1%** (6 W / 17 L = 23 trade · -22.1pp vs baseline)
   - `H4_adx_label ≠ weak_trend`
   - `adx_H1 ≠ [−∞,18)`
   - `H1_ema_stack = up`

**2. Win-rate 33.3%** (11 W / 22 L = 33 trade · -14.9pp vs baseline)
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=mid_session` | 0.0341 |
| 2 | `dow=Wed` | 0.0325 |
| 3 | `volatility_regime=normal` | 0.0303 |
| 4 | `H1_adx_label=ranging` | 0.0298 |
| 5 | `session=overlap` | 0.0289 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0287 |
| 7 | `dow=Thu` | 0.0285 |
| 8 | `adx_H4=[18,25)` | 0.0282 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0275 |
| 10 | `H1_ema_stack=up` | 0.0264 |
| 11 | `H4_adx_label=weak_trend` | 0.0261 |
| 12 | `rsi_H4=[50,65)` | 0.0257 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0256 |
| 14 | `session=us` | 0.0233 |
| 15 | `H1_adx_label=weak_trend` | 0.0217 |

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
- Toplam çözülmüş: **271**  ·  Baseline win-rate: **39.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (20 W / 0 L = 20 trade · +60.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [-3,0)`
   - `dow ≠ Fri`

**2. Win-rate 81.0%** (17 W / 4 L = 21 trade · +41.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [-3,0)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.7%** (2 W / 33 L = 35 trade · -34.2pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = True`

**2. Win-rate 15.1%** (8 W / 45 L = 53 trade · -24.8pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 32.0%** (8 W / 17 L = 25 trade · -7.9pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1140 |
| 2 | `sar_bearish=True` | 0.0976 |
| 3 | `rsi_H1=[30,50)` | 0.0470 |
| 4 | `bb_extreme_upper=True` | 0.0403 |
| 5 | `dow=Wed` | 0.0354 |
| 6 | `dow=Thu` | 0.0265 |
| 7 | `bb_extreme_upper=False` | 0.0221 |
| 8 | `H1_adx_label=trending` | 0.0210 |
| 9 | `dow=Mon` | 0.0197 |
| 10 | `adx_H1=[25,35)` | 0.0190 |
| 11 | `vix_chg1d=[-3,0)` | 0.0186 |
| 12 | `H1_adx_label=weak_trend` | 0.0186 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0184 |
| 14 | `macro_alignment=weak_pro` | 0.0180 |
| 15 | `adx_H1=[18,25)` | 0.0173 |

---

## NDX.INDX · pulse2 · SELL
- Toplam çözülmüş: **218**  ·  Baseline win-rate: **60.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (22 W / 2 L = 24 trade · +31.6pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 85.0%** (17 W / 3 L = 20 trade · +24.9pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.0%** (3 W / 17 L = 20 trade · -45.1pp vs baseline)
   - `dow = Tue`
   - `dxy_chg1d = [-0.5,0)`

**2. Win-rate 27.3%** (6 W / 16 L = 22 trade · -32.8pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.0667 |
| 2 | `H4_ema_stack=up` | 0.0519 |
| 3 | `dxy_chg1d=[0.5,+∞)` | 0.0512 |
| 4 | `H4_ema_stack=mixed` | 0.0360 |
| 5 | `dow=Fri` | 0.0353 |
| 6 | `dow=Thu` | 0.0340 |
| 7 | `H1_ema_stack=mixed` | 0.0322 |
| 8 | `session=overlap` | 0.0299 |
| 9 | `volatility_regime=high` | 0.0280 |
| 10 | `H1_adx_label=trending` | 0.0276 |
| 11 | `session=us` | 0.0229 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0215 |
| 13 | `hour_bucket=12-16` | 0.0211 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0192 |
| 15 | `H1_adx_label=weak_trend` | 0.0190 |

---

## NDX.INDX · pulse2_inv · BUY
- Toplam çözülmüş: **123**  ·  Baseline win-rate: **56.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +28.9pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `H4_ema_stack = down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (9 W / 18 L = 27 trade · -22.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `rsi_H1 = [30,50)`
   - `H4_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0582 |
| 2 | `rsi_H1=[30,50)` | 0.0477 |
| 3 | `mtf_trend=mixed` | 0.0429 |
| 4 | `bb_extreme_lower=False` | 0.0398 |
| 5 | `mtf_trend=all_down` | 0.0380 |
| 6 | `sar_bearish=False` | 0.0374 |
| 7 | `rsi_H1=[50,65)` | 0.0370 |
| 8 | `sar_bearish=True` | 0.0335 |
| 9 | `session_phase=mid_session` | 0.0314 |
| 10 | `regime_label=ranging` | 0.0301 |
| 11 | `vix_chg1d=[0,3)` | 0.0281 |
| 12 | `adx_H4=[25,35)` | 0.0260 |
| 13 | `bb_extreme_lower=True` | 0.0258 |
| 14 | `H4_adx_label=ranging` | 0.0227 |
| 15 | `regime_label=strong_trend_down` | 0.0217 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **540**  ·  Baseline win-rate: **31.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (34 W / 0 L = 34 trade · +68.9pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [-0.5,0)`
   - `H4_ema_stack = up`

**2. Win-rate 76.2%** (16 W / 5 L = 21 trade · +45.1pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 107 L = 107 trade · -31.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `mtf_trend = all_up`

**2. Win-rate 4.8%** (1 W / 20 L = 21 trade · -26.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `mtf_trend ≠ all_up`

**3. Win-rate 8.0%** (4 W / 46 L = 50 trade · -23.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `vix_chg1d = [−∞,-3)`

**4. Win-rate 8.3%** (2 W / 22 L = 24 trade · -22.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session_phase = mid_session`

**5. Win-rate 9.1%** (2 W / 20 L = 22 trade · -22.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session_phase ≠ mid_session`

**6. Win-rate 18.4%** (7 W / 31 L = 38 trade · -12.7pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow = Mon`

**7. Win-rate 25.7%** (9 W / 26 L = 35 trade · -5.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `vix_chg1d ≠ [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1164 |
| 2 | `sar_bearish=True` | 0.1112 |
| 3 | `H4_ema_stack=NA` | 0.0291 |
| 4 | `bb_extreme_upper=False` | 0.0275 |
| 5 | `macro_alignment=weak_pro` | 0.0267 |
| 6 | `near_resistance=False` | 0.0226 |
| 7 | `overbought=False` | 0.0224 |
| 8 | `H1_ema_stack=up` | 0.0207 |
| 9 | `near_resistance=True` | 0.0189 |
| 10 | `dow=Wed` | 0.0181 |
| 11 | `rsi_H4=[75,+∞)` | 0.0170 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0166 |
| 13 | `rsi_H1=[65,75)` | 0.0164 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0151 |
| 15 | `mtf_trend=mixed` | 0.0151 |

---

## NDX.INDX · pulse3 · SELL
- Toplam çözülmüş: **577**  ·  Baseline win-rate: **61.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (44 W / 0 L = 44 trade · +38.5pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 91.3%** (21 W / 2 L = 23 trade · +29.8pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 = [30,50)`

**3. Win-rate 88.1%** (37 W / 5 L = 42 trade · +26.6pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow = Fri`
   - `session_phase ≠ mid_session`

**4. Win-rate 76.5%** (26 W / 8 L = 34 trade · +15.0pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow ≠ Fri`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.8%** (1 W / 20 L = 21 trade · -56.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [−∞,-3)`

**2. Win-rate 9.5%** (2 W / 19 L = 21 trade · -52.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `vix_chg1d = [−∞,-3)`

**3. Win-rate 15.4%** (4 W / 22 L = 26 trade · -46.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ mixed`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0789 |
| 2 | `adx_H1=[−∞,18)` | 0.0515 |
| 3 | `dow=Tue` | 0.0401 |
| 4 | `adx_H1=[35,+∞)` | 0.0381 |
| 5 | `H1_adx_label=ranging` | 0.0379 |
| 6 | `macro_alignment=strong_against` | 0.0344 |
| 7 | `H1_ema_stack=mixed` | 0.0330 |
| 8 | `adx_H4=[35,+∞)` | 0.0267 |
| 9 | `H4_ema_stack=up` | 0.0261 |
| 10 | `sar_bearish=True` | 0.0224 |
| 11 | `dow=Fri` | 0.0219 |
| 12 | `macro_alignment=neutral` | 0.0183 |
| 13 | `sar_bearish=False` | 0.0181 |
| 14 | `H1_ema_stack=down` | 0.0171 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0163 |

---

## NDX.INDX · pulse3_inv · BUY
- Toplam çözülmüş: **228**  ·  Baseline win-rate: **56.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +43.9pp vs baseline)
   - `H4_ema_stack = up`
   - `adx_H1 = [18,25)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.3%** (9 W / 24 L = 33 trade · -28.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_H4 ≠ [35,+∞)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0526 |
| 2 | `H4_adx_label=trending` | 0.0474 |
| 3 | `rsi_H4=[30,50)` | 0.0397 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0396 |
| 5 | `rsi_H4=[50,65)` | 0.0350 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0329 |
| 7 | `session=us` | 0.0313 |
| 8 | `H4_ema_stack=down` | 0.0285 |
| 9 | `adx_H4=[−∞,18)` | 0.0260 |
| 10 | `H1_adx_label=weak_trend` | 0.0253 |
| 11 | `session_phase=mid_session` | 0.0249 |
| 12 | `adx_H4=[35,+∞)` | 0.0247 |
| 13 | `adx_H4=[25,35)` | 0.0244 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0229 |
| 15 | `dow=Wed` | 0.0227 |

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
- Toplam çözülmüş: **203**  ·  Baseline win-rate: **31.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +51.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -31.0pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label = trending`

**2. Win-rate 4.5%** (1 W / 21 L = 22 trade · -26.5pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label ≠ trending`

**3. Win-rate 28.6%** (8 W / 20 L = 28 trade · -2.4pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label = trending`

**4. Win-rate 29.2%** (7 W / 17 L = 24 trade · -1.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session = overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0935 |
| 2 | `H1_ema_stack=up` | 0.0680 |
| 3 | `H4_ema_stack=mixed` | 0.0573 |
| 4 | `mtf_trend=all_down` | 0.0547 |
| 5 | `mtf_trend=mixed` | 0.0494 |
| 6 | `H4_adx_label=trending` | 0.0431 |
| 7 | `rsi_H4=[65,75)` | 0.0336 |
| 8 | `dow=Mon` | 0.0271 |
| 9 | `H4_adx_label=ranging` | 0.0204 |
| 10 | `H1_ema_stack=down` | 0.0171 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0167 |
| 12 | `regime_label=transition` | 0.0166 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0162 |
| 14 | `M30_ema_stack=up` | 0.0155 |
| 15 | `session=overlap` | 0.0154 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **206**  ·  Baseline win-rate: **2.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 52 L = 52 trade · -2.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 ≠ [50,65)`

**2. Win-rate 0.0%** (0 W / 24 L = 24 trade · -2.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_M30 = [25,35)`

**3. Win-rate 0.0%** (0 W / 78 L = 78 trade · -2.9pp vs baseline)
   - `adx_H1 = [−∞,18)`

**4. Win-rate 6.2%** (2 W / 30 L = 32 trade · 3.3pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_M30 ≠ [25,35)`
   - `vix_chg1d ≠ [3,+∞)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · 17.1pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `rsi_H1 = [50,65)`
   - `adx_M30 ≠ [25,35)`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H4=[18,25)` | 0.0417 |
| 2 | `H1_adx_label=trending` | 0.0391 |
| 3 | `H1_adx_label=ranging` | 0.0376 |
| 4 | `adx_H1=[−∞,18)` | 0.0368 |
| 5 | `dow=Tue` | 0.0340 |
| 6 | `H4_adx_label=trending` | 0.0332 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0322 |
| 8 | `H1_ema_stack=down` | 0.0310 |
| 9 | `rsi_H1=[50,65)` | 0.0293 |
| 10 | `M30_adx_label=ranging` | 0.0272 |
| 11 | `vix_chg1d=[0,3)` | 0.0252 |
| 12 | `H1_ema_stack=up` | 0.0249 |
| 13 | `macro_alignment=neutral` | 0.0246 |
| 14 | `session_phase=late_pit` | 0.0232 |
| 15 | `M30_adx_label=trending` | 0.0219 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **408**  ·  Baseline win-rate: **85.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +14.5pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`
   - `adx_M30 = [35,+∞)`

**2. Win-rate 100.0%** (106 W / 0 L = 106 trade · +14.5pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label ≠ trending`
   - `H4_adx_label ≠ weak_trend`
   - `session_phase ≠ late_pit`

**3. Win-rate 100.0%** (20 W / 0 L = 20 trade · +14.5pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label ≠ trending`
   - `H4_adx_label ≠ weak_trend`
   - `session_phase = late_pit`

**4. Win-rate 97.3%** (36 W / 1 L = 37 trade · +11.8pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dow = Fri`

**5. Win-rate 93.9%** (31 W / 2 L = 33 trade · +8.4pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label = trending`
   - `bb_pctb_M30 = [0.2,0.5)`

**6. Win-rate 90.9%** (30 W / 3 L = 33 trade · +5.4pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `H1_adx_label ≠ trending`
   - `H4_adx_label = weak_trend`

**7. Win-rate 80.0%** (20 W / 5 L = 25 trade · -5.5pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d = [−∞,-3)`
   - `adx_M30 ≠ [35,+∞)`

**8. Win-rate 78.7%** (48 W / 13 L = 61 trade · -6.8pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.0%** (12 W / 28 L = 40 trade · -55.5pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dist_low_M30 ≠ [0.7,1.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0578 |
| 2 | `H1_adx_label=trending` | 0.0424 |
| 3 | `dist_low_M30=[0.3,0.7)` | 0.0385 |
| 4 | `dist_low_M30=[1.5,+∞)` | 0.0367 |
| 5 | `dow=Fri` | 0.0352 |
| 6 | `dow=Mon` | 0.0340 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0323 |
| 8 | `macro_alignment=neutral` | 0.0320 |
| 9 | `vix_chg1d=[-3,0)` | 0.0289 |
| 10 | `macd_atr_M30=[0,0.3)` | 0.0261 |
| 11 | `bb_pctb_M30=[0.2,0.5)` | 0.0256 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0229 |
| 13 | `adx_H1=[35,+∞)` | 0.0196 |
| 14 | `sar_bearish=True` | 0.0186 |
| 15 | `sar_bearish=False` | 0.0175 |

---

## USOIL.FOREX · ml:aggressive · BUY
- Toplam çözülmüş: **330**  ·  Baseline win-rate: **30.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (27 W / 9 L = 36 trade · +44.4pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase = off_hours`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -30.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -30.6pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -25.8pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -16.3pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -10.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `adx_H1 = [−∞,18)`

**6. Win-rate 25.7%** (9 W / 26 L = 35 trade · -4.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `consec_red_M30 = [0,2)`

**7. Win-rate 25.8%** (8 W / 23 L = 31 trade · -4.8pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0760 |
| 2 | `H4_ema_stack=down` | 0.0744 |
| 3 | `H4_ema_stack=mixed` | 0.0598 |
| 4 | `H4_adx_label=trending` | 0.0490 |
| 5 | `H1_ema_stack=down` | 0.0389 |
| 6 | `H1_ema_stack=up` | 0.0388 |
| 7 | `macro_alignment=strong_against` | 0.0207 |
| 8 | `adx_H4=[−∞,18)` | 0.0202 |
| 9 | `H4_adx_label=weak_trend` | 0.0194 |
| 10 | `adx_H4=[18,25)` | 0.0186 |
| 11 | `vix_chg1d=[0,3)` | 0.0184 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0180 |
| 13 | `regime_label=ranging` | 0.0172 |
| 14 | `adx_H4=[25,35)` | 0.0170 |
| 15 | `regime_label=transition` | 0.0158 |

---

## USOIL.FOREX · ml:aggressive · SELL
- Toplam çözülmüş: **309**  ·  Baseline win-rate: **69.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (31 W / 0 L = 31 trade · +30.1pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +25.1pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 90.1%** (82 W / 9 L = 91 trade · +20.2pp vs baseline)
   - `H1_ema_stack = down`
   - `dow ≠ Fri`
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.1%** (6 W / 29 L = 35 trade · -52.8pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0628 |
| 2 | `H1_ema_stack=down` | 0.0591 |
| 3 | `adx_M30=[35,+∞)` | 0.0482 |
| 4 | `dow=Fri` | 0.0467 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0458 |
| 6 | `dow=Mon` | 0.0362 |
| 7 | `mtf_trend=mixed` | 0.0354 |
| 8 | `M30_ema_stack=mixed` | 0.0342 |
| 9 | `mtf_trend=all_down` | 0.0342 |
| 10 | `M30_ema_stack=down` | 0.0299 |
| 11 | `rsi_H4=[50,65)` | 0.0291 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0225 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0184 |
| 14 | `M30_adx_label=ranging` | 0.0172 |
| 15 | `adx_M30=[−∞,18)` | 0.0169 |

---

## USOIL.FOREX · ml:balanced · BUY
- Toplam çözülmüş: **331**  ·  Baseline win-rate: **30.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -30.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `macro_alignment = strong_against`
   - `session_phase ≠ off_hours`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -30.2pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -25.4pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -15.9pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.0%** (5 W / 15 L = 20 trade · -5.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `macro_alignment ≠ strong_against`
   - `M30_ema_stack ≠ up`

**6. Win-rate 25.8%** (8 W / 23 L = 31 trade · -4.4pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

**7. Win-rate 33.3%** (7 W / 14 L = 21 trade · 3.1pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `macro_alignment = strong_against`
   - `session_phase = off_hours`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0761 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0639 |
| 3 | `H4_ema_stack=mixed` | 0.0510 |
| 4 | `H1_ema_stack=up` | 0.0441 |
| 5 | `H4_adx_label=trending` | 0.0429 |
| 6 | `H1_ema_stack=down` | 0.0417 |
| 7 | `macro_alignment=strong_against` | 0.0216 |
| 8 | `regime_label=transition` | 0.0198 |
| 9 | `H4_adx_label=weak_trend` | 0.0193 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0188 |
| 11 | `adx_H4=[35,+∞)` | 0.0184 |
| 12 | `vix_chg1d=[0,3)` | 0.0181 |
| 13 | `regime_label=ranging` | 0.0179 |
| 14 | `adx_H4=[−∞,18)` | 0.0173 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0147 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **308**  ·  Baseline win-rate: **70.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (31 W / 0 L = 31 trade · +29.9pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +24.9pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 90.1%** (82 W / 9 L = 91 trade · +20.0pp vs baseline)
   - `H1_ema_stack = down`
   - `dow ≠ Fri`
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.1%** (6 W / 29 L = 35 trade · -53.0pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0584 |
| 2 | `H1_ema_stack=down` | 0.0582 |
| 3 | `dow=Fri` | 0.0469 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0417 |
| 5 | `adx_M30=[35,+∞)` | 0.0410 |
| 6 | `dow=Mon` | 0.0389 |
| 7 | `mtf_trend=mixed` | 0.0381 |
| 8 | `M30_ema_stack=mixed` | 0.0333 |
| 9 | `mtf_trend=all_down` | 0.0316 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0286 |
| 11 | `rsi_H4=[50,65)` | 0.0267 |
| 12 | `M30_ema_stack=down` | 0.0246 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0237 |
| 14 | `M30_adx_label=ranging` | 0.0174 |
| 15 | `rsi_H4=[30,50)` | 0.0147 |

---

## USOIL.FOREX · ml:full_power · BUY
- Toplam çözülmüş: **330**  ·  Baseline win-rate: **30.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (27 W / 9 L = 36 trade · +44.4pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase = off_hours`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -30.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -30.6pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -25.8pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -16.3pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -10.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `adx_H1 = [−∞,18)`

**6. Win-rate 25.7%** (9 W / 26 L = 35 trade · -4.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `consec_red_M30 = [0,2)`

**7. Win-rate 25.8%** (8 W / 23 L = 31 trade · -4.8pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0770 |
| 2 | `H4_ema_stack=down` | 0.0721 |
| 3 | `H4_ema_stack=mixed` | 0.0619 |
| 4 | `H4_adx_label=trending` | 0.0474 |
| 5 | `H1_ema_stack=up` | 0.0380 |
| 6 | `H1_ema_stack=down` | 0.0372 |
| 7 | `macro_alignment=strong_against` | 0.0219 |
| 8 | `adx_H4=[−∞,18)` | 0.0213 |
| 9 | `H4_adx_label=weak_trend` | 0.0208 |
| 10 | `H4_adx_label=ranging` | 0.0198 |
| 11 | `vix_chg1d=[0,3)` | 0.0187 |
| 12 | `adx_H4=[18,25)` | 0.0185 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0180 |
| 14 | `regime_label=transition` | 0.0178 |
| 15 | `adx_H4=[25,35)` | 0.0173 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **307**  ·  Baseline win-rate: **70.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (31 W / 0 L = 31 trade · +29.6pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +24.6pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 90.1%** (82 W / 9 L = 91 trade · +19.7pp vs baseline)
   - `H1_ema_stack = down`
   - `dow ≠ Fri`
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.1%** (6 W / 29 L = 35 trade · -53.3pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=down` | 0.0667 |
| 2 | `M30_adx_label=trending` | 0.0515 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0458 |
| 4 | `adx_M30=[35,+∞)` | 0.0436 |
| 5 | `dow=Fri` | 0.0427 |
| 6 | `mtf_trend=mixed` | 0.0392 |
| 7 | `dow=Mon` | 0.0388 |
| 8 | `M30_ema_stack=mixed` | 0.0370 |
| 9 | `rsi_H4=[50,65)` | 0.0362 |
| 10 | `M30_ema_stack=down` | 0.0301 |
| 11 | `vix_chg1d=[−∞,-3)` | 0.0291 |
| 12 | `mtf_trend=all_down` | 0.0247 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0175 |
| 14 | `M30_adx_label=ranging` | 0.0148 |
| 15 | `rsi_H1=[30,50)` | 0.0148 |

---

## USOIL.FOREX · ml:main · BUY
- Toplam çözülmüş: **331**  ·  Baseline win-rate: **29.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -29.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -29.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [30,50)`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -24.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [30,50)`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -21.8pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ mixed`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -9.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H1_adx_label = ranging`

**6. Win-rate 25.7%** (9 W / 26 L = 35 trade · -4.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `consec_red_M30 = [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0762 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0735 |
| 3 | `H4_ema_stack=mixed` | 0.0480 |
| 4 | `H1_ema_stack=up` | 0.0418 |
| 5 | `H4_adx_label=trending` | 0.0417 |
| 6 | `H1_ema_stack=down` | 0.0415 |
| 7 | `H4_adx_label=weak_trend` | 0.0212 |
| 8 | `macro_alignment=strong_against` | 0.0209 |
| 9 | `regime_label=transition` | 0.0202 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0193 |
| 11 | `vix_chg1d=[0,3)` | 0.0185 |
| 12 | `adx_H4=[−∞,18)` | 0.0176 |
| 13 | `adx_H4=[35,+∞)` | 0.0157 |
| 14 | `regime_label=ranging` | 0.0149 |
| 15 | `adx_H4=[25,35)` | 0.0146 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **311**  ·  Baseline win-rate: **69.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (32 W / 0 L = 32 trade · +30.2pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +25.2pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 90.1%** (82 W / 9 L = 91 trade · +20.3pp vs baseline)
   - `H1_ema_stack = down`
   - `dow ≠ Fri`
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**4. Win-rate 85.7%** (18 W / 3 L = 21 trade · +15.9pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.6%** (6 W / 28 L = 34 trade · -52.2pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`

**2. Win-rate 30.0%** (6 W / 14 L = 20 trade · -39.8pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0591 |
| 2 | `H1_ema_stack=down` | 0.0552 |
| 3 | `adx_M30=[35,+∞)` | 0.0503 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0501 |
| 5 | `dow=Fri` | 0.0405 |
| 6 | `M30_ema_stack=down` | 0.0355 |
| 7 | `mtf_trend=mixed` | 0.0346 |
| 8 | `M30_ema_stack=mixed` | 0.0339 |
| 9 | `mtf_trend=all_down` | 0.0333 |
| 10 | `dow=Mon` | 0.0295 |
| 11 | `rsi_H4=[50,65)` | 0.0241 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0235 |
| 13 | `M30_adx_label=ranging` | 0.0185 |
| 14 | `dist_low_M30=[1.5,+∞)` | 0.0184 |
| 15 | `rsi_H4=[30,50)` | 0.0179 |

---

## USOIL.FOREX · ml:ultra_safe · BUY
- Toplam çözülmüş: **331**  ·  Baseline win-rate: **29.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -29.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`

**2. Win-rate 0.0%** (0 W / 44 L = 44 trade · -29.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [30,50)`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -24.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [30,50)`

**4. Win-rate 8.1%** (3 W / 34 L = 37 trade · -21.8pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ mixed`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -9.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `adx_H1 = [−∞,18)`

**6. Win-rate 28.0%** (7 W / 18 L = 25 trade · -1.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0762 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0734 |
| 3 | `H4_ema_stack=mixed` | 0.0492 |
| 4 | `H1_ema_stack=up` | 0.0427 |
| 5 | `H1_ema_stack=down` | 0.0412 |
| 6 | `H4_adx_label=trending` | 0.0408 |
| 7 | `H4_adx_label=weak_trend` | 0.0217 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0197 |
| 9 | `macro_alignment=strong_against` | 0.0195 |
| 10 | `regime_label=transition` | 0.0187 |
| 11 | `adx_H4=[−∞,18)` | 0.0179 |
| 12 | `vix_chg1d=[0,3)` | 0.0179 |
| 13 | `adx_H4=[35,+∞)` | 0.0159 |
| 14 | `regime_label=ranging` | 0.0150 |
| 15 | `macro_alignment=neutral` | 0.0140 |

---

## USOIL.FOREX · ml:ultra_safe · SELL
- Toplam çözülmüş: **311**  ·  Baseline win-rate: **69.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (32 W / 0 L = 32 trade · +30.2pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 95.0%** (19 W / 1 L = 20 trade · +25.2pp vs baseline)
   - `H1_ema_stack = down`
   - `dow = Fri`
   - `vix_chg1d = [-3,0)`

**3. Win-rate 90.1%** (82 W / 9 L = 91 trade · +20.3pp vs baseline)
   - `H1_ema_stack = down`
   - `dow ≠ Fri`
   - `dist_low_M30 = [1.5,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.1%** (6 W / 29 L = 35 trade · -52.7pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0712 |
| 2 | `H1_ema_stack=down` | 0.0520 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0485 |
| 4 | `adx_M30=[35,+∞)` | 0.0475 |
| 5 | `dow=Fri` | 0.0392 |
| 6 | `mtf_trend=mixed` | 0.0364 |
| 7 | `mtf_trend=all_down` | 0.0338 |
| 8 | `dow=Mon` | 0.0331 |
| 9 | `M30_ema_stack=down` | 0.0314 |
| 10 | `M30_ema_stack=mixed` | 0.0303 |
| 11 | `rsi_H4=[50,65)` | 0.0282 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0234 |
| 13 | `adx_M30=[−∞,18)` | 0.0219 |
| 14 | `dist_low_M30=[1.5,+∞)` | 0.0184 |
| 15 | `M30_adx_label=ranging` | 0.0155 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **2069**  ·  Baseline win-rate: **17.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 71 L = 71 trade · -17.1pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `H1_ema_stack = mixed`

**2. Win-rate 0.0%** (0 W / 335 L = 335 trade · -17.1pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label = trending`
   - `adx_H4 ≠ [35,+∞)`
   - `adx_M30 = [35,+∞)`

**3. Win-rate 0.7%** (1 W / 141 L = 142 trade · -16.4pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `adx_H4 ≠ [25,35)`
   - `vix_chg1d ≠ [3,+∞)`

**4. Win-rate 0.7%** (1 W / 141 L = 142 trade · -16.4pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `adx_H1 = [−∞,18)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**5. Win-rate 2.6%** (1 W / 38 L = 39 trade · -14.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow ≠ Thu`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `vix_chg1d = [−∞,-3)`

**6. Win-rate 4.5%** (1 W / 21 L = 22 trade · -12.6pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `adx_H4 = [25,35)`
   - `hour_bucket = 20-24`

**7. Win-rate 5.3%** (15 W / 270 L = 285 trade · -11.8pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label = trending`
   - `adx_H4 ≠ [35,+∞)`
   - `adx_M30 ≠ [35,+∞)`

**8. Win-rate 10.0%** (3 W / 27 L = 30 trade · -7.1pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `adx_H4 ≠ [25,35)`
   - `vix_chg1d = [3,+∞)`

**9. Win-rate 12.2%** (6 W / 43 L = 49 trade · -4.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `adx_H1 = [−∞,18)`
   - `dist_high_M30 = [1.5,+∞)`

**10. Win-rate 13.6%** (3 W / 19 L = 22 trade · -3.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `H1_ema_stack ≠ mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0396 |
| 2 | `vix_chg1d=[−∞,-3)` | 0.0385 |
| 3 | `H4_ema_stack=down` | 0.0368 |
| 4 | `H4_ema_stack=mixed` | 0.0367 |
| 5 | `H1_ema_stack=up` | 0.0320 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0268 |
| 7 | `macro_alignment=strong_pro` | 0.0244 |
| 8 | `regime_label=transition` | 0.0242 |
| 9 | `H4_adx_label=ranging` | 0.0237 |
| 10 | `dow=Mon` | 0.0231 |
| 11 | `regime_label=ranging` | 0.0214 |
| 12 | `rsi_H4=[30,50)` | 0.0209 |
| 13 | `H1_ema_stack=down` | 0.0207 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0188 |
| 15 | `M30_adx_label=trending` | 0.0178 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **1358**  ·  Baseline win-rate: **72.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (250 W / 0 L = 250 trade · +27.2pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label = trending`
   - `H4_adx_label = ranging`
   - `dow ≠ Tue`

**2. Win-rate 100.0%** (26 W / 0 L = 26 trade · +27.2pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `rsi_H1 = [−∞,30)`

**3. Win-rate 95.0%** (19 W / 1 L = 20 trade · +22.2pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `H4_ema_stack = down`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 94.4%** (118 W / 7 L = 125 trade · +21.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `M30_ema_stack ≠ down`
   - `dxy_chg1d = [0,0.5)`

**5. Win-rate 91.4%** (202 W / 19 L = 221 trade · +18.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label = trending`
   - `H4_adx_label ≠ ranging`
   - `dxy_chg1d = [0,0.5)`

**6. Win-rate 90.6%** (29 W / 3 L = 32 trade · +17.8pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label = trending`
   - `H4_adx_label = ranging`
   - `dow = Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.8%** (1 W / 25 L = 26 trade · -69.0pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `M30_ema_stack = down`
   - `us10y_chg1d = [0.5,+∞)`

**2. Win-rate 7.5%** (6 W / 74 L = 80 trade · -65.3pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `H4_ema_stack ≠ down`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0634 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0617 |
| 3 | `H1_ema_stack=up` | 0.0334 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0315 |
| 5 | `M30_adx_label=ranging` | 0.0279 |
| 6 | `adx_M30=[35,+∞)` | 0.0276 |
| 7 | `adx_M30=[−∞,18)` | 0.0271 |
| 8 | `dow=Mon` | 0.0256 |
| 9 | `H1_adx_label=ranging` | 0.0245 |
| 10 | `adx_H1=[−∞,18)` | 0.0211 |
| 11 | `H4_adx_label=trending` | 0.0207 |
| 12 | `H1_ema_stack=down` | 0.0200 |
| 13 | `dow=Fri` | 0.0175 |
| 14 | `adx_H4=[−∞,18)` | 0.0168 |
| 15 | `macro_alignment=neutral` | 0.0162 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **849**  ·  Baseline win-rate: **22.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 97 L = 97 trade · -22.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`
   - `H1_ema_stack ≠ mixed`

**2. Win-rate 0.0%** (0 W / 43 L = 43 trade · -22.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `H1_ema_stack ≠ up`

**3. Win-rate 0.0%** (0 W / 288 L = 288 trade · -22.9pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ down`
   - `us10y_chg1d ≠ [0,0.5)`

**4. Win-rate 5.0%** (1 W / 19 L = 20 trade · -17.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`
   - `H1_ema_stack = mixed`

**5. Win-rate 6.7%** (2 W / 28 L = 30 trade · -16.2pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ down`
   - `us10y_chg1d = [0,0.5)`

**6. Win-rate 6.9%** (2 W / 27 L = 29 trade · -16.0pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = down`

**7. Win-rate 30.8%** (12 W / 27 L = 39 trade · 7.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0989 |
| 2 | `H4_ema_stack=down` | 0.0890 |
| 3 | `H4_ema_stack=mixed` | 0.0794 |
| 4 | `H1_ema_stack=down` | 0.0657 |
| 5 | `H1_ema_stack=up` | 0.0620 |
| 6 | `H4_adx_label=trending` | 0.0457 |
| 7 | `M30_ema_stack=up` | 0.0297 |
| 8 | `rsi_H4=[30,50)` | 0.0281 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0236 |
| 10 | `rsi_H4=[65,75)` | 0.0219 |
| 11 | `M30_ema_stack=mixed` | 0.0214 |
| 12 | `vix_chg1d=[0,3)` | 0.0177 |
| 13 | `adx_H4=[18,25)` | 0.0172 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0170 |
| 15 | `macro_alignment=strong_against` | 0.0152 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **1034**  ·  Baseline win-rate: **70.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (179 W / 0 L = 179 trade · +29.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `H1_ema_stack = down`
   - `consec_green_M30 = [0,2)`

**2. Win-rate 97.9%** (46 W / 1 L = 47 trade · +27.1pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `H1_ema_stack = down`
   - `consec_green_M30 ≠ [0,2)`

**3. Win-rate 90.8%** (266 W / 27 L = 293 trade · +20.0pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow ≠ Mon`
   - `rsi_H4 = [30,50)`

**4. Win-rate 90.6%** (29 W / 3 L = 32 trade · +19.8pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `H1_ema_stack ≠ down`

**5. Win-rate 81.2%** (26 W / 6 L = 32 trade · +10.4pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label = strong_trend_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.3%** (4 W / 51 L = 55 trade · -63.5pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label ≠ strong_trend_down`
   - `rsi_H1 ≠ [30,50)`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 23.3%** (7 W / 23 L = 30 trade · -47.5pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow = Mon`
   - `ml_confidence_bucket ≠ [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.1158 |
| 2 | `adx_M30=[35,+∞)` | 0.0603 |
| 3 | `dow=Mon` | 0.0437 |
| 4 | `M30_adx_label=ranging` | 0.0329 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0304 |
| 6 | `adx_M30=[−∞,18)` | 0.0302 |
| 7 | `adx_M30=[18,25)` | 0.0295 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0285 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0283 |
| 10 | `H1_ema_stack=down` | 0.0243 |
| 11 | `M30_adx_label=weak_trend` | 0.0229 |
| 12 | `mtf_trend=all_down` | 0.0220 |
| 13 | `mtf_trend=mixed` | 0.0206 |
| 14 | `dow=Fri` | 0.0197 |
| 15 | `adx_M30=[25,35)` | 0.0156 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **1416**  ·  Baseline win-rate: **19.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 219 L = 219 trade · -19.3pp vs baseline)
   - `H1_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 0.3%** (1 W / 312 L = 313 trade · -19.0pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `H1_ema_stack ≠ mixed`

**3. Win-rate 3.1%** (1 W / 31 L = 32 trade · -16.2pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 6.2%** (17 W / 256 L = 273 trade · -13.1pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `H1_ema_stack = mixed`

**5. Win-rate 13.3%** (6 W / 39 L = 45 trade · -6.0pp vs baseline)
   - `H1_ema_stack = up`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Mon`

**6. Win-rate 14.3%** (3 W / 18 L = 21 trade · -5.0pp vs baseline)
   - `H1_ema_stack = up`
   - `H4_adx_label = trending`
   - `rsi_H1 = [30,50)`
   - `bb_pctb_M30 = [−∞,0.2)`

**7. Win-rate 23.1%** (6 W / 20 L = 26 trade · 3.8pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `macro_alignment = strong_pro`
   - `dist_high_M30 ≠ [1.5,+∞)`

**8. Win-rate 24.7%** (23 W / 70 L = 93 trade · 5.4pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_M30 ≠ [35,+∞)`

**9. Win-rate 31.2%** (10 W / 22 L = 32 trade · 11.9pp vs baseline)
   - `H1_ema_stack = up`
   - `H4_adx_label = trending`
   - `rsi_H1 = [30,50)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**10. Win-rate 33.3%** (12 W / 24 L = 36 trade · 14.0pp vs baseline)
   - `H1_ema_stack = up`
   - `H4_adx_label = trending`
   - `rsi_H1 ≠ [30,50)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=up` | 0.0626 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0515 |
| 3 | `H4_ema_stack=down` | 0.0430 |
| 4 | `H1_ema_stack=down` | 0.0427 |
| 5 | `H4_adx_label=trending` | 0.0369 |
| 6 | `H4_ema_stack=mixed` | 0.0350 |
| 7 | `macro_alignment=strong_pro` | 0.0243 |
| 8 | `rsi_H4=[65,75)` | 0.0235 |
| 9 | `adx_H4=[18,25)` | 0.0221 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0216 |
| 11 | `H4_adx_label=weak_trend` | 0.0193 |
| 12 | `macro_alignment=strong_against` | 0.0178 |
| 13 | `adx_H4=[25,35)` | 0.0169 |
| 14 | `vix_chg1d=[0,3)` | 0.0166 |
| 15 | `M30_adx_label=trending` | 0.0163 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **1453**  ·  Baseline win-rate: **79.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (51 W / 0 L = 51 trade · +20.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `ml_confidence_bucket ≠ [70,80)`

**2. Win-rate 100.0%** (29 W / 0 L = 29 trade · +20.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 100.0%** (126 W / 0 L = 126 trade · +20.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack ≠ mixed`

**4. Win-rate 100.0%** (344 W / 0 L = 344 trade · +20.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow ≠ Mon`

**5. Win-rate 100.0%** (22 W / 0 L = 22 trade · +20.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow = Mon`
   - `atr_ratio_M30 = [1,1.3)`

**6. Win-rate 94.1%** (32 W / 2 L = 34 trade · +14.3pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack = mixed`

**7. Win-rate 93.4%** (71 W / 5 L = 76 trade · +13.6pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [3,+∞)`

**8. Win-rate 89.9%** (214 W / 24 L = 238 trade · +10.1pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d ≠ [−∞,-3)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `mtf_trend = all_down`

**9. Win-rate 85.0%** (17 W / 3 L = 20 trade · +5.2pp vs baseline)
   - `M30_adx_label = trending`
   - `vix_chg1d = [−∞,-3)`
   - `dow = Mon`
   - `atr_ratio_M30 ≠ [1,1.3)`

**10. Win-rate 78.8%** (26 W / 7 L = 33 trade · -1.0pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `regime_label = strong_trend_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (4 W / 16 L = 20 trade · -59.8pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `rsi_M30 = [50,65)`

**2. Win-rate 32.6%** (74 W / 153 L = 227 trade · -47.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `regime_label ≠ strong_trend_down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0827 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0403 |
| 3 | `vix_chg1d=[−∞,-3)` | 0.0382 |
| 4 | `dow=Mon` | 0.0361 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0357 |
| 6 | `adx_M30=[−∞,18)` | 0.0307 |
| 7 | `adx_M30=[35,+∞)` | 0.0304 |
| 8 | `M30_adx_label=ranging` | 0.0303 |
| 9 | `ml_confidence_bucket=[−∞,50)` | 0.0299 |
| 10 | `mtf_trend=all_down` | 0.0257 |
| 11 | `us10y_chg1d=[-0.5,0)` | 0.0241 |
| 12 | `H1_ema_stack=down` | 0.0237 |
| 13 | `adx_H4=[−∞,18)` | 0.0205 |
| 14 | `M30_ema_stack=down` | 0.0183 |
| 15 | `H4_adx_label=ranging` | 0.0179 |

---

## USOIL.FOREX · smc · BUY
- Toplam çözülmüş: **286**  ·  Baseline win-rate: **18.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 24 L = 24 trade · -18.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack ≠ mixed`

**2. Win-rate 0.0%** (0 W / 40 L = 40 trade · -18.2pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `adx_M30 ≠ [35,+∞)`

**3. Win-rate 0.0%** (0 W / 27 L = 27 trade · -18.2pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 2.6%** (1 W / 37 L = 38 trade · -15.6pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket = [70,80)`
   - `dxy_chg1d ≠ [0,0.5)`

**5. Win-rate 13.9%** (5 W / 31 L = 36 trade · -4.3pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`

**6. Win-rate 15.0%** (3 W / 17 L = 20 trade · -3.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack = mixed`

**7. Win-rate 20.0%** (4 W / 16 L = 20 trade · 1.8pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket ≠ [70,80)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `hour_bucket = 04-08`

**8. Win-rate 20.0%** (6 W / 24 L = 30 trade · 1.8pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `ml_confidence_bucket = [70,80)`
   - `dxy_chg1d = [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=ranging` | 0.0618 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0521 |
| 3 | `M30_adx_label=trending` | 0.0510 |
| 4 | `adx_M30=[−∞,18)` | 0.0507 |
| 5 | `rsi_H4=[30,50)` | 0.0411 |
| 6 | `M30_ema_stack=down` | 0.0362 |
| 7 | `hour_bucket=00-04` | 0.0337 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0308 |
| 9 | `M30_ema_stack=mixed` | 0.0292 |
| 10 | `mtf_trend=all_down` | 0.0290 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0275 |
| 12 | `rsi_H4=[50,65)` | 0.0265 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0244 |
| 14 | `ml_confidence_bucket=[−∞,50)` | 0.0242 |
| 15 | `H1_ema_stack=down` | 0.0230 |

---

## USOIL.FOREX · smc · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **82.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (62 W / 0 L = 62 trade · +17.6pp vs baseline)
   - `H1_ema_stack = down`
   - `H1_adx_label = ranging`
   - `dist_high_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (21 W / 0 L = 21 trade · +17.6pp vs baseline)
   - `H1_ema_stack = down`
   - `H1_adx_label = ranging`
   - `dist_high_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 94.7%** (36 W / 2 L = 38 trade · +12.3pp vs baseline)
   - `H1_ema_stack = down`
   - `H1_adx_label = ranging`
   - `dist_high_M30 ≠ [1.5,+∞)`

**4. Win-rate 88.0%** (22 W / 3 L = 25 trade · +5.6pp vs baseline)
   - `H1_ema_stack = down`
   - `H1_adx_label ≠ ranging`

**5. Win-rate 79.2%** (19 W / 5 L = 24 trade · -3.2pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.8%** (4 W / 25 L = 29 trade · -68.6pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=down` | 0.1447 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0846 |
| 3 | `rsi_H4=[50,65)` | 0.0721 |
| 4 | `rsi_H4=[30,50)` | 0.0591 |
| 5 | `H1_ema_stack=mixed` | 0.0458 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0368 |
| 7 | `ml_confidence_bucket=[70,80)` | 0.0354 |
| 8 | `M30_adx_label=trending` | 0.0333 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0291 |
| 10 | `vix_chg1d=[0,3)` | 0.0272 |
| 11 | `adx_H4=[25,35)` | 0.0265 |
| 12 | `H1_adx_label=ranging` | 0.0244 |
| 13 | `adx_M30=[35,+∞)` | 0.0228 |
| 14 | `M30_ema_stack=down` | 0.0226 |
| 15 | `M30_adx_label=ranging` | 0.0208 |

---

## XAUUSD · ai_panel · BUY
- Toplam çözülmüş: **122**  ·  Baseline win-rate: **74.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.8%** (30 W / 1 L = 31 trade · +22.2pp vs baseline)
   - `adx_H1 ≠ [25,35)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`

**2. Win-rate 80.8%** (21 W / 5 L = 26 trade · +6.2pp vs baseline)
   - `adx_H1 ≠ [25,35)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0,0.5)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=weak_trend` | 0.0528 |
| 2 | `adx_H1=[18,25)` | 0.0523 |
| 3 | `adx_H1=[25,35)` | 0.0491 |
| 4 | `dist_low_M30=[1.5,+∞)` | 0.0399 |
| 5 | `M30_ema_stack=up` | 0.0396 |
| 6 | `H1_adx_label=trending` | 0.0386 |
| 7 | `dist_low_M30=[0.3,0.7)` | 0.0302 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0241 |
| 9 | `adx_H1=[35,+∞)` | 0.0228 |
| 10 | `sar_bearish=True` | 0.0219 |
| 11 | `M30_adx_label=trending` | 0.0216 |
| 12 | `rsi_M30=[50,65)` | 0.0210 |
| 13 | `rsi_H1=[30,50)` | 0.0210 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0199 |
| 15 | `mtf_trend=all_up` | 0.0179 |

---

## XAUUSD · emel · BUY
- Toplam çözülmüş: **215**  ·  Baseline win-rate: **81.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (20 W / 0 L = 20 trade · +18.6pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 = [30,50)`
   - `dow = Wed`

**2. Win-rate 100.0%** (38 W / 0 L = 38 trade · +18.6pp vs baseline)
   - `macro_alignment = weak_against`
   - `M30_ema_stack = down`

**3. Win-rate 87.9%** (29 W / 4 L = 33 trade · +6.5pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 ≠ [30,50)`
   - `adx_H1 = [35,+∞)`

**4. Win-rate 86.2%** (25 W / 4 L = 29 trade · +4.8pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `consec_red_M30 ≠ [2,4)`
   - `rsi_M30 = [30,50)`
   - `dow ≠ Wed`

**5. Win-rate 86.2%** (25 W / 4 L = 29 trade · +4.8pp vs baseline)
   - `macro_alignment = weak_against`
   - `M30_ema_stack ≠ down`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0693 |
| 2 | `adx_H1=[35,+∞)` | 0.0628 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0574 |
| 4 | `macro_alignment=weak_against` | 0.0546 |
| 5 | `mtf_trend=all_down` | 0.0414 |
| 6 | `dist_low_M30=[1.5,+∞)` | 0.0366 |
| 7 | `atr_ratio_M30=[1,1.3)` | 0.0345 |
| 8 | `adx_M30=[35,+∞)` | 0.0254 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0250 |
| 10 | `M30_ema_stack=down` | 0.0233 |
| 11 | `mtf_trend=all_up` | 0.0227 |
| 12 | `consec_red_M30=[2,4)` | 0.0210 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0205 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0185 |
| 15 | `M30_ema_stack=up` | 0.0152 |

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
- Toplam çözülmüş: **333**  ·  Baseline win-rate: **62.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.7%** (26 W / 3 L = 29 trade · +27.5pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 84.0%** (21 W / 4 L = 25 trade · +21.8pp vs baseline)
   - `rsi_H1 = [−∞,30)`

**3. Win-rate 76.7%** (33 W / 10 L = 43 trade · +14.5pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0408 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0364 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0315 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0227 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0220 |
| 6 | `adx_H1=[35,+∞)` | 0.0209 |
| 7 | `adx_M30=[35,+∞)` | 0.0199 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0187 |
| 9 | `rsi_M30=[30,50)` | 0.0177 |
| 10 | `macro_alignment=weak_pro` | 0.0176 |
| 11 | `vix_chg1d=[−∞,-3)` | 0.0168 |
| 12 | `mtf_trend=all_down` | 0.0168 |
| 13 | `macro_alignment=strong_pro` | 0.0166 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0164 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0160 |

---

## XAUUSD · ml:aggressive · SELL
- Toplam çözülmüş: **158**  ·  Baseline win-rate: **22.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -19.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 12.5%** (3 W / 21 L = 24 trade · -10.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**3. Win-rate 14.3%** (4 W / 24 L = 28 trade · -8.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`

**4. Win-rate 21.7%** (5 W / 18 L = 23 trade · -1.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow = Thu`

**5. Win-rate 31.2%** (10 W / 22 L = 32 trade · 8.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0885 |
| 2 | `macro_alignment=weak_pro` | 0.0568 |
| 3 | `adx_H1=[35,+∞)` | 0.0565 |
| 4 | `macro_alignment=strong_against` | 0.0357 |
| 5 | `adx_M30=[25,35)` | 0.0302 |
| 6 | `atr_ratio_M30=[0.7,1)` | 0.0292 |
| 7 | `macro_alignment=neutral` | 0.0262 |
| 8 | `rsi_H1=[30,50)` | 0.0241 |
| 9 | `H1_adx_label=trending` | 0.0224 |
| 10 | `bb_pctb_M30=[0.8,+∞)` | 0.0220 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0208 |
| 12 | `consec_green_M30=[2,4)` | 0.0203 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0188 |
| 14 | `macro_alignment=weak_against` | 0.0176 |
| 15 | `consec_green_M30=[0,2)` | 0.0174 |

---

## XAUUSD · ml:balanced · BUY
- Toplam çözülmüş: **335**  ·  Baseline win-rate: **61.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.3%** (28 W / 3 L = 31 trade · +28.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 88.9%** (24 W / 3 L = 27 trade · +27.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.1%** (15 W / 29 L = 44 trade · -27.7pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0314 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0308 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0254 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0244 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0228 |
| 6 | `atr_ratio_M30=[0.7,1)` | 0.0202 |
| 7 | `adx_H1=[35,+∞)` | 0.0185 |
| 8 | `ml_confidence_bucket=[80,+∞)` | 0.0179 |
| 9 | `M30_ema_stack=down` | 0.0172 |
| 10 | `mtf_trend=all_down` | 0.0171 |
| 11 | `adx_M30=[35,+∞)` | 0.0170 |
| 12 | `sar_bearish=True` | 0.0169 |
| 13 | `adx_M30=[25,35)` | 0.0167 |
| 14 | `consec_red_M30=[0,2)` | 0.0161 |
| 15 | `adx_H1=[25,35)` | 0.0161 |

---

## XAUUSD · ml:balanced · SELL
- Toplam çözülmüş: **158**  ·  Baseline win-rate: **21.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.1%** (1 W / 31 L = 32 trade · -18.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 12.5%** (3 W / 21 L = 24 trade · -9.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**3. Win-rate 14.3%** (4 W / 24 L = 28 trade · -7.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`

**4. Win-rate 17.4%** (4 W / 19 L = 23 trade · -4.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow = Thu`

**5. Win-rate 29.0%** (9 W / 22 L = 31 trade · 7.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0831 |
| 2 | `macro_alignment=weak_pro` | 0.0497 |
| 3 | `adx_H1=[35,+∞)` | 0.0409 |
| 4 | `adx_M30=[25,35)` | 0.0405 |
| 5 | `macro_alignment=strong_against` | 0.0370 |
| 6 | `rsi_H1=[30,50)` | 0.0315 |
| 7 | `rsi_M30=[50,65)` | 0.0289 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0287 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0276 |
| 10 | `H1_adx_label=trending` | 0.0264 |
| 11 | `macd_atr_M30=[0,0.3)` | 0.0257 |
| 12 | `bb_pctb_M30=[0.5,0.8)` | 0.0196 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0192 |
| 14 | `rsi_M30=[30,50)` | 0.0190 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0190 |

---

## XAUUSD · ml:full_power · BUY
- Toplam çözülmüş: **332**  ·  Baseline win-rate: **61.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.0%** (23 W / 2 L = 25 trade · +30.6pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d = [-0.5,0)`
   - `macro_alignment = neutral`

**2. Win-rate 84.0%** (21 W / 4 L = 25 trade · +22.6pp vs baseline)
   - `rsi_H1 = [−∞,30)`

**3. Win-rate 76.7%** (33 W / 10 L = 43 trade · +15.3pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (10 W / 20 L = 30 trade · -28.1pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `hour_bucket = 00-04`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0369 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0343 |
| 3 | `macro_alignment=weak_against` | 0.0275 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0274 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0269 |
| 6 | `M30_ema_stack=down` | 0.0217 |
| 7 | `session=overlap` | 0.0214 |
| 8 | `rsi_H1=[−∞,30)` | 0.0179 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0174 |
| 10 | `adx_H1=[35,+∞)` | 0.0174 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0173 |
| 12 | `mtf_trend=all_down` | 0.0170 |
| 13 | `session=asia` | 0.0155 |
| 14 | `adx_M30=[25,35)` | 0.0154 |
| 15 | `M30_adx_label=trending` | 0.0154 |

---

## XAUUSD · ml:full_power · SELL
- Toplam çözülmüş: **157**  ·  Baseline win-rate: **21.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -18.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`

**2. Win-rate 13.0%** (3 W / 20 L = 23 trade · -8.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**3. Win-rate 14.3%** (4 W / 24 L = 28 trade · -7.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`

**4. Win-rate 17.4%** (4 W / 19 L = 23 trade · -4.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow = Thu`

**5. Win-rate 29.0%** (9 W / 22 L = 31 trade · 7.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `adx_M30 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0844 |
| 2 | `adx_H1=[35,+∞)` | 0.0503 |
| 3 | `macro_alignment=weak_pro` | 0.0486 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0432 |
| 5 | `macro_alignment=strong_against` | 0.0376 |
| 6 | `rsi_M30=[50,65)` | 0.0339 |
| 7 | `adx_M30=[25,35)` | 0.0306 |
| 8 | `atr_ratio_M30=[0.7,1)` | 0.0232 |
| 9 | `macd_atr_M30=[0,0.3)` | 0.0226 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0225 |
| 11 | `rsi_H1=[30,50)` | 0.0211 |
| 12 | `bb_pctb_M30=[0.8,+∞)` | 0.0206 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0200 |
| 14 | `H1_adx_label=trending` | 0.0198 |
| 15 | `mtf_trend=all_down` | 0.0191 |

---

## XAUUSD · ml:main · BUY
- Toplam çözülmüş: **332**  ·  Baseline win-rate: **62.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.3%** (28 W / 2 L = 30 trade · +30.6pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 92.3%** (24 W / 2 L = 26 trade · +29.6pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (15 W / 30 L = 45 trade · -29.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0359 |
| 2 | `macro_alignment=weak_against` | 0.0341 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0276 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0275 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0243 |
| 6 | `dxy_chg1d=[-0.5,0)` | 0.0235 |
| 7 | `mtf_trend=all_down` | 0.0224 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0224 |
| 9 | `adx_H1=[25,35)` | 0.0203 |
| 10 | `bb_pctb_M30=[−∞,0.2)` | 0.0199 |
| 11 | `adx_H1=[35,+∞)` | 0.0188 |
| 12 | `rsi_H1=[−∞,30)` | 0.0164 |
| 13 | `M30_ema_stack=down` | 0.0159 |
| 14 | `H1_adx_label=ranging` | 0.0148 |
| 15 | `M30_adx_label=trending` | 0.0138 |

---

## XAUUSD · ml:main · SELL
- Toplam çözülmüş: **159**  ·  Baseline win-rate: **21.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.1%** (1 W / 31 L = 32 trade · -18.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`

**2. Win-rate 12.5%** (3 W / 21 L = 24 trade · -8.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**3. Win-rate 14.3%** (4 W / 24 L = 28 trade · -7.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`

**4. Win-rate 17.4%** (4 W / 19 L = 23 trade · -4.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow = Thu`

**5. Win-rate 29.0%** (9 W / 22 L = 31 trade · 7.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Thu`
   - `adx_M30 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0804 |
| 2 | `adx_H1=[35,+∞)` | 0.0558 |
| 3 | `macro_alignment=weak_pro` | 0.0482 |
| 4 | `macro_alignment=strong_against` | 0.0389 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0360 |
| 6 | `H1_adx_label=trending` | 0.0336 |
| 7 | `adx_M30=[25,35)` | 0.0298 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0282 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0249 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0228 |
| 11 | `macd_atr_M30=[0,0.3)` | 0.0227 |
| 12 | `rsi_H1=[50,65)` | 0.0210 |
| 13 | `bb_pctb_M30=[0.8,+∞)` | 0.0207 |
| 14 | `rsi_M30=[50,65)` | 0.0201 |
| 15 | `us10y_chg1d=[−∞,-0.5)` | 0.0199 |

---

## XAUUSD · ml:main_inv · SELL
- Toplam çözülmüş: **175**  ·  Baseline win-rate: **40.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +36.7pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dist_low_M30 = [0.7,1.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -30.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 = [2,4)`

**2. Win-rate 23.3%** (7 W / 23 L = 30 trade · -17.3pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 ≠ [2,4)`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 31.8%** (7 W / 15 L = 22 trade · -8.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `ml_confidence_bucket = [60,70)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0923 |
| 2 | `adx_M30=[35,+∞)` | 0.0663 |
| 3 | `consec_red_M30=[2,4)` | 0.0512 |
| 4 | `macro_alignment=weak_pro` | 0.0418 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0293 |
| 6 | `H1_adx_label=trending` | 0.0288 |
| 7 | `session=asia` | 0.0273 |
| 8 | `dist_high_M30=[1.5,+∞)` | 0.0266 |
| 9 | `consec_red_M30=[0,2)` | 0.0263 |
| 10 | `adx_H1=[−∞,18)` | 0.0225 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0221 |
| 12 | `dist_low_M30=[0.7,1.5)` | 0.0220 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0200 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0183 |
| 15 | `hour_bucket=08-12` | 0.0183 |

---

## XAUUSD · ml:ultra_safe · BUY
- Toplam çözülmüş: **336**  ·  Baseline win-rate: **61.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.7%** (26 W / 3 L = 29 trade · +27.8pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 84.0%** (21 W / 4 L = 25 trade · +22.1pp vs baseline)
   - `rsi_H1 = [−∞,30)`

**3. Win-rate 79.1%** (34 W / 9 L = 43 trade · +17.2pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0319 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0306 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0304 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0267 |
| 5 | `mtf_trend=all_down` | 0.0252 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0225 |
| 7 | `M30_ema_stack=down` | 0.0216 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0213 |
| 9 | `bb_pctb_M30=[−∞,0.2)` | 0.0200 |
| 10 | `adx_H1=[35,+∞)` | 0.0176 |
| 11 | `rsi_H1=[−∞,30)` | 0.0172 |
| 12 | `dist_low_M30=[0.3,0.7)` | 0.0172 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0166 |
| 14 | `dist_low_M30=[1.5,+∞)` | 0.0164 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0160 |

---

## XAUUSD · ml:ultra_safe · SELL
- Toplam çözülmüş: **155**  ·  Baseline win-rate: **21.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.2%** (1 W / 30 L = 31 trade · -18.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_down`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -16.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_M30 = [50,65)`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 14.3%** (4 W / 24 L = 28 trade · -7.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_down`

**4. Win-rate 28.6%** (8 W / 20 L = 28 trade · 7.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_M30 = [50,65)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**5. Win-rate 29.6%** (8 W / 19 L = 27 trade · 8.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_M30 ≠ [50,65)`
   - `M30_ema_stack = down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0794 |
| 2 | `adx_H1=[35,+∞)` | 0.0433 |
| 3 | `macro_alignment=weak_pro` | 0.0398 |
| 4 | `macro_alignment=strong_against` | 0.0362 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0355 |
| 6 | `adx_M30=[25,35)` | 0.0303 |
| 7 | `rsi_H1=[30,50)` | 0.0267 |
| 8 | `rsi_M30=[50,65)` | 0.0253 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0217 |
| 10 | `bb_pctb_M30=[0.8,+∞)` | 0.0211 |
| 11 | `atr_ratio_M30=[0.7,1)` | 0.0203 |
| 12 | `rsi_M30=[30,50)` | 0.0201 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0184 |
| 14 | `M30_ema_stack=down` | 0.0183 |
| 15 | `rsi_H1=[50,65)` | 0.0175 |

---

## XAUUSD · ml_cross_xau_nasdaq · BUY
- Toplam çözülmüş: **517**  ·  Baseline win-rate: **55.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (68 W / 0 L = 68 trade · +44.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ neutral`

**2. Win-rate 86.0%** (49 W / 8 L = 57 trade · +30.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 85.0%** (17 W / 3 L = 20 trade · +29.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment = neutral`

**4. Win-rate 80.0%** (16 W / 4 L = 20 trade · +24.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket = 00-04`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.4%** (9 W / 58 L = 67 trade · -41.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 00-04`
   - `adx_H1 = [−∞,18)`

**2. Win-rate 31.8%** (7 W / 15 L = 22 trade · -23.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket = 12-16`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 33.3%** (37 W / 74 L = 111 trade · -21.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 12-16`
   - `hour_bucket ≠ 00-04`
   - `adx_H1 ≠ [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1110 |
| 2 | `macro_alignment=weak_against` | 0.0518 |
| 3 | `adx_H1=[35,+∞)` | 0.0476 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0400 |
| 5 | `M30_adx_label=trending` | 0.0393 |
| 6 | `dow=Fri` | 0.0349 |
| 7 | `dow=Mon` | 0.0283 |
| 8 | `M30_adx_label=weak_trend` | 0.0272 |
| 9 | `H1_adx_label=ranging` | 0.0270 |
| 10 | `mtf_trend=NA` | 0.0229 |
| 11 | `adx_H1=[−∞,18)` | 0.0217 |
| 12 | `H1_adx_label=trending` | 0.0210 |
| 13 | `M30_ema_stack=NA` | 0.0200 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0191 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0189 |

---

## XAUUSD · ml_cross_xau_nasdaq · SELL
- Toplam çözülmüş: **282**  ·  Baseline win-rate: **14.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 35 L = 35 trade · -14.5pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**2. Win-rate 0.0%** (0 W / 69 L = 69 trade · -14.5pp vs baseline)
   - `dxy_chg1d = [0.5,+∞)`

**3. Win-rate 8.7%** (2 W / 21 L = 23 trade · -5.8pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `bb_pctb_M30 = [0.2,0.5)`

**4. Win-rate 13.2%** (5 W / 33 L = 38 trade · -1.3pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

**5. Win-rate 14.3%** (3 W / 18 L = 21 trade · -0.2pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `hour_bucket = 04-08`

**6. Win-rate 25.8%** (8 W / 23 L = 31 trade · 11.3pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0.5,+∞)` | 0.1024 |
| 2 | `us10y_chg1d=[−∞,-0.5)` | 0.0517 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0444 |
| 4 | `vix_chg1d=[−∞,-3)` | 0.0350 |
| 5 | `adx_H1=[35,+∞)` | 0.0330 |
| 6 | `dow=Mon` | 0.0294 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0247 |
| 8 | `hour_bucket=00-04` | 0.0243 |
| 9 | `macro_alignment=weak_pro` | 0.0229 |
| 10 | `dow=Thu` | 0.0218 |
| 11 | `near_support=False` | 0.0215 |
| 12 | `near_support=True` | 0.0211 |
| 13 | `atr_ratio_M30=[1,1.3)` | 0.0210 |
| 14 | `adx_M30=[35,+∞)` | 0.0191 |
| 15 | `session=asia` | 0.0190 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · BUY
- Toplam çözülmüş: **145**  ·  Baseline win-rate: **49.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (23 W / 5 L = 28 trade · +33.1pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.2%** (6 W / 27 L = 33 trade · -30.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [0,2)`
   - `ml_confidence_bucket ≠ [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0923 |
| 2 | `adx_M30=[35,+∞)` | 0.0710 |
| 3 | `H1_adx_label=trending` | 0.0560 |
| 4 | `consec_red_M30=[0,2)` | 0.0438 |
| 5 | `dow=Mon` | 0.0432 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0341 |
| 7 | `M30_adx_label=trending` | 0.0326 |
| 8 | `dow=Wed` | 0.0294 |
| 9 | `dist_low_M30=[0.7,1.5)` | 0.0265 |
| 10 | `bb_pctb_M30=[−∞,0.2)` | 0.0263 |
| 11 | `bb_extreme_lower=True` | 0.0250 |
| 12 | `dist_low_M30=[1.5,+∞)` | 0.0247 |
| 13 | `adx_M30=[18,25)` | 0.0214 |
| 14 | `H1_adx_label=weak_trend` | 0.0207 |
| 15 | `bb_pctb_M30=[0.5,0.8)` | 0.0187 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · SELL
- Toplam çözülmüş: **428**  ·  Baseline win-rate: **21.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -21.5pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend ≠ mixed`

**2. Win-rate 3.1%** (1 W / 31 L = 32 trade · -18.4pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -17.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 = NA`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 4.8%** (1 W / 20 L = 21 trade · -16.7pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend = mixed`

**5. Win-rate 6.5%** (2 W / 29 L = 31 trade · -15.0pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 ≠ NA`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [-3,0)`

**6. Win-rate 9.5%** (2 W / 19 L = 21 trade · -12.0pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 = [50,65)`

**7. Win-rate 11.4%** (4 W / 31 L = 35 trade · -10.1pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [3,+∞)`

**8. Win-rate 13.6%** (3 W / 19 L = 22 trade · -7.9pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 ≠ NA`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `hour_bucket = 08-12`

**9. Win-rate 20.0%** (4 W / 16 L = 20 trade · -1.5pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 = NA`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0568 |
| 2 | `adx_M30=[35,+∞)` | 0.0534 |
| 3 | `macro_alignment=weak_pro` | 0.0400 |
| 4 | `M30_adx_label=trending` | 0.0375 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0324 |
| 6 | `hour_bucket=12-16` | 0.0272 |
| 7 | `dow=Mon` | 0.0202 |
| 8 | `mtf_trend=NA` | 0.0195 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0195 |
| 10 | `rsi_H1=[30,50)` | 0.0194 |
| 11 | `dist_high_M30=[1.5,+∞)` | 0.0175 |
| 12 | `H1_adx_label=trending` | 0.0171 |
| 13 | `M30_ema_stack=up` | 0.0168 |
| 14 | `M30_ema_stack=NA` | 0.0166 |
| 15 | `bb_pctb_M30=[0.2,0.5)` | 0.0160 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **1016**  ·  Baseline win-rate: **39.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +61.0pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d = [0,3)`
   - `bb_pctb_M30 ≠ [0.8,+∞)`

**2. Win-rate 100.0%** (26 W / 0 L = 26 trade · +61.0pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d = [0,3)`
   - `bb_pctb_M30 = [0.8,+∞)`

**3. Win-rate 96.9%** (31 W / 1 L = 32 trade · +57.9pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [−∞,0.7)`
   - `bb_pctb_M30 = [0.5,0.8)`

**4. Win-rate 92.2%** (47 W / 4 L = 51 trade · +53.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment ≠ strong_pro`
   - `dow = Fri`

**5. Win-rate 88.0%** (44 W / 6 L = 50 trade · +49.0pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [0,3)`
   - `dow = Wed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.3%** (8 W / 142 L = 150 trade · -33.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `M30_adx_label ≠ trending`
   - `macro_alignment ≠ neutral`

**2. Win-rate 10.1%** (8 W / 71 L = 79 trade · -28.9pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `M30_adx_label = trending`
   - `macro_alignment = strong_pro`

**3. Win-rate 12.5%** (3 W / 21 L = 24 trade · -26.5pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment = strong_pro`

**4. Win-rate 16.7%** (13 W / 65 L = 78 trade · -22.3pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `M30_adx_label ≠ trending`
   - `macro_alignment = neutral`

**5. Win-rate 23.5%** (43 W / 140 L = 183 trade · -15.5pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `rsi_H1 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0602 |
| 2 | `mtf_trend=all_down` | 0.0552 |
| 3 | `M30_ema_stack=down` | 0.0460 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0311 |
| 5 | `dow=Fri` | 0.0271 |
| 6 | `macro_alignment=strong_pro` | 0.0253 |
| 7 | `dow=Mon` | 0.0241 |
| 8 | `rsi_M30=[65,75)` | 0.0225 |
| 9 | `adx_M30=[35,+∞)` | 0.0191 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0189 |
| 11 | `dow=Tue` | 0.0178 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0174 |
| 13 | `adx_H1=[35,+∞)` | 0.0158 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0157 |
| 15 | `H1_adx_label=trending` | 0.0155 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **1996**  ·  Baseline win-rate: **12.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 51 L = 51 trade · -12.1pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 ≠ [4,6)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 0.0%** (0 W / 24 L = 24 trade · -12.1pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [4,6)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**3. Win-rate 0.0%** (0 W / 37 L = 37 trade · -12.1pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [4,6)`
   - `macd_atr_M30 = [-0.3,0)`

**4. Win-rate 0.0%** (0 W / 22 L = 22 trade · -12.1pp vs baseline)
   - `adx_H1 = [18,25)`
   - `oversold ≠ False`
   - `session = overlap`
   - `macd_atr_M30 ≠ [−∞,-0.3)`

**5. Win-rate 0.0%** (0 W / 24 L = 24 trade · -12.1pp vs baseline)
   - `adx_H1 = [18,25)`
   - `oversold ≠ False`
   - `session = overlap`
   - `macd_atr_M30 = [−∞,-0.3)`

**6. Win-rate 0.0%** (0 W / 39 L = 39 trade · -12.1pp vs baseline)
   - `adx_H1 = [18,25)`
   - `oversold = False`
   - `us10y_chg1d = [-0.5,0)`
   - `session = asia`

**7. Win-rate 3.2%** (17 W / 514 L = 531 trade · -8.9pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 = [35,+∞)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `macro_alignment ≠ weak_against`

**8. Win-rate 4.5%** (1 W / 21 L = 22 trade · -7.6pp vs baseline)
   - `adx_H1 = [18,25)`
   - `oversold ≠ False`
   - `session ≠ overlap`

**9. Win-rate 9.5%** (2 W / 19 L = 21 trade · -2.6pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `adx_H1 = [35,+∞)`
   - `us10y_chg1d = [0,0.5)`
   - `macro_alignment ≠ weak_pro`

**10. Win-rate 10.5%** (6 W / 51 L = 57 trade · -1.6pp vs baseline)
   - `adx_H1 = [18,25)`
   - `oversold = False`
   - `us10y_chg1d = [-0.5,0)`
   - `session ≠ asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0424 |
| 2 | `adx_H1=[18,25)` | 0.0406 |
| 3 | `H1_adx_label=weak_trend` | 0.0361 |
| 4 | `adx_H1=[35,+∞)` | 0.0357 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0319 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0240 |
| 7 | `vix_chg1d=[0,3)` | 0.0233 |
| 8 | `adx_M30=[25,35)` | 0.0194 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0194 |
| 10 | `H1_adx_label=trending` | 0.0190 |
| 11 | `rsi_H1=[30,50)` | 0.0174 |
| 12 | `hour_bucket=12-16` | 0.0168 |
| 13 | `macro_alignment=neutral` | 0.0153 |
| 14 | `rsi_M30=[30,50)` | 0.0153 |
| 15 | `rsi_H1=[50,65)` | 0.0151 |

---

## XAUUSD · pulse1_inv · BUY
- Toplam çözülmüş: **563**  ·  Baseline win-rate: **55.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.9%** (173 W / 26 L = 199 trade · +31.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `volatility_regime = normal`
   - `us10y_chg1d ≠ [0,0.5)`
   - `rsi_H1 ≠ [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 12.5%** (4 W / 28 L = 32 trade · -42.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `macro_alignment = weak_pro`

**2. Win-rate 32.1%** (63 W / 133 L = 196 trade · -23.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket ≠ 00-04`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1129 |
| 2 | `adx_H1=[35,+∞)` | 0.0853 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0438 |
| 4 | `M30_adx_label=trending` | 0.0343 |
| 5 | `H1_adx_label=trending` | 0.0343 |
| 6 | `adx_M30=[25,35)` | 0.0303 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0253 |
| 8 | `dist_low_M30=[1.5,+∞)` | 0.0222 |
| 9 | `M30_adx_label=weak_trend` | 0.0212 |
| 10 | `adx_M30=[18,25)` | 0.0208 |
| 11 | `macro_alignment=weak_against` | 0.0203 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0193 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0190 |
| 14 | `H1_adx_label=ranging` | 0.0182 |
| 15 | `adx_H1=[−∞,18)` | 0.0178 |

---

## XAUUSD · pulse1_inv · SELL
- Toplam çözülmüş: **270**  ·  Baseline win-rate: **29.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.8%** (1 W / 25 L = 26 trade · -25.8pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment = weak_pro`

**2. Win-rate 9.5%** (2 W / 19 L = 21 trade · -20.1pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `consec_red_M30 = [2,4)`

**3. Win-rate 18.8%** (9 W / 39 L = 48 trade · -10.8pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `consec_red_M30 ≠ [2,4)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**4. Win-rate 26.1%** (6 W / 17 L = 23 trade · -3.5pp vs baseline)
   - `session = overlap`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `rsi_M30 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.0387 |
| 2 | `session=overlap` | 0.0349 |
| 3 | `rsi_H1=[30,50)` | 0.0302 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0286 |
| 5 | `dist_low_M30=[0.7,1.5)` | 0.0278 |
| 6 | `macro_alignment=weak_pro` | 0.0243 |
| 7 | `atr_ratio_M30=[0.7,1)` | 0.0232 |
| 8 | `H1_adx_label=ranging` | 0.0230 |
| 9 | `consec_red_M30=[2,4)` | 0.0190 |
| 10 | `bb_extreme_upper=True` | 0.0189 |
| 11 | `volatility_regime=normal` | 0.0183 |
| 12 | `M30_adx_label=ranging` | 0.0178 |
| 13 | `hour_bucket=04-08` | 0.0171 |
| 14 | `adx_M30=[18,25)` | 0.0166 |
| 15 | `macro_alignment=neutral` | 0.0165 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **1235**  ·  Baseline win-rate: **37.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.8%** (87 W / 11 L = 98 trade · +50.9pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Fri`
   - `macro_alignment ≠ strong_pro`
   - `M30_ema_stack ≠ down`

**2. Win-rate 76.9%** (20 W / 6 L = 26 trade · +39.0pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 = [18,25)`
   - `dow = Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.3%** (3 W / 67 L = 70 trade · -33.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Fri`
   - `macro_alignment = strong_against`
   - `adx_M30 ≠ [18,25)`

**2. Win-rate 7.9%** (10 W / 117 L = 127 trade · -30.0pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `rsi_M30 = [30,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**3. Win-rate 11.5%** (3 W / 23 L = 26 trade · -26.4pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow = Fri`
   - `macro_alignment = strong_pro`
   - `H1_adx_label ≠ weak_trend`

**4. Win-rate 18.0%** (9 W / 41 L = 50 trade · -19.9pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 = [18,25)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**5. Win-rate 18.7%** (25 W / 109 L = 134 trade · -19.2pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `rsi_M30 ≠ [30,50)`
   - `session ≠ overlap`

**6. Win-rate 25.4%** (34 W / 100 L = 134 trade · -12.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Fri`
   - `macro_alignment ≠ strong_against`
   - `dow = Mon`

**7. Win-rate 25.9%** (7 W / 20 L = 27 trade · -12.0pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `adx_H1 ≠ [18,25)`
   - `rsi_M30 = [30,50)`
   - `us10y_chg1d = [−∞,-0.5)`

**8. Win-rate 31.4%** (11 W / 24 L = 35 trade · -6.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Fri`
   - `macro_alignment = strong_against`
   - `adx_M30 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0519 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0497 |
| 3 | `dow=Fri` | 0.0382 |
| 4 | `dow=Wed` | 0.0347 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0309 |
| 6 | `us10y_chg1d=[-0.5,0)` | 0.0307 |
| 7 | `macro_alignment=strong_against` | 0.0187 |
| 8 | `dow=Mon` | 0.0182 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0175 |
| 10 | `M30_ema_stack=mixed` | 0.0172 |
| 11 | `macro_alignment=weak_pro` | 0.0169 |
| 12 | `adx_H1=[−∞,18)` | 0.0166 |
| 13 | `dow=Thu` | 0.0160 |
| 14 | `M30_ema_stack=down` | 0.0155 |
| 15 | `rsi_M30=[65,75)` | 0.0154 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **1447**  ·  Baseline win-rate: **12.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 58 L = 58 trade · -12.4pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 0.0%** (0 W / 110 L = 110 trade · -12.4pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [3,+∞)`

**3. Win-rate 0.0%** (0 W / 271 L = 271 trade · -12.4pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Mon`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `M30_ema_stack ≠ up`

**4. Win-rate 0.0%** (0 W / 70 L = 70 trade · -12.4pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`
   - `sar_bearish ≠ False`

**5. Win-rate 1.4%** (1 W / 71 L = 72 trade · -11.0pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Mon`
   - `dist_low_M30 = [0.7,1.5)`
   - `rsi_H1 ≠ [−∞,30)`

**6. Win-rate 4.3%** (1 W / 22 L = 23 trade · -8.1pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Fri`
   - `vix_chg1d = [3,+∞)`

**7. Win-rate 5.3%** (6 W / 107 L = 113 trade · -7.1pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `M30_ema_stack = NA`

**8. Win-rate 7.4%** (2 W / 25 L = 27 trade · -5.0pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Mon`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `M30_ema_stack = up`

**9. Win-rate 10.9%** (5 W / 41 L = 46 trade · -1.5pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `dow = Mon`
   - `vix_chg1d = [3,+∞)`
   - `sar_bearish = False`

**10. Win-rate 14.3%** (4 W / 24 L = 28 trade · 1.9pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0616 |
| 2 | `H1_adx_label=trending` | 0.0429 |
| 3 | `adx_M30=[35,+∞)` | 0.0387 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0367 |
| 5 | `macro_alignment=strong_against` | 0.0314 |
| 6 | `H1_adx_label=weak_trend` | 0.0278 |
| 7 | `us10y_chg1d=[0,0.5)` | 0.0239 |
| 8 | `dow=Tue` | 0.0195 |
| 9 | `us10y_chg1d=[−∞,-0.5)` | 0.0190 |
| 10 | `rsi_H1=[30,50)` | 0.0183 |
| 11 | `vix_chg1d=[−∞,-3)` | 0.0179 |
| 12 | `adx_H1=[18,25)` | 0.0177 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0171 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0171 |
| 15 | `dow=Fri` | 0.0160 |

---

## XAUUSD · pulse2_inv · BUY
- Toplam çözülmüş: **398**  ·  Baseline win-rate: **62.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (36 W / 0 L = 36 trade · +37.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 = [1,1.3)`
   - `sar_bearish ≠ False`

**2. Win-rate 93.8%** (45 W / 3 L = 48 trade · +31.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macro_alignment = weak_against`

**3. Win-rate 93.8%** (30 W / 2 L = 32 trade · +31.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `atr_ratio_M30 = [1,1.3)`
   - `sar_bearish = False`

**4. Win-rate 76.2%** (16 W / 5 L = 21 trade · +13.6pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.2%** (26 W / 77 L = 103 trade · -37.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `consec_red_M30 = [0,2)`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1211 |
| 2 | `adx_H1=[35,+∞)` | 0.0670 |
| 3 | `adx_M30=[25,35)` | 0.0508 |
| 4 | `M30_adx_label=trending` | 0.0499 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0445 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0390 |
| 7 | `dist_high_M30=[1.5,+∞)` | 0.0354 |
| 8 | `M30_adx_label=weak_trend` | 0.0349 |
| 9 | `adx_M30=[18,25)` | 0.0261 |
| 10 | `macro_alignment=weak_against` | 0.0249 |
| 11 | `consec_red_M30=[0,2)` | 0.0214 |
| 12 | `mtf_trend=all_down` | 0.0206 |
| 13 | `H1_adx_label=trending` | 0.0202 |
| 14 | `M30_ema_stack=down` | 0.0191 |
| 15 | `adx_H1=[25,35)` | 0.0184 |

---

## XAUUSD · pulse2_inv · SELL
- Toplam çözülmüş: **408**  ·  Baseline win-rate: **26.5%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -26.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 10.0%** (4 W / 36 L = 40 trade · -16.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session = asia`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `macd_atr_M30 ≠ [0,0.3)`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -16.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment = weak_pro`

**4. Win-rate 10.7%** (3 W / 25 L = 28 trade · -15.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d = [3,+∞)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -6.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment ≠ weak_pro`

**6. Win-rate 20.6%** (7 W / 27 L = 34 trade · -5.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session ≠ asia`
   - `session = us`

**7. Win-rate 28.6%** (8 W / 20 L = 28 trade · 2.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `vix_chg1d ≠ [3,+∞)`

**8. Win-rate 29.9%** (20 W / 47 L = 67 trade · 3.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session ≠ asia`
   - `session ≠ us`
   - `atr_ratio_M30 = [0.7,1)`

**9. Win-rate 32.0%** (8 W / 17 L = 25 trade · 5.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session = asia`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `macd_atr_M30 = [0,0.3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0488 |
| 2 | `macro_alignment=weak_pro` | 0.0396 |
| 3 | `rsi_H1=[30,50)` | 0.0285 |
| 4 | `session=europe` | 0.0231 |
| 5 | `adx_M30=[25,35)` | 0.0221 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0218 |
| 7 | `hour_bucket=12-16` | 0.0207 |
| 8 | `adx_H1=[35,+∞)` | 0.0203 |
| 9 | `us10y_chg1d=[−∞,-0.5)` | 0.0198 |
| 10 | `session=asia` | 0.0190 |
| 11 | `dist_high_M30=[1.5,+∞)` | 0.0185 |
| 12 | `sar_bearish=True` | 0.0172 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0162 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0160 |
| 15 | `macd_atr_M30=[-0.3,0)` | 0.0159 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **1156**  ·  Baseline win-rate: **46.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.0%** (120 W / 5 L = 125 trade · +49.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Wed`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 73 L = 73 trade · -46.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 2.9%** (1 W / 33 L = 34 trade · -43.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**3. Win-rate 7.9%** (3 W / 35 L = 38 trade · -38.6pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 = [−∞,0.2)`

**4. Win-rate 13.0%** (12 W / 80 L = 92 trade · -33.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `M30_ema_stack ≠ up`
   - `ml_confidence_bucket ≠ [70,80)`

**5. Win-rate 24.0%** (6 W / 19 L = 25 trade · -22.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `M30_ema_stack = up`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 25.9%** (7 W / 20 L = 27 trade · -20.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow = Wed`

**7. Win-rate 26.7%** (8 W / 22 L = 30 trade · -19.8pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d = [−∞,-0.5)`

**8. Win-rate 33.3%** (11 W / 22 L = 33 trade · -13.2pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.1083 |
| 2 | `dow=Fri` | 0.0498 |
| 3 | `vix_chg1d=[−∞,-3)` | 0.0449 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0426 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0400 |
| 6 | `dow=Wed` | 0.0292 |
| 7 | `adx_H1=[35,+∞)` | 0.0220 |
| 8 | `ml_confidence_bucket=[−∞,50)` | 0.0212 |
| 9 | `M30_ema_stack=up` | 0.0193 |
| 10 | `adx_M30=[35,+∞)` | 0.0192 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0156 |
| 12 | `rsi_M30=[65,75)` | 0.0152 |
| 13 | `vix_chg1d=[-3,0)` | 0.0146 |
| 14 | `sar_bearish=False` | 0.0142 |
| 15 | `H1_adx_label=trending` | 0.0140 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **1708**  ·  Baseline win-rate: **11.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 239 L = 239 trade · -11.3pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Tue`
   - `rsi_M30 ≠ [50,65)`

**2. Win-rate 0.0%** (0 W / 41 L = 41 trade · -11.3pp vs baseline)
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**3. Win-rate 1.4%** (4 W / 291 L = 295 trade · -9.9pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_pro`
   - `session ≠ us`

**4. Win-rate 3.1%** (1 W / 31 L = 32 trade · -8.2pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Tue`
   - `rsi_M30 = [50,65)`

**5. Win-rate 4.0%** (1 W / 24 L = 25 trade · -7.3pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Tue`
   - `consec_red_M30 ≠ [0,2)`

**6. Win-rate 5.0%** (1 W / 19 L = 20 trade · -6.3pp vs baseline)
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `atr_ratio_M30 = [1,1.3)`

**7. Win-rate 5.3%** (8 W / 144 L = 152 trade · -6.0pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_pro`
   - `oversold ≠ False`

**8. Win-rate 8.3%** (8 W / 88 L = 96 trade · -3.0pp vs baseline)
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `dist_high_M30 = [1.5,+∞)`
   - `session = asia`

**9. Win-rate 11.8%** (11 W / 82 L = 93 trade · 0.5pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_pro`
   - `session = us`

**10. Win-rate 14.3%** (4 W / 24 L = 28 trade · 3.0pp vs baseline)
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Tue`
   - `consec_red_M30 = [0,2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0390 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0386 |
| 3 | `adx_H1=[35,+∞)` | 0.0326 |
| 4 | `dow=Thu` | 0.0261 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0250 |
| 6 | `H1_adx_label=weak_trend` | 0.0239 |
| 7 | `macro_alignment=strong_against` | 0.0235 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0224 |
| 9 | `H1_adx_label=trending` | 0.0216 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0194 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0191 |
| 12 | `sar_bearish=False` | 0.0165 |
| 13 | `adx_H1=[18,25)` | 0.0161 |
| 14 | `session=asia` | 0.0160 |
| 15 | `rsi_H1=[30,50)` | 0.0151 |

---

## XAUUSD · pulse3_inv · BUY
- Toplam çözülmüş: **382**  ·  Baseline win-rate: **60.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (54 W / 0 L = 54 trade · +39.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 85.5%** (53 W / 9 L = 62 trade · +25.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 = [1.5,+∞)`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +18.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_support ≠ False`
   - `macro_alignment = weak_against`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.5%** (19 W / 62 L = 81 trade · -36.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_support = False`
   - `adx_M30 ≠ [−∞,18)`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1370 |
| 2 | `adx_H1=[35,+∞)` | 0.0683 |
| 3 | `M30_adx_label=weak_trend` | 0.0402 |
| 4 | `adx_M30=[25,35)` | 0.0375 |
| 5 | `adx_M30=[18,25)` | 0.0351 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0341 |
| 7 | `M30_adx_label=trending` | 0.0282 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0268 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0267 |
| 10 | `mtf_trend=all_down` | 0.0259 |
| 11 | `M30_ema_stack=down` | 0.0224 |
| 12 | `adx_H1=[25,35)` | 0.0205 |
| 13 | `H1_adx_label=trending` | 0.0193 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0176 |
| 15 | `macro_alignment=weak_against` | 0.0171 |

---

## XAUUSD · pulse3_inv · SELL
- Toplam çözülmüş: **378**  ·  Baseline win-rate: **22.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 27 L = 27 trade · -22.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 0.0%** (0 W / 30 L = 30 trade · -22.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 = [50,65)`
   - `session ≠ europe`

**3. Win-rate 0.0%** (0 W / 20 L = 20 trade · -22.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 = [50,65)`
   - `session = europe`

**4. Win-rate 11.4%** (4 W / 31 L = 35 trade · -10.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 ≠ [50,65)`

**5. Win-rate 14.7%** (5 W / 29 L = 34 trade · -7.5pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**6. Win-rate 15.4%** (4 W / 22 L = 26 trade · -6.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

**7. Win-rate 16.0%** (4 W / 21 L = 25 trade · -6.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket = 20-24`

**8. Win-rate 31.4%** (38 W / 83 L = 121 trade · 9.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `hour_bucket ≠ 20-24`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0800 |
| 2 | `dist_high_M30=[1.5,+∞)` | 0.0336 |
| 3 | `rsi_H1=[50,65)` | 0.0268 |
| 4 | `macro_alignment=weak_pro` | 0.0256 |
| 5 | `M30_ema_stack=mixed` | 0.0237 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0236 |
| 7 | `M30_adx_label=trending` | 0.0231 |
| 8 | `volatility_regime=normal` | 0.0228 |
| 9 | `macro_alignment=strong_pro` | 0.0223 |
| 10 | `adx_H1=[35,+∞)` | 0.0205 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0203 |
| 12 | `H1_adx_label=trending` | 0.0202 |
| 13 | `dist_high_M30=[0.7,1.5)` | 0.0201 |
| 14 | `dow=Mon` | 0.0197 |
| 15 | `adx_M30=[25,35)` | 0.0177 |

---

## XAUUSD · smc · BUY
- Toplam çözülmüş: **268**  ·  Baseline win-rate: **70.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (56 W / 0 L = 56 trade · +29.1pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`
   - `dow ≠ Tue`

**2. Win-rate 96.2%** (25 W / 1 L = 26 trade · +25.3pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `vix_chg1d ≠ [3,+∞)`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +24.3pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend = all_down`
   - `dow = Tue`

**4. Win-rate 88.9%** (32 W / 4 L = 36 trade · +18.0pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `mtf_trend ≠ all_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.6%** (5 W / 27 L = 32 trade · -55.3pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `adx_H1 ≠ [18,25)`
   - `dist_low_M30 ≠ [0.7,1.5)`

**2. Win-rate 31.8%** (7 W / 15 L = 22 trade · -39.1pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `adx_H1 = [18,25)`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.1373 |
| 2 | `M30_ema_stack=down` | 0.0812 |
| 3 | `mtf_trend=all_down` | 0.0807 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0414 |
| 5 | `session=asia` | 0.0352 |
| 6 | `mtf_trend=all_up` | 0.0277 |
| 7 | `M30_ema_stack=up` | 0.0271 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0251 |
| 9 | `H1_adx_label=weak_trend` | 0.0214 |
| 10 | `macro_alignment=strong_pro` | 0.0207 |
| 11 | `adx_H1=[18,25)` | 0.0186 |
| 12 | `adx_M30=[−∞,18)` | 0.0169 |
| 13 | `M30_adx_label=ranging` | 0.0164 |
| 14 | `hour_bucket=20-24` | 0.0159 |
| 15 | `vix_chg1d=[-3,0)` | 0.0151 |

---

## XAUUSD · smc · SELL
- Toplam çözülmüş: **327**  ·  Baseline win-rate: **27.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 88.5%** (23 W / 3 L = 26 trade · +60.7pp vs baseline)
   - `dow = Fri`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -27.8pp vs baseline)
   - `dow ≠ Fri`
   - `macro_alignment = weak_pro`
   - `M30_adx_label ≠ trending`

**2. Win-rate 5.7%** (5 W / 82 L = 87 trade · -22.1pp vs baseline)
   - `dow ≠ Fri`
   - `macro_alignment ≠ weak_pro`
   - `dxy_chg1d = [-0.5,0)`
   - `macro_alignment ≠ strong_against`

**3. Win-rate 7.7%** (2 W / 24 L = 26 trade · -20.1pp vs baseline)
   - `dow ≠ Fri`
   - `macro_alignment ≠ weak_pro`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 12.9%** (4 W / 27 L = 31 trade · -14.9pp vs baseline)
   - `dow ≠ Fri`
   - `macro_alignment = weak_pro`
   - `M30_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[-0.5,0)` | 0.0568 |
| 2 | `dxy_chg1d=[0,0.5)` | 0.0527 |
| 3 | `dow=Fri` | 0.0450 |
| 4 | `macro_alignment=strong_pro` | 0.0412 |
| 5 | `adx_M30=[35,+∞)` | 0.0379 |
| 6 | `bb_pctb_M30=[0.2,0.5)` | 0.0374 |
| 7 | `macd_atr_M30=[-0.3,0)` | 0.0284 |
| 8 | `us10y_chg1d=[0,0.5)` | 0.0276 |
| 9 | `macro_alignment=weak_pro` | 0.0274 |
| 10 | `H1_adx_label=ranging` | 0.0253 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0220 |
| 12 | `adx_H1=[−∞,18)` | 0.0215 |
| 13 | `H1_adx_label=trending` | 0.0202 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0194 |
| 15 | `mtf_trend=all_down` | 0.0183 |

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
