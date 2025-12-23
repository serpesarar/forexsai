import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from rhythm_detector_v2 import RhythmDetector, RhythmConfig


@dataclass
class BacktestResult:
    win_rate: float
    sharpe: float
    max_drawdown: float
    trades: int


def generate_sine_series(length: int, freq_hz: float, noise: float = 0.001) -> np.ndarray:
    t = np.arange(length)
    base = np.sin(2 * np.pi * freq_hz * t)
    return base + np.random.normal(scale=noise, size=length)


def backtest(detector: RhythmDetector, prices: np.ndarray) -> BacktestResult:
    returns: List[float] = []
    equity = 1.0
    peak = 1.0
    drawdowns = []
    trades = 0

    for idx, price in enumerate(prices):
        detector.add_tick(float(price), timestamp=float(idx))
        if idx % 10 == 0 and idx > 100:
            detector.detect_wave_pattern()
            decision = detector.should_trade()
            if decision["should_trade"]:
                horizon = 60
                if idx + horizon < len(prices):
                    future = prices[idx + horizon]
                    pnl = (future - price) / price
                    if decision["direction"] == "SELL":
                        pnl = -pnl
                    returns.append(pnl)
                    equity *= 1.0 + pnl
                    peak = max(peak, equity)
                    drawdowns.append((peak - equity) / peak)
                    trades += 1

    if not returns:
        return BacktestResult(0.0, 0.0, 0.0, trades)

    ret_series = pd.Series(returns)
    sharpe = float(ret_series.mean() / (ret_series.std() + 1e-9) * math.sqrt(252))
    win_rate = float((ret_series > 0).mean())
    max_drawdown = float(max(drawdowns) if drawdowns else 0.0)
    return BacktestResult(win_rate=win_rate, sharpe=sharpe, max_drawdown=max_drawdown, trades=trades)


def main() -> None:
    np.random.seed(42)
    config = RhythmConfig(window_seconds=600)
    detector = RhythmDetector(config)

    prices = 100 + generate_sine_series(5000, freq_hz=1 / 60, noise=0.01)
    result = backtest(detector, prices)

    print("Backtest Results")
    print(result)

    plt.figure(figsize=(10, 4))
    plt.plot(prices, label="Price")
    plt.title("Synthetic Price Series")
    plt.legend()
    plt.tight_layout()
    plt.savefig("backtest_price_series.png")


if __name__ == "__main__":
    main()
