"""Scheduled bias runs — no manual triggering needed.

On each tick (called ~every 60s from main's background loop) this checks the NY
clock and, on trading days:
  * at each configured run window (default 08:00 & 09:45 ET) → runs the debate
    engine and logs the verdict to bias_test_log with that window's run_label;
  * shortly after the cash close (default 16:15 ET) → fills that day's outcomes.

Opt-in: gated behind ``settings.bias_auto_run_enabled`` (default False) because
each run spends real LLM tokens. Idempotent: an in-memory guard plus a DB check
prevent duplicate runs across ticks and restarts.
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
_FILL_BAND_MIN = 8

# In-memory "done today" guards (date-scoped), reset naturally each new day.
_ran: set[tuple[str, str]] = set()   # (ny_date, run_label) — completed
_filled: set[str] = set()            # ny_date — completed
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

    # Non-trading days: nothing to run or fill.
    if ctx["current_session"] == "closed" or ctx["is_holiday"]:
        return None

    _prune_guards(ny_date)
    actions: dict[str, str] = {}

    # ── Run windows ───────────────────────────────────────────────────────────
    for w_min, label in _parse_windows(settings.bias_run_windows_et):
        if not (0 <= minute - w_min < _WINDOW_BAND_MIN):
            continue
        key = (ny_date, label)
        # completed, already in-flight on another tick, or already in DB → skip.
        if key in _ran or key in _inflight:
            continue
        if bts.already_logged(ny_date, label):
            _ran.add(key)
            continue
        _inflight.add(key)                      # mark BEFORE awaiting (dedup)
        try:
            from services.bias_debate_engine import run_debate
            verdict = await run_debate(now_utc=now_utc)
            res = await bts.record_run(verdict, run_label=label, run_ts=now_utc)
            _ran.add(key)
            actions[label] = f"logged {res['predicted_bias']}"
            logger.info("[bias-auto] %s @ %s → %s", label, ctx["ny_time"],
                        res["predicted_bias"])
        except Exception as e:
            logger.warning("[bias-auto] run %s failed: %s", label, e)
            actions[label] = f"failed: {str(e)[:80]}"
        finally:
            _inflight.discard(key)

    # ── Outcome fill after close ──────────────────────────────────────────────
    fill_min = _parse_hhmm(settings.bias_fill_time_et)
    fkey = ("__fill__", ny_date)
    if fill_min is not None and 0 <= minute - fill_min < _FILL_BAND_MIN \
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

    return actions or None
