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
  ENTRY_SCORE_GATE_ENABLED=1 → 8 koşullu giriş skoru kapısı (default açık — ölç+logla)
  ENTRY_SCORE_GATE_BLOCK=0   → 1 ise GERÇEKTEN bloklar (2026-08-11'den beri GÖLGE)
  ENTRY_SCORE_MIN=7          → minimum skor eşiği (0-8)
  FAKEOUT_GATE_ENABLED=1     → sahte kırılım radarı (default açık — değerlendir+logla)
  FAKEOUT_GATE_BLOCK=0       → 1 ise GERÇEKTEN bloklar (default GÖLGE: sadece log)
  FAKEOUT_BLOCK_PROB=80      → blok için minimum sahte-kırılım olasılığı (%)
  DEBATE_BIAS_GATE_ENABLED=1 → tartışma-bias karşıt-sinyal freni (default açık — logla)
  DEBATE_BIAS_GATE_BLOCK=0   → 1 ise GERÇEKTEN bloklar (default GÖLGE: sadece log)
  DEBATE_BIAS_VALID_MIN=240  → tartışma kararının geçerlilik penceresi (dakika)

2026-07-28 eki (Pulse NDX denetimi — pulse_ndx_denetimi_2026-07-28.md):
  MT5 botunun canlı-kanıtlı ön-giriş filtreleri Pulse'a GÖLGE modda taşındı.
  TREND_ALIGN_GATE_ENABLED=1   → 1h EMA50 hizası (bot 30g/332: hizalı %63.3 vs karşıt %43.4)
  TREND_ALIGN_GATE_BLOCK=0     → 1 ise gerçekten bloklar (default GÖLGE)
  WAVE_POSITION_GATE_ENABLED=1 → 4h dalga pozisyonu: tepe %60+ BUY / dip %40− SELL frenle
  WAVE_POSITION_GATE_BLOCK=0   → 1 ise gerçekten bloklar (default GÖLGE)
  VIX_REGIME_GATE_ENABLED=1    → VIX≥eşik→BUY lehte, altı→SELL lehte (plasebo p=0, OOS +17pp)
  VIX_REGIME_GATE_BLOCK=1      → default BLOK (2026-08-01: 30g gölge-eşdeğeri ölçüm
                                 lehte %58.0 vs karşıt %42.5, n=1098 — 0 ile gölgeye döner)
  VIX_REGIME_GATE_THRESHOLD=18.4

2026-08-01 eki (AI işlem envanteri denetimi):
  XAU_SCALP_GATE_ENABLED=1     → XAUUSD pulse1/2/3+smc scalp sinyali kapısı
                                 (30g: pulse XAU %16-18 WR, smc %25 — statik
                                 15-pip SL epoch'unda ölçüldü; aynı gün geometri
                                 atr_ladder_v1 + 1.5×ATR tabanına taşındı)
  XAU_SCALP_GATE_BLOCK=0       → default GÖLGE: yeni geometri epoch'u ölçülmeden
                                 bloklanmaz; 1 → XAU pulse/smc BUY+SELL → HOLD

2026-08-01 eki-2 (gün/saat denetimi — zaman-kalitesi katmanı):
  Kanıt (30g panel, çözülmüş, inv/ml_cross hariç):
    NDX 13-14 UTC %58 (n=683, taban %50, p<1e-4) → ALTIN pencere (dokunulmaz,
    factors.time_quality=golden etiketi). NDX 16 %45 (n=261) / 19 %45 (n=334)
    → ÇUKUR. NDX 18 UTC seans bloğu KALIR ama yüksek-güven sinyale altın-istisna
    açılır (kullanıcı kararı 2026-08-01: çukurda yalnız çok-emin işlem).
    USOIL Perşembe %35 (n=941) vs Salı/Çarş %50-52 → ÇUKUR günü.
    NOT: Cuma freni PANELDE YOK (NDX panel Cuma %53 — kanıt bot tarafında;
    Cuma kuralı bot'ta uygulanır).
  TQ_GATE_ENABLED=1            → zaman-kalitesi kapısı (pulse1/2/3+smc)
  TQ_GATE_BLOCK=1              → çukurda güven < eşik sinyali BLOKLAR (0 → gölge)
  TQ_COOL_MIN_CONF=80          → çukur penceresinde "çok emin" güven eşiği
  TQ_NDX_COOL_HOURS=16,17,19   → NDX çukur saatleri (UTC; 15 hariç — panel %53)
  TQ_USOIL_COOL_DOWS=4         → USOIL çukur günleri (ISO; 4=Perşembe)
  TQ_SESSION_EXCEPTION=1       → NDX 18 UTC: güven ≥ eşik ise seans bloğunu aş
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


# ─── Kapı 1b: formasyon teyit-bonusu yön kapısı ─────────────────────────────
#
# ÖLÇÜM (shadow_trade_tracker, sızıntısız ileriye dönük kâğıt-işlem, 60 gün):
#     formasyon SELL : 26/115 = %22.6   (iki-yönlü binom p ≈ 3e-9)
#     formasyon BUY  : 62/124 = %50.0   (p = 1.0 — edge yok ama zararsız)
# Sembol kırılımında SELL her sembolde kaybediyor (USOIL %19.5 n=41, GDAXI
# %20.8 n=24, XAU %24.2 n=33, NDX %29.4 n=17) → tek bir sembolün artefaktı
# değil, dedektörün ayı tarafı sistematik olarak yanlış.
# Ayrıca NDX'te BUY tarafı da kırık: 2/22 = %9.1 (p ≈ 1e-4).
#
# emel_pulse.py formasyon "teyidi" için skora +6 (klasik) / +10 (harmonik)
# ekliyor. Ölçülen isabete göre bu bonus ayı tarafında sinyali GÜÇLENDİRMEK
# yerine zayıflatmalı. Bu kapı yalnızca bonusu GERİ ÇEKER — asla yeni sinyal
# üretmez, yön çevirmez; en kötü ihtimalle sinyal eşiği geçemez (konservatif).

_PATTERN_BONUS_BLOCKED = {
    ("*", "SELL"),            # global: %22.6 (n=115)
    ("NDX.INDX", "BUY"),      # NDX boğa formasyonları da kırık: %9.1 (n=22)
}


def pattern_bonus_allowed(symbol: str, direction: Optional[str]) -> bool:
    """Formasyon teyit bonusu bu sembol+yön için verilebilir mi?

    Args:
        symbol: Enstrüman (normalize edilir).
        direction: "BUY" | "SELL" (None → bonus yok sayılmaz, serbest).

    Returns:
        False ise çağıran taraf ``pattern_pts``'i eklememelidir.
        ``PATTERN_BONUS_GATE_ENABLED=0`` ile tamamen kapatılır.
    """
    if not _flag("PATTERN_BONUS_GATE_ENABLED", "1"):
        return True
    d = (direction or "").upper()
    if not d:
        return True
    sym = _norm_symbol(symbol)
    return not (("*", d) in _PATTERN_BONUS_BLOCKED
                or (sym, d) in _PATTERN_BONUS_BLOCKED)


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
    """8 koşullu giriş skoru — skor < ENTRY_SCORE_MIN ise blok (default GÖLGE).

    ⚠️ 2026-08-11 — VARSAYILAN GÖLGEYE ALINDI (ENTRY_SCORE_GATE_BLOCK=0).
    Kapıyı gerekçelendiren 2026-07-09 otopsisi (NDX skor≥7 WR %60→%65, USOIL
    %49→%72) SIZINTISIZ ölçümde yeniden üretilemedi. Ölçüm:
    backend/research/backend_entry_gate_validation.py — 20.732 panel sinyali
    (2026-05-01→07-14, kapı canlıya girmeden önceki sansürsüz pencere), skor
    karar anında KAPANMIŞ MT5 M5/M30 barlarından, sonuç M1 yarışıyla
    (status kullanılmadı), nötr geometri TP=SL=1×ATR(5m):
        tümü    n=20.732  WR %53.8  ort.R +0.076   (toplam +1.580R)
        geçen   n= 7.648  WR %54.1  ort.R +0.082
        elenen  n=13.084  WR %53.6  ort.R +0.073   ← pratikte AYNI
    Gün-bloklu bootstrap: P(elenen > geçen) = %44 → fark şanstan ayırt edilemiyor.
    Kapı sinyallerin %63'ünü eliyor ve toplam R'yi +1.580R'den +626R'ye düşürüyor;
    eşiklerin hiçbiri (5/6/7/8) kapısız hâli geçemiyor. Aynı mantık bot tarafında
    da (45 gün gerçek işlem) aleyhte çıktı → orada da gölgede.
    Kapı ÖLÇMEYE devam eder (log satırları karne için); bloklamak isteyen
    ENTRY_SCORE_GATE_BLOCK=1 yapar. Veri alınamazsa fail-open.
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
            if not _flag("ENTRY_SCORE_GATE_BLOCK", "0"):
                logger.info(
                    f"entry_score_gate SHADOW {symbol} {direction}: {score}/8 < {min_score} "
                    f"(ihlal: {', '.join(fails)}) — ölçülüyor, BLOKLANMIYOR"
                )
                return True, None
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


# ─── Kapı 6: Sahte kırılım (fakeout) kapısı ─────────────────────────────────

#: Fakeout dedektörleri 4 sembolde OOS %70/%70+ doğrulandı (2026-07-17):
#: NDX %70/%83 · GDAXI %75/%89 · XAU %72/%93 (tp0.75) · USOIL %86/%81 (kantil eşik).
#: Kural dosyası olmayan sembolde kapı no-op'tur (fail-open).
FAKEOUT_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}


async def fakeout_gate(
    symbol: str,
    direction: str,
) -> Tuple[bool, Optional[str]]:
    """Taze bir seviye kırılımı sinyal yönündeyse ve OOS-doğrulanmış kurallara
    göre yüksek olasılıkla SAHTE ise sinyali blokla.

    Kanıt: backend/data/fakeout_report.md (fakeout_miner.py, NDX 5m, kronolojik
    %70/30 OOS). Örn. pen_atr≥0.865 & body_ratio≥0.78 → sahte %89 (train n=91) /
    %87.8 (test n=41); vol_ratio≥1.274 & body_ratio≥0.78 → %85.7 OOS.

    GÖLGE MODU (default): FAKEOUT_GATE_BLOCK=0 iken yalnızca INFO loglar,
    bloklamaz — canlı sinyal-bazlı doğrulama toplandıktan sonra açılmalı.
    Kurallar sembole özgü JSON'dan gelir; başka sembolde kural yoksa no-op.
    Fail-open: servis/veri hatası asla sinyal bloklamaz.
    """
    if not _flag("FAKEOUT_GATE_ENABLED"):
        return True, None

    try:
        from services.fakeout_service import assess_symbol
        result = await assess_symbol(symbol)
        if result.get("status") != "assessed":
            return True, None
        bo = result.get("breakout") or {}
        aligned = (direction == "BUY" and bo.get("direction") == "up") or \
                  (direction == "SELL" and bo.get("direction") == "down")
        if not aligned:
            return True, None

        try:
            block_prob = float(os.getenv("FAKEOUT_BLOCK_PROB", "80"))
        except ValueError:
            block_prob = 80.0
        prob = float(result.get("fake_probability") or 0)
        matched = result.get("matched_rules") or []
        score = result.get("breakout_score")
        det_call = (result.get("detector") or {}).get("call")
        # Kanıt şartı: +1-bar dedektör SAHTE çağrısı (OOS %70) VEYA eşleşen kural
        # VEYA skor-kalibrasyonlu klimaks hücresi (OOS %87 sahte)
        evidence = det_call == "fake" or bool(matched) or \
            (isinstance(score, (int, float)) and score <= -2)

        if (det_call == "fake" and prob >= 60.0) or (prob >= block_prob and evidence):
            why = ("dedektör SAHTE çağrısı (OOS %70)" if det_call == "fake"
                   else f"kural: {matched[0].get('rule')}" if matched
                   else f"birleşik skor {score} (klimaks hücresi)")
            reason = (
                f"Fakeout kapısı: {bo.get('level_kind')} {bo.get('level_price')} "
                f"kırılımı sinyal yönünde ama sahte olasılığı %{prob:.0f} ({why})"
            )
            if _flag("FAKEOUT_GATE_BLOCK", "0"):
                logger.info(f"fakeout_gate BLOCK {symbol} {direction}: {reason}")
                return False, reason
            logger.info(f"fakeout_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
        else:
            logger.debug(
                f"fakeout_gate PASS {symbol} {direction}: prob=%{prob:.0f} "
                f"verdict={result.get('verdict')}"
            )
    except Exception as exc:  # fail-open
        logger.debug(f"fakeout_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Kapı 8-10: Bot-taşıması kapılar (2026-07-28 Pulse NDX denetimi) ─────────
#
# Kaynak: backend/data/evolution/analyst_reports/pulse_ndx_denetimi_2026-07-28.md
# Denetim: 60g NDX'te pulse BUY %32-41 WR (yukarı günlerde bile %33.7 — giriş
# zamanlaması yapısal olarak kötü). MT5 botu ("yeni deneme/") aynı pulse
# oylarını bu üç YEREL filtreden geçirerek kullanıyor ve üçü de canlı işlem
# verisiyle ölçülü. Panele GÖLGE modda taşındı: default yalnız loglar,
# *_BLOCK=1 ile gerçek blok. Hepsi fail-open.

# ─── Zaman-kalitesi katmanı (2026-08-01 gün/saat denetimi) ───────────────────
#
# Fikir: kötü pencereleri tamamen kapatmak yerine "yalnız çok emin sinyal"
# çıtası koy (kullanıcı kararı). Altın pencerede davranış DEĞİŞMEZ (zaten tam
# çalışıyor) — yalnız factors.time_quality etiketiyle ileriki analize işaretlenir.

TQ_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}

_TQ_GOLDEN_HOURS = {"NDX.INDX": {13, 14}}        # ABD açılışı — %58 (n=683)
_TQ_SESSION_EXCEPTION_HOURS = {"NDX.INDX": {18}}  # hard-bloklu saat, yüksek güvene açılır


def _tq_cool_hours(symbol: str) -> set:
    if _norm_symbol(symbol) != "NDX.INDX":
        return set()
    raw = os.getenv("TQ_NDX_COOL_HOURS", "16,17,19")
    try:
        return {int(h) for h in raw.split(",") if h.strip()}
    except ValueError:
        return {16, 17, 19}


def _tq_cool_dows(symbol: str) -> set:
    if _norm_symbol(symbol) != "USOIL.FOREX":
        return set()
    raw = os.getenv("TQ_USOIL_COOL_DOWS", "4")
    try:
        return {int(d) for d in raw.split(",") if d.strip()}
    except ValueError:
        return {4}


def _tq_conf_min() -> float:
    try:
        return float(os.getenv("TQ_COOL_MIN_CONF", "80"))
    except ValueError:
        return 80.0


def _tq_norm_conf(confidence: Optional[float]) -> Optional[float]:
    """Güveni 0-100 ölçeğine getir (bazı üreticiler 0-1 kesir geçer)."""
    if confidence is None:
        return None
    try:
        c = float(confidence)
    except (TypeError, ValueError):
        return None
    return c * 100.0 if 0.0 < c <= 1.0 else c


def time_quality_tier(symbol: str, when: Optional[datetime] = None) -> Tuple[str, Optional[str]]:
    """('golden'|'cool'|'normal', sebep). Yalnız UTC saat/gün — veri çekmez."""
    now = when or datetime.now(timezone.utc)
    sym = _norm_symbol(symbol)
    if now.hour in _TQ_GOLDEN_HOURS.get(sym, set()):
        return "golden", f"altın pencere {now.hour:02d} UTC (NDX ABD açılışı %58, n=683)"
    if now.hour in _tq_cool_hours(symbol):
        return "cool", f"çukur saat {now.hour:02d} UTC (NDX %44-45 kanıtı)"
    if now.isoweekday() in _tq_cool_dows(symbol):
        return "cool", "çukur günü Perşembe (USOIL %35, n=941)"
    return "normal", None


def time_quality_gate(
    symbol: str, direction: str, confidence: Optional[float],
) -> Tuple[bool, Optional[str]]:
    """Çukur penceresinde güven < eşik sinyali frenle (TQ_GATE_BLOCK=0 → gölge).

    Fail-open: güven bilinmiyorsa (None) bloklamaz — yalnız loglar.
    """
    if not _flag("TQ_GATE_ENABLED"):
        return True, None
    tier, why = time_quality_tier(symbol)
    if tier != "cool":
        return True, None
    conf = _tq_norm_conf(confidence)
    if conf is None:
        logger.info(f"time_quality_gate {symbol} {direction}: {why} ama güven "
                    "bilinmiyor — fail-open geçti")
        return True, None
    if conf >= _tq_conf_min():
        return True, None      # "çok emin" sinyal — çukurda da açılır
    reason = (f"Zaman-kalitesi kapısı: {why}; güven {conf:.0f} < eşik "
              f"{_tq_conf_min():.0f} — çukurda yalnız çok-emin sinyal")
    if _flag("TQ_GATE_BLOCK", "1"):
        logger.info(f"time_quality_gate BLOCK {symbol} {direction}: {reason}")
        return False, reason
    logger.info(f"time_quality_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
    return True, None


def tq_session_exception(symbol: str, confidence: Optional[float]) -> bool:
    """NDX 18 UTC seans bloğu altın-istisnası: güven ≥ eşik ise saat açılır.

    Kullanıcı kararı (2026-08-01): 18-20 penceresi 'çok emin' işlemlere aktif —
    panel kanıtı 18 UTC'de zayıf (%44) olduğundan tam açmak yerine yüksek-güven
    şartıyla açılır. TQ_SESSION_EXCEPTION=0 ile eski tam-blok davranışı.
    """
    if not _flag("TQ_SESSION_EXCEPTION"):
        return False
    now = datetime.now(timezone.utc)
    if now.hour not in _TQ_SESSION_EXCEPTION_HOURS.get(_norm_symbol(symbol), set()):
        return False
    conf = _tq_norm_conf(confidence)
    return conf is not None and conf >= _tq_conf_min()


# ─── Kapı: XAU scalp kapısı (2026-08-01 AI işlem envanteri denetimi) ─────────
#
# Kanıt (30g prediction_logs): XAUUSD'de pulse1 %18.2 (n=965), pulse2 %16.3
# (n=995), pulse3 %18.2 (n=853), smc %25.2 (n=131) — hepsi statik 15-pip SL
# epoch'unda ölçüldü. Kök neden geometri (XAU BUY "patient WR", dar stop −EV);
# aynı gün geometri atr_ladder_v1 + 1.5×ATR tabanına taşındı. Bu kapı default
# GÖLGE: yeni epoch ölçülmeden bloklamaz; epoch da kurtarmazsa
# XAU_SCALP_GATE_BLOCK=1 ile XAU pulse/smc üretimi tamamen durdurulur.

XAU_SCALP_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}


def xau_scalp_gate(symbol: str, direction: str) -> Tuple[bool, Optional[str]]:
    """XAUUSD scalp-modeli sinyal kapısı (default GÖLGE — sadece loglar)."""
    if not _flag("XAU_SCALP_GATE_ENABLED"):
        return True, None
    if not _is_xau(symbol) or direction not in ("BUY", "SELL"):
        return True, None
    reason = ("XAU scalp kapısı: 30g WR pulse %16-18 / smc %25 (statik-SL "
              "epoch) — XAU'da 5m scalp edge'i yok, geometri epoch'u izleniyor")
    if _flag("XAU_SCALP_GATE_BLOCK", "0"):
        logger.info(f"xau_scalp_gate BLOCK {symbol} {direction}: {reason}")
        return False, reason
    logger.info(f"xau_scalp_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
    return True, None


_BOT_PORT_GATE_SYMBOLS = {"NDX.INDX"}

#: Bot-taşıması kapılar yalnız pulse ailesine uygulanır (SMC'nin kendi NDX
#: SELL kapısı var; EMEL/ML kendi eşiklerini yönetir).
BOT_PORT_GATED_MODELS = {"pulse1", "pulse2", "pulse3"}


async def trend_align_gate(symbol: str, direction: str) -> Tuple[bool, Optional[str]]:
    """1h EMA50 trend-hiza kapısı (botun _trend_gate'inin panel karşılığı).

    Kanıt (bot, 30g/332 gerçek MT5 işlemi): 1h EMA50 ile hizalı girişler
    WR %63.3 / +9.710$, karşıt girişler %43.4 / −13.161$. Pulse'ın NDX BUY
    kanaması tam bu karşıt-trend desenindeydi (denetim §KN-3).
    Default GÖLGE: TREND_ALIGN_GATE_BLOCK=1 olana dek sadece loglar.
    """
    if not _flag("TREND_ALIGN_GATE_ENABLED"):
        return True, None
    if _norm_symbol(symbol) not in _BOT_PORT_GATE_SYMBOLS:
        return True, None

    try:
        from services.market_data_service import get_ohlcv_data
        candles = await get_ohlcv_data(symbol, timeframe="1h", limit=60)
        if not candles or len(candles) < 55:
            return True, None
        closes = [c.get("close") for c in candles]
        ema50 = _ema(closes, 50)
        last_close = float(closes[-1]) if closes[-1] is not None else None
        if ema50 is None or last_close is None:
            return True, None
        sgn = 1.0 if direction == "BUY" else -1.0
        if sgn * (last_close - ema50) <= 0:
            reason = (
                f"Trend-hiza kapısı: 1h close {last_close:.1f}, EMA50 {ema50:.1f} "
                f"— {direction} counter-trend (bot kanıtı: karşıt WR %43.4)"
            )
            if _flag("TREND_ALIGN_GATE_BLOCK", "0"):
                logger.info(f"trend_align_gate BLOCK {symbol} {direction}: {reason}")
                return False, reason
            logger.info(f"trend_align_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
    except Exception as exc:  # fail-open
        logger.debug(f"trend_align_gate fail-open ({symbol}): {exc}")

    return True, None


async def wave_position_gate(symbol: str, direction: str) -> Tuple[bool, Optional[str]]:
    """4h dalga pozisyon kapısı (botun _position_gate'inin panel karşılığı).

    Son 48×5m barın hi-lo aralığında fiyatın konumu: tepe bölgede (>%60)
    BUY, dip bölgede (<%40) SELL frenlenir — "tepeden alma / dipten satma"
    deseni. Bot kanıtı: NDX VIXREG SELL dip-üçlükte %53.4 WR / −3.738$ vs
    tepe-üçlükte %65.8 / +2.860$. Pulse kaybedenlerinin medyan MFE'si +2-5
    puan (girişte yanlış) — bu kapının hedeflediği desen.
    Default GÖLGE: WAVE_POSITION_GATE_BLOCK=1 olana dek sadece loglar.
    """
    if not _flag("WAVE_POSITION_GATE_ENABLED"):
        return True, None
    if _norm_symbol(symbol) not in _BOT_PORT_GATE_SYMBOLS:
        return True, None

    try:
        buy_max = float(os.getenv("WAVE_POS_BUY_MAX", "0.60"))
        sell_min = float(os.getenv("WAVE_POS_SELL_MIN", "0.40"))
    except ValueError:
        buy_max, sell_min = 0.60, 0.40

    try:
        from services.market_data_service import get_ohlcv_data
        candles = await get_ohlcv_data(symbol, timeframe="5m", limit=48)
        if not candles or len(candles) < 36:
            return True, None
        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]
        last_close = float(candles[-1]["close"])
        hi, lo = max(highs), min(lows)
        if hi <= lo:
            return True, None
        pos = (last_close - lo) / (hi - lo)
        blocked = (direction == "BUY" and pos > buy_max) or \
                  (direction == "SELL" and pos < sell_min)
        if blocked:
            reason = (
                f"Dalga pozisyon kapısı: fiyat 4h dalgasının %{pos*100:.0f} "
                f"konumunda — {'tepe bölgede BUY' if direction == 'BUY' else 'dip bölgede SELL'} "
                "frenli (bot kanıtı: dip-üçlük SELL %53.4 vs tepe %65.8)"
            )
            if _flag("WAVE_POSITION_GATE_BLOCK", "0"):
                logger.info(f"wave_position_gate BLOCK {symbol} {direction}: {reason}")
                return False, reason
            logger.info(f"wave_position_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
    except Exception as exc:  # fail-open
        logger.debug(f"wave_position_gate fail-open ({symbol}): {exc}")

    return True, None


async def vix_regime_gate(symbol: str, direction: str) -> Tuple[bool, Optional[str]]:
    """VIX rejim yön kapısı (botun VIXREG yön kuralının freni olarak).

    Kanıt: VIX rejimi NDX yönünü öngörüyor (+25pp, plasebo p=0.000, OOS +17;
    bot: lehte yön WR %70 vs karşıt %45). Kural: VIX ≥ eşik → lehte yön BUY,
    altı → SELL. Karşıt yöndeki pulse sinyali frenlenir (lehte yöne bonus
    verilmez — o iş Precision Veto katmanının).
    Default BLOK (2026-08-01): 30g gölge-eşdeğeri ölçüm (NDX pulse1-3, n=1098,
    factors.macro_vix_price ile) lehte %58.0 vs karşıt %42.5 (+15.5pp) — bot
    kanıtı (+25pp) ve OOS (+17pp) ile tutarlı. VIX_REGIME_GATE_BLOCK=0 → gölge.
    """
    if not _flag("VIX_REGIME_GATE_ENABLED"):
        return True, None
    if _norm_symbol(symbol) not in _BOT_PORT_GATE_SYMBOLS:
        return True, None

    try:
        threshold = float(os.getenv("VIX_REGIME_GATE_THRESHOLD", "18.4"))
    except ValueError:
        threshold = 18.4

    try:
        from services.macro_data_service import get_macro_dict
        vix_raw = ((get_macro_dict() or {}).get("vix") or {}).get("price")
        if vix_raw is None:
            return True, None
        vix = float(vix_raw)
        favored = "BUY" if vix >= threshold else "SELL"
        if direction != favored:
            reason = (
                f"VIX rejim kapısı: VIX {vix:.1f} ({'≥' if vix >= threshold else '<'} "
                f"{threshold}) → lehte yön {favored}, sinyal {direction} karşıt "
                "(kanıt: lehte %70 vs karşıt %45 WR)"
            )
            if _flag("VIX_REGIME_GATE_BLOCK", "1"):
                logger.info(f"vix_regime_gate BLOCK {symbol} {direction}: {reason}")
                return False, reason
            logger.info(f"vix_regime_gate GÖLGE {symbol} {direction}: {reason} — bloklanMADI")
    except Exception as exc:  # fail-open
        logger.debug(f"vix_regime_gate fail-open ({symbol}): {exc}")

    return True, None


# ─── Kapı: Tartışma-bias kapısı (agent debate → intraday karşıt-sinyal freni) ─
#
# Kanıt (backend/data/agent_debate_analysis_report.md, 2026-07-18, n=18 yönlü —
# ERKEN KANIT, bu yüzden default GÖLGE):
#   - Tartışma kararı GÜN-KAPANIŞI değil İNTRADAY (≤240dk) bias'tır: NDX bearish
#     gün 0/4 ama +60dk 4/6, +240dk 4/5 (ort +0.24..0.29%); boğa-drift kapanışa
#     doğru çağrıyı ters çeviriyor → NDX'te 14:00 ET sonrası etki YOK.
#   - debate_winner=bear → +60dk %77; winner=balanced → 30-60dk 0/3 → etkisiz.
#   - Placebo: USOIL "başarısı" büyük ölçüde dönem trendi; NDX bearish baseline'ı
#     +0.14pp geçiyor. XAU 6/6 bearish kilitlenmesi negatif, DAX 5/5 nötr →
#     XAU/DAX tüketilmez.
#   - LLM confidence TERS kalibre (med 60-75 en kötü) → kararda KULLANILMAZ.
#   - invalid_if seviyeleri XAU/USOIL'de sık deliniyor ama kimse tüketmiyordu →
#     seviye delinmişse bias geçersiz sayılır (etkisiz).

DEBATE_GATED_MODELS = {"pulse1", "pulse2", "pulse3", "smc"}
DEBATE_BIAS_SYMBOLS = {"NDX.INDX", "USOIL.FOREX"}
_NDX_LATE_CUTOFF_ET = 14 * 60          # 14:00 ET sonrası NDX bias etkisiz


async def debate_bias_gate(
    symbol: str,
    direction: str,
) -> Tuple[bool, Optional[str]]:
    """Taze tartışma bias'ına KARŞIT sinyali frenle (default GÖLGE: sadece log).

    Yalnız karşıt yönü frenler; hizalı sinyale bonus vermez (o iş Precision
    Veto'nun MiroShark katmanında). Fail-open: veri/DB hatası asla bloklamaz.
    """
    if not _flag("DEBATE_BIAS_GATE_ENABLED"):
        return True, None
    sym = _norm_symbol(symbol)
    if sym not in DEBATE_BIAS_SYMBOLS:
        return True, None

    try:
        from services.bias_test_service import latest_bias_for_symbol
        row = latest_bias_for_symbol(sym)
        if not row or row.get("bias") not in ("bullish", "bearish"):
            return True, None

        try:
            valid_min = float(os.getenv("DEBATE_BIAS_VALID_MIN", "240"))
        except ValueError:
            valid_min = 240.0
        if row["age_min"] > valid_min:
            return True, None
        if (row.get("debate_winner") or "") == "balanced":
            return True, None          # balanced-kazanan koşular 30-60dk 0/3

        if sym == "NDX.INDX":
            from zoneinfo import ZoneInfo
            ny = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
            if ny.hour * 60 + ny.minute >= _NDX_LATE_CUTOFF_ET:
                return True, None      # kapanış drift'i intraday çağrıyı bozar

        opposed = (direction == "BUY" and row["bias"] == "bearish") or \
                  (direction == "SELL" and row["bias"] == "bullish")
        if not opposed:
            logger.debug(f"debate_bias_gate hizalı {sym} {direction} "
                         f"({row['bias']}, {row['age_min']:.0f}dk)")
            return True, None

        # Bias'ın kendi geçersizlik seviyesi delindiyse artık frenleme.
        try:
            from services.data_fetcher import fetch_latest_price
            price = await fetch_latest_price(sym)
            sup, res = row.get("main_support"), row.get("main_resistance")
            if price and row["bias"] == "bullish" and sup and price < float(sup):
                return True, None
            if price and row["bias"] == "bearish" and res and price > float(res):
                return True, None
        except Exception:
            pass   # fiyat okunamazsa seviye kontrolünü atla, frene devam

        reason = (
            f"Tartışma-bias kapısı: {row['run_label']} kararı {row['bias']} "
            f"({row['age_min']:.0f}dk önce, winner={row.get('debate_winner')}) — "
            f"{direction} karşıt yönde"
        )
        if _flag("DEBATE_BIAS_GATE_BLOCK", "0"):
            logger.info(f"debate_bias_gate BLOCK {sym} {direction}: {reason}")
            return False, reason
        logger.info(f"debate_bias_gate GÖLGE {sym} {direction}: {reason} — bloklanMADI")
    except Exception as exc:  # fail-open
        logger.debug(f"debate_bias_gate fail-open ({symbol}): {exc}")

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
    confidence: Optional[float] = None,
) -> Tuple[str, List[str]]:
    """Tüm kapıları sırasıyla uygula; bloklanırsa yönü HOLD'a düşür.

    Panel endpoint'leri (UI tutarlılığı) ve prediction_logger (güvenlik ağı)
    tarafından ortak kullanılır — idempotenttir.

    Args:
        symbol: Panel sembolü (örn. "XAUUSD", "GDAXI.INDX").
        direction: "BUY" | "SELL" | diğer (dokunulmaz).
        model_type: "pulse1" | "pulse2" | "pulse3" | "smc" | "emel" | "ml:*" ...
        regime: Varsa RegimeResult (tekrar tespit maliyetini önler).
        confidence: Sinyal güveni (0-100 veya 0-1; zaman-kalitesi kapısı ve NDX
            18 UTC altın-istisnası kullanır; None → o kontroller fail-open).

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

    # 2a) XAU scalp kapısı (2026-08-01; default GÖLGE — sadece loglar)
    if base in XAU_SCALP_GATED_MODELS:
        allowed, reason = xau_scalp_gate(symbol, direction)
        if not allowed:
            notes.append(reason or "XAU scalp kapısı")
            return "HOLD", notes

    # 2b) NDX SMC counter-trend SELL kapısı (2026-07-15 denetimi: 1W/28L)
    allowed, reason = await ndx_smc_sell_gate(symbol, direction, model_type)
    if not allowed:
        notes.append(reason or "NDX SMC SELL kapısı")
        return "HOLD", notes

    # 3) Seans kapısı (+ NDX 18 UTC altın-istisnası: güven ≥ TQ eşiği ise geç)
    if base in SESSION_GATED_MODELS:
        allowed, reason = session_gate(symbol)
        if not allowed:
            if tq_session_exception(symbol, confidence):
                notes.append("NDX 18 UTC altın-istisna: yüksek güvenli sinyal "
                             "seans bloğunu aştı (TQ_SESSION_EXCEPTION)")
            else:
                notes.append(reason or "Seans kapısı")
                return "HOLD", notes

    # 3b) Zaman-kalitesi kapısı (çukur pencerede yalnız çok-emin sinyal)
    if base in TQ_GATED_MODELS:
        allowed, reason = time_quality_gate(symbol, direction, confidence)
        if not allowed:
            notes.append(reason or "Zaman-kalitesi kapısı")
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

    # 5b) Bot-taşıması kapılar (2026-07-28 denetimi; default GÖLGE — sadece log)
    if base in BOT_PORT_GATED_MODELS:
        for _bot_gate in (trend_align_gate, wave_position_gate, vix_regime_gate):
            allowed, reason = await _bot_gate(symbol, direction)
            if not allowed:
                notes.append(reason or "Bot-taşıması kapı")
                return "HOLD", notes

    # 6) Sahte kırılım kapısı (60s cache'li; default GÖLGE modda — sadece loglar)
    if base in FAKEOUT_GATED_MODELS:
        allowed, reason = await fakeout_gate(symbol, direction)
        if not allowed:
            notes.append(reason or "Fakeout kapısı")
            return "HOLD", notes

    # 7) Tartışma-bias kapısı (60s cache'li DB okuma; default GÖLGE — sadece log)
    if base in DEBATE_GATED_MODELS:
        allowed, reason = await debate_bias_gate(symbol, direction)
        if not allowed:
            notes.append(reason or "Tartışma-bias kapısı")
            return "HOLD", notes

    return direction, notes
