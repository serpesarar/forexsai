"""
event_calendar.py — yüksek-etkili olay penceresi (near_event stub'ının yerine).
=============================================================================
NEDEN: PLAYBOOK'un RİSK kuralı ("FOMC/CPI/NFP/EIA penceresinde yön tahmin etme, KÜÇÜLT/BEKLE")
2026-07-27 denetimine kadar HİÇ tetiklenemiyordu — run_decider.NEAR_EVENT sabit False'tu.
Olay-kaynaklı 5m aşırılığı Opus'a normal mean-reversion fırsatı gibi gidiyordu.

NEDEN BACKEND TAKVİMİNE BAĞLANMADI: backend/services/economic_calendar_service.py gerçek
veri değil — `_generate_today_events()` sabit-kodlu sentetik program ve DST'ye DUYARSIZ
(EIA'yı yıl boyu 14:30 UTC sanıyor; oysa 10:30 ET kışın 15:30 UTC). Yanlış saatte kapı
açmak, kapı olmamasından kötüdür. Burada saatler zoneinfo ile ET'den hesaplanır.

KAPSAM (dürüstlük): yalnız GERÇEKTEN kural-tabanlı olaylar kodda:
  · EIA Ham Petrol Stokları — her Çarşamba 10:30 ET (tatil haftalarında Perşembe'ye kayar:
    yakalanmaz, bilinen sınır)
  · NFP (Tarım Dışı İstihdam) — ayın ilk Cuma'sı 08:30 ET
FOMC/CPI takvimden türetilemez (tarihleri yıl başında ilan edilir) → memory/event_dates.json
dosyasından okunur. Dosya yoksa o olaylar hiç tetiklenmez (fail-open, uydurma tarih YOK).

Dosya biçimi (UTC değil — YEREL ET saati, DST kod tarafından uygulanır):
  {"events": [{"date": "2026-01-28", "time_et": "14:00", "name": "FOMC kararı",
               "symbols": ["*"], "impact": "high"}]}
  symbols: ["*"] = tüm semboller; ya da ["USOIL.FOREX", "XAUUSD"] gibi liste.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENT_DATES_FILE = HERE / "memory" / "event_dates.json"

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:                       # zoneinfo yoksa modül sessizce devre dışı (fail-open)
    _ET = None

NEAR_EVENT_MINUTES = int(os.getenv("NEAR_EVENT_MINUTES", "30"))   # backend CALENDAR_GATE ile aynı
EVENT_CALENDAR_ENABLED = os.getenv("EVENT_CALENDAR_ENABLED", "1") == "1"

_ALL = "*"
# Kural-tabanlı olaylar: (ad, ET saati, etkilenen semboller, impact)
_EIA = ("EIA Ham Petrol Stokları", (10, 30), ["USOIL.FOREX", "XAUUSD"], "high")
_NFP = ("Tarım Dışı İstihdam (NFP)", (8, 30), [_ALL], "high")

_dates_cache: tuple[float, list] | None = None
_DATES_TTL = 300.0


def _et_dt(day: datetime, hm: tuple[int, int]) -> datetime | None:
    """Verilen günün ET saatini UTC'ye çevir (DST-doğru)."""
    if _ET is None:
        return None
    return day.astimezone(_ET).replace(hour=hm[0], minute=hm[1], second=0,
                                       microsecond=0).astimezone(timezone.utc)


def _rule_events(now: datetime) -> list[tuple[datetime, str, list, str]]:
    """O gün ve komşu günlerdeki kural-tabanlı olaylar (gün sınırı penceresini kaçırmamak için
    dün/bugün/yarın taranır — ET günü UTC gününden kayabilir)."""
    out = []
    if _ET is None:
        return out
    for delta in (-1, 0, 1):
        d = (now + timedelta(days=delta)).astimezone(_ET)
        if d.weekday() == 2:                                   # Çarşamba → EIA
            name, hm, syms, imp = _EIA
            ts = _et_dt(d, hm)
            if ts:
                out.append((ts, name, syms, imp))
        if d.weekday() == 4 and d.day <= 7:                    # ayın ilk Cuma'sı → NFP
            name, hm, syms, imp = _NFP
            ts = _et_dt(d, hm)
            if ts:
                out.append((ts, name, syms, imp))
    return out


def _file_events(now: datetime) -> list[tuple[datetime, str, list, str]]:
    """memory/event_dates.json'daki elle girilmiş olaylar (FOMC/CPI vb.). Yoksa boş."""
    global _dates_cache
    import time as _t
    if _dates_cache and _t.time() - _dates_cache[0] < _DATES_TTL:
        rows = _dates_cache[1]
    else:
        rows = []
        try:
            if EVENT_DATES_FILE.exists():
                rows = (json.loads(EVENT_DATES_FILE.read_text(encoding="utf-8")) or {}).get("events") or []
        except Exception as e:
            print("  event_calendar: event_dates.json okunamadı (devam):", e)
            rows = []
        _dates_cache = (_t.time(), rows)
    out = []
    if _ET is None:
        return out
    today_et = now.astimezone(_ET).date()
    for r in rows:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
            if abs((d - today_et).days) > 1:
                continue
            hh, mm = (r.get("time_et") or "08:30").split(":")
            ts = datetime(d.year, d.month, d.day, int(hh), int(mm),
                          tzinfo=_ET).astimezone(timezone.utc)
            out.append((ts, r.get("name") or "planlı olay",
                        r.get("symbols") or [_ALL], r.get("impact") or "high"))
        except Exception:
            continue
    return out


def near_event(symbol: str, now: datetime | None = None,
               minutes: int | None = None) -> dict | None:
    """Sembol için ±minutes penceresinde yüksek-etkili olay var mı?
    Dönüş: {"event", "impact", "minutes_to" (− = geçti), "window_min"} ya da None.
    Fail-open: her hata None (karar akışı asla bloklanmaz)."""
    if not EVENT_CALENDAR_ENABLED:
        return None
    try:
        now = now or datetime.now(timezone.utc)
        win = minutes if minutes is not None else NEAR_EVENT_MINUTES
        best = None
        for ts, name, syms, imp in _rule_events(now) + _file_events(now):
            if imp != "high":
                continue
            if _ALL not in syms and symbol not in syms:
                continue
            delta_min = (ts - now).total_seconds() / 60.0
            if abs(delta_min) <= win and (best is None or abs(delta_min) < abs(best[0])):
                best = (delta_min, name, imp)
        if best is None:
            return None
        return {"event": best[1], "impact": best[2],
                "minutes_to": round(best[0]), "window_min": win}
    except Exception as e:
        print("  event_calendar hatası (fail-open):", e)
        return None


if __name__ == "__main__":
    now = datetime.now(timezone.utc)
    print(f"Şimdi (UTC): {now:%Y-%m-%d %H:%M} | pencere ±{NEAR_EVENT_MINUTES}dk")
    print(f"event_dates.json: {'VAR' if EVENT_DATES_FILE.exists() else 'YOK (FOMC/CPI tetiklenmez)'}")
    for sym in ("NDX.INDX", "GDAXI.INDX", "XAUUSD", "USOIL.FOREX"):
        print(f"  {sym:14s} → {near_event(sym, now) or 'olay yok'}")
    print("\nÖnümüzdeki 7 günün kural-tabanlı olayları:")
    for d in range(8):
        t = now + timedelta(days=d)
        for ts, name, syms, imp in _rule_events(t):
            if abs((ts - t).total_seconds()) < 86400 / 2:
                print(f"  {ts:%Y-%m-%d %H:%M} UTC  {name}  → {syms}")
