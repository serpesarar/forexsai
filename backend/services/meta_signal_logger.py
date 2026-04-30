"""
Meta-Signal Logger
Logs meta-engine signals to Supabase and updates combination stats.
"""

from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from itertools import combinations
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

META_MODEL_TYPE = "meta"
META_STRATEGY = "META_ENGINE"
META_SIGNAL_TIMEFRAME = "20m"
META_SNAPSHOT_INTERVAL_SECONDS = 20 * 60
_last_meta_snapshot_log: Dict[str, datetime] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(parsed):
        return default
    return parsed


def _get_last_persisted_meta_log_time(symbol: str) -> Optional[datetime]:
    from database.supabase_client import get_supabase_client, is_db_available
    from utils.safe_supabase import safe_get_data

    if not is_db_available():
        return None

    client = get_supabase_client()
    if not client:
        return None

    try:
        result = client.table("prediction_logs").select(
            "created_at"
        ).eq(
            "symbol", symbol
        ).eq(
            "model_type", META_MODEL_TYPE
        ).order(
            "created_at", desc=True
        ).limit(1).execute()
        rows = safe_get_data(result) or []
        if not rows:
            return None
        return _parse_datetime(rows[0].get("created_at"))
    except Exception as exc:
        logger.debug("[MetaSignalLogger] last meta snapshot lookup failed for %s: %s", symbol, exc)
        return None


def _resolve_last_meta_snapshot_time(symbol: str) -> Optional[datetime]:
    memory_last = _last_meta_snapshot_log.get(symbol)
    db_last = _get_last_persisted_meta_log_time(symbol)
    if memory_last and db_last:
        return max(memory_last, db_last)
    return memory_last or db_last


def should_log_meta_snapshot(symbol: str, now: Optional[datetime] = None) -> bool:
    reference = now or _utc_now()
    last_logged = _resolve_last_meta_snapshot_time(symbol)
    if not last_logged:
        return True
    return (reference - last_logged).total_seconds() >= META_SNAPSHOT_INTERVAL_SECONDS


async def capture_meta_snapshot_if_due(signal_data: Dict[str, Any]) -> Optional[str]:
    symbol = str(signal_data.get("symbol") or "").upper().strip()
    if not symbol:
        return None

    now = _utc_now()
    if not should_log_meta_snapshot(symbol, now=now):
        return None

    prediction_id = await log_meta_prediction(signal_data, timeframe=META_SIGNAL_TIMEFRAME)
    if prediction_id:
        _last_meta_snapshot_log[symbol] = now
    return prediction_id


async def log_meta_prediction(signal_data: Dict[str, Any], timeframe: str = "1h") -> Optional[str]:
    try:
        from database.supabase_client import get_supabase_client, is_db_available
        from services.prediction_logger import _check_session_filter, _close_existing_signal, _get_current_session, _has_active_signal
        from services.target_config import calculate_stoploss_price, calculate_target_prices, pips_from_price_change
        from utils.safe_supabase import safe_get_data, safe_get_error

        direction = str(signal_data.get("direction") or "").upper().strip()
        symbol = str(signal_data.get("symbol") or "").upper().strip()
        if direction not in {"BUY", "SELL"} or not symbol:
            return None

        should_filter, reason = _check_session_filter(symbol)
        if should_filter:
            logger.info("[MetaSignalLogger] %s", reason)
            return None

        entry_price = _coerce_float(signal_data.get("entry_price") or 0)
        confidence = _coerce_float(signal_data.get("confidence") or 0)
        if entry_price <= 0:
            return None

        if not is_db_available():
            return None

        client = get_supabase_client()
        if not client:
            return None

        normalized_timeframe = (timeframe or "1h").lower().strip() or "1h"

        has_active, active_signal_id, active_direction = _has_active_signal(
            client,
            symbol,
            META_MODEL_TYPE,
            normalized_timeframe,
            direction,
        )

        if has_active:
            if active_direction != direction:
                if not active_signal_id:
                    return None
                closed = _close_existing_signal(
                    client,
                    active_signal_id,
                    direction,
                    entry_price,
                    reason="direction_flip",
                )
                if not closed:
                    return None

        targets = calculate_target_prices(entry_price, direction, symbol, normalized_timeframe)
        stop_loss = calculate_stoploss_price(entry_price, direction, symbol, normalized_timeframe)
        targets["SL"] = round(stop_loss, 4)

        stop_loss_pips = abs(pips_from_price_change(abs(entry_price - stop_loss), symbol))
        factors = {
            "session": _get_current_session(),
            "target_type": "static_pips",
            "strategy": META_STRATEGY,
            "source": META_STRATEGY,
            "source_combo": signal_data.get("source_combo"),
            "regime": signal_data.get("regime"),
            "agreement_ratio": signal_data.get("agreement_ratio"),
            "technical_score": signal_data.get("technical_score"),
            "passed_conditions": signal_data.get("passed_conditions", []),
            "risk_reward": signal_data.get("risk_reward"),
            "strength": signal_data.get("strength"),
            "model_breakdown": signal_data.get("model_breakdown", {}),
            "alternatives": signal_data.get("alternatives", []),
            "meta_snapshot_interval_seconds": META_SNAPSHOT_INTERVAL_SECONDS,
            "meta_live_stop_loss": round(_coerce_float(signal_data.get("stop_loss"), stop_loss), 4),
            "meta_live_take_profit_1": round(_coerce_float(signal_data.get("take_profit_1"), 0.0), 4),
            "meta_live_take_profit_2": round(_coerce_float(signal_data.get("take_profit_2"), 0.0), 4),
        }
        factors = {key: value for key, value in factors.items() if value not in (None, "", [], {})}

        # Enrich with comprehensive feature snapshot for AI-ops analysis (failsafe)
        try:
            from services.signal_feature_snapshot import build_signal_feature_snapshot
            snap = await build_signal_feature_snapshot(symbol)
            if snap:
                for k, v in snap.items():
                    factors.setdefault(k, v)
        except Exception as snap_err:
            logger.debug("[MetaSignalLogger] snapshot enrich failed: %s", snap_err)

        record = {
            "symbol": symbol,
            "timeframe": normalized_timeframe,
            "ml_direction": direction,
            "ml_confidence": round(confidence, 1),
            "ml_target_price": targets.get("TP1") or None,
            "ml_stop_price": stop_loss,
            "ml_entry_price": entry_price,
            "claude_direction": direction,
            "claude_confidence": round(confidence, 1),
            "claude_model": META_STRATEGY,
            "factors": factors,
            "outcome_checked": False,
            "strategy": META_STRATEGY,
            "status": "active",
            "targets": targets,
            "stop_loss_pips": round(stop_loss_pips, 2),
            "targets_hit": {tp: False for tp in targets if tp != "SL"},
            "highest_profit_pips": 0,
            "lowest_drawdown_pips": 0,
            "model_type": META_MODEL_TYPE,
        }

        result = client.table("prediction_logs").insert_ignore(record)
        if safe_get_error(result):
            logger.error("[MetaSignalLogger] prediction_logs insert error: %s", result["error"])
            return None
        if result.get("duplicate"):
            return None

        rows = safe_get_data(result) or []
        if rows:
            prediction_id = rows[0].get("id")
            await log_meta_signal(signal_data)
            _last_meta_snapshot_log[symbol] = _utc_now()
            logger.info("[MetaSignalLogger] Logged meta prediction %s for %s", prediction_id, symbol)
            return prediction_id
        return None
    except Exception as e:
        logger.error(f"[MetaSignalLogger] Prediction log error: {e}")
        return None


async def log_meta_signal(signal_data: Dict[str, Any]) -> Optional[str]:
    """Log a meta-signal to the meta_signals table. Returns the row ID."""
    try:
        from database.supabase_client import get_supabase_client
        from utils.safe_supabase import safe_get_data
        client = get_supabase_client()
        if not client:
            logger.warning("[MetaSignalLogger] No Supabase client")
            return None

        row = {
            "symbol": signal_data.get("symbol"),
            "direction": signal_data.get("direction"),
            "confidence": signal_data.get("confidence"),
            "strength": signal_data.get("strength"),
            "source_combo": signal_data.get("source_combo"),
            "regime": signal_data.get("regime"),
            "agreement_ratio": signal_data.get("agreement_ratio"),
            "technical_score": signal_data.get("technical_score"),
            "passed_conditions": signal_data.get("passed_conditions", []),
            "entry_price": signal_data.get("entry_price"),
            "stop_loss": signal_data.get("stop_loss"),
            "take_profit_1": signal_data.get("take_profit_1"),
            "take_profit_2": signal_data.get("take_profit_2"),
            "risk_reward": signal_data.get("risk_reward"),
            "model_breakdown": signal_data.get("model_breakdown", {}),
            "status": "active",
        }

        result = client.table("meta_signals").insert(row)
        data = safe_get_data(result) or []

        if data and len(data) > 0:
            row_id = data[0].get("id")
            logger.info(f"[MetaSignalLogger] Logged signal {row_id} for {signal_data.get('symbol')}")
            return row_id

        return None
    except Exception as e:
        logger.error(f"[MetaSignalLogger] Insert error: {e}")
        return None


async def update_combination_stats(
    combo_key: str,
    symbol: str,
    regime: str,
    is_win: bool,
    profit_pips: float,
) -> None:
    """Update meta_combination_stats after a signal resolves."""
    try:
        from database.supabase_client import get_supabase_client
        from utils.safe_supabase import safe_get_data
        client = get_supabase_client()
        if not client:
            return

        # Check if row exists
        existing = client.table("meta_combination_stats") \
            .select("*") \
            .eq("combo_key", combo_key) \
            .eq("symbol", symbol) \
            .eq("regime", regime) \
            .limit(1) \
            .execute()

        rows = safe_get_data(existing) or []
        now_iso = _utc_now().isoformat().replace("+00:00", "Z")

        if rows and len(rows) > 0:
            # Update existing
            row = rows[0]
            total = row.get("total_signals", 0) + 1
            wins = row.get("wins", 0) + (1 if is_win else 0)
            losses = row.get("losses", 0) + (0 if is_win else 1)
            win_rate = wins / total if total > 0 else 0

            # Running average for pips
            if is_win:
                old_avg = row.get("avg_profit_pips", 0) or 0
                old_count = row.get("wins", 0)
                avg_profit = ((old_avg * old_count) + profit_pips) / max(1, wins)
                avg_loss = row.get("avg_loss_pips", 0) or 0
            else:
                old_avg = row.get("avg_loss_pips", 0) or 0
                old_count = row.get("losses", 0)
                avg_loss = ((old_avg * old_count) + abs(profit_pips)) / max(1, losses)
                avg_profit = row.get("avg_profit_pips", 0) or 0

            # Profit factor = (wins * avg_profit) / (losses * avg_loss)
            total_profit = wins * avg_profit if wins > 0 else 0
            total_loss_val = losses * avg_loss if losses > 0 else 1
            profit_factor = total_profit / total_loss_val if total_loss_val > 0 else 0

            # Expectancy = (win_rate * avg_profit) - ((1-win_rate) * avg_loss)
            expectancy = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)

            client.table("meta_combination_stats").eq("id", row["id"]).update({
                "total_signals": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 4),
                "avg_profit_pips": round(avg_profit, 2),
                "avg_loss_pips": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "expectancy": round(expectancy, 2),
                "last_updated": now_iso,
            })

            logger.info(
                f"[MetaSignalLogger] Updated combo {combo_key}/{symbol}/{regime}: "
                f"WR={win_rate:.0%} PF={profit_factor:.2f}"
            )
        else:
            # Insert new
            new_row = {
                "combo_key": combo_key,
                "symbol": symbol,
                "regime": regime,
                "total_signals": 1,
                "wins": 1 if is_win else 0,
                "losses": 0 if is_win else 1,
                "avg_profit_pips": round(profit_pips, 2) if is_win else 0,
                "avg_loss_pips": round(abs(profit_pips), 2) if not is_win else 0,
                "win_rate": 1.0 if is_win else 0.0,
                "profit_factor": 0,
                "expectancy": 0,
                "last_updated": now_iso,
            }
            client.table("meta_combination_stats").insert(new_row)
            logger.info(f"[MetaSignalLogger] Created combo {combo_key}/{symbol}/{regime}")

    except Exception as e:
        logger.error(f"[MetaSignalLogger] Stats update error: {e}")


async def backfill_combination_stats() -> Dict[str, Any]:
    """
    Populate meta_combination_stats from historical prediction_logs.
    Groups concurrent signals (within 15min window) by direction agreement.
    """
    try:
        from database.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            return {"error": "No Supabase client"}

        # Query prediction_logs and compute in Python

        logger.info("[MetaSignalLogger] Starting backfill from prediction_logs...")

        # Fetch all resolved signals with model_type (Run safely in a thread to avoid blocking)
        import asyncio
        
        def fetch_signals():
            all_sigs = []
            for model_type in ['ml', 'pulse1', 'pulse2', 'pulse3', 'emel', 'smc']:
                res = client.table("prediction_logs") \
                    .select("id,symbol,model_type,ml_direction,status,created_at,highest_profit_pips,lowest_drawdown_pips") \
                    .eq("model_type", model_type) \
                    .in_("status", ["completed", "stopped"]) \
                    .order("created_at", desc=True) \
                    .limit(2000) \
                    .execute()
                rows = res.get("data", []) if isinstance(res, dict) else (res.data if hasattr(res, "data") else [])
                all_sigs.extend(rows or [])
            return all_sigs

        all_signals = await asyncio.to_thread(fetch_signals)

        logger.info(f"[MetaSignalLogger] Fetched {len(all_signals)} historical signals")

        if not all_signals:
            return {"message": "No historical data found", "combos_created": 0}

        # Group by symbol + hour window
        from datetime import datetime, timedelta
        from collections import defaultdict

        # Parse and group
        hourly_groups = defaultdict(list)
        for sig in all_signals:
            try:
                created = sig.get("created_at", "")
                if isinstance(created, str):
                    # Truncate to hour
                    hour_key = created[:13]  # "2026-03-27T14"
                else:
                    hour_key = str(created)[:13]

                key = f"{sig['symbol']}|{hour_key}"
                hourly_groups[key].append(sig)
            except Exception:
                continue

        # Find combos where 2+ models agree on direction
        combo_results = defaultdict(lambda: {"wins": 0, "losses": 0, "profit_sum": 0, "loss_sum": 0})

        for group_key, group_signals in hourly_groups.items():
            if len(group_signals) < 2:
                continue

            symbol = group_signals[0]["symbol"]

            # Group by direction (UNIQUE models only for combinations)
            buy_models = list(set([s["model_type"] for s in group_signals if s.get("ml_direction") == "BUY"]))
            sell_models = list(set([s["model_type"] for s in group_signals if s.get("ml_direction") == "SELL"]))

            # Generate all 2+ model combinations that agree
            for models_list, direction in [(buy_models, "BUY"), (sell_models, "SELL")]:
                if len(models_list) < 2:
                    continue

                # Generate combos of size 2 to len
                for size in range(2, min(len(models_list) + 1, 7)):
                    for combo in combinations(sorted(models_list), size):
                        combo_key = "+".join(combo)
                        stat_key = f"{combo_key}|{symbol}|UNKNOWN"

                        # Check if these specific signals were wins
                        combo_signals = [
                            s for s in group_signals
                            if s["model_type"] in combo and s.get("ml_direction") == direction
                        ]

                        for cs in combo_signals:
                            is_win = cs.get("status") == "completed"
                            profit = float(cs.get("highest_profit_pips", 0) or 0)
                            loss = float(abs(cs.get("lowest_drawdown_pips", 0) or 0))

                            if is_win:
                                combo_results[stat_key]["wins"] += 1
                                combo_results[stat_key]["profit_sum"] += profit
                            else:
                                combo_results[stat_key]["losses"] += 1
                                combo_results[stat_key]["loss_sum"] += loss

            # Yield control back to event loop briefly so API stays responsive
            await asyncio.sleep(0)

        # Collect rows to upsert
        rows_to_upsert = []
        for stat_key, stats in combo_results.items():
            parts = stat_key.split("|")
            if len(parts) != 3:
                continue

            combo_key, symbol, regime = parts
            total = stats["wins"] + stats["losses"]
            if total < 3:
                continue

            win_rate = stats["wins"] / total if total > 0 else 0
            avg_profit = stats["profit_sum"] / max(1, stats["wins"])
            avg_loss = stats["loss_sum"] / max(1, stats["losses"])
            pf = (stats["wins"] * avg_profit) / max(1, stats["losses"] * avg_loss) if stats["losses"] > 0 else 0
            expectancy = (win_rate * avg_profit) - ((1 - win_rate) * avg_loss)

            rows_to_upsert.append({
                "combo_key": combo_key,
                "symbol": symbol,
                "regime": regime,
                "total_signals": total,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "avg_profit_pips": round(avg_profit, 2),
                "avg_loss_pips": round(avg_loss, 2),
                "win_rate": round(win_rate, 4),
                "profit_factor": round(pf, 2),
                "expectancy": round(expectancy, 2),
            })
            
        inserted = len(rows_to_upsert)
        
        # Upsert in bulk using thread to avoid blocking the event loop
        def bulk_upsert(rows):
            if not rows: return
            try:
                # Break into chunks of 500
                for i in range(0, len(rows), 500):
                    batch = rows[i:i+500]
                    client.table("meta_combination_stats").upsert(
                        batch,
                        on_conflict="combo_key,symbol,regime"
                    )
            except Exception as e:
                logger.error(f"Bulk upsert error: {e}")

        if rows_to_upsert:
            await asyncio.to_thread(bulk_upsert, rows_to_upsert)

        logger.info(f"[MetaSignalLogger] Backfill complete: {inserted} combos updated")
        return {
            "message": "Backfill complete",
            "total_signals_analyzed": len(all_signals),
            "combos_created": inserted,
        }

    except Exception as e:
        logger.error(f"[MetaSignalLogger] Backfill error: {e}")
        return {"error": str(e)}
