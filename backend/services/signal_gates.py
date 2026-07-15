"""Merkezi sinyal kapıları — 2026-07-01 gösterge denetimi uygulaması.

Kaynak analiz: GOSTERGE_UYGUNLUK_ANALIZ_RAPORU_2026-07-01.md
Kanıt (60 gün prediction_logs):
  - XAUUSD SELL WR: pulse1 %19.1, pulse2 %20.3, pulse3 %19.7, smc %31.8
    (BUY tarafı %64-85) → trend/ATH ortamında SELL üretimi ana kayıp kaynağı.
  - EMEL'in ATH SELL bloğu ile XAUUSD %84.8 WR → koruma kanıtlı, genelleniyor.
  - GDAXI pulse1: düz %25 / inverse %38 WR → sinyal bilgi taşımıyor, askıda.
  - Saat etkisi: XAUUSD 20 UTC %37.9, 01-03 UTC ~%42; GDAXI 07-12 UTC %40-43.

Tüm kapılar fail-open tasarlanmıştır: veri/servis hatasında sinyali BLOKLAMAZ,
sadece loglar. Env bayrakları ile tek tek kapatılabilir.

2026-07-10 eki (MT5 işlem otopsisi — analiz_paketi_2026-07-09/RAPOR_MT5_ISLEM_OTOPSISI.md):
  - NDX {03,04,18,22} UTC + USOIL <12 UTC seans blokları (14g gerçek MT5:
    ΔPnL +5.078 / +1.868; temporal split tutarlı).
  - entry_score_gate: 8 koşullu giriş skoru (saat, 5m/30m trend, EMA200 tarafı,
    ADX, hacim, 1h momentum, bıçak-yakalama). Skor < eşik → blok.
    Kanıt: NDX skor≥7 WR %60→%65, USOIL skor≥7 WR %49→%72.

Env bayrakları:
  XAU_TREND_SELL_GATE=1      → XAUUSD trend-yönü SELL kapısı (default açık)
  SESSION_GATES_ENABLED=1    → saat/seans kapıları (default açık)
  CALENDAR_GATE_ENABLED=1    → yüksek etkili takvim olayı ±30dk kapısı (default açık)
  GDAXI_PULSE1_ENABLED=0     → GDAXI'de pulse1 (default KAPALI/askıda)
  CALENDAR_GATE_MINUTES=30   → takvim penceresi (dakika)
  ENTRY_SCORE_GATE_ENABLED=1 → 8 koşullu giriş skoru kapısı (default açık)
  ENTRY_SCORE_MIN=7          → minimum skor eşiği (0-8)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ─── Sabitler ────────────────────────────────────────────────────────────────

_XAU_ALIASES = {"XAUUSD", "XAUUSD.FOREX", "GOLD"}

#: Yön kapılarının uygulandığı modeller (EMEL kendi ATH kapısına sahip,
#: ML/meta kendi eşiklerini yönetir — rapor bölüm 3/6).
TREND_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

#: Seans kapısı scalp-karakterli modellere uygulanır.
SESSION_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

#: Takvim kapısı: rapor aksiyon #9 (PULSE + EMEL + SMC).
CALENDAR_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc", "emel"}

#: UTC saat → blok. Rapor bölüm 2 saatlik WR verisi.
#: XAUUSD: 20:00-20:59 (%37.9 WR) + 01:00-02:59 (~%42 WR, Asya gecesi)
#: GDAXI:  07:00-07:59 (Xetra açılış gürültüsü; sabah bandı %39.9-42.8 WR)
#: NDX:    03-04 UTC (Asya gecesi) + 18 UTC (öğle dönüşü) + 22 UTC (kapanış
#:         sonrası) — 14g MT5 otopsisi: 23 işlem blok → ΔPnL +5.078, WR 60→68.
#: USOIL:  00-11 UTC (NY enerji seansı öncesi) — ΔPnL +1.868, WR 49→59.
SESSION_BLOCK_HOURS_UTC = {
    "XAUUSD": (20, 1, 2),
    "GDAXI.INDX": (7,),
    "NDX.INDX": (3, 4, 18, 22),
    "USOIL.FOREX": tuple(range(0, 12)),
}

_H4_EMA_PERIOD = 50
_H4_MIN_CANDLES = 55


# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def _flag(name: str, default: str = "1") -> bool:
    """Env bayrağı: '0' → kapalı, diğer her şey → açık."""
    return os.getenv(name, default) != "0"


def _norm_symbol(symbol: str) -> str:
    return (symbol or "").upper().strip()


def _base_model(model_type: str) -> str:
    """'ml:balanced' → 'ml', 'pulse1' → 'pulse1'."""
    return (model_type or "").lower().strip().split(":")[0]


def _is_xau(symbol: str) -> bool:
    return _norm_symbol(symbol) in _XAU_ALIASES


def _ema(values: Sequence[float], period: int) -> Optional[float]:
    """TradingView uyumlu EMA (emel_pulse._calc_ema ile aynı yaklaşım)."""
    vals = [float(v) for v in values if v is not None]
    if len(vals) < period:
        return None
    alpha = 2.0 / (period + 1.0)
    ema = sum(vals[:period]) / period
    for v in vals[period:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema


# ─── Kapı 1: GDAXI pulse1 askıya alma ────────────────────────────────────────

def pulse1_symbol_enabled(symbol: str) -> bool:
    """GDAXI'de pulse1 askıda (60g: 446W/1339L, inverse dahi %38 WR).

    GDAXI_PULSE1_ENABLED=1 ile tekrar açılabilir.
    """
    if _norm_symbol(symbol) == "GDAXI.INDX":
        return _flag("GDAXI_PULSE1_ENABLED", "0")
    return True


# ─── Kapı 2: XAUUSD trend-yönü SELL kapısı ──────────────────────────────────

async def xau_trend_sell_gate(
    symbol: str,
    direction: str,
    regime: Any = None,
) -> Tuple[bool, Optional[str]]:
    """XAUUSD'de trend/ATH ortamında counter-trend SELL'i blokla.

    EMEL'in kanıtlanmış ATH-SELL bloğunun (XAUUSD %84.8 WR) genellemesi.
    Blok koşulu (sırayla):
      1. Rejim STRONG_TREND_DOWN ise → SELL serbest (trend yönü).
      2. Rejim STRONG_TREND_UP veya is_ath_zone ise → SELL blok.
      3. H4 kapanış > H4 EMA50 ise → SELL blok (H4 trend up).
    Veri alınamazsa fail-open (blok yok).

    Returns:
        (allowed, reason): allowed=False ise reason blok açıklamasıdır.
    """
    if not _flag("XAU_TREND_SELL_GATE"):
        return True, None
    if direction != "SELL" or not _is_xau(symbol):
        return True, None

    try:
        if regime is None:
            from services.market_regime_service import detect_regime
            regime = await detect_regime(symbol)

        regime_name = str(getattr(regime, "regime", "") or "").upper()
        is_ath = bool(getattr(regime, "is_ath_zone", False))

        if regime_name == "STRONG_TREND_DOWN":
            return True, None
        if is_ath or regime_name == "STRONG_TREND_UP":
            return False, (
                f"XAU SELL kapısı: {'ATH bölgesi' if is_ath else 'STRONG_TREND_UP'} "
                "— counter-trend SELL blok (rapor aksiyon #2)"
            )

        # H4 trend kontrolü
        from services.market_data_service import get_ohlcv_data
        candles = await get_ohlcv_data(symbol, timeframe="4h", limit=_H4_MIN_CANDLES + 10)
        if candles and len(candles) >= _H4_MIN_CANDLES:
            closes = [c.get("close") for c in candles]
            ema50_h4 = _ema(closes, _H4_EMA_PERIOD)
            last_close = float(closes[-1]) if closes[-1] is not None else None
            if ema50_h4 is not None and last_close is not None and last_close > ema50_h4:
                return False, (
                    f"XAU SELL kapısı: H4 trend up (close {last_close:.2f} > "
                    f"EMA50 {ema50_h4:.2f}) — counter-trend SELL blok"
                )
    except Exception as exc:  # fail-open
        logger.debug(f"xau_trend_sell_gate fail-open ({symbol}): {exc}")

    return True, None


async def ndx_smc_sell_gate(
    symbol: str,
    direction: str,
    model_type: str,
) -> Tuple[bool, Optional[str]]:
    """NDX'te SMC counter-trend SELL'i blokla (H4 close > EMA50 iken).

    Kanıt (14g prediction_logs, 2026-07-15 denetimi): smc NDX SELL
    "transition" rejiminde 1W/28L (%3.4 WR); smc_inv NDX %90 WR — yani SMC'nin
    premium-zone bearish OB satışları NASDAQ'ın yükseliş düzeltmelerinde
    sistematik ters. XAU SELL kapısıyla aynı H4-EMA50 kuralı, yalnız smc+NDX.
    Env: NDX_SMC_SELL_GATE=0 ile kapatılır. Fail-open.
    """
    if not _flag("NDX_SMC_SELL_GATE"):
        return True, None
    if direction != "SELL" or _norm_symbol(symbol) != "NDX.INDX":
        return True, None
    if _base_model(model_type) != "smc":
        return True, None

    try:
        from services.market_data_service import get_ohlcv_data
        candles = await get_ohlcv_data(symbol, timeframe="4h", limit=_H4_MIN_CANDLES + 10)
        if candles and len(candles) >= _H4_MIN_CANDLES:
            closes = [c.get("close") for c in candles]
            ema50_h4 = _ema(closes, _H4_EMA_PERIOD)
            last_close = float(closes[-1]) if closes[-1] is not None else None
            if ema50_h4 is not None and last_close is not None and last_close > ema50_h4:
                return False, (
                    f"NDX SMC SELL kapısı: H4 trend up (close {last_close:.2f} > "
                    f"EMA50 {ema50_h4:.2f}) — counter-trend SELL blok (14g: 1W/28L)"
                )
    except Exception as exc:  # fail-open
        logger.debug(f"ndx_smc_sell_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Kapı 3: Seans/saat kapısı ───────────────────────────────────────────────

def session_gate(symbol: str, now: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
    """Düşük-WR saat pencerelerinde yeni sinyal üretimini blokla.

    Returns:
        (allowed, reason)
    """
    if not _flag("SESSION_GATES_ENABLED"):
        return True, None

    sym = _norm_symbol(symbol)
    if sym in _XAU_ALIASES:
        sym = "XAUUSD"
    blocked_hours = SESSION_BLOCK_HOURS_UTC.get(sym)
    if not blocked_hours:
        return True, None

    hour = (now or datetime.now(timezone.utc)).hour
    if hour in blocked_hours:
        return False, (
            f"Seans kapısı: {sym} için {hour:02d}:00-{hour:02d}:59 UTC düşük-WR "
            "penceresi (rapor bölüm 2.4) — yeni sinyal blok"
        )
    return True, None


# ─── Kapı 5: 8 koşullu giriş skoru ──────────────────────────────────────────

#: Skor kapısının kanıt tabanı yalnızca bu sembolleri kapsıyor (14g MT5 otopsisi).
ENTRY_SCORE_SYMBOLS = {"NDX.INDX", "USOIL.FOREX"}

#: Skor kapısı scalp-karakterli modellere uygulanır (seans kapısıyla aynı küme).
ENTRY_SCORE_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

_SCORE_5M_LIMIT = 260   # EMA200(5m) + ADX/ATR ısınması için
_SCORE_30M_LIMIT = 60   # EMA50(30m) için

#: Otopsideki eşikler 1m ATR cinsindendi; canlıda 1m stream yok → 5m ATR'ye
#: ölçeklendi (1m ATR ≈ 5m ATR / √5): mom60 > −1.0·ATR1m ≈ −0.45·ATR5m,
#: run30 > −1.5·ATR1m ≈ −0.67·ATR5m.
_MOM60_MIN_ATR5 = -0.45
_RUN30_MIN_ATR5 = -0.67
_ADX_MIN = 20.0
_VOL_RATIO_MAX = 1.5


def _wilder_atr(candles: Sequence[dict], period: int = 14) -> Optional[float]:
    """Wilder ATR — son değer. Veri yetersizse None."""
    if not candles or len(candles) < period + 1:
        return None
    atr = None
    trs: List[float] = []
    prev_close = None
    for c in candles:
        h, l, cl = float(c["high"]), float(c["low"]), float(c["close"])
        tr = h - l if prev_close is None else max(h - l, abs(h - prev_close), abs(l - prev_close))
        prev_close = cl
        if atr is None:
            trs.append(tr)
            if len(trs) == period:
                atr = sum(trs) / period
        else:
            atr = (atr * (period - 1) + tr) / period
    return atr


def _wilder_adx(candles: Sequence[dict], period: int = 14) -> Optional[float]:
    """Wilder ADX — son değer. Veri yetersizse None."""
    if not candles or len(candles) < 3 * period:
        return None
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    alpha = 1.0 / period
    s_tr = s_plus = s_minus = 0.0
    adx = None
    for i in range(1, len(candles)):
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        plus_dm = up if (up > dn and up > 0) else 0.0
        minus_dm = dn if (dn > up and dn > 0) else 0.0
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        if i == 1:
            s_tr, s_plus, s_minus = tr, plus_dm, minus_dm
            continue
        s_tr = s_tr * (1 - alpha) + tr * alpha
        s_plus = s_plus * (1 - alpha) + plus_dm * alpha
        s_minus = s_minus * (1 - alpha) + minus_dm * alpha
        if s_tr <= 0:
            continue
        pdi = 100.0 * s_plus / s_tr
        mdi = 100.0 * s_minus / s_tr
        dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) > 0 else 0.0
        adx = dx if adx is None else adx * (1 - alpha) + dx * alpha
    return adx


def compute_entry_score(
    symbol: str,
    direction: str,
    candles_5m: Optional[Sequence[dict]],
    candles_30m: Optional[Sequence[dict]],
    now: Optional[datetime] = None,
) -> Tuple[int, List[str]]:
    """8 koşullu giriş skorunu hesapla (saf/senkron; test edilebilir çekirdek).

    Her koşul veri yetersizliğinde SAĞLANMIŞ sayılır (fail-open). Dönen liste
    yalnızca İHLAL edilen koşulların adlarıdır; skor = 8 − ihlal sayısı.
    """
    sgn = 1.0 if direction == "BUY" else -1.0
    fails: List[str] = []

    # 1) saat penceresi
    hour = (now or datetime.now(timezone.utc)).hour
    blocked = SESSION_BLOCK_HOURS_UTC.get(_norm_symbol(symbol)) or ()
    if hour in blocked:
        fails.append("saat_penceresi")

    c5 = list(candles_5m or [])
    closes5 = [float(c["close"]) for c in c5]
    atr5 = _wilder_atr(c5)
    last5 = closes5[-1] if closes5 else None

    # 2) 5m trend hizası (close vs EMA50)
    ema50_5 = _ema(closes5, 50)
    if last5 is not None and ema50_5 is not None and sgn * (last5 - ema50_5) <= 0:
        fails.append("5m_trend")

    # 3) 30m trend hizası
    c30 = list(candles_30m or [])
    closes30 = [float(c["close"]) for c in c30]
    ema50_30 = _ema(closes30, 50)
    if closes30 and ema50_30 is not None and sgn * (closes30[-1] - ema50_30) <= 0:
        fails.append("30m_trend")

    # 4) EMA200 doğru tarafta (5m)
    ema200_5 = _ema(closes5, 200)
    if last5 is not None and ema200_5 is not None and sgn * (last5 - ema200_5) <= 0:
        fails.append("ema200_tarafi")

    # 5) ADX(5m) ≥ 20 (trendsiz piyasa filtresi)
    adx5 = _wilder_adx(c5)
    if adx5 is not None and adx5 < _ADX_MIN:
        fails.append("adx_dusuk")

    # 6) hacim sakin (son 5m hacmi / 60-bar ortalaması < 1.5)
    vols = [float(c.get("volume") or 0) for c in c5]
    if len(vols) >= 61:
        base = sum(vols[-61:-1]) / 60.0
        if base > 0 and vols[-1] / base >= _VOL_RATIO_MAX:
            fails.append("hacim_patlamasi")

    # 7) 1h momentum lehte (12×5m bar, ATR5 ölçekli)
    if last5 is not None and atr5 and len(closes5) >= 13:
        if sgn * (last5 - closes5[-13]) / atr5 <= _MOM60_MIN_ATR5:
            fails.append("1h_karsi_momentum")

    # 8) bıçak yakalama değil (son 30dk = 6×5m bar)
    if last5 is not None and atr5 and len(closes5) >= 7:
        if sgn * (last5 - closes5[-7]) / atr5 <= _RUN30_MIN_ATR5:
            fails.append("bicak_yakalama")

    return 8 - len(fails), fails


async def entry_score_gate(
    symbol: str,
    direction: str,
    now: Optional[datetime] = None,
) -> Tuple[bool, Optional[str]]:
    """8 koşullu giriş skoru kapısı — skor < ENTRY_SCORE_MIN ise blok.

    Kanıt: analiz_paketi_2026-07-09/RAPOR_MT5_ISLEM_OTOPSISI.md §6
    (NDX skor≥7: WR %60→%65; USOIL skor≥7: WR %49→%72; bloklanan işlemlerin
    toplam PnL'i her iki sembolde negatif). Veri alınamazsa fail-open.
    """
    if not _flag("ENTRY_SCORE_GATE_ENABLED"):
        return True, None
    if _norm_symbol(symbol) not in ENTRY_SCORE_SYMBOLS:
        return True, None

    try:
        min_score = int(os.getenv("ENTRY_SCORE_MIN", "7"))
    except ValueError:
        min_score = 7

    try:
        from services.market_data_service import get_ohlcv_data
        candles_5m = await get_ohlcv_data(symbol, timeframe="5m", limit=_SCORE_5M_LIMIT)
        candles_30m = await get_ohlcv_data(symbol, timeframe="30m", limit=_SCORE_30M_LIMIT)
        score, fails = compute_entry_score(symbol, direction, candles_5m, candles_30m, now=now)
        if score < min_score:
            logger.info(
                f"entry_score_gate BLOCK {symbol} {direction}: {score}/8 < {min_score} "
                f"(ihlal: {', '.join(fails)})"
            )
            return False, (
                f"Giriş skoru kapısı: {score}/8 < {min_score} "
                f"(ihlal: {', '.join(fails)}) — yeni sinyal blok"
            )
        # Telemetri: geçen skorlar da ölçülebilsin (log-grep ile dağılım).
        logger.info(f"entry_score_gate PASS {symbol} {direction}: {score}/8")
    except Exception as exc:  # fail-open
        # Sessiz kalıcı no-op'u görünür kıl: veri hatası sürekli yaşanıyorsa
        # kapı fiilen devre dışı demektir — WARNING seviyesinde raporla.
        logger.warning(f"entry_score_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Kapı 4: Ekonomik takvim kapısı ─────────────────────────────────────────

async def calendar_gate(symbol: str) -> Tuple[bool, Optional[str]]:
    """Yüksek etkili takvim olayı ±CALENDAR_GATE_MINUTES içinde sinyal blok.

    Fail-open: takvim servisi hata verirse blok uygulanmaz.
    """
    if not _flag("CALENDAR_GATE_ENABLED"):
        return True, None

    try:
        minutes = int(os.getenv("CALENDAR_GATE_MINUTES", "30"))
    except ValueError:
        minutes = 30

    try:
        from services.economic_calendar_service import get_calendar_service
        events = await get_calendar_service().get_upcoming_high_impact_events(
            minutes_ahead=minutes
        )
        sym = _norm_symbol(symbol)
        for ev in events or []:
            affected = [
                _norm_symbol(s) for s in (getattr(ev, "affected_symbols", None) or [])
            ]
            hit = sym in affected or (
                sym in _XAU_ALIASES and any(a in _XAU_ALIASES for a in affected)
            )
            if hit:
                ev_name = getattr(ev, "event_name", None) or "high-impact event"
                return False, (
                    f"Takvim kapısı: {ev_name} ±{minutes}dk penceresi — yeni sinyal blok"
                )
    except Exception as exc:  # fail-open
        logger.debug(f"calendar_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Birleşik uygulayıcı ─────────────────────────────────────────────────────

async def apply_signal_gates(
    symbol: str,
    direction: str,
    model_type: str,
    regime: Any = None,
) -> Tuple[str, List[str]]:
    """Tüm kapıları sırasıyla uygula; bloklanırsa yönü HOLD'a düşür.

    Panel endpoint'leri (UI tutarlılığı) ve prediction_logger (güvenlik ağı)
    tarafından ortak kullanılır — idempotenttir.

    Args:
        symbol: Panel sembolü (örn. "XAUUSD", "GDAXI.INDX").
        direction: "BUY" | "SELL" | diğer (dokunulmaz).
        model_type: "pulse1" | "pulse2" | "pulse3" | "smc" | "emel" | "ml:*" ...
        regime: Varsa RegimeResult (tekrar tespit maliyetini önler).

    Returns:
        (yeni_direction, notlar): Bloklanırsa ("HOLD", [sebepler]).
    """
    notes: List[str] = []
    if direction not in ("BUY", "SELL"):
        return direction, notes

    base = _base_model(model_type)

    # 1) GDAXI pulse1 askıda
    if base == "pulse1" and not pulse1_symbol_enabled(symbol):
        notes.append("GDAXI pulse1 askıda (60g WR %25; GDAXI_PULSE1_ENABLED=1 ile açılır)")
        return "HOLD", notes

    # 2) XAU trend-yönü SELL kapısı
    if base in TREND_GATED_MODELS:
        allowed, reason = await xau_trend_sell_gate(symbol, direction, regime=regime)
        if not allowed:
            notes.append(reason or "XAU SELL kapısı")
            return "HOLD", notes

    # 2b) NDX SMC counter-trend SELL kapısı (2026-07-15 denetimi: 1W/28L)
    allowed, reason = await ndx_smc_sell_gate(symbol, direction, model_type)
    if not allowed:
        notes.append(reason or "NDX SMC SELL kapısı")
        return "HOLD", notes

    # 3) Seans kapısı
    if base in SESSION_GATED_MODELS:
        allowed, reason = session_gate(symbol)
        if not allowed:
            notes.append(reason or "Seans kapısı")
            return "HOLD", notes

    # 4) Takvim kapısı
    if base in CALENDAR_GATED_MODELS:
        allowed, reason = await calendar_gate(symbol)
        if not allowed:
            notes.append(reason or "Takvim kapısı")
            return "HOLD", notes

    # 5) Giriş skoru kapısı (en pahalı — veri çeker; en sona bırakıldı)
    if base in ENTRY_SCORE_GATED_MODELS:
        allowed, reason = await entry_score_gate(symbol, direction)
        if not allowed:
            notes.append(reason or "Giriş skoru kapısı")
            return "HOLD", notes

    return direction, notes
