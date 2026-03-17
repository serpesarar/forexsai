import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from services.ml_history_backfill_service import DESIRED_TIMEFRAME, plan_ml_backfill_update, run_ml_history_backfill


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


def test_plan_ml_backfill_update_supports_non_xau_symbols():
    row = {
        "id": "pred-ndx-1",
        "symbol": "NDX.INDX",
        "strategy": "main",
        "model_type": "ml:main",
        "timeframe": "1h",
        "ml_direction": "BUY",
        "ml_entry_price": 20000.0,
        "targets": {},
        "targets_hit": {},
        "highest_profit_pips": 30.0,
        "stop_loss_pips": 10.0,
        "status": "completed",
        "created_at": _iso(datetime.now(timezone.utc)),
    }

    payload = plan_ml_backfill_update(row)

    assert payload is not None
    assert payload["symbol"] == "NDX.INDX"
    assert payload["updates"]["timeframe"] == DESIRED_TIMEFRAME
    assert payload["updates"]["stop_loss_pips"] > 0
    assert payload["updates"]["targets"]["SL"] is not None


def test_run_ml_history_backfill_tracks_updates_per_symbol():
    now = datetime.now(timezone.utc)
    rows = [
        {
            "id": "xau-1",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "ml:balanced",
            "timeframe": "1d",
            "ml_direction": "BUY",
            "ml_entry_price": 2000.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 10.0,
            "stop_loss_pips": 10.0,
            "status": "completed",
            "created_at": _iso(now - timedelta(hours=2)),
        },
        {
            "id": "ndx-1",
            "symbol": "NDX.INDX",
            "strategy": "main",
            "model_type": "ml:main",
            "timeframe": "1h",
            "ml_direction": "SELL",
            "ml_entry_price": 20000.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 40.0,
            "stop_loss_pips": 20.0,
            "status": "completed",
            "created_at": _iso(now - timedelta(hours=1)),
        },
        {
            "id": "pulse-1",
            "symbol": "XAUUSD",
            "strategy": "balanced",
            "model_type": "pulse2",
            "timeframe": "1h",
            "ml_direction": "BUY",
            "ml_entry_price": 2000.0,
            "targets": {},
            "targets_hit": {},
            "highest_profit_pips": 0.0,
            "stop_loss_pips": 10.0,
            "status": "active",
            "created_at": _iso(now - timedelta(minutes=30)),
        },
    ]
    client = _Client(rows)

    payload = run_ml_history_backfill(
        dry_run=True,
        client=client,
        symbols=["XAUUSD", "NDX.INDX"],
        max_records=100,
        window_days=1,
        sample_size=5,
    )

    assert payload["success"] is True
    assert payload["symbols"] == ["XAUUSD", "NDX.INDX"]
    assert payload["rows_scanned"] == 3
    assert payload["ml_rows_considered"] == 2
    assert payload["rows_needing_update"] == 2
    assert payload["rows_updated"] == 0
    assert payload["symbol_update_counts"] == {"XAUUSD": 1, "NDX.INDX": 1}
    assert client.updates_log == []
