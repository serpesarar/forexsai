# Pattern Mining Raporu
_2026-07-21T20:56:05.816166Z — son 60 gün — 37624 resolved sinyal_

**Yöntem:** Decision Tree (max_depth=4) + Random Forest feature importance.
Her leaf bir kural. min_samples_leaf=20, class_weight=balanced.

**Yorum kılavuzu:**
- 🟢 Win-rate ≥ %75 = pattern güvenilir (confidence boost veya yeni feature adayı)
- 🔴 Win-rate ≤ %35 = pattern toksik (filter rule olarak ekle)
- Baseline win-rate'i her segment için ayrıca göster — relative kazanım önemli

---

## GLOBAL — tüm sembol & model
- Toplam çözülmüş: **37624**  ·  Baseline win-rate: **40.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.7%** (686 W / 134 L = 820 trade · +43.4pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `macd_atr_M30 ≠ [−∞,-0.3)`
   - `consec_red_M30 ≠ [0,2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.2%** (6 W / 90 L = 96 trade · -34.1pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label = trending`
   - `macd_atr_M30 = [−∞,-0.3)`
   - `H4_ema_stack = down`

**2. Win-rate 19.5%** (68 W / 280 L = 348 trade · -20.8pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label = trending`
   - `M30_ema_stack = mixed`
   - `session ≠ europe`

**3. Win-rate 26.6%** (275 W / 759 L = 1034 trade · -13.7pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `consec_red_M30 ≠ NA`

**4. Win-rate 27.7%** (358 W / 934 L = 1292 trade · -12.6pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label ≠ trending`
   - `macro_alignment = weak_against`
   - `dxy_chg1d = [-0.5,0)`

**5. Win-rate 27.9%** (113 W / 292 L = 405 trade · -12.4pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label = trending`
   - `M30_ema_stack ≠ mixed`
   - `bb_extreme_upper ≠ False`

**6. Win-rate 28.9%** (4229 W / 10420 L = 14649 trade · -11.4pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `H4_adx_label ≠ trending`
   - `macro_alignment ≠ weak_against`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[30,50)` | 0.0326 |
| 2 | `H4_ema_stack=NA` | 0.0245 |
| 3 | `H1_ema_stack=down` | 0.0225 |
| 4 | `rsi_H4=[50,65)` | 0.0183 |
| 5 | `macro_alignment=weak_pro` | 0.0181 |
| 6 | `mtf_trend=all_down` | 0.0176 |
| 7 | `M30_ema_stack=down` | 0.0168 |
| 8 | `M30_ema_stack=up` | 0.0168 |
| 9 | `rsi_H1=[30,50)` | 0.0166 |
| 10 | `H4_ema_stack=down` | 0.0160 |
| 11 | `H4_adx_label=NA` | 0.0148 |
| 12 | `rsi_H4=NA` | 0.0143 |
| 13 | `regime_label=transition` | 0.0141 |
| 14 | `macro_alignment=strong_against` | 0.0138 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0137 |

---

## GDAXI.INDX · ai_panel
- Toplam çözülmüş: **104**  ·  Baseline win-rate: **55.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.0%** (20 W / 3 L = 23 trade · +31.2pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label = weak_trend`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.0%** (6 W / 18 L = 24 trade · -30.8pp vs baseline)
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.0855 |
| 2 | `us10y_chg1d=[-0.5,0)` | 0.0744 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0595 |
| 4 | `H1_ema_stack=mixed` | 0.0473 |
| 5 | `dow=Mon` | 0.0362 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0332 |
| 7 | `H1_adx_label=weak_trend` | 0.0327 |
| 8 | `macro_alignment=neutral` | 0.0320 |
| 9 | `adx_H1=[18,25)` | 0.0299 |
| 10 | `regime_label=transition` | 0.0289 |
| 11 | `regime_label=ranging` | 0.0279 |
| 12 | `hour_bucket=08-12` | 0.0271 |
| 13 | `H4_ema_stack=up` | 0.0271 |
| 14 | `adx_H4=[−∞,18)` | 0.0260 |
| 15 | `H4_adx_label=ranging` | 0.0260 |

---

## GDAXI.INDX · meta
- Toplam çözülmüş: **365**  ·  Baseline win-rate: **46.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.6%** (29 W / 7 L = 36 trade · +33.8pp vs baseline)
   - `regime_label = ranging`
   - `us10y_chg1d = [-0.5,0)`

**2. Win-rate 75.0%** (33 W / 11 L = 44 trade · +28.2pp vs baseline)
   - `regime_label ≠ ranging`
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [0,0.5)`
   - `H4_ema_stack = up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.8%** (4 W / 33 L = 37 trade · -36.0pp vs baseline)
   - `regime_label ≠ ranging`
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [−∞,18)`

**2. Win-rate 28.6%** (8 W / 20 L = 28 trade · -18.2pp vs baseline)
   - `regime_label ≠ ranging`
   - `sar_bearish = True`
   - `us10y_chg1d = [0,0.5)`

**3. Win-rate 29.4%** (25 W / 60 L = 85 trade · -17.4pp vs baseline)
   - `regime_label ≠ ranging`
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0423 |
| 2 | `H4_adx_label=ranging` | 0.0386 |
| 3 | `regime_label=ranging` | 0.0380 |
| 4 | `sar_bearish=True` | 0.0361 |
| 5 | `us10y_chg1d=[0,0.5)` | 0.0326 |
| 6 | `adx_H4=[−∞,18)` | 0.0315 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0296 |
| 8 | `macro_alignment=neutral` | 0.0233 |
| 9 | `rsi_H1=[30,50)` | 0.0227 |
| 10 | `mtf_trend=all_up` | 0.0227 |
| 11 | `dow=Mon` | 0.0207 |
| 12 | `H4_ema_stack=mixed` | 0.0188 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0179 |
| 14 | `rsi_H1=[50,65)` | 0.0175 |
| 15 | `adx_H1=[−∞,18)` | 0.0169 |

---

## GDAXI.INDX · ml:balanced
- Toplam çözülmüş: **191**  ·  Baseline win-rate: **63.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +31.8pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +22.3pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`
   - `hour_bucket = 12-16`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +14.9pp vs baseline)
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [30,50)`
   - `sar_bearish = True`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.6%** (8 W / 21 L = 29 trade · -35.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `H1_adx_label ≠ weak_trend`
   - `vix_chg1d = [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0499 |
| 2 | `H4_ema_stack=up` | 0.0497 |
| 3 | `rsi_H1=[30,50)` | 0.0412 |
| 4 | `H1_adx_label=weak_trend` | 0.0408 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0405 |
| 6 | `adx_H1=[18,25)` | 0.0391 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0387 |
| 8 | `H1_adx_label=ranging` | 0.0386 |
| 9 | `sar_bearish=True` | 0.0293 |
| 10 | `adx_H1=[−∞,18)` | 0.0289 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0286 |
| 12 | `bb_extreme_upper=True` | 0.0247 |
| 13 | `H1_ema_stack=down` | 0.0226 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0216 |
| 15 | `hour_bucket=08-12` | 0.0214 |

---

## GDAXI.INDX · ml:full_power
- Toplam çözülmüş: **214**  ·  Baseline win-rate: **57.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.5%** (29 W / 2 L = 31 trade · +36.0pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.4%** (6 W / 22 L = 28 trade · -36.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -24.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `adx_H1 = [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0742 |
| 2 | `sar_bearish=False` | 0.0725 |
| 3 | `H4_ema_stack=up` | 0.0464 |
| 4 | `regime_label=transition` | 0.0446 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0432 |
| 6 | `bb_extreme_upper=True` | 0.0344 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0281 |
| 8 | `adx_H1=[−∞,18)` | 0.0259 |
| 9 | `bb_extreme_lower=True` | 0.0249 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0240 |
| 11 | `rsi_H1=[30,50)` | 0.0238 |
| 12 | `rsi_H1=[50,65)` | 0.0228 |
| 13 | `adx_H4=[−∞,18)` | 0.0201 |
| 14 | `H1_ema_stack=down` | 0.0190 |
| 15 | `bb_extreme_upper=False` | 0.0169 |

---

## GDAXI.INDX · ml:main
- Toplam çözülmüş: **214**  ·  Baseline win-rate: **57.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.5%** (29 W / 2 L = 31 trade · +36.0pp vs baseline)
   - `sar_bearish = True`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.4%** (6 W / 22 L = 28 trade · -36.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -24.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `H1_adx_label = ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0859 |
| 2 | `sar_bearish=True` | 0.0643 |
| 3 | `H4_ema_stack=up` | 0.0544 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0408 |
| 5 | `bb_extreme_upper=True` | 0.0330 |
| 6 | `rsi_H1=[30,50)` | 0.0310 |
| 7 | `regime_label=transition` | 0.0302 |
| 8 | `vix_chg1d=[−∞,-3)` | 0.0289 |
| 9 | `H1_ema_stack=down` | 0.0249 |
| 10 | `H1_adx_label=ranging` | 0.0211 |
| 11 | `bb_extreme_upper=False` | 0.0210 |
| 12 | `H4_adx_label=weak_trend` | 0.0196 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0195 |
| 14 | `H4_ema_stack=mixed` | 0.0192 |
| 15 | `rsi_H1=[50,65)` | 0.0188 |

---

## GDAXI.INDX · pulse1
- Toplam çözülmüş: **884**  ·  Baseline win-rate: **28.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.7%** (55 W / 14 L = 69 trade · +51.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `rsi_H1 = [50,65)`
   - `hour_bucket = 08-12`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 125 L = 125 trade · -28.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish ≠ True`

**2. Win-rate 0.0%** (0 W / 28 L = 28 trade · -28.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 8.1%** (5 W / 57 L = 62 trade · -20.5pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish = True`

**4. Win-rate 18.4%** (38 W / 169 L = 207 trade · -10.2pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket ≠ 04-08`
   - `ml_confidence_bucket ≠ [−∞,50)`

**5. Win-rate 19.0%** (4 W / 17 L = 21 trade · -9.6pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ ranging`
   - `hour_bucket = 04-08`
   - `vix_chg1d = [−∞,-3)`

**6. Win-rate 20.8%** (5 W / 19 L = 24 trade · -7.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label = ranging`
   - `rsi_H1 ≠ [50,65)`
   - `dxy_chg1d = [-0.5,0)`

**7. Win-rate 22.2%** (6 W / 21 L = 27 trade · -6.4pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 = NA`
   - `adx_H1 = [18,25)`

**8. Win-rate 28.6%** (10 W / 25 L = 35 trade · 0.0pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `rsi_H4 ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.1258 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0467 |
| 3 | `H4_adx_label=weak_trend` | 0.0396 |
| 4 | `adx_H4=[18,25)` | 0.0360 |
| 5 | `adx_H4=[−∞,18)` | 0.0347 |
| 6 | `regime_label=ranging` | 0.0337 |
| 7 | `vix_chg1d=[0,3)` | 0.0327 |
| 8 | `bb_extreme_upper=True` | 0.0265 |
| 9 | `vix_chg1d=[-3,0)` | 0.0235 |
| 10 | `bb_extreme_upper=False` | 0.0222 |
| 11 | `H4_adx_label=ranging` | 0.0187 |
| 12 | `regime_label=transition` | 0.0183 |
| 13 | `hour_bucket=12-16` | 0.0183 |
| 14 | `hour_bucket=08-12` | 0.0164 |
| 15 | `rsi_H1=[50,65)` | 0.0164 |

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
- Toplam çözülmüş: **465**  ·  Baseline win-rate: **42.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.3%** (36 W / 1 L = 37 trade · +54.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `hour_bucket ≠ 12-16`

**2. Win-rate 86.2%** (25 W / 4 L = 29 trade · +43.4pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime = high`
   - `regime_label ≠ transition`

**3. Win-rate 75.9%** (22 W / 7 L = 29 trade · +33.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `hour_bucket = 12-16`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.4%** (25 W / 119 L = 144 trade · -25.4pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime ≠ high`
   - `session ≠ asia`
   - `dow ≠ Tue`

**2. Win-rate 20.0%** (5 W / 20 L = 25 trade · -22.8pp vs baseline)
   - `sar_bearish = False`
   - `volatility_regime = high`
   - `regime_label = transition`

**3. Win-rate 24.3%** (9 W / 28 L = 37 trade · -18.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ strong_pro`

**4. Win-rate 29.3%** (12 W / 29 L = 41 trade · -13.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0482 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0396 |
| 3 | `sar_bearish=True` | 0.0386 |
| 4 | `volatility_regime=high` | 0.0362 |
| 5 | `adx_H4=[−∞,18)` | 0.0350 |
| 6 | `regime_label=ranging` | 0.0318 |
| 7 | `dow=Mon` | 0.0312 |
| 8 | `regime_label=transition` | 0.0297 |
| 9 | `H4_adx_label=ranging` | 0.0295 |
| 10 | `bb_extreme_upper=False` | 0.0294 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0253 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0228 |
| 13 | `bb_extreme_upper=True` | 0.0204 |
| 14 | `dow=Wed` | 0.0191 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0189 |

---

## GDAXI.INDX · pulse2_inv
- Toplam çözülmüş: **141**  ·  Baseline win-rate: **50.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 78.3%** (18 W / 5 L = 23 trade · +27.9pp vs baseline)
   - `rsi_H4 ≠ NA`
   - `rsi_H4 ≠ [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.2%** (8 W / 25 L = 33 trade · -26.2pp vs baseline)
   - `rsi_H4 = NA`
   - `volatility_regime = normal`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=NA` | 0.0573 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0567 |
| 3 | `rsi_H4=[75,+∞)` | 0.0410 |
| 4 | `volatility_regime=normal` | 0.0367 |
| 5 | `adx_H4=NA` | 0.0338 |
| 6 | `macro_alignment=strong_pro` | 0.0332 |
| 7 | `H4_adx_label=trending` | 0.0319 |
| 8 | `hour_bucket=08-12` | 0.0279 |
| 9 | `rsi_H4=NA` | 0.0278 |
| 10 | `H4_adx_label=NA` | 0.0273 |
| 11 | `ml_confidence_bucket=[−∞,50)` | 0.0236 |
| 12 | `dow=Mon` | 0.0231 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0230 |
| 14 | `sar_bearish=True` | 0.0229 |
| 15 | `ml_confidence_bucket=[50,60)` | 0.0215 |

---

## GDAXI.INDX · pulse3
- Toplam çözülmüş: **803**  ·  Baseline win-rate: **36.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 33 L = 33 trade · -36.1pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `rsi_H4 ≠ NA`
   - `bb_extreme_upper ≠ False`
   - `macro_alignment ≠ weak_against`

**2. Win-rate 4.4%** (2 W / 43 L = 45 trade · -31.7pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `rsi_H4 ≠ NA`
   - `bb_extreme_upper = False`
   - `session = europe`

**3. Win-rate 5.0%** (1 W / 19 L = 20 trade · -31.1pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `rsi_H4 ≠ NA`
   - `bb_extreme_upper ≠ False`
   - `macro_alignment = weak_against`

**4. Win-rate 10.1%** (9 W / 80 L = 89 trade · -26.0pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `sar_bearish ≠ False`
   - `H4_ema_stack ≠ NA`

**5. Win-rate 11.3%** (6 W / 47 L = 53 trade · -24.8pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `dxy_chg1d = [-0.5,0)`
   - `vix_chg1d = [-3,0)`
   - `dow = Mon`

**6. Win-rate 21.7%** (5 W / 18 L = 23 trade · -14.4pp vs baseline)
   - `adx_H1 ≠ [−∞,18)`
   - `dxy_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [-3,0)`
   - `H4_adx_label = NA`

**7. Win-rate 22.7%** (15 W / 51 L = 66 trade · -13.4pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `rsi_H4 ≠ NA`
   - `bb_extreme_upper = False`
   - `session ≠ europe`

**8. Win-rate 25.0%** (5 W / 15 L = 20 trade · -11.1pp vs baseline)
   - `adx_H1 = [−∞,18)`
   - `rsi_H4 = NA`
   - `session = europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[−∞,18)` | 0.0397 |
| 2 | `H1_adx_label=ranging` | 0.0384 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0363 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0305 |
| 5 | `ml_confidence_bucket=[60,70)` | 0.0277 |
| 6 | `H1_adx_label=trending` | 0.0238 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0231 |
| 8 | `us10y_chg1d=[0,0.5)` | 0.0206 |
| 9 | `hour_bucket=12-16` | 0.0194 |
| 10 | `dow=Tue` | 0.0193 |
| 11 | `vix_chg1d=[0,3)` | 0.0184 |
| 12 | `H4_ema_stack=mixed` | 0.0175 |
| 13 | `session=europe` | 0.0173 |
| 14 | `H1_ema_stack=mixed` | 0.0164 |
| 15 | `dow=Mon` | 0.0161 |

---

## GDAXI.INDX · pulse3_inv
- Toplam çözülmüş: **196**  ·  Baseline win-rate: **44.4%**

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
| 1 | `us10y_chg1d=[0,0.5)` | 0.0420 |
| 2 | `H4_adx_label=NA` | 0.0419 |
| 3 | `macro_alignment=strong_pro` | 0.0366 |
| 4 | `H4_ema_stack=NA` | 0.0323 |
| 5 | `H4_adx_label=trending` | 0.0309 |
| 6 | `ml_confidence_bucket=[60,70)` | 0.0284 |
| 7 | `adx_H4=NA` | 0.0282 |
| 8 | `rsi_H4=NA` | 0.0275 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0219 |
| 10 | `mtf_trend=mixed` | 0.0217 |
| 11 | `rsi_H4=[75,+∞)` | 0.0216 |
| 12 | `H1_ema_stack=mixed` | 0.0213 |
| 13 | `H1_adx_label=ranging` | 0.0207 |
| 14 | `session=europe` | 0.0199 |
| 15 | `mtf_trend=all_up` | 0.0197 |

---

## NDX.INDX · ai_panel
- Toplam çözülmüş: **127**  ·  Baseline win-rate: **61.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.5%** (19 W / 2 L = 21 trade · +29.1pp vs baseline)
   - `H4_ema_stack = up`
   - `volatility_regime = high`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.1%** (6 W / 17 L = 23 trade · -35.3pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `mtf_trend = mixed`
   - `H1_ema_stack ≠ mixed`
   - `volatility_regime = normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0770 |
| 2 | `sar_bearish=True` | 0.0623 |
| 3 | `sar_bearish=False` | 0.0459 |
| 4 | `dow=Mon` | 0.0431 |
| 5 | `session=us` | 0.0396 |
| 6 | `macro_alignment=weak_pro` | 0.0351 |
| 7 | `mtf_trend=mixed` | 0.0325 |
| 8 | `session=overlap` | 0.0324 |
| 9 | `H1_adx_label=trending` | 0.0314 |
| 10 | `volatility_regime=high` | 0.0302 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0272 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0267 |
| 13 | `hour_bucket=12-16` | 0.0261 |
| 14 | `rsi_H4=[50,65)` | 0.0235 |
| 15 | `rsi_H1=[30,50)` | 0.0221 |

---

## NDX.INDX · meta
- Toplam çözülmüş: **240**  ·  Baseline win-rate: **52.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.0%** (27 W / 3 L = 30 trade · +37.9pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `hour_bucket = 16-20`

**2. Win-rate 85.7%** (18 W / 3 L = 21 trade · +33.6pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `us10y_chg1d = [-0.5,0)`
   - `adx_H4 = [25,35)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.3%** (1 W / 22 L = 23 trade · -47.8pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [50,65)`

**2. Win-rate 23.8%** (5 W / 16 L = 21 trade · -28.3pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `sar_bearish ≠ True`
   - `rsi_H4 = [50,65)`

**3. Win-rate 29.0%** (9 W / 22 L = 31 trade · -23.1pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `sar_bearish = True`
   - `hour_bucket = 16-20`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H4=[30,50)` | 0.0611 |
| 2 | `H1_ema_stack=up` | 0.0592 |
| 3 | `H1_ema_stack=mixed` | 0.0489 |
| 4 | `sar_bearish=True` | 0.0354 |
| 5 | `ml_confidence_bucket=[70,80)` | 0.0342 |
| 6 | `sar_bearish=False` | 0.0342 |
| 7 | `H1_adx_label=trending` | 0.0310 |
| 8 | `adx_H1=[18,25)` | 0.0289 |
| 9 | `rsi_H1=[65,75)` | 0.0228 |
| 10 | `adx_H4=[25,35)` | 0.0221 |
| 11 | `us10y_chg1d=[-0.5,0)` | 0.0207 |
| 12 | `H1_adx_label=weak_trend` | 0.0204 |
| 13 | `volatility_regime=normal` | 0.0202 |
| 14 | `H4_ema_stack=NA` | 0.0202 |
| 15 | `H4_ema_stack=up` | 0.0196 |

---

## NDX.INDX · ml:balanced
- Toplam çözülmüş: **257**  ·  Baseline win-rate: **53.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +31.7pp vs baseline)
   - `H4_ema_stack = up`
   - `dow = Wed`

**2. Win-rate 80.0%** (20 W / 5 L = 25 trade · +26.7pp vs baseline)
   - `H4_ema_stack = up`
   - `dow ≠ Wed`
   - `session = us`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 11.5%** (3 W / 23 L = 26 trade · -41.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `rsi_H1 = [50,65)`

**2. Win-rate 28.6%** (6 W / 15 L = 21 trade · -24.7pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `vix_chg1d ≠ [−∞,-3)`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0835 |
| 2 | `rsi_H1=[30,50)` | 0.0567 |
| 3 | `dow=Mon` | 0.0481 |
| 4 | `H4_ema_stack=mixed` | 0.0431 |
| 5 | `dow=Thu` | 0.0371 |
| 6 | `us10y_chg1d=[-0.5,0)` | 0.0310 |
| 7 | `mtf_trend=mixed` | 0.0291 |
| 8 | `session_phase=mid_session` | 0.0272 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0266 |
| 10 | `mtf_trend=all_up` | 0.0205 |
| 11 | `adx_H1=[25,35)` | 0.0197 |
| 12 | `hour_bucket=12-16` | 0.0194 |
| 13 | `H1_ema_stack=up` | 0.0168 |
| 14 | `session_phase=open_drive` | 0.0166 |
| 15 | `hour_bucket=16-20` | 0.0154 |

---

## NDX.INDX · ml:full_power
- Toplam çözülmüş: **267**  ·  Baseline win-rate: **54.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 80.6%** (29 W / 7 L = 36 trade · +25.9pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -30.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `H4_adx_label = trending`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -19.7pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow = Mon`
   - `hour_bucket = 12-16`

**3. Win-rate 35.0%** (7 W / 13 L = 20 trade · -19.7pp vs baseline)
   - `macro_alignment = weak_pro`
   - `H4_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0495 |
| 2 | `H4_ema_stack=up` | 0.0456 |
| 3 | `macro_alignment=weak_pro` | 0.0424 |
| 4 | `dow=Thu` | 0.0362 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0345 |
| 6 | `macro_alignment=neutral` | 0.0328 |
| 7 | `rsi_H1=[30,50)` | 0.0297 |
| 8 | `session_phase=mid_session` | 0.0286 |
| 9 | `adx_H1=[25,35)` | 0.0255 |
| 10 | `sar_bearish=True` | 0.0238 |
| 11 | `H4_ema_stack=mixed` | 0.0222 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0217 |
| 13 | `rsi_H4=[30,50)` | 0.0201 |
| 14 | `H1_adx_label=weak_trend` | 0.0196 |
| 15 | `adx_H1=[18,25)` | 0.0195 |

---

## NDX.INDX · ml:main
- Toplam çözülmüş: **268**  ·  Baseline win-rate: **55.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +30.5pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow ≠ Mon`
   - `regime_label = strong_trend_up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -31.4pp vs baseline)
   - `macro_alignment = weak_pro`
   - `H4_adx_label = trending`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -20.2pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dow = Mon`
   - `hour_bucket = 12-16`

**3. Win-rate 35.0%** (7 W / 13 L = 20 trade · -20.2pp vs baseline)
   - `macro_alignment = weak_pro`
   - `H4_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0534 |
| 2 | `dow=Mon` | 0.0497 |
| 3 | `macro_alignment=weak_pro` | 0.0444 |
| 4 | `dow=Thu` | 0.0361 |
| 5 | `rsi_H1=[30,50)` | 0.0296 |
| 6 | `macro_alignment=neutral` | 0.0284 |
| 7 | `sar_bearish=True` | 0.0251 |
| 8 | `H4_ema_stack=mixed` | 0.0233 |
| 9 | `adx_H1=[25,35)` | 0.0222 |
| 10 | `session_phase=mid_session` | 0.0216 |
| 11 | `sar_bearish=False` | 0.0207 |
| 12 | `adx_H1=[18,25)` | 0.0207 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0206 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0205 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0196 |

---

## NDX.INDX · ml:main_inv
- Toplam çözülmüş: **167**  ·  Baseline win-rate: **59.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +25.7pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `rsi_H1 ≠ [30,50)`
   - `rsi_H1 ≠ [50,65)`

**2. Win-rate 75.0%** (18 W / 6 L = 24 trade · +15.7pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `rsi_H1 ≠ [30,50)`
   - `rsi_H1 = [50,65)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0,0.5)` | 0.0499 |
| 2 | `dow=Mon` | 0.0448 |
| 3 | `regime_label=transition` | 0.0344 |
| 4 | `session=overlap` | 0.0342 |
| 5 | `session=us` | 0.0329 |
| 6 | `session_phase=mid_session` | 0.0316 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0315 |
| 8 | `H4_ema_stack=down` | 0.0301 |
| 9 | `adx_H1=[25,35)` | 0.0299 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0297 |
| 11 | `sar_bearish=True` | 0.0292 |
| 12 | `H4_ema_stack=up` | 0.0261 |
| 13 | `H4_adx_label=trending` | 0.0214 |
| 14 | `volatility_regime=high` | 0.0203 |
| 15 | `rsi_H1=[30,50)` | 0.0202 |

---

## NDX.INDX · pulse1
- Toplam çözülmüş: **969**  ·  Baseline win-rate: **41.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 87.8%** (36 W / 5 L = 41 trade · +46.3pp vs baseline)
   - `sar_bearish = True`
   - `dow = Fri`
   - `rsi_H4 = [30,50)`
   - `near_support = False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 1.3%** (1 W / 74 L = 75 trade · -40.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [30,50)`
   - `ml_confidence_bucket = [80,+∞)`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 13.6%** (3 W / 19 L = 22 trade · -27.9pp vs baseline)
   - `sar_bearish = True`
   - `dow ≠ Fri`
   - `rsi_H1 ≠ [−∞,30)`
   - `rsi_H4 = [65,75)`

**3. Win-rate 16.7%** (5 W / 25 L = 30 trade · -24.8pp vs baseline)
   - `sar_bearish = True`
   - `dow ≠ Fri`
   - `rsi_H1 = [−∞,30)`

**4. Win-rate 16.9%** (11 W / 54 L = 65 trade · -24.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [30,50)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `volatility_regime = high`

**5. Win-rate 17.9%** (7 W / 32 L = 39 trade · -23.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 ≠ [30,50)`
   - `ml_confidence_bucket = [80,+∞)`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 25.0%** (18 W / 54 L = 72 trade · -16.5pp vs baseline)
   - `sar_bearish ≠ True`
   - `rsi_H4 = [30,50)`
   - `macro_alignment ≠ weak_against`
   - `H4_ema_stack = mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.0363 |
| 2 | `sar_bearish=False` | 0.0331 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0313 |
| 4 | `H1_adx_label=trending` | 0.0295 |
| 5 | `adx_H1=[35,+∞)` | 0.0283 |
| 6 | `rsi_H4=[30,50)` | 0.0242 |
| 7 | `overbought=True` | 0.0221 |
| 8 | `overbought=False` | 0.0219 |
| 9 | `rsi_H1=[30,50)` | 0.0211 |
| 10 | `rsi_H1=[65,75)` | 0.0203 |
| 11 | `macro_alignment=strong_pro` | 0.0202 |
| 12 | `near_resistance=True` | 0.0198 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0181 |
| 14 | `H1_ema_stack=up` | 0.0172 |
| 15 | `bb_extreme_upper=True` | 0.0155 |

---

## NDX.INDX · pulse1_inv
- Toplam çözülmüş: **391**  ·  Baseline win-rate: **49.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +36.1pp vs baseline)
   - `dow ≠ Fri`
   - `rsi_H1 = [65,75)`
   - `ml_confidence_bucket = [80,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 22.9%** (8 W / 27 L = 35 trade · -26.7pp vs baseline)
   - `dow ≠ Fri`
   - `rsi_H1 ≠ [65,75)`
   - `session_phase = mid_session`
   - `H1_ema_stack = up`

**2. Win-rate 22.9%** (8 W / 27 L = 35 trade · -26.7pp vs baseline)
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0399 |
| 2 | `session_phase=mid_session` | 0.0319 |
| 3 | `macro_alignment=neutral` | 0.0309 |
| 4 | `H4_ema_stack=mixed` | 0.0287 |
| 5 | `macro_alignment=weak_pro` | 0.0282 |
| 6 | `session_phase=after_hours` | 0.0257 |
| 7 | `H4_ema_stack=down` | 0.0253 |
| 8 | `overbought=False` | 0.0248 |
| 9 | `overbought=True` | 0.0247 |
| 10 | `ml_confidence_bucket=[80,+∞)` | 0.0223 |
| 11 | `adx_H4=[35,+∞)` | 0.0221 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0208 |
| 13 | `rsi_H1=[50,65)` | 0.0208 |
| 14 | `session=us` | 0.0179 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0172 |

---

## NDX.INDX · pulse2
- Toplam çözülmüş: **459**  ·  Baseline win-rate: **50.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 86.5%** (32 W / 5 L = 37 trade · +35.7pp vs baseline)
   - `sar_bearish = True`
   - `dow = Fri`
   - `H4_adx_label = trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -50.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `volatility_regime ≠ normal`

**2. Win-rate 15.4%** (4 W / 22 L = 26 trade · -35.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`
   - `volatility_regime = normal`

**3. Win-rate 20.0%** (4 W / 16 L = 20 trade · -30.8pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `adx_H4 = [18,25)`

**4. Win-rate 20.0%** (4 W / 16 L = 20 trade · -30.8pp vs baseline)
   - `sar_bearish = True`
   - `dow ≠ Fri`
   - `adx_H1 = [18,25)`
   - `session_phase = mid_session`

**5. Win-rate 29.2%** (7 W / 17 L = 24 trade · -21.6pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `dow ≠ Thu`
   - `H1_ema_stack = mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=up` | 0.0392 |
| 2 | `sar_bearish=True` | 0.0347 |
| 3 | `sar_bearish=False` | 0.0333 |
| 4 | `rsi_H4=[30,50)` | 0.0318 |
| 5 | `volatility_regime=high` | 0.0261 |
| 6 | `ml_confidence_bucket=[50,60)` | 0.0246 |
| 7 | `H1_ema_stack=up` | 0.0241 |
| 8 | `rsi_H1=[30,50)` | 0.0230 |
| 9 | `dow=Fri` | 0.0225 |
| 10 | `H1_adx_label=trending` | 0.0218 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0199 |
| 12 | `H4_ema_stack=NA` | 0.0192 |
| 13 | `dxy_chg1d=[0.5,+∞)` | 0.0190 |
| 14 | `adx_H1=[18,25)` | 0.0189 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0186 |

---

## NDX.INDX · pulse2_inv
- Toplam çözülmüş: **204**  ·  Baseline win-rate: **54.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.0%** (8 W / 17 L = 25 trade · -22.4pp vs baseline)
   - `H1_ema_stack ≠ up`
   - `ml_confidence_bucket = [70,80)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0429 |
| 2 | `mtf_trend=mixed` | 0.0422 |
| 3 | `H4_ema_stack=up` | 0.0292 |
| 4 | `adx_H1=[25,35)` | 0.0270 |
| 5 | `rsi_H4=[50,65)` | 0.0250 |
| 6 | `H4_ema_stack=down` | 0.0239 |
| 7 | `hour_bucket=16-20` | 0.0237 |
| 8 | `rsi_H4=[30,50)` | 0.0229 |
| 9 | `mtf_trend=all_down` | 0.0228 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0227 |
| 11 | `H1_ema_stack=mixed` | 0.0217 |
| 12 | `session=overlap` | 0.0216 |
| 13 | `vix_chg1d=[0,3)` | 0.0215 |
| 14 | `H1_ema_stack=down` | 0.0210 |
| 15 | `H4_adx_label=trending` | 0.0209 |

---

## NDX.INDX · pulse3
- Toplam çözülmüş: **1071**  ·  Baseline win-rate: **49.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +50.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish = True`
   - `session = us`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 82.1%** (165 W / 36 L = 201 trade · +32.9pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ weak_pro`
   - `adx_H4 = [25,35)`
   - `dxy_chg1d ≠ [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 21 L = 21 trade · -49.2pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = weak_pro`
   - `H4_adx_label = trending`
   - `dow = Mon`

**2. Win-rate 6.9%** (9 W / 122 L = 131 trade · -42.3pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish ≠ True`
   - `vix_chg1d ≠ [3,+∞)`
   - `session_phase ≠ after_hours`

**3. Win-rate 19.4%** (19 W / 79 L = 98 trade · -29.8pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish = True`
   - `session ≠ us`
   - `H4_ema_stack ≠ down`

**4. Win-rate 20.0%** (4 W / 16 L = 20 trade · -29.2pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = weak_pro`
   - `H4_adx_label = trending`
   - `dow ≠ Mon`

**5. Win-rate 27.0%** (10 W / 27 L = 37 trade · -22.2pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `sar_bearish ≠ True`
   - `vix_chg1d = [3,+∞)`
   - `session ≠ overlap`

**6. Win-rate 27.0%** (20 W / 54 L = 74 trade · -22.2pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ weak_pro`
   - `adx_H4 ≠ [25,35)`
   - `sar_bearish ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0591 |
| 2 | `adx_H1=[35,+∞)` | 0.0403 |
| 3 | `sar_bearish=False` | 0.0321 |
| 4 | `dow=Tue` | 0.0319 |
| 5 | `H1_adx_label=weak_trend` | 0.0292 |
| 6 | `sar_bearish=True` | 0.0262 |
| 7 | `H1_ema_stack=up` | 0.0261 |
| 8 | `H1_ema_stack=mixed` | 0.0243 |
| 9 | `adx_H1=[18,25)` | 0.0241 |
| 10 | `rsi_H1=[65,75)` | 0.0216 |
| 11 | `overbought=True` | 0.0213 |
| 12 | `adx_H4=[35,+∞)` | 0.0212 |
| 13 | `dow=Fri` | 0.0202 |
| 14 | `macro_alignment=strong_pro` | 0.0196 |
| 15 | `adx_H4=[25,35)` | 0.0193 |

---

## NDX.INDX · pulse3_inv
- Toplam çözülmüş: **453**  ·  Baseline win-rate: **53.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +46.6pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack ≠ down`
   - `adx_H1 = [18,25)`
   - `H4_ema_stack ≠ mixed`

**2. Win-rate 79.6%** (39 W / 10 L = 49 trade · +26.2pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack ≠ down`
   - `adx_H1 = [18,25)`
   - `H4_ema_stack = mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.1%** (3 W / 30 L = 33 trade · -44.3pp vs baseline)
   - `dow = Fri`
   - `hour_bucket = 16-20`

**2. Win-rate 22.6%** (7 W / 24 L = 31 trade · -30.8pp vs baseline)
   - `dow ≠ Fri`
   - `H4_ema_stack = down`
   - `session = us`
   - `session_phase = mid_session`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0.5,+∞)` | 0.0438 |
| 2 | `H4_ema_stack=down` | 0.0383 |
| 3 | `H4_adx_label=trending` | 0.0357 |
| 4 | `dow=Fri` | 0.0349 |
| 5 | `H1_adx_label=weak_trend` | 0.0289 |
| 6 | `adx_H1=[18,25)` | 0.0283 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0239 |
| 8 | `regime_label=ranging` | 0.0222 |
| 9 | `adx_H4=[−∞,18)` | 0.0218 |
| 10 | `volatility_regime=high` | 0.0208 |
| 11 | `H4_adx_label=ranging` | 0.0204 |
| 12 | `H4_ema_stack=up` | 0.0202 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0201 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0200 |
| 15 | `session=us` | 0.0191 |

---

## NDX.INDX · smc
- Toplam çözülmüş: **98**  ·  Baseline win-rate: **28.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.5%** (1 W / 21 L = 22 trade · -24.1pp vs baseline)
   - `dow = Wed`
   - `H1_ema_stack = down`

**2. Win-rate 15.0%** (3 W / 17 L = 20 trade · -13.6pp vs baseline)
   - `dow = Wed`
   - `H1_ema_stack ≠ down`

**3. Win-rate 28.6%** (6 W / 15 L = 21 trade · 0.0pp vs baseline)
   - `dow ≠ Wed`
   - `H1_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.0858 |
| 2 | `macro_alignment=weak_pro` | 0.0692 |
| 3 | `adx_H1=[−∞,18)` | 0.0604 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0558 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0555 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0516 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0446 |
| 8 | `H1_adx_label=trending` | 0.0426 |
| 9 | `H1_adx_label=ranging` | 0.0391 |
| 10 | `adx_H4=[35,+∞)` | 0.0365 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0332 |
| 12 | `adx_H1=[25,35)` | 0.0276 |
| 13 | `H1_ema_stack=up` | 0.0269 |
| 14 | `adx_H4=[25,35)` | 0.0267 |
| 15 | `session_phase=close_drive` | 0.0245 |

---

## USOIL.FOREX · ai_panel
- Toplam çözülmüş: **102**  ·  Baseline win-rate: **55.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +29.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dxy_chg1d = [-0.5,0)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +19.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.4%** (4 W / 19 L = 23 trade · -38.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.1104 |
| 2 | `mtf_trend=mixed` | 0.0559 |
| 3 | `M30_ema_stack=down` | 0.0541 |
| 4 | `H1_ema_stack=down` | 0.0510 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0430 |
| 6 | `bb_pctb_M30=[0.5,0.8)` | 0.0397 |
| 7 | `mtf_trend=all_down` | 0.0385 |
| 8 | `rsi_H4=[50,65)` | 0.0374 |
| 9 | `rsi_H1=[50,65)` | 0.0302 |
| 10 | `H4_ema_stack=down` | 0.0245 |
| 11 | `rsi_H1=[30,50)` | 0.0240 |
| 12 | `dist_high_M30=[0.7,1.5)` | 0.0228 |
| 13 | `atr_ratio_M30=[1,1.3)` | 0.0225 |
| 14 | `M30_ema_stack=up` | 0.0222 |
| 15 | `vix_chg1d=[-3,0)` | 0.0189 |

---

## USOIL.FOREX · emel
- Toplam çözülmüş: **213**  ·  Baseline win-rate: **34.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +48.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -34.3pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label = trending`

**2. Win-rate 4.5%** (1 W / 21 L = 22 trade · -29.8pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label ≠ trending`

**3. Win-rate 28.6%** (8 W / 20 L = 28 trade · -5.7pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0815 |
| 2 | `H1_ema_stack=up` | 0.0604 |
| 3 | `H4_ema_stack=mixed` | 0.0565 |
| 4 | `mtf_trend=all_down` | 0.0516 |
| 5 | `H4_adx_label=trending` | 0.0499 |
| 6 | `H1_ema_stack=down` | 0.0424 |
| 7 | `rsi_M30=[30,50)` | 0.0399 |
| 8 | `mtf_trend=mixed` | 0.0369 |
| 9 | `rsi_H4=[65,75)` | 0.0292 |
| 10 | `dow=Mon` | 0.0274 |
| 11 | `adx_H4=[−∞,18)` | 0.0231 |
| 12 | `H4_adx_label=ranging` | 0.0227 |
| 13 | `M30_ema_stack=down` | 0.0215 |
| 14 | `rsi_H4=[30,50)` | 0.0200 |
| 15 | `regime_label=ranging` | 0.0196 |

---

## USOIL.FOREX · meta
- Toplam çözülmüş: **512**  ·  Baseline win-rate: **58.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (73 W / 0 L = 73 trade · +41.8pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 ≠ [−∞,18)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 90.9%** (30 W / 3 L = 33 trade · +32.7pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 = [−∞,18)`
   - `dow = Wed`

**3. Win-rate 84.2%** (128 W / 24 L = 152 trade · +26.0pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 ≠ [−∞,18)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d ≠ [−∞,-3)`

**4. Win-rate 77.8%** (42 W / 12 L = 54 trade · +19.6pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 ≠ [−∞,18)`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `adx_H4 = [18,25)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 54 L = 54 trade · -58.2pp vs baseline)
   - `M30_ema_stack = up`
   - `session ≠ us`
   - `H4_ema_stack = down`

**2. Win-rate 5.1%** (2 W / 37 L = 39 trade · -53.1pp vs baseline)
   - `M30_ema_stack = up`
   - `session ≠ us`
   - `H4_ema_stack ≠ down`

**3. Win-rate 8.0%** (2 W / 23 L = 25 trade · -50.2pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 = [−∞,18)`
   - `dow ≠ Wed`
   - `macd_atr_M30 = [0,0.3)`

**4. Win-rate 13.0%** (3 W / 20 L = 23 trade · -45.2pp vs baseline)
   - `M30_ema_stack = up`
   - `session = us`

**5. Win-rate 22.6%** (7 W / 24 L = 31 trade · -35.6pp vs baseline)
   - `M30_ema_stack ≠ up`
   - `adx_H1 = [−∞,18)`
   - `dow ≠ Wed`
   - `macd_atr_M30 ≠ [0,0.3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=up` | 0.0929 |
| 2 | `mtf_trend=all_down` | 0.0699 |
| 3 | `mtf_trend=mixed` | 0.0583 |
| 4 | `rsi_H4=[50,65)` | 0.0513 |
| 5 | `rsi_H4=[30,50)` | 0.0500 |
| 6 | `M30_ema_stack=down` | 0.0436 |
| 7 | `rsi_H1=[50,65)` | 0.0422 |
| 8 | `rsi_H1=[30,50)` | 0.0325 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0261 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0260 |
| 11 | `rsi_M30=[30,50)` | 0.0255 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0200 |
| 13 | `H1_adx_label=weak_trend` | 0.0184 |
| 14 | `H1_ema_stack=up` | 0.0163 |
| 15 | `H4_ema_stack=mixed` | 0.0154 |

---

## USOIL.FOREX · ml:aggressive
- Toplam çözülmüş: **630**  ·  Baseline win-rate: **48.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (79 W / 4 L = 83 trade · +47.1pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 92.0%** (23 W / 2 L = 25 trade · +43.9pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 90.9%** (20 W / 2 L = 22 trade · +42.8pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack ≠ up`
   - `macd_atr_M30 = [0,0.3)`

**4. Win-rate 78.3%** (18 W / 5 L = 23 trade · +30.2pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -48.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -43.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -34.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 25.5%** (14 W / 41 L = 55 trade · -22.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack = up`
   - `H4_adx_label = weak_trend`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · -18.1pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0723 |
| 2 | `mtf_trend=mixed` | 0.0666 |
| 3 | `mtf_trend=all_down` | 0.0619 |
| 4 | `rsi_H4=[50,65)` | 0.0367 |
| 5 | `dow=Mon` | 0.0297 |
| 6 | `rsi_H1=[50,65)` | 0.0288 |
| 7 | `H4_ema_stack=down` | 0.0251 |
| 8 | `rsi_H1=[30,50)` | 0.0244 |
| 9 | `M30_adx_label=trending` | 0.0206 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0197 |
| 11 | `H1_ema_stack=down` | 0.0185 |
| 12 | `H4_ema_stack=mixed` | 0.0176 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0174 |
| 14 | `M30_ema_stack=up` | 0.0173 |
| 15 | `M30_ema_stack=mixed` | 0.0161 |

---

## USOIL.FOREX · ml:balanced
- Toplam çözülmüş: **629**  ·  Baseline win-rate: **48.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (79 W / 4 L = 83 trade · +47.2pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 87.5%** (21 W / 3 L = 24 trade · +39.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `H1_adx_label = trending`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +30.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -48.0pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -43.0pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 12.8%** (6 W / 41 L = 47 trade · -35.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `macro_alignment ≠ neutral`

**4. Win-rate 14.0%** (8 W / 49 L = 57 trade · -34.0pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0767 |
| 2 | `M30_ema_stack=down` | 0.0736 |
| 3 | `mtf_trend=all_down` | 0.0717 |
| 4 | `rsi_H4=[50,65)` | 0.0325 |
| 5 | `rsi_H1=[30,50)` | 0.0299 |
| 6 | `rsi_H1=[50,65)` | 0.0299 |
| 7 | `H4_ema_stack=down` | 0.0292 |
| 8 | `dow=Mon` | 0.0251 |
| 9 | `H1_ema_stack=down` | 0.0226 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0200 |
| 11 | `M30_adx_label=trending` | 0.0173 |
| 12 | `rsi_M30=[30,50)` | 0.0163 |
| 13 | `H4_ema_stack=mixed` | 0.0157 |
| 14 | `M30_ema_stack=mixed` | 0.0153 |
| 15 | `rsi_H4=[30,50)` | 0.0151 |

---

## USOIL.FOREX · ml:full_power
- Toplam çözülmüş: **627**  ·  Baseline win-rate: **48.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (79 W / 4 L = 83 trade · +46.9pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 90.9%** (20 W / 2 L = 22 trade · +42.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack ≠ up`
   - `macd_atr_M30 = [0,0.3)`

**3. Win-rate 87.5%** (21 W / 3 L = 24 trade · +39.2pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `H1_adx_label = trending`

**4. Win-rate 78.3%** (18 W / 5 L = 23 trade · +30.0pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -48.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -43.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -34.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 25.5%** (14 W / 41 L = 55 trade · -22.8pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack = up`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0757 |
| 2 | `mtf_trend=mixed` | 0.0751 |
| 3 | `mtf_trend=all_down` | 0.0603 |
| 4 | `rsi_H4=[50,65)` | 0.0340 |
| 5 | `rsi_H1=[30,50)` | 0.0316 |
| 6 | `rsi_H1=[50,65)` | 0.0305 |
| 7 | `dow=Mon` | 0.0286 |
| 8 | `H4_ema_stack=down` | 0.0280 |
| 9 | `H1_ema_stack=down` | 0.0227 |
| 10 | `ml_confidence_bucket=[70,80)` | 0.0209 |
| 11 | `M30_adx_label=trending` | 0.0202 |
| 12 | `rsi_M30=[50,65)` | 0.0188 |
| 13 | `rsi_H4=[30,50)` | 0.0164 |
| 14 | `H4_ema_stack=mixed` | 0.0164 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0157 |

---

## USOIL.FOREX · ml:main
- Toplam çözülmüş: **633**  ·  Baseline win-rate: **47.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (79 W / 4 L = 83 trade · +47.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 92.0%** (23 W / 2 L = 25 trade · +44.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 87.0%** (20 W / 3 L = 23 trade · +39.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack ≠ up`
   - `macd_atr_M30 = [0,0.3)`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · +31.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -47.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -42.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -33.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 25.5%** (14 W / 41 L = 55 trade · -22.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack = up`
   - `H4_adx_label = weak_trend`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · -17.7pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0793 |
| 2 | `M30_ema_stack=down` | 0.0742 |
| 3 | `mtf_trend=all_down` | 0.0580 |
| 4 | `rsi_H4=[50,65)` | 0.0368 |
| 5 | `rsi_H1=[30,50)` | 0.0322 |
| 6 | `H4_ema_stack=down` | 0.0309 |
| 7 | `dow=Mon` | 0.0278 |
| 8 | `rsi_H1=[50,65)` | 0.0270 |
| 9 | `M30_adx_label=trending` | 0.0235 |
| 10 | `H1_ema_stack=down` | 0.0189 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0179 |
| 12 | `rsi_H4=[30,50)` | 0.0171 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0153 |
| 14 | `H4_ema_stack=mixed` | 0.0152 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0149 |

---

## USOIL.FOREX · ml:ultra_safe
- Toplam çözülmüş: **633**  ·  Baseline win-rate: **47.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (79 W / 4 L = 83 trade · +47.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 92.0%** (23 W / 2 L = 25 trade · +44.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 87.0%** (20 W / 3 L = 23 trade · +39.3pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack ≠ up`
   - `macd_atr_M30 = [0,0.3)`

**4. Win-rate 79.2%** (19 W / 5 L = 24 trade · +31.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -47.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 = [50,65)`

**2. Win-rate 5.0%** (1 W / 19 L = 20 trade · -42.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ mixed`
   - `rsi_H4 ≠ [50,65)`

**3. Win-rate 14.0%** (8 W / 49 L = 57 trade · -33.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `M30_ema_stack = mixed`
   - `ml_confidence_bucket ≠ [50,60)`

**4. Win-rate 25.5%** (14 W / 41 L = 55 trade · -22.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `H1_ema_stack = up`
   - `H4_adx_label = weak_trend`

**5. Win-rate 30.0%** (6 W / 14 L = 20 trade · -17.7pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0778 |
| 2 | `M30_ema_stack=down` | 0.0729 |
| 3 | `mtf_trend=all_down` | 0.0557 |
| 4 | `rsi_H4=[50,65)` | 0.0414 |
| 5 | `rsi_H1=[30,50)` | 0.0314 |
| 6 | `dow=Mon` | 0.0283 |
| 7 | `rsi_H1=[50,65)` | 0.0282 |
| 8 | `H4_ema_stack=down` | 0.0263 |
| 9 | `H1_ema_stack=down` | 0.0244 |
| 10 | `H4_ema_stack=mixed` | 0.0222 |
| 11 | `M30_adx_label=trending` | 0.0213 |
| 12 | `ml_confidence_bucket=[70,80)` | 0.0170 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0164 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0149 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0143 |

---

## USOIL.FOREX · pulse1
- Toplam çözülmüş: **3127**  ·  Baseline win-rate: **37.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (33 W / 3 L = 36 trade · +54.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket = [80,+∞)`
   - `macro_alignment = neutral`

**2. Win-rate 84.6%** (219 W / 40 L = 259 trade · +47.1pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label ≠ trending`
   - `sar_bearish = True`

**3. Win-rate 81.8%** (27 W / 6 L = 33 trade · +44.3pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label = trending`
   - `session_phase ≠ off_hours`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.1%** (6 W / 68 L = 74 trade · -29.4pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d = [3,+∞)`
   - `M30_adx_label ≠ trending`
   - `adx_M30 ≠ [18,25)`

**2. Win-rate 12.8%** (67 W / 457 L = 524 trade · -24.7pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_ema_stack ≠ up`

**3. Win-rate 20.1%** (56 W / 223 L = 279 trade · -17.4pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = strong_against`

**4. Win-rate 27.4%** (34 W / 90 L = 124 trade · -10.1pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H4_adx_label ≠ weak_trend`

**5. Win-rate 28.2%** (11 W / 28 L = 39 trade · -9.3pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H4_adx_label = trending`
   - `regime_label ≠ strong_trend_down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0627 |
| 2 | `consec_red_M30=[2,4)` | 0.0542 |
| 3 | `consec_green_M30=[0,2)` | 0.0387 |
| 4 | `bb_pctb_M30=[−∞,0.2)` | 0.0218 |
| 5 | `H4_adx_label=trending` | 0.0202 |
| 6 | `adx_M30=[35,+∞)` | 0.0199 |
| 7 | `consec_green_M30=[2,4)` | 0.0193 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0185 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0178 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0169 |
| 11 | `dist_high_M30=[0.3,0.7)` | 0.0166 |
| 12 | `bb_extreme_lower=True` | 0.0164 |
| 13 | `macro_alignment=strong_against` | 0.0139 |
| 14 | `us10y_chg1d=[-0.5,0)` | 0.0137 |
| 15 | `rsi_H4=[30,50)` | 0.0121 |

---

## USOIL.FOREX · pulse2
- Toplam çözülmüş: **1762**  ·  Baseline win-rate: **47.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (265 W / 9 L = 274 trade · +49.0pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label = trending`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `regime_label ≠ strong_trend_down`

**2. Win-rate 87.5%** (35 W / 5 L = 40 trade · +39.8pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label = trending`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 = [25,35)`

**3. Win-rate 84.1%** (53 W / 10 L = 63 trade · +36.4pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 ≠ [50,65)`
   - `dow = Tue`

**4. Win-rate 82.8%** (53 W / 11 L = 64 trade · +35.1pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label = trending`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `regime_label = strong_trend_down`

**5. Win-rate 79.7%** (59 W / 15 L = 74 trade · +32.0pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack ≠ down`
   - `adx_H4 = [−∞,18)`
   - `consec_green_M30 = [0,2)`

**6. Win-rate 75.8%** (25 W / 8 L = 33 trade · +28.1pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `vix_chg1d = [0,3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.0%** (11 W / 355 L = 366 trade · -44.7pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `rsi_M30 ≠ [30,50)`

**2. Win-rate 11.1%** (3 W / 24 L = 27 trade · -36.6pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `vix_chg1d ≠ [0,3)`

**3. Win-rate 14.3%** (3 W / 18 L = 21 trade · -33.4pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `dow = Tue`

**4. Win-rate 19.0%** (4 W / 17 L = 21 trade · -28.7pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `M30_adx_label ≠ trending`
   - `rsi_H1 = [50,65)`
   - `dow ≠ Tue`

**5. Win-rate 23.5%** (8 W / 26 L = 34 trade · -24.2pp vs baseline)
   - `mtf_trend = mixed`
   - `H4_ema_stack = down`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `rsi_M30 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0800 |
| 2 | `mtf_trend=mixed` | 0.0712 |
| 3 | `M30_ema_stack=down` | 0.0509 |
| 4 | `H4_ema_stack=down` | 0.0360 |
| 5 | `M30_adx_label=trending` | 0.0308 |
| 6 | `rsi_H1=[50,65)` | 0.0297 |
| 7 | `rsi_H4=[50,65)` | 0.0269 |
| 8 | `H4_ema_stack=mixed` | 0.0266 |
| 9 | `rsi_M30=[30,50)` | 0.0241 |
| 10 | `rsi_H1=[30,50)` | 0.0205 |
| 11 | `rsi_M30=[50,65)` | 0.0186 |
| 12 | `M30_adx_label=ranging` | 0.0180 |
| 13 | `dist_high_M30=[1.5,+∞)` | 0.0169 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0168 |
| 15 | `adx_M30=[35,+∞)` | 0.0154 |

---

## USOIL.FOREX · pulse3
- Toplam çözülmüş: **2665**  ·  Baseline win-rate: **49.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.9%** (562 W / 43 L = 605 trade · +43.8pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_extreme_upper ≠ True`

**2. Win-rate 92.2%** (142 W / 12 L = 154 trade · +43.1pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `regime_label = ranging`
   - `rsi_M30 = [30,50)`

**3. Win-rate 90.5%** (76 W / 8 L = 84 trade · +41.4pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment = neutral`
   - `us10y_chg1d ≠ [-0.5,0)`

**4. Win-rate 82.4%** (61 W / 13 L = 74 trade · +33.3pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.2%** (22 W / 333 L = 355 trade · -42.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label ≠ trending`
   - `H4_ema_stack = down`

**2. Win-rate 8.0%** (4 W / 46 L = 50 trade · -41.1pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment ≠ neutral`
   - `bb_pctb_M30 = [0.2,0.5)`

**3. Win-rate 16.2%** (13 W / 67 L = 80 trade · -32.9pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label = trending`
   - `rsi_H1 = [30,50)`

**4. Win-rate 19.6%** (60 W / 246 L = 306 trade · -29.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 = [50,65)`
   - `H4_adx_label ≠ trending`
   - `H4_ema_stack ≠ down`

**5. Win-rate 23.1%** (6 W / 20 L = 26 trade · -26.0pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_extreme_upper = True`

**6. Win-rate 24.6%** (88 W / 269 L = 357 trade · -24.5pp vs baseline)
   - `M30_ema_stack ≠ down`
   - `rsi_H4 ≠ [50,65)`
   - `regime_label ≠ ranging`
   - `macro_alignment = neutral`

**7. Win-rate 28.4%** (19 W / 48 L = 67 trade · -20.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow ≠ Mon`
   - `us10y_chg1d = [0.5,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

**8. Win-rate 34.4%** (11 W / 21 L = 32 trade · -14.7pp vs baseline)
   - `M30_ema_stack = down`
   - `dow = Mon`
   - `macro_alignment = neutral`
   - `us10y_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0640 |
| 2 | `M30_ema_stack=down` | 0.0611 |
| 3 | `rsi_H4=[50,65)` | 0.0565 |
| 4 | `mtf_trend=mixed` | 0.0523 |
| 5 | `rsi_H4=[30,50)` | 0.0404 |
| 6 | `M30_ema_stack=up` | 0.0269 |
| 7 | `H1_ema_stack=down` | 0.0246 |
| 8 | `rsi_H1=[50,65)` | 0.0223 |
| 9 | `M30_adx_label=trending` | 0.0211 |
| 10 | `rsi_H1=[30,50)` | 0.0197 |
| 11 | `M30_adx_label=ranging` | 0.0195 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0176 |
| 13 | `adx_M30=[−∞,18)` | 0.0163 |
| 14 | `H4_ema_stack=mixed` | 0.0159 |
| 15 | `dow=Mon` | 0.0158 |

---

## USOIL.FOREX · smc
- Toplam çözülmüş: **435**  ·  Baseline win-rate: **40.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (41 W / 0 L = 41 trade · +59.1pp vs baseline)
   - `M30_ema_stack = mixed`
   - `H1_ema_stack = down`
   - `vix_chg1d = [0,3)`
   - `adx_M30 = [35,+∞)`

**2. Win-rate 91.7%** (22 W / 2 L = 24 trade · +50.8pp vs baseline)
   - `M30_ema_stack = mixed`
   - `H1_ema_stack = down`
   - `vix_chg1d = [0,3)`
   - `adx_M30 ≠ [35,+∞)`

**3. Win-rate 86.4%** (19 W / 3 L = 22 trade · +45.5pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `adx_M30 = [−∞,18)`
   - `adx_H4 ≠ [25,35)`
   - `macd_atr_M30 ≠ [0,0.3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 2.9%** (2 W / 66 L = 68 trade · -38.0pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `adx_M30 ≠ [−∞,18)`
   - `adx_H1 ≠ [−∞,18)`
   - `adx_H4 = [−∞,18)`

**2. Win-rate 8.3%** (2 W / 22 L = 24 trade · -32.6pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `adx_M30 ≠ [−∞,18)`
   - `adx_H1 = [−∞,18)`
   - `session = europe`

**3. Win-rate 14.6%** (7 W / 41 L = 48 trade · -26.3pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `adx_M30 ≠ [−∞,18)`
   - `adx_H1 ≠ [−∞,18)`
   - `adx_H4 ≠ [−∞,18)`

**4. Win-rate 15.4%** (4 W / 22 L = 26 trade · -25.5pp vs baseline)
   - `M30_ema_stack ≠ mixed`
   - `adx_M30 = [−∞,18)`
   - `adx_H4 = [25,35)`

**5. Win-rate 20.0%** (4 W / 16 L = 20 trade · -20.9pp vs baseline)
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ down`
   - `hour_bucket = 04-08`

**6. Win-rate 29.6%** (8 W / 19 L = 27 trade · -11.3pp vs baseline)
   - `M30_ema_stack = mixed`
   - `H1_ema_stack ≠ down`
   - `hour_bucket ≠ 04-08`
   - `M30_adx_label = ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=mixed` | 0.0644 |
| 2 | `vix_chg1d=[0,3)` | 0.0503 |
| 3 | `M30_ema_stack=down` | 0.0428 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0428 |
| 5 | `rsi_H1=[50,65)` | 0.0322 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0305 |
| 7 | `mtf_trend=all_down` | 0.0301 |
| 8 | `mtf_trend=mixed` | 0.0243 |
| 9 | `rsi_H1=[30,50)` | 0.0228 |
| 10 | `dow=Mon` | 0.0227 |
| 11 | `H1_ema_stack=down` | 0.0221 |
| 12 | `dist_high_M30=[0.7,1.5)` | 0.0190 |
| 13 | `adx_H1=[−∞,18)` | 0.0183 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0172 |
| 15 | `M30_adx_label=ranging` | 0.0170 |

---

## XAUUSD · ai_panel
- Toplam çözülmüş: **171**  ·  Baseline win-rate: **64.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.2%** (31 W / 3 L = 34 trade · +26.3pp vs baseline)
   - `consec_green_M30 = [0,2)`
   - `adx_H1 = [18,25)`

**2. Win-rate 80.0%** (48 W / 12 L = 60 trade · +15.1pp vs baseline)
   - `consec_green_M30 = [0,2)`
   - `adx_H1 ≠ [18,25)`
   - `M30_ema_stack ≠ up`
   - `atr_ratio_M30 ≠ [1,1.3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 35.0%** (7 W / 13 L = 20 trade · -29.9pp vs baseline)
   - `consec_green_M30 = [0,2)`
   - `adx_H1 ≠ [18,25)`
   - `M30_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_green_M30=[0,2)` | 0.0608 |
| 2 | `H1_adx_label=weak_trend` | 0.0548 |
| 3 | `rsi_M30=[50,65)` | 0.0461 |
| 4 | `adx_H1=[18,25)` | 0.0385 |
| 5 | `sar_bearish=False` | 0.0339 |
| 6 | `bb_pctb_M30=[−∞,0.2)` | 0.0310 |
| 7 | `dist_low_M30=[0.3,0.7)` | 0.0282 |
| 8 | `H1_adx_label=trending` | 0.0270 |
| 9 | `rsi_M30=[30,50)` | 0.0262 |
| 10 | `sar_bearish=True` | 0.0251 |
| 11 | `near_support=False` | 0.0249 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0247 |
| 13 | `consec_green_M30=[2,4)` | 0.0228 |
| 14 | `mtf_trend=all_up` | 0.0207 |
| 15 | `dist_low_M30=[0.7,1.5)` | 0.0170 |

---

## XAUUSD · emel
- Toplam çözülmüş: **216**  ·  Baseline win-rate: **80.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +19.4pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 = [1,1.3)`
   - `M30_ema_stack = down`

**2. Win-rate 95.7%** (22 W / 1 L = 23 trade · +15.1pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +14.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack = down`
   - `adx_H1 ≠ [25,35)`

**4. Win-rate 95.2%** (20 W / 1 L = 21 trade · +14.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 = [1,1.3)`
   - `M30_ema_stack ≠ down`

**5. Win-rate 86.4%** (19 W / 3 L = 22 trade · +5.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack = down`
   - `adx_H1 = [25,35)`

**6. Win-rate 78.4%** (29 W / 8 L = 37 trade · -2.2pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack ≠ down`
   - `dxy_chg1d = [0,0.5)`

**7. Win-rate 78.4%** (29 W / 8 L = 37 trade · -2.2pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macd_atr_M30 = [-0.3,0)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[-0.5,0)` | 0.0716 |
| 2 | `adx_H1=[35,+∞)` | 0.0670 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0539 |
| 4 | `macro_alignment=weak_against` | 0.0453 |
| 5 | `mtf_trend=all_down` | 0.0379 |
| 6 | `M30_ema_stack=down` | 0.0305 |
| 7 | `consec_red_M30=[2,4)` | 0.0298 |
| 8 | `adx_M30=[35,+∞)` | 0.0283 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0257 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0238 |
| 11 | `consec_red_M30=[0,2)` | 0.0209 |
| 12 | `atr_ratio_M30=[0.7,1)` | 0.0192 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0191 |
| 14 | `macd_atr_M30=[0,0.3)` | 0.0186 |
| 15 | `sar_bearish=True` | 0.0186 |

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
- Toplam çözülmüş: **492**  ·  Baseline win-rate: **47.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.5%** (22 W / 5 L = 27 trade · +34.3pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 76.3%** (29 W / 9 L = 38 trade · +29.1pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.0%** (1 W / 19 L = 20 trade · -42.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_pro`
   - `rsi_M30 ≠ [50,65)`

**2. Win-rate 20.0%** (4 W / 16 L = 20 trade · -27.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_pro`
   - `rsi_M30 = [50,65)`

**3. Win-rate 27.8%** (20 W / 52 L = 72 trade · -19.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_pro`
   - `rsi_H1 ≠ [30,50)`

**4. Win-rate 28.6%** (6 W / 15 L = 21 trade · -18.6pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket = [80,+∞)`
   - `M30_adx_label ≠ trending`

**5. Win-rate 31.6%** (12 W / 26 L = 38 trade · -15.6pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket = 04-08`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket ≠ 04-08`
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0420 |
| 2 | `macro_alignment=weak_pro` | 0.0279 |
| 3 | `macro_alignment=weak_against` | 0.0251 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0235 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0211 |
| 6 | `rsi_H1=[50,65)` | 0.0209 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0208 |
| 8 | `rsi_M30=[50,65)` | 0.0198 |
| 9 | `sar_bearish=True` | 0.0192 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0182 |
| 11 | `bb_extreme_lower=True` | 0.0180 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0175 |
| 13 | `hour_bucket=12-16` | 0.0175 |
| 14 | `ml_confidence_bucket=[50,60)` | 0.0174 |
| 15 | `consec_red_M30=[2,4)` | 0.0166 |

---

## XAUUSD · ml:balanced
- Toplam çözülmüş: **494**  ·  Baseline win-rate: **47.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.5%** (22 W / 5 L = 27 trade · +34.5pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 76.3%** (29 W / 9 L = 38 trade · +29.3pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.1%** (14 W / 68 L = 82 trade · -29.9pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ neutral`

**2. Win-rate 30.0%** (6 W / 14 L = 20 trade · -17.0pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket = [80,+∞)`
   - `dist_low_M30 = [0.7,1.5)`

**3. Win-rate 31.6%** (12 W / 26 L = 38 trade · -15.4pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket = 04-08`

**4. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket ≠ 04-08`
   - `dow = Fri`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0567 |
| 2 | `macro_alignment=weak_pro` | 0.0366 |
| 3 | `macro_alignment=weak_against` | 0.0251 |
| 4 | `sar_bearish=True` | 0.0246 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0238 |
| 6 | `rsi_M30=[50,65)` | 0.0212 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0212 |
| 8 | `near_support=True` | 0.0187 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0186 |
| 10 | `consec_green_M30=[0,2)` | 0.0186 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0182 |
| 12 | `consec_red_M30=[2,4)` | 0.0180 |
| 13 | `rsi_M30=[30,50)` | 0.0170 |
| 14 | `dist_low_M30=[−∞,0.3)` | 0.0167 |
| 15 | `rsi_H1=[50,65)` | 0.0158 |

---

## XAUUSD · ml:full_power
- Toplam çözülmüş: **490**  ·  Baseline win-rate: **46.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.5%** (22 W / 5 L = 27 trade · +34.8pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 = [−∞,30)`

**2. Win-rate 76.3%** (29 W / 9 L = 38 trade · +29.6pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.7%** (14 W / 65 L = 79 trade · -29.0pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ neutral`

**2. Win-rate 23.8%** (5 W / 16 L = 21 trade · -22.9pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `rsi_H1 ≠ [−∞,30)`
   - `ml_confidence_bucket = [80,+∞)`
   - `M30_adx_label ≠ trending`

**3. Win-rate 30.4%** (7 W / 16 L = 23 trade · -16.3pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket ≠ 04-08`
   - `dow = Fri`

**4. Win-rate 31.6%** (12 W / 26 L = 38 trade · -15.1pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket = 04-08`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0374 |
| 2 | `macro_alignment=weak_pro` | 0.0270 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0225 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0216 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0192 |
| 6 | `rsi_M30=[50,65)` | 0.0190 |
| 7 | `macro_alignment=weak_against` | 0.0190 |
| 8 | `sar_bearish=True` | 0.0185 |
| 9 | `rsi_H1=[30,50)` | 0.0170 |
| 10 | `rsi_M30=[30,50)` | 0.0169 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0169 |
| 12 | `rsi_H1=[50,65)` | 0.0169 |
| 13 | `consec_red_M30=[0,2)` | 0.0169 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0165 |
| 15 | `dist_low_M30=[−∞,0.3)` | 0.0158 |

---

## XAUUSD · ml:main
- Toplam çözülmüş: **493**  ·  Baseline win-rate: **47.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.2%** (32 W / 6 L = 38 trade · +36.9pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.3%** (9 W / 50 L = 59 trade · -32.0pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ weak_against`
   - `dxy_chg1d ≠ [-0.5,0)`

**2. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.5pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket = [80,+∞)`
   - `M30_adx_label ≠ trending`

**3. Win-rate 33.7%** (33 W / 65 L = 98 trade · -13.6pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `vix_chg1d ≠ [3,+∞)`
   - `rsi_M30 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0577 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0256 |
| 3 | `macro_alignment=weak_pro` | 0.0234 |
| 4 | `macro_alignment=weak_against` | 0.0208 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0199 |
| 6 | `ml_confidence_bucket=[80,+∞)` | 0.0199 |
| 7 | `consec_red_M30=[2,4)` | 0.0193 |
| 8 | `rsi_M30=[50,65)` | 0.0192 |
| 9 | `rsi_M30=[30,50)` | 0.0189 |
| 10 | `consec_green_M30=[0,2)` | 0.0177 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0172 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0171 |
| 13 | `consec_red_M30=[0,2)` | 0.0167 |
| 14 | `ml_confidence_bucket=[60,70)` | 0.0164 |
| 15 | `sar_bearish=True` | 0.0158 |

---

## XAUUSD · ml:main_inv
- Toplam çözülmüş: **272**  ·  Baseline win-rate: **49.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.1%** (40 W / 7 L = 47 trade · +35.8pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment ≠ weak_pro`
   - `session = asia`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (5 W / 20 L = 25 trade · -29.3pp vs baseline)
   - `consec_red_M30 = [2,4)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 23.8%** (5 W / 16 L = 21 trade · -25.5pp vs baseline)
   - `consec_red_M30 ≠ [2,4)`
   - `macro_alignment = weak_pro`
   - `atr_ratio_M30 = [0.7,1)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `consec_red_M30=[0,2)` | 0.0515 |
| 2 | `consec_red_M30=[2,4)` | 0.0487 |
| 3 | `macro_alignment=weak_pro` | 0.0369 |
| 4 | `hour_bucket=00-04` | 0.0274 |
| 5 | `session=asia` | 0.0266 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0243 |
| 7 | `macro_alignment=weak_against` | 0.0229 |
| 8 | `adx_H1=[35,+∞)` | 0.0217 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0217 |
| 10 | `dist_low_M30=[−∞,0.3)` | 0.0209 |
| 11 | `M30_ema_stack=up` | 0.0201 |
| 12 | `adx_M30=[35,+∞)` | 0.0194 |
| 13 | `ml_confidence_bucket=[60,70)` | 0.0191 |
| 14 | `bb_pctb_M30=[−∞,0.2)` | 0.0182 |
| 15 | `H1_adx_label=trending` | 0.0176 |

---

## XAUUSD · ml:ultra_safe
- Toplam çözülmüş: **491**  ·  Baseline win-rate: **47.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (32 W / 7 L = 39 trade · +35.1pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label ≠ trending`

**2. Win-rate 76.2%** (16 W / 5 L = 21 trade · +29.2pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `M30_adx_label = trending`
   - `rsi_H1 = [−∞,30)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 17.5%** (14 W / 66 L = 80 trade · -29.5pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `macro_alignment ≠ neutral`

**2. Win-rate 30.8%** (12 W / 27 L = 39 trade · -16.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket = 04-08`

**3. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.2pp vs baseline)
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dxy_chg1d = [-0.5,0)`
   - `hour_bucket ≠ 04-08`
   - `dow = Fri`

**4. Win-rate 31.8%** (7 W / 15 L = 22 trade · -15.2pp vs baseline)
   - `bb_pctb_M30 = [−∞,0.2)`
   - `ml_confidence_bucket = [80,+∞)`
   - `M30_adx_label ≠ trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0488 |
| 2 | `macro_alignment=weak_pro` | 0.0273 |
| 3 | `rsi_M30=[50,65)` | 0.0248 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0221 |
| 5 | `rsi_M30=[30,50)` | 0.0220 |
| 6 | `macro_alignment=weak_against` | 0.0190 |
| 7 | `consec_red_M30=[0,2)` | 0.0185 |
| 8 | `consec_green_M30=[0,2)` | 0.0184 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0183 |
| 10 | `sar_bearish=True` | 0.0181 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0180 |
| 12 | `rsi_H1=[30,50)` | 0.0178 |
| 13 | `ml_confidence_bucket=[50,60)` | 0.0175 |
| 14 | `macd_atr_M30=[0,0.3)` | 0.0166 |
| 15 | `hour_bucket=12-16` | 0.0163 |

---

## XAUUSD · ml_cross_xau_nasdaq
- Toplam çözülmüş: **853**  ·  Baseline win-rate: **39.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 83.7%** (139 W / 27 L = 166 trade · +44.1pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ weak_pro`

**2. Win-rate 76.2%** (16 W / 5 L = 21 trade · +36.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket = 00-04`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 67 L = 67 trade · -39.6pp vs baseline)
   - `mtf_trend = all_down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 18.5%** (25 W / 110 L = 135 trade · -21.1pp vs baseline)
   - `mtf_trend = all_down`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `hour_bucket ≠ 16-20`

**3. Win-rate 20.0%** (7 W / 28 L = 35 trade · -19.6pp vs baseline)
   - `mtf_trend = all_down`
   - `dist_low_M30 = [1.5,+∞)`
   - `ml_confidence_bucket = [−∞,50)`

**4. Win-rate 23.6%** (37 W / 120 L = 157 trade · -16.0pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 12-16`

**5. Win-rate 26.1%** (12 W / 34 L = 46 trade · -13.5pp vs baseline)
   - `mtf_trend = all_down`
   - `dist_low_M30 = [1.5,+∞)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `H1_adx_label ≠ trending`

**6. Win-rate 29.4%** (10 W / 24 L = 34 trade · -10.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [65,75)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0550 |
| 2 | `macro_alignment=weak_against` | 0.0422 |
| 3 | `adx_M30=[35,+∞)` | 0.0420 |
| 4 | `M30_ema_stack=down` | 0.0419 |
| 5 | `dist_high_M30=[1.5,+∞)` | 0.0361 |
| 6 | `dxy_chg1d=[0.5,+∞)` | 0.0359 |
| 7 | `M30_ema_stack=NA` | 0.0313 |
| 8 | `macro_alignment=weak_pro` | 0.0305 |
| 9 | `mtf_trend=NA` | 0.0281 |
| 10 | `H1_adx_label=ranging` | 0.0268 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0210 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0204 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0203 |
| 14 | `adx_H1=[−∞,18)` | 0.0193 |
| 15 | `M30_adx_label=trending` | 0.0176 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv
- Toplam çözülmüş: **618**  ·  Baseline win-rate: **28.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 63 L = 63 trade · -28.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment = weak_pro`
   - `mtf_trend ≠ all_up`

**2. Win-rate 13.6%** (9 W / 57 L = 66 trade · -14.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment ≠ weak_pro`
   - `volatility_regime = normal`
   - `adx_H1 = [35,+∞)`

**3. Win-rate 20.0%** (4 W / 16 L = 20 trade · -8.2pp vs baseline)
   - `mtf_trend = all_down`
   - `ml_confidence_bucket ≠ [60,70)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dist_high_M30 ≠ [0.7,1.5)`

**4. Win-rate 23.1%** (9 W / 30 L = 39 trade · -5.1pp vs baseline)
   - `mtf_trend = all_down`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 25.6%** (53 W / 154 L = 207 trade · -2.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment ≠ weak_pro`
   - `volatility_regime = normal`
   - `adx_H1 ≠ [35,+∞)`

**6. Win-rate 28.1%** (9 W / 23 L = 32 trade · -0.1pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `macro_alignment = weak_pro`
   - `mtf_trend = all_up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0502 |
| 2 | `mtf_trend=all_down` | 0.0481 |
| 3 | `M30_ema_stack=down` | 0.0446 |
| 4 | `dist_high_M30=[1.5,+∞)` | 0.0438 |
| 5 | `mtf_trend=NA` | 0.0257 |
| 6 | `hour_bucket=12-16` | 0.0210 |
| 7 | `adx_H1=[35,+∞)` | 0.0183 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0171 |
| 9 | `dow=Mon` | 0.0169 |
| 10 | `M30_ema_stack=NA` | 0.0167 |
| 11 | `dist_high_M30=[0.3,0.7)` | 0.0164 |
| 12 | `macro_alignment=weak_against` | 0.0158 |
| 13 | `sar_bearish=True` | 0.0150 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0141 |
| 15 | `atr_ratio_M30=[1,1.3)` | 0.0140 |

---

## XAUUSD · pulse1
- Toplam çözülmüş: **2903**  ·  Baseline win-rate: **20.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 103 L = 103 trade · -20.2pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime = normal`
   - `us10y_chg1d ≠ [0,0.5)`

**2. Win-rate 0.9%** (1 W / 106 L = 107 trade · -19.3pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 ≠ [4,6)`
   - `dow = Thu`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 1.1%** (1 W / 94 L = 95 trade · -19.1pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket ≠ 20-24`
   - `vix_chg1d ≠ [-3,0)`

**4. Win-rate 3.7%** (1 W / 26 L = 27 trade · -16.5pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime = normal`
   - `us10y_chg1d = [0,0.5)`

**5. Win-rate 7.0%** (3 W / 40 L = 43 trade · -13.2pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket ≠ 20-24`
   - `vix_chg1d = [-3,0)`

**6. Win-rate 8.3%** (2 W / 22 L = 24 trade · -11.9pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 = [4,6)`
   - `volatility_regime ≠ normal`

**7. Win-rate 11.6%** (58 W / 442 L = 500 trade · -8.6pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 ≠ [4,6)`
   - `dow ≠ Thu`
   - `adx_M30 ≠ [25,35)`

**8. Win-rate 12.1%** (66 W / 481 L = 547 trade · -8.1pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack ≠ NA`
   - `sar_bearish = True`
   - `dow ≠ Tue`

**9. Win-rate 13.6%** (3 W / 19 L = 22 trade · -6.6pp vs baseline)
   - `consec_red_M30 = [0,2)`
   - `M30_ema_stack = NA`
   - `hour_bucket = 20-24`

**10. Win-rate 14.6%** (6 W / 35 L = 41 trade · -5.6pp vs baseline)
   - `consec_red_M30 ≠ [0,2)`
   - `consec_red_M30 ≠ [4,6)`
   - `dow = Thu`
   - `us10y_chg1d = [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `bb_pctb_M30=[−∞,0.2)` | 0.0318 |
| 2 | `sar_bearish=True` | 0.0267 |
| 3 | `consec_green_M30=[2,4)` | 0.0248 |
| 4 | `consec_red_M30=[0,2)` | 0.0238 |
| 5 | `sar_bearish=False` | 0.0234 |
| 6 | `M30_ema_stack=down` | 0.0232 |
| 7 | `M30_ema_stack=NA` | 0.0201 |
| 8 | `mtf_trend=all_down` | 0.0196 |
| 9 | `dow=Tue` | 0.0194 |
| 10 | `H1_adx_label=weak_trend` | 0.0187 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0183 |
| 12 | `rsi_M30=[65,75)` | 0.0180 |
| 13 | `adx_H1=[18,25)` | 0.0180 |
| 14 | `dow=Fri` | 0.0174 |
| 15 | `bb_extreme_lower=True` | 0.0173 |

---

## XAUUSD · pulse1_inv
- Toplam çözülmüş: **881**  ·  Baseline win-rate: **44.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (154 W / 44 L = 198 trade · +33.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment ≠ weak_pro`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 5.9%** (2 W / 32 L = 34 trade · -38.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 12.5%** (4 W / 28 L = 32 trade · -32.3pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `ml_confidence_bucket = [70,80)`

**3. Win-rate 25.6%** (10 W / 29 L = 39 trade · -19.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [65,75)`

**4. Win-rate 30.0%** (12 W / 28 L = 40 trade · -14.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `dxy_chg1d ≠ [0,0.5)`
   - `vix_chg1d = [3,+∞)`

**5. Win-rate 31.1%** (59 W / 131 L = 190 trade · -13.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `ml_confidence_bucket ≠ [70,80)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -13.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `dxy_chg1d = [0,0.5)`
   - `macro_alignment = weak_pro`

**7. Win-rate 32.6%** (57 W / 118 L = 175 trade · -12.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `mtf_trend ≠ NA`
   - `us10y_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0870 |
| 2 | `adx_H1=[35,+∞)` | 0.0537 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0424 |
| 4 | `M30_adx_label=trending` | 0.0332 |
| 5 | `adx_H1=[−∞,18)` | 0.0326 |
| 6 | `macro_alignment=weak_against` | 0.0310 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0289 |
| 8 | `H1_adx_label=ranging` | 0.0284 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0273 |
| 10 | `dist_high_M30=[1.5,+∞)` | 0.0223 |
| 11 | `M30_adx_label=weak_trend` | 0.0161 |
| 12 | `rsi_H1=[65,75)` | 0.0153 |
| 13 | `adx_H1=[25,35)` | 0.0150 |
| 14 | `adx_M30=[18,25)` | 0.0146 |
| 15 | `H1_adx_label=trending` | 0.0138 |

---

## XAUUSD · pulse2
- Toplam çözülmüş: **2626**  ·  Baseline win-rate: **21.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +78.1pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 = [65,75)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 66 L = 66 trade · -21.9pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = NA`
   - `vix_chg1d ≠ [0,3)`
   - `ml_confidence_bucket = [−∞,50)`

**2. Win-rate 1.9%** (4 W / 209 L = 213 trade · -20.0pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d = [−∞,-3)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**3. Win-rate 7.7%** (2 W / 24 L = 26 trade · -14.2pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = NA`
   - `vix_chg1d = [0,3)`
   - `macro_alignment = strong_against`

**4. Win-rate 10.0%** (2 W / 18 L = 20 trade · -11.9pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = NA`
   - `vix_chg1d ≠ [0,3)`
   - `ml_confidence_bucket ≠ [−∞,50)`

**5. Win-rate 10.9%** (50 W / 408 L = 458 trade · -11.0pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `adx_M30 = [35,+∞)`

**6. Win-rate 11.1%** (29 W / 233 L = 262 trade · -10.8pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend ≠ NA`
   - `vix_chg1d = [3,+∞)`
   - `hour_bucket ≠ 16-20`

**7. Win-rate 14.1%** (13 W / 79 L = 92 trade · -7.8pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d = [−∞,-3)`
   - `dist_low_M30 = [1.5,+∞)`

**8. Win-rate 14.3%** (3 W / 18 L = 21 trade · -7.6pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 = [65,75)`
   - `dow ≠ Fri`
   - `dist_high_M30 ≠ [0.7,1.5)`

**9. Win-rate 20.0%** (4 W / 16 L = 20 trade · -1.9pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `mtf_trend = NA`
   - `vix_chg1d = [0,3)`
   - `macro_alignment ≠ strong_against`

**10. Win-rate 20.5%** (110 W / 427 L = 537 trade · -1.4pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[-0.5,0)` | 0.0383 |
| 2 | `dist_low_M30=[1.5,+∞)` | 0.0258 |
| 3 | `dow=Tue` | 0.0253 |
| 4 | `dow=Wed` | 0.0248 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0248 |
| 6 | `dow=Fri` | 0.0247 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0241 |
| 8 | `H1_adx_label=weak_trend` | 0.0235 |
| 9 | `M30_ema_stack=NA` | 0.0211 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0200 |
| 11 | `rsi_M30=[65,75)` | 0.0187 |
| 12 | `adx_H1=[35,+∞)` | 0.0173 |
| 13 | `adx_H1=[18,25)` | 0.0173 |
| 14 | `bb_pctb_M30=[−∞,0.2)` | 0.0173 |
| 15 | `mtf_trend=NA` | 0.0169 |

---

## XAUUSD · pulse2_inv
- Toplam çözülmüş: **859**  ·  Baseline win-rate: **43.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (29 W / 1 L = 30 trade · +53.6pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 ≠ [25,35)`
   - `adx_M30 = [35,+∞)`
   - `dow = Tue`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.8%** (11 W / 69 L = 80 trade · -29.3pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `macro_alignment = weak_pro`

**2. Win-rate 23.2%** (22 W / 73 L = 95 trade · -19.9pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `ml_confidence_bucket = [−∞,50)`
   - `adx_M30 ≠ [35,+∞)`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 28.6%** (8 W / 20 L = 28 trade · -14.5pp vs baseline)
   - `macro_alignment = weak_against`
   - `adx_H1 = [25,35)`

**4. Win-rate 31.9%** (87 W / 186 L = 273 trade · -11.2pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `macro_alignment ≠ weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0670 |
| 2 | `ml_confidence_bucket=[−∞,50)` | 0.0631 |
| 3 | `macro_alignment=weak_pro` | 0.0514 |
| 4 | `adx_M30=[35,+∞)` | 0.0494 |
| 5 | `ml_confidence_bucket=[80,+∞)` | 0.0410 |
| 6 | `adx_H1=[35,+∞)` | 0.0232 |
| 7 | `mtf_trend=NA` | 0.0219 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0215 |
| 9 | `adx_M30=[18,25)` | 0.0204 |
| 10 | `M30_ema_stack=NA` | 0.0191 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0172 |
| 12 | `adx_M30=[25,35)` | 0.0153 |
| 13 | `M30_adx_label=trending` | 0.0150 |
| 14 | `H1_adx_label=trending` | 0.0145 |
| 15 | `M30_adx_label=weak_trend` | 0.0144 |

---

## XAUUSD · pulse3
- Toplam çözülmüş: **2802**  ·  Baseline win-rate: **23.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.0%** (99 W / 2 L = 101 trade · +74.3pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `dow = Fri`
   - `adx_M30 = [35,+∞)`
   - `macd_atr_M30 = [-0.3,0)`

**2. Win-rate 81.1%** (30 W / 7 L = 37 trade · +57.4pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `dow = Fri`
   - `adx_M30 = [35,+∞)`
   - `macd_atr_M30 ≠ [-0.3,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 170 L = 170 trade · -23.7pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `dow ≠ Tue`

**2. Win-rate 1.6%** (2 W / 122 L = 124 trade · -22.1pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend ≠ all_down`
   - `us10y_chg1d = [0.5,+∞)`
   - `hour_bucket ≠ 12-16`

**3. Win-rate 2.9%** (1 W / 33 L = 34 trade · -20.8pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `dow = Tue`

**4. Win-rate 6.0%** (13 W / 204 L = 217 trade · -17.7pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `bb_extreme_lower ≠ False`

**5. Win-rate 9.7%** (9 W / 84 L = 93 trade · -14.0pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend ≠ all_down`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `M30_ema_stack = NA`

**6. Win-rate 10.0%** (3 W / 27 L = 30 trade · -13.7pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `dow = Fri`
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ strong_pro`

**7. Win-rate 10.6%** (5 W / 42 L = 47 trade · -13.1pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend ≠ all_down`
   - `us10y_chg1d = [0.5,+∞)`
   - `hour_bucket = 12-16`

**8. Win-rate 11.2%** (34 W / 269 L = 303 trade · -12.5pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Mon`

**9. Win-rate 14.8%** (62 W / 356 L = 418 trade · -8.9pp vs baseline)
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `bb_extreme_lower = False`

**10. Win-rate 21.0%** (69 W / 259 L = 328 trade · -2.7pp vs baseline)
   - `dist_low_M30 = [1.5,+∞)`
   - `dow ≠ Fri`
   - `vix_chg1d ≠ [3,+∞)`
   - `dxy_chg1d ≠ [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=up` | 0.0410 |
| 2 | `mtf_trend=all_down` | 0.0357 |
| 3 | `M30_ema_stack=down` | 0.0319 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0317 |
| 5 | `dist_low_M30=[1.5,+∞)` | 0.0303 |
| 6 | `mtf_trend=all_up` | 0.0284 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0283 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0253 |
| 9 | `dow=Fri` | 0.0233 |
| 10 | `adx_H1=[35,+∞)` | 0.0196 |
| 11 | `rsi_M30=[50,65)` | 0.0188 |
| 12 | `rsi_H1=[65,75)` | 0.0184 |
| 13 | `rsi_M30=[65,75)` | 0.0183 |
| 14 | `rsi_M30=[30,50)` | 0.0177 |
| 15 | `dow=Wed` | 0.0173 |

---

## XAUUSD · pulse3_inv
- Toplam çözülmüş: **813**  ·  Baseline win-rate: **39.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 75.2%** (118 W / 39 L = 157 trade · +35.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_up`
   - `macro_alignment ≠ weak_pro`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.4%** (12 W / 116 L = 128 trade · -30.5pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ True`
   - `volatility_regime = normal`
   - `vix_chg1d ≠ [0,3)`

**2. Win-rate 19.0%** (4 W / 17 L = 21 trade · -20.9pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper = True`
   - `mtf_trend ≠ all_up`

**3. Win-rate 22.0%** (9 W / 32 L = 41 trade · -17.9pp vs baseline)
   - `sar_bearish = False`
   - `bb_extreme_upper ≠ True`
   - `volatility_regime = normal`
   - `vix_chg1d = [0,3)`

**4. Win-rate 30.5%** (61 W / 139 L = 200 trade · -9.4pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `near_support = False`
   - `M30_adx_label ≠ ranging`

**5. Win-rate 30.6%** (11 W / 25 L = 36 trade · -9.3pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 ≠ [35,+∞)`
   - `near_support ≠ False`
   - `dxy_chg1d ≠ [0,0.5)`

**6. Win-rate 34.0%** (16 W / 31 L = 47 trade · -5.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `mtf_trend = all_up`
   - `dist_low_M30 ≠ [0.7,1.5)`

**7. Win-rate 35.0%** (7 W / 13 L = 20 trade · -4.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `adx_M30 = [35,+∞)`
   - `mtf_trend ≠ all_up`
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0776 |
| 2 | `sar_bearish=True` | 0.0654 |
| 3 | `adx_H1=[35,+∞)` | 0.0447 |
| 4 | `macro_alignment=weak_pro` | 0.0341 |
| 5 | `macro_alignment=weak_against` | 0.0335 |
| 6 | `rsi_H1=[30,50)` | 0.0291 |
| 7 | `adx_M30=[35,+∞)` | 0.0287 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0246 |
| 9 | `adx_M30=[25,35)` | 0.0217 |
| 10 | `rsi_H1=[50,65)` | 0.0212 |
| 11 | `rsi_M30=[50,65)` | 0.0201 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0192 |
| 13 | `adx_H1=[25,35)` | 0.0180 |
| 14 | `rsi_M30=[30,50)` | 0.0166 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0137 |

---

## XAUUSD · smc
- Toplam çözülmüş: **509**  ·  Baseline win-rate: **42.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (27 W / 0 L = 27 trade · +58.0pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**2. Win-rate 96.4%** (27 W / 1 L = 28 trade · +54.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_H1 = [30,50)`
   - `macro_alignment = weak_against`
   - `us10y_chg1d = [0,0.5)`

**3. Win-rate 90.5%** (19 W / 2 L = 21 trade · +48.5pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `atr_ratio_M30 = [1,1.3)`

**4. Win-rate 81.6%** (40 W / 9 L = 49 trade · +39.6pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 = [1.5,+∞)`
   - `atr_ratio_M30 = [0.7,1)`
   - `H1_adx_label ≠ trending`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 8.6%** (9 W / 96 L = 105 trade · -33.4pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_H1 ≠ [30,50)`
   - `adx_M30 ≠ [25,35)`
   - `consec_green_M30 ≠ [2,4)`

**2. Win-rate 16.2%** (12 W / 62 L = 74 trade · -25.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `rsi_H1 = [30,50)`
   - `macro_alignment ≠ weak_against`
   - `bb_pctb_M30 ≠ [0.2,0.5)`

**3. Win-rate 28.1%** (9 W / 23 L = 32 trade · -13.9pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `dist_high_M30 ≠ [1.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.1185 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0481 |
| 3 | `M30_ema_stack=down` | 0.0438 |
| 4 | `mtf_trend=all_down` | 0.0353 |
| 5 | `dist_high_M30=[1.5,+∞)` | 0.0336 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0279 |
| 7 | `vix_chg1d=[-3,0)` | 0.0228 |
| 8 | `H1_adx_label=weak_trend` | 0.0208 |
| 9 | `rsi_H1=[30,50)` | 0.0199 |
| 10 | `bb_pctb_M30=[0.2,0.5)` | 0.0188 |
| 11 | `adx_M30=[25,35)` | 0.0178 |
| 12 | `macro_alignment=weak_against` | 0.0173 |
| 13 | `adx_M30=[35,+∞)` | 0.0170 |
| 14 | `M30_ema_stack=up` | 0.0167 |
| 15 | `adx_H1=[18,25)` | 0.0163 |

---

## XAUUSD · smc_inv
- Toplam çözülmüş: **198**  ·  Baseline win-rate: **48.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 81.4%** (35 W / 8 L = 43 trade · +33.4pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `dxy_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -38.0pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `adx_H1 = [35,+∞)`

**2. Win-rate 26.7%** (8 W / 22 L = 30 trade · -21.3pp vs baseline)
   - `ml_confidence_bucket = [70,80)`
   - `us10y_chg1d = [0,0.5)`

**3. Win-rate 34.5%** (10 W / 19 L = 29 trade · -13.5pp vs baseline)
   - `ml_confidence_bucket ≠ [70,80)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_high_M30=[1.5,+∞)` | 0.0920 |
| 2 | `ml_confidence_bucket=[70,80)` | 0.0625 |
| 3 | `macro_alignment=weak_against` | 0.0402 |
| 4 | `dow=Tue` | 0.0387 |
| 5 | `mtf_trend=mixed` | 0.0368 |
| 6 | `us10y_chg1d=[0,0.5)` | 0.0289 |
| 7 | `dist_high_M30=[0.7,1.5)` | 0.0272 |
| 8 | `dow=Wed` | 0.0256 |
| 9 | `us10y_chg1d=[0.5,+∞)` | 0.0251 |
| 10 | `atr_ratio_M30=[0.7,1)` | 0.0248 |
| 11 | `vix_chg1d=[0,3)` | 0.0226 |
| 12 | `H1_adx_label=trending` | 0.0205 |
| 13 | `M30_ema_stack=mixed` | 0.0198 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0195 |
| 15 | `hour_bucket=16-20` | 0.0177 |

---

## GDAXI.INDX · meta · BUY
- Toplam çözülmüş: **243**  ·  Baseline win-rate: **43.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.7%** (22 W / 1 L = 23 trade · +52.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [0,0.5)`
   - `H4_ema_stack ≠ NA`
   - `macro_alignment = neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.3%** (1 W / 22 L = 23 trade · -39.3pp vs baseline)
   - `sar_bearish = False`
   - `dow ≠ Fri`
   - `session ≠ overlap`
   - `bb_extreme_upper = True`

**2. Win-rate 23.7%** (14 W / 45 L = 59 trade · -19.9pp vs baseline)
   - `sar_bearish = False`
   - `dow ≠ Fri`
   - `session ≠ overlap`
   - `bb_extreme_upper ≠ True`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0864 |
| 2 | `sar_bearish=True` | 0.0626 |
| 3 | `rsi_H1=[30,50)` | 0.0469 |
| 4 | `adx_H1=[18,25)` | 0.0456 |
| 5 | `H1_adx_label=weak_trend` | 0.0382 |
| 6 | `adx_H4=[−∞,18)` | 0.0371 |
| 7 | `macro_alignment=neutral` | 0.0236 |
| 8 | `H4_adx_label=ranging` | 0.0235 |
| 9 | `adx_H4=[18,25)` | 0.0210 |
| 10 | `us10y_chg1d=[-0.5,0)` | 0.0209 |
| 11 | `regime_label=ranging` | 0.0203 |
| 12 | `H4_adx_label=weak_trend` | 0.0193 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0190 |
| 14 | `volatility_regime=normal` | 0.0177 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0164 |

---

## GDAXI.INDX · meta · SELL
- Toplam çözülmüş: **122**  ·  Baseline win-rate: **53.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (32 W / 7 L = 39 trade · +28.8pp vs baseline)
   - `H1_adx_label = trending`
   - `H1_ema_stack ≠ mixed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.4%** (6 W / 22 L = 28 trade · -31.9pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `rsi_H4 ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=weak_trend` | 0.0750 |
| 2 | `H1_adx_label=trending` | 0.0745 |
| 3 | `adx_H1=[18,25)` | 0.0616 |
| 4 | `adx_H1=[25,35)` | 0.0407 |
| 5 | `dow=Mon` | 0.0390 |
| 6 | `dow=Fri` | 0.0322 |
| 7 | `sar_bearish=False` | 0.0306 |
| 8 | `H4_ema_stack=mixed` | 0.0299 |
| 9 | `H1_ema_stack=down` | 0.0298 |
| 10 | `H1_ema_stack=mixed` | 0.0297 |
| 11 | `dow=Wed` | 0.0278 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0269 |
| 13 | `regime_label=ranging` | 0.0262 |
| 14 | `bb_extreme_lower=True` | 0.0208 |
| 15 | `adx_H4=[−∞,18)` | 0.0204 |

---

## GDAXI.INDX · ml:balanced · BUY
- Toplam çözülmüş: **144**  ·  Baseline win-rate: **62.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.6%** (28 W / 1 L = 29 trade · +34.1pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`

**2. Win-rate 75.0%** (15 W / 5 L = 20 trade · +12.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 ≠ [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 34.3%** (12 W / 23 L = 35 trade · -28.2pp vs baseline)
   - `sar_bearish = False`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0661 |
| 2 | `sar_bearish=True` | 0.0624 |
| 3 | `rsi_H1=[30,50)` | 0.0583 |
| 4 | `rsi_H1=[50,65)` | 0.0493 |
| 5 | `H4_ema_stack=up` | 0.0483 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0400 |
| 7 | `H1_adx_label=ranging` | 0.0379 |
| 8 | `adx_H1=[−∞,18)` | 0.0352 |
| 9 | `volatility_regime=high` | 0.0344 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0337 |
| 11 | `H1_ema_stack=down` | 0.0299 |
| 12 | `vix_chg1d=[0,3)` | 0.0297 |
| 13 | `volatility_regime=normal` | 0.0233 |
| 14 | `us10y_chg1d=[−∞,-0.5)` | 0.0218 |
| 15 | `macro_alignment=strong_against` | 0.0207 |

---

## GDAXI.INDX · ml:full_power · BUY
- Toplam çözülmüş: **157**  ·  Baseline win-rate: **55.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.6%** (28 W / 1 L = 29 trade · +41.2pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (4 W / 22 L = 26 trade · -40.0pp vs baseline)
   - `sar_bearish = False`
   - `adx_H4 = [18,25)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1048 |
| 2 | `sar_bearish=False` | 0.0989 |
| 3 | `rsi_H1=[30,50)` | 0.0912 |
| 4 | `H4_ema_stack=up` | 0.0466 |
| 5 | `rsi_H1=[50,65)` | 0.0414 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0294 |
| 7 | `bb_extreme_lower=False` | 0.0290 |
| 8 | `vix_chg1d=[0,3)` | 0.0283 |
| 9 | `adx_H1=[−∞,18)` | 0.0280 |
| 10 | `H4_adx_label=weak_trend` | 0.0249 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0231 |
| 12 | `bb_extreme_lower=True` | 0.0208 |
| 13 | `H1_ema_stack=mixed` | 0.0205 |
| 14 | `vix_chg1d=[−∞,-3)` | 0.0205 |
| 15 | `bb_extreme_upper=True` | 0.0202 |

---

## GDAXI.INDX · ml:main · BUY
- Toplam çözülmüş: **158**  ·  Baseline win-rate: **55.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.6%** (28 W / 1 L = 29 trade · +41.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `H4_ema_stack = up`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (4 W / 22 L = 26 trade · -39.7pp vs baseline)
   - `sar_bearish = False`
   - `H4_adx_label = weak_trend`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1099 |
| 2 | `sar_bearish=False` | 0.1003 |
| 3 | `H4_ema_stack=up` | 0.0580 |
| 4 | `rsi_H1=[30,50)` | 0.0485 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0460 |
| 6 | `rsi_H1=[50,65)` | 0.0422 |
| 7 | `volatility_regime=high` | 0.0323 |
| 8 | `H4_adx_label=weak_trend` | 0.0315 |
| 9 | `vix_chg1d=[0,3)` | 0.0284 |
| 10 | `rsi_H4=[50,65)` | 0.0218 |
| 11 | `H1_ema_stack=down` | 0.0208 |
| 12 | `bb_extreme_upper=True` | 0.0199 |
| 13 | `H1_ema_stack=mixed` | 0.0194 |
| 14 | `H1_adx_label=ranging` | 0.0178 |
| 15 | `bb_extreme_upper=False` | 0.0177 |

---

## GDAXI.INDX · pulse1 · BUY
- Toplam çözülmüş: **597**  ·  Baseline win-rate: **30.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 93.2%** (41 W / 3 L = 44 trade · +62.9pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `regime_label = ranging`
   - `vix_chg1d = [0,3)`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 103 L = 103 trade · -30.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `regime_label ≠ ranging`

**2. Win-rate 0.0%** (0 W / 25 L = 25 trade · -30.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 6.7%** (2 W / 28 L = 30 trade · -23.6pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d ≠ [0,3)`
   - `regime_label = ranging`

**4. Win-rate 7.8%** (5 W / 59 L = 64 trade · -22.5pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `regime_label ≠ ranging`
   - `session = europe`
   - `H4_adx_label = weak_trend`

**5. Win-rate 26.9%** (7 W / 19 L = 26 trade · -3.4pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `regime_label = ranging`
   - `vix_chg1d ≠ [0,3)`
   - `sar_bearish = False`

**6. Win-rate 28.2%** (20 W / 51 L = 71 trade · -2.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `regime_label ≠ ranging`
   - `session = europe`
   - `H4_adx_label ≠ weak_trend`

**7. Win-rate 29.5%** (23 W / 55 L = 78 trade · -0.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `regime_label ≠ ranging`
   - `session ≠ europe`
   - `dow ≠ Mon`

**8. Win-rate 30.0%** (9 W / 21 L = 30 trade · -0.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_adx_label ≠ NA`
   - `vix_chg1d = [0,3)`
   - `hour_bucket = 08-12`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0928 |
| 2 | `regime_label=ranging` | 0.0441 |
| 3 | `adx_H4=[−∞,18)` | 0.0405 |
| 4 | `vix_chg1d=[0,3)` | 0.0384 |
| 5 | `H4_adx_label=weak_trend` | 0.0382 |
| 6 | `adx_H4=[18,25)` | 0.0366 |
| 7 | `sar_bearish=True` | 0.0359 |
| 8 | `bb_extreme_upper=False` | 0.0357 |
| 9 | `H4_adx_label=ranging` | 0.0303 |
| 10 | `bb_extreme_upper=True` | 0.0300 |
| 11 | `volatility_regime=normal` | 0.0276 |
| 12 | `sar_bearish=False` | 0.0256 |
| 13 | `ml_confidence_bucket=[−∞,50)` | 0.0229 |
| 14 | `dow=Fri` | 0.0213 |
| 15 | `volatility_regime=high` | 0.0193 |

---

## GDAXI.INDX · pulse1 · SELL
- Toplam çözülmüş: **287**  ·  Baseline win-rate: **25.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 41 L = 41 trade · -25.1pp vs baseline)
   - `hour_bucket = 12-16`
   - `adx_H1 ≠ [25,35)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `H4_ema_stack ≠ up`

**2. Win-rate 4.8%** (1 W / 20 L = 21 trade · -20.3pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack = up`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -20.3pp vs baseline)
   - `hour_bucket = 12-16`
   - `adx_H1 ≠ [25,35)`
   - `ml_confidence_bucket ≠ [−∞,50)`
   - `H4_ema_stack = up`

**4. Win-rate 13.8%** (4 W / 25 L = 29 trade · -11.3pp vs baseline)
   - `hour_bucket = 12-16`
   - `adx_H1 ≠ [25,35)`
   - `ml_confidence_bucket = [−∞,50)`

**5. Win-rate 14.3%** (4 W / 24 L = 28 trade · -10.8pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `H1_ema_stack = mixed`
   - `macro_alignment ≠ strong_pro`

**6. Win-rate 25.0%** (5 W / 15 L = 20 trade · -0.1pp vs baseline)
   - `hour_bucket ≠ 12-16`
   - `ml_confidence_bucket = [80,+∞)`
   - `H4_ema_stack ≠ up`

**7. Win-rate 30.0%** (12 W / 28 L = 40 trade · 4.9pp vs baseline)
   - `hour_bucket = 12-16`
   - `adx_H1 = [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[−∞,50)` | 0.0645 |
| 2 | `hour_bucket=12-16` | 0.0598 |
| 3 | `rsi_H1=[50,65)` | 0.0546 |
| 4 | `session=europe` | 0.0448 |
| 5 | `hour_bucket=08-12` | 0.0407 |
| 6 | `session=overlap` | 0.0398 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0390 |
| 8 | `rsi_H1=[30,50)` | 0.0287 |
| 9 | `H1_adx_label=trending` | 0.0275 |
| 10 | `H4_ema_stack=up` | 0.0263 |
| 11 | `volatility_regime=normal` | 0.0216 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0192 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0182 |
| 14 | `volatility_regime=high` | 0.0176 |
| 15 | `H1_ema_stack=mixed` | 0.0173 |

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
- Toplam çözülmüş: **370**  ·  Baseline win-rate: **43.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (28 W / 0 L = 28 trade · +56.2pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 = [30,50)`

**2. Win-rate 87.5%** (28 W / 4 L = 32 trade · +43.7pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label ≠ transition`
   - `rsi_H4 ≠ [30,50)`

**3. Win-rate 78.1%** (25 W / 7 L = 32 trade · +34.3pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `rsi_H1 = [30,50)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 2.9%** (1 W / 34 L = 35 trade · -40.9pp vs baseline)
   - `sar_bearish ≠ True`
   - `volatility_regime ≠ high`
   - `hour_bucket ≠ 04-08`
   - `vix_chg1d = [-3,0)`

**2. Win-rate 22.9%** (8 W / 27 L = 35 trade · -20.9pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d = [3,+∞)`

**3. Win-rate 25.4%** (29 W / 85 L = 114 trade · -18.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `volatility_regime ≠ high`
   - `hour_bucket ≠ 04-08`
   - `vix_chg1d ≠ [-3,0)`

**4. Win-rate 28.0%** (7 W / 18 L = 25 trade · -15.8pp vs baseline)
   - `sar_bearish = True`
   - `vix_chg1d ≠ [3,+∞)`
   - `regime_label = transition`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0710 |
| 2 | `sar_bearish=True` | 0.0635 |
| 3 | `regime_label=ranging` | 0.0398 |
| 4 | `H4_adx_label=ranging` | 0.0377 |
| 5 | `adx_H4=[−∞,18)` | 0.0361 |
| 6 | `bb_extreme_upper=False` | 0.0324 |
| 7 | `dow=Mon` | 0.0320 |
| 8 | `volatility_regime=high` | 0.0295 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0264 |
| 10 | `H4_adx_label=weak_trend` | 0.0248 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0207 |
| 12 | `rsi_H1=[30,50)` | 0.0205 |
| 13 | `ml_confidence_bucket=[−∞,50)` | 0.0196 |
| 14 | `regime_label=transition` | 0.0193 |
| 15 | `vix_chg1d=[0,3)` | 0.0189 |

---

## GDAXI.INDX · pulse2 · SELL
- Toplam çözülmüş: **95**  ·  Baseline win-rate: **38.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.1%** (2 W / 20 L = 22 trade · -29.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `dow ≠ Wed`
   - `H4_ema_stack = NA`

**2. Win-rate 35.0%** (7 W / 13 L = 20 trade · -3.9pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `dow ≠ Wed`
   - `H4_ema_stack ≠ NA`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Wed` | 0.0823 |
| 2 | `H4_ema_stack=up` | 0.0466 |
| 3 | `ml_confidence_bucket=[−∞,50)` | 0.0465 |
| 4 | `adx_H4=[25,35)` | 0.0421 |
| 5 | `macro_alignment=neutral` | 0.0394 |
| 6 | `H1_adx_label=weak_trend` | 0.0370 |
| 7 | `H1_adx_label=ranging` | 0.0344 |
| 8 | `adx_H4=NA` | 0.0306 |
| 9 | `H4_adx_label=NA` | 0.0293 |
| 10 | `adx_H1=[18,25)` | 0.0278 |
| 11 | `rsi_H4=NA` | 0.0272 |
| 12 | `rsi_H1=[30,50)` | 0.0266 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0261 |
| 14 | `H4_ema_stack=NA` | 0.0253 |
| 15 | `H4_adx_label=trending` | 0.0247 |

---

## GDAXI.INDX · pulse2_inv · SELL
- Toplam çözülmüş: **88**  ·  Baseline win-rate: **47.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.8%** (5 W / 16 L = 21 trade · -23.9pp vs baseline)
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=strong_pro` | 0.0698 |
| 2 | `H1_adx_label=trending` | 0.0554 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0536 |
| 4 | `mtf_trend=mixed` | 0.0528 |
| 5 | `rsi_H4=NA` | 0.0480 |
| 6 | `H4_ema_stack=up` | 0.0440 |
| 7 | `H4_adx_label=NA` | 0.0402 |
| 8 | `H4_ema_stack=NA` | 0.0336 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0315 |
| 10 | `volatility_regime=normal` | 0.0300 |
| 11 | `ml_confidence_bucket=[50,60)` | 0.0300 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0299 |
| 13 | `adx_H1=[18,25)` | 0.0297 |
| 14 | `sar_bearish=False` | 0.0276 |
| 15 | `adx_H4=NA` | 0.0274 |

---

## GDAXI.INDX · pulse3 · BUY
- Toplam çözülmüş: **519**  ·  Baseline win-rate: **34.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 40 L = 40 trade · -34.7pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_H4 ≠ NA`
   - `bb_extreme_upper = True`

**2. Win-rate 0.0%** (0 W / 32 L = 32 trade · -34.7pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `overbought = True`
   - `H4_ema_stack = up`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -24.7pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `overbought = True`
   - `H4_ema_stack ≠ up`

**4. Win-rate 13.3%** (6 W / 39 L = 45 trade · -21.4pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `overbought ≠ True`
   - `dow = Mon`
   - `vix_chg1d = [-3,0)`

**5. Win-rate 15.2%** (15 W / 84 L = 99 trade · -19.5pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_H4 ≠ NA`
   - `bb_extreme_upper ≠ True`

**6. Win-rate 24.0%** (6 W / 19 L = 25 trade · -10.7pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `adx_H4 = NA`
   - `session = europe`

**7. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.9pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `overbought ≠ True`
   - `dow ≠ Mon`
   - `rsi_H4 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `volatility_regime=normal` | 0.0450 |
| 2 | `dow=Tue` | 0.0355 |
| 3 | `overbought=True` | 0.0352 |
| 4 | `dxy_chg1d=[-0.5,0)` | 0.0348 |
| 5 | `sar_bearish=False` | 0.0276 |
| 6 | `overbought=False` | 0.0275 |
| 7 | `vix_chg1d=[0,3)` | 0.0273 |
| 8 | `H1_adx_label=ranging` | 0.0271 |
| 9 | `adx_H1=[−∞,18)` | 0.0259 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0242 |
| 11 | `rsi_H4=[30,50)` | 0.0220 |
| 12 | `H1_adx_label=weak_trend` | 0.0190 |
| 13 | `bb_extreme_upper=True` | 0.0187 |
| 14 | `dow=Fri` | 0.0187 |
| 15 | `dow=Mon` | 0.0186 |

---

## GDAXI.INDX · pulse3 · SELL
- Toplam çözülmüş: **284**  ·  Baseline win-rate: **38.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 97.4%** (38 W / 1 L = 39 trade · +58.7pp vs baseline)
   - `H1_adx_label = trending`
   - `H4_ema_stack = mixed`
   - `session = europe`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 31 L = 31 trade · -38.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `regime_label ≠ transition`
   - `session ≠ europe`

**2. Win-rate 8.7%** (2 W / 21 L = 23 trade · -30.0pp vs baseline)
   - `H1_adx_label = trending`
   - `H4_ema_stack ≠ mixed`
   - `session = europe`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -28.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `regime_label ≠ transition`
   - `session = europe`

**4. Win-rate 16.7%** (6 W / 30 L = 36 trade · -22.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `regime_label = transition`
   - `ml_confidence_bucket = [60,70)`

**5. Win-rate 20.0%** (5 W / 20 L = 25 trade · -18.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `regime_label = transition`
   - `ml_confidence_bucket ≠ [60,70)`
   - `session = overlap`

**6. Win-rate 35.0%** (7 W / 13 L = 20 trade · -3.7pp vs baseline)
   - `H1_adx_label = trending`
   - `H4_ema_stack ≠ mixed`
   - `session ≠ europe`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0869 |
| 2 | `adx_H1=[35,+∞)` | 0.0740 |
| 3 | `us10y_chg1d=[0.5,+∞)` | 0.0596 |
| 4 | `sar_bearish=True` | 0.0496 |
| 5 | `sar_bearish=False` | 0.0486 |
| 6 | `dow=Mon` | 0.0427 |
| 7 | `rsi_H1=[50,65)` | 0.0364 |
| 8 | `H4_ema_stack=mixed` | 0.0313 |
| 9 | `H1_ema_stack=down` | 0.0297 |
| 10 | `H1_ema_stack=mixed` | 0.0221 |
| 11 | `dow=Fri` | 0.0207 |
| 12 | `rsi_H4=NA` | 0.0199 |
| 13 | `adx_H1=[18,25)` | 0.0196 |
| 14 | `bb_extreme_lower=True` | 0.0191 |
| 15 | `session=overlap` | 0.0187 |

---

## GDAXI.INDX · pulse3_inv · BUY
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **44.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 28.6%** (10 W / 25 L = 35 trade · -15.8pp vs baseline)
   - `ml_confidence_bucket ≠ [60,70)`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.1163 |
| 2 | `sar_bearish=False` | 0.0443 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0425 |
| 4 | `H1_ema_stack=down` | 0.0413 |
| 5 | `H1_adx_label=trending` | 0.0354 |
| 6 | `hour_bucket=12-16` | 0.0340 |
| 7 | `ml_confidence_bucket=[50,60)` | 0.0315 |
| 8 | `H1_ema_stack=mixed` | 0.0308 |
| 9 | `adx_H1=[18,25)` | 0.0289 |
| 10 | `macro_alignment=strong_against` | 0.0286 |
| 11 | `oversold=True` | 0.0269 |
| 12 | `H1_adx_label=weak_trend` | 0.0269 |
| 13 | `rsi_H1=[−∞,30)` | 0.0265 |
| 14 | `session=europe` | 0.0254 |
| 15 | `rsi_H1=[30,50)` | 0.0254 |

---

## GDAXI.INDX · pulse3_inv · SELL
- Toplam çözülmüş: **106**  ·  Baseline win-rate: **44.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +40.7pp vs baseline)
   - `rsi_H4 ≠ NA`
   - `sar_bearish ≠ False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -34.3pp vs baseline)
   - `rsi_H4 = NA`
   - `macro_alignment ≠ neutral`
   - `session = europe`

**2. Win-rate 33.3%** (7 W / 14 L = 21 trade · -11.0pp vs baseline)
   - `rsi_H4 = NA`
   - `macro_alignment ≠ neutral`
   - `session ≠ europe`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H4=NA` | 0.0747 |
| 2 | `us10y_chg1d=[0,0.5)` | 0.0552 |
| 3 | `macro_alignment=strong_pro` | 0.0520 |
| 4 | `H4_ema_stack=NA` | 0.0460 |
| 5 | `vix_chg1d=[3,+∞)` | 0.0447 |
| 6 | `H1_adx_label=trending` | 0.0429 |
| 7 | `H4_ema_stack=up` | 0.0411 |
| 8 | `H4_adx_label=trending` | 0.0376 |
| 9 | `rsi_H4=NA` | 0.0370 |
| 10 | `H4_adx_label=NA` | 0.0369 |
| 11 | `ml_confidence_bucket=[80,+∞)` | 0.0360 |
| 12 | `rsi_H4=[75,+∞)` | 0.0330 |
| 13 | `adx_H1=[35,+∞)` | 0.0281 |
| 14 | `sar_bearish=True` | 0.0279 |
| 15 | `adx_H1=[−∞,18)` | 0.0256 |

---

## NDX.INDX · meta · BUY
- Toplam çözülmüş: **137**  ·  Baseline win-rate: **46.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +44.9pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `dxy_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -46.0pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `volatility_regime ≠ normal`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -21.0pp vs baseline)
   - `sar_bearish = False`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `volatility_regime = normal`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=True` | 0.1244 |
| 2 | `sar_bearish=False` | 0.1117 |
| 3 | `rsi_H1=[30,50)` | 0.0471 |
| 4 | `rsi_H4=[30,50)` | 0.0445 |
| 5 | `H4_ema_stack=NA` | 0.0422 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0358 |
| 7 | `us10y_chg1d=[-0.5,0)` | 0.0286 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0277 |
| 9 | `mtf_trend=all_up` | 0.0264 |
| 10 | `dow=Wed` | 0.0225 |
| 11 | `adx_H1=[18,25)` | 0.0216 |
| 12 | `near_resistance=False` | 0.0179 |
| 13 | `dxy_chg1d=[-0.5,0)` | 0.0174 |
| 14 | `H4_adx_label=trending` | 0.0167 |
| 15 | `dow=Mon` | 0.0166 |

---

## NDX.INDX · meta · SELL
- Toplam çözülmüş: **103**  ·  Baseline win-rate: **60.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.7%** (26 W / 3 L = 29 trade · +29.5pp vs baseline)
   - `H1_ema_stack = mixed`
   - `dxy_chg1d ≠ [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.9%** (7 W / 19 L = 26 trade · -33.3pp vs baseline)
   - `H1_ema_stack ≠ mixed`
   - `H4_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=mixed` | 0.1171 |
| 2 | `H1_ema_stack=down` | 0.0410 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0400 |
| 4 | `macro_alignment=strong_against` | 0.0397 |
| 5 | `dow=Thu` | 0.0396 |
| 6 | `H4_ema_stack=up` | 0.0386 |
| 7 | `rsi_H4=[30,50)` | 0.0358 |
| 8 | `sar_bearish=True` | 0.0357 |
| 9 | `sar_bearish=False` | 0.0333 |
| 10 | `H1_adx_label=trending` | 0.0333 |
| 11 | `dow=Fri` | 0.0303 |
| 12 | `H4_adx_label=weak_trend` | 0.0264 |
| 13 | `adx_H4=[25,35)` | 0.0257 |
| 14 | `regime_label=transition` | 0.0227 |
| 15 | `ml_confidence_bucket=[80,+∞)` | 0.0227 |

---

## NDX.INDX · ml:balanced · BUY
- Toplam çözülmüş: **133**  ·  Baseline win-rate: **48.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +36.9pp vs baseline)
   - `H4_ema_stack = up`
   - `dow = Wed`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.9%** (7 W / 30 L = 37 trade · -29.2pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `dow = Mon`

**2. Win-rate 27.3%** (6 W / 16 L = 22 trade · -20.8pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `dow ≠ Mon`
   - `us10y_chg1d = [−∞,-0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0632 |
| 2 | `H4_ema_stack=up` | 0.0589 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0500 |
| 4 | `sar_bearish=True` | 0.0482 |
| 5 | `H1_adx_label=ranging` | 0.0458 |
| 6 | `volatility_regime=high` | 0.0438 |
| 7 | `mtf_trend=mixed` | 0.0437 |
| 8 | `volatility_regime=normal` | 0.0362 |
| 9 | `sar_bearish=False` | 0.0358 |
| 10 | `mtf_trend=all_up` | 0.0299 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0267 |
| 12 | `rsi_H4=[30,50)` | 0.0244 |
| 13 | `adx_H1=[−∞,18)` | 0.0239 |
| 14 | `vix_chg1d=[-3,0)` | 0.0238 |
| 15 | `rsi_H1=[30,50)` | 0.0233 |

---

## NDX.INDX · ml:balanced · SELL
- Toplam çözülmüş: **124**  ·  Baseline win-rate: **58.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.3%** (17 W / 5 L = 22 trade · +18.4pp vs baseline)
   - `dow = Thu`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 33.3%** (7 W / 14 L = 21 trade · -25.6pp vs baseline)
   - `dow ≠ Thu`
   - `session_phase = mid_session`
   - `dxy_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0596 |
| 2 | `rsi_H1=[30,50)` | 0.0404 |
| 3 | `adx_H1=[25,35)` | 0.0402 |
| 4 | `H4_ema_stack=up` | 0.0356 |
| 5 | `H4_ema_stack=mixed` | 0.0354 |
| 6 | `hour_bucket=16-20` | 0.0312 |
| 7 | `vix_chg1d=[0,3)` | 0.0308 |
| 8 | `macro_alignment=strong_pro` | 0.0285 |
| 9 | `hour_bucket=12-16` | 0.0276 |
| 10 | `vix_chg1d=[−∞,-3)` | 0.0275 |
| 11 | `dow=Tue` | 0.0265 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0263 |
| 13 | `near_resistance=False` | 0.0262 |
| 14 | `sar_bearish=True` | 0.0257 |
| 15 | `dxy_chg1d=[0,0.5)` | 0.0231 |

---

## NDX.INDX · ml:full_power · BUY
- Toplam çözülmüş: **133**  ·  Baseline win-rate: **51.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (21 W / 6 L = 27 trade · +26.7pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`

**2. Win-rate 76.9%** (20 W / 6 L = 26 trade · +25.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_H4 ≠ [25,35)`
   - `adx_H4 ≠ [−∞,18)`
   - `dow ≠ Mon`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.9%** (7 W / 19 L = 26 trade · -24.2pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_H4 = [25,35)`

**2. Win-rate 30.8%** (8 W / 18 L = 26 trade · -20.3pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_H4 ≠ [25,35)`
   - `adx_H4 = [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0824 |
| 2 | `volatility_regime=normal` | 0.0640 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0545 |
| 4 | `sar_bearish=False` | 0.0462 |
| 5 | `adx_H1=[−∞,18)` | 0.0381 |
| 6 | `H4_ema_stack=up` | 0.0355 |
| 7 | `adx_H4=[35,+∞)` | 0.0315 |
| 8 | `session_phase=mid_session` | 0.0312 |
| 9 | `sar_bearish=True` | 0.0312 |
| 10 | `H1_adx_label=ranging` | 0.0294 |
| 11 | `volatility_regime=high` | 0.0273 |
| 12 | `rsi_H4=[50,65)` | 0.0240 |
| 13 | `macro_alignment=weak_pro` | 0.0233 |
| 14 | `adx_H4=[25,35)` | 0.0230 |
| 15 | `macro_alignment=neutral` | 0.0226 |

---

## NDX.INDX · ml:full_power · SELL
- Toplam çözülmüş: **134**  ·  Baseline win-rate: **58.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +27.5pp vs baseline)
   - `dow = Thu`
   - `volatility_regime = high`

**2. Win-rate 75.0%** (21 W / 7 L = 28 trade · +16.8pp vs baseline)
   - `dow ≠ Thu`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session_phase ≠ mid_session`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.0%** (8 W / 17 L = 25 trade · -26.2pp vs baseline)
   - `dow ≠ Thu`
   - `vix_chg1d = [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0680 |
| 2 | `vix_chg1d=[0,3)` | 0.0451 |
| 3 | `H1_adx_label=weak_trend` | 0.0419 |
| 4 | `macro_alignment=weak_pro` | 0.0402 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0367 |
| 6 | `rsi_H1=[30,50)` | 0.0350 |
| 7 | `dow=Tue` | 0.0333 |
| 8 | `hour_bucket=16-20` | 0.0328 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0323 |
| 10 | `H1_ema_stack=up` | 0.0301 |
| 11 | `adx_H1=[25,35)` | 0.0298 |
| 12 | `H4_ema_stack=up` | 0.0277 |
| 13 | `H1_ema_stack=down` | 0.0273 |
| 14 | `regime_label=transition` | 0.0260 |
| 15 | `session_phase=mid_session` | 0.0247 |

---

## NDX.INDX · ml:main · BUY
- Toplam çözülmüş: **134**  ·  Baseline win-rate: **50.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 77.8%** (21 W / 6 L = 27 trade · +27.1pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.1%** (2 W / 20 L = 22 trade · -41.6pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `adx_H4 ≠ [35,+∞)`
   - `H4_adx_label ≠ weak_trend`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0682 |
| 2 | `sar_bearish=False` | 0.0489 |
| 3 | `H4_ema_stack=up` | 0.0424 |
| 4 | `adx_H1=[−∞,18)` | 0.0400 |
| 5 | `sar_bearish=True` | 0.0397 |
| 6 | `volatility_regime=normal` | 0.0396 |
| 7 | `ml_confidence_bucket=[−∞,50)` | 0.0381 |
| 8 | `adx_H4=[25,35)` | 0.0371 |
| 9 | `H1_adx_label=ranging` | 0.0359 |
| 10 | `macro_alignment=neutral` | 0.0326 |
| 11 | `volatility_regime=high` | 0.0326 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0322 |
| 13 | `macro_alignment=weak_pro` | 0.0266 |
| 14 | `rsi_H1=[30,50)` | 0.0265 |
| 15 | `us10y_chg1d=[-0.5,0)` | 0.0261 |

---

## NDX.INDX · ml:main · SELL
- Toplam çözülmüş: **134**  ·  Baseline win-rate: **59.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +26.0pp vs baseline)
   - `dow = Thu`
   - `volatility_regime = high`

**2. Win-rate 78.6%** (22 W / 6 L = 28 trade · +18.9pp vs baseline)
   - `dow ≠ Thu`
   - `vix_chg1d ≠ [−∞,-3)`
   - `session_phase ≠ mid_session`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 32.0%** (8 W / 17 L = 25 trade · -27.7pp vs baseline)
   - `dow ≠ Thu`
   - `vix_chg1d = [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Thu` | 0.0456 |
| 2 | `vix_chg1d=[0,3)` | 0.0405 |
| 3 | `macro_alignment=weak_pro` | 0.0382 |
| 4 | `hour_bucket=16-20` | 0.0357 |
| 5 | `H1_adx_label=weak_trend` | 0.0346 |
| 6 | `H1_adx_label=trending` | 0.0334 |
| 7 | `H1_ema_stack=up` | 0.0329 |
| 8 | `regime_label=transition` | 0.0310 |
| 9 | `dow=Tue` | 0.0300 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0296 |
| 11 | `adx_H1=[25,35)` | 0.0289 |
| 12 | `rsi_H1=[30,50)` | 0.0273 |
| 13 | `H4_adx_label=ranging` | 0.0263 |
| 14 | `H4_ema_stack=up` | 0.0251 |
| 15 | `adx_H4=[−∞,18)` | 0.0225 |

---

## NDX.INDX · ml:main_inv · BUY
- Toplam çözülmüş: **90**  ·  Baseline win-rate: **60.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.7%** (18 W / 3 L = 21 trade · +25.7pp vs baseline)
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d = [0.5,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `rsi_H1=[30,50)` | 0.1248 |
| 2 | `adx_H4=[35,+∞)` | 0.0511 |
| 3 | `adx_H1=[25,35)` | 0.0507 |
| 4 | `H4_ema_stack=down` | 0.0417 |
| 5 | `sar_bearish=True` | 0.0384 |
| 6 | `session=overlap` | 0.0348 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0290 |
| 8 | `us10y_chg1d=[0.5,+∞)` | 0.0281 |
| 9 | `session=us` | 0.0273 |
| 10 | `hour_bucket=16-20` | 0.0260 |
| 11 | `sar_bearish=False` | 0.0253 |
| 12 | `H4_adx_label=trending` | 0.0225 |
| 13 | `macro_alignment=strong_against` | 0.0215 |
| 14 | `H1_ema_stack=down` | 0.0212 |
| 15 | `mtf_trend=mixed` | 0.0209 |

---

## NDX.INDX · pulse1 · BUY
- Toplam çözülmüş: **507**  ·  Baseline win-rate: **29.8%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -29.8pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `session ≠ overlap`

**2. Win-rate 0.0%** (0 W / 73 L = 73 trade · -29.8pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack ≠ mixed`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -25.3pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow = Mon`

**4. Win-rate 8.7%** (2 W / 21 L = 23 trade · -21.1pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label ≠ trending`
   - `H1_ema_stack = mixed`

**5. Win-rate 15.6%** (5 W / 27 L = 32 trade · -14.2pp vs baseline)
   - `ml_confidence_bucket = [80,+∞)`
   - `H1_adx_label = trending`
   - `dow ≠ Mon`
   - `macro_alignment = neutral`

**6. Win-rate 23.7%** (22 W / 71 L = 93 trade · -6.1pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `sar_bearish = False`
   - `rsi_H4 ≠ [30,50)`

**7. Win-rate 26.1%** (6 W / 17 L = 23 trade · -3.7pp vs baseline)
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `macro_alignment = weak_pro`
   - `session = overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0898 |
| 2 | `sar_bearish=False` | 0.0445 |
| 3 | `sar_bearish=True` | 0.0372 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0282 |
| 5 | `rsi_H4=[30,50)` | 0.0277 |
| 6 | `H4_ema_stack=NA` | 0.0260 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0238 |
| 8 | `macro_alignment=weak_pro` | 0.0218 |
| 9 | `session=overlap` | 0.0216 |
| 10 | `rsi_H1=[30,50)` | 0.0199 |
| 11 | `H1_ema_stack=up` | 0.0197 |
| 12 | `rsi_H1=[65,75)` | 0.0196 |
| 13 | `session=us` | 0.0194 |
| 14 | `overbought=True` | 0.0188 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0188 |

---

## NDX.INDX · pulse1 · SELL
- Toplam çözülmüş: **462**  ·  Baseline win-rate: **54.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.0%** (19 W / 1 L = 20 trade · +40.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = NA`

**2. Win-rate 92.1%** (35 W / 3 L = 38 trade · +37.8pp vs baseline)
   - `H1_adx_label = trending`
   - `dow ≠ Tue`
   - `adx_H1 = [35,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 6.2%** (3 W / 45 L = 48 trade · -48.1pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ NA`
   - `H4_adx_label = trending`
   - `adx_H1 = [−∞,18)`

**2. Win-rate 29.6%** (8 W / 19 L = 27 trade · -24.7pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ NA`
   - `H4_adx_label ≠ trending`
   - `macro_alignment = neutral`

**3. Win-rate 33.3%** (19 W / 38 L = 57 trade · -21.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ NA`
   - `H4_adx_label = trending`
   - `adx_H1 ≠ [−∞,18)`

**4. Win-rate 33.3%** (7 W / 14 L = 21 trade · -21.0pp vs baseline)
   - `H1_adx_label = trending`
   - `dow = Tue`
   - `H1_ema_stack ≠ down`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0688 |
| 2 | `H1_adx_label=ranging` | 0.0481 |
| 3 | `adx_H1=[35,+∞)` | 0.0416 |
| 4 | `adx_H1=[−∞,18)` | 0.0402 |
| 5 | `dow=Tue` | 0.0379 |
| 6 | `dow=Mon` | 0.0298 |
| 7 | `rsi_H4=[50,65)` | 0.0255 |
| 8 | `adx_H4=[25,35)` | 0.0227 |
| 9 | `H4_ema_stack=mixed` | 0.0216 |
| 10 | `H4_ema_stack=NA` | 0.0210 |
| 11 | `dow=Wed` | 0.0209 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0207 |
| 13 | `rsi_H4=[30,50)` | 0.0194 |
| 14 | `adx_H4=[18,25)` | 0.0178 |
| 15 | `bb_extreme_lower=True` | 0.0178 |

---

## NDX.INDX · pulse1_inv · BUY
- Toplam çözülmüş: **175**  ·  Baseline win-rate: **49.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 26.1%** (6 W / 17 L = 23 trade · -23.0pp vs baseline)
   - `H4_adx_label ≠ weak_trend`
   - `adx_H1 ≠ [−∞,18)`
   - `H1_ema_stack = up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `session_phase=mid_session` | 0.0378 |
| 2 | `dow=Wed` | 0.0357 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0286 |
| 4 | `H4_adx_label=weak_trend` | 0.0284 |
| 5 | `session_phase=after_hours` | 0.0277 |
| 6 | `session=overlap` | 0.0275 |
| 7 | `adx_H1=[18,25)` | 0.0260 |
| 8 | `H1_ema_stack=down` | 0.0259 |
| 9 | `dxy_chg1d=[-0.5,0)` | 0.0255 |
| 10 | `adx_H4=[18,25)` | 0.0245 |
| 11 | `hour_bucket=16-20` | 0.0244 |
| 12 | `volatility_regime=normal` | 0.0235 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0222 |
| 14 | `mtf_trend=mixed` | 0.0217 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0216 |

---

## NDX.INDX · pulse1_inv · SELL
- Toplam çözülmüş: **216**  ·  Baseline win-rate: **50.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 84.6%** (33 W / 6 L = 39 trade · +34.6pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.2%** (5 W / 28 L = 33 trade · -34.8pp vs baseline)
   - `H4_ema_stack ≠ mixed`
   - `session_phase = mid_session`
   - `dxy_chg1d = [-0.5,0)`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -25.0pp vs baseline)
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [−∞,-3)`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=mixed` | 0.0619 |
| 2 | `macro_alignment=neutral` | 0.0451 |
| 3 | `rsi_H1=[50,65)` | 0.0425 |
| 4 | `ml_confidence_bucket=[80,+∞)` | 0.0410 |
| 5 | `us10y_chg1d=[0,0.5)` | 0.0346 |
| 6 | `session_phase=mid_session` | 0.0334 |
| 7 | `vix_chg1d=[−∞,-3)` | 0.0278 |
| 8 | `adx_H4=[35,+∞)` | 0.0266 |
| 9 | `H4_ema_stack=down` | 0.0260 |
| 10 | `overbought=False` | 0.0256 |
| 11 | `dow=Fri` | 0.0251 |
| 12 | `ml_confidence_bucket=[60,70)` | 0.0234 |
| 13 | `hour_bucket=16-20` | 0.0218 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0213 |
| 15 | `rsi_H1=[65,75)` | 0.0196 |

---

## NDX.INDX · pulse2 · BUY
- Toplam çözülmüş: **232**  ·  Baseline win-rate: **41.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.3%** (24 W / 2 L = 26 trade · +50.5pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d ≠ [3,+∞)`
   - `macro_alignment = neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -41.8pp vs baseline)
   - `sar_bearish = False`
   - `rsi_H4 ≠ [30,50)`
   - `rsi_H4 ≠ [50,65)`
   - `volatility_regime ≠ normal`

**2. Win-rate 14.3%** (3 W / 18 L = 21 trade · -27.5pp vs baseline)
   - `sar_bearish = False`
   - `rsi_H4 ≠ [30,50)`
   - `rsi_H4 = [50,65)`
   - `dxy_chg1d = [-0.5,0)`

**3. Win-rate 14.8%** (4 W / 23 L = 27 trade · -27.0pp vs baseline)
   - `sar_bearish = False`
   - `rsi_H4 ≠ [30,50)`
   - `rsi_H4 ≠ [50,65)`
   - `volatility_regime = normal`

**4. Win-rate 25.8%** (8 W / 23 L = 31 trade · -16.0pp vs baseline)
   - `sar_bearish ≠ False`
   - `us10y_chg1d = [−∞,-0.5)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0923 |
| 2 | `sar_bearish=True` | 0.0844 |
| 3 | `dow=Thu` | 0.0532 |
| 4 | `dow=Wed` | 0.0389 |
| 5 | `rsi_H1=[30,50)` | 0.0363 |
| 6 | `H4_ema_stack=NA` | 0.0330 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0291 |
| 8 | `rsi_H4=[65,75)` | 0.0235 |
| 9 | `volatility_regime=high` | 0.0219 |
| 10 | `H1_ema_stack=down` | 0.0195 |
| 11 | `dow=Mon` | 0.0192 |
| 12 | `bb_extreme_upper=True` | 0.0182 |
| 13 | `H4_adx_label=trending` | 0.0172 |
| 14 | `session=us` | 0.0169 |
| 15 | `adx_H1=[25,35)` | 0.0168 |

---

## NDX.INDX · pulse2 · SELL
- Toplam çözülmüş: **227**  ·  Baseline win-rate: **59.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 91.7%** (22 W / 2 L = 24 trade · +31.8pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 82.6%** (19 W / 4 L = 23 trade · +22.7pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `bb_extreme_lower ≠ False`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.0%** (3 W / 17 L = 20 trade · -44.9pp vs baseline)
   - `dow = Tue`
   - `dxy_chg1d = [-0.5,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.0624 |
| 2 | `H4_ema_stack=up` | 0.0483 |
| 3 | `H1_ema_stack=mixed` | 0.0350 |
| 4 | `dxy_chg1d=[0.5,+∞)` | 0.0336 |
| 5 | `session=us` | 0.0309 |
| 6 | `dow=Thu` | 0.0285 |
| 7 | `dow=Fri` | 0.0282 |
| 8 | `session=overlap` | 0.0277 |
| 9 | `H4_ema_stack=mixed` | 0.0258 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0238 |
| 11 | `H1_adx_label=trending` | 0.0237 |
| 12 | `rsi_H1=[30,50)` | 0.0236 |
| 13 | `vix_chg1d=[−∞,-3)` | 0.0214 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0210 |
| 15 | `H1_ema_stack=down` | 0.0203 |

---

## NDX.INDX · pulse2_inv · BUY
- Toplam çözülmüş: **131**  ·  Baseline win-rate: **55.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 85.0%** (17 W / 3 L = 20 trade · +29.3pp vs baseline)
   - `rsi_H1 = [50,65)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[50,60)` | 0.0733 |
| 2 | `rsi_H1=[30,50)` | 0.0576 |
| 3 | `session_phase=mid_session` | 0.0438 |
| 4 | `rsi_H1=[50,65)` | 0.0424 |
| 5 | `sar_bearish=False` | 0.0422 |
| 6 | `bb_extreme_lower=False` | 0.0398 |
| 7 | `sar_bearish=True` | 0.0365 |
| 8 | `vix_chg1d=[0,3)` | 0.0339 |
| 9 | `mtf_trend=all_down` | 0.0313 |
| 10 | `bb_extreme_lower=True` | 0.0301 |
| 11 | `dow=Tue` | 0.0285 |
| 12 | `dow=Thu` | 0.0236 |
| 13 | `mtf_trend=mixed` | 0.0227 |
| 14 | `volatility_regime=high` | 0.0212 |
| 15 | `adx_H4=[35,+∞)` | 0.0212 |

---

## NDX.INDX · pulse3 · BUY
- Toplam çözülmüş: **484**  ·  Baseline win-rate: **34.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (34 W / 0 L = 34 trade · +65.9pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d = [-0.5,0)`
   - `H4_ema_stack = up`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 72 L = 72 trade · -34.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 ≠ [50,65)`

**2. Win-rate 5.9%** (2 W / 32 L = 34 trade · -28.2pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session ≠ overlap`

**3. Win-rate 8.0%** (4 W / 46 L = 50 trade · -26.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `vix_chg1d = [−∞,-3)`

**4. Win-rate 21.4%** (9 W / 33 L = 42 trade · -12.7pp vs baseline)
   - `sar_bearish = True`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `us10y_chg1d ≠ [0,0.5)`
   - `dow = Mon`

**5. Win-rate 25.0%** (7 W / 21 L = 28 trade · -9.1pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack ≠ up`
   - `vix_chg1d = [−∞,-3)`
   - `session = overlap`

**6. Win-rate 25.7%** (9 W / 26 L = 35 trade · -8.4pp vs baseline)
   - `sar_bearish ≠ True`
   - `H1_ema_stack = up`
   - `rsi_H4 = [50,65)`
   - `vix_chg1d ≠ [−∞,-3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `sar_bearish=False` | 0.0926 |
| 2 | `sar_bearish=True` | 0.0814 |
| 3 | `dow=Fri` | 0.0348 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0345 |
| 5 | `near_resistance=True` | 0.0318 |
| 6 | `overbought=False` | 0.0288 |
| 7 | `overbought=True` | 0.0253 |
| 8 | `near_resistance=False` | 0.0252 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0224 |
| 10 | `H1_ema_stack=up` | 0.0213 |
| 11 | `dow=Tue` | 0.0194 |
| 12 | `macro_alignment=weak_pro` | 0.0179 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0168 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0155 |
| 15 | `dow=Wed` | 0.0155 |

---

## NDX.INDX · pulse3 · SELL
- Toplam çözülmüş: **587**  ·  Baseline win-rate: **61.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (44 W / 0 L = 44 trade · +38.3pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 = [50,65)`

**2. Win-rate 91.3%** (21 W / 2 L = 23 trade · +29.6pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment = strong_against`
   - `rsi_H1 ≠ [50,65)`

**3. Win-rate 88.1%** (37 W / 5 L = 42 trade · +26.4pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow = Fri`
   - `session_phase ≠ mid_session`

**4. Win-rate 76.5%** (26 W / 8 L = 34 trade · +14.8pp vs baseline)
   - `H1_adx_label = trending`
   - `macro_alignment ≠ strong_against`
   - `dow ≠ Fri`
   - `us10y_chg1d = [0,0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 4.8%** (1 W / 20 L = 21 trade · -56.9pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `vix_chg1d ≠ [−∞,-3)`

**2. Win-rate 9.5%** (2 W / 19 L = 21 trade · -52.2pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack = mixed`
   - `vix_chg1d = [−∞,-3)`

**3. Win-rate 20.7%** (6 W / 23 L = 29 trade · -41.0pp vs baseline)
   - `H1_adx_label ≠ trending`
   - `H4_ema_stack ≠ mixed`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_adx_label=trending` | 0.0696 |
| 2 | `adx_H1=[−∞,18)` | 0.0454 |
| 3 | `dow=Tue` | 0.0446 |
| 4 | `H1_adx_label=ranging` | 0.0407 |
| 5 | `adx_H1=[35,+∞)` | 0.0388 |
| 6 | `H1_ema_stack=mixed` | 0.0320 |
| 7 | `macro_alignment=strong_against` | 0.0310 |
| 8 | `H4_ema_stack=up` | 0.0259 |
| 9 | `sar_bearish=True` | 0.0221 |
| 10 | `dow=Fri` | 0.0218 |
| 11 | `adx_H4=[25,35)` | 0.0197 |
| 12 | `vix_chg1d=[-3,0)` | 0.0189 |
| 13 | `adx_H4=[35,+∞)` | 0.0185 |
| 14 | `sar_bearish=False` | 0.0182 |
| 15 | `H1_adx_label=weak_trend` | 0.0181 |

---

## NDX.INDX · pulse3_inv · BUY
- Toplam çözülmüş: **237**  ·  Baseline win-rate: **55.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (21 W / 0 L = 21 trade · +44.3pp vs baseline)
   - `H4_ema_stack = up`
   - `adx_H1 = [18,25)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.3%** (9 W / 24 L = 33 trade · -28.4pp vs baseline)
   - `H4_ema_stack ≠ up`
   - `adx_H4 ≠ [35,+∞)`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0496 |
| 2 | `H4_ema_stack=up` | 0.0466 |
| 3 | `H4_ema_stack=down` | 0.0425 |
| 4 | `ml_confidence_bucket=[60,70)` | 0.0326 |
| 5 | `adx_H4=[25,35)` | 0.0310 |
| 6 | `rsi_H4=[50,65)` | 0.0309 |
| 7 | `volatility_regime=normal` | 0.0300 |
| 8 | `H1_ema_stack=up` | 0.0264 |
| 9 | `session=us` | 0.0255 |
| 10 | `volatility_regime=high` | 0.0253 |
| 11 | `H1_adx_label=trending` | 0.0243 |
| 12 | `session_phase=close_drive` | 0.0242 |
| 13 | `adx_H1=[18,25)` | 0.0242 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0224 |
| 15 | `H1_adx_label=weak_trend` | 0.0213 |

---

## NDX.INDX · pulse3_inv · SELL
- Toplam çözülmüş: **216**  ·  Baseline win-rate: **50.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 89.2%** (33 W / 4 L = 37 trade · +38.3pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `H4_ema_stack ≠ down`
   - `vix_chg1d = [−∞,-3)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 7.7%** (2 W / 24 L = 26 trade · -43.2pp vs baseline)
   - `dxy_chg1d = [0.5,+∞)`

**2. Win-rate 21.7%** (5 W / 18 L = 23 trade · -29.2pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `H4_ema_stack = down`
   - `hour_bucket ≠ 12-16`
   - `macro_alignment = weak_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Fri` | 0.0639 |
| 2 | `dxy_chg1d=[0.5,+∞)` | 0.0522 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0372 |
| 4 | `overbought=False` | 0.0341 |
| 5 | `dxy_chg1d=[0,0.5)` | 0.0327 |
| 6 | `hour_bucket=16-20` | 0.0307 |
| 7 | `overbought=True` | 0.0306 |
| 8 | `session=overlap` | 0.0295 |
| 9 | `rsi_H1=[50,65)` | 0.0294 |
| 10 | `H4_ema_stack=mixed` | 0.0293 |
| 11 | `vix_chg1d=[−∞,-3)` | 0.0273 |
| 12 | `adx_H1=[18,25)` | 0.0228 |
| 13 | `ml_confidence_bucket=[70,80)` | 0.0212 |
| 14 | `adx_H4=[−∞,18)` | 0.0201 |
| 15 | `H4_ema_stack=up` | 0.0200 |

---

## USOIL.FOREX · emel · BUY
- Toplam çözülmüş: **213**  ·  Baseline win-rate: **34.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.8%** (24 W / 5 L = 29 trade · +48.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `session ≠ overlap`
   - `macro_alignment ≠ neutral`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -34.3pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label = trending`

**2. Win-rate 4.5%** (1 W / 21 L = 22 trade · -29.8pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label ≠ trending`
   - `H1_adx_label ≠ trending`

**3. Win-rate 28.6%** (8 W / 20 L = 28 trade · -5.7pp vs baseline)
   - `H4_ema_stack = down`
   - `dow ≠ Mon`
   - `H4_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0815 |
| 2 | `H1_ema_stack=up` | 0.0604 |
| 3 | `H4_ema_stack=mixed` | 0.0565 |
| 4 | `mtf_trend=all_down` | 0.0516 |
| 5 | `H4_adx_label=trending` | 0.0499 |
| 6 | `H1_ema_stack=down` | 0.0424 |
| 7 | `rsi_M30=[30,50)` | 0.0399 |
| 8 | `mtf_trend=mixed` | 0.0369 |
| 9 | `rsi_H4=[65,75)` | 0.0292 |
| 10 | `dow=Mon` | 0.0274 |
| 11 | `adx_H4=[−∞,18)` | 0.0231 |
| 12 | `H4_adx_label=ranging` | 0.0227 |
| 13 | `M30_ema_stack=down` | 0.0215 |
| 14 | `rsi_H4=[30,50)` | 0.0200 |
| 15 | `regime_label=ranging` | 0.0196 |

---

## USOIL.FOREX · meta · BUY
- Toplam çözülmüş: **161**  ·  Baseline win-rate: **3.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -3.7pp vs baseline)
   - `H4_adx_label ≠ weak_trend`
   - `rsi_H1 ≠ [50,65)`

**2. Win-rate 0.0%** (0 W / 57 L = 57 trade · -3.7pp vs baseline)
   - `H4_adx_label = weak_trend`
   - `session ≠ us`
   - `dow ≠ Thu`

**3. Win-rate 0.0%** (0 W / 23 L = 23 trade · -3.7pp vs baseline)
   - `H4_adx_label = weak_trend`
   - `session ≠ us`
   - `dow = Thu`

**4. Win-rate 3.7%** (1 W / 26 L = 27 trade · 0.0pp vs baseline)
   - `H4_adx_label = weak_trend`
   - `session = us`

**5. Win-rate 15.6%** (5 W / 27 L = 32 trade · 11.9pp vs baseline)
   - `H4_adx_label ≠ weak_trend`
   - `rsi_H1 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=weak_trend` | 0.0621 |
| 2 | `adx_H4=[18,25)` | 0.0592 |
| 3 | `rsi_H1=[50,65)` | 0.0377 |
| 4 | `session_phase=late_pit` | 0.0317 |
| 5 | `dist_high_M30=[0.7,1.5)` | 0.0272 |
| 6 | `macro_alignment=neutral` | 0.0239 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0220 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0219 |
| 9 | `adx_M30=[25,35)` | 0.0216 |
| 10 | `session=us` | 0.0210 |
| 11 | `rsi_M30=[50,65)` | 0.0203 |
| 12 | `vix_chg1d=[0,3)` | 0.0199 |
| 13 | `H1_ema_stack=up` | 0.0195 |
| 14 | `macd_atr_M30=[0,0.3)` | 0.0195 |
| 15 | `M30_adx_label=ranging` | 0.0193 |

---

## USOIL.FOREX · meta · SELL
- Toplam çözülmüş: **351**  ·  Baseline win-rate: **83.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (24 W / 0 L = 24 trade · +16.8pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `adx_H1 ≠ [18,25)`
   - `bb_pctb_M30 ≠ [0.2,0.5)`
   - `hour_bucket = 08-12`

**2. Win-rate 100.0%** (109 W / 0 L = 109 trade · +16.8pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `adx_H1 = [18,25)`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 98.5%** (66 W / 1 L = 67 trade · +15.3pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `adx_H1 ≠ [18,25)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `ml_confidence_bucket ≠ [70,80)`

**4. Win-rate 85.0%** (17 W / 3 L = 20 trade · +1.8pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `adx_H1 = [18,25)`
   - `hour_bucket = 08-12`

**5. Win-rate 82.6%** (19 W / 4 L = 23 trade · -0.6pp vs baseline)
   - `dist_low_M30 ≠ [0.3,0.7)`
   - `adx_H1 ≠ [18,25)`
   - `bb_pctb_M30 = [0.2,0.5)`
   - `ml_confidence_bucket = [70,80)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.8%** (8 W / 18 L = 26 trade · -52.4pp vs baseline)
   - `dist_low_M30 = [0.3,0.7)`
   - `adx_H1 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dist_low_M30=[1.5,+∞)` | 0.0530 |
| 2 | `bb_pctb_M30=[−∞,0.2)` | 0.0427 |
| 3 | `dist_low_M30=[0.3,0.7)` | 0.0340 |
| 4 | `H1_adx_label=weak_trend` | 0.0336 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0302 |
| 6 | `macd_atr_M30=[0,0.3)` | 0.0300 |
| 7 | `adx_H1=[18,25)` | 0.0298 |
| 8 | `vix_chg1d=[-3,0)` | 0.0288 |
| 9 | `sar_bearish=False` | 0.0270 |
| 10 | `dow=Mon` | 0.0254 |
| 11 | `mtf_trend=mixed` | 0.0233 |
| 12 | `H4_ema_stack=mixed` | 0.0215 |
| 13 | `mtf_trend=all_down` | 0.0211 |
| 14 | `regime_label=transition` | 0.0193 |
| 15 | `adx_H1=[35,+∞)` | 0.0188 |

---

## USOIL.FOREX · ml:aggressive · BUY
- Toplam çözülmüş: **352**  ·  Baseline win-rate: **34.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +44.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -34.7pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -34.7pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -29.9pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -20.4pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.9pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0966 |
| 2 | `H4_adx_label=trending` | 0.0750 |
| 3 | `H1_ema_stack=up` | 0.0401 |
| 4 | `H4_ema_stack=mixed` | 0.0381 |
| 5 | `H1_ema_stack=down` | 0.0351 |
| 6 | `H4_adx_label=ranging` | 0.0297 |
| 7 | `H4_adx_label=weak_trend` | 0.0286 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0265 |
| 9 | `adx_H4=[18,25)` | 0.0263 |
| 10 | `regime_label=ranging` | 0.0249 |
| 11 | `adx_H4=[−∞,18)` | 0.0229 |
| 12 | `adx_H4=[25,35)` | 0.0215 |
| 13 | `macro_alignment=strong_against` | 0.0203 |
| 14 | `macro_alignment=neutral` | 0.0203 |
| 15 | `vix_chg1d=[0,3)` | 0.0186 |

---

## USOIL.FOREX · ml:aggressive · SELL
- Toplam çözülmüş: **278**  ·  Baseline win-rate: **65.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +30.1pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 = [30,50)`
   - `H4_ema_stack = mixed`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 95.1%** (78 W / 4 L = 82 trade · +30.0pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +13.2pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -55.1pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 ≠ [30,50)`
   - `H1_ema_stack = up`

**2. Win-rate 20.0%** (4 W / 16 L = 20 trade · -45.1pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 ≠ [30,50)`
   - `H1_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=all_down` | 0.0714 |
| 2 | `mtf_trend=mixed` | 0.0621 |
| 3 | `M30_ema_stack=down` | 0.0501 |
| 4 | `H1_ema_stack=down` | 0.0479 |
| 5 | `rsi_H1=[50,65)` | 0.0391 |
| 6 | `rsi_H4=[50,65)` | 0.0358 |
| 7 | `M30_adx_label=trending` | 0.0327 |
| 8 | `adx_M30=[35,+∞)` | 0.0283 |
| 9 | `M30_ema_stack=mixed` | 0.0275 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0262 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0257 |
| 12 | `dow=Mon` | 0.0250 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0239 |
| 14 | `regime_label=transition` | 0.0198 |
| 15 | `rsi_H4=[30,50)` | 0.0188 |

---

## USOIL.FOREX · ml:balanced · BUY
- Toplam çözülmüş: **353**  ·  Baseline win-rate: **34.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +44.9pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -34.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -34.3pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -29.5pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -20.0pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.5pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -2.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0857 |
| 2 | `H4_adx_label=trending` | 0.0721 |
| 3 | `H4_ema_stack=mixed` | 0.0436 |
| 4 | `H4_adx_label=ranging` | 0.0354 |
| 5 | `H1_ema_stack=up` | 0.0332 |
| 6 | `H1_ema_stack=down` | 0.0304 |
| 7 | `regime_label=ranging` | 0.0275 |
| 8 | `H4_adx_label=weak_trend` | 0.0262 |
| 9 | `adx_H4=[−∞,18)` | 0.0255 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0244 |
| 11 | `adx_H4=[18,25)` | 0.0239 |
| 12 | `adx_H4=[35,+∞)` | 0.0216 |
| 13 | `vix_chg1d=[0,3)` | 0.0201 |
| 14 | `regime_label=transition` | 0.0187 |
| 15 | `macro_alignment=neutral` | 0.0175 |

---

## USOIL.FOREX · ml:balanced · SELL
- Toplam çözülmüş: **276**  ·  Baseline win-rate: **65.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +29.6pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 = [30,50)`
   - `H4_ema_stack ≠ down`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 95.1%** (78 W / 4 L = 82 trade · +29.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +12.7pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (6 W / 33 L = 39 trade · -50.2pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0743 |
| 2 | `mtf_trend=all_down` | 0.0596 |
| 3 | `rsi_H4=[50,65)` | 0.0470 |
| 4 | `H1_ema_stack=down` | 0.0399 |
| 5 | `M30_ema_stack=down` | 0.0387 |
| 6 | `M30_adx_label=trending` | 0.0376 |
| 7 | `adx_M30=[35,+∞)` | 0.0365 |
| 8 | `rsi_H1=[50,65)` | 0.0308 |
| 9 | `dow=Mon` | 0.0302 |
| 10 | `M30_ema_stack=mixed` | 0.0286 |
| 11 | `vix_chg1d=[3,+∞)` | 0.0263 |
| 12 | `rsi_H4=[30,50)` | 0.0248 |
| 13 | `dxy_chg1d=[0,0.5)` | 0.0213 |
| 14 | `rsi_H1=[30,50)` | 0.0209 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0195 |

---

## USOIL.FOREX · ml:full_power · BUY
- Toplam çözülmüş: **352**  ·  Baseline win-rate: **34.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +44.5pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -34.7pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -34.7pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -29.9pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -20.4pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.9pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0960 |
| 2 | `H4_adx_label=trending` | 0.0769 |
| 3 | `H1_ema_stack=up` | 0.0376 |
| 4 | `H1_ema_stack=down` | 0.0363 |
| 5 | `H4_ema_stack=mixed` | 0.0360 |
| 6 | `H4_adx_label=ranging` | 0.0307 |
| 7 | `H4_adx_label=weak_trend` | 0.0295 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0294 |
| 9 | `adx_H4=[18,25)` | 0.0262 |
| 10 | `regime_label=ranging` | 0.0241 |
| 11 | `adx_H4=[−∞,18)` | 0.0236 |
| 12 | `macro_alignment=strong_against` | 0.0226 |
| 13 | `adx_H4=[25,35)` | 0.0223 |
| 14 | `macro_alignment=neutral` | 0.0195 |
| 15 | `vix_chg1d=[0,3)` | 0.0182 |

---

## USOIL.FOREX · ml:full_power · SELL
- Toplam çözülmüş: **275**  ·  Baseline win-rate: **65.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (20 W / 1 L = 21 trade · +29.4pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 = [30,50)`
   - `H4_ema_stack = mixed`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 95.1%** (78 W / 4 L = 82 trade · +29.3pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +12.5pp vs baseline)
   - `mtf_trend ≠ mixed`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (6 W / 33 L = 39 trade · -50.4pp vs baseline)
   - `mtf_trend = mixed`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0711 |
| 2 | `mtf_trend=all_down` | 0.0553 |
| 3 | `H1_ema_stack=down` | 0.0458 |
| 4 | `rsi_H4=[50,65)` | 0.0454 |
| 5 | `M30_ema_stack=down` | 0.0389 |
| 6 | `adx_M30=[35,+∞)` | 0.0376 |
| 7 | `dow=Mon` | 0.0351 |
| 8 | `rsi_H1=[50,65)` | 0.0326 |
| 9 | `M30_adx_label=trending` | 0.0295 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0271 |
| 11 | `rsi_H4=[30,50)` | 0.0258 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0238 |
| 13 | `M30_ema_stack=mixed` | 0.0198 |
| 14 | `H4_adx_label=trending` | 0.0192 |
| 15 | `H1_ema_stack=mixed` | 0.0183 |

---

## USOIL.FOREX · ml:main · BUY
- Toplam çözülmüş: **353**  ·  Baseline win-rate: **34.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +45.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -34.0pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [0,3)`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -34.0pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -29.2pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -19.7pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.2pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -2.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0839 |
| 2 | `H4_adx_label=trending` | 0.0714 |
| 3 | `H4_ema_stack=mixed` | 0.0401 |
| 4 | `H4_adx_label=ranging` | 0.0350 |
| 5 | `H1_ema_stack=up` | 0.0343 |
| 6 | `H1_ema_stack=down` | 0.0315 |
| 7 | `regime_label=ranging` | 0.0286 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0282 |
| 9 | `H4_adx_label=weak_trend` | 0.0268 |
| 10 | `adx_H4=[18,25)` | 0.0253 |
| 11 | `vix_chg1d=[0,3)` | 0.0228 |
| 12 | `adx_H4=[−∞,18)` | 0.0220 |
| 13 | `regime_label=transition` | 0.0195 |
| 14 | `adx_H4=[35,+∞)` | 0.0180 |
| 15 | `adx_H4=[25,35)` | 0.0171 |

---

## USOIL.FOREX · ml:main · SELL
- Toplam çözülmüş: **280**  ·  Baseline win-rate: **65.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.1%** (78 W / 4 L = 82 trade · +30.1pp vs baseline)
   - `mtf_trend = all_down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 91.7%** (22 W / 2 L = 24 trade · +26.7pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_H4 = [30,50)`
   - `H4_ema_stack = mixed`
   - `macd_atr_M30 ≠ [-0.3,0)`

**3. Win-rate 79.2%** (19 W / 5 L = 24 trade · +14.2pp vs baseline)
   - `mtf_trend = all_down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 15.4%** (6 W / 33 L = 39 trade · -49.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_H4 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0794 |
| 2 | `mtf_trend=all_down` | 0.0609 |
| 3 | `M30_ema_stack=down` | 0.0438 |
| 4 | `rsi_H4=[50,65)` | 0.0402 |
| 5 | `M30_ema_stack=mixed` | 0.0364 |
| 6 | `H1_ema_stack=down` | 0.0364 |
| 7 | `adx_M30=[35,+∞)` | 0.0363 |
| 8 | `M30_adx_label=trending` | 0.0357 |
| 9 | `dxy_chg1d=[0,0.5)` | 0.0268 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0259 |
| 11 | `dow=Mon` | 0.0249 |
| 12 | `H1_ema_stack=mixed` | 0.0231 |
| 13 | `rsi_H1=[50,65)` | 0.0225 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0215 |
| 15 | `H4_adx_label=trending` | 0.0180 |

---

## USOIL.FOREX · ml:ultra_safe · BUY
- Toplam çözülmüş: **353**  ·  Baseline win-rate: **34.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.2%** (19 W / 5 L = 24 trade · +45.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -34.0pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [0,3)`

**2. Win-rate 0.0%** (0 W / 48 L = 48 trade · -34.0pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 = [0.5,0.8)`

**3. Win-rate 4.8%** (1 W / 20 L = 21 trade · -29.2pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 = [1.5,+∞)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -19.7pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [50,60)`
   - `dist_low_M30 ≠ [1.5,+∞)`

**5. Win-rate 25.8%** (8 W / 23 L = 31 trade · -8.2pp vs baseline)
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [50,60)`

**6. Win-rate 31.8%** (7 W / 15 L = 22 trade · -2.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label = trending`
   - `bb_pctb_M30 ≠ [−∞,0.2)`
   - `dow = Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0838 |
| 2 | `H4_adx_label=trending` | 0.0712 |
| 3 | `H4_ema_stack=mixed` | 0.0414 |
| 4 | `H4_adx_label=ranging` | 0.0363 |
| 5 | `H1_ema_stack=up` | 0.0343 |
| 6 | `H1_ema_stack=down` | 0.0320 |
| 7 | `H4_adx_label=weak_trend` | 0.0290 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0286 |
| 9 | `regime_label=ranging` | 0.0281 |
| 10 | `adx_H4=[18,25)` | 0.0252 |
| 11 | `vix_chg1d=[0,3)` | 0.0224 |
| 12 | `adx_H4=[−∞,18)` | 0.0216 |
| 13 | `regime_label=transition` | 0.0194 |
| 14 | `adx_H4=[35,+∞)` | 0.0185 |
| 15 | `adx_H4=[25,35)` | 0.0176 |

---

## USOIL.FOREX · ml:ultra_safe · SELL
- Toplam çözülmüş: **280**  ·  Baseline win-rate: **65.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.1%** (78 W / 4 L = 82 trade · +30.1pp vs baseline)
   - `mtf_trend = all_down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**2. Win-rate 90.9%** (20 W / 2 L = 22 trade · +25.9pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_H4 = [30,50)`
   - `H4_ema_stack = mixed`
   - `macd_atr_M30 = [0,0.3)`

**3. Win-rate 79.2%** (19 W / 5 L = 24 trade · +14.2pp vs baseline)
   - `mtf_trend = all_down`
   - `dow ≠ Mon`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `bb_pctb_M30 = [−∞,0.2)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -55.0pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_H4 ≠ [30,50)`
   - `H1_ema_stack = up`

**2. Win-rate 20.0%** (4 W / 16 L = 20 trade · -45.0pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_H4 ≠ [30,50)`
   - `H1_ema_stack ≠ up`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `mtf_trend=mixed` | 0.0777 |
| 2 | `mtf_trend=all_down` | 0.0617 |
| 3 | `M30_ema_stack=down` | 0.0499 |
| 4 | `rsi_H4=[50,65)` | 0.0431 |
| 5 | `adx_M30=[35,+∞)` | 0.0354 |
| 6 | `M30_adx_label=trending` | 0.0346 |
| 7 | `H1_ema_stack=down` | 0.0346 |
| 8 | `M30_ema_stack=mixed` | 0.0316 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0281 |
| 10 | `rsi_H1=[50,65)` | 0.0260 |
| 11 | `dow=Mon` | 0.0254 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0247 |
| 13 | `rsi_H4=[30,50)` | 0.0223 |
| 14 | `dxy_chg1d=[0,0.5)` | 0.0168 |
| 15 | `adx_H4=[18,25)` | 0.0161 |

---

## USOIL.FOREX · pulse1 · BUY
- Toplam çözülmüş: **1956**  ·  Baseline win-rate: **19.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 46 L = 46 trade · -19.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `rsi_M30 = [30,50)`

**2. Win-rate 0.0%** (0 W / 46 L = 46 trade · -19.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `H4_adx_label ≠ trending`
   - `session_phase ≠ off_hours`

**3. Win-rate 0.0%** (0 W / 53 L = 53 trade · -19.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `H4_adx_label ≠ trending`
   - `session_phase = off_hours`

**4. Win-rate 0.0%** (0 W / 335 L = 335 trade · -19.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label = trending`
   - `adx_H4 ≠ [35,+∞)`
   - `adx_M30 = [35,+∞)`

**5. Win-rate 0.7%** (1 W / 141 L = 142 trade · -18.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `H1_adx_label = ranging`
   - `dist_high_M30 ≠ [1.5,+∞)`

**6. Win-rate 5.3%** (15 W / 270 L = 285 trade · -14.0pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label = trending`
   - `adx_H4 ≠ [35,+∞)`
   - `adx_M30 ≠ [35,+∞)`

**7. Win-rate 8.0%** (2 W / 23 L = 25 trade · -11.3pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow = Thu`
   - `H4_adx_label = trending`
   - `rsi_H4 = [65,75)`

**8. Win-rate 11.5%** (3 W / 23 L = 26 trade · -7.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `dow ≠ Thu`
   - `us10y_chg1d = [-0.5,0)`
   - `rsi_M30 ≠ [30,50)`

**9. Win-rate 12.2%** (6 W / 43 L = 49 trade · -7.1pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `H1_adx_label = ranging`
   - `dist_high_M30 = [1.5,+∞)`

**10. Win-rate 16.7%** (53 W / 264 L = 317 trade · -2.6pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_adx_label ≠ trending`
   - `H1_adx_label ≠ ranging`
   - `macro_alignment ≠ strong_pro`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.0607 |
| 2 | `H4_ema_stack=mixed` | 0.0554 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0435 |
| 4 | `adx_H4=[−∞,18)` | 0.0275 |
| 5 | `H4_adx_label=trending` | 0.0262 |
| 6 | `regime_label=transition` | 0.0254 |
| 7 | `M30_adx_label=trending` | 0.0251 |
| 8 | `H4_adx_label=ranging` | 0.0251 |
| 9 | `regime_label=ranging` | 0.0233 |
| 10 | `H1_ema_stack=up` | 0.0228 |
| 11 | `dow=Mon` | 0.0222 |
| 12 | `dow=Thu` | 0.0188 |
| 13 | `mtf_trend=all_down` | 0.0184 |
| 14 | `macro_alignment=strong_pro` | 0.0180 |
| 15 | `H1_ema_stack=down` | 0.0172 |

---

## USOIL.FOREX · pulse1 · SELL
- Toplam çözülmüş: **1171**  ·  Baseline win-rate: **68.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.4%** (412 W / 20 L = 432 trade · +27.4pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dow ≠ Mon`
   - `macd_atr_M30 ≠ [−∞,-0.3)`

**2. Win-rate 90.3%** (159 W / 17 L = 176 trade · +22.3pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `M30_adx_label ≠ trending`
   - `M30_ema_stack ≠ down`
   - `vix_chg1d ≠ [3,+∞)`

**3. Win-rate 84.1%** (53 W / 10 L = 63 trade · +16.1pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack = down`
   - `us10y_chg1d = [−∞,-0.5)`
   - `vix_chg1d ≠ [0,3)`

**4. Win-rate 80.3%** (49 W / 12 L = 61 trade · +12.3pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `H4_ema_stack = down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 21 L = 21 trade · -68.0pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `M30_adx_label = trending`
   - `dow = Mon`
   - `H4_ema_stack ≠ down`

**2. Win-rate 0.0%** (0 W / 54 L = 54 trade · -68.0pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack ≠ down`
   - `M30_ema_stack ≠ up`

**3. Win-rate 2.4%** (1 W / 41 L = 42 trade · -65.6pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack ≠ down`
   - `M30_ema_stack = up`
   - `adx_H1 ≠ [−∞,18)`

**4. Win-rate 15.0%** (3 W / 17 L = 20 trade · -53.0pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack ≠ down`
   - `M30_ema_stack = up`
   - `adx_H1 = [−∞,18)`

**5. Win-rate 15.0%** (6 W / 34 L = 40 trade · -53.0pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack = down`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**6. Win-rate 26.5%** (26 W / 72 L = 98 trade · -41.5pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `M30_adx_label ≠ trending`
   - `M30_ema_stack = down`
   - `dow ≠ Tue`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0627 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0471 |
| 3 | `M30_adx_label=trending` | 0.0460 |
| 4 | `adx_M30=[35,+∞)` | 0.0396 |
| 5 | `adx_H4=[−∞,18)` | 0.0327 |
| 6 | `regime_label=ranging` | 0.0295 |
| 7 | `adx_H4=[25,35)` | 0.0281 |
| 8 | `us10y_chg1d=[-0.5,0)` | 0.0248 |
| 9 | `H4_adx_label=ranging` | 0.0241 |
| 10 | `us10y_chg1d=[0.5,+∞)` | 0.0239 |
| 11 | `dow=Mon` | 0.0213 |
| 12 | `adx_H4=[18,25)` | 0.0208 |
| 13 | `M30_adx_label=ranging` | 0.0199 |
| 14 | `H4_ema_stack=down` | 0.0187 |
| 15 | `H4_ema_stack=mixed` | 0.0174 |

---

## USOIL.FOREX · pulse2 · BUY
- Toplam çözülmüş: **832**  ·  Baseline win-rate: **26.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 87 L = 87 trade · -26.2pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_ema_stack = up`

**2. Win-rate 0.0%** (0 W / 288 L = 288 trade · -26.2pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ down`
   - `us10y_chg1d ≠ [0,0.5)`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -21.7pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_ema_stack ≠ up`

**4. Win-rate 6.7%** (2 W / 28 L = 30 trade · -19.5pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack ≠ down`
   - `us10y_chg1d = [0,0.5)`

**5. Win-rate 6.9%** (2 W / 27 L = 29 trade · -19.3pp vs baseline)
   - `H4_ema_stack = down`
   - `M30_ema_stack = down`

**6. Win-rate 31.0%** (13 W / 29 L = 42 trade · 4.8pp vs baseline)
   - `H4_ema_stack ≠ down`
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_ema_stack=down` | 0.1391 |
| 2 | `H4_adx_label=trending` | 0.0813 |
| 3 | `H4_ema_stack=mixed` | 0.0625 |
| 4 | `H1_ema_stack=up` | 0.0524 |
| 5 | `H1_ema_stack=down` | 0.0499 |
| 6 | `vix_chg1d=[3,+∞)` | 0.0447 |
| 7 | `M30_ema_stack=up` | 0.0294 |
| 8 | `H4_adx_label=weak_trend` | 0.0245 |
| 9 | `adx_H4=[25,35)` | 0.0242 |
| 10 | `vix_chg1d=[0,3)` | 0.0233 |
| 11 | `rsi_H4=[65,75)` | 0.0217 |
| 12 | `rsi_H4=[30,50)` | 0.0214 |
| 13 | `M30_ema_stack=mixed` | 0.0207 |
| 14 | `adx_H4=[−∞,18)` | 0.0195 |
| 15 | `adx_H4=[18,25)` | 0.0192 |

---

## USOIL.FOREX · pulse2 · SELL
- Toplam çözülmüş: **930**  ·  Baseline win-rate: **67.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +33.0pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label ≠ strong_trend_down`
   - `H4_adx_label ≠ trending`
   - `H1_ema_stack = up`

**2. Win-rate 98.1%** (303 W / 6 L = 309 trade · +31.1pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `adx_H4 ≠ [35,+∞)`

**3. Win-rate 89.2%** (91 W / 11 L = 102 trade · +22.2pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `rsi_H4 = [30,50)`
   - `dow ≠ Mon`

**4. Win-rate 86.8%** (33 W / 5 L = 38 trade · +19.8pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 = [25,35)`

**5. Win-rate 81.2%** (26 W / 6 L = 32 trade · +14.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label = strong_trend_down`

**6. Win-rate 75.0%** (15 W / 5 L = 20 trade · +8.0pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `adx_H4 = [35,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -67.0pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label ≠ strong_trend_down`
   - `H4_adx_label = trending`
   - `atr_ratio_M30 = [1,1.3)`

**2. Win-rate 0.0%** (0 W / 27 L = 27 trade · -67.0pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `rsi_H4 ≠ [30,50)`

**3. Win-rate 9.5%** (2 W / 19 L = 21 trade · -57.5pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `regime_label ≠ strong_trend_down`
   - `H4_adx_label = trending`
   - `atr_ratio_M30 ≠ [1,1.3)`

**4. Win-rate 28.1%** (9 W / 23 L = 32 trade · -38.9pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `rsi_H4 = [30,50)`
   - `dow = Mon`

**5. Win-rate 34.6%** (9 W / 17 L = 26 trade · -32.4pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `us10y_chg1d = [0.5,+∞)`
   - `adx_H1 ≠ [25,35)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0719 |
| 2 | `mtf_trend=mixed` | 0.0471 |
| 3 | `dow=Mon` | 0.0466 |
| 4 | `mtf_trend=all_down` | 0.0466 |
| 5 | `adx_M30=[35,+∞)` | 0.0401 |
| 6 | `M30_adx_label=ranging` | 0.0328 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0272 |
| 8 | `adx_M30=[−∞,18)` | 0.0265 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0250 |
| 10 | `M30_adx_label=weak_trend` | 0.0238 |
| 11 | `rsi_H1=[50,65)` | 0.0230 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0218 |
| 13 | `adx_M30=[18,25)` | 0.0212 |
| 14 | `H1_ema_stack=down` | 0.0205 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0204 |

---

## USOIL.FOREX · pulse3 · BUY
- Toplam çözülmüş: **1361**  ·  Baseline win-rate: **22.1%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.6%** (3 W / 485 L = 488 trade · -21.5pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket ≠ [−∞,50)`

**2. Win-rate 5.6%** (10 W / 167 L = 177 trade · -16.5pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [3,+∞)`
   - `H4_ema_stack = down`
   - `ml_confidence_bucket ≠ [−∞,50)`

**3. Win-rate 7.4%** (2 W / 25 L = 27 trade · -14.7pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack = down`

**4. Win-rate 10.4%** (8 W / 69 L = 77 trade · -11.7pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `vix_chg1d ≠ [3,+∞)`
   - `macro_alignment ≠ strong_pro`
   - `ml_confidence_bucket = [−∞,50)`

**5. Win-rate 11.8%** (6 W / 45 L = 51 trade · -10.3pp vs baseline)
   - `H4_adx_label = trending`
   - `H1_ema_stack ≠ down`
   - `dow = Thu`
   - `session ≠ europe`

**6. Win-rate 16.0%** (8 W / 42 L = 50 trade · -6.1pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [3,+∞)`
   - `H4_ema_stack ≠ down`
   - `dow ≠ Mon`

**7. Win-rate 21.4%** (9 W / 33 L = 42 trade · -0.7pp vs baseline)
   - `H4_adx_label ≠ trending`
   - `vix_chg1d = [3,+∞)`
   - `H4_ema_stack = down`
   - `ml_confidence_bucket = [−∞,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H4_adx_label=trending` | 0.0870 |
| 2 | `H4_ema_stack=down` | 0.0650 |
| 3 | `H4_ema_stack=mixed` | 0.0518 |
| 4 | `H1_ema_stack=down` | 0.0394 |
| 5 | `H4_adx_label=weak_trend` | 0.0309 |
| 6 | `H1_ema_stack=up` | 0.0285 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0283 |
| 8 | `adx_H4=[25,35)` | 0.0269 |
| 9 | `us10y_chg1d=[-0.5,0)` | 0.0268 |
| 10 | `adx_H4=[18,25)` | 0.0238 |
| 11 | `dow=Mon` | 0.0204 |
| 12 | `vix_chg1d=[0,3)` | 0.0193 |
| 13 | `adx_H4=[−∞,18)` | 0.0174 |
| 14 | `rsi_H4=[65,75)` | 0.0171 |
| 15 | `macro_alignment=strong_pro` | 0.0168 |

---

## USOIL.FOREX · pulse3 · SELL
- Toplam çözülmüş: **1304**  ·  Baseline win-rate: **77.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (60 W / 0 L = 60 trade · +22.8pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `regime_label ≠ strong_trend_down`

**2. Win-rate 100.0%** (20 W / 0 L = 20 trade · +22.8pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d = [−∞,-0.5)`
   - `regime_label = strong_trend_down`

**3. Win-rate 100.0%** (113 W / 0 L = 113 trade · +22.8pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `regime_label = ranging`
   - `vix_chg1d ≠ [3,+∞)`

**4. Win-rate 98.9%** (461 W / 5 L = 466 trade · +21.7pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `adx_H4 ≠ [35,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**5. Win-rate 93.3%** (70 W / 5 L = 75 trade · +16.1pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [3,+∞)`

**6. Win-rate 88.6%** (70 W / 9 L = 79 trade · +11.4pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend = all_down`
   - `adx_H4 ≠ [35,+∞)`
   - `us10y_chg1d = [0.5,+∞)`

**7. Win-rate 85.0%** (17 W / 3 L = 20 trade · +7.8pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `regime_label = ranging`
   - `vix_chg1d = [3,+∞)`

**8. Win-rate 81.5%** (22 W / 5 L = 27 trade · +4.3pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `regime_label ≠ ranging`
   - `session = overlap`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 20.0%** (4 W / 16 L = 20 trade · -57.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow = Tue`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `rsi_M30 = [50,65)`

**2. Win-rate 26.0%** (50 W / 142 L = 192 trade · -51.2pp vs baseline)
   - `M30_adx_label ≠ trending`
   - `dow ≠ Tue`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `vix_chg1d ≠ [−∞,-3)`

**3. Win-rate 31.9%** (29 W / 62 L = 91 trade · -45.3pp vs baseline)
   - `M30_adx_label = trending`
   - `mtf_trend ≠ all_down`
   - `regime_label ≠ ranging`
   - `session ≠ overlap`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_adx_label=trending` | 0.0719 |
| 2 | `mtf_trend=mixed` | 0.0488 |
| 3 | `mtf_trend=all_down` | 0.0426 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0345 |
| 5 | `regime_label=transition` | 0.0329 |
| 6 | `H4_ema_stack=mixed` | 0.0293 |
| 7 | `adx_M30=[−∞,18)` | 0.0292 |
| 8 | `regime_label=ranging` | 0.0288 |
| 9 | `adx_H4=[−∞,18)` | 0.0286 |
| 10 | `H4_adx_label=ranging` | 0.0283 |
| 11 | `dow=Mon` | 0.0268 |
| 12 | `adx_M30=[35,+∞)` | 0.0238 |
| 13 | `M30_adx_label=ranging` | 0.0236 |
| 14 | `vix_chg1d=[3,+∞)` | 0.0221 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0202 |

---

## USOIL.FOREX · smc · BUY
- Toplam çözülmüş: **274**  ·  Baseline win-rate: **19.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 98 L = 98 trade · -19.3pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `hour_bucket ≠ 00-04`
   - `adx_M30 ≠ [−∞,18)`
   - `atr_ratio_M30 ≠ [1,1.3)`

**2. Win-rate 4.8%** (2 W / 40 L = 42 trade · -14.5pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `hour_bucket ≠ 00-04`
   - `adx_M30 ≠ [−∞,18)`
   - `atr_ratio_M30 = [1,1.3)`

**3. Win-rate 10.0%** (2 W / 18 L = 20 trade · -9.3pp vs baseline)
   - `rsi_H4 ≠ [30,50)`
   - `ml_confidence_bucket = [70,80)`

**4. Win-rate 30.0%** (9 W / 21 L = 30 trade · 10.7pp vs baseline)
   - `rsi_H4 = [30,50)`
   - `hour_bucket ≠ 00-04`
   - `adx_M30 = [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[70,80)` | 0.0598 |
| 2 | `M30_adx_label=ranging` | 0.0586 |
| 3 | `ml_confidence_bucket=[80,+∞)` | 0.0421 |
| 4 | `M30_ema_stack=mixed` | 0.0395 |
| 5 | `adx_M30=[−∞,18)` | 0.0394 |
| 6 | `H1_ema_stack=down` | 0.0361 |
| 7 | `rsi_H4=[30,50)` | 0.0354 |
| 8 | `mtf_trend=mixed` | 0.0337 |
| 9 | `rsi_H4=[50,65)` | 0.0300 |
| 10 | `mtf_trend=all_down` | 0.0289 |
| 11 | `ml_confidence_bucket=[60,70)` | 0.0274 |
| 12 | `M30_adx_label=trending` | 0.0274 |
| 13 | `rsi_H1=[30,50)` | 0.0273 |
| 14 | `rsi_H1=[50,65)` | 0.0260 |
| 15 | `M30_ema_stack=down` | 0.0249 |

---

## USOIL.FOREX · smc · SELL
- Toplam çözülmüş: **161**  ·  Baseline win-rate: **77.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (68 W / 0 L = 68 trade · +22.4pp vs baseline)
   - `H1_ema_stack = down`
   - `us10y_chg1d = [−∞,-0.5)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**2. Win-rate 95.2%** (20 W / 1 L = 21 trade · +17.6pp vs baseline)
   - `H1_ema_stack = down`
   - `us10y_chg1d = [−∞,-0.5)`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 85.0%** (17 W / 3 L = 20 trade · +7.4pp vs baseline)
   - `H1_ema_stack = down`
   - `us10y_chg1d ≠ [−∞,-0.5)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 13.8%** (4 W / 25 L = 29 trade · -63.8pp vs baseline)
   - `H1_ema_stack ≠ down`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `H1_ema_stack=down` | 0.1042 |
| 2 | `vix_chg1d=[3,+∞)` | 0.0889 |
| 3 | `rsi_H4=[50,65)` | 0.0792 |
| 4 | `vix_chg1d=[0,3)` | 0.0761 |
| 5 | `rsi_H4=[30,50)` | 0.0641 |
| 6 | `us10y_chg1d=[−∞,-0.5)` | 0.0578 |
| 7 | `H4_adx_label=trending` | 0.0436 |
| 8 | `ml_confidence_bucket=[70,80)` | 0.0366 |
| 9 | `adx_H4=[25,35)` | 0.0299 |
| 10 | `regime_label=transition` | 0.0285 |
| 11 | `H1_ema_stack=mixed` | 0.0285 |
| 12 | `H4_ema_stack=mixed` | 0.0241 |
| 13 | `us10y_chg1d=[0.5,+∞)` | 0.0204 |
| 14 | `M30_adx_label=trending` | 0.0196 |
| 15 | `H4_adx_label=ranging` | 0.0180 |

---

## XAUUSD · ai_panel · BUY
- Toplam çözülmüş: **121**  ·  Baseline win-rate: **75.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.7%** (29 W / 1 L = 30 trade · +21.5pp vs baseline)
   - `H1_adx_label = weak_trend`

**2. Win-rate 88.2%** (30 W / 4 L = 34 trade · +13.0pp vs baseline)
   - `H1_adx_label ≠ weak_trend`
   - `adx_H1 ≠ [25,35)`
   - `dist_low_M30 ≠ [1.5,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[18,25)` | 0.0705 |
| 2 | `H1_adx_label=weak_trend` | 0.0659 |
| 3 | `H1_adx_label=trending` | 0.0590 |
| 4 | `adx_H1=[25,35)` | 0.0582 |
| 5 | `us10y_chg1d=[0.5,+∞)` | 0.0404 |
| 6 | `mtf_trend=all_up` | 0.0386 |
| 7 | `rsi_M30=[30,50)` | 0.0341 |
| 8 | `dist_low_M30=[0.3,0.7)` | 0.0320 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0305 |
| 10 | `M30_ema_stack=mixed` | 0.0304 |
| 11 | `rsi_M30=[50,65)` | 0.0272 |
| 12 | `M30_ema_stack=up` | 0.0245 |
| 13 | `rsi_H1=[30,50)` | 0.0216 |
| 14 | `macd_atr_M30=[-0.3,0)` | 0.0180 |
| 15 | `sar_bearish=False` | 0.0174 |

---

## XAUUSD · emel · BUY
- Toplam çözülmüş: **216**  ·  Baseline win-rate: **80.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (22 W / 0 L = 22 trade · +19.4pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 = [1,1.3)`
   - `M30_ema_stack = down`

**2. Win-rate 95.7%** (22 W / 1 L = 23 trade · +15.1pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**3. Win-rate 95.2%** (20 W / 1 L = 21 trade · +14.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack = down`
   - `adx_H1 ≠ [25,35)`

**4. Win-rate 95.2%** (20 W / 1 L = 21 trade · +14.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 = [1,1.3)`
   - `M30_ema_stack ≠ down`

**5. Win-rate 86.4%** (19 W / 3 L = 22 trade · +5.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack = down`
   - `adx_H1 = [25,35)`

**6. Win-rate 78.4%** (29 W / 8 L = 37 trade · -2.2pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `M30_ema_stack ≠ down`
   - `dxy_chg1d = [0,0.5)`

**7. Win-rate 78.4%** (29 W / 8 L = 37 trade · -2.2pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `macd_atr_M30 = [-0.3,0)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[-0.5,0)` | 0.0716 |
| 2 | `adx_H1=[35,+∞)` | 0.0670 |
| 3 | `dxy_chg1d=[0,0.5)` | 0.0539 |
| 4 | `macro_alignment=weak_against` | 0.0453 |
| 5 | `mtf_trend=all_down` | 0.0379 |
| 6 | `M30_ema_stack=down` | 0.0305 |
| 7 | `consec_red_M30=[2,4)` | 0.0298 |
| 8 | `adx_M30=[35,+∞)` | 0.0283 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0257 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0238 |
| 11 | `consec_red_M30=[0,2)` | 0.0209 |
| 12 | `atr_ratio_M30=[0.7,1)` | 0.0192 |
| 13 | `us10y_chg1d=[-0.5,0)` | 0.0191 |
| 14 | `macd_atr_M30=[0,0.3)` | 0.0186 |
| 15 | `sar_bearish=True` | 0.0186 |

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
- Toplam çözülmüş: **328**  ·  Baseline win-rate: **60.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +30.8pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment = weak_against`
   - `sar_bearish ≠ True`

**2. Win-rate 81.5%** (22 W / 5 L = 27 trade · +21.4pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment = weak_against`
   - `sar_bearish = True`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 27.3%** (6 W / 16 L = 22 trade · -32.8pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [0.5,+∞)`
   - `H1_adx_label ≠ trending`

**2. Win-rate 28.6%** (6 W / 15 L = 21 trade · -31.5pp vs baseline)
   - `rsi_H1 = [65,75)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0400 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0283 |
| 3 | `M30_ema_stack=down` | 0.0253 |
| 4 | `mtf_trend=all_down` | 0.0247 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0231 |
| 6 | `adx_M30=[25,35)` | 0.0219 |
| 7 | `rsi_H1=[30,50)` | 0.0202 |
| 8 | `adx_H1=[35,+∞)` | 0.0195 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0193 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0191 |
| 11 | `M30_adx_label=trending` | 0.0188 |
| 12 | `atr_ratio_M30=[0.7,1)` | 0.0184 |
| 13 | `rsi_H1=[50,65)` | 0.0177 |
| 14 | `adx_H1=[25,35)` | 0.0177 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0173 |

---

## XAUUSD · ml:aggressive · SELL
- Toplam çözülmüş: **164**  ·  Baseline win-rate: **21.3%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -21.3pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 7.7%** (2 W / 24 L = 26 trade · -13.6pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 = [0.7,1.5)`

**3. Win-rate 14.3%** (3 W / 18 L = 21 trade · -7.0pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 ≠ [0,0.3)`

**4. Win-rate 16.7%** (8 W / 40 L = 48 trade · -4.6pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `adx_M30 ≠ [25,35)`
   - `rsi_H1 ≠ [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0563 |
| 2 | `dxy_chg1d=[-0.5,0)` | 0.0506 |
| 3 | `adx_M30=[35,+∞)` | 0.0406 |
| 4 | `adx_H1=[35,+∞)` | 0.0400 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0310 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0256 |
| 7 | `adx_M30=[25,35)` | 0.0252 |
| 8 | `hour_bucket=12-16` | 0.0242 |
| 9 | `macro_alignment=strong_against` | 0.0240 |
| 10 | `ml_confidence_bucket=[60,70)` | 0.0222 |
| 11 | `dist_low_M30=[1.5,+∞)` | 0.0217 |
| 12 | `M30_adx_label=weak_trend` | 0.0212 |
| 13 | `dist_low_M30=[0.7,1.5)` | 0.0202 |
| 14 | `session=asia` | 0.0196 |
| 15 | `macro_alignment=neutral` | 0.0194 |

---

## XAUUSD · ml:balanced · BUY
- Toplam çözülmüş: **330**  ·  Baseline win-rate: **60.0%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.6%** (25 W / 2 L = 27 trade · +32.6pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 91.7%** (22 W / 2 L = 24 trade · +31.7pp vs baseline)
   - `rsi_H1 ≠ [65,75)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 28.6%** (6 W / 15 L = 21 trade · -31.4pp vs baseline)
   - `rsi_H1 = [65,75)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_against` | 0.0332 |
| 2 | `M30_ema_stack=down` | 0.0280 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0250 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0225 |
| 5 | `mtf_trend=all_down` | 0.0224 |
| 6 | `sar_bearish=True` | 0.0223 |
| 7 | `macro_alignment=strong_against` | 0.0195 |
| 8 | `M30_ema_stack=up` | 0.0188 |
| 9 | `ml_confidence_bucket=[80,+∞)` | 0.0181 |
| 10 | `session=overlap` | 0.0180 |
| 11 | `rsi_M30=[30,50)` | 0.0172 |
| 12 | `adx_M30=[25,35)` | 0.0168 |
| 13 | `adx_H1=[35,+∞)` | 0.0167 |
| 14 | `adx_H1=[25,35)` | 0.0166 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0161 |

---

## XAUUSD · ml:balanced · SELL
- Toplam çözülmüş: **164**  ·  Baseline win-rate: **20.7%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -20.7pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 7.7%** (2 W / 24 L = 26 trade · -13.0pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 = [0.7,1.5)`

**3. Win-rate 14.3%** (6 W / 36 L = 42 trade · -6.4pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `adx_M30 ≠ [25,35)`
   - `rsi_M30 = [50,65)`

**4. Win-rate 14.3%** (3 W / 18 L = 21 trade · -6.4pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 ≠ [0,0.3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0587 |
| 2 | `macro_alignment=weak_pro` | 0.0504 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0424 |
| 4 | `adx_H1=[35,+∞)` | 0.0400 |
| 5 | `macro_alignment=strong_against` | 0.0370 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0292 |
| 7 | `dist_low_M30=[0.7,1.5)` | 0.0281 |
| 8 | `adx_M30=[25,35)` | 0.0272 |
| 9 | `hour_bucket=12-16` | 0.0236 |
| 10 | `consec_green_M30=[2,4)` | 0.0221 |
| 11 | `us10y_chg1d=[0.5,+∞)` | 0.0220 |
| 12 | `vix_chg1d=[3,+∞)` | 0.0197 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0193 |
| 14 | `adx_H1=[25,35)` | 0.0187 |
| 15 | `bb_pctb_M30=[0.8,+∞)` | 0.0186 |

---

## XAUUSD · ml:full_power · BUY
- Toplam çözülmüş: **327**  ·  Baseline win-rate: **59.6%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 90.9%** (20 W / 2 L = 22 trade · +31.3pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d = [-0.5,0)`
   - `macro_alignment = neutral`

**2. Win-rate 84.0%** (21 W / 4 L = 25 trade · +24.4pp vs baseline)
   - `rsi_H1 = [−∞,30)`

**3. Win-rate 76.7%** (33 W / 10 L = 43 trade · +17.1pp vs baseline)
   - `rsi_H1 ≠ [−∞,30)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0380 |
| 2 | `macro_alignment=weak_against` | 0.0316 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0285 |
| 4 | `mtf_trend=all_down` | 0.0277 |
| 5 | `us10y_chg1d=[-0.5,0)` | 0.0244 |
| 6 | `rsi_H1=[−∞,30)` | 0.0243 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0220 |
| 8 | `adx_H1=[35,+∞)` | 0.0212 |
| 9 | `adx_H1=[25,35)` | 0.0210 |
| 10 | `session=overlap` | 0.0209 |
| 11 | `adx_M30=[25,35)` | 0.0207 |
| 12 | `consec_red_M30=[0,2)` | 0.0183 |
| 13 | `adx_M30=[35,+∞)` | 0.0159 |
| 14 | `M30_ema_stack=down` | 0.0156 |
| 15 | `atr_ratio_M30=[0.7,1)` | 0.0153 |

---

## XAUUSD · ml:full_power · SELL
- Toplam çözülmüş: **163**  ·  Baseline win-rate: **20.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 22 L = 22 trade · -20.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 7.7%** (2 W / 24 L = 26 trade · -13.2pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 = [0.7,1.5)`

**3. Win-rate 14.3%** (3 W / 18 L = 21 trade · -6.6pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 ≠ [0,0.3)`

**4. Win-rate 14.6%** (6 W / 35 L = 41 trade · -6.3pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `adx_M30 ≠ [25,35)`
   - `rsi_M30 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0493 |
| 2 | `adx_M30=[35,+∞)` | 0.0474 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0469 |
| 4 | `macro_alignment=strong_against` | 0.0419 |
| 5 | `adx_H1=[35,+∞)` | 0.0354 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0332 |
| 7 | `adx_M30=[25,35)` | 0.0305 |
| 8 | `dist_low_M30=[0.7,1.5)` | 0.0294 |
| 9 | `H1_adx_label=weak_trend` | 0.0263 |
| 10 | `us10y_chg1d=[−∞,-0.5)` | 0.0248 |
| 11 | `hour_bucket=12-16` | 0.0240 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0239 |
| 13 | `us10y_chg1d=[0,0.5)` | 0.0224 |
| 14 | `bb_pctb_M30=[0.8,+∞)` | 0.0206 |
| 15 | `consec_green_M30=[2,4)` | 0.0201 |

---

## XAUUSD · ml:main · BUY
- Toplam çözülmüş: **328**  ·  Baseline win-rate: **60.4%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.7%** (22 W / 1 L = 23 trade · +35.3pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**2. Win-rate 92.9%** (26 W / 2 L = 28 trade · +32.5pp vs baseline)
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**3. Win-rate 81.0%** (17 W / 4 L = 21 trade · +20.6pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket = [70,80)`
   - `dist_low_M30 ≠ [1.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 30.6%** (11 W / 25 L = 36 trade · -29.8pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket ≠ [70,80)`
   - `adx_H1 = [−∞,18)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[80,+∞)` | 0.0339 |
| 2 | `macro_alignment=weak_against` | 0.0318 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0314 |
| 4 | `M30_ema_stack=down` | 0.0286 |
| 5 | `mtf_trend=all_down` | 0.0251 |
| 6 | `adx_H1=[35,+∞)` | 0.0251 |
| 7 | `us10y_chg1d=[0.5,+∞)` | 0.0250 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0191 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0173 |
| 10 | `rsi_M30=[50,65)` | 0.0173 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0172 |
| 12 | `dist_low_M30=[1.5,+∞)` | 0.0165 |
| 13 | `rsi_M30=[30,50)` | 0.0161 |
| 14 | `adx_H1=[25,35)` | 0.0160 |
| 15 | `sar_bearish=True` | 0.0160 |

---

## XAUUSD · ml:main · SELL
- Toplam çözülmüş: **165**  ·  Baseline win-rate: **21.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 23 L = 23 trade · -21.2pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 = [0,0.3)`

**2. Win-rate 7.7%** (2 W / 24 L = 26 trade · -13.5pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 = [0.7,1.5)`

**3. Win-rate 14.3%** (3 W / 18 L = 21 trade · -6.9pp vs baseline)
   - `macro_alignment = weak_pro`
   - `macd_atr_M30 ≠ [0,0.3)`

**4. Win-rate 16.7%** (7 W / 35 L = 42 trade · -4.5pp vs baseline)
   - `macro_alignment ≠ weak_pro`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `adx_M30 ≠ [25,35)`
   - `rsi_M30 = [50,65)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=weak_pro` | 0.0501 |
| 2 | `dxy_chg1d=[-0.5,0)` | 0.0500 |
| 3 | `adx_H1=[35,+∞)` | 0.0494 |
| 4 | `adx_M30=[35,+∞)` | 0.0484 |
| 5 | `adx_M30=[25,35)` | 0.0281 |
| 6 | `macro_alignment=strong_against` | 0.0272 |
| 7 | `us10y_chg1d=[−∞,-0.5)` | 0.0250 |
| 8 | `dist_low_M30=[0.7,1.5)` | 0.0236 |
| 9 | `ml_confidence_bucket=[60,70)` | 0.0226 |
| 10 | `us10y_chg1d=[0,0.5)` | 0.0197 |
| 11 | `adx_M30=[18,25)` | 0.0197 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0187 |
| 13 | `bb_pctb_M30=[0.8,+∞)` | 0.0185 |
| 14 | `ml_confidence_bucket=[80,+∞)` | 0.0181 |
| 15 | `consec_green_M30=[2,4)` | 0.0180 |

---

## XAUUSD · ml:main_inv · BUY
- Toplam çözülmüş: **85**  ·  Baseline win-rate: **68.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.6%** (25 W / 2 L = 27 trade · +24.4pp vs baseline)
   - `dxy_chg1d = [0,0.5)`
   - `M30_ema_stack ≠ down`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `ml_confidence_bucket=[60,70)` | 0.0740 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0585 |
| 3 | `M30_adx_label=weak_trend` | 0.0459 |
| 4 | `M30_adx_label=trending` | 0.0427 |
| 5 | `dow=Mon` | 0.0401 |
| 6 | `dxy_chg1d=[0,0.5)` | 0.0360 |
| 7 | `dxy_chg1d=[-0.5,0)` | 0.0322 |
| 8 | `session=europe` | 0.0306 |
| 9 | `M30_ema_stack=down` | 0.0276 |
| 10 | `adx_M30=[35,+∞)` | 0.0244 |
| 11 | `macd_atr_M30=[0,0.3)` | 0.0236 |
| 12 | `dist_low_M30=[1.5,+∞)` | 0.0234 |
| 13 | `adx_M30=[18,25)` | 0.0234 |
| 14 | `consec_green_M30=[0,2)` | 0.0222 |
| 15 | `adx_H1=[35,+∞)` | 0.0202 |

---

## XAUUSD · ml:main_inv · SELL
- Toplam çözülmüş: **187**  ·  Baseline win-rate: **40.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 10.0%** (2 W / 18 L = 20 trade · -30.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 = [2,4)`

**2. Win-rate 23.3%** (7 W / 23 L = 30 trade · -17.3pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `consec_red_M30 ≠ [2,4)`
   - `dxy_chg1d = [0,0.5)`

**3. Win-rate 28.0%** (7 W / 18 L = 25 trade · -12.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 ≠ [0,2)`
   - `us10y_chg1d ≠ [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0635 |
| 2 | `consec_red_M30=[2,4)` | 0.0546 |
| 3 | `adx_M30=[35,+∞)` | 0.0540 |
| 4 | `macro_alignment=weak_pro` | 0.0467 |
| 5 | `consec_red_M30=[0,2)` | 0.0388 |
| 6 | `H1_adx_label=trending` | 0.0273 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0262 |
| 8 | `session=asia` | 0.0223 |
| 9 | `adx_H1=[25,35)` | 0.0208 |
| 10 | `bb_pctb_M30=[−∞,0.2)` | 0.0203 |
| 11 | `H1_adx_label=ranging` | 0.0198 |
| 12 | `macro_alignment=strong_pro` | 0.0177 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0173 |
| 14 | `us10y_chg1d=[0.5,+∞)` | 0.0164 |
| 15 | `dist_low_M30=[−∞,0.3)` | 0.0159 |

---

## XAUUSD · ml:ultra_safe · BUY
- Toplam çözülmüş: **331**  ·  Baseline win-rate: **59.8%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 92.9%** (26 W / 2 L = 28 trade · +33.1pp vs baseline)
   - `macro_alignment = weak_against`
   - `ml_confidence_bucket ≠ [80,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 91.7%** (22 W / 2 L = 24 trade · +31.9pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d = [-0.5,0)`
   - `sar_bearish = True`

**3. Win-rate 77.3%** (17 W / 5 L = 22 trade · +17.5pp vs baseline)
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `ml_confidence_bucket = [70,80)`
   - `dist_low_M30 ≠ [1.5,+∞)`

_kaçınılacak pattern bulunamadı (35% altı eşiği)_

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `M30_ema_stack=down` | 0.0279 |
| 2 | `ml_confidence_bucket=[80,+∞)` | 0.0278 |
| 3 | `mtf_trend=all_down` | 0.0274 |
| 4 | `macro_alignment=weak_against` | 0.0272 |
| 5 | `ml_confidence_bucket=[50,60)` | 0.0235 |
| 6 | `us10y_chg1d=[0.5,+∞)` | 0.0221 |
| 7 | `macro_alignment=strong_against` | 0.0205 |
| 8 | `dxy_chg1d=[0,0.5)` | 0.0204 |
| 9 | `rsi_H1=[30,50)` | 0.0196 |
| 10 | `dxy_chg1d=[-0.5,0)` | 0.0190 |
| 11 | `adx_H1=[35,+∞)` | 0.0188 |
| 12 | `mtf_trend=mixed` | 0.0186 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0183 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0169 |
| 15 | `rsi_H1=[65,75)` | 0.0165 |

---

## XAUUSD · ml:ultra_safe · SELL
- Toplam çözülmüş: **160**  ·  Baseline win-rate: **20.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -20.6pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_M30 = [50,65)`
   - `adx_M30 = [35,+∞)`

**2. Win-rate 7.7%** (2 W / 24 L = 26 trade · -12.9pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_M30 = [50,65)`
   - `adx_M30 ≠ [35,+∞)`

**3. Win-rate 9.1%** (2 W / 20 L = 22 trade · -11.5pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_M30 ≠ [50,65)`
   - `macro_alignment = weak_pro`

**4. Win-rate 10.0%** (2 W / 18 L = 20 trade · -10.6pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `macro_alignment ≠ strong_against`
   - `H1_adx_label ≠ trending`

**5. Win-rate 30.8%** (8 W / 18 L = 26 trade · 10.2pp vs baseline)
   - `dxy_chg1d ≠ [-0.5,0)`
   - `rsi_M30 ≠ [50,65)`
   - `macro_alignment ≠ weak_pro`

**6. Win-rate 33.3%** (8 W / 16 L = 24 trade · 12.7pp vs baseline)
   - `dxy_chg1d = [-0.5,0)`
   - `macro_alignment ≠ strong_against`
   - `H1_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[-0.5,0)` | 0.0556 |
| 2 | `macro_alignment=weak_pro` | 0.0433 |
| 3 | `adx_M30=[35,+∞)` | 0.0432 |
| 4 | `dxy_chg1d=[0,0.5)` | 0.0381 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0355 |
| 6 | `adx_H1=[35,+∞)` | 0.0332 |
| 7 | `macro_alignment=strong_against` | 0.0300 |
| 8 | `rsi_M30=[50,65)` | 0.0281 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0252 |
| 10 | `adx_M30=[25,35)` | 0.0228 |
| 11 | `adx_H1=[25,35)` | 0.0198 |
| 12 | `rsi_H1=[30,50)` | 0.0193 |
| 13 | `hour_bucket=20-24` | 0.0191 |
| 14 | `us10y_chg1d=[0,0.5)` | 0.0189 |
| 15 | `hour_bucket=12-16` | 0.0189 |

---

## XAUUSD · ml_cross_xau_nasdaq · BUY
- Toplam çözülmüş: **569**  ·  Baseline win-rate: **52.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 98.7%** (75 W / 1 L = 76 trade · +46.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d = [3,+∞)`
   - `dow ≠ Wed`

**2. Win-rate 77.3%** (75 W / 22 L = 97 trade · +25.1pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [65,75)`
   - `vix_chg1d ≠ [3,+∞)`
   - `dow ≠ Tue`

**3. Win-rate 76.0%** (19 W / 6 L = 25 trade · +23.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket = 00-04`
   - `dxy_chg1d ≠ [-0.5,0)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 14.0%** (12 W / 74 L = 86 trade · -38.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 12-16`
   - `H1_adx_label = ranging`

**2. Win-rate 25.0%** (7 W / 21 L = 28 trade · -27.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket = 12-16`
   - `atr_ratio_M30 = [0.7,1)`

**3. Win-rate 29.4%** (10 W / 24 L = 34 trade · -22.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [65,75)`

**4. Win-rate 33.3%** (37 W / 74 L = 111 trade · -18.9pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `hour_bucket ≠ 00-04`
   - `hour_bucket ≠ 12-16`
   - `H1_adx_label ≠ ranging`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1026 |
| 2 | `adx_H1=[35,+∞)` | 0.0493 |
| 3 | `macro_alignment=weak_against` | 0.0482 |
| 4 | `M30_adx_label=trending` | 0.0349 |
| 5 | `H1_adx_label=ranging` | 0.0323 |
| 6 | `mtf_trend=NA` | 0.0276 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0256 |
| 8 | `dow=Fri` | 0.0244 |
| 9 | `adx_H1=[−∞,18)` | 0.0244 |
| 10 | `M30_adx_label=weak_trend` | 0.0240 |
| 11 | `adx_M30=[18,25)` | 0.0234 |
| 12 | `macro_alignment=strong_against` | 0.0219 |
| 13 | `M30_ema_stack=NA` | 0.0204 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0189 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0185 |

---

## XAUUSD · ml_cross_xau_nasdaq · SELL
- Toplam çözülmüş: **284**  ·  Baseline win-rate: **14.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -14.4pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label = ranging`

**2. Win-rate 0.0%** (0 W / 35 L = 35 trade · -14.4pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment ≠ weak_pro`

**3. Win-rate 0.0%** (0 W / 69 L = 69 trade · -14.4pp vs baseline)
   - `dxy_chg1d = [0.5,+∞)`

**4. Win-rate 8.7%** (2 W / 21 L = 23 trade · -5.7pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `macro_alignment = weak_pro`

**5. Win-rate 14.3%** (3 W / 18 L = 21 trade · -0.1pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `hour_bucket = 04-08`

**6. Win-rate 25.0%** (5 W / 15 L = 20 trade · 10.6pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `H1_adx_label ≠ ranging`

**7. Win-rate 25.8%** (8 W / 23 L = 31 trade · 11.4pp vs baseline)
   - `dxy_chg1d ≠ [0.5,+∞)`
   - `adx_H1 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dxy_chg1d=[0.5,+∞)` | 0.0942 |
| 2 | `us10y_chg1d=[−∞,-0.5)` | 0.0680 |
| 3 | `vix_chg1d=[3,+∞)` | 0.0446 |
| 4 | `dow=Mon` | 0.0329 |
| 5 | `adx_H1=[35,+∞)` | 0.0329 |
| 6 | `vix_chg1d=[−∞,-3)` | 0.0274 |
| 7 | `near_support=True` | 0.0233 |
| 8 | `session=asia` | 0.0222 |
| 9 | `hour_bucket=00-04` | 0.0210 |
| 10 | `consec_red_M30=[0,2)` | 0.0192 |
| 11 | `near_support=False` | 0.0191 |
| 12 | `dxy_chg1d=[0,0.5)` | 0.0187 |
| 13 | `macro_alignment=weak_pro` | 0.0185 |
| 14 | `dxy_chg1d=[-0.5,0)` | 0.0180 |
| 15 | `atr_ratio_M30=[1,1.3)` | 0.0180 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · BUY
- Toplam çözülmüş: **146**  ·  Baseline win-rate: **49.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 82.1%** (23 W / 5 L = 28 trade · +32.8pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `atr_ratio_M30 ≠ [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 18.5%** (5 W / 22 L = 27 trade · -30.8pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [0,2)`
   - `macd_atr_M30 ≠ [-0.3,0)`

**2. Win-rate 25.0%** (5 W / 15 L = 20 trade · -24.3pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `consec_red_M30 = [0,2)`
   - `macd_atr_M30 = [-0.3,0)`
   - `us10y_chg1d = [0.5,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0822 |
| 2 | `adx_H1=[35,+∞)` | 0.0740 |
| 3 | `consec_red_M30=[0,2)` | 0.0568 |
| 4 | `M30_adx_label=trending` | 0.0440 |
| 5 | `H1_adx_label=trending` | 0.0396 |
| 6 | `dow=Mon` | 0.0315 |
| 7 | `dist_low_M30=[0.7,1.5)` | 0.0314 |
| 8 | `bb_extreme_lower=False` | 0.0312 |
| 9 | `dist_low_M30=[1.5,+∞)` | 0.0285 |
| 10 | `bb_extreme_lower=True` | 0.0275 |
| 11 | `adx_M30=[25,35)` | 0.0260 |
| 12 | `adx_H1=[18,25)` | 0.0244 |
| 13 | `macd_atr_M30=[-0.3,0)` | 0.0227 |
| 14 | `ml_confidence_bucket=[70,80)` | 0.0219 |
| 15 | `bb_pctb_M30=[−∞,0.2)` | 0.0210 |

---

## XAUUSD · ml_cross_xau_nasdaq_inv · SELL
- Toplam çözülmüş: **472**  ·  Baseline win-rate: **21.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 47 L = 47 trade · -21.6pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend ≠ mixed`

**2. Win-rate 3.1%** (1 W / 31 L = 32 trade · -18.5pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d = [−∞,-0.5)`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -17.1pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 = NA`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 4.8%** (1 W / 20 L = 21 trade · -16.8pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 ≠ [50,65)`
   - `mtf_trend = mixed`

**5. Win-rate 9.5%** (2 W / 19 L = 21 trade · -12.1pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `rsi_M30 = [50,65)`

**6. Win-rate 11.3%** (6 W / 47 L = 53 trade · -10.3pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 ≠ NA`
   - `vix_chg1d = [−∞,-3)`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**7. Win-rate 11.4%** (4 W / 31 L = 35 trade · -10.2pp vs baseline)
   - `adx_H1 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `us10y_chg1d ≠ [−∞,-0.5)`
   - `vix_chg1d = [3,+∞)`

**8. Win-rate 19.4%** (6 W / 25 L = 31 trade · -2.2pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 ≠ NA`
   - `vix_chg1d ≠ [−∞,-3)`
   - `hour_bucket = 08-12`

**9. Win-rate 20.0%** (4 W / 16 L = 20 trade · -1.6pp vs baseline)
   - `adx_H1 ≠ [35,+∞)`
   - `adx_H1 = NA`
   - `adx_M30 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_H1=[35,+∞)` | 0.0644 |
| 2 | `adx_M30=[35,+∞)` | 0.0419 |
| 3 | `macro_alignment=weak_pro` | 0.0406 |
| 4 | `vix_chg1d=[3,+∞)` | 0.0336 |
| 5 | `M30_adx_label=trending` | 0.0291 |
| 6 | `dist_high_M30=[1.5,+∞)` | 0.0249 |
| 7 | `M30_ema_stack=up` | 0.0225 |
| 8 | `hour_bucket=12-16` | 0.0213 |
| 9 | `H1_adx_label=trending` | 0.0202 |
| 10 | `rsi_H1=[30,50)` | 0.0193 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0185 |
| 12 | `bb_pctb_M30=[0.5,0.8)` | 0.0174 |
| 13 | `mtf_trend=all_up` | 0.0172 |
| 14 | `bb_pctb_M30=[0.2,0.5)` | 0.0172 |
| 15 | `dxy_chg1d=[-0.5,0)` | 0.0162 |

---

## XAUUSD · pulse1 · BUY
- Toplam çözülmüş: **993**  ·  Baseline win-rate: **39.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (29 W / 0 L = 29 trade · +60.9pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 = [−∞,0.7)`
   - `bb_pctb_M30 = [0.5,0.8)`

**2. Win-rate 100.0%** (34 W / 0 L = 34 trade · +60.9pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d ≠ [0,3)`
   - `hour_bucket = 16-20`

**3. Win-rate 100.0%** (47 W / 0 L = 47 trade · +60.9pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d = [-0.5,0)`
   - `vix_chg1d = [0,3)`

**4. Win-rate 91.3%** (21 W / 2 L = 23 trade · +52.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `adx_H1 = [35,+∞)`
   - `dow = Fri`

**5. Win-rate 88.7%** (55 W / 7 L = 62 trade · +49.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment ≠ strong_pro`
   - `atr_ratio_M30 = [0.7,1)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 9.0%** (19 W / 193 L = 212 trade · -30.1pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `adx_H1 ≠ [35,+∞)`
   - `M30_adx_label ≠ trending`

**2. Win-rate 12.5%** (3 W / 21 L = 24 trade · -26.6pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 = [65,75)`
   - `macro_alignment = strong_pro`

**3. Win-rate 17.9%** (10 W / 46 L = 56 trade · -21.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Fri`

**4. Win-rate 22.9%** (32 W / 108 L = 140 trade · -16.2pp vs baseline)
   - `mtf_trend ≠ all_down`
   - `rsi_M30 ≠ [65,75)`
   - `adx_H1 ≠ [35,+∞)`
   - `M30_adx_label = trending`

**5. Win-rate 23.6%** (43 W / 139 L = 182 trade · -15.5pp vs baseline)
   - `mtf_trend = all_down`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `atr_ratio_M30 ≠ [−∞,0.7)`
   - `rsi_H1 = [30,50)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.0627 |
| 2 | `mtf_trend=all_down` | 0.0502 |
| 3 | `M30_ema_stack=down` | 0.0389 |
| 4 | `us10y_chg1d=[−∞,-0.5)` | 0.0288 |
| 5 | `macro_alignment=strong_pro` | 0.0282 |
| 6 | `dow=Mon` | 0.0266 |
| 7 | `dow=Fri` | 0.0249 |
| 8 | `rsi_M30=[65,75)` | 0.0246 |
| 9 | `adx_H1=[35,+∞)` | 0.0218 |
| 10 | `vix_chg1d=[3,+∞)` | 0.0206 |
| 11 | `adx_M30=[35,+∞)` | 0.0191 |
| 12 | `us10y_chg1d=[0.5,+∞)` | 0.0164 |
| 13 | `H1_adx_label=trending` | 0.0162 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0159 |
| 15 | `vix_chg1d=[−∞,-3)` | 0.0146 |

---

## XAUUSD · pulse1 · SELL
- Toplam çözülmüş: **1910**  ·  Baseline win-rate: **10.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 42 L = 42 trade · -10.4pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket = 12-16`
   - `dow ≠ Mon`
   - `us10y_chg1d = [-0.5,0)`

**2. Win-rate 0.0%** (0 W / 36 L = 36 trade · -10.4pp vs baseline)
   - `adx_H1 = [18,25)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `oversold ≠ False`
   - `ml_confidence_bucket = [80,+∞)`

**3. Win-rate 0.0%** (0 W / 57 L = 57 trade · -10.4pp vs baseline)
   - `adx_H1 = [18,25)`
   - `vix_chg1d = [−∞,-3)`
   - `dist_low_M30 ≠ [0.7,1.5)`

**4. Win-rate 2.5%** (11 W / 427 L = 438 trade · -7.9pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `adx_M30 = [35,+∞)`
   - `session ≠ europe`

**5. Win-rate 3.7%** (7 W / 184 L = 191 trade · -6.7pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `adx_M30 ≠ [35,+∞)`
   - `dow = Thu`

**6. Win-rate 4.2%** (1 W / 23 L = 24 trade · -6.2pp vs baseline)
   - `adx_H1 = [18,25)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `oversold ≠ False`
   - `ml_confidence_bucket ≠ [80,+∞)`

**7. Win-rate 4.8%** (1 W / 20 L = 21 trade · -5.6pp vs baseline)
   - `adx_H1 = [18,25)`
   - `vix_chg1d = [−∞,-3)`
   - `dist_low_M30 = [0.7,1.5)`

**8. Win-rate 7.7%** (2 W / 24 L = 26 trade · -2.7pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket = 12-16`
   - `dow = Mon`
   - `us10y_chg1d = [0.5,+∞)`

**9. Win-rate 7.9%** (9 W / 105 L = 114 trade · -2.5pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `adx_M30 = [35,+∞)`
   - `session = europe`

**10. Win-rate 11.3%** (47 W / 369 L = 416 trade · 0.9pp vs baseline)
   - `adx_H1 ≠ [18,25)`
   - `hour_bucket ≠ 12-16`
   - `adx_M30 ≠ [35,+∞)`
   - `dow ≠ Thu`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=strong_against` | 0.0409 |
| 2 | `adx_M30=[35,+∞)` | 0.0315 |
| 3 | `adx_H1=[35,+∞)` | 0.0289 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0263 |
| 5 | `adx_M30=[25,35)` | 0.0258 |
| 6 | `vix_chg1d=[0,3)` | 0.0252 |
| 7 | `H1_adx_label=weak_trend` | 0.0249 |
| 8 | `dow=Thu` | 0.0246 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0246 |
| 10 | `adx_H1=[18,25)` | 0.0239 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0218 |
| 12 | `dow=Fri` | 0.0195 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0193 |
| 14 | `rsi_H1=[30,50)` | 0.0171 |
| 15 | `us10y_chg1d=[0.5,+∞)` | 0.0161 |

---

## XAUUSD · pulse1_inv · BUY
- Toplam çözülmüş: **587**  ·  Baseline win-rate: **53.3%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 95.2%** (99 W / 5 L = 104 trade · +41.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dist_low_M30 = [1.5,+∞)`
   - `consec_red_M30 ≠ [2,4)`

**2. Win-rate 86.1%** (31 W / 5 L = 36 trade · +32.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dist_low_M30 ≠ [1.5,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**3. Win-rate 85.7%** (18 W / 3 L = 21 trade · +32.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `hour_bucket = 04-08`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 23.1%** (6 W / 20 L = 26 trade · -30.2pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `hour_bucket ≠ 04-08`
   - `rsi_M30 ≠ [30,50)`

**2. Win-rate 23.3%** (42 W / 138 L = 180 trade · -30.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `atr_ratio_M30 ≠ [1,1.3)`
   - `atr_ratio_M30 ≠ [1.3,1.7)`

**3. Win-rate 34.6%** (18 W / 34 L = 52 trade · -18.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `bb_extreme_upper = False`
   - `atr_ratio_M30 = [1,1.3)`
   - `macd_atr_M30 ≠ [-0.3,0)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0975 |
| 2 | `adx_H1=[35,+∞)` | 0.0833 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0465 |
| 4 | `M30_adx_label=trending` | 0.0430 |
| 5 | `H1_adx_label=trending` | 0.0331 |
| 6 | `adx_M30=[18,25)` | 0.0320 |
| 7 | `ml_confidence_bucket=[80,+∞)` | 0.0292 |
| 8 | `H1_adx_label=ranging` | 0.0286 |
| 9 | `M30_adx_label=weak_trend` | 0.0265 |
| 10 | `adx_M30=[25,35)` | 0.0240 |
| 11 | `dxy_chg1d=[0,0.5)` | 0.0233 |
| 12 | `dxy_chg1d=[-0.5,0)` | 0.0216 |
| 13 | `macro_alignment=weak_against` | 0.0207 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0161 |
| 15 | `adx_H1=[−∞,18)` | 0.0155 |

---

## XAUUSD · pulse1_inv · SELL
- Toplam çözülmüş: **294**  ·  Baseline win-rate: **27.9%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 3.8%** (1 W / 25 L = 26 trade · -24.1pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment = weak_pro`

**2. Win-rate 18.3%** (26 W / 116 L = 142 trade · -9.6pp vs baseline)
   - `session ≠ overlap`
   - `macro_alignment ≠ weak_pro`
   - `bb_extreme_upper ≠ True`
   - `hour_bucket ≠ 00-04`

**3. Win-rate 25.0%** (6 W / 18 L = 24 trade · -2.9pp vs baseline)
   - `session = overlap`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `hour_bucket=12-16` | 0.0369 |
| 2 | `session=overlap` | 0.0278 |
| 3 | `atr_ratio_M30=[0.7,1)` | 0.0236 |
| 4 | `vix_chg1d=[−∞,-3)` | 0.0213 |
| 5 | `bb_extreme_upper=True` | 0.0193 |
| 6 | `consec_red_M30=[2,4)` | 0.0193 |
| 7 | `dist_low_M30=[0.7,1.5)` | 0.0189 |
| 8 | `hour_bucket=08-12` | 0.0187 |
| 9 | `session=europe` | 0.0181 |
| 10 | `adx_H1=[−∞,18)` | 0.0178 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0178 |
| 12 | `M30_adx_label=weak_trend` | 0.0176 |
| 13 | `rsi_H1=[30,50)` | 0.0175 |
| 14 | `H1_adx_label=ranging` | 0.0174 |
| 15 | `rsi_M30=[50,65)` | 0.0168 |

---

## XAUUSD · pulse2 · BUY
- Toplam çözülmüş: **1226**  ·  Baseline win-rate: **35.9%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 79.0%** (94 W / 25 L = 119 trade · +43.1pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment = weak_pro`
   - `dow ≠ Wed`
   - `vix_chg1d ≠ [3,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 20 L = 20 trade · -35.9pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `H1_adx_label = NA`
   - `dist_low_M30 ≠ [1.5,+∞)`

**2. Win-rate 0.0%** (0 W / 35 L = 35 trade · -35.9pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_M30 = [30,50)`
   - `M30_adx_label = ranging`

**3. Win-rate 3.4%** (1 W / 28 L = 29 trade · -32.5pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `H1_adx_label ≠ NA`
   - `dxy_chg1d = [0.5,+∞)`

**4. Win-rate 4.0%** (2 W / 48 L = 50 trade · -31.9pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_M30 = [30,50)`
   - `M30_adx_label ≠ ranging`
   - `dow = Wed`

**5. Win-rate 5.0%** (2 W / 38 L = 40 trade · -30.9pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_M30 ≠ [30,50)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `macd_atr_M30 = [0,0.3)`

**6. Win-rate 15.0%** (3 W / 17 L = 20 trade · -20.9pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `H1_adx_label = NA`
   - `dist_low_M30 = [1.5,+∞)`

**7. Win-rate 15.4%** (4 W / 22 L = 26 trade · -20.5pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment = weak_pro`
   - `dow = Wed`

**8. Win-rate 18.9%** (20 W / 86 L = 106 trade · -17.0pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_M30 = [30,50)`
   - `M30_adx_label ≠ ranging`
   - `dow ≠ Wed`

**9. Win-rate 20.0%** (11 W / 44 L = 55 trade · -15.9pp vs baseline)
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_M30 ≠ [30,50)`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `macd_atr_M30 ≠ [0,0.3)`

**10. Win-rate 29.2%** (7 W / 17 L = 24 trade · -6.7pp vs baseline)
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `macro_alignment = weak_pro`
   - `dow ≠ Wed`
   - `vix_chg1d = [3,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0441 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0435 |
| 3 | `macro_alignment=weak_pro` | 0.0280 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0279 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0272 |
| 6 | `dow=Wed` | 0.0259 |
| 7 | `dow=Fri` | 0.0259 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0234 |
| 9 | `dow=Tue` | 0.0195 |
| 10 | `macro_alignment=strong_against` | 0.0193 |
| 11 | `rsi_M30=[65,75)` | 0.0186 |
| 12 | `rsi_M30=[30,50)` | 0.0172 |
| 13 | `dist_low_M30=[1.5,+∞)` | 0.0165 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0157 |
| 15 | `adx_H1=[18,25)` | 0.0150 |

---

## XAUUSD · pulse2 · SELL
- Toplam çözülmüş: **1400**  ·  Baseline win-rate: **9.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 87 L = 87 trade · -9.6pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `consec_green_M30 = [0,2)`

**2. Win-rate 0.0%** (0 W / 24 L = 24 trade · -9.6pp vs baseline)
   - `macro_alignment = strong_against`
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 = [50,65)`
   - `M30_adx_label ≠ trending`

**3. Win-rate 0.0%** (0 W / 75 L = 75 trade · -9.6pp vs baseline)
   - `macro_alignment = strong_against`
   - `adx_M30 = [35,+∞)`

**4. Win-rate 0.4%** (2 W / 461 L = 463 trade · -9.2pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**5. Win-rate 4.1%** (5 W / 117 L = 122 trade · -5.5pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d = [0.5,+∞)`
   - `dow ≠ Mon`

**6. Win-rate 5.8%** (3 W / 49 L = 52 trade · -3.8pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `consec_green_M30 ≠ [0,2)`

**7. Win-rate 8.0%** (11 W / 126 L = 137 trade · -1.6pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `adx_H1 = [35,+∞)`

**8. Win-rate 9.1%** (2 W / 20 L = 22 trade · -0.5pp vs baseline)
   - `macro_alignment = strong_against`
   - `adx_M30 ≠ [35,+∞)`
   - `rsi_H1 = [50,65)`
   - `M30_adx_label = trending`

**9. Win-rate 9.5%** (2 W / 19 L = 21 trade · -0.1pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `ml_confidence_bucket = [80,+∞)`

**10. Win-rate 18.0%** (33 W / 150 L = 183 trade · 8.4pp vs baseline)
   - `macro_alignment ≠ strong_against`
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `adx_H1 ≠ [35,+∞)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `macro_alignment=strong_against` | 0.0728 |
| 2 | `vix_chg1d=[−∞,-3)` | 0.0478 |
| 3 | `us10y_chg1d=[-0.5,0)` | 0.0375 |
| 4 | `adx_H1=[35,+∞)` | 0.0366 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0340 |
| 6 | `H1_adx_label=weak_trend` | 0.0300 |
| 7 | `adx_M30=[35,+∞)` | 0.0279 |
| 8 | `dow=Tue` | 0.0251 |
| 9 | `vix_chg1d=[3,+∞)` | 0.0246 |
| 10 | `adx_H1=[18,25)` | 0.0240 |
| 11 | `rsi_H1=[30,50)` | 0.0212 |
| 12 | `atr_ratio_M30=[1,1.3)` | 0.0208 |
| 13 | `macro_alignment=weak_against` | 0.0200 |
| 14 | `rsi_H1=[50,65)` | 0.0181 |
| 15 | `dow=Mon` | 0.0166 |

---

## XAUUSD · pulse2_inv · BUY
- Toplam çözülmüş: **410**  ·  Baseline win-rate: **62.2%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (50 W / 0 L = 50 trade · +37.8pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 ≠ [0.5,0.8)`

**2. Win-rate 90.2%** (55 W / 6 L = 61 trade · +28.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `macro_alignment ≠ weak_against`
   - `us10y_chg1d ≠ [0.5,+∞)`

**3. Win-rate 88.5%** (23 W / 3 L = 26 trade · +26.3pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `macro_alignment = weak_against`
   - `bb_pctb_M30 = [0.5,0.8)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 25.2%** (26 W / 77 L = 103 trade · -37.0pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `consec_red_M30 = [0,2)`
   - `vix_chg1d ≠ [−∞,-3)`
   - `hour_bucket ≠ 12-16`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1217 |
| 2 | `adx_H1=[35,+∞)` | 0.0648 |
| 3 | `adx_M30=[25,35)` | 0.0563 |
| 4 | `M30_adx_label=trending` | 0.0449 |
| 5 | `M30_adx_label=weak_trend` | 0.0424 |
| 6 | `adx_M30=[18,25)` | 0.0390 |
| 7 | `dxy_chg1d=[0,0.5)` | 0.0375 |
| 8 | `dxy_chg1d=[-0.5,0)` | 0.0347 |
| 9 | `dist_high_M30=[1.5,+∞)` | 0.0332 |
| 10 | `H1_adx_label=trending` | 0.0190 |
| 11 | `adx_H1=[25,35)` | 0.0178 |
| 12 | `macro_alignment=weak_against` | 0.0160 |
| 13 | `mtf_trend=all_down` | 0.0158 |
| 14 | `consec_red_M30=[0,2)` | 0.0155 |
| 15 | `dist_low_M30=[1.5,+∞)` | 0.0148 |

---

## XAUUSD · pulse2_inv · SELL
- Toplam çözülmüş: **449**  ·  Baseline win-rate: **25.6%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 36 L = 36 trade · -25.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 ≠ [0.7,1)`

**2. Win-rate 7.1%** (2 W / 26 L = 28 trade · -18.5pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `macd_atr_M30 = [0,0.3)`

**3. Win-rate 8.9%** (4 W / 41 L = 45 trade · -16.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session = asia`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `H1_adx_label ≠ trending`

**4. Win-rate 10.0%** (2 W / 18 L = 20 trade · -15.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment = weak_pro`

**5. Win-rate 18.9%** (7 W / 30 L = 37 trade · -6.7pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session ≠ asia`
   - `session = us`

**6. Win-rate 20.0%** (4 W / 16 L = 20 trade · -5.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 = [30,50)`
   - `atr_ratio_M30 = [0.7,1)`
   - `macro_alignment ≠ weak_pro`

**7. Win-rate 26.2%** (11 W / 31 L = 42 trade · 0.6pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [30,50)`
   - `hour_bucket ≠ 12-16`
   - `macd_atr_M30 ≠ [0,0.3)`

**8. Win-rate 28.7%** (23 W / 57 L = 80 trade · 3.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session ≠ asia`
   - `session ≠ us`
   - `atr_ratio_M30 = [0.7,1)`

**9. Win-rate 30.8%** (8 W / 18 L = 26 trade · 5.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `session = asia`
   - `dist_low_M30 ≠ [0.7,1.5)`
   - `H1_adx_label = trending`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0423 |
| 2 | `macro_alignment=weak_pro` | 0.0292 |
| 3 | `us10y_chg1d=[−∞,-0.5)` | 0.0258 |
| 4 | `adx_M30=[25,35)` | 0.0253 |
| 5 | `rsi_H1=[30,50)` | 0.0227 |
| 6 | `session=asia` | 0.0223 |
| 7 | `hour_bucket=12-16` | 0.0208 |
| 8 | `vix_chg1d=[3,+∞)` | 0.0205 |
| 9 | `session=us` | 0.0200 |
| 10 | `atr_ratio_M30=[1,1.3)` | 0.0191 |
| 11 | `us10y_chg1d=[0,0.5)` | 0.0188 |
| 12 | `ml_confidence_bucket=[80,+∞)` | 0.0183 |
| 13 | `adx_H1=[35,+∞)` | 0.0180 |
| 14 | `dist_high_M30=[1.5,+∞)` | 0.0177 |
| 15 | `dow=Mon` | 0.0158 |

---

## XAUUSD · pulse3 · BUY
- Toplam çözülmüş: **1136**  ·  Baseline win-rate: **43.5%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 96.0%** (120 W / 5 L = 125 trade · +52.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow ≠ Wed`
   - `dow = Fri`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 33 L = 33 trade · -43.5pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d ≠ [−∞,-0.5)`

**2. Win-rate 0.0%** (0 W / 73 L = 73 trade · -43.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 ≠ [−∞,0.2)`

**3. Win-rate 7.9%** (3 W / 35 L = 38 trade · -35.6pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow ≠ Mon`
   - `bb_pctb_M30 = [−∞,0.2)`

**4. Win-rate 12.8%** (12 W / 82 L = 94 trade · -30.7pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `mtf_trend ≠ all_up`
   - `ml_confidence_bucket ≠ [70,80)`

**5. Win-rate 24.0%** (6 W / 19 L = 25 trade · -19.5pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`
   - `mtf_trend = all_up`
   - `dxy_chg1d = [-0.5,0)`

**6. Win-rate 25.9%** (7 W / 20 L = 27 trade · -17.6pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 = [35,+∞)`
   - `dow = Wed`

**7. Win-rate 26.7%** (8 W / 22 L = 30 trade · -16.8pp vs baseline)
   - `vix_chg1d ≠ [3,+∞)`
   - `adx_H1 ≠ [35,+∞)`
   - `mtf_trend = NA`
   - `us10y_chg1d = [−∞,-0.5)`

**8. Win-rate 32.4%** (12 W / 25 L = 37 trade · -11.1pp vs baseline)
   - `vix_chg1d = [3,+∞)`
   - `dist_high_M30 = [1.5,+∞)`
   - `dow = Mon`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `vix_chg1d=[3,+∞)` | 0.0881 |
| 2 | `us10y_chg1d=[0.5,+∞)` | 0.0645 |
| 3 | `dow=Fri` | 0.0500 |
| 4 | `us10y_chg1d=[-0.5,0)` | 0.0386 |
| 5 | `adx_H1=[35,+∞)` | 0.0342 |
| 6 | `vix_chg1d=[−∞,-3)` | 0.0250 |
| 7 | `dow=Wed` | 0.0222 |
| 8 | `macro_alignment=weak_pro` | 0.0219 |
| 9 | `H1_adx_label=trending` | 0.0214 |
| 10 | `mtf_trend=all_up` | 0.0173 |
| 11 | `vix_chg1d=[-3,0)` | 0.0156 |
| 12 | `ml_confidence_bucket=[−∞,50)` | 0.0154 |
| 13 | `adx_M30=[35,+∞)` | 0.0152 |
| 14 | `macro_alignment=strong_pro` | 0.0151 |
| 15 | `M30_ema_stack=up` | 0.0149 |

---

## XAUUSD · pulse3 · SELL
- Toplam çözülmüş: **1666**  ·  Baseline win-rate: **10.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 50 L = 50 trade · -10.2pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment = strong_against`
   - `rsi_H1 ≠ [30,50)`
   - `ml_confidence_bucket = [80,+∞)`

**2. Win-rate 1.7%** (2 W / 114 L = 116 trade · -8.5pp vs baseline)
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `mtf_trend ≠ all_down`
   - `hour_bucket ≠ 08-12`

**3. Win-rate 2.6%** (2 W / 74 L = 76 trade · -7.6pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment ≠ strong_against`
   - `session = us`
   - `macd_atr_M30 ≠ [-0.3,0)`

**4. Win-rate 2.7%** (22 W / 803 L = 825 trade · -7.5pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment ≠ strong_against`
   - `session ≠ us`
   - `dow ≠ Sun`

**5. Win-rate 4.8%** (1 W / 20 L = 21 trade · -5.4pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment = strong_against`
   - `rsi_H1 = [30,50)`
   - `mtf_trend = all_up`

**6. Win-rate 5.5%** (5 W / 86 L = 91 trade · -4.7pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment = strong_against`
   - `rsi_H1 ≠ [30,50)`
   - `ml_confidence_bucket ≠ [80,+∞)`

**7. Win-rate 9.8%** (8 W / 74 L = 82 trade · -0.4pp vs baseline)
   - `dow = Mon`
   - `sar_bearish ≠ False`
   - `mtf_trend = all_down`
   - `adx_H1 = [35,+∞)`

**8. Win-rate 17.2%** (5 W / 24 L = 29 trade · 7.0pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment ≠ strong_against`
   - `session ≠ us`
   - `dow = Sun`

**9. Win-rate 18.4%** (14 W / 62 L = 76 trade · 8.2pp vs baseline)
   - `dow ≠ Mon`
   - `macro_alignment ≠ strong_against`
   - `session = us`
   - `macd_atr_M30 = [-0.3,0)`

**10. Win-rate 20.0%** (5 W / 20 L = 25 trade · 9.8pp vs baseline)
   - `dow = Mon`
   - `sar_bearish = False`
   - `macro_alignment ≠ weak_pro`
   - `bb_pctb_M30 = [0.5,0.8)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Mon` | 0.0475 |
| 2 | `dow=Thu` | 0.0386 |
| 3 | `dxy_chg1d=[-0.5,0)` | 0.0330 |
| 4 | `adx_H1=[35,+∞)` | 0.0313 |
| 5 | `macro_alignment=strong_against` | 0.0311 |
| 6 | `us10y_chg1d=[-0.5,0)` | 0.0242 |
| 7 | `vix_chg1d=[0,3)` | 0.0208 |
| 8 | `H1_adx_label=weak_trend` | 0.0195 |
| 9 | `vix_chg1d=[−∞,-3)` | 0.0187 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0185 |
| 11 | `adx_H1=[18,25)` | 0.0176 |
| 12 | `rsi_H1=[30,50)` | 0.0173 |
| 13 | `us10y_chg1d=[−∞,-0.5)` | 0.0159 |
| 14 | `atr_ratio_M30=[1,1.3)` | 0.0153 |
| 15 | `vix_chg1d=[3,+∞)` | 0.0147 |

---

## XAUUSD · pulse3_inv · BUY
- Toplam çözülmüş: **388**  ·  Baseline win-rate: **60.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (54 W / 0 L = 54 trade · +39.9pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 ≠ [1.5,+∞)`

**2. Win-rate 85.5%** (53 W / 9 L = 62 trade · +25.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `rsi_H1 ≠ [−∞,30)`
   - `adx_H1 = [35,+∞)`
   - `dist_high_M30 = [1.5,+∞)`

**3. Win-rate 78.3%** (18 W / 5 L = 23 trade · +18.2pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_support ≠ False`
   - `macro_alignment = weak_against`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 24.7%** (21 W / 64 L = 85 trade · -35.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `near_support = False`
   - `M30_adx_label ≠ ranging`
   - `macro_alignment ≠ neutral`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.1523 |
| 2 | `adx_H1=[35,+∞)` | 0.0796 |
| 3 | `adx_M30=[25,35)` | 0.0488 |
| 4 | `M30_adx_label=trending` | 0.0379 |
| 5 | `M30_adx_label=weak_trend` | 0.0356 |
| 6 | `adx_M30=[18,25)` | 0.0324 |
| 7 | `dist_low_M30=[1.5,+∞)` | 0.0236 |
| 8 | `dist_high_M30=[1.5,+∞)` | 0.0236 |
| 9 | `H1_adx_label=trending` | 0.0233 |
| 10 | `dxy_chg1d=[0,0.5)` | 0.0206 |
| 11 | `dxy_chg1d=[-0.5,0)` | 0.0205 |
| 12 | `mtf_trend=all_down` | 0.0197 |
| 13 | `M30_ema_stack=down` | 0.0161 |
| 14 | `H1_adx_label=ranging` | 0.0159 |
| 15 | `adx_H1=[25,35)` | 0.0155 |

---

## XAUUSD · pulse3_inv · SELL
- Toplam çözülmüş: **425**  ·  Baseline win-rate: **21.4%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 29 L = 29 trade · -21.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d = [−∞,-3)`

**2. Win-rate 0.0%** (0 W / 50 L = 50 trade · -21.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 = [50,65)`

**3. Win-rate 11.4%** (4 W / 31 L = 35 trade · -10.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d = [3,+∞)`
   - `rsi_M30 ≠ [50,65)`

**4. Win-rate 14.3%** (5 W / 30 L = 35 trade · -7.1pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment = weak_pro`

**5. Win-rate 15.0%** (3 W / 17 L = 20 trade · -6.4pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `ml_confidence_bucket = [70,80)`

**6. Win-rate 15.0%** (3 W / 17 L = 20 trade · -6.4pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d = [0.5,+∞)`
   - `rsi_H1 = [65,75)`

**7. Win-rate 15.4%** (4 W / 22 L = 26 trade · -6.0pp vs baseline)
   - `adx_M30 = [35,+∞)`
   - `vix_chg1d ≠ [3,+∞)`
   - `us10y_chg1d ≠ [0.5,+∞)`
   - `vix_chg1d ≠ [−∞,-3)`

**8. Win-rate 23.2%** (16 W / 53 L = 69 trade · 1.8pp vs baseline)
   - `adx_M30 ≠ [35,+∞)`
   - `macro_alignment ≠ weak_pro`
   - `ml_confidence_bucket ≠ [70,80)`
   - `mtf_trend = mixed`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[35,+∞)` | 0.0618 |
| 2 | `vix_chg1d=[−∞,-3)` | 0.0276 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0255 |
| 4 | `volatility_regime=normal` | 0.0246 |
| 5 | `ml_confidence_bucket=[−∞,50)` | 0.0240 |
| 6 | `rsi_H1=[50,65)` | 0.0237 |
| 7 | `vix_chg1d=[3,+∞)` | 0.0213 |
| 8 | `macro_alignment=weak_pro` | 0.0208 |
| 9 | `adx_H1=[35,+∞)` | 0.0194 |
| 10 | `M30_adx_label=trending` | 0.0193 |
| 11 | `mtf_trend=mixed` | 0.0188 |
| 12 | `ml_confidence_bucket=[50,60)` | 0.0167 |
| 13 | `dist_high_M30=[0.7,1.5)` | 0.0165 |
| 14 | `H1_adx_label=trending` | 0.0164 |
| 15 | `dow=Mon` | 0.0154 |

---

## XAUUSD · smc · BUY
- Toplam çözülmüş: **246**  ·  Baseline win-rate: **70.7%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (56 W / 0 L = 56 trade · +29.3pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack = down`
   - `macd_atr_M30 ≠ [-0.3,0)`

**2. Win-rate 95.5%** (21 W / 1 L = 22 trade · +24.8pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment = weak_against`
   - `vix_chg1d ≠ [3,+∞)`

**3. Win-rate 95.0%** (19 W / 1 L = 20 trade · +24.3pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack = down`
   - `macd_atr_M30 = [-0.3,0)`

**4. Win-rate 88.9%** (32 W / 4 L = 36 trade · +18.2pp vs baseline)
   - `us10y_chg1d = [-0.5,0)`
   - `M30_ema_stack ≠ down`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 16.0%** (4 W / 21 L = 25 trade · -54.7pp vs baseline)
   - `us10y_chg1d ≠ [-0.5,0)`
   - `macro_alignment ≠ weak_against`
   - `atr_ratio_M30 ≠ [0.7,1)`
   - `sar_bearish = False`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `us10y_chg1d=[-0.5,0)` | 0.1631 |
| 2 | `mtf_trend=all_down` | 0.0668 |
| 3 | `M30_ema_stack=down` | 0.0657 |
| 4 | `us10y_chg1d=[0.5,+∞)` | 0.0395 |
| 5 | `us10y_chg1d=[−∞,-0.5)` | 0.0257 |
| 6 | `ml_confidence_bucket=[70,80)` | 0.0250 |
| 7 | `session=asia` | 0.0248 |
| 8 | `macro_alignment=strong_pro` | 0.0227 |
| 9 | `atr_ratio_M30=[0.7,1)` | 0.0201 |
| 10 | `hour_bucket=20-24` | 0.0200 |
| 11 | `atr_ratio_M30=[1,1.3)` | 0.0199 |
| 12 | `M30_ema_stack=up` | 0.0185 |
| 13 | `vix_chg1d=[0,3)` | 0.0183 |
| 14 | `adx_M30=[−∞,18)` | 0.0183 |
| 15 | `macd_atr_M30=[-0.3,0)` | 0.0178 |

---

## XAUUSD · smc · SELL
- Toplam çözülmüş: **263**  ·  Baseline win-rate: **15.2%**

_yüksek başarı pattern bulunamadı (75%+ eşiği)_

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 0.0%** (0 W / 30 L = 30 trade · -15.2pp vs baseline)
   - `adx_M30 ≠ [25,35)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `H1_adx_label ≠ trending`
   - `consec_red_M30 ≠ [0,2)`

**2. Win-rate 0.0%** (0 W / 42 L = 42 trade · -15.2pp vs baseline)
   - `adx_M30 ≠ [25,35)`
   - `us10y_chg1d = [-0.5,0)`

**3. Win-rate 4.5%** (1 W / 21 L = 22 trade · -10.7pp vs baseline)
   - `adx_M30 ≠ [25,35)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `H1_adx_label = trending`
   - `hour_bucket = 20-24`

**4. Win-rate 7.9%** (3 W / 35 L = 38 trade · -7.3pp vs baseline)
   - `adx_M30 ≠ [25,35)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `H1_adx_label ≠ trending`
   - `consec_red_M30 = [0,2)`

**5. Win-rate 22.5%** (18 W / 62 L = 80 trade · 7.3pp vs baseline)
   - `adx_M30 ≠ [25,35)`
   - `us10y_chg1d ≠ [-0.5,0)`
   - `H1_adx_label = trending`
   - `hour_bucket ≠ 20-24`

**6. Win-rate 23.3%** (7 W / 23 L = 30 trade · 8.1pp vs baseline)
   - `adx_M30 = [25,35)`
   - `session ≠ asia`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `adx_M30=[25,35)` | 0.0477 |
| 2 | `dow=Thu` | 0.0390 |
| 3 | `macro_alignment=strong_against` | 0.0387 |
| 4 | `hour_bucket=20-24` | 0.0365 |
| 5 | `vix_chg1d=[−∞,-3)` | 0.0350 |
| 6 | `M30_ema_stack=down` | 0.0296 |
| 7 | `mtf_trend=all_down` | 0.0277 |
| 8 | `M30_adx_label=trending` | 0.0251 |
| 9 | `consec_red_M30=[0,2)` | 0.0231 |
| 10 | `consec_green_M30=[2,4)` | 0.0229 |
| 11 | `us10y_chg1d=[−∞,-0.5)` | 0.0216 |
| 12 | `session=asia` | 0.0201 |
| 13 | `adx_M30=[35,+∞)` | 0.0197 |
| 14 | `macro_alignment=weak_pro` | 0.0191 |
| 15 | `adx_M30=[−∞,18)` | 0.0190 |

---

## XAUUSD · smc_inv · BUY
- Toplam çözülmüş: **135**  ·  Baseline win-rate: **54.1%**

### 🟢 Yüksek Başarı Pattern'leri
> Bu kurulumlar çıktığında modeller tutturuyor — confidence boost adayı.

**1. Win-rate 100.0%** (23 W / 0 L = 23 trade · +45.9pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0,0.5)`
   - `us10y_chg1d ≠ [0.5,+∞)`

**2. Win-rate 77.3%** (17 W / 5 L = 22 trade · +23.2pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d = [0,0.5)`
   - `us10y_chg1d = [0.5,+∞)`

### 🔴 Kaçınılacak Pattern'ler
> Bu kombinasyonlar geliyorsa modeli HOLD'a çek veya filter rule olarak ekle.

**1. Win-rate 21.1%** (8 W / 30 L = 38 trade · -33.0pp vs baseline)
   - `dow = Tue`

**2. Win-rate 32.0%** (8 W / 17 L = 25 trade · -22.1pp vs baseline)
   - `dow ≠ Tue`
   - `dxy_chg1d ≠ [0,0.5)`
   - `macd_atr_M30 = [0,0.3)`

### 📊 En Tahminlikli 15 Özellik (Random Forest)
| Sıra | Özellik | Önem |
|---|---|---|
| 1 | `dow=Tue` | 0.0801 |
| 2 | `dxy_chg1d=[0,0.5)` | 0.0705 |
| 3 | `dist_high_M30=[1.5,+∞)` | 0.0682 |
| 4 | `ml_confidence_bucket=[70,80)` | 0.0411 |
| 5 | `dxy_chg1d=[-0.5,0)` | 0.0385 |
| 6 | `adx_M30=[35,+∞)` | 0.0378 |
| 7 | `atr_ratio_M30=[1,1.3)` | 0.0335 |
| 8 | `dist_high_M30=[0.7,1.5)` | 0.0309 |
| 9 | `mtf_trend=mixed` | 0.0299 |
| 10 | `dist_low_M30=[1.5,+∞)` | 0.0262 |
| 11 | `M30_ema_stack=mixed` | 0.0260 |
| 12 | `macro_alignment=weak_against` | 0.0244 |
| 13 | `vix_chg1d=[3,+∞)` | 0.0229 |
| 14 | `atr_ratio_M30=[0.7,1)` | 0.0222 |
| 15 | `macd_atr_M30=[0,0.3)` | 0.0213 |

---
