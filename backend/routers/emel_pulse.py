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
        
        # Get market data — for XAUUSD, 1H is derived from 30m by DataHub.
        # If 30m not seeded yet, fall back to 5m or 30m to avoid "Insufficient data".
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=250)
        if not ohlcv or len(ohlcv) < 50:
            # Fallback: try 5m (always fetched for XAUUSD via 1m→5m resample)
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=250)
        if not ohlcv or len(ohlcv) < 50:
            # Fallback: try 30m (XAUUSD directly fetched)
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=250)
        if not ohlcv or len(ohlcv) < 20:
            logger.warning(f"EMEL: Insufficient candle data for {symbol} (tried 1H/5m/30m)")
            return {"error": "Insufficient data"}

        
        # Convert to numpy arrays - CRITICAL for correct EMA calculation
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        # Calculate TA with numpy arrays
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # Get ML prediction for context
        from dataclasses import asdict
        prediction_raw = await get_ml_prediction(symbol, "balanced")
        prediction = asdict(prediction_raw) if hasattr(prediction_raw, '__dataclass_fields__') else (prediction_raw if isinstance(prediction_raw, dict) else {})
        
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
        # DEBUG: Hacim verisi detaylarını logla
        logger.info(f"[EMEL Volume Debug] {symbol}: volumes_count={len(volumes)}, sum={float(np.sum(volumes)):.2f}, sample={volumes[-5:].tolist() if len(volumes) >= 5 else volumes.tolist()}")
        
        # Minimum anlamlı hacim threshold'u (sembole VE timeframe'e göre değişir)
        # Timeframe çarpanı: Daha kısa timeframe'lerde hacimler daha düşük olur
        tf_multiplier = {
            "5m": 0.01, "15m": 0.03, "30m": 0.06, "1h": 1.0, "4h": 4.0, "1d": 24.0
        }.get(timeframe.lower(), 1.0)
        
        MIN_MEANINGFUL_VOLUME_BASE = {
            "NDX.INDX": 1000000,      # 1M - NASDAQ (saatlik baz)
            "XAUUSD": 50,             # 50 - XAUUSD foreks
            "GDAXI.INDX": 100000,     # 100K - DAX (saatlik baz)
            "CL.COMM": 100,           # 100 - Petrol
        }.get(symbol, 100)
        
        MIN_MEANINGFUL_VOLUME = MIN_MEANINGFUL_VOLUME_BASE * tf_multiplier
        
        # Hacim verisi var mı kontrol et (en az birkaç mumda hacim > 0)
        meaningful_volumes = [v for v in volumes if v > 0]
        has_meaningful_volume = len(meaningful_volumes) >= 5 and np.mean(meaningful_volumes) > MIN_MEANINGFUL_VOLUME
        
        if has_meaningful_volume:
            # Son 5 tam mumun hacim ortalaması (son mum hariç)
            recent_volumes = volumes[-6:-1] if len(volumes) >= 6 else volumes[:-1] if len(volumes) >= 2 else volumes
            avg_volume = np.mean(recent_volumes) if len(recent_volumes) > 0 else 1
            
            # Son TAM mumu bul (sondan geriye doğru 0 olmayan ilk değer)
            current_volume = avg_volume  # Default olarak ortalama
            for i in range(2, min(6, len(volumes) + 1)):  # Sondan 2.'den 5.'ye kadar kontrol et
                if volumes[-i] > 0:
                    current_volume = volumes[-i]
                    break
            
            # Hacim trendini belirle
            if current_volume > 0 and avg_volume > 0:
                volume_ratio = current_volume / avg_volume
            else:
                volume_ratio = 1.0  # Nötr
            
            # DEBUG: Detaylı log
            logger.info(f"[EMEL Volume Debug] {symbol} {timeframe}: avg={avg_volume:.2f}, current={current_volume:.2f}, ratio={volume_ratio:.2f}")
            
            if volume_ratio >= 1.2:
                vol_status = "pass"
                vol_color = "green"
                vol_label = "YÜKSEK HACİM"
                vol_comment = "Hacim ortalamanın üzerinde. Hareket güçlü."
                green_count += 1
            elif volume_ratio >= 0.6:  # 0.8'den 0.6'ya düşürdük (daha toleranslı)
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
            # Hacim verisi yok veya çok düşük - bunu red yerine warning yap
            # Çünkü bazı sembollerde (özellikle endekslerde) hacim verisi eksik olabilir
            vol_status = "warning"
            vol_color = "yellow"
            vol_label = "VERİ YOK"
            vol_comment = f"Hacim verisi yetersiz (toplam: {float(np.sum(volumes)):.0f})."
            yellow_count += 1
            volume_ratio = 1.0  # Nötr kabul et
            logger.warning(f"[EMEL Volume Debug] {symbol}: Yetersiz hacim verisi - sum={float(np.sum(volumes)):.2f}, threshold={MIN_MEANINGFUL_VOLUME}")
        
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
                "trend": "Artıyor" if volume_ratio > 1 else "Azalıyor",
                "debug": {
                    "volumes_count": len(volumes),
                    "total_volume": float(np.sum(volumes)),
                    "avg_volume": float(avg_volume) if 'avg_volume' in locals() else 0,
                    "current_volume": float(current_volume) if 'current_volume' in locals() else 0,
                    "meaningful_count": len(meaningful_volumes),
                    "threshold": float(MIN_MEANINGFUL_VOLUME),
                    "last_5": [float(v) for v in volumes[-5:]] if len(volumes) >= 5 else [float(v) for v in volumes],
                }
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
        # 5+ green = strong signal, 4 green + ML agrees = cautious signal
        if red_count >= 3:
            decision = "HOLD"
            decision_reason = "Çok fazla risk faktörü var"
        elif green_count >= 5:
            decision = signal if signal != "HOLD" else "BUY" if trend_direction == "up" else "SELL"
        elif green_count >= 4 and signal in ("BUY", "SELL") and red_count <= 1:
            decision = signal
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
                    strategy="EMEL",
                    model_type="emel",
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
# PULSE 1 (ALGORİTMİK) - GELİŞTİRİLMİŞ KURAL TABANLI SCALP
# Sorun düzeltmeleri: 
#   - Son 5 mum yetersiz → 10 mum + EMA stack + hacim eklendi
#   - Trend gücü 0.6 çok katı → 0.4 SCOUT / 0.65 CONFIRM iki kademe
#   - R/R 1.5 çok katı → 1.2 optimal
#   - Sadece yön bakıyordu → Multi-indicator trend puanlama sistemi
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pulse/{symbol}")
async def get_pulse_analysis(symbol: str, timeframe: str = "5m"):
    """
    PULSE 1 - Geliştirilmiş Algoritmik Scalp Analizi
    İki kademeli sinyal: SCOUT (izle) + CONFIRM (işlem yap)
    
    REGIME-AWARE: Güçlü trend modlarında (STRONG_TREND_UP/DOWN) devre dışı kalır.
    Sadece RANGING ve TRANSITION rejimlerinde aktif çalışır.
    """
    try:
        from services.ml_prediction_service import _compute_technical_indicators
        from services.market_data_service import get_ohlcv_data
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout
        
        # ─── REGIME CHECK: Pulse 1 disabled in strong trends ────────────
        regime = await detect_regime(symbol)
        
        if regime.model_weights.get("pulse1", 0) == 0:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat(),
                "signal": "HOLD",
                "signal_type": "REGIME_DISABLED",
                "pulse_score": 0,
                "regime": {
                    "type": regime.regime,
                    "reason": f"Pulse 1 devre dışı: {regime.regime} rejiminde scalp sinyalleri güvenilir değil",
                    "adx": regime.adx,
                    "session": regime.session,
                    "allowed_models": [k for k, v in regime.model_weights.items() if v > 0],
                },
                "trend": {"direction": "neutral", "strength": 0, "label": "REGIME DISABLED", "strength_pct": 0, "last_5_candles": []},
                "price": {"current": regime.current_price or 0, "change_5": 0},
                "levels": {"r2": 0, "r1": 0, "pivot": 0, "s1": {"price": 0, "distance": 0, "alert": False}, "s2": 0, "nearest": "none", "nearest_distance": 0},
                "momentum": {"rsi": {"value": 50, "trend": "neutral"}, "macd": {"value": 0, "trend": "neutral"}, "stochastic": {"value": 50, "trend": "neutral"}},
                "volume": {"status": "unknown", "label": "N/A", "ratio": 0, "available": False},
                "score_breakdown": {},
                "decision_notes": [f"Pulse 1 kapalı: {regime.regime} rejimi"],
                "suggestion": {"text": f"⛔ Pulse 1 {regime.regime} rejiminde devre dışı. ML ve Pulse 2/3 kullanın.", "target": regime.current_price or 0, "stop": regime.current_price or 0, "target_distance": 0, "stop_distance": 0, "rr_ratio": 0, "timeframe_estimate": "N/A"}
            }
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        if is_timed_out:
            return {
                "symbol": symbol, "timeframe": timeframe, "timestamp": datetime.now().isoformat(),
                "signal": "HOLD", "signal_type": "TIMEOUT",
                "pulse_score": 0,
                "regime": {"type": regime.regime, "reason": timeout_reason},
                "decision_notes": [timeout_reason],
                "suggestion": {"text": f"⏸️ {timeout_reason}", "target": 0, "stop": 0, "target_distance": 0, "stop_distance": 0, "rr_ratio": 0, "timeframe_estimate": "N/A"},
                "trend": {"direction": "neutral", "strength": 0, "label": "TIMEOUT", "strength_pct": 0, "last_5_candles": []},
                "price": {"current": regime.current_price or 0, "change_5": 0},
                "levels": {"r2": 0, "r1": 0, "pivot": 0, "s1": {"price": 0, "distance": 0, "alert": False}, "s2": 0, "nearest": "none", "nearest_distance": 0},
                "momentum": {"rsi": {"value": 50, "trend": "neutral"}, "macd": {"value": 0, "trend": "neutral"}, "stochastic": {"value": 50, "trend": "neutral"}},
                "volume": {"status": "unknown", "label": "N/A", "ratio": 0, "available": False},
                "score_breakdown": {},
            }
        
        # Get market data - 100 bar (EMA20 için yeterli)
        # XAUUSD: 1H derives from 30m in DataHub — fallback to 5m if insufficient
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=100)
        if not ohlcv or len(ohlcv) < 20:
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=100)
        if not ohlcv or len(ohlcv) < 20:
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=100)
        if not ohlcv or len(ohlcv) < 20:
            return {"error": "Insufficient data"}
        
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        
        # ─── PUANLAMA SİSTEMİ (0-100) ─────────────────────────────────────
        score = 0.0
        score_details = {}
        
        # 1. Son 10 mum yönü (20 puan) - Eskiden 5 mumdu, artık 10
        last_10 = []
        for i in range(-10, 0):
            if closes[i] > closes[i-1]:
                last_10.append("up")
            elif closes[i] < closes[i-1]:
                last_10.append("down")
            else:
                last_10.append("neutral")
        
        up_count = last_10.count("up")
        down_count = last_10.count("down")
        
        if up_count >= 7:
            score += 20
            candle_bias = "up"
        elif up_count >= 5:
            score += 10
            candle_bias = "up"
        elif down_count >= 7:
            score += 20
            candle_bias = "down"
        elif down_count >= 5:
            score += 10
            candle_bias = "down"
        else:
            candle_bias = "neutral"
        
        score_details["candle_10"] = {"up": up_count, "down": down_count, "bias": candle_bias, "pts": round(score)}
        
        # 2. EMA Stack (25 puan) - YENİ: EMA5 > EMA10 > EMA20
        ema_5 = ta.get("close", current_price)  # Use last close as proxy for very short EMA
        if len(closes) >= 5:
            ema_5 = float(np.mean(closes[-5:]))  # SMA5 as fast EMA proxy
        ema_10 = float(np.mean(closes[-10:])) if len(closes) >= 10 else current_price
        ema_20 = ta.get("ema_20", current_price)
        
        ema_pts = 0
        if ema_5 > ema_10 > ema_20:
            ema_pts = 25
            ema_stack = "bullish"
        elif ema_5 > ema_10:
            ema_pts = 12
            ema_stack = "weak_bullish"
        elif ema_5 < ema_10 < ema_20:
            ema_pts = 25
            ema_stack = "bearish"
        elif ema_5 < ema_10:
            ema_pts = 12
            ema_stack = "weak_bearish"
        else:
            ema_stack = "neutral"
        score += ema_pts
        score_details["ema_stack"] = {"ema5": round(ema_5, 2), "ema10": round(ema_10, 2), "ema20": round(ema_20, 2), "stack": ema_stack, "pts": ema_pts}
        
        # 3. RSI Momentum (20 puan)
        rsi_14 = ta.get("rsi_14", 50)
        rsi_pts = 0
        if 40 <= rsi_14 <= 60:
            rsi_pts = 10  # Neutral = trend devam ediyor
        elif (rsi_14 > 60 and candle_bias == "up") or (rsi_14 < 40 and candle_bias == "down"):
            rsi_pts = 20  # RSI yönle uyumlu
        elif rsi_14 > 75 or rsi_14 < 25:
            rsi_pts = 0  # Aşırı bölge = risk
        else:
            rsi_pts = 5
        score += rsi_pts
        score_details["rsi"] = {"value": round(rsi_14, 1), "pts": rsi_pts}
        
        # 4. MACD Histogram (15 puan)
        macd_hist = ta.get("macd_hist", 0)
        macd_pts = 0
        if macd_hist > 0 and candle_bias == "up":
            macd_pts = 15
        elif macd_hist < 0 and candle_bias == "down":
            macd_pts = 15
        elif macd_hist > 0 or candle_bias != "down":
            macd_pts = 5
        score += macd_pts
        score_details["macd"] = {"hist": round(macd_hist, 4), "pts": macd_pts}
        
        # 5. Hacim (10 puan)
        vol_pts = 0
        volume_status = "unknown"
        volume_ratio = 1.0
        if len(volumes) >= 20 and float(np.sum(volumes)) > 0:
            avg_volume = float(np.mean(volumes[-20:]))
            current_volume = float(volumes[-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            if volume_ratio >= 1.3:
                vol_pts = 10
                volume_status = "high"
            elif volume_ratio >= 1.1:
                vol_pts = 5
                volume_status = "normal"
            else:
                volume_status = "low"
        score += vol_pts
        score_details["volume"] = {"ratio": round(volume_ratio, 2), "status": volume_status, "pts": vol_pts}
        
        # 6. Stochastic onayı (10 puan)
        stoch_k = ta.get("stoch_k", 50)
        stoch_pts = 0
        if (stoch_k > 50 and candle_bias == "up") or (stoch_k < 50 and candle_bias == "down"):
            stoch_pts = 10
        elif 30 <= stoch_k <= 70:
            stoch_pts = 5
        score += stoch_pts
        score_details["stochastic"] = {"k": round(stoch_k, 1), "pts": stoch_pts}
        
        # ─── TOPLAM SKOR → SİNYAL TİPİ ───────────────────────────────────
        # Yönü belirle (dominant yön)
        bullish_score = 0
        bearish_score = 0
        if candle_bias == "up": bullish_score += 30
        elif candle_bias == "down": bearish_score += 30
        if ema_stack in ["bullish", "weak_bullish"]: bullish_score += 25
        elif ema_stack in ["bearish", "weak_bearish"]: bearish_score += 25
        if rsi_14 > 50: bullish_score += 15
        else: bearish_score += 15
        if macd_hist > 0: bullish_score += 15
        else: bearish_score += 15
        if stoch_k > 50: bullish_score += 15
        else: bearish_score += 15
        
        if bullish_score > bearish_score:
            trend_direction = "up"
        elif bearish_score > bullish_score:
            trend_direction = "down"
        else:
            trend_direction = "neutral"
        
        trend_strength = score / 100.0
        
        # İki kademeli sinyal sistemi
        signal_type = "HOLD"  # HOLD / SCOUT / CONFIRM
        pulse_signal = "HOLD"
        decision_notes = []
        
        if score >= 56:  # 56'ya düşürüldü (threshold: 56)
            signal_type = "CONFIRM"
            pulse_signal = "BUY" if trend_direction == "up" else "SELL" if trend_direction == "down" else "HOLD"
        elif score >= 35:  # Scout threshold da düşürüldü (40'tan)
            signal_type = "SCOUT"
            pulse_signal = "BUY" if trend_direction == "up" else "SELL" if trend_direction == "down" else "HOLD"
        else:
            signal_type = "HOLD"
            pulse_signal = "HOLD"
        
        # ─── SEVİYELER ────────────────────────────────────────────────────
        high_20 = float(np.max(highs[-20:]))
        low_20 = float(np.min(lows[-20:]))
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        r2 = pivot + (high_20 - low_20)
        s1 = 2 * pivot - high_20
        s2 = pivot - (high_20 - low_20)
        
        dist_s1 = current_price - s1
        dist_r1 = r1 - current_price
        nearest_level = "s1" if dist_s1 < dist_r1 else "r1"
        nearest_distance = min(dist_s1, dist_r1)
        
        # Hedef ve Stop — ATR fallback if pivot levels contradict trend direction
        atr_14 = ta.get("atr_14", abs(high_20 - low_20) / 20)
        if trend_direction == "up":
            target = r1 if r1 > current_price else current_price + atr_14 * 1.5
            stop = s1 if s1 < current_price else current_price - atr_14 * 1.0
        elif trend_direction == "down":
            target = s1 if s1 < current_price else current_price - atr_14 * 1.5
            stop = r1 if r1 > current_price else current_price + atr_14 * 1.0
        else:
            target = r1 if r1 > current_price else current_price + atr_14 * 1.0
            stop = s1 if s1 < current_price else current_price - atr_14 * 1.0
        
        potential_profit = abs(target - current_price)
        potential_loss = abs(current_price - stop)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # ─── FİLTRELER (REGIME-AWARE) ────────────────────────────────────
        # R/R minimum from regime (dynamic instead of static 1.2)
        min_rr = regime.min_rr
        if pulse_signal in ["BUY", "SELL"] and rr_ratio < min_rr:
            decision_notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr})")
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"  # CONFIRM → SCOUT downgrade
            else:
                pulse_signal = "HOLD"
                signal_type = "HOLD"
        
        # RSI filtresi - REGIME-AWARE (trend modunda RSI>70 = momentum, sat değil)
        rsi_interpretation = interpret_rsi(rsi_14, regime, pulse_signal)
        if rsi_interpretation["action"] == "caution":
            decision_notes.append(rsi_interpretation["note"])
            if signal_type == "CONFIRM":
                signal_type = "SCOUT"
        elif rsi_interpretation["action"] == "block":
            decision_notes.append(rsi_interpretation["note"])
            pulse_signal = "HOLD"
            signal_type = "HOLD"
        elif rsi_interpretation["action"] == "boost":
            decision_notes.append(rsi_interpretation["note"])
            score += rsi_interpretation["score_adjustment"]
        
        # Direction filter - enforce regime allowed directions
        pulse_signal, was_filtered, filter_reason = filter_signal_by_regime(pulse_signal, regime)
        if was_filtered:
            signal_type = "HOLD"
            decision_notes.append(filter_reason)
        
        # Hacim notu (iptal değil, bilgi)
        if pulse_signal in ["BUY", "SELL"] and volume_status == "low":
            decision_notes.append("Low volume - be cautious")
        
        # ─── SUGGESTION ───────────────────────────────────────────────────
        rsi_trend = "up" if rsi_14 > 50 else "down" if rsi_14 < 50 else "neutral"
        macd_trend = "up" if macd_hist > 0 else "down"
        stoch_trend = "up" if stoch_k > 50 else "down"
        
        if signal_type == "CONFIRM":
            if pulse_signal == "BUY":
                suggestion_text = f"🟢 Strong BUY signal (score: {score:.0f}). Target: {r1:.0f}, Stop: {s1:.0f}"
            else:
                suggestion_text = f"🔴 Strong SELL signal (score: {score:.0f}). Target: {s1:.0f}, Stop: {r1:.0f}"
        elif signal_type == "SCOUT":
            if pulse_signal == "BUY":
                suggestion_text = f"👀 Bullish momentum building (score: {score:.0f}). Hold above {s1:.0f}, consider if strengthens."
            elif pulse_signal == "SELL":
                suggestion_text = f"👀 Bearish momentum building (score: {score:.0f}). Hold below {r1:.0f}, consider if strengthens."
            else:
                suggestion_text = f"👀 Watch mode (score: {score:.0f}). Direction unclear."
        else:
            suggestion_text = f"⏱️ Hold mode (score: {score:.0f}). No strong trend formation."
        
        if decision_notes:
            suggestion_text += f" | Notes: {', '.join(decision_notes)}"
        
        # ─── LEARNING ENTEGRASYONU ────────────────────────────────────────
        # Log ALL BUY/SELL signals regardless of signal_type (CONFIRM/SCOUT/HOLD)
        # so Signal Performance panel tracks every directional signal from Pulse 1
        if pulse_signal in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                context = {
                    "ta": ta,
                    "source": "PULSE",
                    "score": score,
                    "signal_type": signal_type,
                    "score_details": score_details,
                    "decision_notes": decision_notes,
                    "ml_prediction": {
                        "direction": pulse_signal,
                        "confidence": round(score),
                        "entry_price": current_price,
                        "target_price": target,
                        "stop_price": stop
                    }
                }
                analysis = {
                    "final_decision": pulse_signal,
                    "confidence": round(score),
                    "model_used": "PULSE-V1-Improved"
                }
                await log_prediction(
                    symbol=symbol,
                    context=context,
                    analysis=analysis,
                    timeframe=timeframe,
                    strategy="PULSE",
                    model_type="pulse1",
                )
                logger.info(f"PULSE signal logged: {symbol} {pulse_signal} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE prediction: {log_err}")
        
        # Last 5 candles for frontend (backward compat)
        last_5 = last_10[-5:]
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "signal": pulse_signal,
            "signal_type": signal_type,
            "pulse_score": round(score, 1),
            "trend": {
                "direction": trend_direction,
                "strength": round(trend_strength, 2),
                "label": f"{'UPTREND' if trend_direction == 'up' else 'DOWNTREND' if trend_direction == 'down' else 'NEUTRAL'}",
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
                "label": "High ▲" if volume_status == "high" else "Low ▼" if volume_status == "low" else "Normal" if volume_status == "normal" else "N/A",
                "ratio": round(volume_ratio, 2),
                "available": volume_status != "unknown"
            },
            "score_breakdown": score_details,
            "decision_notes": decision_notes,
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
            },
            "suggestion": {
                "text": suggestion_text,
                "target": round(target, 2),
                "stop": round(stop, 2),
                "target_distance": round(potential_profit, 1),
                "stop_distance": round(potential_loss, 1),
                "rr_ratio": round(rr_ratio, 2),
                "timeframe_estimate": "15-30 min"
            }
        }
        
    except Exception as e:
        logger.error(f"PULSE analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE 2 (ML TABANLI) - GELİŞTİRİLMİŞ ML + TA HİBRİT
# Sorun düzeltmeleri:
#   - ML güveni %60 çok yüksek → %45 SCOUT / %60 CONFIRM
#   - EMA50 tek başına yetersiz → EMA20 + EMA50 + MACD üçlü onay
#   - R/R 1.0 çok düşük → 1.2 optimal
#   - İki kademeli sinyal eklendi (SCOUT/CONFIRM)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/pulse-ml/{symbol}")
async def get_pulse_ml_analysis(symbol: str, timeframe: str = "15m"):
    """
    PULSE 2 - Geliştirilmiş ML + TA Hibrit Scalp (REGIME-AWARE)
    ML modelini kullanır, EMA20+EMA50+MACD ile trend onayı yapar.
    İki kademeli: SCOUT (izle) + CONFIRM (işlem)
    
    REGIME-AWARE:
    - Trend modunda RSI>70 = momentum sinyali (sat değil)
    - ATH'de SELL bloklanır, ML confidence threshold düşer
    - Session bazlı R/R ayarı
    - Fake signal timeout koruması
    """
    try:
        from services.ml_prediction_service import get_ml_prediction, _compute_technical_indicators
        from services.market_data_service import get_ohlcv_data
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout
        
        # ─── REGIME DETECTION ───────────────────────────────────────────
        regime = await detect_regime(symbol)
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        
        # 1. Market Data — XAUUSD fallback to 5m/30m if 1h not seeded yet
        ohlcv = await get_ohlcv_data(symbol, timeframe, limit=200)
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "5M", limit=200)
        if not ohlcv or len(ohlcv) < 50:
            ohlcv = await get_ohlcv_data(symbol, "30M", limit=200)
        if not ohlcv or len(ohlcv) < 20:
            return {"error": "Insufficient data"}
            
        closes = np.array([c["close"] for c in ohlcv], dtype=np.float64)
        highs = np.array([c["high"] for c in ohlcv], dtype=np.float64)
        lows = np.array([c["low"] for c in ohlcv], dtype=np.float64)
        volumes = np.array([c.get("volume", 0) for c in ohlcv], dtype=np.float64)
        # Use live price from DataHub (updated every 30s) instead of stale candle close
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(closes[-1])
        
        # 2. ML Tahmini Al
        from dataclasses import asdict
        prediction_raw = await get_ml_prediction(symbol, "aggressive")
        prediction = asdict(prediction_raw) if hasattr(prediction_raw, '__dataclass_fields__') else (prediction_raw if isinstance(prediction_raw, dict) else {})
        ml_direction = prediction.get("direction", "HOLD")
        ml_confidence = prediction.get("confidence", 0)
        
        # 3. Teknik İndikatörler
        ta = _compute_technical_indicators(closes, highs, lows, volumes)
        ema_20 = ta.get("ema_20", current_price)
        ema_50 = ta.get("ema_50", current_price)
        rsi_14 = ta.get("rsi_14", 50)
        macd_hist = ta.get("macd_hist", 0)
        stoch_k = ta.get("stoch_k", 50)
        atr_val = ta.get("atr_14", current_price * 0.002)
        
        # 4. PUANLAMA SİSTEMİ (ML + TA hybrid skor) - REGIME-AWARE
        score = 0.0
        notes = []
        signal_type = "HOLD"
        signal = "HOLD"
        
        # ─── TA-ONLY DIRECTION (fallback when ML is HOLD/low conf) ─────
        # Derive direction from technical indicators alone
        ta_direction = "HOLD"
        ta_votes = 0
        if current_price > ema_20 > ema_50:
            ta_direction = "BUY"
            ta_votes += 2
        elif current_price < ema_20 < ema_50:
            ta_direction = "SELL"
            ta_votes += 2
        elif current_price > ema_20:
            ta_direction = "BUY"
            ta_votes += 1
        elif current_price < ema_20:
            ta_direction = "SELL"
            ta_votes += 1
        
        if macd_hist > 0:
            if ta_direction == "BUY": ta_votes += 1
            elif ta_direction == "HOLD": ta_direction = "BUY"; ta_votes += 1
        elif macd_hist < 0:
            if ta_direction == "SELL": ta_votes += 1
            elif ta_direction == "HOLD": ta_direction = "SELL"; ta_votes += 1
        
        if rsi_14 < 35: 
            if ta_direction != "SELL": ta_votes += 1
        elif rsi_14 > 65:
            if ta_direction != "BUY": ta_votes += 1
        
        # Use ML direction if available, else fallback to TA direction
        active_direction = ml_direction if ml_direction in ("BUY", "SELL") else ta_direction
        is_ta_fallback = ml_direction == "HOLD" and ta_direction in ("BUY", "SELL")
        if is_ta_fallback:
            notes.append(f"ML HOLD → TA analiz yönü: {ta_direction} ({ta_votes} onay)")
        
        # ─── ML Güven Puanı (40 puan max) ────────────────────────────────
        ml_pts = 0
        ml_confirm_floor = 50.0  # 55'ten 50'ye düşürüldü
        ml_scout_floor = 45.0    # 52'den 45'e düşürüldü
        
        if regime.regime == "STRONG_TREND_UP" and regime.is_ath_zone:
            ml_confirm_floor = 42.0  # 48'den düşürüldü
            ml_scout_floor = 38.0    # 42'den düşürüldü
            notes.append("ATH modu: ML threshold düşürüldü")
        elif regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            ml_confirm_floor = 45.0  # 50'den düşürüldü
            ml_scout_floor = 40.0    # 45'ten düşürüldü
        
        if ml_direction in ("BUY", "SELL"):
            if ml_confidence >= 70:
                ml_pts = 40
            elif ml_confidence >= 60:
                ml_pts = 30
            elif ml_confidence >= ml_scout_floor:
                ml_pts = 20
            else:
                ml_pts = 10  # ML has a direction but low confidence
                notes.append(f"ML yön var ({ml_direction}) ama güven düşük ({ml_confidence:.1f}%)")
        else:
            # ML gave HOLD — give partial credit if TA fallback aligns with regime
            if is_ta_fallback and ta_votes >= 2:
                ml_pts = 15  # TA consensus replaces ML
                notes.append("TA konsensüs ML yerine geçti")
            elif is_ta_fallback:
                ml_pts = 8
            else:
                ml_pts = 0
                notes.append(f"ML HOLD, TA belirsiz")
        score += ml_pts
        
        # ─── EMA Trend Onayı (25 puan max) ──────────────────────────────
        ema_pts = 0
        ema_status = "neutral"
        
        if active_direction == "BUY":
            if current_price > ema_20 > ema_50:
                ema_pts = 25
                ema_status = "strong_confirm"
            elif current_price > ema_20:
                ema_pts = 15
                ema_status = "confirm"
            elif current_price > ema_50:
                ema_pts = 8
                ema_status = "weak"
                if regime.regime == "STRONG_TREND_UP":
                    ema_pts = 15
                    ema_status = "pullback_opportunity"
                    notes.append("Trend pullback: EMA20 retest, dip alım fırsatı")
                else:
                    notes.append("Fiyat EMA20 altında, temkinli ol")
            else:
                ema_pts = 0
                ema_status = "against"
                if regime.regime == "STRONG_TREND_UP":
                    ema_pts = 5
                    ema_status = "deep_pullback"
                    notes.append("Derin pullback: EMA50 altında ama trend yukarı")
                else:
                    notes.append("Trend (EMA) yönü desteklemiyor")
        elif active_direction == "SELL":
            if current_price < ema_20 < ema_50:
                ema_pts = 25
                ema_status = "strong_confirm"
            elif current_price < ema_20:
                ema_pts = 15
                ema_status = "confirm"
            elif current_price < ema_50:
                ema_pts = 8
                ema_status = "weak"
                if regime.regime == "STRONG_TREND_DOWN":
                    ema_pts = 15
                    ema_status = "pullback_opportunity"
                    notes.append("Trend pullback: EMA20 retest, ralli satış fırsatı")
                else:
                    notes.append("Fiyat EMA20 üstünde, temkinli ol")
            else:
                ema_pts = 0
                ema_status = "against"
                if regime.regime == "STRONG_TREND_DOWN":
                    ema_pts = 5
                    ema_status = "deep_pullback"
                    notes.append("Derin pullback: EMA50 üstünde ama trend aşağı")
                else:
                    notes.append("Trend (EMA) yönü desteklemiyor")
        score += ema_pts
        
        # ─── MACD Momentum Onayı (15 puan max) ──────────────────────────
        macd_pts = 0
        if active_direction == "BUY" and macd_hist > 0:
            macd_pts = 15
        elif active_direction == "SELL" and macd_hist < 0:
            macd_pts = 15
        elif abs(macd_hist) < 0.01:
            macd_pts = 5
        else:
            if regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
                macd_pts = 3
                notes.append("MACD gecikmeli, trend güçlü devam ediyor")
            else:
                notes.append("MACD yönü desteklemiyor")
        score += macd_pts
        
        # ─── RSI Filtresi (10 puan max) - REGIME-AWARE ──────────────────
        rsi_pts = 0
        rsi_interpretation = interpret_rsi(rsi_14, regime, active_direction)
        
        if rsi_interpretation["action"] == "boost":
            rsi_pts = 10 + rsi_interpretation["score_adjustment"]
            notes.append(rsi_interpretation["note"])
        elif rsi_interpretation["action"] == "caution":
            rsi_pts = 0
            notes.append(rsi_interpretation["note"])
        elif rsi_interpretation["action"] == "neutral":
            if active_direction in ("BUY", "SELL"):
                if regime.rsi_oversold < rsi_14 < regime.rsi_overbought:
                    rsi_pts = 10
                else:
                    rsi_pts = 3
        score += max(0, rsi_pts)
        
        # ─── Hacim Onayı (10 puan max) ───────────────────────────────────
        vol_pts = 0
        if len(volumes) >= 10 and float(np.sum(volumes)) > 0:
            vol_avg = float(np.mean(volumes[-10:]))
            vol_current = float(volumes[-1])
            vol_ratio = vol_current / vol_avg if vol_avg > 0 else 1
            if vol_ratio >= 1.2:
                vol_pts = 10
            elif vol_ratio >= 0.9:
                vol_pts = 5
            else:
                notes.append("Düşük hacim")
        score += vol_pts
        
        # ─── SİNYAL BELİRLEME (İki kademe) - REGIME-AWARE ──────────────
        # For TA fallback mode, use lower thresholds (TA has already proven direction)
        confirm_threshold = 56 if is_ta_fallback else 56  # 56'ya düşürüldü
        scout_threshold = 35 if is_ta_fallback else 35    # 40'tan 35'e düşürüldü
        conf_floor = ml_scout_floor if is_ta_fallback else ml_confirm_floor
        scout_conf_floor = 0 if is_ta_fallback else ml_scout_floor  # No ML floor needed for TA fallback
        
        if score >= confirm_threshold and (ml_confidence >= conf_floor or is_ta_fallback):
            signal_type = "CONFIRM"
            signal = active_direction
        elif score >= scout_threshold and (ml_confidence >= scout_conf_floor or is_ta_fallback):
            signal_type = "SCOUT"
            signal = active_direction
        else:
            signal_type = "HOLD"
            signal = "HOLD"
        
        # ─── DIRECTION FILTER (enforce regime rules) ────────────────────
        signal, was_filtered, filter_reason = filter_signal_by_regime(signal, regime)
        if was_filtered:
            signal_type = "HOLD"
            notes.append(filter_reason)
            
        # ─── Hedef / Stop (ATR bazlı - trend modunda daha geniş target) ─
        target = prediction.get("target_price")
        stop = prediction.get("stop_price")
        
        # Trend modunda hedef genişlet (trendde küçük risk, büyük kâr)
        atr_target_mult = 2.0
        atr_stop_mult = 1.5
        if regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            atr_target_mult = 3.0  # Trendde 3x ATR hedef
            atr_stop_mult = 1.2    # Trendde daha dar stop (trailing)
        
        if not target or not stop:
            if signal == "BUY":
                stop = current_price - (atr_val * atr_stop_mult)
                target = current_price + (atr_val * atr_target_mult)
            elif signal == "SELL":
                stop = current_price + (atr_val * atr_stop_mult)
                target = current_price - (atr_val * atr_target_mult)
            else:
                target = current_price
                stop = current_price
        
        # ─── R/R Kontrolü (regime-dynamic minimum) ──────────────────────
        min_rr = regime.min_rr
        rr_ratio = 0
        if signal != "HOLD" and target and stop:
            profit = abs(target - current_price)
            risk = abs(current_price - stop)
            rr_ratio = profit / risk if risk > 0 else 0
            
            if rr_ratio < min_rr:
                if signal_type == "CONFIRM":
                    signal_type = "SCOUT"
                    notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr}), downgraded to SCOUT")
                else:
                    signal = "HOLD"
                    signal_type = "HOLD"
                    notes.append(f"R/R too low ({rr_ratio:.2f} < {min_rr})")
        
        # ─── FAKE SIGNAL TIMEOUT (reduce to SCOUT if in timeout) ────────
        if is_timed_out and signal_type == "CONFIRM" and ml_confidence < 75:
            signal_type = "SCOUT"
            notes.append(f"Timeout aktif: CONFIRM→SCOUT (ML<75%)")
            
        # ─── SUGGESTION ──────────────────────────────────────────────────
        regime_tag = f" [{regime.regime}]" if regime.regime != "TRANSITION" else ""
        if signal_type == "CONFIRM":
            suggestion = f"🟢 ML confirmed {'BUY' if signal == 'BUY' else 'SELL'} signal{regime_tag} (score: {score:.0f}, ML: {ml_confidence:.0f}%)"
        elif signal_type == "SCOUT":
            suggestion = f"👀 ML watch mode{regime_tag} (score: {score:.0f}). Consider if strengthens."
        else:
            suggestion = f"⏱️ Hold{regime_tag}. ML score: {score:.0f}/100"
        
        # Loglama — ALL BUY/SELL signals (not just CONFIRM/SCOUT)
        if signal in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                await log_prediction(
                    symbol=symbol,
                    context={
                        "source": "PULSE_ML",
                        "ta": ta,
                        "score": score,
                        "signal_type": signal_type,
                        "ml_prediction": {
                            "direction": signal,
                            "confidence": ml_confidence,
                            "entry_price": current_price,
                            "target_price": target,
                            "stop_price": stop,
                        }
                    },
                    analysis={"final_decision": signal, "confidence": ml_confidence, "model_used": "PULSE-ML-V2"},
                    timeframe=timeframe,
                    strategy="PULSE_ML",
                    model_type="pulse2",
                )
                logger.info(f"PULSE-ML signal logged: {symbol} {signal} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE-ML prediction: {log_err}")

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "signal": signal,
            "signal_type": signal_type,
            "pulse_score": round(score, 1),
            "confidence": ml_confidence,
            "model_type": "PULSE_ML_V2",
            "price": current_price,
            "target": round(target, 2) if target else 0,
            "stop": round(stop, 2) if stop else 0,
            "rr_ratio": round(rr_ratio, 2),
            "score_breakdown": {
                "ml": {"pts": ml_pts, "confidence": round(ml_confidence, 1), "direction": ml_direction},
                "ema": {"pts": ema_pts, "status": ema_status, "ema20": round(ema_20, 2), "ema50": round(ema_50, 2)},
                "macd": {"pts": macd_pts, "hist": round(macd_hist, 4)},
                "rsi": {"pts": rsi_pts, "value": round(rsi_14, 1)},
                "volume": {"pts": vol_pts}
            },
            "details": {
                "ml_direction": ml_direction,
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "rsi_14": round(rsi_14, 1),
                "macd_hist": round(macd_hist, 4),
                "notes": notes
            },
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
                "ml_confirm_floor": ml_confirm_floor,
                "ml_scout_floor": ml_scout_floor,
            },
            "suggestion": suggestion
        }
            
    except Exception as e:
        logger.error(f"PULSE-ML analysis error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# PULSE 3 (HYBRID SCALP) - 3 ZAMANLI, 3 FİLTRELİ, HIZLI KARAR
# Konsept: Hem hızlı olsun, hem güvenilir, hem sık sinyal versin
#   - 5m: Anlık momentum (%50 ağırlık)
#   - 1H: Kısa trend (%30 ağırlık)
#   - 4H: Ana trend yönü (%20 ağırlık)
#   - İki kademe: SCOUT (zayıf-sık) + CONFIRM (güçlü-az)
#   - R/R minimum 1.2
#   - Cache sistemi ile hız optimizasyonu
# ═══════════════════════════════════════════════════════════════════════════════

# In-memory cache for PULSE 3 speed
_pulse3_cache: Dict[str, Any] = {}

def _cache_get(key: str, max_age_seconds: int) -> Any:
    """Get from cache if not expired"""
    if key in _pulse3_cache:
        data, ts = _pulse3_cache[key]
        if (datetime.now() - ts).total_seconds() < max_age_seconds:
            return data
    return None

def _cache_set(key: str, data: Any):
    """Store in cache with timestamp"""
    _pulse3_cache[key] = (data, datetime.now())


async def _fetch_tf_data(symbol: str, tf: str, limit: int, cache_seconds: int):
    """Fetch OHLCV data with caching. Falls back to EOD daily for symbols without intraday (e.g. XAUUSD)."""
    cache_key = f"p3_{symbol}_{tf}"
    cached = _cache_get(cache_key, cache_seconds)
    if cached is not None:
        return cached
    
    from services.market_data_service import get_ohlcv_data
    ohlcv = await get_ohlcv_data(symbol, tf, limit=limit)
    if ohlcv:
        _cache_set(cache_key, ohlcv)
        return ohlcv
    
    # Fallback: use EOD daily data for symbols without intraday support (e.g. XAUUSD)
    logger.warning(f"No intraday {tf} data for {symbol}, falling back to EOD daily")
    ohlcv = await get_ohlcv_data(symbol, "1d", limit=limit)
    if ohlcv:
        _cache_set(cache_key, ohlcv)
    return ohlcv


def _analyze_5m(closes, highs, lows, volumes, ta) -> Dict:
    """5 dakikalık analiz - 50 puan üzerinden"""
    score = 0.0
    details = {}
    
    if len(closes) < 10:
        return {"score": 25.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    # 1. Son 5 mum yönü (15 puan)
    last_5_dirs = []
    for i in range(-5, 0):
        if closes[i] > closes[i-1]:
            last_5_dirs.append("up")
        elif closes[i] < closes[i-1]:
            last_5_dirs.append("down")
        else:
            last_5_dirs.append("neutral")
    
    bullish = last_5_dirs.count("up")
    bearish = last_5_dirs.count("down")
    
    candle_pts = 0
    if bullish >= 4:
        candle_pts = 15
    elif bullish == 3:
        candle_pts = 5
    elif bearish >= 4:
        candle_pts = 15
    elif bearish == 3:
        candle_pts = 5
    score += candle_pts
    details["candles"] = {"up": bullish, "down": bearish, "pts": candle_pts, "last_5": last_5_dirs}
    
    # 2. EMA Stack: SMA5 > SMA10 > EMA20 (20 puan)
    sma5 = float(np.mean(closes[-5:])) if len(closes) >= 5 else float(closes[-1])
    sma10 = float(np.mean(closes[-10:])) if len(closes) >= 10 else float(closes[-1])
    ema20 = ta.get("ema_20", float(closes[-1]))
    
    ema_pts = 0
    if sma5 > sma10 > ema20:
        ema_pts = 20
        ema_dir = "bullish"
    elif sma5 > sma10:
        ema_pts = 10
        ema_dir = "weak_bullish"
    elif sma5 < sma10 < ema20:
        ema_pts = 20
        ema_dir = "bearish"
    elif sma5 < sma10:
        ema_pts = 10
        ema_dir = "weak_bearish"
    else:
        ema_dir = "neutral"
    score += ema_pts
    details["ema_stack"] = {"sma5": round(sma5, 2), "sma10": round(sma10, 2), "ema20": round(ema20, 2), "dir": ema_dir, "pts": ema_pts}
    
    # 3. Hacim artışı (10 puan)
    vol_pts = 0
    if len(volumes) >= 10 and float(np.sum(volumes)) > 0:
        vol_avg = float(np.mean(volumes[-10:]))
        vol_last = float(volumes[-1])
        vol_ratio = vol_last / vol_avg if vol_avg > 0 else 1
        if vol_ratio >= 1.3:
            vol_pts = 10
        elif vol_ratio >= 1.1:
            vol_pts = 5
    score += vol_pts
    details["volume"] = {"pts": vol_pts}
    
    # 4. RSI hızlı (5 puan) - 40-60 neutral = trend gücü
    rsi = ta.get("rsi_7", ta.get("rsi_14", 50))
    rsi_pts = 0
    if 40 <= rsi <= 60:
        rsi_pts = 5
    elif rsi > 70 or rsi < 30:
        rsi_pts = -5  # Aşırı bölge riski
    score += rsi_pts
    details["rsi"] = {"value": round(rsi, 1), "pts": rsi_pts}
    
    # Normalize to 0-50
    score = max(0, min(50, score))
    
    # Trend yönü
    if bullish > bearish and ema_dir in ["bullish", "weak_bullish"]:
        trend = "up"
    elif bearish > bullish and ema_dir in ["bearish", "weak_bearish"]:
        trend = "down"
    else:
        trend = "neutral"
    
    return {"score": round(score, 1), "trend": trend, "details": details}


def _analyze_1h(closes, ta) -> Dict:
    """1 saatlik analiz - 30 puan üzerinden"""
    if len(closes) < 20:
        return {"score": 15.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    score = 0.0
    details = {}
    current = float(closes[-1])
    
    # 1. EMA50 pozisyonu (15 puan)
    ema50 = ta.get("ema_50", current)
    ema_pts = 0
    if current > ema50 * 1.005:  # %0.5 üzerinde
        ema_pts = 15
        ema_dir = "above"
    elif current > ema50:
        ema_pts = 10
        ema_dir = "slightly_above"
    elif current < ema50 * 0.995:
        ema_pts = 15
        ema_dir = "below"
    elif current < ema50:
        ema_pts = 10
        ema_dir = "slightly_below"
    else:
        ema_dir = "at"
    score += ema_pts
    details["ema50"] = {"value": round(ema50, 2), "dir": ema_dir, "pts": ema_pts}
    
    # 2. MACD Histogram yönü (10 puan)
    macd_hist = ta.get("macd_hist", 0)
    macd_pts = 0
    if macd_hist > 0:
        macd_pts = 10
        macd_dir = "bullish"
    elif macd_hist < 0:
        macd_pts = 10
        macd_dir = "bearish"
    else:
        macd_dir = "neutral"
    score += macd_pts
    details["macd"] = {"hist": round(macd_hist, 4), "dir": macd_dir, "pts": macd_pts}
    
    # 3. Son 20 mum performans (5 puan)
    perf_pts = 0
    if len(closes) >= 20:
        change = (closes[-1] - closes[-20]) / closes[-20]
        if abs(change) > 0.01:  # %1 hareket
            perf_pts = 5
    score += perf_pts
    details["performance"] = {"pts": perf_pts}
    
    score = max(0, min(30, score))
    
    if current > ema50 and macd_dir == "bullish":
        trend = "up"
    elif current < ema50 and macd_dir == "bearish":
        trend = "down"
    else:
        trend = "neutral"
    
    return {"score": round(score, 1), "trend": trend, "details": details}


def _analyze_4h(closes, ta) -> Dict:
    """4 saatlik analiz - 20 puan üzerinden"""
    if len(closes) < 10:
        return {"score": 10.0, "trend": "neutral", "details": {"error": "insufficient data"}}
    
    score = 0.0
    details = {}
    current = float(closes[-1])
    
    # Son 10 mumun genel yönü
    first = float(closes[-10])
    change = (current - first) / first
    
    change_pts = 0
    if change > 0.02:  # %2 yukarı
        change_pts = 15
        trend = "up"
    elif change > 0.01:
        change_pts = 10
        trend = "up"
    elif change > 0.003:
        change_pts = 5
        trend = "up"
    elif change < -0.02:
        change_pts = 15
        trend = "down"
    elif change < -0.01:
        change_pts = 10
        trend = "down"
    elif change < -0.003:
        change_pts = 5
        trend = "down"
    else:
        trend = "neutral"
    score += change_pts
    details["change"] = {"pct": round(change * 100, 2), "pts": change_pts}
    
    # EMA20 ek kontrol (5 puan)
    ema20 = ta.get("ema_20", current)
    ema_pts = 0
    if current > ema20 and trend in ["up", "neutral"]:
        ema_pts = 5
    elif current < ema20 and trend in ["down", "neutral"]:
        ema_pts = 5
    score += ema_pts
    details["ema20"] = {"value": round(ema20, 2), "pts": ema_pts}
    
    score = max(0, min(20, score))
    
    return {"score": round(score, 1), "trend": trend, "details": details}


@router.get("/pulse-v3/{symbol}")
async def get_pulse_v3_analysis(symbol: str):
    """
    PULSE 3 - Hybrid Scalp: 3 Zamanlı, 3 Filtreli, Hızlı Karar (REGIME-AWARE)
    
    Zaman Dilimleri: 5m(%50) + 1H(%30) + 4H(%20)
    Sinyal Tipleri: SCOUT (40-65) / CONFIRM (65+) / HOLD (<40)
    R/R Minimum: Regime-dynamic (1.2-1.5)
    Cache: 5m=30sn, 1H=5dk, 4H=10dk
    
    REGIME-AWARE:
    - Order Block detection (ICT simplified) replaces basic S/R in trend
    - Direction filtering (no SELL in STRONG_TREND_UP)
    - Dynamic R/R based on regime
    - Entry zones adjusted for trend pullbacks
    """
    try:
        from services.ml_prediction_service import _compute_technical_indicators
        from services.market_regime_service import detect_regime, filter_signal_by_regime, interpret_rsi, check_fake_signal_timeout, detect_order_blocks
        import asyncio
        
        # ─── REGIME DETECTION ───────────────────────────────────────────
        regime = await detect_regime(symbol)
        
        # ─── FAKE SIGNAL TIMEOUT CHECK ──────────────────────────────────
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        
        # ─── PARALEL VERİ ÇEKME (Cache'li) ───────────────────────────────
        data_5m, data_1h, data_4h = await asyncio.gather(
            _fetch_tf_data(symbol, "5m", limit=50, cache_seconds=30),
            _fetch_tf_data(symbol, "1H", limit=60, cache_seconds=300),
            _fetch_tf_data(symbol, "4H", limit=30, cache_seconds=600)
        )
        
        if not data_5m or len(data_5m) < 15:
            return {"error": "Insufficient data for this symbol. Intraday data may not be available.", "error_key": "pulse.insufficientData"}
        
        # Convert 5m data
        c5 = np.array([c["close"] for c in data_5m], dtype=np.float64)
        h5 = np.array([c["high"] for c in data_5m], dtype=np.float64)
        l5 = np.array([c["low"] for c in data_5m], dtype=np.float64)
        v5 = np.array([c.get("volume", 0) for c in data_5m], dtype=np.float64)
        # Use live price from DataHub (updated every 30s)
        from services.data_fetcher import fetch_latest_price
        _live = await fetch_latest_price(symbol)
        current_price = float(_live) if _live else float(c5[-1])
        ta_5m = _compute_technical_indicators(c5, h5, l5, v5)
        
        # Convert 1H data
        ta_1h = {}
        if data_1h and len(data_1h) >= 20:
            c1h = np.array([c["close"] for c in data_1h], dtype=np.float64)
            h1h = np.array([c["high"] for c in data_1h], dtype=np.float64)
            l1h = np.array([c["low"] for c in data_1h], dtype=np.float64)
            v1h = np.array([c.get("volume", 0) for c in data_1h], dtype=np.float64)
            ta_1h = _compute_technical_indicators(c1h, h1h, l1h, v1h)
        else:
            c1h = c5  # Fallback
        
        # Convert 4H data
        ta_4h = {}
        if data_4h and len(data_4h) >= 10:
            c4h = np.array([c["close"] for c in data_4h], dtype=np.float64)
            h4h = np.array([c["high"] for c in data_4h], dtype=np.float64)
            l4h = np.array([c["low"] for c in data_4h], dtype=np.float64)
            v4h = np.array([c.get("volume", 0) for c in data_4h], dtype=np.float64)
            ta_4h = _compute_technical_indicators(c4h, h4h, l4h, v4h)
        else:
            c4h = c5  # Fallback
        
        # ─── 3 ZAMANLI ANALİZ ────────────────────────────────────────────
        result_5m = _analyze_5m(c5, h5, l5, v5, ta_5m)
        result_1h = _analyze_1h(c1h, ta_1h)
        result_4h = _analyze_4h(c4h, ta_4h)
        
        # Ağırlıklı toplam skor
        total_score = result_5m["score"] + result_1h["score"] + result_4h["score"]
        # Max: 50 + 30 + 20 = 100
        
        # ─── YÖN BELİRLEME (regime-biased) ──────────────────────────────
        up_votes = sum(1 for r in [result_5m, result_1h, result_4h] if r["trend"] == "up")
        down_votes = sum(1 for r in [result_5m, result_1h, result_4h] if r["trend"] == "down")
        
        # Regime bias: in strong trend, bias toward trend direction
        if regime.regime == "STRONG_TREND_UP" and up_votes >= 1:
            direction = "BUY"  # 1 vote enough in strong uptrend
        elif regime.regime == "STRONG_TREND_DOWN" and down_votes >= 1:
            direction = "SELL"
        elif up_votes >= 2:
            direction = "BUY"
        elif down_votes >= 2:
            direction = "SELL"
        elif result_5m["trend"] != "neutral":
            direction = "BUY" if result_5m["trend"] == "up" else "SELL"
        else:
            direction = "NEUTRAL"
        
        # ─── SİNYAL TİPİ ────────────────────────────────────────────────
        if total_score >= 56:  # 56'ya düşürüldü
            signal_type = "CONFIRM"
        elif total_score >= 35:  # 40'tan 35'e
            signal_type = "SCOUT"
        else:
            signal_type = "HOLD"
            direction = "NEUTRAL"
        
        # ─── DIRECTION FILTER (enforce regime rules) ────────────────────
        direction, was_filtered, filter_reason = filter_signal_by_regime(direction, regime)
        notes = []
        if was_filtered:
            signal_type = "HOLD"
            notes.append(filter_reason)
        
        # ─── ORDER BLOCK DETECTION (4H) ─────────────────────────────────
        order_blocks_data = []
        ob_entry_zone = None
        if data_4h and len(data_4h) >= 20:
            o4h = np.array([c["open"] for c in data_4h], dtype=np.float64)
            h4h_arr = np.array([c["high"] for c in data_4h], dtype=np.float64)
            l4h_arr = np.array([c["low"] for c in data_4h], dtype=np.float64)
            c4h_arr = np.array([c["close"] for c in data_4h], dtype=np.float64)
            v4h_arr = np.array([c.get("volume", 0) for c in data_4h], dtype=np.float64)
            
            obs = detect_order_blocks(o4h, h4h_arr, l4h_arr, c4h_arr, v4h_arr, lookback=20)
            
            for ob in obs:
                ob_dict = {
                    "type": ob.type, "low": round(ob.low, 2), "high": round(ob.high, 2),
                    "strength": ob.strength,
                    "is_nearby": abs(current_price - (ob.low + ob.high) / 2) / current_price < 0.02
                }
                order_blocks_data.append(ob_dict)
                
                # In trend mode, if price is at a bullish OB = strong buy zone
                if regime.regime == "STRONG_TREND_UP" and ob.type == "bullish" and ob_dict["is_nearby"]:
                    if current_price >= ob.low and current_price <= ob.high * 1.005:
                        ob_entry_zone = ob
                        if signal_type == "SCOUT":
                            signal_type = "CONFIRM"
                            notes.append(f"Order Block onayı: Fiyat bullish OB'de ({ob.low:.0f}-{ob.high:.0f})")
                elif regime.regime == "STRONG_TREND_DOWN" and ob.type == "bearish" and ob_dict["is_nearby"]:
                    if current_price <= ob.high and current_price >= ob.low * 0.995:
                        ob_entry_zone = ob
                        if signal_type == "SCOUT":
                            signal_type = "CONFIRM"
                            notes.append(f"Order Block onayı: Fiyat bearish OB'de ({ob.low:.0f}-{ob.high:.0f})")
        
        # ─── SEVİYELER (5m verilerinden) ─────────────────────────────────
        high_20 = float(np.max(h5[-20:])) if len(h5) >= 20 else float(np.max(h5))
        low_20 = float(np.min(l5[-20:])) if len(l5) >= 20 else float(np.min(l5))
        pivot = (high_20 + low_20 + current_price) / 3
        r1 = 2 * pivot - low_20
        r2 = pivot + (high_20 - low_20)
        s1 = 2 * pivot - high_20
        s2 = pivot - (high_20 - low_20)
        
        # Hedef/Stop — regime-aware ATR multipliers
        atr_val = ta_5m.get("atr_14", abs(high_20 - low_20) / 20)
        atr_target_mult = 1.5
        atr_stop_mult = 1.0
        if regime.regime in ["STRONG_TREND_UP", "STRONG_TREND_DOWN"]:
            atr_target_mult = 2.5  # Trend: wider target (küçük risk, büyük kâr)
            atr_stop_mult = 0.8    # Trend: tighter stop (trailing)
        
        if direction == "BUY":
            target = r1 if r1 > current_price else current_price + atr_val * atr_target_mult
            stop = s1 if s1 < current_price else current_price - atr_val * atr_stop_mult
        elif direction == "SELL":
            target = s1 if s1 < current_price else current_price - atr_val * atr_target_mult
            stop = r1 if r1 > current_price else current_price + atr_val * atr_stop_mult
        else:
            target = r1 if r1 > current_price else current_price + atr_val * 1.0
            stop = s1 if s1 < current_price else current_price - atr_val * 1.0
        
        potential_profit = abs(target - current_price)
        potential_loss = abs(current_price - stop)
        rr_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
        
        # ─── R/R FİLTRE (regime-dynamic) ─────────────────────────────────
        min_rr = regime.min_rr
        if signal_type == "CONFIRM" and rr_ratio < min_rr:
            signal_type = "SCOUT"
            notes.append(f"R/R low ({rr_ratio:.2f} < {min_rr}), downgraded to SCOUT")
        elif signal_type == "SCOUT" and rr_ratio < 1.0:
            signal_type = "HOLD"
            direction = "NEUTRAL"
            notes.append(f"R/R too low ({rr_ratio:.2f})")
        
        # Timeframe conflict note
        if up_votes == 1 and down_votes == 1:
            notes.append("Timeframes conflicting")
        
        # ─── FAKE SIGNAL TIMEOUT ────────────────────────────────────────
        if is_timed_out and signal_type == "CONFIRM":
            signal_type = "SCOUT"
            notes.append(f"Timeout aktif: {timeout_reason}")
        
        # ─── RSI REGIME CHECK ───────────────────────────────────────────
        rsi_5m = ta_5m.get("rsi_14", 50)
        rsi_check = interpret_rsi(rsi_5m, regime, direction)
        if rsi_check["action"] == "boost":
            total_score += rsi_check["score_adjustment"]
            notes.append(rsi_check["note"])
        elif rsi_check["action"] == "caution" and signal_type == "CONFIRM":
            signal_type = "SCOUT"
            notes.append(rsi_check["note"])
        
        # ─── SUGGESTION ──────────────────────────────────────────────────
        regime_tag = f" [{regime.regime}]" if regime.regime != "TRANSITION" else ""
        if signal_type == "CONFIRM":
            if direction == "BUY":
                suggestion = f"🚀 Strong BUY{regime_tag} (score: {total_score:.0f}). 3 TF aligned. Target: {target:.0f}, Stop: {stop:.0f}"
            else:
                suggestion = f"🔻 Strong SELL{regime_tag} (score: {total_score:.0f}). 3 TF aligned. Target: {target:.0f}, Stop: {stop:.0f}"
        elif signal_type == "SCOUT":
            if direction == "BUY":
                suggestion = f"👀 Bullish momentum{regime_tag} (score: {total_score:.0f}). Hold above {s1:.0f}."
            elif direction == "SELL":
                suggestion = f"👀 Bearish momentum{regime_tag} (score: {total_score:.0f}). Hold below {r1:.0f}."
            else:
                suggestion = f"👀 Watch mode{regime_tag} (score: {total_score:.0f}). Direction unclear."
        else:
            suggestion = f"⏱️ Hold{regime_tag} (score: {total_score:.0f}). No strong trend."
        
        if notes:
            suggestion += f" | {', '.join(notes)}"
        
        # ─── GİRİŞ BÖLGELERİ (regime-aware) ────────────────────────────
        atr = ta_5m.get("atr_14", current_price * 0.002)
        entry_zones = []
        if direction == "BUY":
            if regime.regime == "STRONG_TREND_UP" and ob_entry_zone:
                # Use Order Block as entry zone in trend
                entry_zones = [
                    {"price": round(current_price, 2), "share": 30, "label": "Instant"},
                    {"price": round(ob_entry_zone.high, 2), "share": 40, "label": "Order Block Top"},
                    {"price": round(ob_entry_zone.low, 2), "share": 30, "label": "Order Block Bottom"},
                ]
            else:
                entry_zones = [
                    {"price": round(current_price, 2), "share": 40, "label": "Instant"},
                    {"price": round(current_price - atr * 0.5, 2), "share": 30, "label": "On Dip"},
                    {"price": round(current_price - atr, 2), "share": 30, "label": "Support"},
                ]
        elif direction == "SELL":
            if regime.regime == "STRONG_TREND_DOWN" and ob_entry_zone:
                entry_zones = [
                    {"price": round(current_price, 2), "share": 30, "label": "Instant"},
                    {"price": round(ob_entry_zone.low, 2), "share": 40, "label": "Order Block Bottom"},
                    {"price": round(ob_entry_zone.high, 2), "share": 30, "label": "Order Block Top"},
                ]
            else:
                entry_zones = [
                    {"price": round(current_price, 2), "share": 40, "label": "Instant"},
                    {"price": round(current_price + atr * 0.5, 2), "share": 30, "label": "On Rise"},
                    {"price": round(current_price + atr, 2), "share": 30, "label": "Resistance"},
                ]
        
        # ─── LEARNING ENTEGRASYONU ────────────────────────────────────────
        # Log ALL BUY/SELL signals (not just CONFIRM/SCOUT)
        if direction in ["BUY", "SELL"]:
            try:
                from services.prediction_logger import log_prediction
                await log_prediction(
                    symbol=symbol,
                    context={
                        "source": "PULSE_V3",
                        "total_score": total_score,
                        "signal_type": signal_type,
                        "regime": regime.regime,
                        "tf_scores": {"5m": result_5m["score"], "1h": result_1h["score"], "4h": result_4h["score"]},
                        "ml_prediction": {
                            "direction": direction,
                            "confidence": round(total_score),
                            "entry_price": current_price,
                            "target_price": target,
                            "stop_price": stop
                        }
                    },
                    analysis={
                        "final_decision": direction,
                        "confidence": round(total_score),
                        "model_used": "PULSE-V3-Hybrid-Regime"
                    },
                    timeframe="5m",
                    strategy="PULSE_V3",
                    model_type="pulse3",
                )
                logger.info(f"PULSE-V3 signal logged: {symbol} {direction} ({signal_type}) @ {current_price}")
            except Exception as log_err:
                logger.warning(f"Failed to log PULSE-V3 prediction: {log_err}")
        
        # ─── OIL ANALYSIS (CL.COMM only) ─────────────────────────────────
        oil_analysis = None
        if symbol == "CL.COMM":
            try:
                from services.oil_analysis_service import generate_oil_analysis
                from services.market_data_service import get_ohlcv_data as get_ohlcv

                # Fetch DXY and S&P500 data for correlation
                dxy_data, spx_data = None, None
                try:
                    dxy_candles = await get_ohlcv("DX-Y.NYB", "5m", limit=50)
                    if dxy_candles:
                        dxy_data = dxy_candles
                except Exception:
                    pass
                try:
                    spx_candles = await get_ohlcv("GSPC.INDX", "5m", limit=50)
                    if spx_candles:
                        spx_data = spx_candles
                except Exception:
                    pass

                oil_analysis = await generate_oil_analysis(
                    wti_candles=data_5m,
                    session=regime.session,
                    dxy_candles=dxy_data,
                    spx_candles=spx_data,
                )

                # Blend oil composite score into total (20% weight)
                oil_score_adjust = oil_analysis.get("composite_score", 0) * 0.2
                total_score = total_score * 0.8 + oil_score_adjust

                # Add oil-specific notes
                for r in oil_analysis.get("risks", []):
                    notes.append(r)
                for m in oil_analysis.get("modifiers", []):
                    notes.append(m)
            except Exception as oil_err:
                logger.warning(f"Oil analysis error for CL.COMM: {oil_err}")

        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "pulse_score": round(total_score, 1),
            "max_score": 100,
            "signal_type": signal_type,
            "direction": direction,
            "confidence": min(95, int(total_score)),
            "price": round(current_price, 2),
            "timeframes": {
                "5m": {"raw_score": result_5m["score"], "max": 50, "trend": result_5m["trend"], "details": result_5m["details"]},
                "1h": {"raw_score": result_1h["score"], "max": 30, "trend": result_1h["trend"], "details": result_1h["details"]},
                "4h": {"raw_score": result_4h["score"], "max": 20, "trend": result_4h["trend"], "details": result_4h["details"]}
            },
            "levels": {
                "r2": round(r2, 2),
                "r1": round(r1, 2),
                "pivot": round(pivot, 2),
                "s1": round(s1, 2),
                "s2": round(s2, 2),
                "target": round(target, 2),
                "stop": round(stop, 2)
            },
            "regime": {
                "type": regime.regime,
                "adx": regime.adx,
                "session": regime.session,
                "is_ath": regime.is_ath_zone,
                "rsi_mode": "trend_momentum" if regime.rsi_trend_boost else "classic",
                "allowed_directions": regime.allowed_directions,
                "min_rr": regime.min_rr,
            },
            "order_blocks": order_blocks_data[:4],
            "rr_ratio": round(rr_ratio, 2),
            "suggestion": suggestion,
            "entry_zones": entry_zones,
            "notes": notes,
            "valid_for_seconds": 300,
            # Oil-specific analysis (only for CL.COMM)
            **({"oil_analysis": {
                "composite_score": oil_analysis["composite_score"],
                "label": oil_analysis["label"],
                "confidence": oil_analysis["confidence"],
                "layers": oil_analysis["layers"],
                "key_levels": oil_analysis["key_levels"],
                "reasons": oil_analysis["reasons"],
                "risks": oil_analysis["risks"],
            }} if oil_analysis else {}),
        }
        
    except Exception as e:
        logger.error(f"PULSE V3 analysis error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME ENDPOINT - Piyasa Rejimi Algılama
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/regime/{symbol}")
async def get_market_regime(symbol: str, force_refresh: bool = False):
    """
    Market Regime Detection - Piyasa Rejimi
    
    Regimes:
    - STRONG_TREND_UP: ADX>25, bullish structure → only LONG
    - STRONG_TREND_DOWN: ADX>25, bearish structure → only SHORT
    - RANGING: ADX<20, low volatility → mean reversion
    - TRANSITION: everything else → low risk
    
    Returns regime info, model weights, RSI thresholds, ATH status, session.
    Cached for 30 minutes (use force_refresh=true to override).
    """
    try:
        from services.market_regime_service import get_regime_info, check_fake_signal_timeout
        
        regime_info = await get_regime_info(symbol)
        
        # Add fake signal timeout status
        is_timed_out, timeout_until, timeout_reason = await check_fake_signal_timeout(symbol)
        regime_info["fake_signal_timeout"] = {
            "active": is_timed_out,
            "until": timeout_until,
            "reason": timeout_reason,
        }
        
        return regime_info
        
    except Exception as e:
        logger.error(f"Regime detection error: {e}")
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


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL KARŞILAŞTIRMA
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/compare/{symbol}")
async def compare_models(symbol: str, timeframe: str = "M15"):
    """
    Run both EMEL and PULSE models and compare their signals.
    Logs predictions to database for performance tracking.
    """
    try:
        from services.model_comparison_service import run_model_comparison
        
        result = await run_model_comparison(symbol, timeframe)
        return result
        
    except Exception as e:
        logger.error(f"Model comparison error: {e}")
        return {"error": str(e)}


@router.get("/performance-stats")
async def get_performance_stats(days: int = 7):
    """
    Get performance statistics for EMEL vs PULSE models.
    """
    try:
        from services.model_comparison_service import get_model_performance_stats
        
        stats = await get_model_performance_stats(days)
        return stats
        
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# DATAHUB DEBUG - Hacim Verisi Kontrolü
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/debug/datahub/{symbol}")
async def debug_datahub_volumes(symbol: str):
    """
    DataHub'daki hacim verilerini kontrol et.
    Hacim analizinin neden 0.0 gösterdiğini debug etmek için.
    """
    try:
        from services.data_hub import get_candles, get_hub_status
        from services.market_data_service import get_ohlcv_data
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_hub_status": get_hub_status(),
            "candle_data": {}
        }
        
        # Her timeframe için hacim verisini kontrol et
        for tf in ["5m", "15m", "30m", "1h", "4h", "eod"]:
            candles = get_candles(symbol, tf, limit=20)
            if candles:
                volumes = [c.get("volume", 0) for c in candles]
                result["candle_data"][tf] = {
                    "count": len(candles),
                    "volumes_sample": volumes[-5:],  # Son 5 hacim
                    "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
                    "max_volume": max(volumes) if volumes else 0,
                    "min_volume": min(volumes) if volumes else 0,
                    "total_volume": sum(volumes),
                }
            else:
                result["candle_data"][tf] = {"count": 0, "error": "No data in cache"}
        
        # EMEL'in kullandığı get_ohlcv_data ile karşılaştır
        ohlcv_1h = await get_ohlcv_data(symbol, "1h", limit=20)
        if ohlcv_1h:
            volumes = [c.get("volume", 0) for c in ohlcv_1h]
            result["ohlcv_1h_via_market_data_service"] = {
                "count": len(ohlcv_1h),
                "volumes_sample": volumes[-5:],
                "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
            }
        else:
            result["ohlcv_1h_via_market_data_service"] = {"error": "No data"}
        
        return result
        
    except Exception as e:
        logger.error(f"DataHub debug error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}

