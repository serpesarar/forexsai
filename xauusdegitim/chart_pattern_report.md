# Price Action Pattern Mining Report
_2026-05-04T18:11:07.022195Z_

Bu rapor **HİÇBİR MODELE BAKMADAN** üretilmiştir — yalnızca ham OHLCV.
Üç bağımsız layer:
1. **SMC Structure**: swing pivots, FVG, CHoCH, BOS, Order Blocks
2. **Trend Ladders**: ritmik kademeli hareketler + öncesi/sonrası analiz
3. **Generic Events**: candle patterns, breakouts, S/R touches

---

## XAUUSD · 5m
- Candles: **8111**  ·  Swing pivots: 1300  ·  FVG: 1799
- CHoCH/BOS events: 905  ·  Order Blocks: 1370
- Trend Ladders detected: 43  ·  Candle patterns: 2000  ·  Breakouts: 677

### S/R Cluster Seviyeleri (top 8)
- 4741.6114 (touches: **1293**, strong)
- 4532.4333 (touches: **3**, moderate)
- 4907.55 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (43 ladder)
- Continued: 15  ·  Reversed: 21  ·  Baseline continuation: **34.9%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **30.0%** (3/10)
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`
- **27.3%** (3/11)
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`
   - `before_rsi_avg_bucket = (50.0, 70.0]`
- **10.0%** (1/10)
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`

### 📊 XAUUSD/5m · ALL EVENTS
- Events: 5809  ·  Baseline continuation: **42.4%**

  - 🟢 **100.0%** (75/75)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **100.0%** (102/102)
      - `type = bearish_OB`
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
  - 🟢 **98.5%** (66/67)
      - `type = bearish_OB`
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🟢 **85.8%** (392/457)
      - `type = bearish_OB`
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **80.0%** (204/255)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **21.0%** (526/2499)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `type ≠ CHoCH_bearish`

### 📊 XAUUSD/5m · BOS_bearish
- Events: 200  ·  Baseline continuation: **20.5%**

  - 🔴 **20.0%** (4/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **13.0%** (3/23)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Wed`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`

### 📊 XAUUSD/5m · BOS_bullish
- Events: 132  ·  Baseline continuation: **14.4%**

  - 🔴 **25.0%** (4/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **16.7%** (2/12)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **8.3%** (1/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **6.2%** (1/16)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`
      - `dow = Mon`

### 📊 XAUUSD/5m · CHoCH_bearish
- Events: 269  ·  Baseline continuation: **56.9%**

  - 🟢 **92.6%** (87/94)
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
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
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
- Events: 262  ·  Baseline continuation: **45.8%**

  - 🟢 **100.0%** (37/37)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **90.5%** (19/21)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
  - 🔴 **28.0%** (7/25)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **7.5%** (3/40)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **0.0%** (0/26)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/5m · bearish
- Events: 879  ·  Baseline continuation: **24.5%**

  - 🟢 **72.4%** (42/58)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
      - `dow = Tue`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **27.3%** (3/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
      - `dow = Tue`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **21.7%** (5/23)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **15.4%** (2/13)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **5.4%** (13/239)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **0.0%** (0/218)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 XAUUSD/5m · bearish_OB
- Events: 813  ·  Baseline continuation: **85.0%**

  - 🟢 **100.0%** (28/28)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **100.0%** (102/102)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
  - 🟢 **100.0%** (41/41)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **97.8%** (89/91)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **96.2%** (25/26)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/5m · breakdown
- Events: 326  ·  Baseline continuation: **27.0%**

  - 🟢 **77.3%** (17/22)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **30.0%** (18/60)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow = Tue`
      - `adx_b = (-inf, 18.0]`
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

### 📊 XAUUSD/5m · breakout_up
- Events: 342  ·  Baseline continuation: **24.3%**

  - 🟢 **73.3%** (11/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **30.0%** (3/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`
  - 🔴 **30.0%** (3/10)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **14.3%** (2/14)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`
  - 🔴 **11.9%** (7/59)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 XAUUSD/5m · bullish
- Events: 887  ·  Baseline continuation: **19.7%**

  - 🔴 **16.7%** (3/18)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Thu`
  - 🔴 **16.0%** (4/25)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Fri`
  - 🔴 **13.2%** (10/76)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Fri`
  - 🔴 **6.2%** (1/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 XAUUSD/5m · bullish_OB
- Events: 556  ·  Baseline continuation: **74.5%**

  - 🟢 **100.0%** (75/75)
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **94.1%** (16/17)
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
- Events: 184  ·  Baseline continuation: **47.3%**

  - 🟢 **90.0%** (9/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Wed`
  - 🔴 **25.0%** (6/24)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
  - 🔴 **7.1%** (1/14)
      - `adx_b = (25.0, inf]`
      - `dow = Mon`

### 📊 XAUUSD/5m · engulfing_bull
- Events: 195  ·  Baseline continuation: **30.3%**

  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **23.5%** (4/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **20.6%** (7/34)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **17.9%** (5/28)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **8.7%** (2/23)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/5m · hammer
- Events: 398  ·  Baseline continuation: **35.4%**

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
  - 🔴 **1.6%** (1/63)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`

### 📊 XAUUSD/5m · shooting_star
- Events: 366  ·  Baseline continuation: **48.4%**

  - 🟢 **100.0%** (37/37)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **83.3%** (50/60)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **70.6%** (12/17)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **23.1%** (6/26)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **15.8%** (6/38)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **0.0%** (0/29)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
  - 🔴 **0.0%** (0/11)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Thu`

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
- Candles: **4929**  ·  Swing pivots: 2566  ·  FVG: 300
- CHoCH/BOS events: 1346  ·  Order Blocks: 572
- Trend Ladders detected: 33  ·  Candle patterns: 1429  ·  Breakouts: 228

### S/R Cluster Seviyeleri (top 8)
- 4755.3371 (touches: **2566**, strong)

### 🪜 Trend Ladder Analizi (33 ladder)
- Continued: 6  ·  Reversed: 17  ·  Baseline continuation: **18.2%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **5.6%** (1/18)
   - `bb_squeeze_str ≠ False`

### 📊 XAUUSD/1h · ALL EVENTS
- Events: 2685  ·  Baseline continuation: **42.1%**

  - 🟢 **99.0%** (194/196)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **95.5%** (106/111)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
  - 🟢 **91.9%** (113/123)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **88.4%** (114/129)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = CHoCH_bearish`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **80.0%** (24/30)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **16.6%** (210/1265)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ CHoCH_bearish`
      - `type ≠ BOS_bearish`
  - 🔴 **16.1%** (9/56)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = CHoCH_bearish`
      - `rsi_b = (30.0, 50.0]`

### 📊 XAUUSD/1h · BOS_bearish
- Events: 663  ·  Baseline continuation: **42.1%**

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
  - 🟢 **90.6%** (29/32)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **29.4%** (15/51)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **18.2%** (8/44)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **16.7%** (5/30)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **13.9%** (17/122)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **4.2%** (5/119)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/1h · CHoCH_bearish
- Events: 185  ·  Baseline continuation: **66.5%**

  - 🟢 **100.0%** (13/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **100.0%** (13/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
  - 🟢 **90.9%** (10/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🟢 **88.2%** (67/76)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **19.0%** (4/21)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **7.1%** (1/14)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`

### 📊 XAUUSD/1h · CHoCH_bullish
- Events: 184  ·  Baseline continuation: **37.0%**

  - 🟢 **93.0%** (40/43)
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
  - 🔴 **14.3%** (2/14)
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
  - 🔴 **0.0%** (0/67)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`

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

  - 🟢 **100.0%** (23/23)
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
- Events: 101  ·  Baseline continuation: **10.9%**

  - 🔴 **11.1%** (2/18)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **7.7%** (1/13)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **5.9%** (1/17)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/40)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/1h · breakout_up
- Events: 118  ·  Baseline continuation: **2.5%**

  - 🔴 **11.1%** (2/18)
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **6.2%** (1/16)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/84)
      - `atr_pct_b ≠ (0.15, 0.4]`
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
- Events: 159  ·  Baseline continuation: **89.3%**

  - 🟢 **100.0%** (17/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow = Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **100.0%** (10/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **95.9%** (70/73)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **86.7%** (13/15)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
  - 🟢 **81.8%** (9/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.15, 0.4]`

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
- Events: 109  ·  Baseline continuation: **11.9%**

  - 🔴 **17.9%** (5/28)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **6.2%** (1/16)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/14)
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/22)
      - `dow = Wed`

### 📊 XAUUSD/1h · hammer
- Events: 256  ·  Baseline continuation: **8.2%**

  - 🔴 **30.0%** (3/10)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **23.5%** (4/17)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **5.3%** (1/19)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **1.1%** (1/91)
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
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`

---

## NDX.INDX · 5m
- Candles: **8946**  ·  Swing pivots: 1103  ·  FVG: 2079
- CHoCH/BOS events: 767  ·  Order Blocks: 1435
- Trend Ladders detected: 119  ·  Candle patterns: 2696  ·  Breakouts: 1067

### S/R Cluster Seviyeleri (top 8)
- 24095.5769 (touches: **343**, strong)
- 24885.6814 (touches: **117**, strong)
- 27243.2941 (touches: **85**, strong)
- 25091.0403 (touches: **54**, strong)
- 27045.9077 (touches: **26**, strong)
- 27783.0769 (touches: **26**, strong)
- 26548.316 (touches: **25**, strong)
- 23638.8169 (touches: **23**, strong)

### 🪜 Trend Ladder Analizi (119 ladder)
- Continued: 45  ·  Reversed: 54  ·  Baseline continuation: **37.8%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (6/36)
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
   - `start_dist_ema50_atr_bucket ≠ (-1.0, 0.0]`
   - `before_volz_avg_bucket ≠ (-inf, -0.5]`

### 📊 NDX.INDX/5m · ALL EVENTS
- Events: 6923  ·  Baseline continuation: **46.4%**

  - 🟢 **96.9%** (31/32)
      - `type = bullish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Tue`
  - 🟢 **92.0%** (23/25)
      - `type = bullish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Tue`
      - `dow = Thu`
  - 🟢 **76.7%** (69/90)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **75.3%** (219/291)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Wed`
  - 🟢 **71.2%** (52/73)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **14.6%** (18/123)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `dow ≠ Fri`

### 📊 NDX.INDX/5m · BOS_bearish
- Events: 163  ·  Baseline continuation: **20.2%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
  - 🔴 **20.0%** (3/15)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **18.2%** (2/11)
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **6.2%** (2/32)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
  - 🔴 **0.0%** (0/37)
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`

### 📊 NDX.INDX/5m · BOS_bullish
- Events: 175  ·  Baseline continuation: **27.4%**

  - 🔴 **27.3%** (3/11)
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **23.5%** (4/17)
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
  - 🔴 **20.0%** (2/10)
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`

### 📊 NDX.INDX/5m · CHoCH_bearish
- Events: 209  ·  Baseline continuation: **39.2%**

  - 🟢 **73.7%** (28/38)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **23.1%** (3/13)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **17.1%** (7/41)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **0.0%** (0/16)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/5m · CHoCH_bullish
- Events: 207  ·  Baseline continuation: **41.1%**

  - 🟢 **91.7%** (11/12)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`
  - 🔴 **23.5%** (8/34)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **5.0%** (1/20)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`

### 📊 NDX.INDX/5m · bearish
- Events: 979  ·  Baseline continuation: **39.7%**

  - 🟢 **94.7%** (18/19)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **75.0%** (15/20)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **25.0%** (5/20)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **14.7%** (14/95)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.7%** (3/31)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Mon`
      - `adx_b = (18.0, 25.0]`

### 📊 NDX.INDX/5m · bearish_OB
- Events: 697  ·  Baseline continuation: **64.1%**

  - 🟢 **100.0%** (13/13)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **91.7%** (11/12)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **80.0%** (12/15)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Wed`
  - 🟢 **78.4%** (40/51)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **76.9%** (70/91)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow = Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
  - 🔴 **20.0%** (3/15)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Wed`

### 📊 NDX.INDX/5m · breakdown
- Events: 481  ·  Baseline continuation: **41.4%**

  - 🟢 **92.3%** (12/13)
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **70.8%** (17/24)
      - `dow ≠ Fri`
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Fri`
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`
  - 🔴 **20.0%** (3/15)
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🔴 **9.7%** (3/31)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`

### 📊 NDX.INDX/5m · breakout_up
- Events: 562  ·  Baseline continuation: **45.0%**

  - 🟢 **75.0%** (9/12)
      - `dow = Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **29.6%** (8/27)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **27.8%** (5/18)
      - `dow ≠ Thu`
      - `adx_b = (18.0, 25.0]`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **12.0%** (3/25)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`

### 📊 NDX.INDX/5m · bullish
- Events: 1071  ·  Baseline continuation: **45.5%**

  - 🟢 **84.6%** (22/26)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **76.9%** (10/13)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (-inf, 0.05]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
      - `atr_pct_b = (-inf, 0.05]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/5m · bullish_OB
- Events: 738  ·  Baseline continuation: **70.7%**

  - 🟢 **100.0%** (27/27)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **90.2%** (37/41)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **84.4%** (27/32)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
  - 🟢 **78.6%** (176/224)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
  - 🟢 **71.1%** (32/45)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 NDX.INDX/5m · engulfing_bear
- Events: 412  ·  Baseline continuation: **36.9%**

  - 🔴 **29.2%** (7/24)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **19.2%** (5/26)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **0.0%** (0/12)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Thu`
  - 🔴 **0.0%** (0/14)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`

### 📊 NDX.INDX/5m · engulfing_bull
- Events: 456  ·  Baseline continuation: **44.7%**

  - 🟢 **80.0%** (8/10)
      - `dow ≠ Thu`
      - `dow = Fri`
      - `atr_pct_b = (-inf, 0.05]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **23.1%** (9/39)
      - `dow ≠ Thu`
      - `dow = Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`
  - 🔴 **15.0%** (3/20)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **14.3%** (4/28)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/5m · hammer
- Events: 367  ·  Baseline continuation: **43.9%**

  - 🟢 **75.0%** (24/32)
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Mon`
  - 🔴 **21.4%** (3/14)
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (-inf, 0.05]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **18.8%** (3/16)
      - `dow = Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **10.0%** (1/10)
      - `dow = Fri`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/5m · shooting_star
- Events: 406  ·  Baseline continuation: **36.2%**

  - 🔴 **24.4%** (10/41)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
  - 🔴 **23.8%** (5/21)
      - `adx_b = (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
  - 🔴 **23.3%** (10/43)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Wed`
  - 🔴 **7.7%** (1/13)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (-inf, 30.0]`

---

## NDX.INDX · 30m
- Candles: **1343**  ·  Swing pivots: 170  ·  FVG: 329
- CHoCH/BOS events: 119  ·  Order Blocks: 244
- Trend Ladders detected: 77  ·  Candle patterns: 397  ·  Breakouts: 176

### S/R Cluster Seviyeleri (top 8)
- 24042.7824 (touches: **34**, strong)
- 26685.4867 (touches: **15**, strong)
- 24271.1143 (touches: **14**, strong)
- 27014.2636 (touches: **11**, strong)
- 25067.6286 (touches: **7**, strong)
- 27182.6 (touches: **7**, strong)
- 23795.7833 (touches: **6**, strong)
- 24776.9333 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (77 ladder)
- Continued: 29  ·  Reversed: 37  ·  Baseline continuation: **37.7%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **18.2%** (2/11)
   - `direction = up`
   - `before_adx_avg_bucket = (25.0, inf]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
- **15.0%** (3/20)
   - `direction ≠ up`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`

### 📊 NDX.INDX/30m · ALL EVENTS
- Events: 1109  ·  Baseline continuation: **47.0%**

  - 🟢 **95.5%** (21/22)
      - `type = bullish_OB`
      - `dow ≠ Thu`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **85.7%** (24/28)
      - `type = bullish_OB`
      - `dow ≠ Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🟢 **78.6%** (33/42)
      - `type ≠ bullish_OB`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **21.7%** (5/23)
      - `type ≠ bullish_OB`
      - `rsi_b = (70.0, inf]`
      - `dow = Thu`

### 📊 NDX.INDX/30m · BOS_bullish
- Events: 30  ·  Baseline continuation: **20.0%**

  - 🔴 **11.1%** (2/18)
      - `dow ≠ Wed`

### 📊 NDX.INDX/30m · CHoCH_bearish
- Events: 34  ·  Baseline continuation: **41.2%**

  - 🔴 **23.1%** (3/13)
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 NDX.INDX/30m · CHoCH_bullish
- Events: 33  ·  Baseline continuation: **57.6%**

  - 🟢 **78.6%** (11/14)
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/30m · bearish
- Events: 132  ·  Baseline continuation: **37.1%**

  - 🟢 **100.0%** (15/15)
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **81.8%** (9/11)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **28.0%** (7/25)
      - `dow ≠ Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
  - 🔴 **7.5%** (3/40)
      - `dow ≠ Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`

### 📊 NDX.INDX/30m · bearish_OB
- Events: 119  ·  Baseline continuation: **61.3%**

  - 🟢 **85.7%** (18/21)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **72.7%** (8/11)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **71.1%** (27/38)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **20.0%** (3/15)
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/30m · breakdown
- Events: 58  ·  Baseline continuation: **37.9%**

  - 🟢 **70.0%** (7/10)
      - `dow ≠ Mon`
      - `dow = Fri`
  - 🔴 **23.1%** (3/13)
      - `dow ≠ Mon`
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **0.0%** (0/10)
      - `dow = Mon`

### 📊 NDX.INDX/30m · breakout_up
- Events: 115  ·  Baseline continuation: **53.0%**

  - 🟢 **100.0%** (18/18)
      - `rsi_b = (70.0, inf]`
      - `dow = Tue`
  - 🟢 **81.8%** (9/11)
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **26.7%** (4/15)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **11.1%** (2/18)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 NDX.INDX/30m · bullish
- Events: 195  ·  Baseline continuation: **50.8%**

  - 🟢 **87.9%** (29/33)
      - `dow ≠ Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
  - 🟢 **80.0%** (8/10)
      - `dow ≠ Thu`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **22.7%** (5/22)
      - `dow ≠ Thu`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **16.7%** (2/12)
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **10.0%** (1/10)
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`

### 📊 NDX.INDX/30m · bullish_OB
- Events: 125  ·  Baseline continuation: **72.0%**

  - 🟢 **100.0%** (14/14)
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **90.9%** (10/11)
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
  - 🟢 **90.0%** (18/20)
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **76.9%** (10/13)
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **75.0%** (12/16)
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🔴 **22.2%** (4/18)
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Wed`

### 📊 NDX.INDX/30m · engulfing_bear
- Events: 67  ·  Baseline continuation: **35.8%**

  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **14.3%** (2/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/30m · engulfing_bull
- Events: 63  ·  Baseline continuation: **36.5%**

  - 🔴 **18.2%** (2/11)
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **0.0%** (0/17)
      - `dow = Fri`

### 📊 NDX.INDX/30m · hammer
- Events: 62  ·  Baseline continuation: **37.1%**

  - 🟢 **90.9%** (10/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
  - 🔴 **8.3%** (1/12)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
  - 🔴 **0.0%** (0/11)
      - `atr_pct_b = (0.05, 0.15]`

### 📊 NDX.INDX/30m · shooting_star
- Events: 56  ·  Baseline continuation: **28.6%**

  - 🔴 **10.5%** (2/19)
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`

---

## NDX.INDX · 1h
- Candles: **4918**  ·  Swing pivots: 844  ·  FVG: 758
- CHoCH/BOS events: 584  ·  Order Blocks: 900
- Trend Ladders detected: 180  ·  Candle patterns: 1316  ·  Breakouts: 505

### S/R Cluster Seviyeleri (top 8)
- 25227.4847 (touches: **791**, strong)
- 23797.2805 (touches: **12**, strong)
- 27003.2429 (touches: **7**, strong)
- 26716.4333 (touches: **6**, strong)
- 27381.5667 (touches: **6**, strong)
- 26575.7 (touches: **3**, moderate)
- 27186.3 (touches: **3**, moderate)
- 23561.5 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (180 ladder)
- Continued: 56  ·  Reversed: 94  ·  Baseline continuation: **31.1%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **23.5%** (4/17)
   - `bb_squeeze_str ≠ False`
   - `before_adx_avg_bucket = (-inf, 18.0]`
- **20.0%** (8/40)
   - `bb_squeeze_str = False`
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
- **7.1%** (1/14)
   - `bb_squeeze_str ≠ False`
   - `before_adx_avg_bucket ≠ (-inf, 18.0]`

### 📊 NDX.INDX/1h · ALL EVENTS
- Events: 3452  ·  Baseline continuation: **43.3%**

  - 🟢 **88.2%** (15/17)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **85.7%** (156/182)
      - `type = bearish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **73.2%** (169/231)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **70.0%** (35/50)
      - `type = bearish_OB`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
  - 🔴 **16.7%** (15/90)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **14.3%** (3/21)
      - `type = bearish_OB`
      - `vol_z_b = (0.5, inf]`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **12.0%** (14/117)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 NDX.INDX/1h · BOS_bearish
- Events: 161  ·  Baseline continuation: **17.4%**

  - 🟢 **70.0%** (7/10)
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **11.5%** (3/26)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Tue`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Tue`
  - 🔴 **7.1%** (1/14)
      - `dow = Wed`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **5.3%** (1/19)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
  - 🔴 **5.0%** (1/20)
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 NDX.INDX/1h · BOS_bullish
- Events: 90  ·  Baseline continuation: **16.7%**

  - 🔴 **21.7%** (5/23)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
  - 🔴 **17.6%** (3/17)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **12.5%** (2/16)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/1h · CHoCH_bearish
- Events: 148  ·  Baseline continuation: **44.6%**

  - 🟢 **81.8%** (9/11)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **75.0%** (12/16)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **71.4%** (10/14)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **26.7%** (4/15)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **16.0%** (4/25)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/1h · CHoCH_bullish
- Events: 148  ·  Baseline continuation: **45.9%**

  - 🟢 **86.7%** (13/15)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
  - 🟢 **73.7%** (14/19)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **26.9%** (7/26)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **15.4%** (4/26)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 NDX.INDX/1h · bearish
- Events: 323  ·  Baseline continuation: **37.2%**

  - 🟢 **80.0%** (8/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **73.9%** (17/23)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **12.5%** (8/64)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
  - 🔴 **9.5%** (2/21)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **8.3%** (1/12)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 NDX.INDX/1h · bearish_OB
- Events: 493  ·  Baseline continuation: **66.5%**

  - 🟢 **100.0%** (53/53)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **85.7%** (12/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🟢 **79.8%** (103/129)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **78.1%** (25/32)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
  - 🟢 **73.3%** (11/15)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b = (0.5, inf]`
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **14.3%** (3/21)
      - `vol_z_b = (0.5, inf]`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 NDX.INDX/1h · breakdown
- Events: 184  ·  Baseline continuation: **22.8%**

  - 🔴 **16.7%** (2/12)
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (3/18)
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **14.0%** (7/50)
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
  - 🔴 **13.3%** (2/15)
      - `dow ≠ Thu`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/27)
      - `dow ≠ Thu`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/1h · breakout_up
- Events: 312  ·  Baseline continuation: **29.2%**

  - 🟢 **78.6%** (11/14)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
      - `rsi_b = (70.0, inf]`
  - 🔴 **29.7%** (19/64)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **28.9%** (11/38)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **25.5%** (13/51)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **6.7%** (1/15)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `dow = Wed`

### 📊 NDX.INDX/1h · bullish
- Events: 420  ·  Baseline continuation: **35.5%**

  - 🟢 **90.0%** (9/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **26.7%** (4/15)
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **25.0%** (4/16)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **23.3%** (7/30)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
      - `dow = Tue`
  - 🔴 **23.3%** (24/103)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 NDX.INDX/1h · bullish_OB
- Events: 407  ·  Baseline continuation: **67.1%**

  - 🟢 **100.0%** (11/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **100.0%** (10/10)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🟢 **88.9%** (16/18)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **80.0%** (24/30)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **76.7%** (23/30)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow = Tue`

### 📊 NDX.INDX/1h · engulfing_bear
- Events: 174  ·  Baseline continuation: **39.1%**

  - 🟢 **81.8%** (9/11)
      - `dow = Thu`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **27.1%** (13/48)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **18.8%** (3/16)
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 NDX.INDX/1h · engulfing_bull
- Events: 187  ·  Baseline continuation: **41.7%**

  - 🟢 **75.0%** (12/16)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🔴 **29.4%** (5/17)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **24.0%** (6/25)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **10.0%** (1/10)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/1h · hammer
- Events: 232  ·  Baseline continuation: **41.8%**

  - 🟢 **81.8%** (9/11)
      - `dow ≠ Thu`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **29.2%** (7/24)
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
  - 🔴 **27.8%** (5/18)
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.8%** (3/19)
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`

### 📊 NDX.INDX/1h · shooting_star
- Events: 173  ·  Baseline continuation: **41.0%**

  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `dow = Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **25.0%** (4/16)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **5.9%** (1/17)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`

---

## GDAXI.INDX · 5m
- Candles: **7905**  ·  Swing pivots: 1022  ·  FVG: 1901
- CHoCH/BOS events: 744  ·  Order Blocks: 1347
- Trend Ladders detected: 96  ·  Candle patterns: 2288  ·  Breakouts: 975

### S/R Cluster Seviyeleri (top 8)
- 24065.4132 (touches: **553**, strong)
- 22834.936 (touches: **267**, strong)
- 23188.4053 (touches: **32**, strong)
- 22376.65 (touches: **24**, strong)
- 23290.5178 (touches: **18**, strong)
- 22261.1364 (touches: **11**, strong)
- 23542.2326 (touches: **11**, strong)
- 22207.1 (touches: **10**, strong)

### 🪜 Trend Ladder Analizi (96 ladder)
- Continued: 41  ·  Reversed: 36  ·  Baseline continuation: **42.7%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **81.8%** (9/11)
   - `before_volz_avg_bucket = (0.5, inf]`
   - `before_rsi_last_bucket = (30.0, 50.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (3/15)
   - `before_volz_avg_bucket ≠ (0.5, inf]`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`

### 📊 GDAXI.INDX/5m · ALL EVENTS
- Events: 6425  ·  Baseline continuation: **46.4%**

  - 🟢 **81.0%** (68/84)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **78.4%** (222/283)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow ≠ Fri`
  - 🟢 **75.8%** (25/33)
      - `type = bearish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **22.1%** (32/145)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **16.4%** (21/128)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 GDAXI.INDX/5m · BOS_bearish
- Events: 163  ·  Baseline continuation: **22.1%**

  - 🔴 **27.3%** (3/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
  - 🔴 **27.3%** (3/11)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **23.1%** (3/13)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **22.0%** (9/41)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Mon`
  - 🔴 **8.3%** (1/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/5m · BOS_bullish
- Events: 145  ·  Baseline continuation: **22.1%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **26.3%** (5/19)
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (3/15)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **16.0%** (8/50)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`

### 📊 GDAXI.INDX/5m · CHoCH_bearish
- Events: 216  ·  Baseline continuation: **47.7%**

  - 🟢 **86.2%** (25/29)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
  - 🔴 **27.5%** (11/40)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
  - 🔴 **25.0%** (3/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **16.7%** (3/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `dow = Mon`

### 📊 GDAXI.INDX/5m · CHoCH_bullish
- Events: 217  ·  Baseline continuation: **42.4%**

  - 🟢 **84.6%** (11/13)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **80.0%** (8/10)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (14/56)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **15.4%** (2/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/5m · bearish
- Events: 927  ·  Baseline continuation: **40.6%**

  - 🟢 **75.0%** (12/16)
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **71.4%** (20/28)
      - `dow ≠ Fri`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **70.0%** (14/20)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **25.7%** (9/35)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **20.0%** (11/55)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`

### 📊 GDAXI.INDX/5m · bearish_OB
- Events: 687  ·  Baseline continuation: **67.8%**

  - 🟢 **90.9%** (20/22)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **80.7%** (46/57)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow = Fri`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **79.7%** (216/271)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow ≠ Fri`
      - `vol_z_b ≠ nan`
  - 🟢 **76.9%** (10/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **76.9%** (10/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **25.0%** (3/12)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 GDAXI.INDX/5m · breakdown
- Events: 501  ·  Baseline continuation: **43.3%**

  - 🔴 **16.7%** (5/30)
      - `vol_z_b ≠ nan`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow = Wed`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b = nan`

### 📊 GDAXI.INDX/5m · breakout_up
- Events: 464  ·  Baseline continuation: **42.9%**

  - 🟢 **90.9%** (10/11)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **75.0%** (12/16)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **28.6%** (4/14)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Tue`
  - 🔴 **22.2%** (6/27)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **15.0%** (3/20)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b = (70.0, inf]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`

### 📊 GDAXI.INDX/5m · bullish
- Events: 966  ·  Baseline continuation: **40.1%**

  - 🟢 **72.9%** (35/48)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **22.4%** (11/49)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **21.6%** (11/51)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **20.0%** (2/10)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **20.0%** (2/10)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **7.1%** (1/14)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 GDAXI.INDX/5m · bullish_OB
- Events: 660  ·  Baseline continuation: **64.4%**

  - 🟢 **100.0%** (11/11)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **92.3%** (24/26)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **82.1%** (23/28)
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Wed`
  - 🟢 **81.8%** (9/11)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **75.0%** (30/40)
      - `dow ≠ Mon`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`

### 📊 GDAXI.INDX/5m · engulfing_bear
- Events: 392  ·  Baseline continuation: **44.9%**

  - 🟢 **70.4%** (38/54)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Mon`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **26.9%** (7/26)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **22.7%** (5/22)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **13.3%** (2/15)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/12)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`

### 📊 GDAXI.INDX/5m · engulfing_bull
- Events: 377  ·  Baseline continuation: **41.9%**

  - 🟢 **78.9%** (15/19)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow = Wed`
  - 🟢 **70.0%** (7/10)
      - `atr_pct_b = (-inf, 0.05]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **28.9%** (13/45)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/5m · hammer
- Events: 376  ·  Baseline continuation: **41.0%**

  - 🟢 **84.6%** (11/13)
      - `atr_pct_b = (-inf, 0.05]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **80.0%** (8/10)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.4%** (25/88)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **16.7%** (5/30)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`

### 📊 GDAXI.INDX/5m · shooting_star
- Events: 334  ·  Baseline continuation: **47.0%**

  - 🟢 **71.0%** (22/31)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Wed`
  - 🔴 **20.0%** (2/10)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **18.8%** (3/16)
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Tue`
      - `atr_pct_b = (-inf, 0.05]`
      - `vol_z_b = (-inf, -0.5]`

---

## GDAXI.INDX · 30m
- Candles: **1256**  ·  Swing pivots: 172  ·  FVG: 289
- CHoCH/BOS events: 121  ·  Order Blocks: 209
- Trend Ladders detected: 77  ·  Candle patterns: 401  ·  Breakouts: 120

### S/R Cluster Seviyeleri (top 8)
- 24093.0059 (touches: **85**, strong)
- 22861.0813 (touches: **16**, strong)
- 22585.9692 (touches: **13**, strong)
- 23387.3429 (touches: **7**, strong)
- 22380.8 (touches: **6**, strong)
- 23003.55 (touches: **6**, strong)
- 23086.3 (touches: **6**, strong)
- 24485.3667 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (77 ladder)
- Continued: 26  ·  Reversed: 42  ·  Baseline continuation: **33.8%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **25.0%** (3/12)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
- **20.0%** (2/10)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket ≠ (4.0, inf]`
   - `before_rsi_avg_bucket = (30.0, 50.0]`
- **20.0%** (2/10)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
- **10.0%** (1/10)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`
   - `before_rsi_avg_bucket = (50.0, 70.0]`

### 📊 GDAXI.INDX/30m · ALL EVENTS
- Events: 985  ·  Baseline continuation: **48.0%**

  - 🟢 **100.0%** (24/24)
      - `type = bullish_OB`
      - `dow = Mon`
  - 🟢 **81.5%** (22/27)
      - `type = bullish_OB`
      - `dow ≠ Mon`
      - `dow = Tue`
  - 🟢 **80.4%** (37/46)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **76.5%** (13/17)
      - `type = bullish_OB`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **73.5%** (25/34)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/30m · CHoCH_bearish
- Events: 34  ·  Baseline continuation: **41.2%**

  - 🔴 **25.0%** (5/20)
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/30m · CHoCH_bullish
- Events: 35  ·  Baseline continuation: **40.0%**

  - 🔴 **18.2%** (2/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (50.0, 70.0]`

### 📊 GDAXI.INDX/30m · bearish
- Events: 137  ·  Baseline continuation: **38.0%**

  - 🟢 **100.0%** (11/11)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **25.0%** (3/12)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **9.1%** (4/44)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 GDAXI.INDX/30m · bearish_OB
- Events: 110  ·  Baseline continuation: **67.3%**

  - 🟢 **91.7%** (11/12)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🟢 **84.6%** (11/13)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **73.3%** (11/15)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **71.0%** (22/31)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 GDAXI.INDX/30m · breakdown
- Events: 57  ·  Baseline continuation: **36.8%**

  - 🔴 **15.4%** (2/13)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`

### 📊 GDAXI.INDX/30m · breakout_up
- Events: 62  ·  Baseline continuation: **46.8%**

  - 🟢 **76.9%** (10/13)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/30m · bullish
- Events: 150  ·  Baseline continuation: **48.0%**

  - 🟢 **90.0%** (9/10)
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **89.5%** (17/19)
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Thu`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
  - 🔴 **10.5%** (2/19)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/30m · bullish_OB
- Events: 99  ·  Baseline continuation: **75.8%**

  - 🟢 **100.0%** (24/24)
      - `dow = Mon`
  - 🟢 **93.3%** (14/15)
      - `dow ≠ Mon`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **76.5%** (13/17)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 GDAXI.INDX/30m · engulfing_bear
- Events: 67  ·  Baseline continuation: **37.3%**

  - 🟢 **70.0%** (7/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow ≠ Tue`
  - 🔴 **0.0%** (0/13)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 GDAXI.INDX/30m · engulfing_bull
- Events: 67  ·  Baseline continuation: **49.3%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **72.2%** (13/18)
      - `dow = Tue`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 GDAXI.INDX/30m · hammer
- Events: 57  ·  Baseline continuation: **42.1%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **0.0%** (0/11)
      - `dow = Wed`

### 📊 GDAXI.INDX/30m · shooting_star
- Events: 59  ·  Baseline continuation: **45.8%**

  - 🔴 **28.6%** (4/14)
      - `dow = Tue`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`

---

## GDAXI.INDX · 1h
- Candles: **3905**  ·  Swing pivots: 618  ·  FVG: 778
- CHoCH/BOS events: 436  ·  Order Blocks: 675
- Trend Ladders detected: 175  ·  Candle patterns: 1152  ·  Breakouts: 444

### S/R Cluster Seviyeleri (top 8)
- 24206.2154 (touches: **559**, strong)
- 23116.5389 (touches: **16**, strong)
- 22834.9801 (touches: **11**, strong)
- 22698.5422 (touches: **9**, strong)
- 23008.0817 (touches: **6**, strong)
- 22379.2 (touches: **3**, moderate)
- 25461.6333 (touches: **3**, moderate)
- 21921.4 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (175 ladder)
- Continued: 74  ·  Reversed: 69  ·  Baseline continuation: **42.3%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **29.2%** (7/24)
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`
   - `direction ≠ down`
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
- **16.7%** (2/12)
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`
   - `direction ≠ down`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`

### 📊 GDAXI.INDX/1h · ALL EVENTS
- Events: 3012  ·  Baseline continuation: **44.5%**

  - 🟢 **94.4%** (17/18)
      - `type = bullish_OB`
      - `dow = Tue`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **90.9%** (40/44)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **86.2%** (25/29)
      - `type = bullish_OB`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **72.9%** (94/129)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **70.7%** (41/58)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
  - 🔴 **29.1%** (25/86)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **2.9%** (1/34)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/1h · BOS_bearish
- Events: 120  ·  Baseline continuation: **21.7%**

  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `dow = Thu`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **0.0%** (0/19)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Wed`
  - 🔴 **0.0%** (0/24)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`

### 📊 GDAXI.INDX/1h · BOS_bullish
- Events: 85  ·  Baseline continuation: **22.4%**

  - 🔴 **25.0%** (3/12)
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **23.1%** (3/13)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **6.7%** (1/15)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/15)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 GDAXI.INDX/1h · CHoCH_bearish
- Events: 108  ·  Baseline continuation: **37.0%**

  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Mon`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`

### 📊 GDAXI.INDX/1h · CHoCH_bullish
- Events: 110  ·  Baseline continuation: **36.4%**

  - 🟢 **90.0%** (9/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
  - 🔴 **25.0%** (3/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`
  - 🔴 **25.0%** (3/12)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/1h · bearish
- Events: 364  ·  Baseline continuation: **37.4%**

  - 🔴 **21.4%** (3/14)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **20.0%** (2/10)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **9.1%** (4/44)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
  - 🔴 **0.0%** (0/12)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/1h · bearish_OB
- Events: 364  ·  Baseline continuation: **66.8%**

  - 🟢 **100.0%** (19/19)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **85.7%** (12/14)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **85.7%** (18/21)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **83.3%** (10/12)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **78.6%** (11/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **30.0%** (3/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/1h · breakdown
- Events: 197  ·  Baseline continuation: **41.6%**

  - 🟢 **75.0%** (15/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **22.2%** (4/18)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Wed`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow = Thu`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/1h · breakout_up
- Events: 237  ·  Baseline continuation: **34.6%**

  - 🟢 **76.9%** (10/13)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `dow = Tue`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **22.2%** (4/18)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **10.7%** (3/28)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/1h · bullish
- Events: 405  ·  Baseline continuation: **39.3%**

  - 🟢 **76.9%** (20/26)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **29.7%** (11/37)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **29.2%** (7/24)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **23.1%** (3/13)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `dow = Wed`

### 📊 GDAXI.INDX/1h · bullish_OB
- Events: 311  ·  Baseline continuation: **69.5%**

  - 🟢 **94.4%** (17/18)
      - `dow = Tue`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **90.9%** (10/11)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **83.3%** (15/18)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **77.8%** (77/99)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`

### 📊 GDAXI.INDX/1h · engulfing_bear
- Events: 203  ·  Baseline continuation: **41.4%**

  - 🔴 **28.6%** (4/14)
      - `dow ≠ Thu`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **21.1%** (4/19)
      - `dow = Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Thu`
      - `dow = Tue`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **0.0%** (0/10)
      - `dow = Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`

### 📊 GDAXI.INDX/1h · engulfing_bull
- Events: 171  ·  Baseline continuation: **50.3%**

  - 🔴 **29.4%** (5/17)
      - `dow ≠ Fri`
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`

### 📊 GDAXI.INDX/1h · hammer
- Events: 178  ·  Baseline continuation: **40.4%**

  - 🔴 **27.3%** (3/11)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Fri`
  - 🔴 **20.8%** (5/24)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`

### 📊 GDAXI.INDX/1h · shooting_star
- Events: 159  ·  Baseline continuation: **34.6%**

  - 🔴 **25.8%** (8/31)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **21.1%** (4/19)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `dow = Tue`
  - 🔴 **8.3%** (1/12)
      - `rsi_b = (70.0, inf]`

---

## USOIL.FOREX · 5m
- Candles: **5472**  ·  Swing pivots: 749  ·  FVG: 1288
- CHoCH/BOS events: 522  ·  Order Blocks: 846
- Trend Ladders detected: 51  ·  Candle patterns: 1385  ·  Breakouts: 548

### S/R Cluster Seviyeleri (top 8)
- 97.1932 (touches: **310**, strong)
- 91.2295 (touches: **151**, strong)
- 104.3709 (touches: **125**, strong)
- 86.6 (touches: **17**, strong)
- 87.8927 (touches: **11**, strong)
- 89.0444 (touches: **9**, strong)
- 107.5344 (touches: **9**, strong)
- 115.5913 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (51 ladder)
- Continued: 14  ·  Reversed: 26  ·  Baseline continuation: **27.5%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **10.0%** (1/10)
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
- **10.0%** (1/10)
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`

### 📊 USOIL.FOREX/5m · ALL EVENTS
- Events: 4034  ·  Baseline continuation: **46.7%**

  - 🟢 **85.5%** (65/76)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **80.4%** (82/102)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Wed`
  - 🟢 **71.6%** (48/67)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **71.3%** (82/115)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
  - 🟢 **71.2%** (42/59)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
  - 🔴 **27.0%** (30/111)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `rsi_b ≠ (70.0, inf]`
      - `type = BOS_bearish`
  - 🔴 **20.7%** (18/87)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/5m · BOS_bearish
- Events: 112  ·  Baseline continuation: **27.7%**

  - 🟢 **80.0%** (8/10)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **27.0%** (10/37)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **6.7%** (1/15)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/11)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/5m · BOS_bullish
- Events: 107  ·  Baseline continuation: **25.2%**

  - 🔴 **28.6%** (8/28)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
  - 🔴 **13.8%** (4/29)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/5m · CHoCH_bearish
- Events: 146  ·  Baseline continuation: **46.6%**

  - 🟢 **81.8%** (9/11)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Fri`
  - 🟢 **73.3%** (11/15)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow = Wed`
  - 🟢 **70.6%** (12/17)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **28.6%** (4/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **18.8%** (3/16)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 USOIL.FOREX/5m · CHoCH_bullish
- Events: 147  ·  Baseline continuation: **47.6%**

  - 🟢 **92.3%** (12/13)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **76.5%** (13/17)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Mon`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🔴 **12.0%** (3/25)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 USOIL.FOREX/5m · bearish
- Events: 599  ·  Baseline continuation: **40.7%**

  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **23.1%** (3/13)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Thu`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **17.6%** (3/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **13.9%** (5/36)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/5m · bearish_OB
- Events: 435  ·  Baseline continuation: **65.3%**

  - 🟢 **100.0%** (15/15)
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **92.9%** (13/14)
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Mon`
  - 🟢 **92.3%** (24/26)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **80.6%** (25/31)
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Mon`
      - `dow = Tue`

### 📊 USOIL.FOREX/5m · breakdown
- Events: 232  ·  Baseline continuation: **43.1%**

  - 🔴 **21.4%** (3/14)
      - `dow = Wed`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **14.3%** (2/14)
      - `dow = Wed`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **7.7%** (1/13)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/5m · breakout_up
- Events: 310  ·  Baseline continuation: **38.1%**

  - 🟢 **85.7%** (12/14)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **30.0%** (6/20)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **29.4%** (5/17)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🔴 **25.0%** (4/16)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Tue`
  - 🔴 **6.7%** (3/45)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`

### 📊 USOIL.FOREX/5m · bullish
- Events: 672  ·  Baseline continuation: **43.3%**

  - 🟢 **80.0%** (32/40)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **23.5%** (4/17)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Fri`
  - 🔴 **0.0%** (0/13)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.4, inf]`

### 📊 USOIL.FOREX/5m · bullish_OB
- Events: 410  ·  Baseline continuation: **67.8%**

  - 🟢 **90.0%** (9/10)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Wed`
  - 🟢 **88.3%** (53/60)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
  - 🟢 **83.3%** (10/12)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **76.8%** (53/69)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **75.0%** (12/16)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`
  - 🔴 **28.6%** (4/14)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Tue`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/5m · engulfing_bear
- Events: 192  ·  Baseline continuation: **39.6%**

  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **22.7%** (5/22)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/5m · engulfing_bull
- Events: 181  ·  Baseline continuation: **46.4%**

  - 🟢 **72.7%** (8/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
  - 🟢 **70.0%** (7/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **14.3%** (2/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · hammer
- Events: 254  ·  Baseline continuation: **43.3%**

  - 🟢 **84.6%** (11/13)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **25.9%** (14/54)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 USOIL.FOREX/5m · shooting_star
- Events: 237  ·  Baseline continuation: **43.0%**

  - 🔴 **27.3%** (3/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (4/16)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **20.0%** (3/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **0.0%** (0/16)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`

---

## USOIL.FOREX · 30m
- Candles: **1312**  ·  Swing pivots: 162  ·  FVG: 284
- CHoCH/BOS events: 120  ·  Order Blocks: 218
- Trend Ladders detected: 67  ·  Candle patterns: 339  ·  Breakouts: 144

### S/R Cluster Seviyeleri (top 8)
- 98.3076 (touches: **75**, strong)
- 92.7673 (touches: **22**, strong)
- 90.4162 (touches: **21**, strong)
- 104.4633 (touches: **15**, strong)
- 86.982 (touches: **5**, strong)
- 88.18 (touches: **3**, moderate)
- 112.4767 (touches: **3**, moderate)
- 106.995 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (67 ladder)
- Continued: 31  ·  Reversed: 27  ·  Baseline continuation: **46.3%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **70.0%** (7/10)
   - `before_rsi_last_bucket = (70.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (3/15)
   - `before_rsi_last_bucket ≠ (70.0, inf]`
   - `start_dist_ema50_atr_bucket ≠ (0.0, 1.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`

### 📊 USOIL.FOREX/30m · ALL EVENTS
- Events: 972  ·  Baseline continuation: **50.5%**

  - 🟢 **100.0%** (20/20)
      - `type = bullish_OB`
      - `dow = Wed`
  - 🟢 **86.4%** (19/22)
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **86.4%** (19/22)
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `dow = Fri`
  - 🔴 **23.8%** (5/21)
      - `type ≠ bullish_OB`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **22.2%** (6/27)
      - `type ≠ bullish_OB`
      - `rsi_b ≠ (30.0, 50.0]`
      - `type = BOS_bullish`
  - 🔴 **16.7%** (3/18)
      - `type ≠ bullish_OB`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/30m · CHoCH_bearish
- Events: 38  ·  Baseline continuation: **36.8%**

  - 🔴 **21.1%** (4/19)
      - `rsi_b = (30.0, 50.0]`

### 📊 USOIL.FOREX/30m · CHoCH_bullish
- Events: 37  ·  Baseline continuation: **59.5%**

  - 🟢 **82.4%** (14/17)
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · bearish
- Events: 122  ·  Baseline continuation: **39.3%**

  - 🟢 **78.6%** (11/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **20.0%** (4/20)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **5.9%** (1/17)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · bearish_OB
- Events: 103  ·  Baseline continuation: **62.1%**

  - 🟢 **93.3%** (14/15)
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **91.7%** (11/12)
      - `dow ≠ Tue`
      - `rsi_b = (70.0, inf]`
  - 🟢 **80.0%** (16/20)
      - `dow = Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **15.8%** (3/19)
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/30m · breakout_up
- Events: 102  ·  Baseline continuation: **57.8%**

  - 🟢 **100.0%** (11/11)
      - `dow = Wed`
      - `rsi_b = (70.0, inf]`
  - 🟢 **80.0%** (8/10)
      - `dow = Wed`
      - `rsi_b ≠ (70.0, inf]`
  - 🟢 **75.9%** (22/29)
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **25.0%** (4/16)
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Wed`
      - `dow = Mon`

### 📊 USOIL.FOREX/30m · bullish
- Events: 160  ·  Baseline continuation: **48.8%**

  - 🟢 **93.8%** (15/16)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🟢 **84.6%** (11/13)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `dow = Fri`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Mon`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **20.0%** (2/10)
      - `dow = Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Mon`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/10)
      - `dow = Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`

### 📊 USOIL.FOREX/30m · bullish_OB
- Events: 115  ·  Baseline continuation: **74.8%**

  - 🟢 **100.0%** (10/10)
      - `dow = Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **100.0%** (10/10)
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **86.4%** (19/22)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **86.4%** (19/22)
      - `dow ≠ Wed`
      - `dow = Fri`

### 📊 USOIL.FOREX/30m · engulfing_bear
- Events: 47  ·  Baseline continuation: **38.3%**

  - 🔴 **20.0%** (3/15)
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/30m · engulfing_bull
- Events: 51  ·  Baseline continuation: **56.9%**

  - 🟢 **91.7%** (11/12)
      - `dow = Fri`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/30m · hammer
- Events: 64  ·  Baseline continuation: **42.2%**

  - 🔴 **26.7%** (4/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`

### 📊 USOIL.FOREX/30m · shooting_star
- Events: 48  ·  Baseline continuation: **29.2%**

  - 🔴 **26.7%** (4/15)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **0.0%** (0/14)
      - `vol_z_b = (0.5, inf]`

---

## USOIL.FOREX · 1h
- Candles: **2230**  ·  Swing pivots: 494  ·  FVG: 364
- CHoCH/BOS events: 331  ·  Order Blocks: 404
- Trend Ladders detected: 69  ·  Candle patterns: 578  ·  Breakouts: 193

### S/R Cluster Seviyeleri (top 8)
- 95.1771 (touches: **402**, strong)
- 64.8678 (touches: **51**, strong)
- 78.5986 (touches: **7**, strong)
- 82.1271 (touches: **7**, strong)
- 108.27 (touches: **5**, strong)
- 73.1075 (touches: **4**, moderate)
- 106.6433 (touches: **3**, moderate)
- 76.98 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (69 ladder)
- Continued: 27  ·  Reversed: 32  ·  Baseline continuation: **39.1%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **80.0%** (8/10)
   - `direction = up`
   - `bb_squeeze_str = False`
   - `before_rsi_avg_bucket = (30.0, 50.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (2/12)
   - `direction ≠ up`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
- **10.0%** (1/10)
   - `direction = up`
   - `bb_squeeze_str ≠ False`

### 📊 USOIL.FOREX/1h · ALL EVENTS
- Events: 1549  ·  Baseline continuation: **47.0%**

  - 🟢 **96.9%** (31/32)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **93.3%** (14/15)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **92.9%** (26/28)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow = Fri`
      - `rsi_b = (70.0, inf]`
  - 🟢 **82.4%** (14/17)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **80.3%** (94/117)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **13.3%** (6/45)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow ≠ Fri`
      - `type = breakdown`

### 📊 USOIL.FOREX/1h · BOS_bearish
- Events: 117  ·  Baseline continuation: **29.9%**

  - 🟢 **88.9%** (16/18)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Wed`
  - 🔴 **21.1%** (4/19)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`

### 📊 USOIL.FOREX/1h · BOS_bullish
- Events: 38  ·  Baseline continuation: **23.7%**

  - 🔴 **20.0%** (3/15)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/1h · CHoCH_bearish
- Events: 73  ·  Baseline continuation: **50.7%**

  - 🟢 **100.0%** (12/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **75.0%** (12/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **26.7%** (4/15)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **6.7%** (1/15)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/1h · CHoCH_bullish
- Events: 74  ·  Baseline continuation: **39.2%**

  - 🟢 **90.0%** (9/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`
  - 🟢 **70.0%** (7/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/12)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · bearish
- Events: 152  ·  Baseline continuation: **27.0%**

  - 🟢 **85.7%** (12/14)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Mon`
  - 🔴 **27.3%** (6/22)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`
  - 🔴 **20.0%** (2/10)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **15.3%** (9/59)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
  - 🔴 **0.0%** (0/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`

### 📊 USOIL.FOREX/1h · bearish_OB
- Events: 212  ·  Baseline continuation: **72.2%**

  - 🟢 **96.0%** (24/25)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
  - 🟢 **83.3%** (10/12)
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`
  - 🟢 **79.3%** (65/82)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
  - 🟢 **73.1%** (19/26)
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **23.1%** (3/13)
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/1h · breakdown
- Events: 59  ·  Baseline continuation: **20.3%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
  - 🔴 **0.0%** (0/11)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/1h · breakout_up
- Events: 132  ·  Baseline continuation: **41.7%**

  - 🟢 **84.6%** (11/13)
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **21.7%** (5/23)
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
  - 🔴 **6.2%** (1/16)
      - `dow ≠ Fri`
      - `dow = Mon`

### 📊 USOIL.FOREX/1h · bullish
- Events: 203  ·  Baseline continuation: **42.4%**

  - 🟢 **100.0%** (11/11)
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **78.6%** (11/14)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **72.7%** (8/11)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **17.3%** (9/52)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/1h · bullish_OB
- Events: 192  ·  Baseline continuation: **77.6%**

  - 🟢 **100.0%** (21/21)
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **94.1%** (16/17)
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **93.3%** (14/15)
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **85.2%** (23/27)
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **73.7%** (14/19)
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/1h · engulfing_bear
- Events: 52  ·  Baseline continuation: **46.2%**

  - 🟢 **75.0%** (12/16)
      - `dow = Tue`
  - 🔴 **16.7%** (3/18)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/1h · engulfing_bull
- Events: 52  ·  Baseline continuation: **38.5%**

  - 🟢 **70.0%** (7/10)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **13.3%** (2/15)
      - `dow = Tue`

### 📊 USOIL.FOREX/1h · hammer
- Events: 121  ·  Baseline continuation: **43.8%**

  - 🟢 **76.2%** (16/21)
      - `dow = Fri`
  - 🔴 **28.6%** (12/42)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **7.7%** (1/13)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · shooting_star
- Events: 72  ·  Baseline continuation: **34.7%**

  - 🔴 **7.7%** (1/13)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **0.0%** (0/12)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`

---
