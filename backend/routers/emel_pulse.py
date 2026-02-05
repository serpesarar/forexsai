"""
EMEL + PULSE Panel API Endpoints
- EMEL: 9 kontrol noktalı stratejik analiz
- PULSE: Hızlı scalp analizi
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/panel", tags=["Panel Analysis"])


# ═══════════════════════════════════════════════════════════════════════════════
# EMEL PANEL - 9 KONTROL NOKTASI
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/emel/{symbol}")
async def get_emel_analysis(symbol: str, timeframe: str = "1H"):
    """
    EMEL Panel - 9 Kontrol Noktası ile Detaylı Analiz
    """
    try:
        from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
        from services.market_data_service import get_ohlcv_data
        
        # Get market data
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=250)
        if not ohlcv or len(ohlcv) < 50:
            return {"error": "Yetersiz veri"}
        
        # Convert to numpy arrays - CRITICAL for correct EMA calculation
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        current_price = float(closes[-1])
        
        # Calculate TA with numpy arrays
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # Get ML prediction for context
        prediction = await get_ml_prediction(symbol, "balanced")
        
        # Build 9 checkpoints
        checks = []
        green_count = 0
        yellow_count = 0
        red_count = 0
        
        # ─────────────────────────────────────────────────────────────────────
        # 1️⃣ TREND ANALİZİ (EMA 20/50/200)
        # ─────────────────────────────────────────────────────────────────────
        ema_20 = ta.get("ema_20", current_price)
        ema_50 = ta.get("ema_50", current_price)
        ema_200 = ta.get("ema_200", current_price)
        
        price_above_ema20 = current_price > ema_20
        ema20_above_ema50 = ema_20 > ema_50
        ema50_above_ema200 = ema_50 > ema_200
        
        if price_above_ema20 and ema20_above_ema50 and ema50_above_ema200:
            trend_status = "pass"
            trend_direction = "up"
            trend_color = "green"
            trend_label = "YUKARI YÖN"
            trend_comment = "Kısa ve orta vadeli trend yukarı. EMA50 yakın destek olarak çalışabilir."
            green_count += 1
        elif not price_above_ema20 and not ema20_above_ema50 and not ema50_above_ema200:
            trend_status = "fail"
            trend_direction = "down"
            trend_color = "red"
            trend_label = "AŞAĞI YÖN"
            trend_comment = "Trend aşağı yönlü. EMA50 direnç konumunda."
            red_count += 1
        else:
            trend_status = "warning"
            trend_direction = "neutral"
            trend_color = "yellow"
            trend_label = "KARIŞIK"
            trend_comment = "EMA'lar karışık sinyal veriyor. Net bir yön yok."
            yellow_count += 1
        
        checks.append({
            "id": 1,
            "name": "Trend Analizi",
            "subtitle": "EMA 20/50/200",
            "status": trend_status,
            "direction": trend_direction,
            "color": trend_color,
            "label": trend_label,
            "details": {
                "ema20": round(ema_20, 2),
                "ema50": round(ema_50, 2),
                "ema200": round(ema_200, 2),
                "price_vs_ema20": "üzerinde" if price_above_ema20 else "altında"
            },
            "comment": trend_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 2️⃣ REJİM TESPİTİ (ADX + Yapı)
        # ─────────────────────────────────────────────────────────────────────
        adx_val = ta.get("adx", 20)
        
        if adx_val >= 25:
            regime_status = "pass"
            regime_color = "green"
            regime_label = "GÜÇLÜ TREND"
            regime_comment = "ADX güçlü trend gösteriyor. Trend takip stratejileri uygun."
            green_count += 1
        elif adx_val >= 18:
            regime_status = "warning"
            regime_color = "yellow"
            regime_label = "ZAYIF TREND"
            regime_comment = "Trend gücü zayıf. Büyük pozisyonlar için beklemek daha güvenli."
            yellow_count += 1
        else:
            regime_status = "fail"
            regime_color = "red"
            regime_label = "YATAY PİYASA"
            regime_comment = "Piyasa yatay seyrediyor. Range stratejileri düşün."
            red_count += 1
        
        checks.append({
            "id": 2,
            "name": "Rejim Tespiti",
            "subtitle": "ADX + Yapı",
            "status": regime_status,
            "direction": "neutral",
            "color": regime_color,
            "label": regime_label,
            "details": {
                "adx": round(adx_val, 1),
                "strength": "Güçlü" if adx_val >= 25 else "Zayıf" if adx_val >= 18 else "Yok"
            },
            "comment": regime_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 3️⃣ MULTI-TIMEFRAME UYUMU
        # ─────────────────────────────────────────────────────────────────────
        mtf_data = prediction.get("mtf_data", {})
        mtf_checks = []
        mtf_conflicts = 0
        
        for tf in ["1D", "4H", "1H", "15m"]:
            tf_trend = mtf_data.get(tf, {}).get("trend", "NEUTRAL")
            if tf_trend == "UP":
                mtf_checks.append({"tf": tf, "dir": "up", "icon": "🟢"})
            elif tf_trend == "DOWN":
                mtf_checks.append({"tf": tf, "dir": "down", "icon": "🔴"})
                if tf in ["4H", "1H"]:
                    mtf_conflicts += 1
            else:
                mtf_checks.append({"tf": tf, "dir": "neutral", "icon": "🟡"})
        
        if mtf_conflicts == 0:
            mtf_status = "pass"
            mtf_color = "green"
            mtf_label = "UYUMLU"
            mtf_comment = "Tüm zaman dilimleri aynı yönü gösteriyor."
            green_count += 1
        elif mtf_conflicts == 1:
            mtf_status = "warning"
            mtf_color = "yellow"
            mtf_label = "KISMI UYUM"
            mtf_comment = "Bazı zaman dilimlerinde çelişki var. Dikkatli ol."
            yellow_count += 1
        else:
            mtf_status = "fail"
            mtf_color = "red"
            mtf_label = "ÇELİŞKİLİ"
            mtf_comment = "4H ve 1H ana trende karşı. BEKLE tavsiyesi."
            red_count += 1
        
        checks.append({
            "id": 3,
            "name": "Multi-Timeframe Uyumu",
            "subtitle": "1D/4H/1H/15m",
            "status": mtf_status,
            "direction": "neutral",
            "color": mtf_color,
            "label": mtf_label,
            "details": {"timeframes": mtf_checks},
            "comment": mtf_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 4️⃣ FORMASYON ANALİZİ
        # ─────────────────────────────────────────────────────────────────────
        patterns = prediction.get("active_patterns", [])
        if patterns and len(patterns) > 0:
            top_pattern = patterns[0] if isinstance(patterns[0], dict) else {"name": str(patterns[0])}
            pattern_name = top_pattern.get("name", "Bilinmiyor")
            pattern_completion = top_pattern.get("completion", 80)
            pattern_direction = top_pattern.get("direction", "neutral")
            
            if pattern_completion >= 85:
                pattern_status = "pass"
                pattern_color = "green"
                pattern_label = f"{pattern_name.upper()}"
                pattern_comment = f"Formasyon onaylandı. Hedef ve stop seviyeleri belirlendi."
                green_count += 1
            else:
                pattern_status = "warning"
                pattern_color = "yellow"
                pattern_label = f"{pattern_name.upper()} (Oluşuyor)"
                pattern_comment = f"Formasyon %{pattern_completion} tamamlandı. Onay bekliyor."
                yellow_count += 1
        else:
            pattern_status = "warning"
            pattern_color = "yellow"
            pattern_label = "FORMASYON YOK"
            pattern_comment = "Aktif formasyon tespit edilmedi."
            yellow_count += 1
            pattern_completion = 0
        
        checks.append({
            "id": 4,
            "name": "Formasyon Analizi",
            "subtitle": "Pattern Recognition",
            "status": pattern_status,
            "direction": "neutral",
            "color": pattern_color,
            "label": pattern_label,
            "details": {
                "completion": pattern_completion,
                "patterns_found": len(patterns)
            },
            "comment": pattern_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 5️⃣ DESTEK/DİRENÇ SEVİYELERİ
        # ─────────────────────────────────────────────────────────────────────
        boll_upper = ta.get("boll_upper", current_price * 1.02)
        boll_lower = ta.get("boll_lower", current_price * 0.98)
        boll_middle = ta.get("boll_middle", current_price)
        
        # Calculate pivot points
        high_20 = max(highs[-20:])
        low_20 = min(lows[-20:])
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        s1 = 2 * pivot - high_20
        
        dist_to_support = current_price - s1
        dist_to_resistance = r1 - current_price
        
        if dist_to_support < dist_to_resistance * 0.5:
            sr_status = "pass"
            sr_color = "green"
            sr_label = "DESTEK YAKINI"
            sr_comment = f"Destek bölgesine yakın ({dist_to_support:.0f} pts). Buradan dönüş olabilir."
            green_count += 1
        elif dist_to_resistance < dist_to_support * 0.5:
            sr_status = "fail"
            sr_color = "red"
            sr_label = "DİRENÇ YAKINI"
            sr_comment = f"Direnç bölgesine yakın ({dist_to_resistance:.0f} pts). Satış baskısı gelebilir."
            red_count += 1
        else:
            sr_status = "warning"
            sr_color = "yellow"
            sr_label = "ORTADA"
            sr_comment = "Fiyat destek ve direnç arasında ortada."
            yellow_count += 1
        
        checks.append({
            "id": 5,
            "name": "Destek/Direnç Seviyeleri",
            "subtitle": "S/R + Pivot",
            "status": sr_status,
            "direction": "neutral",
            "color": sr_color,
            "label": sr_label,
            "details": {
                "price": round(current_price, 2),
                "s1": round(s1, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "dist_support": round(dist_to_support, 1),
                "dist_resistance": round(dist_to_resistance, 1)
            },
            "comment": sr_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 6️⃣ MOMENTUM GÖSTERGELERİ
        # ─────────────────────────────────────────────────────────────────────
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        stoch_k = ta.get("stoch_k", 50)
        
        bullish_momentum = rsi_14 > 50 and macd_hist > 0 and stoch_k > 50
        bearish_momentum = rsi_14 < 50 and macd_hist < 0 and stoch_k < 50
        
        if bullish_momentum:
            mom_status = "pass"
            mom_color = "green"
            mom_label = "YUKARI MOMENTUM"
            mom_comment = "Tüm momentum göstergeleri yukarı yönlü."
            green_count += 1
        elif bearish_momentum:
            mom_status = "fail"
            mom_color = "red"
            mom_label = "AŞAĞI MOMENTUM"
            mom_comment = "Tüm momentum göstergeleri aşağı yönlü."
            red_count += 1
        else:
            mom_status = "warning"
            mom_color = "yellow"
            mom_label = "KARARSIZ"
            mom_comment = "Momentum göstergeleri kararsız. Net bir yön yok."
            yellow_count += 1
        
        checks.append({
            "id": 6,
            "name": "Momentum Göstergeleri",
            "subtitle": "RSI/MACD/Stoch",
            "status": mom_status,
            "direction": "up" if bullish_momentum else "down" if bearish_momentum else "neutral",
            "color": mom_color,
            "label": mom_label,
            "details": {
                "rsi": round(rsi_14, 1),
                "macd_hist": round(macd_hist, 4),
                "stoch_k": round(stoch_k, 1)
            },
            "comment": mom_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 7️⃣ HACİM ANALİZİ
        # ─────────────────────────────────────────────────────────────────────
        if volumes and sum(volumes) > 0:
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio >= 1.2:
                vol_status = "pass"
                vol_color = "green"
                vol_label = "YÜKSEK HACİM"
                vol_comment = "Hacim ortalamanın üzerinde. Hareket güçlü."
                green_count += 1
            elif volume_ratio >= 0.8:
                vol_status = "warning"
                vol_color = "yellow"
                vol_label = "NORMAL HACİM"
                vol_comment = "Hacim ortalama seviyede."
                yellow_count += 1
            else:
                vol_status = "fail"
                vol_color = "red"
                vol_label = "DÜŞÜK HACİM"
                vol_comment = "Düşük hacimli hareket güvenilmez. Hacim artmadan işlem açma."
                red_count += 1
        else:
            vol_status = "warning"
            vol_color = "yellow"
            vol_label = "VERİ YOK"
            vol_comment = "Hacim verisi mevcut değil."
            yellow_count += 1
            volume_ratio = 1
        
        checks.append({
            "id": 7,
            "name": "Hacim Analizi",
            "subtitle": "Volume",
            "status": vol_status,
            "direction": "neutral",
            "color": vol_color,
            "label": vol_label,
            "details": {
                "ratio": round(volume_ratio * 100, 0),
                "trend": "Artıyor" if volume_ratio > 1 else "Azalıyor"
            },
            "comment": vol_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 8️⃣ LEARNING / GEÇMİŞ PERFORMANS
        # ─────────────────────────────────────────────────────────────────────
        learning_data = prediction.get("learning_insights", {})
        win_rate = learning_data.get("win_rate", 50)
        sample_count = learning_data.get("sample_count", 0)
        
        if win_rate >= 60 and sample_count >= 5:
            learn_status = "pass"
            learn_color = "green"
            learn_label = "İYİ GEÇMİŞ"
            learn_comment = f"Benzer setup'larda %{win_rate:.0f} başarı ({sample_count} örnek)."
            green_count += 1
        elif win_rate >= 45:
            learn_status = "warning"
            learn_color = "yellow"
            learn_label = "ORTA RİSK"
            learn_comment = f"Geçmiş performans ortalama (%{win_rate:.0f})."
            yellow_count += 1
        else:
            learn_status = "fail"
            learn_color = "red"
            learn_label = "DÜŞÜK BAŞARI"
            learn_comment = f"Benzer setup'larda düşük başarı (%{win_rate:.0f}). Dikkatli ol."
            red_count += 1
        
        checks.append({
            "id": 8,
            "name": "Learning / Geçmiş Performans",
            "subtitle": "Historical Analysis",
            "status": learn_status,
            "direction": "neutral",
            "color": learn_color,
            "label": learn_label,
            "details": {
                "win_rate": round(win_rate, 1),
                "samples": sample_count
            },
            "comment": learn_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # 9️⃣ PORTFÖY RİSK YÖNETİMİ
        # ─────────────────────────────────────────────────────────────────────
        portfolio_risk = prediction.get("portfolio_risk", {})
        current_risk = portfolio_risk.get("current_risk_pct", 0)
        daily_limit = portfolio_risk.get("daily_limit_pct", 3)
        
        if current_risk < daily_limit * 0.5:
            port_status = "pass"
            port_color = "green"
            port_label = "UYGUN"
            port_comment = f"Portföy risk limitleri uygun. Yeni pozisyona izin veriliyor."
            green_count += 1
        elif current_risk < daily_limit:
            port_status = "warning"
            port_color = "yellow"
            port_label = "DİKKAT"
            port_comment = f"Risk limiti %{current_risk:.1f}/{daily_limit}. Küçük pozisyon al."
            yellow_count += 1
        else:
            port_status = "fail"
            port_color = "red"
            port_label = "LİMİT AŞILDI"
            port_comment = f"Günlük risk limiti aşıldı. Yeni pozisyon açma."
            red_count += 1
        
        checks.append({
            "id": 9,
            "name": "Portföy Risk Yönetimi",
            "subtitle": "Risk Management",
            "status": port_status,
            "direction": "neutral",
            "color": port_color,
            "label": port_label,
            "details": {
                "current_risk": round(current_risk, 1),
                "daily_limit": daily_limit
            },
            "comment": port_comment
        })
        
        # ─────────────────────────────────────────────────────────────────────
        # KARAR ÖZETİ
        # ─────────────────────────────────────────────────────────────────────
        signal = prediction.get("direction", "HOLD")
        confidence = prediction.get("confidence", 50)
        
        # Determine final decision
        if red_count >= 3:
            decision = "HOLD"
            decision_reason = "Çok fazla risk faktörü var"
        elif green_count >= 6:
            decision = signal if signal != "HOLD" else "BUY" if trend_direction == "up" else "SELL"
        else:
            decision = "HOLD"
            decision_reason = "Yeterli onay yok"
        
        # Build rejection reasons
        rejections = []
        for check in checks:
            if check["status"] == "fail":
                rejections.append(f"✗ {check['name']}: {check['label']}")
        
        # Build conditions for entry
        conditions = []
        if mtf_status != "pass":
            conditions.append("MTF uyumu sağlanmalı")
        if mom_status != "pass":
            conditions.append("Momentum onayı gerekli")
        if vol_status == "fail":
            conditions.append("Hacim artmalı")
        
        # ─────────────────────────────────────────────────────────────────────
        # LEARNING ENTEGRASYONU - Sinyali kaydet
        # ─────────────────────────────────────────────────────────────────────
        if decision in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                
                context = {
                    "ta": ta,
                    "source": "EMEL",
                    "checks_summary": {
                        "green": green_count,
                        "yellow": yellow_count,
                        "red": red_count
                    },
                    "ml_prediction": {
                        "direction": signal,
                        "confidence": confidence,
                        "entry_price": current_price,
                        "target_price": prediction.get("target_price"),
                        "stop_price": prediction.get("stop_price")
                    }
                }
                
                analysis = {
                    "final_decision": decision,
                    "confidence": confidence,
                    "model_used": "EMEL-9-Check"
                }
                
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe=timeframe,
                    strategy="EMEL"
                )
                logger.info(f"EMEL signal logged: {symbol} {decision} @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log EMEL prediction: {log_err}")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "signal": decision,
            "confidence": confidence,
            "price": current_price,
            "checks": checks,
            "summary": {
                "green_count": green_count,
                "yellow_count": yellow_count,
                "red_count": red_count,
                "total": 9,
                "decision": decision,
                "rejections": rejections,
                "entry_conditions": conditions
            }
        }
        
    except Exception as e:
        logger.error(f"EMEL analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE PANEL - HIZLI SCALP ANALİZİ
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pulse/{symbol}")
async def get_pulse_analysis(symbol: str, timeframe: str = "5m"):
    """
    PULSE Panel - Anlık Scalp Analizi
    """
    try:
        from services.ml_prediction_service import _compute_technical_indicators
        from services.market_data_service import get_ohlcv_data
        
        # Get market data
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 20:
            return {"error": "Yetersiz veri"}
        
        # Convert to numpy arrays for correct calculation
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        current_price = float(closes[-1])
        
        # Calculate TA
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # Last 5 candles direction
        last_5 = []
        for i in range(-5, 0):
            if closes[i] > closes[i-1]:
                last_5.append("up")
            elif closes[i] < closes[i-1]:
                last_5.append("down")
            else:
                last_5.append("neutral")
        
        up_count = last_5.count("up")
        down_count = last_5.count("down")
        
        # Trend strength (0-1)
        if up_count > down_count:
            trend_direction = "up"
            trend_strength = (up_count / 5) * (1 + (ta.get("rsi_14", 50) - 50) / 100)
        elif down_count > up_count:
            trend_direction = "down"
            trend_strength = (down_count / 5) * (1 + (50 - ta.get("rsi_14", 50)) / 100)
        else:
            trend_direction = "neutral"
            trend_strength = 0.5
        
        trend_strength = min(1.0, max(0.0, trend_strength))
        
        # Support/Resistance levels
        high_20 = max(highs[-20:])
        low_20 = min(lows[-20:])
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        r2 = pivot + (high_20 - low_20)
        s1 = 2 * pivot - high_20
        s2 = pivot - (high_20 - low_20)
        
        # Distance to nearest level
        dist_s1 = current_price - s1
        dist_r1 = r1 - current_price
        
        nearest_level = "s1" if dist_s1 < dist_r1 else "r1"
        nearest_distance = min(dist_s1, dist_r1)
        
        # Momentum indicators
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        stoch_k = ta.get("stoch_k", 50)
        
        rsi_trend = "up" if rsi_14 > 50 else "down" if rsi_14 < 50 else "neutral"
        macd_trend = "up" if macd_hist > 0 else "down"
        stoch_trend = "up" if stoch_k > 50 else "down"
        
        # Volume analysis
        if volumes and sum(volumes) > 0:
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_status = "high" if current_volume > avg_volume else "low"
        else:
            volume_status = "unknown"
        
        # Generate suggestion
        if trend_direction == "up" and trend_strength > 0.6:
            suggestion_text = f"Yukarı momentum güçlü. S1 ({s1:.0f}) üzerinde tutunma sağlandıkça kısa vadeli AL denenebilir. Hedef R1 ({r1:.0f})."
            target = r1
            stop = s1
        elif trend_direction == "down" and trend_strength > 0.6:
            suggestion_text = f"Aşağı momentum güçlü. R1 ({r1:.0f}) altında kaldıkça kısa vadeli SAT denenebilir. Hedef S1 ({s1:.0f})."
            target = s1
            stop = r1
        else:
            suggestion_text = "Momentum zayıf veya kararsız. Scalp için uygun değil. Bekle."
            target = r1 if trend_direction == "up" else s1
            stop = s1 if trend_direction == "up" else r1
        
        # R/R ratio
        potential_profit = abs(target - current_price)
        potential_loss = abs(current_price - stop)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # Sinyal yönünü belirle
        pulse_signal = "HOLD"
        if trend_direction == "up" and trend_strength > 0.6:
            pulse_signal = "BUY"
        elif trend_direction == "down" and trend_strength > 0.6:
            pulse_signal = "SELL"
        
        # ─────────────────────────────────────────────────────────────────────
        # LEARNING ENTEGRASYONU - Sinyali kaydet
        # ─────────────────────────────────────────────────────────────────────
        if pulse_signal in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                
                context = {
                    "ta": ta,
                    "source": "PULSE",
                    "momentum": {
                        "rsi": rsi_14,
                        "macd_hist": macd_hist,
                        "stoch_k": stoch_k
                    },
                    "ml_prediction": {
                        "direction": pulse_signal,
                        "confidence": round(trend_strength * 100),
                        "entry_price": current_price,
                        "target_price": target,
                        "stop_price": stop
                    }
                }
                
                analysis = {
                    "final_decision": pulse_signal,
                    "confidence": round(trend_strength * 100),
                    "model_used": "PULSE-Scalp"
                }
                
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe=timeframe,
                    strategy="PULSE"
                )
                logger.info(f"PULSE signal logged: {symbol} {pulse_signal} @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE prediction: {log_err}")
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "signal": pulse_signal,
            "trend": {
                "direction": trend_direction,
                "strength": round(trend_strength, 2),
                "label": f"{'YUKARI' if trend_direction == 'up' else 'AŞAĞI' if trend_direction == 'down' else 'NÖTR'} EĞİLİMİ",
                "strength_pct": round(trend_strength * 100),
                "last_5_candles": last_5
            },
            "price": {
                "current": round(current_price, 2),
                "change_5": round((closes[-1] - closes[-6]) / closes[-6] * 100, 2) if len(closes) >= 6 else 0
            },
            "levels": {
                "r2": round(r2, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "s1": {"price": round(s1, 2), "distance": round(dist_s1, 1), "alert": nearest_level == "s1"},
                "s2": round(s2, 2),
                "nearest": nearest_level,
                "nearest_distance": round(nearest_distance, 1)
            },
            "momentum": {
                "rsi": {"value": round(rsi_14, 1), "trend": rsi_trend},
                "macd": {"value": round(macd_hist, 4), "trend": macd_trend},
                "stochastic": {"value": round(stoch_k, 1), "trend": stoch_trend}
            },
            "volume": {
                "status": volume_status,
                "label": "Yüksek ▲" if volume_status == "high" else "Düşük ▼" if volume_status == "low" else "Bilinmiyor"
            },
            "suggestion": {
                "text": suggestion_text,
                "target": round(target, 2),
                "stop": round(stop, 2),
                "target_distance": round(potential_profit, 1),
                "stop_distance": round(potential_loss, 1),
                "rr_ratio": round(rr_ratio, 2),
                "timeframe_estimate": "15-30 dk"
            }
        }
        
    except Exception as e:
        logger.error(f"PULSE analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# EMA DEBUG ENDPOINT - TradingView Karşılaştırması
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/debug/ema/{symbol}")
async def debug_ema_calculation(symbol: str, timeframe: str = "1H"):
    """
    EMA Debug - TradingView değerleriyle karşılaştırma için
    """
    try:
        from services.market_data_service import get_ohlcv_data
        
        # Get market data - need 250+ candles for EMA200
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=300)
        if not ohlcv:
            return {"error": "Veri alınamadı"}
        
        # Convert to numpy arrays
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        
        # Manual EMA calculation for verification
        def calculate_ema_manual(values, period):
            """Standard EMA formula matching TradingView"""
            if len(values) < period:
                return None
            alpha = 2.0 / (period + 1.0)
            # Start with SMA for first value
            ema = float(np.mean(values[:period]))
            # Then apply EMA formula
            for v in values[period:]:
                ema = alpha * float(v) + (1 - alpha) * ema
            return ema
        
        current_price = float(closes[-1])
        
        # Calculate EMAs
        ema20 = calculate_ema_manual(closes, 20)
        ema50 = calculate_ema_manual(closes, 50)
        ema200 = calculate_ema_manual(closes, 200)
        
        # Also calculate using our existing function for comparison
        from services.ml_prediction_service import _compute_technical_indicators
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data_points": len(closes),
            "current_price": round(current_price, 2),
            "manual_ema": {
                "ema20": round(ema20, 2) if ema20 else None,
                "ema50": round(ema50, 2) if ema50 else None,
                "ema200": round(ema200, 2) if ema200 else None,
            },
            "service_ema": {
                "ema20": round(ta.get("ema_20", 0), 2),
                "ema50": round(ta.get("ema_50", 0), 2),
                "ema200": round(ta.get("ema_200", 0), 2),
            },
            "distances": {
                "price_to_ema20": round(current_price - (ema20 or current_price), 2),
                "price_to_ema50": round(current_price - (ema50 or current_price), 2),
                "price_to_ema200": round(current_price - (ema200 or current_price), 2),
            },
            "distances_pct": {
                "price_to_ema20_pct": round(((current_price - (ema20 or current_price)) / current_price) * 100, 3) if ema20 else None,
                "price_to_ema50_pct": round(((current_price - (ema50 or current_price)) / current_price) * 100, 3) if ema50 else None,
                "price_to_ema200_pct": round(((current_price - (ema200 or current_price)) / current_price) * 100, 3) if ema200 else None,
            },
            "first_5_closes": [round(c, 2) for c in closes[:5]],
            "last_5_closes": [round(c, 2) for c in closes[-5:]],
            "note": "TradingView'deki EMA değerleriyle karşılaştırın. ±5 pips içinde olmalı."
        }
        
    except Exception as e:
        logger.error(f"EMA debug error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
