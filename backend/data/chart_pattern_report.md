# Price Action Pattern Mining Report
_2026-07-21T20:58:26.219922Z_

Bu rapor **HİÇBİR MODELE BAKMADAN** üretilmiştir — yalnızca ham OHLCV.
Üç bağımsız layer:
1. **SMC Structure**: swing pivots, FVG, CHoCH, BOS, Order Blocks
2. **Trend Ladders**: ritmik kademeli hareketler + öncesi/sonrası analiz
3. **Generic Events**: candle patterns, breakouts, S/R touches

---

## XAUUSD · 5m
- Candles: **10000**  ·  Swing pivots: 1320  ·  FVG: 1835
- CHoCH/BOS events: 897  ·  Order Blocks: 1571
- Trend Ladders detected: 104  ·  Candle patterns: 2742  ·  Breakouts: 1003

### S/R Cluster Seviyeleri (top 8)
- 4091.0642 (touches: **1088**, strong)
- 4328.5248 (touches: **156**, strong)
- 4266.2111 (touches: **36**, strong)
- 4234.4613 (touches: **16**, strong)
- 4365.56 (touches: **7**, strong)
- 4468.6 (touches: **4**, moderate)
- 4294.32 (touches: **3**, moderate)
- 4459.5967 (touches: **3**, moderate)

### 🪜 Trend Ladder Analizi (104 ladder)
- Continued: 37  ·  Reversed: 46  ·  Baseline continuation: **35.6%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **21.4%** (6/28)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `before_rsi_avg_bucket = (30.0, 50.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
- **18.8%** (3/16)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`

### 📊 XAUUSD/5m · ALL EVENTS
- Events: 6863  ·  Baseline continuation: **45.7%**

  - 🟢 **100.0%** (22/22)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🟢 **95.7%** (44/46)
      - `type = bearish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **95.0%** (19/20)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Mon`
  - 🟢 **83.6%** (107/128)
      - `type = bearish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
  - 🟢 **81.8%** (27/33)
      - `type = bearish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **21.5%** (41/191)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **18.8%** (30/160)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **0.0%** (0/19)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · BOS_bearish
- Events: 210  ·  Baseline continuation: **19.5%**

  - 🔴 **28.6%** (6/21)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **27.3%** (3/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **16.4%** (11/67)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **13.3%** (2/15)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
      - `dow = Fri`
  - 🔴 **6.2%** (1/16)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/5m · BOS_bullish
- Events: 160  ·  Baseline continuation: **18.8%**

  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **25.0%** (5/20)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **15.4%** (2/13)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/5m · CHoCH_bearish
- Events: 254  ·  Baseline continuation: **43.7%**

  - 🟢 **85.4%** (35/41)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Thu`
  - 🟢 **70.0%** (7/10)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Thu`
  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **19.5%** (8/41)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **11.1%** (2/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **0.0%** (0/15)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 XAUUSD/5m · CHoCH_bullish
- Events: 258  ·  Baseline continuation: **38.4%**

  - 🟢 **100.0%** (10/10)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **77.3%** (17/22)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **27.8%** (15/54)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
  - 🔴 **25.0%** (4/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **12.5%** (2/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
  - 🔴 **7.4%** (2/27)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **0.0%** (0/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · bearish
- Events: 954  ·  Baseline continuation: **43.6%**

  - 🟢 **78.6%** (22/28)
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **71.4%** (10/14)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **29.7%** (11/37)
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **29.4%** (30/102)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **26.7%** (4/15)
      - `dow = Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **15.0%** (3/20)
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/5m · bearish_OB
- Events: 784  ·  Baseline continuation: **72.2%**

  - 🟢 **100.0%** (32/32)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **100.0%** (10/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **92.9%** (26/28)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow = Mon`
  - 🟢 **86.4%** (19/22)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **85.7%** (12/14)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/5m · breakdown
- Events: 561  ·  Baseline continuation: **39.0%**

  - 🔴 **25.0%** (3/12)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **22.2%** (4/18)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **6.7%** (1/15)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **4.5%** (1/22)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🔴 **0.0%** (0/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Wed`

### 📊 XAUUSD/5m · breakout_up
- Events: 428  ·  Baseline continuation: **35.0%**

  - 🟢 **70.0%** (7/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **29.4%** (10/34)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **18.9%** (7/37)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **6.7%** (2/30)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/22)
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · bullish
- Events: 862  ·  Baseline continuation: **35.7%**

  - 🔴 **27.6%** (8/29)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **26.3%** (5/19)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Fri`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **19.6%** (9/46)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Fri`
      - `dow = Mon`
  - 🔴 **14.3%** (2/14)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 XAUUSD/5m · bullish_OB
- Events: 786  ·  Baseline continuation: **67.0%**

  - 🟢 **100.0%** (28/28)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Wed`
  - 🟢 **92.9%** (13/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🟢 **80.3%** (98/122)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **78.3%** (18/23)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **70.1%** (61/87)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/5m · engulfing_bear
- Events: 323  ·  Baseline continuation: **46.1%**

  - 🟢 **71.4%** (10/14)
      - `dow = Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **71.4%** (10/14)
      - `dow = Fri`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **29.4%** (5/17)
      - `dow ≠ Fri`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **27.3%** (3/11)
      - `dow = Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`

### 📊 XAUUSD/5m · engulfing_bull
- Events: 374  ·  Baseline continuation: **37.2%**

  - 🔴 **29.2%** (7/24)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **28.3%** (15/53)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **23.1%** (6/26)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **6.2%** (1/16)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/5m · hammer
- Events: 437  ·  Baseline continuation: **40.3%**

  - 🟢 **92.3%** (12/13)
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **70.6%** (12/17)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Thu`
  - 🔴 **22.2%** (8/36)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **21.4%** (6/28)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **18.8%** (3/16)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`

### 📊 XAUUSD/5m · shooting_star
- Events: 472  ·  Baseline continuation: **43.6%**

  - 🟢 **83.3%** (15/18)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **82.4%** (14/17)
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **23.0%** (20/87)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.15, 0.4]`

---

## XAUUSD · 15m
- Candles: **4709**  ·  Swing pivots: 558  ·  FVG: 902
- CHoCH/BOS events: 389  ·  Order Blocks: 761
- Trend Ladders detected: 262  ·  Candle patterns: 1293  ·  Breakouts: 502

### S/R Cluster Seviyeleri (top 8)
- 4066.4898 (touches: **204**, strong)
- 4510.777 (touches: **157**, strong)
- 4186.9977 (touches: **48**, strong)
- 4320.9056 (touches: **45**, strong)
- 4710.785 (touches: **16**, strong)
- 4347.9579 (touches: **14**, strong)
- 3985.435 (touches: **10**, strong)
- 3972.0963 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (262 ladder)
- Continued: 111  ·  Reversed: 112  ·  Baseline continuation: **42.4%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **86.7%** (13/15)
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
   - `before_volz_avg_bucket = (-inf, -0.5]`
   - `before_adx_avg_bucket = (-inf, 18.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **6.2%** (1/16)
   - `before_adx_avg_bucket = (18.0, 25.0]`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`

### 📊 XAUUSD/15m · ALL EVENTS
- Events: 3319  ·  Baseline continuation: **47.7%**

  - 🟢 **100.0%** (21/21)
      - `type = bearish_OB`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **85.0%** (17/20)
      - `type = bearish_OB`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **81.7%** (94/115)
      - `type = bearish_OB`
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **80.0%** (12/15)
      - `type = bearish_OB`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **75.8%** (25/33)
      - `type = bearish_OB`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **21.9%** (16/73)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ bearish`
      - `type = BOS_bullish`
  - 🔴 **16.7%** (3/18)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/15m · BOS_bearish
- Events: 99  ·  Baseline continuation: **25.3%**

  - 🔴 **25.0%** (4/16)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b = (25.0, inf]`
      - `dow = Wed`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
      - `dow = Fri`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
  - 🔴 **0.0%** (0/11)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/15m · BOS_bullish
- Events: 73  ·  Baseline continuation: **21.9%**

  - 🔴 **23.8%** (5/21)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
  - 🔴 **23.1%** (3/13)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
  - 🔴 **6.7%** (1/15)
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/15m · CHoCH_bearish
- Events: 108  ·  Baseline continuation: **49.1%**

  - 🟢 **80.0%** (12/15)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **23.1%** (6/26)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`

### 📊 XAUUSD/15m · CHoCH_bullish
- Events: 108  ·  Baseline continuation: **37.0%**

  - 🟢 **78.9%** (15/19)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🔴 **27.3%** (6/22)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 XAUUSD/15m · bearish
- Events: 473  ·  Baseline continuation: **50.3%**

  - 🟢 **85.7%** (12/14)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **72.7%** (8/11)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **72.2%** (13/18)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
  - 🟢 **70.4%** (19/27)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **23.5%** (4/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **11.1%** (2/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/15m · bearish_OB
- Events: 402  ·  Baseline continuation: **74.4%**

  - 🟢 **100.0%** (21/21)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **85.7%** (72/84)
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`
  - 🟢 **85.0%** (17/20)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **84.6%** (11/13)
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Tue`
  - 🟢 **84.2%** (16/19)
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`

### 📊 XAUUSD/15m · breakdown
- Events: 293  ·  Baseline continuation: **44.7%**

  - 🟢 **92.9%** (13/14)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **90.9%** (10/11)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
  - 🔴 **20.0%** (4/20)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `dow ≠ Thu`
  - 🔴 **13.6%** (3/22)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/15m · breakout_up
- Events: 205  ·  Baseline continuation: **37.6%**

  - 🔴 **6.7%** (1/15)
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **6.2%** (1/16)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/15m · bullish
- Events: 426  ·  Baseline continuation: **35.4%**

  - 🔴 **26.7%** (8/30)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **24.4%** (11/45)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Wed`
      - `rsi_b = (70.0, inf]`
  - 🔴 **15.4%** (2/13)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 XAUUSD/15m · bullish_OB
- Events: 359  ·  Baseline continuation: **61.6%**

  - 🟢 **100.0%** (14/14)
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
  - 🟢 **79.3%** (46/58)
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
  - 🟢 **74.4%** (32/43)
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Mon`
  - 🔴 **30.0%** (3/10)
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **16.7%** (3/18)
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/15m · engulfing_bear
- Events: 195  ·  Baseline continuation: **47.7%**

  - 🟢 **81.8%** (9/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **30.0%** (6/20)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **25.0%** (3/12)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`

### 📊 XAUUSD/15m · engulfing_bull
- Events: 190  ·  Baseline continuation: **37.9%**

  - 🔴 **25.8%** (8/31)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **17.6%** (3/17)
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **7.7%** (1/13)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/15m · hammer
- Events: 179  ·  Baseline continuation: **35.8%**

  - 🟢 **70.6%** (12/17)
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.8%** (6/38)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`

### 📊 XAUUSD/15m · shooting_star
- Events: 209  ·  Baseline continuation: **49.3%**

  - 🟢 **80.0%** (20/25)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **70.0%** (7/10)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **21.4%** (3/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **14.3%** (2/14)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Thu`

---

## XAUUSD · 30m
- Candles: **4394**  ·  Swing pivots: 553  ·  FVG: 894
- CHoCH/BOS events: 380  ·  Order Blocks: 710
- Trend Ladders detected: 245  ·  Candle patterns: 1220  ·  Breakouts: 442

### S/R Cluster Seviyeleri (top 8)
- 4623.7044 (touches: **298**, strong)
- 4068.7673 (touches: **98**, strong)
- 4318.6962 (touches: **24**, strong)
- 4178.2117 (touches: **23**, strong)
- 3966.6418 (touches: **11**, strong)
- 4349.7882 (touches: **11**, strong)
- 4837.786 (touches: **10**, strong)
- 4226.625 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (245 ladder)
- Continued: 110  ·  Reversed: 104  ·  Baseline continuation: **44.9%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **75.0%** (9/12)
   - `bb_squeeze_str ≠ False`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (2/12)
   - `bb_squeeze_str = False`
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `start_dist_ema50_atr_bucket = (-1.0, 0.0]`

### 📊 XAUUSD/30m · ALL EVENTS
- Events: 3179  ·  Baseline continuation: **49.0%**

  - 🟢 **100.0%** (17/17)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **85.4%** (35/41)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🟢 **83.3%** (60/72)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **81.8%** (18/22)
      - `type = bearish_OB`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.4%** (43/57)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **28.1%** (73/260)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `dow = Mon`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 XAUUSD/30m · BOS_bearish
- Events: 93  ·  Baseline continuation: **32.3%**

  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **20.8%** (5/24)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **10.5%** (2/19)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 XAUUSD/30m · BOS_bullish
- Events: 76  ·  Baseline continuation: **23.7%**

  - 🔴 **21.1%** (4/19)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **5.3%** (1/19)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/30m · CHoCH_bearish
- Events: 105  ·  Baseline continuation: **53.3%**

  - 🟢 **80.0%** (16/20)
      - `dow = Wed`
  - 🟢 **76.5%** (13/17)
      - `dow ≠ Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 XAUUSD/30m · CHoCH_bullish
- Events: 106  ·  Baseline continuation: **49.1%**

  - 🟢 **86.7%** (13/15)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **72.7%** (8/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **17.6%** (3/17)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/30m · bearish
- Events: 466  ·  Baseline continuation: **50.9%**

  - 🟢 **75.0%** (15/20)
      - `dow ≠ Mon`
      - `rsi_b = (-inf, 30.0]`
      - `dow = Fri`
  - 🟢 **71.4%** (10/14)
      - `dow ≠ Mon`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **29.0%** (9/31)
      - `dow ≠ Mon`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Fri`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **27.3%** (3/11)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **16.7%** (2/12)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **12.5%** (2/16)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`

### 📊 XAUUSD/30m · bearish_OB
- Events: 375  ·  Baseline continuation: **77.1%**

  - 🟢 **100.0%** (17/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`
  - 🟢 **100.0%** (17/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **93.8%** (15/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **88.9%** (16/18)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **82.9%** (34/41)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`

### 📊 XAUUSD/30m · breakdown
- Events: 235  ·  Baseline continuation: **50.6%**

  - 🟢 **78.9%** (15/19)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
      - `dow = Fri`
  - 🟢 **72.9%** (35/48)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
  - 🔴 **27.3%** (3/11)
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **20.0%** (3/15)
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **7.7%** (1/13)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Fri`

### 📊 XAUUSD/30m · breakout_up
- Events: 204  ·  Baseline continuation: **40.7%**

  - 🟢 **70.4%** (19/27)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **30.0%** (3/10)
      - `dow = Mon`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **14.3%** (2/14)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **14.3%** (2/14)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/30m · bullish
- Events: 426  ·  Baseline continuation: **38.3%**

  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **16.7%** (3/18)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`
  - 🔴 **7.1%** (1/14)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🔴 **5.9%** (1/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/30m · bullish_OB
- Events: 335  ·  Baseline continuation: **63.0%**

  - 🟢 **93.3%** (28/30)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Fri`
      - `dow ≠ Thu`
  - 🟢 **72.0%** (90/125)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/30m · engulfing_bear
- Events: 176  ·  Baseline continuation: **43.8%**

  - 🟢 **82.4%** (14/17)
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (3/12)
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (4/16)
      - `dow ≠ Mon`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
  - 🔴 **20.0%** (2/10)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **7.7%** (1/13)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/30m · engulfing_bull
- Events: 191  ·  Baseline continuation: **35.6%**

  - 🟢 **83.3%** (10/12)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **30.0%** (6/20)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Thu`
  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **26.7%** (4/15)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
  - 🔴 **26.3%** (5/19)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`

### 📊 XAUUSD/30m · hammer
- Events: 199  ·  Baseline continuation: **32.2%**

  - 🔴 **26.7%** (4/15)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **20.0%** (14/70)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 XAUUSD/30m · shooting_star
- Events: 192  ·  Baseline continuation: **47.9%**

  - 🟢 **76.9%** (10/13)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **75.0%** (12/16)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **27.3%** (6/22)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`

---

## XAUUSD · 1h
- Candles: **1979**  ·  Swing pivots: 243  ·  FVG: 395
- CHoCH/BOS events: 172  ·  Order Blocks: 344
- Trend Ladders detected: 102  ·  Candle patterns: 545  ·  Breakouts: 195

### S/R Cluster Seviyeleri (top 8)
- 4071.7573 (touches: **52**, strong)
- 4507.8266 (touches: **47**, strong)
- 4698.035 (touches: **44**, strong)
- 4592.7195 (touches: **20**, strong)
- 4786.2462 (touches: **16**, strong)
- 3971.6891 (touches: **11**, strong)
- 4183.2682 (touches: **11**, strong)
- 4356.3133 (touches: **9**, strong)

### 🪜 Trend Ladder Analizi (102 ladder)
- Continued: 48  ·  Reversed: 40  ·  Baseline continuation: **47.1%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **77.8%** (21/27)
   - `ladder_total_atr_bucket ≠ (2.5, inf]`
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **23.1%** (3/13)
   - `ladder_total_atr_bucket ≠ (2.5, inf]`
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
- **10.0%** (1/10)
   - `ladder_total_atr_bucket = (2.5, inf]`
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`

### 📊 XAUUSD/1h · ALL EVENTS
- Events: 1435  ·  Baseline continuation: **49.1%**

  - 🟢 **95.0%** (19/20)
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **90.0%** (27/30)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `dow = Tue`
  - 🟢 **82.6%** (19/23)
      - `type = bearish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🟢 **78.9%** (15/19)
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **74.4%** (29/39)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `dow = Tue`
      - `type = bearish`
  - 🔴 **12.9%** (4/31)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `dow ≠ Tue`
      - `type = BOS_bullish`

### 📊 XAUUSD/1h · BOS_bearish
- Events: 40  ·  Baseline continuation: **25.0%**

  - 🔴 **23.1%** (3/13)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **13.3%** (2/15)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/1h · BOS_bullish
- Events: 37  ·  Baseline continuation: **16.2%**

  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **6.7%** (1/15)
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/1h · CHoCH_bearish
- Events: 47  ·  Baseline continuation: **48.9%**

  - 🔴 **27.8%** (5/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/1h · CHoCH_bullish
- Events: 48  ·  Baseline continuation: **39.6%**

  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/1h · bearish
- Events: 203  ·  Baseline continuation: **48.3%**

  - 🟢 **93.8%** (15/16)
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **82.4%** (14/17)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **20.0%** (4/20)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`

### 📊 XAUUSD/1h · bearish_OB
- Events: 185  ·  Baseline continuation: **67.6%**

  - 🟢 **100.0%** (12/12)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **100.0%** (15/15)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **90.0%** (9/10)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **80.0%** (8/10)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
  - 🟢 **77.8%** (14/18)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 XAUUSD/1h · breakdown
- Events: 108  ·  Baseline continuation: **50.9%**

  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`

### 📊 XAUUSD/1h · breakout_up
- Events: 84  ·  Baseline continuation: **40.5%**

  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **4.8%** (1/21)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/1h · bullish
- Events: 189  ·  Baseline continuation: **36.5%**

  - 🔴 **21.4%** (3/14)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
  - 🔴 **20.0%** (2/10)
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `dow = Thu`
  - 🔴 **7.1%** (1/14)
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/1h · bullish_OB
- Events: 159  ·  Baseline continuation: **69.2%**

  - 🟢 **100.0%** (18/18)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **82.1%** (46/56)
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **75.0%** (9/12)
      - `dow ≠ Wed`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/1h · engulfing_bear
- Events: 96  ·  Baseline continuation: **56.2%**

  - 🟢 **80.0%** (16/20)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 XAUUSD/1h · engulfing_bull
- Events: 75  ·  Baseline continuation: **41.3%**

  - 🔴 **27.8%** (5/18)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **21.4%** (3/14)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 XAUUSD/1h · hammer
- Events: 73  ·  Baseline continuation: **35.6%**

  - 🔴 **21.4%** (3/14)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/1h · shooting_star
- Events: 91  ·  Baseline continuation: **48.4%**

  - 🟢 **72.7%** (8/11)
      - `adx_b = (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **27.3%** (3/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Fri`

---

## NDX.INDX · 5m
- Candles: **10000**  ·  Swing pivots: 1143  ·  FVG: 2408
- CHoCH/BOS events: 801  ·  Order Blocks: 1778
- Trend Ladders detected: 154  ·  Candle patterns: 2688  ·  Breakouts: 1390

### S/R Cluster Seviyeleri (top 8)
- 29692.1484 (touches: **1017**, strong)
- 28641.2972 (touches: **76**, strong)
- 30678.38 (touches: **40**, strong)
- 28241.1908 (touches: **2**, weak)
- 28348.95 (touches: **2**, weak)
- 28421.35 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (154 ladder)
- Continued: 68  ·  Reversed: 65  ·  Baseline continuation: **44.2%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **27.3%** (3/11)
   - `start_dist_ema50_atr_bucket ≠ (-1.0, 0.0]`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
- **10.0%** (1/10)
   - `start_dist_ema50_atr_bucket = (-1.0, 0.0]`
   - `ladder_slope_atr_bucket = (-inf, 0.2]`

### 📊 NDX.INDX/5m · ALL EVENTS
- Events: 8110  ·  Baseline continuation: **47.1%**

  - 🟢 **96.6%** (28/29)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **77.7%** (87/112)
      - `type = bearish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Wed`
  - 🟢 **77.1%** (131/170)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **75.9%** (22/29)
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Fri`
  - 🔴 **26.5%** (26/98)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **26.4%** (48/182)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bullish`
      - `type = BOS_bearish`
  - 🔴 **9.9%** (7/71)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/5m · BOS_bearish
- Events: 182  ·  Baseline continuation: **26.4%**

  - 🔴 **30.0%** (6/20)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **26.7%** (8/30)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
  - 🔴 **26.4%** (14/53)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 NDX.INDX/5m · BOS_bullish
- Events: 169  ·  Baseline continuation: **19.5%**

  - 🔴 **21.7%** (5/23)
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **8.3%** (1/12)
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **7.1%** (1/14)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow = Fri`
  - 🔴 **6.7%** (1/15)
      - `adx_b = (25.0, inf]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **5.6%** (1/18)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`

### 📊 NDX.INDX/5m · CHoCH_bearish
- Events: 224  ·  Baseline continuation: **43.8%**

  - 🟢 **76.9%** (40/52)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
  - 🔴 **25.0%** (10/40)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **10.0%** (2/20)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/17)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/5m · CHoCH_bullish
- Events: 222  ·  Baseline continuation: **43.2%**

  - 🟢 **81.2%** (13/16)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🟢 **71.4%** (10/14)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **28.0%** (7/25)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **23.1%** (3/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `dow = Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **13.3%** (2/15)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/5m · bearish
- Events: 1197  ·  Baseline continuation: **45.0%**

  - 🔴 **25.9%** (15/58)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **18.8%** (3/16)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Mon`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **0.0%** (0/11)
      - `atr_pct_b = (-inf, 0.05]`

### 📊 NDX.INDX/5m · bearish_OB
- Events: 883  ·  Baseline continuation: **67.6%**

  - 🟢 **83.3%** (45/54)
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **83.3%** (15/18)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **76.3%** (87/114)
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **73.7%** (14/19)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
  - 🟢 **72.4%** (42/58)
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 NDX.INDX/5m · breakdown
- Events: 672  ·  Baseline continuation: **46.0%**

  - 🟢 **86.7%** (13/15)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **80.0%** (20/25)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **27.1%** (16/59)
      - `dow ≠ Fri`
      - `dow = Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/5m · breakout_up
- Events: 702  ·  Baseline continuation: **38.7%**

  - 🟢 **100.0%** (11/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = NA`
  - 🔴 **29.0%** (20/69)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **24.2%** (8/33)
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ NA`
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **23.3%** (10/43)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
  - 🔴 **20.0%** (8/40)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **13.3%** (2/15)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow = Tue`

### 📊 NDX.INDX/5m · bullish
- Events: 1204  ·  Baseline continuation: **39.1%**

  - 🟢 **90.0%** (9/10)
      - `vol_z_b = NA`
  - 🟢 **76.2%** (16/21)
      - `vol_z_b ≠ NA`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **21.2%** (25/118)
      - `vol_z_b ≠ NA`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `rsi_b = (50.0, 70.0]`

### 📊 NDX.INDX/5m · bullish_OB
- Events: 895  ·  Baseline continuation: **66.9%**

  - 🟢 **100.0%** (19/19)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **100.0%** (14/14)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **90.0%** (9/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
  - 🟢 **83.3%** (35/42)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **79.5%** (66/83)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **22.2%** (6/27)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/5m · engulfing_bear
- Events: 466  ·  Baseline continuation: **42.3%**

  - 🔴 **29.4%** (5/17)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **29.4%** (5/17)
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **23.8%** (5/21)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **19.5%** (8/41)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **15.8%** (3/19)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/5m · engulfing_bull
- Events: 399  ·  Baseline continuation: **38.8%**

  - 🟢 **76.9%** (10/13)
      - `dow ≠ Tue`
      - `atr_pct_b = (-inf, 0.05]`
  - 🟢 **72.2%** (13/18)
      - `dow = Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **30.0%** (3/10)
      - `dow = Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **22.7%** (17/75)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/5m · hammer
- Events: 497  ·  Baseline continuation: **41.4%**

  - 🟢 **81.8%** (9/11)
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **26.1%** (12/46)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b ≠ (70.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
  - 🔴 **25.0%** (4/16)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/5m · shooting_star
- Events: 398  ·  Baseline continuation: **50.0%**

  - 🟢 **90.0%** (9/10)
      - `dow = Wed`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **75.0%** (12/16)
      - `dow ≠ Wed`
      - `rsi_b = (-inf, 30.0]`

---

## NDX.INDX · 15m
- Candles: **4709**  ·  Swing pivots: 542  ·  FVG: 1115
- CHoCH/BOS events: 385  ·  Order Blocks: 879
- Trend Ladders detected: 268  ·  Candle patterns: 1373  ·  Breakouts: 620

### S/R Cluster Seviyeleri (top 8)
- 29647.4224 (touches: **514**, strong)
- 28627.6882 (touches: **17**, strong)
- 28517.1 (touches: **4**, moderate)
- 28207.0 (touches: **2**, weak)
- 30771.25 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (268 ladder)
- Continued: 110  ·  Reversed: 115  ·  Baseline continuation: **41.0%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (2/10)
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `ladder_total_atr_bucket = (-inf, 1.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
- **17.6%** (3/17)
   - `start_dist_ema50_atr_bucket ≠ (1.0, inf]`
   - `ladder_total_atr_bucket = (2.5, inf]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
- **15.4%** (2/13)
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `ladder_total_atr_bucket ≠ (-inf, 1.0]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
- **10.0%** (1/10)
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `ladder_total_atr_bucket = (-inf, 1.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`

### 📊 NDX.INDX/15m · ALL EVENTS
- Events: 3851  ·  Baseline continuation: **46.2%**

  - 🟢 **87.9%** (51/58)
      - `type = bearish_OB`
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **79.2%** (42/53)
      - `type = bearish_OB`
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **74.0%** (154/208)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **70.6%** (12/17)
      - `type = bearish_OB`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **27.5%** (14/51)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **12.1%** (4/33)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/15m · BOS_bearish
- Events: 79  ·  Baseline continuation: **25.3%**

  - 🔴 **28.6%** (6/21)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **8.7%** (2/23)
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 NDX.INDX/15m · BOS_bullish
- Events: 84  ·  Baseline continuation: **21.4%**

  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **18.8%** (3/16)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 NDX.INDX/15m · CHoCH_bearish
- Events: 111  ·  Baseline continuation: **43.2%**

  - 🟢 **83.3%** (10/12)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **5.6%** (1/18)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 NDX.INDX/15m · CHoCH_bullish
- Events: 111  ·  Baseline continuation: **40.5%**

  - 🔴 **25.0%** (3/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🔴 **6.7%** (1/15)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/15m · bearish
- Events: 523  ·  Baseline continuation: **44.6%**

  - 🟢 **91.7%** (11/12)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **70.6%** (24/34)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **25.0%** (3/12)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **11.1%** (2/18)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **9.4%** (3/32)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
      - `dow = Wed`

### 📊 NDX.INDX/15m · bearish_OB
- Events: 440  ·  Baseline continuation: **64.8%**

  - 🟢 **95.7%** (22/23)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **91.7%** (11/12)
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **90.0%** (18/20)
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`
  - 🟢 **87.0%** (20/23)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **75.0%** (9/12)
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/15m · breakdown
- Events: 277  ·  Baseline continuation: **44.0%**

  - 🟢 **81.8%** (9/11)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **75.0%** (9/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Tue`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **20.6%** (7/34)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
  - 🔴 **12.5%** (2/16)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/15m · breakout_up
- Events: 332  ·  Baseline continuation: **39.2%**

  - 🟢 **85.7%** (18/21)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **28.6%** (4/14)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **21.3%** (10/47)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **12.5%** (2/16)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Thu`
  - 🔴 **0.0%** (0/14)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`

### 📊 NDX.INDX/15m · bullish
- Events: 588  ·  Baseline continuation: **42.2%**

  - 🟢 **75.0%** (15/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **17.6%** (3/17)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
  - 🔴 **15.2%** (5/33)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **10.0%** (1/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/15m · bullish_OB
- Events: 439  ·  Baseline continuation: **62.0%**

  - 🟢 **88.9%** (24/27)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **76.9%** (50/65)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **73.0%** (65/89)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
  - 🟢 **71.8%** (28/39)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **29.4%** (5/17)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Mon`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/15m · engulfing_bear
- Events: 218  ·  Baseline continuation: **35.8%**

  - 🔴 **25.0%** (4/16)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **12.5%** (2/16)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **9.1%** (1/11)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **0.0%** (0/16)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 NDX.INDX/15m · engulfing_bull
- Events: 193  ·  Baseline continuation: **36.8%**

  - 🔴 **26.7%** (4/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **17.4%** (4/23)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 NDX.INDX/15m · hammer
- Events: 252  ·  Baseline continuation: **46.8%**

  - 🟢 **85.7%** (12/14)
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🟢 **75.0%** (9/12)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **20.0%** (5/25)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/15m · shooting_star
- Events: 204  ·  Baseline continuation: **45.6%**

  - 🔴 **14.3%** (3/21)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`

---

## NDX.INDX · 30m
- Candles: **3987**  ·  Swing pivots: 488  ·  FVG: 950
- CHoCH/BOS events: 338  ·  Order Blocks: 721
- Trend Ladders detected: 228  ·  Candle patterns: 1131  ·  Breakouts: 534

### S/R Cluster Seviyeleri (top 8)
- 29540.6178 (touches: **287**, strong)
- 24109.3792 (touches: **48**, strong)
- 26685.4867 (touches: **15**, strong)
- 27025.1909 (touches: **11**, strong)
- 23812.0875 (touches: **8**, strong)
- 27196.7 (touches: **8**, strong)
- 25067.6286 (touches: **7**, strong)
- 24776.9333 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (228 ladder)
- Continued: 99  ·  Reversed: 83  ·  Baseline continuation: **43.4%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **27.3%** (3/11)
   - `before_rsi_last_bucket ≠ (70.0, inf]`
   - `start_dist_ema50_atr_bucket = (-1.0, 0.0]`
   - `before_volz_avg_bucket ≠ (-0.5, 0.5]`
- **20.0%** (3/15)
   - `before_rsi_last_bucket = (70.0, inf]`

### 📊 NDX.INDX/30m · ALL EVENTS
- Events: 3265  ·  Baseline continuation: **46.8%**

  - 🟢 **100.0%** (24/24)
      - `type = bullish_OB`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **81.1%** (30/37)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🟢 **75.0%** (129/172)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **73.1%** (19/26)
      - `type = bullish_OB`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **21.0%** (17/81)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow ≠ Tue`
      - `type = BOS_bullish`

### 📊 NDX.INDX/30m · BOS_bearish
- Events: 57  ·  Baseline continuation: **24.6%**

  - 🔴 **18.2%** (2/11)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **10.5%** (2/19)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/30m · BOS_bullish
- Events: 90  ·  Baseline continuation: **22.2%**

  - 🔴 **27.3%** (3/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **25.0%** (5/20)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **13.3%** (2/15)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **0.0%** (0/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 NDX.INDX/30m · CHoCH_bearish
- Events: 94  ·  Baseline continuation: **36.2%**

  - 🔴 **22.2%** (4/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **14.3%** (2/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/30m · CHoCH_bullish
- Events: 94  ·  Baseline continuation: **43.6%**

  - 🟢 **90.0%** (9/10)
      - `adx_b = (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **12.5%** (2/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/30m · bearish
- Events: 408  ·  Baseline continuation: **40.4%**

  - 🟢 **84.6%** (11/13)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **80.0%** (8/10)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **78.6%** (11/14)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **0.0%** (0/22)
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Tue`
  - 🔴 **0.0%** (0/12)
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 NDX.INDX/30m · bearish_OB
- Events: 368  ·  Baseline continuation: **62.5%**

  - 🟢 **87.9%** (51/58)
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
  - 🟢 **86.7%** (13/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **80.0%** (12/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **76.9%** (20/26)
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **70.0%** (7/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 NDX.INDX/30m · breakdown
- Events: 203  ·  Baseline continuation: **42.4%**

  - 🔴 **22.2%** (4/18)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **20.0%** (2/10)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **15.8%** (3/19)
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **5.3%** (1/19)
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/30m · breakout_up
- Events: 326  ·  Baseline continuation: **47.5%**

  - 🟢 **88.9%** (16/18)
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **72.4%** (21/29)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`

### 📊 NDX.INDX/30m · bullish
- Events: 539  ·  Baseline continuation: **46.0%**

  - 🟢 **100.0%** (11/11)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **80.0%** (16/20)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`
  - 🟢 **75.0%** (12/16)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **24.4%** (19/78)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`

### 📊 NDX.INDX/30m · bullish_OB
- Events: 353  ·  Baseline continuation: **66.9%**

  - 🟢 **100.0%** (24/24)
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **90.0%** (9/10)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **84.6%** (11/13)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **83.3%** (10/12)
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **79.3%** (23/29)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`

### 📊 NDX.INDX/30m · engulfing_bear
- Events: 199  ·  Baseline continuation: **40.2%**

  - 🟢 **80.0%** (8/10)
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **71.4%** (10/14)
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **14.3%** (2/14)
      - `dow ≠ Fri`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/30m · engulfing_bull
- Events: 163  ·  Baseline continuation: **42.3%**

  - 🟢 **75.0%** (12/16)
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **27.8%** (5/18)
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Wed`
  - 🔴 **0.0%** (0/16)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/30m · hammer
- Events: 214  ·  Baseline continuation: **40.7%**

  - 🟢 **71.4%** (10/14)
      - `rsi_b = (70.0, inf]`
  - 🔴 **29.1%** (16/55)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **20.0%** (3/15)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 NDX.INDX/30m · shooting_star
- Events: 157  ·  Baseline continuation: **39.5%**

  - 🔴 **25.0%** (3/12)
      - `adx_b = (25.0, inf]`
      - `dow = Tue`
  - 🔴 **22.6%** (7/31)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **13.3%** (2/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow = Fri`

---

## NDX.INDX · 1h
- Candles: **5257**  ·  Swing pivots: 608  ·  FVG: 1030
- CHoCH/BOS events: 411  ·  Order Blocks: 974
- Trend Ladders detected: 252  ·  Candle patterns: 1500  ·  Breakouts: 632

### S/R Cluster Seviyeleri (top 8)
- 25088.9092 (touches: **352**, strong)
- 29589.8754 (touches: **181**, strong)
- 26242.4234 (touches: **26**, strong)
- 26723.5571 (touches: **7**, strong)
- 27008.6297 (touches: **6**, strong)
- 27394.28 (touches: **5**, strong)
- 23795.35 (touches: **4**, moderate)
- 27199.2993 (touches: **4**, moderate)

### 🪜 Trend Ladder Analizi (252 ladder)
- Continued: 94  ·  Reversed: 110  ·  Baseline continuation: **37.3%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **21.4%** (3/14)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `start_dist_ema50_atr_bucket ≠ (-1.0, 0.0]`
   - `before_volz_avg_bucket ≠ (-0.5, 0.5]`
- **16.7%** (2/12)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`
- **0.0%** (0/14)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`

### 📊 NDX.INDX/1h · ALL EVENTS
- Events: 3967  ·  Baseline continuation: **45.2%**

  - 🟢 **94.1%** (16/17)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **91.3%** (42/46)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **85.4%** (35/41)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **77.8%** (14/18)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **77.6%** (83/107)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.6%** (21/82)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type ≠ BOS_bullish`
      - `type = BOS_bearish`
  - 🔴 **23.6%** (17/72)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **8.6%** (3/35)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/1h · BOS_bearish
- Events: 82  ·  Baseline continuation: **25.6%**

  - 🔴 **23.1%** (3/13)
      - `dow ≠ Thu`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **14.3%** (3/21)
      - `dow ≠ Thu`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **5.9%** (1/17)
      - `dow ≠ Thu`
      - `rsi_b = (-inf, 30.0]`

### 📊 NDX.INDX/1h · BOS_bullish
- Events: 107  ·  Baseline continuation: **18.7%**

  - 🔴 **30.0%** (3/10)
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **20.0%** (2/10)
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **15.4%** (2/13)
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **10.5%** (2/19)
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 NDX.INDX/1h · CHoCH_bearish
- Events: 109  ·  Baseline continuation: **48.6%**

  - 🟢 **84.6%** (11/13)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **70.0%** (7/10)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `dow = Mon`
  - 🔴 **14.3%** (2/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`

### 📊 NDX.INDX/1h · CHoCH_bullish
- Events: 110  ·  Baseline continuation: **37.3%**

  - 🟢 **84.6%** (11/13)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **29.4%** (5/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **28.6%** (6/21)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **10.5%** (2/19)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/1h · bearish
- Events: 448  ·  Baseline continuation: **43.1%**

  - 🟢 **77.8%** (14/18)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `dow = Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **28.6%** (4/14)
      - `dow = Mon`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **22.2%** (4/18)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **20.8%** (10/48)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow ≠ Thu`
  - 🔴 **0.0%** (0/18)
      - `dow = Mon`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/1h · bearish_OB
- Events: 529  ·  Baseline continuation: **62.6%**

  - 🟢 **92.9%** (13/14)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **92.3%** (12/13)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **82.9%** (29/35)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
  - 🟢 **74.0%** (37/50)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 NDX.INDX/1h · breakdown
- Events: 247  ·  Baseline continuation: **34.0%**

  - 🟢 **82.4%** (14/17)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
  - 🔴 **29.2%** (7/24)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **23.1%** (12/52)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **13.3%** (2/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`
  - 🔴 **10.0%** (1/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **0.0%** (0/19)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/1h · breakout_up
- Events: 375  ·  Baseline continuation: **33.9%**

  - 🟢 **76.9%** (10/13)
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **29.6%** (8/27)
      - `dow ≠ Tue`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **22.0%** (11/50)
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **17.4%** (8/46)
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **12.2%** (5/41)
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/1h · bullish
- Events: 576  ·  Baseline continuation: **41.5%**

  - 🟢 **90.9%** (10/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **88.9%** (16/18)
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **28.0%** (7/25)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **21.1%** (32/152)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **0.0%** (0/15)
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b = (70.0, inf]`

### 📊 NDX.INDX/1h · bullish_OB
- Events: 445  ·  Baseline continuation: **67.6%**

  - 🟢 **100.0%** (13/13)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **94.1%** (16/17)
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **93.3%** (28/30)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **87.9%** (29/33)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **85.7%** (18/21)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`

### 📊 NDX.INDX/1h · engulfing_bear
- Events: 227  ·  Baseline continuation: **41.9%**

  - 🟢 **80.0%** (12/15)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (6/24)
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **16.7%** (3/18)
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **9.1%** (1/11)
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/1h · engulfing_bull
- Events: 237  ·  Baseline continuation: **43.9%**

  - 🟢 **71.4%** (10/14)
      - `dow ≠ Fri`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🔴 **29.4%** (5/17)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Fri`
      - `dow = Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Fri`
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 NDX.INDX/1h · hammer
- Events: 275  ·  Baseline continuation: **38.2%**

  - 🔴 **16.1%** (5/31)
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **0.0%** (0/10)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`

### 📊 NDX.INDX/1h · shooting_star
- Events: 200  ·  Baseline continuation: **40.5%**

  - 🔴 **29.0%** (9/31)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (2/10)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Mon`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **7.7%** (1/13)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`

---

## GDAXI.INDX · 5m
- Candles: **10000**  ·  Swing pivots: 1301  ·  FVG: 2333
- CHoCH/BOS events: 912  ·  Order Blocks: 1681
- Trend Ladders detected: 133  ·  Candle patterns: 2165  ·  Breakouts: 1204

### S/R Cluster Seviyeleri (top 8)
- 24918.5752 (touches: **1107**, strong)
- 25814.7322 (touches: **58**, strong)
- 24217.5924 (touches: **20**, strong)
- 25719.3759 (touches: **17**, strong)
- 24425.3116 (touches: **13**, strong)
- 25572.496 (touches: **10**, strong)
- 24463.825 (touches: **8**, strong)
- 24119.4 (touches: **7**, strong)

### 🪜 Trend Ladder Analizi (133 ladder)
- Continued: 42  ·  Reversed: 60  ·  Baseline continuation: **31.6%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **27.7%** (13/47)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
   - `ladder_slope_atr_bucket ≠ (0.2, 0.5]`
- **23.1%** (3/13)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
- **20.0%** (3/15)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`
   - `before_volz_avg_bucket = (-inf, -0.5]`
- **11.1%** (2/18)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
   - `ladder_slope_atr_bucket = (0.2, 0.5]`

### 📊 GDAXI.INDX/5m · ALL EVENTS
- Events: 7312  ·  Baseline continuation: **44.5%**

  - 🟢 **78.4%** (203/259)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **74.0%** (370/500)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
  - 🟢 **71.0%** (44/62)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **70.6%** (60/85)
      - `type = bullish_OB`
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **70.0%** (145/207)
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **28.9%** (11/38)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `dow = Thu`
  - 🔴 **28.6%** (12/42)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **21.9%** (49/224)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type ≠ BOS_bullish`
      - `type = BOS_bearish`
  - 🔴 **12.4%** (16/129)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `dow ≠ Thu`

### 📊 GDAXI.INDX/5m · BOS_bearish
- Events: 224  ·  Baseline continuation: **21.9%**

  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **25.0%** (19/76)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
      - `dow = Wed`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.4%** (2/13)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 GDAXI.INDX/5m · BOS_bullish
- Events: 167  ·  Baseline continuation: **16.2%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.9%** (10/63)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **9.1%** (1/11)
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/16)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Thu`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **0.0%** (0/10)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/5m · CHoCH_bearish
- Events: 258  ·  Baseline continuation: **48.8%**

  - 🟢 **85.7%** (18/21)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **71.2%** (47/66)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
  - 🔴 **28.6%** (4/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **22.6%** (7/31)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **0.0%** (0/15)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/5m · CHoCH_bullish
- Events: 258  ·  Baseline continuation: **37.2%**

  - 🟢 **82.4%** (14/17)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (11/44)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **16.9%** (11/65)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **0.0%** (0/19)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/5m · bearish
- Events: 1160  ·  Baseline continuation: **40.5%**

  - 🔴 **26.7%** (8/30)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Thu`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **21.4%** (3/14)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (-inf, 0.05]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **15.4%** (2/13)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Tue`
  - 🔴 **8.3%** (3/36)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · bearish_OB
- Events: 848  ·  Baseline continuation: **66.5%**

  - 🟢 **90.6%** (29/32)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🟢 **83.3%** (10/12)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **81.2%** (13/16)
      - `dow = Tue`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **80.0%** (8/10)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.0%** (237/316)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
  - 🔴 **25.0%** (3/12)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **16.7%** (3/18)
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 GDAXI.INDX/5m · breakdown
- Events: 609  ·  Baseline continuation: **37.3%**

  - 🟢 **82.4%** (14/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (-inf, 0.05]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **22.6%** (14/62)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **21.9%** (7/32)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **6.9%** (2/29)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/15)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · breakout_up
- Events: 582  ·  Baseline continuation: **35.4%**

  - 🔴 **28.6%** (12/42)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **26.3%** (5/19)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **21.4%** (6/28)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **10.5%** (2/19)
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · bullish
- Events: 1159  ·  Baseline continuation: **37.1%**

  - 🟢 **73.3%** (11/15)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **20.9%** (24/115)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **16.7%** (2/12)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (70.0, inf]`
  - 🔴 **16.1%** (5/31)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **6.9%** (2/29)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/5m · bullish_OB
- Events: 832  ·  Baseline continuation: **68.1%**

  - 🟢 **94.4%** (17/18)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **82.4%** (42/51)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **81.8%** (45/55)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **80.3%** (49/61)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Tue`
      - `dow = Thu`
  - 🟢 **74.4%** (32/43)
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b = (-inf, 0.05]`
      - `vol_z_b ≠ (-inf, -0.5]`

### 📊 GDAXI.INDX/5m · engulfing_bear
- Events: 256  ·  Baseline continuation: **40.2%**

  - 🟢 **80.0%** (8/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
      - `adx_b = (-inf, 18.0]`
      - `dow = Wed`
  - 🟢 **73.3%** (11/15)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Thu`
  - 🔴 **22.9%** (8/35)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **17.6%** (3/17)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
  - 🔴 **11.8%** (2/17)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`

### 📊 GDAXI.INDX/5m · engulfing_bull
- Events: 216  ·  Baseline continuation: **37.5%**

  - 🔴 **26.5%** (9/34)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **25.0%** (3/12)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/5m · hammer
- Events: 371  ·  Baseline continuation: **37.7%**

  - 🟢 **75.0%** (12/16)
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **23.8%** (29/122)
      - `dow ≠ Thu`
      - `dow ≠ Sat`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
  - 🔴 **0.0%** (0/10)
      - `dow ≠ Thu`
      - `dow = Sat`

### 📊 GDAXI.INDX/5m · shooting_star
- Events: 372  ·  Baseline continuation: **44.4%**

  - 🟢 **75.0%** (9/12)
      - `adx_b = (25.0, inf]`
      - `dow = Fri`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **26.7%** (4/15)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
  - 🔴 **20.0%** (3/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **7.1%** (1/14)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`

---

## GDAXI.INDX · 15m
- Candles: **4679**  ·  Swing pivots: 548  ·  FVG: 1039
- CHoCH/BOS events: 405  ·  Order Blocks: 823
- Trend Ladders detected: 268  ·  Candle patterns: 1177  ·  Breakouts: 557

### S/R Cluster Seviyeleri (top 8)
- 24859.446 (touches: **424**, strong)
- 24224.9119 (touches: **42**, strong)
- 25838.2308 (touches: **13**, strong)
- 25719.65 (touches: **10**, strong)
- 24070.9 (touches: **8**, strong)
- 23927.2667 (touches: **6**, strong)
- 24003.1167 (touches: **6**, strong)
- 25376.9667 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (268 ladder)
- Continued: 110  ·  Reversed: 105  ·  Baseline continuation: **41.0%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **28.0%** (7/25)
   - `before_rsi_last_bucket = (30.0, 50.0]`
   - `before_rsi_avg_bucket ≠ (30.0, 50.0]`
   - `before_volz_avg_bucket ≠ (0.5, inf]`
- **11.1%** (2/18)
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`

### 📊 GDAXI.INDX/15m · ALL EVENTS
- Events: 3513  ·  Baseline continuation: **46.4%**

  - 🟢 **95.0%** (19/20)
      - `type = bearish_OB`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🟢 **83.3%** (30/36)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Thu`
  - 🟢 **78.6%** (55/70)
      - `type = bearish_OB`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **78.1%** (25/32)
      - `type = bearish_OB`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **74.5%** (35/47)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **9.1%** (3/33)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `vol_z_b = (0.5, inf]`
      - `type = BOS_bullish`

### 📊 GDAXI.INDX/15m · BOS_bearish
- Events: 85  ·  Baseline continuation: **28.2%**

  - 🔴 **19.0%** (4/21)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **12.5%** (3/24)
      - `rsi_b = (-inf, 30.0]`

### 📊 GDAXI.INDX/15m · BOS_bullish
- Events: 66  ·  Baseline continuation: **18.2%**

  - 🔴 **20.0%** (4/20)
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **0.0%** (0/13)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (50.0, 70.0]`

### 📊 GDAXI.INDX/15m · CHoCH_bearish
- Events: 126  ·  Baseline continuation: **46.8%**

  - 🟢 **85.7%** (18/21)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **22.7%** (5/22)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Mon`

### 📊 GDAXI.INDX/15m · CHoCH_bullish
- Events: 125  ·  Baseline continuation: **36.8%**

  - 🟢 **80.0%** (8/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **18.8%** (3/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/15m · bearish
- Events: 531  ·  Baseline continuation: **42.0%**

  - 🔴 **28.6%** (4/14)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **23.1%** (6/26)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **23.1%** (3/13)
      - `adx_b = (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **17.6%** (3/17)
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Thu`
  - 🔴 **14.7%** (5/34)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 GDAXI.INDX/15m · bearish_OB
- Events: 429  ·  Baseline continuation: **67.1%**

  - 🟢 **100.0%** (10/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **83.3%** (10/12)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **78.9%** (15/19)
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **78.6%** (55/70)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Wed`
      - `rsi_b = (-inf, 30.0]`

### 📊 GDAXI.INDX/15m · breakdown
- Events: 287  ·  Baseline continuation: **41.1%**

  - 🔴 **30.0%** (9/30)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **15.0%** (3/20)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **12.5%** (2/16)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`

### 📊 GDAXI.INDX/15m · breakout_up
- Events: 264  ·  Baseline continuation: **41.7%**

  - 🟢 **92.3%** (12/13)
      - `dow = Tue`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **25.7%** (18/70)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`
  - 🔴 **10.0%** (1/10)
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **7.7%** (1/13)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`

### 📊 GDAXI.INDX/15m · bullish
- Events: 505  ·  Baseline continuation: **39.8%**

  - 🟢 **71.9%** (23/32)
      - `dow = Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **25.0%** (3/12)
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `dow = Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **21.3%** (10/47)
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **7.7%** (1/13)
      - `dow = Tue`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/15m · bullish_OB
- Events: 394  ·  Baseline continuation: **64.2%**

  - 🟢 **100.0%** (13/13)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🟢 **100.0%** (11/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **91.7%** (11/12)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🟢 **90.9%** (10/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **85.0%** (17/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/15m · engulfing_bear
- Events: 157  ·  Baseline continuation: **47.1%**

  - 🟢 **100.0%** (11/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **90.9%** (10/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **78.6%** (11/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **26.1%** (6/23)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Mon`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/10)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`

### 📊 GDAXI.INDX/15m · engulfing_bull
- Events: 123  ·  Baseline continuation: **36.6%**

  - 🟢 **80.0%** (8/10)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **18.2%** (6/33)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`

### 📊 GDAXI.INDX/15m · hammer
- Events: 222  ·  Baseline continuation: **41.0%**

  - 🟢 **84.2%** (16/19)
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (14/56)
      - `dow ≠ Thu`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Mon`
  - 🔴 **17.6%** (3/17)
      - `dow = Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.05, 0.15]`

### 📊 GDAXI.INDX/15m · shooting_star
- Events: 199  ·  Baseline continuation: **43.7%**

  - 🔴 **27.3%** (3/11)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (4/16)
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **25.0%** (4/16)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`

---

## GDAXI.INDX · 30m
- Candles: **3759**  ·  Swing pivots: 479  ·  FVG: 862
- CHoCH/BOS events: 341  ·  Order Blocks: 636
- Trend Ladders detected: 226  ·  Candle patterns: 1071  ·  Breakouts: 420

### S/R Cluster Seviyeleri (top 8)
- 24596.2194 (touches: **377**, strong)
- 22861.0813 (touches: **16**, strong)
- 22585.9692 (touches: **13**, strong)
- 23387.3429 (touches: **7**, strong)
- 25838.5714 (touches: **7**, strong)
- 22380.8 (touches: **6**, strong)
- 23003.55 (touches: **6**, strong)
- 23086.3 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (226 ladder)
- Continued: 96  ·  Reversed: 101  ·  Baseline continuation: **42.5%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **23.1%** (12/52)
   - `before_rsi_avg_bucket = (50.0, 70.0]`
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`
   - `ladder_slope_atr_bucket ≠ (0.2, 0.5]`
- **20.0%** (2/10)
   - `before_rsi_avg_bucket = (50.0, 70.0]`
   - `before_rsi_last_bucket = (30.0, 50.0]`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
- **17.6%** (3/17)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
   - `before_rsi_last_bucket = (30.0, 50.0]`

### 📊 GDAXI.INDX/30m · ALL EVENTS
- Events: 2914  ·  Baseline continuation: **47.5%**

  - 🟢 **90.9%** (50/55)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **73.1%** (128/175)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **72.4%** (144/199)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **23.5%** (4/17)
      - `type = bullish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`
  - 🔴 **15.6%** (10/64)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 GDAXI.INDX/30m · BOS_bearish
- Events: 68  ·  Baseline continuation: **27.9%**

  - 🔴 **20.0%** (2/10)
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
  - 🔴 **17.6%** (3/17)
      - `dow ≠ Mon`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **0.0%** (0/15)
      - `dow = Mon`

### 📊 GDAXI.INDX/30m · BOS_bullish
- Events: 79  ·  Baseline continuation: **19.0%**

  - 🔴 **26.7%** (4/15)
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **25.0%** (4/16)
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **8.3%** (2/24)
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/12)
      - `dow = Fri`

### 📊 GDAXI.INDX/30m · CHoCH_bearish
- Events: 95  ·  Baseline continuation: **48.4%**

  - 🟢 **90.0%** (9/10)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **70.0%** (7/10)
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **26.3%** (5/19)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
  - 🔴 **18.8%** (3/16)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/30m · CHoCH_bullish
- Events: 97  ·  Baseline continuation: **40.2%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/10)
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/30m · bearish
- Events: 414  ·  Baseline continuation: **39.6%**

  - 🔴 **28.6%** (12/42)
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **24.3%** (9/37)
      - `dow = Mon`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **21.1%** (4/19)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **0.0%** (0/13)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 GDAXI.INDX/30m · bearish_OB
- Events: 324  ·  Baseline continuation: **65.4%**

  - 🟢 **85.7%** (24/28)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
  - 🟢 **84.8%** (28/33)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
  - 🟢 **79.2%** (19/24)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 GDAXI.INDX/30m · breakdown
- Events: 203  ·  Baseline continuation: **41.4%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Mon`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **28.6%** (12/42)
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **21.1%** (4/19)
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **6.2%** (1/16)
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/30m · breakout_up
- Events: 214  ·  Baseline continuation: **48.1%**

  - 🟢 **70.0%** (14/20)
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `dow = Mon`

### 📊 GDAXI.INDX/30m · bullish
- Events: 445  ·  Baseline continuation: **46.5%**

  - 🔴 **25.0%** (3/12)
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **16.7%** (2/12)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/11)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/30m · bullish_OB
- Events: 312  ·  Baseline continuation: **70.5%**

  - 🟢 **100.0%** (21/21)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **88.5%** (23/26)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **85.3%** (29/34)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **75.0%** (9/12)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **70.5%** (105/149)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **23.5%** (4/17)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`

### 📊 GDAXI.INDX/30m · engulfing_bear
- Events: 164  ·  Baseline continuation: **45.7%**

  - 🟢 **75.0%** (27/36)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **26.7%** (4/15)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`

### 📊 GDAXI.INDX/30m · engulfing_bull
- Events: 154  ·  Baseline continuation: **39.6%**

  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **15.8%** (3/19)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Fri`
  - 🔴 **13.0%** (3/23)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 GDAXI.INDX/30m · hammer
- Events: 187  ·  Baseline continuation: **37.4%**

  - 🟢 **75.0%** (21/28)
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **27.3%** (6/22)
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
      - `dow = Tue`
  - 🔴 **23.5%** (4/17)
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow = Fri`
  - 🔴 **15.8%** (3/19)
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
  - 🔴 **5.3%** (1/19)
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 GDAXI.INDX/30m · shooting_star
- Events: 158  ·  Baseline continuation: **43.0%**

  - 🟢 **83.3%** (15/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **23.5%** (4/17)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **14.3%** (2/14)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **0.0%** (0/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`

---

## GDAXI.INDX · 1h
- Candles: **4651**  ·  Swing pivots: 576  ·  FVG: 1076
- CHoCH/BOS events: 409  ·  Order Blocks: 864
- Trend Ladders detected: 244  ·  Candle patterns: 1379  ·  Breakouts: 542

### S/R Cluster Seviyeleri (top 8)
- 24504.5373 (touches: **492**, strong)
- 23363.2571 (touches: **28**, strong)
- 23089.3222 (touches: **18**, strong)
- 22801.16 (touches: **5**, strong)
- 25461.778 (touches: **5**, strong)
- 22717.025 (touches: **4**, moderate)
- 22620.8 (touches: **3**, moderate)
- 21922.55 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (244 ladder)
- Continued: 107  ·  Reversed: 90  ·  Baseline continuation: **43.9%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **78.6%** (11/14)
   - `before_rsi_avg_bucket = (50.0, 70.0]`
   - `ladder_total_atr_bucket = (2.5, inf]`
   - `before_rsi_last_bucket = (30.0, 50.0]`
- **73.3%** (11/15)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `ladder_total_atr_bucket = (-inf, 1.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **25.0%** (13/52)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `ladder_total_atr_bucket ≠ (-inf, 1.0]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`

### 📊 GDAXI.INDX/1h · ALL EVENTS
- Events: 3747  ·  Baseline continuation: **46.3%**

  - 🟢 **81.2%** (13/16)
      - `type = bearish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **81.2%** (65/80)
      - `type = bearish_OB`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **71.6%** (154/215)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
  - 🟢 **70.4%** (38/54)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.9%** (7/44)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/1h · BOS_bearish
- Events: 81  ·  Baseline continuation: **24.7%**

  - 🔴 **29.4%** (5/17)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **15.4%** (2/13)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **6.2%** (1/16)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 GDAXI.INDX/1h · BOS_bullish
- Events: 113  ·  Baseline continuation: **28.3%**

  - 🔴 **27.6%** (8/29)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **5.6%** (1/18)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/1h · CHoCH_bearish
- Events: 107  ·  Baseline continuation: **48.6%**

  - 🟢 **73.7%** (14/19)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/1h · CHoCH_bullish
- Events: 108  ·  Baseline continuation: **41.7%**

  - 🟢 **77.8%** (14/18)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
      - `dow ≠ Wed`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **25.0%** (3/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/1h · bearish
- Events: 509  ·  Baseline continuation: **38.5%**

  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **28.0%** (7/25)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **25.0%** (4/16)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **13.5%** (5/37)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **6.5%** (3/46)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow ≠ Fri`

### 📊 GDAXI.INDX/1h · bearish_OB
- Events: 468  ·  Baseline continuation: **65.4%**

  - 🟢 **91.7%** (11/12)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Fri`
  - 🟢 **85.7%** (12/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **84.6%** (22/26)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Fri`
  - 🟢 **78.2%** (43/55)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **74.2%** (23/31)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/1h · breakdown
- Events: 247  ·  Baseline continuation: **42.5%**

  - 🟢 **80.0%** (16/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **17.6%** (6/34)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **7.7%** (1/13)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/1h · breakout_up
- Events: 291  ·  Baseline continuation: **42.3%**

  - 🔴 **29.4%** (5/17)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **27.8%** (10/36)
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Fri`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **21.4%** (3/14)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/1h · bullish
- Events: 562  ·  Baseline continuation: **43.2%**

  - 🔴 **25.0%** (5/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **16.7%** (2/12)
      - `atr_pct_b = (0.05, 0.15]`

### 📊 GDAXI.INDX/1h · bullish_OB
- Events: 396  ·  Baseline continuation: **64.6%**

  - 🟢 **88.9%** (16/18)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **81.8%** (9/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **76.3%** (116/152)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 GDAXI.INDX/1h · engulfing_bear
- Events: 244  ·  Baseline continuation: **43.0%**

  - 🟢 **80.0%** (8/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **70.0%** (7/10)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Thu`
  - 🔴 **28.6%** (4/14)
      - `adx_b = (25.0, inf]`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **20.0%** (2/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Wed`
      - `dow = Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **16.7%** (2/12)
      - `adx_b = (25.0, inf]`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **7.7%** (1/13)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`

### 📊 GDAXI.INDX/1h · engulfing_bull
- Events: 212  ·  Baseline continuation: **46.2%**

  - 🟢 **76.5%** (13/17)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **25.0%** (3/12)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `dow = Thu`
  - 🔴 **9.1%** (1/11)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`

### 📊 GDAXI.INDX/1h · hammer
- Events: 220  ·  Baseline continuation: **38.2%**

  - 🟢 **72.7%** (8/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **30.0%** (6/20)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **15.4%** (2/13)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/1h · shooting_star
- Events: 189  ·  Baseline continuation: **36.5%**

  - 🟢 **75.0%** (9/12)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b = (70.0, inf]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `dow = Tue`
      - `adx_b = (-inf, 18.0]`

---

## USOIL.FOREX · 5m
- Candles: **10000**  ·  Swing pivots: 1385  ·  FVG: 2329
- CHoCH/BOS events: 976  ·  Order Blocks: 1706
- Trend Ladders detected: 100  ·  Candle patterns: 2030  ·  Breakouts: 1097

### S/R Cluster Seviyeleri (top 8)
- 71.5824 (touches: **648**, strong)
- 80.4794 (touches: **251**, strong)
- 76.963 (touches: **112**, strong)
- 92.8582 (touches: **52**, strong)
- 95.1489 (touches: **37**, strong)
- 90.2421 (touches: **21**, strong)
- 97.9952 (touches: **20**, strong)
- 91.2568 (touches: **19**, strong)

### 🪜 Trend Ladder Analizi (100 ladder)
- Continued: 43  ·  Reversed: 44  ·  Baseline continuation: **43.0%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **72.7%** (8/11)
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (2/12)
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`

### 📊 USOIL.FOREX/5m · ALL EVENTS
- Events: 7210  ·  Baseline continuation: **46.7%**

  - 🟢 **79.8%** (134/168)
      - `type = bearish_OB`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **72.6%** (304/419)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **70.9%** (317/447)
      - `type = bearish_OB`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
  - 🔴 **25.7%** (94/366)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `rsi_b = (70.0, inf]`
      - `type ≠ shooting_star`
  - 🔴 **25.0%** (60/240)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `rsi_b ≠ (70.0, inf]`
      - `type = BOS_bearish`
  - 🔴 **20.0%** (6/30)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Wed`

### 📊 USOIL.FOREX/5m · BOS_bearish
- Events: 240  ·  Baseline continuation: **25.0%**

  - 🔴 **22.6%** (19/84)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **19.0%** (4/21)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **17.6%** (3/17)
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **16.7%** (2/12)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 USOIL.FOREX/5m · BOS_bullish
- Events: 154  ·  Baseline continuation: **23.4%**

  - 🔴 **26.3%** (5/19)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **18.2%** (4/22)
      - `rsi_b = (70.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **10.0%** (2/20)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **0.0%** (0/10)
      - `rsi_b = (70.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 USOIL.FOREX/5m · CHoCH_bearish
- Events: 290  ·  Baseline continuation: **46.2%**

  - 🟢 **83.3%** (15/18)
      - `rsi_b ≠ (-inf, 30.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **29.2%** (19/65)
      - `rsi_b ≠ (-inf, 30.0]`
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **4.5%** (1/22)
      - `rsi_b = (-inf, 30.0]`

### 📊 USOIL.FOREX/5m · CHoCH_bullish
- Events: 291  ·  Baseline continuation: **40.2%**

  - 🟢 **100.0%** (10/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **87.5%** (14/16)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **19.2%** (5/26)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
  - 🔴 **15.0%** (9/60)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **0.0%** (0/17)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · bearish
- Events: 1202  ·  Baseline continuation: **44.1%**

  - 🟢 **81.2%** (26/32)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
  - 🟢 **72.7%** (8/11)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **29.0%** (36/124)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
  - 🔴 **10.7%** (3/28)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/5m · bearish_OB
- Events: 885  ·  Baseline continuation: **70.5%**

  - 🟢 **94.1%** (16/17)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Fri`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **82.4%** (14/17)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **82.4%** (14/17)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (30.0, 50.0]`

### 📊 USOIL.FOREX/5m · breakdown
- Events: 583  ·  Baseline continuation: **43.9%**

  - 🟢 **80.0%** (8/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🟢 **75.0%** (24/32)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Fri`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Mon`

### 📊 USOIL.FOREX/5m · breakout_up
- Events: 508  ·  Baseline continuation: **35.6%**

  - 🔴 **26.3%** (10/38)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **17.6%** (3/17)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.8%** (6/38)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **9.5%** (2/21)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Mon`
  - 🔴 **9.1%** (2/22)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/5m · bullish
- Events: 1116  ·  Baseline continuation: **40.5%**

  - 🔴 **25.0%** (13/52)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **17.6%** (3/17)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **12.5%** (2/16)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **12.5%** (2/16)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/5m · bullish_OB
- Events: 821  ·  Baseline continuation: **63.5%**

  - 🟢 **81.2%** (13/16)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **78.3%** (206/263)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow ≠ Thu`
  - 🟢 **77.8%** (28/36)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **71.4%** (25/35)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.3%** (3/29)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · engulfing_bear
- Events: 132  ·  Baseline continuation: **40.2%**

  - 🔴 **25.0%** (3/12)
      - `dow ≠ Mon`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🔴 **12.5%** (2/16)
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/5m · engulfing_bull
- Events: 110  ·  Baseline continuation: **46.4%**

  - 🟢 **75.0%** (12/16)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **21.4%** (3/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow = Tue`
  - 🔴 **20.0%** (3/15)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`

### 📊 USOIL.FOREX/5m · hammer
- Events: 412  ·  Baseline continuation: **38.6%**

  - 🔴 **29.4%** (35/119)
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Tue`
  - 🔴 **24.1%** (7/29)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Fri`
  - 🔴 **10.0%** (1/10)
      - `adx_b = (25.0, inf]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **7.7%** (1/13)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`

### 📊 USOIL.FOREX/5m · shooting_star
- Events: 466  ·  Baseline continuation: **41.8%**

  - 🟢 **75.0%** (12/16)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Mon`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **29.4%** (5/17)
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **24.5%** (24/98)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`

---

## USOIL.FOREX · 15m
- Candles: **4709**  ·  Swing pivots: 627  ·  FVG: 967
- CHoCH/BOS events: 449  ·  Order Blocks: 826
- Trend Ladders detected: 241  ·  Candle patterns: 989  ·  Breakouts: 482

### S/R Cluster Seviyeleri (top 8)
- 73.7911 (touches: **129**, strong)
- 80.3632 (touches: **83**, strong)
- 94.8264 (touches: **73**, strong)
- 69.3874 (touches: **72**, strong)
- 101.9259 (touches: **50**, strong)
- 97.6556 (touches: **30**, strong)
- 91.5272 (touches: **26**, strong)
- 92.7893 (touches: **21**, strong)

### 🪜 Trend Ladder Analizi (241 ladder)
- Continued: 107  ·  Reversed: 89  ·  Baseline continuation: **44.4%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **74.1%** (20/27)
   - `ladder_total_atr_bucket = (1.0, 2.5]`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **15.0%** (3/20)
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · ALL EVENTS
- Events: 3232  ·  Baseline continuation: **46.9%**

  - 🟢 **87.5%** (28/32)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **79.5%** (31/39)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🟢 **78.2%** (43/55)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
  - 🟢 **77.4%** (24/31)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🟢 **72.2%** (122/169)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
  - 🔴 **17.2%** (5/29)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow = Wed`
      - `rsi_b = (70.0, inf]`

### 📊 USOIL.FOREX/15m · BOS_bearish
- Events: 97  ·  Baseline continuation: **23.7%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow = Thu`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **14.3%** (2/14)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🔴 **12.5%** (2/16)
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **7.7%** (1/13)
      - `dow = Thu`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/15m · BOS_bullish
- Events: 93  ·  Baseline continuation: **28.0%**

  - 🔴 **30.0%** (3/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **27.8%** (5/18)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.0%** (3/20)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **6.7%** (1/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/15m · CHoCH_bearish
- Events: 129  ·  Baseline continuation: **40.3%**

  - 🟢 **75.0%** (9/12)
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **29.2%** (7/24)
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/18)
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/15m · CHoCH_bullish
- Events: 129  ·  Baseline continuation: **41.9%**

  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Tue`
  - 🟢 **75.0%** (9/12)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **19.0%** (4/21)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/15m · bearish
- Events: 479  ·  Baseline continuation: **43.2%**

  - 🔴 **30.0%** (6/20)
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **14.3%** (4/28)
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **13.3%** (2/15)
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **0.0%** (0/10)
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Mon`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/15m · bearish_OB
- Events: 427  ·  Baseline continuation: **64.4%**

  - 🟢 **100.0%** (15/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **83.0%** (39/47)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **81.8%** (9/11)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`
  - 🟢 **80.0%** (8/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **75.0%** (18/24)
      - `adx_b = (25.0, inf]`
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (25.0, inf]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/15m · breakdown
- Events: 260  ·  Baseline continuation: **45.4%**

  - 🟢 **90.9%** (10/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **81.8%** (9/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **71.4%** (10/14)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🟢 **71.4%** (10/14)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **27.8%** (10/36)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **21.1%** (4/19)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow = Thu`
  - 🔴 **14.3%** (2/14)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`

### 📊 USOIL.FOREX/15m · breakout_up
- Events: 220  ·  Baseline continuation: **40.0%**

  - 🟢 **91.7%** (11/12)
      - `dow = Tue`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **30.0%** (12/40)
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **29.0%** (9/31)
      - `dow ≠ Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **5.0%** (1/20)
      - `dow ≠ Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 USOIL.FOREX/15m · bullish
- Events: 482  ·  Baseline continuation: **40.2%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Thu`
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **27.3%** (3/11)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **27.3%** (3/11)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **22.2%** (12/54)
      - `dow ≠ Thu`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.5%** (8/39)
      - `dow ≠ Thu`
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 USOIL.FOREX/15m · bullish_OB
- Events: 399  ·  Baseline continuation: **66.9%**

  - 🟢 **92.3%** (12/13)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **87.0%** (20/23)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **83.8%** (31/37)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
  - 🟢 **81.8%** (9/11)
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (-inf, 30.0]`
      - `dow = Thu`
  - 🟢 **81.8%** (9/11)
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/15m · engulfing_bear
- Events: 52  ·  Baseline continuation: **32.7%**

  - 🔴 **18.2%** (2/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **7.7%** (1/13)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/15m · engulfing_bull
- Events: 64  ·  Baseline continuation: **43.8%**

  - 🟢 **71.4%** (10/14)
      - `adx_b = (-inf, 18.0]`
  - 🔴 **14.3%** (2/14)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · hammer
- Events: 220  ·  Baseline continuation: **35.5%**

  - 🔴 **22.6%** (7/31)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **14.3%** (3/21)
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **13.3%** (4/30)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/15m · shooting_star
- Events: 181  ·  Baseline continuation: **48.6%**

  - 🟢 **80.0%** (20/25)
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **74.2%** (23/31)
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **28.6%** (4/14)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **16.7%** (4/24)
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **11.8%** (2/17)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.4, inf]`

---

## USOIL.FOREX · 30m
- Candles: **3959**  ·  Swing pivots: 495  ·  FVG: 811
- CHoCH/BOS events: 353  ·  Order Blocks: 685
- Trend Ladders detected: 204  ·  Candle patterns: 942  ·  Breakouts: 416

### S/R Cluster Seviyeleri (top 8)
- 95.5139 (touches: **233**, strong)
- 70.8373 (touches: **80**, strong)
- 103.8493 (touches: **46**, strong)
- 79.8274 (touches: **43**, strong)
- 75.6184 (touches: **23**, strong)
- 108.9148 (touches: **15**, strong)
- 107.0262 (touches: **13**, strong)
- 85.3322 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (204 ladder)
- Continued: 85  ·  Reversed: 83  ·  Baseline continuation: **41.7%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **70.6%** (12/17)
   - `before_rsi_last_bucket = (70.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **25.6%** (10/39)
   - `before_rsi_last_bucket ≠ (70.0, inf]`
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/30m · ALL EVENTS
- Events: 2787  ·  Baseline continuation: **48.5%**

  - 🟢 **93.8%** (15/16)
      - `type = bullish_OB`
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`
  - 🟢 **88.5%** (23/26)
      - `type = bullish_OB`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Mon`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **78.2%** (61/78)
      - `type = bullish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Tue`
  - 🟢 **76.0%** (76/100)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **25.7%** (28/109)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow = Mon`
      - `type = bullish`

### 📊 USOIL.FOREX/30m · BOS_bearish
- Events: 74  ·  Baseline continuation: **24.3%**

  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **15.4%** (2/13)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **7.1%** (1/14)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`

### 📊 USOIL.FOREX/30m · BOS_bullish
- Events: 70  ·  Baseline continuation: **25.7%**

  - 🔴 **23.5%** (4/17)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **8.3%** (1/12)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Mon`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **7.1%** (1/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`

### 📊 USOIL.FOREX/30m · CHoCH_bearish
- Events: 104  ·  Baseline continuation: **43.3%**

  - 🟢 **78.6%** (11/14)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **26.1%** (6/23)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
  - 🔴 **15.8%** (3/19)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`

### 📊 USOIL.FOREX/30m · CHoCH_bullish
- Events: 104  ·  Baseline continuation: **44.2%**

  - 🔴 **29.0%** (9/31)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b = (70.0, inf]`

### 📊 USOIL.FOREX/30m · bearish
- Events: 390  ·  Baseline continuation: **43.6%**

  - 🟢 **90.9%** (10/11)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🟢 **90.5%** (19/21)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
  - 🟢 **70.6%** (12/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **27.3%** (3/11)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `dow = Wed`
  - 🔴 **20.8%** (5/24)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`

### 📊 USOIL.FOREX/30m · bearish_OB
- Events: 333  ·  Baseline continuation: **63.7%**

  - 🟢 **94.1%** (16/17)
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🟢 **86.4%** (19/22)
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **84.1%** (37/44)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🟢 **73.3%** (11/15)
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **72.7%** (8/11)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **26.3%** (5/19)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · breakdown
- Events: 183  ·  Baseline continuation: **45.9%**

  - 🟢 **76.9%** (10/13)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **9.1%** (1/11)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **0.0%** (0/15)
      - `adx_b = (25.0, inf]`
      - `dow = Thu`

### 📊 USOIL.FOREX/30m · breakout_up
- Events: 231  ·  Baseline continuation: **49.8%**

  - 🟢 **92.3%** (12/13)
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **73.3%** (11/15)
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **10.0%** (1/10)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/30m · bullish
- Events: 418  ·  Baseline continuation: **41.4%**

  - 🔴 **30.0%** (3/10)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **28.6%** (12/42)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **20.0%** (3/15)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **18.8%** (3/16)
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **13.6%** (3/22)
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/30m · bullish_OB
- Events: 352  ·  Baseline continuation: **69.9%**

  - 🟢 **100.0%** (10/10)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🟢 **93.3%** (14/15)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Mon`
  - 🟢 **93.3%** (14/15)
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **84.2%** (16/19)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **71.9%** (41/57)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow ≠ Mon`

### 📊 USOIL.FOREX/30m · engulfing_bear
- Events: 80  ·  Baseline continuation: **38.8%**

  - 🟢 **70.0%** (7/10)
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **16.7%** (3/18)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/30m · engulfing_bull
- Events: 90  ·  Baseline continuation: **48.9%**

  - 🟢 **84.6%** (11/13)
      - `rsi_b = (70.0, inf]`
  - 🔴 **15.8%** (3/19)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · hammer
- Events: 191  ·  Baseline continuation: **44.5%**

  - 🔴 **26.1%** (6/23)
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **18.8%** (3/16)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/30m · shooting_star
- Events: 167  ·  Baseline continuation: **38.3%**

  - 🟢 **72.7%** (8/11)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Fri`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Fri`
      - `dow = Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **29.5%** (13/44)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`
  - 🔴 **28.6%** (4/14)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **22.2%** (4/18)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`

---

## USOIL.FOREX · 1h
- Candles: **2833**  ·  Swing pivots: 389  ·  FVG: 630
- CHoCH/BOS events: 265  ·  Order Blocks: 552
- Trend Ladders detected: 126  ·  Candle patterns: 825  ·  Breakouts: 290

### S/R Cluster Seviyeleri (top 8)
- 96.628 (touches: **187**, strong)
- 66.8214 (touches: **86**, strong)
- 77.0561 (touches: **32**, strong)
- 72.8882 (touches: **16**, strong)
- 86.9386 (touches: **14**, strong)
- 81.3304 (touches: **12**, strong)
- 74.6887 (touches: **11**, strong)
- 84.53 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (126 ladder)
- Continued: 58  ·  Reversed: 51  ·  Baseline continuation: **46.0%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **81.2%** (13/16)
   - `direction ≠ down`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **30.0%** (3/10)
   - `direction ≠ down`
   - `before_adx_avg_bucket = (25.0, inf]`
   - `before_rsi_last_bucket = (50.0, 70.0]`
- **30.0%** (3/10)
   - `direction = down`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
- **27.3%** (3/11)
   - `direction = down`
   - `start_dist_ema50_atr_bucket ≠ (1.0, inf]`
   - `start_dist_ema50_atr_bucket = (-1.0, 0.0]`
- **16.7%** (2/12)
   - `direction = down`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`

### 📊 USOIL.FOREX/1h · ALL EVENTS
- Events: 2200  ·  Baseline continuation: **44.8%**

  - 🟢 **85.7%** (36/42)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **77.8%** (49/63)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.4%** (43/57)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `dow = Fri`
  - 🔴 **17.1%** (6/35)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **16.3%** (8/49)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **11.1%** (2/18)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · BOS_bearish
- Events: 53  ·  Baseline continuation: **15.1%**

  - 🔴 **20.0%** (2/10)
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/20)
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · BOS_bullish
- Events: 49  ·  Baseline continuation: **16.3%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `dow = Mon`
  - 🔴 **6.7%** (1/15)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
  - 🔴 **0.0%** (0/12)
      - `dow = Tue`

### 📊 USOIL.FOREX/1h · CHoCH_bearish
- Events: 81  ·  Baseline continuation: **49.4%**

  - 🟢 **80.0%** (12/15)
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **25.0%** (6/24)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/1h · CHoCH_bullish
- Events: 82  ·  Baseline continuation: **37.8%**

  - 🟢 **76.9%** (10/13)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **30.0%** (3/10)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **23.1%** (3/13)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
  - 🔴 **15.4%** (2/13)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/1h · bearish
- Events: 288  ·  Baseline continuation: **38.5%**

  - 🟢 **78.6%** (11/14)
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **29.9%** (26/87)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Wed`
  - 🔴 **27.8%** (5/18)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **12.5%** (5/40)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`

### 📊 USOIL.FOREX/1h · bearish_OB
- Events: 279  ·  Baseline continuation: **62.7%**

  - 🟢 **88.9%** (16/18)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
  - 🟢 **80.0%** (8/10)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
  - 🟢 **78.9%** (15/19)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **78.6%** (11/14)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **75.0%** (12/16)
      - `dow = Fri`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **28.6%** (4/14)
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · breakdown
- Events: 111  ·  Baseline continuation: **29.7%**

  - 🔴 **21.4%** (3/14)
      - `dow = Thu`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **21.2%** (7/33)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
  - 🔴 **7.1%** (1/14)
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **0.0%** (0/10)
      - `dow = Thu`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/1h · breakout_up
- Events: 174  ·  Baseline continuation: **39.7%**

  - 🟢 **100.0%** (15/15)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **22.2%** (8/36)
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
  - 🔴 **20.0%** (2/10)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **0.0%** (0/13)
      - `dow ≠ Fri`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/1h · bullish
- Events: 339  ·  Baseline continuation: **41.6%**

  - 🟢 **92.9%** (13/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **29.4%** (5/17)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **25.0%** (4/16)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **23.7%** (9/38)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · bullish_OB
- Events: 273  ·  Baseline continuation: **66.7%**

  - 🟢 **94.7%** (18/19)
      - `dow ≠ Mon`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **93.3%** (14/15)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **81.8%** (9/11)
      - `dow ≠ Mon`
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **81.8%** (9/11)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **81.2%** (13/16)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · engulfing_bear
- Events: 88  ·  Baseline continuation: **35.2%**

  - 🔴 **22.7%** (5/22)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
  - 🔴 **22.2%** (4/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`

### 📊 USOIL.FOREX/1h · engulfing_bull
- Events: 104  ·  Baseline continuation: **39.4%**

  - 🟢 **73.7%** (14/19)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **22.7%** (5/22)
      - `dow = Tue`
  - 🔴 **17.6%** (3/17)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/1h · hammer
- Events: 145  ·  Baseline continuation: **44.8%**

  - 🟢 **72.2%** (13/18)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **70.0%** (14/20)
      - `dow = Wed`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **23.1%** (9/39)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/1h · shooting_star
- Events: 134  ·  Baseline continuation: **38.1%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **23.1%** (3/13)
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Wed`
  - 🔴 **21.4%** (3/14)
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **13.3%** (2/15)
      - `dow = Fri`
      - `rsi_b = (30.0, 50.0]`

---
