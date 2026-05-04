# Price Action Pattern Mining Report
_2026-05-04T13:23:48.546487Z_

Bu rapor **HİÇBİR MODELE BAKMADAN** üretilmiştir — yalnızca ham OHLCV.
Üç bağımsız layer:
1. **SMC Structure**: swing pivots, FVG, CHoCH, BOS, Order Blocks
2. **Trend Ladders**: ritmik kademeli hareketler + öncesi/sonrası analiz
3. **Generic Events**: candle patterns, breakouts, S/R touches

---

## XAUUSD · 5m
- Candles: **7941**  ·  Swing pivots: 1262  ·  FVG: 1787
- CHoCH/BOS events: 883  ·  Order Blocks: 1353
- Trend Ladders detected: 39  ·  Candle patterns: 1962  ·  Breakouts: 664

### S/R Cluster Seviyeleri (top 8)
- 4744.2551 (touches: **1256**, strong)
- 4531.1499 (touches: **2**, weak)
- 4907.55 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (39 ladder)
- Continued: 15  ·  Reversed: 19  ·  Baseline continuation: **38.5%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **72.7%** (8/11)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (3/15)
   - `before_rsi_avg_bucket = (50.0, 70.0]`

### 📊 XAUUSD/5m · ALL EVENTS
- Events: 5719  ·  Baseline continuation: **42.4%**

  - 🟢 **100.0%** (75/75)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **100.0%** (28/28)
      - `type = bearish_OB`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **100.0%** (102/102)
      - `type = bearish_OB`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
  - 🟢 **98.5%** (66/67)
      - `type = bearish_OB`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🟢 **95.6%** (131/137)
      - `type = bearish_OB`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Wed`
  - 🔴 **21.0%** (520/2481)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `type ≠ CHoCH_bearish`

### 📊 XAUUSD/5m · BOS_bearish
- Events: 191  ·  Baseline continuation: **19.4%**

  - 🔴 **21.1%** (4/19)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Mon`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **16.7%** (4/24)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **13.0%** (3/23)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **5.3%** (1/19)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 XAUUSD/5m · BOS_bullish
- Events: 132  ·  Baseline continuation: **15.2%**

  - 🔴 **26.7%** (4/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **25.0%** (3/12)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **7.7%** (1/13)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **6.2%** (1/16)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`
      - `dow = Mon`

### 📊 XAUUSD/5m · CHoCH_bearish
- Events: 264  ·  Baseline continuation: **57.6%**

  - 🟢 **93.5%** (87/93)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
  - 🟢 **80.0%** (12/15)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🟢 **76.9%** (10/13)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (8/32)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/24)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · CHoCH_bullish
- Events: 255  ·  Baseline continuation: **45.5%**

  - 🟢 **100.0%** (37/37)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **81.8%** (9/11)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🟢 **81.0%** (34/42)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **28.2%** (11/39)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **15.6%** (7/45)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Fri`
  - 🔴 **0.0%** (0/22)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 XAUUSD/5m · bearish
- Events: 869  ·  Baseline continuation: **24.1%**

  - 🔴 **28.1%** (16/57)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Thu`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **15.4%** (2/13)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **5.4%** (13/239)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **0.0%** (0/221)
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · bearish_OB
- Events: 805  ·  Baseline continuation: **85.0%**

  - 🟢 **100.0%** (28/28)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **100.0%** (40/40)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
  - 🟢 **100.0%** (62/62)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `dow = Tue`
  - 🟢 **100.0%** (41/41)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **97.8%** (89/91)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 XAUUSD/5m · breakdown
- Events: 317  ·  Baseline continuation: **27.1%**

  - 🟢 **77.3%** (17/22)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **23.8%** (5/21)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **11.5%** (3/26)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (2/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **2.9%** (1/35)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Wed`
  - 🔴 **0.0%** (0/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`

### 📊 XAUUSD/5m · breakout_up
- Events: 338  ·  Baseline continuation: **24.0%**

  - 🟢 **73.3%** (11/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **26.7%** (4/15)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **14.3%** (2/14)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`
  - 🔴 **7.1%** (2/28)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/5m · bullish
- Events: 884  ·  Baseline continuation: **19.7%**

  - 🟢 **81.8%** (9/11)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Mon`
  - 🟢 **75.0%** (9/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **71.4%** (10/14)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
      - `dow = Fri`
  - 🔴 **18.2%** (14/77)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Mon`
      - `dow ≠ Wed`
  - 🔴 **12.0%** (9/75)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Mon`
  - 🔴 **6.2%** (1/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **4.9%** (9/184)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Mon`
  - 🔴 **3.8%** (1/26)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Wed`

### 📊 XAUUSD/5m · bullish_OB
- Events: 548  ·  Baseline continuation: **74.8%**

  - 🟢 **100.0%** (75/75)
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **93.8%** (15/16)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
  - 🟢 **84.6%** (132/156)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.9%** (63/83)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **72.9%** (51/70)
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`

### 📊 XAUUSD/5m · engulfing_bear
- Events: 177  ·  Baseline continuation: **46.9%**

  - 🟢 **90.0%** (9/10)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Wed`
  - 🔴 **25.0%** (6/24)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
  - 🔴 **21.4%** (3/14)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **8.3%** (1/12)
      - `adx_b = (25.0, inf]`
      - `dow = Mon`

### 📊 XAUUSD/5m · engulfing_bull
- Events: 192  ·  Baseline continuation: **30.7%**

  - 🔴 **23.1%** (12/52)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `dow ≠ Fri`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **14.3%** (3/21)
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **0.0%** (0/13)
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`

### 📊 XAUUSD/5m · hammer
- Events: 391  ·  Baseline continuation: **35.8%**

  - 🟢 **100.0%** (30/30)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **29.4%** (5/17)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **26.9%** (7/26)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **8.3%** (2/24)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **8.0%** (2/25)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
  - 🔴 **1.6%** (1/62)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`

### 📊 XAUUSD/5m · shooting_star
- Events: 356  ·  Baseline continuation: **48.9%**

  - 🟢 **100.0%** (37/37)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **83.1%** (54/65)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **22.2%** (6/27)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **15.8%** (6/38)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **0.0%** (0/40)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`

---

## XAUUSD · 30m
- Candles: **1747**  ·  Swing pivots: 226  ·  FVG: 360
- CHoCH/BOS events: 160  ·  Order Blocks: 278
- Trend Ladders detected: 103  ·  Candle patterns: 477  ·  Breakouts: 171

### S/R Cluster Seviyeleri (top 8)
- 4741.4755 (touches: **110**, strong)
- 4547.9411 (touches: **27**, strong)
- 5139.0323 (touches: **13**, strong)
- 4613.19 (touches: **12**, strong)
- 5023.6 (touches: **12**, strong)
- 4482.4825 (touches: **8**, strong)
- 5186.3725 (touches: **8**, strong)
- 4973.496 (touches: **5**, strong)

### 🪜 Trend Ladder Analizi (103 ladder)
- Continued: 43  ·  Reversed: 44  ·  Baseline continuation: **41.7%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **25.0%** (4/16)
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`
- **18.8%** (3/16)
   - `start_dist_ema50_atr_bucket ≠ (0.0, 1.0]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`

### 📊 XAUUSD/30m · ALL EVENTS
- Events: 1240  ·  Baseline continuation: **48.6%**

  - 🟢 **91.5%** (43/47)
      - `type = bearish_OB`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **81.2%** (39/48)
      - `type = bearish_OB`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
  - 🟢 **77.2%** (61/79)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
  - 🔴 **27.7%** (44/159)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `dow = Mon`
      - `type ≠ bullish`
  - 🔴 **27.4%** (20/73)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `dow ≠ Mon`
      - `rsi_b = (70.0, inf]`

### 📊 XAUUSD/30m · BOS_bearish
- Events: 33  ·  Baseline continuation: **30.3%**

  - 🔴 **16.7%** (2/12)
      - `dow = Thu`

### 📊 XAUUSD/30m · CHoCH_bearish
- Events: 49  ·  Baseline continuation: **51.0%**

  - 🟢 **90.9%** (10/11)
      - `dow = Wed`
  - 🟢 **71.4%** (10/14)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
  - 🔴 **23.1%** (3/13)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Wed`
      - `dow = Tue`

### 📊 XAUUSD/30m · CHoCH_bullish
- Events: 50  ·  Baseline continuation: **48.0%**

  - 🟢 **73.3%** (11/15)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/30m · bearish
- Events: 178  ·  Baseline continuation: **48.3%**

  - 🟢 **84.2%** (16/19)
      - `dow ≠ Mon`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **72.2%** (13/18)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
  - 🔴 **27.8%** (5/18)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Thu`
  - 🔴 **20.0%** (2/10)
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **15.8%** (3/19)
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (-inf, 30.0]`

### 📊 XAUUSD/30m · bearish_OB
- Events: 152  ·  Baseline continuation: **76.3%**

  - 🟢 **100.0%** (10/10)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **91.7%** (11/12)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **91.2%** (31/34)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **76.9%** (30/39)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🟢 **76.9%** (10/13)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 XAUUSD/30m · breakdown
- Events: 89  ·  Baseline continuation: **49.4%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
  - 🔴 **20.0%** (3/15)
      - `dow = Mon`

### 📊 XAUUSD/30m · breakout_up
- Events: 82  ·  Baseline continuation: **37.8%**

  - 🟢 **72.7%** (8/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/12)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 XAUUSD/30m · bullish
- Events: 178  ·  Baseline continuation: **38.2%**

  - 🟢 **78.6%** (11/14)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
  - 🔴 **23.5%** (4/17)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
      - `rsi_b = (70.0, inf]`
  - 🔴 **18.2%** (2/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **11.1%** (2/18)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/30m · bullish_OB
- Events: 124  ·  Baseline continuation: **65.3%**

  - 🟢 **94.4%** (17/18)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **80.0%** (32/40)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **73.3%** (11/15)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 XAUUSD/30m · engulfing_bear
- Events: 60  ·  Baseline continuation: **36.7%**

  - 🔴 **16.7%** (2/12)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`

### 📊 XAUUSD/30m · engulfing_bull
- Events: 70  ·  Baseline continuation: **37.1%**

  - 🟢 **83.3%** (10/12)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **5.9%** (1/17)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/30m · hammer
- Events: 72  ·  Baseline continuation: **31.9%**

  - 🔴 **29.4%** (5/17)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **22.2%** (4/18)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **7.1%** (1/14)
      - `dow = Wed`

### 📊 XAUUSD/30m · shooting_star
- Events: 75  ·  Baseline continuation: **52.0%**

  - 🟢 **81.8%** (9/11)
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **81.8%** (9/11)
      - `dow ≠ Mon`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **20.0%** (3/15)
      - `dow = Mon`

---

## XAUUSD · 1h
- Candles: **4900**  ·  Swing pivots: 2562  ·  FVG: 300
- CHoCH/BOS events: 1344  ·  Order Blocks: 570
- Trend Ladders detected: 34  ·  Candle patterns: 1425  ·  Breakouts: 231

### S/R Cluster Seviyeleri (top 8)
- 4755.6196 (touches: **2562**, strong)

### 🪜 Trend Ladder Analizi (34 ladder)
- Continued: 8  ·  Reversed: 17  ·  Baseline continuation: **23.5%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **12.5%** (2/16)
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`

### 📊 XAUUSD/1h · ALL EVENTS
- Events: 2679  ·  Baseline continuation: **42.2%**

  - 🟢 **99.0%** (195/197)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **96.3%** (103/107)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **91.9%** (113/123)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **89.0%** (113/127)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = CHoCH_bearish`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **84.0%** (21/25)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **17.2%** (10/58)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = CHoCH_bearish`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **17.0%** (215/1264)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ CHoCH_bearish`
      - `type ≠ BOS_bearish`

### 📊 XAUUSD/1h · BOS_bearish
- Events: 660  ·  Baseline continuation: **41.7%**

  - 🟢 **100.0%** (17/17)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **100.0%** (29/29)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **100.0%** (14/14)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🟢 **95.1%** (39/41)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
  - 🟢 **92.9%** (13/14)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **29.6%** (16/54)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **17.5%** (7/40)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **16.7%** (5/30)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **12.2%** (15/123)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **3.4%** (4/117)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/1h · CHoCH_bearish
- Events: 185  ·  Baseline continuation: **66.5%**

  - 🟢 **100.0%** (12/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **92.5%** (62/67)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **91.7%** (11/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **85.0%** (17/20)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **7.1%** (1/14)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`

### 📊 XAUUSD/1h · CHoCH_bullish
- Events: 184  ·  Baseline continuation: **37.5%**

  - 🟢 **93.2%** (41/44)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **80.0%** (8/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **70.0%** (7/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **15.4%** (2/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Fri`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/49)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `dow ≠ Wed`
  - 🔴 **0.0%** (0/18)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `dow = Wed`

### 📊 XAUUSD/1h · bearish
- Events: 125  ·  Baseline continuation: **4.8%**

  - 🔴 **21.4%** (3/14)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **5.6%** (1/18)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/55)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Thu`

### 📊 XAUUSD/1h · bearish_OB
- Events: 413  ·  Baseline continuation: **91.0%**

  - 🟢 **100.0%** (24/24)
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🟢 **100.0%** (109/109)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **97.5%** (39/40)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **92.6%** (112/121)
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **92.3%** (12/13)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 XAUUSD/1h · breakdown
- Events: 103  ·  Baseline continuation: **14.6%**

  - 🔴 **14.3%** (2/14)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **13.3%** (2/15)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/48)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 XAUUSD/1h · breakout_up
- Events: 119  ·  Baseline continuation: **2.5%**

  - 🔴 **11.1%** (2/18)
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **6.2%** (1/16)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/85)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/1h · bullish
- Events: 152  ·  Baseline continuation: **6.6%**

  - 🔴 **25.0%** (5/20)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Fri`
  - 🔴 **10.7%** (3/28)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
  - 🔴 **7.1%** (1/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow = Wed`
  - 🔴 **4.2%** (1/24)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **0.0%** (0/52)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow ≠ Thu`

### 📊 XAUUSD/1h · bullish_OB
- Events: 157  ·  Baseline continuation: **90.4%**

  - 🟢 **100.0%** (29/29)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
  - 🟢 **100.0%** (10/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
  - 🟢 **97.0%** (32/33)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🟢 **94.3%** (33/35)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `dow = Wed`

### 📊 XAUUSD/1h · engulfing_bear
- Events: 95  ·  Baseline continuation: **23.2%**

  - 🟢 **81.8%** (9/11)
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **22.6%** (7/31)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow ≠ Tue`
  - 🔴 **7.1%** (1/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **0.0%** (0/28)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`

### 📊 XAUUSD/1h · engulfing_bull
- Events: 106  ·  Baseline continuation: **12.3%**

  - 🔴 **20.0%** (5/25)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
  - 🔴 **5.6%** (1/18)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`
  - 🔴 **4.2%** (1/24)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/22)
      - `dow = Wed`

### 📊 XAUUSD/1h · hammer
- Events: 255  ·  Baseline continuation: **8.2%**

  - 🔴 **30.0%** (3/10)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **23.5%** (4/17)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **5.6%** (1/18)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **1.1%** (1/92)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 XAUUSD/1h · shooting_star
- Events: 111  ·  Baseline continuation: **50.5%**

  - 🟢 **100.0%** (16/16)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **91.7%** (11/12)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **28.0%** (7/25)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Mon`

---
