# Price Action Pattern Mining Report
_2026-07-20T05:52:38.099356Z_

Bu rapor **HİÇBİR MODELE BAKMADAN** üretilmiştir — yalnızca ham OHLCV.
Üç bağımsız layer:
1. **SMC Structure**: swing pivots, FVG, CHoCH, BOS, Order Blocks
2. **Trend Ladders**: ritmik kademeli hareketler + öncesi/sonrası analiz
3. **Generic Events**: candle patterns, breakouts, S/R touches

---

## XAUUSD · 5m
- Candles: **10000**  ·  Swing pivots: 1307  ·  FVG: 1841
- CHoCH/BOS events: 884  ·  Order Blocks: 1546
- Trend Ladders detected: 105  ·  Candle patterns: 2741  ·  Breakouts: 1003

### S/R Cluster Seviyeleri (top 8)
- 4094.7658 (touches: **1020**, strong)
- 4328.5248 (touches: **156**, strong)
- 4465.4796 (touches: **50**, strong)
- 4266.2111 (touches: **36**, strong)
- 4234.4613 (touches: **16**, strong)
- 4365.56 (touches: **7**, strong)
- 4435.83 (touches: **4**, moderate)
- 4492.2074 (touches: **4**, moderate)

### 🪜 Trend Ladder Analizi (105 ladder)
- Continued: 36  ·  Reversed: 47  ·  Baseline continuation: **34.3%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **71.4%** (10/14)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`
   - `ladder_total_atr_bucket = (1.0, 2.5]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **30.0%** (3/10)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `before_rsi_avg_bucket = (50.0, 70.0]`
- **20.0%** (2/10)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_adx_avg_bucket = (25.0, inf]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
- **16.7%** (2/12)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_rsi_last_bucket = (30.0, 50.0]`
   - `before_volz_avg_bucket = (-0.5, 0.5]`
- **7.1%** (1/14)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`

### 📊 XAUUSD/5m · ALL EVENTS
- Events: 6819  ·  Baseline continuation: **45.7%**

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
  - 🟢 **84.0%** (110/131)
      - `type = bearish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
  - 🟢 **81.8%** (27/33)
      - `type = bearish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **22.2%** (42/189)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **17.8%** (29/163)
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
- Events: 208  ·  Baseline continuation: **20.2%**

  - 🔴 **19.0%** (8/42)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **18.2%** (4/22)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **17.6%** (3/17)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Mon`
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **5.0%** (1/20)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/5m · BOS_bullish
- Events: 163  ·  Baseline continuation: **17.8%**

  - 🔴 **26.7%** (4/15)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **21.4%** (3/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Thu`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **20.7%** (6/29)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (3/15)
      - `adx_b = (18.0, 25.0]`
      - `dow = Tue`
  - 🔴 **18.8%** (3/16)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 XAUUSD/5m · CHoCH_bearish
- Events: 246  ·  Baseline continuation: **43.5%**

  - 🟢 **86.0%** (37/43)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **25.0%** (4/16)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.3%** (14/69)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Fri`
  - 🔴 **5.3%** (1/19)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `rsi_b = (-inf, 30.0]`

### 📊 XAUUSD/5m · CHoCH_bullish
- Events: 252  ·  Baseline continuation: **38.5%**

  - 🟢 **100.0%** (10/10)
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Mon`
  - 🔴 **22.0%** (9/41)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **10.3%** (3/29)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/19)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Tue`

### 📊 XAUUSD/5m · bearish
- Events: 959  ·  Baseline continuation: **43.7%**

  - 🟢 **80.0%** (16/20)
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **29.6%** (16/54)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **29.2%** (7/24)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **28.0%** (7/25)
      - `dow = Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **23.8%** (5/21)
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/5m · bearish_OB
- Events: 785  ·  Baseline continuation: **73.5%**

  - 🟢 **100.0%** (32/32)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **100.0%** (12/12)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **92.3%** (24/26)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `dow = Mon`
  - 🟢 **92.3%** (12/13)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **85.7%** (12/14)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/5m · breakdown
- Events: 568  ·  Baseline continuation: **39.4%**

  - 🔴 **29.5%** (13/44)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **22.6%** (7/31)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Thu`
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **15.4%** (2/13)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **4.5%** (1/22)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🔴 **0.0%** (0/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Wed`

### 📊 XAUUSD/5m · breakout_up
- Events: 420  ·  Baseline continuation: **34.0%**

  - 🔴 **25.7%** (9/35)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **20.0%** (2/10)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **18.9%** (7/37)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **3.3%** (1/30)
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **0.0%** (0/22)
      - `atr_pct_b = (0.4, inf]`

### 📊 XAUUSD/5m · bullish
- Events: 867  ·  Baseline continuation: **35.2%**

  - 🔴 **27.6%** (16/58)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **22.4%** (17/76)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Mon`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Tue`
  - 🔴 **17.4%** (4/23)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 XAUUSD/5m · bullish_OB
- Events: 761  ·  Baseline continuation: **66.2%**

  - 🟢 **100.0%** (28/28)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Wed`
  - 🟢 **92.9%** (13/14)
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🟢 **80.2%** (97/121)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`

### 📊 XAUUSD/5m · engulfing_bear
- Events: 328  ·  Baseline continuation: **47.3%**

  - 🟢 **75.0%** (30/40)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **25.0%** (5/20)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **14.3%** (2/14)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `dow = Mon`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/5m · engulfing_bull
- Events: 356  ·  Baseline continuation: **36.8%**

  - 🟢 **72.7%** (8/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **29.4%** (5/17)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Tue`
  - 🔴 **24.2%** (16/66)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Mon`
  - 🔴 **23.8%** (5/21)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
  - 🔴 **21.4%** (3/14)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Mon`
  - 🔴 **10.7%** (3/28)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`

### 📊 XAUUSD/5m · hammer
- Events: 433  ·  Baseline continuation: **40.0%**

  - 🔴 **26.3%** (5/19)
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **24.0%** (6/25)
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **18.8%** (6/32)
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.8%** (3/19)
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **0.0%** (0/10)
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`

### 📊 XAUUSD/5m · shooting_star
- Events: 473  ·  Baseline continuation: **45.0%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **18.2%** (8/44)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **17.6%** (3/17)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **15.0%** (3/20)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **0.0%** (0/12)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-0.5, 0.5]`

---

## XAUUSD · 15m
- Candles: **4557**  ·  Swing pivots: 538  ·  FVG: 875
- CHoCH/BOS events: 377  ·  Order Blocks: 738
- Trend Ladders detected: 253  ·  Candle patterns: 1242  ·  Breakouts: 484

### S/R Cluster Seviyeleri (top 8)
- 4069.8137 (touches: **184**, strong)
- 4510.777 (touches: **157**, strong)
- 4186.9977 (touches: **48**, strong)
- 4320.9056 (touches: **45**, strong)
- 4710.785 (touches: **16**, strong)
- 4347.9579 (touches: **14**, strong)
- 3985.435 (touches: **10**, strong)
- 3972.0963 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (253 ladder)
- Continued: 108  ·  Reversed: 107  ·  Baseline continuation: **42.7%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (2/12)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
   - `before_rsi_avg_bucket ≠ (30.0, 50.0]`
- **6.2%** (1/16)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`

### 📊 XAUUSD/15m · ALL EVENTS
- Events: 3215  ·  Baseline continuation: **48.1%**

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
  - 🟢 **79.7%** (63/79)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **16.7%** (3/18)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/15m · BOS_bearish
- Events: 96  ·  Baseline continuation: **26.0%**

  - 🔴 **25.0%** (4/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🔴 **16.7%** (2/12)
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/15m · BOS_bullish
- Events: 71  ·  Baseline continuation: **22.5%**

  - 🔴 **26.3%** (5/19)
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
- Events: 105  ·  Baseline continuation: **49.5%**

  - 🟢 **80.0%** (12/15)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **21.7%** (5/23)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/15m · CHoCH_bullish
- Events: 105  ·  Baseline continuation: **38.1%**

  - 🟢 **78.9%** (15/19)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🔴 **28.6%** (6/21)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **9.1%** (1/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 XAUUSD/15m · bearish
- Events: 459  ·  Baseline continuation: **51.4%**

  - 🟢 **85.7%** (12/14)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.05, 0.15]`
  - 🟢 **80.0%** (8/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`
  - 🟢 **72.2%** (13/18)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
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
  - 🔴 **11.8%** (2/17)
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
- Events: 393  ·  Baseline continuation: **75.6%**

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
- Events: 286  ·  Baseline continuation: **45.8%**

  - 🟢 **100.0%** (13/13)
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
      - `dow = Wed`

### 📊 XAUUSD/15m · breakout_up
- Events: 195  ·  Baseline continuation: **36.4%**

  - 🟢 **80.0%** (8/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Tue`
  - 🔴 **27.6%** (8/29)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Tue`
  - 🔴 **6.7%** (1/15)
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **5.0%** (1/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/15m · bullish
- Events: 413  ·  Baseline continuation: **35.1%**

  - 🔴 **26.7%** (8/30)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **22.0%** (9/41)
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
- Events: 345  ·  Baseline continuation: **60.6%**

  - 🟢 **100.0%** (14/14)
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
  - 🟢 **81.5%** (44/54)
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
  - 🟢 **72.1%** (31/43)
      - `dow ≠ Wed`
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **30.0%** (3/10)
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **16.7%** (3/18)
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/15m · engulfing_bear
- Events: 190  ·  Baseline continuation: **48.4%**

  - 🟢 **70.0%** (7/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **30.0%** (6/20)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **27.3%** (3/11)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`

### 📊 XAUUSD/15m · engulfing_bull
- Events: 185  ·  Baseline continuation: **37.3%**

  - 🔴 **25.8%** (8/31)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **12.5%** (2/16)
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **7.7%** (1/13)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/15m · hammer
- Events: 177  ·  Baseline continuation: **35.0%**

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
  - 🔴 **8.3%** (1/12)
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (18.0, 25.0]`

### 📊 XAUUSD/15m · shooting_star
- Events: 195  ·  Baseline continuation: **51.3%**

  - 🟢 **83.3%** (10/12)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`
  - 🔴 **28.6%** (4/14)
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `dow = Mon`

---

## XAUUSD · 30m
- Candles: **4318**  ·  Swing pivots: 544  ·  FVG: 881
- CHoCH/BOS events: 375  ·  Order Blocks: 696
- Trend Ladders detected: 242  ·  Candle patterns: 1189  ·  Breakouts: 433

### S/R Cluster Seviyeleri (top 8)
- 4623.7044 (touches: **298**, strong)
- 4073.0504 (touches: **89**, strong)
- 4318.6962 (touches: **24**, strong)
- 4178.2117 (touches: **23**, strong)
- 3966.6418 (touches: **11**, strong)
- 4349.7882 (touches: **11**, strong)
- 4837.786 (touches: **10**, strong)
- 4226.625 (touches: **8**, strong)

### 🪜 Trend Ladder Analizi (242 ladder)
- Continued: 109  ·  Reversed: 102  ·  Baseline continuation: **45.0%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **75.0%** (9/12)
   - `bb_squeeze_str = True`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **16.7%** (2/12)
   - `bb_squeeze_str ≠ True`
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `start_dist_ema50_atr_bucket = (-1.0, 0.0]`

### 📊 XAUUSD/30m · ALL EVENTS
- Events: 3113  ·  Baseline continuation: **49.4%**

  - 🟢 **100.0%** (17/17)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **85.4%** (35/41)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **84.5%** (60/71)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **79.5%** (31/39)
      - `type = bearish_OB`
      - `adx_b = (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
  - 🟢 **75.7%** (112/148)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **28.8%** (72/250)
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
- Events: 72  ·  Baseline continuation: **25.0%**

  - 🔴 **23.5%** (4/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **5.6%** (1/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b = (-inf, -0.5]`

### 📊 XAUUSD/30m · CHoCH_bearish
- Events: 104  ·  Baseline continuation: **54.8%**

  - 🟢 **80.0%** (16/20)
      - `dow = Wed`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`

### 📊 XAUUSD/30m · CHoCH_bullish
- Events: 105  ·  Baseline continuation: **48.6%**

  - 🟢 **85.7%** (12/14)
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
- Events: 460  ·  Baseline continuation: **51.5%**

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
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.4%** (2/13)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **12.5%** (2/16)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `rsi_b = (30.0, 50.0]`

### 📊 XAUUSD/30m · bearish_OB
- Events: 371  ·  Baseline continuation: **78.2%**

  - 🟢 **100.0%** (17/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`
  - 🟢 **100.0%** (17/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **93.8%** (15/16)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **88.9%** (16/18)
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **84.6%** (33/39)
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
- Events: 196  ·  Baseline continuation: **39.8%**

  - 🔴 **30.0%** (3/10)
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **29.0%** (9/31)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
  - 🔴 **14.3%** (2/14)
      - `dow = Mon`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **0.0%** (0/18)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`

### 📊 XAUUSD/30m · bullish
- Events: 417  ·  Baseline continuation: **38.4%**

  - 🔴 **27.3%** (3/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **25.0%** (4/16)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Fri`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **22.2%** (8/36)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`

### 📊 XAUUSD/30m · bullish_OB
- Events: 325  ·  Baseline continuation: **62.2%**

  - 🟢 **93.3%** (28/30)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow ≠ Thu`
  - 🟢 **71.2%** (84/118)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/30m · engulfing_bear
- Events: 168  ·  Baseline continuation: **45.2%**

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
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.0%** (3/20)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 XAUUSD/30m · engulfing_bull
- Events: 186  ·  Baseline continuation: **34.9%**

  - 🟢 **83.3%** (10/12)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Tue`
  - 🔴 **30.0%** (6/20)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **26.7%** (4/15)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
  - 🔴 **26.3%** (5/19)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Thu`
  - 🔴 **22.2%** (4/18)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **12.5%** (2/16)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/30m · hammer
- Events: 198  ·  Baseline continuation: **31.8%**

  - 🔴 **27.7%** (18/65)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Mon`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **13.8%** (4/29)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Mon`

### 📊 XAUUSD/30m · shooting_star
- Events: 183  ·  Baseline continuation: **49.7%**

  - 🟢 **83.3%** (10/12)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **75.0%** (12/16)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`

---

## XAUUSD · 1h
- Candles: **1941**  ·  Swing pivots: 236  ·  FVG: 387
- CHoCH/BOS events: 169  ·  Order Blocks: 338
- Trend Ladders detected: 100  ·  Candle patterns: 533  ·  Breakouts: 192

### S/R Cluster Seviyeleri (top 8)
- 4507.8266 (touches: **47**, strong)
- 4076.8513 (touches: **46**, strong)
- 4698.035 (touches: **44**, strong)
- 4592.7195 (touches: **20**, strong)
- 4786.2462 (touches: **16**, strong)
- 4183.2682 (touches: **11**, strong)
- 3970.596 (touches: **10**, strong)
- 4356.3133 (touches: **9**, strong)

### 🪜 Trend Ladder Analizi (100 ladder)
- Continued: 48  ·  Reversed: 39  ·  Baseline continuation: **48.0%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **88.2%** (15/17)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `ladder_total_atr_bucket = (1.0, 2.5]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **25.0%** (3/12)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_adx_avg_bucket = (25.0, inf]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
- **14.3%** (2/14)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`

### 📊 XAUUSD/1h · ALL EVENTS
- Events: 1408  ·  Baseline continuation: **49.1%**

  - 🟢 **95.0%** (19/20)
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **82.6%** (19/23)
      - `type = bearish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🟢 **78.9%** (75/95)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
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
  - 🔴 **6.9%** (2/29)
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
- Events: 34  ·  Baseline continuation: **11.8%**

  - 🔴 **15.8%** (3/19)
      - `adx_b ≠ (25.0, inf]`
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
- Events: 201  ·  Baseline continuation: **48.8%**

  - 🟢 **93.8%** (15/16)
      - `dow = Tue`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **87.5%** (14/16)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **20.0%** (4/20)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`

### 📊 XAUUSD/1h · bearish_OB
- Events: 184  ·  Baseline continuation: **69.0%**

  - 🟢 **95.0%** (19/20)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **84.6%** (22/26)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **80.0%** (8/10)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Tue`
  - 🟢 **78.9%** (15/19)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **75.0%** (15/20)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 XAUUSD/1h · breakdown
- Events: 108  ·  Baseline continuation: **50.9%**

  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`

### 📊 XAUUSD/1h · breakout_up
- Events: 81  ·  Baseline continuation: **40.7%**

  - 🔴 **4.8%** (1/21)
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`

### 📊 XAUUSD/1h · bullish
- Events: 185  ·  Baseline continuation: **35.7%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
  - 🔴 **21.4%** (3/14)
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
  - 🔴 **13.3%** (2/15)
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **10.0%** (1/10)
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **7.7%** (1/13)
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Thu`
  - 🔴 **7.7%** (1/13)
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`

### 📊 XAUUSD/1h · bullish_OB
- Events: 153  ·  Baseline continuation: **68.0%**

  - 🟢 **89.5%** (34/38)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
      - `adx_b = (25.0, inf]`
  - 🟢 **85.7%** (12/14)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **76.9%** (10/13)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **72.7%** (24/33)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 XAUUSD/1h · engulfing_bear
- Events: 95  ·  Baseline continuation: **56.8%**

  - 🟢 **80.0%** (16/20)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 XAUUSD/1h · engulfing_bull
- Events: 71  ·  Baseline continuation: **39.4%**

  - 🔴 **27.3%** (3/11)
      - `adx_b = (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **23.5%** (4/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (2/10)
      - `adx_b = (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`

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
- Events: 88  ·  Baseline continuation: **50.0%**

  - 🟢 **72.2%** (13/18)
      - `adx_b = (-inf, 18.0]`
  - 🔴 **27.3%** (3/11)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Fri`

---

## NDX.INDX · 5m
- Candles: **10000**  ·  Swing pivots: 1139  ·  FVG: 2420
- CHoCH/BOS events: 796  ·  Order Blocks: 1797
- Trend Ladders detected: 157  ·  Candle patterns: 2700  ·  Breakouts: 1388

### S/R Cluster Seviyeleri (top 8)
- 29782.9829 (touches: **1075**, strong)
- 28615.1573 (touches: **46**, strong)
- 28745.4 (touches: **8**, strong)
- 28241.1908 (touches: **2**, weak)
- 28348.95 (touches: **2**, weak)
- 28421.35 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (157 ladder)
- Continued: 68  ·  Reversed: 64  ·  Baseline continuation: **43.3%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **70.4%** (19/27)
   - `before_adx_avg_bucket ≠ (-inf, 18.0]`
   - `start_dist_ema50_atr_bucket = (-inf, -1.0]`
   - `ladder_slope_atr_bucket ≠ (0.2, 0.5]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **28.6%** (6/21)
   - `before_adx_avg_bucket ≠ (-inf, 18.0]`
   - `start_dist_ema50_atr_bucket ≠ (-inf, -1.0]`
   - `before_volz_avg_bucket = (-inf, -0.5]`
- **11.1%** (2/18)
   - `before_adx_avg_bucket = (-inf, 18.0]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`

### 📊 NDX.INDX/5m · ALL EVENTS
- Events: 8146  ·  Baseline continuation: **47.0%**

  - 🟢 **79.7%** (126/158)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
  - 🟢 **77.4%** (24/31)
      - `type = bearish_OB`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
  - 🟢 **72.8%** (311/427)
      - `type = bearish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **70.4%** (174/247)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **27.4%** (49/179)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bullish`
      - `type = BOS_bearish`
  - 🔴 **26.0%** (25/96)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **12.7%** (9/71)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/5m · BOS_bearish
- Events: 179  ·  Baseline continuation: **27.4%**

  - 🔴 **30.0%** (9/30)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **25.0%** (4/16)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **23.1%** (9/39)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **16.7%** (2/12)
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`

### 📊 NDX.INDX/5m · BOS_bullish
- Events: 167  ·  Baseline continuation: **20.4%**

  - 🔴 **18.4%** (7/38)
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Tue`
  - 🔴 **14.3%** (2/14)
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **12.5%** (2/16)
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **9.1%** (1/11)
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 NDX.INDX/5m · CHoCH_bearish
- Events: 224  ·  Baseline continuation: **44.6%**

  - 🟢 **85.7%** (12/14)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **73.2%** (41/56)
      - `rsi_b = (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **22.9%** (8/35)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **13.6%** (3/22)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/5m · CHoCH_bullish
- Events: 223  ·  Baseline continuation: **43.0%**

  - 🟢 **82.4%** (14/17)
      - `rsi_b = (30.0, 50.0]`
      - `dow = Thu`
  - 🟢 **72.7%** (8/11)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **26.7%** (4/15)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **0.0%** (0/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **0.0%** (0/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Wed`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/5m · bearish
- Events: 1211  ·  Baseline continuation: **45.5%**

  - 🔴 **23.5%** (4/17)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **14.6%** (7/48)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`

### 📊 NDX.INDX/5m · bearish_OB
- Events: 900  ·  Baseline continuation: **67.4%**

  - 🟢 **90.0%** (9/10)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **74.3%** (252/339)
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
  - 🟢 **71.6%** (58/81)
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **71.4%** (15/21)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **71.4%** (10/14)
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`

### 📊 NDX.INDX/5m · breakdown
- Events: 686  ·  Baseline continuation: **46.9%**

  - 🟢 **86.7%** (13/15)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **76.9%** (20/26)
      - `dow = Fri`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **72.7%** (8/11)
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **25.8%** (16/62)
      - `dow ≠ Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 NDX.INDX/5m · breakout_up
- Events: 689  ·  Baseline continuation: **37.6%**

  - 🔴 **28.3%** (15/53)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
  - 🔴 **25.0%** (4/16)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow = Wed`
  - 🔴 **25.0%** (5/20)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
      - `dow = Thu`
  - 🔴 **13.0%** (6/46)
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`

### 📊 NDX.INDX/5m · bullish
- Events: 1207  ·  Baseline continuation: **38.3%**

  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **29.3%** (17/58)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **27.5%** (11/40)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`
  - 🔴 **27.0%** (33/122)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
  - 🔴 **25.0%** (6/24)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Tue`
  - 🔴 **12.5%** (8/64)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 NDX.INDX/5m · bullish_OB
- Events: 897  ·  Baseline continuation: **66.4%**

  - 🟢 **100.0%** (15/15)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **89.7%** (26/29)
      - `atr_pct_b = (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **87.0%** (20/23)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **81.2%** (13/16)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **80.0%** (8/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/5m · engulfing_bear
- Events: 461  ·  Baseline continuation: **42.7%**

  - 🔴 **19.0%** (4/21)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **18.6%** (8/43)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **11.8%** (2/17)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/5m · engulfing_bull
- Events: 393  ·  Baseline continuation: **38.4%**

  - 🟢 **70.0%** (7/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`
  - 🟢 **70.0%** (7/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`
  - 🔴 **22.1%** (23/104)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **20.0%** (6/30)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 NDX.INDX/5m · hammer
- Events: 511  ·  Baseline continuation: **40.9%**

  - 🔴 **25.0%** (12/48)
      - `rsi_b ≠ (70.0, inf]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `dow = Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **13.6%** (3/22)
      - `rsi_b = (70.0, inf]`

### 📊 NDX.INDX/5m · shooting_star
- Events: 398  ·  Baseline continuation: **50.0%**

  - 🟢 **90.9%** (10/11)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Wed`
  - 🟢 **90.0%** (9/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **70.0%** (7/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
  - 🟢 **70.0%** (14/20)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **27.8%** (5/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`

---

## NDX.INDX · 15m
- Candles: **4557**  ·  Swing pivots: 526  ·  FVG: 1084
- CHoCH/BOS events: 375  ·  Order Blocks: 856
- Trend Ladders detected: 257  ·  Candle patterns: 1329  ·  Breakouts: 597

### S/R Cluster Seviyeleri (top 8)
- 29663.2855 (touches: **503**, strong)
- 28624.3786 (touches: **14**, strong)
- 28207.0 (touches: **2**, weak)
- 28514.9 (touches: **2**, weak)
- 30771.25 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (257 ladder)
- Continued: 105  ·  Reversed: 111  ·  Baseline continuation: **40.9%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (2/10)
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `ladder_total_atr_bucket = (-inf, 1.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
- **18.8%** (3/16)
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
- Events: 3738  ·  Baseline continuation: **46.1%**

  - 🟢 **87.9%** (51/58)
      - `type = bearish_OB`
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **80.8%** (42/52)
      - `type = bearish_OB`
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **74.0%** (148/200)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **70.6%** (12/17)
      - `type = bearish_OB`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **30.0%** (9/30)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **14.0%** (7/50)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/15m · BOS_bearish
- Events: 78  ·  Baseline continuation: **25.6%**

  - 🔴 **28.6%** (6/21)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **8.7%** (2/23)
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **8.3%** (1/12)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 NDX.INDX/15m · BOS_bullish
- Events: 80  ·  Baseline continuation: **20.0%**

  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `adx_b = (25.0, inf]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **5.9%** (1/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Mon`

### 📊 NDX.INDX/15m · CHoCH_bearish
- Events: 108  ·  Baseline continuation: **43.5%**

  - 🟢 **90.9%** (10/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **5.6%** (1/18)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.15, 0.4]`

### 📊 NDX.INDX/15m · CHoCH_bullish
- Events: 108  ·  Baseline continuation: **39.8%**

  - 🔴 **25.0%** (3/12)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🔴 **6.7%** (1/15)
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/15m · bearish
- Events: 513  ·  Baseline continuation: **45.0%**

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
- Events: 428  ·  Baseline continuation: **65.2%**

  - 🟢 **91.7%** (11/12)
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **91.3%** (42/46)
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **90.0%** (18/20)
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Fri`
  - 🟢 **75.0%** (24/32)
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
  - 🟢 **75.0%** (9/12)
      - `dow ≠ Thu`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **20.0%** (2/10)
      - `dow = Thu`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 NDX.INDX/15m · breakdown
- Events: 271  ·  Baseline continuation: **44.6%**

  - 🟢 **81.8%** (9/11)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **75.0%** (9/12)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **11.4%** (4/35)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (-inf, 30.0]`

### 📊 NDX.INDX/15m · breakout_up
- Events: 316  ·  Baseline continuation: **38.0%**

  - 🟢 **83.3%** (15/18)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **30.0%** (6/20)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Fri`
  - 🔴 **23.1%** (3/13)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🔴 **22.7%** (10/44)
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

### 📊 NDX.INDX/15m · bullish
- Events: 567  ·  Baseline continuation: **40.7%**

  - 🔴 **30.0%** (3/10)
      - `atr_pct_b = (0.05, 0.15]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.2%** (20/71)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `rsi_b = (50.0, 70.0]`
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

### 📊 NDX.INDX/15m · bullish_OB
- Events: 427  ·  Baseline continuation: **61.6%**

  - 🟢 **94.1%** (16/17)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **81.0%** (17/21)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **77.6%** (52/67)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **71.1%** (27/38)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`

### 📊 NDX.INDX/15m · engulfing_bear
- Events: 211  ·  Baseline continuation: **37.0%**

  - 🟢 **72.2%** (13/18)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Thu`
  - 🔴 **25.0%** (4/16)
      - `dow ≠ Mon`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **13.3%** (2/15)
      - `dow ≠ Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **9.1%** (1/11)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **0.0%** (0/14)
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`

### 📊 NDX.INDX/15m · engulfing_bull
- Events: 189  ·  Baseline continuation: **36.5%**

  - 🔴 **26.7%** (4/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow = Tue`
  - 🔴 **20.0%** (3/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
  - 🔴 **17.4%** (4/23)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`

### 📊 NDX.INDX/15m · hammer
- Events: 246  ·  Baseline continuation: **46.7%**

  - 🟢 **75.0%** (15/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow ≠ Fri`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Fri`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **27.3%** (3/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Fri`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **26.1%** (6/23)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **15.4%** (2/13)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Fri`
      - `dow = Thu`

### 📊 NDX.INDX/15m · shooting_star
- Events: 196  ·  Baseline continuation: **45.9%**

  - 🔴 **23.1%** (3/13)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **10.0%** (1/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **0.0%** (0/10)
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`

---

## NDX.INDX · 30m
- Candles: **3911**  ·  Swing pivots: 481  ·  FVG: 931
- CHoCH/BOS events: 332  ·  Order Blocks: 708
- Trend Ladders detected: 223  ·  Candle patterns: 1107  ·  Breakouts: 523

### S/R Cluster Seviyeleri (top 8)
- 29559.1543 (touches: **280**, strong)
- 24109.3792 (touches: **48**, strong)
- 26685.4867 (touches: **15**, strong)
- 27025.1909 (touches: **11**, strong)
- 23812.0875 (touches: **8**, strong)
- 27196.7 (touches: **8**, strong)
- 25067.6286 (touches: **7**, strong)
- 24776.9333 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (223 ladder)
- Continued: 97  ·  Reversed: 81  ·  Baseline continuation: **43.5%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (3/15)
   - `before_rsi_last_bucket = (70.0, inf]`

### 📊 NDX.INDX/30m · ALL EVENTS
- Events: 3206  ·  Baseline continuation: **46.8%**

  - 🟢 **100.0%** (23/23)
      - `type = bullish_OB`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **81.1%** (30/37)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🟢 **75.6%** (127/168)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🟢 **72.0%** (18/25)
      - `type = bullish_OB`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **70.6%** (24/34)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
  - 🔴 **16.9%** (10/59)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bullish`
      - `vol_z_b ≠ (-0.5, 0.5]`

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
- Events: 89  ·  Baseline continuation: **22.5%**

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
  - 🔴 **14.3%** (2/14)
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
- Events: 92  ·  Baseline continuation: **38.0%**

  - 🔴 **22.2%** (4/18)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **14.3%** (2/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/30m · CHoCH_bullish
- Events: 92  ·  Baseline continuation: **42.4%**

  - 🟢 **75.0%** (15/20)
      - `adx_b = (-inf, 18.0]`
  - 🔴 **25.0%** (3/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.0%** (3/20)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 NDX.INDX/30m · bearish
- Events: 404  ·  Baseline continuation: **40.8%**

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
      - `adx_b ≠ (18.0, 25.0]`
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
      - `adx_b = (18.0, 25.0]`

### 📊 NDX.INDX/30m · bearish_OB
- Events: 363  ·  Baseline continuation: **62.8%**

  - 🟢 **90.0%** (9/10)
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
  - 🟢 **87.5%** (49/56)
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
  - 🟢 **86.7%** (13/15)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **85.7%** (12/14)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **70.0%** (7/10)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`

### 📊 NDX.INDX/30m · breakdown
- Events: 199  ·  Baseline continuation: **43.2%**

  - 🔴 **22.2%** (4/18)
      - `dow ≠ Mon`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **15.8%** (3/19)
      - `dow ≠ Mon`
      - `dow = Wed`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.4%** (2/13)
      - `dow = Mon`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **7.7%** (1/13)
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 NDX.INDX/30m · breakout_up
- Events: 320  ·  Baseline continuation: **47.2%**

  - 🟢 **88.9%** (16/18)
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.0%** (9/12)
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
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
- Events: 524  ·  Baseline continuation: **45.6%**

  - 🟢 **84.2%** (16/19)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`
  - 🟢 **81.2%** (13/16)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **73.3%** (11/15)
      - `atr_pct_b = (0.4, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.8%** (19/66)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **0.0%** (0/12)
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
      - `rsi_b = (70.0, inf]`

### 📊 NDX.INDX/30m · bullish_OB
- Events: 345  ·  Baseline continuation: **67.0%**

  - 🟢 **100.0%** (20/20)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **93.3%** (14/15)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Tue`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🟢 **79.3%** (23/29)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🟢 **75.0%** (9/12)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/30m · engulfing_bear
- Events: 193  ·  Baseline continuation: **40.4%**

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
- Events: 161  ·  Baseline continuation: **42.2%**

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
- Events: 212  ·  Baseline continuation: **40.6%**

  - 🟢 **71.4%** (10/14)
      - `rsi_b = (70.0, inf]`
  - 🔴 **29.1%** (16/55)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 NDX.INDX/30m · shooting_star
- Events: 155  ·  Baseline continuation: **39.4%**

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
- Candles: **5219**  ·  Swing pivots: 604  ·  FVG: 1020
- CHoCH/BOS events: 410  ·  Order Blocks: 967
- Trend Ladders detected: 250  ·  Candle patterns: 1490  ·  Breakouts: 628

### S/R Cluster Seviyeleri (top 8)
- 25088.9092 (touches: **352**, strong)
- 29694.382 (touches: **163**, strong)
- 26242.4234 (touches: **26**, strong)
- 28638.4418 (touches: **11**, strong)
- 26723.5571 (touches: **7**, strong)
- 27008.6297 (touches: **6**, strong)
- 27394.28 (touches: **5**, strong)
- 23795.35 (touches: **4**, moderate)

### 🪜 Trend Ladder Analizi (250 ladder)
- Continued: 94  ·  Reversed: 111  ·  Baseline continuation: **37.6%**

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
- Events: 3939  ·  Baseline continuation: **45.3%**

  - 🟢 **94.1%** (16/17)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **90.9%** (40/44)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **85.4%** (35/41)
      - `type = bullish_OB`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **78.5%** (84/107)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🟢 **77.8%** (14/18)
      - `type = bullish_OB`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`
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
- Events: 109  ·  Baseline continuation: **37.6%**

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
  - 🔴 **11.1%** (2/18)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`

### 📊 NDX.INDX/1h · bearish
- Events: 445  ·  Baseline continuation: **43.6%**

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
  - 🔴 **0.0%** (0/17)
      - `dow = Mon`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (25.0, inf]`

### 📊 NDX.INDX/1h · bearish_OB
- Events: 527  ·  Baseline continuation: **63.2%**

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
  - 🟢 **81.0%** (17/21)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`

### 📊 NDX.INDX/1h · breakdown
- Events: 246  ·  Baseline continuation: **34.1%**

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
  - 🔴 **14.3%** (2/14)
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
- Events: 374  ·  Baseline continuation: **34.0%**

  - 🟢 **76.9%** (10/13)
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
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
- Events: 569  ·  Baseline continuation: **40.9%**

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
- Events: 440  ·  Baseline continuation: **67.0%**

  - 🟢 **100.0%** (12/12)
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
  - 🟢 **87.5%** (28/32)
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **83.3%** (15/18)
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Mon`

### 📊 NDX.INDX/1h · engulfing_bear
- Events: 225  ·  Baseline continuation: **42.2%**

  - 🟢 **80.0%** (12/15)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `atr_pct_b ≠ (0.15, 0.4]`
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
- Events: 234  ·  Baseline continuation: **43.6%**

  - 🟢 **71.4%** (10/14)
      - `dow ≠ Fri`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Wed`
  - 🔴 **27.8%** (5/18)
      - `dow = Fri`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Fri`
      - `dow = Thu`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Fri`
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **9.1%** (1/11)
      - `dow = Fri`
      - `adx_b = (-inf, 18.0]`

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
- Events: 197  ·  Baseline continuation: **41.1%**

  - 🔴 **29.0%** (9/31)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **13.6%** (3/22)
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`

---

## GDAXI.INDX · 5m
- Candles: **10000**  ·  Swing pivots: 1302  ·  FVG: 2339
- CHoCH/BOS events: 909  ·  Order Blocks: 1670
- Trend Ladders detected: 132  ·  Candle patterns: 2193  ·  Breakouts: 1199

### S/R Cluster Seviyeleri (top 8)
- 24931.0803 (touches: **1110**, strong)
- 25814.7322 (touches: **58**, strong)
- 24217.5924 (touches: **20**, strong)
- 25719.3759 (touches: **17**, strong)
- 24425.3116 (touches: **13**, strong)
- 25572.496 (touches: **10**, strong)
- 24463.825 (touches: **8**, strong)
- 24119.4 (touches: **7**, strong)

### 🪜 Trend Ladder Analizi (132 ladder)
- Continued: 43  ·  Reversed: 57  ·  Baseline continuation: **32.6%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **28.6%** (4/14)
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
   - `before_rsi_avg_bucket = (30.0, 50.0]`
- **24.0%** (6/25)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`
- **17.6%** (6/34)
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `before_rsi_last_bucket = (50.0, 70.0]`
   - `before_volz_avg_bucket ≠ (-inf, -0.5]`

### 📊 GDAXI.INDX/5m · ALL EVENTS
- Events: 7320  ·  Baseline continuation: **44.6%**

  - 🟢 **75.7%** (265/350)
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **74.2%** (330/445)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
  - 🔴 **30.0%** (12/40)
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
  - 🔴 **28.0%** (7/25)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **27.9%** (12/43)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `dow = Thu`
  - 🔴 **21.4%** (48/224)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bullish`
      - `type = BOS_bearish`
  - 🔴 **12.4%** (15/121)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `dow ≠ Thu`

### 📊 GDAXI.INDX/5m · BOS_bearish
- Events: 224  ·  Baseline continuation: **21.4%**

  - 🔴 **28.6%** (6/21)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **27.3%** (6/22)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **18.4%** (14/76)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **15.4%** (2/13)
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`

### 📊 GDAXI.INDX/5m · BOS_bullish
- Events: 164  ·  Baseline continuation: **16.5%**

  - 🔴 **27.8%** (5/18)
      - `dow ≠ Wed`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Thu`
  - 🔴 **12.5%** (2/16)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Thu`
  - 🔴 **12.5%** (7/56)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
  - 🔴 **9.1%** (1/11)
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **0.0%** (0/10)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Thu`

### 📊 GDAXI.INDX/5m · CHoCH_bearish
- Events: 258  ·  Baseline continuation: **50.4%**

  - 🟢 **88.2%** (15/17)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **78.1%** (25/32)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Tue`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **75.0%** (9/12)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **28.6%** (4/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (-inf, 0.05]`
  - 🔴 **11.8%** (4/34)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`

### 📊 GDAXI.INDX/5m · CHoCH_bullish
- Events: 259  ·  Baseline continuation: **35.9%**

  - 🟢 **90.0%** (9/10)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **73.7%** (14/19)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **29.6%** (8/27)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
  - 🔴 **20.0%** (2/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **15.3%** (13/85)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
  - 🔴 **0.0%** (0/19)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/5m · bearish
- Events: 1169  ·  Baseline continuation: **41.3%**

  - 🟢 **87.5%** (14/16)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **15.4%** (2/13)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
  - 🔴 **13.3%** (2/15)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
      - `dow = Tue`
  - 🔴 **7.1%** (3/42)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · bearish_OB
- Events: 854  ·  Baseline continuation: **67.0%**

  - 🟢 **83.7%** (113/135)
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **81.2%** (13/16)
      - `dow ≠ Fri`
      - `dow = Tue`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **74.0%** (91/123)
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **70.7%** (152/215)
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **70.7%** (29/41)
      - `dow = Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **30.0%** (3/10)
      - `dow = Fri`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **21.4%** (6/28)
      - `dow ≠ Fri`
      - `dow = Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · breakdown
- Events: 612  ·  Baseline continuation: **38.4%**

  - 🟢 **78.9%** (15/19)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Tue`
  - 🟢 **78.9%** (15/19)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (-inf, 0.05]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **28.0%** (40/143)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **23.1%** (15/65)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **21.4%** (6/28)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🔴 **6.9%** (2/29)
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/5m · breakout_up
- Events: 570  ·  Baseline continuation: **35.1%**

  - 🔴 **29.6%** (8/27)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **21.0%** (17/81)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.5%** (2/19)
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/5m · bullish
- Events: 1154  ·  Baseline continuation: **36.8%**

  - 🟢 **70.6%** (12/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **30.0%** (21/70)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Wed`
  - 🔴 **25.0%** (4/16)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Mon`
      - `dow ≠ Thu`
  - 🔴 **20.5%** (26/127)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Thu`
  - 🔴 **5.0%** (1/20)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **0.0%** (0/11)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
      - `dow = Mon`

### 📊 GDAXI.INDX/5m · bullish_OB
- Events: 816  ·  Baseline continuation: **67.3%**

  - 🟢 **100.0%** (14/14)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **75.7%** (255/337)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
  - 🟢 **73.8%** (48/65)
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b ≠ (-inf, 0.05]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`
  - 🟢 **72.2%** (26/36)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **26.3%** (5/19)
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `adx_b = (18.0, 25.0]`
      - `atr_pct_b = (-inf, 0.05]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 GDAXI.INDX/5m · engulfing_bear
- Events: 262  ·  Baseline continuation: **41.2%**

  - 🟢 **80.0%** (8/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Wed`
  - 🔴 **18.2%** (6/33)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`

### 📊 GDAXI.INDX/5m · engulfing_bull
- Events: 218  ·  Baseline continuation: **37.2%**

  - 🟢 **80.0%** (8/10)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`
  - 🔴 **28.6%** (4/14)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **22.5%** (9/40)
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 GDAXI.INDX/5m · hammer
- Events: 382  ·  Baseline continuation: **37.2%**

  - 🟢 **77.8%** (14/18)
      - `dow = Thu`
      - `adx_b ≠ (18.0, 25.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **29.4%** (5/17)
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **22.2%** (6/27)
      - `dow ≠ Thu`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **16.7%** (13/78)
      - `dow ≠ Thu`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`

### 📊 GDAXI.INDX/5m · shooting_star
- Events: 378  ·  Baseline continuation: **45.0%**

  - 🔴 **25.0%** (8/32)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **20.0%** (8/40)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Thu`

---

## GDAXI.INDX · 15m
- Candles: **4544**  ·  Swing pivots: 532  ·  FVG: 1012
- CHoCH/BOS events: 394  ·  Order Blocks: 797
- Trend Ladders detected: 261  ·  Candle patterns: 1152  ·  Breakouts: 542

### S/R Cluster Seviyeleri (top 8)
- 24858.8039 (touches: **408**, strong)
- 24224.9119 (touches: **42**, strong)
- 25838.2308 (touches: **13**, strong)
- 25719.65 (touches: **10**, strong)
- 24070.9 (touches: **8**, strong)
- 23927.2667 (touches: **6**, strong)
- 24003.1167 (touches: **6**, strong)
- 25376.9667 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (261 ladder)
- Continued: 107  ·  Reversed: 103  ·  Baseline continuation: **41.0%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **18.2%** (2/11)
   - `start_dist_ema50_atr_bucket ≠ (0.0, 1.0]`
   - `before_rsi_avg_bucket ≠ (30.0, 50.0]`
   - `before_rsi_last_bucket = (70.0, inf]`
- **18.2%** (2/11)
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
- **13.3%** (2/15)
   - `start_dist_ema50_atr_bucket = (0.0, 1.0]`
   - `before_adx_avg_bucket = (18.0, 25.0]`

### 📊 GDAXI.INDX/15m · ALL EVENTS
- Events: 3423  ·  Baseline continuation: **46.5%**

  - 🟢 **90.0%** (18/20)
      - `type = bearish_OB`
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🟢 **83.3%** (30/36)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Thu`
  - 🟢 **78.7%** (59/75)
      - `type = bearish_OB`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **72.1%** (31/43)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Tue`
  - 🟢 **71.9%** (120/167)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
  - 🔴 **27.3%** (9/33)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **17.6%** (3/17)
      - `type = bearish_OB`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **6.7%** (2/30)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bullish`
      - `vol_z_b = (0.5, inf]`

### 📊 GDAXI.INDX/15m · BOS_bearish
- Events: 83  ·  Baseline continuation: **28.9%**

  - 🔴 **12.5%** (2/16)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **12.5%** (3/24)
      - `rsi_b = (-inf, 30.0]`

### 📊 GDAXI.INDX/15m · BOS_bullish
- Events: 63  ·  Baseline continuation: **17.5%**

  - 🔴 **20.0%** (4/20)
      - `vol_z_b ≠ (0.5, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **5.6%** (1/18)
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`

### 📊 GDAXI.INDX/15m · CHoCH_bearish
- Events: 123  ·  Baseline continuation: **48.0%**

  - 🟢 **90.0%** (18/20)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **23.8%** (5/21)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Mon`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **8.3%** (1/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Mon`

### 📊 GDAXI.INDX/15m · CHoCH_bullish
- Events: 123  ·  Baseline continuation: **36.6%**

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
  - 🔴 **0.0%** (0/10)
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/15m · bearish
- Events: 521  ·  Baseline continuation: **42.4%**

  - 🟢 **75.0%** (15/20)
      - `dow = Tue`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **71.4%** (10/14)
      - `dow = Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **22.2%** (10/45)
      - `dow ≠ Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Mon`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **21.5%** (14/65)
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Mon`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (0.05, 0.15]`

### 📊 GDAXI.INDX/15m · bearish_OB
- Events: 414  ·  Baseline continuation: **68.1%**

  - 🟢 **95.5%** (21/22)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **91.7%** (11/12)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = NA`
  - 🟢 **90.0%** (18/20)
      - `adx_b = (-inf, 18.0]`
      - `dow = Tue`
  - 🟢 **80.0%** (8/10)
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **71.9%** (120/167)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ NA`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
  - 🔴 **17.6%** (3/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ NA`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/15m · breakdown
- Events: 281  ·  Baseline continuation: **42.0%**

  - 🔴 **15.0%** (3/20)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🔴 **10.0%** (1/10)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b = (0.5, inf]`
      - `dow = Mon`

### 📊 GDAXI.INDX/15m · breakout_up
- Events: 257  ·  Baseline continuation: **41.2%**

  - 🟢 **90.9%** (10/11)
      - `dow = Tue`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **78.6%** (11/14)
      - `dow ≠ Tue`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Mon`
      - `rsi_b = (50.0, 70.0]`
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
- Events: 489  ·  Baseline continuation: **39.1%**

  - 🟢 **78.6%** (11/14)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Fri`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🔴 **20.0%** (3/15)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow = Mon`
      - `atr_pct_b = (0.05, 0.15]`
  - 🔴 **19.0%** (4/21)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `adx_b = (25.0, inf]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `dow ≠ Mon`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Fri`
  - 🔴 **11.8%** (2/17)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow = Fri`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/15m · bullish_OB
- Events: 382  ·  Baseline continuation: **63.6%**

  - 🟢 **100.0%** (11/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **95.0%** (19/20)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Tue`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **91.7%** (11/12)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`
  - 🟢 **84.2%** (16/19)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/15m · engulfing_bear
- Events: 155  ·  Baseline continuation: **47.1%**

  - 🟢 **100.0%** (11/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **90.9%** (10/11)
      - `vol_z_b ≠ (0.5, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Wed`
  - 🟢 **76.9%** (10/13)
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
- Events: 216  ·  Baseline continuation: **40.7%**

  - 🟢 **84.2%** (16/19)
      - `dow = Thu`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (6/24)
      - `dow ≠ Thu`
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Tue`
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
- Events: 193  ·  Baseline continuation: **44.6%**

  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **25.0%** (4/16)
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **25.0%** (3/12)
      - `adx_b = (25.0, inf]`
      - `dow = Mon`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **21.4%** (3/14)
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Fri`

---

## GDAXI.INDX · 30m
- Candles: **3691**  ·  Swing pivots: 470  ·  FVG: 845
- CHoCH/BOS events: 334  ·  Order Blocks: 621
- Trend Ladders detected: 219  ·  Candle patterns: 1059  ·  Breakouts: 415

### S/R Cluster Seviyeleri (top 8)
- 24227.5147 (touches: **191**, strong)
- 24980.2056 (touches: **177**, strong)
- 22861.0813 (touches: **16**, strong)
- 22585.9692 (touches: **13**, strong)
- 23387.3429 (touches: **7**, strong)
- 25838.5714 (touches: **7**, strong)
- 22380.8 (touches: **6**, strong)
- 23003.55 (touches: **6**, strong)

### 🪜 Trend Ladder Analizi (219 ladder)
- Continued: 95  ·  Reversed: 97  ·  Baseline continuation: **43.4%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **20.0%** (3/15)
   - `ladder_slope_atr_bucket ≠ (-inf, 0.2]`
   - `before_bb_width_atr_avg_bucket ≠ (4.0, inf]`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`
- **14.3%** (3/21)
   - `ladder_slope_atr_bucket = (-inf, 0.2]`
   - `before_rsi_last_bucket = (50.0, 70.0]`
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`

### 📊 GDAXI.INDX/30m · ALL EVENTS
- Events: 2869  ·  Baseline continuation: **47.6%**

  - 🟢 **90.6%** (48/53)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **73.4%** (124/169)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **72.7%** (141/194)
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
- Events: 66  ·  Baseline continuation: **28.8%**

  - 🟢 **70.0%** (7/10)
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (25.0, inf]`
  - 🔴 **30.0%** (3/10)
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **17.6%** (3/17)
      - `dow ≠ Mon`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **0.0%** (0/14)
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
- Events: 93  ·  Baseline continuation: **48.4%**

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
- Events: 95  ·  Baseline continuation: **41.1%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **23.8%** (5/21)
      - `dow = Mon`
  - 🔴 **16.7%** (2/12)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/30m · bearish
- Events: 408  ·  Baseline continuation: **40.0%**

  - 🔴 **30.0%** (3/10)
      - `dow = Mon`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **28.6%** (12/42)
      - `dow ≠ Mon`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **27.8%** (5/18)
      - `dow = Mon`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **21.1%** (4/19)
      - `dow ≠ Mon`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`

### 📊 GDAXI.INDX/30m · bearish_OB
- Events: 317  ·  Baseline continuation: **65.9%**

  - 🟢 **89.5%** (17/19)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🟢 **85.7%** (24/28)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **81.8%** (9/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Tue`
  - 🟢 **73.7%** (14/19)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **72.7%** (16/22)
      - `atr_pct_b = (0.15, 0.4]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/30m · breakdown
- Events: 201  ·  Baseline continuation: **41.8%**

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
  - 🔴 **7.1%** (1/14)
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 GDAXI.INDX/30m · breakout_up
- Events: 213  ·  Baseline continuation: **48.4%**

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
- Events: 436  ·  Baseline continuation: **46.1%**

  - 🟢 **82.4%** (14/17)
      - `dow ≠ Fri`
      - `dow = Mon`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **16.7%** (2/12)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **0.0%** (0/11)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`

### 📊 GDAXI.INDX/30m · bullish_OB
- Events: 304  ·  Baseline continuation: **70.4%**

  - 🟢 **100.0%** (20/20)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **88.5%** (23/26)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **84.8%** (28/33)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b = (30.0, 50.0]`
  - 🟢 **75.0%** (9/12)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Fri`
      - `rsi_b = (50.0, 70.0]`
  - 🟢 **70.6%** (101/143)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Fri`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **23.5%** (4/17)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Wed`

### 📊 GDAXI.INDX/30m · engulfing_bear
- Events: 163  ·  Baseline continuation: **46.0%**

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
- Events: 186  ·  Baseline continuation: **37.1%**

  - 🟢 **75.0%** (21/28)
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **23.8%** (5/21)
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
- Events: 154  ·  Baseline continuation: **44.2%**

  - 🟢 **83.3%** (15/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Fri`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **27.8%** (5/18)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Fri`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **23.5%** (4/17)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **14.3%** (2/14)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`

---

## GDAXI.INDX · 1h
- Candles: **4617**  ·  Swing pivots: 571  ·  FVG: 1071
- CHoCH/BOS events: 403  ·  Order Blocks: 858
- Trend Ladders detected: 239  ·  Candle patterns: 1370  ·  Breakouts: 538

### S/R Cluster Seviyeleri (top 8)
- 24499.8381 (touches: **487**, strong)
- 23363.2571 (touches: **28**, strong)
- 23089.3222 (touches: **18**, strong)
- 22801.16 (touches: **5**, strong)
- 25461.778 (touches: **5**, strong)
- 22717.025 (touches: **4**, moderate)
- 22620.8 (touches: **3**, moderate)
- 21922.55 (touches: **2**, weak)

### 🪜 Trend Ladder Analizi (239 ladder)
- Continued: 105  ·  Reversed: 89  ·  Baseline continuation: **43.9%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **78.6%** (11/14)
   - `before_rsi_avg_bucket = (50.0, 70.0]`
   - `ladder_total_atr_bucket = (2.5, inf]`
   - `before_rsi_last_bucket = (30.0, 50.0]`
- **76.9%** (10/13)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `ladder_total_atr_bucket = (-inf, 1.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **24.5%** (12/49)
   - `before_rsi_avg_bucket ≠ (50.0, 70.0]`
   - `ladder_total_atr_bucket ≠ (-inf, 1.0]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`

### 📊 GDAXI.INDX/1h · ALL EVENTS
- Events: 3724  ·  Baseline continuation: **46.4%**

  - 🟢 **89.5%** (17/19)
      - `type = bearish_OB`
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`
  - 🟢 **82.7%** (67/81)
      - `type = bearish_OB`
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **70.9%** (151/213)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
  - 🟢 **70.9%** (39/55)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.6%** (32/112)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **15.9%** (7/44)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `adx_b = (25.0, inf]`

### 📊 GDAXI.INDX/1h · BOS_bearish
- Events: 80  ·  Baseline continuation: **25.0%**

  - 🔴 **29.2%** (7/24)
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **16.7%** (2/12)
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🔴 **0.0%** (0/20)
      - `adx_b = (25.0, inf]`
      - `rsi_b = (-inf, 30.0]`

### 📊 GDAXI.INDX/1h · BOS_bullish
- Events: 112  ·  Baseline continuation: **28.6%**

  - 🔴 **28.6%** (8/28)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Tue`
  - 🔴 **20.0%** (2/10)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **5.6%** (1/18)
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (70.0, inf]`

### 📊 GDAXI.INDX/1h · CHoCH_bearish
- Events: 105  ·  Baseline continuation: **49.5%**

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
- Events: 105  ·  Baseline continuation: **41.9%**

  - 🟢 **76.5%** (13/17)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
      - `dow ≠ Wed`
  - 🔴 **28.6%** (4/14)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **23.1%** (3/13)
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b = (0.4, inf]`

### 📊 GDAXI.INDX/1h · bearish
- Events: 506  ·  Baseline continuation: **38.9%**

  - 🔴 **29.2%** (7/24)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **25.8%** (8/31)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `dow = Fri`
  - 🔴 **25.0%** (4/16)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **20.0%** (3/15)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **10.0%** (2/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`

### 📊 GDAXI.INDX/1h · bearish_OB
- Events: 462  ·  Baseline continuation: **65.8%**

  - 🟢 **100.0%** (12/12)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Fri`
  - 🟢 **89.5%** (17/19)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Fri`
  - 🟢 **84.6%** (22/26)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Fri`
  - 🟢 **81.2%** (13/16)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Fri`
      - `dow = Thu`
  - 🟢 **78.6%** (44/56)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (30.0, 50.0]`
      - `atr_pct_b ≠ (0.4, inf]`

### 📊 GDAXI.INDX/1h · breakdown
- Events: 246  ·  Baseline continuation: **42.7%**

  - 🟢 **80.0%** (16/20)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🟢 **72.7%** (8/11)
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Thu`
      - `rsi_b = (-inf, 30.0]`
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
- Events: 290  ·  Baseline continuation: **42.4%**

  - 🔴 **29.4%** (5/17)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b = (0.5, inf]`
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
      - `rsi_b = (70.0, inf]`
  - 🔴 **21.4%** (3/14)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 GDAXI.INDX/1h · bullish
- Events: 562  ·  Baseline continuation: **43.2%**

  - 🔴 **29.2%** (7/24)
      - `dow ≠ Thu`
      - `dow ≠ Wed`
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **28.6%** (12/42)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **25.0%** (5/20)
      - `dow = Thu`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **22.0%** (9/41)
      - `dow ≠ Thu`
      - `dow = Wed`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (2/10)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 GDAXI.INDX/1h · bullish_OB
- Events: 396  ·  Baseline continuation: **64.1%**

  - 🟢 **88.9%** (16/18)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
      - `atr_pct_b ≠ (0.15, 0.4]`
  - 🟢 **85.7%** (24/28)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **81.8%** (9/11)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Thu`
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **72.7%** (80/110)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **71.1%** (27/38)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Thu`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
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
- Events: 211  ·  Baseline continuation: **46.4%**

  - 🔴 **25.0%** (3/12)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
      - `dow = Thu`
  - 🔴 **9.1%** (1/11)
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`

### 📊 GDAXI.INDX/1h · hammer
- Events: 218  ·  Baseline continuation: **38.1%**

  - 🔴 **30.0%** (3/10)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.0%** (4/16)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **21.1%** (4/19)
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `dow ≠ Tue`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **18.2%** (2/11)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **12.5%** (2/16)
      - `vol_z_b = (-0.5, 0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b ≠ (-inf, 18.0]`

### 📊 GDAXI.INDX/1h · shooting_star
- Events: 187  ·  Baseline continuation: **36.9%**

  - 🟢 **75.0%** (9/12)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **29.3%** (24/82)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Wed`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b ≠ (70.0, inf]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (2/12)
      - `rsi_b = (70.0, inf]`

---

## USOIL.FOREX · 5m
- Candles: **10000**  ·  Swing pivots: 1391  ·  FVG: 2310
- CHoCH/BOS events: 978  ·  Order Blocks: 1721
- Trend Ladders detected: 98  ·  Candle patterns: 2030  ·  Breakouts: 1084

### S/R Cluster Seviyeleri (top 8)
- 71.5578 (touches: **656**, strong)
- 79.8776 (touches: **177**, strong)
- 76.963 (touches: **112**, strong)
- 92.9108 (touches: **60**, strong)
- 95.1304 (touches: **48**, strong)
- 93.9885 (touches: **41**, strong)
- 81.721 (touches: **29**, strong)
- 97.1878 (touches: **28**, strong)

### 🪜 Trend Ladder Analizi (98 ladder)
- Continued: 44  ·  Reversed: 39  ·  Baseline continuation: **44.9%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **81.8%** (9/11)
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
   - `before_adx_avg_bucket ≠ (-inf, 18.0]`
   - `before_rsi_avg_bucket ≠ (30.0, 50.0]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **14.3%** (2/14)
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`
   - `ladder_slope_atr_bucket ≠ (0.5, 1.0]`
   - `before_rsi_last_bucket = (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · ALL EVENTS
- Events: 7163  ·  Baseline continuation: **46.7%**

  - 🟢 **88.2%** (30/34)
      - `type = bearish_OB`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **82.9%** (68/82)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **78.3%** (130/166)
      - `type = bearish_OB`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **27.3%** (9/33)
      - `type ≠ bearish_OB`
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Wed`
  - 🔴 **26.9%** (54/201)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `dow ≠ Fri`
  - 🔴 **22.4%** (35/156)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **13.3%** (6/45)
      - `type ≠ bearish_OB`
      - `type ≠ bullish_OB`
      - `type = BOS_bearish`
      - `dow = Fri`

### 📊 USOIL.FOREX/5m · BOS_bearish
- Events: 246  ·  Baseline continuation: **24.4%**

  - 🔴 **26.7%** (4/15)
      - `dow = Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **25.0%** (5/20)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **22.4%** (19/85)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
  - 🔴 **10.0%** (1/10)
      - `dow = Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **5.0%** (1/20)
      - `dow = Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`

### 📊 USOIL.FOREX/5m · BOS_bullish
- Events: 156  ·  Baseline continuation: **22.4%**

  - 🔴 **30.0%** (18/60)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Tue`
  - 🔴 **23.1%** (3/13)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **15.0%** (3/20)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (25.0, inf]`
  - 🔴 **12.5%** (3/24)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **7.7%** (1/13)
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow = Tue`

### 📊 USOIL.FOREX/5m · CHoCH_bearish
- Events: 286  ·  Baseline continuation: **43.7%**

  - 🟢 **86.7%** (13/15)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Mon`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **22.2%** (4/18)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Thu`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Fri`
  - 🔴 **16.7%** (2/12)
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Mon`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **5.0%** (1/20)
      - `rsi_b ≠ (50.0, 70.0]`
      - `rsi_b = (-inf, 30.0]`

### 📊 USOIL.FOREX/5m · CHoCH_bullish
- Events: 288  ·  Baseline continuation: **41.7%**

  - 🟢 **100.0%** (11/11)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **86.7%** (13/15)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **70.8%** (34/48)
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Thu`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **19.2%** (5/26)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Wed`
  - 🔴 **18.5%** (12/65)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **0.0%** (0/16)
      - `rsi_b ≠ (30.0, 50.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · bearish
- Events: 1206  ·  Baseline continuation: **43.8%**

  - 🟢 **76.6%** (36/47)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
  - 🟢 **72.7%** (8/11)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b = (0.05, 0.15]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **25.8%** (33/128)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🔴 **9.7%** (3/31)
      - `rsi_b = (-inf, 30.0]`
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `dow ≠ Thu`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/5m · bearish_OB
- Events: 890  ·  Baseline continuation: **68.8%**

  - 🟢 **90.9%** (10/11)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
      - `dow = Thu`
  - 🟢 **90.7%** (49/54)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
  - 🟢 **87.0%** (20/23)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (70.0, inf]`
      - `dow ≠ Thu`
  - 🟢 **74.3%** (156/210)
      - `rsi_b ≠ (-inf, 30.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/5m · breakdown
- Events: 575  ·  Baseline continuation: **42.3%**

  - 🟢 **90.9%** (10/11)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Mon`
      - `dow = Thu`
  - 🟢 **78.6%** (11/14)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **75.0%** (9/12)
      - `atr_pct_b = (0.05, 0.15]`
      - `dow = Thu`
  - 🔴 **29.9%** (44/147)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Thu`
  - 🔴 **23.1%** (3/13)
      - `atr_pct_b ≠ (0.05, 0.15]`
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Mon`

### 📊 USOIL.FOREX/5m · breakout_up
- Events: 503  ·  Baseline continuation: **38.2%**

  - 🔴 **23.3%** (7/30)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **21.4%** (3/14)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **15.4%** (6/39)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **9.5%** (2/21)
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/5m · bullish
- Events: 1093  ·  Baseline continuation: **40.5%**

  - 🟢 **73.0%** (27/37)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Fri`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **21.1%** (4/19)
      - `rsi_b ≠ (70.0, inf]`
      - `dow = Fri`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **20.0%** (3/15)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **18.2%** (2/11)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Thu`
  - 🔴 **12.5%** (2/16)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b = (0.5, inf]`
      - `atr_pct_b = (0.4, inf]`
  - 🔴 **0.0%** (0/11)
      - `rsi_b = (70.0, inf]`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Thu`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/5m · bullish_OB
- Events: 828  ·  Baseline continuation: **64.9%**

  - 🟢 **100.0%** (15/15)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
      - `dow = Wed`
  - 🟢 **90.9%** (20/22)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Wed`
      - `dow = Tue`
  - 🟢 **82.7%** (62/75)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Mon`
  - 🟢 **73.3%** (33/45)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b = (-inf, 30.0]`
      - `dow ≠ Wed`
      - `dow ≠ Tue`
  - 🟢 **71.7%** (33/46)
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow = Tue`
  - 🔴 **11.8%** (2/17)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow = Wed`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **9.1%** (1/11)
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/5m · engulfing_bear
- Events: 129  ·  Baseline continuation: **38.8%**

  - 🔴 **18.2%** (2/11)
      - `dow ≠ Mon`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow ≠ Mon`
      - `dow ≠ Tue`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **7.1%** (1/14)
      - `dow = Mon`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/5m · engulfing_bull
- Events: 109  ·  Baseline continuation: **45.9%**

  - 🟢 **90.9%** (10/11)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **70.0%** (7/10)
      - `dow ≠ Tue`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Thu`
  - 🔴 **27.3%** (3/11)
      - `dow ≠ Tue`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `dow = Tue`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/5m · hammer
- Events: 402  ·  Baseline continuation: **39.1%**

  - 🔴 **27.3%** (3/11)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Mon`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **13.6%** (3/22)
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
      - `dow = Wed`

### 📊 USOIL.FOREX/5m · shooting_star
- Events: 452  ·  Baseline continuation: **42.7%**

  - 🟢 **73.3%** (11/15)
      - `rsi_b ≠ (-inf, 30.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
  - 🔴 **0.0%** (0/13)
      - `rsi_b = (-inf, 30.0]`
      - `vol_z_b ≠ (0.5, inf]`

---

## USOIL.FOREX · 15m
- Candles: **4557**  ·  Swing pivots: 604  ·  FVG: 938
- CHoCH/BOS events: 430  ·  Order Blocks: 800
- Trend Ladders detected: 232  ·  Candle patterns: 955  ·  Breakouts: 462

### S/R Cluster Seviyeleri (top 8)
- 73.7911 (touches: **129**, strong)
- 80.2896 (touches: **78**, strong)
- 94.8264 (touches: **73**, strong)
- 69.3874 (touches: **72**, strong)
- 101.9259 (touches: **50**, strong)
- 97.6556 (touches: **30**, strong)
- 91.5272 (touches: **26**, strong)
- 92.7893 (touches: **21**, strong)

### 🪜 Trend Ladder Analizi (232 ladder)
- Continued: 104  ·  Reversed: 85  ·  Baseline continuation: **44.8%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **76.0%** (19/25)
   - `ladder_total_atr_bucket = (1.0, 2.5]`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket = (4.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **30.0%** (6/20)
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_adx_avg_bucket = (25.0, inf]`
   - `before_rsi_last_bucket = (50.0, 70.0]`
- **15.8%** (3/19)
   - `ladder_total_atr_bucket ≠ (1.0, 2.5]`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `before_rsi_last_bucket ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · ALL EVENTS
- Events: 3120  ·  Baseline continuation: **46.9%**

  - 🟢 **91.9%** (34/37)
      - `type = bullish_OB`
      - `vol_z_b = (-inf, -0.5]`
      - `dow ≠ Fri`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🟢 **80.7%** (46/57)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
  - 🟢 **80.6%** (29/36)
      - `type = bullish_OB`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **17.2%** (5/29)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow = Wed`
      - `rsi_b = (70.0, inf]`

### 📊 USOIL.FOREX/15m · BOS_bearish
- Events: 94  ·  Baseline continuation: **23.4%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b ≠ (0.4, inf]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow = Thu`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **15.4%** (2/13)
      - `dow ≠ Thu`
      - `dow ≠ Fri`
      - `atr_pct_b = (0.4, inf]`
      - `dow = Mon`
  - 🔴 **12.5%** (2/16)
      - `dow ≠ Thu`
      - `dow = Fri`
  - 🔴 **7.7%** (1/13)
      - `dow = Thu`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/15m · BOS_bullish
- Events: 90  ·  Baseline continuation: **27.8%**

  - 🔴 **30.0%** (3/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **29.4%** (5/17)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **15.8%** (3/19)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **6.7%** (1/15)
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/15m · CHoCH_bearish
- Events: 123  ·  Baseline continuation: **41.5%**

  - 🟢 **75.0%** (9/12)
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
      - `dow = Tue`
  - 🔴 **0.0%** (0/16)
      - `dow ≠ Wed`
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/15m · CHoCH_bullish
- Events: 122  ·  Baseline continuation: **41.8%**

  - 🟢 **90.0%** (9/10)
      - `vol_z_b = (-inf, -0.5]`
      - `dow = Tue`
  - 🟢 **80.0%** (8/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **29.4%** (5/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **21.1%** (4/19)
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
- Events: 466  ·  Baseline continuation: **42.9%**

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
  - 🔴 **0.0%** (0/11)
      - `dow ≠ Fri`
      - `dow = Mon`
      - `adx_b = (-inf, 18.0]`

### 📊 USOIL.FOREX/15m · bearish_OB
- Events: 411  ·  Baseline continuation: **65.5%**

  - 🟢 **100.0%** (15/15)
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **91.3%** (21/23)
      - `dow ≠ Wed`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🟢 **81.8%** (18/22)
      - `dow ≠ Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `dow = Fri`
      - `adx_b = (25.0, inf]`
  - 🟢 **81.8%** (18/22)
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b = (25.0, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **80.0%** (8/10)
      - `dow = Wed`
      - `atr_pct_b = (0.15, 0.4]`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/15m · breakdown
- Events: 252  ·  Baseline continuation: **44.8%**

  - 🟢 **71.4%** (10/14)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (18.0, 25.0]`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Thu`
  - 🟢 **71.1%** (27/38)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow ≠ Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **30.0%** (6/20)
      - `atr_pct_b ≠ (0.4, inf]`
      - `dow = Thu`
  - 🔴 **21.1%** (4/19)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow ≠ Fri`
      - `dow = Thu`
  - 🔴 **14.3%** (2/14)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (18.0, 25.0]`
      - `dow = Fri`

### 📊 USOIL.FOREX/15m · breakout_up
- Events: 209  ·  Baseline continuation: **39.7%**

  - 🟢 **73.7%** (14/19)
      - `adx_b ≠ (25.0, inf]`
      - `dow = Tue`
  - 🟢 **72.7%** (8/11)
      - `adx_b = (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **25.8%** (8/31)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.15, 0.4]`
      - `dow ≠ Mon`
  - 🔴 **18.2%** (2/11)
      - `adx_b ≠ (25.0, inf]`
      - `dow ≠ Tue`
      - `dow = Mon`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **5.9%** (1/17)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · bullish
- Events: 466  ·  Baseline continuation: **39.9%**

  - 🔴 **27.3%** (3/11)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.15, 0.4]`
  - 🔴 **27.3%** (3/11)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **26.5%** (18/68)
      - `dow ≠ Thu`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (70.0, inf]`
  - 🔴 **20.5%** (8/39)
      - `dow ≠ Thu`
      - `dow ≠ Mon`
      - `rsi_b ≠ (50.0, 70.0]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **16.7%** (2/12)
      - `dow = Thu`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/15m · bullish_OB
- Events: 389  ·  Baseline continuation: **66.3%**

  - 🟢 **96.3%** (26/27)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow ≠ Mon`
  - 🟢 **92.3%** (12/13)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `dow = Mon`
  - 🟢 **90.0%** (18/20)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **80.0%** (8/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (-inf, 18.0]`
  - 🟢 **80.0%** (8/10)
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b ≠ (30.0, 50.0]`
      - `dow ≠ Fri`
      - `dow = Mon`

### 📊 USOIL.FOREX/15m · engulfing_bear
- Events: 48  ·  Baseline continuation: **35.4%**

  - 🔴 **20.0%** (2/10)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/15m · engulfing_bull
- Events: 62  ·  Baseline continuation: **45.2%**

  - 🟢 **71.4%** (10/14)
      - `adx_b = (-inf, 18.0]`
  - 🔴 **26.3%** (5/19)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · hammer
- Events: 213  ·  Baseline continuation: **36.2%**

  - 🔴 **30.0%** (3/10)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **22.9%** (8/35)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b = (0.4, inf]`
      - `dow ≠ Tue`
  - 🔴 **14.3%** (3/21)
      - `adx_b ≠ (25.0, inf]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **5.3%** (1/19)
      - `adx_b = (25.0, inf]`
      - `vol_z_b ≠ (-0.5, 0.5]`
      - `atr_pct_b ≠ (0.4, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/15m · shooting_star
- Events: 175  ·  Baseline continuation: **47.4%**

  - 🟢 **90.9%** (10/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🟢 **73.7%** (14/19)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b = (25.0, inf]`
  - 🟢 **72.7%** (8/11)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **16.7%** (4/24)
      - `rsi_b = (50.0, 70.0]`
      - `dow ≠ Tue`
      - `adx_b ≠ (25.0, inf]`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🔴 **7.1%** (1/14)
      - `rsi_b = (50.0, 70.0]`
      - `dow = Tue`
      - `adx_b = (25.0, inf]`

---

## USOIL.FOREX · 30m
- Candles: **3883**  ·  Swing pivots: 486  ·  FVG: 800
- CHoCH/BOS events: 346  ·  Order Blocks: 669
- Trend Ladders detected: 200  ·  Candle patterns: 918  ·  Breakouts: 406

### S/R Cluster Seviyeleri (top 8)
- 95.5139 (touches: **233**, strong)
- 70.8373 (touches: **80**, strong)
- 103.8493 (touches: **46**, strong)
- 79.7623 (touches: **41**, strong)
- 75.6184 (touches: **23**, strong)
- 108.9148 (touches: **15**, strong)
- 107.0262 (touches: **13**, strong)
- 86.982 (touches: **5**, strong)

### 🪜 Trend Ladder Analizi (200 ladder)
- Continued: 83  ·  Reversed: 83  ·  Baseline continuation: **41.5%**

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **21.1%** (4/19)
   - `before_rsi_last_bucket ≠ (70.0, inf]`
   - `before_rsi_last_bucket ≠ (30.0, 50.0]`
   - `ladder_slope_atr_bucket = (0.5, 1.0]`

### 📊 USOIL.FOREX/30m · ALL EVENTS
- Events: 2730  ·  Baseline continuation: **48.5%**

  - 🟢 **93.3%** (14/15)
      - `type = bullish_OB`
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **93.3%** (14/15)
      - `type = bullish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Mon`
  - 🟢 **84.2%** (16/19)
      - `type = bullish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **83.3%** (40/48)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **74.6%** (47/63)
      - `type = bullish_OB`
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Mon`
  - 🔴 **25.7%** (27/105)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow = Mon`
      - `type = bullish`
  - 🔴 **23.6%** (13/55)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `dow ≠ Mon`
      - `type = BOS_bearish`

### 📊 USOIL.FOREX/30m · BOS_bearish
- Events: 73  ·  Baseline continuation: **24.7%**

  - 🔴 **20.0%** (2/10)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b ≠ (30.0, 50.0]`
  - 🔴 **15.4%** (2/13)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Thu`
      - `vol_z_b = (0.5, inf]`
      - `rsi_b = (30.0, 50.0]`
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
- Events: 101  ·  Baseline continuation: **43.6%**

  - 🟢 **76.9%** (10/13)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (8/32)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `rsi_b ≠ (-inf, 30.0]`
  - 🔴 **10.0%** (1/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `dow ≠ Tue`
      - `dow ≠ Mon`
      - `rsi_b = (-inf, 30.0]`

### 📊 USOIL.FOREX/30m · CHoCH_bullish
- Events: 101  ·  Baseline continuation: **44.6%**

  - 🔴 **30.0%** (9/30)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **10.0%** (1/10)
      - `rsi_b = (70.0, inf]`

### 📊 USOIL.FOREX/30m · bearish
- Events: 385  ·  Baseline continuation: **43.6%**

  - 🟢 **85.7%** (12/14)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Fri`
  - 🟢 **73.3%** (11/15)
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Fri`
      - `dow = Thu`
  - 🟢 **70.6%** (12/17)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Tue`
      - `rsi_b = (-inf, 30.0]`
  - 🔴 **20.8%** (5/24)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Tue`
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`

### 📊 USOIL.FOREX/30m · bearish_OB
- Events: 324  ·  Baseline continuation: **64.2%**

  - 🟢 **92.3%** (12/13)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **91.7%** (11/12)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **82.6%** (19/23)
      - `dow ≠ Tue`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **81.8%** (9/11)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `rsi_b ≠ (50.0, 70.0]`
      - `vol_z_b ≠ (-0.5, 0.5]`
  - 🟢 **73.7%** (14/19)
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **26.3%** (5/19)
      - `dow ≠ Tue`
      - `dow = Fri`
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · breakdown
- Events: 181  ·  Baseline continuation: **45.9%**

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
- Events: 223  ·  Baseline continuation: **49.8%**

  - 🟢 **92.3%** (12/13)
      - `dow = Wed`
      - `adx_b ≠ (25.0, inf]`
  - 🟢 **73.3%** (11/15)
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **71.4%** (15/21)
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `dow = Fri`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **26.7%** (4/15)
      - `dow ≠ Wed`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Wed`
      - `dow = Mon`
      - `vol_z_b ≠ (0.5, inf]`
      - `rsi_b ≠ (50.0, 70.0]`

### 📊 USOIL.FOREX/30m · bullish
- Events: 412  ·  Baseline continuation: **41.5%**

  - 🔴 **30.0%** (3/10)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **28.9%** (11/38)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **20.0%** (3/15)
      - `dow = Mon`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (-inf, 18.0]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **18.8%** (3/16)
      - `dow = Mon`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **13.6%** (3/22)
      - `dow ≠ Mon`
      - `rsi_b = (30.0, 50.0]`
      - `dow ≠ Wed`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/30m · bullish_OB
- Events: 345  ·  Baseline continuation: **69.6%**

  - 🟢 **100.0%** (10/10)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow = Thu`
  - 🟢 **93.3%** (14/15)
      - `atr_pct_b ≠ (0.4, inf]`
  - 🟢 **93.3%** (14/15)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b = (-inf, 18.0]`
      - `dow ≠ Thu`
      - `dow = Mon`
  - 🟢 **84.2%** (16/19)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (70.0, inf]`
  - 🟢 **71.1%** (64/90)
      - `atr_pct_b = (0.4, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b ≠ (70.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/30m · engulfing_bear
- Events: 77  ·  Baseline continuation: **40.3%**

  - 🔴 **17.6%** (3/17)
      - `adx_b ≠ (25.0, inf]`
      - `vol_z_b = (0.5, inf]`

### 📊 USOIL.FOREX/30m · engulfing_bull
- Events: 87  ·  Baseline continuation: **48.3%**

  - 🟢 **84.6%** (11/13)
      - `rsi_b = (70.0, inf]`
  - 🔴 **15.8%** (3/19)
      - `rsi_b ≠ (70.0, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (-0.5, 0.5]`

### 📊 USOIL.FOREX/30m · hammer
- Events: 185  ·  Baseline continuation: **44.3%**

  - 🔴 **26.1%** (6/23)
      - `dow ≠ Fri`
      - `adx_b = (25.0, inf]`
      - `dow ≠ Wed`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **18.8%** (3/16)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`

### 📊 USOIL.FOREX/30m · shooting_star
- Events: 166  ·  Baseline continuation: **38.6%**

  - 🔴 **29.4%** (5/17)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **27.8%** (5/18)
      - `vol_z_b ≠ (0.5, inf]`
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
  - 🔴 **25.0%** (3/12)
      - `vol_z_b = (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **8.3%** (1/12)
      - `vol_z_b = (0.5, inf]`
      - `adx_b = (-inf, 18.0]`

---

## USOIL.FOREX · 1h
- Candles: **2794**  ·  Swing pivots: 383  ·  FVG: 628
- CHoCH/BOS events: 259  ·  Order Blocks: 543
- Trend Ladders detected: 126  ·  Candle patterns: 816  ·  Breakouts: 286

### S/R Cluster Seviyeleri (top 8)
- 96.5701 (touches: **187**, strong)
- 66.8214 (touches: **86**, strong)
- 77.0561 (touches: **32**, strong)
- 72.8882 (touches: **16**, strong)
- 86.9386 (touches: **14**, strong)
- 74.6887 (touches: **11**, strong)
- 80.85 (touches: **7**, strong)
- 79.434 (touches: **5**, strong)

### 🪜 Trend Ladder Analizi (126 ladder)
- Continued: 58  ·  Reversed: 52  ·  Baseline continuation: **46.0%**

**🟢 Ladder devam etme ihtimali yüksek olan koşullar:**
- **82.4%** (14/17)
   - `direction ≠ down`
   - `before_adx_avg_bucket ≠ (25.0, inf]`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`

**🔴 Ladder devam etme ihtimali düşük olan koşullar (reverse adayı):**
- **29.4%** (5/17)
   - `direction = down`
   - `start_dist_ema50_atr_bucket ≠ (1.0, inf]`
   - `before_adx_avg_bucket ≠ (18.0, 25.0]`
- **27.3%** (3/11)
   - `direction = down`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket = (2.0, 4.0]`
- **18.2%** (2/11)
   - `direction = down`
   - `start_dist_ema50_atr_bucket = (1.0, inf]`
   - `before_bb_width_atr_avg_bucket ≠ (2.0, 4.0]`

### 📊 USOIL.FOREX/1h · ALL EVENTS
- Events: 2170  ·  Baseline continuation: **44.9%**

  - 🟢 **94.4%** (17/18)
      - `type = bullish_OB`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **77.8%** (49/63)
      - `type ≠ bullish_OB`
      - `type = bearish_OB`
      - `dow ≠ Fri`
      - `vol_z_b = (0.5, inf]`
  - 🟢 **75.0%** (12/16)
      - `type = bullish_OB`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **16.7%** (8/48)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type ≠ BOS_bearish`
      - `type = BOS_bullish`
  - 🔴 **16.7%** (6/36)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `adx_b ≠ (18.0, 25.0]`
  - 🔴 **11.1%** (2/18)
      - `type ≠ bullish_OB`
      - `type ≠ bearish_OB`
      - `type = BOS_bearish`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · BOS_bearish
- Events: 54  ·  Baseline continuation: **14.8%**

  - 🔴 **15.4%** (2/13)
      - `dow ≠ Tue`
      - `dow = Thu`
  - 🔴 **8.3%** (1/12)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `adx_b = (18.0, 25.0]`
  - 🔴 **0.0%** (0/18)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `adx_b ≠ (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · BOS_bullish
- Events: 48  ·  Baseline continuation: **16.7%**

  - 🔴 **30.0%** (3/10)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `dow = Mon`
  - 🔴 **6.7%** (1/15)
      - `dow ≠ Tue`
      - `dow ≠ Thu`
      - `dow ≠ Mon`
  - 🔴 **0.0%** (0/11)
      - `dow = Tue`

### 📊 USOIL.FOREX/1h · CHoCH_bearish
- Events: 78  ·  Baseline continuation: **50.0%**

  - 🟢 **86.7%** (13/15)
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **25.0%** (6/24)
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b ≠ (25.0, inf]`

### 📊 USOIL.FOREX/1h · CHoCH_bullish
- Events: 78  ·  Baseline continuation: **37.2%**

  - 🔴 **30.0%** (3/10)
      - `rsi_b ≠ (50.0, 70.0]`
      - `adx_b ≠ (-inf, 18.0]`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **27.3%** (3/11)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **15.4%** (2/13)
      - `rsi_b = (50.0, 70.0]`
      - `adx_b = (18.0, 25.0]`

### 📊 USOIL.FOREX/1h · bearish
- Events: 286  ·  Baseline continuation: **39.2%**

  - 🟢 **80.0%** (12/15)
      - `dow = Tue`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **70.0%** (7/10)
      - `dow = Tue`
      - `adx_b ≠ (18.0, 25.0]`
      - `vol_z_b = (-0.5, 0.5]`
  - 🔴 **29.5%** (18/61)
      - `dow ≠ Tue`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow ≠ Sun`
      - `adx_b = (25.0, inf]`
  - 🔴 **20.0%** (2/10)
      - `dow ≠ Tue`
      - `rsi_b = (-inf, 30.0]`
      - `adx_b ≠ (25.0, inf]`
  - 🔴 **8.3%** (1/12)
      - `dow ≠ Tue`
      - `rsi_b ≠ (-inf, 30.0]`
      - `dow = Sun`
  - 🔴 **8.3%** (1/12)
      - `dow ≠ Tue`
      - `rsi_b = (-inf, 30.0]`
      - `adx_b = (25.0, inf]`

### 📊 USOIL.FOREX/1h · bearish_OB
- Events: 275  ·  Baseline continuation: **62.5%**

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
      - `vol_z_b ≠ (-0.5, 0.5]`
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
- Events: 110  ·  Baseline continuation: **30.0%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Tue`
      - `dow = Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **15.4%** (4/26)
      - `dow ≠ Tue`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **6.7%** (1/15)
      - `dow ≠ Tue`
      - `dow ≠ Wed`
      - `dow ≠ Mon`
      - `vol_z_b ≠ (0.5, inf]`

### 📊 USOIL.FOREX/1h · breakout_up
- Events: 172  ·  Baseline continuation: **40.7%**

  - 🟢 **100.0%** (15/15)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🟢 **70.0%** (7/10)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `rsi_b = (50.0, 70.0]`
  - 🔴 **29.4%** (5/17)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow = Thu`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Fri`
      - `dow = Wed`
      - `vol_z_b ≠ (0.5, inf]`
  - 🔴 **28.1%** (9/32)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow = Tue`
  - 🔴 **18.2%** (6/33)
      - `dow ≠ Fri`
      - `dow ≠ Wed`
      - `dow ≠ Thu`
      - `dow ≠ Tue`

### 📊 USOIL.FOREX/1h · bullish
- Events: 337  ·  Baseline continuation: **42.7%**

  - 🟢 **84.6%** (11/13)
      - `vol_z_b = (0.5, inf]`
      - `dow = Fri`
  - 🟢 **70.0%** (14/20)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Wed`
      - `vol_z_b = (-0.5, 0.5]`
  - 🟢 **70.0%** (7/10)
      - `vol_z_b = (0.5, inf]`
      - `dow ≠ Fri`
      - `adx_b ≠ (25.0, inf]`
      - `dow = Thu`
  - 🔴 **25.4%** (30/118)
      - `vol_z_b ≠ (0.5, inf]`
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Wed`
      - `rsi_b ≠ (70.0, inf]`

### 📊 USOIL.FOREX/1h · bullish_OB
- Events: 268  ·  Baseline continuation: **65.7%**

  - 🟢 **94.4%** (17/18)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b ≠ (18.0, 25.0]`
  - 🟢 **85.7%** (12/14)
      - `dow ≠ Fri`
      - `rsi_b = (-inf, 30.0]`
  - 🟢 **75.0%** (12/16)
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `adx_b = (18.0, 25.0]`
  - 🟢 **72.7%** (8/11)
      - `dow = Fri`
      - `vol_z_b = (-inf, -0.5]`
      - `rsi_b = (30.0, 50.0]`

### 📊 USOIL.FOREX/1h · engulfing_bear
- Events: 89  ·  Baseline continuation: **37.1%**

  - 🟢 **72.7%** (8/11)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow ≠ Wed`
      - `adx_b = (25.0, inf]`
  - 🔴 **28.6%** (4/14)
      - `dow ≠ Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
      - `dow = Wed`
  - 🔴 **12.5%** (2/16)
      - `dow = Fri`

### 📊 USOIL.FOREX/1h · engulfing_bull
- Events: 101  ·  Baseline continuation: **39.6%**

  - 🟢 **72.2%** (13/18)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow ≠ Tue`
      - `rsi_b = (30.0, 50.0]`
      - `adx_b = (25.0, inf]`
  - 🔴 **25.0%** (3/12)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🔴 **25.0%** (3/12)
      - `adx_b = (-inf, 18.0]`
      - `vol_z_b = (-inf, -0.5]`
  - 🔴 **14.3%** (2/14)
      - `adx_b ≠ (-inf, 18.0]`
      - `dow = Tue`

### 📊 USOIL.FOREX/1h · hammer
- Events: 142  ·  Baseline continuation: **43.0%**

  - 🟢 **72.2%** (13/18)
      - `dow ≠ Wed`
      - `dow = Fri`
      - `vol_z_b ≠ (-inf, -0.5]`
  - 🟢 **70.0%** (14/20)
      - `dow = Wed`
  - 🔴 **25.0%** (3/12)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `dow = Tue`
      - `rsi_b ≠ (50.0, 70.0]`
  - 🔴 **22.2%** (8/36)
      - `dow ≠ Wed`
      - `dow ≠ Fri`
      - `dow ≠ Tue`
      - `dow ≠ Thu`

### 📊 USOIL.FOREX/1h · shooting_star
- Events: 132  ·  Baseline continuation: **37.9%**

  - 🔴 **27.3%** (3/11)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b ≠ (-inf, 18.0]`
  - 🔴 **23.1%** (3/13)
      - `dow = Mon`
      - `vol_z_b = (0.5, inf]`
  - 🔴 **18.2%** (2/11)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b ≠ (18.0, 25.0]`
      - `adx_b = (-inf, 18.0]`
  - 🔴 **8.3%** (1/12)
      - `dow ≠ Mon`
      - `vol_z_b = (-0.5, 0.5]`
      - `adx_b = (18.0, 25.0]`

---
