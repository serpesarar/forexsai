import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, call, patch

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


def _load_background_scheduler_module(module_name: str):
    with patch.dict(
        sys.modules,
        {
            "utils.safe_supabase": SimpleNamespace(safe_get_data=lambda value: value, safe_get_error=lambda value: None),
            "database.supabase_client": SimpleNamespace(get_supabase_client=lambda: None, is_db_available=lambda: True),
            "services.ml_prediction_service": SimpleNamespace(get_ml_prediction=AsyncMock()),
            "services.ta_service": SimpleNamespace(compute_ta_snapshot=AsyncMock()),
            "services.data_fetcher": SimpleNamespace(fetch_eod_candles=AsyncMock(), fetch_latest_price=AsyncMock()),
            "services.marketaux_service": SimpleNamespace(fetch_marketaux_headlines=AsyncMock()),
            "services.outcome_tracker": SimpleNamespace(check_pending_outcomes=AsyncMock(), check_multi_target_outcome=AsyncMock()),
            "services.error_analysis_service": SimpleNamespace(check_and_analyze_failed_predictions=AsyncMock()),
            "services.signal_lifecycle": SimpleNamespace(check_lifecycle_if_needed=AsyncMock()),
        },
    ):
        module_path = backend_dir / "services" / "background_scheduler.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module


@pytest.mark.asyncio
async def test_log_pulse_signals_uses_only_legacy_default_timeframes():
    scheduler = _load_background_scheduler_module("test_background_scheduler_legacy")
    scheduler.TRACKED_SYMBOLS = ["XAUUSD"]
    scheduler._last_pulse_log.clear()

    check_and_log = AsyncMock()
    sleep_mock = AsyncMock()

    with patch.object(scheduler, "is_db_available", return_value=True), patch.object(
        scheduler, "_check_and_log_pulse", check_and_log
    ), patch.object(scheduler.asyncio, "sleep", sleep_mock):
        await scheduler.log_pulse_signals_if_needed()

    assert check_and_log.await_args_list == [
        call("XAUUSD", "emel", None, "1h"),
        call("XAUUSD", "pulse1", None, "5m"),
        call("XAUUSD", "pulse2", None, "15m"),
        call("XAUUSD", "pulse3", None, "5m"),
    ]
    assert all(args.args[1] != "emel_inverse" for args in check_and_log.await_args_list)
    assert sleep_mock.await_count == 4


@pytest.mark.asyncio
async def test_log_pulse_signals_respects_interval_guard_after_first_run():
    scheduler = _load_background_scheduler_module("test_background_scheduler_interval")
    scheduler.TRACKED_SYMBOLS = ["NDX.INDX"]
    scheduler._last_pulse_log.clear()

    check_and_log = AsyncMock()

    with patch.object(scheduler, "is_db_available", return_value=True), patch.object(
        scheduler, "_check_and_log_pulse", check_and_log
    ), patch.object(scheduler.asyncio, "sleep", AsyncMock()):
        await scheduler.log_pulse_signals_if_needed()
        await scheduler.log_pulse_signals_if_needed()

    assert check_and_log.await_count == 4
