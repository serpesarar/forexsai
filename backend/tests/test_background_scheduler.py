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
            "services.outcome_tracker": SimpleNamespace(check_pending_outcomes=AsyncMock(), check_multi_target_outcome=AsyncMock()),
            "services.error_analysis_service": SimpleNamespace(
                check_and_analyze_failed_predictions=AsyncMock(),
                save_candle_snapshot=AsyncMock(),
            ),
            "services.order_block_service": SimpleNamespace(service=SimpleNamespace(detect=AsyncMock())),
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
        call("XAUUSD", "emel_inverse", None, "1h"),
        call("XAUUSD", "pulse1", None, "5m"),
        call("XAUUSD", "pulse2", None, "15m"),
        call("XAUUSD", "pulse3", None, "5m"),
    ]
    assert sleep_mock.await_count == 5


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

    assert check_and_log.await_count == 5


@pytest.mark.asyncio
async def test_log_smc_signals_bypasses_cache_and_enables_logging():
    scheduler = _load_background_scheduler_module("test_background_scheduler_smc")
    scheduler.TRACKED_SYMBOLS = ["XAUUSD"]
    scheduler._last_smc_log = None

    detect_mock = AsyncMock()
    sleep_mock = AsyncMock()

    with patch.object(scheduler, "order_block_service", SimpleNamespace(detect=detect_mock)), patch.object(
        scheduler.asyncio, "sleep", sleep_mock
    ):
        await scheduler.log_smc_signals_if_needed()

    assert detect_mock.await_count == len(scheduler.SMC_AUTO_LOG_TIMEFRAMES)
    for args in detect_mock.await_args_list:
        assert args.args[0] == "XAUUSD"
        assert args.args[2] == 500
        assert args.kwargs["use_cache"] is False
        assert args.kwargs["log_signals"] is True


@pytest.mark.asyncio
async def test_log_predictions_logs_main_and_all_strategy_scopes_for_nasdaq_family():
    scheduler = _load_background_scheduler_module("test_background_scheduler_ml_scopes")
    scheduler.TRACKED_SYMBOLS = ["NDX.INDX"]
    scheduler._last_prediction_log.clear()

    ml_prediction = SimpleNamespace(
        direction="BUY",
        confidence=71.2,
        probability_up=71.2,
        probability_down=28.8,
        entry_price=100.0,
        target_price=110.0,
        stop_price=95.0,
        model_version="test-model",
    )
    get_prediction = AsyncMock(return_value=ml_prediction)
    log_prediction = AsyncMock(side_effect=[f"pred-{idx}" for idx in range(6)])

    with patch.object(scheduler, "get_ml_prediction", get_prediction), patch.dict(
        sys.modules,
        {
            "services.prediction_logger": SimpleNamespace(log_prediction=log_prediction),
            "database.supabase_client": SimpleNamespace(is_db_available=lambda: True),
        },
    ):
        await scheduler.log_predictions_if_needed()

    assert [args.kwargs["strategy"] for args in log_prediction.await_args_list] == [
        "main",
        "ultra_safe",
        "balanced",
        "full_power",
        "aggressive",
        "nasdaq_precision",
    ]
    assert [args.kwargs["model_type"] for args in log_prediction.await_args_list] == [
        "ml:main",
        "ml:ultra_safe",
        "ml:balanced",
        "ml:full_power",
        "ml:aggressive",
        "ml:nasdaq_precision",
    ]
    assert [args.kwargs["strategy"] for args in get_prediction.await_args_list] == [
        "main",
        "ultra_safe",
        "balanced",
        "full_power",
        "aggressive",
        "nasdaq_precision",
    ]


@pytest.mark.asyncio
async def test_log_predictions_respects_interval_guard_after_first_run():
    scheduler = _load_background_scheduler_module("test_background_scheduler_ml_interval")
    scheduler.TRACKED_SYMBOLS = ["XAUUSD"]
    scheduler._last_prediction_log.clear()

    ml_prediction = SimpleNamespace(
        direction="SELL",
        confidence=68.0,
        probability_up=32.0,
        probability_down=68.0,
        entry_price=200.0,
        target_price=190.0,
        stop_price=205.0,
        model_version="test-model",
    )
    get_prediction = AsyncMock(return_value=ml_prediction)
    log_prediction = AsyncMock(side_effect=[f"pred-{idx}" for idx in range(5)])

    with patch.object(scheduler, "get_ml_prediction", get_prediction), patch.dict(
        sys.modules,
        {
            "services.prediction_logger": SimpleNamespace(log_prediction=log_prediction),
            "database.supabase_client": SimpleNamespace(is_db_available=lambda: True),
        },
    ):
        await scheduler.log_predictions_if_needed()
        await scheduler.log_predictions_if_needed()

    assert get_prediction.await_count == 5
    assert log_prediction.await_count == 5
