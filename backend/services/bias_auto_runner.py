"""Scheduled bias runs — no manual triggering needed.

On each tick (called ~every 60s from main's background loop):
  * NY trading days, ET windows (default 08:00 & 09:45 ET) → NDX debate →
    bias_test_log; 16:15 ET → o günün outcome'ları doldurulur.
  * UTC hafta içi, sembol pencereleri (``BIAS_SYMBOL_RUNS_UTC``, default
    XAU 08:00 / DAX 08:10 / USOIL 13:05 UTC) → o sembolün debate'i; 22:20 UTC
    (``BIAS_SYMBOL_FILL_UTC``) → geç kapanan sembollerin notlaması.

Çok-sembol pencereler 2026-07-19'da lokal koda geri inşa edildi — önceki
deploy yalnız-NDX runner içeriyordu ve XAU/DAX/USOIL koşuları susmuştu.

Opt-in: gated behind ``settings.bias_auto_run_enabled`` (default False) because
each run spends real LLM tokens. Idempotent: in-memory guard + DB check +
record_run'ın kendi insert-önü idempotensisi (çift-yazar koruması).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from config import settings
from services import bias_test_service as bts
from services import session_context_service as sc

logger = logging.getLogger(__name__)

_WINDOW_BAND_MIN = 3       # fire if within this many minutes of the window
_SYMBOL_BAND_MIN = 12      # UTC sembol pencereleri: önceki debate ~6dk tick yiyebilir
_FILL_BAND_MIN = 8

# In-memory "done today" guards (date-scoped), reset naturally each new day.
_ran: set[tuple[str, str]] = set()   # (ny_date, run_label) — completed
_filled: set[str] = set()            # ny_date — ET (16:15) fill completed
_filled_utc: set[str] = set()        # ny_date — UTC (22:20) sembol fill completed
# In-flight guard: a debate can take >60s while ticks fire every 60s, so mark
# work as started BEFORE awaiting to stop a second tick launching a duplicate
# (expensive) run before the first finishes / writes its row.
_inflight: set[tuple[str, str]] = set()


def _prune_guards(keep_date: str) -> None:
    """Drop completed-guard entries from previous days so the sets can't grow
    forever. (_inflight self-clears in each tick's finally, so it's left alone.)"""
    for k in [k for k in _ran if k[0] != keep_date]:
        _ran.discard(k)
    for d in [d for d in _filled if d != keep_date]:
        _filled.discard(d)
    for d in [d for d in _filled_utc if d != keep_date]:
        _filled_utc.discard(d)


def _parse_symbol_windows(spec: str) -> list[tuple[int, str, str]]:
    """'08:00=xau_daily:XAUUSD,...' → [(480, 'xau_daily', 'XAUUSD'), ...] (UTC dk)."""
    out: list[tuple[int, str, str]] = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part or "=" not in part or ":" not in part.split("=", 1)[1]:
            continue
        hhmm, rest = part.split("=", 1)
        label, sym = rest.split(":", 1)
        try:
            h, m = hhmm.strip().split(":")
            out.append((int(h) * 60 + int(m), label.strip(), sym.strip()))
        except ValueError:
            logger.warning("[bias-auto] bad symbol window spec: %r", part)
    return out


def _parse_windows(spec: str) -> list[tuple[int, str]]:
    """'08:00=0800_main,09:45=0945_confirm' → [(480,'0800_main'), (585,'0945_confirm')]."""
    out: list[tuple[int, str]] = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        hhmm, label = part.split("=", 1)
        try:
            h, m = hhmm.strip().split(":")
            out.append((int(h) * 60 + int(m), label.strip()))
        except ValueError:
            logger.warning("[bias-auto] bad window spec: %r", part)
    return out


def _parse_hhmm(s: str) -> Optional[int]:
    try:
        h, m = s.strip().split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return None


async def tick(now_utc: Optional[datetime] = None) -> Optional[dict]:
    """One scheduler step. Returns a small summary of any action taken."""
    if not settings.bias_auto_run_enabled:
        return None

    now_utc = now_utc or datetime.now(timezone.utc)
    ctx = sc.get_session_context(now_utc)
    ny = datetime.fromisoformat(ctx["ny_time"])
    ny_date = ctx["ny_time"][:10]
    minute = ny.hour * 60 + ny.minute

    _prune_guards(ny_date)
    actions: dict[str, str] = {}
    ny_trading = ctx["current_session"] != "closed" and not ctx["is_holiday"]
    utc_weekday = now_utc.weekday() < 5   # sembol pencereleri NY takviminden bağımsız

    async def _run_window(label: str, symbol: Optional[str]) -> None:
        key = (ny_date, label)
        # completed, already in-flight on another tick, or already in DB → skip.
        if key in _ran or key in _inflight:
            return
        if bts.already_logged(ny_date, label):
            _ran.add(key)
            return
        _inflight.add(key)                      # mark BEFORE awaiting (dedup)
        try:
            from services.bias_debate_engine import run_debate
            verdict = await (run_debate(symbol=symbol, now_utc=now_utc)
                             if symbol else run_debate(now_utc=now_utc))
            res = await bts.record_run(verdict, run_label=label, run_ts=now_utc)
            _ran.add(key)
            actions[label] = f"logged {res.get('predicted_bias')}"
            logger.info("[bias-auto] %s @ %s → %s", label, ctx["ny_time"],
                        res.get("predicted_bias"))
        except Exception as e:
            logger.warning("[bias-auto] run %s failed: %s", label, e)
            actions[label] = f"failed: {str(e)[:80]}"
        finally:
            _inflight.discard(key)

    # ── NDX ET pencereleri (NY işlem günü şartıyla) ──────────────────────────
    if ny_trading:
        for w_min, label in _parse_windows(settings.bias_run_windows_et):
            if 0 <= minute - w_min < _WINDOW_BAND_MIN:
                await _run_window(label, None)

    # ── Çok-sembol UTC pencereleri (XAU/DAX/USOIL — 2026-07-19'da geri inşa) ──
    # NOT: yalnız-NDX runner'lı deploy bu pencereleri silmişti; artık koddalar.
    # Bant geniş (_SYMBOL_BAND_MIN): önceki pencerenin ~6dk'lık debate'i tick
    # kaçırtabiliyor. Sembol tatilleri kontrol edilmez (nadir boşa koşu kabul).
    if utc_weekday:
        utc_minute = now_utc.hour * 60 + now_utc.minute
        for w_min, label, sym in _parse_symbol_windows(settings.bias_symbol_runs_utc):
            if 0 <= utc_minute - w_min < _SYMBOL_BAND_MIN:
                await _run_window(label, sym)

    # ── ET outcome fill (NDX kapanışı sonrası) ───────────────────────────────
    fill_min = _parse_hhmm(settings.bias_fill_time_et)
    fkey = ("__fill__", ny_date)
    if ny_trading and fill_min is not None and 0 <= minute - fill_min < _FILL_BAND_MIN \
            and ny_date not in _filled and fkey not in _inflight:
        _inflight.add(fkey)
        try:
            res = await bts.fill_outcomes(ny_date)
            _filled.add(ny_date)
            actions["fill"] = f"{res['rows_updated']} rows · {res['actual_close_direction']}"
            logger.info("[bias-auto] filled outcomes %s: %s", ny_date, res)
        except Exception as e:
            logger.warning("[bias-auto] fill %s failed: %s", ny_date, e)
        finally:
            _inflight.discard(fkey)

    # ── UTC sembol fill (22:20 — XAU 17:00 NY kapanışından sonra; ET fill'in
    #    notlayamadığı sembolleri yakalar; fill_outcomes idempotent) ──────────
    ufill_min = _parse_hhmm(settings.bias_symbol_fill_utc)
    ufkey = ("__fill_utc__", ny_date)
    if utc_weekday and ufill_min is not None \
            and 0 <= (now_utc.hour * 60 + now_utc.minute) - ufill_min < _FILL_BAND_MIN \
            and ny_date not in _filled_utc and ufkey not in _inflight:
        _inflight.add(ufkey)
        try:
            res = await bts.fill_outcomes(ny_date)
            _filled_utc.add(ny_date)
            actions["fill_utc"] = f"{res['rows_updated']} rows"
            logger.info("[bias-auto] UTC fill %s: %s", ny_date, res)
        except Exception as e:
            logger.warning("[bias-auto] UTC fill %s failed: %s", ny_date, e)
        finally:
            _inflight.discard(ufkey)

    return actions or None
