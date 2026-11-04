"""Behavior checks for the offline trade audit's time and risk boundaries."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_trades.py"
SPEC = importlib.util.spec_from_file_location("audit_trades", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)


class TradeAuditTests(unittest.TestCase):
    def test_entry_minute_and_future_bars_do_not_affect_features(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
        bars = [
            {"ts": start + index * 60, "open": 100 + index * 0.1,
             "high": 101 + index * 0.1, "low": 99 + index * 0.1,
             "close": 100 + index * 0.1}
            for index in range(103)
        ]
        entry = datetime.fromtimestamp(start + 100 * 60 + 20, timezone.utc).isoformat()
        trade = {"entry_time": entry, "direction": "BUY"}
        original = audit.decision_features(trade, bars, [bar["ts"] for bar in bars])
        self.assertIsNotNone(original)
        self.assertEqual(original["decision_bar_ts"], start + 99 * 60)
        for bar in bars[100:]:
            bar.update({"open": 10000, "high": 10001, "low": 9999, "close": 10000})
        changed = audit.decision_features(trade, bars, [bar["ts"] for bar in bars])
        self.assertEqual(original, changed)

    def test_inferred_stop_never_becomes_realized_r(self) -> None:
        trade = {"pnl": 50, "lot": 1, "sl_dist": 100, "geometry_ok": True}
        self.assertIsNone(audit.realized_r(trade, 1))
        trade["risk_cash"] = 100
        self.assertEqual(audit.realized_r(trade, 1), 0.5)

    def test_train_trade_with_outcome_after_test_start_is_embargoed(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        rows = []
        for index in range(10):
            entry = start + timedelta(hours=index)
            exit_ = entry + timedelta(minutes=10)
            if index == 6:
                exit_ = start + timedelta(hours=8)
            rows.append({"entry_time": entry.isoformat(), "exit_time": exit_.isoformat(),
                         "win": index % 2 == 0, "estimated_r": None, "pnl": 1,
                         "trend_aligned": True, "momentum_aligned": True,
                         "confluence_score": 2})
        result = audit.evaluate(rows)
        self.assertEqual(result["embargoed_n"], 1)
        self.assertEqual(result["train_n"], 6)
        self.assertEqual(result["test_n"], 3)

    def _walk_bars(self, start: float, count: int) -> list[dict[str, float]]:
        closes, price = [], 100.0
        for index in range(count):
            price += ((index * 7919) % 13) - 6  # deterministic, non-monotonic walk
            closes.append(price)
        return [{"ts": start + i * 60, "open": c, "high": c + 1, "low": c - 1, "close": c}
                for i, c in enumerate(closes)]

    def test_alignment_ignores_price_basis_but_flags_clock_shift(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
        bars = self._walk_bars(start, 600)
        basis = 27.0  # broker vs backend feed offset: not a timing problem
        trades = [{"entry_time": datetime.fromtimestamp(bars[i]["ts"] + 15, timezone.utc)
                   .isoformat(), "entry_px": bars[i]["close"] + basis}
                  for i in range(250, 450, 10)]
        self.assertEqual(audit.alignment_check(trades, bars)["status"], "ok")
        for trade in trades:  # trade clock labeled in broker time (UTC+3)
            utc = audit.utc_timestamp(trade["entry_time"]) + 3 * 3600
            trade["entry_time"] = datetime.fromtimestamp(utc, timezone.utc).isoformat()
        result = audit.alignment_check(trades, bars)
        self.assertEqual(result["status"], "MISALIGNED")
        self.assertEqual(result["best_shift_min"], -180)

    def test_mt5_csv_export_is_loaded_with_net_pnl(self) -> None:
        header = ("position_id,symbol,direction,magic,volume,open_time_utc,open_price,"
                  "close_time_utc,close_price,sl_price,tp_price,exit_reason,profit,"
                  "commission,swap,comment_in,comment_out\n")
        row = ("1,NAS100,SELL,5,5.0,2026-07-01T10:00:00+00:00,100,"
               "2026-07-01T11:00:00+00:00,90,100,90,tp,50,-1.5,-0.5,fxs X,[tp]\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trades.csv"
            path.write_text(header + row, encoding="utf-8")
            [trade] = audit.load_trades(path)
        self.assertEqual(trade["pnl"], 48.0)
        self.assertEqual(trade["direction"], "SELL")
        self.assertIsNone(audit.realized_r(trade, 1))  # close-time SL is not risk


if __name__ == "__main__":
    unittest.main()
