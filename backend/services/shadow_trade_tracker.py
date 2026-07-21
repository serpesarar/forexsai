"""Shadow Trade Tracker — formasyon + fakeout tespitlerinin SIZINTISIZ
ileriye dönük paper-trade doğrulaması.

Üç kaynak izlenir:
  1. ``pattern``  — harmonic_pattern_service tespitleri (confidence >= %60,
     status=COMPLETED, TAZE: son pivot son N bar içinde kapanmış).
  2. ``fakeout``  — fakeout_service dedektör çağrıları (call=fake/genuine,
     stage=confirm_bar|wave_k2; ``resolved_observed`` HARİÇ — o gözlemdir,
     tahmin değildir → hindsight sızıntısı olurdu).
  3. ``meta``     — 6-model ensemble/core sinyali (meta_analysis_engine).
     Core'un CANLI çıktısı olduğu gibi test edilir (XAUUSD dahil 4 sembol);
     TP/SL = core'un kendi risk hesabı (SL=ATR×1.5, TP1=ATR×1.0). Aynı
     sembol+yönde yalnız 1 açık meta işlem tutulur (dedup); sinyal sürerken
     her turda yeni işlem AÇILMAZ.

Sızıntı (leak) garantileri:
  * Giriş fiyatı = karar anındaki SON KAPANMIŞ 5m barın kapanışı; koşan bar
    asla kullanılmaz (bar_close <= now şartı).
  * Çözümleme yalnız entry_time'dan SONRA AÇILAN 5m barların high/low'u ile
    yapılır; giriş barı dahil edilmez.
  * Aynı 5m barda TP ve SL birlikte vurulursa KONSERVATİF: LOSS + ambiguous.
  * Geç tespit koruması: fiyat zaten TP'yi geçmişse işlem AÇILMAZ (geometri
    sanity), tamamlanmış-ama-bayat formasyonlar tazelik penceresiyle elenir.
  * Piyasa kapalıyken (son 5m bar > 30dk eski) yeni işlem açılmaz.

Persistans: Supabase ``shadow_pattern_trades`` (RLS kilitli, service-role ile
yazılır). DB yoksa in-memory'ye düşer (fail-open) ve raporda belirtilir.
prediction_logs / signal_lifecycle akışına DOKUNMAZ.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

SYMBOLS: List[str] = [
    s.strip() for s in os.getenv(
        "SHADOW_TRACKER_SYMBOLS", "NDX.INDX,GDAXI.INDX,XAUUSD,USOIL.FOREX"
    ).split(",") if s.strip()
]
MIN_CONFIDENCE = float(os.getenv("SHADOW_TRACKER_MIN_CONF", "60"))
INTERVAL_SECONDS = int(os.getenv("SHADOW_TRACKER_INTERVAL_SECONDS", "120"))

# Meta/core kaynağı: core'un kendi min_confidence kapısı (40) olduğu gibi
# korunur — amaç core'u OLDUĞU GİBİ ölçmek, üstüne filtre koymak değil.
# Rapor güven-kovaları (<60/60-70/70-80/80+) kaliteyi zaten ayrıştırır.
META_SHADOW_ENABLED = os.getenv("META_SHADOW_ENABLED", "1") == "1"
META_MIN_CONF = float(os.getenv("META_SHADOW_MIN_CONF", "40"))
META_EXPIRY_HOURS = float(os.getenv("META_SHADOW_EXPIRY_HOURS", "24"))

PATTERN_TIMEFRAMES = ["4h", "1h"]
PATTERN_FRESH_BARS = 4                    # son pivot en fazla N bar önce kapanmış olmalı
                                          # (fraktal pivot +2 bar teyit ister → efektif pencere ~2 bar)
PATTERN_EXPIRY_HOURS = {"4h": 120.0, "1h": 48.0}
FAKEOUT_EXPIRY_HOURS = 8.0
STALE_MARKET_MINUTES = 30                 # son 5m bar bundan eskiyse piyasa kapalı say
FIVE_MIN_MS = 300_000
TF_SECONDS = {"5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400}

TABLE = "shadow_pattern_trades"

# ─── Durum ───────────────────────────────────────────────────────────────────

_memory_trades: List[Dict[str, Any]] = []      # DB yokken fail-open depo
_last_cycle: Dict[str, Any] = {"time": None, "opened": 0, "resolved": 0, "errors": []}
_db_degraded = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _parse_ts(value: Any) -> Optional[datetime]:
    """ISO string veya epoch(s/ms) → aware UTC datetime."""
    if value is None:
        return None
    try:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            num = float(value)
            if num > 10_000_000_000:
                num /= 1000.0
            return datetime.fromtimestamp(num, tz=timezone.utc)
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _db():
    """Supabase client veya None (fail-open)."""
    global _db_degraded
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            _db_degraded = True
            return None
        client = get_supabase_client()
        _db_degraded = client is None
        return client
    except Exception as exc:
        logger.warning("[shadow-tracker] DB erişilemedi (fail-open): %s", exc)
        _db_degraded = True
        return None


# ─── Mum yardımcıları (sızıntı korumalı) ─────────────────────────────────────

def _closed_bars(candles: List[dict], tf_ms: int = FIVE_MIN_MS,
                 now: Optional[datetime] = None) -> List[dict]:
    """Yalnız KAPANMIŞ barlar: bar_open + tf <= now. Koşan bar elenir."""
    now = now or _utcnow()
    now_ms = now.timestamp() * 1000
    out = []
    for c in candles or []:
        ts = c.get("timestamp", c.get("time"))
        if ts is None:
            continue
        ts = float(ts)
        if ts < 10_000_000_000:      # epoch saniye geldiyse ms'e çevir
            ts *= 1000
        if ts + tf_ms <= now_ms:
            out.append({**c, "_ts_ms": ts})
    return out


def _atr14(bars: List[dict]) -> Optional[float]:
    if len(bars) < 15:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l = float(bars[i]["high"]), float(bars[i]["low"])
        pc = float(bars[i - 1]["close"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    tail = trs[-14:]
    return sum(tail) / len(tail) if tail else None


def _market_is_fresh(bars: List[dict], now: datetime) -> bool:
    if not bars:
        return False
    last_close_ms = bars[-1]["_ts_ms"] + FIVE_MIN_MS
    age_min = (now.timestamp() * 1000 - last_close_ms) / 60000.0
    return age_min <= STALE_MARKET_MINUTES


# ─── İşlem açma ──────────────────────────────────────────────────────────────

def _geometry_ok(direction: str, entry: float, tp: float, sl: float) -> bool:
    """Geç tespit / bozuk geometri koruması. Risk mesafesi > 0 şart."""
    if direction == "BUY":
        return sl < entry < tp
    return tp < entry < sl


def _build_trade(source: str, symbol: str, timeframe: str, pattern_type: str,
                 pattern_name: str, direction: str, confidence: float,
                 anchor_time: datetime, entry_time: datetime, entry: float,
                 tp: float, sl: float, expiry_hours: float,
                 details: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": source,
        "symbol": symbol,
        "timeframe": timeframe,
        "pattern_type": pattern_type,
        "pattern_name": pattern_name,
        "direction": direction,
        "confidence": round(float(confidence), 1),
        "anchor_time": _iso(anchor_time),
        "entry_time": _iso(entry_time),
        "entry_price": round(float(entry), 4),
        "tp_price": round(float(tp), 4),
        "sl_price": round(float(sl), 4),
        "expiry_time": _iso(entry_time + timedelta(hours=expiry_hours)),
        "status": "open",
        "details": details,
    }


def _persist_trade(trade: Dict[str, Any]) -> bool:
    """Insert (unique anchor dedup). True = yeni kayıt açıldı."""
    client = _db()
    if client is None:
        key = (trade["source"], trade["symbol"], trade["pattern_type"],
               trade["direction"], trade["anchor_time"])
        if any((t["source"], t["symbol"], t["pattern_type"], t["direction"],
                t["anchor_time"]) == key for t in _memory_trades):
            return False
        trade["id"] = f"mem_{len(_memory_trades) + 1}"
        _memory_trades.append(trade)
        return True
    res = client.table(TABLE).insert_ignore(trade)
    if res.get("error"):
        err_text = str(res["error"])
        # DB şeması 'meta' kaynağını henüz tanımıyorsa (CHECK kısıtı eski) veri
        # kaybetme: belleğe düş. Migration uygulanınca bu yol kendiliğinden ölür.
        if trade["source"] == "meta" and ("check" in err_text.lower()
                                          or "23514" in err_text):
            key = (trade["source"], trade["symbol"], trade["pattern_type"],
                   trade["direction"], trade["anchor_time"])
            if any((t["source"], t["symbol"], t["pattern_type"], t["direction"],
                    t["anchor_time"]) == key for t in _memory_trades):
                return False
            trade["id"] = f"mem_{len(_memory_trades) + 1}"
            _memory_trades.append(trade)
            logger.warning("[shadow-tracker] meta insert DB CHECK kısıtına takıldı "
                           "— belleğe alındı (migration bekliyor): %s", err_text)
            return True
        logger.warning("[shadow-tracker] insert hatası: %s", res["error"])
        return False
    return not res.get("duplicate", False)


async def _entry_snapshot(symbol: str, now: datetime) -> Optional[Tuple[List[dict], float, datetime]]:
    """(kapanmış 5m barlar, giriş fiyatı, giriş zamanı) — piyasa bayatsa None."""
    from services.data_fetcher import fetch_ohlc_data
    candles = await fetch_ohlc_data(symbol, timeframe="5m", limit=500)
    bars = _closed_bars(candles, FIVE_MIN_MS, now)
    if len(bars) < 20 or not _market_is_fresh(bars, now):
        return None
    last = bars[-1]
    entry_price = float(last["close"])
    entry_time = datetime.fromtimestamp((last["_ts_ms"] + FIVE_MIN_MS) / 1000.0,
                                        tz=timezone.utc)
    return bars, entry_price, entry_time


async def scan_patterns(now: Optional[datetime] = None) -> int:
    """%60+ güvenli TAZE tamamlanmış formasyonlar → sanal işlem."""
    from services.harmonic_pattern_service import detect_chart_patterns
    now = now or _utcnow()
    opened = 0
    for symbol in SYMBOLS:
        snap = await _entry_snapshot(symbol, now)
        if snap is None:
            continue
        _, entry_price, entry_time = snap
        for tf in PATTERN_TIMEFRAMES:
            try:
                result = await detect_chart_patterns(symbol, timeframe=tf, limit=260)
            except Exception as exc:
                logger.warning("[shadow-tracker] pattern tespiti hata %s %s: %s", symbol, tf, exc)
                continue
            tf_sec = TF_SECONDS.get(tf, 14400)
            for p in result.get("patterns", []):
                conf = float(p.get("confidence", 0))
                if conf < MIN_CONFIDENCE or p.get("status") != "COMPLETED":
                    continue
                tp = p.get("target_price")
                sl = p.get("stop_loss") or p.get("invalidation_price")
                if tp is None or sl is None:
                    continue
                points = p.get("points", {})
                pivot_times = [_parse_ts(v.get("time")) for v in points.values()]
                pivot_times = [t for t in pivot_times if t]
                if not pivot_times:
                    continue
                # Tazelik: son pivot (bar açılışı) + 1 bar = pivotun kapanışı;
                # şimdiden en fazla FRESH_BARS bar geride olmalı. Bayat
                # tamamlanmış formasyonla işlem açmak hindsight olurdu.
                anchor = max(pivot_times)
                age_sec = (now - anchor).total_seconds() - tf_sec
                if age_sec < 0 or age_sec > PATTERN_FRESH_BARS * tf_sec:
                    continue
                direction = "BUY" if p.get("direction") == "BULLISH" else "SELL"
                if not _geometry_ok(direction, entry_price, float(tp), float(sl)):
                    continue
                trade = _build_trade(
                    source="pattern", symbol=symbol, timeframe=tf,
                    pattern_type=str(p.get("type", "UNKNOWN")),
                    pattern_name=str(p.get("name_tr") or p.get("name") or ""),
                    direction=direction, confidence=conf,
                    anchor_time=anchor, entry_time=entry_time,
                    entry=entry_price, tp=float(tp), sl=float(sl),
                    expiry_hours=PATTERN_EXPIRY_HOURS.get(tf, 72.0),
                    details={
                        "category": p.get("category"),
                        "fib_ratios": p.get("fib_ratios"),
                        "invalidation_price": p.get("invalidation_price"),
                        "points": {k: v.get("price") for k, v in points.items()},
                    },
                )
                if _persist_trade(trade):
                    opened += 1
                    logger.info("[shadow-tracker] pattern işlem: %s %s %s %s conf=%s",
                                symbol, tf, trade["pattern_type"], direction, conf)
    return opened


async def scan_fakeouts(now: Optional[datetime] = None) -> int:
    """Fakeout dedektör çağrıları (fake/genuine, %60+ güven) → sanal işlem."""
    from services.fakeout_service import assess_bars, load_rules
    now = now or _utcnow()
    opened = 0
    for symbol in SYMBOLS:
        snap = await _entry_snapshot(symbol, now)
        if snap is None:
            continue
        bars, entry_price, entry_time = snap
        try:
            assessment = assess_bars(bars, symbol=symbol)
        except Exception as exc:
            logger.warning("[shadow-tracker] fakeout assess hata %s: %s", symbol, exc)
            continue
        if assessment.get("status") != "assessed":
            continue
        det = assessment.get("detector") or {}
        call = det.get("call")
        stage = det.get("stage")
        # KRİTİK sızıntı koruması: resolved_observed = yarışın SONUCU gözlenmiş
        # demektir; o bir tahmin değildir, işlem açılmaz.
        if call not in ("fake", "genuine") or stage not in ("confirm_bar", "wave_k2"):
            continue
        p_fake = det.get("p_fake")
        if p_fake is None:
            continue
        conf = float(p_fake) if call == "fake" else 100.0 - float(p_fake)
        if conf < MIN_CONFIDENCE:
            continue
        bo = assessment.get("breakout") or {}
        bo_dir_up = bo.get("direction") == "up"
        # fake → kırılımın TERSİ (fade); genuine → kırılım yönü
        if call == "genuine":
            direction = "BUY" if bo_dir_up else "SELL"
        else:
            direction = "SELL" if bo_dir_up else "BUY"
        atr = _atr14(bars)
        if not atr or atr <= 0:
            continue
        det_cfg = (load_rules(symbol) or {}).get("detector") or {}
        tp_mult = float(det_cfg.get("tp_atr", 1.0))
        sl_mult = float(det_cfg.get("sl_atr", 1.0))
        if direction == "BUY":
            tp, sl = entry_price + tp_mult * atr, entry_price - sl_mult * atr
        else:
            tp, sl = entry_price - tp_mult * atr, entry_price + sl_mult * atr
        # anchor = kırılım barının zamanı (dedup: aynı kırılım bir kez işlenir)
        offset = int(bo.get("bar_offset_from_end", 0))
        anchor_idx = max(0, len(bars) - 1 - offset)
        anchor = datetime.fromtimestamp(bars[anchor_idx]["_ts_ms"] / 1000.0,
                                        tz=timezone.utc)
        trade = _build_trade(
            source="fakeout", symbol=symbol, timeframe="5m",
            pattern_type=f"{call}_call",
            pattern_name=("AI Dedektör: SAHTE (fade)" if call == "fake"
                          else "AI Dedektör: GERÇEK (kırılım yönü)"),
            direction=direction, confidence=conf,
            anchor_time=anchor, entry_time=entry_time,
            entry=entry_price, tp=tp, sl=sl,
            expiry_hours=FAKEOUT_EXPIRY_HOURS,
            details={
                "stage": stage, "p_fake": p_fake,
                "breakout_direction": bo.get("direction"),
                "level_kind": bo.get("level_kind"),
                "level_price": bo.get("level_price"),
                "breakout_score": assessment.get("breakout_score"),
                "recommendation": assessment.get("recommendation"),
                "atr": round(atr, 4), "tp_atr": tp_mult, "sl_atr": sl_mult,
            },
        )
        if _persist_trade(trade):
            opened += 1
            logger.info("[shadow-tracker] fakeout işlem: %s %s %s conf=%.1f",
                        symbol, trade["pattern_type"], direction, conf)
    return opened


def _open_meta_keys() -> Optional[set]:
    """Açık meta işlemlerin (symbol, direction) kümesi.

    None = sorgu başarısız → bu turda meta işlem AÇMA (dup spam koruması,
    fail-closed). In-memory modda her zaman küme döner.
    """
    client = _db()
    if client is None:
        return {(t["symbol"], t["direction"]) for t in _memory_trades
                if t.get("status") == "open" and t.get("source") == "meta"}
    res = (client.table(TABLE).select("symbol,direction")
           .eq("status", "open").eq("source", "meta").limit(200).execute())
    if res.get("error"):
        logger.warning("[shadow-tracker] açık meta sorgusu hata: %s", res["error"])
        return None
    keys = {(r["symbol"], r["direction"]) for r in (res.get("data") or [])}
    # CHECK-kısıtı fallback'iyle belleğe düşmüş açık meta işlemler de sayılır
    keys |= {(t["symbol"], t["direction"]) for t in _memory_trades
             if t.get("status") == "open" and t.get("source") == "meta"}
    return keys


async def scan_meta(now: Optional[datetime] = None) -> int:
    """Core/meta ensemble sinyalini (XAUUSD dahil 4 sembol) sanal işleme çevir.

    Sızıntı garantileri diğer kaynaklarla aynı: giriş = son KAPANMIŞ 5m bar
    kapanışı; TP/SL = core'un KENDİ risk hesabı (üzerine oynanmaz); çözüm
    yalnız girişten sonraki barlarla. Core HOLD derse işlem yok — çekimserlik
    de olduğu gibi kaydedilmez (işlem yoksa istatistiğe girmez).
    """
    if not META_SHADOW_ENABLED:
        return 0
    from services.meta_analysis_engine import get_meta_signal
    now = now or _utcnow()
    opened = 0
    open_keys = _open_meta_keys()
    if open_keys is None:
        return 0
    for symbol in SYMBOLS:
        snap = await _entry_snapshot(symbol, now)
        if snap is None:
            continue                       # piyasa kapalı/bayat → açma
        _, entry_price, entry_time = snap
        try:
            sig = await get_meta_signal(symbol)
        except Exception as exc:
            logger.warning("[shadow-tracker] meta sinyal hata %s: %s", symbol, exc)
            continue
        if sig is None:
            continue
        direction = str(sig.direction or "HOLD").upper()
        if direction not in ("BUY", "SELL"):
            continue
        conf = float(sig.confidence or 0)
        if conf < META_MIN_CONF:
            continue
        if (symbol, direction) in open_keys:
            continue                       # aynı yönde açık meta işlem var
        tp = float(sig.take_profit_1 or 0)
        sl = float(sig.stop_loss or 0)
        if tp <= 0 or sl <= 0:
            continue
        # Geometri sanity: core'un TP/SL'i bizim sızıntısız girişimizle hâlâ
        # tutarlı mı? (core kendi anlık fiyatından hesaplar; kayma olabilir)
        if not _geometry_ok(direction, entry_price, tp, sl):
            continue
        trade = _build_trade(
            source="meta", symbol=symbol, timeframe="live",
            pattern_type=str(sig.strength or "UNKNOWN"),
            pattern_name=f"Core Ensemble: {sig.source_combo or '?'}",
            direction=direction, confidence=conf,
            anchor_time=entry_time,        # bar-bazlı dedup (unique anchor)
            entry_time=entry_time,
            entry=entry_price, tp=tp, sl=sl,
            expiry_hours=META_EXPIRY_HOURS,
            details={
                "regime": sig.regime,
                "agreement_ratio": sig.agreement_ratio,
                "technical_score": sig.technical_score,
                "source_combo": sig.source_combo,
                "raw_confidence": sig.raw_confidence,
                "take_profit_2": sig.take_profit_2,
                "risk_reward": sig.risk_reward,
                "core_entry_price": sig.entry_price,   # audit: core'un kendi girişi
            },
        )
        if _persist_trade(trade):
            opened += 1
            open_keys.add((symbol, direction))
            logger.info("[shadow-tracker] meta işlem: %s %s conf=%.1f (%s)",
                        symbol, direction, conf, sig.source_combo)
    return opened


# ─── Çözümleme (yalnız girişten SONRAKİ barlarla) ────────────────────────────

def _resolve_against_bars(trade: Dict[str, Any], bars: List[dict],
                          now: datetime) -> Optional[Dict[str, Any]]:
    """Açık işlemi girişten SONRAKİ kapanmış barlarla değerlendir.

    Dönen dict = update alanları; None = hâlâ açık.
    """
    entry_time = _parse_ts(trade["entry_time"])
    expiry_time = _parse_ts(trade["expiry_time"])
    entry = float(trade["entry_price"])
    tp = float(trade["tp_price"])
    sl = float(trade["sl_price"])
    direction = trade["direction"]
    risk = abs(entry - sl)
    if risk <= 0 or entry_time is None:
        return {"status": "invalid", "exit_time": _iso(now)}

    entry_ms = entry_time.timestamp() * 1000
    # Giriş barı DAHİL DEĞİL: yalnız açılışı giriş zamanından sonra olan barlar.
    future = [b for b in bars if b["_ts_ms"] >= entry_ms]
    last_close = None
    for b in future:
        h, l = float(b["high"]), float(b["low"])
        last_close = float(b["close"])
        bar_close = datetime.fromtimestamp((b["_ts_ms"] + FIVE_MIN_MS) / 1000.0,
                                           tz=timezone.utc)
        if direction == "BUY":
            hit_tp, hit_sl = h >= tp, l <= sl
        else:
            hit_tp, hit_sl = l <= tp, h >= sl
        if hit_tp and hit_sl:
            # Aynı barda iki taraf — sıra bilinmiyor → KONSERVATİF: kayıp say.
            return {"status": "loss", "ambiguous": True, "exit_price": sl,
                    "exit_time": _iso(bar_close), "r_multiple": -1.0}
        if hit_sl:
            return {"status": "loss", "exit_price": sl,
                    "exit_time": _iso(bar_close), "r_multiple": -1.0}
        if hit_tp:
            r = abs(tp - entry) / risk
            return {"status": "win", "exit_price": tp,
                    "exit_time": _iso(bar_close), "r_multiple": round(r, 3)}
    if expiry_time and now >= expiry_time:
        if last_close is None:
            return {"status": "expired", "exit_time": _iso(now)}
        signed = (last_close - entry) if direction == "BUY" else (entry - last_close)
        return {"status": "expired", "exit_price": last_close,
                "exit_time": _iso(now), "r_multiple": round(signed / risk, 3)}
    return None


async def resolve_open_trades(now: Optional[datetime] = None) -> int:
    """Tüm açık sanal işlemleri ileriye dönük 5m barlarla çözer."""
    from services.data_fetcher import fetch_ohlc_data
    now = now or _utcnow()
    client = _db()
    if client is None:
        open_trades = [t for t in _memory_trades if t.get("status") == "open"]
    else:
        res = client.table(TABLE).select("*").eq("status", "open").limit(500).execute()
        if res.get("error"):
            logger.warning("[shadow-tracker] açık işlem sorgusu hata: %s", res["error"])
            return 0
        open_trades = res.get("data") or []
        # bellek fallback'indeki açık işlemler de çözülür (id: mem_*)
        open_trades += [t for t in _memory_trades if t.get("status") == "open"]
    if not open_trades:
        return 0

    bars_by_symbol: Dict[str, List[dict]] = {}
    resolved = 0
    for trade in open_trades:
        symbol = trade["symbol"]
        if symbol not in bars_by_symbol:
            candles = await fetch_ohlc_data(symbol, timeframe="5m", limit=2000)
            bars_by_symbol[symbol] = _closed_bars(candles, FIVE_MIN_MS, now)
        update = _resolve_against_bars(trade, bars_by_symbol[symbol], now)
        if not update:
            continue
        update["updated_at"] = _iso(now)
        if client is None or str(trade.get("id", "")).startswith("mem_"):
            trade.update(update)
            resolved += 1
        else:
            res = client.table(TABLE).eq("id", trade["id"]).update(update)
            if res.get("error"):
                logger.warning("[shadow-tracker] update hata id=%s: %s",
                               trade.get("id"), res["error"])
            else:
                resolved += 1
        logger.info("[shadow-tracker] çözüldü: #%s %s %s → %s (R=%s)",
                    trade.get("id"), symbol, trade.get("pattern_type"),
                    update["status"], update.get("r_multiple"))
    return resolved


# ─── Rapor ───────────────────────────────────────────────────────────────────

def _bucket(conf: float) -> str:
    if conf >= 80:
        return "80+"
    if conf >= 70:
        return "70-80"
    if conf >= 60:
        return "60-70"
    return "<60"       # meta kaynağı core'un kendi 40 kapısıyla açılabilir


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    resolved = [r for r in rows if r.get("status") in ("win", "loss")]
    wins = sum(1 for r in resolved if r["status"] == "win")
    rs = [float(r["r_multiple"]) for r in rows
          if r.get("r_multiple") is not None and r.get("status") in ("win", "loss", "expired")]
    return {
        "total": len(rows),
        "open": sum(1 for r in rows if r.get("status") == "open"),
        "wins": wins,
        "losses": len(resolved) - wins,
        "expired": sum(1 for r in rows if r.get("status") == "expired"),
        "win_rate": round(100.0 * wins / len(resolved), 1) if resolved else None,
        "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
        "sample_warning": len(resolved) < 10,
    }


async def build_report(days: int = 30, symbol: Optional[str] = None) -> Dict[str, Any]:
    """Kaynak/sembol/formasyon/güven-kovası kırılımlı isabet raporu."""
    client = _db()
    since = _iso(_utcnow() - timedelta(days=days))
    if client is None:
        rows = [t for t in _memory_trades if t.get("entry_time", "") >= since]
    else:
        q = client.table(TABLE).select("*").gte("created_at", since)
        if symbol:
            q = q.eq("symbol", symbol)
        res = q.order("created_at", desc=True).limit(2000).execute()
        rows = (res.get("data") or []) if not res.get("error") else []
        # bellek fallback'i (meta CHECK kısıtı) rapora dahil
        rows += [t for t in _memory_trades if t.get("entry_time", "") >= since]
    if symbol:
        rows = [r for r in rows if r.get("symbol") == symbol]

    def group(key_fn) -> Dict[str, Any]:
        out: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            out.setdefault(key_fn(r), []).append(r)
        return {k: _aggregate(v) for k, v in sorted(out.items())}

    recent = [{
        "id": r.get("id"), "source": r.get("source"), "symbol": r.get("symbol"),
        "timeframe": r.get("timeframe"), "pattern": r.get("pattern_name") or r.get("pattern_type"),
        "direction": r.get("direction"), "confidence": r.get("confidence"),
        "status": r.get("status"), "r_multiple": r.get("r_multiple"),
        "entry_time": r.get("entry_time"), "entry_price": r.get("entry_price"),
        "tp_price": r.get("tp_price"), "sl_price": r.get("sl_price"),
        "ambiguous": r.get("ambiguous", False),
    } for r in rows[:25]]

    return {
        "success": True,
        "days": days,
        "symbol": symbol,
        "db_degraded": _db_degraded,
        "min_confidence": MIN_CONFIDENCE,
        "overall": _aggregate(rows),
        "by_source": group(lambda r: r.get("source", "?")),
        "by_symbol": group(lambda r: r.get("symbol", "?")),
        "by_pattern": group(lambda r: f"{r.get('source')}:{r.get('pattern_type')}"),
        "by_confidence": group(lambda r: _bucket(float(r.get("confidence", 0)))),
        "recent": recent,
        "note": ("Sızıntısız ileriye dönük ölçüm: giriş = karar anındaki son kapanmış "
                 "5m bar kapanışı; çözüm yalnız SONRAKİ barlarla. Aynı barda TP+SL → "
                 "konservatif LOSS. n<10 kova istatistiği güvenilmez."),
    }


# ─── Döngü ───────────────────────────────────────────────────────────────────

async def run_cycle() -> Dict[str, Any]:
    """Tek tarama + çözümleme turu (router run-once da bunu çağırır)."""
    now = _utcnow()
    errors: List[str] = []
    opened = resolved = 0
    try:
        opened += await scan_patterns(now)
    except Exception as exc:
        errors.append(f"scan_patterns: {exc}")
        logger.exception("[shadow-tracker] scan_patterns hata")
    try:
        opened += await scan_fakeouts(now)
    except Exception as exc:
        errors.append(f"scan_fakeouts: {exc}")
        logger.exception("[shadow-tracker] scan_fakeouts hata")
    try:
        opened += await scan_meta(now)
    except Exception as exc:
        errors.append(f"scan_meta: {exc}")
        logger.exception("[shadow-tracker] scan_meta hata")
    try:
        resolved = await resolve_open_trades(now)
    except Exception as exc:
        errors.append(f"resolve: {exc}")
        logger.exception("[shadow-tracker] resolve hata")
    _last_cycle.update({"time": _iso(now), "opened": opened,
                        "resolved": resolved, "errors": errors})
    return dict(_last_cycle)


def get_status() -> Dict[str, Any]:
    return {
        "enabled": os.getenv("SHADOW_TRACKER_ENABLED", "1") == "1",
        "symbols": SYMBOLS,
        "min_confidence": MIN_CONFIDENCE,
        "interval_seconds": INTERVAL_SECONDS,
        "pattern_timeframes": PATTERN_TIMEFRAMES,
        "meta_shadow_enabled": META_SHADOW_ENABLED,
        "meta_min_confidence": META_MIN_CONF,
        "meta_expiry_hours": META_EXPIRY_HOURS,
        "db_degraded": _db_degraded,
        "memory_trades": len(_memory_trades),
        "last_cycle": _last_cycle,
    }


async def tracker_loop() -> None:
    """main.py lifespan'dan başlatılan sonsuz döngü (fail-open)."""
    logger.info("[shadow-tracker] döngü başladı (interval=%ss, min_conf=%s)",
                INTERVAL_SECONDS, MIN_CONFIDENCE)
    await asyncio.sleep(20)          # DataHub'ın ısınmasını bekle
    while True:
        try:
            await run_cycle()
        except Exception as exc:      # asla ölme
            logger.exception("[shadow-tracker] döngü hatası: %s", exc)
        await asyncio.sleep(INTERVAL_SECONDS)
