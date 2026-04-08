import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.xauusd_backfill_service import DESIRED_TIMEFRAME, plan_xauusd_ml_backfill_update, run_xauusd_ml_history_backfill


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


def test_plan_xauusd_ml_backfill_update_rebuilds_timeframe_targets_and_tp_hits():
    row = {
        "id": "pred-1",
        "symbol": "XAUUSD",
        "strategy": "balanced",
        "model_type": "ml:balanced",
        "timeframe": "1d",
        "ml_direction": "BUY",
        "ml_entry_price": 2000.0,
        "targets": {"TP1": 2024.0, "TP2": 2030.0, "TP3": 2040.0, "TP4": 2054.0, "SL": 1990.0},
        "targets_hit": {"TP1": False, "TP2": False, "TP3": False, "TP4": False},
        "highest_profit_pips": 16.0,
        "stop_loss_pips": 10.0,
        "status": "completed",
        "created_at": _iso(datetime.now(timezone.utc)),
    }

    payload = plan_xauusd_ml_backfill_update(row)

    assert payload is not None
    assert payload["updates"]["timeframe"] == DESIRED_TIMEFRAME
    assert payload["updates"]["stop_loss_pips"] == 15.0
    assert payload["updates"]["targets"]["TP1"] == 2008.0
    assert payload["updates"]["targets"]["TP2"] == 2015.0
    assert payload["updates"]["targets"]["TP3"] == 2025.0
    assert payload["updates"]["targets"]["TP4"] == 2040.0
    assert payload["updates"]["targets"]["SL"] == 1985.0
    assert payload["updates"]["targets_hit"] == {"TP1": True, "TP2": True, "TP3": False, "TP4": False}


def test_run_xauusd_ml_history_backfill_dry_run_counts_only_ml_xauusd_rows():
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "pred-1",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "ml:balanced",
            "timeframe": "1d",
            "ml_direction": "BUY",
            "ml_entry_price": 2000.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 9.0,
            "stop_loss_pips": 15.0,
            "status": "completed",
            "created_at": _iso(now - timedelta(hours=2)),
        },
        {
            "id": "pred-2",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "smc",
            "timeframe": "1h",
            "ml_direction": "BUY",
            "ml_entry_price": 2000.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 0.0,
            "stop_loss_pips": 15.0,
            "status": "active",
            "created_at": _iso(now - timedelta(hours=1)),
        },
        {
            "id": "pred-3",
            "symbol": "NDX.INDX",
            "strategy": "main",
            "model_type": "ml:main",
            "timeframe": "1d",
            "ml_direction": "BUY",
            "ml_entry_price": 100.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 20.0,
            "stop_loss_pips": 50.0,
            "status": "completed",
            "created_at": _iso(now - timedelta(hours=3)),
        },
    ]
    client = _Client(rows)

    payload = run_xauusd_ml_history_backfill(dry_run=True, client=client, max_records=100, window_days=1, sample_size=5)

    assert payload["success"] is True
    assert payload["dry_run"] is True
    assert payload["rows_scanned"] == 2
    assert payload["ml_rows_considered"] == 1
    assert payload["rows_needing_update"] == 1
    assert payload["rows_updated"] == 0
    assert payload["field_change_counts"]["timeframe"] == 1
    assert client.updates_log == []


def test_run_xauusd_ml_history_backfill_apply_updates_matching_rows():
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "pred-1",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "ml:balanced",
            "timeframe": "1d",
            "ml_direction": "SELL",
            "ml_entry_price": 2100.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 18.0,
            "stop_loss_pips": 15.0,
            "status": "completed",
            "created_at": _iso(now - timedelta(hours=2)),
        }
    ]
    client = _Client(rows)

    payload = run_xauusd_ml_history_backfill(dry_run=False, client=client, max_records=100, window_days=1, sample_size=5)

    assert payload["rows_needing_update"] == 1
    assert payload["rows_updated"] == 1
    assert client.updates_log
    assert rows[0]["timeframe"] == DESIRED_TIMEFRAME
    assert rows[0]["targets_hit"]["TP1"] is True
