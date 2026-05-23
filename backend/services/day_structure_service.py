"""
Day Structure Analyzer — günün yapısal seviyelerini hesaplar.

Hesaplananlar:
  • Day H/L (bugün UTC 00:00'dan itibaren) + dünün H/L/C (PDH/PDL/PDC)
  • PWH/PWL (önceki hafta)
  • Floor Trader Pivot Noktaları (PP/R1-3/S1-3)
  • Multi-scale swing high/low (küçük + büyük ölçek)
  • Memory zones: ATR×0.25 toleransla swing+pivot kümeleme, dokunma sayısı,
    her dokunmanın REJECTION (geri çekilme) mu BREAK (kırılım) mu olduğu,
    son dokunmaya göre eksponansiyel freshness puanı
  • ATR + günün volatilite oranı (today_ATR / N-day avg ATR)

Precision Veto Engine'in Stage 1c'si BU servisi çağırır. Aynı veriler Stage 4
ML meta-classifier'ın feature seti için de hazır — DayStructure dataclass
tek seferde her şeyi dolduruyor.

Caching: per (symbol, signal_tf, current_minute) 60sn TTL. Aynı dakikada
ikinci kez çağrılırsa yeniden hesaplama yok.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Konfigürasyon ───────────────────────────────────────────────────────────
SWING_ORDER_SMALL = 3        # mikro swing (1-3 saatlik salınım)
SWING_ORDER_LARGE = 8        # günün ana yapısal swing'leri
SWING_LOOKBACK_BARS = 200    # swing taraması için son N mum
MEMORY_LOOKBACK_BARS = 300   # memory zone clustering penceresi
MEMORY_ZONE_ATR_MULT = 0.25  # bir zone'un yarı genişliği = ATR × bu
MEMORY_FRESHNESS_HALFLIFE_MIN = 240   # freshness için 4 saat yarı ömür
REJECTION_LOOKAHEAD_BARS = 3          # dokunma sonrası kaç bar bakılır
REJECTION_RETRACE_ATR = 0.5           # geri çekilme ATR×bu kadarsa = REJECT
ATR_PERIOD = 14
PIVOT_LOOKBACK_DAYS_FOR_AVG_ATR = 7

_cache: dict[tuple, tuple[float, "DayStructure"]] = {}
_CACHE_TTL = 60.0


# ─── Veri yapısı ─────────────────────────────────────────────────────────────
@dataclass
class MemoryZone:
    center: float
    lower: float
    upper: float
    touches: int                  # toplam dokunma
    rejections: int               # bu dokunmaların kaçı reject oldu
    breaks: int                   # kaçı break oldu
    last_touch_minutes_ago: float
    freshness: float              # 0..1 (eksponansiyel decay)
    strength: str                 # "weak" | "moderate" | "strong"

    @property
    def is_strong_rejection_zone(self) -> bool:
        """HV1 için kapı: ≥4 reddetme + freshness ≥0.6 (≈ son 2 saat içinde test)."""
        return self.rejections >= 4 and self.freshness >= 0.6


@dataclass
class DayStructure:
    symbol: str
    timeframe: str
    computed_at: datetime
    current_price: float
    atr: float
    today_atr_ratio: float        # today_ATR / N-day avg ATR (1.0 = normal)
    # Referans seviyeleri
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    pdh: Optional[float] = None
    pdl: Optional[float] = None
    pdc: Optional[float] = None
    pwh: Optional[float] = None
    pwl: Optional[float] = None
    # Floor Trader Pivots (dünün H/L/C'sinden)
    pivots: dict[str, float] = field(default_factory=dict)
    # Multi-scale swing noktaları (timestamp, price)
    swings_small_highs: list[tuple[datetime, float]] = field(default_factory=list)
    swings_small_lows: list[tuple[datetime, float]] = field(default_factory=list)
    swings_large_highs: list[tuple[datetime, float]] = field(default_factory=list)
    swings_large_lows: list[tuple[datetime, float]] = field(default_factory=list)
    # Memory zones (en güçlüden zayıfa sıralı)
    memory_zones: list[MemoryZone] = field(default_factory=list)
    # PDH/PDL'nin BUGÜN nasıl test edildiği (HV2 için)
    pdh_touches_today: int = 0
    pdh_rejections_today: int = 0
    pdl_touches_today: int = 0
    pdl_rejections_today: int = 0
    notes: list[str] = field(default_factory=list)

    def distance_atr(self, level: Optional[float]) -> Optional[float]:
        """Mevcut fiyatın bir seviyeye ATR cinsinden uzaklığı (mutlak)."""
        if level is None or self.atr <= 0:
            return None
        return abs(self.current_price - level) / self.atr

    def nearest_memory_zone_in_direction(self, direction: str
                                          ) -> Optional[MemoryZone]:
        """Sinyal yönünde (BUY=yukarı, SELL=aşağı) mevcut fiyata en yakın zone."""
        if not self.memory_zones:
            return None
        if direction == "BUY":
            # Yukarıdaki en yakın zone (price'tan yüksek)
            above = [z for z in self.memory_zones if z.center > self.current_price]
            return min(above, key=lambda z: z.center - self.current_price) if above else None
        # SELL: aşağıdaki en yakın
        below = [z for z in self.memory_zones if z.center < self.current_price]
        return max(below, key=lambda z: z.center) if below else None


# ─── Mum yardımcıları (precision_veto_service'ten farklı erişim için yerel) ─
def _v(c: dict, *keys: str) -> float:
    for k in keys:
        if k in c and c[k] is not None:
            try:
                return float(c[k])
            except (TypeError, ValueError):
                pass
    return 0.0

def _o(c): return _v(c, "open", "o")
def _h(c): return _v(c, "high", "h")
def _l(c): return _v(c, "low", "l")
def _cl(c): return _v(c, "close", "c")
def _t(c):
    ts = c.get("timestamp") or c.get("ts") or c.get("time")
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if isinstance(ts, (int, float)):
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


# ─── ATR ─────────────────────────────────────────────────────────────────────
def _atr(candles: list[dict], period: int = ATR_PERIOD) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs = []
    for i in range(1, len(candles)):
        c, p = candles[i], candles[i - 1]
        tr = max(_h(c) - _l(c), abs(_h(c) - _cl(p)), abs(_l(c) - _cl(p)))
        trs.append(tr)
    window = trs[-period:]
    return sum(window) / len(window) if window else 0.0


# ─── Multi-scale swing tespiti (saf-Python, scipy yok) ───────────────────────
def _find_swings(candles: list[dict], order: int) -> tuple[list, list]:
    """Yerel ekstremum: pencere içindeki bar diğer 2×order komşusundan daha
    yüksek/düşükse swing. Yeterli komşusu olmayan kenar bar'lar atlanır."""
    highs, lows = [], []
    n = len(candles)
    for i in range(order, n - order):
        h_i, l_i = _h(candles[i]), _l(candles[i])
        is_swing_high = all(h_i > _h(candles[j])
                             for j in range(i - order, i + order + 1) if j != i)
        is_swing_low = all(l_i < _l(candles[j])
                            for j in range(i - order, i + order + 1) if j != i)
        ts = _t(candles[i])
        if is_swing_high and ts is not None:
            highs.append((ts, h_i))
        if is_swing_low and ts is not None:
            lows.append((ts, l_i))
    return highs, lows


# ─── Pivot Noktaları (Floor Trader) ──────────────────────────────────────────
def _floor_pivots(prev_h: float, prev_l: float, prev_c: float) -> dict[str, float]:
    if not (prev_h > 0 and prev_l > 0 and prev_c > 0):
        return {}
    pp = (prev_h + prev_l + prev_c) / 3.0
    rng = prev_h - prev_l
    return {
        "PP": pp,
        "R1": (2 * pp) - prev_l,
        "R2": pp + rng,
        "R3": prev_h + 2 * (pp - prev_l),
        "S1": (2 * pp) - prev_h,
        "S2": pp - rng,
        "S3": prev_l - 2 * (prev_h - pp),
    }


# ─── Memory Zone clustering + freshness + rejection/break ────────────────────
def _classify_touch(candles: list[dict], touch_idx: int,
                     level: float, atr: float) -> str:
    """Bir dokunma sonrası 3 bar bakılır. Fiyat geri çekildiyse REJECT,
    seviyeyi geçip orada kaldıysa BREAK, kararsızsa NEUTRAL."""
    end = min(len(candles), touch_idx + REJECTION_LOOKAHEAD_BARS + 1)
    if end - touch_idx < 2:
        return "neutral"
    retrace_thr = atr * REJECTION_RETRACE_ATR
    look = candles[touch_idx + 1:end]
    if not look:
        return "neutral"
    # En yakın geri çekilme + en uzak break
    closes = [_cl(c) for c in look]
    above = max((c - level for c in closes), default=0)
    below = max((level - c for c in closes), default=0)
    if above > retrace_thr and below < retrace_thr:
        return "break_up"
    if below > retrace_thr and above < retrace_thr:
        return "break_down"
    # Yön ne olursa olsun seviyeden uzaklaşma var mı?
    last_close = closes[-1]
    if abs(last_close - level) > retrace_thr:
        return "break"
    return "rejection"


def _build_memory_zones(candles: list[dict],
                        seed_levels: list[float],
                        atr: float,
                        now_utc: datetime) -> list[MemoryZone]:
    """seed_levels: swing high/low + pivot + PDH/PDL noktaları. Her bar için
    fiyat aralığı bir seed'in toleransına giriyorsa o seed'in 'dokunma' kovasına
    bir kayıt düşülür. Sonra yakın seed'ler clusterlanır."""
    if not seed_levels or atr <= 0 or not candles:
        return []
    zone_half = atr * MEMORY_ZONE_ATR_MULT
    # Her seed için dokunmaları topla
    touches_per_seed: list[list[tuple[int, str]]] = [[] for _ in seed_levels]
    for i, c in enumerate(candles):
        hi, lo = _h(c), _l(c)
        for j, level in enumerate(seed_levels):
            if lo <= level + zone_half and hi >= level - zone_half:
                cls = _classify_touch(candles, i, level, atr)
                touches_per_seed[j].append((i, cls))

    # Yakın seed'leri (≤ ATR×0.25) birleştir
    indexed = sorted(enumerate(seed_levels), key=lambda x: x[1])
    used = set()
    clusters: list[list[int]] = []
    for idx, (orig_idx, level) in enumerate(indexed):
        if orig_idx in used:
            continue
        cluster = [orig_idx]
        used.add(orig_idx)
        for jdx in range(idx + 1, len(indexed)):
            o2, l2 = indexed[jdx]
            if o2 in used:
                continue
            if abs(l2 - indexed[idx][1]) <= zone_half:
                cluster.append(o2)
                used.add(o2)
            else:
                break
        clusters.append(cluster)

    zones: list[MemoryZone] = []
    half_life_sec = MEMORY_FRESHNESS_HALFLIFE_MIN * 60
    for cluster in clusters:
        center = sum(seed_levels[i] for i in cluster) / len(cluster)
        all_touches = []
        for i in cluster:
            all_touches.extend(touches_per_seed[i])
        if not all_touches:
            continue
        rejections = sum(1 for _, cls in all_touches if cls == "rejection")
        breaks = sum(1 for _, cls in all_touches if cls.startswith("break"))
        last_bar_idx = max(idx for idx, _ in all_touches)
        last_ts = _t(candles[last_bar_idx])
        if last_ts is None:
            minutes_ago = 9999.0
            freshness = 0.0
        else:
            minutes_ago = max(0.0, (now_utc - last_ts).total_seconds() / 60.0)
            # Eksponansiyel decay: half_life'ta 0.5
            freshness = 0.5 ** (minutes_ago / MEMORY_FRESHNESS_HALFLIFE_MIN)
        touches = len(all_touches)
        if touches >= 4 and rejections >= 3:
            strength = "strong"
        elif touches >= 2:
            strength = "moderate"
        else:
            strength = "weak"
        zones.append(MemoryZone(
            center=round(center, 5),
            lower=round(center - zone_half, 5),
            upper=round(center + zone_half, 5),
            touches=touches, rejections=rejections, breaks=breaks,
            last_touch_minutes_ago=round(minutes_ago, 1),
            freshness=round(freshness, 3),
            strength=strength,
        ))
    # En güçlüden zayıfa: önce reject sayısı, sonra freshness
    zones.sort(key=lambda z: (-z.rejections, -z.freshness))
    return zones


# ─── Bugünün PDH/PDL test sayımı (HV2 için kritik) ───────────────────────────
def _count_today_tests(candles_intraday: list[dict], level: float, atr: float,
                       today_start_utc: datetime) -> tuple[int, int]:
    """Bugün'ün barları içinde `level`'a kaç kez dokunuldu ve kaçı reject?"""
    if not candles_intraday or atr <= 0:
        return 0, 0
    tolerance = atr * 0.15
    touches = 0
    rejections = 0
    last_touch_bar = -10  # ardışık aynı bar'larda saymamak için
    for i, c in enumerate(candles_intraday):
        ts = _t(c)
        if ts is None or ts < today_start_utc:
            continue
        if abs(_h(c) - level) <= tolerance or abs(_l(c) - level) <= tolerance \
                or (_l(c) <= level <= _h(c)):
            if i - last_touch_bar < 3:   # aynı dokunma içinde sayma
                continue
            last_touch_bar = i
            touches += 1
            cls = _classify_touch(candles_intraday, i, level, atr)
            if cls == "rejection":
                rejections += 1
    return touches, rejections


# ─── Ana giriş ───────────────────────────────────────────────────────────────
async def compute_day_structure(symbol: str, signal_tf: str = "15m"
                                 ) -> Optional[DayStructure]:
    """Bir sinyal için tam gün yapısı paketi. Cache: per (symbol, tf, dakika)."""
    now = datetime.now(timezone.utc)
    cache_key = (symbol, signal_tf, now.strftime("%Y%m%d%H%M"))
    cached = _cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL:
        return cached[1]

    try:
        from services.data_fetcher import fetch_ohlc_data
        # 1m or signal_tf for swing/memory, 1h for intraday tests, 1d for PDH/PDL/PWH/PWL
        candles_tf = await fetch_ohlc_data(symbol, signal_tf, limit=400)
        candles_1h = await fetch_ohlc_data(symbol, "1h", limit=200)
        candles_1d = await fetch_ohlc_data(symbol, "1d", limit=30)
    except Exception as e:
        logger.warning("[day-structure] mum verisi alınamadı %s: %s", symbol, e)
        return None

    if not candles_tf or len(candles_tf) < 30:
        return None

    atr = _atr(candles_tf, ATR_PERIOD)
    if atr <= 0:
        return None

    # today_atr_ratio = mevcut ATR / son N gün ATR ortalaması
    today_atr_ratio = 1.0
    if candles_1d and len(candles_1d) > PIVOT_LOOKBACK_DAYS_FOR_AVG_ATR:
        daily_ranges = [_h(c) - _l(c) for c in candles_1d[-PIVOT_LOOKBACK_DAYS_FOR_AVG_ATR:]]
        avg_daily_range = sum(daily_ranges) / len(daily_ranges)
        # ATR (15m bazlı) ile daily range farklı birim — sadece relatif bilgi
        # için bugünün gerçek H-L'sini kullan.
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        today_bars = [c for c in candles_tf if _t(c) and _t(c) >= today_start]
        if today_bars:
            today_range = max(_h(c) for c in today_bars) - min(_l(c) for c in today_bars)
            if avg_daily_range > 0:
                today_atr_ratio = round(today_range / avg_daily_range, 2)

    current_price = _cl(candles_tf[-1])

    ds = DayStructure(symbol=symbol, timeframe=signal_tf, computed_at=now,
                       current_price=current_price, atr=atr,
                       today_atr_ratio=today_atr_ratio)

    # Day H/L (UTC 00:00'dan itibaren)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    today_bars = [c for c in candles_tf if _t(c) and _t(c) >= today_start]
    if today_bars:
        ds.day_high = round(max(_h(c) for c in today_bars), 5)
        ds.day_low = round(min(_l(c) for c in today_bars), 5)

    # PDH/PDL/PDC (dünün barı)
    if candles_1d and len(candles_1d) >= 2:
        prev_day = candles_1d[-2]
        ds.pdh = round(_h(prev_day), 5)
        ds.pdl = round(_l(prev_day), 5)
        ds.pdc = round(_cl(prev_day), 5)
        ds.pivots = {k: round(v, 5) for k, v in
                     _floor_pivots(ds.pdh, ds.pdl, ds.pdc).items()}

    # PWH/PWL (önceki tam haftanın H/L'i — son 7+ gün)
    if candles_1d and len(candles_1d) >= 14:
        prev_week = candles_1d[-14:-7]
        if prev_week:
            ds.pwh = round(max(_h(c) for c in prev_week), 5)
            ds.pwl = round(min(_l(c) for c in prev_week), 5)

    # Multi-scale swings
    look = candles_tf[-SWING_LOOKBACK_BARS:]
    ds.swings_small_highs, ds.swings_small_lows = _find_swings(look, SWING_ORDER_SMALL)
    ds.swings_large_highs, ds.swings_large_lows = _find_swings(look, SWING_ORDER_LARGE)

    # Memory zones — seed: tüm swing + pivot + PDH/PDL/PWH/PWL noktaları
    seed_levels: list[float] = []
    seed_levels.extend(p for _, p in ds.swings_small_highs)
    seed_levels.extend(p for _, p in ds.swings_small_lows)
    seed_levels.extend(p for _, p in ds.swings_large_highs)
    seed_levels.extend(p for _, p in ds.swings_large_lows)
    seed_levels.extend(v for k, v in ds.pivots.items() if k != "PP")
    for lvl in (ds.pdh, ds.pdl, ds.pwh, ds.pwl):
        if lvl is not None:
            seed_levels.append(lvl)
    memory_lookback = candles_tf[-MEMORY_LOOKBACK_BARS:]
    ds.memory_zones = _build_memory_zones(memory_lookback, seed_levels, atr, now)

    # Bugünün PDH/PDL test sayımı (HV2 için)
    if ds.pdh is not None:
        t, r = _count_today_tests(candles_tf, ds.pdh, atr, today_start)
        ds.pdh_touches_today = t
        ds.pdh_rejections_today = r
    if ds.pdl is not None:
        t, r = _count_today_tests(candles_tf, ds.pdl, atr, today_start)
        ds.pdl_touches_today = t
        ds.pdl_rejections_today = r

    _cache[cache_key] = (time.time(), ds)
    # Eski cache temizliği — basit bir cap
    if len(_cache) > 256:
        oldest = sorted(_cache.items(), key=lambda kv: kv[1][0])[:128]
        for k, _ in oldest:
            _cache.pop(k, None)
    return ds
