import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


class _Query:
    def __init__(self, responses):
        self._responses = list(responses)

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self._responses.pop(0) if self._responses else [], error=None)


class _DetailClient:
    def __init__(self, signal_rows, checks=None, failures=None):
        self._tables = {
            "prediction_logs": _Query([signal_rows]),
            "signal_checks": _Query([checks or []]),
            "signal_failures": _Query([failures or []]),
        }

    def table(self, name):
        if name not in self._tables:
            raise AssertionError(f"Unexpected table requested: {name}")
        return self._tables[name]


class _ActiveClient:
    def __init__(self, rows):
        self._table = _Query([rows])

    def table(self, name):
        if name != "prediction_logs":
            raise AssertionError(f"Unexpected table requested: {name}")
        return self._table


def _load_router_module(module_name: str):
    module_path = backend_dir / "routers" / "signal_lifecycle_router.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_get_signal_detail_normalizes_hourly_inflated_geometry():
    from services import signal_lifecycle

    client = _DetailClient(
        [
            {
                "id": "dax-hourly-win-001",
                "symbol": "GDAXI.INDX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "status": "completed",
                "resolution_reason": "tp4_hit",
                "ml_entry_price": 23591.8,
                "exit_price": 23736.1562,
                "highest_profit_pips": 144.4,
                "lowest_drawdown_pips": -12.0,
                "stop_loss_pips": 144.4,
                "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
                "targets": {"TP1": 23656.1562, "TP2": 23666.1562, "TP3": 23676.1562, "TP4": 23736.1562},
                "factors": {},
            }
        ]
    )

    with patch.object(signal_lifecycle, "is_db_available", return_value=True), patch.object(
        signal_lifecycle, "get_supabase_client", return_value=client
    ):
        payload = await signal_lifecycle.get_signal_detail("dax-hourly-win-001")

    signal = payload["signal"]
    assert signal["normalized_status"] == "completed"
    assert signal["calculated_pnl_pips"] == 50.0
    assert signal["targets"] == {"TP1": 23606.8, "TP2": 23616.8, "TP3": 23626.8, "TP4": 23641.8}
    assert signal["targets_hit"] == {"TP1": True, "TP2": True, "TP3": True, "TP4": True}
    assert signal["stop_loss_pips"] == 50.0
    assert signal["raw_exit_price"] == 23736.1562
    assert signal["exit_price"] == pytest.approx(23641.8, abs=0.0001)


@pytest.mark.asyncio
async def test_get_active_signals_normalizes_hourly_inflated_geometry():
    router_module = _load_router_module("test_signal_lifecycle_router_module")
    client = _ActiveClient(
        [
            {
                "id": "dax-hourly-active-001",
                "symbol": "GDAXI.INDX",
                "timeframe": "1h",
                "ml_direction": "BUY",
                "ml_confidence": 74,
                "ml_entry_price": 23591.8,
                "model_type": "pulse3",
                "strategy": "PULSE",
                "status": "active",
                "targets": '{"TP1": 23656.1562, "TP2": 23666.1562, "TP3": 23676.1562, "TP4": 23736.1562}',
                "targets_hit": '{}',
                "highest_profit_pips": 18.0,
                "lowest_drawdown_pips": -5.0,
                "stop_loss_pips": 144.4,
                "created_at": "2026-03-21T12:00:00Z",
            }
        ]
    )

    with patch.dict(
        sys.modules,
        {
            "database.supabase_client": SimpleNamespace(
                is_db_available=lambda: True,
                get_supabase_client=lambda: client,
            ),
        },
    ):
        payload = await router_module.get_active_signals()

    signal = payload["signals"][0]
    assert signal["targets"] == {"TP1": 23606.8, "TP2": 23616.8, "TP3": 23626.8, "TP4": 23641.8}
    assert signal["targets_hit"] == {"TP1": True, "TP2": False, "TP3": False, "TP4": False}
    assert signal["stop_loss_pips"] == 50.0
