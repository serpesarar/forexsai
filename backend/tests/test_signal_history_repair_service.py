import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.signal_history_repair_service import plan_signal_history_repair, run_signal_history_repair


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value):
    if not isinstance(value, str):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class _Query:
    def __init__(self, rows, updates_log):
        self._rows = rows
        self._updates_log = updates_log
        self._eq_filters = []
        self._in_filters = []
        self._gte_filters = []
        self._lt_filters = []
        self._limit = None
        self._order = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self._eq_filters.append((field, value))
        return self

    def in_(self, field, values):
        self._in_filters.append((field, set(values)))
        return self

    def gte(self, field, value):
        self._gte_filters.append((field, value))
        return self

    def lt(self, field, value):
        self._lt_filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self._order = (field, desc)
        return self

    def limit(self, value):
        self._limit = value
        return self

    def update(self, data):
        rows = self._filtered_rows()
        for row in rows:
            row.update(data)
            self._updates_log.append((row["id"], data))
        return {"data": rows, "error": None}

    def execute(self):
        rows = self._filtered_rows()
        return SimpleNamespace(data=rows, error=None)

    def _filtered_rows(self):
        rows = list(self._rows)
        for field, value in self._eq_filters:
            rows = [row for row in rows if row.get(field) == value]
        for field, values in self._in_filters:
            rows = [row for row in rows if row.get(field) in values]
        for field, value in self._gte_filters:
            compare = _parse_iso(value)
            rows = [row for row in rows if _parse_iso(row.get(field)) >= compare]
        for field, value in self._lt_filters:
            compare = _parse_iso(value)
            rows = [row for row in rows if _parse_iso(row.get(field)) < compare]
        if self._order:
            field, desc = self._order
            rows.sort(key=lambda row: _parse_iso(row.get(field)) or row.get(field), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return rows


class _Client:
    def __init__(self, rows):
        self.rows = rows
        self.updates_log = []

    def table(self, name):
        assert name == "prediction_logs"
        return _Query(self.rows, self.updates_log)


def test_plan_signal_history_repair_normalizes_completed_target_exit_price():
    row = {
        "id": "pred-1",
        "symbol": "NDX.INDX",
        "strategy": "PULSE",
        "model_type": "pulse1",
        "timeframe": "15m",
        "ml_direction": "SELL",
        "ml_entry_price": 24359.9,
        "targets": {"TP1": 24344.9, "TP2": 24334.9, "TP3": 24324.9, "TP4": 24309.9},
        "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
        "highest_profit_pips": 129.6,
        "lowest_drawdown_pips": 0.0,
        "stop_loss_pips": 50.0,
        "status": "completed",
        "exit_price": 24230.3,
        "exit_time": _iso(datetime.now(timezone.utc)),
        "resolution_reason": "tp4_hit",
        "created_at": _iso(datetime.now(timezone.utc) - timedelta(minutes=10)),
    }

    plan = plan_signal_history_repair(row)

    assert plan is not None
    assert plan["updates"]["exit_price"] == 24309.9
    assert "status" not in plan["updates"]


def test_plan_signal_history_repair_reclassifies_stopped_target_hit_rows():
    row = {
        "id": "pred-2",
        "symbol": "GDAXI.INDX",
        "strategy": "SMART_MONEY_ZONES",
        "model_type": "smc",
        "timeframe": "15m",
        "ml_direction": "SELL",
        "ml_entry_price": 23502.2,
        "targets": {"TP1": 23487.2, "TP2": 23477.2, "TP3": 23467.2, "TP4": 23452.2},
        "targets_hit": {"TP1": True, "TP2": False, "TP3": False, "TP4": False},
        "highest_profit_pips": 15.0,
        "lowest_drawdown_pips": -89.6,
        "stop_loss_pips": 50.0,
        "status": "stopped",
        "exit_price": 23591.8,
        "exit_time": _iso(datetime.now(timezone.utc)),
        "resolution_reason": "sl_hit",
        "created_at": _iso(datetime.now(timezone.utc) - timedelta(minutes=30)),
    }

    plan = plan_signal_history_repair(row)

    assert plan is not None
    assert plan["updates"]["status"] == "completed"
    assert plan["updates"]["exit_price"] == 23487.2
    assert plan["updates"]["resolution_reason"] == "tp1_3_hit_then_sl"


def test_run_signal_history_repair_counts_and_applies_updates():
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "ndx-1",
            "symbol": "NDX.INDX",
            "strategy": "PULSE",
            "model_type": "pulse1",
            "timeframe": "15m",
            "ml_direction": "SELL",
            "ml_entry_price": 24359.9,
            "targets": {"TP1": 24344.9, "TP2": 24334.9, "TP3": 24324.9, "TP4": 24309.9},
            "targets_hit": {"TP1": True, "TP2": True, "TP3": True, "TP4": True},
            "highest_profit_pips": 129.6,
            "lowest_drawdown_pips": 0.0,
            "stop_loss_pips": 50.0,
            "status": "completed",
            "exit_price": 24230.3,
            "exit_time": _iso(now - timedelta(minutes=5)),
            "resolution_reason": "tp4_hit",
            "created_at": _iso(now - timedelta(minutes=20)),
        },
        {
            "id": "xau-1",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "ml:balanced",
            "timeframe": "30m",
            "ml_direction": "BUY",
            "ml_entry_price": 3000.0,
            "targets": {"TP1": 3008.0, "TP2": 3015.0, "TP3": 3025.0, "TP4": 3040.0},
            "targets_hit": {},
            "highest_profit_pips": 5.0,
            "lowest_drawdown_pips": -2.0,
            "stop_loss_pips": 15.0,
            "status": "completed",
            "exit_price": 3005.0,
            "exit_time": _iso(now - timedelta(minutes=15)),
            "resolution_reason": "window_resolve_positive",
            "created_at": _iso(now - timedelta(hours=2)),
        },
    ]
    client = _Client(rows)

    dry_payload = run_signal_history_repair(
        dry_run=True,
        client=client,
        symbols=["NDX.INDX", "XAUUSD"],
        max_records=100,
        window_days=1,
        sample_size=5,
    )

    assert dry_payload["success"] is True
    assert dry_payload["rows_scanned"] == 2
    assert dry_payload["rows_needing_update"] == 1
    assert dry_payload["symbol_update_counts"] == {"NDX.INDX": 1}
    assert client.updates_log == []

    apply_payload = run_signal_history_repair(
        dry_run=False,
        client=client,
        symbols=["NDX.INDX", "XAUUSD"],
        max_records=100,
        window_days=1,
        sample_size=5,
    )

    assert apply_payload["rows_needing_update"] == 1
    assert apply_payload["rows_updated"] == 1
    assert client.updates_log[0][0] == "ndx-1"
    assert client.updates_log[0][1]["exit_price"] == 24309.9
