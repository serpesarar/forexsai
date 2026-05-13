# Pattern Mining Raporu
_2026-05-08T02:14:54.732200Z — son 7 gün — 8934 resolved sinyal_

**Yöntem:** Decision Tree (max_depth=4) + Random Forest feature importance.
Her leaf bir kural. min_samples_leaf=20, class_weight=balanced.

**Yorum kılavuzu:**
- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)
- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)
- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli

---

## GLOBAL — tüm sembol & model
- Toplam çözülmüş: **8934**  ·  Baseline win-rate: **79.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.3%** (2771 W / 49 L = 2820 trade · +18.7pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 ≠ NA`
   - `rsi_H1 ≠ [65,75)`
   - `session ≠ asia`

**2. Win-rate 96.3%** (1519 W / 59 L = 1578 trade · +16.7pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 ≠ NA`
   - `rsi_H1 ≠ [65,75)`
   - `session = asia`

**3. Win-rate 95.8%** (412 W / 18 L = 430 trade · +16.2pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 = NA`
   - `rsi_H1 ≠ [65,75)`
   - `sar_bearish ≠ False`

**4. Win-rate 87.1%** (176 W / 26 L = 202 trade · +7.5pp vs baseline)
   - `H4_ema_stack = NA`
   - `rsi_M30 = NA`
   - `near_resistance = False`
   - `session_phase = mid_session`

**5. Win-rate 84.2%** (112 W / 21 L = 133 trade · +4.6pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 = NA`
   - `rsi_H1 = [65,75)`
   - `vix_chg1d = [−∞,-3)`

**6. Win-rate 76.2%** (16 W / 5 L = 21 trade · -3.4pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 ≠ NA`
   - `rsi_H1 = [65,75)`

**7. Win-rate 75.9%** (22 W / 7 L = 29 trade · -3.7pp vs baseline)
   - `H4_ema_stack = NA`
   - `rsi_M30 ≠ NA`
   - `M30_ema_stack = mixed`
   - `dow = Sun`

**8. Win-rate 75.3%** (259 W / 85 L = 344 trade · -4.3pp vs baseline)
   - `H4_ema_stack ≠ NA`
   - `consec_red_M30 = NA`
   - `rsi_H1 ≠ [65,75)`
   - `sar_bearish = False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.0%** (3 W / 17 L = 20 trade · -64.6pp vs baseline)
   - `H4_ema_stack = NA`
   - `rsi_M30 = NA`
   - `near_resistance ≠ False`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 27.1%** (13 W / 35 L = 48 trade · -52.5pp vs baseline)
   - `H4_ema_stack = NA`
   - `rsi_M30 = NA`
   - `near_resistance ≠ False`
   - `ml_confidence_bucket ≠ [80,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=NA` | 0.0915 |
| 2 | `session_phase=any` | 0.0647 |
| 3 | `rsi_H4=NA` | 0.0634 |
| 4 | `H4_adx_label=NA` | 0.0577 |
| 5 | `adx_H4=NA` | 0.0568 |
| 6 | `H1_ema_stack=NA` | 0.0518 |
| 7 | `rsi_H4=[30,50)` | 0.0420 |
| 8 | `session_phase=off_hours` | 0.0383 |
| 9 | `H4_ema_stack=up` | 0.0285 |
| 10 | `M30_ema_stack=NA` | 0.0151 |
| 11 | `bb_pctb_M30=NA` | 0.0148 |
| 12 | `dist_low_M30=NA` | 0.0147 |
| 13 | `H4_adx_label=weak_trend` | 0.0144 |
| 14 | `adx_M30=NA` | 0.0140 |
| 15 | `H1_ema_stack=down` | 0.0137 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **83.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +16.7pp vs baseline)
   - `sar_bearish = True`
   - `volatility_regime = high`

**2. Win-rate 86.4%** (19 W / 3 L = 22 trade · +3.1pp vs baseline)
   - `sar_bearish = True`
   - `volatility_regime ≠ high`

**3. Win-rate 80.0%** (16 W / 4 L = 20 trade · -3.3pp vs baseline)
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket ≠ [−∞,50)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0836 |
| 2 | `sar_bearish=False` | 0.0672 |
| 3 | `rsi_H1=[50,65)` | 0.0404 |
| 4 | `H1_ema_stack=mixed` | 0.0361 |
| 5 | `H4_adx_label=trending` | 0.0360 |
| 6 | `volatility_regime=high` | 0.0353 |
| 7 | `H4_adx_label=weak_trend` | 0.0333 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0327 |
| 9 | `adx_H4=[18,25)` | 0.0314 |
| 10 | `hour_bucket=08-12` | 0.0312 |
| 11 | `rsi_extreme=True` | 0.0283 |
| 12 | `H1_ema_stack=up` | 0.0270 |
| 13 | `regime_label=transition` | 0.0266 |
| 14 | `session=europe` | 0.0257 |
| 15 | `adx_H4=[25,35)` | 0.0257 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **246**  ·  Baseline win-rate: **76.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (26 W / 0 L = 26 trade · +23.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 90.6%** (29 W / 3 L = 32 trade · +14.2pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dxy_chg1d = [0,0.5)`
   - `ml_confidence_bucket ≠ [50,60)`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · +14.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `dow = Tue`

**4. Win-rate 85.7%** (30 W / 5 L = 35 trade · +9.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish = True`

**5. Win-rate 81.0%** (17 W / 4 L = 21 trade · +4.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d = [-3,0)`

**6. Win-rate 79.2%** (19 W / 5 L = 24 trade · +2.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `dow ≠ Tue`
   - `sar_bearish = False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 29.2%** (7 W / 17 L = 24 trade · -47.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `sar_bearish ≠ True`
   - `dxy_chg1d = [0,0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0706 |
| 2 | `sar_bearish=True` | 0.0585 |
| 3 | `volatility_regime=high` | 0.0463 |
| 4 | `near_resistance=False` | 0.0374 |
| 5 | `sar_bearish=False` | 0.0373 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0343 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0339 |
| 8 | `volatility_regime=normal` | 0.0329 |
| 9 | `near_resistance=True` | 0.0327 |
| 10 | `session=europe` | 0.0311 |
| 11 | `session=overlap` | 0.0285 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0249 |
| 13 | `H1_ema_stack=mixed` | 0.0246 |
| 14 | `macro_alignment=strong_pro` | 0.0229 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0221 |

---

## GDAXI.INDX · pulse2
- Toplam çözülmüş: **133**  ·  Baseline win-rate: **85.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (46 W / 0 L = 46 trade · +14.3pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**2. Win-rate 88.6%** (31 W / 4 L = 35 trade · +2.9pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 87.5%** (21 W / 3 L = 24 trade · +1.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [50,65)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1246 |
| 2 | `sar_bearish=True` | 0.1025 |
| 3 | `rsi_H1=[30,50)` | 0.0773 |
| 4 | `macro_alignment=strong_against` | 0.0473 |
| 5 | `rsi_H1=[65,75)` | 0.0431 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0401 |
| 7 | `volatility_regime=high` | 0.0304 |
| 8 | `volatility_regime=normal` | 0.0270 |
| 9 | `session=overlap` | 0.0266 |
| 10 | `H1_ema_stack=up` | 0.0229 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0229 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0211 |
| 13 | `session=europe` | 0.0210 |
| 14 | `hour_bucket=08-12` | 0.0197 |
| 15 | `vix_chg1d=[0,3)` | 0.0189 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **300**  ·  Baseline win-rate: **83.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (76 W / 0 L = 76 trade · +16.3pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 ≠ [65,75)`
   - `ml_confidence_bucket ≠ [60,70)`

**2. Win-rate 96.2%** (25 W / 1 L = 26 trade · +12.5pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 ≠ [65,75)`
   - `ml_confidence_bucket = [60,70)`
   - `macro_alignment = strong_against`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · +6.8pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 ≠ [65,75)`
   - `ml_confidence_bucket = [60,70)`
   - `macro_alignment ≠ strong_against`

**4. Win-rate 90.4%** (47 W / 5 L = 52 trade · +6.7pp vs baseline)
   - `sar_bearish ≠ True`
   - `near_resistance ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d ≠ [−∞,-3)`

**5. Win-rate 81.1%** (30 W / 7 L = 37 trade · -2.6pp vs baseline)
   - `sar_bearish = True`
   - `rsi_H1 = [65,75)`

**6. Win-rate 76.7%** (23 W / 7 L = 30 trade · -7.0pp vs baseline)
   - `sar_bearish ≠ True`
   - `near_resistance ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d = [−∞,-3)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0831 |
| 2 | `sar_bearish=True` | 0.0775 |
| 3 | `near_resistance=True` | 0.0571 |
| 4 | `near_resistance=False` | 0.0468 |
| 5 | `H1_ema_stack=mixed` | 0.0398 |
| 6 | `rsi_H1=[65,75)` | 0.0390 |
| 7 | `H1_ema_stack=up` | 0.0303 |
| 8 | `macro_alignment=strong_against` | 0.0284 |
| 9 | `rsi_H1=[30,50)` | 0.0267 |
| 10 | `rsi_H1=[50,65)` | 0.0254 |
| 11 | `volatility_regime=normal` | 0.0231 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0211 |
| 13 | `adx_H4=[25,35)` | 0.0199 |
| 14 | `H4_adx_label=weak_trend` | 0.0185 |
| 15 | `ml_confidence_bucket=[70,80)` | 0.0183 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.6%** (29 W / 3 L = 32 trade · +18.7pp vs baseline)
   - `volatility_regime = high`
   - `rsi_H1 ≠ [65,75)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0678 |
| 2 | `volatility_regime=normal` | 0.0574 |
| 3 | `rsi_H4=[65,75)` | 0.0556 |
| 4 | `sar_bearish=True` | 0.0425 |
| 5 | `sar_bearish=False` | 0.0425 |
| 6 | `session=us` | 0.0396 |
| 7 | `mtf_trend=all_up` | 0.0392 |
| 8 | `volatility_regime=high` | 0.0373 |
| 9 | `rsi_H1=[65,75)` | 0.0303 |
| 10 | `vix_chg1d=[-3,0)` | 0.0299 |
| 11 | `adx_H4=[35,+∞)` | 0.0291 |
| 12 | `rsi_H1=[30,50)` | 0.0271 |
| 13 | `regime_label=strong_trend_up` | 0.0250 |
| 14 | `rsi_H4=[75,+∞)` | 0.0248 |
| 15 | `dow=Thu` | 0.0239 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **233**  ·  Baseline win-rate: **56.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.5%** (32 W / 5 L = 37 trade · +30.3pp vs baseline)
   - `near_resistance = False`
   - `rsi_H4 = [65,75)`
   - `session_phase = open_drive`

**2. Win-rate 80.0%** (16 W / 4 L = 20 trade · +23.8pp vs baseline)
   - `near_resistance = False`
   - `rsi_H4 = [65,75)`
   - `session_phase ≠ open_drive`
   - `ml_confidence_bucket = [50,60)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (3 W / 18 L = 21 trade · -41.9pp vs baseline)
   - `near_resistance ≠ False`
   - `vix_chg1d ≠ [-3,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `near_resistance=False` | 0.0947 |
| 2 | `near_resistance=True` | 0.0687 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0494 |
| 4 | `rsi_H4=[65,75)` | 0.0377 |
| 5 | `session=overlap` | 0.0367 |
| 6 | `session=us` | 0.0332 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0324 |
| 8 | `dow=Wed` | 0.0238 |
| 9 | `H1_adx_label=weak_trend` | 0.0233 |
| 10 | `adx_H4=[25,35)` | 0.0231 |
| 11 | `session_phase=mid_session` | 0.0211 |
| 12 | `macro_alignment=weak_pro` | 0.0198 |
| 13 | `rsi_H4=[75,+∞)` | 0.0198 |
| 14 | `macro_alignment=strong_pro` | 0.0196 |
| 15 | `us10y_chg1d=[-0.5,0)` | 0.0184 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **163**  ·  Baseline win-rate: **65.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.9%** (37 W / 2 L = 39 trade · +29.9pp vs baseline)
   - `near_resistance = False`
   - `rsi_H4 ≠ [75,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `adx_H1 ≠ [25,35)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -41.2pp vs baseline)
   - `near_resistance ≠ False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0644 |
| 2 | `dow=Thu` | 0.0585 |
| 3 | `near_resistance=True` | 0.0521 |
| 4 | `near_resistance=False` | 0.0411 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0398 |
| 6 | `sar_bearish=False` | 0.0372 |
| 7 | `session=overlap` | 0.0336 |
| 8 | `H4_ema_stack=NA` | 0.0294 |
| 9 | `adx_H4=[25,35)` | 0.0269 |
| 10 | `volatility_regime=high` | 0.0263 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0257 |
| 12 | `sar_bearish=True` | 0.0257 |
| 13 | `rsi_H4=[65,75)` | 0.0246 |
| 14 | `rsi_H4=[75,+∞)` | 0.0240 |
| 15 | `volatility_regime=normal` | 0.0202 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **265**  ·  Baseline win-rate: **68.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (33 W / 0 L = 33 trade · +31.7pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ strong_against`
   - `session_phase = mid_session`

**2. Win-rate 86.0%** (37 W / 6 L = 43 trade · +17.7pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ strong_against`
   - `session_phase ≠ mid_session`

**3. Win-rate 83.3%** (35 W / 7 L = 42 trade · +15.0pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 = [65,75)`
   - `dow ≠ Wed`
   - `session ≠ us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 28.6%** (6 W / 15 L = 21 trade · -39.7pp vs baseline)
   - `near_resistance ≠ False`
   - `hour_bucket = 16-20`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `near_resistance=False` | 0.0695 |
| 2 | `near_resistance=True` | 0.0663 |
| 3 | `sar_bearish=False` | 0.0619 |
| 4 | `sar_bearish=True` | 0.0469 |
| 5 | `rsi_H4=[75,+∞)` | 0.0313 |
| 6 | `macro_alignment=weak_pro` | 0.0307 |
| 7 | `rsi_H1=[30,50)` | 0.0293 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0253 |
| 9 | `session=overlap` | 0.0243 |
| 10 | `session=us` | 0.0239 |
| 11 | `volatility_regime=normal` | 0.0237 |
| 12 | `adx_H4=[25,35)` | 0.0231 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0230 |
| 14 | `dow=Thu` | 0.0211 |
| 15 | `ml_confidence_bucket=[70,80)` | 0.0210 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **290**  ·  Baseline win-rate: **97.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +2.1pp vs baseline)
   - `volatility_regime ≠ normal`
   - `H4_adx_label = weak_trend`

**2. Win-rate 100.0%** (141 W / 0 L = 141 trade · +2.1pp vs baseline)
   - `volatility_regime = normal`
   - `session ≠ asia`
   - `H1_adx_label ≠ ranging`

**3. Win-rate 100.0%** (23 W / 0 L = 23 trade · +2.1pp vs baseline)
   - `volatility_regime = normal`
   - `session ≠ asia`
   - `H1_adx_label = ranging`

**4. Win-rate 100.0%** (34 W / 0 L = 34 trade · +2.1pp vs baseline)
   - `volatility_regime = normal`
   - `session = asia`
   - `adx_H1 = [18,25)`

**5. Win-rate 94.3%** (33 W / 2 L = 35 trade · -3.6pp vs baseline)
   - `volatility_regime = normal`
   - `session = asia`
   - `adx_H1 ≠ [18,25)`

**6. Win-rate 88.6%** (31 W / 4 L = 35 trade · -9.3pp vs baseline)
   - `volatility_regime ≠ normal`
   - `H4_adx_label ≠ weak_trend`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `volatility_regime=normal` | 0.0540 |
| 2 | `session=asia` | 0.0405 |
| 3 | `hour_bucket=04-08` | 0.0354 |
| 4 | `volatility_regime=low` | 0.0268 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0238 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0197 |
| 7 | `macd_atr_M30=[0,0.3)` | 0.0196 |
| 8 | `macro_alignment=strong_against` | 0.0195 |
| 9 | `ml_confidence_bucket=[50,60)` | 0.0188 |
| 10 | `adx_M30=[25,35)` | 0.0186 |
| 11 | `vix_chg1d=[−∞,-3)` | 0.0178 |
| 12 | `atr_ratio_M30=[−∞,0.7)` | 0.0175 |
| 13 | `H4_ema_stack=mixed` | 0.0175 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0174 |
| 15 | `macro_alignment=neutral` | 0.0171 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **170**  ·  Baseline win-rate: **98.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (110 W / 0 L = 110 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (39 W / 0 L = 39 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · -8.3pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label = weak_trend`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0621 |
| 2 | `session=asia` | 0.0573 |
| 3 | `H4_adx_label=trending` | 0.0549 |
| 4 | `bb_pctb_M30=[0.5,0.8)` | 0.0529 |
| 5 | `hour_bucket=04-08` | 0.0443 |
| 6 | `mtf_trend=mixed` | 0.0426 |
| 7 | `H1_adx_label=weak_trend` | 0.0415 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0364 |
| 9 | `adx_H1=[18,25)` | 0.0331 |
| 10 | `M30_adx_label=weak_trend` | 0.0329 |
| 11 | `adx_H4=[18,25)` | 0.0326 |
| 12 | `dow=Tue` | 0.0323 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0263 |
| 15 | `macro_alignment=strong_against` | 0.0236 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **170**  ·  Baseline win-rate: **98.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (110 W / 0 L = 110 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (39 W / 0 L = 39 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · -8.3pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label = weak_trend`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0621 |
| 2 | `session=asia` | 0.0573 |
| 3 | `H4_adx_label=trending` | 0.0549 |
| 4 | `bb_pctb_M30=[0.5,0.8)` | 0.0529 |
| 5 | `hour_bucket=04-08` | 0.0443 |
| 6 | `mtf_trend=mixed` | 0.0426 |
| 7 | `H1_adx_label=weak_trend` | 0.0415 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0364 |
| 9 | `adx_H1=[18,25)` | 0.0331 |
| 10 | `M30_adx_label=weak_trend` | 0.0329 |
| 11 | `adx_H4=[18,25)` | 0.0326 |
| 12 | `dow=Tue` | 0.0323 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0263 |
| 15 | `macro_alignment=strong_against` | 0.0236 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **170**  ·  Baseline win-rate: **98.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (110 W / 0 L = 110 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (39 W / 0 L = 39 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · -8.3pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label = weak_trend`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0621 |
| 2 | `session=asia` | 0.0573 |
| 3 | `H4_adx_label=trending` | 0.0549 |
| 4 | `bb_pctb_M30=[0.5,0.8)` | 0.0529 |
| 5 | `hour_bucket=04-08` | 0.0443 |
| 6 | `mtf_trend=mixed` | 0.0426 |
| 7 | `H1_adx_label=weak_trend` | 0.0415 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0364 |
| 9 | `adx_H1=[18,25)` | 0.0331 |
| 10 | `M30_adx_label=weak_trend` | 0.0329 |
| 11 | `adx_H4=[18,25)` | 0.0326 |
| 12 | `dow=Tue` | 0.0323 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0263 |
| 15 | `macro_alignment=strong_against` | 0.0236 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **170**  ·  Baseline win-rate: **98.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (108 W / 0 L = 108 trade · +1.8pp vs baseline)
   - `session ≠ asia`

**2. Win-rate 100.0%** (33 W / 0 L = 33 trade · +1.8pp vs baseline)
   - `session = asia`
   - `H4_adx_label = trending`

**3. Win-rate 89.7%** (26 W / 3 L = 29 trade · -8.5pp vs baseline)
   - `session = asia`
   - `H4_adx_label ≠ trending`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0879 |
| 2 | `H4_adx_label=weak_trend` | 0.0692 |
| 3 | `session=asia` | 0.0659 |
| 4 | `adx_H4=[18,25)` | 0.0626 |
| 5 | `hour_bucket=04-08` | 0.0531 |
| 6 | `H1_adx_label=weak_trend` | 0.0507 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0411 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0386 |
| 9 | `adx_H1=[18,25)` | 0.0347 |
| 10 | `H1_adx_label=ranging` | 0.0302 |
| 11 | `mtf_trend=mixed` | 0.0286 |
| 12 | `adx_H1=[−∞,18)` | 0.0248 |
| 13 | `dow=Wed` | 0.0232 |
| 14 | `adx_H4=[25,35)` | 0.0230 |
| 15 | `bb_pctb_M30=[0.5,0.8)` | 0.0201 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **170**  ·  Baseline win-rate: **98.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (110 W / 0 L = 110 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (39 W / 0 L = 39 trade · +1.2pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · -8.3pp vs baseline)
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H4_adx_label = weak_trend`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0621 |
| 2 | `session=asia` | 0.0573 |
| 3 | `H4_adx_label=trending` | 0.0549 |
| 4 | `bb_pctb_M30=[0.5,0.8)` | 0.0529 |
| 5 | `hour_bucket=04-08` | 0.0443 |
| 6 | `mtf_trend=mixed` | 0.0426 |
| 7 | `H1_adx_label=weak_trend` | 0.0415 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0364 |
| 9 | `adx_H1=[18,25)` | 0.0331 |
| 10 | `M30_adx_label=weak_trend` | 0.0329 |
| 11 | `adx_H4=[18,25)` | 0.0326 |
| 12 | `dow=Tue` | 0.0323 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0318 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0263 |
| 15 | `macro_alignment=strong_against` | 0.0236 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **1187**  ·  Baseline win-rate: **95.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (209 W / 0 L = 209 trade · +4.3pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_extreme ≠ True`
   - `session ≠ us`

**2. Win-rate 100.0%** (107 W / 0 L = 107 trade · +4.3pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `atr_ratio_M30 = [1.3,1.7)`
   - `H4_adx_label ≠ weak_trend`

**3. Win-rate 100.0%** (25 W / 0 L = 25 trade · +4.3pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `atr_ratio_M30 = [1.3,1.7)`
   - `H4_adx_label = weak_trend`
   - `dist_high_M30 ≠ [1.5,+∞)`

**4. Win-rate 98.7%** (153 W / 2 L = 155 trade · +3.0pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [1.3,1.7)`
   - `consec_green_M30 = [0,2)`
   - `rsi_M30 ≠ [30,50)`

**5. Win-rate 96.4%** (54 W / 2 L = 56 trade · +0.7pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [1.3,1.7)`
   - `consec_green_M30 ≠ [0,2)`
   - `H1_ema_stack = down`

**6. Win-rate 96.2%** (25 W / 1 L = 26 trade · +0.5pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_extreme ≠ True`
   - `session = us`

**7. Win-rate 95.0%** (19 W / 1 L = 20 trade · -0.7pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_extreme = True`
   - `rsi_H4 ≠ [−∞,30)`

**8. Win-rate 95.0%** (19 W / 1 L = 20 trade · -0.7pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `rsi_H1 ≠ [50,65)`
   - `rsi_extreme = True`
   - `rsi_H4 = [−∞,30)`

**9. Win-rate 93.8%** (391 W / 26 L = 417 trade · -1.9pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [1.3,1.7)`
   - `consec_green_M30 = [0,2)`
   - `rsi_M30 = [30,50)`

**10. Win-rate 91.3%** (21 W / 2 L = 23 trade · -4.4pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `rsi_H1 = [50,65)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0230 |
| 2 | `session=overlap` | 0.0219 |
| 3 | `dist_low_M30=[1.5,+∞)` | 0.0210 |
| 4 | `bb_pctb_M30=[−∞,0.2)` | 0.0180 |
| 5 | `bb_pctb_M30=[0.2,0.5)` | 0.0179 |
| 6 | `dist_high_M30=[0.7,1.5)` | 0.0177 |
| 7 | `consec_green_M30=[0,2)` | 0.0173 |
| 8 | `consec_red_M30=[2,4)` | 0.0169 |
| 9 | `session=asia` | 0.0163 |
| 10 | `adx_H4=[35,+∞)` | 0.0159 |
| 11 | `rsi_M30=[50,65)` | 0.0153 |
| 12 | `rsi_H1=[50,65)` | 0.0146 |
| 13 | `vix_chg1d=[-3,0)` | 0.0142 |
| 14 | `M30_adx_label=weak_trend` | 0.0140 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0140 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **602**  ·  Baseline win-rate: **98.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (190 W / 0 L = 190 trade · +2.0pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase ≠ active_pit`
   - `session ≠ europe`

**2. Win-rate 100.0%** (59 W / 0 L = 59 trade · +2.0pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase ≠ active_pit`
   - `session = europe`

**3. Win-rate 100.0%** (48 W / 0 L = 48 trade · +2.0pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `session ≠ asia`

**4. Win-rate 100.0%** (20 W / 0 L = 20 trade · +2.0pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `dist_high_M30 ≠ [0.7,1.5)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

**5. Win-rate 100.0%** (65 W / 0 L = 65 trade · +2.0pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `dist_high_M30 ≠ [0.7,1.5)`
   - `us10y_chg1d = [0.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**6. Win-rate 100.0%** (35 W / 0 L = 35 trade · +2.0pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `dist_high_M30 = [0.7,1.5)`

**7. Win-rate 97.0%** (32 W / 1 L = 33 trade · -1.0pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase = active_pit`

**8. Win-rate 96.9%** (31 W / 1 L = 32 trade · -1.1pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `session = asia`
   - `hour_bucket = 00-04`

**9. Win-rate 95.2%** (40 W / 2 L = 42 trade · -2.8pp vs baseline)
   - `rsi_H4 = [50,65)`
   - `dist_high_M30 ≠ [0.7,1.5)`
   - `us10y_chg1d = [0.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**10. Win-rate 90.5%** (19 W / 2 L = 21 trade · -7.5pp vs baseline)
   - `rsi_H4 ≠ [50,65)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `session = asia`
   - `hour_bucket ≠ 00-04`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[0.5,0.8)` | 0.0362 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0254 |
| 3 | `bb_pctb_M30=[0.2,0.5)` | 0.0248 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0235 |
| 5 | `rsi_H4=[50,65)` | 0.0230 |
| 6 | `H1_ema_stack=up` | 0.0211 |
| 7 | `atr_ratio_M30=[−∞,0.7)` | 0.0192 |
| 8 | `dow=Fri` | 0.0190 |
| 9 | `H1_ema_stack=down` | 0.0190 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0187 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0178 |
| 12 | `session=asia` | 0.0178 |
| 13 | `session_phase=off_hours` | 0.0177 |
| 14 | `consec_red_M30=[0,2)` | 0.0174 |
| 15 | `M30_ema_stack=mixed` | 0.0163 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **1267**  ·  Baseline win-rate: **97.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (187 W / 0 L = 187 trade · +2.6pp vs baseline)
   - `bb_extreme_lower ≠ False`

**2. Win-rate 100.0%** (82 W / 0 L = 82 trade · +2.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `atr_ratio_M30 = [1.3,1.7)`

**3. Win-rate 100.0%** (156 W / 0 L = 156 trade · +2.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 = [0.5,0.8)`

**4. Win-rate 98.4%** (183 W / 3 L = 186 trade · +1.0pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase ≠ late_pit`

**5. Win-rate 98.2%** (217 W / 4 L = 221 trade · +0.8pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `atr_ratio_M30 ≠ [1.3,1.7)`
   - `ml_confidence_bucket = [70,80)`

**6. Win-rate 94.2%** (374 W / 23 L = 397 trade · -3.2pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `atr_ratio_M30 ≠ [1.3,1.7)`
   - `ml_confidence_bucket ≠ [70,80)`

**7. Win-rate 92.1%** (35 W / 3 L = 38 trade · -5.3pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `session_phase = late_pit`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_extreme_lower=True` | 0.0243 |
| 2 | `sar_bearish=True` | 0.0231 |
| 3 | `bb_extreme_lower=False` | 0.0226 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0212 |
| 5 | `consec_red_M30=[0,2)` | 0.0211 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0202 |
| 7 | `sar_bearish=False` | 0.0191 |
| 8 | `consec_green_M30=[0,2)` | 0.0176 |
| 9 | `macro_alignment=strong_against` | 0.0171 |
| 10 | `consec_green_M30=[4,6)` | 0.0168 |
| 11 | `bb_pctb_M30=[0.5,0.8)` | 0.0163 |
| 12 | `vix_chg1d=[0,3)` | 0.0162 |
| 13 | `atr_ratio_M30=[0.7,1)` | 0.0161 |
| 14 | `session=us` | 0.0157 |
| 15 | `dow=Tue` | 0.0157 |

---

## USOIL.FOREX · smc
_atlandı: y is constant_

---

## XAUUSD · meta
- Toplam çözülmüş: **169**  ·  Baseline win-rate: **64.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +35.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H1_adx_label = trending`
   - `session = europe`

**2. Win-rate 87.9%** (29 W / 4 L = 33 trade · +23.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `H1_adx_label = trending`
   - `session ≠ europe`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.6%** (8 W / 21 L = 29 trade · -36.9pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_low_M30=[1.5,+∞)` | 0.0734 |
| 2 | `H1_adx_label=trending` | 0.0584 |
| 3 | `bb_pctb_M30=[−∞,0.2)` | 0.0582 |
| 4 | `macro_alignment=weak_pro` | 0.0522 |
| 5 | `adx_M30=[35,+∞)` | 0.0504 |
| 6 | `macd_atr_M30=[0,0.3)` | 0.0361 |
| 7 | `adx_H1=[18,25)` | 0.0349 |
| 8 | `adx_M30=[25,35)` | 0.0305 |
| 9 | `H1_adx_label=weak_trend` | 0.0277 |
| 10 | `macd_atr_M30=[-0.3,0)` | 0.0263 |
| 11 | `sar_bearish=True` | 0.0228 |
| 12 | `bb_pctb_M30=[0.5,0.8)` | 0.0221 |
| 13 | `bb_extreme_lower=False` | 0.0218 |
| 14 | `adx_H1=[35,+∞)` | 0.0211 |
| 15 | `rsi_M30=[30,50)` | 0.0191 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **858**  ·  Baseline win-rate: **35.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +49.2pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `near_support ≠ True`
   - `adx_M30 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.8%** (5 W / 46 L = 51 trade · -26.0pp vs baseline)
   - `bb_extreme_lower = False`
   - `adx_M30 ≠ [18,25)`
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket = 00-04`

**2. Win-rate 22.5%** (9 W / 31 L = 40 trade · -13.3pp vs baseline)
   - `bb_extreme_lower ≠ False`
   - `near_support = True`
   - `dow ≠ Mon`

**3. Win-rate 24.2%** (8 W / 25 L = 33 trade · -11.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `adx_M30 = [18,25)`
   - `consec_green_M30 ≠ [0,2)`
   - `M30_ema_stack = mixed`

**4. Win-rate 27.8%** (57 W / 148 L = 205 trade · -8.0pp vs baseline)
   - `bb_extreme_lower = False`
   - `adx_M30 ≠ [18,25)`
   - `ml_confidence_bucket = [80,+∞)`
   - `hour_bucket ≠ 00-04`

**5. Win-rate 28.0%** (28 W / 72 L = 100 trade · -7.8pp vs baseline)
   - `bb_extreme_lower = False`
   - `adx_M30 ≠ [18,25)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0322 |
| 2 | `bb_extreme_lower=False` | 0.0255 |
| 3 | `dist_high_M30=[0.7,1.5)` | 0.0199 |
| 4 | `bb_extreme_lower=True` | 0.0196 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0192 |
| 6 | `macd_atr_M30=[-0.3,0)` | 0.0184 |
| 7 | `dist_low_M30=[0.3,0.7)` | 0.0183 |
| 8 | `session=overlap` | 0.0182 |
| 9 | `macro_alignment=weak_pro` | 0.0172 |
| 10 | `consec_green_M30=[0,2)` | 0.0171 |
| 11 | `dow=Fri` | 0.0160 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0158 |
| 13 | `M30_adx_label=weak_trend` | 0.0157 |
| 14 | `consec_green_M30=[2,4)` | 0.0153 |
| 15 | `bb_pctb_M30=[0.2,0.5)` | 0.0146 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **456**  ·  Baseline win-rate: **50.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.7%** (35 W / 4 L = 39 trade · +39.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `consec_green_M30 = [0,2)`
   - `M30_ema_stack ≠ down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.6%** (75 W / 142 L = 217 trade · -15.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`
   - `macd_atr_M30 ≠ [0.3,+∞)`
   - `dow ≠ Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0655 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0534 |
| 3 | `session=asia` | 0.0280 |
| 4 | `volatility_regime=normal` | 0.0254 |
| 5 | `dow=Thu` | 0.0245 |
| 6 | `hour_bucket=16-20` | 0.0242 |
| 7 | `adx_H1=[−∞,18)` | 0.0213 |
| 8 | `vix_chg1d=[-3,0)` | 0.0202 |
| 9 | `session=us` | 0.0179 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0170 |
| 11 | `dow=Fri` | 0.0167 |
| 12 | `M30_adx_label=trending` | 0.0164 |
| 13 | `dist_high_M30=[1.5,+∞)` | 0.0162 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0151 |
| 15 | `adx_H1=[18,25)` | 0.0150 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **686**  ·  Baseline win-rate: **56.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.9%** (77 W / 17 L = 94 trade · +25.9pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `us10y_chg1d = [0.5,+∞)`
   - `consec_red_M30 ≠ [2,4)`
   - `mtf_trend = all_down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.7%** (2 W / 28 L = 30 trade · -49.3pp vs baseline)
   - `M30_ema_stack = mixed`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 11.5%** (3 W / 23 L = 26 trade · -44.5pp vs baseline)
   - `M30_ema_stack = mixed`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket ≠ [50,60)`
   - `rsi_H1 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0370 |
| 2 | `M30_ema_stack=mixed` | 0.0353 |
| 3 | `H1_adx_label=trending` | 0.0305 |
| 4 | `M30_ema_stack=down` | 0.0245 |
| 5 | `consec_green_M30=[0,2)` | 0.0224 |
| 6 | `macro_alignment=strong_against` | 0.0200 |
| 7 | `rsi_M30=[30,50)` | 0.0196 |
| 8 | `us10y_chg1d=[−∞,-0.5)` | 0.0188 |
| 9 | `consec_red_M30=[0,2)` | 0.0183 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0171 |
| 11 | `adx_H1=[35,+∞)` | 0.0166 |
| 12 | `dist_high_M30=[1.5,+∞)` | 0.0164 |
| 13 | `rsi_H1=[30,50)` | 0.0159 |
| 14 | `mtf_trend=all_down` | 0.0159 |
| 15 | `near_resistance=True` | 0.0154 |

---

## XAUUSD · smc
- Toplam çözülmüş: **100**  ·  Baseline win-rate: **61.0%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_M30=[30,50)` | 0.0451 |
| 2 | `rsi_H1=[50,65)` | 0.0446 |
| 3 | `adx_M30=[−∞,18)` | 0.0376 |
| 4 | `dow=Tue` | 0.0324 |
| 5 | `rsi_H1=[30,50)` | 0.0317 |
| 6 | `dist_low_M30=[1.5,+∞)` | 0.0300 |
| 7 | `dow=Fri` | 0.0288 |
| 8 | `M30_adx_label=ranging` | 0.0284 |
| 9 | `hour_bucket=16-20` | 0.0266 |
| 10 | `macro_alignment=strong_pro` | 0.0265 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0263 |
| 12 | `dist_low_M30=[0.7,1.5)` | 0.0262 |
| 13 | `consec_green_M30=[2,4)` | 0.0239 |
| 14 | `vix_chg1d=[0,3)` | 0.0227 |
| 15 | `volatility_regime=low` | 0.0221 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **85**  ·  Baseline win-rate: **82.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +17.6pp vs baseline)
   - `sar_bearish ≠ False`
   - `volatility_regime = high`

**2. Win-rate 86.4%** (19 W / 3 L = 22 trade · +4.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `volatility_regime ≠ high`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1192 |
| 2 | `sar_bearish=False` | 0.0961 |
| 3 | `adx_H4=[18,25)` | 0.0467 |
| 4 | `rsi_extreme=False` | 0.0359 |
| 5 | `H4_adx_label=trending` | 0.0354 |
| 6 | `adx_H4=[25,35)` | 0.0353 |
| 7 | `rsi_extreme=True` | 0.0353 |
| 8 | `rsi_H1=[50,65)` | 0.0325 |
| 9 | `regime_label=strong_trend_up` | 0.0311 |
| 10 | `overbought=True` | 0.0290 |
| 11 | `volatility_regime=high` | 0.0288 |
| 12 | `H1_ema_stack=up` | 0.0287 |
| 13 | `volatility_regime=normal` | 0.0283 |
| 14 | `H1_ema_stack=mixed` | 0.0260 |
| 15 | `rsi_H1=[65,75)` | 0.0253 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **152**  ·  Baseline win-rate: **69.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.5%** (34 W / 4 L = 38 trade · +19.8pp vs baseline)
   - `H1_ema_stack = up`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket ≠ [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0507 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0465 |
| 3 | `near_resistance=True` | 0.0453 |
| 4 | `macro_alignment=strong_against` | 0.0443 |
| 5 | `volatility_regime=normal` | 0.0438 |
| 6 | `H1_ema_stack=up` | 0.0414 |
| 7 | `H1_ema_stack=mixed` | 0.0396 |
| 8 | `volatility_regime=high` | 0.0388 |
| 9 | `near_resistance=False` | 0.0360 |
| 10 | `vix_chg1d=[0,3)` | 0.0327 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0243 |
| 12 | `dxy_chg1d=[−∞,-0.5)` | 0.0235 |
| 13 | `rsi_H4=[50,65)` | 0.0218 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0208 |
| 15 | `rsi_H4=[65,75)` | 0.0202 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **94**  ·  Baseline win-rate: **87.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +12.8pp vs baseline)
   - `ml_confidence_bucket = [50,60)`

**2. Win-rate 89.5%** (34 W / 4 L = 38 trade · +2.3pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `session ≠ europe`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.1106 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0715 |
| 3 | `session=europe` | 0.0671 |
| 4 | `session=overlap` | 0.0586 |
| 5 | `macro_alignment=strong_pro` | 0.0539 |
| 6 | `adx_H1=[35,+∞)` | 0.0369 |
| 7 | `macro_alignment=weak_against` | 0.0297 |
| 8 | `mtf_trend=mixed` | 0.0264 |
| 9 | `hour_bucket=12-16` | 0.0251 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0223 |
| 11 | `rsi_H1=[30,50)` | 0.0221 |
| 12 | `vix_chg1d=[−∞,-3)` | 0.0207 |
| 13 | `dow=Wed` | 0.0207 |
| 14 | `volatility_regime=normal` | 0.0205 |
| 15 | `hour_bucket=08-12` | 0.0202 |

---

## GDAXI.INDX · pulse2 · BUY
- Toplam çözülmüş: **131**  ·  Baseline win-rate: **85.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +14.5pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `macro_alignment ≠ strong_against`

**2. Win-rate 100.0%** (25 W / 0 L = 25 trade · +14.5pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `macro_alignment = strong_against`

**3. Win-rate 88.6%** (31 W / 4 L = 35 trade · +3.1pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [−∞,-0.5)`

**4. Win-rate 86.4%** (19 W / 3 L = 22 trade · +0.9pp vs baseline)
   - `sar_bearish ≠ True`
   - `mtf_trend = all_up`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.1259 |
| 2 | `sar_bearish=True` | 0.1238 |
| 3 | `macro_alignment=strong_against` | 0.0488 |
| 4 | `rsi_H1=[30,50)` | 0.0487 |
| 5 | `rsi_H1=[65,75)` | 0.0421 |
| 6 | `volatility_regime=normal` | 0.0332 |
| 7 | `H1_ema_stack=mixed` | 0.0330 |
| 8 | `H1_ema_stack=up` | 0.0307 |
| 9 | `adx_H1=[25,35)` | 0.0292 |
| 10 | `vix_chg1d=[0,3)` | 0.0262 |
| 11 | `volatility_regime=high` | 0.0237 |
| 12 | `us10y_chg1d=[−∞,-0.5)` | 0.0208 |
| 13 | `session=overlap` | 0.0205 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0196 |
| 15 | `ml_confidence_bucket=[60,70)` | 0.0190 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **267**  ·  Baseline win-rate: **82.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (70 W / 0 L = 70 trade · +17.2pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 ≠ [65,75)`
   - `ml_confidence_bucket ≠ [60,70)`

**2. Win-rate 95.0%** (38 W / 2 L = 40 trade · +12.2pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 ≠ [65,75)`
   - `ml_confidence_bucket = [60,70)`

**3. Win-rate 89.1%** (41 W / 5 L = 46 trade · +6.3pp vs baseline)
   - `sar_bearish = False`
   - `near_resistance ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d ≠ [−∞,-3)`

**4. Win-rate 84.8%** (28 W / 5 L = 33 trade · +2.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `rsi_H1 = [65,75)`

**5. Win-rate 76.7%** (23 W / 7 L = 30 trade · -6.1pp vs baseline)
   - `sar_bearish = False`
   - `near_resistance ≠ True`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -59.0pp vs baseline)
   - `sar_bearish = False`
   - `near_resistance = True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1009 |
| 2 | `sar_bearish=False` | 0.0995 |
| 3 | `near_resistance=True` | 0.0559 |
| 4 | `H1_ema_stack=up` | 0.0465 |
| 5 | `rsi_H1=[65,75)` | 0.0336 |
| 6 | `H1_ema_stack=mixed` | 0.0332 |
| 7 | `near_resistance=False` | 0.0324 |
| 8 | `rsi_H1=[30,50)` | 0.0314 |
| 9 | `adx_H4=[18,25)` | 0.0219 |
| 10 | `volatility_regime=high` | 0.0216 |
| 11 | `macro_alignment=strong_against` | 0.0209 |
| 12 | `rsi_extreme=False` | 0.0207 |
| 13 | `volatility_regime=normal` | 0.0200 |
| 14 | `dow=Thu` | 0.0194 |
| 15 | `rsi_extreme=True` | 0.0190 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **89**  ·  Baseline win-rate: **71.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.6%** (29 W / 3 L = 32 trade · +18.7pp vs baseline)
   - `volatility_regime = high`
   - `rsi_H1 ≠ [65,75)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=overlap` | 0.0678 |
| 2 | `volatility_regime=normal` | 0.0574 |
| 3 | `rsi_H4=[65,75)` | 0.0556 |
| 4 | `sar_bearish=True` | 0.0425 |
| 5 | `sar_bearish=False` | 0.0425 |
| 6 | `session=us` | 0.0396 |
| 7 | `mtf_trend=all_up` | 0.0392 |
| 8 | `volatility_regime=high` | 0.0373 |
| 9 | `rsi_H1=[65,75)` | 0.0303 |
| 10 | `vix_chg1d=[-3,0)` | 0.0299 |
| 11 | `adx_H4=[35,+∞)` | 0.0291 |
| 12 | `rsi_H1=[30,50)` | 0.0271 |
| 13 | `regime_label=strong_trend_up` | 0.0250 |
| 14 | `rsi_H4=[75,+∞)` | 0.0248 |
| 15 | `dow=Thu` | 0.0239 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **218**  ·  Baseline win-rate: **55.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.4%** (27 W / 5 L = 32 trade · +29.4pp vs baseline)
   - `near_resistance ≠ True`
   - `rsi_H1 = [75,+∞)`

**2. Win-rate 77.8%** (35 W / 10 L = 45 trade · +22.8pp vs baseline)
   - `near_resistance ≠ True`
   - `rsi_H1 ≠ [75,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `session ≠ us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.3%** (3 W / 18 L = 21 trade · -40.7pp vs baseline)
   - `near_resistance = True`
   - `vix_chg1d ≠ [-3,0)`

**2. Win-rate 26.9%** (7 W / 19 L = 26 trade · -28.1pp vs baseline)
   - `near_resistance ≠ True`
   - `rsi_H1 ≠ [75,+∞)`
   - `ml_confidence_bucket = [80,+∞)`
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `near_resistance=True` | 0.0819 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0760 |
| 3 | `near_resistance=False` | 0.0733 |
| 4 | `session_phase=mid_session` | 0.0349 |
| 5 | `session=us` | 0.0343 |
| 6 | `session=overlap` | 0.0308 |
| 7 | `dow=Wed` | 0.0300 |
| 8 | `macro_alignment=weak_pro` | 0.0256 |
| 9 | `session_phase=open_drive` | 0.0254 |
| 10 | `ml_confidence_bucket=[50,60)` | 0.0229 |
| 11 | `sar_bearish=False` | 0.0225 |
| 12 | `rsi_H4=[65,75)` | 0.0214 |
| 13 | `volatility_regime=normal` | 0.0181 |
| 14 | `H4_ema_stack=up` | 0.0177 |
| 15 | `rsi_H4=[75,+∞)` | 0.0177 |

---

## NDX.INDX · pulse2 · BUY
- Toplam çözülmüş: **163**  ·  Baseline win-rate: **65.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 94.9%** (37 W / 2 L = 39 trade · +29.9pp vs baseline)
   - `near_resistance = False`
   - `rsi_H4 ≠ [75,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `adx_H1 ≠ [25,35)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -41.2pp vs baseline)
   - `near_resistance ≠ False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0644 |
| 2 | `dow=Thu` | 0.0585 |
| 3 | `near_resistance=True` | 0.0521 |
| 4 | `near_resistance=False` | 0.0411 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0398 |
| 6 | `sar_bearish=False` | 0.0372 |
| 7 | `session=overlap` | 0.0336 |
| 8 | `H4_ema_stack=NA` | 0.0294 |
| 9 | `adx_H4=[25,35)` | 0.0269 |
| 10 | `volatility_regime=high` | 0.0263 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0257 |
| 12 | `sar_bearish=True` | 0.0257 |
| 13 | `rsi_H4=[65,75)` | 0.0246 |
| 14 | `rsi_H4=[75,+∞)` | 0.0240 |
| 15 | `volatility_regime=normal` | 0.0202 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **265**  ·  Baseline win-rate: **68.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (33 W / 0 L = 33 trade · +31.7pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ strong_against`
   - `session_phase = mid_session`

**2. Win-rate 86.0%** (37 W / 6 L = 43 trade · +17.7pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ strong_against`
   - `session_phase ≠ mid_session`

**3. Win-rate 83.3%** (35 W / 7 L = 42 trade · +15.0pp vs baseline)
   - `near_resistance = False`
   - `rsi_H1 = [65,75)`
   - `dow ≠ Wed`
   - `session ≠ us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 28.6%** (6 W / 15 L = 21 trade · -39.7pp vs baseline)
   - `near_resistance ≠ False`
   - `hour_bucket = 16-20`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `near_resistance=False` | 0.0695 |
| 2 | `near_resistance=True` | 0.0663 |
| 3 | `sar_bearish=False` | 0.0619 |
| 4 | `sar_bearish=True` | 0.0469 |
| 5 | `rsi_H4=[75,+∞)` | 0.0313 |
| 6 | `macro_alignment=weak_pro` | 0.0307 |
| 7 | `rsi_H1=[30,50)` | 0.0293 |
| 8 | `ml_confidence_bucket=[60,70)` | 0.0253 |
| 9 | `session=overlap` | 0.0243 |
| 10 | `session=us` | 0.0239 |
| 11 | `volatility_regime=normal` | 0.0237 |
| 12 | `adx_H4=[25,35)` | 0.0231 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0230 |
| 14 | `dow=Thu` | 0.0211 |
| 15 | `ml_confidence_bucket=[70,80)` | 0.0210 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **91**  ·  Baseline win-rate: **97.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (60 W / 0 L = 60 trade · +2.2pp vs baseline)
   - `session ≠ asia`

**2. Win-rate 93.5%** (29 W / 2 L = 31 trade · -4.3pp vs baseline)
   - `session = asia`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session=asia` | 0.0769 |
| 2 | `bb_pctb_M30=[0.5,0.8)` | 0.0401 |
| 3 | `adx_M30=[18,25)` | 0.0391 |
| 4 | `session_phase=off_hours` | 0.0391 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0377 |
| 6 | `rsi_M30=[50,65)` | 0.0345 |
| 7 | `M30_adx_label=ranging` | 0.0342 |
| 8 | `dow=Mon` | 0.0332 |
| 9 | `H1_ema_stack=up` | 0.0324 |
| 10 | `atr_ratio_M30=[0.7,1)` | 0.0302 |
| 11 | `M30_adx_label=weak_trend` | 0.0300 |
| 12 | `M30_ema_stack=mixed` | 0.0295 |
| 13 | `volatility_regime=normal` | 0.0272 |
| 14 | `rsi_H4=[50,65)` | 0.0270 |
| 15 | `rsi_M30=[30,50)` | 0.0241 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **199**  ·  Baseline win-rate: **98.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (127 W / 0 L = 127 trade · +2.0pp vs baseline)
   - `volatility_regime = normal`
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 97.2%** (35 W / 1 L = 36 trade · -0.8pp vs baseline)
   - `volatility_regime = normal`
   - `adx_H1 = [−∞,18)`

**3. Win-rate 91.7%** (33 W / 3 L = 36 trade · -6.3pp vs baseline)
   - `volatility_regime ≠ normal`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `volatility_regime=normal` | 0.0610 |
| 2 | `hour_bucket=04-08` | 0.0540 |
| 3 | `H1_adx_label=ranging` | 0.0453 |
| 4 | `atr_ratio_M30=[−∞,0.7)` | 0.0356 |
| 5 | `volatility_regime=low` | 0.0346 |
| 6 | `adx_H1=[−∞,18)` | 0.0279 |
| 7 | `adx_M30=[25,35)` | 0.0256 |
| 8 | `macd_atr_M30=[0,0.3)` | 0.0251 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0246 |
| 10 | `macro_alignment=neutral` | 0.0243 |
| 11 | `dow=Wed` | 0.0236 |
| 12 | `bb_pctb_M30=[0.2,0.5)` | 0.0227 |
| 13 | `adx_M30=[−∞,18)` | 0.0220 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0213 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0186 |

---

## USOIL.FOREX · ml:aggressive · SELL
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **99.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (87 W / 0 L = 87 trade · +0.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 95.8%** (23 W / 1 L = 24 trade · -3.3pp vs baseline)
   - `adx_H1 = [−∞,18)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=04-08` | 0.1000 |
| 2 | `H4_adx_label=trending` | 0.1000 |
| 3 | `adx_H1=[−∞,18)` | 0.0915 |
| 4 | `H4_adx_label=weak_trend` | 0.0827 |
| 5 | `H1_adx_label=ranging` | 0.0769 |
| 6 | `bb_pctb_M30=[0.5,0.8)` | 0.0577 |
| 7 | `H1_ema_stack=mixed` | 0.0527 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0480 |
| 9 | `adx_H4=[25,35)` | 0.0351 |
| 10 | `adx_H4=[18,25)` | 0.0340 |
| 11 | `adx_H1=[18,25)` | 0.0319 |
| 12 | `session=asia` | 0.0305 |
| 13 | `macro_alignment=neutral` | 0.0301 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0268 |
| 15 | `H1_adx_label=weak_trend` | 0.0244 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **99.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (87 W / 0 L = 87 trade · +0.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 95.8%** (23 W / 1 L = 24 trade · -3.3pp vs baseline)
   - `adx_H1 = [−∞,18)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=04-08` | 0.1000 |
| 2 | `H4_adx_label=trending` | 0.1000 |
| 3 | `adx_H1=[−∞,18)` | 0.0915 |
| 4 | `H4_adx_label=weak_trend` | 0.0827 |
| 5 | `H1_adx_label=ranging` | 0.0769 |
| 6 | `bb_pctb_M30=[0.5,0.8)` | 0.0577 |
| 7 | `H1_ema_stack=mixed` | 0.0527 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0480 |
| 9 | `adx_H4=[25,35)` | 0.0351 |
| 10 | `adx_H4=[18,25)` | 0.0340 |
| 11 | `adx_H1=[18,25)` | 0.0319 |
| 12 | `session=asia` | 0.0305 |
| 13 | `macro_alignment=neutral` | 0.0301 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0268 |
| 15 | `H1_adx_label=weak_trend` | 0.0244 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **99.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (87 W / 0 L = 87 trade · +0.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 95.8%** (23 W / 1 L = 24 trade · -3.3pp vs baseline)
   - `adx_H1 = [−∞,18)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=04-08` | 0.1000 |
| 2 | `H4_adx_label=trending` | 0.1000 |
| 3 | `adx_H1=[−∞,18)` | 0.0915 |
| 4 | `H4_adx_label=weak_trend` | 0.0827 |
| 5 | `H1_adx_label=ranging` | 0.0769 |
| 6 | `bb_pctb_M30=[0.5,0.8)` | 0.0577 |
| 7 | `H1_ema_stack=mixed` | 0.0527 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0480 |
| 9 | `adx_H4=[25,35)` | 0.0351 |
| 10 | `adx_H4=[18,25)` | 0.0340 |
| 11 | `adx_H1=[18,25)` | 0.0319 |
| 12 | `session=asia` | 0.0305 |
| 13 | `macro_alignment=neutral` | 0.0301 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0268 |
| 15 | `H1_adx_label=weak_trend` | 0.0244 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **98.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (87 W / 0 L = 87 trade · +1.8pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 91.7%** (22 W / 2 L = 24 trade · -6.5pp vs baseline)
   - `adx_H1 = [−∞,18)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.1237 |
| 2 | `hour_bucket=04-08` | 0.0909 |
| 3 | `adx_H1=[−∞,18)` | 0.0823 |
| 4 | `H4_adx_label=weak_trend` | 0.0794 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0785 |
| 6 | `H1_adx_label=ranging` | 0.0687 |
| 7 | `H1_ema_stack=mixed` | 0.0466 |
| 8 | `adx_H1=[18,25)` | 0.0460 |
| 9 | `adx_H4=[18,25)` | 0.0342 |
| 10 | `H1_adx_label=weak_trend` | 0.0329 |
| 11 | `dow=Wed` | 0.0306 |
| 12 | `adx_H4=[25,35)` | 0.0303 |
| 13 | `session=asia` | 0.0256 |
| 14 | `bb_pctb_M30=[0.5,0.8)` | 0.0210 |
| 15 | `sar_bearish=True` | 0.0190 |

---

## USOIL.FOREX · ml:ultra_safe · SELL
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **99.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (87 W / 0 L = 87 trade · +0.9pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`

**2. Win-rate 95.8%** (23 W / 1 L = 24 trade · -3.3pp vs baseline)
   - `adx_H1 = [−∞,18)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=04-08` | 0.1000 |
| 2 | `H4_adx_label=trending` | 0.1000 |
| 3 | `adx_H1=[−∞,18)` | 0.0915 |
| 4 | `H4_adx_label=weak_trend` | 0.0827 |
| 5 | `H1_adx_label=ranging` | 0.0769 |
| 6 | `bb_pctb_M30=[0.5,0.8)` | 0.0577 |
| 7 | `H1_ema_stack=mixed` | 0.0527 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0480 |
| 9 | `adx_H4=[25,35)` | 0.0351 |
| 10 | `adx_H4=[18,25)` | 0.0340 |
| 11 | `adx_H1=[18,25)` | 0.0319 |
| 12 | `session=asia` | 0.0305 |
| 13 | `macro_alignment=neutral` | 0.0301 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0268 |
| 15 | `H1_adx_label=weak_trend` | 0.0244 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **547**  ·  Baseline win-rate: **92.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (31 W / 0 L = 31 trade · +7.1pp vs baseline)
   - `dow ≠ Thu`
   - `consec_red_M30 = [0,2)`
   - `session_phase = active_pit`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**2. Win-rate 100.0%** (22 W / 0 L = 22 trade · +7.1pp vs baseline)
   - `dow ≠ Thu`
   - `consec_red_M30 = [0,2)`
   - `session_phase = active_pit`
   - `bb_pctb_M30 = [0.2,0.5)`

**3. Win-rate 100.0%** (59 W / 0 L = 59 trade · +7.1pp vs baseline)
   - `dow = Thu`
   - `rsi_M30 ≠ [30,50)`

**4. Win-rate 95.8%** (23 W / 1 L = 24 trade · +2.9pp vs baseline)
   - `dow = Thu`
   - `rsi_M30 = [30,50)`

**5. Win-rate 93.9%** (290 W / 19 L = 309 trade · +1.0pp vs baseline)
   - `dow ≠ Thu`
   - `consec_red_M30 = [0,2)`
   - `session_phase ≠ active_pit`
   - `hour_bucket ≠ 00-04`

**6. Win-rate 85.3%** (64 W / 11 L = 75 trade · -7.6pp vs baseline)
   - `dow ≠ Thu`
   - `consec_red_M30 = [0,2)`
   - `session_phase ≠ active_pit`
   - `hour_bucket = 00-04`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0396 |
| 2 | `session=overlap` | 0.0266 |
| 3 | `ml_confidence_bucket=[60,70)` | 0.0265 |
| 4 | `hour_bucket=00-04` | 0.0242 |
| 5 | `vix_chg1d=[-3,0)` | 0.0222 |
| 6 | `consec_red_M30=[2,4)` | 0.0210 |
| 7 | `rsi_M30=[50,65)` | 0.0194 |
| 8 | `vix_chg1d=[0,3)` | 0.0182 |
| 9 | `H4_ema_stack=up` | 0.0179 |
| 10 | `consec_green_M30=[2,4)` | 0.0177 |
| 11 | `consec_red_M30=[0,2)` | 0.0168 |
| 12 | `atr_ratio_M30=[1.3,1.7)` | 0.0164 |
| 13 | `dist_high_M30=[0.7,1.5)` | 0.0159 |
| 14 | `H1_ema_stack=down` | 0.0154 |
| 15 | `macd_atr_M30=[0,0.3)` | 0.0153 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **640**  ·  Baseline win-rate: **98.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (120 W / 0 L = 120 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [−∞,-0.5)`
   - `session ≠ overlap`

**2. Win-rate 100.0%** (44 W / 0 L = 44 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [−∞,-0.5)`
   - `session = overlap`

**3. Win-rate 100.0%** (32 W / 0 L = 32 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `rsi_M30 ≠ [50,65)`
   - `session = overlap`

**4. Win-rate 100.0%** (100 W / 0 L = 100 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `rsi_M30 = [50,65)`

**5. Win-rate 100.0%** (107 W / 0 L = 107 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `hour_bucket ≠ 04-08`

**6. Win-rate 100.0%** (31 W / 0 L = 31 trade · +1.9pp vs baseline)
   - `ml_confidence_bucket = [50,60)`
   - `hour_bucket = 04-08`

**7. Win-rate 96.3%** (26 W / 1 L = 27 trade · -1.8pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [−∞,-0.5)`

**8. Win-rate 93.9%** (168 W / 11 L = 179 trade · -4.2pp vs baseline)
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `rsi_M30 ≠ [50,65)`
   - `session ≠ overlap`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0296 |
| 2 | `dist_low_M30=[1.5,+∞)` | 0.0280 |
| 3 | `rsi_M30=[30,50)` | 0.0268 |
| 4 | `consec_red_M30=[2,4)` | 0.0263 |
| 5 | `sar_bearish=False` | 0.0261 |
| 6 | `macd_atr_M30=[0,0.3)` | 0.0246 |
| 7 | `session=asia` | 0.0235 |
| 8 | `rsi_M30=[50,65)` | 0.0227 |
| 9 | `hour_bucket=04-08` | 0.0222 |
| 10 | `sar_bearish=True` | 0.0220 |
| 11 | `bb_pctb_M30=[0.2,0.5)` | 0.0209 |
| 12 | `macd_atr_M30=[-0.3,0)` | 0.0199 |
| 13 | `ml_confidence_bucket=[80,+∞)` | 0.0180 |
| 14 | `vix_chg1d=[-3,0)` | 0.0180 |
| 15 | `dist_low_M30=[0.7,1.5)` | 0.0176 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **220**  ·  Baseline win-rate: **97.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (103 W / 0 L = 103 trade · +2.3pp vs baseline)
   - `consec_green_M30 ≠ [2,4)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 100.0%** (34 W / 0 L = 34 trade · +2.3pp vs baseline)
   - `consec_green_M30 ≠ [2,4)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H1_ema_stack ≠ up`

**3. Win-rate 100.0%** (25 W / 0 L = 25 trade · +2.3pp vs baseline)
   - `consec_green_M30 ≠ [2,4)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H1_ema_stack = up`
   - `session = us`

**4. Win-rate 92.0%** (23 W / 2 L = 25 trade · -5.7pp vs baseline)
   - `consec_green_M30 ≠ [2,4)`
   - `bb_pctb_M30 = [0.5,0.8)`
   - `H1_ema_stack = up`
   - `session ≠ us`

**5. Win-rate 90.9%** (30 W / 3 L = 33 trade · -6.8pp vs baseline)
   - `consec_green_M30 = [2,4)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=off_hours` | 0.0531 |
| 2 | `hour_bucket=00-04` | 0.0465 |
| 3 | `consec_green_M30=[0,2)` | 0.0464 |
| 4 | `bb_pctb_M30=[0.5,0.8)` | 0.0395 |
| 5 | `sar_bearish=True` | 0.0349 |
| 6 | `atr_ratio_M30=[1.3,1.7)` | 0.0307 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0288 |
| 8 | `sar_bearish=False` | 0.0278 |
| 9 | `M30_adx_label=weak_trend` | 0.0273 |
| 10 | `consec_green_M30=[2,4)` | 0.0271 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0262 |
| 12 | `rsi_M30=[30,50)` | 0.0241 |
| 13 | `atr_ratio_M30=[0.7,1)` | 0.0232 |
| 14 | `macro_alignment=neutral` | 0.0225 |
| 15 | `adx_M30=[18,25)` | 0.0201 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **382**  ·  Baseline win-rate: **98.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +1.8pp vs baseline)
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `H1_ema_stack ≠ down`
   - `session = europe`

**2. Win-rate 100.0%** (69 W / 0 L = 69 trade · +1.8pp vs baseline)
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `H1_ema_stack = down`
   - `ml_confidence_bucket ≠ [70,80)`

**3. Win-rate 100.0%** (24 W / 0 L = 24 trade · +1.8pp vs baseline)
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `H1_ema_stack = down`
   - `ml_confidence_bucket = [70,80)`

**4. Win-rate 100.0%** (142 W / 0 L = 142 trade · +1.8pp vs baseline)
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `bb_pctb_M30 = [0.2,0.5)`

**5. Win-rate 100.0%** (38 W / 0 L = 38 trade · +1.8pp vs baseline)
   - `atr_ratio_M30 = [−∞,0.7)`
   - `consec_red_M30 ≠ [2,4)`

**6. Win-rate 94.9%** (56 W / 3 L = 59 trade · -3.3pp vs baseline)
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `H1_ema_stack ≠ down`
   - `session ≠ europe`

**7. Win-rate 81.8%** (18 W / 4 L = 22 trade · -16.4pp vs baseline)
   - `atr_ratio_M30 = [−∞,0.7)`
   - `consec_red_M30 = [2,4)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `atr_ratio_M30=[−∞,0.7)` | 0.0566 |
| 2 | `ml_confidence_bucket=[60,70)` | 0.0403 |
| 3 | `H1_adx_label=ranging` | 0.0388 |
| 4 | `volatility_regime=low` | 0.0356 |
| 5 | `M30_ema_stack=mixed` | 0.0300 |
| 6 | `consec_red_M30=[2,4)` | 0.0292 |
| 7 | `consec_red_M30=[0,2)` | 0.0291 |
| 8 | `M30_adx_label=trending` | 0.0289 |
| 9 | `rsi_H4=[50,65)` | 0.0277 |
| 10 | `H1_ema_stack=up` | 0.0267 |
| 11 | `ml_confidence_bucket=[70,80)` | 0.0259 |
| 12 | `dow=Fri` | 0.0251 |
| 13 | `hour_bucket=04-08` | 0.0231 |
| 14 | `volatility_regime=normal` | 0.0198 |
| 15 | `us10y_chg1d=[-0.5,0)` | 0.0197 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **347**  ·  Baseline win-rate: **94.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +5.2pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `sar_bearish = True`

**2. Win-rate 100.0%** (20 W / 0 L = 20 trade · +5.2pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `macd_atr_M30 ≠ [0,0.3)`
   - `sar_bearish ≠ True`
   - `consec_red_M30 = [2,4)`

**3. Win-rate 100.0%** (57 W / 0 L = 57 trade · +5.2pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `macd_atr_M30 ≠ [0,0.3)`
   - `sar_bearish = True`
   - `ml_confidence_bucket ≠ [80,+∞)`

**4. Win-rate 100.0%** (72 W / 0 L = 72 trade · +5.2pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `macd_atr_M30 = [0,0.3)`

**5. Win-rate 96.0%** (24 W / 1 L = 25 trade · +1.2pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `macd_atr_M30 ≠ [0,0.3)`
   - `sar_bearish = True`
   - `ml_confidence_bucket = [80,+∞)`

**6. Win-rate 92.0%** (92 W / 8 L = 100 trade · -2.8pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `macd_atr_M30 ≠ [0,0.3)`
   - `sar_bearish ≠ True`
   - `consec_red_M30 ≠ [2,4)`

**7. Win-rate 90.0%** (18 W / 2 L = 20 trade · -4.8pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `sar_bearish ≠ True`

**8. Win-rate 76.7%** (23 W / 7 L = 30 trade · -18.1pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `atr_ratio_M30 = [0.7,1)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0386 |
| 2 | `dist_low_M30=[1.5,+∞)` | 0.0298 |
| 3 | `dist_low_M30=[0.7,1.5)` | 0.0283 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0278 |
| 5 | `macro_alignment=neutral` | 0.0255 |
| 6 | `macro_alignment=strong_against` | 0.0243 |
| 7 | `atr_ratio_M30=[0.7,1)` | 0.0227 |
| 8 | `session=us` | 0.0223 |
| 9 | `sar_bearish=False` | 0.0213 |
| 10 | `H1_ema_stack=mixed` | 0.0208 |
| 11 | `session_phase=off_hours` | 0.0208 |
| 12 | `sar_bearish=True` | 0.0195 |
| 13 | `macd_atr_M30=[0.3,+∞)` | 0.0193 |
| 14 | `macd_atr_M30=[0,0.3)` | 0.0193 |
| 15 | `atr_ratio_M30=[1.3,1.7)` | 0.0185 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **920**  ·  Baseline win-rate: **98.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (170 W / 0 L = 170 trade · +1.6pp vs baseline)
   - `bb_extreme_lower ≠ False`

**2. Win-rate 100.0%** (58 W / 0 L = 58 trade · +1.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = strong_against`

**3. Win-rate 100.0%** (58 W / 0 L = 58 trade · +1.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `rsi_H1 ≠ [30,50)`

**4. Win-rate 100.0%** (127 W / 0 L = 127 trade · +1.6pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 = [0.5,0.8)`

**5. Win-rate 99.5%** (199 W / 1 L = 200 trade · +1.1pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `us10y_chg1d = [-0.5,0)`
   - `macro_alignment = neutral`

**6. Win-rate 97.9%** (140 W / 3 L = 143 trade · -0.5pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `rsi_H1 = [30,50)`

**7. Win-rate 93.5%** (129 W / 9 L = 138 trade · -4.9pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ strong_against`

**8. Win-rate 92.3%** (24 W / 2 L = 26 trade · -6.1pp vs baseline)
   - `bb_extreme_lower = False`
   - `H1_ema_stack ≠ down`
   - `us10y_chg1d = [-0.5,0)`
   - `macro_alignment ≠ neutral`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_extreme_lower=True` | 0.0294 |
| 2 | `bb_pctb_M30=[0.2,0.5)` | 0.0269 |
| 3 | `ml_confidence_bucket=[70,80)` | 0.0245 |
| 4 | `H1_ema_stack=down` | 0.0227 |
| 5 | `bb_extreme_lower=False` | 0.0219 |
| 6 | `macro_alignment=neutral` | 0.0216 |
| 7 | `ml_confidence_bucket=[60,70)` | 0.0212 |
| 8 | `sar_bearish=False` | 0.0209 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0208 |
| 10 | `macd_atr_M30=[0,0.3)` | 0.0207 |
| 11 | `macd_atr_M30=[-0.3,0)` | 0.0206 |
| 12 | `macro_alignment=strong_against` | 0.0201 |
| 13 | `consec_red_M30=[0,2)` | 0.0200 |
| 14 | `H4_ema_stack=mixed` | 0.0186 |
| 15 | `vix_chg1d=[0,3)` | 0.0174 |

---

## USOIL.FOREX · smc · SELL
_atlandı: y is constant_

---

## XAUUSD · meta · BUY
- Toplam çözülmüş: **111**  ·  Baseline win-rate: **65.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.6%** (28 W / 1 L = 29 trade · +30.8pp vs baseline)
   - `rsi_M30 ≠ [30,50)`
   - `adx_M30 ≠ [25,35)`
   - `consec_green_M30 = [0,2)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +9.2pp vs baseline)
   - `rsi_M30 ≠ [30,50)`
   - `adx_M30 ≠ [25,35)`
   - `consec_green_M30 ≠ [0,2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.5%** (10 W / 19 L = 29 trade · -31.3pp vs baseline)
   - `rsi_M30 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[25,35)` | 0.0703 |
| 2 | `rsi_M30=[30,50)` | 0.0577 |
| 3 | `macro_alignment=weak_pro` | 0.0537 |
| 4 | `rsi_H1=[30,50)` | 0.0535 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0428 |
| 6 | `dist_low_M30=[1.5,+∞)` | 0.0426 |
| 7 | `H1_adx_label=trending` | 0.0425 |
| 8 | `adx_M30=[35,+∞)` | 0.0386 |
| 9 | `macd_atr_M30=[0,0.3)` | 0.0353 |
| 10 | `session=europe` | 0.0333 |
| 11 | `bb_pctb_M30=[0.5,0.8)` | 0.0329 |
| 12 | `adx_H1=[18,25)` | 0.0304 |
| 13 | `sar_bearish=False` | 0.0250 |
| 14 | `H1_adx_label=weak_trend` | 0.0247 |
| 15 | `bb_pctb_M30=[−∞,0.2)` | 0.0242 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **501**  ·  Baseline win-rate: **33.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.0%** (18 W / 6 L = 24 trade · +41.3pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `sar_bearish ≠ True`
   - `ml_confidence_bucket = [50,60)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.3%** (2 W / 22 L = 24 trade · -25.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend = mixed`
   - `bb_pctb_M30 = [0.2,0.5)`

**2. Win-rate 12.7%** (9 W / 62 L = 71 trade · -21.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `macro_alignment ≠ weak_pro`

**3. Win-rate 15.4%** (4 W / 22 L = 26 trade · -18.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 ≠ [18,25)`
   - `hour_bucket = 12-16`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 19.0%** (4 W / 17 L = 21 trade · -14.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend = mixed`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**5. Win-rate 24.0%** (6 W / 19 L = 25 trade · -9.7pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 = [18,25)`
   - `near_resistance ≠ False`

**6. Win-rate 24.5%** (12 W / 37 L = 49 trade · -9.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `macro_alignment = weak_pro`

**7. Win-rate 25.0%** (13 W / 39 L = 52 trade · -8.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `mtf_trend ≠ mixed`
   - `dist_low_M30 = [0.7,1.5)`

**8. Win-rate 29.6%** (8 W / 19 L = 27 trade · -4.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `sar_bearish = True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0551 |
| 2 | `bb_pctb_M30=[0.5,0.8)` | 0.0332 |
| 3 | `macro_alignment=weak_pro` | 0.0326 |
| 4 | `M30_adx_label=weak_trend` | 0.0231 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0217 |
| 6 | `mtf_trend=mixed` | 0.0213 |
| 7 | `adx_M30=[18,25)` | 0.0201 |
| 8 | `M30_ema_stack=mixed` | 0.0196 |
| 9 | `adx_H1=[−∞,18)` | 0.0196 |
| 10 | `hour_bucket=12-16` | 0.0177 |
| 11 | `bb_pctb_M30=[0.8,+∞)` | 0.0170 |
| 12 | `consec_green_M30=[0,2)` | 0.0167 |
| 13 | `sar_bearish=True` | 0.0164 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0163 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0155 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **357**  ·  Baseline win-rate: **38.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.5%** (2 W / 19 L = 21 trade · -29.2pp vs baseline)
   - `macd_atr_M30 ≠ [-0.3,0)`
   - `rsi_H1 ≠ [50,65)`
   - `dist_low_M30 = [0.7,1.5)`

**2. Win-rate 20.7%** (6 W / 23 L = 29 trade · -18.0pp vs baseline)
   - `macd_atr_M30 ≠ [-0.3,0)`
   - `rsi_H1 ≠ [50,65)`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `session = europe`

**3. Win-rate 24.4%** (10 W / 31 L = 41 trade · -14.3pp vs baseline)
   - `macd_atr_M30 = [-0.3,0)`
   - `dow = Fri`

**4. Win-rate 29.0%** (9 W / 22 L = 31 trade · -9.7pp vs baseline)
   - `macd_atr_M30 ≠ [-0.3,0)`
   - `rsi_H1 = [50,65)`
   - `dist_high_M30 = [0.7,1.5)`

**5. Win-rate 33.3%** (13 W / 26 L = 39 trade · -5.4pp vs baseline)
   - `macd_atr_M30 = [-0.3,0)`
   - `dow ≠ Fri`
   - `adx_M30 = [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_extreme_lower=False` | 0.0337 |
| 2 | `bb_extreme_lower=True` | 0.0317 |
| 3 | `adx_M30=[25,35)` | 0.0305 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0295 |
| 5 | `session=us` | 0.0265 |
| 6 | `dow=Fri` | 0.0255 |
| 7 | `macd_atr_M30=[-0.3,0)` | 0.0246 |
| 8 | `sar_bearish=True` | 0.0241 |
| 9 | `bb_pctb_M30=[−∞,0.2)` | 0.0215 |
| 10 | `consec_red_M30=[0,2)` | 0.0214 |
| 11 | `consec_red_M30=[2,4)` | 0.0196 |
| 12 | `near_support=True` | 0.0195 |
| 13 | `atr_ratio_M30=[1,1.3)` | 0.0182 |
| 14 | `sar_bearish=False` | 0.0178 |
| 15 | `dist_high_M30=[0.7,1.5)` | 0.0177 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **301**  ·  Baseline win-rate: **48.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (24 W / 4 L = 28 trade · +36.9pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `adx_M30 = [25,35)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.4%** (19 W / 66 L = 85 trade · -26.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macd_atr_M30 ≠ [0.3,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0744 |
| 2 | `consec_green_M30=[0,2)` | 0.0373 |
| 3 | `session=asia` | 0.0362 |
| 4 | `M30_adx_label=trending` | 0.0345 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0330 |
| 6 | `ml_confidence_bucket=[−∞,50)` | 0.0288 |
| 7 | `volatility_regime=normal` | 0.0266 |
| 8 | `vix_chg1d=[-3,0)` | 0.0230 |
| 9 | `bb_pctb_M30=[0.5,0.8)` | 0.0204 |
| 10 | `hour_bucket=16-20` | 0.0197 |
| 11 | `consec_red_M30=[0,2)` | 0.0178 |
| 12 | `rsi_M30=[30,50)` | 0.0176 |
| 13 | `dist_high_M30=[1.5,+∞)` | 0.0169 |
| 14 | `session=europe` | 0.0164 |
| 15 | `adx_M30=[−∞,18)` | 0.0160 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **155**  ·  Baseline win-rate: **52.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.8%** (21 W / 5 L = 26 trade · +27.9pp vs baseline)
   - `dow = Thu`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.7%** (5 W / 29 L = 34 trade · -38.2pp vs baseline)
   - `dow ≠ Thu`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_M30 ≠ [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.0638 |
| 2 | `dow=Thu` | 0.0481 |
| 3 | `consec_red_M30=[2,4)` | 0.0408 |
| 4 | `mtf_trend=all_up` | 0.0337 |
| 5 | `session=europe` | 0.0327 |
| 6 | `session=us` | 0.0306 |
| 7 | `M30_adx_label=weak_trend` | 0.0304 |
| 8 | `adx_M30=[18,25)` | 0.0255 |
| 9 | `rsi_H1=[50,65)` | 0.0250 |
| 10 | `M30_ema_stack=down` | 0.0246 |
| 11 | `macro_alignment=strong_against` | 0.0235 |
| 12 | `dist_low_M30=[0.7,1.5)` | 0.0235 |
| 13 | `consec_red_M30=[0,2)` | 0.0230 |
| 14 | `near_support=False` | 0.0189 |
| 15 | `bb_pctb_M30=[−∞,0.2)` | 0.0172 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **405**  ·  Baseline win-rate: **49.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.8%** (30 W / 2 L = 32 trade · +44.2pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `H1_adx_label = trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.3%** (2 W / 22 L = 24 trade · -41.3pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `mtf_trend = mixed`
   - `dow = Tue`

**2. Win-rate 15.0%** (3 W / 17 L = 20 trade · -34.6pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `mtf_trend ≠ mixed`
   - `consec_green_M30 = [2,4)`
   - `hour_bucket = 12-16`

**3. Win-rate 22.2%** (10 W / 35 L = 45 trade · -27.4pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `mtf_trend = mixed`
   - `dow ≠ Tue`
   - `hour_bucket = 00-04`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0434 |
| 2 | `mtf_trend=mixed` | 0.0405 |
| 3 | `consec_green_M30=[0,2)` | 0.0354 |
| 4 | `consec_green_M30=[2,4)` | 0.0338 |
| 5 | `consec_red_M30=[2,4)` | 0.0320 |
| 6 | `M30_ema_stack=mixed` | 0.0295 |
| 7 | `mtf_trend=all_up` | 0.0279 |
| 8 | `M30_ema_stack=up` | 0.0268 |
| 9 | `dow=Tue` | 0.0248 |
| 10 | `bb_pctb_M30=[0.8,+∞)` | 0.0238 |
| 11 | `H1_adx_label=trending` | 0.0209 |
| 12 | `dxy_chg1d=[−∞,-0.5)` | 0.0195 |
| 13 | `volatility_regime=low` | 0.0195 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0184 |
| 15 | `adx_H1=[18,25)` | 0.0182 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **281**  ·  Baseline win-rate: **65.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +34.9pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `vix_chg1d ≠ [0,3)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 88.5%** (23 W / 3 L = 26 trade · +23.4pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `vix_chg1d ≠ [0,3)`
   - `ml_confidence_bucket = [60,70)`
   - `vix_chg1d = [−∞,-3)`

**3. Win-rate 83.3%** (25 W / 5 L = 30 trade · +18.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `vix_chg1d ≠ [0,3)`
   - `ml_confidence_bucket ≠ [60,70)`
   - `atr_ratio_M30 = [0.7,1)`

**4. Win-rate 83.3%** (20 W / 4 L = 24 trade · +18.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `vix_chg1d = [0,3)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.4%** (3 W / 29 L = 32 trade · -55.7pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `us10y_chg1d = [−∞,-0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0857 |
| 2 | `consec_red_M30=[2,4)` | 0.0580 |
| 3 | `adx_H1=[−∞,18)` | 0.0319 |
| 4 | `H1_adx_label=ranging` | 0.0286 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0282 |
| 6 | `dist_low_M30=[−∞,0.3)` | 0.0276 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0241 |
| 8 | `M30_ema_stack=down` | 0.0238 |
| 9 | `oversold=True` | 0.0206 |
| 10 | `hour_bucket=12-16` | 0.0188 |
| 11 | `near_support=False` | 0.0177 |
| 12 | `M30_adx_label=trending` | 0.0172 |
| 13 | `rsi_M30=[30,50)` | 0.0171 |
| 14 | `rsi_M30=[−∞,30)` | 0.0169 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0164 |

---
