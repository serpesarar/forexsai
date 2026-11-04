"""Behavior checks for the rejected-opportunity replay's fill and dedupe rules."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("audit_skipped", SCRIPTS / "audit_skipped.py")
skipped = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(skipped)


def make_bars(rows: list[tuple[float, float, float, float]]) -> dict[str, list[float]]:
    """rows = (high, low, spread, open); bars start at t=0,60,120,..."""
    return {"ts": [i * 60.0 for i in range(len(rows))],
            "high": [r[0] for r in rows], "low": [r[1] for r in rows],
            "spread": [r[2] for r in rows], "open": [r[3] for r in rows]}


class ReplayTests(unittest.TestCase):
    def test_bars_before_the_decision_never_resolve_it(self) -> None:
        bars = make_bars([(300, 100, 0, 200), (201, 199, 0, 200), (201, 199, 0, 200)])
        # bar 0 would hit TP and SL, but it closed before the decision at t=60
        self.assertEqual(skipped.resolve(bars, 60.0, "BUY", 200.0, 50.0, 50.0), "open")

    def test_sell_exit_pays_the_spread_and_same_bar_is_a_loss(self) -> None:
        # SELL entry 200, TP 150: bar low 149 + spread 2 = 151 -> not reached
        bars = make_bars([(201, 149, 2.0, 200)])
        self.assertEqual(skipped.resolve(bars, 0.0, "SELL", 200.0, 50.0, 50.0), "open")
        bars = make_bars([(201, 147, 2.0, 200)])
        self.assertEqual(skipped.resolve(bars, 0.0, "SELL", 200.0, 50.0, 50.0), "win")
        bars = make_bars([(255, 140, 0.0, 200)])  # touches both TP and SL
        self.assertEqual(skipped.resolve(bars, 0.0, "SELL", 200.0, 50.0, 50.0), "loss")

    def test_repeated_skips_are_one_opportunity_until_it_resolves(self) -> None:
        rows = [(201, 199, 0, 200)] * 5 + [(260, 199, 0, 200)] + [(201, 199, 0, 200)] * 4
        bars = make_bars(rows)
        events = [{"ts": 10.0 + 75 * k, "scope": "s", "direction": "BUY", "price": 200.0,
                   "reason": "r", "source": "t"} for k in range(4)]
        outcomes, censored = skipped.sequence(events, bars, (50.0, 50.0))
        self.assertEqual(len(outcomes), 1)  # ticks at 10/85/160/235 s all sit inside the hold
        self.assertTrue(outcomes[0]["win"])
        self.assertEqual(censored, 0)

    def test_ci_containing_breakeven_is_not_called_proven(self) -> None:
        whole = skipped.stats([{"win": i < 5} for i in range(10)], (80.0, 110.0))
        half = {"n": 5, "usd_per_trade": -1.0}
        self.assertIn("CI başabaşı içeriyor", skipped.verdict(half, half, whole))


if __name__ == "__main__":
    unittest.main()
