"""Fiyat alarmları — day-trader-skill trader-alerts karşılığı (MIT, Copyright (c) 2026 Jake Schincariol).

Alarm türleri:
    above / below  : fiyat seviyenin üstüne / altına geçince.
    stop / target  : seviye, kurulum anı fiyatının (ref_price) KARŞI tarafına geçince (yönü ref belirler).
    pct_move       : |fiyat / ref_price − 1| ≥ pct %.
    time           : at_utc anı geldiğinde (fiyat gerekmez).

Döngü 60 sn'de bir aktif alarmları çeker; fiyat DataHub'dan, yalnız TAZE MT5 fiyatıyla değerlendirilir
(bayat fiyatla sahte tetik olmasın). Tetik atomiktir: ``UPDATE ... WHERE status='active'`` — iki backend
aynı anda koşsa da bir alarm bir kez tetiklenir. Bildirim Telegram (``telegram_notifier``), fail-open.
Tablo: ``price_alerts`` (supabase/migrations/20261104_price_alerts.sql). Bayrak: PRICE_ALERTS_ENABLED.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TABLE = "price_alerts"
LOOP_SECONDS = int(os.getenv("PRICE_ALERTS_INTERVAL_SECONDS", "60"))
REPEAT_COOLDOWN_MIN = 60          # tek-sefer olmayan alarmın iki tetik arası en kısa süre
MAX_ACTIVE_ALERTS = 200           # kötüye kullanım/hata tavanı
PRICE_KINDS = ("above", "below", "stop", "target", "pct_move")
KINDS = PRICE_KINDS + ("time",)
SOURCES = ("manual", "plan", "signal")

_last_run: Dict[str, Any] = {"at": None, "checked": 0, "triggered": 0, "error": None}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(v: Any) -> Optional[datetime]:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def canonical_symbol(symbol: str) -> str:
    """DataHub kanonik adı (NDX → NDX.INDX ...); DataHub yüklenemezse girdi büyük harfle."""
    try:
        from services import data_hub
        return data_hub._canonical_symbol(symbol)
    except Exception:
        return (symbol or "").strip().upper()


# ─── Saf çekirdek ────────────────────────────────────────────────────────────

def evaluate(alert: Dict[str, Any], price: Optional[float], now: datetime) -> bool:
    """Alarm şu an tetiklenmeli mi? Fiyat gerektiren türde fiyat yoksa False."""
    kind = alert.get("kind")
    if kind == "time":
        at = _parse_ts(alert.get("at_utc"))
        return at is not None and now >= at
    if price is None or price <= 0:
        return False
    level = alert.get("price")
    ref = alert.get("ref_price")
    if kind == "above":
        return level is not None and price >= float(level)
    if kind == "below":
        return level is not None and price <= float(level)
    if kind in ("stop", "target"):
        if level is None or ref is None:
            return False
        level, ref = float(level), float(ref)
        return price >= level if level > ref else price <= level
    if kind == "pct_move":
        pct = alert.get("pct")
        if not pct or not ref:
            return False
        return abs(price / float(ref) - 1.0) * 100.0 >= float(pct)
    return False


def validate(payload: Dict[str, Any], current_price: Optional[float] = None) -> Dict[str, Any]:
    """Girdiyi tabloya yazılacak satıra çevirir; hatada ValueError."""
    kind = payload.get("kind")
    if kind not in KINDS:
        raise ValueError(f"kind şunlardan biri olmalı: {', '.join(KINDS)}")
    symbol = canonical_symbol(str(payload.get("symbol") or ""))
    if not symbol:
        raise ValueError("symbol gerekli")
    source = payload.get("source") or "manual"
    if source not in SOURCES:
        raise ValueError(f"source şunlardan biri olmalı: {', '.join(SOURCES)}")
    row: Dict[str, Any] = {
        "symbol": symbol, "kind": kind, "source": source,
        "label": (str(payload.get("label"))[:200] if payload.get("label") else None),
        "one_shot": bool(payload.get("one_shot", True)),
        "notify_telegram": bool(payload.get("notify_telegram", True)),
    }
    ref = payload.get("ref_price") or current_price
    if kind in ("above", "below", "stop", "target"):
        price = payload.get("price")
        if price is None or float(price) <= 0:
            raise ValueError("price gerekli (pozitif)")
        row["price"] = float(price)
        if kind in ("stop", "target"):
            if not ref:
                raise ValueError("stop/target için ref_price (ya da canlı fiyat) gerekli")
            if float(ref) == float(price):
                raise ValueError("seviye kurulum fiyatına eşit olamaz")
            row["ref_price"] = float(ref)
    elif kind == "pct_move":
        pct = payload.get("pct")
        if pct is None or float(pct) <= 0:
            raise ValueError("pct gerekli (pozitif)")
        if not ref:
            raise ValueError("pct_move için ref_price (ya da canlı fiyat) gerekli")
        row["pct"], row["ref_price"] = float(pct), float(ref)
    else:
        at = _parse_ts(payload.get("at_utc"))
        if at is None:
            raise ValueError("at_utc gerekli (ISO-8601)")
        row["at_utc"] = at.isoformat()
        if payload.get("ref_price"):
            row["ref_price"] = float(payload["ref_price"])
    return row


def plan_alerts(symbol: str, side: str, entry: float, stop: float, target: float,
                horizon_min: Optional[int] = None, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Zaman Makinesi planından stop + hedef (+ ufuk sonu zaman) alarmları — repo `add --from-plan`."""
    if side not in ("buy", "sell"):
        raise ValueError("side buy|sell olmalı")
    long = side == "buy"
    if (long and not (stop < entry < target)) or (not long and not (target < entry < stop)):
        raise ValueError("plan geometrisi tutarsız (buy: stop < giriş < hedef; sell: tersi)")
    tag = f"{'AL' if long else 'SAT'} plan @{entry:g}"
    base = {"symbol": symbol, "source": "plan", "ref_price": entry}
    out = [validate({**base, "kind": "stop", "price": stop, "label": f"{tag} — STOP"}),
           validate({**base, "kind": "target", "price": target, "label": f"{tag} — HEDEF"})]
    if horizon_min:
        at = (now or _utcnow()) + timedelta(minutes=int(horizon_min))
        out.append(validate({**base, "kind": "time", "at_utc": at.isoformat(),
                             "label": f"{tag} — {int(horizon_min)} dk ufuk doldu"}))
    return out


def format_message(alert: Dict[str, Any], price: Optional[float]) -> str:
    kind = alert.get("kind")
    what = {
        "above": f"{alert.get('price')} üstüne çıktı", "below": f"{alert.get('price')} altına indi",
        "stop": f"STOP seviyesi {alert.get('price')} geçildi", "target": f"HEDEF {alert.get('price')} geçildi",
        "pct_move": f"{alert.get('ref_price')} referansından %{alert.get('pct')} hareket",
        "time": "zaman alarmı",
    }.get(kind, kind)
    lines = [f"<b>{alert.get('symbol')}</b> — {what}"]
    if price is not None:
        lines.append(f"Fiyat: {price}")
    if alert.get("label"):
        lines.append(str(alert["label"]))
    return "\n".join(lines)


# ─── DB katmanı ──────────────────────────────────────────────────────────────

def _db():
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        if not is_db_available():
            return None
        return get_supabase_client()
    except Exception as exc:
        logger.warning("[price-alerts] DB erişilemedi: %s", exc)
        return None


def _require_db():
    client = _db()
    if client is None:
        raise RuntimeError("veritabanı erişilemiyor")
    return client


def _data(res: Any) -> List[Dict[str, Any]]:
    """Sarmalayıcı sonucu ({data, error}) → satırlar; hata RuntimeError."""
    if isinstance(res, dict):
        if res.get("error"):
            raise RuntimeError(str(res["error"])[:300])
        data = res.get("data")
    else:
        data = getattr(res, "data", None)
    if isinstance(data, dict):
        return [data]
    return data or []


def list_alerts(status: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    q = _require_db().table(TABLE).select("*")
    if status:
        q = q.eq("status", status)
    return _data(q.order("created_at", desc=True).limit(limit).execute())


def create_alerts(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    client = _require_db()
    active = client.count_rows(TABLE, "status=eq.active") or 0
    if active + len(rows) > MAX_ACTIVE_ALERTS:
        raise ValueError(f"en fazla {MAX_ACTIVE_ALERTS} aktif alarm")
    # PostgREST toplu insert'te tüm satırların anahtarları aynı olmalı.
    cols = sorted({k for r in rows for k in r})
    return _data(client.table(TABLE).insert([{c: r.get(c) for c in cols} for r in rows]))


def set_status(alert_id: int, status: str) -> Optional[Dict[str, Any]]:
    if status not in ("active", "disabled"):
        raise ValueError("status active|disabled olmalı")
    data = _data(_require_db().table(TABLE).eq("id", alert_id).update({"status": status}))
    return data[0] if data else None


def delete_alert(alert_id: int) -> bool:
    return bool(_data(_require_db().table(TABLE).eq("id", alert_id).delete(returning=True)))


def current_price(symbol: str) -> Optional[float]:
    """Yalnız TAZE MT5 fiyatı (bayat fiyatla tetik yok)."""
    try:
        from services import data_hub
        sym = data_hub._canonical_symbol(symbol)
        if not data_hub._mt5_price_is_fresh(sym):
            return None
        return data_hub.get_price(sym)
    except Exception:
        return None


def _claim(client, alert: Dict[str, Any], price: Optional[float], now: datetime) -> bool:
    """Atomik tetik: satırı yalnız hâlâ uygunsa güncelle; başka backend kaptıysa False."""
    patch: Dict[str, Any] = {"triggered_at": now.isoformat(), "triggered_price": price}
    q = client.table(TABLE).eq("id", alert["id"]).eq("status", "active")
    if alert.get("one_shot", True):
        patch["status"] = "triggered"
    else:
        cutoff = (now - timedelta(minutes=REPEAT_COOLDOWN_MIN)).strftime("%Y-%m-%dT%H:%M:%SZ")
        q = q.or_(f"triggered_at.is.null,triggered_at.lt.{cutoff}")
    try:
        return bool(_data(q.update(patch)))
    except RuntimeError as exc:
        logger.warning("[price-alerts] tetik yazılamadı #%s: %s", alert.get("id"), exc)
        return False


def _in_cooldown(alert: Dict[str, Any], now: datetime) -> bool:
    if alert.get("one_shot", True):
        return False
    last = _parse_ts(alert.get("triggered_at"))
    return last is not None and now - last < timedelta(minutes=REPEAT_COOLDOWN_MIN)


async def run_once(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Bir tarama turu: aktif alarmları değerlendir, tetiklenenleri işaretle + bildir."""
    now = now or _utcnow()
    client = _db()
    if client is None:
        _last_run.update(at=now.isoformat(), error="db_unavailable")
        return dict(_last_run)
    alerts = _data(client.table(TABLE).select("*").eq("status", "active").limit(MAX_ACTIVE_ALERTS).execute())
    prices: Dict[str, Optional[float]] = {}
    fired = 0
    for a in alerts:
        if _in_cooldown(a, now):
            continue
        sym = a.get("symbol") or ""
        if a.get("kind") in PRICE_KINDS and sym not in prices:
            prices[sym] = current_price(sym)
        price = prices.get(sym)
        if not evaluate(a, price, now):
            continue
        if not _claim(client, a, price, now):
            continue
        fired += 1
        logger.info("[price-alerts] tetik #%s %s %s fiyat=%s", a.get("id"), sym, a.get("kind"), price)
        if a.get("notify_telegram", True):
            try:
                from services.telegram_service import telegram_notifier
                await telegram_notifier.send_market_alert("Fiyat alarmı", format_message(a, price))
            except Exception as exc:
                logger.warning("[price-alerts] Telegram gönderilemedi: %s", exc)
    _last_run.update(at=now.isoformat(), checked=len(alerts), triggered=fired, error=None)
    return dict(_last_run)


def status() -> Dict[str, Any]:
    return {"enabled": os.getenv("PRICE_ALERTS_ENABLED", "1") == "1", "interval_s": LOOP_SECONDS,
            "last_run": dict(_last_run)}


async def alert_loop() -> None:
    """main.py lifespan döngüsü."""
    while True:
        try:
            await run_once()
        except Exception as exc:
            _last_run.update(at=_utcnow().isoformat(), error=str(exc)[:200])
            logger.warning("[price-alerts] tur hatası: %s", exc)
        await asyncio.sleep(LOOP_SECONDS)
